--!strict
-- Remotes : RemoteEvents / RemoteFunctions entre le serveur et l'interface, rangés dans ReplicatedStorage.Remotes.
-- Le serveur les crée au premier appel, le client les attend. Les demandes du client sont validées
-- dans src/server/InterfaceService.luau.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local NOM_DOSSIER = "Remotes"

-- Serveur → client
export type NomEvenement = "Inventaire" | "ResultatTirage" | "Collecte" | "Notification"
-- Client → serveur (renvoient true si l'action a été faite)
export type NomFonction = "Poser" | "Retirer"

export type PersonnageInventaire = {
	Uid: string,
	Id: string,
	Etoiles: number,
	Emplacement: number?, -- nil si le personnage est dans l'inventaire
}

export type EtatInventaire = {
	Personnages: { PersonnageInventaire },
	EmplacementsDebloques: number,
	Rebirths: number,
	Max: number, -- nombre max de personnages (posés + inventaire)
}

export type ResultatTirage = {
	Id: string,
	Etoiles: number,
	Revenu: number, -- $/s avec étoiles et rebirths
	Emplacement: number?, -- nil si le personnage est parti dans l'inventaire
}

-- Doit lister tous les noms des types ci-dessus.
local EVENEMENTS: { NomEvenement } = { "Inventaire", "ResultatTirage", "Collecte", "Notification" }
local FONCTIONS: { NomFonction } = { "Poser", "Retirer" }

-- Côté serveur, crée le dossier avec toutes les remotes d'un coup : le client peut ainsi brancher
-- chacune sans attendre qu'elle serve une première fois.
local function dossier(): Instance
	if RunService:IsServer() then
		local existant = ReplicatedStorage:FindFirstChild(NOM_DOSSIER)
		if existant then
			return existant
		end
		local nouveau = Instance.new("Folder")
		nouveau.Name = NOM_DOSSIER
		for _, nom in EVENEMENTS do
			local remote = Instance.new("RemoteEvent")
			remote.Name = nom
			remote.Parent = nouveau
		end
		for _, nom in FONCTIONS do
			local remote = Instance.new("RemoteFunction")
			remote.Name = nom
			remote.Parent = nouveau
		end
		nouveau.Parent = ReplicatedStorage
		return nouveau
	end
	return ReplicatedStorage:WaitForChild(NOM_DOSSIER)
end

local function obtenir(nom: string): Instance
	local parent = dossier()
	if RunService:IsServer() then
		local remote = parent:FindFirstChild(nom)
		assert(remote, `[Remotes] « {nom} » absent de EVENEMENTS / FONCTIONS`)
		return remote
	end
	return parent:WaitForChild(nom)
end

return {
	-- Attributs du Player mis à jour par le serveur (affichage uniquement)
	Attributs = {
		ArgentNonCollecte = "ArgentNonCollecte",
		RevenuParSeconde = "RevenuParSeconde",
	},

	Evenement = function(nom: NomEvenement): RemoteEvent
		return obtenir(nom) :: RemoteEvent
	end,

	Fonction = function(nom: NomFonction): RemoteFunction
		return obtenir(nom) :: RemoteFunction
	end,
}
