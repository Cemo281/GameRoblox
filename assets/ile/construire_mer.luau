--!strict
-- Mer sous l'île volante : eau du Terrain (lancé par MCP, Edit). Relançable : vide d'abord la zone.

local Terrain = workspace.Terrain

local CENTRE = Vector3.new(-14, 0, 0) -- centre du Hub
local NIVEAU = -380 -- surface de l'eau (pointe de l'île à ≈ -255)
local EPAISSEUR = 16
local DEMI_COTE = 4096 -- la mer couvre 8192 × 8192 studs, l'Atmosphere estompe le bord
local BLOC = 1024

local function remplir(materiau: Enum.Material)
	local y = NIVEAU - EPAISSEUR / 2
	for x = -DEMI_COTE, DEMI_COTE - BLOC, BLOC do
		for z = -DEMI_COTE, DEMI_COTE - BLOC, BLOC do
			local cf = CFrame.new(CENTRE.X + x + BLOC / 2, y, CENTRE.Z + z + BLOC / 2)
			Terrain:FillBlock(cf, Vector3.new(BLOC, EPAISSEUR, BLOC), materiau)
		end
		task.wait()
	end
end

remplir(Enum.Material.Air)
remplir(Enum.Material.Water)

-- Bleu proche de l'horizon du ciel : au-delà de la distance d'affichage du terrain, on voit le ciel
Terrain.WaterColor = Color3.fromRGB(16, 84, 170)
Terrain.WaterTransparency = 0.15
Terrain.WaterReflectance = 0.6
Terrain.WaterWaveSize = 0.2
Terrain.WaterWaveSpeed = 8

return "Mer construite à y = " .. NIVEAU
