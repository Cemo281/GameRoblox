"""Texture des accessoires 3D de zoro (acc_zoro.png, 1024x1024) et ses zones (acc_zones.json).

Chaque zone est peinte pour une projection precise (voir accessoires_zoro.py) :
u = autour / le long de la piece, v = de haut en bas (0 = haut de la zone).
Usage : uv run --with pillow assets/persos/zoro/texture_acc_zoro.py
"""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).parent
T = 1024


def hexa(h, a=255):
	h = h.lstrip("#")
	return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def melange(a, b, f):
	return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3)) + (255,)


ZONES = {
	"bandana": (0, 0, 256, 256),
	"cheveux": (256, 0, 512, 256),
	"or": (512, 0, 640, 128),
	"haramaki": (640, 0, 1024, 128),
	"lame": (512, 128, 1024, 256),
	"manteau": (0, 256, 1024, 576),
	"manteau_int": (0, 576, 512, 704),
	"echarpe": (512, 576, 1024, 704),
	"fourreau_blanc": (0, 704, 1024, 768),
	"fourreau_rouge": (0, 768, 1024, 832),
	"fourreau_noir": (0, 832, 1024, 896),
	"poignee_noir": (0, 896, 341, 1024),
	"poignee_rouge": (341, 896, 682, 1024),
	"poignee_blanc": (682, 896, 1024, 1024),
}

# nombre de plis du manteau sur le tour (doit egaler PLIS dans accessoires_zoro.py)
PLIS_MANTEAU = 9


def degrade_vertical(d, z, haut, bas):
	x0, y0, x1, y1 = z
	for y in range(y0, y1):
		d.line([(x0, y), (x1 - 1, y)], fill=melange(haut, bas, (y - y0) / max(1, y1 - y0 - 1)))


def peindre():
	img = Image.new("RGBA", (T, T), (0, 0, 0, 255))
	d = ImageDraw.Draw(img)

	# bandana, style anime : u = tour (0 et 1 = arriere, noeud ; 0,5 = front), v = sommet -> bord (0,85), ourlet (0,9 a 1)
	x0, y0, x1, y1 = ZONES["bandana"]
	w, h = x1 - x0, y1 - y0
	z = Image.new("RGBA", (w, h))
	dz = ImageDraw.Draw(z)
	degrade_vertical(dz, (0, 0, w, h), hexa("2C2C2C"), hexa("141414"))
	# plis qui partent du noeud (arriere) vers les cotes : creux noir et arete claire
	for cote in (0, 1):
		for k in range(5):
			ya = int(h * (0.62 + 0.05 * k))
			xa = 0 if cote == 0 else w
			xb = w * (0.16 + 0.05 * k) if cote == 0 else w * (0.84 - 0.05 * k)
			yb = int(h * (0.25 + 0.08 * k))
			xm = (xa + xb) / 2
			dz.line([(xa, ya), (xm, (ya + yb) / 2 + 8), (xb, yb)], fill=hexa("070707"), width=5)
			dz.line([(xa, ya - 5), (xm, (ya + yb) / 2 + 3), (xb, yb - 5)], fill=hexa("3E3E3E"), width=2)
	# plis de tension au-dessus du front
	for k in range(3):
		yy = int(h * (0.66 + 0.05 * k))
		dz.arc([w * 0.36, yy - 10, w * 0.64, yy + 10], 200, 340, fill=hexa("080808"), width=3)
		dz.arc([w * 0.37, yy - 13, w * 0.63, yy + 7], 205, 335, fill=hexa("3A3A3A"), width=1)
	# reflets nets (cel-shading) sur le dessus et l'avant
	dz.polygon([(w * 0.30, h * 0.30), (w * 0.42, h * 0.20), (w * 0.62, h * 0.20), (w * 0.72, h * 0.30), (w * 0.60, h * 0.27), (w * 0.42, h * 0.27)], fill=hexa("5A5A5A"))
	dz.polygon([(w * 0.45, h * 0.36), (w * 0.55, h * 0.34), (w * 0.58, h * 0.37), (w * 0.47, h * 0.39)], fill=hexa("4A4A4A"))
	for xc in (0.18, 0.82):
		dz.polygon([(w * (xc - 0.05), h * 0.32), (w * (xc + 0.05), h * 0.26), (w * (xc + 0.06), h * 0.30), (w * (xc - 0.04), h * 0.36)], fill=hexa("444444"))
	# ourlet : bande plus sombre, liseres et surpiqure
	dz.rectangle([0, int(h * 0.86), w, h], fill=hexa("0E0E0E"))
	dz.line([(0, int(h * 0.86)), (w, int(h * 0.86))], fill=hexa("050505"), width=3)
	dz.line([(0, int(h * 0.88)), (w, int(h * 0.88))], fill=hexa("3C3C3C"), width=2)
	for x in range(0, w, 10):
		dz.line([(x, int(h * 0.94)), (x + 5, int(h * 0.94))], fill=hexa("4A4A4A"), width=2)
	img.paste(z, (x0, y0))

	# cheveux : du vert fonce (base, v = 0) au vert clair (pointe, v = 1), meches
	x0, y0, x1, y1 = ZONES["cheveux"]
	# cel-shading, u = tour de la meche (4 faces : dessus, cote, dessous, cote), v = base (0) -> pointe (1)
	w, h = x1 - x0, y1 - y0
	# teintes de la reference cheveux (vert vif) : base, ombre, reflet, encre
	d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=hexa("5DB84A"))
	# base dans l'ombre du bandana (aplat sombre en dents de scie)
	d.polygon([(x0, y0)] + [(x0 + i * w / 16, y0 + h * (0.20 if i % 2 else 0.28)) for i in range(17)] + [(x1, y0)], fill=hexa("3A8A34"))
	# face interieure de la lame (3e quart du tour) dans l'ombre, flancs (2e et 4e quarts) en mi-ombre
	d.rectangle([x0 + w // 2, y0, x0 + 3 * w // 4, y1 - 1], fill=hexa("3A8A34"))
	for q in (1, 3):
		d.rectangle([x0 + q * w // 4, y0, x0 + (q + 1) * w // 4, y1 - 1], fill=hexa("4CA23F"))
	# face exterieure (1er quart) : reflets en longues stries effilees vers la pointe
	for xa, l in ((0.03, 0.80), (0.09, 0.62), (0.16, 0.72)):
		d.polygon([(x0 + w * xa, y0 + h * 0.30), (x0 + w * (xa + 0.035), y0 + h * 0.30), (x0 + w * (xa + 0.025), y0 + h * l), (x0 + w * (xa + 0.01), y0 + h * l)], fill=hexa("A6E38A"))
	# encre aux aretes de la lame et a la pointe
	for i in range(5):
		d.line([(x0 + i * w / 4, y0), (x0 + i * w / 4, y1 - 1)], fill=hexa("1E4A1A"), width=4)
	d.rectangle([x0, y1 - 12, x1 - 1, y1 - 1], fill=hexa("1E4A1A"))

	# or : degrade avec bord fonce
	x0, y0, x1, y1 = ZONES["or"]
	degrade_vertical(d, ZONES["or"], hexa("F7DE6A"), hexa("C29A1E"))
	d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=hexa("9C7A14"), width=6)

	# haramaki : cotes horizontales (v de haut en bas)
	x0, y0, x1, y1 = ZONES["haramaki"]
	# cel-shading : dessus de chaque cote eclaire, liseré clair, dessous dans l'ombre, encre entre les cotes
	d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=hexa("3E8B4A"))
	n = 7
	h = (y1 - y0) / n
	for i in range(n):
		ya = y0 + i * h
		d.rectangle([x0, ya + h * 0.55, x1 - 1, ya + h], fill=hexa("255A30"))
		d.rectangle([x0, ya + 2, x1 - 1, ya + 4], fill=hexa("6CBF74"))
		d.line([(x0, ya + h - 1), (x1 - 1, ya + h - 1)], fill=hexa("10301A"), width=2)

	# lame : dos (v = 0) acier fonce, centre clair, tranchant blanc, hamon ondule
	x0, y0, x1, y1 = ZONES["lame"]
	degrade_vertical(d, (x0, y0, x1, y0 + 64), hexa("6F7882"), hexa("C9D1DA"))
	degrade_vertical(d, (x0, y0 + 64, x1, y1), hexa("D8DEE6"), hexa("F7FAFF"))
	pts = [(x, y0 + 82 + 8 * math.sin((x - x0) / 14)) for x in range(x0, x1, 4)]
	d.line(pts, fill=hexa("FFFFFF"), width=3)

	# manteau : u = tour (0 et 1 = bords de l'ouverture), v = haut -> ourlet
	x0, y0, x1, y1 = ZONES["manteau"]
	# cel-shading : un pli par periode = creux en aplat sombre + arete eclairee nette, traits d'encre effiles
	d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=hexa("1F5A3A"))
	w = x1 - x0
	p = w / PLIS_MANTEAU
	for i in range(PLIS_MANTEAU):
		xc = x0 + (i + 0.5) * p
		# creux du pli (s'elargit vers le bas)
		d.polygon([(xc - 2, y0 + 30), (xc + 4, y0 + 30), (xc + 22, y1), (xc - 16, y1)], fill=hexa("123A24"))
		# arete eclairee (entre deux creux)
		xa = xc + p / 2
		d.polygon([(xa - 3, y0 + 50), (xa + 2, y0 + 50), (xa + 12, y1 - 24), (xa - 2, y1 - 24)], fill=hexa("2E7D52"))
		d.polygon([(xa - 1, y0 + 90), (xa + 1, y0 + 90), (xa + 6, y1 - 60), (xa + 2, y1 - 60)], fill=hexa("4FA36E"))
		# encre au fond du creux
		d.line([(xc + 1, y0 + 40), (xc + 3, y0 + 140), (xc + 5, y1 - 30)], fill=hexa("06180D"), width=3)
	# revers le long de l'ouverture (u proches de 0 et 1) : bande plus sombre, liseré clair, encre
	for xa, xb, xl, xr in ((x0, x0 + 46, x0 + 46, x0 + 40), (x1 - 46, x1, x1 - 47, x1 - 42)):
		d.rectangle([xa, y0, xb - 1, y1 - 1], fill=hexa("164A2E"))
		d.rectangle([xr, y0, xr + 3, y1 - 1], fill=hexa("3E9466"))
		d.line([(xl, y0), (xl, y1 - 1)], fill=hexa("06180D"), width=4)
		for y in range(y0 + 6, y1, 14):
			d.line([(xa + 20, y), (xa + 20, y + 6)], fill=hexa("2F7D52"), width=2)
	# haut (sous l'echarpe) et ourlet avec encre et surpiqure
	d.rectangle([x0, y0, x1 - 1, y0 + 26], fill=hexa("123A24"))
	d.rectangle([x0, y1 - 22, x1 - 1, y1 - 1], fill=hexa("123A24"))
	d.line([(x0, y1 - 22), (x1 - 1, y1 - 22)], fill=hexa("06180D"), width=3)
	d.line([(x0, y1 - 3), (x1 - 1, y1 - 3)], fill=hexa("06180D"), width=4)
	for x in range(x0 + 4, x1, 16):
		d.line([(x, y1 - 30), (x + 8, y1 - 30)], fill=hexa("3E9466"), width=2)

	# interieur du manteau
	x0, y0, x1, y1 = ZONES["manteau_int"]
	degrade_vertical(d, ZONES["manteau_int"], hexa("0E2E1C"), hexa("153F27"))

	# echarpe : bordeaux, plis en long (u) et ombres
	x0, y0, x1, y1 = ZONES["echarpe"]
	# cel-shading : plis en aplats sombres nets, reflets francs, encre au creux
	d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=hexa("8E1F2E"))
	for i in range(8):
		x = x0 + 8 + i * 64
		d.polygon([(x, y0), (x + 22, y0), (x + 44, y1), (x + 14, y1)], fill=hexa("5E1220"))
		d.polygon([(x + 28, y0), (x + 36, y0), (x + 58, y1), (x + 50, y1)], fill=hexa("C24A5C"))
		d.line([(x + 6, y0), (x + 24, y1)], fill=hexa("2A0810"), width=3)
	d.line([(x0, y0 + 2), (x1 - 1, y0 + 2)], fill=hexa("2A0810"), width=4)
	d.line([(x0, y1 - 3), (x1 - 1, y1 - 3)], fill=hexa("2A0810"), width=4)

	# fourreaux : u = de l'embouchure (0) a la pointe (1), v = tour
	for nom, base, reflet in (("fourreau_blanc", "EDEDE6", "FFFFFF"), ("fourreau_rouge", "7A1E26", "A8404A"), ("fourreau_noir", "161616", "3A3A3A")):
		x0, y0, x1, y1 = ZONES[nom]
		d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=hexa(base))
		d.rectangle([x0, y0 + 14, x1 - 1, y0 + 20], fill=hexa(reflet))
		d.rectangle([x0, y0, x0 + 30, y1 - 1], fill=hexa("C9A42E"))  # embouchure doree
		d.rectangle([x1 - 26, y0, x1 - 1, y1 - 1], fill=hexa("C9A42E"))  # bout dore
		for x in (x0 + 140, x0 + 190):  # liens (sageo) noues
			d.rectangle([x, y0, x + 10, y1 - 1], fill=hexa("2A2A6A") if nom != "fourreau_noir" else hexa("4A3A1A"))

	# poignees tressees : u = le long (0 = garde, 1 = pommeau), v = tour, motif en losanges
	for nom, tresse, peau in (("poignee_noir", "151515", "E8E0CC"), ("poignee_rouge", "7A1E26", "E8E0CC"), ("poignee_blanc", "F0F0EA", "3A3A44")):
		x0, y0, x1, y1 = ZONES[nom]
		w, h = x1 - x0, y1 - y0
		z = Image.new("RGBA", (w, h), hexa(peau))
		dz = ImageDraw.Draw(z)
		for x in range(-h, w + h, 32):
			dz.line([(x, 0), (x + h, h)], fill=hexa(tresse), width=12)
			dz.line([(x + h, 0), (x, h)], fill=hexa(tresse), width=12)
		dz.rectangle([0, 0, 12, h - 1], fill=hexa("C9A42E"))  # fuchi
		dz.rectangle([w - 16, 0, w - 1, h - 1], fill=hexa("C9A42E"))  # kashira
		img.paste(z, (x0, y0))

	img = img.filter(ImageFilter.SMOOTH)
	img.save(DOSSIER / "acc_zoro.png")
	# zones normalisees pour les UV de Blender : (u0, v0, u1, v1), v vers le bas
	(DOSSIER / "acc_zones.json").write_text(json.dumps({k: [v[0] / T, v[1] / T, v[2] / T, v[3] / T] for k, v in ZONES.items()}, indent="\t"), encoding="utf-8")


if __name__ == "__main__":
	peindre()
	print("acc_zoro.png, acc_zones.json")
