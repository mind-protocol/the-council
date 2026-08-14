#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fils.py — ce qui court, et qui tient la plume dessus.

Un fil est une affaire en cours qui porte un nom d'homme et une echeance. Il vit
dans etat/joueurs/<siege>/fils.json, donc PAR SIEGE. Le mode ne change jamais le
calcul : seulement par ou ca passe. mode=joue -> ca se joue en scene ;
mode=delegue -> ca tourne hors champ et revient en UNE LIGNE au passe.

Doctrine et format : docs/fils.md.

    python scripts/fils.py                       # tous les sieges
    python scripts/fils.py --qui rhaenyra
    python scripts/fils.py --qui rhaenyra --mode fil-plancher-garnison delegue
    python scripts/fils.py --qui rhaenyra --poser "Le pli d'Accalmie" --sur gerardys \
        --echeance 129.4.2 --detail "parti le 27e, pas de reponse"
    python scripts/fils.py --qui rhaenyra --clore fil-quatre-sceaux
"""
import argparse
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
JOURS_PAR_LUNE = 30
CONDITIONS = ("parole", "cout", "froisse", "contredit")

LISEZ_MOI = (
    "Les fils : ce qui court, avec le nom de l homme dessus et QUI TIENT LA PLUME. "
    "mode=joue -> ca se joue en scene ; mode=delegue -> ca tourne hors champ et revient "
    "en UNE LIGNE au passe. Un fil sans `sur` ne se delegue pas : il revient a la main du "
    "joueur. Un fil delegue ne remonte QUE si remonte_si s arme (parole, cout, froisse, "
    "contredit) - et alors il remonte dans la SCENE, en `demande`, jamais dans le rail. "
    "Format : docs/fils.md."
)


def chemin(siege):
    return os.path.join(ETAT, "joueurs", siege, "fils.json")


def sieges():
    d = os.path.join(ETAT, "joueurs")
    if not os.path.isdir(d):
        return []
    return sorted(x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x)))


def lire(siege):
    p = chemin(siege)
    if not os.path.exists(p):
        return {"_lisez_moi": LISEZ_MOI, "fils": []}
    with open(p, encoding="utf-8") as f:
        doc = json.load(f)
    doc.setdefault("fils", [])
    return doc


def ecrire(siege, doc):
    doc["_lisez_moi"] = LISEZ_MOI
    with open(chemin(siege), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)


def noms():
    try:
        with open(os.path.join(ETAT, "personnages.json"), encoding="utf-8") as f:
            return {p["id"]: p["nom"].split(",")[0].strip() for p in json.load(f)}
    except Exception:
        return {}


def horloge(siege):
    try:
        with open(os.path.join(ETAT, "horloges.json"), encoding="utf-8") as f:
            h = json.load(f)
        if siege in h:
            return h[siege]
    except Exception:
        pass
    try:
        with open(os.path.join(ETAT, "monde.json"), encoding="utf-8") as f:
            return json.load(f).get("date")
    except Exception:
        return None


def en_jours(d):
    if not d:
        return None
    return (d["annee"] * 12 + (d["lune"] - 1)) * JOURS_PAR_LUNE + d["jour"]


def delai(f, aujourdhui):
    a, b = en_jours(aujourdhui), en_jours(f.get("echeance"))
    if a is None or b is None:
        return "sans echeance"
    n = b - a
    if n < 0:
        return "EN RETARD de %d j" % -n
    if n == 0:
        return "aujourd hui"
    if n == 1:
        return "demain"
    return "dans %d j" % n


def parse_date(s):
    """129.4.2 ou 129.4.2.720 -> dict."""
    m = [int(x) for x in s.split(".")]
    d = {"annee": m[0], "lune": m[1], "jour": m[2]}
    if len(m) > 3:
        d["minute"] = m[3]
    return d


def slug(titre):
    out = []
    for c in titre.lower():
        out.append(c if c.isalnum() else "-")
    return "fil-" + "-".join(x for x in "".join(out).split("-") if x)[:60]


def montrer(siege, N):
    doc = lire(siege)
    fils = [f for f in doc["fils"] if f.get("statut", "en-cours") == "en-cours"]
    aujourdhui = horloge(siege)
    print("\n== %s  (%d fil%s)" % (siege, len(fils), "s" if len(fils) > 1 else ""))
    if not fils:
        print("   rien ne court")
        return
    fils.sort(key=lambda f: (f.get("mode") != "joue", en_jours(f.get("echeance")) or 10 ** 9))
    for f in fils:
        mode = "delegue" if f.get("mode") == "delegue" else "JOUE   "
        sur = N.get(f.get("sur"), (f.get("sur") or "").replace("-", " ")) or "SUR PERSONNE"
        print("  %-8s %-22s %-16s %s" % (mode, sur[:22], delai(f, aujourdhui), f.get("titre", "")))
        print("           %s" % f.get("id"))
        if f.get("mode") == "delegue":
            manque = [c for c in f.get("remonte_si", []) if c not in CONDITIONS]
            if manque:
                print("           !! condition hors format : %s" % ", ".join(manque))
            if not f.get("remonte_si"):
                print("           !! delegue SANS remonte_si — il ne frappera jamais")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--qui", help="le siege (rhaenyra, aurore-inchauspe...)")
    ap.add_argument("--mode", nargs=2, metavar=("FIL_ID", "MODE"),
                    help="basculer un fil : joue | delegue")
    ap.add_argument("--poser", metavar="TITRE", help="ouvrir un fil")
    ap.add_argument("--sur", help="l id du personnage sur qui l affaire tombe")
    ap.add_argument("--detail", default="")
    ap.add_argument("--echeance", help="129.4.2 ou 129.4.2.720")
    ap.add_argument("--remonte-si", default="parole,cout",
                    help="conditions separees par des virgules : %s" % ", ".join(CONDITIONS))
    ap.add_argument("--clore", metavar="FIL_ID")
    ap.add_argument("--dernier", nargs=2, metavar=("FIL_ID", "TEXTE"),
                    help="la derniere ligne rendue au passe")
    a = ap.parse_args()

    ecrit = a.mode or a.poser or a.clore or a.dernier
    if ecrit and not a.qui:
        sys.exit("il faut --qui : un fil appartient a un siege")

    if not ecrit:
        N = noms()
        for s in ([a.qui] if a.qui else sieges()):
            if os.path.exists(chemin(s)) or a.qui:
                montrer(s, N)
        return

    doc = lire(a.qui)

    if a.poser:
        conds = [c.strip() for c in a.remonte_si.split(",") if c.strip()]
        mauvais = [c for c in conds if c not in CONDITIONS]
        if mauvais:
            sys.exit("condition inconnue : %s (attendu : %s)" % (", ".join(mauvais), ", ".join(CONDITIONS)))
        f = {
            "id": slug(a.poser), "titre": a.poser, "detail": a.detail,
            "sur": a.sur, "echeance": parse_date(a.echeance) if a.echeance else None,
            "mode": "joue", "statut": "en-cours", "remonte_si": conds,
            "depuis": horloge(a.qui), "dernier": "",
        }
        doc["fils"] = [x for x in doc["fils"] if x.get("id") != f["id"]] + [f]
        ecrire(a.qui, doc)
        print("pose : %s (%s)" % (f["id"], a.qui))
        return

    cible = (a.mode[0] if a.mode else a.clore or a.dernier[0])
    f = next((x for x in doc["fils"] if x.get("id") == cible), None)
    if not f:
        sys.exit("fil inconnu chez %s : %s" % (a.qui, cible))

    if a.mode:
        m = a.mode[1]
        if m not in ("joue", "delegue"):
            sys.exit("mode : joue | delegue")
        # Un fil sur personne ne se delegue pas : il n y a personne pour le tenir.
        if m == "delegue" and not f.get("sur"):
            sys.exit("« %s » n est sur personne — nomme d abord un homme (--sur)." % f["titre"])
        f["mode"] = m
        print("%s -> %s" % (f["titre"], m))
    elif a.clore:
        f["statut"] = "clos"
        print("clos : %s" % f["titre"])
    else:
        f["dernier"] = a.dernier[1]
        print("dernier : %s" % f["titre"])

    ecrire(a.qui, doc)


if __name__ == "__main__":
    main()
