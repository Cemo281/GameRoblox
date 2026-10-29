"""Genere le code Luau d'un apercu dans Studio : une copie figee de ModelesPersonnages.nami par image de
anims/apercu_<Nom>.json, posee dans Workspace.Apercu_Anim (en ligne, en (-14, y, 300)).

Usage : python assets/persos/nami/apercu_studio.py Idle > <fichier>.luau  (puis execute via le MCP Studio, mode Edit)
En mode edition, Motor6D.Transform ne bouge pas les pieces : on ancre tout et on calcule chaque CFrame
(Part1 = Part0 * C0 * Transform * C1:Inverse()) ; les pieces soudees (vetements, cheveux, accessoires) suivent leur
piece porteuse avec leur ecart de repos.
"""

import json
import sys
from pathlib import Path

DOSSIER = Path(__file__).parent

LUAU = r"""local HttpService = game:GetService("HttpService")
local D = HttpService:JSONDecode([==[%JSON%]==])
local dossier = workspace:FindFirstChild("Apercu_Anim")
if dossier then dossier:Destroy() end
dossier = Instance.new("Folder")
dossier.Name = "Apercu_Anim"
dossier.Parent = workspace
local images = {}
for k in D do table.insert(images, tonumber(k)) end
table.sort(images)
for rang, image in images do
	local info = D[tostring(image)]
	local c = game.ReplicatedStorage.ModelesPersonnages.nami:Clone()
	c.Name = "Image_" .. image
	local hum = c:FindFirstChildOfClass("Humanoid")
	if hum then hum:Destroy() end -- pas de recalage des accessoires par le Humanoid
	c:PivotTo(CFrame.new(-14 + (rang - 1) * 4.5, 3.192428, 300))
	local hrp = c.HumanoidRootPart
	-- moteurs et pieces suiveuses (avec leur ecart de repos)
	local moteurs, porteuses = {}, {}
	for _, d in c:GetDescendants() do
		if d:IsA("Motor6D") then moteurs[d.Part1] = d end
	end
	local suiveuses = {}
	for _, d in c:GetDescendants() do
		if (d:IsA("WeldConstraint") or d:IsA("Weld")) and d.Part0 and d.Part1 then
			for _, paire in { { d.Part0, d.Part1 }, { d.Part1, d.Part0 } } do
				local p, autre = paire[1], paire[2]
				if not moteurs[p] and p ~= hrp and (moteurs[autre] or autre == hrp or porteuses[autre]) and not porteuses[p] then
					porteuses[p] = autre
					table.insert(suiveuses, { p, autre, autre.CFrame:Inverse() * p.CFrame })
				end
			end
		end
	end
	-- pieces suiveuses de suiveuses (ex. pieces du baton soudees au Handle)
	for _ = 1, 3 do
		for _, d in c:GetDescendants() do
			if (d:IsA("WeldConstraint") or d:IsA("Weld")) and d.Part0 and d.Part1 then
				for _, paire in { { d.Part0, d.Part1 }, { d.Part1, d.Part0 } } do
					local p, autre = paire[1], paire[2]
					if not moteurs[p] and p ~= hrp and not porteuses[p] and porteuses[autre] then
						porteuses[p] = autre
						table.insert(suiveuses, { p, autre, autre.CFrame:Inverse() * p.CFrame })
					end
				end
			end
		end
	end
	for _, d in c:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true end
		if d:IsA("JointInstance") or d:IsA("WeldConstraint") then d.Enabled = false end
	end
	-- pose : parcours de l'arbre des moteurs depuis HumanoidRootPart
	local faits = { [hrp] = true }
	local reste = true
	while reste do
		reste = false
		for p1, m in moteurs do
			if not faits[p1] and faits[m.Part0] then
				local t = info.poses[m.Name]
				p1.CFrame = m.Part0.CFrame * m.C0 * CFrame.new(table.unpack(t)) * m.C1:Inverse()
				faits[p1] = true
				reste = true
			end
		end
	end
	for _, s in suiveuses do
		s[1].CFrame = s[2].CFrame * s[3]
	end
	-- accessoires visibles a cette image
	local visibles = {}
	for _, n in info.visibles do visibles[n] = true end
	for _, a in c:GetChildren() do
		if a:IsA("Accessory") then
			for _, p in a:GetDescendants() do
				if p:IsA("BasePart") then p.Transparency = visibles[a.Name] and 0 or 1 end
			end
		end
	end
	c.Parent = dossier
end
game:GetService("ContentProvider"):PreloadAsync({ dossier })
return #images .. " images posees"
"""


def generer(nom):
	d = json.loads((DOSSIER / "anims" / f"apercu_{nom}.json").read_text(encoding="utf-8"))
	return LUAU.replace("%JSON%", json.dumps(d, separators=(",", ":")))


if __name__ == "__main__":
	sys.stdout.write(generer(sys.argv[1]))
