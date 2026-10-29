"""Peint ombre_torse_nami.png : decalque (fond transparent) pour la face avant de UpperTorso de l'avatar R15 Roblox.

Usage : uv run --with pillow assets/persos/nami/peindre_ombre_torse.py
Uniquement du modele (ombre douce sous le haut, cotes un peu plus sombres) : AUCUN detail anatomique (ni nombril, ni
traits du ventre ou du bassin) ; un decalque de ventre detaille a valu un avertissement de moderation Roblox.
La face avant de UpperTorso fait 1,943 x 1,698 studs (hauteur Blender 2,593 a 4,291) ; le haut couvre 3,42 a 4,06.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).resolve().parent
L, H = 512, 448
X0, X1, Z0, Z1 = -0.9716, 0.9716, 2.593, 4.291
OMBRE = (196, 132, 100)


def P(x, z):
	return ((x - X0) / (X1 - X0) * L, (Z1 - z) / (Z1 - Z0) * H)


def flou(dessin, rayon):
	c = Image.new("RGBA", (L, H), (0, 0, 0, 0))
	dessin(ImageDraw.Draw(c))
	return c.filter(ImageFilter.GaussianBlur(rayon))


def ombre():
	img = Image.new("RGBA", (L, H), (0, 0, 0, 0))
	img.alpha_composite(flou(lambda d: d.rectangle([P(-1, 3.44), P(1, 3.3)], fill=(*OMBRE, 110)), 7))  # sous le haut
	for s in (1, -1):  # cotes plus sombres : le bloc parait arrondi
		img.alpha_composite(flou(lambda d, s=s: d.rectangle([P(min(0.8 * s, 1.1 * s), 3.42), P(max(0.8 * s, 1.1 * s), 2.6)], fill=(*OMBRE, 80)), 12))
	img.save(DOSSIER / "ombre_torse_nami.png", optimize=True)
	print("ombre_torse_nami.png ecrit")


if __name__ == "__main__":
	ombre()
