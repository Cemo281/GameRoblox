"""Tenue d'aventurier sur un rig Roblox R15 bloc (handoff design_handoff_tenue_r15).

Usage (Blender 5.x, sans interface) :
	blender -b --factory-startup --python tools/build_outfit_r15.py

Produit dans export/ :
	salopette.fbx, chaussures.fbx (+ chaussure_gauche.fbx / chaussure_droite.fbx), brassard.fbx
		layered clothing : maillage skinné sur les os R15 + <nom>_InnerCage + <nom>_OuterCage
	chapeau.fbx, cheveux.fbx, sac.fbx : accessoires rigides
	lance_pierre.fbx : Handle du Tool, origine sur la prise
	palette_tenue.png (atlas 16 x 16, 4 x 4 cases de 4 px), offsets.json (attachments, Grip, contrôles),
	tenue_r15.blend (rig, pièces nommées, pièces assemblées)

Repères
	Roblox (relatif au HumanoidRootPart) : Y en haut, le perso regarde vers -Z, sa droite est +X.
	Blender (convention du projet, assets/persos/_mannequin/r15_bloc.json) : (x, y, z) = (-xR, zR, yR + H),
		Z en haut, le perso regarde vers -Y, sa gauche est +X, pieds à z = 0, 1 unité = 1 stud.
	Référence HTML (three.js) : mètres, Y en haut, avant = +Z, gauche = +x. Vers Blender : (x, y, z) -> (x, -z, y),
		mis à l'échelle sur le rig (pas en mètres bruts).
	Export FBX : axis_forward '-Z', axis_up 'Y' : dans le FBX, avant = +Z, gauche = +X, Y en haut (comme les gabarits Roblox).

L'apparence suit les images de assets/references/ quand elles contredisent le HTML (voir les écarts dans
export/IMPORT_STUDIO.md) ; les noms des pièces reprennent ceux du HTML quand le rôle est le même.
"""

import json
import math
import struct
import sys
import time
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector, kdtree
from mathutils.bvhtree import BVHTree

DEBUT = time.time()
RACINE = Path(__file__).resolve().parent.parent
EXPORT = RACINE / "export"
R15 = json.loads((RACINE / "assets/persos/_mannequin/r15_bloc.json").read_text(encoding="utf-8"))
GABARIT_CAGE = RACINE / "tools/cages_roblox/Clothing_Cage_Template.blend"
CAGES_CORPS = RACINE / "tools/cages_roblox/corps_bloc"

H = R15["hauteurHRP"]  # hauteur du HumanoidRootPart au-dessus des pieds (studs)

# Brassard : la référence le montre sous le coude (avant-bras) ; le README le mappe sur LeftUpperArm.
BRASSARD_OS = "LeftLowerArm"  # ou "LeftUpperArm"

# Échelles référence (m) -> studs, alignées sur le rig : 1 bloc de réf. (0,3 m) = 1 bloc R15 (≈ 1 stud).
S_CORPS = 1 / 0.3  # torse 0,6 m -> 2 studs, jambe 0,3 m -> 1 stud
S_TETE = 3.3  # tête de réf. 0,36 m de large -> 1,19 stud (tête R15 : 1,16)

LIMITE_TRIS = 4000

# ---------------------------------------------------------------- palette / atlas
PALETTE = [
	# nom, hex, rugosité, métal (README ; « bretelle » ajoutée d'après la référence)
	("peau", "D9A67A", 0.7, 0.0),
	("salopette", "9A8A3C", 0.9, 0.0),
	("salopette_piece", "7C6E2C", 0.9, 0.0),
	("cuir", "5A3A22", 0.75, 0.0),
	("noir", "161412", 0.6, 0.0),
	("chapeau", "E9E4CF", 0.85, 0.0),
	("toile", "C9B48A", 0.85, 0.0),
	("orange", "E2662A", 0.55, 0.0),
	("rouge_sac", "C8432A", 0.7, 0.0),
	("bleu", "2F4F9E", 0.7, 0.0),
	("blanc", "F2F0EA", 0.7, 0.0),
	("vert", "4F8A1F", 0.5, 0.0),
	("vert_fonce", "3A6614", 0.6, 0.0),
	("bandage", "A9ACA8", 0.85, 0.0),
	("metal", "B8B2A2", 0.35, 0.35),
	("bretelle", "7A2E1C", 0.8, 0.0),
]
CASE = 4  # px par couleur
ATLAS = 16


def uv_couleur(nom):
	i = next(k for k, c in enumerate(PALETTE) if c[0] == nom)
	col, lig = i % 4, i // 4
	# origine des UV et des pixels Blender : en bas à gauche
	return ((col * CASE + CASE / 2) / ATLAS, (lig * CASE + CASE / 2) / ATLAS)


def creer_atlas():
	img = bpy.data.images.new("palette_tenue", ATLAS, ATLAS, alpha=False)
	px = [0.0] * (ATLAS * ATLAS * 4)
	for i, (_, hexa, _, _) in enumerate(PALETTE):
		r, g, b = (int(hexa[k : k + 2], 16) / 255 for k in (0, 2, 4))
		col, lig = i % 4, i // 4
		for y in range(lig * CASE, lig * CASE + CASE):
			for x in range(col * CASE, col * CASE + CASE):
				o = (y * ATLAS + x) * 4
				px[o : o + 4] = [r, g, b, 1.0]
	img.pixels[:] = px
	img.filepath_raw = str(EXPORT / "palette_tenue.png")
	img.file_format = "PNG"
	img.save()
	mat = bpy.data.materials.new("atlas_tenue")
	try:
		mat.use_nodes = True
	except AttributeError:
		pass
	nodes = mat.node_tree.nodes
	bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
	tex = nodes.new("ShaderNodeTexImage")
	tex.image = img
	tex.interpolation = "Closest"
	entree = next(s for s in bsdf.inputs if s.identifier == "Base Color")
	mat.node_tree.links.new(tex.outputs[0], entree)
	rug = next(s for s in bsdf.inputs if s.identifier == "Roughness")
	rug.default_value = 0.8
	return mat


# ---------------------------------------------------------------- repères
def rb(p):
	"""Point Roblox (relatif au HRP) -> Blender."""
	return Vector((-p[0], p[2], p[1] + H))


ART = {n: Vector(v) for n, v in R15["blender"]["articulations"].items()}


def bloc_b(nom):
	"""Boîte visible d'une pièce R15, en Blender : ((x0, x1), (y0, y1), (z0, z1))."""
	(x0, x1), (y0, y1), (z0, z1) = R15["blocs_visibles"][nom]
	return ((-x1, -x0), (z0, z1), (y0 + H, y1 + H))


def att_b(piece, nom):
	return rb(R15["attachments"][piece][nom][:3])


# repère de la référence (three.js) -> Blender : (x, y, z) -> (x, -z, y)
R_REF = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def euler3(rx, ry, rz):
	"""Rotation three.js (ordre 'XYZ' : M = Rx Ry Rz) = Euler Blender 'ZYX'."""
	return Euler((rx, ry, rz), "ZYX").to_matrix().to_4x4()


def M3(pos=(0, 0, 0), rot=(0, 0, 0), ech=(1, 1, 1)):
	"""Matrice d'un objet three.js (position, rotation, échelle)."""
	return Matrix.Translation(Vector(pos)) @ euler3(*rot) @ Matrix.Diagonal((*ech, 1))


ROT_Y_VERS_Z = Matrix.Rotation(-math.pi / 2, 4, "X")  # axe local Z (Blender) -> Y (three.js)

# ---------------------------------------------------------------- éléments nommés
COLL = {}
ELEMENTS = []  # (groupe, nom)
MATERIAU = None


def collection(nom, parent=None):
	if nom in COLL:
		return COLL[nom]
	c = bpy.data.collections.new(nom)
	(parent or bpy.context.scene.collection).children.link(c)
	COLL[nom] = c
	return c


def element(groupe, nom, bm, couleur, couleurs_faces=None):
	"""Range un élément nommé (bmesh déjà en coordonnées Blender) dans la collection du groupe.
	couleurs_faces : liste (une couleur par face, ordre de bm.faces) pour les éléments multicolores."""
	bm.faces.ensure_lookup_table()
	uv = bm.loops.layers.uv.verify()
	for i, f in enumerate(bm.faces):
		u, v = uv_couleur(couleurs_faces[i] if couleurs_faces else couleur)
		for lo in f.loops:
			lo[uv].uv = (u, v)
	bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
	ngones = [f for f in bm.faces if len(f.verts) > 4]
	if ngones:
		bmesh.ops.triangulate(bm, faces=ngones, quad_method="BEAUTY", ngon_method="BEAUTY")
	me = bpy.data.meshes.new(nom)
	bm.to_mesh(me)
	bm.free()
	ident = len(ELEMENTS)
	ELEMENTS.append((groupe, nom))
	att = me.attributes.new("element", "INT", "FACE")
	att.data.foreach_set("value", [ident] * len(me.polygons))
	me.materials.append(MATERIAU)
	ob = bpy.data.objects.new(nom, me)
	collection("Pieces_" + groupe, collection("Pieces_nommees")).objects.link(ob)
	return ob


# ---------------------------------------------------------------- primitives (bmesh)
def bm_boite(x0, x1, y0, y1, z0, z1, coupes_x=(), coupes_y=(), coupes_z=()):
	bm = bmesh.new()
	c = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
	bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)))
	for axe, coupes in ((0, coupes_x), (1, coupes_y), (2, coupes_z)):
		for val in coupes:
			n = Vector((0, 0, 0))
			n[axe] = 1
			co = Vector((0, 0, 0))
			co[axe] = val
			bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=n)
	return bm


def bm_cube_m(M):
	bm = bmesh.new()
	bmesh.ops.create_cube(bm, size=1.0, matrix=M)
	return bm


def bm_cyl(r1, r2, h, seg, M):
	"""Cylindre / cône le long de l'axe local Z, centré."""
	bm = bmesh.new()
	bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h, matrix=M)
	return bm


def bm_sphere(r, u, v, M):
	bm = bmesh.new()
	bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r, matrix=M)
	return bm


def bm_tore(R, r, n_maj, n_min, M, debut=0.0, arc=2 * math.pi):
	"""Tore dans le plan XY (axe Z) comme TorusGeometry ; arc partiel fermé par deux bouchons."""
	bm = bmesh.new()
	complet = arc >= 2 * math.pi - 1e-6
	n_anneaux = n_maj if complet else n_maj + 1
	anneaux = []
	for i in range(n_anneaux):
		a = debut + arc * i / n_maj
		c, s = math.cos(a), math.sin(a)
		anneau = []
		for j in range(n_min):
			b = 2 * math.pi * j / n_min
			rr = R + r * math.cos(b)
			anneau.append(bm.verts.new(M @ Vector((rr * c, rr * s, r * math.sin(b)))))
		anneaux.append(anneau)
	for i in range(n_maj):
		a0, a1 = anneaux[i], anneaux[(i + 1) % n_anneaux]
		for j in range(n_min):
			k = (j + 1) % n_min
			bm.faces.new((a0[j], a1[j], a1[k], a0[k]))
	if not complet:
		bm.faces.new(anneaux[0])
		bm.faces.new(list(reversed(anneaux[-1])))
	return bm


def bm_tube(points, r, cotes, ferme=False):
	"""Tube le long d'une polyligne (repères transportés), bouts fermés."""
	bm = bmesh.new()
	n = len(points)
	tang = []
	for i in range(n):
		a = points[i - 1] if (i > 0 or ferme) else points[i]
		b = points[(i + 1) % n] if (i < n - 1 or ferme) else points[i]
		tang.append((b - a).normalized())
	ref = Vector((0, 0, 1)) if abs(tang[0].z) < 0.9 else Vector((1, 0, 0))
	u = tang[0].cross(ref).normalized()
	anneaux = []
	for i, p in enumerate(points):
		t = tang[i]
		u = (u - t * u.dot(t)).normalized()
		w = t.cross(u)
		anneaux.append(
			[bm.verts.new(p + (u * math.cos(2 * math.pi * j / cotes) + w * math.sin(2 * math.pi * j / cotes)) * r) for j in range(cotes)]
		)
	segs = n if ferme else n - 1
	for i in range(segs):
		a0, a1 = anneaux[i], anneaux[(i + 1) % n]
		for j in range(cotes):
			k = (j + 1) % cotes
			bm.faces.new((a0[j], a1[j], a1[k], a0[k]))
	if not ferme:
		bm.faces.new(list(reversed(anneaux[0])))
		bm.faces.new(anneaux[-1])
	return bm


def contour_chanfrein(cx, cy, hx, hy, ch):
	"""Rectangle à coins coupés (8 points), sens trigonométrique, dans le plan XY."""
	return [
		(cx + hx, cy - hy + ch),
		(cx + hx, cy + hy - ch),
		(cx + hx - ch, cy + hy),
		(cx - hx + ch, cy + hy),
		(cx - hx, cy + hy - ch),
		(cx - hx, cy - hy + ch),
		(cx - hx + ch, cy - hy),
		(cx + hx - ch, cy - hy),
	]


def bm_prisme(contour, niveaux):
	"""Extrusion verticale d'un contour 2D (x, y) avec une boucle par niveau z ; fermé en haut et en bas.
	Renvoie (bm, bandes) : bandes[i] = faces latérales entre niveaux[i] et niveaux[i + 1]."""
	bm = bmesh.new()
	anneaux = [[bm.verts.new((x, y, z)) for x, y in contour] for z in niveaux]
	n = len(contour)
	bandes = []
	for i in range(len(niveaux) - 1):
		bande = []
		for j in range(n):
			k = (j + 1) % n
			bande.append(bm.faces.new((anneaux[i][j], anneaux[i][k], anneaux[i + 1][k], anneaux[i + 1][j])))
		bandes.append(bande)
	bas = bm.faces.new(list(reversed(anneaux[0])))
	haut = bm.faces.new(anneaux[-1])
	return bm, bandes, bas, haut


def bm_profil_xz(points, y0, y1):
	"""Extrusion le long de Y d'un polygone (x, z), pour les formes plates (passepoil en U)."""
	bm = bmesh.new()
	avant = [bm.verts.new((x, y0, z)) for x, z in points]
	arriere = [bm.verts.new((x, y1, z)) for x, z in points]
	n = len(points)
	bm.faces.new(avant)
	bm.faces.new(list(reversed(arriere)))
	for j in range(n):
		k = (j + 1) % n
		bm.faces.new((avant[j], arriere[j], arriere[k], avant[k]))
	return bm


def bm_ruban(points, normales, largeur, epaisseur):
	"""Sangle plate fermée en boucle : section rectangulaire, la face large suit la normale donnée."""
	bm = bmesh.new()
	n = len(points)
	anneaux = []
	for i, p in enumerate(points):
		t = (points[(i + 1) % n] - points[i - 1]).normalized()
		nn = (normales[i] - t * normales[i].dot(t)).normalized()
		w = t.cross(nn)
		coins = []
		for a, b in ((-1, 0), (1, 0), (1, 1), (-1, 1)):
			coins.append(bm.verts.new(p + w * (a * largeur / 2) + nn * (b * epaisseur)))
		anneaux.append(coins)
	for i in range(n):
		a0, a1 = anneaux[i], anneaux[(i + 1) % n]
		for j in range(4):
			k = (j + 1) % 4
			bm.faces.new((a0[j], a1[j], a1[k], a0[k]))
	return bm


def catmull(points, normales, sub, ferme=True):
	"""Lissage Catmull-Rom d'une boucle (points et normales interpolés)."""
	n = len(points)
	res_p, res_n = [], []
	for i in range(n if ferme else n - 1):
		p0, p1, p2, p3 = points[i - 1], points[i], points[(i + 1) % n], points[(i + 2) % n]
		n1, n2 = normales[i], normales[(i + 1) % n]
		for k in range(sub):
			t = k / sub
			t2, t3 = t * t, t * t * t
			p = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
			res_p.append(p)
			res_n.append((n1 * (1 - t) + n2 * t).normalized())
	return res_p, res_n


def transformer(bm, M):
	bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])
	return bm


# ================================================================ RIG R15 BLOC
OS = {
	# os : (articulation de la tête de l'os, parent)
	"Root": (None, None),
	"HumanoidRootNode": (None, "Root"),
	"LowerTorso": ("Root", "HumanoidRootNode"),
	"UpperTorso": ("Waist", "LowerTorso"),
	"Head": ("Neck", "UpperTorso"),
	"LeftUpperArm": ("LeftShoulder", "UpperTorso"),
	"LeftLowerArm": ("LeftElbow", "LeftUpperArm"),
	"LeftHand": ("LeftWrist", "LeftLowerArm"),
	"RightUpperArm": ("RightShoulder", "UpperTorso"),
	"RightLowerArm": ("RightElbow", "RightUpperArm"),
	"RightHand": ("RightWrist", "RightLowerArm"),
	"LeftUpperLeg": ("LeftHip", "LowerTorso"),
	"LeftLowerLeg": ("LeftKnee", "LeftUpperLeg"),
	"LeftFoot": ("LeftAnkle", "LeftLowerLeg"),
	"RightUpperLeg": ("RightHip", "LowerTorso"),
	"RightLowerLeg": ("RightKnee", "RightUpperLeg"),
	"RightFoot": ("RightAnkle", "RightLowerLeg"),
}


def creer_rig():
	"""Armature R15 aux noms officiels : tête de chaque os sur l'articulation avec son parent (relevé Studio),
	os orientés comme dans les gabarits Roblox (repère identique au monde dans le FBX : os vers le haut)."""
	arm_data = bpy.data.armatures.new("R15")
	arm = bpy.data.objects.new("R15", arm_data)
	collection("Rig_R15").objects.link(arm)
	bpy.context.view_layer.objects.active = arm
	bpy.ops.object.mode_set(mode="EDIT")
	eb = arm_data.edit_bones
	for nom, (art, parent) in OS.items():
		b = eb.new(nom)
		tete = Vector((0, 0, H)) if art is None else ART[art]
		b.head = tete
		b.tail = tete + Vector((0, 0, 0.4))
		b.roll = 0.0
		if parent:
			b.parent = eb[parent]
		b.use_deform = nom not in ("Root", "HumanoidRootNode")
	bpy.ops.object.mode_set(mode="OBJECT")
	m = arm_data.bones["UpperTorso"].matrix_local.to_3x3()
	attendu = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # os Y = monde Z, os X = monde X
	ecart = max(abs(m[i][j] - attendu[i][j]) for i in range(3) for j in range(3))
	print(f"rig : {len(arm_data.bones)} os, écart d'orientation {ecart:.2e}")

	# blocs visibles du R15 (aperçu, non exportés), parentés à leur os
	for piece in ("LowerTorso", "UpperTorso", "Head") + tuple(
		c + p for c in ("Left", "Right") for p in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot")
	):
		if piece == "Head":
			b = R15["blocs_visibles"]["Head"]
			cz = b["centre"][1] + H
			bm = bm_boite(-0.58, 0.58, -0.58, 0.58, cz - b["hauteur"] / 2, cz + b["hauteur"] / 2)
			bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.2, segments=3, affect="EDGES")
		else:
			(x0, x1), (y0, y1), (z0, z1) = bloc_b(piece)
			bm = bm_boite(x0, x1, y0, y1, z0, z1)
		uv = bm.loops.layers.uv.verify()
		for f in bm.faces:
			for lo in f.loops:
				lo[uv].uv = uv_couleur("peau")
		me = bpy.data.meshes.new(piece)
		bm.to_mesh(me)
		bm.free()
		me.materials.append(MATERIAU)
		ob = bpy.data.objects.new(piece, me)
		collection("Rig_R15").objects.link(ob)
		mw = ob.matrix_world.copy()
		ob.parent = arm
		ob.parent_type = "BONE"
		ob.parent_bone = piece
		ob.matrix_world = mw
		ob.color = (0.85, 0.65, 0.48, 1)
	return arm


# ================================================================ SALOPETTE (layered, Pants)
def construire_salopette():
	G = "salopette"
	m = 0.03  # jeu entre le corps et le tissu
	# bassin : du haut des cuisses à la ceinture
	bm, _, _, _ = bm_prisme(contour_chanfrein(0, 0, 1.03, 0.535, 0.06), [2.12, 2.19, 2.30, 2.45, 2.593, 2.72, 2.88])
	element(G, "bassin", bm, "salopette")
	for s, sd in ((1, "g"), (-1, "d")):
		cx = s * 0.518  # jambe : bord intérieur à |x| = 0,012, extérieur à 1,024
		niv = [0.70, 0.80, 0.95, 1.10, 1.20, 1.27, 1.35, 1.45, 1.60, 1.80, 2.00, 2.12, 2.22, 2.30]
		bm, _, _, _ = bm_prisme(contour_chanfrein(cx, 0, 0.506, 0.486 + m, 0.05), niv)
		element(G, f"pantalon_{'gauche' if s > 0 else 'droit'}", bm, "salopette")
		# ourlet gris à mi-mollet (référence ; « revers » dans le HTML)
		bm, _, _, _ = bm_prisme(contour_chanfrein(s * 0.523, 0, 0.517, 0.532, 0.055), [0.66, 0.79])
		element(G, f"revers_{'gauche' if s > 0 else 'droit'}", bm, "bandage")
		# coutures latérales (extérieur de la jambe, avant et arrière)
		xo = s * 1.024
		for yy, nom in ((-0.40, f"couture_jambe_{sd}"), (0.40, f"couture_jambe_dos_{sd}")):
			bm = bm_boite(min(xo - s * 0.004, xo + s * 0.009), max(xo - s * 0.004, xo + s * 0.009), yy - 0.012, yy + 0.012, 0.80, 2.10)
			element(G, nom, bm, "salopette_piece")
		# petites poches brunes aux hanches (référence) + rabat + bouton
		px = s * 0.66
		bm = bm_boite(px - 0.12, px + 0.12, -0.552, -0.532, 2.30, 2.56)
		element(G, f"poche_hanche_{sd}", bm, "cuir")
		bm = bm_boite(px - 0.13, px + 0.13, -0.562, -0.528, 2.50, 2.585)
		element(G, f"rabat_poche_{sd}", bm, "salopette_piece")
		bm = bm_cyl(0.03, 0.03, 0.02, 10, Matrix.Translation((px, -0.5685, 2.535)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
		element(G, f"bouton_rabat_{sd}", bm, "metal")
		# bretelles rouille : devant, sur l'épaule, dans le dos
		bx = s * 0.62
		bm = bm_boite(bx - 0.06, bx + 0.06, -0.548, -0.528, 2.80, 4.315)
		element(G, f"bretelle_avant_{sd}", bm, "bretelle")
		bm = bm_boite(bx - 0.054, bx + 0.054, -0.540, 0.540, 4.300, 4.325)
		element(G, f"bretelle_epaule_{sd}", bm, "bretelle")
		bm = bm_boite(bx - 0.06, bx + 0.06, 0.528, 0.548, 2.80, 4.315)
		element(G, f"bretelle_dos_{sd}", bm, "bretelle")
		# poches arrière
		qx = s * 0.45
		bm = bm_boite(qx - 0.20, qx + 0.20, 0.540, 0.552, 2.24, 2.55)
		element(G, f"poche_arriere_{sd}", bm, "salopette_piece")
		bm = bm_boite(qx - 0.17, qx + 0.17, 0.545, 0.558, 2.49, 2.51)
		element(G, f"couture_poche_arriere_{sd}", bm, "cuir")
	# ceinture grise + liseré clair
	bm, _, _, _ = bm_prisme(contour_chanfrein(0, 0, 1.055, 0.56, 0.065), [2.60, 2.75, 2.90])
	element(G, "ceinture", bm, "bandage")
	bm, _, _, _ = bm_prisme(contour_chanfrein(0, 0, 1.062, 0.567, 0.067), [2.855, 2.885])
	element(G, "lisere_ceinture", bm, "blanc")
	# panneau avant brun sous la ceinture (référence) : découpé pour suivre les deux cuisses
	bm = bm_boite(-0.38, 0.38, -0.562, -0.548, 1.58, 2.59, coupes_x=(-0.19, 0.0, 0.19), coupes_z=(1.75, 1.92, 2.05, 2.19, 2.32, 2.45))
	element(G, "bavette", bm, "cuir")
	# passepoil gris en U sur le panneau
	u_ext, u_int, bas, haut = 0.33, 0.28, 1.62, 2.55
	contour_u = [
		(-u_ext, haut), (-u_ext, bas), (u_ext, bas), (u_ext, haut), (u_int, haut), (u_int, bas + 0.05),
		(-u_int, bas + 0.05), (-u_int, haut),
	]  # fmt: skip
	bm = bm_profil_xz(contour_u, -0.574, -0.558)  # enfoncé de 4 mm dans le panneau (pas de faces collées)
	for z in (1.80, 2.00, 2.19, 2.35):
		bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z), plane_no=(0, 0, 1))
	element(G, "passepoil_bavette", bm, "bandage")
	bm = bm_boite(-0.012, 0.012, -0.568, -0.553, 1.65, 2.55, coupes_z=(1.92, 2.19, 2.35))
	element(G, "couture_bavette", bm, "noir")
	# pièce au dos de la jambe gauche (HTML)
	M = Matrix.Translation((0.50, 0.527, 1.10)) @ Matrix.Rotation(0.15, 4, "Y") @ Matrix.Diagonal((0.30, 0.012, 0.27, 1))
	element(G, "piece_dos", bm_cube_m(M), "salopette_piece")


# ================================================================ CHAUSSURES (layered, LeftShoe / RightShoe)
def construire_chaussures():
	for s, cote in ((1, "gauche"), (-1, "droite")):
		G = f"chaussure_{cote}"
		sd = "g" if s > 0 else "d"
		cx = s * 0.4979

		def bx(interieur, exterieur):
			# bornes en x : bord intérieur près de l'axe (sans le croiser), bord extérieur hors du pied
			a, b = s * interieur, s * exterieur
			return min(a, b), max(a, b)

		x0, x1 = bx(0.012, 1.033)
		bm, _, _, _ = bm_prisme(contour_chanfrein((x0 + x1) / 2, -0.015, (x1 - x0) / 2, 0.545, 0.06), [0.03, 0.12, 0.20, 0.262, 0.33, 0.42, 0.56])
		element(G, f"chaussure_{cote}", bm, "cuir")
		bm = bm_boite(*bx(0.006, 1.048), -0.575, 0.545, -0.01, 0.045)
		element(G, f"semelle_{sd}", bm, "noir")
		bm = bm_boite(*bx(0.017, 1.043), -0.572, -0.43, 0.035, 0.20)
		element(G, f"bout_chaussure_{sd}", bm, "noir")
		for i, z in enumerate((0.28, 0.36, 0.44)):
			bm = bm_boite(cx - 0.16, cx + 0.16, -0.572, -0.564, z - 0.008, z + 0.008)
			element(G, f"lacet_{sd}_{i}", bm, "noir")


# ================================================================ BRASSARD (layered, Jacket)
def construire_brassard():
	G = "brassard"
	cx = ART["LeftElbow"].x  # centre du bras gauche (x Blender > 0)
	if BRASSARD_OS == "LeftLowerArm":
		haut = 3.20  # juste sous le coude (z 3,2656)
	else:
		haut = 3.85
	niv = [haut - 0.09 * i for i in range(6)][::-1]
	bm, bandes, bas, dessus = bm_prisme(contour_chanfrein(cx, 0, 0.531, 0.531, 0.04), niv)
	couleurs = {}
	ordre = ["bleu", "blanc", "bleu", "blanc", "bleu"]  # de haut en bas
	for i, bande in enumerate(bandes):
		for f in bande:
			couleurs[f] = ordre[len(bandes) - 1 - i]
	couleurs[bas] = "bleu"
	couleurs[dessus] = "bleu"
	element(G, "brassard", bm, None, couleurs_faces=[couleurs[f] for f in bm.faces])


# ================================================================ TÊTE : chapeau + lunettes, cheveux (rigides)
Z_HAUT_TETE = att_b("Head", "HatAttachment").z
# repère tête de la réf. (origine au cou, y = 0,384 au sommet) -> Blender, sommet sur HatAttachment
C_TETE = Matrix.Translation((0, 0, Z_HAUT_TETE)) @ Matrix.Scale(S_TETE, 4) @ R_REF @ Matrix.Translation((0, -0.384, 0))
Y_CHAPEAU = 0.305  # base du chapeau (réf. : bord au-dessus des yeux, pas posé tout en haut comme dans le HTML)


def bord_chapeau(n=32):
	"""Bord en révolution (32 segments), plus long et relevé en pointe sur les côtés (référence)."""
	bm = bmesh.new()
	r_in, ep = 0.205, 0.012
	prof = [0.0, 0.35, 0.65, 0.85, 1.0]
	haut, bas_ = [], []
	for i in range(n):
		th = 2 * math.pi * i / n
		c, s = math.cos(th), math.sin(th)
		r_out = 0.30 + 0.13 * abs(c) ** 6
		lev = 0.11 * abs(c) ** 4
		tombe = 0.018 * max(0.0, s)  # l'avant (+z) retombe un peu
		lh, lb = [], []
		for t in prof:
			r = r_in + t * (r_out - r_in)
			y = 0.004 - 0.010 * t + lev * t**2.5 - tombe * t
			lh.append(bm.verts.new((r * c, y + ep / 2, r * s)))
			lb.append(bm.verts.new((r * c, y - ep / 2, r * s)))
		haut.append(lh)
		bas_.append(lb)
	k = len(prof)
	for i in range(n):
		j = (i + 1) % n
		for t in range(k - 1):
			bm.faces.new((haut[i][t], haut[i][t + 1], haut[j][t + 1], haut[j][t]))
			bm.faces.new((bas_[i][t], bas_[j][t], bas_[j][t + 1], bas_[i][t + 1]))
		bm.faces.new((haut[i][-1], bas_[i][-1], bas_[j][-1], haut[j][-1]))
		bm.faces.new((haut[i][0], haut[j][0], bas_[j][0], bas_[i][0]))
	return bm


def calotte(n=24):
	"""Calotte basse, à peine évasée, pincée et creusée sur le devant, dessus enfoncé au centre (référence)."""
	bm = bmesh.new()
	anneaux = []
	for k, (y, r, pince) in enumerate(((-0.02, 0.205, 1.0), (0.10, 0.21, 0.95), (0.185, 0.212, 0.87), (0.215, 0.195, 0.80))):
		anneau = []
		for i in range(n):
			a = 2 * math.pi * i / n
			c, sn = math.cos(a), math.sin(a)
			avant = max(0.0, sn)  # +z = avant du chapeau
			rr, yy = r, y
			if k >= 2:
				rr *= 1 - 0.13 * avant**2  # pincé sur le devant
				yy -= 0.035 * avant**3  # le dessus plonge vers l'avant
			if k == 3 and i == n // 4:
				rr -= 0.02  # pli central du devant
			anneau.append(bm.verts.new((rr * c, yy, rr * pince * sn)))
		anneaux.append(anneau)
	for a, b in zip(anneaux, anneaux[1:]):
		for i in range(n):
			j = (i + 1) % n
			bm.faces.new((a[i], a[j], b[j], b[i]))
	creux = bm.verts.new((0, 0.172, -0.015))
	for i in range(n):
		bm.faces.new((anneaux[-1][i], anneaux[-1][(i + 1) % n], creux))
	bm.faces.new(list(reversed(anneaux[0])))
	return bm


def construire_tete():
	G = "chapeau"
	M_chap = C_TETE @ M3((0, Y_CHAPEAU, -0.01), (-0.08, 0, 0.06))
	element(G, "calotte", transformer(calotte(), M_chap), "chapeau")
	element(G, "bord", transformer(bord_chapeau(32), M_chap), "chapeau")
	# lunettes sur le côté gauche, sous le bord (HTML)
	M_lun = C_TETE @ M3((0.19, 0.17, 0.06), (0, math.pi / 2 - 0.3, 0))
	# cylindres three.js tournés de pi/2 sur X = axe local Z, celui des cônes bmesh
	element(G, "lunette_monture", bm_cyl(0.06, 0.06, 0.05, 24, M_lun), "orange")
	element(G, "lunette_verre", bm_cyl(0.042, 0.042, 0.01, 24, M_lun @ Matrix.Translation((0, 0, 0.026))), "blanc")
	for i in range(3):
		Mf = M_lun @ Matrix.Translation((0, -0.016 + i * 0.016, 0.032)) @ Matrix.Diagonal((0.05, 0.008, 0.006, 1))
		element(G, f"lunette_fente_{i}", bm_cube_m(Mf), "noir")
	element(G, "lunette_sangle", bm_cube_m(M_lun @ Matrix.Translation((0, 0, -0.12)) @ Matrix.Diagonal((0.03, 0.03, 0.24, 1))), "noir")

	G = "cheveux"
	boucles = [
		(0, 0.28, -0.13, 0.11), (-0.11, 0.24, -0.1, 0.09), (0.11, 0.24, -0.1, 0.09), (0, 0.14, -0.16, 0.11),
		(-0.14, 0.1, -0.1, 0.09), (0.14, 0.1, -0.1, 0.09), (-0.08, 0.0, -0.17, 0.1), (0.08, 0.0, -0.17, 0.1),
		(0, -0.06, -0.2, 0.1), (-0.17, 0.18, -0.03, 0.07), (0.17, 0.18, -0.03, 0.07), (-0.16, -0.02, -0.06, 0.08),
		(0.16, -0.02, -0.06, 0.08),
	]  # fmt: skip
	element(G, "cheveux_boucles", masse_bouclee(boucles), "noir")


def masse_bouclee(boucles, graine=7):
	"""Cheveux d'une seule masse bouclée : métaboules aux 13 boucles du HTML + petites bosses vers l'arrière et les
	côtés (jamais sur le visage), converties en maillage fermé."""
	import random

	rnd = random.Random(graine)
	elements = []
	for x, y, z, r in boucles:
		elements.append((Vector((x, y, z)), r))
		for _ in range(4):
			d = Vector((rnd.uniform(-1, 1), rnd.uniform(-0.6, 1), -abs(rnd.uniform(0.3, 1)))).normalized()
			elements.append((Vector((x, y, z)) + d * r * 0.75, r * rnd.uniform(0.55, 0.68)))
	mb = bpy.data.metaballs.new("cheveux_mb")
	mb.resolution = 0.085
	mb.render_resolution = 0.085
	mb.threshold = 0.6
	ob = bpy.data.objects.new("cheveux_mb", mb)
	bpy.context.scene.collection.objects.link(ob)
	for c, r in elements:
		e = mb.elements.new()
		e.co = C_TETE @ c
		e.radius = r * S_TETE * 1.05
		e.stiffness = 3.0
	bpy.context.view_layer.update()
	me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
	bm = bmesh.new()
	bm.from_mesh(me)
	bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
	tris = sum(len(f.verts) - 2 for f in bm.faces)
	if tris > 3200:
		bmesh.ops.triangulate(bm, faces=bm.faces[:])
		bm.to_mesh(me)
		bm.free()
		dec = bpy.data.objects.new("dec", me)
		bpy.context.scene.collection.objects.link(dec)
		mod = dec.modifiers.new("d", "DECIMATE")
		mod.ratio = 3000 / tris
		bpy.context.view_layer.update()
		me2 = bpy.data.meshes.new_from_object(dec.evaluated_get(bpy.context.evaluated_depsgraph_get()))
		bm = bmesh.new()
		bm.from_mesh(me2)
		bpy.data.objects.remove(dec)
		bpy.data.meshes.remove(me2)
	bpy.data.objects.remove(ob)
	bpy.data.metaballs.remove(mb)
	return bm


# ================================================================ SAC + BANDOULIÈRE (rigide, Back)
SAC_REF = Vector((0.38, 0.6, 0.14))
SAC_B = Vector((1.36, -0.25, 1.742))  # sous la main gauche, à côté de la cuisse (référence)
C_SAC = Matrix.Translation(SAC_B) @ Matrix.Scale(S_CORPS, 4) @ R_REF @ Matrix.Translation(-SAC_REF)


def construire_sac():
	G = "sac"
	element(G, "sac", bm_sphere(0.11, 16, 10, C_SAC @ M3(SAC_REF, ech=(1, 0.9, 0.85))), "rouge_sac")
	element(G, "noeud_sac", bm_sphere(0.035, 10, 7, C_SAC @ M3((0.33, 0.7, 0.16))), "rouge_sac")
	element(G, "lien_sac", bm_tore(0.03, 0.008, 16, 6, C_SAC @ M3((0.34, 0.68, 0.16), (0.3, 0, 0.6))), "blanc")
	element(G, "ecusson_sac", bm_cyl(0.03, 0.03, 0.008, 20, C_SAC @ M3((0.38, 0.6, 0.232))), "toile")
	element(G, "ecusson_centre", bm_cyl(0.012, 0.012, 0.006, 12, C_SAC @ M3((0.38, 0.6, 0.2375))), "cuir")
	element(G, "couture_sac", bm_tore(0.1, 0.004, 32, 5, C_SAC @ M3((0.38, 0.6, 0.14), (math.pi / 2, 0, 0)) @ Matrix.Diagonal((1.0, 0.85, 1.0, 1))), "cuir")  # fmt: skip
	element(G, "pompon_sac", bm_sphere(0.02, 10, 7, C_SAC @ M3((0.31, 0.62, 0.18))), "toile")
	a, b = C_SAC @ Vector((0.33, 0.69, 0.16)), C_SAC @ Vector((0.31, 0.635, 0.18))
	element(G, "cordon_pompon", bm_tube([a, b], 0.004 * S_CORPS, 5), "cuir")

	# bandoulière claire en boucle : nœud du sac -> dos -> épaule droite -> devant -> nœud
	noeud = C_SAC @ Vector((0.33, 0.7, 0.16))
	X, Yv, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
	chemin = [
		(noeud + Vector((0, 0.06, 0.01)), -Z + X * 0.3),
		(Vector((1.12, 0.05, 2.08)), X),
		(Vector((1.06, 0.42, 2.20)), Yv + X),
		(Vector((0.80, 0.605, 2.62)), Yv),
		(Vector((-0.42, 0.60, 4.30)), Yv + Z * 0.5),
		(Vector((-0.42, 0.0, 4.375)), Z),
		(Vector((-0.42, -0.60, 4.30)), -Yv + Z * 0.5),
		(Vector((0.80, -0.605, 2.62)), -Yv),
		(Vector((1.12, -0.58, 2.18)), -Yv + X * 0.5),
		(noeud + Vector((0, -0.06, 0.01)), -Yv - Z * 0.3),
	]
	pts, nrm = catmull([p for p, _ in chemin], [n.normalized() for _, n in chemin], 4)
	element(G, "bandouliere", bm_ruban(pts, nrm, 0.13, 0.035), "blanc")
	# boucle de la bandoulière, au milieu du brin avant
	p1, p2 = Vector((-0.42, -0.60, 4.30)), Vector((0.80, -0.605, 2.62))
	centre = (p1 + p2) / 2 + Vector((0, -0.04, 0))
	t = (p2 - p1).normalized()
	rot = Matrix((t.cross(-Yv), t, -Yv)).transposed().to_4x4()  # colonnes : largeur, long, normale
	element(G, "boucle_bandouliere", bm_cube_m(Matrix.Translation(centre) @ rot @ Matrix.Diagonal((0.20, 0.17, 0.035, 1))), "metal")
	element(G, "boucle_bandouliere_int", bm_cube_m(Matrix.Translation(centre - Yv * 0.02) @ rot @ Matrix.Diagonal((0.11, 0.09, 0.02, 1))), "cuir")  # fmt: skip


# ================================================================ LANCE-PIERRE (Tool)
C_ARME = Matrix.Scale(S_CORPS, 4) @ R_REF  # origine = point de prise (y = 0 de la réf.), bâton le long de +Z Blender (+Y Roblox)


def cyl_ab(a, b, r, seg):
	"""Cylindre entre deux points du repère de la réf. (comme cyl() du HTML)."""
	A, B = Vector(a), Vector(b)
	d = B - A
	q = Vector((0, 1, 0)).rotation_difference(d.normalized()).to_matrix().to_4x4()
	return bm_cyl(r, r, d.length, seg, C_ARME @ Matrix.Translation((A + B) / 2) @ q @ ROT_Y_VERS_Z)


def construire_arme():
	G = "lance_pierre"
	element(G, "manche", cyl_ab((0, -0.5, 0), (0, 0.95, 0), 0.02, 12), "bandage")
	element(G, "embout_bas", cyl_ab((0, -0.56, 0), (0, -0.44, 0), 0.024, 12), "vert")
	element(G, "col", cyl_ab((0, 0.92, 0), (0, 1.02, 0), 0.026, 12), "vert")
	# bandage croisé (référence) : deux hélices noires de sens opposés
	for nom, sens in (("bande_croisee_a", 1), ("bande_croisee_b", -1)):
		pas, y0, y1 = 0.16, -0.42, 0.90
		n = int((y1 - y0) / pas * 8)
		pts = []
		for i in range(n + 1):
			y = y0 + (y1 - y0) * i / n
			a = sens * 2 * math.pi * (y - y0) / pas
			pts.append(C_ARME @ Vector((0.0215 * math.cos(a), y, 0.0215 * math.sin(a))))
		element(G, nom, bm_tube(pts, 0.0028 * S_CORPS, 3), "noir")
	# anneau en C, ouverture à l'opposé du manche (référence : ~68°)
	R, tube = 0.2, 0.024
	cy = 1.0 + R
	ouv = math.radians(68)
	debut = math.pi / 2 + ouv / 2
	element(G, "anneau", bm_tore(R, tube, 36, 10, C_ARME @ Matrix.Translation((0, cy, 0)), debut, 2 * math.pi - ouv), "vert")
	for i, a in enumerate((debut, debut + 2 * math.pi - ouv)):
		element(G, f"anneau_extremite_{i}", bm_sphere(tube * 1.15, 10, 7, C_ARME @ Matrix.Translation((R * math.cos(a), cy + R * math.sin(a), 0))), "vert")  # fmt: skip
	pochette = Vector((0.0, cy - 0.03, 0.0))
	element(G, "pochette", bm_sphere(0.03, 12, 8, C_ARME @ Matrix.Translation(pochette) @ Matrix.Diagonal((1.3, 0.7, 1, 1))), "toile")
	# 5 dents vers l'intérieur (référence), la 5e dans le prolongement du manche
	for i, deg in enumerate((22, -36, 155, 214, 270)):
		a = math.radians(deg)
		o = (R * math.cos(a), cy + R * math.sin(a), 0)
		t = ((R - 0.09) * math.cos(a), cy + (R - 0.09) * math.sin(a), 0)
		element(G, f"dent_{i}", cyl_ab(o, t, 0.016, 10), "vert")
		element(G, f"dent_bout_{i}", bm_sphere(0.02, 10, 7, C_ARME @ Matrix.Translation(t)), "vert_fonce")
		depart = Vector(t) + (pochette - Vector(t)).normalized() * 0.012  # part de l'intérieur de la bosse
		element(G, f"elastique_{i}", bm_tube([C_ARME @ depart, C_ARME @ pochette], 0.003 * S_CORPS, 4), "noir")


# ================================================================ CAGES (gabarit officiel recalé sur le R15 bloc)
# Articulations du gabarit Roblox (LayeredClothingTemplate.blend, têtes d'os), converties en Blender (x, -z, y + 2,994).
def g(x, y, z):
	return Vector((x, -z, y + 2.994))


def segments_cage():
	"""Segments (gabarit -> cible). Pour chaque segment : extrémités du gabarit, rayons de tri, boîte cible
	(centre, demi-tailles), axe « long » cible et bouts exposés (projection 3D) ou internes (projection 2D)."""
	segs = []

	def boite(nom):
		(x0, x1), (y0, y1), (z0, z1) = bloc_b(nom)
		return Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)), ((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2)

	segs.append(dict(nom="LowerTorso", A=g(0, -0.35, 0.06), B=g(0, 0.304, 0.072), r=(0.42, 0.30), haut=1, bout_a=True, bout_b=False, cible=boite("LowerTorso")))  # fmt: skip
	segs.append(dict(nom="UpperTorso", A=g(0, 0.304, 0.072), B=g(0, 1.47, 0.03), r=(0.72, 0.36), haut=1, bout_a=False, bout_b=True, cible=boite("UpperTorso")))  # fmt: skip
	segs.append(dict(nom="Head", A=g(0, 1.47, 0.02), B=g(0, 2.507, 0.02), r=(0.30, 0.36), haut=1, bout_a=False, bout_b=True,
		cible=(Vector((0, 0, (ART["Neck"].z + Z_HAUT_TETE) / 2)), (0.58, 0.58, (Z_HAUT_TETE - ART["Neck"].z) / 2))))  # fmt: skip
	for s, c in ((1, "Left"), (-1, "Right")):
		ep, co, po = g(s * 0.472, 1.399, 0.019), g(s * 0.871, 0.81, 0.019), g(s * 1.341, 0.124, 0.177)
		bout_main = po + (po - co).normalized() * 0.42
		ha, ge, ch = g(s * 0.3, -0.119, 0.088), g(s * 0.488, -1.431, 0.031), g(s * 0.647, -2.747, -0.074)
		segs += [
			dict(nom=c + "UpperArm", A=ep, B=co, r=(0.17, 0.17), haut=-1, bout_a=True, bout_b=False, cible=boite(c + "UpperArm")),
			dict(nom=c + "LowerArm", A=co, B=po, r=(0.15, 0.15), haut=-1, bout_a=False, bout_b=False, cible=boite(c + "LowerArm")),
			dict(nom=c + "Hand", A=po, B=bout_main, r=(0.15, 0.13), haut=-1, bout_a=False, bout_b=True, cible=boite(c + "Hand")),
			dict(nom=c + "UpperLeg", A=ha, B=ge, r=(0.25, 0.25), haut=-1, bout_a=False, bout_b=False, cible=boite(c + "UpperLeg")),
			dict(nom=c + "LowerLeg", A=ge, B=ch, r=(0.21, 0.21), haut=-1, bout_a=False, bout_b=False, cible=boite(c + "LowerLeg")),
			dict(nom=c + "Foot", A=ch, B=Vector((ch.x, ch.y, 0.0)), r=(0.22, 0.32), haut=-1, bout_a=False, bout_b=True, cible=boite(c + "Foot")),
		]  # fmt: skip
	for sg in segs:
		long_g = (sg["B"] - sg["A"]).normalized()
		dep = Vector((0, 1, 0))
		dep = (dep - long_g * dep.dot(long_g)).normalized()
		sg["axes_g"] = (long_g.cross(dep), dep, long_g)  # latéral, profondeur, long
		long_c = Vector((0, 0, sg["haut"]))
		sg["axes_c"] = (long_c.cross(Vector((0, 1, 0))), Vector((0, 1, 0)), long_c)
		sg["L"] = (sg["B"] - sg["A"]).length
	return segs


def score(sg, v):
	d = v - sg["A"]
	lat, dep, lon = (d.dot(a) for a in sg["axes_g"])
	exces = max(0.0, -lon, lon - sg["L"]) / 0.12
	return math.sqrt((lat / sg["r"][0]) ** 2 + (dep / sg["r"][1]) ** 2 + exces**2)


def recaler_cage(verts_g, segs, jeu=0.012):
	"""Déplace les sommets du gabarit sur la surface des blocs R15 (même topologie, mêmes UV)."""
	n = len(verts_g)
	scores = [[score(sg, v) for sg in segs] for v in verts_g]
	attrib = [min(range(len(segs)), key=lambda k: sc[k]) for sc in scores]
	# boîte du gabarit par segment (centiles 2 / 98 des sommets attribués), dans le repère du segment
	for k, sg in enumerate(segs):
		loc = [[(verts_g[i] - sg["A"]).dot(a) for a in sg["axes_g"]] for i in range(n) if attrib[i] == k]
		sg["nb"] = len(loc)
		cen, dem = [], []
		for ax in range(3):
			vals = sorted(p[ax] for p in loc)
			lo, hi = vals[int(0.02 * (len(vals) - 1))], vals[int(0.98 * (len(vals) - 1))]
			cen.append((lo + hi) / 2)
			dem.append(max((hi - lo) / 2, 1e-3))
		sg["boite_g"] = (cen, dem)

	def projeter(sg, v):
		cen, dem = sg["boite_g"]
		d = v - sg["A"]
		q = [((d.dot(sg["axes_g"][ax])) - cen[ax]) / dem[ax] for ax in range(3)]
		bout = sg["bout_b"] if q[2] > 0 else sg["bout_a"]
		m2 = max(abs(q[0]), abs(q[1]))
		if bout and abs(q[2]) >= m2:
			m3 = max(m2, abs(q[2]))
			q = [x / m3 for x in q]
		elif m2 > 1e-6:
			q[0] /= m2
			q[1] /= m2
		c, h = sg["cible"]
		# « long » des cibles : sens de sg["haut"] ; boîte cible exprimée dans ses axes (lat = ±X, prof = Y, long = ±Z)
		hs = (h[0] + jeu, h[1] + jeu, h[2] + jeu)
		p = c.copy()
		for ax in range(3):
			p += sg["axes_c"][ax] * (q[ax] * hs[ax])
		return p

	# mélange des segments voisins (poids négligeables retirés puis renormalisés)
	res = []
	for i, v in enumerate(verts_g):
		sc = scores[i]
		smin = min(sc)
		poids = [math.exp(-(x - smin) / 0.12) for x in sc]
		garde = [(k, w) for k, w in enumerate(poids) if w / sum(poids) > 0.01]
		tot = sum(w for _, w in garde)
		res.append(sum((projeter(segs[k], v) * (w / tot) for k, w in garde), Vector((0, 0, 0))))
	return res, attrib


def charger_gabarit():
	with bpy.data.libraries.load(str(GABARIT_CAGE), link=False) as (src, dst):
		dst.objects = [n for n in src.objects if n.endswith("_InnerCage")]
	ob = dst.objects[0]
	return ob.data


def lire_maillage_roblox(chemin):
	"""Maillage Roblox « version 2.00 » : renvoie [(position, uv)]."""
	d = chemin.read_bytes()
	i = d.index(b"\n") + 1
	taille_entete, taille_sommet, _, nv, _ = struct.unpack_from("<HBBII", d, i)
	i += taille_entete
	res = []
	for k in range(nv):
		px, py, pz, _, _, _, u, v = struct.unpack_from("<8f", d, i + taille_sommet * k)
		res.append(((px, py, pz), (u, v)))
	return res


def cage_corps_bloc():
	"""Cages réelles du corps R15 bloc par défaut (WrapTarget des 14 pièces hors tête, tools/cages_roblox/corps_bloc/),
	placées par pièce + CageOrigin (relevé Studio), en coordonnées Blender ; arbre de recherche sur les UV (u, 1 - v)."""
	releve = json.loads((CAGES_CORPS / "releve_studio.json").read_text(encoding="utf-8"))["pieces"]
	pts = []
	for f in sorted(CAGES_CORPS.glob("*.mesh")):
		r = releve[f.stem]
		base = [r["cframe"][a] + r["cageOrigin"][a] for a in range(3)]
		for (px, py, pz), (u, v) in lire_maillage_roblox(f):
			pts.append((rb((base[0] + px, base[1] + py, base[2] + pz)), (u, 1 - v)))
	kd = kdtree.KDTree(len(pts))
	for i, (_, uv) in enumerate(pts):
		kd.insert(Vector((uv[0], uv[1], 0)), i)
	kd.balance()
	return pts, kd


def construire_cage_interne():
	"""Cage interne = gabarit officiel dont chaque sommet prend la position du sommet de même UV dans la cage
	réelle du corps bloc (aucune déformation au repos). La tête (cage non téléchargeable) garde le recalage sur blocs."""
	me_g = charger_gabarit()
	verts_g = [g(v.co.x, v.co.y, v.co.z) for v in me_g.vertices]
	segs = segments_cage()
	pos, attrib = recaler_cage(verts_g, segs)
	# directions de poussée de la cage externe : normales de la cage recalée sur les blocs (la cage réelle a des
	# sommets confondus, donc des faces dégénérées aux normales fausses)
	me_dir = me_g.copy()
	for v, p in zip(me_dir.vertices, pos):
		v.co = p
	me_dir.update()
	NORMALES_CAGE[:] = [v.normal.normalized() for v in me_dir.vertices]
	bpy.data.meshes.remove(me_dir)
	pts, kd = cage_corps_bloc()
	uv = me_g.uv_layers[0].data
	uvs = {}
	for poly in me_g.polygons:
		for li, vi in zip(poly.loop_indices, poly.vertices):
			uvs.setdefault(vi, []).append(uv[li].uv.copy())
	exacts = 0
	for vi, liste in uvs.items():
		for u in liste:
			_, i, dist = kd.find(Vector((u.x, u.y, 0)))
			if dist < 1e-3:
				pos[vi] = pts[i][0]
				exacts += 1
				break
	print(f"cage interne : {exacts} sommets sur {len(verts_g)} pris sur la cage réelle du corps, les autres (tête) recalés")
	me = me_g.copy()
	me.name = "cage_interne_R15"
	for v, p in zip(me.vertices, pos):
		v.co = p
	me.update()
	print("cage : %d sommets, %d faces, UV %s ; sommets par segment : %s" % (
		len(me.vertices), len(me.polygons), [u.name for u in me.uv_layers], {sg["nom"]: sg["nb"] for sg in segs}))  # fmt: skip
	segment_par_sommet = [segs[k]["nom"] for k in attrib]
	return me, segment_par_sommet


NORMALES_CAGE = []
POUSSEE_MAX = 0.45  # écart max cage externe / interne (évite les pointes aux sommets confondus)


def cage_externe(me_int, vetement, marge=0.045, portee=0.9, exclus=frozenset()):
	"""Cage externe : la cage interne poussée le long des normales jusqu'au-delà du vêtement, lissée ;
	là où il n'y a pas de vêtement, elle reste sur la cage interne."""
	vs = [vetement.matrix_world @ v.co for v in vetement.data.vertices]
	bvh = BVHTree.FromPolygons(vs, [tuple(p.vertices) for p in vetement.data.polygons])
	n = len(me_int.vertices)
	besoin = [0.0] * n
	for i, v in enumerate(me_int.vertices):
		nrm = NORMALES_CAGE[i]
		org = v.co - nrm * 0.25
		loin = None
		o = org.copy()
		parcours = 0.0
		while parcours < portee:
			hit, _, _, dist = bvh.ray_cast(o, nrm, portee - parcours)
			if hit is None:
				break
			loin = hit
			parcours += dist + 1e-4
			o = hit + nrm * 1e-4
		if loin is not None and i not in exclus:
			besoin[i] = min(POUSSEE_MAX, max(0.0, (loin - v.co).dot(nrm) + marge))
	voisins = [[] for _ in range(n)]
	for e in me_int.edges:
		a, b = e.vertices
		voisins[a].append(b)
		voisins[b].append(a)
	base = [v.co.copy() for v in me_int.vertices]
	normales = NORMALES_CAGE
	faces = [tuple(p.vertices) for p in me_int.polygons]
	# faces de cage qu'on peut pousser (pas celles des bras pour un vêtement du bas : la main touche la hanche)
	poussables = [f for f in faces if not any(v in exclus for v in f)]

	def lisser(bes):
		d = bes[:]
		for _ in range(6):
			d = [bes[i] if i in exclus else max(bes[i], 0.6 * sum(d[j] for j in voisins[i]) / max(1, len(voisins[i]))) for i in range(n)]
		return d

	# tant que des sommets du vêtement sortent de la cage (test de parité), on pousse la face de cage la plus proche
	dep = lisser(besoin)
	for iteration in range(25):
		pos = [base[i] + normales[i] * dep[i] for i in range(n)]
		bvh_c = BVHTree.FromPolygons(pos, poussables)
		enr = Enroulement(pos, faces)
		dehors = [p for p in vs if not enr.dedans(p)]
		if not dehors:
			break
		for p in dehors:
			_, _, idx, dist = bvh_c.find_nearest(p)
			for vi in poussables[idx]:
				besoin[vi] = min(POUSSEE_MAX, max(besoin[vi], dep[vi] + dist + marge * 0.5))
		dep = lisser(besoin)
	CAGE_ITERATIONS[vetement.name] = iteration + 1
	me = me_int.copy()
	for i, v in enumerate(me.vertices):
		v.co = base[i] + normales[i] * dep[i]  # noqa
	me.update()
	return me


CAGE_ITERATIONS = {}


class Enroulement:
	"""Intérieur d'un maillage fermé par nombre d'enroulement généralisé (somme des angles solides) :
	reste juste quand la cage se recoupe (entre les jambes, aux aisselles), contrairement à la parité."""

	def __init__(self, pos, faces):
		tris = []
		for f in faces:
			for k in range(1, len(f) - 1):
				tris.append((f[0], f[k], f[k + 1]))
		P = np.array([tuple(p) for p in pos], dtype=np.float64)
		T = np.array(tris, dtype=np.int64)
		self.a, self.b, self.c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]

	def valeur(self, p):
		q = np.array(tuple(p), dtype=np.float64)
		a, b, c = self.a - q, self.b - q, self.c - q
		la, lb, lc = (np.linalg.norm(x, axis=1) for x in (a, b, c))
		det = np.einsum("ij,ij->i", a, np.cross(b, c))
		den = la * lb * lc + np.einsum("ij,ij->i", a, b) * lc + np.einsum("ij,ij->i", b, c) * la + np.einsum("ij,ij->i", c, a) * lb
		return float(np.sum(2 * np.arctan2(det, den)) / (4 * math.pi))

	def dedans(self, p):
		return abs(self.valeur(p)) > 0.5


# ================================================================ SKINNING
def lisse(t):
	t = min(1.0, max(0.0, t))
	return t * t * (3 - 2 * t)


def poids_vertex(p, chaine, cote=None):
	"""Poids R15 lissés d'un sommet de vêtement (coordonnées Blender).
	chaine « corps » : UpperTorso / LowerTorso / jambes (taille, hanches, genoux, chevilles) ;
	chaine « bras » : bras du côté du sommet (coude, poignet)."""
	x, z = p.x, p.z
	w = {}

	def ajoute(os_, val):
		if val > 1e-4:
			w[os_] = w.get(os_, 0.0) + val

	if chaine == "bras":
		c = "Left" if x > 0 else "Right"
		ze, zp = ART[c + "Elbow"].z, ART[c + "Wrist"].z
		t = lisse((ze + 0.12 - z) / 0.24)  # 0 au-dessus du coude, 1 en dessous
		u = lisse((zp + 0.08 - z) / 0.16)
		ajoute(c + "UpperArm", 1 - t)
		ajoute(c + "LowerArm", t * (1 - u))
		ajoute(c + "Hand", t * u)
		return w
	z_taille, z_hanche, z_genou, z_cheville = ART["Waist"].z, ART["Root"].z, ART["LeftKnee"].z, ART["LeftAnkle"].z
	t_taille = lisse((z_taille + 0.12 - z) / 0.24)  # 0 = UpperTorso, 1 = en dessous
	t_hanche = lisse((z_hanche + 0.15 - z) / 0.30)  # 1 = jambe
	t_genou = lisse((z_genou + 0.15 - z) / 0.30)
	t_cheville = lisse((z_cheville + 0.10 - z) / 0.20)
	# +x = gauche du perso ; partage gauche / droite seulement sur l'axe (bas du bassin, milieu du panneau)
	gauche = {"Left": 1.0, "Right": 0.0}.get(cote, lisse((x + 0.01) / 0.02))
	ajoute("UpperTorso", 1 - t_taille)
	bas = t_taille
	ajoute("LowerTorso", bas * (1 - t_hanche))
	jambe = bas * t_hanche
	for c, f in (("Left", gauche), ("Right", 1 - gauche)):
		ajoute(c + "UpperLeg", jambe * f * (1 - t_genou))
		ajoute(c + "LowerLeg", jambe * f * t_genou * (1 - t_cheville))
		ajoute(c + "Foot", jambe * f * t_genou * t_cheville)
	return w


def skinner(ob, arm, chaine, cote=None):
	groupes = {}
	trop = 0
	for v in ob.data.vertices:
		w = poids_vertex(ob.matrix_world @ v.co, chaine, cote)
		w = dict(sorted(w.items(), key=lambda kv: -kv[1])[:4])
		trop += len(w) > 4
		tot = sum(w.values())
		for os_, val in w.items():
			if os_ not in groupes:
				groupes[os_] = ob.vertex_groups.new(name=os_)
			groupes[os_].add([v.index], val / tot, "REPLACE")
	ob.parent = arm
	mod = ob.modifiers.new("Armature", "ARMATURE")
	mod.object = arm
	return sorted(groupes)


# ================================================================ ASSEMBLAGE / CONTRÔLES / EXPORT
def assembler(groupe, nom_final):
	src = list(COLL["Pieces_" + groupe].objects)
	copies = []
	for o in src:
		c = o.copy()
		c.data = o.data.copy()
		collection("Export").objects.link(c)
		copies.append(c)
	with bpy.context.temp_override(active_object=copies[0], object=copies[0], selected_objects=copies, selected_editable_objects=copies):
		bpy.ops.object.join()
	ob = copies[0]
	if nom_final in bpy.data.objects and bpy.data.objects[nom_final] is not ob:
		bpy.data.objects[nom_final].name = nom_final + "_element"  # l'élément homonyme garde un nom distinct
	ob.name = nom_final
	ob.data.name = nom_final
	return ob


def triangles(me):
	return sum(len(p.vertices) - 2 for p in me.polygons)


def aretes_ouvertes(me):
	bm = bmesh.new()
	bm.from_mesh(me)
	n = sum(1 for e in bm.edges if len(e.link_faces) != 2)
	bm.free()
	return n


def coplanaires(me, tol_d=0.003):
	"""Paires de faces d'éléments différents dans le même plan et qui se recouvrent."""
	elem = [0] * len(me.polygons)
	me.attributes["element"].data.foreach_get("value", elem)
	faces = []
	for p in me.polygons:
		nrm = p.normal.copy()
		signe = 1
		for c in nrm:
			if abs(c) > 1e-6:
				signe = 1 if c > 0 else -1
				break
		nc = nrm * signe
		cle = tuple(round(c, 2) for c in nc)
		pts = [me.vertices[i].co for i in p.vertices]
		faces.append((cle, nc.dot(pts[0]), signe, elem[p.index], pts, nc))
	par_cle = {}
	for f in faces:
		par_cle.setdefault(f[0], []).append(f)
	paires = []
	for liste in par_cle.values():
		liste.sort(key=lambda f: f[1])
		for i, a in enumerate(liste):
			for b in liste[i + 1 :]:
				if b[1] - a[1] > tol_d:
					break
				if a[3] == b[3]:
					continue
				if recouvrement(a[4], b[4], a[5]):
					paires.append(tuple(sorted((ELEMENTS[a[3]][1], ELEMENTS[b[3]][1]))) + ("face à face" if a[2] != b[2] else "même sens",))
	return sorted(set(paires))


def recouvrement(pa, pb, nrm, eps=1e-3):
	"""Deux faces convexes du même plan se recouvrent-elles (théorème de l'axe séparateur, en 2D) ?"""
	u = nrm.orthogonal().normalized()
	v = nrm.cross(u)
	A = [(p.dot(u), p.dot(v)) for p in pa]
	B = [(p.dot(u), p.dot(v)) for p in pb]
	for poly in (A, B):
		for i in range(len(poly)):
			x0, y0 = poly[i]
			x1, y1 = poly[(i + 1) % len(poly)]
			ax = (y0 - y1, x1 - x0)
			nn = math.hypot(*ax)
			if nn < 1e-9:
				continue
			ax = (ax[0] / nn, ax[1] / nn)
			pA = [x * ax[0] + y * ax[1] for x, y in A]
			pB = [x * ax[0] + y * ax[1] for x, y in B]
			if min(max(pA), max(pB)) - max(min(pA), min(pB)) <= eps:
				return False
	return True


def boite_roblox(ob):
	"""Boîte (Blender) -> centre Roblox (relatif au HRP) et taille Roblox (X, Y, Z)."""
	vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
	mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
	mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
	c = (mn + mx) / 2
	return c, mn, mx


def vers_roblox_delta(d):
	return [round(-d.x + 0.0, 4), round(d.z + 0.0, 4), round(d.y + 0.0, 4)]


def taille_roblox(mn, mx):
	d = mx - mn
	return [round(d.x, 4), round(d.z, 4), round(d.y, 4)]


def exporter(objets, chemin, armature=None):
	for o in bpy.context.view_layer.objects:
		o.select_set(False)
	sel = list(objets) + ([armature] if armature else [])
	for o in sel:
		o.select_set(True)
	bpy.context.view_layer.objects.active = sel[0]
	bpy.ops.export_scene.fbx(
		filepath=str(chemin), use_selection=True, object_types={"MESH", "ARMATURE"} if armature else {"MESH"},
		axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_ALL", path_mode="COPY", embed_textures=True,
		mesh_smooth_type="FACE", use_mesh_modifiers=False, add_leaf_bones=False, bake_anim=False,
		primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=False,
	)  # fmt: skip


def main():
	global MATERIAU
	EXPORT.mkdir(exist_ok=True)
	bpy.ops.wm.read_factory_settings(use_empty=True)
	MATERIAU = creer_atlas()
	arm = creer_rig()

	construire_salopette()
	construire_chaussures()
	construire_brassard()
	construire_tete()
	construire_sac()
	construire_arme()

	me_int, seg_cage = construire_cage_interne()
	cage_ob = bpy.data.objects.new("cage_interne_R15", me_int)
	collection("Rig_R15").objects.link(cage_ob)

	rapport = {"unites": "studs ; positions Roblox relatives au HumanoidRootPart (Y haut, avant -Z, droite +X)", "pieces": {}}
	corps_enr = Enroulement([v.co for v in me_int.vertices], [tuple(p.vertices) for p in me_int.polygons])

	# ---- layered clothing
	for groupe, fichier, type_lc in (
		("salopette", "salopette", "Pants"),
		("chaussure_gauche", "chaussure_gauche", "LeftShoe"),
		("chaussure_droite", "chaussure_droite", "RightShoe"),
		("brassard", "brassard", "Jacket"),
	):
		ob = assembler(groupe, groupe)
		inner = bpy.data.objects.new(groupe + "_InnerCage", me_int.copy())
		inner.data.name = inner.name
		bras = frozenset(i for i, sg in enumerate(seg_cage) if "Arm" in sg or "Hand" in sg)
		outer = bpy.data.objects.new(groupe + "_OuterCage", cage_externe(me_int, ob, exclus=frozenset() if groupe == "brassard" else bras))
		outer.data.name = outer.name
		for c in (inner, outer):
			collection("Export").objects.link(c)
			c.hide_render = True
		cote = {"chaussure_gauche": "Left", "chaussure_droite": "Right"}.get(groupe)
		os_ = skinner(ob, arm, "bras" if groupe == "brassard" else "corps", cote)
		ext_enr = Enroulement([v.co for v in outer.data.vertices], [tuple(p.vertices) for p in outer.data.polygons])
		vs = [v.co for v in ob.data.vertices]
		hors = [p for p in vs if not ext_enr.dedans(p)]
		hors_ext = len(hors)
		for p in hors[:12]:
			print(f"  {groupe} hors cage externe : ({p.x:.3f}, {p.y:.3f}, {p.z:.3f}) enroulement {ext_enr.valeur(p):.2f}")
		dans_corps = sum(1 for p in vs if corps_enr.dedans(p))
		c, mn, mx = boite_roblox(ob)
		att = rb(R15["attachments"]["LowerTorso"]["WaistCenterAttachment"][:3])
		rapport["pieces"][groupe] = {
			"type": "layered", "accessoire": type_lc, "triangles": triangles(ob.data), "aretes_ouvertes": aretes_ouvertes(ob.data),
			"coplanaires": coplanaires(ob.data), "os": os_, "sommets_hors_cage_externe": hors_ext,
			"sommets_dans_cage_interne": dans_corps, "sommets": len(vs), "iterations_cage_externe": CAGE_ITERATIONS.get(groupe),
			"taille_roblox": taille_roblox(mn, mx), "centre_roblox": vers_roblox_delta(c - Vector((0, 0, H))),
			"ecart_max_au_WaistCenterAttachment": round(max((mx - att).length, (mn - att).length), 3),
		}  # fmt: skip
		rapport["pieces"][groupe]["_objets"] = (ob, inner, outer)

	# ---- accessoires rigides et Tool
	rigides = (
		("chapeau", "Hat", ("Head", "HatAttachment")),
		("cheveux", "Hair", ("Head", "HairAttachment")),
		("sac", "Back", ("UpperTorso", "BodyBackAttachment")),
		("lance_pierre", "Tool", None),
	)
	for groupe, type_acc, att in rigides:
		ob = assembler(groupe, "Handle" if groupe == "lance_pierre" else groupe)
		c, mn, mx = boite_roblox(ob)
		info = {
			"type": "rigide", "accessoire": type_acc, "triangles": triangles(ob.data), "aretes_ouvertes": aretes_ouvertes(ob.data),
			"coplanaires": coplanaires(ob.data), "taille_roblox": taille_roblox(mn, mx),
		}  # fmt: skip
		if att:
			p_att = att_b(*att)
			info["attachment"] = att[1]
			info["centre_roblox"] = vers_roblox_delta(c - Vector((0, 0, H)))
			info["attachment_dans_Handle"] = vers_roblox_delta(p_att - c)
			# étendue par rapport à l'attachment (pour les boîtes limites, axes de l'attachment = axes du perso)
			a, b = vers_roblox_delta(mn - p_att), vers_roblox_delta(mx - p_att)
			info["etendue_depuis_attachment"] = {"min": [min(u, v) for u, v in zip(a, b)], "max": [max(u, v) for u, v in zip(a, b)]}
		else:
			info["centre_handle_depuis_prise"] = vers_roblox_delta(c)
			info["Tool.Grip_position"] = vers_roblox_delta(-c)
		rapport["pieces"][groupe] = info
		rapport["pieces"][groupe]["_objets"] = (ob,)
	# le Handle du Tool est construit à l'origine : on le range à côté du perso pour l'aperçu dans le .blend
	# (l'export se fait à l'origine, voir plus bas)

	# ---- exports
	for groupe, info in rapport["pieces"].items():
		objets = info.pop("_objets")
		if info["type"] == "layered":
			if groupe.startswith("chaussure"):
				exporter(objets, EXPORT / f"{groupe}.fbx", arm)
			else:
				exporter(objets, EXPORT / f"{groupe}.fbx", arm)
			info["_objets"] = objets
		else:
			exporter(objets, EXPORT / f"{groupe}.fbx")
	chs = rapport["pieces"]["chaussure_gauche"]["_objets"] + rapport["pieces"]["chaussure_droite"]["_objets"]
	exporter(chs, EXPORT / "chaussures.fbx", arm)
	for info in rapport["pieces"].values():
		info.pop("_objets", None)

	rapport["palette"] = {nom: {"hex": "#" + hx, "rugosite": r, "metal": mt, "uv": [round(c, 4) for c in uv_couleur(nom)]} for nom, hx, r, mt in PALETTE}  # fmt: skip
	rapport["brassard_os"] = BRASSARD_OS
	rapport["elements"] = {}
	for grp, nom in ELEMENTS:
		rapport["elements"].setdefault(grp, []).append(nom)
	(EXPORT / "offsets.json").write_text(json.dumps(rapport, ensure_ascii=False, indent="\t"), encoding="utf-8")
	COLL["Pieces_nommees"].hide_render = True
	COLL["Pieces_nommees"].hide_viewport = True
	bpy.ops.wm.save_as_mainfile(filepath=str(EXPORT / "tenue_r15.blend"))

	print("\n=== CONTRÔLES ===")
	ok = True
	for grp, info in rapport["pieces"].items():
		alerte = []
		if info["triangles"] > LIMITE_TRIS:
			alerte.append("TROP DE TRIANGLES")
		if info["aretes_ouvertes"]:
			alerte.append(f"{info['aretes_ouvertes']} arêtes ouvertes")
		if info["coplanaires"]:
			alerte.append(f"{len(info['coplanaires'])} paires coplanaires")
		if info.get("sommets_hors_cage_externe"):
			alerte.append(f"{info['sommets_hors_cage_externe']} sommets hors cage externe")
		ok &= not alerte
		print(f"{grp:18s} {info['accessoire']:9s} {info['triangles']:5d} tris  taille {info['taille_roblox']}  {' ; '.join(alerte) or 'OK'}")
		for p in info["coplanaires"][:12]:
			print("      coplanaire :", p)
	print("durée : %.1f s" % (time.time() - DEBUT))
	return ok


if __name__ == "__main__":
	main()
	if "--quitter" in sys.argv:
		bpy.ops.wm.quit_blender()
