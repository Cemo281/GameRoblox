--!nocheck
-- Généré par adapter_sequences.py depuis roblox/SabreurAnimations.lua (handoff « sabreur à trois sabres »).
-- Ne pas modifier à la main : modifier anims.js, régénérer SabreurAnimations.lua (SABRE.toLuau()), relancer le .py.
-- Crée Workspace.Sabreur_Apercu (clone de ModelesPersonnages.zoro, ancré) et ses 5 KeyframeSequence dans
-- ServerStorage.RBX_ANIMSAVES.Sabreur_Apercu. Ensuite : Éditeur d'animation > Sabreur_Apercu > Charger > Publier.
-- Lancer vfx_sabreur.luau avant (sabre en bouche retourné, effets Sabreur_* copiés avec le clone).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local source = ReplicatedStorage.ModelesPersonnages.zoro
local rig = workspace:FindFirstChild("Sabreur_Apercu")
if rig then rig:Destroy() end
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

local saves = ServerStorage:FindFirstChild("RBX_ANIMSAVES")
if not saves then saves = Instance.new("Folder") saves.Name = "RBX_ANIMSAVES" saves.Parent = ServerStorage end
-- un seul dossier par rig, réutilisé (l'Éditeur d'animation ignore un 2e dossier du même nom) ; il pointe vers le rig recréé
local holder
for _, c in saves:GetChildren() do
	if c.Name == rig.Name then
		if holder then c:Destroy() else holder = c end
	end
end
if not holder then holder = Instance.new("ObjectValue") holder.Name = rig.Name holder.Parent = saves end
holder.Value = rig
local animSavesRig = rig:FindFirstChild("AnimSaves")
if animSavesRig then animSavesRig:Destroy() end -- ancien emplacement : l'éditeur demanderait une migration

local rad = math.rad
local ZERO = { 0, 0, 0, 0, 0, 0 }
local STYLE = { Cubic = Enum.PoseEasingStyle.CubicV2, Linear = Enum.PoseEasingStyle.Linear, Constant = Enum.PoseEasingStyle.Constant, Elastic = Enum.PoseEasingStyle.Elastic, Bounce = Enum.PoseEasingStyle.Bounce }
local TREE = {"LowerTorso", {{"UpperTorso", {{"Head", {}}, {"RightUpperArm", {{"RightLowerArm", {{"RightHand", {}}}}}}, {"LeftUpperArm", {{"LeftLowerArm", {{"LeftHand", {}}}}}}}}, {"RightUpperLeg", {{"RightLowerLeg", {{"RightFoot", {}}}}}}, {"LeftUpperLeg", {{"LeftLowerLeg", {{"LeftFoot", {}}}}}}}}
local CLIPS = {
	{ name = "Sabreur_Degainage", loop = false, priority = "Action", keys = {
		{ t = 0, e = "Cubic", d = "InOut", p = { RightUpperArm = {0, 0, 0, 5, 0, 6}, RightLowerArm = {0, 0, 0, 10, 0, 0}, LeftUpperArm = {0, 0, 0, 5, 0, -6}, LeftLowerArm = {0, 0, 0, 10, 0, 0} } },
		{ t = 0.2, e = "Cubic", d = "Out", p = { LowerTorso = {0, -0.15, 0, 0, 0, 0}, UpperTorso = {0, 0, 0, -5, 25, 0}, Head = {0, 0, 0, -15, -10, 0}, RightUpperArm = {0, 0, 0, 35, 0, -30}, RightLowerArm = {0, 0, 0, 75, 0, 0}, LeftUpperArm = {0, 0, 0, 10, 0, -15}, LeftLowerArm = {0, 0, 0, 40, 0, 0} } },
		{ t = 0.35, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.25, 0, 0, -15, 0}, UpperTorso = {0, 0, 0, -5, -15, 0}, Head = {0, 0, 0, -5, 10, 0}, RightUpperArm = {0, 0, 0, 100, 0, 55}, RightLowerArm = {0, 0, 0, 15, 0, 0}, RightHand = {0, 0, 0, -40, 0, 0}, LeftUpperArm = {0, 0, 0, 15, 0, -15}, LeftLowerArm = {0, 0, 0, 50, 0, 0} } },
		{ t = 0.55, e = "Cubic", d = "Out", p = { LowerTorso = {0, -0.25, 0, 0, -15, 0}, UpperTorso = {0, 0, 0, -8, 10, 0}, Head = {0, 0, 0, -15, 0, 0}, RightUpperArm = {0, 0, 0, 100, 0, 55}, RightLowerArm = {0, 0, 0, 15, 0, 0}, RightHand = {0, 0, 0, -40, 0, 0}, LeftUpperArm = {0, 0, 0, 20, 0, -5}, LeftLowerArm = {0, 0, 0, 60, 0, 0} } },
		{ t = 0.7, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.3, 0, 0, 15, 0}, UpperTorso = {0, 0, 0, -5, 10, 0}, Head = {0, 0, 0, -5, -5, 0}, RightUpperArm = {0, 0, 0, 100, 0, 55}, RightLowerArm = {0, 0, 0, 15, 0, 0}, RightHand = {0, 0, 0, -40, 0, 0}, LeftUpperArm = {0, 0, 0, 100, 0, -55}, LeftLowerArm = {0, 0, 0, 15, 0, 0}, LeftHand = {0, 0, 0, -40, 0, 0} } },
		{ t = 0.92, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.3, 0, 0, 15, 0}, UpperTorso = {0, 0, 0, -5, 10, 0}, Head = {0, 0, 0, -10, 0, 0}, RightUpperArm = {0, 0, 0, 110, 0, -25}, RightLowerArm = {0, 0, 0, 120, 0, 0}, RightHand = {0, 0, 0, -20, 0, 0}, LeftUpperArm = {0, 0, 0, 100, 0, -55}, LeftLowerArm = {0, 0, 0, 15, 0, 0}, LeftHand = {0, 0, 0, -40, 0, 0} } },
		{ t = 1.12, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.4, 0, 0, -20, 0}, UpperTorso = {0, 0, 0, -10, 15, 0}, Head = {0, 0, 0, -6, 8, 0}, RightUpperArm = {0, 0, 0, 60, 15, 25}, RightLowerArm = {0, 0, 0, 50, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 35, -15, -40}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
		{ t = 1.4, e = "Cubic", d = "Out", p = { LowerTorso = {0, -0.47, 0, 0, -20, 0}, UpperTorso = {0, 0, 0, -13, 15, 0}, Head = {0, 0, 0, -8, 8, 0}, RightUpperArm = {0, 0, 0, 63, 15, 25}, RightLowerArm = {0, 0, 0, 50, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 38, -15, -40}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
	}, markers = { { 0, "Montrer", "SabresHanche" }, { 0, "Cacher", "SabreDroit" }, { 0, "Cacher", "SabreGauche" }, { 0, "Cacher", "SabreBouche" }, { 0.22, "Montrer", "SabreDroit" }, { 0.55, "Montrer", "SabreGauche" }, { 0.95, "Montrer", "SabreBouche" }, { 0.95, "Cacher", "SabresHanche" } } },
	{ name = "Sabreur_Charge_Aura", loop = false, priority = "Action", keys = {
		{ t = 0, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.4, 0, 0, -20, 0}, UpperTorso = {0, 0, 0, -10, 15, 0}, Head = {0, 0, 0, -6, 8, 0}, RightUpperArm = {0, 0, 0, 60, 15, 25}, RightLowerArm = {0, 0, 0, 50, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 35, -15, -40}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
		{ t = 0.28, e = "Cubic", d = "In", p = { LowerTorso = {0, -0.9, 0, 0, 0, 0}, UpperTorso = {0, 0, 0, -35, 0, 0}, Head = {0, 0, 0, -25, 0, 0}, RightUpperArm = {0, 0, 0, 25, 0, -45}, RightLowerArm = {0, 0, 0, 70, 0, 0}, RightHand = {0, 0, 0, -30, 0, 0}, LeftUpperArm = {0, 0, 0, 25, 0, 45}, LeftLowerArm = {0, 0, 0, 70, 0, 0}, LeftHand = {0, 0, 0, -30, 0, 0}, RightUpperLeg = {0, 0, 0, 60, 0, 18}, RightLowerLeg = {0, 0, 0, -90, 0, 0}, RightFoot = {0, 0, 0, 30, 0, 0}, LeftUpperLeg = {0, 0, 0, 60, 0, -18}, LeftLowerLeg = {0, 0, 0, -90, 0, 0} } },
		{ t = 0.4, e = "Cubic", d = "Out", p = { LowerTorso = {0, 0.4, 0, 0, 0, 0}, UpperTorso = {0, 0, 0, 12, 0, 0}, Head = {0, 0, 0, -12, 0, 0}, RightUpperArm = {0, 0, 0, 0, 0, 100}, RightLowerArm = {0, 0, 0, 5, 0, 0}, RightHand = {0, 0, 0, -80, 0, 0}, LeftUpperArm = {0, 0, 0, 0, 0, -100}, LeftLowerArm = {0, 0, 0, 5, 0, 0}, LeftHand = {0, 0, 0, -80, 0, 0}, RightUpperLeg = {0, 0, 0, 20, 0, 8}, RightLowerLeg = {0, 0, 0, -35, 0, 0}, RightFoot = {0, 0, 0, 20, 0, 0}, LeftUpperLeg = {0, 0, 0, 5, 0, -8}, LeftLowerLeg = {0, 0, 0, -15, 0, 0} } },
		{ t = 0.75, e = "Cubic", d = "InOut", p = { LowerTorso = {0, 1.3, 0, 0, 0, 0}, UpperTorso = {0, 0, 0, 8, 0, 0}, Head = {0, 0, 0, -14, 0, 0}, RightUpperArm = {0, 0, 0, 6, 0, 88}, RightLowerArm = {0, 0, 0, 10, 0, 0}, RightHand = {0, 0, 0, -75, 0, 0}, LeftUpperArm = {0, 0, 0, 6, 0, -88}, LeftLowerArm = {0, 0, 0, 10, 0, 0}, LeftHand = {0, 0, 0, -75, 0, 0}, RightUpperLeg = {0, 0, 0, 28, 0, 8}, RightLowerLeg = {0, 0, 0, -45, 0, 0}, RightFoot = {0, 0, 0, 25, 0, 0}, LeftUpperLeg = {0, 0, 0, 10, 0, -8}, LeftLowerLeg = {0, 0, 0, -20, 0, 0} } },
		{ t = 1.3, e = "Cubic", d = "InOut", p = { LowerTorso = {0, 1.5, 0, 0, 0, 0}, UpperTorso = {0, 0, 0, 10, 0, 0}, Head = {0, 0, 0, -10, 0, 0}, RightUpperArm = {0, 0, 0, 4, 0, 92}, RightLowerArm = {0, 0, 0, 10, 0, 0}, RightHand = {0, 0, 0, -75, 0, 0}, LeftUpperArm = {0, 0, 0, 4, 0, -92}, LeftLowerArm = {0, 0, 0, 10, 0, 0}, LeftHand = {0, 0, 0, -75, 0, 0}, RightUpperLeg = {0, 0, 0, 28, 0, 8}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 25, 0, 0}, LeftUpperLeg = {0, 0, 0, 10, 0, -8}, LeftLowerLeg = {0, 0, 0, -25, 0, 0} } },
		{ t = 1.85, e = "Cubic", d = "InOut", p = { LowerTorso = {0, 1.3, 0, 0, 0, 0}, UpperTorso = {0, 0, 0, 8, 0, 0}, Head = {0, 0, 0, -14, 0, 0}, RightUpperArm = {0, 0, 0, 6, 0, 88}, RightLowerArm = {0, 0, 0, 10, 0, 0}, RightHand = {0, 0, 0, -75, 0, 0}, LeftUpperArm = {0, 0, 0, 6, 0, -88}, LeftLowerArm = {0, 0, 0, 10, 0, 0}, LeftHand = {0, 0, 0, -75, 0, 0}, RightUpperLeg = {0, 0, 0, 28, 0, 8}, RightLowerLeg = {0, 0, 0, -45, 0, 0}, RightFoot = {0, 0, 0, 25, 0, 0}, LeftUpperLeg = {0, 0, 0, 10, 0, -8}, LeftLowerLeg = {0, 0, 0, -20, 0, 0} } },
		{ t = 2.4, e = "Cubic", d = "In", p = { LowerTorso = {0, 1.5, 0, 0, 0, 0}, UpperTorso = {0, 0, 0, 10, 0, 0}, Head = {0, 0, 0, -10, 0, 0}, RightUpperArm = {0, 0, 0, 4, 0, 92}, RightLowerArm = {0, 0, 0, 10, 0, 0}, RightHand = {0, 0, 0, -75, 0, 0}, LeftUpperArm = {0, 0, 0, 4, 0, -92}, LeftLowerArm = {0, 0, 0, 10, 0, 0}, LeftHand = {0, 0, 0, -75, 0, 0}, RightUpperLeg = {0, 0, 0, 28, 0, 8}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 25, 0, 0}, LeftUpperLeg = {0, 0, 0, 10, 0, -8}, LeftLowerLeg = {0, 0, 0, -25, 0, 0} } },
		{ t = 2.75, e = "Cubic", d = "Out", p = { LowerTorso = {0, -0.85, 0, 0, -20, 0}, UpperTorso = {0, 0, 0, -18, 15, 0}, Head = {0, 0, 0, -12, 8, 0}, RightUpperArm = {0, 0, 0, 60, 15, 25}, RightLowerArm = {0, 0, 0, 50, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 35, -15, -40}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 45, 0, 12}, RightLowerLeg = {0, 0, 0, -75, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -55, 0, 0} } },
		{ t = 3, e = "Cubic", d = "Out", p = { LowerTorso = {0, -0.4, 0, 0, -20, 0}, UpperTorso = {0, 0, 0, -10, 15, 0}, Head = {0, 0, 0, -6, 8, 0}, RightUpperArm = {0, 0, 0, 60, 15, 25}, RightLowerArm = {0, 0, 0, 50, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 35, -15, -40}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
	}, markers = { { 0.05, "Aura", "Debut" }, { 0.4, "Explosion", "Aura" }, { 2.8, "Fin", "Aura" } } },
	{ name = "Sabreur_Combat_Esquives", loop = false, priority = "Action", keys = {
		{ t = 0, e = "Cubic", d = "Out", p = { LowerTorso = {0, -0.4, 0, 0, -20, 0}, UpperTorso = {0, 0, 0, -10, 15, 0}, Head = {0, 0, 0, -6, 8, 0}, RightUpperArm = {0, 0, 0, 60, 15, 25}, RightLowerArm = {0, 0, 0, 50, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 35, -15, -40}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
		{ t = 0.16, e = "Cubic", d = "Out", p = { LowerTorso = {-2, -0.75, 0, 0, -20, 15}, UpperTorso = {0, 0, 0, -15, 25, 0}, Head = {0, 0, 0, -10, 8, 0}, RightUpperArm = {0, 0, 0, 45, 0, 30}, RightLowerArm = {0, 0, 0, 70, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 20, 0, -50}, LeftLowerArm = {0, 0, 0, 55, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 10, 0, 35}, RightLowerLeg = {0, 0, 0, -10, 0, 0}, LeftUpperLeg = {0, 0, 0, 45, 0, -5}, LeftLowerLeg = {0, 0, 0, -85, 0, 0} } },
		{ t = 0.3, e = "Cubic", d = "Out", p = { LowerTorso = {-2, -0.5, 0, 0, 15, 0}, UpperTorso = {0, 0, 0, -8, -45, 0}, Head = {0, 0, 0, -6, -5, 0}, RightUpperArm = {0, 0, 0, 80, 0, 85}, RightLowerArm = {0, 0, 0, 20, 0, 0}, RightHand = {0, 0, 0, -80, 0, 0}, LeftUpperArm = {0, 0, 0, 85, 0, 40}, LeftLowerArm = {0, 0, 0, 35, 0, 0}, LeftHand = {0, 0, 0, -80, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
		{ t = 0.4, e = "Cubic", d = "InOut", p = { LowerTorso = {-2, -0.6, -0.3, 0, -30, 0}, UpperTorso = {0, 0, 0, -12, 50, 0}, Head = {0, 0, 0, -6, -12, 0}, RightUpperArm = {0, 0, 0, 85, 0, -30}, RightLowerArm = {0, 0, 0, 10, 0, 0}, RightHand = {0, 0, 0, -80, 0, 0}, LeftUpperArm = {0, 0, 0, 80, 0, -85}, LeftLowerArm = {0, 0, 0, 10, 0, 0}, LeftHand = {0, 0, 0, -80, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
		{ t = 0.56, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.1, 0, 0, -20, -6}, UpperTorso = {0, 0, 0, -8, 10, 0}, Head = {0, 0, 0, -6, 8, 0}, RightUpperArm = {0, 0, 0, 60, 15, 25}, RightLowerArm = {0, 0, 0, 50, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 35, -15, -40}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 50, 0, 10}, RightLowerLeg = {0, 0, 0, -90, 0, 0}, RightFoot = {0, 0, 0, 10, 0, 0}, LeftUpperLeg = {0, 0, 0, 40, 0, -10}, LeftLowerLeg = {0, 0, 0, -90, 0, 0} } },
		{ t = 0.72, e = "Cubic", d = "Out", p = { LowerTorso = {2, -0.75, 0, 0, -20, -15}, UpperTorso = {0, 0, 0, -15, 5, 0}, Head = {0, 0, 0, -10, 8, 0}, RightUpperArm = {0, 0, 0, 50, 0, 45}, RightLowerArm = {0, 0, 0, 70, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 30, 0, -30}, LeftLowerArm = {0, 0, 0, 55, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 45, 0, 5}, RightLowerLeg = {0, 0, 0, -85, 0, 0}, RightFoot = {0, 0, 0, 30, 0, 0}, LeftUpperLeg = {0, 0, 0, 10, 0, -35}, LeftLowerLeg = {0, 0, 0, -10, 0, 0} } },
		{ t = 0.86, e = "Cubic", d = "Out", p = { LowerTorso = {2, -0.5, 0, 0, -40, 0}, UpperTorso = {0, 0, 0, -8, 45, 0}, Head = {0, 0, 0, -6, 10, 0}, RightUpperArm = {0, 0, 0, 85, 0, -40}, RightLowerArm = {0, 0, 0, 35, 0, 0}, RightHand = {0, 0, 0, -80, 0, 0}, LeftUpperArm = {0, 0, 0, 80, 0, -85}, LeftLowerArm = {0, 0, 0, 20, 0, 0}, LeftHand = {0, 0, 0, -80, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
		{ t = 0.96, e = "Cubic", d = "InOut", p = { LowerTorso = {2, -0.6, -0.3, 0, 10, 0}, UpperTorso = {0, 0, 0, -12, -45, 0}, Head = {0, 0, 0, -6, 10, 0}, RightUpperArm = {0, 0, 0, 80, 0, 85}, RightLowerArm = {0, 0, 0, 10, 0, 0}, RightHand = {0, 0, 0, -80, 0, 0}, LeftUpperArm = {0, 0, 0, 85, 0, 30}, LeftLowerArm = {0, 0, 0, 10, 0, 0}, LeftHand = {0, 0, 0, -80, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
		{ t = 1.1, e = "Cubic", d = "Out", p = { LowerTorso = {1, -0.9, 0.2, 0, 0, 0}, UpperTorso = {0, 0, 0, -25, 0, 0}, Head = {0, 0, 0, 10, 0, 0}, RightUpperArm = {0, 0, 0, -30, 0, 35}, RightLowerArm = {0, 0, 0, 15, 0, 0}, RightHand = {0, 0, 0, -30, 0, 0}, LeftUpperArm = {0, 0, 0, -30, 0, -35}, LeftLowerArm = {0, 0, 0, 15, 0, 0}, LeftHand = {0, 0, 0, -30, 0, 0}, RightUpperLeg = {0, 0, 0, 60, 0, 14}, RightLowerLeg = {0, 0, 0, -90, 0, 0}, RightFoot = {0, 0, 0, 25, 0, 0}, LeftUpperLeg = {0, 0, 0, 50, 0, -14}, LeftLowerLeg = {0, 0, 0, -85, 0, 0} } },
		{ t = 1.2, e = "Cubic", d = "InOut", p = { LowerTorso = {1, -0.2, -0.5, 0, 0, 0}, UpperTorso = {0, 0, 0, 15, 0, 0}, Head = {0, 0, 0, 12, 0, 0}, RightUpperArm = {0, 0, 0, 165, 0, 20}, RightLowerArm = {0, 0, 0, 10, 0, 0}, RightHand = {0, 0, 0, -20, 0, 0}, LeftUpperArm = {0, 0, 0, 165, 0, -20}, LeftLowerArm = {0, 0, 0, 10, 0, 0}, LeftHand = {0, 0, 0, -20, 0, 0}, RightUpperLeg = {0, 0, 0, 35, 0, 10}, RightLowerLeg = {0, 0, 0, -30, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -25, 0, -10}, LeftLowerLeg = {0, 0, 0, -15, 0, 0} } },
		{ t = 1.38, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.8, 2, 12, -20, 0}, UpperTorso = {0, 0, 0, -5, 15, 0}, Head = {0, 0, 0, -12, 8, 0}, RightUpperArm = {0, 0, 0, 70, 0, 20}, RightLowerArm = {0, 0, 0, 60, 0, 0}, RightHand = {0, 0, 0, -60, 0, 0}, LeftUpperArm = {0, 0, 0, 60, 0, -25}, LeftLowerArm = {0, 0, 0, 60, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, -25, 0, 10}, RightLowerLeg = {0, 0, 0, -20, 0, 0}, RightFoot = {0, 0, 0, 25, 0, 0}, LeftUpperLeg = {0, 0, 0, 60, 0, -10}, LeftLowerLeg = {0, 0, 0, -95, 0, 0} } },
		{ t = 1.48, e = "Cubic", d = "Out", p = { LowerTorso = {0, -0.85, 2, 12, -20, 0}, UpperTorso = {0, 0, 0, -5, 15, 0}, Head = {0, 0, 0, -12, 8, 0}, RightUpperArm = {0, 0, 0, 70, 0, 20}, RightLowerArm = {0, 0, 0, 60, 0, 0}, RightHand = {0, 0, 0, -60, 0, 0}, LeftUpperArm = {0, 0, 0, 60, 0, -25}, LeftLowerArm = {0, 0, 0, 60, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, -25, 0, 10}, RightLowerLeg = {0, 0, 0, -20, 0, 0}, RightFoot = {0, 0, 0, 25, 0, 0}, LeftUpperLeg = {0, 0, 0, 60, 0, -10}, LeftLowerLeg = {0, 0, 0, -95, 0, 0} } },
		{ t = 1.55, e = "Cubic", d = "Out", p = { LowerTorso = {0, -1.2, 2, 0, 0, 0}, UpperTorso = {0, 0, 0, -30, 0, 0}, Head = {0, 0, 0, 15, 0, 0}, RightUpperArm = {0, 0, 0, -45, 0, 20}, RightLowerArm = {0, 0, 0, 20, 0, 0}, RightHand = {0, 0, 0, -20, 0, 0}, LeftUpperArm = {0, 0, 0, -45, 0, -20}, LeftLowerArm = {0, 0, 0, 20, 0, 0}, LeftHand = {0, 0, 0, -20, 0, 0}, RightUpperLeg = {0, 0, 0, 80, 0, 12}, RightLowerLeg = {0, 0, 0, -110, 0, 0}, RightFoot = {0, 0, 0, 30, 0, 0}, LeftUpperLeg = {0, 0, 0, 80, 0, -12}, LeftLowerLeg = {0, 0, 0, -110, 0, 0} } },
		{ t = 1.8, e = "Cubic", d = "Out", p = { LowerTorso = {0, 5, 0.8, 0, 0, 0}, UpperTorso = {0, 0, 0, 18, 0, 0}, Head = {0, 0, 0, 10, 0, 0}, RightUpperArm = {0, 0, 0, 175, 0, 10}, RightLowerArm = {0, 0, 0, 45, 0, 0}, LeftUpperArm = {0, 0, 0, 175, 0, -10}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, RightUpperLeg = {0, 0, 0, 60, 0, 10}, RightLowerLeg = {0, 0, 0, -100, 0, 0}, LeftUpperLeg = {0, 0, 0, 30, 0, -10}, LeftLowerLeg = {0, 0, 0, -80, 0, 0} } },
		{ t = 1.95, e = "Cubic", d = "In", p = { LowerTorso = {0, 5.6, 0, 15, 0, 0}, UpperTorso = {0, 0, 0, 24, 0, 0}, Head = {0, 0, 0, 10, 0, 0}, RightUpperArm = {0, 0, 0, 178, 0, 10}, RightLowerArm = {0, 0, 0, 45, 0, 0}, LeftUpperArm = {0, 0, 0, 178, 0, -10}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, RightUpperLeg = {0, 0, 0, 60, 0, 10}, RightLowerLeg = {0, 0, 0, -100, 0, 0}, LeftUpperLeg = {0, 0, 0, 30, 0, -10}, LeftLowerLeg = {0, 0, 0, -80, 0, 0} } },
		{ t = 2.12, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -1.1, -1, 0, 0, 0}, UpperTorso = {0, 0, 0, -45, 0, 0}, Head = {0, 0, 0, -15, 0, 0}, RightUpperArm = {0, 0, 0, 25, 0, 10}, RightHand = {0, 0, 0, -60, 0, 0}, LeftUpperArm = {0, 0, 0, 25, 0, -10}, LeftHand = {0, 0, 0, -60, 0, 0}, RightUpperLeg = {0, 0, 0, 85, 0, 10}, RightLowerLeg = {0, 0, 0, -100, 0, 0}, RightFoot = {0, 0, 0, 15, 0, 0}, LeftUpperLeg = {0, 0, 0, -20, 0, -10}, LeftLowerLeg = {0, 0, 0, -100, 0, 0} } },
		{ t = 2.35, e = "Cubic", d = "In", p = { LowerTorso = {0, -0.85, -0.8, 0, 0, 0}, UpperTorso = {0, 0, 0, 10, 0, 0}, Head = {0, 0, 0, 8, 0, 0}, RightUpperArm = {0, 0, 0, 142, 0, -52}, RightLowerArm = {0, 0, 0, 20, 0, 0}, RightHand = {0, 0, 0, -20, 0, 0}, LeftUpperArm = {0, 0, 0, 142, 0, 52}, LeftLowerArm = {0, 0, 0, 20, 0, 0}, LeftHand = {0, 0, 0, -20, 0, 0}, RightUpperLeg = {0, 0, 0, 45, 0, 15}, RightLowerLeg = {0, 0, 0, -70, 0, 0}, RightFoot = {0, 0, 0, 25, 0, 0}, LeftUpperLeg = {0, 0, 0, 45, 0, -15}, LeftLowerLeg = {0, 0, 0, -70, 0, 0} } },
		{ t = 2.48, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.9, -1.6, 0, 0, 0}, UpperTorso = {0, 0, 0, -25, 0, 0}, RightUpperArm = {0, 0, 0, 35, 0, 85}, RightHand = {0, 0, 0, -60, 0, 0}, LeftUpperArm = {0, 0, 0, 35, 0, -85}, LeftHand = {0, 0, 0, -60, 0, 0}, RightUpperLeg = {0, 0, 0, 70, 0, 12}, RightLowerLeg = {0, 0, 0, -80, 0, 0}, RightFoot = {0, 0, 0, 10, 0, 0}, LeftUpperLeg = {0, 0, 0, -40, 0, -12}, LeftLowerLeg = {0, 0, 0, -25, 0, 0} } },
		{ t = 2.8, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.85, -1.5, 0, 0, 0}, UpperTorso = {0, 0, 0, -22, 0, 0}, RightUpperArm = {0, 0, 0, 35, 0, 85}, RightHand = {0, 0, 0, -60, 0, 0}, LeftUpperArm = {0, 0, 0, 35, 0, -85}, LeftHand = {0, 0, 0, -60, 0, 0}, RightUpperLeg = {0, 0, 0, 70, 0, 12}, RightLowerLeg = {0, 0, 0, -80, 0, 0}, RightFoot = {0, 0, 0, 10, 0, 0}, LeftUpperLeg = {0, 0, 0, -40, 0, -12}, LeftLowerLeg = {0, 0, 0, -25, 0, 0} } },
		{ t = 3.15, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.4, 0, 0, -20, 0}, UpperTorso = {0, 0, 0, -10, 15, 0}, Head = {0, 0, 0, -6, 8, 0}, RightUpperArm = {0, 0, 0, 60, 15, 25}, RightLowerArm = {0, 0, 0, 50, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 35, -15, -40}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
		{ t = 3.4, e = "Cubic", d = "Out", p = { LowerTorso = {0, -0.47, 0, 0, -20, 0}, UpperTorso = {0, 0, 0, -13, 15, 0}, Head = {0, 0, 0, -8, 8, 0}, RightUpperArm = {0, 0, 0, 63, 15, 25}, RightLowerArm = {0, 0, 0, 50, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 38, -15, -40}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
	}, markers = { { 0.16, "Esquive", "Gauche" }, { 0.4, "Impact", "Contre1" }, { 0.72, "Esquive", "Droite" }, { 0.96, "Impact", "Contre2" }, { 1.2, "Impact", "Contre3" }, { 1.38, "Esquive", "Arriere" }, { 2.12, "Impact", "Sol" }, { 2.48, "Impact", "CoupeX" } } },
	{ name = "Sabreur_Rengainage", loop = false, priority = "Action", keys = {
		{ t = 0, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.4, 0, 0, -20, 0}, UpperTorso = {0, 0, 0, -10, 15, 0}, Head = {0, 0, 0, -6, 8, 0}, RightUpperArm = {0, 0, 0, 60, 15, 25}, RightLowerArm = {0, 0, 0, 50, 0, 0}, RightHand = {0, 0, 0, -55, 0, 0}, LeftUpperArm = {0, 0, 0, 35, -15, -40}, LeftLowerArm = {0, 0, 0, 45, 0, 0}, LeftHand = {0, 0, 0, -45, 0, 0}, RightUpperLeg = {0, 0, 0, 30, 0, 12}, RightLowerLeg = {0, 0, 0, -50, 0, 0}, RightFoot = {0, 0, 0, 18, 0, 0}, LeftUpperLeg = {0, 0, 0, -15, 0, -14}, LeftLowerLeg = {0, 0, 0, -30, 0, 0} } },
		{ t = 0.25, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.3, 0, 0, 15, 0}, UpperTorso = {0, 0, 0, -5, 10, 0}, Head = {0, 0, 0, -10, 0, 0}, RightUpperArm = {0, 0, 0, 110, 0, -25}, RightLowerArm = {0, 0, 0, 120, 0, 0}, RightHand = {0, 0, 0, -20, 0, 0}, LeftUpperArm = {0, 0, 0, 100, 0, -55}, LeftLowerArm = {0, 0, 0, 15, 0, 0}, LeftHand = {0, 0, 0, -40, 0, 0} } },
		{ t = 0.45, e = "Cubic", d = "Out", p = { LowerTorso = {0, -0.3, 0, 0, 15, 0}, UpperTorso = {0, 0, 0, -5, 10, 0}, Head = {0, 0, 0, -5, -5, 0}, RightUpperArm = {0, 0, 0, 100, 0, 55}, RightLowerArm = {0, 0, 0, 15, 0, 0}, RightHand = {0, 0, 0, -40, 0, 0}, LeftUpperArm = {0, 0, 0, 100, 0, -55}, LeftLowerArm = {0, 0, 0, 15, 0, 0}, LeftHand = {0, 0, 0, -40, 0, 0} } },
		{ t = 0.65, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.25, 0, 0, -15, 0}, UpperTorso = {0, 0, 0, -8, 10, 0}, Head = {0, 0, 0, -15, 0, 0}, RightUpperArm = {0, 0, 0, 100, 0, 55}, RightLowerArm = {0, 0, 0, 15, 0, 0}, RightHand = {0, 0, 0, -40, 0, 0}, LeftUpperArm = {0, 0, 0, 20, 0, -5}, LeftLowerArm = {0, 0, 0, 60, 0, 0} } },
		{ t = 0.85, e = "Cubic", d = "Out", p = { LowerTorso = {0, -0.25, 0, 0, -15, 0}, UpperTorso = {0, 0, 0, -5, -15, 0}, Head = {0, 0, 0, -5, 10, 0}, RightUpperArm = {0, 0, 0, 100, 0, 55}, RightLowerArm = {0, 0, 0, 15, 0, 0}, RightHand = {0, 0, 0, -40, 0, 0}, LeftUpperArm = {0, 0, 0, 15, 0, -15}, LeftLowerArm = {0, 0, 0, 50, 0, 0} } },
		{ t = 1.05, e = "Cubic", d = "InOut", p = { LowerTorso = {0, -0.15, 0, 0, 0, 0}, UpperTorso = {0, 0, 0, -5, 25, 0}, Head = {0, 0, 0, -15, -10, 0}, RightUpperArm = {0, 0, 0, 35, 0, -30}, RightLowerArm = {0, 0, 0, 75, 0, 0}, LeftUpperArm = {0, 0, 0, 10, 0, -15}, LeftLowerArm = {0, 0, 0, 40, 0, 0} } },
		{ t = 1.4, e = "Cubic", d = "Out", p = { RightUpperArm = {0, 0, 0, 5, 0, 6}, RightLowerArm = {0, 0, 0, 10, 0, 0}, LeftUpperArm = {0, 0, 0, 5, 0, -6}, LeftLowerArm = {0, 0, 0, 10, 0, 0} } },
	}, markers = { { 0.25, "Cacher", "SabreBouche" }, { 0.65, "Cacher", "SabreGauche" }, { 0.65, "Montrer", "SabresHanche" }, { 1.05, "Cacher", "SabreDroit" } } },
}

-- Séquence complète = les 4 clips bout à bout (la 1re clé d'un clip remplace la dernière du précédent)
local DECALAGES = { 0, 1.4, 4.4, 7.8 }
local sequence = { name = "Sabreur_Sequence_Complete", loop = false, priority = "Action", keys = {}, markers = {} }
for i, clip in ipairs(CLIPS) do
	local dec = DECALAGES[i]
	for _, k in ipairs(clip.keys) do
		local t = math.round((k.t + dec) * 10000) / 10000
		local derniere = sequence.keys[#sequence.keys]
		if derniere and math.abs(derniere.t - t) < 1e-4 then
			table.remove(sequence.keys)
		end
		table.insert(sequence.keys, { t = t, e = k.e, d = k.d, p = k.p })
	end
	for _, m in ipairs(clip.markers) do
		table.insert(sequence.markers, { math.round((m[1] + dec) * 10000) / 10000, m[2], m[3] })
	end
end
local ANIMS = { sequence, CLIPS[1], CLIPS[2], CLIPS[3], CLIPS[4] }

-- Accessoires du handoff → accessoires de zoro
local RENOMMER = {
	SabresHanche = "Acc_Sabres_Hanche",
	SabreDroit = "Acc_Sabre_Droit",
	SabreGauche = "Acc_Sabre_Gauche",
	SabreBouche = "Acc_Sabre_Bouche",
}
-- Les effets ne passent plus par des marqueurs « VFX » : src/client/Vitrine.luau déclenche zoro.VFX.<Marqueur>_<Valeur>
-- (Aura_Debut, Explosion_Aura, Impact_Sol…, créés par vfx_sabreur.luau) directement sur les marqueurs d'origine.
-- L'Éditeur d'animation ne publie qu'un marqueur de chaque nom par image clé : deux « VFX » au même instant en perdaient un.
local EFFETS = {}
-- Traînées des lames pendant tout le combat
local DEBUT_COMBAT = { Sabreur_Combat_Esquives = 0.1, Sabreur_Sequence_Complete = 4.5 }

for _, a in ipairs(ANIMS) do
	local liste = {}
	for _, m in ipairs(a.markers) do
		local t, nom, valeur = m[1], m[2], m[3]
		if nom == "Montrer" or nom == "Cacher" then
			table.insert(liste, { t, nom, RENOMMER[valeur] or valeur })
		else
			table.insert(liste, m)
			for _, effet in ipairs(EFFETS[nom .. "/" .. valeur] or {}) do
				table.insert(liste, { t, "VFX", effet })
			end
		end
	end
	if DEBUT_COMBAT[a.name] then
		table.insert(liste, { DEBUT_COMBAT[a.name], "VFX", "Sabreur_Trail" })
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
return table.concat(bilan, "\n")
