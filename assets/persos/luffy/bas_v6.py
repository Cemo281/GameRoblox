"""Ceinture (echarpe jaune nouee) et short en jean de luffy, v6 : meme methode et meme style anime que chemise_v6.py.

A lancer DANS Blender (MCP Blender), chemise_rig15.blend ouvert (la chemise v6 deja construite : elle fait de l'ombre) :
	exec(open(r"<depot>/assets/persos/luffy/bas_v6.py", encoding="utf-8").read())
	construire_bas()   # Ceinture (suit LowerTorso), Short_JambeD / Short_JambeG (suivent les UpperLeg)
	cuire_bas()        # cuisson_bas/ao.png et lumiere.png
	peindre_bas()      # tex_bas_v6_anime.png

Reprend les outils de chemise_v6.py (contours, bords effiloches, plis, cuisson, paliers anime).
Reperes : monde Blender du rig, Z en haut, avant du perso = +Y, gauche du perso = -X, studs.
"""

import math
import random
from pathlib import Path

exec(open(Path(r"C:\Users\alice\Documents\GameRoblox\assets\persos\luffy") / "chemise_v6.py", encoding="utf-8").read())  # noqa: S102

TEX_BAS = DOSSIER / "tex_bas_v6_anime.png"
CUISSON_BAS = DOSSIER / "cuisson_bas"
ZONES_BAS = {
	"bande": (0, 0, 2048, 384), "noeud": (0, 384, 512, 256), "pan1": (512, 384, 384, 640), "pan2": (896, 384, 384, 640),
	"jambe_d": (0, 1024, 1024, 640), "jambe_g": (1024, 1024, 1024, 640), "revers_d": (0, 1664, 1024, 192), "revers_g": (1024, 1664, 1024, 192),
}
PIECES_BAS = {"Ceinture": "LowerTorso", "Short_JambeD": "RightUpperLeg", "Short_JambeG": "LeftUpperLeg"}

# echarpe : serree sur le LowerTorso (0,996 x 0,502, z 2,19 -> 2,59), sous la chemise (interieur de la chemise a ~1,012 / 0,525) :
# presque pas de renflement en volume, les plis sont peints ; noeud et pans dans l'ouverture du devant
E_Z0, E_Z1 = 2.19, 2.59
E_W, E_D, E_R = 1.006, 0.512, 0.12
E_RELIEF = 0.12  # part du relief d'origine (0,03 + plis) gardee : reste sous l'interieur de la chemise
NOEUD = Vector((-0.17, E_D + 0.1, 2.4))
# short : du dessous de l'echarpe au-dessus du genou (z monde) ; le haut se resserre sous la chemise et l'echarpe
S_HAUT, S_BAS = 2.4, 1.1  # bas juste au-dessus du genou (articulation a 1,27 : le revers la couvre)
S_RESSERRE = (2.12, 2.26)
EP_BAS = 0.03

PALIERS = {
	"jaune": [(0.0, (150, 92, 10)), (0.42, (208, 148, 18)), (0.72, (246, 198, 40)), (1.04, (255, 232, 124))],
	"bleu": [(0.0, (20, 36, 90)), (0.42, (34, 62, 134)), (0.72, (50, 94, 182)), (1.04, (98, 146, 222))],
	"blanc": [(0.0, (122, 132, 166)), (0.42, (182, 190, 214)), (0.72, (234, 237, 246)), (1.04, (255, 255, 255))],
}
PASTILLES = {"Ceinture": ((420, 1000, 1300, 1640), (110, 66, 8)), "Short": ((420, 1000, 1700, 2040), (14, 26, 66))}  # zone libre
PALETTE_ZONE = {"bande": "jaune", "noeud": "jaune", "pan1": "jaune", "pan2": "jaune", "jambe_d": "bleu", "jambe_g": "bleu", "revers_d": "blanc", "revers_g": "blanc"}


def uvb(zone, a, b):
	x0, y0, w, h = ZONES_BAS[zone]
	return ((x0 + a * w) / T, 1 - (y0 + (1 - b) * h) / T)


# --- echarpe ---------------------------------------------------------------------------------------------------------
def bande_echarpe():
	"""Bande roulee autour de la taille : renflement, plis en biais, bords un peu ondules."""
	nu = 140
	vs = [0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0]
	L = chemin(1.0, E_W, E_D, E_R)[4]
	pts, uvs = [], []
	for i in range(nu):
		u = i / nu
		s = u * L
		x, y, nx, ny, _ = chemin(u, E_W, E_D, E_R)
		col_p, col_uv = [], []
		for v in vs:
			d = 0.03 * math.sin(math.pi * v) + 0.012 * math.sin(2 * math.pi * (2 * v + s / 0.7)) + 0.008 * math.sin(2 * math.pi * (3 * v - s / 0.45))
			d *= E_RELIEF
			z = E_Z0 + (E_Z1 - E_Z0) * v
			if v in (0, 1.0):
				z += 0.01 * math.sin(2 * math.pi * s / 0.55 + (0.7 if v else 2.1))
			col_p.append(Vector((x + nx * d, y + ny * d, z)))
			col_uv.append(uvb("bande", u, v))
		pts.append(col_p)
		uvs.append(col_uv)
	return pts, uvs


def noeud(bm, uvl):
	"""Noeud bossele sur la hanche gauche (sphere deformee, UV spheriques)."""
	r = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
	vs = r["verts"]
	for v in vs:
		p = v.co.copy()
		th, ph = math.atan2(p.y, p.x), math.acos(max(-1.0, min(1.0, p.z)))
		k = 1 + 0.13 * math.sin(3 * th + 0.4) * math.sin(ph) + 0.08 * math.cos(2 * ph + th)
		v.co = NOEUD + Vector((p.x * 0.21, p.y * 0.13, p.z * 0.17)) * k
	faces = list({f for v in vs for f in v.link_faces})
	for f in faces:
		us = []
		for l in f.loops:
			p = (l.vert.co - NOEUD)
			th = math.atan2(p.y / 0.13, p.x / 0.21)
			ph = math.acos(max(-1.0, min(1.0, p.z / 0.17 / max(1e-6, (p.x / 0.21) ** 2 + (p.y / 0.13) ** 2 + (p.z / 0.17) ** 2) ** 0.5)))
			us.append(((th / (2 * math.pi)) % 1.0, 1 - ph / math.pi))
		if max(a for a, _ in us) - min(a for a, _ in us) > 0.5:
			us = [(a + 1 if a < 0.5 else a, b) for a, b in us]
		for l, (a, b) in zip(f.loops, us):
			x0, y0, w, h = ZONES_BAS["noeud"]
			l[uvl].uv = ((x0 + a * 0.93 * w) / T, 1 - (y0 + (1 - b) * h) / T)  # 0,93 : la couture (a jusqu'a 1,07) reste dans la zone
	return faces


def pan(bm, uvl, zone, depart, fin, w0, w1, torsion, graine):
	"""Pan qui pend du noeud : bande plissee, legere torsion, bout effiloche."""
	rng = random.Random(graine)
	nr, nc = 16, 7
	pointes = ondes(1.0, graine, (0.18, 0.4), (0.04, 0.1), False, n_dech=1, larg_d=(0.12, 0.2), prof_d=(0.1, 0.16))
	pts, uvs = [], []
	for j in range(nc):
		c = j / (nc - 1)
		col_p, col_uv = [], []
		for k in range(nr):
			t = k / (nr - 1)
			p = depart.lerp(fin, t)
			p.x += 0.05 * math.sin(math.pi * t)
			w = w0 + (w1 - w0) * t
			tau = torsion * t
			a = Vector((math.cos(tau), math.sin(tau), 0))
			q = p + a * (c - 0.5) * w
			q.y += 0.022 * math.sin(2 * math.pi * 1.5 * c + 2 * t) + 0.01 * rng.uniform(-1, 1) * t
			if k == nr - 1:
				q.z -= 0.12 - pointes(c)  # bout effiloche : pointes vers le bas, creux entre elles
			col_p.append(q)
			col_uv.append(uvb(zone, c, 1 - t))
		pts.append(col_p)
		uvs.append(col_uv)
	_, faces = grille(bm, uvl, pts, uvs, False)
	for f in faces:
		f.normal_update()
		if f.normal.y < 0:
			f.normal_flip()
	return faces


# --- short -----------------------------------------------------------------------------------------------------------
def jambe(o, zone_j, zone_r, graine):
	"""Jambe du short (tube ouvert, evase, plis) et revers blanc duveteux (anneau bombe aux bords en touffes)."""
	c, (ex, ey, ez), (ax, ay, az) = repere_bras(o)
	zc = (o.matrix_world @ c).z
	zb, zt = S_BAS - zc, S_HAUT - zc

	def section(z):
		f = lisse(zt, zb, z)
		marge = 0.07 * (1 - lisse(S_RESSERRE[0], S_RESSERRE[1], zc + z))  # haut resserre : sous la chemise et l'echarpe
		return ax + marge + 0.04 * f, ay + marge + 0.035 * f, 0.17

	L = chemin(1.0, *section(zb))[4]
	pl = plis(graine, 9, L, (0.012, 0.026), (0.06, 0.12), (0.4, 0.9))

	def local(x, y, z):
		return c + ex * x + ey * y + ez * z

	nu = 112
	zs = rangs_cote(zb, zt, [0, 0.05, 0.1, 0.16, 0.24])
	v_max = zt - zb
	pts, uvs = [], []
	for i in range(nu):
		u = i / nu
		s = u * L
		col_p, col_uv = [], []
		for z in zs:
			hx, hy, r = section(z)
			x, y, nx, ny, _ = chemin(u, hx, hy, r)
			d = relief(pl, s, z - zb, periode=L)
			col_p.append(local(x + nx * d, y + ny * d, z))
			col_uv.append(uvb(zone_j, u, (z - zb) / v_max))
		pts.append(col_p)
		uvs.append(col_uv)
	# revers duveteux
	o_haut = ondes(L, graine + 3, (0.07, 0.16), (0.015, 0.035), True)
	o_bas = ondes(L, graine + 4, (0.07, 0.16), (0.02, 0.045), True)
	hx0, hy0, r0 = section(zb)
	ts = [0, 0.12, 0.3, 0.5, 0.7, 0.88, 1.0]
	rpts, ruvs = [], []
	rng = random.Random(graine + 9)
	bosses = [(rng.uniform(0, L), rng.uniform(0.04, 0.09), rng.uniform(0.008, 0.02)) for _ in range(14)]
	for i in range(nu):
		u = i / nu
		s = u * L
		col_p, col_uv = [], []
		for t in ts:
			bombe = 0.045 + 0.045 * math.sin(math.pi * t)
			for s0, w, a in bosses:
				ds = (s - s0 + L / 2) % L - L / 2
				bombe += a * math.exp(-((ds / w) ** 2)) * math.sin(math.pi * t)
			x, y, nx, ny, _ = chemin(u, hx0 + bombe, hy0 + bombe, r0 + 0.02)
			z = zb - 0.07 + 0.25 * t
			if t == 0:
				z -= o_bas(s)
			elif t == 1.0:
				z += o_haut(s)
			col_p.append(local(x, y, z))
			col_uv.append(uvb(zone_r, u, t))
		rpts.append(col_p)
		ruvs.append(col_uv)
	return pts, uvs, rpts, ruvs, {"L": L, "plis": pl, "v_max": v_max}


# --- construction ----------------------------------------------------------------------------------------------------
def construire_bas():
	global bm_courant
	img = bpy.data.images.get(TEX_BAS.name)
	if img is None and TEX_BAS.exists():
		img = bpy.data.images.load(str(TEX_BAS))
	mat = materiau("Mat_Bas_v6", (0.8, 0.6, 0.1, 1), img)
	int_jaune = materiau("Mat_Ceinture_Int", (0.25, 0.14, 0.02, 1))
	int_bleu = materiau("Mat_Short_Int", (0.03, 0.05, 0.14, 1))
	objets = []
	# ceinture (monde puis local de LowerTorso)
	lt = bpy.data.objects["LowerTorso"]
	bm = bmesh.new()
	bm_courant = bm
	uvl = bm.loops.layers.uv.new("UVMap")
	pts, uvs = bande_echarpe()
	_, faces = grille(bm, uvl, pts, uvs, True)
	x0, w = ZONES_BAS["bande"][0] / T, ZONES_BAS["bande"][2] / T
	for f in faces:  # couture des UV de la bande fermee
		us = [l[uvl].uv.x for l in f.loops]
		if max(us) - min(us) > w / 2:
			for l in f.loops:
				if l[uvl].uv.x < x0 + w / 2:
					l[uvl].uv.x += w
	orienter(faces, lambda c: Vector((0, 0, c.z)))
	fn = noeud(bm, uvl)
	orienter(fn, lambda c: NOEUD)
	pan(bm, uvl, "pan1", NOEUD + Vector((-0.02, 0.04, -0.05)), Vector((-0.5, E_D + 0.12, 1.42)), 0.26, 0.22, 0.35, 61)
	pan(bm, uvl, "pan2", NOEUD + Vector((0.07, 0.07, -0.06)), Vector((-0.08, E_D + 0.13, 1.66)), 0.22, 0.17, -0.3, 67)
	bm.transform(lt.matrix_world.inverted())
	bm.normal_update()
	objets.append((objet_piece("Ceinture", "LowerTorso", bm), int_jaune))
	# jambes (local des UpperLeg)
	for nom, piece, zj, zr, graine in (("Short_JambeD", "RightUpperLeg", "jambe_d", "revers_d", 71), ("Short_JambeG", "LeftUpperLeg", "jambe_g", "revers_g", 83)):
		o = bpy.data.objects[piece]
		bm = bmesh.new()
		bm_courant = bm
		uvl = bm.loops.layers.uv.new("UVMap")
		pts, uvs, rpts, ruvs, _ = jambe(o, zj, zr, graine)
		for p_, u_, zone in ((pts, uvs, zj), (rpts, ruvs, zr)):
			_, faces = grille(bm, uvl, p_, u_, True)
			x0, w = ZONES_BAS[zone][0] / T, ZONES_BAS[zone][2] / T
			for f in faces:
				us = [l[uvl].uv.x for l in f.loops]
				if max(us) - min(us) > w / 2:
					for l in f.loops:
						if l[uvl].uv.x < x0 + w / 2:
							l[uvl].uv.x += w
			ctr = sum((v.co for f in faces for v in f.verts), Vector()) / sum(len(f.verts) for f in faces)
			axe = repere_bras(o)[1][2]
			orienter(faces, lambda q, ctr=ctr, axe=axe: ctr + axe * (q - ctr).dot(axe))
		bm.normal_update()
		objets.append((objet_piece(nom, piece, bm), int_bleu))
	res = []
	for o, m_int in objets:
		o.data.materials.clear()
		o.data.materials.append(mat)
		o.data.materials.append(m_int)
		for p in o.data.polygons:
			p.material_index = 0
			p.use_smooth = True
		m = o.modifiers.new("Epaisseur", "SOLIDIFY")
		m.thickness = EP_BAS
		m.offset = -1
		m.use_rim = True
		m.use_even_offset = True
		m.use_quality_normals = True
		m.material_offset = 1
		m.material_offset_rim = 1
		ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
		print(o.name, [round(d, 3) for d in o.dimensions], sum(len(p.vertices) - 2 for p in ev.data.polygons), "triangles avec epaisseur")
		res.append(o)
	return res


def cuire_bas(echantillons=32):
	cuire_objets([bpy.data.objects[n] for n in PIECES_BAS], "Mat_Bas_v6", CUISSON_BAS, "cuisson_bas_", echantillons)


# --- peinture anime --------------------------------------------------------------------------------------------------
def traits_h(F, S, V, liste):
	"""Plis peints couches (le long de s) : (s0, v0, longueur, largeur, force, pente)."""
	for s0, v0, longueur, larg, force, pente in liste:
		t = np.clip((S - s0) / longueur, 0, 1)
		d = np.abs(V - (v0 + pente * (S - s0)))
		F *= 1 - force * np.exp(-((d / larg) ** 2)) * np.clip(np.sin(np.pi * t), 0, 1) ** 0.6 * ((S >= s0) & (S <= s0 + longueur))


def peindre_bas():
	ao, lum = lire("ao", CUISSON_BAS), lire("lumiere", CUISSON_BAS)
	masque = ao > 0.001
	lumiere = np.clip(lum / np.percentile(lum[masque], 97), 0, 1.25)
	F = (0.2 + 0.88 * lumiere ** 0.85) * (0.5 + 0.5 * ao)
	ys, xs = np.mgrid[0:T, 0:T].astype(np.float32)

	def zone(nom):
		x0, y0, w, h = ZONES_BAS[nom]
		sl = (slice(y0, y0 + h), slice(x0, x0 + w))
		return sl, (xs[sl] - x0 + 0.5) / w, 1 - (ys[sl] - y0 + 0.5) / h

	rng = random.Random(5)
	# bande : tissu plie en epaisseurs horizontales (creux sombre dessous, bord eclaire dessus), qui ondulent le long de la taille
	sl, A, B = zone("bande")
	Lb = chemin(1.0, E_W, E_D, E_R)[4]
	S = A * Lb
	for k, (v0, phase) in enumerate(((0.26, 0.3), (0.5, 2.0), (0.75, 4.1))):
		vk = v0 + 0.045 * np.sin(2 * np.pi * S / 1.3 + phase) + 0.02 * np.sin(2 * np.pi * S / 0.47 + 1.7 * k)
		F[sl] *= 1 - 0.42 * np.exp(-(((B - vk + 0.025) / 0.03) ** 2))  # creux sous le pli
		F[sl] *= 1 + 0.2 * np.exp(-(((B - vk - 0.035) / 0.035) ** 2))  # dessus du pli, dans la lumiere
	traits_h(F[sl], S, B, [(rng.uniform(0, Lb - 0.5), rng.uniform(0.15, 0.85), rng.uniform(0.25, 0.6), rng.uniform(0.015, 0.03), rng.uniform(0.15, 0.25), rng.uniform(-0.06, 0.06)) for _ in range(10)])
	F[sl] *= 1 - 0.2 * (np.exp(-((B / 0.06) ** 2)) + np.exp(-(((1 - B) / 0.06) ** 2)))  # bords roules
	# pans : bords plus sombres, plis en long
	for nom in ("pan1", "pan2"):
		sl, A, B = zone(nom)
		F[sl] *= 1 - 0.16 * (np.exp(-((A / 0.08) ** 2)) + np.exp(-(((1 - A) / 0.08) ** 2)))
		for _ in range(4):
			a0 = rng.uniform(0.2, 0.8)
			F[sl] *= 1 - 0.25 * np.exp(-(((A - a0 - 0.1 * (1 - B)) / 0.05) ** 2)) * np.clip(1 - B, 0, 1)
	# jambes : ombres des plis, couture laterale surpiquee
	for piece, zj, zr, graine in (("RightUpperLeg", "jambe_d", "revers_d", 71), ("LeftUpperLeg", "jambe_g", "revers_g", 83)):
		_, _, _, _, info = jambe(bpy.data.objects[piece], zj, zr, graine)
		sl, A, B = zone(zj)
		S, V = A * info["L"], B * info["v_max"]
		bandes_plis(F[sl], S, V, info["plis"], periode=info["L"])
		dc = np.abs(S - info["L"] / 2)  # milieu du cote exterieur
		F[sl] *= 1 - 0.22 * np.exp(-((dc / 0.012) ** 2))  # couture laterale (continue : des pointilles moucheteraient)
		F[sl] *= 1 - 0.25 * np.exp(-(((V - info["v_max"]) / 0.08) ** 2))  # sous l'echarpe
		# revers : touffes
		sl, A, B = zone(zr)
		nz = np.random.default_rng(graine).standard_normal(A.shape).astype(np.float32)
		nz = flou(nz, 14)
		nz /= nz.std()
		F[sl] *= 1 - 0.14 * np.clip(nz, 0, None) * np.sin(np.pi * np.clip(B, 0, 1))
	F = flou(F, 3.5)
	for nom in ("bande", "noeud", "pan1", "pan2"):  # echarpe : formes plus larges, reflets plus rares
		x0, y0, w, h = ZONES_BAS[nom]
		sl = (slice(y0, y0 + h), slice(x0, x0 + w))
		F[sl] = flou(F[sl], 6) * 0.94
	img = np.zeros((T, T, 3), np.float32)
	for nom, (x0, y0, w, h) in ZONES_BAS.items():
		sl = (slice(y0, y0 + h), slice(x0, x0 + w))
		pal = PALIERS[PALETTE_ZONE[nom]]
		img[sl] = np.where(masque[sl][..., None], cel(F[sl], pal), np.array(pal[0][1], np.float32))
	for (y0, y1, x0, x1), c in PASTILLES.values():  # interieur du tissu (UV des faces interieures a l'export)
		img[y0:y1, x0:x1] = c
	img = np.clip(img, 0, 255) / 255.0
	px = np.concatenate([img[::-1], np.ones((T, T, 1), np.float32)], -1)
	out = bpy.data.images.get(TEX_BAS.name) or bpy.data.images.new(TEX_BAS.name, T, T, alpha=False)
	out.pixels.foreach_set(px.astype(np.float32).ravel())
	out.filepath_raw = str(TEX_BAS)
	out.file_format = "PNG"
	out.save()
	materiau("Mat_Bas_v6", (0.8, 0.6, 0.1, 1), out)
	return TEX_BAS
