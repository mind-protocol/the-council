"""Moteur arithmetique du hors-scene : ce qui tombe, et rien de plus.

Usage :
    python scripts/tick.py --verifier
        Audit de coherence de etat/ (intentions, evenements, diffusion, lieux).
        Sort en code 1 des qu'il y a une anomalie, 0 sinon.

    python scripts/tick.py --jours 3
    python scripts/tick.py --jusqu-a 129.3.20
        Calcule la fenetre depuis monde.date jusqu'a la cible, ecrit une
        PROPOSITION dans etat/tick-<AAAAMMJJ-HHMMSS>.json, et imprime
        un resume lisible.

    python scripts/tick.py --jours 3 --acteur daemon --acteur corlys
        Restreint le calcul a ces acteurs (repetable).

Le script ne decide RIEN. Il lit etat/ et n'ecrit que sous etat/ :
le MJ seul relit, arbitre et applique dans etat/*.json. Un seul ecrivain.

Reference normative du format : docs/schema.md. Calendrier : 12 lunes de
30 jours. Ce qui n'y est pas tranche l'est ici, au plus simple :
- Budget d'etapes : on compte le plan VIVANT (etapes `en-cours` ou `bloque`).
  Une etape `fait` ou `abandonne` ne charge plus la tete.
- Une etape dont `jours_restants` vaut null est une posture permanente : elle
  ne tombe jamais, ne se decompte jamais, et n'apparait dans aucun des trois
  paniers d'etapes (seulement dans le compte du resume).
- Une etape dont un `depend_de` n'est pas `fait` voit son horloge arretee :
  elle passe en attente, sans consommer les jours de la fenetre.
- Retard tolere d'une tete avant rafraichissement : 1 jour (scene), 3 jours
  (orbite), 15 jours (royaume).
- Un plan encore ecrit en chaines de caracteres (format d'avant les etapes
  horlogees) est signale, jamais reparé.
- LA BOUCHE (docs/plis.md) : un homme qui se deplace porte TOUT ce qu'il sait.
  Le tick detecte les arrivees a partir de ce qui existe deja (evenements de la
  fenetre, etapes qui tombent) et sort le DIFFERENTIEL de croyances — jamais un
  verdict. Il ne recopie aucune croyance : le MJ arbitre ce qui se dit.
- Les plis (etat/plis.json, voir docs/plis.md) sont routes : un pli `en-route`
  dont `attendu_le` est echu passe `remis`, dans la main du destinataire NATUREL
  du lieu (le mestre), jamais dans celle du `pour`. `evenements.diffusion` reste
  en place a cote : c'est une coexistence, pas un remplacement.
"""
import argparse
import collections
import hashlib
import io
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# LES PENSEES NE SE CALCULENT PLUS ICI, et `travaux.py` a disparu avec son
# excitation. Un compteur ne pouvait pas dire ce qu'un homme a appris : ce qui
# le dit, c'est sa JOURNEE — le quartier ou il se tient, les creux qu'elle lui
# laisse, les sources a portee de ces creux. C'est `presence.py` qui le mesure
# et `evaluer.py` qui en tire la feuille de route.
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from temps.expose import occupation  # qui est ASSIS — mesure, pas drapeau
# La regence (docs/regence.md) : ce qu'un siege vacant peut faire et ce qu'il
# doit rendre. Branche ici pour la seule garde — clause posee, passation due.
from temps.expose import regence
from etat.expose import tables  # LA PORTE de etat/

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
STAGING = ETAT

# L'echelle mesuree sur le quartier et ses budgets vivent dans temps/bouche.py.
from temps.bouche import (ECHELLES, BUDGETS,  # noqa: E402,F401
                          TOLERANCE_MAJ, FENETRE_ROYAUME)

# Les plis (docs/plis.md) : les constantes du courrier vivent desormais dans
# temps/lecture.py, a cote de jours_de_route et des methodes plis d'Etat.
from temps.lecture import (CANAUX_PLI, ETATS_PLI,  # noqa: E402,F401
                           ETATS_PLI_EN_MAIN, TOLERANCE_PLI, DIVISEUR_CORBEAU)

# LA BOUCHE — le rapprochement de textes vit dans temps/bouche.py.
from temps.bouche import MOTS_COMMUNS, MOTS_PARTAGES_MINIMUM  # noqa: E402,F401

# LA RUMEUR vit dans temps/rumeur.py (decoupage du container temps).
from temps.rumeur import (CERTITUDES, LENTEUR_RUMEUR,  # noqa: E402,F401
                          SAUT_RUMEUR_MINIMUM, PORTEE_SAUT_RUMEUR,
                          VOISINS_PAR_RUMEUR, SILENCE_RUMEUR)


# ------------------------------------------------------------------- dates
# Demenage dans temps/calendrier.py (decoupage du container temps).

from temps.calendrier import (JOURS_PAR_LUNE, LUNES_PAR_AN,  # noqa: E402,F401
                              jour_absolu, date_de, fmt, lire_date)


# ---------------------------------------------------------------- lecture

# Demenage dans temps/lecture.py (decoupage du container temps).
from temps.lecture import charger, Etat, jours_de_route  # noqa: E402,F401


# ------------------------------------------------------------- LA BOUCHE
# Demenage dans temps/bouche.py (decoupage du container temps).

from temps.bouche import (mots_rares, se_recoupent,  # noqa: E402,F401
                          croyances_de, _dans_le_quartier, echelle_de,
                          etapes_de)


# --------------------------------------------------- MAINS : l'arithmetique
# Demenage dans temps/mains.py (decoupage du container temps).

from temps.mains import (rythme_de, borner, au_plancher,  # noqa: E402,F401
                         decompter, porteur_absent, couts_chiffres,
                         chiffrer_cout, seuil_franchi)


# ------------------------------------------------------- garde d'ecriture

# Demenage dans temps/scelle.py (decoupage du container temps).
from temps.scelle import (TABLES_MUTABLES, CROYANCES,  # noqa: E402,F401
                          chemin_scelle, empreintes_etat, ecrire_proposition)


# ------------------------------------------------------- MODE A : verifier
# Demenage dans temps/gardes/ (decoupage du container temps).

from temps.gardes import (GRAVITES, Rapport, verifier,  # noqa: E402,F401
                          verifier_intentions, verifier_mains,
                          verifier_couts_chiffres, verifier_etats_du_plan,
                          verifier_rapporteurs, CLES_BOOK, CLES_BOITE,
                          TYPES_BOOK, verifier_pensees, qui_a_du_temps,
                          verifier_books, verifier_boites, sources_possibles,
                          verifier_croyances_sans_porteur, verifier_evenements,
                          verifier_personnages, verifier_plis,
                          verifier_rumeurs, verifier_occupation, siege_par_id,
                          verifier_sieges, verifier_audiences,
                          verifier_affectations, verifier_registres_derives,
                          verifier_activations)

# ------------------------------------------------------------- LA RUMEUR
# Demenage dans temps/rumeur.py (decoupage du container temps).

from temps.rumeur import (temoins_des_incidents,  # noqa: E402,F401
                          rang_certitude, degrader, relais_de,
                          saut_rumeur, propager_rumeurs, sans_accents,
                          lieu_cite, detecter_bouches, cycles)


# ----------------------------------------------------------- MODE B : tick
# Demenage dans temps/fenetre.py (calculer eclate en phases) et
# temps/mutations.py (decoupage du container temps).

from temps.fenetre import calculer, tick  # noqa: E402,F401


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Moteur arithmetique du hors-scene (lit etat/, "
                    "n'ecrit que dans etat/)")
    ap.add_argument("--verifier", action="store_true",
                    help="audit de coherence de etat/ (code 1 si anomalie)")
    ap.add_argument("--json", dest="en_json", action="store_true",
                    help="avec --verifier : l'audit en JSON, pour /admin/sante")
    ap.add_argument("--jours", type=int,
                    help="taille de la fenetre depuis monde.date")
    ap.add_argument("--jusqu-a", dest="jusqu_a", metavar="129.3.20",
                    help="date cible de la fenetre")
    ap.add_argument("--acteur", action="append", default=[], metavar="ID",
                    help="restreint le calcul a cet acteur (repetable)")
    ap.add_argument("--joueur", default=None, metavar="ID",
                    help="personnage_id dont les croyances (jetons, vues, "
                         "objectifs) seront scellees et appliquees. Inscrit "
                         "dans la proposition ; appliquer.py le reprend.")
    args = ap.parse_args()

    e = Etat()

    if args.verifier:
        if args.jours is not None or args.jusqu_a:
            sys.exit("--verifier ne se combine pas avec --jours / --jusqu-a")
        return verifier(e, args.en_json)

    if args.jours is not None and args.jusqu_a:
        sys.exit("choisir --jours OU --jusqu-a, pas les deux")
    if args.jours is not None:
        if args.jours < 0:
            sys.exit("--jours doit etre positif")
        cible = date_de(e.aujourdhui + args.jours)
    elif args.jusqu_a:
        cible = lire_date(args.jusqu_a)
    else:
        ap.print_help()
        return 0

    return tick(e, cible, set(args.acteur), args.joueur)


if __name__ == "__main__":
    sys.exit(main())
