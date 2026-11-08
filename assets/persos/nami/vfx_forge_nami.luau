--!strict
-- Effets VFX Forge de la vitrine de nami, lancé par MCP dans Studio, relançable (voir vfx_forge_luffy.luau pour le format).
-- Modèles dans ReplicatedStorage.EffetsForge.nami.<Effet>, ObjectValue « Forge » dans ModelesPersonnages.nami.VFX.<Effet> ;
-- joués par src/client/EffetsForge ; les marqueurs des animations publiées ne changent pas.
--   Eclair (Action 1,83 s)          : impact brûlé au point de chute (fond noirci, rochers, fissures, débris, flash, anneau)
--   Rafales (Action 1,87 s, 1 s)    : trois petits impacts successifs dans la zone de l'éclair
--   Pieces (Signature 1,33 s)       : pluie de pièces d'or qui rebondissent (l'effet n'existait pas : marqueur sans effet)
--   Pieces_Brillent (Idle 1 s)      : quelques pièces qui sautent de la bourse
-- Action : 3,5 s ; les traces de l'éclair disparaissent vers 3,3 s.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local nami = ReplicatedStorage.ModelesPersonnages.nami
local vfx = nami:FindFirstChild("VFX") :: Folder
local utilitaire = (require :: any)(ReplicatedStorage.EmitModule.mod.utility)

local racine = ReplicatedStorage:FindFirstChild("EffetsForge")
if not racine then
	racine = Instance.new("Folder")
	racine.Name = "EffetsForge"
	racine.Parent = ReplicatedStorage
end
assert(racine, "ReplicatedStorage.EffetsForge manquant")
local ancienPerso = racine:FindFirstChild("nami")
if ancienPerso then
	ancienPerso:Destroy()
end
local modeles = Instance.new("Folder")
modeles.Name = "nami"
modeles.Parent = racine

local function courbe(p0Droite: UDim2, p1Gauche: UDim2): string
	return buffer.tostring(utilitaire.serializePath({
		Path2DControlPoint.new(UDim2.fromScale(0, 1), UDim2.new(), p0Droite),
		Path2DControlPoint.new(UDim2.fromScale(1, 0), p1Gauche, UDim2.new()),
	}))
end
local COURBE_RAPIDE = courbe(UDim2.fromScale(0, -1), UDim2.fromScale(-0.98, 0))
local COURBE_TENUE = courbe(UDim2.fromScale(0.9, 0), UDim2.fromScale(-0.02, 0.9))

local OR = Color3.fromRGB(255, 196, 58)
local JAUNE_ECLAIR = Color3.fromRGB(255, 228, 110)

local function attributs(instance: Instance, valeurs: { [string]: any })
	for nom, valeur in valeurs do
		instance:SetAttribute(nom, valeur)
	end
end

local function v(x: number, y: number, z: number): Vector3
	return Vector3.new(x, y, z)
end

local function nr(a: number, b: number): NumberRange
	return NumberRange.new(a, b)
end

-- Modèle de l'effet `nomEffet` (créé dans nami.VFX s'il manque, ex. « Pieces »)
local function forge(nomEffet: string): Folder
	local effet = vfx:FindFirstChild(nomEffet)
	if not effet then
		effet = Instance.new("Folder")
		effet.Name = nomEffet
		effet.Parent = vfx
	end
	assert(effet, `effet {nomEffet} introuvable`)
	local ancien = effet:FindFirstChild("Forge")
	if ancien then
		ancien:Destroy()
	end
	local dossier = Instance.new("Folder")
	dossier.Name = nomEffet
	dossier.Parent = modeles
	local lien = Instance.new("ObjectValue")
	lien.Name = "Forge"
	lien.Value = dossier
	lien.Parent = effet
	return dossier
end

local function groupe(dossierForge: Folder, nom: string, ancre: string, extra: { [string]: any }?): Folder
	local g = Instance.new("Folder")
	g.Name = nom
	g:SetAttribute("Ancre", ancre)
	if extra then
		attributs(g, extra)
	end
	g.Parent = dossierForge
	return g
end

local function sousDossier(parent: Instance, nom: string): Folder
	local d = parent:FindFirstChild(nom)
	if d then
		return d :: Folder
	end
	local nouveau = Instance.new("Folder")
	nouveau.Name = nom
	nouveau.Parent = parent
	return nouveau
end

local function pieceModele(nom: string): Part
	local p = Instance.new("Part")
	p.Name = nom
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.Material = Enum.Material.SmoothPlastic
	p.Color = Color3.fromRGB(110, 100, 90)
	p.Size = v(1, 1, 1)
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.CFrame = CFrame.identity
	return p
end

local function support(g: Folder): Part
	local existant = g:FindFirstChild("Support")
	if existant then
		return existant :: Part
	end
	local s = pieceModele("Support")
	s.Transparency = 1
	s.CastShadow = false
	s.Size = v(0.2, 0.2, 0.2)
	s.Parent = g
	return s
end

-- Support > Attachment « Shockwave » (origine) > Rings / Lines / Debris > pièce modèle
local function onde(g: Folder, type_: string, nom: string, origine: Vector3, valeurs: { [string]: any }): Part
	local a = Instance.new("Attachment")
	a.Name = `Origine_{nom}`
	a.Position = origine
	attributs(a, {
		RayDirection = v(0, -8, 0),
		FilterTag = "ForgeIgnore", -- tag local posé par EffetsForge (vitrines + pièces déjà posées par Forge)
		FilterType = "Exclude",
	})
	CollectionService:AddTag(a, "Shockwave")
	a.Parent = support(g)
	local p = pieceModele(nom)
	attributs(p, valeurs)
	p.Parent = sousDossier(a, type_)
	return p
end

-- Maillage animé (SpecialMesh Sphere, échelles `debut` → `fin`, axe X = épaisseur)
local function maillage(
	g: Folder,
	nom: string,
	cadre: CFrame,
	debut: Vector3,
	fin: Vector3,
	couleur: Color3,
	matiere: Enum.Material,
	valeurs: { [string]: any }
): Model
	local a = Instance.new("Attachment")
	a.Name = nom
	a.CFrame = cadre
	a.Parent = support(g)
	local m = Instance.new("Model")
	m.Name = nom
	attributs(m, valeurs)
	for _, info in { { "Start", debut }, { "End", fin } } do
		local p = pieceModele(info[1])
		p.Color = couleur
		p.Material = matiere
		p.CastShadow = false
		p.Transparency = 1 -- invisible pendant EmitDelay (Forge pose la pièce au centre avant le délai)
		local mesh = Instance.new("SpecialMesh")
		mesh.MeshType = Enum.MeshType.Sphere
		mesh.Scale = info[2]
		mesh.Parent = p
		p.Parent = m
	end
	m.Parent = a
	return m
end

local A_PLAT = CFrame.Angles(0, 0, math.pi / 2) -- axe X du maillage vertical : disque posé au sol

-- Disque au sol (couleur du sol assombrie de `teinte`) qui se creuse vite puis tient et s'efface à la fin
local function fond(g: Folder, position: Vector3, diametre: number, duree: number, transparence: number, teinte: number)
	local m = maillage(
		g,
		"Fond",
		CFrame.new(position) * A_PLAT,
		v(0.06, 0.5, 0.5),
		v(0.06, diametre, diametre),
		Color3.fromRGB(30, 26, 22),
		Enum.Material.SmoothPlastic,
		{
			EffectDuration = nr(duree, duree),
			Part_Transparency_Start = transparence,
			Part_Transparency_End = 1,
			Part_Transparency_Curve = COURBE_TENUE,
			Mesh_Scale_Curve = COURBE_RAPIDE,
		}
	)
	for _, p in m:GetChildren() do
		p:SetAttribute("TeinteSol", teinte)
	end
end

-- Éclat lumineux (néon) qui grandit et s'efface
local function eclat(
	g: Folder,
	nom: string,
	cadre: CFrame,
	debut: Vector3,
	fin: Vector3,
	couleur: Color3,
	duree: number,
	transparence: number,
	delai: number
)
	maillage(g, nom, cadre, debut, fin, couleur, Enum.Material.Neon, {
		EffectDuration = nr(duree, duree),
		EmitDelay = delai,
		Part_Transparency_Start = transparence,
		Part_Transparency_End = 1,
	})
end

local function bord(
	g: Folder,
	nom: string,
	position: Vector3,
	rayon: number,
	segments: number,
	taille: number,
	duree: number,
	delai: number
)
	onde(g, "Rings", nom, position + v(0, 1.5, 0), {
		Radius = rayon,
		Segments = segments,
		EmitDelay = delai,
		-- tailles très variées : sinon le bord ressemble à une couronne de blocs identiques (vu sur l'aperçu)
		MinSize = v(0.5, 0.28, 0.45) * taille,
		MaxSize = v(1.35, 0.85, 1.15) * taille,
		Lifetime = nr(duree - 0.15, duree),
		Offset_Start = v(0, -0.7 * taille, 0),
		BaseOffset = v(0, 0, 0),
		Offset_Start_Duration = 0.08,
		Offset_End = v(0, -1 * taille, 0),
		Offset_End_Duration = 0.45,
		SizeScaleStart = v(0.25, 0.25, 0.25),
		Size_Start_Duration = 0.08,
		SizeScaleEnd = v(0, 0, 0),
		Size_End_Duration = 0.45,
		Transparency_Start = 0,
		Transparency_End = 1,
		Transparency_Duration = 0.45,
	})
end

local function fissures(g: Folder, nombre: number, longueur: number, quantite: number, taille: number, duree: number)
	for i = 1, nombre do
		local angle = (i - 1) / nombre * math.pi * 2 + 0.4
		onde(g, "Lines", `Fissure{i}`, v(0, 1.5, 0), {
			Direction = v(math.cos(angle), 0, math.sin(angle)),
			Length = longueur * (0.8 + 0.4 * ((i * 37) % 10) / 10),
			FixedAmount = quantite,
			Duration = 0.1,
			Scale_Start = 1,
			Scale_End = 0.5,
			Lifetime = nr(duree - 0.15, duree),
			MinSize = v(0.5, 0.15, 0.6) * taille,
			MaxSize = v(0.8, 0.3, 1.0) * taille,
			Offset_Start = v(0, -0.4, 0),
			BaseOffset = v(0, 0, 0),
			Offset_Start_Duration = 0.08,
			SizeScaleStart = v(0.3, 0.3, 0.3),
			Size_Start_Duration = 0.08,
			SizeScaleEnd = v(0, 0, 0),
			Size_End_Duration = 0.45,
			Offset_End = v(0, -0.6, 0),
			Offset_End_Duration = 0.45,
			Transparency_Start = 0,
			Transparency_End = 1,
			Transparency_Duration = 0.45,
		})
	end
end

-- Débris projetés : `LinearMagnitude` = distance jusqu'au point visé, atteint en `Airtime` s ; la gravité (196) fait
-- monter la parabole d'environ 196 × Airtime² / 8 studs : 0,3 s ≈ 2 studs, 0,45 s ≈ 5 studs, 0,7 s ≈ 12 studs.
local function debris(g: Folder, nom: string, origine: Vector3, valeurs: { [string]: any }): Part
	local base: { [string]: any } = {
		InheritanceEnabled = false,
		-- impulsion angulaire × masse : sur une petite pièce (faible inertie) la rotation devient énorme (vu : 1 900 rad/s,
		-- transformée en saut au contact du sol) → ≈ 25 × valeur rad/s pour des éclats de 0,3 à 0,5 stud
		AngularMagnitude = nr(0.4, 1),
		SizeScaleEnd = v(0, 0, 0),
		Size_Duration = 0.35,
		Transparency_Start = 0,
		Transparency_End = 0,
	}
	for cle, valeur in valeurs do
		base[cle] = valeur
	end
	return onde(g, "Debris", nom, origine, base)
end

-- Débris couleur du sol (attribut TeinteSol, posé par EffetsForge)
local function eclats(
	g: Folder,
	nom: string,
	quantite: NumberRange,
	taille: number,
	distance: NumberRange,
	duree: NumberRange
)
	local p = debris(g, nom, v(0, 0.5, 0), {
		Amount = quantite,
		MinSize = v(0.25, 0.22, 0.25) * taille,
		MaxSize = v(0.5, 0.42, 0.5) * taille,
		LinearMagnitude = distance,
		Airtime = nr(0.28, 0.38),
		Lifetime = duree,
		-- vers l'avant et les côtés seulement (-Z = regard de nami) : rien ne part dans ses jambes ni son bâton,
		-- qui projetteraient les débris très loin
		MinDirection = v(-1, 0.8, -1),
		MaxDirection = v(1, 1.5, 0.1),
	})
	p:SetAttribute("TeinteSol", 0.35)
end

-- Pièces d'or (cylindres plats en métal doré) qui tournent et rebondissent
local function pieces(g: Folder, nom: string, origine: Vector3, valeurs: { [string]: any })
	local base: { [string]: any } = {
		MinSize = v(0.08, 0.45, 0.45),
		MaxSize = v(0.1, 0.6, 0.6),
		AngularMagnitude = nr(0.2, 0.5), -- pièce plate : ≈ 60 × valeur rad/s
	}
	for cle, valeur in valeurs do
		base[cle] = valeur
	end
	local p = debris(g, nom, origine, base)
	p.Shape = Enum.PartType.Cylinder
	p.Material = Enum.Material.Metal
	p.Color = OR
	p.Reflectance = 0.2
end

-- 1) Éclair : impact brûlé au point de chute (VFX_Eclair_5, au sol devant nami)
do
	local f = forge("Eclair")
	local g = groupe(f, "Impact", "Sol", { Point = "VFX_Eclair_5" })
	local duree = 1.45
	fond(g, v(0, 0.04, 0), 3.6, duree + 0.1, 0.2, 0.85)
	bord(g, "Bord", v(0, 0, 0), 1.45, 9, 0.9, duree, 0)
	fissures(g, 5, 3.2, 5, 0.8, duree - 0.05)
	eclats(g, "Eclats", nr(6, 9), 1.1, nr(1.5, 3.5), nr(0.7, 1.1))
	eclat(
		g,
		"Flash",
		CFrame.new(0, 0.8, 0),
		v(0.4, 0.4, 0.4),
		v(4.5, 4.5, 4.5),
		Color3.fromRGB(255, 250, 215),
		0.14,
		0,
		0
	)
	eclat(g, "Anneau", CFrame.new(0, 0.15, 0) * A_PLAT, v(0.05, 0.5, 0.5), v(0.3, 10, 10), JAUNE_ECLAIR, 0.3, 0.2, 0)
	eclat(
		g,
		"Anneau2",
		CFrame.new(0, 0.25, 0) * A_PLAT,
		v(0.05, 0.5, 0.5),
		v(0.2, 6, 6),
		Color3.fromRGB(255, 255, 240),
		0.22,
		0.4,
		0.05
	)
end

-- 2) Rafales : trois petits impacts successifs autour du point de chute
do
	local f = forge("Rafales")
	local g = groupe(f, "Impacts", "Sol", { Point = "VFX_Eclair_5" })
	local points = {
		{ v(-1.4, 0, 0.7), 0.2 },
		{ v(1.3, 0, -0.6), 0.45 },
		{ v(0.2, 0, 1.3), 0.7 },
	}
	for i, info in points do
		local position, delai = info[1], info[2]
		bord(g, `Impact{i}`, position, 0.75, 6, 0.55, 0.85, delai)
		eclat(
			g,
			`Eclat{i}`,
			CFrame.new(position + v(0, 0.12, 0)) * A_PLAT,
			v(0.05, 0.3, 0.3),
			v(0.15, 3.5, 3.5),
			JAUNE_ECLAIR,
			0.2,
			0.25,
			delai
		)
	end
end

-- 3) Signature : pluie de pièces d'or au-dessus de nami, éclat doré
do
	local f = forge("Pieces")
	local g = groupe(f, "Pluie", "Torse")
	-- au-dessus de la tête : une pièce créée dans le corps en est éjectée violemment (vu en test : 22 studs de haut)
	pieces(g, "Pieces", v(0, 2.8, 0), {
		Amount = nr(14, 20),
		LinearMagnitude = nr(2.5, 5),
		Airtime = nr(0.32, 0.42),
		Lifetime = nr(1.4, 2),
		MinDirection = v(-1, 0.4, -1),
		MaxDirection = v(1, 1, 1),
	})
	eclat(
		g,
		"Eclat",
		CFrame.new(0, 1.2, 0),
		v(0.4, 0.4, 0.4),
		v(3.5, 3.5, 3.5),
		Color3.fromRGB(255, 225, 120),
		0.2,
		0.1,
		0
	)
	local sol = groupe(f, "Sol", "Sol")
	eclat(sol, "Anneau", CFrame.new(0, 0.1, 0) * A_PLAT, v(0.05, 0.5, 0.5), v(0.2, 8, 8), OR, 0.4, 0.35, 0)
end

-- 4) Idle : quelques pièces qui sautent de la bourse
do
	local f = forge("Pieces_Brillent")
	local g = groupe(f, "Bourse", "Point", { Point = "VFX_Pieces_Bourse" })
	-- à côté de la bourse, vers l'extérieur (-X local = côté gauche de nami, la bourse est dans sa main gauche)
	pieces(g, "Pieces", v(-0.6, 0.6, 0), {
		Amount = nr(3, 4),
		MinSize = v(0.06, 0.35, 0.35),
		MaxSize = v(0.08, 0.45, 0.45),
		LinearMagnitude = nr(0.8, 1.6),
		Airtime = nr(0.22, 0.3),
		Lifetime = nr(0.6, 0.9),
		MinDirection = v(-1, 1.5, -0.5),
		MaxDirection = v(-0.2, 2.5, 0.5),
	})
end

return `Forge nami : {#modeles:GetDescendants()} instances dans {#modeles:GetChildren()} effets`
