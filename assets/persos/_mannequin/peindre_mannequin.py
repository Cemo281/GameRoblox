"""Peint tex_corps_mannequin.png (peau neutre + face anime de test) et controle_uv.png (damier par ilot).

Usage : uv run --with pillow assets/persos/_mannequin/peindre_mannequin.py
Lit uv_mannequin.json (ecrit par construire_mannequin.py). Les traits de la face sont places en studs sur
l'avant de la tete (x vers la GAUCHE du perso, z vers le haut, relatifs au centre de la tete) puis convertis en
pixels par la grille "tete.face" : un perso peut reprendre fonction_face() pour peindre sa propre face.
"""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).resolve().parent
INFOS = json.loads((DOSSIER / "uv_mannequin.json").read_text(encoding="utf-8"))
TAILLE = INFOS["taille"]
SUR = 4  # sur-echantillonnage
PEAU = (236, 199, 168)
PEAU_OMBRE = (214, 168, 140)
CONTOUR = (34, 24, 28)
IRIS_HAUT, IRIS_BAS = (48, 70, 140), (120, 175, 235)


def fonction_face(face):
	"""(x, z) en studs -> (px, py) dans la texture, par interpolation bilineaire de la grille."""
	pas, xs, zs, g = face["pas"], face["x"], face["z"], face["pixels"]

	def f(x, z):
		fx = (x - xs[0]) / pas
		fz = (z - zs[0]) / pas
		i0 = min(max(int(math.floor(fx)), 0), len(xs) - 2)
		j0 = min(max(int(math.floor(fz)), 0), len(zs) - 2)
		tx, tz = fx - i0, fz - j0
		coins = [g[j0][i0], g[j0][i0 + 1], g[j0 + 1][i0], g[j0 + 1][i0 + 1]]
		if any(c is None for c in coins):
			raise ValueError("point hors de la face : (%.2f, %.2f)" % (x, z))
		px = (coins[0][0] * (1 - tx) + coins[1][0] * tx) * (1 - tz) + (coins[2][0] * (1 - tx) + coins[3][0] * tx) * tz
		py = (coins[0][1] * (1 - tx) + coins[1][1] * tx) * (1 - tz) + (coins[2][1] * (1 - tx) + coins[3][1] * tx) * tz
		return px * SUR, py * SUR

	return f


def ellipse(cx, cz, rx, rz, n=48, debut=0.0, fin=2 * math.pi):
	return [(cx + rx * math.cos(debut + (fin - debut) * k / (n - 1)), cz + rz * math.sin(debut + (fin - debut) * k / (n - 1))) for k in range(n)]


def degrade(img, poly_px, haut, bas):
	"""Remplit le polygone d'un degrade vertical haut -> bas."""
	ys = [p[1] for p in poly_px]
	y0, y1 = int(min(ys)), int(max(ys)) + 1
	masque = Image.new("L", img.size, 0)
	ImageDraw.Draw(masque).polygon(poly_px, fill=255)
	couleur = Image.new("RGB", img.size)
	d = ImageDraw.Draw(couleur)
	for y in range(y0, y1):
		t = (y - y0) / max(y1 - y0 - 1, 1)
		d.line([(0, y), (img.size[0], y)], fill=tuple(int(haut[i] + (bas[i] - haut[i]) * t) for i in range(3)))
	img.paste(couleur, (0, 0), masque)


def oeil(img, f, cote):
	"""cote = +1 : oeil gauche du perso (x > 0), -1 : oeil droit."""
	d = ImageDraw.Draw(img)
	cx, cz = 0.205 * cote, -0.04
	P = lambda pts: [f(x, z) for x, z in pts]
	# blanc de l'oeil (haut plat, bas arrondi)
	blanc = ellipse(cx, cz, 0.105, 0.125)
	d.polygon(P(blanc), fill=(250, 250, 252))
	# iris en degrade (fonce en haut, clair en bas), pupille, reflets
	iris = ellipse(cx + 0.008 * cote, cz - 0.01, 0.075, 0.105)
	degrade(img, P(iris), IRIS_HAUT, IRIS_BAS)
	d.polygon(P(ellipse(cx + 0.008 * cote, cz - 0.0, 0.035, 0.05)), fill=(20, 22, 45))
	d.ellipse(_boite(P(ellipse(cx - 0.02 * cote, cz + 0.035, 0.026, 0.03))), fill=(255, 255, 255))
	d.ellipse(_boite(P(ellipse(cx + 0.035 * cote, cz - 0.05, 0.013, 0.015))), fill=(255, 255, 255))
	# ombre de paupiere (bande sous la ligne de cils)
	d.line(P(ellipse(cx, cz + 0.01, 0.11, 0.115, n=24, debut=math.radians(25), fin=math.radians(155))), fill=(200, 150, 140), width=int(5 * SUR))
	# ligne de cils epaisse en haut, plus epaisse vers l'exterieur
	arc = ellipse(cx, cz, 0.12, 0.13, n=32, debut=math.radians(20), fin=math.radians(160))
	if cote > 0:
		arc = arc[::-1]  # de l'interieur (vers le nez) vers l'exterieur
	pts = P(arc)
	for k in range(len(pts) - 1):
		ep = (3.5 + 4.5 * k / (len(pts) - 1)) * SUR
		d.line([pts[k], pts[k + 1]], fill=CONTOUR, width=int(ep))
	# petite pointe de cil a l'exterieur
	ext = arc[-1]
	d.line(P([ext, (ext[0] + 0.035 * cote, ext[1] + 0.012)]), fill=CONTOUR, width=int(4 * SUR))
	# trait du bas, fin
	d.line(P(ellipse(cx, cz - 0.005, 0.1, 0.125, n=16, debut=math.radians(235), fin=math.radians(305))), fill=(120, 80, 80), width=int(1.6 * SUR))
	# sourcil fin
	d.line(P([(cx - 0.085 * cote, cz + 0.175), (cx, cz + 0.205), (cx + 0.1 * cote, cz + 0.19)]), fill=(70, 45, 40), width=int(2.6 * SUR), joint="curve")


def _boite(pts):
	xs, ys = [p[0] for p in pts], [p[1] for p in pts]
	return [min(xs), min(ys), max(xs), max(ys)]


def face(img, f):
	d = ImageDraw.Draw(img)
	for cote in (1, -1):
		oeil(img, f, cote)
	# nez suggere, bouche simple
	d.line([f(0.012, -0.15), f(-0.008, -0.175)], fill=PEAU_OMBRE, width=int(3 * SUR))
	d.line([f(x, -0.29 - 0.018 * math.cos(x / 0.07 * math.pi / 2)) for x in [k * 0.007 - 0.07 for k in range(21)]], fill=(150, 80, 80), width=int(3 * SUR), joint="curve")


def texture():
	img = Image.new("RGB", (TAILLE * SUR, TAILLE * SUR), PEAU)
	face(img, fonction_face(INFOS["tete"]["face"]))
	img = img.resize((TAILLE, TAILLE), Image.LANCZOS)
	img.save(DOSSIER / "tex_corps_mannequin.png", optimize=True)


def controle():
	"""Damier de 0,1 stud sur chaque ilot du corps, damier 32 x 16 sur la tete, noms des faces."""
	img = Image.new("RGB", (TAILLE, TAILLE), (40, 40, 40))
	d = ImageDraw.Draw(img)
	dens = INFOS["densite_corps_px_par_stud"]
	couleurs = {"Avant": (230, 90, 90), "Arriere": (90, 90, 230), "Droite": (90, 200, 90), "Gauche": (230, 200, 70), "Dessus": (220, 220, 220), "Dessous": (150, 90, 200)}
	for nom, p in INFOS["pieces"].items():
		for fn, (x, y, w, h) in p["faces"].items():
			c = couleurs[fn]
			c2 = tuple(int(v * 0.65) for v in c)
			case = dens * 0.1
			for i in range(int(math.ceil(w / case))):
				for j in range(int(math.ceil(h / case))):
					xa, ya = x + i * case, y + j * case
					xb, yb = max(xa, min(x + (i + 1) * case, x + w) - 1), max(ya, min(y + (j + 1) * case, y + h) - 1)
					d.rectangle([xa, ya, xb, yb], fill=c if (i + j) % 2 == 0 else c2)
			if fn == "Avant":
				d.text((x + 2, y + 2), nom.replace("Right", "R").replace("Left", "L"), fill=(0, 0, 0))
		if "jointure" in p:
			x, y, w, h = p["jointure"]
			d.rectangle([x, y, x + w - 1, y + h - 1], fill=(255, 140, 0))
	x0, y0, x1, y1 = INFOS["tete"]["zone"]
	for i in range(32):
		for j in range(16):
			xa, xb = x0 + (x1 - x0) * i / 32, x0 + (x1 - x0) * (i + 1) / 32
			ya, yb = y0 + (y1 - y0) * j / 16, y0 + (y1 - y0) * (j + 1) / 16
			d.rectangle([xa, ya, xb - 1, yb - 1], fill=(235, 235, 235) if (i + j) % 2 == 0 else (60, 160, 200))
	f = fonction_face(INFOS["tete"]["face"])

	def pixels(points):
		res = []
		for x, z in points:
			try:
				res.append(tuple(v / SUR for v in f(x, z)))
			except ValueError:
				pass
		return res

	# lignes rouges tous les 0,1 stud sur l'avant de la tete (vue de face, doivent sortir droites et regulieres)
	for k in range(-5, 6):
		d.line(pixels([(k * 0.1, z * 0.05) for z in range(-9, 10)]), fill=(220, 30, 30), width=2)
		d.line(pixels([(x * 0.05, k * 0.1) for x in range(-10, 11)]), fill=(220, 30, 30), width=2)
	img.save(DOSSIER / "controle_uv.png", optimize=True)


if __name__ == "__main__":
	texture()
	controle()
	print("tex_corps_mannequin.png et controle_uv.png ecrits")
