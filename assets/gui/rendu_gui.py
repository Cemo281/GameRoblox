"""Images d'interface d'un personnage, rendues depuis son modele Blender (MCP Blender).

	exec(open(r"C:/Users/alice/Documents/GameRoblox/assets/gui/rendu_gui.py", encoding="utf-8").read())
	rendre("nami")

Source : assets/persos/<Id>/<Id>_apercu.blend ou <Id>.blend (skill perso-roblox, poses de anims/<Id>_Idle.json)
ou assets/blender/<Id>/<Id>.blend (skill perso-r6, pose lue dans l'action <Id>_Idle).
Le .blend est copie dans un dossier temporaire et c'est la copie qui est ouverte (l'original n'est jamais touche).
Sortie dans assets/gui/<Id>/ : portrait.png, pied.png, silhouette.png, idle_sheet.png, infos.json.

Studio commun a tous les persos (tout est defini par rapport au perso, qui regarde vers -Y) :
fond transparent, EEVEE, vue "Standard", 3 soleils (principale chaude en haut a gauche, contre-jour blanc,
remplissage leger), contour Freestyle sombre (silhouette + contour exterieur).
"""

import json
import math
import os
import shutil
import struct
import tempfile
import time
import zlib
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

DEPOT = Path(r"C:\Users\alice\Documents\GameRoblox")
SORTIE = DEPOT / "assets" / "gui"

# ---------------------------------------------------------------- reglages du studio (identiques pour tous)

# azimut en degres : 0 = face au perso, positif = vers sa droite (cote -X)
AZIMUT_CAMERA = 30
LUMIERES = [  # nom, azimut, elevation, couleur, force, angle (flou des ombres), ombre
	("Studio_Principale", 35, 50, (1.0, 0.86, 0.70), 2.4, 25, True),
	# derriere, cote gauche de l'image : sur des persos en blocs, seul ce cote du contour a des faces visibles a eclairer
	("Studio_ContreJour", 150, 25, (1.0, 1.0, 1.0), 2.2, 5, False),
	("Studio_Remplissage", -45, 5, (0.85, 0.90, 1.0), 0.5, 40, False),
]
AMBIANCE = ((0.75, 0.78, 0.85), 0.3)  # couleur, force du monde (invisible : film transparent)
CONTOUR = ((0.06, 0.04, 0.08), 2.0)  # couleur, epaisseur en pixels pour une image de 512
ECHANTILLONS = 64

# portrait cadre sur la tete du rig (taille fixe en studs), pas sur les cheveux ou le chapeau : meme zoom pour tous
PORTRAIT = {"taille": 512, "elevation": 3, "tete": 1.25, "recul": 7.0, "hauteur_image": 3.8, "centre_tete": 1 / 3}
PIED = {"taille": 1024, "elevation": -8, "focale": 35, "marge": 0.06}
GRILLE = {"cote": 4, "taille": 256}

# pose du portrait et du plein pied : image de l'Idle, ou nom d'un fichier de pose fixe de anims/ (perso-roblox,
# format des apercu_*.json) ; sinon l'image de l'Idle la plus eloignee de l'image 0
POSES_PORTRAIT = {
	"nami": 40,  # main gauche levee, orbe pres du visage, tete tournee vers elle
	"zoro": "zoro_PoseGUI.json",  # main droite sur les poignees, bras gauche le long du corps (bras croises de l'Idle = visage cache)
}

# ---------------------------------------------------------------- poses


OS_DE = {
	"Root": "LowerTorso", "Waist": "UpperTorso", "Neck": "Head",
	"RightShoulder": "RightUpperArm", "RightElbow": "RightLowerArm", "RightWrist": "RightHand",
	"LeftShoulder": "LeftUpperArm", "LeftElbow": "LeftLowerArm", "LeftWrist": "LeftHand",
	"RightHip": "RightUpperLeg", "RightKnee": "RightLowerLeg", "RightAnkle": "RightFoot",
	"LeftHip": "LeftUpperLeg", "LeftKnee": "LeftLowerLeg", "LeftAnkle": "LeftFoot",
}
VERS_LE_HAUT = {"LowerTorso", "UpperTorso", "Head"}


class AnimAction:
	"""Perso perso-r6 : action Blender <Id>_Idle sur l'armature."""

	def __init__(self, id):
		self.scene = bpy.context.scene
		self.rig = next((o for o in self.scene.objects if o.type == "ARMATURE" and o.animation_data and o.animation_data.action), None)
		if self.rig is None:
			raise RuntimeError(f"{id} : aucune armature avec une action (lecture de {id}_Idle_roblox.json non prise en charge)")
		action = self.rig.animation_data.action
		self.debut, fin = action.frame_range
		self.fps = self.scene.render.fps / self.scene.render.fps_base
		self.images = int(round(fin - self.debut))
		self.duree = self.images / self.fps
		self.nom = action.name

	def poser(self, image):
		f = self.debut + image
		self.scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))


class AnimJson:
	"""Perso perso-roblox : cles de anims/<Id>_Idle.json appliquees a Rig_R15 (conversion de apercu_pose.py)."""

	def __init__(self, id):
		self.dossier = DEPOT / "assets" / "persos" / id / "anims"
		donnees = json.loads((self.dossier / f"{id}_Idle.json").read_text(encoding="utf-8"))
		self.rig = bpy.data.objects["Rig_R15"]
		self.fps = donnees["fps"]
		self.images = donnees["images"]
		self.duree = donnees["duree"]
		self.nom = donnees["nom"]
		self.cles = [(c["image"], c["easing"], {art: p["cframe"] for art, p in c["poses"].items()}) for c in donnees["cles"]]
		# accessoires montres / caches par les marqueurs (comme src/client/Vitrine.luau) : Acc_X et ses pieces Acc_X_*
		self.marqueurs = sorted((m["image"], m["nom"] == "Montrer", m["valeur"]) for m in donnees.get("marqueurs", []) if m["nom"] in ("Montrer", "Cacher"))
		self.accessoires = {
			nom: [o for o in bpy.context.scene.objects if o.type == "MESH" and (o.name == nom or o.name.startswith(nom + "_"))]
			for nom in {v for _, _, v in self.marqueurs}
		}
		self.visible_defaut = {nom: bool(bpy.data.objects[nom].get("VisibleParDefaut", not bpy.data.objects[nom].hide_render)) for nom in self.accessoires}

	def montrer_accessoires(self, image):
		visible = dict(self.visible_defaut)
		if not isinstance(image, str):
			for im, montrer, nom in self.marqueurs:
				if im <= image:
					visible[nom] = montrer
		for nom, objets in self.accessoires.items():
			for o in objets:
				o.hide_render = not visible[nom]

	@staticmethod
	def lisser(t, easing):
		if easing == "Linear":
			return t
		if easing == "Constant":
			return 0.0
		return t * t * (3 - 2 * t)  # Cubic InOut (comme anims_zoro.py)

	def poser(self, image):
		if isinstance(image, str):  # pose fixe (fichier de anims/)
			pa = pb = json.loads((self.dossier / image).read_text(encoding="utf-8"))
			t = 0.0
		else:
			image = min(max(image, self.cles[0][0]), self.cles[-1][0])
			for (fa, ea, pa), (fb, _, pb) in zip(self.cles, self.cles[1:]):
				if fa <= image <= fb:
					t = self.lisser(0.0 if fb == fa else (image - fa) / (fb - fa), ea)
					break
		for art, os_nom in OS_DE.items():
			a, b = pa[art], pb[art]
			qa = Matrix((a[3:6], a[6:9], a[9:12])).to_quaternion()
			qb = Matrix((b[3:6], b[6:9], b[9:12])).to_quaternion()
			T = qa.slerp(qb, t).to_matrix()
			p = Vector(a[:3]).lerp(Vector(b[:3]), t)
			B = Matrix(((-1, 0, 0), (0, 1, 0), (0, 0, -1))) if os_nom in VERS_LE_HAUT else Matrix(((-1, 0, 0), (0, -1, 0), (0, 0, 1)))
			pb_ = self.rig.pose.bones[os_nom]
			pb_.rotation_mode = "QUATERNION"
			pb_.rotation_quaternion = (B @ T @ B).to_quaternion()
			pb_.location = B @ p
		self.montrer_accessoires(image)
		bpy.context.view_layer.update()


def ecart_pose(anim, image, reference):
	anim.poser(image)
	return sum(math.degrees(pb.matrix_basis.to_quaternion().rotation_difference(reference[pb.name]).angle) for pb in anim.rig.pose.bones)


def image_expressive(id, anim):
	if id in POSES_PORTRAIT:
		return POSES_PORTRAIT[id]
	anim.poser(0)
	reference = {pb.name: pb.matrix_basis.to_quaternion() for pb in anim.rig.pose.bones}
	return max(range(anim.images), key=lambda i: ecart_pose(anim, i, reference))


def raccord_boucle(anim):
	"""Ecart maximal (matrice des os) entre le debut et la fin de la boucle : 0 = enchainement sans saut."""
	anim.poser(0)
	a = [pb.matrix.copy() for pb in anim.rig.pose.bones]
	anim.poser(anim.images)
	b = [pb.matrix.copy() for pb in anim.rig.pose.bones]
	return max(abs(x - y) for ma, mb in zip(a, b) for ra, rb in zip(ma, mb) for x, y in zip(ra, rb))


# ---------------------------------------------------------------- geometrie et cadrage


def direction(azimut, elevation):
	az, el = math.radians(azimut), math.radians(elevation)
	return Vector((-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))


def objets_rendus(scene):
	return [o for o in scene.objects if o.type == "MESH" and not o.hide_render]


def points(scene, os_tete=None):
	"""Sommets (monde) des meshes rendus ; avec os_tete, seulement ceux des objets attaches a cet os."""
	dg = bpy.context.evaluated_depsgraph_get()
	morceaux = []
	for o in objets_rendus(scene):
		if os_tete and o.parent_bone != os_tete:
			continue
		ev = o.evaluated_get(dg)
		me = ev.to_mesh()
		co = np.empty(len(me.vertices) * 3)
		me.vertices.foreach_get("co", co)
		ev.to_mesh_clear()
		co = co.reshape(-1, 3)
		m = np.array(o.matrix_world)
		morceaux.append(co @ m[:3, :3].T + m[:3, 3])
	return np.concatenate(morceaux)


def placer_camera(cam, cible, dir_vers_camera, recul):
	f = -dir_vers_camera.normalized()
	droite = f.cross(Vector((0, 0, 1))).normalized()
	haut = droite.cross(f)
	pos = cible + dir_vers_camera.normalized() * recul
	cam.matrix_world = Matrix((
		(droite.x, haut.x, -f.x, pos.x),
		(droite.y, haut.y, -f.y, pos.y),
		(droite.z, haut.z, -f.z, pos.z),
		(0, 0, 0, 1),
	))
	return pos, droite, haut, f


def tangentes(pts, pos, droite, haut, f):
	"""Coordonnees (x / profondeur, y / profondeur) dans le repere de la camera."""
	d = pts - np.array(pos)
	prof = d @ np.array(f)
	return d @ np.array(droite) / prof, d @ np.array(haut) / prof


def cadrer_portrait(cam, rig, os_tete):
	"""Centre de la tete = sur l'os de la tete, a mi-hauteur d'une tete Roblox ; image de hauteur_image tetes, vue de recul tetes."""
	r = PORTRAIT
	os_ = rig.pose.bones[os_tete]
	cou = rig.matrix_world @ os_.head
	centre = cou + (rig.matrix_world @ os_.tail - cou).normalized() * (r["tete"] / 2)
	placer_camera(cam, centre, direction(AZIMUT_CAMERA, r["elevation"]), r["recul"] * r["tete"])
	c = cam.data
	c.type, c.sensor_fit, c.sensor_width = "PERSP", "AUTO", 36
	c.lens = 36 * r["recul"] / r["hauteur_image"]  # hauteur_image * tete studs a la distance de la tete
	c.shift_x = 0.0
	c.shift_y = 0.5 - (1 - r["centre_tete"])  # centre de la tete au tiers haut


def cadrer_pied(cam, nuage):
	"""Plein pied : tout le nuage tient dans l'image avec la marge, pieds sur la marge du bas."""
	r = PIED
	c = cam.data
	c.type, c.sensor_fit, c.sensor_width, c.lens = "PERSP", "AUTO", 36, r["focale"]
	echelle = r["focale"] / 36
	bas, hautb = nuage.min(axis=0), nuage.max(axis=0)
	centre = Vector(((bas + hautb) / 2).tolist())
	dirc = direction(AZIMUT_CAMERA, r["elevation"])
	recul = float(np.linalg.norm(hautb - bas)) * 2
	for _ in range(8):
		pos, dr, ht, f = placer_camera(cam, centre, dirc, recul)
		a, b = tangentes(nuage, pos, dr, ht, f)
		etendue = max(a.max() - a.min(), b.max() - b.min()) * echelle
		recul *= etendue / (1 - 2 * r["marge"])
	pos, dr, ht, f = placer_camera(cam, centre, dirc, recul)
	a, b = tangentes(nuage, pos, dr, ht, f)
	c.shift_x = echelle * (a.max() + a.min()) / 2
	c.shift_y = 0.5 + echelle * b.min() - r["marge"]


# ---------------------------------------------------------------- studio


def regler_studio(scene):
	for o in scene.objects:
		if o.type in {"LIGHT", "CAMERA"}:
			o.hide_render = True
	try:
		scene.render.engine = "BLENDER_EEVEE"
	except TypeError:
		scene.render.engine = "BLENDER_EEVEE_NEXT"
	scene.eevee.taa_render_samples = ECHANTILLONS
	r = scene.render
	r.film_transparent = True
	r.resolution_percentage = 100
	r.image_settings.file_format = "PNG"
	r.image_settings.color_mode = "RGBA"
	r.image_settings.color_depth = "8"
	# pas de metadonnees dans les PNG (date, chemin local du .blend) : images reproductibles a l'octet pres
	for nom in dir(r):
		if nom.startswith("use_stamp"):
			setattr(r, nom, False)
	vs = scene.view_settings
	vs.view_transform = "Standard"
	vs.look = "None"
	vs.exposure = 0.0
	vs.gamma = 1.0

	monde = bpy.data.worlds.new("Studio_Monde")
	monde.use_nodes = True
	fond = next(n for n in monde.node_tree.nodes if n.type == "BACKGROUND")
	fond.inputs[0].default_value = (*AMBIANCE[0], 1.0)
	fond.inputs[1].default_value = AMBIANCE[1]
	scene.world = monde

	for nom, az, el, couleur, force, angle, ombre in LUMIERES:
		l = bpy.data.lights.new(nom, "SUN")
		l.color, l.energy, l.angle, l.use_shadow = couleur, force, math.radians(angle), ombre
		o = bpy.data.objects.new(nom, l)
		scene.collection.objects.link(o)
		o.rotation_mode = "QUATERNION"
		o.rotation_quaternion = direction(az, el).to_track_quat("Z", "Y")  # le soleil eclaire selon son -Z

	r.use_freestyle = True
	r.line_thickness_mode = "ABSOLUTE"
	vl = scene.view_layers[0]
	vl.use_freestyle = True
	fs = vl.freestyle_settings
	for ls in list(fs.linesets):
		fs.linesets.remove(ls)
	ls = fs.linesets.new("Studio_Contour")
	ls.select_by_visibility = True
	ls.visibility = "VISIBLE"
	ls.select_by_edge_types = True
	for type_arete in ("silhouette", "border", "crease", "ridge_valley", "suggestive_contour", "material_boundary", "contour", "external_contour", "edge_mark"):
		setattr(ls, "select_" + type_arete, type_arete in ("silhouette", "external_contour"))
	ls.linestyle.color = CONTOUR[0]
	ls.linestyle.alpha = 1.0

	cam = bpy.data.objects.new("Studio_Camera", bpy.data.cameras.new("Studio_Camera"))
	scene.collection.objects.link(cam)
	scene.camera = cam
	return cam


def rendu(scene, taille, chemin):
	scene.render.resolution_x = scene.render.resolution_y = taille
	scene.view_layers[0].freestyle_settings.linesets["Studio_Contour"].linestyle.thickness = CONTOUR[1] * taille / 512
	scene.render.filepath = str(chemin)
	bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------- PNG (lecture par Blender, ecriture maison : pas de conversion de couleurs)


def lire_png(chemin):
	img = bpy.data.images.load(str(chemin), check_existing=False)
	img.colorspace_settings.name = "Non-Color"
	l, h = img.size
	px = np.empty(l * h * 4, dtype=np.float32)
	img.pixels.foreach_get(px)
	bpy.data.images.remove(img)
	return np.flipud(px.reshape(h, l, 4))  # Blender stocke de bas en haut


def ecrire_png(chemin, rgba):
	"""rgba : tableau (h, l, 4) en flottants 0..1, de haut en bas."""
	octets = np.clip(np.round(rgba * 255), 0, 255).astype(np.uint8)
	h, l = octets.shape[:2]
	brut = b"".join(b"\x00" + ligne.tobytes() for ligne in octets)

	def bloc(type_, donnees):
		return struct.pack(">I", len(donnees)) + type_ + donnees + struct.pack(">I", zlib.crc32(type_ + donnees) & 0xFFFFFFFF)

	Path(chemin).write_bytes(b"\x89PNG\r\n\x1a\n" + bloc(b"IHDR", struct.pack(">IIBBBBB", l, h, 8, 6, 0, 0, 0)) + bloc(b"IDAT", zlib.compress(brut, 9)) + bloc(b"IEND", b""))


# ---------------------------------------------------------------- point d'entree


def source(id):
	for nom in (f"{id}_apercu.blend", f"{id}.blend"):
		p = DEPOT / "assets" / "persos" / id / nom
		if p.exists():
			return p, AnimJson
	p = DEPOT / "assets" / "blender" / id / f"{id}.blend"
	if p.exists():
		return p, AnimAction
	raise FileNotFoundError(f"pas de fichier d'apercu pour {id}")


def rendre(id):
	debut = time.time()
	ancien = SORTIE / id / "infos.json"
	if ancien.exists() and json.loads(ancien.read_text(encoding="utf-8")).get("source", "").startswith("Studio"):
		raise RuntimeError(f"{id} : images rendues depuis Studio (le .blend n'est pas le modele du jeu) : utiliser rendu_studio.py")
	original, Anim = source(id)
	copie = Path(tempfile.mkdtemp(prefix="rendu_gui_")) / f"{id}_copie.blend"
	shutil.copy2(original, copie)
	bpy.ops.wm.open_mainfile(filepath=str(copie))
	# textures en chemin relatif (//tex.png) : rattachees au dossier de l'original, pas a celui de la copie
	for img in bpy.data.images:
		if img.filepath.startswith("//") and not img.packed_file:
			img.filepath = str(original.parent / img.filepath[2:])
			img.reload()
	scene = bpy.context.scene
	anim = Anim(id)
	dossier = SORTIE / id
	dossier.mkdir(parents=True, exist_ok=True)
	cam = regler_studio(scene)

	pose = image_expressive(id, anim)
	anim.poser(pose)
	cadrer_portrait(cam, anim.rig, "Head")
	rendu(scene, PORTRAIT["taille"], dossier / "portrait.png")

	# silhouette = alpha du portrait (meme cadrage, contour compris), rempli de noir, bord durci
	px = lire_png(dossier / "portrait.png")
	coupe_haut = int((px[0, :, 3] > 0.03).sum())
	if coupe_haut:
		print(f"ATTENTION {id} : {coupe_haut} pixels opaques sur le bord haut du portrait (chapeau ou cheveux coupes)")
	alpha = np.clip((px[:, :, 3] - 0.5) * 3 + 0.5, 0, 1)
	sil = np.zeros_like(px)
	sil[:, :, 3] = alpha
	ecrire_png(dossier / "silhouette.png", sil)

	cadrer_pied(cam, points(scene))
	rendu(scene, PIED["taille"], dossier / "pied.png")

	# grille : 16 images regulieres sur la boucle, l'image 16 (= la 0) n'est pas rendue -> enchainement sans saut
	n = GRILLE["cote"] ** 2
	temps = [k * anim.images / n for k in range(n)]
	nuage = []
	for t in temps:
		anim.poser(t)
		nuage.append(points(scene))
	cadrer_pied(cam, np.concatenate(nuage))
	taille = GRILLE["taille"]
	feuille = np.zeros((taille * GRILLE["cote"], taille * GRILLE["cote"], 4), dtype=np.float32)
	tmp = copie.parent / "case.png"
	for k, t in enumerate(temps):
		anim.poser(t)
		rendu(scene, taille, tmp)
		ligne, col = divmod(k, GRILLE["cote"])
		feuille[ligne * taille : (ligne + 1) * taille, col * taille : (col + 1) * taille] = lire_png(tmp)
	ecrire_png(dossier / "idle_sheet.png", feuille)

	infos = {
		"id": id,
		"source": str(original.relative_to(DEPOT)).replace("\\", "/"),
		"animation": anim.nom,
		"images": {
			"portrait.png": {"taille": [512, 512], "pose": pose, "temps": None if isinstance(pose, str) else round(pose / anim.fps, 4)},
			"pied.png": {"taille": [1024, 1024], "pose": pose, "temps": None if isinstance(pose, str) else round(pose / anim.fps, 4)},
			"silhouette.png": {"taille": [512, 512], "cadrage": "portrait"},
			"idle_sheet.png": {
				"taille": [1024, 1024],
				"grille": [GRILLE["cote"], GRILLE["cote"]],
				"taille_case": [taille, taille],
				"ordre": "ligne par ligne, de gauche a droite puis de haut en bas (case k : ligne k // 4, colonne k % 4)",
				"images_animation": [round(t, 3) for t in temps],
			},
		},
		"boucle": {
			"duree": round(anim.duree, 4),
			"images": anim.images,
			"fps_source": anim.fps,
			"raccord_fin_debut": round(raccord_boucle(anim), 6),
		},
		"fps_conseille": round(n / anim.duree, 4),
	}
	ancien = dossier / "infos.json"
	if ancien.exists():  # IDs Roblox notes apres l'envoi : a garder (a renvoyer si l'image a change)
		infos["ids_roblox"] = json.loads(ancien.read_text(encoding="utf-8")).get("ids_roblox", {})
	(dossier / "infos.json").write_text(json.dumps(infos, indent="\t", ensure_ascii=False), encoding="utf-8")
	duree = round(time.time() - debut, 1)
	print(f"{id} : images dans {dossier}, pose {pose}, boucle {anim.duree} s, {duree} s de calcul")
	return infos
