# -*- coding: utf-8 -*-
"""CLI — l'entree de scripts/etat_du_plan.py, gelee (la facade l'appelle
par la porte plan/expose.py).
"""
import sys

from plan.expose import sans_emoji
import jours_relatifs as JR
import plan_modele as PM

from plan.etat_du_plan.echeances import aujourdhui, echelle, registre
from plan.etat_du_plan.sections import (section_jour, section_portee,
                                        section_synthese, section_brouillons,
                                        section_du, section_chaines,
                                        section_arrache, section_charge,
                                        section_muettes, section_trous,
                                        section_grille, section_comparer)
from plan.etat_du_plan.missions import (section_pour, section_emblemes,
                                        section_qui)

AIDE = u"""etat_du_plan.py — l'état du plan, toutes affaires confondues.

    python scripts/etat_du_plan.py                 le rapport entier
    python scripts/etat_du_plan.py --du            ce qui est dû, et les chaînes
    python scripts/etat_du_plan.py --tout          toutes les chaînes, même dormantes
    python scripts/etat_du_plan.py --affaire "port-real"
    python scripts/etat_du_plan.py --office O03
    python scripts/etat_du_plan.py --grille          une ligne par cahier
    python scripts/etat_du_plan.py --qui             les trous par homme
    python scripts/etat_du_plan.py --pour gerardys   ses affaires, à lui seul
    python scripts/etat_du_plan.py --vue-de marlo-vasse
                                      le plan visible depuis un autre siège
    python scripts/etat_du_plan.py --comparer        l'écart avec la route /echiquier
    python scripts/etat_du_plan.py --jour-entree "30e de la 4e lune"
                                     résout les J−N sous hypothèse, et le dit en tête

DEUX ÉCHELLES. Le plan se date à rebours du jour d'entrée, qui n'est arrêté
nulle part (verrou 11001). Sans jour d'entrée, les J−N sont comptés et triés
entre eux dans leur propre section ; avec `--jour-entree`, ils sont convertis
en jours de lune sous une hypothèse annoncée en tête de rapport.

Lecture seule : rien n'est écrit. Les dérivations viennent du chargeur de
couverture.py ; si un cahier dit autre chose, relancer couverture.py.
"""


def main(args=None):
    if args is None:
        args = sys.argv[1:]
        if "--aide" in args or "-h" in args or "--help" in args:
            sys.stdout.write(AIDE)
            raise SystemExit(0)

        filtre_aff = None
        if "--affaire" in args:
            filtre_aff = sans_emoji(args[args.index("--affaire") + 1]).lower()
        filtre_off = args[args.index("--office") + 1] if "--office" in args else None
        pour = args[args.index("--pour") + 1] if "--pour" in args else None
        plafond = int(args[args.index("--combien") + 1]) if "--combien" in args else 12
        seul_du = "--du" in args

        vue_de = (args[args.index("--vue-de") + 1]
                  if "--vue-de" in args else PM.personnage_par_defaut())
        modele = PM.charger(vue_de)
        livres = modele["livres"]
        pieces = modele["pieces"]
        inventaire = modele["inventaire"]
        affaires = modele["affaires"]
        date = aujourdhui()

        # L'ECHELLE RELATIVE, ET SON ANCRE. On cherche d'abord le jour d'entree
        # dans l'etat ; a defaut on prend l'hypothese donnee en argument ; a defaut
        # on ne resout rien et on le DIT. Jamais de date supposee en silence.
        rel = echelle(livres)
        jour_j, source_j = JR.cherche_dans_etat()
        if not jour_j and "--jour-entree" in args:
            jour_j = JR.lire_hypothese(args[args.index("--jour-entree") + 1], date)
            source_j = u"hypothèse donnée en argument"
            if not jour_j:
                raise SystemExit(u"--jour-entree : date illisible. Ex. \"30e de la 4e lune\".")
        elif not jour_j:
            source_j = None
        # LE NOM D'UN OFFICE VIENT DU CHARGEUR, le reste du registre du grand plan.
        # `registre()` lit un volume à plat et ne sait donc rien de `nera-moyens`,
        # qui porte ses deux tables dans `tables` : sans le repli sur l'inventaire,
        # l'office O01 de la Néra s'afficherait sans nom.
        offices = dict(inventaire)
        offices.update(registre(livres, "plan-offices", u"l'office|loffice"))
        titulaires = registre(livres, "plan-offices", u"titulaire")
        etats_moyens = registre(livres, "plan-moyens", u"^état$|^etat$")

        # LA COUPE PAR PERSONNE ferme le reste : un homme qui ouvre ça veut SES
        # affaires, pas l'état du royaume. Le conseil du matin, lui, garde sa page.
        if pour:
            section_jour(date, pieces, affaires)
            section_portee(modele)
            section_pour(pour, pieces, affaires, plafond)
            sys.stdout.write(u"\n")
            raise SystemExit(0)
        if "--grille" in args:
            section_jour(date, pieces, affaires)
            section_portee(modele)
            section_grille(pieces, affaires, date, rel)
            section_brouillons(modele)
            sys.stdout.write(u"\n")
            raise SystemExit(0)
        if "--qui" in args:
            section_jour(date, pieces, affaires)
            section_portee(modele)
            section_qui(pieces, affaires)
            section_emblemes(livres)
            section_brouillons(modele)
            if "--comparer" in args:
                section_comparer(pieces, affaires)
            sys.stdout.write(u"\n")
            raise SystemExit(0)
        if "--comparer" in args:
            section_comparer(pieces, affaires)
            sys.stdout.write(u"\n")
            raise SystemExit(0)

        section_jour(date, pieces, affaires)
        section_portee(modele)
        section_synthese(modele)
        section_du(pieces, date, rel, jour_j, source_j, filtre_aff, filtre_off,
                   "--tout" in args)
        section_chaines(pieces, date, filtre_aff, "--tout" in args, rel)
        if not seul_du:
            section_arrache(pieces, inventaire, etats_moyens, filtre_aff)
            section_charge(pieces, offices, titulaires, filtre_aff)
            if not filtre_aff and not filtre_off:
                section_muettes(pieces, affaires)
            section_trous(pieces, inventaire, affaires, filtre_aff)
            section_brouillons(modele)
        sys.stdout.write(u"\n")
