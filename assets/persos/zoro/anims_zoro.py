"""Animations de vitrine de zoro (Idle, Action, Signature), calculees sur le rig du mannequin R15.

Sortie : assets/persos/zoro/anims/zoro_<Nom>.json (source de verite), construits ensuite en KeyframeSequence dans Studio.
Repere Studio : +X = droite du perso, +Y = haut, +Z = arriere. Une pose = Motor6D.Transform par articulation,
donnee en angles (degres) : Transform = CFrame.Angles(rx, ry, rz) (= Rx * Ry * Rz), plus la translation de Root.
Sens des axes : assets/persos/_mannequin/axes_r15.json.

Usage : uv run --with numpy --with scipy assets/persos/zoro/anims_zoro.py [Idle|Action|Signature]
"""

import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).parent.parent / "_anim"))
import finition  # noqa: E402

DOSSIER = Path(__file__).parent
RIG = json.loads((DOSSIER.parent / "_mannequin" / "v1" / "r15_bloc.json").read_text(encoding="utf-8"))  # zoro est construit sur le mannequin v1
ACC = json.loads((DOSSIER / "accessoires.json").read_text(encoding="utf-8"))
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


def tr(x, y, z):
	m = np.eye(4)
	m[:3, 3] = (x, y, z)
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


def vers_douze(m):
	return [round(float(v), 6) for v in list(m[:3, 3]) + list(m[:3, :3].reshape(9))]


MOTEURS = {k: (v["part0"], v["part1"], cf(v["c0"]), cf(v["c1"])) for k, v in RIG["motors"].items()}
# boites visibles en repere local de chaque piece (centre de piece au repos)
BOITES = {}
for nom, (bx, by, bz) in ((k, v) for k, v in RIG["blocs_visibles"].items() if isinstance(v, list)):
	c = RIG["pieces"][nom]["cframe"][:3]
	BOITES[nom] = (np.array([bx[0], by[0], bz[0]]) - c, np.array([bx[1], by[1], bz[1]]) - c)
# tete classique (cylindre arrondi) : boite englobante, centre 0,02 au-dessus de la piece Head
BOITES["Head"] = (np.array([-0.595, -0.605, -0.595]), np.array([0.595, 0.645, 0.595]))


def transform(pose, art):
	"""Transform d'une articulation : angles + translation eventuelle (cle '<art>Pos' : Root, et epaules pour l'effet elastique)."""
	rx, ry, rz = pose.get(art, (0, 0, 0))[:3]
	m = angles(math.radians(rx), math.radians(ry), math.radians(rz))
	if art + "Pos" in pose:
		m[:3, 3] = pose[art + "Pos"]
	return m


def fk(pose):
	"""CFrame de chaque piece, relatif au HumanoidRootPart (identite)."""
	cfs = {"HumanoidRootPart": np.eye(4)}
	reste = list(MOTEURS)
	while reste:
		for art in list(reste):
			p0, p1, c0, c1 = MOTEURS[art]
			if p0 in cfs:
				cfs[p1] = cfs[p0] @ c0 @ transform(pose, art) @ np.linalg.inv(c1)
				reste.remove(art)
	return cfs


# ---------------------------------------------------------------- volumes pour les verifications


def points_boite(nom, cfm, pas=5):
	lo, hi = BOITES[nom]
	pts = []
	for i in range(pas):
		for j in range(pas):
			for k in range(pas):
				if 0 < i < pas - 1 and 0 < j < pas - 1 and 0 < k < pas - 1:
					continue  # surface seulement
				p = lo + (hi - lo) * np.array([i, j, k]) / (pas - 1)
				pts.append((cfm @ np.append(p, 1))[:3])
	return np.array(pts)


def dans_boite(pts, nom, cfm, marge=0.03):
	"""Profondeur de penetration maximale de points dans la boite visible d'une piece."""
	lo, hi = BOITES[nom]
	loc = (np.linalg.inv(cfm) @ np.c_[pts, np.ones(len(pts))].T).T[:, :3]
	d = np.minimum(loc - (lo + marge), (hi - marge) - loc).min(axis=1)
	return max(0.0, float(d.max()))


def blender_vers_roblox(p, H=3.192428):
	return np.array([-p[0], p[2] - H, p[1]])


# manteau : rangs (y Roblox, demi-largeur x, demi-profondeur z), dans le repere du LowerTorso au repos (centre y = -0.8)
MANTEAU = [(z - 3.192428 + 0.8, ax * 1.07, ay * 1.07) for z, ax, ay, _, _ in [(2.47, 1.12, 0.63, 0, 0), (2.44, 1.03, 0.535, 0, 0), (2.20, 1.09, 0.59, 0, 0), (1.85, 1.18, 0.68, 0, 0), (1.40, 1.29, 0.79, 0, 0), (0.95, 1.38, 0.88, 0, 0), (0.70, 1.42, 0.92, 0, 0)]]
MANTEAU.sort(key=lambda r: -r[0])


def dans_manteau(pts, cf_lt):
	loc = (np.linalg.inv(cf_lt) @ np.c_[pts, np.ones(len(pts))].T).T[:, :3]
	pire = 0.0
	for x, y, z in loc:
		for (y0, ax0, az0), (y1, ax1, az1) in zip(MANTEAU, MANTEAU[1:]):
			if y1 <= y <= y0:
				t = (y0 - y) / (y0 - y1)
				ax, az = ax0 + (ax1 - ax0) * t, az0 + (az1 - az0) * t
				v = (abs(x) / ax) ** 4 + (abs(z) / az) ** 4
				if v < 1:
					pire = max(pire, (1 - v) * min(ax, az) * 0.25)
	return pire


# fourreaux et poignees a la hanche : segments (Roblox, repere LowerTorso au repos)
FOURREAUX_B = [((-1.25, -0.62, 2.12), (-0.25, 0.80, -0.60)), ((-1.41, -0.56, 2.08), (-0.25, 0.84, -0.53)), ((-1.57, -0.50, 2.04), (-0.25, 0.88, -0.46))]  # = FOURREAUX de accessoires_zoro.py
SEGMENTS_HANCHE = []
for g, d in FOURREAUX_B:
	g = blender_vers_roblox(np.array(g)) - np.array([0, -0.8, 0])
	d = np.array([-d[0], d[2], d[1]])
	d = d / np.linalg.norm(d)
	SEGMENTS_HANCHE.append((g - d * 1.04, g + d * 2.15))


def dist_segment(p, a, b):
	ab = b - a
	t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
	return np.linalg.norm(p - (a + ab * t))


def dans_fourreaux(pts, cf_lt, rayon=0.14):
	loc = (np.linalg.inv(cf_lt) @ np.c_[pts, np.ones(len(pts))].T).T[:, :3]
	pire = 0.0
	for p in loc:
		for a, b in SEGMENTS_HANCHE:
			pire = max(pire, rayon - dist_segment(p, a, b))
	return pire


BRAS = ["RightUpperArm", "RightLowerArm", "RightHand", "LeftUpperArm", "LeftLowerArm", "LeftHand"]


def verifier(pose, avec_hanche=True):
	"""Penetrations (studs) des bras dans le torse, la tete, le manteau, les fourreaux ; deplacement du LowerTorso."""
	cfs = fk(pose)
	res = {}
	for b in BRAS:
		pts = points_boite(b, cfs[b])
		res[b + ">torse"] = max(dans_boite(pts, "UpperTorso", cfs["UpperTorso"]), dans_boite(pts, "LowerTorso", cfs["LowerTorso"]))
		res[b + ">manteau"] = dans_manteau(pts, cfs["LowerTorso"])
		if avec_hanche and b.startswith("Right"):
			res[b + ">fourreaux"] = dans_fourreaux(pts, cfs["LowerTorso"])
	repos = fk({})
	res["deplacement_LowerTorso"] = float(np.linalg.norm(cfs["LowerTorso"][:3, 3] - repos["LowerTorso"][:3, 3]))
	return res


def centre(pose, piece):
	return fk(pose)[piece][:3, 3]


def axe(pose, piece, i=1):
	return fk(pose)[piece][:3, i]


# ---------------------------------------------------------------- IK numerique


def resoudre(pose, variables, cout, bornes=None):
	"""Optimise les angles listes [(articulation, axe)] pour minimiser cout(pose) ; renvoie la pose completee."""
	x0 = [pose.get(a, (0, 0, 0))[k] for a, k in variables]

	def appliquer(x):
		p = {k: (list(v) if isinstance(v, (tuple, list)) else v) for k, v in pose.items()}
		for (a, k), val in zip(variables, x):
			v = list(p.get(a, [0, 0, 0]))
			v[k] = val
			p[a] = v
		return p

	b = bornes or []
	if not b:
		for a, k in variables:
			lim = next((mn, mx) for ax, mn, mx in LIMITES.get(a, [(k, -180, 180)]) if ax == k) if a in LIMITES else (-180, 180)
			b.append(lim)
	r = minimize(lambda x: cout(appliquer(x)), x0, bounds=b, method="L-BFGS-B", options={"maxiter": 400})
	return {k: (tuple(round(float(c), 2) for c in v) if isinstance(v, list) else v) for k, v in appliquer(r.x).items()}, r.fun


# ---------------------------------------------------------------- poses


def neutre():
	"""Image 0 de l'Idle : debout, jambes un peu ecartees, bras le long du corps ecartes de 6 deg (manteau)."""
	return {
		"RightShoulder": (0, 0, 6),
		"LeftShoulder": (0, 0, -6),
		"RightHip": (0, 0, 4),
		"LeftHip": (0, 0, -4),
		"RightAnkle": (0, 0, -4),
		"LeftAnkle": (0, 0, 4),
	}


def euler_de(m3):
	"""Angles (degres) tels que CFrame.Angles(rx, ry, rz) = m3 ; verifie la reconstruction (blocage de cardan compris)."""
	import warnings

	from scipy.spatial.transform import Rotation as R

	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		e = tuple(round(float(v), 3) for v in R.from_matrix(m3).as_euler("XYZ", degrees=True))
	ecart = np.abs(angles(*np.radians(e))[:3, :3] - m3).max()
	assert ecart < 1e-3, f"angles mal reconstruits ({ecart})"
	return e


def bras_dirige(pose, cote, u, f, avance=0.0, descente=0.0):
	"""Construit le bras a partir de deux directions monde : u = haut du bras (epaule -> coude),
	f = avant-bras (coude -> main). Le coude ne plie que sur X+ : son axe est impose par u et f.
	avance = translation de l'epaule vers l'avant (effet elastique)."""
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
	p[S + "Pos"] = (0.0, -descente, -avance)
	R_ut = fk(p)["UpperTorso"][:3, :3]
	p[S] = euler_de(R_ut.T @ R_u)
	p[E] = (round(math.degrees(theta), 2), 0, 0)
	p[W] = (0, 0, 0)
	return p


def chercher_bras(pose, cote, y_cible, z_cible, tolerance=0.0, avances=(0.0, 0.15, 0.3, 0.45), descentes=(0.0,)):
	"""Grille sur les directions du bras et la translation de l'epaule (avancee, descente) : main au-dela du milieu,
	avant-bras a la hauteur et a la profondeur voulues, sans traverser le torse (au-dela de la tolerance) ;
	translation la plus faible possible."""
	sx = 1 if cote == "Right" else -1  # vers l'interieur = -sx
	meilleur = (1e9, None, None)
	grille = itertools.product((30, 45, 60, 70, 80, 88), (0, 15, 30, 45), (0, 10, 20, 30), (-10, 0, 10), avances, descentes)
	for el, az, fy, fp, av, de in grille:
		el_r, az_r, fy_r, fp_r = (math.radians(v) for v in (el, az, fy, fp))
		u = (-sx * math.sin(az_r) * math.cos(el_r), -math.sin(el_r), -math.cos(az_r) * math.cos(el_r))
		f = (-sx * math.cos(fy_r) * math.cos(fp_r), -math.sin(fp_r), -math.sin(fy_r) * math.cos(fp_r))
		p = bras_dirige(pose, cote, u, f, av, de)
		if p is None:
			continue
		cfs = fk(p)
		pen = 0.0
		for b in (cote + "UpperArm", cote + "LowerArm", cote + "Hand"):
			pts = points_boite(b, cfs[b], 3)
			pen += dans_boite(pts, "UpperTorso", cfs["UpperTorso"], 0.0) + dans_boite(pts, "LowerTorso", cfs["LowerTorso"], 0.0)
		main = cfs[cote + "Hand"][:3, 3]
		ab = cfs[cote + "LowerArm"][:3, 3]
		coude = p[cote + "Elbow"][0]
		cout = 1000 * max(0.0, pen - tolerance) + 5 * pen + 10 * max(0.0, sx * main[0] + 0.1) + 4 * (ab[1] - y_cible) ** 2 + 8 * (ab[2] - z_cible) ** 2 + av + de + 0.0001 * (coude - 95) ** 2
		if cout < meilleur[0]:
			meilleur = (cout, p, dict(el=el, az=az, fy=fy, fp=fp, avance=av, descente=de, penetration=round(pen, 3), main=np.round(main, 2).tolist(), avant_bras=np.round(ab, 2).tolist()))
	return meilleur


def apercu(nom, cles, images):
	"""Poses completes a quelques images, pour l'apercu Blender et les clones Studio."""
	sortie = {str(i): {art: vers_douze(transform(pose_a(cles, i), art)) for art in ARTICULATIONS} for i in images}
	(DOSSIER / "anims" / f"apercu_{nom}.json").write_text(json.dumps(sortie), encoding="utf-8")


# ---------------------------------------------------------------- animation


def lisser(t, easing):
	return finition.courbe(t, easing)


def slerp_pose(pa, pb, t):
	"""Interpolation de deux poses (angles interpoles par quaternions, comme Studio)."""
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
		# retour en angles CFrame.Angles (Rx*Ry*Rz = 'XYZ' intrinseque)
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


def verifier_anim(nom, cles, n_images, avec_hanche=True):
	pire = {}
	for i in range(0, n_images + 1):
		r = verifier(pose_a(cles, i), avec_hanche)
		for k, v in r.items():
			if v > pire.get(k, (0, -1))[0]:
				pire[k] = (v, i)
	print(f"--- verification {nom} (pire valeur, image)")
	for k, (v, i) in sorted(pire.items()):
		if v > 0.005:
			print(f"  {k}: {v:.3f} (image {i})")


def finir(nom, cles, n_images, boucle, priorite, marqueurs, **reglages):
	"""Version finie (assets/persos/_anim/finition.py) : verifiee sur chaque image, ecrite dans anims/zoro_<Nom>_fini.json."""
	toutes, gardees = finition.finir(cles, n_images, ARTICULATIONS, boucle=boucle, limites=LIMITES, **reglages)
	verifier_anim(nom + "_fini", toutes, n_images, avec_hanche=False)
	if nom == "Idle":
		verifier_lames(nom + "_fini", toutes, n_images, depuis={"Right": 15, "Left": 22})
	elif nom == "Action":
		verifier_lames(nom + "_fini", toutes, n_images, depuis={"Right": 0, "Left": 0})
	elif nom == "Signature":
		verifier_lames(nom + "_fini", toutes, 44, depuis={"Right": 0, "Left": 0})  # lames rangees au clac (45)
	ecrire(nom + "_fini", gardees, n_images, boucle, priorite, marqueurs)
	return toutes


def ecrire(nom, cles, n_images, boucle, priorite, marqueurs):
	donnees = {
		"nom": "zoro_" + nom,
		"images": n_images,
		"fps": FPS,
		"duree": round(n_images / FPS, 4),
		"boucle": boucle,
		"priorite": priorite,
		"repere": "Pose.CFrame = Motor6D.Transform ; angles en degres, CFrame.Angles(rx, ry, rz) ; cframe = 12 composantes",
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
	(DOSSIER / "anims").mkdir(exist_ok=True)
	(DOSSIER / "anims" / f"zoro_{nom}.json").write_text(json.dumps(donnees, indent="\t", ensure_ascii=False), encoding="utf-8")
	print("ecrit", f"anims/zoro_{nom}.json", len(cles), "cles")


# ---------------------------------------------------------------- sabres tenus, bras vises, pieds plantes

# lame d'un sabre tenu, dans le repere de la main (garde devant le poing, pointe 2,3 plus loin, courbe vers le haut)
LAME_MAIN = np.array([(0.0, 0.004 + 0.10 * t * t, -0.59 - 2.36 * t) for t in np.linspace(0, 1, 9)])
CORPS = ["UpperTorso", "LowerTorso", "Head", "RightUpperLeg", "LeftUpperLeg", "RightLowerLeg", "LeftLowerLeg"]
INV_C1 = {k: np.linalg.inv(c1) for k, (_, _, _, c1) in MOTEURS.items()}


def lame_monde(cfs, cote):
	m = cfs[cote + "Hand"]
	return (m @ np.c_[LAME_MAIN, np.ones(len(LAME_MAIN))].T).T[:, :3]


def lame_dans_corps(cfs, cote):
	pts = lame_monde(cfs, cote)
	return max(dans_boite(pts, b, cfs[b], 0.0) for b in CORPS)


def chaine_bras(cfs, pose, cote):
	"""Recalcule seulement le bras (plus rapide que fk complet)."""
	out = dict(cfs)
	for art, p0, p1 in ((cote + "Shoulder", "UpperTorso", cote + "UpperArm"), (cote + "Elbow", cote + "UpperArm", cote + "LowerArm"), (cote + "Wrist", cote + "LowerArm", cote + "Hand")):
		out[p1] = out[p0] @ MOTEURS[art][2] @ transform(pose, art) @ INV_C1[art]
	return out


def bras_lame(pose, cote, f, lame, theta, R_ut, avance=0.0):
	"""Bras defini par l'avant-bras (direction f, coude -> main), la lame (perpendiculaire a f, choisie par la rotation
	du bras) et l'angle du coude theta (deg). La lame d'un sabre tenu suit -Z de la main."""
	f = np.array(f, float) / np.linalg.norm(f)
	b = np.array(lame, float)
	b = b - f * np.dot(f, b)
	if np.linalg.norm(b) < 1e-6:
		return None
	b = b / np.linalg.norm(b)
	x = np.cross(f, b)
	R_l = np.column_stack([x, -f, -b])
	R_u = R_l @ angles(-math.radians(theta), 0, 0)[:3, :3]
	p = dict(pose)
	p[cote + "Shoulder"] = euler_de(R_ut.T @ R_u)
	p[cote + "ShoulderPos"] = (0.0, 0.0, -avance)
	p[cote + "Elbow"] = (round(theta, 3), 0, 0)
	p[cote + "Wrist"] = (0, 0, 0)
	return p


def viser(pose, cote, main=None, lame=None, sabre=True, avances=(0.0, 0.2), poids_main=10.0, coude=None, tolerance_epaule=0.0):
	"""Cherche le bras qui amene le centre de la main sur 'main' et la lame dans la direction 'lame',
	sans que le bras traverse le torse ni que la lame traverse le corps. coude = angle voulu (bras tendu) ;
	tolerance_epaule = recouvrement admis du haut du bras dans le torse (pivot d'epaule a l'interieur du torse). Grille puis affinage."""
	cfs0 = fk(pose)
	R_ut = cfs0["UpperTorso"][:3, :3]
	main = None if main is None else np.array(main, float)
	lame = None if lame is None else np.array(lame, float) / np.linalg.norm(lame)

	def evaluer(yaw, pitch, roll, theta, av):
		f = np.array([math.cos(pitch) * math.sin(yaw), math.sin(pitch), -math.cos(pitch) * math.cos(yaw)])
		# deux vecteurs perpendiculaires a f, la lame tourne autour de f (roll)
		a = np.cross(f, [0, 1, 0]) if abs(f[1]) < 0.95 else np.cross(f, [1, 0, 0])
		a /= np.linalg.norm(a)
		c = np.cross(a, f)
		bl = math.cos(roll) * c + math.sin(roll) * a
		p = bras_lame(pose, cote, f, bl, theta, R_ut, av)
		if p is None:
			return 1e9, None
		cfs = chaine_bras(cfs0, p, cote)
		cout = 0.3 * av
		if coude is not None:
			cout += 0.004 * (theta - coude) ** 2
		if main is not None:
			cout += poids_main * np.sum((cfs[cote + "Hand"][:3, 3] - main) ** 2)
		if lame is not None:
			cout += 3 * (1 - float(np.dot(-cfs[cote + "Hand"][:3, 2], lame)))
		pen = 0.0
		for bo in (cote + "UpperArm", cote + "LowerArm", cote + "Hand"):
			pts = points_boite(bo, cfs[bo], 3)
			torse = dans_boite(pts, "UpperTorso", cfs["UpperTorso"], 0.0)
			if bo.endswith("UpperArm"):
				torse = max(0.0, torse - tolerance_epaule)
			pen += torse + dans_boite(pts, "LowerTorso", cfs["LowerTorso"], 0.0) + dans_boite(pts, "Head", cfs["Head"], 0.0)
		cout += 200 * pen
		if sabre:
			cout += 100 * lame_dans_corps(cfs, cote)
		return cout, p

	meilleur = (1e9, None, None)
	for yaw in np.radians(np.arange(-180, 180, 30)):
		for pitch in np.radians(np.arange(-75, 76, 25)):
			for roll in np.radians(np.arange(0, 360, 45)):
				for theta in (8, 40, 75, 110):
					for av in avances:
						c, p = evaluer(yaw, pitch, roll, theta, av)
						if c < meilleur[0]:
							meilleur = (c, p, (yaw, pitch, roll, theta, av))
	# affinage autour du meilleur point de grille
	x0 = np.array(meilleur[2][:4])
	av = meilleur[2][4]
	r = minimize(lambda x: evaluer(x[0], x[1], x[2], float(np.clip(x[3], 5, 140)), av)[0], x0, method="Nelder-Mead", options={"xatol": 1e-3, "fatol": 1e-5, "maxiter": 600})
	c, p = evaluer(r.x[0], r.x[1], r.x[2], float(np.clip(r.x[3], 5, 140)), av)
	if c > meilleur[0]:
		c, p = meilleur[0], meilleur[1]
	cfs = fk(p)
	info = {"cout": round(float(c), 3), "main": np.round(cfs[cote + "Hand"][:3, 3], 2).tolist(), "lame": np.round(-cfs[cote + "Hand"][:3, 2], 2).tolist(), "coude": p[cote + "Elbow"][0]}
	return p, info


PIEDS_REPOS = None


def planter(pose):
	"""Ajuste hanches, genoux et chevilles pour que chaque pied garde sa place et son orientation de la pose neutre."""
	global PIEDS_REPOS
	if PIEDS_REPOS is None:
		r = fk(neutre())
		PIEDS_REPOS = {c: r[c + "Foot"] for c in ("Right", "Left")}
	p = dict(pose)
	for c in ("Right", "Left"):
		# depart genou flechi : genou tendu, la hauteur du pied ne varie pas au premier ordre (l'optimiseur resterait bloque)
		hx, hy, hz = p.get(c + "Hip", (0, 0, 0))[:3]
		p[c + "Hip"], p[c + "Knee"], p[c + "Ankle"] = (hx + 12, hy, hz), (-25, 0, 0), (12, 0, -hz)
		variables = [(c + "Hip", 0), (c + "Hip", 1), (c + "Hip", 2), (c + "Knee", 0), (c + "Ankle", 0), (c + "Ankle", 1), (c + "Ankle", 2)]
		cible = PIEDS_REPOS[c]

		def cout(q, c=c, cible=cible):
			m = fk(q)[c + "Foot"]
			return 50 * np.sum((m[:3, 3] - cible[:3, 3]) ** 2) + 5 * np.sum((m[:3, :3] - cible[:3, :3]) ** 2)

		bornes = [(-90, 90), (-30, 30), (-40, 40), (-150, 0), (-30, 30), (-30, 30), (-30, 30)]
		p, _ = resoudre(p, variables, cout, bornes)
	return p


# ---------------------------------------------------------------- jeu de jambes (Action)

N_IDLE = 150
N_ACTION = 120
LARGE = {"Right": (0.25, 0, 0.1, 12), "Left": (-0.25, 0, -0.1, -12)}  # pieds ecartes pour les grands balayages
FENTE = {"Right": (0.3, 0, 0.45, 20), "Left": (-0.3, 0, -0.85, -10)}  # pied gauche devant, pied droit en arriere
NEUTRES = {"Right": (0, 0, 0, 0), "Left": (0, 0, 0, 0)}
# pieds de l'Action par image : {cote: (dx, dy, dz, lacet, tangage)} par rapport au pied de la pose neutre (dy > 0 =
# en l'air, tangage < 0 = pointe vers le bas) ; entre deux cles au sol, le pied qui se deplace decrit un arc.
PAS = [
	(0, NEUTRES, "Cubic"),
	(8, LARGE, "Cubic"),
	(46, LARGE, "Sortie"),
	(53, FENTE, "Cubic"),
	(92, FENTE, "Cubic"),
	(106, NEUTRES, "Cubic"),
	(N_ACTION, NEUTRES, "Cubic"),
]


def pieds_a(image, pas=None):
	"""Cibles des pieds a une image, interpolees entre les cles de pas (PAS par defaut ; arc de 0,3 x la distance, au plus 0,4 stud)."""
	pas = pas or PAS
	for (fa, pa, ea), (fb, pb, _) in zip(pas, pas[1:]):
		if fa <= image <= fb:
			t = lisser(0 if fb == fa else (image - fa) / (fb - fa), ea)
			s = 0 if fb == fa else (image - fa) / (fb - fa)
			out = {}
			for c in ("Right", "Left"):
				a = np.array((list(pa[c]) + [0])[:5], float)
				b = np.array((list(pb[c]) + [0])[:5], float)
				v = a + (b - a) * t
				if a[1] == 0 and b[1] == 0:
					v[1] = min(0.4, 0.3 * float(np.linalg.norm(b[[0, 2]] - a[[0, 2]]))) * math.sin(math.pi * s)
				out[c] = v
			return out
	return {c: np.array((list(pas[-1][1][c]) + [0])[:5], float) for c in ("Right", "Left")}


def cible_pied(cote, v):
	if PIEDS_REPOS is None:
		planter(neutre())
	m = PIEDS_REPOS[cote].copy()
	dx, dy, dz, lacet, tangage = v
	m[:3, :3] = angles(0, math.radians(lacet), 0)[:3, :3] @ m[:3, :3] @ angles(math.radians(tangage), 0, 0)[:3, :3]
	m[:3, 3] += (dx, dy, dz)
	return m


JAMBE = {c: [MOTEURS[c + a] for a in ("Hip", "Knee", "Ankle")] for c in ("Right", "Left")}
BORNES_JAMBE = [(-90, 90), (-30, 30), (-40, 40), (-150, 0), (-30, 30), (-30, 30), (-30, 30)]


def pied_fk(lt, cote, x):
	(_, _, c0h, c1h), (_, _, c0k, c1k), (_, _, c0a, c1a) = JAMBE[cote]
	r = np.radians(x)
	m = lt @ c0h @ angles(r[0], r[1], r[2]) @ np.linalg.inv(c1h)
	m = m @ c0k @ angles(r[3], 0, 0) @ np.linalg.inv(c1k)
	return m @ c0a @ angles(r[4], r[5], r[6]) @ np.linalg.inv(c1a)


def ik_jambe(lt, cote, cible, x0):
	cout = lambda x: 50 * np.sum((pied_fk(lt, cote, x)[:3, 3] - cible[:3, 3]) ** 2) + 5 * np.sum((pied_fk(lt, cote, x)[:3, :3] - cible[:3, :3]) ** 2)
	r = minimize(cout, x0, bounds=BORNES_JAMBE, method="L-BFGS-B", options={"maxiter": 400})
	return r.x, float(np.linalg.norm(pied_fk(lt, cote, r.x)[:3, 3] - cible[:3, 3]))


def poser_jambes(p, pieds, depart=None):
	"""Remplace hanches, genoux et chevilles de p pour amener les pieds sur leurs cibles ; renvoie (pose, ecart max)."""
	p = dict(p)
	lt = MOTEURS["Root"][2] @ transform(p, "Root") @ INV_C1["Root"]
	pire = 0.0
	for c in ("Right", "Left"):
		if depart:
			x0 = depart[c]
		else:  # genou flechi : genou tendu, la hauteur du pied ne varie pas au premier ordre
			hx, hy, hz = p.get(c + "Hip", (0, 0, 0))[:3]
			x0 = [hx + 12, hy, hz, -25, 12, 0, -hz]
		x, e = ik_jambe(lt, c, cible_pied(c, pieds[c]), x0)
		x = [round(float(v), 3) for v in x]
		p[c + "Hip"], p[c + "Knee"], p[c + "Ankle"] = tuple(x[:3]), (x[3], 0, 0), tuple(x[4:])
		pire = max(pire, e)
	return p, pire


def deplacer(p, root, image):
	"""Bassin deplace (x, y, z) et tourne (lacet en degres) ; le Waist compense le lacet pour que le buste (et les bras
	vises par construire) garde exactement son orientation ; jambes posees sur les pieds de PAS a cette image."""
	x, y, z, lacet = root
	ut_avant = fk(p)["UpperTorso"]
	q = dict(p)
	q["Root"], q["RootPos"] = (0, lacet, 0), (x, y, z)
	r_root = angles(0, math.radians(lacet), 0)[:3, :3]
	q["Waist"] = euler_de(r_root.T @ angles(*np.radians(p.get("Waist", (0, 0, 0))[:3]))[:3, :3])
	q, ecart = poser_jambes(q, pieds_a(image))
	ut = fk(q)["UpperTorso"]
	dep = np.array([x, y, z]) - np.array(p.get("RootPos", (0, 0, 0)))
	assert np.abs(ut[:3, :3] - ut_avant[:3, :3]).max() < 1e-3 and np.abs(ut[:3, 3] - ut_avant[:3, 3] - dep).max() < 1e-3, "buste deplace"
	print(f"    image {image} : pieds a {ecart:.3f} stud de leur cible")
	return q


def jambes_suivies(images):
	"""Apres la cuisson : jambes recalculees a chaque image pour suivre PAS (pieds plantes, arcs, saut)."""
	depart = None
	pire = (0.0, -1)
	sortie = []
	for i, p in enumerate(images):
		if i in (0, len(images) - 1):  # raccords exacts avec l'Idle et la Signature
			q, e = p, 0.0
		else:
			q, e = poser_jambes(p, pieds_a(i), depart)
		depart = {c: [*q[c + "Hip"], q[c + "Knee"][0], *q[c + "Ankle"]] for c in ("Right", "Left")}
		pire = max(pire, (e, i))
		sortie.append(q)
	print(f"--- jambes suivies : pire ecart des pieds {pire[0]:.3f} stud (image {pire[1]})")
	return sortie


# ---------------------------------------------------------------- Action et Signature


def corps(base, root=(0, 0, 0), root_pos=(0, 0, 0), waist=(0, 0, 0), neck=(0, 0, 0)):
	p = dict(base)
	p["Root"], p["RootPos"], p["Waist"], p["Neck"] = root, root_pos, waist, neck
	return p


def ajuster_poignet(p, cote, lame):
	"""Tourne le poignet (+/- 30 deg sur chaque axe) pour aligner la lame, sans qu'elle traverse le corps."""
	lame = np.array(lame, float) / np.linalg.norm(lame)

	def cout(q):
		cfs = fk(q)
		return 3 * (1 - float(np.dot(-cfs[cote + "Hand"][:3, 2], lame))) + 100 * lame_dans_corps(cfs, cote)

	return resoudre(p, [(cote + "Wrist", 0), (cote + "Wrist", 1), (cote + "Wrist", 2)], cout)[0]


BRAS_TENDU = 1.78  # pivot de l'epaule -> centre de la main, coude droit


def construire(base, bras):
	"""bras = {cote: dict(main=... ou dir=..., lame=..., sabre=bool)} ; renvoie la pose avec pieds plantes."""
	p = planter(base)
	for cote, spec in bras.items():
		spec = dict(spec)
		if "dir" in spec:  # bras tendu : main a BRAS_TENDU du pivot de l'epaule, dans cette direction (monde)
			d = np.array(spec.pop("dir"), float)
			pivot = (fk(p)["UpperTorso"] @ MOTEURS[cote + "Shoulder"][2])[:3, 3]
			spec["main"] = pivot + BRAS_TENDU * d / np.linalg.norm(d)
			spec.setdefault("coude", 6)
			spec.setdefault("tolerance_epaule", 0.15)  # bras leve sur le cote : le haut du bras entre un peu dans l'epaule
		p, info = viser(p, cote, **spec)
		if spec.get("lame") is not None and spec.get("sabre", True):
			p = ajuster_poignet(p, cote, spec["lame"])
			info["lame_apres_poignet"] = np.round(-fk(p)[cote + "Hand"][:3, 2], 2).tolist()
			info["poignet"] = p[cote + "Wrist"]
		print("   ", cote, info)
	return p


def verifier_lames(nom, cles, n_images, depuis):
	pire = {}
	for i in range(n_images + 1):
		cfs = fk(pose_a(cles, i))
		for cote, d in depuis.items():
			if i >= d:
				v = lame_dans_corps(cfs, cote)
				if v > pire.get(cote, (0, -1))[0]:
					pire[cote] = (v, i)
	print(f"--- lames {nom} (penetration dans le corps, pire image) :", {k: (round(v, 3), i) for k, (v, i) in pire.items()})


def haki(n, bras=(0.75, -0.62, -0.22), lame=(0.85, 0.45, 0.25), waist=(-5, 0, 0), neck=(-6, 0, 0), root_y=-0.15):
	"""Pose de la reference : bras tendus vers le bas et l'exterieur, lames vers l'exterieur et le haut (un peu en
	arriere), sabre a la bouche, buste un peu penche, tete baissee (regard par en dessous). Pieds a leur place."""
	b = corps(n, root_pos=(0, root_y, 0), waist=waist, neck=neck)
	miroir = lambda v: (-v[0], v[1], v[2])
	return construire(b, {"Right": dict(dir=bras, lame=lame), "Left": dict(dir=miroir(bras), lame=miroir(lame))})


def degainage(n):
	"""Les trois sabres : main droite sur les poignees, degaine a droite, puis a gauche, sabre a la bouche."""
	print("10 main droite sur les poignees")
	p10 = construire(corps(n, root_pos=(0, -0.05, 0), waist=(0, -10, 0)), {"Right": dict(main=(1.45, -0.72, -1.0), sabre=False)})
	print("15 degaine (droite)")
	p15 = construire(corps(n, waist=(0, -5, 0)), {"Right": dict(main=(1.35, 0.45, -1.5), lame=(0.25, 0.85, -0.45))})
	print("19 main gauche vers la hanche droite")
	p19 = construire(corps(n, root_pos=(0, -0.1, 0), waist=(-10, -30, 0)), {"Right": dict(main=(1.7, 0.5, -0.9), lame=(0.4, 0.9, 0.0)), "Left": dict(main=(0.55, -0.4, -1.35), sabre=False)})
	print("22 degaine (gauche)")
	p22 = construire(corps(n, waist=(0, -8, 0)), {"Right": dict(main=(1.6, 0.5, -1.1), lame=(0.4, 0.9, 0.0)), "Left": dict(main=(-1.35, 0.35, -1.5), lame=(-0.3, 0.85, -0.4))})
	print("30 sabre a la bouche")
	p30 = construire(corps(n, waist=(0, 0, 0), neck=(-8, 0, 0)), {"Right": dict(main=(0.5, 1.0, -1.15), lame=(0.6, 0.6, 0.5)), "Left": dict(main=(-1.5, 0.35, -1.4), lame=(-0.3, 0.85, -0.4))})
	return p10, p15, p19, p22, p30


def idle():
	"""Degaine les trois sabres, se ramasse, puis ouvre les bras d'un coup : pose haki tenue (la charge monte, le corps
	vibre). Finit sur la pose haki, qui est l'image 0 de l'Action."""
	n = neutre()
	p10, p15, p19, p22, p30 = degainage(n)
	print("40 ramasse : bras plies, lames vers le bas, tete baissee")
	p40 = construire(corps(n, root_pos=(0, -0.3, 0), waist=(-12, 0, 0), neck=(-10, 0, 0)), {"Right": dict(main=(1.25, -0.35, -1.15), lame=(0.35, -0.8, -0.45)), "Left": dict(main=(-1.25, -0.35, -1.15), lame=(-0.35, -0.8, -0.45))})
	print("46 pose haki")
	h = haki(n)
	print("80 bras un peu plus hauts et ecartes, tete plus basse")
	h80 = haki(n, bras=(0.8, -0.52, -0.25), waist=(-7, 0, 0), neck=(-9, 0, 0), root_y=-0.2)
	print("115 buste qui se gonfle, tete relevee")
	h115 = haki(n, bras=(0.72, -0.66, -0.2), waist=(-3, 0, 0), neck=(-3, 0, 0), root_y=-0.12)
	cles = [
		(0, n, "Cubic"),
		(10, p10, "Sortie"),
		(15, p15, "Cubic"),
		(19, p19, "Sortie"),
		(22, p22, "Cubic"),
		(30, p30, "Cubic"),
		(40, p40, "Sortie"),  # Sortie : les bras s'ouvrent d'un coup
		(46, h, "Cubic"),
		(80, h80, "Cubic"),
		(115, h115, "Cubic"),
		(N_IDLE, h, "Cubic"),
	]
	marqueurs = [
		{"image": 15, "nom": "Cacher", "valeur": "Acc_Sabres_Hanche"}, {"image": 15, "nom": "Montrer", "valeur": "Acc_Sabre_Droit"},
		{"image": 22, "nom": "Montrer", "valeur": "Acc_Sabre_Gauche"}, {"image": 30, "nom": "Montrer", "valeur": "Acc_Sabre_Bouche"},
		{"image": 46, "nom": "VFX", "valeur": "Haki_Explosion"}, {"image": 47, "nom": "VFX", "valeur": "Haki_Aura"},
	]
	verifier_anim("Idle", cles, N_IDLE, avec_hanche=False)
	verifier_lames("Idle", cles, N_IDLE, depuis={"Right": 15, "Left": 22})
	ecrire("Idle", cles, N_IDLE, False, "Idle", marqueurs)
	finir("Idle", cles, N_IDLE, False, "Idle", marqueurs, secousses=[(46, 14, 4.0), (80, 10, 1.2), (115, 10, 1.2)])
	apercu("Idle", cles, [10, 22, 30, 40, 46, 80, 115, N_IDLE])
	return cles


def action():
	"""Grands coups bras tendus a partir de la pose haki : balayage droit, balayage gauche, double coup plongeant en
	fente (bras leves en V puis abattus), bras croises devant puis ouverture en croix ; retour sur la pose haki."""
	n = neutre()
	h = pose_du_json("Idle", N_IDLE)
	print("9 armer le coup droit : bras droit tendu en arriere")
	p9 = construire(corps(n, waist=(-4, -35, 0), neck=(-4, 15, 0)), {"Right": dict(dir=(0.85, 0.1, 0.5), lame=(0.3, 0.2, -0.9)), "Left": dict(dir=(-0.75, -0.55, -0.3), lame=(-0.85, 0.45, 0.25))})
	print("15 balayage droit, bras tendu en travers")
	p15 = construire(corps(n, waist=(-6, 30, 0), neck=(-4, -15, 0)), {"Right": dict(dir=(-0.55, 0.05, -0.85), lame=(-0.85, 0.1, 0.45)), "Left": dict(dir=(-0.85, -0.45, 0.2), lame=(-0.4, 0.6, 0.7))})
	print("23 le bras droit remonte devant, par-dessus (il ne repasse pas dans la poitrine)")
	p23 = construire(corps(n, waist=(-4, 10, 0), neck=(-4, -5, 0)), {"Right": dict(dir=(0.35, 0.65, -0.68), lame=(0.2, 0.3, 0.93)), "Left": dict(dir=(-0.85, -0.45, 0.2), lame=(-0.4, 0.6, 0.7))})
	print("30 armer le coup gauche")
	p30 = construire(corps(n, waist=(-4, 35, 0), neck=(-4, -15, 0)), {"Left": dict(dir=(-0.85, 0.1, 0.5), lame=(-0.3, 0.2, -0.9)), "Right": dict(dir=(0.85, -0.3, -0.1), lame=(0.5, 0.8, 0.1))})
	print("36 balayage gauche")
	p36 = construire(corps(n, waist=(-6, -30, 0), neck=(-4, 15, 0)), {"Left": dict(dir=(0.55, 0.05, -0.85), lame=(0.85, 0.1, 0.45)), "Right": dict(dir=(0.85, -0.45, 0.2), lame=(0.4, 0.6, 0.7))})
	print("46 bras leves en V, buste en arriere")
	p46 = construire(corps(n, waist=(8, 0, 0), neck=(4, 0, 0)), {"Right": dict(dir=(0.55, 0.8, 0.25), lame=(0.5, -0.2, 0.85)), "Left": dict(dir=(-0.55, 0.8, 0.25), lame=(-0.5, -0.2, 0.85))})
	print("53 double coup plongeant, en fente")
	p53 = construire(corps(n, waist=(-18, 0, 0), neck=(10, 0, 0)), {"Right": dict(dir=(0.6, -0.55, -0.6), lame=(0.75, 0.6, -0.1)), "Left": dict(dir=(-0.6, -0.55, -0.6), lame=(-0.75, 0.6, -0.1))})
	print("74 bras croises tendus devant, lames vers le haut")
	p74 = construire(corps(n, waist=(-8, 0, 0), neck=(2, 0, 0)), {"Right": dict(dir=(-0.35, 0.15, -0.95), lame=(-0.3, 0.8, 0.5)), "Left": dict(dir=(0.35, 0.3, -0.92), lame=(0.3, 0.8, 0.5))})
	print("101 bras redescendus, lames encore en arriere (elles tournent une fois les bras en bas)")
	p101 = haki(n, lame=(0.5, 0.35, 0.8))
	print("80 ouverture en croix, lames en arriere")
	p80 = construire(corps(n, waist=(-4, 0, 0), neck=(2, 0, 0)), {"Right": dict(dir=(0.95, 0.15, -0.25), lame=(0.3, 0.35, 0.88)), "Left": dict(dir=(-0.95, 0.15, -0.25), lame=(-0.3, 0.35, 0.88))})
	# root = (x, y, z, lacet) : le bassin tourne, le buste garde l'orientation du blocage (voir deplacer)
	cles = [
		(0, h, "Cubic"),
		(9, deplacer(p9, (0, -0.3, 0.1, -20), 9), "Sortie"),  # Sortie : chaque coup part d'un coup et freine en fin de geste
		(15, deplacer(p15, (0, -0.4, -0.1, 20), 15), "Cubic"),
		(23, deplacer(p23, (0, -0.3, 0, 5), 23), "Cubic"),
		(30, deplacer(p30, (0, -0.3, 0.1, 20), 30), "Sortie"),
		(36, deplacer(p36, (0, -0.4, -0.1, -20), 36), "Cubic"),
		(46, deplacer(p46, (0, -0.1, 0.1, 0), 46), "Sortie"),
		(53, deplacer(p53, (0, -0.7, -0.4, 0), 53), "Cubic"),
		(66, deplacer(p53, (0, -0.65, -0.35, 0), 66), "Cubic"),
		(74, deplacer(p74, (0, -0.4, -0.3, 0), 74), "Sortie"),
		(80, deplacer(p80, (0, -0.55, -0.35, 0), 80), "Cubic"),
		(94, deplacer(p80, (0, -0.5, -0.3, 0), 94), "Cubic"),
		(101, deplacer(p101, (0, -0.3, -0.15, 0), 101), "Cubic"),
		(110, deplacer(h, (0, -0.15, 0, 0), 110), "Cubic"),
		(N_ACTION, h, "Cubic"),
	]
	marqueurs = [
		{"image": 8, "nom": "VFX", "valeur": "Trail_Lames"}, {"image": 86, "nom": "VFX", "valeur": "Trail_Lames_Fin"},
		{"image": 14, "nom": "VFX", "valeur": "Entaille_Droite"}, {"image": 35, "nom": "VFX", "valeur": "Entaille_Gauche"},
		{"image": 52, "nom": "VFX", "valeur": "Entaille_Droite"}, {"image": 53, "nom": "VFX", "valeur": "Entaille_Gauche"},
		{"image": 80, "nom": "VFX", "valeur": "Tornade_Sabres"},
	]
	verifier_anim("Action", cles, N_ACTION, avec_hanche=False)
	verifier_lames("Action", cles, N_ACTION, depuis={"Right": 0, "Left": 0})
	ecrire("Action", cles, N_ACTION, False, "Action", marqueurs)
	finir("Action", cles, N_ACTION, False, "Action", marqueurs, secousses=[(15, 8, 2.5), (36, 8, 2.5), (53, 16, 4.5), (80, 14, 4.0)], retouche=jambes_suivies)
	apercu("Action", cles, [9, 15, 23, 30, 36, 46, 53, 74, 80, 101])
	return cles


def pose_du_json(nom, image):
	"""Relit une cle d'une animation deja ecrite (raccords exacts entre animations)."""
	d = json.loads((DOSSIER / "anims" / f"zoro_{nom}.json").read_text(encoding="utf-8"))
	cle = next(c for c in d["cles"] if c["image"] == image)
	pose = {a: tuple(v["angles"]) for a, v in cle["poses"].items()}
	for a, v in cle["poses"].items():
		if any(abs(x) > 1e-9 for x in v["cframe"][:3]):
			pose[a + "Pos"] = tuple(v["cframe"][:3])
	return pose


# Lames pendant le rangement. L'axe des fourreaux (0,06 ; -0,6 ; 0,8) est hors d'atteinte : la lame sort du poing
# perpendiculaire a l'avant-bras, il faudrait plier le poignet bien au-dela de 30 deg. On abaisse donc les lames pointe
# vers le bas puis legerement vers l'arriere ; au clac (image 45) elles disparaissent et les poignees reapparaissent.
LAMES_BAISSEES = (0.1, -0.95, -0.3)
LAMES_RANGEES = (0.1, -0.9, 0.4)


def signature():
	"""Rangement des sabres : part de la pose haki (derniere image de l'Action), finit sur la pose neutre."""
	n = neutre()
	g = pose_du_json("Action", N_ACTION)
	print("15 retire le sabre de la bouche")
	p15 = construire(corps(g, root_pos=(0, -0.15, 0), waist=(-3, 0, 0), neck=(-4, 0, 0)), {"Right": dict(main=(0.5, 1.0, -1.15), lame=(0.6, 0.6, 0.5))})
	print("25 ramene les deux sabres vers la hanche droite")
	p25 = construire(corps(p15, root_pos=(0, -0.1, 0), waist=(-4, -10, 0), neck=(-4, -5, 0)), {"Right": dict(main=(1.6, -0.3, -1.5), lame=LAMES_BAISSEES), "Left": dict(main=(0.6, -0.3, -1.6), lame=LAMES_BAISSEES)})
	print("45 clac : lames dans les fourreaux")
	p45 = construire(corps(p25, root_pos=(0, -0.1, 0), waist=(-6, -18, 0), neck=(-4, -8, 0)), {"Right": dict(main=(1.45, -0.72, -1.0), lame=LAMES_RANGEES), "Left": dict(main=(1.0, -0.6, -1.3), lame=LAMES_RANGEES)})
	print("55 yeux fermes, tete baissee")
	p55 = corps(n, waist=(-3, 0, 0), neck=(-8, 0, 0))
	cles = [(0, g, "Cubic"), (15, p15, "Cubic"), (25, p25, "Entree"), (45, p45, "Cubic"), (55, p55, "Cubic"), (75, n, "Cubic")]  # Entree : les lames accelerent jusqu'au clac
	marqueurs = [
		{"image": 15, "nom": "Cacher", "valeur": "Acc_Sabre_Bouche"},
		{"image": 45, "nom": "Cacher", "valeur": "Acc_Sabre_Droit"},
		# image 46 : l'editeur d'animation fusionne deux marqueurs de meme nom sur la meme image
		{"image": 46, "nom": "Cacher", "valeur": "Acc_Sabre_Gauche"},
		{"image": 45, "nom": "Montrer", "valeur": "Acc_Sabres_Hanche"}, {"image": 45, "nom": "VFX", "valeur": "Eclat_Garde"},
		{"image": 46, "nom": "VFX", "valeur": "Haki_Aura_Fin"},  # l'aura allumee dans l'Idle s'eteint au clac
	]
	verifier_anim("Signature", cles, 75, avec_hanche=False)
	verifier_lames("Signature", cles, 44, depuis={"Right": 0, "Left": 0})
	ecrire("Signature", cles, 75, False, "Action", marqueurs)
	finir("Signature", cles, 75, False, "Action", marqueurs, secousses=[(45, 8, 2.0)])
	apercu("Signature", cles, [0, 15, 25, 45, 55, 75])
	# raccords : image 0 = derniere image de l'Action, image 75 = image 0 de l'Idle
	for nom_a, im_a, im_b in (("Action", N_ACTION, 0), ("Idle", 0, 75)):
		a = json.loads((DOSSIER / "anims" / f"zoro_{nom_a}.json").read_text(encoding="utf-8"))
		b = json.loads((DOSSIER / "anims" / "zoro_Signature.json").read_text(encoding="utf-8"))
		ca = next(c for c in a["cles"] if c["image"] == im_a)["poses"]
		cb = next(c for c in b["cles"] if c["image"] == im_b)["poses"]
		ecart = max(abs(x - y) for art in ARTICULATIONS for x, y in zip(ca[art]["cframe"], cb[art]["cframe"]))
		print(f"raccord {nom_a}[{im_a}] / Signature[{im_b}] : ecart max {ecart:.2e}")
	return cles


if __name__ == "__main__":
	quoi = sys.argv[1] if len(sys.argv) > 1 else "Idle"
	{"Idle": idle, "Action": action, "Signature": signature}[quoi]()
