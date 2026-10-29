"""Animations de vitrine de nami (Idle, Action, Signature), calculees sur le rig releve dans Studio (rig_nami.json).

Sortie : assets/persos/nami/anims/nami_<Nom>.json (source de verite), construits ensuite en KeyframeSequence dans Studio
(vers_studio.py) ; apercus : anims/apercu_<Nom>.json (poses completes a quelques images, pour apercu_studio.py).
Repere Studio : +X = droite du perso, +Y = haut, +Z = arriere. Une pose = Motor6D.Transform par articulation, donnee en
angles (degres) : Transform = CFrame.Angles(rx, ry, rz), plus des translations ('<Art>Pos' : Root, epaules).
Sens des axes : assets/persos/_mannequin/axes_r15.json (+X : un membre qui pend part vers l'avant ; +Y : tourne vers
la gauche du perso ; +Z : le bout part vers la droite du perso).

Usage : uv run --with numpy --with scipy assets/persos/nami/anims_nami.py [Idle|Action|Signature]
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

DOSSIER = Path(__file__).parent
RIG = json.loads((DOSSIER / "rig_nami.json").read_text(encoding="utf-8"))
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


def vers_douze(m):
	return [round(float(v), 6) for v in list(m[:3, 3]) + list(m[:3, :3].reshape(9))]


MOTEURS = {k: (v["part0"], v["part1"], cf(v["c0"]), cf(v["c1"])) for k, v in RIG["motors"].items()}
TAILLES = {k: np.array(v["taille"]) for k, v in RIG["pieces"].items()}
ACCESSOIRES = {k: (v["piece"], cf(v["rel"]), np.array(v["taille"])) for k, v in RIG["accessoires"].items()}


def transform(pose, art):
	rx, ry, rz = pose.get(art, (0, 0, 0))[:3]
	m = angles(math.radians(rx), math.radians(ry), math.radians(rz))
	if art + "Pos" in pose:
		m[:3, 3] = pose[art + "Pos"]
	return m


def fk(pose):
	"""CFrame de chaque piece (et des Handle d'accessoires), relatif au HumanoidRootPart."""
	cfs = {"HumanoidRootPart": np.eye(4)}
	reste = list(MOTEURS)
	while reste:
		for art in list(reste):
			p0, p1, c0, c1 = MOTEURS[art]
			if p0 in cfs:
				cfs[p1] = cfs[p0] @ c0 @ transform(pose, art) @ np.linalg.inv(c1)
				reste.remove(art)
	for nom, (piece, rel, _) in ACCESSOIRES.items():
		cfs[nom] = cfs[piece] @ rel
	return cfs


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
	"""Penetrations (studs) des bras et des accessoires dans le corps ; deplacement du LowerTorso et des pieds."""
	cfs = fk(pose)
	res = {}
	for b in BRAS + list(ACCESSOIRES):
		taille = TAILLES[b] if b in TAILLES else ACCESSOIRES[b][2]
		pts = points_boite(taille, cfs[b])
		for c in CORPS:
			if b == "Acc_Baton" and c == "Head":
				pass
			res[b + ">" + c] = penetration(pts, TAILLES[c], cfs[c])
	repos = fk({})
	res["deplacement_LowerTorso"] = float(np.linalg.norm(cfs["LowerTorso"][:3, 3] - repos["LowerTorso"][:3, 3]))
	for pied in ("RightFoot", "LeftFoot"):
		res["glissement_" + pied] = float(np.linalg.norm(cfs[pied][:3, 3] - repos[pied][:3, 3]))
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


PIEDS_REPOS = None


def planter(pose):
	"""Pieds plantes : hanches, genoux et chevilles recalcules pour garder chaque pied a sa place de repos (position et
	orientation), quelle que soit la pose du bassin."""
	global PIEDS_REPOS
	if PIEDS_REPOS is None:
		PIEDS_REPOS = {p: fk({})[p] for p in ("RightFoot", "LeftFoot")}
	p = dict(pose)
	for cote in ("Right", "Left"):
		cible = PIEDS_REPOS[cote + "Foot"]
		genou_pref = p.get(cote + "Knee", (0, 0, 0))[0]

		def cout(q, cote=cote, cible=cible, genou_pref=genou_pref):
			m = fk(q)[cote + "Foot"]
			return 50 * float(np.sum((m[:3, 3] - cible[:3, 3]) ** 2)) + 5 * float(np.sum((m[:3, :3] - cible[:3, :3]) ** 2)) + 0.0005 * (q[cote + "Knee"][0] - genou_pref) ** 2

		variables = [(cote + "Hip", 0), (cote + "Hip", 1), (cote + "Hip", 2), (cote + "Knee", 0), (cote + "Ankle", 0), (cote + "Ankle", 1), (cote + "Ankle", 2)]
		p, _ = resoudre(p, variables, cout)
	return p


def main_vers(pose, cote, cible, ecart_coude=None, poids_pen=200.0, orientation=None, poids_coude=0.5, tolerance=0.0, departs_en_plus=()):
	"""IK du bras : la main (centre) va vers cible (repere HRP), sans traverser le corps ; ecart_coude = direction
	vers laquelle pousser le coude ; orientation = (axe local de la main, direction monde voulue, poids)."""
	S, E, W = cote + "Shoulder", cote + "Elbow", cote + "Wrist"
	cible = np.array(cible, float)

	def cout(q):
		cfs = fk(q)
		c = 20 * float(np.sum((cfs[cote + "Hand"][:3, 3] - cible) ** 2))
		pen = 0.0
		for b in (cote + "UpperArm", cote + "LowerArm", cote + "Hand"):
			pts = points_boite(TAILLES[b], cfs[b], 3)
			for corps in ("UpperTorso", "LowerTorso", "Head"):
				pen += penetration(pts, TAILLES[corps], cfs[corps], 0.0)
		c += poids_pen * max(0.0, pen - tolerance) + 2.0 * pen
		if ecart_coude is not None:
			coude = cfs[cote + "LowerArm"][:3, 3]
			c -= poids_coude * float(np.dot(coude, ecart_coude))
		if orientation is not None:
			axe_local, voulu, poids = orientation
			c += poids * float(np.sum((cfs[cote + "Hand"][:3, :3] @ np.array(axe_local) - np.array(voulu)) ** 2))
		return c

	variables = [(S, 0), (S, 1), (S, 2), (E, 0), (W, 0), (W, 1), (W, 2)]
	# plusieurs departs (l'optimiseur reste sinon pres de la pose initiale) : on garde le meilleur
	sz = 1 if cote == "Right" else -1
	departs = [None, ((-10, 0, 40 * sz), 100), ((-20, -50 * sz, 30 * sz), 110), ((40, 0, 20 * sz), 110), ((10, 40 * sz, 50 * sz), 90), ((60, 0, 10 * sz), 130)] + list(departs_en_plus)
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
	Le coude ne plie que sur X+ (avant-bras vers l'avant de la piece) : son axe est impose par u et f (cf. zoro)."""
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


def main_hanche(pose, cote, cible, tolerance=0.08):
	"""Poing sur la hanche : grille sur la position du coude (sorti sur le cote), avant-bras dirige vers la cible ;
	cout = distance main-cible + penetration dans le torse au-dela de la tolerance."""
	sx = 1 if cote == "Right" else -1
	cfs0 = fk(pose)
	epaule = (cfs0["UpperTorso"] @ MOTEURS[cote + "Shoulder"][2])[:3, 3]
	cible = np.array(cible, float)
	meilleur = (1e9, None, None)
	for ex in np.linspace(0.35, 0.8, 10):
		for ey in np.linspace(-0.75, -0.25, 11):
			for ez in np.linspace(-0.25, 0.35, 7):
				coude_dir = np.array([sx * ex, ey, ez])
				q = bras_dirige(pose, cote, coude_dir, cible - (epaule + coude_dir / np.linalg.norm(coude_dir) * 0.78))
				if q is None:
					continue
				cfs = fk(q)
				pen = 0.0
				for b in (cote + "UpperArm", cote + "LowerArm", cote + "Hand"):
					pts = points_boite(TAILLES[b], cfs[b], 3)
					pen = max(pen, penetration(pts, TAILLES["UpperTorso"], cfs["UpperTorso"], 0.0), penetration(pts, TAILLES["LowerTorso"], cfs["LowerTorso"], 0.0))
				d = float(np.linalg.norm(cfs[cote + "Hand"][:3, 3] - cible))
				cout = d + 10 * max(0.0, pen - tolerance) + 0.5 * pen
				if cout < meilleur[0]:
					meilleur = (cout, q, dict(distance=round(d, 3), penetration=round(pen, 3), coude=np.round(cfs[cote + "LowerArm"][:3, 3], 2).tolist()))
	return meilleur


# ---------------------------------------------------------------- animation


def lisser(t, easing):
	if easing == "Linear":
		return t
	return t * t * (3 - 2 * t)  # Cubic InOut (approx.)


def slerp_pose(pa, pb, t):
	from scipy.spatial.transform import Rotation as R, Slerp

	out = {}
	for art in ARTICULATIONS:
		a = pa.get(art, (0, 0, 0))
		b = pb.get(art, (0, 0, 0))
		ra = R.from_matrix(angles(*np.radians(a[:3]))[:3, :3])
		rb = R.from_matrix(angles(*np.radians(b[:3]))[:3, :3])
		r = Slerp([0, 1], R.concatenate([ra, rb]))(t)
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


def verifier_anim(nom, cles, n_images):
	pire = {}
	for i in range(0, n_images + 1, 2):
		for k, v in verifier(pose_a(cles, i)).items():
			if v > pire.get(k, (0, -1))[0]:
				pire[k] = (v, i)
	print(f"--- verification {nom} (pire valeur, image ; seuil 0,02)")
	for k, (v, i) in sorted(pire.items()):
		if v > 0.02:
			print(f"  {k}: {v:.3f} (image {i})")


def ecrire(nom, cles, n_images, boucle, priorite, marqueurs):
	donnees = {
		"nom": "nami_" + nom,
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
	(DOSSIER / "anims" / f"nami_{nom}.json").write_text(json.dumps(donnees, indent="\t", ensure_ascii=False), encoding="utf-8")
	print("ecrit", f"anims/nami_{nom}.json", len(cles), "cles,", len(marqueurs), "marqueurs")


def apercu(nom, cles, images, visibles):
	"""Poses completes a quelques images (Transform de chaque Motor6D + accessoires visibles), pour apercu_studio.py."""
	sortie = {str(i): {"poses": {art: vers_douze(transform(pose_a(cles, i), art)) for art in ARTICULATIONS}, "visibles": visibles(i)} for i in images}
	(DOSSIER / "anims" / f"apercu_{nom}.json").write_text(json.dumps(sortie), encoding="utf-8")


# ---------------------------------------------------------------- poses de nami


def avec(base, **kw):
	p = dict(base)
	p.update(kw)
	return p


def neutre():
	"""Image 0 de l'Idle (pose de la reference) : baton tenu a la verticale dans la main droite (coude plie, la tige du
	Clima-Tact est perpendiculaire a l'avant-bras), main gauche sur la hanche, poids sur la jambe droite, hanche sortie."""
	p = {
		"Root": (0, 0, 4),  # bassin incline (hanche droite haute : poids sur la jambe droite)
		"RootPos": (0.1, -0.03, 0),
		"Waist": (0, 3, -6),  # buste qui compense, un peu tourne
		"Neck": (0, -4, 6),  # tete penchee, air espiegle
		# bras droit au repos : coude a 45 deg, poignet tourne de 30 deg : le Clima-Tact reste vertical
		"RightShoulder": (15, 0, 8),
		"RightElbow": (45, 0, 0),
		"RightWrist": (30, 0, 0),
		"LeftKnee": (-10, 0, 0),
	}
	p = planter(p)
	# main gauche sur la hanche : coude vers l'exterieur (gauche du perso = -X)
	# poing sur la hanche : coude sorti sur le cote, avant-bras qui revient vers la hanche
	f, p, info = main_hanche(p, "Left", (-1.25, -0.52, 0.05), tolerance=0.35)  # la main rentre un peu dans la hanche (poses Roblox standard)
	print("main gauche sur la hanche", info)
	print("main gauche sur la hanche, cout", round(f, 3), {k: p[k] for k in ("LeftShoulder", "LeftElbow", "LeftWrist")})
	return p


def idle():
	n = neutre()
	cfs = fk(n)
	print("baton (axe de la tige)", np.round(cfs["Acc_Baton"][:3, 0], 2), "main droite", np.round(cfs["RightHand"][:3, 3], 2))
	# bourse levee a hauteur du visage, coude plie, la tete suit
	haut, f = main_vers(avec(n, Neck=(4, 14, 4)), "Left", (-0.95, 1.25, -0.95), ecart_coude=np.array([-1.0, -0.5, 0]))
	print("bourse levee, cout", round(f, 3), {k: haut[k] for k in ("LeftShoulder", "LeftElbow", "LeftWrist")})

	def secoue(signe, penche):
		p = dict(haut)
		w = list(haut["LeftWrist"])
		w[0] = max(-30, min(30, w[0] + 22 * signe))
		p["LeftWrist"] = tuple(w)
		e = list(haut["LeftElbow"])
		e[0] = e[0] + 6 * signe
		p["LeftElbow"] = tuple(e)
		p["Neck"] = (4, 14, 4 + penche)
		return p

	balance_d = planter(avec(n, Root=(0, 0, 6), RootPos=(0.14, -0.03, 0), Waist=(0, 4, -8)))
	balance_g = planter(avec(n, Root=(0, 0, 1), RootPos=(0.05, -0.03, 0), Waist=(0, 2, -3)))
	cles = [
		(0, n, "Cubic"),
		(12, n, "Cubic"),
		(24, haut, "Cubic"),
		(30, secoue(0, 6), "Linear"),
		(33, secoue(1, 8), "Linear"),
		(36, secoue(-1, 8), "Linear"),
		(39, secoue(1, 8), "Linear"),
		(42, secoue(-1, 8), "Linear"),
		(45, secoue(0, 8), "Cubic"),
		(55, avec(haut, Neck=(2, 10, 6)), "Cubic"),
		(65, balance_d, "Cubic"),
		(78, balance_g, "Cubic"),
		(90, n, "Cubic"),
	]
	marqueurs = [
		{"image": 15, "nom": "Montrer", "valeur": "Acc_Bourse"},
		{"image": 30, "nom": "VFX", "valeur": "Pieces_Brillent"},
		{"image": 65, "nom": "Cacher", "valeur": "Acc_Bourse"},
	]
	verifier_anim("Idle", cles, 90)
	ecrire("Idle", cles, 90, True, "Idle", marqueurs)
	apercu("Idle", cles, [0, 15, 24, 36, 65, 78], lambda i: ["Acc_Baton"] + (["Acc_Bourse"] if 15 <= i < 65 else []))
	return cles


def action():
	"""Coup de tonnerre (105 images, une fois) : baton leve tres haut (nuage), moulinet au-dessus de la tete
	(etincelles), abattu vers l'avant (eclair), replante, retour a la pose neutre. Pieds plantes tout du long."""
	n = neutre()

	def droit(base, epaule, coude, poignet=(0, 0, 0), **corps):
		p = avec(base, RightShoulder=epaule, RightElbow=(coude, 0, 0), RightWrist=poignet, **corps)
		return planter(p)

	# bras droit leve presque a la verticale, coude un peu plie : le Clima-Tact (perpendiculaire a l'avant-bras)
	# passe a l'horizontale au-dessus de la tete ; buste un peu cambre, regard vers le haut
	leve = droit(n, (160, 0, 28), 15, Waist=(-6, 3, -4), Neck=(-14, -4, 4), Root=(0, 0, 3))
	tour = [droit(n, (160, y, 35), 15, (0, 0, z), Waist=(-6, 3 + y / 6, -4), Neck=(-14, -4, 4), Root=(0, 0, 3)) for y, z in ((-25, -28), (25, 28), (-25, -28), (25, 28))]
	# abattu vers l'avant : le bras redescend en arc devant elle jusqu'un peu en arriere ; le baton (perpendiculaire a
	# l'avant-bras) finit pointe vers l'avant et vers le sol, la ou tombe l'eclair ; buste penche
	abat = droit(n, (-30, 0, 10), 0, (-20, 0, 0), Waist=(12, 6, -2), Neck=(6, 0, 0), Root=(4, 0, 2), RootPos=(0.1, -0.12, 0))
	elan = droit(n, (175, 0, 25), 25, Waist=(-10, 3, -4), Neck=(-16, -4, 4), Root=(-2, 0, 3))
	replante = avec(n, Neck=(0, -10, 10), Waist=(0, 6, -6))
	cles = [
		(0, n, "Cubic"),
		(15, leve, "Cubic"),
		(20, tour[0], "Linear"),
		(26, tour[1], "Linear"),
		(32, tour[2], "Linear"),
		(38, tour[3], "Linear"),
		(45, leve, "Cubic"),
		(50, elan, "Cubic"),
		(55, abat, "Cubic"),
		(63, abat, "Cubic"),
		(75, replante, "Cubic"),
		(90, n, "Cubic"),
		(105, n, "Cubic"),
	]
	marqueurs = [
		{"image": 15, "nom": "VFX", "valeur": "Nuage"},
		{"image": 16, "nom": "VFX", "valeur": "Charge"},
		{"image": 30, "nom": "VFX", "valeur": "Etincelles"},
		{"image": 55, "nom": "VFX", "valeur": "Eclair"},
		{"image": 56, "nom": "VFX", "valeur": "Rafales"},
	]
	cfs = fk(abat)
	print("baton abattu (axe de la tige)", np.round(cfs["Acc_Baton"][:3, 0], 2), "main", np.round(cfs["RightHand"][:3, 3], 2))
	cfs = fk(leve)
	print("baton leve (axe)", np.round(cfs["Acc_Baton"][:3, 0], 2), "main", np.round(cfs["RightHand"][:3, 3], 2))
	verifier_anim("Action", cles, 105)
	ecrire("Action", cles, 105, False, "Action", marqueurs)
	apercu("Action", cles, [0, 15, 26, 50, 55, 75], lambda i: ["Acc_Baton"])
	return cles


def signature():
	"""Carte au tresor (105 images, une fois) : la main gauche deroule la carte devant elle (tete penchee de 8 deg),
	petit saut de joie (+0,2) avec les pieces, la carte disparait, retour a la pose neutre."""
	n = neutre()
	# main gauche devant la poitrine, avant-bras releve : la carte (sous la main au repos) part vers l'avant, face
	# tournee vers elle ; elle la regarde, tete penchee de 8 deg vers sa gauche
	lit, f = main_vers(avec(n, Neck=(-12, 8, -8), Waist=(4, 6, -4)), "Left", (-0.65, 0.3, -1.05), ecart_coude=np.array([-1.0, 0, 0]))
	cfs = fk(lit)
	print("carte : centre", np.round(cfs["Acc_Carte"][:3, 3], 2), "normale (face dessinee)", np.round(-cfs["Acc_Carte"][:3, 2], 2), "main", np.round(cfs["LeftHand"][:3, 3], 2))
	accroupi = planter(avec(lit, RootPos=(0.1, -0.16, 0), Root=(6, 0, 4), RightKnee=(-20, 0, 0), LeftKnee=(-25, 0, 0)))
	# saut : tout le corps monte de 0,2 (les pieds quittent le sol), jambes tendues, tete relevee de joie
	# (pose aux pieds plantes, puis tout le corps monte : les pieds montent droit de 0,2)
	saut = planter(avec(lit, Root=(-4, 0, 2), Neck=(-18, 8, -8)))
	pos = saut.get("RootPos", (0, 0, 0))
	saut["RootPos"] = (pos[0], pos[1] + 0.2, pos[2])
	cles = [
		(0, n, "Cubic"),
		(15, lit, "Cubic"),
		(30, avec(lit, Neck=(-14, 10, -8)), "Cubic"),
		(35, accroupi, "Cubic"),
		(40, saut, "Cubic"),
		(46, accroupi, "Cubic"),
		(54, lit, "Cubic"),
		(66, avec(lit, Neck=(-8, 4, -4)), "Cubic"),
		(75, n, "Cubic"),
		(105, n, "Cubic"),
	]
	marqueurs = [
		{"image": 15, "nom": "Montrer", "valeur": "Acc_Carte"},
		{"image": 40, "nom": "VFX", "valeur": "Pieces"},
		{"image": 75, "nom": "Cacher", "valeur": "Acc_Carte"},
	]
	verifier_anim("Signature", cles, 105)
	ecrire("Signature", cles, 105, False, "Action", marqueurs)
	apercu("Signature", cles, [0, 15, 35, 40, 75], lambda i: ["Acc_Baton"] + (["Acc_Carte"] if 15 <= i < 75 else []))
	return cles


if __name__ == "__main__":
	quoi = sys.argv[1] if len(sys.argv) > 1 else "Idle"
	{"Idle": idle, "Action": action, "Signature": signature}[quoi]()
