--!strict
-- Hud (HUD v3 du handoff, sans les offres) : argent avec la liasse de billets, revenu par seconde, argent à collecter,
-- barre de gauche (Téléportation, Inventaire, Index), Boutique et Réglages en haut à droite.
-- Les autres modules branchent les boutons avec Hud.SurMenu et posent des pastilles avec Hud.Pastille.

local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Remotes = require(ReplicatedStorage.Shared.Remotes)
local UiConfig = require(ReplicatedStorage.Shared.UiConfig)
local Ui = require(script.Parent.Ui)

local Hud = {}

local joueur = Players.LocalPlayer
local DUREE_COMPTEUR = 0.4

-- Barre de gauche : 3 boutons essentiels ; en haut à droite : petits boutons sans libellé
local MENU = {
	{ Id = "teleport", Nom = "Téléport." },
	{ Id = "inventaire", Nom = "Inventaire" },
	{ Id = "index", Nom = "Index" },
}
local MENU_HAUT = { "boutique", "parametres" }
local A_VENIR: { [string]: string } = {
	boutique = "Boutique : bientôt disponible",
	parametres = "Réglages : bientôt disponibles",
	stats = "Mes stats : bientôt disponibles",
}

local labelArgent: TextLabel
local labelRevenu: TextLabel
local labelCollecte: TextLabel
local boutons: { [string]: TextButton } = {}
local pastilles: { [string]: TextLabel } = {}
local rappels: { [string]: () -> () } = {}
local notifier: ((string, string?) -> ())? = nil

Hud.Boosts = nil :: Frame? -- rangée sous l'argent pour les boosts actifs (offres 1f, plus tard)

local function pastille(teinte: Ui.Teinte, hauteur: number): Frame
	local cadre = Ui.Creer("Frame", {
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, hauteur),
		BackgroundColor3 = Color3.new(1, 1, 1),
	}, { Ui.Coins(8), Ui.Trait(1.5), Ui.Degrade(teinte, 90, 0.3, 0.45) })
	return cadre
end

local function construireArgent(racine: Frame)
	local colonne = Ui.Creer("Frame", {
		Name = "Argent",
		Position = UDim2.fromOffset(72, 12),
		Size = UDim2.fromOffset(400, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		Parent = racine,
	}, { Ui.Liste(Enum.FillDirection.Vertical, 9) })

	-- Compteur : panneau H 50, liasse de 58 px qui déborde de −6 px, filet doré en bas
	local compteur = Ui.Creer("Frame", {
		Name = "Compteur",
		LayoutOrder = 1,
		Size = UDim2.fromOffset(210, 50),
		BackgroundTransparency = 1,
		Parent = colonne,
	})
	Ui.Creer("Frame", {
		Name = "Ombre",
		Position = UDim2.fromOffset(0, 3),
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Ui.C.Trait,
		Parent = compteur,
	}, { Ui.Coins(12) })
	local face = Ui.Creer("Frame", {
		Name = "Face",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Color3.new(1, 1, 1),
		BackgroundTransparency = 0.06,
		Parent = compteur,
	}, {
		Ui.Coins(12),
		Ui.Trait(2),
		Ui.Degrade2(Ui.C.PanneauHaut, Ui.C.PanneauBas),
	})
	Ui.Lisere(face, 2, 12, Ui.C.Lisere)
	Ui.Filet({ Position = UDim2.new(0, 14, 1, -6), Size = UDim2.new(1, -28, 0, 2), Parent = face })
	labelArgent = Ui.Texte({
		Name = "Montant",
		Position = UDim2.fromOffset(56, 0),
		Size = UDim2.new(1, -78, 1, 0),
		TextSize = 30,
		TextColor3 = Ui.C.Or,
		Text = "0",
		Contour = true,
		Parent = face,
	})
	-- largeur : 56 (liasse) + montant + 22, au moins 210
	labelArgent:GetPropertyChangedSignal("TextBounds"):Connect(function()
		compteur.Size = UDim2.fromOffset(math.max(210, 56 + labelArgent.TextBounds.X + 22), 50)
	end)
	Ui.Icone("billets", 58, { Position = UDim2.fromOffset(-6, -6), ZIndex = 3, Parent = compteur })

	-- Pastilles : revenu (vert) et argent à collecter
	local rangee = Ui.Creer("Frame", {
		Name = "Pastilles",
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.XY,
		BackgroundTransparency = 1,
		Parent = colonne,
	}, { Ui.Liste(Enum.FillDirection.Horizontal, 6) })
	local revenu = pastille(Ui.Teintes.Vert, 28)
	revenu.Name = "Revenu"
	revenu.LayoutOrder = 1
	revenu.Parent = rangee
	Ui.Marges(0, 11).Parent = revenu
	labelRevenu = Ui.Texte({
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromScale(0, 1),
		TextSize = 15,
		TextColor3 = Color3.fromHex("#0B2A10"),
		Text = "+0 $/s",
		Parent = revenu,
	})

	local collecte = Ui.Creer("Frame", {
		Name = "ACollecter",
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 28),
		BackgroundColor3 = Ui.C.Trait,
		BackgroundTransparency = 0.1,
		Parent = rangee,
	}, {
		Ui.Coins(8),
		Ui.Contour(Ui.C.LisereSombre, 1.5),
		Ui.Marges(0, 11, 0, 5),
		Ui.Liste(Enum.FillDirection.Horizontal, 6, { VerticalAlignment = Enum.VerticalAlignment.Center }),
	})
	Ui.Icone("billets", 20, { LayoutOrder = 1, Parent = collecte })
	Ui.Texte({
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromScale(0, 1),
		FontFace = Ui.Montserrat(Enum.FontWeight.Bold),
		TextSize = 10,
		TextColor3 = Ui.C.TexteDiscret,
		Text = "À COLLECTER",
		Parent = collecte,
	})
	labelCollecte = Ui.Texte({
		LayoutOrder = 3,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromScale(0, 1),
		TextSize = 15,
		TextColor3 = Ui.C.Or,
		Text = "0",
		Parent = collecte,
	})

	Hud.Boosts = Ui.Creer("Frame", {
		Name = "Boosts",
		LayoutOrder = 3,
		AutomaticSize = Enum.AutomaticSize.XY,
		BackgroundTransparency = 1,
		Parent = colonne,
	}, { Ui.Liste(Enum.FillDirection.Horizontal, 6) })
end

-- Bouton du menu `id` : rappel branché par Hud.SurMenu, sinon toast « bientôt ».
local function activer(id: string)
	local rappel = rappels[id]
	if rappel then
		rappel()
	elseif notifier and A_VENIR[id] then
		notifier(A_VENIR[id], "info")
	end
end

local function construireMenus(racine: Frame)
	local gauche = Ui.Creer("Frame", {
		Name = "MenuGauche",
		Position = UDim2.fromOffset(12, 220),
		Size = UDim2.fromOffset(64, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		Parent = racine,
	}, { Ui.Liste(Enum.FillDirection.Vertical, 8) })
	for ordre, entree in MENU do
		local bouton = Ui.BoutonIcone({
			Name = entree.Id,
			LayoutOrder = ordre,
			Icone = entree.Id,
			Teinte = UiConfig.CouleursFonctions[entree.Id],
			Taille = 58,
			TailleIcone = 40,
			Libelle = entree.Nom,
			Parent = gauche,
		})
		bouton.Activated:Connect(function()
			activer(entree.Id)
		end)
		boutons[entree.Id] = bouton
	end

	local haut = Ui.Creer("Frame", {
		Name = "MenuHaut",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, -72, 0, 12),
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 50),
		BackgroundTransparency = 1,
		Parent = racine,
	}, { Ui.Liste(Enum.FillDirection.Horizontal, 8) })
	for ordre, id in MENU_HAUT do
		local bouton = Ui.BoutonIcone({
			Name = id,
			LayoutOrder = ordre,
			Size = UDim2.fromOffset(46, 49),
			Icone = id,
			Teinte = UiConfig.CouleursFonctions[id],
			Taille = 46,
			Rayon = 12,
			TailleIcone = 30,
			Parent = haut,
		})
		bouton.Size = UDim2.fromOffset(46, 49)
		bouton.Activated:Connect(function()
			activer(id)
		end)
		boutons[id] = bouton
	end
end

-- La barre de Roblox (menu, chat, voix…) est plus large que dans la maquette (60 px) : l'argent se place juste
-- à sa droite et les boutons du haut juste à gauche de ses boutons de droite (GuiService.TopbarInset).
local function suivreBarreRoblox(racine: Frame)
	local argent = racine:FindFirstChild("Argent") :: Frame
	local menuHaut = racine:FindFirstChild("MenuHaut") :: Frame
	local ecran = racine.Parent :: ScreenGui
	local function maj()
		local zone = GuiService.TopbarInset
		local echelle = math.max(Ui.Echelle, 0.01)
		local gauche = if zone.Width > 0 then zone.Min.X / echelle + 12 else 72
		local droite = if zone.Width > 0 then (ecran.AbsoluteSize.X - zone.Max.X) / echelle + 12 else 72
		argent.Position = UDim2.fromOffset(math.max(72, gauche), 12)
		menuHaut.Position = UDim2.new(1, -math.max(72, droite), 0, 12)
	end
	GuiService:GetPropertyChangedSignal("TopbarInset"):Connect(maj)
	ecran:GetPropertyChangedSignal("AbsoluteSize"):Connect(maj)
	maj()
end

function Hud.Init(racine: Frame, notifierToast: (string, string?) -> ())
	notifier = notifierToast
	construireArgent(racine)
	construireMenus(racine)
	suivreBarreRoblox(racine)

	local function majCollecte()
		local montant = joueur:GetAttribute(Remotes.Attributs.ArgentNonCollecte)
		labelCollecte.Text = Ui.FormaterNombre(if typeof(montant) == "number" then montant else 0)
	end
	local function majRevenu()
		local revenu = joueur:GetAttribute(Remotes.Attributs.RevenuParSeconde)
		labelRevenu.Text = `+{Ui.FormaterRevenu(if typeof(revenu) == "number" then revenu else 0)} $/s`
	end
	joueur:GetAttributeChangedSignal(Remotes.Attributs.ArgentNonCollecte):Connect(majCollecte)
	joueur:GetAttributeChangedSignal(Remotes.Attributs.RevenuParSeconde):Connect(majRevenu)
	majCollecte()
	majRevenu()

	-- Argent : leaderstats créées par le serveur après le chargement des données ; le compteur défile.
	task.spawn(function()
		local leaderstats = joueur:WaitForChild("leaderstats")
		local argent = leaderstats:WaitForChild("Argent") :: IntValue
		local affiche = Instance.new("NumberValue")
		affiche.Value = argent.Value
		local function majTexte()
			labelArgent.Text = Ui.FormaterNombre(affiche.Value)
		end
		affiche.Changed:Connect(majTexte)
		argent.Changed:Connect(function(valeur: number)
			TweenService:Create(affiche, TweenInfo.new(DUREE_COMPTEUR, Enum.EasingStyle.Quad), { Value = valeur })
				:Play()
		end)
		majTexte()
	end)
end

function Hud.Activer(id: string)
	activer(id)
end

-- Branche un bouton du menu ("teleport", "inventaire", "index", "boutique", "parametres").
function Hud.SurMenu(id: string, rappel: () -> ())
	rappels[id] = rappel
end

-- Pastille rouge sur un bouton du menu (nil ou "" pour l'enlever).
function Hud.Pastille(id: string, texte: string?)
	local bouton = boutons[id]
	if not bouton then
		return
	end
	local existante = pastilles[id]
	if not texte or texte == "" then
		if existante then
			(existante.Parent :: Instance):Destroy()
			pastilles[id] = nil
		end
		return
	end
	if existante then
		existante.Text = texte
	else
		local face = bouton:FindFirstChild("Face", true) :: Frame
		pastilles[id] = Ui.Pastille(face, texte)
	end
end

-- « +X $ » vert qui monte depuis le compteur et s'efface, puis toast « argent ».
function Hud.MontrerCollecte(montant: number)
	if typeof(montant) ~= "number" then
		return
	end
	local label = Ui.Texte({
		Name = "Gain",
		Position = UDim2.fromOffset(4, -4),
		Size = UDim2.fromScale(1, 1),
		TextSize = 28,
		TextColor3 = Ui.C.Gain,
		Text = `+{Ui.FormaterNombre(montant)} $`,
		Contour = true,
		ZIndex = 10,
		Parent = labelArgent,
	})
	local echelle = Ui.Creer("UIScale", { Scale = 0.8, Parent = label })
	Ui.Tween(echelle, 0.18, { Scale = 1.15 })
	task.delay(0.18, function()
		Ui.Tween(echelle, 1, { Scale = 1 })
	end)
	local stroke = label:FindFirstChildOfClass("UIStroke")
	local tween = Ui.Tween(label, 1.2, { Position = UDim2.fromOffset(4, -50), TextTransparency = 1 })
	if stroke then
		Ui.Tween(stroke, 1.2, { Transparency = 1 })
	end
	tween.Completed:Connect(function()
		label:Destroy()
	end)
	if notifier then
		notifier(`+{Ui.FormaterNombre(montant)} $ collectés`, "argent")
	end
end

return Hud
