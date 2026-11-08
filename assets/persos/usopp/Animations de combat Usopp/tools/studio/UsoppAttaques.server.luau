--!strict
-- Script à mettre DANS le modèle d'Usopp (hors Rojo, comme CombatIdle.server.luau).
-- Joue les 3 attaques en boucle (démo) et crée les effets aux marqueurs de l'animation.
-- Cible : ObjectValue « Cible » dans le modèle (un Model avec HumanoidRootPart ou une BasePart) ;
-- sinon un point à 16 studs devant le personnage.
-- Dégâts : valeurs *(proposition)*, à reporter dans docs/wiki/Personnages.md une fois validées.
-- Effets créés côté serveur pour la démo ; dans le vrai système de combat, les déplacer côté client.

local Debris = game:GetService("Debris")
local KeyframeSequenceProvider = game:GetService("KeyframeSequenceProvider")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")
local TweenService = game:GetService("TweenService")

local ANIMATIONS: { [string]: string } = {
	Usopp_Grenades = "", -- "rbxassetid://..." après publication
	Usopp_Liane = "",
	Usopp_Rafale = "",
}
local ORDRE = { "Usopp_Grenades", "Usopp_Liane", "Usopp_Rafale" }
local PAUSE_ENTRE_ATTAQUES = 1.5
local DEGATS = { Grenade = 120, Fouet = 90, Bille = 20, TirCharge = 130 } -- (proposition)

local modele = script.Parent :: Model
local racine = modele:WaitForChild("HumanoidRootPart") :: BasePart
local brasDroit = modele:WaitForChild("Right Arm") :: BasePart
local ctrl: Instance? = modele:FindFirstChildWhichIsA("Humanoid") or modele:FindFirstChildWhichIsA("AnimationController")
if not ctrl then
	local ac = Instance.new("AnimationController")
	ac.Parent = modele
	ctrl = ac
end
assert(ctrl)
local animateur = ctrl:FindFirstChildOfClass("Animator")
if not animateur then
	local a = Instance.new("Animator")
	a.Parent = ctrl
	animateur = a
end
assert(animateur)

local dossierFx = Instance.new("Folder")
dossierFx.Name = "EffetsUsopp"
dossierFx.Parent = workspace

local filtre = RaycastParams.new()
filtre.FilterType = Enum.RaycastFilterType.Exclude
filtre.FilterDescendantsInstances = { modele, dossierFx }

-- ---------- utilitaires ----------
local function piece(taille: Vector3, couleur: Color3, matiere: Enum.Material?, forme: Enum.PartType?): Part
	local p = Instance.new("Part")
	p.Size = taille
	p.Color = couleur
	p.Material = matiere or Enum.Material.SmoothPlastic
	p.Shape = forme or Enum.PartType.Block
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Parent = dossierFx
	return p
end

local function sol(pos: Vector3): Vector3
	local r = workspace:Raycast(pos + Vector3.new(0, 10, 0), Vector3.new(0, -60, 0), filtre)
	return if r then r.Position else Vector3.new(pos.X, racine.Position.Y - 3, pos.Z)
end

local function cible(): (Vector3, Instance?)
	local ov = modele:FindFirstChild("Cible")
	if ov and ov:IsA("ObjectValue") and ov.Value then
		local v = ov.Value
		if v:IsA("Model") then
			local hrp = v:FindFirstChild("HumanoidRootPart")
			if hrp and hrp:IsA("BasePart") then
				return hrp.Position, v
			end
		elseif v:IsA("BasePart") then
			return v.Position, v
		end
	end
	return (racine.CFrame * CFrame.new(0, 0, -16)).Position, nil
end

local function blesser(qui: Instance?, montant: number)
	if qui and qui:IsA("Model") then
		local h = qui:FindFirstChildWhichIsA("Humanoid")
		if h then
			h:TakeDamage(montant)
		end
	end
end

local function main(): Vector3
	return (brasDroit.CFrame * CFrame.new(0, -1.1, 0)).Position
end
local function boutLancePierre(): Vector3
	return (brasDroit.CFrame * CFrame.new(0, -1.7, 0)).Position
end

-- déplace p de a vers b en `duree` s avec une cloche de hauteur `h`, puis appelle fin()
local function voler(p: BasePart, a: Vector3, b: Vector3, duree: number, h: number, fin: (() -> ())?)
	local t = 0
	local cx: RBXScriptConnection
	cx = RunService.Heartbeat:Connect(function(dt)
		t = math.min(t + dt, duree)
		local k = t / duree
		p.CFrame = CFrame.new(a:Lerp(b, k) + Vector3.new(0, 4 * h * k * (1 - k), 0)) * CFrame.Angles(k * 10, 0, k * 4)
		if t >= duree then
			cx:Disconnect()
			if fin then
				fin()
			end
		end
	end)
end

local function flash(pos: Vector3, couleur: Color3, de: number, a: number, duree: number)
	local b = piece(Vector3.one * de, couleur, Enum.Material.Neon, Enum.PartType.Ball)
	b.CFrame = CFrame.new(pos)
	TweenService:Create(b, TweenInfo.new(duree, Enum.EasingStyle.Cubic, Enum.EasingDirection.Out), {
		Size = Vector3.one * a,
		Transparency = 1,
	}):Play()
	Debris:AddItem(b, duree + 0.1)
end

-- ---------- 1 · grenades ----------
local grenadeEnMain: Part? = nil
local numeroGrenade = 0
local DECALAGES = { -3, 0, 3 } -- points d'impact autour de la cible (en studs, vers l'avant)

local function sortirGrenade()
	local g = piece(Vector3.one * 0.9, Color3.fromRGB(47, 59, 42), Enum.Material.Metal, Enum.PartType.Ball)
	local meche = Instance.new("PointLight")
	meche.Color = Color3.fromRGB(255, 160, 60)
	meche.Range = 4
	meche.Parent = g
	grenadeEnMain = g
	local cx: RBXScriptConnection
	cx = RunService.Heartbeat:Connect(function()
		if grenadeEnMain ~= g then
			cx:Disconnect()
			return
		end
		g.CFrame = CFrame.new(main())
	end)
end

local function exploser(pos: Vector3, qui: Instance?)
	local e = Instance.new("Explosion")
	e.Position = pos
	e.BlastRadius = 6
	e.BlastPressure = 0
	e.DestroyJointRadiusPercent = 0
	e.ExplosionType = Enum.ExplosionType.NoCraters
	e.Parent = dossierFx
	flash(pos + Vector3.new(0, 1.5, 0), Color3.fromRGB(255, 179, 64), 2, 9, 0.35)
	-- dégâts au sol : brûlure + fissures, restent quelques secondes
	local brulure = piece(Vector3.new(0.1, 6, 6), Color3.fromRGB(38, 24, 14), Enum.Material.Slate, Enum.PartType.Cylinder)
	brulure.CFrame = CFrame.new(pos + Vector3.new(0, 0.05, 0)) * CFrame.Angles(0, 0, math.rad(90))
	brulure.Transparency = 0.25
	for i = 1, 4 do
		local f = piece(Vector3.new(0.15, 0.06, 2.5 + i * 0.4), Color3.fromRGB(30, 20, 12))
		f.CFrame = CFrame.new(pos + Vector3.new(0, 0.08, 0)) * CFrame.Angles(0, math.rad(i * 77), 0) * CFrame.new(0, 0, 1.6)
		Debris:AddItem(f, 6)
	end
	-- débris
	for i = 1, 6 do
		local d = piece(Vector3.one * 0.4, if i % 2 == 0 then Color3.fromRGB(122, 90, 58) else Color3.fromRGB(92, 143, 58))
		local arrivee = sol(pos + Vector3.new(math.cos(i) * 4, 0, math.sin(i) * 4))
		voler(d, pos, arrivee, 0.6, 3 + i % 3)
		Debris:AddItem(d, 1.5)
	end
	TweenService:Create(brulure, TweenInfo.new(1.5, Enum.EasingStyle.Linear, Enum.EasingDirection.In, 0, false, 4.5), {
		Transparency = 1,
	}):Play()
	Debris:AddItem(brulure, 6.2)
	local dist = if qui and qui:IsA("Model") and qui.PrimaryPart then (qui.PrimaryPart.Position - pos).Magnitude else 0
	if dist < 7 then
		blesser(qui, DEGATS.Grenade)
	end
end

local function lancerGrenade()
	local g = grenadeEnMain
	if not g then
		return
	end
	grenadeEnMain = nil
	numeroGrenade += 1
	local pc, qui = cible()
	local avant = (pc - racine.Position) * Vector3.new(1, 0, 1)
	avant = if avant.Magnitude > 0 then avant.Unit else -racine.CFrame.LookVector
	local impact = sol(pc + avant * DECALAGES[(numeroGrenade - 1) % 3 + 1])
	voler(g, g.Position, impact + Vector3.new(0, 0.45, 0), 0.6, 6, function()
		task.delay(0.25, function()
			g:Destroy()
			exploser(impact, qui)
		end)
	end)
end

-- ---------- 2 · balle-liane ----------
local NB_SEGMENTS, LONG_SEGMENT = 12, 0.75
local segmentsLiane: { Part } = {}
local debutLiane = 0
local baseLiane = Vector3.zero
local avantLiane = Vector3.zAxis

local function cleLiane(t: number): (number, number)
	-- (angle de départ, courbure totale) ; repos → armé → claque, 3 fois (aligné sur les marqueurs Fouet)
	local seq = {
		{ 0.0, -5, 40 }, { 0.6, -5, 40 },
		{ 0.75, -40, -70 }, { 0.9, -45, 175 }, { 1.1, -5, 40 },
		{ 1.25, -40, -70 }, { 1.4, -45, 175 }, { 1.6, -5, 40 },
		{ 1.75, -40, -70 }, { 1.9, -45, 175 }, { 2.2, -5, 40 },
	}
	if t <= 0 then
		return -5, 40
	end
	for i = 1, #seq - 1 do
		local a, b = seq[i], seq[i + 1]
		if t < b[1] then
			local k = TweenService:GetValue((t - a[1]) / (b[1] - a[1]), Enum.EasingStyle.Cubic, Enum.EasingDirection.Out)
			return a[2] + (b[2] - a[2]) * k, a[3] + (b[3] - a[3]) * k
		end
	end
	return -5, 40
end

local function pousserLiane()
	for _, s in segmentsLiane do
		s:Destroy()
	end
	table.clear(segmentsLiane)
	for i = 1, NB_SEGMENTS do
		local w = 0.7 - 0.4 * (i / NB_SEGMENTS)
		local s = piece(Vector3.new(w, w, LONG_SEGMENT + 0.15), if i % 2 == 0 then Color3.fromRGB(63, 154, 58) else Color3.fromRGB(54, 140, 51), Enum.Material.Grass)
		table.insert(segmentsLiane, s)
	end
	debutLiane = os.clock()
	local cx: RBXScriptConnection
	cx = RunService.Heartbeat:Connect(function()
		local t = os.clock() - debutLiane
		local pousse = math.clamp(t / 0.6, 0, 1) * (1 - math.clamp((t - 2.4) / 0.6, 0, 1))
		if t > 3.1 then
			cx:Disconnect()
			for _, s in segmentsLiane do
				s:Destroy()
			end
			table.clear(segmentsLiane)
			return
		end
		local a0, courbe = cleLiane(t - 0.05)
		local pos = baseLiane
		local visibles = pousse * NB_SEGMENTS
		for i, s in segmentsLiane do
			local part = math.clamp(visibles - (i - 1), 0, 1)
			local dir = math.rad(a0 + courbe * (i - 0.5) / NB_SEGMENTS)
			local v = (Vector3.yAxis * math.cos(dir) + avantLiane * math.sin(dir)) * LONG_SEGMENT * part
			s.Transparency = if part <= 0 then 1 else 0
			if part > 0 then
				s.CFrame = CFrame.lookAt(pos + v / 2, pos + v)
			end
			pos += v
		end
	end)
end

local function tirerGraine()
	local pc = cible()
	local depart = boutLancePierre()
	local avant = (pc - racine.Position) * Vector3.new(1, 0, 1)
	avantLiane = if avant.Magnitude > 0 then avant.Unit else -racine.CFrame.LookVector
	baseLiane = sol(pc - avantLiane * 4)
	local graine = piece(Vector3.one * 0.5, Color3.fromRGB(95, 191, 58), Enum.Material.Neon, Enum.PartType.Ball)
	voler(graine, depart, baseLiane, 0.33, 0.5, function()
		graine:Destroy()
		flash(baseLiane, Color3.fromRGB(217, 196, 155), 1, 4, 0.4)
		pousserLiane()
	end)
end

-- ---------- 3 · rafale ----------
local numeroBille = 0
local charge: Part? = nil

local function tirerBille()
	numeroBille += 1
	local pc, qui = cible()
	local j = ((numeroBille * 37) % 11 - 5) * 0.15
	local arrivee = pc + Vector3.new(0, 0.5 + j, 0)
	local b = piece(Vector3.one * 0.35, Color3.fromRGB(232, 198, 106), Enum.Material.SmoothPlastic, Enum.PartType.Ball)
	flash(boutLancePierre(), Color3.fromRGB(255, 243, 194), 0.4, 1.2, 0.12)
	voler(b, boutLancePierre(), arrivee, 0.18, 0, function()
		b:Destroy()
		flash(arrivee, Color3.fromRGB(255, 241, 176), 0.3, 1.6, 0.2)
		blesser(qui, DEGATS.Bille)
	end)
end

local function chargerTir()
	local c = piece(Vector3.one * 0.3, Color3.fromRGB(255, 138, 43), Enum.Material.Neon, Enum.PartType.Ball)
	local lumiere = Instance.new("PointLight")
	lumiere.Color = c.Color
	lumiere.Range = 8
	lumiere.Parent = c
	charge = c
	local t0 = os.clock()
	local cx: RBXScriptConnection
	cx = RunService.Heartbeat:Connect(function()
		if charge ~= c then
			cx:Disconnect()
			return
		end
		local k = math.clamp((os.clock() - t0) / 0.45, 0, 1)
		c.Size = Vector3.one * (0.3 + 0.9 * k + 0.08 * math.sin(os.clock() * 50))
		c.CFrame = CFrame.new(boutLancePierre())
	end)
end

local function tirCharge()
	local c = charge
	charge = nil
	if not c then
		return
	end
	local pc, qui = cible()
	local arrivee = pc + Vector3.new(0, 0.5, 0)
	voler(c, c.Position, arrivee, 0.25, 0, function()
		c:Destroy()
		flash(arrivee, Color3.fromRGB(255, 122, 43), 1.5, 8, 0.4)
		blesser(qui, DEGATS.TirCharge)
	end)
end

local function fouet()
	local pc, qui = cible()
	task.delay(0.05, function()
		flash(pc + Vector3.new(0, 1, 0), Color3.fromRGB(182, 255, 122), 0.5, 3, 0.25)
		blesser(qui, DEGATS.Fouet)
	end)
end

-- ---------- lecture ----------
local REACTIONS: { [string]: () -> () } = {
	Grenade = sortirGrenade,
	Lancer = lancerGrenade,
	Tir = tirerGraine,
	Fouet = fouet,
	Bille = tirerBille,
	Charge = chargerTir,
	TirCharge = tirCharge,
}

local function idAnimation(nom: string): string?
	if ANIMATIONS[nom] ~= "" then
		return ANIMATIONS[nom]
	end
	if RunService:IsStudio() then
		-- test sans publier : séquence générée par GenererUsoppAttaques.luau
		local saves = ServerStorage:FindFirstChild("RBX_ANIMSAVES")
		local entree = saves and saves:FindFirstChild(modele.Name)
		local seq = entree and entree:FindFirstChild(nom)
		if seq and seq:IsA("KeyframeSequence") then
			return KeyframeSequenceProvider:RegisterKeyframeSequence(seq)
		end
	end
	warn("[Usopp] Pas d'animation pour " .. nom)
	return nil
end

local pistes: { AnimationTrack } = {}
for _, nom in ORDRE do
	local id = idAnimation(nom)
	if id then
		local anim = Instance.new("Animation")
		anim.AnimationId = id
		local piste = animateur:LoadAnimation(anim)
		piste.Priority = Enum.AnimationPriority.Action
		for marqueur, reaction in REACTIONS do
			piste:GetMarkerReachedSignal(marqueur):Connect(reaction)
		end
		table.insert(pistes, piste)
	end
end

while #pistes > 0 do
	for _, piste in pistes do
		numeroGrenade, numeroBille = 0, 0
		piste:Play(0.15)
		piste.Stopped:Wait()
		task.wait(PAUSE_ENTRE_ATTAQUES)
	end
end
