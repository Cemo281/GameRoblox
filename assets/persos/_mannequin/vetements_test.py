"""Images de calibration des vetements classiques Roblox (585x559).

Chaque zone du modele officiel (face de chaque bloc) a sa couleur et son nom ecrit
a l'endroit, plus des bandes numerotees tous les 16 px pour reperer ou le modele
se coupe entre les pieces R15 (bras haut / bas / main, torse haut / bas...).

Usage : python assets/persos/_mannequin/vetements_test.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DOSSIER = Path(__file__).parent
TAILLE = (585, 559)

# (x, y, largeur, hauteur) de chaque face dans le modele officiel.
# Torse : R F L B en ligne, U au-dessus et D en dessous de F.
# Bras / jambe droits : L B R F, U et D au-dessus / en dessous de F.
# Bras / jambe gauches : F L B R, U et D au-dessus / en dessous de F.
ZONES = {
	"torse": {
		"HAUT": (231, 8, 128, 64),
		"DROITE": (165, 74, 64, 128),
		"AVANT": (231, 74, 128, 128),
		"GAUCHE": (361, 74, 64, 128),
		"DOS": (427, 74, 128, 128),
		"BAS": (231, 204, 128, 64),
	},
	"droit": {
		"HAUT": (217, 289, 64, 64),
		"INT": (19, 355, 64, 128),
		"DOS": (85, 355, 64, 128),
		"EXT": (151, 355, 64, 128),
		"AVANT": (217, 355, 64, 128),
		"BAS": (217, 485, 64, 64),
	},
	"gauche": {
		"HAUT": (308, 289, 64, 64),
		"AVANT": (308, 355, 64, 128),
		"EXT": (374, 355, 64, 128),
		"DOS": (440, 355, 64, 128),
		"INT": (506, 355, 64, 128),
		"BAS": (308, 485, 64, 64),
	},
}

COULEURS = {
	"AVANT": (230, 60, 60),
	"DOS": (60, 110, 230),
	"HAUT": (240, 200, 40),
	"BAS": (60, 170, 80),
	"DROITE": (200, 90, 220),
	"GAUCHE": (40, 200, 200),
	"EXT": (200, 90, 220),
	"INT": (40, 200, 200),
}

NOMS = {
	"shirt": {"torse": "TORSE", "droit": "BRAS D", "gauche": "BRAS G"},
	"pants": {"torse": "BASSIN", "droit": "JAMBE D", "gauche": "JAMBE G"},
}


def police(taille):
	for nom in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"):
		try:
			return ImageFont.truetype(nom, taille)
		except OSError:
			pass
	return ImageFont.load_default()


def assombrir(c, f):
	return tuple(int(v * f) for v in c)


def dessiner_zone(d, rect, couleur, lignes):
	x, y, w, h = rect
	# bandes de 16 px alternees, numerotees sur le bord gauche
	for i in range(0, h, 16):
		c = couleur if (i // 16) % 2 == 0 else assombrir(couleur, 0.8)
		d.rectangle([x, y + i, x + w - 1, min(y + i + 15, y + h - 1)], fill=c)
		d.text((x + 2, y + i + 2), str(i), font=police(9), fill=(255, 255, 255))
	d.rectangle([x, y, x + w - 1, y + h - 1], outline=(0, 0, 0), width=2)
	# triangle dans le coin haut-droit : repere de sens et de miroir
	d.polygon([(x + w - 14, y + 2), (x + w - 3, y + 2), (x + w - 3, y + 13)], fill=(0, 0, 0))
	# nom au centre, la plus grande taille qui rentre
	for t in range(28, 8, -1):
		f = police(t)
		boites = [d.textbbox((0, 0), ligne, font=f) for ligne in lignes]
		lw = max(b[2] - b[0] for b in boites)
		lh = sum(b[3] - b[1] for b in boites) + 4 * (len(lignes) - 1)
		if lw <= w - 10 and lh <= h - 10:
			break
	cy = y + (h - lh) / 2
	for ligne, b in zip(lignes, boites):
		bw, bh = b[2] - b[0], b[3] - b[1]
		d.text((x + (w - bw) / 2 - b[0], cy - b[1]), ligne, font=f, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
		cy += bh + 4


REGLE = [(230, 40, 40), (250, 220, 30), (40, 180, 60), (40, 90, 230)]


def dessiner_regle(d, rect):
	"""Bandes de 4 px rouge / jaune / vert / bleu, numerotees tous les 16 px."""
	x, y, w, h = rect
	for i in range(0, h, 4):
		d.rectangle([x, y + i, x + w - 1, min(y + i + 3, y + h - 1)], fill=REGLE[(i // 4) % 4])
	for i in range(0, h, 16):
		d.text((x + w / 2, y + i + 8), str(i), font=police(11), fill=(255, 255, 255), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))


def generer_regle(type_vetement):
	img = Image.new("RGBA", TAILLE, (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	for faces in ZONES.values():
		for rect in faces.values():
			dessiner_regle(d, rect)
	chemin = DOSSIER / f"regle_{type_vetement}.png"
	img.save(chemin)
	print(chemin)


def generer_face():
	"""Quadrillage 512x512 pour reperer la zone couverte par le Decal face."""
	img = Image.new("RGBA", (512, 512), (255, 255, 255, 255))
	d = ImageDraw.Draw(img)
	for i in range(0, 512, 64):
		for j in range(0, 512, 64):
			c = REGLE[((i + j) // 64) % 4]
			d.rectangle([i, j, i + 63, j + 63], fill=c + (255,))
			d.text((i + 32, j + 32), f"{i // 64}{j // 64}", font=police(26), fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
	d.line([(256, 0), (256, 511)], fill=(0, 0, 0), width=3)
	d.line([(0, 256), (511, 256)], fill=(0, 0, 0), width=3)
	d.polygon([(470, 4), (507, 4), (507, 41)], fill=(0, 0, 0))
	chemin = DOSSIER / "test_face.png"
	img.save(chemin)
	print(chemin)


def generer(type_vetement):
	img = Image.new("RGBA", TAILLE, (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	for groupe, faces in ZONES.items():
		prefixe = NOMS[type_vetement][groupe]
		for face, rect in faces.items():
			dessiner_zone(d, rect, COULEURS[face], prefixe.split(" ") + [face] if rect[2] <= 64 else [prefixe, face])
	chemin = DOSSIER / f"test_{type_vetement}.png"
	img.save(chemin)
	print(chemin)


if __name__ == "__main__":
	generer("shirt")
	generer("pants")
	generer_regle("shirt")
	generer_regle("pants")
	generer_face()
