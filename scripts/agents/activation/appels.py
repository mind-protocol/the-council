# -*- coding: utf-8 -*-
"""APPELS — raccord de la boucle au dépêcheur canonique actuel.

L'ancien moteur intercalait un narrateur local, un MJ de zone et un format de
mutations. Ces trois autorités ont disparu : l'homme reçoit le dépôt, agit et
écrit directement les changements d'état dont il est propriétaire.
"""
import datetime as dt
import os
import time
import uuid

from agents.expose import depecher

from agents.activation.socle import (DEPOT, RACINE, ecrire_atomique,
                                     journaliser,
                                     secondes_monde_pour_energie)


def _mission(tache, budget_energie):
    return (
        u"BOUCLE D'ACTIVATION — le graphe t'a élu pour poursuivre cette "
        u"tâche maintenant.\n"
        u"TÂCHE : `%s`\n"
        u"OBJET : %s\n"
        u"BUDGET DE TRAVAIL : %d unités.\n\n"
        u"Agis depuis ta tête, tes documents de maison et l'état réel du "
        u"dépôt. Tu as accès au dépôt : écris directement, par les portes "
        u"canoniques, les changements d'état, d'action, d'étape, d'acte ou "
        u"de mesure que ton travail produit. Ne demande rien au MJ. Si une "
        u"issue dépend d'un autre ou d'un fait absent, écris ton geste et "
        u"laisse seulement cette issue en attente."
        % (tache.get("id") or "sans-id", tache.get("quoi") or "",
           int(budget_energie)))


def appeler_acteur(pid, tache, budget_energie, horloge, noeuds, modele, effort,
                   minutes, sec, heartbeat, etat=None):
    """Lance une journée canonique et rend l'enveloppe attendue par cycle.py."""
    mission = _mission(tache, budget_energie)
    journaliser("appel.depeche", acteur=pid, tache=tache.get("id"),
                fournisseur="runtime-global", sec=bool(sec))
    debut = time.time()
    ok = depecher.depecher(
        pid, mission, modele, minutes or None, bool(sec), attendre=True,
        contexte_id=None, ref=None, mode="journee", forcer_creux=True)
    if sec:
        return None, 0, {}
    if not ok:
        raise RuntimeError("la dépêche canonique de %s a échoué" % pid)

    duree_monde = secondes_monde_pour_energie(budget_energie)
    rapport = {
        "version": "activation-graphe/2",
        "qui": pid,
        "tache": {"id": str(tache.get("id") or ""),
                  "quoi": str(tache.get("quoi") or "")},
        "activation": {
            "issue": "traitee-par-depeche",
            "energie_depensee": float(budget_energie),
            "activites": [{
                "action": {"verbe": "poursuivre", "quoi": mission},
                "temps": {"duree_s": duree_monde},
                "resultats_produits": [],
                "cout_energie": float(budget_energie),
            }],
        },
        "_activation": {
            "cree_le": dt.datetime.now().astimezone().isoformat(),
            "front": horloge.get("front_id"),
            "present_secondes": round(
                float(horloge.get("present_secondes") or 0), 3),
            "budget": int(budget_energie),
            "duree_api_ms": int((time.time() - debut) * 1000),
            "mode": "depeche-directe-repo",
        },
    }
    os.makedirs(DEPOT, exist_ok=True)
    nom = "%s-%s-%s.json" % (
        dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f"),
        uuid.uuid4().hex[:6], pid)
    cible = os.path.join(DEPOT, nom)
    ecrire_atomique(cible, rapport)
    journaliser("appel.depeche.termine", acteur=pid,
                rapport=os.path.relpath(cible, RACINE).replace("\\", "/"))
    return cible, float(budget_energie), rapport
