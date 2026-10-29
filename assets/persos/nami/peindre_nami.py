"""Peint tex_corps_nami.png (1024 x 1024 : peau, face, cheveux en cel-shading, haut vert a pois, jean, pastilles)
et tex_acc_nami.png (512 x 512 : baton, bourse, carte au tresor ; zones lues dans acc_nami.json).

Usage : uv run --with pillow assets/persos/nami/peindre_nami.py
Lit uv_nami.json et ombrage_nami.json (ecrits dans Blender par uv_nami.py : atlas() puis ombrage()).
Reperes : studs, monde Blender a la pose de repos (le perso regarde vers -Y, sa gauche est +X, pieds a Z = 0).
"""

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

DOSSIER = Path(__file__).resolve().parent
INFOS = json.loads((DOSSIER / "uv_nami.json").read_text(encoding="utf-8"))
OMBRE = json.loads((DOSSIER / "ombrage_nami.json").read_text(encoding="utf-8"))
TAILLE = INFOS["taille"]
SUR = 2  # sur-echantillonnage
D = INFOS["dens"]
TETE_C = (0.0, 0.0, 4.867)


def hexa(h):
	return tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))


PEAU, PEAU_OMBRE = hexa("#F5C9A0"), hexa("#D9A27E")
CHEVEUX = {"clair": hexa("#FFB45A"), "moyen": hexa("#F28C28"), "fonce": hexa("#C9661A"), "profond": (168, 78, 20), "lisere": (255, 224, 165)}
VERT, VERT_FONCE, POIS = hexa("#2E9E7A"), hexa("#1F7A5C"), hexa("#F4F4F4")
VERT_CLAIR = (112, 200, 150)
JEAN, JEAN_FONCE, OR = hexa("#4A7DB5"), hexa("#2F5A8A"), hexa("#E8B93A")
TATOUAGE = hexa("#2E5FA8")
CONTOUR = (40, 24, 20)
# teinte des ombres (multiplicateur) selon la matiere
TEINTE = {"peau": (0.83, 0.68, 0.66), "jean": (0.6, 0.62, 0.72), "vert": (0.55, 0.62, 0.62)}
MATIERE = {
	"UpperTorso": "peau", "LeftUpperArm": "peau", "RightUpperArm": "peau", "LeftLowerArm": "peau", "RightLowerArm": "peau",
	"LeftHand": "peau", "RightHand": "peau", "LeftFoot": "peau", "RightFoot": "peau", "UpperTorso_Haut": "vert",
	"LowerTorso_Jean": "jean", "LeftUpperLeg_Jean": "jean", "RightUpperLeg_Jean": "jean", "LeftLowerLeg_Jean": "jean", "RightLowerLeg_Jean": "jean",
	"Head": "peau",
}
BASE = {"peau": PEAU, "jean": JEAN, "vert": VERT}


def S(v):
	return v * SUR


# ---------------------------------------------------------------- objets projetes sur leur boite


class Proj:
	"""Dessin en coordonnees monde (studs) sur les faces d'un objet projete sur sa boite."""

	def __init__(self, nom):
		self.nom = nom
		info = INFOS["projetes"][nom]
		self.b = info["boite"]
		self.faces = info["faces"]  # {face: [x, y, densite]} : pixel du coin (a, b) = (0, 0)
		x0, x1, y0, y1, z0, z1 = self.b
		self.w, self.d, self.h = x1 - x0, y1 - y0, z1 - z0

	def taille(self, face):
		return {"Avant": (self.w, self.h), "Arriere": (self.w, self.h), "Droite": (self.d, self.h), "Gauche": (self.d, self.h), "Dessus": (self.w, self.d), "Dessous": (self.w, self.d)}[face]

	def rect(self, face):
		"""Rectangle (pixels sur-echantillonnes) de la face : x, y, l, h."""
		x, y, dn = self.faces[face]
		l, h = self.taille(face)
		return S(x), S(y), S(l * dn), S(h * dn)

	def ab(self, face, p):
		x0, x1, y0, y1, z0, z1 = self.b
		x, y, z = p
		return {
			"Avant": (x - x0, z1 - z), "Arriere": (x1 - x, z1 - z), "Droite": (y1 - y, z1 - z), "Gauche": (y - y0, z1 - z),
			"Dessus": (x - x0, y1 - y), "Dessous": (x - x0, y - y0),
		}[face]

	def dessiner(self, img, face, fn):
		"""fn(draw, P) dessine avec P(x, y, z) -> pixel local ; le resultat est colle seulement dans la face."""
		x, y, l, h = self.rect(face)
		dn = self.faces[face][2]
		calque = Image.new("RGBA", (int(math.ceil(l)), int(math.ceil(h))), (0, 0, 0, 0))
		dr = ImageDraw.Draw(calque)

		def P(*p):
			a, b = self.ab(face, p)
			return (S(a * dn), S(b * dn))

		fn(dr, P)
		img.alpha_composite(calque, (int(x), int(y)))

	def bande(self, img, fn):
		"""fn(draw, T, l) sur la bande Droite | Avant | Gauche | Arriere (meme densite) : T(t, z), t = distance (studs) le long du tour."""
		x, y, dn = self.faces["Droite"]
		l, h = 2 * (self.w + self.d), self.h
		calque = Image.new("RGBA", (int(S(l * dn)) + 1, int(S(h * dn)) + 1), (0, 0, 0, 0))
		dr = ImageDraw.Draw(calque)
		z1 = self.b[5]
		fn(dr, lambda t, z: (S(t * dn), S((z1 - z) * dn)), l)
		img.alpha_composite(calque, (int(S(x)), int(S(y))))

	def remplir(self, img, couleur, debord=2, faces=None):
		d = ImageDraw.Draw(img)
		for f in faces or self.faces:
			x, y, l, h = self.rect(f)
			d.rectangle([x - S(debord), y - S(debord), x + l + S(debord), y + h + S(debord)], fill=couleur)


def pointilles(dr, pts, couleur, ep=1.4, trait=0.05, vide=0.035):
	"""Couture surpiquee le long d'une polyligne (pixels) : traits de `trait` studs separes de `vide`."""
	for a, b in zip(pts, pts[1:]):
		lg = math.dist(a, b)
		if lg < 1e-6:
			continue
		pas = S((trait + vide) * D)
		n = int(lg / pas) + 1
		for k in range(n):
			t0, t1 = k * pas / lg, min((k * pas + S(trait * D)) / lg, 1)
			if t0 >= 1:
				break
			dr.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=couleur, width=max(1, int(S(ep))))


def courbe(f, t0, t1, n=24):
	return [f(t0 + (t1 - t0) * k / (n - 1)) for k in range(n)]


# ---------------------------------------------------------------- ombres douces (occlusion)


def ombres(img):
	"""Multiplie chaque objet projete par son occlusion (grille floutee), teinte selon la matiere, + bords assombris."""
	for nom, faces in OMBRE["grilles"].items():
		teinte = TEINTE[MATIERE[nom]]
		for face, g in faces.items():
			x, y, l, h = g["px"]
			nx, ny = g["n"]
			petit = Image.new("L", (nx, ny))
			petit.putdata([int(255 * min(1.0, max(0.0, (a - 0.3) / 0.62)) ** 0.9) for a in g["ao"]])
			lw, lh = max(1, int(S(l))), max(1, int(S(h)))
			masque = petit.resize((lw, lh), Image.BILINEAR).filter(ImageFilter.GaussianBlur(S(2)))
			# bords de la face un peu plus sombres (lecture « bloc arrondi »)
			marge = max(2, int(min(lw, lh) * 0.1))
			bord = Image.new("L", (lw, lh), int(255 * 0.82))
			ImageDraw.Draw(bord).rectangle([marge, marge, lw - 1 - marge, lh - 1 - marge], fill=255)
			bord = bord.filter(ImageFilter.GaussianBlur(marge * 0.7))
			masque = ImageChops.multiply(masque, bord)
			zone = img.crop((int(S(x)), int(S(y)), int(S(x)) + lw, int(S(y)) + lh)).convert("RGB")
			sombre = Image.merge("RGB", [c.point(lambda v, f=f: int(v * f)) for c, f in zip(zone.split(), teinte)])
			res = Image.composite(zone, sombre, masque)
			img.paste(res.convert("RGBA"), (int(S(x)), int(S(y))))


# ---------------------------------------------------------------- vetements et peau


def denim(img, p):
	"""Grain du jean : fines stries verticales claires et sombres."""
	rnd = random.Random(p.nom)
	for face in ("Droite", "Avant", "Gauche", "Arriere"):

		def f(dr, P):
			x, y, l, h = p.rect(face)
			for _ in range(int(l / S(1.2))):
				px = rnd.uniform(0, l)
				c = (110, 150, 200, 40) if rnd.random() < 0.5 else (30, 55, 95, 40)
				y0 = rnd.uniform(-h * 0.2, h)
				dr.line([(px, y0), (px, y0 + rnd.uniform(S(6), S(30)))], fill=c, width=1)

		p.dessiner(img, face, f)


def jean(img):
	coutures = (*OR, 255)
	lt = Proj("LowerTorso_Jean")
	lt.remplir(img, JEAN)
	denim(img, lt)
	# ceinture plus sombre, double surpiqure doree tout autour
	lt.bande(img, lambda dr, T, l: (
		dr.rectangle([T(0, 2.72), T(l, 2.585)], fill=(*JEAN_FONCE, 120)),
		pointilles(dr, [T(0, 2.705), T(l, 2.705)], coutures),
		pointilles(dr, [T(0, 2.6), T(l, 2.6)], coutures),
		dr.line([T(0, 2.585), T(l, 2.585)], fill=(*JEAN_FONCE, 255), width=int(S(1.5))),
	))

	def devant(dr, P):
		# braguette en J, poches avant arrondies
		pointilles(dr, [P(0.13, -0.6, 2.58), P(0.13, -0.6, 2.32)] + courbe(lambda t: P(0.13 * math.cos(t), -0.6, 2.32 - 0.12 * math.sin(t)), 0, math.pi / 2, 8), coutures)
		dr.line([P(0, -0.6, 2.58), P(0, -0.6, 2.18)], fill=(*JEAN_FONCE, 255), width=int(S(1.5)))
		for c in (1, -1):
			bord = courbe(lambda t: P(c * (0.5 + 0.48 * t), -0.6, 2.58 - 0.3 * t * t), 0, 1, 12)
			dr.line(bord, fill=(*JEAN_FONCE, 255), width=int(S(2)))
			pointilles(dr, [(x, y + S(3)) for x, y in bord], coutures)

	lt.dessiner(img, "Avant", devant)

	def poche_arriere(dr, P, z_haut=2.44):
		for c in (1, -1):
			cx = 0.48 * c
			pts = [P(cx - 0.27, 0.6, z_haut), P(cx + 0.27, 0.6, z_haut), P(cx + 0.25, 0.6, 2.06), P(cx, 0.6, 1.96), P(cx - 0.25, 0.6, 2.06)]
			dr.polygon(pts, fill=(*JEAN, 255), outline=(*JEAN_FONCE, 255))
			pointilles(dr, pts + [pts[0]], coutures)
			# petite surpiqure decorative en vague
			pointilles(dr, courbe(lambda t: P(cx - 0.18 + 0.36 * t, 0.6, 2.25 + 0.04 * math.sin(t * math.pi * 2)), 0, 1, 10), coutures)

	def derriere(dr, P):
		# empiecement en V et couture du milieu
		dr.line([P(0.98, 0.6, 2.5), P(0, 0.6, 2.4), P(-0.98, 0.6, 2.5)], fill=(*JEAN_FONCE, 255), width=int(S(1.5)))
		pointilles(dr, [P(0.98, 0.6, 2.48), P(0, 0.6, 2.38), P(-0.98, 0.6, 2.48)], coutures)
		dr.line([P(0, 0.6, 2.58), P(0, 0.6, 2.17)], fill=(*JEAN_FONCE, 255), width=int(S(1.5)))
		poche_arriere(dr, P)

	lt.dessiner(img, "Arriere", derriere)

	for cote in ("Left", "Right"):
		sg = 1 if cote == "Left" else -1
		xc = 0.4979 * sg
		ul, ll = Proj(cote + "UpperLeg_Jean"), Proj(cote + "LowerLeg_Jean")
		for p in (ul, ll):
			p.remplir(img, JEAN)
			denim(img, p)
			# coutures laterales (exterieur double doree, interieur simple)
			ext, inte = ("Gauche", "Droite") if sg > 0 else ("Droite", "Gauche")
			x0, x1, y0, y1, z0, z1 = p.b

			def cote_ext(dr, P, p=p):
				for dy in (-0.03, 0.03):
					pointilles(dr, [P(0, dy, p.b[5]), P(0, dy, p.b[4])], coutures)

			def cote_int(dr, P, p=p):
				pointilles(dr, [P(0, 0, p.b[5]), P(0, 0, p.b[4])], coutures)

			p.dessiner(img, ext, cote_ext)
			p.dessiner(img, inte, cote_int)

		def cuisse(dr, P):
			# reflets delaves en haut de cuisse (moustaches)
			for k in range(3):
				z = 2.3 - 0.07 * k
				dr.line([P(xc - 0.05 * sg, -0.6, z), P(xc + 0.28 * sg, -0.6, z - 0.08)], fill=(150, 185, 225, 90), width=int(S(2.2)))

		ul.dessiner(img, "Avant", cuisse)
		ul.dessiner(img, "Arriere", lambda dr, P: poche_arriere(dr, P, z_haut=2.6))

		def genou_cheville(dr, P):
			# plis du genou
			for k, (z, lg) in enumerate([(1.36, 0.28), (1.27, 0.34), (1.18, 0.24)]):
				pts = courbe(lambda t: P(xc + (t - 0.5) * lg * 2, -0.6, z + 0.035 * math.sin(t * math.pi) * (1 if k % 2 else -1)), 0, 1, 8)
				dr.line(pts, fill=(*JEAN_FONCE, 200), width=int(S(2)))
				dr.line([(x, y + S(2)) for x, y in pts], fill=(140, 175, 215, 110), width=int(S(1)))
			# plis accumules a la cheville (zigzags)
			for k, z in enumerate((0.62, 0.52, 0.43)):
				pts = [P(xc + (-0.45 + 0.15 * i) , -0.6, z + (0.04 if (i + k) % 2 else -0.02)) for i in range(7)]
				dr.line(pts, fill=(*JEAN_FONCE, 190), width=int(S(1.8)), joint="curve")
			# ourlet
			dr.rectangle([P(xc - 0.6, -0.6, 0.36), P(xc + 0.6, -0.6, 0.0)], fill=(*JEAN_FONCE, 140))

		def ourlet(dr, P):
			dr.rectangle([(0, P(0, 0, 0.36)[1]), (S(200), P(0, 0, 0.0)[1])], fill=(*JEAN_FONCE, 140))

		ll.dessiner(img, "Avant", genou_cheville)
		for face in ("Arriere", "Droite", "Gauche"):
			ll.dessiner(img, face, ourlet)
		ll.bande(img, lambda dr, T, l: pointilles(dr, [T(0, 0.37), T(l, 0.37)], coutures))


def haut(img):
	"""Haut couvrant : rayures vert fonce / blanc / vert clair, fine bande blanche en bas, liseré fonce au bord du haut."""
	p = Proj("UpperTorso_Haut")
	p.remplir(img, VERT)
	z_haut = lambda x, y: 4.06 - (0.1 * math.cos(x / 0.62 * math.pi / 2) if (y < 0 and abs(x) < 0.62) else 0.0) - (0.04 if y > 0 else 0.0)

	def rayures(dr, T, l):
		motif = [(VERT_FONCE, 0.07), (POIS, 0.04), (VERT_CLAIR, 0.08), (VERT, 0.07), (POIS, 0.04)]
		z, k = 3.5, 0
		while z < 4.45:
			c, e = motif[k % len(motif)]
			dr.rectangle([T(0, z + e), T(l, z)], fill=(*c, 255))
			z += e
			k += 1
		dr.rectangle([T(0, 3.5), T(l, 3.42)], fill=(*VERT_FONCE, 255))
		dr.rectangle([T(0, 3.49), T(l, 3.455)], fill=(*POIS, 255))

	p.bande(img, rayures)
	p.remplir(img, VERT_FONCE, faces=["Dessus", "Dessous"])

	def bord(y):
		def f(dr, P):
			x0, x1 = p.b[0], p.b[1]
			dr.line([P(x0 + (x1 - x0) * k / 40, y, z_haut(x0 + (x1 - x0) * k / 40, y)) for k in range(41)], fill=(*VERT_FONCE, 255), width=int(S(2.5)))

		return f

	p.dessiner(img, "Avant", bord(-0.55))
	p.dessiner(img, "Arriere", bord(0.55))


def peau(img):
	t = Proj("UpperTorso")

	def ventre(dr, P):
		# seulement les clavicules (pas de nombril ni de traits du ventre : avertissement de moderation Roblox)
		for c in (1, -1):
			dr.line([P(0.12 * c, -0.5, 4.17), P(0.45 * c, -0.5, 4.2)], fill=(*PEAU_OMBRE, 150), width=int(S(1.6)))

	t.dessiner(img, "Avant", ventre)

	# tatouage bleu sur l'epaule gauche (face exterieure du haut du bras) : cercle et tourbillon a 3 branches
	bras = Proj("LeftUpperArm")

	def tatouage(dr, P):
		cy, cz, r = 0.0, 3.86, 0.17
		x = bras.b[1]
		dr.ellipse([P(x, cy - r, cz + r), P(x, cy + r, cz - r)], outline=(*TATOUAGE, 255), width=int(S(2.2)))
		for k in range(3):
			a0 = k * 2 * math.pi / 3
			pts = [P(x, cy + 0.13 * t * math.cos(a0 + 2.2 * t), cz + 0.13 * t * math.sin(a0 + 2.2 * t)) for t in [i / 10 for i in range(11)]]
			dr.line(pts, fill=(*TATOUAGE, 255), width=int(S(2.4)), joint="curve")
		dr.ellipse([P(x, cy - 0.025, cz + 0.025), P(x, cy + 0.025, cz - 0.025)], fill=(*TATOUAGE, 255))

	bras.dessiner(img, "Gauche", tatouage)


# ---------------------------------------------------------------- tete et face


def racine(x):
	"""Racine des cheveux sur l'avant (meme formule que construire_nami.py), relative au centre de la tete."""
	t = min(1.0, max(0.0, (abs(x) - 0.38) / 0.22))
	return 0.31 - 0.3 * t * t * (3 - 2 * t)


def degrade(img, poly, haut, bas, masque_clip=None):
	ys = [p[1] for p in poly]
	y0, y1 = int(min(ys)), int(max(ys)) + 1
	m = Image.new("L", img.size, 0)
	ImageDraw.Draw(m).polygon(poly, fill=255)
	if masque_clip is not None:
		m = ImageChops.multiply(m, masque_clip)
	c = Image.new("RGBA", img.size)
	d = ImageDraw.Draw(c)
	for y in range(y0, y1):
		t = (y - y0) / max(y1 - y0 - 1, 1)
		d.line([(0, y), (img.size[0], y)], fill=tuple(int(haut[i] + (bas[i] - haut[i]) * t) for i in range(3)) + (255,))
	img.paste(c, (0, 0), m)


def ellipse(cx, cz, rx, rz, n=48, debut=0.0, fin=2 * math.pi):
	return [(cx + rx * math.cos(debut + (fin - debut) * k / (n - 1)), cz + rz * math.sin(debut + (fin - debut) * k / (n - 1))) for k in range(n)]


def bezier(p0, p1, p2, n=16):
	return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [k / (n - 1) for k in range(n)]]


def oeil(img, f, sg):
	"""Grand oeil anime (style de la reference), sg = +1 : oeil gauche du perso (x > 0).
	Contour noir epais en haut avec une petite aile vers l'exterieur, grand iris ambre en degrade, 2 reflets."""
	d = ImageDraw.Draw(img)
	P = lambda pts: [f(x, z) for x, z in pts]
	cx, cz = 0.24 * sg, -0.05
	rx, rz = 0.14, 0.16
	# blanc de l'oeil : haut un peu aplati, bas arrondi
	haut = bezier((cx - rx * sg, cz + 0.02), (cx, cz + rz * 1.45), (cx + rx * sg, cz + 0.045), 24)
	bas = bezier((cx + rx * sg, cz + 0.045), (cx + 0.01 * sg, cz - rz * 1.35), (cx - rx * sg, cz + 0.02), 24)
	blanc = haut + bas
	d.polygon(P(blanc), fill=(252, 250, 247))
	masque = Image.new("L", img.size, 0)
	ImageDraw.Draw(masque).polygon(P(blanc), fill=255)
	# iris : grand, brun-rouge en haut vers orange ambre en bas
	ix, iz = cx + 0.006 * sg, cz - 0.012
	iris = ellipse(ix, iz, 0.1, 0.13)
	degrade(img, P(iris), (92, 34, 18), (238, 128, 52), masque)
	calque = Image.new("RGBA", img.size)
	dc = ImageDraw.Draw(calque)
	dc.polygon(P(ellipse(ix, iz + 0.014, 0.055, 0.075)), fill=(58, 20, 12, 255))  # pupille
	dc.line(P(iris + iris[:1]), fill=(70, 26, 14, 255), width=int(S(2.2)))  # contour de l'iris
	dc.line(P(bezier((ix - 0.06, iz - 0.075), (ix, iz - 0.1), (ix + 0.06, iz - 0.075), 10)), fill=(255, 175, 95, 255), width=int(S(3)))  # lueur basse
	dc.line(P([(x, z - 0.012) for x, z in haut]), fill=(60, 30, 25, 140), width=int(S(9)))  # ombre de la paupiere
	img.paste(calque, (0, 0), ImageChops.multiply(calque.split()[3], masque))
	# reflets blancs nets : un grand en haut (cote du nez), un petit en bas
	for rx_, rz_, r in ((ix - 0.04 * sg, iz + 0.06, 0.038), (ix + 0.045 * sg, iz - 0.06, 0.018)):
		d.polygon(P(ellipse(rx_, rz_, r, r * 1.1)), fill=(255, 255, 255))
	# contour du haut epais, plus epais vers l'exterieur, petite aile
	pts = P(haut)
	for k in range(len(pts) - 1):
		d.line([pts[k], pts[k + 1]], fill=CONTOUR, width=int(S(4 + 5 * k / (len(pts) - 1))))
	ex = haut[-1]
	d.polygon(P([(ex[0] - 0.04 * sg, ex[1] + 0.03), (ex[0] + 0.05 * sg, ex[1] + 0.035), (ex[0] - 0.01 * sg, ex[1] - 0.02)]), fill=CONTOUR)
	# pli de la paupiere, trait du bas (cote exterieur), cils du bas
	d.line(P(bezier((cx - 0.08 * sg, cz + 0.17), (cx + 0.01 * sg, cz + 0.215), (cx + 0.11 * sg, cz + 0.15), 12)), fill=(150, 85, 60), width=int(S(1.6)))
	d.line(P(bas[3:12]), fill=(150, 70, 45), width=int(S(1.8)))
	# sourcil fin orange, court, legerement arque (le gauche un peu plus haut : air malicieux)
	lev = 0.02 if sg > 0 else 0.0
	d.line(P(bezier((cx - 0.09 * sg, cz + 0.255 + lev), (cx + 0.01 * sg, cz + 0.29 + lev), (cx + 0.1 * sg, cz + 0.25 + lev), 12)), fill=(200, 95, 35), width=int(S(2.6)), joint="curve")


def face(img, f):
	d = ImageDraw.Draw(img)
	rose = Image.new("RGBA", img.size)
	for sg in (1, -1):
		ImageDraw.Draw(rose).polygon([f(x, z) for x, z in ellipse(0.27 * sg, -0.2, 0.07, 0.03)], fill=(245, 150, 140, 80))
	img.alpha_composite(rose)
	for sg in (1, -1):
		oeil(img, f, sg)
	# nez a peine suggere, petite bouche avec un coin releve (malicieux)
	d.line([f(0.012, -0.175), f(-0.006, -0.19)], fill=PEAU_OMBRE, width=int(S(2.2)))
	d.line([f(x, z) for x, z in bezier((-0.06, -0.3), (0.0, -0.31), (0.055, -0.29), 12)], fill=(120, 55, 45), width=int(S(2.6)), joint="curve")
	d.line([f(0.055, -0.29), f(0.07, -0.278)], fill=(120, 55, 45), width=int(S(2)))


def tete(img):
	"""Peau de la tete (ombres par la grille d'occlusion, voir ombres()), cheveux fonces sous les nappes, face."""
	t = Proj("Head")
	cx, cy, cz = TETE_C
	t.remplir(img, PEAU)
	t.remplir(img, CHEVEUX["fonce"], faces=["Dessus", "Arriere"])
	# cotes : cheveux au-dessus de la tempe (le reste est sous les nappes)
	for face_, x in (("Droite", t.b[0]), ("Gauche", t.b[1])):
		t.dessiner(img, face_, lambda dr, P, x=x: dr.polygon([P(x, cy - 0.7, cz + racine(0.6)), P(x, cy + 0.7, cz + racine(0.6)), P(x, cy + 0.7, cz + 1), P(x, cy - 0.7, cz + 1)], fill=(*CHEVEUX["fonce"], 255)))
	y_av = t.b[2]
	t.dessiner(img, "Avant", lambda dr, P: dr.polygon([P(cx + x / 40 * 1.3 - 0.65, y_av, cz + racine(x / 40 * 1.3 - 0.65)) for x in range(41)] + [P(cx + 0.7, y_av, cz + 1), P(cx - 0.7, y_av, cz + 1)], fill=(*CHEVEUX["fonce"], 255)))


def tete_face(img):
	t = Proj("Head")
	x, y, dn = t.faces["Avant"]
	x0, z1 = t.b[0], t.b[5]
	cx, cz = TETE_C[0], TETE_C[2]
	face(img, lambda a, b: (S(x + (cx + a - x0) * dn), S(y + (z1 - (cz + b)) * dn)))


# ---------------------------------------------------------------- cheveux lisses (nappes et rubans peints)


def cheveux(img):
	"""Chaque meche / nappe a son rectangle (u en travers, v de la racine a la pointe) : degrade vertical, anneau de
	lumiere en zigzag, sillons fonces et liseres clairs dans le sens des cheveux, pointes plus foncees."""
	rnd = random.Random(3)
	for nom, liste in INFOS["meches"].items():
		for m in liste:
			x, y, w, h = [S(v) for v in m["rect"]]
			calque = Image.new("RGB", (int(w) + S(4), int(h) + S(4)))
			d = ImageDraw.Draw(calque)
			H = calque.size[1]
			for k in range(H):
				v = k / max(H - 1, 1)
				if v < 0.55:
					c0, c1, t = CHEVEUX["moyen"], CHEVEUX["moyen"], 0
				else:
					c0, c1, t = CHEVEUX["moyen"], CHEVEUX["fonce"], (v - 0.55) / 0.45
				d.line([(0, k), (calque.size[0], k)], fill=tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3)))
			W = calque.size[0]
			# anneau de lumiere (dessus de la tete) : bande claire, bord du bas en zigzag
			if m["genre"] in ("calotte", "nappe") and nom == "Head_Cheveux":
				haut_, bas_ = (0.1, 0.2) if m["genre"] == "calotte" else (0.16, 0.27)
				haut_, bas_ = haut_ * H, bas_ * H
				n = max(3, int(W / S(10)))
				zig = [(W * i / n, bas_ + (S(4) if i % 2 else -S(3))) for i in range(n + 1)]
				d.polygon([(0, haut_), (W, haut_)] + zig[::-1], fill=CHEVEUX["clair"])
				d.line([(0, haut_), (W, haut_)], fill=CHEVEUX["lisere"], width=max(1, int(S(1))))
			# sillons et liseres dans le sens des cheveux
			for _ in range(max(2, int(W / S(7)))):
				u = rnd.uniform(0.04, 0.96) * W
				v0, v1 = rnd.uniform(0.2, 0.4) * H, rnd.uniform(0.6, 0.97) * H
				d.line([(u, v0), (u + rnd.uniform(-S(2), S(2)), v1)], fill=CHEVEUX["fonce"], width=max(1, int(S(1.3))))
				d.line([(u + S(1.6), v0 + S(6)), (u + S(1.6), v0 + (v1 - v0) * 0.45)], fill=CHEVEUX["lisere"], width=max(1, int(S(0.8))))
			img.paste(calque, (int(x) - S(2), int(y) - S(2)))


# ---------------------------------------------------------------- pastilles


def pastilles(img):
	d = ImageDraw.Draw(img)
	degr = {
		"or": [(255, 232, 140), OR, (165, 115, 28)],
		"verre": [(235, 252, 255), hexa("#BFE8F5"), (110, 180, 215)],
		"sandale": [(160, 108, 68), hexa("#7A4E2D"), (78, 48, 26)],
		"jean": [JEAN, JEAN, JEAN_FONCE],
		"cheveux": [CHEVEUX["moyen"], CHEVEUX["fonce"], CHEVEUX["fonce"]],
		"ceinture": [(80, 80, 88), (43, 43, 48), (18, 18, 22)],
		"clous": [(255, 255, 255), (237, 237, 237), (170, 170, 178)],
	}
	for nom, (x, y, w, h) in INFOS["pastilles"].items():
		c0, c1, c2 = degr[nom]
		for k in range(int(S(h))):
			t = k / max(S(h) - 1, 1)
			a, b, u = (c0, c1, t * 2) if t < 0.5 else (c1, c2, t * 2 - 1)
			d.line([(S(x), S(y) + k), (S(x + w), S(y) + k)], fill=tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3)))


def texture():
	img = Image.new("RGBA", (S(TAILLE), S(TAILLE)), (*PEAU, 255))
	pastilles(img)
	for nom, mat in MATIERE.items():
		if mat != "peau":
			Proj(nom).remplir(img, BASE[mat])
	peau(img)
	haut(img)
	jean(img)
	tete(img)
	ombres(img)
	tete_face(img)
	cheveux(img)
	img = img.convert("RGB").resize((TAILLE, TAILLE), Image.LANCZOS)
	img.save(DOSSIER / "tex_corps_nami.png", optimize=True)
	print("tex_corps_nami.png ecrit")




# ---------------------------------------------------------------- accessoires (tex_acc_nami.png)


def texture_acc():
	acc = json.loads((DOSSIER / "acc_nami.json").read_text(encoding="utf-8"))
	T = acc["taille"]
	img = Image.new("RGBA", (S(T), S(T)), (*hexa("#F2E6C4"), 255))
	d = ImageDraw.Draw(img)

	def Z(nom):
		x, y, w, h = acc["zones"][nom]
		return S(x), S(y), S(w), S(h)

	def bandes_verticales(nom, couleurs):
		"""Degrade horizontal (tour du cylindre) : couleurs = [(position 0..1, rgb)]."""
		x, y, w, h = Z(nom)
		for k in range(int(w)):
			t = k / max(w - 1, 1)
			for (t0, c0), (t1, c1) in zip(couleurs, couleurs[1:]):
				if t0 <= t <= t1:
					u = (t - t0) / max(t1 - t0, 1e-6)
					d.line([(x + k, y), (x + k, y + h)], fill=tuple(int(c0[i] + (c1[i] - c0[i]) * u) for i in range(3)))
					break

	clair, base, fonce = (190, 236, 252), hexa("#6FC3E8"), (60, 140, 190)
	# baton : reflet net en bande (cote du haut), ombre opposee
	bandes_verticales("baton", [(0, base), (0.18, base), (0.22, clair), (0.3, clair), (0.34, base), (0.6, base), (0.75, fonce), (0.9, base), (1, base)])
	bandes_verticales("bague", [(0, hexa("#3A8FC4")), (0.25, (120, 190, 230)), (0.45, hexa("#3A8FC4")), (0.75, (30, 80, 130)), (1, hexa("#3A8FC4"))])
	bandes_verticales("rouleau", [(0, (250, 242, 215)), (0.4, hexa("#F2E6C4")), (0.75, (200, 180, 140)), (1, (250, 242, 215))])
	for nom in ("ruban", "cordon"):
		x, y, w, h = Z(nom)
		d.rectangle([x, y, x + w, y + h], fill=hexa("#C8342C"))
		d.rectangle([x, y + h * 0.6, x + w, y + h], fill=(150, 30, 28))
	# bourse doree : degrade vertical, plis qui partent du col, couture
	x, y, w, h = Z("bourse")
	for k in range(int(h)):
		t = k / h
		c = [int(a + (b - a) * t) for a, b in zip((255, 228, 130), (175, 120, 30))]
		d.line([(x, y + k), (x + w, y + k)], fill=tuple(c))
	for i in range(10):
		px = x + w * (i + 0.5) / 10
		d.line([(px, y), (px + S(4), y + h * 0.45)], fill=(160, 110, 25), width=S(2))
		d.line([(px + S(3), y), (px + S(7), y + h * 0.35)], fill=(255, 238, 170), width=S(1))
	d.line([(x, y + h * 0.82), (x + w, y + h * 0.82)], fill=(150, 100, 22), width=S(2))
	# carte : papier vieilli, cote, ile, chemin en pointilles, croix rouge, rose des vents
	x, y, w, h = Z("carte")
	d.rectangle([x, y, x + w, y + h], fill=hexa("#F2E6C4"))
	rnd = random.Random(7)
	for _ in range(60):
		cx, cy, r = x + rnd.uniform(0, w), y + rnd.uniform(0, h), rnd.uniform(S(4), S(16))
		d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(232, 216, 176))
	cad = [(x + S(6), y + S(6)), (x + w - S(6), y + h - S(6))]
	d.rectangle(cad, outline=(150, 105, 60), width=S(2))
	ile = [(0.15, 0.55), (0.25, 0.3), (0.45, 0.22), (0.62, 0.3), (0.7, 0.5), (0.6, 0.72), (0.4, 0.8), (0.22, 0.72)]
	pts = [(x + w * a, y + h * b) for a, b in ile]
	d.polygon(pts, fill=(196, 220, 150), outline=(110, 85, 50))
	d.line(pts + [pts[0]], fill=(110, 85, 50), width=S(2), joint="curve")
	for k in range(3):  # vagues
		vx, vy = x + w * (0.78 + 0.05 * k), y + h * (0.2 + 0.25 * k)
		d.arc([vx, vy, vx + S(14), vy + S(8)], 200, 340, fill=(90, 140, 180), width=S(2))
	chemin = [(0.24, 0.62), (0.32, 0.48), (0.42, 0.55), (0.5, 0.4)]
	pointilles(d, [(x + w * a, y + h * b) for a, b in chemin], (170, 40, 35), ep=1.5, trait=0.15, vide=0.12)
	cx, cy, r = x + w * 0.53, y + h * 0.37, S(9)
	d.line([(cx - r, cy - r), (cx + r, cy + r)], fill=(200, 35, 30), width=S(4))
	d.line([(cx - r, cy + r), (cx + r, cy - r)], fill=(200, 35, 30), width=S(4))
	rx, ry, rr = x + w * 0.84, y + h * 0.78, S(18)
	d.polygon([(rx, ry - rr), (rx + rr * 0.25, ry), (rx, ry + rr), (rx - rr * 0.25, ry)], fill=(120, 80, 45))
	d.polygon([(rx - rr, ry), (rx, ry - rr * 0.25), (rx + rr, ry), (rx, ry + rr * 0.25)], fill=(160, 115, 70))
	d.ellipse([rx - S(3), ry - S(3), rx + S(3), ry + S(3)], fill=(200, 35, 30))
	img = img.convert("RGB").resize((T, T), Image.LANCZOS)
	img.save(DOSSIER / "tex_acc_nami.png", optimize=True)
	print("tex_acc_nami.png ecrit")


if __name__ == "__main__":
	texture()
	if (DOSSIER / "acc_nami.json").exists():
		texture_acc()
