--!strict
-- Personnages : données des personnages, par lot. Voir docs/wiki/Personnages.md.
-- Les noms sont des noms de travail, remplacés par des personnages originaux avant publication.

export type Personnage = {
	Id: string, -- identifiant sauvegardé : ne jamais le changer une fois publié
	Nom: string,
	Rarete: string, -- Id d'une rareté de GachaConfig
	Revenu: number, -- $/s de base
	Lot: number,
}

local liste: { Personnage } = {
	{ Id = "nami", Nom = "Nami", Rarete = "Commun", Revenu = 10, Lot = 1 },
	{ Id = "usopp", Nom = "Usopp", Rarete = "Commun", Revenu = 12, Lot = 1 },
	{ Id = "chopper", Nom = "Chopper", Rarete = "Commun", Revenu = 15, Lot = 1 },
	{ Id = "franky", Nom = "Franky", Rarete = "Rare", Revenu = 30, Lot = 1 },
	{ Id = "brook", Nom = "Brook", Rarete = "Rare", Revenu = 35, Lot = 1 },
	{ Id = "robin", Nom = "Robin", Rarete = "Legendaire", Revenu = 60, Lot = 1 },
	{ Id = "jinbei", Nom = "Jinbei", Rarete = "Legendaire", Revenu = 70, Lot = 1 },
	{ Id = "sanji", Nom = "Sanji", Rarete = "Mythique", Revenu = 85, Lot = 1 },
	{ Id = "zoro", Nom = "Zoro", Rarete = "Mythique", Revenu = 90, Lot = 1 },
	{ Id = "luffy", Nom = "Luffy", Rarete = "Mythique", Revenu = 100, Lot = 1 },
	{ Id = "luffy_gear2", Nom = "Luffy Gear 2", Rarete = "Secret", Revenu = 1000, Lot = 1 },
}

local parId: { [string]: Personnage } = {}
for _, personnage in liste do
	parId[personnage.Id] = personnage
end

return {
	Liste = liste,
	ParId = parId,
}
