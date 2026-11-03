--!strict
-- VFX v2 de la séquence « combattant élastique » de luffy (Gear 2 → Combo), 04/11 : « bien plus épique », impact et
-- vitesse des coups, recharge stylée, fumée de la transformation, tempos variés. Relançable (MCP, mode édition :
-- passer par un ModuleScript temporaire, le script renvoie un bilan).
-- Dossiers <modèle>.VFX nommés d'après les marqueurs de l'animation, déclenchés par src/client/Vitrine.luau
-- (« <Marqueur>_<Valeur> », ou marqueur « VFX <Nom> ») ; bulles des pompes et peau rose : src/client/Elastique.luau.
-- Membres élastiques : Beam « Elastique_<articulation> » entre les points d'articulation (visibles partout).
-- Tempos :
--   Pompe_1..4 (Burst, sec)           bouffée de vapeur, jets qui montent des jambes, onde au sol, petite secousse
--   Aura_Vapeur (Duree, lent)         vapeur épaisse qui monte doucement (Montee 1,2 s) + nappe au sol, jusqu'à la fin
--   Explosion_Vapeur (Burst, énorme)  vapeur radiale rapide + gros nuage lent qui traîne, ondes, lignes, flash, secousse
--   Rafale_Trainees (Duree)           traînées des deux poings pendant la rafale (marqueur VFX au début de la rafale)
--   Impact_Rafale (Burst, mitraille)  poing fantôme (TraineeMembre), éclat, étincelles, traits de vitesse, hit-stop 0,045
--   Impact_Pied (Burst, lourd)        jambe fantôme, éclat, onde, lignes, traits, poussière, secousse, hit-stop 0,09
--   Feu_Debut (Duree, montée)         recharge : feu du poing qui grossit (Montee), lignes qui convergent, anneaux qui
--                                     implosent, braises qui tournent, lumière orange ; Feu_Fin l'éteint
--   Impact_AirPoing (Duree 0,25)      traits de vitesse le long du bras étiré, hit-stop 0,12
--   Explosion_AirPoing (Burst, détonation) éclat géant, boule de feu, ondes blanche et orange, lignes, fumée, secousse forte
--   Esquive_Atterrissage (Burst)      poussière et onde à l'atterrissage
-- Textures : intégrées (rbxasset://) ou déjà en ligne (luffy, zoro). Aucun envoi.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local BLANC = Color3.new(1, 1, 1)
local VAPEUR = Color3.fromRGB(248, 244, 244)
local VAPEUR_ROSE = Color3.fromRGB(255, 225, 228)
local JAUNE = Color3.fromRGB(255, 225, 90)
local ORANGE = Color3.fromRGB(255, 138, 42) -- #ff8a2a
local ROUGE = Color3.fromRGB(255, 55, 25)
local FUMEE_SOMBRE = Color3.fromRGB(60, 55, 55)
local POUSSIERE_COULEUR = Color3.fromRGB(235, 222, 196)
local FANTOME = Color3.fromRGB(255, 205, 190)

local TEX_ETINCELLE = "rbxasset://textures/particles/sparkles_main.dds"
local TEX_FEU = "rbxasset://textures/particles/fire_main.dds"
local TEX_FUMEE = "rbxasset://textures/particles/smoke_main.dds"
local TEX_ANNEAU = "rbxassetid://101774142734315" -- zoro / nami
local TEX_POUSSIERE = "rbxassetid://70434048288435" -- luffy
local TEX_ETOILE_IMPACT = "rbxassetid://112249090477155" -- luffy
local TEX_ANNEAU_IMPACT = "rbxassetid://93783833153831" -- luffy
local TEX_TRAITS = "rbxassetid://97795166368994" -- luffy (traits de vitesse)
local TEX_LIGNES_IMPACT = "rbxassetid://135983583011818" -- luffy

-- articulations étirées par les animations (pièce enfant → AnimationConstraint)
local ARTICULATIONS = {
	RightLowerArm = "RightElbow",
	RightHand = "RightWrist",
	LeftLowerArm = "LeftElbow",
	LeftHand = "LeftWrist",
	RightLowerLeg = "RightKnee",
	RightFoot = "RightAnkle",
	LeftLowerLeg = "LeftKnee",
	LeftFoot = "LeftAnkle",
}

local DOSSIERS = {
	"Pompe_1",
	"Pompe_2",
	"Pompe_3",
	"Pompe_4",
	"Aura_Vapeur",
	"Explosion_Vapeur",
	"Rafale_Trainees",
	"Impact_Rafale",
	"Impact_Pied",
	"Feu_Debut",
	"Feu_Fin",
	"Impact_AirPoing",
	"Explosion_AirPoing",
	"Esquive_Atterrissage",
}

local function seq(a: number, b: number): NumberSequence
	return NumberSequence.new({ NumberSequenceKeypoint.new(0, a), NumberSequenceKeypoint.new(1, b) })
end

-- taille : jaillit vite jusqu'à `pic` puis finit à `fin` (impacts)
local function jaillir(debut: number, pic: number, fin: number): NumberSequence
	return NumberSequence.new({
		NumberSequenceKeypoint.new(0, debut),
		NumberSequenceKeypoint.new(0.25, pic),
		NumberSequenceKeypoint.new(1, fin),
	})
end

local function fondu(debut: number): NumberSequence
	return NumberSequence.new({
		NumberSequenceKeypoint.new(0, debut),
		NumberSequenceKeypoint.new(0.7, debut + (1 - debut) * 0.3),
		NumberSequenceKeypoint.new(1, 1),
	})
end

-- apparaît en fondu (nuages qui se forment) puis disparaît
local function nuage(opacite: number): NumberSequence
	return NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.15, opacite),
		NumberSequenceKeypoint.new(0.6, opacite + (1 - opacite) * 0.35),
		NumberSequenceKeypoint.new(1, 1),
	})
end

type Reglages = { [string]: any }

local function emetteur(parent: Instance, nom: string, r: Reglages): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Name = nom
	e.Enabled = false
	e.Texture = r.Texture or TEX_ETINCELLE
	local couleur = r.Couleur or BLANC
	e.Color = if typeof(couleur) == "ColorSequence" then couleur else ColorSequence.new(couleur)
	-- plein jour : l'additif pur (LightEmission 1) disparaît sur le sable clair des bases (vu sur zoro)
	e.LightEmission = r.LightEmission or 0.4
	e.LightInfluence = r.LightInfluence or 0
	e.Brightness = r.Eclat or 2
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

-- émetteurs d'un ancien effet de luffy (dossier VFX existant), réutilisés tels quels
local function anciens(vfx: Folder, nom: string, classe: string): { Instance }
	local liste = {}
	local d = vfx:FindFirstChild(nom)
	if d then
		for _, lien in d:GetChildren() do
			if lien:IsA("ObjectValue") and lien.Value and lien.Value:IsA(classe) then
				table.insert(liste, lien.Value)
			end
		end
	end
	return liste
end

local function nettoyer(modele: Model, vfx: Folder)
	for _, d in vfx:GetChildren() do
		if table.find(DOSSIERS, d.Name) then
			d:Destroy()
		end
	end
	for _, d in modele:GetDescendants() do
		if
			string.sub(d.Name, 1, 14) == "VFX_Elastique_"
			or (d:IsA("Beam") and string.sub(d.Name, 1, 10) == "Elastique_")
		then
			d:Destroy()
		end
	end
end

local function membresElastiques(modele: Model): number
	-- Membres élastiques : un Beam couleur peau entre les deux points de chaque articulation étirée. Roblox le dessine à
	-- chaque rendu (jeu, mode édition, Éditeur d'animation), sans script ni retard ; longueur nulle quand le membre
	-- n'est pas étiré, donc invisible.
	local nb = 0
	for membre, nomJoint in ARTICULATIONS do
		local part = modele:FindFirstChild(membre)
		local joint = part and part:FindFirstChild(nomJoint)
		if
			part
			and part:IsA("BasePart")
			and joint
			and joint:IsA("AnimationConstraint")
			and joint.Attachment0
			and joint.Attachment1
		then
			local beam = Instance.new("Beam")
			beam.Name = `Elastique_{nomJoint}`
			beam.Attachment0 = joint.Attachment0
			beam.Attachment1 = joint.Attachment1
			-- non éclairé et assombri : éclairé (ou à la couleur exacte), il paraissait plus clair que le bras
			beam.Color = ColorSequence.new(part.Color:Lerp(Color3.new(0, 0, 0), 0.25))
			beam.Transparency = NumberSequence.new(0)
			beam.LightEmission = 0
			beam.LightInfluence = 0
			beam.FaceCamera = true
			beam.Segments = 1
			beam.Width0 = math.min(part.Size.X, part.Size.Z) * 0.8
			beam.Width1 = beam.Width0
			beam.Parent = part
			nb += 1
		end
	end
	return nb
end

local function construire(modele: Model): string
	local vfx = modele:FindFirstChild("VFX") :: Folder
	local hrp = modele:FindFirstChild("HumanoidRootPart") :: BasePart
	local haut = modele:FindFirstChild("UpperTorso") :: BasePart
	local main = modele:FindFirstChild("RightHand") :: BasePart
	local humanoid = modele:FindFirstChildOfClass("Humanoid") :: Humanoid
	assert(vfx and hrp and haut and main and humanoid, `{modele.Name} : VFX, pièces du corps ou Humanoid manquants`)
	nettoyer(modele, vfx)
	modele:SetAttribute("Elastique", true) -- src/client/Elastique.luau : bulles des pompes, peau du Gear 2, Beam
	local nbBeams = membresElastiques(modele)

	local solY = -(hrp.Size.Y / 2 + humanoid.HipHeight) + 0.1
	local sol = attache(hrp, "VFX_Elastique_Sol", Vector3.new(0, solY, 0))
	local torse = attache(haut, "VFX_Elastique_Torse", Vector3.zero)

	-- Gear 2 ---------------------------------------------------------------------------------------------------------
	-- Pompes (tempo sec) : bouffée au sol, jets de vapeur qui fusent des jambes, onde
	local jets: { Instance } = {}
	for _, nom in { "RightUpperLeg", "LeftUpperLeg", "LowerTorso" } do
		local part = modele:FindFirstChild(nom)
		if part and part:IsA("BasePart") then
			table.insert(
				jets,
				emetteur(part, "VFX_Elastique_JetPompe", {
					Texture = TEX_FUMEE,
					Couleur = VAPEUR,
					LightEmission = 0.1,
					LightInfluence = 0.3,
					Taille = seq(0.8, 2.8),
					Transparence = fondu(0.08),
					Duree = NumberRange.new(0.35, 0.6),
					Vitesse = NumberRange.new(10, 16),
					Ecart = Vector2.new(25, 25),
					Frein = 5,
					Rotation = NumberRange.new(-120, 120),
					Quantite = 5,
				})
			)
		end
	end
	local pompe: { Instance } = {
		emetteur(sol, "OndePompe", {
			Texture = TEX_ANNEAU,
			Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
			Taille = jaillir(1, 6, 8),
			Transparence = fondu(0.3),
			Duree = NumberRange.new(0.3),
			Vitesse = NumberRange.new(0.01),
			Ecart = Vector2.zero,
			Quantite = 1,
		}),
		emetteur(sol, "BouffeePompe", {
			Texture = TEX_FUMEE,
			Couleur = VAPEUR,
			LightEmission = 0,
			LightInfluence = 0.3,
			Taille = seq(1.6, 3.8),
			Transparence = fondu(0.12),
			Duree = NumberRange.new(0.5, 0.9),
			Vitesse = NumberRange.new(9, 14),
			Ecart = Vector2.new(90, 90),
			Frein = 5,
			Rotation = NumberRange.new(-60, 60),
			Quantite = 10,
		}),
	}
	for _, jet in jets do
		table.insert(pompe, jet)
	end
	for i = 1, 4 do
		dossier(vfx, `Pompe_{i}`, { Mode = "Burst", Secousse = 0.2 }, pompe)
	end

	-- Vapeur du Gear 2 (tempo lent) : épaisse, monte doucement en puissance, jusqu'à la fin de la séquence
	local vapeur: { Instance } = {}
	for nom, debit in
		{
			UpperTorso = 34,
			LowerTorso = 18,
			RightUpperArm = 14,
			LeftUpperArm = 14,
			RightUpperLeg = 14,
			LeftUpperLeg = 14,
			Head = 10,
		}
	do
		local part = modele:FindFirstChild(nom)
		if part and part:IsA("BasePart") then
			table.insert(
				vapeur,
				emetteur(part, "VFX_Elastique_Vapeur", {
					Texture = TEX_FUMEE,
					Couleur = ColorSequence.new(VAPEUR, VAPEUR_ROSE),
					LightEmission = 0.15,
					LightInfluence = 0,
					Eclat = 1.6,
					Taille = seq(1.2, 3.4),
					Transparence = nuage(0.12),
					Duree = NumberRange.new(1, 1.6),
					Vitesse = NumberRange.new(0.8, 2),
					Acceleration = Vector3.new(0, 3.5, 0),
					Rotation = NumberRange.new(-50, 50),
					Debit = debit,
				})
			)
		end
	end
	-- nappe de vapeur qui s'étale au sol
	table.insert(
		vapeur,
		emetteur(sol, "NappeVapeur", {
			Texture = TEX_FUMEE,
			Couleur = VAPEUR,
			LightEmission = 0,
			LightInfluence = 0.3,
			Taille = seq(2.5, 6),
			Transparence = nuage(0.3),
			Duree = NumberRange.new(1.5, 2.2),
			Vitesse = NumberRange.new(2, 4),
			Ecart = Vector2.new(88, 88),
			Frein = 1,
			Acceleration = Vector3.new(0, 0.6, 0),
			Rotation = NumberRange.new(-30, 30),
			Debit = 8,
		})
	)
	-- 7,2 s réelles : les hit-stops rallongent la séquence
	dossier(vfx, "Aura_Vapeur", { Mode = "Duree", Duree = 7.2, Montee = 1.2 }, vapeur)

	-- Explosion de vapeur (tempo énorme) : jet radial rapide + nuage lent qui traîne
	dossier(vfx, "Explosion_Vapeur", { Mode = "Burst", Secousse = 0.8, DureeFlash = 0.15 }, {
		emetteur(torse, "VapeurRadiale", {
			Texture = TEX_FUMEE,
			Couleur = VAPEUR,
			LightEmission = 0.1,
			LightInfluence = 0.3,
			Taille = seq(2, 6),
			Transparence = fondu(0.05),
			Duree = NumberRange.new(0.6, 1.1),
			Vitesse = NumberRange.new(30, 48),
			Frein = 4.5,
			Rotation = NumberRange.new(-120, 120),
			Quantite = 90,
		}),
		emetteur(torse, "NuageLent", {
			Texture = TEX_FUMEE,
			Couleur = ColorSequence.new(VAPEUR, VAPEUR_ROSE),
			LightEmission = 0,
			LightInfluence = 0.3,
			Taille = seq(3.5, 8),
			Transparence = nuage(0.1),
			Duree = NumberRange.new(1.8, 2.6),
			Vitesse = NumberRange.new(3, 6),
			Frein = 1.5,
			Acceleration = Vector3.new(0, 1.5, 0),
			Rotation = NumberRange.new(-25, 25),
			Quantite = 18,
		}),
		emetteur(sol, "OndeVapeur", {
			Texture = TEX_ANNEAU,
			Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
			Taille = jaillir(1, 14, 20),
			Transparence = fondu(0.2),
			Duree = NumberRange.new(0.55),
			Vitesse = NumberRange.new(0.01),
			Ecart = Vector2.zero,
			Quantite = 1,
		}),
		emetteur(sol, "OndeRapide", {
			Texture = TEX_ANNEAU_IMPACT,
			Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
			Taille = seq(0.5, 12),
			Duree = NumberRange.new(0.3),
			Vitesse = NumberRange.new(0.01),
			Ecart = Vector2.zero,
			Quantite = 1,
		}),
		emetteur(sol, "PoussiereVapeur", {
			Texture = TEX_POUSSIERE,
			Couleur = POUSSIERE_COULEUR,
			LightEmission = 0,
			LightInfluence = 1,
			Eclat = 1,
			Taille = seq(1, 2.6),
			Transparence = fondu(0.4),
			Duree = NumberRange.new(0.5, 0.8),
			Vitesse = NumberRange.new(20, 30),
			Ecart = Vector2.new(90, 90),
			Frein = 5,
			Quantite = 16,
		}),
		emetteur(torse, "LignesImpact", {
			Texture = TEX_LIGNES_IMPACT,
			Taille = seq(10, 13),
			Transparence = fondu(0.25),
			Duree = NumberRange.new(0.2),
			Quantite = 1,
		}),
		lumiere(haut, "VFX_Elastique_FlashVapeur", BLANC, 2, 14),
	})

	-- Combo ----------------------------------------------------------------------------------------------------------
	-- Rafale : traînées des deux poings pendant toute la rafale (anciennes traînées de luffy)
	dossier(vfx, "Rafale_Trainees", { Mode = "Duree", Duree = 1.1 }, anciens(vfx, "Rafale", "Trail"))

	-- Coups : sur le membre qui frappe (AuMembre), poing ou jambe fantôme (TraineeMembre)
	local membre = attache(hrp, "VFX_Elastique_Membre", Vector3.zero)
	dossier(vfx, "Impact_Rafale", {
		Mode = "Burst",
		AuMembre = true,
		TraineeMembre = FANTOME,
		Secousse = 0.2,
		HitStop = 0.045,
		DureeFlash = 0.04,
	}, {
		emetteur(membre, "Eclat", {
			Texture = TEX_ETOILE_IMPACT,
			Taille = jaillir(0.6, 2.8, 2),
			Duree = NumberRange.new(0.08),
			Quantite = 1,
		}),
		emetteur(membre, "Etincelles", {
			Couleur = ColorSequence.new(BLANC, JAUNE),
			Taille = seq(0.3, 0),
			Duree = NumberRange.new(0.15, 0.3),
			Vitesse = NumberRange.new(18, 30),
			Frein = 6,
			Quantite = 10,
		}),
		emetteur(membre, "Anneau", {
			Texture = TEX_ANNEAU_IMPACT,
			Taille = seq(0.3, 3.2),
			Duree = NumberRange.new(0.12),
			Angle = NumberRange.new(0),
			Quantite = 1,
		}),
		emetteur(membre, "TraitsVitesse", {
			Texture = TEX_TRAITS,
			Orientation = Enum.ParticleOrientation.VelocityParallel,
			Direction = Enum.NormalId.Front,
			Ecart = Vector2.new(20, 20),
			Taille = seq(0.3, 0.1),
			Duree = NumberRange.new(0.1),
			Vitesse = NumberRange.new(40, 60),
			Quantite = 4,
		}),
		lumiere(membre, "VFX_Elastique_FlashCoup", JAUNE, 1.5, 7),
	})
	dossier(vfx, "Impact_Pied", {
		Mode = "Burst",
		AuMembre = true,
		TraineeMembre = FANTOME,
		Secousse = 0.65,
		HitStop = 0.09,
		DureeFlash = 0.08,
	}, {
		emetteur(membre, "EclatPied", {
			Texture = TEX_ETOILE_IMPACT,
			Taille = jaillir(1, 5, 3.5),
			Duree = NumberRange.new(0.12),
			Quantite = 1,
		}),
		emetteur(membre, "EtincellesPied", {
			Couleur = ColorSequence.new(BLANC, JAUNE),
			Taille = seq(0.4, 0),
			Duree = NumberRange.new(0.2, 0.35),
			Vitesse = NumberRange.new(22, 36),
			Frein = 6,
			Quantite = 22,
		}),
		emetteur(membre, "AnneauPied", {
			Texture = TEX_ANNEAU_IMPACT,
			Taille = seq(0.5, 7),
			Duree = NumberRange.new(0.2),
			Quantite = 1,
		}),
		emetteur(membre, "LignesPied", {
			Texture = TEX_LIGNES_IMPACT,
			Taille = seq(7, 8.5),
			Transparence = fondu(0.3),
			Duree = NumberRange.new(0.13),
			Quantite = 1,
		}),
		emetteur(membre, "TraitsPied", {
			Texture = TEX_TRAITS,
			Orientation = Enum.ParticleOrientation.VelocityParallel,
			Direction = Enum.NormalId.Front,
			Ecart = Vector2.new(35, 35),
			Taille = seq(0.35, 0.1),
			Duree = NumberRange.new(0.12),
			Vitesse = NumberRange.new(40, 55),
			Quantite = 8,
		}),
		emetteur(membre, "SoufflePied", {
			Texture = TEX_FUMEE,
			Couleur = VAPEUR,
			LightEmission = 0,
			LightInfluence = 0.5,
			Taille = seq(1, 2.6),
			Transparence = fondu(0.45),
			Duree = NumberRange.new(0.4, 0.6),
			Vitesse = NumberRange.new(12, 18),
			Frein = 5,
			Quantite = 8,
		}),
		lumiere(membre, "VFX_Elastique_FlashPied", JAUNE, 2, 10),
	})

	-- Recharge du poing aérien (tempo montée en puissance) ----------------------------------------------------------
	local recharge: { Instance } = {
		emetteur(main, "VFX_Elastique_Feu", {
			Texture = TEX_FEU,
			Couleur = ColorSequence.new({
				ColorSequenceKeypoint.new(0, JAUNE),
				ColorSequenceKeypoint.new(0.5, ORANGE),
				ColorSequenceKeypoint.new(1, ROUGE),
			}),
			-- vu en Play : en plein jour, le feu doit être opaque et lumineux pour se voir
			LightEmission = 0.3,
			Eclat = 3,
			Taille = seq(2.2, 0.3),
			Transparence = fondu(0),
			Duree = NumberRange.new(0.3, 0.5),
			Vitesse = NumberRange.new(1, 3),
			Acceleration = Vector3.new(0, 7, 0),
			Debit = 110,
		}),
		emetteur(main, "VFX_Elastique_Braises", {
			Couleur = ORANGE,
			Taille = seq(0.3, 0),
			Duree = NumberRange.new(0.5, 0.9),
			Vitesse = NumberRange.new(3, 7),
			Acceleration = Vector3.new(0, 5, 0),
			Rotation = NumberRange.new(-300, 300),
			Debit = 35,
		}),
		-- anneaux qui implosent autour du poing (chargement)
		emetteur(main, "VFX_Elastique_AnneauxCharge", {
			Texture = TEX_ANNEAU_IMPACT,
			Couleur = ColorSequence.new(JAUNE, ORANGE),
			Taille = seq(4.5, 0.4),
			Transparence = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 1),
				NumberSequenceKeypoint.new(0.3, 0.2),
				NumberSequenceKeypoint.new(1, 0.6),
			}),
			Duree = NumberRange.new(0.3),
			Accroche = true,
			Rotation = NumberRange.new(-200, 200),
			Debit = 7,
		}),
		lumiere(main, "VFX_Elastique_LumiereFeu", ORANGE, 1.5, 10),
	}
	-- lignes qui convergent vers le poing (ancien effet de luffy : sphère soudée à la main, émission vers l'intérieur)
	for _, ancien in anciens(vfx, "Charge_Poing", "ParticleEmitter") do
		if ancien.Name == "Charge_Lignes" then
			table.insert(recharge, ancien)
		end
	end
	dossier(vfx, "Feu_Debut", { Mode = "Duree", Duree = 1.6, Montee = 0.8 }, recharge)
	dossier(vfx, "Feu_Fin", { Mode = "Eteindre", Cible = "Feu_Debut" }, {})

	-- Poing aérien : traits de vitesse le long du bras étiré (anciens effets) pendant le lancer, puis détonation ------
	dossier(
		vfx,
		"Impact_AirPoing",
		{ Mode = "Duree", Duree = 0.25, HitStop = 0.12 },
		anciens(vfx, "Poing_Elastique", "ParticleEmitter")
	)
	dossier(vfx, "Explosion_AirPoing", {
		Mode = "Burst",
		AuMembre = true,
		TraineeMembre = Color3.fromRGB(255, 190, 120),
		Secousse = 1.4,
		DureeFlash = 0.18,
	}, {
		emetteur(membre, "EclatPoing", {
			Texture = TEX_ETOILE_IMPACT,
			Taille = jaillir(2, 10, 7),
			Transparence = fondu(0.05),
			Duree = NumberRange.new(0.16),
			Quantite = 1,
		}),
		emetteur(membre, "BouleDeFeu", {
			Texture = TEX_FEU,
			Couleur = ColorSequence.new({
				ColorSequenceKeypoint.new(0, JAUNE),
				ColorSequenceKeypoint.new(0.4, ORANGE),
				ColorSequenceKeypoint.new(1, ROUGE),
			}),
			LightEmission = 0.4,
			Eclat = 3,
			Taille = seq(2.8, 0.6),
			Duree = NumberRange.new(0.35, 0.6),
			Vitesse = NumberRange.new(18, 30),
			Frein = 5,
			Quantite = 45,
		}),
		emetteur(membre, "EtincellesPoing", {
			Couleur = ColorSequence.new(JAUNE, ORANGE),
			Taille = seq(0.5, 0),
			Duree = NumberRange.new(0.3, 0.7),
			Vitesse = NumberRange.new(30, 50),
			Frein = 5,
			Quantite = 60,
		}),
		emetteur(membre, "OndeBlanche", {
			Texture = TEX_ANNEAU_IMPACT,
			Taille = seq(1, 15),
			Duree = NumberRange.new(0.22),
			Quantite = 1,
		}),
		emetteur(membre, "OndeOrange", {
			Texture = TEX_ANNEAU,
			Couleur = ORANGE,
			Taille = seq(1, 11),
			Transparence = fondu(0.2),
			Duree = NumberRange.new(0.35),
			Quantite = 1,
		}),
		emetteur(membre, "LignesPoing", {
			Texture = TEX_LIGNES_IMPACT,
			Taille = seq(13, 15),
			Transparence = fondu(0.25),
			Duree = NumberRange.new(0.18),
			Quantite = 1,
		}),
		emetteur(membre, "FumeePoing", {
			Texture = TEX_FUMEE,
			Couleur = FUMEE_SOMBRE,
			LightEmission = 0,
			LightInfluence = 1,
			Eclat = 1,
			Taille = seq(2.5, 6),
			Transparence = nuage(0.35),
			Duree = NumberRange.new(0.9, 1.4),
			Vitesse = NumberRange.new(8, 14),
			Frein = 3,
			Acceleration = Vector3.new(0, 2, 0),
			Quantite = 18,
		}),
		lumiere(membre, "VFX_Elastique_FlashPoing", ORANGE, 3, 16),
	})

	-- Atterrissage ------------------------------------------------------------------------------------------------------
	dossier(vfx, "Esquive_Atterrissage", { Mode = "Burst", Secousse = 0.3 }, {
		emetteur(sol, "PoussiereAtterrissage", {
			Texture = TEX_POUSSIERE,
			Couleur = POUSSIERE_COULEUR,
			LightEmission = 0,
			LightInfluence = 1,
			Eclat = 1,
			Taille = seq(1, 2.6),
			Transparence = fondu(0.35),
			Duree = NumberRange.new(0.5, 0.8),
			Vitesse = NumberRange.new(12, 18),
			Ecart = Vector2.new(90, 90),
			Frein = 5,
			Quantite = 16,
		}),
		emetteur(sol, "OndeAtterrissage", {
			Texture = TEX_ANNEAU,
			Orientation = Enum.ParticleOrientation.VelocityPerpendicular,
			Taille = jaillir(1, 7, 9),
			Transparence = fondu(0.4),
			Duree = NumberRange.new(0.3),
			Vitesse = NumberRange.new(0.01),
			Ecart = Vector2.zero,
			Quantite = 1,
		}),
	})

	return `{modele:GetFullName()} : {#DOSSIERS} effets, vapeur sur {#vapeur - 1} pièces, {nbBeams} membres élastiques`
end

local resultats = {}
local dossierModeles = ReplicatedStorage:FindFirstChild("ModelesPersonnages")
local luffy = dossierModeles and dossierModeles:FindFirstChild("luffy")
local apercu = workspace:FindFirstChild("Elastique_Apercu")
if luffy and luffy:IsA("Model") then
	table.insert(resultats, construire(luffy))
end
if apercu and apercu:IsA("Model") then
	table.insert(resultats, construire(apercu))
end
return table.concat(resultats, "\n")
