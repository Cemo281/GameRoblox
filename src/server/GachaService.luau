--!strict
-- GachaService : tirage gratuit sur la machine RNG de sa base (Part taguée "MachineRNG") via un ProximityPrompt.
-- Le serveur vérifie propriétaire, distance et temps de recharge, puis tire rareté, personnage et étoiles.
-- Voir docs/wiki/Machine-RNG.md.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local Economie = require(ReplicatedStorage.Shared.Economie)
local GachaConfig = require(ReplicatedStorage.Shared.GachaConfig)
local Personnages = require(ReplicatedStorage.Shared.Personnages)
local BaseService = require(script.Parent.BaseService)
local DataService = require(script.Parent.DataService)

local GachaService = {}

local TAG_MACHINE = "MachineRNG"

local random = Random.new()
local dernierTirage: { [Player]: number } = {}
local machinesInstallees: { [BasePart]: boolean } = {}

local function choisirPondere<T>(options: { T }, poids: (T) -> number): T
	local total = 0
	for _, option in options do
		total += poids(option)
	end
	local tirage = random:NextNumber(0, total)
	for _, option in options do
		tirage -= poids(option)
		if tirage <= 0 then
			return option
		end
	end
	return options[#options]
end

-- Tire un personnage parmi les lots débloqués (1 lot de plus par rebirth).
local function tirerPersonnage(rebirths: number): (Personnages.Personnage, number)
	local candidatsParRarete: { [string]: { Personnages.Personnage } } = {}
	for _, personnage in Personnages.Liste do
		if personnage.Lot <= rebirths + 1 then
			local candidats = candidatsParRarete[personnage.Rarete] or {}
			table.insert(candidats, personnage)
			candidatsParRarete[personnage.Rarete] = candidats
		end
	end

	local raretesDisponibles = {}
	for _, rarete in GachaConfig.Raretes do
		if candidatsParRarete[rarete.Id] then
			table.insert(raretesDisponibles, rarete)
		end
	end

	local rarete = choisirPondere(raretesDisponibles, function(r)
		return r.Chance
	end)
	local candidats = candidatsParRarete[rarete.Id]
	local personnage = candidats[random:NextInteger(1, #candidats)]
	local etoiles = choisirPondere(GachaConfig.Etoiles, function(e)
		return e.Chance
	end).Etoiles
	return personnage, etoiles
end

local function premierEmplacementLibre(player: Player): number?
	local data = DataService.GetData(player)
	if not data then
		return nil
	end
	for index = 1, data.EmplacementsDebloques do
		if not data.Emplacements[tostring(index)] then
			return index
		end
	end
	return nil
end

-- Affichage provisoire du résultat au-dessus de la machine, en attendant l'animation de tirage.
local function afficherResultat(machine: BasePart, nom: string, etoiles: number, couleur: Color3)
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "ResultatTirage"
	billboard.Size = UDim2.fromOffset(240, 60)
	billboard.StudsOffset = Vector3.new(0, machine.Size.Y / 2 + 3, 0)
	billboard.AlwaysOnTop = true

	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Text = `{nom} {string.rep("★", etoiles)}`
	label.TextColor3 = couleur
	label.TextStrokeTransparency = 0
	label.TextScaled = true
	label.Font = Enum.Font.GothamBold
	label.Parent = billboard

	local ancien = machine:FindFirstChild("ResultatTirage")
	if ancien then
		ancien:Destroy()
	end
	billboard.Parent = machine
	task.delay(GachaConfig.DureeAnimation, function()
		if billboard.Parent then
			billboard:Destroy()
		end
	end)
end

-- Effectue un tirage pour `player` sur `machine`. Renvoie false si le tirage est refusé.
local function tirer(player: Player, machine: BasePart): boolean
	local maintenant = os.clock()
	local dernier = dernierTirage[player]
	if dernier and maintenant - dernier < GachaConfig.DureeAnimation then
		return false
	end

	if BaseService.GetProprietaire(machine) ~= player then
		return false
	end

	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not root or not root:IsA("BasePart") then
		return false
	end
	if (root.Position - machine.Position).Magnitude > GachaConfig.DistanceMax then
		return false
	end

	local data = DataService.GetData(player)
	if not data then
		return false
	end
	if DataService.NombrePersonnages(player) >= Economie.PersonnagesMax then
		print(`[Gacha] {player.Name} : inventaire plein ({Economie.PersonnagesMax})`)
		return false
	end
	dernierTirage[player] = maintenant

	local personnage, etoiles = tirerPersonnage(data.Rebirths)
	local uid = DataService.AjouterPersonnage(player, personnage.Id, etoiles)
	if not uid then
		return false
	end

	local index = premierEmplacementLibre(player)
	if index and DataService.Poser(player, uid, index) then
		BaseService.RafraichirEmplacements(player)
		print(`[Gacha] {player.Name} : {personnage.Nom} {etoiles}★ → emplacement {index}`)
	else
		print(`[Gacha] {player.Name} : {personnage.Nom} {etoiles}★ → inventaire`)
	end

	local rarete = GachaConfig.RaretesParId[personnage.Rarete]
	afficherResultat(machine, personnage.Nom, etoiles, if rarete then rarete.Couleur else Color3.new(1, 1, 1))
	return true
end

local function installerMachine(instance: Instance)
	if not instance:IsA("BasePart") or machinesInstallees[instance] then
		return
	end
	local machine = instance
	machinesInstallees[machine] = true
	machine.Destroying:Connect(function()
		machinesInstallees[machine] = nil
	end)

	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText = "Tirer"
	prompt.ObjectText = "Machine RNG (gratuit)"
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = GachaConfig.DistanceMax - 5
	prompt.RequiresLineOfSight = false
	prompt.Parent = machine
	prompt.Triggered:Connect(function(player: Player)
		tirer(player, machine)
	end)
end

-- Studio uniquement : BindableFunction pour tester un tirage depuis la barre de commande ou le MCP.
-- ServerStorage n'est pas accessible aux clients.
local function installerOutilTest()
	local outil = Instance.new("BindableFunction")
	outil.Name = "TestTirage"
	outil.OnInvoke = function(player: Player): boolean
		local base = BaseService.GetBase(player)
		local machine = base and base:FindFirstChild("RNG", true)
		if not machine or not machine:IsA("BasePart") then
			return false
		end
		dernierTirage[player] = nil
		return tirer(player, machine)
	end
	outil.Parent = ServerStorage
end

function GachaService.Init()
	for _, machine in CollectionService:GetTagged(TAG_MACHINE) do
		installerMachine(machine)
	end
	CollectionService:GetInstanceAddedSignal(TAG_MACHINE):Connect(installerMachine)

	Players.PlayerRemoving:Connect(function(player: Player)
		dernierTirage[player] = nil
	end)

	if RunService:IsStudio() then
		installerOutilTest()
	end
end

return GachaService
