--!strict
-- RevenuService : les personnages posés produisent de l'argent chaque seconde, à récupérer au collecteur
-- (Part taguée "Collecteur" dans la base). Voir docs/wiki/Economie.md.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economie = require(ReplicatedStorage.Shared.Economie)
local Personnages = require(ReplicatedStorage.Shared.Personnages)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local BaseService = require(script.Parent.BaseService)
local DataService = require(script.Parent.DataService)
local InterfaceService = require(script.Parent.InterfaceService)

local RevenuService = {}

local TAG_COLLECTEUR = "Collecteur"
local INTERVALLE = 1 -- secondes
local DELAI_COLLECTE = 1 -- secondes minimum entre deux collectes d'un même joueur

local derniereCollecte: { [Player]: number } = {}
local textesCollecteurs: { [BasePart]: TextLabel } = {}

-- Revenu total par seconde des personnages posés sur les emplacements du joueur.
function RevenuService.RevenuTotal(player: Player): number
	local data = DataService.GetData(player)
	if not data then
		return 0
	end
	local total = 0
	for _, uid in data.Emplacements do
		local personnage = data.Personnages[uid]
		local definition = personnage and Personnages.ParId[personnage.Id]
		if personnage and definition then
			total += Economie.RevenuParSeconde(definition.Revenu, personnage.Etoiles, data.Rebirths)
		end
	end
	return total
end

-- Attributs lus par le HUD du client.
local function mettreAJourAttributs(player: Player, revenu: number)
	local data = DataService.GetData(player)
	if data then
		player:SetAttribute(Remotes.Attributs.ArgentNonCollecte, math.floor(data.ArgentNonCollecte))
		player:SetAttribute(Remotes.Attributs.RevenuParSeconde, revenu)
	end
end

local function rafraichirCollecteur(collecteur: BasePart, label: TextLabel)
	local proprietaire = BaseService.GetProprietaire(collecteur)
	local data = proprietaire and DataService.GetData(proprietaire)
	if proprietaire and data then
		local revenu = RevenuService.RevenuTotal(proprietaire)
		label.Text = `{math.floor(data.ArgentNonCollecte)} $\n+{math.round(revenu * 10) / 10} $/s`
	else
		label.Text = "Collecteur"
	end
end

local function onToucheCollecteur(collecteur: BasePart, autre: BasePart)
	local character = autre.Parent
	local player = character and Players:GetPlayerFromCharacter(character)
	if not player or BaseService.GetProprietaire(collecteur) ~= player then
		return
	end

	local maintenant = os.clock()
	local derniere = derniereCollecte[player]
	if derniere and maintenant - derniere < DELAI_COLLECTE then
		return
	end
	derniereCollecte[player] = maintenant

	local montant = DataService.Collecter(player)
	if montant > 0 then
		mettreAJourAttributs(player, RevenuService.RevenuTotal(player))
		InterfaceService.EnvoyerCollecte(player, montant)
		local label = textesCollecteurs[collecteur]
		if label then
			rafraichirCollecteur(collecteur, label)
		end
	end
end

local function installerCollecteur(instance: Instance)
	if not instance:IsA("BasePart") or textesCollecteurs[instance] then
		return
	end
	local collecteur = instance

	local billboard = Instance.new("BillboardGui")
	billboard.Size = UDim2.fromOffset(160, 60)
	billboard.StudsOffset = Vector3.new(0, 4, 0)
	billboard.MaxDistance = 100

	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.TextColor3 = Color3.fromRGB(255, 215, 0)
	label.TextStrokeTransparency = 0
	label.TextScaled = true
	label.Font = Enum.Font.GothamBold
	label.Parent = billboard
	billboard.Parent = collecteur

	textesCollecteurs[collecteur] = label
	rafraichirCollecteur(collecteur, label)

	collecteur.Touched:Connect(function(autre: BasePart)
		onToucheCollecteur(collecteur, autre)
	end)
	collecteur.Destroying:Connect(function()
		textesCollecteurs[collecteur] = nil
	end)
end

function RevenuService.Init()
	for _, collecteur in CollectionService:GetTagged(TAG_COLLECTEUR) do
		installerCollecteur(collecteur)
	end
	CollectionService:GetInstanceAddedSignal(TAG_COLLECTEUR):Connect(installerCollecteur)

	Players.PlayerRemoving:Connect(function(player: Player)
		derniereCollecte[player] = nil
	end)

	task.spawn(function()
		while true do
			local ecoule = task.wait(INTERVALLE) -- temps réel écoulé, légèrement supérieur à INTERVALLE
			for _, player in Players:GetPlayers() do
				local revenu = RevenuService.RevenuTotal(player)
				DataService.AjouterNonCollecte(player, revenu * ecoule)
				mettreAJourAttributs(player, revenu)
			end
			for collecteur, label in textesCollecteurs do
				rafraichirCollecteur(collecteur, label)
			end
		end
	end)
end

return RevenuService
