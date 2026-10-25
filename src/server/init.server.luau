--!strict
-- Point d'entrée serveur : initialise les services dans l'ordre.

local BaseService = require(script.BaseService)
local DataService = require(script.DataService)
local GachaService = require(script.GachaService)
local InterfaceService = require(script.InterfaceService)
local RevenuService = require(script.RevenuService)

DataService.Init()
BaseService.Init()
InterfaceService.Init()
GachaService.Init()
RevenuService.Init()
