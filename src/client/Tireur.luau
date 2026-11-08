--!strict
-- Tireur : projectiles de la vitrine de usopp (modèle avec l'attribut Tireur = true), appelé par Vitrine.
-- Séquence : assets/persos/usopp/anims_usopp.py (marqueurs), effets : assets/persos/usopp/vfx_usopp.luau.
-- Marqueurs :
--   Grenade "Main"            : une grenade apparaît dans la main droite ;
--   Lancer "dx,dz[,Grosse]"   : lancée en cloche vers ce point du sol (studs, repère du perso, -Z = devant), puis
--                               effet VFX « Explosion_Grenade » (ou « Explosion_GrosseGrenade ») à l'impact ;
--   Tir "dx,dz"               : graine tirée dans le sol, effet « Impact_Graine », une liane pousse ;
--   Fouet "1".."3"            : la liane frappe devant elle (effet « Impact_Fouet » au bout) ; elle fane après le 3e ;
--   Bille "dx,dy,dz"          : bille tirée de la fourche dans cette direction (repère du perso ; sinon dans l'axe de
--                               la poignée), effet « Impact_Bille » ;
--   Charge / TirCharge "dx,dy,dz" : bille qui grossit dans la fourche, puis tir (effet « Explosion_Charge »).
-- Les effets sont placés sur l'Attachment « PointImpact » du HumanoidRootPart (créé au besoin), déplacé avant chaque
-- déclenchement : les particules partent en coordonnées monde, les groupes Forge cherchent le sol sous ce point.
-- Élastique : deux Beam locaux des bouts de la fourche à la main gauche (Tireur.Init), affichés quand le lance-pierre
-- est en main et la main gauche près du visage (traction), cachés après chaque tir (claquement).
-- Côté client (comme Vitrine) : projectiles et liane sont des pièces locales, ancrées, sans collision.

local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Tireur = {}

export type Declencheur = (modele: Model, nom: string) -> ()

Tireur.MARQUEURS = { "Grenade", "Lancer", "Tir", "Fouet", "Bille", "Charge", "TirCharge" }

local TAG_VITRINE = "PersonnageVitrine"
local TAG_IGNORE = "ForgeIgnore"
local DISTANCE_MAX = 160
local FOURCHE_Y = 2.6 -- centre de la fourche, repère de la poignée du lance-pierre
local VOL_GRENADE = 0.55
local MECHE = 0.18 -- délai entre l'arrivée au sol et l'explosion
local VITESSE_BILLE = 140
local VITESSE_CHARGE = 90
local PORTEE = 30

-- élastique (repère de la poignée : bouts des branches de la fourche vers x = ±0,36, y = 3,4)
local BOUTS_FOURCHE = { Vector3.new(-0.38, 3.3, 0), Vector3.new(0.38, 3.3, 0) }
local TRACTION_TETE = 1.8 -- main gauche à moins de ça du centre de la tête = élastique tiré
local TRACTION_MAX = 3.4 -- et à moins de ça de la fourche
local DUREE_LACHE = 0.07 -- élastique caché après une bille de rafale (la main revient tirer 2 images plus tard)
local DUREE_LACHE_SEUL = 1.5 -- après un tir isolé (graine, tir chargé) : la main reste ouverte
local COULEUR_ELASTIQUE = Color3.fromRGB(96, 62, 44)

-- liane
local NB_SEGMENTS = 14
local LONG_SEGMENT = 0.55
local POUSSE = 0.5
local DUREE_FOUET = 0.5
local INSTANT_IMPACT_FOUET = 0.27
local FANE_APRES = 1.3 -- après le dernier fouet
local DUREE_FANE = 0.6

local COULEUR_GRENADE = Color3.fromRGB(58, 74, 50)
local COULEUR_BILLE = Color3.fromRGB(255, 214, 120)
local COULEUR_CHARGE = Color3.fromRGB(255, 132, 40)
local COULEUR_GRAINE = Color3.fromRGB(120, 210, 70)
local VERTS = { Color3.fromRGB(58, 140, 52), Color3.fromRGB(70, 158, 60), Color3.fromRGB(48, 120, 46) }

type Liane = {
	segments: { BasePart },
	feuilles: { [number]: BasePart },
	base: Vector3,
	avant: Vector3,
	cote: Vector3,
	debut: number,
	fouet: number?,
	impactFait: boolean,
	fane: number?,
	connexion: RBXScriptConnection?,
}

type Etat = {
	dossier: Folder,
	grenade: BasePart?,
	charge: BasePart?,
	liane: Liane?,
	lache: number, -- os.clock() jusqu'auquel l'élastique reste caché (après un tir)
}

local etats: { [Model]: Etat } = {}

local function etatDe(modele: Model): Etat
	local e = etats[modele]
	if e then
		return e
	end
	local dossier = Instance.new("Folder")
	dossier.Name = "Tireur_" .. modele.Name
	dossier.Parent = workspace
	dossier:AddTag(TAG_IGNORE)
	local nouveau: Etat = { dossier = dossier, lache = 0 }
	etats[modele] = nouveau
	modele.Destroying:Once(function()
		Tireur.Reinitialiser(modele)
		dossier:Destroy()
		etats[modele] = nil
	end)
	return nouveau
end

local function proche(modele: Model): boolean
	local camera = workspace.CurrentCamera
	return camera ~= nil and (camera.CFrame.Position - modele:GetPivot().Position).Magnitude <= DISTANCE_MAX
end

local function piece(etat: Etat, taille: Vector3, couleur: Color3, matiere: Enum.Material?, forme: Enum.PartType?): Part
	local p = Instance.new("Part")
	p.Size = taille
	p.Color = couleur
	p.Material = matiere or Enum.Material.SmoothPlastic
	p.Shape = forme or Enum.PartType.Block
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = etat.dossier
	return p
end

local function parametres(): RaycastParams
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	local exclus = CollectionService:GetTagged(TAG_VITRINE)
	for _, i in CollectionService:GetTagged(TAG_IGNORE) do
		table.insert(exclus, i)
	end
	params.FilterDescendantsInstances = exclus
	params.IgnoreWater = true
	return params
end

local function sol(position: Vector3): Vector3
	local r = workspace:Raycast(position + Vector3.new(0, 6, 0), Vector3.new(0, -30, 0), parametres())
	return if r then r.Position else position
end

-- point du sol à (dx, dz) studs du perso, dans son repère
local function pointSol(modele: Model, texte: string): (Vector3, boolean)
	local dx, dz, extra = string.match(texte, "^%s*([%-%d%.]+)%s*,%s*([%-%d%.]+)%s*,?%s*(%a*)")
	local pivot = modele:GetPivot()
	local p = pivot * Vector3.new(tonumber(dx) or 0, 0, tonumber(dz) or -8)
	return sol(Vector3.new(p.X, pivot.Position.Y, p.Z)), extra == "Grosse"
end

local function regardAPlat(modele: Model): Vector3
	local v = modele:GetPivot().LookVector
	local plat = Vector3.new(v.X, 0, v.Z)
	return if plat.Magnitude > 1e-3 then plat.Unit else Vector3.new(0, 0, -1)
end

-- place PointImpact puis déclenche l'effet VFX.<nom>
local function effetEn(modele: Model, declencher: Declencheur, nom: string, position: Vector3)
	local hrp = modele:FindFirstChild("HumanoidRootPart")
	if not (hrp and hrp:IsA("BasePart")) then
		return
	end
	local point = hrp:FindFirstChild("PointImpact")
	if not point then
		local a = Instance.new("Attachment")
		a.Name = "PointImpact"
		a.Parent = hrp
		point = a
	end
	if point and point:IsA("Attachment") then
		local regard = regardAPlat(modele)
		point.WorldCFrame = CFrame.lookAt(position, position + regard)
	end
	declencher(modele, nom)
end

local function flash(etat: Etat, position: Vector3, couleur: Color3, de: number, a: number, duree: number)
	local b = piece(etat, Vector3.one * de, couleur, Enum.Material.Neon, Enum.PartType.Ball)
	b.CFrame = CFrame.new(position)
	b.Transparency = 0.1
	TweenService:Create(b, TweenInfo.new(duree, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
		Size = Vector3.one * a,
		Transparency = 1,
	}):Play()
	task.delay(duree + 0.05, function()
		b:Destroy()
	end)
end

local function poignee(modele: Model): BasePart?
	local acc = modele:FindFirstChild("Acc_LancePierre_Main")
	local h = acc and acc:FindFirstChild("Handle")
	return if h and h:IsA("BasePart") then h else nil
end

-- direction « dx,dy,dz » du marqueur (repère du perso), sinon nil
local function directionMarqueur(modele: Model, texte: string): Vector3?
	local x, y, z = string.match(texte, "^%s*([%-%d%.]+)%s*,%s*([%-%d%.]+)%s*,%s*([%-%d%.]+)")
	local v = Vector3.new(tonumber(x) or 0, tonumber(y) or 0, tonumber(z) or 0)
	if v.Magnitude < 1e-3 then
		return nil
	end
	return modele:GetPivot():VectorToWorldSpace(v.Unit)
end

local function fourche(modele: Model): (Vector3?, Vector3?)
	local h = poignee(modele)
	if not h then
		return nil
	end
	return (h.CFrame * CFrame.new(0, FOURCHE_Y, 0)).Position, h.CFrame.LookVector
end

-- déplace p de a vers b en cloche (hauteur h) en `duree` s, en tournant ; puis fin()
local function voler(p: BasePart, a: Vector3, b: Vector3, duree: number, h: number, fin: () -> ())
	local t = 0
	local cx: RBXScriptConnection
	cx = RunService.Heartbeat:Connect(function(dt)
		if not p.Parent then
			cx:Disconnect()
			return
		end
		t = math.min(t + dt, duree)
		local k = t / duree
		p.CFrame = CFrame.new(a:Lerp(b, k) + Vector3.new(0, 4 * h * k * (1 - k), 0)) * CFrame.Angles(k * 9, 0, k * 5)
		if t >= duree then
			cx:Disconnect()
			fin()
		end
	end)
end

-- projectile en ligne droite, s'arrête au premier obstacle ou à PORTEE studs ; fin(point d'arrivée)
local function filer(p: BasePart, depart: Vector3, direction: Vector3, vitesse: number, fin: (Vector3) -> ())
	local position = depart
	local parcouru = 0
	local params = parametres()
	local cx: RBXScriptConnection
	cx = RunService.Heartbeat:Connect(function(dt)
		if not p.Parent then
			cx:Disconnect()
			return
		end
		local pas = direction * vitesse * dt
		local r = workspace:Raycast(position, pas, params)
		if r or parcouru >= PORTEE then
			cx:Disconnect()
			local arrivee = if r then r.Position else position
			p.CFrame = CFrame.new(arrivee)
			fin(arrivee)
			return
		end
		position += pas
		parcouru += pas.Magnitude
		p.CFrame = CFrame.lookAt(position, position + direction)
	end)
end

---------------------------------------------------------------- grenades

local function sortirGrenade(modele: Model, etat: Etat)
	if etat.grenade then
		etat.grenade:Destroy()
	end
	local main = modele:FindFirstChild("RightHand")
	if not (main and main:IsA("BasePart")) then
		return
	end
	local g = piece(etat, Vector3.one * 0.62, COULEUR_GRENADE, Enum.Material.Metal, Enum.PartType.Ball)
	local meche = piece(etat, Vector3.new(0.08, 0.22, 0.08), Color3.fromRGB(255, 190, 90), Enum.Material.Neon)
	meche.Parent = g
	local lumiere = Instance.new("PointLight")
	lumiere.Color = Color3.fromRGB(255, 170, 70)
	lumiere.Range = 5
	lumiere.Brightness = 2
	lumiere.Parent = g
	etat.grenade = g
	local cx: RBXScriptConnection
	cx = RunService.RenderStepped:Connect(function()
		if not g.Parent then
			cx:Disconnect()
			return
		end
		local cadre = if etat.grenade == g then main.CFrame * CFrame.new(0, -0.38, -0.05) else g.CFrame
		g.CFrame = cadre
		meche.CFrame = cadre * CFrame.new(0, 0.38, 0)
		meche.Transparency = if (os.clock() * 14) % 2 < 1 then 0 else 0.6
	end)
end

local function lancerGrenade(modele: Model, etat: Etat, declencher: Declencheur, valeur: string)
	local g = etat.grenade
	if not g then
		return
	end
	etat.grenade = nil
	local impact, grosse = pointSol(modele, valeur)
	voler(g, g.Position, impact + Vector3.new(0, 0.31, 0), VOL_GRENADE, 5, function()
		task.delay(MECHE, function()
			g:Destroy()
			flash(etat, impact + Vector3.new(0, 1, 0), Color3.fromRGB(255, 196, 92), 1.5, if grosse then 13 else 9, 0.32)
			effetEn(modele, declencher, if grosse then "Explosion_GrosseGrenade" else "Explosion_Grenade", impact)
		end)
	end)
end

---------------------------------------------------------------- liane

-- (angle de départ, courbure totale) en degrés, par rapport à la verticale, vers l'avant
local function formeLiane(l: Liane, maintenant: number): (number, number)
	local t = maintenant - l.debut
	local base = -6 + 5 * math.sin(t * 2.3)
	local courbe = 40 + 12 * math.sin(t * 1.7 + 1)
	local tf = l.fouet
	if tf then
		local u = maintenant - tf
		if u < DUREE_FOUET then
			-- armer (en arrière), frapper (vers l'avant et le sol), revenir
			local cles = { { 0, base, courbe }, { 0.14, -38, -70 }, { 0.27, 62, 150 }, { DUREE_FOUET, base, courbe } }
			for i = 1, #cles - 1 do
				local a, b = cles[i], cles[i + 1]
				if u < b[1] then
					local k = (u - a[1]) / (b[1] - a[1])
					local style = if i == 2 then Enum.EasingStyle.Quad else Enum.EasingStyle.Sine
					local direction = if i == 2 then Enum.EasingDirection.In else Enum.EasingDirection.Out
					k = TweenService:GetValue(k, style, direction)
					return a[2] + (b[2] - a[2]) * k, a[3] + (b[3] - a[3]) * k
				end
			end
		end
	end
	return base, courbe
end

local function poserLiane(l: Liane, maintenant: number): Vector3
	local pousse = math.clamp((maintenant - l.debut) / POUSSE, 0, 1)
	pousse = TweenService:GetValue(pousse, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
	if l.fane then
		pousse *= 1 - math.clamp((maintenant - l.fane) / DUREE_FANE, 0, 1)
	end
	local a0, courbe = formeLiane(l, maintenant)
	local position = l.base
	local visibles = pousse * NB_SEGMENTS
	local ondule = math.sin((maintenant - l.debut) * 3.1)
	for i, s in l.segments do
		local part = math.clamp(visibles - (i - 1), 0, 1)
		local angle = math.rad(a0 + courbe * (i - 0.5) / NB_SEGMENTS)
		local lateral = 0.12 * ondule * (i / NB_SEGMENTS)
		local dir = (Vector3.yAxis * math.cos(angle) + l.avant * math.sin(angle) + l.cote * lateral).Unit
		local v = dir * LONG_SEGMENT * part
		if part <= 0 then
			s.Transparency = 1
		else
			s.Transparency = 0
			local largeur = (0.62 - 0.4 * (i / NB_SEGMENTS)) * math.max(part, 0.3)
			s.Size = Vector3.new(LONG_SEGMENT * part + 0.12, largeur, largeur)
			-- cylindre : axe X le long du segment
			s.CFrame = CFrame.lookAt(position + v / 2, position + v) * CFrame.Angles(0, math.rad(90), 0)
		end
		local feuille = l.feuilles[i]
		if feuille then
			feuille.Transparency = s.Transparency
			local cote = if i % 2 == 0 then 1 else -1
			feuille.CFrame = CFrame.lookAt(position + v, position + v + dir) * CFrame.new(cote * 0.28, 0, 0) * CFrame.Angles(0, 0, math.rad(cote * 35))
		end
		position += v
	end
	return position
end

local function detruireLiane(etat: Etat)
	local l = etat.liane
	if not l then
		return
	end
	etat.liane = nil
	if l.connexion then
		l.connexion:Disconnect()
	end
	for _, s in l.segments do
		s:Destroy()
	end
	for _, f in l.feuilles do
		f:Destroy()
	end
end

local function pousserLiane(modele: Model, etat: Etat, declencher: Declencheur, base: Vector3)
	detruireLiane(etat)
	local avant = regardAPlat(modele)
	local l: Liane = {
		segments = {},
		feuilles = {},
		base = base,
		avant = avant,
		cote = avant:Cross(Vector3.yAxis),
		debut = os.clock(),
		impactFait = true,
	}
	for i = 1, NB_SEGMENTS do
		local s = piece(etat, Vector3.new(LONG_SEGMENT, 0.5, 0.5), VERTS[i % 3 + 1], Enum.Material.Grass, Enum.PartType.Cylinder)
		s.Transparency = 1
		table.insert(l.segments, s)
		if i % 3 == 0 and i < NB_SEGMENTS then
			local f = piece(etat, Vector3.new(0.5, 0.05, 0.32), Color3.fromRGB(96, 186, 72), Enum.Material.SmoothPlastic)
			f.Transparency = 1
			l.feuilles[i] = f
		end
	end
	etat.liane = l
	l.connexion = RunService.Heartbeat:Connect(function()
		local maintenant = os.clock()
		if l.fane and maintenant - l.fane > DUREE_FANE then
			detruireLiane(etat)
			return
		end
		local bout = poserLiane(l, maintenant)
		local tf = l.fouet
		if tf and not l.impactFait and maintenant - tf >= INSTANT_IMPACT_FOUET then
			l.impactFait = true
			effetEn(modele, declencher, "Impact_Fouet", sol(bout))
		end
	end)
end

local function tirerGraine(modele: Model, etat: Etat, declencher: Declencheur, valeur: string)
	local depart = fourche(modele)
	if not depart then
		return
	end
	local cible = pointSol(modele, valeur)
	local graine = piece(etat, Vector3.one * 0.42, COULEUR_GRAINE, Enum.Material.Neon, Enum.PartType.Ball)
	flash(etat, depart, Color3.fromRGB(220, 255, 170), 0.4, 1.6, 0.15)
	voler(graine, depart, cible, 0.22, 0.2, function()
		graine:Destroy()
		effetEn(modele, declencher, "Impact_Graine", cible)
		pousserLiane(modele, etat, declencher, cible)
	end)
end

local function fouet(etat: Etat, valeur: string)
	local l = etat.liane
	if not l then
		return
	end
	l.fouet = os.clock()
	l.impactFait = false
	if valeur == "3" then
		task.delay(DUREE_FOUET + FANE_APRES, function()
			if etat.liane == l then
				l.fane = os.clock()
			end
		end)
	end
end

---------------------------------------------------------------- billes

local function tirerBille(modele: Model, etat: Etat, declencher: Declencheur, valeur: string)
	local depart, axe = fourche(modele)
	local direction = directionMarqueur(modele, valeur) or axe
	if not (depart and direction) then
		return
	end
	flash(etat, depart, Color3.fromRGB(255, 244, 200), 0.3, 1.3, 0.1)
	local b = piece(etat, Vector3.new(0.28, 0.28, 1.1), COULEUR_BILLE, Enum.Material.Neon)
	filer(b, depart, direction, VITESSE_BILLE, function(arrivee)
		b:Destroy()
		flash(etat, arrivee, Color3.fromRGB(255, 236, 170), 0.3, 1.8, 0.18)
		effetEn(modele, declencher, "Impact_Bille", arrivee)
	end)
end

local function charger(modele: Model, etat: Etat)
	if etat.charge then
		etat.charge:Destroy()
	end
	local c = piece(etat, Vector3.one * 0.3, COULEUR_CHARGE, Enum.Material.Neon, Enum.PartType.Ball)
	local lumiere = Instance.new("PointLight")
	lumiere.Color = COULEUR_CHARGE
	lumiere.Range = 10
	lumiere.Brightness = 3
	lumiere.Parent = c
	etat.charge = c
	local t0 = os.clock()
	local cx: RBXScriptConnection
	cx = RunService.RenderStepped:Connect(function()
		if not c.Parent or etat.charge ~= c then
			cx:Disconnect()
			return
		end
		-- dans la poche de l'élastique, tenue par la main gauche (sinon dans la fourche)
		local main = modele:FindFirstChild("LeftHand")
		local depart = if main and main:IsA("BasePart") then main.Position else fourche(modele)
		if depart then
			local k = math.clamp((os.clock() - t0) / 0.7, 0, 1)
			c.Size = Vector3.one * (0.3 + 1.0 * k + 0.08 * math.sin(os.clock() * 55))
			c.CFrame = CFrame.new(depart)
		end
	end)
end

local function tirCharge(modele: Model, etat: Etat, declencher: Declencheur, valeur: string)
	local c = etat.charge
	etat.charge = nil
	local depart, axe = fourche(modele)
	local direction = directionMarqueur(modele, valeur) or axe
	if not (c and depart and direction) then
		if c then
			c:Destroy()
		end
		return
	end
	flash(etat, depart, Color3.fromRGB(255, 200, 120), 0.8, 4, 0.2)
	filer(c, depart, direction, VITESSE_CHARGE, function(arrivee)
		c:Destroy()
		flash(etat, arrivee + Vector3.new(0, 1, 0), Color3.fromRGB(255, 150, 60), 2, 12, 0.4)
		effetEn(modele, declencher, "Explosion_Charge", sol(arrivee))
	end)
end

---------------------------------------------------------------- entrée

function Tireur.Marqueur(modele: Model, marqueur: string, valeur: string, declencher: Declencheur)
	if modele:GetAttribute("Tireur") ~= true or not proche(modele) then
		return
	end
	local etat = etatDe(modele)
	if marqueur == "Bille" then
		etat.lache = os.clock() + DUREE_LACHE
	elseif marqueur == "Tir" or marqueur == "TirCharge" then
		etat.lache = os.clock() + DUREE_LACHE_SEUL
	end
	if marqueur == "Grenade" then
		sortirGrenade(modele, etat)
	elseif marqueur == "Lancer" then
		lancerGrenade(modele, etat, declencher, valeur)
	elseif marqueur == "Tir" then
		tirerGraine(modele, etat, declencher, valeur)
	elseif marqueur == "Fouet" then
		fouet(etat, valeur)
	elseif marqueur == "Bille" then
		tirerBille(modele, etat, declencher, valeur)
	elseif marqueur == "Charge" then
		charger(modele, etat)
	elseif marqueur == "TirCharge" then
		tirCharge(modele, etat, declencher, valeur)
	end
end

-- Début de cycle : enlève ce qui reste du cycle précédent (grenade en main, liane, charge)
function Tireur.Reinitialiser(modele: Model)
	local etat = etats[modele]
	if not etat then
		return
	end
	detruireLiane(etat)
	if etat.grenade then
		etat.grenade:Destroy()
		etat.grenade = nil
	end
	if etat.charge then
		etat.charge:Destroy()
		etat.charge = nil
	end
end

---------------------------------------------------------------- élastique

type Elastique = { faisceaux: { Beam } }
local elastiques: { [Model]: Elastique } = {}

local function attache(parent: BasePart, nom: string, position: Vector3): Attachment
	local a = parent:FindFirstChild(nom)
	if a and a:IsA("Attachment") then
		return a
	end
	local nouvelle = Instance.new("Attachment")
	nouvelle.Name = nom
	nouvelle.Position = position
	nouvelle.Parent = parent
	return nouvelle
end

local function creerElastique(modele: Model): Elastique?
	local h = poignee(modele)
	local main = modele:FindFirstChild("LeftHand")
	if not (h and main and main:IsA("BasePart")) then
		return nil
	end
	local poche = attache(main, "Tireur_Poche", Vector3.new(0, -0.1, 0))
	local e: Elastique = { faisceaux = {} }
	for i, bout in BOUTS_FOURCHE do
		local b = Instance.new("Beam")
		b.Name = `Tireur_Elastique{i}`
		b.Attachment0 = attache(h, `Tireur_Bout{i}`, bout)
		b.Attachment1 = poche
		b.Color = ColorSequence.new(COULEUR_ELASTIQUE)
		b.Width0 = 0.12
		b.Width1 = 0.1
		b.FaceCamera = true
		b.Segments = 1
		b.LightInfluence = 1
		b.Transparency = NumberSequence.new(0)
		b.Enabled = false
		b.Parent = h
		table.insert(e.faisceaux, b)
	end
	elastiques[modele] = e
	modele.Destroying:Once(function()
		elastiques[modele] = nil
	end)
	return e
end

local function majElastique(modele: Model)
	local e = elastiques[modele] or creerElastique(modele)
	if not e then
		return
	end
	local h = poignee(modele)
	local main = modele:FindFirstChild("LeftHand")
	local tete = modele:FindFirstChild("Head")
	local etat = etats[modele]
	local tendu = false
	if h and h.Transparency < 0.5 and main and main:IsA("BasePart") and tete and tete:IsA("BasePart") then
		local centre = (h.CFrame * CFrame.new(0, FOURCHE_Y, 0)).Position
		tendu = (main.Position - tete.Position).Magnitude < TRACTION_TETE
			and (main.Position - centre).Magnitude < TRACTION_MAX
			and not (etat and os.clock() < etat.lache)
	end
	for _, b in e.faisceaux do
		b.Enabled = tendu
	end
end

-- Élastique de chaque vitrine « Tireur » proche, à chaque image
function Tireur.Init()
	RunService.RenderStepped:Connect(function()
		for _, modele in CollectionService:GetTagged(TAG_VITRINE) do
			if modele:IsA("Model") and modele:GetAttribute("Tireur") == true and proche(modele) then
				majElastique(modele)
			end
		end
	end)
end

return Tireur
