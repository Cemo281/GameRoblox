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

-- Étiquette du collecteur (BillboardGui « Etiquette » de la zone : Montant + Aide), créée si absente.
type Etiquette = { gui: BillboardGui, montant: TextLabel }

local textesCollecteurs: { [BasePart]: Etiquette } = {}

local function rafraichirCollecteur(collecteur: BasePart, etiquette: Etiquette)
	local proprietaire = BaseService.GetProprietaire(collecteur)
	local data = proprietaire and DataService.GetData(proprietaire)
	etiquette.gui.Enabled = data ~= nil
	if data then
		etiquette.montant.Text = `{math.floor(data.ArgentNonCollecte)} $`
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
		local etiquette = textesCollecteurs[collecteur]
		if etiquette then
			rafraichirCollecteur(collecteur, etiquette)
		end
	end
end

local function installerCollecteur(instance: Instance)
	if not instance:IsA("BasePart") or textesCollecteurs[instance] then
		return
	end
	local collecteur = instance

	local etiquette: Etiquette
	local existante = collecteur:FindFirstChild("Etiquette")
	local montant = existante and existante:FindFirstChild("Montant")
	if existante and existante:IsA("BillboardGui") and montant and montant:IsA("TextLabel") then
		etiquette = { gui = existante, montant = montant }
	else
		local billboard = Instance.new("BillboardGui")
		billboard.Name = "Etiquette"
		billboard.Size = UDim2.fromOffset(160, 40)
		billboard.StudsOffsetWorldSpace = Vector3.new(0, 4, 0)
		billboard.MaxDistance = 100

		local label = Instance.new("TextLabel")
		label.Name = "Montant"
		label.Size = UDim2.fromScale(1, 1)
		label.BackgroundTransparency = 1
		label.TextColor3 = Color3.fromRGB(255, 211, 77)
		label.TextStrokeTransparency = 0
		label.TextScaled = true
		label.Font = Enum.Font.GothamBold
		label.Parent = billboard
		billboard.Parent = collecteur
		etiquette = { gui = billboard, montant = label }
	end

	textesCollecteurs[collecteur] = etiquette
	rafraichirCollecteur(collecteur, etiquette)

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
			for collecteur, etiquette in textesCollecteurs do
				rafraichirCollecteur(collecteur, etiquette)
			end
		end
	end)
end

return RevenuService
