"""pants_zoro.png sans le noir du torse (zoro v2 : le torse est fait par le Shirt d'abdos, transparent sur la peau).

Garde la bande verte du haramaki (bas des faces du torse, lignes 160 a 202) et toutes les jambes.
Usage : python assets/persos/zoro/pants_zoro_v2.py -> pants_zoro_v2.png
"""

from pathlib import Path

from PIL import Image

DOSSIER = Path(__file__).parent
im = Image.open(DOSSIER / "pants_zoro.png").convert("RGBA")
px = im.load()
for y in range(0, 160):  # dessus du torse (8-72) et haut des 4 faces (74-159)
    for x in range(160, 560):
        px[x, y] = (0, 0, 0, 0)
im.save(DOSSIER / "pants_zoro_v2.png")
print("ok", im.size)
