"""Textures des VFX de luffy (style anime : formes nettes, fond transparent), en niveaux de clair pour etre teintees
par la Color des ParticleEmitter (Rafale : couleur peau).

poing.png : poing stylise vu de face (4 phalanges, pouce replie, contour doux) pour la Rafale
trait.png : trait de vitesse vertical effile aux deux bouts (Orientation VelocityParallel)
eclairs_haki.png : planche 4 x 4 d'eclairs noir et rouge (Flipbook Random) pour Eclairs_Haki
eclat.png, anneau.png, trait_vif.png, lignes_impact.png, poussiere.png : coups de la rafale et impact final (Action)
Usage : uv run --with pillow assets/persos/luffy/vfx_luffy.py
"""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

DOSSIER = Path(__file__).parent / "vfx"
S = 2  # dessin en 2x puis reduction


def poing():
	w = 256 * S
	img = Image.new("RGBA", (w, w), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	u = w / 256
	# dos de la main + 4 phalanges arrondies (blanc casse), ombres grises dans les creux
	d.rounded_rectangle([46 * u, 70 * u, 214 * u, 214 * u], radius=40 * u, fill=(250, 250, 250, 255))
	for i in range(4):
		x0 = (50 + i * 41) * u
		d.rounded_rectangle([x0, 44 * u, x0 + 40 * u, 120 * u], radius=18 * u, fill=(255, 255, 255, 255))
	for i in range(1, 4):
		x = (50 + i * 41) * u
		d.line([(x, 60 * u), (x, 112 * u)], fill=(200, 200, 200, 255), width=int(5 * u))
	# pouce replie en travers, sous les phalanges
	d.rounded_rectangle([70 * u, 128 * u, 176 * u, 166 * u], radius=18 * u, fill=(235, 235, 235, 255))
	d.line([(80 * u, 168 * u), (170 * u, 168 * u)], fill=(195, 195, 195, 255), width=int(5 * u))
	img = img.filter(ImageFilter.GaussianBlur(1.2 * S))
	img.resize((256, 256), Image.LANCZOS).save(DOSSIER / "poing.png")


def trait():
	w, h = 32 * S, 256 * S
	img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	# losange tres allonge : pointe fine en haut et en bas, plus large au tiers haut
	d.polygon([(w / 2, 0), (w * 0.85, h * 0.3), (w / 2, h), (w * 0.15, h * 0.3)], fill=(255, 255, 255, 255))
	img = img.filter(ImageFilter.GaussianBlur(1.5 * S))
	img.resize((32, 256), Image.LANCZOS).save(DOSSIER / "trait.png")


def zigzag(rng, a, b, n, ampl):
	"""Ligne brisee de a a b : n segments, ecarts perpendiculaires aleatoires (plus forts au milieu)."""
	import math

	(x0, y0), (x1, y1) = a, b
	dx, dy = x1 - x0, y1 - y0
	lg = math.hypot(dx, dy)
	px, py = -dy / lg, dx / lg
	pts = [a]
	for i in range(1, n):
		t = i / n
		e = rng.uniform(-1, 1) * ampl * math.sin(math.pi * t) ** 0.5
		pts.append((x0 + dx * t + px * e, y0 + dy * t + py * e))
	pts.append(b)
	return pts


def foudre():
	"""eclairs_haki.png : planche 4 x 4 (1024 px) d'eclairs du Haki, lue en Flipbook Random par un ParticleEmitter
	(un eclair different a chaque particule : crepitement). Halo rouge, corps noir, bords rouge sombre, coeur rouge vif,
	ramifications. Couleurs dans la texture (Color du ParticleEmitter = blanc)."""
	import math
	import random

	rng = random.Random(7)
	c = 256 * S
	img = Image.new("RGBA", (4 * c, 4 * c), (0, 0, 0, 0))
	for k in range(16):
		ox, oy = (k % 4) * c, (k // 4) * c
		ang = rng.uniform(0, math.pi)
		r = c * 0.44
		cx, cy = ox + c / 2, oy + c / 2
		a = (cx - r * math.cos(ang), cy - r * math.sin(ang))
		b = (cx + r * math.cos(ang), cy + r * math.sin(ang))
		tronc = zigzag(rng, a, b, rng.randint(7, 10), c * 0.12)
		branches = []
		for _ in range(rng.randint(2, 3)):
			i = rng.randint(2, len(tronc) - 3)
			p = tronc[i]
			d = ang + rng.choice((-1, 1)) * rng.uniform(0.5, 1.1)
			lg = c * rng.uniform(0.14, 0.24)
			q = (p[0] + lg * math.cos(d), p[1] + lg * math.sin(d))
			q = (min(max(q[0], ox + 8 * S), ox + c - 8 * S), min(max(q[1], oy + 8 * S), oy + c - 8 * S))
			branches.append(zigzag(rng, p, q, 4, c * 0.04))
		cellule = Image.new("RGBA", img.size, (0, 0, 0, 0))
		halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
		dh = ImageDraw.Draw(halo)
		for ligne, w in [(tronc, 40)] + [(br, 22) for br in branches]:
			dh.line(ligne, fill=(255, 0, 25, 255), width=w * S, joint="curve")
		halo = halo.filter(ImageFilter.GaussianBlur(13 * S))
		cellule.alpha_composite(halo)
		cellule.alpha_composite(halo)  # deux passes : halo plus lumineux, sous les traits
		d = ImageDraw.Draw(cellule)
		for ligne, f in [(tronc, 1.0)] + [(br, 0.6) for br in branches]:
			d.line(ligne, fill=(90, 0, 0, 255), width=int(20 * f * S), joint="curve")  # bords rouge sombre
			d.line(ligne, fill=(8, 0, 0, 255), width=int(13 * f * S), joint="curve")  # corps noir
			d.line(ligne, fill=(255, 30, 30, 255), width=max(3, int(5 * f * S)), joint="curve")  # coeur rouge vif
		img.alpha_composite(cellule)
	img.resize((1024, 1024), Image.LANCZOS).save(DOSSIER / "eclairs_haki.png")


def eclat():
	"""eclat.png : etoile d'impact anime (12 pointes irregulieres, coeur blanc, bord jaune puis orange), couleurs dans
	la texture (Color du ParticleEmitter = blanc) ; chaque coup de la rafale et l'impact final."""
	import math
	import random

	rng = random.Random(3)
	w = 256 * S
	c = w / 2
	img = Image.new("RGBA", (w, w), (0, 0, 0, 0))

	def etoile(r_out, r_in, couleur, decal=0.0):
		pts = []
		n = 12
		for i in range(2 * n):
			a = math.pi * i / n + decal
			r = (r_out * rng.uniform(0.62, 1.0)) if i % 2 == 0 else r_in * rng.uniform(0.85, 1.1)
			pts.append((c + r * math.cos(a), c + r * math.sin(a)))
		couche = Image.new("RGBA", img.size, (0, 0, 0, 0))
		ImageDraw.Draw(couche).polygon(pts, fill=couleur)
		img.alpha_composite(couche)

	halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
	ImageDraw.Draw(halo).ellipse([c - w * 0.3, c - w * 0.3, c + w * 0.3, c + w * 0.3], fill=(255, 190, 60, 150))
	img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(14 * S)))
	etoile(w * 0.49, w * 0.16, (255, 140, 30, 255))  # bord orange
	etoile(w * 0.40, w * 0.13, (255, 225, 70, 255), 0.13)  # jaune
	etoile(w * 0.27, w * 0.10, (255, 255, 255, 255), 0.05)  # coeur blanc
	ImageDraw.Draw(img).ellipse([c - w * 0.11, c - w * 0.11, c + w * 0.11, c + w * 0.11], fill=(255, 255, 255, 255))
	img = img.filter(ImageFilter.GaussianBlur(0.8 * S))
	img.resize((256, 256), Image.LANCZOS).save(DOSSIER / "eclat.png")


def anneau():
	"""anneau.png : onde d'air nette (anneau blanc, bord exterieur franc, interieur qui s'estompe), teinte par Color."""
	w = 256 * S
	c = w / 2
	img = Image.new("RGBA", (w, w), (0, 0, 0, 0))
	for i in range(40):  # degrade vers l'interieur : r de 0,47 a 0,33
		t = i / 39
		r = w * (0.47 - 0.14 * t)
		a = int(255 * (1 - t) ** 1.6)
		ImageDraw.Draw(img).ellipse([c - r, c - r, c + r, c + r], outline=(255, 255, 255, a), width=int(2 * S))
	ImageDraw.Draw(img).ellipse([c - w * 0.47, c - w * 0.47, c + w * 0.47, c + w * 0.47], outline=(255, 255, 255, 255), width=int(7 * S))
	img = img.filter(ImageFilter.GaussianBlur(0.7 * S))
	img.resize((256, 256), Image.LANCZOS).save(DOSSIER / "anneau.png")


def trait_vif():
	"""trait_vif.png : trait de vitesse fin, horizontal, dans une image carree (une particule Roblox est toujours carree :
	une image etroite serait etiree en gros rectangle). Tete vive a gauche, queue fine qui s'efface a droite.
	Avec Orientation VelocityParallel, l'horizontale de l'image suit la vitesse (Size = longueur du trait)."""
	w = 256 * S
	img = Image.new("RGBA", (w, w), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	c = w / 2
	e = w * 0.035  # demi-epaisseur de la tete
	d.polygon([(0, c), (w * 0.1, c - e), (w, c), (w * 0.1, c + e)], fill=(255, 255, 255, 255))
	masque = Image.new("L", (w, w))
	for x in range(w):  # queue qui s'efface
		ImageDraw.Draw(masque).line([(x, 0), (x, w)], fill=int(255 * max(0.0, 1 - x / w) ** 0.6))
	img.putalpha(ImageChops.multiply(img.getchannel("A"), masque))
	img = img.filter(ImageFilter.GaussianBlur(0.6 * S))
	img.resize((256, 256), Image.LANCZOS).save(DOSSIER / "trait_vif.png")


def lignes_impact():
	"""lignes_impact.png : lignes d'impact anime en etoile (24 traits effiles partant d'un cercle vide vers le bord),
	blanc, pour l'impact final (une particule face camera qui grossit vite)."""
	import math
	import random

	rng = random.Random(11)
	w = 512 * S
	c = w / 2
	img = Image.new("RGBA", (w, w), (0, 0, 0, 0))
	d = ImageDraw.Draw(img)
	for i in range(28):
		a = 2 * math.pi * i / 28 + rng.uniform(-0.08, 0.08)
		r0, r1 = w * rng.uniform(0.2, 0.3), w * rng.uniform(0.42, 0.5)
		e = w * rng.uniform(0.008, 0.016)
		px, py = -math.sin(a), math.cos(a)
		x0, y0 = c + r0 * math.cos(a), c + r0 * math.sin(a)
		x1, y1 = c + r1 * math.cos(a), c + r1 * math.sin(a)
		m = 0.35  # plus large au tiers interieur, pointes aux deux bouts
		xm, ym = x0 + (x1 - x0) * m, y0 + (y1 - y0) * m
		d.polygon([(x0, y0), (xm + px * e, ym + py * e), (x1, y1), (xm - px * e, ym - py * e)], fill=(255, 255, 255, 255))
	img = img.filter(ImageFilter.GaussianBlur(0.8 * S))
	img.resize((512, 512), Image.LANCZOS).save(DOSSIER / "lignes_impact.png")


def poussiere():
	"""poussiere.png : bouffee de poussiere en aplats (3 tons de gris clair, bords nets arrondis, style anime),
	teinte par Color (beige)."""
	import random

	rng = random.Random(5)
	w = 256 * S
	img = Image.new("RGBA", (w, w), (0, 0, 0, 0))
	bulles = [(rng.uniform(0.3, 0.7) * w, rng.uniform(0.35, 0.68) * w, rng.uniform(0.14, 0.22) * w) for _ in range(7)]
	for ton, dx, dy, f in ((175, 0.02, 0.04, 1.0), (215, 0, 0, 0.94), (250, -0.025, -0.03, 0.62)):  # ombre, base, reflet
		d = ImageDraw.Draw(img)
		for x, y, r in bulles:
			r2 = r * f
			x2, y2 = x + dx * w, y + dy * w
			d.ellipse([x2 - r2, y2 - r2, x2 + r2, y2 + r2], fill=(ton, ton, ton, 255))
	img = img.filter(ImageFilter.GaussianBlur(1.2 * S))
	img.resize((256, 256), Image.LANCZOS).save(DOSSIER / "poussiere.png")


if __name__ == "__main__":
	DOSSIER.mkdir(exist_ok=True)
	poing()
	trait()
	foudre()
	eclat()
	anneau()
	trait_vif()
	lignes_impact()
	poussiere()
	print("ecrit", [p.name for p in DOSSIER.iterdir()])
