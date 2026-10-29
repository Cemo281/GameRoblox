"""Peint Texture_zoro.png (1024 x 1024) a partir des zones de uv_zoro.json.

Usage : uv run --with pillow assets/blender/zoro/texture_zoro.py [--uv chemin_uvpolys.json]
Dessine en 2048 px puis reduit en 1024 (anticrenelage). --uv superpose les polygones UV
dans Texture_zoro_uv.png pour controler le placage.
"""

import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ICI = Path(__file__).parent
UV = json.loads((ICI / "uv_zoro.json").read_text(encoding="utf-8"))
ZONES = UV["zones"]
RANGEES = UV["rangees"]
S = 2  # sur-echantillonnage
T = UV["taille"] * S


def hx(c):
	c = c.lstrip("#")
	return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))


def mix(a, b, f):
	return tuple(int(round(a[i] + (b[i] - a[i]) * f)) for i in range(3))


def plus(c, f):
	"""f > 0 eclaircit, f < 0 assombrit"""
	return mix(c, (255, 255, 255), f) if f > 0 else mix(c, (0, 0, 0), -f)


PEAU = hx("#E2B48C")
PEAU_OMBRE = hx("#B98560")
PEAU_TRAIT = hx("#7E5236")
CHEV_C = hx("#4FA34A")
CHEV_F = hx("#2F6B2A")
BANDANA = hx("#151515")
HARA_C = hx("#3E8B4A")
HARA_F = hx("#255A30")
MANT_C = hx("#1F5A3A")
MANT_F = hx("#123A24")
ECHARPE = hx("#8E1F2E")
PANTALON = hx("#1A1A1A")
BOTTES = hx("#0F0F0F")
OR = hx("#E8C33A")
CICATRICE = hx("#7A2A22")
NOIR = (12, 12, 12)
BLANC = (245, 245, 240)

img = Image.new("RGB", (T, T), (255, 0, 255))
d = ImageDraw.Draw(img)


def rect(nom):
	x0, y0, x1, y1 = ZONES[nom]
	return (x0 * S, y0 * S, x1 * S, y1 * S)


def sous(r, y0, y1):
	"""sous-rectangle d'une colonne entre deux rangees (pixels 1024)"""
	return (r[0], y0 * S, r[2], y1 * S)


def P(r, s, t):
	"""point (s, t) dans [0, 1] d'un rectangle, t vers le haut"""
	return (r[0] + s * (r[2] - r[0]), r[3] - t * (r[3] - r[1]))


def W(r):
	return r[2] - r[0]


def H(r):
	return r[3] - r[1]


def degrade_v(r, haut, bas, marge=2):
	x0, y0, x1, y1 = r
	h = max(1, y1 - y0)
	for y in range(int(y0) - marge, int(y1) + marge):
		f = min(max((y - y0) / h, 0), 1)
		d.line([(x0 - marge, y), (x1 + marge, y)], fill=mix(haut, bas, f))


def degrade_h(r, gauche, droite, marge=2):
	x0, y0, x1, y1 = r
	w = max(1, x1 - x0)
	for x in range(int(x0) - marge, int(x1) + marge):
		f = min(max((x - x0) / w, 0), 1)
		d.line([(x, y0 - marge), (x, y1 + marge)], fill=mix(gauche, droite, f))


def calque_flou(r, dessin, flou, opacite=1.0):
	"""dessine sur un calque RGBA de la taille du rectangle, floute, puis colle"""
	x0, y0, x1, y1 = (int(v) for v in r)
	cal = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
	dc = ImageDraw.Draw(cal)
	dessin(dc, lambda s, t: (s * (x1 - x0), (1 - t) * (y1 - y0)), x1 - x0, y1 - y0)
	if flou:
		cal = cal.filter(ImageFilter.GaussianBlur(flou * S))
	if opacite < 1:
		a = cal.getchannel("A").point(lambda v: int(v * opacite))
		cal.putalpha(a)
	img.paste(cal, (x0, y0), cal)


def bords_ombre(r, couleur, largeur=10, opacite=0.55, cotes="gdhb"):
	"""ombre douce le long des bords (volume des boites)"""

	def f(dc, p, w, h):
		lw = largeur * S
		c = couleur + (255,)
		if "g" in cotes:
			dc.rectangle([0, 0, lw, h], fill=c)
		if "d" in cotes:
			dc.rectangle([w - lw, 0, w, h], fill=c)
		if "h" in cotes:
			dc.rectangle([0, 0, w, lw * 0.6], fill=c)
		if "b" in cotes:
			dc.rectangle([0, h - lw * 0.6, w, h], fill=c)

	calque_flou(r, f, largeur * 0.8, opacite)


def contour(r, couleur, ep=2):
	x0, y0, x1, y1 = r
	d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=couleur, width=ep * S)


def courbe(pts, couleur, ep):
	d.line(pts, fill=couleur, width=int(ep * S), joint="curve")
	for x, y in (pts[0], pts[-1]):
		e = ep * S / 2
		d.ellipse([x - e, y - e, x + e, y + e], fill=couleur)


def bezier(a, b, c, n=16):
	return [
		(
			(1 - u) ** 2 * a[0] + 2 * (1 - u) * u * b[0] + u * u * c[0],
			(1 - u) ** 2 * a[1] + 2 * (1 - u) * u * b[1] + u * u * c[1],
		)
		for u in (i / n for i in range(n + 1))
	]


def pointilles(a, b, couleur, ep=1.5, pas=7, trait=4):
	L = math.dist(a, b)
	n = int(L / (pas * S))
	for i in range(n):
		u0 = i * pas * S / L
		u1 = min(1, u0 + trait * S / L)
		d.line(
			[
				(a[0] + (b[0] - a[0]) * u0, a[1] + (b[1] - a[1]) * u0),
				(a[0] + (b[0] - a[0]) * u1, a[1] + (b[1] - a[1]) * u1),
			],
			fill=couleur,
			width=int(ep * S),
		)


# ---------------------------------------------------------------- unis
for nom, c in (("Peau_Unie", plus(PEAU, -0.06)), ("Noir_Uni", PANTALON)):
	d.rectangle(rect(nom), fill=c)

r = rect("Or")
degrade_v(r, plus(OR, 0.35), plus(OR, -0.3))
d.line([P(r, 0, 0.7), P(r, 1, 0.7)], fill=plus(OR, 0.6), width=2 * S)


# ---------------------------------------------------------------- visage
def visage():
	r = rect("Visage")
	degrade_v(r, plus(PEAU, -0.04), PEAU)

	# volume : cotes de la tete plus sombres (cylindre), menton
	def vol(dc, p, w, h):
		dc.rectangle([0, 0, w * 0.13, h], fill=PEAU_OMBRE + (255,))
		dc.rectangle([w * 0.87, 0, w, h], fill=PEAU_OMBRE + (255,))
		dc.rectangle([0, h * 0.94, w, h], fill=PEAU_OMBRE + (200,))
		# ombre du bandana sur le front
		dc.polygon([p(0, 0.78), p(0.25, 0.82), p(0.5, 0.92), p(0.75, 0.82), p(1, 0.78), p(1, 1), p(0, 1)], fill=PEAU_OMBRE + (255,))

	calque_flou(r, vol, 9, 0.7)

	# ombres sous les pommettes et de la machoire
	def joues(dc, p, w, h):
		for sx in (0.33, 0.67):
			x, y = p(sx, 0.38)
			dc.ellipse([x - 18 * S, y - 7 * S, x + 18 * S, y + 9 * S], fill=PEAU_OMBRE + (255,))
		x, y = p(0.5, 0.06)
		dc.ellipse([x - 40 * S, y - 8 * S, x + 40 * S, y + 10 * S], fill=PEAU_OMBRE + (255,))

	calque_flou(r, joues, 7, 0.3)

	def pt(x, y):  # coordonnees en pixels du rectangle visage (256 x 256, y vers le bas), traits agrandis de 25 %
		k = 1.25
		return (r[0] + (128 + (x - 128) * k) * S, r[1] + (110 + (y - 100) * k) * S)

	# sourcils epais tres fronces (descendent vers le nez)
	for sens in (-1, 1):
		cx = 128 + sens * 32
		ext = (cx + sens * 25, 67)
		inte = (cx - sens * 22, 80)
		poly = [pt(*ext), pt(cx + sens * 2, 66), pt(*inte), pt(inte[0] + sens * 1, inte[1] + 7), pt(cx, 77), pt(ext[0] - sens * 3, ext[1] + 7)]
		d.polygon(poly, fill=NOIR)
	# plis du front entre les sourcils
	for x in (123, 133):
		courbe([pt(x, 74), pt(x + (1 if x > 128 else -1), 86)], plus(PEAU_TRAIT, 0.1), 1.6)

	# oeil droit (cote gauche de l'image) ouvert, dur
	cx, cy = 96, 95
	amande = [pt(cx - 18, cy + 1), pt(cx - 8, cy - 6), pt(cx + 8, cy - 4), pt(cx + 17, cy + 3), pt(cx + 6, cy + 7), pt(cx - 8, cy + 7)]
	d.polygon(amande, fill=(250, 248, 240))
	# iris gris-noir en degrade, coupe par la paupiere
	ix, iy, ir = cx + 3, cy + 2, 7.5 * 1.25
	icx, icy = pt(ix, iy)
	for k in range(int(ir * S), 0, -1):
		f = k / (ir * S)
		c = mix((25, 25, 28), (95, 98, 105), f * 0.9)
		d.ellipse([icx - k, icy - k, icx + k, icy + k], fill=c)
	d.ellipse([*pt(ix - 3.2, iy - 3.2), *pt(ix + 3.2, iy + 3.2)], fill=(8, 8, 8))
	d.ellipse([*pt(ix + 1, iy - 4.5), *pt(ix + 4, iy - 1.5)], fill=(255, 255, 255))
	# peau qui recouvre le haut de l'iris (paupiere lourde) + ombre de paupiere
	d.polygon([pt(cx - 20, cy - 10), pt(cx + 20, cy - 10), pt(cx + 17, cy + 2), pt(cx + 8, cy - 3), pt(cx - 8, cy - 5), pt(cx - 19, cy + 1)], fill=plus(PEAU_OMBRE, 0.15))
	# trait de paupiere superieure epais
	courbe([pt(cx - 19, cy + 1), pt(cx - 8, cy - 5), pt(cx + 8, cy - 3), pt(cx + 18, cy + 3)], NOIR, 3.4)
	courbe([pt(cx - 6, cy + 8), pt(cx + 7, cy + 8)], PEAU_TRAIT, 1.4)

	# oeil gauche ferme + cicatrice verticale
	cx2 = 160
	courbe([pt(cx2 - 17, cy + 2), pt(cx2 - 6, cy + 5), pt(cx2 + 6, cy + 4), pt(cx2 + 17, cy)], NOIR, 3)
	d.polygon([pt(cx2 - 18, cy - 8), pt(cx2 + 18, cy - 10), pt(cx2 + 17, cy), pt(cx2 + 6, cy + 4), pt(cx2 - 6, cy + 5), pt(cx2 - 17, cy + 2)], fill=plus(PEAU_OMBRE, 0.2))
	courbe([pt(cx2 - 17, cy + 2), pt(cx2 - 6, cy + 5), pt(cx2 + 6, cy + 4), pt(cx2 + 17, cy)], NOIR, 3)
	cic = [pt(cx2 + 1, 58), pt(cx2 + 2, 80), pt(cx2, 100), pt(cx2 - 2, 124)]
	courbe(cic, plus(CICATRICE, 0.35), 6)
	courbe(cic, CICATRICE, 3.6)
	courbe([pt(cx2 + 1.2, 60), pt(cx2 + 2.2, 80)], plus(CICATRICE, -0.3), 1.2)

	# nez
	courbe([pt(130, 104), pt(132, 122), pt(126, 127)], PEAU_TRAIT, 1.8)
	courbe([pt(121, 126), pt(126, 128)], plus(PEAU_TRAIT, 0.15), 1.4)

	# bouche fermee en trait severe (coins vers le bas)
	courbe([pt(110, 158), pt(116, 155), pt(128, 154), pt(140, 155), pt(147, 159)], (60, 30, 22), 3)
	courbe([pt(120, 163), pt(136, 163)], plus(PEAU_TRAIT, 0.3), 1.4)


visage()


# ---------------------------------------------------------------- torse
def torse_avant():
	r = rect("UT_Avant")
	degrade_v(r, plus(PEAU, 0.04), plus(PEAU, -0.05))
	bords_ombre(r, PEAU_OMBRE, 14, 0.6)
	w, h = W(r) / S, H(r) / S

	def pt(x, y):
		return (r[0] + x * S, r[1] + y * S)

	# ombres douces des muscles
	def ombres(dc, p, ww, hh):
		c = PEAU_OMBRE + (255,)
		# sous les pectoraux
		for sens in (-1, 1):
			cx = w / 2 + sens * 52
			dc.ellipse([(cx - 50) * S, 72 * S, (cx + 50) * S, 92 * S], fill=c)
		# sillon central, abdominaux
		dc.rectangle([(w / 2 - 3) * S, 30 * S, (w / 2 + 3) * S, 168 * S], fill=c)
		for y in (112, 136):
			dc.rectangle([(w / 2 - 34) * S, (y - 3) * S, (w / 2 + 34) * S, (y + 4) * S], fill=c)
		# obliques
		for sens in (-1, 1):
			x = w / 2 + sens * 45
			dc.rectangle([(x - 5) * S, 95 * S, (x + 5) * S, 165 * S], fill=c)

	calque_flou(r, ombres, 5, 0.65)

	# reflets sur les pectoraux et abdos
	def reflets(dc, p, ww, hh):
		c = (255, 225, 195, 255)
		for sens in (-1, 1):
			cx = w / 2 + sens * 50
			dc.ellipse([(cx - 28) * S, 42 * S, (cx + 24) * S, 64 * S], fill=c)
			for y in (100, 124, 148):
				dc.ellipse([(w / 2 + sens * 17 - 10) * S, (y - 6) * S, (w / 2 + sens * 17 + 10) * S, (y + 5) * S], fill=c)

	calque_flou(r, reflets, 7, 0.35)
	trait = PEAU_TRAIT
	# clavicules
	for sens in (-1, 1):
		courbe(bezier(pt(w / 2 + sens * 12, 18), pt(w / 2 + sens * 40, 12), pt(w / 2 + sens * 80, 20)), plus(trait, 0.25), 1.6)
	# contours des pectoraux
	for sens in (-1, 1):
		courbe(bezier(pt(w / 2 + sens * 3, 50), pt(w / 2 + sens * 40, 96), pt(w / 2 + sens * 96, 62)), trait, 2.6)
	courbe([pt(w / 2, 28), pt(w / 2, 168)], trait, 1.8)
	# abdominaux
	for y in (110, 134):
		for sens in (-1, 1):
			courbe(bezier(pt(w / 2 + sens * 3, y), pt(w / 2 + sens * 18, y + 3), pt(w / 2 + sens * 32, y - 1)), trait, 2)
	for sens in (-1, 1):
		courbe(bezier(pt(w / 2 + sens * 36, 92), pt(w / 2 + sens * 42, 130), pt(w / 2 + sens * 34, 168)), trait, 2)
		# dentele (cotes)
		for k in range(3):
			y = 96 + k * 13
			courbe([pt(w / 2 + sens * 62, y), pt(w / 2 + sens * 50, y + 6)], plus(trait, 0.2), 1.5)
	# grande cicatrice : epaule gauche (droite de l'image) -> hanche droite
	a, b = pt(w - 14, 16), pt(26, 166)
	courbe([a, b], plus(CICATRICE, 0.4), 9)
	courbe([a, b], CICATRICE, 5.5)
	courbe([(a[0] - S, a[1] - 2 * S), (b[0] - S, b[1] - 2 * S)], plus(CICATRICE, -0.35), 1.2)
	L = math.dist(a, b)
	ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
	for k in range(1, int(L / (13 * S))):
		cx, cy = a[0] + ux * k * 13 * S, a[1] + uy * k * 13 * S
		e = 5.5 * S
		for sx, sy in ((1, 1), (1, -1)):
			# croix tournee selon la cicatrice
			vx, vy = (ux * sx - uy * sy) * 0.7, (uy * sx + ux * sy) * 0.7
			d.line([(cx - vx * e, cy - vy * e), (cx + vx * e, cy + vy * e)], fill=NOIR, width=int(1.8 * S))
	haramaki(r, "avant")


def haramaki(r, face):
	"""bande verte cotelee en bas du torse (z 2,62 -> 2,96 sur 2,592 -> 4,29)"""
	t0, t1 = (2.62 - 2.592) / 1.698, (2.97 - 2.592) / 1.698
	y_haut, y_bas = P(r, 0, t1)[1], r[3] + 2 * S
	degrade_v((r[0], y_haut, r[2], y_bas), HARA_C, plus(HARA_C, -0.1), marge=0)
	n = 10
	for k in range(n):
		y = y_haut + (y_bas - y_haut) * (k + 0.5) / n
		d.line([(r[0] - 2, y), (r[2] + 2, y)], fill=HARA_F, width=int(2.2 * S))
		d.line([(r[0] - 2, y - 2 * S), (r[2] + 2, y - 2 * S)], fill=plus(HARA_C, 0.18), width=S)
	d.line([(r[0] - 2, y_haut), (r[2] + 2, y_haut)], fill=plus(HARA_F, -0.4), width=3 * S)
	# ombre portee sur la peau au-dessus
	calque_flou((r[0], y_haut - 10 * S, r[2], y_haut), lambda dc, p, w, h: dc.rectangle([0, h * 0.5, w, h], fill=PEAU_OMBRE + (255,)), 3, 0.6)


def torse_dos():
	r = rect("UT_Dos")
	degrade_v(r, plus(PEAU, 0.02), plus(PEAU, -0.06))
	bords_ombre(r, PEAU_OMBRE, 14, 0.6)
	w = W(r) / S

	def pt(x, y):
		return (r[0] + x * S, r[1] + y * S)

	def ombres(dc, p, ww, hh):
		c = PEAU_OMBRE + (255,)
		dc.rectangle([(w / 2 - 4) * S, 10 * S, (w / 2 + 4) * S, 170 * S], fill=c)
		for sens in (-1, 1):
			dc.ellipse([(w / 2 + sens * 50 - 30) * S, 70 * S, (w / 2 + sens * 50 + 30) * S, 90 * S], fill=c)

	calque_flou(r, ombres, 6, 0.6)
	for sens in (-1, 1):
		# omoplates et dorsaux
		courbe(bezier(pt(w / 2 + sens * 22, 30), pt(w / 2 + sens * 30, 75), pt(w / 2 + sens * 70, 80)), PEAU_TRAIT, 2.2)
		courbe(bezier(pt(w / 2 + sens * 90, 60), pt(w / 2 + sens * 70, 130), pt(w / 2 + sens * 20, 165)), plus(PEAU_TRAIT, 0.15), 1.8)
		courbe(bezier(pt(w / 2 + sens * 10, 14), pt(w / 2 + sens * 50, 22), pt(w / 2 + sens * 100, 18)), plus(PEAU_TRAIT, 0.25), 1.6)
	courbe([pt(w / 2, 20), pt(w / 2, 168)], PEAU_TRAIT, 1.8)
	haramaki(r, "dos")


def torse_cote(nom):
	r = rect(nom)
	degrade_v(r, plus(PEAU, 0.0), plus(PEAU, -0.06))
	bords_ombre(r, PEAU_OMBRE, 14, 0.55)
	w = W(r) / S

	def pt(x, y):
		return (r[0] + x * S, r[1] + y * S)

	for k in range(3):
		y = 92 + k * 16
		courbe(bezier(pt(w * 0.3, y), pt(w * 0.5, y + 5), pt(w * 0.72, y + 1)), plus(PEAU_TRAIT, 0.25), 1.5)
	haramaki(r, "cote")


torse_avant()
torse_dos()
torse_cote("UT_Droite")
torse_cote("UT_Gauche")
r = rect("UT_Dessus")
degrade_v(r, PEAU, plus(PEAU, -0.05))
bords_ombre(r, PEAU_OMBRE, 8, 0.5)


# ---------------------------------------------------------------- bras (droit, le gauche est en miroir)
def bras():
	rg = RANGEES["Bras"]
	for col in ("Bras_Avant", "Bras_Ext", "Bras_Dos", "Bras_Int"):
		c = rect(col)
		for i in range(3):
			r = sous(c, rg[i], rg[i + 1])
			degrade_v(r, plus(PEAU, 0.03 if i == 0 else 0), plus(PEAU, -0.05))
			bords_ombre(r, PEAU_OMBRE, 10, 0.55, "gd" + ("h" if i == 0 else ""))
		haut = sous(c, rg[0], rg[1])
		bas = sous(c, rg[1], rg[2])
		main = sous(c, rg[2], rg[3])
		w = W(c) / S

		def pt(r, x, y):
			return (r[0] + x * S, r[1] + y * S)

		trait = PEAU_TRAIT
		if col in ("Bras_Avant", "Bras_Ext", "Bras_Dos"):
			# deltoide (rond de l'epaule)
			courbe(bezier(pt(haut, 6, 44), pt(haut, w / 2, 62), pt(haut, w - 6, 44)), trait, 2.2)
			calque_flou(haut, lambda dc, p, ww, hh: dc.rectangle([0, 46 * S, ww, 62 * S], fill=PEAU_OMBRE + (255,)), 4, 0.5)
			calque_flou(haut, lambda dc, p, ww, hh: dc.ellipse([ww * 0.2, 10 * S, ww * 0.8, 36 * S], fill=(255, 228, 200, 255)), 6, 0.35)
		if col == "Bras_Avant":
			# biceps
			courbe(bezier(pt(haut, 18, 120), pt(haut, 10, 82), pt(haut, 40, 70)), trait, 2)
			courbe(bezier(pt(haut, w - 18, 120), pt(haut, w - 10, 82), pt(haut, w - 40, 70)), trait, 2)
			calque_flou(haut, lambda dc, p, ww, hh: dc.ellipse([ww * 0.28, 76 * S, ww * 0.72, 112 * S], fill=(255, 228, 200, 255)), 7, 0.35)
		if col == "Bras_Dos":
			courbe([pt(haut, w / 2, 66), pt(haut, w / 2 - 2, 120)], trait, 1.8)
		if col == "Bras_Ext":
			courbe(bezier(pt(haut, w * 0.5, 66), pt(haut, w * 0.6, 95), pt(haut, w * 0.45, 128)), plus(trait, 0.2), 1.6)
		# avant-bras : muscles et veine discrete
		courbe(bezier(pt(bas, w * 0.3, 30), pt(bas, w * 0.22, 70), pt(bas, w * 0.4, 118)), plus(trait, 0.15), 1.8)
		if col in ("Bras_Avant", "Bras_Int"):
			courbe(bezier(pt(bas, w * 0.65, 40), pt(bas, w * 0.6, 80), pt(bas, w * 0.7, 115)), plus(PEAU_OMBRE, 0.0), 1.4)
		# main (poing) : doigts
		for k in range(1, 4):
			x = w * k / 4
			courbe([pt(main, x, 3), pt(main, x, H(main) / S - 3)], trait, 1.6)
		courbe([pt(main, 2, 2), pt(main, w - 2, 2)], plus(trait, 0.2), 1.4)
	# dessus de l'epaule, dessous du poing
	r = rect("Bras_Dessus")
	degrade_v(r, PEAU, plus(PEAU, -0.06))
	bords_ombre(r, PEAU_OMBRE, 10, 0.5)
	r = rect("Main_Dessous")
	degrade_v(r, plus(PEAU, -0.02), plus(PEAU, -0.08))
	for k in range(1, 4):
		x = r[0] + W(r) * k / 4
		courbe([(x, r[1] + 6 * S), (x, r[3] - 6 * S)], PEAU_TRAIT, 1.6)
	bords_ombre(r, PEAU_OMBRE, 10, 0.5)


bras()


# ---------------------------------------------------------------- jambes (pantalon + bottes)
def jambes():
	rg = RANGEES["Jambe"]
	z0_bas, haut_bas = 0.2075, 1.3013  # LowerLeg : bas et hauteur
	t_botte = (0.86 - z0_bas) / haut_bas
	for col in ("Jambe_Avant", "Jambe_Ext", "Jambe_Dos", "Jambe_Int"):
		c = rect(col)
		cuisse = sous(c, rg[0], rg[1])
		tibia = sous(c, rg[1], rg[2])
		pied = sous(c, rg[2], rg[3])
		w = W(c) / S
		degrade_v(cuisse, plus(PANTALON, 0.08), PANTALON)
		degrade_v(tibia, plus(PANTALON, 0.04), PANTALON)
		bords_ombre(cuisse, (0, 0, 0), 9, 0.6, "gd")
		bords_ombre(tibia, (0, 0, 0), 9, 0.6, "gd")
		pli = plus(PANTALON, 0.22)

		def pt(r, x, y):
			return (r[0] + x * S, r[1] + y * S)

		# plis du pantalon (genou)
		for k, y in enumerate((96, 108, 120)):
			courbe(bezier(pt(cuisse, w * 0.15, y), pt(cuisse, w * 0.5, y + 6 - k * 2), pt(cuisse, w * 0.85, y - 3)), pli, 1.6)
			courbe(bezier(pt(cuisse, w * 0.15, y + 2.5), pt(cuisse, w * 0.5, y + 8.5 - k * 2), pt(cuisse, w * 0.85, y - 0.5)), (5, 5, 5), 1.2)
		courbe([pt(cuisse, w * 0.5, 8), pt(cuisse, w * 0.47, 80)], plus(PANTALON, 0.12), 1.2)
		for y in (8, 20):
			courbe(bezier(pt(tibia, w * 0.2, y), pt(tibia, w * 0.5, y + 5), pt(tibia, w * 0.8, y)), pli, 1.4)
		# botte
		yb = P(tibia, 0, t_botte)[1]
		degrade_v((tibia[0], yb, tibia[2], tibia[3]), plus(BOTTES, 0.1), BOTTES, marge=0)
		bords_ombre((tibia[0], yb, tibia[2], tibia[3]), (0, 0, 0), 8, 0.7, "gd")
		# revers de la botte
		d.rectangle([tibia[0] - 2, yb, tibia[2] + 2, yb + 12 * S], fill=plus(BOTTES, 0.12))
		d.line([(tibia[0] - 2, yb + 12 * S), (tibia[2] + 2, yb + 12 * S)], fill=(0, 0, 0), width=2 * S)
		d.line([(tibia[0] - 2, yb + 1.5 * S), (tibia[2] + 2, yb + 1.5 * S)], fill=plus(BOTTES, 0.3), width=S)
		if col == "Jambe_Avant":
			# lacets croises
			y = yb + 18 * S
			while y < tibia[3] - 8 * S:
				d.line([(tibia[0] + w * 0.32 * S, y), (tibia[0] + w * 0.68 * S, y + 7 * S)], fill=(90, 90, 92), width=int(1.6 * S))
				d.line([(tibia[0] + w * 0.68 * S, y), (tibia[0] + w * 0.32 * S, y + 7 * S)], fill=(90, 90, 92), width=int(1.6 * S))
				y += 10 * S
		if col == "Jambe_Ext":
			# petites boucles dorees
			for k in range(2):
				y = yb + (22 + k * 22) * S
				x = tibia[0] + w * 0.5 * S
				d.rectangle([x - 8 * S, y - 3 * S, x + 8 * S, y + 3 * S], fill=plus(BOTTES, 0.18))
				d.rectangle([x - 5 * S, y - 5 * S, x + 3 * S, y + 5 * S], outline=OR, width=int(2 * S))
		# pied : semelle
		degrade_v(pied, plus(BOTTES, 0.1), BOTTES)
		d.rectangle([pied[0] - 2, pied[3] - 7 * S, pied[2] + 2, pied[3] + 2], fill=(40, 34, 30))
		d.line([(pied[0] - 2, pied[3] - 7 * S), (pied[2] + 2, pied[3] - 7 * S)], fill=(0, 0, 0), width=S)
	for nom in ("Pied_Dessus", "Pied_Dessous"):
		d.rectangle(rect(nom), fill=BOTTES)


jambes()


# ---------------------------------------------------------------- bas du torse (pantalon, ceinture)
for nom in ("LT_Avant", "LT_Dos", "LT_Droite", "LT_Gauche"):
	r = rect(nom)
	degrade_v(r, plus(PANTALON, 0.1), PANTALON)
	d.line([(r[0] - 2, r[1] + 10 * S), (r[2] + 2, r[1] + 10 * S)], fill=(0, 0, 0), width=2 * S)


# ---------------------------------------------------------------- bandana, cheveux
def bandana():
	r = rect("Bandana")
	degrade_v(r, plus(BANDANA, 0.1), BANDANA)

	# plis souples (reflets courbes)
	def plis(dc, p, w, h):
		for k in range(14):
			s = (k + 0.5) / 14
			dc.line([p(s - 0.02, 0.05), p(s + 0.01, 0.5), p(s - 0.015, 0.95)], fill=(70, 70, 72, 255), width=int(3 * S))

	calque_flou(r, plis, 3, 0.5)
	# bas : ourlet + couture
	y = P(r, 0, 0.08)[1]
	d.rectangle([r[0] - 2, y, r[2] + 2, r[3] + 2], fill=plus(BANDANA, 0.06))
	d.line([(r[0] - 2, y), (r[2] + 2, y)], fill=(0, 0, 0), width=2 * S)
	pointilles((r[0], y + 4 * S), (r[2], y + 4 * S), (75, 75, 75), 1.2, 6, 3)
	# reflet sur le dessus
	calque_flou(r, lambda dc, p, w, h: dc.rectangle([0, h * 0.25, w, h * 0.45], fill=(80, 80, 85, 255)), 6, 0.4)
	r = rect("Bandana_Noeud")
	degrade_v(r, plus(BANDANA, 0.12), BANDANA)
	for k in range(4):
		x = r[0] + W(r) * (k + 0.5) / 4
		courbe([(x, r[1] + 4 * S), (x + 4 * S, r[3] - 4 * S)], (0, 0, 0), 2)
	contour(r, (0, 0, 0), 2)


def cheveux():
	r = rect("Cheveux")
	degrade_v(r, plus(CHEV_C, 0.1), CHEV_F)
	for k in range(9):
		x = r[0] + W(r) * (k + 0.5) / 9
		courbe([(x, r[1] + 4 * S), (x + 3 * S, r[3] - 2 * S)], plus(CHEV_F, -0.25), 1.6)
		courbe([(x + 5 * S, r[1] + 4 * S), (x + 7 * S, r[1] + H(r) * 0.4)], plus(CHEV_C, 0.35), 1.2)


bandana()
cheveux()


# ---------------------------------------------------------------- manteau
def manteau():
	r = rect("Manteau")
	degrade_v(r, plus(MANT_C, -0.15), MANT_C)
	w, h = W(r), H(r)

	# plis verticaux : creux sombres + aretes claires
	def plis(dc, p, ww, hh):
		for k in range(16):
			s = (k + 0.5) / 16
			ond = 0.012 * math.sin(k * 1.7)
			dc.line([p(s + ond, 1.0), p(s - ond, 0.5), p(s + ond * 2, 0)], fill=MANT_F + (255,), width=int(5 * S))
			dc.line([p(s + 0.022 + ond, 0.95), p(s + 0.02 - ond, 0.5), p(s + 0.024 + ond * 2, 0)], fill=plus(MANT_C, 0.25) + (255,), width=int(2.5 * S))

	calque_flou(r, plis, 2.5, 0.8)
	# ombre sous le bourrelet
	calque_flou(r, lambda dc, p, ww, hh: dc.rectangle([0, 0, ww, hh * 0.12], fill=MANT_F + (255,)), 6, 0.8)
	# ourlet et couture du bas
	y = P(r, 0, 0.06)[1]
	d.rectangle([r[0] - 2, y, r[2] + 2, r[3] + 2], fill=plus(MANT_F, -0.1))
	d.line([(r[0] - 2, y), (r[2] + 2, y)], fill=(5, 20, 12), width=2 * S)
	pointilles((r[0], y - 5 * S), (r[2], y - 5 * S), plus(MANT_C, 0.35), 1.2, 7, 4)
	# revers devant (les deux bords de l'ouverture)
	for s0, s1 in ((0, 0.035), (0.965, 1)):
		x0, x1 = r[0] + w * s0, r[0] + w * s1
		d.rectangle([x0 - (2 if s0 == 0 else 0), r[1] - 2, x1 + (2 if s1 == 1 else 0), r[3] + 2], fill=plus(MANT_C, 0.12))
		xb = x1 if s0 == 0 else x0
		d.line([(xb, r[1]), (xb, r[3])], fill=(5, 20, 12), width=2 * S)
		pointilles((xb + (-5 * S if s0 == 0 else 5 * S), r[1]), (xb + (-5 * S if s0 == 0 else 5 * S), r[3]), plus(MANT_C, 0.4), 1.1, 7, 4)
	r = rect("Manteau_Doublure")
	degrade_v(r, plus(MANT_F, -0.3), MANT_F)
	for k in range(6):
		x = r[0] + W(r) * (k + 0.5) / 6
		courbe([(x, r[1]), (x + 3 * S, r[3])], plus(MANT_F, -0.4), 3)
	r = rect("Manteau_Bourrelet")
	degrade_v(r, plus(MANT_C, 0.22), MANT_C)

	def torsade(dc, p, ww, hh):
		for k in range(22):
			s = k / 22
			dc.line([p(s, 1.0), p(s + 0.05, 0.0)], fill=MANT_F + (255,), width=int(4 * S))
			dc.line([p(s + 0.015, 1.0), p(s + 0.065, 0.0)], fill=plus(MANT_C, 0.3) + (255,), width=int(2 * S))

	calque_flou(r, torsade, 1.5, 0.85)
	contour(r, (5, 20, 12), 2)


manteau()


# ---------------------------------------------------------------- echarpe
def echarpe():
	r = rect("Echarpe_Bande")
	degrade_v(r, plus(ECHARPE, 0.12), plus(ECHARPE, -0.2))

	def plis(dc, p, ww, hh):
		for k in range(14):
			s = k / 14
			dc.line([p(s, 1.0), p(s + 0.04, 0.0)], fill=plus(ECHARPE, -0.45) + (255,), width=int(3 * S))

	calque_flou(r, plis, 1.5, 0.8)
	contour(r, plus(ECHARPE, -0.6), 2)
	r = rect("Echarpe_Pans")
	degrade_v(r, plus(ECHARPE, 0.08), plus(ECHARPE, -0.15))

	def plis2(dc, p, ww, hh):
		for k in range(7):
			s = (k + 0.5) / 7
			dc.line([p(s, 1.0), p(s + 0.03, 0.0)], fill=plus(ECHARPE, -0.45) + (255,), width=int(4 * S))
			dc.line([p(s + 0.05, 1.0), p(s + 0.07, 0.0)], fill=plus(ECHARPE, 0.25) + (255,), width=int(2 * S))

	calque_flou(r, plis2, 2, 0.8)
	contour(r, plus(ECHARPE, -0.6), 2)


echarpe()


# ---------------------------------------------------------------- fourreaux, poignees, lame
def fourreau(nom, base):
	r = rect(nom)
	# t = tour autour du fourreau : bandes claires / sombres pour le volume laque
	degrade_v(r, plus(base, -0.25), plus(base, -0.25))
	for k, f in enumerate((0.0, 0.25, 0.5, 0.75)):
		y0, y1 = P(r, 0, f + 0.25)[1], P(r, 0, f)[1]
		degrade_v((r[0], y0, r[2], y1), plus(base, 0.18), plus(base, -0.2), marge=0)
	# embouchure (koiguchi) et bout (kojiri) dores, cordon pres de l'embouchure
	d.rectangle([r[0] - 2, r[1] - 2, r[0] + W(r) * 0.035, r[3] + 2], fill=OR)
	d.rectangle([r[0] + W(r) * 0.95, r[1] - 2, r[2] + 2, r[3] + 2], fill=plus(OR, -0.15))
	for k in range(3):
		x = r[0] + W(r) * (0.09 + k * 0.025)
		d.rectangle([x, r[1] - 2, x + W(r) * 0.012, r[3] + 2], fill=plus(base, -0.5) if base != BLANC else (60, 60, 70))


fourreau("Fourreau_Blanc", (232, 232, 225))
fourreau("Fourreau_Rouge", hx("#7A1A24"))
fourreau("Fourreau_Noir", (40, 40, 44))


def poignee(nom, tresse, fond):
	"""motif en losanges : tresse croisee sur fond de galuchat"""
	r = rect(nom)
	d.rectangle([r[0] - 2, r[1] - 2, r[2] + 2, r[3] + 2], fill=fond)
	n = 8
	pw = W(r) / n
	for k in range(n):
		x = r[0] + k * pw
		for y0, y1 in ((r[1], r[1] + H(r) / 2), (r[1] + H(r) / 2, r[3])):
			ym = (y0 + y1) / 2
			d.polygon([(x, y0), (x + pw / 2, ym), (x, y1), (x - pw * 0.1, ym)], fill=tresse)
			d.polygon([(x + pw, y0), (x + pw / 2, ym), (x + pw, y1), (x + pw * 1.1, ym)], fill=tresse)
	for k in range(n + 1):
		x = r[0] + k * pw
		d.line([(x, r[1]), (x, r[3])], fill=plus(tresse, -0.4), width=S)


poignee("Poignee_Blanche", (238, 238, 232), (40, 40, 40))
poignee("Poignee_Rouge", hx("#9A1E2C"), (30, 20, 20))
poignee("Poignee_Noire", (28, 28, 30), (210, 205, 195))

r = rect("Lame")
degrade_v(r, (250, 252, 255), (150, 160, 168))
y = P(r, 0, 0.55)[1]
pts = [(r[0] + k * W(r) / 30, y + math.sin(k * 1.3) * 2 * S) for k in range(31)]
courbe(pts, (255, 255, 255), 2)

# ---------------------------------------------------------------- sortie
out = img.resize((UV["taille"], UV["taille"]), Image.LANCZOS)
out.save(ICI / "Texture_zoro.png")
print("Texture_zoro.png ecrite")

if "--uv" in sys.argv:
	polys = json.loads(Path(sys.argv[sys.argv.index("--uv") + 1]).read_text())
	dbg = out.copy()
	dd = ImageDraw.Draw(dbg)
	for p in polys:
		dd.polygon([tuple(v) for v in p], outline=(0, 255, 255))
	dbg.save(ICI / "Texture_zoro_uv.png")
	print("Texture_zoro_uv.png ecrite")
