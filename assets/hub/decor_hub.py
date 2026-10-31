"""Décor du Hub (style « sanctuaire de festival animé ») : pièces sculptées pour Roblox.

Lancer en arrière-plan (n'utilise pas le Blender ouvert) :
	blender -b --factory-startup --python assets/hub/decor_hub.py -- [apercu]

Produit dans assets/hub/ :
	palette_hub.png      texture partagée (une ligne par teinte, dégradé ombre → lumière)
	decor_hub.blend      scène source
	fbx/decor_hub.fbx    toutes les pièces (1 objet = 1 MeshPart), 1 unité = 1 stud
	decor_hub.json       taille de chaque pièce (axes Roblox) et triangles
	apercu/*.png         rendus de contrôle (option « apercu »)

Ombrage peint doux cuit dans les UV : u = éclairage (normale · lumière, hauteur), v = teinte.
Jamais de traits noirs.
"""

import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

DOSSIER = Path(__file__).resolve().parent
ARGS = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []

# --- palette : (ombre, moyen, lumière) en sRGB -------------------------------------------
TEINTES = {
	"sakura": ((172, 102, 142), (236, 162, 192), (255, 232, 238)),
	"sakura2": ((160, 94, 138), (228, 148, 182), (252, 222, 232)),
	"tronc": ((72, 50, 56), (116, 84, 84), (162, 128, 118)),
	"vermillon": ((168, 38, 52), (232, 64, 52), (255, 128, 96)),
	"prune": ((30, 20, 34), (54, 38, 52), (98, 76, 92)),
	"or": ((196, 116, 52), (240, 170, 80), (255, 222, 146)),
	"pierre": ((146, 134, 154), (204, 194, 196), (242, 236, 230)),
	"toit": ((132, 56, 80), (196, 88, 110), (236, 146, 156)),
	"corde": ((176, 136, 78), (228, 198, 138), (250, 234, 192)),
	"papier": ((206, 196, 214), (248, 244, 238), (255, 255, 255)),
}
LIGNES = list(TEINTES)
LARG, HAUT_LIGNE = 64, 8
LUMIERE = Vector((0.45, -0.55, 0.75)).normalized()


def creer_palette():
	h = HAUT_LIGNE * len(LIGNES)
	pix = np.zeros((h, LARG, 4), dtype=np.float32)
	u = np.linspace(0, 1, LARG)
	for i, nom in enumerate(LIGNES):
		o, m, l = (np.array(c, dtype=np.float32) / 255 for c in TEINTES[nom])
		# dégradé doux en 2 segments (ombre → moyen sur 0..0,55, moyen → lumière ensuite)
		t1 = np.clip(u / 0.55, 0, 1)[:, None]
		t2 = np.clip((u - 0.55) / 0.45, 0, 1)[:, None]
		t1 = t1 * t1 * (3 - 2 * t1)
		t2 = t2 * t2 * (3 - 2 * t2)
		ligne = o + (m - o) * t1
		ligne = ligne + (l - m) * t2
		y0 = h - (i + 1) * HAUT_LIGNE  # Blender : origine des images en bas
		pix[y0 : y0 + HAUT_LIGNE, :, :3] = ligne[None, :, :]
	pix[..., 3] = 1
	img = bpy.data.images.get("palette_hub") or bpy.data.images.new("palette_hub", LARG, h)
	img.scale(LARG, h)
	img.pixels.foreach_set(pix.ravel())
	img.filepath_raw = str(DOSSIER / "palette_hub.png")
	img.file_format = "PNG"
	img.save()
	img.colorspace_settings.name = "sRGB"
	return img


def materiau(img):
	mat = bpy.data.materials.new("Mat_DecorHub")
	mat.use_nodes = True
	nt = mat.node_tree
	bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
	tex = nt.nodes.new("ShaderNodeTexImage")
	tex.image = img
	tex.interpolation = "Linear"
	nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
	bsdf.inputs["Roughness"].default_value = 0.8
	return mat


# --- construction ------------------------------------------------------------------------
def objet_bm(nom, bm):
	me = bpy.data.meshes.new(nom)
	bm.to_mesh(me)
	bm.free()
	ob = bpy.data.objects.new(nom, me)
	bpy.context.scene.collection.objects.link(ob)
	return ob


def boite(nom, taille, pos, rot=(0, 0, 0), biseau=0.0, decoupe_x=0):
	bm = bmesh.new()
	bmesh.ops.create_cube(bm, size=1)
	bmesh.ops.scale(bm, vec=Vector(taille), verts=bm.verts)
	if decoupe_x:
		aretes = [e for e in bm.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > 1e-4]
		bmesh.ops.subdivide_edges(bm, edges=aretes, cuts=decoupe_x, use_grid_fill=True)
	ob = objet_bm(nom, bm)
	if biseau:
		mod = ob.modifiers.new("Biseau", "BEVEL")
		mod.width = biseau
		mod.segments = 2
		mod.limit_method = "ANGLE"
	ob.rotation_euler = rot
	ob.location = pos
	return ob


def cylindre(nom, r1, r2, h, pos, segs=16, rot=(0, 0, 0), biseau=0.0):
	bm = bmesh.new()
	bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=h)
	ob = objet_bm(nom, bm)
	if biseau:
		mod = ob.modifiers.new("Biseau", "BEVEL")
		mod.width = biseau
		mod.segments = 2
		mod.limit_method = "ANGLE"
	ob.rotation_euler = rot
	ob.location = pos
	return ob


def sphere(nom, r, pos, segs=12, anneaux=8, echelle=(1, 1, 1)):
	bm = bmesh.new()
	bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=anneaux, radius=r)
	ob = objet_bm(nom, bm)
	ob.location = pos
	ob.scale = echelle
	return ob


def figer(ob):
	"""Applique modificateurs et transformations (maillage évalué)."""
	dg = bpy.context.evaluated_depsgraph_get()
	me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
	me.transform(ob.matrix_world)
	ancien = ob.data
	ob.modifiers.clear()
	ob.data = me
	ob.matrix_world = Matrix.Identity(4)
	if ancien.users == 0:
		bpy.data.meshes.remove(ancien)
	return ob


def colorier(ob, teinte, hauteur=None, force=1.0, lisse=True):
	"""UV = (éclairage peint, ligne de la teinte). hauteur = (zmin, zmax, poids)."""
	figer(ob)
	me = ob.data
	if lisse:
		for p in me.polygons:
			p.use_smooth = True
	if not me.uv_layers:
		me.uv_layers.new(name="UVMap")
	uv = me.uv_layers.active.data
	i = LIGNES.index(teinte)
	v = 1 - (i + 0.5) / len(LIGNES)
	nrm = [Vector(n.vector) for n in me.vertex_normals] if lisse else None
	for p in me.polygons:
		for li in p.loop_indices:
			vi = me.loops[li].vertex_index
			n = nrm[vi] if lisse else Vector(p.normal)
			f = 0.5 + 0.5 * n.dot(LUMIERE)
			f = 0.5 + (f - 0.5) * force
			if hauteur:
				z0, z1, w = hauteur
				t = min(1, max(0, (me.vertices[vi].co.z - z0) / (z1 - z0)))
				f = f * (1 - w) + t * w
			uv[li].uv = (min(0.97, max(0.03, f)), v)
	return ob


def joindre(nom, objets):
	ctx = bpy.context
	for o in ctx.scene.objects:
		o.select_set(False)
	for o in objets:
		o.select_set(True)
	ctx.view_layer.objects.active = objets[0]
	bpy.ops.object.join()
	ob = ctx.view_layer.objects.active
	ob.name = nom
	ob.data.name = nom
	bm = bmesh.new()
	bm.from_mesh(ob.data)
	bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
	bm.to_mesh(ob.data)
	bm.free()
	return ob


def triangles(ob):
	return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# --- cerisier : ramure visible + touffes séparées, facettes peintes ------------------------
def touffe(nom, centre, rayon, rnd, teinte):
	"""Une touffe de fleurs : métaboules aplaties dessous, bosselées, à facettes."""
	mb = bpy.data.metaballs.new(nom)
	mb.resolution = 0.32
	mb.render_resolution = 0.32
	mb.threshold = 0.6
	el = mb.elements.new()
	el.co = centre
	el.radius = rayon
	for k in range(6):
		a = k / 6 * math.tau + rnd.uniform(-0.4, 0.4)
		d = rayon * rnd.uniform(0.55, 0.8)
		e = mb.elements.new()
		e.co = centre + Vector((math.cos(a) * d, math.sin(a) * d, rnd.uniform(-0.15, 0.45) * rayon))
		e.radius = rayon * rnd.uniform(0.5, 0.7)
	mo = bpy.data.objects.new(nom, mb)
	bpy.context.scene.collection.objects.link(mo)
	dg = bpy.context.evaluated_depsgraph_get()
	me = bpy.data.meshes.new_from_object(mo.evaluated_get(dg))
	bpy.data.objects.remove(mo)
	# dessous aplati (touffes « posées » comme dans les décors d'anime)
	zb = centre.z - rayon * 0.45
	for v in me.vertices:
		if v.co.z < zb:
			v.co.z = zb + (v.co.z - zb) * 0.25
	ob = bpy.data.objects.new(nom, me)
	bpy.context.scene.collection.objects.link(ob)
	tex = bpy.data.textures.get("BruitFeuillage") or bpy.data.textures.new("BruitFeuillage", "CLOUDS")
	tex.noise_scale = 0.55
	dep = ob.modifiers.new("Bosses", "DISPLACE")
	dep.texture = tex
	dep.strength = 0.55
	dep.mid_level = 0.5
	dec = ob.modifiers.new("Facettes", "DECIMATE")
	dec.ratio = min(1.0, 300 / max(1, sum(len(p.vertices) - 2 for p in me.polygons)))
	colorier(ob, teinte, hauteur=(centre.z - rayon * 0.6, centre.z + rayon, 0.5), force=1.3, lisse=False)
	return ob


def cerisier(nom, graine, teinte):
	rnd = random.Random(graine)
	pts, aretes, rayons = [], [], []

	def point(p, r):
		pts.append(p)
		rayons.append(r)
		return len(pts) - 1

	# tronc noueux
	ang = rnd.uniform(0, math.tau)
	prec = point(Vector((0, 0, 0)), 0.8)
	pos = Vector((0, 0, 0))
	for k, r in enumerate((0.62, 0.52, 0.47)):
		a = ang + k * 1.7
		pos = pos + Vector((math.cos(a) * 0.55, math.sin(a) * 0.55, 1.45))
		i = point(pos, r)
		aretes.append((prec, i))
		prec = i
	fourche = prec
	bouts = []
	# 4 grosses branches, chacune fourchue en 2 rameaux
	for b in range(4):
		a = ang + b * math.tau / 4 + rnd.uniform(-0.35, 0.35)
		h = Vector((math.cos(a), math.sin(a), 0))
		m1 = point(pts[fourche] + h * 2.0 + Vector((0, 0, 1.7 + rnd.uniform(-0.3, 0.5))), 0.3)
		aretes.append((fourche, m1))
		for s in (-1, 1):
			a2 = a + s * rnd.uniform(0.45, 0.7)
			h2 = Vector((math.cos(a2), math.sin(a2), 0))
			m2 = point(pts[m1] + h2 * 2.0 + Vector((0, 0, rnd.uniform(-0.2, 1.4))), 0.17)
			aretes.append((m1, m2))
			t = point(pts[m2] + h2 * 0.9 + Vector((0, 0, rnd.uniform(-0.3, 0.4))), 0.1)
			aretes.append((m2, t))
			bouts.append(pts[t])
	# flèche centrale
	cime = point(pts[fourche] + Vector((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), 4.0)), 0.2)
	aretes.append((fourche, cime))
	bouts.append(pts[cime])

	me = bpy.data.meshes.new(nom + "_Tronc")
	me.from_pydata([tuple(p) for p in pts], aretes, [])
	tronc = bpy.data.objects.new(nom + "_Tronc", me)
	bpy.context.scene.collection.objects.link(tronc)
	tronc.modifiers.new("Skin", "SKIN")
	for sv, r in zip(me.skin_vertices[0].data, rayons):
		sv.radius = (r, r)
	me.skin_vertices[0].data[0].use_root = True
	sub = tronc.modifiers.new("Subdiv", "SUBSURF")
	sub.levels = 1
	colorier(tronc, "tronc", hauteur=(0, 9, 0.35))
	racines = []
	for k in range(3):
		a = ang + k * math.tau / 3 + 0.3
		c = cylindre(nom + "_Racine", 0.32, 0.1, 0.9, (math.cos(a) * 0.55, math.sin(a) * 0.55, 0.22), segs=6,
			rot=(math.sin(a) * 1.0, -math.cos(a) * 1.0, 0))
		racines.append(colorier(c, "tronc", hauteur=(0, 9, 0.35)))

	# touffes au bout des rameaux + quelques touffes intermédiaires pour remplir sans fermer
	touffes = []
	for k, b in enumerate(bouts):
		r = rnd.uniform(1.45, 1.85) if k < len(bouts) - 1 else 2.0
		touffes.append(touffe(f"{nom}_T{k}", b + Vector((0, 0, 0.5)), r, rnd, teinte))
	for k in range(4):
		a = ang + (k + 0.5) * math.tau / 4
		c = pts[fourche] + Vector((math.cos(a) * 2.2, math.sin(a) * 2.2, rnd.uniform(2.6, 3.6)))
		touffes.append(touffe(f"{nom}_M{k}", c, rnd.uniform(1.2, 1.5), rnd, teinte))
	return joindre(nom, touffes + [tronc] + racines)


# --- torii ------------------------------------------------------------------------------
def torii():
	parts = []
	for s in (-1, 1):
		parts.append(colorier(cylindre("Pilier", 0.8, 0.68, 13.4, (s * 7.6, 0, 1.2 + 6.7), segs=16), "vermillon", lisse=True))
		parts.append(colorier(cylindre("Socle", 1.08, 1.0, 1.2, (s * 7.6, 0, 0.6), segs=16, biseau=0.08), "prune", lisse=False))
		parts.append(colorier(cylindre("Bague", 0.86, 0.86, 0.25, (s * 7.6, 0, 1.35), segs=16), "or"))
		# coin du nuki qui dépasse
		parts.append(colorier(boite("Cale", (0.5, 1.3, 0.5), (s * 7.6, 0, 10.55), biseau=0.06), "vermillon", lisse=False))

	# kasagi courbe (noir prune) et shimaki (vermillon) : boîtes découpées puis relevées aux bouts
	def courber(ob, demi, fleche, puissance=2.6):
		for v in ob.data.vertices:
			t = min(1, abs(v.co.x) / demi)
			v.co.z += fleche * t**puissance
		return ob

	k = boite("Kasagi", (22.4, 2.4, 0.95), (0, 0, 0), biseau=0.12, decoupe_x=28)
	figer(k)
	courber(k, 11.2, 1.25)
	k.location = (0, 0, 15.15)
	parts.append(colorier(k, "prune", lisse=False))
	sh = boite("Shimaki", (20.2, 1.8, 0.8), (0, 0, 0), biseau=0.08, decoupe_x=24)
	figer(sh)
	courber(sh, 10.1, 0.75)
	sh.location = (0, 0, 14.3)
	parts.append(colorier(sh, "vermillon", lisse=False))
	parts.append(colorier(boite("Nuki", (19.4, 0.85, 0.85), (0, 0, 11.2), biseau=0.08), "vermillon", lisse=False))
	parts.append(colorier(boite("Gakuzuka", (0.8, 0.8, 2.4), (0, 0, 12.8), biseau=0.06), "vermillon", lisse=False))
	parts.append(colorier(boite("Plaque", (2.4, 0.5, 2.9), (0, 0, 12.75), biseau=0.1), "prune", lisse=False))
	for s in (-1, 1):
		parts.append(colorier(boite("PlaqueOr", (1.9, 0.1, 2.3), (0, s * 0.27, 12.75), biseau=0.04), "or", lisse=False))
	# shimenawa : corde torsadée en chaînette + 3 shide en zigzag (des deux côtés)
	segs = 40
	brins = []
	for b in range(2):
		pts = []
		for i in range(segs + 1):
			x = -6.9 + 13.8 * i / segs
			z = 10.15 - 0.9 * (1 - (x / 6.9) ** 2)
			a = i * 0.9 + b * math.pi
			pts.append(Vector((x, math.cos(a) * 0.14, z + math.sin(a) * 0.14)))
		cu = bpy.data.curves.new("Corde%d" % b, "CURVE")
		cu.dimensions = "3D"
		cu.bevel_depth = 0.24
		cu.bevel_resolution = 2
		sp = cu.splines.new("POLY")
		sp.points.add(len(pts) - 1)
		for p, q in zip(sp.points, pts):
			p.co = (q.x, q.y, q.z, 1)
		co = bpy.data.objects.new("Corde%d" % b, cu)
		bpy.context.scene.collection.objects.link(co)
		dg = bpy.context.evaluated_depsgraph_get()
		mc = bpy.data.meshes.new_from_object(co.evaluated_get(dg))
		bpy.data.objects.remove(co)
		oc = bpy.data.objects.new("Corde%d" % b, mc)
		bpy.context.scene.collection.objects.link(oc)
		brins.append(colorier(oc, "corde"))
	parts += brins
	for x in (-4.2, 0, 4.2):
		z0 = 10.15 - 0.9 * (1 - (x / 6.9) ** 2) - 0.25
		bm = bmesh.new()
		zig = [(0, 0), (0.55, 0), (0.55, -0.55), (0.25, -0.55), (0.25, -1.1), (0.75, -1.1), (0.75, -1.75), (0.45, -1.75), (0.45, -2.3), (0.15, -2.3), (0.15, -1.4), (0, -1.4)]
		vs = [bm.verts.new((x - 0.35 + a, 0, z0 + b)) for a, b in zig]
		f = bm.faces.new(vs)
		bmesh.ops.triangulate(bm, faces=[f])
		ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
		bmesh.ops.translate(bm, verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)], vec=(0, 0.08, 0))
		bmesh.ops.translate(bm, verts=bm.verts, vec=(0, -0.04, 0))
		bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
		parts.append(colorier(objet_bm("Shide", bm), "papier", lisse=False, force=0.4))
	return joindre("Hub_Torii", parts)


# --- lanterne de pierre (tōrō) -----------------------------------------------------------
def lanterne_pierre():
	p = []
	z = 0

	def etage(nom, r1, r2, h, segs=6, teinte="pierre", biseau=0.05):
		nonlocal z
		o = cylindre(nom, r1, r2, h, (0, 0, z + h / 2), segs=segs, biseau=biseau)
		z += h
		p.append(colorier(o, teinte, lisse=False, force=0.9))
		return o

	etage("Socle", 1.25, 1.15, 0.35)
	etage("Socle2", 0.95, 0.85, 0.3)
	etage("Pied", 0.42, 0.38, 1.9, segs=10)
	etage("Collier", 0.55, 0.55, 0.18, segs=10)
	etage("Plateau", 0.95, 1.05, 0.38)
	z_feu = z
	# chambre du feu : 6 montants (le feu Neon est posé dans Studio)
	for k in range(6):
		a = k * math.tau / 6 + math.pi / 6
		o = boite("Montant", (0.22, 0.22, 1.15), (math.cos(a) * 0.72, math.sin(a) * 0.72, z + 0.575), rot=(0, 0, a), biseau=0.03)
		p.append(colorier(o, "pierre", lisse=False))
	z += 1.15
	etage("Linteau", 0.85, 0.85, 0.15)
	# toit hexagonal aux coins relevés
	bm = bmesh.new()
	bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=1.75, radius2=0.35, depth=0.95)
	for v in bm.verts:
		if v.co.z < 0 and Vector((v.co.x, v.co.y)).length > 1.5:
			v.co.z += 0.22
	toit = objet_bm("Toit", bm)
	toit.location = (0, 0, z + 0.45)
	p.append(colorier(toit, "toit", lisse=False))
	for k in range(6):
		a = k * math.tau / 6
		s = sphere("Volute", 0.17, (math.cos(a) * 1.78, math.sin(a) * 1.78, z + 0.2), segs=8, anneaux=6)
		p.append(colorier(s, "toit"))
	z += 0.95
	p.append(colorier(sphere("Hoju", 0.32, (0, 0, z + 0.25), segs=12, anneaux=8, echelle=(1, 1, 1.15)), "pierre"))
	p.append(colorier(cylindre("Pointe", 0.18, 0.0, 0.35, (0, 0, z + 0.65), segs=10), "pierre"))
	ob = joindre("Hub_LanternePierre", p)
	return ob, z_feu


# --- lanterne en papier (chōchin) : corps côtelé seul, Neon dans Studio ------------------
def chochin():
	bm = bmesh.new()
	bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=22, radius=1)
	for v in bm.verts:
		t = math.acos(max(-1, min(1, v.co.z)))  # 0..pi
		cote = 1 - 0.045 * (0.5 + 0.5 * math.cos(t * 22))
		v.co.x *= 0.9 * cote
		v.co.y *= 0.9 * cote
		v.co.z *= 1.15
	# ouvertures coupées en haut et en bas (les bagues sont des pièces Studio)
	for v in bm.verts:
		v.co.z = max(-0.95, min(0.95, v.co.z))
	ob = objet_bm("Hub_Chochin", bm)
	colorier(ob, "papier")
	return ob


def apercu(objets):
	sc = bpy.context.scene
	try:
		sc.render.engine = "BLENDER_EEVEE"
	except TypeError:
		sc.render.engine = "BLENDER_EEVEE_NEXT"
	sc.render.resolution_x, sc.render.resolution_y = 1400, 700
	sc.view_settings.view_transform = "Standard"
	monde = bpy.data.worlds.new("Monde")
	monde.use_nodes = True
	bg = next(n for n in monde.node_tree.nodes if n.type == "BACKGROUND")
	bg.inputs[0].default_value = (0.75, 0.82, 0.95, 1)
	bg.inputs[1].default_value = 0.9
	sc.world = monde
	sol = bpy.data.meshes.new("Sol")
	sol.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
	so = bpy.data.objects.new("Sol", sol)
	sc.collection.objects.link(so)
	ms = bpy.data.materials.new("Mat_Sol")
	ms.use_nodes = True
	next(n for n in ms.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.75, 0.48, 0.42, 1)
	sol.materials.append(ms)
	soleil = bpy.data.lights.new("Soleil", "SUN")
	soleil.energy = 3.5
	sl = bpy.data.objects.new("Soleil", soleil)
	sl.rotation_euler = (math.radians(50), 0, math.radians(35))
	sc.collection.objects.link(sl)
	cam = bpy.data.cameras.new("Cam")
	cam.lens = 40
	co = bpy.data.objects.new("Cam", cam)
	sc.collection.objects.link(co)
	sc.camera = co
	(DOSSIER / "apercu").mkdir(exist_ok=True)
	vues = {"ensemble": ((0, -62, 22), (0, 0, 7)), "cerisiers": ((-19.5, -30, 9), (-19.5, 0, 6.5))}
	for nom, (oeil, cible) in vues.items():
		co.location = oeil
		d = Vector(cible) - Vector(oeil)
		co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
		sc.render.filepath = str(DOSSIER / "apercu" / f"{nom}.png")
		bpy.ops.render.render(write_still=True)


def main():
	bpy.ops.wm.read_factory_settings(use_empty=True)
	img = creer_palette()
	mat = materiau(img)
	objets = []
	ca = cerisier("Hub_CerisierA", 7, "sakura")
	cb = cerisier("Hub_CerisierB", 23, "sakura2")
	to = torii()
	lp, z_feu = lanterne_pierre()
	ch = chochin()
	positions = {ca: (-26, 0), cb: (-13, 0), to: (4, 0), lp: (18, 0), ch: (24, 0)}
	infos = {}
	for ob, (x, y) in positions.items():
		ob.data.materials.clear()
		ob.data.materials.append(mat)
		# origine au centre de la boîte englobante (comme le pivot d'un MeshPart)
		vs = np.array([v.co[:] for v in ob.data.vertices])
		mn, mx = vs.min(0), vs.max(0)
		c = (mn + mx) / 2
		ob.data.transform(Matrix.Translation(Vector(-c)))
		ob.location = (x, y, c[2])
		taille = mx - mn
		infos[ob.name] = {
			# axes Roblox : X = X, Y = Z Blender, Z = -Y Blender
			"taille_roblox": [round(float(taille[0]), 3), round(float(taille[2]), 3), round(float(taille[1]), 3)],
			"centre_au_dessus_du_sol": round(float(c[2] - mn[2]), 3),
			"triangles": triangles(ob),
		}
		objets.append(ob)
	infos["Hub_LanternePierre"]["feu"] = {"bas": round(z_feu, 3), "hauteur": 1.15, "rayon": 0.62}
	(DOSSIER / "fbx").mkdir(exist_ok=True)
	for o in bpy.context.scene.objects:
		o.select_set(o in objets)
	bpy.ops.export_scene.fbx(filepath=str(DOSSIER / "fbx" / "decor_hub.fbx"), use_selection=True, object_types={"MESH"},
		axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_ALL", path_mode="COPY", embed_textures=True,
		mesh_smooth_type="FACE")
	(DOSSIER / "decor_hub.json").write_text(json.dumps(infos, indent="\t", ensure_ascii=False), encoding="utf-8")
	print(json.dumps(infos, ensure_ascii=False))
	if "apercu" in ARGS:
		apercu(objets)
	bpy.ops.wm.save_as_mainfile(filepath=str(DOSSIER / "decor_hub.blend"))


main()
