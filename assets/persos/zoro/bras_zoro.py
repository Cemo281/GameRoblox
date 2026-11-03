"""Shirt de zoro : bras et dos musclés style manga (le devant du torse reste au ShirtGraphic TorseZoro).

Gabarit Shirt 585 x 559, corps R15 « Blocky » : chaque face de bras (64 x 128) couvre tout le bras d'un seul
tenant (haut du bras 0-59 px, avant-bras 59-113, main 113-128). Calibré dans Studio avec un gabarit à bandes
numérotées (2026-10-31). Traits effilés en ombre de peau (comme les abdos, jamais de noir), ombrage doux sur
les bords des faces pour le volume, reflets clairs. Tout est dessiné en x4 puis réduit.
Usage : python assets/persos/zoro/bras_zoro.py -> shirt_zoro_v2.png
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).parent
S = 4
OMBRE = (150, 92, 62)
REFLET = (255, 226, 200)
VEINE = (176, 120, 110)
COUDE = 59  # pli du coude (px)
POIGNET = 113

# faces des bras : (x, y, mode) ; mode = (rôle, miroir) ; sans miroir, u = 0 côté extérieur (devant/dos)
# ou côté avant (faces latérales)
BRAS = {
	"droit": {"avant": (217, 355, False), "dos": (85, 355, True), "exterieur": (151, 355, True), "interieur": (19, 355, False)},
	"gauche": {"avant": (308, 355, True), "dos": (440, 355, False), "exterieur": (374, 355, False), "interieur": (506, 355, True)},
}
DOS = (427, 74)
FLANCS = {"droit": (165, 74, True), "gauche": (361, 74, False)}


def courbe(points, n=24):
	"""Catmull-Rom à travers les points."""
	if len(points) < 3:
		return [
			(points[0][0] + (points[-1][0] - points[0][0]) * t / n, points[0][1] + (points[-1][1] - points[0][1]) * t / n)
			for t in range(n + 1)
		]
	p = [points[0]] + list(points) + [points[-1]]
	res = []
	for i in range(1, len(p) - 2):
		p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
		for k in range(n):
			t = k / n
			t2, t3 = t * t, t * t * t
			res.append(
				tuple(
					0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
					for j in range(2)
				)
			)
	res.append(points[-1])
	return res


class Face:
	"""Dessin dans une face (coordonnées en px du gabarit, relatives à la face), avec miroir horizontal."""

	def __init__(self, calque, x, y, l, h, miroir):
		self.c, self.x, self.y, self.l, self.h, self.m = calque, x, y, l, h, miroir
		self.d = ImageDraw.Draw(calque)
		self.dr = ImageDraw.Draw(reflets)

	def pt(self, u, v):
		u = self.l - u if self.m else u
		return ((self.x + u) * S, (self.y + v) * S)

	def trait(self, points, largeur, couleur, alpha=200, effile=0.6):
		ligne = [self.pt(u, v) for u, v in courbe(points)]
		n = len(ligne) - 1
		gauche, droite = [], []
		for i, (px, py) in enumerate(ligne):
			a, b = ligne[max(i - 1, 0)], ligne[min(i + 1, n)]
			dx, dy = b[0] - a[0], b[1] - a[1]
			lg = math.hypot(dx, dy) or 1
			w = largeur * S * ((1 - effile) + effile * math.sin(math.pi * i / n)) / 2
			gauche.append((px - dy / lg * w, py + dx / lg * w))
			droite.append((px + dy / lg * w, py - dx / lg * w))
		self.d.polygon(gauche + droite[::-1], fill=couleur + (alpha,))

	def tache(self, u, v, ru, rv, couleur, alpha):
		(x0, y0), (x1, y1) = self.pt(u - ru, v - rv), self.pt(u + ru, v + rv)
		self.dr.ellipse([min(x0, x1), y0, max(x0, x1), y1], fill=couleur + (alpha,))


def volume(calque, x, y, l, h, force=70):
	"""Assombrit doucement les bords gauche et droit d'une face (forme arrondie)."""
	d = ImageDraw.Draw(calque)
	bande = l * 0.3
	for i in range(int(bande * S)):
		a = int(force * (1 - i / (bande * S)) ** 2)
		for xx in (x * S + i, (x + l) * S - 1 - i):
			d.line([(xx, y * S), (xx, (y + h) * S - 1)], fill=OMBRE + (a,))


def bras_avant(f):
	# deltoïde : arrondi de l'épaule, ombre sous le muscle
	f.trait([(4, 2), (14, 14), (30, 22), (46, 20)], 4, OMBRE, 170)
	f.tache(24, 9, 16, 7, REFLET, 80)
	# biceps : deux bords qui se rejoignent au pli du coude, reflet au sommet
	f.trait([(12, 24), (8, 38), (16, 54), (28, 58)], 4.5, OMBRE, 190)
	f.trait([(50, 24), (54, 40), (46, 54), (34, 58)], 3.5, OMBRE, 150)
	f.trait([(30, 30), (31, 40), (30, 48)], 2, OMBRE, 110)  # séparation des deux chefs
	f.tache(22, 38, 9, 12, REFLET, 90)
	f.tache(40, 38, 6, 10, REFLET, 70)
	# pli du coude
	f.trait([(20, 60), (32, 63), (44, 60)], 3, OMBRE, 170)
	# avant-bras : muscle brachio-radial (côté extérieur) et fléchisseurs
	f.trait([(6, 62), (12, 76), (20, 92), (26, 108)], 3.5, OMBRE, 160)
	f.trait([(42, 66), (40, 82), (36, 100)], 2.5, OMBRE, 120)
	f.tache(14, 78, 7, 12, REFLET, 75)
	# veines (manga) : fines, en relief
	f.trait([(34, 66), (31, 76), (34, 86), (30, 98), (32, 110)], 1.6, VEINE, 150, 0.3)
	f.trait([(31, 76), (24, 84), (22, 94)], 1.2, VEINE, 120, 0.3)
	f.trait([(38, 30), (36, 42), (38, 52)], 1.2, VEINE, 90, 0.3)
	# poignet
	f.trait([(14, 112), (32, 114), (50, 112)], 2, OMBRE, 120)


def bras_dos(f):
	# arrière du deltoïde
	f.trait([(6, 4), (16, 16), (34, 22), (52, 16)], 4, OMBRE, 160)
	# triceps en fer à cheval
	f.trait([(14, 22), (12, 36), (20, 50), (30, 54)], 4, OMBRE, 180)
	f.trait([(48, 22), (52, 36), (44, 50), (34, 54)], 3.5, OMBRE, 160)
	f.trait([(24, 40), (32, 44), (40, 40)], 3, OMBRE, 150)
	f.tache(20, 34, 7, 10, REFLET, 80)
	f.tache(42, 32, 6, 9, REFLET, 70)
	# pointe du coude
	f.trait([(26, 58), (32, 62), (38, 58)], 2.5, OMBRE, 160)
	f.trait([(28, 64), (32, 66), (36, 64)], 1.5, OMBRE, 110)
	# extenseurs de l'avant-bras
	f.trait([(18, 68), (16, 84), (22, 104)], 3, OMBRE, 140)
	f.trait([(44, 68), (46, 86), (40, 104)], 3, OMBRE, 130)
	f.tache(30, 80, 8, 12, REFLET, 70)
	# dos de la main : tendons
	for u in (18, 28, 38, 48):
		f.trait([(u, 114), (u + 1, 126)], 1.2, OMBRE, 90)


def bras_exterieur(f):
	# u = 0 côté avant : coiffe du deltoïde en V, séparation biceps / triceps
	f.trait([(4, 4), (16, 22), (32, 32), (48, 22), (60, 4)], 4.5, OMBRE, 180)
	f.tache(32, 14, 18, 9, REFLET, 90)
	f.trait([(32, 34), (31, 46), (32, 58)], 3, OMBRE, 150)
	f.tache(16, 44, 7, 10, REFLET, 75)
	f.tache(48, 44, 7, 10, REFLET, 65)
	# coude et avant-bras
	f.trait([(22, 60), (32, 62), (42, 60)], 2.5, OMBRE, 130)
	f.trait([(20, 66), (26, 84), (30, 108)], 3, OMBRE, 140)
	f.trait([(36, 64), (40, 74), (36, 88), (40, 100)], 1.4, VEINE, 120, 0.3)
	f.tache(14, 80, 6, 12, REFLET, 70)


def bras_interieur(f):
	# u = 0 côté avant : bord du biceps et veine principale
	f.trait([(14, 22), (10, 40), (18, 56)], 3, OMBRE, 130)
	f.trait([(40, 18), (44, 36), (40, 56)], 2.5, OMBRE, 110)
	f.trait([(26, 14), (28, 30), (24, 46), (28, 60), (24, 78), (28, 96), (26, 110)], 1.8, VEINE, 150, 0.3)
	f.trait([(24, 78), (16, 90), (14, 104)], 1.3, VEINE, 110, 0.3)
	f.trait([(18, 64), (22, 86), (30, 108)], 2.5, OMBRE, 110)


def dos(f):
	# trapèzes du cou aux épaules
	f.trait([(52, 2), (40, 10), (18, 16), (2, 18)], 4, OMBRE, 160)
	f.trait([(76, 2), (88, 10), (110, 16), (126, 18)], 4, OMBRE, 160)
	# colonne
	f.trait([(64, 8), (63, 50), (64, 90), (64, 126)], 3.5, OMBRE, 170, 0.4)
	# omoplates
	f.trait([(52, 26), (36, 30), (26, 46), (36, 60), (54, 54)], 3.5, OMBRE, 150)
	f.trait([(76, 26), (92, 30), (102, 46), (92, 60), (74, 54)], 3.5, OMBRE, 150)
	f.tache(40, 44, 11, 12, REFLET, 75)
	f.tache(88, 44, 11, 12, REFLET, 75)
	# grands dorsaux en V
	f.trait([(8, 34), (14, 64), (34, 92), (54, 114)], 4, OMBRE, 160)
	f.trait([(120, 34), (114, 64), (94, 92), (74, 114)], 4, OMBRE, 160)
	f.tache(28, 76, 10, 18, REFLET, 65)
	f.tache(100, 76, 10, 18, REFLET, 65)
	# érecteurs de part et d'autre de la colonne, en bas
	f.trait([(56, 84), (54, 104), (56, 124)], 2.5, OMBRE, 120)
	f.trait([(72, 84), (74, 104), (72, 124)], 2.5, OMBRE, 120)


def flanc(f):
	# u = 0 côté avant : dentelés en dents de scie, bord du grand dorsal
	for v in (40, 54, 68, 82):
		f.trait([(4, v), (16, v + 4), (26, v + 2)], 3, OMBRE, 150)
	f.trait([(40, 20), (36, 50), (40, 80), (46, 110)], 3.5, OMBRE, 150)
	f.tache(16, 30, 10, 10, REFLET, 70)
	f.trait([(10, 96), (18, 112), (22, 126)], 3, OMBRE, 130)  # obliques


calque = Image.new("RGBA", (585 * S, 559 * S), (0, 0, 0, 0))
ombres = Image.new("RGBA", (585 * S, 559 * S), (0, 0, 0, 0))
reflets = Image.new("RGBA", (585 * S, 559 * S), (0, 0, 0, 0))
for cote, faces in BRAS.items():
	for role, (x, y, miroir) in faces.items():
		volume(ombres, x, y, 64, 128)
		f = Face(calque, x, y, 64, 128, miroir)
		{"avant": bras_avant, "dos": bras_dos, "exterieur": bras_exterieur, "interieur": bras_interieur}[role](f)
volume(ombres, DOS[0], DOS[1], 128, 128, 50)
dos(Face(calque, DOS[0], DOS[1], 128, 128, False))
for x, y, miroir in FLANCS.values():
	volume(ombres, x, y, 64, 128, 40)
	flanc(Face(calque, x, y, 64, 128, miroir))

ombres = ombres.filter(ImageFilter.GaussianBlur(3 * S))
calque = calque.filter(ImageFilter.GaussianBlur(0.6 * S))
reflets = reflets.filter(ImageFilter.GaussianBlur(4 * S))
image = Image.alpha_composite(Image.alpha_composite(ombres, reflets), calque).resize((585, 559), Image.LANCZOS)
image.save(DOSSIER / "shirt_zoro_v2.png")
print("ok", image.size)
