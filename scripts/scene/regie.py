# -*- coding: utf-8 -*-
"""REGIE — l'outil du MJ de Corneille : retrouver un moment dans le fil.

    python scripts/regie.py --chercher "steffon arrive"
    python scripts/regie.py --chercher "les prisonniers" --max 20
    python scripts/regie.py --autour 7412            # ce qu'il y a autour

POURQUOI CE FICHIER EXISTE. Corneille est un siege de REGIE : il ne joue
personne, il regarde, et ce qu'il demande le plus souvent est « emmene-moi au
moment ou X est arrive ». Le fil fait huit mille lignes ; personne ne les
remonte a la molette. Ce script rend les endroits ou la chose est dite, avec
leur date, leur lieu et trois lignes autour.

CE QU'IL NE FAIT PAS, ET C'EST VOULU : il ne CHOISIT pas. « Le moment ou
Steffon est arrive » n'est pas une chaine de caracteres, c'est un jugement sur
ce qui compte — la premiere occurrence du mot est presque toujours la
mauvaise. Le script donne les candidats, le MJ lit, le MJ tranche, puis il
pousse la tranche a Corneille :

    python scripts/append_flux.py --pour corneille \\
      '{"type":"extrait","titre":"L arrivee de ser Steffon","de":7412,"a":7440}'

La page de Corneille rouvre alors le fil a cet endroit, tel qu'il a ete joue.
Rien n'est rejoue dans la scene en cours, aucune horloge ne bouge, rien
n'entre dans etat/ : la regie est hors fiction de bout en bout.
"""
from __future__ import print_function

import io
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLUX = os.path.join(RACINE, "etat", "flux.jsonl")


def lire_flux():
    items = []
    try:
        with io.open(FLUX, encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne:
                    continue
                try:
                    items.append(json.loads(ligne))
                except ValueError:
                    items.append({})
    except IOError:
        pass
    return items


def dire_date(d):
    if not d:
        return "date inconnue"
    heure = ""
    if isinstance(d.get("minute"), int):
        heure = " %dh%02d" % (d["minute"] // 60, d["minute"] % 60)
    return "%s AC %se lune j%s%s" % (d.get("annee"), d.get("lune"),
                                     d.get("jour"), heure)


def contexte(items):
    """(date, lieu) courants a chaque index : ils ne sont pas sur chaque item."""
    date, lieu = None, ""
    out = []
    for it in items:
        if it.get("date"):
            date = it["date"]
        if it.get("lieu"):
            lieu = it["lieu"]
        out.append((date, lieu))
    return out


def chercher(besoin, maximum):
    items = lire_flux()
    ctx = contexte(items)
    mots = [m for m in besoin.lower().split() if len(m) > 2]
    trouves = []
    for i, it in enumerate(items):
        t = (it.get("texte") or "").lower()
        if not t:
            continue
        if mots:
            if not all(m in t for m in mots):
                continue
        elif besoin.lower() not in t:
            continue
        trouves.append(i)
    if not trouves:
        print("rien pour « %s » dans %d lignes de fil." % (besoin, len(items)))
        return
    print("%d endroit(s) pour « %s » — les %d derniers :"
          % (len(trouves), besoin, min(maximum, len(trouves))))
    for i in trouves[-maximum:][::-1]:
        it = items[i]
        date, lieu = ctx[i]
        qui = it.get("locuteur_id") or it.get("acteur_id") or ""
        print("\n  [%d] %s · %s%s" % (i, dire_date(date), lieu or "—",
                                      (" · " + qui) if qui else ""))
        print("      %s : %s" % (it.get("type"),
                                 (it.get("texte") or "")[:200].replace("\n", " ")))
    print("\n  Pour l'emmener la :")
    print("    python scripts/append_flux.py --pour corneille \\")
    print("      '{\"type\":\"extrait\",\"titre\":\"...\",\"de\":<i-5>,\"a\":<i+20>}'")


def autour(i, marge):
    items = lire_flux()
    ctx = contexte(items)
    for k in range(max(0, i - marge), min(len(items), i + marge + 1)):
        it = items[k]
        date, lieu = ctx[k]
        marque = ">>" if k == i else "  "
        qui = it.get("locuteur_id") or it.get("acteur_id") or ""
        print("%s [%d] %s %s %s | %s" % (
            marque, k, dire_date(date), it.get("type"), qui,
            (it.get("texte") or "")[:120].replace("\n", " ")))


def main(argv):
    if "--chercher" in argv:
        i = argv.index("--chercher")
        besoin = argv[i + 1] if len(argv) > i + 1 else ""
        maximum = 12
        if "--max" in argv:
            maximum = int(argv[argv.index("--max") + 1])
        if not besoin:
            sys.exit("--chercher quoi ?")
        return chercher(besoin, maximum)
    if "--autour" in argv:
        i = argv.index("--autour")
        marge = 10
        if "--marge" in argv:
            marge = int(argv[argv.index("--marge") + 1])
        return autour(int(argv[i + 1]), marge)
    print(__doc__)


