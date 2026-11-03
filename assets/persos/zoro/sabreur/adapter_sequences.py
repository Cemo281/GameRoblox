"""Adapte roblox/SabreurAnimations.lua (généré depuis anims.js par le visualiseur, SABRE.toLuau())
au rig de zoro et au module client Vitrine. Sortie : creer_sequences.luau (lancé par MCP ou barre de commande).

- reprend les 4 clips du handoff (poses, easing, marqueurs d'origine) dans un format compact (parties à zéro omises) ;
- reconstruit Sabreur_Sequence_Complete en les mettant bout à bout (vérifié identique à celle du handoff) ;
- cible un clone de ReplicatedStorage.ModelesPersonnages.zoro dans Workspace.Sabreur_Apercu (pas la Selection) ;
- renomme les valeurs Montrer / Cacher vers les accessoires de zoro (Acc_Sabre_*) ;
- ajoute les marqueurs « VFX <Nom> » lus par src/client/Vitrine.luau (effets créés par vfx_sabreur.luau).

Usage : python -I adapter_sequences.py
"""

import pathlib
import re

ICI = pathlib.Path(__file__).resolve().parent
CLIPS = ["Sabreur_Degainage", "Sabreur_Charge_Aura", "Sabreur_Combat_Esquives", "Sabreur_Rengainage"]
SEQUENCE = "Sabreur_Sequence_Complete"


def lire(source: str) -> dict:
	anims = {}
	for bloc in re.split(r"\n  \{name = ", source)[1:]:
		nom = re.match(r'"(\w+)"', bloc).group(1)
		entete = re.match(r'"\w+", loop = (\w+), priority = "(\w+)"', bloc)
		cles = []
		for m in re.finditer(r'\{t = ([\d.]+), e = "(\w+)", d = "(\w+)", p = \{(.*?)\}\}', bloc):
			parties = {a: [float(x) for x in b.split(",")] for a, b in re.findall(r"(\w+) = \{([^}]*)\}", m.group(4))}
			cles.append((float(m.group(1)), m.group(2), m.group(3), parties))
		marqueurs = [(float(a), b, c) for a, b, c in re.findall(r'\{([\d.]+), "(\w+)", "(\w+)"\}', bloc.split("markers = ")[1])]
		anims[nom] = {"loop": entete.group(1), "priority": entete.group(2), "cles": cles, "marqueurs": marqueurs}
	return anims


def nombre(x: float) -> str:
	return format(x, "g")


def verifier_sequence(anims: dict) -> list:
	"""Décalage de chaque clip dans la séquence complète, après vérification qu'elle en est la concaténation."""
	decalages, concat, debut = [], [], 0.0
	for nom in CLIPS:
		decalages.append(debut)
		for t, e, d, p in anims[nom]["cles"]:
			t = round(t + debut, 4)
			if concat and abs(concat[-1][0] - t) < 1e-4:
				concat.pop()
			concat.append((t, e, d, p))
		debut = round(debut + anims[nom]["cles"][-1][0], 4)
	attendu = anims[SEQUENCE]["cles"]
	assert len(concat) == len(attendu) and all(
		abs(a[0] - b[0]) < 1e-4 and a[1:] == b[1:] for a, b in zip(concat, attendu)
	), "Sabreur_Sequence_Complete n'est plus la concaténation des 4 clips : adapter le générateur"
	return decalages


def luau_clips(anims: dict) -> str:
	lignes = ["local CLIPS = {"]
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


source = (ICI / "roblox" / "SabreurAnimations.lua").read_text(encoding="utf-8")
anims = lire(source)
decalages = verifier_sequence(anims)
tree = re.search(r"^local TREE = .*$", source, re.M).group(0)

ENTETE = """--!nocheck
-- Généré par adapter_sequences.py depuis roblox/SabreurAnimations.lua (handoff « sabreur à trois sabres »).
-- Ne pas modifier à la main : modifier anims.js, régénérer SabreurAnimations.lua (SABRE.toLuau()), relancer le .py.
-- Crée Workspace.Sabreur_Apercu (clone de ModelesPersonnages.zoro, ancré) et ses 5 KeyframeSequence dans
-- ServerStorage.RBX_ANIMSAVES.Sabreur_Apercu. Ensuite : Éditeur d'animation > Sabreur_Apercu > Charger > Publier.
-- Lancer vfx_sabreur.luau avant (sabre en bouche retourné, effets Sabreur_* copiés avec le clone).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local source = ReplicatedStorage.ModelesPersonnages.zoro
-- le rig existant est réutilisé : l'Éditeur d'animation suit l'instance du rig, en recréer un lui fait créer un
-- nouveau dossier vide dans RBX_ANIMSAVES et « perdre » les animations (supprimer le rig à la main pour le refaire)
local rig = workspace:FindFirstChild("Sabreur_Apercu")
local nouveau = rig == nil
if nouveau then
rig = source:Clone()
rig.Name = "Sabreur_Apercu"
for _, attribut in { "AnimationIdle", "AnimationAction", "AnimationSignature", "AnimationSequence" } do
	rig:SetAttribute(attribut, nil)
end
rig.HumanoidRootPart.Anchored = true
-- zone d'essais dans le ciel, à côté de Workspace.Essais_Zoro (hors de l'île)
local voisin = workspace:FindFirstChild("Essais_Zoro") and workspace.Essais_Zoro:FindFirstChild("Zoro_v2")
rig:PivotTo(if voisin then voisin:GetPivot() + Vector3.new(30, 0, 0) else CFrame.new(25, 303, 400))
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

SUITE = f"""
-- Séquence complète = les 4 clips bout à bout (la 1re clé d'un clip remplace la dernière du précédent)
local DECALAGES = {{ {", ".join(nombre(d) for d in decalages)} }}
local sequence = {{ name = "{SEQUENCE}", loop = false, priority = "Action", keys = {{}}, markers = {{}} }}
for i, clip in ipairs(CLIPS) do
	local dec = DECALAGES[i]
	for _, k in ipairs(clip.keys) do
		local t = math.round((k.t + dec) * 10000) / 10000
		local derniere = sequence.keys[#sequence.keys]
		if derniere and math.abs(derniere.t - t) < 1e-4 then
			table.remove(sequence.keys)
		end
		table.insert(sequence.keys, {{ t = t, e = k.e, d = k.d, p = k.p }})
	end
	for _, m in ipairs(clip.markers) do
		table.insert(sequence.markers, {{ math.round((m[1] + dec) * 10000) / 10000, m[2], m[3] }})
	end
end
local ANIMS = {{ sequence, CLIPS[1], CLIPS[2], CLIPS[3], CLIPS[4] }}

-- Accessoires du handoff → accessoires de zoro
local RENOMMER = {{
	SabresHanche = "Acc_Sabres_Hanche",
	SabreDroit = "Acc_Sabre_Droit",
	SabreGauche = "Acc_Sabre_Gauche",
	SabreBouche = "Acc_Sabre_Bouche",
}}
-- Les effets ne passent plus par des marqueurs « VFX » : src/client/Vitrine.luau déclenche zoro.VFX.<Marqueur>_<Valeur>
-- (Aura_Debut, Explosion_Aura, Impact_Sol…, créés par vfx_sabreur.luau) directement sur les marqueurs d'origine.
-- L'Éditeur d'animation ne publie qu'un marqueur de chaque nom par image clé : deux « VFX » au même instant en perdaient un.
local EFFETS = {{}}
-- Traînées des lames pendant tout le combat
local DEBUT_COMBAT = {{ Sabreur_Combat_Esquives = 0.1, {SEQUENCE} = {nombre(decalages[CLIPS.index("Sabreur_Combat_Esquives")] + 0.1)} }}

for _, a in ipairs(ANIMS) do
	local liste = {{}}
	for _, m in ipairs(a.markers) do
		local t, nom, valeur = m[1], m[2], m[3]
		if nom == "Montrer" or nom == "Cacher" then
			table.insert(liste, {{ t, nom, RENOMMER[valeur] or valeur }})
		else
			table.insert(liste, m)
			for _, effet in ipairs(EFFETS[nom .. "/" .. valeur] or {{}}) do
				table.insert(liste, {{ t, "VFX", effet }})
			end
		end
	end
	if DEBUT_COMBAT[a.name] then
		table.insert(liste, {{ DEBUT_COMBAT[a.name], "VFX", "Sabreur_Trail" }})
	end
	a.markers = liste
end

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

local bilan = {{}}
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
print("creer_sequences.luau :", len(sortie), "caracteres, decalages", decalages)
