--!strict
-- InterfaceService : fait le lien entre l'interface du client et les données du joueur.
-- Envoie l'inventaire, le résultat des tirages, les collectes et les notifications ;
-- reçoit les demandes Poser / Retirer, validées ici (type, possession, cadence).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economie = require(ReplicatedStorage.Shared.Economie)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local BaseService = require(script.Parent.BaseService)
local DataService = require(script.Parent.DataService)

local InterfaceService = {}

local DELAI_ACTION = 0.2 -- secondes minimum entre deux actions d'inventaire d'un même joueur
local LONGUEUR_UID_MAX = 16

local derniereAction: { [Player]: number } = {}
local initialized = false

function InterfaceService.EnvoyerInventaire(player: Player)
	local data = DataService.GetData(player)
	if not data then
		return
	end
	local emplacementDe: { [string]: number } = {}
	for index, uid in data.Emplacements do
		emplacementDe[uid] = tonumber(index) :: number
	end
	local personnages: { Remotes.PersonnageInventaire } = {}
	for uid, personnage in data.Personnages do
		table.insert(personnages, {
			Uid = uid,
			Id = personnage.Id,
			Etoiles = personnage.Etoiles,
			Emplacement = emplacementDe[uid],
		})
	end
	local etat: Remotes.EtatInventaire = {
		Personnages = personnages,
		EmplacementsDebloques = data.EmplacementsDebloques,
		Rebirths = data.Rebirths,
		Max = Economie.PersonnagesMax,
	}
	Remotes.Evenement("Inventaire"):FireClient(player, etat)
end

function InterfaceService.EnvoyerResultatTirage(player: Player, resultat: Remotes.ResultatTirage)
	Remotes.Evenement("ResultatTirage"):FireClient(player, resultat)
end

function InterfaceService.EnvoyerCollecte(player: Player, montant: number)
	Remotes.Evenement("Collecte"):FireClient(player, montant)
end

function InterfaceService.Notifier(player: Player, texte: string)
	Remotes.Evenement("Notification"):FireClient(player, texte)
end

-- Renvoie l'uid si c'est bien un personnage du joueur, sinon nil.
local function validerUid(player: Player, uid: unknown): string?
	if typeof(uid) ~= "string" or #uid > LONGUEUR_UID_MAX then
		return nil
	end
	local data = DataService.GetData(player)
	if not data or not data.Personnages[uid] then
		return nil
	end
	return uid
end

local function cadenceRespectee(player: Player): boolean
	local maintenant = os.clock()
	local derniere = derniereAction[player]
	if derniere and maintenant - derniere < DELAI_ACTION then
		return false
	end
	derniereAction[player] = maintenant
	return true
end

-- Pose le personnage sur le premier emplacement libre.
local function poser(player: Player, uid: string): boolean
	local index = DataService.PremierEmplacementLibre(player)
	if not index then
		InterfaceService.Notifier(player, "Tous tes emplacements sont occupés : retire d'abord un personnage.")
		return false
	end
	return DataService.Poser(player, uid, index)
end

local function brancher(nom: Remotes.NomFonction, action: (Player, string) -> boolean)
	Remotes.Fonction(nom).OnServerInvoke = function(player: Player, uidRecu: unknown): boolean
		if not cadenceRespectee(player) then
			return false
		end
		local uid = validerUid(player, uidRecu)
		if not uid or not action(player, uid) then
			return false
		end
		BaseService.RafraichirEmplacements(player)
		InterfaceService.EnvoyerInventaire(player)
		return true
	end
end

function InterfaceService.Init()
	if initialized then
		return
	end
	initialized = true

	brancher("Poser", poser)
	brancher("Retirer", DataService.Retirer)

	DataService.OnChargement(function(player: Player)
		InterfaceService.EnvoyerInventaire(player)
	end)
	Players.PlayerRemoving:Connect(function(player: Player)
		derniereAction[player] = nil
	end)
end

return InterfaceService
