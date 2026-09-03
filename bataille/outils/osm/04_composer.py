# -*- coding: utf-8 -*-
"""Composer une ville de l'état depuis l'OSM nettoyé et le relief.

    python bataille/outils/osm/04_composer.py --nom gelibolu --id gelibolu-peninsule

Écrit etat/villes/<id>.json au format que scripts/monde/cuire_ville.py cuit et
que le calque terrain du moteur peint : `repere`, `sol` en unités (par défaut
5 m l'unité), l'y VERS LE SUD comme dans les villes tracées à la main — nos
couches ont l'y vers le nord, on retourne ici. Ce fichier est une sortie
d'outil : on ne l'édite pas, on relance.

Ce que la composition décide, et d'où ça vient :
- la MER : construite depuis le trait de côte OSM (terre à gauche, mer à
  droite — règle OSM), découpé à l'emprise et refermé le long du bord, puis
  vérifié contre la mer du relief (altitude ≤ 0). Les îlots sont ignorés.
- les COLLINES : là où la pente du relief dépasse `--pente` ; contours tracés
  sur le masque de pente, lissés, les moins de 4 ha écartés. C'est la seule
  couverture du sol qui ne vient pas d'OSM, parce qu'OSM n'en a presque pas ici.
- le reste passe d'OSM au vocabulaire du calque : champ et verger → champ,
  bois et lande → bois, ruisseau → riviere, route, piste et sentier → route
  (l'origine reste dans `detail`), plage → greve, plan d'eau → eau.
- les VILLAGES : le site est OSM, l'étendue est COMPOSÉE (un octogone de 120 m),
  et `detail` le dit. Les lieux-dits restent des points nommés, non peints.

Le fond nu du calque vaut pour tout ce qui n'est rien de cela : la campagne.
"""
import argparse, io, json, math, os
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _travail import dossier_travail  # les intermédiaires vivent hors du dépôt

MOTEUR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # bataille/
RACINE = os.path.dirname(MOTEUR)
EPS = 0.05


# ── la mer, depuis le trait de côte ──────────────────────────────────────────
def chainer(lignes):
    """Raccorde des polylignes par leurs extrémités (mêmes nœuds = mêmes coordonnées)."""
    cle = lambda p: (round(p[0], 1), round(p[1], 1))
    restantes = [list(map(tuple, l)) for l in lignes]
    par_debut = {}
    for k, l in enumerate(restantes):
        par_debut.setdefault(cle(l[0]), []).append(k)
    vus, chaines = set(), []
    for k in range(len(restantes)):
        if k in vus:
            continue
        vus.add(k)
        ch = list(restantes[k])
        while True:
            suivants = [s for s in par_debut.get(cle(ch[-1]), []) if s not in vus]
            if not suivants:
                break
            s = suivants[0]
            vus.add(s)
            ch += restantes[s][1:]
        chaines.append(ch)
    # Une chaîne commencée au milieu d'une côte s'arrête là où une autre finit :
    # on recolle tant qu'une fin rejoint un début.
    recolle = True
    while recolle:
        recolle = False
        for i, a in enumerate(chaines):
            for j, b in enumerate(chaines):
                if i != j and cle(a[-1]) == cle(b[0]):
                    chaines[i] = a + b[1:]
                    del chaines[j]
                    recolle = True
                    break
            if recolle:
                break
    return chaines


def clip_segment(p, q, W, H):
    """Liang–Barsky : la part de [p,q] dans [0,W]×[0,H], ou None ; dit si l'on entre / si l'on sort."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for num, den in ((p[0], -dx), (W - p[0], dx), (p[1], -dy), (H - p[1], dy)):
        if den == 0:
            if num < 0:
                return None
        else:
            t = num / den
            if den < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    if t0 > t1:
        return None
    return (p[0] + t0 * dx, p[1] + t0 * dy), (p[0] + t1 * dx, p[1] + t1 * dy), t0 > 0, t1 < 1


def decouper(chaine, W, H):
    """Une chaîne → ses morceaux intérieurs, chacun coupé net là où il traverse le bord."""
    morceaux, cour = [], []
    for p, q in zip(chaine, chaine[1:]):
        c = clip_segment(p, q, W, H)
        if c is None:
            if cour:
                morceaux.append(cour)
                cour = []
            continue
        a, b, entre, sort = c
        if entre and cour:
            morceaux.append(cour)
            cour = []
        if not cour:
            cour.append(a)
        cour.append(b)
        if sort:
            morceaux.append(cour)
            cour = []
    if cour:
        morceaux.append(cour)
    return morceaux


def sur_bord(p, W, H):
    return abs(p[0]) < EPS or abs(p[0] - W) < EPS or abs(p[1]) < EPS or abs(p[1] - H) < EPS


def t_bord(p, W, H):
    """Abscisse le long du bord, sens horaire en repère y-vers-le-nord : (0,0)→(0,H)→(W,H)→(W,0)→(0,0)."""
    x, y = p
    if abs(x) < EPS:
        return y
    if abs(y - H) < EPS:
        return H + x
    if abs(x - W) < EPS:
        return H + W + (H - y)
    return 2 * H + W + (W - x)


def coins_entre(t0, t1, W, H):
    """Les coins du rectangle rencontrés en allant de t0 à t1 dans le sens horaire (cyclique)."""
    P = 2 * (W + H)
    coins = [(H, (0, H)), (H + W, (W, H)), (2 * H + W, (W, 0)), (P, (0, 0))]
    d = (t1 - t0) % P
    return [c for t, c in coins if 0 < (t - t0) % P < d]


def mer_depuis_cote(cotes, W, H):
    """La mer : on suit la côte (mer à droite), et au bord on tourne dans le sens horaire jusqu'à la côte suivante."""
    chaines = chainer(cotes)
    morceaux, avert = [], []
    for ch in chaines:
        for m in decouper(ch, W, H):
            if len(m) < 2:
                continue
            if not (sur_bord(m[0], W, H) and sur_bord(m[-1], W, H)):
                avert.append(f"morceau de côte qui commence ou finit dedans ({len(m)} pts) — ignoré (îlot ou côte brisée)")
                continue
            morceaux.append(m)
    P = 2 * (W + H)
    entrees = [(t_bord(m[0], W, H), k) for k, m in enumerate(morceaux)]

    def suivant(t):
        return min(entrees, key=lambda e: ((e[0] - t) % P) or P)[1]

    polys, vus = [], set()
    for k in range(len(morceaux)):
        if k in vus:
            continue
        poly, cur = [], k
        for _ in range(len(morceaux) + 1):
            vus.add(cur)
            poly += morceaux[cur]
            te = t_bord(poly[-1], W, H)
            j = suivant(te)
            poly += coins_entre(te, t_bord(morceaux[j][0], W, H), W, H)
            if j == k:
                break
            if j in vus:
                avert.append("boucle de côte incohérente — polygone forcé fermé")
                break
            cur = j
        polys.append(poly)
    return polys, avert


# ── les collines, depuis la pente ────────────────────────────────────────────
def anneaux(mask):
    """Contours d'un masque binaire (intérieur à gauche), en coordonnées de cases."""
    ny, nx = mask.shape
    M = np.zeros((ny + 2, nx + 2), bool)
    M[1:-1, 1:-1] = mask
    aretes = {}
    js, is_ = np.nonzero(M)
    for j, i in zip(js.tolist(), is_.tolist()):
        if not M[j - 1, i]:
            aretes.setdefault((i, j), []).append((i + 1, j))
        if not M[j, i + 1]:
            aretes.setdefault((i + 1, j), []).append((i + 1, j + 1))
        if not M[j + 1, i]:
            aretes.setdefault((i + 1, j + 1), []).append((i, j + 1))
        if not M[j, i - 1]:
            aretes.setdefault((i, j + 1), []).append((i, j))
    rings = []
    while aretes:
        a = next(iter(aretes))
        ring = [a]
        while True:
            b = aretes[ring[-1]].pop()
            if not aretes[ring[-1]]:
                del aretes[ring[-1]]
            if b == a:
                break
            ring.append(b)
            if b not in aretes:
                break
        rings.append([(x - 1, y - 1) for x, y in ring])
    return rings


def aire_signee(pts):
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1])) / 2


def simplifier(pts, tol):
    """Douglas–Peucker, itératif."""
    if len(pts) < 3:
        return pts
    garde = [False] * len(pts)
    garde[0] = garde[-1] = True
    pile = [(0, len(pts) - 1)]
    while pile:
        a, b = pile.pop()
        (ax, ay), (bx, by) = pts[a], pts[b]
        dx, dy = bx - ax, by - ay
        ll = math.hypot(dx, dy) or 1e-9
        dmax, imax = -1, a
        for i in range(a + 1, b):
            d = abs(dy * (pts[i][0] - ax) - dx * (pts[i][1] - ay)) / ll
            if d > dmax:
                dmax, imax = d, i
        if dmax > tol:
            garde[imax] = True
            pile += [(a, imax), (imax, b)]
    return [p for p, g in zip(pts, garde) if g]


def collines(H, pas, pente, aire_min_m2, tol_m):
    gy, gx = np.gradient(H, pas)
    M = np.hypot(gx, gy) > pente
    S = np.zeros(M.shape, int)
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            S[1:-1, 1:-1] += M[1 + dj:M.shape[0] - 1 + dj, 1 + di:M.shape[1] - 1 + di]
    M = S >= 5  # majorité 3×3 : la poussière tombe
    out = []
    for r in anneaux(M):
        pts = [(x * pas, y * pas) for x, y in r]
        if aire_signee(pts) < aire_min_m2:  # trous (négatifs) et poussière écartés
            continue
        # Un anneau se simplifie en deux arcs, coupé au point le plus loin du
        # premier : sur un anneau fermé d'un seul tenant, la corde est nulle et
        # toutes les distances valent zéro — il ne resterait rien.
        k = max(range(len(pts)), key=lambda n: (pts[n][0] - pts[0][0]) ** 2 + (pts[n][1] - pts[0][1]) ** 2)
        s = simplifier(pts[:k + 1], tol_m)[:-1] + simplifier(pts[k:] + [pts[0]], tol_m)[:-1]
        if len(s) >= 3:
            out.append(s)
    return out, float(M.mean())


# ── composition ──────────────────────────────────────────────────────────────
def dedans(poly, x, y):
    r = False; j = len(poly) - 1
    for i in range(len(poly)):
        if (poly[i][1] > y) != (poly[j][1] > y) and \
           x < (poly[j][0]-poly[i][0])*(y-poly[i][1])/(poly[j][1]-poly[i][1])+poly[i][0]:
            r = not r
        j = i
    return r


def hors_de(pts, poly):
    """les bouts d'une polyligne qui restent hors du polygone (au moins deux points chacun)"""
    bouts, cur = [], []
    for p in pts:
        if dedans(poly, p[0], p[1]):
            if len(cur) >= 2: bouts.append(cur)
            cur = []
        else:
            cur.append(p)
    if len(cur) >= 2: bouts.append(cur)
    return bouts


def centre(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def slug(texte):
    """Un id en kebab-case ASCII depuis un nom (turc compris) : « Kadı Çeşmesi » → kadi-cesmesi."""
    if not texte:
        return ""
    import unicodedata
    t = texte.replace("ı", "i").replace("İ", "I").replace("ğ", "g").replace("Ğ", "G").replace("ş", "s").replace("Ş", "S")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = "".join(c.lower() if c.isalnum() else "-" for c in t)
    while "--" in t:
        t = t.replace("--", "-")
    return t.strip("-")


GENRES = {"champ": "champ", "verger": "champ", "bois": "bois", "lande": "bois", "ru": "riviere",
          "riviere": "riviere", "route": "route", "piste": "route", "sentier": "route",
          "greve": "greve", "eau": "eau"}


# ── ce qui n'est pas de la géographie ───────────────────────────────────
def preserver_croyances(dst, doc):
    """`faits`, `corps` et `acteurs` sont des CROYANCES : la chaîne ne les fabrique
    pas et n'a pas le droit de les effacer. On les reprend au fichier qu'on
    remplace — mais leurs coordonnées sont dans SON repère, alors on ne les
    reprend en silence que si le repère est le même ; sinon on les garde et on
    le DIT, parce qu'un acteur transposé sans le savoir est un acteur posé dans
    un champ."""
    garde = []
    if not os.path.exists(dst):
        return doc, garde
    try:
        vieux = json.load(io.open(dst, encoding="utf-8"))
    except Exception as e:
        return doc, [f"{os.path.basename(dst)} illisible ({e}) : croyances perdues"]
    memes = vieux.get("repere") == doc["repere"]
    for cle in ("faits", "corps", "acteurs"):
        gardees = vieux.get(cle) or []
        if not gardees:
            continue
        doc[cle] = gardees
        if not memes:
            garde.append(f"{len(gardees)} {cle} repris de l'ancien fichier, repère {vieux.get('repere')} ≠ {doc['repere']} : "
                         f"leurs coordonnées sont À REPLACER ({', '.join(str(x.get('id')) for x in gardees[:4])}…)")
        else:
            garde.append(f"{len(gardees)} {cle} repris (même repère)")
    return doc, garde


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nom", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--metres-par-unite", type=float, default=5.0)
    ap.add_argument("--pente", type=float, default=0.18, help="tangente ; 0.18 ≈ 10°")
    ap.add_argument("--donnees", help="dossier de travail (défaut : bataille/donnees/osm/<nom>/)")
    ap.add_argument("--ville", help="tissu d'une ville engendrée (scripts/ville/<x>.tissu.json) à verser à la place de son octogone")
    a = ap.parse_args()
    a.donnees = a.donnees or dossier_travail(a.nom)
    tissu = json.load(io.open(a.ville, encoding="utf-8")) if a.ville else None
    enceinte = next((t["points"] for t in tissu["tracé"] if t["id"] == "enceinte"), None) if tissu else None
    prop = json.load(io.open(os.path.join(a.donnees, f"{a.nom}.propre.json"), encoding="utf-8"))
    rel = json.load(io.open(os.path.join(a.donnees, f"{a.nom}.relief.json"), encoding="utf-8"))
    Hm = np.fromfile(os.path.join(a.donnees, f"{a.nom}.relief.bin"), dtype="<i2").reshape(rel["ny"], rel["nx"]) / 10.0
    W, Ht = prop["largeur_m"], prop["hauteur_m"]
    u = a.metres_par_unite

    def U(pts):  # mètres, y vers le nord → unités, y vers le sud
        return [[round(x / u, 1), round((Ht - y) / u, 1)] for x, y in pts]

    sol = []
    # la mer
    cotes = [e["points"] for e in prop["sol"] if e["genre"] == "cote"]
    mer, avert = mer_depuis_cote(cotes, W, Ht)
    for k, p in enumerate(mer):
        sol.append({"genre": "eau", "nom": "La mer" if k == 0 else f"La mer ({k + 1})", "points": U(p),
                    "detail": "trait de côte OSM, refermé sur le bord de l'emprise"})
    # contrôle contre le relief
    img = Image.new("1", (rel["nx"], rel["ny"]), 0)
    dr = ImageDraw.Draw(img)
    for p in mer:
        dr.polygon([(x / rel["pas"], y / rel["pas"]) for x, y in p], fill=1)
    mer_cote = np.asarray(img, bool)
    mer_relief = Hm <= 0.5
    accord = float((mer_cote == mer_relief).mean())
    # les collines
    coll, part = collines(Hm, rel["pas"], a.pente, 40_000, 20)
    for p in coll:
        sol.append({"genre": "colline", "nom": "", "points": U(p), "detail": f"pente > {a.pente} sur le relief SRTM"})
    # le reste d'OSM
    for e in prop["sol"]:
        g = GENRES.get(e["genre"])
        if g and len(e["points"]) >= 2:
            if g == "route" and enceinte:
                # la voirie d'aujourd'hui s'arrête au mur : dedans, ce sont les rues engendrées
                for bout in hors_de(e["points"], enceinte):
                    sol.append({"genre": g, "nom": e.get("nom", ""), "points": U(bout), "detail": e["tag"], "osm": e["osm"]})
                continue
            sol.append({"genre": g, "nom": e.get("nom", ""), "points": U(e["points"]), "detail": e["tag"], "osm": e["osm"]})
    for e in prop["sol"]:
        if e["genre"] == "village" and enceinte and dedans(enceinte, *e["points"][0]):
            continue                               # la ville engendrée prend la place de l'octogone
        if e["genre"] == "village":
            cx, cy = e["points"][0]
            r = 120
            octo = [(cx + r * math.cos(math.pi / 4 * k), cy + r * math.sin(math.pi / 4 * k)) for k in range(8)]
            sol.append({"genre": "village", "nom": e.get("nom", ""), "points": U(octo),
                        "detail": "site OSM ; étendue COMPOSÉE (octogone de 120 m)", "etiq": U([(cx, cy)])[0]})
        elif e["genre"] in ("lieu-dit", "ilot") and e.get("nom"):
            sol.append({"genre": e["genre"], "nom": e["nom"], "points": U(e["points"][:1]), "detail": e["tag"], "osm": e["osm"]})

    # la ville engendrée : son tracé, ses voies, ses toits — dans l'ordre où ça se peint
    if tissu:
        for t in tissu["tracé"]:
            p = {"genre": t["genre"], "id": t["id"], "nom": t["nom"], "points": U(t["points"]),
                 "detail": t["detail"], "fiabilite": t["fiabilite"], "etiq": U([centre(t["points"])])[0]}
            if t.get("largeur"): p["largeur"] = round(t["largeur"] / u, 2)
            sol.append(p)
        for v in tissu["voies"]:
            p = {"genre": "route", "nom": v.get("nom", ""), "largeur": round(v["largeur"] / u, 2),
                 "points": U(v["points"]), "detail": v["raison"], "rang": v["rang"]}
            if v.get("nom"): p["etiq"] = U([centre(v["points"])])[0]
            sol.append(p)
        # les quartiers portent leurs noms dans le tissu : cet outil ne connaît
        # pas les quartiers d'une ville et n'a pas à les tenir en dur
        quartiers = tissu.get("quartiers", {})
        for z, toits in tissu["toits"].items():
            q = quartiers.get(z, {})
            pts = [[round(p[0] / u, 2), round((Ht - p[1]) / u, 2), -p[2], round(p[3] / u, 2)]
                   + ([round(p[4] / u, 2)] if len(p) >= 5 else []) for p in toits]
            sol.append({"genre": "village", "nom": q.get("nom", z), "points": pts,
                        "detail": q.get("detail", "Toits engendrés par la circulation : façade sur rue"),
                        "etiq": U([centre([(p[0], p[1]) for p in toits])])[0]})

    # Chaque pièce du sol reçoit un `id` stable : c'est ce qu'une présence nomme
    # (« il se tient à bolayir ») et ce que le moteur retrouve dans le plan cuit.
    # Dérivé du nom quand il y en a un, du genre et de l'id OSM sinon ; une
    # pièce qui arrive avec son id le garde.
    vus = {}
    for s in sol:
        base = s.get("id") or slug(s.get("nom")) or (s["genre"] + "-" + s["osm"].replace("/", "-") if s.get("osm") else s["genre"])
        n = vus.get(base, 0) + 1
        vus[base] = n
        s["id"] = base if n == 1 else f"{base}-{n}"

    doc = {
        "_lisez_moi": f"Composée par bataille/outils/osm/04_composer.py depuis {a.nom}.propre.json et {a.nom}.relief.bin. Sortie d'outil : relancer, ne pas éditer. Unités de {u} m, y vers le sud. Chaque pièce du sol porte un `id` stable, référence des présences.",
        "_engendre": "OSM (ODbL) pour la structure — côte, voirie, eau, bois, villages, toponymes ; relief SRTM (tuiles Terrarium) pour les collines. Les champs et bois ont les limites d'aujourd'hui ; l'étendue des villages est composée.",
        "id": a.id, "nom": "La péninsule de Gallipoli — du col de Bolayır à la ville",
        "quand": "1305", "echelle": "La péninsule : le col, l'échine, les villages, la ville au bout",
        "lieu_id": "gallipoli", "basculer": False,
        "repere": [0, 0, math.ceil(W / u), math.ceil(Ht / u)], "par_cercle": 50,
        "sol": sol, "faits": [], "corps": [], "acteurs": [],
        "_acteurs_lisez_moi": "Vide, et volontairement : les acteurs d'une ville sont ce que le joueur CROIT y voir.",
    }
    dst = os.path.join(RACINE, "etat", "villes", f"{a.id}.json")
    doc, garde = preserver_croyances(dst, doc)
    with io.open(dst, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    c = Counter(s["genre"] for s in sol)
    print(f"{len(sol)} entrées -> {os.path.relpath(dst, RACINE)} ({os.path.getsize(dst) // 1024} Ko) ; repère {doc['repere']}")
    print("  genres :", ", ".join(f"{g} {n}" for g, n in c.most_common()))
    print(f"  mer : {len(mer)} polygone(s) ; accord côte OSM / mer du relief : {accord * 100:.1f} %")
    print(f"  collines : {len(coll)} aires, pente > {a.pente} sur {part * 100:.0f} % des cases")
    for w in garde:
        print("  ⚠", w)
    for w in avert:
        print("  ⚠", w)


if __name__ == "__main__":
    main()
