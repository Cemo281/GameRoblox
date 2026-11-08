--!strict
-- Cartes : carte de personnage 140 × 184 de la planche de style v2 (inventaire, index).
-- Fond au dégradé de la rareté, lueur, render plein pied, plaque sombre en bas, ruban de rareté, nom, étoiles, revenu.
-- Légendaire et plus : rayons (fixes en Légendaire, tournants en Mythique 16 s / Secret 8 s) et losanges dans les coins ;
-- Secret : reflet animé et anneau rouge. Un perso sans images garde un bloc coloré avec son initiale.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Economie = require(ReplicatedStorage.Shared.Economie)
local GachaConfig = require(ReplicatedStorage.Shared.GachaConfig)
local Personnages = require(ReplicatedStorage.Shared.Personnages)
local Images = require(script.Parent.Images)
local Ui = require(script.Parent.Ui)

local Cartes = {}

Cartes.Taille = Vector2.new(140, 184)
local RAYON = 12

export type Options = {
	Id: string,
	Etoiles: number, -- étoiles affichées (0 = toutes vides)
	Revenu: number?, -- $/s (inventaire)
	Chance: number?, -- % (index) : remplace le revenu
	Pose: boolean?,
	Inconnu: boolean?, -- index : pas encore obtenu → silhouette noire, nom « ??? »
	TitreEtoiles: string?, -- petit texte devant les étoiles (« MEILLEUR »)
}

-- Rayons tournants : un seul Heartbeat pour toutes les cartes
local rayonsTournants: { [Frame]: number } = {} -- cadre → degrés par seconde
RunService.Heartbeat:Connect(function()
	local t = os.clock()
	for cadre, vitesse in rayonsTournants do
		if not cadre.Parent then
			rayonsTournants[cadre] = nil
		elseif cadre.Visible then
			cadre.Rotation = (t * vitesse) % 360
		end
	end
end)

local LOSANGE: { [string]: Color3 } = {
	Legendaire = Color3.fromHex("#FFF0A8"),
	Mythique = Color3.fromHex("#F5C8FF"),
	Secret = Color3.fromHex("#FFD0D0"),
}
local RAYONS: { [string]: { Nombre: number, Largeur: number, Vitesse: number, Transparence: number } } = {
	Legendaire = { Nombre = 16, Largeur = 10, Vitesse = 0, Transparence = 0.72 },
	Mythique = { Nombre = 24, Largeur = 8, Vitesse = 360 / 16, Transparence = 0.7 },
	Secret = { Nombre = 30, Largeur = 6, Vitesse = 360 / 8, Transparence = 0.62 },
}

-- Rayons qui partent du centre d'un cadre (remplace le repeating-conic-gradient de la maquette).
function Cartes.Rayons(
	parent: GuiObject,
	centre: UDim2,
	nombre: number,
	longueur: number,
	largeur: number,
	couleur: Color3,
	transparence: number,
	zIndex: number
): Frame
	local cadre = Ui.Creer("Frame", {
		Name = "Rayons",
		Position = centre,
		Size = UDim2.fromOffset(0, 0),
		BackgroundTransparency = 1,
		ZIndex = zIndex,
		Parent = parent,
	})
	for i = 0, nombre - 1 do
		local pivot = Ui.Creer("Frame", {
			Rotation = i * 360 / nombre,
			Size = UDim2.fromOffset(0, 0),
			BackgroundTransparency = 1,
			ZIndex = zIndex,
			Parent = cadre,
		})
		Ui.Creer("Frame", {
			AnchorPoint = Vector2.new(0, 0.5),
			Size = UDim2.fromOffset(longueur, largeur),
			BackgroundColor3 = couleur,
			BackgroundTransparency = transparence,
			BorderSizePixel = 0,
			ZIndex = zIndex,
			Parent = pivot,
		}, { Ui.Creer("UIGradient", { Transparency = NumberSequence.new(0, 1) }) })
	end
	return cadre
end

function Cartes.Tourner(cadre: Frame, degresParSeconde: number)
	if degresParSeconde ~= 0 then
		rayonsTournants[cadre] = degresParSeconde
	end
end

-- Lueur douce : disques concentriques de plus en plus transparents (pas d'image radiale). Renvoie les disques et
-- la transparence de base de chacun (pour les faire disparaître ensemble).
local DISQUES_LUEUR = 8
function Cartes.Lueur(parent: GuiObject, centre: UDim2, diametre: number, couleur: Color3, opacite: number, zIndex: number): ({ Frame }, number)
	local disques: { Frame } = {}
	local transparence = 1 - opacite * 0.16
	for i = 1, DISQUES_LUEUR do
		local d = diametre * (1 - (i - 1) / DISQUES_LUEUR)
		disques[i] = Ui.Creer("Frame", {
			Name = "Lueur",
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = centre,
			Size = UDim2.fromOffset(d, d),
			BackgroundColor3 = couleur,
			BackgroundTransparency = transparence,
			ZIndex = zIndex,
			Parent = parent,
		}, { Ui.Rond() })
	end
	return disques, transparence
end

-- Ruban de rareté (petite étiquette sombre en haut à gauche)
local function ruban(parent: GuiObject, rarete: string, zIndex: number)
	local definition = GachaConfig.RaretesParId[rarete]
	local label = Ui.Texte({
		Name = "Ruban",
		Position = UDim2.fromOffset(0, 7),
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 18),
		BackgroundTransparency = 0,
		BackgroundColor3 = if rarete == "Commun" then Color3.fromHex("#4A494F") else Ui.Rarete(rarete).Fonce,
		FontFace = Ui.Montserrat(Enum.FontWeight.ExtraBold),
		TextSize = 9,
		Text = Ui.Majuscules(if definition then definition.Nom else rarete),
		ZIndex = zIndex,
		Parent = parent,
	})
	Ui.Marges(0, 12, 0, 7).Parent = label
	Ui.Creer("UICorner", { CornerRadius = UDim.new(0, 3) }).Parent = label
end

function Cartes.Creer(options: Options, props: { [string]: any }?): Frame
	local definition = Personnages.ParId[options.Id]
	local rarete = if definition then definition.Rarete else "Commun"
	local t = Ui.Rarete(rarete)
	local inconnu = options.Inconnu == true

	local defauts: { [string]: any } = {
		Name = options.Id,
		Size = UDim2.fromOffset(Cartes.Taille.X, Cartes.Taille.Y),
		BackgroundTransparency = 1,
	}
	for cle, valeur in props or {} do
		defauts[cle] = valeur
	end
	local carte = Ui.Creer("Frame", defauts)
	if rarete == "Secret" and not inconnu then
		Ui.Creer("Frame", {
			Name = "AnneauSecret",
			Position = UDim2.fromOffset(-3, -3),
			Size = UDim2.new(1, 6, 1, 6),
			BackgroundColor3 = Color3.fromHex("#FF8A8A"),
			Parent = carte,
		}, { Ui.Coins(RAYON + 3) })
	end
	Ui.Creer("Frame", {
		Name = "Ombre",
		Position = UDim2.fromOffset(0, 3),
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Ui.C.Trait,
		Parent = carte,
	}, { Ui.Coins(RAYON) })
	local face = Ui.Creer("Frame", {
		Name = "Face",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Color3.new(1, 1, 1),
		ClipsDescendants = true,
		Parent = carte,
	}, {
		Ui.Coins(RAYON),
		Ui.Trait(2),
		if inconnu then Ui.Degrade2(Color3.fromHex("#3A3462"), Color3.fromHex("#1F1B36")) else Ui.Degrade(t, 70),
	})

	-- Décor derrière le perso : rayons (Légendaire+), lueur
	local rayons = RAYONS[rarete]
	if rayons and not inconnu then
		local cadre = Cartes.Rayons(
			face,
			UDim2.fromOffset(70, 64),
			rayons.Nombre,
			110,
			rayons.Largeur,
			Color3.new(1, 1, 1),
			rayons.Transparence,
			1
		)
		Cartes.Tourner(cadre, rayons.Vitesse)
	end
	if not inconnu then
		Cartes.Lueur(face, UDim2.fromOffset(70, 64), 120, t.Clair:Lerp(Color3.new(1, 1, 1), 0.6), 0.8, 1)
	end

	-- Render : plein pied, silhouette (inconnu) ou bloc coloré avec l'initiale
	local images = definition and Images.De(options.Id)
	if images then
		Ui.Creer("ImageLabel", {
			Name = "Render",
			Position = UDim2.fromOffset(0, 2),
			Size = UDim2.fromOffset(136, 150),
			BackgroundTransparency = 1,
			Image = images.Pied,
			ImageColor3 = if inconnu then Color3.new(0, 0, 0) else Color3.new(1, 1, 1),
			ScaleType = Enum.ScaleType.Fit,
			ZIndex = 2,
			Parent = face,
		})
	elseif definition then
		local bloc = Ui.Creer("Frame", {
			Name = "Render",
			AnchorPoint = Vector2.new(0.5, 0),
			Position = UDim2.fromOffset(70, 22),
			Size = UDim2.fromOffset(84, 92),
			BackgroundColor3 = if inconnu then Color3.new(0, 0, 0) else t.Base,
			ZIndex = 2,
			Parent = face,
		}, { Ui.Coins(14), Ui.Trait(2) })
		Ui.Texte({
			Size = UDim2.fromScale(1, 1),
			TextSize = 52,
			TextXAlignment = Enum.TextXAlignment.Center,
			Text = if inconnu then "?" else string.sub(definition.Nom, 1, 1),
			Contour = 2,
			ZIndex = 3,
			Parent = bloc,
		})
	end

	-- Plaque sombre en bas (64 px, fondu vers le haut)
	Ui.Creer("Frame", {
		Name = "Plaque",
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Size = UDim2.new(1, 0, 0, 64),
		BackgroundColor3 = Ui.C.Trait,
		BorderSizePixel = 0,
		ZIndex = 3,
		Parent = face,
	}, {
		Ui.Creer("UIGradient", {
			Rotation = 90,
			Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 1),
				NumberSequenceKeypoint.new(0.45, 0.08),
				NumberSequenceKeypoint.new(1, 0.08),
			}),
		}),
	})
	ruban(face, rarete, 4)
	if options.Pose then
		local pose = Ui.EtiquetteDegrade({
			Name = "Pose",
			AnchorPoint = Vector2.new(1, 0),
			Position = UDim2.new(1, -5, 0, 6),
			Size = UDim2.fromOffset(0, 18),
			ZIndex = 4,
			Parent = face,
		}, Ui.Degrade2(Color3.fromHex("#B6FFB0"), Color3.fromHex("#3FCB52")), {
			FontFace = Ui.Montserrat(Enum.FontWeight.ExtraBold),
			TextSize = 9,
			TextColor3 = Color3.fromHex("#0B2A10"),
			Text = "POSÉ",
		})
		Ui.Rond().Parent = pose
		Ui.Trait(1.5).Parent = pose
		Ui.Marges(0, 6).Parent = pose
	end

	-- Bas : nom, étoiles, revenu ou chance
	local bas = Ui.Creer("Frame", {
		Name = "Bas",
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.new(0, 0, 1, -6),
		Size = UDim2.fromScale(1, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		ZIndex = 4,
		Parent = face,
	}, { Ui.Liste(Enum.FillDirection.Vertical, 2, { HorizontalAlignment = Enum.HorizontalAlignment.Center }) })
	Ui.Texte({
		Name = "Nom",
		LayoutOrder = 1,
		Size = UDim2.new(1, -10, 0, 17),
		TextSize = 15,
		TextXAlignment = Enum.TextXAlignment.Center,
		TextTruncate = Enum.TextTruncate.AtEnd,
		TextColor3 = if inconnu then Ui.C.TexteEteint else Ui.C.Texte,
		Text = if inconnu or not definition then "???" else definition.Nom,
		Contour = not inconnu,
		ZIndex = 4,
		Parent = bas,
	})
	if options.Chance then
		Ui.Texte({
			Name = "Chance",
			LayoutOrder = 2,
			Size = UDim2.new(1, 0, 0, 13),
			FontFace = Ui.Montserrat(Enum.FontWeight.Bold),
			TextSize = 11,
			TextColor3 = Ui.C.TexteDiscret,
			TextXAlignment = Enum.TextXAlignment.Center,
			Text = `Chance {Ui.FormaterPourcent(options.Chance)}`,
			ZIndex = 4,
			Parent = bas,
		})
	end
	local ligneEtoiles = Ui.Creer("Frame", {
		Name = "LigneEtoiles",
		LayoutOrder = 3,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 13),
		BackgroundTransparency = 1,
		ZIndex = 4,
		Parent = bas,
	}, {
		Ui.Liste(Enum.FillDirection.Horizontal, 3, { VerticalAlignment = Enum.VerticalAlignment.Center }),
	})
	if options.TitreEtoiles then
		Ui.Texte({
			LayoutOrder = 1,
			AutomaticSize = Enum.AutomaticSize.X,
			Size = UDim2.fromOffset(0, 13),
			FontFace = Ui.Montserrat(Enum.FontWeight.SemiBold),
			TextSize = 9,
			TextColor3 = Ui.C.TexteEteint,
			Text = options.TitreEtoiles,
			ZIndex = 4,
			Parent = ligneEtoiles,
		})
	end
	local etoiles = Ui.EtoilesIcones(options.Etoiles, Economie.EtoilesMax, 13, { LayoutOrder = 2, ZIndex = 4 })
	for _, enfant in etoiles:GetDescendants() do
		if enfant:IsA("GuiObject") then
			enfant.ZIndex = 4
		end
	end
	etoiles.Parent = ligneEtoiles
	if options.Revenu then
		local revenu = Ui.Creer("Frame", {
			Name = "Revenu",
			LayoutOrder = 4,
			AutomaticSize = Enum.AutomaticSize.X,
			Size = UDim2.fromOffset(0, 14),
			BackgroundTransparency = 1,
			ZIndex = 4,
			Parent = bas,
		}, {
			Ui.Liste(Enum.FillDirection.Horizontal, 3, { VerticalAlignment = Enum.VerticalAlignment.Center }),
		})
		Ui.Icone("billets", 12, { LayoutOrder = 1, ZIndex = 4, Parent = revenu })
		Ui.Texte({
			LayoutOrder = 2,
			AutomaticSize = Enum.AutomaticSize.X,
			Size = UDim2.fromOffset(0, 14),
			FontFace = Ui.Montserrat(Enum.FontWeight.Bold),
			TextSize = 11,
			TextColor3 = Ui.C.Gain,
			Text = `{Ui.FormaterRevenu(options.Revenu)} $/s`,
			ZIndex = 4,
			Parent = revenu,
		})
	end

	-- Liseré intérieur, losanges (Légendaire+), reflet (Secret)
	local lisere = Ui.Lisere(face, 3, RAYON, Color3.new(1, 1, 1), if rayons then 0.2 else 0.45)
	lisere.ZIndex = 5
	local couleurLosange = LOSANGE[rarete]
	if couleurLosange and not inconnu then
		for _, cote in { 0, 1 } do
			Ui.Creer("Frame", {
				Name = "Losange",
				AnchorPoint = Vector2.new(cote, 1),
				Position = UDim2.new(cote, if cote == 0 then 6 else -6, 1, -6),
				Size = UDim2.fromOffset(9, 9),
				Rotation = 45,
				BackgroundColor3 = couleurLosange,
				ZIndex = 5,
				Parent = face,
			}, { Ui.Trait(1.5) })
		end
	end
	if rarete == "Secret" and not inconnu then
		Images.Reflet(face, RAYON, 6)
	end
	return carte
end

return Cartes
