--!strict
-- Notifications : toasts en haut au centre, sous la barre rapide (planche de style v2).
-- Types : "succes" (vert), "argent" (or), "erreur" (rouge), "info" (violet) ou un Id de rareté (Mythique…).

local Ui = require(script.Parent.Ui)

local Notifications = {}

local DUREE = 2.6
local MAX_VISIBLES = 3

export type Type = string

local TYPES: { [string]: { Teinte: Ui.Teinte, Icone: string } } = {
	succes = { Teinte = Ui.Teintes.Vert, Icone = "etoile" },
	argent = { Teinte = Ui.Teintes.Or, Icone = "billets" },
	erreur = { Teinte = Ui.Teintes.Danger, Icone = "fermer" },
	info = { Teinte = Ui.Teintes.Principal, Icone = "teleport" },
}

local pile: Frame
local compteur = 0

function Notifications.Init(racine: Frame)
	pile = Ui.Creer("Frame", {
		Name = "Notifications",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 72),
		Size = UDim2.fromOffset(600, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		ZIndex = 40,
		Parent = racine,
	}, {
		Ui.Liste(Enum.FillDirection.Vertical, 8, { HorizontalAlignment = Enum.HorizontalAlignment.Center }),
	})
end

function Notifications.Montrer(texte: string, typeToast: Type?)
	if typeof(texte) ~= "string" then
		return
	end
	local t = TYPES[typeToast or "info"]
	local teinte = if t then t.Teinte else Ui.Rarete(typeToast or "")
	local icone = if t then t.Icone else "etoile"
	if not t and not Ui.Raretes[typeToast or ""] then
		teinte, icone = TYPES.info.Teinte, TYPES.info.Icone
	end

	compteur += 1
	local toasts = {}
	for _, enfant in pile:GetChildren() do
		if enfant:IsA("Frame") then
			table.insert(toasts, enfant)
		end
	end
	if #toasts >= MAX_VISIBLES then
		table.sort(toasts, function(a, b)
			return a.LayoutOrder < b.LayoutOrder
		end)
		toasts[1]:Destroy()
	end

	-- Conteneur (taille du toast) → Ombre (+3 px) + Face qui glisse depuis le haut → Rangée (ruban, message) + barre
	local toast = Ui.Creer("Frame", {
		Name = "Toast",
		LayoutOrder = compteur,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 53),
		BackgroundTransparency = 1,
		Parent = pile,
	})
	Ui.Creer("Frame", {
		Name = "Ombre",
		Position = UDim2.fromOffset(0, 3),
		Size = UDim2.new(1, 0, 0, 50),
		BackgroundColor3 = Ui.C.Trait,
		Parent = toast,
	}, { Ui.Coins(12) })
	local face = Ui.Creer("Frame", {
		Name = "Face",
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(320, 50),
		BackgroundColor3 = Color3.new(1, 1, 1),
		ClipsDescendants = true,
		ZIndex = 2,
		Parent = toast,
	}, {
		Ui.Coins(12),
		Ui.Trait(2),
		Ui.Degrade2(Ui.C.PanneauHaut, Ui.C.PanneauBas),
	})
	local rangee = Ui.Creer("Frame", {
		Name = "Rangee",
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 50),
		BackgroundTransparency = 1,
		ZIndex = 2,
		Parent = face,
	}, {
		Ui.Liste(Enum.FillDirection.Horizontal, 12, { VerticalAlignment = Enum.VerticalAlignment.Center }),
		Ui.Marges(0, 20, 0, 0),
	})
	local ruban = Ui.Creer("Frame", {
		Name = "Ruban",
		LayoutOrder = 1,
		Size = UDim2.fromOffset(56, 50),
		BackgroundColor3 = Color3.new(1, 1, 1),
		BorderSizePixel = 0,
		ZIndex = 2,
		Parent = rangee,
	}, { Ui.Degrade(teinte, 90) })
	Ui.Icone(icone, 30, {
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.45, 0.5),
		ZIndex = 3,
		Parent = ruban,
	})
	Ui.Texte({
		Name = "Message",
		LayoutOrder = 2,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 50),
		TextSize = 17,
		Text = texte,
		Contour = true,
		ZIndex = 2,
		Parent = rangee,
	})
	Ui.Creer("Frame", {
		Name = "BarreBas",
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Size = UDim2.new(1, 0, 0, 3),
		BackgroundColor3 = teinte.Base,
		BorderSizePixel = 0,
		ZIndex = 3,
		Parent = face,
	})

	face.Position = UDim2.fromOffset(0, -24)
	Ui.Tween(face, 0.3, { Position = UDim2.new() }, Enum.EasingStyle.Back)

	task.delay(DUREE, function()
		if toast.Parent then
			toast:Destroy()
		end
	end)
end

return Notifications
