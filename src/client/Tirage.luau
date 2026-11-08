--!strict
-- Tirage : révélation plein écran (maquette « Tirage animé » du handoff, tirage-anim.jsx).
-- 1. Apparition : un rig R6 tout noir tourne sous un projecteur.
-- 2. Montée : la rareté grimpe palier par palier jusqu'à celle obtenue (onde, couleur du liseré, titre, jauge, secousse).
-- 3. Impact : deux cases manga noir / blanc avec le rig, flash blanc.
-- 4. Révélation : le perso remplace le rig (silhouette puis couleurs), rayons, titre de rareté, ruban du nom, étoiles.
-- 5. Pose : revenu, destination, bouton « Super ! », fondu.
-- Le résultat est tiré par le serveur avant l'animation. Sa durée (GachaConfig.Minutage) est le temps de recharge
-- de la machine, appliqué par le serveur : pas de bouton pour passer (offre payante prévue plus tard).

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Economie = require(ReplicatedStorage.Shared.Economie)
local GachaConfig = require(ReplicatedStorage.Shared.GachaConfig)
local Personnages = require(ReplicatedStorage.Shared.Personnages)
local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Cartes = require(script.Parent.Cartes)
local Images = require(script.Parent.Images)
local Ui = require(script.Parent.Ui)
local Vue3D = require(script.Parent.Vue3D)

local Tirage = {}

local NOIR_RIG = Color3.fromRGB(34, 30, 52)
local FOND = Color3.fromHex("#040308")

-- Easing (mêmes courbes que la maquette)
local function clamp01(x: number): number
	return math.clamp(x, 0, 1)
end
local function easeOutCubic(x: number): number
	return 1 - (1 - x) ^ 3
end
local function easeOutBack(x: number): number
	local c1, c3 = 1.70158, 2.70158
	return 1 + c3 * (x - 1) ^ 3 + c1 * (x - 1) ^ 2
end
local function easeInOutQuart(x: number): number
	return if x < 0.5 then 8 * x ^ 4 else 1 - (-2 * x + 2) ^ 4 / 2
end
local function anim(de: number, a: number, debut: number, fin: number, ease: (number) -> number, t: number): number
	local k = clamp01((t - debut) / math.max(fin - debut, 1e-3))
	return de + (a - de) * ease(k)
end

local racineUi: Frame
local generation = 0

type Palier = { Rarete: string, T: number }

-- Minutage d'un tirage : Commun en version courte, un palier par rareté jusqu'à celle obtenue.
local function minutage(rarete: string)
	local m = GachaConfig.Minutage(rarete)
	-- paliers répartis sur la montée, un par rareté jusqu'à celle obtenue
	local paliers: { Palier } = {}
	local debut, duree = m.Montee + 0.2, m.Impact - m.Montee - 0.5
	for i = 1, m.Rang do
		local t = if m.Rang == 1 then debut + duree * 0.3 else debut + (i - 1) * duree / (m.Rang - 1)
		table.insert(paliers, { Rarete = GachaConfig.Raretes[i].Id, T = t })
	end
	return {
		Montee = m.Montee,
		Impact = m.Impact,
		Revelation = m.Revelation,
		Pose = m.Pose,
		Total = m.Total,
		Paliers = paliers,
	}
end

local function texteChoc(
	props: { [string]: any },
	couleurOmbre: Color3,
	decalage: Vector2
): (Frame, TextLabel, TextLabel)
	-- titre blanc à gros contour avec une ombre de couleur décalée
	local cadre = Ui.Creer("Frame", {
		AutomaticSize = Enum.AutomaticSize.X,
		BackgroundTransparency = 1,
		Size = UDim2.fromOffset(0, props.TextSize + 10),
	})
	for cle, valeur in props do
		if cle == "Position" or cle == "AnchorPoint" or cle == "Rotation" or cle == "ZIndex" or cle == "Parent" then
			(cadre :: any)[cle] = valeur
		end
	end
	local function label(couleur: Color3, position: Vector2, z: number): TextLabel
		local l = Ui.Texte({
			AutomaticSize = Enum.AutomaticSize.X,
			Position = UDim2.fromOffset(position.X, position.Y),
			Size = UDim2.fromOffset(0, props.TextSize + 10),
			TextSize = props.TextSize,
			TextColor3 = couleur,
			Text = props.Text,
			ZIndex = (props.ZIndex or 1) + z,
			Parent = cadre,
		})
		Ui.Creer("UIStroke", {
			Color = Ui.C.Trait,
			Thickness = 4,
			ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual,
			Parent = l,
		})
		return l
	end
	local ombre = label(couleurOmbre, decalage, 0)
	local texte = label(Color3.new(1, 1, 1), Vector2.zero, 1)
	return cadre, texte, ombre
end

-- Lignes de vitesse (couleur `couleur`) autour du centre d'un cadre
local function lignesVitesse(parent: GuiObject, couleur: Color3, zIndex: number): Frame
	local cadre = Ui.Creer("Frame", {
		Name = "Lignes",
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(0, 0),
		BackgroundTransparency = 1,
		ZIndex = zIndex,
		Parent = parent,
	})
	local graine = Random.new(3)
	for i = 0, 59 do
		local pivot = Ui.Creer("Frame", {
			Rotation = i * 6 + graine:NextNumber(-2, 2),
			Size = UDim2.fromOffset(0, 0),
			BackgroundTransparency = 1,
			ZIndex = zIndex,
			Parent = cadre,
		})
		Ui.Creer("Frame", {
			AnchorPoint = Vector2.new(0, 0.5),
			Position = UDim2.fromOffset(graine:NextNumber(170, 280), 0),
			Size = UDim2.fromOffset(1100, if i % 3 == 0 then 8 else 3),
			BackgroundColor3 = couleur,
			BorderSizePixel = 0,
			ZIndex = zIndex,
			Parent = pivot,
		})
	end
	return cadre
end

function Tirage.Init(racine: Frame)
	racineUi = racine
end

function Tirage.Montrer(resultat: Remotes.ResultatTirage)
	local definition = typeof(resultat) == "table" and Personnages.ParId[resultat.Id]
	if not definition then
		return
	end
	generation += 1
	local tirage = generation
	local ancien = racineUi:FindFirstChild("Tirage")
	if ancien then
		ancien:Destroy()
	end
	Ui.FermerFenetre()

	local rarete = definition.Rarete
	local R = Ui.Rarete(rarete)
	local C = minutage(rarete)
	local definitionRarete = GachaConfig.RaretesParId[rarete]
	local nomRarete = Ui.Majuscules(if definitionRarete then definitionRarete.Nom else rarete)

	-- Plein écran : fond, puis scène 1100 × 650 centrée (coordonnées de la maquette)
	local ecran = Ui.Creer("TextButton", {
		Name = "Tirage",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = FOND,
		AutoButtonColor = false,
		Text = "",
		ZIndex = 50,
		ClipsDescendants = true,
		Parent = racineUi,
	})
	local fondCouleur = Ui.Creer("Frame", {
		Name = "FondCouleur",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Color3.new(1, 1, 1),
		BackgroundTransparency = 1,
		ZIndex = 50,
		Parent = ecran,
	}, {
		Ui.Creer("UIGradient", {
			Rotation = 90,
			Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 1),
				NumberSequenceKeypoint.new(0.62, 0),
				NumberSequenceKeypoint.new(1, 0.6),
			}),
		}),
	})
	local scene = Ui.Creer("Frame", {
		Name = "Scene",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(1100, 650),
		BackgroundTransparency = 1,
		ZIndex = 51,
		Parent = ecran,
	})
	local function frame(props: { [string]: any }, enfants: { Instance }?): Frame
		local defauts: { [string]: any } = { BackgroundTransparency = 1, BorderSizePixel = 0, Parent = scene }
		for cle, valeur in props do
			defauts[cle] = valeur
		end
		return Ui.Creer("Frame", defauts, enfants)
	end

	-- Rayons de la révélation (2 couronnes)
	local rayons = frame({ Name = "RayonsRevelation", Position = UDim2.fromOffset(550, 290), ZIndex = 52 })
	local rayonsLarges = Cartes.Rayons(rayons, UDim2.new(), 16, 400, 60, R.Clair, 0.55, 52)
	local rayonsFins = Cartes.Rayons(rayons, UDim2.new(), 24, 280, 14, Color3.new(1, 1, 1), 0.6, 52)
	local echelleRayons = Ui.Creer("UIScale", { Scale = 0.4, Parent = rayons })

	-- Halo de la couleur du palier
	local halo = frame({ Name = "Halo", Position = UDim2.fromOffset(550, 400), ZIndex = 52 })
	local disquesHalo = Cartes.Lueur(halo, UDim2.new(), 560, Color3.new(1, 1, 1), 1, 52)

	-- Projecteur : faisceau vertical qui s'efface vers le bas, ellipse au sol
	local faisceaux: { Frame } = {}
	for i, largeur in { 110, 190, 270 } do
		faisceaux[i] = frame({
			Name = "Faisceau",
			AnchorPoint = Vector2.new(0.5, 0),
			Position = UDim2.fromOffset(550, -40),
			Size = UDim2.fromOffset(largeur, 620),
			BackgroundColor3 = Color3.new(1, 1, 1),
			BackgroundTransparency = 1,
			ZIndex = 53,
		}, {
			Ui.Creer("UIGradient", {
				Rotation = 90,
				Transparency = NumberSequence.new({
					NumberSequenceKeypoint.new(0, 0.2),
					NumberSequenceKeypoint.new(0.75, 0.75),
					NumberSequenceKeypoint.new(1, 1),
				}),
			}),
		})
	end
	local solProjecteur = frame({
		Name = "Sol",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromOffset(550, 535),
		Size = UDim2.fromOffset(320, 70),
		BackgroundColor3 = Color3.new(1, 1, 1),
		BackgroundTransparency = 0.6,
		ZIndex = 53,
	}, { Ui.Rond() })

	-- Particules qui montent
	local particules: { Frame } = {}
	for i = 0, 29 do
		local taille = 2 + i % 4
		table.insert(
			particules,
			frame({
				Name = "Particule",
				Size = UDim2.fromOffset(taille, taille),
				BackgroundColor3 = Color3.new(1, 1, 1),
				BackgroundTransparency = 1,
				ZIndex = 54,
			}, { Ui.Rond() })
		)
	end

	-- Ondes de choc (une par palier)
	local ondes: { Frame } = {}
	for _, palier in C.Paliers do
		local onde = frame({
			Name = "Onde",
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromOffset(550, 400),
			Size = UDim2.fromOffset(120, 120),
			Visible = false,
			ZIndex = 55,
		}, { Ui.Rond() })
		Ui.Contour(Ui.Rarete(palier.Rarete).Clair, 6).Parent = onde
		table.insert(ondes, onde)
	end

	-- Rig R6 noir dans un ViewportFrame 360 × 400 (lumière de la couleur du palier, par le haut)
	local cadreRig = frame({
		Name = "Rig",
		AnchorPoint = Vector2.new(0.5, 0.93),
		Position = UDim2.fromOffset(550, 150 + 400 * 0.93),
		Size = UDim2.fromOffset(360, 400),
		ZIndex = 56,
	})
	local echelleRig = Ui.Creer("UIScale", { Parent = cadreRig })
	local ombreRig = frame({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromOffset(180, 344),
		Size = UDim2.fromOffset(180, 30),
		BackgroundColor3 = Color3.new(0, 0, 0),
		BackgroundTransparency = 0.4,
		ZIndex = 56,
		Parent = cadreRig,
	}, { Ui.Rond() })
	local vueRig = Vue3D.Creer({
		Name = "Vue",
		Size = UDim2.fromScale(1, 1),
		Ambient = Color3.fromRGB(30, 26, 48),
		LightColor = Color3.new(1, 1, 1),
		LightDirection = Vector3.new(0.35, -1, -0.25), -- par le haut, un peu de face : liseré sur le dessus
		ZIndex = 57,
		Parent = cadreRig,
	})
	local rig = Vue3D.RigR6(NOIR_RIG)
	rig.Modele.Parent = vueRig.Monde
	vueRig.Camera.FieldOfView = 30
	vueRig.Camera.CFrame = CFrame.lookAt(Vector3.new(0, 3.6, 15.5), Vector3.new(0, 2.6, 0))

	-- Titre du palier, jauge
	local titrePalier, textePalier, ombrePalier = texteChoc({
		Text = "",
		TextSize = 58,
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromOffset(550, 116),
		Rotation = -5,
		ZIndex = 58,
		Parent = scene,
	}, R.Base, Vector2.new(7, 9))
	local echellePalier = Ui.Creer("UIScale", { Parent = titrePalier })
	local jauge = frame({
		Name = "Jauge",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.fromOffset(550, 552),
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 14),
		ZIndex = 58,
	}, { Ui.Liste(Enum.FillDirection.Horizontal, 10) })
	local segments: { Frame } = {}
	for i, r in GachaConfig.Raretes do
		segments[i] = frame({
			Name = r.Id,
			LayoutOrder = i,
			Size = UDim2.fromOffset(52, 12),
			BackgroundColor3 = Ui.C.Zone,
			BackgroundTransparency = 0,
			ZIndex = 58,
			Parent = jauge,
		}, { Ui.Coins(3), Ui.Contour(Ui.C.LisereSombre, 1.5) })
	end

	-- Héros : render plein pied, sinon modèle 3D, sinon bloc coloré
	local heros = frame({
		Name = "Heros",
		AnchorPoint = Vector2.new(0.5, 0.92),
		Position = UDim2.fromOffset(550, 50 + 540 * 0.92),
		Size = UDim2.fromOffset(480, 540),
		ZIndex = 60,
	})
	local echelleHeros = Ui.Creer("UIScale", { Parent = heros })
	local lueurHeros, transparenceLueur = Cartes.Lueur(heros, UDim2.fromOffset(240, 250), 400, R.Clair, 0.9, 60)
	frame({
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, 0, 1, -70),
		Size = UDim2.fromOffset(300, 40),
		BackgroundColor3 = FOND,
		BackgroundTransparency = 0.4,
		ZIndex = 60,
		Parent = heros,
	}, { Ui.Rond() })
	local images = Images.De(definition.Id)
	local visuelHeros: GuiObject
	if images then
		visuelHeros = Ui.Creer("ImageLabel", {
			Name = "Render",
			Size = UDim2.fromScale(1, 1),
			BackgroundTransparency = 1,
			Image = images.Pied,
			ImageColor3 = Color3.new(0, 0, 0),
			ScaleType = Enum.ScaleType.Fit,
			ZIndex = 61,
			Parent = heros,
		})
	else
		local vueHeros = Vue3D.Creer({
			Name = "Modele",
			Size = UDim2.fromScale(1, 1),
			ImageColor3 = Color3.new(0, 0, 0),
			ZIndex = 61,
			Parent = heros,
		})
		visuelHeros = vueHeros.Cadre
		if not Vue3D.Montrer(vueHeros, definition.Id) then
			vueHeros.Cadre:Destroy()
			local bloc = Ui.Creer("Frame", {
				Name = "Bloc",
				AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromScale(0.5, 0.5),
				Size = UDim2.fromOffset(220, 260),
				BackgroundColor3 = Color3.new(0, 0, 0),
				ZIndex = 61,
				Parent = heros,
			}, { Ui.Coins(24), Ui.Trait(3) })
			Ui.Texte({
				Size = UDim2.fromScale(1, 1),
				TextSize = 150,
				TextXAlignment = Enum.TextXAlignment.Center,
				Text = string.sub(definition.Nom, 1, 1),
				Contour = 3,
				ZIndex = 62,
				Parent = bloc,
			})
			visuelHeros = bloc
		end
	end
	local function teinterHeros(k: number) -- 0 = silhouette noire, 1 = couleurs
		local couleur = Color3.new(0, 0, 0):Lerp(Color3.new(1, 1, 1), k)
		if visuelHeros:IsA("ImageLabel") or visuelHeros:IsA("ViewportFrame") then
			(visuelHeros :: any).ImageColor3 = couleur
		else
			visuelHeros.BackgroundColor3 = Color3.new(0, 0, 0):Lerp(R.Base, k)
		end
	end

	-- Titres de la révélation : « MYTHIQUE ! », ruban du nom, étoiles
	local titreRarete, _, _ = texteChoc({
		Text = `{nomRarete} !`,
		TextSize = 64,
		Position = UDim2.fromOffset(56, 54),
		Rotation = -6,
		ZIndex = 64,
		Parent = scene,
	}, R.Base, Vector2.new(8, 10))
	titreRarete.Visible = false
	local echelleTitre = Ui.Creer("UIScale", { Parent = titreRarete })
	local ruban = frame({
		Name = "Ruban",
		Position = UDim2.fromOffset(-1100, 452),
		Size = UDim2.fromOffset(1020, 92), -- 400 px de plus à gauche que la maquette : touche le bord des écrans larges
		Rotation = -4,
		BackgroundColor3 = Color3.new(1, 1, 1),
		BackgroundTransparency = 0,
		ZIndex = 64,
	}, {
		Ui.Creer("UIGradient", {
			Color = ColorSequence.new({
				ColorSequenceKeypoint.new(0, R.Fonce),
				ColorSequenceKeypoint.new(0.39, R.Fonce),
				ColorSequenceKeypoint.new(0.76, R.Base),
				ColorSequenceKeypoint.new(1, R.Base),
			}),
			Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 0),
				NumberSequenceKeypoint.new(0.76, 0),
				NumberSequenceKeypoint.new(1, 1),
			}),
		}),
	})
	for _, y in { 6, 84 } do
		Ui.Filet({ Position = UDim2.fromOffset(0, y), Size = UDim2.new(1, 0, 0, 2), ZIndex = 65, Parent = ruban })
	end
	local nomHeros = Ui.Texte({
		Name = "Nom",
		Position = UDim2.fromOffset(464, 8),
		Size = UDim2.fromOffset(540, 76),
		TextSize = 62,
		TextTransparency = 1,
		Text = definition.Nom,
		ZIndex = 66,
		Parent = ruban,
	})
	local contourNom = Ui.Creer("UIStroke", {
		Color = Ui.C.Trait,
		Thickness = 3,
		Transparency = 1,
		ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual,
		Parent = nomHeros,
	})
	local rangeeEtoiles = frame({
		Name = "Etoiles",
		Position = UDim2.fromOffset(74, 560),
		Size = UDim2.fromOffset(300, 46),
		Rotation = -4,
		ZIndex = 64,
	}, { Ui.Liste(Enum.FillDirection.Horizontal, 8) })
	local etoiles: { GuiObject } = {}
	local echellesEtoiles: { UIScale } = {}
	for i = 1, Economie.EtoilesMax do
		local pleine = i <= resultat.Etoiles
		local etoile = Ui.Icone(if pleine then "etoile" else "etoile_vide", 46, {
			LayoutOrder = i,
			TextColor3 = if pleine then Color3.fromHex("#FFC93C") else Ui.C.TexteEteint,
			Visible = false,
			ZIndex = 65,
			Parent = rangeeEtoiles,
		})
		etoiles[i] = etoile
		echellesEtoiles[i] = Ui.Creer("UIScale", { Parent = etoile })
	end

	-- Pose : revenu, destination, « Super ! »
	local infos = frame({
		Name = "Infos",
		AnchorPoint = Vector2.new(1, 1),
		Position = UDim2.fromOffset(1100 - 60, 650 - 46),
		AutomaticSize = Enum.AutomaticSize.XY,
		Visible = false,
		ZIndex = 66,
	}, {
		Ui.Liste(Enum.FillDirection.Horizontal, 12, { VerticalAlignment = Enum.VerticalAlignment.Center }),
	})
	local pilule = frame({
		LayoutOrder = 1,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 40),
		BackgroundColor3 = Ui.C.Trait,
		BackgroundTransparency = 0.15,
		ZIndex = 66,
		Parent = infos,
	}, {
		Ui.Coins(10),
		Ui.Contour(Ui.C.LisereSombre, 1.5),
		Ui.Marges(0, 14, 0, 8),
		Ui.Liste(Enum.FillDirection.Horizontal, 6, { VerticalAlignment = Enum.VerticalAlignment.Center }),
	})
	Ui.Icone("billets", 26, { LayoutOrder = 1, ZIndex = 67, Parent = pilule })
	Ui.Texte({
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 40),
		TextSize = 20,
		TextColor3 = Ui.C.Gain,
		Text = `+{Ui.FormaterRevenu(resultat.Revenu)} $/s`,
		ZIndex = 67,
		Parent = pilule,
	})
	Ui.Texte({
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 40),
		FontFace = Ui.Montserrat(Enum.FontWeight.Bold),
		TextSize = 14,
		Text = if resultat.Emplacement
			then `→ Emplacement {resultat.Emplacement}`
			else "→ Inventaire (emplacements pleins)",
		Contour = true,
		ZIndex = 67,
		Parent = infos,
	})
	local super = Ui.Bouton({
		LayoutOrder = 3,
		Taille = Vector2.new(150, 50),
		Style = "Vert",
		Texte = "Super !",
		TailleTexte = 22,
		ZIndex = 67,
		Parent = infos,
	})
	for _, descendant in super:GetDescendants() do
		if descendant:IsA("GuiObject") then
			descendant.ZIndex = 67
		end
	end

	-- Cases manga de l'impact (rig blanc sur fond noir, puis rig noir sur fond blanc) et flash
	local case = Ui.Creer("Frame", {
		Name = "CaseManga",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Ui.C.Trait,
		Visible = false,
		ZIndex = 80,
		Parent = ecran,
	})
	local lignesBlanches = lignesVitesse(case, Color3.new(1, 1, 1), 80)
	local lignesNoires = lignesVitesse(case, Ui.C.Trait, 80)
	local flash = Ui.Creer("Frame", {
		Name = "Flash",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = Color3.new(1, 1, 1),
		BackgroundTransparency = 1,
		ZIndex = 85,
		Parent = ecran,
	})

	-- Boucle d'animation
	local debut = os.clock()
	local connexion: RBXScriptConnection
	local function fermer()
		if connexion then
			connexion:Disconnect()
		end
		if ecran.Parent then
			ecran:Destroy()
		end
	end
	super.Activated:Connect(fermer)

	local function palierActuel(t: number): number
		local k = 0
		for i, palier in C.Paliers do
			if t >= palier.T then
				k = i
			end
		end
		return k
	end

	connexion = RunService.RenderStepped:Connect(function()
		if tirage ~= generation or not ecran.Parent then
			connexion:Disconnect()
			return
		end
		local T = os.clock() - debut
		if T >= C.Total then
			fermer()
			return
		end
		local sortie = anim(1, 0, C.Total - 0.8, C.Total, easeInOutQuart, T)
		local idx = palierActuel(T)
		local cur = if idx > 0 then Ui.Rarete(C.Paliers[idx].Rarete) else nil
		local avantImpact = T < C.Impact

		-- Secousse : à chaque palier (plus forte à chaque fois), puis à l'impact
		local secousse = 0
		for i, palier in C.Paliers do
			local d = T - palier.T
			if d >= 0 and d < 0.3 then
				secousse = math.sin(d * 120) * (3 + (i - 1) * 2.5) * (1 - d / 0.3)
			end
		end
		if T > C.Impact + 0.3 and T < C.Impact + 0.9 then
			secousse = math.sin(T * 90) * 10 * (1 - (T - C.Impact - 0.3) / 0.6)
		end
		scene.Position = UDim2.new(0.5, secousse, 0.5, secousse * 0.5)

		-- Fond : teinte du palier pendant la montée, de la rareté obtenue à la révélation
		local teintePalier = if cur then anim(0.25, 0.55, C.Montee, C.Impact, easeOutCubic, T) else 0
		local revele = anim(0, 1, C.Impact + 0.2, C.Revelation + 0.6, easeOutCubic, T)
		local couleurFond = if avantImpact then (cur or R).Base else R.Base
		fondCouleur.BackgroundColor3 = couleurFond
		fondCouleur.BackgroundTransparency = 1 - (if avantImpact then teintePalier else revele * 0.75) * sortie

		-- Halo derrière le rig, faisceau et sol du projecteur
		local projecteur = anim(0, 1, 0.1, 1, easeOutCubic, T)
			* anim(1, 0, C.Impact, C.Impact + 0.3, easeInOutQuart, T)
			* (0.9 + math.sin(T * 23) * 0.05)
			* sortie
		local couleurLumiere = if cur then cur.Clair else Color3.new(1, 1, 1)
		for _, faisceau in faisceaux do
			faisceau.BackgroundColor3 = couleurLumiere
			faisceau.BackgroundTransparency = 1 - projecteur * 0.16
		end
		solProjecteur.BackgroundColor3 = couleurLumiere
		solProjecteur.BackgroundTransparency = 1 - projecteur * 0.22
		for _, disque in disquesHalo do
			disque.BackgroundColor3 = if cur then cur.Base else Color3.fromHex("#2A2448")
			disque.BackgroundTransparency = 1 - 0.07 * projecteur
		end

		-- Particules
		local boost = if T > C.Impact then 2.4 else 1 + clamp01((T - C.Montee) / 3)
		local couleurParticules = if avantImpact then (if cur then cur.Clair else Ui.C.TexteDiscretClair) else R.Clair
		local visibles = anim(0, 1, 0, 1.2, easeOutCubic, T) * sortie
		for i, particule in particules do
			local n = i - 1
			local vitesse = 40 + (n * 53) % 60
			local y = 650 - ((T * vitesse * boost + n * 83) % 700)
			local x = 120 + (n * 397) % 860 + math.sin(T * 1.3 + n) * 14
			particule.Position = UDim2.fromOffset(x, y)
			particule.BackgroundColor3 = couleurParticules
			particule.BackgroundTransparency = 1 - visibles * (0.35 + (n % 3) * 0.2)
		end

		-- Ondes de choc
		for i, palier in C.Paliers do
			local k = clamp01((T - palier.T) / 0.7)
			local onde = ondes[i]
			onde.Visible = T >= palier.T and k < 1
			if onde.Visible then
				local echelle = 0.6 + easeOutCubic(k) * 4.2
				onde.Size = UDim2.fromOffset(120 * echelle, 120 * echelle)
				local contour = onde:FindFirstChildOfClass("UIStroke") :: UIStroke
				contour.Thickness = 6 - k * 4
				contour.Transparency = k
			end
		end

		-- Rig : apparition, rotation (un quart de tour par palier), balancement, coup à chaque palier
		local apparition = anim(0, 1, 0.2, 1.4, easeOutCubic, T)
		local disparu = anim(1, 0, C.Impact + 0.25, C.Impact + 0.45, easeInOutQuart, T)
		cadreRig.Visible = apparition * disparu > 0.01
		if cadreRig.Visible then
			local coup, tour = 0, 0
			for _, palier in C.Paliers do
				local d = T - palier.T
				if d >= 0 and d < 0.35 then
					coup = math.max(coup, math.sin(d / 0.35 * math.pi) * (1 - d / 0.35))
				end
				tour += 90 * easeOutCubic(clamp01(d / 0.55))
			end
			local charge = clamp01((T - C.Montee) / (C.Impact - C.Montee))
			local tremble = if T > C.Montee and avantImpact then math.sin(T * 64) * charge * charge * 2.5 else 0
			local lacet = math.rad(-30 + T * 22 + tour)
			local balance = math.rad(6 + math.sin(T * 2.4) * 8 + coup * 22)
			local torse = CFrame.new(0, 3, 0) * CFrame.Angles(0, lacet, 0)
			local parties = rig.Parties
			parties.Torse.CFrame = torse
			parties.Tete.CFrame = torse * CFrame.new(0, 1.5, 0) * CFrame.Angles(0, 0, math.rad(math.sin(T * 1.8) * 4))
			local function membre(nom: string, epaule: Vector3, angle: number)
				parties[nom].CFrame = torse * CFrame.new(epaule) * CFrame.Angles(angle, 0, 0) * CFrame.new(0, -1, 0)
			end
			membre("BrasG", Vector3.new(-1.5, 1, 0), balance)
			membre("BrasD", Vector3.new(1.5, 1, 0), -balance)
			membre("JambeG", Vector3.new(-0.5, -1, 0), -balance * 0.6)
			membre("JambeD", Vector3.new(0.5, -1, 0), balance * 0.6)

			local blanchi = anim(0, 1, C.Impact - 0.3, C.Impact + 0.05, easeOutCubic, T)
			local couleur = NOIR_RIG:Lerp(Color3.new(1, 1, 1), blanchi)
			for _, partie in parties do
				partie.Color = couleur
			end
			vueRig.Cadre.LightColor = if cur then cur.Clair else Color3.fromHex("#4A3F86")
			vueRig.Cadre.ImageTransparency = 1 - apparition * disparu
			echelleRig.Scale = (1 + coup * 0.08 + charge * 0.06) * anim(0.85, 1, 0.2, 1.4, easeOutBack, T)
			cadreRig.Rotation = tremble
			cadreRig.Position = UDim2.fromOffset(550, 150 + 400 * 0.93 + anim(40, 0, 0.2, 1.4, easeOutCubic, T))
			ombreRig.BackgroundTransparency = 1 - 0.6 * apparition * disparu
		end

		-- Titre du palier et jauge
		local horsTitre = anim(1, 0, C.Impact - 0.1, C.Impact + 0.1, easeInOutQuart, T)
		titrePalier.Visible = idx > 0 and horsTitre > 0.01
		if titrePalier.Visible then
			local palier = C.Paliers[idx]
			local k = clamp01((T - palier.T) / 0.32)
			local definitionPalier = GachaConfig.RaretesParId[palier.Rarete]
			local nom = Ui.Majuscules(if definitionPalier then definitionPalier.Nom else palier.Rarete)
			textePalier.Text = nom .. (if idx > 1 then " !" else "")
			ombrePalier.Text = textePalier.Text
			ombrePalier.TextColor3 = Ui.Rarete(palier.Rarete).Base
			echellePalier.Scale = 1 + (1 - easeOutBack(k)) * 1.2
			local opacite = clamp01(k * 3) * horsTitre
			textePalier.TextTransparency = 1 - opacite
			ombrePalier.TextTransparency = 1 - opacite
		end
		local jaugeVisible = anim(0, 1, C.Montee - 0.1, C.Montee + 0.3, easeOutCubic, T)
			* anim(1, 0, C.Impact - 0.1, C.Impact + 0.15, easeInOutQuart, T)
		jauge.Visible = jaugeVisible > 0.01
		for i, segment in segments do
			local allume = i <= idx
			local t = Ui.Rarete(GachaConfig.Raretes[i].Id)
			segment.BackgroundColor3 = if allume then t.Base else Ui.C.Zone
			segment.BackgroundTransparency = 1 - jaugeVisible
			local contour = segment:FindFirstChildOfClass("UIStroke") :: UIStroke
			contour.Color = if allume then Ui.C.Trait else Ui.C.LisereSombre
			contour.Transparency = 1 - jaugeVisible
		end

		-- Impact : 2 cases manga puis flash blanc
		local t0 = C.Impact + 0.05
		if T >= t0 and T < t0 + 0.3 then
			local premiere = T < t0 + 0.14
			case.Visible = true
			cadreRig.Visible = true
			case.BackgroundColor3 = if premiere then Ui.C.Trait else Color3.new(1, 1, 1)
			lignesBlanches.Visible = premiere
			lignesNoires.Visible = not premiere
			lignesNoires.Rotation = 7
			-- le rig passe au-dessus de la case : blanc puis noir
			cadreRig.ZIndex = 81
			vueRig.Cadre.ZIndex = 82
			vueRig.Cadre.ImageTransparency = 0
			vueRig.Cadre.ImageColor3 = if premiere then Color3.new(1, 1, 1) else Color3.new(0, 0, 0)
			vueRig.Cadre.Ambient = Color3.new(1, 1, 1)
			echelleRig.Scale = if premiere then 1.15 else 1.22
			cadreRig.Rotation = if premiere then 0 else -3
			cadreRig.Parent = ecran
			cadreRig.Position = UDim2.new(0.5, 0, 0.5, 150 + 400 * 0.93 - 325)
		elseif case.Visible then
			case.Visible = false
			cadreRig.Visible = false
		end
		flash.BackgroundTransparency = if T >= t0 + 0.3 then 1 - anim(1, 0, t0 + 0.3, t0 + 0.9, easeOutCubic, T) else 1

		-- Rayons de la révélation
		local rayonsOn = clamp01(anim(0, 1, C.Impact + 0.3, C.Revelation + 0.4, easeOutBack, T)) * sortie
		rayons.Visible = rayonsOn > 0.01
		if rayons.Visible then
			echelleRayons.Scale = 0.4 + rayonsOn * 0.6
			rayonsLarges.Rotation = T * 18
			rayonsFins.Rotation = -T * 18 * 1.4
			for _, descendant in rayons:GetDescendants() do
				if descendant:IsA("Frame") and descendant.Size.X.Offset > 0 then
					descendant.BackgroundTransparency = 1 - rayonsOn * 0.4
				end
			end
		end

		-- Héros : monte (Back), silhouette qui disparaît, respiration, poussée caméra
		local s = C.Impact + 0.35
		local monte = anim(0, 1, s, s + 0.8, easeOutBack, T)
		local horsHeros = anim(1, 0, C.Total - 0.8, C.Total - 0.2, easeInOutQuart, T)
		heros.Visible = monte > 0.01
		if heros.Visible then
			local respiration = 1 + math.sin(T * 2) * 0.012
			local poussee = 1 + anim(0, 0.05, C.Pose, C.Total, easeOutCubic, T)
			echelleHeros.Scale = (0.7 + monte * 0.3) * respiration * poussee
			heros.Position = UDim2.fromOffset(550, 50 + 540 * 0.92 + (1 - monte) * 60)
			teinterHeros(anim(0, 1, s + 0.1, s + 0.7, easeOutCubic, T))
			local opacite = clamp01(monte) * horsHeros
			for _, disque in lueurHeros do
				disque.BackgroundTransparency = 1 - (1 - transparenceLueur) * opacite
			end
			if visuelHeros:IsA("ImageLabel") or visuelHeros:IsA("ViewportFrame") then
				(visuelHeros :: any).ImageTransparency = 1 - opacite
			end
		end

		-- Titre de rareté, ruban, nom, étoiles
		local r0 = C.Revelation + 0.2
		titreRarete.Visible = T >= r0 and horsHeros > 0.01
		if titreRarete.Visible then
			echelleTitre.Scale = anim(2.4, 1, r0, r0 + 0.35, easeOutBack, T)
		end
		ruban.Position = UDim2.fromOffset(anim(-1100, -400, r0 + 0.35, r0 + 0.85, easeOutCubic, T), 452)
		ruban.Visible = T >= r0 + 0.35 and horsHeros > 0.01
		local opaciteNom = clamp01(anim(0, 1, r0 + 0.55, r0 + 0.9, easeOutCubic, T))
		nomHeros.Position = UDim2.fromOffset(464 + anim(-40, 0, r0 + 0.55, r0 + 1, easeOutCubic, T), 8)
		nomHeros.TextTransparency = 1 - opaciteNom
		contourNom.Transparency = 1 - opaciteNom
		for i, etoile in etoiles do
			local pleine = i <= resultat.Etoiles
			local st = r0 + 1 + i * 0.22
			local k = if pleine
				then anim(0, 1, st, st + 0.3, easeOutBack, T)
				else clamp01(anim(0, 1, r0 + 0.9, r0 + 1.2, easeOutCubic, T))
			etoile.Visible = k > 0.01 and horsHeros > 0.01
			echellesEtoiles[i].Scale = if pleine then math.max(k, 0) else 1
			etoile.Rotation = if pleine then (1 - clamp01(k)) * -120 else 0
		end
		infos.Visible = T >= C.Pose and horsHeros > 0.01
	end)
end

return Tirage
