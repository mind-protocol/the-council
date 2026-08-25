# -*- coding: utf-8 -*-
u"""LE GUET — poser les guettes, calculer leurs rondes, et mesurer ce qu'elles tiennent.

    python scripts/monde/guet.py --lieu port-real
    python scripts/monde/guet.py --lieu port-real --appliquer
    python scripts/monde/guet.py --lieu port-real --sites      (proposer les sites)

CE QUI EST FIGE ET CE QUI EST CALCULE, et la separation n'est pas negociable :

  LES SITES SONT FIGES ET NOMMES dans `scripts/ville/port-real-guet.json`. Une
  guette est un lieu de la fiction — on la cite en scene, un homme y a servi
  vingt ans, un joueur s'en souvient. Un site recalcule a chaque cuisson serait
  un lieu qui bouge, c'est-a-dire pas un lieu.

  LES RONDES SONT CALCULEES SUR LE GRAPHE DES RUES, jamais ecrites a la main. Un
  circuit est un fait de voirie : il doit suivre les rues telles qu'elles sont,
  et se refaire quand elles changent. Une polyligne recopiee serait juste le jour
  ou on l'ecrit et fausse le lendemain — la meme faute que des coordonnees
  recopiees (cf. `cloches.py`).

  LES EFFECTIFS SONT CALCULES sur les toits desservis. Une guette qui sert six
  mille toits n'a pas la taille d'une qui en sert huit cents, et ecrire les deux
  a la main aurait garanti qu'ils soient faux.

L'ALGORITHME DE LA RONDE — six secteurs, et l'on referme. On tire six secteurs
de soixante degres autour de la guette ; dans chacun on prend le point le plus
proche d'une cible de ~330 m qui soit sur une rue PORTANT UN NOM ; on relie les
six au plus court sur le graphe, et l'on referme sur le premier. Ca donne une
BOUCLE et non une etoile : un homme qui patrouille fait le tour, il ne rentre
pas au poste entre deux rues. Ordonner par secteur plutot que par proximite est
tout le truc — un glouton du plus proche voisin produit un zigzag, pas une ronde.

QUAND LE LANCER. Apres `plan_ville.py` et `toponymie.py` — il lit les carrefours
que la toponymie a nommes, et ecrit dans le meme `plan2d.json`.
"""
import argparse
import collections
import heapq
import io
import json
import math
import os
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MONDE = os.path.join(RACINE, "monde")
PREFIXES = {"port-real": "portreal", "peyredragon": "peyredragon"}
CATALOGUES = {
    "portreal": os.path.join(RACINE, "scripts", "ville", "port-real-guet.json"),
}
ALLURE = 78.0          # metres par minute, l'allure de `journee.js`

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def lire(chemin):
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# LE GRAPHE DE SURFACE — celui sur lequel on marche
# ---------------------------------------------------------------------------
class Rues(object):
    def __init__(self, chemin):
        R = lire(chemin)
        self.N = R["noeuds"]
        self.reperes = R.get("reperes") or {}
        self.meta = R.get("reperes_meta") or {}
        self.adj = collections.defaultdict(list)
        self.nom = {}
        for a in R["aretes"]:
            self.adj[a["de"]].append((a["vers"], a["m"]))
            self.adj[a["vers"]].append((a["de"], a["m"]))
            if a.get("n"):
                self.nom.setdefault(a["de"], a["n"])
                self.nom.setdefault(a["vers"], a["n"])
        # LES ANCRES DE TOPONYMIE N'ONT PAS D'ARETES : ce sont des points poses
        # a cote de la voirie, pas des carrefours du graphe. Sans ce rattachement,
        # toute recherche partant d'un carrefour nomme ne trouve rien et ne le
        # dit pas — elle rend simplement zero.
        self.grille = collections.defaultdict(list)
        for k in self.adj:
            x, y, _ = self.N[k]
            self.grille[(int(x // 60), int(y // 60))].append(k)

    def proche(self, x, y, cases=2):
        ci, cj = int(x // 60), int(y // 60)
        best, bd = None, 1e18
        for i in range(ci - cases, ci + cases + 1):
            for j in range(cj - cases, cj + cases + 1):
                for k in self.grille.get((i, j), ()):
                    p = self.N[k]
                    d = (p[0] - x) ** 2 + (p[1] - y) ** 2
                    if d < bd:
                        bd, best = d, k
        return best, math.sqrt(bd) if best else 1e18

    def carrefour(self, nom):
        u"""Le noeud de voirie d'un carrefour nomme par la toponymie."""
        cle = self.reperes.get(nom)
        if not cle or cle not in self.N:
            return None
        x, y, _ = self.N[cle]
        k, _ = self.proche(x, y)
        return k

    def dijkstra(self, src, rmax, penalite=1.0):
        u"""`penalite` majore le poids des rues SANS NOM.

        UNE PATROUILLE PASSE PAR LA RUE, PAS PAR LE BOYAU DERRIERE — et sans ce
        biais elle prenait systematiquement le plus court, c'est-a-dire les
        venelles. Mesure faite : six rondes sur seize ne traversaient pas deux
        rues nommees, donc ne pouvaient pas se raconter en scene. A 1.0 le
        comportement est l'ancien, et c'est ce qu'on garde pour la DESSERTE :
        un homme qui court au secours prend le plus court, lui."""
        d, prev = {src: 0.0}, {}
        pq = [(0.0, src)]
        while pq:
            c, u = heapq.heappop(pq)
            if c > d.get(u, 1e18):
                continue
            for v, m in self.adj[u]:
                nd = c + m * (1.0 if v in self.nom else penalite)
                if nd <= rmax and nd < d.get(v, 1e18):
                    d[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        return d, prev

    def chemin(self, prev, src, dst):
        out = [dst]
        while out[-1] != src:
            if out[-1] not in prev:
                return None
            out.append(prev[out[-1]])
        out.reverse()
        return out


# ---------------------------------------------------------------------------
# LA RONDE
# ---------------------------------------------------------------------------
def ronde(rues, src, cible=330.0, rmax=520.0, secteurs=6):
    d, prev = rues.dijkstra(src, rmax)
    x0, y0, _ = rues.N[src]
    par_secteur = {}
    for u, dist in d.items():
        if dist < cible * 0.45:
            continue
        x, y, _ = rues.N[u]
        ang = (math.degrees(math.atan2(y - y0, x - x0)) + 360) % 360
        s = int(ang // (360.0 / secteurs))
        # Une rue qui porte un nom vaut cent quarante metres de detour : une
        # ronde se raconte (« il passe par la rue de la Soie »), et une ronde
        # qui n'enfile que des ruelles sans nom ne se raconte pas.
        score = abs(dist - cible) + (0.0 if u in rues.nom else 140.0)
        if s not in par_secteur or score < par_secteur[s][0]:
            par_secteur[s] = (score, u)
    points = [par_secteur[s][1] for s in sorted(par_secteur)]
    if len(points) < 3:
        return None

    boucle, total = [], 0.0
    for i in range(len(points)):
        a, b = points[i], points[(i + 1) % len(points)]
        # 1.45 : une venelle vaut une rue et demie. Assez pour choisir la rue
        # quand elle existe, pas assez pour faire un detour absurde.
        da, pa = rues.dijkstra(a, 2200.0, penalite=1.45)
        c = rues.chemin(pa, a, b)
        if c is None:
            return None
        boucle += c[:-1]
        # LA LONGUEUR SE MESURE SUR LE CHEMIN RETENU, pas sur le cout de
        # Dijkstra : `da[b]` porte la penalite, donc des metres qui n'existent
        # pas. Une ronde de 2 400 m aurait ete annoncee a 3 200.
        for j in range(len(c) - 1):
            for v, m in rues.adj[c[j]]:
                if v == c[j + 1]:
                    total += m
                    break
    boucle.append(boucle[0])
    rues_vues = []
    for k in boucle:
        n = rues.nom.get(k)
        if n and (not rues_vues or rues_vues[-1] != n):
            rues_vues.append(n)
    return {"noeuds": boucle, "m": total, "points": points,
            "rues": [x for x in dict.fromkeys(rues_vues)]}


def alleger_boucle(pts, epsilon=2.5):
    u"""DOUGLAS-PEUCKER DEGENERE SUR UNE BOUCLE, et silencieusement. Depart et
    arrivee confondus donnent une corde de longueur nulle : la distance de tout
    point a cette corde vaut alors zero, `pire` reste sous le seuil, et le
    circuit s'effondre a DEUX POINTS sans que rien ne le signale — mesure faite,
    les seize rondes rendaient deux points chacune.

    On coupe donc la boucle au point le plus eloigne du depart, on allege les
    deux moitieres separement, et l'on referme."""
    if len(pts) < 4:
        return pts
    x0, y0 = pts[0]
    loin = max(range(len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
    a = alleger(pts[:loin + 1], epsilon)
    b = alleger(pts[loin:], epsilon)
    return a[:-1] + b


def alleger(pts, epsilon=2.5):
    u"""Douglas-Peucker. Un circuit fait quatre cents noeuds de voirie ; ce qui
    doit atteindre le navigateur est la FORME, pas la liste des paves."""
    if len(pts) < 3:
        return pts
    x0, y0 = pts[0]
    x1, y1 = pts[-1]
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1e-9
    pire, loin = 0.0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x1 * y0 - y1 * x0) / n
        if d > pire:
            pire, loin = d, i
    if pire <= epsilon:
        return [pts[0], pts[-1]]
    return alleger(pts[:loin + 1], epsilon)[:-1] + alleger(pts[loin:], epsilon)


# ---------------------------------------------------------------------------
# CE QU'UNE GUETTE TIENT — mesure sur les toits, jamais sur une surface
# ---------------------------------------------------------------------------
def desserte(rues, sites, toits, rayon=600.0):
    u"""Pour chaque toit, la guette la plus proche À PIED et en combien de
    minutes. On mesure sur le graphe et jamais a vol d'oiseau : une ruelle qui
    ne debouche pas est a trois cents metres et a douze minutes."""
    a_qui = {}
    for gid, src in sites:
        d, _ = rues.dijkstra(src, rayon)
        for u, m in d.items():
            if u not in a_qui or m < a_qui[u][1]:
                a_qui[u] = (gid, m)
    compte = collections.Counter()
    minutes = collections.defaultdict(list)
    sourds = 0
    for noeud, quartier in toits:
        v = a_qui.get(noeud)
        if not v:
            sourds += 1
            continue
        compte[v[0]] += 1
        minutes[v[0]].append(v[1] / ALLURE)
    return compte, minutes, sourds


def _ecrire_atomique(chemin, donnees):
    dossier = os.path.dirname(os.path.abspath(chemin))
    fd, tmp = tempfile.mkstemp(prefix=os.path.basename(chemin) + ".",
                               suffix=".tmp", dir=dossier)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, chemin)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def proposer_sites(rues, toits, n=16, rayon=600.0):
    u"""GLOUTON DE COUVERTURE MAXIMALE, pour PROPOSER — jamais pour ecrire. On
    prend a chaque tour le carrefour nomme qui ajoute le plus de toits non
    encore desservis. C'est ce qui a choisi les seize du catalogue ; on le garde
    pour pouvoir le rejouer quand la ville change, et discuter du resultat."""
    par_noeud = collections.defaultdict(list)
    for i, (k, q) in enumerate(toits):
        par_noeud[k].append(i)
    atteint = {}
    for nom in rues.meta:
        k = rues.carrefour(nom)
        if not k:
            continue
        s = set()
        for u in rues.dijkstra(k, rayon)[0]:
            s.update(par_noeud.get(u, ()))
        atteint[nom] = s
    couvert, pris = set(), []
    while len(pris) < n:
        best, gain = None, 0
        for nom, s in atteint.items():
            if nom in pris:
                continue
            g = len(s - couvert)
            if g > gain:
                gain, best = g, nom
        if not best or gain < 250:
            break
        couvert |= atteint[best]
        pris.append(best)
        yield len(pris), best, gain, len(couvert)


def main():
    ap = argparse.ArgumentParser(description=u"Poser le Guet sur la ville cuite.")
    ap.add_argument("--lieu", default="port-real")
    ap.add_argument("--appliquer", action="store_true")
    ap.add_argument("--sites", action="store_true",
                    help=u"rejouer le glouton qui a choisi les seize")
    a = ap.parse_args()

    prefixe = PREFIXES.get(a.lieu, a.lieu)
    chem_cat = CATALOGUES.get(prefixe)
    if not chem_cat or not os.path.exists(chem_cat):
        print(u"pas de catalogue du Guet pour %s" % a.lieu)
        return 0
    cat = lire(chem_cat)

    chem_rues = os.path.join(MONDE, prefixe + ".rues.json")
    chem_bati = os.path.join(MONDE, prefixe + ".bati.json")
    chem_plan = os.path.join(MONDE, prefixe + ".plan2d.json")
    for c in (chem_rues, chem_bati, chem_plan):
        if not os.path.exists(c):
            print(u"manque : %s" % c)
            return 2

    rues = Rues(chem_rues)
    b = lire(chem_bati)
    C = {n: k for k, n in enumerate(b["_colonnes"])}
    toits = []
    for x in b["bati"]:
        k, _ = rues.proche(x[C["porte_x"]], x[C["porte_y"]])
        toits.append((k, x[C["quartier"]]))

    if a.sites:
        print(u"Glouton de couverture, rayon 600 m (7 min de marche) :")
        for i, nom, gain, tot in proposer_sites(rues, toits):
            print(u"  %2d. %-40s +%5d → %6d (%4.1f %%)"
                  % (i, nom[:40], gain, tot, 100.0 * tot / len(toits)))
        return 0

    # --- resoudre les sites, puis calculer les rondes ----------------------
    fautes, sites, resolues = [], [], []
    for g in cat.get("guettes", []):
        k = rues.carrefour(g.get("carrefour"))
        if not k:
            fautes.append(u"%s : carrefour introuvable : %r" % (g["id"], g.get("carrefour")))
            continue
        if not g.get("description"):
            fautes.append(u"%s : pas de description" % g["id"])
        sites.append((g["id"], k))
        resolues.append((g, k))
    if fautes:
        print(u"%d faute(s) :" % len(fautes))
        for f in fautes:
            print(u"  · " + f)
        return 1

    par = cat.get("_ronde") or {}
    arrets = par.get("part_arrets", 0.25)
    compte, minutes, sourds = desserte(rues, sites, toits)
    nuit = (cat.get("_effectifs") or {}).get("nuit_en_ville", 900)
    part_ronde = (cat.get("_effectifs") or {}).get("part_en_ronde", 0.25)
    total_toits = sum(compte.values()) or 1

    sortie = []
    print(u"%d guettes." % len(resolues))
    print(u"\n  %-30s %6s %6s %7s %5s %5s   %s"
          % (u"guette", u"toits", u"effect", u"ronde", u"min", u"poste", u"par ou"))
    for g, k in resolues:
        r = ronde(rues, k, cible=par.get("cible_m", 330),
                  rmax=par.get("rayon_m", 520), secteurs=par.get("secteurs", 6))
        x, y, z = rues.N[k]
        toits_g = compte.get(g["id"], 0)
        # L'EFFECTIF SUIT LES TOITS. Une guette n'est pas une unite de compte :
        # c'est un poste dimensionne sur ce qu'il dessert.
        eff = max(8, int(round(nuit * toits_g / float(total_toits))))
        en_ronde = max(2, int(round(eff * part_ronde / 2.0)) * 2)   # par paires
        item = {
            "id": g["id"], "nom": g["nom"], "carrefour": g["carrefour"],
            "x": round(x, 1), "y": round(y, 1), "z": round(z, 1),
            "statut": g.get("statut", "pose"), "description": g["description"],
            "toits": toits_g, "effectif": eff,
            "en_ronde": en_ronde, "au_poste": eff - en_ronde,
            "minutes_moyennes": round(sum(minutes[g["id"]]) / max(1, len(minutes[g["id"]])), 1),
        }
        if r:
            pts = alleger_boucle([[round(rues.N[n][0], 1), round(rues.N[n][1], 1)]
                                  for n in r["noeuds"]])
            # DEUX DUREES, ET IL FAUT LES DEUX. `minutes` est de la marche
            # pure ; un homme du guet s'arrete — une porte qu'on pousse, un mot
            # a quelqu'un, une lanterne qu'on rallume. Le tour reel est ce qui
            # decide de la frequence a laquelle une rue revoit une patrouille,
            # et c'est donc lui qu'on juge.
            marche = r["m"] / ALLURE
            item["ronde"] = {"m": round(r["m"]), "minutes": round(marche),
                             "minutes_tour": round(marche * (1.0 + arrets)),
                             "rues": r["rues"][:8], "trace": pts}
        sortie.append(item)
        print(u"  %-30s %6d %6d %5d p %6d %5d   %s"
              % (g["nom"][:30], toits_g, eff, en_ronde,
                 (r or {}).get("m", 0) and round(r["m"]), eff - en_ronde,
                 ", ".join((r or {}).get("rues", [])[:2])))

    dedans = sum(compte.values())
    print(u"\nDESSERTE — a moins de sept minutes de marche d'une guette :")
    print(u"  %d toits sur %d — %.1f %%" % (dedans, len(toits), 100.0 * dedans / len(toits)))
    print(u"  %d toits hors de portee : c'est la que le Guet n'ira pas a temps." % sourds)
    m = [x for lot in minutes.values() for x in lot]
    if m:
        m.sort()
        print(u"  delai median %.1f min · neuvieme decile %.1f min"
              % (m[len(m) // 2], m[int(len(m) * 0.9)]))
    tour = [g["ronde"]["minutes_tour"] for g in sortie if "ronde" in g]
    if tour:
        print(u"\nRONDES — %d circuits, %d a %d minutes de marche (mediane %d)."
              % (len(tour), min(tour), max(tour), sorted(tour)[len(tour) // 2]))

    if a.appliquer:
        plan = lire(chem_plan)
        plan["guettes"] = sortie
        # LA MESURE VOYAGE AVEC LA DONNEE. Sans elle, l'epreuve du banc devrait
        # refaire tout le calcul de desserte dans le navigateur — 45 000 toits
        # et seize Dijkstra — pour verifier un chiffre que ce script vient de
        # produire. On ecrit le resultat a cote, avec de quoi le rejouer.
        plan["guet_meta"] = {"version": cat.get("version"),
                             "systeme": cat.get("_le_systeme"),
                             "effectifs": cat.get("_effectifs"),
                             "ronde": cat.get("_ronde"),
                             "desserte": {
                                 "toits": len(toits),
                                 "desservis": dedans,
                                 "hors_de_portee": sourds,
                                 "rayon_m": 600,
                                 "minutes_medianes": round(m[len(m) // 2], 1) if m else None,
                                 "minutes_d9": round(m[int(len(m) * 0.9)], 1) if m else None,
                                 "commande": "python scripts/monde/guet.py --lieu port-real"}}
        _ecrire_atomique(chem_plan, plan)
        print(u"\necrit : %s" % chem_plan)
    else:
        print(u"\nverification seule ; ajouter --appliquer pour ecrire")
    return 0


if __name__ == "__main__":
    sys.exit(main())
