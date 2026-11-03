--!strict
-- VFX v2 de la séquence du sabreur sur zoro (03/11 : « plus stylé et énervé », aura façon image de référence,
-- coups avec impact, vitesse et puissance). Relançable (MCP, mode édition).
-- Crée dans <modèle>.VFX des dossiers nommés d'après les marqueurs de gameplay de l'animation, que
-- src/client/Vitrine.luau déclenche directement (« <Marqueur>_<Valeur> ») :
--   Aura_Debut (Duree)      flammes vertes et rouges, éclairs sur les 3 lames, œil rouge, braises, fumée sombre
--   Fin_Aura (Eteindre)     coupe l'aura
--   Explosion_Aura (Burst)  double onde, éclairs, lignes d'impact, gerbe de braises, flash, secousse
--   Esquive_* (Burst)       image rémanente verte, poussière, traits de vitesse
--   Impact_Contre1..3       arc de coupe, étoile, onde, lignes, éclats, traits de vitesse, flash, secousse, hit-stop
--   Impact_Sol              grosse onde, poussière, débris, éclairs, secousse forte, hit-stop long
--   Impact_CoupeX           deux arcs croisés, éclairs verts et rouges, secousse, hit-stop long
--   Sabreur_Trail (Duree)   traînées des 3 lames (marqueur « VFX Sabreur_Trail » au début du combat)
-- Textures : intégrées (rbxasset://) ou déjà en ligne (zoro, luffy, nami). Aucun envoi.
-- Aussi : sabre en bouche retourné une fois (lame vers la droite du perso, convention du handoff).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local VERT = Color3.fromRGB(70, 255, 130)
local VERT_CLAIR = Color3.fromRGB(190, 255, 210)
local VERT_FLAMME = Color3.fromRGB(40, 220, 100)
local ROUGE = Color3.fromRGB(255, 40, 30)
local BRAISE = Color3.fromRGB(255, 120, 40)
local FUMEE = Color3.fromRGB(18, 22, 20)
local BLANC = Color3.new(1, 1, 1)
local TERRE = Color3.fromRGB(120, 95, 70)
local POUSSIERE_COULEUR = Color3.fromRGB(235, 222, 196)

local TEX_ETINCELLE = "rbxasset://textures/particles/sparkles_main.dds"
local TEX_FEU = "rbxasset://textures/particles/fire_main.dds"
local TEX_FUMEE = "rbxasset://textures/particles/smoke_main.dds"
local TEX_ANNEAU = "rbxassetid://101774142734315" -- zoro / nami
local TEX_ARC = "rbxassetid://100815645874876" -- zoro (entailles)
local TEX_POUSSIERE = "rbxassetid://70434048288435" -- luffy
local TEX_ECLAIRS = "rbxassetid://88432637509015" -- nami (claire, se teinte ; celle de luffy est sombre)
local TEX_ETOILE_IMPACT = "rbxassetid://112249090477155" -- luffy
local TEX_ANNEAU_IMPACT = "rbxassetid://93783833153831" -- luffy
local TEX_TRAITS = "rbxassetid://97795166368994" -- luffy (traits de vitesse)
local TEX_LIGNES_IMPACT = "rbxassetid://135983583011818" -- luffy (lignes radiales façon manga)

-- dossiers VFX créés par cette version ou les précédentes (supprimés puis recréés)
local ANCIENS_DOSSIERS = {
	"Explosion_Aura",
	"Impact_Sol",
	"Impact_CoupeX",
	"Impact_Contre1",
	"Impact_Contre2",
	"Impact_Contre3",
	"Aura_Debut",
	"Fin_Aura",
	"Esquive_Gauche",
	"Esquive_Droite",
	"Esquive_Arriere",
}

local function seq(a: number, b: number): NumberSequence
	return NumberSequence.new({ NumberSequenceKeypoint.new(0, a), NumberSequenceKeypoint.new(1, b) })
end

local function fondu(debut: number): NumberSequence
	return NumberSequence.new({
		NumberSequenceKeypoint.new(0, debut),
		NumberSequenceKeypoint.new(0.7, debut + (1 - debut) * 0.3),
		NumberSequenceKeypoint.new(1, 1),
	})
end

local function degrade(a: Color3, b: Color3): ColorSequence
	return ColorSequence.new(a, b)
end

type Reglages = { [string]: any }

local function emetteur(parent: Instance, nom: string, r: Reglages): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Name = nom
	e.Enabled = false
	e.Texture = r.Texture or TEX_ETINCELLE
	local couleur = r.Couleur or VERT
	e.Color = if typeof(couleur) == "ColorSequence" then couleur else ColorSequence.new(couleur)
	e.LightEmission = r.LightEmission or 1
	e.LightInfluence = 0
	e.Brightness = r.Eclat or 1
	e.Size = r.Taille or seq(0.5, 0)
	e.Transparency = r.Transparence or fondu(0)
	e.Lifetime = r.Duree or NumberRange.new(0.5, 0.8)
	e.Speed = r.Vitesse or NumberRange.new(0)
	e.SpreadAngle = r.Ecart or Vector2.new(180, 180)
	e.Acceleration = r.Acceleration or Vector3.zero
	e.Drag = r.Frein or 0
	e.Rate = r.Debit or 20
	e.Rotation = r.Angle or NumberRange.new(0, 360)
	e.RotSpeed = r.Rotation or NumberRange.new(0)
	e.Orientation = r.Orientation or Enum.ParticleOrientation.FacingCamera
	e.EmissionDirection = r.Direction or Enum.NormalId.Top
	e.LockedToPart = r.Accroche or false
	e.ZOffset = r.ZOffset or 0
	if r.Quantite then
		e:SetAttribute("Quantite", r.Quantite)
	end
	e.Parent = parent
	return e
end

local function attache(part: BasePart, nom: string, position: Vector3): Attachment
	local a = Instance.new("Attachment")
	a.Name = nom
	a.Position = position
	a.Parent = part
	return a
end

local function lumiere(parent: Instance, nom: string, couleur: Color3, eclat: number, portee: number): PointLight
	local l = Instance.new("PointLight")
	l.Name = nom
	l.Color = couleur
	l.Brightness = eclat
	l.Range = portee
	l.Shadows = false
	l.Enabled = false
	l.Parent = parent
	return l
end

local function dossier(vfx: Folder, nom: string, attributs: { [string]: any }, effets: { Instance }): ()
	local d = Instance.new("Folder")
	d.Name = nom
	for cle, valeur in attributs do
		d:SetAttribute(cle, valeur)
	end
	for i, effet in effets do
		local lien = Instance.new("ObjectValue")
		lien.Name = `Effet{i}`
		lien.Value = effet
		lien.Parent = d
	end
	d.Parent = vfx
end

local function nettoyer(modele: Model, vfx: Folder)
	for _, d in vfx:GetChildren() do
		if string.sub(d.Name, 1, 8) == "Sabreur_" or table.find(ANCIENS_DOSSIERS, d.Name) then
			d:Destroy()
		end
	end
	for _, d in modele:GetDescendants() do
		if string.sub(d.Name, 1, 12) == "VFX_Sabreur_" then
			d:Destroy()
		end
	end
end

local function retournerSabreBouche(modele: Model)
	local acc = modele:FindFirstChild("Acc_Sabre_Bouche")
	local handle = acc and acc:FindFirstChild("Handle")
	local att = handle and handle:FindFirstChild("FaceFrontAttachment")
	if not (acc and att and att:IsA("Attachment")) or acc:GetAttribute("RetournePourSabreur") then
		return
	end
	att.CFrame = att.CFrame * CFrame.Angles(0, math.pi, 0)
	acc:SetAttribute("RetournePourSabreur", true)
end

local function lames(modele: Model): { BasePart }
	local liste = {}
	for _, nom in { "Acc_Sabre_Droit", "Acc_Sabre_Gauche", "Acc_Sabre_Bouche" } do
		local acc = modele:FindFirstChild(nom)
		local handle = acc and acc:FindFirstChild("Handle")
		if handle and handle:IsA("BasePart") then
			table.insert(liste, handle)
		end
	end
	return liste
end

-- Traînée blanc → vert, vive et courte ; réutilise VFX_Trail des sabres en main, en crée une sur le sabre en bouche.
local function styliserTrainee(trail: Trail)
	trail.Color = degrade(BLANC, VERT)
	trail.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.05),
		NumberSequenceKeypoint.new(0.5, 0.45),
		NumberSequenceKeypoint.new(1, 1),
	})
	trail.Lifetime = 0.18
	trail.LightEmission = 1
	trail.LightInfluence = 0
	trail.FaceCamera = true
	trail.MinLength = 0.05
	trail.Enabled = false
end

local function trainees(modele: Model): { Instance }
	local liste: { Instance } = {}
	for _, nom in { "Acc_Sabre_Droit", "Acc_Sabre_Gauche" } do
		local acc = modele:FindFirstChild(nom)
		local trail = acc and acc:FindFirstChild("VFX_Trail", true)
		if trail and trail:IsA("Trail") then
			styliserTrainee(trail)
			table.insert(liste, trail)
		end
	end
	local bouche = modele:FindFirstChild("Acc_Sabre_Bouche")
	local handle = bouche and bouche:FindFirstChild("Handle")
	if handle and handle:IsA("BasePart") then
		-- lame vers -X du Handle (prise en bouche côté +X, voir retournerSabreBouche)
		local demi = handle.Size.X / 2
		local base = attache(handle, "VFX_Sabreur_LameBase", Vector3.new(demi * 0.3, 0, 0))
		local pointe = attache(handle, "VFX_Sabreur_LamePointe", Vector3.new(-demi * 0.95, 0, 0))
		local trail = Instance.new("Trail")
		trail.Name = "VFX_Sabreur_Trail"
		trail.Attachment0 = base
		trail.Attachment1 = pointe
		styliserTrainee(trail)
		trail.Parent = handle
		table.insert(liste, trail)
	end
	return liste
end

local function construire(modele: Model): string
	local vfx = modele:FindFirstChild("VFX") :: Folder
	local hrp = modele:FindFirstChild("HumanoidRootPart") :: BasePart
	local haut = modele:FindFirstChild("UpperTorso") :: BasePart
	local bas = modele:FindFirstChild("LowerTorso") :: BasePart
	local tete = modele:FindFirstChild("Head") :: BasePart
	local humanoid = modele:FindFirstChildOfClass("Humanoid") :: Humanoid
	assert(
		vfx and hrp and haut and bas and tete and humanoid,
		`{modele.Name} : VFX, pièces du corps ou Humanoid manquants`
	)
	nettoyer(modele, vfx)
	retournerSabreBouche(modele)

	local solY = -(hrp.Size.Y / 2 + humanoid.HipHeight) + 0.1
	local lamesListe = lames(modele)

	-- Aura ----------------------------------------------------------------------------------------------------------
	local aura: { Instance } = {}
	for _, part in { haut, bas } do
		table.insert(
			aura,
			emetteur(part, "VFX_Sabreur_FlammeVerte", {
				Texture = TEX_FEU,
				Couleur = VERT_FLAMME,
				Taille = seq(1.3, 0.1),
				Transparence = fondu(0.05),
				Duree = NumberRange.new(0.4, 0.7),
				Vitesse = NumberRange.new(1, 2),
				Acceleration = Vector3.new(0, 9, 0),
				Debit = 35,
			})
		)
	end
	table.insert(
		aura,
		emetteur(haut, "VFX_Sabreur_FlammeRouge", {
			Texture = TEX_FEU,
			Couleur = ROUGE,
			Taille = seq(0.8, 0),
			Transparence = fondu(0.2),
			Duree = NumberRange.new(0.3, 0.5),
			Vitesse = NumberRange.new(1, 2),
			Acceleration = Vector3.new(0, 8, 0),
			Debit = 12,
		})
	)
	for _, lame in lamesListe do
		table.insert(
			aura,
			emetteur(lame, "VFX_Sabreur_FoudreVerte", {
				Texture = TEX_ECLAIRS,
				Taille = seq(1.5, 1.1),
				Transparence = fondu(0),
				Duree = NumberRange.new(0.08, 0.16),
				Debit = 10,
				Accroche = true,
				Eclat = 2,
			})
		)
		table.insert(
			aura,
			emetteur(lame, "VFX_Sabreur_FoudreRouge", {
				Texture = TEX_ECLAIRS,
				Couleur = ROUGE,
				Taille = seq(1.4, 1),
				Transparence = fondu(0.1),
				Duree = NumberRange.new(0.06, 0.12),
				Debit = 7,
				Accroche = true,
				Eclat = 2,
			})
		)
		table.insert(
			aura,
			emetteur(lame, "VFX_Sabreur_FlammeLame", {
				Texture = TEX_FEU,
				Couleur = VERT_FLAMME,
				Taille = seq(0.7, 0),
				Transparence = fondu(0.05),
				Duree = NumberRange.new(0.3, 0.5),
				Vitesse = NumberRange.new(0.5, 1),
				Acceleration = Vector3.new(0, 6, 0),
				Debit = 40,
			})
		)
		table.insert(
			aura,
			emetteur(lame, "VFX_Sabreur_EtincellesLame", {
				Couleur = BRAISE,
				Taille = seq(0.25, 0),
				Duree = NumberRange.new(0.3, 0.6),
				Vitesse = NumberRange.new(2, 5),
				Acceleration = Vector3.new(0, 3, 0),
				Debit = 15,
			})
		)
	end
	-- œil rouge (œil droit, l'œil gauche est balafré) et sa traînée vers la droite du perso, comme sur l'image
	local oeil =
		attache(tete, "VFX_Sabreur_Oeil", Vector3.new(tete.Size.X * 0.17, tete.Size.Y * 0.08, -tete.Size.Z / 2 - 0.03))
	table.insert(
		aura,
		emetteur(oeil, "LueurOeil", {
			Couleur = ROUGE,
			Taille = seq(0.55, 0.25),
			Duree = NumberRange.new(0.12),
			Debit = 40,
			Accroche = true,
			Eclat = 3,
		})
	)
	table.insert(
		aura,
		emetteur(oeil, "TraineeOeil", {
			Texture = TEX_TRAITS,
			Couleur = ROUGE,
			Orientation = Enum.ParticleOrientation.VelocityParallel,
			Direction = Enum.NormalId.Right,
			Ecart = Vector2.new(8, 8),
			Taille = seq(0.3, 0.1),
			Duree = NumberRange.new(0.2),
			Vitesse = NumberRange.new(5, 8),
			Debit = 18,
			Eclat = 2,
		})
	)
	table.insert(
		aura,
		emetteur(hrp, "VFX_Sabreur_Braises", {
			Couleur = BRAISE,
			Taille = seq(0.25, 0),
			Duree = NumberRange.new(1, 1.6),
			Vitesse = NumberRange.new(3, 7),
			Acceleration = Vector3.new(0, 4, 0),
			Frein = 1,
			Debit = 30,
		})
	)
	local sol = attache(hrp, "VFX_Sabreur_Sol", Vector3.new(0, solY, 0))
	table.insert(
		aura,
		emetteur(sol, "FumeeSombre", {
			Texture = TEX_FUMEE,
			Couleur = FUMEE,
			LightEmission = 0,
			Taille = seq(2, 4),
			Transparence = fondu(0.72),
			Duree = NumberRange.new(1, 1.5),
			Vitesse = NumberRange.new(1, 3),
			Ecart = Vector2.new(90, 90),
			Acceleration = Vector3.new(0, 1.5, 0),
			Rotation = NumberRange.new(-40, 40),
			Debit = 8,
		})
	)
	-- lumières modérées : le sable clair des bases sature vite en blanc
	table.insert(aura, lumiere(haut, "VFX_Sabreur_LueurVerte", VERT, 0.8, 7))
	table.insert(aura, lumiere(tete, "VFX_Sabreur_LueurRouge", ROUGE, 0.6, 4))
	-- plein jour (vu en Play) : sur le sable clair, l'additif pur (LightEmission 1) délave l'aura jusqu'à la rendre
	-- invisible ; moins d'additif et plus de luminosité
	for _, effet in aura do
		if effet:IsA("ParticleEmitter") and effet.Name ~= "FumeeSombre" then
			effet.LightEmission = 0.35
			effet.Brightness = 3
		end
	end
	dossier(vfx, "Aura_Debut", { Mode = "Duree", Duree = 2.8 }, aura)
	dossier(vfx, "Fin_Aura", { Mode = "Eteindre", Cible = "Aura_Debut" }, {})

	-- Explosion d'aura ------------------------------------------------------------------------------------------------
	local torse = attache(haut, "VFX_Sabreur_Torse", Vector3.zero)
	dossier(vfx, "Explosion_Aura", { Mode = "Burst", DureeFlash = 0.15, Secousse = 0.7 }, {
		emetteur(sol, "AnneauVert", {
			Texture = TEX_ANNEAU,
			Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
			LightEmission = 0.5,
			Taille = seq(1, 14),
			Transparence = fondu(0.25),
			Duree = NumberRange.new(0.4),
			Vitesse = NumberRange.new(0.01),
			Ecart = Vector2.zero,
			Quantite = 1,
		}),
		emetteur(sol, "AnneauRouge", {
			Texture = TEX_ANNEAU,
			Couleur = ROUGE,
			Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
			LightEmission = 0.4,
			Taille = seq(0.5, 9),
			Transparence = fondu(0.35),
			Duree = NumberRange.new(0.5),
			Vitesse = NumberRange.new(0.01),
			Ecart = Vector2.zero,
			Quantite = 1,
		}),
		emetteur(sol, "Poussiere", {
			Texture = TEX_POUSSIERE,
			Couleur = POUSSIERE_COULEUR,
			LightEmission = 0,
			Taille = seq(1, 2.2),
			Transparence = fondu(0.45),
			Duree = NumberRange.new(0.4, 0.7),
			Vitesse = NumberRange.new(18, 28),
			Ecart = Vector2.new(90, 90),
			Frein = 5,
			Quantite = 10,
		}),
		emetteur(torse, "EclairsVerts", {
			Texture = TEX_ECLAIRS,
			Taille = seq(3.2, 2.2),
			Duree = NumberRange.new(0.12, 0.22),
			Eclat = 2,
			Quantite = 8,
		}),
		emetteur(torse, "EclairsRouges", {
			Texture = TEX_ECLAIRS,
			Couleur = ROUGE,
			Taille = seq(2.6, 1.8),
			Duree = NumberRange.new(0.1, 0.18),
			Eclat = 2,
			Quantite = 4,
		}),
		emetteur(torse, "LignesImpact", {
			Texture = TEX_LIGNES_IMPACT,
			Couleur = BLANC,
			Taille = seq(9, 12),
			Transparence = fondu(0.2),
			Duree = NumberRange.new(0.18),
			Angle = NumberRange.new(0),
			Quantite = 1,
		}),
		emetteur(torse, "Flash", {
			Couleur = VERT_CLAIR,
			Taille = seq(6, 10),
			Transparence = fondu(0.2),
			Duree = NumberRange.new(0.12),
			Quantite = 1,
		}),
		emetteur(torse, "GerbeBraises", {
			Couleur = BRAISE,
			Taille = seq(0.4, 0),
			Duree = NumberRange.new(0.5, 0.9),
			Vitesse = NumberRange.new(20, 35),
			Frein = 3,
			Quantite = 45,
		}),
		lumiere(haut, "VFX_Sabreur_FlashAura", VERT_CLAIR, 2.5, 12),
	})

	-- Esquives : image rémanente + poussière + traits de vitesse -------------------------------------------------------
	local pieds = attache(hrp, "VFX_Sabreur_Pieds", Vector3.new(0, solY, 0))
	local esquive = {
		emetteur(pieds, "Poussiere", {
			Texture = TEX_POUSSIERE,
			Couleur = POUSSIERE_COULEUR,
			LightEmission = 0,
			Taille = seq(0.8, 1.8),
			Transparence = fondu(0.3),
			Duree = NumberRange.new(0.4, 0.6),
			Vitesse = NumberRange.new(4, 8),
			Ecart = Vector2.new(90, 90),
			Frein = 4,
			Quantite = 10,
		}),
		emetteur(torse, "TraitsVitesse", {
			Texture = TEX_TRAITS,
			Couleur = BLANC,
			Orientation = Enum.ParticleOrientation.VelocityParallel,
			Taille = seq(0.35, 0.1),
			Duree = NumberRange.new(0.12),
			Vitesse = NumberRange.new(18, 26),
			Quantite = 6,
		}),
	}
	for _, sens in { "Gauche", "Droite", "Arriere" } do
		dossier(vfx, `Esquive_{sens}`, { Mode = "Burst", Fantome = VERT }, esquive)
	end

	-- Coups ----------------------------------------------------------------------------------------------------------
	local devant = attache(hrp, "VFX_Sabreur_Devant", Vector3.new(0, 0.5, -2.6))
	local coup = {
		emetteur(devant, "Arc", {
			Texture = TEX_ARC,
			Couleur = degrade(BLANC, VERT),
			Taille = seq(5.5, 7),
			Transparence = fondu(0),
			Duree = NumberRange.new(0.14),
			Angle = NumberRange.new(-60, 60),
			Eclat = 2,
			Quantite = 1,
		}),
		emetteur(devant, "ArcCoeur", {
			Texture = TEX_ARC,
			Couleur = BLANC,
			Taille = seq(4, 5),
			Duree = NumberRange.new(0.08),
			Angle = NumberRange.new(-60, 60),
			Eclat = 3,
			Quantite = 1,
		}),
		emetteur(devant, "Etoile", {
			Texture = TEX_ETOILE_IMPACT,
			Couleur = BLANC,
			LightEmission = 0.7,
			Taille = seq(1, 3.5),
			Transparence = fondu(0.2),
			Duree = NumberRange.new(0.09),
			Quantite = 1,
		}),
		emetteur(devant, "Onde", {
			Texture = TEX_ANNEAU_IMPACT,
			Taille = seq(0.5, 6),
			Duree = NumberRange.new(0.16),
			Angle = NumberRange.new(0),
			Quantite = 1,
		}),
		emetteur(devant, "Lignes", {
			Texture = TEX_LIGNES_IMPACT,
			Couleur = BLANC,
			Taille = seq(6, 7),
			Transparence = fondu(0.3),
			Duree = NumberRange.new(0.1),
			Quantite = 1,
		}),
		emetteur(devant, "Eclats", {
			Couleur = degrade(BLANC, VERT),
			Taille = seq(0.35, 0),
			Duree = NumberRange.new(0.2, 0.35),
			Vitesse = NumberRange.new(20, 34),
			Frein = 7,
			Quantite = 18,
		}),
		emetteur(devant, "Vitesse", {
			Texture = TEX_TRAITS,
			Couleur = BLANC,
			Orientation = Enum.ParticleOrientation.VelocityParallel,
			Direction = Enum.NormalId.Front,
			Ecart = Vector2.new(25, 25),
			Taille = seq(0.3, 0.1),
			Duree = NumberRange.new(0.1),
			Vitesse = NumberRange.new(35, 50),
			Quantite = 6,
		}),
		lumiere(devant, "VFX_Sabreur_FlashCoup", VERT, 2, 9),
	}
	for i = 1, 3 do
		dossier(vfx, `Impact_Contre{i}`, { Mode = "Burst", DureeFlash = 0.06, Secousse = 0.35, HitStop = 0.07 }, coup)
	end

	-- Impact au sol (retombée du saut) --------------------------------------------------------------------------------
	local devantSol = attache(hrp, "VFX_Sabreur_DevantSol", Vector3.new(0, solY, -1.2))
	dossier(vfx, "Impact_Sol", { Mode = "Burst", DureeFlash = 0.12, Secousse = 1, HitStop = 0.12 }, {
		emetteur(devantSol, "Onde", {
			Texture = TEX_ANNEAU,
			Couleur = degrade(BLANC, VERT),
			Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
			LightEmission = 0.4,
			Taille = seq(1, 16),
			Transparence = fondu(0.2),
			Duree = NumberRange.new(0.45),
			Vitesse = NumberRange.new(0.01),
			Ecart = Vector2.zero,
			Quantite = 1,
		}),
		emetteur(devantSol, "OndeRapide", {
			Texture = TEX_ANNEAU_IMPACT,
			Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
			Taille = seq(0.5, 10),
			Duree = NumberRange.new(0.3),
			Vitesse = NumberRange.new(0.01),
			Ecart = Vector2.zero,
			Quantite = 1,
		}),
		emetteur(devantSol, "Poussiere", {
			Texture = TEX_POUSSIERE,
			Couleur = POUSSIERE_COULEUR,
			LightEmission = 0,
			Taille = seq(1.2, 2.8),
			Transparence = fondu(0.4),
			Duree = NumberRange.new(0.5, 0.8),
			Vitesse = NumberRange.new(18, 28),
			Ecart = Vector2.new(90, 90),
			Frein = 5,
			Quantite = 16,
		}),
		emetteur(devantSol, "Debris", {
			Texture = TEX_POUSSIERE,
			Couleur = TERRE,
			LightEmission = 0,
			Taille = seq(0.5, 0.3),
			Duree = NumberRange.new(0.6, 0.9),
			Vitesse = NumberRange.new(18, 30),
			Ecart = Vector2.new(40, 40),
			Acceleration = Vector3.new(0, -70, 0),
			Rotation = NumberRange.new(-200, 200),
			Quantite = 18,
		}),
		emetteur(devantSol, "Eclairs", {
			Texture = TEX_ECLAIRS,
			Taille = seq(3, 2),
			Duree = NumberRange.new(0.12, 0.2),
			Eclat = 2,
			Quantite = 6,
		}),
		emetteur(devantSol, "Lignes", {
			Texture = TEX_LIGNES_IMPACT,
			Couleur = BLANC,
			Taille = seq(12, 14),
			Transparence = fondu(0.2),
			Duree = NumberRange.new(0.15),
			Quantite = 1,
		}),
		emetteur(devantSol, "Etoile", {
			Texture = TEX_ETOILE_IMPACT,
			Couleur = BLANC,
			Taille = seq(2, 7),
			Duree = NumberRange.new(0.12),
			Quantite = 1,
		}),
		lumiere(devantSol, "VFX_Sabreur_FlashSol", VERT_CLAIR, 2.5, 12),
	})

	-- Coupe en X ------------------------------------------------------------------------------------------------------
	local devantX = attache(hrp, "VFX_Sabreur_DevantX", Vector3.new(0, 0.6, -3))
	dossier(vfx, "Impact_CoupeX", { Mode = "Burst", DureeFlash = 0.12, Secousse = 0.9, HitStop = 0.12 }, {
		emetteur(devantX, "ArcX1", {
			Texture = TEX_ARC,
			Couleur = degrade(VERT_CLAIR, VERT),
			LightEmission = 0.6,
			Taille = seq(7, 8.5),
			Transparence = fondu(0.1),
			Duree = NumberRange.new(0.22),
			Angle = NumberRange.new(45),
			Quantite = 1,
		}),
		emetteur(devantX, "ArcX2", {
			Texture = TEX_ARC,
			Couleur = degrade(VERT_CLAIR, VERT),
			LightEmission = 0.6,
			Taille = seq(7, 8.5),
			Transparence = fondu(0.1),
			Duree = NumberRange.new(0.22),
			Angle = NumberRange.new(-135),
			Quantite = 1,
		}),
		emetteur(devantX, "Etoile", {
			Texture = TEX_ETOILE_IMPACT,
			Couleur = BLANC,
			LightEmission = 0.6,
			Taille = seq(1.5, 4.5),
			Transparence = fondu(0.3),
			Duree = NumberRange.new(0.1),
			Quantite = 1,
		}),
		emetteur(devantX, "Onde", {
			Texture = TEX_ANNEAU_IMPACT,
			Taille = seq(1, 9),
			Duree = NumberRange.new(0.2),
			Quantite = 1,
		}),
		emetteur(devantX, "EclairsVerts", {
			Texture = TEX_ECLAIRS,
			Taille = seq(3, 2),
			Duree = NumberRange.new(0.12, 0.2),
			Eclat = 2,
			Quantite = 5,
		}),
		emetteur(devantX, "EclairsRouges", {
			Texture = TEX_ECLAIRS,
			Couleur = ROUGE,
			Taille = seq(2.5, 1.8),
			Duree = NumberRange.new(0.1, 0.18),
			Eclat = 2,
			Quantite = 3,
		}),
		emetteur(devantX, "Lignes", {
			Texture = TEX_LIGNES_IMPACT,
			Couleur = BLANC,
			Taille = seq(9, 10),
			Transparence = fondu(0.35),
			Duree = NumberRange.new(0.15),
			Quantite = 1,
		}),
		emetteur(devantX, "Eclats", {
			Couleur = degrade(BLANC, VERT),
			Taille = seq(0.4, 0),
			Duree = NumberRange.new(0.25, 0.4),
			Vitesse = NumberRange.new(22, 38),
			Frein = 6,
			Quantite = 30,
		}),
		emetteur(devantX, "Vitesse", {
			Texture = TEX_TRAITS,
			Couleur = BLANC,
			Orientation = Enum.ParticleOrientation.VelocityParallel,
			Direction = Enum.NormalId.Front,
			Ecart = Vector2.new(30, 30),
			Taille = seq(0.35, 0.1),
			Duree = NumberRange.new(0.12),
			Vitesse = NumberRange.new(40, 55),
			Quantite = 10,
		}),
		lumiere(devantX, "VFX_Sabreur_FlashX", VERT, 1.5, 10),
	})

	-- Traînées des 3 lames pendant le combat
	local listeTrainees = trainees(modele)
	dossier(vfx, "Sabreur_Trail", { Mode = "Duree", Duree = 3.2 }, listeTrainees)

	return `{modele:GetFullName()} : {#aura} effets d'aura, {#listeTrainees} traînées`
end

local resultats = {}
local dossierModeles = ReplicatedStorage:FindFirstChild("ModelesPersonnages")
local zoro = dossierModeles and dossierModeles:FindFirstChild("zoro")
local apercu = workspace:FindFirstChild("Sabreur_Apercu")
if zoro and zoro:IsA("Model") then
	table.insert(resultats, construire(zoro))
end
if apercu and apercu:IsA("Model") then
	table.insert(resultats, construire(apercu))
end
return table.concat(resultats, "\n")
