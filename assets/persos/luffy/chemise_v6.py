"""Chemise rouge ouverte de luffy, v6 : refaite de zero sur le rig R15 (chemise_rig15.blend), d'apres la reference
« chemise ample, manches evasees effilochees, ombrage peint doux ».

A lancer DANS Blender (MCP Blender), chemise_rig15.blend ouvert :
	exec(open(r"<depot>/assets/persos/luffy/chemise_v6.py", encoding="utf-8").read())
	construire()   # Chemise_Torse / Chemise_MancheD / Chemise_MancheG (copies des pieces du rig : suivent leurs os)
	cuire()        # cuisson_v6/ao.png et cuisson_v6/lumiere.png (Cycles, epaisseur coupee pendant la cuisson)
	peindre()      # tex_chemise_v6.png (numpy dans Blender)

Reperes : monde Blender du rig, Z en haut, l'avant du perso est +Y (visage Rig22 en +Y), unites en studs.
Le torse est construit en coordonnees monde puis ramene dans le repere local de UpperTorso ; chaque manche est construite
dans le repere de sa piece UpperArm (axes locaux les plus proches de X, Y, Z monde).
"""

import math
import random
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector

DOSSIER = Path(r"C:\Users\alice\Documents\GameRoblox\assets\persos\luffy")
T = 2048
TEXTURE = DOSSIER / "tex_chemise_v6.png"
CUISSON = DOSSIER / "cuisson_v6"

# torse (monde)
ZB, ZT, RR = 2.17, 4.34, 0.1  # bas (sous le LowerTorso), haut, arrondi des epaules
BANDE_T = 0.35  # hauteur sur laquelle le bas ondule
R_COIN = 0.14
COU = (0.46, 0.34, 0.14)  # demi-tailles et rayon de l'encolure
NU_T = 100
# manches (repere du bras : x vers l'exterieur, y vers l'avant, z le long du bras)
M_BAS, M_HAUT, M_RR = -0.12, 0.06, 0.1  # bas : 0,12 sous le bas du bras ; haut : 0,06 au-dessus du haut
BANDE_M = 0.42
NU_M = 120
EPAISSEUR = 0.035

ZONES = {"torse": (0, 0, 2048, 1024), "manche_d": (0, 1024, 1024, 768), "manche_g": (1024, 1024, 1024, 768), "revers": (0, 1792, 512, 256)}
PIECES = {"Chemise_Torse": "UpperTorso", "Chemise_MancheD": "RightUpperArm", "Chemise_MancheG": "LeftUpperArm"}


def lisse(a, b, t):
	t = min(max((t - a) / (b - a), 0.0), 1.0)
	return t * t * (3 - 2 * t)


def W(z):
	return 1.03 + 0.035 * lisse(3.0, ZB, z)


def D(z):
	return 0.56 + 0.04 * lisse(3.0, ZB, z)


def OUV(z):
	"""Demi-largeur de l'ouverture du devant : 0,26 en haut, 0,44 en bas."""
	return 0.26 + 0.18 * lisse(ZT, ZB, z)


# --- contours --------------------------------------------------------------------------------------------------------
def chemin(u, hx, hy, r, o=None):
	"""Point, normale et longueur totale du contour d'un rectangle arrondi (demi-tailles hx, hy, rayon r).
	o = None : contour ferme, depart au milieu du cote -x. Sinon contour ouvert sur le devant (+y) entre -o et +o,
	depart en (o, hy) vers +x."""
	if o is None:
		segs = [("l", (-hx, 0), (-hx, -(hy - r)), (-1, 0)), ("a", (-(hx - r), -(hy - r)), math.pi, 1.5 * math.pi),
			("l", (-(hx - r), -hy), (hx - r, -hy), (0, -1)), ("a", (hx - r, -(hy - r)), 1.5 * math.pi, 2 * math.pi),
			("l", (hx, -(hy - r)), (hx, hy - r), (1, 0)), ("a", (hx - r, hy - r), 0.0, 0.5 * math.pi),
			("l", (hx - r, hy), (-(hx - r), hy), (0, 1)), ("a", (-(hx - r), hy - r), 0.5 * math.pi, math.pi),
			("l", (-hx, hy - r), (-hx, 0), (-1, 0))]
	else:
		segs = [("l", (o, hy), (hx - r, hy), (0, 1)), ("a", (hx - r, hy - r), 0.5 * math.pi, 0.0),
			("l", (hx, hy - r), (hx, -(hy - r)), (1, 0)), ("a", (hx - r, -(hy - r)), 0.0, -0.5 * math.pi),
			("l", (hx - r, -hy), (-(hx - r), -hy), (0, -1)), ("a", (-(hx - r), -(hy - r)), -0.5 * math.pi, -math.pi),
			("l", (-hx, -(hy - r)), (-hx, hy - r), (-1, 0)), ("a", (-(hx - r), hy - r), -math.pi, -1.5 * math.pi),
			("l", (-(hx - r), hy), (-o, hy), (0, 1))]
	longueurs = [math.dist(s[1], s[2]) if s[0] == "l" else abs(s[3] - s[2]) * r for s in segs]
	total = sum(longueurs)
	d = u * total
	for s, L in zip(segs, longueurs):
		if d <= L + 1e-12 or s is segs[-1]:
			t = min(d / L, 1.0) if L > 0 else 0.0
			if s[0] == "l":
				(x0, y0), (x1, y1), n = s[1], s[2], s[3]
				return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, n[0], n[1], total
			(cx, cy), a0, a1 = s[1], s[2], s[3]
			a = a0 + (a1 - a0) * t
			return cx + r * math.cos(a), cy + r * math.sin(a), math.cos(a), math.sin(a), total
		d -= L
	raise ValueError(u)


# --- bas effiloche et plis -------------------------------------------------------------------------------------------
def ondes(longueur, graine, larg, prof, ferme, n_dech=0, larg_d=(0.07, 0.12), prof_d=(0.15, 0.24)):
	"""Bord ondule a intervalles irreguliers : vagues arrondies (1 - cos) et quelques dechirures etroites en U.
	Renvoie f(s) -> hauteur dont le bord remonte (0 = bord d'origine)."""
	rng = random.Random(graine)
	segs = []
	while sum(s[0] for s in segs) < longueur:
		segs.append([rng.uniform(*larg), rng.uniform(*prof), False])
	for i in rng.sample(range(len(segs)), min(n_dech, len(segs))):
		segs[i] = [rng.uniform(*larg_d), rng.uniform(*prof_d), True]
	k = longueur / sum(s[0] for s in segs)
	bornes = [0.0]
	for s in segs:
		bornes.append(bornes[-1] + s[0] * k)

	def f(s):
		s = s % longueur if ferme else min(max(s, 0.0), longueur - 1e-9)
		i = int(np.searchsorted(bornes, s, side="right")) - 1
		i = min(max(i, 0), len(segs) - 1)
		t = (s - bornes[i]) / (bornes[i + 1] - bornes[i])
		_, a, dech = segs[i]
		if dech:
			return a * math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2))
		return a * (1 - math.cos(2 * math.pi * t)) / 2

	f.segments = [(bornes[i], bornes[i + 1], s[1], s[2]) for i, s in enumerate(segs)]
	return f


def plis(graine, n, s_max, amp, larg, h_haut):
	"""Plis verticaux qui partent du bas : (position, largeur, amplitude signee, hauteur ou ils s'effacent)."""
	rng = random.Random(graine)
	return [(rng.uniform(0, s_max), rng.uniform(*larg), rng.choice((1, 1, -1)) * rng.uniform(*amp), rng.uniform(*h_haut)) for _ in range(n)]


def relief(liste, s, h, periode=None):
	d = 0.0
	for s0, w, a, hh in liste:
		ds = s - s0
		if periode:
			ds = (ds + periode / 2) % periode - periode / 2
		d += a * math.exp(-((ds / w) ** 2)) * (1 - lisse(0.0, hh, h))
	return d


# parametres (fixes : le resultat ne change pas d'un lancement a l'autre)
L_T = chemin(1.0, W(ZB), D(ZB), R_COIN, OUV(ZB))[4]
ONDES_T = ondes(L_T, 11, (0.3, 0.6), (0.05, 0.1), False, n_dech=2, prof_d=(0.12, 0.18))
PLIS_T = plis(31, 12, L_T, (0.01, 0.022), (0.05, 0.11), (0.6, 1.5))


# --- maillages -------------------------------------------------------------------------------------------------------
def uv_zone(zone, a, b):
	"""a, b dans [0, 1] (a vers la droite, b vers le haut de la zone) -> UV Blender."""
	x0, y0, w, h = ZONES[zone]
	return ((x0 + a * w) / T, 1 - (y0 + (1 - b) * h) / T)


def grille(bm, uvl, pts, uvs, fermer):
	"""pts[i][j] (i : colonnes, j : rangs). fermer : la colonne apres la derniere est la premiere (UV deroulees)."""
	ni, nj = len(pts), len(pts[0])
	vs = [[bm.verts.new(pts[i][j]) for j in range(nj)] for i in range(ni)]
	faces = []
	for i in range(ni if fermer else ni - 1):
		i2 = (i + 1) % ni
		for j in range(nj - 1):
			f = bm.faces.new((vs[i][j], vs[i2][j], vs[i2][j + 1], vs[i][j + 1]))
			for l, (a, b) in zip(f.loops, ((i, j), (i2, j), (i2, j + 1), (i, j + 1))):
				l[uvl].uv = uvs[a][b]
			faces.append(f)
	return vs, faces


def orienter(faces, centre_de):
	"""Retourne toutes les faces si elles regardent majoritairement vers l'interieur (centre_de(face) -> point interieur)."""
	s = 0.0
	for f in faces:
		f.normal_update()
		c = f.calc_center_median()
		s += f.normal.dot(c - centre_de(c)) * f.calc_area()
	if s < 0:
		bmesh.ops.reverse_faces(bm_courant, faces=faces)


bm_courant = None


def rangs_cote(z0, z1, bas):
	"""Hauteurs des rangs d'une paroi : serres pres du bas (pour les vagues), puis tous les 0,15."""
	zs = [z0 + d for d in bas]
	z = zs[-1] + 0.15
	while z < z1 - 0.07:
		zs.append(z)
		z += 0.15
	return zs + [z1]


def torse(uvl):
	"""Torse ouvert sur le devant : parois, arrondi des epaules, dessus jusqu'a l'encolure, revers."""
	zs = rangs_cote(ZB, ZT - RR, [0, 0.03, 0.07, 0.12, 0.18, 0.25, 0.35, 0.47])
	rangs = [("cote", z, W(z), D(z), R_COIN, OUV(z), 0.0) for z in zs]
	w_t, d_t = W(ZT), D(ZT)
	for phi in (30, 60, 90):
		k = RR * (1 - math.cos(math.radians(phi)))
		rangs.append(("arc", ZT - RR + RR * math.sin(math.radians(phi)), w_t - k, d_t - k, max(R_COIN - k, 0.06), OUV(ZT), 0.0))
	_, _, hx0, hy0, r0, o0, _ = rangs[-1]
	for t in (0.25, 0.5, 0.75, 1.0):
		rangs.append(("dessus", ZT + 0.03 * t * t, hx0 + (COU[0] - hx0) * t, hy0 + (COU[1] - hy0) * t, r0 + (COU[2] - r0) * t, o0 + (0.24 - o0) * t, t))
	# hauteur deroulee de chaque rang (pour les UV), mesuree au milieu du dos
	v, prec, vs_rang = 0.0, None, []
	for kind, z, hx, hy, r, o, _ in rangs:
		x, y, *_ = chemin(0.5, hx, hy, r, o)
		p = Vector((x, y, z))
		v += (p - prec).length if prec is not None else 0.0
		prec = p
		vs_rang.append(v)
	v_max = vs_rang[-1]
	pts, uvs = [], []
	for i in range(NU_T + 1):
		u = i / NU_T
		s = u * L_T
		col_p, col_uv = [], []
		for (kind, z, hx, hy, r, o, t), vr in zip(rangs, vs_rang):
			x, y, nx, ny, _ = chemin(u, hx, hy, r, o)
			d = 0.0
			if kind != "dessus":
				h = z - ZB
				d += relief(PLIS_T, s, h)
				bord = min(s, L_T - s)
				d += 0.014 * math.exp(-((bord / 0.035) ** 2))  # bord de l'ouverture un peu roule
				if h < BANDE_T:
					z += ONDES_T(s) * (1 - h / BANDE_T)
			col_p.append(Vector((x + nx * d, y + ny * d, z)))
			col_uv.append(uv_zone("torse", u, vr / v_max))
		pts.append(col_p)
		uvs.append(col_uv)
	return pts, uvs, v_max


def revers(uvl, bm):
	"""Revers : rabats poses sur le haut du devant, le long de l'ouverture (rouge interieur, peint plus clair au pli)."""
	faces = []
	z_fin = ZT - RR - 0.62
	for sg in (1, -1):
		pts, uvs = [], []
		for j in range(4):
			c = j / 3
			col_p, col_uv = [], []
			for k in range(10):
				b = k / 9
				z = z_fin + (ZT - RR - z_fin) * b
				larg = 0.18 * b ** 0.85
				x = sg * (OUV(z) - 0.01 + larg * c)
				y = D(z) + 0.012 + 0.012 * c * b
				col_p.append(Vector((x, y, z)))
				col_uv.append(uv_zone("revers", (0.5 if sg > 0 else 0.0) + 0.5 * c, b))
			pts.append(col_p)
			uvs.append(col_uv)
		_, f = grille(bm, uvl, pts, uvs, False)
		for x in f:
			x.normal_update()
			if x.normal.y < 0:
				x.normal_flip()
		faces += f
	return faces


def repere_bras(o):
	"""Axes locaux de la piece les plus proches de (exterieur, avant, haut) et sa boite locale."""
	R = o.matrix_world.to_3x3().normalized()
	ext = Vector((1 if o.name.startswith("Right") else -1, 0, 0))
	axes = []
	for cible in (ext, Vector((0, 1, 0)), Vector((0, 0, 1))):
		i = max(range(3), key=lambda k: abs(R.col[k].dot(cible)))
		sgn = 1 if R.col[i].dot(cible) > 0 else -1
		e = Vector((0, 0, 0))
		e[i] = sgn
		axes.append(e)
	ps = [x.co for x in o.data.vertices]
	mn = Vector([min(p[k] for p in ps) for k in range(3)])
	mx = Vector([max(p[k] for p in ps) for k in range(3)])
	c = (mn + mx) / 2
	demi = [abs((mx - mn).dot(e)) / 2 for e in axes]
	return c, axes, demi


def manche(o, zone, graine):
	"""Manche evasee, fermee en haut, bas effiloche (local de la piece UpperArm)."""
	c, (ex, ey, ez), (ax, ay, az) = repere_bras(o)
	zb, zt = -az + M_BAS, az + M_HAUT
	L = chemin(1.0, ax + 0.13, ay + 0.12, 0.15)[4]
	onde = ondes(L, graine, (0.3, 0.6), (0.05, 0.1), True, n_dech=2, prof_d=(0.12, 0.18))  # memes vagues que le bas du torse
	pl = plis(graine + 100, 9, L, (0.015, 0.032), (0.06, 0.12), (0.5, 1.0))

	def section(z):
		f = lisse(zt, zb, z) ** 1.5
		return ax + 0.06 + 0.07 * f, ay + 0.06 + 0.06 * f, 0.15

	zs = rangs_cote(zb, zt - M_RR, [0, 0.03, 0.07, 0.12, 0.18, 0.25, 0.33, 0.42, 0.55])
	rangs = [("cote", z) + section(z) for z in zs]
	hx_t, hy_t, r_t = section(zt)
	for phi in (30, 60, 90):
		k = M_RR * (1 - math.cos(math.radians(phi)))
		rangs.append(("arc", zt - M_RR + M_RR * math.sin(math.radians(phi)), hx_t - k, hy_t - k, max(r_t - k, 0.06)))
	_, _, hx0, hy0, r0 = rangs[-1]
	for t in (0.35, 0.7):
		rangs.append(("dessus", zt, hx0 + (0.16 - hx0) * t, hy0 + (0.16 - hy0) * t, r0 + (0.07 - r0) * t))
	v, prec, vs_rang = 0.0, None, []
	for kind, z, hx, hy, r in rangs:
		x, y, *_ = chemin(0.25, hx, hy, r)
		p = Vector((x, y, z))
		v += (p - prec).length if prec is not None else 0.0
		prec = p
		vs_rang.append(v)
	v_max = vs_rang[-1] + 0.12

	def local(x, y, z):
		return c + ex * x + ey * y + ez * z

	pts, uvs = [], []
	for i in range(NU_M):
		u = i / NU_M
		s = u * L
		col_p, col_uv = [], []
		for (kind, z, hx, hy, r), vr in zip(rangs, vs_rang):
			x, y, nx, ny, _ = chemin(u, hx, hy, r)
			d = 0.0
			if kind == "cote":
				h = z - zb
				d += relief(pl, s, h, periode=L)
				d += 0.012 * math.sin(2 * math.pi * s / 0.45 + 1.3) * (1 - lisse(0.0, 0.5, h))  # ondulation du bas evase
				if h < BANDE_M:
					z += onde(s) * (1 - h / BANDE_M)
			col_p.append(local(x + nx * d, y + ny * d, z))
			col_uv.append(uv_zone(zone, u, vr / v_max))
		pts.append(col_p)
		uvs.append(col_uv)
	return pts, uvs, (local(0, 0, zt + 0.0), uv_zone(zone, 0.5, 1.0)), {"zb": zb, "L": L, "onde": onde, "plis": pl, "v_max": v_max, "vs": vs_rang}


def materiau(nom, couleur, image=None):
	mat = bpy.data.materials.get(nom) or bpy.data.materials.new(nom)
	mat.use_nodes = True
	nt = mat.node_tree
	bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
	bsdf.inputs["Roughness"].default_value = 0.85
	bsdf.inputs["Base Color"].default_value = couleur
	mat.diffuse_color = couleur
	if image is not None:
		tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and n.name != "Cuisson"), None) or nt.nodes.new("ShaderNodeTexImage")
		tex.image = image
		nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
	return mat


def objet_piece(nom, piece, bm):
	"""Copie de la piece du rig (memes contraintes Child Of : suit son os), maillage remplace."""
	src = bpy.data.objects[piece]
	ancien = bpy.data.objects.get(nom)
	if ancien:
		bpy.data.objects.remove(ancien, do_unlink=True)
	me = bpy.data.meshes.new(nom)
	bm.to_mesh(me)
	bm.free()
	o = src.copy()
	o.data = me
	o.name = nom
	for col in src.users_collection:
		col.objects.link(o)
	o.hide_set(False)
	o.hide_render = False
	return o


def construire():
	global bm_courant
	CUISSON.mkdir(exist_ok=True)
	img = bpy.data.images.get(TEXTURE.name)
	if img is None and TEXTURE.exists():
		img = bpy.data.images.load(str(TEXTURE))
	mats = [materiau("Mat_Chemise_v6", (0.6, 0.06, 0.07, 1), img), materiau("Mat_Chemise_v6_Int", (0.22, 0.025, 0.03, 1)),
		materiau("Mat_Chemise_v6_Bord", (0.32, 0.04, 0.045, 1))]
	objets = []
	# torse
	ut = bpy.data.objects["UpperTorso"]
	inv = ut.matrix_world.inverted()
	bm = bmesh.new()
	bm_courant = bm
	uvl = bm.loops.layers.uv.new("UVMap")
	pts, uvs, _ = torse(uvl)
	_, faces = grille(bm, uvl, pts, uvs, False)
	orienter(faces, lambda c: Vector((0, 0, min(c.z, ZT - 0.5))))
	revers(uvl, bm)
	bm.transform(inv)  # monde -> local de UpperTorso
	bm.normal_update()
	objets.append(objet_piece("Chemise_Torse", "UpperTorso", bm))
	# manches
	for nom, piece, zone, graine in (("Chemise_MancheD", "RightUpperArm", "manche_d", 41), ("Chemise_MancheG", "LeftUpperArm", "manche_g", 57)):
		o = bpy.data.objects[piece]
		bm = bmesh.new()
		bm_courant = bm
		uvl = bm.loops.layers.uv.new("UVMap")
		pts, uvs, (sommet, uv_s), _ = manche(o, zone, graine)
		vs, faces = grille(bm, uvl, pts, uvs, True)
		dernier = [col[-1] for col in vs]
		v_s = bm.verts.new(sommet)
		for i in range(len(dernier)):
			a, b = dernier[i], dernier[(i + 1) % len(dernier)]
			f = bm.faces.new((a, b, v_s))
			ua, ub = uvs[i][-1], uvs[(i + 1) % len(dernier)][-1]
			if i + 1 == len(dernier):
				ub = (ub[0] + ZONES[zone][2] / T, ub[1])
			for l, uu in zip(f.loops, (ua, ub, uv_s)):
				l[uvl].uv = uu
			faces.append(f)
		c_loc = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
		orienter(faces, lambda c: c_loc)
		# couture : les boucles de la derniere colonne de faces prennent u + largeur de zone
		w = ZONES[zone][2] / T
		x0 = ZONES[zone][0] / T
		for f in faces:
			us = [l[uvl].uv.x for l in f.loops]
			if max(us) - min(us) > w / 2:
				for l in f.loops:
					if l[uvl].uv.x < x0 + w / 2:
						l[uvl].uv.x += w
		bm.normal_update()
		objets.append(objet_piece(nom, piece, bm))
	for o in objets:
		o.data.materials.clear()
		for m in mats:
			o.data.materials.append(m)
		for p in o.data.polygons:
			p.material_index = 0
			p.use_smooth = True
		m = o.modifiers.new("Epaisseur", "SOLIDIFY")
		m.thickness = EPAISSEUR
		m.offset = -1
		m.use_rim = True
		m.use_even_offset = True
		m.use_quality_normals = True
		m.material_offset = 1
		m.material_offset_rim = 2
	for nom in ("veste", "veste_sauvegarde", "veste_modifiee", "veste_avant_reparation", "veste_avant_reparation2", "veste_avant_zigzag"):
		o = bpy.data.objects.get(nom)
		if o:
			o.hide_set(True)
			o.hide_render = True
	for o in objets:
		ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
		tris = sum(len(p.vertices) - 2 for p in ev.data.polygons)
		print(o.name, [round(d, 3) for d in o.dimensions], tris, "triangles avec epaisseur")
	return objets


# --- cuisson ---------------------------------------------------------------------------------------------------------
def cuire(echantillons=32):
	"""Occlusion ambiante et lumiere (soleil devant, en hauteur) cuites dans cuisson_v6/ (epaisseur coupee : seule la face
	exterieure porte les UV utiles). Le corps du rig reste visible : il assombrit le dessous des manches."""
	cuire_objets([bpy.data.objects[n] for n in PIECES], "Mat_Chemise_v6", CUISSON, "cuisson_v6_", echantillons)


def cuire_objets(objs, nom_mat, dossier, prefixe, echantillons=32):
	"""Cuisson ao.png / lumiere.png dans dossier pour des objets qui partagent le materiau texture nom_mat."""
	sc = bpy.context.scene
	moteur = sc.render.engine
	try:
		sc.render.engine = "CYCLES"
	except TypeError as e:
		print(e)
	sc.cycles.samples = echantillons
	soleil = bpy.data.objects.get("Soleil_v6")
	if soleil is None:
		soleil = bpy.data.objects.new("Soleil_v6", bpy.data.lights.new("Soleil_v6", "SUN"))
		sc.collection.objects.link(soleil)
	soleil.data.energy = 3.0
	soleil.data.angle = math.radians(25)
	soleil.rotation_euler = Vector((-0.25, -0.75, -1.0)).normalized().to_track_quat("-Z", "Y").to_euler()  # vient de l'avant (+Y), d'en haut
	if sc.world is None:
		sc.world = bpy.data.worlds.new("Monde")
	sc.world.use_nodes = True
	fond = next(n for n in sc.world.node_tree.nodes if n.type == "BACKGROUND")
	fond.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1)
	fond.inputs["Strength"].default_value = 0.6
	for o in objs:
		o.modifiers["Epaisseur"].show_render = False
		o.modifiers["Epaisseur"].show_viewport = False
	nt = bpy.data.materials[nom_mat].node_tree
	noeud = nt.nodes.get("Cuisson") or nt.nodes.new("ShaderNodeTexImage")
	noeud.name = "Cuisson"
	dossier.mkdir(exist_ok=True)
	for nom, type_, filtre in (("ao", "AO", None), ("lumiere", "DIFFUSE", {"DIRECT", "INDIRECT"})):
		img = bpy.data.images.get(prefixe + nom) or bpy.data.images.new(prefixe + nom, T, T, alpha=False)
		img.generated_color = (0, 0, 0, 1)
		noeud.image = img
		nt.nodes.active = noeud
		for o in bpy.context.view_layer.objects:
			o.select_set(o in objs)
		bpy.context.view_layer.objects.active = objs[0]
		args = {"type": type_, "margin": 8}
		if filtre:
			args["pass_filter"] = filtre
		with bpy.context.temp_override(selected_objects=objs, selected_editable_objects=objs, active_object=objs[0], object=objs[0]):
			bpy.ops.object.bake(**args)
		img.filepath_raw = str(dossier / (nom + ".png"))
		img.file_format = "PNG"
		img.save()
	nt.nodes.remove(noeud)
	for o in objs:
		o.modifiers["Epaisseur"].show_render = True
		o.modifiers["Epaisseur"].show_viewport = True
	try:
		sc.render.engine = moteur
	except TypeError:
		pass


# --- peinture --------------------------------------------------------------------------------------------------------
RAMPE = [(0.0, (48, 6, 12)), (0.3, (86, 10, 18)), (0.5, (126, 16, 26)), (0.7, (166, 22, 32)), (0.88, (194, 32, 40)), (1.05, (214, 52, 52)), (1.3, (234, 98, 86))]
INTERIEUR = (88, 12, 18)
BOUTON, BOUTON_OMBRE, BOUTON_CLAIR = (196, 160, 104), (120, 88, 52), (236, 214, 168)


def lire(nom, dossier=CUISSON):
	img = bpy.data.images.load(str(dossier / (nom + ".png")), check_existing=False)
	a = np.array(img.pixels[:], dtype=np.float32).reshape(T, T, 4)[::-1, :, 0]
	bpy.data.images.remove(img)
	return a


def flou(a, r):
	"""Flou gaussien separable (r en pixels)."""
	k = np.exp(-0.5 * (np.arange(-3 * r, 3 * r + 1) / r) ** 2)
	k /= k.sum()
	a = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, a)
	return np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 1, a)


def rampe(f):
	q = np.round(f * 6) / 6
	f = 0.6 * f + 0.4 * q  # aplats doux facon peinture
	xs = np.array([r[0] for r in RAMPE])
	return np.stack([np.interp(f, xs, [r[1][k] for r in RAMPE]) for k in range(3)], -1)


def traits(F, S, H, liste, sombre=True):
	"""Plis peints (traits effiles) dans l'espace (s, h) : F *= 1 - force (sombre) ou 1 + force (clair)."""
	for s0, h0, longueur, larg, force, pente in liste:
		t = np.clip((H - h0) / longueur, 0, 1)
		d = np.abs(S - (s0 + pente * (H - h0)))
		prof = np.exp(-((d / larg) ** 2)) * np.clip(np.sin(np.pi * t), 0, 1) ** 0.6 * ((H >= h0) & (H <= h0 + longueur))  # clip : sin(pi) < 0 en float32
		F *= (1 - force * prof) if sombre else (1 + force * prof)


def plis_peints(graine, onde, s_max, longueurs):
	"""Plis qui partent des pointes du bas effiloche (et quelques-uns au hasard)."""
	rng = random.Random(graine)
	pointes = [a for a, _, _, _ in onde.segments] + [rng.uniform(0, s_max) for _ in range(6)]
	res = []
	for s0 in pointes:
		if rng.random() < 0.25:
			continue
		res.append((s0 + rng.uniform(-0.03, 0.03), 0.0, rng.uniform(*longueurs), rng.uniform(0.014, 0.032), rng.uniform(0.25, 0.45), rng.uniform(-0.08, 0.08)))
	return res


def bandes_plis(F, S, H, liste, periode=None):
	"""Ombre et lumiere larges le long des plis de la geometrie : un cote du pli sombre, l'autre clair (lumiere a +s)."""
	for s0, w, a, hh in liste:
		ds = S - s0
		if periode:
			ds = (ds + periode / 2) % periode - periode / 2
		env = 1 - np.clip(H / hh, 0, 1) ** 1.5
		if a > 0:  # pli en relief : ombre d'un cote, lumiere de l'autre
			F *= 1 - 0.3 * np.exp(-(((ds - 0.75 * w) / (0.7 * w)) ** 2)) * env
			F *= 1 + 0.14 * np.exp(-(((ds + 0.5 * w) / (0.6 * w)) ** 2)) * env
		else:  # creux : sombre au centre
			F *= 1 - 0.32 * np.exp(-((ds / (0.6 * w)) ** 2)) * env


TEXTURE_ANIME = DOSSIER / "tex_chemise_v6_anime.png"
# style anime : aplats francs (seuils sur le meme eclairage que la version peinte)
CEL = [(0.0, (92, 10, 22)), (0.42, (150, 18, 32)), (0.72, (206, 30, 42)), (1.04, (240, 92, 80))]
CEL_BORD = 0.015  # largeur de l'anticrenelage des seuils


def cel(f, paliers=None):
	"""Paliers nets : chaque seuil (de CEL par defaut) fait passer d'une teinte a la suivante sur CEL_BORD."""
	paliers = paliers or CEL
	out = np.broadcast_to(np.array(paliers[0][1], np.float32), f.shape + (3,)).copy()
	for seuil, c in paliers[1:]:
		t = np.clip((f - seuil) / CEL_BORD + 0.5, 0, 1)[..., None]
		out = out * (1 - t) + np.array(c, np.float32) * t
	return out


def peindre(anime=False):
	"""anime=False : rendu peint (tex_chemise_v6.png) ; anime=True : aplats francs (tex_chemise_v6_anime.png)."""
	ao, lum = lire("ao"), lire("lumiere")
	masque = ao > 0.001
	ref = np.percentile(lum[masque], 97)
	lumiere = np.clip(lum / ref, 0, 1.25)
	F = (0.2 + 0.88 * lumiere ** 0.85) * (0.5 + 0.5 * ao)
	ys, xs = np.mgrid[0:T, 0:T].astype(np.float32)
	couleur_fixe = np.zeros((T, T, 3), np.float32)
	fixe = np.zeros((T, T), bool)

	def zone_sh(zone, s_tot, v_max):
		x0, y0, w, h = ZONES[zone]
		sl = (slice(y0, y0 + h), slice(x0, x0 + w))
		S = (xs[sl] - x0 + 0.5) / w * s_tot
		V = (1 - (ys[sl] - y0 + 0.5) / h) * v_max
		return sl, S, V

	# torse
	_, _, v_max_t = torse(None)
	sl, S, V = zone_sh("torse", L_T, v_max_t)
	Fz = F[sl]
	e = np.array([ONDES_T(s) for s in S[0]], np.float32)[None, :]
	hb = np.where(V < BANDE_T, V * (1 - e / BANDE_T), V)
	cote = V <= ZT - RR - ZB
	bandes_plis(Fz, S, V, PLIS_T)
	liste = plis_peints(5, ONDES_T, L_T, (0.25, 0.75))
	traits(Fz, S, V, liste)
	traits(Fz, S + 0.03, V, [(s0, h0, l, w * 0.8, f * 0.5, p) for s0, h0, l, w, f, p in liste], sombre=False)
	bord_ouv = np.minimum(S, L_T - S)
	Fz *= np.where(cote, 1 - 0.1 * (bord_ouv < 0.075) - 0.06 * np.exp(-((bord_ouv / 0.02) ** 2)), 1)  # patte de boutonnage
	Fz *= 1 + 0.12 * np.exp(-(((bord_ouv - 0.005) / 0.006) ** 2))  # liseré clair du bord
	Fz *= np.where(cote, 1 - 0.22 * np.exp(-hb / 0.045), 1)  # bord du bas roule, dans l'ombre
	Fz *= 1 + 0.16 * ((hb < 0.01) & cote)  # liseré clair tout en bas
	F[sl] = Fz
	# boutons (pan droit du perso, cote +X : debut du contour)
	x0, y0, w, h = ZONES["torse"]
	for k in range(4):
		hz = ZT - 0.5 - ZB - 0.33 * k
		cx, cy = x0 + 0.06 / L_T * w, y0 + (1 - hz / v_max_t) * h
		rx, ry = 0.045 / L_T * w, 0.045 / v_max_t * h
		dd = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2
		om = (((xs - cx - 3) / rx) ** 2 + ((ys - cy - 4) / ry) ** 2) < 1.15
		F[om & ~(dd < 1)] *= 0.7
		for msk, c in ((dd < 1.0, BOUTON_OMBRE), (dd < 0.75, BOUTON), ((((xs - cx + rx * 0.3) / rx) ** 2 + ((ys - cy + ry * 0.3) / ry) ** 2) < 0.12, BOUTON_CLAIR)):
			couleur_fixe[msk] = c
			fixe |= msk
	# manches
	for piece, zone, graine in (("RightUpperArm", "manche_d", 41), ("LeftUpperArm", "manche_g", 57)):
		_, _, _, info = manche(bpy.data.objects[piece], zone, graine)
		sl, S, V = zone_sh(zone, info["L"], info["v_max"])
		Fz = F[sl]
		e = np.array([info["onde"](s) for s in S[0]], np.float32)[None, :]
		hb = np.where(V < BANDE_M, V * (1 - e / BANDE_M), V)
		bandes_plis(Fz, S, V, info["plis"], periode=info["L"])
		liste = plis_peints(graine + 7, info["onde"], info["L"], (0.2, 0.6))
		traits(Fz, S, V, liste)
		traits(Fz, S + 0.025, V, [(s0, h0, l, w * 0.8, f * 0.5, p) for s0, h0, l, w, f, p in liste], sombre=False)
		Fz *= 1 - 0.25 * np.exp(-hb / 0.04)
		Fz *= 1 + 0.18 * (hb < 0.008)
		Fz *= 1 + 0.08 * np.exp(-(((V - (info["v_max"] - 0.3)) / 0.12) ** 2))  # epaule plus claire
		F[sl] = Fz
	# grain du tissu
	rng = np.random.default_rng(3)
	grain = flou(rng.standard_normal((T, T)).astype(np.float32), 1.2)
	grain /= grain.std()
	if anime:
		img = cel(flou(F, 3.5))  # pas de grain ; flou : le bruit de la cuisson ne mouchete pas les seuils
	else:
		F *= 1 + 0.035 * grain + 0.018 * np.sin((xs + ys) * 2 * np.pi / 7)
		img = rampe(F)
	img[fixe] = couleur_fixe[fixe]
	img[~(masque | fixe)] = INTERIEUR
	# revers : rouge interieur, plus clair vers le pli
	x0, y0, w, h = ZONES["revers"]
	sl = (slice(y0, y0 + h), slice(x0, x0 + w))
	c = ((xs[sl] - x0) % (w / 2)) / (w / 2)
	b = 1 - (ys[sl] - y0) / h
	fr = (0.62 + 0.25 * np.exp(-(((c - 0.05) / 0.12) ** 2)) - 0.12 * c) * (0.85 + 0.15 * b)
	img[sl] = cel(fr) if anime else rampe(fr * (1 + 0.03 * grain[sl]))
	img = np.clip(img, 0, 255) / 255.0
	px = np.concatenate([img[::-1], np.ones((T, T, 1), np.float32)], -1)
	chemin = TEXTURE_ANIME if anime else TEXTURE
	out = bpy.data.images.get(chemin.name) or bpy.data.images.new(chemin.name, T, T, alpha=False)
	if out.size[0] != T:
		out.scale(T, T)
	out.pixels.foreach_set(px.astype(np.float32).ravel())
	out.filepath_raw = str(chemin)
	out.file_format = "PNG"
	out.save()
	materiau("Mat_Chemise_v6", (0.6, 0.06, 0.07, 1), out)
	return chemin
