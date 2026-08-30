# -*- coding: utf-8 -*-
"""ACTIVATION — la boucle d'activation narrative pilotee par le graphe miroir.

La boucle ne modifie jamais l'etat canonique. Elle lit le tissu et les
horloges, calcule la meme diffusion d'importance que la regie, accumule une
energie technique (0..100), puis appelle la depeche pour l'acteur qui porte
le maximum. Les mutations sont appliquees a etat/ ; le rapport reste comme
trace dans etat/activations, qui n'est PAS un purgatoire.

CE QUE CE PAQUET POSSEDE, decoupe sous le plafond de 500 lignes
(docs/organisation.md §7 voulait activation.py — 3 184 lignes ne tiennent
pas dans un fichier ne sous le cliquet) :
    socle.py      : constantes, journal, lectures de base
    horloges.py   : minute absolue, horloge directe, polarites
    graphe.py     : adjacence, diffusion, clusters, etat des taches
    taches.py     : choisir la tache, mettre a jour les energies
    missions.py   : les textes du narrateur local, et leurs extractions
    dossier.py    : les references servies a l'activation
    mutations.py  : plausibilite et controle des mutations rendues
    rapport.py    : normaliser le rapport brut
    continuite.py : la continuite des taches, l'amorcage historique
    appels.py     : l'appel claude en stream, appeler_acteur
    cycle.py      : le verrou, un cycle complet, la prevision
    cli.py        : main() — la CLI gelee de scripts/boucle_activation.py

NOTE aux bancs : AFFICHER_LOGS / PERSISTER_LOGS vivent dans socle.py — pour
les debrayer, ecrire `activation.socle.AFFICHER_LOGS = False` (les poser sur
ce paquet ne changerait rien a journaliser()).

La commande gelee `scripts/boucle_activation.py` est une FACADE qui appelle
main() par la porte agents/expose.py.
"""
from agents.activation import socle  # noqa: F401 — pour socle.AFFICHER_LOGS
from agents.activation.socle import (  # noqa: F401
    RACINE, ETAT, TISSU, DEPOT, ETAT_BOUCLE, VERROU, JOURNAL, JUGER_PY,
    PERSISTER_LOGS, AFFICHER_LOGS, AMORTISSEMENT, TOURS_DIFFUSION,
    ENERGIE_MAX, ENERGIE_MIN, ENERGIE_ACTIVATION_MIN,
    SECONDES_MONDE_PAR_ENERGIE, DUREE_ACTIVATION_MIN_SECONDES,
    DEMI_VIE_ENERGIE, ECHECS_CONSECUTIFS_MAX, REPOS_ACTEUR_SECONDES,
    REPOS_PAIRE_SECONDES, TRANSFERT_HORLOGE_MAX, GENRES_RELAIS,
    ETATS_TERMINES, TYPES_RESULTAT_ACTIVITE, secondes_monde_pour_energie,
    energie_pour_secondes, journaliser, lire_json, ecrire_atomique,
    charger_tissu)
from agents.activation.horloges import (  # noqa: F401
    minute_absolue, horloge_directe, polarites_horloge_acteurs,
    appliquer_polarites_horloge)
from agents.activation.graphe import (  # noqa: F401
    adjacence, sources_de_charge, diffuser, importance, energie_de_tache,
    clusters_par_lieu, normaliser_par_cluster, calendrier, tache_active,
    empreinte_tache, continuite_tache, repos_perime, tache_disponible,
    acteur_en_repos)
from agents.activation.taches import (  # noqa: F401
    choisir_tache, mettre_a_jour_energie_graphe, mettre_a_jour_energies)
from agents.activation.missions import (  # noqa: F401
    mission_activation, mission_ouverture_narrateur, mission_veille_narrateur,
    mission_resolution_narrateur, mission_correction_narrateur,
    mission_relance_acteur, extraire_appel_pnj, extraire_tentative,
    extraire_relance_acteur, intitule_tache_activation)
from agents.activation.dossier import (  # noqa: F401
    references_du_monde, references_du_dossier, dossier_activation,
    contrainte_regence)
from agents.activation.mutations import (  # noqa: F401
    valider_plausibilite_temporelle, valider_mutations_applicables,
    reparer_mutations, filtrer_mutations_applicables)
from agents.activation.rapport import (  # noqa: F401
    normaliser_rapport_activation)
from agents.activation.continuite import (  # noqa: F401
    enregistrer_continuite, amorcer_continuite_historique)
from agents.activation.appels import (  # noqa: F401
    appeler_stream, appeler_acteur, poser_jugement_narrateur)
from agents.activation.cycle import (  # noqa: F401
    VerrouBoucle, cycle, prevoir_activations)
from agents.activation.cli import main  # noqa: F401
