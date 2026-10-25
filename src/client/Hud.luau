--!strict
-- Hud : argent, revenu par seconde et argent à collecter, en haut à gauche de l'écran.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Ui = require(script.Parent.Ui)

local Hud = {}

local joueur = Players.LocalPlayer
local DUREE_COMPTEUR = 0.4

local labelArgent: TextLabel
local labelRevenu: TextLabel
local labelCollecte: TextLabel

function Hud.Init(ecran: ScreenGui)
	local cadre: Frame = Ui.Creer("Frame", {
		Name = "Hud",
		Position = UDim2.fromOffset(16, 16),
		Size = UDim2.fromOffset(250, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		BackgroundColor3 = Ui.Couleurs.Fond,
		BackgroundTransparency = 0.15,
		Parent = ecran,
	}, {
		Ui.Coins(14),
		Ui.Contour(Ui.Couleurs.Contour),
		Ui.Marges(12),
		Ui.Creer("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }),
	})
	Ui.Adapter(cadre)

	labelArgent = Ui.Texte({
		Name = "Argent",
		LayoutOrder = 1,
		Size = UDim2.new(1, 0, 0, 34),
		TextSize = 32,
		TextColor3 = Ui.Couleurs.Or,
		Text = "💰 0 $",
		Parent = cadre,
	})
	labelRevenu = Ui.Texte({
		Name = "Revenu",
		LayoutOrder = 2,
		Size = UDim2.new(1, 0, 0, 22),
		TextSize = 20,
		TextColor3 = Ui.Couleurs.Vert,
		Text = "+0 $/s",
		Parent = cadre,
	})
	labelCollecte = Ui.Texte({
		Name = "ACollecter",
		LayoutOrder = 3,
		Size = UDim2.new(1, 0, 0, 20),
		TextSize = 16,
		Font = Ui.PoliceTexte,
		TextColor3 = Ui.Couleurs.TexteDiscret,
		Text = "À collecter : 0 $",
		Parent = cadre,
	})

	local function majCollecte()
		local montant = joueur:GetAttribute(Remotes.Attributs.ArgentNonCollecte)
		local texte = Ui.FormaterNombre(if typeof(montant) == "number" then montant else 0)
		labelCollecte.Text = `À collecter : {texte} $`
	end
	local function majRevenu()
		local revenu = joueur:GetAttribute(Remotes.Attributs.RevenuParSeconde)
		labelRevenu.Text = `+{Ui.FormaterRevenu(if typeof(revenu) == "number" then revenu else 0)} $/s`
	end
	joueur:GetAttributeChangedSignal(Remotes.Attributs.ArgentNonCollecte):Connect(majCollecte)
	joueur:GetAttributeChangedSignal(Remotes.Attributs.RevenuParSeconde):Connect(majRevenu)
	majCollecte()
	majRevenu()

	-- Argent : leaderstats créées par le serveur après le chargement des données ; le compteur défile.
	task.spawn(function()
		local leaderstats = joueur:WaitForChild("leaderstats")
		local argent = leaderstats:WaitForChild("Argent") :: IntValue
		local affiche = Instance.new("NumberValue")
		affiche.Value = argent.Value
		local function majTexte()
			labelArgent.Text = `💰 {Ui.FormaterNombre(affiche.Value)} $`
		end
		affiche.Changed:Connect(majTexte)
		argent.Changed:Connect(function(valeur: number)
			TweenService:Create(affiche, TweenInfo.new(DUREE_COMPTEUR, Enum.EasingStyle.Quad), { Value = valeur })
				:Play()
		end)
		majTexte()
	end)
end

-- « +X $ » qui part de l'argent, monte et s'efface (rangé dans le label pour suivre l'échelle du HUD).
function Hud.MontrerCollecte(montant: number)
	local label = Ui.Texte({
		Name = "Gain",
		Position = UDim2.fromOffset(36, 0),
		Size = UDim2.fromScale(1, 1),
		TextSize = 28,
		TextColor3 = Ui.Couleurs.Vert,
		TextStrokeTransparency = 0.4,
		Text = `+{Ui.FormaterNombre(montant)} $`,
		ZIndex = 5,
		Parent = labelArgent,
	})
	local infos = TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	local tween = TweenService:Create(label, infos, {
		Position = UDim2.fromOffset(36, -40),
		TextTransparency = 1,
		TextStrokeTransparency = 1,
	})
	tween.Completed:Connect(function()
		label:Destroy()
	end)
	tween:Play()
end

return Hud
