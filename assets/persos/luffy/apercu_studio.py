"""Genere le code Luau d'un apercu dans Studio : une copie figee de luffy par image de anims/apercu_<Nom>.json,
posee dans Workspace.Apercu_Anim (en ligne, a cote du modele).

Usage : uv run --with scipy assets/persos/luffy/apercu_studio.py Idle > <fichier>.luau  (puis execute via le MCP Studio, mode Edit)
Repris de assets/persos/nami/apercu_studio.py, pour un rig a AnimationConstraint (avatar du catalogue) : en mode
edition, Transform ne bouge pas les pieces ; on ancre tout et on calcule chaque CFrame
(Part1 = Part0 * C0 * Transform * C1:Inverse(), C0 / C1 = CFrame des Attachment0 / Attachment1) ; les pieces soudees
(tenue, accessoires) suivent leur piece porteuse avec leur ecart de repos. Seuls les accessoires Acc_* sont montres ou
caches selon l'image.
"""

import json
import sys
from pathlib import Path

DOSSIER = Path(__file__).parent

LUAU = r"""local HttpService = game:GetService("HttpService")
local D = HttpService:JSONDecode([==[%JSON%]==])
local source = game.ReplicatedStorage.ModelesPersonnages:FindFirstChild("luffy") or workspace.luffy
local dossier = workspace:FindFirstChild("Apercu_Anim")
if dossier then dossier:Destroy() end
dossier = Instance.new("Folder")
dossier.Name = "Apercu_Anim"
dossier.Parent = workspace
local images = {}
for k in D do table.insert(images, tonumber(k)) end
table.sort(images)
local origine = workspace.luffy:GetPivot()
local function transform(t)
	local r = CFrame.Angles(math.rad(t[1]), math.rad(t[2]), math.rad(t[3]))
	return if t[4] then CFrame.new(t[4], t[5], t[6]) * r else r
end
for rang, image in images do
	local info = D[tostring(image)]
	local c = source:Clone()
	c.Name = "Image_" .. image
	local anim = c:FindFirstChild("Animate")
	if anim then anim:Destroy() end
	c:PivotTo(origine * CFrame.new(-rang * 5, 0, 0))
	local hrp = c.HumanoidRootPart
	local moteurs = {}
	for _, d in c:GetDescendants() do
		if d:IsA("AnimationConstraint") and d.Attachment0 and d.Attachment1 then
			moteurs[d.Attachment1.Parent] = d
		end
	end
	-- pieces suiveuses (soudures et RigidConstraint d'accessoires), avec leur ecart de repos
	local porteuses, suiveuses = {}, {}
	local function liens()
		local l = {}
		for _, d in c:GetDescendants() do
			if (d:IsA("WeldConstraint") or d:IsA("Weld")) and d.Part0 and d.Part1 then
				table.insert(l, { d.Part0, d.Part1 })
			elseif d:IsA("RigidConstraint") and d.Attachment0 and d.Attachment1 then
				table.insert(l, { d.Attachment0.Parent, d.Attachment1.Parent })
			end
		end
		return l
	end
	local L = liens()
	for _ = 1, 4 do
		for _, lien in L do
			for _, paire in { { lien[1], lien[2] }, { lien[2], lien[1] } } do
				local p, autre = paire[1], paire[2]
				if p:IsA("BasePart") and autre:IsA("BasePart") and not moteurs[p] and p ~= hrp and not porteuses[p] and (moteurs[autre] or autre == hrp or porteuses[autre]) then
					porteuses[p] = autre
					table.insert(suiveuses, { p, autre, autre.CFrame:Inverse() * p.CFrame })
				end
			end
		end
	end
	for _, d in c:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true end
		if d:IsA("JointInstance") or d:IsA("WeldConstraint") or d:IsA("Constraint") then d.Enabled = false end
	end
	local faits = { [hrp] = true }
	local reste = true
	while reste do
		reste = false
		for p1, m in moteurs do
			local p0 = m.Attachment0.Parent
			if not faits[p1] and faits[p0] then
				p1.CFrame = p0.CFrame * m.Attachment0.CFrame * transform(info.poses[m.Name]) * m.Attachment1.CFrame:Inverse()
				faits[p1] = true
				reste = true
			end
		end
	end
	for _, s in suiveuses do
		s[1].CFrame = s[2].CFrame * s[3]
	end
	local visibles = {}
	for _, n in info.visibles do visibles[n] = true end
	for _, a in c:GetChildren() do
		if a:IsA("Accessory") and string.sub(a.Name, 1, 4) == "Acc_" then
			for _, p in a:GetDescendants() do
				if p:IsA("BasePart") then p.Transparency = visibles[a.Name] and 0 or 1 end
			end
		end
	end
	c.Parent = dossier
end
return #images .. " images posees"
"""


def compacter(m):
	from scipy.spatial.transform import Rotation as R

	rot = R.from_matrix([m[3:6], m[6:9], m[9:12]]).as_euler("XYZ", degrees=True)  # = CFrame.Angles(rx, ry, rz)
	v = [round(float(a), 1) for a in rot]
	if any(abs(c) > 1e-4 for c in m[:3]):
		v += [round(c, 3) for c in m[:3]]
	return v


def generer(nom):
	d = json.loads((DOSSIER / "anims" / f"apercu_{nom}.json").read_text(encoding="utf-8"))
	for info in d.values():  # angles en degres (1 decimale) + position : code envoye a Studio 4 fois plus court
		info["poses"] = {a: compacter(m) for a, m in info["poses"].items()}
	return LUAU.replace("%JSON%", json.dumps(d, separators=(",", ":")))


if __name__ == "__main__":
	sys.stdout.write(generer(sys.argv[1]))
