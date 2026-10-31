"""Peint tex_chemise_luffy.png (2048 px), la texture de la chemise rouge ouverte de luffy (v2).

A lancer avec le Python systeme (Pillow, numpy), apres construire() et cuire() dans Blender (chemise_luffy.py) :
	python -I peindre_chemise_luffy.py
Entrees : chemise_luffy_atlas.json (zones, plis, details en pixels), cuisson/ao.png et cuisson/lumiere.png.
Ombrage : lumiere et occlusion cuites x relief des plis (memes formules que la geometrie, plus des petits plis peints),
passe dans une palette de rouges en aplats doux ; puis contours rouge sombre (pas de traits noirs), coutures, boutons.
"""

import json
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).resolve().parent
A = json.loads((DOSSIER / "chemise_luffy_atlas.json").read_text(encoding="utf-8"))
T = A["taille"]
ATLAS = A["atlas"]
C = A["constantes"]

# palette : facteur d'eclairage -> couleur (rouges #D62828 / #9E1A1A de la fiche au milieu)
RAMPE = [(0.0, (62, 8, 10)), (0.42, (112, 16, 18)), (0.66, (158, 26, 26)), (0.9, (214, 40, 40)), (1.08, (234, 66, 56)), (1.3, (250, 112, 92))]
INTERIEUR = (92, 14, 16)
BORD = (52, 8, 10)
CONTOUR = (104, 15, 17)  # rouge sombre : couture dans l'ombre, pas un trait d'encre
COUTURE = (118, 18, 20)
JAUNE, JAUNE_OMBRE, JAUNE_CLAIR, JAUNE_CONTOUR = (242, 194, 48), (190, 140, 26), (255, 238, 160), (120, 80, 12)
LUMIERE = np.array([0.35, 0.8, 0.5]) / np.linalg.norm([0.35, 0.8, 0.5])  # (droite du perso, haut, vers nous)


def grille(zone):
	"""Coordonnees (a, b) de chaque pixel d'une zone, et sa boite."""
	(x0, y0, w, h), (a0, a1), (b0, b1) = ATLAS[zone]
	xs = a0 + (np.arange(w) + 0.5) / w * (a1 - a0)
	ys = b0 + (np.arange(h) + 0.5) / h * (b1 - b0)
	a, b = np.meshgrid(xs, ys)
	return a, b, (x0, y0, w, h)


def champ(plis, x, y, effile=False):
	"""Somme de plis en relief le long de segments ; effile : amplitude nulle aux deux bouts (petits plis peints)."""
	f = np.zeros_like(x)
	for (ax, ay), (bx, by), amp, lg in plis:
		dx, dy = bx - ax, by - ay
		t = np.clip(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0, 1)
		d = np.hypot(x - ax - t * dx, y - ay - t * dy)
		f += amp * np.exp(-((d / lg) ** 2)) * (np.sin(np.pi * t) ** 0.7 if effile else 1)
	return f


def lisse(a, b, t):
	t = np.clip((t - a) / (b - a), 0, 1)
	return t * t * (3 - 2 * t)


def relief(f, pas_a, pas_b, sens_a=1.0):
	"""Facteur d'eclairage d'un champ de hauteur f (studs) : pente vers la lumiere, creux assombris."""
	fb, fa = np.gradient(f, pas_b, pas_a)
	fb, fa = 0.65 * fb, 0.65 * fa  # relief adouci
	fy = -fb  # b va vers le bas de l'image quand y monte
	n = np.stack([-fa * sens_a, -fy, np.ones_like(f)], -1)
	n /= np.linalg.norm(n, axis=-1, keepdims=True)
	lam = (n @ LUMIERE) / LUMIERE[2]
	return np.clip(lam, 0.3, 1.6) - 0.35 * np.clip(-f / 0.03, 0, 1)


def plis_fins(rng, n, xa, xb, ya, yb, longueur, angle, amp=(0.008, 0.016), larg=(0.035, 0.06)):
	res = []
	for _ in range(n):
		x, y = rng.uniform(xa, xb), rng.uniform(ya, yb)
		ang = math.radians(rng.uniform(*angle))
		lg = rng.uniform(*longueur)
		res.append(((x, y), (x + lg * math.cos(ang), y + lg * math.sin(ang)), rng.choice((1, 1, -1)) * rng.uniform(*amp), rng.uniform(*larg)))
	return res


def facteur_pans(zone, rng):
	a, b, boite = grille(zone)
	pas_a, pas_b = (ATLAS[zone][1][1] - ATLAS[zone][1][0]) / boite[2], (ATLAS[zone][2][1] - ATLAS[zone][2][0]) / boite[3]
	y = np.minimum(b, C["HAUT"])
	poids = 1 - lisse(C["B_ARC"] - 0.2, C["B_ARC"], b)
	if zone == "devant":
		s = np.sign(a)
		fins = plis_fins(rng, 11, 0.3, 0.95, C["OURLET"] + 0.4, 1.0, (0.3, 0.6), (-110, -60))
		f = champ(A["plis_devant"], np.abs(a) + 0.03 * s, y) + champ(fins, np.abs(a), y, True)
	else:
		fins = plis_fins(rng, 10, -0.95, 0.95, C["OURLET"] + 0.4, 0.85, (0.35, 0.7), (-105, -75))
		f = champ(A["plis_dos"], a, y) + champ(fins, a, y, True)
	# plis de traction pres de l'ourlet et sous les bras
	f += 0.012 * np.sin(a * 23 + 1.1) * lisse(C["OURLET"] + 0.25, C["OURLET"], b)
	return relief(f * poids, pas_a, -pas_b, sens_a=1.0), boite, fins


def facteur_manche(rng):
	a, b, boite = grille("manche")
	perimetre = 4.4
	t = (C["M_HAUT"] - b) / (C["M_HAUT"] - C["M_BAS"])
	tc = np.clip(t, 0, 1)
	theta = 2 * math.pi * a
	# meme formule que point_manche (chemise_luffy.py)
	d = (0.028 * np.sin(5 * theta + 3 * tc) * tc ** 0.7 + 0.018 * np.sin(9 * theta - 2 + 5 * tc) * tc
		+ 0.02 * np.sin(7 * theta + 1.3) * np.maximum(0.0, tc - 0.6) / 0.4)
	X = a * perimetre
	fins = plis_fins(rng, 14, 0, perimetre, C["M_BAS"], C["M_HAUT"], (0.25, 0.5), (-130, -50))
	fins += plis_fins(rng, 6, 0, perimetre, C["M_HAUT"] - 0.25, C["M_HAUT"], (0.3, 0.6), (-20, 20), amp=(0.006, 0.012))
	d = d + champ(fins, X, b, True)
	pas_a = perimetre / boite[2]
	pas_b = (ATLAS["manche"][2][1] - ATLAS["manche"][2][0]) / boite[3]
	return relief(d, pas_a, -pas_b), boite, fins


def facteur_poignet(rng):
	"""Fronces au-dessus du revers (meme formule que point_poignet), revers lisse un peu plus sombre en bas."""
	a, b, boite = grille("poignet")
	perimetre = 4.2
	theta = 2 * math.pi * a
	t = np.clip((C["P_HAUT"] - b) / (C["P_HAUT"] - C["P_REVERS"]), 0, 1)
	revers = b <= C["P_REVERS"]
	d = np.where(revers, 0.0, 0.014 * np.sin(6 * theta + 4 * t) * np.sin(np.pi * t) + 0.008 * np.sin(11 * theta - 1))
	fins = plis_fins(rng, 8, 0, perimetre, C["P_REVERS"] + 0.02, C["P_HAUT"], (0.12, 0.22), (-120, -60), amp=(0.005, 0.01))
	d = d + np.where(revers, 0.0, champ(fins, a * perimetre, b, True))
	pas_a = perimetre / boite[2]
	pas_b = (ATLAS["poignet"][2][1] - ATLAS["poignet"][2][0]) / boite[3]
	f = relief(d, pas_a, -pas_b)
	f = np.where(revers, 1.02 - 0.12 * lisse(C["P_REVERS"], C["P_BAS"], b), f)
	return f, boite


def rampe(f):
	q = np.round(f * 7) / 7
	f = 0.55 * f + 0.45 * q  # aplats facon anime
	xs = np.array([r[0] for r in RAMPE])
	out = np.zeros(f.shape + (3,))
	for k in range(3):
		out[..., k] = np.interp(f, xs, [r[1][k] for r in RAMPE])
	return out


def pixel(zone, a, b):
	(x0, y0, w, h), (a0, a1), (b0, b1) = ATLAS[zone]
	return (x0 + (a - a0) / (a1 - a0) * w, y0 + (b - b0) / (b1 - b0) * h)


def tirets(d, pts, couleur, largeur, tiret=16, vide=10):
	(x0, y0), (x1, y1) = pts
	lg = math.hypot(x1 - x0, y1 - y0)
	n = int(lg // (tiret + vide))
	for i in range(n + 1):
		t0, t1 = i * (tiret + vide) / lg, min((i * (tiret + vide) + tiret) / lg, 1)
		d.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0), (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=couleur, width=largeur)


def peindre():
	rng = random.Random(7)
	ao = np.asarray(Image.open(DOSSIER / "cuisson" / "ao.png").convert("L"), dtype=float) / 255
	lum = np.asarray(Image.open(DOSSIER / "cuisson" / "lumiere.png").convert("L"), dtype=float) / 255
	base = (0.62 + 0.42 * lum ** 0.8) * (0.62 + 0.38 * ao)
	f = base.copy()
	fins = {}
	for zone in ("devant", "dos"):
		fz, (x0, y0, w, h), fins[zone] = facteur_pans(zone, rng)
		f[y0 : y0 + h, x0 : x0 + w] *= fz
	fz, (x0, y0, w, h), fins["manche"] = facteur_manche(rng)
	f[y0 : y0 + h, x0 : x0 + w] *= fz
	fz, (x0, y0, w, h) = facteur_poignet(rng)
	f[y0 : y0 + h, x0 : x0 + w] *= fz
	# teintes par zone : parementure, revers et col un peu plus sombres
	masque = Image.new("L", (T, T), 0)
	dm = ImageDraw.Draw(masque)
	for poly in A["parementure"]:
		dm.polygon([tuple(p) for p in poly], fill=255)
	m = np.asarray(masque.filter(ImageFilter.GaussianBlur(2)), dtype=float) / 255
	f *= 1 - 0.16 * m
	x0, y0, w, h = ATLAS["revers"][0]
	f[y0 : y0 + h, x0 : x0 + w] *= 0.88
	img = Image.fromarray(rampe(f).astype(np.uint8))
	d = ImageDraw.Draw(img)
	for zone, c in (("interieur", INTERIEUR), ("bord", BORD)):
		x0, y0, w, h = ATLAS[zone][0]
		d.rectangle([x0, y0, x0 + w, y0 + h], fill=c)

	# coutures et contours
	for poly in A["parementure"]:
		moitie = len(poly) // 2
		piqure = poly[moitie:]
		for i in range(0, len(piqure) - 1, 2):
			d.line([tuple(piqure[i]), tuple(piqure[i + 1])], fill=COUTURE, width=3)
	for ligne in A["bord_ouvert"]:
		d.line([tuple(p) for p in ligne], fill=CONTOUR, width=5, joint="curve")
	for poly in A["revers"]:
		d.line([tuple(p) for p in poly] + [tuple(poly[0])], fill=CONTOUR, width=4, joint="curve")
		d.line([tuple(p) for p in poly[len(poly) // 2 :]], fill=(196, 44, 40), width=3)  # reflet sur le pli du revers
	for l in A["ourlets"] + [A["ourlet_poignet"]]:
		tirets(d, l, COUTURE, 4)
	for l in A["coutures_epaule"]:
		d.line([tuple(p) for p in l], fill=COUTURE, width=5)
	tirets(d, A["empiecement_dos"], COUTURE, 4)
	d.line([tuple(p) for p in A["bord_poignet"]], fill=CONTOUR, width=5)
	d.line([tuple(p) for p in A["haut_revers"]], fill=(196, 44, 40), width=4)  # reflet sur le haut du revers

	r = A["rayon_bouton"]
	for cx, cy in A["boutons"]:
		d.ellipse([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], fill=JAUNE_CONTOUR)
		d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=JAUNE_OMBRE)
		d.ellipse([cx - r, cy - r, cx + r * 0.7, cy + r * 0.6], fill=JAUNE)
		d.ellipse([cx - r * 0.6, cy - r * 0.65, cx - r * 0.1, cy - r * 0.2], fill=JAUNE_CLAIR)
		for ox in (-0.3, 0.3):  # trous du bouton
			d.ellipse([cx + ox * r - 3, cy + 0.15 * r - 3, cx + ox * r + 3, cy + 0.15 * r + 3], fill=JAUNE_CONTOUR)
	for bx, by in A["boutonnieres"]:
		d.line([(bx - r, by), (bx + r, by)], fill=(170, 34, 32), width=10)
		d.line([(bx - r, by), (bx + r, by)], fill=CONTOUR, width=5)
	chemin = DOSSIER / "tex_chemise_luffy.png"
	img.save(chemin)
	return chemin


if __name__ == "__main__":
	print(peindre())
