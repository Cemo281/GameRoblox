--!strict
-- VFX de luffy_Action (style anime net : vif, rapide, puissant), à exécuter dans Studio via le MCP (mode Edit).
-- Construit sur le modèle `M` (ModelesPersonnages.luffy ou une copie d'aperçu) les effets lus par src/client/Vitrine.luau :
--   Coup_Right / Coup_Left (Burst, un marqueur par coup de la rafale) : éclat, anneau d'air, traits vers l'épaule
--   Rafale (Duree) : traînées courtes derrière les deux poings
--   Charge_Poing (Duree) : lignes aspirées et anneaux qui se resserrent sur le poing
--   Lancer_Poing (Burst) : anneaux d'air qui éclatent au départ du poing élastique
--   Poing_Elastique (Duree) : traits le long du bras, traînée du poing
--   Impact_Final (Burst) : gros éclat, lignes d'impact, 2 ondes, étincelles, poussière au sol
-- Textures : assets/persos/luffy/vfx_luffy.py. Main R15 : -Y = sens du coup (vers les doigts).

-- cible passée par le MCP (copie d'aperçu), sinon le vrai modèle
-- selene: allow(global_usage)
local M: Model = (_G :: any).CibleVfxLuffy or game.ReplicatedStorage.ModelesPersonnages.luffy

local TEX = {
	eclat = "rbxassetid://112249090477155",
	anneau = "rbxassetid://93783833153831",
	trait = "rbxassetid://97795166368994",
	lignes = "rbxassetid://135983583011818",
	poussiere = "rbxassetid://70434048288435",
}

local function ns(...: number): NumberSequence
	local v = { ... }
	local k = {}
	for i = 1, #v, 2 do
		table.insert(k, NumberSequenceKeypoint.new(v[i], v[i + 1]))
	end
	return NumberSequence.new(k)
end

local function cs(...: any): ColorSequence
	local v = { ... }
	local k = {}
	for i = 1, #v, 2 do
		table.insert(k, ColorSequenceKeypoint.new(v[i], v[i + 1]))
	end
	return ColorSequence.new(k)
end

-- sens « vers l'épaule » pour un émetteur sur un Attachment de la main (+Y de la main), vérifié en Play
local DIR_EPAULE = Enum.NormalId.Top

local BLANC = Color3.new(1, 1, 1)
local JAUNE = Color3.fromRGB(255, 226, 90)
local ORANGE = Color3.fromRGB(255, 150, 40)

local function attache(parent: BasePart, nom: string, pos: Vector3, ori: Vector3?): Attachment
	local a = parent:FindFirstChild(nom)
	if not (a and a:IsA("Attachment")) then
		a = Instance.new("Attachment")
		a.Name = nom
		a.Parent = parent
	end
	local att = a :: Attachment
	att.Position = pos
	att.Orientation = ori or Vector3.zero
	return att
end

local function emetteur(parent: Instance, nom: string, p: { [string]: any }): ParticleEmitter
	local ancien = parent:FindFirstChild(nom)
	if ancien then
		ancien:Destroy()
	end
	local e = Instance.new("ParticleEmitter")
	e.Name = nom
	e.Enabled = false
	e.Rate = 0
	e.LightInfluence = 0
	e.LockedToPart = false
	for k, v in p do
		if k ~= "Quantite" then
			(e :: any)[k] = v
		end
	end
	if p.Quantite then
		e:SetAttribute("Quantite", p.Quantite)
	end
	e.Parent = parent
	return e
end

local function trainee(main: BasePart, nom: string, vie: number, largeur: number, couleur: ColorSequence): Trail
	local a0 = attache(main, nom .. "0", Vector3.new(largeur / 2, -0.1, 0))
	local a1 = attache(main, nom .. "1", Vector3.new(-largeur / 2, -0.1, 0))
	local ancien = main:FindFirstChild(nom)
	if ancien then
		ancien:Destroy()
	end
	local t = Instance.new("Trail")
	t.Name = nom
	t.Attachment0 = a0
	t.Attachment1 = a1
	t.FaceCamera = true
	t.Lifetime = vie
	t.MinLength = 0.05
	t.Color = couleur
	t.Transparency = ns(0, 0.15, 0.6, 0.6, 1, 1)
	t.WidthScale = ns(0, 1, 1, 0.2)
	t.LightEmission = 0.7
	t.LightInfluence = 0
	t.Enabled = false
	t.Parent = main
	return t
end

-- dossier VFX/<nom> lu par Vitrine.luau (ObjectValue vers chaque émetteur)
local function effet(nom: string, mode: string, duree: number?, liste: { Instance })
	local vfx = M:FindFirstChild("VFX") :: Folder
	local ancien = vfx:FindFirstChild(nom)
	if ancien then
		ancien:Destroy()
	end
	local f = Instance.new("Folder")
	f.Name = nom
	f:SetAttribute("Mode", mode)
	if duree then
		f:SetAttribute("Duree", duree)
	end
	for _, e in liste do
		local o = Instance.new("ObjectValue")
		o.Name = e.Name
		o.Value = e
		o.Parent = f
	end
	f.Parent = vfx
end

-- anciens émetteurs de l'Action (poings flottants, traits, étincelles génériques)
for _, chemin in
	{
		{ "HumanoidRootPart", "VFX_Rafale" },
		{ "RightHand", "VFX_Impact" },
	}
do
	local p = M:FindFirstChild(chemin[1])
	local a = p and p:FindFirstChild(chemin[2])
	if a then
		a:Destroy()
	end
end
local zoneCharge = M:FindFirstChild("VFX_ZoneCharge") :: BasePart
for _, e in zoneCharge:GetChildren() do
	if e:IsA("ParticleEmitter") then
		e:Destroy()
	end
end

-- ---------------------------------------------------------------- coups de la rafale (un par poing)
local trainees = {}
for _, cote in { "Right", "Left" } do
	local main = M:FindFirstChild(cote .. "Hand") :: BasePart
	local pointe = attache(main, "VFX_Coup", Vector3.new(0, -0.35, 0))
	local liste = {
		-- éclat d'impact : apparaît d'un coup, grossit puis disparaît (≈ 0,1 s)
		emetteur(pointe, "Coup_Eclat", {
			Texture = TEX.eclat,
			Lifetime = NumberRange.new(0.1),
			Speed = NumberRange.new(0),
			Size = ns(0, 0.7, 0.25, 1.8, 1, 2.0),
			Transparency = ns(0, 0, 0.5, 0.1, 1, 1),
			Rotation = NumberRange.new(0, 360),
			LightEmission = 0.35,
			ZOffset = 1.5,
			Quantite = 1,
		}),
		-- anneau d'air perpendiculaire au coup (vitesse quasi nulle dans le sens du coup = orientation)
		emetteur(pointe, "Coup_Anneau", {
			Texture = TEX.anneau,
			Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
			EmissionDirection = Enum.NormalId.Bottom,
			Lifetime = NumberRange.new(0.16),
			Speed = NumberRange.new(0.05),
			Size = ns(0, 0.5, 0.4, 2.2, 1, 2.8),
			Transparency = ns(0, 0, 0.6, 0.35, 1, 1),
			Color = cs(0, BLANC, 1, Color3.fromRGB(255, 240, 200)),
			LightEmission = 0.6,
			Quantite = 1,
		}),
	}
	-- traits de vitesse qui filent vers l'épaule, nés autour du bras (dedans, la boîte étirée les cacherait)
	local ancien = main:FindFirstChild("Coup_Traits")
	if ancien then
		ancien:Destroy()
	end
	for i, decalage in
		{ Vector3.new(0.85, 0, 0), Vector3.new(-0.85, 0, 0), Vector3.new(0, 0, 0.85), Vector3.new(0, 0, -0.85) }
	do
		table.insert(
			liste,
			emetteur(attache(main, "VFX_Traits" .. i, decalage + Vector3.new(0, -0.2, 0)), "Coup_Traits", {
				Texture = TEX.trait,
				Orientation = Enum.ParticleOrientation.VelocityParallel,
				EmissionDirection = DIR_EPAULE,
				SpreadAngle = Vector2.new(6, 6),
				Lifetime = NumberRange.new(0.08, 0.12),
				Speed = NumberRange.new(40, 60),
				Size = ns(0, 2.4, 1, 1.2),
				Transparency = ns(0, 0, 0.7, 0.2, 1, 1),
				LightEmission = 0.8,
				Quantite = 2,
			})
		)
	end
	effet("Coup_" .. cote, "Burst", nil, liste)
	table.insert(trainees, trainee(main, "VFX_TraineeRafale", 0.09, 0.8, cs(0, BLANC, 1, JAUNE)))
end
effet("Rafale", "Duree", 1.4, trainees)

-- ---------------------------------------------------------------- charge du poing
effet("Charge_Poing", "Duree", 0.67, {
	emetteur(zoneCharge, "Charge_Lignes", {
		Texture = TEX.trait,
		Shape = Enum.ParticleEmitterShape.Sphere,
		ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
		ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward,
		Orientation = Enum.ParticleOrientation.VelocityParallel,
		Rate = 120,
		Lifetime = NumberRange.new(0.12),
		Speed = NumberRange.new(11),
		Size = ns(0, 1.1, 1, 0.4),
		Transparency = ns(0, 1, 0.3, 0.1, 1, 0.4),
		Color = cs(0, BLANC, 1, JAUNE),
		LightEmission = 0.8,
		LockedToPart = true,
	}),
	emetteur(
		attache(M:FindFirstChild("RightHand") :: BasePart, "VFX_Coup", Vector3.new(0, -0.35, 0)),
		"Charge_Anneaux",
		{
			Texture = TEX.anneau,
			Rate = 9,
			Lifetime = NumberRange.new(0.22),
			Speed = NumberRange.new(0),
			Size = ns(0, 3.2, 1, 0.4),
			Transparency = ns(0, 1, 0.3, 0.2, 1, 0),
			Color = cs(0, BLANC, 1, JAUNE),
			LightEmission = 0.6,
			LockedToPart = true,
		}
	),
})

-- ---------------------------------------------------------------- départ et vol du poing élastique
local mainD = M:FindFirstChild("RightHand") :: BasePart
local pointeD = mainD:FindFirstChild("VFX_Coup") :: Attachment
effet("Lancer_Poing", "Burst", nil, {
	emetteur(pointeD, "Lancer_Anneaux", {
		Texture = TEX.anneau,
		Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
		EmissionDirection = Enum.NormalId.Bottom,
		Lifetime = NumberRange.new(0.18, 0.26),
		Speed = NumberRange.new(0.05, 6),
		Size = ns(0, 0.8, 0.5, 3.6, 1, 4.2),
		Transparency = ns(0, 0, 0.6, 0.4, 1, 1),
		LightEmission = 0.6,
		Quantite = 3,
	}),
})
local traitsBras = {}
for _, n in { "RightUpperArm", "RightLowerArm" } do
	local p = M:FindFirstChild(n) :: BasePart
	for _, nom in { "VFX_TraitsBras", "VFX_TraitsBras_" .. n } do
		local ancien = p:FindFirstChild(nom)
		if ancien and ancien:IsA("Attachment") then
			for _, e in ancien:GetChildren() do
				e:Destroy()
			end
		elseif ancien then
			ancien:Destroy()
		end
	end
end
-- autour de l'avant-bras qui file (dans la boîte étirée, les traits seraient cachés)
local avantBras = M:FindFirstChild("RightLowerArm") :: BasePart
for i, decalage in { Vector3.new(0.8, 0, 0), Vector3.new(-0.8, 0, 0), Vector3.new(0, 0, 0.8), Vector3.new(0, 0, -0.8) } do
	table.insert(
		traitsBras,
		emetteur(attache(avantBras, "VFX_TraitsBras" .. i, decalage), "Elastique_Traits", {
			Texture = TEX.trait,
			Orientation = Enum.ParticleOrientation.VelocityParallel,
			EmissionDirection = DIR_EPAULE,
			SpreadAngle = Vector2.new(4, 4),
			Rate = 30,
			Lifetime = NumberRange.new(0.08, 0.12),
			Speed = NumberRange.new(45, 65),
			Size = ns(0, 2.6, 1, 1.2),
			Transparency = ns(0, 0, 0.7, 0.3, 1, 1),
			LightEmission = 0.8,
		})
	)
end
local ancienneTrainee = mainD:FindFirstChild("VFX_Trail")
if ancienneTrainee then
	ancienneTrainee:Destroy()
end
table.insert(traitsBras, mainD:FindFirstChild("VFX_TraineeRafale") :: Instance)
effet("Poing_Elastique", "Duree", 0.5, traitsBras)

-- ---------------------------------------------------------------- impact final
local impact = attache(mainD, "VFX_Impact", Vector3.new(0, -0.5, 0))
local hrp = M:FindFirstChild("HumanoidRootPart") :: BasePart
local sol = attache(hrp, "VFX_Sol", Vector3.new(0, -3.1, -1.5))
effet("Impact_Final", "Burst", nil, {
	emetteur(impact, "Impact_Eclat", {
		Texture = TEX.eclat,
		Lifetime = NumberRange.new(0.16),
		Speed = NumberRange.new(0),
		Size = ns(0, 1, 0.2, 3.6, 1, 4.2), -- le poing frappe vers le joueur : pas plus grand
		Transparency = ns(0, 0, 0.55, 0.05, 1, 1),
		Rotation = NumberRange.new(0, 360),
		LightEmission = 0.35,
		ZOffset = 2,
		Quantite = 1,
	}),
	emetteur(impact, "Impact_Lignes", {
		Texture = TEX.lignes,
		Lifetime = NumberRange.new(0.22),
		Speed = NumberRange.new(0),
		Size = ns(0, 2, 0.3, 6, 1, 7.5),
		Transparency = ns(0, 0, 0.5, 0.1, 1, 1),
		Rotation = NumberRange.new(0, 360),
		LightEmission = 0.5,
		ZOffset = 1,
		Quantite = 1,
	}),
	emetteur(impact, "Impact_Ondes", {
		Texture = TEX.anneau,
		Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
		EmissionDirection = Enum.NormalId.Bottom,
		Lifetime = NumberRange.new(0.22, 0.38),
		Speed = NumberRange.new(0.05, 4),
		Size = ns(0, 0.8, 0.4, 5, 1, 6.5),
		Transparency = ns(0, 0, 0.5, 0.3, 1, 1),
		LightEmission = 0.6,
		Quantite = 2,
	}),
	emetteur(impact, "Impact_Etincelles", {
		Texture = TEX.trait,
		Orientation = Enum.ParticleOrientation.VelocityParallel,
		EmissionDirection = Enum.NormalId.Bottom,
		SpreadAngle = Vector2.new(70, 70),
		Lifetime = NumberRange.new(0.12, 0.22),
		Speed = NumberRange.new(30, 55),
		Drag = 6,
		Size = ns(0, 1.4, 1, 0.4),
		Color = cs(0, BLANC, 0.4, JAUNE, 1, ORANGE),
		Transparency = ns(0, 0, 0.7, 0.1, 1, 1),
		LightEmission = 0.8,
		Quantite = 26,
	}),
	emetteur(sol, "Impact_Poussiere", {
		Texture = TEX.poussiere,
		EmissionDirection = Enum.NormalId.Front,
		SpreadAngle = Vector2.new(5, 100), -- éventail à plat sur le sol
		Lifetime = NumberRange.new(0.5, 0.8),
		Speed = NumberRange.new(18, 28),
		Drag = 4,
		Size = ns(0, 0.6, 0.3, 1.6, 1, 2.2),
		Transparency = ns(0, 0.15, 0.5, 0.35, 1, 1),
		Rotation = NumberRange.new(0, 360),
		RotSpeed = NumberRange.new(-60, 60),
		Color = cs(0, Color3.fromRGB(235, 222, 196), 1, Color3.fromRGB(210, 196, 170)),
		LightEmission = 0,
		LightInfluence = 0.6,
		Quantite = 18,
	}),
	-- onde de choc à plat sur le sol
	emetteur(sol, "Impact_OndeSol", {
		Texture = TEX.anneau,
		Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
		EmissionDirection = Enum.NormalId.Top,
		Lifetime = NumberRange.new(0.35),
		Speed = NumberRange.new(0.05),
		Size = ns(0, 1, 0.5, 9, 1, 11),
		Transparency = ns(0, 0, 0.6, 0.4, 1, 1),
		Color = cs(0, Color3.fromRGB(255, 245, 225), 1, Color3.fromRGB(255, 245, 225)),
		LightEmission = 0.4,
		Quantite = 1,
	}),
})

local noms = {}
for _, f in (M:FindFirstChild("VFX") :: Folder):GetChildren() do
	table.insert(noms, f.Name .. "(" .. #f:GetChildren() .. ")")
end
return M:GetFullName() .. " : " .. table.concat(noms, ", ")
