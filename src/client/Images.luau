--!strict
-- Images : affichage des images de personnages (cadre de rareté, portrait, silhouette, grille Idle animée, reflet Secret).
-- IDs dans Shared.ImagesPersonnages ; un perso sans images renvoie nil et l'appelant garde son bloc coloré.

local ContentProvider = game:GetService("ContentProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local ImagesPersonnages = require(ReplicatedStorage.Shared.ImagesPersonnages)
local Ui = require(script.Parent.Ui)

local Images = {}

local DUREE_REFLET = 1.4
local PAUSE_REFLET = 1.6

type Animation = { Grille: ImagesPersonnages.GrilleIdle, Debut: number }
local animations: { [ImageLabel]: Animation } = {}

function Images.De(id: string): ImagesPersonnages.ImagesPerso?
	return ImagesPersonnages.ParPerso[id]
end

-- ImageLabel du cadre de la rareté, à la taille du parent (nil si la rareté n'a pas de cadre).
function Images.Cadre(rarete: string, props: { [string]: any }?): ImageLabel?
	local image = ImagesPersonnages.Cadres[rarete]
	if not image then
		return nil
	end
	local defauts: { [string]: any } = {
		Name = "Cadre",
		Size = UDim2.fromScale(1, 1),
		BackgroundTransparency = 1,
		Image = image,
	}
	for cle, valeur in props or {} do
		defauts[cle] = valeur
	end
	return Ui.Creer("ImageLabel", defauts)
end

-- Fait jouer la grille Idle du perso dans `label` (renvoie false si le perso n'a pas de grille).
-- L'animation s'arrête d'elle-même quand le label est détruit ou reçoit une autre image.
function Images.Animer(label: ImageLabel, id: string): boolean
	local images = ImagesPersonnages.ParPerso[id]
	if not images then
		Images.Arreter(label)
		return false
	end
	local grille = images.Idle
	label.Image = grille.Image
	label.ImageRectSize = Vector2.new(grille.TailleCase, grille.TailleCase)
	label.ImageRectOffset = Vector2.zero
	animations[label] = { Grille = grille, Debut = os.clock() }
	return true
end

-- Arrête l'animation de `label` et lui rend l'image entière.
function Images.Arreter(label: ImageLabel)
	animations[label] = nil
	label.ImageRectSize = Vector2.zero
	label.ImageRectOffset = Vector2.zero
end

local function avancer()
	local maintenant = os.clock()
	for label, animation in animations do
		local grille = animation.Grille
		if not label.Parent or label.Image ~= grille.Image then
			animations[label] = nil
			continue
		end
		local case = math.floor((maintenant - animation.Debut) * grille.Fps) % (grille.Colonnes * grille.Lignes)
		label.ImageRectOffset =
			Vector2.new((case % grille.Colonnes) * grille.TailleCase, (case // grille.Colonnes) * grille.TailleCase)
	end
end

-- Bande de lumière qui traverse `parent` en boucle (cadre Secret), découpée aux coins arrondis.
function Images.Reflet(parent: GuiObject, rayon: number, zIndex: number?): CanvasGroup
	local groupe = Ui.Creer("CanvasGroup", {
		Name = "Reflet",
		Size = UDim2.fromScale(1, 1),
		BackgroundTransparency = 1,
		ZIndex = zIndex or 5,
		Parent = parent,
	}, { Ui.Coins(rayon) })
	local bande = Ui.Creer("ImageLabel", {
		Size = UDim2.fromScale(1, 1),
		Position = UDim2.fromScale(-1, 0),
		BackgroundTransparency = 1,
		Image = ImagesPersonnages.RefletSecret,
		Parent = groupe,
	})
	-- premier passage tout de suite, puis un toutes les DUREE_REFLET + PAUSE_REFLET secondes
	-- (le DelayTime d'un TweenInfo retarderait aussi le premier)
	local tween = TweenService:Create(
		bande,
		TweenInfo.new(DUREE_REFLET, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut),
		{ Position = UDim2.fromScale(1, 0) }
	)
	task.spawn(function()
		while groupe.Parent do
			bande.Position = UDim2.fromScale(-1, 0)
			tween:Play()
			task.wait(DUREE_REFLET + PAUSE_REFLET)
		end
	end)
	groupe.Destroying:Connect(function()
		tween:Cancel()
	end)
	return groupe
end

function Images.Init()
	RunService.Heartbeat:Connect(avancer)
	task.spawn(function()
		local liste: { string } = { ImagesPersonnages.RefletSecret }
		for _, image in ImagesPersonnages.Cadres do
			table.insert(liste, image)
		end
		for _, images in ImagesPersonnages.ParPerso do
			table.insert(liste, images.Portrait)
			table.insert(liste, images.Silhouette)
			table.insert(liste, images.Idle.Image)
		end
		ContentProvider:PreloadAsync(liste)
	end)
end

return Images
