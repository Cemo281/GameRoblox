--!strict
-- Index (maquette « Inventaire et Index » du handoff, au style v2) : collection par lot ouverte depuis la barre de gauche.
-- Bandeau « Collection du Lot N » avec barre de progression, onglets des lots, grille de cartes (chance de tirage,
-- meilleur score d'étoiles) ; un perso pas encore obtenu est en silhouette, nom « ??? ».
-- Obtenu = présent dans l'inventaire actuel (pas encore de mémoire des persos déjà obtenus dans la sauvegarde).
-- Lots : le lot N se débloque au rebirth N - 1 (GachaService : Lot <= Rebirths + 1).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GachaConfig = require(ReplicatedStorage.Shared.GachaConfig)
local Personnages = require(ReplicatedStorage.Shared.Personnages)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local UiConfig = require(ReplicatedStorage.Shared.UiConfig)
local Cartes = require(script.Parent.Cartes)
local Hud = require(script.Parent.Hud)
local Ui = require(script.Parent.Ui)

local Index = {}

local fenetre: Ui.Fenetre
local grille: ScrollingFrame
local verrou: Frame
local labelVerrou: TextLabel
local labelCondition: TextLabel
local labelCollection: TextLabel
local majBarre: (number, string) -> ()
local choisirOnglet: (number) -> ()
local lotChoisi = 1
local dernierLot = 1
local etat: Remotes.EtatInventaire? = nil

for _, personnage in Personnages.Liste do
	dernierLot = math.max(dernierLot, personnage.Lot)
end

local function rebirths(): number
	return if etat then etat.Rebirths else 0
end

-- Chance d'obtenir `id` : chance de sa rareté ÷ nombre de persos de cette rareté dans les lots débloqués
-- (même tirage que GachaService). Les raretés absentes des lots débloqués ne comptent pas.
local function chances(): { [string]: number }
	local lotMax = rebirths() + 1
	local parRarete: { [string]: number } = {}
	for _, personnage in Personnages.Liste do
		if personnage.Lot <= lotMax then
			parRarete[personnage.Rarete] = (parRarete[personnage.Rarete] or 0) + 1
		end
	end
	local total = 0
	for _, rarete in GachaConfig.Raretes do
		if parRarete[rarete.Id] then
			total += rarete.Chance
		end
	end
	local resultat: { [string]: number } = {}
	for _, personnage in Personnages.Liste do
		local rarete = GachaConfig.RaretesParId[personnage.Rarete]
		local nombre = parRarete[personnage.Rarete]
		if personnage.Lot <= lotMax and rarete and nombre and total > 0 then
			resultat[personnage.Id] = rarete.Chance / total * 100 / nombre
		end
	end
	return resultat
end

local function reconstruire()
	for _, enfant in grille:GetChildren() do
		if enfant:IsA("GuiObject") then
			enfant:Destroy()
		end
	end
	local meilleur: { [string]: number } = {}
	if etat then
		for _, personnage in etat.Personnages do
			meilleur[personnage.Id] = math.max(meilleur[personnage.Id] or 0, personnage.Etoiles)
		end
	end
	local debloque = lotChoisi <= rebirths() + 1
	local duLot = {}
	for _, personnage in Personnages.Liste do
		if personnage.Lot == lotChoisi then
			table.insert(duLot, personnage)
		end
	end
	local possedes = 0
	for _, personnage in duLot do
		if meilleur[personnage.Id] then
			possedes += 1
		end
	end
	labelCollection.Text = `Collection du Lot {lotChoisi}`
	majBarre(if #duLot > 0 then possedes / #duLot else 0, `{possedes} / {#duLot}`)

	grille.Visible = debloque and #duLot > 0
	verrou.Visible = not grille.Visible
	if not grille.Visible then
		labelVerrou.Text = `Lot {lotChoisi} verrouillé`
		labelCondition.Text = if #duLot > 0
			then `Débloqué au rebirth {lotChoisi - 1}`
			else "Prochain lot : contenu à définir"
		return
	end
	local chance = chances()
	for ordre, personnage in duLot do
		Cartes.Creer({
			Id = personnage.Id,
			Etoiles = meilleur[personnage.Id] or 0,
			Chance = chance[personnage.Id],
			Inconnu = meilleur[personnage.Id] == nil,
			TitreEtoiles = "MEILLEUR",
		}, { LayoutOrder = ordre, Parent = grille })
	end
end

function Index.Init()
	fenetre = Ui.Fenetre({
		Nom = "Index",
		Titre = "Index",
		Icone = "index",
		Ruban = UiConfig.CouleursFonctions.index,
		Taille = Vector2.new(1060, 570),
		Position = UDim2.new(0.5, 0, 0.5, 18),
	})
	local contenu = fenetre.Contenu

	-- Bandeau H 78 : titre de la collection et barre de progression
	local bandeau = Ui.Zone({
		Name = "Bandeau",
		Position = UDim2.fromOffset(18, 14),
		Size = UDim2.new(1, -36, 0, 78),
		Parent = contenu,
	})
	labelCollection = Ui.Texte({
		Position = UDim2.fromOffset(16, 12),
		Size = UDim2.fromOffset(360, 20),
		TextSize = 17,
		Parent = bandeau,
	})
	local barre
	barre, majBarre = Ui.Barre({ Position = UDim2.fromOffset(16, 38), Size = UDim2.fromOffset(360, 28) })
	barre.Parent = bandeau
	Ui.Texte({
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, -16, 0.5, 0),
		Size = UDim2.fromOffset(420, 40),
		FontFace = Ui.Montserrat(Enum.FontWeight.Medium),
		TextSize = 12,
		TextWrapped = true,
		TextColor3 = Ui.C.TexteDiscret,
		TextXAlignment = Enum.TextXAlignment.Right,
		Text = "Récompenses de collection : à définir",
		Parent = bandeau,
	})

	-- Onglets des lots (un de plus que le dernier lot connu : « à venir »)
	local noms = {}
	for lot = 1, dernierLot + 1 do
		table.insert(noms, `Lot {lot}`)
	end
	local onglets
	onglets, choisirOnglet = Ui.Onglets(noms, function(index)
		lotChoisi = index
		reconstruire()
	end, { Position = UDim2.fromOffset(18, 104) })
	onglets.Parent = contenu

	grille = Ui.Creer("ScrollingFrame", {
		Name = "Grille",
		Position = UDim2.fromOffset(18, 160),
		Size = UDim2.new(1, -36, 1, -176),
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 6,
		ScrollBarImageColor3 = Ui.C.Lisere,
		Parent = contenu,
	}, {
		Ui.Creer("UIGridLayout", {
			CellSize = UDim2.fromOffset(Cartes.Taille.X, Cartes.Taille.Y),
			CellPadding = UDim2.fromOffset(18, 14),
			HorizontalAlignment = Enum.HorizontalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder,
		}),
		Ui.Marges(4, 4, 10, 4),
	})

	-- Lot verrouillé
	verrou = Ui.Creer("Frame", {
		Name = "Verrou",
		Position = UDim2.fromOffset(18, 160),
		Size = UDim2.new(1, -36, 1, -176),
		BackgroundColor3 = Color3.fromHex("#1F1B36"),
		Visible = false,
		Parent = contenu,
	}, {
		Ui.Coins(16),
		Ui.Contour(Color3.fromHex("#605096"), 2),
		Ui.Liste(Enum.FillDirection.Vertical, 12, {
			HorizontalAlignment = Enum.HorizontalAlignment.Center,
			VerticalAlignment = Enum.VerticalAlignment.Center,
		}),
	})
	Ui.Icone("cadenas", 96, { LayoutOrder = 1, Parent = verrou })
	labelVerrou = Ui.Texte({
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 36),
		TextSize = 30,
		Contour = 2,
		Parent = verrou,
	})
	labelCondition = Ui.Texte({
		LayoutOrder = 3,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 34),
		BackgroundTransparency = 0,
		BackgroundColor3 = Ui.C.Trait,
		TextSize = 17,
		TextColor3 = Color3.fromHex("#FF8FC0"),
		Parent = verrou,
	})
	Ui.Rond().Parent = labelCondition
	Ui.Contour(Color3.fromHex("#FF5FA2"), 2).Parent = labelCondition
	Ui.Marges(0, 16).Parent = labelCondition

	fenetre.AuChangement(function(ouverte)
		if ouverte then
			Hud.Pastille("index", nil)
			reconstruire()
		end
	end)
	Hud.SurMenu("index", fenetre.Basculer)
end

function Index.MettreAJour(nouvelEtat: Remotes.EtatInventaire)
	-- pastille « ! » quand un perso jamais vu dans l'index arrive
	if etat then
		local avant: { [string]: boolean } = {}
		for _, personnage in etat.Personnages do
			avant[personnage.Id] = true
		end
		for _, personnage in nouvelEtat.Personnages do
			if not avant[personnage.Id] and not fenetre.EstOuverte() then
				Hud.Pastille("index", "!")
				break
			end
		end
	end
	etat = nouvelEtat
	if fenetre.EstOuverte() then
		reconstruire()
	end
end

function Index.Ouvrir(lot: number?)
	fenetre.Ouvrir()
	if lot then
		lotChoisi = lot
		choisirOnglet(lot)
		reconstruire()
	end
end

return Index
