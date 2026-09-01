# -*- coding: utf-8 -*-
"""CLI — l'entree de scripts/boucle_activation.py, gelee (la facade
l'appelle par la porte agents/expose.py).
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time

from agents.activation import socle  # LES DRAPEAUX SE POSENT SUR LE MODULE
from agents.activation.socle import (ECHECS_CONSECUTIFS_MAX, journaliser,
                                     _court)
from agents.activation.cycle import VerrouBoucle, cycle, prevoir_activations


def retisser_tissu():
    """Regénère le miroir après qu'un lot a changé ses sources canoniques."""
    debut = time.monotonic()
    commande = [sys.executable,
                os.path.join(socle.RACINE, "scripts", "tisser.py"),
                "--ecrire"]
    resultat = subprocess.run(
        commande, cwd=socle.RACINE, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120)
    if resultat.returncode:
        detail = resultat.stderr or resultat.stdout or "aucune sortie"
        raise RuntimeError("retissage du tissu échoué : " + _court(detail, 400))
    journaliser("graphe.retisse",
                duree_s=round(time.monotonic() - debut, 3))

def main():
    # `global PERSISTER_LOGS` NE FAISAIT RIEN, ET C'EST LE PIEGE CLASSIQUE DU
    # DECOUPAGE. `from socle import PERSISTER_LOGS` copie la VALEUR dans ce
    # module-ci ; la reaffecter n'a jamais touche celle que `journaliser()`
    # relit dans socle. Consequence mesuree le 31.8 : `--prevoir`, documente
    # « rendre les N prochains candidats en JSON », rendait quarante lignes de
    # log AVANT le JSON — donc une sortie que personne ne peut parser, et une
    # commande de lecture inutilisable pour un banc ou pour la regie.
    # On pose desormais les drapeaux SUR le module, comme la fiche du container
    # le dit deja aux bancs (`activation.socle.AFFICHER_LOGS = False`).
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--une-fois", action="store_true",
                    help="un seul examen du front puis sortie")
    ap.add_argument("--sec", action="store_true",
                    help="selection et mission seulement, aucun appel ni ecriture")
    ap.add_argument("--acteur", help="borner la selection a cet acteur")
    ap.add_argument("--braavos", action="store_true",
                    help="borner la sélection aux acteurs situés à Braavos")
    ap.add_argument("--intervalle", type=float, default=5.0,
                    help="secondes entre deux examens sans activation")
    ap.add_argument("--modele", default="opus",
                    help="modele transmis au script d'appel")
    ap.add_argument("--effort", default="low",
                    help="effort de raisonnement transmis au CLI, ex. low")
    # 0 = PAS D'EXPIRATION, et c'est le defaut (31.8). Un plafond de session
    # ne protege de rien : le processus rend la main quand il a fini. Il
    # coupe seulement du travail en cours — mesure le meme jour, une journee
    # d'homme entiere perdue a 180 s, zero octet ecrit.
    ap.add_argument("--minutes-appel", type=int, default=0,
                    help="borner l'appel a N minutes ; 0 = la session"
                         " n'expire pas (defaut)")
    ap.add_argument("--max-activations", type=int, default=0,
                    help="0 = sans plafond")
    ap.add_argument("--heartbeat", type=float, default=5.0,
                    help="secondes entre deux logs quand le CLI est silencieux")
    ap.add_argument("--parallele", type=int, default=1,
                    help="nombre maximal d'activations simultanees")
    ap.add_argument("--prevoir", type=int, default=0, metavar="N",
                    help="rendre les N prochains candidats en JSON, sans ecriture")
    args = ap.parse_args()
    if (args.intervalle <= 0 or args.minutes_appel < 0 or
            args.heartbeat <= 0 or args.parallele <= 0):
        ap.error("intervalle, heartbeat et parallele doivent etre positifs ; "
                 "minutes-appel accepte 0 (pas d'expiration)")
    if args.prevoir < 0:
        ap.error("prevoir doit etre positif")
    if args.prevoir:
        socle.PERSISTER_LOGS = False
        socle.AFFICHER_LOGS = False
        json.dump(prevoir_activations(args.prevoir, braavos=args.braavos), sys.stdout,
                  ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    socle.PERSISTER_LOGS = not args.sec
    journaliser("boucle.demarrage", sec=args.sec, une_fois=args.une_fois,
                heartbeat_s=args.heartbeat, parallele=args.parallele,
                braavos=args.braavos)

    if args.sec:
        cycle(args)
        return 0
    faites = 0
    echecs_consecutifs = 0
    with VerrouBoucle():
        etat = None
        # Le premier lot doit lui aussi partir du canon courant. Ensuite, un
        # lot réussi salit nécessairement le miroir : les hommes peuvent avoir
        # clos, créé ou réaffecté une pièce pendant leur journée.
        tissu_sale = True
        while True:
            try:
                if tissu_sale:
                    retisser_tissu()
                    tissu_sale = False
                if args.max_activations:
                    args.capacite_cycle = min(
                        args.parallele, args.max_activations - faites)
                else:
                    args.capacite_cycle = args.parallele
                etat, actives, tentees = cycle(args, etat)
            except KeyboardInterrupt:
                journaliser("boucle.arretee", raison="clavier")
                return 130
            except Exception as e:
                # Un cycle qui casse ne doit jamais eteindre la boucle : on
                # journalise, on souffle, et on repart au cycle suivant.
                echecs_consecutifs += 1
                journaliser("cycle.echoue", raison=type(e).__name__,
                            erreur=_court(str(e), 400),
                            consecutifs=echecs_consecutifs)
                # Mais une panne qui ne passe pas — disque plein, etat illisible —
                # ne se guerit pas en dormant : sans ce compteur, la boucle
                # tournait a vide toute la nuit en croyant travailler.
                if echecs_consecutifs >= ECHECS_CONSECUTIFS_MAX:
                    journaliser("boucle.arretee", raison="echecs_consecutifs",
                                seuil=ECHECS_CONSECUTIFS_MAX,
                                dernier=type(e).__name__)
                    return 1
                time.sleep(args.intervalle)
                continue
            echecs_consecutifs = 0
            if actives:
                tissu_sale = True
            # ON COMPTE LES TENTATIVES, PAS LES REUSSITES. `--max-activations`
            # ne bornait que le succes : une panne qui annule tout laissait le
            # compteur a zero, et la course ne pouvait plus se terminer. Onze
            # appels et 3,91 USD le 31.8, sur le meme homme et la meme tache.
            # Le plafond borne desormais ce qu'on DEPENSE, ce qui est le seul
            # sens utile d'un plafond.
            faites += tentees
            if args.une_fois or (args.max_activations and
                                 faites >= args.max_activations):
                return 0
            if not actives:
                time.sleep(args.intervalle)


