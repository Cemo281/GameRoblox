"""Accessoires 3D de zoro, modelises sur le mannequin de zoro_apercu.blend.

A lancer DANS Blender (MCP Blender), un accessoire par appel :
	exec(open(r"<depot>/assets/persos/zoro/accessoires_zoro.py", encoding="utf-8").read())
	construire("Bandana")
Repere du mannequin : 1 unite = 1 stud, le perso regarde vers -Y, sa droite est -X, pieds a Z = 0.
Roblox (x, y, z) relatif au HumanoidRootPart = (-xB, zB - H, yB).
"""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

DOSSIER = Path(r"C:\Users\alice\Documents\GameRoblox\assets\persos\zoro")
ZONES = json.loads((DOSSIER / "acc_zones.json").read_text(encoding="utf-8"))
H = 3.192428
PLIS = 9  # plis du manteau, comme PLIS_MANTEAU de texture_acc_zoro.py

# tete classique : cylindre vertical aux aretes arrondies
TETE_R, TETE_HAUT, TETE_ARRONDI = 0.595, 5.435, 0.3

# attachments du corps (Roblox, relatifs au HumanoidRootPart)
ATTACHMENTS = {
	"HairAttachment": (0.0, 2.198, 0.0),
	"FaceCenterAttachment": (0.0, 1.598, 0.0),
	"FaceFrontAttachment": (0.0, 1.598, -0.6),
	"WaistCenterAttachment": (0.0, -1.0, 0.0),
	"RightGripAttachment": (1.472137, -1.02366, 0.0),
	"LeftGripAttachment": (-1.472129, -1.02366, 0.0),
}


def vers_blender(p):
	return Vector((-p[0], p[2], p[1] + H))


def vers_roblox(v):
	return [round(-v.x, 4), round(v.z - H, 4), round(v.y, 4)]


class Maillage:
	"""Sommets + faces avec UV dans une zone de l'atlas (u, v de 0 a 1, v vers le bas)."""

	def __init__(self):
		self.v = []
		self.f = []

	def pt(self, p):
		self.v.append(Vector(p))
		return len(self.v) - 1

	def face(self, idx, uvs, zone):
		u0, v0, u1, v1 = ZONES[zone]
		# marge de 3 px : pas de debordement sur la zone voisine (filtrage)
		e = 3 / 1024
		u0, v0, u1, v1 = u0 + e, v0 + e, u1 - e, v1 - e
		self.f.append((list(idx), [(u0 + u * (u1 - u0), 1 - (v0 + v * (v1 - v0))) for u, v in uvs]))

	def grille(self, lignes, zone, ferme=False, us=None, vs=None, double=False):
		"""lignes[i][j] : i de haut en bas, j dans le sens trigo vu du dessus (normales vers l'exterieur)."""
		n, m = len(lignes), len(lignes[0])
		ids = [[self.pt(p) for p in ligne] for ligne in lignes]
		vs = vs or [i / (n - 1) for i in range(n)]
		cols = m if ferme else m - 1
		us = us or [j / cols for j in range(cols + 1)]
		for i in range(n - 1):
			for j in range(cols):
				j2 = (j + 1) % m
				q = [ids[i][j], ids[i + 1][j], ids[i + 1][j2], ids[i][j2]]
				uv = [(us[j], vs[i]), (us[j], vs[i + 1]), (us[j + 1], vs[i + 1]), (us[j + 1], vs[i])]
				self.face(q, uv, zone)
				if double:
					self.face(q[::-1], uv[::-1], zone)
		return ids

	def boite(self, centre, ax, ay, az, zone):
		"""Boite orientee : ax, ay, az = demi-axes (vecteurs)."""
		c = Vector(centre)
		ids = {}
		for sx in (-1, 1):
			for sy in (-1, 1):
				for sz in (-1, 1):
					ids[sx, sy, sz] = self.pt(c + sx * Vector(ax) + sy * Vector(ay) + sz * Vector(az))
		faces = [
			[(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)],
			[(-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1)],
			[(1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1)],
			[(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)],
			[(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)],
			[(-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)],
		]
		for f in faces:
			self.face([ids[k] for k in f], [(0, 0), (1, 0), (1, 1), (0, 1)], zone)

	def objet(self, nom, origine, lisse=False):
		o = bpy.data.objects.get(nom)
		if o:
			bpy.data.meshes.remove(o.data)
		me = bpy.data.meshes.new(nom)
		org = Vector(origine)
		me.from_pydata([p - org for p in self.v], [], [f[0] for f in self.f])
		uvl = me.uv_layers.new(name="UVMap")
		for poly, (_, uvs) in zip(me.polygons, self.f):
			for li, uv in zip(poly.loop_indices, uvs):
				uvl.data[li].uv = uv
		me.materials.append(materiau())
		me.validate()
		if lisse:
			me.shade_smooth()
		o = bpy.data.objects.new(nom, me)
		o.location = org
		coll = bpy.data.collections.get("Accessoires") or bpy.data.collections.new("Accessoires")
		if coll.name not in bpy.context.scene.collection.children:
			bpy.context.scene.collection.children.link(coll)
		coll.objects.link(o)
		return o


def materiau():
	m = bpy.data.materials.get("Mat_Acc_zoro")
	if m:
		return m
	m = bpy.data.materials.new("Mat_Acc_zoro")
	m.use_nodes = True
	nt = m.node_tree
	bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
	bsdf.inputs["Roughness"].default_value = 0.8
	tex = nt.nodes.new("ShaderNodeTexImage")
	tex.image = bpy.data.images.load(str(DOSSIER / "acc_zoro.png"), check_existing=True)
	nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
	return m


def superellipse(ax, ay, phi, n=4):
	c, s = math.cos(phi), math.sin(phi)
	e = 2 / n
	return (ax * math.copysign(abs(c) ** e, c), ay * math.copysign(abs(s) ** e, s))


# ---------------------------------------------------------------- tete


def bord_bandana(phi):
	"""Hauteur du bord du bandana : bas sur le front (z 4,89), plus bas a l'arriere (4,55)."""
	return 4.725 - 0.175 * math.sin(phi) - 0.0 * math.cos(phi)


def point_tete(s, phi, d):
	"""Point de la surface de la tete decalee de d, a l'abscisse curviligne s depuis le sommet."""
	a = TETE_R - TETE_ARRONDI
	rr = TETE_ARRONDI + d
	zc = TETE_HAUT - TETE_ARRONDI
	l1, l2 = a, math.pi / 2 * rr
	if s <= l1:
		r, z = s, TETE_HAUT + d
	elif s <= l1 + l2:
		t = (s - l1) / rr
		r, z = a + rr * math.sin(t), zc + rr * math.cos(t)
	else:
		r, z = TETE_R + d, zc - (s - l1 - l2)
	return (r * math.cos(phi), r * math.sin(phi), z)


def longueur_jusqua(z_bord, d):
	a = TETE_R - TETE_ARRONDI
	return a + math.pi / 2 * (TETE_ARRONDI + d) + (TETE_HAUT - TETE_ARRONDI - z_bord)


# dome du bandana : superellipse (r / RH)^P + ((z - ZC) / RV)^P = 1 au-dessus de ZC, cylindre vertical en dessous.
# P = 2,6 : plus rond que la tete (aretes arrondies de 0,3) sans la traverser (coin de la tete a 0,88 < 1).
DOME_RH, DOME_RV, DOME_ZC, DOME_P = 0.64, 0.56, 4.98, 2.6


def point_dome(z_bord, f, phi):
	"""Point a la fraction f (0 = sommet, 1 = bord) de la longueur du profil, a l'angle phi."""
	prof = [(DOME_RH * math.sin(t) ** (2 / DOME_P), DOME_ZC + DOME_RV * math.cos(t) ** (2 / DOME_P)) for t in (math.pi / 2 * k / 40 for k in range(41))]
	prof.append((DOME_RH, z_bord))
	longueurs = [0.0]
	for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
		longueurs.append(longueurs[-1] + math.hypot(r1 - r0, z1 - z0))
	cible = f * longueurs[-1]
	for k in range(1, len(prof)):
		if longueurs[k] >= cible:
			t = (cible - longueurs[k - 1]) / max(1e-9, longueurs[k] - longueurs[k - 1])
			r = prof[k - 1][0] + (prof[k][0] - prof[k - 1][0]) * t
			z = prof[k - 1][1] + (prof[k][1] - prof[k - 1][1]) * t
			return (r * math.cos(phi), r * math.sin(phi), z)
	return (DOME_RH * math.cos(phi), DOME_RH * math.sin(phi), z_bord)


def bandana():
	m = Maillage()
	d, n_phi, n_s = 0.045, 48, 14
	# raccord des UV a l'arriere (cache par le noeud)
	phis = [math.pi / 2 + 2 * math.pi * j / n_phi for j in range(n_phi)]
	lignes = []
	for i in range(1, n_s + 1):
		lignes.append([point_dome(bord_bandana(p) + 0.06, i / n_s, p) for p in phis])
	# ourlet roule
	lignes.append([((TETE_R + d + 0.03) * math.cos(p), (TETE_R + d + 0.03) * math.sin(p), bord_bandana(p) + 0.04) for p in phis])
	lignes.append([((TETE_R + d + 0.03) * math.cos(p), (TETE_R + d + 0.03) * math.sin(p), bord_bandana(p)) for p in phis])
	lignes.append([((TETE_R + 0.005) * math.cos(p), (TETE_R + 0.005) * math.sin(p), bord_bandana(p)) for p in phis])
	vs = [0.85 * i / n_s for i in range(1, n_s + 1)] + [0.9, 0.95, 1.0]
	ids = m.grille(lignes, "bandana", ferme=True, vs=vs)
	# calotte : eventail autour du sommet
	c = m.pt((0, 0, DOME_ZC + DOME_RV))
	for j in range(n_phi):
		j2 = (j + 1) % n_phi
		m.face([c, ids[0][j], ids[0][j2]], [(0.5, 0), ((j + 0.5) / n_phi, 0.1), ((j + 1.5) / n_phi, 0.1)], "bandana")
	# noeud a l'arriere : deux boucles inclinees autour d'un noeud central, puis deux pans effiles
	zn = 4.80
	yn = TETE_R + d + 0.05
	m.boite((0, yn + 0.03, zn), (0.07, 0, 0), (0, 0.07, 0), (0, 0, 0.08), "bandana")
	for sx in (-1, 1):
		a = math.radians(22 * sx)
		m.boite((sx * 0.15, yn + 0.01, zn + 0.03), (0.10 * math.cos(a), 0, 0.10 * math.sin(a)), (0, 0.045, 0), (-0.06 * math.sin(a), 0, 0.06 * math.cos(a)), "bandana")
	for sx, ang in ((-1, 0.35), (1, 0.25)):
		haut = Vector((sx * 0.05, yn + 0.06, zn - 0.05))
		bas = haut + Vector((sx * 0.16, 0.10 + ang * 0.1, -0.42))
		larg = Vector((0.07, 0, 0))
		lignes = []
		for k in range(6):
			t = k / 5
			p = haut.lerp(bas, t) + Vector((0, 0.04 * math.sin(t * math.pi), 0))
			w = larg * (1 - 0.55 * t)
			# leger vrillage du pan
			w = w + Vector((0, 0.02 * math.sin(t * 2.5) * sx, 0))
			lignes.append([p + w if sx > 0 else p - w, p - w if sx > 0 else p + w])
		m.grille(lignes, "bandana", double=True)
	return m.objet("Acc_Bandana", vers_blender(ATTACHMENTS["HairAttachment"]), lisse=True)


def cheveux():
	"""Meches vertes en grandes lames plates et pointues, superposees, qui s'evasent sous le bandana (style anime).
	Angles phi : -90 = front, 0 = gauche du perso (oreille aux boucles : meches courtes qui remontent), 90 = nuque, 180 = droite.
	La face (|angle| <= 45 deg autour du front) reste degagee."""
	m = Maillage()
	haut = Vector((0, 0, 1))

	def lame_meche(phi, z, larg, long, chute, evase, k, ep=0.035, releve=0.0):
		n = Vector((math.cos(phi), math.sin(phi), 0))
		t = Vector((-math.sin(phi), math.cos(phi), 0))
		b = n * (TETE_R - 0.03) + haut * z
		d = (n * 0.55 - haut * chute).normalized()
		nb = d.cross(t).normalized()  # face exterieure de la lame
		jit = t * 0.06 * math.sin(k * 1.7)
		centres = [b, b + d * long * 0.5 + n * evase * 0.35 + jit * 0.4, b + d * long + n * evase + haut * releve + jit]
		sections = []
		for c, w, e in zip(centres[:2], (larg, larg * 0.72), (ep, ep * 0.7)):
			sections.append([m.pt(c + t * w + nb * e), m.pt(c - t * w + nb * e), m.pt(c - t * w * 0.9 - nb * e), m.pt(c + t * w * 0.9 - nb * e)])
		ip = m.pt(centres[2])
		ic, im = sections
		for a in range(4):
			a2 = (a + 1) % 4
			m.face([ic[a], im[a], im[a2], ic[a2]][::-1], [(a / 4, 0), (a / 4, 0.5), ((a + 1) / 4, 0.5), ((a + 1) / 4, 0)][::-1], "cheveux")
			m.face([im[a], ip, im[a2]][::-1], [(a / 4, 0.5), ((a + 0.5) / 4, 1), ((a + 1) / 4, 0.5)][::-1], "cheveux")

	rangs = [
		# (decalage sous le bord, angles, demi-largeur, longueur, chute, evasement)
		(0.02, [-40, -27, -14, 16, 29, 42, 56, 70, 84, 98, 112, 126, 140, 154, 168, 182, 196, 209, 220], 0.13, 0.19, 0.55, 0.08),
		(-0.12, [24, 38, 52, 66, 80, 94, 108, 122, 136, 150, 164, 178, 192, 206], 0.14, 0.20, 0.85, 0.05),
		(-0.25, [52, 68, 84, 100, 116, 132], 0.12, 0.15, 1.2, 0.03),
	]
	k = 0
	for dz, angles, larg, long, chute, evase in rangs:
		for deg in angles:
			phi = math.radians(deg)
			var = 1 + 0.18 * math.sin(k * 2.3)
			if abs(deg) < 20:
				# pres de l'oreille gauche : meches courtes qui remontent (degagent les boucles)
				lame_meche(phi, bord_bandana(phi) + dz, larg * 0.8, long * 0.6, -0.15, 0.10, k)
			elif dz == 0.02 and (150 <= deg <= 215 or 20 <= deg <= 45):
				# cotes : les pointes s'evasent et remontent un peu, comme sur la reference
				lame_meche(phi, bord_bandana(phi) + dz, larg, long * var, chute * 0.6, evase * 1.4, k, releve=0.06)
			else:
				lame_meche(phi, bord_bandana(phi) + dz, larg, long * var, chute * (1 + 0.2 * math.cos(k * 1.3)), evase, k)
			k += 1
	# sous-couche plaquee sur la tete (cotes et nuque) : bouche les trous entre les lames, bas en dents de scie
	degs = list(range(-44, 225, 4))
	haut_c, bas_c = [], []
	for j, deg in enumerate(degs):
		phi = math.radians(deg)
		n = Vector((math.cos(phi), math.sin(phi), 0))
		zb = bord_bandana(phi)
		if abs(deg) < 20:
			prof = 0.09  # oreille gauche : degage les boucles (haut a 4,64)
		elif deg < -30 or deg > 210:
			prof = 0.12  # vers les tempes
		else:
			prof = 0.20 + 0.10 * max(0.0, math.sin(phi))  # 0,20 sur les cotes, 0,30 dans la nuque
		prof += 0.05 * (j % 2)
		haut_c.append(n * (TETE_R + 0.012) + Vector((0, 0, zb + 0.03)))
		bas_c.append(n * (TETE_R + 0.012) + Vector((0, 0, zb - prof)))
	m.grille([haut_c, bas_c], "cheveux", us=[0.27 + 0.2 * j / (len(degs) - 1) for j in range(len(degs))], vs=[0.05, 0.6])
	# pattes aux tempes : plaquees sur la tete, longues vers le bas
	for deg in (-42, 222):
		lame_meche(math.radians(deg), bord_bandana(math.radians(deg)) - 0.02, 0.08, 0.24, 4.0, 0.02, k, ep=0.025)
		k += 1
	return m.objet("Acc_Cheveux", vers_blender(ATTACHMENTS["HairAttachment"]))


def boucles():
	"""Trois pendentifs dores a l'oreille gauche du perso (Blender +X)."""
	m = Maillage()
	x = TETE_R + 0.03
	for k, y in enumerate((-0.09, 0.0, 0.09)):
		haut, bas = Vector((x, y, 4.64)), Vector((x, y, 4.44 - 0.02 * k))
		mil = haut.lerp(bas, 0.35)
		r = 0.035
		anneau = [m.pt(mil + Vector((r * math.cos(a), r * math.sin(a), 0))) for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
		ih, ib = m.pt(haut), m.pt(bas)
		for a in range(4):
			a2 = (a + 1) % 4
			m.face([ih, anneau[a], anneau[a2]], [(0.5, 0.1), (0.2, 0.5), (0.8, 0.5)], "or")
			m.face([ib, anneau[a2], anneau[a]], [(0.5, 0.9), (0.8, 0.5), (0.2, 0.5)], "or")
	return m.objet("Acc_Boucles", vers_blender(ATTACHMENTS["FaceCenterAttachment"]))


# ---------------------------------------------------------------- taille


def haramaki():
	m = Maillage()
	n_phi = 28
	phis = [-math.pi / 2 + 2 * math.pi * j / n_phi for j in range(n_phi)]
	z_haut, z_bas, n = 2.77, 2.19, 15
	lignes, vs = [], []
	lignes.append([(*superellipse(0.975, 0.505, p), z_haut) for p in phis])
	vs.append(0.0)
	for k in range(n):
		z = z_haut - (z_haut - z_bas) * k / (n - 1)
		e = 0.045 if k % 2 else 0.028
		lignes.append([(*superellipse(1.0 + e, 0.502 + e, p), z) for p in phis])
		vs.append(k / (n - 1))
	lignes.append([(*superellipse(1.0, 0.505, p), z_bas) for p in phis])
	vs.append(1.0)
	m.grille(lignes, "haramaki", ferme=True, vs=vs)
	return m.objet("Haramaki", vers_blender(ATTACHMENTS["WaistCenterAttachment"]))


MANTEAU = [  # z, demi-largeur x, demi-profondeur y, ouverture (deg depuis l'avant), amplitude des plis
	(2.44, 1.03, 0.535, 6, 0.0),
	(2.20, 1.09, 0.59, 10, 0.012),
	(1.85, 1.18, 0.68, 13, 0.03),
	(1.40, 1.29, 0.79, 16, 0.05),
	(0.95, 1.38, 0.88, 18, 0.065),
	(0.70, 1.42, 0.92, 19, 0.07),
]


def manteau():
	"""Manteau ouvert porte a la taille, evase en jupe jusqu'aux genoux, double face."""
	m = Maillage()
	n_col = PLIS * 4
	ext, inte = [], []
	for z, ax, ay, ouv, amp in MANTEAU:
		le, li = [], []
		for j in range(n_col + 1):
			u = j / n_col
			phi = math.radians(-90 + ouv + u * (360 - 2 * ouv))
			f = 1 + amp * math.cos(2 * math.pi * PLIS * u)
			x, y = superellipse(ax * f, ay * f, phi)
			le.append((x, y, z))
			k = 1 - 0.03 / ax
			li.append((x * k, y * (1 - 0.03 / ay), z))
		ext.append(le)
		inte.append(li)
	ie = m.grille(ext, "manteau")
	ii = m.grille([l[::-1] for l in inte], "manteau_int")
	n = len(MANTEAU)
	# ourlet du bas, haut, et bords de l'ouverture
	for j in range(n_col):
		jr = n_col - j
		m.face([ie[n - 1][j], ii[n - 1][jr], ii[n - 1][jr - 1], ie[n - 1][j + 1]], [(0, 0.95), (0, 1), (1, 1), (1, 0.95)], "manteau")
		m.face([ie[0][j + 1], ii[0][jr - 1], ii[0][jr], ie[0][j]], [(0, 0), (0, 0.05), (1, 0.05), (1, 0)], "manteau")
	for i in range(n - 1):
		vi, vj = i / (n - 1), (i + 1) / (n - 1)
		# bord u = 0 (ext[.][0] <-> int[.][n_col] inverse)
		m.face([ie[i][0], ii[i][n_col], ii[i + 1][n_col], ie[i + 1][0]], [(0, vi), (0.04, vi), (0.04, vj), (0, vj)], "manteau")
		m.face([ie[i + 1][n_col], ii[i + 1][0], ii[i][0], ie[i][n_col]], [(1, vj), (0.96, vj), (0.96, vi), (1, vi)], "manteau")
	return m.objet("Manteau", vers_blender(ATTACHMENTS["WaistCenterAttachment"]))


def echarpe():
	"""Echarpe bordeaux nouee a la taille, noeud devant, un pan qui pend entre les jambes."""
	m = Maillage()
	n_phi = 28
	phis = [-math.pi / 2 + 2 * math.pi * j / n_phi for j in range(n_phi)]
	anneaux = [(2.47, 1.0, 0.505), (2.47, 1.05, 0.555), (2.34, 1.09, 0.595), (2.21, 1.12, 0.63), (2.21, 1.07, 0.58)]
	lignes = []
	for i, (z, ax, ay) in enumerate(anneaux):
		lignes.append([(*superellipse(ax * (1 + 0.012 * math.sin(6 * p + i)), ay * (1 + 0.012 * math.sin(6 * p + i)), p), z) for p in phis])
	m.grille(lignes, "echarpe", ferme=True)
	# noeud, un peu sur la gauche du perso
	m.boite((0.18, -0.66, 2.34), (0.15, -0.03, 0), (0.03, 0.08, 0), (0, 0, 0.12), "echarpe")
	# pan entre les jambes, plis alternes
	lignes = []
	for k in range(6):
		t = k / 5
		z = 2.26 - 1.20 * t
		y = -0.70 - 0.08 * t * t
		xg, xd = 0.30 + 0.04 * t, -0.10 - 0.10 * t
		row = []
		for c in range(5):
			s = c / 4
			row.append((xg + (xd - xg) * s, y - 0.035 * (c % 2), z))
		lignes.append(row)
	m.grille(lignes, "echarpe", double=True)
	return m.objet("Echarpe", vers_blender(ATTACHMENTS["WaistCenterAttachment"]))


# ---------------------------------------------------------------- sabres

# hanche droite (Blender -X) : embouchure, direction vers la pointe (arriere, bas), couleur
FOURREAUX = [
	# colles au manteau (hanche droite) sans le traverser, en faisceau (axes a 0,17 l'un de l'autre au moins)
	((-1.25, -0.62, 2.12), (-0.25, 0.80, -0.60), "blanc"),
	((-1.41, -0.56, 2.08), (-0.25, 0.84, -0.53), "rouge"),
	((-1.57, -0.50, 2.04), (-0.25, 0.88, -0.46), "noir"),
]
LONG_FOURREAU, LONG_POIGNEE = 2.15, 1.0
# epaisseur des sabres (lames, poignees, gardes, fourreaux) : x1,6 pour aller avec les blocs du gabarit
ECH_SABRE = 1.6


def repere(direction, haut=Vector((0, 0, 1))):
	"""(axe, cote, dessus) orthonormes : axe = direction, dessus = cote du dos de la lame."""
	a = Vector(direction).normalized()
	c = a.cross(haut).normalized()
	return a, c, c.cross(a).normalized()


def prisme(m, depart, axe, cote, dessus, longueur, rx, rz, zone, rangs, n=8, fermer=True, courbe=0.0):
	"""Prisme ovale le long de axe ; rangs = [(t, echelle)], u = le long, v = autour."""
	p0 = Vector(depart)
	lignes = []
	for t, ech in rangs:
		c = p0 + axe * (longueur * t) + dessus * (courbe * t * t)
		lignes.append([c + cote * (rx * ech * math.cos(2 * math.pi * k / n)) + dessus * (rz * ech * math.sin(2 * math.pi * k / n)) for k in range(n)])
	# colonnes = rangs (u le long), lignes = tour : on transpose pour la grille
	grille = [[lignes[i][k] for i in range(len(rangs))] for k in range(n)]
	ids = m.grille(grille[::-1] + [grille[-1]], zone, us=[t for t, _ in rangs], vs=[k / n for k in range(n + 1)])
	if fermer:
		for bout, i in ((0, 0), (1, len(rangs) - 1)):
			anneau = [ids[k][i] for k in range(n)]
			if bout == 0:
				anneau = anneau[::-1]
			m.face(anneau, [(0.02 if bout == 0 else 0.98, k / n) for k in range(n)], zone)
	return ids


def tsuba(m, centre, axe, cote, dessus, r=0.14 * ECH_SABRE, ep=0.035 * ECH_SABRE):
	n = 8
	c = Vector(centre)
	av = [m.pt(c - axe * ep / 2 + cote * r * math.cos(2 * math.pi * k / n + math.pi / 8) + dessus * r * math.sin(2 * math.pi * k / n + math.pi / 8)) for k in range(n)]
	ar = [m.pt(c + axe * ep / 2 + cote * r * math.cos(2 * math.pi * k / n + math.pi / 8) + dessus * r * math.sin(2 * math.pi * k / n + math.pi / 8)) for k in range(n)]
	uv = [(0.5 + 0.4 * math.cos(2 * math.pi * k / n), 0.5 + 0.4 * math.sin(2 * math.pi * k / n)) for k in range(n)]
	m.face(av, uv, "or")
	m.face(ar[::-1], uv[::-1], "or")
	for k in range(n):
		k2 = (k + 1) % n
		m.face([av[k2], av[k], ar[k], ar[k2]], [(0, 0), (1, 0), (1, 1), (0, 1)], "or")


def poignee(m, garde, axe, cote, dessus, couleur):
	"""Tsuba a garde, poignee tressee de garde vers -axe (axe = vers la pointe de la lame)."""
	tsuba(m, Vector(garde), axe, cote, dessus)
	prisme(m, Vector(garde) - axe * 0.018 * ECH_SABRE, -axe, -cote, dessus, LONG_POIGNEE, 0.055 * ECH_SABRE, 0.068 * ECH_SABRE, "poignee_" + couleur, [(0, 1), (0.5, 0.96), (0.97, 1), (1, 0.8)])


def lame(m, garde, axe, cote, dessus, longueur=2.3):
	"""Lame courbe : dos vers dessus, tranchant vers -dessus, pointe en biseau."""
	p0 = Vector(garde) + axe * 0.018 * ECH_SABRE
	n = 12
	sections = []
	for i in range(n + 1):
		t = i / n
		c = p0 + axe * (longueur * t) + dessus * (0.10 * t * t)
		h0 = 0.06 * ECH_SABRE
		h = h0 if t < 0.92 else h0 * (1 - t) / 0.08 + 0.004
		sections.append([c + dessus * h, c + cote * 0.022 * ECH_SABRE + dessus * 0.012 * ECH_SABRE, c - dessus * h * 1.05, c - cote * 0.022 * ECH_SABRE + dessus * 0.012 * ECH_SABRE])
	vs = [0.0, 0.4, 1.0, 0.4, 0.0]
	grille = [[sections[i][k % 4] for i in range(n + 1)] for k in range(5)]
	m.grille(grille, "lame", us=[i / n for i in range(n + 1)], vs=vs)
	ip = m.pt(p0 + axe * (longueur + 0.06) + dessus * (0.10 + 0.012 * ECH_SABRE))
	fin = [m.pt(p) for p in sections[-1]]
	for k in range(4):
		m.face([fin[k], fin[(k + 1) % 4], ip], [(0.98, vs[k]), (0.98, vs[k + 1]), (1, 0.5)], "lame")
	base = [m.pt(p) for p in sections[0]]
	m.face(base[::-1], [(0, 0), (0, 0.4), (0, 1), (0, 0.4)], "lame")


def fourreaux():
	m = Maillage()
	for garde, d, couleur in FOURREAUX:
		a, c, h = repere(d)
		prisme(m, garde, a, c, h, LONG_FOURREAU, 0.06 * ECH_SABRE, 0.078 * ECH_SABRE, "fourreau_" + couleur, [(0, 1), (0.03, 1), (0.3, 0.98), (0.7, 0.94), (0.97, 0.9), (1, 0.75)], courbe=0.05)
	return m.objet("Fourreaux", vers_blender(ATTACHMENTS["WaistCenterAttachment"]))


def sabres_hanche():
	m = Maillage()
	for garde, d, couleur in FOURREAUX:
		a, c, h = repere(d)
		poignee(m, Vector(garde) - a * 0.02, a, c, h, couleur)
	return m.objet("Acc_Sabres_Hanche", vers_blender(ATTACHMENTS["WaistCenterAttachment"]))


def sabre_main(nom, x, couleur, attachment):
	"""Sabre tenu dans le poing : poignee a travers la main (centre z 2,33), lame vers l'avant, dos en haut."""
	m = Maillage()
	garde = Vector((x, -0.57, 2.33))
	a, c, h = repere((0, -1, 0))
	poignee(m, garde, a, c, h, couleur)
	lame(m, garde, a, c, h)
	return m.objet(nom, vers_blender(ATTACHMENTS[attachment]))


def sabre_bouche():
	"""Poignee blanche tenue entre les dents (z 4,49), lame vers la gauche du perso (+X), tranchant vers l'avant."""
	m = Maillage()
	garde = Vector((0.45, -0.63, 4.49))
	a, c, h = repere((1, 0, 0), haut=Vector((0, 1, 0)))
	poignee(m, garde, a, c, h, "blanc")
	lame(m, garde, a, c, h)
	return m.objet("Acc_Sabre_Bouche", vers_blender(ATTACHMENTS["FaceFrontAttachment"]))


# ---------------------------------------------------------------- catalogue

ACCESSOIRES = {
	"Bandana": (bandana, "Acc_Bandana", "HairAttachment", True),
	"Cheveux": (cheveux, "Acc_Cheveux", "HairAttachment", True),
	"Boucles": (boucles, "Acc_Boucles", "FaceCenterAttachment", True),
	"Haramaki": (haramaki, "Haramaki", "WaistCenterAttachment", True),
	"Manteau": (manteau, "Manteau", "WaistCenterAttachment", True),
	"Echarpe": (echarpe, "Echarpe", "WaistCenterAttachment", True),
	"Fourreaux": (fourreaux, "Fourreaux", "WaistCenterAttachment", True),
	"Sabres_Hanche": (sabres_hanche, "Acc_Sabres_Hanche", "WaistCenterAttachment", True),
	"Sabre_Droit": (lambda: sabre_main("Acc_Sabre_Droit", -1.472, "noir", "RightGripAttachment"), "Acc_Sabre_Droit", "RightGripAttachment", False),
	"Sabre_Gauche": (lambda: sabre_main("Acc_Sabre_Gauche", 1.472, "rouge", "LeftGripAttachment"), "Acc_Sabre_Gauche", "LeftGripAttachment", False),
	"Sabre_Bouche": (sabre_bouche, "Acc_Sabre_Bouche", "FaceFrontAttachment", False),
}


def construire(cle):
	o = ACCESSOIRES[cle][0]()
	tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
	print(o.name, "triangles :", tris)
	return o


def ecrire_json():
	"""accessoires.json : attachment, decalage du centre de la boite par rapport a l'attachment (Roblox), visibilite."""
	sortie = []
	total = 0
	for cle, (_, nom, att, visible) in ACCESSOIRES.items():
		o = bpy.data.objects[nom]
		coins = [o.matrix_world @ Vector(c) for c in o.bound_box]
		centre = sum(coins, Vector()) / 8
		taille = [max(c[i] for c in coins) - min(c[i] for c in coins) for i in range(3)]
		tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
		total += tris
		pa = ATTACHMENTS[att]
		cr = vers_roblox(centre)
		sortie.append({
			"nom": nom,
			"fbx": "acc_" + nom.removeprefix("Acc_") + ".fbx",
			"attachment": att,
			"centre_boite_roblox": cr,
			"decalage_depuis_attachment": [round(cr[i] - pa[i], 4) for i in range(3)],
			"taille_roblox": [round(taille[0], 4), round(taille[2], 4), round(taille[1], 4)],
			"visible_par_defaut": visible,
			"triangles": tris,
		})
	(DOSSIER / "accessoires.json").write_text(json.dumps({"repere": "Roblox, relatif au HumanoidRootPart, pose de repos (bras le long du corps), sans rotation : le Handle doit garder l'orientation du monde", "accessoires": sortie, "triangles_total": total}, indent="\t", ensure_ascii=False), encoding="utf-8")
	print("accessoires.json :", total, "triangles")
