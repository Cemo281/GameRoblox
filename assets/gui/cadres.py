"""Cadres de carte par rarete (280 x 368 = le double de la carte de l'inventaire, 140 x 184).

Usage : uv run --with pillow assets/gui/cadres.py
Sortie dans assets/gui/cadres/ : <Rarete>.png (Commun, Rare, Legendaire, Mythique, Secret), secret_reflet.png
(bande de lumiere a faire defiler par-dessus le cadre Secret), apercu.png (les 5 cadres avec le portrait de nami)
et infos.json (zone interieure ou poser le portrait).
Couleurs : src/shared/GachaConfig.luau.
"""

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

DOSSIER = Path(__file__).parent
SORTIE = DOSSIER / "cadres"

RARETES = {
	"Commun": (163, 162, 165),
	"Rare": (0, 120, 255),
	"Legendaire": (255, 190, 0),
	"Mythique": (200, 0, 255),
	"Secret": (255, 40, 40),
}
L, H = 280, 368
S = 4  # sur-echantillonnage (anticrenelage), tout est dessine en L*S x H*S puis reduit
RAYON = 26
BORD = 14
SOMBRE = (14, 13, 22)


def melange(a, b, t):
	return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def px(v):
	return round(v * S)


def masque_arrondi(retrait, rayon):
	m = Image.new("L", (px(L), px(H)), 0)
	ImageDraw.Draw(m).rounded_rectangle((px(retrait), px(retrait), px(L - retrait) - 1, px(H - retrait) - 1), radius=px(rayon), fill=255)
	return m


def degrade(arrets):
	"""Degrade vertical : arrets = [(position 0..1, couleur RGB), ...]."""
	img = Image.new("RGB", (1, px(H)))
	for y in range(px(H)):
		t = y / (px(H) - 1)
		for (ta, ca), (tb, cb) in zip(arrets, arrets[1:]):
			if ta <= t <= tb:
				img.putpixel((0, y), melange(ca, cb, (t - ta) / (tb - ta)))
				break
	return img.resize((px(L), px(H)))


def calque(couleur, masque):
	c = Image.new("RGBA", (px(L), px(H)), (*couleur, 0))
	c.putalpha(masque)
	return c


def etoile(dessin, cx, cy, rayon, branches, creux, couleur, angle=-90):
	pts = []
	for i in range(branches * 2):
		r = rayon if i % 2 == 0 else rayon * creux
		a = math.radians(angle + i * 180 / branches)
		pts.append((px(cx) + px(r) * math.cos(a), px(cy) + px(r) * math.sin(a)))
	dessin.polygon(pts, fill=couleur)


def eclats(dessin, couleur, graine, n, zone):
	"""Etincelles a 4 branches."""
	alea = random.Random(graine)
	for _ in range(n):
		x, y = alea.uniform(zone[0], zone[2]), alea.uniform(zone[1], zone[3])
		r = alea.uniform(4, 10)
		etoile(dessin, x, y, r, 4, 0.18, (*couleur, alea.randint(140, 230)), angle=0)


def cadre(nom, couleur):
	interieur = masque_arrondi(BORD, RAYON - BORD * 0.6)
	exterieur = masque_arrondi(0, RAYON)
	anneau = ImageChops.subtract(exterieur, interieur)
	clair = melange(couleur, (255, 255, 255), 0.55)
	fonce = melange(couleur, (0, 0, 0), 0.55)

	# fond : degrade sombre vers la couleur, halo doux derriere la tete
	fond = degrade([(0, melange(SOMBRE, couleur, 0.10)), (0.55, melange(SOMBRE, couleur, 0.30)), (1, melange(SOMBRE, couleur, 0.62))]).convert("RGBA")
	halo = Image.new("L", (px(L), px(H)), 0)
	ImageDraw.Draw(halo).ellipse((px(L * 0.12), px(H * 0.06), px(L * 0.88), px(H * 0.58)), fill=110)
	halo = halo.filter(ImageFilter.GaussianBlur(px(34)))
	fond.alpha_composite(calque(melange(couleur, (255, 255, 255), 0.35), halo))

	motif = Image.new("RGBA", (px(L), px(H)), (0, 0, 0, 0))
	d = ImageDraw.Draw(motif)
	if nom == "Legendaire":
		# rayons depuis le haut + eclats
		for i in range(12):
			a0 = math.radians(-180 + i * 15 + 3)
			a1 = a0 + math.radians(6)
			cx, cy, r = px(L / 2), px(H * 0.30), px(H)
			d.polygon([(cx, cy), (cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1))], fill=(*clair, 26))
			d.polygon([(cx, cy), (cx + r * math.cos(-a0), cy + r * math.sin(-a0)), (cx + r * math.cos(-a1), cy + r * math.sin(-a1))], fill=(*clair, 26))
		eclats(d, (255, 248, 210), 7, 14, (BORD + 8, BORD + 8, L - BORD - 8, H - BORD - 8))
	elif nom == "Mythique":
		# motif d'etoiles en quinconce
		for j, y in enumerate(range(0, H + 30, 30)):
			for x in range(-15 if j % 2 else 0, L + 30, 30):
				etoile(d, x, y, 5.5, 5, 0.45, (*clair, 46), angle=-90 + (x + y) % 36)
		eclats(d, (240, 215, 255), 11, 6, (BORD + 10, BORD + 10, L - BORD - 10, H * 0.5))
	elif nom == "Secret":
		# lueur interieure qui part de la bordure
		lueur = anneau.filter(ImageFilter.GaussianBlur(px(10)))
		motif.alpha_composite(calque(melange(couleur, (255, 255, 255), 0.25), lueur.point(lambda v: min(255, v * 2))))
		eclats(d, (255, 220, 220), 23, 8, (BORD + 10, BORD + 10, L - BORD - 10, H - BORD - 10))
	fond.alpha_composite(motif)
	fond.putalpha(ImageChops.multiply(fond.getchannel("A"), interieur))

	# bordure : degrade clair en haut (reflet) -> couleur -> fonce en bas
	bordure = degrade([(0, clair), (0.10, melange(couleur, (255, 255, 255), 0.2)), (0.25, couleur), (1, fonce)]).convert("RGBA")
	bordure.putalpha(anneau)
	img = Image.new("RGBA", (px(L), px(H)), (0, 0, 0, 0))
	img.alpha_composite(fond)
	img.alpha_composite(bordure)
	d = ImageDraw.Draw(img)
	# reflet : arc blanc sur le haut de la bordure
	reflet = Image.new("L", (px(L), px(H)), 0)
	ImageDraw.Draw(reflet).rounded_rectangle((px(3), px(3), px(L - 3) - 1, px(H * 0.5)), radius=px(RAYON - 3), outline=170, width=px(3))
	reflet = ImageChops.multiply(reflet, degrade([(0, (255,) * 3), (0.16, (0,) * 3), (1, (0,) * 3)]).convert("L"))
	img.alpha_composite(calque((255, 255, 255), reflet))
	# filets : sombre a l'interieur de la bordure, fin et sombre a l'exterieur
	d.rounded_rectangle((px(BORD), px(BORD), px(L - BORD) - 1, px(H - BORD) - 1), radius=px(RAYON - BORD * 0.6), outline=(*SOMBRE, 220), width=px(2))
	d.rounded_rectangle((0, 0, px(L) - 1, px(H) - 1), radius=px(RAYON), outline=(*melange(fonce, (0, 0, 0), 0.4), 255), width=px(1.5))
	if nom == "Secret":
		# bordure double : second filet lumineux, separe de la bordure par un filet sombre
		e = BORD + 5
		d.rounded_rectangle((px(BORD + 2), px(BORD + 2), px(L - BORD - 2) - 1, px(H - BORD - 2) - 1), radius=px(RAYON - BORD * 0.6 - 2), outline=(*SOMBRE, 255), width=px(3))
		d.rounded_rectangle((px(e), px(e), px(L - e) - 1, px(H - e) - 1), radius=px(RAYON - BORD * 0.6 - 5), outline=(*melange(couleur, (255, 255, 255), 0.45), 255), width=px(2.5))
	if nom in ("Legendaire", "Mythique", "Secret"):
		# eclats aux coins de la bordure
		for cx, cy in ((BORD * 0.5 + 6, BORD * 0.5 + 6), (L - BORD * 0.5 - 6, BORD * 0.5 + 6), (BORD * 0.5 + 6, H - BORD * 0.5 - 6), (L - BORD * 0.5 - 6, H - BORD * 0.5 - 6)):
			etoile(d, cx, cy, 9, 4, 0.22, (255, 255, 255, 235), angle=0)
	return img.resize((L, H), Image.LANCZOS)


def reflet_secret():
	"""Bande diagonale (45 degres) au centre, bords doux, a deplacer de gauche a droite par-dessus le cadre."""
	img = Image.new("L", (L, H), 0)
	pixels = img.load()
	for y in range(H):
		for x in range(L):
			dist = abs((x - L / 2) + (y - H / 2)) / math.sqrt(2)  # distance a la diagonale qui passe par le centre
			pixels[x, y] = round(150 * math.exp(-((dist / 18) ** 2)) + 60 * math.exp(-((dist / 45) ** 2)))
	bande = Image.new("RGBA", (L, H), (255, 245, 245, 0))
	bande.putalpha(img)
	return bande


def apercu(cadres):
	portrait = Image.open(DOSSIER / "nami" / "portrait.png").convert("RGBA")
	cote = L - 2 * BORD
	portrait = portrait.resize((cote, cote), Image.LANCZOS)
	# fondu du bas du portrait (buste coupe) et decoupe dans la zone interieure
	fondu = Image.new("L", (cote, cote), 255)
	for y in range(cote):
		fondu.paste(round(255 * min(1, (cote - y) / (cote * 0.18))), (0, y, cote, y + 1))
	portrait.putalpha(ImageChops.multiply(portrait.getchannel("A"), fondu))
	marge, ecart = 24, 20
	feuille = Image.new("RGBA", (marge * 2 + len(cadres) * L + (len(cadres) - 1) * ecart, marge * 2 + H), (38, 40, 48, 255))
	interieur = masque_arrondi(BORD, RAYON - BORD * 0.6).resize((L, H), Image.LANCZOS)
	for i, (nom, img) in enumerate(cadres.items()):
		carte = img.copy()
		calque_p = Image.new("RGBA", (L, H), (0, 0, 0, 0))
		calque_p.paste(portrait, (BORD, BORD))
		calque_p.putalpha(ImageChops.multiply(calque_p.getchannel("A"), interieur))
		# portrait sous la bordure : fond du cadre, portrait, puis bordure remise par-dessus
		bordure = img.copy()
		bordure.putalpha(ImageChops.multiply(img.getchannel("A"), ImageChops.invert(interieur)))
		carte.alpha_composite(calque_p)
		carte.alpha_composite(bordure)
		feuille.alpha_composite(carte, (marge + i * (L + ecart), marge))
	return feuille


def main():
	SORTIE.mkdir(exist_ok=True)
	cadres = {}
	for nom, couleur in RARETES.items():
		cadres[nom] = cadre(nom, couleur)
		cadres[nom].save(SORTIE / f"{nom}.png")
	reflet_secret().save(SORTIE / "secret_reflet.png")
	apercu(cadres).save(SORTIE / "apercu.png")
	infos = {
		"taille": [L, H],
		"carte_inventaire": [L // 2, H // 2],
		"zone_interieure": {"position": [BORD, BORD], "taille": [L - 2 * BORD, H - 2 * BORD], "note": "le portrait se pose ici (largeur de la zone, en haut)"},
		"secret_reflet": "bande diagonale centree : la faire defiler de -1 a +1 largeur de carte (Position X), dans un cadre ClipsDescendants",
		"couleurs": RARETES,
	}
	ancien = SORTIE / "infos.json"
	if ancien.exists():  # IDs Roblox notes apres l'envoi : a garder (a renvoyer si l'image a change)
		infos["ids_roblox"] = json.loads(ancien.read_text(encoding="utf-8")).get("ids_roblox", {})
	(SORTIE / "infos.json").write_text(json.dumps(infos, indent="\t", ensure_ascii=False), encoding="utf-8")
	print("ecrit", sorted(p.name for p in SORTIE.iterdir()))


if __name__ == "__main__":
	main()
