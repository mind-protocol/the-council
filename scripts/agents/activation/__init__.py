# -*- coding: utf-8 -*-
"""ACTIVATION — la boucle d'activation narrative pilotee par le graphe miroir.

La boucle lit le tissu et les horloges, calcule une diffusion d'importance,
accumule une energie technique (0..100), puis appelle la depeche canonique
pour l'acteur qui porte le maximum. L'homme agit avec accès au dépôt et écrit
directement son état ; etat/activations conserve seulement la trace du choix.

CE QUE CE PAQUET POSSEDE, decoupe sous le plafond de 500 lignes
(docs/organisation.md §7 voulait activation.py — 3 184 lignes ne tiennent
pas dans un fichier ne sous le cliquet) :
    socle.py      : constantes, journal, lectures de base
    horloges.py   : minute absolue, horloge directe, polarites
    graphe.py     : adjacence, diffusion, clusters, etat des taches
    taches.py     : choisir la tache, mettre a jour les energies
    continuite.py : la continuite des taches, l'amorcage historique
    appels.py     : le raccord direct au depecheur canonique avec acces depot
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
    DEMI_VIE_CHARGE_COMPUTE_HEURES, MINUTES_COMPUTE_DEMI_ENERGIE,
    MINUTES_COMPUTE_DEMI_MJ, CAPACITE_FERMETURE, CAPACITE_REOUVERTURE,
    HEURES_RETARD_GRACE, HEURES_RETARD_DEMI_ENERGIE,
    VERSION_FATIGUE_ACTEURS,
    REPOS_PAIRE_SECONDES, TRANSFERT_HORLOGE_MAX, GENRES_RELAIS,
    ETATS_TERMINES, TYPES_RESULTAT_ACTIVITE, secondes_monde_pour_energie,
    energie_pour_secondes, journaliser, lire_json, ecrire_atomique,
    charger_tissu)
from agents.activation.horloges import (  # noqa: F401
    minute_absolue, date_civile_acteur, horloge_directe,
    commettre_lot_horloge,
    polarites_horloge_acteurs,
    appliquer_polarites_horloge)
from agents.activation.fatigue import (  # noqa: F401
    charge_compute_decroissante, instant_fictionnel_secondes,
    facteur_de_charge, capacite_acteur,
    mettre_a_jour_porte, mesurer_fatigue, ajouter_activation,
    amorcer_fatigue_historique)
from agents.activation.graphe import (  # noqa: F401
    adjacence, sources_de_charge, diffuser, importance, energie_de_tache,
    clusters_par_lieu, normaliser_par_cluster, calendrier, tache_active,
    empreinte_tache, continuite_tache, repos_perime, tache_disponible,
    acteur_en_repos)
from agents.activation.taches import (  # noqa: F401
    choisir_tache, mettre_a_jour_energie_graphe, mettre_a_jour_energies)
from agents.activation.continuite import (  # noqa: F401
    enregistrer_continuite, amorcer_continuite_historique)
from agents.activation.appels import (  # noqa: F401
    appeler_acteur)
from agents.activation.cycle import (  # noqa: F401
    VerrouBoucle, cycle, prevoir_activations)
from agents.activation.cli import main  # noqa: F401
