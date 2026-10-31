"""Peint torse_luffy_anime.png : decalque transparent du devant de UpperTorso, style anime de la tenue v6 (aplats nets,
pas de contours) : pectoraux, abdos, cicatrice en X. Remplace torse_luffy.png (traits bruns) pour la tenue v6.

A lancer avec le Python systeme (Pillow) : python -I peindre_torse_anime.py
Pose dans Studio : Decal Face = Front sur UpperTorso, sur la peau #E8B48C.
Coordonnees en studs dans le repere du HumanoidRootPart (x = droite du perso, y = haut) : UpperTorso couvre
x de -0,972 a 0,972 et y de -0,6 a 1,098. Vu de face, la droite du perso est a gauche de l'image.
Seule une bande centrale se voit dans l'ouverture de la chemise v6 (|x| < 0,27 en haut, 0,40 en bas) : la cicatrice
et les abdos y tiennent ; les pecs (ombre dessous, reflet, sillon) debordent sous la chemise. Pas de nombril ni de detail sous la ceinture (regles Roblox, voir l'avertissement de nami).
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).resolve().parent
X0, X1, Y0, Y1 = -0.972, 0.972, -0.6, 1.098
W, H = 1024, 896
SUR = 3  # sur-echantillonnage (bords nets mais lisses)
PEAU = (232, 180, 140)  # apercu seulement : la peau vient de la skin
OMBRE = (70, 30, 16)
REFLET = (255, 248, 236)
CICATRICE = (108, 72, 62)
CICATRICE_BORD = (176, 116, 96)
CENTRE_X = (0.0, 0.64)
POINTES = [(0.46, 1.04), (-0.46, 1.04), (0.42, 0.22), (-0.42, 0.22)]  # le bout des branches passe sous la chemise


def p(x, y):
	return ((X1 - x) / (X1 - X0) * W * SUR, (Y1 - y) / (Y1 - Y0) * H * SUR)


def bezier(points, n=40):
	res = []
	for i in range(n + 1):
		t = i / n
		if len(points) == 3:
			a, b, c = points
			res.append(tuple((1 - t) ** 2 * a[k] + 2 * (1 - t) * t * b[k] + t * t * c[k] for k in range(2)))
		else:
			a, b, c, d = points
			res.append(tuple((1 - t) ** 3 * a[k] + 3 * (1 - t) ** 2 * t * b[k] + 3 * (1 - t) * t * t * c[k] + t ** 3 * d[k] for k in range(2)))
	return res


def croissant(haut, bas):
	"""Forme fermee entre deux courbes (studs) : bord du haut puis bord du bas a l'envers."""
	return [p(*q) for q in bezier(haut)] + [p(*q) for q in reversed(bezier(bas))]


def cicatrice(marge):
	"""Contours (studs) des 4 branches et du coeur du X ; marge > 0 : contour elargi pour le liseré."""
	rng = random.Random(13)
	cx, cy = CENTRE_X
	polys = []
	for k, (tx, ty) in enumerate(POINTES):
		dx, dy = tx - cx, ty - cy
		lg = math.hypot(dx, dy)
		ux, uy = dx / lg, dy / lg
		nx, ny = -uy, ux
		courbe_s = 0.022 * (1 if k % 2 else -1)  # branches a peine creusees
		cotes = []
		for cote in (1, -1):
			# eclats : encoches en V etroites (negatives) et petites pointes (positives), a des positions au hasard
			eclats = [(rng.uniform(0.12, 0.88), rng.uniform(0.012, 0.03), rng.uniform(0.3, 0.6)) for _ in range(rng.randint(2, 4))]
			eclats += [(rng.uniform(0.15, 0.8), rng.uniform(0.008, 0.018), -rng.uniform(0.25, 0.45)) for _ in range(rng.randint(1, 2))]
			pts = []
			for i in range(121):
				t = i / 120
				larg = 0.09 * (1 - t) ** 1.3 + 0.003  # epais au coeur, pointe fine
				for t0, w, prof in eclats:
					larg *= 1 - prof * max(0.0, 1 - abs(t - t0) / w)
				larg += marge * (1 - t * 0.6)
				bx = cx + dx * t + nx * courbe_s * math.sin(math.pi * t)
				by = cy + dy * t + ny * courbe_s * math.sin(math.pi * t)
				pts.append((bx + nx * larg * cote, by + ny * larg * cote))
			cotes.append(pts)
		polys.append(cotes[0] + list(reversed(cotes[1])))
	# coeur du X : losange arrondi qui soude les branches
	polys.append([(cx + (0.075 + marge) * math.cos(a) * (1 + 0.15 * math.sin(3 * a)), cy + (0.064 + marge) * math.sin(a)) for a in [i * math.pi / 20 for i in range(40)]])
	return polys


def peindre():
	calques = {c: Image.new("L", (W * SUR, H * SUR), 0) for c in ("ombre", "reflet", "bord", "cicatrice")}
	d = {c: ImageDraw.Draw(m) for c, m in calques.items()}
	for s in (1, -1):
		# abdos seulement (la peau vient de la skin) : 2 rangees (4 blocs), ombre en croissant sous chaque bloc
		# (memes extremites en haut et en bas : epais au milieu, effile aux bouts), reflet en haut du bloc
		for y in (0.0, -0.36):
			d["ombre"].polygon(croissant([(s * 0.03, y), (s * 0.14, y - 0.03), (s * 0.3, y - 0.02), (s * 0.38, y + 0.035)],
				[(s * 0.03, y), (s * 0.14, y - 0.125), (s * 0.3, y - 0.115), (s * 0.38, y + 0.035)]), fill=255)
			d["reflet"].polygon(croissant([(s * 0.08, y + 0.2), (s * 0.18, y + 0.24), (s * 0.3, y + 0.2)],
				[(s * 0.08, y + 0.2), (s * 0.18, y + 0.145), (s * 0.3, y + 0.2)]), fill=255)
		# bord exterieur des abdos (ligne semi-lunaire) : croissant effile
		d["ombre"].polygon(croissant([(s * 0.37, 0.32), (s * 0.41, 0.0), (s * 0.39, -0.35), (s * 0.33, -0.6)],
			[(s * 0.37, 0.32), (s * 0.49, 0.0), (s * 0.47, -0.35), (s * 0.33, -0.6)]), fill=255)
	for s in (1, -1):
		# pectoraux : ombre en croissant sous le pec (du sternum vers l'aisselle, remonte sous la chemise), reflet en haut
		d["ombre"].polygon(croissant([(s * 0.02, 0.4), (s * 0.13, 0.33), (s * 0.3, 0.31), (s * 0.46, 0.44)],
			[(s * 0.02, 0.4), (s * 0.13, 0.21), (s * 0.31, 0.18), (s * 0.46, 0.44)]), fill=255)
		d["reflet"].polygon(croissant([(s * 0.14, 0.5), (s * 0.25, 0.6), (s * 0.4, 0.54)],
			[(s * 0.14, 0.5), (s * 0.26, 0.45), (s * 0.4, 0.54)]), fill=255)
	# sillon entre les pecs : aplat etroit, effile, jusque sous le coeur du X
	d["ombre"].polygon(croissant([(0.0, 0.36), (0.026, 0.44), (0.02, 0.52), (0.0, 0.6)], [(0.0, 0.36), (-0.026, 0.44), (-0.02, 0.52), (0.0, 0.6)]), fill=255)
	# ligne blanche entre les abdos : aplat etroit, effile
	d["ombre"].polygon(croissant([(0.0, 0.32), (0.022, 0.1), (0.022, -0.3), (0.0, -0.6)], [(0.0, 0.32), (-0.022, 0.1), (-0.022, -0.3), (0.0, -0.6)]), fill=255)
	# cicatrice en X, dans l'ouverture de la chemise (|x| < 0,27 en haut) : 4 branches epaisses au centre, effilees en
	# pointes un peu courbes, bords dechiquetes (encoches irregulieres), liseré clair
	for cle, marge in (("bord", 0.012), ("cicatrice", 0.0)):
		for poly in cicatrice(marge):
			d[cle].polygon([p(*q) for q in poly], fill=255)
	img = Image.new("RGBA", (W * SUR, H * SUR), (0, 0, 0, 0))
	# ombres et reflets translucides : ils assombrissent / eclaircissent n'importe quelle couleur de peau ; cicatrice opaque
	for cle, couleur, opacite in (("ombre", OMBRE, 0.32), ("reflet", REFLET, 0.35), ("bord", CICATRICE_BORD, 1.0), ("cicatrice", CICATRICE, 1.0)):
		m = calques[cle].filter(ImageFilter.GaussianBlur(1.2))  # bord net, juste anticrenele
		m = m.point(lambda v, o=opacite: int(v * o))
		img.alpha_composite(Image.merge("RGBA", (*[Image.new("L", m.size, c) for c in couleur], m)))
	img = img.resize((W, H), Image.LANCZOS)
	chemin = DOSSIER / "torse_luffy_anime.png"
	img.save(chemin)
	apercu = Image.new("RGBA", (W, H), PEAU + (255,))
	apercu.alpha_composite(img)
	apercu.convert("RGB").save(DOSSIER / "apercu_torse_luffy_anime.png")
	return chemin


if __name__ == "__main__":
	print(peindre())
