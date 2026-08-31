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
                                     REPOS_ACTEUR_SECONDES,
                                     MINUTES_COMPUTE_DEMI_MJ,
                                     VERSION_FATIGUE_ACTEURS,
                                     secondes_monde_pour_energie, _court,
                                     journaliser, lire_json,
                                     ecrire_atomique, charger_tissu)
from agents.activation.horloges import (minute_absolue, horloge_directe,
                                        commettre_lot_horloge,
                                        polarites_horloge_acteurs,
                                        appliquer_polarites_horloge)
from agents.activation.fatigue import (amorcer_fatigue_historique,
                                       ajouter_activation,
                                       instant_fictionnel_secondes,
                                       mettre_a_jour_porte,
                                       mesurer_fatigue)
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


VERSION_RUNTIME_ACTIVATION = 2


def migrer_runtime_actuel(etat):
    """Conserve l'historique, réinitialise seulement l'ordonnancement mort.

    La dernière boucle s'est arrêtée avec des ancres de fatigue vieilles de
    plusieurs semaines fictionnelles. Les reprendre telles quelles met toute
    énergie à zéro et rend la boucle restaurée incapable d'élire quiconque.
    """
    if int(etat.get("version_runtime_activation") or 0) >= \
            VERSION_RUNTIME_ACTIVATION:
        return False
    for cle in ("acteurs", "graphe", "source_cle", "rotation_activation",
                "repos", "fatigue_acteurs", "fatigue_mj",
                "portes_compute"):
        etat.pop(cle, None)
    # Les événements compute déjà absorbés ne doivent pas être refacturés.
    etat["version_fatigue_acteurs"] = VERSION_FATIGUE_ACTEURS
    etat["version_runtime_activation"] = VERSION_RUNTIME_ACTIVATION
    journaliser("runtime.migre", version=VERSION_RUNTIME_ACTIVATION,
                historique=len(etat.get("historique") or []))
    return True

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
    migrer_runtime_actuel(etat)
    journaliser("horloge.lecture")
    horloge, occupes = horloge_directe(etat)
    journaliser("horloge.direct", origine=horloge["source_id"],
                front=horloge["front_id"],
                present_s=round(horloge["present_secondes"], 1))
    journaliser("graphe.lecture")
    noeuds, aretes, evaluation = charger_tissu()
    journaliser("graphe.charge", noeuds=len(noeuds), aretes=len(aretes))
    amorcer_continuite_historique(etat, noeuds)
    amorcer_fatigue_historique(etat)
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
        return etat, 0, 0
    rotation = etat.setdefault("rotation_activation", {"tour": 1, "vus": []})
    # UNE ROTATION QUI A DORMI N'EST PLUS UNE ROTATION, C'EST UNE EXCLUSION.
    # Le tour en cours reserve ceux qui viennent de passer, pour etaler les
    # activations : c'est juste tant que la boucle TOURNE. Arretee dix-sept
    # jours, elle reprend avec les memes noms en reserve — et ce sont les plus
    # energises, puisque ce sont eux qui avaient ete elus. Mesure du 31.8 :
    # tour 33, douze reserves dont Otto (53,7), Gerardys (37,1) et Criston
    # (33,9), tous trois sur LEUR propre tache a distance 1 ; le cycle a sec
    # les rejetait tous les trois et elisait le quatrieme. La premiere
    # activation apres une pause n'etait donc jamais la plus juste.
    # On date la reserve, et une reserve plus vieille qu'une journee de monde
    # est echue : la rotation reprend au premier tour.
    pose_a = rotation.get("pose_a")
    age = None if pose_a is None else (horloge["present_secondes"] - float(pose_a))
    if rotation.get("vus") and (age is None or age < 0 or age > 86400):
        journaliser("rotation.echue", tour=rotation.get("tour"),
                    reserves=len(rotation.get("vus") or []),
                    age_s=None if age is None else round(age, 1),
                    note="reserve d'un repere anterieur : on repart au tour 1")
        rotation["tour"] = 1
        rotation["vus"] = []
    vus_rotation = set(rotation.get("vus") or [])
    def selectionner(exclus_rotation):
        choix = []
        taches_selectionnees = set()
        for energie, score, pid, jauge in eligibles:
            capacite_homme = float(jauge.get("facteur_compute") or 1.0)
            homme_ouvert = mettre_a_jour_porte(
                etat, "acteurs", pid, capacite_homme)
            jauge["capacite_compute"] = capacite_homme
            jauge["porte_compute"] = "ouverte" if homme_ouvert else "fermee"
            jauge["mj"] = "mj"
            # Le dépêcheur parle directement à l'homme. L'unique MJ n'est ni
            # réveillé ni facturé ; seule la capacité de l'acteur ferme.
            if not args.acteur and not homme_ouvert:
                journaliser(
                    "selection.rejetee", acteur=pid, energie=round(energie, 3),
                    raison="capacite_compute",
                    porte_acteur=jauge["porte_compute"],
                    capacite_acteur=round(capacite_homme, 3), mj="mj")
                continue
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
        rotation.pop("pose_a", None)
        vus_rotation.clear()
        journaliser("rotation.nouveau_tour", tour=rotation["tour"])
        selections = selectionner(vus_rotation)
    if not selections:
        journaliser("cycle.attente", raison="aucun couple acteur-tache energise")
        if not args.sec:
            ecrire_atomique(ETAT_BOUCLE, etat)
        return etat, 0, 0

    lots = []
    for energie, score, pid, jauge, tache, energie_tache in selections:
        # La tâche attire et oriente ; l'énergie vient de la personne élue.
        budget = min(100, int(math.floor(energie)))
        budget_secondes = secondes_monde_pour_energie(budget)
        polarite = polarites.get("pers:" + pid) or {}
        lot = {
            "energie": energie, "score": score, "pid": pid,
            "energie_brute": float(jauge.get("energie_brute") or energie),
            "jauge": jauge, "tache": tache,
            "energie_tache": energie_tache, "budget": budget,
            "horloge_pj": polarite.get("horloge_pj"),
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
    rotation["pose_a"] = round(float(horloge["present_secondes"]), 3)
    journaliser("rotation.acteurs_reserves", tour=rotation.get("tour"),
                acteurs=rotation["vus"])

    journaliser("selection.lot", nombre=len(lots), parallele=capacite)
    if args.sec:
        for lot in lots:
            horloge_acteur = dict(horloge)
            horloge_acteur["horloge_pj"] = lot.get("horloge_pj")
            appeler_acteur(
                lot["pid"], lot["tache"], lot["budget"], horloge_acteur,
                noeuds,
                args.modele, args.effort, args.minutes_appel, True,
                args.heartbeat, etat=etat)
        return etat, len(lots), len(lots)

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
                {**horloge, "horloge_pj": lot.get("horloge_pj")}, noeuds,
                args.modele, args.effort,
                args.minutes_appel, False, args.heartbeat, etat): lot
            for lot in lots
        }
        for futur in concurrent.futures.as_completed(futurs):
            lot = futurs[futur]
            cle = (lot["pid"], lot["tache"]["id"])
            try:
                resultats[cle] = futur.result()
            except BaseException as e:
                # UN ECHEC DOIT COUTER QUELQUE CHOSE, SINON C'EST UNE BOUCLE.
                # On defaisait tout : le compteur d'activations, et la reserve
                # de rotation. Le meme homme redevenait donc le premier elu, a
                # l'identique, indefiniment — et comme `faites` ne compte que
                # les REUSSIES, `--max-activations` n'etait jamais atteint.
                # Mesure du 31.8 : onze tentatives sur Otto, la meme tache a
                # chaque tour, 3,91 USD, et rien n'aurait arrete la course.
                # On garde donc la reserve (le tour passe au suivant) et l'on
                # met l'homme au repos, comme apres une activation reussie :
                # ce qui a echoue une fois echouera encore dans la minute.
                lot["jauge"]["activations"] = max(
                    0, lot["jauge"]["activations"] - 1)
                repos = etat.setdefault("repos", {}).setdefault("acteurs", {})
                repos[lot["pid"]] = round(
                    float(horloge["present_secondes"])
                    + REPOS_ACTEUR_SECONDES, 3)
                journaliser("activation.annulee", acteur=lot["pid"],
                            raison=type(e).__name__,
                            repos_jusqu_a=repos[lot["pid"]],
                            erreur=_court(str(e), 400))

    reussies = 0
    durees_reussies = []
    # Les appels viennent de finir : le runtime central a pose une entree par
    # processus, y compris ceux du narrateur et les echecs. On les absorbe
    # avant de recalculer la fiche, sans repayer le rapport agrege ci-dessous.
    amorcer_fatigue_historique(etat)
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
        energie_brute = lot["energie_brute"]
        energie_acteur_apres = max(0.0, energie_brute - float(depense))
        reserves_noeuds[acteur_nid] = energie_acteur_apres
        activation_meta = rapport.get("_activation") or {}
        duree_compute_ms = activation_meta.get("duree_api_ms")
        if duree_compute_ms is None:
            duree_compute_ms = activation_meta.get("duree_ms")
        compute_minutes = max(
            0.0, float(duree_compute_ms or 0.0) / 60000.0)
        horloge_acteur = {**horloge, "horloge_pj": lot.get("horloge_pj")}
        instant_fiction = instant_fictionnel_secondes(pid, horloge_acteur)
        mesure_fatigue = ajouter_activation(
            etat.setdefault("fatigue_acteurs", {}).setdefault(pid, {}),
            0.0, instant_fiction, duree_monde)
        jauge["energie_brute"] = energie_acteur_apres
        jauge["energie"] = energie_acteur_apres * mesure_fatigue["facteur_total"]
        jauge["charge_compute_minutes"] = mesure_fatigue["charge_compute_minutes"]
        jauge["ecart_heures"] = mesure_fatigue["ecart_heures"]
        jauge.pop("avance_heures", None)
        jauge["facteur_compute"] = mesure_fatigue["facteur_compute"]
        jauge["facteur_heures"] = mesure_fatigue["facteur_heures"]
        jauge["disponible_a"] = round(
            float(horloge["present_secondes"]) + duree_monde, 3)
        journaliser("acteur.energie.debitee", acteur=pid,
                    avant=round(energie_brute, 3), energie=depense,
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
            # Trace de l'enveloppe du rapport, pas autorite de fatigue : le
            # registre runtime separe maintenant acteur et MJ.
            "duree_rapport_minutes": round(compute_minutes, 3),
            "energie_avant": round(energie, 3),
            "energie_apres": round(jauge["energie"], 3),
            "energie_brute_avant": round(energie_brute, 3),
            "energie_brute_apres": round(energie_acteur_apres, 3),
            "charge_compute_minutes": round(
                mesure_fatigue["charge_compute_minutes"], 3),
            "ecart_heures": round(mesure_fatigue["ecart_heures"], 3),
            "importance": round(score, 6), "front": horloge["front_id"],
            "present_secondes": round(horloge["present_secondes"], 3),
            "rapport": os.path.relpath(cible, RACINE).replace("\\", "/"),
            "termine_le": dt.datetime.now().astimezone().isoformat(),
        }
        etat.setdefault("historique", []).append(entree)
        journaliser("cycle.termine", acteur=pid, rapport=entree["rapport"])
        durees_reussies.append(duree_monde)
        reussies += 1

    avance_horloge = commettre_lot_horloge(horloge, durees_reussies)
    etat["horloge"] = {k: v for k, v in horloge.items()
                       if k != "present_secondes"}
    if avance_horloge:
        journaliser("horloge.commise", avance_s=round(avance_horloge, 3),
                    present_s=round(horloge["present_secondes"], 3),
                    reussies=reussies)
    etat["historique"] = etat.get("historique", [])[-200:]
    ecrire_atomique(ETAT_BOUCLE, etat)
    journaliser("cycle.lot.termine", reussies=reussies,
                annulees=len(lots) - reussies)
    # ON REND AUSSI LES TENTATIVES. `--max-activations` ne comptait que les
    # reussites : une panne qui annule tout ne faisait donc jamais avancer le
    # compteur, et la course ne pouvait pas se terminer. Le troisieme membre
    # est ce qui la borne ; les appelants qui n'en veulent pas depaquettent
    # les deux premiers comme avant.
    return etat, reussies, len(lots)


def prevoir_activations(limite):
    """Classement instantane de la physique, sans appel ni ecriture.

    L'ordre au-dela du premier reste conditionnel : une activation peut
    modifier le graphe, depenser moins que sa reserve ou durer assez longtemps
    pour recharger un acteur deja passe.
    """
    etat = lire_json(ETAT_BOUCLE, {"version": 1, "historique": []})
    migrer_runtime_actuel(etat)
    horloge, occupes = horloge_directe(etat)
    noeuds, aretes, evaluation = charger_tissu()
    amorcer_continuite_historique(etat, noeuds)
    amorcer_fatigue_historique(etat)
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
    for energie, score, pid, jauge in eligibles:
        motifs = []
        mj = "mj"
        cap_homme = float(jauge.get("facteur_compute") or 1.0)
        ouverte_homme = mettre_a_jour_porte(
            etat, "acteurs", pid, cap_homme)
        if not ouverte_homme:
            attentes["porte_acteur_fermee"] += 1
            motifs.append("capacité acteur fermée")
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
            "energie_brute": round(float(jauge.get("energie_brute") or 0.0), 3),
            "charge_compute_minutes": round(
                float(jauge.get("charge_compute_minutes") or 0.0), 3),
            "ecart_heures": round(float(jauge.get("ecart_heures") or 0.0), 3),
            "facteur_compute": round(float(jauge.get("facteur_compute") or 1.0), 6),
            "facteur_heures": round(float(jauge.get("facteur_heures") or 1.0), 6),
            "capacite_compute": round(cap_homme, 6),
            "porte_compute": "ouverte" if ouverte_homme else "fermee",
            "mj": mj,
            "capacite_mj": 1.0,
            "porte_mj": "non-sollicitee",
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
        "charge_mj": {},
        "capacite_zones": {
            "mj": {"compute_minutes": 0.0, "capacite": 1.0,
                   "porte": "non-sollicitee", "comptes": []}},
        "previsions": resultat,
    }
