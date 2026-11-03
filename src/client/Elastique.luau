--!strict
-- Elastique : corps en caoutchouc des personnages tagués par l'attribut `Elastique` (luffy, séquence Gear 2 → Combo).
-- Les membres étirés sont reliés par des Beam rangés dans le modèle (« Elastique_<articulation> », créés par
-- assets/persos/luffy/elastique/vfx_elastique.luau) : Roblox les dessine entre les deux points d'articulation à chaque
-- rendu, en jeu comme dans l'Éditeur d'animation, sans retard (les anciens tubes recalculés par script décrochaient).
-- Appelé par Vitrine pour chaque personnage posé qui a cet attribut :
--   - Beam : couleur et largeur suivent le membre (peau rose du Gear 2) ;
--   - marqueur Pompe : bulles qui gonflent aux chevilles et remontent dans le corps (plus de gonflement des membres :
--     les bras dépassaient du t-shirt) ; Aura Vapeur : peau rose du Gear 2 ;
--   - Reinitialiser au début de chaque cycle de vitrine (couleurs d'origine, bulles retirées).

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Elastique = {}

-- trajet d'une bulle de pompe : de la cheville au torse
local CHEMINS_BULLES = {
	{ "RightFoot", "RightLowerLeg", "RightUpperLeg", "LowerTorso", "UpperTorso" },
	{ "LeftFoot", "LeftLowerLeg", "LeftUpperLeg", "LowerTorso", "UpperTorso" },
}
local PARTIES_CORPS = {
	"Head",
	"UpperTorso",
	"LowerTorso",
	"RightUpperArm",
	"RightLowerArm",
	"RightHand",
	"LeftUpperArm",
	"LeftLowerArm",
	"LeftHand",
	"RightUpperLeg",
	"RightLowerLeg",
	"RightFoot",
	"LeftUpperLeg",
	"LeftLowerLeg",
	"LeftFoot",
}
local BULLE_GONFLE = 0.14 -- s : la bulle gonfle sur place à la cheville
local BULLE_MONTEE = 0.38 -- s : puis remonte jusqu'au torse
local BULLES_PAR_JAMBE = 2
local BULLE_DECALAGE = 0.07 -- s entre deux bulles d'une même jambe
local PEAU_GEAR2 = Color3.fromRGB(242, 133, 138) -- #f2858a
local LARGEUR = 0.8 -- largeur du Beam / plus petite dimension du membre
local ASSOMBRIR = 0.25 -- Beam non éclairé : assombri pour ressembler au membre ombré (même valeur que vfx_elastique.luau)
local DISTANCE_MAJ = 160 -- studs : au-delà, couleur et largeur des Beam ne sont plus suivies

type Lien = { beam: Beam, membre: BasePart, couleur: Color3? }
type Bulle = { part: Part, chemin: { BasePart }, debut: number, taille: number }
type Etat = {
	liens: { Lien },
	couleurs: { [BasePart]: Color3 },
	tweens: { Tween },
	bulles: { Bulle },
}

local etats: { [Model]: Etat } = {}
local enCours: { [Model]: boolean } = {}

local function arreterTweens(etat: Etat)
	for _, tween in etat.tweens do
		tween:Cancel()
	end
	table.clear(etat.tweens)
	for _, bulle in etat.bulles do
		bulle.part:Destroy()
	end
	table.clear(etat.bulles)
end

-- Position d'une bulle : avance le long des pièces du chemin (u de 0 à 1), en suivant le corps qui bouge.
local function positionSur(chemin: { BasePart }, u: number): Vector3
	local n = #chemin - 1
	local x = math.clamp(u, 0, 1) * n
	local i = math.min(math.floor(x) + 1, n)
	local f = x - (i - 1)
	return chemin[i].Position:Lerp(chemin[i + 1].Position, f)
end

-- Bulles : gonflent à la cheville (0 → taille, effet ressort), remontent, rétrécissent en entrant dans le torse.
local function animerBulles(etat: Etat, maintenant: number)
	for i = #etat.bulles, 1, -1 do
		local bulle = etat.bulles[i]
		local t = maintenant - bulle.debut
		if t < 0 then
			bulle.part.Transparency = 1
			continue
		end
		local taille, u
		if t < BULLE_GONFLE then
			local k = t / BULLE_GONFLE
			taille = bulle.taille * (1 - (1 - k) ^ 3) * (1 + 0.25 * math.sin(k * math.pi))
			u = 0
		else
			local k = (t - BULLE_GONFLE) / BULLE_MONTEE
			if k >= 1 then
				bulle.part:Destroy()
				table.remove(etat.bulles, i)
				continue
			end
			taille = bulle.taille * (1 - 0.55 * k * k)
			u = k * k * (3 - 2 * k) -- départ et arrivée en douceur
		end
		bulle.part.Transparency = 0.05
		bulle.part.Size = Vector3.one * taille
		bulle.part.Position = positionSur(bulle.chemin, u)
	end
end

-- Couleur et largeur des Beam = celles du membre (changent pendant le Gear 2).
local function mettreAJour()
	local camera = workspace.CurrentCamera
	local oeil = camera and camera.CFrame.Position
	for modele, etat in etats do
		if not modele.Parent then
			arreterTweens(etat)
			etats[modele] = nil
			continue
		end
		animerBulles(etat, time())
		if oeil and (modele:GetPivot().Position - oeil).Magnitude < DISTANCE_MAJ then
			for _, lien in etat.liens do
				local membre = lien.membre
				local largeur = math.min(membre.Size.X, membre.Size.Z) * LARGEUR
				if math.abs(lien.beam.Width0 - largeur) > 0.005 then
					lien.beam.Width0 = largeur
					lien.beam.Width1 = largeur
				end
				if lien.couleur ~= membre.Color then
					lien.couleur = membre.Color
					lien.beam.Color = ColorSequence.new(membre.Color:Lerp(Color3.new(0, 0, 0), ASSOMBRIR))
				end
			end
		end
	end
end

local function lancerBulles(modele: Model)
	local etat = etats[modele]
	if not etat then
		return
	end
	local maintenant = time() -- temps de jeu (os.clock = temps processeur, avançait trop lentement)
	for _, noms in CHEMINS_BULLES do
		local chemin: { BasePart } = {}
		for _, nom in noms do
			local part = modele:FindFirstChild(nom)
			if part and part:IsA("BasePart") then
				table.insert(chemin, part)
			end
		end
		if #chemin == #noms then
			local jambe = chemin[2]
			for k = 1, BULLES_PAR_JAMBE do
				local part = Instance.new("Part")
				part.Name = "BulleGear2"
				part.Shape = Enum.PartType.Ball
				part.Anchored = true
				part.CanCollide = false
				part.CanQuery = false
				part.CanTouch = false
				part.CastShadow = false
				part.Material = jambe.Material
				part.Color = jambe.Color:Lerp(Color3.new(1, 1, 1), 0.18) -- un peu plus clair : on voit la bulle
				part.Transparency = 1
				part.Size = Vector3.one * 0.05
				part.Position = chemin[1].Position
				part.Parent = workspace
				table.insert(etat.bulles, {
					part = part,
					chemin = chemin,
					debut = maintenant + (k - 1) * BULLE_DECALAGE,
					-- un peu plus épaisse que la jambe : elle déforme la peau
					taille = math.min(jambe.Size.X, jambe.Size.Z) * (if k == 1 then 1.6 else 1.35),
				})
			end
		end
	end
end

local function teinter(modele: Model, actif: boolean)
	local etat = etats[modele]
	if not etat then
		return
	end
	for part, couleur in etat.couleurs do
		local tween = TweenService:Create(part, TweenInfo.new(0.6, Enum.EasingStyle.Quad), {
			Color = if actif then PEAU_GEAR2 else couleur,
		})
		table.insert(etat.tweens, tween)
		tween:Play()
	end
end

-- Remet les couleurs d'origine et retire les bulles (début de cycle de vitrine, joueur arrivé en cours de séquence).
function Elastique.Reinitialiser(modele: Model)
	local etat = etats[modele]
	if not etat then
		return
	end
	arreterTweens(etat)
	for part, couleur in etat.couleurs do
		part.Color = couleur
	end
end

function Elastique.Marqueur(modele: Model, nom: string, valeur: string)
	if not etats[modele] then
		return
	end
	if nom == "Pompe" then
		lancerBulles(modele)
	elseif nom == "Aura" and valeur == "Vapeur" then
		teinter(modele, true)
	end
end

function Elastique.Suivre(modele: Model)
	if etats[modele] or enCours[modele] or modele:GetAttribute("Elastique") ~= true then
		return
	end
	enCours[modele] = true
	-- streaming : le modèle arrive avant ses pièces, les attendre (appelé dans un thread par Vitrine)
	for _, nom in PARTIES_CORPS do
		modele:WaitForChild(nom, 5)
	end
	enCours[modele] = nil
	if not modele.Parent then
		return
	end
	local etat: Etat = { liens = {}, couleurs = {}, tweens = {}, bulles = {} }
	for _, beam in modele:GetDescendants() do
		local membre = beam.Parent
		if beam:IsA("Beam") and string.sub(beam.Name, 1, 10) == "Elastique_" and membre and membre:IsA("BasePart") then
			table.insert(etat.liens, { beam = beam, membre = membre })
		end
	end
	-- peau : pièces du corps de la couleur de la tête (les vêtements sont des pièces à part)
	local tete = modele:FindFirstChild("Head")
	local peau = tete and tete:IsA("BasePart") and tete.Color
	for _, nom in PARTIES_CORPS do
		local part = modele:FindFirstChild(nom)
		if peau and part and part:IsA("BasePart") and part.Color == peau then
			etat.couleurs[part] = part.Color
		end
	end
	etats[modele] = etat
	modele.Destroying:Connect(function()
		arreterTweens(etat)
		etats[modele] = nil
	end)
end

function Elastique.Init()
	RunService.PostSimulation:Connect(mettreAJour)
end

return Elastique
