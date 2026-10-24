--!strict
-- DataService : charge, sauvegarde et expose les données persistantes des joueurs (argent).
-- Toute modification de l'argent passe par ce module, côté serveur uniquement.

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local DataService = {}

-- Format sauvegardé sous la clé "Player_<UserId>". Demander avant de le modifier.
export type PlayerData = {
	Version: number,
	Argent: number,
}

type Profile = {
	data: PlayerData,
	argentValue: IntValue,
	canSave: boolean, -- false si le chargement a échoué en Studio : on ne doit pas écraser la sauvegarde
}

local DATA_VERSION = 1
local STORE_NAME = "PlayerData"
local MAX_RETRIES = 3
local AUTOSAVE_INTERVAL = 120

local store = DataStoreService:GetDataStore(STORE_NAME)
local profiles: { [Player]: Profile } = {}
local initialized = false

local function defaultData(): PlayerData
	return { Version = DATA_VERSION, Argent = 0 }
end

local function keyFor(player: Player): string
	return `Player_{player.UserId}`
end

local function isValidAmount(amount: number): boolean
	return amount == amount and amount > 0 and amount ~= math.huge
end

-- Renvoie nil si le DataStore est inaccessible après plusieurs essais.
local function loadData(player: Player): PlayerData?
	for attempt = 1, MAX_RETRIES do
		local ok, result = pcall(function()
			return store:GetAsync(keyFor(player))
		end)
		if ok then
			if typeof(result) == "table" and typeof(result.Argent) == "number" then
				return { Version = DATA_VERSION, Argent = math.max(0, math.floor(result.Argent)) }
			end
			if result ~= nil then
				warn(`[DataService] Données invalides pour {player.Name}, remise à zéro`)
			end
			return defaultData()
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
	local snapshot: PlayerData = { Version = profile.data.Version, Argent = profile.data.Argent }
	for attempt = 1, MAX_RETRIES do
		local ok, err = pcall(function()
			store:UpdateAsync(keyFor(player), function()
				return snapshot
			end)
		end)
		if ok then
			return
		end
		warn(`[DataService] Sauvegarde échouée pour {player.Name} (essai {attempt}) : {err}`)
		if attempt < MAX_RETRIES then
			task.wait(attempt * 2)
		end
	end
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

	profiles[player] = { data = data, argentValue = argentValue, canSave = canSave }
end

local function onPlayerRemoving(player: Player)
	local profile = profiles[player]
	if not profile then
		return
	end
	profiles[player] = nil
	saveProfile(player, profile)
end

local function saveAll()
	local pending = 0
	for player, profile in profiles do
		pending += 1
		task.spawn(function()
			saveProfile(player, profile)
			pending -= 1
		end)
	end
	while pending > 0 do
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

return DataService
