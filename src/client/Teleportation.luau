--!strict
-- Teleportation : fenêtre avec la mini-carte du Hub (MiniCarteHub2 du handoff) et la liste des stands, bouton Ma base,
-- barre rapide en haut au centre (Hub, Ma base) et effet manga plein écran pendant le trajet.
-- Le serveur fait la téléportation (Remotes "Teleporter", validée dans DeplacementService).

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Remotes = require(ReplicatedStorage.Shared.Remotes)
local UiConfig = require(ReplicatedStorage.Shared.UiConfig)
local Hud = require(script.Parent.Hud)
local Ui = require(script.Parent.Ui)

local Teleportation = {}

local joueur = Players.LocalPlayer

local TAILLE_CARTE = 420
local C = TAILLE_CARTE / 2
local RAYON_STANDS = 100
local RAYON_BASES = 188
local DUREE_EFFET = 1.2
local DUREE_ENTREE = 0.22 -- fondu d'entrée de l'écran de transition
local DUREE_SORTIE = 0.3 -- fondu de sortie, une fois arrivé
local DUREE_MIN_EFFET = 0.9 -- l'écran reste couvert au moins ce temps (plaque du lieu lisible)
local ATTENTE_ARRIVEE = 1.5 -- secondes max d'attente de la nouvelle position après la réponse du serveur
local DISTANCE_QUITTE = 30 -- studs : au-delà, on n'est plus « sur place » (anneau de la barre rapide)
local RUBAN = { Clair = Color3.fromHex("#7FE0FF"), Base = Color3.fromHex("#2E9BE0"), Fonce = Color3.fromHex("#1A6FA8") }

local fenetre: Ui.Fenetre
local racineUi: Frame
local notifier: (string, string?) -> ()
local barreRapide: Frame
local survolCarte: { [string]: (boolean) -> () } = {} -- surbrillance des lieux sur la carte
local survolListe: { [string]: (boolean) -> () } = {}
local anneauxBarre: { [string]: Frame } = {}
local infobulle: Frame
local lieuActuel: string? = "base"
local pointArrivee: Vector3? = nil
local enCours = false

local function position(angle: number, rayon: number): Vector2
	local a = math.rad(angle)
	return Vector2.new(C + rayon * math.sin(a), C - rayon * math.cos(a))
end

-- Index (1..7) de l'emplacement de la base du joueur autour du Hub, d'après la position de son Centre.
local function indexDeMaBase(): number
	local hub = workspace:FindFirstChild("Hub")
	local emplacements = hub and hub:FindFirstChild("EmplacementsBases")
	if not emplacements then
		return 1
	end
	for _, base in CollectionService:GetTagged("BaseJoueur") do
		if base:IsA("Model") and base:GetAttribute("Proprietaire") == joueur.UserId then
			local centre = base:GetPivot().Position
			local meilleur, distance = 1, math.huge
			for _, emplacement in emplacements:GetChildren() do
				local n = tonumber(string.match(emplacement.Name, "^Base(%d+)$"))
				if n and emplacement:IsA("BasePart") then
					local d = (emplacement.Position - centre).Magnitude
					if d < distance then
						meilleur, distance = n, d
					end
				end
			end
			return meilleur
		end
	end
	return 1
end

-- Anneau blanc de 3 px derrière un élément (surbrillance, lieu actuel)
local function anneau(parent: GuiObject, cible: GuiObject, rond: boolean, rayon: number?): Frame
	return Ui.Creer("Frame", {
		Name = "Anneau",
		AnchorPoint = cible.AnchorPoint,
		Position = cible.Position,
		Size = cible.Size + UDim2.fromOffset(6, 6),
		BackgroundColor3 = Color3.new(1, 1, 1),
		Visible = false,
		ZIndex = cible.ZIndex - 1,
		Parent = parent,
	}, { if rond then Ui.Rond() else Ui.Coins((rayon or 11) + 3) })
end

local function survoler(id: string?, actif: boolean)
	for autre, rappel in survolCarte do
		rappel(actif and autre == id)
	end
	for autre, rappel in survolListe do
		rappel(actif and autre == id)
	end
	local lieu = id and UiConfig.LieuxParId[id]
	infobulle.Visible = actif and lieu ~= nil
	if not (actif and lieu) then
		return
	end
	local barre = infobulle:FindFirstChild("Couleur") :: Frame
	local nom = infobulle:FindFirstChild("Nom", true) :: TextLabel
	local description = infobulle:FindFirstChild("Description", true) :: TextLabel
	barre.BackgroundColor3 = lieu.Teinte.Base
	nom.TextColor3 = lieu.Teinte.Base
	nom.Text = lieu.Nom
	description.Text = lieu.Description
	-- au-dessus du lieu, ou en dessous s'il est en haut de la carte
	local centre = Vector2.new(C, C - 4)
	local demi = 50
	if lieu.Angle then
		centre, demi = position(lieu.Angle, RAYON_STANDS), 36
	elseif lieu.Id == "base" then
		centre, demi = position((indexDeMaBase() - 1) * 360 / UiConfig.NombreBases, 186), 32
	end
	local x = math.clamp(centre.X - 110, 6, TAILLE_CARTE - 226)
	if centre.Y < 150 then
		infobulle.Position = UDim2.fromOffset(x, centre.Y + demi)
	else
		infobulle.Position = UDim2.fromOffset(x, centre.Y - demi - 66)
	end
end

-- Effet manga plein écran : fond blanc, lignes de vitesse qui tournent et grossissent, plaque du lieu, flash.
-- Renvoie la fonction qui termine l'effet (fondu de sortie) : l'écran reste couvert jusqu'à son appel.
local function jouerEffet(lieu: UiConfig.Lieu): () -> ()
	local groupe = Ui.Creer("CanvasGroup", {
		Name = "EffetTeleportation",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Color3.new(1, 1, 1),
		GroupTransparency = 1,
		ZIndex = 60,
		Parent = racineUi,
	})
	local lignes = Ui.Creer("Frame", {
		Name = "Lignes",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(0, 0),
		BackgroundTransparency = 1,
		Parent = groupe,
	})
	local echelleLignes = Ui.Creer("UIScale", { Scale = 0.7, Parent = lignes })
	local graine = Random.new(7)
	for i = 0, 71 do
		local pivot = Ui.Creer("Frame", {
			Rotation = i * 5 + graine:NextNumber(-1.5, 1.5),
			Size = UDim2.fromOffset(0, 0),
			BackgroundTransparency = 1,
			Parent = lignes,
		})
		local debut = graine:NextNumber(150, 260)
		Ui.Creer("Frame", {
			AnchorPoint = Vector2.new(0, 0.5),
			Position = UDim2.fromOffset(debut, 0),
			Size = UDim2.fromOffset(1200, if i % 3 == 0 then 7 else 3),
			BackgroundColor3 = Ui.C.Trait,
			BorderSizePixel = 0,
			Parent = pivot,
		}, {
			Ui.Creer("UIGradient", {
				Transparency = NumberSequence.new({
					NumberSequenceKeypoint.new(0, 1),
					NumberSequenceKeypoint.new(0.12, 0),
					NumberSequenceKeypoint.new(1, 0),
				}),
			}),
		})
	end
	-- Plaque : ombre de la couleur du lieu décalée de 6 px, cadre blanc à trait de 3 px
	local plaque = Ui.Creer("Frame", {
		Name = "Plaque",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 82),
		BackgroundTransparency = 1,
		ZIndex = 3,
		Parent = groupe,
	})
	local echellePlaque = Ui.Creer("UIScale", { Scale = 1.8, Parent = plaque })
	local blanc = Ui.Creer("Frame", {
		Name = "Blanc",
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 76),
		BackgroundColor3 = Color3.new(1, 1, 1),
		ZIndex = 4,
		Parent = plaque,
	}, {
		Ui.Trait(3),
		Ui.Marges(0, 24, 0, 14),
		Ui.Liste(Enum.FillDirection.Horizontal, 12, { VerticalAlignment = Enum.VerticalAlignment.Center }),
	})
	Ui.Creer("Frame", {
		Name = "OmbreCouleur",
		Position = UDim2.fromOffset(6, 6),
		Size = UDim2.new(1, 0, 0, 76),
		BackgroundColor3 = lieu.Teinte.Base,
		ZIndex = 3,
		Parent = plaque,
	}, { Ui.Trait(3) })
	Ui.Icone(lieu.Icone, 56, { LayoutOrder = 1, ZIndex = 5, Parent = blanc })
	Ui.Texte({
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 76),
		TextSize = 40,
		TextColor3 = Ui.C.Trait,
		Text = lieu.Nom,
		ZIndex = 5,
		Parent = blanc,
	})
	local flash = Ui.Creer("Frame", {
		Name = "Flash",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Color3.new(1, 1, 1),
		ZIndex = 10,
		Parent = groupe,
	})

	Ui.Tween(groupe, DUREE_ENTREE, { GroupTransparency = 0 })
	Ui.Tween(echelleLignes, DUREE_EFFET * 1.5, { Scale = 1.9 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	Ui.Tween(lignes, DUREE_EFFET * 1.5, { Rotation = 14 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	Ui.Tween(echellePlaque, 0.35, { Scale = 1 }, Enum.EasingStyle.Back)
	Ui.Tween(flash, 0.3, { BackgroundTransparency = 1 })
	local termine = false
	return function()
		if termine then
			return
		end
		termine = true
		Ui.Tween(groupe, DUREE_SORTIE, { GroupTransparency = 1 })
		task.delay(DUREE_SORTIE + 0.05, function()
			groupe:Destroy()
		end)
	end
end

local function majBarreRapide()
	for id, cadre in anneauxBarre do
		cadre.Visible = id == lieuActuel
	end
end

-- Téléportation pendant l'écran de transition : la demande part dès que l'écran est couvert, et le fondu de sortie
-- n'a lieu qu'une fois le personnage arrivé (position reçue du serveur), jamais avant.
function Teleportation.Aller(id: string)
	local lieu = UiConfig.LieuxParId[id]
	if not lieu or enCours then
		return
	end
	enCours = true
	fenetre.Fermer()
	local debut = os.clock()
	local terminer = jouerEffet(lieu)
	local function racinePerso(): BasePart?
		local character = joueur.Character
		local racine = character and character:FindFirstChild("HumanoidRootPart")
		return if racine and racine:IsA("BasePart") then racine else nil
	end
	local depart = racinePerso()
	local positionDepart = if depart then depart.Position else nil

	task.spawn(function()
		task.wait(DUREE_ENTREE) -- écran couvert
		local ok, reussi = pcall(function()
			return Remotes.Fonction("Teleporter"):InvokeServer(id)
		end)
		local succes = ok and reussi == true
		if succes then
			-- attendre que la nouvelle position du personnage soit arrivée (au plus ATTENTE_ARRIVEE s)
			local limite = os.clock() + ATTENTE_ARRIVEE
			while os.clock() < limite do
				local racine = racinePerso()
				if not positionDepart or (racine and (racine.Position - positionDepart).Magnitude > 5) then
					break
				end
				task.wait()
			end
			local racine = racinePerso()
			lieuActuel = id
			pointArrivee = if racine then racine.Position else nil
			-- caméra derrière le joueur, tournée vers le lieu (le serveur l'a tourné vers le comptoir)
			local camera = workspace.CurrentCamera
			if camera and racine then
				local avant = racine.CFrame.LookVector
				camera.CFrame = CFrame.lookAt(racine.Position - avant * 14 + Vector3.new(0, 6, 0), racine.Position + avant * 6)
			end
			majBarreRapide()
			-- laisser la plaque du lieu lisible un minimum de temps
			local reste = DUREE_MIN_EFFET - (os.clock() - debut)
			if reste > 0 then
				task.wait(reste)
			end
		end
		terminer()
		enCours = false
		if succes then
			notifier(if id == "base" then "Retour à ta base !" else `Arrivé : {lieu.Nom}`, "succes")
		else
			notifier("Téléportation impossible pour l'instant", "erreur")
		end
	end)
end

local function construireCarte(parent: Frame)
	local carte = Ui.Creer("Frame", {
		Name = "MiniCarte",
		Position = UDim2.fromOffset(18, 14),
		Size = UDim2.fromOffset(TAILLE_CARTE, TAILLE_CARTE),
		BackgroundColor3 = Color3.new(1, 1, 1),
		Parent = parent,
	}, {
		Ui.Coins(16),
		Ui.Trait(2),
		Ui.Creer("UIGradient", {
			Color = ColorSequence.new({
				ColorSequenceKeypoint.new(0, Color3.fromHex("#1C3A34")),
				ColorSequenceKeypoint.new(0.5, Color3.fromHex("#2C5A4C")),
				ColorSequenceKeypoint.new(1, Color3.fromHex("#122420")),
			}),
			Rotation = 90,
		}),
	})
	local function rond(nom: string, taille: number, centre: Vector2, props: { [string]: any }?): Frame
		local defauts: { [string]: any } = {
			Name = nom,
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromOffset(centre.X, centre.Y),
			Size = UDim2.fromOffset(taille, taille),
			BackgroundColor3 = Color3.new(1, 1, 1),
			Parent = carte,
		}
		for cle, valeur in props or {} do
			defauts[cle] = valeur
		end
		return Ui.Creer("Frame", defauts, { Ui.Rond() })
	end
	local milieu = Vector2.new(C, C)
	-- Bord de l'île (cercle pointillé dans la maquette)
	local bord = rond("Bord", 396, milieu, { BackgroundTransparency = 1 })
	Ui.Contour(Color3.fromHex("#C9C3E6"), 1.5, 0.7).Parent = bord

	-- 7 chemins espacés de 360/7°, de 128 à 170 px du centre
	local pas = 360 / UiConfig.NombreBases
	for i = 0, UiConfig.NombreBases - 1 do
		local pivot = Ui.Creer("Frame", {
			Name = `Chemin{i + 1}`,
			Position = UDim2.fromOffset(C, C),
			Size = UDim2.fromOffset(0, 0),
			Rotation = i * pas,
			BackgroundTransparency = 1,
			Parent = carte,
		})
		Ui.Creer("Frame", {
			Position = UDim2.fromOffset(-8, -170),
			Size = UDim2.fromOffset(16, 42),
			BackgroundColor3 = Color3.new(1, 1, 1),
			Parent = pivot,
		}, {
			Ui.Coins(3),
			Ui.Trait(1.5),
			Ui.Creer("UIGradient", {
				Color = ColorSequence.new({
					ColorSequenceKeypoint.new(0, Color3.fromHex("#8C80C8")),
					ColorSequenceKeypoint.new(0.5, Color3.fromHex("#B4AAE6")),
					ColorSequenceKeypoint.new(1, Color3.fromHex("#8C80C8")),
				}),
			}),
		})
	end

	-- Bases des autres joueurs (numérotées) et la mienne (bouton Ma base)
	local maBase = indexDeMaBase()
	for n = 1, UiConfig.NombreBases do
		if n ~= maBase then
			local p = position((n - 1) * pas, RAYON_BASES)
			local case = Ui.Creer("Frame", {
				Name = `Base{n}`,
				AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromOffset(p.X, p.Y),
				Size = UDim2.fromOffset(36, 36),
				BackgroundColor3 = Color3.new(1, 1, 1),
				Parent = carte,
			}, {
				Ui.Coins(8),
				Ui.Trait(1.5),
				Ui.Degrade2(Color3.fromHex("#3A3462"), Color3.fromHex("#221C42")),
			})
			Ui.Texte({
				Size = UDim2.fromScale(1, 1),
				TextSize = 14,
				TextColor3 = Ui.C.TexteEteint,
				TextXAlignment = Enum.TextXAlignment.Center,
				Text = tostring(n),
				Parent = case,
			})
		end
	end

	-- Plateau du Hub
	local plateau = rond("Plateau", 264, milieu, { ZIndex = 1 })
	Ui.Trait(2).Parent = plateau
	Ui.Degrade(
		{ Clair = Color3.fromHex("#5A5096"), Base = Color3.fromHex("#3A3270"), Fonce = Color3.fromHex("#262050") },
		90
	).Parent =
		plateau
	local anneauInterieur = rond("AnneauInterieur", 252, milieu, { BackgroundTransparency = 1 })
	Ui.Contour(Color3.fromHex("#C9B6FF"), 1, 0.65).Parent = anneauInterieur
	local place = rond("Place", 128, milieu)
	Ui.Trait(2).Parent = place
	Ui.Degrade2(Color3.fromHex("#7468B8"), Color3.fromHex("#564A98")).Parent = place
	for _, angle in UiConfig.AnglesLibres do
		local libre = rond("Libre", 28, position(angle, RAYON_STANDS), { BackgroundTransparency = 1 })
		Ui.Contour(Color3.fromHex("#8A80C0"), 1.5, 0.3).Parent = libre
	end

	-- Bouton d'un lieu sur la carte : rond (stands, centre) ou carré (Ma base)
	local function lieuCarte(lieu: UiConfig.Lieu, taille: number, centre: Vector2, tailleIcone: number, carre: boolean)
		local bouton = Ui.Creer("TextButton", {
			Name = lieu.Id,
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromOffset(centre.X, centre.Y),
			Size = UDim2.fromOffset(taille, taille),
			BackgroundColor3 = Color3.new(1, 1, 1),
			AutoButtonColor = false,
			Text = "",
			ZIndex = 4,
			Parent = carte,
		}, {
			if carre then Ui.Coins(11) else Ui.Rond(),
			Ui.Trait(2),
			Ui.Degrade(lieu.Teinte, 90, if carre then 0.25 else 0, 0.45),
		})
		local bordure = anneau(carte, bouton, not carre, 11)
		Ui.Lisere(bouton, if carre then 2 else 3, if carre then 11 else taille / 2, Color3.new(1, 1, 1), 0.4, 1.5)
		Ui.Icone(lieu.Icone, tailleIcone, {
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, 0.5),
			ZIndex = 5,
			Parent = bouton,
		})
		Ui.Reagir(bouton, nil, nil, 1.12)
		local echelleBordure = Ui.Creer("UIScale", { Parent = bordure })
		local echelleBouton = bouton:FindFirstChildOfClass("UIScale") :: UIScale
		echelleBouton:GetPropertyChangedSignal("Scale"):Connect(function()
			echelleBordure.Scale = echelleBouton.Scale
		end)
		survolCarte[lieu.Id] = function(actif: boolean)
			bordure.Visible = actif
		end
		bouton.MouseEnter:Connect(function()
			survoler(lieu.Id, true)
		end)
		bouton.MouseLeave:Connect(function()
			survoler(lieu.Id, false)
		end)
		bouton.Activated:Connect(function()
			Teleportation.Aller(lieu.Id)
		end)
	end

	for _, lieu in UiConfig.Lieux do
		if lieu.Angle then
			lieuCarte(lieu, 56, position(lieu.Angle, RAYON_STANDS), 36, false)
		end
	end
	lieuCarte(UiConfig.LieuxParId.base, 48, position((maBase - 1) * pas, 186), 34, true)

	-- Rayons dorés qui tournent derrière le centre (12 s par tour)
	local rayons = Ui.Creer("Frame", {
		Name = "Rayons",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromOffset(C, C - 4),
		Size = UDim2.fromOffset(0, 0),
		BackgroundTransparency = 1,
		ZIndex = 3,
		Parent = carte,
	})
	for i = 0, 11 do
		local pivot = Ui.Creer("Frame", {
			Rotation = i * 30,
			Size = UDim2.fromOffset(0, 0),
			BackgroundTransparency = 1,
			ZIndex = 3,
			Parent = rayons,
		})
		Ui.Creer("Frame", {
			AnchorPoint = Vector2.new(0, 0.5),
			Position = UDim2.fromOffset(28, 0),
			Size = UDim2.fromOffset(42, 7),
			BackgroundColor3 = Ui.C.Filet,
			BackgroundTransparency = 0.55,
			BorderSizePixel = 0,
			ZIndex = 3,
			Parent = pivot,
		}, { Ui.Creer("UIGradient", { Transparency = NumberSequence.new(0, 1) }) })
	end
	RunService.RenderStepped:Connect(function()
		if fenetre.EstOuverte() then
			rayons.Rotation = (os.clock() * 30) % 360
		end
	end)
	lieuCarte(UiConfig.LieuxParId.centre, 88, Vector2.new(C, C - 4), 52, false)
	local etiquette = Ui.Texte({
		Name = "EtiquetteCentre",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.fromOffset(C, 254),
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 20),
		BackgroundTransparency = 0,
		BackgroundColor3 = Ui.C.Trait,
		TextSize = 12,
		TextColor3 = Ui.C.Or,
		Text = "Centre du Hub",
		ZIndex = 6,
		Parent = carte,
	})
	Ui.Coins(6).Parent = etiquette
	Ui.Contour(Ui.C.Or, 1).Parent = etiquette
	Ui.Marges(0, 9).Parent = etiquette

	-- Infobulle du lieu survolé
	infobulle = Ui.Creer("Frame", {
		Name = "Infobulle",
		Size = UDim2.fromOffset(220, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundColor3 = Color3.new(1, 1, 1),
		Visible = false,
		ZIndex = 10,
		Parent = carte,
	}, { Ui.Coins(10), Ui.Trait(2), Ui.Degrade2(Ui.C.PanneauHaut, Ui.C.PanneauBas) })
	Ui.Creer("Frame", {
		Name = "Couleur",
		Size = UDim2.new(0, 5, 1, 0),
		BorderSizePixel = 0,
		ZIndex = 11,
		Parent = infobulle,
	})
	local textes = Ui.Creer("Frame", {
		Position = UDim2.fromOffset(5, 0),
		Size = UDim2.new(1, -5, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		ZIndex = 11,
		Parent = infobulle,
	}, { Ui.Marges(7, 11), Ui.Liste(Enum.FillDirection.Vertical, 2) })
	Ui.Texte({
		Name = "Nom",
		LayoutOrder = 1,
		Size = UDim2.new(1, 0, 0, 18),
		TextSize = 15,
		ZIndex = 11,
		Parent = textes,
	})
	Ui.Texte({
		Name = "Description",
		LayoutOrder = 2,
		Size = UDim2.fromScale(1, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		FontFace = Ui.Montserrat(Enum.FontWeight.Medium),
		TextSize = 12,
		TextWrapped = true,
		ZIndex = 11,
		Parent = textes,
	})
end

local function construireListe(parent: Frame)
	local colonne = Ui.Creer("Frame", {
		Name = "Liste",
		Position = UDim2.fromOffset(18 + TAILLE_CARTE + 18, 14),
		Size = UDim2.new(1, -(18 + TAILLE_CARTE + 18 + 18), 1, -28),
		BackgroundTransparency = 1,
		Parent = parent,
	}, { Ui.Liste(Enum.FillDirection.Vertical, 6) })
	Ui.Texte({
		LayoutOrder = 0,
		Size = UDim2.new(1, 0, 0, 16),
		FontFace = Ui.Montserrat(Enum.FontWeight.ExtraBold),
		TextSize = 10,
		TextColor3 = Ui.C.TexteDiscret,
		Text = "STANDS DU HUB",
		Parent = colonne,
	})
	for ordre, id in UiConfig.StandsListe do
		local lieu = UiConfig.LieuxParId[id]
		local ligne = Ui.Creer("TextButton", {
			Name = id,
			LayoutOrder = ordre,
			Size = UDim2.new(1, 0, 0, 50),
			BackgroundColor3 = Ui.C.Zone,
			AutoButtonColor = false,
			ClipsDescendants = true,
			Text = "",
			Parent = colonne,
		}, { Ui.Coins(10) })
		local contour = Ui.Contour(Ui.C.LisereSombre, 1.5)
		contour.Parent = ligne
		local interieur = Ui.Creer("Frame", {
			Name = "Interieur",
			Size = UDim2.fromScale(1, 1),
			BackgroundTransparency = 1,
			Parent = ligne,
		})
		Ui.Creer("Frame", {
			Name = "Barre",
			Size = UDim2.new(0, 5, 1, 0),
			BackgroundColor3 = lieu.Teinte.Base,
			BorderSizePixel = 0,
			Parent = interieur,
		})
		local orbe = Ui.Creer("Frame", {
			Name = "Orbe",
			AnchorPoint = Vector2.new(0, 0.5),
			Position = UDim2.new(0, 15, 0.5, 0),
			Size = UDim2.fromOffset(38, 38),
			BackgroundColor3 = Color3.new(1, 1, 1),
			Parent = interieur,
		}, { Ui.Rond(), Ui.Trait(1.5), Ui.Degrade(lieu.Teinte, 90) })
		Ui.Icone(lieu.Icone, 26, {
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, 0.5),
			Parent = orbe,
		})
		Ui.Texte({
			Position = UDim2.fromOffset(63, 6),
			Size = UDim2.new(1, -90, 0, 20),
			TextSize = 17,
			Text = lieu.Nom,
			Parent = interieur,
		})
		Ui.Texte({
			Position = UDim2.fromOffset(63, 27),
			Size = UDim2.new(1, -90, 0, 14),
			FontFace = Ui.Montserrat(Enum.FontWeight.Medium),
			TextSize = 11,
			TextColor3 = Ui.C.TexteDiscret,
			TextTruncate = Enum.TextTruncate.AtEnd,
			Text = lieu.Description,
			Parent = interieur,
		})
		Ui.Texte({
			AnchorPoint = Vector2.new(1, 0.5),
			Position = UDim2.new(1, -12, 0.5, 0),
			Size = UDim2.fromOffset(12, 20),
			TextSize = 18,
			TextColor3 = lieu.Teinte.Base,
			TextXAlignment = Enum.TextXAlignment.Right,
			Text = ">",
			Parent = interieur,
		})
		survolListe[id] = function(actif: boolean)
			ligne.BackgroundColor3 = if actif then Ui.C.ZoneSurvol else Ui.C.Zone
			contour.Color = if actif then lieu.Teinte.Base else Ui.C.LisereSombre
			Ui.Tween(interieur, 0.12, { Position = UDim2.fromOffset(if actif then 4 else 0, 0) }, Enum.EasingStyle.Back)
		end
		ligne.MouseEnter:Connect(function()
			survoler(id, true)
		end)
		ligne.MouseLeave:Connect(function()
			survoler(id, false)
		end)
		ligne.Activated:Connect(function()
			Teleportation.Aller(id)
		end)
	end

	local base = Ui.Bouton({
		Name = "MaBase",
		LayoutOrder = 10,
		Size = UDim2.new(1, 0, 0, 50),
		Style = "Base",
		Texte = "Ma base",
		TailleTexte = 20,
		Icone = "base",
		TailleIcone = 34,
		Parent = colonne,
	})
	base.Activated:Connect(function()
		Teleportation.Aller("base")
	end)
	-- marge au-dessus du bouton
	Ui.Creer("Frame", { LayoutOrder = 9, Size = UDim2.fromOffset(0, 0), BackgroundTransparency = 1, Parent = colonne })

	local rangee = Ui.Creer("Frame", {
		Name = "BarreRapide",
		LayoutOrder = 11,
		Size = UDim2.new(1, 0, 0, 40),
		BackgroundTransparency = 1,
		Parent = colonne,
	}, {
		Ui.Liste(Enum.FillDirection.Horizontal, 10, { VerticalAlignment = Enum.VerticalAlignment.Center }),
	})
	local interrupteur, majInterrupteur = Ui.Interrupteur({ LayoutOrder = 1, Parent = rangee }, function(actif)
		-- la barre rapide ne cache que les raccourcis de lieux, pas le bouton Mes stats
		for _, enfant in barreRapide:GetChildren() do
			if enfant:IsA("GuiObject") and enfant.Name ~= "stats" then
				enfant.Visible = actif
			end
		end
	end)
	majInterrupteur(true)
	interrupteur.Name = "Interrupteur"
	Ui.Texte({
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 40),
		FontFace = Ui.Montserrat(Enum.FontWeight.SemiBold),
		TextSize = 13,
		Text = "Barre rapide à l'écran",
		Parent = rangee,
	})
end

local function construireBarreRapide(racine: Frame)
	barreRapide = Ui.Creer("Frame", {
		Name = "BarreRapide",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 12),
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 52),
		BackgroundTransparency = 1,
		Parent = racine,
	}, { Ui.Liste(Enum.FillDirection.Horizontal, 10) })
	for ordre, id in UiConfig.BarreRapide do
		local lieu = UiConfig.LieuxParId[id]
		local bouton = Ui.Creer("TextButton", {
			Name = id,
			LayoutOrder = ordre,
			Size = UDim2.fromOffset(150, 49),
			BackgroundTransparency = 1,
			AutoButtonColor = false,
			Text = "",
			Parent = barreRapide,
		})
		local anneauLieu = Ui.Creer("Frame", {
			Name = "Anneau",
			Position = UDim2.fromOffset(-3, -3),
			Size = UDim2.fromOffset(156, 52),
			BackgroundColor3 = Color3.new(1, 1, 1),
			Visible = false,
			Parent = bouton,
		}, { Ui.Coins(14) })
		anneauxBarre[id] = anneauLieu
		local ombre = Ui.Creer("Frame", {
			Name = "Ombre",
			Position = UDim2.fromOffset(0, 3),
			Size = UDim2.fromOffset(150, 46),
			BackgroundColor3 = Ui.C.Trait,
			Parent = bouton,
		}, { Ui.Coins(11) })
		local face = Ui.Creer("Frame", {
			Name = "Face",
			Size = UDim2.fromOffset(150, 46),
			BackgroundColor3 = Color3.new(1, 1, 1),
			Parent = bouton,
		}, {
			Ui.Coins(11),
			Ui.Trait(2),
			Ui.Degrade(lieu.Teinte, 70, 0.22, 0.46),
		})
		Ui.Lisere(face, 2, 11, Color3.new(1, 1, 1), 0.4, 1.5)
		local contenu = Ui.Creer("Frame", {
			Size = UDim2.fromScale(1, 1),
			BackgroundTransparency = 1,
			Parent = face,
		}, {
			Ui.Marges(0, 12, 0, 8),
			Ui.Liste(Enum.FillDirection.Horizontal, 8, { VerticalAlignment = Enum.VerticalAlignment.Center }),
		})
		Ui.Icone(lieu.Icone, 30, { LayoutOrder = 1, Parent = contenu })
		Ui.Texte({
			LayoutOrder = 2,
			AutomaticSize = Enum.AutomaticSize.X,
			Size = UDim2.fromOffset(0, 46),
			TextSize = 17,
			Text = lieu.Court,
			Contour = true,
			Parent = contenu,
		})
		Ui.Reagir(bouton, face, ombre, 1.06)
		bouton.Activated:Connect(function()
			Teleportation.Aller(id)
		end)
	end

	-- Mes stats : petit bouton carré à droite de Ma base (panneau des stats : idée 2b, plus tard)
	local stats = Ui.BoutonIcone({
		Name = "stats",
		LayoutOrder = #UiConfig.BarreRapide + 1,
		Icone = "stats",
		Teinte = UiConfig.CouleursFonctions.stats,
		Taille = 46,
		Rayon = 12,
		TailleIcone = 32,
		Parent = barreRapide,
	})
	stats.Size = UDim2.fromOffset(46, 49)
	stats.Activated:Connect(function()
		Hud.Activer("stats")
	end)
end

function Teleportation.Init(racine: Frame, notifierToast: (string, string?) -> ())
	racineUi = racine
	notifier = notifierToast
	fenetre = Ui.Fenetre({
		Nom = "Teleportation",
		Titre = "Téléportation",
		SousTitre = "Clique un lieu sur la carte ou dans la liste",
		Icone = "teleport",
		Ruban = RUBAN,
		Taille = Vector2.new(790, 514),
	})
	construireBarreRapide(racine)
	-- la carte dépend de la base attribuée : construite à la première ouverture
	local construite = false
	fenetre.AuChangement(function(ouverte)
		if ouverte and not construite then
			construite = true
			construireCarte(fenetre.Contenu)
			construireListe(fenetre.Contenu)
		end
		if not ouverte and infobulle then
			survoler(nil, false)
		end
	end)

	-- On quitte le lieu actuel dès qu'on s'en éloigne (anneau de la barre rapide)
	task.spawn(function()
		while true do
			task.wait(0.5)
			local character = joueur.Character
			local racinePerso = character and character:FindFirstChild("HumanoidRootPart")
			-- au lancement on est dans sa base : point de départ = première position connue
			if lieuActuel and not pointArrivee and racinePerso and racinePerso:IsA("BasePart") then
				pointArrivee = racinePerso.Position
			end
			if lieuActuel and pointArrivee and racinePerso and racinePerso:IsA("BasePart") then
				if (racinePerso.Position - pointArrivee).Magnitude > DISTANCE_QUITTE then
					lieuActuel = nil
					pointArrivee = nil
					majBarreRapide()
				end
			end
		end
	end)
	majBarreRapide()
end

function Teleportation.Basculer()
	fenetre.Basculer()
end

return Teleportation
