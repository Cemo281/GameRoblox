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
-- Socles de la zone « Sanctuaire » (assets/zone/construire_zone.luau)
local COULEUR_SOCLE_LIBRE = Color3.fromHex("6C6A78")
local COULEUR_SOCLE_VERROUILLE = Color3.fromHex("3B3F52")
local TEXTE_SOCLE_LIBRE = "Socle libre"
local TEXTE_SOCLE_VERROUILLE = "🔒 Verrouillé"
local COULEUR_TEXTE_LIBRE = Color3.fromHex("B9B6C6")
local COULEUR_TEXTE_VERROUILLE = Color3.fromHex("8C8A99")
local NIVEAU_MAX_AUTEL = 10
local TAILLE_PERSONNAGE = Vector3.new(3, 5, 3)
local TAG_VITRINE = "PersonnageVitrine"
local VITRINE_PAUSE = 2 -- secondes entre deux animations de vitrine
local HIT_STOP = 0.06 -- arrêt sur image à chaque marqueur « Impact »

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

local function texte(parent: Instance?, nom: string): TextLabel?
	local label = parent and parent:FindFirstChild(nom, true)
	return if label and label:IsA("TextLabel") then label else nil
end

local function emplacementsDe(base: Model): { BasePart }
	local resultat = {}
	local socles = base:FindFirstChild("Socles")
	if socles then
		for _, socle in socles:GetChildren() do
			local emplacement = socle:FindFirstChild("Emplacement")
			if
				emplacement
				and emplacement:IsA("BasePart")
				and typeof(emplacement:GetAttribute("Index")) == "number"
			then
				table.insert(resultat, emplacement)
			end
		end
	end
	return resultat
end

-- Orientation d'un personnage posé : face à l'allée de sa base (axe x = 0 du repère du Centre, +Z vers l'entrée).
local function orientationVersAllee(emplacement: BasePart, position: Vector3): CFrame
	local base = trouverBase(emplacement)
	local centre = base and base:FindFirstChild("Centre")
	if centre and centre:IsA("BasePart") then
		local relatif = centre.CFrame:PointToObjectSpace(position)
		local direction = centre.CFrame:VectorToWorldSpace(Vector3.new(-relatif.X, 0, 0))
		if direction.Magnitude > 0.01 then
			return CFrame.lookAt(position, position + direction)
		end
	end
	return CFrame.new(position)
end

type EtatSocle = "Libre" | "Verrouille" | "Occupe"

-- Apparence d'un socle : anneau (néon à la couleur de la rareté s'il est occupé), lumière, étiquettes.
local function afficherSocle(
	emplacement: BasePart,
	etat: EtatSocle,
	couleur: Color3?,
	nom: string?,
	rarete: string?,
	gain: string?
)
	local socle = emplacement.Parent
	local anneau = socle and socle:FindFirstChild("Neon_Socle_Anneau")
	if anneau and anneau:IsA("BasePart") then
		anneau.Color = if etat == "Occupe"
			then couleur or COULEUR_SOCLE_LIBRE
			elseif etat == "Verrouille" then COULEUR_SOCLE_VERROUILLE
			else COULEUR_SOCLE_LIBRE
		anneau.Material = if etat == "Occupe" then Enum.Material.Neon else Enum.Material.SmoothPlastic
	end
	local lumiere = emplacement:FindFirstChildWhichIsA("PointLight", true)
	if lumiere then
		lumiere.Enabled = etat == "Occupe"
		lumiere.Color = couleur or lumiere.Color
	end

	local etiquette = emplacement:FindFirstChild("Etiquette")
	if etiquette and etiquette:IsA("BillboardGui") then
		etiquette.Enabled = etat == "Occupe"
		local labelNom, labelRarete, labelGain =
			texte(etiquette, "Nom"), texte(etiquette, "Rarete"), texte(etiquette, "Gain")
		if labelNom and labelRarete and labelGain then
			labelNom.Text = nom or ""
			labelRarete.Text = rarete or ""
			labelRarete.TextColor3 = couleur or labelRarete.TextColor3
			labelGain.Text = gain or ""
		end
	end
	local libre = emplacement:FindFirstChild("Libre")
	if libre and libre:IsA("BillboardGui") then
		libre.Enabled = etat ~= "Occupe"
		local label = texte(libre, "Texte")
		if label then
			label.Text = if etat == "Verrouille" then TEXTE_SOCLE_VERROUILLE else TEXTE_SOCLE_LIBRE
			label.TextColor3 = if etat == "Verrouille" then COULEUR_TEXTE_VERROUILLE else COULEUR_TEXTE_LIBRE
		end
	end
end

-- Panneau du propriétaire (nom + niveau de l'autel) et pupitre d'amélioration (niveau suivant).
local function afficherNiveau(base: Model, niveau: number?)
	local niveauPanneau = texte(base:FindFirstChild("Panneau"), "Niveau")
	if niveauPanneau then
		niveauPanneau.Text = if niveau then `Niveau {niveau}` else ""
	end
	local pupitre = base:FindFirstChild("Amelioration")
	local niveauPupitre = texte(pupitre, "Niveau")
	local prix = texte(pupitre, "Prix")
	local n = niveau or 1
	if niveauPupitre and prix then
		niveauPupitre.Text = if n >= NIVEAU_MAX_AUTEL then "MAX" else `Niv. {n} → {n + 1}`
		-- coût des niveaux à définir (docs/wiki/Machine-RNG.md) : pas encore d'achat
		prix.Text = if n >= NIVEAU_MAX_AUTEL then "" else "Bientôt"
	end
end

local function chargerPiste(animator: Animator, animationId: unknown): AnimationTrack?
	if typeof(animationId) ~= "string" then
		return nil
	end
	local animation = Instance.new("Animation")
	animation.AnimationId = animationId
	local piste = animator:LoadAnimation(animation)
	piste.Looped = false
	piste.Priority = Enum.AnimationPriority.Action
	return piste
end

-- Joue `piste` jusqu'à sa dernière image et l'y fige (la pose de repos du rig n'est pas la pose neutre).
-- Renvoie false si le modèle a disparu entre-temps.
local function jouerEtFiger(modele: Model, piste: AnimationTrack, precedente: AnimationTrack?): boolean
	if piste.IsPlaying then
		-- piste encore figée sur sa dernière image (vitrine à une seule animation) : repartir du début
		piste:Stop(0)
		piste.TimePosition = 0
	end
	piste:Play(0)
	if precedente and precedente ~= piste then
		precedente:Stop(0)
	end
	-- longueur inconnue tant que l'animation publiée n'est pas chargée
	while piste.Length == 0 do
		if not modele.Parent then
			return false
		end
		task.wait(0.1)
	end
	task.wait(math.max(0, piste.Length - piste.TimePosition - 0.05))
	-- les arrêts sur image (hit-stop) ont pu retarder la fin
	while modele.Parent and piste.IsPlaying and piste.TimePosition < piste.Length - 0.05 do
		task.wait()
	end
	piste:AdjustSpeed(0)
	piste.TimePosition = piste.Length * 0.999
	return modele.Parent ~= nil
end

-- Arrêt sur image à chaque marqueur « Impact » (coups de la séquence du sabreur) : attribut HitStop de l'effet
-- VFX.Impact_<valeur> du modèle (ex. plus long pour l'impact au sol), HIT_STOP sinon.
local function brancherHitStop(modele: Model, piste: AnimationTrack)
	piste:GetMarkerReachedSignal("Impact"):Connect(function(valeur: string)
		local vfx = modele:FindFirstChild("VFX")
		local effet = vfx and vfx:FindFirstChild(`Impact_{valeur}`)
		local duree = effet and effet:GetAttribute("HitStop")
		piste:AdjustSpeed(0)
		task.delay(if typeof(duree) == "number" then math.clamp(duree, 0, 0.3) else HIT_STOP, function()
			-- ne pas relancer une piste figée sur sa dernière image
			if piste.IsPlaying and piste.TimePosition < piste.Length - 0.1 then
				piste:AdjustSpeed(1)
			end
		end)
	end)
end

-- Vitrine d'un personnage posé : Idle, pause, Action, pause, Signature, pause, en boucle (VITRINE_PAUSE secondes).
-- Un personnage avec une AnimationSequence (ex. séquence du sabreur de zoro) la joue seule, en boucle avec pause.
-- Un personnage sans Action ni Signature joue seulement son Idle en boucle.
local function animerVitrine(modele: Model, animator: Animator)
	local sequence = chargerPiste(animator, modele:GetAttribute("AnimationSequence"))
	if sequence then
		brancherHitStop(modele, sequence)
		while modele.Parent do
			if not jouerEtFiger(modele, sequence, nil) then
				return
			end
			task.wait(VITRINE_PAUSE)
		end
		return
	end

	local idle = chargerPiste(animator, modele:GetAttribute("AnimationIdle"))
	if not idle then
		return
	end
	local action = chargerPiste(animator, modele:GetAttribute("AnimationAction"))
	local signature = chargerPiste(animator, modele:GetAttribute("AnimationSignature"))
	if not (action and signature) then
		idle.Looped = true
		idle.Priority = Enum.AnimationPriority.Idle
		idle:Play()
		return
	end
	local cycle = { idle, action, signature }
	local precedente: AnimationTrack? = nil
	while modele.Parent do
		for _, piste in cycle do
			if not jouerEtFiger(modele, piste, precedente) then
				return
			end
			precedente = piste
			task.wait(VITRINE_PAUSE)
			if not modele.Parent then
				return
			end
		end
	end
end

-- Modèle 3D animé (ReplicatedStorage.ModelesPersonnages.<Id>, rangé par le skill /perso-roblox), ou nil.
local function creerModele(emplacement: BasePart, id: string): Model?
	local dossier = ReplicatedStorage:FindFirstChild("ModelesPersonnages")
	local source = dossier and dossier:FindFirstChild(id)
	if not (source and source:IsA("Model") and source.PrimaryPart) then
		return nil
	end

	local modele = source:Clone()
	modele.Name = "Personnage"
	local boite, taille = modele:GetBoundingBox()
	local pivot = modele:GetPivot().Position
	local sousPivot = pivot.Y - (boite.Position.Y - taille.Y / 2)
	local position = emplacement.Position + Vector3.new(0, emplacement.Size.Y / 2 + sousPivot, 0)
	modele:PivotTo(orientationVersAllee(emplacement, position))
	modele.Parent = emplacement

	-- Animator dans un AnimationController (persos sans Humanoid) ou dans le Humanoid (persos habilles :
	-- un Humanoid et un AnimationController dans le meme modele se bloquent)
	local controleur = modele:FindFirstChildOfClass("AnimationController") or modele:FindFirstChildOfClass("Humanoid")
	local animator = controleur and controleur:FindFirstChildOfClass("Animator")
	if animator then
		-- le client (module Vitrine) y affiche sabres et effets a partir des marqueurs des animations
		CollectionService:AddTag(modele, TAG_VITRINE)
		task.spawn(animerVitrine, modele, animator)
	end

	return modele
end

-- Modèle 3D du personnage sur le socle (bloc coloré s'il n'a pas de modèle) ; l'étiquette est celle du socle.
local function creerPersonnage(emplacement: BasePart, id: string, couleur: Color3)
	local modele = creerModele(emplacement, id)
	if not modele then
		local part = Instance.new("Part")
		part.Name = "Personnage"
		part.Anchored = true
		part.Size = TAILLE_PERSONNAGE
		part.Color = couleur
		part.Material = Enum.Material.SmoothPlastic
		part.Position = emplacement.Position + Vector3.new(0, emplacement.Size.Y / 2 + TAILLE_PERSONNAGE.Y / 2, 0)
		part.Parent = emplacement
	end
end

-- Remet une base dans son apparence « libre ».
local function reinitialiserBase(base: Model)
	for _, emplacement in emplacementsDe(base) do
		local ancien = emplacement:FindFirstChild("Personnage")
		if ancien then
			ancien:Destroy()
		end
		afficherSocle(emplacement, "Libre")
	end
	local nom = texte(base:FindFirstChild("Panneau"), "NomProprietaire")
	if nom then
		nom.Text = TEXTE_BASE_LIBRE
	end
	afficherNiveau(base, nil)
	local autel = base:FindFirstChild("AutelInvocation")
	if autel then
		autel:SetAttribute("Level", 1)
		autel:SetAttribute("Rarete", nil) -- autel éteint jusqu'au premier tirage
		autel:SetAttribute("FinRecharge", nil)
	end
end

-- Niveau affiché par l'autel d'invocation (Autel.luau côté client) : niveau de la machine, de 1 à 10.
-- NiveauMachine vaut 0 tant que la machine n'a pas été améliorée → autel de base (niveau 1).
function BaseService.RafraichirAutel(player: Player)
	local base = basesParJoueur[player]
	local data = DataService.GetData(player)
	local autel = base and base:FindFirstChild("AutelInvocation")
	if base and data then
		local niveau = math.clamp(data.NiveauMachine, 1, NIVEAU_MAX_AUTEL)
		if autel then
			autel:SetAttribute("Level", niveau)
		end
		afficherNiveau(base, niveau)
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

			local nom = texte(instance:FindFirstChild("Panneau"), "NomProprietaire")
			if nom then
				nom.Text = player.DisplayName
			end

			connexionsApparition[player] = player.CharacterAdded:Connect(function(character)
				-- Laisse le personnage apparaître au SpawnLocation avant de le déplacer
				task.defer(teleporterALaBase, player, character)
			end)
			if player.Character then
				teleporterALaBase(player, player.Character)
			end

			BaseService.RafraichirEmplacements(player)
			BaseService.RafraichirAutel(player)
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

-- Ramène le personnage du joueur devant l'entrée de sa base (PointApparition). Renvoie false sans base ou sans perso.
function BaseService.TeleporterALaBase(player: Player): boolean
	local character = player.Character
	if not character or not basesParJoueur[player] then
		return false
	end
	teleporterALaBase(player, character)
	return true
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

		local uid = data.Emplacements[tostring(index)]
		local personnage = uid and data.Personnages[uid]
		local definition = personnage and Personnages.ParId[personnage.Id]
		if personnage and definition then
			local rarete = GachaConfig.RaretesParId[definition.Rarete]
			local couleur = if rarete then rarete.Couleur else Color3.new(1, 1, 1)
			local revenu = Economie.RevenuParSeconde(definition.Revenu, personnage.Etoiles, data.Rebirths)
			creerPersonnage(emplacement, definition.Id, couleur)
			afficherSocle(
				emplacement,
				"Occupe",
				couleur,
				`{definition.Nom} {string.rep("★", personnage.Etoiles)}`,
				if rarete then rarete.Nom else definition.Rarete,
				`{math.round(revenu * 10) / 10} $/s`
			)
		else
			afficherSocle(emplacement, if index <= data.EmplacementsDebloques then "Libre" else "Verrouille")
		end
	end
end

return BaseService
