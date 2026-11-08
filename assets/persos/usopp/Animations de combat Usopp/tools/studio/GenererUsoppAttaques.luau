--!strict
-- Générateur des 3 attaques de combat d'Usopp (rig R6) — à lancer dans la Command Bar de Studio.
-- 1. Sélectionne le modèle R6 (Torso, Head, Left/Right Arm, Left/Right Leg, HumanoidRootPart + Motor6D standard).
-- 2. Colle ce fichier dans la Command Bar et Entrée.
-- Crée Usopp_Grenades, Usopp_Liane, Usopp_Rafale dans ServerStorage.RBX_ANIMSAVES.<nom du modèle>
-- (« … » → Charger dans l'éditeur d'animation, puis Publier sur Roblox et coller les ID dans UsoppAttaques.server.luau).
-- Marqueurs (GetMarkerReachedSignal) : Grenade, Lancer, LancePierre, Tir, Atterrissage, Fouet, Bille, Charge, TirCharge.
-- Angles en degrés, vue de profil : bras/jambe négatif = vers l'avant. buste positif = penché en avant. saut en studs.

local Selection = game:GetService("Selection")
local ServerStorage = game:GetService("ServerStorage")

type Cle = {
	t: number,
	bd: number, -- bras droit (tient grenades / lance-pierre)
	bg: number, -- bras gauche (tire l'élastique)
	jd: number,
	jg: number,
	buste: number?,
	saut: number?,
	tete: number?,
	e: string?, -- easing pour ARRIVER à cette clé : "InOut" (défaut), "Out", "In", "Linear"
	m: { string }?,
}

local NEUTRE = { bd = 8, bg = -8, jd = -6, jg = 6 }
local function c(t: number, bd: number, bg: number, jd: number, jg: number, extra: { [string]: any }?): Cle
	local cle: Cle = { t = t, bd = bd, bg = bg, jd = jd, jg = jg }
	if extra then
		cle.buste = extra.buste
		cle.saut = extra.saut
		cle.tete = extra.tete
		cle.e = extra.e
		cle.m = extra.m
	end
	return cle
end

-- 1 · Grenades du sac (5,5 s)
local GRENADES: { Cle } = {
	c(0, 8, -8, -6, 6),
	c(0.3, 8, -8, -6, 6),
	c(0.6, -15, -8, -6, 6, { tete = 14 }),
	c(0.8, -28, -8, -6, 6, { tete = 14 }),
	c(1.0, -10, -8, -6, 6, { tete = 14 }),
	c(1.2, -28, -8, -6, 6, { tete = 14 }),
	c(1.4, -12, -8, -6, 6, { tete = 14 }),
	c(1.6, -20, -8, -6, 6, { tete = 14, m = { "Grenade" } }),
	c(1.75, 60, -40, -18, 16, { buste = -6 }),
	c(1.85, 150, -70, -24, 22, { buste = -10 }),
	c(1.93, 220, -20, -24, 22, { buste = 0, e = "In" }),
	c(2.0, 290, 40, -24, 22, { buste = 12, e = "Out", m = { "Lancer" } }),
	c(2.15, 342, -10, -24, 22, { buste = 4, m = { "Grenade" } }),
	c(2.22, 60, -40, -24, 22, { buste = -6 }),
	c(2.3, 150, -70, -24, 22, { buste = -10 }),
	c(2.38, 220, -20, -24, 22, { e = "In" }),
	c(2.45, 290, 40, -24, 22, { buste = 12, e = "Out", m = { "Lancer" } }),
	c(2.6, 342, -10, -24, 22, { buste = 4, m = { "Grenade" } }),
	c(2.67, 60, -40, -24, 22, { buste = -6 }),
	c(2.75, 150, -70, -24, 22, { buste = -10 }),
	c(2.83, 220, -20, -24, 22, { e = "In" }),
	c(2.9, 290, 40, -24, 22, { buste = 12, e = "Out", m = { "Lancer" } }),
	c(3.2, 330, 10, -24, 22, { buste = 4 }),
	c(3.4, -30, 0, -16, 14),
	c(3.9, -160, 30, -8, 8, { buste = -6, tete = -10, e = "Out" }),
	c(4.3, -145, 30, -8, 8, { buste = -6, tete = -10 }),
	c(4.7, -165, 30, -8, 8, { buste = -6, tete = -10 }),
	c(5.3, 8, -8, -6, 6),
	c(5.5, 8, -8, -6, 6),
}

-- 2 · Saut + balle-liane (6 s)
local LIANE: { Cle } = {
	c(0, 8, -8, -6, 6),
	c(0.4, -20, -8, -8, 8, { m = { "LancePierre" } }),
	c(0.8, 25, 30, -38, 32, { buste = 14 }),
	c(0.95, -60, -60, -10, 8, { buste = 0, saut = 3, e = "Out" }),
	c(1.1, -160, -160, -30, 22, { buste = -6, saut = 7.5, e = "Out" }),
	c(1.35, -55, -62, -40, 30, { buste = 20, saut = 8.6, tete = 16, e = "Out" }),
	c(1.65, -55, -22, -36, 28, { buste = 20, saut = 8.9, tete = 16 }),
	c(1.72, -55, -78, -34, 26, { buste = 20, saut = 8.95, tete = 16, e = "Out", m = { "Tir" } }),
	c(1.95, -55, -78, -30, 22, { buste = 20, saut = 9.1, tete = 16 }),
	c(2.35, -120, -120, -10, 8, { saut = 4.2, e = "In" }),
	c(2.6, 15, 25, -36, 32, { buste = 12, saut = 0, e = "In", m = { "Atterrissage" } }),
	c(2.95, -95, 10, -14, 12, { buste = 4, e = "Out", m = { "Fouet" } }),
	c(3.5, -95, 10, -14, 12, { buste = 4, m = { "Fouet" } }),
	c(4.0, -95, 10, -14, 12, { buste = 4, m = { "Fouet" } }),
	c(4.5, -95, 10, -14, 12, { buste = 4 }),
	c(5.2, 8, -8, -6, 6),
	c(6.0, 8, -8, -6, 6),
}

-- 3 · Rafale de billes puis tir chargé (5 s)
local RAFALE: { Cle } = {
	c(0, 8, -8, -6, 6, { m = { "LancePierre" } }),
	c(0.4, -90, -85, -22, 22, { buste = 6 }),
	c(0.6, -90, -85, -22, 22, { buste = 6 }),
}
local DT = 0.16
for i = 0, 11 do
	local t0 = 0.6 + i * DT
	table.insert(RAFALE, c(t0 + DT * 0.75, -90, -48, -22, 22, { buste = 5, e = "Out" }))
	table.insert(RAFALE, c(t0 + DT, -90, -88, -22, 22, { buste = 7, e = "Linear", m = { "Bille" } }))
end
for _, cle in
	{
		c(2.6, -90, -80, -22, 22, { buste = 6, m = { "Charge" } }),
		c(3.0, -90, -25, -22, 22, { buste = -4 }),
		c(3.05, -90, -92, -22, 22, { buste = 10, e = "Out", m = { "TirCharge" } }),
		c(3.2, -80, -88, -22, 22, { buste = 8 }),
		c(3.6, -90, -85, -22, 22, { buste = 6 }),
		c(4.4, -90, -85, -22, 22, { buste = 6 }),
		c(5.0, 8, -8, -6, 6),
	}
do
	table.insert(RAFALE, cle)
end

local function poseCF(nom: string, cf: CFrame, style: Enum.PoseEasingStyle, dir: Enum.PoseEasingDirection): Pose
	local p = Instance.new("Pose")
	p.Name = nom
	p.CFrame = cf
	p.EasingStyle = style
	p.EasingDirection = dir
	return p
end

local function easing(e: string?): (Enum.PoseEasingStyle, Enum.PoseEasingDirection)
	if e == "Linear" then
		return Enum.PoseEasingStyle.Linear, Enum.PoseEasingDirection.InOut
	elseif e == "Out" then
		return Enum.PoseEasingStyle.CubicV2, Enum.PoseEasingDirection.Out
	elseif e == "In" then
		return Enum.PoseEasingStyle.CubicV2, Enum.PoseEasingDirection.In
	end
	return Enum.PoseEasingStyle.CubicV2, Enum.PoseEasingDirection.InOut
end

local function construire(nom: string, cles: { Cle }): KeyframeSequence
	table.sort(cles, function(a, b)
		return a.t < b.t
	end)
	local seq = Instance.new("KeyframeSequence")
	seq.Name = nom
	seq.Loop = false
	seq.Priority = Enum.AnimationPriority.Action
	for i, cle in cles do
		-- l'easing d'une Pose s'applique entre CETTE clé et la suivante
		local suivante = cles[i + 1]
		local style, dir = easing(suivante and suivante.e or nil)
		local kf = Instance.new("Keyframe")
		kf.Time = cle.t
		local rad = math.rad
		-- les jambes écartées font descendre le buste (pieds au sol)
		local ecart = math.max(math.abs(cle.jd), math.abs(cle.jg))
		local baisse = 2 * (1 - math.cos(rad(ecart)))
		local racine = poseCF("HumanoidRootPart", CFrame.identity, style, dir)
		racine.Weight = 0
		racine.Parent = kf
		local torse = poseCF(
			"Torso",
			CFrame.new(0, 0, (cle.saut or 0) - baisse) * CFrame.Angles(rad(cle.buste or 0), 0, 0),
			style,
			dir
		)
		torse.Parent = racine
		poseCF("Head", CFrame.Angles(rad(cle.tete or 0), 0, 0), style, dir).Parent = torse
		poseCF("Right Arm", CFrame.Angles(0, 0, rad(-cle.bd)), style, dir).Parent = torse
		poseCF("Left Arm", CFrame.Angles(0, 0, rad(cle.bg)), style, dir).Parent = torse
		poseCF("Right Leg", CFrame.Angles(0, 0, rad(-cle.jd)), style, dir).Parent = torse
		poseCF("Left Leg", CFrame.Angles(0, 0, rad(cle.jg)), style, dir).Parent = torse
		for _, m in cle.m or {} do
			local marqueur = Instance.new("KeyframeMarker")
			marqueur.Name = m
			kf:AddMarker(marqueur)
		end
		kf.Parent = seq
	end
	return seq
end

local modele = Selection:Get()[1]
assert(modele and modele:IsA("Model"), "Sélectionne le modèle R6 du personnage avant d'exécuter le script")
for _, piece in { "HumanoidRootPart", "Torso", "Head", "Left Arm", "Right Arm", "Left Leg", "Right Leg" } do
	assert(modele:FindFirstChild(piece), "Pièce R6 manquante : " .. piece)
end

local saves = ServerStorage:FindFirstChild("RBX_ANIMSAVES") or Instance.new("Folder")
saves.Name = "RBX_ANIMSAVES"
saves.Parent = ServerStorage
local entree = saves:FindFirstChild(modele.Name)
if not entree then
	-- même forme que l'entrée créée par l'éditeur d'animation
	local ov = Instance.new("ObjectValue")
	ov.Name = modele.Name
	ov.Value = modele
	ov.Parent = saves
	entree = ov
end
assert(entree)

for nom, cles in { Usopp_Grenades = GRENADES, Usopp_Liane = LIANE, Usopp_Rafale = RAFALE } do
	local ancien = entree:FindFirstChild(nom)
	if ancien then
		ancien:Destroy()
	end
	local seq = construire(nom, cles)
	seq.Parent = entree
	print(("[Usopp] %s : %d images, %.2f s"):format(nom, #seq:GetChildren(), cles[#cles].t))
end
print("[Usopp] Séquences rangées dans ServerStorage.RBX_ANIMSAVES." .. modele.Name)
