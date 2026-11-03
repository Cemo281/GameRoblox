"""Graphique du torse de zoro (ShirtGraphic) : abdos de l'image fournie + cicatrice en diagonale.

L'image source (abdos_source.png) a un faux damier de transparence : les traits gris (~160) sont gardés,
le damier (>= 228) devient transparent. Les traits prennent une teinte d'ombre de peau (pas de noir).
Cicatrice : de l'épaule gauche de zoro (à droite de l'image) à la hanche droite, peinte en aplats doux
(bourrelet rosé, bord plus foncé, points de suture discrets).
Usage : python assets/persos/zoro/torse_zoro.py -> torse_zoro.png (512 x 512)
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DOSSIER = Path(__file__).parent
TAILLE = 512
OMBRE = (150, 92, 62)  # ombre de peau (peau #E8B48C)
CICATRICE = (196, 118, 104)
CICATRICE_BORD = (140, 76, 64)
SUTURE = (120, 66, 56)

# 1. Abdos : alpha selon la luminance, couleur d'ombre de peau
src = Image.open(DOSSIER / "abdos_source.png").convert("L")
alpha = src.point(lambda v: 255 if v < 214 else 0).filter(ImageFilter.MedianFilter(5))
alpha = alpha.filter(ImageFilter.GaussianBlur(1.5))
abdos = Image.new("RGBA", src.size, OMBRE + (0,))
abdos.putalpha(alpha.point(lambda a: int(a * 0.6)))
abdos = abdos.resize((TAILLE, TAILLE), Image.LANCZOS)

# 2. Cicatrice (dessinée en x4 puis réduite pour adoucir)
S = 4
cic = Image.new("RGBA", (TAILLE * S, TAILLE * S), (0, 0, 0, 0))
d = ImageDraw.Draw(cic)
a = (0.86 * TAILLE * S, 0.04 * TAILLE * S)  # épaule gauche de zoro
b = (0.16 * TAILLE * S, 0.97 * TAILLE * S)  # hanche droite
n = 60
longueur = math.dist(a, b)
nx, ny = (b[1] - a[1]) / longueur, -(b[0] - a[0]) / longueur  # normale


def point(t, decalage=0.0):
    # légère courbe et ondulation pour un trait vivant
    ondul = math.sin(t * math.pi) * 0.025 * longueur + math.sin(t * 9) * 0.004 * longueur
    return (a[0] + (b[0] - a[0]) * t + nx * (ondul + decalage), a[1] + (b[1] - a[1]) * t + ny * (ondul + decalage))


def bande(largeur_max, couleur):
    gauche, droite = [], []
    for i in range(n + 1):
        t = i / n
        w = largeur_max * (0.35 + 0.65 * math.sin(t * math.pi) ** 0.6)
        gauche.append(point(t, -w / 2))
        droite.append(point(t, w / 2))
    d.polygon(gauche + droite[::-1], fill=couleur)


bande(34 * S, CICATRICE_BORD + (150,))
bande(22 * S, CICATRICE + (235,))
bande(6 * S, (225, 160, 140, 200))  # reflet du bourrelet
# points de suture
for i in range(1, 15):
    t = i / 15
    cx, cy = point(t)
    dx, dy = nx * 20 * S, ny * 20 * S
    tx, ty = (b[0] - a[0]) / longueur * 3 * S, (b[1] - a[1]) / longueur * 3 * S
    d.line([(cx - dx - tx, cy - dy - ty), (cx + dx + tx, cy + dy + ty)], fill=SUTURE + (190,), width=5 * S)
cic = cic.resize((TAILLE, TAILLE), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8))

torse = Image.alpha_composite(abdos, cic)
torse.save(DOSSIER / "torse_zoro.png")
print("ok", torse.size)
