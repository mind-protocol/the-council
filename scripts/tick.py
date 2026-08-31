"""Moteur arithmetique du hors-scene : ce qui tombe, et rien de plus.

Usage :
    python scripts/tick.py --verifier
        Audit de coherence de etat/ (intentions, evenements, diffusion, lieux).
        Sort en code 1 des qu'il y a une anomalie, 0 sinon.

    python scripts/tick.py --jours 3
    python scripts/tick.py --jusqu-a 129.3.20
        Calcule la fenetre depuis monde.date jusqu'a la cible et imprime
        un resume lisible. Rien n'est ecrit.

    python scripts/tick.py --jours 3 --acteur daemon --acteur corlys
        Restreint le calcul a ces acteurs (repetable).

Le script ne decide et n'ecrit rien.

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container temps/ — calendrier, lecture, bouche, mains, rumeur,
gardes/, fenetre, resume. Les regles de calcul sont en tete de
temps/fenetre.py ; la reference normative du format reste docs/schema.md
(calendrier : 12 lunes de 30 jours). Le chemin et la CLI de cette commande
sont geles ; les reexports ci-dessous gardent les anciens noms `tick.*`
vivants pour les importeurs historiques (tests, temps/expose.py).
"""
import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE D'ABORD : charger temps.expose lie occupation, presence, regence
# et evaluer AVANT les modules du tick, qui relisent la porte pendant leur
# propre chargement (contrainte d'ordre documentee en tete de temps/expose.py).
import temps.expose  # noqa: E402,F401

from temps.calendrier import (JOURS_PAR_LUNE, LUNES_PAR_AN,  # noqa: E402,F401
                              jour_absolu, date_de, fmt, lire_date)
from temps.lecture import (RACINE, ETAT, CANAUX_PLI, ETATS_PLI,  # noqa: E402,F401
                           ETATS_PLI_EN_MAIN, TOLERANCE_PLI, DIVISEUR_CORBEAU,
                           charger, Etat, jours_de_route)
from temps.bouche import (ECHELLES, BUDGETS, TOLERANCE_MAJ,  # noqa: E402,F401
                          FENETRE_ROYAUME, MOTS_COMMUNS, MOTS_PARTAGES_MINIMUM,
                          mots_rares, se_recoupent, croyances_de,
                          _dans_le_quartier, echelle_de, etapes_de)
from temps.mains import (rythme_de, borner, au_plancher,  # noqa: E402,F401
                         decompter, porteur_absent, couts_chiffres,
                         chiffrer_cout, seuil_franchi)
from temps.rumeur import (CERTITUDES, LENTEUR_RUMEUR,  # noqa: E402,F401
                          SAUT_RUMEUR_MINIMUM, PORTEE_SAUT_RUMEUR,
                          VOISINS_PAR_RUMEUR, SILENCE_RUMEUR,
                          temoins_des_incidents, rang_certitude, degrader,
                          relais_de, saut_rumeur, propager_rumeurs,
                          sans_accents, lieu_cite, detecter_bouches, cycles)
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
                          verifier_affectations, verifier_registres_derives)
from temps.fenetre import calculer, tick  # noqa: E402,F401
from temps.resume import resumer  # noqa: E402,F401


def main():
    ap = argparse.ArgumentParser(
        description="Moteur arithmetique du hors-scene (lecture seule)")
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
                    help="personnage_id dont les croyances sont lues")
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
