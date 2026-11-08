--!strict
-- GachaService : tirage gratuit sur la machine RNG de sa base (Part taguée "MachineRNG") via un ProximityPrompt.
-- La machine est l'autel d'invocation (Model "AutelInvocation") ; la Part "RNG" est son volume invisible.
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
local InterfaceService = require(script.Parent.InterfaceService)

local GachaService = {}

local TAG_MACHINE = "MachineRNG"

local random = Random.new()
local finTirage: { [Player]: number } = {} -- os.clock() de la fin de l'animation en cours
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

-- Affichage provisoire du résultat au-dessus de la machine, en attendant l'animation de tirage.
local function afficherResultat(machine: BasePart, nom: string, etoiles: number, couleur: Color3, duree: number)
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "ResultatTirage"
	billboard.Size = UDim2.fromOffset(240, 60)
	billboard.StudsOffset = Vector3.new(0, machine.Size.Y / 2 + 7, 0) -- au-dessus du compte à rebours et de « MAX »
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
	task.delay(duree, function()
		if billboard.Parent then
			billboard:Destroy()
		end
	end)
end

-- Effectue un tirage pour `player` sur `machine`. Renvoie false si le tirage est refusé.
local function tirer(player: Player, machine: BasePart): boolean
	local maintenant = os.clock()
	-- pas de nouveau tirage tant que l'animation du précédent se joue
	local fin = finTirage[player]
	if fin and maintenant < fin then
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
		InterfaceService.Notifier(player, `Inventaire plein ({Economie.PersonnagesMax} personnages maximum).`)
		return false
	end
	-- rien ne cède la main entre la vérification ci-dessus et ici : deux tirages ne peuvent pas se croiser
	local personnage, etoiles = tirerPersonnage(data.Rebirths)
	local duree = GachaConfig.DureeTirage(personnage.Rarete)
	finTirage[player] = maintenant + duree
	local uid = DataService.AjouterPersonnage(player, personnage.Id, etoiles)
	if not uid then
		finTirage[player] = nil
		return false
	end

	local index = DataService.PremierEmplacementLibre(player)
	local pose = index ~= nil and DataService.Poser(player, uid, index)
	if pose then
		BaseService.RafraichirEmplacements(player)
	end
	local destination = if pose then `emplacement {index}` else "inventaire"
	print(`[Gacha] {player.Name} : {personnage.Nom} {etoiles}★ → {destination}`)

	local rarete = GachaConfig.RaretesParId[personnage.Rarete]
	-- L'autel prend la couleur de la rareté obtenue au moment de la révélation (Autel.luau côté client)
	local autel = machine.Parent and machine.Parent:FindFirstChild("AutelInvocation")
	if autel then
		-- compte à rebours au-dessus du toit (heure serveur, lue par le client)
		autel:SetAttribute("FinRecharge", workspace:GetServerTimeNow() + duree)
		local rareteId = personnage.Rarete
		task.delay(GachaConfig.Minutage(rareteId).Revelation, function()
			if autel.Parent then
				autel:SetAttribute("Rarete", rareteId)
			end
		end)
	end
	afficherResultat(machine, personnage.Nom, etoiles, if rarete then rarete.Couleur else Color3.new(1, 1, 1), duree)
	InterfaceService.EnvoyerResultatTirage(player, {
		Id = personnage.Id,
		Etoiles = etoiles,
		Revenu = Economie.RevenuParSeconde(personnage.Revenu, etoiles, data.Rebirths),
		Emplacement = if pose then index else nil,
	})
	InterfaceService.EnvoyerInventaire(player)
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
	prompt.ObjectText = "Autel d'invocation (gratuit)"
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
		finTirage[player] = nil
		return tirer(player, machine)
	end
	outil.Parent = ServerStorage
end

-- Studio uniquement : BindableFunction qui ajoute un personnage précis à l'inventaire (test d'un nouveau modèle).
-- Renvoie l'uid, ou nil si l'Id est inconnu, les données pas chargées ou l'inventaire plein.
local function installerOutilDonner()
	local outil = Instance.new("BindableFunction")
	outil.Name = "TestDonnerPersonnage"
	outil.OnInvoke = function(player: Player, id: string, etoiles: number?): string?
		if typeof(id) ~= "string" or not Personnages.ParId[id] then
			return nil
		end
		local uid = DataService.AjouterPersonnage(player, id, etoiles or Economie.EtoilesMin)
		if uid then
			InterfaceService.EnvoyerInventaire(player)
		end
		return uid
	end
	outil.Parent = ServerStorage
end

function GachaService.Init()
	for _, machine in CollectionService:GetTagged(TAG_MACHINE) do
		installerMachine(machine)
	end
	CollectionService:GetInstanceAddedSignal(TAG_MACHINE):Connect(installerMachine)

	Players.PlayerRemoving:Connect(function(player: Player)
		finTirage[player] = nil
	end)

	if RunService:IsStudio() then
		installerOutilTest()
		installerOutilDonner()
	end
end

return GachaService
