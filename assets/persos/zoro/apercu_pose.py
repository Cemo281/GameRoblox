"""Applique une pose calculee par anims_zoro.py au mannequin de zoro_apercu.blend (MCP Blender).

	exec(open(r"<depot>/assets/persos/zoro/apercu_pose.py", encoding="utf-8").read())
	poser("Idle", 20)
Conversion (axes_r15.json) : rotation de l'os = B * Transform * B, location = B * position,
B = diag(-1, -1, 1) pour un os vers le bas, diag(-1, 1, -1) pour un os vers le haut.
"""

import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

DOSSIER_ANIMS = Path(r"C:\Users\alice\Documents\GameRoblox\assets\persos\zoro\anims")
OS_DE = {
	"Root": "LowerTorso", "Waist": "UpperTorso", "Neck": "Head",
	"RightShoulder": "RightUpperArm", "RightElbow": "RightLowerArm", "RightWrist": "RightHand",
	"LeftShoulder": "LeftUpperArm", "LeftElbow": "LeftLowerArm", "LeftWrist": "LeftHand",
	"RightHip": "RightUpperLeg", "RightKnee": "RightLowerLeg", "RightAnkle": "RightFoot",
	"LeftHip": "LeftUpperLeg", "LeftKnee": "LeftLowerLeg", "LeftAnkle": "LeftFoot",
}
VERS_LE_HAUT = {"LowerTorso", "UpperTorso", "Head"}


def poser(nom, image):
	poses = json.loads((DOSSIER_ANIMS / f"apercu_{nom}.json").read_text(encoding="utf-8"))[str(image)]
	rig = bpy.data.objects["Rig_R15"]
	for art, c in poses.items():
		os_nom = OS_DE[art]
		B = Matrix(((-1, 0, 0), (0, 1, 0), (0, 0, -1))) if os_nom in VERS_LE_HAUT else Matrix(((-1, 0, 0), (0, -1, 0), (0, 0, 1)))
		T = Matrix((c[3:6], c[6:9], c[9:12]))
		pb = rig.pose.bones[os_nom]
		pb.rotation_mode = "QUATERNION"
		pb.rotation_quaternion = (B @ T @ B).to_quaternion()
		pb.location = B @ Vector(c[:3])
	bpy.context.view_layer.update()


def montrer_sabres(droit=False, gauche=False, bouche=False, hanche=True):
	for nom, v in (("Acc_Sabre_Droit", droit), ("Acc_Sabre_Gauche", gauche), ("Acc_Sabre_Bouche", bouche), ("Acc_Sabres_Hanche", hanche)):
		o = bpy.data.objects[nom]
		o.hide_viewport = not v
		o.hide_render = not v
		o.hide_set(not v)
