--!strict
-- Cicatrice de poitrine de zoro en géométrie (aucune image envoyée à Roblox) : bourrelet en diagonale de l'épaule
-- gauche du perso à la hanche droite, en deux couches (bord plus sombre, cœur plus clair), avec points de suture.
-- Lancé par MCP (execute_luau, mode Edit), relançable : remplace le Model `Cicatrice` de chaque cible.
-- Pièces soudées à UpperTorso (Weld), sans collision ni masse : elles suivent les animations.

local CIBLES = { "ReplicatedStorage.ModelesPersonnages.zoro", "Workspace.Essais_Zoro.Zoro_v2" }

-- repère de UpperTorso : +X = droite du perso, +Y = haut, -Z = devant (face avant à z = -0,502)
local DEBUT = Vector2.new(-0.72, 0.66) -- épaule gauche
local FIN = Vector2.new(0.74, -0.84) -- hanche droite (le bas passe sous le haramaki)
local Z_SURFACE = -0.502
local SEGMENTS = 9
local LARGEUR_BORD = { 0.05, 0.13 } -- aux extrémités, au milieu
local LARGEUR_COEUR = { 0.025, 0.075 }
local POINTS = 6 -- points de suture

-- ombrage doux, pas de noir (cf. style des vêtements)
local COULEUR_BORD = Color3.fromRGB(170, 100, 84)
local COULEUR_COEUR = Color3.fromRGB(214, 140, 122)
local COULEUR_POINT = Color3.fromRGB(128, 70, 60)

local function chemin(texte: string): Instance?
	local courant: Instance? = game
	for nom in string.gmatch(texte, "[^%.]+") do
		if courant == nil then
			return nil
		end
		courant = if courant == game then game:GetService(nom) else courant:FindFirstChild(nom)
	end
	return courant
end

local function piece(parent: Instance, torse: BasePart, nom: string, taille: Vector3, cf: CFrame, couleur: Color3)
	local p = Instance.new("Part")
	p.Name = nom
	p.Size = taille
	p.Color = couleur
	p.Material = Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Massless = true
	p.Anchored = torse.Anchored
	p.CFrame = torse.CFrame * cf
	local w = Instance.new("Weld")
	w.Part0 = torse
	w.Part1 = p
	w.C0 = cf
	w.Parent = p
	p.Parent = parent
end

local function largeur(bornes: { number }, t: number): number
	return bornes[1] + (bornes[2] - bornes[1]) * math.sin(math.pi * t)
end

local rapport = {}
for _, texte in CIBLES do
	local modele = chemin(texte)
	local torse = modele and modele:FindFirstChild("UpperTorso")
	if not (modele and torse and torse:IsA("BasePart")) then
		table.insert(rapport, texte .. " : introuvable")
		continue
	end
	local ancien = modele:FindFirstChild("Cicatrice")
	if ancien then
		ancien:Destroy()
	end
	local dossier = Instance.new("Model")
	dossier.Name = "Cicatrice"

	local d = FIN - DEBUT
	local angle = math.atan2(d.Y, d.X)
	local rot = CFrame.Angles(0, 0, angle)
	local pas = d.Magnitude / SEGMENTS
	for i = 0, SEGMENTS - 1 do
		local t = (i + 0.5) / SEGMENTS
		local c = DEBUT + d * t
		local base = CFrame.new(c.X, c.Y, Z_SURFACE) * rot
		-- segments légèrement plus longs que le pas pour ne pas laisser de trou
		piece(
			dossier,
			torse,
			"Bord" .. i,
			Vector3.new(pas * 1.15, largeur(LARGEUR_BORD, t), 0.03),
			base * CFrame.new(0, 0, -0.01),
			COULEUR_BORD
		)
		piece(
			dossier,
			torse,
			"Coeur" .. i,
			Vector3.new(pas * 1.15, largeur(LARGEUR_COEUR, t), 0.03),
			base * CFrame.new(0, 0.008, -0.022),
			COULEUR_COEUR
		)
	end
	for i = 1, POINTS do
		local t = i / (POINTS + 1)
		local c = DEBUT + d * t
		local base = CFrame.new(c.X, c.Y, Z_SURFACE) * rot
		piece(
			dossier,
			torse,
			"Point" .. i,
			Vector3.new(0.035, largeur(LARGEUR_BORD, t) + 0.09, 0.03),
			base * CFrame.new(0, 0, -0.03),
			COULEUR_POINT
		)
	end

	dossier.Parent = modele
	table.insert(rapport, texte .. " : " .. #dossier:GetChildren() .. " pièces")
end
return table.concat(rapport, "\n")
