--!strict
-- Construit l'île volante (Workspace.Ile) autour du Hub, dans la place Studio (lancé par MCP, Edit).
-- Remplace Wall / Wall_Grass / Base / Baseplate, rangés dans ServerStorage.Sauvegarde_AvantIleVolante.
-- Relançable : supprime l'ancienne Workspace.Ile avant de reconstruire.

local ServerStorage = game:GetService("ServerStorage")

local CENTRE = Vector3.new(-14, 0, 0) -- centre du Hub (et de l'ancien anneau de murs)
local RAYON = 265 -- bord de l'île (bases jusqu'à ≈ 236)
local SOL_Y = 1 -- dessus du sol marchable (= ancien Base)
local MUR_HAUTEUR = 120
local alea = Random.new(20261031)

local function rgb(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

local C = {
	herbe = rgb(128, 176, 96),
	herbeFoncee = rgb(104, 152, 80),
	terre = rgb(140, 98, 70),
	terreFoncee = rgb(120, 72, 56),
	pierres = { rgb(201, 190, 169), rgb(176, 166, 149), rgb(158, 148, 133), rgb(142, 132, 118) },
	pierreProfonde = rgb(112, 104, 96),
	muret = rgb(207, 198, 182),
	chaperon = rgb(92, 95, 107),
	or_ = rgb(255, 196, 90),
}

-- Strates du dessous : {y du haut, y du bas, rayon}
local STRATES = {
	{ SOL_Y - 4, -12, RAYON - 3 },
	{ -12, -40, 250 },
	{ -40, -78, 220 },
	{ -78, -120, 178 },
	{ -120, -162, 128 },
	{ -162, -200, 78 },
	{ -200, -232, 36 },
}

local function piece(
	parent: Instance,
	nom: string,
	taille: Vector3,
	cf: CFrame,
	couleur: Color3,
	opts: { [string]: any }?,
	classe: string?
): BasePart
	local p = Instance.new(classe or "Part") :: BasePart
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
	if opts then
		for k, v in opts do
			(p :: any)[k] = v
		end
	end
	p.Parent = parent
	return p
end

-- Cylindre vertical de rayon r entre yHaut et yBas
local function disque(
	parent: Instance,
	nom: string,
	r: number,
	yHaut: number,
	yBas: number,
	couleur: Color3,
	opts: { [string]: any }?
): BasePart
	local h = yHaut - yBas
	local p = piece(
		parent,
		nom,
		Vector3.new(h, r * 2, r * 2),
		CFrame.new(CENTRE.X, (yHaut + yBas) / 2, CENTRE.Z) * CFrame.Angles(0, 0, math.rad(90)),
		couleur,
		opts
	)
	local cylindre = p :: Part
	cylindre.Shape = Enum.PartType.Cylinder
	return p
end

local function surCercle(r: number, angle: number, y: number): CFrame
	local pos = Vector3.new(CENTRE.X + math.cos(angle) * r, y, CENTRE.Z + math.sin(angle) * r)
	local dehors = Vector3.new(math.cos(angle), 0, math.sin(angle))
	return CFrame.lookAt(pos, pos + dehors)
end

local function pierreAuHasard(): Color3
	return C.pierres[alea:NextInteger(1, #C.pierres)]
end

-- Sauvegarde et retrait de l'ancienne limite de carte et des sols
local sauvegarde = ServerStorage:FindFirstChild("Sauvegarde_AvantIleVolante")
if not sauvegarde then
	sauvegarde = Instance.new("Folder")
	sauvegarde.Name = "Sauvegarde_AvantIleVolante"
	sauvegarde.Parent = ServerStorage
	for _, nom in { "Wall", "Wall_Grass", "Base", "Baseplate" } do
		local inst = workspace:FindFirstChild(nom)
		if inst then
			inst.Parent = sauvegarde
		end
	end
end
local ancienne = workspace:FindFirstChild("Ile")
if ancienne then
	ancienne:Destroy()
end

local ile = Instance.new("Model")
ile.Name = "Ile"

-- 1. Dessus : sol d'herbe marchable + bourrelets d'herbe qui débordent du bord
do
	local dessus = Instance.new("Folder")
	dessus.Name = "Dessus"
	dessus.Parent = ile
	local sol =
		disque(dessus, "Sol", RAYON, SOL_Y, SOL_Y - 4, C.herbe, { CanCollide = true, CanQuery = true, CanTouch = true })
	ile.PrimaryPart = sol
	local n = 70
	for i = 1, n do
		local a = (i + alea:NextNumber(-0.3, 0.3)) / n * math.pi * 2
		local l = alea:NextNumber(22, 34)
		local cf = surCercle(RAYON - 1.5, a, SOL_Y - 2.2) * CFrame.Angles(math.rad(alea:NextNumber(-8, 4)), 0, 0)
		piece(
			dessus,
			"TouffeBord",
			Vector3.new(l, alea:NextNumber(3, 4.5), alea:NextNumber(4, 6)),
			cf,
			C.herbeFoncee
		)
	end
end
task.wait()

-- 2. Muret bas le long du bord, comme la bordure du Hub (muret clair + chaperon en tuiles grises)
do
	local bordure = Instance.new("Folder")
	bordure.Name = "Bordure"
	bordure.Parent = ile
	local r = RAYON - 4
	local n = 72
	local longueur = 2 * math.pi * r / n + 0.6
	for i = 1, n do
		local a = i / n * math.pi * 2
		local base = surCercle(r, a, SOL_Y)
		piece(bordure, "Muret", Vector3.new(longueur, 1.6, 1.6), base * CFrame.new(0, 0.8, 0), C.muret)
		piece(bordure, "Chaperon", Vector3.new(longueur + 0.2, 0.5, 2.2), base * CFrame.new(0, 1.85, 0), C.chaperon)
	end
end
task.wait()

-- 3. Dessous : strates de terre puis de pierre, de plus en plus étroites, habillées de rochers
do
	local dessous = Instance.new("Folder")
	dessous.Name = "Dessous"
	dessous.Parent = ile
	for i, s in STRATES do
		local yHaut, yBas, r = s[1], s[2], s[3]
		local couleur = if i == 1 then C.terre elseif i <= 4 then C.pierres[i - 1] else C.pierreProfonde
		disque(dessous, "Strate" .. i, r, yHaut, yBas, couleur)
		local h = yHaut - yBas
		local n = math.max(8, math.floor(2 * math.pi * r / 20))
		for j = 1, n do
			local a = (j + alea:NextNumber(-0.35, 0.35)) / n * math.pi * 2
			local hauteur = h * alea:NextNumber(1.0, 1.45)
			local cf = surCercle(r - alea:NextNumber(1, 5), a, (yHaut + yBas) / 2 - alea:NextNumber(0, h * 0.25))
				* CFrame.Angles(
					math.rad(alea:NextNumber(-14, 14)),
					math.rad(alea:NextNumber(-20, 20)),
					math.rad(alea:NextNumber(-10, 10))
				)
			local c = if i == 1 then (if alea:NextNumber() < 0.5 then C.terre else C.terreFoncee) else pierreAuHasard()
			piece(dessous, "Rocher", Vector3.new(alea:NextNumber(16, 28), hauteur, alea:NextNumber(10, 18)), cf, c)
		end
		-- Pointes qui pendent sous la strate
		if i >= 2 then
			local nPointes = math.floor(n / 4)
			for _ = 1, nPointes do
				local a = alea:NextNumber(0, math.pi * 2)
				local rr = r * alea:NextNumber(0.55, 0.95)
				local longueur = alea:NextNumber(16, 34)
				local largeur = alea:NextNumber(6, 12)
				local cf = surCercle(rr, a, yBas - longueur / 2 + 4)
				-- deux coins retournés, adossés : arête basse au milieu = pointe vers le bas
				local couleurPointe = pierreAuHasard()
				for k = 0, 1 do
					piece(
						dessous,
						"Pointe",
						Vector3.new(largeur, longueur, largeur / 2),
						cf
							* CFrame.Angles(0, math.rad(180 * k), 0)
							* CFrame.Angles(0, 0, math.rad(180))
							* CFrame.new(0, 0, -largeur / 4),
						couleurPointe,
						nil,
						"WedgePart"
					)
				end
			end
		end
		task.wait()
	end
	-- Pointe finale
	local yBas = STRATES[#STRATES][2]
	for k = 0, 3 do
		piece(
			dessous,
			"PointeFinale",
			Vector3.new(44, 46, 22),
			CFrame.new(CENTRE.X, yBas - 23 + 2, CENTRE.Z)
				* CFrame.Angles(0, math.rad(90 * k), 0)
				* CFrame.Angles(0, 0, math.rad(180))
				* CFrame.new(0, 0, -11),
			C.pierreProfonde,
			nil,
			"WedgePart"
		)
	end
end
task.wait()

-- 4. Cristaux dorés incrustés sous l'île (rappel du cœur du Hub)
do
	local cristaux = Instance.new("Folder")
	cristaux.Name = "Cristaux"
	cristaux.Parent = ile
	for i = 1, 14 do
		local s = STRATES[alea:NextInteger(2, 5)]
		local a = alea:NextNumber(0, math.pi * 2)
		local y = alea:NextNumber(s[2] + 4, s[1] - 4)
		local base = surCercle(s[3] + 1, a, y)
			* CFrame.Angles(math.rad(alea:NextNumber(-60, -25)), 0, math.rad(alea:NextNumber(-25, 25)))
		for k = 1, 3 do
			local h = alea:NextNumber(7, 14) / k
			local c = piece(
				cristaux,
				"Cristal",
				Vector3.new(h * 0.32, h, h * 0.32),
				base
					* CFrame.Angles(0, math.rad(k * 120), math.rad(alea:NextNumber(-30, 30) * (k - 1)))
					* CFrame.new(0, h / 2, 0),
				C.or_,
				{ Material = Enum.Material.Neon }
			)
			if k == 1 and i % 3 == 0 then
				local l = Instance.new("PointLight")
				l.Color = C.or_
				l.Range = 30
				l.Brightness = 1.5
				l.Parent = c
			end
		end
	end
end
task.wait()

-- 5. Murs invisibles juste derrière le muret (empêchent de tomber)
do
	local murs = Instance.new("Folder")
	murs.Name = "MursInvisibles"
	murs.Parent = ile
	local n = 48
	local r = RAYON - 1
	local longueur = 2 * math.pi * r / n + 2
	for i = 1, n do
		local a = i / n * math.pi * 2
		piece(
			murs,
			"MurInvisible",
			Vector3.new(longueur, MUR_HAUTEUR, 2),
			surCercle(r, a, SOL_Y + MUR_HAUTEUR / 2),
			C.muret,
			{
				Transparency = 1,
				CanCollide = true,
				CastShadow = false,
			}
		)
	end
end

ile.Parent = workspace
return "Île construite : " .. #ile:GetDescendants() .. " objets"
