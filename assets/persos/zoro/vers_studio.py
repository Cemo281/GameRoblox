"""Genere le code Luau qui construit la KeyframeSequence d'une animation a partir de anims/zoro_<Nom>.json.

Usage : python assets/persos/zoro/vers_studio.py Idle > <fichier>.luau  (puis execute via le MCP Studio, mode Edit)
La sequence est rangee dans ServerStorage.RBX_ANIMSAVES.zoro (remplace celle du meme nom).
"""

import json
import sys
from pathlib import Path

DOSSIER = Path(__file__).parent

LUAU = r"""local HttpService = game:GetService("HttpService")
local D = HttpService:JSONDecode([==[%JSON%]==])
-- arbre des Motor6D : Pose nommee comme Part1, sous la Pose de Part0
local ARBRE = {
	{ "Root", "HumanoidRootPart", "LowerTorso" }, { "Waist", "LowerTorso", "UpperTorso" }, { "Neck", "UpperTorso", "Head" },
	{ "RightShoulder", "UpperTorso", "RightUpperArm" }, { "RightElbow", "RightUpperArm", "RightLowerArm" }, { "RightWrist", "RightLowerArm", "RightHand" },
	{ "LeftShoulder", "UpperTorso", "LeftUpperArm" }, { "LeftElbow", "LeftUpperArm", "LeftLowerArm" }, { "LeftWrist", "LeftLowerArm", "LeftHand" },
	{ "RightHip", "LowerTorso", "RightUpperLeg" }, { "RightKnee", "RightUpperLeg", "RightLowerLeg" }, { "RightAnkle", "RightLowerLeg", "RightFoot" },
	{ "LeftHip", "LowerTorso", "LeftUpperLeg" }, { "LeftKnee", "LeftUpperLeg", "LeftLowerLeg" }, { "LeftAnkle", "LeftLowerLeg", "LeftFoot" },
}
local saves = game.ServerStorage.RBX_ANIMSAVES.zoro
local ancien = saves:FindFirstChild(D.nom)
if ancien then ancien:Destroy() end
local ks = Instance.new("KeyframeSequence")
ks.Name = D.nom
ks.Loop = D.boucle
ks.Priority = Enum.AnimationPriority[D.priorite]
local images = {}
for _, cle in D.cles do
	local kf = Instance.new("Keyframe")
	kf.Time = cle.temps
	local poses = { HumanoidRootPart = Instance.new("Pose") }
	poses.HumanoidRootPart.Name = "HumanoidRootPart"
	poses.HumanoidRootPart.Weight = 0
	poses.HumanoidRootPart.Parent = kf
	for _, a in ARBRE do
		local p = Instance.new("Pose")
		p.Name = a[3]
		p.CFrame = CFrame.new(table.unpack(cle.poses[a[1]]))
		p.EasingStyle = Enum.PoseEasingStyle[cle.easing]
		p.EasingDirection = Enum.PoseEasingDirection.InOut
		p.Weight = 1
		p.Parent = poses[a[2]]
		poses[a[3]] = p
	end
	kf.Parent = ks
	images[cle.image] = kf
end
-- marqueurs sur la cle la plus proche (ajoutee si besoin)
for _, m in D.marqueurs do
	local kf = images[m.image]
	if not kf then
		kf = Instance.new("Keyframe")
		kf.Time = m.image / D.fps
		kf.Parent = ks
		images[m.image] = kf
	end
	local km = Instance.new("KeyframeMarker")
	km.Name = m.nom
	km.Value = m.valeur
	km.Parent = kf
end
ks.Parent = saves
local n, nm = 0, 0
for _, k in ks:GetChildren() do
	n += 1
	nm += #k:GetMarkers()
end
return string.format("%s : %d keyframes, %d marqueurs, duree %.3f s, boucle %s, priorite %s", ks.Name, n, nm, D.duree, tostring(ks.Loop), tostring(ks.Priority))
"""


def generer(nom):
	d = json.loads((DOSSIER / "anims" / f"zoro_{nom}.json").read_text(encoding="utf-8"))
	compact = {
		"nom": d["nom"],
		"boucle": d["boucle"],
		"priorite": d["priorite"],
		"fps": d["fps"],
		"duree": d["duree"],
		"cles": [{"image": c["image"], "temps": c["temps"], "easing": c["easing"], "poses": {a: [round(v, 5) for v in p["cframe"]] for a, p in c["poses"].items()}} for c in d["cles"]],
		"marqueurs": d["marqueurs"],
	}
	return LUAU.replace("%JSON%", json.dumps(compact, separators=(",", ":")))


if __name__ == "__main__":
	sys.stdout.write(generer(sys.argv[1]))
