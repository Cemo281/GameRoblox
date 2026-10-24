--!strict
-- GachaSystem : tirage sur le cube RNG du Workspace via un ProximityPrompt.
-- Le serveur vérifie cooldown, distance et argent, puis tire la rareté : rien ne vient du client.

local Debris = game:GetService("Debris")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local DataService = require(script.Parent:WaitForChild("DataService"))
local GachaConfig = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("GachaConfig"))

type Rarete = {
	Nom: string,
	Poids: number,
	Couleur: Color3,
}

local machine = workspace:WaitForChild("RNG") :: BasePart
local random = Random.new()
local dernierTirage: { [Player]: number } = {}

local resultats = Instance.new("Folder")
resultats.Name = "ResultatsGacha"
resultats.Parent = workspace

local function tirerRarete(): Rarete
	local total = 0
	for _, rarete in GachaConfig.Raretes do
		total += rarete.Poids
	end

	local tirage = random:NextNumber(0, total)
	for _, rarete in GachaConfig.Raretes do
		tirage -= rarete.Poids
		if tirage <= 0 then
			return rarete
		end
	end
	return GachaConfig.Raretes[#GachaConfig.Raretes]
end

local function afficherResultat(player: Player, rarete: Rarete)
	local bloc = Instance.new("Part")
	bloc.Name = rarete.Nom
	bloc.Size = Vector3.new(3, 3, 3)
	bloc.Color = rarete.Couleur
	bloc.Material = Enum.Material.Neon
	bloc.Position = machine.Position + Vector3.new(0, machine.Size.Y / 2 + 3, 0)

	local billboard = Instance.new("BillboardGui")
	billboard.Size = UDim2.fromOffset(200, 50)
	billboard.StudsOffset = Vector3.new(0, 3, 0)
	billboard.AlwaysOnTop = true

	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Text = `{player.DisplayName} : {rarete.Nom}`
	label.TextColor3 = rarete.Couleur
	label.TextStrokeTransparency = 0
	label.TextScaled = true
	label.Font = Enum.Font.GothamBold
	label.Parent = billboard

	billboard.Parent = bloc
	bloc.Parent = resultats
	Debris:AddItem(bloc, GachaConfig.DureeVieResultat)
end

local function onTriggered(player: Player)
	local maintenant = os.clock()
	local dernier = dernierTirage[player]
	if dernier and maintenant - dernier < GachaConfig.Cooldown then
		return
	end
	dernierTirage[player] = maintenant

	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not root or not root:IsA("BasePart") then
		return
	end
	if (root.Position - machine.Position).Magnitude > GachaConfig.DistanceMax then
		return
	end

	if not DataService.SpendArgent(player, GachaConfig.Prix) then
		return
	end

	local rarete = tirerRarete()
	print(`[Gacha] {player.Name} a obtenu : {rarete.Nom}`)
	afficherResultat(player, rarete)
end

local prompt = Instance.new("ProximityPrompt")
prompt.ActionText = "Tirer"
prompt.ObjectText = `Machine RNG ({GachaConfig.Prix} Argent)`
prompt.HoldDuration = 0
prompt.MaxActivationDistance = GachaConfig.DistanceMax - 5
prompt.RequiresLineOfSight = false
prompt.Parent = machine
prompt.Triggered:Connect(onTriggered)

Players.PlayerRemoving:Connect(function(player: Player)
	dernierTirage[player] = nil
end)
