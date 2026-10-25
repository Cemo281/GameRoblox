--!strict
-- Tirage : carte de résultat au centre de l'écran. Suspense (les personnages défilent) puis révélation.
-- Le résultat est décidé par le serveur avant l'animation, qui tient dans GachaConfig.DureeAnimation.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Economie = require(ReplicatedStorage.Shared.Economie)
local GachaConfig = require(ReplicatedStorage.Shared.GachaConfig)
local Personnages = require(ReplicatedStorage.Shared.Personnages)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Ui = require(script.Parent.Ui)

local Tirage = {}

local DUREE_SUSPENSE = math.min(1.3, GachaConfig.DureeAnimation * 0.45)
local DUREE_AFFICHAGE = 2.5
local EPAISSEUR_CONTOUR = 4
local RARETES_SPECIALES: { [string]: boolean } = { Mythique = true, Secret = true }

local conteneur: Frame
local echellePop: UIScale
local contour: UIStroke
local portrait: Frame
local labelRarete: TextLabel
local labelInitiale: TextLabel
local labelNom: TextLabel
local labelEtoiles: TextLabel
local labelRevenu: TextLabel
local labelDestination: TextLabel
local pulsation: Tween? = nil
local generation = 0 -- un nouveau tirage interrompt l'animation en cours

local function afficherPersonnage(personnage: Personnages.Personnage)
	local rarete = GachaConfig.RaretesParId[personnage.Rarete]
	local couleur = if rarete then rarete.Couleur else Ui.Couleurs.Texte
	contour.Color = couleur
	portrait.BackgroundColor3 = couleur
	labelRarete.TextColor3 = couleur
	labelRarete.Text = if rarete then rarete.Nom else personnage.Rarete
	labelInitiale.Text = string.sub(personnage.Nom, 1, 1)
	labelNom.Text = personnage.Nom
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
		Size = UDim2.fromOffset(300, 400),
		BackgroundTransparency = 1,
		Visible = false,
		ZIndex = 10,
		Parent = ecran,
	})
	Ui.Adapter(conteneur)

	contour = Ui.Contour(Ui.Couleurs.Contour, EPAISSEUR_CONTOUR)
	echellePop = Ui.Creer("UIScale", {})
	local carte = Ui.Creer("Frame", {
		Name = "Carte",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Ui.Couleurs.Fond,
		Parent = conteneur,
	}, {
		Ui.Coins(18),
		contour,
		echellePop,
		Ui.Marges(16),
		Ui.Creer("UIListLayout", {
			Padding = UDim.new(0, 8),
			HorizontalAlignment = Enum.HorizontalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder,
		}),
	})

	labelRarete = texteCentre("Rarete", 1, 28, 24, Ui.Couleurs.Texte)
	labelRarete.Parent = carte

	-- Emplacement du futur visuel du personnage (initiale en attendant les modèles 3D)
	portrait = Ui.Creer("Frame", {
		Name = "Portrait",
		LayoutOrder = 2,
		Size = UDim2.fromOffset(180, 180),
		Parent = carte,
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
	labelNom.Parent = carte
	labelEtoiles = texteCentre("Etoiles", 4, 28, 26, Ui.Couleurs.Or)
	labelEtoiles.Parent = carte
	labelRevenu = texteCentre("Revenu", 5, 22, 20, Ui.Couleurs.Vert)
	labelRevenu.Parent = carte
	labelDestination = texteCentre("Destination", 6, 20, 16, Ui.Couleurs.TexteDiscret)
	labelDestination.Font = Ui.PoliceTexte
	labelDestination.Parent = carte
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
	contour.Thickness = EPAISSEUR_CONTOUR
	labelEtoiles.Text = "?"
	labelRevenu.Text = ""
	labelDestination.Text = ""
	conteneur.Visible = true
	pop(0.5, 0.25)

	local fin = os.clock() + DUREE_SUSPENSE
	local pause = 0.05
	while os.clock() < fin do
		afficherPersonnage(candidats[math.random(#candidats)])
		task.wait(pause)
		if tirage ~= generation then
			return
		end
		pause *= 1.18
	end

	-- Révélation
	afficherPersonnage(definition)
	labelEtoiles.Text = Ui.Etoiles(resultat.Etoiles, Economie.EtoilesMax)
	labelRevenu.Text = `+{Ui.FormaterRevenu(resultat.Revenu)} $/s`
	labelDestination.Text = if resultat.Emplacement
		then `→ Emplacement {resultat.Emplacement}`
		else "→ Inventaire (emplacements pleins)"
	pop(1.25, 0.35)
	if RARETES_SPECIALES[definition.Rarete] then
		local infos = TweenInfo.new(0.35, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, 3, true)
		local tween = TweenService:Create(contour, infos, { Thickness = EPAISSEUR_CONTOUR * 3 })
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
