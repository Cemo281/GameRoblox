--!strict
-- ImagesPersonnages : IDs Roblox des images d'interface, rendues depuis les modèles Blender.
-- Source : assets/gui/<Id>/infos.json et assets/gui/cadres/infos.json (champ ids_roblox), générés par
-- assets/gui/rendu_gui.py et assets/gui/cadres.py. Un perso absent d'ici garde le bloc coloré avec son initiale.

export type GrilleIdle = {
	Image: string,
	Colonnes: number, -- cases lues ligne par ligne, de gauche à droite puis de haut en bas
	Lignes: number,
	TailleCase: number, -- pixels
	Fps: number, -- 16 images / durée de la boucle Idle
}

export type ImagesPerso = {
	Portrait: string, -- 512 × 512, buste
	Pied: string, -- 1024 × 1024, plein pied
	Silhouette: string, -- 512 × 512, cadrage du portrait, noir
	Idle: GrilleIdle, -- 1024 × 1024
}

local parPerso: { [string]: ImagesPerso } = {
	nami = {
		Portrait = "rbxassetid://140496050097409",
		Pied = "rbxassetid://114044211519143",
		Silhouette = "rbxassetid://111957893757960",
		Idle = { Image = "rbxassetid://122462618381607", Colonnes = 4, Lignes = 4, TailleCase = 256, Fps = 16 / 3 },
	},
	zoro = {
		Portrait = "rbxassetid://105241865396938",
		Pied = "rbxassetid://117974979456961",
		Silhouette = "rbxassetid://119444152343751",
		Idle = { Image = "rbxassetid://136335869201198", Colonnes = 4, Lignes = 4, TailleCase = 256, Fps = 16 / 4 },
	},
	luffy = {
		Portrait = "rbxassetid://101428508083176",
		Pied = "rbxassetid://74465039531995",
		Silhouette = "rbxassetid://131257289640939",
		Idle = { Image = "rbxassetid://124882063717952", Colonnes = 4, Lignes = 4, TailleCase = 256, Fps = 16 / 3 },
	},
	usopp = {
		Portrait = "rbxassetid://131621362760145",
		Pied = "rbxassetid://133262628291191",
		Silhouette = "rbxassetid://128942612022486",
		Idle = { Image = "rbxassetid://105982684554992", Colonnes = 4, Lignes = 4, TailleCase = 256, Fps = 16 / 4 },
	},
}

-- Cadres de carte 280 × 368 (le double de la carte de l'inventaire), par Id de rareté de GachaConfig
local cadres: { [string]: string } = {
	Commun = "rbxassetid://73991991603192",
	Rare = "rbxassetid://90758012188875",
	Legendaire = "rbxassetid://139155695753037",
	Mythique = "rbxassetid://75830200946156",
	Secret = "rbxassetid://78993290810706",
}

return {
	ParPerso = parPerso,
	Cadres = cadres,
	TailleCadre = Vector2.new(280, 368),
	BordCadre = 14, -- pixels du bord du cadre (à 280 × 368) : le portrait se pose à l'intérieur
	RefletSecret = "rbxassetid://97681142840985", -- bande diagonale à faire défiler par-dessus le cadre Secret
}
