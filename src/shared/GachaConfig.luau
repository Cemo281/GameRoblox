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
local rangParId: { [string]: number } = {}
for rang, rarete in raretes do
	raretesParId[rarete.Id] = rarete
	rangParId[rarete.Id] = rang
end

-- Animation de tirage (secondes) : sa durée est le temps entre deux tirages (docs/wiki/Machine-RNG.md).
-- Commun en version courte ; un palier de montée de plus par rareté au-dessus.
local animation = {
	Apparition = 1.6,
	ApparitionCourte = 1.0,
	MonteeBase = 0.8,
	MonteeParPalier = 0.75,
	Impact = 0.7,
	Revelation = 3,
	RevelationCourte = 2,
	Pose = 2.5,
	PoseCourte = 1.5,
}

export type Minutage = {
	Rang: number, -- 1 = Commun … 5 = Secret : nombre de paliers de la montée
	Montee: number, -- début de chaque phase, en secondes depuis le début
	Impact: number,
	Revelation: number,
	Pose: number,
	Total: number, -- durée totale = temps de recharge de la machine
}

local function minutage(rareteId: string): Minutage
	local rang = rangParId[rareteId] or 1
	local court = rang == 1
	local apparition = if court then animation.ApparitionCourte else animation.Apparition
	local impact = apparition + animation.MonteeBase + animation.MonteeParPalier * (rang - 1)
	local revelation = impact + animation.Impact
	local pose = revelation + (if court then animation.RevelationCourte else animation.Revelation)
	return {
		Rang = rang,
		Montee = apparition,
		Impact = impact,
		Revelation = revelation,
		Pose = pose,
		Total = pose + (if court then animation.PoseCourte else animation.Pose),
	}
end

return {
	Animation = animation,
	Minutage = minutage,
	-- Durée de l'animation de tirage de cette rareté = temps de recharge de la machine (Commun 6 s → Secret 11,6 s)
	DureeTirage = function(rareteId: string): number
		return minutage(rareteId).Total
	end,
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
