"""Images d'interface d'un personnage rendues depuis Studio (le modele du jeu fait foi), pas depuis Blender.

A utiliser quand le modele de ReplicatedStorage.ModelesPersonnages.<Id> differe du .blend (corps, tete ou cheveux de
Roblox). Meme sortie que rendu_gui.py dans assets/gui/<Id>/ : portrait.png, pied.png, silhouette.png, idle_sheet.png,
infos.json (ids_roblox conserves).

Procedure (MCP Roblox_Studio, en Play, cote Client ; voir plateau_studio.luau) :
1. un plateau par image et par fond (copie du modele figee a son image de l'Idle publiee, fond SurfaceGui sans
   lumiere noir puis gris), pose 0 = portrait / plein pied, poses 1..16 = grille ;
2. cibles.json (cadrages calcules dans Studio) puis prises.json (camera de chaque capture : python rendu_studio.py
   prises <dossier>) ;
3. une capture screen_capture par prise, rangee dans <dossier>/captures/NN.jpg (ordre de prises.json) ;
4. python rendu_studio.py images <dossier> <Id> : detourage par difference des deux fonds, reprojection exacte des
   captures vers la camera cible (meme repere que rendu_gui.py : 3/4 a 30 degres, tete a 4,75 studs de haut),
   cadrage du plein pied et de la grille sur l'alpha, contour sombre.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

DEPOT = Path(__file__).resolve().parents[2]
SORTIE = DEPOT / "assets" / "gui"

CONTOUR = ((0.06, 0.04, 0.08), 2.0)  # comme rendu_gui.py : couleur, epaisseur en pixels pour une image de 512
PIED = {"taille": 1024, "marge": 0.06}
GRILLE = {"cote": 4, "taille": 256}
SURECHANTILLON = 2
SEUIL_ALPHA = 0.05  # bruit JPEG du fond


# ---------------------------------------------------------------- cameras


def repere(pos, vise):
	fw = np.asarray(vise, float) - np.asarray(pos, float)
	fw /= np.linalg.norm(fw)
	rt = np.cross(fw, [0.0, 1.0, 0.0])
	rt /= np.linalg.norm(rt)
	return fw, rt, np.cross(rt, fw)


def prises(dossier):
	"""Camera de chaque capture (fov 40 : portrait et plein pied en 2 bandes ; fov 70 : une capture par case)."""
	c = json.loads((dossier / "cibles.json").read_text(encoding="utf-8"))
	liste = []

	def ajoute(nom, cible, tx, ty, fov, plateaux):
		fw, rt, up = repere(cible["pos"], cible["centre"])
		d = fw + rt * tx + up * ty
		d /= np.linalg.norm(d)
		for i in plateaux:
			p = np.array(c["O"][i]) + np.array(cible["pos"])
			liste.append({"nom": nom, "plateau": i, "fond": i % 2, "fov": fov, "pos": [round(float(v), 5) for v in p], "vise": [round(float(v), 5) for v in p + d * 10]})

	ajoute("portrait", c["portrait"], c["portrait"]["cx"], c["portrait"]["cy"], 40, [0, 1])
	for nom, dy in (("pied_haut", 0.26), ("pied_bas", -0.26)):
		ajoute(nom, c["pied"], c["pied"]["cx"], c["pied"]["cy"] + dy, 40, [0, 1])
	for k in range(GRILLE["cote"] ** 2):
		ajoute(f"case{k:02d}", c["grille"], c["grille"]["cx"], c["grille"]["cy"], 70, [2 + 2 * k, 3 + 2 * k])
	(dossier / "prises.json").write_text(json.dumps(liste, indent=1), encoding="utf-8")
	return liste


# ---------------------------------------------------------------- detourage


def detourer(noir, gris):
	"""Deux captures identiques sur fond noir et gris -> RGBA premultiplie (flottants 0..1)."""
	n = np.asarray(noir, float) / 255
	g = np.asarray(gris, float) / 255
	ecart = (g - n).mean(axis=2)
	fond = ecart > 0.55
	plein = np.median(ecart[fond])  # ecart des deux fonds (correction de couleur du jeu comprise)
	fond_noir = np.median(n[fond], axis=0)
	a = np.clip(1 - ecart / plein, 0, 1)
	a = np.clip((a - SEUIL_ALPHA) / (1 - 2 * SEUIL_ALPHA), 0, 1)
	rgb = np.clip(n - (1 - a[..., None]) * fond_noir, 0, None)
	rgb = np.minimum(rgb, a[..., None])  # premultiplie
	return np.dstack([rgb, a])


# ---------------------------------------------------------------- reprojection


def echantillonner(img, u, v):
	"""Bilineaire ; hors image -> transparent."""
	h, l = img.shape[:2]
	dedans = (u >= 0) & (u <= l - 1) & (v >= 0) & (v <= h - 1)
	u = np.clip(u, 0, l - 1.001)
	v = np.clip(v, 0, h - 1.001)
	u0, v0 = np.floor(u).astype(int), np.floor(v).astype(int)
	fu, fv = (u - u0)[..., None], (v - v0)[..., None]
	p = img[v0, u0] * (1 - fu) * (1 - fv) + img[v0, u0 + 1] * fu * (1 - fv) + img[v0 + 1, u0] * (1 - fu) * fv + img[v0 + 1, u0 + 1] * fu * fv
	return np.where(dedans[..., None], p, 0), dedans


def projeter(cible, fenetre, taille, tuiles):
	"""Image taille x taille de la camera cible sur la fenetre (cx, cy, demi-cote en tangentes), depuis les tuiles."""
	cx, cy, th = fenetre
	n = taille * SURECHANTILLON
	fw, rt, up = repere(cible["pos"], cible["centre"])
	t = (np.arange(n) + 0.5) / n * 2 - 1
	x = cx + t[None, :] * th
	y = cy - t[:, None] * th
	d = fw[None, None] + x[..., None] * rt[None, None] + y[..., None] * up[None, None]
	sortie = np.zeros((n, n, 4))
	meilleur = np.full((n, n), np.inf)
	for img, pr in tuiles:
		tf, tr, tu = repere(pr["pos"], pr["vise"])
		h, l = img.shape[:2]
		f = (h / 2) / np.tan(np.radians(pr["fov"]) / 2)
		z = d @ tf
		xt, yt = (d @ tr) / z, (d @ tu) / z
		p, dedans = echantillonner(img, l / 2 + xt * f - 0.5, h / 2 - yt * f - 0.5)
		score = np.where(dedans & (z > 0), np.abs(xt) + np.abs(yt), np.inf)  # pixel le plus proche du centre d'une tuile
		prendre = score < meilleur
		sortie[prendre] = p[prendre]
		meilleur[prendre] = score[prendre]
	return sortie.reshape(taille, SURECHANTILLON, taille, SURECHANTILLON, 4).mean(axis=(1, 3))


def boite_alpha(img, fenetre):
	"""Boite de l'alpha en tangentes (xmin, xmax, ymin, ymax)."""
	cx, cy, th = fenetre
	n = img.shape[0]
	lignes, cols = np.nonzero(img[..., 3] > 0.1)
	x = cx + ((cols + 0.5) / n * 2 - 1) * th
	y = cy - ((lignes + 0.5) / n * 2 - 1) * th
	return x.min(), x.max(), y.min(), y.max()


def cadrer(boite, marge):
	"""Comme cadrer_pied de rendu_gui.py : tout tient avec la marge, pieds sur la marge du bas, centre en largeur."""
	ax, bx, ay, by = boite
	th = max(bx - ax, by - ay) / (1 - 2 * marge) / 2
	return ((ax + bx) / 2, ay - marge * 2 * th + th, th)


# ---------------------------------------------------------------- finitions


def contour(img):
	"""Contour sombre autour de la silhouette (epaisseur de rendu_gui.py), dessine sous le perso."""
	r = CONTOUR[1] * img.shape[0] / 512
	a = img[..., 3]
	h, l = a.shape
	k = int(np.ceil(r))
	bord = np.pad(a, k)  # decalages sans reboucler (le bas coupe du portrait ne doit pas border le haut)
	dil = a.copy()
	for dy in range(-k, k + 1):
		for dx in range(-k, k + 1):
			dist = np.hypot(dx, dy)
			if dist > r + 0.5:
				continue
			poids = np.clip(r + 0.5 - dist, 0, 1)
			dil = np.maximum(dil, bord[k + dy : k + dy + h, k + dx : k + dx + l] * poids)
	fond = np.dstack([np.array(CONTOUR[0])[None, None] * dil[..., None], dil])
	return img + fond * (1 - a[..., None])


def png(chemin, premult):
	a = premult[..., 3:4]
	rgb = np.where(a > 0, premult[..., :3] / np.maximum(a, 1e-6), 0)
	Image.fromarray(np.clip(np.round(np.dstack([rgb, a]) * 255), 0, 255).astype(np.uint8), "RGBA").save(chemin, optimize=True)


def raccord_idle(id):
	"""Ecart max entre la premiere et la derniere cle de l'Idle (0 = boucle sans saut), d'apres anims/<Id>_Idle.json."""
	f = DEPOT / "assets" / "persos" / id / "anims" / f"{id}_Idle.json"
	if not f.exists():
		return None
	cles = json.loads(f.read_text(encoding="utf-8"))["cles"]
	a, b = cles[0]["poses"], cles[-1]["poses"]
	return round(max(abs(x - y) for art in a for x, y in zip(a[art]["cframe"], b[art]["cframe"])), 6), cles[-1]["image"]


# ---------------------------------------------------------------- point d'entree


def images(dossier, id):
	c = json.loads((dossier / "cibles.json").read_text(encoding="utf-8"))
	liste = json.loads((dossier / "prises.json").read_text(encoding="utf-8"))
	captures = [np.asarray(Image.open(dossier / "captures" / f"{i:02d}.jpg").convert("RGB")) for i in range(len(liste))]
	detoures = {}
	for i in range(0, len(liste), 2):
		pr = liste[i]
		assert pr["fond"] == 0 and liste[i + 1]["fond"] == 1 and liste[i + 1]["nom"] == pr["nom"]
		detoures.setdefault(pr["nom"], []).append((detourer(captures[i], captures[i + 1]), pr))
	sortie = SORTIE / id
	sortie.mkdir(parents=True, exist_ok=True)

	po = c["portrait"]
	portrait = projeter(po, (po["cx"], po["cy"], po["th"]), 512, detoures["portrait"])
	coupe_haut = int((portrait[0, :, 3] > 0.03).sum())
	if coupe_haut:
		print(f"ATTENTION {id} : {coupe_haut} pixels opaques sur le bord haut du portrait (chapeau ou cheveux coupes)")
	portrait = contour(portrait)
	png(sortie / "portrait.png", portrait)
	alpha = np.clip((portrait[..., 3] - 0.5) * 3 + 0.5, 0, 1)
	png(sortie / "silhouette.png", np.dstack([np.zeros(alpha.shape + (3,)), alpha]))

	pi = c["pied"]
	large = (pi["cx"], pi["cy"], pi["th"] * 1.3)
	tuiles = detoures["pied_haut"] + detoures["pied_bas"]
	fen = cadrer(boite_alpha(projeter(pi, large, 512, tuiles), large), PIED["marge"])
	png(sortie / "pied.png", contour(projeter(pi, fen, PIED["taille"], tuiles)))

	gr = c["grille"]
	large = (gr["cx"], gr["cy"], gr["th"] * 1.3)
	cases = [detoures[f"case{k:02d}"] for k in range(GRILLE["cote"] ** 2)]
	boites = np.array([boite_alpha(projeter(gr, large, 256, t), large) for t in cases])
	fen = cadrer((boites[:, 0].min(), boites[:, 1].max(), boites[:, 2].min(), boites[:, 3].max()), PIED["marge"])
	n = GRILLE["taille"]
	feuille = np.zeros((n * GRILLE["cote"], n * GRILLE["cote"], 4))
	for k, t in enumerate(cases):
		ligne, col = divmod(k, GRILLE["cote"])
		feuille[ligne * n : (ligne + 1) * n, col * n : (col + 1) * n] = contour(projeter(gr, fen, n, t))
	png(sortie / "idle_sheet.png", feuille)

	images_idle = c["images"]  # [image, fond, temps] par plateau
	raccord = raccord_idle(id)
	duree = c["duree"]
	nb = GRILLE["cote"] ** 2
	infos = {
		"id": id,
		"source": f"Studio : ReplicatedStorage.ModelesPersonnages.{id} (rendu_studio.py)",
		"animation": c["animation"],
		"images": {
			"portrait.png": {"taille": [512, 512], "pose": images_idle[0][0], "temps": round(images_idle[0][2], 4)},
			"pied.png": {"taille": [PIED["taille"]] * 2, "pose": images_idle[0][0], "temps": round(images_idle[0][2], 4)},
			"silhouette.png": {"taille": [512, 512], "cadrage": "portrait"},
			"idle_sheet.png": {
				"taille": [n * GRILLE["cote"]] * 2,
				"grille": [GRILLE["cote"]] * 2,
				"taille_case": [n, n],
				"ordre": "ligne par ligne, de gauche a droite puis de haut en bas (case k : ligne k // 4, colonne k % 4)",
				"images_animation": [images_idle[2 + 2 * k][0] for k in range(nb)],
			},
		},
		"boucle": {
			"duree": duree,
			"images": raccord[1] if raccord else None,
			"fps_source": 30,
			"raccord_fin_debut": raccord[0] if raccord else None,
		},
		"fps_conseille": round(nb / duree, 4),
	}
	ancien = sortie / "infos.json"
	if ancien.exists():  # IDs Roblox notes apres l'envoi : a garder (a renvoyer si l'image a change)
		infos["ids_roblox"] = json.loads(ancien.read_text(encoding="utf-8")).get("ids_roblox", {})
	ancien.write_text(json.dumps(infos, indent="\t", ensure_ascii=False), encoding="utf-8")
	print(f"{id} : images dans {sortie}")
	return infos


if __name__ == "__main__":
	action, dossier = sys.argv[1], Path(sys.argv[2])
	if action == "prises":
		for p in prises(dossier):
			print(p["nom"], p["fond"], p["fov"], p["pos"], p["vise"])
	else:
		images(dossier, sys.argv[3])
