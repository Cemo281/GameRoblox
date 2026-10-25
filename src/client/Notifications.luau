--!strict
-- Notifications : messages courts en haut au centre de l'écran (inventaire plein, emplacements occupés…).

local TweenService = game:GetService("TweenService")

local Ui = require(script.Parent.Ui)

local Notifications = {}

local DUREE = 3
local MAX_VISIBLES = 3

local pile: Frame

function Notifications.Init(ecran: ScreenGui)
	pile = Ui.Creer("Frame", {
		Name = "Notifications",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 16),
		Size = UDim2.fromOffset(460, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 1,
		ZIndex = 20,
		Parent = ecran,
	}, {
		Ui.Creer("UIListLayout", {
			Padding = UDim.new(0, 6),
			HorizontalAlignment = Enum.HorizontalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder,
		}),
	})
	Ui.Adapter(pile)
end

local compteur = 0
function Notifications.Montrer(texte: string)
	compteur += 1
	local messages = {}
	for _, enfant in pile:GetChildren() do
		if enfant:IsA("TextLabel") then
			table.insert(messages, enfant)
		end
	end
	if #messages >= MAX_VISIBLES then
		table.sort(messages, function(a, b)
			return a.LayoutOrder < b.LayoutOrder
		end)
		messages[1]:Destroy()
	end

	local label = Ui.Texte({
		Name = "Message",
		LayoutOrder = compteur,
		Size = UDim2.fromScale(1, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundTransparency = 0.1,
		BackgroundColor3 = Ui.Couleurs.Fond,
		TextSize = 18,
		TextWrapped = true,
		TextXAlignment = Enum.TextXAlignment.Center,
		Text = texte,
		Parent = pile,
	})
	Ui.Coins(10).Parent = label
	Ui.Contour(Ui.Couleurs.Or).Parent = label
	Ui.Marges(10).Parent = label

	task.delay(DUREE, function()
		if not label.Parent then
			return
		end
		local tween =
			TweenService:Create(label, TweenInfo.new(0.3), { TextTransparency = 1, BackgroundTransparency = 1 })
		tween.Completed:Connect(function()
			label:Destroy()
		end)
		tween:Play()
	end)
end

return Notifications
