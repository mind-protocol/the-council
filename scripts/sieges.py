# -*- coding: utf-8 -*-
"""Les sieges — s'asseoir dans un personnage, en quitter un.

    python scripts/sieges.py                          # l'etat des sieges
    python scripts/sieges.py --quitter rhaenyra --vraiment
    python scripts/sieges.py --asseoir marlo-vasse --vraiment

Un siege est une entree de `etat/joueurs.json`. Etre ASSIS dedans ne se
DECLARE plus : ça se MESURE (`scripts/occupation.py`) — la veille de sa session
date de moins de deux heures reelles, ou son inbox porte une action non traitee.
Le champ `occupe` du fichier n'est plus que le CACHE de ce calcul ; ce script le
recale a chaque passage. C'est la reparation du 10 aout : les quatre sieges
etaient restes a `true` depuis la veille, deux d'entre eux n'etaient plus joues,
et personne ne pouvait le voir puisque l'etat restait coherent avec lui-meme.

De l'etat assis ou vacant decoule toute la regle :

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
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from temps.expose import occupation  # QUI EST ASSIS — la mesure, pas le drapeau
from temps.expose import regence  # ce que le siege a decide seul pendant l'absence
from etat.expose import tables  # LA PORTE de etat/ : une lecture, une ecriture, une semantique d'erreur

lire = tables.lire      # absent -> defaut ; corrompu -> plante, jamais un defaut
ecrire = tables.ecrire  # atomique (os.replace) : jamais un fichier a moitie ecrit


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
    """Le roster, l'index des tetes, et la MESURE de chaque siege.

    On ne rend plus le drapeau `occupe` : c'est lui qui a menti pendant deux
    jours. Chaque ligne porte ce qui a ete mesure et POURQUOI — l'age de la
    veille, le compte de l'inbox —, parce qu'un verdict qu'on ne peut pas
    verifier a l'oeil est exactement ce qui a induit en erreur.
    """
    roster = lire("joueurs", [])
    index = tetes()
    return roster, index, occupation.mesures()


def imprimer(mesures):
    if not mesures:
        print("aucun siege dans etat/joueurs.json")
        return
    occupation.imprimer(mesures)


def basculer(cible, vers_occupe, vraiment):
    roster, index, _ = etat_des_sieges()
    siege = None
    for s in roster:
        if s.get("personnage_id") == cible:
            siege = s
            break
    if siege is None:
        sys.exit("aucun siege pour '{}' dans etat/joueurs.json".format(cible))

    # LA MESURE FAIT FOI, pas le drapeau. Si le fichier dit « occupe » et que
    # plus rien ne respire depuis dix heures, le siege est vacant, un point
    # c'est tout — et c'est le cas qu'on repare.
    mesure = occupation.mesurer(siege, tetes=set(index))
    deja = mesure["occupe"]
    if mesure["derive"]:
        print("  (le cache disait '{}' ; mesure : {} — {})".format(
            "occupe" if mesure["cache"] else "vacant",
            "assis" if deja else "vacant", mesure["raison"]))
    if deja == vers_occupe:
        print("{} est deja {} ({}).".format(
            cible, "assis" if deja else "vacant", mesure["raison"]))
        if mesure["derive"]:
            occupation.rafraichir(vraiment)
            print("  cache recale." if vraiment
                  else "  (cache a recaler — ajoutez --vraiment)")
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
    actions.append(
        "marquer {} dans son entree — s'asseoir et se lever sont des gestes "
        "dates, et ils battent la mesure le temps qu'elle rattrape".format(
            "assis_a" if vers_occupe else "quitte_a"))

    tete = index.get(cible)
    if vers_occupe and tete is not None:
        actions.append(
            "retirer sa tete d'intentions.json (archivee dans "
            "etat/archive/tetes/{}-{}.json)".format(cible, horodatage()))
    if not vers_occupe:
        actions.append("sa tete reste en place : il agit desormais seul")
        if not regence.clause_posee(tete):
            actions.append(
                "AVERTISSEMENT : sa tete ne porte pas la clause de regence. "
                "Il sera active comme n'importe quel acteur et le garde "
                "mecanique le retiendra, mais il l'ignorera en agissant.\n"
                "    python scripts/regence.py --poser {} --vraiment"
                .format(cible))
    if vers_occupe:
        _, en_attente = regence.compte_rendu(cible)
        if en_attente:
            actions.append(
                "vous rendre ce qui s'est decide sans vous : {} activation(s) "
                "en regence, ecrites dans etat/joueurs/{}/"
                .format(len(en_attente), cible))

    for a in actions:
        print("  " + a)
    if not vraiment:
        print("\n(rien n'a ete ecrit — ajoutez --vraiment)")
        return

    if vers_occupe and tete is not None:
        ecrire("archive/tetes/{}-{}".format(cible, horodatage()), tete)
        ecrire("intentions", [t for t in lire("intentions", [])
                              if t.get("personnage_id") != cible])

    # ON NE REECRIT PLUS LE ROSTER ENTIER depuis une lecture vieille de trois
    # etapes : une autre session peut avoir touche un `pnj` ou une `note`
    # pendant ce temps. On pose la marque, puis on laisse le rafraichissement
    # recaler `occupe` — les deux relisent le fichier juste avant d'ecrire et
    # ne touchent que leurs propres clefs.
    occupation.marquer(cible, "assis_a" if vers_occupe else "quitte_a")
    _, refuses, _ = occupation.rafraichir(True)
    print("\necrit.")
    for m in refuses:
        print("  ATTENTION : {} est mesure vacant et n'a pas de tete — laisse "
              "occupe.".format(m["personnage_id"]))
    if vers_occupe:
        # LA PASSATION. Se rasseoir sans savoir ce qu'on herite, c'est
        # decouvrir trois lunes plus tard qu'un pli est parti en son nom. On
        # rend la liste, on l'ecrit sur disque, et on marque le registre :
        # ce qui a ete rendu ne sera pas rendu deux fois.
        texte, chemin = regence.remettre(cible)
        print("")
        print(texte)
        if chemin:
            print("\n(cette passation est ecrite dans {})".format(
                os.path.relpath(chemin, RACINE).replace("\\", "/")))
        print("\nPensez a relire son dossier avant de jouer : "
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
    ap.add_argument("--rafraichir", action="store_true",
                    help="recaler le cache `occupe` sur la mesure, sans "
                         "changer qui joue quoi")
    ap.add_argument("--vraiment", action="store_true",
                    help="ecrire pour de bon")
    args = ap.parse_args()

    if args.rafraichir and not (args.asseoir or args.quitter):
        changements, refuses, releve = occupation.rafraichir(args.vraiment)
        imprimer(releve)
        print("")
        if not changements:
            print("  le cache est deja juste : rien a recaler.")
        for m in changements:
            print("  {} : {} -> {}{}".format(
                m["personnage_id"],
                "occupe" if m["cache"] else "vacant",
                "occupe" if m["occupe"] else "vacant",
                "  (REFUSE : sans tete)" if m in refuses else ""))
        if changements and not args.vraiment:
            print("\n  (rien n'a ete ecrit — ajoutez --vraiment)")
        return

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
