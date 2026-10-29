"""Exporte les vetements 3D de nami (haut, jean, sandales, bracelets) pour les poser sur l'avatar R15 vide de Studio.

A lancer DANS Blender (MCP Blender), nami.blend ouvert, apres construire_nami.py / uv_nami.py :
	exec(open(r"<depot>/assets/persos/nami/export_vetements.py", encoding="utf-8").read())
	exporter()   # fbx/vetements_nami.fbx + vetements_nami.json, verification par reimport
	exporter_accessoires()   # fbx/accessoires_nami.fbx + accessoires_nami.json (Acc_Bourse, Acc_Carte)

Un objet par piece R15 (Vet_<Piece>), texture tex_corps_nami.png (atlas commun) integree. vetements_nami.json donne, pour
chaque Vet_<Piece>, sa taille et le centre de sa boite par rapport au centre de la piece R15 (reperes Roblox, studs) :
dans Studio, MeshPart.Size = taille, MeshPart.CFrame = Piece.CFrame * CFrame.new(decalage), puis Weld a la piece.
"""

import json
from pathlib import Path

import bpy
from mathutils import Vector

DOSSIER = Path(r"C:\Users\alice\Documents\GameRoblox\assets\persos\nami")
RIG = json.loads((DOSSIER.parent / "_mannequin" / "r15_bloc.json").read_text(encoding="utf-8"))
CENTRES = RIG["blender"]["centres_r15"]

GROUPES = {
	"UpperTorso": ["UpperTorso_Haut"],
	"LowerTorso": ["LowerTorso_Jean", "LowerTorso_Bouton", "LowerTorso_Ceinture", "LowerTorso_Clous"],
	"LeftUpperLeg": ["LeftUpperLeg_Jean"],
	"RightUpperLeg": ["RightUpperLeg_Jean"],
	"LeftLowerLeg": ["LeftLowerLeg_Jean"],
	"RightLowerLeg": ["RightLowerLeg_Jean"],
	"LeftFoot": ["LeftFoot_Sandale"],
	"RightFoot": ["RightFoot_Sandale"],
	"LeftLowerArm": ["LeftLowerArm_Bracelets", "LeftLowerArm_Boussole"],
}


def vers_roblox(v):
	"""Vecteur Blender -> Roblox (sans la hauteur : pour des ecarts et des tailles)."""
	return [-v.x, v.z, v.y]


# accessoires separes (main gauche, caches par defaut) : nom de l'objet exporte -> (piece porteuse, objets Blender)
ACCESSOIRES = {
	"Acc_Bourse": ("LeftHand", ["Acc_Bourse", "Acc_Bourse_Cordon"]),
	"Acc_Carte": ("LeftHand", ["Acc_Carte", "Acc_Carte_Ruban"]),
}


def exporter():
	"""Vetements : fbx/vetements_nami.fbx + vetements_nami.json."""
	return _exporter({"Vet_" + p: (p, noms) for p, noms in GROUPES.items()}, "vetements_nami")


def exporter_accessoires():
	"""Acc_Bourse et Acc_Carte : fbx/accessoires_nami.fbx (texture tex_acc_nami.png) + accessoires_nami.json."""
	return _exporter(ACCESSOIRES, "accessoires_nami")


def _exporter(groupes, nom):
	rig = bpy.data.objects["Rig_R15"]
	for pb in rig.pose.bones:
		pb.rotation_euler = (0, 0, 0)
		pb.location = (0, 0, 0)
	bpy.context.view_layer.update()
	# un objet d'origine peut porter le nom de l'objet exporte (Acc_Bourse) : renomme le temps de l'export
	renommes = {}
	for nom_objet, (_, noms) in groupes.items():
		if nom_objet in noms:
			bpy.data.objects[nom_objet].name = nom_objet + "__src"
			renommes[nom_objet] = nom_objet + "__src"
	infos = {}
	objets = []
	for nom_objet, (piece, noms) in groupes.items():
		copies = []
		for n in noms:
			src = bpy.data.objects[renommes.get(n, n)]
			me = src.data.copy()
			me.transform(src.matrix_world)
			c = bpy.data.objects.new("tmp_" + n, me)
			bpy.context.scene.collection.objects.link(c)
			copies.append(c)
		with bpy.context.temp_override(active_object=copies[0], object=copies[0], selected_objects=copies, selected_editable_objects=copies):
			bpy.ops.object.join()
		o = copies[0]
		o.name = o.data.name = nom_objet
		o.hide_viewport = o.hide_render = False
		ps = [v.co for v in o.data.vertices]
		mn = Vector((min(p.x for p in ps), min(p.y for p in ps), min(p.z for p in ps)))
		mx = Vector((max(p.x for p in ps), max(p.y for p in ps), max(p.z for p in ps)))
		centre_boite = (mn + mx) / 2
		# origine au centre de la boite (l'importeur de Studio centre la MeshPart sur sa boite)
		o.data.transform(__import__("mathutils").Matrix.Translation(-centre_boite))
		o.location = centre_boite
		taille = mx - mn
		ecart = centre_boite - Vector(CENTRES[piece])
		infos[nom_objet] = {
			"piece": piece,
			"taille": [round(abs(t), 4) for t in vers_roblox(taille)],
			"decalage": [round(t, 4) for t in vers_roblox(ecart)],
			"triangles": sum(len(p.vertices) - 2 for p in o.data.polygons),
		}
		objets.append(o)
	(DOSSIER / "fbx").mkdir(exist_ok=True)
	chemin = DOSSIER / "fbx" / (nom + ".fbx")
	for o in bpy.context.scene.objects:
		o.select_set(o in objets)
	bpy.context.view_layer.objects.active = objets[0]
	bpy.ops.export_scene.fbx(
		filepath=str(chemin), use_selection=True, object_types={"MESH"}, axis_forward="-Z", axis_up="Y",
		apply_scale_options="FBX_SCALE_ALL", path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE", use_mesh_modifiers=True,
	)
	(DOSSIER / (nom + ".json")).write_text(json.dumps(infos, indent="\t"), encoding="utf-8")
	for o in objets:
		bpy.data.objects.remove(o, do_unlink=True)
	for nom_objet, tmp in renommes.items():
		bpy.data.objects[tmp].name = nom_objet
	print("%s.fbx : %d objets, %d triangles" % (nom, len(infos), sum(v["triangles"] for v in infos.values())))
	return verifier(chemin, infos)


def verifier(chemin, infos):
	"""Reimporte le FBX dans une scene temporaire : noms, tailles (studs, reperes Blender), texture, UV."""
	sc_avant = bpy.context.window.scene
	sc = bpy.data.scenes.new("Verif_FBX")
	bpy.context.window.scene = sc
	avant = set(bpy.data.objects)
	bpy.ops.import_scene.fbx(filepath=str(chemin))
	res = []
	for o in set(bpy.data.objects) - avant:
		if o.type != "MESH":
			continue
		dims = o.dimensions
		mat = o.data.materials[0] if o.data.materials else None
		tex = None
		if mat and mat.use_nodes:
			tex = next((n.image.name for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
		attendu = infos.get(o.name)
		res.append("%s dims %s attendu %s tex %s uv %d" % (o.name, [round(d, 3) for d in dims], attendu and attendu["taille"], tex, len(o.data.uv_layers)))
	for o in set(bpy.data.objects) - avant:
		bpy.data.objects.remove(o, do_unlink=True)
	bpy.context.window.scene = sc_avant
	bpy.data.scenes.remove(sc)
	fbm = chemin.with_suffix(".fbm")
	if fbm.exists():
		import shutil

		shutil.rmtree(fbm)
	print("\n".join(res))
	return res
