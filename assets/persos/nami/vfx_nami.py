"""Textures des effets de nami (fond transparent) : vfx/piece.png (piece d'or), vfx/eclair.png (eclair vertical en
zigzag, pour les rafales de foudre), vfx/arc.png (petits arcs electriques, pour la charge du baton).

Usage : uv run --with pillow assets/persos/nami/vfx_nami.py
Les autres effets utilisent des textures de Roblox (fumee, etincelles) et l'anneau de zoro (101774142734315).
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).resolve().parent / "vfx"
T = 128


def piece():
	img = Image.new("RGBA", (T * 2, T * 2), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	c, r = T, T - 8
	d.ellipse([c - r, c - r, c + r, c + r], fill=(176, 120, 22, 255))  # tranche foncee
	d.ellipse([c - r + 10, c - r + 10, c + r - 10, c + r - 10], fill=(244, 196, 58, 255))  # face
	d.ellipse([c - r + 30, c - r + 30, c + r - 30, c + r - 30], outline=(196, 140, 30, 255), width=8)  # filet
	# etoile au centre (pas de symbole monetaire reel)
	pts = []
	for k in range(10):
		a = -math.pi / 2 + k * math.pi / 5
		rr = 44 if k % 2 == 0 else 18
		pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
	d.polygon(pts, fill=(255, 226, 120, 255))
	# reflet
	d.ellipse([c - r + 26, c - r + 22, c - 10, c - 30], fill=(255, 246, 200, 150))
	img = img.filter(ImageFilter.GaussianBlur(0.8)).resize((T, T), Image.LANCZOS)
	DOSSIER.mkdir(exist_ok=True)
	img.save(DOSSIER / "piece.png", optimize=True)
	print("vfx/piece.png ecrit")


def zigzag(rnd, depart, arrivee, n, ecart):
	"""Polyligne brisee de depart a arrivee (n segments, ecart lateral aleatoire)."""
	(x0, y0), (x1, y1) = depart, arrivee
	pts = [depart]
	for k in range(1, n):
		t = k / n
		pts.append((x0 + (x1 - x0) * t + rnd.uniform(-ecart, ecart), y0 + (y1 - y0) * t + rnd.uniform(-ecart * 0.2, ecart * 0.2)))
	pts.append(arrivee)
	return pts


def trait_lumineux(taille, chemins, epaisseur, halo):
	"""Traits blancs avec un halo jaune pale flou (style anime)."""
	halo_img = Image.new("RGBA", (taille, taille), (0, 0, 0, 0))
	dh = ImageDraw.Draw(halo_img)
	coeur = Image.new("RGBA", (taille, taille), (0, 0, 0, 0))
	dc = ImageDraw.Draw(coeur)
	for pts, f in chemins:
		dh.line(pts, fill=(255, 235, 120, 200), width=int(epaisseur * f * 3), joint="curve")
		dc.line(pts, fill=(255, 255, 255, 255), width=max(1, int(epaisseur * f)), joint="curve")
	img = halo_img.filter(ImageFilter.GaussianBlur(halo))
	img.alpha_composite(coeur)
	return img


def eclair():
	rnd = random.Random(4)
	T2 = 256
	tronc = zigzag(rnd, (T2 / 2, 0), (T2 / 2 + 10, T2), 9, 34)
	chemins = [(tronc, 1.0)]
	for k in (3, 5, 7):  # branches
		x, y = tronc[k]
		chemins.append((zigzag(rnd, (x, y), (x + rnd.choice((-1, 1)) * rnd.uniform(40, 70), y + rnd.uniform(40, 70)), 4, 12), 0.5))
	img = trait_lumineux(T2, chemins, 7, 6)
	DOSSIER.mkdir(exist_ok=True)
	img.save(DOSSIER / "eclair.png", optimize=True)
	print("vfx/eclair.png ecrit")


def arc():
	rnd = random.Random(9)
	T2 = 128
	chemins = []
	for _ in range(3):
		a = rnd.uniform(0, math.pi)
		r = 50
		depart = (T2 / 2 + r * math.cos(a), T2 / 2 + r * math.sin(a))
		arrivee = (T2 / 2 - r * math.cos(a), T2 / 2 - r * math.sin(a))
		chemins.append((zigzag(rnd, depart, arrivee, 6, 16), 0.7))
	img = trait_lumineux(T2, chemins, 4, 3)
	img.save(DOSSIER / "arc.png", optimize=True)
	print("vfx/arc.png ecrit")


if __name__ == "__main__":
	piece()
	eclair()
	arc()
