--!strict
-- Ui : construction des éléments d'interface, couleurs, adaptation à la taille d'écran et format des nombres.

local Ui = {}

Ui.Couleurs = {
	Fond = Color3.fromRGB(24, 22, 38),
	FondClair = Color3.fromRGB(42, 38, 66),
	Contour = Color3.fromRGB(96, 84, 150),
	Texte = Color3.fromRGB(255, 255, 255),
	TexteDiscret = Color3.fromRGB(185, 180, 210),
	Or = Color3.fromRGB(255, 205, 60),
	Vert = Color3.fromRGB(110, 230, 120),
	Bouton = Color3.fromRGB(100, 72, 210),
	BoutonSecondaire = Color3.fromRGB(70, 66, 96),
}
Ui.Police = Enum.Font.FredokaOne
Ui.PoliceTexte = Enum.Font.GothamMedium

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

function Ui.Coins(rayon: number): UICorner
	return Ui.Creer("UICorner", { CornerRadius = UDim.new(0, rayon) })
end

function Ui.Contour(couleur: Color3, epaisseur: number?): UIStroke
	return Ui.Creer("UIStroke", {
		Color = couleur,
		Thickness = epaisseur or 2,
		ApplyStrokeMode = Enum.ApplyStrokeMode.Border,
	})
end

function Ui.Marges(px: number): UIPadding
	local marge = UDim.new(0, px)
	return Ui.Creer(
		"UIPadding",
		{ PaddingTop = marge, PaddingBottom = marge, PaddingLeft = marge, PaddingRight = marge }
	)
end

-- TextLabel transparent avec les réglages par défaut du jeu.
function Ui.Texte(props: { [string]: any }): TextLabel
	local defauts: { [string]: any } = {
		BackgroundTransparency = 1,
		Font = Ui.Police,
		TextColor3 = Ui.Couleurs.Texte,
		TextSize = 18,
		TextXAlignment = Enum.TextXAlignment.Left,
	}
	for cle, valeur in props do
		defauts[cle] = valeur
	end
	return Ui.Creer("TextLabel", defauts)
end

function Ui.Bouton(props: { [string]: any }): TextButton
	local defauts: { [string]: any } = {
		BackgroundColor3 = Ui.Couleurs.Bouton,
		AutoButtonColor = true,
		Font = Ui.Police,
		TextColor3 = Ui.Couleurs.Texte,
		TextSize = 18,
	}
	for cle, valeur in props do
		defauts[cle] = valeur
	end
	local bouton = Ui.Creer("TextButton", defauts)
	Ui.Coins(10).Parent = bouton
	return bouton
end

-- Mise à l'échelle selon la taille de l'écran (interface conçue pour 1100 × 650).
local LARGEUR_REF, HAUTEUR_REF = 1100, 650
local echelles: { UIScale } = {}

local function echelleActuelle(): number
	local camera = workspace.CurrentCamera
	local taille = if camera then camera.ViewportSize else Vector2.new(LARGEUR_REF, HAUTEUR_REF)
	return math.clamp(math.min(taille.X / LARGEUR_REF, taille.Y / HAUTEUR_REF), 0.5, 1)
end

local function rafraichirEchelles()
	local valeur = echelleActuelle()
	for _, echelle in echelles do
		echelle.Scale = valeur
	end
end

local connexionCamera: RBXScriptConnection? = nil
local function suivreCamera()
	if connexionCamera then
		connexionCamera:Disconnect()
	end
	local camera = workspace.CurrentCamera
	if camera then
		connexionCamera = camera:GetPropertyChangedSignal("ViewportSize"):Connect(rafraichirEchelles)
	end
	rafraichirEchelles()
end
workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(suivreCamera)
suivreCamera()

-- Ajoute à `gui` un UIScale qui suit la taille de l'écran.
function Ui.Adapter(gui: GuiObject)
	local echelle = Ui.Creer("UIScale", { Scale = echelleActuelle(), Parent = gui })
	table.insert(echelles, echelle)
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

function Ui.Etoiles(etoiles: number, max: number): string
	return string.rep("★", etoiles) .. string.rep("☆", max - etoiles)
end

return Ui
