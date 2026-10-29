# Texture peinte de zoro (style B, rig R15). Lancer : uv run --with pillow assets/blender/zoro/texture_zoro.py
# Lit uv_zoro.json (rectangles des zones, en px sur 1024, origine en haut à gauche) écrit par Blender.
# Convention des zones : haut du rectangle = haut de la pièce ; gauche = côté droit du perso (vue de face).
import json, math, os
from PIL import Image, ImageDraw, ImageFilter

ICI = os.path.dirname(os.path.abspath(__file__))
LAYOUT = json.load(open(os.path.join(ICI, "uv_zoro.json")))["regions"]
SS = 2  # suréchantillonnage, réduit à la fin
TAILLE = 1024


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))


def ombre(c, a):
    return (c[0], c[1], c[2], a)


PEAU, PEAU_O, PEAU_C = hexc("E2B48C"), hexc("B98560"), hexc("F2CFA8")
TRAIT = hexc("5A3420")
CHEV, CHEV_O = hexc("4FA34A"), hexc("2F6B2A")
BANDANA = hexc("151515")
HARA, HARA_O = hexc("3E8B4A"), hexc("255A30")
MANT, MANT_O, MANT_C = hexc("1F5A3A"), hexc("123A24"), hexc("2E7A50")
ECH, ECH_O, ECH_C = hexc("8E1F2E"), hexc("5E1420"), hexc("B8394C")
PANT, PANT_C = hexc("1A1A1A"), hexc("343434")
BOTTE = hexc("0F0F0F")
OR, OR_O, OR_C = hexc("E8C33A"), hexc("A8821A"), hexc("FFF0A0")
CICA = hexc("7A2A22")
NOIR = hexc("0A0A0A")
BLANC_OEIL, IRIS = hexc("F4F1EA"), hexc("3A3A3A")
LAME = hexc("D8DDE2")

atlas = Image.new("RGBA", (TAILLE * SS, TAILLE * SS), hexc("808080"))


class Zone:
    """Canvas local d'une zone. Coordonnées en px de la zone (échelle 1024), multipliées par SS."""

    def __init__(self, nom):
        self.nom = nom
        x, y, w, h = LAYOUT[nom]
        self.x, self.y, self.w, self.h = x, y, w, h
        self.img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))

    def pts(self, p):
        return [(a * SS, b * SS) for a, b in p]

    def calque(self):
        return Image.new("RGBA", self.img.size, (0, 0, 0, 0))

    def fond(self, c):
        ImageDraw.Draw(self.img).rectangle([0, 0, self.img.size[0], self.img.size[1]], fill=c)

    def degrade_v(self, haut, bas, y0=0, y1=None):
        y1 = self.h if y1 is None else y1
        d = ImageDraw.Draw(self.img)
        for yy in range(int(y0 * SS), int(y1 * SS)):
            t = (yy - y0 * SS) / max((y1 - y0) * SS - 1, 1)
            d.line([(0, yy), (self.img.size[0], yy)], fill=mix(haut, bas, t))

    def ombre_bords(self, c, larg=14, cotes="lrtb", force=0.55):
        cal = self.calque()
        d = ImageDraw.Draw(cal)
        W, H = cal.size
        L = int(larg * SS)
        for i in range(L):
            col = ombre(c, int(255 * force * (1 - i / L) ** 2))
            if "l" in cotes:
                d.line([(i, 0), (i, H)], fill=col)
            if "r" in cotes:
                d.line([(W - 1 - i, 0), (W - 1 - i, H)], fill=col)
            if "t" in cotes:
                d.line([(0, i), (W, i)], fill=col)
            if "b" in cotes:
                d.line([(0, H - 1 - i), (W, H - 1 - i)], fill=col)
        self.img.alpha_composite(cal)

    def doux(self, dessin, flou=4):
        cal = self.calque()
        dessin(ImageDraw.Draw(cal))
        self.img.alpha_composite(cal.filter(ImageFilter.GaussianBlur(flou * SS)))

    def net(self, dessin):
        cal = self.calque()
        dessin(ImageDraw.Draw(cal))
        self.img.alpha_composite(cal)

    def ligne(self, d, p, c, w):
        d.line(self.pts(p), fill=c, width=max(1, int(w * SS)), joint="curve")

    def courbe(self, d, p0, p1, p2, c, w, n=16):
        pts = []
        for i in range(n + 1):
            t = i / n
            pts.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                        (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
        self.ligne(d, pts, c, w)

    def poser(self):
        atlas.alpha_composite(self.img, (self.x * SS, self.y * SS))


def zone(nom):
    return Zone(nom) if nom in LAYOUT else None


def peau(z, bords="lr", force=0.6):
    z.fond(PEAU)
    z.ombre_bords(PEAU_O, larg=max(z.w // 6, 6), cotes=bords, force=force)


# ---------------------------------------------------------------- torse (UpperTorso : z 2,7 -> 4,0)
def torse_avant():
    z = Zone("ut_front")
    peau(z, "lrt")
    z.doux(lambda d: d.ellipse(z.pts([(96, -30), (160, 18)]), fill=ombre(PEAU_O, 210)), 6)

    def volumes(d):
        d.ellipse(z.pts([(24, 84), (126, 118)]), fill=ombre(PEAU_O, 150))  # sous les pectoraux
        d.ellipse(z.pts([(130, 84), (232, 118)]), fill=ombre(PEAU_O, 150))
        d.rectangle(z.pts([(124, 30), (132, 168)]), fill=ombre(PEAU_O, 130))
        d.rectangle(z.pts([(86, 132), (170, 137)]), fill=ombre(PEAU_O, 110))
        d.ellipse(z.pts([(10, 30), (50, 170)]), fill=ombre(PEAU_O, 90))
        d.ellipse(z.pts([(206, 30), (246, 170)]), fill=ombre(PEAU_O, 90))

    z.doux(volumes, 5)
    z.doux(lambda d: (d.ellipse(z.pts([(48, 40), (106, 74)]), fill=ombre(PEAU_C, 120)),
                      d.ellipse(z.pts([(150, 40), (208, 74)]), fill=ombre(PEAU_C, 120))), 6)

    def traits(d):
        c = ombre(TRAIT, 230)
        z.courbe(d, (40, 22), (80, 30), (118, 18), c, 2.2)  # clavicules
        z.courbe(d, (138, 18), (176, 30), (216, 22), c, 2.2)
        z.courbe(d, (28, 62), (52, 108), (124, 102), c, 3)  # pectoraux
        z.courbe(d, (228, 62), (204, 108), (132, 102), c, 3)
        z.ligne(d, [(128, 36), (128, 100)], ombre(TRAIT, 150), 2)
        z.ligne(d, [(128, 108), (128, 168)], c, 2.6)  # abdominaux
        for yy in (130, 156):
            z.courbe(d, (90, yy + 2), (108, yy - 3), (125, yy), c, 2.2)
            z.courbe(d, (131, yy), (148, yy - 3), (166, yy + 2), c, 2.2)
        z.courbe(d, (86, 110), (80, 140), (86, 168), ombre(TRAIT, 190), 2.2)
        z.courbe(d, (170, 110), (176, 140), (170, 168), ombre(TRAIT, 190), 2.2)
        for k in range(3):  # dentelés
            yy = 112 + k * 16
            z.ligne(d, [(38, yy), (56, yy + 8)], ombre(TRAIT, 150), 2)
            z.ligne(d, [(218, yy), (200, yy + 8)], ombre(TRAIT, 150), 2)

    z.net(traits)
    # grande cicatrice : épaule gauche (droite de l'image) -> hanche droite (gauche de l'image)
    p0, p1 = (240, 6), (40, 168)
    z.doux(lambda d: z.ligne(d, [p0, p1], ombre(CICA, 150), 14), 3)
    z.net(lambda d: z.ligne(d, [p0, p1], CICA, 7))
    z.net(lambda d: z.ligne(d, [(p0[0] - 2, p0[1] + 1), (p1[0] - 2, p1[1] + 1)], hexc("A0483C"), 2.4))

    def suture(d):
        n = 11
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        lg = math.hypot(dx, dy)
        ux, uy = dx / lg, dy / lg
        px, py = -uy, ux
        for i in range(1, n):
            cx, cy = p0[0] + dx * i / n, p0[1] + dy * i / n
            a = 7
            z.ligne(d, [(cx - px * a - ux * 3, cy - py * a - uy * 3), (cx + px * a + ux * 3, cy + py * a + uy * 3)], NOIR, 2.2)
            z.ligne(d, [(cx - px * a + ux * 3, cy - py * a + uy * 3), (cx + px * a - ux * 3, cy + py * a - uy * 3)], NOIR, 2.2)

    z.net(suture)
    z.poser()


def torse_dos():
    z = Zone("ut_back")
    peau(z, "lrt")

    def volumes(d):
        d.rectangle(z.pts([(124, 6), (132, 168)]), fill=ombre(PEAU_O, 160))
        d.ellipse(z.pts([(30, 24), (110, 96)]), fill=ombre(PEAU_O, 50))
        d.ellipse(z.pts([(146, 24), (226, 96)]), fill=ombre(PEAU_O, 50))

    z.doux(volumes, 6)

    def traits(d):
        c = ombre(TRAIT, 200)
        z.ligne(d, [(128, 16), (128, 168)], c, 2.4)
        z.courbe(d, (60, 34), (40, 70), (70, 100), c, 2.4)  # omoplates
        z.courbe(d, (196, 34), (216, 70), (186, 100), c, 2.4)
        z.courbe(d, (30, 108), (70, 134), (106, 160), ombre(TRAIT, 160), 2)
        z.courbe(d, (226, 108), (186, 134), (150, 160), ombre(TRAIT, 160), 2)
        z.courbe(d, (100, 4), (128, 18), (156, 4), c, 2)

    z.net(traits)
    z.poser()


def torse_cote():
    z = Zone("ut_side")
    peau(z, "lrt")
    z.doux(lambda d: d.ellipse(z.pts([(30, 30), (100, 170)]), fill=ombre(PEAU_O, 80)), 6)
    z.net(lambda d: [z.ligne(d, [(40, 104 + k * 18), (78, 112 + k * 18)], ombre(TRAIT, 150), 2) for k in range(3)])
    z.poser()


def peau_unie(nom):
    z = zone(nom)
    if z:
        peau(z, "lrtb")
        z.poser()


def torse_haut():
    z = Zone("ut_top")
    peau(z, "lrtb")
    z.doux(lambda d: d.ellipse(z.pts([(92, 14), (164, 82)]), fill=ombre(PEAU_O, 220)), 8)
    z.poser()


# ---------------------------------------------------------------- bras (UpperArm z 3-4, LowerArm 2,3-3,12, Hand 2-2,36)
def bras_haut(face):
    z = Zone("ua_" + face)
    peau(z, "lr")
    z.ombre_bords(PEAU_O, larg=14, cotes="t", force=0.35)
    if face in ("front", "out"):
        z.doux(lambda d: d.ellipse(z.pts([(16, 6), (112, 70)]), fill=ombre(PEAU_C, 70)), 6)

    def traits(d):
        c = ombre(TRAIT, 210)
        if face in ("front", "out", "back"):
            z.courbe(d, (8, 70), (64, 88), (120, 66), c, 2.6)  # bas du deltoïde
        if face == "front":
            z.courbe(d, (30, 88), (24, 112), (34, 128), c, 2.2)  # biceps
            z.courbe(d, (98, 88), (104, 112), (94, 128), c, 2.2)
        if face == "back":
            z.courbe(d, (40, 90), (64, 112), (88, 90), c, 2.2)  # triceps
        if face == "out":
            z.courbe(d, (40, 92), (34, 112), (40, 128), ombre(TRAIT, 150), 2)

    z.net(traits)
    z.poser()


def bras_bas(face):
    z = Zone("la_" + face)
    peau(z, "lr")
    z.doux(lambda d: d.rectangle(z.pts([(0, 0), (128, 14)]), fill=ombre(PEAU_O, 150)), 4)  # pli du coude

    def traits(d):
        c = ombre(TRAIT, 190)
        if face == "front":
            z.courbe(d, (30, 18), (40, 60), (54, 100), c, 2)
            z.courbe(d, (96, 18), (90, 60), (80, 100), c, 2)
        if face == "out":
            z.courbe(d, (50, 20), (70, 60), (60, 100), ombre(TRAIT, 150), 2)
        if face == "back":
            z.ligne(d, [(64, 14), (64, 40)], ombre(TRAIT, 140), 2)

    z.net(traits)
    z.ombre_bords(PEAU_O, larg=10, cotes="b", force=0.5)  # poignet
    z.poser()


def main(face):
    z = Zone("hd_" + face)
    peau(z, "lr")
    z.ombre_bords(PEAU_O, larg=6, cotes="t", force=0.5)

    def traits(d):
        c = ombre(TRAIT, 220)
        if face == "front":  # doigts repliés
            for k in range(1, 4):
                z.ligne(d, [(k * 32, 14), (k * 32, 46)], c, 2)
            z.courbe(d, (6, 12), (64, 6), (122, 12), c, 2.2)
        if face == "in":  # pouce replié par-dessus
            d.rounded_rectangle(z.pts([(36, 8), (92, 30)]), radius=8 * SS, fill=PEAU_C, outline=c, width=2 * SS)
        if face == "back":  # jointures
            for k in range(1, 4):
                z.ligne(d, [(k * 32 - 6, 12), (k * 32 + 6, 12)], ombre(TRAIT, 170), 2.4)

    z.net(traits)
    z.poser()


# ---------------------------------------------------------------- jambes (UpperLeg z 1,15-2, LowerLeg 0,35-1,25, Foot 0-0,42)
def pantalon(z):
    z.fond(PANT)
    z.ombre_bords(hexc("000000"), larg=14, cotes="lr", force=0.55)


def cuisse(face):
    z = Zone("ul_" + face)
    pantalon(z)

    def plis(d):
        c = ombre(PANT_C, 255)
        z.courbe(d, (16, 20), (40, 50), (30, 96), c, 2)
        z.courbe(d, (110, 30), (92, 60), (104, 100), c, 2)
        if face == "front":
            z.ligne(d, [(64, 0), (64, 24)], hexc("2A2A2A"), 1.6)
        for x in range(4, 128, 9):  # couture
            z.ligne(d, [(x, 104), (x + 5, 104)], hexc("2C2C2C"), 1.4)

    z.net(plis)
    z.poser()


def tibia(face):
    z = Zone("ll_" + face)
    pantalon(z)

    def plis(d):
        c = ombre(PANT_C, 255)
        for yy in (12, 22, 32):  # plis aux genoux
            z.courbe(d, (14, yy), (64, yy + 8), (114, yy - 2), c, 2)
        # botte : z < 0,82 -> y > 62
        d.rectangle(z.pts([(0, 62), (128, 116)]), fill=BOTTE)
        z.ligne(d, [(0, 62), (128, 62)], hexc("2C2C2C"), 2)
        if face == "front":
            for k in range(3):  # lacets croisés
                yy = 70 + k * 14
                z.ligne(d, [(46, yy), (82, yy + 11)], hexc("6A6A6A"), 2)
                z.ligne(d, [(82, yy), (46, yy + 11)], hexc("6A6A6A"), 2)
                d.ellipse(z.pts([(43, yy - 2), (49, yy + 4)]), fill=OR_O)
                d.ellipse(z.pts([(79, yy - 2), (85, yy + 4)]), fill=OR_O)
        if face == "out":
            z.courbe(d, (30, 70), (60, 90), (40, 112), hexc("262626"), 2)

    z.net(plis)
    z.poser()


def pied(face):
    z = Zone("ft_" + face)
    z.fond(BOTTE)
    z.degrade_v(hexc("242424"), BOTTE, 0, z.h)

    def det(d):
        z.ligne(d, [(0, z.h - 8), (z.w, z.h - 8)], hexc("3A3A3A"), 2)  # trépointe
        if face == "front":
            z.courbe(d, (20, 8), (64, 2), (108, 8), hexc("3A3A3A"), 2)
        if face == "out":
            d.rectangle(z.pts([(90, 14), (112, 28)]), outline=OR, width=int(2.4 * SS))  # boucle
            z.ligne(d, [(30, 21), (90, 21)], hexc("2E2E2E"), 4)

    z.net(det)
    z.poser()


def dessus_pied():
    z = Zone("ft_top")
    z.degrade_v(hexc("2A2A2A"), BOTTE, 0, z.h)
    z.poser()


def sangle():
    z = Zone("strap")  # sangle verticale avec 2 boucles dorées (anneaux en D)
    z.fond(hexc("101010"))
    z.ombre_bords(hexc("2E2E2E"), larg=4, cotes="lr", force=0.9)

    def boucles(d):
        for yy in (14, 58):
            d.rounded_rectangle(z.pts([(5, yy), (27, yy + 22)]), radius=7 * SS, outline=OR, width=int(3 * SS))
            z.ligne(d, [(8, yy + 3), (24, yy + 3)], OR_C, 1.4)
            z.ligne(d, [(16, yy + 2), (16, yy + 20)], OR_O, 2)

    z.net(boucles)
    z.poser()


def bande(nom, haut, bas, pointilles=None):
    z = zone(nom)
    if not z:
        return
    z.degrade_v(haut, bas, 0, z.h)
    if pointilles:
        z.net(lambda d: [z.ligne(d, [(x, z.h / 2), (x + 4, z.h / 2)], pointilles, 1.4) for x in range(0, z.w, 8)])
    z.poser()


# ---------------------------------------------------------------- tête
def visage():
    z = Zone("face")
    z.fond(PEAU)
    z.ombre_bords(PEAU_O, larg=44, cotes="lr", force=0.75)
    z.ombre_bords(PEAU_O, larg=26, cotes="b", force=0.5)
    # ombre portée du bandana sur le front et les yeux
    z.doux(lambda d: d.rectangle(z.pts([(0, 50), (256, 112)]), fill=ombre(hexc("5A3420"), 215)), 8)
    z.doux(lambda d: (d.polygon(z.pts([(58, 158), (98, 146), (102, 156), (64, 174)]), fill=ombre(PEAU_O, 80)),
                      d.polygon(z.pts([(198, 158), (158, 146), (154, 156), (192, 174)]), fill=ombre(PEAU_O, 80))), 7)

    def favoris(d):
        d.polygon(z.pts([(0, 70), (34, 72), (30, 118), (18, 150), (0, 140)]), fill=CHEV_O)
        d.polygon(z.pts([(256, 70), (222, 72), (226, 118), (238, 150), (256, 140)]), fill=CHEV_O)
        for xx in (8, 18, 26):
            z.ligne(d, [(xx, 76), (xx - 2, 130)], ombre(CHEV, 200), 2)
            z.ligne(d, [(256 - xx, 76), (258 - xx, 130)], ombre(CHEV, 200), 2)

    z.net(favoris)

    def traits(d):
        d.polygon(z.pts([(66, 98), (82, 92), (118, 106), (120, 114), (112, 115), (70, 104)]), fill=NOIR)
        d.polygon(z.pts([(190, 98), (174, 92), (138, 106), (136, 114), (144, 115), (186, 104)]), fill=NOIR)
        z.ligne(d, [(124, 104), (126, 118)], ombre(TRAIT, 200), 2)
        z.ligne(d, [(132, 104), (130, 118)], ombre(TRAIT, 200), 2)
        # œil droit (gauche de l'image) : petit, dur
        d.polygon(z.pts([(80, 124), (92, 117), (112, 118), (114, 124), (104, 129), (86, 129)]), fill=BLANC_OEIL)
        d.ellipse(z.pts([(95, 117), (107, 129)]), fill=IRIS)
        d.ellipse(z.pts([(98, 120), (104, 126)]), fill=NOIR)
        d.ellipse(z.pts([(99, 119), (102, 122)]), fill=(255, 255, 255, 255))
        z.ligne(d, [(78, 124), (90, 116), (114, 117), (118, 121)], NOIR, 3.6)
        z.ligne(d, [(86, 130), (104, 130)], ombre(TRAIT, 200), 1.6)
        # œil gauche (droite de l'image) : fermé
        z.courbe(d, (140, 124), (156, 129), (174, 123), NOIR, 3.2)
        z.courbe(d, (144, 118), (156, 116), (170, 117), ombre(TRAIT, 200), 1.8)
        # nez, bouche, mâchoire
        z.courbe(d, (124, 132), (120, 150), (126, 156), ombre(TRAIT, 170), 2)
        z.ligne(d, [(122, 157), (134, 157)], ombre(TRAIT, 220), 2.2)
        z.ligne(d, [(108, 182), (114, 180), (142, 180), (148, 183)], hexc("4A2416"), 3)
        z.ligne(d, [(116, 189), (140, 189)], ombre(PEAU_O, 200), 2)
        z.courbe(d, (64, 186), (92, 222), (128, 226), ombre(TRAIT, 110), 2)
        z.courbe(d, (192, 186), (164, 222), (128, 226), ombre(TRAIT, 110), 2)

    z.net(traits)
    z.doux(lambda d: z.ligne(d, [(157, 88), (157, 168)], ombre(CICA, 150), 9), 2)
    z.net(lambda d: z.ligne(d, [(157, 90), (157, 166)], CICA, 4))
    z.net(lambda d: z.ligne(d, [(156, 92), (156, 164)], hexc("A0483C"), 1.4))
    z.poser()


def tete_cotes():
    z = Zone("headside")
    z.fond(PEAU)
    z.degrade_v(PEAU, PEAU_O, 70, 128)

    def oreilles(d):
        for cx in (0.27 * 256, 0.73 * 256):
            d.ellipse(z.pts([(cx - 10, 44), (cx + 10, 88)]), fill=PEAU_O)
            d.ellipse(z.pts([(cx - 5, 52), (cx + 5, 80)]), fill=ombre(TRAIT, 200))

    z.net(oreilles)
    z.net(lambda d: d.rectangle(z.pts([(70, 0), (186, 46)]), fill=CHEV_O))
    z.poser()


def bandana():
    # u = tour de tête (0 = devant, 0,5 = nuque, où est le nœud) ; haut = sommet
    z = Zone("bandana")
    z.degrade_v(hexc("2B2B2B"), BANDANA, 0, z.h)
    W, H = z.w, z.h
    # reflet doux sur le dessus avant
    z.doux(lambda d: (d.ellipse(z.pts([(-60, -10), (60, 50)]), fill=ombre(hexc("4A4A4A"), 150)),
                      d.ellipse(z.pts([(W - 60, -10), (W + 60, 50)]), fill=ombre(hexc("4A4A4A"), 150))), 10)

    def plis(d):
        # plis qui convergent vers le nœud (u = 0,5, en bas)
        cx = W / 2
        for k in range(-5, 6):
            if k == 0:
                continue
            x0 = cx + k * W / 12
            z.courbe(d, (x0, 10), (cx + k * W / 20, H * 0.5), (cx + k * 6, H - 10), ombre(hexc("050505"), 170), 2.4)
            z.courbe(d, (x0 + 5, 14), (cx + k * W / 20 + 5, H * 0.5), (cx + k * 6 + 4, H - 14), ombre(hexc("3A3A3A"), 110), 1.6)
        z.ligne(d, [(0, H - 3), (W, H - 3)], hexc("050505"), 4)

    z.doux(plis, 1)
    z.poser()
    bande("bandana_hem", hexc("202020"), hexc("050505"))
    z = Zone("bandana_knot")
    z.degrade_v(hexc("2E2E2E"), hexc("0C0C0C"), 0, z.h)
    z.net(lambda d: [z.courbe(d, (x, 0), (x + 10, 32), (x - 4, 64), ombre(hexc("000000"), 200), 2) for x in range(8, 128, 22)])
    z.poser()


def cheveux():
    z = Zone("hair")
    z.degrade_v(CHEV, CHEV_O, 0, 64)

    def meches(d):
        for x in range(4, 256, 12):
            z.ligne(d, [(x, 64), (x + 4, 30), (x + 1, 4)], ombre(CHEV_O, 220), 2)
            z.ligne(d, [(x + 6, 50), (x + 8, 10)], ombre(hexc("8FD07A"), 200), 1.6)

    z.net(meches)
    z.poser()


# ---------------------------------------------------------------- tenue
def haramaki():
    z = Zone("haramaki")  # côtes horizontales du tricot
    z.degrade_v(hexc("4A9A56"), HARA, 0, z.h)

    def cotes(d):
        for k in range(10):
            yy = 4 + k * 6
            z.ligne(d, [(0, yy), (z.w, yy)], HARA_O, 2.6)
            z.ligne(d, [(0, yy + 2.4), (z.w, yy + 2.4)], ombre(hexc("6CBA74"), 170), 1.2)
        for x in range(0, z.w, 6):  # mailles
            z.ligne(d, [(x, 0), (x, z.h)], ombre(HARA_O, 50), 1)
        z.ligne(d, [(0, 1), (z.w, 1)], hexc("163A1E"), 3)
        z.ligne(d, [(0, z.h - 1), (z.w, z.h - 1)], hexc("163A1E"), 3)

    z.net(cotes)
    z.ombre_bords(hexc("163A1E"), larg=8, cotes="b", force=0.5)
    z.poser()
    bande("haramaki_rib", hexc("2C6A38"), hexc("1C4626"))


def manteau():
    z = Zone("coat")  # u = tour (bord avant droit -> dos -> bord avant gauche), haut = taille
    W, H = z.w, z.h
    z.degrade_v(MANT_O, MANT, 0, 50)
    z.degrade_v(MANT, hexc("1A4E32"), 50, H)
    n = 36
    lw = W / n

    def plis(d):
        for k in range(n):
            x = k * lw
            ph = k % 4
            if ph == 3:
                d.polygon(z.pts([(x - 2, 20), (x + lw + 2, 20), (x + lw + 6, H), (x - 6, H)]), fill=ombre(MANT_O, 220))
            if ph == 1:
                d.polygon(z.pts([(x + 2, 24), (x + lw - 2, 24), (x + lw, H), (x, H)]), fill=ombre(MANT_C, 170))

    z.doux(plis, 5)

    def traits(d):
        for k in range(n):
            if k % 4 == 3:
                x = k * lw + lw / 2
                z.ligne(d, [(x, H), (x - 3, H * 0.5), (x + 2, 20)], ombre(hexc("0B2817"), 230), 2.4)
            if k % 4 == 1:
                x = k * lw + lw / 2
                z.ligne(d, [(x, H - 10), (x + 2, 40)], ombre(hexc("4A9A6C"), 150), 1.6)
        # plis de tension partant de la taille
        for k in range(0, n, 2):
            x = k * lw
            z.courbe(d, (x, 0), (x + 6, 14), (x + 2, 30), ombre(hexc("0B2817"), 200), 2)
        z.ligne(d, [(0, H - 8), (W, H - 8)], hexc("0E2E1C"), 6)  # ourlet
        for x in range(0, W, 9):
            z.ligne(d, [(x, H - 16), (x + 5, H - 16)], hexc("4C9A6C"), 1.6)  # piqûre
        d.rectangle(z.pts([(0, 0), (5, H)]), fill=hexc("0E2E1C"))  # liseré des bords avant
        d.rectangle(z.pts([(W - 5, 0), (W, H)]), fill=hexc("0E2E1C"))

    z.net(traits)
    z.poser()
    bande("coat_in", MANT_O, hexc("0C2618"))
    bande("coat_hem", hexc("0E2E1C"), hexc("0E2E1C"))
    z = Zone("coat_rev")
    z.fond(hexc("2A6C47"))
    z.ombre_bords(MANT_O, larg=20, cotes="lrtb", force=0.7)
    z.net(lambda d: [z.ligne(d, [(x, 10), (x + 4, 10)], hexc("5CAA7C"), 1.6) for x in range(6, 128, 9)])
    z.poser()
    z = Zone("coat_roll")  # tissu bouffant noué à la taille
    z.degrade_v(MANT_C, MANT_O, 0, z.h)

    def roul(d):
        for k in range(0, z.w, 18):
            z.courbe(d, (k, z.h), (k + 16, z.h * 0.5), (k + 4, 0), ombre(hexc("0B2817"), 230), 2.6)
            z.courbe(d, (k + 8, z.h - 4), (k + 20, z.h * 0.5), (k + 12, 6), ombre(hexc("5AAA7C"), 170), 1.8)

    z.doux(roul, 1)
    z.poser()


def echarpe():
    z = Zone("scarf")
    z.degrade_v(ECH_C, ECH_O, 0, z.h)

    def plis(d):
        for k in range(0, z.w, 16):
            z.courbe(d, (k, 0), (k + 12, z.h * 0.5), (k + 4, z.h), ombre(hexc("3E0C14"), 220), 2.4)
            z.courbe(d, (k + 7, 6), (k + 16, z.h * 0.5), (k + 10, z.h - 6), ombre(hexc("D25A6C"), 160), 1.6)

    z.net(plis)
    z.poser()
    z = Zone("scarf_knot")
    z.degrade_v(ECH_C, ECH_O, 0, z.h)
    z.net(lambda d: [z.courbe(d, (x, 0), (x + 14, 32), (x, 64), ombre(hexc("3E0C14"), 230), 2.4) for x in (10, 30, 50)])
    z.poser()
    z = Zone("scarf_pan")  # u = largeur du pan, haut = attache
    z.degrade_v(ECH, ECH_O, 0, z.h)

    def pan(d):
        W, H = z.w, z.h
        for x, s in ((W * 0.25, 1), (W * 0.5, -1), (W * 0.75, 1)):
            z.courbe(d, (x, 0), (x + 8 * s, H * 0.5), (x - 4 * s, H - 14), ombre(hexc("3E0C14"), 220), 2.6)
            z.courbe(d, (x + 10, 4), (x + 18 * s, H * 0.5), (x + 6, H - 18), ombre(hexc("D25A6C"), 150), 1.8)
        z.ligne(d, [(0, H - 12), (W, H - 12)], hexc("3E0C14"), 2)
        for x in range(2, W, 5):  # franges
            z.ligne(d, [(x, H - 10), (x + 1, H)], hexc("4A1018"), 1.6)

    z.net(pan)
    z.poser()


def fourreau(nom, c, clair):
    z = Zone(nom)
    z.degrade_v(clair, c, 0, z.h)
    z.net(lambda d: (z.ligne(d, [(0, 5), (z.w, 5)], ombre(hexc("FFFFFF"), 90), 2),
                     z.ligne(d, [(0, z.h - 6), (z.w, z.h - 6)], ombre(hexc("000000"), 120), 2)))
    z.poser()


def poignee(nom, cord, losange):
    z = Zone(nom)
    z.fond(cord)

    def tresse(d):
        for x in range(-16, 80, 16):
            for y in range(-8, 40, 16):
                d.polygon(z.pts([(x + 8, y + 2), (x + 14, y + 8), (x + 8, y + 14), (x + 2, y + 8)]), fill=losange)
        for x in range(-32, 96, 16):
            z.ligne(d, [(x, 0), (x + 32, 32)], ombre(hexc("000000"), 90), 1.2)
            z.ligne(d, [(x + 32, 0), (x, 32)], ombre(hexc("000000"), 90), 1.2)

    z.net(tresse)
    z.poser()


def lame():
    z = Zone("blade")
    z.degrade_v(hexc("F4F7FA"), LAME, 0, z.h)
    z.net(lambda d: (z.ligne(d, [(0, 20), (z.w, 20)], hexc("FFFFFF"), 3),
                     z.ligne(d, [(0, 44), (z.w, 44)], hexc("A9B2BC"), 2)))
    z.poser()


def or_():
    for nom in ("gold", "gold_ring"):
        z = Zone(nom)
        z.degrade_v(hexc("F6DD70"), OR_O, 0, z.h)
        z.net(lambda d: z.ligne(d, [(0, 8), (z.w, 8)], OR_C, 2))
        z.poser()


def unie(nom, c):
    z = zone(nom)
    if z:
        z.fond(c)
        z.poser()


# ---------------------------------------------------------------- tout
torse_avant()
torse_dos()
torse_cote()
torse_haut()
peau_unie("ut_bottom")
for nom in ("lt_front", "lt_back", "lt_side", "lt_top", "lt_bottom"):
    unie(nom, HARA)
for face in ("front", "back", "out", "in"):
    bras_haut(face)
    bras_bas(face)
    main(face)
    cuisse(face)
    tibia(face)
    pied(face)
peau_unie("ua_top")
for nom in ("ua_bottom", "la_bottom", "hd_bottom"):
    peau_unie(nom)
for nom in ("ul_top", "ul_bottom", "ll_bottom"):
    unie(nom, PANT)
dessus_pied()
unie("ft_bottom", hexc("262626"))
bande("sole", hexc("3A3A3A"), hexc("1E1E1E"))
sangle()
bande("knee_wrap", hexc("2A2A2A"), hexc("111111"), hexc("4A4A4A"))
bande("boot_cuff", hexc("262626"), BOTTE, hexc("4A4A4A"))
visage()
tete_cotes()
bandana()
cheveux()
haramaki()
manteau()
echarpe()
fourreau("sheath_white", hexc("EDEDED"), hexc("FFFFFF"))
fourreau("sheath_red", hexc("5E1A22"), hexc("8A2A34"))
fourreau("sheath_black", hexc("151515"), hexc("3A3A3A"))
poignee("grip_white", hexc("F2F2F2"), hexc("2A2A2A"))
poignee("grip_red", hexc("8E1F2E"), hexc("EEE6D2"))
poignee("grip_black", hexc("111111"), hexc("EEE6D2"))
lame()
or_()
unie("hrp", hexc("808080"))

out = atlas.resize((TAILLE, TAILLE), Image.LANCZOS).convert("RGB")
out.save(os.path.join(ICI, "Texture_zoro.png"))
print("Texture_zoro.png écrite")
