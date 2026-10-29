--!strict
-- Tirage : carte de résultat au centre de l'écran. Suspense (les personnages défilent) puis révélation.
-- Le résultat est décidé par le serveur avant l'animation, qui tient dans GachaConfig.DureeAnimation.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Economie = require(ReplicatedStorage.Shared.Economie)
local GachaConfig = require(ReplicatedStorage.Shared.GachaConfig)
local ImagesPersonnages = require(ReplicatedStorage.Shared.ImagesPersonnages)
local Personnages = require(ReplicatedStorage.Shared.Personnages)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Images = require(script.Parent.Images)
local Ui = require(script.Parent.Ui)

local Tirage = {}

local DUREE_SUSPENSE = math.min(1.3, GachaConfig.DureeAnimation * 0.45)
local DUREE_AFFICHAGE = 2.5
local EPAISSEUR_PULSATION = 10
local LARGEUR_CARTE = 300
local RAYON_CARTE = math.round(26 * LARGEUR_CARTE / ImagesPersonnages.TailleCadre.X) -- coins du cadre
local RARETES_SPECIALES: { [string]: boolean } = { Mythique = true, Secret = true }

local conteneur: Frame
local echellePop: UIScale
local contour: UIStroke
local cadre: ImageLabel
local carte: Frame
local portrait: Frame
local visuel: ImageLabel
local labelRarete: TextLabel
local labelInitiale: TextLabel
local labelNom: TextLabel
local labelEtoiles: TextLabel
local labelRevenu: TextLabel
local labelDestination: TextLabel
local reflet: CanvasGroup? = nil
local pulsation: Tween? = nil
local generation = 0 -- un nouveau tirage interrompt l'animation en cours

-- Pendant le suspense : silhouette du perso ; à la révélation : sa grille Idle animée.
-- Sans images : bloc coloré avec l'initiale.
local function afficherPersonnage(personnage: Personnages.Personnage, revele: boolean)
	local rarete = GachaConfig.RaretesParId[personnage.Rarete]
	local couleur = if rarete then rarete.Couleur else Ui.Couleurs.Texte
	contour.Color = couleur
	cadre.Image = ImagesPersonnages.Cadres[personnage.Rarete] or ""
	labelRarete.TextColor3 = couleur
	labelRarete.Text = if rarete then rarete.Nom else personnage.Rarete
	labelNom.Text = personnage.Nom

	local images = Images.De(personnage.Id)
	portrait.Visible = images == nil
	visuel.Visible = images ~= nil
	if images and revele then
		Images.Animer(visuel, personnage.Id)
	elseif images then
		Images.Arreter(visuel)
		visuel.Image = images.Silhouette
	else
		portrait.BackgroundColor3 = couleur
		labelInitiale.Text = string.sub(personnage.Nom, 1, 1)
	end
end

local function texteCentre(nom: string, ordre: number, hauteur: number, taille: number, couleur: Color3): TextLabel
	return Ui.Texte({
		Name = nom,
		LayoutOrder = ordre,
		Size = UDim2.new(1, 0, 0, hauteur),
		TextSize = taille,
		TextColor3 = couleur,
		TextXAlignment = Enum.TextXAlignment.Center,
	})
end

function Tirage.Init(ecran: ScreenGui)
	conteneur = Ui.Creer("Frame", {
		Name = "Tirage",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.45),
		-- proportions du cadre de carte (280 × 368)
		Size = UDim2.fromOffset(
			LARGEUR_CARTE,
			math.round(LARGEUR_CARTE * ImagesPersonnages.TailleCadre.Y / ImagesPersonnages.TailleCadre.X)
		),
		BackgroundTransparency = 1,
		Visible = false,
		ZIndex = 10,
		Parent = ecran,
	})
	Ui.Adapter(conteneur)

	-- Carte : cadre de la rareté, contenu par-dessus, reflet Secret encore au-dessus (ajouté à la révélation)
	contour = Ui.Contour(Ui.Couleurs.Contour, 0)
	echellePop = Ui.Creer("UIScale", {})
	carte = Ui.Creer("Frame", {
		Name = "Carte",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Ui.Couleurs.Fond,
		BackgroundTransparency = 1,
		Parent = conteneur,
	}, {
		Ui.Coins(RAYON_CARTE),
		contour,
		echellePop,
	})
	cadre = Ui.Creer("ImageLabel", {
		Name = "Cadre",
		Size = UDim2.fromScale(1, 1),
		BackgroundTransparency = 1,
		ZIndex = 1,
		Parent = carte,
	})
	local contenu = Ui.Creer("Frame", {
		Name = "Contenu",
		Size = UDim2.fromScale(1, 1),
		BackgroundTransparency = 1,
		ZIndex = 2,
		Parent = carte,
	}, {
		Ui.Marges(18),
		Ui.Creer("UIListLayout", {
			Padding = UDim.new(0, 4),
			HorizontalAlignment = Enum.HorizontalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder,
		}),
	})

	labelRarete = texteCentre("Rarete", 1, 28, 24, Ui.Couleurs.Texte)
	labelRarete.TextStrokeTransparency = 0.4
	labelRarete.Parent = contenu

	-- Visuel : silhouette puis grille Idle animée (assets/gui/<Id>) ; bloc coloré + initiale si le perso n'a pas d'images
	local zoneVisuel = Ui.Creer("Frame", {
		Name = "ZoneVisuel",
		LayoutOrder = 2,
		Size = UDim2.fromOffset(200, 200),
		BackgroundTransparency = 1,
		Parent = contenu,
	})
	visuel = Ui.Creer("ImageLabel", {
		Name = "Visuel",
		Size = UDim2.fromScale(1, 1),
		BackgroundTransparency = 1,
		Parent = zoneVisuel,
	})
	portrait = Ui.Creer("Frame", {
		Name = "Portrait",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(170, 170),
		Parent = zoneVisuel,
	}, {
		Ui.Coins(16),
		Ui.Creer("UIGradient", {
			Rotation = 90,
			Transparency = NumberSequence.new(0, 0.35),
		}),
	})
	labelInitiale = Ui.Texte({
		Name = "Initiale",
		Size = UDim2.fromScale(1, 1),
		TextSize = 110,
		TextXAlignment = Enum.TextXAlignment.Center,
		TextStrokeTransparency = 0.6,
		Parent = portrait,
	})

	labelNom = texteCentre("Nom", 3, 34, 30, Ui.Couleurs.Texte)
	labelNom.TextStrokeTransparency = 0.4
	labelNom.Parent = contenu
	labelEtoiles = texteCentre("Etoiles", 4, 28, 26, Ui.Couleurs.Or)
	labelEtoiles.TextStrokeTransparency = 0.5
	labelEtoiles.Parent = contenu
	labelRevenu = texteCentre("Revenu", 5, 22, 20, Ui.Couleurs.Vert)
	labelRevenu.TextStrokeTransparency = 0.5
	labelRevenu.Parent = contenu
	labelDestination = texteCentre("Destination", 6, 20, 16, Ui.Couleurs.Texte)
	labelDestination.Font = Ui.PoliceTexte
	labelDestination.TextStrokeTransparency = 0.5
	labelDestination.Parent = contenu
end

local function pop(depart: number, duree: number)
	echellePop.Scale = depart
	TweenService:Create(echellePop, TweenInfo.new(duree, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
		Scale = 1,
	}):Play()
end

function Tirage.Montrer(resultat: Remotes.ResultatTirage)
	local definition = Personnages.ParId[resultat.Id]
	if not definition then
		return
	end
	generation += 1
	local tirage = generation

	-- Suspense : défilement de plus en plus lent parmi les personnages du même lot ou d'avant
	local candidats = {}
	for _, personnage in Personnages.Liste do
		if personnage.Lot <= definition.Lot then
			table.insert(candidats, personnage)
		end
	end
	if pulsation then
		pulsation:Cancel()
	end
	if reflet then
		reflet:Destroy()
		reflet = nil
	end
	contour.Thickness = 0
	labelEtoiles.Text = "?"
	labelRevenu.Text = ""
	labelDestination.Text = ""
	conteneur.Visible = true
	pop(0.5, 0.25)

	local fin = os.clock() + DUREE_SUSPENSE
	local pause = 0.05
	while os.clock() < fin do
		afficherPersonnage(candidats[math.random(#candidats)], false)
		task.wait(pause)
		if tirage ~= generation then
			return
		end
		pause *= 1.18
	end

	-- Révélation
	afficherPersonnage(definition, true)
	if definition.Rarete == "Secret" then
		reflet = Images.Reflet(carte, RAYON_CARTE, 3)
	end
	labelEtoiles.Text = Ui.Etoiles(resultat.Etoiles, Economie.EtoilesMax)
	labelRevenu.Text = `+{Ui.FormaterRevenu(resultat.Revenu)} $/s`
	labelDestination.Text = if resultat.Emplacement
		then `→ Emplacement {resultat.Emplacement}`
		else "→ Inventaire (emplacements pleins)"
	pop(1.25, 0.35)
	if RARETES_SPECIALES[definition.Rarete] then
		local infos = TweenInfo.new(0.35, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, 3, true)
		local tween = TweenService:Create(contour, infos, { Thickness = EPAISSEUR_PULSATION })
		pulsation = tween
		tween:Play()
	end

	task.wait(DUREE_AFFICHAGE)
	if tirage ~= generation then
		return
	end
	local fermeture =
		TweenService:Create(echellePop, TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
			Scale = 0,
		})
	fermeture.Completed:Connect(function()
		if tirage == generation then
			conteneur.Visible = false
		end
	end)
	fermeture:Play()
end

return Tirage
