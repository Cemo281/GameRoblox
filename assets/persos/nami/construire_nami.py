"""Construit les cheveux, la tenue et les accessoires de nami sur la copie du mannequin v2 (nami.blend).

A lancer DANS Blender (MCP Blender), nami.blend ouvert :
	exec(open(r"<depot>/assets/persos/nami/construire_nami.py", encoding="utf-8").read())
	cheveux()     # mèches 3D (Cheveux_Head sur Head, Cheveux_Dos sur UpperTorso)
	tenue()       # haut vert, jean, sandales, bracelets
	accessoires() # Acc_Baton (visible), Acc_Bourse et Acc_Carte (caches)

Chaque morceau est un objet <Piece>_<Nom> parente en rigide a l'os de sa piece R15 ; la fusion dans les pieces
se fait a l'export. Repere du mannequin : 1 unite = 1 stud, le perso regarde vers -Y, sa droite est -X, pieds a Z = 0.
"""

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

DOSSIER = Path(r"C:\Users\alice\Documents\GameRoblox\assets\persos\nami")
RIG = json.loads((DOSSIER.parent / "_mannequin" / "r15_bloc.json").read_text(encoding="utf-8"))
ART = RIG["blender"]["articulations"]

COULEURS = {
	"Cheveux": "#F28C28",
	"Haut": "#2E9E7A",
	"Jean": "#4A7DB5",
	"Or": "#E8B93A",
	"Verre": "#BFE8F5",
	"Sandale": "#7A4E2D",
	"Baton": "#6FC3E8",
	"BatonBague": "#3A8FC4",
	"Papier": "#F2E6C4",
	"Ruban": "#C8342C",
	"Ceinture": "#2B2B30",
	"Clou": "#EDEDED",
}


def hex_rgb(h):
	h = h.lstrip("#")
	return tuple((int(h[i : i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))


def materiau(nom):
	"""Materiau de blockout (couleur unie) ; remplace par les textures a l'etape « modele final »."""
	m = bpy.data.materials.get("Mat_" + nom)
	if m is None:
		m = bpy.data.materials.new("Mat_" + nom)
		m.use_nodes = True
		bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
		c = hex_rgb(COULEURS[nom])
		bsdf.inputs["Base Color"].default_value = (*c, 1)
		bsdf.inputs["Roughness"].default_value = 0.7
		m.diffuse_color = (*c, 1)
	return m


TAILLES = {}  # {id de meche: (largeur, longueur)} de l'objet en cours (lu par uv_nami.py)


def objet(nom, bm, mat, piece):
	"""bmesh -> objet lisse, parente en rigide a l'os de la piece (remplace l'objet du meme nom)."""
	ancien = bpy.data.objects.get(nom)
	if ancien is not None:
		bpy.data.objects.remove(ancien, do_unlink=True)
	me = bpy.data.meshes.new(nom)
	bm.to_mesh(me)
	bm.free()
	for p in me.polygons:
		p.use_smooth = True
	o = bpy.data.objects.new(nom, me)
	bpy.context.scene.collection.objects.link(o)
	o.data.materials.append(materiau(mat))
	if TAILLES:
		o["tailles_meches"] = json.dumps(TAILLES)
		TAILLES.clear()
	parenter(o, piece)
	return o


def parenter(o, os_nom):
	rig = bpy.data.objects["Rig_R15"]
	bpy.context.view_layer.update()
	mw = o.matrix_world.copy()
	o.parent = rig
	o.parent_type = "BONE"
	o.parent_bone = os_nom
	pb = rig.pose.bones[os_nom]
	o.matrix_parent_inverse = (rig.matrix_world @ pb.bone.matrix_local @ Matrix.Translation((0, pb.bone.length, 0))).inverted()
	o.matrix_basis = mw


# ---------------------------------------------------------------- primitives


def calque_uv(bm):
	"""Un seul calque UV, nomme UVMap (comme la tete du mannequin : la calotte des cheveux garde ses UV)."""
	return bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")


def spline(points, n):
	"""Catmull-Rom passant par les points, n echantillons."""
	P = [Vector(p) for p in points]
	P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
	res = []
	segs = len(P) - 3
	for k in range(n):
		t = k / (n - 1) * segs
		i = min(int(t), segs - 1)
		u = t - i
		p0, p1, p2, p3 = P[i : i + 4]
		res.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u**3))
	return res


def meche(bm, points, largeur, epaisseur, cote, n=10, sections=4, profil=None):
	"""Tube a section en lentille le long d'une spline, qui s'affine en pointe.

	cote : direction de la largeur (vecteur), corrigee pour rester perpendiculaire a la mèche.
	profil(t) -> facteur de largeur (t = 0 a la racine, 1 a la pointe).
	UV : u = tour de la section (0,25 = face exterieure, 0,75 = face interieure), v = longueur.
	"""
	profil = profil or (lambda t: (1 - t**1.6) ** 0.8 if t < 1 else 0.0)
	uv = calque_uv(bm)
	id_meche = bm.faces.layers.int.get("meche") or bm.faces.layers.int.new("meche")
	num = max((f[id_meche] for f in bm.faces), default=0) + 1
	c = spline(points, n)
	TAILLES[num] = (round(largeur + epaisseur, 3), round(sum((c[k + 1] - c[k]).length for k in range(n - 1)), 3), "ruban")
	anneaux = []
	for k, p in enumerate(c):
		t = k / (n - 1)
		T = (c[min(k + 1, n - 1)] - c[max(k - 1, 0)]).normalized()
		S = Vector(cote) - T * Vector(cote).dot(T)
		S.normalize()
		N = T.cross(S)
		f = profil(t)
		if f <= 0.001:
			anneaux.append([bm.verts.new(p)])
			continue
		a = []
		for j in range(sections):
			ang = 2 * math.pi * j / sections
			a.append(bm.verts.new(p + S * (math.cos(ang) * largeur * f / 2) + N * (math.sin(ang) * epaisseur * max(f, 0.35) / 2)))
		anneaux.append(a)
	for k in range(n - 1):
		A, B = anneaux[k], anneaux[k + 1]
		for j in range(sections):
			j2 = (j + 1) % sections
			u0, u1 = j / sections, (j + 1) / sections
			v0, v1 = k / (n - 1), (k + 1) / (n - 1)
			# ordre (A[j], A[j2], ...) : normales vers l'exterieur de la meche
			if len(B) == 1:
				f = bm.faces.new((A[j], A[j2], B[0]))
				coords = [(u0, v0), (u1, v0), ((u0 + u1) / 2, v1)]
			else:
				f = bm.faces.new((A[j], A[j2], B[j2], B[j]))
				coords = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
			f[id_meche] = num
			for l, co in zip(f.loops, coords):
				l[uv].uv = co
	if len(anneaux[0]) > 1:
		f = bm.faces.new(anneaux[0][::-1])
		f[id_meche] = num
		for l in f.loops:
			l[uv].uv = (0.5, 0.0)


def boite_arrondie(bm, centre, taille, biseau=0.05, segments=2):
	"""Boite aux aretes arrondies, ajoutee a bm."""
	tmp = bmesh.new()
	bmesh.ops.create_cube(tmp, size=1.0)
	tmp.transform(Matrix.Translation(centre) @ Matrix.Diagonal((*taille, 1)))
	bmesh.ops.bevel(tmp, geom=list(tmp.edges), offset=min(biseau, 0.45 * min(taille)), segments=segments, profile=0.5, affect="EDGES")
	me = bpy.data.meshes.new("tmp")
	tmp.to_mesh(me)
	tmp.free()
	bm.from_mesh(me)
	bpy.data.meshes.remove(me)


def cylindre(bm, a, b, r1, r2=None, segments=16, bouchons=True):
	"""Cylindre (ou cone) de a vers b."""
	a, b = Vector(a), Vector(b)
	axe = b - a
	tmp = bmesh.new()
	bmesh.ops.create_cone(tmp, cap_ends=bouchons, cap_tris=False, segments=segments, radius1=r1, radius2=r1 if r2 is None else r2, depth=axe.length)
	rot = Vector((0, 0, 1)).rotation_difference(axe.normalized()).to_matrix().to_4x4()
	tmp.transform(Matrix.Translation((a + b) / 2) @ rot)
	me = bpy.data.meshes.new("tmp")
	tmp.to_mesh(me)
	tmp.free()
	bm.from_mesh(me)
	bpy.data.meshes.remove(me)


def sphere(bm, centre, rayon, echelle=(1, 1, 1), segments=12, anneaux=8):
	tmp = bmesh.new()
	bmesh.ops.create_uvsphere(tmp, u_segments=segments, v_segments=anneaux, radius=1.0)
	tmp.transform(Matrix.Translation(centre) @ Matrix.Diagonal((rayon * echelle[0], rayon * echelle[1], rayon * echelle[2], 1)))
	me = bpy.data.meshes.new("tmp")
	tmp.to_mesh(me)
	tmp.free()
	bm.from_mesh(me)
	bpy.data.meshes.remove(me)


def tore(bm, centre, axe, R, r, segments=24, tour=8, ecrase=1.0):
	"""Anneau (bracelet) d'axe donne ; ecrase < 1 aplatit la section dans le sens de l'axe."""
	tmp = bmesh.new()
	vs = []
	for i in range(segments):
		a = 2 * math.pi * i / segments
		ligne = []
		for j in range(tour):
			b = 2 * math.pi * j / tour
			rr = R + r * math.cos(b)
			ligne.append(tmp.verts.new((rr * math.cos(a), rr * math.sin(a), r * math.sin(b) * ecrase)))
		vs.append(ligne)
	for i in range(segments):
		for j in range(tour):
			i2, j2 = (i + 1) % segments, (j + 1) % tour
			tmp.faces.new((vs[i][j], vs[i2][j], vs[i2][j2], vs[i][j2]))
	rot = Vector((0, 0, 1)).rotation_difference(Vector(axe).normalized()).to_matrix().to_4x4()
	tmp.transform(Matrix.Translation(centre) @ rot)
	me = bpy.data.meshes.new("tmp")
	tmp.to_mesh(me)
	tmp.free()
	bm.from_mesh(me)
	bpy.data.meshes.remove(me)


# ---------------------------------------------------------------- corps (blocs peu arrondis) et tete en bloc

BISEAU_CORPS = 0.05  # arrondi des aretes (0,15 du mannequin v2 : effet « bouee »)
TETE_TAILLE = (1.2, 1.16, 1.182)  # x, y, z (meme hauteur et meme centre que la tete R15)
BISEAU_TETE = 0.2


def corps():
	"""Remplace les 15 pieces du mannequin par des blocs a peine arrondis et la tete par un bloc arrondi (face plate)."""
	m = {"__name__": "mannequin"}
	exec(open(DOSSIER.parent / "_mannequin" / "construire_mannequin.py", encoding="utf-8").read(), m)
	m["BISEAU"], m["SEGMENTS"] = BISEAU_CORPS, 2
	rig = bpy.data.objects["Rig_R15"]
	for pb in rig.pose.bones:
		pb.rotation_euler = (0, 0, 0)
		pb.location = (0, 0, 0)
	bpy.context.view_layer.update()
	for nom in m["NOMS"]:
		ancien = bpy.data.objects.get(nom)
		if ancien is not None:
			bpy.data.objects.remove(ancien, do_unlink=True)
		o = m["bloc_arrondi"](nom)
		if nom[4 if nom.startswith("Left") else 5 :] in m["JOINTURES"]:
			j, _ = m["jointure"](nom)
			with bpy.context.temp_override(active_object=o, object=o, selected_objects=[o, j], selected_editable_objects=[o, j]):
				bpy.ops.object.join()
		m["origine"](o, ART[m["MOTOR_DE"][nom]])
		m["parenter"](o, rig, nom)
	ancien = bpy.data.objects.get("Head")
	if ancien is not None:
		bpy.data.objects.remove(ancien, do_unlink=True)
	bm = bmesh.new()
	boite_arrondie(bm, TETE_C, TETE_TAILLE, BISEAU_TETE, 4)
	me = bpy.data.meshes.new("Head")
	bm.to_mesh(me)
	bm.free()
	for p in me.polygons:
		p.use_smooth = True
	o = bpy.data.objects.new("Head", me)
	bpy.context.scene.collection.objects.link(o)
	m["origine"](o, ART["Neck"])
	m["parenter"](o, rig, "Head")
	for o in bpy.data.objects:
		if o.type == "MESH":
			o.data.update()
	print("corps reconstruit (biseau %.2f), tete en bloc %s" % (BISEAU_CORPS, TETE_TAILLE))


# ---------------------------------------------------------------- cheveux

TETE_C = Vector((0, 0, 4.867))


def surface_tete():
	"""Renvoie f(direction, decalage) -> point de la surface de Head (monde) le long de la direction depuis son centre, + decalage."""
	from mathutils.bvhtree import BVHTree

	tete = bpy.data.objects["Head"]
	bvh = BVHTree.FromObject(tete, bpy.context.evaluated_depsgraph_get())
	inv = tete.matrix_world.inverted()

	def f(d, decalage=0.0):
		d = Vector(d).normalized()
		o = inv @ (TETE_C + d * 3)
		hit = bvh.ray_cast(o, (inv.to_3x3() @ -d).normalized())
		p = tete.matrix_world @ hit[0]
		return p + d * decalage

	return f


def dir_sph(azimut, elevation):
	"""azimut 0 = avant (-Y), 90 = gauche du perso (+X), 180 = arriere ; elevation en degres."""
	a, e = math.radians(azimut), math.radians(elevation)
	return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def lisse(a, b, x):
	t = min(1.0, max(0.0, (x - a) / (b - a)))
	return t * t * (3 - 2 * t)


def racine(x):
	"""Hauteur (relative au centre de la tete) de la racine des cheveux sur l'avant, x relatif."""
	return 0.31 - 0.3 * lisse(0.38, 0.6, abs(x))


def calotte(bm):
	"""Copie agrandie de la tete : masse de base sous les nappes. Sur le visage, les sommets rentrent sous la peau
	(poids continu) : le bord visible suit une courbe lisse au lieu des marches de la grille."""
	tete = bpy.data.objects["Head"]
	tmp = bmesh.new()
	tmp.from_mesh(tete.data)
	tmp.transform(tete.matrix_world)
	bmesh.ops.subdivide_edges(tmp, edges=tmp.edges[:], cuts=2, use_grid_fill=True)
	for v in tmp.verts:
		r = v.co - TETE_C
		visage = lisse(-0.3, -0.5, r.y) * lisse(0.03, -0.03, r.z - racine(r.x))
		dome = 0.03 * lisse(0.25, 0.55, r.z) * max(0.0, 1 - (r.x**2 + r.y**2) / 0.75)  # dessus arrondi (volume)
		dehors = Vector((r.x * 1.1, r.y * 1.1 + 0.02, r.z * 1.07 + 0.04 + dome))
		v.co = TETE_C + dehors.lerp(r * 0.92, visage)
		v.tag = visage > 0.99
	enlever = [f for f in tmp.faces if all(v.tag for v in f.verts) or (f.calc_center_median() - TETE_C).z < -0.45]
	bmesh.ops.delete(tmp, geom=enlever, context="FACES")
	me = bpy.data.meshes.new("tmp")
	tmp.to_mesh(me)
	tmp.free()
	o = bpy.data.objects.new("tmp", me)
	bpy.context.scene.collection.objects.link(o)
	m = o.modifiers.new("Decimer", "DECIMATE")
	m.ratio = 0.35
	dg = bpy.context.evaluated_depsgraph_get()
	tmp = bmesh.new()
	tmp.from_object(o, dg)
	bpy.data.objects.remove(o, do_unlink=True)
	bpy.data.meshes.remove(me)
	me = bpy.data.meshes.new("tmp")
	tmp.to_mesh(me)
	tmp.free()
	bm.from_mesh(me)
	bpy.data.meshes.remove(me)


def nappe(bm, P, nu, nv, epaisseur, centre, vmax=lambda u: 1.0):
	"""Nappe de cheveux lisse et epaisse : surface P(u, v) (u en travers, v de la racine a la pointe), bord du bas
	decoupe par vmax(u) (pointes), epaisseur qui s'affine vers les pointes. centre(v) : point a l'interieur de la
	nappe, pour orienter les normales vers l'exterieur. UV : (u, v) dans [0, 1]."""
	uv = calque_uv(bm)
	id_meche = bm.faces.layers.int.get("meche") or bm.faces.layers.int.new("meche")
	id_int = bm.faces.layers.int.get("interieur") or bm.faces.layers.int.new("interieur")
	num = max((f[id_meche] for f in bm.faces), default=0) + 1
	grille = []
	for j in range(nu + 1):
		u = j / nu
		col = []
		for i in range(nv + 1):
			v = i / nv * vmax(u)
			p = P(u, v)
			du = P(min(u + 0.01, 1), v) - P(max(u - 0.01, 0), v)
			dv = P(u, min(v + 0.01, 1)) - P(u, max(v - 0.01, 0))
			n = du.cross(dv).normalized()
			if n.dot(p - centre(v)) < 0:
				n = -n
			e = epaisseur * (1 - 0.75 * (i / nv) ** 3) / 2
			col.append((p + n * e, p - n * e, (u, v)))
		grille.append(col)
	ext = [[bm.verts.new(c[0]) for c in col] for col in grille]
	inte = [[bm.verts.new(c[1]) for c in col] for col in grille]

	def face(vs, uvs, interieur=0):
		"""interieur = 1 : dessous et bords de la nappe (uv_nami.py les met sur la pastille foncee)."""
		f = bm.faces.new(vs)
		f[id_meche] = num
		f[id_int] = interieur
		for l, t in zip(f.loops, uvs):
			l[uv].uv = t
		return f

	nouvelles = []
	for j in range(nu):
		for i in range(nv):
			c = [grille[j][i][2], grille[j][i + 1][2], grille[j + 1][i + 1][2], grille[j + 1][i][2]]
			nouvelles.append(face((ext[j][i], ext[j][i + 1], ext[j + 1][i + 1], ext[j + 1][i]), c))
			nouvelles.append(face((inte[j + 1][i], inte[j + 1][i + 1], inte[j][i + 1], inte[j][i]), c[::-1], 1))
	for j in range(nu):  # bords du haut et du bas
		for i in (0, nv):
			c = [grille[j][i][2], grille[j + 1][i][2], grille[j + 1][i][2], grille[j][i][2]]
			nouvelles.append(face((ext[j][i], ext[j + 1][i], inte[j + 1][i], inte[j][i]), c, 1))
	for j in (0, nu):  # cotes
		for i in range(nv):
			c = [grille[j][i][2], grille[j][i + 1][2], grille[j][i + 1][2], grille[j][i][2]]
			nouvelles.append(face((ext[j][i], ext[j][i + 1], inte[j][i + 1], inte[j][i]), c, 1))
	bmesh.ops.recalc_face_normals(bm, faces=nouvelles)
	largeur = sum((P((j + 1) / nu, 0.5) - P(j / nu, 0.5)).length for j in range(nu))
	longueur = max(sum((P(j / nu, (i + 1) / nv) - P(j / nu, i / nv)).length for i in range(nv)) for j in range(nu + 1))
	TAILLES[num] = (round(largeur + 2 * epaisseur, 3), round(longueur, 3), "nappe")


def pointes(n, creux=0.12, decalage=0.0):
	"""vmax(u) en dents de scie : n pointes (v = 1) separees par des creux (v = 1 - creux)."""
	return lambda u: 1 - creux * abs(math.sin(math.pi * (u * n + decalage)))


LARGE = lambda t: (1 - t**3) ** 0.7  # meche qui reste large et finit en pointe nette


def ruban(bm, points, largeur, cote, n=10):
	"""Meche plate (ruban lisse, pointe nette) : section en lentille aplatie a 6 cotes."""
	meche(bm, points, largeur, 0.055, cote, n=n, sections=6, profil=LARGE)


def cheveux():
	S = surface_tete()
	TAILLES.clear()
	bm = bmesh.new()
	calque_uv(bm)
	calotte(bm)
	TAILLES[0] = (6.0, 1.2, "calotte")  # tour de tete x hauteur (UV : azimut, hauteur ; voir uv_nami.py)
	raie = S(dir_sph(25, 70), 0.1)  # raie sur le cote gauche du perso
	# frange en rubans plats, pointes au-dessus des yeux (plus longue au milieu), balayee vers la droite du perso
	for x, zb, l in [(0.36, 0.15, 0.42), (0.15, 0.07, 0.44), (-0.06, 0.11, 0.44), (-0.27, 0.16, 0.42), (-0.47, 0.09, 0.36)]:
		bout = TETE_C + Vector((x, -0.635, zb))
		haut = TETE_C + Vector((x * 0.75 + 0.08, -0.66, racine(x) + 0.12))
		dessus = S(dir_sph(10 + x * 40, 48), 0.09)
		ruban(bm, [raie, dessus, haut, bout], l, (1, 0, -0.35))
	# meches qui encadrent le visage et tombent devant les clavicules (rubans plats)
	for cote in (1, -1):
		for k, (x, l) in enumerate([(0.58, 0.36), (0.74, 0.36)]):
			pts = [
				S(dir_sph(62 * cote, 40), 0.06),
				TETE_C + Vector((x * cote, -0.6 + 0.08 * k, 0.05)),
				TETE_C + Vector((x * cote, -0.66 + 0.08 * k, -0.45)),
				Vector((x * cote, -0.64 + 0.04 * k, 3.95 + 0.08 * k)),
				Vector(((x - 0.04) * cote, -0.66 + 0.04 * k, 3.82 + 0.1 * k)),
			]
			ruban(bm, pts, l, (1, 0, 0), n=12)

	# nappe de la tete : cotes et arriere, du crane jusqu'au-dessus des epaules, evasee, pointes en dents de scie
	def P_tete(u, v):
		az = 68 + (292 - 68) * u
		# part du sommet et passe au-dessus de la calotte (points a la surface du crane + 0,2) : pas de rebord
		pts = [S(dir_sph(az, el), 0.2) for el in (78, 55, 30, 5)]
		rayon = Vector((pts[0].x, pts[0].y, 0)).normalized()
		pts.append(rayon * (0.98 + 0.08 * math.sin(math.pi * u)) + Vector((0, 0, 4.36)))
		c = spline(pts, 41)
		t = v * 40
		k = min(int(t), 39)
		return c[k].lerp(c[k + 1], t - k)

	nappe(bm, P_tete, 24, 6, 0.09, lambda v: Vector((0, 0, 4.4 + 0.5 * (1 - v))), pointes(9, 0.18))
	objet("Head_Cheveux", bm, "Cheveux", "Head")

	# nappe du dos (UpperTorso) : deux couches lisses, legerement bombees et evasees, pointes en dents de scie
	bm = bmesh.new()
	calque_uv(bm)
	for couche, (y0, z0, z1, n, creux) in enumerate([(0.6, 4.45, 2.62, 6, 0.1), (0.7, 4.5, 2.45, 8, 0.14)]):

		def P_dos(u, v, y0=y0, z0=z0, z1=z1):
			lx = 0.85 + 0.2 * v
			y = y0 + 0.16 * math.cos((u - 0.5) * math.pi) + 0.06 * math.sin(math.pi * v) + 0.08 * v**3
			return Vector(((u - 0.5) * 2 * lx, y, z0 + (z1 - z0) * v))

		nappe(bm, P_dos, 16, 8, 0.08, lambda v: Vector((0, 0.2, 3.5)), pointes(n, creux, 0.5 * couche))
	objet("UpperTorso_Cheveux", bm, "Cheveux", "UpperTorso")


# ---------------------------------------------------------------- tenue

PLEIN = lambda t: 1.0


def anneau_arrondi(cx, cy, dx, dy, r, n):
	"""n points (x, y) d'un rectangle aux coins arrondis, a longueur d'arc egale, depart a l'avant (-Y) au centre."""
	r = min(r, dx, dy)
	pts = []
	for i in range(400):
		a = 2 * math.pi * i / 400 - math.pi / 2  # depart vers -Y
		ux, uy = math.cos(a), math.sin(a)
		# point du rectangle arrondi dans la direction (ux, uy) par dichotomie sur le rayon
		lo, hi = 0.0, 3.0
		for _ in range(30):
			m = (lo + hi) / 2
			x, y = abs(ux * m), abs(uy * m)
			qx, qy = max(x - (dx - r), 0), max(y - (dy - r), 0)
			dedans = (x <= dx and y <= dy) and (qx * qx + qy * qy <= r * r)
			lo, hi = (m, hi) if dedans else (lo, m)
		pts.append(Vector((cx + ux * lo, cy + uy * lo)))
	longueurs = [0.0]
	for i in range(1, 401):
		longueurs.append(longueurs[-1] + (pts[i % 400] - pts[i - 1]).length)
	res, j = [], 0
	for k in range(n):
		cible = longueurs[-1] * k / n
		while longueurs[j + 1] < cible:
			j += 1
		t = (cible - longueurs[j]) / max(longueurs[j + 1] - longueurs[j], 1e-9)
		res.append(pts[j].lerp(pts[(j + 1) % 400], t))
	return res


def manchon(bm, cx, cy, dx, dy, z_bas, z_haut, epais, coin=0.07, n=32, rangs=2, evase=None):
	"""Bande epaisse autour d'un bloc (vetement) : face interne au ras du bloc, externe a +epais, bords fermes.

	z_bas, z_haut : nombre ou fonction (x, y) -> z. evase(t) -> decalage en plus (t = 0 en bas, 1 en haut).
	UV : u = tour (0 = avant centre), v = hauteur.
	"""
	uv = calque_uv(bm)
	fz = lambda f: f if callable(f) else (lambda x, y: f)
	zb, zh = fz(z_bas), fz(z_haut)
	evase = evase or (lambda t: 0.0)
	contour = anneau_arrondi(cx, cy, dx, dy, coin, n)
	centre = Vector((cx, cy))
	def point(p, t, dec):
		d = (p - centre).normalized()
		q = p + d * (dec + evase(t))
		return bm.verts.new((q.x, q.y, zb(p.x, p.y) + (zh(p.x, p.y) - zb(p.x, p.y)) * t))

	externe = [[point(p, i / rangs, epais) for p in contour] for i in range(rangs + 1)]
	bords = [[point(p, 0.0, 0.0) for p in contour], [point(p, 1.0, 0.0) for p in contour]]

	def quad(a, b, c, d, coords):
		f = bm.faces.new((a, b, c, d))
		for l, co in zip(f.loops, coords):
			l[uv].uv = co

	for i in range(rangs):
		for k in range(n):
			k2 = (k + 1) % n
			u0, u1, v0, v1 = k / n, (k + 1) / n, i / rangs, (i + 1) / rangs
			quad(externe[i][k], externe[i][k2], externe[i + 1][k2], externe[i + 1][k], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
	# bords (epaisseur du tissu) : interieur au ras du bloc
	for k in range(n):
		k2 = (k + 1) % n
		a, b = bords[0][k], bords[0][k2]
		quad(a, b, externe[0][k2], externe[0][k], [(k / n, 0), ((k + 1) / n, 0), ((k + 1) / n, 0.02), (k / n, 0.02)])
		a, b = bords[1][k], bords[1][k2]
		quad(externe[rangs][k], externe[rangs][k2], b, a, [(k / n, 0.98), ((k + 1) / n, 0.98), ((k + 1) / n, 1), (k / n, 1)])


def jambe_cote(nom):
	return 1 if nom.startswith("Left") else -1


def tenue():
	# haut couvrant (UpperTorso) facon haut de sport : bande du torse, decollete arrondi devant, bretelles fines
	# (le bikini a ete retire : avertissement de moderation Roblox)
	bm = bmesh.new()
	haut_z = lambda x, y: 4.06 - (0.1 * math.cos(x / 0.62 * math.pi / 2) if (y < 0 and abs(x) < 0.62) else 0.0) - (0.04 if y > 0 else 0.0)
	manchon(bm, 0, 0, 0.972, 0.502, 3.42, haut_z, 0.05, rangs=3)
	for cote in (1, -1):
		x = 0.5 * cote
		meche(bm, [(x, -0.56, 3.97), (x, -0.545, 4.24), (x, -0.25, 4.335), (x, 0.25, 4.335), (x, 0.545, 4.24), (x, 0.56, 4.0)], 0.1, 0.05, (1, 0, 0), n=10, sections=4, profil=PLEIN)
	objet("UpperTorso_Haut", bm, "Haut", "UpperTorso")

	# jean : ceinture basse (LowerTorso), cuisses, mollets evases jusqu'a la cheville
	bm = bmesh.new()
	manchon(bm, 0, 0, 0.996, 0.502, 2.17, 2.7, 0.045)
	manchon(bm, 0, 0, 1.04, 0.546, 2.58, 2.72, 0.035, rangs=1)  # ceinture
	for x in (-0.75, -0.3, 0.3, 0.75):
		boite_arrondie(bm, (x, -0.6, 2.645), (0.07, 0.04, 0.17), 0.015, 1)  # passants
	for x in (-0.7, 0, 0.7):
		boite_arrondie(bm, (x, 0.6, 2.645), (0.07, 0.04, 0.17), 0.015, 1)
	objet("LowerTorso_Jean", bm, "Jean", "LowerTorso")
	bm = bmesh.new()
	cylindre(bm, (0, -0.635, 2.645), (0, -0.605, 2.645), 0.045, segments=12)
	cylindre(bm, (0, -0.625, 2.645), (0, -0.66, 2.645), 0.05, segments=12)
	objet("LowerTorso_Bouton", bm, "Or", "LowerTorso")
	# ceinture noire cloutee, portee de travers (plus basse a droite du perso), boucle ronde argentee
	z_c = lambda x: 2.62 + 0.07 * x
	bm = bmesh.new()
	manchon(bm, 0, 0, 1.08, 0.6, lambda x, y: z_c(x) - 0.085, lambda x, y: z_c(x) + 0.085, 0.04, n=40, rangs=1)
	objet("LowerTorso_Ceinture", bm, "Ceinture", "LowerTorso")
	bm = bmesh.new()
	for k in range(-5, 6):
		x = k * 0.19
		if abs(x) < 0.12:
			continue
		cylindre(bm, (x, -0.635, z_c(x)), (x, -0.66, z_c(x)), 0.048, segments=10)
	for cote in (1, -1):
		for y in (-0.38, -0.19, 0.0, 0.19, 0.38):
			x = 1.11 * cote
			x = 1.12 * cote
			cylindre(bm, (x - 0.005 * cote, y, z_c(x)), (x + 0.025 * cote, y, z_c(x)), 0.048, segments=10)
	tore(bm, (0, -0.665, z_c(0)), (0, 1, 0), 0.1, 0.028, segments=16, tour=6)
	objet("LowerTorso_Clous", bm, "Clou", "LowerTorso")
	for cote, nom in ((1, "Left"), (-1, "Right")):
		x = 0.4979 * cote
		bm = bmesh.new()
		manchon(bm, x, 0, 0.496, 0.486, 1.26, 2.42, 0.04)
		objet(nom + "UpperLeg_Jean", bm, "Jean", nom + "UpperLeg")
		bm = bmesh.new()
		manchon(bm, x, 0, 0.492, 0.486, 0.3, 1.34, 0.04, rangs=3, evase=lambda t: 0.05 * (1 - t) ** 3)
		cylindre(bm, (x - 0.47, 0, 1.2718), (x + 0.47, 0, 1.2718), 0.5, segments=20, bouchons=False)  # genou (jointure)
		objet(nom + "LowerLeg_Jean", bm, "Jean", nom + "LowerLeg")
		# chaussure fermee (le pied de l'avatar Roblox fait 1,009 x 1,001 x 0,312 : on l'enveloppe entierement),
		# semelle qui deborde, talon a l'arriere, bride sur le dessus du pied
		bm = bmesh.new()
		boite_arrondie(bm, (x, -0.01, 0.175), (1.07, 1.07, 0.35), 0.06, 2)
		boite_arrondie(bm, (x, -0.02, 0.03), (1.11, 1.12, 0.06), 0.025, 1)  # semelle
		boite_arrondie(bm, (x, 0.42, 0.06), (0.62, 0.26, 0.12), 0.03, 1)  # talon
		meche(bm, [(x - 0.55, -0.1, 0.22), (x - 0.42, -0.555, 0.33), (x + 0.42, -0.555, 0.33), (x + 0.55, -0.1, 0.22)], 0.1, 0.03, (0, 0, 1), n=8, profil=PLEIN)
		objet(nom + "Foot_Sandale", bm, "Sandale", nom + "Foot")

	# bracelets dores et bracelet-boussole au poignet gauche (LeftLowerArm)
	bm = bmesh.new()
	for z in (2.53, 2.61):
		manchon(bm, 1.4725, 0, 0.5, 0.5, z, z + 0.05, 0.035, n=24, rangs=1)
	manchon(bm, 1.4725, 0, 0.5, 0.5, 2.68, 2.8, 0.03, n=24, rangs=1)
	cylindre(bm, (1.4725, -0.53, 2.74), (1.4725, -0.6, 2.74), 0.13, segments=14)
	objet("LeftLowerArm_Bracelets", bm, "Or", "LeftLowerArm")
	bm = bmesh.new()
	sphere(bm, (1.4725, -0.6, 2.74), 0.1, (1, 0.7, 1), segments=12, anneaux=6)
	objet("LeftLowerArm_Boussole", bm, "Verre", "LeftLowerArm")


BATON_L = 5.5
BATON_SOUS_MAIN = 3.3  # longueur sous la main (pose 0 : main a hauteur du coude, bout au sol)


def bourse(bm, centre, profil, plis=9, n_tour=24, n_haut=20):
	"""Sachet de tissu : surface de revolution (profil [(z, rayon)] de bas en haut) avec des plis radiaux, plus
	marques pres du col et dans la collerette."""
	cx, cy = centre
	zs = [z for z, _ in profil]
	pts = spline([(0, z, r) for z, r in profil], n_haut)
	anneaux = []
	for k, p in enumerate(pts):
		z, r = p.y, max(p.z, 0.0)
		t = (z - zs[0]) / (zs[-1] - zs[0])
		amplitude = 0.03 + 0.09 * lisse(0.55, 0.85, t)  # plis plus marques vers le col
		ligne = []
		for i in range(n_tour):
			a = 2 * math.pi * i / n_tour
			rr = r * (1 + amplitude * math.sin(plis * a + 1.3 * t))
			ligne.append(bm.verts.new((cx + rr * math.cos(a), cy + rr * math.sin(a), z)))
		anneaux.append(ligne)
	for k in range(n_haut - 1):
		for i in range(n_tour):
			i2 = (i + 1) % n_tour
			bm.faces.new((anneaux[k][i], anneaux[k][i2], anneaux[k + 1][i2], anneaux[k + 1][i]))
	bm.faces.new(anneaux[0][::-1])
	bm.faces.new(anneaux[-1])
	bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def cacher(*noms):
	for n in noms:
		o = bpy.data.objects[n]
		o["VisibleParDefaut"] = False
		o.hide_viewport = o.hide_render = True


def accessoires():
	# Acc_Baton : perpendiculaire a l'avant-bras (comme un outil Roblox), le long de Y a la pose de repos :
	# coude plie de 90 deg vers l'avant, il devient vertical, le bout arriere (+Y) en bas, plante au sol.
	x, z = -1.4721, 2.33
	bas, haut = BATON_SOUS_MAIN, BATON_L - BATON_SOUS_MAIN
	bm = bmesh.new()
	cylindre(bm, (x, bas - 0.06, z), (x, -haut + 0.06, z), 0.085, segments=12, bouchons=False)
	objet("Acc_Baton", bm, "Baton", "RightHand")
	bm = bmesh.new()
	for d in (BATON_L / 3, 2 * BATON_L / 3):
		y = bas - d
		cylindre(bm, (x, y - 0.09, z), (x, y + 0.09, z), 0.115, segments=12)
	for y in (bas - 0.08, -haut + 0.08):
		sphere(bm, (x, y, z), 0.11, segments=12, anneaux=6)
	objet("Acc_Baton_Bagues", bm, "BatonBague", "RightHand")
	# Acc_Bourse : vrai sachet en tissu dore, tenu par le col dans le poing gauche : panse ronde et plissee qui pend
	# sous la main, col serre par un cordon, collerette froncee qui depasse du poing
	cx, cy = 1.4721, -0.02
	bm = bmesh.new()
	bourse(bm, (cx, cy), [(1.43, 0.0), (1.47, 0.2), (1.56, 0.3), (1.72, 0.34), (1.9, 0.3), (2.03, 0.19), (2.12, 0.09), (2.17, 0.085), (2.24, 0.14), (2.31, 0.17), (2.33, 0.12)])
	objet("Acc_Bourse", bm, "Or", "LeftHand")
	bm = bmesh.new()
	tore(bm, (cx, cy, 2.15), (0, 0, 1), 0.105, 0.028, segments=16, tour=6)
	for dx, dz in ((0.09, -0.02), (0.13, -0.05)):  # deux bouts de cordon qui pendent
		meche(bm, [(cx + 0.08, cy - 0.08, 2.15), (cx + dx + 0.05, cy - 0.14, 2.02 + dz), (cx + dx + 0.08, cy - 0.16, 1.86 + dz)], 0.035, 0.035, (1, 0, 0), n=6, sections=4, profil=PLEIN)
	objet("Acc_Bourse_Cordon", bm, "Ruban", "LeftHand")
	# Acc_Carte : carte deroulee tenue par le haut, deux rouleaux sur les cotes, ruban rouge
	bm = bmesh.new()
	boite_arrondie(bm, (1.4721, -0.25, 1.8), (0.85, 0.02, 0.62), 0.008, 1)
	for dx in (-0.45, 0.45):
		cylindre(bm, (1.4721 + dx, -0.25, 1.47), (1.4721 + dx, -0.25, 2.13), 0.06, segments=12)
	objet("Acc_Carte", bm, "Papier", "LeftHand")
	bm = bmesh.new()
	tore(bm, (1.0221, -0.25, 1.8), (0, 0, 1), 0.07, 0.018, segments=12, tour=4)
	objet("Acc_Carte_Ruban", bm, "Ruban", "LeftHand")
	bpy.data.objects["Acc_Baton"]["VisibleParDefaut"] = True
	cacher("Acc_Bourse", "Acc_Bourse_Cordon", "Acc_Carte", "Acc_Carte_Ruban")
