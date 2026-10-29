--!strict
-- Vitrine : sur chaque personnage posé (Model tagué "PersonnageVitrine" par BaseService), applique les marqueurs
-- des animations jouées par le serveur : Montrer / Cacher un accessoire, déclencher un effet du dossier VFX.
-- Fait côté client car ParticleEmitter:Emit() n'est pas répliqué ; chaque joueur voit donc sabres et effets.
-- Conventions du modèle : skill /perso-roblox (sections 3 et 5).

local CollectionService = game:GetService("CollectionService")

local Vitrine = {}

local TAG_VITRINE = "PersonnageVitrine"

-- Remet chaque accessoire dans son état par défaut (attribut VisibleParDefaut), ex. pour un joueur arrivé en cours d'Action.
local function reinitialiserAccessoires(modele: Model)
	for _, enfant in modele:GetChildren() do
		local visible = enfant:GetAttribute("VisibleParDefaut")
		local handle = enfant:IsA("Accessory") and enfant:FindFirstChild("Handle")
		if typeof(visible) == "boolean" and handle and handle:IsA("BasePart") then
			handle.Transparency = if visible then 0 else 1
		end
	end
end

local function montrer(modele: Model, nom: string, visible: boolean)
	local accessoire = modele:FindFirstChild(nom)
	local handle = accessoire and accessoire:FindFirstChild("Handle")
	if handle and handle:IsA("BasePart") then
		handle.Transparency = if visible then 0 else 1
	end
end

local function emetteurs(dossier: Instance): { Instance }
	local liste = {}
	for _, lien in dossier:GetChildren() do
		if lien:IsA("ObjectValue") and lien.Value then
			table.insert(liste, lien.Value)
		end
	end
	return liste
end

local function allumer(emetteur: Instance, actif: boolean)
	if emetteur:IsA("ParticleEmitter") or emetteur:IsA("Trail") or emetteur:IsA("Beam") then
		emetteur.Enabled = actif
	end
end

-- Marqueur « VFX <Nom> » : Mode "Burst" (Emit(Quantite) de chaque émetteur) ou "Duree" (allumé Duree secondes).
-- Marqueur « VFX <Nom>_Fin » : éteint l'effet <Nom>.
local function declencher(modele: Model, nom: string)
	local vfx = modele:FindFirstChild("VFX")
	if not vfx then
		return
	end
	local base = string.match(nom, "^(.+)_Fin$")
	if base then
		local dossier = vfx:FindFirstChild(base)
		if dossier then
			for _, emetteur in emetteurs(dossier) do
				allumer(emetteur, false)
			end
		end
		return
	end

	local dossier = vfx:FindFirstChild(nom)
	if not dossier then
		return
	end
	local mode = dossier:GetAttribute("Mode")
	if mode == "Burst" then
		for _, emetteur in emetteurs(dossier) do
			if emetteur:IsA("ParticleEmitter") then
				local quantite = emetteur:GetAttribute("Quantite")
				emetteur:Emit(if typeof(quantite) == "number" then quantite else 1)
			end
		end
	elseif mode == "Duree" then
		local duree = dossier:GetAttribute("Duree")
		for _, emetteur in emetteurs(dossier) do
			allumer(emetteur, true)
			task.delay(if typeof(duree) == "number" then duree else 1, function()
				if emetteur.Parent then
					allumer(emetteur, false)
				end
			end)
		end
	end
end

local function suivre(instance: Instance)
	if not instance:IsA("Model") then
		return
	end
	local modele = instance
	local controleur = modele:FindFirstChildOfClass("AnimationController") or modele:FindFirstChildOfClass("Humanoid")
	local animator = controleur and controleur:WaitForChild("Animator", 10)
	if not (animator and animator:IsA("Animator")) then
		return
	end

	local idle = modele:GetAttribute("AnimationIdle")
	local connexions: { RBXScriptConnection } = {}
	table.insert(
		connexions,
		animator.AnimationPlayed:Connect(function(piste: AnimationTrack)
			if piste.Animation and piste.Animation.AnimationId == idle then
				reinitialiserAccessoires(modele)
			end
			table.insert(
				connexions,
				piste:GetMarkerReachedSignal("Montrer"):Connect(function(nom: string)
					montrer(modele, nom, true)
				end)
			)
			table.insert(
				connexions,
				piste:GetMarkerReachedSignal("Cacher"):Connect(function(nom: string)
					montrer(modele, nom, false)
				end)
			)
			table.insert(
				connexions,
				piste:GetMarkerReachedSignal("VFX"):Connect(function(nom: string)
					declencher(modele, nom)
				end)
			)
		end)
	)
	table.insert(
		connexions,
		modele.Destroying:Connect(function()
			for _, connexion in connexions do
				connexion:Disconnect()
			end
		end)
	)
end

function Vitrine.Init()
	for _, instance in CollectionService:GetTagged(TAG_VITRINE) do
		task.spawn(suivre, instance)
	end
	CollectionService:GetInstanceAddedSignal(TAG_VITRINE):Connect(suivre)
end

return Vitrine
