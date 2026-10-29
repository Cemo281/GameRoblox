"""Ecrit r15_bloc.json (v2) a partir de releve_brut.json.

Usage : python assets/persos/_mannequin/rig_r15.py

Rig R15 en blocs de Roblox nettoye : paires gauche / droite symetrisees (ecarts du releve < 0,0005 stud),
articulations dans le plan z = 0, blocs visibles de chaque piece (d'une articulation a la suivante),
tete du mannequin (cube arrondi de la hauteur de la tete R15), coordonnees Blender.
La section "mannequin" (tailles et CFrame des MeshPart du mannequin, C0 / C1) est ajoutee par
construire_mannequin.py, a partir des boites reelles des maillages.
"""

import json
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
BRUT = json.loads((DOSSIER / "releve_brut.json").read_text(encoding="utf-8"))
P = BRUT["releve"]["pieces"]
J = BRUT["releve"]["joints"]
ARRONDI = 6

# tete du mannequin (Roblox : x = largeur, y = hauteur, z = profondeur)
TETE = {"largeur_haut": 1.24, "largeur_bas": 1.08, "profondeur": 1.16, "exposant_horizontal": 3.2, "exposant_vertical": 3.0}


def r(v):
	return round(v + 0.0, ARRONDI)


def centre(nom):
	return P[nom]["cframe"][:3]


def symetrique(nom, f):
	"""Moyenne de f sur la piece / articulation et sa symetrique, x remis au bon signe."""
	if nom.startswith("Left") or nom.startswith("Right"):
		cote = "Left" if nom.startswith("Left") else "Right"
		autre = ("Right" if cote == "Left" else "Left") + nom[len(cote) :]
		a, b = f(nom), f(autre)
		x = (abs(a[0]) + abs(b[0])) / 2
		return [r(x if cote == "Right" else -x), r((a[1] + b[1]) / 2), 0.0]
	a = f(nom)
	return [0.0, r(a[1]), 0.0]


def main():
	# articulations relevees, vues des deux pieces
	ecart_max = 0.0
	brut_art = {}
	for nom, j in J.items():
		a0 = [centre(j["part0"])[i] + j["c0"][i] for i in range(3)]
		a1 = [centre(j["part1"])[i] + j["c1"][i] for i in range(3)]
		ecart_max = max(ecart_max, max(abs(a0[i] - a1[i]) for i in range(3)))
		brut_art[nom] = a0

	centres = {nom: symetrique(nom, centre) for nom in P}
	art = {nom: symetrique(nom, lambda n: brut_art[n]) for nom in J}
	tailles = {nom: P[nom]["taille"] for nom in P}

	def haut(nom):
		return centres[nom][1] + tailles[nom][1] / 2

	def bas(nom):
		return centres[nom][1] - tailles[nom][1] / 2

	# blocs visibles (repere Roblox relatif au HRP) : [[xmin, xmax], [ymin, ymax], [zmin, zmax]]
	blocs = {
		"UpperTorso": [[-0.972, 0.972], [art["Waist"][1], art["Neck"][1]], [-0.502, 0.502]],
		"LowerTorso": [[-0.996, 0.996], [art["Root"][1], art["Waist"][1]], [-0.502, 0.502]],
	}
	for cote, s in (("Right", 1), ("Left", -1)):
		xb = abs(centres[cote + "UpperArm"][0])
		xj = abs(centres[cote + "UpperLeg"][0])
		haut_main, haut_pied = haut(cote + "Hand"), haut(cote + "Foot")

		def bx(xc, demi):
			return sorted([r(s * (xc - demi)), r(s * (xc + demi))])

		blocs[cote + "UpperArm"] = [bx(xb, 0.5005), [art[cote + "Elbow"][1], r(haut(cote + "UpperArm"))], [-0.501, 0.501]]
		blocs[cote + "LowerArm"] = [bx(xb, 0.5005), [r(haut_main), art[cote + "Elbow"][1]], [-0.501, 0.501]]
		blocs[cote + "Hand"] = [bx(xb, 0.4921), [r(bas(cote + "Hand")), r(haut_main)], [-0.5141, 0.5141]]
		blocs[cote + "UpperLeg"] = [bx(xj, 0.496), [art[cote + "Knee"][1], -0.79], [-0.486, 0.486]]
		blocs[cote + "LowerLeg"] = [bx(xj, 0.496), [r(haut_pied), art[cote + "Knee"][1]], [-0.486, 0.486]]
		blocs[cote + "Foot"] = [bx(xj, 0.5044), [r(bas(cote + "Foot")), r(haut_pied)], [-0.5005, 0.5005]]
	ht = tailles["Head"][1]
	cy = centres["Head"][1]
	blocs["Head"] = dict(
		TETE,
		centre=[0.0, cy, 0.0],
		hauteur=r(ht),
		note="cube tres arrondi (superellipsoide), plus large en haut ; meme hauteur et meme centre que la tete dynamique R15 (1,159 x 1,182 x 1,161)",
	)

	pieds = min(bas(n) for n in ("LeftFoot", "RightFoot"))
	h = r(-pieds)

	def vers_blender(p):
		return [r(-p[0]), r(p[2]), r(p[1] + h)]

	motors = {}
	for nom, j in J.items():
		motors[nom] = {
			"part0": j["part0"],
			"part1": j["part1"],
			"c0": [r(art[nom][i] - centres[j["part0"]][i]) for i in range(3)] + [1, 0, 0, 0, 1, 0, 0, 0, 1],
			"c1": [r(art[nom][i] - centres[j["part1"]][i]) for i in range(3)] + [1, 0, 0, 0, 1, 0, 0, 0, 1],
		}

	sortie = {
		"source": "Releve du 2026-10-29 (releve_brut.json) : Players:CreateHumanoidModelFromDescription(HumanoidDescription vide, R15) en mode edition. Articulations Roblox = AnimationConstraint, C0 = Attachment0.CFrame, C1 = Attachment1.CFrame (equivalent Motor6D). Nettoyage par rig_r15.py : paires gauche / droite symetrisees, articulations a z = 0 (ecart max du releve entre les deux pieces d'une articulation : %.6f stud)." % ecart_max,
		"repere": "Roblox : Y = haut, le perso regarde vers -Z, sa droite est +X. CFrame = 12 composantes {x, y, z, R00, R01, R02, R10, R11, R12, R20, R21, R22}. Positions relatives a HumanoidRootPart.",
		"hauteurHRP": h,
		"hipHeight": r(BRUT["hipHeight"]),
		"piedsY": 0.0,
		"blender": {
			"correspondance": "Blender (x, y, z) = (-xR, zR, yR + hauteurHRP) ; inverse : Roblox (x, y, z) = (-xB, zB - hauteurHRP, yB). Matrice A = ((-1,0,0),(0,0,1),(0,1,0)), det = +1. Le perso regarde vers -Y, sa droite est -X, pieds a Z = 0, 1 unite = 1 stud.",
			"articulations": {n: vers_blender(p) for n, p in art.items()},
			"centres_r15": {n: vers_blender(p) for n, p in centres.items()},
		},
		"r15": {
			"note": "pieces du rig Roblox d'origine (MeshPart R15 en blocs, avec leurs bouchons caches), pour reference",
			"pieces": {n: {"taille": [r(v) for v in tailles[n]], "cframe": centres[n] + [1, 0, 0, 0, 1, 0, 0, 0, 1]} for n in P},
			"motors": motors,
		},
		"articulations": art,
		"attachments": BRUT["attachments"],
		"blocs_visibles": dict(
			{"note": "Boites visibles du R15 en blocs (repere Roblox relatif au HRP) : [[xmin, xmax], [ymin, ymax], [zmin, zmax]]. Chaque bloc va d'une articulation a la suivante ; le haut de la cuisse (-0,79 a -1,0) est cache dans le LowerTorso. Le mannequin arrondit ces blocs (biseau 0,15) et ajoute un cylindre de jointure aux coudes et aux genoux."},
			**blocs,
		),
	}
	ancien = DOSSIER / "r15_bloc.json"
	if ancien.exists():
		precedent = json.loads(ancien.read_text(encoding="utf-8"))
		if "mannequin" in precedent:
			sortie["mannequin"] = precedent["mannequin"]
	ancien.write_text(json.dumps(sortie, ensure_ascii=False, indent="\t"), encoding="utf-8")
	print("ecart max releve : %.6f, hauteurHRP %.6f" % (ecart_max, h))
	for n in ("Neck", "RightShoulder", "RightElbow", "RightWrist", "RightHip", "RightKnee", "RightAnkle"):
		print(n, art[n])


if __name__ == "__main__":
	main()
