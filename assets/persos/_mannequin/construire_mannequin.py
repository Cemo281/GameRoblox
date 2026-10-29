"""Construit assets/persos/_mannequin/mannequin.blend (v2 « blocs arrondis ») a partir de r15_bloc.json.

A lancer DANS Blender (MCP Blender) :
	exec(open(r"<depot>/assets/persos/_mannequin/construire_mannequin.py", encoding="utf-8").read())
	construire()          # vide la scene, geometrie + UV + armature, ecrit uv_mannequin.json, enregistre
	# puis : uv run --with pillow assets/persos/_mannequin/peindre_mannequin.py
	charger_texture()     # recharge tex_corps_mannequin.png et enregistre
	poser({...})          # pose de test (rotations des os en degres, axes : axes_r15.json)
	exporter_fbx()        # mannequin.fbx (sans armature, origines au centre des boites) + section "mannequin" de r15_bloc.json

Repere : 1 unite = 1 stud, le perso regarde vers -Y, sa droite est -X, pieds a Z = 0.
Blender (x, y, z) = (-xR, zR, yR + hauteurHRP).
Atlas tex_corps_mannequin.png (1024 x 1024) : tete en haut (face au centre), pieces du corps en bas,
un patron en croix par piece (Droite | Avant | Gauche | Arriere, dessus au-dessus de l'avant, dessous en dessous).
"""

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

DOSSIER = Path(r"C:\Users\alice\Documents\GameRoblox\assets\persos\_mannequin")
RIG = json.loads((DOSSIER / "r15_bloc.json").read_text(encoding="utf-8"))
H = RIG["hauteurHRP"]
BLOCS = RIG["blocs_visibles"]
ART = RIG["blender"]["articulations"]
TEXTURE = "tex_corps_mannequin.png"
TAILLE_TEX = 1024
BISEAU, SEGMENTS = 0.15, 3
PEAU = (0.93, 0.78, 0.66)  # couleur de secours (viewport) ; la vraie couleur est dans la texture
# zones de l'atlas en pixels (x0, y0, x1, y1), origine en haut a gauche comme dans l'image
ZONE_TETE = (8, 8, 1016, 520)
ZONE_CORPS = (8, 532, 1016, 1016)
MARGE = 6  # pixels entre deux ilots
# cylindre de jointure (chevauchement) porte par la piece du bas : (rayon, longueur)
JOINTURES = {"LowerArm": ("Elbow", 0.47, 0.88), "LowerLeg": ("Knee", 0.455, 0.88)}
NOMS = ["UpperTorso", "LowerTorso"] + [c + n for c in ("Right", "Left") for n in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot")]
MOTOR_DE = {m["part1"]: nom for nom, m in RIG["r15"]["motors"].items()}
PARENT_DE = {m["part1"]: m["part0"] for m in RIG["r15"]["motors"].values()}


def vers_blender(x, y, z):
	return Vector((-x, z, y + H))


def vers_roblox(v):
	return [-v.x, v.z - H, v.y]


def boite(nom):
	"""Bloc visible en Blender : (x0, x1, y0, y1, z0, z1)."""
	(xa, xb), (ya, yb), (za, zb) = BLOCS[nom]
	return (-xb, -xa, za, zb, ya + H, yb + H)


def px_vers_uv(x, y):
	return (x / TAILLE_TEX, 1 - y / TAILLE_TEX)


# ---------------------------------------------------------------- pieces du corps


def objet_maillage(nom, me):
	o = bpy.data.objects.new(nom, me)
	bpy.context.scene.collection.objects.link(o)
	return o


def appliquer_modificateurs(o):
	with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], selected_editable_objects=[o]):
		for m in list(o.modifiers):
			bpy.ops.object.modifier_apply(modifier=m.name)


def bloc_arrondi(nom):
	"""Boite du bloc visible, aretes arrondies (biseau, normales durcies : faces planes bien planes)."""
	x0, x1, y0, y1, z0, z1 = boite(nom)
	me = bpy.data.meshes.new(nom)
	bm = bmesh.new()
	bmesh.ops.create_cube(bm, size=1.0)
	bm.transform(Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)))
	bm.to_mesh(me)
	bm.free()
	for p in me.polygons:
		p.use_smooth = True
	o = objet_maillage(nom, me)
	b = o.modifiers.new("Biseau", "BEVEL")
	b.width = min(BISEAU, 0.4 * min(x1 - x0, y1 - y0, z1 - z0))
	b.segments = SEGMENTS
	b.profile = 0.5
	b.limit_method = "NONE"
	b.harden_normals = True
	appliquer_modificateurs(o)
	return o


def jointure(nom):
	"""Cylindre d'axe X centre sur l'articulation du haut de la piece (coude, genou) : comble l'angle quand ca plie."""
	cote = "Left" if nom.startswith("Left") else "Right"
	art, rayon, longueur = JOINTURES[nom[len(cote) :]]
	c = Vector(ART[cote + art])
	me = bpy.data.meshes.new(nom + "_Jointure")
	bm = bmesh.new()
	bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=24, radius1=rayon, radius2=rayon, depth=longueur)
	bm.transform(Matrix.Translation(c) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
	bm.to_mesh(me)
	bm.free()
	for p in me.polygons:
		p.use_smooth = abs(p.normal.x) < 0.5  # cotes lisses, bouchons plats
	return objet_maillage(nom + "_Jointure", me), (rayon, longueur, c)


def classer(n):
	"""Face du patron d'apres la normale."""
	ax = max(range(3), key=lambda i: abs(n[i]))
	return {(0, -1): "Droite", (0, 1): "Gauche", (1, -1): "Avant", (1, 1): "Arriere", (2, 1): "Dessus", (2, -1): "Dessous"}[(ax, 1 if n[ax] > 0 else -1)]


def patron(nom):
	"""Taille (studs) des 6 faces et leur place dans la croix : {face: (x, y, l, h)}, y vers le bas."""
	x0, x1, y0, y1, z0, z1 = boite(nom)
	w, d, h = x1 - x0, y1 - y0, z1 - z0
	faces = {
		"Droite": (0, d, d, h),
		"Avant": (d, d, w, h),
		"Gauche": (d + w, d, d, h),
		"Arriere": (2 * d + w, d, w, h),
		"Dessus": (d, 0, w, d),
		"Dessous": (d, d + h, w, d),
	}
	return faces, (2 * d + 2 * w, 2 * d + h)


def uv_bloc(o, nom, origine_px, densite):
	"""UV du bloc : projection plane de chaque face sur sa case de la croix."""
	x0, x1, y0, y1, z0, z1 = boite(nom)
	faces, _ = patron(nom)
	me = o.data
	uv = me.uv_layers.new(name="UVMap")
	ox, oy = origine_px

	def coord(face, p):
		fx, fy, _, fh = faces[face]
		# (a, b) dans la case, en studs, b vers le bas
		a, b = {
			"Avant": (p.x - x0, z1 - p.z),
			"Arriere": (x1 - p.x, z1 - p.z),
			"Droite": (y1 - p.y, z1 - p.z),  # vue depuis -X : gauche de l'image = arriere
			"Gauche": (p.y - y0, z1 - p.z),  # vue depuis +X : gauche de l'image = avant
			"Dessus": (p.x - x0, y1 - p.y),  # bas de la case = bord avant
			"Dessous": (p.x - x0, p.y - y0),  # haut de la case = bord avant
		}[face]
		return px_vers_uv(ox + (fx + a) * densite, oy + (fy + b) * densite)

	for poly in me.polygons:
		face = classer(poly.normal)
		for li in poly.loop_indices:
			uv.data[li].uv = coord(face, me.vertices[me.loops[li].vertex_index].co)
	return {f: [round(ox + fx * densite, 2), round(oy + fy * densite, 2), round(fw * densite, 2), round(fh * densite, 2)] for f, (fx, fy, fw, fh) in faces.items()}


def uv_jointure(o, dims, origine_px, densite):
	"""Bande du cylindre (tour x longueur) puis les deux bouchons."""
	rayon, longueur, c = dims
	ox, oy = origine_px
	tour = 2 * math.pi * rayon
	me = o.data
	uv = me.uv_layers.new(name="UVMap")
	for poly in me.polygons:
		bouchon = abs(poly.normal.x) > 0.5
		angles = []
		for li in poly.loop_indices:
			p = me.vertices[me.loops[li].vertex_index].co - c
			angles.append(math.atan2(p.z, -p.y) % (2 * math.pi))
		couture = max(angles) - min(angles) > math.pi
		for li, ang in zip(poly.loop_indices, angles):
			p = me.vertices[me.loops[li].vertex_index].co - c
			if bouchon:
				dx = tour + (0 if p.x < 0 else 2 * rayon) + rayon
				uv.data[li].uv = px_vers_uv(ox + (dx + p.y) * densite, oy + (rayon - p.z) * densite)
			else:
				if couture and ang < math.pi:
					ang += 2 * math.pi
				uv.data[li].uv = px_vers_uv(ox + ang / (2 * math.pi) * tour * densite, oy + (p.x + longueur / 2) * densite)
	return [round(ox, 2), round(oy, 2), round((tour + 4 * rayon) * densite, 2), round(max(longueur, 2 * rayon) * densite, 2)]


def taille_ilots(nom):
	_, (lw, lh) = patron(nom)
	seg = nom[4:] if nom.startswith("Left") else nom[5:]
	j = None
	if seg in JOINTURES:
		_, rayon, longueur = JOINTURES[seg]
		j = (2 * math.pi * rayon + 4 * rayon, max(longueur, 2 * rayon))
	return (lw, lh), j


def ranger(densite):
	"""Rangement en etageres dans ZONE_CORPS. Renvoie {nom: (origine croix, origine jointure)} ou None."""
	x0, y0, x1, y1 = ZONE_CORPS
	rects = []
	for nom in NOMS:
		croix, j = taille_ilots(nom)
		rects.append((nom, "croix", croix))
		if j:
			rects.append((nom, "jointure", j))
	rects.sort(key=lambda r: -r[2][1])
	x, y, h_etagere = x0, y0, 0
	places = {}
	for nom, genre, (lw, lh) in rects:
		w, h = lw * densite, lh * densite
		if x + w > x1:
			x, y, h_etagere = x0, y + h_etagere + MARGE, 0
		if y + h > y1:
			return None
		places.setdefault(nom, {})[genre] = (x, y)
		x += w + MARGE
		h_etagere = max(h_etagere, h)
	return places


# ---------------------------------------------------------------- tete


def courbe_super(p, n, debut, fin):
	"""n parametres t de la superellipse |x|^p + |y|^p = 1 (x = cos, y = sin), espaces a longueur d'arc egale."""

	def pt(t):
		c, s = math.cos(t), math.sin(t)
		return (math.copysign(abs(c) ** (2 / p), c), math.copysign(abs(s) ** (2 / p), s))

	fin_ = 4000
	ts = [debut + (fin - debut) * k / fin_ for k in range(fin_ + 1)]
	cumul = [0.0]
	for a, b in zip(ts, ts[1:]):
		(xa, ya), (xb, yb) = pt(a), pt(b)
		cumul.append(cumul[-1] + math.hypot(xb - xa, yb - ya))
	total = cumul[-1]
	res, k = [], 0
	for i in range(n):
		cible = total * i / (n - 1) if n > 1 else 0
		while k < fin_ and cumul[k + 1] < cible:
			k += 1
		f = (cible - cumul[k]) / max(cumul[k + 1] - cumul[k], 1e-12) if k < fin_ else 0
		res.append((ts[k] + f * (ts[min(k + 1, fin_)] - ts[k]), pt(ts[k] + f * (ts[min(k + 1, fin_)] - ts[k]))))
	return res


def u_tete(s):
	"""Tour de tete s (0 = arriere, 0,5 = face) -> u dans la zone : l'avant (+/- 108 deg) prend 80 % de la largeur."""
	if 0.2 <= s <= 0.8:
		return 0.1 + (s - 0.2) * (0.8 / 0.6)
	return 0.9 + (s - 0.8) * 0.5 if s > 0.8 else s * 0.5


def v_tete(w):
	"""Profil w (0 = dessous, 1 = dessus) -> v vers le bas dans la zone : les cotes prennent 84 %."""
	if w < 0.2:
		return 1 - w / 0.2 * 0.08
	if w <= 0.85:
		return 0.92 - (w - 0.2) / 0.65 * 0.84
	return 0.08 - (w - 0.85) / 0.15 * 0.08


def tete():
	info = BLOCS["Head"]
	c = vers_blender(*info["centre"])
	demi_h = info["hauteur"] / 2
	ph, pv = info["exposant_horizontal"], info["exposant_vertical"]
	n_tour, n_profil = 64, 31
	tour = courbe_super(ph, n_tour + 1, math.pi / 2, math.pi / 2 + 2 * math.pi)[:-1]
	profil = courbe_super(pv, n_profil, -math.pi / 2, math.pi / 2)  # (r, z) de bas en haut

	def demi_largeur(zf):
		return (info["largeur_bas"] + (info["largeur_haut"] - info["largeur_bas"]) * (zf + 1) / 2) / 2

	me = bpy.data.meshes.new("Head")
	bm = bmesh.new()
	uvl = bm.loops.layers.uv.new("UVMap")
	anneaux = []
	for j, (_, (rf, zf)) in enumerate(profil):
		if j in (0, n_profil - 1):
			anneaux.append([bm.verts.new((0, 0, zf * demi_h))])
			continue
		a = demi_largeur(zf)
		b = info["profondeur"] / 2
		anneaux.append([bm.verts.new((a * rf * x, b * rf * y, zf * demi_h)) for _, (x, y) in tour])
	zx0, zy0, zx1, zy1 = ZONE_TETE

	def uv(i, j):
		s = i / n_tour
		w = j / (n_profil - 1)
		return px_vers_uv(zx0 + u_tete(s) * (zx1 - zx0), zy0 + v_tete(w) * (zy1 - zy0))

	for j in range(n_profil - 1):
		a, b = anneaux[j], anneaux[j + 1]
		for i in range(n_tour):
			i2 = (i + 1) % n_tour
			if len(a) == 1:
				f = bm.faces.new((a[0], b[i2], b[i]))
				uvs = [uv(i + 0.5, j), uv(i + 1, j + 1), uv(i, j + 1)]
			elif len(b) == 1:
				f = bm.faces.new((a[i], a[i2], b[0]))
				uvs = [uv(i, j), uv(i + 1, j), uv(i + 0.5, j + 1)]
			else:
				f = bm.faces.new((a[i], a[i2], b[i2], b[i]))
				uvs = [uv(i, j), uv(i + 1, j), uv(i + 1, j + 1), uv(i, j + 1)]
			for loop, t in zip(f.loops, uvs):
				loop[uvl].uv = t
	bm.normal_update()
	# normales vers l'exterieur
	if sum((f.calc_center_median().dot(f.normal)) for f in bm.faces) < 0:
		bmesh.ops.reverse_faces(bm, faces=bm.faces[:], flip_multires=False)
	bm.transform(Matrix.Translation(c))
	bm.to_mesh(me)
	bm.free()
	for p in me.polygons:
		p.use_smooth = True
	return objet_maillage("Head", me)


def repere_face(o):
	"""Grille de la face : point (x, z) de l'avant de la tete (studs, relatif au centre) -> pixel de la texture."""
	info = BLOCS["Head"]
	c = vers_blender(*info["centre"])
	me = o.data
	bvh = BVHTree.FromPolygons([v.co for v in me.vertices], [p.vertices for p in me.polygons])
	uv = me.uv_layers["UVMap"].data
	pas = 0.05
	grille = []
	for kz in range(-12, 13):
		ligne = []
		for kx in range(-13, 14):
			x, z = kx * pas, kz * pas
			loc, _, idx, _ = bvh.ray_cast(Vector((c.x + x, c.y - 3, c.z + z)), Vector((0, 1, 0)))
			if loc is None:
				ligne.append(None)
				continue
			poly = me.polygons[idx]
			pts = [me.vertices[v].co for v in poly.vertices]
			uvs = [uv[li].uv for li in poly.loop_indices]
			# coordonnees barycentriques sur le triangle (0, k, k+1) qui contient le point
			res = None
			for k in range(1, len(pts) - 1):
				a, b, cc = pts[0], pts[k], pts[k + 1]
				v0, v1, v2 = b - a, cc - a, loc - a
				d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
				den = d00 * d11 - d01 * d01
				bb = (d11 * d20 - d01 * d21) / den
				gg = (d00 * d21 - d01 * d20) / den
				if bb >= -1e-4 and gg >= -1e-4 and bb + gg <= 1 + 1e-4:
					u_ = uvs[0] * (1 - bb - gg) + uvs[k] * bb + uvs[k + 1] * gg
					res = [round(u_.x * TAILLE_TEX, 2), round((1 - u_.y) * TAILLE_TEX, 2), round(loc.y - c.y, 4)]
					break
			ligne.append(res)
		grille.append(ligne)
	return {"pas": pas, "x": [kx * pas for kx in range(-13, 14)], "z": [kz * pas for kz in range(-12, 13)], "pixels": grille, "note": "pixels[iz][ix] = [px, py, profondeur y] du point (x, z) de la face vue de devant ; x vers la GAUCHE du perso (+X Blender), z vers le haut, relatifs au centre de la tete"}


# ---------------------------------------------------------------- armature et parentage


def armature():
	"""Un os par Motor6D (+ HumanoidRootPart), tous verticaux, tete de l'os a l'articulation (comme la v1 : axes_r15.json)."""
	fin = {"LowerTorso": ART["Waist"][2], "UpperTorso": ART["Neck"][2], "Head": ART["Neck"][2] + 1.3}
	ad = bpy.data.armatures.new("Rig_R15")
	ob = bpy.data.objects.new("Rig_R15", ad)
	bpy.context.scene.collection.objects.link(ob)
	bpy.context.view_layer.objects.active = ob
	bpy.ops.object.mode_set(mode="EDIT")
	eb = ad.edit_bones
	b = eb.new("HumanoidRootPart")
	b.head, b.tail = (0, 0, H), (0, 0, H + 1)
	ordre = ["LowerTorso", "UpperTorso", "Head"] + [c + n for c in ("Left", "Right") for n in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot")]
	suivant = {"UpperArm": "Elbow", "LowerArm": "Wrist", "UpperLeg": "Knee", "LowerLeg": "Ankle"}
	for nom in ordre:
		tete_os = Vector(ART[MOTOR_DE[nom]])
		if nom in fin:
			zq = fin[nom]
		else:
			cote = "Left" if nom.startswith("Left") else "Right"
			seg = nom[len(cote) :]
			zq = ART[cote + suivant[seg]][2] if seg in suivant else (tete_os.z - 0.29 if seg == "Hand" else 0.0)
		b = eb.new(nom)
		b.head, b.tail = tete_os, Vector((tete_os.x, tete_os.y, zq))
		b.roll = 0
		b.parent = eb[PARENT_DE[nom]]
	bpy.ops.object.mode_set(mode="OBJECT")
	for nom, m in MOTOR_DE.items():
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
	m_os = rig.matrix_world @ pb.bone.matrix_local @ Matrix.Translation((0, pb.bone.length, 0))
	obj.matrix_parent_inverse = m_os.inverted()
	obj.matrix_basis = mw


def origine(o, p):
	"""Origine de l'objet en p (monde), sans bouger la geometrie."""
	o.data.transform(Matrix.Translation(-(Vector(p) - o.location)))
	o.location = Vector(p)


# ---------------------------------------------------------------- materiau, scene


def materiau():
	m = bpy.data.materials.new("Mat_Mannequin")
	m.use_nodes = True
	nt = m.node_tree
	bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
	bsdf.inputs["Base Color"].default_value = (*PEAU, 1)
	bsdf.inputs["Roughness"].default_value = 0.8
	tex = nt.nodes.new("ShaderNodeTexImage")
	tex.name = tex.label = "Texture"
	tex.location = (-400, 200)
	chemin = DOSSIER / TEXTURE
	if chemin.exists():
		img = bpy.data.images.load(str(chemin))
		img.filepath = "//" + TEXTURE
		tex.image = img
		nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
	m.diffuse_color = (*PEAU, 1)
	return m


def scene_studio():
	sc = bpy.context.scene
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
		sc.render.engine = "BLENDER_EEVEE"
	except TypeError:
		pass
	sc.view_settings.view_transform = "Standard"
	soleil = bpy.data.lights.new("Soleil", "SUN")
	soleil.energy = 2.5
	so = bpy.data.objects.new("Soleil", soleil)
	so.rotation_euler = (math.radians(50), 0, math.radians(30))
	sc.collection.objects.link(so)


def camera_studio(position, cible, decalage=(-14.0, 300.0, 0.0)):
	"""Place Camera_Studio comme screen_capture de Studio (coordonnees monde Studio, HRP du clone en decalage + (0, hauteurHRP, 0))."""
	dx, dy, dz = decalage
	p = Vector((-(position[0] - dx), position[2] - dz, position[1] - dy))
	c = Vector((-(cible[0] - dx), cible[2] - dz, cible[1] - dy))
	co = bpy.data.objects["Camera_Studio"]
	co.location = p
	co.rotation_euler = (c - p).to_track_quat("-Z", "Y").to_euler()


# ---------------------------------------------------------------- construction


def construire():
	if bpy.context.object and bpy.context.object.mode != "OBJECT":
		bpy.ops.object.mode_set(mode="OBJECT")
	for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.images, bpy.data.cameras, bpy.data.lights, bpy.data.worlds, bpy.data.actions):
		for d in list(coll):
			coll.remove(d)
	sc = bpy.context.scene
	sc.unit_settings.system = "METRIC"
	sc.unit_settings.scale_length = 1.0
	mat = materiau()

	densite = 80.0
	while (places := ranger(densite)) is None:
		densite -= 1
	infos = {"taille": TAILLE_TEX, "densite_corps_px_par_stud": densite, "pieces": {}}

	rig = armature()
	for nom in NOMS:
		o = bloc_arrondi(nom)
		infos["pieces"][nom] = {"faces": uv_bloc(o, nom, places[nom]["croix"], densite)}
		if "jointure" in places[nom]:
			j, dims = jointure(nom)
			infos["pieces"][nom]["jointure"] = uv_jointure(j, dims, places[nom]["jointure"], densite)
			with bpy.context.temp_override(active_object=o, object=o, selected_objects=[o, j], selected_editable_objects=[o, j]):
				bpy.ops.object.join()
		o.data.materials.append(mat)
		origine(o, ART[MOTOR_DE[nom]])
		parenter(o, rig, nom)

	t = tete()
	t.data.materials.append(mat)
	infos["tete"] = {"zone": list(ZONE_TETE), "face": repere_face(t), "note": "u : tour de tete (0 = arriere, milieu = face, l'avant +/- 108 deg occupe 80 % de la zone) ; v : profil de bas en haut (les cotes occupent 84 %)"}
	origine(t, ART["Neck"])
	parenter(t, rig, "Head")

	# HumanoidRootPart : boite invisible 2 x 1 x 2 (Blender x, y, z)
	me = bpy.data.meshes.new("HumanoidRootPart")
	bm = bmesh.new()
	bmesh.ops.create_cube(bm, size=1.0)
	bm.transform(Matrix.Diagonal((2, 1, 2, 1)))
	bm.to_mesh(me)
	bm.free()
	o = objet_maillage("HumanoidRootPart", me)
	o.location = (0, 0, H)
	o.display_type = "WIRE"
	o.hide_render = True
	parenter(o, rig, "HumanoidRootPart")

	scene_studio()
	(DOSSIER / "uv_mannequin.json").write_text(json.dumps(infos, ensure_ascii=False, indent="\t"), encoding="utf-8")
	bpy.ops.wm.save_as_mainfile(filepath=str(DOSSIER / "mannequin.blend"), relative_remap=True)
	tri = sum(sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in bpy.data.objects if ob.type == "MESH" and ob.name != "HumanoidRootPart")
	print("mannequin.blend enregistre ; densite corps %.0f px/stud ; %d triangles" % (densite, tri))


def charger_texture():
	m = bpy.data.materials["Mat_Mannequin"]
	nt = m.node_tree
	tex = nt.nodes["Texture"]
	img = bpy.data.images.get(TEXTURE)
	if img is None:
		img = bpy.data.images.load(str(DOSSIER / TEXTURE))
		img.filepath = "//" + TEXTURE
	else:
		img.reload()
	tex.image = img
	bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
	nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
	bpy.ops.wm.save_mainfile()


def poser(rotations=None):
	"""rotations = {os: (x, y, z) en degres, rotation_euler XYZ} ; None remet la pose de repos."""
	rig = bpy.data.objects["Rig_R15"]
	for pb in rig.pose.bones:
		pb.rotation_mode = "XYZ"
		pb.rotation_euler = (0, 0, 0)
		pb.location = (0, 0, 0)
	for nom, (x, y, z) in (rotations or {}).items():
		rig.pose.bones[nom].rotation_euler = (math.radians(x), math.radians(y), math.radians(z))
	bpy.context.view_layer.update()
