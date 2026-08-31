# -*- coding: utf-8 -*-
"""CLI — l'entree de scripts/depecher.py, gelee (la facade l'appelle par
la porte agents/expose.py).
"""
import argparse
import io
import json
import os
import sys
import time

from agents.depeche.brief import (RACINE, ETAT, DEPOT_RAPPORTS, lire,
                                  date_du_monde, identifiant_de_session,
                                  id_item_affaire,
                                  a_convoquer, brief_de,
                                  dans_la_salle, dans_le_rayon,
                                  les_pj, salles_peuplees)
from agents.depeche.mission import depecher, appeler, extraire_json
from agents.depeche.retour import verser_sur_le_champ, _poser

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qui", action="append", default=[],
                    help="un homme, repetable")
    ap.add_argument("--tous", action="store_true",
                    help="tous ceux qui doivent une journee")
    ap.add_argument("--salle", action="append", default=[],
                    help="toute une salle, PJ exclus — repetable")
    ap.add_argument("--salles", action="store_true",
                    help="dire quelles salles sont peuplees, et s'en tenir la")
    ap.add_argument("--autour", action="append", default=[],
                    help="tous ceux a portee de quelqu'un ou d'une salle")
    ap.add_argument("--rayon", type=float, default=10.0,
                    help="la portee en metres reels (defaut 10)")
    ap.add_argument("--front", type=int, default=4,
                    help="combien partent ensemble (1 = en file)")
    ap.add_argument("--mission", default="",
                    help="consigne du jour, en plus de son brief")
    ap.add_argument("--contexte", default=None, metavar="N_ITEM",
                    help="numero d'un item d'affaire generale (ex. 23030, "
                         "#23030 ou 'n° 23030') : session et fil de chambre "
                         "distincts pour cet item")
    ap.add_argument("--ref", default=None,
                    help="ref du message joueur à conserver dans la session")
    ap.add_argument("--mode", choices=("journee", "reponse", "discussion"),
                    default="journee",
                    help="instructions du brief : journée autonome, réponse "
                         "courte, ou réponse envoyée dans une discussion")
    ap.add_argument("--modele", default=None,
                    help="opus | sonnet | fable — defaut : celui de la session")
    ap.add_argument("--minutes", type=int, default=None,
                    help="borner l'appel a N minutes ; par defaut la"
                         " session n'expire pas")
    ap.add_argument("--sec", action="store_true",
                    help="montre tout, n'appelle rien, ne coute rien")
    # CALL ou CAST (docs/habitant.md §4). Le DEFAUT reste le call — attendre
    # et rendre le rapport, le comportement historique — tant que les
    # reveils-bancs 3-5 n'ont pas tourne. --cast est une OPTION nouvelle :
    # spawn detache, stdout dans fil/ de sa chambre, la suite par les canaux.
    ap.add_argument("--cast", action="store_true",
                    help="lancer une vie sans l'attendre (detache, log en"
                         " chambre) — le call reste le defaut")
    ap.add_argument("--attendre", action="store_true",
                    help="forcer le call (deja le defaut ; prime sur --cast)")
    a = ap.parse_args()
    if a.contexte is not None:
        try:
            a.contexte = id_item_affaire(a.contexte)
        except ValueError as e:
            ap.error(str(e))
    attendre = a.attendre or not a.cast
    if a.mode != "journee" and not attendre:
        ap.error("--mode reponse/discussion exige un call attendu, pas --cast")

    if a.salles:
        pj = les_pj()
        print(u"LES SALLES PEUPLEES")
        for s, g in sorted(salles_peuplees().items(),
                           key=lambda x: (-len(x[1]), x[0] or u"")):
            if not s:
                continue
            hors = [q for q in g if q not in pj]
            print(u"  %-24s %2d a depecher%s" % (
                s, len(hors),
                u"   (%d PJ ecarte(s))" % (len(g) - len(hors))
                if len(g) - len(hors) else u""))
        return

    # On additionne les cibles, sans jamais retenir quelqu'un deux fois : la
    # meme personne peut etre nommee et se trouver dans une salle demandee.
    gens, vus = [], set()
    ecartes, aveugles = [], []
    autour = []
    for c in a.autour:
        d, e, av = dans_le_rayon(c, a.rayon)
        autour += d
        ecartes += e
        aveugles += av
        print(u"  a %g m de %s : %d homme(s)%s"
              % (a.rayon, c, len(d), u" + %d PJ" % len(e) if e else u""))
    if aveugles:
        # On ne tait jamais ce qu'on n'a pas pu voir.
        print(u"  sans adresse physique, donc hors du rayon quoi qu'il arrive :"
              u"\n    %s" % u", ".join(sorted(set(aveugles))))
    for source in (list(a.qui),
                   a_convoquer() if a.tous else [],
                   [q for s in a.salle for q in dans_la_salle(s)[0]],
                   autour):
        for q in source:
            if q not in vus:
                vus.add(q)
                gens.append(q)
    for s in a.salle:
        ecartes += dans_la_salle(s)[1]
    # Un PJ nomme a la main est ecarte comme les autres : la regle ne se
    # contourne pas en le demandant explicitement.
    pj = les_pj()
    nommes_pj = [q for q in gens if q in pj]
    gens = [q for q in gens if q not in pj]
    ecartes += nommes_pj
    if ecartes:
        print(u"  PJ ecarte(s), on ne les joue jamais : %s"
              % u", ".join(sorted(set(ecartes))))
    if not gens:
        raise SystemExit("Personne. --qui <homme>, --salle <salle>, --tous, "
                         "ou --salles pour voir.")

    date = date_du_monde()
    print(u"DEPECHER — le %d.%d.%d · %d homme(s)%s"
          % (date + (len(gens), u" · A SEC" if a.sec else u"")))
    ok = 0
    if a.sec or a.front <= 1 or len(gens) == 1 or not attendre:
        # Les casts n'ont pas besoin d'un pool : ils partent detaches.
        for qui in gens:
            if depecher(qui, a.mission, a.modele, a.minutes, a.sec,
                        attendre=attendre, contexte_id=a.contexte, ref=a.ref,
                        mode=a.mode):
                ok += 1
    else:
        # ILS PARTENT ENSEMBLE. Une journee d'homme se paie en minutes ; sept
        # en file en prendraient sept fois, et une salle entiere ne se
        # depecherait jamais. Ils n'ont rien a se dire, ne partagent aucun
        # fichier et n'ecrivent nulle part : chacun a son dossier, sa session
        # et ses documents de maison, et le seul ecrivain reste ce processus-ci, a la fin.
        # `--front 1` rend la file a qui veut suivre un echec a la trace.
        import concurrent.futures as cf
        print(u"  (%d de front)" % min(a.front, len(gens)))
        with cf.ThreadPoolExecutor(max_workers=a.front) as pool:
            envoyes = {pool.submit(depecher, q, a.mission, a.modele,
                                   a.minutes, False, True, a.contexte,
                                   a.ref, a.mode): q
                       for q in gens}
            for fini in cf.as_completed(envoyes):
                try:
                    if fini.result():
                        ok += 1
                except Exception as e:
                    print(u"  %-18s ECHEC — %s" % (envoyes[fini], e))
    if not a.sec and not attendre:
        print(u"\n%d/%d partis detaches. Leurs logs vivent dans fil/ de leur"
              u" chambre ; leurs retours arriveront par leurs versements."
              % (ok, len(gens)))
        return
    if not a.sec:
        if a.mode != "journee":
            print(u"\n%d/%d %s(s) rendue(s). Aucun rapport de journee ni mot "
                  u"de reprise n'a ete ecrit."
                  % (ok, len(gens), a.mode))
        else:
            print(u"\n%d/%d rentres. Leurs pensees sont versees ; leurs "
                  u"changements de registre sont des PROPOSITIONS."
                  % (ok, len(gens)))
            print(u"  python scripts/verser_cahier.py             # a sec, montre tout")
            print(u"  python scripts/verser_cahier.py --vraiment  # écrit dans les documents de maison")

