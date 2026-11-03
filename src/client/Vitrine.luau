--!strict
-- Vitrine : sur chaque personnage posé (Model tagué "PersonnageVitrine" par BaseService), applique les marqueurs
-- des animations jouées par le serveur : Montrer / Cacher un accessoire, déclencher un effet du dossier VFX.
-- Fait côté client car ParticleEmitter:Emit() n'est pas répliqué ; chaque joueur voit donc sabres et effets.
-- Conventions du modèle : skill /perso-roblox (sections 3 et 5).

local CollectionService = game:GetService("CollectionService")
local Debris = game:GetService("Debris")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Elastique = require(script.Parent.Elastique)

local Vitrine = {}

local TAG_VITRINE = "PersonnageVitrine"
-- Marqueurs de gameplay (séquence du sabreur) : « Impact Sol » déclenche l'effet VFX « Impact_Sol » s'il existe.
-- Utile car l'Éditeur d'animation ne publie qu'un marqueur de chaque nom par image clé : un 2e « VFX » au même
-- instant est perdu, alors que le marqueur de gameplay voisin est gardé.
local MARQUEURS_EFFETS = { "Impact", "Esquive", "Aura", "Explosion", "Fin", "Feu", "Pompe" }
-- Marqueurs du corps élastique (luffy), transmis au module Elastique
local MARQUEURS_ELASTIQUE = { "Pompe", "Aura" }
local EXTREMITES = { "RightHand", "LeftHand", "RightFoot", "LeftFoot" }
-- Secousse de caméra : pleine jusqu'à SECOUSSE_PORTEE_PLEINE studs du personnage, nulle au-delà de + SECOUSSE_PORTEE
local SECOUSSE_PORTEE_PLEINE = 15
local SECOUSSE_PORTEE = 25
local SECOUSSE_ECHELLE = 0.6 -- studs de décalage pour une amplitude 1
local SECOUSSE_AMORTI = 9
local INFO_FANTOME = TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

-- Remet chaque accessoire dans son état par défaut (attribut VisibleParDefaut), ex. pour un joueur arrivé en cours d'Action.
local function reinitialiserAccessoires(modele: Model)
	for _, enfant in modele:GetChildren() do
		local visible = enfant:GetAttribute("VisibleParDefaut")
		local handle = enfant:IsA("Accessory") and enfant:FindFirstChild("Handle")
		if typeof(visible) == "boolean" and handle and handle:IsA("BasePart") then
			handle.Transparency = if visible then 0 else 1
		end
	end
end

local function montrer(modele: Model, nom: string, visible: boolean)
	local accessoire = modele:FindFirstChild(nom)
	local handle = accessoire and accessoire:FindFirstChild("Handle")
	if handle and handle:IsA("BasePart") then
		handle.Transparency = if visible then 0 else 1
	end
end

local function emetteurs(dossier: Instance): { Instance }
	local liste = {}
	for _, lien in dossier:GetChildren() do
		if lien:IsA("ObjectValue") and lien.Value then
			table.insert(liste, lien.Value)
		end
	end
	return liste
end

local function allumer(emetteur: Instance, actif: boolean)
	if emetteur:IsA("ParticleEmitter") or emetteur:IsA("Trail") or emetteur:IsA("Beam") or emetteur:IsA("Light") then
		emetteur.Enabled = actif
	end
end

local function eteindre(vfx: Instance, nom: string)
	local dossier = vfx:FindFirstChild(nom)
	if dossier then
		for _, emetteur in emetteurs(dossier) do
			allumer(emetteur, false)
		end
	end
end

-- Secousse de caméra (impacts) : amplitude courante, amortie chaque image, appliquée après la caméra du joueur.
local secousse = 0
local function secouer(modele: Model, amplitude: number)
	local camera = workspace.CurrentCamera
	if not camera then
		return
	end
	local distance = (camera.Focus.Position - modele:GetPivot().Position).Magnitude
	local attenuation = 1 - math.clamp((distance - SECOUSSE_PORTEE_PLEINE) / SECOUSSE_PORTEE, 0, 1)
	secousse = math.max(secousse, amplitude * attenuation)
end

-- Décalage appliqué à l'image précédente : retiré avant la mise à jour de la caméra du joueur, sinon la caméra repart
-- de la position secouée et dérive (vu en Play : après un gros impact, la caméra restait tournée).
local decalageApplique = CFrame.identity

local function retirerSecousse()
	local camera = workspace.CurrentCamera
	if camera and decalageApplique ~= CFrame.identity then
		camera.CFrame *= decalageApplique:Inverse()
	end
	decalageApplique = CFrame.identity
end

local function appliquerSecousse(dt: number)
	if secousse < 0.01 then
		secousse = 0
		return
	end
	local camera = workspace.CurrentCamera
	if camera then
		local a = secousse * SECOUSSE_ECHELLE
		local decalage = Vector3.new((math.random() - 0.5) * a, (math.random() - 0.5) * a, 0)
		decalageApplique = CFrame.new(decalage) * CFrame.Angles(0, 0, math.rad((math.random() - 0.5) * a * 6))
		camera.CFrame *= decalageApplique
	end
	secousse *= math.exp(-dt * SECOUSSE_AMORTI)
end

-- Membre le plus éloigné du torse (main ou pied qui frappe, membres étirés).
local function membreLePlusLoin(modele: Model): BasePart?
	local torse = modele:FindFirstChild("UpperTorso")
	if not (torse and torse:IsA("BasePart")) then
		return nil
	end
	local meilleur: BasePart? = nil
	local distance = -1
	for _, nom in EXTREMITES do
		local part = modele:FindFirstChild(nom)
		if part and part:IsA("BasePart") then
			local d = (part.Position - torse.Position).Magnitude
			if d > distance then
				meilleur, distance = part, d
			end
		end
	end
	return meilleur
end

-- Traînée de coup : bande lumineuse de l'épaule (ou de la hanche) jusqu'au poing (ou au pied) qui frappe, qui
-- s'efface très vite (vitesse des coups étirés). Attribut TraineeMembre (Color3) d'un effet.
local RACINES = {
	RightHand = "RightUpperArm",
	LeftHand = "LeftUpperArm",
	RightFoot = "RightUpperLeg",
	LeftFoot = "LeftUpperLeg",
}
local INFO_TRAINEE = TweenInfo.new(0.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
local function traineeMembre(modele: Model, couleur: Color3)
	local membre = membreLePlusLoin(modele)
	local racine = membre and modele:FindFirstChild(RACINES[membre.Name] or "")
	if not (membre and racine and racine:IsA("BasePart")) then
		return
	end
	local a, b = racine.Position, membre.Position
	local longueur = (b - a).Magnitude
	if longueur < 1 then
		return
	end
	local largeur = math.min(racine.Size.X, racine.Size.Z) * 0.9
	local part = Instance.new("Part")
	part.Name = "TraineeCoup"
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	part.Material = Enum.Material.Neon
	part.Color = couleur
	part.Transparency = 0.35
	part.Size = Vector3.new(largeur, largeur, longueur)
	part.CFrame = CFrame.lookAt((a + b) / 2, b)
	part.Parent = workspace
	TweenService:Create(part, INFO_TRAINEE, {
		Transparency = 1,
		Size = Vector3.new(largeur * 1.8, largeur * 1.8, longueur * 1.05),
	}):Play()
	Debris:AddItem(part, INFO_TRAINEE.Time + 0.05)
end

-- Image rémanente (esquives) : copie fantôme des pièces visibles, couleur `couleur`, qui s'efface.
local function fantome(modele: Model, couleur: Color3)
	local dossier = Instance.new("Model")
	dossier.Name = "Fantome"
	for _, part in modele:GetDescendants() do
		if part:IsA("BasePart") and part.Transparency < 0.9 and part.Size.Magnitude > 0.6 then
			local copie = part:Clone()
			copie:ClearAllChildren()
			copie.Anchored = true
			copie.CanCollide = false
			copie.CanQuery = false
			copie.CanTouch = false
			copie.CastShadow = false
			copie.Material = Enum.Material.Neon
			copie.Color = couleur
			copie.Transparency = 0.55
			if copie:IsA("MeshPart") then
				copie.TextureID = ""
			end
			copie.CFrame = part.CFrame
			copie.Parent = dossier
			TweenService:Create(copie, INFO_FANTOME, { Transparency = 1 }):Play()
		end
	end
	dossier.Parent = workspace
	Debris:AddItem(dossier, INFO_FANTOME.Time + 0.05)
end

-- Marqueur « VFX <Nom> » (ou marqueur de gameplay → effet « <Marqueur>_<Valeur> ») sur le dossier VFX.<Nom> :
--   Mode "Burst" : Emit(Quantite) de chaque émetteur, lumières allumées DureeFlash s (0,1 par défaut) ;
--   Mode "Duree" : tout allumé Duree secondes (attribut Montee : débit des émetteurs de 0 à sa valeur en Montee s) ;
--   Mode "Eteindre" : éteint l'effet nommé par l'attribut Cible.
--   Attributs facultatifs : Secousse (amplitude de la secousse de caméra), Fantome (Color3 de l'image rémanente),
--   TraineeMembre (Color3 : traînée de l'épaule / hanche au membre qui frappe), AuMembre (effets placés sur ce membre).
-- Marqueur « VFX <Nom>_Fin » : éteint l'effet <Nom>.
local function declencher(modele: Model, nom: string)
	local vfx = modele:FindFirstChild("VFX")
	if not vfx then
		return
	end
	local base = string.match(nom, "^(.+)_Fin$")
	if base and not vfx:FindFirstChild(nom) then
		eteindre(vfx, base)
		return
	end

	local dossier = vfx:FindFirstChild(nom)
	if not dossier then
		return
	end
	local amplitude = dossier:GetAttribute("Secousse")
	if typeof(amplitude) == "number" then
		secouer(modele, amplitude)
	end
	local couleurTrainee = dossier:GetAttribute("TraineeMembre")
	if typeof(couleurTrainee) == "Color3" then
		traineeMembre(modele, couleurTrainee)
	end
	local couleurFantome = dossier:GetAttribute("Fantome")
	if typeof(couleurFantome) == "Color3" then
		fantome(modele, couleurFantome)
	end
	if dossier:GetAttribute("AuMembre") == true then
		-- effets dans des Attachment : déplacés sur la main ou le pied qui frappe
		local membre = membreLePlusLoin(modele)
		if membre then
			for _, effet in emetteurs(dossier) do
				local attache = effet.Parent
				if attache and attache:IsA("Attachment") then
					attache.WorldPosition = membre.Position
				end
			end
		end
	end
	local mode = dossier:GetAttribute("Mode")
	if mode == "Eteindre" then
		local cible = dossier:GetAttribute("Cible")
		if typeof(cible) == "string" then
			eteindre(vfx, cible)
		end
	elseif mode == "Burst" then
		local dureeFlash = dossier:GetAttribute("DureeFlash")
		for _, emetteur in emetteurs(dossier) do
			if emetteur:IsA("ParticleEmitter") then
				local quantite = emetteur:GetAttribute("Quantite")
				emetteur:Emit(if typeof(quantite) == "number" then quantite else 1)
			elseif emetteur:IsA("Light") then
				emetteur.Enabled = true
				task.delay(if typeof(dureeFlash) == "number" then dureeFlash else 0.1, function()
					emetteur.Enabled = false
				end)
			end
		end
	elseif mode == "Duree" then
		local duree = dossier:GetAttribute("Duree")
		local montee = dossier:GetAttribute("Montee")
		for _, emetteur in emetteurs(dossier) do
			if typeof(montee) == "number" and emetteur:IsA("ParticleEmitter") then
				-- montée en puissance : débit de 0 à sa valeur d'origine en `montee` secondes
				local debit = emetteur:GetAttribute("DebitBase")
				if typeof(debit) ~= "number" then
					debit = emetteur.Rate
					emetteur:SetAttribute("DebitBase", debit)
				end
				emetteur.Rate = 0
				TweenService:Create(emetteur, TweenInfo.new(montee, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
					Rate = debit,
				}):Play()
			end
			allumer(emetteur, true)
			task.delay(if typeof(duree) == "number" then duree else 1, function()
				if emetteur.Parent then
					allumer(emetteur, false)
				end
			end)
		end
	end
end

local suivis: { [Instance]: boolean } = setmetatable({}, { __mode = "k" }) :: any

local function suivre(instance: Instance)
	if not instance:IsA("Model") or suivis[instance] then
		return
	end
	suivis[instance] = true
	local modele = instance
	local controleur = modele:FindFirstChildOfClass("AnimationController") or modele:FindFirstChildOfClass("Humanoid")
	local animator = controleur and controleur:WaitForChild("Animator", 10)
	if not (animator and animator:IsA("Animator")) then
		return
	end
	task.spawn(Elastique.Suivre, modele)

	-- premières animations du cycle : les accessoires y repartent de leur état par défaut
	local debutsDeCycle: { unknown } = {}
	for _, attribut in { "AnimationIdle", "AnimationSequence" } do
		local id = modele:GetAttribute(attribut)
		if id ~= nil then
			table.insert(debutsDeCycle, id)
		end
	end
	local connexions: { RBXScriptConnection } = {}
	-- le serveur relance les mêmes pistes à chaque cycle : AnimationPlayed se redéclenche, ne brancher qu'une fois
	local pistesBranchees: { [AnimationTrack]: boolean } = {}
	table.insert(
		connexions,
		animator.AnimationPlayed:Connect(function(piste: AnimationTrack)
			if piste.Animation and table.find(debutsDeCycle, piste.Animation.AnimationId) then
				reinitialiserAccessoires(modele)
				Elastique.Reinitialiser(modele)
			end
			if pistesBranchees[piste] then
				return
			end
			pistesBranchees[piste] = true
			table.insert(
				connexions,
				piste:GetMarkerReachedSignal("Montrer"):Connect(function(nom: string)
					montrer(modele, nom, true)
				end)
			)
			table.insert(
				connexions,
				piste:GetMarkerReachedSignal("Cacher"):Connect(function(nom: string)
					montrer(modele, nom, false)
				end)
			)
			table.insert(
				connexions,
				piste:GetMarkerReachedSignal("VFX"):Connect(function(nom: string)
					declencher(modele, nom)
				end)
			)
			for _, marqueur in MARQUEURS_ELASTIQUE do
				table.insert(
					connexions,
					piste:GetMarkerReachedSignal(marqueur):Connect(function(valeur: string)
						Elastique.Marqueur(modele, marqueur, valeur)
					end)
				)
			end
			for _, marqueur in MARQUEURS_EFFETS do
				table.insert(
					connexions,
					piste:GetMarkerReachedSignal(marqueur):Connect(function(valeur: string)
						declencher(modele, `{marqueur}_{valeur}`)
					end)
				)
			end
		end)
	)
	table.insert(
		connexions,
		modele.Destroying:Connect(function()
			for _, connexion in connexions do
				connexion:Disconnect()
			end
		end)
	)
end

function Vitrine.Init()
	for _, instance in CollectionService:GetTagged(TAG_VITRINE) do
		task.spawn(suivre, instance)
	end
	CollectionService:GetInstanceAddedSignal(TAG_VITRINE):Connect(suivre)
	-- après la mise à jour de la caméra du joueur, pour que la secousse ne soit pas écrasée
	RunService:BindToRenderStep("SecousseVitrineRetrait", Enum.RenderPriority.Camera.Value - 1, retirerSecousse)
	RunService:BindToRenderStep("SecousseVitrine", Enum.RenderPriority.Camera.Value + 1, appliquerSecousse)
	Elastique.Init()
end

return Vitrine
