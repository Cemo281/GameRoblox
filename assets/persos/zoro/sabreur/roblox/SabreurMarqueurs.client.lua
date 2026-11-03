-- LocalScript à placer dans StarterPlayer > StarterPlayerScripts
-- Affiche / cache les Accessory des sabres selon les marqueurs Montrer / Cacher des animations.
-- Les marqueurs Impact / Aura / Explosion sont exposés via onMarker() pour brancher tes hitbox et VFX.
local Players = game:GetService("Players")

local function setVisible(character, accessoryName, visible)
	local acc = character:FindFirstChild(accessoryName)
	if not acc then return end
	for _, d in ipairs(acc:GetDescendants()) do
		if d:IsA("BasePart") or d:IsA("Decal") then d.Transparency = visible and 0 or 1 end
	end
end

local function onMarker(character, name, value)
	-- ex : if name == "Impact" then ... end
end

local function hook(character)
	local humanoid = character:WaitForChild("Humanoid")
	local animator = humanoid:WaitForChild("Animator")
	animator.AnimationPlayed:Connect(function(track)
		track:GetMarkerReachedSignal("Montrer"):Connect(function(v) setVisible(character, v, true) end)
		track:GetMarkerReachedSignal("Cacher"):Connect(function(v) setVisible(character, v, false) end)
		for _, n in ipairs({"Impact", "Aura", "Explosion"}) do
			track:GetMarkerReachedSignal(n):Connect(function(v) onMarker(character, n, v) end)
		end
	end)
end

local function watch(player)
	if player.Character then task.spawn(hook, player.Character) end
	player.CharacterAdded:Connect(hook)
end
for _, p in ipairs(Players:GetPlayers()) do watch(p) end
Players.PlayerAdded:Connect(watch)
