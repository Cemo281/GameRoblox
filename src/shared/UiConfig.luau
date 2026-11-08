--!strict
-- UiConfig : réglages de l'interface (données uniquement) : icônes, couleurs des fonctions, lieux de téléportation. Maquettes : design_handoff_ui_roblox/ (planche de style v2, HUD v3).

export type Teinte = { Clair: Color3, Base: Color3, Fonce: Color3 }

export type Icone = {
	Image: string, -- rbxassetid ; vide tant que l'icône n'est pas envoyée à Roblox
	Symbole: string, -- remplaçant texte affiché sans image
}

export type Lieu = {
	Id: string,
	Nom: string,
	Court: string, -- libellé de la barre rapide
	Description: string,
	Icone: string, -- clé de Icones
	Teinte: Teinte,
	Angle: number?, -- position sur la mini-carte (degrés, sens horaire depuis le chemin 1) ; nil = centre ou base
	Stand: string?, -- attribut `Stand` du stand du Hub (Workspace.Hub.Stands)
}

local function rgb(hex: string): Color3
	return Color3.fromHex(hex)
end

local function teinte(clair: string, base: string, fonce: string): Teinte
	return { Clair = rgb(clair), Base = rgb(base), Fonce = rgb(fonce) }
end

-- Icônes du handoff (icons2/*.svg, icons/billets.png) : à convertir en PNG 256 × 256 et à envoyer.
local icones: { [string]: Icone } = {
	billets = { Image = "", Symbole = "💵" },
	teleport = { Image = "", Symbole = "🌀" },
	inventaire = { Image = "", Symbole = "🎒" },
	index = { Image = "", Symbole = "📖" },
	boutique = { Image = "", Symbole = "🛒" },
	parametres = { Image = "", Symbole = "⚙️" },
	rebirth = { Image = "", Symbole = "🔄" },
	centre = { Image = "", Symbole = "⛩️" },
	evolutions = { Image = "", Symbole = "🧬" },
	etoiles_stand = { Image = "", Symbole = "🌟" },
	atelier = { Image = "", Symbole = "🔨" },
	recyclage = { Image = "", Symbole = "♻️" },
	classements = { Image = "", Symbole = "🏆" },
	base = { Image = "", Symbole = "🏠" },
	etoile = { Image = "", Symbole = "★" },
	etoile_vide = { Image = "", Symbole = "☆" },
	cadenas = { Image = "", Symbole = "🔒" },
	loupe = { Image = "", Symbole = "🔍" },
	fermer = { Image = "", Symbole = "X" }, -- FredokaOne n'a pas ✕
	stats = { Image = "", Symbole = "📊" }, -- dessinée pour le jeu : assets/gui/icones/sources/stats.svg
}

-- Fond des boutons du menu, par fonction (dégradé 160°, 3 tons)
local couleursFonctions: { [string]: Teinte } = {
	teleport = teinte("#9EEFFF", "#22B8F0", "#0B5FA8"),
	index = teinte("#FFD596", "#FF962A", "#B85000"),
	inventaire = teinte("#DCC6FF", "#9B6BFF", "#5226C0"),
	rebirth = teinte("#FFB8D8", "#FF4F9A", "#A8124F"),
	boutique = teinte("#C2FFB8", "#3FD45E", "#137A2C"),
	parametres = teinte("#D2DCFF", "#7A8CD6", "#38448A"),
	stats = teinte("#E4DCFF", "#9C86F0", "#5B45B8"),
}

-- Lieux : ordre des stands repris de docs/wiki/Hub.md (intervalles entre chemins à partir du chemin 1 :
-- Évolutions, Classements, Étoiles, libre, Ateliers, Recyclage, libre).
local PAS = 360 / 7
local lieux: { Lieu } = {
	{
		Id = "centre",
		Nom = "Centre du Hub",
		Court = "Hub",
		Description = "Le piédestal d'événement, au cœur du Hub.",
		Icone = "centre",
		Teinte = teinte("#FFF6C8", "#FFC93C", "#B06A08"),
	},
	{
		Id = "evolutions",
		Nom = "Évolutions",
		Court = "Évolutions",
		Description = "Fusionne tes doublons en perso évolué.",
		Icone = "evolutions",
		Teinte = teinte("#F6C2FF", "#E45CFF", "#7A1A9A"),
		Angle = PAS * 0.5,
		Stand = "Evolutions",
	},
	{
		Id = "classements",
		Nom = "Classements",
		Court = "Classements",
		Description = "Les meilleurs joueurs du serveur.",
		Icone = "classements",
		Teinte = teinte("#BCD3FF", "#4F8BFF", "#1C46A8"),
		Angle = PAS * 1.5,
	},
	{
		Id = "etoiles",
		Nom = "Étoiles",
		Court = "Étoiles",
		Description = "Relance les étoiles d'un personnage.",
		Icone = "etoiles_stand",
		Teinte = teinte("#FFF1B0", "#FFCF3A", "#A07400"),
		Angle = PAS * 2.5,
		Stand = "Etoiles",
	},
	{
		Id = "atelier",
		Nom = "Atelier",
		Court = "Atelier",
		Description = "Achète des bonus permanents.",
		Icone = "atelier",
		Teinte = teinte("#FFD2B0", "#FF8A3D", "#A0460A"),
		Angle = PAS * 4.5,
		Stand = "Ateliers",
	},
	{
		Id = "recyclage",
		Nom = "Recyclage",
		Court = "Recyclage",
		Description = "Vends tes persos en trop contre de l'argent.",
		Icone = "recyclage",
		Teinte = teinte("#D6F5AE", "#8BD346", "#467E10"),
		Angle = PAS * 5.5,
		Stand = "Recyclage",
	},
	{
		Id = "base",
		Nom = "Ma base",
		Court = "Ma base",
		Description = "Retour à ta machine et tes emplacements.",
		Icone = "base",
		Teinte = teinte("#C2F7EA", "#4FDDBB", "#17705C"),
	},
}

local lieuxParId: { [string]: Lieu } = {}
for _, lieu in lieux do
	lieuxParId[lieu.Id] = lieu
end

return {
	Icones = icones,
	CouleursFonctions = couleursFonctions,
	Lieux = lieux,
	LieuxParId = lieuxParId,
	StandsListe = { "evolutions", "etoiles", "atelier", "recyclage", "classements" }, -- liste de la fenêtre
	BarreRapide = { "centre", "base" }, -- raccourcis en haut au centre (choix de l'utilisateur, 05/11)
	AnglesLibres = { PAS * 3.5, PAS * 6.5 }, -- intervalles sans stand (mini-carte)
	NombreBases = 7,
	DelaiTeleportation = 2, -- secondes minimum entre deux téléportations (vérifié par le serveur)
}
