#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Le graphe d'architecture, LU DANS LE CODE — jamais ecrit a la main.

    python scripts/analyse/graphe_archi.py            le graphe + les ecarts
    python scripts/analyse/graphe_archi.py --mermaid  le diagramme seul
    python scripts/analyse/graphe_archi.py --json     tout, pour un autre outil

POURQUOI IL EXISTE. `docs/architecture.md` et `docs/organisation.md` sont
ecrits a la main : ils decrivent une CIBLE, et rien ne mesurait la distance
entre elle et le cablage reel. Le depot connait deja le prix de cet ecart —
soixante-quatre fiches decrivaient une architecture en dix couches dont quatre
pieces seulement existaient. Une carte qui montre un pays ou l'on n'habite pas
se lit comme une carte du pays ou l'on est.

CE QU'IL LIT, ET IL NE DEVINE RIEN :
  Python      les `import x` / `from x import` entre fichiers du depot ;
  Node        les `require("./x")` ;
  Navigateur  les globales `window.X = ...` posees, et les `X.` lues ailleurs.

Chaque fichier est rattache a son container par `docs/containers.json` — la
declaration qui FAIT le triplet. Les liens fichier a fichier sont ensuite
projetes sur les containers.

CE QU'IL COMPTE COMME ECART, et c'est la moitie utile de sa sortie :
  1. ORPHELIN      un fichier de code qu'aucun container ne reclame ;
  2. HORS PORTE    un lien qui entre dans un container ailleurs que par sa porte ;
  3. REMONTEE      un lien qui va vers un rang superieur ou egal (loi 2) ;
  4. COMMANDE-BIBLIOTHEQUE  une commande racine importee comme un module.

LECTURE SEULE, et aucun script du depot n'est importe : la passe du 30e jour a
appris qu'importer un script pour voir s'il se charge peut reinitialiser
`etat/flux.jsonl`.
"""

import fnmatch
import io
import json
import os
import re
import sys

# Le shell d'ici est en cp1252 : sans ca, une fleche tue la sortie (meme
# precaution que scripts/mesures.py).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DECLARATION = os.path.join(RACINE, "docs", "containers.json")

STDLIB = set("""os sys json io re time math random subprocess datetime argparse collections
hashlib shutil pathlib glob textwrap unicodedata itertools copy tempfile traceback urllib
base64 struct csv difflib functools typing uuid zlib codecs string statistics threading
signal errno platform locale warnings abc enum contextlib heapq bisect operator numbers
fractions decimal array binascii calendar pprint inspect importlib site sysconfig gc
weakref types dataclasses secrets getpass socket select queue asyncio concurrent
multiprocessing ctypes mmap unittest doctest pdb profile timeit trace logging numpy PIL
__future__ bpy mathutils""".split())


def lire(chemin):
    try:
        with io.open(chemin, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def fichiers_de_code():
    """Tous les fichiers de code suivis, chemins relatifs a la racine."""
    sortie = []
    for base, dossiers, noms in os.walk(RACINE):
        dossiers[:] = [d for d in dossiers if d not in
                       (".git", "node_modules", "__pycache__", "vendor", "archive", "etat")]
        for n in noms:
            if n.endswith((".py", ".js", ".mjs")):
                rel = os.path.relpath(os.path.join(base, n), RACINE).replace("\\", "/")
                if rel.startswith(("scripts/", "serveur/", "ecrans/")):
                    sortie.append(rel)
    return sorted(sortie)


def charger_declaration():
    d = json.loads(lire(DECLARATION))
    return {k: v for k, v in d.items() if not k.startswith("_")}


def rattacher(fichiers, declaration):
    """fichier -> container, par les motifs declares. Le premier qui matche gagne."""
    ou = {}
    for f in fichiers:
        for nom, c in declaration.items():
            if any(fnmatch.fnmatch(f, m) for m in c["fichiers"]):
                ou[f] = nom
                break
    return ou


def liens_python(fichiers):
    """(source, cible) pour chaque import d'un module du depot."""
    par_module = {}
    for f in fichiers:
        if f.endswith(".py"):
            par_module.setdefault(os.path.basename(f)[:-3], []).append(f)
    liens = []
    for f in fichiers:
        if not f.endswith(".py"):
            continue
        texte = lire(os.path.join(RACINE, f))
        noms = set(re.findall(r"^\s*(?:from|import)\s+([a-zA-Z_][\w]*)", texte, re.M))
        for n in noms - STDLIB:
            for cible in par_module.get(n, []):
                if cible != f:
                    liens.append((f, cible))
        # Les portes : `from plan.expose import ...` est un import pointe que le
        # motif au nom nu ne voit pas (il capture `plan`, qui n'est le nom d'aucun
        # module). Sans cette resolution, un lien bascule sur une porte SORTIRAIT
        # du graphe au lieu d'y entrer par la porte.
        for n in set(re.findall(r"^\s*(?:from|import)\s+([a-zA-Z_]\w*)\.expose\b",
                                texte, re.M)):
            cible = "scripts/%s/expose.py" % n
            if cible in fichiers and cible != f:
                liens.append((f, cible))
    return liens


def liens_node(fichiers):
    liens = []
    for f in fichiers:
        if not (f.endswith((".js", ".mjs")) and f.startswith(("serveur/", "scripts/"))):
            continue
        texte = lire(os.path.join(RACINE, f))
        for rel in re.findall(r"require\(\s*[\"'](\.[^\"']+)[\"']", texte):
            cible = os.path.normpath(os.path.join(os.path.dirname(f), rel)).replace("\\", "/")
            for essai in (cible, cible + ".js", cible + "/index.js"):
                if essai in fichiers:
                    liens.append((f, essai))
                    break
    return liens


def liens_navigateur(fichiers):
    """Les globales : qui pose `window.X`, et qui lit `X.` ailleurs."""
    front = [f for f in fichiers if f.startswith("ecrans/")]
    pose = {}
    for f in front:
        for g in re.findall(r"window\.([A-Za-z_$][\w$]*)\s*=", lire(os.path.join(RACINE, f))):
            pose.setdefault(g, f)
    liens = []
    for f in front:
        texte = lire(os.path.join(RACINE, f))
        for g, source in pose.items():
            if source == f or len(g) < 3:
                continue
            if re.search(r"\b%s\s*[.\[(]" % re.escape(g), texte):
                liens.append((f, source))
    return liens, pose


def analyser():
    declaration = charger_declaration()
    fichiers = fichiers_de_code()
    ou = rattacher(fichiers, declaration)

    tous = liens_python(fichiers) + liens_node(fichiers)
    nav, globales = liens_navigateur(fichiers)
    tous += nav

    # projection sur les containers
    arcs = {}
    hors_porte = []
    for source, cible in tous:
        a, b = ou.get(source), ou.get(cible)
        if not a or not b or a == b:
            continue
        arcs[(a, b)] = arcs.get((a, b), 0) + 1
        if cible != declaration[b]["porte"]:
            hors_porte.append((source, cible, a, b))

    # les ecarts
    orphelins = [f for f in fichiers if f not in ou]
    remontees = [(a, b, n) for (a, b), n in arcs.items()
                 if declaration[a]["rang"] <= declaration[b]["rang"]
                 and declaration[a]["rang"] != 9]
    racine_py = {f for f in fichiers
                 if f.startswith("scripts/") and f.count("/") == 1 and f.endswith(".py")}
    # La porte d'un container est l'importeur LEGITIME de ses propres commandes :
    # pendant le lot 1 (docs/organisation.md §5), c'est elle qui reexporte ce que
    # les commandes offrent, en attendant que le lot 2 les vide. Sans cette
    # exemption le compteur ne pourrait jamais atteindre zero avant le lot 2.
    porte_de = {c["porte"]: nom for nom, c in declaration.items()}
    commandes_bibliotheques = sorted(
        {cible for source, cible in tous if cible in racine_py
         and porte_de.get(source) != ou.get(cible)})

    return {
        "declaration": declaration, "ou": ou, "arcs": arcs, "globales": len(globales),
        "fichiers": len(fichiers), "orphelins": orphelins, "hors_porte": hors_porte,
        "remontees": remontees, "commandes_bibliotheques": commandes_bibliotheques,
    }


def mermaid(r):
    d, arcs = r["declaration"], r["arcs"]
    compte = {}
    for f, c in r["ou"].items():
        compte[c] = compte.get(c, 0) + 1
    lignes = ["flowchart TB"]
    for rang in sorted({c["rang"] for c in d.values()}):
        noms = [n for n, c in d.items() if c["rang"] == rang]
        lignes.append('  subgraph R%d["rang %d"]' % (rang, rang))
        lignes.append("    direction LR")
        for n in noms:
            lignes.append('    %s["%s %s<br/><i>%d fichiers</i>"]'
                          % (n, d[n]["emoji"], n, compte.get(n, 0)))
        lignes.append("  end")
    for (a, b), n in sorted(arcs.items(), key=lambda x: -x[1]):
        fleche = "-.->" if d[a]["rang"] == 9 else "-->"
        lignes.append("  %s %s|%d| %s" % (a, fleche, n, b))
    return "\n".join(lignes)


def imprimer(r):
    d = r["declaration"]
    compte = {}
    for f, c in r["ou"].items():
        compte[c] = compte.get(c, 0) + 1
    print()
    print("GRAPHE D'ARCHITECTURE — %d fichiers de code, %d containers declares"
          % (r["fichiers"], len(d)))
    print()
    print("  LES CONTAINERS")
    for n, c in sorted(d.items(), key=lambda x: (x[1]["rang"], x[0])):
        sortants = sum(v for (a, _), v in r["arcs"].items() if a == n)
        entrants = sum(v for (_, b), v in r["arcs"].items() if b == n)
        print("    rang %d  %-10s %4d fichiers   %3d liens sortants, %3d entrants"
              % (c["rang"], n, compte.get(n, 0), sortants, entrants))
    print()
    print("  LES LIENS (source -> cible : nombre de references)")
    for (a, b), n in sorted(r["arcs"].items(), key=lambda x: -x[1]):
        marque = "  ⚠ remontee" if d[a]["rang"] <= d[b]["rang"] and d[a]["rang"] != 9 else ""
        print("    %-10s -> %-10s %4d%s" % (a, b, n, marque))
    print()
    print("  LES ECARTS A LA CIBLE")
    print("    orphelins (aucun container ne les reclame) : %d" % len(r["orphelins"]))
    for f in r["orphelins"][:12]:
        print("        %s" % f)
    if len(r["orphelins"]) > 12:
        print("        … et %d autres" % (len(r["orphelins"]) - 12))
    print("    liens hors porte                           : %d" % len(r["hors_porte"]))
    print("    dependances qui remontent                  : %d" % len(r["remontees"]))
    print("    commandes racine importees comme modules   : %d"
          % len(r["commandes_bibliotheques"]))
    for f in r["commandes_bibliotheques"]:
        print("        %s" % f)
    print()


def document(r):
    """Le markdown de docs/graphe-archi.md — GENERE, jamais edite a la main."""
    d, ou = r["declaration"], r["ou"]
    par_container = {}
    for f, c in ou.items():
        par_container.setdefault(c, []).append(f)

    L = ["# Le graphe d'architecture — **généré**, jamais écrit à la main",
         "",
         "> Produit par `python scripts/analyse/graphe_archi.py --doc` en lisant les",
         "> imports Python, les `require` Node et les globales du navigateur, projetés",
         "> sur la déclaration de [`containers.json`](containers.json). **Ne pas éditer :**",
         "> toute correction se fait dans la déclaration ou dans le code, et l'on régénère.",
         "",
         "Les intentions et les lois sont dans [`organisation.md`](organisation.md) ;",
         "les boucles du jeu dans [`architecture.md`](architecture.md).",
         "",
         "## Les containers et leurs liens", "", "```mermaid", mermaid(r), "```", "",
         "## Le tableau des liens", "",
         "| de | vers | références | |", "|---|---|---:|---|"]
    for (a, b), n in sorted(r["arcs"].items(), key=lambda x: -x[1]):
        remonte = d[a]["rang"] <= d[b]["rang"] and d[a]["rang"] != 9
        L.append("| `%s` | `%s` | %d | %s |" % (a, b, n, "⚠️ remontée" if remonte else ""))

    L += ["", "## Les modules, par container", ""]
    for nom, c in sorted(d.items(), key=lambda x: (x[1]["rang"], x[0])):
        fichiers = sorted(par_container.get(nom, []),
                          key=lambda f: -len(lire(os.path.join(RACINE, f)).splitlines()))
        lignes_total = sum(len(lire(os.path.join(RACINE, f)).splitlines()) for f in fichiers)
        L += ["### %s %s — rang %d" % (c["emoji"], nom, c["rang"]), "",
              "*%s*" % c["intention"], "",
              "**%d fichiers, %d lignes.** Porte : `%s`" % (len(fichiers), lignes_total, c["porte"]),
              ""]
        for racine in ("scripts/", "serveur/", "ecrans/"):
            lot = [f for f in fichiers if f.startswith(racine)]
            if not lot:
                continue
            tetes = ", ".join("`%s`" % os.path.basename(f) for f in lot[:9])
            reste = " … et %d autres" % (len(lot) - 9) if len(lot) > 9 else ""
            L.append("- **%s** (%d) — %s%s" % (racine, len(lot), tetes, reste))
        L.append("")

    L += ["## Les écarts à la cible", "",
          "| écart | compte | ce que ça veut dire |", "|---|---:|---|",
          "| orphelins | %d | un fichier qu'aucun container ne réclame |" % len(r["orphelins"]),
          "| liens hors porte | %d | un lien qui entre ailleurs que par la porte |" % len(r["hors_porte"]),
          "| dépendances qui remontent | %d | violation de la loi 2 (rangs) |" % len(r["remontees"]),
          "| commandes-bibliothèques | %d | une commande racine importée comme module |"
          % len(r["commandes_bibliotheques"]), "",
          "Ces quatre chiffres ne doivent que **descendre**. Ils sont la distance entre",
          "la cible déclarée et le câblage réel — le chantier, en nombres.", ""]
    if r["commandes_bibliotheques"]:
        L += ["### Les commandes qui sont aussi des bibliothèques", ""]
        L += ["- `%s`" % f for f in r["commandes_bibliotheques"]]
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    resultat = analyser()
    if "--doc" in sys.argv:
        chemin = os.path.join(RACINE, "docs", "graphe-archi.md")
        with io.open(chemin, "w", encoding="utf-8") as fh:
            fh.write(document(resultat))
        print("ecrit : docs/graphe-archi.md")
    elif "--mermaid" in sys.argv:
        print(mermaid(resultat))
    else:
        if "--json" in sys.argv:
            sortie = dict(resultat)
            sortie["arcs"] = [{"de": a, "vers": b, "n": n} for (a, b), n in resultat["arcs"].items()]
            sortie["hors_porte"] = [list(x) for x in resultat["hors_porte"]]
            sortie["remontees"] = [list(x) for x in resultat["remontees"]]
            del sortie["ou"]
            print(json.dumps(sortie, ensure_ascii=False, indent=2))
        else:
            imprimer(resultat)
        # Le code de sortie dit si la distance a la cible est nulle. C'est la
        # convention des MESURES de verifier.mjs : non-zero tant que l'ecart de
        # fond persiste, zero le jour ou la mesure peut monter en garde. Les
        # modes generateurs (--doc, --mermaid) ne sont pas des sondes et
        # sortent toujours en 0.
        ecarts = (len(resultat["orphelins"]) + len(resultat["hors_porte"])
                  + len(resultat["remontees"]) + len(resultat["commandes_bibliotheques"]))
        sys.exit(1 if ecarts else 0)
