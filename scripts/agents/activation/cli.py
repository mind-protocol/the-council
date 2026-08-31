# -*- coding: utf-8 -*-
"""CLI — l'entree de scripts/boucle_activation.py, gelee (la facade
l'appelle par la porte agents/expose.py).
"""
import argparse
import io
import json
import sys
import time

from agents.activation import socle  # LES DRAPEAUX SE POSENT SUR LE MODULE
from agents.activation.socle import (ECHECS_CONSECUTIFS_MAX, journaliser,
                                     _court)
from agents.activation.cycle import VerrouBoucle, cycle, prevoir_activations

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
        json.dump(prevoir_activations(args.prevoir), sys.stdout,
                  ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    socle.PERSISTER_LOGS = not args.sec
    journaliser("boucle.demarrage", sec=args.sec, une_fois=args.une_fois,
                heartbeat_s=args.heartbeat, parallele=args.parallele)

    if args.sec:
        cycle(args)
        return 0
    faites = 0
    echecs_consecutifs = 0
    annulations = 0
    with VerrouBoucle():
        etat = None
        while True:
            # LA TABLE DU MJ FAIT PARTIE DU FRONT (habitant.md : le MJ est
            # un travailleur — la boucle l'elit comme tout le monde). A
            # chaque battement : si sa table porte quelque chose (memes
            # comptes que son mot d'etabli) et qu'aucun etabli n'est recent
            # (cooldown reel, marqueur dans sa chambre), son etabli part
            # DETACHE. Gradue, jamais bloquant : un echec de calcul se
            # journalise et la boucle continue. Import local : la porte lie
            # `zone` avant `activation`, mais on ne paie l'import qu'ici.
            try:
                from agents.expose import zone as _zone
                # TOUS les MJ de joueurs (decide le 31.8) : comptes OU un
                # etabli par jour de fiction meme a table vide — la piece 3
                # du narrateur (developper les plans, pas juste reagir).
                lances = _zone.veiller_etablis()
                for _mj, comptes in (lances or {}).items():
                    journaliser("etabli.lance", mj=_mj, **comptes)
            except Exception as e:
                journaliser("etabli.echoue", raison=type(e).__name__,
                            erreur=_court(str(e), 200))
            try:
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
            # ON COMPTE LES TENTATIVES, PAS LES REUSSITES. `--max-activations`
            # ne bornait que le succes : une panne qui annule tout laissait le
            # compteur a zero, et la course ne pouvait plus se terminer. Onze
            # appels et 3,91 USD le 31.8, sur le meme homme et la meme tache.
            # Le plafond borne desormais ce qu'on DEPENSE, ce qui est le seul
            # sens utile d'un plafond.
            faites += tentees
            # ET L'ON S'ARRETE SI RIEN N'ABOUTIT. Le plafond borne la depense,
            # mais il ne dit pas qu'une panne est une panne : onze tentatives
            # d'affilee sur le meme homme, toutes annulees, sont un systeme
            # casse — pas une journee difficile. Trois annulations de suite
            # sans une seule reussite arretent la course et le disent.
            if actives:
                annulations = 0
            else:
                annulations += 1
                if annulations >= 3:
                    journaliser("boucle.arretee", raison="rien n'aboutit",
                                tentatives=faites, annulations=annulations)
                    return 1
            if args.une_fois or (args.max_activations and
                                 faites >= args.max_activations):
                return 0
            if not actives:
                time.sleep(args.intervalle)

