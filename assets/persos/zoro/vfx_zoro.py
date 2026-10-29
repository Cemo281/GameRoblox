"""Textures des VFX de zoro (style anime : formes nettes, coeur blanc, bord vert), fond transparent.

entaille.png : arc de lumiere (Entaille_Droite / Entaille_Gauche)
anneau.png   : anneau de vent vu de dessus (Tornade_Sabres)
eclat.png    : etoile a 4 branches (Eclat_Garde)
Usage : uv run --with pillow assets/persos/zoro/vfx_zoro.py
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).parent / "vfx"
S = 2  # dessin en 2x puis reduction


def hexa(h, a=255):
	h = h.lstrip("#")
	return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def croissant(d, cx, cy, r, ep, a0, a1, couleur, n=80):
	"""Croissant effile aux deux bouts : bord exterieur sur le cercle r, epaisseur max ep au milieu."""
	ext, inte = [], []
	for i in range(n + 1):
		t = i / n
		a = math.radians(a0 + (a1 - a0) * t)
		e = ep * math.sin(math.pi * t) ** 0.8
		ext.append((cx + r * math.cos(a), cy + r * math.sin(a)))
		inte.append((cx + (r - e) * math.cos(a), cy + (r - e) * math.sin(a)))
	d.polygon(ext + inte[::-1], fill=couleur)


def entaille():
	w, h = 1024 * S // 2, 512 * S // 2
	img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
	halo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
	# arc de 100 deg qui tient dans l'image (pointes effilees visibles)
	r = w * 0.58
	cx, cy = w / 2, h * 0.18 + r
	croissant(ImageDraw.Draw(halo), cx, cy, r + 6 * S, 80 * S, 218, 322, hexa("6FE38F", 200))
	img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(10 * S)))
	d = ImageDraw.Draw(img)
	croissant(d, cx, cy, r, 62 * S, 220, 320, hexa("3FCF6B"))  # bord vert
	croissant(d, cx, cy, r - 6 * S, 46 * S, 223, 317, hexa("D8FFE4"))  # transition
	croissant(d, cx, cy, r - 10 * S, 30 * S, 227, 313, hexa("FFFFFF"))  # coeur blanc
	img.resize((1024 // 2, 512 // 2), Image.LANCZOS).save(DOSSIER / "entaille.png")


def anneau():
	t = 512 * S
	img = Image.new("RGBA", (t, t), (0, 0, 0, 0))
	halo = Image.new("RGBA", (t, t), (0, 0, 0, 0))
	c = t / 2
	ImageDraw.Draw(halo).ellipse([c - 230 * S, c - 230 * S, c + 230 * S, c + 230 * S], outline=hexa("A8F5B8", 180), width=40 * S)
	img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(12 * S)))
	d = ImageDraw.Draw(img)
	d.ellipse([c - 220 * S, c - 220 * S, c + 220 * S, c + 220 * S], outline=hexa("CFFAD8", 230), width=18 * S)
	# traits de vent en spirale, nets, qui donnent le sens de rotation
	for k in range(10):
		a0 = k * 36
		croissant(d, c, c, (200 - 14 * (k % 3)) * S, 16 * S, a0, a0 + 55, hexa("FFFFFF", 235))
		croissant(d, c, c, (165 - 10 * (k % 2)) * S, 10 * S, a0 + 18, a0 + 48, hexa("B8F7C6", 210))
	img.resize((512, 512), Image.LANCZOS).save(DOSSIER / "anneau.png")


def eclat():
	t = 256 * S
	img = Image.new("RGBA", (t, t), (0, 0, 0, 0))
	halo = Image.new("RGBA", (t, t), (0, 0, 0, 0))
	c = t / 2
	ImageDraw.Draw(halo).ellipse([c - 60 * S, c - 60 * S, c + 60 * S, c + 60 * S], fill=hexa("FFD84A", 170))
	img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(18 * S)))
	d = ImageDraw.Draw(img)
	for (l, e), coul in (((120, 26), hexa("E8C33A")), ((100, 16), hexa("FFF2A8")), ((70, 7), hexa("FFFFFF"))):
		pts = []
		for i in range(8):
			a = math.radians(i * 45 - 90)
			rr = (l if i % 2 == 0 else e) * S
			pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
		d.polygon(pts, fill=coul)
	img.resize((256, 256), Image.LANCZOS).save(DOSSIER / "eclat.png")


if __name__ == "__main__":
	DOSSIER.mkdir(exist_ok=True)
	entaille()
	anneau()
	eclat()
	print("entaille.png, anneau.png, eclat.png")
