# -*- coding: utf-8 -*-
"""JUMP 1 — préparer exactement le prochain événement choisi pour le MJ.

Cette couche ne joue rien et ne dépêche personne. Elle choisit la cible
explicite, ou le premier événement à venir, puis rend au MJ le sous-graphe,
le contexte numérique de chambre et la coupe humaine possible. Le MJ garde
l'arbitrage et lance au plus trois appels courts avant de jouer une scène.
"""
import io
import json
import os
import re


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
ETAT = os.path.join(RACINE, "etat")
MAX_HOMMES = 3
MIN_ECART_JUMP_HEURES = 24
MINUTES_PAR_JOUR = 24 * 60


def _lire_json(chemin, defaut):
    try:
        with io.open(chemin, encoding="utf-8") as fichier:
            return json.load(fichier)
    except (OSError, ValueError, TypeError):
        return defaut


def _date(d):
    d = d or {}
    return tuple(int(d.get(k, 0) or 0) for k in
                 ("annee", "lune", "jour", "minute"))


def _minute_absolue(d):
    """Place une date du calendrier de jeu sur une ligne de minutes."""
    d = d or {}
    annee = int(d.get("annee", 0) or 0)
    lune = int(d.get("lune", 1) or 1)
    jour = int(d.get("jour", 1) or 1)
    minute = int(d.get("minute", 0) or 0)
    return (((annee * 12 + lune - 1) * 30 + jour - 1)
            * MINUTES_PAR_JOUR + minute)


def choisir_evenement(consigne="", evenements=None, monde=None):
    evenements = (_lire_json(os.path.join(ETAT, "evenements.json"), [])
                  if evenements is None else evenements)
    monde = (_lire_json(os.path.join(ETAT, "monde.json"), {})
             if monde is None else monde)
    ouverts = [e for e in evenements if isinstance(e, dict)
               and e.get("id") and e.get("statut") == "a-venir"]
    texte = str(consigne or "").casefold()
    nommes = [e for e in ouverts
              if re.search(r"(?<![a-z0-9-]){}(?![a-z0-9-])".format(
                  re.escape(str(e["id"]).casefold())), texte)]
    if len(nommes) > 1:
        raise ValueError("jump ambigu : plusieurs événements sont nommés")
    depart = _minute_absolue((monde or {}).get("date"))
    seuil = depart + MIN_ECART_JUMP_HEURES * 60
    if nommes:
        if _minute_absolue(nommes[0].get("date_prevue")) < seuil:
            raise ValueError(
                "jump trop proche : la cible doit être située à au moins "
                "24 heures du départ")
        return nommes[0]
    candidats = [e for e in ouverts
                  if _minute_absolue(e.get("date_prevue")) >= seuil]
    if not candidats:
        raise ValueError(
            "aucun événement à venir situé à au moins 24 heures pour le jump")
    return min(candidats, key=lambda e: (
        _date(e.get("date_prevue")), -int(e.get("importance") or 0),
        str(e.get("id"))))


def _contexte_mj(event_id, noeuds, aretes):
    cible = "ev:" + str(event_id)
    directs = []
    for a in aretes:
        # Un moment MJ dépend de l'événement : son numéro est précisément le
        # contexte de préparation de cette scène.
        if (a.get("nature") == "depend_de" and a.get("vers") == cible
                and (noeuds.get(a.get("de")) or {}).get("genre") == "moment_mj"):
            directs.append(str(a["de"]))
    return min(directs, key=int) if directs else None


def preparer(consigne="", evenements=None, monde=None, tissu=None,
             joueurs=None):
    cible = choisir_evenement(consigne, evenements=evenements, monde=monde)
    if tissu is None:
        from plan.expose import graphe_causal
        noeuds, aretes = graphe_causal.charger_tissu()
    else:
        noeuds, aretes = tissu
    from plan.expose import graphe_causal
    graphe = graphe_causal.extraire(cible["id"], noeuds, aretes)
    contexte_id = _contexte_mj(cible["id"], noeuds, aretes)
    joueurs = set(joueurs or [])
    hommes = [str(x) for x in (cible.get("acteurs") or [])
              if str(x) not in joueurs]
    hommes = list(dict.fromkeys(hommes))[:MAX_HOMMES]
    conditions = [n for n in graphe["noeuds"]
                  if n.get("genre") == "condition_causale"
                  and any(a.get("de") == n["id"]
                          and a.get("vers") == "ev:" + str(cible["id"])
                          for a in graphe["aretes"])]
    return {
        "version": "jump/1",
        "event": cible,
        "contexte_id": contexte_id,
        "coupe": {
            "maximum_hommes": MAX_HOMMES,
            "hommes_candidats": hommes,
            "prompts": [{
                "type": "test_ou_decision_homme",
                "id": n["id"],
                "prompt": n.get("quoi"),
                "statut": n.get("statut") or "a_evaluer",
            } for n in conditions],
        },
        "graphe": graphe,
        "contrat": {
            "decision_joueur": False,
            "un_seul_evenement": True,
            "ecart_minimum_heures": MIN_ECART_JUMP_HEURES,
            "depeches_attendues": True,
            "arbitrage_mj": True,
            "sortie": "jouer immédiatement une scène puis rendre la main",
        },
    }
