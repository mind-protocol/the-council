# -*- coding: utf-8 -*-
"""CRITICITE — ce qu'on perd si ce pas-la rate.

Usage :
    python scripts/criticite.py                  le classement, tous genres
    python scripts/criticite.py --combien 30
    python scripts/criticite.py --affaire "Prise de Port-Real"
    python scripts/criticite.py --restant        sans ce qui est deja fait
    python scripts/criticite.py --strict         un verrou sans clef bloque
    python scripts/criticite.py --sans-dep       ignorer « ⛓️ Depend de »
    python scripts/criticite.py --etats          le poids par etat cible
    python scripts/criticite.py --acteurs        ce que chaque homme porte
    python scripts/criticite.py --charge         ce qu il voit / ne voit pas
    python scripts/criticite.py --charge gerardys
    python scripts/criticite.py --decisions      l arbre des fourches
    python scripts/criticite.py --decisions 43011
    python scripts/criticite.py --pourquoi 8201  la chaine qui empeche une piece

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container plan/criticite/ — page, graphe, hommes, affaires, decisions, note,
calcul, cli. Le chemin et la CLI de cette commande sont geles ; les reexports
ci-dessous gardent les anciens noms `criticite.*` vivants pour les importeurs
historiques (depecher, analyse/bilan).
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from plan.expose import criticite as _criticite  # noqa: E402
from plan.expose import criticite_main as _entree  # noqa: E402

amonts = _criticite.amonts
atteignables = _criticite.atteignables
cercles = _criticite.cercles
calculer = _criticite.calculer
charge_de = _criticite.charge_de
arbre_des_decisions = _criticite.arbre_des_decisions
objectifs_finaux = _criticite.objectifs_finaux
plan_de = _criticite.plan_de
declaree = _criticite.declaree
cout = _criticite.cout
prix = _criticite.prix
main = _criticite.main

if __name__ == "__main__":
    _entree()
