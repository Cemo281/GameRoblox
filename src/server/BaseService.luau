--!strict
-- BaseService : attribue une base (Model tagué "BaseJoueur") à chaque joueur et affiche ses personnages
-- sur les emplacements. Voir docs/wiki/Base-et-inventaire.md.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economie = require(ReplicatedStorage.Shared.Economie)
local GachaConfig = require(ReplicatedStorage.Shared.GachaConfig)
local Personnages = require(ReplicatedStorage.Shared.Personnages)
local DataService = require(script.Parent.DataService)

local BaseService = {}

local TAG_BASE = "BaseJoueur"
local TEXTE_BASE_LIBRE = "Base libre"
local COULEUR_EMPLACEMENT = Color3.fromRGB(235, 235, 235)
local COULEUR_VERROUILLE = Color3.fromRGB(110, 110, 110)
local TAILLE_PERSONNAGE = Vector3.new(3, 5, 3)

local proprietaires: { [Model]: Player } = {}
local basesParJoueur: { [Player]: Model } = {}
local connexionsApparition: { [Player]: RBXScriptConnection } = {}

local function trouverBase(instance: Instance): Model?
	local courant: Instance? = instance
	while courant do
		if courant:IsA("Model") and CollectionService:HasTag(courant, TAG_BASE) then
			return courant
		end
		courant = courant.Parent
	end
	return nil
end

local function texteEmplacement(emplacement: BasePart): TextLabel?
	local gui = emplacement:FindFirstChildWhichIsA("SurfaceGui")
	return if gui then gui:FindFirstChildWhichIsA("TextLabel") else nil
end

local function texteProprietaire(base: Model): TextLabel?
	local panneau = base:FindFirstChild("Panneau")
	local label = panneau and panneau:FindFirstChild("NomProprietaire", true)
	return if label and label:IsA("TextLabel") then label else nil
end

local function emplacementsDe(base: Model): { BasePart }
	local resultat = {}
	local dossier = base:FindFirstChild("Emplacements")
	if dossier then
		for _, enfant in dossier:GetChildren() do
			if enfant:IsA("BasePart") and typeof(enfant:GetAttribute("Index")) == "number" then
				table.insert(resultat, enfant)
			end
		end
	end
	return resultat
end

-- Orientation d'un personnage posé : face à l'allée de sa base (perpendiculaire à son grand axe).
local function orientationVersAllee(emplacement: BasePart, position: Vector3): CFrame
	local base = trouverBase(emplacement)
	local allee = base and base:FindFirstChild("Allee")
	if allee and allee:IsA("BasePart") then
		local relatif = allee.CFrame:PointToObjectSpace(position)
		local surAxe = if allee.Size.Z >= allee.Size.X
			then Vector3.new(0, relatif.Y, relatif.Z)
			else Vector3.new(relatif.X, relatif.Y, 0)
		local direction = (allee.CFrame:PointToWorldSpace(surAxe) - position) * Vector3.new(1, 0, 1)
		if direction.Magnitude > 0.01 then
			return CFrame.lookAt(position, position + direction)
		end
	end
	return CFrame.new(position)
end

-- Modèle 3D animé (ReplicatedStorage.ModelesPersonnages.<Id>, rangé par le skill /perso-r6), ou nil.
-- Renvoie le support de l'étiquette et la hauteur de l'étiquette au-dessus de ce support.
local function creerModele(emplacement: BasePart, id: string): (Model?, BasePart?, number)
	local dossier = ReplicatedStorage:FindFirstChild("ModelesPersonnages")
	local source = dossier and dossier:FindFirstChild(id)
	if not (source and source:IsA("Model") and source.PrimaryPart) then
		return nil, nil, 0
	end

	local modele = source:Clone()
	modele.Name = "Personnage"
	local boite, taille = modele:GetBoundingBox()
	local pivot = modele:GetPivot().Position
	local sousPivot = pivot.Y - (boite.Position.Y - taille.Y / 2)
	local position = emplacement.Position + Vector3.new(0, emplacement.Size.Y / 2 + sousPivot, 0)
	modele:PivotTo(orientationVersAllee(emplacement, position))
	modele.Parent = emplacement

	local animationId = modele:GetAttribute("AnimationIdle")
	local controleur = modele:FindFirstChildOfClass("AnimationController")
	local animator = controleur and controleur:FindFirstChildOfClass("Animator")
	if typeof(animationId) == "string" and animator then
		local animation = Instance.new("Animation")
		animation.AnimationId = animationId
		local piste = animator:LoadAnimation(animation)
		piste.Looped = true
		piste:Play()
	end

	return modele, modele.PrimaryPart, taille.Y - sousPivot + 1.5
end

local function creerPersonnage(
	emplacement: BasePart,
	id: string,
	nom: string,
	etoiles: number,
	revenu: number,
	couleur: Color3
)
	local modele, support, hauteurEtiquette = creerModele(emplacement, id)
	local bloc: BasePart
	if modele and support then
		bloc = support
	else
		local part = Instance.new("Part")
		part.Name = "Personnage"
		part.Anchored = true
		part.Size = TAILLE_PERSONNAGE
		part.Color = couleur
		part.Material = Enum.Material.SmoothPlastic
		part.Position = emplacement.Position + Vector3.new(0, emplacement.Size.Y / 2 + TAILLE_PERSONNAGE.Y / 2, 0)
		bloc = part
		hauteurEtiquette = TAILLE_PERSONNAGE.Y / 2 + 1.5
	end

	local billboard = Instance.new("BillboardGui")
	billboard.Size = UDim2.fromOffset(160, 50)
	billboard.StudsOffset = Vector3.new(0, hauteurEtiquette, 0)
	billboard.MaxDistance = 80

	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Text = `{nom} {string.rep("★", etoiles)}\n{math.round(revenu * 10) / 10} $/s`
	label.TextColor3 = couleur
	label.TextStrokeTransparency = 0
	label.TextScaled = true
	label.Font = Enum.Font.GothamBold
	label.Parent = billboard

	billboard.Parent = bloc
	if not modele then
		bloc.Parent = emplacement
	end
end

-- Remet une base dans son apparence « libre ».
local function reinitialiserBase(base: Model)
	for _, emplacement in emplacementsDe(base) do
		local ancien = emplacement:FindFirstChild("Personnage")
		if ancien then
			ancien:Destroy()
		end
		emplacement.Color = COULEUR_EMPLACEMENT
		local label = texteEmplacement(emplacement)
		if label then
			label.Text = tostring(emplacement:GetAttribute("Index"))
		end
	end
	local nom = texteProprietaire(base)
	if nom then
		nom.Text = TEXTE_BASE_LIBRE
	end
end

local function teleporterALaBase(player: Player, character: Model)
	local base = basesParJoueur[player]
	local apparition = base and base:FindFirstChild("PointApparition")
	if apparition and apparition:IsA("BasePart") then
		character:PivotTo(apparition.CFrame + Vector3.new(0, 3, 0))
	end
end

local function attribuerBase(player: Player)
	if basesParJoueur[player] then
		return
	end
	for _, instance in CollectionService:GetTagged(TAG_BASE) do
		if instance:IsA("Model") and not proprietaires[instance] then
			proprietaires[instance] = player
			basesParJoueur[player] = instance
			instance:SetAttribute("Proprietaire", player.UserId)

			local nom = texteProprietaire(instance)
			if nom then
				nom.Text = `Base de {player.DisplayName}`
			end

			connexionsApparition[player] = player.CharacterAdded:Connect(function(character)
				-- Laisse le personnage apparaître au SpawnLocation avant de le déplacer
				task.defer(teleporterALaBase, player, character)
			end)
			if player.Character then
				teleporterALaBase(player, player.Character)
			end

			BaseService.RafraichirEmplacements(player)
			return
		end
	end
	warn(`[BaseService] Aucune base libre pour {player.Name}`)
end

local function libererBase(player: Player)
	local connexion = connexionsApparition[player]
	if connexion then
		connexion:Disconnect()
		connexionsApparition[player] = nil
	end
	local base = basesParJoueur[player]
	if not base then
		return
	end
	basesParJoueur[player] = nil
	proprietaires[base] = nil
	base:SetAttribute("Proprietaire", nil)
	reinitialiserBase(base)

	-- Donne la base libérée à un joueur qui n'en avait pas trouvé
	for _, autre in Players:GetPlayers() do
		if autre ~= player and not basesParJoueur[autre] and DataService.GetData(autre) then
			attribuerBase(autre)
			return
		end
	end
end

function BaseService.Init()
	for _, instance in CollectionService:GetTagged(TAG_BASE) do
		if instance:IsA("Model") then
			reinitialiserBase(instance)
		end
	end
	DataService.OnChargement(attribuerBase)
	Players.PlayerRemoving:Connect(libererBase)
end

function BaseService.GetBase(player: Player): Model?
	return basesParJoueur[player]
end

-- Propriétaire de la base qui contient `instance` (machine, collecteur…), ou nil.
function BaseService.GetProprietaire(instance: Instance): Player?
	local base = trouverBase(instance)
	return if base then proprietaires[base] else nil
end

-- Redessine les emplacements de la base du joueur à partir de ses données.
function BaseService.RafraichirEmplacements(player: Player)
	local base = basesParJoueur[player]
	local data = DataService.GetData(player)
	if not base or not data then
		return
	end

	for _, emplacement in emplacementsDe(base) do
		local index = emplacement:GetAttribute("Index") :: number
		local ancien = emplacement:FindFirstChild("Personnage")
		if ancien then
			ancien:Destroy()
		end

		local debloque = index <= data.EmplacementsDebloques
		emplacement.Color = if debloque then COULEUR_EMPLACEMENT else COULEUR_VERROUILLE
		local label = texteEmplacement(emplacement)
		if label then
			label.Text = if debloque then tostring(index) else "🔒"
		end

		local uid = data.Emplacements[tostring(index)]
		local personnage = uid and data.Personnages[uid]
		local definition = personnage and Personnages.ParId[personnage.Id]
		if personnage and definition then
			local rarete = GachaConfig.RaretesParId[definition.Rarete]
			local revenu = Economie.RevenuParSeconde(definition.Revenu, personnage.Etoiles, data.Rebirths)
			creerPersonnage(
				emplacement,
				definition.Id,
				definition.Nom,
				personnage.Etoiles,
				revenu,
				if rarete then rarete.Couleur else Color3.new(1, 1, 1)
			)
		end
	end
end

return BaseService
