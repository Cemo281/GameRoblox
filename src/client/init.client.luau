--!strict
-- Point d'entrée client : crée l'interface (style v2 du handoff design_handoff_ui_roblox) et la relie au serveur.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = require(ReplicatedStorage.Shared.Remotes)
local Autel = require(script.Autel)
local DecorAnime = require(script.DecorAnime)
local Hud = require(script.Hud)
local Images = require(script.Images)
local Index = require(script.Index)
local Inventaire = require(script.Inventaire)
local Notifications = require(script.Notifications)
local Teleportation = require(script.Teleportation)
local Tirage = require(script.Tirage)
local Ui = require(script.Ui)
local Vitrine = require(script.Vitrine)
local ZoneCollecte = require(script.ZoneCollecte)

local ecran = Ui.Creer("ScreenGui", {
	Name = "Interface",
	ResetOnSpawn = false,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
	-- plein écran (la maquette place l'argent à côté du bouton menu de Roblox), en évitant les encoches
	ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets,
	Parent = Players.LocalPlayer:WaitForChild("PlayerGui"),
})
local racine = Ui.Racine(ecran)

Images.Init()
Notifications.Init(racine)
Hud.Init(racine, Notifications.Montrer)
Teleportation.Init(racine, Notifications.Montrer)
Inventaire.Init()
Index.Init()
Tirage.Init(racine)
Vitrine.Init()
DecorAnime.Init()
Autel.Init()
ZoneCollecte.Init()

Hud.SurMenu("teleport", Teleportation.Basculer)

Remotes.Evenement("Inventaire").OnClientEvent:Connect(function(etat: Remotes.EtatInventaire)
	Inventaire.MettreAJour(etat)
	Index.MettreAJour(etat)
end)
Remotes.Evenement("ResultatTirage").OnClientEvent:Connect(Tirage.Montrer)
Remotes.Evenement("Collecte").OnClientEvent:Connect(function(montant: number)
	Hud.MontrerCollecte(montant)
	ZoneCollecte.Gerbe()
end)
Remotes.Evenement("Notification").OnClientEvent:Connect(Notifications.Montrer)
