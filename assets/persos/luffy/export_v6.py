"""Export de la tenue v6 de luffy pour Studio : fbx/tenue_v6.fbx (6 pieces) + tenue_v6.json (soudure).

A lancer DANS Blender (MCP Blender), chemise_rig15.blend ouvert, apres chemise_v6.py et bas_v6.py :
	exec(open(r"<depot>/assets/persos/luffy/export_v6.py", encoding="utf-8").read())
	exporter_tenue()

Chaque piece : epaisseur appliquee, faces interieures et tranches -> UV d'une zone sombre de sa texture, un seul materiau,
maillage remis dans les axes du monde (pose du rig ignoree) et centre sur sa boite.
tenue_v6.json, en studs dans le repere Roblox de la piece R15 (x droite, y haut, z arriere) :
	MeshPart.Size = taille ; MeshPart.CFrame = Piece.CFrame * CFrame.new(decalage) ; WeldConstraint a la piece ;
	TextureID = l'image de "texture" (chemise : tex_chemise_v6_anime.png, bas : tex_bas_v6_anime.png).
Conversion Blender -> Roblox : (x, y, z) -> (x, z, -y) (l'avant du perso, +Y dans Blender, est -Z dans Roblox).
"""

import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

DOSSIER = Path(r"C:\Users\alice\Documents\GameRoblox\assets\persos\luffy")
T = 2048
PIECES_EXPORT = {
	"Chemise_Torse": ("UpperTorso", "chemise", (1800, 1900)),
	"Chemise_MancheD": ("RightUpperArm", "chemise", (1800, 1900)),
	"Chemise_MancheG": ("LeftUpperArm", "chemise", (1800, 1900)),
	"Ceinture": ("LowerTorso", "bas", (1470, 700)),
	"Short_JambeD": ("RightUpperLeg", "bas", (1870, 700)),
	"Short_JambeG": ("LeftUpperLeg", "bas", (1870, 700)),
}  # piece R15, texture, pixel (x, y depuis le haut) de la couleur interieure


def axes_monde(o):
	"""Matrice 3x3 (signes) qui remet les axes locaux de o dans les axes du monde les plus proches (pose ignoree)."""
	R = o.matrix_world.to_3x3().normalized()
	S = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
	for k in range(3):
		cible = Vector([1 if j == k else 0 for j in range(3)])
		i = max(range(3), key=lambda a: abs(R.col[a].dot(cible)))
		S[k][i] = 1 if R.col[i].dot(cible) > 0 else -1
	return S


def boite(points):
	mn = Vector([min(p[k] for p in points) for k in range(3)])
	mx = Vector([max(p[k] for p in points) for k in range(3)])
	return (mn + mx) / 2, mx - mn


def exporter_tenue():
	dg = bpy.context.evaluated_depsgraph_get()
	infos, copies = {}, []
	for nom, (piece, tex, (px, py)) in PIECES_EXPORT.items():
		o = bpy.data.objects[nom]
		corps = bpy.data.objects[piece]
		me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))  # epaisseur appliquee, coordonnees locales
		uv = me.uv_layers.active.data
		pastille = (px / T, 1 - py / T)
		for p in me.polygons:
			if p.material_index != 0:
				for li in p.loop_indices:
					uv[li].uv = pastille
			p.material_index = 0
		mat = o.data.materials[0]
		me.materials.clear()
		me.materials.append(mat)
		S = axes_monde(o)
		c_piece, _ = boite([v.co for v in me.vertices])
		c_corps, _ = boite([v.co for v in corps.data.vertices])
		me.transform(Matrix.Translation(-c_piece))
		me.transform(S.to_4x4())
		_, taille = boite([v.co for v in me.vertices])
		dec = S @ (c_piece - c_corps)
		infos[nom] = {
			"piece": piece,
			"texture": tex,
			"taille": [round(taille.x, 4), round(taille.z, 4), round(taille.y, 4)],
			"decalage": [round(dec.x, 4), round(dec.z, 4), round(-dec.y, 4)],
			"triangles": sum(len(p.vertices) - 2 for p in me.polygons),
		}
		o.name = nom + "__src"  # la copie exportee prend le vrai nom (Studio garde le nom de l'objet)
		copie = bpy.data.objects.new(nom, me)
		bpy.context.scene.collection.objects.link(copie)
		copies.append((copie, o, nom))
	(DOSSIER / "fbx").mkdir(exist_ok=True)
	chemin = DOSSIER / "fbx" / "tenue_v6.fbx"
	exportes = [c for c, _, _ in copies]
	for x in bpy.context.view_layer.objects:
		x.select_set(x in exportes)
	bpy.context.view_layer.objects.active = exportes[0]
	try:
		bpy.ops.export_scene.fbx(filepath=str(chemin), use_selection=True, object_types={"MESH"}, axis_forward="-Z", axis_up="Y",
			apply_scale_options="FBX_SCALE_ALL", path_mode="COPY", embed_textures=False, mesh_smooth_type="FACE")
	finally:
		for c, o, nom in copies:
			me = c.data
			bpy.data.objects.remove(c, do_unlink=True)
			bpy.data.meshes.remove(me)
			o.name = nom
	(DOSSIER / "tenue_v6.json").write_text(json.dumps(infos, indent="\t", ensure_ascii=False), encoding="utf-8")
	for n, i in infos.items():
		print(n, i)
	return chemin
