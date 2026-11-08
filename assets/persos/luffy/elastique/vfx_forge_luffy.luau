--!strict
-- Effets VFX Forge de la vitrine de luffy (séquence « combattant élastique »), lancé par MCP dans Studio, relançable.
-- Ajoute un dossier « Forge » dans les effets existants de ModelesPersonnages.luffy.VFX (joué par src/client/EffetsForge,
-- format de l'EmitModule de VFX Forge 1.4.5) ; les marqueurs de l'animation publiée ne changent pas.
--   Pompe_1..4         : le sol s'enfonce aux pieds (bord de cratère qui grandit, fond qui s'assombrit, fissures, gravillons)
--   Explosion_Vapeur   : gros cratère (bord, couronne, fissures, blocs projetés, fond sombre)
--   Impact_Pied        : onde d'air du coup de pied
--   Explosion_AirPoing : ondes d'air autour du poing, sol fendu devant luffy
--   Esquive_Atterrissage : petite couronne de gravillons
-- Durées calées sur la séquence (9,7 s) : le cratère reste jusqu'à ≈ 9,2 s puis s'enfonce et disparaît.
-- Format Forge : pièce dans un dossier Rings / Lines / Debris avec un Attachment tagué « Shockwave » (origine du lancer
-- de rayon) ; Model avec pièces Start / End dans un Attachment = maillage animé (taille, transparence).

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local luffy = ReplicatedStorage.ModelesPersonnages.luffy
local vfx = luffy:FindFirstChild("VFX") :: Folder
local utilitaire = (require :: any)(ReplicatedStorage.EmitModule.mod.utility)

-- Modèles rangés hors du personnage (ReplicatedStorage.EffetsForge.luffy.<Effet>) : des pièces dans le Model fausseraient
-- sa boîte englobante (BaseService le poserait trop haut) et seraient affichées. L'effet VFX.<Effet> n'a qu'un ObjectValue
-- « Forge » qui pointe vers son modèle.
local racine = ReplicatedStorage:FindFirstChild("EffetsForge")
if not racine then
	racine = Instance.new("Folder")
	racine.Name = "EffetsForge"
	racine.Parent = ReplicatedStorage
end
assert(racine, "ReplicatedStorage.EffetsForge manquant")
local ancienPerso = racine:FindFirstChild("luffy")
if ancienPerso then
	ancienPerso:Destroy()
end
local modelesLuffy = Instance.new("Folder")
modelesLuffy.Name = "luffy"
modelesLuffy.Parent = racine

-- Courbes Forge (format Path2D sérialisé, y = 1 au départ)
local function courbe(p0Droite: UDim2, p1Gauche: UDim2): string
	return buffer.tostring(utilitaire.serializePath({
		Path2DControlPoint.new(UDim2.fromScale(0, 1), UDim2.new(), p0Droite),
		Path2DControlPoint.new(UDim2.fromScale(1, 0), p1Gauche, UDim2.new()),
	}))
end
-- presque tout au début puis lent (fond du cratère qui se creuse)
local COURBE_RAPIDE = courbe(UDim2.fromScale(0, -1), UDim2.fromScale(-0.98, 0))
-- tient puis s'efface à la fin
local COURBE_TENUE = courbe(UDim2.fromScale(0.9, 0), UDim2.fromScale(-0.02, 0.9))

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

local function forge(nomEffet: string): Folder
	local effet = vfx:FindFirstChild(nomEffet)
	assert(effet, `effet {nomEffet} introuvable`)
	local ancien = effet:FindFirstChild("Forge")
	if ancien then
		ancien:Destroy()
	end
	local dossier = Instance.new("Folder")
	dossier.Name = nomEffet
	dossier.Parent = modelesLuffy
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
	p.CastShadow = true
	p.Material = Enum.Material.Slate
	p.Color = Color3.fromRGB(110, 100, 90)
	p.Size = v(1, 1, 1)
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.CFrame = CFrame.identity
	return p
end

-- Pièce transparente qui porte les Attachment du groupe (origines des ondes, maillages)
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

-- Pièce d'onde de choc : Support > Attachment tagué « Shockwave » (origine du lancer de rayon, position locale
-- `origine`) > dossier Rings / Lines / Debris > pièce modèle (Forge cherche l'Attachment parmi les ancêtres de la pièce).
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

-- Maillage animé : disque ou ellipsoïde plat (SpecialMesh Sphere) qui passe de `debut` à `fin` (échelles du maillage).
-- `cadre` : position et orientation locales (l'axe X du maillage est l'épaisseur).
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

-- Fond de cratère : disque sombre (couleur du sol assombrie) posé sur le sol, qui se creuse vite puis tient.
local function fond(
	g: Folder,
	nom: string,
	hauteur: number,
	diametreDebut: number,
	diametreFin: number,
	duree: number,
	transparence: number,
	teinte: number
)
	local m = maillage(
		g,
		nom,
		CFrame.new(0, hauteur, 0) * CFrame.Angles(0, 0, math.pi / 2),
		v(0.06, diametreDebut, diametreDebut),
		v(0.06, diametreFin, diametreFin),
		Color3.fromRGB(40, 35, 30),
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

-- Onde d'air : ellipsoïde très plat perpendiculaire à l'axe -Z de l'ancre, qui s'élargit et s'efface.
local function ondeAir(
	g: Folder,
	nom: string,
	avance: number,
	taille: number,
	duree: number,
	couleur: Color3,
	transparence: number,
	delai: number
)
	maillage(
		g,
		nom,
		CFrame.new(0, 0, -avance) * CFrame.Angles(0, math.pi / 2, 0),
		v(0.05, 0.6, 0.6),
		v(0.25, taille, taille),
		couleur,
		Enum.Material.Neon,
		{
			EffectDuration = nr(duree, duree),
			EmitDelay = delai,
			Part_Transparency_Start = transparence,
			Part_Transparency_End = 1,
		}
	)
end

local FISSURE: { [string]: any } = {
	Offset_Start = v(0, -0.5, 0),
	BaseOffset = v(0, 0, 0),
	Offset_Start_Duration = 0.1,
	SizeScaleStart = v(0.3, 0.3, 0.3),
	Size_Start_Duration = 0.1,
	SizeScaleEnd = v(0, 0, 0),
	Size_End_Duration = 0.6,
	Offset_End = v(0, -0.8, 0),
	Offset_End_Duration = 0.6,
	Transparency_Start = 0,
	Transparency_End = 1,
	Transparency_Duration = 0.6,
}

local function fissures(
	g: Folder,
	prefixe: string,
	nombre: number,
	longueur: number,
	quantite: number,
	taille: number,
	duree: number,
	decalage: number
)
	for i = 1, nombre do
		local angle = (i - 1) / nombre * math.pi * 2 + decalage
		local valeurs = table.clone(FISSURE)
		valeurs.Direction = v(math.cos(angle), 0, math.sin(angle))
		valeurs.Length = longueur * (0.8 + 0.4 * ((i * 37) % 10) / 10)
		valeurs.FixedAmount = quantite
		valeurs.Duration = 0.15
		valeurs.Scale_Start = 1
		valeurs.Scale_End = 0.6
		valeurs.Lifetime = nr(duree - 0.2, duree)
		valeurs.MinSize = v(0.5, 0.15, 0.6) * taille
		valeurs.MaxSize = v(0.8, 0.3, 1.0) * taille
		onde(g, "Lines", `{prefixe}{i}`, v(0, 1.5, 0), valeurs)
	end
end

-- Débris : couleur du sol sous le personnage (un peu assombrie), posée par EffetsForge (attribut TeinteSol). L'héritage
-- de Forge (InheritanceEnabled) prenait aussi l'herbe de l'île, sous la base.
local function couleurDuSol(p: Part)
	p.Material = Enum.Material.SmoothPlastic
	p:SetAttribute("TeinteSol", 0.12)
end

local function gravillons(
	g: Folder,
	nom: string,
	quantite: NumberRange,
	taille: number,
	force: NumberRange,
	duree: NumberRange
)
	local p = onde(g, "Debris", nom, v(0, 0.5, 0), {
		Amount = quantite,
		MinSize = v(0.25, 0.22, 0.25) * taille,
		MaxSize = v(0.5, 0.42, 0.5) * taille,
		LinearMagnitude = force,
		-- impulsion angulaire × masse : ≈ 25 × valeur rad/s pour ces gravillons (plus fort, ils rebondissent très haut)
		AngularMagnitude = nr(0.4, 1),
		Airtime = nr(0.28, 0.38),
		Lifetime = duree,
		MinDirection = v(-1, 0.7, -1),
		MaxDirection = v(1, 1.4, 1),
		InheritanceEnabled = false,
		SizeScaleEnd = v(0, 0, 0),
		Size_Duration = 0.4,
		Transparency_Start = 0,
		Transparency_End = 0,
	})
	couleurDuSol(p)
end

local function bord(
	g: Folder,
	nom: string,
	rayon: number,
	segments: number,
	taille: number,
	duree: number,
	enfoncement: number,
	delai: number
)
	onde(g, "Rings", nom, v(0, 1.5, 0), {
		Radius = rayon,
		Segments = segments,
		EmitDelay = delai,
		MinSize = v(0.7, 0.35, 0.6) * taille,
		MaxSize = v(1.15, 0.65, 1.0) * taille,
		Lifetime = nr(duree - 0.25, duree),
		Offset_Start = v(0, -0.7 * taille, 0),
		BaseOffset = v(0, -enfoncement, 0),
		Offset_Start_Duration = 0.12,
		Offset_End = v(0, -1.2 * taille, 0),
		Offset_End_Duration = 0.7,
		SizeScaleStart = v(0.25, 0.25, 0.25),
		Size_Start_Duration = 0.12,
		SizeScaleEnd = v(0, 0, 0),
		Size_End_Duration = 0.7,
		Transparency_Start = 0,
		Transparency_End = 1,
		Transparency_Duration = 0.7,
	})
end

-- Fin visée du cratère dans la séquence (s) ; instants des marqueurs (elastique.js : Gear 2 puis Combo à 4,1 s)
local FIN_CRATERE = 9.2
local POMPES = { 0.45, 0.75, 1.4, 1.9 }
local EXPLOSION = 2.32

-- 1) Pompes : le sol s'enfonce aux pieds, un peu plus à chaque pompe
for k, instant in POMPES do
	local f = forge(`Pompe_{k}`)
	local g = groupe(f, "Sol", "Sol")
	local duree = FIN_CRATERE - instant
	local echelle = 1 + 0.15 * (k - 1)
	bord(g, "Bord", 1.5 + 0.38 * k, 7 + k, echelle, duree, 0.06 * k, 0)
	fond(g, "Fond", 0.02 + 0.012 * k, 0.6, 2 * (1.2 + 0.38 * k), duree, 0.62, 0.55)
	gravillons(g, "Gravillons", nr(3 + k, 5 + k), 0.8 + 0.1 * k, nr(1.5, 2.5 + 0.4 * k), nr(0.9, 1.5))
	if k >= 2 then
		fissures(g, "Fissure", k + 1, 1.6 + 0.7 * k, 3 + k, 0.8 + 0.1 * k, duree, k * 0.9)
	end
end

-- 2) Explosion de vapeur (Gear 2) : le cratère se forme d'un coup
do
	local f = forge("Explosion_Vapeur")
	local g = groupe(f, "Sol", "Sol")
	local duree = FIN_CRATERE - EXPLOSION
	bord(g, "Cratere", 4.2, 15, 2.1, duree, 0.35, 0)
	bord(g, "Couronne", 5.8, 20, 1, duree - 0.1, 0, 0.06)
	fissures(g, "Fissure", 6, 10, 7, 1.15, duree, 0.3)
	fond(g, "Fond", 0.08, 3, 9, duree, 0.45, 0.65)
	local blocs = onde(g, "Debris", "Blocs", v(0, 0.6, 0), {
		Amount = nr(10, 14),
		MinSize = v(0.55, 0.45, 0.55),
		MaxSize = v(1.25, 0.95, 1.25),
		-- distance jusqu'au point visé, atteint en Airtime s ; la parabole monte d'environ 196 × Airtime² / 8 studs
		-- (0,45 s ≈ 5 studs) : les blocs retombent autour du cratère
		LinearMagnitude = nr(4, 8),
		AngularMagnitude = nr(2, 5), -- ≈ 6 × valeur rad/s pour ces blocs
		Airtime = nr(0.4, 0.5),
		Lifetime = nr(2, 3),
		MinDirection = v(-1, 0.6, -1),
		MaxDirection = v(1, 1.5, 1),
		InheritanceEnabled = false,
		SizeScaleEnd = v(0, 0, 0),
		Size_Duration = 0.5,
		Transparency_Start = 0,
		Transparency_End = 0,
	})
	couleurDuSol(blocs)
	-- onde d'air horizontale au ras du sol
	maillage(
		g,
		"OndeSol",
		CFrame.new(0, 0.4, 0) * CFrame.Angles(0, 0, math.pi / 2),
		v(0.05, 1, 1),
		v(0.4, 22, 22),
		Color3.fromRGB(255, 225, 220),
		Enum.Material.Neon,
		{ EffectDuration = nr(0.35, 0.35), Part_Transparency_Start = 0.35, Part_Transparency_End = 1 }
	)
end

-- 3) Coup de pied : onde d'air autour du pied
do
	local f = forge("Impact_Pied")
	local g = groupe(f, "Air", "Membre")
	ondeAir(g, "Onde1", 0, 7, 0.22, Color3.fromRGB(255, 240, 235), 0.3, 0)
	ondeAir(g, "Onde2", 0.8, 10, 0.3, Color3.fromRGB(255, 205, 190), 0.55, 0.04)
end

-- 4) Poing aérien : ondes d'air en cascade devant le poing, sol fendu devant luffy
do
	local f = forge("Explosion_AirPoing")
	local air = groupe(f, "Air", "Membre")
	ondeAir(air, "Onde1", 0, 12, 0.25, Color3.fromRGB(255, 245, 235), 0.2, 0)
	ondeAir(air, "Onde2", 1.6, 18, 0.35, Color3.fromRGB(255, 160, 80), 0.4, 0.05)
	ondeAir(air, "Onde3", 3.4, 25, 0.45, Color3.fromRGB(255, 120, 60), 0.6, 0.1)
	maillage(
		air,
		"Boule",
		CFrame.identity,
		v(0.5, 0.5, 0.5),
		v(7, 7, 7),
		Color3.fromRGB(255, 250, 240),
		Enum.Material.Neon,
		{ EffectDuration = nr(0.16, 0.16), Part_Transparency_Start = 0, Part_Transparency_End = 1 }
	)
	local sol = groupe(f, "Sol", "Sol", { Orientation = "Membre" })
	local valeurs = table.clone(FISSURE)
	valeurs.Direction = v(0, 0, -1)
	valeurs.Length = 16
	valeurs.FixedAmount = 14
	valeurs.Duration = 0.3
	valeurs.Scale_Start = 0.6
	valeurs.Scale_End = 1.5
	valeurs.Rotation = nr(-20, 20)
	valeurs.Offset_Start = v(0, -1.2, 0)
	valeurs.Lifetime = nr(1.6, 2.1)
	valeurs.MinSize = v(0.9, 0.5, 0.8)
	valeurs.MaxSize = v(1.4, 0.9, 1.3)
	onde(sol, "Lines", "SolFendu", v(0, 1.5, -2.5), valeurs)
end

-- 5) Atterrissage : petite couronne de gravillons
do
	local f = forge("Esquive_Atterrissage")
	local g = groupe(f, "Sol", "Sol")
	bord(g, "Couronne", 1.7, 8, 0.65, 1.1, 0, 0)
	gravillons(g, "Gravillons", nr(4, 6), 0.8, nr(1.5, 3), nr(0.6, 1))
end

return `Forge luffy : {#modelesLuffy:GetDescendants()} instances dans {#modelesLuffy:GetChildren()} effets`
