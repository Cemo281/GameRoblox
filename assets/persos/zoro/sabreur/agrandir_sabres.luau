--!strict
-- Agrandit les 3 sabres sortis de zoro (Acc_Sabre_Droit / Gauche / Bouche), jugés « jouets » à 3,5 studs.
-- Relançable : l'échelle est relative à la taille d'origine (attribut TailleOrigine), pas cumulée.
-- Cibles : ReplicatedStorage.ModelesPersonnages.zoro et Workspace.Sabreur_Apercu.
local ECHELLE = 1.4

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function agrandir(modele: Model): string
	local lignes = {}
	for _, nom in { "Acc_Sabre_Droit", "Acc_Sabre_Gauche", "Acc_Sabre_Bouche" } do
		local acc = modele:FindFirstChild(nom)
		local handle = acc and acc:FindFirstChild("Handle")
		if acc and handle and handle:IsA("BasePart") then
			local origine = acc:GetAttribute("TailleOrigine")
			local echelleActuelle = 1
			if typeof(origine) == "Vector3" then
				echelleActuelle = handle.Size.Z / origine.Z
			else
				origine = handle.Size
				acc:SetAttribute("TailleOrigine", origine)
			end
			local k = ECHELLE / echelleActuelle -- facteur à appliquer depuis l'état actuel
			handle.Size = (origine :: Vector3) * ECHELLE
			local tailleOriginale = handle:FindFirstChild("OriginalSize")
			if tailleOriginale and tailleOriginale:IsA("Vector3Value") then
				tailleOriginale.Value = (origine :: Vector3) * ECHELLE
			end
			-- prise en main et points des VFX (traînées) : positions dans le repère du Handle, mises à l'échelle
			for _, enfant in handle:GetChildren() do
				if enfant:IsA("Attachment") then
					enfant.Position *= k
				end
			end
			table.insert(lignes, `{nom} {handle.Size}`)
		end
	end
	return modele:GetFullName() .. " : " .. table.concat(lignes, " ; ")
end

local resultats = {}
local dossier = ReplicatedStorage:FindFirstChild("ModelesPersonnages")
local zoro = dossier and dossier:FindFirstChild("zoro")
local apercu = workspace:FindFirstChild("Sabreur_Apercu")
if zoro and zoro:IsA("Model") then
	table.insert(resultats, agrandir(zoro))
end
if apercu and apercu:IsA("Model") then
	table.insert(resultats, agrandir(apercu))
end
return table.concat(resultats, "\n")
