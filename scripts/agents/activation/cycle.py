# -*- coding: utf-8 -*-
"""CYCLE — le verrou de la boucle, un cycle complet (diffusion, choix,
appel, energies), et la prevision des prochaines activations.
"""
import collections
import concurrent.futures
import datetime as dt
import io
import json
import math
import os
import sys
import time

from etat.expose import tables
from temps.expose import occupation

from agents.activation.socle import (RACINE, ETAT, DEPOT, ETAT_BOUCLE,
                                     VERROU, ENERGIE_ACTIVATION_MIN,
                                     ENERGIE_MAX, ENERGIE_MIN,
                                     secondes_monde_pour_energie, _court,
                                     journaliser, lire_json,
                                     ecrire_atomique, charger_tissu)
from agents.activation.horloges import (minute_absolue, horloge_directe,
                                        polarites_horloge_acteurs,
                                        appliquer_polarites_horloge)
from agents.activation.graphe import (adjacence, sources_de_charge, diffuser,
                                      importance, clusters_par_lieu,
                                      tache_active, empreinte_tache,
                                      acteur_en_repos, calendrier,
                                      energie_de_tache)
from agents.activation.taches import (choisir_tache,
                                      mettre_a_jour_energie_graphe,
                                      mettre_a_jour_energies)
from agents.activation.continuite import (amorcer_continuite_historique,
                                          enregistrer_continuite)
from agents.activation.appels import appeler_acteur

class VerrouBoucle:
    def __enter__(self):
        os.makedirs(DEPOT, exist_ok=True)
        try:
            fd = os.open(VERROU, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            age = time.time() - os.path.getmtime(VERROU)
            if age < 6 * 3600:
                raise RuntimeError("une boucle tient deja %s" % VERROU)
            os.remove(VERROU)
            fd = os.open(VERROU, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, ("%d %s\n" % (os.getpid(), dt.datetime.now().isoformat()))
                 .encode("ascii", "replace"))
        os.close(fd)
        return self

    def __exit__(self, _type, _value, _traceback):
        try:
            os.remove(VERROU)
        except FileNotFoundError:
            pass


def cycle(args, etat=None):
    journaliser("cycle.depart")
    # LE CACHE D'OCCUPATION, RECALE ICI ET NULLE PART AILLEURS DANS LA BOUCLE.
    # Ce cycle, lui, mesure de son cote (`horloge_directe`) ; mais le serveur,
    # `depecher.py` et `append_flux.py` lisent encore le drapeau `occupe` du
    # fichier, et un drapeau qu'on ne recale jamais est ce qui a endormi deux
    # sieges. On le remet d'aplomb au depart de chaque cycle — c'est le seul
    # moment ou une session tourne a coup sur.
    try:
        _chg, _refuses, _ = occupation.rafraichir(True)
        for m in _chg:
            journaliser("sieges.occupation", acteur=m["personnage_id"],
                        vers="occupe" if m["occupe"] else "vacant",
                        raison=m["raison"],
                        refuse=int(m in _refuses))
    except Exception as bruit:  # jamais bloquant : c'est un cache
        journaliser("sieges.occupation.echec", erreur=str(bruit))
    capacite = int(getattr(args, "capacite_cycle", args.parallele))
    etat = etat or lire_json(ETAT_BOUCLE, {"version": 1, "historique": []})
    journaliser("horloge.lecture")
    horloge, occupes = horloge_directe(etat)
    journaliser("horloge.direct", origine=horloge["source_id"],
                front=horloge["front_id"],
                present_s=round(horloge["present_secondes"], 1))
    journaliser("graphe.lecture")
    noeuds, aretes, evaluation = charger_tissu()
    journaliser("graphe.charge", noeuds=len(noeuds), aretes=len(aretes))
    amorcer_continuite_historique(etat, noeuds)
    journaliser("diffusion.importance")
    scores, adj = importance(noeuds, aretes, evaluation, horloge["source_id"],
                             occupes)
    polarites, _horloge_moyenne = polarites_horloge_acteurs(noeuds, adj)
    energies_graphe = mettre_a_jour_energie_graphe(
        etat, horloge, scores, noeuds, adj, polarites)
    journaliser("diffusion.calendrier")
    disponibilites = calendrier(noeuds, aretes, evaluation,
                                 horloge["source_id"])
    for nid, score in scores.items():
        noeuds[nid]["importance_activation"] = score
    eligibles = mettre_a_jour_energies(
        etat, horloge, scores, energies_graphe,
        disponibilites, noeuds, occupes)
    journaliser("energie.calculee", acteurs=len(eligibles),
                maximum=round(eligibles[0][0], 3) if eligibles else 0)
    if args.acteur:
        eligibles = [x for x in eligibles if x[2] == args.acteur]
    etat["horloge"] = {k: v for k, v in horloge.items()
                       if k != "present_secondes"}
    if not eligibles:
        journaliser("cycle.sans_acteur")
        if not args.sec:
            ecrire_atomique(ETAT_BOUCLE, etat)
        return etat, False
    rotation = etat.setdefault("rotation_activation", {"tour": 1, "vus": []})
    vus_rotation = set(rotation.get("vus") or [])

    def selectionner(exclus_rotation):
        choix = []
        taches_selectionnees = set()
        for energie, score, pid, jauge in eligibles:
            if energie < ENERGIE_ACTIVATION_MIN:
                journaliser("selection.borne", acteur=pid,
                            energie=round(energie, 3),
                            seuil=ENERGIE_ACTIVATION_MIN)
                break
            if pid in exclus_rotation:
                journaliser("selection.rejetee", acteur=pid,
                            energie=round(energie, 3),
                            raison="deja_passe_dans_rotation",
                            tour=rotation.get("tour"))
                continue
            if acteur_en_repos(etat, pid, horloge["present_secondes"]):
                jusqua = ((etat.get("repos") or {}).get("acteurs") or {}).get(pid)
                journaliser("selection.rejetee", acteur=pid,
                            energie=round(energie, 3), raison="repos_acteur",
                            reprendre_a=jusqua)
                continue
            tache = choisir_tache(
                "pers:" + pid, noeuds, aretes, adj, energies_graphe,
                etat=etat, present=horloge["present_secondes"])
            if tache is None:
                journaliser("selection.rejetee", acteur=pid,
                            energie=round(energie, 3), raison="aucune_tache")
                continue
            energie_tache = energie_de_tache(tache, energies_graphe, energie)
            if energie_tache >= ENERGIE_MIN:
                if tache["id"] in taches_selectionnees:
                    journaliser("selection.rejetee", acteur=pid,
                                tache=tache["id"],
                                raison="tache_deja_selectionnee")
                    continue
                choix.append(
                    (energie, score, pid, jauge, tache, energie_tache))
                taches_selectionnees.add(tache["id"])
                if len(choix) >= capacite:
                    break
                continue
            journaliser("selection.rejetee", acteur=pid,
                        energie=round(energie, 3), tache=tache["id"],
                        energie_tache=round(energie_tache, 3),
                        raison="tache_sous_seuil")
        return choix

    selections = selectionner(vus_rotation)
    if not selections and vus_rotation:
        rotation["tour"] = int(rotation.get("tour") or 1) + 1
        rotation["vus"] = []
        vus_rotation.clear()
        journaliser("rotation.nouveau_tour", tour=rotation["tour"])
        selections = selectionner(vus_rotation)
    if not selections:
        journaliser("cycle.attente", raison="aucun couple acteur-tache energise")
        if not args.sec:
            ecrire_atomique(ETAT_BOUCLE, etat)
        return etat, 0

    lots = []
    for energie, score, pid, jauge, tache, energie_tache in selections:
        # La tâche attire et oriente ; l'énergie vient de la personne élue.
        budget = min(100, int(math.floor(energie)))
        budget_secondes = secondes_monde_pour_energie(budget)
        polarite = polarites.get("pers:" + pid) or {}
        lot = {
            "energie": energie, "score": score, "pid": pid,
            "jauge": jauge, "tache": tache,
            "energie_tache": energie_tache, "budget": budget,
        }
        lots.append(lot)
        journaliser("selection.elue", acteur=pid, energie=round(energie, 3),
                    tache=tache["id"], energie_tache=round(energie_tache, 3),
                    budget_energie=budget, budget_s=budget_secondes,
                    flux_horloge=polarite.get("mode"),
                    ecart_horloge_min=round(
                        polarite.get("ecart_minutes", 0.0), 3),
                    horloge_pj=polarite.get("horloge_pj"))
        journaliser("acteur.choisi", acteur=pid, energie=round(energie, 3),
                    importance=round(score, 6), budget=budget)
        journaliser("tache.choisie", id=tache["id"],
                    distance=tache["distance"], creee=tache["creee"],
                    energie=round(energie_tache, 3))
        print("ACTIVATION  %s  energie %.2f · budget %d (%.0f min)  importance %.3f" %
              (pid, energie, budget, budget_secondes / 60, score))
        print("  tache %s · distance %d · %s" %
              (tache["id"], tache["distance"], tache["quoi"][:100]))
        print("  front %s · +%.1fs depuis %s" %
              (horloge["front_id"], horloge["present_secondes"],
               horloge["source_id"]))

    rotation["vus"] = sorted(vus_rotation | {lot["pid"] for lot in lots})
    journaliser("rotation.acteurs_reserves", tour=rotation.get("tour"),
                acteurs=rotation["vus"])

    journaliser("selection.lot", nombre=len(lots), parallele=capacite)
    if args.sec:
        for lot in lots:
            appeler_acteur(
                lot["pid"], lot["tache"], lot["budget"], horloge, noeuds,
                args.modele, args.effort, args.minutes_appel, True,
                args.heartbeat, etat=etat)
        return etat, len(lots)

    for lot in lots:
        journaliser("energie.reservee", acteur=lot["pid"],
                    valeur=round(lot["energie"], 3), plafond=lot["budget"])
        lot["jauge"]["activations"] = int(
            lot["jauge"].get("activations") or 0) + 1
    ecrire_atomique(ETAT_BOUCLE, etat)

    resultats = {}
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(lots), thread_name_prefix="activation") as pool:
        futurs = {
            pool.submit(
                appeler_acteur, lot["pid"], lot["tache"], lot["budget"],
                horloge, noeuds, args.modele, args.effort,
                args.minutes_appel, False, args.heartbeat, etat): lot
            for lot in lots
        }
        for futur in concurrent.futures.as_completed(futurs):
            lot = futurs[futur]
            cle = (lot["pid"], lot["tache"]["id"])
            try:
                resultats[cle] = futur.result()
            except BaseException as e:
                lot["jauge"]["activations"] = max(
                    0, lot["jauge"]["activations"] - 1)
                rotation["vus"] = [x for x in rotation.get("vus") or []
                                   if x != lot["pid"]]
                journaliser("activation.annulee", acteur=lot["pid"],
                            raison=type(e).__name__,
                            erreur=_court(str(e), 400))

    reussies = 0
    for lot in lots:
        pid = lot["pid"]
        tache = lot["tache"]
        cle = (pid, tache["id"])
        if cle not in resultats:
            continue
        cible, depense, rapport = resultats[cle]
        energie = lot["energie"]
        score = lot["score"]
        budget = lot["budget"]
        jauge = lot["jauge"]
        restitue = round(budget - depense, 3)
        activites_rapport = (
            (rapport.get("activation") or {}).get("activites") or [])
        duree_monde = sum(
            int((a.get("temps") or {}).get("duree_s") or 0)
            for a in activites_rapport)
        reserves_noeuds = etat["graphe"]["noeuds"]
        acteur_nid = "pers:" + pid
        energie_acteur_apres = max(0.0, float(energie) - float(depense))
        reserves_noeuds[acteur_nid] = energie_acteur_apres
        jauge["energie"] = energie_acteur_apres
        jauge["disponible_a"] = round(
            float(horloge["present_secondes"]) + duree_monde, 3)
        journaliser("acteur.energie.debitee", acteur=pid,
                    avant=round(energie, 3), energie=depense,
                    duree_monde_s=duree_monde,
                    apres=round(energie_acteur_apres, 3))
        if restitue:
            journaliser("budget.inutilise", acteur=pid, montant=restitue,
                        budget=budget, utilise=depense)
        enregistrer_continuite(
            etat, pid, tache, rapport, horloge, cible, noeuds)
        entree = {
            "qui": pid, "tache": tache["id"], "budget": budget,
            "depense": depense, "restitue": restitue,
            "duree_monde_secondes": duree_monde,
            "energie_avant": round(energie, 3),
            "energie_apres": round(energie_acteur_apres, 3),
            "importance": round(score, 6), "front": horloge["front_id"],
            "present_secondes": round(horloge["present_secondes"], 3),
            "rapport": os.path.relpath(cible, RACINE).replace("\\", "/"),
            "termine_le": dt.datetime.now().astimezone().isoformat(),
        }
        etat.setdefault("historique", []).append(entree)
        journaliser("cycle.termine", acteur=pid, rapport=entree["rapport"])
        reussies += 1

    etat["historique"] = etat.get("historique", [])[-200:]
    ecrire_atomique(ETAT_BOUCLE, etat)
    journaliser("cycle.lot.termine", reussies=reussies,
                annulees=len(lots) - reussies)
    return etat, reussies


def prevoir_activations(limite):
    """Classement instantane de la physique, sans appel ni ecriture.

    L'ordre au-dela du premier reste conditionnel : une activation peut
    modifier le graphe, depenser moins que sa reserve ou durer assez longtemps
    pour recharger un acteur deja passe.
    """
    etat = lire_json(ETAT_BOUCLE, {"version": 1, "historique": []})
    horloge, occupes = horloge_directe(etat)
    noeuds, aretes, evaluation = charger_tissu()
    amorcer_continuite_historique(etat, noeuds)
    scores, adj = importance(noeuds, aretes, evaluation, horloge["source_id"],
                             occupes)
    polarites, _horloge_moyenne = polarites_horloge_acteurs(noeuds, adj)
    energies_graphe = mettre_a_jour_energie_graphe(
        etat, horloge, scores, noeuds, adj, polarites)
    disponibilites = calendrier(noeuds, aretes, evaluation,
                                 horloge["source_id"])
    for nid, score in scores.items():
        noeuds[nid]["importance_activation"] = score
    eligibles = mettre_a_jour_energies(
        etat, horloge, scores, energies_graphe,
        disponibilites, noeuds, occupes)
    resultat = []
    attentes = collections.Counter()
    # TOUT ACTEUR ACTIF PARAIT. On n'ecarte plus personne de la liste : un
    # homme sous le seuil, au repos ou sans tache energisee reste un homme
    # qu'on doit pouvoir voir et lancer a la main depuis l'admin. Le motif
    # d'attente l'accompagne au lieu de le faire disparaitre.
    for energie, score, pid, _jauge in eligibles:
        motifs = []
        if energie < ENERGIE_ACTIVATION_MIN:
            attentes["energie_sous_seuil"] += 1
            motifs.append("énergie sous le seuil")
        if acteur_en_repos(etat, pid, horloge["present_secondes"]):
            attentes["repos_acteur"] += 1
            motifs.append("au repos")
        tache = choisir_tache(
            "pers:" + pid, noeuds, aretes, adj, energies_graphe,
            etat=etat, present=horloge["present_secondes"])
        if tache is None:
            attentes["aucune_tache_disponible"] += 1
            motifs.append("aucune tâche")
            tache = {"id": "", "quoi": "rien à faire aujourd'hui",
                     "distance": 0, "creee": False}
        else:
            energie_tache = energie_de_tache(tache, energies_graphe, energie)
            if energie_tache < ENERGIE_MIN:
                attentes["tache_sous_seuil"] += 1
                motifs.append("tâche peu énergisée")
        budget_energie = min(100, int(math.floor(energie)))
        resultat.append({
            "rang": len(resultat) + 1,
            "qui": pid,
            "nom": (noeuds.get("pers:" + pid) or {}).get("quoi") or pid,
            "energie": round(energie, 3),
            "importance": round(score, 6),
            "budget": budget_energie,
            "duree_monde_secondes": secondes_monde_pour_energie(
                budget_energie),
            "flux_horloge": (polarites.get("pers:" + pid) or {}).get("mode"),
            "ecart_horloge_minutes": round(
                (polarites.get("pers:" + pid) or {}).get("ecart_minutes", 0.0), 3),
            "horloge_pj": (polarites.get("pers:" + pid) or {}).get("horloge_pj"),
            "tache_id": tache["id"],
            "tache": tache["quoi"],
            "distance": tache["distance"],
            "creee": tache["creee"],
            "pret": not motifs,
            "attente": " · ".join(motifs) or None,
        })
        if len(resultat) >= limite:
            break
    return {
        "calcule_le": dt.datetime.now().astimezone().isoformat(),
        "origine": horloge["source_id"],
        "front": horloge["front_id"],
        "present_secondes": round(horloge["present_secondes"], 3),
        "hypothese": ("classement instantane si aucun resultat ne modifie "
                       "le graphe, les disponibilites ou les energies"),
        "attente": dict(attentes),
        "previsions": resultat,
    }

