--!strict
-- DeplacementService : téléportation vers les lieux du Hub et la base du joueur (fenêtre Téléportation, barre rapide).
-- RemoteFunction "Teleporter"(idLieu) validée ici : type, lieu connu (UiConfig.Lieux), cadence, personnage en vie.
-- Les points d'arrivée sont lus dans Workspace.Hub (Centre, Stands.Stand<Id>.Comptoir, Classements).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = require(ReplicatedStorage.Shared.Remotes)
local UiConfig = require(ReplicatedStorage.Shared.UiConfig)
local BaseService = require(script.Parent.BaseService)

local DeplacementService = {}

local DISTANCE_COMPTOIR = 7 -- studs devant le comptoir d'un stand
local DISTANCE_CENTRE = 16 -- studs du piédestal, côté chemin 1
local DISTANCE_CLASSEMENTS = 12
local HAUTEUR_SONDE = 60

local derniere: { [Player]: number } = {}
local initialized = false

local function hub(): Model?
	local instance = workspace:FindFirstChild("Hub")
	return if instance and instance:IsA("Model") then instance else nil
end

-- Point devant `cframe` (à `distance` studs dans sa direction LookVector), tourné vers lui.
local function devant(cframe: CFrame, distance: number): CFrame
	local position = cframe.Position + cframe.LookVector * distance
	return CFrame.lookAt(position, Vector3.new(cframe.X, position.Y, cframe.Z))
end

local function arrivee(lieu: UiConfig.Lieu): CFrame?
	local modele = hub()
	if not modele then
		return nil
	end
	if lieu.Id == "centre" then
		local centre = modele:FindFirstChild("Centre")
		return if centre and centre:IsA("BasePart") then devant(centre.CFrame, DISTANCE_CENTRE) else nil
	elseif lieu.Id == "classements" then
		local classements = modele:FindFirstChild("Classements")
		return if classements and classements:IsA("Model")
			then devant(classements:GetPivot(), DISTANCE_CLASSEMENTS)
			else nil
	elseif lieu.Stand then
		local stands = modele:FindFirstChild("Stands")
		for _, stand in if stands then stands:GetChildren() else {} do
			if stand:GetAttribute("Stand") == lieu.Stand then
				local comptoir = stand:FindFirstChild("Comptoir")
				if comptoir and comptoir:IsA("BasePart") then
					return devant(comptoir.CFrame, DISTANCE_COMPTOIR)
				end
			end
		end
	end
	return nil
end

-- Pose le personnage au sol sous `cible` (sonde vers le bas, en ignorant les personnages).
local function poser(character: Model, cible: CFrame)
	local parametres = RaycastParams.new()
	parametres.FilterType = Enum.RaycastFilterType.Exclude
	local exclus: { Instance } = {}
	for _, joueur in Players:GetPlayers() do
		if joueur.Character then
			table.insert(exclus, joueur.Character)
		end
	end
	parametres.FilterDescendantsInstances = exclus
	local depart = cible.Position + Vector3.new(0, HAUTEUR_SONDE, 0)
	local resultat = workspace:Raycast(depart, Vector3.new(0, -HAUTEUR_SONDE * 2, 0), parametres)
	local sol = if resultat then resultat.Position.Y else cible.Y
	character:PivotTo(cible.Rotation + Vector3.new(cible.X, sol + 3, cible.Z))
end

local function teleporter(player: Player, idRecu: unknown): boolean
	if typeof(idRecu) ~= "string" or #idRecu > 32 then
		return false
	end
	local lieu = UiConfig.LieuxParId[idRecu]
	if not lieu then
		return false
	end
	local maintenant = os.clock()
	if derniere[player] and maintenant - derniere[player] < UiConfig.DelaiTeleportation then
		return false
	end
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not character or not humanoid or humanoid.Health <= 0 then
		return false
	end
	derniere[player] = maintenant
	humanoid.Sit = false

	if lieu.Id == "base" then
		return BaseService.TeleporterALaBase(player)
	end
	local cible = arrivee(lieu)
	if not cible then
		warn(`[Deplacement] lieu « {lieu.Id} » introuvable dans Workspace.Hub`)
		return false
	end
	poser(character, cible)
	return true
end

function DeplacementService.Init()
	if initialized then
		return
	end
	initialized = true

	Remotes.Fonction("Teleporter").OnServerInvoke = function(player: Player, idRecu: unknown): boolean
		return teleporter(player, idRecu)
	end
	Players.PlayerRemoving:Connect(function(player: Player)
		derniere[player] = nil
	end)
end

return DeplacementService
