# -*- coding: utf-8 -*-
u"""LES CLOCHES — projeter le reseau sonore sur la ville cuite.

Le catalogue humain vit dans ``scripts/ville/port-real-cloches.json`` et ne
contient AUCUNE coordonnee : chaque cloche designe son ancre par un id de noeud
du graphe. Ce script resout les ancres, verifie ce qui doit l'etre, et ecrit la
couche ``cloches`` dans ``monde/portreal.plan2d.json``.

    python scripts/monde/cloches.py --lieu port-real
    python scripts/monde/cloches.py --lieu port-real --appliquer
    python scripts/monde/cloches.py --lieu port-real --couverture

POURQUOI UNE COUCHE ET PAS DES REPERES. Un repere est un endroit ou l'on se
donne rendez-vous ; une cloche est un EMETTEUR, et ce qui la definit n'est pas
son point mais sa portee. Les meler ferait entrer sept cloches dans l'index de
recherche des lieux et dans le filtre des portes de `bataille2d.js`, pour un
gain nul.

QUAND LE LANCER. Apres `plan_ville.py`, qui reecrit `plan2d.json` en entier et
emporte cette couche avec lui — meme regle que `toponymie.py`, et pour la meme
raison. L'ordre est : plan → toponymie → cloches.

CE QUE CE SCRIPT NE FAIT PAS. Il ne propage rien. Il pose des emetteurs avec
leur portee et dit ce qu'ils couvrent ; qui entend quoi, a quelle minute, et ce
qu'il en comprend, c'est une autre affaire et elle n'appartient pas au monde
cuit. Voir docs/recherche/les-gardes-et-patrouilles-de-ville.md, section 7.
"""
import argparse
import io
import json
import math
import os
import re
import sys
import tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MONDE = os.path.join(RACINE, "monde")
PREFIXES = {"port-real": "portreal", "peyredragon": "peyredragon"}
CATALOGUES = {
    "portreal": os.path.join(RACINE, "scripts", "ville", "port-real-cloches.json"),
}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def lire(chemin):
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


def catalogue(prefixe):
    chemin = CATALOGUES.get(prefixe)
    if not chemin or not os.path.exists(chemin):
        return None
    return lire(chemin)


# ---------------------------------------------------------------------------
# VERIFIER — avant d'ecrire, pas apres
# ---------------------------------------------------------------------------
# Une cloche mal ancree ne casse rien : elle disparait du plan sans un mot, et
# l'on croit l'avoir posee. C'est exactement la faute que `tick.py --verifier`
# traque ailleurs dans le depot, et elle se traque ici de la meme facon.
def verifier(cat, noeuds):
    fautes = []
    vus = set()
    sonneries = set(k for k in cat.get("_sonneries", {}) if not k.startswith("_"))
    statuts = set(cat.get("_statuts", {}))
    ids = set(c.get("id") for c in cat.get("cloches", []))

    for c in cat.get("cloches", []):
        ident = c.get("id") or "(sans id)"
        if not c.get("id"):
            fautes.append(u"une cloche sans id : %r" % c.get("nom"))
        elif c["id"] in vus:
            fautes.append(u"id en double : %s" % c["id"])
        vus.add(c.get("id"))

        if not c.get("nom"):
            fautes.append(u"%s : pas de nom" % ident)
        if not c.get("description"):
            fautes.append(u"%s : pas de description" % ident)
        if c.get("statut") not in statuts:
            fautes.append(u"%s : statut inconnu %r" % (ident, c.get("statut")))
        if c.get("ancre") not in noeuds:
            fautes.append(u"%s : ancre introuvable dans le graphe : %r"
                          % (ident, c.get("ancre")))
        for s in c.get("sonneries") or []:
            if s not in sonneries:
                fautes.append(u"%s : sonnerie hors vocabulaire : %r" % (ident, s))
        if not c.get("sonneries"):
            fautes.append(u"%s : ne sait rien dire" % ident)
        if not c.get("portee"):
            fautes.append(u"%s : pas de portee" % ident)
        # UNE CLOCHE QUI SONNE LE TOCSIN DOIT DIRE QUI TIRE LA CORDE. C'est la
        # regle florentine de 1355 rendue verifiable : sonner sans droit est une
        # trahison, donc le droit doit exister quelque part et pas dans la tete
        # du MJ. `null` explicite est une reponse — c'est un refus, pas un oubli.
        if "tocsin" in (c.get("sonneries") or []) and "tocsin_par" not in c:
            fautes.append(u"%s : sonne le tocsin sans dire par quelle main "
                          u"(`tocsin_par`)" % ident)
        if c.get("relaie") and c["relaie"] not in ids:
            fautes.append(u"%s : relaie une cloche inconnue : %r"
                          % (ident, c["relaie"]))
    return fautes


# ---------------------------------------------------------------------------
# PROJETER — resoudre les ancres, et rien de plus
# ---------------------------------------------------------------------------
def projeter(cat, noeuds):
    out = []
    for c in cat.get("cloches", []):
        p = noeuds.get(c.get("ancre"))
        if not p:
            continue
        item = {
            "id": c["id"], "nom": c["nom"],
            "ensemble": c.get("ensemble") or "",
            "x": round(p[0], 1), "y": round(p[1], 1),
            # LE SOL PLUS LE BEFFROI. La hauteur n'est pas un ornement : c'est
            # ce qui fait qu'un bourdon sur la colline de Visenya couvre la
            # ville et qu'une cloche de porte ne passe pas son quartier.
            "z": round(p[2] + (c.get("beffroi") or 0), 1),
            "sol": round(p[2], 1), "beffroi": c.get("beffroi") or 0,
            "voix": c.get("voix") or "moyenne",
            "portee": c["portee"],
            "sonneries": list(c.get("sonneries") or []),
            "tocsin": "tocsin" in (c.get("sonneries") or []),
            "droit": c.get("droit") or "",
            "statut": c.get("statut") or "pose",
            "description": c["description"],
        }
        if c.get("tocsin_par"):
            item["tocsin_par"] = c["tocsin_par"]
        if c.get("relaie"):
            item["relaie"] = c["relaie"]
        out.append(item)
    # Les petites d'abord : une grande cloche se peint par-dessus si les deux
    # se touchent. Meme regle que les reperes de `toponymie.py`.
    return sorted(out, key=lambda c: (c["portee"], c["nom"]))


# ---------------------------------------------------------------------------
# LA COUVERTURE — le seul chiffre qui decide quelque chose
# ---------------------------------------------------------------------------
# On ne propage pas le son ici (voir la docstring). Mais on peut dire, sans rien
# simuler, quelle part de la ville est dans la portee d'au moins une cloche de
# tocsin — et c'est la question qui commande tout le reste : un reseau qui laisse
# un quartier sourd est un quartier ou l'alarme arrive a pied.
# ON MESURE SUR LES TOITS, PAS SUR UNE SURFACE, et c'est toute la difference.
# La premiere version comptait des points d'une grille dans le rectangle cuit et
# rendait 98,5 % — un chiffre circulaire, puisque l'emprise etait deduite des
# cloches elles-memes. La seconde comptait la surface dans les murs et rendait
# 100 %. Aucune des deux ne dit ce qu'on veut savoir, qui est : COMBIEN DE
# MAISONS entendent, et LESQUELLES. Une lieue de greve sourde ne se joue pas
# comme trois cents toits sourds, et un pourcentage confond les deux.
def couverture(cloches, prefixe):
    chem = os.path.join(MONDE, prefixe + ".bati.json")
    if not os.path.exists(chem):
        return None
    b = lire(chem)
    C = {n: k for k, n in enumerate(b["_colonnes"])}
    ix, iy, iq = C["x"], C["y"], C["quartier"]
    alarme = [c for c in cloches if c["tocsin"]]

    par_quartier = {}
    for bat in b["bati"]:
        x, y, q = bat[ix], bat[iy], bat[iq]
        e = par_quartier.setdefault(q, {"n": 0, "entend": 0, "par": {}})
        e["n"] += 1
        # LA PREMIERE QUI PORTE, pas la plus proche : ce qu'on veut nommer est
        # la cloche dont ce toit depend, et c'est celle qui l'atteint de plus
        # loin qui compte le moins — on garde donc la plus serree qui suffit.
        mieux, quelle = None, None
        for c in alarme:
            d = math.hypot(x - c["x"], y - c["y"])
            if d <= c["portee"] and (mieux is None or d < mieux):
                mieux, quelle = d, c["nom"]
        if quelle:
            e["entend"] += 1
            e["par"][quelle] = e["par"].get(quelle, 0) + 1
    return par_quartier, alarme


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


def main():
    ap = argparse.ArgumentParser(description=u"Poser les cloches sur la ville cuite.")
    ap.add_argument("--lieu", default="port-real")
    ap.add_argument("--appliquer", action="store_true")
    ap.add_argument("--couverture", action="store_true",
                    help=u"la part de la ville a portee d'un tocsin")
    a = ap.parse_args()

    prefixe = PREFIXES.get(a.lieu, a.lieu)
    cat = catalogue(prefixe)
    if not cat:
        print(u"pas de catalogue de cloches pour %s" % a.lieu)
        return 0

    chem_graphe = os.path.join(MONDE, prefixe + ".graph.json")
    chem_plan = os.path.join(MONDE, prefixe + ".plan2d.json")
    for c in (chem_graphe, chem_plan):
        if not os.path.exists(c):
            print(u"manque : %s" % c)
            return 2

    noeuds = {n["id"]: n["xyz"] for n in lire(chem_graphe)["noeuds"]}
    fautes = verifier(cat, noeuds)
    if fautes:
        print(u"%d faute(s) :" % len(fautes))
        for f in fautes:
            print(u"  · " + f)
        return 1

    cloches = projeter(cat, noeuds)
    plan = lire(chem_plan)

    par_ensemble = {}
    for c in cloches:
        par_ensemble.setdefault(c["ensemble"] or u"(seule)", []).append(c)
    print(u"%d cloches, %d ensembles :" % (len(cloches), len(par_ensemble)))
    for nom, lot in sorted(par_ensemble.items(), key=lambda kv: -len(kv[1])):
        t = sum(1 for c in lot if c["tocsin"])
        print(u"  %-32s %2d cloche(s), %d tocsin, portee %d–%d m"
              % (nom, len(lot), t,
                 min(c["portee"] for c in lot), max(c["portee"] for c in lot)))

    if a.couverture:
        res = couverture(cloches, prefixe)
        if not res:
            print(u"\npas de bati cuit : couverture impossible")
        else:
            par_q, alarme = res
            n = sum(q["n"] for q in par_q.values())
            e = sum(q["entend"] for q in par_q.values())
            print(u"\n%d emetteurs de tocsin, %d toits : %.1f %% entendent."
                  % (len(alarme), n, 100.0 * e / max(1, n)))
            # PAR QUARTIER, dans l'ordre du plus sourd : un pourcentage global
            # ne se joue pas, un quartier nomme se joue.
            print(u"\n  %-26s %7s %7s   %s" % (u"quartier", u"toits", u"sourds",
                                               u"qui les tient"))
            for nom, q in sorted(par_q.items(),
                                 key=lambda kv: -(kv[1]["n"] - kv[1]["entend"])):
                muets = q["n"] - q["entend"]
                pri = sorted(q["par"].items(), key=lambda kv: -kv[1])[:1]
                print(u"  %-26s %7d %7d   %s"
                      % (nom[:26], q["n"], muets,
                         (u"%s (%d)" % (pri[0][0], pri[0][1])) if pri else u"—"))
            print(u"\nUn toit sourd n'est pas un toit tranquille : c'est un toit"
                  u" ou l'alarme arrive a pied.")

    if a.appliquer:
        plan["cloches"] = cloches
        plan["cloches_meta"] = {
            "version": cat.get("version"),
            "sonneries": {k: v for k, v in (cat.get("_sonneries") or {}).items()
                          if not k.startswith("_")},
            "muettes": {k: v for k, v in (cat.get("_muettes") or {}).items()
                        if not k.startswith("_")},
        }
        _ecrire_atomique(chem_plan, plan)
        print(u"\necrit : %s" % chem_plan)
    else:
        print(u"\nverification seule ; ajouter --appliquer pour ecrire")
    return 0


if __name__ == "__main__":
    sys.exit(main())
