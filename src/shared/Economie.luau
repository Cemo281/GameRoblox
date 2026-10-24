--!strict
-- Economie : règles de revenu et d'emplacements. Voir docs/wiki/Economie.md.

local BONUS_PAR_ETOILE = 0.2
local BONUS_PAR_REBIRTH = 0.5

-- revenu de base × (1 + 0,2 × étoiles) × (1 + 0,5 × rebirths)
local function revenuParSeconde(revenuBase: number, etoiles: number, rebirths: number): number
	return revenuBase * (1 + BONUS_PAR_ETOILE * etoiles) * (1 + BONUS_PAR_REBIRTH * rebirths)
end

return {
	EmplacementsMax = 10,
	EmplacementsDepart = 2,
	EtoilesMin = 1,
	EtoilesMax = 5,
	-- PROVISOIRE (taille à définir dans le wiki) : limite technique pour que la sauvegarde ne grossisse pas sans fin
	PersonnagesMax = 100,
	RevenuParSeconde = revenuParSeconde,
}
