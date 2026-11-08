--!strict
-- Plateau photo pour rendu_studio.py : a coller dans execute_luau (MCP Roblox_Studio), en Play, datamodel Client.
-- Pas un script du jeu (hors de src/, non synchronise par Rojo). Tout est cree cote client et disparait a l'arret du Play.
-- Renvoie le JSON a enregistrer dans <dossier>/cibles.json, puis : python rendu_studio.py prises <dossier>.
-- Apres l'appel, passer FieldOfView a 40 (portrait, plein pied) puis 70 (grille) avant les captures correspondantes.

local ID = "usopp"
type Config = {
	pose: number, -- image de l'Idle du portrait et du plein pied (comme POSES_PORTRAIT de rendu_gui.py)
	images: number, -- images de l'Idle a 30 i/s (duree de la boucle x 30)
	accessoires: { { any } }, -- visibilite selon les marqueurs Montrer / Cacher de l'Idle : {nom, debut, fin} (images)
	caches: { string },
	poseFixe: string?, -- au lieu de l'image `pose` : contenu de assets/persos/<Id>/anims/<Id>_PoseGUI.json (a coller)
	source: string?, -- chemin du modele dans workspace (perso pas encore dans ModelesPersonnages)
	idleLocale: string?, -- chemin d'une KeyframeSequence dans workspace : Idle non publiee, enregistree en local
}
local CONFIGS: { [string]: Config } = {
	nami = { pose = 40, images = 90, accessoires = { { "Acc_Bourse", 15, 65 } }, caches = { "Acc_Carte" } },
	luffy = { pose = 0, images = 90, accessoires = {}, caches = { "Acc_Haki", "Acc_Haki_Main" } },
	zoro = { pose = 0, images = 120, accessoires = {}, caches = {}, poseFixe = [[COLLER zoro_PoseGUI.json]] },
	-- Idle d'interface (anims_usopp.py idle -> outils_studio.py sequence IdleGui_fini, copie dans Essais_Usopp)
	usopp = {
		pose = 0,
		images = 120,
		accessoires = {},
		caches = { "Acc_LancePierre_Main" },
		source = "Essais_Usopp.usopp",
		idleLocale = "Essais_Usopp.usopp_IdleGui",
	},
}
local POSE_FIXE = CONFIGS[ID].poseFixe
local POSE_PORTRAIT = CONFIGS[ID].pose
local ACCESSOIRES = CONFIGS[ID].accessoires
local CACHES = CONFIGS[ID].caches

local RS = game:GetService("ReplicatedStorage")
local HS = game:GetService("HttpService")

local function chemin(c: string): Instance
	local i: Instance = workspace
	for nom in c:gmatch("[^%.]+") do
		i = i:WaitForChild(nom)
	end
	return i
end
local function modeleSource(): Model
	local c = CONFIGS[ID].source
	return (if c then chemin(c) else (RS:WaitForChild("ModelesPersonnages") :: Folder):FindFirstChild(ID)) :: Model
end
local ID_IDLE: string = if CONFIGS[ID].idleLocale
	then game:GetService("KeyframeSequenceProvider")
		:RegisterKeyframeSequence(chemin(CONFIGS[ID].idleLocale :: string) :: KeyframeSequence)
	else modeleSource():GetAttribute("AnimationIdle") :: string
local plr = game:GetService("Players").LocalPlayer
pcall(function()
	game:GetService("StarterGui"):SetCoreGuiEnabled(Enum.CoreGuiType.All, false)
end)
for _, g in plr.PlayerGui:GetChildren() do
	if g:IsA("ScreenGui") then
		g.Enabled = false
	end
end

local ancien = workspace:FindFirstChild("RenduGui")
if ancien then
	ancien:Destroy()
end
local dossier = Instance.new("Folder")
dossier.Name = "RenduGui"
dossier.Parent = workspace
local P0 = Vector3.new(0, 600, 0)

-- perso tourne pour que le soleil vienne de 35 degres sur sa droite avant (lumiere principale de rendu_gui.py)
local s = game:GetService("Lighting"):GetSunDirection()
local sh = Vector3.new(s.X, 0, s.Z).Unit
local f, meilleur = Vector3.zAxis, -2
for a = 0, 359 do
	local v = Vector3.new(math.sin(math.rad(a)), 0, math.cos(math.rad(a)))
	local l = v * math.cos(math.rad(35)) + v:Cross(Vector3.yAxis) * math.sin(math.rad(35))
	if l:Dot(sh) > meilleur then
		f, meilleur = v, l:Dot(sh)
	end
end
local r = f:Cross(Vector3.yAxis)
local dcam = f * math.cos(math.rad(30)) + r * math.sin(math.rad(30))
local lat = dcam:Cross(Vector3.yAxis).Unit

-- un plateau par image et par fond (0 noir, 1 gris), alignes sur le cote : la camera n'en voit qu'un
local poses = { POSE_PORTRAIT }
for k = 0, 15 do
	table.insert(poses, k * CONFIGS[ID].images / 16)
end
type Plateau = { perso: Model, O: Vector3, image: number, fond: number, track: AnimationTrack }
local plateaux: { Plateau } = {}
for _, image in poses do
	for fond = 0, 1 do
		local O = P0 + lat * 600 * #plateaux
		local perso = modeleSource():Clone()
		perso.Parent = dossier
		perso:PivotTo(CFrame.lookAt(O, O + f))
		for _, p in perso:GetDescendants() do
			if p:IsA("BasePart") then
				p.Anchored = p.Name == "HumanoidRootPart"
			end
		end
		for _, acc in ACCESSOIRES do
			local visible = image >= acc[2] and image < acc[3]
			for _, p in perso:FindFirstChild(acc[1]):GetDescendants() do
				if p:IsA("BasePart") then
					p.Transparency = if visible then 0 else 1
				end
			end
		end
		for _, nom in CACHES do
			for _, p in perso:FindFirstChild(nom):GetDescendants() do
				if p:IsA("BasePart") then
					p.Transparency = 1
				end
			end
		end
		local fd = Instance.new("Part")
		fd.Anchored, fd.CanCollide, fd.CastShadow = true, false, false
		fd.Size = Vector3.new(200, 200, 1)
		fd.CFrame = CFrame.lookAt(O - dcam * 50 + Vector3.yAxis, O + dcam * 100)
		fd.Parent = dossier
		local sg = Instance.new("SurfaceGui")
		sg.Face = Enum.NormalId.Front
		sg.LightInfluence = 0
		sg.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		sg.PixelsPerStud = 1
		sg.Parent = fd
		local fr = Instance.new("Frame")
		fr.Size = UDim2.fromScale(1, 1)
		fr.BorderSizePixel = 0
		fr.BackgroundColor3 = if fond == 1 then Color3.fromRGB(150, 150, 150) else Color3.new(0, 0, 0)
		fr.Parent = sg
		local anim = Instance.new("Animation")
		anim.AnimationId = ID_IDLE
		local animator = (perso:FindFirstChildOfClass("Humanoid") :: Humanoid):FindFirstChildOfClass(
				"Animator"
			) :: Animator
		local track = animator:LoadAnimation(anim)
		if #plateaux < 2 and POSE_FIXE then
			-- pose d'interface : Transform des Motor6D, sans Animator (il les remettrait a zero)
			animator.Parent = nil
			local transforms = HS:JSONDecode(POSE_FIXE) :: { [string]: { number } }
			for _, m in perso:GetDescendants() do
				local t = if m:IsA("Motor6D") then transforms[m.Name] else nil
				if t then
					m.Transform = CFrame.new(table.unpack(t))
				end
			end
		end
		track:Play(0, 1, 0)
		local t0 = os.clock()
		while track.Length == 0 and os.clock() - t0 < 5 do -- Idle locale : longueur connue une image plus tard
			task.wait()
		end
		track.TimePosition = math.clamp(image / 30, 0, track.Length - 1e-4)
		table.insert(plateaux, { perso = perso, O = O, image = image, fond = fond, track = track })
	end
end
task.wait(0.2)

-- cadrages (relatifs a l'origine de chaque plateau), memes regles que rendu_gui.py
local function coins(b: Plateau): { Vector3 }
	local pts = {}
	for _, p in b.perso:GetDescendants() do
		if p:IsA("BasePart") and p.Transparency < 1 and p.Name ~= "HumanoidRootPart" and not p.Name:find("^VFX_") then
			local t = p.Size / 2
			for _, sx in { -1, 1 } do
				for _, sy in { -1, 1 } do
					for _, sz in { -1, 1 } do
						table.insert(pts, (p.CFrame * Vector3.new(sx * t.X, sy * t.Y, sz * t.Z)) - b.O)
					end
				end
			end
		end
	end
	return pts
end
local function dir(az: number, el: number): Vector3
	local a, e = math.rad(az), math.rad(el)
	return ((f * math.cos(a) + r * math.sin(a)) * math.cos(e) + Vector3.yAxis * math.sin(e)).Unit
end
local function base(pos: Vector3, cible: Vector3)
	local fw = (cible - pos).Unit
	local rt = fw:Cross(Vector3.yAxis).Unit
	return fw, rt, rt:Cross(fw)
end
local function tangentes(pts: { Vector3 }, pos: Vector3, fw: Vector3, rt: Vector3, up: Vector3)
	local ax, bx, ay, by = math.huge, -math.huge, math.huge, -math.huge
	for _, q in pts do
		local d = q - pos
		local z = d:Dot(fw)
		local x, y = d:Dot(rt) / z, d:Dot(up) / z
		ax, bx, ay, by = math.min(ax, x), math.max(bx, x), math.min(ay, y), math.max(by, y)
	end
	return ax, bx, ay, by
end
local function v3(v: Vector3)
	return { v.X, v.Y, v.Z }
end
local function pied(pts: { Vector3 })
	local th, m = 18 / 35, 0.06
	local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, q in pts do
		lo, hi = lo:Min(q), hi:Max(q)
	end
	local centre = (lo + hi) / 2
	local recul = (hi - lo).Magnitude * 2
	for _ = 1, 8 do
		local pos = centre + dir(30, -8) * recul
		local ax, bx, ay, by = tangentes(pts, pos, base(pos, centre))
		recul *= math.max(bx - ax, by - ay) / ((1 - 2 * m) * 2 * th)
	end
	local pos = centre + dir(30, -8) * recul
	local ax, bx, ay = tangentes(pts, pos, base(pos, centre))
	return { pos = v3(pos), centre = v3(centre), th = th, cx = (ax + bx) / 2, cy = ay + th - 2 * m * th }
end

local b = plateaux[1]
local tete = b.perso:FindFirstChild("Head") :: BasePart
local cou = (tete.CFrame * (tete:FindFirstChild("Neck") :: Motor6D).C1).Position
local centre = cou + tete.CFrame.UpVector * 0.625 - b.O
local th = 4.75 / 2 / 8.75
local tous = {}
for i = 3, #plateaux, 2 do
	for _, q in coins(plateaux[i]) do
		table.insert(tous, q)
	end
end
local res = {
	portrait = { pos = v3(centre + dir(30, 3) * 8.75), centre = v3(centre), th = th, cx = 0, cy = -1 / 3 * th },
	pied = pied(coins(b)),
	grille = pied(tous),
	O = {},
	images = {},
	duree = plateaux[3].track.Length,
	animation = ID_IDLE,
}
for i, p in plateaux do
	res.O[i] = v3(p.O)
	res.images[i] = { p.image, p.fond, p.track.TimePosition }
	if i <= 2 and POSE_FIXE then
		res.images[i] = { ID .. "_PoseGUI.json", p.fond, 0 }
	end
end

-- chauffe : un fond vu pour la premiere fois n'est pas encore affiche a la premiere capture
local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
for _, p in plateaux do
	cam.CFrame = CFrame.lookAt(p.O + dcam * 9 + Vector3.yAxis, p.O)
	task.wait(0.4)
end
cam.CameraType = Enum.CameraType.Custom
return HS:JSONEncode(res)
