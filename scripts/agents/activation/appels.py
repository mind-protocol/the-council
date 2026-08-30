# -*- coding: utf-8 -*-
"""APPELS — poser le jugement du narrateur, l'appel claude en stream avec
heartbeat, et appeler_acteur : toute la sequence d'une activation.
"""
import concurrent.futures
import datetime as dt
import hashlib
import io
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid

from agents.expose import depecher  # le script d'appel canonique
from etat.expose import tables
from temps.expose import regence

from agents.activation.socle import (RACINE, ETAT, DEPOT, JUGER_PY,
                                     SECONDES_MONDE_PAR_ENERGIE,
                                     DUREE_ACTIVATION_MIN_SECONDES,
                                     secondes_monde_pour_energie,
                                     journaliser, lire_json, ecrire_atomique)
from agents.activation.horloges import minute_absolue
from agents.activation.graphe import continuite_tache
from agents.activation.missions import (mission_activation,
                                        contexte_narrateur_activation,
                                        mission_ouverture_narrateur,
                                        mission_veille_narrateur,
                                        mission_resolution_narrateur,
                                        mission_correction_narrateur,
                                        extraire_appel_pnj,
                                        extraire_tentative,
                                        extraire_relance_acteur,
                                        mission_relance_acteur,
                                        intitule_tache_activation)
from agents.activation.dossier import dossier_activation, contrainte_regence
from agents.activation.rapport import normaliser_rapport_activation
from agents.activation.continuite import (enregistrer_continuite,
                                          _dire_evenement_cli, _court)

def poser_jugement_narrateur(neutre, qui):
    """Installe le hook Stop exclusivement dans la session du narrateur."""
    dossier = os.path.join(neutre, ".claude")
    os.makedirs(dossier, exist_ok=True)
    cible = os.path.join(dossier, "settings.json")
    commande = subprocess.list2cmdline(
        [sys.executable, JUGER_PY, "--qui", qui])
    with io.open(cible, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({
            "hooks": {
                "Stop": [{"hooks": [{
                    "type": "command",
                    "command": commande,
                    "timeout": 240,
                }]}],
            },
        }, ensure_ascii=False, indent=2))
    return cible


def appeler_stream(pid, manuel, mission, sid, modele, effort, minutes, heartbeat,
                   neutre=None, reprendre=False, autoriser_lecture=True,
                   phase="acteur", reglages=None):
    """Appel stream-json, neuf ou repris dans le meme repertoire neutre."""
    if neutre is None:
        with tempfile.TemporaryDirectory(prefix="activation-%s-" % pid) as d:
            return appeler_stream(
                pid, manuel, mission, sid, modele, effort, minutes, heartbeat,
                neutre=d, reprendre=reprendre,
                autoriser_lecture=autoriser_lecture, phase=phase,
                reglages=reglages)
    prompt_systeme = os.path.join(
        neutre, "system-prompt.md" if autoriser_lecture else "CLAUDE.md")
    if not reprendre:
        if autoriser_lecture:
            depecher.poser_letagere(neutre, pid)
            # Le message ne porte plus ses croyances ni ses pensees : il y
            # POINTE. Les poser ici aussi, sinon l'homme active suit une
            # adresse morte — la faute exacte du billet-fichier.
            depecher.poser_la_memoire(neutre, pid)
        with io.open(prompt_systeme, "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(manuel)
    # --restricted : L'ISOLATION DES HOOKS, ET ELLE COUTAIT 100 % DES
    # ACTIVATIONS. Le chemin de la depeche s'isole depuis le 30.8
    # (`mission.appeler`) ; celui-ci ne le faisait pas, et les hooks du niveau
    # UTILISATEUR se declenchaient dans la session engendree. Mesure du 31.8,
    # onze tentatives et 3,91 USD pour zero activation : le narrateur rendait
    # le bon objet — verifie dans son transcript, `{"appel_pnj": {"qui":
    # "otto", ...}}` — puis un hook Stop herite le faisait travailler encore.
    # Comme le parseur lit le DERNIER message de la session, il tombait sur la
    # sortie du hook : « le narrateur a reveille None au lieu de otto », sept
    # fois, plus quatre JSON malformes. Un --settings explicite frappe encore
    # sous --restricted (mesure de mission.py) : le hook de jugement du
    # narrateur et le parloir de l'acteur restent donc charges, et eux seuls.
    commande = ["claude", "-p", "--output-format", "stream-json",
                "--verbose", "--restricted"]
    if autoriser_lecture:
        # Le PNJ reçoit explicitement SON manuel comme prompt système. Il ne
        # dépend plus de la découverte automatique de CLAUDE.md, qui pouvait
        # réinjecter le manuel global du MJ. Le narrateur suit l'autre branche
        # et conserve son fonctionnement automatique inchangé.
        commande += ["--system-prompt-file", prompt_systeme]
        # Le dossier neutre ne contient que le prompt et l'étagère fermée
        # matérialisée pour ce PNJ. Le dépôt canonique n'est pas ajouté.
        # Sous --restricted, `--tools` porte seul la liste : `--allowedTools`
        # n'a plus d'objet (meme motif que depeche/mission.appeler).
        commande += ["--tools", ",".join(depecher.OUTILS)]
    else:
        # Le narrateur reçoit toute sa vérité dans le dossier local du prompt.
        # Il arbitre ; il ne fouille ni n'écrit le monde pendant l'appel.
        commande += ["--tools", ""]
    commande += ["--permission-mode", "acceptEdits"]
    if reglages:
        commande += ["--settings", reglages]
    commande += ["--resume" if reprendre else "--session-id", sid]
    if modele:
        commande += ["--model", modele]
    if effort:
        commande += ["--effort", effort]
    journaliser("cli.depart", acteur=pid, session=sid, phase=phase,
                reprise=reprendre, modele=modele or "defaut",
                effort=effort or "defaut", timeout_s=minutes * 60)
    processus = subprocess.Popen(
        commande, cwd=neutre, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", bufsize=1)
    processus.stdin.write(mission)
    processus.stdin.close()
    messages = queue.Queue()

    def lire_flux(nom, flux):
        try:
            for ligne in iter(flux.readline, ""):
                messages.put((nom, ligne.rstrip("\r\n")))
        finally:
            messages.put((nom, None))

    for nom, flux in (("stdout", processus.stdout), ("stderr", processus.stderr)):
        threading.Thread(target=lire_flux, args=(nom, flux), daemon=True,
                         name="activation-%s-%s" % (pid, nom)).start()

    debut = time.monotonic()
    prochain = debut + heartbeat
    fin = debut + minutes * 60
    ouverts = 2
    resultat = None
    while ouverts or processus.poll() is None:
        maintenant = time.monotonic()
        if maintenant >= fin:
            processus.kill()
            processus.wait(timeout=5)
            journaliser("cli.timeout", acteur=pid, phase=phase,
                        secondes=round(maintenant - debut, 1))
            raise subprocess.TimeoutExpired(commande, minutes * 60)
        attente = min(1.0, max(0.05, prochain - maintenant), fin - maintenant)
        try:
            origine, ligne = messages.get(timeout=attente)
        except queue.Empty:
            origine, ligne = None, None
        if origine is not None:
            if ligne is None:
                ouverts -= 1
            elif origine == "stderr":
                journaliser("cli.stderr", phase=phase,
                            contenu=_court(ligne, 400))
            elif ligne:
                try:
                    ev = json.loads(ligne)
                except json.JSONDecodeError:
                    journaliser("cli.stdout", phase=phase,
                                contenu=_court(ligne, 400))
                else:
                    _dire_evenement_cli(ev)
                    if ev.get("type") == "result":
                        resultat = ev
        maintenant = time.monotonic()
        if maintenant >= prochain:
            journaliser("cli.heartbeat", acteur=pid, phase=phase,
                        secondes=round(maintenant - debut, 1))
            prochain = maintenant + heartbeat
    code = processus.wait()
    if code != 0:
        raise RuntimeError("claude a quitte avec le code %d" % code)
    if resultat is None:
        raise RuntimeError("le flux claude s'est ferme sans resultat")
    return resultat


def appeler_acteur(pid, tache, budget_energie, horloge, noeuds, modele, effort,
                   minutes, sec, heartbeat, etat=None):
    journaliser("appel.dossier", acteur=pid, tache=tache["id"])
    dossier = dossier_activation(pid, tache, horloge, noeuds, etat=etat)
    budget_secondes = secondes_monde_pour_energie(budget_energie)
    contexte_narrateur = contexte_narrateur_activation(
        pid, tache, budget_energie, budget_secondes, horloge, dossier)
    manuel_narrateur = depecher.manuel_narrateur_local(contexte_narrateur)
    manuel_acteur = depecher.manuel_de(
        pid, mode="tentative", contexte=dossier)
    ouverture = mission_ouverture_narrateur(
        pid, tache, budget_energie, budget_secondes, contexte_narrateur)
    journaliser("appel.systeme_narrateur", acteur=pid,
                caracteres=len(manuel_narrateur))
    journaliser("appel.systeme_pnj", acteur=pid,
                caracteres=len(manuel_acteur))
    journaliser("appel.ouverture", acteur=pid, caracteres=len(ouverture),
                budget_energie=budget_energie,
                budget_secondes=budget_secondes)
    if sec:
        journaliser("appel.a_sec", acteur=pid)
        print("\n--- SYSTEME NARRATEUR ---\n")
        print(manuel_narrateur.strip())
        print("\n--- OUVERTURE DU NARRATEUR A SEC ---\n")
        print(ouverture)
        print("--- ACTEUR ---")
        print("Le message exact sera formulé par le narrateur. Le système de "
              "l'acteur fait %d caractères." %
              len(manuel_acteur))
        return None, 0

    sid_narrateur = str(uuid.uuid4())
    sid_acteur = str(uuid.uuid4())
    salle_id = (dossier.get("salle_actuelle") or {}).get("id") or "inconnue"
    role_narrateur = "narrateur-local:" + salle_id
    reponses = []
    corrections = []
    relances_acteur = []
    tentatives_acteur = []
    with tempfile.TemporaryDirectory(
            prefix="narrateur-local-%s-" % salle_id) as neutre_narrateur, \
         tempfile.TemporaryDirectory(
            prefix="acteur-%s-" % pid) as neutre_acteur:
        reglages_narrateur = poser_jugement_narrateur(
            neutre_narrateur, pid)
        reglages_acteur = depecher.poser_le_parloir(neutre_acteur, pid)
        reponse_ouverture = appeler_stream(
            role_narrateur, manuel_narrateur, ouverture, sid_narrateur,
            modele, effort, minutes, heartbeat, neutre=neutre_narrateur,
            reprendre=False, autoriser_lecture=False,
            phase="narrateur.ouverture", reglages=reglages_narrateur)
        reponses.append(reponse_ouverture)
        appel = extraire_appel_pnj(reponse_ouverture, pid)
        journaliser("narrateur.reveille_pnj", acteur=pid,
                    caracteres=len(appel["message"]))
        message_acteur = depecher.message_tentative(
            pid, dossier, appel["message"])

        # LE NARRATEUR VEILLE PENDANT QU'IL TRAVAILLE. Sa session se terminait
        # sur l'appel, et il ne revenait qu'a l'arbitrage : on lui demandait de
        # guider un homme qui n'existait pas encore. On le relance donc EN
        # PARALLELE de l'acteur, sur la meme session, avec pour seul travail de
        # le suivre au parloir et de le depanner. Un echec de cette veille ne
        # doit jamais coûter l'activation : elle est en marge, pas au milieu.
        def veiller():
            try:
                return appeler_stream(
                    role_narrateur, manuel_narrateur,
                    mission_veille_narrateur(pid, tache, appel),
                    sid_narrateur, modele, effort, minutes, heartbeat,
                    neutre=neutre_narrateur, reprendre=True,
                    autoriser_lecture=True, phase="narrateur.veille",
                    reglages=reglages_narrateur)
            except BaseException as e:
                journaliser("narrateur.veille_echouee", acteur=pid,
                            raison=type(e).__name__, erreur=_court(str(e), 200))
                return None

        with concurrent.futures.ThreadPoolExecutor(
                max_workers=2, thread_name_prefix="veille") as duo:
            veille = duo.submit(veiller)
            reponse_acteur = appeler_stream(
                pid, manuel_acteur, message_acteur, sid_acteur,
                modele, effort, minutes, heartbeat,
                neutre=neutre_acteur, phase="pnj.tentative",
                reglages=reglages_acteur)
            veille.cancel()
        reponses.append(reponse_acteur)
        tentative = extraire_tentative(reponse_acteur)
        tentatives_acteur.append(tentative)
        journaliser("pnj.tentative_valide", acteur=pid,
                    verbe=tentative.get("verbe"),
                    caracteres=len(json.dumps(tentative, ensure_ascii=False)))

        for numero_relance in range(3):
            resolution = mission_resolution_narrateur(
                pid, tache, budget_energie, budget_secondes, horloge,
                tentative, contexte_narrateur)
            journaliser("narrateur.arbitrage", acteur=pid,
                        caracteres=len(resolution),
                        passage=numero_relance + 1)
            reponse = appeler_stream(
                role_narrateur, manuel_narrateur, resolution, sid_narrateur,
                modele, effort, minutes, heartbeat, neutre=neutre_narrateur,
                reprendre=True, autoriser_lecture=False,
                phase="narrateur.resolution",
                reglages=reglages_narrateur)
            relance = extraire_relance_acteur(reponse)
            if relance is None:
                break
            reponses.append(reponse)
            if numero_relance >= 2:
                raise RuntimeError(
                    "le narrateur relance encore l'acteur après trois passages")
            relances_acteur.append(relance)
            journaliser("narrateur.relance_acteur", acteur=pid,
                        passage=numero_relance + 1,
                        manques=len(relance.get("manques") or []))
            reprise_acteur = mission_relance_acteur(tache, relance)
            reponse_acteur = appeler_stream(
                pid, manuel_acteur, reprise_acteur, sid_acteur,
                modele, effort, minutes, heartbeat,
                neutre=neutre_acteur, reprendre=True,
                phase="pnj.relance", reglages=reglages_acteur)
            reponses.append(reponse_acteur)
            tentative = extraire_tentative(reponse_acteur)
            tentatives_acteur.append(tentative)
            journaliser("pnj.tentative_relance_valide", acteur=pid,
                        passage=numero_relance + 1,
                        verbe=tentative.get("verbe"))
        else:
            raise RuntimeError("aucun rapport final après les relances acteur")
        # Le MJ se débrouille : les écarts formels réparables repartent dans
        # le même thread narrateur, sans réveiller ni repayer le PNJ.
        for essai in range(3):
            reponses.append(reponse)
            try:
                journaliser("rapport.extraction", acteur=pid,
                            essai=essai + 1)
                rapport_brut, note = depecher.extraire_json(
                    reponse.get("result", ""))
                if rapport_brut is None:
                    raise RuntimeError(
                        "rapport du narrateur illisible : %s" % note)
                rapport = normaliser_rapport_activation(
                    rapport_brut, pid, tache, dossier,
                    budget_energie, budget_secondes)
                activation = rapport.get("activation") or {}
                activites = activation.get("activites") or []
                depense = round(sum(float(x.get("cout_energie") or 0)
                                    for x in activites), 3)
                annoncee = float(activation.get("energie_depensee") or 0)
                duree_monde = sum(int((x.get("temps") or {}).get("duree_s") or 0)
                                   for x in activites)
                if activation.get("issue") not in (
                        "avance", "termine", "bloque", "echoue", "rien"):
                    journaliser("rapport.issue_recadree", acteur=pid,
                                issue=activation.get("issue"))
                    activation["issue"] = "avance"
                # LE BUDGET EST NOTRE COMPTABILITE, PAS SA FAUTE. Une seconde
                # de depassement sur 360 faisait sauter le rapport entier :
                # quatre minutes de session detruites pour un arrondi. On
                # encaisse au plafond, on note, et la journee de l'homme reste.
                minimum = min(DUREE_ACTIVATION_MIN_SECONDES, budget_secondes)
                if abs(depense - annoncee) > 0.001:
                    journaliser("rapport.energie_recadree", acteur=pid,
                                annoncee=annoncee, calculee=depense)
                    activation["energie_depensee"] = depense
                if duree_monde > budget_secondes or duree_monde < minimum:
                    journaliser("rapport.duree_hors_budget", acteur=pid,
                                monde_s=duree_monde, minimum=minimum,
                                plafond=budget_secondes)
                if depense > budget_energie:
                    journaliser("rapport.energie_plafonnee", acteur=pid,
                                depense=depense, plafond=budget_energie)
                    depense = float(budget_energie)
                    activation["energie_depensee"] = depense
                break
            except RuntimeError as erreur:
                journaliser("rapport.refuse", acteur=pid, essai=essai + 1,
                            erreur=_court(str(erreur), 400))
                if essai >= 2:
                    raise
                correction = mission_correction_narrateur(
                    erreur, budget_secondes, horloge)
                corrections.append(correction)
                journaliser("narrateur.corrige", acteur=pid,
                            essai=essai + 2,
                            caracteres=len(correction))
                reponse = appeler_stream(
                    role_narrateur, manuel_narrateur, correction,
                    sid_narrateur, modele, effort, minutes, heartbeat,
                    neutre=neutre_narrateur, reprendre=True,
                    autoriser_lecture=False,
                    phase="narrateur.correction",
                    reglages=reglages_narrateur)

    journaliser("rapport.valide", acteur=pid, depense=depense,
                activites=len(activites), corrections=len(corrections))
    rapport.setdefault("qui", pid)
    duree_ms = sum(int(r.get("duration_ms") or 0) for r in reponses)
    duree_api_ms = sum(int(r.get("duration_api_ms") or 0) for r in reponses)
    cout_usd = sum(float(r.get("total_cost_usd") or 0) for r in reponses)
    rapport["_activation"] = {
        "session": sid_narrateur,
        "session_narrateur": sid_narrateur,
        "session_pnj": sid_acteur,
        "cree_le": dt.datetime.now().astimezone().isoformat(),
        "front": horloge["front_id"],
        "present_secondes": round(horloge["present_secondes"], 3),
        "importance": round(float((noeuds.get("pers:" + pid) or {})
                                  .get("importance_activation", 0.0)), 6),
        "budget": budget_energie,
        "budget_secondes": budget_secondes,
        # Le narrateur est le thread canonique de l'activation. Le PNJ garde
        # son propre thread, auditable, mais ne tranche aucun resultat.
        "system_prompt": manuel_narrateur,
        "system_prompt_source": "scripts/depecher.py:manuel_narrateur_local",
        "system_prompt_sha256": hashlib.sha256(
            manuel_narrateur.encode("utf-8")).hexdigest(),
        "message": ouverture,
        "appel_pnj": appel["message"],
        "system_prompt_pnj": manuel_acteur,
        "system_prompt_pnj_source": "scripts/depecher.py:manuel_de(mode=tentative)",
        "system_prompt_pnj_sha256": hashlib.sha256(
            manuel_acteur.encode("utf-8")).hexdigest(),
        "tentative_pnj": tentative,
        "tentatives_pnj": tentatives_acteur,
        "relances_acteur": relances_acteur,
        "message_resolution": resolution,
        "messages_correction": corrections,
        "modele": modele or reponse.get("model") or "defaut",
        "effort": effort or "defaut",
        "duree_ms": duree_ms,
        "duree_api_ms": duree_api_ms,
        "cout_usd": cout_usd,
        "tours": sum(int(r.get("num_turns") or 0) for r in reponses),
        "usage": reponse.get("usage") or {},
    }
    os.makedirs(DEPOT, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    cible = os.path.join(DEPOT, "%s-%s.json" % (stamp, pid))
    ecrire_atomique(cible, rapport)
    journaliser("rapport.depose", acteur=pid,
                fichier=os.path.relpath(cible, RACINE).replace("\\", "/"))
    # CE QU'UN SIEGE DECIDE SEUL SE CONSIGNE, SINON PERSONNE NE LE RETROUVE.
    # Le registre de regence est ce qu'on rendra au joueur en le rasseyant.
    # Il ne doit jamais coûter une activation : on l'entoure.
    try:
        trace = regence.consigner(pid, rapport, fichier=cible)
        if trace:
            journaliser("regence.consignee", acteur=pid,
                        engagements=len(trace.get("engagements") or []),
                        faits=len(trace.get("faits") or []))
    except Exception as erreur_regence:  # pragma: no cover - garde-fou
        journaliser("regence.consigne_echouee", acteur=pid,
                    raison=type(erreur_regence).__name__,
                    erreur=_court(str(erreur_regence), 200))
    return cible, depense, rapport

