"""Adapte roblox/ElastiqueAnimations.lua (généré depuis elastique.js, toLuau()) à la vitrine de luffy.
Sortie : creer_sequences.luau (lancé par MCP ; trop gros pour être collé, passer par un ModuleScript temporaire).

- ne garde que Elastique_Sequence_Complete (Gear 2 → Combo), la seule jouée par la vitrine, et éventuellement
  les autres clips listés dans CLIPS ;
- format compact (parties à zéro omises) ;
- cible un clone de ReplicatedStorage.ModelesPersonnages.luffy dans Workspace.Elastique_Apercu (pas la Selection),
  ancré, et réutilise le dossier ServerStorage.RBX_ANIMSAVES.Elastique_Apercu de l'Éditeur d'animation
  (un 2e dossier du même nom est ignoré par l'éditeur) ;
- les marqueurs sont gardés tels quels : src/client/Vitrine.luau déclenche luffy.VFX.<Marqueur>_<Valeur>
  (vfx_elastique.luau) et src/client/Elastique.luau gère Gonfler / Pompe.

Usage : python -I adapter_sequences.py
"""

import pathlib
import re

ICI = pathlib.Path(__file__).resolve().parent
CLIPS = ["Elastique_Sequence_Complete"]


def lire(source: str) -> dict:
	anims = {}
	for bloc in re.split(r"\n  \{name = ", source)[1:]:
		nom = re.match(r'"(\w+)"', bloc).group(1)
		entete = re.match(r'"\w+", loop = (\w+), priority = "(\w+)"', bloc)
		cles = []
		for m in re.finditer(r'\{t = ([\d.]+), e = "(\w+)", d = "(\w+)", p = \{(.*?)\}\}', bloc):
			parties = {a: [float(x) for x in b.split(",")] for a, b in re.findall(r"(\w+) = \{([^}]*)\}", m.group(4))}
			cles.append((float(m.group(1)), m.group(2), m.group(3), parties))
		marqueurs = [
			(float(a), b, c) for a, b, c in re.findall(r'\{([\d.]+), "(\w+)", "(\w+)"\}', bloc.split("markers = ")[1])
		]
		anims[nom] = {"loop": entete.group(1), "priority": entete.group(2), "cles": cles, "marqueurs": marqueurs}
	return anims


def nombre(x: float) -> str:
	return format(x, "g")


def verifier(anims: dict):
	"""Un seul marqueur de chaque nom par instant : l'Éditeur d'animation ne publie pas les doublons."""
	for nom in CLIPS:
		vus = {}
		for t, n, v in anims[nom]["marqueurs"]:
			cle = (round(t, 4), n)
			if cle in vus and vus[cle] != v:
				print(f"ATTENTION {nom} : deux marqueurs « {n} » à {t} s ({vus[cle]}, {v}) : un seul sera publié")
			vus[cle] = v


def luau_clips(anims: dict) -> str:
	lignes = ["local ANIMS = {"]
	for nom in CLIPS:
		a = anims[nom]
		lignes.append(f'\t{{ name = "{nom}", loop = {a["loop"]}, priority = "{a["priority"]}", keys = {{')
		for t, e, d, p in a["cles"]:
			poses = ", ".join(
				f"{partie} = {{{', '.join(nombre(v) for v in valeurs)}}}"
				for partie, valeurs in p.items()
				if any(v != 0 for v in valeurs)
			)
			lignes.append(f'\t\t{{ t = {nombre(t)}, e = "{e}", d = "{d}", p = {{ {poses} }} }},')
		marqueurs = ", ".join(f'{{ {nombre(t)}, "{n}", "{v}" }}' for t, n, v in a["marqueurs"])
		lignes.append(f"\t}}, markers = {{ {marqueurs} }} }},")
	lignes.append("}")
	return "\n".join(lignes)


source = (ICI / "roblox" / "ElastiqueAnimations.lua").read_text(encoding="utf-8")
anims = lire(source)
verifier(anims)
tree = re.search(r"^local TREE = .*$", source, re.M).group(0)

ENTETE = """--!nocheck
-- Généré par adapter_sequences.py depuis roblox/ElastiqueAnimations.lua (handoff « combattant élastique »).
-- Ne pas modifier à la main : modifier elastique.js, régénérer ElastiqueAnimations.lua (toLuau()), relancer le .py.
-- Crée Workspace.Elastique_Apercu (clone de ModelesPersonnages.luffy, ancré) et ses KeyframeSequence dans
-- ServerStorage.RBX_ANIMSAVES.Elastique_Apercu. Ensuite : Éditeur d'animation > Elastique_Apercu > Charger > Publier.
-- Renvoie un bilan ; lancé par require() d'un ModuleScript temporaire (le script renvoie une chaîne).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local source = ReplicatedStorage.ModelesPersonnages.luffy
-- le rig existant est réutilisé : l'Éditeur d'animation suit l'instance du rig, en recréer un lui fait créer un
-- nouveau dossier vide dans RBX_ANIMSAVES et « perdre » les animations (supprimer le rig à la main pour le refaire)
local rig = workspace:FindFirstChild("Elastique_Apercu")
local nouveau = rig == nil
if nouveau then
rig = source:Clone()
rig.Name = "Elastique_Apercu"
for _, attribut in { "AnimationIdle", "AnimationAction", "AnimationSignature", "AnimationSequence" } do
	rig:SetAttribute(attribut, nil)
end
rig.HumanoidRootPart.Anchored = true
-- zone d'essais dans le ciel, à côté de Workspace.Sabreur_Apercu / Essais_Zoro (hors de l'île)
local voisin = workspace:FindFirstChild("Sabreur_Apercu")
rig:PivotTo(if voisin then voisin:GetPivot() + Vector3.new(15, 0, 0) else CFrame.new(40, 303, 400))
rig.Parent = workspace
end

local saves = ServerStorage:FindFirstChild("RBX_ANIMSAVES")
if not saves then saves = Instance.new("Folder") saves.Name = "RBX_ANIMSAVES" saves.Parent = ServerStorage end
-- un seul dossier par rig, réutilisé (l'Éditeur d'animation ignore un 2e dossier du même nom) ; il pointe vers le rig recréé
-- s'il y en a plusieurs, garder le dernier créé (celui que l'éditeur lit) et y regrouper le contenu des autres
local holder
for _, c in saves:GetChildren() do
	if c.Name == rig.Name then
		if holder then
			for _, s in holder:GetChildren() do s.Parent = c end
			holder:Destroy()
		end
		holder = c
	end
end
if not holder then holder = Instance.new("ObjectValue") holder.Name = rig.Name holder.Parent = saves end
holder.Value = rig
local animSavesRig = rig:FindFirstChild("AnimSaves")
if animSavesRig then animSavesRig:Destroy() end -- ancien emplacement : l'éditeur demanderait une migration

local rad = math.rad
local ZERO = { 0, 0, 0, 0, 0, 0 }
local STYLE = { Cubic = Enum.PoseEasingStyle.CubicV2, Linear = Enum.PoseEasingStyle.Linear, Constant = Enum.PoseEasingStyle.Constant, Elastic = Enum.PoseEasingStyle.Elastic, Bounce = Enum.PoseEasingStyle.Bounce }
"""

SUITE = """
local function addPose(kf, parentPose, node, k)
	local name, children = node[1], node[2]
	local v = k.p[name] or ZERO
	local pose = Instance.new("Pose")
	pose.Name = name
	pose.CFrame = CFrame.new(v[1], v[2], v[3]) * CFrame.Angles(rad(v[4]), rad(v[5]), rad(v[6]))
	pose.Weight = 1
	pose.EasingStyle = STYLE[k.e]
	pose.EasingDirection = Enum.PoseEasingDirection[k.d]
	parentPose:AddSubPose(pose)
	for _, child in ipairs(children) do addPose(kf, pose, child, k) end
end

local bilan = {}
for _, a in ipairs(ANIMS) do
	local seq = Instance.new("KeyframeSequence")
	seq.Name = a.name
	seq.Loop = a.loop
	seq.Priority = Enum.AnimationPriority[a.priority]
	for _, k in ipairs(a.keys) do
		local kf = Instance.new("Keyframe")
		kf.Time = k.t
		local hrp = Instance.new("Pose")
		hrp.Name = "HumanoidRootPart"
		hrp.Weight = 0
		kf:AddPose(hrp)
		addPose(kf, hrp, TREE, k)
		kf.Parent = seq
	end
	for _, m in ipairs(a.markers) do
		local kf
		for _, existing in ipairs(seq:GetKeyframes()) do
			if math.abs(existing.Time - m[1]) < 1e-4 then kf = existing break end
		end
		if not kf then kf = Instance.new("Keyframe") kf.Time = m[1] kf.Parent = seq end
		local mk = Instance.new("KeyframeMarker")
		mk.Name = m[2]
		mk.Value = m[3]
		kf:AddMarker(mk)
	end
	local ancienne = holder:FindFirstChild(a.name)
	if ancienne then ancienne:Destroy() end
	seq.Parent = holder
	table.insert(bilan, a.name .. " : " .. #a.keys .. " clés, " .. #a.markers .. " marqueurs")
end
return table.concat(bilan, "\\n")
"""

sortie = ENTETE + tree + "\n" + luau_clips(anims) + "\n" + SUITE
(ICI / "creer_sequences.luau").write_text(sortie, encoding="utf-8")
print("creer_sequences.luau :", len(sortie), "caracteres")
