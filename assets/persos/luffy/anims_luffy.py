"""Animations de vitrine de luffy (Idle, Action, Signature), calculees sur le rig releve dans Studio (rig_luffy.json).

Sortie : assets/persos/luffy/anims/luffy_<Nom>.json (source de verite), construits ensuite en KeyframeSequence dans
Studio (vers_studio.py) ; apercus : anims/apercu_<Nom>.json (poses completes a quelques images, pour apercu_studio.py).
Repere Studio : +X = droite du perso, +Y = haut, +Z = arriere. Une pose = Transform par articulation (AnimationConstraint),
donnee en angles (degres) : Transform = CFrame.Angles(rx, ry, rz), plus des translations ('<Art>Pos' : Root, coude
droit pour le bras elastique). Sens des axes : assets/persos/_rig/axes_r15.json.
Moteur repris de assets/persos/nami/anims_nami.py (IK numerique, pieds plantes, verifications).

Usage : uv run --with numpy --with scipy assets/persos/luffy/anims_luffy.py [Idle|Action|Signature]
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).parent.parent / "_anim"))
import finition  # noqa: E402

DOSSIER = Path(__file__).parent
RIG = json.loads((DOSSIER / "rig_luffy.json").read_text(encoding="utf-8"))
FPS = 30

ARTICULATIONS = ["Root", "Waist", "Neck", "RightShoulder", "RightElbow", "RightWrist", "LeftShoulder", "LeftElbow", "LeftWrist", "RightHip", "RightKnee", "RightAnkle", "LeftHip", "LeftKnee", "LeftAnkle"]
LIMITES = {  # (axe, min, max) en degres, Studio
	"RightElbow": [(0, 0, 150), (1, 0, 0), (2, 0, 0)],
	"LeftElbow": [(0, 0, 150), (1, 0, 0), (2, 0, 0)],
	"RightKnee": [(0, -150, 0), (1, 0, 0), (2, 0, 0)],
	"LeftKnee": [(0, -150, 0), (1, 0, 0), (2, 0, 0)],
	"RightWrist": [(0, -30, 30), (1, -30, 30), (2, -30, 30)],
	"LeftWrist": [(0, -30, 30), (1, -30, 30), (2, -30, 30)],
	"RightAnkle": [(0, -30, 30), (1, -30, 30), (2, -30, 30)],
	"LeftAnkle": [(0, -30, 30), (1, -30, 30), (2, -30, 30)],
	"Neck": [(0, -25, 25), (1, -25, 25), (2, -25, 25)],
}


# ---------------------------------------------------------------- CFrame (matrices 4x4)


def cf(l):
	m = np.eye(4)
	m[:3, 3] = l[:3]
	m[:3, :3] = np.array(l[3:]).reshape(3, 3)
	return m


def angles(rx, ry, rz):
	"""CFrame.Angles(rx, ry, rz) de Roblox (radians) = Rx * Ry * Rz."""
	cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
	Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
	Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
	Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
	m = np.eye(4)
	m[:3, :3] = Rx @ Ry @ Rz
	return m


def deplacement(x, y, z):
	m = np.eye(4)
	m[:3, 3] = (x, y, z)
	return m


def vers_douze(m):
	return [round(float(v), 6) for v in list(m[:3, 3]) + list(m[:3, :3].reshape(9))]


MOTEURS = {k: (v["part0"], v["part1"], cf(v["c0"]), cf(v["c1"])) for k, v in RIG["motors"].items()}
TAILLES = {k: np.array(v["taille"]) for k, v in RIG["pieces"].items()}


def transform(pose, art):
	rx, ry, rz = pose.get(art, (0, 0, 0))[:3]
	m = angles(math.radians(rx), math.radians(ry), math.radians(rz))
	if art + "Pos" in pose:
		m[:3, 3] = pose[art + "Pos"]
	return m


def fk(pose):
	"""CFrame de chaque piece, relatif au HumanoidRootPart."""
	cfs = {"HumanoidRootPart": np.eye(4)}
	reste = list(MOTEURS)
	while reste:
		for art in list(reste):
			p0, p1, c0, c1 = MOTEURS[art]
			if p0 in cfs:
				cfs[p1] = cfs[p0] @ c0 @ transform(pose, art) @ np.linalg.inv(c1)
				reste.remove(art)
	return cfs


REPOS = fk({})


# ---------------------------------------------------------------- volumes (verifications)


def points_boite(taille, cfm, pas=4):
	lo, hi = -taille / 2, taille / 2
	pts = []
	for i in range(pas):
		for j in range(pas):
			for k in range(pas):
				if 0 < i < pas - 1 and 0 < j < pas - 1 and 0 < k < pas - 1:
					continue
				p = lo + (hi - lo) * np.array([i, j, k]) / (pas - 1)
				pts.append((cfm @ np.append(p, 1))[:3])
	return np.array(pts)


def penetration(pts, taille, cfm, marge=0.04):
	"""Profondeur de penetration maximale de points dans une boite (taille, CFrame)."""
	lo, hi = -taille / 2 + marge, taille / 2 - marge
	loc = (np.linalg.inv(cfm) @ np.c_[pts, np.ones(len(pts))].T).T[:, :3]
	d = np.minimum(loc - lo, hi - loc).min(axis=1)
	return max(0.0, float(d.max()))


BRAS = ["RightUpperArm", "RightLowerArm", "RightHand", "LeftUpperArm", "LeftLowerArm", "LeftHand"]
CORPS = ["UpperTorso", "LowerTorso", "Head", "RightUpperLeg", "LeftUpperLeg"]


def verifier(pose):
	"""Penetrations (studs) des bras dans le corps ; deplacement du LowerTorso."""
	cfs = fk(pose)
	res = {}
	for b in BRAS:
		pts = points_boite(TAILLES[b], cfs[b])
		for c in CORPS:
			res[b + ">" + c] = penetration(pts, TAILLES[c], cfs[c])
	res["deplacement_LowerTorso"] = float(np.linalg.norm(cfs["LowerTorso"][:3, 3] - REPOS["LowerTorso"][:3, 3]))
	return res


# ---------------------------------------------------------------- IK numerique


def resoudre(pose, variables, cout):
	"""Optimise les angles listes [(articulation, axe)] (bornes : LIMITES) pour minimiser cout(pose)."""
	x0 = [pose.get(a, (0, 0, 0))[k] for a, k in variables]

	def appliquer(x):
		p = {k: (list(v) if isinstance(v, (tuple, list)) else v) for k, v in pose.items()}
		for (a, k), val in zip(variables, x):
			v = list(p.get(a, [0, 0, 0]))
			v[k] = val
			p[a] = v
		return p

	bornes = []
	for a, k in variables:
		lim = next(((mn, mx) for ax, mn, mx in LIMITES[a] if ax == k), (-180, 180)) if a in LIMITES else (-180, 180)
		bornes.append(lim)
	r = minimize(lambda x: cout(appliquer(x)), x0, bounds=bornes, method="L-BFGS-B", options={"maxiter": 500})
	return {k: (tuple(round(float(c), 2) for c in v) if isinstance(v, list) else v) for k, v in appliquer(r.x).items()}, r.fun


def pied(cote, dx=0.0, dz=0.0, dy=0.0, talon=0.0):
	"""CFrame voulu d'un pied : position de repos decalee (dx, dy, dz) ; talon = talon leve de 'talon' degres
	(rotation autour de la pointe du pied, qui reste au sol)."""
	m = REPOS[cote + "Foot"].copy()
	m = deplacement(dx, dy, dz) @ m
	if talon:
		t = TAILLES[cote + "Foot"]
		pointe = (m @ np.array([0, -t[1] / 2, -t[2] / 2, 1]))[:3]
		m = deplacement(*pointe) @ angles(math.radians(-talon), 0, 0) @ deplacement(*(-pointe)) @ m
	return m


def planter(pose, cibles=None, cotes=("Right", "Left")):
	"""Pieds plantes : hanches, genoux et chevilles recalcules pour amener chaque pied sur sa cible (position et
	orientation ; par defaut sa place de repos), quelle que soit la pose du bassin. cibles = {cote: CFrame}."""
	cibles = cibles or {}
	p = dict(pose)
	for cote in cotes:
		cible = cibles.get(cote, REPOS[cote + "Foot"])
		genou_pref = p.get(cote + "Knee", (0, 0, 0))[0]

		def cout(q, cote=cote, cible=cible, genou_pref=genou_pref):
			m = fk(q)[cote + "Foot"]
			return 50 * float(np.sum((m[:3, 3] - cible[:3, 3]) ** 2)) + 5 * float(np.sum((m[:3, :3] - cible[:3, :3]) ** 2)) + 0.0005 * (q[cote + "Knee"][0] - genou_pref) ** 2

		variables = [(cote + "Hip", 0), (cote + "Hip", 1), (cote + "Hip", 2), (cote + "Knee", 0), (cote + "Ankle", 0), (cote + "Ankle", 1), (cote + "Ankle", 2)]
		depart = dict(p)
		if depart.get(cote + "Knee", (0, 0, 0))[0] > -10:
			depart[cote + "Knee"] = (-20, 0, 0)  # genou un peu plie au depart : l'optimiseur trouve le bon sens
		p, _ = resoudre(depart, variables, cout)
		m = fk(p)[cote + "Foot"]
		ecart = float(np.linalg.norm(m[:3, 3] - cible[:3, 3]))
		if ecart > 0.03:
			print("   ! pied %s a %.3f stud de sa cible" % (cote, ecart))
	return p


def main_vers(pose, cote, cible, ecart_coude=None, poids_pen=200.0, poids_coude=0.5, tolerance=0.0, obstacles=(), departs_en_plus=()):
	"""IK du bras : la main (centre) va vers cible (repere HRP), sans traverser le corps (ni les obstacles : noms de
	pieces) ; ecart_coude = direction vers laquelle pousser le coude."""
	S, E, W = cote + "Shoulder", cote + "Elbow", cote + "Wrist"
	cible = np.array(cible, float)

	def cout(q):
		cfs = fk(q)
		c = 20 * float(np.sum((cfs[cote + "Hand"][:3, 3] - cible) ** 2))
		pen = 0.0
		for b in (cote + "UpperArm", cote + "LowerArm", cote + "Hand"):
			pts = points_boite(TAILLES[b], cfs[b], 3)
			for corps in ("UpperTorso", "LowerTorso", "Head") + tuple(obstacles):
				pen += penetration(pts, TAILLES[corps], cfs[corps], 0.0)
		c += poids_pen * max(0.0, pen - tolerance) + 2.0 * pen
		if ecart_coude is not None:
			c -= poids_coude * float(np.dot(cfs[cote + "LowerArm"][:3, 3], ecart_coude))
		return c

	variables = [(S, 0), (S, 1), (S, 2), (E, 0), (W, 0), (W, 1), (W, 2)]
	sz = 1 if cote == "Right" else -1
	departs = [None, ((-10, 0, 40 * sz), 100), ((-20, -50 * sz, 30 * sz), 110), ((40, 0, 20 * sz), 110), ((10, 40 * sz, 50 * sz), 90), ((60, 0, 10 * sz), 130), ((120, 0, 60 * sz), 90)] + list(departs_en_plus)
	meilleur = (None, 1e18)
	for d in departs:
		q = dict(pose)
		if d is not None:
			q[S], q[E], q[W] = d[0], (d[1], 0, 0), (0, 0, 0)
		r = resoudre(q, variables, cout)
		if r[1] < meilleur[1]:
			meilleur = r
	cfs = fk(meilleur[0])
	print("   %s : main a %.3f stud de la cible" % (cote, float(np.linalg.norm(cfs[cote + "Hand"][:3, 3] - cible))))
	return meilleur


def euler_de(m3):
	from scipy.spatial.transform import Rotation as R

	return tuple(float(v) for v in R.from_matrix(m3).as_euler("XYZ", degrees=True))


def bras_dirige(pose, cote, u, f):
	"""Bras construit a partir de deux directions monde (repere HRP) : u = epaule -> coude, f = coude -> main.
	Le coude ne plie que sur X+ : son axe est impose par u et f (cf. nami)."""
	S, E, W = cote + "Shoulder", cote + "Elbow", cote + "Wrist"
	u = np.array(u, float) / np.linalg.norm(u)
	f = np.array(f, float) / np.linalg.norm(f)
	c = float(np.clip(np.dot(u, f), -1, 1))
	theta = math.acos(c)
	if not math.radians(3) < theta < math.radians(150):
		return None
	z_u = -(f - u * c) / math.sin(theta)
	y_u = -u
	x_u = np.cross(y_u, z_u)
	R_u = np.column_stack([x_u, y_u, z_u])
	p = dict(pose)
	R_ut = fk(p)["UpperTorso"][:3, :3]
	p[S] = euler_de(R_ut.T @ R_u)
	p[E] = (round(math.degrees(theta), 2), 0, 0)
	p[W] = p.get(W, (0, 0, 0))
	return p


def etirer(pose, cote, d):
	"""Bras elastique : l'epaule et le haut du bras (manche) restent en place, l'avant-bras s'eloigne de d studs le long
	de son axe (d > 0 : vers la main, d < 0 : vers le coude) ; la peau etiree entre les deux est un Beam dans Studio
	(BrasElastique_*). La translation de Transform est exprimee dans le repere du haut du bras (C0 du coude)."""
	p = dict(pose)
	rx, ry, rz = p.get(cote + "Elbow", (0, 0, 0))[:3]
	axe = angles(math.radians(rx), math.radians(ry), math.radians(rz))[:3, :3] @ np.array([0, -1.0, 0])
	p[cote + "ElbowPos"] = tuple(round(float(v), 4) for v in axe * d)
	return p


# ---------------------------------------------------------------- animation


def lisser(t, easing):
	return finition.courbe(t, easing)


def slerp_pose(pa, pb, t):
	from scipy.spatial.transform import Rotation as R, Slerp

	out = {}
	for art in ARTICULATIONS:
		a = pa.get(art, (0, 0, 0))
		b = pb.get(art, (0, 0, 0))
		ra = R.from_matrix(angles(*np.radians(a[:3]))[:3, :3])
		rb = R.from_matrix(angles(*np.radians(b[:3]))[:3, :3])
		if 0 <= t <= 1:
			r = Slerp([0, 1], R.concatenate([ra, rb]))(t)
		else:  # depassement (courbes Rebond, Elastique de finition.py) : rotation prolongee au-dela de b
			r = R.from_rotvec((rb * ra.inv()).as_rotvec() * t) * ra
		out[art] = tuple(np.degrees(r.as_euler("XYZ")))
	for art in ARTICULATIONS:
		cle = art + "Pos"
		if cle in pa or cle in pb:
			a_pos = np.array(pa.get(cle, (0, 0, 0)))
			b_pos = np.array(pb.get(cle, (0, 0, 0)))
			out[cle] = tuple(a_pos + (b_pos - a_pos) * t)
	return out


def pose_a(cles, image):
	"""Pose a une image. Comme dans Roblox, l'easing d'une cle regit la transition qui PART de cette cle."""
	for (fa, pa, ea), (fb, pb, _) in zip(cles, cles[1:]):
		if fa <= image <= fb:
			t = 0 if fb == fa else (image - fa) / (fb - fa)
			return slerp_pose(pa, pb, lisser(t, ea))
	return cles[-1][1]


def verifier_anim(nom, cles, n_images, ignorer=()):
	pire = {}
	for i in range(0, n_images + 1, 2):
		for k, v in verifier(pose_a(cles, i)).items():
			if v > pire.get(k, (0, -1))[0]:
				pire[k] = (v, i)
	print(f"--- verification {nom} (pire valeur, image ; seuil 0,02 ; LowerTorso <= 0,5)")
	for k, (v, i) in sorted(pire.items()):
		if k in ignorer:
			continue
		if k == "deplacement_LowerTorso":
			print(f"  {k}: {v:.3f} (image {i})" + ("  !!! > 0,5" if v > 0.5 else ""))
		elif v > 0.02:
			print(f"  {k}: {v:.3f} (image {i})")


def ecrire(nom, cles, n_images, boucle, priorite, marqueurs):
	donnees = {
		"nom": "luffy_" + nom,
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
				"poses": {art: {"angles": [round(float(v), 2) for v in p.get(art, (0, 0, 0))[:3]], "cframe": vers_douze(transform(p, art))} for art in ARTICULATIONS},
			}
			for f, p, e in cles
		],
		"marqueurs": marqueurs,
	}
	vus = [(m["image"], m["nom"]) for m in marqueurs]
	assert len(vus) == len(set(vus)), "deux marqueurs de meme nom sur la meme image (l'editeur d'animation en supprime un)"
	images = [f for f, _, _ in cles]
	assert images == sorted(images) and len(images) == len(set(images)), "cles pas dans l'ordre"
	(DOSSIER / "anims").mkdir(exist_ok=True)
	(DOSSIER / "anims" / f"luffy_{nom}.json").write_text(json.dumps(donnees, indent="\t", ensure_ascii=False), encoding="utf-8")
	print("ecrit", f"anims/luffy_{nom}.json", len(cles), "cles,", len(marqueurs), "marqueurs")


def finir(nom, cles, n_images, boucle, priorite, marqueurs, **reglages):
	"""Version finie (finition.py) : cuisson image par image (ressorts, respiration, secousses), verifications sur
	chaque image, allegement, ecrite dans anims/luffy_<Nom>_fini.json a cote du blocage."""
	images = finition.cuire(cles, n_images, ARTICULATIONS, boucle=boucle, limites=LIMITES, **reglages)
	for art in ARTICULATIONS:
		for i in (0, n_images):
			assert np.allclose(transform(images[i], art), transform(cles[0 if i == 0 else -1][1], art), atol=1e-4), f"raccord fini {art} image {i}"
	pire = {}
	for i, p in enumerate(images):
		for k, v in verifier(p).items():
			if v > pire.get(k, (0, -1))[0]:
				pire[k] = (v, i)
	bloc = {}
	for i in range(0, n_images + 1):
		for k, v in verifier(pose_a(cles, i)).items():
			bloc[k] = max(bloc.get(k, 0), v)
	print(f"--- verification {nom}_fini (pire valeur, image ; entre parentheses : blocage)")
	for k, (v, i) in sorted(pire.items()):
		if k == "deplacement_LowerTorso" or v > 0.02:
			alerte = "  !!!" if (k == "deplacement_LowerTorso" and v > 0.5) or (k != "deplacement_LowerTorso" and v > bloc.get(k, 0) + 0.05) else ""
			print(f"  {k}: {v:.3f} (image {i}) ({bloc.get(k, 0):.3f}){alerte}")
	gardees = finition.alleger(images, ARTICULATIONS)
	ecrire(nom + "_fini", [(i, images[i], "Linear") for i in gardees], n_images, boucle, priorite, marqueurs)
	return images


def apercu(nom, cles, images, visibles):
	"""Poses completes a quelques images (Transform de chaque articulation + accessoires Acc_* visibles)."""
	sortie = {str(i): {"poses": {art: vers_douze(transform(pose_a(cles, i), art)) for art in ARTICULATIONS}, "visibles": visibles(i)} for i in images}
	(DOSSIER / "anims" / f"apercu_{nom}.json").write_text(json.dumps(sortie), encoding="utf-8")


def raccord(cles, ref):
	"""Verifie que la premiere et la derniere cle sont identiques a la pose neutre (image 0 de l'Idle)."""
	for f, p, _ in (cles[0], cles[-1]):
		for art in ARTICULATIONS:
			assert np.allclose(transform(p, art), transform(ref, art), atol=1e-6), f"raccord image {f} : {art}"


# ---------------------------------------------------------------- poses de luffy


def avec(base, **kw):
	p = dict(base)
	p.update(kw)
	return p


# bord du chapeau tenu par la main gauche, repere HRP en pose de repos (cote gauche, un peu devant)
BORD_CHAPEAU = np.array([-1.0, 2.0, -0.3])
BORD_DANS_TETE = np.linalg.inv(REPOS["Head"]) @ np.append(BORD_CHAPEAU, 1)


def tient_chapeau(pose):
	"""Main gauche sur le bord du chapeau (qui suit la tete) ; coude sorti sur le cote."""
	cible = (fk(pose)["Head"] @ BORD_DANS_TETE)[:3]
	p, f = main_vers(pose, "Left", cible, ecart_coude=np.array([-1.0, 0.0, 0.0]), tolerance=0.06)
	return p


def poing_hanche(pose):
	"""Poing droit sur le haut de la hanche, coude sorti sur le cote et un peu en arriere (le coude ne plie que vers
	l'avant et l'epaule pivote 0,5 stud a l'interieur du bras : pas de vrai poing sur la hanche tourne vers l'interieur)."""
	p, f = main_vers(pose, "Right", (1.4, -0.45, 0.0), ecart_coude=np.array([1.0, 0, 0.2]), poids_coude=4.0, tolerance=0.2)
	return p


_NEUTRE = None


def neutre():
	"""Image 0 de l'Idle : debout, pieds plantes, main gauche au bord du chapeau, poing droit sur la hanche, sourire
	tete un peu penchee (energique)."""
	global _NEUTRE
	if _NEUTRE is None:
		p = planter({"Root": (0, 0, -2), "RootPos": (-0.05, -0.03, 0), "Waist": (0, -4, 3), "Neck": (4, 6, -4), "RightKnee": (-8, 0, 0)})
		p = poing_hanche(p)
		_NEUTRE = tient_chapeau(p)
	return dict(_NEUTRE)


def ecarte(dx=0.32, dz_d=0.0, dz_g=0.0):
	"""Cibles de pieds ecartes (jambes ecartees de 2*dx)."""
	return {"Right": pied("Right", dx=dx, dz=dz_d), "Left": pied("Left", dx=-dx, dz=dz_g)}


def saut_entre(cibles_a, cibles_b, hauteur=0.15):
	"""Pieds a mi-chemin entre deux placements, decolles de 'hauteur' (petit saut au lieu d'une glissade)."""
	out = {}
	for cote in ("Right", "Left"):
		a, b = cibles_a.get(cote, REPOS[cote + "Foot"]), cibles_b.get(cote, REPOS[cote + "Foot"])
		m = a.copy()
		m[:3, 3] = (a[:3, 3] + b[:3, 3]) / 2 + np.array([0, hauteur, 0])
		out[cote] = m
	return out


def idle():
	n = neutre()
	# rire : le torse descend et remonte 2 fois de 0,1 (genoux qui plient, pieds plantes), tete en arriere de 10 deg
	rire_bas = tient_chapeau(planter(avec(n, RootPos=(-0.05, -0.13, 0), Waist=(6, -4, 3), Neck=(14, 6, -4), Root=(0, 0, -2))))
	rire_haut = tient_chapeau(avec(n, Waist=(5, -4, 3), Neck=(14, 6, -4)))

	# moulinet : bras droit tendu, un peu ecarte, 2 tours complets vers l'avant autour de l'epaule (cles tous les
	# quarts de tour) ; le buste accompagne
	def moulinet(x, k):
		p = avec(rire_haut, RightShoulder=(x, 0, 18), RightElbow=(5, 0, 0), RightWrist=(0, 0, 0), Waist=(0, -6 + 4 * math.sin(k), 3), Neck=(4, 8, -4))
		return p

	depart = avec(rire_haut, RightShoulder=(-10, 0, 18), RightElbow=(5, 0, 0), RightWrist=(0, 0, 0), Neck=(4, 8, -4), Waist=(0, -6, 3))
	tours = [(30 + i * 2.5, moulinet((i * 90) % 360, i * math.pi / 2)) for i in range(9)]
	# etirement : les deux bras vers le haut, torse cambre, tete en arriere (baillement)
	etire = planter(avec(n, Waist=(14, 0, 0), Neck=(18, 0, 0), Root=(2, 0, 0), RootPos=(0, 0, 0.05),
		RightShoulder=(172, 0, 28), RightElbow=(6, 0, 0), RightWrist=(0, 0, 0),
		LeftShoulder=(172, 0, -28), LeftElbow=(6, 0, 0), LeftWrist=(0, 0, 0)))
	retour = tient_chapeau(poing_hanche(avec(n, Waist=(4, -4, 3), Neck=(6, 6, -2))))
	cles = [
		(0, n, "Cubic"),
		(6, rire_bas, "Cubic"),
		(12, rire_haut, "Cubic"),
		(18, rire_bas, "Cubic"),
		(25, rire_haut, "Cubic"),
		(28, depart, "Linear"),
	] + [(f, p, "Linear") for f, p in tours] + [
		(54, depart, "Cubic"),
		(62, etire, "Cubic"),
		(70, etire, "Cubic"),
		(80, retour, "Cubic"),
		(90, n, "Cubic"),
	]
	verifier_anim("Idle", cles, 90)
	raccord(cles, n)
	ecrire("Idle", cles, 90, True, "Idle", [])
	# main gauche au chapeau : bras gauche et tete exacts tant que la main tient le bord
	tient = [(0, 28), (78, 90)]
	finir("Idle", cles, 90, True, "Idle", [], respiration=1.4, contacts={a: tient for a in ("Neck", "LeftShoulder", "LeftElbow", "LeftWrist")})
	apercu("Idle", cles, [0, 6, 33, 36, 45, 62], lambda i: [])
	return cles


def action():
	"""Rafale et coup de poing elastique (150 images, une fois)."""
	n = neutre()
	garde_pieds = ecarte(0.3, dz_d=0.35, dz_g=-0.15)
	# 10 : jambes ecartees, bras en arriere, torse penche en avant
	elan = planter(avec(n, RootPos=(0, -0.28, 0.05), Root=(-6, 0, 0), Waist=(-18, 0, 0), Neck=(18, 0, 0),
		RightShoulder=(-50, 0, 18), RightElbow=(40, 0, 0), RightWrist=(0, 0, 0),
		LeftShoulder=(-50, 0, -18), LeftElbow=(40, 0, 0), LeftWrist=(0, 0, 0)), garde_pieds)
	hop = planter(avec(n, RootPos=(0, 0.06, 0.02), Waist=(-8, 0, 0), Neck=(8, 0, 0),
		RightShoulder=(-20, 0, 15), RightElbow=(30, 0, 0), RightWrist=(0, 0, 0),
		LeftShoulder=(-20, 0, -15), LeftElbow=(30, 0, 0), LeftWrist=(0, 0, 0)), saut_entre({}, garde_pieds))

	# rafale : un coup toutes les 4 images, bras alternes, bras qui frappe tendu et etire de 1,5 stud
	base_rafale = avec(elan, Waist=(-12, 0, 0), Neck=(12, 0, 0))
	hauteurs = [100, 88, 106, 94, 84, 102, 92, 108, 90, 98, 96]
	cotes = [-6, 8, -2, 4, -8, 6, 0, -4, 8, -6, 2]

	def coup(i):
		droite = i % 2 == 0
		frappe, garde = ("Right", "Left") if droite else ("Left", "Right")
		sf = 1 if frappe == "Right" else -1
		p = dict(base_rafale)
		p[frappe + "Shoulder"] = (hauteurs[i], 0, -sf * (4 + cotes[i] / 2))
		p[frappe + "Elbow"] = (0, 0, 0)
		p[frappe + "Wrist"] = (0, 0, 0)
		p[garde + "Shoulder"] = (35, 0, -sf * 18)  # coude sorti vers l'exterieur (Z+ a droite, Z- a gauche)
		p[garde + "Elbow"] = (115, 0, 0)
		p[garde + "Wrist"] = (0, 0, 0)
		p["Waist"] = (-12, 10 * sf, 0)  # le buste suit le bras qui frappe (droit : vers sa gauche)
		p["Neck"] = (12, -6 * sf, 0)
		p = etirer(p, frappe, 1.5)
		p[garde + "ElbowPos"] = (0, 0, 0)
		return p

	rafale = [(20 + 4 * i, coup(i), "Linear") for i in range(11)]
	fin_rafale = avec(base_rafale, RightShoulder=(35, 0, 20), RightElbow=(115, 0, 0), LeftShoulder=(35, 0, -20), LeftElbow=(115, 0, 0), RightElbowPos=(0, 0, 0), LeftElbowPos=(0, 0, 0))

	# 65-90 : charge ; pied droit plante, genou gauche leve devant, buste tourne de 30 deg vers sa droite, bras
	# droit loin derriere (etire de 1 stud vers l'arriere), bras gauche devant pour l'equilibre
	charge = avec(n, RootPos=(0.12, -0.12, 0.05), Root=(0, -8, 0), Waist=(-4, -24, 0), Neck=(4, 22, 0),
		LeftHip=(80, 0, -5), LeftKnee=(-95, 0, 0), LeftAnkle=(-15, 0, 0),
		RightShoulder=(-58, 0, 22), RightElbow=(20, 0, 0), RightWrist=(-10, 0, 0),
		LeftShoulder=(70, 0, -18), LeftElbow=(25, 0, 0), LeftWrist=(0, 0, 0))
	charge = planter(charge, {"Right": garde_pieds["Right"]}, cotes=("Right",))
	charge = etirer(charge, "Right", 1.0)  # le bras s'allonge vers l'arriere (vers la main)
	debut_charge = avec(charge, Waist=(-6, -14, 0), Neck=(6, 12, 0))
	debut_charge = etirer(debut_charge, "Right", 0.5)

	def tremble(k):
		p = dict(charge)
		s = 1 if k % 2 == 0 else -1
		r = charge["RightShoulder"]
		p["RightShoulder"] = (r[0] + 2.5 * s, r[1], r[2] - 2 * s)
		p["RightWrist"] = (-10 + 6 * s, 0, 4 * s)
		return etirer(p, "Right", 1.0)

	# 94 : declenchement ; pied gauche pose devant (genou flechi), jambe droite tendue derriere (talon leve), buste
	# penche de 25 deg et revenu face a l'avant, bras droit tendu devant et etire de 3 studs
	fente_pieds = {"Right": pied("Right", dx=0.3, dz=0.35, talon=25), "Left": pied("Left", dx=-0.3, dz=-0.9)}
	frappe = avec(n, RootPos=(0, -0.3, -0.34), Root=(-8, 0, 0), Waist=(-17, 0, 0), Neck=(10, 0, 0),
		RightKnee=(-10, 0, 0), LeftKnee=(-60, 0, 0),
		RightShoulder=(122, 0, -4), RightElbow=(0, 0, 0), RightWrist=(0, 0, 0),
		LeftShoulder=(-45, 0, -22), LeftElbow=(55, 0, 0), LeftWrist=(0, 0, 0))
	frappe = planter(frappe, fente_pieds)
	frappe_3 = etirer(frappe, "Right", 3.0)
	frappe_plus = etirer(frappe, "Right", 3.25)  # petit rebond elastique au bout du coup
	rappel = etirer(frappe, "Right", -0.15)  # petit depassement au retour (l'avant-bras rentre a peine dans la manche)
	frappe_0 = etirer(frappe, "Right", 0.0)
	# 125 : il se redresse, toujours en fente ; 135 : le pied gauche revient (pas en l'air) ; 142 : pieds en place
	redresse = planter(avec(frappe_0, RootPos=(0, -0.18, -0.3), Root=(0, 0, 0), Waist=(-4, 0, 0), Neck=(4, 0, 0),
		RightShoulder=(20, 0, 15), RightElbow=(30, 0, 0), LeftShoulder=(10, 0, -15), LeftElbow=(30, 0, 0)), fente_pieds)
	redresse["RightElbowPos"] = (0, 0, 0)
	pas_retour = planter(avec(redresse, RootPos=(0, -0.05, -0.12)), saut_entre({"Right": pied("Right", dx=0.3, dz=0.35)}, {}, 0.2))
	pas_retour["RightElbowPos"] = (0, 0, 0)
	cles = [
		(0, n, "Cubic"),
		(5, hop, "Cubic"),
		(10, elan, "Cubic"),
		(16, elan, "Cubic"),
	] + rafale + [
		(62, fin_rafale, "Cubic"),
		(67, debut_charge, "Cubic"),
		(75, charge, "Cubic"),
		(80, tremble(0), "Linear"),
		(82, tremble(1), "Linear"),
		(84, tremble(2), "Linear"),
		(86, tremble(3), "Linear"),
		(88, tremble(4), "Linear"),
		(90, charge, "Sortie"),  # depart explosif : le bras est presque tendu en 2 images
		(94, frappe_3, "Sortie"),
		(98, frappe_plus, "Cubic"),
		(104, frappe_3, "Cubic"),
		(112, frappe_3, "Entree"),  # le bras revient en accelerant (elastique relache)
		(115, rappel, "Rebond"),
		(118, frappe_0, "Cubic"),
		(125, redresse, "Cubic"),
		(133, pas_retour, "Cubic"),
		(141, n, "Cubic"),
		(150, n, "Cubic"),
	]
	# toutes les poses ont une translation de coude (interpolation de l'etirement)
	for f, p, _ in cles:
		p.setdefault("RightElbowPos", (0, 0, 0))
		p.setdefault("LeftElbowPos", (0, 0, 0))
		p.setdefault("RootPos", (0, 0, 0))
	marqueurs = [
		{"image": 20, "nom": "VFX", "valeur": "Rafale"},
		{"image": 70, "nom": "VFX", "valeur": "Charge_Poing"},
		{"image": 94, "nom": "VFX", "valeur": "Poing_Elastique"},
		{"image": 98, "nom": "VFX", "valeur": "Impact_Final"},
	]
	cfs = fk(frappe_3)
	print("poing a l'impact", np.round(cfs["RightHand"][:3, 3], 2), "LowerTorso", np.round(cfs["LowerTorso"][:3, 3] - REPOS["LowerTorso"][:3, 3], 2))
	verifier_anim("Action", cles, 150)
	raccord(cles, n)
	ecrire("Action", cles, 150, False, "Action", marqueurs)
	secousses = [(20 + 8 * i, 5, 1.2) for i in range(6)] + [(94, 18, 4.5)]
	# retour de la main gauche au chapeau (133-150) : bras gauche et tete exacts
	finir("Action", cles, 150, False, "Action", marqueurs, secousses=secousses, contacts={a: [(130, 150)] for a in ("Neck", "LeftShoulder", "LeftElbow", "LeftWrist")})
	apercu("Action", cles, [0, 10, 24, 75, 94, 115, 133], lambda i: [])
	return cles


def main_sur_bras(pose):
	"""Main gauche posee sur la face interieure du haut du bras droit leve : grille d'angles (l'IK restait bloquee par
	le torse ; bras croise devant la poitrine, chevauchement ~0,3 avec le torse comme des bras croises en blocs)."""
	import itertools

	meilleur = None
	for x, y, z, e in itertools.product(range(30, 121, 15), range(-60, 61, 30), range(0, 91, 15), range(0, 121, 20)):
		q = avec(pose, LeftShoulder=(x, y, z), LeftElbow=(e, 0, 0), LeftWrist=(0, 0, 0))
		c = fk(q)
		loc = (np.linalg.inv(c["RightUpperArm"]) @ np.append(c["LeftHand"][:3, 3], 1))[:3]
		dist = float(np.linalg.norm(np.maximum(np.abs(loc) - TAILLES["RightUpperArm"] / 2, 0)))
		pen = 0.0
		for b in ("LeftUpperArm", "LeftLowerArm", "LeftHand"):
			pts = points_boite(TAILLES[b], c[b], 3)
			for o in ("UpperTorso", "Head", "RightUpperArm", "RightLowerArm"):
				pen = max(pen, penetration(pts, TAILLES[o], c[o], 0.0))
		cout = dist + 2 * max(0.0, pen - 0.12) + (0.3 if loc[0] > -0.3 else 0)  # cote interieur du bras
		if meilleur is None or cout < meilleur[0]:
			meilleur = (cout, q, round(dist, 3), round(pen, 3), np.round(loc, 2))
	print("   main gauche sur le biceps : distance %.3f, chevauchement %.3f, position dans le bras %s" % meilleur[2:])
	return meilleur[1]


def signature():
	"""Bras de Haki (120 images, une fois)."""
	n = neutre()
	pieds = ecarte(0.3)
	# 15 : pieds ecartes, bras droit leve devant, coude a 90 deg (avant-bras vertical, poing a hauteur du visage),
	# main gauche posee sur le biceps droit, menton baisse
	# buste tourne vers sa droite, tete face a l'avant : le poing leve passe a cote du visage au lieu de le cacher
	pose = planter(avec(n, RootPos=(0, -0.2, 0), Root=(0, 0, 0), Waist=(-4, -14, 0), Neck=(-14, 14, 0),
		RightShoulder=(88, 0, -8), RightElbow=(92, 0, 0), RightWrist=(0, 0, 0)), pieds)
	pose = main_sur_bras(pose)
	cfs = fk(pose)
	print("poing droit", np.round(cfs["RightHand"][:3, 3], 2), "tete", np.round(cfs["Head"][:3, 3], 2))
	hop = planter(avec(n, RootPos=(0, 0.06, 0), LeftShoulder=(25, 0, -25), LeftElbow=(40, 0, 0), LeftWrist=(0, 0, 0)), saut_entre({}, pieds))
	# 30 : le Haki : petit tassement (energie), le poing se serre
	tasse = planter(avec(pose, RootPos=(0, -0.28, 0), Neck=(-16, 14, 0)), pieds)

	def tremble(k):
		s = 1 if k % 2 == 0 else -1
		p = dict(tasse)
		p["RightWrist"] = (5 * s, 3 * s, -4 * s)
		e = tasse["RightElbow"]
		p["RightElbow"] = (e[0] + 2 * s, 0, 0)
		return p

	# 90 : il secoue son bras (baisse sur le cote) et sourit (tete relevee et penchee)
	def secoue(s):
		p = avec(pose, RootPos=(0, -0.12, 0), Waist=(0, 0, 0), Neck=(10, 4, 8 * s),
			RightShoulder=(15, 0, 28 + 8 * s), RightElbow=(45 - 25 * s, 0, 0), RightWrist=(20 * s, 0, 0))
		return tient_chapeau(planter(p, pieds))

	sec = [secoue(1), secoue(-1)]
	cles = [
		(0, n, "Cubic"),
		(7, hop, "Cubic"),
		(15, pose, "Cubic"),
		(26, pose, "Cubic"),
		(30, tasse, "Linear"),
	] + [(33 + 4 * k, tremble(k), "Linear") for k in range(13)] + [
		(85, tasse, "Cubic"),
		(90, sec[0], "Linear"),
		(94, sec[1], "Linear"),
		(98, sec[0], "Linear"),
		(102, sec[1], "Cubic"),
		(110, planter(avec(n, RootPos=(0, 0.06, 0)), saut_entre({}, pieds)), "Cubic"),
		(120, n, "Cubic"),
	]
	for f, p, _ in cles:
		p.setdefault("RootPos", (0, 0, 0))
	marqueurs = [
		{"image": 30, "nom": "Montrer", "valeur": "Acc_Haki"},
		{"image": 31, "nom": "Montrer", "valeur": "Acc_Haki_Main"},
		{"image": 30, "nom": "VFX", "valeur": "Eclairs_Haki"},
		{"image": 31, "nom": "VFX", "valeur": "Onde_Haki"},
		{"image": 90, "nom": "VFX", "valeur": "Eclairs_Haki_Fin"},
		{"image": 90, "nom": "Cacher", "valeur": "Acc_Haki"},
		{"image": 91, "nom": "Cacher", "valeur": "Acc_Haki_Main"},
	]
	verifier_anim("Signature", cles, 120)
	raccord(cles, n)
	ecrire("Signature", cles, 120, False, "Action", marqueurs)
	# main gauche sur le biceps droit (15-85) puis au chapeau (90-102) ; la secousse du Haki part a 30
	gauche = [(15, 85), (88, 104)]
	finir("Signature", cles, 120, False, "Action", marqueurs, secousses=[(30, 14, 2.5)],
		contacts={**{a: gauche for a in ("LeftShoulder", "LeftElbow", "LeftWrist")}, "Neck": [(88, 104)], **{a: [(26, 85)] for a in ("RightShoulder", "RightElbow", "RightWrist")}})
	apercu("Signature", cles, [0, 15, 30, 61, 94], lambda i: ["Acc_Haki", "Acc_Haki_Main"] if 30 <= i < 90 else [])
	return cles


if __name__ == "__main__":
	quoi = sys.argv[1] if len(sys.argv) > 1 else "Idle"
	{"Idle": idle, "Action": action, "Signature": signature}[quoi]()
