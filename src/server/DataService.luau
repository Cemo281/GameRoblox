--!strict
-- DataService : charge, sauvegarde et expose les données persistantes des joueurs.
-- Toute modification des données passe par ce module, côté serveur uniquement.

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Economie = require(ReplicatedStorage.Shared.Economie)

local DataService = {}

-- Format sauvegardé sous la clé "Player_<UserId>". Demander avant de le modifier.
export type PersonnageSauve = {
	Id: string,
	Etoiles: number,
}

export type PlayerData = {
	Version: number,
	Argent: number,
	ArgentNonCollecte: number,
	Personnages: { [string]: PersonnageSauve }, -- clé : uid
	Emplacements: { [string]: string }, -- clé : index de l'emplacement en texte, valeur : uid
	EmplacementsDebloques: number,
	NiveauMachine: number,
	Rebirths: number,
	ProchainUid: number,
}

type Profile = {
	data: PlayerData,
	argentValue: IntValue,
	canSave: boolean, -- false si le chargement a échoué en Studio : on ne doit pas écraser la sauvegarde
	saveEnCours: boolean, -- une seule sauvegarde à la fois par joueur
}

local DATA_VERSION = 2
local STORE_NAME = "PlayerData"
local MAX_RETRIES = 3
local AUTOSAVE_INTERVAL = 120

local store = DataStoreService:GetDataStore(STORE_NAME)
local profiles: { [Player]: Profile } = {}
local sauvegardesEnCours = 0
local callbacksChargement: { (Player, PlayerData) -> () } = {}
local initialized = false

local function defaultData(): PlayerData
	return {
		Version = DATA_VERSION,
		Argent = 0,
		ArgentNonCollecte = 0,
		Personnages = {},
		Emplacements = {},
		EmplacementsDebloques = Economie.EmplacementsDepart,
		NiveauMachine = 0,
		Rebirths = 0,
		ProchainUid = 1,
	}
end

local function keyFor(player: Player): string
	return `Player_{player.UserId}`
end

local function isValidAmount(amount: number): boolean
	return amount == amount and amount > 0 and amount ~= math.huge
end

local function nombre(valeur: any, defaut: number): number
	if typeof(valeur) == "number" and valeur == valeur and math.abs(valeur) ~= math.huge then
		return valeur
	end
	return defaut
end

-- Lit une sauvegarde (v1 ou v2) champ par champ : une valeur invalide reprend sa valeur par défaut.
local function lireDonnees(brut: any): PlayerData
	local data = defaultData()
	if typeof(brut) ~= "table" then
		return data
	end

	data.Argent = math.max(0, math.floor(nombre(brut.Argent, 0)))
	data.ArgentNonCollecte = math.max(0, nombre(brut.ArgentNonCollecte, 0))
	data.EmplacementsDebloques = math.clamp(
		math.floor(nombre(brut.EmplacementsDebloques, Economie.EmplacementsDepart)),
		Economie.EmplacementsDepart,
		Economie.EmplacementsMax
	)
	data.NiveauMachine = math.max(0, math.floor(nombre(brut.NiveauMachine, 0)))
	data.Rebirths = math.max(0, math.floor(nombre(brut.Rebirths, 0)))

	local prochainUid = math.max(1, math.floor(nombre(brut.ProchainUid, 1)))
	if typeof(brut.Personnages) == "table" then
		for uid, personnage in brut.Personnages do
			if
				typeof(uid) == "string"
				and typeof(personnage) == "table"
				and typeof(personnage.Id) == "string"
				and typeof(personnage.Etoiles) == "number"
			then
				data.Personnages[uid] = {
					Id = personnage.Id,
					Etoiles = math.clamp(math.floor(personnage.Etoiles), Economie.EtoilesMin, Economie.EtoilesMax),
				}
				local numero = tonumber(uid)
				if numero and numero >= prochainUid then
					prochainUid = math.floor(numero) + 1
				end
			end
		end
	end
	data.ProchainUid = prochainUid

	if typeof(brut.Emplacements) == "table" then
		local dejaPose: { [string]: boolean } = {}
		for index, uid in brut.Emplacements do
			local numero = tonumber(index)
			if
				typeof(index) == "string"
				and typeof(uid) == "string"
				and numero
				and tostring(numero) == index
				and numero % 1 == 0
				and numero >= 1
				and numero <= data.EmplacementsDebloques
				and data.Personnages[uid]
				and not dejaPose[uid]
			then
				data.Emplacements[index] = uid
				dejaPose[uid] = true
			end
		end
	end

	return data
end

local function copier(data: PlayerData): PlayerData
	local copie = table.clone(data)
	copie.Personnages = {}
	for uid, personnage in data.Personnages do
		copie.Personnages[uid] = table.clone(personnage)
	end
	copie.Emplacements = table.clone(data.Emplacements)
	return copie
end

-- Une sauvegarde d'une version plus récente (serveur pas encore mis à jour) ne doit être ni lue ni écrasée.
local function estPlusRecente(brut: any): boolean
	return typeof(brut) == "table" and typeof(brut.Version) == "number" and brut.Version > DATA_VERSION
end

-- Renvoie nil si le DataStore est inaccessible après plusieurs essais, ou si la sauvegarde
-- ne peut pas être lue sans risque (version plus récente, type inattendu) : on ne doit pas l'écraser.
local function loadData(player: Player): PlayerData?
	for attempt = 1, MAX_RETRIES do
		local ok, result = pcall(function()
			return store:GetAsync(keyFor(player))
		end)
		if ok then
			if result ~= nil and typeof(result) ~= "table" then
				warn(`[DataService] Données de type inattendu pour {player.Name}, sauvegarde non chargée`)
				return nil
			end
			if estPlusRecente(result) then
				warn(`[DataService] Sauvegarde plus récente que ce serveur pour {player.Name}`)
				return nil
			end
			return lireDonnees(result)
		end
		warn(`[DataService] Chargement échoué pour {player.Name} (essai {attempt}) : {result}`)
		if attempt < MAX_RETRIES then
			task.wait(attempt * 2)
		end
	end
	return nil
end

local function saveProfile(player: Player, profile: Profile)
	if not profile.canSave then
		return
	end
	sauvegardesEnCours += 1

	-- Les sauvegardes d'un même joueur passent l'une après l'autre ; chacune copie les données
	-- au moment où elle démarre, donc la dernière écrite est toujours la plus récente.
	while profile.saveEnCours do
		task.wait()
	end
	profile.saveEnCours = true

	local snapshot = copier(profile.data)
	for attempt = 1, MAX_RETRIES do
		local ok, err = pcall(function()
			store:UpdateAsync(keyFor(player), function(ancien)
				if estPlusRecente(ancien) then
					return nil -- annule l'écriture
				end
				return snapshot
			end)
		end)
		if ok then
			break
		end
		warn(`[DataService] Sauvegarde échouée pour {player.Name} (essai {attempt}) : {err}`)
		if attempt < MAX_RETRIES then
			task.wait(attempt * 2)
		end
	end

	profile.saveEnCours = false
	sauvegardesEnCours -= 1
end

local function setArgent(profile: Profile, value: number)
	profile.data.Argent = value
	profile.argentValue.Value = value
end

local function onPlayerAdded(player: Player)
	local data = loadData(player)
	local canSave = true

	if not data then
		if not RunService:IsStudio() then
			player:Kick("Impossible de charger tes données. Réessaie dans quelques instants.")
			return
		end
		-- En Studio, l'accès aux API est peut-être désactivé : on joue sans sauvegarder.
		warn("[DataService] DataStore indisponible en Studio : la partie ne sera pas sauvegardée")
		data = defaultData()
		canSave = false
	end
	assert(data, "data est défini à ce stade")

	-- Le joueur a pu partir pendant le chargement
	if player.Parent ~= Players then
		return
	end

	local leaderstats = Instance.new("Folder")
	leaderstats.Name = "leaderstats"

	local argentValue = Instance.new("IntValue")
	argentValue.Name = "Argent"
	argentValue.Value = data.Argent
	argentValue.Parent = leaderstats

	leaderstats.Parent = player

	profiles[player] = { data = data, argentValue = argentValue, canSave = canSave, saveEnCours = false }
	for _, callback in callbacksChargement do
		task.spawn(callback, player, data)
	end
end

local function onPlayerRemoving(player: Player)
	local profile = profiles[player]
	if not profile then
		return
	end
	profiles[player] = nil
	saveProfile(player, profile)
end

-- Fermeture du serveur : lance les sauvegardes restantes et attend toutes celles en cours,
-- y compris celles lancées par PlayerRemoving (dont le profil n'est déjà plus dans `profiles`).
local function saveAll()
	for player, profile in profiles do
		task.spawn(saveProfile, player, profile)
	end
	while sauvegardesEnCours > 0 do
		task.wait()
	end
end

function DataService.Init()
	if initialized then
		return
	end
	initialized = true

	Players.PlayerAdded:Connect(onPlayerAdded)
	Players.PlayerRemoving:Connect(onPlayerRemoving)
	for _, player in Players:GetPlayers() do
		task.spawn(onPlayerAdded, player)
	end

	game:BindToClose(saveAll)

	task.spawn(function()
		while true do
			task.wait(AUTOSAVE_INTERVAL)
			for player, profile in profiles do
				task.spawn(saveProfile, player, profile)
			end
		end
	end)
end

-- Appelle `callback` dès que les données d'un joueur sont chargées (y compris pour ceux déjà chargés).
function DataService.OnChargement(callback: (Player, PlayerData) -> ())
	table.insert(callbacksChargement, callback)
	for player, profile in profiles do
		task.spawn(callback, player, profile.data)
	end
end

-- Lecture seule par convention : modifier les données via les fonctions ci-dessous.
function DataService.GetData(player: Player): PlayerData?
	local profile = profiles[player]
	return if profile then profile.data else nil
end

-- Renvoie nil si les données du joueur ne sont pas (encore) chargées.
function DataService.GetArgent(player: Player): number?
	local profile = profiles[player]
	return if profile then profile.data.Argent else nil
end

function DataService.AddArgent(player: Player, amount: number): boolean
	local profile = profiles[player]
	if not profile or not isValidAmount(amount) then
		return false
	end
	setArgent(profile, profile.data.Argent + math.floor(amount))
	return true
end

-- Renvoie false (sans rien retirer) si le joueur n'a pas assez d'argent.
function DataService.SpendArgent(player: Player, amount: number): boolean
	local profile = profiles[player]
	if not profile or not isValidAmount(amount) then
		return false
	end
	local cost = math.floor(amount)
	if profile.data.Argent < cost then
		return false
	end
	setArgent(profile, profile.data.Argent - cost)
	return true
end

function DataService.NombrePersonnages(player: Player): number
	local profile = profiles[player]
	local nombrePersonnages = 0
	if profile then
		for _ in profile.data.Personnages do
			nombrePersonnages += 1
		end
	end
	return nombrePersonnages
end

-- Ajoute un personnage à l'inventaire. Renvoie son uid, ou nil si les données ne sont pas chargées
-- ou si le joueur a atteint `Economie.PersonnagesMax`.
function DataService.AjouterPersonnage(player: Player, id: string, etoiles: number): string?
	local profile = profiles[player]
	if not profile or DataService.NombrePersonnages(player) >= Economie.PersonnagesMax then
		return nil
	end
	local data = profile.data
	local uid = tostring(data.ProchainUid)
	data.ProchainUid += 1
	data.Personnages[uid] = {
		Id = id,
		Etoiles = math.clamp(math.floor(etoiles), Economie.EtoilesMin, Economie.EtoilesMax),
	}
	return uid
end

-- Pose un personnage de l'inventaire sur un emplacement débloqué et libre.
function DataService.Poser(player: Player, uid: string, index: number): boolean
	local profile = profiles[player]
	if not profile then
		return false
	end
	local data = profile.data
	if not data.Personnages[uid] or index < 1 or index > data.EmplacementsDebloques or index % 1 ~= 0 then
		return false
	end
	if data.Emplacements[tostring(index)] then
		return false
	end
	for _, uidPose in data.Emplacements do
		if uidPose == uid then
			return false
		end
	end
	data.Emplacements[tostring(index)] = uid
	return true
end

-- Retire un personnage posé et le remet dans l'inventaire. Renvoie false s'il n'était pas posé.
function DataService.Retirer(player: Player, uid: string): boolean
	local profile = profiles[player]
	if not profile then
		return false
	end
	local emplacements = profile.data.Emplacements
	for index, uidPose in emplacements do
		if uidPose == uid then
			emplacements[index] = nil
			return true
		end
	end
	return false
end

-- Premier emplacement débloqué et libre, ou nil.
function DataService.PremierEmplacementLibre(player: Player): number?
	local profile = profiles[player]
	if not profile then
		return nil
	end
	local data = profile.data
	for index = 1, data.EmplacementsDebloques do
		if not data.Emplacements[tostring(index)] then
			return index
		end
	end
	return nil
end

function DataService.AjouterNonCollecte(player: Player, montant: number)
	local profile = profiles[player]
	if profile and isValidAmount(montant) then
		profile.data.ArgentNonCollecte += montant
	end
end

-- Transfère la partie entière de l'argent non collecté vers l'argent du joueur. Renvoie le montant collecté.
function DataService.Collecter(player: Player): number
	local profile = profiles[player]
	if not profile then
		return 0
	end
	local montant = math.floor(profile.data.ArgentNonCollecte)
	if montant <= 0 then
		return 0
	end
	profile.data.ArgentNonCollecte -= montant
	setArgent(profile, profile.data.Argent + montant)
	return montant
end

return DataService
