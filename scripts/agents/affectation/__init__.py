# -*- coding: utf-8 -*-
"""AFFECTATION — donner une adresse physique a une chose de la fiction.

Tant qu'une chose n'est pas affectee, elle n'a pas de metres : on ne peut pas
dire combien de pas la separent d'une autre, donc on l'estime, donc on se
trompe. Affecter transforme des distances en FAITS. Le contrat : le monde
engendre (monde/) est regenerable et bete — on n'y ecrit JAMAIS ; ce qui est
decide en jeu vit dans etat/corps.json sous la clef `affectations` ; rien ne
s'ecrit sans --vraiment ; --verifier signale les cibles disparues.

CE QUE CE PAQUET POSSEDE, decoupe sous le plafond de 500 lignes :
    lecture.py  : le bati, les pieces, les liens, positions et adresses
    controle.py : verifier() et reancrer()
    cli.py      : main() — la CLI gelee de scripts/affecter.py

La commande gelee `scripts/affecter.py` est une FACADE qui appelle main()
par la porte agents/expose.py.
"""
from agents.affectation.lecture import (  # noqa: F401
    RACINE, DEFAUT_MONDE, GENS, LIENS, PERSOS, BOOKS, PLANS, VILLE, GENRES,
    RAYON_REANCRAGE, OCCUPANTS, sortir, charger_bati, charger_pieces,
    fiche_piece, monde_de, charger_liens, retrait, ecrire, fiche_bati,
    dire_bati, position, adresse, corps_par_id, identifiants,
    visibilite_demandee, voit)
from agents.affectation.controle import verifier, reancrer  # noqa: F401
from agents.affectation.cli import main  # noqa: F401
