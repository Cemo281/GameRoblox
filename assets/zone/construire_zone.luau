--!strict
-- Construit la zone joueur « Sanctuaire » (spec « Zone joueur A - spec Claude Code », fonction zone('A') de la planche)
-- dans chaque Model tagué "BaseJoueur". Lancé par MCP, relançable. L'autel est construit à part
-- (assets/autel/construire_autel.luau, à relancer après ce script : il lit l'attribut AutelZ posé ici).
-- Repère : origine = sol extérieur sous le Centre (Centre.CFrame décalé de -0,5 stud), +Z local = entrée (vers le Hub).
-- Positions de la spec = centres, déjà calculées avec Y0 = 1,8 (dessus du sol de la zone).
-- Pas de barrière anti-intrus (décision de l'utilisateur du 08/11 : tout le monde peut visiter toutes les bases).
-- Noms lus par le code : Socles/Socle_n/Emplacement (attribut Index), Collecte/Collecte_Disque_Or (tag Collecteur),
-- Panneau/Panneau_Face (labels NomProprietaire, Niveau), Amelioration (BillboardGui Etiquette), PointApparition.

local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")

local AUTEL_Z = -36.55 -- pivot de l'autel (échelle 1,5) : ses marches arrivent au bout de l'allée (z -26,5)
local POLICE = Font.new("rbxasset://fonts/families/FredokaOne.json", Enum.FontWeight.Bold)

local MAT = {
	Pierre_Ardoise = { "3B3F52", Enum.Material.Slate, 0 },
	Pierre_Claire = { "5A5F78", Enum.Material.Slate, 0 },
	Dalle_Allee = { "6A6F86", Enum.Material.Slate, 0 },
	Sol_Sable = { "D8C29A", Enum.Material.Sand, 0 },
	Bois_Sombre = { "2B1D1A", Enum.Material.Wood, 0 },
	Bois_Clair = { "C9A27A", Enum.Material.Wood, 0 },
	Laque = { "C23B32", Enum.Material.SmoothPlastic, 0.05 },
	Metal_Or = { "D9A441", Enum.Material.Metal, 0.2 },
	Metal_Sombre = { "2A2C36", Enum.Material.Metal, 0 },
	Corde_Paille = { "D9C48A", Enum.Material.Fabric, 0 },
	Shide_Papier = { "F4F2EE", Enum.Material.SmoothPlastic, 0 },
	Banniere_Tissu = { "C23B32", Enum.Material.Fabric, 0 },
	Banniere_Bande = { "F4ECDC", Enum.Material.Fabric, 0 },
	Neon_Ambre = { "FFE2B0", Enum.Material.Neon, 0 },
	Neon_Blanc = { "FFF3DC", Enum.Material.Neon, 0 },
	Neon_Collecte = { "FFD34D", Enum.Material.Neon, 0 },
	Neon_Amelioration = { "3DDC84", Enum.Material.Neon, 0 },
	Socle_Libre = { "6C6A78", Enum.Material.SmoothPlastic, 0 }, -- anneau d'un socle libre (rallumé en néon par le serveur)
	Invisible = { "FFFFFF", Enum.Material.SmoothPlastic, 0 },
}

-- Anciennes pièces de la base remplacées par la zone (sauvegardées une fois) et dossiers construits ici.
local ANCIENS = { "Podium", "Emplacements", "Zone Joueur", "Sol", "Allee", "Panneau", "PointApparition", "Collecteur" }
local CONSTRUITS = {
	"Sol",
	"Allee",
	"Lanternes",
	"Cloture",
	"ToriiEntree",
	"Panneau",
	"Socles",
	"Collecte",
	"Amelioration",
	"Bannieres",
	"PointApparition",
}

local origine: CFrame

local function piece(nom: string, mat: string, forme: Enum.PartType, taille: Vector3, collision: boolean): Part
	local m = MAT[mat]
	local p = Instance.new("Part")
	p.Name = nom
	p.Shape = forme
	p.Size = taille
	p.Color = Color3.fromHex(m[1] :: string)
	p.Material = m[2] :: Enum.Material
	p.Reflectance = m[3] :: number
	p.Anchored = true
	p.CanCollide = collision
	p.CanTouch = false
	p.CanQuery = collision
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	if mat:sub(1, 4) == "Neon" or mat == "Invisible" then
		p.CastShadow = false
	end
	if mat == "Invisible" then
		p.Transparency = 1
	end
	return p
end

local function mettre(p: BasePart, cf: CFrame, parent: Instance): Part
	p.CFrame = origine * cf
	p.Parent = parent
	return p :: Part
end

-- Box : B(nom, mat, w, h, d, x, y, z, rx, ry, rz) ; collision par défaut
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
	rz: number?,
	collision: boolean?
): Part
	local p = piece(nom, mat, Enum.PartType.Block, Vector3.new(w, h, d), collision ~= false)
	return mettre(p, CFrame.new(x, y, z) * CFrame.fromEulerAnglesXYZ(rx or 0, ry or 0, rz or 0), parent)
end

-- Cylindre vertical (axe Roblox X couché de 90° autour de Z)
local function C(
	parent: Instance,
	nom: string,
	mat: string,
	r: number,
	h: number,
	x: number,
	y: number,
	z: number,
	collision: boolean?
): Part
	local p = piece(nom, mat, Enum.PartType.Cylinder, Vector3.new(h, 2 * r, 2 * r), collision ~= false)
	return mettre(p, CFrame.new(x, y, z) * CFrame.Angles(0, 0, math.rad(90)), parent)
end

-- Cylindre couché dans l'axe X
local function CX(
	parent: Instance,
	nom: string,
	mat: string,
	r: number,
	h: number,
	x: number,
	y: number,
	z: number,
	collision: boolean?
): Part
	local p = piece(nom, mat, Enum.PartType.Cylinder, Vector3.new(h, 2 * r, 2 * r), collision ~= false)
	return mettre(p, CFrame.new(x, y, z), parent)
end

local function S(parent: Instance, nom: string, mat: string, r: number, x: number, y: number, z: number): Part
	local p = piece(nom, mat, Enum.PartType.Ball, Vector3.one * 2 * r, false)
	return mettre(p, CFrame.new(x, y, z), parent)
end

local function neon(p: Part): Part
	p.CanCollide = false
	p.CanQuery = false
	p.CastShadow = false
	return p
end

local function lumiere(
	parent: BasePart,
	couleur: string,
	eclat: number,
	portee: number,
	positionLocale: Vector3?
): PointLight
	local l = Instance.new("PointLight")
	l.Color = Color3.fromHex(couleur)
	l.Brightness = eclat
	l.Range = portee
	l.Shadows = false
	if positionLocale then
		local a = Instance.new("Attachment")
		a.Name = "Lumiere"
		a.Parent = parent
		a.WorldPosition = (origine * CFrame.new(positionLocale)).Position
		l.Parent = a
	else
		l.Parent = parent
	end
	return l
end

local function groupe(parent: Instance?, nom: string, classe: string?): Instance
	local d = Instance.new(classe or "Model")
	d.Name = nom
	d.Parent = parent
	return d
end

local function etiquette(
	parent: Instance,
	nom: string,
	texte: string,
	couleur: string,
	position: UDim2,
	taille: UDim2,
	contour: string?
): TextLabel
	local label = Instance.new("TextLabel")
	label.Name = nom
	label.BackgroundTransparency = 1
	label.Position = position
	label.Size = taille
	label.Text = texte
	label.TextScaled = true
	label.FontFace = POLICE
	label.TextColor3 = Color3.fromHex(couleur)
	if contour then
		label.TextStrokeColor3 = Color3.fromHex(contour)
		label.TextStrokeTransparency = 0
	end
	label.Parent = parent
	return label
end

-- BillboardGui posé en (x, y, z) local (Attachment dans `parent`), taille en studs
local function billboard(
	parent: BasePart,
	nom: string,
	x: number,
	y: number,
	z: number,
	largeur: number,
	haut: number
): BillboardGui
	local a = Instance.new("Attachment")
	a.Name = nom .. "_Ancre"
	a.Parent = parent
	a.WorldPosition = (origine * CFrame.new(x, y, z)).Position
	local gui = Instance.new("BillboardGui")
	gui.Name = nom
	gui.Size = UDim2.fromScale(largeur, haut)
	gui.LightInfluence = 0
	gui.MaxDistance = 90
	gui.Adornee = a
	gui.Parent = parent
	return gui
end

----------------------------------------------------------------------------------------------------
-- 1. Sol
local function construireSol(base: Model)
	local sol = groupe(nil, "Sol")
	B(sol, "Fondation", "Pierre_Ardoise", 92, 1.5, 104, 0, 0.75, 0)
	B(sol, "Sol_Sable", "Sol_Sable", 90, 0.3, 102, 0, 1.65, 0)
	B(sol, "Marche_Haute", "Pierre_Claire", 14, 1.2, 1.2, 0, 0.6, 52.6)
	B(sol, "Marche_Basse", "Pierre_Claire", 14, 0.6, 1.2, 0, 0.3, 53.8)
	sol.Parent = base
end

-- 2. Allée
local function construireAllee(base: Model)
	local allee = groupe(nil, "Allee")
	for i = 0, 30 do
		local mat = if i % 2 == 0 then "Pierre_Claire" else "Dalle_Allee"
		B(allee, `Dalle_{i + 1}`, mat, 11, 0.25, 2.38, 0, 1.925, 49.75 - 2.5 * i)
	end
	for _, s in { -1, 1 } do
		B(allee, "Bordure_Allee", "Pierre_Ardoise", 0.5, 0.4, 77.5, 5.75 * s, 2.0, 12.25)
	end
	allee.Parent = base
end

-- 3. Lanternes de pierre
local function construireLanternes(base: Model)
	local lanternes = groupe(nil, "Lanternes")
	local y0 = 1.8
	for _, x in { -8, 8 } do
		for _, z in { 44, 28, 12, -4, -20 } do
			local m = groupe(lanternes, "Lanterne")
			B(m, "Lanterne_Socle", "Pierre_Claire", 1.4, 0.4, 1.4, x, y0 + 0.2, z)
			C(m, "Lanterne_Pied", "Pierre_Claire", 0.3, 1.6, x, y0 + 1.2, z)
			B(m, "Lanterne_Cadre", "Metal_Sombre", 1.25, 0.14, 1.25, x, y0 + 2.07, z)
			local feu = neon(B(m, "Neon_Lanterne", "Neon_Ambre", 1, 1, 1, x, y0 + 2.6, z))
			B(m, "Lanterne_Toit", "Bois_Sombre", 1.9, 0.3, 1.9, x, y0 + 3.25, z)
			B(m, "Lanterne_Toit_Haut", "Bois_Sombre", 1, 0.3, 1, x, y0 + 3.55, z)
			S(m, "Lanterne_Pointe", "Metal_Or", 0.2, x, y0 + 3.85, z)
			lumiere(feu, "FFC070", 1.5, 9)
		end
	end
	lanternes.Parent = base
end

-- 4. Clôture bois
local function construireCloture(base: Model)
	local cloture = groupe(nil, "Cloture")
	local E, F = 44.5, 50.5
	local function poteau(x: number, z: number)
		B(cloture, "Cloture_Poteau", "Bois_Sombre", 0.9, 4, 0.9, x, 3.8, z)
		B(cloture, "Cloture_Chapeau", "Bois_Sombre", 1.3, 0.3, 1.3, x, 5.95, z)
	end
	for i = 0, 13 do
		poteau(-E, -F + i * (2 * F / 13))
		poteau(E, -F + i * (2 * F / 13))
	end
	for i = 1, 11 do
		poteau(-E + i * (2 * E / 12), -F)
	end
	for _, s in { -1, 1 } do
		for i = 0, 4 do
			poteau(s * (8.5 + 7.2 * i), F)
		end
	end
	for _, y in { 3.2, 4.8 } do
		B(cloture, "Cloture_Lisse", "Bois_Sombre", 0.35, 0.5, 2 * F, -E, y, 0)
		B(cloture, "Cloture_Lisse", "Bois_Sombre", 0.35, 0.5, 2 * F, E, y, 0)
		B(cloture, "Cloture_Lisse", "Bois_Sombre", 2 * E, 0.5, 0.35, 0, y, -F)
		local l = E - 8.5
		B(cloture, "Cloture_Lisse", "Bois_Sombre", l, 0.5, 0.35, -(8.5 + l / 2), y, F)
		B(cloture, "Cloture_Lisse", "Bois_Sombre", l, 0.5, 0.35, 8.5 + l / 2, y, F)
	end
	cloture.Parent = base
end

-- 6. Torii d'entrée
local function construireTorii(base: Model)
	local torii = groupe(nil, "ToriiEntree")
	local tz = 49.3
	for _, s in { -1, 1 } do
		B(torii, "Torii_Socle", "Metal_Sombre", 1.6, 0.6, 1.6, 7.2 * s, 2.1, tz)
		C(torii, "Torii_Pilier", "Laque", 0.6, 10, 7.2 * s, 7.4, tz)
		B(torii, "Torii_Kasagi_Bout", "Bois_Sombre", 1.6, 0.7, 1.6, 9.6 * s, 12.92, tz, 0, 0, 0.2 * s)
	end
	B(torii, "Torii_Nuki", "Laque", 17, 0.6, 0.7, 0, 10.0, tz)
	B(torii, "Torii_Plaque_Cadre", "Metal_Or", 2.2, 1.6, 0.3, 0, 11.1, tz)
	B(torii, "Torii_Plaque", "Bois_Sombre", 1.8, 1.2, 0.4, 0, 11.1, tz)
	B(torii, "Torii_Shimaki", "Laque", 17.6, 0.6, 1.0, 0, 12.1, tz)
	B(torii, "Torii_Kasagi", "Bois_Sombre", 18, 0.7, 1.6, 0, 12.8, tz)
	neon(B(torii, "Neon_Torii_Sous_Toit", "Neon_Blanc", 16.4, 0.14, 0.14, 0, 11.72, tz + 0.55))

	local corde = groupe(torii, "Shimenawa")
	CX(corde, "Shimenawa", "Corde_Paille", 0.32, 14.4, 0, 9.35, tz + 0.45, false)
	for _, x in { -5.4, -1.8, 1.8, 5.4 } do
		B(corde, "Shide", "Shide_Papier", 0.5, 0.7, 0.06, x, 8.6, tz + 0.5, 0, 0, 0.25, false)
		B(corde, "Shide", "Shide_Papier", 0.5, 0.7, 0.06, x + 0.1, 8.0, tz + 0.5, 0, 0, -0.25, false)
	end
	for _, s in { -1, 1 } do
		C(corde, "Shimenawa_Gland", "Corde_Paille", 0.18, 1.4, 6.3 * s, 8.6, tz + 0.45, false)
	end
	torii.Parent = base
end

-- 7. Panneau du propriétaire (devant la zone, à gauche)
local function construirePanneau(base: Model)
	local panneau = groupe(nil, "Panneau")
	local px, pz = -14, 55.5
	for _, s in { -1, 1 } do
		B(panneau, "Panneau_Poteau", "Bois_Sombre", 0.6, 7, 0.6, px + 4.3 * s, 3.5, pz)
		C(panneau, "Panneau_Chaine", "Metal_Sombre", 0.05, 0.8, px + 3 * s, 6.05, pz, false)
	end
	B(panneau, "Panneau_Traverse", "Bois_Sombre", 10, 0.5, 0.7, px, 6.6, pz)
	B(panneau, "Panneau_Toit", "Bois_Sombre", 11.4, 0.4, 1.6, px, 7.1, pz)
	B(panneau, "Panneau_Cadre", "Laque", 7.6, 3.4, 0.3, px, 4.6, pz)
	local face = B(panneau, "Panneau_Face", "Bois_Clair", 7, 2.8, 0.32, px, 4.6, pz)

	local gui = Instance.new("SurfaceGui")
	gui.Name = "Texte"
	gui.Face = Enum.NormalId.Back -- +Z local = côté entrée (Back d'une pièce non tournée)
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 50
	gui.LightInfluence = 0.3
	gui.MaxDistance = 150
	gui.Parent = face
	local nom =
		etiquette(gui, "NomProprietaire", "Base libre", "2B1D1A", UDim2.fromScale(0.05, 0.1), UDim2.fromScale(0.9, 0.5))
	nom.TextWrapped = true
	etiquette(gui, "Niveau", "", "8A3A2A", UDim2.fromScale(0.15, 0.62), UDim2.fromScale(0.7, 0.28))
	panneau.Parent = base
end

-- 8. Socles de personnages
local Z_PAIRES = { 36, 20, 4, -12, -28 }
local function construireSocles(base: Model)
	local socles = groupe(nil, "Socles")
	for n = 1, 10 do
		local s = if n % 2 == 1 then -1 else 1
		local x, z = 22 * s, Z_PAIRES[math.ceil(n / 2)]
		local m = groupe(socles, `Socle_{n}`)
		B(m, "Socle_Base", "Pierre_Ardoise", 10, 0.6, 10, x, 2.1, z)
		C(m, "Socle_Plateau", "Pierre_Claire", 4, 0.6, x, 2.7, z)
		local anneau = C(m, "Neon_Socle_Anneau", "Socle_Libre", 4.12, 0.16, x, 2.9, z, false)
		anneau.CanQuery = false
		C(m, "Socle_Centre_Or", "Metal_Or", 1.4, 0.1, x, 3.05, z)
		for _, cx in { -1, 1 } do
			for _, cz in { -1, 1 } do
				B(m, "Socle_Coin_Or", "Metal_Or", 0.7, 0.7, 0.7, x + 4.6 * cx, 2.5, z + 4.6 * cz, 0, math.rad(45), 0)
			end
		end

		-- Stèle numérotée, côté allée
		local sx = x - 5.6 * s
		local stele = B(m, "Stele", "Pierre_Claire", 0.6, 2.2, 2.8, sx, 2.9, z)
		B(m, "Stele_Chapeau", "Bois_Sombre", 0.9, 0.3, 3.2, sx, 4.15, z)
		local gui = Instance.new("SurfaceGui")
		gui.Name = "Numero"
		gui.Face = if s < 0 then Enum.NormalId.Right else Enum.NormalId.Left -- face tournée vers l'allée (x = 0)
		gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		gui.PixelsPerStud = 50
		gui.LightInfluence = 0.3
		gui.MaxDistance = 120
		gui.Parent = stele
		local carre = Instance.new("Frame")
		carre.Name = "Carre"
		carre.AnchorPoint = Vector2.new(0.5, 0.5)
		carre.Position = UDim2.fromScale(0.5, 0.45)
		carre.Size = UDim2.fromOffset(80, 80)
		carre.BackgroundColor3 = Color3.fromHex("D9A441")
		carre.Parent = gui
		local coin = Instance.new("UICorner")
		coin.CornerRadius = UDim.new(0.2, 0)
		coin.Parent = carre
		etiquette(carre, "Texte", tostring(n), "2B1D1A", UDim2.fromScale(0.1, 0.1), UDim2.fromScale(0.8, 0.8))

		-- Point de pose : dessus du centre doré (y 3,1) ; lu par BaseService (attribut Index)
		local pose = B(m, "Emplacement", "Invisible", 8, 0.1, 8, x, 3.05, z, 0, 0, 0, false)
		pose.CanQuery = false
		pose:SetAttribute("Index", n)
		lumiere(pose, "FFFFFF", 1, 8, Vector3.new(x, 3.8, z)).Enabled = false

		-- Étiquette d'un socle occupé (nom, rareté, gain) et d'un socle libre
		local occupe = billboard(pose, "Etiquette", x, 11.2, z, 7, 2.6)
		occupe.Enabled = false
		etiquette(occupe, "Nom", "", "FFFFFF", UDim2.fromScale(0, 0), UDim2.fromScale(1, 0.4), "1C1733")
		etiquette(occupe, "Rarete", "", "FFFFFF", UDim2.fromScale(0, 0.4), UDim2.fromScale(1, 0.3), "1C1733")
		etiquette(occupe, "Gain", "", "FFD34D", UDim2.fromScale(0, 0.7), UDim2.fromScale(1, 0.3), "1C1733")
		local libre = billboard(pose, "Libre", x, 5.8, z, 5, 0.9)
		etiquette(libre, "Texte", "Socle libre", "B9B6C6", UDim2.fromScale(0, 0), UDim2.fromScale(1, 1), "1C1733")
	end
	socles.Parent = base
end

-- 9. Collecte (juste après l'entrée, à droite)
local function construireCollecte(base: Model)
	local collecte = groupe(nil, "Collecte")
	CollectionService:AddTag(collecte, "CollecteAnimee") -- colonne et pièces animées par le client (ZoneCollecte)
	local cx, cz = 12, 45
	C(collecte, "Collecte_Socle", "Pierre_Ardoise", 3, 0.3, cx, 1.95, cz)
	local disque = C(collecte, "Collecte_Disque_Or", "Metal_Or", 2.6, 0.2, cx, 2.2, cz)
	disque.CanTouch = true
	CollectionService:AddTag(disque, "Collecteur")
	neon(C(collecte, "Neon_Collecte_Anneau", "Neon_Collecte", 2.78, 0.14, cx, 2.25, cz))

	-- « $ » peint sur le dessus du disque (face Right = haut d'un cylindre debout) : pas d'image envoyée
	local gui = Instance.new("SurfaceGui")
	gui.Name = "Dollar"
	gui.Face = Enum.NormalId.Right
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 40
	gui.LightInfluence = 0.5
	gui.Parent = disque
	local rond = Instance.new("Frame")
	rond.AnchorPoint = Vector2.new(0.5, 0.5)
	rond.Position = UDim2.fromScale(0.5, 0.5)
	rond.Size = UDim2.fromScale(0.62, 0.62)
	rond.BackgroundColor3 = Color3.fromHex("FFD34D")
	rond.Parent = gui
	local arrondi = Instance.new("UICorner")
	arrondi.CornerRadius = UDim.new(0.5, 0)
	arrondi.Parent = rond
	etiquette(rond, "Texte", "$", "8A5A10", UDim2.fromScale(0.15, 0.1), UDim2.fromScale(0.7, 0.8))

	local colonne = neon(C(collecte, "Colonne", "Neon_Collecte", 2.5, 4, cx, 4.3, cz, false))
	colonne.Transparency = 0.85
	colonne.CanTouch = false
	local pieces = groupe(collecte, "Pieces", "Folder")
	for i = 1, 3 do
		local p = neon(CX(pieces, `Piece_{i}`, "Neon_Collecte", 0.5, 0.12, cx, 3.6, cz, false))
		p:SetAttribute("Index", i - 1)
	end
	lumiere(disque, "FFD34D", 2, 9, Vector3.new(cx, 3.8, cz))

	-- Gerbe de pièces à la collecte : émise par le client (Emit n'est pas répliqué)
	local gerbe = Instance.new("ParticleEmitter")
	gerbe.Name = "Gerbe"
	gerbe.Color = ColorSequence.new(Color3.fromHex("FFD34D"))
	gerbe.LightEmission = 0.6
	gerbe.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(1, 0.1) })
	gerbe.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) })
	gerbe.Lifetime = NumberRange.new(0.6, 1)
	gerbe.Speed = NumberRange.new(10, 16)
	gerbe.SpreadAngle = Vector2.new(35, 35)
	gerbe.Acceleration = Vector3.new(0, -30, 0)
	gerbe.Rotation = NumberRange.new(0, 360)
	gerbe.RotSpeed = NumberRange.new(-200, 200)
	gerbe.EmissionDirection = Enum.NormalId.Right -- vers le haut (cylindre debout)
	gerbe.Rate = 0
	gerbe.Parent = disque

	local gui2 = billboard(disque, "Etiquette", cx, 8.4, cz, 7, 2.2)
	etiquette(gui2, "Montant", "", "FFD34D", UDim2.fromScale(0, 0), UDim2.fromScale(1, 0.62), "5A3A00")
	etiquette(
		gui2,
		"Aide",
		"Marche pour collecter",
		"FFFFFF",
		UDim2.fromScale(0, 0.64),
		UDim2.fromScale(1, 0.36),
		"1C1733"
	)
	collecte.Parent = base
end

-- 10. Pupitre d'amélioration (près de l'autel, à gauche) : visuel ; coût des niveaux à définir (wiki Machine-RNG)
local function construireAmelioration(base: Model)
	local amelioration = groupe(nil, "Amelioration")
	local ux, uz = -12, -22
	B(amelioration, "Pupitre_Socle", "Pierre_Ardoise", 3.2, 0.4, 3.2, ux, 2.0, uz)
	local pied = B(amelioration, "Pupitre_Pied", "Pierre_Claire", 2, 2.6, 2, ux, 3.5, uz)
	local plateau = groupe(amelioration, "Pupitre_Plateau")
	local pivot = CFrame.new(ux, 5.0, uz) * CFrame.Angles(0.35, 0, 0) -- incliné vers l'entrée (+Z)
	mettre(
		piece("Pupitre_Plateau_Fer", "Metal_Sombre", Enum.PartType.Block, Vector3.new(2.8, 0.35, 2.4), true),
		pivot,
		plateau
	)
	mettre(
		piece("Pupitre_Lisere_Or", "Metal_Or", Enum.PartType.Block, Vector3.new(3, 0.12, 2.6), true),
		pivot * CFrame.new(0, -0.2, 0),
		plateau
	)
	local bouton = mettre(
		piece(
			"Neon_Bouton_Amelioration",
			"Neon_Amelioration",
			Enum.PartType.Cylinder,
			Vector3.new(0.35, 1.6, 1.6),
			false
		),
		pivot * CFrame.new(0, 0.3, 0) * CFrame.Angles(0, 0, math.rad(90)),
		plateau
	)
	neon(bouton)
	lumiere(pied, "3DDC84", 1, 7, Vector3.new(ux, 5.8, uz + 1))
	local gui = billboard(pied, "Etiquette", ux, 9.2, uz, 6, 2.4)
	etiquette(gui, "Titre", "Améliorer l'autel", "FFFFFF", UDim2.fromScale(0, 0), UDim2.fromScale(1, 0.4), "1C1733")
	etiquette(gui, "Niveau", "Niv. 1 → 2", "3DDC84", UDim2.fromScale(0, 0.4), UDim2.fromScale(1, 0.3), "1C1733")
	etiquette(gui, "Prix", "Bientôt", "FFD34D", UDim2.fromScale(0, 0.7), UDim2.fromScale(1, 0.3), "1C1733")
	amelioration.Parent = base
end

-- 11. Bannières nobori
local function construireBannieres(base: Model)
	local bannieres = groupe(nil, "Bannieres")
	for _, x in { -43, 43 } do
		for _, z in { 44, 4, -36 } do
			local m = groupe(bannieres, "Banniere")
			C(m, "Banniere_Mat", "Metal_Sombre", 0.12, 9, x, 6.3, z)
			B(m, "Banniere_Barre", "Metal_Sombre", 0.1, 0.1, 1.9, x, 10.5, z + 0.95, 0, 0, 0, false)
			B(m, "Banniere_Tissu", "Banniere_Tissu", 0.08, 6, 1.8, x, 7.4, z + 0.95, 0, 0, 0, false)
			B(m, "Banniere_Bande", "Banniere_Bande", 0.1, 4.2, 0.5, x, 7.2, z + 0.95, 0, 0, 0, false)
			S(m, "Banniere_Pointe", "Metal_Or", 0.2, x, 10.9, z)
		end
	end
	bannieres.Parent = base
end

----------------------------------------------------------------------------------------------------
local function construire(base: Model)
	local centre = base:FindFirstChild("Centre")
	if not (centre and centre:IsA("BasePart")) then
		warn(`[Zone] pas de Centre dans {base:GetFullName()}`)
		return
	end
	origine = centre.CFrame * CFrame.new(0, -centre.Size.Y / 2, 0)

	-- Sauvegarde de l'ancienne base (une seule fois), puis ménage
	if base:GetAttribute("ZoneSanctuaire") == nil then
		local sauvegarde = Instance.new("Model")
		sauvegarde.Name = base.Name
		for _, nom in ANCIENS do
			local ancien = base:FindFirstChild(nom)
			if ancien then
				ancien.Parent = sauvegarde
			end
		end
		local dossier = ServerStorage:FindFirstChild("Sauvegarde_AvantZoneSanctuaire")
		if not dossier then
			dossier = Instance.new("Folder")
			dossier.Name = "Sauvegarde_AvantZoneSanctuaire"
			dossier.Parent = ServerStorage
		end
		sauvegarde.Parent = dossier
	end
	for _, nom in CONSTRUITS do
		local ancien = base:FindFirstChild(nom)
		if ancien then
			ancien:Destroy()
		end
	end
	task.wait()

	for _, etape in
		{
			construireSol,
			construireAllee,
			construireLanternes,
			construireCloture,
			construireTorii,
			construirePanneau,
			construireSocles,
			construireCollecte,
			construireAmelioration,
			construireBannieres,
		}
	do
		etape(base)
		task.wait()
	end

	-- Point d'apparition devant les marches, tourné vers l'autel (-Z)
	local apparition = piece("PointApparition", "Invisible", Enum.PartType.Block, Vector3.new(4, 1, 4), false)
	apparition.CanQuery = false
	mettre(apparition, CFrame.new(0, 0.5, 58), base)

	base:SetAttribute("ZoneSanctuaire", true)
	base:SetAttribute("AutelZ", AUTEL_Z)
	print(`[Zone] construite dans {base:GetFullName()} ({#base:GetDescendants()} objets)`)
end

for _, base in CollectionService:GetTagged("BaseJoueur") do
	if base:IsA("Model") then
		construire(base)
	end
end
