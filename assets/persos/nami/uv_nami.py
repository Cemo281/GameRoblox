"""Atlas de nami (tex_corps_nami.png, 1024 x 1024) : une seule image pour toutes les pieces du corps.

A lancer DANS Blender (MCP Blender), apres construire_nami.py (pose de repos) :
	exec(open(r"<depot>/assets/persos/nami/uv_nami.py", encoding="utf-8").read())
	atlas()   # UV de tous les objets du corps + uv_nami.json (lu par peindre_nami.py)
	ombrage() # ombrage_nami.json (occlusion, lumiere) ; puis : uv run --with pillow assets/persos/nami/peindre_nami.py
	materiau_nami()  # Mat_Nami (tex_corps_nami.png) sur le corps

Une MeshPart Roblox n'a qu'une texture : la tete (face + cheveux fusionnes), le torse (peau + haut + cheveux du dos), etc.
partagent donc la meme image.
- Head (bloc arrondi) : projection sur sa boite dans la zone du haut, face avant a 380 px/stud (TETE_ZONE).
- Calotte des cheveux : pastille en degrade.
- Pieces de peau visibles et vetements : projection sur leur boite, une bande Droite | Avant | Gauche | Arriere + Dessus + Dessous.
- Pieces cachees sous le jean : ramenees sur une pastille de jean.
- Meches : une bande par meche (u = tour, v = longueur), pour peindre l'ombrage cel-shading meche par meche.
- Petits objets (bracelets, boussole, bouton, sandales) : pastilles en degrade vertical.
Accessoires separes (Acc_*) : leur propre image tex_acc_nami.png (voir accessoires_uv()).
"""

import json
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

DOSSIER = Path(r"C:\Users\alice\Documents\GameRoblox\assets\persos\nami")
TAILLE = 1024
ZONE = (8, 528, 1016, 1016)  # zone du corps (pixels, y vers le bas) ; la tete garde 8..520 en haut
MARGE = 4
DENS = 48.0  # pixels par stud (corps, vetements)
DENS_CHEVEUX = 46.0

PROJETES = [
	"UpperTorso", "LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm", "LeftHand", "RightHand", "LeftFoot", "RightFoot",
	"UpperTorso_Haut", "LowerTorso_Jean", "LeftUpperLeg_Jean", "RightUpperLeg_Jean", "LeftLowerLeg_Jean", "RightLowerLeg_Jean",
]
CACHES = {"LowerTorso": "jean", "LeftUpperLeg": "jean", "RightUpperLeg": "jean", "LeftLowerLeg": "jean", "RightLowerLeg": "jean", "HumanoidRootPart": "jean"}
PASTILLES = {
	"LowerTorso_Bouton": "or", "LeftLowerArm_Bracelets": "or", "LeftLowerArm_Boussole": "verre",
	"LeftFoot_Sandale": "sandale", "RightFoot_Sandale": "sandale",
	"LowerTorso_Ceinture": "ceinture", "LowerTorso_Clous": "clous",
}
# pastilles placees hors du rangement (sous la derniere etagere) : en ajouter ne deplace pas les UV deja exportes
PASTILLES_FIXES = {"ceinture": [960, 990, 24, 24], "clous": [988, 990, 24, 24]}
TAILLE_PASTILLE = 24
COULEURS_PASTILLES = ["jean", "or", "verre", "sandale", "cheveux"]
MECHES = ["Head_Cheveux", "UpperTorso_Cheveux"]


def vers_uv(px, py):
	return (px / TAILLE, 1 - py / TAILLE)


def classer(n):
	ax = max(range(3), key=lambda i: abs(n[i]))
	return {(0, -1): "Droite", (0, 1): "Gauche", (1, -1): "Avant", (1, 1): "Arriere", (2, 1): "Dessus", (2, -1): "Dessous"}[(ax, 1 if n[ax] > 0 else -1)]


def boite_monde(o):
	ps = [o.matrix_world @ v.co for v in o.data.vertices]
	return [min(p.x for p in ps), max(p.x for p in ps), min(p.y for p in ps), max(p.y for p in ps), min(p.z for p in ps), max(p.z for p in ps)]


def coord_face(face, p, b):
	"""(a, b) en studs dans la case de la face (a vers la droite de l'image, b vers le bas)."""
	x0, x1, y0, y1, z0, z1 = b
	return {
		"Avant": (p.x - x0, z1 - p.z),
		"Arriere": (x1 - p.x, z1 - p.z),
		"Droite": (y1 - p.y, z1 - p.z),
		"Gauche": (p.y - y0, z1 - p.z),
		"Dessus": (p.x - x0, y1 - p.y),
		"Dessous": (p.x - x0, p.y - y0),
	}[face]


def rects_projete(b):
	"""Rectangles (studs) : bande (Droite | Avant | Gauche | Arriere), Dessus, Dessous."""
	w, d, h = b[1] - b[0], b[3] - b[2], b[5] - b[4]
	return {"bande": (2 * w + 2 * d, h), "Dessus": (w, d), "Dessous": (w, d)}


def decalage_bande(face, b):
	w, d = b[1] - b[0], b[3] - b[2]
	return {"Droite": 0.0, "Avant": d, "Gauche": d + w, "Arriere": 2 * d + w}[face]


def meches_de(o):
	"""{id: (largeur, longueur)} en studs des meches et nappes d'un objet (ecrit par construire_nami.py ; id 0 = calotte)."""
	return {int(k): tuple(v) for k, v in json.loads(o["tailles_meches"]).items()}


def uv_calotte(o, uv, polys, rect):
	"""Calotte : u = azimut autour de la tete (0 = avant, couture a l'avant, sous la frange), v = du sommet vers le bas."""
	import math

	x, y, w, h = rect
	for p in polys:
		pts = [o.matrix_world @ o.data.vertices[o.data.loops[li].vertex_index].co for li in p.loop_indices]
		us = [(math.atan2(q.x, -q.y) / (2 * math.pi)) % 1 for q in pts]
		if max(us) - min(us) > 0.5:
			us = [u + 1 if u < 0.5 else u for u in us]
		for li, q, u in zip(p.loop_indices, pts, us):
			v = min(1.0, max(0.0, (5.62 - q.z) / 1.2))
			uv[li].uv = vers_uv(x + 1 + u / 1.5 * (w - 2), y + 1 + v * (h - 2))


TETE_ZONE = {  # tete (bloc arrondi) dans la zone du haut : face avant en haute definition, le reste plus bas
	"Avant": (190, 12, 380.0), "Droite": (8, 12, 150.0), "Gauche": (654, 12, 150.0), "Arriere": (836, 12, 150.0),
	"Dessus": (8, 215, 150.0), "Dessous": (200, 470, 30.0),
}


def ranger(rects):
	"""Etageres dans ZONE. rects = [(cle, l_px, h_px)] -> {cle: (x, y)} ; leve une erreur si ca deborde."""
	x0, y0, x1, y1 = ZONE
	x, y, h_et = x0, y0, 0
	places = {}
	for cle, w, h in sorted(rects, key=lambda r: (-r[2], -r[1])):
		if x + w > x1:
			x, y, h_et = x0, y + h_et + MARGE, 0
		if y + h > y1:
			raise RuntimeError("atlas plein (%s), baisser DENS" % (cle,))
		places[cle] = (x, y)
		x += w + MARGE
		h_et = max(h_et, h)
	return places, y + h_et


def atlas():
	for pb in bpy.data.objects["Rig_R15"].pose.bones:
		pb.rotation_euler = (0, 0, 0)
		pb.location = (0, 0, 0)
	bpy.context.view_layer.update()
	rects = []
	boites = {"Head": boite_monde(bpy.data.objects["Head"])}
	for n in PROJETES:
		b = boite_monde(bpy.data.objects[n])
		boites[n] = b
		for k, (w, h) in rects_projete(b).items():
			rects.append(((n, k), int(w * DENS + 2), int(h * DENS + 2)))
	meches = {}
	for n in MECHES:
		meches[n] = meches_de(bpy.data.objects[n])
		for i, (larg, lg, _) in meches[n].items():
			rects.append(((n, i), int(larg * DENS_CHEVEUX + 2), int(lg * DENS_CHEVEUX + 2)))
	for c in COULEURS_PASTILLES:
		rects.append((("pastille", c), TAILLE_PASTILLE, TAILLE_PASTILLE))
	places, bas = ranger(rects)
	print("atlas : %d rectangles, bas de la zone a y = %d / %d" % (len(rects), bas, ZONE[3]))

	infos = {"taille": TAILLE, "dens": DENS, "dens_cheveux": DENS_CHEVEUX, "projetes": {}, "meches": {}, "pastilles": {}, "objets_pastille": {}}
	for c in COULEURS_PASTILLES:
		x, y = places[("pastille", c)]
		infos["pastilles"][c] = [x, y, TAILLE_PASTILLE, TAILLE_PASTILLE]
	assert bas < PASTILLES_FIXES["ceinture"][1], "les pastilles fixes chevauchent le rangement"
	infos["pastilles"].update(PASTILLES_FIXES)

	# projection sur la boite : faces = {face: [x, y, densite]} (pixel du coin (a, b) = (0, 0) de la face)
	for n in ["Head"] + PROJETES:
		o = bpy.data.objects[n]
		b = boites[n]
		me = o.data
		uv = me.uv_layers.active or me.uv_layers.new(name="UVMap")
		if n == "Head":
			faces = {f: list(v) for f, v in TETE_ZONE.items()}
		else:
			bx, by = places[(n, "bande")]
			faces = {f: [bx + 1 + decalage_bande(f, b) * DENS, by + 1, DENS] for f in ("Droite", "Avant", "Gauche", "Arriere")}
			for k in ("Dessus", "Dessous"):
				faces[k] = [places[(n, k)][0] + 1, places[(n, k)][1] + 1, DENS]
		for p in me.polygons:
			face = classer(o.matrix_world.to_3x3() @ p.normal)
			ox, oy, dn = faces[face]
			for li in p.loop_indices:
				q = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
				a, bb = coord_face(face, q, b)
				uv.data[li].uv = vers_uv(ox + a * dn, oy + bb * dn)
		infos["projetes"][n] = {"boite": [round(v, 4) for v in b], "faces": faces}

	# pastilles : degrade vertical selon la hauteur de l'objet
	for n, c in list(PASTILLES.items()) + list(CACHES.items()):
		o = bpy.data.objects[n]
		b = boite_monde(o)
		me = o.data
		uv = me.uv_layers.active or me.uv_layers.new(name="UVMap")
		x, y, w, h = infos["pastilles"][c]
		for p in me.polygons:
			for li in p.loop_indices:
				q = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
				t = (b[5] - q.z) / max(b[5] - b[4], 1e-6) if n in PASTILLES else 0.5
				uv.data[li].uv = vers_uv(x + w / 2, y + 3 + t * (h - 6))
		infos["objets_pastille"][n] = c

	# meches : bande par meche ; la calotte (id 0) garde les UV de la tete
	for n in MECHES:
		o = bpy.data.objects[n]
		me = o.data
		uv = me.uv_layers.active.data
		attr = me.attributes["meche"].data
		liste = []
		for i, (larg, lg, genre) in meches[n].items():
			x, y = places[(n, i)]
			w, h = int(larg * DENS_CHEVEUX + 2), int(lg * DENS_CHEVEUX + 2)
			liste.append({"id": i, "rect": [x, y, w, h], "genre": genre})
		par_id = {d["id"]: d["rect"] for d in liste}
		px, py, pw, ph = infos["pastilles"]["cheveux"]
		interieur = me.attributes["interieur"].data if "interieur" in me.attributes else None
		if 0 in par_id:
			uv_calotte(o, uv, [p for p in me.polygons if attr[p.index].value == 0], par_id[0])
		for p in me.polygons:
			i = attr[p.index].value
			if i == 0:
				continue
			if interieur is not None and interieur[p.index].value:  # dessous des nappes : pastille en degrade
				for li in p.loop_indices:
					z = (o.matrix_world @ me.vertices[me.loops[li].vertex_index].co).z
					t = min(1.0, max(0.0, (5.65 - z) / 1.4))
					uv[li].uv = vers_uv(px + pw / 2, py + 3 + t * (ph - 6))
				continue
			x, y, w, h = par_id[i]
			for li in p.loop_indices:
				u, v = uv[li].uv
				uv[li].uv = vers_uv(x + 1 + u * (w - 2), y + 1 + v * (h - 2))
		infos["meches"][n] = liste
	(DOSSIER / "uv_nami.json").write_text(json.dumps(infos, indent="\t"), encoding="utf-8")
	print("uv_nami.json ecrit")



def ombrage(rayons=16, portee=0.6, pas_px=4):
	"""Ombrage pour peindre_nami.py (ombrage_nami.json), pose de repos, apres atlas() :
	- "faces" : pour Head et les cheveux, chaque face : polygone UV (pixels), occlusion ambiante (0 = bouchee, 1 = libre),
	  lumiere cle (demi-lambert 0..1, lumiere surtout du haut, un peu de face et de la gauche du perso), centre (monde).
	- "grilles" : pour les objets projetes, occlusion echantillonnee tous les pas_px pixels sur chaque zone (bande, Dessus, Dessous).
	"""
	import math

	from mathutils.bvhtree import BVHTree

	objets = [o for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith("Acc_") and o.name != "HumanoidRootPart"]
	dg = bpy.context.evaluated_depsgraph_get()

	def bvh_de(liste):
		bm = bmesh.new()
		for o in liste:
			tmp = bmesh.new()
			tmp.from_object(o, dg)
			tmp.transform(o.matrix_world)
			me = bpy.data.meshes.new("tmp")
			tmp.to_mesh(me)
			tmp.free()
			bm.from_mesh(me)
			bpy.data.meshes.remove(me)
		arbre = BVHTree.FromBMesh(bm)
		bm.free()
		return arbre

	tout = bvh_de(objets)
	dirs = []
	for k in range(rayons):
		z = 1 - (k + 0.5) / rayons
		r = math.sqrt(1 - z * z)
		a = k * 2.399963
		dirs.append(Vector((r * math.cos(a), r * math.sin(a), z)))
	cle = Vector((0.1, -0.2, 0.97)).normalized()

	def occlusion(c, n):
		c = c + n * 0.004
		t = n.orthogonal().normalized()
		b = n.cross(t)
		libre = poids = 0.0
		for d in dirs:
			w = t * d.x + b * d.y + n * d.z
			poids += d.z
			if tout.ray_cast(c, w, portee)[0] is None:
				libre += d.z
		return libre / poids

	res = {"faces": {}, "grilles": {}}
	for n in MECHES:
		o = bpy.data.objects[n]
		me = o.data
		uv = me.uv_layers.active.data
		m3 = o.matrix_world.to_3x3()
		faces = []
		for p in me.polygons:
			nn = (m3 @ p.normal).normalized()
			c = o.matrix_world @ p.center
			pts = [[round(uv[li].uv.x * TAILLE, 1), round((1 - uv[li].uv.y) * TAILLE, 1)] for li in p.loop_indices]
			faces.append([pts, round(occlusion(c, nn), 3), round(0.5 + 0.5 * nn.dot(cle), 3), [round(v, 3) for v in c]])
		res["faces"][n] = faces

	infos = json.loads((DOSSIER / "uv_nami.json").read_text(encoding="utf-8"))
	normales = {"Avant": (0, -1, 0), "Arriere": (0, 1, 0), "Droite": (-1, 0, 0), "Gauche": (1, 0, 0), "Dessus": (0, 0, 1), "Dessous": (0, 0, -1)}
	for n, info in infos["projetes"].items():
		o = bpy.data.objects[n]
		propre = bvh_de([o])
		x0, x1, y0, y1, z0, z1 = info["boite"]
		w, d, h = x1 - x0, y1 - y0, z1 - z0
		cases = {"Droite": (d, h), "Avant": (w, h), "Gauche": (d, h), "Arriere": (w, h), "Dessus": (w, d), "Dessous": (w, d)}
		grille = {}
		for face, (fw, fh) in cases.items():
			zx, zy, dn = info["faces"][face]
			N = Vector(normales[face])
			nx, ny = max(1, int(fw * dn / pas_px)), max(1, int(fh * dn / pas_px))
			vals = []
			for j in range(ny):
				for i in range(nx):
					a, b = (i + 0.5) / nx * fw, (j + 0.5) / ny * fh
					# point de la boite correspondant a (a, b) (inverse de coord_face)
					p = {
						"Avant": Vector((x0 + a, y0, z1 - b)),
						"Arriere": Vector((x1 - a, y1, z1 - b)),
						"Droite": Vector((x0, y1 - a, z1 - b)),
						"Gauche": Vector((x1, y0 + a, z1 - b)),
						"Dessus": Vector((x0 + a, y1 - b, z1)),
						"Dessous": Vector((x0 + a, y0 + b, z0)),
					}[face]
					hit = propre.ray_cast(p + N * 0.5, -N, 1.5)
					if hit[0] is None:
						vals.append(1.0)
						continue
					vals.append(round(occlusion(hit[0], hit[1].normalized()), 2))
			grille[face] = {"px": [zx, zy, fw * dn, fh * dn], "n": [nx, ny], "ao": vals}
		res["grilles"][n] = grille
	(DOSSIER / "ombrage_nami.json").write_text(json.dumps(res), encoding="utf-8")
	print("ombrage_nami.json ecrit")


def materiau_nami():
	"""Mat_Nami (tex_corps_nami.png) sur tous les objets du corps (hors accessoires)."""
	img = bpy.data.images.get("tex_corps_nami.png") or bpy.data.images.load(str(DOSSIER / "tex_corps_nami.png"))
	img.filepath = "//tex_corps_nami.png"
	img.reload()
	m = bpy.data.materials.get("Mat_Nami") or bpy.data.materials.new("Mat_Nami")
	m.use_nodes = True
	nt = m.node_tree
	bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
	bsdf.inputs["Roughness"].default_value = 0.8
	tex = nt.nodes.get("Texture") or nt.nodes.new("ShaderNodeTexImage")
	tex.name = "Texture"
	tex.image = img
	nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
	for o in bpy.data.objects:
		if o.type == "MESH" and not o.name.startswith("Acc_"):
			o.data.materials.clear()
			o.data.materials.append(m)


# ---------------------------------------------------------------- accessoires (tex_acc_nami.png, 512 x 512)

TAILLE_ACC = 512
ZONES_ACC = {
	"carte": (8, 8, 320, 232), "dos_carte": (336, 8, 168, 124), "bourse": (8, 248, 240, 240),
	"baton": (256, 248, 40, 240), "bague": (304, 248, 40, 240), "rouleau": (352, 248, 40, 240),
	"ruban": (400, 248, 40, 120), "cordon": (448, 248, 40, 120),
}


def accessoires_uv():
	"""UV des accessoires dans tex_acc_nami.png ; ecrit acc_nami.json (zones et cadrage de la carte) pour peindre_nami.py."""
	import math

	def uv_px(x, y):
		return (x / TAILLE_ACC, 1 - y / TAILLE_ACC)

	def dans(zone, u, v):
		x, y, w, h = ZONES_ACC[zone]
		return uv_px(x + 2 + u * (w - 4), y + 2 + v * (h - 4))

	infos = {"taille": TAILLE_ACC, "zones": ZONES_ACC}
	for nom in ("Acc_Baton", "Acc_Baton_Bagues", "Acc_Bourse", "Acc_Bourse_Cordon", "Acc_Carte", "Acc_Carte_Ruban"):
		o = bpy.data.objects[nom]
		me = o.data
		uv = (me.uv_layers.active or me.uv_layers.new(name="UVMap")).data
		ps = [o.matrix_world @ v.co for v in me.vertices]
		b = [min(p.x for p in ps), max(p.x for p in ps), min(p.y for p in ps), max(p.y for p in ps), min(p.z for p in ps), max(p.z for p in ps)]
		c = Vector(((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2))
		if nom == "Acc_Carte":
			infos["carte"] = [round(v, 4) for v in b]
		for p in me.polygons:
			n = o.matrix_world.to_3x3() @ p.normal
			pc = o.matrix_world @ p.center
			for li in p.loop_indices:
				q = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
				if nom.startswith("Acc_Baton"):
					# axe du baton le long de Y a la pose de repos
					u = (math.atan2(q.z - c.z, q.x - c.x) / (2 * math.pi)) % 1
					v = (q.y - b[2]) / (b[3] - b[2])
					uv[li].uv = dans("baton" if nom == "Acc_Baton" else "bague", u, v)
				elif nom == "Acc_Bourse":
					u = (math.atan2(q.y - c.y, q.x - c.x) / (2 * math.pi)) % 1
					uv[li].uv = dans("bourse", u, (b[5] - q.z) / (b[5] - b[4]))
				elif nom in ("Acc_Bourse_Cordon", "Acc_Carte_Ruban"):
					uv[li].uv = dans("cordon" if nom == "Acc_Bourse_Cordon" else "ruban", 0.5, (b[5] - q.z) / (b[5] - b[4]))
				else:  # carte : feuille (face avant dessinee, dos uni) et deux rouleaux
					rouleau = min(abs(pc.x - (c.x - 0.45)), abs(pc.x - (c.x + 0.45))) < 0.075
					if rouleau:
						cx = c.x - 0.45 if pc.x < c.x else c.x + 0.45
						u = (math.atan2(q.y - c.y, q.x - cx) / (2 * math.pi)) % 1
						uv[li].uv = dans("rouleau", u, (b[5] - q.z) / (b[5] - b[4]))
					elif n.y < -0.5:
						uv[li].uv = dans("carte", (q.x - (c.x - 0.425)) / 0.85, (c.z + 0.31 - q.z) / 0.62)  # feuille 0,85 x 0,62
					else:
						uv[li].uv = dans("dos_carte", 0.5, 0.5)
	(DOSSIER / "acc_nami.json").write_text(json.dumps(infos, indent="\t"), encoding="utf-8")
	img = bpy.data.images.get("tex_acc_nami.png")
	chemin = DOSSIER / "tex_acc_nami.png"
	if chemin.exists():
		img = img or bpy.data.images.load(str(chemin))
		img.filepath = "//tex_acc_nami.png"
		img.reload()
		m = bpy.data.materials.get("Mat_Acc_Nami") or bpy.data.materials.new("Mat_Acc_Nami")
		m.use_nodes = True
		nt = m.node_tree
		bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
		bsdf.inputs["Roughness"].default_value = 0.6
		tex = nt.nodes.get("Texture") or nt.nodes.new("ShaderNodeTexImage")
		tex.name = "Texture"
		tex.image = img
		nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
		for o in bpy.data.objects:
			if o.name.startswith("Acc_"):
				o.data.materials.clear()
				o.data.materials.append(m)
	print("acc_nami.json ecrit")
