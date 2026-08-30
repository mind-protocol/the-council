#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Les mesures de docs/audit-technique.md, rejouables en une commande.

    python scripts/analyse/audit_technique.py

LECTURE SEULE, ET IL LE FAUT. Rien n'est ecrit, rien n'est importe : l'audit
mesure un depot, il ne le touche pas. Aucun script du depot n'est importe non
plus — la passe du 30e jour a appris que charger un script pour voir s'il se
charge peut reinitialiser etat/flux.jsonl.

POURQUOI CE FICHIER PLUTOT QU'UN TEXTE. Un audit chiffre se perime des que le
depot bouge, et le depot bouge tous les jours. Un instantane en prose oblige a
tout re-explorer ; celui-ci recrache les vingt chiffres du document, et la mise
a jour redevient une lecture. Chaque mesure porte le numero de la section
qu'elle alimente : un ecart entre cette sortie et le texte est un texte perime,
pas une mesure fausse.

Sortie : un tableau lisible, plus --json pour comparer deux passages.
"""

import json
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def git(*args):
    """Une commande git dans le depot, en texte. Jamais d'ecriture."""
    sortie = subprocess.run(
        ["git"] + list(args), cwd=RACINE, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    return sortie.stdout


def suivis(*motifs):
    """Les fichiers suivis correspondant aux motifs, hors vendor et caches."""
    lignes = git("ls-files", *motifs).splitlines()
    return [f for f in lignes if "vendor/" not in f and "__pycache__" not in f]


def lignes_de(chemin):
    plein = os.path.join(RACINE, chemin)
    try:
        with open(plein, encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def octets_de(chemin):
    try:
        return os.path.getsize(os.path.join(RACINE, chemin))
    except OSError:
        return 0


def mesurer():
    m = {}
    m["commit"] = git("rev-parse", "--short", "HEAD").strip()
    m["date_commit"] = git("log", "-1", "--format=%ad", "--date=short").strip()

    # -- §1 taille et decoupage -------------------------------------------
    code = suivis("*.py", "*.js", "*.mjs")
    tailles = sorted(((lignes_de(f), f) for f in code), reverse=True)
    m["fichiers_code"] = len(code)
    m["lignes_code"] = sum(n for n, _ in tailles)
    m["sur_500"] = sum(1 for n, _ in tailles if n > 500)
    m["sur_1000"] = sum(1 for n, _ in tailles if n > 1000)
    m["sur_2000"] = sum(1 for n, _ in tailles if n > 2000)
    m["plus_gros"] = [{"f": f, "l": n} for n, f in tailles[:8]]

    # le monolithe : sa taille, ses fonctions, sa plus longue fonction
    mono = "ecrans/modules/bataille2d.js"
    m["monolithe"] = {"f": mono, "l": lignes_de(mono)}
    plein = os.path.join(RACINE, mono)
    if os.path.exists(plein):
        with open(plein, encoding="utf-8", errors="replace") as fh:
            src = fh.readlines()
        depuis = [(i, l) for i, l in enumerate(src) if re.match(r"^  function [A-Za-z_$]", l)]
        longues = []
        for k, (i, l) in enumerate(depuis):
            fin = depuis[k + 1][0] if k + 1 < len(depuis) else len(src)
            longues.append((fin - i, l.strip().rstrip(" {")))
        longues.sort(reverse=True)
        m["monolithe"]["fonctions"] = len(depuis)
        m["monolithe"]["plus_longue"] = (
            {"nom": longues[0][1], "l": longues[0][0]} if longues else None
        )
        champs = set(re.findall(r"\bh\.([A-Za-z_$][\w$]*)", "".join(src)))
        m["monolithe"]["champs_sur_h"] = len(champs)

    # -- §2 frontieres de module ------------------------------------------
    front = [f for f in code if f.startswith("ecrans/")]
    esm = 0
    for f in front:
        plein = os.path.join(RACINE, f)
        try:
            with open(plein, encoding="utf-8", errors="replace") as fh:
                if re.search(r"^(import|export) ", fh.read(), re.M):
                    esm += 1
        except OSError:
            pass
    m["front_fichiers"] = len(front)
    m["front_esm"] = esm
    m["front_globals"] = len(front) - esm
    globales = set()
    for f in front:
        try:
            with open(os.path.join(RACINE, f), encoding="utf-8", errors="replace") as fh:
                globales.update(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*=", fh.read()))
        except OSError:
            pass
    m["globales_window"] = len(globales)
    for page in ("ecrans/jeu.html", "ecrans/bataille.html"):
        try:
            with open(os.path.join(RACINE, page), encoding="utf-8", errors="replace") as fh:
                texte = fh.read()
            m.setdefault("balises_script", {})[os.path.basename(page)] = texte.count("<script src=")
            m.setdefault("cache_manuel", {})[os.path.basename(page)] = len(re.findall(r"\?v=", texte))
        except OSError:
            pass

    # -- §3 verification ---------------------------------------------------
    bancs = suivis("ecrans/modules/bataille/banc-*.js")
    m["bancs"] = len(bancs)
    attaches = []
    for f in bancs:
        try:
            with open(os.path.join(RACINE, f), encoding="utf-8", errors="replace") as fh:
                if "localhost:3" in fh.read():
                    attaches.append(os.path.basename(f))
        except OSError:
            pass
    m["bancs_lies_au_serveur"] = attaches
    m["tests_python"] = len(suivis("scripts/**/test_*.py", "scripts/test_*.py"))
    m["config_projet"] = {
        n: os.path.exists(os.path.join(RACINE, n))
        for n in ("package.json", "pyproject.toml", "Makefile", ".github")
    }
    py = suivis("scripts/**/*.py", "scripts/*.py")
    m["sys_path_inserts"] = sum(
        1 for f in py
        if "sys.path" in open(os.path.join(RACINE, f), encoding="utf-8", errors="replace").read()
    )

    # -- §4 ecrivains de etat/ --------------------------------------------
    ecrivains, lire_json = [], []
    for f in py:
        texte = open(os.path.join(RACINE, f), encoding="utf-8", errors="replace").read()
        if re.search(r"json\.dump|open\([^)]*[\"']w", texte) and "etat" in texte:
            ecrivains.append(f)
        if "def lire_json" in texte:
            lire_json.append(f)
    m["ecrivains_etat"] = len(ecrivains)
    m["lire_json_definitions"] = lire_json
    m["fichiers_python"] = len(py)

    # -- §5 poids du depot -------------------------------------------------
    avant = [f for f in git("ls-files").splitlines() if ".avant" in f]
    m["sauvegardes_avant"] = len(avant)
    m["sauvegardes_mo"] = round(sum(octets_de(f) for f in avant) / 1048576, 1)
    binaires = git("ls-files", "*.mp3", "*.png", "*.jpg", "*.blend*", "*.bin",
                   "*.m4a", "*.pdf").splitlines()
    m["binaires"] = len(binaires)
    m["binaires_mo"] = round(sum(octets_de(f) for f in binaires) / 1048576, 1)
    m["commits"] = int(git("rev-list", "--count", "HEAD").strip() or 0)
    m["fichiers_suivis"] = len(git("ls-files").splitlines())

    # -- §6 documentation --------------------------------------------------
    claudes = [f for f in git("ls-files").splitlines() if f.endswith("CLAUDE.md")]
    m["claude_md"] = {"n": len(claudes), "ou": claudes}
    m["claude_md_racine_octets"] = octets_de("CLAUDE.md")
    m["agents_md_octets"] = octets_de("AGENTS.md")
    m["fiches_combat"] = len([f for f in git("ls-files", "docs/combat/*").splitlines()])
    return m


def imprimer(m):
    print()
    print("AUDIT TECHNIQUE — %s (%s)" % (m["commit"], m["date_commit"]))
    print()
    print("  §1 taille      %d fichiers, %d lignes ; %d > 500 l. (%d%%), %d > 1000, %d > 2000"
          % (m["fichiers_code"], m["lignes_code"], m["sur_500"],
             round(m["sur_500"] * 100.0 / max(m["fichiers_code"], 1)), m["sur_1000"], m["sur_2000"]))
    for g in m["plus_gros"][:4]:
        print("                 %6d  %s" % (g["l"], g["f"]))
    mono = m.get("monolithe", {})
    if mono.get("plus_longue"):
        print("     monolithe   %d l., %d fonctions, %d champs sur h ; la plus longue : %s (%d l.)"
              % (mono["l"], mono["fonctions"], mono["champs_sur_h"],
                 mono["plus_longue"]["nom"], mono["plus_longue"]["l"]))
    print("  §2 frontieres  %d fichiers front : %d ESM / %d globales-IIFE ; %d globales window.*"
          % (m["front_fichiers"], m["front_esm"], m["front_globals"], m["globales_window"]))
    print("                 balises <script> : %s ; ?v= manuels : %s"
          % (m.get("balises_script"), m.get("cache_manuel")))
    print("  §3 verif       %d bancs, dont %d lies a un serveur : %s"
          % (m["bancs"], len(m["bancs_lies_au_serveur"]), ", ".join(m["bancs_lies_au_serveur"])))
    print("                 %d tests python pour %d fichiers ; sys.path.insert : %d"
          % (m["tests_python"], m["fichiers_python"], m["sys_path_inserts"]))
    print("                 config : %s" % m["config_projet"])
    print("  §4 etat/       %d ecrivains ; lire_json defini %d fois : %s"
          % (m["ecrivains_etat"], len(m["lire_json_definitions"]),
             ", ".join(os.path.basename(f) for f in m["lire_json_definitions"])))
    print("  §5 poids       %d sauvegardes .avant-* (%s Mo) ; %d binaires (%s Mo) ; %d fichiers suivis, %d commits"
          % (m["sauvegardes_avant"], m["sauvegardes_mo"], m["binaires"],
             m["binaires_mo"], m["fichiers_suivis"], m["commits"]))
    print("  §6 docs        %d CLAUDE.md ; racine %d Ko, AGENTS.md %d Ko ; %d fiches docs/combat/"
          % (m["claude_md"]["n"], m["claude_md_racine_octets"] // 1024,
             m["agents_md_octets"] // 1024, m["fiches_combat"]))
    print()


if __name__ == "__main__":
    mesures = mesurer()
    if "--json" in sys.argv:
        print(json.dumps(mesures, ensure_ascii=False, indent=2))
    else:
        imprimer(mesures)
