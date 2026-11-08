"""Sequence de combat de usopp (vitrine) : Grenades -> Balle-liane -> Rafale en mouvement, une seule animation.

Reecrit en R15 depuis les scripts R6 de l'utilisateur (assets/persos/usopp/Animations de combat Usopp/tools/studio/ :
GenererUsoppAttaques.luau = minutage et marqueurs d'origine, UsoppAttaques.server.luau = effets d'origine).
Moteur : celui de luffy (assets/persos/luffy/anims_luffy.py : IK numerique, pieds plantes, verifications), branche sur
le rig de usopp (rig_usopp.json, Motor6D : meme formule Part1 = Part0 * C0 * Transform * C1:Inverse()), puis finition
(assets/persos/_anim/finition.py).

Sorties : anims/usopp_Sequence.json (blocage), anims/usopp_Sequence_fini.json (a publier), anims/apercu_Sequence.json.
Repere : +X = droite du perso, +Y = haut, +Z = arriere (le perso regarde vers -Z). Angles en degres.

Le lance-pierre (Acc_LancePierre_Main) est tenu par la RightGripAttachment : le manche suit l'axe -Z de la main, la
fourche est a 1,4 stud au-dessus de la prise ; le plan de la fourche est perpendiculaire a l'avant-bras, donc un tir part
dans l'axe de l'avant-bras (src/client/Tireur.luau : direction = LookVector de la poignee). Viser = orienter
l'avant-bras ; la main gauche tire l'elastique jusqu'a la joue gauche (tenue classique, 08/11 : remplace la tenue a deux
mains sur le manche).

Marqueurs (src/client/Tireur.luau, src/client/Vitrine.luau) :
  Grenade "Main" : une grenade apparait dans la main droite ; Lancer "dx,dz" : lancee vers ce point du sol (studs,
  repere du perso) puis explosion (VFX Explosion_Grenade, sol fissure) ; Lancer "dx,dz,Grosse" : la derniere, plus forte.
  Tir "dx,dz" : graine tiree dans le sol a ce point, une liane pousse ; Fouet "1".."3" : la liane frappe.
  Bille : une bille part de la fourche dans l'axe du tir ; Charge / TirCharge : tir charge.
  Montrer / Cacher : lance-pierre dans le dos ou en main ; Esquive "Poussiere" : poussiere au sol (atterrissages).

Usage : uv run --with numpy --with scipy python assets/persos/usopp/anims_usopp.py
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI.parent / "luffy"))
sys.path.insert(0, str(ICI.parent / "_anim"))
import anims_luffy as M  # noqa: E402
import finition  # noqa: E402

# ---------------------------------------------------------------- moteur de luffy branche sur le rig de usopp

RIG = json.loads((ICI / "rig_usopp.json").read_text(encoding="utf-8"))
M.RIG = RIG
M.MOTEURS = {k: (v["part0"], v["part1"], M.cf(v["c0"]), M.cf(v["c1"])) for k, v in RIG["motors"].items()}
M.TAILLES = {k: np.array(v["taille"]) for k, v in RIG["pieces"].items()}
M.REPOS = M.fk({})
M.DOSSIER = ICI
FPS = M.FPS
ARTICULATIONS = M.ARTICULATIONS
fk, avec, planter, pied, main_vers, bras_dirige = M.fk, M.avec, M.planter, M.pied, M.main_vers, M.bras_dirige
REPOS = M.REPOS


def ecrire(nom, cles, n_images, boucle, priorite, marqueurs):
	donnees = {
		"nom": "usopp_" + nom,
		"images": n_images,
		"fps": FPS,
		"duree": round(n_images / FPS, 4),
		"boucle": boucle,
		"priorite": priorite,
		"repere": "Pose.CFrame = Transform de l'articulation ; angles en degres, CFrame.Angles(rx, ry, rz) ; cframe = 12 composantes",
		"cles": [
			{
				"image": f,
				"temps": round(f / FPS, 4),
				"easing": finition.vers_roblox(e),
				"poses": {art: {"angles": [round(float(v), 2) for v in p.get(art, (0, 0, 0))[:3]], "cframe": M.vers_douze(M.transform(p, art))} for art in ARTICULATIONS},
			}
			for f, p, e in cles
		],
		"marqueurs": marqueurs,
	}
	vus = [(m["image"], m["nom"]) for m in marqueurs]
	assert len(vus) == len(set(vus)), "deux marqueurs de meme nom sur la meme image (l'editeur d'animation en supprime un)"
	images = [f for f, _, _ in cles]
	assert images == sorted(images) and len(images) == len(set(images)), "cles pas dans l'ordre"
	(ICI / "anims").mkdir(exist_ok=True)
	(ICI / "anims" / f"usopp_{nom}.json").write_text(json.dumps(donnees, indent="\t", ensure_ascii=False), encoding="utf-8")
	print("ecrit", f"anims/usopp_{nom}.json", len(cles), "cles,", len(marqueurs), "marqueurs")


M.ecrire = ecrire  # finir() de luffy ecrit par ce biais

# ---------------------------------------------------------------- lance-pierre

GRIP = M.deplacement(0, -0.15778, 0) @ M.angles(-math.pi / 2, 0, 0)  # RightGripAttachment de la main (rotation X -90)
FOURCHE = 1.15  # centre de la fourche (y = 2,6 sur la poignee) : 1,15 stud au-dessus de la prise (y = 1,45), le long du manche


def fourche(pose):
	"""(centre de la fourche, direction du tir, direction du manche vers la fourche), repere HRP."""
	m = fk(pose)["RightHand"] @ GRIP
	manche = m[:3, :3] @ np.array([0, 1.0, 0])
	tir = -fk(pose)["RightHand"][:3, :3] @ np.array([0, 1.0, 0])  # le long de l'avant-bras, vers la main
	return m[:3, 3] + manche * FOURCHE, tir, manche


def unit(v):
	v = np.array(v, float)
	return v / np.linalg.norm(v)


def viser(pose, direction, ancre=(-1.0, -0.35, 0.8), fourche_tete=(0.15, -0.15, 2.05), incline=(0.0, 1.0), recul=0.0, tourne=30):
	"""Tenue classique du lance-pierre (demande de l'utilisateur du 08/11, remplace la tenue a deux mains « comme un
	fusil ») : la main droite tient le manche, bras tendu vers la cible, fourche dressee devant ; la main gauche tire
	l'elastique jusqu'a la joue gauche. Reperes de visee (avant = 'direction', droite, haut), decalages (droite, haut,
	avant) depuis le centre de la tete : ancre = point de traction, a cote de la joue (devant le visage, la main entre
	dans la tete carree de 1,25 stud et le bras gauche n'a pas l'allonge), fourche_tete = centre de la fourche ; manche penche (incline = (droite, haut)). Le bras droit est resolu en position et orientation (prise sous
	la fourche, axe -Z de la main = manche, sans traverser le corps). Buste tourne de 'tourne' deg (positif : epaule
	droite en avant, vers la cible). recul (0..1) : la main gauche lache l'elastique et s'ouvre vers l'arriere, l'arme
	revient de 0,2 stud et se cabre."""
	pose = dict(pose)
	w = pose.get("Waist", (0, 0, 0))
	nk = pose.get("Neck", (0, 0, 0))
	pose["Waist"] = (w[0], w[1] + tourne, w[2])
	pose["Neck"] = (nk[0], nk[1] - max(-25, min(25, tourne * 0.8)), nk[2])
	f = unit(direction)
	# repere de visee : avant = f, droite = horizontale perpendiculaire, haut = perpendiculaire aux deux
	droite = unit(np.cross(f, [0, 1.0, 0])) if abs(f[1]) < 0.99 else np.array([1.0, 0, 0])
	haut = np.cross(droite, f)
	manche = unit(droite * incline[0] + haut * incline[1] - f * 0.35 * recul)
	tete = fk(pose)["Head"][:3, 3]
	traction = tete + droite * ancre[0] + haut * ancre[1] + f * ancre[2]
	fo = tete + droite * fourche_tete[0] + haut * fourche_tete[1] + f * (fourche_tete[2] - 0.2 * recul)
	prise = fo - manche * FOURCHE
	# orientation voulue de la main : -Z = manche, axe Y dans l'axe du tir (plan de la fourche face a la cible) ; le
	# tir part de la fourche dans la direction donnee par le marqueur (Tireur.luau)
	z_main = -manche

	def cout(q):
		cfs = fk(q)
		m = cfs["RightHand"] @ GRIP
		c = 30 * float(np.sum((m[:3, 3] - prise) ** 2)) + 8 * float(np.sum((cfs["RightHand"][:3, 2] - z_main) ** 2)) + 6 * (1 - float(cfs["RightHand"][:3, 1] @ f) ** 2)
		pen = 0.0
		for b in ("RightUpperArm", "RightLowerArm", "RightHand"):
			pts = M.points_boite(M.TAILLES[b], cfs[b], 3)
			for corps in ("UpperTorso", "LowerTorso", "Head"):
				pen += M.penetration(pts, M.TAILLES[corps], cfs[corps], 0.0)
		return c + 60 * max(0.0, pen - 0.08)

	variables = [("RightShoulder", 0), ("RightShoulder", 1), ("RightShoulder", 2), ("RightElbow", 0), ("RightWrist", 0), ("RightWrist", 1), ("RightWrist", 2)]
	meilleur = (None, 1e18)
	for depart in [(90, 0, 0, 40), (60, -40, -30, 70), (100, 30, 20, 30), (40, -60, -40, 100), (120, -20, 0, 60)]:
		q = dict(pose)
		q["RightShoulder"], q["RightElbow"], q["RightWrist"] = depart[:3], (depart[3], 0, 0), (0, 0, 0)
		r = M.resoudre(q, variables, cout)
		if r[1] < meilleur[1]:
			meilleur = r
	p = meilleur[0]
	ecart = float(np.linalg.norm((fk(p)["RightHand"] @ GRIP)[:3, 3] - prise))
	if ecart > 0.2:
		print("   ! prise droite a %.2f de sa cible" % ecart)
	# main gauche : au point de traction (elastique tendu), ou lachee : ouverte, un peu en arriere et sur le cote
	main_g = traction + recul * (-f * 0.3 - droite * 0.35 + haut * 0.1)
	p, _ = main_vers(p, "Left", main_g, ecart_coude=np.array([-1.0, 0.2, 0.0]), tolerance=0.15)
	return p


# ---------------------------------------------------------------- poses de base

_NEUTRE = None


def neutre():
	"""Debout, fier, lance-pierre dans le dos : bras le long du corps un peu ecartes, menton leve."""
	global _NEUTRE
	if _NEUTRE is None:
		p = planter({"RootPos": (0, -0.04, 0), "Waist": (3, 0, 0), "Neck": (4, 0, 0), "RightKnee": (-6, 0, 0), "LeftKnee": (-6, 0, 0),
			"RightShoulder": (4, 0, 10), "RightElbow": (12, 0, 0), "LeftShoulder": (4, 0, -10), "LeftElbow": (12, 0, 0)},
			ecarte(0.12))
		_NEUTRE = p
	return dict(_NEUTRE)


def ecarte(dx=0.3, dz_d=0.0, dz_g=0.0, x=0.0, z=0.0):
	"""Pieds ecartes de 2*dx, decales de (x, z) (deplacements : le perso se retrouve ailleurs dans sa case)."""
	return {"Right": pied("Right", dx=dx + x, dz=dz_d + z), "Left": pied("Left", dx=-dx + x, dz=dz_g + z)}


def en_garde(x=0.0, z=0.0, bas=0.22, tourne=-10):
	"""Garde de tireur : pieds ecartes, gauche devant, genoux plies, buste un peu de 3/4."""
	pieds = ecarte(0.38, dz_d=0.32, dz_g=-0.3, x=x, z=z)
	p = planter(avec(neutre(), RootPos=(x, -bas, z), Root=(0, tourne, 0), Waist=(-6, -tourne * 0.6, 0), Neck=(4, -tourne * 0.4, 0)), pieds)
	return p, pieds


def en_l_air(base, hauteur, x=0.0, z=0.0, root=(0, 0, 0), groupe=1.0):
	"""Corps en l'air : jambes repliees (groupe 0 = tendues, 1 = genoux a la poitrine), sans pieds plantes."""
	p = dict(base)
	p["RootPos"] = (x, hauteur, z)
	p["Root"] = root
	g = groupe
	p["RightHip"] = (25 + 75 * g, 0, 6)
	p["LeftHip"] = (35 + 70 * g, 0, -6)
	p["RightKnee"] = (-20 - 95 * g, 0, 0)
	p["LeftKnee"] = (-25 - 100 * g, 0, 0)
	p["RightAnkle"] = (-10, 0, 0)
	p["LeftAnkle"] = (-10, 0, 0)
	return p


def accroupi(pose, pieds, bas=0.75):
	"""Reception / impulsion : bassin bas, buste penche, pieds plantes."""
	rp = pose.get("RootPos", (0, 0, 0))
	return planter(avec(pose, RootPos=(rp[0], -bas, rp[2]), Waist=(-22, 0, 0), Neck=(18, 0, 0)), pieds)


# ---------------------------------------------------------------- 1 : grenades (0-165)


def grenades():
	n = neutre()
	pieds = ecarte(0.36, dz_d=0.3, dz_g=-0.32)
	cles, marq = [], []
	# fouille dans le sac (hanche gauche) : main droite croisee, regard vers le sac, petit tassement
	fouille = planter(avec(n, RootPos=(0, -0.18, 0), Root=(0, 8, 0), Waist=(-14, 16, 0), Neck=(-16, 18, 0)), pieds)
	fouille, _ = main_vers(fouille, "Right", (-1.0, -0.95, -0.55), ecart_coude=np.array([0.6, 0, -0.3]), tolerance=0.1)
	fouille2 = dict(fouille)
	fouille2["RightWrist"] = (18, 0, -10)
	fouille2["Neck"] = (-10, 14, 4)

	def armer(k):
		# bras droit en arriere, grenade derriere la tete, bras gauche tendu vers la cible, buste tourne vers la droite
		p = planter(avec(n, RootPos=(0, -0.2, 0.08), Root=(0, -16, 0), Waist=(8, -24, 0), Neck=(-4, 28, 0)), pieds)
		p = bras_dirige(p, "Right", unit((0.75, 0.15, 0.65)), unit((0.05, 1.0, 0.35)))
		p = bras_dirige(p, "Left", unit((-0.25, 0.25, -1.0)), unit((-0.05, 0.35, -1.0)))
		return p

	def lacher(k):
		# bras fouette au-dessus de l'epaule, buste qui bascule vers l'avant et tourne vers la gauche
		p = planter(avec(n, RootPos=(0, -0.3, -0.12), Root=(0, 14, 0), Waist=(-20, 22, 0), Neck=(16, -18, 0)), pieds)
		p = bras_dirige(p, "Right", unit((0.25, 0.75, -0.6)), unit((0.0, 0.25, -1.0)))
		p = bras_dirige(p, "Left", unit((-0.6, -0.5, 0.45)), unit((-0.2, -0.9, 0.2)))
		return p

	def accompagner(k):
		p = planter(avec(n, RootPos=(0, -0.34, -0.1), Root=(0, 18, 0), Waist=(-26, 22, 0), Neck=(22, -20, 0)), pieds)
		p = bras_dirige(p, "Right", unit((-0.15, -0.55, -0.8)), unit((-0.45, -0.8, -0.35)))
		p = bras_dirige(p, "Left", unit((-0.65, -0.55, 0.4)), unit((-0.2, -0.95, 0.1)))
		return p

	cles += [(0, n, "Cubic"), (10, fouille, "Cubic"), (16, fouille2, "Linear"), (22, fouille, "Linear"), (28, fouille2, "Cubic")]
	marq.append({"image": 30, "nom": "Grenade", "valeur": "Main"})
	cibles = ["-2.5,-7", "2,-8.5", "0,-10,Grosse"]
	t = 30
	for k in range(3):
		cles += [(t + 6, armer(k), "Entree"), (t + 11, lacher(k), "Sortie"), (t + 16, accompagner(k), "Cubic")]
		marq.append({"image": t + 11, "nom": "Lancer", "valeur": cibles[k]})
		if k < 2:
			# la main repasse au sac et ressort une grenade
			cles.append((t + 21, fouille, "Cubic"))
			marq.append({"image": t + 22, "nom": "Grenade", "valeur": "Main"})
			t += 22
		else:
			t += 16
	# t = 90 : il regarde le spectacle, mains sur les oreilles a la grosse explosion (~ image 118), puis bras leves
	regarde = planter(avec(n, RootPos=(0, -0.12, 0), Waist=(-6, 0, 0), Neck=(8, 0, 0)), pieds)
	regarde = bras_dirige(regarde, "Right", unit((0.7, -0.6, -0.2)), unit((0.2, -0.9, -0.4)))
	regarde = bras_dirige(regarde, "Left", unit((-0.7, -0.6, -0.2)), unit((-0.2, -0.9, -0.4)))
	tete = fk(n)["Head"][:3, 3]
	oreilles = planter(avec(n, RootPos=(0, -0.42, 0.1), Root=(-4, 0, 0), Waist=(-18, 0, 0), Neck=(-14, 0, 0)), pieds)
	oreilles, _ = main_vers(oreilles, "Right", fk(oreilles)["Head"][:3, 3] + np.array([0.75, 0.0, 0.0]), ecart_coude=np.array([1, 0, -0.3]), tolerance=0.12, obstacles=())
	oreilles, _ = main_vers(oreilles, "Left", fk(oreilles)["Head"][:3, 3] + np.array([-0.75, 0.0, 0.0]), ecart_coude=np.array([-1, 0, -0.3]), tolerance=0.12)
	victoire = planter(avec(n, RootPos=(0, 0.02, 0), Waist=(10, 0, 0), Neck=(14, 0, 0)), pieds)
	victoire = bras_dirige(victoire, "Right", unit((0.55, 0.85, 0.0)), unit((0.25, 1.0, -0.05)))
	victoire = bras_dirige(victoire, "Left", unit((-0.55, 0.85, 0.0)), unit((-0.25, 1.0, -0.05)))
	hop = planter(avec(victoire, RootPos=(0, 0.12, 0)), M.saut_entre({}, pieds, 0.25))
	del tete
	cles += [
		(98, regarde, "Cubic"),
		(110, regarde, "Entree"),
		(114, oreilles, "Cubic"),
		(126, oreilles, "Rebond"),
		(134, victoire, "Cubic"),
		(140, hop, "Cubic"),
		(146, victoire, "Cubic"),
		(165, n, "Cubic"),
	]
	return cles, marq


# ---------------------------------------------------------------- 2 : saut + balle-liane (165-345)


def liane():
	n = neutre()
	cles, marq = [], []
	pieds0 = ecarte(0.12)
	# 172 : main droite au-dessus de l'epaule droite, sur le lance-pierre du dos
	dos = planter(avec(n, RootPos=(0, -0.08, 0), Waist=(-4, -10, 0), Neck=(2, 8, 0)), pieds0)
	dos, _ = main_vers(dos, "Right", (1.15, 2.05, 0.75), ecart_coude=np.array([1, 0.4, -0.4]), tolerance=0.15)
	# 182 : il le sort et le fait tourner devant lui (manche vertical a droite)
	garde, pieds = en_garde()
	sortie = viser(garde, (0.15, 0.55, -1.0))
	# 190 : impulsion (accroupi, bras en arriere)
	impulsion = accroupi(avec(garde, RightShoulder=(-40, 0, 20), RightElbow=(30, 0, 0), LeftShoulder=(-45, 0, -20), LeftElbow=(30, 0, 0)), pieds, 0.8)
	# en l'air : monte a 4,5 studs, vise le sol devant lui (balle-graine), redescend
	monte = en_l_air(avec(sortie, Waist=(-4, 0, 0), Neck=(4, 0, 0)), 2.6, groupe=0.2)
	vise = viser(en_l_air(avec(n, Waist=(-22, 0, 0), Neck=(12, 0, 0)), 4.4, root=(-12, 0, 0), groupe=0.9), (0.0, -0.35, -1.0))
	tire = dict(vise)
	tire = viser(tire, (0.0, -0.35, -1.0), recul=1.0, tourne=0)
	descend = en_l_air(avec(tire, Waist=(-6, 0, 0)), 2.0, groupe=0.35)
	recep = accroupi(avec(garde, RightShoulder=(20, 0, 30), RightElbow=(40, 0, 0), LeftShoulder=(30, 0, -35), LeftElbow=(30, 0, 0)), pieds, 0.9)
	# la liane se bat : il la commande (bras gauche tendu, doigt pointe), lance-pierre leve, petits bonds d'excitation
	def ordre(s):
		p = planter(avec(garde, RootPos=(0, -0.2 - 0.06 * s, 0), Waist=(-8 + 4 * s, -6 * s, 0), Neck=(6, 6 * s, 0)), pieds)
		p = bras_dirige(p, "Left", unit((-0.35, 0.3, -1.0)), unit((-0.15, 0.4 + 0.15 * s, -1.0)))
		p = bras_dirige(p, "Right", unit((0.8, 0.45, 0.1)), unit((0.1, 1.0, 0.0)))
		return p

	cles += [
		(172, dos, "Cubic"),
		(182, sortie, "Cubic"),
		(190, impulsion, "Entree"),
		(196, monte, "Sortie"),
		(204, vise, "Cubic"),
		(212, vise, "Linear"),
		(214, tire, "Cubic"),
		(220, tire, "Entree"),
		(228, descend, "Entree"),
		(233, recep, "Rebond"),
		(242, garde, "Cubic"),
		(252, ordre(1), "Sortie"),
		(262, ordre(-1), "Cubic"),
		(270, ordre(1), "Sortie"),
		(280, ordre(-1), "Cubic"),
		(288, ordre(1), "Sortie"),
		(300, ordre(-1), "Cubic"),
		(318, garde, "Cubic"),
	]
	marq += [
		{"image": 174, "nom": "Montrer", "valeur": "Acc_LancePierre_Main"},
		{"image": 174, "nom": "Cacher", "valeur": "Acc_LancePierre_Dos"},
		{"image": 212, "nom": "Tir", "valeur": "0,-6"},
		{"image": 233, "nom": "Esquive", "valeur": "Poussiere"},
		{"image": 253, "nom": "Fouet", "valeur": "1"},
		{"image": 271, "nom": "Fouet", "valeur": "2"},
		{"image": 289, "nom": "Fouet", "valeur": "3"},
	]
	return cles, marq, garde, pieds


# ---------------------------------------------------------------- 3 : rafale en mouvement (318-540)


def direction_bille(k, dx, dy):
	"""Direction d'une bille (repere du perso, -Z = devant), avec une petite dispersion reguliere."""
	ex = ((k * 37) % 11 - 5) * 0.012
	ey = ((k * 53) % 7 - 3) * 0.01
	return "%g,%g,-1" % (round(dx + ex, 3), round(dy + ey, 3))


def rafale(garde, pieds):
	n = neutre()
	cles, marq = [], []
	devant = (0.0, 0.08, -1.0)
	# a) rafale debout (8 billes, une toutes les 4 images), l'elastique claque d'avant en arriere
	arme = viser(garde, devant)
	lache = viser(garde, devant, recul=1.0)
	t = 326
	cles.append((t, arme, "Cubic"))
	for k in range(8):
		cles += [(t + 2 + 4 * k, lache, "Linear"), (t + 4 + 4 * k, arme, "Linear")]
		marq.append({"image": t + 2 + 4 * k, "nom": "Bille", "valeur": direction_bille(k, 0.0, 0.04)})
	t += 34  # 360
	# b) esquive : plongeon sur sa droite (+2,4 studs), roulade d'epaule, se releve a genou
	x1 = 2.4
	elan = accroupi(arme, pieds, 0.6)
	plonge = en_l_air(avec(n, Waist=(-20, 0, 0), Neck=(10, 0, 0), RightShoulder=(150, 0, 30), LeftShoulder=(150, 0, -30)), 1.6, x=x1 * 0.5, root=(0, 0, -55), groupe=0.4)
	# roulade adoucie (08/11) : -120 deg et bassin a 0,6 -> l'epaule droite effleure le sol, la tete reste a 0,8 stud
	# au-dessus (avant : -150 deg a 0,2, tete 0,47 stud sous le sol)
	roule = en_l_air(avec(n, Waist=(-35, 0, 0), Neck=(-20, 0, 0), RightShoulder=(60, 0, 10), LeftShoulder=(60, 0, -10), RightElbow=(90, 0, 0), LeftElbow=(90, 0, 0)), 0.6, x=x1 * 0.85, root=(0, 0, -120), groupe=1.0)
	# a genou : pied gauche devant, genou droit au sol (bassin a -0,9 : le tibia ne s'enfonce plus)
	pieds_g = {"Left": pied("Left", dx=-0.4 + x1, dz=-0.55), "Right": pied("Right", dx=0.4 + x1, dz=1.15, talon=70)}
	genou = planter(avec(n, RootPos=(x1, -0.9, 0.2), Waist=(-4, 0, 0), Neck=(2, 0, 0)), pieds_g)
	g_arme = viser(genou, (-0.12, 0.05, -1.0))
	g_lache = viser(genou, (-0.12, 0.05, -1.0), recul=1.0)
	cles += [(t + 4, elan, "Entree"), (t + 10, plonge, "Linear"), (t + 16, roule, "Sortie"), (t + 24, g_arme, "Rebond")]
	marq.append({"image": t + 22, "nom": "Esquive", "valeur": "Poussiere"})
	t += 24  # 384
	for k in range(6):
		cles += [(t + 2 + 4 * k, g_lache, "Linear"), (t + 4 + 4 * k, g_arme, "Linear")]
		marq.append({"image": t + 2 + 4 * k, "nom": "Bille", "valeur": direction_bille(k + 8, -0.12, 0.02)})
	t += 28  # 412
	# c) salto arriere en revenant au centre, tire deux billes tete en bas
	pieds_c = ecarte(0.38, dz_d=0.32, dz_g=-0.3, z=0.6)
	appel = planter(avec(n, RootPos=(x1 * 0.8, -0.85, 0.2), Waist=(-24, 0, 0), Neck=(20, 0, 0), RightShoulder=(-30, 0, 20), LeftShoulder=(-30, 0, -20)), {"Right": pied("Right", dx=0.38 + x1 * 0.8, dz=0.3), "Left": pied("Left", dx=-0.38 + x1 * 0.8, dz=-0.3)})
	s1 = en_l_air(avec(n, RightShoulder=(160, 0, 20), LeftShoulder=(160, 0, -20)), 2.6, x=x1 * 0.6, z=0.3, root=(70, 0, 0), groupe=0.6)
	# tete en bas : les epaules sont au-dessus de la tete, la fourche reste a droite du visage (le bras ne va pas plus loin)
	salto = {"fourche_tete": (0.9, -0.1, 1.35), "ancre": (-1.0, 0.3, 0.8), "tourne": 0}
	s2 = viser(en_l_air(n, 4.6, x=x1 * 0.4, z=0.45, root=(165, 0, 0), groupe=1.0), (0.0, -0.55, -1.0), **salto)
	s2b = viser(s2, (0.0, -0.6, -1.0), recul=1.0, **salto)
	s3 = en_l_air(avec(n, RightShoulder=(90, 0, 40), LeftShoulder=(90, 0, -40)), 3.0, x=x1 * 0.2, z=0.55, root=(260, 0, 0), groupe=0.8)
	s4 = en_l_air(avec(n, RightShoulder=(40, 0, 40), LeftShoulder=(40, 0, -40)), 1.0, z=0.6, root=(330, 0, 0), groupe=0.3)
	recep_c = accroupi(avec(garde, RootPos=(0, 0, 0.6), RightShoulder=(30, 0, 40), LeftShoulder=(30, 0, -40)), pieds_c, 0.85)
	cles += [
		(t + 6, appel, "Entree"),
		(t + 12, s1, "Linear"),
		(t + 18, s2, "Linear"),
		(t + 22, s2b, "Linear"),
		(t + 26, s2, "Linear"),
		(t + 32, s3, "Linear"),
		(t + 37, s4, "Entree"),
		(t + 42, recep_c, "Rebond"),
	]
	marq += [
		{"image": t + 20, "nom": "Bille", "valeur": direction_bille(14, 0.0, -0.45)},
		{"image": t + 24, "nom": "Bille", "valeur": direction_bille(15, 0.0, -0.5)},
		{"image": t + 42, "nom": "Esquive", "valeur": "Poussiere"},
	]
	t += 42  # 454
	# d) tir charge : il tire l'elastique tres loin, la bille grossit, puis TIR (recul d'un demi-stud)
	garde_c = planter(avec(garde, RootPos=(0, -0.3, 0.6)), pieds_c)
	charge = viser(garde_c, (0.0, 0.1, -1.0), ancre=(-1.1, -0.3, 0.45))  # elastique tire plus loin, a l'oreille
	charge2 = dict(charge)
	charge2["Neck"] = (charge["Neck"][0] - 4, charge["Neck"][1], 3)
	part = viser(planter(avec(garde, RootPos=(0, -0.24, 1.05), Waist=(8, 0, 0)), pieds_c), (0.0, 0.16, -1.0), recul=1.0)
	cles += [(t + 10, charge, "Cubic"), (t + 22, charge2, "Linear"), (t + 30, charge, "Linear"), (t + 32, part, "Sortie"), (t + 44, part, "Cubic")]
	marq += [{"image": t + 10, "nom": "Charge", "valeur": "1"}, {"image": t + 32, "nom": "TirCharge", "valeur": "0,0.04,-1"}]
	t += 44  # 498
	# e) remet le lance-pierre dans le dos et se replace au centre (petit pas), fier
	range_ = planter(avec(n, RootPos=(0, -0.06, 0.3), Waist=(-4, -10, 0), Neck=(6, 8, 0)), {"Right": pied("Right", dx=0.12, dz=0.3), "Left": pied("Left", dx=-0.12, dz=0.3)})
	range_, _ = main_vers(range_, "Right", fk(range_)["UpperTorso"][:3, 3] + np.array([1.15, 1.8, 0.75]), ecart_coude=np.array([1, 0.4, -0.4]), tolerance=0.15)
	pas = planter(avec(n, RootPos=(0, 0.04, 0.15)), M.saut_entre(ecarte(0.12, z=0.3), ecarte(0.12), 0.2))
	cles += [(t + 12, range_, "Cubic"), (t + 22, pas, "Cubic"), (540, n, "Cubic")]
	marq += [{"image": t + 12, "nom": "Montrer", "valeur": "Acc_LancePierre_Dos"}, {"image": t + 12, "nom": "Cacher", "valeur": "Acc_LancePierre_Main"}]
	return cles, marq


def sequence():
	c1, m1 = grenades()
	c2, m2, garde, pieds = liane()
	c3, m3 = rafale(garde, pieds)
	cles = c1 + c2 + c3
	for _, p, _ in cles:
		p.setdefault("RootPos", (0, 0, 0))
	marq = sorted(m1 + m2 + m3, key=lambda m: m["image"])
	n_images = 540
	M.verifier_anim("Sequence", cles, n_images)
	M.raccord(cles, neutre())
	ecrire("Sequence", cles, n_images, False, "Action", marq)
	# lance-pierre en main entre 174 et 510 ; impacts : secousses
	secousses = [(41, 4, 1.5), (63, 4, 1.5), (79, 4, 2.0), (233, 6, 3.0), (382, 5, 2.5), (454, 6, 3.0), (486, 10, 4.0)]
	M.finir("Sequence", cles, n_images, False, "Action", marq, secousses=secousses, respiration=1.0)

	def visibles(i):
		return ["Acc_LancePierre_Main"] if 174 <= i < 510 else ["Acc_LancePierre_Dos"]

	M.apercu("Sequence", cles, [0, 10, 36, 41, 114, 134, 172, 182, 204, 214, 233, 252, 328, 370, 376, 386, 430, 436, 446, 464, 486, 510], visibles)


def idle_gui():
	"""Idle de 4 s pour les images d'interface (grille de la carte) : fier, poings sur les hanches, respire, regarde a
	gauche puis a droite en levant le menton. Pas publiee : jouee en local dans Studio par assets/gui/plateau_studio.luau."""
	n = neutre()
	pieds = ecarte(0.2)

	def hanches(p):
		p = planter(p, pieds)
		bas = fk(p)["LowerTorso"][:3, 3]
		p, _ = main_vers(p, "Right", bas + np.array([1.05, 0.25, -0.05]), ecart_coude=np.array([1, 0, 0.3]), tolerance=0.12)
		p, _ = main_vers(p, "Left", bas + np.array([-1.05, 0.25, -0.05]), ecart_coude=np.array([-1, 0, 0.3]), tolerance=0.12)
		return p

	base = hanches(avec(n, RootPos=(0, -0.05, 0), Waist=(4, 0, 0), Neck=(6, 0, 0)))
	gauche = hanches(avec(n, RootPos=(0, -0.03, 0), Waist=(5, 6, 0), Neck=(12, 22, -4)))
	droite = hanches(avec(n, RootPos=(0, -0.03, 0), Waist=(5, -6, 0), Neck=(12, -22, 4)))
	cles = [(0, base, "Cubic"), (30, gauche, "Cubic"), (48, gauche, "Cubic"), (78, droite, "Cubic"), (96, droite, "Cubic"), (120, base, "Cubic")]
	for _, p, _ in cles:
		p.setdefault("RootPos", (0, 0, 0))
	M.verifier_anim("IdleGui", cles, 120)
	ecrire("IdleGui", cles, 120, True, "Idle", [])
	M.finir("IdleGui", cles, 120, True, "Idle", [], respiration=1.2)


if __name__ == "__main__":
	if len(sys.argv) > 1 and sys.argv[1] == "idle":
		idle_gui()
	else:
		sequence()
