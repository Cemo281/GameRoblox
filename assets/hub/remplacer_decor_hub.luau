--!strict
-- Remplace les pièces provisoires du décor du Hub par les MeshParts de assets/hub/fbx/decor_hub.fbx.
-- À lancer dans Studio en mode édition (MCP execute_luau) après l'import manuel du FBX (Fichier → Importer 3D).
-- Les MeshParts importées (Hub_CerisierA/B, Hub_Torii, Hub_LanternePierre, Hub_Chochin) peuvent être n'importe où
-- dans Workspace ou ServerStorage : elles sont rangées dans ServerStorage.Gabarits.DecorHub.
-- État d'avant : ServerStorage.Sauvegarde_AvantMeshDecorHub (Torii, Cerisiers, Centre, Stands).

local ServerStorage = game:GetService("ServerStorage")

local SOL = 1.4 -- dessus du Plateau
local NOMS = { "Hub_CerisierA", "Hub_CerisierB", "Hub_Torii", "Hub_LanternePierre", "Hub_Chochin" }
local FEU = { bas = 3.11, hauteur = 1.15, rayon = 0.62 } -- chambre du feu de Hub_LanternePierre, depuis le sol
local HAUTEUR_FEUILLAGE = 10.5 -- hauteur visée du cerisier provisoire pour l'échelle 1

local decor = workspace:WaitForChild("Hub"):WaitForChild("Decor")
local journal = {}

-- 1. Gabarits
local gabarits = ServerStorage:FindFirstChild("Gabarits") or Instance.new("Folder")
gabarits.Name = "Gabarits"
gabarits.Parent = ServerStorage
local dossier = gabarits:FindFirstChild("DecorHub") or Instance.new("Folder")
dossier.Name = "DecorHub"
dossier.Parent = gabarits

local function chercher(nom: string): MeshPart?
	local deja = dossier:FindFirstChild(nom)
	if deja and deja:IsA("MeshPart") then
		return deja
	end
	for _, racine in { workspace, ServerStorage } do
		for _, d in racine:GetDescendants() do
			if d.Name == nom and not d:IsDescendantOf(dossier) then
				local mesh = if d:IsA("MeshPart") then d else d:FindFirstChildWhichIsA("MeshPart", true)
				if mesh then
					return mesh :: MeshPart
				end
			end
		end
	end
	return nil
end

local modeles: { [string]: MeshPart } = {}
for _, nom in NOMS do
	local mesh = chercher(nom)
	assert(mesh, "MeshPart introuvable : " .. nom .. " (importer assets/hub/fbx/decor_hub.fbx)")
	local ancienParent = mesh.Parent
	mesh.Name = nom
	mesh.Anchored = true
	mesh.CanCollide = false
	mesh.CanTouch = false
	mesh.CastShadow = true
	mesh.Material = Enum.Material.SmoothPlastic
	mesh.Color = Color3.new(1, 1, 1)
	mesh.CFrame = CFrame.new()
	mesh.Parent = dossier
	-- l'import laisse un Model vide autour des pièces
	if ancienParent and ancienParent ~= dossier and ancienParent:IsA("Model") and #ancienParent:GetChildren() == 0 then
		ancienParent:Destroy()
	end
	modeles[nom] = mesh
	table.insert(journal, string.format("%s taille %s", nom, tostring(mesh.Size)))
end
-- l'import peut laisser des Models vides (ex. decor_hub) dans Workspace
for _, c in workspace:GetChildren() do
	if c:IsA("Model") and #c:GetDescendants() == 0 then
		c:Destroy()
	end
end

-- 2. Sauvegarde
if not ServerStorage:FindFirstChild("Sauvegarde_AvantMeshDecorHub") then
	local sauvegarde = Instance.new("Folder")
	sauvegarde.Name = "Sauvegarde_AvantMeshDecorHub"
	for _, nom in { "Torii", "Cerisiers", "Centre", "Stands" } do
		decor[nom]:Clone().Parent = sauvegarde
	end
	sauvegarde.Parent = ServerStorage
end

local function poser(nom: string, cf: CFrame, echelle: number, parent: Instance, nouveauNom: string): MeshPart
	local m = modeles[nom]:Clone()
	m.Size = m.Size * echelle
	m.CFrame = cf
	m.Name = nouveauNom
	m.Parent = parent
	return m
end

local function collision(cf: CFrame, diametre: number, hauteur: number, parent: Instance)
	local p = Instance.new("Part")
	p.Name = "Collision"
	p.Shape = Enum.PartType.Cylinder
	p.Size = Vector3.new(hauteur, diametre, diametre)
	p.CFrame = cf * CFrame.Angles(0, 0, math.rad(90))
	p.Anchored = true
	p.Transparency = 1
	p.CanTouch = false
	p.CastShadow = false
	p.Parent = parent
end

-- cylindre de collision recentré sur le tronc mesuré par 4 rayons horizontaux (l'import ne garde pas l'origine Blender)
local function centrerSurTronc(mesh: MeshPart, col: BasePart)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { mesh }
	local function mesurer(c: Vector3, h: number): (Vector3, number)
		local e = {}
		for k = 0, 3 do
			local dir = Vector3.new(math.cos(k * math.pi / 2), 0, math.sin(k * math.pi / 2))
			local r = workspace:Raycast(Vector3.new(c.X, SOL + h, c.Z) + dir * 8, -dir * 16, params)
			e[k] = if r then 8 - r.Distance else 0
		end
		return Vector3.new(c.X + (e[0] - e[2]) / 2, c.Y, c.Z + (e[1] - e[3]) / 2), (e[0] + e[1] + e[2] + e[3]) / 4
	end
	local c, r = col.Position, 0
	for _ = 1, 4 do
		c, r = mesurer(c, 1.5)
	end
	local _, r2 = mesurer(c, 3)
	local diametre = math.max(1, math.min(r, r2) * 1.8)
	col.Size = Vector3.new(col.Size.X, diametre, diametre)
	col.Position = c
end

-- lanternes de pierre : pièces Lanterne* regroupées par position au sol
local function remplacerLanternes(conteneur: Instance, rotation: CFrame)
	local groupes: { { parts: { BasePart }, pos: Vector3 } } = {}
	for _, p in conteneur:GetChildren() do
		if p:IsA("BasePart") and p.Name:match("^Lanterne") and p.Name ~= "LanterneMesh" then
			local trouve
			for _, g in groupes do
				if Vector2.new(g.pos.X - p.Position.X, g.pos.Z - p.Position.Z).Magnitude < 0.5 then
					trouve = g
				end
			end
			if not trouve then
				trouve = { parts = {}, pos = p.Position }
				table.insert(groupes, trouve)
			end
			table.insert(trouve.parts, p)
		end
	end
	for _, g in groupes do
		local bas, haut = math.huge, -math.huge
		local feu: BasePart?
		for _, p in g.parts do
			bas = math.min(bas, p.Position.Y - p.Size.Y / 2)
			haut = math.max(haut, p.Position.Y + p.Size.Y / 2)
			if p.Name == "LanterneFeu" then
				feu = p
			end
		end
		local h = modeles.Hub_LanternePierre.Size.Y
		local s = (haut - bas) * 1.1 / h
		local base = Vector3.new(g.pos.X, bas, g.pos.Z)
		poser(
			"Hub_LanternePierre",
			CFrame.new(base + Vector3.new(0, h * s / 2, 0)) * rotation,
			s,
			conteneur,
			"LanterneMesh"
		)
		collision(CFrame.new(base + Vector3.new(0, 1.3 * s, 0)), 1.0 * s, 2.6 * s, conteneur)
		if feu then
			-- feu Neon (garde sa PointLight) en cylindre debout dans la chambre aux 6 montants
			feu.Shape = Enum.PartType.Cylinder
			feu.Size = Vector3.new(FEU.hauteur * s * 0.95, FEU.rayon * 2 * s * 0.95, FEU.rayon * 2 * s * 0.95)
			feu.CFrame = CFrame.new(base + Vector3.new(0, (FEU.bas + FEU.hauteur / 2) * s, 0))
				* CFrame.Angles(0, 0, math.rad(90))
			feu.CanCollide = false
			feu.Name = "LanterneFeuMesh"
		end
		for _, p in g.parts do
			if p ~= feu then
				p:Destroy()
			end
		end
	end
end

-- 3. Torii (+ leurs 2 lanternes)
for _, torii in decor.Torii:GetChildren() do
	local piliers = {}
	for _, p in torii:GetChildren() do
		if p.Name == "Pilier" then
			table.insert(piliers, p)
		end
	end
	assert(#piliers == 2, torii.Name .. " : 2 piliers attendus")
	local milieu = (piliers[1].Position + piliers[2].Position) / 2
	local rotation = (torii :: any).Kasagi.CFrame.Rotation
	local h = modeles.Hub_Torii.Size.Y
	remplacerLanternes(torii, rotation)
	for _, p in torii:GetChildren() do
		if p:IsA("BasePart") and not p.Name:match("Mesh$") and p.Name ~= "Collision" then
			if p.Name == "Pilier" then
				p.Transparency = 1 -- gardé comme collision
				p.CastShadow = false
				p.Name = "Collision"
			else
				p:Destroy()
			end
		end
	end
	poser("Hub_Torii", CFrame.new(milieu.X, SOL + h / 2, milieu.Z) * rotation, 1, torii, "ToriiMesh")
end

-- 4. Lanternes du centre
remplacerLanternes(decor.Centre, CFrame.new())

-- 5. Cerisiers (pétales gardés)
local rng = Random.new(31)
for i, arbre in decor.Cerisiers:GetChildren() do
	local mini, maxi = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, p in arbre:GetChildren() do
		if p.Name == "Feuillage" then
			mini = mini:Min(p.Position - p.Size / 2)
			maxi = maxi:Max(p.Position + p.Size / 2)
		end
	end
	local nom = if i % 2 == 0 then "Hub_CerisierB" else "Hub_CerisierA"
	local s = (maxi.Y - SOL) / HAUTEUR_FEUILLAGE
	local taille = modeles[nom].Size * s
	local cf = CFrame.new((mini.X + maxi.X) / 2, SOL + taille.Y / 2, (mini.Z + maxi.Z) / 2)
		* CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0)
	for _, p in arbre:GetChildren() do
		if p.Name == "Feuillage" or p.Name == "Tronc" or p.Name == "Branche" then
			p:Destroy()
		end
	end
	local mesh = poser(nom, cf, s, arbre, "CerisierMesh")
	collision(CFrame.new(cf.X, SOL + 2.5 * s, cf.Z), 1.6 * s, 5 * s, arbre)
	local col = arbre:FindFirstChild("Collision") :: BasePart
	centrerSurTronc(mesh, col)
	-- grand cerisier : tronc au centre de son banc circulaire (8 BancRond)
	if arbre.Name == "GrandCerisier" then
		local somme, nb = Vector3.zero, 0
		for _, p in decor.Bancs:GetDescendants() do
			if
				p:IsA("BasePart")
				and p.Name == "BancRond"
				and Vector2.new(p.Position.X - col.Position.X, p.Position.Z - col.Position.Z).Magnitude < 10
			then
				somme += p.Position
				nb += 1
			end
		end
		if nb > 0 then
			local delta = Vector3.new(somme.X / nb - col.Position.X, 0, somme.Z / nb - col.Position.Z)
			for _, p in arbre:GetChildren() do
				if p:IsA("BasePart") then
					p.CFrame += delta
				end
			end
		end
	end
end

-- 6. Chochin des stands : corps côtelé en Neon de la couleur du stand, bagues recollées
for _, stand in decor.Stands:GetChildren() do
	for _, boule in stand:GetChildren() do
		if boule.Name == "Chochin" and boule:IsA("BasePart") then
			local s = boule.Size.Y / modeles.Hub_Chochin.Size.Y * 1.05
			local m = poser("Hub_Chochin", boule.CFrame, s, stand, "ChochinMesh")
			m.Material = Enum.Material.Neon
			m.Color = boule.Color
			m.TextureID = "" -- sinon la texture papier blanche masque la couleur Neon
			m.CastShadow = false
			for _, c in boule:GetChildren() do
				if c:IsA("Light") then
					c.Parent = m
				end
			end
			local demi = m.Size.Y / 2
			for _, bague in stand:GetChildren() do
				if bague.Name == "ChochinBague" and bague:IsA("BasePart") then
					local d = bague.Position - boule.Position
					if Vector2.new(d.X, d.Z).Magnitude < 0.5 and math.abs(d.Y) < 2 then
						local signe = if d.Y > 0 then 1 else -1
						bague.CFrame = bague.CFrame
							+ Vector3.new(0, boule.Position.Y + signe * (demi + 0.1) - bague.Position.Y, 0)
					end
				end
			end
			boule:Destroy()
		end
	end
end

local n = 0
for _, d in decor:GetDescendants() do
	if d:IsA("BasePart") then
		n += 1
	end
end
table.insert(journal, "pièces dans Hub.Decor : " .. n)
return table.concat(journal, "\n")
