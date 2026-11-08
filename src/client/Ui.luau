--!strict
-- Ui : tokens de style v2 (planche de style du handoff design_handoff_ui_roblox) et composants communs :
-- palette, polices, boutons à 3 tons, boutons icônes, fenêtres, onglets, barres, pastilles, format des nombres.
-- Toute l'interface est rangée dans une racine à l'échelle de la maquette (1100 × 650 px) : les tailles et
-- positions sont données en pixels de maquette, l'échelle suit la taille de l'écran.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local UiConfig = require(ReplicatedStorage.Shared.UiConfig)

local Ui = {}

export type Teinte = UiConfig.Teinte

local function hex(code: string): Color3
	return Color3.fromHex(code)
end

-- Palette (README du handoff, « Design Tokens »)
Ui.C = {
	Trait = hex("#0D0A1C"), -- contours, ombres
	Fond = hex("#16122A"),
	PanneauHaut = hex("#2A2350"),
	PanneauBas = hex("#17132E"),
	Zone = hex("#1C1738"),
	ZoneSurvol = hex("#2E2660"),
	Lisere = hex("#5A4E9E"),
	LisereSombre = hex("#3E3478"),
	Texte = hex("#FFFFFF"),
	TexteDiscret = hex("#A9A2CC"),
	TexteDiscretClair = hex("#C9C3E6"),
	TexteEteint = hex("#7A7596"),
	Filet = hex("#FFD66B"),
	Or = hex("#FFD66B"),
	Gain = hex("#7DF08A"),
	Pastille1 = hex("#FF7A92"),
	Pastille2 = hex("#F0244A"),
	FondBarre = hex("#120E26"),
	Desactive = hex("#322D4E"),
}

local function teinte(c1: string, c2: string, c3: string): Teinte
	return { Clair = hex(c1), Base = hex(c2), Fonce = hex(c3) }
end

Ui.Teintes = {
	Or = teinte("#FFF0A8", "#FFC93C", "#F29A12"),
	Vert = teinte("#B6FFB0", "#5EE06A", "#2FAE45"),
	Principal = teinte("#B49CFF", "#7454F0", "#5235C4"),
	Danger = teinte("#FF8C96", "#F0414F", "#C42234"),
	Secondaire = teinte("#7E78A8", "#4A4570", "#36315C"),
	Desactive = teinte("#3A3558", "#322D4E", "#2A2644"),
	Base = teinte("#B8F7E8", "#5FE6C6", "#2EAE90"),
}

-- Raretés (clair · base · foncé), par Id de GachaConfig
Ui.Raretes = {
	Commun = teinte("#E4E3E6", "#A3A2A5", "#5C5B60"),
	Rare = teinte("#6CC0FF", "#0078FF", "#003A80"),
	Legendaire = teinte("#FFE98A", "#FFBE00", "#8A5A00"),
	Mythique = teinte("#EBA0FF", "#C800FF", "#5A0080"),
	Secret = teinte("#FF9A9A", "#FF2828", "#6E0606"),
} :: { [string]: Teinte }
-- Texte lisible sur le badge de rareté
Ui.TexteBadge = {
	Commun = hex("#0D0A1C"),
	Rare = hex("#FFFFFF"),
	Legendaire = hex("#0D0A1C"),
	Mythique = hex("#FFFFFF"),
	Secret = hex("#FFFFFF"),
} :: { [string]: Color3 }

function Ui.Rarete(id: string): Teinte
	return Ui.Raretes[id] or Ui.Raretes.Commun
end

-- Styles de boutons : dégradé, ombre pleine, texte, opacité du reflet et du liseré
export type StyleBouton = {
	Teinte: Teinte,
	Ombre: Color3,
	Texte: Color3,
	ContourTexte: boolean,
	Reflet: number, -- opacité de la bande blanche sur les 48 % du haut
	Lisere: number, -- opacité du liseré intérieur blanc
	Actif: boolean,
}

local function style(
	t: Teinte,
	ombre: string,
	texte: string,
	contour: boolean,
	reflet: number,
	lisere: number
): StyleBouton
	return {
		Teinte = t,
		Ombre = hex(ombre),
		Texte = hex(texte),
		ContourTexte = contour,
		Reflet = reflet,
		Lisere = lisere,
		Actif = true,
	}
end

Ui.Styles = {
	Principal = style(Ui.Teintes.Principal, "#2E1C8A", "#FFFFFF", true, 0.2, 0.4),
	Secondaire = style(Ui.Teintes.Secondaire, "#1E1A38", "#FFFFFF", true, 0.12, 0.25),
	Or = style(Ui.Teintes.Or, "#94570A", "#4A2600", false, 0.3, 0.6),
	Danger = style(Ui.Teintes.Danger, "#7A1020", "#FFFFFF", true, 0.2, 0.4),
	Vert = style(Ui.Teintes.Vert, "#1E8A33", "#0B2A10", false, 0.3, 0.5),
	Base = style(Ui.Teintes.Base, "#17705C", "#06352B", false, 0.3, 0.5),
	Desactive = (function()
		local s = style(Ui.Teintes.Desactive, "#18152C", "#6E6890", false, 0.04, 0.08)
		s.Actif = false
		return s
	end)(),
} :: { [string]: StyleBouton }

-- Polices : FredokaOne (titres, boutons, nombres), Montserrat 500–800 (textes, labels)
Ui.Police = Enum.Font.FredokaOne
function Ui.Montserrat(poids: Enum.FontWeight?): Font
	return Font.new("rbxasset://fonts/families/Montserrat.json", poids or Enum.FontWeight.Medium)
end

local EASE_REBOND = TweenInfo.new(0.12, Enum.EasingStyle.Back, Enum.EasingDirection.Out)

-- Crée une instance, applique `props` puis range `enfants` dedans. `Parent` est appliqué en dernier.
function Ui.Creer(classe: string, props: { [string]: any }, enfants: { Instance }?): any
	local instance = Instance.new(classe)
	for cle, valeur in props do
		if cle ~= "Parent" then
			(instance :: any)[cle] = valeur
		end
	end
	if enfants then
		for _, enfant in enfants do
			enfant.Parent = instance
		end
	end
	if props.Parent then
		instance.Parent = props.Parent
	end
	return instance
end

function Ui.Tween(
	instance: Instance,
	duree: number,
	props: { [string]: any },
	easing: Enum.EasingStyle?,
	direction: Enum.EasingDirection?
): Tween
	local tween = TweenService:Create(
		instance,
		TweenInfo.new(duree, easing or Enum.EasingStyle.Quad, direction or Enum.EasingDirection.Out),
		props
	)
	tween:Play()
	return tween
end

function Ui.Coins(rayon: number): UICorner
	return Ui.Creer("UICorner", { CornerRadius = UDim.new(0, rayon) })
end

function Ui.Rond(): UICorner
	return Ui.Creer("UICorner", { CornerRadius = UDim.new(0.5, 0) })
end

function Ui.Contour(couleur: Color3, epaisseur: number?, transparence: number?): UIStroke
	return Ui.Creer("UIStroke", {
		Color = couleur,
		Thickness = epaisseur or 2,
		Transparency = transparence or 0,
		ApplyStrokeMode = Enum.ApplyStrokeMode.Border,
	})
end

function Ui.Trait(epaisseur: number?): UIStroke
	return Ui.Contour(Ui.C.Trait, epaisseur or 2)
end

function Ui.Marges(haut: number, droite: number?, bas: number?, gauche: number?): UIPadding
	return Ui.Creer("UIPadding", {
		PaddingTop = UDim.new(0, haut),
		PaddingRight = UDim.new(0, droite or haut),
		PaddingBottom = UDim.new(0, bas or haut),
		PaddingLeft = UDim.new(0, gauche or droite or haut),
	})
end

function Ui.Liste(direction: Enum.FillDirection, ecart: number, props: { [string]: any }?): UIListLayout
	local defauts: { [string]: any } = {
		FillDirection = direction,
		Padding = UDim.new(0, ecart),
		SortOrder = Enum.SortOrder.LayoutOrder,
	}
	for cle, valeur in props or {} do
		defauts[cle] = valeur
	end
	return Ui.Creer("UIListLayout", defauts)
end

local function eclaircir(couleur: Color3, alpha: number): Color3
	return couleur:Lerp(Color3.new(1, 1, 1), alpha)
end

-- Dégradé 3 tons (clair 0 %, base 50 %, foncé 100 %). `reflet` > 0 : bande blanche sur les `hauteurReflet` du haut.
-- Rotation Roblox : 90 = de haut en bas (CSS 180°), 70 ≈ CSS 160°.
function Ui.Degrade(t: Teinte, rotation: number?, reflet: number?, hauteurReflet: number?): UIGradient
	local points
	local r = reflet or 0
	if r > 0 then
		local h = hauteurReflet or 0.48
		local milieu = t.Clair:Lerp(t.Base, h / 0.5)
		points = {
			ColorSequenceKeypoint.new(0, eclaircir(t.Clair, r)),
			ColorSequenceKeypoint.new(h - 0.001, eclaircir(milieu, r)),
			ColorSequenceKeypoint.new(h, milieu),
			ColorSequenceKeypoint.new(0.5, t.Base),
			ColorSequenceKeypoint.new(1, t.Fonce),
		}
	else
		points = {
			ColorSequenceKeypoint.new(0, t.Clair),
			ColorSequenceKeypoint.new(0.5, t.Base),
			ColorSequenceKeypoint.new(1, t.Fonce),
		}
	end
	return Ui.Creer("UIGradient", { Color = ColorSequence.new(points), Rotation = rotation or 90 })
end

-- Dégradé 2 couleurs
function Ui.Degrade2(c1: Color3, c2: Color3, rotation: number?): UIGradient
	return Ui.Creer("UIGradient", { Color = ColorSequence.new(c1, c2), Rotation = rotation or 90 })
end

-- Filet doré qui s'efface vers la droite (2 px)
function Ui.Filet(props: { [string]: any }): Frame
	local defauts: { [string]: any } = {
		Name = "Filet",
		BorderSizePixel = 0,
		BackgroundColor3 = Ui.C.Filet,
		Size = UDim2.new(1, 0, 0, 2),
	}
	for cle, valeur in props do
		defauts[cle] = valeur
	end
	return Ui.Creer("Frame", defauts, {
		Ui.Creer("UIGradient", { Transparency = NumberSequence.new(0, 1) }),
	})
end

-- Liseré intérieur : cadre transparent décalé de `retrait` px avec un contour fin.
function Ui.Lisere(
	parent: GuiObject,
	retrait: number,
	rayon: number,
	couleur: Color3,
	transparence: number?,
	epaisseur: number?
): Frame
	return Ui.Creer("Frame", {
		Name = "Lisere",
		Position = UDim2.fromOffset(retrait, retrait),
		Size = UDim2.new(1, -2 * retrait, 1, -2 * retrait),
		BackgroundTransparency = 1,
		ZIndex = parent.ZIndex,
		Parent = parent,
	}, {
		Ui.Coins(math.max(0, rayon - retrait)),
		Ui.Contour(couleur, epaisseur or 1, transparence),
	})
end

-- Contour sombre du texte des titres (ombre 1,5 px de la maquette)
function Ui.ContourTexte(label: TextLabel | TextButton, epaisseur: number?)
	Ui.Creer("UIStroke", {
		Color = Ui.C.Trait,
		Thickness = epaisseur or 1.5,
		ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual,
		Parent = label,
	})
end

-- TextLabel transparent (FredokaOne par défaut ; passer FontFace = Ui.Montserrat(...) pour le texte courant).
function Ui.Texte(props: { [string]: any }): TextLabel
	local defauts: { [string]: any } = {
		BackgroundTransparency = 1,
		TextColor3 = Ui.C.Texte,
		TextSize = 18,
		TextXAlignment = Enum.TextXAlignment.Left,
	}
	if not props.FontFace then
		defauts.Font = Ui.Police
	end
	for cle, valeur in props do
		defauts[cle] = valeur
	end
	local contour = defauts.Contour
	defauts.Contour = nil
	local label = Ui.Creer("TextLabel", defauts)
	if contour then
		Ui.ContourTexte(label, if typeof(contour) == "number" then contour else nil)
	end
	return label
end

-- Icône du handoff (UiConfig.Icones) : image si elle est envoyée, sinon son symbole en texte.
function Ui.Icone(nom: string, taille: number, props: { [string]: any }?): GuiObject
	local icone = UiConfig.Icones[nom]
	local defauts: { [string]: any } = {
		Name = "Icone",
		Size = UDim2.fromOffset(taille, taille),
		BackgroundTransparency = 1,
	}
	for cle, valeur in props or {} do
		defauts[cle] = valeur
	end
	if icone and icone.Image ~= "" then
		defauts.Image = icone.Image
		defauts.ScaleType = Enum.ScaleType.Fit
		defauts.TextColor3 = nil
		return Ui.Creer("ImageLabel", defauts)
	end
	defauts.Font = Ui.Police
	defauts.Text = if icone then icone.Symbole else "?"
	defauts.TextScaled = true
	defauts.TextColor3 = defauts.TextColor3 or Ui.C.Texte
	local label = Ui.Creer("TextLabel", defauts)
	Ui.ContourTexte(label, 1)
	return label
end

-- Rebond au survol (UIScale) et enfoncement à l'appui (face décalée de 3 px, ombre masquée).
function Ui.Reagir(bouton: GuiButton, face: GuiObject?, ombre: GuiObject?, survol: number?, rotation: number?)
	local echelle = bouton:FindFirstChildOfClass("UIScale") or Ui.Creer("UIScale", { Parent = bouton })
	local survole = false
	local function majSurvol()
		local actif = bouton:GetAttribute("Actif") ~= false
		TweenService:Create(echelle, EASE_REBOND, { Scale = if survole and actif then survol or 1.05 else 1 }):Play()
		if rotation then
			TweenService:Create(bouton, EASE_REBOND, { Rotation = if survole and actif then rotation else 0 }):Play()
		end
	end
	local function enfoncer(bas: boolean)
		if bouton:GetAttribute("Actif") == false then
			return
		end
		if face then
			face.Position = if bas then UDim2.fromOffset(0, 3) else UDim2.new()
		end
		if ombre then
			ombre.Visible = not bas
		end
	end
	bouton.MouseEnter:Connect(function()
		survole = true
		majSurvol()
	end)
	bouton.MouseLeave:Connect(function()
		survole = false
		majSurvol()
		enfoncer(false)
	end)
	bouton.MouseButton1Down:Connect(function()
		enfoncer(true)
	end)
	bouton.MouseButton1Up:Connect(function()
		enfoncer(false)
	end)
	bouton:GetAttributeChangedSignal("Actif"):Connect(majSurvol)
end

-- Bouton à 3 tons : conteneur transparent (TextButton) → Ombre (+3 px) → Face (dégradé, trait, liseré) → Label.
-- Options : Texte, Style (nom de Ui.Styles), Taille (Vector2), TailleTexte, Rayon, Icone, TailleIcone, + props du conteneur.
export type OptionsBouton = { [string]: any }

function Ui.Bouton(options: OptionsBouton): TextButton
	local rayon = options.Rayon or 12
	local taille: Vector2 = options.Taille or Vector2.new(150, 50)
	local props: { [string]: any } = {
		Name = options.Name or "Bouton",
		Size = UDim2.fromOffset(taille.X, taille.Y),
		BackgroundTransparency = 1,
		AutoButtonColor = false,
		Text = "",
	}
	for cle, valeur in options do
		if
			cle ~= "Texte"
			and cle ~= "Style"
			and cle ~= "Taille"
			and cle ~= "TailleTexte"
			and cle ~= "Rayon"
			and cle ~= "Icone"
			and cle ~= "TailleIcone"
			and cle ~= "Name"
		then
			props[cle] = valeur
		end
	end
	local bouton = Ui.Creer("TextButton", props)
	local ombre = Ui.Creer("Frame", {
		Name = "Ombre",
		Position = UDim2.fromOffset(0, 3),
		Size = UDim2.fromScale(1, 1),
		BorderSizePixel = 0,
		Parent = bouton,
	}, { Ui.Coins(rayon) })
	local face = Ui.Creer("Frame", {
		Name = "Face",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Color3.new(1, 1, 1),
		BorderSizePixel = 0,
		Parent = bouton,
	}, { Ui.Coins(rayon), Ui.Trait(2) })
	local contenu = Ui.Creer("Frame", {
		Name = "Contenu",
		Size = UDim2.fromScale(1, 1),
		BackgroundTransparency = 1,
		Parent = face,
	}, {
		Ui.Liste(Enum.FillDirection.Horizontal, 8, {
			HorizontalAlignment = Enum.HorizontalAlignment.Center,
			VerticalAlignment = Enum.VerticalAlignment.Center,
		}),
	})
	if options.Icone then
		local tailleIcone = options.TailleIcone or math.floor(taille.Y * 0.62)
		Ui.Icone(options.Icone, tailleIcone, { LayoutOrder = 1, Parent = contenu })
	end
	Ui.Texte({
		Name = "Label",
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromScale(0, 1),
		TextSize = options.TailleTexte or 19,
		Text = options.Texte or "",
		Parent = contenu,
	})
	Ui.ChangerStyle(bouton, options.Style or "Principal")
	Ui.Reagir(bouton, face, ombre)
	return bouton
end

-- Change le style d'un bouton créé par Ui.Bouton (dégradé, ombre, texte, état actif).
function Ui.ChangerStyle(bouton: TextButton, nom: string)
	local s = Ui.Styles[nom] or Ui.Styles.Principal
	local face = bouton:FindFirstChild("Face") :: Frame
	local ombre = bouton:FindFirstChild("Ombre") :: Frame
	local rayon = (face:FindFirstChildOfClass("UICorner") :: UICorner).CornerRadius.Offset
	local ancien = face:FindFirstChildOfClass("UIGradient")
	if ancien then
		ancien:Destroy()
	end
	Ui.Degrade(s.Teinte, 90, s.Reflet).Parent = face
	local lisere = face:FindFirstChild("Lisere")
	if lisere then
		lisere:Destroy()
	end
	Ui.Lisere(face, 2, rayon, Color3.new(1, 1, 1), 1 - s.Lisere)
	ombre.BackgroundColor3 = s.Ombre
	local label = face:FindFirstChild("Label", true) :: TextLabel
	label.TextColor3 = s.Texte
	local contour = label:FindFirstChildOfClass("UIStroke")
	if s.ContourTexte and not contour then
		Ui.ContourTexte(label)
	elseif not s.ContourTexte and contour then
		contour:Destroy()
	end
	bouton:SetAttribute("Actif", s.Actif)
	bouton.Active = s.Actif
end

function Ui.ChangerTexte(bouton: TextButton, texte: string)
	local label = bouton:FindFirstChild("Label", true)
	if label and label:IsA("TextLabel") then
		label.Text = texte
	end
end

-- Un UIGradient teinte aussi le texte de son parent : les éléments à fond dégradé portent donc leur texte
-- dans un label enfant transparent. Renvoie le cadre (fond) et le label.
function Ui.EtiquetteDegrade(props: { [string]: any }, gradient: UIGradient, labelProps: { [string]: any }): (Frame, TextLabel)
	local defauts: { [string]: any } = {
		AutomaticSize = Enum.AutomaticSize.X,
		BackgroundColor3 = Color3.new(1, 1, 1),
	}
	for cle, valeur in props do
		defauts[cle] = valeur
	end
	local cadre = Ui.Creer("Frame", defauts)
	gradient.Parent = cadre
	local proprietesLabel: { [string]: any } = {
		Name = "Label",
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromScale(0, 1),
		TextXAlignment = Enum.TextXAlignment.Center,
		ZIndex = cadre.ZIndex,
		Parent = cadre,
	}
	for cle, valeur in labelProps do
		proprietesLabel[cle] = valeur
	end
	return cadre, Ui.Texte(proprietesLabel)
end

-- Pastille rouge en haut à droite (badge « ! », « 3 »…). Renvoie le label (son parent est la pastille).
function Ui.Pastille(parent: GuiObject, texte: string): TextLabel
	local pastille, label = Ui.EtiquetteDegrade({
		Name = "Pastille",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(1, -3, 0, 3),
		Size = UDim2.fromOffset(22, 22),
		ZIndex = parent.ZIndex + 5,
		Parent = parent,
	}, Ui.Degrade2(Ui.C.Pastille1, Ui.C.Pastille2), { TextSize = 13, Text = texte })
	Ui.Rond().Parent = pastille
	Ui.Trait(2).Parent = pastille
	Ui.Marges(0, 5).Parent = pastille
	return label
end

-- Bouton icône (menu) : carré coloré par fonction, dégradé 160°, reflet, liseré blanc, ombre pleine.
-- Options : Icone, Teinte, Taille (px), Rayon, TailleIcone, Libelle (texte sous le bouton), + props du conteneur.
function Ui.BoutonIcone(options: { [string]: any }): TextButton
	local taille = options.Taille or 60
	local rayon = options.Rayon or 14
	local libelle = options.Libelle
	local hauteur = if libelle then taille + 16 else taille
	local props: { [string]: any } = {
		Name = options.Name or "BoutonIcone",
		Size = UDim2.fromOffset(math.max(taille, 64), hauteur),
		BackgroundTransparency = 1,
		AutoButtonColor = false,
		Text = "",
	}
	for cle, valeur in options do
		if
			cle ~= "Icone"
			and cle ~= "Teinte"
			and cle ~= "Taille"
			and cle ~= "Rayon"
			and cle ~= "TailleIcone"
			and cle ~= "Libelle"
			and cle ~= "Name"
		then
			props[cle] = valeur
		end
	end
	local bouton = Ui.Creer("TextButton", props)
	local carre = Ui.Creer("Frame", {
		Name = "Carre",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.fromScale(0.5, 0),
		Size = UDim2.fromOffset(taille, taille),
		BackgroundTransparency = 1,
		Parent = bouton,
	})
	local ombre = Ui.Creer("Frame", {
		Name = "Ombre",
		Position = UDim2.fromOffset(0, 3),
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Ui.C.Trait,
		Parent = carre,
	}, { Ui.Coins(rayon) })
	local face = Ui.Creer("Frame", {
		Name = "Face",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Color3.new(1, 1, 1),
		Parent = carre,
	}, { Ui.Coins(rayon), Ui.Trait(2), Ui.Degrade(options.Teinte, 70, 0.2, 0.44) })
	Ui.Lisere(face, 2, rayon, Color3.new(1, 1, 1), 0.35, 1.5)
	Ui.Icone(options.Icone, options.TailleIcone or math.floor(taille * 0.7), {
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Parent = face,
	})
	if libelle then
		Ui.Texte({
			Name = "Libelle",
			Position = UDim2.fromOffset(0, taille + 2),
			Size = UDim2.new(1, 0, 0, 14),
			TextSize = 12,
			TextXAlignment = Enum.TextXAlignment.Center,
			Text = libelle,
			Contour = true,
			Parent = bouton,
		})
	end
	Ui.Reagir(bouton, face, ombre, 1.1, -4)
	return bouton
end

-- Panneau sombre (dégradé #2A2350 → #17132E, trait 2 px, liseré intérieur #5A4E9E, ombre pleine en dessous).
-- Renvoie le conteneur (à placer) et la face (où ranger le contenu).
function Ui.Panneau(props: { [string]: any }, rayon: number?, transparence: number?): (Frame, Frame)
	local r = rayon or 16
	local defauts: { [string]: any } = { BackgroundTransparency = 1 }
	for cle, valeur in props do
		defauts[cle] = valeur
	end
	local conteneur = Ui.Creer("Frame", defauts)
	Ui.Creer("Frame", {
		Name = "Ombre",
		Position = UDim2.fromOffset(0, 4),
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Ui.C.Trait,
		BackgroundTransparency = transparence or 0,
		Parent = conteneur,
	}, { Ui.Coins(r) })
	local face = Ui.Creer("Frame", {
		Name = "Face",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Color3.new(1, 1, 1),
		BackgroundTransparency = transparence or 0,
		Parent = conteneur,
	}, {
		Ui.Coins(r),
		Ui.Trait(2),
		Ui.Degrade2(Ui.C.PanneauHaut, Ui.C.PanneauBas),
	})
	Ui.Lisere(face, 3, r, Ui.C.Lisere)
	return conteneur, face
end

-- Zone de contenu (#1C1738, liseré #3E3478, coins 12)
function Ui.Zone(props: { [string]: any }): Frame
	local defauts: { [string]: any } = { BackgroundColor3 = Ui.C.Zone }
	for cle, valeur in props do
		defauts[cle] = valeur
	end
	return Ui.Creer("Frame", defauts, { Ui.Coins(12), Ui.Contour(Ui.C.LisereSombre, 1) })
end

-- Fenêtres : une seule ouverte à la fois, fond assombri, apparition avec rebond.
export type Fenetre = {
	Racine: Frame, -- plein écran (fond assombri + fenêtre)
	Cadre: Frame, -- la fenêtre
	Contenu: Frame, -- sous l'en-tête et le filet doré
	Ouvrir: () -> (),
	Fermer: () -> (),
	Basculer: () -> (),
	EstOuverte: () -> boolean,
	AuChangement: (rappel: (ouverte: boolean) -> ()) -> (),
}

local fenetreOuverte: Fenetre? = nil
local racineUi: Frame? = nil

-- Options : Nom, Titre, SousTitre, Icone, Ruban (Teinte), Taille (Vector2), Position (UDim2, centre par défaut)
function Ui.Fenetre(options: { [string]: any }): Fenetre
	assert(racineUi, "Ui.Racine doit être appelé avant Ui.Fenetre")
	local taille: Vector2 = options.Taille or Vector2.new(790, 514)
	local racine = Ui.Creer("Frame", {
		Name = options.Nom or "Fenetre",
		Size = UDim2.fromScale(1, 1),
		BackgroundTransparency = 1,
		Visible = false,
		ZIndex = 20,
		Parent = racineUi,
	})
	local voile = Ui.Creer("TextButton", {
		Name = "Voile",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = hex("#080612"),
		BackgroundTransparency = 0.38,
		AutoButtonColor = false,
		Text = "",
		Parent = racine,
	})
	local echelle = Ui.Creer("UIScale", {})
	local cadre, face = Ui.Panneau({
		Name = "Cadre",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = options.Position or UDim2.new(0.5, 0, 0.5, 6),
		Size = UDim2.fromOffset(taille.X, taille.Y),
		Active = true,
		Parent = racine,
	}, 16)
	echelle.Parent = cadre

	-- En-tête H 58 : ruban coloré + icône qui dépasse, titre, sous-titre, bouton fermer
	local entete = Ui.Creer("Frame", {
		Name = "Entete",
		Size = UDim2.new(1, 0, 0, 58),
		BackgroundTransparency = 1,
		Parent = face,
	})
	local ruban = Ui.Creer("Frame", {
		Name = "Ruban",
		Position = UDim2.fromOffset(14, 9),
		Size = UDim2.fromOffset(76, 40),
		BackgroundColor3 = Color3.new(1, 1, 1),
		Parent = entete,
	}, {
		Ui.Coins(8),
		Ui.Degrade2((options.Ruban :: Teinte).Clair, (options.Ruban :: Teinte).Base),
	})
	Ui.Icone(options.Icone, 46, {
		Position = UDim2.fromOffset(15, -9),
		Parent = ruban,
	})
	local titres = Ui.Creer("Frame", {
		Name = "Titres",
		Position = UDim2.fromOffset(102, 0),
		Size = UDim2.new(1, -160, 1, 0),
		BackgroundTransparency = 1,
		Parent = entete,
	}, {
		Ui.Liste(Enum.FillDirection.Horizontal, 12, { VerticalAlignment = Enum.VerticalAlignment.Center }),
	})
	local labelTitre = Ui.Texte({
		Name = "Titre",
		LayoutOrder = 1,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		TextSize = 24,
		Text = options.Titre or "",
		Contour = 2,
		Parent = titres,
	})
	local labelSousTitre = Ui.Texte({
		Name = "SousTitre",
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 20),
		FontFace = Ui.Montserrat(Enum.FontWeight.SemiBold),
		TextSize = 12,
		TextColor3 = Ui.C.TexteDiscret,
		Text = options.SousTitre or "",
		Parent = titres,
	})
	local boutonFermer = Ui.Bouton({
		Name = "Fermer",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, -12, 0, 10),
		Taille = Vector2.new(38, 38),
		Rayon = 10,
		Style = "Danger",
		Texte = "X", -- FredokaOne n'a pas ✕
		TailleTexte = 20,
		Parent = entete,
	})
	Ui.Filet({ Position = UDim2.fromOffset(14, 58), Size = UDim2.new(1, -28, 0, 2), Parent = face })
	local contenu = Ui.Creer("Frame", {
		Name = "Contenu",
		Position = UDim2.fromOffset(0, 60),
		Size = UDim2.new(1, 0, 1, -60),
		BackgroundTransparency = 1,
		Parent = face,
	})

	local rappels: { (boolean) -> () } = {}
	local fenetre: Fenetre
	local function notifier(ouverte: boolean)
		for _, rappel in rappels do
			task.spawn(rappel, ouverte)
		end
	end
	fenetre = {
		Racine = racine,
		Cadre = cadre,
		Contenu = contenu,
		Ouvrir = function()
			if fenetreOuverte == fenetre then
				return
			end
			if fenetreOuverte then
				fenetreOuverte.Fermer()
			end
			fenetreOuverte = fenetre
			racine.Visible = true
			echelle.Scale = 0.8
			Ui.Tween(echelle, 0.28, { Scale = 1 }, Enum.EasingStyle.Back)
			notifier(true)
		end,
		Fermer = function()
			if not racine.Visible then
				return
			end
			racine.Visible = false
			if fenetreOuverte == fenetre then
				fenetreOuverte = nil
			end
			notifier(false)
		end,
		Basculer = function()
			if racine.Visible then
				fenetre.Fermer()
			else
				fenetre.Ouvrir()
			end
		end,
		EstOuverte = function()
			return racine.Visible
		end,
		AuChangement = function(rappel)
			table.insert(rappels, rappel)
		end,
	}
	voile.Activated:Connect(fenetre.Fermer)
	boutonFermer.Activated:Connect(fenetre.Fermer)
	labelTitre:SetAttribute("Fenetre", true)
	labelSousTitre:SetAttribute("Fenetre", true)
	return fenetre
end

function Ui.FermerFenetre()
	if fenetreOuverte then
		fenetreOuverte.Fermer()
	end
end

-- Onglets : plateau sombre, onglet actif au dégradé `teinteActive`. Renvoie le plateau et une fonction de sélection.
function Ui.Onglets(
	noms: { string },
	auChoix: (index: number) -> (),
	props: { [string]: any },
	teinteActive: Teinte?,
	hauteur: number?
): (Frame, (index: number) -> ())
	local h = hauteur or 36
	local defauts: { [string]: any } = {
		Name = "Onglets",
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, h + 8),
		BackgroundColor3 = Ui.C.Trait,
	}
	for cle, valeur in props do
		defauts[cle] = valeur
	end
	local plateau = Ui.Creer("Frame", defauts, {
		Ui.Coins(12),
		Ui.Contour(hex("#2E2758"), 1),
		Ui.Marges(4),
		Ui.Liste(Enum.FillDirection.Horizontal, 4),
	})
	local t = teinteActive or Ui.Teintes.Principal
	local texteActif = if t == Ui.Teintes.Vert then hex("#0B2A10") else Ui.C.Texte
	local onglets: { TextButton } = {}
	local function choisir(index: number)
		for i, onglet in onglets do
			local actif = i == index
			onglet.BackgroundTransparency = if actif then 0 else 1
			local label = onglet:FindFirstChild("Label") :: TextLabel
			label.TextColor3 = if actif then texteActif else Ui.C.TexteDiscret
		end
	end
	for i, nom in noms do
		local onglet = Ui.Creer("TextButton", {
			Name = nom,
			LayoutOrder = i,
			AutomaticSize = Enum.AutomaticSize.X,
			Size = UDim2.fromOffset(0, h),
			BackgroundColor3 = Color3.new(1, 1, 1),
			AutoButtonColor = false,
			Text = "",
			Parent = plateau,
		}, { Ui.Coins(9), Ui.Marges(0, 16), Ui.Degrade(t, 90, 0.2) })
		Ui.Texte({
			Name = "Label",
			AutomaticSize = Enum.AutomaticSize.X,
			Size = UDim2.fromScale(0, 1),
			TextSize = 16,
			Text = nom,
			Parent = onglet,
		})
		onglet.Activated:Connect(function()
			choisir(i)
			auChoix(i)
		end)
		onglets[i] = onglet
	end
	choisir(1)
	return plateau, choisir
end

-- Barre de progression (fond #120E26, remplissage 3 tons, curseur blanc, texte centré). Renvoie la barre et sa mise à jour.
function Ui.Barre(props: { [string]: any }, t: Teinte?): (Frame, (fraction: number, texte: string) -> ())
	local defauts: { [string]: any } = {
		Name = "Barre",
		Size = UDim2.fromOffset(300, 24),
		BackgroundColor3 = Ui.C.FondBarre,
		ClipsDescendants = true,
	}
	for cle, valeur in props do
		defauts[cle] = valeur
	end
	local barre = Ui.Creer("Frame", defauts, { Ui.Coins(12), Ui.Trait(2) })
	local remplissage = Ui.Creer("Frame", {
		Name = "Remplissage",
		Size = UDim2.fromScale(0, 1),
		BackgroundColor3 = Color3.new(1, 1, 1),
		Parent = barre,
	}, { Ui.Coins(12), Ui.Degrade(t or Ui.Teintes.Vert, 90, 0.3, 0.45) })
	Ui.Creer("Frame", {
		Name = "Curseur",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.fromScale(1, 0),
		Size = UDim2.new(0, 6, 1, 0),
		BackgroundColor3 = Color3.new(1, 1, 1),
		BackgroundTransparency = 0.2,
		BorderSizePixel = 0,
		Parent = remplissage,
	})
	local label = Ui.Texte({
		Size = UDim2.fromScale(1, 1),
		TextSize = 14,
		TextXAlignment = Enum.TextXAlignment.Center,
		Contour = true,
		ZIndex = 3,
		Parent = barre,
	})
	return barre,
		function(fraction: number, texte: string)
			local f = math.clamp(fraction, 0, 1)
			remplissage.Size = UDim2.fromScale(f, 1)
			remplissage.Visible = f > 0
			label.Text = texte
		end
end

-- Interrupteur (50 × 28, vert quand actif). Renvoie le bouton et sa mise à jour.
function Ui.Interrupteur(
	props: { [string]: any },
	auChangement: (actif: boolean) -> ()
): (TextButton, (actif: boolean) -> ())
	local defauts: { [string]: any } = {
		Name = "Interrupteur",
		Size = UDim2.fromOffset(50, 28),
		AutoButtonColor = false,
		Text = "",
		BackgroundColor3 = Ui.C.Desactive,
	}
	for cle, valeur in props do
		defauts[cle] = valeur
	end
	local bouton = Ui.Creer("TextButton", defauts, { Ui.Rond(), Ui.Trait(1.5) })
	local fond = Ui.Creer("UIGradient", { Color = ColorSequence.new(hex("#B6FFB0"), hex("#3FCB52")), Rotation = 90 })
	local bille = Ui.Creer("Frame", {
		Name = "Bille",
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.new(0, 3, 0.5, 0),
		Size = UDim2.fromOffset(20, 20),
		BackgroundColor3 = Color3.new(1, 1, 1),
		Parent = bouton,
	}, { Ui.Rond(), Ui.Trait(1.5), Ui.Degrade2(Color3.new(1, 1, 1), hex("#D2CDEB")) })
	local actif = false
	local function maj(valeur: boolean)
		actif = valeur
		bouton.BackgroundColor3 = if actif then Color3.new(1, 1, 1) else Ui.C.Desactive
		fond.Parent = if actif then bouton else nil
		Ui.Tween(bille, 0.15, { Position = UDim2.new(0, if actif then 26 else 3, 0.5, 0) })
	end
	bouton.Activated:Connect(function()
		maj(not actif)
		auChangement(actif)
	end)
	return bouton, maj
end

-- Étoiles en icônes (pleines puis vides), dans un cadre horizontal.
function Ui.EtoilesIcones(etoiles: number, max: number, taille: number, props: { [string]: any }?): Frame
	local defauts: { [string]: any } = {
		Name = "Etoiles",
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, taille),
		BackgroundTransparency = 1,
	}
	for cle, valeur in props or {} do
		defauts[cle] = valeur
	end
	local cadre = Ui.Creer("Frame", defauts, { Ui.Liste(Enum.FillDirection.Horizontal, 1) })
	for i = 1, max do
		local pleine = i <= etoiles
		Ui.Icone(if pleine then "etoile" else "etoile_vide", taille, {
			LayoutOrder = i,
			TextColor3 = if pleine then hex("#FFC93C") else Ui.C.TexteEteint,
			Parent = cadre,
		})
	end
	return cadre
end

-- Racine à l'échelle de la maquette : enfant de l'écran, taille = écran / échelle, UIScale = échelle.
-- Les enfants sont donc placés en pixels de maquette (1100 × 650) et ancrés aux bords réels de l'écran.
local LARGEUR_REF, HAUTEUR_REF = 1100, 650
Ui.Echelle = 1

function Ui.Racine(ecran: ScreenGui): Frame
	local racine = Ui.Creer("Frame", {
		Name = "Racine",
		BackgroundTransparency = 1,
		Parent = ecran,
	})
	local echelle = Ui.Creer("UIScale", { Parent = racine })
	local function maj()
		local taille = ecran.AbsoluteSize
		if taille.X <= 0 or taille.Y <= 0 then
			return
		end
		local valeur = math.clamp(math.min(taille.X / LARGEUR_REF, taille.Y / HAUTEUR_REF), 0.5, 1.4)
		Ui.Echelle = valeur
		echelle.Scale = valeur
		racine.Size = UDim2.fromOffset(taille.X / valeur, taille.Y / valeur)
	end
	ecran:GetPropertyChangedSignal("AbsoluteSize"):Connect(maj)
	maj()
	racineUi = racine
	return racine
end

local SUFFIXES = { "", "K", "M", "B", "T", "Qa", "Qi" }

-- 950 → "950", 1234 → "1,23K", 45600 → "45,6K", 2 500 000 → "2,5M"
function Ui.FormaterNombre(nombre: number): string
	if nombre < 1000 then
		return tostring(math.floor(nombre))
	end
	local valeur, rang = nombre, 1
	while valeur >= 1000 and rang < #SUFFIXES do
		valeur /= 1000
		rang += 1
	end
	local decimales = if valeur < 10 then 2 elseif valeur < 100 then 1 else 0
	local facteur = 10 ^ decimales
	local texte = string.format(`%.{decimales}f`, math.floor(valeur * facteur) / facteur)
	if decimales > 0 then
		texte = (texte:gsub("0+$", ""):gsub("%.$", ""))
	end
	return (texte:gsub("%.", ",")) .. SUFFIXES[rang]
end

-- Revenu par seconde : une décimale en dessous de 1000 (12,5), sinon comme FormaterNombre.
function Ui.FormaterRevenu(revenu: number): string
	if revenu >= 1000 then
		return Ui.FormaterNombre(revenu)
	end
	local arrondi = math.round(revenu * 10) / 10
	local texte = if arrondi % 1 == 0 then tostring(arrondi) else string.format("%.1f", arrondi)
	return (texte:gsub("%.", ","))
end

-- Majuscules avec les lettres accentuées (string.upper ne traite que l'ASCII) : « Légendaire » → « LÉGENDAIRE »
local ACCENTS = { ["é"] = "É", ["è"] = "È", ["ê"] = "Ê", ["à"] = "À", ["â"] = "Â", ["ô"] = "Ô", ["ç"] = "Ç", ["î"] = "Î", ["û"] = "Û" }
function Ui.Majuscules(texte: string): string
	local resultat = string.upper(texte)
	for minuscule, majuscule in ACCENTS do
		resultat = string.gsub(resultat, minuscule, majuscule)
	end
	return resultat
end

-- Pourcentage à la française : 4.9 → "4,9 %", 1.6333 → "1,63 %"
function Ui.FormaterPourcent(valeur: number): string
	local texte = string.format("%.2f", valeur):gsub("0+$", ""):gsub("%.$", "")
	return (texte:gsub("%.", ",")) .. " %"
end

return Ui
