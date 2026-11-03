--!strict
-- Décore le dessus de l'île volante (Workspace.Ile.Decor), dans le style du Hub (lancé par MCP, Edit).
-- Laisse libres le Hub, les 7 emplacements de base (Hub.EmplacementsBases) et les 7 chemins.
-- Relançable : supprime l'ancien Ile.Decor avant de reconstruire.

local ile = workspace:FindFirstChild("Ile") :: Model
local hub = workspace:FindFirstChild("Hub") :: Model
assert(ile and hub, "Workspace.Ile et Workspace.Hub sont nécessaires")

local CENTRE_ILE = Vector3.new(-14, 0, 0)
local plateau = hub:FindFirstChild("Plateau") :: BasePart
local CENTRE_HUB = Vector3.new(plateau.Position.X, 0, plateau.Position.Z)
local RAYON_HUB = 86 -- plateau, bordure et torii
local RAYON_UTILE = 252 -- muret à 261
local SOL_Y = 1
local alea = Random.new(31102026)

local function rgb(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local C = {
	herbeClaire = rgb(146, 190, 104),
	herbeFoncee = rgb(112, 160, 86),
	buissons = { rgb(86, 136, 72), rgb(100, 152, 80), rgb(74, 120, 66) },
	pierres = { rgb(201, 190, 169), rgb(176, 166, 149), rgb(158, 148, 133), rgb(142, 132, 118) },
	mousse = rgb(96, 140, 74),
	dalle = rgb(217, 208, 191),
	gravier = rgb(232, 224, 207),
	eau = rgb(70, 150, 196),
	nenuphar = rgb(92, 156, 84),
	fleurs = { rgb(250, 246, 235), rgb(255, 206, 120), rgb(232, 98, 72) },
	bois = rgb(176, 112, 76),
	boisFonce = rgb(126, 78, 52),
	pied = rgb(120, 72, 56),
	bambou = rgb(138, 176, 96),
	bambouNoeud = rgb(112, 146, 78),
	bambouFeuilles = rgb(96, 150, 76),
}

local function piece(
	parent: Instance,
	nom: string,
	taille: Vector3,
	cf: CFrame,
	couleur: Color3,
	opts: { [string]: any }?,
	forme: Enum.PartType?
): Part
	local p = Instance.new("Part")
	p.Name = nom
	p.Anchored = true
	p.Size = taille
	p.CFrame = cf
	p.Color = couleur
	p.Material = Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = false
	if forme then
		p.Shape = forme
	end
	if opts then
		for k, v in opts do
			(p :: any)[k] = v
		end
	end
	p.Parent = parent
	return p
end

-- Disque plat posé sur le sol (cylindre couché), dessus à SOL_Y + dessus
local function disque(
	parent: Instance,
	nom: string,
	pos: Vector3,
	r: number,
	dessus: number,
	couleur: Color3,
	opts: { [string]: any }?
): Part
	local ep = 0.2
	return piece(
		parent,
		nom,
		Vector3.new(ep, r * 2, r * 2),
		CFrame.new(pos.X, SOL_Y + dessus - ep / 2, pos.Z) * CFrame.Angles(0, 0, math.rad(90)),
		couleur,
		opts,
		Enum.PartType.Cylinder
	)
end

local function auHasard<T>(liste: { T }): T
	return liste[alea:NextInteger(1, #liste)]
end

-- Zones à laisser libres
local bases: { CFrame } = {}
for _, b in (hub:FindFirstChild("EmplacementsBases") :: Folder):GetChildren() do
	table.insert(bases, (b :: BasePart).CFrame)
end
local chemins: { BasePart } = {}
for _, ch in (hub:FindFirstChild("Chemins") :: Folder):GetChildren() do
	table.insert(chemins, ch :: BasePart)
end
local occupe: { { p: Vector3, r: number } } = {}

local function plat(v: Vector3): Vector3
	return Vector3.new(v.X, 0, v.Z)
end

-- p libre pour un objet de rayon r (enclos de base : x ±47, z -52..+69 en repère local, +Z vers le Hub)
local function libre(p: Vector3, r: number, ignorerOccupe: boolean?): boolean
	p = plat(p)
	if (p - CENTRE_ILE).Magnitude > RAYON_UTILE - r then
		return false
	end
	if (p - CENTRE_HUB).Magnitude < RAYON_HUB + r then
		return false
	end
	for _, cf in bases do
		local l = cf:PointToObjectSpace(Vector3.new(p.X, cf.Position.Y, p.Z))
		if math.abs(l.X) < 54 + r and l.Z > -60 - r and l.Z < 80 + r then
			return false
		end
	end
	for _, ch in chemins do
		local l = ch.CFrame:PointToObjectSpace(Vector3.new(p.X, ch.Position.Y, p.Z))
		if math.abs(l.X) < ch.Size.X / 2 + 5 + r and math.abs(l.Z) < ch.Size.Z / 2 + 4 + r then
			return false
		end
	end
	if not ignorerOccupe then
		for _, o in occupe do
			if (o.p - p).Magnitude < o.r + r then
				return false
			end
		end
	end
	return true
end

local function reserver(p: Vector3, r: number)
	table.insert(occupe, { p = plat(p), r = r })
end

local function surCercle(r: number, angle: number): Vector3
	return Vector3.new(CENTRE_ILE.X + math.cos(angle) * r, 0, CENTRE_ILE.Z + math.sin(angle) * r)
end

-- Gabarits pris dans le décor du Hub
local decorHub = hub:FindFirstChild("Decor") :: Folder
local cerisiers = (decorHub:FindFirstChild("Cerisiers") :: Folder):GetChildren()
local modeleLanterne = Instance.new("Model")
modeleLanterne.Name = "Lanterne"
do
	local torii = (decorHub:FindFirstChild("Torii") :: Folder):GetChildren()[1]
	local mesh = torii:FindFirstChild("LanterneMesh") :: BasePart
	for _, d in torii:GetChildren() do
		if d:IsA("BasePart") and (plat(d.Position) - plat(mesh.Position)).Magnitude < 1.5 then
			d:Clone().Parent = modeleLanterne
		end
	end
	local bas = mesh.Position.Y - mesh.Size.Y / 2
	modeleLanterne.WorldPivot = CFrame.new(mesh.Position.X, bas, mesh.Position.Z)
end

local function lanterne(parent: Instance, pos: Vector3, regard: Vector3?)
	local l = modeleLanterne:Clone()
	local cf = CFrame.new(pos.X, SOL_Y, pos.Z)
	if regard then
		cf = CFrame.lookAt(cf.Position, Vector3.new(regard.X, SOL_Y, regard.Z))
	end
	l:PivotTo(cf)
	l.Parent = parent
	reserver(pos, 3)
end

local function cerisier(parent: Instance, pos: Vector3, echelle: number)
	local modele = cerisiers[alea:NextInteger(1, #cerisiers)]:Clone() :: Model
	modele.Name = "Cerisier"
	local tronc = modele:FindFirstChild("Collision") :: BasePart
	local petales = modele:FindFirstChild("PetalesSol") :: BasePart
	modele:ScaleTo(modele:GetScale() * echelle)
	local dy = SOL_Y + 0.03 - (petales.Position.Y - petales.Size.X / 2)
	local dxz = plat(pos) - plat(tronc.Position)
	modele:PivotTo(
		CFrame.new(dxz.X, dy, dxz.Z)
			* CFrame.new(tronc.Position)
			* CFrame.Angles(0, math.rad(alea:NextNumber(0, 360)), 0)
			* CFrame.new(-tronc.Position)
			* modele:GetPivot()
	)
	modele.Parent = parent
	reserver(pos, 7 * echelle)
end

local function banc(parent: Instance, pos: Vector3, regard: Vector3)
	local cf = CFrame.lookAt(Vector3.new(pos.X, SOL_Y, pos.Z), Vector3.new(regard.X, SOL_Y, regard.Z))
	local m = Instance.new("Model")
	m.Name = "Banc"
	local dur = { CanCollide = true, CanQuery = true }
	piece(m, "Assise", Vector3.new(7, 0.5, 2), cf * CFrame.new(0, 2.2, 0), C.bois, dur)
	piece(
		m,
		"Dossier",
		Vector3.new(7, 1.6, 0.4),
		cf * CFrame.new(0, 3.4, 1.0) * CFrame.Angles(math.rad(-10), 0, 0),
		C.boisFonce,
		dur
	)
	for _, x in { -2.8, 2.8 } do
		piece(m, "Pied", Vector3.new(0.6, 1.95, 1.8), cf * CFrame.new(x, 1.0, 0), C.pied, dur)
	end
	m.Parent = parent
	reserver(pos, 5)
end

local function rocher(parent: Instance, pos: Vector3, taille: number, avecMousse: boolean)
	local n = alea:NextInteger(2, 3)
	for i = 1, n do
		local t = taille * (if i == 1 then 1 else alea:NextNumber(0.45, 0.7))
		local decalage = if i == 1
			then Vector3.zero
			else Vector3.new(alea:NextNumber(-1, 1), 0, alea:NextNumber(-1, 1)).Unit * taille * 0.7
		local cf = CFrame.new(pos.X + decalage.X, SOL_Y + t * 0.3, pos.Z + decalage.Z)
			* CFrame.Angles(
				math.rad(alea:NextNumber(-20, 20)),
				math.rad(alea:NextNumber(0, 360)),
				math.rad(alea:NextNumber(-20, 20))
			)
		local p = piece(
			parent,
			"Rocher",
			Vector3.new(t * alea:NextNumber(1, 1.4), t * alea:NextNumber(0.7, 1), t),
			cf,
			auHasard(C.pierres),
			{ CanCollide = t > 2.5, CanQuery = t > 2.5 }
		)
		if avecMousse and i == 1 then
			piece(
				parent,
				"Mousse",
				Vector3.new(p.Size.X * 0.8, 0.3, p.Size.Z * 0.8),
				p.CFrame * CFrame.new(0, p.Size.Y / 2, 0),
				C.mousse,
				{ CastShadow = false }
			)
		end
	end
	reserver(pos, taille * 1.3)
end

local function buisson(parent: Instance, pos: Vector3, taille: number)
	local couleur = auHasard(C.buissons)
	local n = alea:NextInteger(2, 4)
	for i = 1, n do
		local t = taille * (if i == 1 then 1 else alea:NextNumber(0.55, 0.8))
		local d = if i == 1
			then Vector3.zero
			else Vector3.new(alea:NextNumber(-1, 1), 0, alea:NextNumber(-1, 1)).Unit * taille * 0.6
		piece(
			parent,
			"Buisson",
			Vector3.new(t * 1.2, t, t * 1.2),
			CFrame.new(pos.X + d.X, SOL_Y + t * 0.35, pos.Z + d.Z),
			couleur,
			nil,
			Enum.PartType.Ball
		)
	end
	reserver(pos, taille * 1.1)
end

local function fleurs(parent: Instance, pos: Vector3)
	local couleur = auHasard(C.fleurs)
	for _ = 1, alea:NextInteger(5, 8) do
		local d = Vector3.new(alea:NextNumber(-2.5, 2.5), 0, alea:NextNumber(-2.5, 2.5))
		local t = alea:NextNumber(0.5, 0.8)
		piece(
			parent,
			"Fleur",
			Vector3.new(t, t * 0.7, t),
			CFrame.new(pos + d + Vector3.new(0, SOL_Y + 0.5, 0)),
			couleur,
			{ CastShadow = false },
			Enum.PartType.Ball
		)
		piece(
			parent,
			"Tige",
			Vector3.new(0.15, 0.5, 0.15),
			CFrame.new(pos + d + Vector3.new(0, SOL_Y + 0.2, 0)),
			C.herbeFoncee,
			{ CastShadow = false }
		)
	end
	reserver(pos, 3)
end

local function touffe(parent: Instance, pos: Vector3)
	for k = 1, 3 do
		local h = alea:NextNumber(1, 1.8)
		local w = Instance.new("WedgePart")
		w.Name = "Touffe"
		w.Anchored, w.CanCollide, w.CanTouch, w.CanQuery, w.CastShadow = true, false, false, false, false
		w.Material = Enum.Material.SmoothPlastic
		w.Color = C.herbeFoncee
		w.Size = Vector3.new(0.3, h, 0.6)
		w.CFrame = CFrame.new(pos.X, SOL_Y + h / 2, pos.Z)
			* CFrame.Angles(0, math.rad(k * 120 + alea:NextNumber(-20, 20)), 0)
			* CFrame.new(0, 0, 0.3)
			* CFrame.Angles(math.rad(alea:NextNumber(-12, 12)), 0, 0)
		w.Parent = parent
	end
end

local function bambous(parent: Instance, pos: Vector3)
	local m = Instance.new("Model")
	m.Name = "Bambous"
	for _ = 1, alea:NextInteger(5, 8) do
		local d = Vector3.new(alea:NextNumber(-2.5, 2.5), 0, alea:NextNumber(-2.5, 2.5))
		local h = alea:NextNumber(12, 20)
		local base = CFrame.new(pos.X + d.X, SOL_Y, pos.Z + d.Z)
			* CFrame.Angles(math.rad(alea:NextNumber(-6, 6)), 0, math.rad(alea:NextNumber(-6, 6)))
		piece(
			m,
			"Tige",
			Vector3.new(h, 0.6, 0.6),
			base * CFrame.new(0, h / 2, 0) * CFrame.Angles(0, 0, math.rad(90)),
			C.bambou,
			{
				CanCollide = true,
				CanQuery = true,
			},
			Enum.PartType.Cylinder
		)
		for y = 3, h - 1, 3 do
			piece(
				m,
				"Noeud",
				Vector3.new(0.2, 0.72, 0.72),
				base * CFrame.new(0, y, 0) * CFrame.Angles(0, 0, math.rad(90)),
				C.bambouNoeud,
				{
					CastShadow = false,
				},
				Enum.PartType.Cylinder
			)
		end
		for k = 1, 3 do
			piece(
				m,
				"Feuilles",
				Vector3.new(alea:NextNumber(2.5, 4), 0.15, 0.9),
				base
					* CFrame.new(0, h - k * 1.6, 0)
					* CFrame.Angles(0, math.rad(alea:NextNumber(0, 360)), math.rad(-25))
					* CFrame.new(1.6, 0, 0),
				C.bambouFeuilles,
				{ CastShadow = false }
			)
		end
	end
	m.Parent = parent
	reserver(pos, 4.5)
end

-- Éléments par intervalle entre deux bases
local function bosquet(parent: Instance, centre: Vector3)
	for _ = 1, 30 do
		if #parent:GetChildren() >= 4 then
			break
		end
		local p = centre + Vector3.new(alea:NextNumber(-22, 22), 0, alea:NextNumber(-22, 22))
		local e = alea:NextNumber(1.0, 1.35)
		if libre(p, 7 * e) then
			cerisier(parent, p, e)
		end
	end
	for _ = 1, 4 do
		local p = centre + Vector3.new(alea:NextNumber(-26, 26), 0, alea:NextNumber(-26, 26))
		if libre(p, 3) then
			fleurs(parent, p)
		end
	end
end

local function etang(parent: Instance, centre: Vector3)
	local r = 13
	disque(parent, "Eau", centre, r, 0.12, C.eau, { Reflectance = 0.25 })
	disque(parent, "Fond", centre, r + 1.2, 0.08, C.pierres[3], { CastShadow = false })
	local n = 18
	for i = 1, n do
		local a = i / n * math.pi * 2 + alea:NextNumber(-0.08, 0.08)
		local p = centre + Vector3.new(math.cos(a), 0, math.sin(a)) * (r + 0.8)
		local t = alea:NextNumber(2.2, 3.4)
		piece(
			parent,
			"PierreBord",
			Vector3.new(t * 1.3, t * 0.55, t),
			CFrame.new(p.X, SOL_Y + t * 0.18, p.Z)
				* CFrame.Angles(0, -a + math.rad(alea:NextNumber(-15, 15)), math.rad(alea:NextNumber(-8, 8))),
			auHasard(C.pierres),
			{ CanCollide = true, CanQuery = true }
		)
	end
	for _ = 1, 6 do
		local a = alea:NextNumber(0, math.pi * 2)
		local p = centre + Vector3.new(math.cos(a), 0, math.sin(a)) * alea:NextNumber(2, r - 3)
		local t = alea:NextNumber(1.2, 2)
		disque(parent, "Nenuphar", p, t, 0.18, C.nenuphar, { CastShadow = false })
		if alea:NextNumber() < 0.5 then
			piece(
				parent,
				"FleurNenuphar",
				Vector3.new(0.8, 0.6, 0.8),
				CFrame.new(p.X, SOL_Y + 0.45, p.Z),
				C.fleurs[1],
				{ CastShadow = false },
				Enum.PartType.Ball
			)
		end
	end
	reserver(centre, r + 3)
	local vers = (plat(centre) - CENTRE_ILE).Unit
	lanterne(parent, centre - vers * (r + 4) + vers:Cross(Vector3.yAxis) * 6, centre)
	rocher(parent, centre + vers * (r + 3) - vers:Cross(Vector3.yAxis) * 7, 3, true)
end

local function belvedere(parent: Instance, angle: number)
	local bord = surCercle(236, angle)
	local dehors = (bord - CENTRE_ILE).Unit
	local cote = dehors:Cross(Vector3.yAxis)
	disque(parent, "Dalle", bord, 10, 0.15, C.dalle)
	disque(parent, "DalleBord", bord, 10.8, 0.1, C.pierres[2], { CastShadow = false })
	reserver(bord, 11)
	-- 2 bancs face à la mer, 2 lanternes sur les côtés, un cerisier derrière
	for _, s in { -1, 1 } do
		local p = bord + cote * s * 4 + dehors * 2
		banc(parent, p, p + dehors * 10)
		lanterne(parent, bord + cote * s * 9.5 + dehors * 3, bord)
	end
	local derriere = bord - dehors * 16 + cote * 9
	if libre(derriere, 8) then
		cerisier(parent, derriere, 1.25)
	end
	-- pas japonais vers l'intérieur
	for i = 1, 12 do
		local p = bord - dehors * (11 + i * 4.5) + cote * math.sin(i * 0.7) * 2.5
		if not libre(p, 1.5, true) then
			break
		end
		disque(parent, "PasJaponais", p, alea:NextNumber(1.4, 1.9), 0.12, C.dalle, { CastShadow = false })
	end
end

local function rocaille(parent: Instance, centre: Vector3)
	local r = 14
	disque(parent, "Gravier", centre, r, 0.1, C.gravier, { CastShadow = false })
	-- sillons ratissés en anneaux
	for k = 1, 3 do
		local rr = r - k * 3.2
		local n = math.floor(rr * 2.2)
		for i = 1, n do
			local a = i / n * math.pi * 2
			local p = centre + Vector3.new(math.cos(a), 0, math.sin(a)) * rr
			piece(
				parent,
				"Sillon",
				Vector3.new(2 * math.pi * rr / n + 0.1, 0.06, 0.25),
				CFrame.new(p.X, SOL_Y + 0.13, p.Z) * CFrame.Angles(0, -a - math.pi / 2, 0),
				C.pierres[1],
				{ CastShadow = false }
			)
		end
	end
	for i = 1, 16 do
		local a = i / 16 * math.pi * 2
		local p = centre + Vector3.new(math.cos(a), 0, math.sin(a)) * (r + 0.6)
		piece(
			parent,
			"Bordure",
			Vector3.new(5.6, 0.6, 1.2),
			CFrame.new(p.X, SOL_Y + 0.3, p.Z) * CFrame.Angles(0, -a - math.pi / 2, 0),
			C.pierres[3]
		)
	end
	rocher(parent, centre, 4.2, true)
	rocher(parent, centre + Vector3.new(6, 0, 4), 2.6, true)
	rocher(parent, centre + Vector3.new(-5, 0, -6), 2.2, false)
	reserver(centre, r + 2)
	local vers = (plat(centre) - CENTRE_ILE).Unit
	lanterne(parent, centre + vers:Cross(Vector3.yAxis) * (r + 4), centre)
end

-- Construction
local ancien = ile:FindFirstChild("Decor")
if ancien then
	ancien:Destroy()
end
local decor = Instance.new("Folder")
decor.Name = "Decor"

-- 1. Éléments principaux, un par intervalle entre deux bases
local angles: { number } = {}
for _, cf in bases do
	local v = cf.Position - CENTRE_ILE
	table.insert(angles, math.atan2(v.Z, v.X))
end
table.sort(angles)
local TYPES = { "Bosquet", "Etang", "Belvedere", "Rocaille" }
for i, a in angles do
	local suivant = angles[i % #angles + 1]
	if suivant < a then
		suivant += math.pi * 2
	end
	local milieu = (a + suivant) / 2
	local type = TYPES[(i - 1) % #TYPES + 1]
	local dossier = Instance.new("Folder")
	dossier.Name = type .. i
	dossier.Parent = decor
	if type == "Bosquet" then
		bosquet(dossier, surCercle(205, milieu))
	elseif type == "Etang" then
		etang(dossier, surCercle(200, milieu))
	elseif type == "Belvedere" then
		belvedere(dossier, milieu)
	else
		rocaille(dossier, surCercle(200, milieu))
	end
	-- un 2e petit groupe de cerisiers près du Hub, entre deux chemins
	local pres = surCercle(alea:NextNumber(108, 122), milieu + alea:NextNumber(-0.12, 0.12))
	if libre(pres, 8) then
		cerisier(dossier, pres, alea:NextNumber(0.9, 1.1))
	end
	task.wait()
end

-- 2. Détails semés partout où c'est libre
local function semer(nom: string, combien: number, rayon: number, faire: (Instance, Vector3) -> ())
	local dossier = Instance.new("Folder")
	dossier.Name = nom
	dossier.Parent = decor
	local poses, essais = 0, 0
	while poses < combien and essais < combien * 40 do
		essais += 1
		local p = surCercle(math.sqrt(alea:NextNumber()) * RAYON_UTILE, alea:NextNumber(0, math.pi * 2))
		if libre(p, rayon) then
			faire(dossier, p)
			poses += 1
		end
	end
	task.wait()
end

semer("TachesHerbe", 60, 6, function(parent, p)
	local claire = alea:NextNumber() < 0.5
	disque(
		parent,
		"TacheHerbe",
		p,
		alea:NextNumber(6, 16),
		alea:NextNumber(0.02, 0.06),
		if claire then C.herbeClaire else C.herbeFoncee,
		{ CastShadow = false }
	)
end)
semer("Cerisiers", 12, 8, function(parent, p)
	cerisier(parent, p, alea:NextNumber(0.75, 1.05))
end)
semer("Bambous", 10, 5, bambous)
semer("Lanternes", 10, 3, function(parent, p)
	lanterne(parent, p, CENTRE_HUB)
end)
semer("Buissons", 110, 4, function(parent, p)
	buisson(parent, p, alea:NextNumber(2.2, 3.8))
end)
semer("Rochers", 45, 4, function(parent, p)
	rocher(parent, p, alea:NextNumber(1.6, 3.2), alea:NextNumber() < 0.5)
end)
semer("Fleurs", 70, 3, fleurs)
semer("Touffes", 260, 1, touffe)

decor.Parent = ile
return "Décor de l'île : " .. #decor:GetDescendants() .. " objets"
