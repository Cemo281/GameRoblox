"""Peint torse_luffy.png : decalque transparent du devant de UpperTorso (abdos, pectoraux, clavicules, cicatrice en X).

A lancer avec le Python systeme (Pillow) : python -I peindre_torse_luffy.py
Pose dans Studio : Decal Face = Front sur UpperTorso (comme UpperTorso.OmbreTorse de nami), sur la peau #E8B48C.
Coordonnees en studs dans le repere du HumanoidRootPart (x = droite du perso, y = haut) : UpperTorso couvre
x de -0,972 a 0,972 et y de -0,6 a 1,098. Vu de face, la droite du perso est a gauche de l'image.
Pas de nombril ni de detail sous la ceinture (regles Roblox, voir l'avertissement de nami).
apercu_torse_luffy.png : le decalque sur la couleur de peau, pour verifier.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).resolve().parent
X0, X1, Y0, Y1 = -0.972, 0.972, -0.6, 1.098
W, H = 1024, 896
SUR = 2  # sur-echantillonnage
PEAU = (232, 180, 140)
OMBRE = (150, 92, 62)
TRAIT = (104, 60, 40)
REFLET = (255, 234, 210)
CICATRICE = (122, 42, 34)
CICATRICE_BORD = (196, 118, 100)


def p(x, y):
	return ((X1 - x) / (X1 - X0) * W * SUR, (Y1 - y) / (Y1 - Y0) * H * SUR)


def courbe(points, n=24):
	"""Bezier quadratique / cubique a partir de 3 ou 4 points (studs) -> liste de pixels."""
	res = []
	for i in range(n + 1):
		t = i / n
		if len(points) == 3:
			a, b, c = points
			x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * b[0] + t * t * c[0]
			y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * b[1] + t * t * c[1]
		else:
			a, b, c, d = points
			x = (1 - t) ** 3 * a[0] + 3 * (1 - t) ** 2 * t * b[0] + 3 * (1 - t) * t * t * c[0] + t ** 3 * d[0]
			y = (1 - t) ** 3 * a[1] + 3 * (1 - t) ** 2 * t * b[1] + 3 * (1 - t) * t * t * c[1] + t ** 3 * d[1]
		res.append(p(x, y))
	return res


class Calque:
	"""Masque en niveaux de gris, flou puis compose dans la couleur voulue avec une opacite."""

	def __init__(self):
		self.m = Image.new("L", (W * SUR, H * SUR), 0)
		self.d = ImageDraw.Draw(self.m)

	def trait(self, pts, largeur, effile=True, valeur=255):
		"""Trait de largeur variable (studs), effile aux deux bouts."""
		dense = [pts[0]]
		for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
			k = max(1, int(math.hypot(xb - xa, yb - ya) / 1.5))
			dense += [(xa + (xb - xa) * j / k, ya + (yb - ya) * j / k) for j in range(1, k + 1)]
		n = len(dense)
		for i, (x, y) in enumerate(dense):
			t = i / max(n - 1, 1)
			r = largeur / (X1 - X0) * W * SUR / 2 * ((math.sin(math.pi * t) ** 0.6) if effile else 1)
			self.d.ellipse([x - r, y - r, x + r, y + r], fill=valeur)

	def poser(self, img, couleur, opacite, flou):
		m = self.m.filter(ImageFilter.GaussianBlur(flou * SUR)) if flou else self.m
		m = m.point(lambda v: int(v * opacite))
		img.alpha_composite(Image.merge("RGBA", (*[Image.new("L", m.size, c) for c in couleur], m)))


def peindre():
	img = Image.new("RGBA", (W * SUR, H * SUR), (0, 0, 0, 0))
	ombres, traits, reflets = Calque(), Calque(), Calque()
	for s in (1, -1):
		# clavicules
		traits.trait(courbe([(s * 0.12, 1.0), (s * 0.35, 0.96), (s * 0.62, 1.04)]), 0.025)
		# pectoraux : bord inferieur, ombre dessous, reflet sur le volume
		bas_pec = courbe([(s * 0.05, 0.64), (s * 0.18, 0.40), (s * 0.62, 0.38), (s * 0.86, 0.62)], 40)
		traits.trait(bas_pec, 0.035)
		ombres.trait(courbe([(s * 0.08, 0.6), (s * 0.2, 0.34), (s * 0.6, 0.32), (s * 0.84, 0.56)], 40), 0.1)
		reflets.trait(courbe([(s * 0.22, 0.78), (s * 0.42, 0.84), (s * 0.66, 0.74)]), 0.12)
		# abdos : bords exterieurs (lignes semi-lunaires) et separations
		traits.trait(courbe([(s * 0.36, 0.34), (s * 0.40, -0.05), (s * 0.31, -0.58)], 30), 0.03)
		ombres.trait(courbe([(s * 0.40, 0.32), (s * 0.44, -0.05), (s * 0.35, -0.58)], 30), 0.09)
		for y in (0.2, -0.07, -0.34):
			traits.trait(courbe([(s * 0.05, y + 0.01), (s * 0.18, y - 0.035), (s * 0.34, y + 0.02)]), 0.026)
			ombres.trait(courbe([(s * 0.05, y - 0.02), (s * 0.18, y - 0.065), (s * 0.34, y - 0.01)]), 0.07)
			reflets.trait(courbe([(s * 0.09, y + 0.12), (s * 0.18, y + 0.14), (s * 0.29, y + 0.12)]), 0.06)
		# dentele et obliques sur les cotes
		for k in range(3):
			y = 0.3 - 0.13 * k
			traits.trait(courbe([(s * 0.86, y + 0.06), (s * 0.74, y), (s * 0.62, y - 0.05)]), 0.022)
		traits.trait(courbe([(s * 0.62, -0.1), (s * 0.58, -0.35), (s * 0.48, -0.58)]), 0.024)
		ombres.trait(courbe([(s * 0.95, 0.9), (s * 0.93, 0.2), (s * 0.9, -0.58)]), 0.16)  # flancs
	# sternum et ligne blanche
	traits.trait(courbe([(0, 0.96), (0.005, 0.78), (0, 0.52)]), 0.028)
	traits.trait(courbe([(0, 0.4), (0.008, -0.1), (0, -0.58)], 30), 0.03)
	ombres.trait(courbe([(0, 0.95), (0, 0.2), (0, -0.58)], 30), 0.06)
	ombres.poser(img, OMBRE, 0.55, 6)
	reflets.poser(img, REFLET, 0.32, 7)
	traits.poser(img, TRAIT, 0.85, 0.8)

	# cicatrice en X : bord clair et boursoufle, coeur rouge fonce, points de couture
	cic_bord, cic = Calque(), Calque()
	branches = [[(0.56, 0.98), (0.2, 0.62), (-0.1, 0.32), (-0.44, 0.04)], [(-0.56, 0.98), (-0.2, 0.62), (0.1, 0.32), (0.44, 0.04)]]
	for b in branches:
		pts = courbe(b, 60)
		cic_bord.trait(pts, 0.09)
		cic.trait(pts, 0.05)
	cic_bord.poser(img, CICATRICE_BORD, 0.9, 1.5)
	cic.poser(img, CICATRICE, 0.92, 0.8)
	points = Calque()
	for b in branches:
		pts = courbe(b, 10)
		for i in range(1, len(pts) - 1):
			(xa, ya), (xb, yb) = pts[i - 1], pts[i + 1]
			dx, dy = xb - xa, yb - ya
			lg = math.hypot(dx, dy)
			nx, ny = -dy / lg * 24, dx / lg * 24
			x, y = pts[i]
			points.d.line([(x - nx, y - ny), (x + nx, y + ny)], fill=255, width=5)
	points.poser(img, (88, 28, 24), 0.6, 0.6)

	img = img.resize((W, H), Image.LANCZOS)
	chemin = DOSSIER / "torse_luffy.png"
	img.save(chemin)
	apercu = Image.new("RGBA", (W, H), PEAU + (255,))
	apercu.alpha_composite(img)
	apercu.convert("RGB").save(DOSSIER / "apercu_torse_luffy.png")
	return chemin


if __name__ == "__main__":
	print(peindre())
