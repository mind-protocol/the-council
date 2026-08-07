# -*- coding: utf-8 -*-
"""Les sieges — s'asseoir dans un personnage, en quitter un.

    python scripts/sieges.py                          # l'etat des sieges
    python scripts/sieges.py --quitter rhaenyra --vraiment
    python scripts/sieges.py --asseoir marlo-vasse --vraiment

Un siege est une entree de `etat/joueurs.json`. Son champ `occupe` dit si
quelqu'un est ASSIS dedans en ce moment, et de la decoule toute la regle :

  siege OCCUPE  -> pas d'entree dans intentions.json. Sa tete appartient au
                   joueur ; si le MJ lui en ecrit une, il joue a sa place.
  siege VACANT  -> une entree dans intentions.json, obligatoirement. Un
                   personnage sans tete n'agit pas hors ecran : il ne decide
                   rien, ne poursuit rien, ne repond a rien. Quitter Rhaenyra
                   sans lui en ecrire une, c'est la mettre en sommeil pendant
                   qu'on regarde ailleurs — et l'on ne s'en apercoit qu'en
                   revenant s'asseoir, trois lunes trop tard.

Ce script ne fait que la mecanique — basculer le champ, retirer la tete d'un
siege qu'on occupe, refuser d'en quitter un qui n'en a pas. La tete elle-meme
s'ECRIT a la main : ce que le personnage veut, croit et poursuit pendant son
absence est un acte de jeu, pas une transformation de fichier.

Rien n'est ecrit sans `--vraiment` : sans le drapeau, on dit seulement ce qui
se passerait. La tete retiree n'est jamais perdue — elle part dans
`etat/archive/tetes/` avec sa date, pour qu'on puisse la relire ou la remettre.
"""
from __future__ import print_function

import argparse
import datetime
import io
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")


def lire(nom, defaut):
    chemin = os.path.join(ETAT, nom + ".json")
    if not os.path.exists(chemin):
        return defaut
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


def ecrire(nom, donnees):
    chemin = os.path.join(ETAT, nom + ".json")
    with io.open(chemin, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)
        f.write(u"\n")


def tetes():
    """intentions.json indexe par personnage_id."""
    index = {}
    for tete in lire("intentions", []):
        pid = tete.get("personnage_id")
        if pid:
            index.setdefault(pid, tete)
    return index


def horodatage():
    d = lire("monde", {}).get("date") or {}
    if d:
        return "{}-{}-{}".format(d.get("annee"), d.get("lune"), d.get("jour"))
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def etat_des_sieges():
    roster = lire("joueurs", [])
    index = tetes()
    lignes = []
    for siege in roster:
        pid = siege.get("personnage_id")
        occupe = siege.get("occupe", True)
        a_tete = pid in index
        if occupe and a_tete:
            ennui = "FAUTE : occupe ET une tete — le MJ le joue a votre place"
        elif not occupe and not a_tete:
            ennui = "FAUTE : vacant SANS tete — il n'agira pas hors ecran"
        else:
            ennui = ""
        lignes.append((pid, siege.get("nom") or pid, occupe, a_tete, ennui))
    return roster, index, lignes


def imprimer(lignes):
    if not lignes:
        print("aucun siege dans etat/joueurs.json")
        return
    largeur = max(len(l[0] or "") for l in lignes)
    for pid, nom, occupe, a_tete, ennui in lignes:
        print("  {:<{w}}  {:<8} {:<16} {}".format(
            pid or "?",
            "assis" if occupe else "vacant",
            "tete ecrite" if a_tete else "sans tete",
            ennui, w=largeur))


def basculer(cible, vers_occupe, vraiment):
    roster, index, _ = etat_des_sieges()
    siege = None
    for s in roster:
        if s.get("personnage_id") == cible:
            siege = s
            break
    if siege is None:
        sys.exit("aucun siege pour '{}' dans etat/joueurs.json".format(cible))

    deja = siege.get("occupe", True)
    if deja == vers_occupe:
        print("{} est deja {}.".format(
            cible, "occupe" if deja else "vacant"))
        return

    if not vers_occupe and cible not in index:
        sys.exit(
            "REFUS : quitter '{}' le laisserait sans tete dans "
            "intentions.json.\n"
            "Ecrivez-lui d'abord ce qu'il veut, croit et poursuit pendant "
            "votre absence\n"
            "(echelle, croyances, ignore, etapes chiffrees, declencheurs), "
            "puis relancez.\n"
            "Un personnage sans tete ne fait RIEN hors ecran — ce n'est pas "
            "un detail de forme.".format(cible))

    actions = ["{} : {} -> {}".format(
        cible, "assis" if deja else "vacant",
        "assis" if vers_occupe else "vacant")]

    tete = index.get(cible)
    if vers_occupe and tete is not None:
        actions.append(
            "retirer sa tete d'intentions.json (archivee dans "
            "etat/archive/tetes/{}-{}.json)".format(cible, horodatage()))
    if not vers_occupe:
        actions.append("sa tete reste en place : il agit desormais seul")

    for a in actions:
        print("  " + a)
    if not vraiment:
        print("\n(rien n'a ete ecrit — ajoutez --vraiment)")
        return

    if vers_occupe and tete is not None:
        dossier = os.path.join(ETAT, "archive", "tetes")
        if not os.path.isdir(dossier):
            os.makedirs(dossier)
        chemin = os.path.join(
            dossier, "{}-{}.json".format(cible, horodatage()))
        with io.open(chemin, "w", encoding="utf-8") as f:
            json.dump(tete, f, ensure_ascii=False, indent=2)
            f.write(u"\n")
        ecrire("intentions", [t for t in lire("intentions", [])
                              if t.get("personnage_id") != cible])

    siege["occupe"] = vers_occupe
    ecrire("joueurs", roster)
    print("\necrit.")
    if vers_occupe:
        print("Pensez a relire son dossier avant de jouer : "
              "etat/joueurs/{}/".format(cible))


def main():
    ap = argparse.ArgumentParser(
        description="L'etat des sieges, et comment on en change.")
    ap.add_argument("--asseoir", metavar="PERSONNAGE_ID",
                    help="s'asseoir dedans : le joueur le prend en main, "
                         "sa tete quitte intentions.json")
    ap.add_argument("--quitter", metavar="PERSONNAGE_ID",
                    help="le quitter : il redevient un PNJ et doit deja "
                         "avoir une tete dans intentions.json")
    ap.add_argument("--vraiment", action="store_true",
                    help="ecrire pour de bon")
    args = ap.parse_args()

    if args.asseoir and args.quitter:
        if args.asseoir == args.quitter:
            sys.exit("--asseoir et --quitter sur le meme siege")
        basculer(args.quitter, False, args.vraiment)
        print("")
        basculer(args.asseoir, True, args.vraiment)
    elif args.asseoir:
        basculer(args.asseoir, True, args.vraiment)
    elif args.quitter:
        basculer(args.quitter, False, args.vraiment)
    else:
        _, _, lignes = etat_des_sieges()
        imprimer(lignes)


if __name__ == "__main__":
    main()
