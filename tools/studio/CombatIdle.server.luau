--!strict
-- Joue l'animation « Combat Idle » en boucle sur le personnage qui contient ce Script.
-- À placer directement dans le Model du personnage (Script serveur, pas LocalScript) : l'animation est
-- lancée par le serveur sur l'Animator du Humanoid, donc tous les joueurs la voient.
-- Ce fichier n'est pas synchronisé par Rojo (dossier tools/) : copier son contenu dans le Script.
--
-- Le code de combat signale une attaque avec un attribut du personnage :
--   personnage:SetAttribute("Attacking", true)  -- début de l'attaque : l'idle s'arrête
--   personnage:SetAttribute("Attacking", false) -- fin de l'attaque : l'idle reprend si le personnage est immobile

local ANIMATION_ID = "rbxassetid://0000000000" -- à remplacer par l'ID de l'animation publiée
local VITESSE_MAX = 0.5 -- au-delà, le personnage marche : pas d'idle
local FONDU_ENTREE = 0.3 -- (s)
local FONDU_SORTIE = 0.2 -- (s)

-- États où l'idle ne doit pas jouer (en l'air, à terre, mort…)
local ETATS_BLOQUANTS: { [Enum.HumanoidStateType]: boolean } = {
	[Enum.HumanoidStateType.Jumping] = true,
	[Enum.HumanoidStateType.Freefall] = true,
	[Enum.HumanoidStateType.FallingDown] = true,
	[Enum.HumanoidStateType.Climbing] = true,
	[Enum.HumanoidStateType.Swimming] = true,
	[Enum.HumanoidStateType.Ragdoll] = true,
	[Enum.HumanoidStateType.Dead] = true,
}

local personnage = script.Parent
assert(
	personnage ~= nil and personnage:IsA("Model"),
	"CombatIdle doit être placé directement dans le Model du personnage."
)
local humanoid = personnage:WaitForChild("Humanoid") :: Humanoid

if ANIMATION_ID == "rbxassetid://0000000000" then
	warn(`[CombatIdle] {personnage.Name} : remplacer ANIMATION_ID par l'ID de l'animation publiée.`)
	return
end

-- Animator côté serveur : les animations qu'il joue sont répliquées à tous les clients
local animator = humanoid:FindFirstChildOfClass("Animator")
if animator == nil then
	local nouveau = Instance.new("Animator")
	nouveau.Parent = humanoid
	animator = nouveau
end
assert(animator ~= nil, "Animator introuvable.")

-- Piste chargée une seule fois
local animation = Instance.new("Animation")
animation.AnimationId = ANIMATION_ID
local piste = animator:LoadAnimation(animation)
piste.Looped = true
piste.Priority = Enum.AnimationPriority.Idle

local vitesse = 0
local etat = humanoid:GetState()

local function mettreAJour()
	local doitJouer = humanoid.Health > 0
		and vitesse < VITESSE_MAX
		and not ETATS_BLOQUANTS[etat]
		and personnage:GetAttribute("Attacking") ~= true
	if doitJouer and not piste.IsPlaying then
		piste:Play(FONDU_ENTREE)
	elseif not doitJouer and piste.IsPlaying then
		piste:Stop(FONDU_SORTIE)
	end
end

local connexions: { RBXScriptConnection } = {
	humanoid.Running:Connect(function(nouvelleVitesse: number)
		vitesse = nouvelleVitesse
		mettreAJour()
	end),
	humanoid.StateChanged:Connect(function(_ancien: Enum.HumanoidStateType, nouveau: Enum.HumanoidStateType)
		etat = nouveau
		mettreAJour()
	end),
	personnage:GetAttributeChangedSignal("Attacking"):Connect(mettreAJour),
}

humanoid.Died:Once(function()
	for _, connexion in connexions do
		connexion:Disconnect()
	end
	piste:Stop(FONDU_SORTIE)
end)

mettreAJour()
