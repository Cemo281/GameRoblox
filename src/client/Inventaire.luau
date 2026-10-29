--!strict
-- Inventaire : bouton en bas à gauche et panneau listant les personnages du joueur.
-- Poser / Retirer passent par le serveur (Remotes "Poser" / "Retirer"), qui renvoie l'inventaire à jour.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economie = require(ReplicatedStorage.Shared.Economie)
local GachaConfig = require(ReplicatedStorage.Shared.GachaConfig)
local ImagesPersonnages = require(ReplicatedStorage.Shared.ImagesPersonnages)
local Personnages = require(ReplicatedStorage.Shared.Personnages)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Images = require(script.Parent.Images)
local Ui = require(script.Parent.Ui)

local Inventaire = {}

local TAILLE_CARTE = Vector2.new(140, 184)
local BORD = ImagesPersonnages.BordCadre * TAILLE_CARTE.X / ImagesPersonnages.TailleCadre.X
local RAYON_CARTE = 13 -- coins du cadre (26 px à 280 de large)
local TAILLE_PORTRAIT = Vector2.new(TAILLE_CARTE.X - 2 * BORD, 94)

local panneau: Frame
local grille: ScrollingFrame
local labelResume: TextLabel
local boutonOuvrir: TextButton
local etat: Remotes.EtatInventaire? = nil
local actionEnCours = false

local rangRarete: { [string]: number } = {}
for rang, rarete in GachaConfig.Raretes do
	rangRarete[rarete.Id] = rang
end

local function revenuDe(personnage: Remotes.PersonnageInventaire, rebirths: number): number
	local definition = Personnages.ParId[personnage.Id]
	return if definition then Economie.RevenuParSeconde(definition.Revenu, personnage.Etoiles, rebirths) else 0
end

-- Posés d'abord (par emplacement), puis rareté décroissante, puis revenu décroissant.
local function trier(liste: { Remotes.PersonnageInventaire }, rebirths: number)
	table.sort(liste, function(a, b)
		if (a.Emplacement ~= nil) ~= (b.Emplacement ~= nil) then
			return a.Emplacement ~= nil
		end
		if a.Emplacement and b.Emplacement then
			return a.Emplacement < b.Emplacement
		end
		local definitionA, definitionB = Personnages.ParId[a.Id], Personnages.ParId[b.Id]
		local rangA = if definitionA then rangRarete[definitionA.Rarete] or 0 else 0
		local rangB = if definitionB then rangRarete[definitionB.Rarete] or 0 else 0
		if rangA ~= rangB then
			return rangA > rangB
		end
		local revenuA, revenuB = revenuDe(a, rebirths), revenuDe(b, rebirths)
		if revenuA ~= revenuB then
			return revenuA > revenuB
		end
		return a.Uid < b.Uid
	end)
end

local function demander(nom: Remotes.NomFonction, uid: string, bouton: TextButton)
	if actionEnCours then
		return
	end
	actionEnCours = true
	local texte = bouton.Text
	bouton.Text = "…"
	task.spawn(function()
		local ok, reussi = pcall(function()
			return Remotes.Fonction(nom):InvokeServer(uid)
		end)
		actionEnCours = false
		-- En cas de succès, le serveur renvoie l'inventaire et la carte est reconstruite
		if not (ok and reussi == true) and bouton.Parent then
			bouton.Text = texte
		end
	end)
end

local function creerCarte(personnage: Remotes.PersonnageInventaire, rebirths: number, ordre: number)
	local definition = Personnages.ParId[personnage.Id]
	if not definition then
		return
	end
	local rarete = GachaConfig.RaretesParId[definition.Rarete]
	local couleur = if rarete then rarete.Couleur else Ui.Couleurs.Texte
	local pose = personnage.Emplacement ~= nil

	-- Cadre de la rareté (assets/gui/cadres, dessiné au double de cette carte), portrait en haut, textes dessous
	local cadre = Images.Cadre(definition.Rarete)
	local carte = Ui.Creer("Frame", {
		Name = personnage.Uid,
		LayoutOrder = ordre,
		BackgroundColor3 = Ui.Couleurs.FondClair,
		BackgroundTransparency = if cadre then 1 else 0,
		Parent = grille,
	}, { Ui.Coins(RAYON_CARTE) })
	if cadre then
		cadre.Parent = carte
	else
		Ui.Contour(couleur, 2).Parent = carte
	end

	local images = Images.De(personnage.Id)
	if images then
		Ui.Creer("ImageLabel", {
			Name = "Portrait",
			Position = UDim2.fromOffset(BORD, BORD),
			Size = UDim2.fromOffset(TAILLE_PORTRAIT.X, TAILLE_PORTRAIT.Y),
			BackgroundTransparency = 1,
			Image = images.Portrait,
			-- buste rogné au format de la zone (le portrait est carré)
			ImageRectSize = Vector2.new(512, 512 * TAILLE_PORTRAIT.Y / TAILLE_PORTRAIT.X),
			ZIndex = 2,
			Parent = carte,
		})
	else
		Ui.Creer("Frame", {
			Name = "Portrait",
			Position = UDim2.fromOffset(BORD + 18, BORD + 14),
			Size = UDim2.fromOffset(TAILLE_PORTRAIT.X - 36, TAILLE_PORTRAIT.Y - 20),
			BackgroundColor3 = couleur,
			ZIndex = 2,
			Parent = carte,
		}, {
			Ui.Coins(12),
			Ui.Texte({
				Size = UDim2.fromScale(1, 1),
				TextSize = 52,
				TextXAlignment = Enum.TextXAlignment.Center,
				TextStrokeTransparency = 0.6,
				Text = string.sub(definition.Nom, 1, 1),
			}),
		})
	end
	if definition.Rarete == "Secret" then
		Images.Reflet(carte, RAYON_CARTE, 3)
	end

	local function ligne(texte: string, y: number, taille: number, couleurTexte: Color3)
		Ui.Texte({
			Position = UDim2.fromOffset(BORD, y),
			Size = UDim2.new(1, -2 * BORD, 0, taille + 4),
			TextSize = taille,
			TextColor3 = couleurTexte,
			TextXAlignment = Enum.TextXAlignment.Center,
			TextTruncate = Enum.TextTruncate.AtEnd,
			TextStrokeTransparency = 0.4,
			Text = texte,
			ZIndex = 4,
			Parent = carte,
		})
	end
	ligne(if rarete then rarete.Nom else definition.Rarete, BORD + 1, 13, couleur)
	ligne(definition.Nom, 102, 18, Ui.Couleurs.Texte)
	ligne(Ui.Etoiles(personnage.Etoiles, Economie.EtoilesMax), 122, 14, Ui.Couleurs.Or)
	ligne(`+{Ui.FormaterRevenu(revenuDe(personnage, rebirths))} $/s`, 137, 13, Ui.Couleurs.Vert)

	if pose then
		Ui.Creer("Frame", {
			Name = "Pose",
			AnchorPoint = Vector2.new(1, 0),
			Position = UDim2.new(1, -BORD + 2, 0, BORD - 2),
			Size = UDim2.fromOffset(30, 20),
			BackgroundColor3 = Ui.Couleurs.Or,
			ZIndex = 4,
			Parent = carte,
		}, {
			Ui.Coins(8),
			Ui.Texte({
				Size = UDim2.fromScale(1, 1),
				TextSize = 14,
				TextColor3 = Ui.Couleurs.Fond,
				TextXAlignment = Enum.TextXAlignment.Center,
				Text = `#{personnage.Emplacement}`,
				ZIndex = 4,
			}),
		})
	end

	local bouton = Ui.Bouton({
		Name = "Action",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -BORD + 4),
		Size = UDim2.new(1, -2 * BORD, 0, 24),
		TextSize = 16,
		BackgroundColor3 = if pose then Ui.Couleurs.BoutonSecondaire else Ui.Couleurs.Bouton,
		Text = if pose then "Retirer" else "Poser",
		ZIndex = 4,
		Parent = carte,
	})
	bouton.Activated:Connect(function()
		demander(if pose then "Retirer" else "Poser", personnage.Uid, bouton)
	end)
end

local function reconstruire()
	if not etat then
		return
	end
	local etatActuel = etat
	local poses = 0
	for _, personnage in etatActuel.Personnages do
		if personnage.Emplacement then
			poses += 1
		end
	end
	local total = #etatActuel.Personnages
	boutonOuvrir.Text = `🎒 Inventaire  {total}/{etatActuel.Max}`
	labelResume.Text = `Posés {poses}/{etatActuel.EmplacementsDebloques}  ·  {total}/{etatActuel.Max} personnages`

	if not panneau.Visible then
		return -- reconstruit à l'ouverture
	end
	for _, enfant in grille:GetChildren() do
		if enfant:IsA("Frame") then
			enfant:Destroy()
		end
	end
	local liste = table.clone(etatActuel.Personnages)
	trier(liste, etatActuel.Rebirths)
	for ordre, personnage in liste do
		creerCarte(personnage, etatActuel.Rebirths, ordre)
	end
end

local function basculer(visible: boolean)
	panneau.Visible = visible
	reconstruire()
end

function Inventaire.Init(ecran: ScreenGui)
	boutonOuvrir = Ui.Bouton({
		Name = "BoutonInventaire",
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.new(0, 16, 1, -16),
		Size = UDim2.fromOffset(220, 50),
		TextSize = 22,
		Text = "🎒 Inventaire",
		Parent = ecran,
	})
	Ui.Contour(Ui.Couleurs.Contour).Parent = boutonOuvrir
	Ui.Adapter(boutonOuvrir)

	panneau = Ui.Creer("Frame", {
		Name = "Inventaire",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(800, 500), -- 5 cartes par ligne
		BackgroundColor3 = Ui.Couleurs.Fond,
		Visible = false,
		ZIndex = 5,
		Parent = ecran,
	}, {
		Ui.Coins(18),
		Ui.Contour(Ui.Couleurs.Contour, 3),
		Ui.Marges(16),
	})
	Ui.Adapter(panneau)

	Ui.Texte({
		Name = "Titre",
		Size = UDim2.new(1, -60, 0, 34),
		TextSize = 30,
		Text = "Inventaire",
		Parent = panneau,
	})
	labelResume = Ui.Texte({
		Name = "Resume",
		Position = UDim2.fromOffset(0, 36),
		Size = UDim2.new(1, -60, 0, 20),
		TextSize = 16,
		Font = Ui.PoliceTexte,
		TextColor3 = Ui.Couleurs.TexteDiscret,
		Text = "",
		Parent = panneau,
	})
	local fermer = Ui.Bouton({
		Name = "Fermer",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.fromScale(1, 0),
		Size = UDim2.fromOffset(44, 44),
		BackgroundColor3 = Ui.Couleurs.BoutonSecondaire,
		TextSize = 22,
		Text = "X", -- la police FredokaOne n'a pas le caractère ✕
		Parent = panneau,
	})
	fermer.Activated:Connect(function()
		basculer(false)
	end)

	grille = Ui.Creer("ScrollingFrame", {
		Name = "Grille",
		Position = UDim2.fromOffset(0, 68),
		Size = UDim2.new(1, 0, 1, -68),
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 6,
		ScrollBarImageColor3 = Ui.Couleurs.Contour,
		Parent = panneau,
	}, {
		Ui.Creer("UIGridLayout", {
			CellSize = UDim2.fromOffset(TAILLE_CARTE.X, TAILLE_CARTE.Y),
			CellPadding = UDim2.fromOffset(10, 10),
			SortOrder = Enum.SortOrder.LayoutOrder,
		}),
		Ui.Creer(
			"UIPadding",
			{ PaddingTop = UDim.new(0, 4), PaddingLeft = UDim.new(0, 4), PaddingRight = UDim.new(0, 10) }
		),
	})

	boutonOuvrir.Activated:Connect(function()
		basculer(not panneau.Visible)
	end)
end

function Inventaire.MettreAJour(nouvelEtat: Remotes.EtatInventaire)
	etat = nouvelEtat
	reconstruire()
end

return Inventaire
