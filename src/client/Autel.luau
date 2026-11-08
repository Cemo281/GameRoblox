--!strict
-- Autel : affichage de l'autel d'invocation (machine de tirage) de chaque base, côté client.
-- Modèle construit par assets/autel/construire_autel.luau (tag "AutelInvocation").
-- Lit les attributs posés par le serveur sur le modèle :
--   Level (1 à 10) : niveaux N2..N10 visibles (cumulatif), réglages de lumière, rotation et faisceau ;
--   Rarete (Id de GachaConfig) : couleur de tout ce qui est tagué "AutelRarete" (néons, faisceau, lumière, étincelles) ;
--     absent = autel éteint (néons gris mats, lumière et faisceau coupés, carte immobile) ;
--   FinRecharge (heure serveur, Workspace:GetServerTimeNow) : compte à rebours au-dessus du toit ;
--   Echelle : facteur appliqué aux cotes de la spec par le script de construction.
-- Anime la carte géante (rotation + flottement), le halo (N6) et les cartes en orbite (N7 à N9).
-- Purement visuel : rien n'est envoyé au serveur.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local GachaConfig = require(ReplicatedStorage.Shared.GachaConfig)

local Autel = {}

local TAG = "AutelInvocation"
local TAG_RARETE = "AutelRarete"
local DISTANCE_ANIMATION = 250 -- au-delà, plus d'animation ni de compte à rebours (économie)

-- Autel éteint : tubes de verre gris mat, losange de la carte terne
local COULEUR_ETEINT = Color3.fromHex("6B7085")
local COULEUR_LOSANGE_ETEINT = Color3.fromHex("9A9EAE")
local COULEUR_PRET = Color3.fromHex("7CE38B")
local COULEUR_RECHARGE = Color3.fromHex("FFFFFF")

-- Réglages par niveau (spec de l'autel) : lumière de la carte, rotation (rad/s), transparence du faisceau
local CONFIG: { [number]: { lumiere: number, rotation: number, faisceau: number } } = {
	[1] = { lumiere = 3, rotation = 0.6, faisceau = 0.78 },
	[2] = { lumiere = 3.5, rotation = 0.6, faisceau = 0.78 },
	[3] = { lumiere = 3.5, rotation = 0.6, faisceau = 0.78 },
	[4] = { lumiere = 3.5, rotation = 0.6, faisceau = 0.72 },
	[5] = { lumiere = 4.5, rotation = 0.6, faisceau = 0.72 },
	[6] = { lumiere = 4.5, rotation = 0.7, faisceau = 0.72 },
	[7] = { lumiere = 4.5, rotation = 0.7, faisceau = 0.72 },
	[8] = { lumiere = 4.5, rotation = 0.7, faisceau = 0.65 },
	[9] = { lumiere = 5.5, rotation = 0.8, faisceau = 0.65 },
	[10] = { lumiere = 6, rotation = 0.8, faisceau = 0.65 },
}
-- Cartes en orbite visibles (Index 0 à 5) : 2 opposées, puis 2 paires, puis toutes
local ORBITES: { [number]: { [number]: boolean } } = {
	[7] = { [0] = true, [3] = true },
	[8] = { [0] = true, [1] = true, [3] = true, [4] = true },
}

type Orbite = { modele: Model, index: number }
type Etat = {
	modele: Model,
	origine: CFrame, -- sol au centre de l'autel
	echelle: number,
	carte: Model?,
	halo: Model?,
	orbites: { Orbite },
	recharge: BillboardGui?,
	texteRecharge: TextLabel?,
	angleCarte: number,
	rotation: number,
	niveau: number,
	allume: boolean,
	connexions: { RBXScriptConnection },
}

local etats: { [Model]: Etat } = {}

local function niveauDe(modele: Model): number
	local n = modele:GetAttribute("Level")
	return if typeof(n) == "number" then math.clamp(math.floor(n), 1, 10) else 1
end

-- Visibilité d'un objet des dossiers Niveaux.N2..N10 au niveau donné
local function visibleAuNiveau(d: Instance, n: number, niveau: number): boolean
	if n > niveau then
		return false
	end
	-- N7 contient les 6 cartes en orbite : seules celles du niveau sont montrées
	local orbite = d:FindFirstAncestorWhichIsA("Model")
	local index = orbite and orbite:GetAttribute("Index")
	if typeof(index) == "number" and niveau < 9 then
		local liste = ORBITES[niveau]
		return liste ~= nil and liste[index] == true
	end
	return true
end

-- Applique niveau et rareté (allumé ou éteint) en une passe : les deux décident de Enabled.
local function appliquer(etat: Etat)
	local modele = etat.modele
	local niveau = niveauDe(modele)
	local id = modele:GetAttribute("Rarete")
	local rarete = if typeof(id) == "string" then GachaConfig.RaretesParId[id] else nil
	local allume = rarete ~= nil
	etat.niveau = niveau
	etat.allume = allume

	-- niveau de chaque objet : 1 hors du dossier Niveaux, n dans Niveaux.N<n>
	local niveaux = modele:FindFirstChild("Niveaux")
	local niveauObjet: { [Instance]: number } = {}
	if niveaux then
		for n = 2, 10 do
			local dossier = niveaux:FindFirstChild(`N{n}`)
			if dossier then
				for _, d in dossier:GetDescendants() do
					niveauObjet[d] = n
				end
			end
		end
	end

	for _, d in modele:GetDescendants() do
		local n = niveauObjet[d]
		local visible = if n then visibleAuNiveau(d, n, niveau) else true
		local tague = CollectionService:HasTag(d, TAG_RARETE)
		if d:IsA("BasePart") then
			if n then
				local base = d:GetAttribute("BaseTransparency")
				d.Transparency = if visible then (if typeof(base) == "number" then base else 0) else 1
			end
			if tague then
				-- matière allumée posée par le script de construction (l'autel est enregistré éteint)
				local nom = d:GetAttribute("MateriauAllume")
				local forceField = nom == "ForceField"
				if allume and rarete then
					d.Color = rarete.Couleur
					d.Material = if forceField then Enum.Material.ForceField else Enum.Material.Neon
				else
					d.Color = COULEUR_ETEINT
					d.Material = if forceField then Enum.Material.ForceField else Enum.Material.SmoothPlastic
				end
			elseif d.Name == "Carte_Geante_Losange" then
				d.Color = if allume then Color3.fromHex("FFF3DC") else COULEUR_LOSANGE_ETEINT
				d.Material = if allume then Enum.Material.Neon else Enum.Material.SmoothPlastic
			end
		elseif d:IsA("Light") or d:IsA("ParticleEmitter") or d:IsA("Beam") then
			local effet: any = d
			effet.Enabled = visible and (allume or not tague)
			if tague and rarete then
				if d:IsA("Light") then
					d.Color = rarete.Couleur
				else
					(d :: any).Color = ColorSequence.new(rarete.Couleur)
				end
			end
		elseif d:IsA("BillboardGui") and n then
			d.Enabled = visible
		end
	end

	local c = CONFIG[niveau]
	etat.rotation = c.rotation
	local coeur = modele:FindFirstChild("Autel_Coeur", true)
	if coeur then
		local lumiere = coeur:FindFirstChild("LumiereCarte", true)
		if lumiere and lumiere:IsA("PointLight") then
			lumiere.Brightness = c.lumiere
		end
		local faisceau = coeur:FindFirstChildWhichIsA("Beam")
		if faisceau then
			faisceau.Transparency = NumberSequence.new(c.faisceau)
		end
	end
end

local function retirer(instance: Instance)
	local etat = if instance:IsA("Model") then etats[instance] else nil
	if not etat then
		return
	end
	for _, connexion in etat.connexions do
		connexion:Disconnect()
	end
	etats[instance :: Model] = nil
end

local function ajouter(instance: Instance)
	if not instance:IsA("Model") or etats[instance] then
		return
	end
	local estrade = instance:FindFirstChild("Estrade_Base", true)
	if not estrade or not estrade:IsA("BasePart") then
		return -- pas encore chargé (le modèle arrive d'un bloc : ModelStreamingMode Atomic)
	end
	local carte = instance:FindFirstChild("Carte_Geante")
	local halo = instance:FindFirstChild("Halo", true)
	local recharge = instance:FindFirstChild("Recharge", true)
	local orbites: { Orbite } = {}
	for _, d in instance:GetDescendants() do
		local index = d:GetAttribute("Index")
		if d:IsA("Model") and typeof(index) == "number" and d.Name:match("^Carte_Orbite") then
			table.insert(orbites, { modele = d, index = index })
		end
	end
	local echelle = instance:GetAttribute("Echelle")
	local billboard = if recharge and recharge:IsA("BillboardGui") then recharge else nil
	local texte = billboard and billboard:FindFirstChildWhichIsA("TextLabel")

	local etat: Etat = {
		modele = instance,
		origine = estrade.CFrame * CFrame.new(0, -estrade.Size.Y / 2, 0),
		echelle = if typeof(echelle) == "number" then echelle else 1,
		carte = if carte and carte:IsA("Model") then carte else nil,
		halo = if halo and halo:IsA("Model") then halo else nil,
		orbites = orbites,
		recharge = billboard,
		texteRecharge = texte,
		angleCarte = 0,
		rotation = 0.6,
		niveau = 1,
		allume = false,
		connexions = {},
	}
	etats[instance] = etat
	appliquer(etat)
	for _, attribut in { "Level", "Rarete" } do
		table.insert(
			etat.connexions,
			instance:GetAttributeChangedSignal(attribut):Connect(function()
				appliquer(etat)
			end)
		)
	end
end

local function animer(etat: Etat, t: number, dt: number)
	if not etat.allume then
		return -- éteint : la carte reste immobile
	end
	local o = etat.origine
	local e = etat.echelle
	etat.angleCarte = (etat.angleCarte + dt * etat.rotation) % (2 * math.pi)
	if etat.carte then
		etat.carte:PivotTo(
			o
				* CFrame.new(Vector3.new(0, 6.4 + math.sin(t * 1.3) * 0.15, -0.5) * e)
				* CFrame.Angles(0, etat.angleCarte, 0)
		)
	end
	if etat.niveau >= 6 and etat.halo then
		etat.halo:PivotTo(o * CFrame.new(Vector3.new(0, 6.4, -1.3) * e) * CFrame.Angles(0, 0, -t * 0.4))
	end
	if etat.niveau >= 7 then
		for _, orbite in etat.orbites do
			local a = t * 0.45 + orbite.index * (2 * math.pi / 6)
			local position =
				Vector3.new(math.cos(a) * 3.1, 6.4 + math.sin(t * 1.5 + orbite.index) * 0.4, -0.5 + math.sin(a) * 3.1)
			orbite.modele:PivotTo(o * CFrame.new(position * e) * CFrame.Angles(0, -a + math.pi / 2, 0))
		end
	end
end

-- Compte à rebours au-dessus du toit : affiché seulement si la base a un propriétaire
local function afficherRecharge(etat: Etat)
	local billboard, texte = etat.recharge, etat.texteRecharge
	if not billboard or not texte then
		return
	end
	local base = etat.modele.Parent
	local occupee = base ~= nil and base:GetAttribute("Proprietaire") ~= nil
	billboard.Enabled = occupee
	if not occupee then
		return
	end
	local fin = etat.modele:GetAttribute("FinRecharge")
	local reste = if typeof(fin) == "number" then fin - Workspace:GetServerTimeNow() else 0
	local libelle = if reste > 0 then `RECHARGE {math.ceil(reste)} s` else "PRÊT !"
	if texte.Text ~= libelle then
		texte.Text = libelle
		texte.TextColor3 = if reste > 0 then COULEUR_RECHARGE else COULEUR_PRET
	end
end

function Autel.Init()
	for _, instance in CollectionService:GetTagged(TAG) do
		ajouter(instance)
	end
	CollectionService:GetInstanceAddedSignal(TAG):Connect(function(instance)
		-- les descendants peuvent arriver juste après le modèle
		task.defer(ajouter, instance)
	end)
	CollectionService:GetInstanceRemovedSignal(TAG):Connect(retirer)

	RunService.Heartbeat:Connect(function(dt: number)
		local camera = Workspace.CurrentCamera
		local t = os.clock()
		for modele, etat in etats do
			if not modele.Parent then
				continue
			end
			if camera and (camera.CFrame.Position - etat.origine.Position).Magnitude > DISTANCE_ANIMATION then
				continue
			end
			animer(etat, t, dt)
			afficherRecharge(etat)
		end
	end)
end

return Autel
