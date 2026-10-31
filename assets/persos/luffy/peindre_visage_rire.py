"""Peint visage_luffy_rire.png : decalque transparent du devant de la tete (Decal Face = Front sur Head) : luffy qui rit,
yeux fermes en arcs, sourcils releves, bouche grande ouverte avec les dents du haut et du bas et la langue, plis de rire,
cicatrice recousue sous l'oeil gauche.

A lancer avec le Python systeme (Pillow) : python -I peindre_visage_rire.py
Coordonnees : (u, v) dans [0, 1], u = 0 a gauche de l'image (droite du perso, vu de face), v = 0 en haut.
apercu_visage_rire.png : le decalque sur la peau #E8B48C, pour verifier.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).resolve().parent
T = 1024
SUR = 3
PEAU = (232, 180, 140)  # apercu seulement
NOIR = (24, 16, 16)
BOUCHE = (92, 22, 28)
DENTS = (250, 248, 242)
DENTS_OMBRE = (206, 200, 196)
LANGUE = (226, 96, 100)
CICATRICE = (120, 52, 44)


def P(u, v):
	return (u * T * SUR, v * T * SUR)


def bezier(pts, n=60):
	res = []
	for i in range(n + 1):
		t = i / n
		if len(pts) == 3:
			a, b, c = pts
			res.append(tuple((1 - t) ** 2 * a[k] + 2 * (1 - t) * t * b[k] + t * t * c[k] for k in range(2)))
		else:
			a, b, c, d = pts
			res.append(tuple((1 - t) ** 3 * a[k] + 3 * (1 - t) ** 2 * t * b[k] + 3 * (1 - t) * t * t * c[k] + t ** 3 * d[k] for k in range(2)))
	return res


def trait(d, pts, larg, couleur, effile=True):
	"""Trait epais (larg en fraction de T), effile aux deux bouts si effile."""
	n = len(pts)
	for i, (u, v) in enumerate(pts):
		t = i / (n - 1)
		r = larg / 2 * T * SUR * ((0.25 + 0.75 * (4 * t * (1 - t)) ** 0.5) if effile else 1)
		x, y = P(u, v)
		d.ellipse([x - r, y - r, x + r, y + r], fill=couleur)


def peindre():
	img = Image.new("RGBA", (T * SUR, T * SUR), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	for s in (-1, 1):  # s = -1 : moitie gauche de l'image (droite du perso)
		cx = 0.5 + s * 0.2
		# yeux fermes : arc en ^ epais, petite virgule de cil au coin exterieur
		trait(d, bezier([(cx - 0.11, 0.47), (cx - 0.02, 0.36), (cx + 0.03, 0.36), (cx + 0.11, 0.46)]), 0.032, NOIR)
		trait(d, bezier([(cx + s * 0.1, 0.455), (cx + s * 0.13, 0.43), (cx + s * 0.15, 0.435)], 20), 0.016, NOIR)
		# sourcils releves
		trait(d, bezier([(cx - 0.1, 0.3), (cx - 0.02, 0.24), (cx + 0.05, 0.25), (cx + 0.11, 0.29)]), 0.024, NOIR)
		# plis de rire aux coins de la bouche
		trait(d, bezier([(0.5 + s * 0.35, 0.57), (0.5 + s * 0.38, 0.62), (0.5 + s * 0.36, 0.67)], 30), 0.014, NOIR)
	# bouche grande ouverte : bord du haut presque droit, bas tres arrondi
	haut = bezier([(0.18, 0.585), (0.35, 0.62), (0.65, 0.62), (0.82, 0.585)])
	bas = bezier([(0.82, 0.585), (0.74, 0.86), (0.26, 0.86), (0.18, 0.585)])
	contour = [P(*q) for q in haut + bas]
	d.polygon(contour, fill=BOUCHE)
	# masque de la bouche pour garder dents et langue dedans
	masque = Image.new("L", img.size, 0)
	ImageDraw.Draw(masque).polygon(contour, fill=255)
	dedans = Image.new("RGBA", img.size, (0, 0, 0, 0))
	dd = ImageDraw.Draw(dedans)
	# dents du haut : bande sous le bord du haut, separations legeres
	dd.polygon([P(*q) for q in bezier([(0.15, 0.56), (0.35, 0.6), (0.65, 0.6), (0.85, 0.56)])
		+ list(reversed(bezier([(0.15, 0.64), (0.35, 0.685), (0.65, 0.685), (0.85, 0.64)])))], fill=DENTS)
	for k in range(1, 8):
		u = 0.22 + k * 0.07
		dd.line([P(u, 0.6), P(u, 0.68)], fill=DENTS_OMBRE, width=5)
	# langue au fond, puis dents du bas devant elle, au centre du bas de la bouche
	dd.ellipse([*P(0.37, 0.68), *P(0.63, 0.79)], fill=LANGUE)
	dd.polygon([P(*q) for q in bezier([(0.27, 0.735), (0.38, 0.815), (0.62, 0.815), (0.73, 0.735)])
		+ list(reversed(bezier([(0.29, 0.715), (0.39, 0.77), (0.61, 0.77), (0.71, 0.715)])))], fill=DENTS)
	for k in range(1, 6):
		u = 0.3 + k * 0.066
		dd.line([P(u, 0.75), P(u, 0.82)], fill=DENTS_OMBRE, width=5)
	img.paste(dedans, (0, 0), Image.composite(dedans.split()[3], Image.new("L", img.size, 0), masque))
	# contour noir de la bouche
	d.line(contour + [contour[0]], fill=NOIR, width=int(0.016 * T * SUR), joint="curve")
	# cicatrice sous l'oeil gauche du perso (a droite de l'image) : trait courbe + deux points de couture
	cic = bezier([(0.6, 0.53), (0.66, 0.545), (0.72, 0.535)], 30)
	trait(d, cic, 0.014, CICATRICE)
	for u in (0.64, 0.69):
		trait(d, bezier([(u - 0.008, 0.515), (u, 0.5375), (u + 0.008, 0.56)], 20), 0.009, CICATRICE, effile=False)
	img = img.filter(ImageFilter.GaussianBlur(0.8)).resize((T, T), Image.LANCZOS)
	chemin = DOSSIER / "visage_luffy_rire.png"
	img.save(chemin)
	apercu = Image.new("RGBA", (T, T), PEAU + (255,))
	apercu.alpha_composite(img)
	apercu.convert("RGB").save(DOSSIER / "apercu_visage_rire.png")
	return chemin


if __name__ == "__main__":
	print(peindre())
