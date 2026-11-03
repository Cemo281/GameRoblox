-- LocalScript à placer dans StarterPlayer > StarterPlayerScripts
-- 1) Remplit les trous des membres étirés avec des tubes élastiques (couleur du membre).
-- 2) Affiche / cache les Accessory selon les marqueurs Montrer / Cacher.
-- 3) Expose Impact / Aura / Explosion / Fin / Esquive via onMarker() pour tes hitbox et VFX.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local LIMBS = {"RightElbow", "RightWrist", "LeftElbow", "LeftWrist", "RightKnee", "RightAnkle", "LeftKnee", "LeftAnkle"}
local folder = Instance.new("Folder")
folder.Name = "MembresElastiques"
folder.Parent = workspace
local rigs = {}

local function setVisible(character, accessoryName, visible)
	local acc = character:FindFirstChild(accessoryName)
	if not acc then return end
	for _, d in ipairs(acc:GetDescendants()) do
		if d:IsA("BasePart") or d:IsA("Decal") then d.Transparency = visible and 0 or 1 end
	end
end

local TweenService = game:GetService("TweenService")
local INFLATE = {"RightUpperArm", "RightLowerArm", "LeftUpperArm", "LeftLowerArm", "RightUpperLeg", "RightLowerLeg", "LeftUpperLeg", "LeftLowerLeg"}
local baseSize = {}
local function inflate(character, k, t)
	for _, n in ipairs(INFLATE) do
		local p = character:FindFirstChild(n)
		if p then
			baseSize[p] = baseSize[p] or p.Size
			local s = baseSize[p]
			TweenService:Create(p, TweenInfo.new(t or 0.3, Enum.EasingStyle.Quad), {Size = Vector3.new(s.X * k, s.Y, s.Z * k)}):Play()
		end
	end
end

local function onMarker(character, name, value)
	if name == "Pompe" then
		inflate(character, 1.24, 0.08)
		task.delay(0.1, function() inflate(character, 1.12, 0.25) end)
	end
	-- ex : if name == "Impact" then ... end
end

local function makeTube(motor)
	local p = Instance.new("Part")
	p.Name = "Elastique_" .. motor.Name
	p.Shape = Enum.PartType.Cylinder
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
	p.Material = Enum.Material.SmoothPlastic
	p.Color = motor.Part1 and motor.Part1.Color or Color3.fromRGB(230, 180, 140)
	p.Transparency = 1
	p.Parent = folder
	return p
end

local function hook(character)
	local humanoid = character:WaitForChild("Humanoid")
	local animator = humanoid:WaitForChild("Animator")
	local list = {}
	for _, n in ipairs(LIMBS) do
		local m = character:WaitForChild(n == "RightElbow" and "RightLowerArm" or n == "RightWrist" and "RightHand" or n == "LeftElbow" and "LeftLowerArm" or n == "LeftWrist" and "LeftHand" or n == "RightKnee" and "RightLowerLeg" or n == "RightAnkle" and "RightFoot" or n == "LeftKnee" and "LeftLowerLeg" or "LeftFoot", 5)
		local motor = m and m:FindFirstChild(n)
		if motor and motor:IsA("Motor6D") then table.insert(list, {m = motor, p = makeTube(motor)}) end
	end
	rigs[character] = list
	character.AncestryChanged:Connect(function(_, parent)
		if parent then return end
		for _, e in ipairs(list) do e.p:Destroy() end
		rigs[character] = nil
	end)
	animator.AnimationPlayed:Connect(function(track)
		track:GetMarkerReachedSignal("Montrer"):Connect(function(v) setVisible(character, v, true) end)
		track:GetMarkerReachedSignal("Cacher"):Connect(function(v) setVisible(character, v, false) end)
		track:GetMarkerReachedSignal("Gonfler"):Connect(function(v) inflate(character, v == "Debut" and 1.12 or 1) end)
		for _, n in ipairs({"Impact", "Aura", "Explosion", "Fin", "Esquive", "Feu", "Pompe"}) do
			track:GetMarkerReachedSignal(n):Connect(function(v) onMarker(character, n, v) end)
		end
	end)
end

RunService.RenderStepped:Connect(function()
	for _, list in pairs(rigs) do
		for _, e in ipairs(list) do
			local m = e.m
			if m.Part0 and m.Part1 then
				local a = (m.Part0.CFrame * m.C0).Position
				local b = (m.Part1.CFrame * m.C1).Position
				local d = (b - a).Magnitude
				if d > 0.15 then
					local w = math.min(m.Part1.Size.X, m.Part1.Size.Z) * 0.75
					e.p.Size = Vector3.new(d, w, w)
					e.p.CFrame = CFrame.lookAt((a + b) / 2, b) * CFrame.Angles(0, math.rad(90), 0)
					e.p.Transparency = 0
				else
					e.p.Transparency = 1
				end
			end
		end
	end
end)

local function watch(player)
	if player.Character then task.spawn(hook, player.Character) end
	player.CharacterAdded:Connect(hook)
end
for _, p in ipairs(Players:GetPlayers()) do watch(p) end
Players.PlayerAdded:Connect(watch)
