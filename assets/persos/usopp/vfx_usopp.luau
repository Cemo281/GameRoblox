--!strict
-- Effets de la séquence de combat de usopp (vitrine), lancé par MCP dans Studio, relançable.
-- Cible : ReplicatedStorage.ModelesPersonnages.usopp s'il existe, sinon Workspace.Essais_Usopp.usopp.
-- Crée le dossier VFX du modèle (joué par src/client/Vitrine.luau) et les modèles Forge dans
-- ReplicatedStorage.EffetsForge.usopp (joués par src/client/EffetsForge.luau) :
--   Explosion_Grenade, Explosion_GrosseGrenade : feu, boule de feu, colonne de fumée, étincelles, anneau, lumière ; cratère, fissures, blocs ;
--   Impact_Graine : terre et étincelles vertes, sol fendu ; Impact_Fouet : poussière, gravillons ;
--   Impact_Bille : petit éclat ; Explosion_Charge : explosion orange, petit cratère ;
--   Esquive_Poussiere : poussière et gravillons aux pieds (atterrissages).
-- Les effets d'impact sont dans l'Attachment « PointImpact » du HumanoidRootPart, déplacé par src/client/Tireur.luau
-- avant chaque déclenchement ; les groupes Forge cherchent le sol sous ce point (attribut Point).
-- Textures : intégrées (rbxasset://) ou déjà en ligne (luffy, zoro). Aucun envoi.

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local modeles = ReplicatedStorage:FindFirstChild("ModelesPersonnages")
local modele = (modeles and modeles:FindFirstChild("usopp") or workspace.Essais_Usopp.usopp) :: Model
local hrp = modele:FindFirstChild("HumanoidRootPart") :: BasePart
local bassin = modele:FindFirstChild("LowerTorso") :: BasePart
modele:SetAttribute("Tireur", true)

local TEX_ETINCELLE = "rbxasset://textures/particles/sparkles_main.dds"
local TEX_FEU = "rbxasset://textures/particles/fire_main.dds"
local TEX_FUMEE = "rbxasset://textures/particles/smoke_main.dds"
local TEX_POUSSIERE = "rbxassetid://70434048288435" -- luffy
local TEX_ETOILE_IMPACT = "rbxassetid://112249090477155" -- luffy
local TEX_ANNEAU_IMPACT = "rbxassetid://93783833153831" -- luffy

local ORANGE = Color3.fromRGB(255, 150, 50)
local JAUNE = Color3.fromRGB(255, 220, 120)
local FUMEE = Color3.fromRGB(70, 66, 62)
local TERRE = Color3.fromRGB(190, 168, 130) -- sable clair : la poussière doit se voir sur l'herbe et l'allée
local VERT = Color3.fromRGB(140, 230, 90)

local function v(x: number, y: number, z: number): Vector3
	return Vector3.new(x, y, z)
end
local function nr(a: number, b: number): NumberRange
	return NumberRange.new(a, b)
end
local function seq(a: number, b: number): NumberSequence
	return NumberSequence.new(a, b)
end
local function jaillir(debut: number, pic: number, fin: number): NumberSequence
	return NumberSequence.new({
		NumberSequenceKeypoint.new(0, debut),
		NumberSequenceKeypoint.new(0.2, pic),
		NumberSequenceKeypoint.new(1, fin),
	})
end
local function fondu(debut: number): NumberSequence
	return NumberSequence.new({
		NumberSequenceKeypoint.new(0, debut),
		NumberSequenceKeypoint.new(0.7, debut + (1 - debut) * 0.3),
		NumberSequenceKeypoint.new(1, 1),
	})
end

---------------------------------------------------------------- particules

type Reglages = { [string]: any }

local function emetteur(parent: Instance, nom: string, r: Reglages): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Name = nom
	e.Enabled = false
	e.Texture = r.Texture or TEX_ETINCELLE
	local couleur = r.Couleur or Color3.new(1, 1, 1)
	e.Color = if typeof(couleur) == "ColorSequence" then couleur else ColorSequence.new(couleur)
	e.LightEmission = r.LightEmission or 0.4
	e.LightInfluence = r.LightInfluence or 0
	e.Brightness = r.Eclat or 2
	e.Size = r.Taille or seq(0.5, 0)
	e.Transparency = r.Transparence or fondu(0)
	e.Lifetime = r.Duree or nr(0.5, 0.8)
	e.Speed = r.Vitesse or nr(0, 0)
	e.SpreadAngle = r.Ecart or Vector2.new(180, 180)
	e.Acceleration = r.Acceleration or Vector3.zero
	e.Drag = r.Frein or 0
	e.Rate = 20
	e.Rotation = nr(0, 360)
	e.RotSpeed = r.Rotation or nr(0, 0)
	e.Orientation = r.Orientation or Enum.ParticleOrientation.FacingCamera
	e.EmissionDirection = r.Direction or Enum.NormalId.Top
	e.ZOffset = r.ZOffset or 0
	e:SetAttribute("Quantite", r.Quantite or 1)
	e.Parent = parent
	return e
end

local function lumiere(parent: Instance, nom: string, couleur: Color3, eclat: number, portee: number): PointLight
	local l = Instance.new("PointLight")
	l.Name = nom
	l.Color = couleur
	l.Brightness = eclat
	l.Range = portee
	l.Shadows = false
	l.Enabled = false
	l.Parent = parent
	return l
end

local vfx = modele:FindFirstChild("VFX")
if vfx then
	vfx:Destroy()
end
vfx = Instance.new("Folder")
vfx.Name = "VFX"
vfx.Parent = modele
for _, ancien in { hrp:FindFirstChild("PointImpact"), bassin:FindFirstChild("PoussierePieds") } do
	if ancien then
		ancien:Destroy()
	end
end
local impact = Instance.new("Attachment")
impact.Name = "PointImpact"
impact.Parent = hrp
local pieds = Instance.new("Attachment")
pieds.Name = "PoussierePieds"
pieds.Position = v(0, -2.6, 0)
pieds.Parent = bassin

local function effet(nom: string, attributs: { [string]: any }, liste: { Instance })
	local d = Instance.new("Folder")
	d.Name = nom
	for cle, valeur in attributs do
		d:SetAttribute(cle, valeur)
	end
	for i, e in liste do
		local lien = Instance.new("ObjectValue")
		lien.Name = `Effet{i}`
		lien.Value = e
		lien.Parent = d
	end
	d.Parent = vfx
end

-- feu : blanc-jaune au cœur, orange puis rouge sombre (reste lisible sur le sol clair de l'île)
local DEGRADE_FEU = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 240, 170)),
	ColorSequenceKeypoint.new(0.3, Color3.fromRGB(255, 140, 30)),
	ColorSequenceKeypoint.new(0.75, Color3.fromRGB(200, 60, 20)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(90, 40, 30)),
})

-- PointImpact est posé au sol : tout part en demi-sphère vers le haut (Ecart ≤ 90), sinon la moitié des
-- particules part dans le sol et l'explosion paraît plate
local function explosion(prefixe: string, k: number): { Instance }
	return {
		emetteur(impact, prefixe .. "Feu", {
			Texture = TEX_FEU,
			Couleur = DEGRADE_FEU,
			LightEmission = 0.45,
			Eclat = 3,
			Taille = jaillir(1.4 * k, 3 * k, 0.6 * k),
			Transparence = fondu(0),
			Duree = nr(0.35, 0.65),
			Vitesse = nr(7 * k, 15 * k),
			Frein = 6,
			Acceleration = v(0, 8, 0),
			Ecart = Vector2.new(75, 75),
			Quantite = math.round(24 * k),
		}),
		emetteur(impact, prefixe .. "Boule", { -- boule de feu qui monte au-dessus du point d'impact
			Texture = TEX_FEU,
			Couleur = DEGRADE_FEU,
			LightEmission = 0.6,
			Eclat = 4,
			Taille = jaillir(2 * k, 4.2 * k, 1.2 * k),
			Transparence = fondu(0),
			Duree = nr(0.45, 0.7),
			Vitesse = nr(5 * k, 8 * k),
			Frein = 3,
			Acceleration = v(0, 10, 0),
			Ecart = Vector2.new(20, 20),
			Quantite = math.round(6 * k),
			ZOffset = 0.3,
		}),
		emetteur(impact, prefixe .. "Fumee", { -- colonne de fumée grise qui s'élève
			Texture = TEX_FUMEE,
			Couleur = ColorSequence.new(Color3.fromRGB(95, 88, 82), FUMEE),
			LightEmission = 0,
			LightInfluence = 0.7,
			Eclat = 1,
			Taille = jaillir(1.6 * k, 3.6 * k, 5.5 * k),
			Transparence = fondu(0.25),
			Duree = nr(1.3, 2.2),
			Vitesse = nr(5 * k, 10 * k),
			Frein = 2.5,
			Acceleration = v(0, 5, 0),
			Ecart = Vector2.new(40, 40),
			Rotation = nr(-30, 30),
			Quantite = math.round(14 * k),
		}),
		emetteur(impact, prefixe .. "Etincelles", {
			Couleur = JAUNE,
			LightEmission = 1,
			Eclat = 4,
			Taille = seq(0.35, 0),
			Duree = nr(0.4, 0.8),
			Vitesse = nr(18 * k, 32 * k),
			Frein = 2,
			Acceleration = v(0, -35, 0),
			Ecart = Vector2.new(70, 70),
			Quantite = math.round(26 * k),
		}),
		emetteur(impact, prefixe .. "Anneau", {
			Texture = TEX_ANNEAU_IMPACT,
			Couleur = Color3.fromRGB(255, 235, 200),
			LightEmission = 0.6,
			Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
			Taille = jaillir(1, 7 * k, 9 * k),
			Transparence = fondu(0.2),
			Duree = nr(0.35, 0.35),
			Vitesse = nr(0.01, 0.01),
			Ecart = Vector2.zero,
			Quantite = 1,
		}),
		lumiere(impact, prefixe .. "Lumiere", ORANGE, 6, 18 * k),
	}
end

local function poussiere(parent: Attachment, prefixe: string, k: number, couleur: Color3): ParticleEmitter
	return emetteur(parent, prefixe .. "Poussiere", {
		Texture = TEX_POUSSIERE,
		Couleur = couleur,
		LightEmission = 0,
		LightInfluence = 0.5,
		Eclat = 1,
		Taille = jaillir(1 * k, 2.6 * k, 3.6 * k),
		Transparence = fondu(0.3),
		Duree = nr(0.6, 1.1),
		Vitesse = nr(5 * k, 10 * k),
		Frein = 5,
		Acceleration = v(0, 1.5, 0),
		Ecart = Vector2.new(80, 80),
		Quantite = math.round(14 * k),
	})
end

local function etoile(parent: Attachment, prefixe: string, taille: number, couleur: Color3): ParticleEmitter
	return emetteur(parent, prefixe .. "Etoile", {
		Texture = TEX_ETOILE_IMPACT,
		Couleur = couleur,
		LightEmission = 0.7,
		Eclat = 3,
		Taille = jaillir(taille * 0.4, taille, taille * 1.1),
		Transparence = fondu(0),
		Duree = nr(0.12, 0.16),
		Ecart = Vector2.zero,
		Quantite = 1,
		ZOffset = 0.5,
	})
end

effet("Explosion_Grenade", { Mode = "Burst", Secousse = 0.45, DureeFlash = 0.15 }, explosion("Grenade", 1))
effet("Explosion_GrosseGrenade", { Mode = "Burst", Secousse = 1.0, DureeFlash = 0.25 }, explosion("GrosseGrenade", 1.6))
effet("Explosion_Charge", { Mode = "Burst", Secousse = 0.6, DureeFlash = 0.2 }, explosion("Charge", 1.2))
effet("Impact_Graine", { Mode = "Burst", Secousse = 0.2 }, {
	poussiere(impact, "Graine", 1, TERRE),
	emetteur(impact, "GraineEtincelles", {
		Couleur = VERT,
		LightEmission = 1,
		Eclat = 3,
		Taille = seq(0.3, 0),
		Duree = nr(0.4, 0.7),
		Vitesse = nr(8, 16),
		Acceleration = v(0, -25, 0),
		Ecart = Vector2.new(50, 50),
		Quantite = 18,
	}),
	etoile(impact, "Graine", 4, VERT),
})
effet("Impact_Fouet", { Mode = "Burst", Secousse = 0.3 }, {
	poussiere(impact, "Fouet", 1.2, TERRE),
	etoile(impact, "Fouet", 5, Color3.fromRGB(230, 255, 200)),
})
effet("Impact_Bille", { Mode = "Burst" }, {
	poussiere(impact, "Bille", 0.5, TERRE),
	etoile(impact, "Bille", 1.6, JAUNE),
})
effet("Esquive_Poussiere", { Mode = "Burst" }, { poussiere(pieds, "Pieds", 1.1, TERRE) })

---------------------------------------------------------------- Forge (format de assets/persos/luffy/elastique/vfx_forge_luffy.luau)

local racine = ReplicatedStorage:FindFirstChild("EffetsForge")
if not racine then
	racine = Instance.new("Folder")
	racine.Name = "EffetsForge"
	racine.Parent = ReplicatedStorage
end
assert(racine, "EffetsForge introuvable")
local ancien = racine:FindFirstChild("usopp")
if ancien then
	ancien:Destroy()
end
local modelesForge = Instance.new("Folder")
modelesForge.Name = "usopp"
modelesForge.Parent = racine

local function attributs(instance: Instance, valeurs: { [string]: any })
	for nom, valeur in valeurs do
		instance:SetAttribute(nom, valeur)
	end
end

local function forge(nomEffet: string): Folder
	local e = vfx:FindFirstChild(nomEffet)
	assert(e, `effet {nomEffet} introuvable`)
	local dossier = Instance.new("Folder")
	dossier.Name = nomEffet
	dossier.Parent = modelesForge
	local lien = Instance.new("ObjectValue")
	lien.Name = "Forge"
	lien.Value = dossier
	lien.Parent = e
	return dossier
end

local function groupe(dossierForge: Folder, nom: string, extra: { [string]: any }?): Folder
	local g = Instance.new("Folder")
	g.Name = nom
	g:SetAttribute("Ancre", "Sol")
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
	p:SetAttribute("TeinteSol", 0.12) -- couleur du sol, un peu assombrie (EffetsForge)
	return p
end

local function support(g: Folder): Part
	local existant = g:FindFirstChild("Support")
	if existant then
		return existant :: Part
	end
	local s = pieceModele("Support")
	s:SetAttribute("TeinteSol", nil)
	s.Transparency = 1
	s.CastShadow = false
	s.Size = v(0.2, 0.2, 0.2)
	s.Parent = g
	return s
end

local function onde(g: Folder, type_: string, nom: string, origine: Vector3, valeurs: { [string]: any }): Part
	local a = Instance.new("Attachment")
	a.Name = `Origine_{nom}`
	a.Position = origine
	attributs(a, { RayDirection = v(0, -8, 0), FilterTag = "ForgeIgnore", FilterType = "Exclude" })
	CollectionService:AddTag(a, "Shockwave")
	a.Parent = support(g)
	local p = pieceModele(nom)
	attributs(p, valeurs)
	p.Parent = sousDossier(a, type_)
	return p
end

local function bord(
	g: Folder,
	nom: string,
	rayon: number,
	segments: number,
	taille: number,
	duree: number,
	enfoncement: number
)
	onde(g, "Rings", nom, v(0, 1.5, 0), {
		Radius = rayon,
		Segments = segments,
		MinSize = v(0.7, 0.35, 0.6) * taille,
		MaxSize = v(1.15, 0.65, 1.0) * taille,
		Lifetime = nr(duree - 0.25, duree),
		Offset_Start = v(0, -0.7 * taille, 0),
		BaseOffset = v(0, -enfoncement, 0),
		Offset_Start_Duration = 0.1,
		Offset_End = v(0, -1.2 * taille, 0),
		Offset_End_Duration = 0.6,
		SizeScaleStart = v(0.25, 0.25, 0.25),
		Size_Start_Duration = 0.1,
		SizeScaleEnd = v(0, 0, 0),
		Size_End_Duration = 0.6,
		Transparency_Start = 0,
		Transparency_End = 1,
		Transparency_Duration = 0.6,
	})
end

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
		onde(g, "Lines", `{prefixe}{i}`, v(0, 1.5, 0), {
			Direction = v(math.cos(angle), 0, math.sin(angle)),
			Length = longueur * (0.8 + 0.4 * ((i * 37) % 10) / 10),
			FixedAmount = quantite,
			Duration = 0.15,
			Scale_Start = 1,
			Scale_End = 0.6,
			Lifetime = nr(duree - 0.2, duree),
			MinSize = v(0.5, 0.15, 0.6) * taille,
			MaxSize = v(0.8, 0.3, 1.0) * taille,
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
		})
	end
end

-- débris : LinearMagnitude = distance parcourue, la parabole monte de ≈ 196 × Airtime² / 8 studs ;
-- AngularMagnitude est multiplié par la masse (garder ≈ 0,2 à 1 pour les petites pièces)
local function debris(
	g: Folder,
	nom: string,
	quantite: NumberRange,
	taille: number,
	force: NumberRange,
	airtime: NumberRange,
	angulaire: NumberRange,
	duree: NumberRange
)
	onde(g, "Debris", nom, v(0, 0.6, 0), {
		Amount = quantite,
		MinSize = v(0.3, 0.25, 0.3) * taille,
		MaxSize = v(0.6, 0.5, 0.6) * taille,
		LinearMagnitude = force,
		AngularMagnitude = angulaire,
		Airtime = airtime,
		Lifetime = duree,
		MinDirection = v(-1, 0.7, -1),
		MaxDirection = v(1, 1.4, 1),
		InheritanceEnabled = false,
		SizeScaleEnd = v(0, 0, 0),
		Size_Duration = 0.4,
		Transparency_Start = 0,
		Transparency_End = 0,
	})
end

local AU_POINT = { Point = "PointImpact" }

do -- grenade : cratère moyen, 5 fissures, blocs
	local g = groupe(forge("Explosion_Grenade"), "Sol", AU_POINT)
	bord(g, "Cratere", 2.2, 10, 1.2, 4, 0.2)
	fissures(g, "Fissure", 5, 4.5, 5, 0.9, 4, 0.4)
	debris(g, "Blocs", nr(6, 9), 1.6, nr(3, 6), nr(0.35, 0.45), nr(1, 3), nr(1.5, 2.2))
end
do -- grosse grenade : grand cratère, couronne, 7 fissures, gros blocs
	local g = groupe(forge("Explosion_GrosseGrenade"), "Sol", AU_POINT)
	bord(g, "Cratere", 3.6, 14, 1.9, 5, 0.35)
	bord(g, "Couronne", 5, 18, 0.9, 4.8, 0)
	fissures(g, "Fissure", 7, 8, 7, 1.1, 5, 0.2)
	debris(g, "Blocs", nr(10, 14), 2.2, nr(4, 8), nr(0.4, 0.5), nr(2, 5), nr(2, 3))
end
do -- graine : le sol se fend en étoile là où la liane va pousser
	local g = groupe(forge("Impact_Graine"), "Sol", AU_POINT)
	bord(g, "Bord", 1.2, 7, 0.7, 3.4, 0.05)
	fissures(g, "Fissure", 4, 3, 4, 0.7, 3.4, 0.8)
	debris(g, "Mottes", nr(4, 6), 0.9, nr(1.5, 3), nr(0.28, 0.36), nr(0.4, 1), nr(0.8, 1.2))
end
do -- fouet de la liane : gravillons et petite fissure
	local g = groupe(forge("Impact_Fouet"), "Sol", AU_POINT)
	fissures(g, "Fissure", 2, 2.5, 3, 0.6, 1.5, 0.3)
	debris(g, "Gravillons", nr(4, 6), 0.8, nr(1.5, 3), nr(0.28, 0.36), nr(0.4, 1), nr(0.6, 1))
end
do -- tir chargé : petit cratère
	local g = groupe(forge("Explosion_Charge"), "Sol", AU_POINT)
	bord(g, "Cratere", 1.8, 9, 1, 3, 0.15)
	fissures(g, "Fissure", 4, 3.5, 4, 0.8, 3, 0.2)
	debris(g, "Blocs", nr(5, 7), 1.2, nr(2.5, 5), nr(0.32, 0.42), nr(0.8, 2), nr(1.2, 1.8))
end
do -- atterrissage : couronne de gravillons sous le bassin
	local g = groupe(forge("Esquive_Poussiere"), "Sol")
	bord(g, "Couronne", 1.6, 8, 0.6, 1.1, 0)
	debris(g, "Gravillons", nr(3, 5), 0.7, nr(1.5, 2.5), nr(0.26, 0.34), nr(0.4, 1), nr(0.6, 1))
end

return `usopp : {#vfx:GetChildren()} effets, Forge {#modelesForge:GetDescendants()} instances ({modele:GetFullName()})`
