--!strict
-- PROVISOIRE : revenu passif de test en attendant le vrai revenu généré par les personnages.
-- À supprimer quand la ferme passive sera codée.

local Players = game:GetService("Players")

local DataService = require(script.Parent:WaitForChild("DataService"))

local MONTANT = 1 -- Argent gagné
local INTERVALLE = 1 -- toutes les X secondes

while true do
	task.wait(INTERVALLE)
	for _, player in Players:GetPlayers() do
		DataService.AddArgent(player, MONTANT)
	end
end
