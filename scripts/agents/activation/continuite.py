# -*- coding: utf-8 -*-
"""CONTINUITE — enregistrer la continuite d'une tache apres une activation,
amorcer la continuite historique, et dire un evenement en CLI.
"""
import json
import os
import re
import time

from agents.activation.socle import (RACINE, DEPOT, REPOS_ACTEUR_SECONDES,
                                     REPOS_PAIRE_SECONDES, journaliser,
                                     lire_json, ecrire_atomique, _court)
from agents.activation.graphe import empreinte_tache, continuite_tache
from agents.activation.mutations import cible_est_tache

def enregistrer_continuite(etat, pid, tache, rapport, horloge, cible, noeuds):
    """Inscrit la causalite validee dans l'overlay, jamais dans l'etat canonique."""
    activation = rapport.get("activation") or {}
    issue = activation.get("issue") or "rien"
    etats = {}
    activites = []
    for activite in activation.get("activites") or []:
        activites.append({
            "quoi": _court(activite.get("quoi"), 260),
            "resultat": _court(activite.get("resultat"), 500),
        })
        for resultat in activite.get("resultats_produits") or []:
            if not isinstance(resultat, dict) or not resultat.get("cible"):
                continue
            etats[str(resultat["cible"])] = {
                "type": resultat.get("type"),
                "apres": resultat.get("apres"),
                "resultat_id": resultat.get("id"),
            }
    present = float(horloge["present_secondes"])
    duree_monde = sum(
        int((activite.get("temps") or {}).get("duree_s") or 0)
        for activite in activation.get("activites") or [])
    fin_activation = present + duree_monde
    precedente = continuite_tache(etat, tache.get("id"), noeuds) or {}
    etats_cumules = dict(precedente.get("etat_cibles") or {})
    etats_cumules.update(etats)
    reprise = fin_activation + REPOS_PAIRE_SECONDES
    continuite = {
        "tache_id": tache.get("id"),
        "acteur": pid,
        "issue": issue,
        "rapport": os.path.relpath(cible, RACINE).replace("\\", "/"),
        "present_secondes": round(present, 3),
        "fin_secondes": round(fin_activation, 3),
        "empreinte_canonique": empreinte_tache(noeuds.get(tache.get("id"))),
        "reprendre_a": round(reprise, 3),
        "suspendue": issue in ("termine", "bloque"),
        "etat_cibles": etats_cumules,
        "activites": (list(precedente.get("activites") or []) + activites)[-6:],
        "suite": activation.get("suite"),
    }
    etat.setdefault("continuite", {})[tache.get("id")] = continuite
    repos = etat.setdefault("repos", {})
    repos.setdefault("acteurs", {})[pid] = round(
        fin_activation + REPOS_ACTEUR_SECONDES, 3)
    repos.setdefault("paires", {})[pid + "|" + str(tache.get("id"))] = round(
        reprise, 3)
    journaliser("continuite.enregistree", acteur=pid, tache=tache.get("id"),
                issue=issue, suspendue=continuite["suspendue"],
                fin_s=round(fin_activation, 3),
                reprendre_a=continuite["reprendre_a"], cibles=len(etats_cumules))


def amorcer_continuite_historique(etat, noeuds):
    """Migre une fois les derniers rapports acceptes sans reprendre leurs adresses douteuses."""
    deja = etat.setdefault("continuite", {})
    vus = set(deja)
    for entree in reversed(etat.get("historique") or []):
        tid = str(entree.get("tache") or "")
        if not tid or tid in vus:
            continue
        chemin = entree.get("rapport")
        if not chemin:
            continue
        rapport = lire_json(os.path.join(RACINE, chemin), {})
        activation = rapport.get("activation") or {}
        issue = activation.get("issue") or "rien"
        etats = {}
        activites = []
        for activite in activation.get("activites") or []:
            activites.append({
                "quoi": _court(activite.get("quoi"), 260),
                "resultat": _court(activite.get("resultat"), 500),
            })
            for resultat in activite.get("resultats_produits") or []:
                if not isinstance(resultat, dict) \
                        or not cible_est_tache(resultat.get("cible"), tid):
                    continue
                # L'ancien arbitre pouvait ecrire ref:action:<id>. L'overlay
                # neuf ne garde que l'etat de la tache sous son id exact.
                etats[tid] = {
                    "type": resultat.get("type"),
                    "apres": resultat.get("apres"),
                    "resultat_id": resultat.get("id"),
                }
        present = float(entree.get("present_secondes") or 0.0)
        deja[tid] = {
            "tache_id": tid,
            "acteur": entree.get("qui"),
            "issue": issue,
            "rapport": chemin,
            "present_secondes": present,
            "empreinte_canonique": empreinte_tache(noeuds.get(tid)),
            "reprendre_a": round(present + REPOS_PAIRE_SECONDES, 3),
            "suspendue": issue in ("termine", "bloque"),
            "etat_cibles": etats,
            "activites": activites[-3:],
            "suite": activation.get("suite"),
            "heritee_historique": True,
        }
        pid = entree.get("qui")
        if pid:
            repos = etat.setdefault("repos", {})
            repos.setdefault("acteurs", {}).setdefault(
                pid, round(present + REPOS_ACTEUR_SECONDES, 3))
            repos.setdefault("paires", {}).setdefault(
                pid + "|" + tid, round(present + REPOS_PAIRE_SECONDES, 3))
        vus.add(tid)


def _dire_evenement_cli(ev):
    """Rend visibles les etapes utiles ; le JSON brut reste dans le journal."""
    genre = ev.get("type") or "inconnu"
    if genre == "system":
        journaliser("cli.systeme", brut=ev, sous_type=ev.get("subtype"),
                    modele=ev.get("model"), outils=len(ev.get("tools") or []))
        return
    if genre in ("assistant", "user"):
        message = ev.get("message") or {}
        blocs = message.get("content") or []
        if not isinstance(blocs, list):
            blocs = [blocs]
        if not blocs:
            journaliser("cli." + genre, brut=ev)
        for bloc in blocs:
            if not isinstance(bloc, dict):
                journaliser("cli." + genre, brut=ev, contenu=_court(bloc))
            elif bloc.get("type") == "tool_use":
                journaliser("cli.outil", brut=ev, nom=bloc.get("name"),
                            entree=_court(json.dumps(bloc.get("input") or {},
                                                     ensure_ascii=False)))
            elif bloc.get("type") == "tool_result":
                journaliser("cli.resultat_outil", brut=ev,
                            erreur=bool(bloc.get("is_error")),
                            contenu=_court(bloc.get("content")))
            elif bloc.get("type") == "text":
                journaliser("cli.texte", brut=ev,
                            contenu=_court(bloc.get("text")))
            else:
                journaliser("cli." + genre, brut=ev,
                            bloc=bloc.get("type") or "?")
        return
    if genre == "result":
        usage = ev.get("usage") or {}
        journaliser("cli.resultat", brut=ev, erreur=bool(ev.get("is_error")),
                    duree_ms=ev.get("duration_ms"), cout=ev.get("total_cost_usd"),
                    entree=usage.get("input_tokens"), sortie=usage.get("output_tokens"),
                    caracteres=len(ev.get("result") or ""))
        return
    journaliser("cli." + genre, brut=ev, sous_type=ev.get("subtype"))

