--!strict
-- DecorAnime : animations purement visuelles du décor (cœur flottant du Hub…), jouées côté client.
-- Aucun effet de jeu : rien n'est envoyé au serveur.
-- Tag "DecorTournant" (Model, attribut Vitesse en °/s) : tourne autour de l'axe Y de son pivot.
-- Tag "DecorFlottant" (Model, attributs Amplitude en studs et Periode en s) : monte et descend doucement.

local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")

local DecorAnime = {}

type Anime = {
	modele: Model,
	pivot: CFrame,
	vitesse: number,
	amplitude: number,
	periode: number,
}

local animes: { [Model]: Anime } = {}

local function nombre(modele: Model, nom: string, defaut: number): number
	local valeur = modele:GetAttribute(nom)
	return if typeof(valeur) == "number" then valeur else defaut
end

local function ajouter(instance: Instance)
	if not instance:IsA("Model") or animes[instance] then
		return
	end
	animes[instance] = {
		modele = instance,
		pivot = instance:GetPivot(),
		vitesse = if CollectionService:HasTag(instance, "DecorTournant") then nombre(instance, "Vitesse", 20) else 0,
		amplitude = if CollectionService:HasTag(instance, "DecorFlottant") then nombre(instance, "Amplitude", 1) else 0,
		periode = math.max(0.1, nombre(instance, "Periode", 4)),
	}
end

local function retirer(instance: Instance)
	if instance:IsA("Model") then
		animes[instance] = nil
	end
end

function DecorAnime.Init()
	for _, tag in { "DecorTournant", "DecorFlottant" } do
		for _, instance in CollectionService:GetTagged(tag) do
			ajouter(instance)
		end
		CollectionService:GetInstanceAddedSignal(tag):Connect(ajouter)
		CollectionService:GetInstanceRemovedSignal(tag):Connect(retirer)
	end

	RunService.Heartbeat:Connect(function()
		local t = os.clock()
		for modele, a in animes do
			local cf = a.pivot
			if a.amplitude ~= 0 then
				cf += Vector3.new(0, a.amplitude * math.sin(t * 2 * math.pi / a.periode), 0)
			end
			if a.vitesse ~= 0 then
				cf *= CFrame.Angles(0, math.rad(a.vitesse * t % 360), 0)
			end
			modele:PivotTo(cf)
		end
	end)
end

return DecorAnime
