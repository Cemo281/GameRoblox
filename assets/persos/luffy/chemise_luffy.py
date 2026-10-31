"""Chemise rouge ouverte de luffy (v4) : 5 pieces rigides soudees a l'avatar R15 par defaut (corps sur UpperTorso,
une manche longue sur chaque UpperArm jusqu'au coude, un poignet sur chaque LowerArm jusqu'au milieu de l'avant-bras),
texture tex_chemise_luffy.png.

A lancer DANS Blender (MCP Blender), chemise_luffy.blend ouvert :
	exec(open(r"<depot>/assets/persos/luffy/chemise_luffy.py", encoding="utf-8").read())
	construire()   # pieces Vet_* (plis en relief, revers) + corps d'apercu (collection Apercu_Corps, non exportee)
	cuire()        # cuisson/ao.png et cuisson/lumiere.png (Cycles), puis lancer peindre_chemise_luffy.py (Python systeme)
	exporter()     # fbx/chemise_luffy.fbx + chemise_luffy.json, verification par reimport

Tout est construit en studs dans les reperes Roblox (x = droite du perso, y = haut, z = arriere, origine au HumanoidRootPart),
d'apres assets/persos/_rig/r15.json, puis converti en Blender (X = -x, Y = z, Z = y), comme pour nami.
construire() ecrit aussi chemise_luffy_atlas.json : zones de la texture et position en pixels des details a peindre
(bord ouvert, boutons, coutures...), lu par peindre_chemise_luffy.py.
chemise_luffy.json donne pour chaque piece sa taille et le centre de sa boite par rapport au centre de la piece R15 :
dans Studio, MeshPart.Size = taille, MeshPart.CFrame = Piece.CFrame * CFrame.new(decalage), puis Weld a la piece.
"""

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

DOSSIER = Path(r"C:\Users\alice\Documents\GameRoblox\assets\persos\luffy")
RIG = json.loads((DOSSIER.parent / "_rig" / "r15.json").read_text(encoding="utf-8"))
TEXTURE = DOSSIER / "tex_chemise_luffy.png"
T = 2048

# corps de la chemise : pans avant et dos a 0,08 du torse, qui passent par-dessus l'epaule jusqu'a la couture (z = 0)
HAUT, OURLET = 1.14, -1.32  # ourlet sous l'echarpe, en haut des cuisses
X_EXT = 0.99
Z_PAN = 0.58
R_ARC = 0.1
EPAISSEUR = 0.035
# manches (local du bras : lx vers l'exterieur, ly vers le haut depuis le centre de UpperArm ; coude a ly = -0,355)
M_HAUT, M_BAS = 0.66, -0.62  # jusqu'au bas de UpperArm, le poignet prend le relais
M_CX, M_A0, M_B0, M_EVASE_A, M_EVASE_B = 0.03, 0.575, 0.585, 0.02, 0.02
M_INT = -0.53
# poignets (local de LowerArm) : entrent dans le bas de la manche, revers de P_REVERS a P_BAS (milieu de l'avant-bras visible)
P_HAUT, P_REVERS, P_BAS = 0.10, -0.14, -0.26
P_A, P_EP_REVERS = 0.545, 0.022

ATLAS = {
	"devant": ((0, 0, 1024, 1024), (-1.1, 1.1), (1.75, -1.4)),  # (x), (longueur deroulee : y sur le devant, puis l'epaule)
	"dos": ((1024, 0, 1024, 1024), (-1.1, 1.1), (1.75, -1.4)),
	"manche": ((0, 1024, 1024, 640), (0.0, 1.0), (0.74, -0.7)),  # (tour du bras, depuis l'interieur), (ly)
	"poignet": ((1024, 1024, 1024, 256), (0.0, 1.0), (0.14, -0.3)),  # (tour de l'avant-bras), (ly de LowerArm)
	"epaule": ((0, 1664, 384, 384), (-0.75, 0.75), (-0.75, 0.75)),  # (lx), (lz)
	"revers": ((1024, 1280, 512, 256), (-0.7, 0.7), (1.05, 0.5)),  # (x), (y)
	"interieur": ((1536, 1280, 512, 256), (0, 1), (0, 1)),
	"bord": ((1024, 1536, 512, 512), (0, 1), (0, 1)),
}

PLIS_DEVANT = [  # (|x|, y) debut, fin, amplitude, largeur
	((0.82, 0.95), (0.64, -0.75), 0.035, 0.06),
	((0.95, 0.70), (0.86, -1.28), 0.028, 0.05),
	((0.68, 0.75), (0.57, -0.45), -0.02, 0.045),
	((0.60, 0.20), (0.60, -1.28), 0.022, 0.05),
	((0.90, 0.10), (0.70, -0.60), -0.015, 0.04),
	((0.72, -0.40), (0.80, -1.28), -0.018, 0.04),
]
PLIS_DOS = [
	((0.02, 0.85), (0.08, -1.28), 0.03, 0.06),
	((0.55, 0.80), (0.74, -1.28), 0.03, 0.06),
	((-0.50, 0.80), (-0.72, -1.28), 0.03, 0.06),
	((0.30, 0.60), (0.40, -1.28), -0.02, 0.05),
	((-0.28, 0.60), (-0.38, -1.28), -0.02, 0.05),
]
BOUTONS = [0.40, -0.20, -0.80]


def ouverture(y):
	"""Demi-largeur de l'ouverture du devant a la hauteur y : 0,30 au col, 0,50 a l'ourlet (torse bien visible)."""
	return 0.30 + (HAUT - min(y, HAUT)) / (HAUT - OURLET) * 0.2


def lisse(a, b, t):
	t = min(max((t - a) / (b - a), 0.0), 1.0)
	return t * t * (3 - 2 * t)


def uv(zone, a, b):
	(x0, y0, w, h), (a0, a1), (b0, b1) = ATLAS[zone]
	return ((x0 + (a - a0) / (a1 - a0) * w) / T, 1 - (y0 + (b - b0) / (b1 - b0) * h) / T)


def px(zone, a, b):
	u, v = uv(zone, a, b)
	return [round(u * T, 1), round((1 - v) * T, 1)]


def centre_zone(zone):
	(x0, y0, w, h), _, _ = ATLAS[zone]
	return ((x0 + w / 2) / T, 1 - (y0 + h / 2) / T)


def vb(r):
	return Vector((-r[0], r[2], r[1]))


def dist_segment(p, a, b):
	ax, ay = b[0] - a[0], b[1] - a[1]
	t = max(0.0, min(1.0, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / (ax * ax + ay * ay)))
	return math.hypot(p[0] - a[0] - t * ax, p[1] - a[1] - t * ay)


def champ(plis, x, y):
	return sum(amp * math.exp(-(dist_segment((x, y), a, b) / lg) ** 2) for a, b, amp, lg in plis)


# --- corps -------------------------------------------------------------------------------------------------------------
ARC = math.pi / 2 * R_ARC
B_ARC = HAUT - R_ARC
B_MAX = B_ARC + ARC + (Z_PAN - R_ARC)


def profil(b, zs):
	"""Longueur deroulee b -> (y, z, normale y, normale z) sur un pan (zs = -1 devant, +1 dos)."""
	if b <= B_ARC:
		return b, zs * Z_PAN, 0.0, float(zs)
	t = b - B_ARC
	if t <= ARC:
		phi = t / R_ARC
		return B_ARC + R_ARC * math.sin(phi), zs * (Z_PAN - R_ARC + R_ARC * math.cos(phi)), math.sin(phi), zs * math.cos(phi)
	return HAUT, zs * max(Z_PAN - R_ARC - (t - ARC), 0.0), 1.0, 0.0


def rangs():
	return [OURLET + (B_ARC - OURLET) * i / 30 for i in range(31)] + [B_ARC + ARC * i / 3 for i in (1, 2, 3)] + [
		B_ARC + ARC + (Z_PAN - R_ARC) * i / 3 for i in (1, 2, 3)]


def point_pan(x, b, zs, s=1):
	"""Point du pan (devant si zs = -1) a l'abscisse x : plis, renflement, ourlet evase et ondule."""
	y, z, ny, nz = profil(b, zs)
	poids = 1 - lisse(B_ARC - 0.2, B_ARC, b)
	if zs < 0:
		ax = abs(x) + 0.03 * s
		w = ouverture(b)
		u = (abs(x) - w) / (X_EXT - w)
		d = champ(PLIS_DEVANT, ax, y) + 0.02 * math.exp(-((abs(x) - w) / 0.04) ** 2) + 0.02 * math.sin(math.pi * min(max(u, 0), 1))
	else:
		d = champ(PLIS_DOS, x, y) + 0.015 * math.exp(-((abs(x) - 0.45) / 0.25) ** 2) * lisse(0.0, 0.8, y)
	evase = lisse(OURLET + 0.35, OURLET, b)
	d = d * poids + 0.05 * evase ** 2
	if b <= OURLET + 1e-6:
		y += 0.02 * math.sin(9 * x + (1.3 if zs < 0 else 0.4))
	return (x, y + d * ny, z + d * nz)


class Maillage:
	"""Grilles de quads (points Roblox + UV par sommet), orientees vers l'exterieur, puis objet Blender."""

	def __init__(self, nom):
		self.nom = nom
		self.bm = bmesh.new()
		self.uv = self.bm.loops.layers.uv.new("UVMap")

	def grille(self, pts, uvs, exterieur, fermer_u=False, zone="manche"):
		"""pts[i][j], uvs[i][j] ; exterieur(point) -> direction attendue de la normale."""
		ni, nj = len(pts), len(pts[0])
		vs = [[self.bm.verts.new(vb(pts[i][j])) for j in range(nj)] for i in range(ni)]
		faces = []
		for i in range(ni - 1 if not fermer_u else ni):
			i2 = (i + 1) % ni
			for j in range(nj - 1):
				coins = [(i, j), (i2, j), (i2, j + 1), (i, j + 1)]
				f = self.bm.faces.new([vs[a][b] for a, b in coins])
				for l, (a, b) in zip(f.loops, coins):
					uu = uvs[a][b]
					if fermer_u and i2 == 0 and a == 0:
						uu = (uu[0] + (ATLAS[zone][0][2] / T), uu[1])  # couture : fin du tour a droite de la zone
					l[self.uv].uv = uu
				faces.append(f)
		self._orienter(faces, exterieur)
		return vs

	def face(self, pts, uvs, exterieur):
		vs = [self.bm.verts.new(vb(p)) for p in pts]
		f = self.bm.faces.new(vs)
		for l, uu in zip(f.loops, uvs):
			l[self.uv].uv = uu
		self._orienter([f], exterieur)

	def _orienter(self, faces, exterieur):
		somme = 0.0
		for f in faces:
			f.normal_update()
			c = f.calc_center_median()
			r = Vector((-c.x, c.z, c.y))
			e = vb(exterieur(r))
			somme += f.normal.dot(e) * f.calc_area()
		if somme < 0:
			for f in faces:
				uvs = {l.vert: l[self.uv].uv.copy() for l in f.loops}
				f.normal_flip()
				for l in f.loops:
					l[self.uv].uv = uvs[l.vert]

	def objet(self, epaisseur, materiaux):
		bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-4)
		me = bpy.data.meshes.new(self.nom)
		self.bm.to_mesh(me)
		self.bm.free()
		for m in materiaux:
			me.materials.append(m)
		o = bpy.data.objects.new("Base_" + self.nom, me)
		bpy.context.scene.collection.objects.link(o)
		m = o.modifiers.new("Epaisseur", "SOLIDIFY")
		m.thickness = epaisseur
		m.offset = -1
		m.use_rim = True
		m.use_even_offset = True
		m.material_offset = 1
		m.material_offset_rim = 2
		return o


def ext_torse(r):
	return (r[0], r[1] - min(max(r[1], OURLET), HAUT - 0.3), r[2])


def corps_chemise(materiaux):
	m = Maillage("Vet_UpperTorso_Chemise")
	bs = rangs()
	for s in (1, -1):
		pts, uvs = [], []
		for i in range(7):
			u = i / 6
			col_p, col_uv = [], []
			for b in bs:
				w = ouverture(b)
				x = s * (w + (X_EXT - w) * u)
				col_p.append(point_pan(x, b, -1, s))
				col_uv.append(uv("devant", x, b))
			pts.append(col_p)
			uvs.append(col_uv)
		m.grille(pts, uvs, ext_torse)
	pts, uvs = [], []
	for i in range(17):
		x = -X_EXT + 2 * X_EXT * i / 16
		pts.append([point_pan(x, b, 1) for b in bs])
		uvs.append([uv("dos", x, b) for b in bs])
	m.grille(pts, uvs, ext_torse)
	# revers : rabats poses sur le haut des pans, le long du bord ouvert
	for s in (1, -1):
		pts, uvs = [], []
		for i in range(3):
			col_p, col_uv = [], []
			for j in range(7):
				y = 1.0 - 0.45 * j / 6
				w = ouverture(y)
				larg = max(0.2 * ((y - 0.55) / 0.45) ** 0.8, 0.012)
				x = s * (w + larg * i / 2)
				p = point_pan(x, y, -1, s)
				col_p.append((p[0], p[1], p[2] - 0.022))
				col_uv.append(uv("revers", x, y))
			pts.append(col_p)
			uvs.append(col_uv)
		m.grille(pts, uvs, lambda r: (0, 0, -1))
	return m.objet(EPAISSEUR, materiaux)


# --- manches -----------------------------------------------------------------------------------------------------------
def rectangle_arrondi(u, a, b, r):
	"""Point du contour d'un rectangle arrondi (demi-tailles a, b, rayon r), u dans [0, 1[ depuis le milieu du cote -x,
	parcouru a pas constant : (x, z, normale x, normale z)."""
	cotes = [2 * (b - r), 2 * (a - r)] * 2
	quart = math.pi / 2 * r
	total = sum(cotes) + 4 * quart
	d = (u * total + (b - r)) % total  # depart au milieu du cote -x
	coins = [(-a + r, -b + r), (a - r, -b + r), (a - r, b - r), (-a + r, b - r)]
	angles = [math.pi, 1.5 * math.pi, 0.0, 0.5 * math.pi]
	debuts = [(-a, b - r, 0, -1), (-a + r, -b, 1, 0), (a, -b + r, 0, 1), (a - r, b, -1, 0)]
	normales = [(-1, 0), (0, -1), (1, 0), (0, 1)]
	for k in range(4):
		if d <= cotes[k]:
			x0, z0, dx, dz = debuts[k]
			return x0 + dx * d, z0 + dz * d, normales[k][0], normales[k][1]
		d -= cotes[k]
		if d <= quart:
			phi = angles[k] + d / r
			cx, cz = coins[k]
			return cx + r * math.cos(phi), cz + r * math.sin(phi), math.cos(phi), math.sin(phi)
		d -= quart
	return -a, 0.0, -1, 0


def section(u, t):
	return rectangle_arrondi(u, M_A0 + M_EVASE_A * t, M_B0 + M_EVASE_B * t, 0.2 + 0.05 * t)


def point_manche(u, t):
	x, z, nx, nz = section(u, t)
	theta = 2 * math.pi * u
	d = (0.028 * math.sin(5 * theta + 3 * t) * t ** 0.7 + 0.018 * math.sin(9 * theta - 2 + 5 * t) * t
		+ 0.02 * math.sin(7 * theta + 1.3) * max(0.0, t - 0.6) / 0.4)
	lx = max(M_CX + x + d * nx, M_INT)
	lz = z + d * nz
	ly = M_HAUT + (M_BAS - M_HAUT) * t
	if t >= 1:
		ly += 0.015 * math.sin(4 * theta + 0.5)
	return lx, ly, lz


def manche(cote, materiaux):
	s = 1 if cote == "Right" else -1
	cx, cy, cz = RIG["pieces"][cote + "UpperArm"]["cframe_hrp"][:3]

	def P(lx, ly, lz):
		return (cx + s * lx, cy + ly, cz + lz)

	m = Maillage("Vet_%sUpperArm_Manche" % cote)
	nt, nv = 28, 10
	pts, uvs = [], []
	for i in range(nt):
		u = i / nt
		col_p, col_uv = [], []
		for j in range(nv + 1):
			t = j / nv
			lx, ly, lz = point_manche(u, t)
			col_p.append(P(lx, ly, lz))
			col_uv.append(uv("manche", u, M_HAUT + (M_BAS - M_HAUT) * t))
		pts.append(col_p)
		uvs.append(col_uv)
	m.grille(pts, uvs, lambda r: (r[0] - cx - s * M_CX, 0, r[2] - cz), fermer_u=True)
	# calotte de l'epaule : anneaux qui se resserrent, fermes par un polygone
	anneaux = [(1.0, 0.0), (0.82, 0.06), (0.5, 0.1), (0.2, 0.115)]
	pts, uvs = [], []
	for i in range(nt):
		x, z, _, _ = section(i / nt, 0)
		col_p, col_uv = [], []
		for k, dy in anneaux:
			lx = max(M_CX + x * k, M_INT)
			col_p.append(P(lx, M_HAUT + dy, z * k))
			col_uv.append(uv("epaule", lx, z * k))
		pts.append(col_p)
		uvs.append(col_uv)
	pts.append(pts[0])
	uvs.append(uvs[0])
	m.grille(pts, uvs, lambda r: (0, 1, 0))
	dernier = [pts[i][-1] for i in range(nt)]
	m.face(dernier, [uvs[i][-1] for i in range(nt)], lambda r: (0, 1, 0))
	return m.objet(0.03, materiaux)


def point_poignet(u, ly, revers):
	"""Point du poignet a la hauteur ly (local de LowerArm) : tissu fronce au-dessus du revers, revers lisse et plus large."""
	x, z, nx, nz = rectangle_arrondi(u, P_A, P_A, 0.2)
	theta = 2 * math.pi * u
	if revers:
		d = P_EP_REVERS + (0.006 * math.sin(4 * theta + 0.5) if ly <= P_BAS + 1e-6 else 0.0)
	else:
		t = (P_HAUT - ly) / (P_HAUT - P_REVERS)
		d = 0.014 * math.sin(6 * theta + 4 * t) * math.sin(math.pi * t) + 0.008 * math.sin(11 * theta - 1)
	return max(x + d * nx, M_INT), ly, z + d * nz


def poignet(cote, materiaux):
	s = 1 if cote == "Right" else -1
	cx, cy, cz = RIG["pieces"][cote + "LowerArm"]["cframe_hrp"][:3]
	m = Maillage("Vet_%sLowerArm_Poignet" % cote)
	nt = 28
	# rangs : tissu fronce, puis marche du revers (un peu plus bas et plus large), revers
	rangs_p = [(P_HAUT + (P_REVERS - P_HAUT) * j / 5, False) for j in range(6)]
	rangs_p += [(P_REVERS - 0.012, True), ((P_REVERS + P_BAS) / 2, True), (P_BAS, True)]
	pts, uvs = [], []
	for i in range(nt):
		u = i / nt
		col_p, col_uv = [], []
		for ly, revers in rangs_p:
			lx, y, lz = point_poignet(u, ly, revers)
			col_p.append((cx + s * lx, cy + y, cz + lz))
			col_uv.append(uv("poignet", u, ly))
		pts.append(col_p)
		uvs.append(col_uv)
	m.grille(pts, uvs, lambda r: (r[0] - cx, 0, r[2] - cz), fermer_u=True, zone="poignet")
	return m.objet(0.025, materiaux)


# --- materiaux, apercu, details ----------------------------------------------------------------------------------------
def materiau(nom, image=None, couleur=(0.6, 0.1, 0.1, 1)):
	mat = bpy.data.materials.get(nom) or bpy.data.materials.new(nom)
	mat.use_nodes = True
	nt = mat.node_tree
	bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
	bsdf.inputs["Roughness"].default_value = 0.8
	if image is None:
		bsdf.inputs["Base Color"].default_value = couleur
		return mat
	tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and n.name != "Cuisson"), None) or nt.nodes.new("ShaderNodeTexImage")
	img = bpy.data.images.get(image.name)
	if img:
		img.reload()
	elif image.exists():
		img = bpy.data.images.load(str(image))
	if img:
		tex.image = img
		nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
	return mat


def corps_apercu():
	"""Boites des 15 pieces R15 (hors HRP) a leur place, couleur peau : pour regarder la chemise portee."""
	col = bpy.data.collections.get("Apercu_Corps") or bpy.data.collections.new("Apercu_Corps")
	if col.name not in bpy.context.scene.collection.children:
		bpy.context.scene.collection.children.link(col)
	peau = materiau("Mat_Peau", couleur=(0.81, 0.46, 0.27, 1))
	for nom, p in RIG["pieces"].items():
		if nom == "HumanoidRootPart":
			continue
		bm = bmesh.new()
		bmesh.ops.create_cube(bm, size=1)
		me = bpy.data.meshes.new("Corps_" + nom)
		bm.to_mesh(me)
		bm.free()
		o = bpy.data.objects.new("Corps_" + nom, me)
		t = p["taille"]
		o.scale = (t[0], t[2], t[1])
		o.location = vb(p["cframe_hrp"][:3])
		o.data.materials.append(peau)
		col.objects.link(o)


def finaliser(base, mat):
	"""Applique l'epaisseur ; faces interieures et tranches -> un point des zones interieur / bord ; un seul materiau."""
	dg = bpy.context.evaluated_depsgraph_get()
	me = bpy.data.meshes.new_from_object(base.evaluated_get(dg))
	me.transform(base.matrix_world)
	couche = me.uv_layers.active.data
	pts = {1: centre_zone("interieur"), 2: centre_zone("bord")}
	for p in me.polygons:
		if p.material_index in pts:
			for li in p.loop_indices:
				couche[li].uv = pts[p.material_index]
		p.material_index = 0
	me.materials.clear()
	me.materials.append(mat)
	nom = base.name[len("Base_") :]
	me.name = nom
	o = bpy.data.objects.new(nom, me)
	bpy.context.scene.collection.objects.link(o)
	base.hide_viewport = base.hide_render = True
	return o


def details():
	"""Position en pixels des details peints par peindre_chemise_luffy.py."""
	ys = [OURLET + (HAUT - OURLET) * i / 60 for i in range(61)]
	d = {"taille": T, "atlas": ATLAS, "echelle_devant": ATLAS["devant"][0][2] / 2.2, "plis_devant": PLIS_DEVANT, "plis_dos": PLIS_DOS,
		"constantes": {"HAUT": HAUT, "OURLET": OURLET, "B_ARC": B_ARC, "B_MAX": B_MAX, "M_HAUT": M_HAUT, "M_BAS": M_BAS,
		"P_HAUT": P_HAUT, "P_REVERS": P_REVERS, "P_BAS": P_BAS}}
	d["bord_ouvert"] = [[px("devant", s * ouverture(y), y) for y in ys] for s in (1, -1)]
	d["parementure"] = [[px("devant", s * ouverture(y), y) for y in ys] + [px("devant", s * (ouverture(y) + 0.07), y) for y in reversed(ys)] for s in (1, -1)]
	d["boutons"] = [px("devant", ouverture(y) + 0.15, y) for y in BOUTONS]
	d["boutonnieres"] = [px("devant", -(ouverture(y) + 0.14), y) for y in BOUTONS]
	d["rayon_bouton"] = 0.058 * d["echelle_devant"]
	d["ourlets"] = [[px(z, -1.1, OURLET + 0.05), px(z, 1.1, OURLET + 0.05)] for z in ("devant", "dos")]
	d["coutures_epaule"] = [[px(z, -1.1, B_MAX - 0.01), px(z, 1.1, B_MAX - 0.01)] for z in ("devant", "dos")]
	d["empiecement_dos"] = [px("dos", -1.1, 0.86), px("dos", 1.1, 0.86)]
	d["ourlet_poignet"] = [px("poignet", 0, P_BAS + 0.035), px("poignet", 1, P_BAS + 0.035)]
	d["bord_poignet"] = [px("poignet", 0, P_BAS), px("poignet", 1, P_BAS)]
	d["haut_revers"] = [px("poignet", 0, P_REVERS - 0.014), px("poignet", 1, P_REVERS - 0.014)]
	revers = []
	for s in (1, -1):
		bord, ext = [], []
		for j in range(13):
			y = 1.0 - 0.45 * j / 12
			w = ouverture(y)
			larg = max(0.2 * ((y - 0.55) / 0.45) ** 0.8, 0.012)
			bord.append(px("revers", s * w, y))
			ext.append(px("revers", s * (w + larg), y))
		revers.append(bord + list(reversed(ext)))
	d["revers"] = revers
	return d


def construire():
	for o in list(bpy.data.objects):
		if o.name.startswith(("Vet_", "Base_Vet_", "Corps_")):
			bpy.data.objects.remove(o, do_unlink=True)
	mat = materiau("Mat_Chemise_Luffy", TEXTURE)
	materiaux = [mat, materiau("Mat_Chemise_Interieur", couleur=(0.35, 0.05, 0.05, 1)), materiau("Mat_Chemise_Bord", couleur=(0.2, 0.03, 0.03, 1))]
	bases = [corps_chemise(materiaux), manche("Right", materiaux), manche("Left", materiaux), poignet("Right", materiaux), poignet("Left", materiaux)]
	objets = [finaliser(b, mat) for b in bases]
	for o in objets:
		for p in o.data.polygons:
			p.use_smooth = True
	corps_apercu()
	(DOSSIER / "chemise_luffy_atlas.json").write_text(json.dumps(details()), encoding="utf-8")
	for o in objets:
		print(o.name, [round(v, 3) for v in o.dimensions], sum(len(p.vertices) - 2 for p in o.data.polygons), "triangles")
	return objets


def cuire(echantillons=48):
	"""Occlusion ambiante et lumiere (soleil de face, en hauteur) cuites dans cuisson/ao.png et cuisson/lumiere.png.
	Seuls le corps, la manche et le poignet droits sont cuits : ceux de gauche partagent les UV de droite."""
	sc = bpy.context.scene
	try:
		sc.render.engine = "CYCLES"
	except TypeError as e:
		print(e)
	sc.cycles.samples = echantillons
	soleil = bpy.data.objects.get("Soleil_Cuisson")
	if soleil is None:
		soleil = bpy.data.objects.new("Soleil_Cuisson", bpy.data.lights.new("Soleil_Cuisson", "SUN"))
		sc.collection.objects.link(soleil)
	soleil.data.energy = 3.0
	soleil.data.angle = math.radians(25)
	direction = Vector((0.15, 0.7, -1.0)).normalized()  # vers l'arriere et le bas : la lumiere vient de face, d'en haut
	soleil.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
	if sc.world is None:
		sc.world = bpy.data.worlds.new("Monde")
	sc.world.use_nodes = True
	fond = next(n for n in sc.world.node_tree.nodes if n.type == "BACKGROUND")
	fond.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1)
	fond.inputs["Strength"].default_value = 0.6
	cibles = [bpy.data.objects[n] for n in ("Vet_UpperTorso_Chemise", "Vet_RightUpperArm_Manche", "Vet_RightLowerArm_Poignet")]
	mat = bpy.data.materials["Mat_Chemise_Luffy"]
	nt = mat.node_tree
	noeud = nt.nodes.get("Cuisson") or nt.nodes.new("ShaderNodeTexImage")
	noeud.name = "Cuisson"
	(DOSSIER / "cuisson").mkdir(exist_ok=True)
	res = {}
	for nom, type_, filtre in (("ao", "AO", None), ("lumiere", "DIFFUSE", {"DIRECT", "INDIRECT"})):
		img = bpy.data.images.get("cuisson_" + nom) or bpy.data.images.new("cuisson_" + nom, T, T, alpha=False)
		img.generated_color = (0, 0, 0, 1)
		noeud.image = img
		nt.nodes.active = noeud
		for o in bpy.context.view_layer.objects:
			o.select_set(o in cibles)
		bpy.context.view_layer.objects.active = cibles[0]
		args = {"type": type_, "margin": 12}
		if filtre:
			args["pass_filter"] = filtre
		with bpy.context.temp_override(selected_objects=cibles, selected_editable_objects=cibles, active_object=cibles[0], object=cibles[0]):
			bpy.ops.object.bake(**args)
		chemin = DOSSIER / "cuisson" / (nom + ".png")
		img.filepath_raw = str(chemin)
		img.file_format = "PNG"
		img.save()
		res[nom] = str(chemin)
	tex = next(n for n in nt.nodes if n.type == "TEX_IMAGE" and n.name != "Cuisson")
	nt.nodes.active = tex
	print(res)
	return res


PIECES = {"Vet_UpperTorso_Chemise": "UpperTorso", "Vet_RightUpperArm_Manche": "RightUpperArm", "Vet_LeftUpperArm_Manche": "LeftUpperArm",
	"Vet_RightLowerArm_Poignet": "RightLowerArm", "Vet_LeftLowerArm_Poignet": "LeftLowerArm"}


def exporter():
	materiau("Mat_Chemise_Luffy", TEXTURE)
	infos = {}
	copies = []
	for nom, piece in PIECES.items():
		src = bpy.data.objects[nom]
		me = src.data.copy()
		me.transform(src.matrix_world)
		ps = [v.co for v in me.vertices]
		mn = Vector((min(p.x for p in ps), min(p.y for p in ps), min(p.z for p in ps)))
		mx = Vector((max(p.x for p in ps), max(p.y for p in ps), max(p.z for p in ps)))
		centre = (mn + mx) / 2
		me.transform(Matrix.Translation(-centre))
		src.name = nom + "__src"
		o = bpy.data.objects.new(nom, me)
		bpy.context.scene.collection.objects.link(o)
		o.location = centre
		taille = mx - mn
		ecart = centre - vb(RIG["pieces"][piece]["cframe_hrp"][:3])
		infos[nom] = {
			"piece": piece,
			"taille": [round(taille.x, 4), round(taille.z, 4), round(taille.y, 4)],
			"decalage": [round(-ecart.x, 4), round(ecart.z, 4), round(ecart.y, 4)],
			"triangles": sum(len(p.vertices) - 2 for p in me.polygons),
		}
		copies.append((o, src))
	(DOSSIER / "fbx").mkdir(exist_ok=True)
	chemin = DOSSIER / "fbx" / "chemise_luffy.fbx"
	for o in bpy.context.view_layer.objects:
		o.select_set(any(o is c for c, _ in copies))
	bpy.context.view_layer.objects.active = copies[0][0]
	bpy.ops.export_scene.fbx(
		filepath=str(chemin), use_selection=True, object_types={"MESH"}, axis_forward="-Z", axis_up="Y",
		apply_scale_options="FBX_SCALE_ALL", path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE", use_mesh_modifiers=True,
	)
	(DOSSIER / "chemise_luffy.json").write_text(json.dumps(infos, indent="\t"), encoding="utf-8")
	for o, src in copies:
		bpy.data.objects.remove(o, do_unlink=True)
		src.name = src.name[: -len("__src")]
	print("chemise_luffy.fbx : %d triangles" % sum(v["triangles"] for v in infos.values()))
	print(json.dumps(infos))
	return verifier(chemin, infos)


def verifier(chemin, infos):
	sc_avant = bpy.context.window.scene
	sc = bpy.data.scenes.new("Verif_FBX")
	bpy.context.window.scene = sc
	avant = set(bpy.data.objects)
	bpy.ops.import_scene.fbx(filepath=str(chemin))
	res = []
	for o in set(bpy.data.objects) - avant:
		if o.type != "MESH":
			continue
		mat = o.data.materials[0] if o.data.materials else None
		tex = mat and mat.use_nodes and next((n.image.name for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
		a = infos.get(o.name.split(".")[0])
		res.append("%s dims %s attendu %s tex %s uv %d" % (o.name, [round(d, 3) for d in o.dimensions], a and a["taille"], tex, len(o.data.uv_layers)))
	for o in set(bpy.data.objects) - avant:
		bpy.data.objects.remove(o, do_unlink=True)
	bpy.context.window.scene = sc_avant
	bpy.data.scenes.remove(sc)
	print("\n".join(res))
	return res
