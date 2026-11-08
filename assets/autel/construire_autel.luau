--!strict
-- Construit l'autel d'invocation (remplace le cube RNG) dans chaque Model tagué "BaseJoueur".
-- D'après la spec « Autel - spec Claude Code » (fonction autel(L) de machines-lib.js). Lancé par MCP, relançable.
-- Les cotes de la spec sont gardées telles quelles et multipliées par ECHELLE (attribut Echelle du modèle, lu par le client).
-- +Z local = devant (marches, vers l'entrée de la base). Positions = centres.
-- La pièce invisible "RNG" (tag MachineRNG) reste le point d'accroche du tirage (GachaService).
-- Niveaux 2 à 10 : dossiers Niveaux.N2..N10, rendus visibles par le client (src/client/Autel.luau) selon l'attribut Level ;
-- couleur des objets tagués AutelRarete = rareté du dernier tirage, ou « éteint » avant le premier tirage.

local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")

local NOM = "AutelInvocation"
local ECHELLE = 1.5 -- validé par l'utilisateur le 08/11
local RECUL = 1 -- l'arrière de l'estrade à 1 stud devant le fond de l'ancien cube
local Y_SOL_ZONE = 1.8 -- dessus du sol de la zone « Sanctuaire » au-dessus du sol extérieur

local MAT = {
	Pierre_Ardoise = { Color3.fromHex("3B3F52"), Enum.Material.Slate, 0 },
	Pierre_Claire = { Color3.fromHex("5A5F78"), Enum.Material.Slate, 0 },
	Laque = { Color3.fromHex("C23B32"), Enum.Material.SmoothPlastic, 0.05 },
	Bois_Sombre = { Color3.fromHex("2B1D1A"), Enum.Material.Wood, 0 },
	Metal_Or = { Color3.fromHex("D9A441"), Enum.Material.Metal, 0.2 },
	Metal_Sombre = { Color3.fromHex("2A2C36"), Enum.Material.Metal, 0 },
	Carte_Face = { Color3.fromHex("1C1733"), Enum.Material.SmoothPlastic, 0 },
	Neon_Rarete = { Color3.fromHex("FFBE00"), Enum.Material.Neon, 0 },
	Neon_Ambre = { Color3.fromHex("FFE2B0"), Enum.Material.Neon, 0 },
	Neon_Blanc = { Color3.fromHex("FFF3DC"), Enum.Material.Neon, 0 },
	Aura = { Color3.fromHex("FFBE00"), Enum.Material.ForceField, 0 },
}
local COULEUR_RARETE = MAT.Neon_Rarete[1] :: Color3
local COULEUR_ETEINT = Color3.fromHex("6B7085") -- mêmes valeurs que src/client/Autel.luau
local COULEUR_LOSANGE_ETEINT = Color3.fromHex("9A9EAE")
local E = ECHELLE

local origine: CFrame -- CFrame du sol au centre de l'autel, +Z local vers l'entrée
local function mettre(p: BasePart, cf: CFrame, parent: Instance)
	p.CFrame = origine * (cf.Rotation + cf.Position * E)
	p.Parent = parent
end

local function piece(nom: string, mat: string, forme: Enum.PartType, taille: Vector3): Part
	local m = MAT[mat]
	local p = Instance.new("Part")
	p.Name = nom
	p.Shape = forme
	p.Size = taille * E
	p.Color = m[1] :: Color3
	p.Material = m[2] :: Enum.Material
	p.Reflectance = m[3] :: number
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	if mat == "Neon_Rarete" or mat == "Aura" then
		-- construit éteint (comme avant le premier tirage) ; le client rallume avec MateriauAllume
		CollectionService:AddTag(p, "AutelRarete")
		p:SetAttribute("MateriauAllume", (m[2] :: Enum.Material).Name)
		p.Color = COULEUR_ETEINT
		if mat ~= "Aura" then
			p.Material = Enum.Material.SmoothPlastic
		end
	end
	if mat:sub(1, 4) == "Neon" or mat == "Aura" then
		p.CastShadow = false
	end
	return p
end

-- Box : B(nom, mat, w, h, d, x, y, z, rx, ry, rz)
local function B(
	parent: Instance,
	nom: string,
	mat: string,
	w: number,
	h: number,
	d: number,
	x: number,
	y: number,
	z: number,
	rx: number?,
	ry: number?,
	rz: number?
): Part
	local p = piece(nom, mat, Enum.PartType.Block, Vector3.new(w, h, d))
	mettre(p, CFrame.new(x, y, z) * CFrame.fromEulerAnglesXYZ(rx or 0, ry or 0, rz or 0), parent)
	return p
end

-- Cylindre vertical (en Roblox l'axe du cylindre est X : on le couche de 90° autour de Z)
local function C(
	parent: Instance,
	nom: string,
	mat: string,
	r: number,
	h: number,
	x: number,
	y: number,
	z: number
): Part
	local p = piece(nom, mat, Enum.PartType.Cylinder, Vector3.new(h, 2 * r, 2 * r))
	mettre(p, CFrame.new(x, y, z) * CFrame.Angles(0, 0, math.rad(90)), parent)
	return p
end

local function S(parent: Instance, nom: string, mat: string, r: number, x: number, y: number, z: number): Part
	local p = piece(nom, mat, Enum.PartType.Ball, Vector3.one * 2 * r)
	mettre(p, CFrame.new(x, y, z), parent)
	return p
end

local function attache(parent: BasePart, nom: string, positionLocale: Vector3): Attachment
	local a = Instance.new("Attachment")
	a.Name = nom
	a.Parent = parent
	a.WorldPosition = (origine * CFrame.new(positionLocale * E)).Position
	return a
end

local function lumiere(
	parent: BasePart,
	positionLocale: Vector3,
	couleur: Color3,
	eclat: number,
	portee: number,
	rarete: boolean
): PointLight
	local l = Instance.new("PointLight")
	l.Color = couleur
	l.Brightness = eclat
	l.Range = portee * E
	l.Shadows = false
	l.Parent = attache(parent, "Lumiere", positionLocale)
	if rarete then
		CollectionService:AddTag(l, "AutelRarete")
		l.Enabled = false
	end
	return l
end

local function lanterne(parent: Instance, x: number, z: number, y0: number)
	local m = Instance.new("Model")
	m.Name = "Lanterne"
	B(m, "Lanterne_Socle", "Pierre_Claire", 1.4, 0.4, 1.4, x, y0 + 0.2, z)
	C(m, "Lanterne_Pied", "Pierre_Claire", 0.3, 1.6, x, y0 + 1.2, z)
	B(m, "Lanterne_Cadre", "Metal_Sombre", 1.25, 0.14, 1.25, x, y0 + 2.07, z)
	local feu = B(m, "Neon_Lanterne", "Neon_Ambre", 1, 1, 1, x, y0 + 2.6, z)
	B(m, "Lanterne_Toit", "Bois_Sombre", 1.9, 0.3, 1.9, x, y0 + 3.25, z)
	B(m, "Lanterne_Toit_Haut", "Bois_Sombre", 1, 0.3, 1, x, y0 + 3.55, z)
	S(m, "Lanterne_Pointe", "Metal_Or", 0.2, x, y0 + 3.85, z)
	lumiere(feu, Vector3.new(x, y0 + 2.6, z + 0.8), Color3.fromHex("FFC070"), 1.5, 7, false)
	m.Parent = parent
end

local function dossier(parent: Instance, nom: string, classe: string?): Instance
	local d = Instance.new(classe or "Folder")
	d.Name = nom
	d.Parent = parent
	return d
end

local function etincelles(parent: BasePart, taux: number)
	local e = Instance.new("ParticleEmitter")
	e.Name = "Etincelles"
	e.Color = ColorSequence.new(COULEUR_RARETE)
	e.LightEmission = 1
	e.LightInfluence = 0
	e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.18 * E), NumberSequenceKeypoint.new(1, 0) })
	e.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.2, 0.1),
		NumberSequenceKeypoint.new(1, 1),
	})
	e.Lifetime = NumberRange.new(3, 5)
	e.Speed = NumberRange.new(0.8 * E, 1.4 * E) -- montée lente ≈ 1,1 stud/s (à l'échelle 1)
	e.EmissionDirection = Enum.NormalId.Top
	e.SpreadAngle = Vector2.new(8, 8)
	e.Rate = taux
	e.Shape = Enum.ParticleEmitterShape.Box
	e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	e.Enabled = false
	e.Parent = parent
	CollectionService:AddTag(e, "AutelRarete")
end

-- Panneau texte au-dessus de l'autel, taille en studs ; hauteur = au-dessus du sol (cotes de la spec)
local function panneau(
	parent: BasePart,
	nom: string,
	hauteur: number,
	largeur: number,
	haut: number,
	texte: string,
	couleur: Color3,
	contour: Color3
): BillboardGui
	local billboard = Instance.new("BillboardGui")
	billboard.Name = nom
	billboard.Size = UDim2.fromScale(largeur * E, haut * E)
	billboard.StudsOffsetWorldSpace = origine:VectorToWorldSpace(Vector3.new(0, hauteur * E, 0))
		+ (origine.Position - parent.Position)
	billboard.MaxDistance = 120
	billboard.LightInfluence = 0
	local label = Instance.new("TextLabel")
	label.Name = "Texte"
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.Text = texte
	label.TextScaled = true
	label.FontFace = Font.new("rbxasset://fonts/families/FredokaOne.json")
	label.TextColor3 = couleur
	label.TextStrokeColor3 = contour
	label.TextStrokeTransparency = 0
	label.Parent = billboard
	billboard.Parent = parent
	return billboard
end

local function construire(base: Model)
	local ancienRng = base:FindFirstChild("RNG")
	if not ancienRng or not ancienRng:IsA("BasePart") then
		warn(`[Autel] pas de RNG dans {base:GetFullName()}`)
		return
	end
	-- Sauvegarde de l'ancien cube (une seule fois)
	if ancienRng:GetAttribute("AutelInvocation") == nil then
		local sauvegarde = ServerStorage:FindFirstChild("Sauvegarde_AvantAutel")
			or dossier(ServerStorage, "Sauvegarde_AvantAutel")
		ancienRng:Clone().Parent = sauvegarde
	end
	-- Position : zone « Sanctuaire » (assets/zone/construire_zone.luau) → repère du Centre, sol de la zone (y 1,8),
	-- pivot à l'attribut AutelZ de la base ; sinon ancienne base : arrière de l'estrade calé sur le fond de l'ancien cube
	local centre = base:FindFirstChild("Centre")
	local autelZ = base:GetAttribute("AutelZ")
	if centre and centre:IsA("BasePart") and typeof(autelZ) == "number" then
		origine = centre.CFrame * CFrame.new(0, -centre.Size.Y / 2 + Y_SOL_ZONE, autelZ)
	else
		local fondZ = ancienRng:GetAttribute("FondZ") :: number?
		if not fondZ then
			fondZ = ancienRng.Position.Z - ancienRng.Size.Z / 2
			ancienRng:SetAttribute("FondZ", fondZ)
		end
		local sol = base:FindFirstChild("Sol") :: BasePart
		local yS = sol.Position.Y + sol.Size.Y / 2
		origine = CFrame.new(ancienRng.Position.X, yS, (fondZ :: number) + RECUL + 5.5 * E)
	end

	local ancien = base:FindFirstChild(NOM)
	if ancien then
		ancien:Destroy()
	end

	local autel = Instance.new("Model")
	autel.Name = NOM
	autel.ModelStreamingMode = Enum.ModelStreamingMode.Atomic
	autel:SetAttribute("Level", 1)
	autel:SetAttribute("Echelle", E)
	CollectionService:AddTag(autel, "AutelInvocation")

	-- Estrade
	local estrade = dossier(autel, "Estrade", "Model")
	local baseEstrade = B(estrade, "Estrade_Base", "Pierre_Ardoise", 16, 0.8, 11, 0, 0.4, 0)
	B(estrade, "Estrade_Haut", "Pierre_Claire", 14, 0.8, 9, 0, 1.2, -0.5)
	B(estrade, "Marche_Basse", "Pierre_Claire", 6, 0.4, 1.2, 0, 0.2, 6.1)
	B(estrade, "Marche_Haute", "Pierre_Claire", 5, 0.4, 1.2, 0, 1.0, 4.6)
	for _, p in estrade:GetChildren() do
		(p :: BasePart).CanCollide = true
	end
	B(estrade, "Neon_Estrade_Avant", "Neon_Rarete", 16.1, 0.16, 0.16, 0, 0.8, 5.5)
	B(estrade, "Neon_Estrade_Gauche", "Neon_Rarete", 0.16, 0.16, 11, -8, 0.8, 0)
	B(estrade, "Neon_Estrade_Droite", "Neon_Rarete", 0.16, 0.16, 11, 8, 0.8, 0)
	B(estrade, "Neon_Estrade_Haut", "Neon_Rarete", 14.1, 0.16, 0.16, 0, 1.6, 4.0)

	-- Piliers et bouts du kasagi
	local piliers = dossier(autel, "Piliers", "Model")
	for _, s in { -1, 1 } do
		B(piliers, "Pilier_Socle", "Metal_Sombre", 1.8, 0.8, 1.8, 5 * s, 2.0, -0.5).CanCollide = true
		C(piliers, "Pilier", "Laque", 0.55, 9.4, 5 * s, 7.1, -0.5).CanCollide = true
		C(piliers, "Neon_Anneau_Pilier_Bas", "Neon_Rarete", 0.64, 0.22, 5 * s, 3.2, -0.5)
		C(piliers, "Neon_Anneau_Pilier_Haut", "Neon_Rarete", 0.64, 0.22, 5 * s, 8.6, -0.5)
		B(piliers, "Kasagi_Bout", "Bois_Sombre", 1.7, 0.7, 1.5, 7.85 * s, 12.72, -0.5, 0, 0, 0.2 * s)
	end

	-- Portique torii (+ compte à rebours de recharge au-dessus du toit, texte écrit par le client)
	local torii = dossier(autel, "Torii", "Model")
	B(torii, "Nuki", "Laque", 12.4, 0.6, 0.7, 0, 9.8, -0.5)
	B(torii, "Plaque_Cadre", "Metal_Or", 1.9, 1.7, 0.3, 0, 10.95, -0.5)
	B(torii, "Plaque", "Bois_Sombre", 1.5, 1.3, 0.4, 0, 10.95, -0.5)
	B(torii, "Shimaki", "Laque", 13, 0.6, 1.0, 0, 11.95, -0.5)
	local kasagi = B(torii, "Kasagi", "Bois_Sombre", 14.4, 0.7, 1.5, 0, 12.6, -0.5)
	B(torii, "Neon_Sous_Toit", "Neon_Rarete", 13.2, 0.16, 0.16, 0, 12.2, 0.15)
	panneau(kasagi, "Recharge", 14.4, 7, 1.2, "", Color3.fromHex("FFFFFF"), Color3.fromHex("1C1733")).Enabled = false

	-- Autel central + faisceau vers la carte
	local autelCentral = dossier(autel, "Autel", "Model")
	C(autelCentral, "Autel_Socle", "Metal_Or", 1.5, 0.5, 0, 1.85, -0.5)
	C(autelCentral, "Neon_Anneau_Autel", "Neon_Rarete", 1.62, 0.14, 0, 2.06, -0.5)
	local coeur = C(autelCentral, "Autel_Coeur", "Metal_Sombre", 1.0, 0.3, 0, 2.25, -0.5)
	local beam = Instance.new("Beam")
	beam.Attachment0 = attache(coeur, "Beam_Bas", Vector3.new(0, 2.4, -0.5))
	beam.Attachment1 = attache(coeur, "Beam_Haut", Vector3.new(0, 5.0, -0.5))
	beam.Width0, beam.Width1 = 2.2 * E, 0.7 * E
	beam.LightEmission = 1
	beam.LightInfluence = 0
	beam.Transparency = NumberSequence.new(0.78)
	beam.Color = ColorSequence.new(COULEUR_RARETE)
	beam.FaceCamera = true
	beam.Segments = 1
	beam.Enabled = false
	beam.Parent = coeur
	CollectionService:AddTag(beam, "AutelRarete")
	-- lumière de la carte, fixe (ne tourne pas avec la carte)
	lumiere(coeur, Vector3.new(0, 6.4, 1.5), COULEUR_RARETE, 3, 16, true).Name = "LumiereCarte"

	-- Carte géante (animée par le client : rotation Y + flottement)
	local carte = Instance.new("Model")
	carte.Name = "Carte_Geante"
	local cadre = B(carte, "Carte_Geante_Cadre_Neon", "Neon_Rarete", 3.8, 5.4, 0.16, 0, 6.4, -0.5)
	B(carte, "Carte_Geante_Face", "Carte_Face", 3.27, 4.86, 0.24, 0, 6.4, -0.5)
	local losange = B(carte, "Carte_Geante_Losange", "Neon_Blanc", 1.14, 1.14, 0.3, 0, 6.4, -0.5, 0, 0, math.rad(45))
	losange.Color = COULEUR_LOSANGE_ETEINT
	losange.Material = Enum.Material.SmoothPlastic
	B(carte, "Carte_Losange_Centre", "Carte_Face", 0.62, 0.62, 0.36, 0, 6.4, -0.5, 0, 0, math.rad(45))
	carte.PrimaryPart = cadre
	carte.Parent = autel

	-- Lanternes avant
	local lanternes = dossier(autel, "Lanternes", "Model")
	lanterne(lanternes, -6.8, 4.7, 0.8)
	lanterne(lanternes, 6.8, 4.7, 0.8)

	-- Niveaux 2 à 10 (cumulatifs)
	local niveaux = dossier(autel, "Niveaux")
	local N = {}
	for n = 2, 10 do
		N[n] = dossier(niveaux, `N{n}`, "Model")
	end
	for _, s in { -1, 1 } do
		S(N[2], "Kasagi_Boule_Or", "Metal_Or", 0.38, 8.65 * s, 13.05, -0.5)
		C(N[3], "Lanterne_Suspendue_Fil", "Metal_Sombre", 0.03, 0.9, 3.2 * s, 9.05, -0.5)
		local boule = S(N[3], "Neon_Lanterne_Suspendue", "Neon_Ambre", 0.45, 3.2 * s, 8.35, -0.5)
		lumiere(boule, Vector3.new(3.2 * s, 8.35, -0.5), Color3.fromHex("FFC070"), 1, 6, false)
		B(N[4], "Neon_Pilier_Vertical", "Neon_Rarete", 0.14, 7.6, 0.14, 5 * s, 6.0, 0.07)
		lanterne(N[5], 6.2 * s, -4.2, 1.6)
	end

	-- N6 : halo (tore R 3,3 en 36 segments) derrière la carte, tourne autour de Z
	local halo = Instance.new("Model")
	halo.Name = "Halo"
	local R, SEG = 3.3, 36
	local longueur = 2 * math.pi * R / SEG * 1.04
	for i = 0, SEG - 1 do
		local a = i * 2 * math.pi / SEG
		local p = piece(`Halo_{i + 1}`, "Neon_Rarete", Enum.PartType.Block, Vector3.new(longueur, 0.18, 0.18))
		mettre(p, CFrame.new(0, 6.4, -1.3) * CFrame.Angles(0, 0, a) * CFrame.new(0, R, 0), halo)
	end
	local centreHalo = piece("Halo_Centre", "Neon_Rarete", Enum.PartType.Block, Vector3.one * 0.1)
	centreHalo.Transparency = 1
	centreHalo:SetAttribute("BaseTransparency", 1)
	CollectionService:RemoveTag(centreHalo, "AutelRarete")
	mettre(centreHalo, CFrame.new(0, 6.4, -1.3), halo)
	halo.PrimaryPart = centreHalo
	halo.Parent = N[6]

	-- N7 à N9 : 6 cartes en orbite (rangées dans N7, le client n'affiche que celles du niveau)
	for i = 1, 6 do
		local orbite = Instance.new("Model")
		orbite.Name = `Carte_Orbite_{i}`
		orbite:SetAttribute("Index", i - 1)
		local c = B(orbite, "Cadre_Neon", "Neon_Rarete", 1.1, 1.6, 0.08, 0, 6.4, -0.5)
		B(orbite, "Face", "Carte_Face", 0.94, 1.42, 0.12, 0, 6.4, -0.5)
		orbite.PrimaryPart = c
		orbite.Parent = N[7]
	end

	-- N10 : aura ForceField (cylindre ouvert en 24 panneaux), étincelles, panneau « MAX »
	local PANNEAUX, RA = 24, 7.6
	for i = 0, PANNEAUX - 1 do
		local a = i * 2 * math.pi / PANNEAUX
		local p =
			piece(`Aura_{i + 1}`, "Aura", Enum.PartType.Block, Vector3.new(2 * math.pi * RA / PANNEAUX * 1.02, 11, 0.1))
		p.Transparency = 0.9
		p:SetAttribute("BaseTransparency", 0.9)
		mettre(p, CFrame.new(0, 7.1, -0.5) * CFrame.Angles(0, a, 0) * CFrame.new(0, 0, RA), N[10])
	end
	local zone = piece("Etincelles_Zone", "Neon_Rarete", Enum.PartType.Block, Vector3.new(13, 9, 9))
	zone.Transparency = 1
	zone:SetAttribute("BaseTransparency", 1)
	CollectionService:RemoveTag(zone, "AutelRarete")
	mettre(zone, CFrame.new(0, 6.5, -0.5), N[10])
	etincelles(zone, 14)
	panneau(zone, "Max", 16, 4, 1.6, "MAX", Color3.fromHex("FFD34A"), Color3.fromHex("5A3A00"))

	-- Point d'accroche du tirage : l'ancien "RNG", invisible, au volume de l'autel
	ancienRng.Transparency = 1
	ancienRng.CanCollide = false
	ancienRng.CanTouch = false
	ancienRng.CanQuery = false
	ancienRng.CastShadow = false
	ancienRng.Size = Vector3.new(16, 13.4, 11) * E
	ancienRng.CFrame = origine * CFrame.new(0, 6.7 * E, 0)
	ancienRng:SetAttribute("AutelInvocation", true)
	for _, d in ancienRng:GetChildren() do
		if d:IsA("Decal") or d:IsA("Texture") or d:IsA("SurfaceGui") then
			d:Destroy()
		end
	end

	autel.PrimaryPart = baseEstrade
	autel.Parent = base
	print(`[Autel] construit dans {base:GetFullName()} ({#autel:GetDescendants()} objets)`)
end

for _, base in CollectionService:GetTagged("BaseJoueur") do
	if base:IsA("Model") then
		construire(base)
	end
end
