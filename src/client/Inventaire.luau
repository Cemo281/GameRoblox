--!strict
-- Inventaire : bouton en bas à gauche et panneau listant les personnages du joueur.
-- Poser / Retirer passent par le serveur (Remotes "Poser" / "Retirer"), qui renvoie l'inventaire à jour.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economie = require(ReplicatedStorage.Shared.Economie)
local GachaConfig = require(ReplicatedStorage.Shared.GachaConfig)
local Personnages = require(ReplicatedStorage.Shared.Personnages)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Ui = require(script.Parent.Ui)

local Inventaire = {}

local TAILLE_CARTE = Vector2.new(140, 184)

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

	local carte = Ui.Creer("Frame", {
		Name = personnage.Uid,
		LayoutOrder = ordre,
		BackgroundColor3 = Ui.Couleurs.FondClair,
		Parent = grille,
	}, {
		Ui.Coins(12),
		Ui.Contour(couleur, if pose then 3 else 2),
	})

	Ui.Creer("Frame", {
		Name = "Bandeau",
		Size = UDim2.new(1, 0, 0, 26),
		BackgroundColor3 = couleur,
		Parent = carte,
	}, {
		Ui.Coins(12),
		Ui.Texte({
			Size = UDim2.fromScale(1, 1),
			TextSize = 16,
			TextXAlignment = Enum.TextXAlignment.Center,
			TextStrokeTransparency = 0.5,
			Text = if rarete then rarete.Nom else definition.Rarete,
		}),
	})

	local function ligne(texte: string, y: number, taille: number, couleurTexte: Color3, police: Enum.Font?)
		Ui.Texte({
			Position = UDim2.fromOffset(8, y),
			Size = UDim2.new(1, -16, 0, taille + 4),
			TextSize = taille,
			TextColor3 = couleurTexte,
			TextXAlignment = Enum.TextXAlignment.Center,
			TextTruncate = Enum.TextTruncate.AtEnd,
			Font = police or Ui.Police,
			Text = texte,
			Parent = carte,
		})
	end
	ligne(definition.Nom, 36, 20, Ui.Couleurs.Texte)
	ligne(Ui.Etoiles(personnage.Etoiles, Economie.EtoilesMax), 62, 18, Ui.Couleurs.Or)
	ligne(`+{Ui.FormaterRevenu(revenuDe(personnage, rebirths))} $/s`, 86, 16, Ui.Couleurs.Vert)
	ligne(
		if pose then `Emplacement {personnage.Emplacement}` else "Dans l'inventaire",
		108,
		14,
		Ui.Couleurs.TexteDiscret,
		Ui.PoliceTexte
	)

	local bouton = Ui.Bouton({
		Name = "Action",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -10),
		Size = UDim2.new(1, -20, 0, 34),
		BackgroundColor3 = if pose then Ui.Couleurs.BoutonSecondaire else Ui.Couleurs.Bouton,
		Text = if pose then "Retirer" else "Poser",
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
