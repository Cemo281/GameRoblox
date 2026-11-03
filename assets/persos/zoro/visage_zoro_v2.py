"""Visage de zoro v2 : colle une image de visage (fond couleur peau) sur la face avant de la tete.

- fond couleur peau rendu transparent (la tete garde la couleur du corps, comme le torse) ;
- traits mis a l'echelle et places pour que les yeux tombent sous le bandana
  (le bandana descend jusqu'a environ 57 % de la hauteur de la tete).
Usage : python assets/persos/zoro/visage_zoro_v2.py <source> -> visage_zoro_<source>.png (512x512)
Sources : "import" (Decal 11147423022 du Zoro importe), "2" (image fournie le 2026-10-31, oeil gauche ferme).
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

DOSSIER = Path(__file__).parent
TOLERANCE = (22.0, 55.0)  # distance a la peau : transparent en dessous, opaque au-dessus

# fichier, couleur du fond, centre des yeux (x, y), echelle, hauteur des yeux dans la cible (fraction), etirement en largeur
SOURCES = {
	# yeux y 185, bouche y 300 : yeux -> bouche = 22 % de la hauteur
	"import": ("visage_import_11147423022.png", (231, 178, 136), (190, 185), 0.98, 0.67, 1.0),
	# yeux y 150 (x 73-355), bas de la levre y 322 : yeux a 53 % (bord du bandana a 57 % : haut des yeux sous le bandana), levre a 83 % ; largeur 0,9 x 1,2 = 1,08
	"2": ("visage_source_2.png", (255, 203, 153), (214, 150), 0.9, 0.53, 1.2),
}

nom = sys.argv[1] if len(sys.argv) > 1 else "2"
fichier, peau, yeux_src, echelle, yeux_y, largeur = SOURCES[nom]

src = Image.open(DOSSIER / fichier).convert("RGBA")
px = np.array(src).astype(float)
d = np.linalg.norm(px[..., :3] - np.array(peau, dtype=float), axis=2)
px[..., 3] = np.clip((d - TOLERANCE[0]) / (TOLERANCE[1] - TOLERANCE[0]), 0, 1) * 255
src = Image.fromarray(px.astype(np.uint8), "RGBA")

w, h = round(src.width * echelle * largeur), round(src.height * echelle)
grand = src.resize((w, h), Image.LANCZOS)
sortie = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
sortie.alpha_composite(grand, (round(256 - yeux_src[0] * echelle * largeur), round(yeux_y * 512 - yeux_src[1] * echelle)))
sortie.save(DOSSIER / f"visage_zoro_{nom}.png")
print("ok", nom, (w, h))
