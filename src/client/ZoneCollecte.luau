--!strict
-- ZoneCollecte : animations visuelles de la collecte des zones « Sanctuaire » (Model tagué "CollecteAnimee",
-- construit par assets/zone/construire_zone.luau) : colonne de lumière qui pulse, 3 pièces qui tournent en montant,
-- gerbe de pièces sur le collecteur de sa propre base quand on collecte (Emit n'est pas répliqué : côté client).
-- Purement visuel : rien n'est envoyé au serveur.

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local ZoneCollecte = {}

local TAG = "CollecteAnimee"
local DISTANCE_ANIMATION = 200 -- studs : au-delà, la collecte reste figée
local RAYON_PIECES = 1.3
local MONTEE_PIECES = 2.6
local GERBE = 30

type Collecte = {
	modele: Model,
	colonne: BasePart?,
	pieces: { { part: BasePart, depart: CFrame, index: number } },
	connues: { [BasePart]: boolean },
}

local collectes: { [Model]: Collecte } = {}

local NB_PIECES = 3

-- Colonne et pièces : avec le streaming, elles peuvent arriver après le Model → recherchées tant qu'il en manque.
local function completer(c: Collecte)
	if not c.colonne then
		local colonne = c.modele:FindFirstChild("Colonne")
		c.colonne = if colonne and colonne:IsA("BasePart") then colonne else nil
	end
	local dossier = c.modele:FindFirstChild("Pieces")
	if not dossier then
		return
	end
	for _, p in dossier:GetChildren() do
		local index = p:GetAttribute("Index")
		if p:IsA("BasePart") and typeof(index) == "number" and not c.connues[p] then
			c.connues[p] = true
			table.insert(c.pieces, { part = p, depart = p.CFrame, index = index })
		end
	end
end

local function ajouter(instance: Instance)
	if not instance:IsA("Model") or collectes[instance] then
		return
	end
	local c: Collecte = { modele = instance, colonne = nil, pieces = {}, connues = {} }
	completer(c)
	collectes[instance] = c
end

local function retirer(instance: Instance)
	if instance:IsA("Model") then
		collectes[instance] = nil
	end
end

-- Gerbe de pièces sur le collecteur de la base du joueur local (appelée à la réception d'une collecte).
function ZoneCollecte.Gerbe()
	local joueur = Players.LocalPlayer
	for modele in collectes do
		local base = modele.Parent
		if base and base:GetAttribute("Proprietaire") == joueur.UserId then
			local disque = modele:FindFirstChild("Collecte_Disque_Or")
			local gerbe = disque and disque:FindFirstChild("Gerbe")
			if gerbe and gerbe:IsA("ParticleEmitter") then
				gerbe:Emit(GERBE)
			end
		end
	end
end

function ZoneCollecte.Init()
	for _, instance in CollectionService:GetTagged(TAG) do
		ajouter(instance)
	end
	CollectionService:GetInstanceAddedSignal(TAG):Connect(ajouter)
	CollectionService:GetInstanceRemovedSignal(TAG):Connect(retirer)

	RunService.Heartbeat:Connect(function()
		local camera = workspace.CurrentCamera
		if not camera then
			return
		end
		local t = os.clock()
		for _, c in collectes do
			if #c.pieces < NB_PIECES then
				completer(c)
			end
			if
				#c.pieces == 0
				or (c.pieces[1].depart.Position - camera.CFrame.Position).Magnitude > DISTANCE_ANIMATION
			then
				continue
			end
			if c.colonne then
				c.colonne.Transparency = 0.85 + 0.05 * math.sin(t * 2)
			end
			for _, p in c.pieces do
				local a = t * 1.2 + p.index * math.rad(120)
				local montee = ((t * 0.6 + p.index / 3) % 1) * MONTEE_PIECES
				p.part.CFrame = p.depart
					* CFrame.new(math.cos(a) * RAYON_PIECES, montee, math.sin(a) * RAYON_PIECES)
					* CFrame.Angles(0, t * 3 + p.index, 0)
			end
		end
	end)
end

return ZoneCollecte
