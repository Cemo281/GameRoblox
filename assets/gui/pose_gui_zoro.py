"""Pose d'interface de zoro (portrait et plein pied) : main droite posee sur les poignees a la hanche, bras gauche le long du corps.

Usage : uv run --with numpy --with scipy assets/gui/pose_gui_zoro.py
Sortie : assets/persos/zoro/anims/zoro_PoseGUI.json, format des apercu_*.json ({articulation: 12 composantes du Transform}),
lu par rendu_gui.py (POSES_PORTRAIT). Reutilise le rig, la FK et les verifications de anims_zoro.py.
"""

import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

DOSSIER_ZORO = Path(__file__).parent.parent / "persos" / "zoro"
sys.path.insert(0, str(DOSSIER_ZORO))
import anims_zoro as az  # noqa: E402

# poignee du sabre du milieu : de la garde vers l'arriere de l'axe (repere LowerTorso au repos)
a, b = az.SEGMENTS_HANCHE[1]
garde = a + (b - a) * (1.04 / (1.04 + 2.15))
vers_poignee = (a - garde) / np.linalg.norm(a - garde)
# main a plat sur la poignee, juste derriere la garde : la main fait 0,32 d'epaisseur, la poignee ~0,1 de rayon
CIBLE = garde + vers_poignee * 0.35 + np.array([0, 0.22, 0])


def pose_gui():
	p = az.neutre()
	p["LeftShoulder"] = (0, 0, -8)  # bras gauche le long du corps, decolle du manteau
	p["LeftElbow"] = (8, 0, 0)
	p["Waist"] = (2, -6, 0)  # buste un peu tourne vers la camera (vue de 3/4 cote droit)
	p["Neck"] = (6, -10, 0)  # menton releve, regard vers la camera
	cible = (az.fk(p)["LowerTorso"] @ np.append(CIBLE, 1))[:3]  # SEGMENTS_HANCHE est dans le repere local du LowerTorso
	# main de 1 stud de large, torse de 1 de demi-largeur : centre de la main au ras du flanc, par-dessus les poignees
	cible[0] = max(cible[0], 1.52)

	# grille sur les directions du bras (u : epaule -> coude) et de l'avant-bras (f : coude -> main) ; L-BFGS-B restait
	# bloque loin de la cible. Les collisions ne sont verifiees que sur les meilleurs candidats (verifier est lent).
	def direction_bas(ecart, azimut):
		e, a = math.radians(ecart), math.radians(azimut)
		return (math.sin(e) * math.sin(a), -math.cos(e), -math.sin(e) * math.cos(a))  # ecart a la verticale, azimut 0 = vers l'avant (-Z)

	candidats = []
	for eu, au, ef, af in itertools.product(range(0, 50, 5), range(-60, 61, 15), range(10, 95, 5), range(-90, 91, 15)):
		q = az.bras_dirige(p, "Right", direction_bas(eu, au), direction_bas(ef, af))
		if q is not None:
			candidats.append((float(np.sum((az.fk(q)["RightHand"][:3, 3] - cible) ** 2)), q))
	candidats.sort(key=lambda c: c[0])
	for d2, q in candidats[:300]:
		r = az.verifier(q)
		# la main touche les poignees (contact permis jusqu'a 0,12), le bras ne traverse ni le torse ni le manteau
		if all(v < 0.02 for k, v in r.items() if k.startswith("Right") and not k.endswith("fourreaux")) and r["RightHand>fourreaux"] < 0.12:
			return q, math.sqrt(d2)
	raise RuntimeError("aucune pose sans collision parmi les 300 plus proches")


if __name__ == "__main__":
	p, f = pose_gui()
	cfs = az.fk(p)
	print("distance main - cible", round(f, 3), {k: p[k] for k in ("RightShoulder", "RightElbow", "RightWrist")})
	print("main", np.round(cfs["RightHand"][:3, 3], 2), "verif", {k: round(v, 3) for k, v in az.verifier(p).items() if v > 0.005})
	sortie = {art: az.vers_douze(az.transform(p, art)) for art in az.ARTICULATIONS}
	(DOSSIER_ZORO / "anims" / "zoro_PoseGUI.json").write_text(json.dumps(sortie), encoding="utf-8")
	print("ecrit anims/zoro_PoseGUI.json")
