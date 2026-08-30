# -*- coding: utf-8 -*-
"""CLI — l'entree de scripts/boucle_activation.py, gelee (la facade
l'appelle par la porte agents/expose.py).
"""
import argparse
import io
import json
import sys
import time

from agents.activation.socle import (ECHECS_CONSECUTIFS_MAX, journaliser,
                                     _court)
from agents.activation.cycle import VerrouBoucle, cycle, prevoir_activations

def main():
    global PERSISTER_LOGS, AFFICHER_LOGS
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--une-fois", action="store_true",
                    help="un seul examen du front puis sortie")
    ap.add_argument("--sec", action="store_true",
                    help="selection et mission seulement, aucun appel ni ecriture")
    ap.add_argument("--acteur", help="borner la selection a cet acteur")
    ap.add_argument("--intervalle", type=float, default=5.0,
                    help="secondes entre deux examens sans activation")
    ap.add_argument("--modele", default="opus",
                    help="modele transmis au script d'appel")
    ap.add_argument("--effort", default="low",
                    help="effort de raisonnement transmis au CLI, ex. low")
    ap.add_argument("--minutes-appel", type=int, default=15,
                    help="timeout technique de l'appel (pas le budget fictionnel)")
    ap.add_argument("--max-activations", type=int, default=0,
                    help="0 = sans plafond")
    ap.add_argument("--heartbeat", type=float, default=5.0,
                    help="secondes entre deux logs quand le CLI est silencieux")
    ap.add_argument("--parallele", type=int, default=1,
                    help="nombre maximal d'activations simultanees")
    ap.add_argument("--prevoir", type=int, default=0, metavar="N",
                    help="rendre les N prochains candidats en JSON, sans ecriture")
    args = ap.parse_args()
    if (args.intervalle <= 0 or args.minutes_appel <= 0 or
            args.heartbeat <= 0 or args.parallele <= 0):
        ap.error("intervalle, minutes-appel, heartbeat et parallele "
                 "doivent etre positifs")
    if args.prevoir < 0:
        ap.error("prevoir doit etre positif")
    if args.prevoir:
        PERSISTER_LOGS = False
        AFFICHER_LOGS = False
        json.dump(prevoir_activations(args.prevoir), sys.stdout,
                  ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    PERSISTER_LOGS = not args.sec
    journaliser("boucle.demarrage", sec=args.sec, une_fois=args.une_fois,
                heartbeat_s=args.heartbeat, parallele=args.parallele)

    if args.sec:
        cycle(args)
        return 0
    faites = 0
    echecs_consecutifs = 0
    with VerrouBoucle():
        etat = None
        while True:
            try:
                if args.max_activations:
                    args.capacite_cycle = min(
                        args.parallele, args.max_activations - faites)
                else:
                    args.capacite_cycle = args.parallele
                etat, actives = cycle(args, etat)
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
            faites += actives
            if args.une_fois or (args.max_activations and
                                 faites >= args.max_activations):
                return 0
            if not actives:
                time.sleep(args.intervalle)

