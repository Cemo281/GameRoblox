--!strict
-- GachaConfig : réglages de la machine RNG. Voir docs/wiki/Machine-RNG.md et docs/wiki/Personnages.md.

export type Rarete = {
	Id: string,
	Nom: string,
	Chance: number, -- en %, machine niveau 0
	Couleur: Color3,
}

export type ChanceEtoiles = {
	Etoiles: number,
	Chance: number, -- en %
}

local raretes: { Rarete } = {
	{ Id = "Commun", Nom = "Commun", Chance = 60, Couleur = Color3.fromRGB(163, 162, 165) },
	{ Id = "Rare", Nom = "Rare", Chance = 25, Couleur = Color3.fromRGB(0, 120, 255) },
	{ Id = "Legendaire", Nom = "Légendaire", Chance = 10, Couleur = Color3.fromRGB(255, 190, 0) },
	{ Id = "Mythique", Nom = "Mythique", Chance = 4.9, Couleur = Color3.fromRGB(200, 0, 255) },
	{ Id = "Secret", Nom = "Secret", Chance = 0.1, Couleur = Color3.fromRGB(255, 40, 40) },
}

local raretesParId: { [string]: Rarete } = {}
for _, rarete in raretes do
	raretesParId[rarete.Id] = rarete
end

return {
	DureeAnimation = 3, -- PROVISOIRE (à définir dans le wiki) : temps minimum entre deux tirages
	DistanceMax = 25, -- studs max entre le joueur et le centre du cube RNG

	Raretes = raretes,
	RaretesParId = raretesParId,

	Etoiles = {
		{ Etoiles = 1, Chance = 50 },
		{ Etoiles = 2, Chance = 30 },
		{ Etoiles = 3, Chance = 15 },
		{ Etoiles = 4, Chance = 4 },
		{ Etoiles = 5, Chance = 1 },
	} :: { ChanceEtoiles },
}
