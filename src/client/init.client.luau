--!strict
-- Point d'entrée client : crée l'interface et la relie aux événements du serveur.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Hud = require(script.Hud)
local Inventaire = require(script.Inventaire)
local Notifications = require(script.Notifications)
local Tirage = require(script.Tirage)
local Ui = require(script.Ui)

local ecran = Ui.Creer("ScreenGui", {
	Name = "Interface",
	ResetOnSpawn = false,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
	Parent = Players.LocalPlayer:WaitForChild("PlayerGui"),
})

Hud.Init(ecran)
Inventaire.Init(ecran)
Tirage.Init(ecran)
Notifications.Init(ecran)

Remotes.Evenement("Inventaire").OnClientEvent:Connect(Inventaire.MettreAJour)
Remotes.Evenement("ResultatTirage").OnClientEvent:Connect(Tirage.Montrer)
Remotes.Evenement("Collecte").OnClientEvent:Connect(Hud.MontrerCollecte)
Remotes.Evenement("Notification").OnClientEvent:Connect(Notifications.Montrer)
