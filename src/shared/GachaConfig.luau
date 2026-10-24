--!strict
-- GachaConfig : réglages de la machine RNG.
-- Valeurs PROVISOIRES pour les tests : prix et chances seront définis plus tard.

export type Rarete = {
	Nom: string,
	Poids: number, -- chance relative : Poids / somme des poids
	Couleur: Color3,
}

local GachaConfig = {
	Prix = 10, -- Argent par tirage
	Cooldown = 1, -- secondes minimum entre deux tirages d'un même joueur
	DistanceMax = 25, -- studs max entre le joueur et le centre du cube RNG
	DureeVieResultat = 30, -- secondes avant la disparition du bloc obtenu

	Raretes = {
		{ Nom = "Commun", Poids = 80, Couleur = Color3.fromRGB(163, 162, 165) },
		{ Nom = "Rare", Poids = 18, Couleur = Color3.fromRGB(0, 120, 255) },
		{ Nom = "Légendaire", Poids = 2, Couleur = Color3.fromRGB(255, 190, 0) },
	} :: { Rarete },
}

return GachaConfig
