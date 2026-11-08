--!strict
-- Inventaire (maquette « Inventaire et Index » du handoff, au style v2) : fenêtre ouverte depuis la barre de gauche.
-- Filtres par rareté, tri (rareté, étoiles, revenu), grille de cartes, panneau de détail avec le modèle 3D animé,
-- Poser / Retirer (Remotes "Poser" / "Retirer", le serveur renvoie l'inventaire à jour).
-- Recherche par nom (saisie locale, jamais envoyée au serveur ni montrée aux autres joueurs).
-- Recycler : règles à définir dans le wiki (bouton désactivé).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Economie = require(ReplicatedStorage.Shared.Economie)
local GachaConfig = require(ReplicatedStorage.Shared.GachaConfig)
local Personnages = require(ReplicatedStorage.Shared.Personnages)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local UiConfig = require(ReplicatedStorage.Shared.UiConfig)
local Cartes = require(script.Parent.Cartes)
local Hud = require(script.Parent.Hud)
local Ui = require(script.Parent.Ui)
local Vue3D = require(script.Parent.Vue3D)

local Inventaire = {}

local LARGEUR_GRILLE = 772
local SEUIL_ROUGE = 0.95 -- le compteur passe en rouge à 95 % du maximum
local TRIS = { "Rareté", "Étoiles", "Revenu" }

local fenetre: Ui.Fenetre
local grille: ScrollingFrame
local labelCompteur: TextLabel
local labelResume: TextLabel
local labelVide: TextLabel
local detail: Frame
local vue: Vue3D.Vue
local fondVue: Frame
local blocVue: Frame
local labelNom: TextLabel
local badgeRarete: TextLabel
local fondBadge: Frame
local cadreEtoiles: Frame
local labelRevenu: TextLabel
local labelCalcul: TextLabel
local labelEtat: TextLabel
local boutonAction: TextButton
local boutonsFiltres: { [string]: TextButton } = {}

local etat: Remotes.EtatInventaire? = nil
local filtre = "Tous"
local tri = 1
local recherche = "" -- en minuscules
local LONGUEUR_RECHERCHE = 30
local selection: string? = nil
local actionEnCours = false
local vus: { [string]: boolean }? = nil -- uids déjà vus (pastille « nouveaux » du menu)
local idAffiche3D: string? = nil

local rangRarete: { [string]: number } = {}
for rang, rarete in GachaConfig.Raretes do
	rangRarete[rarete.Id] = rang
end

local function revenuDe(personnage: Remotes.PersonnageInventaire, rebirths: number): number
	local definition = Personnages.ParId[personnage.Id]
	return if definition then Economie.RevenuParSeconde(definition.Revenu, personnage.Etoiles, rebirths) else 0
end

local function rangDe(personnage: Remotes.PersonnageInventaire): number
	local definition = Personnages.ParId[personnage.Id]
	return if definition then rangRarete[definition.Rarete] or 0 else 0
end

-- Posés d'abord (par emplacement), puis selon le tri choisi.
local function trier(liste: { Remotes.PersonnageInventaire }, rebirths: number)
	table.sort(liste, function(a, b)
		if (a.Emplacement ~= nil) ~= (b.Emplacement ~= nil) then
			return a.Emplacement ~= nil
		end
		local revenuA, revenuB = revenuDe(a, rebirths), revenuDe(b, rebirths)
		if tri == 1 and rangDe(a) ~= rangDe(b) then
			return rangDe(a) > rangDe(b)
		elseif tri == 2 and a.Etoiles ~= b.Etoiles then
			return a.Etoiles > b.Etoiles
		end
		if revenuA ~= revenuB then
			return revenuA > revenuB
		end
		return a.Uid < b.Uid
	end)
end

local function trouver(uid: string?): Remotes.PersonnageInventaire?
	if not etat or not uid then
		return nil
	end
	for _, personnage in etat.Personnages do
		if personnage.Uid == uid then
			return personnage
		end
	end
	return nil
end

local function demander(nom: Remotes.NomFonction, uid: string)
	if actionEnCours then
		return
	end
	actionEnCours = true
	Ui.ChangerTexte(boutonAction, "…")
	task.spawn(function()
		local ok, reussi = pcall(function()
			return Remotes.Fonction(nom):InvokeServer(uid)
		end)
		actionEnCours = false
		-- en cas de succès, le serveur renvoie l'inventaire et le détail est redessiné
		if not (ok and reussi == true) then
			Inventaire.Rafraichir()
		end
	end)
end

local function majDetail()
	local personnage = trouver(selection)
	detail.Visible = personnage ~= nil
	if not personnage or not etat then
		return
	end
	local definition = Personnages.ParId[personnage.Id]
	if not definition then
		return
	end
	local t = Ui.Rarete(definition.Rarete)
	local rarete = GachaConfig.RaretesParId[definition.Rarete]

	-- Vue 3D : fond au dégradé de la rareté, modèle animé ou bloc coloré
	local gradient = fondVue:FindFirstChildOfClass("UIGradient")
	if gradient then
		gradient:Destroy()
	end
	Ui.Degrade(t, 90).Parent = fondVue
	if idAffiche3D ~= personnage.Id then
		idAffiche3D = personnage.Id
		local modele = Vue3D.Montrer(vue, personnage.Id)
		blocVue.Visible = modele == nil
		blocVue.BackgroundColor3 = t.Base
		local initiale = blocVue:FindFirstChild("Initiale") :: TextLabel
		initiale.Text = string.sub(definition.Nom, 1, 1)
	end

	labelNom.Text = definition.Nom
	badgeRarete.Text = if rarete then rarete.Nom else definition.Rarete
	badgeRarete.TextColor3 = Ui.TexteBadge[definition.Rarete] or Ui.C.Texte
	local degradeBadge = fondBadge:FindFirstChildOfClass("UIGradient")
	if degradeBadge then
		degradeBadge:Destroy()
	end
	Ui.Degrade2(t.Clair, t.Base).Parent = fondBadge
	cadreEtoiles:ClearAllChildren()
	Ui.EtoilesIcones(personnage.Etoiles, Economie.EtoilesMax, 18).Parent = cadreEtoiles

	labelRevenu.Text = `{Ui.FormaterRevenu(revenuDe(personnage, etat.Rebirths))} $/s`
	local pluriel = if personnage.Etoiles > 1 then "s" else ""
	local calcul =
		`base {definition.Revenu} $/s × (1 + {Ui.FormaterRevenu(Economie.BonusParEtoile)} × {personnage.Etoiles} étoile{pluriel})`
	if etat.Rebirths > 0 then
		calcul ..= ` × (1 + {Ui.FormaterRevenu(Economie.BonusParRebirth)} × {etat.Rebirths} rebirth{if etat.Rebirths
				> 1
			then "s"
			else ""})`
	end
	labelCalcul.Text = calcul
	local pose = personnage.Emplacement ~= nil
	labelEtat.Text = if pose then `Posé · emplacement {personnage.Emplacement}` else "Dans l'inventaire"
	labelEtat.TextColor3 = if pose then Ui.C.Gain else Ui.C.TexteDiscret
	Ui.ChangerStyle(boutonAction, if pose then "Secondaire" else "Principal")
	Ui.ChangerTexte(boutonAction, if pose then "Retirer" else "Poser")
end

local function reconstruireGrille()
	if not etat then
		return
	end
	for _, enfant in grille:GetChildren() do
		if enfant:IsA("GuiObject") then
			enfant:Destroy()
		end
	end
	local liste = {}
	local poses = 0
	for _, personnage in etat.Personnages do
		if personnage.Emplacement then
			poses += 1
		end
		local definition = Personnages.ParId[personnage.Id]
		local correspond = recherche == "" or string.find(string.lower(definition and definition.Nom or ""), recherche, 1, true) ~= nil
		if definition and correspond and (filtre == "Tous" or definition.Rarete == filtre) then
			table.insert(liste, personnage)
		end
	end
	trier(liste, etat.Rebirths)
	labelResume.Text = `{#liste} affichés · posés {poses} / {etat.EmplacementsDebloques} emplacements`
	labelVide.Visible = #liste == 0

	-- la sélection suit les filtres : premier perso affiché si elle n'en fait plus partie
	local visible = false
	for _, personnage in liste do
		if personnage.Uid == selection then
			visible = true
		end
	end
	if not visible then
		selection = if liste[1] then liste[1].Uid else nil
	end
	for ordre, personnage in liste do
		local choisi = personnage.Uid == selection
		local cellule = Ui.Creer("TextButton", {
			Name = personnage.Uid,
			LayoutOrder = ordre,
			BackgroundTransparency = 1,
			AutoButtonColor = false,
			Text = "",
			Parent = grille,
		})
		local contenu = Ui.Creer("Frame", {
			Name = "Contenu",
			Position = UDim2.fromOffset(0, if choisi then 2 else 6),
			Size = UDim2.fromOffset(Cartes.Taille.X, Cartes.Taille.Y),
			BackgroundTransparency = 1,
			Parent = cellule,
		})
		if choisi then
			Ui.Creer("Frame", {
				Name = "Selection",
				Position = UDim2.fromOffset(-4, -4),
				Size = UDim2.new(1, 8, 1, 8),
				BackgroundColor3 = Color3.new(1, 1, 1),
				Parent = contenu,
			}, { Ui.Coins(16) })
		end
		Cartes.Creer({
			Id = personnage.Id,
			Etoiles = personnage.Etoiles,
			Revenu = revenuDe(personnage, etat.Rebirths),
			Pose = personnage.Emplacement ~= nil,
		}, { Parent = contenu })
		Ui.Reagir(cellule, nil, nil, 1.04)
		cellule.Activated:Connect(function()
			selection = personnage.Uid
			reconstruireGrille()
		end)
	end
	majDetail()
end

function Inventaire.Rafraichir()
	if not etat then
		return
	end
	local total = #etat.Personnages
	labelCompteur.Text = `{total} / {etat.Max}`
	labelCompteur.TextColor3 = if total >= etat.Max * SEUIL_ROUGE then Ui.Teintes.Danger.Clair else Ui.C.Texte
	if fenetre.EstOuverte() then
		reconstruireGrille()
	end
end

local function majPastille()
	if not etat or not vus then
		return
	end
	local nouveaux = 0
	for _, personnage in etat.Personnages do
		if not vus[personnage.Uid] then
			nouveaux += 1
		end
	end
	Hud.Pastille("inventaire", if nouveaux > 0 then tostring(nouveaux) else nil)
end

local function toutVoir()
	if not etat then
		return
	end
	local ensemble: { [string]: boolean } = {}
	for _, personnage in etat.Personnages do
		ensemble[personnage.Uid] = true
	end
	vus = ensemble
	majPastille()
end

local function choisirFiltre(nom: string)
	filtre = nom
	for autre, bouton in boutonsFiltres do
		local actif = autre == nom
		local face = bouton:FindFirstChild("Face") :: Frame
		local gradient = face:FindFirstChildOfClass("UIGradient")
		if gradient then
			gradient:Destroy()
		end
		local t = if autre == "Tous" then Ui.Teintes.Principal else Ui.Rarete(autre)
		if actif then
			Ui.Degrade2(t.Clair, t.Base).Parent = face
			face.BackgroundColor3 = Color3.new(1, 1, 1)
		else
			face.BackgroundColor3 = Ui.C.Zone
		end
		local label = face:FindFirstChild("Label") :: TextLabel
		label.TextColor3 = if actif and autre ~= "Tous" then Ui.TexteBadge[autre] or Ui.C.Texte else Ui.C.Texte
	end
	reconstruireGrille()
end

local function construireFiltres(parent: Frame)
	local rangee = Ui.Creer("Frame", {
		Name = "Filtres",
		Size = UDim2.new(1, 0, 0, 40),
		BackgroundTransparency = 1,
		Parent = parent,
	}, { Ui.Liste(Enum.FillDirection.Horizontal, 6, { VerticalAlignment = Enum.VerticalAlignment.Center }) })
	local noms = { "Tous" }
	for _, rarete in GachaConfig.Raretes do
		table.insert(noms, rarete.Id)
	end
	for ordre, nom in noms do
		local definition = GachaConfig.RaretesParId[nom]
		local bouton = Ui.Creer("TextButton", {
			Name = nom,
			LayoutOrder = ordre,
			AutomaticSize = Enum.AutomaticSize.X,
			Size = UDim2.fromOffset(0, 34),
			BackgroundTransparency = 1,
			AutoButtonColor = false,
			Text = "",
			Parent = rangee,
		})
		local face = Ui.Creer("Frame", {
			Name = "Face",
			AutomaticSize = Enum.AutomaticSize.X,
			Size = UDim2.fromOffset(0, 34),
			BackgroundColor3 = Ui.C.Zone,
			Parent = bouton,
		}, {
			Ui.Rond(),
			Ui.Trait(2),
			Ui.Marges(0, 11),
			Ui.Liste(Enum.FillDirection.Horizontal, 6, { VerticalAlignment = Enum.VerticalAlignment.Center }),
		})
		Ui.Creer("Frame", {
			Name = "Point",
			LayoutOrder = 1,
			Size = UDim2.fromOffset(10, 10),
			BackgroundColor3 = if definition then Ui.Rarete(nom).Base else Color3.new(1, 1, 1),
			Parent = face,
		}, { Ui.Rond(), Ui.Trait(2) })
		Ui.Texte({
			Name = "Label",
			LayoutOrder = 2,
			AutomaticSize = Enum.AutomaticSize.X,
			Size = UDim2.fromOffset(0, 34),
			TextSize = 14,
			Text = if definition then definition.Nom else nom,
			Parent = face,
		})
		Ui.Reagir(bouton, nil, nil, 1.05)
		bouton.Activated:Connect(function()
			choisirFiltre(nom)
		end)
		boutonsFiltres[nom] = bouton
	end
end

local function construireTri(parent: Frame)
	local rangee = Ui.Creer("Frame", {
		Name = "Tri",
		Position = UDim2.fromOffset(0, 46),
		Size = UDim2.new(1, 0, 0, 36),
		BackgroundTransparency = 1,
		Parent = parent,
	}, { Ui.Liste(Enum.FillDirection.Horizontal, 8, { VerticalAlignment = Enum.VerticalAlignment.Center }) })
	Ui.Texte({
		LayoutOrder = 1,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 34),
		FontFace = Ui.Montserrat(Enum.FontWeight.Bold),
		TextSize = 11,
		TextColor3 = Ui.C.TexteDiscret,
		Text = "TRIER PAR",
		Parent = rangee,
	})
	local onglets = Ui.Onglets(TRIS, function(index)
		tri = index
		reconstruireGrille()
	end, { LayoutOrder = 2, Parent = rangee }, nil, 28)
	onglets.Name = "Onglets"
	labelResume = Ui.Texte({
		Name = "Resume",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, 0, 0, 46),
		Size = UDim2.fromOffset(330, 36),
		FontFace = Ui.Montserrat(Enum.FontWeight.SemiBold),
		TextSize = 12,
		TextColor3 = Ui.C.TexteDiscret,
		TextXAlignment = Enum.TextXAlignment.Right,
		Parent = parent,
	})
end

local function construireDetail(parent: Frame)
	detail = Ui.Creer("Frame", {
		Name = "Detail",
		Position = UDim2.fromOffset(18 + LARGEUR_GRILLE + 16, 14),
		Size = UDim2.new(1, -(18 + LARGEUR_GRILLE + 16 + 18), 1, -32),
		BackgroundTransparency = 1,
		Visible = false,
		Parent = parent,
	})
	-- Vue 3D H 196
	fondVue = Ui.Creer("Frame", {
		Name = "Vue",
		Size = UDim2.new(1, 0, 0, 196),
		BackgroundColor3 = Color3.new(1, 1, 1),
		ClipsDescendants = true,
		Parent = detail,
	}, { Ui.Coins(16), Ui.Trait(2) })
	local rayons = Cartes.Rayons(fondVue, UDim2.fromScale(0.5, 0.5), 20, 170, 9, Color3.new(1, 1, 1), 0.82, 1)
	Cartes.Tourner(rayons, 360 / 14)
	Ui.Creer("Frame", {
		Name = "OmbreSol",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -14),
		Size = UDim2.fromOffset(130, 22),
		BackgroundColor3 = Color3.fromHex("#120E22"),
		BackgroundTransparency = 0.55,
		ZIndex = 2,
		Parent = fondVue,
	}, { Ui.Rond() })
	vue = Vue3D.Creer({
		Name = "Modele",
		Size = UDim2.fromScale(1, 1),
		ZIndex = 3,
		Parent = fondVue,
	})
	blocVue = Ui.Creer("Frame", {
		Name = "Bloc",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(110, 130),
		Visible = false,
		ZIndex = 3,
		Parent = fondVue,
	}, { Ui.Coins(16), Ui.Trait(2) })
	Ui.Texte({
		Name = "Initiale",
		Size = UDim2.fromScale(1, 1),
		TextSize = 70,
		TextXAlignment = Enum.TextXAlignment.Center,
		Contour = 2,
		ZIndex = 4,
		Parent = blocVue,
	})
	Ui.Lisere(fondVue, 3, 16, Color3.new(1, 1, 1), 0.5).ZIndex = 5

	local infos = Ui.Creer("Frame", {
		Name = "Infos",
		Position = UDim2.fromOffset(0, 206),
		Size = UDim2.fromScale(1, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		Parent = detail,
	}, { Ui.Liste(Enum.FillDirection.Vertical, 6) })
	labelNom = Ui.Texte({
		Name = "Nom",
		LayoutOrder = 1,
		Size = UDim2.new(1, 0, 0, 26),
		TextSize = 24,
		TextTruncate = Enum.TextTruncate.AtEnd,
		Contour = true,
		Parent = infos,
	})
	local ligne = Ui.Creer("Frame", {
		LayoutOrder = 2,
		Size = UDim2.new(1, 0, 0, 24),
		BackgroundTransparency = 1,
		Parent = infos,
	}, { Ui.Liste(Enum.FillDirection.Horizontal, 8, { VerticalAlignment = Enum.VerticalAlignment.Center }) })
	fondBadge, badgeRarete = Ui.EtiquetteDegrade({
		Name = "Rarete",
		LayoutOrder = 1,
		Size = UDim2.fromOffset(0, 24),
		Parent = ligne,
	}, Ui.Degrade2(Color3.new(1, 1, 1), Color3.new(1, 1, 1)), {
		FontFace = Ui.Montserrat(Enum.FontWeight.Bold),
		TextSize = 11,
	})
	Ui.Rond().Parent = fondBadge
	Ui.Trait(2).Parent = fondBadge
	Ui.Marges(0, 10).Parent = fondBadge
	cadreEtoiles = Ui.Creer("Frame", {
		Name = "Etoiles",
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 18),
		BackgroundTransparency = 1,
		Parent = ligne,
	})

	local stats = Ui.Zone({
		Name = "Stats",
		LayoutOrder = 3,
		Size = UDim2.fromScale(1, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		Parent = infos,
	})
	Ui.Marges(10, 12).Parent = stats
	Ui.Liste(Enum.FillDirection.Vertical, 6).Parent = stats
	local function ligneStat(ordre: number, nom: string): TextLabel
		local cadre = Ui.Creer("Frame", {
			LayoutOrder = ordre,
			Size = UDim2.new(1, 0, 0, 20),
			BackgroundTransparency = 1,
			Parent = stats,
		})
		Ui.Texte({
			Size = UDim2.fromScale(0.4, 1),
			FontFace = Ui.Montserrat(Enum.FontWeight.SemiBold),
			TextSize = 12,
			TextColor3 = Ui.C.TexteDiscret,
			Text = nom,
			Parent = cadre,
		})
		return Ui.Texte({
			AnchorPoint = Vector2.new(1, 0),
			Position = UDim2.fromScale(1, 0),
			Size = UDim2.fromScale(0.6, 1),
			FontFace = Ui.Montserrat(Enum.FontWeight.Bold),
			TextSize = 12,
			TextXAlignment = Enum.TextXAlignment.Right,
			Parent = cadre,
		})
	end
	labelRevenu = ligneStat(1, "Revenu")
	labelRevenu.FontFace = Font.fromEnum(Ui.Police)
	labelRevenu.TextSize = 18
	labelRevenu.TextColor3 = Ui.C.Gain
	labelCalcul = Ui.Texte({
		LayoutOrder = 2,
		Size = UDim2.fromScale(1, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		FontFace = Ui.Montserrat(Enum.FontWeight.Medium),
		TextSize = 11,
		TextWrapped = true,
		TextColor3 = Ui.C.TexteDiscret,
		Parent = stats,
	})
	Ui.Creer("Frame", {
		LayoutOrder = 3,
		Size = UDim2.new(1, 0, 0, 2),
		BackgroundColor3 = Color3.fromHex("#3A3462"),
		BorderSizePixel = 0,
		Parent = stats,
	})
	labelEtat = ligneStat(4, "État")

	-- Boutons en bas : Poser / Retirer (H 50), Recycler (H 44, désactivé : règles à définir)
	boutonAction = Ui.Bouton({
		Name = "Action",
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.new(0, 0, 1, -76),
		Size = UDim2.new(1, 0, 0, 50),
		Texte = "Poser",
		TailleTexte = 20,
		Parent = detail,
	})
	boutonAction.Activated:Connect(function()
		local personnage = trouver(selection)
		if personnage then
			demander(if personnage.Emplacement then "Retirer" else "Poser", personnage.Uid)
		end
	end)
	Ui.Bouton({
		Name = "Recycler",
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.new(0, 0, 1, -20),
		Size = UDim2.new(1, 0, 0, 44),
		Style = "Desactive",
		Texte = "Recycler",
		TailleTexte = 17,
		Icone = "recyclage",
		TailleIcone = 24,
		Parent = detail,
	})
	Ui.Texte({
		Name = "NoteRecycler",
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Size = UDim2.new(1, 0, 0, 14),
		FontFace = Ui.Montserrat(Enum.FontWeight.Medium),
		TextSize = 11,
		TextColor3 = Ui.C.TexteEteint,
		TextXAlignment = Enum.TextXAlignment.Center,
		Text = "Recyclage : bientôt (règles à définir)",
		Parent = detail,
	})
end

function Inventaire.Init()
	fenetre = Ui.Fenetre({
		Nom = "Inventaire",
		Titre = "Inventaire",
		Icone = "inventaire",
		Ruban = UiConfig.CouleursFonctions.inventaire,
		Taille = Vector2.new(1060, 570),
		Position = UDim2.new(0.5, 0, 0.5, 18),
	})
	-- Compteur « N / 100 » dans l'en-tête, à gauche du bouton fermer
	local entete = fenetre.Cadre:FindFirstChild("Entete", true) :: Frame
	labelCompteur = Ui.Texte({
		Name = "Compteur",
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, -64, 0.5, 0),
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 34),
		BackgroundTransparency = 0,
		BackgroundColor3 = Ui.C.Trait,
		TextSize = 18,
		Text = "0 / 0",
		Parent = entete,
	})
	Ui.Rond().Parent = labelCompteur
	Ui.Marges(0, 14).Parent = labelCompteur

	local contenu = fenetre.Contenu
	local gauche = Ui.Creer("Frame", {
		Name = "Gauche",
		Position = UDim2.fromOffset(18, 14),
		Size = UDim2.new(0, LARGEUR_GRILLE, 1, -32),
		BackgroundTransparency = 1,
		Parent = contenu,
	})
	construireFiltres(gauche)
	-- Recherche : TextBox 176 × 36 à droite des filtres
	local champ = Ui.Creer("Frame", {
		Name = "Recherche",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, 0, 0, 2),
		Size = UDim2.fromOffset(176, 36),
		BackgroundColor3 = Ui.C.Trait,
		Parent = gauche,
	}, {
		Ui.Rond(),
		Ui.Contour(Color3.fromHex("#605096"), 2),
		Ui.Marges(0, 10),
		Ui.Liste(Enum.FillDirection.Horizontal, 6, { VerticalAlignment = Enum.VerticalAlignment.Center }),
	})
	Ui.Icone("loupe", 20, { LayoutOrder = 1, Parent = champ })
	local saisie: TextBox = Ui.Creer("TextBox", {
		LayoutOrder = 2,
		Size = UDim2.new(1, -26, 1, 0),
		BackgroundTransparency = 1,
		ClearTextOnFocus = false,
		FontFace = Ui.Montserrat(Enum.FontWeight.SemiBold),
		TextSize = 13,
		TextColor3 = Ui.C.Texte,
		PlaceholderText = "Rechercher…",
		PlaceholderColor3 = Ui.C.TexteEteint,
		TextXAlignment = Enum.TextXAlignment.Left,
		TextTruncate = Enum.TextTruncate.AtEnd,
		Text = "",
		Parent = champ,
	})
	saisie:GetPropertyChangedSignal("Text"):Connect(function()
		if utf8.len(saisie.Text) and (utf8.len(saisie.Text) :: number) > LONGUEUR_RECHERCHE then
			saisie.Text = string.sub(saisie.Text, 1, utf8.offset(saisie.Text, LONGUEUR_RECHERCHE + 1) - 1)
			return
		end
		recherche = string.lower(saisie.Text)
		reconstruireGrille()
	end)
	construireTri(gauche)
	grille = Ui.Creer("ScrollingFrame", {
		Name = "Grille",
		Position = UDim2.fromOffset(0, 90),
		Size = UDim2.new(1, 0, 1, -90),
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 6,
		ScrollBarImageColor3 = Ui.C.Lisere,
		Parent = gauche,
	}, {
		Ui.Creer("UIGridLayout", {
			CellSize = UDim2.fromOffset(Cartes.Taille.X, Cartes.Taille.Y + 8),
			CellPadding = UDim2.fromOffset(12, 8),
			SortOrder = Enum.SortOrder.LayoutOrder,
		}),
		Ui.Marges(2, 10, 10, 6),
	})
	labelVide = Ui.Texte({
		Name = "Vide",
		Position = UDim2.fromOffset(0, 150),
		Size = UDim2.new(1, 0, 0, 30),
		TextSize = 18,
		TextColor3 = Ui.C.TexteEteint,
		TextXAlignment = Enum.TextXAlignment.Center,
		Text = "Aucun personnage ne correspond.",
		Visible = false,
		Parent = gauche,
	})
	construireDetail(contenu)
	choisirFiltre("Tous")

	fenetre.AuChangement(function(ouverte)
		if ouverte then
			toutVoir()
			Inventaire.Rafraichir()
		else
			Vue3D.Vider(vue)
			idAffiche3D = nil
		end
	end)
	Hud.SurMenu("inventaire", fenetre.Basculer)
end

function Inventaire.MettreAJour(nouvelEtat: Remotes.EtatInventaire)
	etat = nouvelEtat
	if not vus or fenetre.EstOuverte() then
		toutVoir() -- premier envoi : tout ce qui existe déjà est « vu »
	else
		majPastille()
	end
	Inventaire.Rafraichir()
end

-- Dernier état reçu (utilisé par l'Index pour le meilleur score d'étoiles).
function Inventaire.Etat(): Remotes.EtatInventaire?
	return etat
end

return Inventaire
