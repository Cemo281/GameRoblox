"""Finition des animations de vitrine : transforme un blocage (poses cles) en animation cuite a 30 i/s.

Le blocage donne les poses ; la finition donne la vie :
- courbes d'impact par transition (en plus de Linear / Cubic) : Sortie (part vite, freine), Entree (part lentement,
  arrive vite), Rebond (depasse puis revient), Elastique, Constant ;
- ressorts par articulation (second ordre) : le buste, la tete, puis l'epaule, le coude et le poignet suivent chacun
  avec un petit retard et depassent un peu leur cible (decalage et suivi), au lieu de partir et s'arreter ensemble ;
- respiration discrete (buste et tete), pour qu'aucune pose tenue ne soit figee ;
- secousses d'impact (buste et tete qui vibrent puis s'amortissent) ;
- raccords exacts : la premiere et la derniere image sont celles du blocage (pose neutre) ;
- allegement : on ne garde que les images utiles (l'interpolation lineaire de Roblox redonne les autres a 0,25 deg).
Les jambes et Root ne recoivent ni ressort ni secousse : les pieds restent plantes comme dans le blocage.

Conventions (les memes que les scripts anims_<id>.py) : pose = {articulation: (rx, ry, rz) en degres,
Transform = CFrame.Angles(rx, ry, rz) ; '<Art>Pos': translation}. Une cle de blocage = (image, pose, courbe) ;
comme dans Roblox, la courbe d'une cle regit la transition qui PART de cette cle.
"""

import math

import numpy as np
from scipy.spatial.transform import Rotation as R

FPS = 30
SOUS_PAS = 8  # pas d'integration des ressorts par image

# Courbes de Roblox (exportables telles quelles dans le blocage) et courbes de finition (cuites seulement).
COURBES_ROBLOX = {"Linear", "Constant", "Cubic", "Elastic", "Bounce", "CubicV2"}


def courbe(t, nom):
	t = min(1.0, max(0.0, t))
	if nom == "Linear":
		return t
	if nom == "Constant":
		return 0.0 if t < 1 else 1.0
	if nom in ("Cubic", "CubicV2"):
		return 4 * t**3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2
	if nom == "Sortie":  # quartique sortante : l'essentiel du geste dans le premier tiers
		return 1 - (1 - t) ** 4
	if nom == "Entree":  # cubique entrante : accelere jusqu'au bout (armee qui se libere, chute)
		return t**3
	if nom == "Rebond":  # depasse d'environ 8 % puis revient
		s = 1.2
		u = t - 1
		return 1 + (s + 1) * u**3 + s * u**2
	if nom in ("Elastique", "Elastic"):
		if t in (0.0, 1.0):
			return t
		return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3.4) + 1
	if nom == "Bounce":
		return courbe(t, "Rebond")
	raise ValueError("courbe inconnue : " + nom)


def vers_roblox(nom):
	"""Courbe a ecrire dans le blocage exporte tel quel (les courbes de finition n'existent pas dans Roblox)."""
	return nom if nom in COURBES_ROBLOX else ("Linear" if nom == "Sortie" else "Cubic")


# ---------------------------------------------------------------- ressorts

# (frequence Hz, amortissement, reponse) : plus la frequence est basse, plus l'articulation traine ; amortissement < 1
# = depassement ; reponse > 0 = reagit tout de suite a la vitesse de la cible (garde les coups vifs).
RESSORTS = {
	"Waist": (3.4, 0.8, 1.0),
	"Neck": (2.4, 0.6, 0.6),
	"RightShoulder": (4.2, 0.62, 1.2),
	"LeftShoulder": (4.2, 0.62, 1.2),
	"RightElbow": (3.4, 0.5, 1.0),
	"LeftElbow": (3.4, 0.5, 1.0),
	"RightWrist": (2.8, 0.45, 0.8),
	"LeftWrist": (2.8, 0.45, 0.8),
	"RightShoulderPos": (3.0, 0.35, 1.4),  # bras elastique : rebondit en bout de course
	"LeftShoulderPos": (3.0, 0.35, 1.4),
	"RightElbowPos": (3.0, 0.35, 1.4),  # avant-bras elastique (luffy : l'epaule reste collee, la peau s'etire au coude)
	"LeftElbowPos": (3.0, 0.35, 1.4),
}


def _rot(a):
	return R.from_euler("XYZ", np.radians(a[:3]))


def _euler(r):
	return tuple(float(v) for v in np.degrees(r.as_euler("XYZ")))


def _coefs(f, z, r):
	return z / (math.pi * f), 1 / (2 * math.pi * f) ** 2, r * z / (2 * math.pi * f)


def _ressort_rotation(cibles, reglage, depart=None):
	"""cibles = liste de Rotation (une par image) ; renvoie la liste suivie et l'etat final (q, w)."""
	k1, k2, k3 = _coefs(*reglage)
	n = len(cibles)
	q, w = depart if depart else (cibles[0], np.zeros(3))
	dt = 1 / (FPS * SOUS_PAS)
	sortie = []
	for i in range(n):
		sortie.append(q)
		if i == n - 1:
			break
		a, b = cibles[i], cibles[i + 1]
		vitesse = (b * a.inv()).as_rotvec() * FPS
		for s in range(SOUS_PAS):
			x = R.from_quat(_slerp(a, b, (s + 1) / SOUS_PAS))
			e = (x * q.inv()).as_rotvec()
			w = w + dt * (e + k3 * vitesse - k1 * w) / k2
			q = R.from_rotvec(w * dt) * q
	return sortie, (q, w)


def _slerp(a, b, t):
	qa, qb = a.as_quat(), b.as_quat()
	d = float(np.dot(qa, qb))
	if d < 0:
		qb, d = -qb, -d
	if d > 0.9995:
		q = qa + t * (qb - qa)
		return q / np.linalg.norm(q)
	th = math.acos(d)
	return (math.sin((1 - t) * th) * qa + math.sin(t * th) * qb) / math.sin(th)


def _ressort_vecteur(cibles, reglage, depart=None):
	k1, k2, k3 = _coefs(*reglage)
	y, v = depart if depart else (np.array(cibles[0], float), np.zeros(3))
	dt = 1 / (FPS * SOUS_PAS)
	sortie = []
	for i in range(len(cibles)):
		sortie.append(y.copy())
		if i == len(cibles) - 1:
			break
		a, b = np.array(cibles[i], float), np.array(cibles[i + 1], float)
		vit = (b - a) * FPS
		for s in range(SOUS_PAS):
			x = a + (b - a) * (s + 1) / SOUS_PAS
			v = v + dt * (x + k3 * vit - y - k1 * v) / k2
			y = y + v * dt
	return sortie, (y, v)


# ---------------------------------------------------------------- cuisson


def echantillonner(cles, n_images, articulations):
	"""Pose du blocage a chaque image (slerp par articulation, comme Roblox, avec les courbes de finition)."""
	images = []
	for i in range(n_images + 1):
		for (fa, pa, ea), (fb, pb, _) in zip(cles, cles[1:]):
			if fa <= i <= fb:
				t = courbe(0 if fb == fa else (i - fa) / (fb - fa), ea)
				p = {}
				for art in articulations:
					ra, rb = _rot(pa.get(art, (0, 0, 0))), _rot(pb.get(art, (0, 0, 0)))
					if t < 0 or t > 1:  # depassement (Rebond, Elastique) : on prolonge la rotation de a vers b
						p[art] = _euler(R.from_rotvec((rb * ra.inv()).as_rotvec() * t) * ra)
					else:
						p[art] = _euler(R.from_quat(_slerp(ra, rb, t)))
					cle = art + "Pos"
					if cle in pa or cle in pb:
						a, b = np.array(pa.get(cle, (0, 0, 0)), float), np.array(pb.get(cle, (0, 0, 0)), float)
						p[cle] = tuple(float(v) for v in a + (b - a) * t)
				images.append(p)
				break
		else:
			images.append(dict(cles[-1][1]))
	return images


def _poids(i, n, contacts_art):
	"""Poids de la finition a l'image i (0 = blocage exact) : fondu d'entree et de sortie, contacts."""
	lisse = lambda x: 0.0 if x <= 0 else 1.0 if x >= 1 else x * x * (3 - 2 * x)
	w = lisse(i / 6) * lisse((n - i) / 8)
	for i0, i1 in contacts_art:
		if i0 - 3 <= i <= i1 + 3:
			w *= 1 - lisse(min(i - (i0 - 3), (i1 + 3) - i) / 3)
	return w


def cuire(cles, n_images, articulations, boucle=False, limites=None, respiration=1.2, secousses=(), contacts=None, ressorts=None):
	"""Animation finie, image par image : liste de poses (n_images + 1).

	respiration : amplitude (degres) du buste ; secousses : [(image, duree en images, amplitude en degres)] ;
	contacts : {articulation: [(image debut, image fin)]} ou la pose du blocage est gardee exacte (main posee, etc.)."""
	ressorts = dict(RESSORTS, **(ressorts or {}))
	contacts = contacts or {}
	base = echantillonner(cles, n_images, articulations)
	n = n_images

	# couche additive (respiration, secousses) ajoutee a la cible des ressorts
	nb_souffles = max(1, round(n / (FPS * 3.2)))
	enveloppe = (lambda i: 1.0) if boucle else (lambda i: math.sin(math.pi * i / n) ** 0.5)
	ajout = [{} for _ in range(n + 1)]
	for i in range(n + 1):
		ph = 2 * math.pi * nb_souffles * i / n
		ajout[i]["Waist"] = np.array([respiration * math.sin(ph) * enveloppe(i), 0, 0])
		ajout[i]["Neck"] = np.array([-0.5 * respiration * math.sin(ph - 0.6) * enveloppe(i), 0, 0])
		for i0, duree, amp in secousses:
			if i0 <= i < i0 + duree:
				t = (i - i0) / FPS
				a = amp * math.exp(-5 * (i - i0) / duree)
				ajout[i]["Waist"] = ajout[i]["Waist"] + np.array([a * math.sin(2 * math.pi * 9 * t), 0, 0.7 * a * math.sin(2 * math.pi * 7 * t + 1)])
				ajout[i]["Neck"] = ajout[i]["Neck"] + np.array([-0.8 * a * math.sin(2 * math.pi * 9 * t - 0.8), 0, 0])

	sortie = [dict(p) for p in base]
	for art, reglage in ressorts.items():
		if art.endswith("Pos"):
			nom = art
			if not any(nom in p for p in base):
				continue
			cibles = [p.get(nom, (0, 0, 0)) for p in base]
			suivi, etat = _ressort_vecteur(cibles, reglage)
			if boucle:
				suivi, _ = _ressort_vecteur(cibles, reglage, etat)
			for i in range(n + 1):
				w = _poids(i, n, contacts.get(nom, []))
				sortie[i][nom] = tuple(float(v) for v in np.array(cibles[i]) + w * (suivi[i] - np.array(cibles[i])))
			continue
		if art not in articulations:
			continue
		cibles = [R.from_euler("XYZ", np.radians(np.array(p.get(art, (0, 0, 0))[:3]) + ajout[i].get(art, 0))) for i, p in enumerate(base)]
		suivi, etat = _ressort_rotation(cibles, reglage)
		if boucle:
			suivi, _ = _ressort_rotation(cibles, reglage, etat)
		exact = [_rot(p.get(art, (0, 0, 0))) for p in base]
		for i in range(n + 1):
			w = _poids(i, n, contacts.get(art, []))
			r = R.from_quat(_slerp(exact[i], suivi[i], w))
			a = list(_euler(r))
			for axe, mn, mx in (limites or {}).get(art, []):
				a[axe] = min(mx, max(mn, a[axe]))
			sortie[i][art] = tuple(a)
	return sortie


def alleger(images, articulations, tolerance=0.25, tolerance_pos=0.005, garder=()):
	"""Indices des images a garder : les autres sont redonnees par l'interpolation lineaire de Roblox entre deux cles
	gardees, a moins de 'tolerance' degres (et 'tolerance_pos' stud) pres."""
	rot = [{a: _rot(p.get(a, (0, 0, 0))) for a in articulations} for p in images]
	pos = [{k: np.array(v, float) for k, v in p.items() if k.endswith("Pos")} for p in images]
	garder = set(garder) | {0, len(images) - 1}
	gardees = [0]
	i = 0
	while i < len(images) - 1:
		j = i + 2
		while j < len(images):
			if any(k in garder for k in range(i + 1, j)):
				break
			ok = True
			for k in range(i + 1, j):
				t = (k - i) / (j - i)
				for a in articulations:
					interp = R.from_quat(_slerp(rot[i][a], rot[j][a], t))
					if math.degrees((interp * rot[k][a].inv()).magnitude()) > tolerance:
						ok = False
						break
				if ok:
					for c, v in pos[k].items():
						if c in pos[i] and c in pos[j] and np.linalg.norm(pos[i][c] + (pos[j][c] - pos[i][c]) * t - v) > tolerance_pos:
							ok = False
							break
				if not ok:
					break
			if not ok:
				break
			j += 1
		i = j - 1
		gardees.append(i)
	return gardees


def finir(cles, n_images, articulations, boucle=False, limites=None, retouche=None, **reglages):
	"""Cuisson puis allegement. Renvoie (toutes, gardees) : toutes les images en cles lineaires (pour les verifications
	du script) et les cles gardees (a ecrire). Premiere et derniere image = celles du blocage.
	retouche(images) -> images : passe propre au personnage apres la cuisson (ex. jambes recalculees image par image
	pour suivre des pas)."""
	images = cuire(cles, n_images, articulations, boucle=boucle, limites=limites, **reglages)
	if retouche:
		images = retouche(images)
	toutes = [(i, p, "Linear") for i, p in enumerate(images)]
	return toutes, [toutes[i] for i in alleger(images, articulations)]
