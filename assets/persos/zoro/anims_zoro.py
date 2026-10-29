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

DOSSIER = Path(__file__).parent
RIG = json.loads((DOSSIER.parent / "_mannequin" / "r15_bloc.json").read_text(encoding="utf-8"))
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


def bras_croises(base):
	"""Avant-bras croises devant le torse, a l'horizontale : le droit dessous et plus pres du torse,
	le gauche par-dessus et devant. Les blocs de 1 stud se recouvrent au milieu, comme un croisement."""
	pose = dict(base)
	pose["Waist"] = (6, 0, 0)  # le torse se redresse (et recule : place pour les avant-bras)
	pose["Neck"] = (6, 0, 0)  # menton releve : regard dur, de haut, visage degage au-dessus des bras
	f1, pose, info_d = chercher_bras(pose, "Right", -0.05, -1.05, tolerance=0.05, descentes=(0.0, 0.1, 0.2))
	print("bras droit", info_d)
	f2, pose, info_g = chercher_bras(pose, "Left", 0.25, -1.45, tolerance=0.05, descentes=(0.0, 0.1, 0.2))
	print("bras gauche", info_g)
	return pose, f1 + f2


def bras_devant(base):
	"""Pose de passage : bras leves devant et un peu ecartes, coudes plies, epaules avancees
	(les mains passent devant les poignees et le torse)."""
	p = dict(base)
	# bras d'abord ecartes et un peu leves : la main droite contourne les poignees par l'exterieur
	p["RightShoulder"] = (35, 0, 34)
	p["LeftShoulder"] = (35, 0, -34)
	p["RightElbow"] = (40, 0, 0)
	p["LeftElbow"] = (40, 0, 0)
	p["RightShoulderPos"] = (0.08, 0.02, -0.15)
	p["LeftShoulderPos"] = (-0.08, 0.02, -0.15)
	return p


def apercu(nom, cles, images):
	"""Poses completes a quelques images, pour l'apercu Blender et les clones Studio."""
	sortie = {str(i): {art: vers_douze(transform(pose_a(cles, i), art)) for art in ARTICULATIONS} for i in images}
	(DOSSIER / "anims" / f"apercu_{nom}.json").write_text(json.dumps(sortie), encoding="utf-8")


# ---------------------------------------------------------------- animation


def lisser(t, easing):
	if easing == "Linear":
		return t
	return t * t * (3 - 2 * t)  # Cubic InOut (approx.)


def slerp_pose(pa, pb, t):
	"""Interpolation de deux poses (angles interpoles par quaternions, comme Studio)."""
	from scipy.spatial.transform import Rotation as R, Slerp

	out = {}
	for art in ARTICULATIONS:
		a = pa.get(art, (0, 0, 0))
		b = pb.get(art, (0, 0, 0))
		ra = R.from_matrix(angles(*np.radians(a[:3]))[:3, :3])
		rb = R.from_matrix(angles(*np.radians(b[:3]))[:3, :3])
		r = Slerp([0, 1], R.concatenate([ra, rb]))(t)
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
				"easing": e,
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


def idle():
	n = neutre()
	c, f = bras_croises(n)
	print("bras croises, cout", round(f, 4), {k: c[k] for k in ("RightShoulder", "RightElbow", "LeftShoulder", "LeftElbow", "RightWrist", "LeftWrist")})
	cfs = fk(c)
	print("mains", np.round(cfs["RightHand"][:3, 3], 2), np.round(cfs["LeftHand"][:3, 3], 2))

	def var(base, waist_x, neck_y):
		p = dict(base)
		p["Waist"] = (base["Waist"][0] + waist_x, 0, 0)
		p["Neck"] = (base["Neck"][0], neck_y, 0)
		return p

	d = bras_devant(n)
	cles = [
		(0, n, "Cubic"),
		(10, d, "Cubic"),
		(20, var(c, 0, 0), "Cubic"),
		(38, var(c, 2, -8), "Cubic"),  # inspire, tete vers sa droite
		(56, var(c, -2, 0), "Cubic"),  # expire
		(74, var(c, 2, 8), "Cubic"),  # inspire, tete vers sa gauche
		(90, var(c, 0, 0), "Cubic"),
		(96, d, "Cubic"),
		(104, n, "Cubic"),
		(120, n, "Cubic"),
	]
	verifier_anim("Idle", cles, 120)
	ecrire("Idle", cles, 120, True, "Idle", [])
	apercu("Idle", cles, [0, 10, 20, 38, 74, 96])
	return cles




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


def viser(pose, cote, main=None, lame=None, sabre=True, avances=(0.0, 0.2), poids_main=10.0):
	"""Cherche le bras qui amene le centre de la main sur 'main' et la lame dans la direction 'lame',
	sans que le bras traverse le torse ni que la lame traverse le corps. Grille puis affinage."""
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
		if main is not None:
			cout += poids_main * np.sum((cfs[cote + "Hand"][:3, 3] - main) ** 2)
		if lame is not None:
			cout += 3 * (1 - float(np.dot(-cfs[cote + "Hand"][:3, 2], lame)))
		pen = 0.0
		for bo in (cote + "UpperArm", cote + "LowerArm", cote + "Hand"):
			pts = points_boite(bo, cfs[bo], 3)
			pen += dans_boite(pts, "UpperTorso", cfs["UpperTorso"], 0.0) + dans_boite(pts, "LowerTorso", cfs["LowerTorso"], 0.0) + dans_boite(pts, "Head", cfs["Head"], 0.0)
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


def construire(base, bras):
	"""bras = {cote: dict(main=..., lame=..., sabre=bool)} ; renvoie la pose avec pieds plantes."""
	p = planter(base)
	for cote, spec in bras.items():
		p, info = viser(p, cote, **spec)
		if spec.get("lame") is not None and spec.get("sabre", True):
			p = ajuster_poignet(p, cote, spec["lame"])
			info["lame_apres_poignet"] = np.round(-fk(p)[cote + "Hand"][:3, 2], 2).tolist()
			info["poignet"] = p[cote + "Wrist"]
		print("   ", cote, info)
	return p


def garde(n):
	"""Garde a trois sabres : bras ecartes vers l'avant, lames vers l'exterieur ; genoux flechis, buste penche, regard par en dessous."""
	b = corps(n, root_pos=(0, -0.2, 0), waist=(-6, 0, 0), neck=(4, 0, 0))
	return construire(b, {"Right": dict(main=(1.75, 0.25, -1.35), lame=(0.45, 0.6, -0.65)), "Left": dict(main=(-1.75, 0.25, -1.35), lame=(-0.45, 0.6, -0.65))})


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


def action():
	n = neutre()
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
	print("40 garde")
	g = garde(n)
	print("46 armer le coup droit")
	p46 = construire(corps(n, root_pos=(0, -0.2, 0), waist=(-4, -25, 0), neck=(4, 10, 0)), {"Right": dict(main=(2.0, 0.3, 0.1), lame=(0.6, 0.5, 0.6)), "Left": dict(main=(-1.75, 0.25, -1.3), lame=(-0.45, 0.6, -0.65))})
	print("50 balayage droit")
	p50 = construire(corps(n, root_pos=(0, -0.2, 0), waist=(-4, 20, 0), neck=(4, -12, 0)), {"Right": dict(main=(-0.6, 0.15, -1.7), lame=(-0.85, 0.3, -0.45)), "Left": dict(main=(-1.8, 0.2, -0.8), lame=(-0.45, 0.6, -0.65))})
	print("56 armer le coup gauche")
	p56 = construire(corps(n, root_pos=(0, -0.2, 0), waist=(-4, 25, 0), neck=(4, -10, 0)), {"Left": dict(main=(-2.0, 0.3, 0.1), lame=(-0.6, 0.5, 0.6)), "Right": dict(main=(-0.3, 0.2, -1.6), lame=(-0.85, 0.3, -0.45))})
	print("62 balayage gauche")
	p62 = construire(corps(n, root_pos=(0, -0.2, 0), waist=(-4, -20, 0), neck=(4, 12, 0)), {"Left": dict(main=(0.6, 0.15, -1.7), lame=(0.85, 0.3, -0.45)), "Right": dict(main=(1.8, 0.2, -0.8), lame=(0.45, 0.6, -0.65))})
	print("70 bras croises, lames en X")
	p70 = construire(corps(n, root_pos=(0, -0.3, 0), waist=(-8, 0, 0), neck=(2, 0, 0)), {"Right": dict(main=(-0.35, 0.55, -1.35), lame=(-0.5, 0.85, -0.1)), "Left": dict(main=(0.35, 0.75, -1.6), lame=(0.5, 0.85, -0.1))})
	print("75 ouverture en X, bond")
	p75 = construire(corps(n, root_pos=(0, -0.15, -0.45), waist=(6, 0, 0), neck=(-2, 0, 0)), {"Right": dict(main=(2.0, -0.2, -1.2), lame=(0.6, -0.3, -0.75)), "Left": dict(main=(-2.0, -0.2, -1.2), lame=(-0.6, -0.3, -0.75))})
	cles = [
		(0, n, "Cubic"), (10, p10, "Cubic"), (15, p15, "Cubic"), (19, p19, "Cubic"), (22, p22, "Cubic"), (30, p30, "Cubic"), (40, g, "Cubic"),
		(46, p46, "Cubic"), (50, p50, "Cubic"), (56, p56, "Cubic"), (62, p62, "Cubic"), (70, p70, "Cubic"), (75, p75, "Cubic"),
		(85, g, "Cubic"), (105, g, "Cubic"),
	]
	marqueurs = [
		{"image": 15, "nom": "Cacher", "valeur": "Acc_Sabres_Hanche"}, {"image": 15, "nom": "Montrer", "valeur": "Acc_Sabre_Droit"},
		{"image": 22, "nom": "Montrer", "valeur": "Acc_Sabre_Gauche"}, {"image": 30, "nom": "Montrer", "valeur": "Acc_Sabre_Bouche"},
		{"image": 45, "nom": "VFX", "valeur": "Trail_Lames"}, {"image": 80, "nom": "VFX", "valeur": "Trail_Lames_Fin"},
		{"image": 50, "nom": "VFX", "valeur": "Entaille_Droite"}, {"image": 62, "nom": "VFX", "valeur": "Entaille_Gauche"},
		{"image": 75, "nom": "VFX", "valeur": "Tornade_Sabres"},
	]
	verifier_anim("Action", cles, 105, avec_hanche=False)
	verifier_lames("Action", cles, 105, depuis={"Right": 15, "Left": 22})
	ecrire("Action", cles, 105, False, "Action", marqueurs)
	apercu("Action", cles, [10, 15, 19, 22, 30, 40, 46, 50, 56, 62, 70, 75, 105])
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
	"""Rangement des sabres : part de la garde (derniere image de l'Action), finit sur la pose neutre."""
	n = neutre()
	g = pose_du_json("Action", 105)
	print("15 retire le sabre de la bouche")
	p15 = construire(corps(g, root_pos=(0, -0.15, 0), waist=(-3, 0, 0), neck=(-4, 0, 0)), {"Right": dict(main=(0.5, 1.0, -1.15), lame=(0.6, 0.6, 0.5))})
	print("25 ramene les deux sabres vers la hanche droite")
	p25 = construire(corps(p15, root_pos=(0, -0.1, 0), waist=(-4, -10, 0), neck=(-4, -5, 0)), {"Right": dict(main=(1.6, -0.3, -1.5), lame=LAMES_BAISSEES), "Left": dict(main=(0.6, -0.3, -1.6), lame=LAMES_BAISSEES)})
	print("45 clac : lames dans les fourreaux")
	p45 = construire(corps(p25, root_pos=(0, -0.1, 0), waist=(-6, -18, 0), neck=(-4, -8, 0)), {"Right": dict(main=(1.45, -0.72, -1.0), lame=LAMES_RANGEES), "Left": dict(main=(1.0, -0.6, -1.3), lame=LAMES_RANGEES)})
	print("55 yeux fermes, tete baissee")
	p55 = corps(n, waist=(-3, 0, 0), neck=(-8, 0, 0))
	cles = [(0, g, "Cubic"), (15, p15, "Cubic"), (25, p25, "Cubic"), (45, p45, "Cubic"), (55, p55, "Cubic"), (75, n, "Cubic")]
	marqueurs = [
		{"image": 15, "nom": "Cacher", "valeur": "Acc_Sabre_Bouche"},
		{"image": 45, "nom": "Cacher", "valeur": "Acc_Sabre_Droit"},
		# image 46 : l'editeur d'animation fusionne deux marqueurs de meme nom sur la meme image
		{"image": 46, "nom": "Cacher", "valeur": "Acc_Sabre_Gauche"},
		{"image": 45, "nom": "Montrer", "valeur": "Acc_Sabres_Hanche"}, {"image": 45, "nom": "VFX", "valeur": "Eclat_Garde"},
	]
	verifier_anim("Signature", cles, 75, avec_hanche=False)
	verifier_lames("Signature", cles, 44, depuis={"Right": 0, "Left": 0})
	ecrire("Signature", cles, 75, False, "Action", marqueurs)
	apercu("Signature", cles, [0, 15, 25, 45, 55, 75])
	# raccords : image 0 = derniere image de l'Action, image 75 = image 0 de l'Idle
	for nom_a, im_a, im_b in (("Action", 105, 0), ("Idle", 0, 75)):
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
