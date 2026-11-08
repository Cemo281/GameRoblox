--!strict
-- Point d'entrée serveur : initialise les services dans l'ordre.

local BaseService = require(script.BaseService)
local DataService = require(script.DataService)
local DeplacementService = require(script.DeplacementService)
local GachaService = require(script.GachaService)
local InterfaceService = require(script.InterfaceService)
local RevenuService = require(script.RevenuService)

DataService.Init()
BaseService.Init()
InterfaceService.Init()
GachaService.Init()
RevenuService.Init()
DeplacementService.Init()

-- EmitModule (plugin VFX Forge, dans la place, pas dans Rojo) : côté serveur, init() enregistre seulement les
-- groupes de collision des débris (ForgeDebris) ; les effets sont joués par les clients (EffetsForge).
local emitModule = game:GetService("ReplicatedStorage"):FindFirstChild("EmitModule")
if emitModule and emitModule:IsA("ModuleScript") then
	local ok, resultat = pcall(require, emitModule)
	if ok then
		(resultat :: any).init()
	else
		warn(`EmitModule : {resultat}`)
	end
end
