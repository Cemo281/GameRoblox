--!strict
-- EffetsForge : joue les effets VFX Forge (EmitModule, plugin VFX Forge 1.4.5) d'un effet de vitrine.
-- Un effet VFX.<Nom> peut contenir un ObjectValue « Forge » qui pointe vers son modèle, rangé hors du personnage
-- (ReplicatedStorage.EffetsForge.<perso>.<Nom> : des pièces dans le Model fausseraient sa boîte englobante).
-- Chaque enfant du modèle est un groupe construit autour de l'origine (0, 0, 0), avec l'attribut Ancre :
--   "Sol"    : sol sous le bassin du personnage (LowerTorso), tourné comme le personnage ;
--   "Membre" : main ou pied qui frappe, axe -Z = direction épaule/hanche → membre ;
--   "Torse"  : haut du torse, tourné comme le personnage.
--   "Point"  : attachment ou pièce nommée par l'attribut Point, tourné comme le personnage.
-- Attribut Point (texte) : nom d'un Attachment ou d'une pièce du modèle ; avec "Sol", le sol est cherché sous ce point.
-- Attribut Orientation = "Membre" (groupe "Sol") : sol tourné vers le membre qui frappe.
-- Les pièces portant l'attribut TeinteSol (0..1) prennent la couleur du sol, assombrie d'autant.
-- Le groupe est cloné, déplacé, puis joué par shared.vfx.emit (rochers, fissures, débris, maillages…).
-- Côté client : EmitModule ne crée shared.vfx que sur le client ; le serveur l'initialise pour les groupes de collision.

local CollectionService = game:GetService("CollectionService")
local PhysicsService = game:GetService("PhysicsService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EffetsForge = {}

local TAG_VITRINE = "PersonnageVitrine"
-- Tag local (client) des instances que les lancers de rayon des effets ignorent : personnages de vitrine et pièces
-- déjà posées par Forge (sinon le cratère de l'explosion se pose sur les rochers des pompes). Attribut FilterTag
-- des origines dans les modèles.
local TAG_IGNORE = "ForgeIgnore"
local NOM_CACHE = "DO_NOT_REMOVE_ForgeSharedPartCache"
-- Groupe des débris de Forge (enregistré par EmitModule côté serveur), qui ne collisionne pas avec lui-même : les
-- pièces des personnages de vitrine y sont mises sur ce client seulement, pour que les débris les traversent (un membre
-- animé qui heurte une pièce d'or l'envoyait à 25 studs de haut). Les joueurs (Default) les heurtent toujours.
local GROUPE_DEBRIS = "ForgeDebris"
-- Au-delà, les effets ne sont pas joués (rochers et débris coûtent des pièces)
local DISTANCE_MAX = 160

type Api = {
	init: () -> (),
	emit: (...any) -> { Finished: any },
}
local api: Api? = nil

local function parametresSol(): RaycastParams
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = CollectionService:GetTagged(TAG_IGNORE)
	params.IgnoreWater = true
	return params
end

local function aPlat(direction: Vector3): Vector3?
	local plat = Vector3.new(direction.X, 0, direction.Z)
	if plat.Magnitude < 1e-3 then
		return nil
	end
	return plat.Unit
end

local function directionMembre(modele: Model, membre: BasePart?): Vector3?
	local torse = modele:FindFirstChild("UpperTorso")
	if not (membre and torse and torse:IsA("BasePart")) then
		return nil
	end
	local direction = membre.Position - torse.Position
	if direction.Magnitude < 1e-3 then
		return nil
	end
	return direction.Unit
end

-- Position monde de l'Attachment ou de la pièce nommée `nom` dans le modèle
local function pointNomme(modele: Model, nom: unknown): Vector3?
	if typeof(nom) ~= "string" then
		return nil
	end
	local instance = modele:FindFirstChild(nom, true)
	if instance and instance:IsA("Attachment") then
		return instance.WorldPosition
	elseif instance and instance:IsA("BasePart") then
		return instance.Position
	end
	return nil
end

-- CFrame de l'ancre et résultat du lancer de rayon vers le sol (pour TeinteSol)
local function ancrer(groupe: Instance, modele: Model, membre: BasePart?): (CFrame?, RaycastResult?)
	local pivot = modele:GetPivot()
	local regard = aPlat(pivot.LookVector) or Vector3.new(0, 0, -1)
	local ancre = groupe:GetAttribute("Ancre")
	local point = pointNomme(modele, groupe:GetAttribute("Point"))
	if ancre == "Membre" then
		local direction = directionMembre(modele, membre)
		if not (membre and direction) then
			return nil, nil
		end
		return CFrame.lookAt(membre.Position, membre.Position + direction), nil
	elseif ancre == "Torse" or ancre == "Point" then
		local torse = modele:FindFirstChild("UpperTorso")
		local position = point or (if torse and torse:IsA("BasePart") then torse.Position else pivot.Position)
		return CFrame.lookAt(position, position + regard), nil
	end
	-- "Sol" (par défaut) : sous le point nommé, sinon sous le bassin
	local bassin = modele:FindFirstChild("LowerTorso")
	local depart = point or (if bassin and bassin:IsA("BasePart") then bassin.Position else pivot.Position)
	local resultat = workspace:Raycast(depart + Vector3.new(0, 2, 0), Vector3.new(0, -14, 0), parametresSol())
	if not resultat then
		return nil, nil
	end
	if groupe:GetAttribute("Orientation") == "Membre" then
		local direction = directionMembre(modele, membre)
		regard = direction and aPlat(direction) or regard
	end
	return CFrame.lookAt(resultat.Position, resultat.Position + regard), resultat
end

local function placer(groupe: Instance, cadre: CFrame, sol: RaycastResult?)
	for _, piece in groupe:GetDescendants() do
		if piece:IsA("BasePart") then
			piece.CFrame = cadre * piece.CFrame
			local teinte = piece:GetAttribute("TeinteSol")
			if sol and typeof(teinte) == "number" and sol.Instance:IsA("BasePart") then
				piece.Color = sol.Instance.Color:Lerp(Color3.new(0, 0, 0), teinte)
			end
		end
	end
end

-- Joue les groupes du dossier Forge de l'effet `dossier` (VFX.<Nom>) sur `modele`.
function EffetsForge.Jouer(modele: Model, dossier: Instance, membre: BasePart?)
	local lien = dossier:FindFirstChild("Forge")
	local forge = if lien and lien:IsA("ObjectValue") then lien.Value else lien
	local vfx = api
	if not (forge and vfx) then
		return
	end
	local camera = workspace.CurrentCamera
	if camera and (camera.CFrame.Position - modele:GetPivot().Position).Magnitude > DISTANCE_MAX then
		return
	end
	for _, groupe in forge:GetChildren() do
		local cadre, sol = ancrer(groupe, modele, membre)
		if cadre then
			local copie = groupe:Clone()
			placer(copie, cadre, sol)
			local ok, env = pcall(vfx.emit, copie)
			if ok and env and env.Finished then
				env.Finished:finally(function()
					copie:Destroy()
				end)
			else
				if not ok then
					warn(`[EffetsForge] {dossier.Name}/{groupe.Name} : {env}`)
				end
				copie:Destroy()
			end
		end
	end
end

local function traversableParDebris(piece: Instance)
	if piece:IsA("BasePart") and PhysicsService:IsCollisionGroupRegistered(GROUPE_DEBRIS) then
		piece.CollisionGroup = GROUPE_DEBRIS
	end
end

-- Vitrine : ignorée par les lancers de rayon des effets, traversée par les débris (pièces arrivées plus tard comprises)
local function suivreVitrine(modele: Instance)
	modele:AddTag(TAG_IGNORE)
	for _, piece in modele:GetDescendants() do
		traversableParDebris(piece)
	end
	modele.DescendantAdded:Connect(traversableParDebris)
end

function EffetsForge.Init()
	task.spawn(function()
		local module = ReplicatedStorage:WaitForChild("EmitModule", 15)
		if not (module and module:IsA("ModuleScript")) then
			return
		end
		local ok, resultat = pcall(require, module)
		if not ok then
			warn(`[EffetsForge] EmitModule : {resultat}`)
			return
		end
		local module_api = resultat :: Api
		module_api.init()
		api = module_api
		local cache = workspace.Terrain:FindFirstChild(NOM_CACHE)
		if cache then
			cache:AddTag(TAG_IGNORE)
		end
		-- après l'init : le groupe ForgeDebris est enregistré par le serveur au démarrage
		for _, modele in CollectionService:GetTagged(TAG_VITRINE) do
			suivreVitrine(modele)
		end
		CollectionService:GetInstanceAddedSignal(TAG_VITRINE):Connect(suivreVitrine)
	end)
end

return EffetsForge
