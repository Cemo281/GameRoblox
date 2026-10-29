"""Vetements classiques (Shirt / Pants 585x559) et face (512x512) de zoro, style anime (cel-shading).

Zones : assets/persos/_mannequin/zones_vetements.json.
Style : aplats nets (pas de flou), deux tons d'ombre, reflets francs, traits d'encre effiles.
Lumiere : en haut a gauche de chaque face vue de face (droite du perso), donc ombres a droite et en bas.
Usage : uv run --with pillow assets/persos/zoro/peindre_zoro.py
"""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

DOSSIER = Path(__file__).parent
ZONES = json.loads((DOSSIER.parent / "_mannequin" / "zones_vetements.json").read_text(encoding="utf-8"))["zones"]
TAILLE = (585, 559)
S = 4  # sur-echantillonnage : dessin en 4x puis reduction (traits nets mais lisses)


def hexa(h, a=255):
	h = h.lstrip("#")
	return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


PEAU = hexa("E2B48C")
PEAU_LUMIERE = hexa("F4D0AC")
PEAU_OMBRE = hexa("B98560")
PEAU_OMBRE2 = hexa("9A6644")
PEAU_TRAIT = hexa("7E5238")
ENCRE = hexa("4A2818")
HARA = hexa("3E8B4A")
HARA_L = hexa("6CBF74")
HARA_F = hexa("255A30")
HARA_ENCRE = hexa("10301A")
PANT = hexa("1A1A1A")
PANT_L = hexa("383838")
PANT_L2 = hexa("4E4E4E")
PANT_F = hexa("0A0A0A")
BOTTE = hexa("0F0F0F")
BOTTE_L = hexa("3C3C3C")
OR = hexa("E8C33A")
OR_F = hexa("9C7A14")
CICATRICE = hexa("7A2A22")
NOIR = hexa("101010")


def rect(groupe, face):
	return ZONES[groupe]["faces"][face]["rect"]


class Calque:
	"""Dessin dans une zone, en coordonnees locales (pixels du modele), sur l'image sur-echantillonnee."""

	def __init__(self, img, r):
		self.x, self.y, self.w, self.h = r
		self.d = ImageDraw.Draw(img)

	def p(self, pts):
		return [((self.x + a) * S, (self.y + b) * S) for a, b in pts]

	def rect(self, x0, y0, x1, y1, c):
		self.d.rectangle([(self.x + x0) * S, (self.y + y0) * S, (self.x + x1) * S - 1, (self.y + y1) * S - 1], fill=c)

	def poly(self, pts, c):
		self.d.polygon(self.p(pts), fill=c)

	def miroir(self, pts):
		return [(self.w - x, y) for x, y in pts]

	def trait(self, pts, c, w0, w1=None, w_mil=None):
		"""Trait d'encre effile : epaisseur w0 au debut, w_mil au milieu, w1 a la fin."""
		w1 = w0 if w1 is None else w1
		w_mil = max(w0, w1) if w_mil is None else w_mil
		n = len(pts) - 1
		for i in range(n):
			for k in range(4):
				t0, t1 = (i + k / 4) / n, (i + (k + 1) / 4) / n
				a = (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k / 4, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k / 4)
				b = (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * (k + 1) / 4, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * (k + 1) / 4)
				t = (t0 + t1) / 2
				w = (w0 + (w_mil - w0) * t * 2) if t < 0.5 else (w_mil + (w1 - w_mil) * (t - 0.5) * 2)
				pa, pb = self.p([a, b])
				self.d.line([pa, pb], fill=c, width=max(1, round(w * S)))
				r = w * S / 2
				self.d.ellipse([pb[0] - r, pb[1] - r, pb[0] + r, pb[1] + r], fill=c)


def courbe(pts, n=6):
	"""Lissage de Chaikin d'une polyligne (formes de muscles arrondies)."""
	for _ in range(n // 2):
		nv = [pts[0]]
		for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
			nv += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1), (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
		nv.append(pts[-1])
		pts = nv
	return pts


def finir(img, groupes, nom):
	"""Reduction 4x -> taille Roblox, puis decoupe des zones."""
	img = img.resize(TAILLE, Image.LANCZOS)
	m = Image.new("L", TAILLE, 0)
	d = ImageDraw.Draw(m)
	for g in groupes:
		for f in ZONES[g]["faces"].values():
			x, y, w, h = f["rect"]
			d.rectangle([x, y, x + w - 1, y + h - 1], fill=255)
	out = Image.new("RGBA", TAILLE, (0, 0, 0, 0))
	out.paste(img, (0, 0), m)
	out.save(DOSSIER / nom)


# ---------------------------------------------------------------- haramaki

HARA_HAUT = 86  # ligne du torse ou commence le haramaki


def haramaki(c, y0, y1, w):
	"""Cotes en cel-shading : dessus eclaire, liseré clair, dessous dans l'ombre, encre en haut et en bas."""
	c.rect(0, y0, w, y1, HARA)
	n = 6
	h = (y1 - y0) / n
	for i in range(n):
		ya = y0 + i * h
		c.rect(0, ya + h * 0.55, w, ya + h, HARA_F)
		c.rect(0, ya + 1, w, ya + 2.2, HARA_L)
		c.trait([(0, ya + h), (w, ya + h)], HARA_ENCRE, 1)
	# ombre portee par le torse sur le haut du haramaki
	c.poly([(0, y0), (w, y0), (w, y0 + 3), (0, y0 + 3)], HARA_F)
	c.trait([(0, y0), (w, y0)], HARA_ENCRE, 2)


# ---------------------------------------------------------------- torse


def torse_avant(c):
	w = 128
	c.rect(0, 0, w, HARA_HAUT, PEAU)
	# ombre portee du cou / de la tete
	c.poly(courbe([(44, 0), (84, 0), (78, 7), (64, 10), (50, 7)]), PEAU_OMBRE)
	# flancs dans l'ombre (le cote droit de l'image plus large : lumiere a gauche)
	c.poly(courbe([(0, 6), (6, 14), (10, 40), (16, 70), (14, 86), (0, 86)]), PEAU_OMBRE)
	c.poly(courbe([(128, 4), (116, 14), (110, 40), (104, 70), (106, 86), (128, 86)]), PEAU_OMBRE)
	c.poly(courbe([(128, 20), (122, 40), (120, 86), (128, 86)]), PEAU_OMBRE2)
	# pectoraux : ombre portee sous chaque pec (aplat net) + reflet en croissant
	for s in (1, -1):
		def m(pts):
			return pts if s == 1 else c.miroir(pts)

		c.poly(m(courbe([(62, 30), (56, 39), (44, 44), (28, 43), (14, 38), (8, 30), (18, 44), (32, 49), (48, 49), (60, 42)])), PEAU_OMBRE)
		c.poly(m(courbe([(20, 18), (34, 14), (50, 16), (42, 20), (28, 24)])), PEAU_LUMIERE)
	# sillon du sternum
	c.poly([(62, 10), (66, 10), (65, 44), (63, 44)], PEAU_OMBRE)
	# abdominaux : 3 rangees de 2 blocs, ombre en L (bas + cote droit) et reflet en haut a gauche
	for i in range(3):
		y = 48 + i * 12
		for x0, x1 in ((38, 61), (67, 90)):
			c.poly([(x0, y + 8), (x1, y + 8), (x1, y), (x1 + 2, y), (x1 + 2, y + 11), (x0 + 1, y + 11)], PEAU_OMBRE)
			c.poly([(x0 + 3, y + 1), (x0 + 12, y + 1), (x0 + 9, y + 3), (x0 + 3, y + 4)], PEAU_LUMIERE)
	# ligne blanche
	c.poly([(63, 46), (65, 46), (65, 86), (63, 86)], PEAU_OMBRE2)
	# obliques : aplats en biseau
	c.poly(courbe([(30, 46), (36, 64), (44, 86), (36, 86), (28, 64)]), PEAU_OMBRE)
	c.poly(courbe([(98, 46), (92, 64), (84, 86), (94, 86), (102, 64)]), PEAU_OMBRE2)


def torse_avant_traits(c):
	e = ENCRE
	# clavicules
	c.trait(courbe([(20, 9), (40, 12), (58, 11)]), e, 0.5, 0.5, 1.6)
	c.trait(courbe([(108, 9), (88, 12), (70, 11)]), e, 0.5, 0.5, 1.6)
	# bord inferieur des pectoraux : epais au milieu, effile aux bouts
	for s in (1, -1):
		pts = courbe([(62, 14), (61, 30), (56, 39), (44, 43), (28, 42), (16, 37), (8, 28)])
		c.trait(pts if s == 1 else c.miroir(pts), e, 0.6, 0.6, 2.6)
	c.trait([(64, 14), (64, 40)], e, 0.5, 0.5, 1.4)
	# abdominaux
	for i in range(3):
		y = 50 + i * 12
		c.trait(courbe([(38, y + 7), (50, y + 9), (61, y + 7)]), e, 0.5, 0.8, 1.8)
		c.trait(courbe([(67, y + 7), (78, y + 9), (90, y + 7)]), e, 0.8, 0.5, 1.8)
	c.trait([(64, 46), (64, 84)], e, 0.6, 0.6, 1.6)
	# obliques et dentele
	c.trait(courbe([(30, 46), (34, 66), (42, 85)]), e, 0.5, 1.4, 1.8)
	c.trait(courbe([(98, 46), (94, 66), (86, 85)]), e, 0.5, 1.4, 1.8)
	for y in (46, 53, 60):
		c.trait([(16, y), (26, y + 3)], e, 1.4, 0.4)
		c.trait([(112, y), (102, y + 3)], e, 1.4, 0.4)


def cicatrice(c, a, b):
	"""Cicatrice rouge fonce en relief (reflet), points de suture noirs en croix."""
	(x0, y0), (x1, y1) = a, b
	long = math.hypot(x1 - x0, y1 - y0)
	dx, dy = (x1 - x0) / long, (y1 - y0) / long
	px, py = -dy, dx
	n = 8
	pts = [(x0 + (x1 - x0) * i / n + px * (1 if i % 2 else -1) * (0 if i in (0, n) else 0.8), y0 + (y1 - y0) * i / n + py * (1 if i % 2 else -1) * (0 if i in (0, n) else 0.8)) for i in range(n + 1)]
	c.trait(pts, hexa("3A100C"), 2, 2, 5.5)
	c.trait(pts, CICATRICE, 1.2, 1.2, 3.6)
	c.trait([(x + px * 0.8, y + py * 0.8) for x, y in pts[1:-1]], hexa("B05A4C"), 0.6, 0.6, 1.0)
	for i in range(1, int(long / 10)):
		cx, cy = x0 + (x1 - x0) * i / int(long / 10), y0 + (y1 - y0) * i / int(long / 10)
		for sg in (1, -1):
			c.trait([(cx - px * 5 - dx * 3 * sg, cy - py * 5 - dy * 3 * sg), (cx + px * 5 + dx * 3 * sg, cy + py * 5 + dy * 3 * sg)], NOIR, 1.1)


def torse_dos(c):
	c.rect(0, 0, 128, HARA_HAUT, PEAU)
	# colonne et creux du bas du dos
	c.poly(courbe([(61, 0), (67, 0), (68, 60), (72, 86), (56, 86), (60, 60)]), PEAU_OMBRE)
	# omoplates : ombre sous le bord inferieur, reflet sur le dessus
	for s in (1, -1):
		def m(pts):
			return pts if s == 1 else c.miroir(pts)

		c.poly(m(courbe([(14, 26), (28, 48), (52, 54), (54, 58), (26, 54), (10, 34)])), PEAU_OMBRE)
		c.poly(m(courbe([(18, 16), (32, 10), (48, 14), (36, 18)])), PEAU_LUMIERE)
		c.poly(m(courbe([(0, 50), (12, 60), (16, 86), (0, 86)])), PEAU_OMBRE)
	c.poly(courbe([(128, 30), (118, 60), (114, 86), (128, 86)]), PEAU_OMBRE2)


def torse_dos_traits(c):
	e = ENCRE
	c.trait([(64, 6), (64, 84)], e, 0.5, 0.5, 1.6)
	for s in (1, -1):
		def m(pts):
			return pts if s == 1 else c.miroir(pts)

		c.trait(m(courbe(arc_pts(34, 26, 22, 18, 200, 340))), e, 0.4, 0.4, 1.8)
		c.trait(m(courbe([(14, 26), (28, 48), (52, 54)])), e, 0.5, 0.5, 2.2)
		c.trait(m(courbe([(8, 62), (22, 72), (30, 84)])), e, 0.5, 0.5, 1.6)


def arc_pts(cx, cy, rx, ry, a0, a1, n=12):
	return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def torse_cote(c, avant_a_droite):
	"""Face laterale : moitie arriere dans l'ombre (aplat), dentele et grand dorsal dessines."""
	c.rect(0, 0, 64, HARA_HAUT, PEAU)
	dos = [(0, 0), (22, 0), (18, 30), (26, 60), (22, 86), (0, 86)]
	c.poly(courbe(dos if avant_a_droite else c.miroir(dos)), PEAU_OMBRE)
	# reflet vertical cote avant
	ref = [(46, 10), (52, 10), (50, 70), (44, 70)]
	c.poly(ref if avant_a_droite else c.miroir(ref), PEAU_LUMIERE)


def torse_cote_traits(c, avant_a_droite):
	e = ENCRE
	dorsal = courbe([(20, 14), (30, 46), (40, 86)])
	c.trait(dorsal if avant_a_droite else c.miroir(dorsal), e, 0.5, 0.5, 2.0)
	for y in (34, 44, 54):
		pts = [(44, y), (58, y + 4)]
		c.trait(pts if avant_a_droite else c.miroir(pts), e, 1.6, 0.4)


def torse_haut(c):
	c.rect(0, 0, 128, 64, PEAU)
	c.poly([(0, 0), (128, 0), (128, 5), (0, 5)], PEAU_OMBRE)
	c.poly(courbe([(46, 16), (82, 16), (82, 48), (46, 48)]), PEAU_OMBRE)


# ---------------------------------------------------------------- bras


def bras(c, face):
	"""Bras nu : lignes 0-64 haut du bras, 64-112 avant-bras, 112-128 main. face = Front, Back, EXT ou INT."""
	c.rect(0, 0, 64, 128, PEAU)
	o, o2, l = PEAU_OMBRE, PEAU_OMBRE2, PEAU_LUMIERE
	if face == "INT":
		# cote du torse : presque tout dans l'ombre
		c.rect(0, 0, 64, 128, o)
		c.poly(courbe([(20, 26), (40, 26), (38, 58), (22, 58)]), PEAU)
	else:
		# bord droit de chaque face dans l'ombre, creux du coude, poignet
		c.poly(courbe([(64, 0), (50, 4), (46, 30), (52, 60), (46, 90), (50, 112), (64, 112)]), o)
		c.poly([(0, 58), (64, 58), (64, 64), (0, 64)], o)
		c.poly([(0, 104), (64, 104), (64, 112), (0, 112)], o)
	if face == "Front":
		# biceps : reflet en amande, ombre sous le muscle
		c.poly(courbe([(22, 26), (30, 20), (36, 26), (34, 46), (28, 50), (22, 44)]), l)
		c.poly(courbe([(16, 50), (32, 56), (48, 50), (46, 58), (18, 58)]), o2)
		c.poly(courbe([(20, 70), (28, 68), (30, 96), (24, 98)]), l)
	elif face == "Back":
		c.poly(courbe([(22, 24), (24, 44), (32, 52), (40, 44), (42, 24), (38, 44), (32, 48), (26, 44)]), o2)
		c.poly(courbe([(14, 70), (20, 68), (22, 98), (16, 98)]), l)
	elif face == "EXT":
		# deltoide : calotte eclairee, ombre nette sous le muscle
		c.poly(courbe([(8, 4), (32, 0), (56, 4), (44, 14), (32, 20), (20, 14)]), l)
		c.poly(courbe([(4, 16), (20, 24), (32, 28), (44, 24), (60, 16), (54, 30), (32, 34), (10, 30)]), o)
		c.poly(courbe([(20, 72), (26, 70), (28, 100), (22, 100)]), l)
	# main : ombre en bas, phalanges
	c.poly([(0, 122), (64, 122), (64, 128), (0, 128)], o)


def bras_traits(c, face):
	e = ENCRE
	if face in ("Front", "EXT", "Back"):
		c.trait(courbe(arc_pts(32, 4, 28, 20, 20, 160)), e, 0.4, 0.4, 1.8)
	if face == "Front":
		c.trait(courbe([(14, 26), (12, 40), (16, 54)]), e, 0.4, 0.4, 1.6)
		c.trait(courbe([(50, 26), (52, 40), (48, 54)]), e, 0.4, 0.4, 1.8)
		c.trait(courbe([(24, 60), (32, 63), (40, 60)]), e, 0.4, 0.4, 1.4)
		c.trait(courbe([(14, 72), (18, 90), (22, 106)]), e, 0.4, 0.4, 1.4)
		c.trait(courbe([(46, 72), (44, 90), (40, 106)]), e, 0.4, 0.4, 1.6)
	elif face == "Back":
		c.trait(courbe([(22, 24), (24, 44), (32, 52), (40, 44), (42, 24)]), e, 0.4, 0.4, 1.8)
		c.trait([(30, 74), (32, 104)], e, 0.4, 0.4, 1.2)
	elif face == "EXT":
		c.trait(courbe([(16, 30), (28, 44), (30, 56)]), e, 0.4, 0.4, 1.6)
		c.trait(courbe([(20, 74), (26, 92), (24, 106)]), e, 0.4, 0.4, 1.4)
	else:
		c.trait([(30, 30), (32, 54)], e, 0.4, 0.4, 1.2)
	if face in ("Front", "Back", "EXT"):
		for x in (16, 28, 40):
			c.trait([(x, 115), (x, 122)], e, 0.4, 1.0)


# ---------------------------------------------------------------- pantalon et bottes


def jambe(c, face):
	"""Pantalon noir (0-92) et botte (92-128) en cel-shading."""
	c.rect(0, 0, 64, 128, PANT)
	# reflets francs sur le tissu, a gauche (cote lumiere)
	c.poly(courbe([(10, 4), (22, 4), (20, 40), (16, 50), (12, 40)]), PANT_L)
	c.poly(courbe([(12, 70), (20, 70), (18, 86), (14, 86)]), PANT_L)
	# bord droit dans l'ombre
	c.poly([(54, 0), (64, 0), (64, 92), (56, 92)], PANT_F)
	# plis du genou en Z : aplats clairs et sombres
	for y, d in ((50, 0), (60, 4), (70, -2)):
		c.poly([(8 + d, y), (34 + d, y + 4), (54 + d, y), (52 + d, y + 3), (34 + d, y + 8), (10 + d, y + 3)], PANT_L)
		c.poly([(10 + d, y + 3), (34 + d, y + 8), (52 + d, y + 3), (50 + d, y + 6), (34 + d, y + 11), (12 + d, y + 6)], PANT_F)
	# plis du pantalon qui tombe dans la botte
	c.poly(courbe([(4, 84), (16, 90), (28, 86), (40, 91), (58, 86), (58, 92), (4, 92)]), PANT_F)
	# botte : reflet net sur le cote lumiere et la pointe
	c.rect(0, 92, 64, 128, BOTTE)
	c.rect(0, 92, 64, 99, hexa("1E1E1E"))
	c.poly(courbe([(8, 101), (14, 101), (14, 120), (8, 122)]), BOTTE_L)
	c.rect(0, 92, 64, 94, BOTTE_L)
	if face == "Front":
		c.poly(courbe([(14, 122), (32, 118), (50, 122), (32, 120)]), BOTTE_L)


def jambe_traits(c, face):
	e = NOIR
	if face in ("EXT", "INT"):
		for y in range(4, 90, 6):
			c.rect(31, y, 33, y + 3, hexa("3A3A3A"))
	c.trait([(0, 99), (64, 99)], e, 1.6)
	c.trait([(0, 92), (64, 92)], e, 1.6)
	if face == "Front":
		for i in range(4):
			y = 101 + i * 5
			c.trait([(24, y), (40, y + 4)], hexa("5A5A5A"), 1.4)
			c.trait([(40, y), (24, y + 4)], hexa("5A5A5A"), 1.4)
	if face == "EXT":
		c.rect(0, 104, 64, 109, hexa("222222"))
		c.rect(26, 102, 38, 111, OR_F)
		c.rect(28, 103, 36, 110, OR)
		c.rect(28, 103, 36, 105, hexa("FFF2A8"))
		c.rect(30, 105, 34, 108, hexa("222222"))
	c.rect(0, 125, 64, 128, hexa("2A1E14"))


def pied_dessous(c):
	c.rect(0, 0, 64, 64, hexa("2A1E14"))
	c.trait([(6, 34), (58, 34)], hexa("1A120C"), 1.6)


# ---------------------------------------------------------------- assemblage


def peindre_shirt():
	img = Image.new("RGBA", (TAILLE[0] * S, TAILLE[1] * S), (0, 0, 0, 0))
	t = ZONES["torse"]["faces"]
	cs = {f: Calque(img, t[f]["rect"]) for f in t}
	torse_avant(cs["Front"])
	torse_avant_traits(cs["Front"])
	# cicatrice : epaule gauche (droite de l'image) -> hanche droite (sous le haramaki)
	cicatrice(cs["Front"], (106, 8), (30, 84))
	torse_dos(cs["Back"])
	torse_dos_traits(cs["Back"])
	torse_cote(cs["Right"], avant_a_droite=True)
	torse_cote_traits(cs["Right"], True)
	torse_cote(cs["Left"], avant_a_droite=False)
	torse_cote_traits(cs["Left"], False)
	torse_haut(cs["Top"])
	cs["Bottom"].rect(0, 0, 128, 64, HARA_F)
	for f, w in (("Front", 128), ("Back", 128), ("Right", 64), ("Left", 64)):
		haramaki(cs[f], HARA_HAUT, 128, w)
	for groupe, faces in (("bras_droit", {"Left": "INT", "Right": "EXT"}), ("bras_gauche", {"Left": "EXT", "Right": "INT"})):
		for f in ("Front", "Back", "Left", "Right"):
			c = Calque(img, rect(groupe, f))
			bras(c, faces.get(f, f))
			bras_traits(c, faces.get(f, f))
		Calque(img, rect(groupe, "Top")).rect(0, 0, 64, 64, PEAU)
		Calque(img, rect(groupe, "Bottom")).rect(0, 0, 64, 64, PEAU_OMBRE)
	finir(img, ("torse", "bras_droit", "bras_gauche"), "shirt_zoro.png")


def peindre_pants():
	img = Image.new("RGBA", (TAILLE[0] * S, TAILLE[1] * S), (0, 0, 0, 0))
	t = ZONES["torse"]["faces"]
	# torse : cache par le Shirt (haramaki) ; on peint le meme haramaki par securite
	for f in ("Front", "Back", "Right", "Left"):
		w = t[f]["rect"][2]
		c = Calque(img, t[f]["rect"])
		c.rect(0, 0, w, 128, PANT)
		haramaki(c, HARA_HAUT, 128, w)
	Calque(img, t["Top"]["rect"]).rect(0, 0, 128, 64, PANT)
	Calque(img, t["Bottom"]["rect"]).rect(0, 0, 128, 64, PANT)
	for groupe, faces in (("jambe_droite", {"Left": "INT", "Right": "EXT"}), ("jambe_gauche", {"Left": "EXT", "Right": "INT"})):
		for f in ("Front", "Back", "Left", "Right"):
			c = Calque(img, rect(groupe, f))
			jambe(c, faces.get(f, f))
			jambe_traits(c, faces.get(f, f))
		Calque(img, rect(groupe, "Top")).rect(0, 0, 64, 64, PANT)
		pied_dessous(Calque(img, rect(groupe, "Bottom")))
	finir(img, ("torse", "jambe_droite", "jambe_gauche"), "pants_zoro.png")


# ---------------------------------------------------------------- face


def peindre_face():
	"""512x512, fond transparent. Image a gauche = droite du perso (oeil ouvert)."""
	S = 2  # dessin en 1024 puis reduction (bords lisses)
	img = Image.new("RGBA", (512 * S, 512 * S), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)

	def P(pts):
		return [(x * S, y * S) for x, y in pts]

	def L(pts, c, w):
		d.line(P(pts), fill=c, width=w * S, joint="curve")
		r = w * S / 2
		for x, y in (pts[0], pts[-1]):
			d.ellipse([x * S - r, y * S - r, x * S + r, y * S + r], fill=c)

	def miroir(pts):
		return [(512 - x, y) for x, y in pts]

	# cel-shading : aplats nets (pas de flou), lumiere en haut a gauche de l'image
	ombre = PEAU_OMBRE
	# pommettes : ombre nette en triangle sous l'os, plus large du cote ombre (image droite)
	d.polygon(P([(104, 300), (150, 314), (158, 346), (138, 330), (112, 322)]), fill=ombre)
	d.polygon(P(miroir([(96, 296), (152, 312), (162, 356), (140, 338), (104, 326)])), fill=ombre)
	# petit reflet sur la pommette eclairee
	d.polygon(P([(120, 292), (146, 296), (140, 302), (122, 300)]), fill=hexa("F4D0AC"))
	# nez : coin d'ombre net sur le cote ombre
	d.polygon(P([(262, 282), (278, 318), (272, 330), (262, 328), (268, 316)]), fill=ombre)
	# sous la levre et menton
	d.polygon(P([(230, 392), (282, 392), (274, 402), (238, 402)]), fill=ombre)
	d.polygon(P([(214, 440), (256, 446), (298, 440), (284, 452), (228, 452)]), fill=ombre)

	# ombre projetee par le bandana : suit son bord reel (bord_bandana de accessoires_zoro.py),
	# deux tons en aplats, bord inferieur en dents de scie comme une ombre de meches
	def y_bord(x):
		z = 4.725 + 0.175 * math.cos(math.radians((x / 512 - 0.5) * 120))
		return (0.5 - (z - 3.192428 - 1.598) / 1.17) * 512

	for couleur, prof, dents in ((hexa("9A6644"), 32, 10), ((30, 18, 15, 255), 6, 6)):
		haut = [(x, y_bord(x) - 10) for x in range(0, 513, 16)]
		bas = []
		for i, x in enumerate(range(512, -1, -16)):
			bas.append((x, y_bord(x) + prof + (dents if i % 2 else 0) + 4 * math.sin(x / 37)))
		d.polygon(P(haut + bas), fill=couleur)

	# --- sourcils tres epais et fronces, en partie dans l'ombre
	sourcil = [(96, 228), (150, 212), (212, 220), (248, 240), (244, 249), (208, 231), (150, 223), (100, 235)]
	d.polygon(P(sourcil), fill=NOIR)
	d.polygon(P(miroir(sourcil)), fill=NOIR)

	# --- oeil droit du perso (image gauche) : ouvert, grand et allonge
	cx, cy = 168, 262
	blanc = [(108, 268), (124, 250), (162, 241), (204, 245), (226, 260), (210, 277), (170, 284), (128, 280)]
	d.polygon(P(blanc), fill=(246, 242, 236, 255))
	# iris gris-noir en degrade, coupe par les paupieres
	iris = Image.new("RGBA", img.size, (0, 0, 0, 0))
	di = ImageDraw.Draw(iris)
	for i in range(16, 0, -1):
		f = i / 16
		col = (int(28 + 80 * (1 - f)), int(30 + 80 * (1 - f)), int(34 + 80 * (1 - f)), 255)
		di.ellipse(P([(cx - 20 * f - 1, cy - 22 * f + 2), (cx + 20 * f + 1, cy + 22 * f + 2)]), fill=col)
	di.ellipse(P([(cx - 8, cy - 6), (cx + 8, cy + 10)]), fill=(8, 8, 10, 255))
	m = Image.new("L", img.size, 0)
	ImageDraw.Draw(m).polygon(P(blanc), fill=255)
	img.paste(iris, (0, 0), Image.composite(iris, Image.new("RGBA", img.size), m).getchannel("A"))
	d2 = ImageDraw.Draw(img, "RGBA")
	# ombre de la paupiere sur l'oeil
	d2.polygon(P([(112, 266), (126, 250), (162, 242), (204, 246), (224, 259), (204, 254), (162, 252), (128, 260)]), fill=(40, 26, 20, 140))
	# reflets
	d.ellipse(P([(cx + 4, cy - 14), (cx + 14, cy - 4)]), fill=(255, 255, 255, 255))
	d.ellipse(P([(cx - 12, cy + 8), (cx - 6, cy + 14)]), fill=(255, 255, 255, 210))
	# contour : paupiere superieure tres epaisse avec pointe exterieure, inferieure fine
	L([(98, 274), (120, 248), (162, 237), (208, 242), (232, 262)], NOIR, 9)
	L([(98, 274), (90, 282)], NOIR, 5)
	L([(128, 281), (170, 288), (210, 279)], (60, 40, 30, 255), 3)

	# --- oeil gauche du perso (image droite) : ferme (arc vers le bas), barre d'une cicatrice
	L([(282, 260), (306, 272), (346, 277), (384, 270), (412, 252)], NOIR, 8)
	L([(412, 252), (422, 248)], NOIR, 4)
	L([(300, 286), (346, 291), (386, 284)], (90, 60, 45, 255), 3)
	# cicatrice verticale du sourcil a la joue, coupe le sourcil et la paupiere
	L([(348, 204), (345, 274), (349, 344)], hexa("4A1612"), 9)
	L([(348, 206), (345, 274), (349, 342)], CICATRICE, 5)
	for y in (232, 262, 300, 326):  # bourrelets de la cicatrice
		L([(341, y), (355, y + 2)], hexa("4A1612"), 2)

	# nez manga : arete suggeree par l'ombre, petit trait anguleux au bout
	L([(268, 300), (274, 324)], PEAU_TRAIT, 2)
	L([(250, 330), (262, 334), (274, 328)], PEAU_TRAIT, 3)
	# bouche large et severe, coins tombants
	L([(180, 388), (198, 376), (256, 372), (314, 376), (332, 388)], NOIR, 6)
	L([(230, 394), (282, 394)], PEAU_TRAIT, 2)
	# rides du front fronce entre les sourcils
	L([(248, 236), (252, 254)], PEAU_TRAIT, 2)
	L([(264, 236), (260, 254)], PEAU_TRAIT, 2)

	img = img.resize((512, 512), Image.LANCZOS)
	img.save(DOSSIER / "face_zoro.png")


if __name__ == "__main__":
	peindre_shirt()
	peindre_pants()
	peindre_face()
	print("shirt_zoro.png, pants_zoro.png, face_zoro.png")
