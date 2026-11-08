"""Code Luau pour Studio (a lancer par le MCP, mode Edit) a partir des JSON de anims/.

  apercu <Nom>   : une copie figee de usopp par image de anims/apercu_<Nom>.json, en ligne dans Workspace.Apercu_Anim
                   (rig Motor6D : Part1 = Part0 * C0 * Transform * C1:Inverse(), pieces ancrees ; accessoires et pieces
                   soudees suivent leur porteuse ; seuls les accessoires Acc_LancePierre_* sont montres / caches).
  sequence <Nom> : KeyframeSequence de anims/usopp_<Nom>.json dans ServerStorage.RBX_ANIMSAVES.usopp_test, rig Workspace.usopp_test (meme gabarit
                   que assets/persos/luffy/vers_studio.py) ; trop gros pour le MCP : passer par un module temporaire
                   src/shared/Temp*.luau (voir CLAUDE.md).

Usage : uv run --with scipy python -I assets/persos/usopp/outils_studio.py apercu Sequence > fichier.luau
"""

import importlib.util
import json
import sys
from pathlib import Path

ICI = Path(__file__).parent

APERCU = r"""local HttpService = game:GetService("HttpService")
local D = HttpService:JSONDecode([==[%JSON%]==])
local source = workspace.Essais_Usopp.usopp
local dossier = workspace:FindFirstChild("Apercu_Anim")
if dossier then dossier:Destroy() end
dossier = Instance.new("Folder")
dossier.Name = "Apercu_Anim"
dossier.Parent = workspace
local images = {}
for k in D do table.insert(images, tonumber(k)) end
table.sort(images)
local origine = source:GetPivot() * CFrame.new(0, 0, -14)
local ARTS = { RightUpperArm = "RightShoulder", RightLowerArm = "RightElbow", RightHand = "RightWrist", LeftUpperArm = "LeftShoulder",
	LeftLowerArm = "LeftElbow", LeftHand = "LeftWrist", UpperTorso = "Waist", LowerTorso = "Root", Head = "Neck", RightUpperLeg = "RightHip",
	RightLowerLeg = "RightKnee", RightFoot = "RightAnkle", LeftUpperLeg = "LeftHip", LeftLowerLeg = "LeftKnee", LeftFoot = "LeftAnkle" }
local function transform(t)
	local r = CFrame.Angles(math.rad(t[1]), math.rad(t[2]), math.rad(t[3]))
	return if t[4] then CFrame.new(t[4], t[5], t[6]) * r else r
end
for rang, image in images do
	local info = D[tostring(image)]
	local c = source:Clone()
	c.Name = "Image_" .. image
	c:PivotTo(origine * CFrame.new(-(rang - 1) * %PAS%, 0, 0))
	local hrp = c.HumanoidRootPart
	local moteurs = {}
	for _, d in c:GetDescendants() do
		if d:IsA("Motor6D") and d.Part0 and d.Part1 then moteurs[d.Part1] = d end
	end
	local liens = {}
	for _, d in c:GetDescendants() do
		if (d:IsA("WeldConstraint") or d:IsA("Weld")) and d.Part0 and d.Part1 then
			table.insert(liens, { d.Part0, d.Part1 })
		elseif d:IsA("RigidConstraint") and d.Attachment0 and d.Attachment1 then
			table.insert(liens, { d.Attachment0.Parent, d.Attachment1.Parent })
		end
	end
	local porteuses, suiveuses = {}, {}
	for _ = 1, 4 do
		for _, lien in liens do
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
				p1.CFrame = m.Part0.CFrame * m.C0 * transform(info.poses[ARTS[p1.Name]]) * m.C1:Inverse()
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
		if a:IsA("Accessory") and string.sub(a.Name, 1, 16) == "Acc_LancePierre_" then
			a.Handle.Transparency = visibles[a.Name] and 0 or 1
		end
	end
	local etiquette = Instance.new("BillboardGui")
	etiquette.Size = UDim2.fromOffset(60, 24)
	etiquette.StudsOffset = Vector3.new(0, 4, 0)
	etiquette.AlwaysOnTop = true
	local t = Instance.new("TextLabel")
	t.Size = UDim2.fromScale(1, 1)
	t.BackgroundTransparency = 1
	t.TextScaled = true
	t.Text = tostring(image)
	t.TextColor3 = Color3.new(1, 1, 1)
	t.TextStrokeTransparency = 0
	t.Parent = etiquette
	etiquette.Parent = hrp
	c.Parent = dossier
end
return #images .. " images posees"
"""


def apercu(nom, pas=6):
	spec = importlib.util.spec_from_file_location("apercu_luffy", ICI.parent / "luffy" / "apercu_studio.py")
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	d = json.loads((ICI / "anims" / f"apercu_{nom}.json").read_text(encoding="utf-8"))
	for info in d.values():
		info["poses"] = {a: module.compacter(m) for a, m in info["poses"].items()}
	return APERCU.replace("%JSON%", json.dumps(d, separators=(",", ":"))).replace("%PAS%", str(pas))


def sequence(nom):
	spec = importlib.util.spec_from_file_location("vers_studio_luffy", ICI.parent / "luffy" / "vers_studio.py")
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	module.DOSSIER = ICI
	luau = module.LUAU.replace('local saves = racine:FindFirstChild("luffy")', 'local saves = racine:FindFirstChild("usopp_test")')
	luau = luau.replace('saves.Name = "luffy"', 'saves.Name = "usopp_test"').replace('workspace:FindFirstChild("luffy")', 'workspace:FindFirstChild("usopp_test")')
	d = json.loads((ICI / "anims" / f"usopp_{nom}.json").read_text(encoding="utf-8"))
	compact = {
		"nom": d["nom"],
		"boucle": d["boucle"],
		"priorite": d["priorite"],
		"fps": d["fps"],
		"duree": d["duree"],
		"cles": [{"image": c["image"], "temps": c["temps"], "easing": c["easing"], "poses": {a: module.compacter(p) for a, p in c["poses"].items()}} for c in d["cles"]],
		"marqueurs": d["marqueurs"],
	}
	return luau.replace("%JSON%", json.dumps(compact, separators=(",", ":")).replace(".0,", ",").replace(".0]", "]"))


def temp(nom):
	"""Poses d'apercu en JSON dans src/shared/TempApercuUsopp.luau (synchronise par Rojo), lu dans Studio par
	require(<clone>) puis ServerStorage.OutilsUsopp.apercu(HttpService:JSONDecode(...), pas). A supprimer apres."""
	spec = importlib.util.spec_from_file_location("apercu_luffy", ICI.parent / "luffy" / "apercu_studio.py")
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	d = json.loads((ICI / "anims" / f"apercu_{nom}.json").read_text(encoding="utf-8"))
	for info in d.values():
		info["poses"] = {a: module.compacter(m) for a, m in info["poses"].items()}
	cible = ICI.parents[2] / "src" / "shared" / "TempApercuUsopp.luau"
	cible.write_text("-- Temporaire (apercu de usopp, assets/persos/usopp/outils_studio.py) : a supprimer" + chr(10) + "return [==[" + json.dumps(d, separators=(",", ":")) + "]==]" + chr(10), encoding="utf-8")
	print("ecrit", cible, len(d), "images")


if __name__ == "__main__":
	quoi, nom = sys.argv[1], sys.argv[2]
	if quoi == "temp":
		temp(nom)
		sys.exit(0)
	sys.stdout.reconfigure(encoding="utf-8")
	sys.stdout.write(apercu(nom) if quoi == "apercu" else sequence(nom))
