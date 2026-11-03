"""Genere le code Luau d'un apercu dans Studio : une copie figee de ModelesPersonnages.zoro par image de
anims/apercu_<Nom>.json, posee dans Workspace.Apercu_Anim (en ligne, a cote de Essais_Zoro.Zoro_v2).

Usage : uv run --with scipy assets/persos/zoro/apercu_studio.py Idle > <fichier>.luau  (puis execute via le MCP Studio, mode Edit)
Repris de assets/persos/luffy/apercu_studio.py, pour un rig a Motor6D : en mode edition, Transform ne bouge pas les
pieces ; on ancre tout et on calcule chaque CFrame (Part1 = Part0 * C0 * Transform * C1:Inverse()) ; les pieces
soudees (tenue, accessoires) suivent leur piece porteuse avec leur ecart de repos. Les accessoires Acc_* sont montres
ou caches d'apres les marqueurs du cycle Idle -> Action -> Signature.
"""

import json
import sys
from pathlib import Path

DOSSIER = Path(__file__).parent
CYCLE = ["Idle", "Action", "Signature"]
VISIBLES_DEPART = {"Acc_Sabres_Hanche"}  # attribut VisibleParDefaut du modele

LUAU = r"""local HttpService = game:GetService("HttpService")
local D = HttpService:JSONDecode([==[%JSON%]==])
local source = game.ReplicatedStorage.ModelesPersonnages.zoro
local dossier = workspace:FindFirstChild("Apercu_Anim")
if dossier then dossier:Destroy() end
dossier = Instance.new("Folder")
dossier.Name = "Apercu_Anim"
dossier.Parent = workspace
local images = {}
for k in D do table.insert(images, tonumber(k)) end
table.sort(images)
local repere = workspace:FindFirstChild("Essais_Zoro") and workspace.Essais_Zoro:FindFirstChild("Zoro_v2")
local origine = if repere then repere:GetPivot() else CFrame.new(0, 5, 0)
local function transform(t)
	if not t then return CFrame.identity end
	local r = CFrame.Angles(math.rad(t[1]), math.rad(t[2]), math.rad(t[3]))
	return if t[4] then CFrame.new(t[4], t[5], t[6]) * r else r
end
for rang, image in images do
	local info = D[tostring(image)]
	local c = source:Clone()
	c.Name = "Image_" .. image
	c:PivotTo(origine * CFrame.new(-rang * 7, 0, 0))
	local hrp = c.HumanoidRootPart
	local moteurs = {}
	for _, d in c:GetDescendants() do
		if d:IsA("Motor6D") and d.Part0 and d.Part1 and info.poses[d.Name] then
			moteurs[d.Part1] = d
		end
	end
	-- pieces suiveuses (soudures et RigidConstraint d'accessoires), avec leur ecart de repos
	local porteuses, suiveuses = {}, {}
	local L = {}
	for _, d in c:GetDescendants() do
		if (d:IsA("WeldConstraint") or d:IsA("Weld") or (d:IsA("Motor6D") and not moteurs[d.Part1])) and d.Part0 and d.Part1 then
			table.insert(L, { d.Part0, d.Part1 })
		elseif d:IsA("RigidConstraint") and d.Attachment0 and d.Attachment1 then
			table.insert(L, { d.Attachment0.Parent, d.Attachment1.Parent })
		end
	end
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
			if not faits[p1] and faits[m.Part0] then
				p1.CFrame = m.Part0.CFrame * m.C0 * transform(info.poses[m.Name]) * m.C1:Inverse()
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


def visibles_a(nom, image):
	"""Accessoires Acc_* visibles a cette image, en rejouant les marqueurs du cycle depuis le debut de l'Idle."""
	vis = set(VISIBLES_DEPART)
	for anim in CYCLE:
		d = json.loads((DOSSIER / "anims" / f"zoro_{anim}.json").read_text(encoding="utf-8"))
		for m in sorted(d["marqueurs"], key=lambda m: m["image"]):
			if anim == nom and m["image"] > image:
				break
			if m["nom"] == "Montrer":
				vis.add(m["valeur"])
			elif m["nom"] == "Cacher":
				vis.discard(m["valeur"])
		if anim == nom:
			return sorted(vis)
	raise ValueError(nom)


def generer(nom):
	d = json.loads((DOSSIER / "anims" / f"apercu_{nom}.json").read_text(encoding="utf-8"))
	sortie = {k: {"poses": {a: compacter(m) for a, m in poses.items()}, "visibles": visibles_a(nom, int(k))} for k, poses in d.items()}
	return LUAU.replace("%JSON%", json.dumps(sortie, separators=(",", ":")))


if __name__ == "__main__":
	sys.stdout.write(generer(sys.argv[1]))
