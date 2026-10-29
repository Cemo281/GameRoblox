"""Construit assets/persos/_mannequin/mannequin.blend a partir de r15_bloc.json et zones_vetements.json.

A lancer DANS Blender (MCP Blender) :
	exec(open(r"<depot>/assets/persos/_mannequin/construire_mannequin.py", encoding="utf-8").read())
Vide la scene courante : ouvrir d'abord un fichier vide (Fichier > Nouveau) apres avoir enregistre le travail en cours.

Repere : 1 unite = 1 stud, le perso regarde vers -Y, sa droite est -X, pieds a Z = 0.
Blender (x, y, z) = (-xR, zR, yR + hauteurHRP).
"""

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

DOSSIER = Path(r"C:\Users\alice\Documents\GameRoblox\assets\persos\_mannequin")
RIG = json.loads((DOSSIER / "r15_bloc.json").read_text(encoding="utf-8"))
ZONES = json.loads((DOSSIER / "zones_vetements.json").read_text(encoding="utf-8"))["zones"]
H = RIG["hauteurHRP"]
LARG, HAUT = 585, 559  # taille des modeles de vetements
PEAU = (163 / 255, 162 / 255, 165 / 255)
RETRAIT = 0.01  # retrait des prolongements caches (evite le z-fighting)
HAUTEUR_FACE = 1.17  # hauteur projetee par le Decal face (calibree sur captures Studio)

# piece -> (groupe de zones, lignes [debut, fin] des faces laterales, a une face Top, a une face Bottom)
PIECES = {}
for cote, sens in (("Right", "droit"), ("Left", "gauche")):
	sens_j = "droite" if sens == "droit" else "gauche"
	PIECES[cote + "UpperArm"] = ("bras_" + sens, cote + "UpperArm", True, False)
	PIECES[cote + "LowerArm"] = ("bras_" + sens, cote + "LowerArm", False, False)
	PIECES[cote + "Hand"] = ("bras_" + sens, cote + "Hand", False, True)
	PIECES[cote + "UpperLeg"] = ("jambe_" + sens_j, cote + "UpperLeg", True, False)
	PIECES[cote + "LowerLeg"] = ("jambe_" + sens_j, cote + "LowerLeg", False, False)
	PIECES[cote + "Foot"] = ("jambe_" + sens_j, cote + "Foot", False, True)
PIECES["UpperTorso"] = ("torse", "UpperTorso", True, False)
PIECES["LowerTorso"] = ("torse", "LowerTorso", False, True)

# prolongements caches des maillages Roblox (y Roblox) : (piece, y_depart, y_arrivee, lignes)
# lignes = bande du modele etiree sur le prolongement, comme dans Studio
PROLONGEMENTS = []
for cote in ("Right", "Left"):
	PROLONGEMENTS += [
		(cote + "UpperArm", 0.073, -0.193, (60, 64)),
		(cote + "LowerArm", 0.073, 0.357, (56, 64)),
		(cote + "LowerArm", -0.708, -0.761, (108, 112)),
		(cote + "UpperLeg", -1.920, -2.153, (60, 64)),
		(cote + "LowerLeg", -1.920, -1.684, (56, 64)),
		(cote + "LowerLeg", -2.880, -2.984, (108, 112)),
	]

MATERIAU = {"torse": "Mat_Torse", "bras": "Mat_Bras", "jambe": "Mat_Jambes"}


def vers_blender(x, y, z):
	return Vector((-x, z, y + H))


def uv_px(px, py):
	return (px / LARG, 1 - py / HAUT)


def boite_blender(ext):
	"""Etendues Roblox [[x],[y],[z]] -> (x0, x1, y0, y1, z0, z1) Blender."""
	(xa, xb), (ya, yb), (za, zb) = ext
	return (-xb, -xa, za, zb, ya + H, yb + H)


def ajouter_boite(bm, uvl, b, groupe, lignes, top, bottom, idx_mat):
	"""Boite Blender b = (x0, x1, y0, y1, z0, z1), UV selon zones_vetements.json."""
	x0, x1, y0, y1, z0, z1 = b
	faces_z = ZONES[groupe]["faces"]
	r0, r1 = lignes

	def cote(nom, f_h, z):
		x, y, w, _ = faces_z[nom]["rect"]
		ligne = r0 + (z1 - z) / (z1 - z0) * (r1 - r0)
		return uv_px(x + f_h * w, y + ligne)

	def capuchon(nom, f_h, f_v):
		x, y, w, h = faces_z[nom]["rect"]
		return uv_px(x + f_h * w, y + f_v * h)

	def bande(f_h, ligne):
		# capuchon cache : ligne unique de la face avant
		x, y, w, _ = faces_z["Front"]["rect"]
		return uv_px(x + f_h * w, y + ligne)

	fx = lambda x: (x - x0) / (x1 - x0)
	fy = lambda y: (y - y0) / (y1 - y0)
	# (sommets, fonction UV) ; sommets dans l'ordre anti-horaire vu de l'exterieur
	faces = [
		([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], lambda p: cote("Front", fx(p[0]), p[2])),
		([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], lambda p: cote("Back", 1 - fx(p[0]), p[2])),
		([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], lambda p: cote("Right", 1 - fy(p[1]), p[2])),
		([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], lambda p: cote("Left", fy(p[1]), p[2])),
		(
			[(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
			(lambda p: capuchon("Top", fx(p[0]), 1 - fy(p[1]))) if top else (lambda p: bande(fx(p[0]), r0 + 0.5)),
		),
		(
			[(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
			(lambda p: capuchon("Bottom", fx(p[0]), fy(p[1]))) if bottom else (lambda p: bande(fx(p[0]), r1 - 0.5)),
		),
	]
	for coins, f_uv in faces:
		vs = [bm.verts.new(c) for c in coins]
		f = bm.faces.new(vs)
		f.material_index = idx_mat
		for loop in f.loops:
			loop[uvl].uv = f_uv(tuple(loop.vert.co))


def materiau_corps(nom, couches):
	"""Peau, puis chaque image (Pants, Shirt) melangee par son alpha."""
	m = bpy.data.materials.new(nom)
	m.use_nodes = True
	nt = m.node_tree
	bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
	bsdf.inputs["Roughness"].default_value = 1.0
	peau = nt.nodes.new("ShaderNodeRGB")
	peau.name = peau.label = "Peau"
	peau.outputs[0].default_value = (*PEAU, 1)
	sortie = peau.outputs[0]
	for i, img_nom in enumerate(couches):
		tex = nt.nodes.new("ShaderNodeTexImage")
		tex.name = tex.label = img_nom
		tex.image = bpy.data.images[img_nom]
		tex.extension = "CLIP"
		mix = nt.nodes.new("ShaderNodeMix")
		mix.data_type = "RGBA"
		nt.links.new(tex.outputs["Alpha"], mix.inputs["Factor"])
		nt.links.new(sortie, mix.inputs[6])
		nt.links.new(tex.outputs["Color"], mix.inputs[7])
		sortie = mix.outputs[2]
		tex.location = (-700, 300 - 300 * i)
		mix.location = (-300, 300 - 300 * i)
	nt.links.new(sortie, bsdf.inputs["Base Color"])
	return m


def charger_images():
	for nom, fichier in (("Shirt", "test_shirt.png"), ("Pants", "test_pants.png"), ("Face", "test_face.png")):
		img = bpy.data.images.load(str(DOSSIER / fichier))
		img.name = nom
		img.filepath = "//" + fichier


def tete(bm_mat_tete):
	"""Tete classique : cylindre aux aretes arrondies (diametre et hauteur de r15_bloc.json)."""
	info = RIG["blocs_visibles"]["Head"]
	c = vers_blender(*info["centre"])
	r, hh, rc, seg = info["diametre"] / 2, info["hauteur"] / 2, info["rayon_arrondi"], 32
	# profil (rayon, z) de bas en haut, coins arrondis
	profil = [(0.0, -hh)]
	for k in range(7):
		a = -math.pi / 2 + k * (math.pi / 2) / 6
		profil.append((r - rc + rc * math.cos(a), -hh + rc + rc * math.sin(a)))
	for k in range(7):
		a = k * (math.pi / 2) / 6
		profil.append((r - rc + rc * math.cos(a), hh - rc + rc * math.sin(a)))
	profil.append((0.0, hh))
	me = bpy.data.meshes.new("Head")
	bm = bmesh.new()
	anneaux = []
	for rr, zz in profil:
		if rr < 1e-6:
			anneaux.append([bm.verts.new((0, 0, zz))])
		else:
			anneaux.append([bm.verts.new((rr * math.cos(2 * math.pi * s / seg), rr * math.sin(2 * math.pi * s / seg), zz)) for s in range(seg)])
	for a, b in zip(anneaux, anneaux[1:]):
		for s in range(seg):
			if len(a) == 1:
				bm.faces.new((a[0], b[s], b[(s + 1) % seg]))
			elif len(b) == 1:
				bm.faces.new((a[s], a[(s + 1) % seg], b[0]))
			else:
				bm.faces.new((a[s], a[(s + 1) % seg], b[(s + 1) % seg], b[s]))
	bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
	bm.to_mesh(me)
	bm.free()
	for p in me.polygons:
		p.use_smooth = True
	me.materials.append(bm_mat_tete)
	o = bpy.data.objects.new("Head", me)
	o.location = c
	bpy.context.scene.collection.objects.link(o)

	# Face : coque de l'avant de la tete (|angle| <= 45 deg), decalee de 0,004.
	# Comme le Decal de Studio (r15_bloc.json, "face") : u selon l'angle, v en projection plane.
	me_f = bpy.data.meshes.new("Face")
	bm = bmesh.new()
	bm.from_mesh(me)
	bm.normal_update()
	angle = lambda p: math.degrees(math.atan2(p.x, -p.y))
	hors = [f for f in bm.faces if f.normal.y > -0.05 or abs(angle(f.calc_center_median())) > 45]
	bmesh.ops.delete(bm, geom=hors, context="FACES")
	bm.normal_update()
	for v in bm.verts:
		v.co += v.normal * 0.004
	uvl = bm.loops.layers.uv.new("UVMap")
	zc = vers_blender(0, 1.598031, 0).z - c.z  # centre du Decal = centre de la piece Head
	for f in bm.faces:
		for loop in f.loops:
			p = loop.vert.co
			loop[uvl].uv = (0.5 + angle(p) / 120, 0.5 + (p.z - zc) / HAUTEUR_FACE)
	bm.to_mesh(me_f)
	bm.free()
	for p in me_f.polygons:
		p.use_smooth = True
	mf = bpy.data.materials.new("Mat_Face")
	mf.use_nodes = True
	nt = mf.node_tree
	bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
	bsdf.inputs["Roughness"].default_value = 1.0
	tex = nt.nodes.new("ShaderNodeTexImage")
	tex.name = tex.label = "Face"
	tex.image = bpy.data.images["Face"]
	tex.extension = "CLIP"
	nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
	nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
	try:
		mf.blend_method = "BLEND"
	except (AttributeError, TypeError):
		pass
	try:
		mf.surface_render_method = "BLENDED"
	except (AttributeError, TypeError):
		pass
	me_f.materials.append(mf)
	of = bpy.data.objects.new("Face", me_f)
	of.location = c
	bpy.context.scene.collection.objects.link(of)
	return o, of


def armature():
	"""Un os par Motor6D (+ HumanoidRootPart), tous verticaux, tete de l'os a l'articulation."""
	art = RIG["blender"]["articulations"]
	motor_de = {m["part1"]: nom for nom, m in RIG["motors"].items()}
	parent_de = {m["part1"]: m["part0"] for m in RIG["motors"].values()}
	fin = {"LowerTorso": art["Waist"][2], "UpperTorso": art["Neck"][2], "Head": art["Neck"][2] + 1.3}  # z de la queue
	ad = bpy.data.armatures.new("Rig_R15")
	ob = bpy.data.objects.new("Rig_R15", ad)
	bpy.context.scene.collection.objects.link(ob)
	bpy.context.view_layer.objects.active = ob
	bpy.ops.object.mode_set(mode="EDIT")
	eb = ad.edit_bones
	b = eb.new("HumanoidRootPart")
	b.head, b.tail = (0, 0, H), (0, 0, H + 1)
	ordre = ["LowerTorso", "UpperTorso", "Head"]
	for cote in ("Left", "Right"):
		ordre += [cote + n for n in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot")]
	suivant = {"UpperArm": "Elbow", "LowerArm": "Wrist", "UpperLeg": "Knee", "LowerLeg": "Ankle"}
	for nom in ordre:
		m = motor_de[nom]
		tete_os = Vector(art[m])
		if nom in fin:
			queue = Vector((tete_os.x, tete_os.y, fin[nom]))
		else:
			cote = "Left" if nom.startswith("Left") else "Right"
			seg = nom[len(cote):]
			if seg in suivant:
				zq = art[cote + suivant[seg]][2]
			elif seg == "Hand":
				zq = tete_os.z - 0.29
			else:  # Foot
				zq = 0.0
			queue = Vector((tete_os.x, tete_os.y, zq))
		b = eb.new(nom)
		b.head, b.tail = tete_os, queue
		b.roll = 0
		b.parent = eb[parent_de[nom]]
	bpy.ops.object.mode_set(mode="OBJECT")
	for nom, m in motor_de.items():
		ad.bones[nom]["motor6d"] = m
	return ob


def parenter(obj, rig, os_nom):
	"""Parentage rigide a l'os, sans poids : l'objet garde sa place dans le monde."""
	bpy.context.view_layer.update()
	mw = obj.matrix_world.copy()
	obj.parent = rig
	obj.parent_type = "BONE"
	obj.parent_bone = os_nom
	pb = rig.pose.bones[os_nom]
	# Blender parente au bout de l'os : inverse de la matrice monde du bout de l'os au repos
	m_os = rig.matrix_world @ pb.bone.matrix_local @ Matrix.Translation((0, pb.bone.length, 0))
	obj.matrix_parent_inverse = m_os.inverted()
	obj.matrix_basis = mw


def construire():
	# repart de zero (un read_homefile depuis un script casse le contexte des operateurs)
	if bpy.context.object and bpy.context.object.mode != "OBJECT":
		bpy.ops.object.mode_set(mode="OBJECT")
	for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.images, bpy.data.cameras, bpy.data.lights, bpy.data.worlds):
		for d in list(coll):
			coll.remove(d)
	sc = bpy.context.scene
	sc.unit_settings.system = "METRIC"
	sc.unit_settings.scale_length = 1.0
	charger_images()
	mats = {
		"Mat_Torse": materiau_corps("Mat_Torse", ["Pants", "Shirt"]),
		"Mat_Bras": materiau_corps("Mat_Bras", ["Shirt"]),
		"Mat_Jambes": materiau_corps("Mat_Jambes", ["Pants"]),
	}
	mat_tete = bpy.data.materials.new("Mat_Tete")
	mat_tete.use_nodes = True
	bs = next(n for n in mat_tete.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
	bs.inputs["Base Color"].default_value = (*PEAU, 1)
	bs.inputs["Roughness"].default_value = 1.0

	rig = armature()
	art = RIG["blender"]["articulations"]
	motor_de = {m["part1"]: nom for nom, m in RIG["motors"].items()}
	for nom, (groupe, cle_lignes, top, bottom) in PIECES.items():
		lignes = tuple(ZONES[groupe]["lignes_des_faces_laterales"][cle_lignes])
		mat = mats[MATERIAU[groupe.split("_")[0]]]
		me = bpy.data.meshes.new(nom)
		me.materials.append(mat)
		bm = bmesh.new()
		uvl = bm.loops.layers.uv.new("UVMap")
		ajouter_boite(bm, uvl, boite_blender(RIG["blocs_visibles"][nom]), groupe, lignes, top, bottom, 0)
		(xa, xb), _, (za, zb) = RIG["blocs_visibles"][nom]
		for p_nom, ya, yb, l in PROLONGEMENTS:
			if p_nom != nom:
				continue
			ext = [[xa + RETRAIT, xb - RETRAIT], [min(ya, yb), max(ya, yb)], [za + RETRAIT, zb - RETRAIT]]
			ajouter_boite(bm, uvl, boite_blender(ext), groupe, l, False, False, 0)
		# origine au pivot de la piece
		pivot = Vector(art[motor_de[nom]])
		bm.transform(Matrix.Translation(-pivot))
		bm.to_mesh(me)
		bm.free()
		o = bpy.data.objects.new(nom, me)
		o.location = pivot
		sc.collection.objects.link(o)
		parenter(o, rig, nom)

	head, face = tete(mat_tete)
	for o in (head, face):
		# origine au cou
		cou = Vector(art["Neck"])
		decal = o.location - cou
		o.data.transform(Matrix.Translation(decal))
		o.location = cou
		parenter(o, rig, "Head")

	# HumanoidRootPart : boite invisible 2 x 1 x 2
	me = bpy.data.meshes.new("HumanoidRootPart")
	bm = bmesh.new()
	bmesh.ops.create_cube(bm, size=1.0)
	bm.transform(Matrix.Diagonal((2, 1, 2, 1)))
	bm.to_mesh(me)
	bm.free()
	o = bpy.data.objects.new("HumanoidRootPart", me)
	o.location = (0, 0, H)
	o.display_type = "WIRE"
	o.hide_render = True
	sc.collection.objects.link(o)
	parenter(o, rig, "HumanoidRootPart")

	# camera equivalente a celle de Studio (FOV vertical 70, 1436 x 720)
	cam = bpy.data.cameras.new("Camera_Studio")
	cam.sensor_fit = "VERTICAL"
	cam.angle_y = math.radians(70)
	co = bpy.data.objects.new("Camera_Studio", cam)
	sc.collection.objects.link(co)
	sc.camera = co
	sc.render.resolution_x, sc.render.resolution_y = 1436, 720
	sc.world = bpy.data.worlds.new("Monde")
	sc.world.use_nodes = True
	fond = next(n for n in sc.world.node_tree.nodes if n.type == "BACKGROUND")
	fond.inputs["Color"].default_value = (0.35, 0.55, 0.85, 1)
	fond.inputs["Strength"].default_value = 1.0
	try:
		sc.render.engine = "BLENDER_EEVEE_NEXT"
	except TypeError:
		try:
			sc.render.engine = "BLENDER_EEVEE"
		except TypeError:
			pass
	sc.view_settings.view_transform = "Standard"
	soleil = bpy.data.lights.new("Soleil", "SUN")
	soleil.energy = 2.5
	so = bpy.data.objects.new("Soleil", soleil)
	so.rotation_euler = (math.radians(50), 0, math.radians(30))
	sc.collection.objects.link(so)
	bpy.ops.wm.save_as_mainfile(filepath=str(DOSSIER / "mannequin.blend"), relative_remap=True)
	print("mannequin.blend enregistre")


def camera_studio(position, cible, decalage=(-14.0, 300.0, 0.0)):
	"""Place Camera_Studio comme screen_capture de Studio (coordonnees monde Studio du clone de test)."""
	dx, dy, dz = decalage
	p = Vector((-(position[0] - dx), position[2] - dz, position[1] - dy))
	c = Vector((-(cible[0] - dx), cible[2] - dz, cible[1] - dy))
	co = bpy.data.objects["Camera_Studio"]
	co.location = p
	co.rotation_euler = (c - p).to_track_quat("-Z", "Y").to_euler()


if __name__ == "__main__":
	construire()
