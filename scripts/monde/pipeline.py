# -*- coding: utf-8 -*-
"""LA PIPELINE — refaire le monde du début à la fin, dans l'ordre, sans se perdre.

    python scripts/monde/pipeline.py                    tout Port-Réal
    python scripts/monde/pipeline.py --liste            l'ordre et rien d'autre
    python scripts/monde/pipeline.py --sec              ce qui serait lancé
    python scripts/monde/pipeline.py --depuis usages    reprendre au milieu
    python scripts/monde/pipeline.py --jusqu-a besoins  s'arrêter avant la fin
    python scripts/monde/pipeline.py --seulement plan   une étape, et une seule
    python scripts/monde/pipeline.py --pose organique   l'autre modèle de semis

POURQUOI CE FICHIER. La chaîne fait onze étapes, chacune lit ce que la
précédente a écrit, et l'ordre n'est écrit nulle part — il vit dans les
docstrings des scripts, en phrases (« après coudre.py, avant batir.py »). Le
jour où l'on reprend le monde après trois semaines, on relance dans le désordre,
une étape lit un fichier périmé, et le défaut ne se voit que six écrans plus
loin : des corps rattachés à des maisons qui n'existent plus, une foule qui
marche dans des rues qu'on vient de déplacer.

CE QUE LA PIPELINE GARANTIT, et c'est tout ce qu'on lui demande :
  — l'ORDRE, écrit une fois ici et vérifiable d'un coup d'œil (`--liste`) ;
  — les ENTRÉES : une étape dont un fichier d'entrée manque ne part pas, on dit
    lequel et par quelle étape on l'obtient ;
  — la FRAÎCHEUR : si une sortie est plus vieille que son entrée, on le dit —
    c'est exactement le cas qui ne se voit pas à l'œil nu ;
  — ce que chaque étape a PRODUIT : taille, écart avec l'avant, durée.

CE QU'ELLE NE FAIT PAS. Elle ne devine pas ce qu'il faut relancer, elle ne
saute rien toute seule, et elle ne touche jamais à `etat/` : le monde est le
décor, la partie est ailleurs. Et elle ne lance PAS Blender — le volume
(`batir.py`) est une autre affaire, longue, qu'on décide à la main.
"""
import argparse
import io
import os
import subprocess
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")

# Windows sert du cp1252 sur la sortie standard et avale les accents des
# scripts appelés : on force l'UTF-8 une fois, ici, pour toute la chaîne.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PREFIXES = {"port-real": "portreal", "peyredragon": "peyredragon"}

# ---------------------------------------------------------------------------
# LA CHAÎNE — l'ordre, et la raison de chaque maillon
# ---------------------------------------------------------------------------
# `donne`  : ce que l'étape écrit. `veut` : ce qu'elle lit et qui doit exister.
# Les deux sont des SUFFIXES de fichier du monde (`portreal.<suffixe>`), sauf
# `gens/` qui est un dossier.
#
# L'ordre vient des docstrings des scripts, et il n'est pas négociable :
# le relief décide où l'on peut bâtir, le graphe décide où passent les rues,
# le semis pose les maisons entre elles, la couture rend le réseau navigable,
# les usages donnent un métier à chaque maison — et tout le reste en dépend.
ETAPES = [
    dict(id="relief", script="relief.py", nom="Le relief",
         pourquoi="la sous-couche : altitudes, eau, versants",
         veut=[], donne=["terrain.json"], minutes=2),
    dict(id="graphe", script="graphe.py", nom="Le graphe",
         pourquoi="la voirie métrée : nœuds, arêtes, couches, portails",
         veut=["terrain.json"], donne=["graph.json"], minutes=3),
    dict(id="semis", script="densifier.py", nom="Le semis",
         pourquoi="les parcelles et les maisons, entre les rues",
         veut=["terrain.json", "graph.json"], donne=["bati.json"], minutes=6,
         variante={"organique": "organique.py"}),
    dict(id="coudre", script="coudre.py", nom="La couture",
         pourquoi="recoudre les couches : sans elle, la ville n'est pas un réseau",
         veut=["graph.json", "bati.json"], donne=["graph.json"], minutes=2),
    dict(id="usages", script="usages.py", nom="Les usages",
         pourquoi="un métier par maison, et une porte sur la rue",
         veut=["graph.json", "bati.json", "terrain.json"],
         donne=["bati.json"], minutes=3),
    dict(id="portes", script="portes.py", nom="Les portes",
         pourquoi="faire entrer les portes dans le réseau",
         veut=["graph.json", "bati.json"], donne=["graph.json"], minutes=2),
    dict(id="degager", script="degager_voirie.py", nom="Le dégagement",
         pourquoi="sortir l'axe des rues des façades",
         veut=["graph.json", "bati.json"], donne=["graph.json"], minutes=2),
    dict(id="peupler", script="peupler.py", nom="Les corps",
         pourquoi="quatre cent mille habitants, chacun dans une maison",
         veut=["bati.json"], donne=["gens.json", "gens/"], minutes=4,
         prudence="Les index des corps changent : une partie en cours pointera "
                  "les mauvaises maisons jusqu'au prochain rechargement."),
    dict(id="besoins", script="besoins.py", nom="Les besoins",
         pourquoi="où chacun va, à quelle heure, et par quelle adresse",
         veut=["bati.json", "graph.json"], donne=["besoins.json"], minutes=2),
    dict(id="plan", script="plan_ville.py", nom="Le plan 2D",
         pourquoi="la ville dessinée, et le masque du bâti",
         veut=["terrain.json", "rues.json", "bati.json"],
         donne=["plan2d.json", "masque.bin"], minutes=4),
    dict(id="planches", script="planches.py", nom="Les planches",
         pourquoi="le plan en images, pour le REGARDER (facultatif)",
         veut=["plan2d.json"], donne=[], minutes=2, facultatif=True),
]
PAR_ID = {e["id"]: e for e in ETAPES}


# ---------------------------------------------------------------------------
# Ce qu'on sait d'un fichier — et l'on n'en demande pas plus
# ---------------------------------------------------------------------------
def chemin(prefixe, suffixe):
    if suffixe.endswith("/"):
        d = os.path.join(MONDE, suffixe.rstrip("/"))
        return d if prefixe == "portreal" else os.path.join(d, prefixe)
    return os.path.join(MONDE, prefixe + "." + suffixe)


def poids(p):
    """Taille en octets, dossier compris. -1 s'il n'existe pas."""
    if not os.path.exists(p):
        return -1
    if os.path.isdir(p):
        n = 0
        for r, _, fs in os.walk(p):
            for f in fs:
                n += os.path.getsize(os.path.join(r, f))
        return n
    return os.path.getsize(p)


def date(p):
    """Date de dernière écriture. 0 s'il n'existe pas ; pour un dossier, la
    plus RÉCENTE de ses pièces — c'est elle qui dit quand on l'a refait."""
    if not os.path.exists(p):
        return 0
    if os.path.isdir(p):
        t = 0
        for r, _, fs in os.walk(p):
            for f in fs:
                t = max(t, os.path.getmtime(os.path.join(r, f)))
        return t
    return os.path.getmtime(p)


def mo(n):
    if n < 0:
        return "absent"
    if n < 1024:
        return "%d o" % n
    if n < 1048576:
        return "%.0f Ko" % (n / 1024.)
    return "%.1f Mo" % (n / 1048576.)


def ecart(avant, apres):
    """De combien la sortie a bougé. C'est le chiffre qui dit si l'étape a
    vraiment fait quelque chose — une taille identique au kilo-octet près après
    un relancement est un signal, pas une coïncidence."""
    if avant < 0:
        return "neuf"
    if apres == avant:
        return "identique"
    d = apres - avant
    return "%s%s" % ("+" if d > 0 else "−", mo(abs(d)))


def horodate(t):
    return time.strftime("%H:%M:%S", time.localtime(t)) if t else "—"


def duree(s):
    return "%d min %02d s" % (int(s // 60), int(s % 60)) if s >= 60 else "%.1f s" % s


# ---------------------------------------------------------------------------
# Le journal — c'est tout l'intérêt du fichier, alors il est soigné
# ---------------------------------------------------------------------------
LARG = 78
def titre(t):
    print("\n" + "═" * LARG)
    print("  " + t)
    print("═" * LARG)


def ligne(t=""):
    print("  " + t)


def liste(prefixe, pose):
    titre("LA CHAÎNE — %d étapes" % len(ETAPES))
    for i, e in enumerate(ETAPES, 1):
        s = e.get("variante", {}).get(pose) or e["script"]
        drapeaux = " (facultatif)" if e.get("facultatif") else ""
        ligne("%2d. %-9s %-22s %s%s" % (i, e["id"], e["nom"], s, drapeaux))
        ligne("    %s" % e["pourquoi"])
        etats = []
        for d in e["donne"]:
            p = chemin(prefixe, d)
            etats.append("%s %s (%s)" % (d, mo(poids(p)), horodate(date(p))))
        if etats:
            ligne("    → " + " · ".join(etats))
        if e.get("prudence"):
            ligne("    ⚠ " + e["prudence"])
    print()


def fraicheur(prefixe, e):
    """Une sortie plus vieille que son entrée est le défaut qui ne se voit
    pas : le fichier est là, il a l'air bon, et il décrit un monde qui n'existe
    plus. On le dit, on ne le corrige pas — c'est au joueur de trancher."""
    vieilles = []
    for d in e["donne"]:
        td = date(chemin(prefixe, d))
        if not td:
            continue
        for v in e["veut"]:
            tv = date(chemin(prefixe, v))
            if tv and tv > td + 1:
                vieilles.append((d, v, td, tv))
    return vieilles


def lancer(e, prefixe, lieu, pose, sec):
    script = e.get("variante", {}).get(pose) or e["script"]
    chem = os.path.join(ICI, script)
    if not os.path.exists(chem):
        return None, "script introuvable : scripts/monde/" + script

    # LES ENTRÉES D'ABORD. Une étape qui part sans ses entrées ne rate pas, ce
    # qui serait confortable : elle produit un fichier plausible et faux.
    manque = []
    for v in e["veut"]:
        if poids(chemin(prefixe, v)) < 0:
            qui = [x["id"] for x in ETAPES if v in x["donne"]]
            manque.append("%s (donné par : %s)" % (v, ", ".join(qui) or "personne"))
    if manque:
        return None, "entrée manquante — " + " ; ".join(manque)

    avant = {d: poids(chemin(prefixe, d)) for d in e["donne"]}
    cmd = [sys.executable, chem]
    # Chaque script a sa façon de nommer le lieu, et l'uniformiser serait
    # toucher à onze fichiers pour une cosmétique : on s'adapte ici.
    if lieu != "port-real":
        cmd += (["--lieu", lieu] if e["id"] == "plan" else [lieu])
    if sec:
        return ("sec", " ".join(cmd[1:])), None

    t0 = time.time()
    r = subprocess.run(cmd, cwd=RACINE, capture_output=True)
    dt = time.time() - t0
    sortie = (r.stdout or b"").decode("utf-8", "replace")
    erreur = (r.stderr or b"").decode("utf-8", "replace")
    if r.returncode != 0:
        # On rend la fin de la sortie : l'erreur d'un script Python est en bas.
        fin = "\n".join((erreur or sortie).strip().splitlines()[-12:])
        return None, "code %d après %s\n%s" % (r.returncode, duree(dt), fin)

    apres = {d: poids(chemin(prefixe, d)) for d in e["donne"]}
    return {"dt": dt, "avant": avant, "apres": apres, "sortie": sortie,
            "erreur": erreur}, None


def main():
    ap = argparse.ArgumentParser(
        description="Refaire le monde, dans l'ordre, du début à la fin")
    ap.add_argument("--lieu", default="port-real", choices=sorted(PREFIXES))
    ap.add_argument("--liste", action="store_true", help="montrer la chaîne et sortir")
    ap.add_argument("--sec", action="store_true", help="dire ce qui serait lancé")
    ap.add_argument("--depuis", help="reprendre à cette étape")
    ap.add_argument("--jusqu-a", dest="jusqua", help="s'arrêter après cette étape")
    ap.add_argument("--seulement", help="une seule étape")
    ap.add_argument("--pose", default="reglee", choices=("reglee", "organique"),
                    help="quel modèle de semis (voir densifier.py / organique.py)")
    ap.add_argument("--avec-facultatif", action="store_true",
                    help="lancer aussi ce qui ne sert qu'à regarder")
    ap.add_argument("--bavard", action="store_true",
                    help="recopier toute la sortie de chaque script")
    a = ap.parse_args()

    prefixe = PREFIXES[a.lieu]
    if a.liste:
        return liste(prefixe, a.pose)

    # --- quelles étapes -----------------------------------------------------
    choix = ETAPES
    if a.seulement:
        if a.seulement not in PAR_ID:
            sys.exit("étape inconnue : %s (voir --liste)" % a.seulement)
        choix = [PAR_ID[a.seulement]]
    else:
        ids = [e["id"] for e in ETAPES]
        i0 = ids.index(a.depuis) if a.depuis in ids else 0
        i1 = ids.index(a.jusqua) + 1 if a.jusqua in ids else len(ids)
        if a.depuis and a.depuis not in ids:
            sys.exit("étape inconnue : %s (voir --liste)" % a.depuis)
        if a.jusqua and a.jusqua not in ids:
            sys.exit("étape inconnue : %s (voir --liste)" % a.jusqua)
        choix = ETAPES[i0:i1]
        if not a.avec_facultatif:
            choix = [e for e in choix if not e.get("facultatif")]

    titre("LE MONDE — %s%s" % (a.lieu, " (à sec)" if a.sec else ""))
    ligne("%d étapes, environ %d minutes" % (len(choix), sum(e["minutes"] for e in choix)))
    ligne("racine : " + RACINE)
    avertis = [e for e in choix if e.get("prudence")]
    if avertis and not a.sec:
        print()
        for e in avertis:
            ligne("⚠  %s — %s" % (e["nom"], e["prudence"]))

    # --- la fraîcheur, AVANT de lancer quoi que ce soit ---------------------
    vieux = []
    for e in ETAPES:
        vieux += [(e["id"],) + v for v in fraicheur(prefixe, e)]
    if vieux:
        print()
        ligne("Ce qui est PÉRIMÉ (une sortie plus vieille que son entrée) :")
        for id_, d, v, td, tv in vieux:
            ligne("   %-9s %s (%s) est plus vieux que %s (%s)"
                  % (id_, d, horodate(td), v, horodate(tv)))

    # --- la chaîne ----------------------------------------------------------
    bilan = []
    t0 = time.time()
    for i, e in enumerate(choix, 1):
        script = e.get("variante", {}).get(a.pose) or e["script"]
        titre("%d/%d  %s — %s" % (i, len(choix), e["nom"], e["pourquoi"]))
        ligne("scripts/monde/" + script)
        r, err = lancer(e, prefixe, a.lieu, a.pose, a.sec)
        if err:
            ligne("")
            ligne("✗ ARRÊT : " + err)
            ligne("")
            ligne("On ne continue pas : les étapes suivantes liraient un monde")
            ligne("à moitié refait. Corrigez, puis reprenez ici :")
            ligne("   python scripts/monde/pipeline.py --depuis " + e["id"])
            sys.exit(1)
        if a.sec:
            ligne("→ python " + r[1])
            continue
        if a.bavard and r["sortie"]:
            print()
            for l in r["sortie"].rstrip().splitlines():
                print("    │ " + l)
        else:
            # Les trois dernières lignes utiles : les scripts du dossier
            # finissent tous par leur récapitulatif, et c'est ce qu'on veut
            # lire — pas les trois cents lignes de progression du milieu.
            fin = [l for l in r["sortie"].rstrip().splitlines() if l.strip()][-3:]
            for l in fin:
                print("    │ " + l.strip())
        ligne("")
        for d in e["donne"]:
            p = chemin(prefixe, d)
            ligne("✓ %-14s %-9s %-10s en %s"
                  % (d, mo(r["apres"][d]), ecart(r["avant"][d], r["apres"][d]),
                     duree(r["dt"])))
        if not e["donne"]:
            ligne("✓ terminé en %s" % duree(r["dt"]))
        bilan.append((e, r))

    if a.sec:
        print()
        return

    # --- ce qu'on retient ---------------------------------------------------
    titre("FAIT — %s en tout" % duree(time.time() - t0))
    for e, r in bilan:
        for d in e["donne"]:
            ligne("%-9s %-14s %-9s %s"
                  % (e["id"], d, mo(r["apres"][d]),
                     ecart(r["avant"][d], r["apres"][d])))
    restes = fraicheur(prefixe, PAR_ID["plan"])
    if restes:
        ligne("")
        ligne("⚠  Le plan 2D est encore périmé : relancez --seulement plan")
    print()


if __name__ == "__main__":
    main()
