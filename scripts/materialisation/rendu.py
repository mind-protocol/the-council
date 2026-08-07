# -*- coding: utf-8 -*-
"""Le rendu : un rasteriseur à tampon de profondeur, écrit à la main.

Facettes plates, un soleil, une passe d'ombre portée, de la brume avec la
distance. Pas de dépendance hors numpy et PIL — ce qui sort est une image, et
c'est tout ce qu'on lui demande.
"""
import math
import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# les matières — ce dont les choses sont faites, et comment ça prend la lumière
# ---------------------------------------------------------------------------
from palette import (MATIERES, PLATES, CIEL_HAUT, CIEL_BAS, BRUME,
                     APPAREILLEES, ASSISE_M, BLOC_M, JOINT_M)


def _norm(v):
    v = np.asarray(v, np.float64)
    return v / (np.linalg.norm(v) + 1e-12)


class Camera:
    def __init__(self, oeil, cible, champ=42.0, haut=(0, 0, 1)):
        self.oeil = np.asarray(oeil, np.float64)
        f = _norm(np.asarray(cible, np.float64) - self.oeil)
        d = _norm(np.cross(f, np.asarray(haut, np.float64)))
        u = np.cross(d, f)
        self.base = np.stack([d, u, f])          # lignes : droite, haut, avant
        self.champ = math.radians(champ)

    def vue(self, points):
        """Monde → repère de la caméra (x droite, y haut, z devant)."""
        return (points - self.oeil) @ self.base.T


def _ombre(tris, soleil, taille=2048):
    """Une carte de profondeur vue du soleil : orthographique, une seule passe."""
    f = _norm(-np.asarray(soleil, np.float64))
    a = np.array([0, 0, 1.0]) if abs(f[2]) < 0.9 else np.array([1.0, 0, 0])
    d = _norm(np.cross(f, a))
    u = np.cross(d, f)
    base = np.stack([d, u, f])
    # La mer est une nappe de douze kilomètres : la laisser entrer dans le cadre
    # de l'ombre, c'est étaler la carte sur le large et rendre l'île en escalier.
    p = tris.reshape(-1, 3) @ base.T
    lo, hi = p.min(0), p.max(0)
    etendue = np.maximum(hi[:2] - lo[:2], 1.0)
    ech = (taille - 2) / etendue
    ech = np.minimum(ech, ech.min())            # même échelle en x et en y
    prof = np.full((taille, taille), np.inf, np.float32)
    # on cale x et y sur la texture, mais on laisse z tel quel : c'est la
    # profondeur qu'on comparera plus tard, et elle doit rester dans le monde.
    q = np.stack([(p[:, 0] - lo[0]) * ech[0], (p[:, 1] - lo[1]) * ech[1], p[:, 2]], 1)
    q = q.reshape(-1, 3, 3)
    _peindre_profondeur(q, prof)
    return base, lo, ech, prof


def _peindre_profondeur(tris, prof):
    """Rastérise en Z linéaire (projection orthographique : pas de perspective)."""
    H, W = prof.shape
    xs, ys, zs = tris[:, :, 0], tris[:, :, 1], tris[:, :, 2]
    x0 = np.clip(np.floor(xs.min(1)).astype(int), 0, W - 1)
    x1 = np.clip(np.ceil(xs.max(1)).astype(int) + 1, 0, W)
    y0 = np.clip(np.floor(ys.min(1)).astype(int), 0, H - 1)
    y1 = np.clip(np.ceil(ys.max(1)).astype(int) + 1, 0, H)
    aire = ((xs[:, 1] - xs[:, 0]) * (ys[:, 2] - ys[:, 0]) -
            (xs[:, 2] - xs[:, 0]) * (ys[:, 1] - ys[:, 0]))
    for i in range(len(tris)):
        if x1[i] <= x0[i] or y1[i] <= y0[i] or abs(aire[i]) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x0[i], x1[i]) + 0.5,
                             np.arange(y0[i], y1[i]) + 0.5, indexing="xy")
        X, Y = xs[i], ys[i]
        w0 = (X[1] - X[0]) * (gy - Y[0]) - (Y[1] - Y[0]) * (gx - X[0])
        w1 = (X[2] - X[1]) * (gy - Y[1]) - (Y[2] - Y[1]) * (gx - X[1])
        w2 = (X[0] - X[2]) * (gy - Y[2]) - (Y[0] - Y[2]) * (gx - X[2])
        dedans = ((w0 >= 0) & (w1 >= 0) & (w2 >= 0)) | ((w0 <= 0) & (w1 <= 0) & (w2 <= 0))
        if not dedans.any():
            continue
        l1 = w2 / aire[i]
        l2 = w0 / aire[i]
        z = zs[i, 0] + l1 * (zs[i, 1] - zs[i, 0]) + l2 * (zs[i, 2] - zs[i, 0])
        vue = prof[y0[i]:y1[i], x0[i]:x1[i]]
        m = dedans & (z < vue)
        vue[m] = z[m]


def _clip_proche(t, near):
    """Coupe un triangle sur le plan z = near ; rend 0, 1 ou 2 triangles."""
    dedans = [p for p in t if p[2] >= near]
    dehors = [p for p in t if p[2] < near]
    if len(dedans) == 3:
        return [t]
    if not dedans:
        return []
    def coupe(a, b):
        s = (near - a[2]) / (b[2] - a[2])
        return a + (b - a) * s
    if len(dedans) == 1:
        a = dedans[0]
        return [np.stack([a, coupe(a, dehors[0]), coupe(a, dehors[1])])]
    a, b = dedans
    c = dehors[0]
    p, q = coupe(a, c), coupe(b, c)
    return [np.stack([a, b, q]), np.stack([a, q, p])]


def rendre(tris, matieres, cam, taille=(1600, 900), soleil=(0.52, -0.66, 0.54),
           brume=4200.0, ombres=True, mer=0.0, calque=None, opacite=0.72):
    """Rend une image. `tris` (N,3,3) en mètres, `matieres` (N,) de chaînes."""
    W, H = taille
    soleil = _norm(soleil)
    tris = np.asarray(tris, np.float32)

    # ---- la lumière, une couleur par facette ------------------------------
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
    vers = tris.mean(1) - cam.oeil
    n = np.where((n * vers).sum(1, keepdims=True) > 0, -n, n)     # deux faces
    lam = np.clip(n @ soleil, 0, 1)
    ciel = 0.5 + 0.5 * n[:, 2]                     # ce qui regarde en l'air prend le ciel

    base = np.array([MATIERES.get(m, MATIERES["roche"])[0] for m in matieres], np.float32)
    rug = np.array([MATIERES.get(m, MATIERES["roche"])[1] for m in matieres], np.float32)

    def teinter(l):
        # 0.16 d'ambiante rendait tout mur détourné du soleil quasi noir : une
        # pierre sombre dans une cour n'est pas noire, elle prend le ciel et ce
        # que le sol lui renvoie. D'où les deux termes, avant le soleil.
        lum = (0.30 + 0.34 * ciel + 0.82 * l)[:, None]
        t = base * lum + np.array([255, 232, 196], np.float32) * (l * rug * 0.10)[:, None]
        return np.clip(t, 0, 255)

    couleurs = teinter(lam)
    sombres = teinter(lam * 0.10)
    appareil = np.array([m in APPAREILLEES for m in matieres])
    plat = np.array([m in PLATES for m in matieres])
    if plat.any():
        c = np.array([MATIERES[m][0] if m in PLATES else (0, 0, 0)
                      for m in matieres], np.float32)
        couleurs[plat] = c[plat]
        sombres[plat] = c[plat] * 0.86
    # ce qui porte l'ombre : tout sauf l'eau, dont l'étendue ferait exploser
    # le cadre de la carte de profondeur
    carte = _ombre(tris[np.asarray(matieres) != "mer"], soleil) if ombres else None

    # ---- le ciel ----------------------------------------------------------
    g = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    fond = (CIEL_HAUT * (1 - g) + CIEL_BAS * g)[:, None, :]
    img = np.repeat(fond, W, 1).copy()
    zbuf = np.full((H, W), np.inf, np.float32)

    # ---- la projection ----------------------------------------------------
    focale = (W / 2) / math.tan(cam.champ / 2)
    near = 1.2
    v = cam.vue(tris.reshape(-1, 3).astype(np.float64)).reshape(-1, 3, 3)
    garder = (v[:, :, 2] > near).any(1)
    v = v[garder]
    couleurs, sombres, n = couleurs[garder], sombres[garder], n[garder]
    appareil = appareil[garder]

    ordre = np.argsort(v[:, :, 2].mean(1))         # du plus près au plus loin
    for i in ordre:
        for t in _clip_proche(v[i], near):
            _facette(t, couleurs[i], sombres[i], img, zbuf, W, H, focale, brume,
                     carte, cam, n[i], appareil=bool(appareil[i]))

    if calque is not None and len(calque[0]):
        # la radiographie : une seconde passe qui ignore la profondeur de la
        # première. C'est le seul moyen de montrer ce qui est SOUS la roche
        # sans mentir sur l'endroit où ça se trouve.
        dessus = img.copy()
        zb2 = np.full((H, W), np.inf, np.float32)
        touche = np.zeros((H, W), bool)
        v2 = cam.vue(np.asarray(calque[0], np.float32).reshape(-1, 3)
                     .astype(np.float64)).reshape(-1, 3, 3)
        c2 = np.array([MATIERES.get(m, MATIERES["roche"])[0] for m in calque[1]],
                      np.float32) * 1.15
        n2 = np.cross(calque[0][:, 1] - calque[0][:, 0],
                      calque[0][:, 2] - calque[0][:, 0])
        n2 /= (np.linalg.norm(n2, axis=1, keepdims=True) + 1e-9)
        c2 = np.clip(c2 * (0.55 + 0.45 * np.abs(n2 @ soleil))[:, None], 0, 255)
        for i in np.argsort(v2[:, :, 2].mean(1)):
            for t in _clip_proche(v2[i], near):
                _facette(t, c2[i], c2[i], dessus, zb2, W, H, focale, 1e9,
                         None, cam, n2[i], touche)
        img[touche] = img[touche] * (1 - opacite) + dessus[touche] * opacite

    fini = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    fini.zbuf = zbuf          # `nommer` s'en sert pour taire ce qui est caché
    return fini


def _appareiller(monde, normale):
    """Le dessin des assises et des joints, calculé sur la position monde.

    La tangente du mur sort de sa normale : les blocs courent donc HORIZONTALEMENT
    le long de chaque face, au lieu de suivre un axe du monde qui les ferait
    partir en biais dès qu'un mur n'est pas orienté nord-sud. Une assise sur deux
    est décalée d'un demi-bloc, comme on appareille.
    """
    t = np.array([-normale[1], normale[0], 0.0])
    n = np.linalg.norm(t)
    if n < 0.35:
        # UNE FACE HORIZONTALE N'A PAS D'ASSISES. Lui appliquer le découpage
        # d'un mur donne une seule assise infinie, donc des planches de trente
        # mètres : un sol se dalle en deux directions, pas en lits superposés.
        a = np.floor(monde[:, 0] / BLOC_M)
        b = np.floor((monde[:, 1] + (a % 2) * BLOC_M / 2) / BLOC_M)
        da = np.minimum(monde[:, 0] / BLOC_M % 1.0, 1 - monde[:, 0] / BLOC_M % 1.0)
        db = np.minimum((monde[:, 1] + (a % 2) * BLOC_M / 2) / BLOC_M % 1.0,
                        1 - (monde[:, 1] + (a % 2) * BLOC_M / 2) / BLOC_M % 1.0)
        joint = np.minimum(da, db) * BLOC_M < JOINT_M
        h = np.abs(np.sin(a * 12.9898 + b * 78.233) * 43758.5453)
        return np.where(joint, 0.78, 0.94 + (h - np.floor(h)) * 0.12)[:, None]
    z = monde[:, 2]
    u = monde @ (t / n)
    assise = np.floor(z / ASSISE_M)
    u = u + (assise % 2) * (BLOC_M / 2)
    bloc = np.floor(u / BLOC_M)

    # le joint : une rainure sombre, en creux, sur les deux directions
    dz = np.minimum(z / ASSISE_M % 1.0, 1.0 - z / ASSISE_M % 1.0) * ASSISE_M
    du = np.minimum(u / BLOC_M % 1.0, 1.0 - u / BLOC_M % 1.0) * BLOC_M
    joint = np.minimum(dz, du) < JOINT_M

    # deux pierres voisines ne sont jamais du même ton
    h = np.abs(np.sin(assise * 12.9898 + bloc * 78.233) * 43758.5453)
    ton = 0.93 + (h - np.floor(h)) * 0.14
    return np.where(joint, 0.72, ton)[:, None]


def _facette(t, couleur, sombre, img, zbuf, W, H, focale, brume, carte, cam,
             normale, touche=None, appareil=False):
    z = t[:, 2]
    sx = W / 2 + t[:, 0] / z * focale
    sy = H / 2 - t[:, 1] / z * focale
    x0 = max(0, int(math.floor(sx.min())))
    x1 = min(W, int(math.ceil(sx.max())) + 1)
    y0 = max(0, int(math.floor(sy.min())))
    y1 = min(H, int(math.ceil(sy.max())) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    aire = (sx[1] - sx[0]) * (sy[2] - sy[0]) - (sx[2] - sx[0]) * (sy[1] - sy[0])
    if abs(aire) < 1e-9:
        return
    gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5, indexing="xy")
    w0 = (sx[1] - sx[0]) * (gy - sy[0]) - (sy[1] - sy[0]) * (gx - sx[0])
    w1 = (sx[2] - sx[1]) * (gy - sy[1]) - (sy[2] - sy[1]) * (gx - sx[1])
    w2 = (sx[0] - sx[2]) * (gy - sy[2]) - (sy[0] - sy[2]) * (gx - sx[2])
    dedans = ((w0 >= 0) & (w1 >= 0) & (w2 >= 0)) | ((w0 <= 0) & (w1 <= 0) & (w2 <= 0))
    if not dedans.any():
        return
    l1, l2 = w2 / aire, w0 / aire
    l0 = 1 - l1 - l2
    inv = l0 / z[0] + l1 / z[1] + l2 / z[2]
    prof = 1.0 / np.where(np.abs(inv) < 1e-9, 1e-9, inv)
    m = dedans & (prof > 0) & (prof < zbuf[y0:y1, x0:x1])
    if not m.any():
        return

    # la couleur du pixel : au soleil ou à l'ombre, tranché pixel par pixel —
    # une ombre décidée par facette dessine l'escalier des triangles.
    p = prof[m]
    monde = None
    if carte is None:
        teinte = np.repeat(couleur[None, :], len(p), 0)
        if appareil:
            vx = (gx[m] - W / 2) / focale * p
            vy = -(gy[m] - H / 2) / focale * p
            monde = cam.oeil[None, :] + np.stack([vx, vy, p], 1) @ cam.base
    else:
        bo, lo, ech, carte_p = carte
        vx = (gx[m] - W / 2) / focale * p
        vy = -(gy[m] - H / 2) / focale * p
        monde = cam.oeil[None, :] + np.stack([vx, vy, p], 1) @ cam.base
        monde = monde + normale[None, :] * 1.6          # le biais, le long de la normale
        c = monde @ bo.T
        px = np.clip(((c[:, 0] - lo[0]) * ech[0]).astype(int), 0, carte_p.shape[1] - 1)
        py = np.clip(((c[:, 1] - lo[1]) * ech[1]).astype(int), 0, carte_p.shape[0] - 1)
        au_soleil = np.zeros(len(p), np.float32)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1)):
            qx = np.clip(px + dx, 0, carte_p.shape[1] - 1)
            qy = np.clip(py + dy, 0, carte_p.shape[0] - 1)
            au_soleil += (c[:, 2] <= carte_p[qy, qx] + 1.2)
        au_soleil = (au_soleil / 6.0)[:, None]
        teinte = couleur[None, :] * au_soleil + sombre[None, :] * (1 - au_soleil)
        monde = monde - normale[None, :] * 1.6      # on ôte le biais des ombres

    if appareil and monde is not None:
        teinte = teinte * _appareiller(monde, normale)

    f = np.clip(p / brume, 0, 1)[:, None] ** 1.25
    img[y0:y1, x0:x1][m] = teinte * (1 - f) + BRUME[None, :] * f
    zbuf[y0:y1, x0:x1][m] = p
    if touche is not None:
        touche[y0:y1, x0:x1][m] = True


# ---------------------------------------------------------------------------
# nommer — une image qui montre trente-quatre lieux doit pouvoir les dire
# ---------------------------------------------------------------------------
def _fonte(taille):
    from PIL import ImageFont
    for f in (r"C:\Windows\Fonts\georgia.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try:
            return ImageFont.truetype(f, taille)
        except Exception:
            pass
    return ImageFont.load_default()


def nommer(img, cam, reperes, taille=19, ecart=26):
    """Pose les noms sur l'image. `reperes` = [(point monde, texte), …].

    Les étiquettes se repoussent verticalement jusqu'à ne plus se marcher
    dessus, et chacune garde un fil vers son point : sans ce fil, un nom
    déplacé devient un mensonge sur l'endroit qu'il désigne.
    """
    from PIL import ImageDraw
    W, H = img.size
    focale = (W / 2) / math.tan(cam.champ / 2)
    pts = np.asarray([r[0] for r in reperes], np.float64)
    v = cam.vue(pts)
    zbuf = getattr(img, "zbuf", None)
    ecran = []
    for i, (x, y, z) in enumerate(v):
        if z <= 1.0:
            continue
        sx = W / 2 + x / z * focale
        sy = H / 2 - y / z * focale
        if not (-200 < sx < W + 200 and -200 < sy < H + 200):
            continue
        # Un nom posé sur ce qu'un mur cache est un mensonge : on l'ôte, sauf
        # si le repère est en dehors du cadre (là, il désigne un hors-champ).
        if zbuf is not None and 0 <= sx < W and 0 <= sy < H:
            if zbuf[int(sy), int(sx)] < z - 6.0:
                continue
        ecran.append([sx, sy, sx, sy - 14, reperes[i][1], z])
    ecran.sort(key=lambda e: e[5])

    for _ in range(220):                       # on écarte ce qui se chevauche
        bouge = False
        for a in range(len(ecran)):
            for b in range(a + 1, len(ecran)):
                A, B = ecran[a], ecran[b]
                if abs(A[2] - B[2]) > 190:
                    continue
                d = B[3] - A[3]
                if abs(d) >= ecart:
                    continue
                k = (ecart - abs(d)) / 2 + 0.5
                s = 1 if d >= 0 else -1
                A[3] -= s * k
                B[3] += s * k
                bouge = True
        if not bouge:
            break

    d = ImageDraw.Draw(img, "RGBA")
    f = _fonte(taille)
    for sx, sy, tx, ty, texte, _ in ecran:
        d.line([(sx, sy), (tx, ty + taille * 0.62)], fill=(232, 226, 214, 150), width=1)
        d.ellipse([sx - 2.2, sy - 2.2, sx + 2.2, sy + 2.2], fill=(240, 232, 216, 220))
        lg = d.textlength(texte, font=f)
        x0 = tx - lg / 2
        d.rectangle([x0 - 5, ty - 2, x0 + lg + 5, ty + taille * 1.24],
                    fill=(14, 16, 20, 170))
        d.text((x0, ty), texte, font=f, fill=(238, 232, 220, 255))
    return img
