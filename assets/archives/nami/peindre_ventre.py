"""Peint ventre_nami.png : decalque (fond transparent) pour la face avant de UpperTorso de l'avatar R15 Roblox.

Usage : uv run --with pillow assets/persos/nami/peindre_ventre.py
La face avant de UpperTorso fait 1,943 x 1,698 studs (x de -0,972 a 0,972, hauteur Blender 2,593 a 4,291) ; le haut vert
couvre 3,44 a 4,05 (bikini). On peint ce qui se voit : nombril, ligne mediane, traits du bassin en V, taille marquee, ombre sous le
haut, clavicules. Couleurs : ombre de la peau de la fiche (#D9A27E), en transparence pour garder la couleur du corps.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).resolve().parent
L, H = 1024, 896  # proportions de la face (1,943 x 1,698)
X0, X1, Z0, Z1 = -0.9716, 0.9716, 2.593, 4.291
OMBRE = (196, 132, 100)
TRAIT = (170, 105, 80)


def P(x, z):
	return ((x - X0) / (X1 - X0) * L, (Z1 - z) / (Z1 - Z0) * H)


def courbe(pts, n=24):
	"""Bezier quadratique (3 points) en studs -> pixels."""
	(a, b, c) = pts
	return [P((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * b[0] + t * t * c[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * b[1] + t * t * c[1]) for t in [k / (n - 1) for k in range(n)]]


def calque_flou(dessin, flou):
	c = Image.new("RGBA", (L, H), (0, 0, 0, 0))
	dessin(ImageDraw.Draw(c))
	return c.filter(ImageFilter.GaussianBlur(flou)) if flou else c


def ventre():
	img = Image.new("RGBA", (L, H), (0, 0, 0, 0))
	# ombre douce sous le haut et sur les cotes (taille marquee)
	for s in (1, -1):  # ombre douce sous chaque triangle du bikini (bas arrondi, 3,44 au plus bas)
		img.alpha_composite(calque_flou(lambda d, s=s: d.ellipse([P(min(0.06 * s, 0.84 * s), 3.5), P(max(0.06 * s, 0.84 * s), 3.38)], fill=(*OMBRE, 110)), 8))
	for s in (1, -1):
		taille = [P(0.98 * s, 3.42), P(0.8 * s, 3.05), P(0.86 * s, 2.75), P(0.98 * s, 2.6)]
		img.alpha_composite(calque_flou(lambda d, t=taille, s=s: d.polygon(t + [P(1.2 * s, 2.6), P(1.2 * s, 3.42)], fill=(*OMBRE, 110)), 16))
	# reflet doux au milieu du ventre
	img.alpha_composite(calque_flou(lambda d: d.ellipse([P(-0.3, 3.25), P(0.3, 2.75)], fill=(255, 235, 215, 25)), 40))
	# ligne mediane legere
	img.alpha_composite(calque_flou(lambda dd: dd.line([P(0, 3.3), P(0, 3.0)], fill=(*OMBRE, 60), width=8), 5))
	# traits du bassin en V (vers le jean)
	for s in (1, -1):
		img.alpha_composite(calque_flou(lambda dd, s=s: dd.line(courbe([(0.62 * s, 3.02), (0.52 * s, 2.78), (0.3 * s, 2.62)]), fill=(*TRAIT, 170), width=6, joint="curve"), 1.5))
		# petit pli de hanche au-dessus du trait
		img.alpha_composite(calque_flou(lambda dd, s=s: dd.line(courbe([(0.78 * s, 3.1), (0.74 * s, 3.0), (0.66 * s, 2.93)]), fill=(*TRAIT, 90), width=4), 1.5))
	# nombril : ovale vertical, ombre interne, petit reflet
	img.alpha_composite(calque_flou(lambda dd: dd.ellipse([P(-0.04, 2.93), P(0.04, 2.8)], fill=(*OMBRE, 150)), 4))
	img.alpha_composite(calque_flou(lambda dd: dd.line([P(0, 2.91), P(0, 2.83)], fill=(*TRAIT, 230), width=7), 1.2))
	img.alpha_composite(calque_flou(lambda dd: dd.arc([P(-0.04, 2.95), P(0.04, 2.82)], 200, 340, fill=(*TRAIT, 140), width=4), 1))
	# clavicules et ombre du cou (au-dessus du haut)
	for s in (1, -1):
		img.alpha_composite(calque_flou(lambda dd, s=s: dd.line(courbe([(0.1 * s, 4.17), (0.3 * s, 4.21), (0.5 * s, 4.19)]), fill=(*TRAIT, 150), width=5), 1.2))
	img.alpha_composite(calque_flou(lambda dd: dd.ellipse([P(-0.3, 4.32), P(0.3, 4.16)], fill=(*OMBRE, 120)), 10))
	img.save(DOSSIER / "ventre_nami.png", optimize=True)
	print("ventre_nami.png ecrit")


if __name__ == "__main__":
	ventre()
