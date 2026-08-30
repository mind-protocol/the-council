# -*- coding: utf-8 -*-
"""DEPECHE — envoyer un homme vivre sa journee dans une session a lui.

La Regle Zero : ses paroles sont a lui. Le script rassemble ce que l'homme
sait (brief, dossier, travaux, trous de son plan), lui sert son manuel, ouvre
sa session claude -p (stable par homme et par jour de jeu), et a son retour
pose le rapport dans etat/rapports/ puis le verse sur-le-champ.

CE QUE CE PAQUET POSSEDE, decoupe sous le plafond de 500 lignes
(docs/organisation.md §7 voulait brief/manuel/retour — la coupe est plus fine
parce que le manuel du narrateur et la mission depassaient le plafond) :
    brief.py     : les constantes, la lecture du monde, le brief d'un homme
    manuel.py    : la memoire d'activation, l'etagere, les manuels servis
    narrateur.py : le contrat de rapport du narrateur local
    trous.py     : ce que son plan montre (criticite, charge, attentes)
    mission.py   : le texte de mission, l'archive du prompt, l'appel claude -p
    retour.py    : le versement sur-le-champ et la proposition de tete
    cli.py       : main() — la CLI gelee de scripts/depecher.py

La commande gelee `scripts/depecher.py` est une FACADE qui appelle main()
par la porte agents/expose.py.
"""
from agents.depeche.brief import (  # noqa: F401
    RACINE, ETAT, DEPOT_RAPPORTS, METIER, MANUEL_MJ, SEL, OUTILS, PARLOIR_PY,
    OUTIL_PARLOIR, livre, lire, date_du_monde, identifiant_de_session,
    feuille_de_route, brief_de, travaux_ouverts_de, dossier_journee,
    a_convoquer, les_pj, salles_peuplees, dans_la_salle, positions,
    position_de, dans_le_rayon, travaux_ids)
from agents.depeche.manuel import (  # noqa: F401
    memoire_activation, etagere_systeme, manuel_de, contexte_message,
    message_tentative, manuel_narrateur_local)
from agents.depeche.narrateur import (  # noqa: F401
    contrat_rapport_narrateur)
from agents.depeche.trous import (  # noqa: F401
    TROUS_MONTRES, TROUS_AILLEURS, ses_trous, sa_charge_ailleurs, on_lattend)
from agents.depeche.mission import (  # noqa: F401
    DEPECHES, mission, poser_la_memoire, poser_letagere, poser_le_parloir, archiver_le_prompt,
    appeler, extraire_json, depecher)
from agents.depeche.retour import (  # noqa: F401
    verser_sur_le_champ, proposer_la_tete)
from agents.depeche.cli import main  # noqa: F401
