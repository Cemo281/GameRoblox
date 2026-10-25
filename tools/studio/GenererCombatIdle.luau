--!strict
-- Générateur de l'animation « Combat Idle » en boucle pour un rig R6.
-- Utilisation : sélectionner le Model du personnage dans l'Explorer, coller tout ce script dans la
-- Command Bar de Studio (View > Command Bar) et appuyer sur Entrée.
-- Résultat : ServerStorage > RBX_ANIMSAVES > <nom du rig> > Fighter_CombatIdle (KeyframeSequence),
-- à ouvrir ensuite avec l'Animation Editor.
-- Ce fichier n'est pas synchronisé par Rojo (dossier tools/) : c'est un outil Studio.

-- ============================== RÉGLAGES ==============================
local BIG_ARM = "Right Arm" -- bras au gros poing : "Right Arm" ou "Left Arm"
local DURATION = 3.2 -- durée de la boucle (s)
local STEP = 0.2 -- un keyframe toutes les STEP secondes
local BOUNCE_PERIOD = 0.8 -- durée d'un rebond (s) : 4 rebonds par boucle
local LEG_SPREAD_MIN = 20 -- écart de chaque jambe en haut du rebond (°)
local LEG_SPREAD_MAX = 30 -- écart de chaque jambe au creux du rebond (°)
local SWAY_YAW = 6 -- balancement du torse en lacet (°)
local SWAY_ROLL = 2 -- balancement du torse en roulis (°)
local WINDUP = 25 -- recul du gros bras pendant l'armé (°)
local WINDUP_START = 1.0 -- début de l'armé (s)
local WINDUP_PEAK = 1.4 -- pic de l'armé (s), suivi d'un retour élastique
-- ======================================================================

-- Réglages secondaires
local FOLLOW_DELAY = 0.1 -- retard de la tête, des bras et de la cape sur le rebond (s)
local HEAD_TILT = 6 -- inclinaison de la tête vers l'avant (°)
local HEAD_TILT_BOUNCE = 2 -- inclinaison supplémentaire au creux du rebond (°)
local HEAD_COUNTER_YAW = 0.6 -- contre-rotation de la tête (× lacet du torse)
local GUARD_FORWARD = 75 -- bras de garde tendu devant (°)
local GUARD_TUCK = 15 -- bras de garde rentré vers l'axe du corps (°)
local ARM_DIP = 5 -- les bras descendent de ARM_DIP° au creux du rebond
local BIG_FORWARD = 110 -- gros bras armé en hauteur (°)
local BIG_OUTWARD = 25 -- gros bras écarté vers l'extérieur (°)
local CAPE_SWING = 4 -- cape : amplitude liée au rebond (°)
local CAPE_SWAY = 3 -- cape : amplitude liée au balancement (°)
local LEG_LENGTH = 2 -- longueur d'une jambe R6 (studs), de la hanche au pied

local NOM_SEQUENCE = "Fighter_CombatIdle"
local EPSILON = 1e-6
local TAU = 2 * math.pi

local ChangeHistoryService = game:GetService("ChangeHistoryService")
local Selection = game:GetService("Selection")
local ServerStorage = game:GetService("ServerStorage")

local function estMultiple(valeur: number, pas: number): boolean
	return math.abs(valeur / pas - math.round(valeur / pas)) < EPSILON
end

-- Vérification des réglages
assert(BIG_ARM == "Right Arm" or BIG_ARM == "Left Arm", 'BIG_ARM doit valoir "Right Arm" ou "Left Arm".')
assert(estMultiple(DURATION, STEP), "DURATION doit être un multiple de STEP.")
assert(
	estMultiple(DURATION, BOUNCE_PERIOD),
	"DURATION doit être un multiple de BOUNCE_PERIOD (sinon la boucle saute)."
)
assert(estMultiple(WINDUP_PEAK, STEP), "WINDUP_PEAK doit tomber sur un keyframe (multiple de STEP).")
assert(
	WINDUP_START >= 0 and WINDUP_START < WINDUP_PEAK and WINDUP_PEAK + STEP < DURATION,
	"Il faut 0 <= WINDUP_START < WINDUP_PEAK < DURATION - STEP."
)

-- Vérification du modèle sélectionné
local selection = Selection:Get()
local rig = selection[1]
assert(
	#selection == 1 and rig ~= nil and rig:IsA("Model"),
	"Sélectionne un seul élément dans l'Explorer : le Model du personnage R6."
)
local torse = rig:FindFirstChild("Torso")
assert(torse ~= nil and torse:IsA("BasePart"), `« {rig.Name} » n'a pas de partie Torso : ce n'est pas un rig R6.`)
local racine = rig:FindFirstChild("HumanoidRootPart")
assert(racine ~= nil and racine:IsA("BasePart"), `« {rig.Name} » n'a pas de HumanoidRootPart.`)
local humanoid = rig:FindFirstChildOfClass("Humanoid")
assert(
	humanoid == nil or humanoid.RigType == Enum.HumanoidRigType.R6,
	`Le Humanoid de « {rig.Name} » est en R15 : ce générateur est fait pour un rig R6.`
)

-- Motor6D de `parent` dont Part1 s'appelle `nomPart1` (le nom de la Pose doit être celui de Part1)
local function trouverMoteur(parent: Instance, nomPart1: string): Motor6D?
	for _, enfant in parent:GetChildren() do
		if enfant:IsA("Motor6D") and enfant.Part1 ~= nil and enfant.Part1.Name == nomPart1 then
			return enfant
		end
	end
	return nil
end

assert(trouverMoteur(racine, "Torso") ~= nil, "Il manque le Motor6D RootJoint (HumanoidRootPart → Torso).")
for _, membre in { "Right Arm", "Left Arm", "Right Leg", "Left Leg" } do
	assert(trouverMoteur(torse, membre) ~= nil, `Il manque le Motor6D du Torso vers « {membre} ».`)
end
local aTete = trouverMoteur(torse, "Head") ~= nil
local aCape = trouverMoteur(torse, "Cape") ~= nil
if not aTete then
	warn("[CombatIdle] Pas de Motor6D Neck (Torso → Head) : la tête ne sera pas animée.")
end

-- Côtés : la jambe avant est du côté opposé au gros bras
local BRAS_GARDE = if BIG_ARM == "Right Arm" then "Left Arm" else "Right Arm"
local JAMBE_AVANT = if BIG_ARM == "Right Arm" then "Left Leg" else "Right Leg"
local JAMBE_ARRIERE = if BIG_ARM == "Right Arm" then "Right Leg" else "Left Leg"

-- En R6, l'axe Z des épaules et des hanches pointe vers l'extérieur : un angle positif envoie le
-- membre droit vers l'avant mais le membre gauche vers l'arrière. sideSign corrige ce sens.
local function sideSign(nomMembre: string): number
	return if string.sub(nomMembre, 1, 5) == "Right" then 1 else -1
end

-- Rotation d'une épaule ou d'une hanche R6 (en degrés) :
-- `avant` = vers l'avant, `rentre` = vers l'axe du corps (négatif = vers l'extérieur),
-- `lacet` = autour de l'axe vertical.
local function poseMembre(nomMembre: string, avant: number, rentre: number, lacet: number): CFrame
	return CFrame.Angles(0, math.rad(lacet), 0)
		* CFrame.Angles(0, 0, sideSign(nomMembre) * math.rad(avant))
		* CFrame.Angles(math.rad(rentre), 0, 0)
end

-- Rebond : 0 = haut, 1 = bas
local function rebond(t: number): number
	return (1 - math.cos(TAU * t / BOUNCE_PERIOD)) / 2
end

-- Balancement du torse sur toute la boucle, entre -1 et 1
local function balancement(t: number): number
	return math.sin(TAU * t / DURATION)
end

-- Recul du gros bras (°) : courbe quadratique entre WINDUP_START et WINDUP_PEAK, 0 ailleurs
local function armeGrosBras(t: number): number
	if t < WINDUP_START - EPSILON or t > WINDUP_PEAK + EPSILON then
		return 0
	end
	local u = math.clamp((t - WINDUP_START) / (WINDUP_PEAK - WINDUP_START), 0, 1)
	return WINDUP * u * u
end

-- CFrame (Motor6D.Transform) de chaque partie à l'instant t, indexé par le nom de Part1
local function calculerPoses(t: number): { [string]: CFrame }
	local b = rebond(t)
	local bRetard = rebond(t - FOLLOW_DELAY)
	local s = balancement(t)
	local lacetTorse = SWAY_YAW * s
	local roulisTorse = SWAY_ROLL * s

	-- Pas de genoux en R6 : la flexion est simulée en écartant les jambes, et le torse descend
	-- de LEG_LENGTH × (1 - cos(écart)) pour que les pieds restent au sol.
	local ecart = LEG_SPREAD_MIN + (LEG_SPREAD_MAX - LEG_SPREAD_MIN) * b
	local descente = LEG_LENGTH * (1 - math.cos(math.rad(ecart)))

	local poses: { [string]: CFrame } = {}
	-- Repère du RootJoint : X = gauche, Y = arrière, Z = haut
	poses.Torso = CFrame.new(0, 0, -descente) * CFrame.Angles(0, math.rad(roulisTorse), math.rad(lacetTorse))
	-- Jambes : contre-lacet pour que les pieds restent orientés vers l'avant malgré le torse
	poses[JAMBE_AVANT] = poseMembre(JAMBE_AVANT, ecart, 0, -lacetTorse)
	poses[JAMBE_ARRIERE] = poseMembre(JAMBE_ARRIERE, -ecart, 0, -lacetTorse)
	-- Bras de garde : tendu devant, légèrement rentré
	poses[BRAS_GARDE] = poseMembre(BRAS_GARDE, GUARD_FORWARD - ARM_DIP * bRetard, GUARD_TUCK, 0)
	-- Gros bras : armé en hauteur, recule encore (vers le haut et l'arrière) pendant l'armé
	poses[BIG_ARM] = poseMembre(BIG_ARM, BIG_FORWARD - ARM_DIP * bRetard + armeGrosBras(t), -BIG_OUTWARD, 0)
	if aTete then
		-- Repère du Neck : X = gauche (angle positif = tête vers l'avant), Z = haut
		poses.Head = CFrame.Angles(0, 0, math.rad(-HEAD_COUNTER_YAW * lacetTorse))
			* CFrame.Angles(math.rad(HEAD_TILT + HEAD_TILT_BOUNCE * bRetard), 0, 0)
	end
	if aCape then
		-- Le repère du Motor6D de la cape dépend du modèle : ajuster les axes si elle bouge mal
		poses.Cape = CFrame.Angles(math.rad(CAPE_SWING * bRetard), 0, math.rad(CAPE_SWAY * s))
	end
	return poses
end

local function creerPose(
	nom: string,
	cframe: CFrame,
	parent: Instance,
	style: Enum.PoseEasingStyle,
	direction: Enum.PoseEasingDirection
): Pose
	local pose = Instance.new("Pose")
	pose.Name = nom
	pose.CFrame = cframe
	pose.Weight = 1
	pose.EasingStyle = style
	pose.EasingDirection = direction
	pose.Parent = parent
	return pose
end

-- Construction de la séquence
local sequence = Instance.new("KeyframeSequence")
sequence.Name = NOM_SEQUENCE
sequence.Loop = true
sequence.Priority = Enum.AnimationPriority.Idle

local nbIntervalles = math.round(DURATION / STEP)
local indexPic = math.round(WINDUP_PEAK / STEP)
for i = 0, nbIntervalles do
	-- Le dernier keyframe reprend exactement les valeurs du premier : boucle parfaite
	local poses = calculerPoses(if i == nbIntervalles then 0 else i * STEP)

	local keyframe = Instance.new("Keyframe")
	keyframe.Name = `Keyframe{i}`
	keyframe.Time = if i == nbIntervalles then DURATION else i * STEP

	local cubic, inOut = Enum.PoseEasingStyle.Cubic, Enum.PoseEasingDirection.InOut
	local poseRacine = creerPose("HumanoidRootPart", CFrame.identity, keyframe, cubic, inOut)
	local poseTorse = creerPose("Torso", poses.Torso, poseRacine, cubic, inOut)
	for nom, cframe in poses do
		if nom ~= "Torso" then
			-- L'easing d'une Pose s'applique au trajet vers le keyframe suivant :
			-- Elastic/Out sur le pic = retour élastique du gros bras après l'armé
			if nom == BIG_ARM and i == indexPic then
				creerPose(nom, cframe, poseTorse, Enum.PoseEasingStyle.Elastic, Enum.PoseEasingDirection.Out)
			else
				creerPose(nom, cframe, poseTorse, cubic, inOut)
			end
		end
	end
	keyframe.Parent = sequence
end

-- Rangement : ServerStorage > RBX_ANIMSAVES > <ObjectValue du rig> > séquence
local enregistrement = ChangeHistoryService:TryBeginRecording(`Générer {NOM_SEQUENCE}`)

local dossier = ServerStorage:FindFirstChild("RBX_ANIMSAVES")
if dossier == nil then
	dossier = Instance.new("Folder")
	dossier.Name = "RBX_ANIMSAVES"
	dossier.Parent = ServerStorage
end
assert(dossier ~= nil, "Dossier RBX_ANIMSAVES introuvable.")

local lien: ObjectValue? = nil
for _, enfant in dossier:GetChildren() do
	if enfant:IsA("ObjectValue") and enfant.Value == rig then
		lien = enfant
		break
	end
end
if lien == nil then
	local nouveau = Instance.new("ObjectValue")
	nouveau.Name = rig.Name
	nouveau.Value = rig
	nouveau.Parent = dossier
	lien = nouveau
end
assert(lien ~= nil, "ObjectValue du rig introuvable.")

local ancienne = lien:FindFirstChild(NOM_SEQUENCE)
local remplacee = ancienne ~= nil
if ancienne then
	ancienne:Destroy()
end
sequence.Parent = lien
Selection:Set({ sequence })

if enregistrement then
	ChangeHistoryService:FinishRecording(enregistrement, Enum.FinishRecordingOperation.Commit)
else
	ChangeHistoryService:SetWaypoint(`Générer {NOM_SEQUENCE}`)
end

-- Résumé
print(`[CombatIdle] {NOM_SEQUENCE} {if remplacee then "remplacée" else "créée"} pour « {rig.Name} »`)
print(`  {nbIntervalles + 1} keyframes, {DURATION} s en boucle, un keyframe toutes les {STEP} s`)
print(`  {math.round(DURATION / BOUNCE_PERIOD)} rebonds, écart des jambes {LEG_SPREAD_MIN}° → {LEG_SPREAD_MAX}°`)
print(`  Gros bras : {BIG_ARM} (armé {WINDUP}° de {WINDUP_START} s à {WINDUP_PEAK} s), garde : {BRAS_GARDE}`)
print(
	`  Jambe avant : {JAMBE_AVANT}, tête : {if aTete then "oui" else "non"}, cape : {if aCape then "oui" else "non"}`
)
print(`  Rangée dans {sequence:GetFullName()}`)
