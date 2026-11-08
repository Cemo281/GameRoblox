--!strict
-- Vue3D : modèles 3D dans des ViewportFrame (panneau de détail de l'inventaire, tirage).
-- Le modèle d'un perso est cloné depuis ReplicatedStorage.ModelesPersonnages.<Id> dans un WorldModel pour que
-- son Animator joue l'Idle (attribut `AnimationIdle`) en boucle. Sans modèle, Montrer renvoie false.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Ui = require(script.Parent.Ui)

local Vue3D = {}

export type Vue = {
	Cadre: ViewportFrame,
	Monde: WorldModel,
	Camera: Camera,
}

function Vue3D.Creer(props: { [string]: any }): Vue
	local camera = Instance.new("Camera")
	camera.FieldOfView = 30
	local defauts: { [string]: any } = {
		BackgroundTransparency = 1,
		Ambient = Color3.fromRGB(170, 165, 190),
		LightColor = Color3.new(1, 1, 1),
		LightDirection = Vector3.new(-0.4, -1, -0.6),
		CurrentCamera = camera,
	}
	for cle, valeur in props do
		defauts[cle] = valeur
	end
	local cadre = Ui.Creer("ViewportFrame", defauts)
	camera.Parent = cadre
	local monde = Ui.Creer("WorldModel", { Parent = cadre })
	return { Cadre = cadre, Monde = monde, Camera = camera }
end

function Vue3D.Vider(vue: Vue)
	vue.Monde:ClearAllChildren()
end

-- Cadre la caméra sur `modele`, de face (LookVector du pivot), avec une marge.
function Vue3D.Cadrer(vue: Vue, modele: Model, marge: number?, hauteurVisee: number?)
	local boite, taille = modele:GetBoundingBox()
	local pivot = modele:GetPivot()
	local avant = Vector3.new(pivot.LookVector.X, 0, pivot.LookVector.Z)
	avant = if avant.Magnitude > 0.01 then avant.Unit else Vector3.new(0, 0, -1)
	local demiHauteur = math.max(taille.Y, taille.X * 0.8) / 2 * (marge or 1.15)
	local distance = demiHauteur / math.tan(math.rad(vue.Camera.FieldOfView / 2))
	local cible = boite.Position + Vector3.new(0, (hauteurVisee or 0) * taille.Y, 0)
	vue.Camera.CFrame = CFrame.lookAt(cible + avant * distance + Vector3.new(0, taille.Y * 0.08, 0), cible)
end

-- Affiche le modèle du perso `id` en Idle. Renvoie le modèle, ou nil si le perso n'a pas de modèle 3D.
function Vue3D.Montrer(vue: Vue, id: string): Model?
	Vue3D.Vider(vue)
	local dossier = ReplicatedStorage:FindFirstChild("ModelesPersonnages")
	local source = dossier and dossier:FindFirstChild(id)
	if not (source and source:IsA("Model") and source.PrimaryPart) then
		return nil
	end
	local modele = source:Clone()
	for _, descendant in modele:GetDescendants() do
		if descendant:IsA("BaseScript") then
			descendant:Destroy()
		elseif descendant:IsA("BasePart") then
			descendant.Anchored = descendant == modele.PrimaryPart or descendant.Anchored
		end
	end
	modele:PivotTo(CFrame.new())
	modele.Parent = vue.Monde
	Vue3D.Cadrer(vue, modele)

	local controleur = modele:FindFirstChildOfClass("AnimationController") or modele:FindFirstChildOfClass("Humanoid")
	local animator = controleur and controleur:FindFirstChildOfClass("Animator")
	local idle = modele:GetAttribute("AnimationIdle")
	if animator and typeof(idle) == "string" then
		local animation = Instance.new("Animation")
		animation.AnimationId = idle
		local ok, piste = pcall(function()
			return animator:LoadAnimation(animation)
		end)
		if ok and piste then
			piste.Looped = true
			piste:Play(0)
		end
	end
	return modele
end

-- Rig R6 classique en pièces (tête, torse, bras, jambes), tout noir, pour l'animation de tirage.
-- Les membres sont des pièces indépendantes (pas de Motor6D) : l'appelant les fait bouger par CFrame.
export type Rig = {
	Modele: Model,
	Parties: { [string]: BasePart },
	Repos: { [string]: CFrame }, -- CFrame de chaque partie relative au torse
}

function Vue3D.RigR6(couleur: Color3): Rig
	local modele = Instance.new("Model")
	modele.Name = "RigTirage"
	local definitions: { { Nom: string, Taille: Vector3, Position: Vector3 } } = {
		{ Nom = "Torse", Taille = Vector3.new(2, 2, 1), Position = Vector3.new(0, 3, 0) },
		{ Nom = "Tete", Taille = Vector3.new(2, 1, 1), Position = Vector3.new(0, 4.5, 0) }, -- tête R6 (maillage Head ×1,25)
		{ Nom = "BrasG", Taille = Vector3.new(0.96, 2, 0.96), Position = Vector3.new(-1.5, 3, 0) },
		{ Nom = "BrasD", Taille = Vector3.new(0.96, 2, 0.96), Position = Vector3.new(1.5, 3, 0) },
		{ Nom = "JambeG", Taille = Vector3.new(0.96, 2, 0.96), Position = Vector3.new(-0.5, 1, 0) },
		{ Nom = "JambeD", Taille = Vector3.new(0.96, 2, 0.96), Position = Vector3.new(0.5, 1, 0) },
	}
	local parties: { [string]: BasePart } = {}
	local repos: { [string]: CFrame } = {}
	for _, definition in definitions do
		local partie = Instance.new("Part")
		partie.Name = definition.Nom
		partie.Size = definition.Taille
		partie.Anchored = true
		partie.CanCollide = false
		partie.Material = Enum.Material.SmoothPlastic
		partie.Color = couleur
		partie.CFrame = CFrame.new(definition.Position)
		partie.Parent = modele
		parties[definition.Nom] = partie
		repos[definition.Nom] = CFrame.new(definition.Position - Vector3.new(0, 3, 0))
	end
	local tete = parties.Tete
	local coins = Instance.new("SpecialMesh")
	coins.MeshType = Enum.MeshType.Head
	coins.Scale = Vector3.new(1.25, 1.25, 1.25)
	coins.Parent = tete
	modele.PrimaryPart = parties.Torse
	return { Modele = modele, Parties = parties, Repos = repos }
end

return Vue3D
