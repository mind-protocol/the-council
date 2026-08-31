# -*- coding: utf-8 -*-
"""FATIGUE — disponibilite d'une tete, distincte de l'energie du graphe.

La charge de calcul vit en temps reel et decroit. L'avance d'un acteur vit en
temps fictionnel et se resorbe quand son horloge le rattrape. Aucune des deux
ne detruit la reserve topologique : elles ne font que differer une activation.
"""
import datetime as dt
import io
import json
import math
import os
import time

from agents.activation.socle import (
    RACINE, DEMI_VIE_CHARGE_COMPUTE_HEURES,
    MINUTES_COMPUTE_DEMI_ENERGIE, MINUTES_COMPUTE_DEMI_MJ,
    CAPACITE_FERMETURE, CAPACITE_REOUVERTURE,
    HEURES_RETARD_GRACE, HEURES_RETARD_DEMI_ENERGIE,
    VERSION_FATIGUE_ACTEURS)
from agents.activation.horloges import date_civile_acteur, minute_absolue


def _epoch_iso(valeur):
    if not valeur:
        return None
    try:
        texte = str(valeur).replace("Z", "+00:00")
        instant = dt.datetime.fromisoformat(texte)
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=dt.timezone.utc)
        return instant.timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


def charge_compute_decroissante(fiche, maintenant=None):
    """Rend la charge en minutes au present, sans ajouter de nouveau calcul."""
    maintenant = time.time() if maintenant is None else float(maintenant)
    charge = max(0.0, float(fiche.get("compute_minutes") or 0.0))
    maj = fiche.get("compute_maj_mur_s")
    if maj is not None:
        age_h = max(0.0, (maintenant - float(maj)) / 3600.0)
        charge *= math.pow(0.5, age_h / DEMI_VIE_CHARGE_COMPUTE_HEURES)
    fiche["compute_minutes"] = charge
    fiche["compute_maj_mur_s"] = maintenant
    return charge


def facteur_de_charge(charge_minutes, demi_minutes):
    """Capacite residuelle d'un compte pour une charge et une demi-charge."""
    return math.pow(0.5, max(0.0, float(charge_minutes or 0.0)) /
                    float(demi_minutes))


def capacite_acteur(etat, pid, maintenant=None):
    fiche = (etat.setdefault("fatigue_acteurs", {}).setdefault(pid, {}))
    charge = charge_compute_decroissante(fiche, maintenant)
    return facteur_de_charge(charge, MINUTES_COMPUTE_DEMI_ENERGIE), charge


def capacite_zone(etat, mj, maintenant=None):
    """Capacite d'un arbitre, en fusionnant ses anciens noms de zone.

    `mj` absorbe la zone physique des sieges joueurs. Les appels historiques
    ont pu etre comptes sous `mj-peyredragon`, puis sous `mj`; leur cout est le
    meme et doit donc s'additionner avant d'ouvrir une nouvelle session.
    """
    from agents import zone
    comptes = zone.identifiants_de_charge(mj)
    fatigue_mj = etat.setdefault("fatigue_mj", {})
    charge = sum(charge_compute_decroissante(
        fatigue_mj.setdefault(compte, {}), maintenant) for compte in comptes)
    return facteur_de_charge(charge, MINUTES_COMPUTE_DEMI_MJ), charge, comptes


def mettre_a_jour_porte(etat, categorie, identifiant, capacite):
    """Applique l'hysteresis et rend True si un nouveau travail peut partir."""
    portes = etat.setdefault("portes_compute", {}).setdefault(categorie, {})
    fiche = portes.setdefault(identifiant, {})
    etait_fermee = fiche.get("etat") == "fermee"
    if etait_fermee:
        ouverte = float(capacite) >= CAPACITE_REOUVERTURE
    else:
        ouverte = float(capacite) >= CAPACITE_FERMETURE
    fiche.update({
        "etat": "ouverte" if ouverte else "fermee",
        "capacite": round(float(capacite), 6),
        "fermeture": CAPACITE_FERMETURE,
        "reouverture": CAPACITE_REOUVERTURE,
    })
    return ouverte


def instant_fictionnel_secondes(pid, horloge):
    date = date_civile_acteur(pid, horloge)
    minute = minute_absolue(date)
    if minute is None:
        return None
    # date_civile_acteur garde la minute; on recupere les secondes de la vague
    # pour qu'une activation courte ne disparaisse pas dans cet arrondi.
    present = float((horloge or {}).get("present_secondes") or 0.0)
    base = float((horloge or {}).get("base_secondes") or 0.0)
    return float(minute * 60) + max(0.0, present - base) % 60.0


def mesurer_fatigue(fiche, instant_fiction_s=None, maintenant=None):
    charge = charge_compute_decroissante(fiche, maintenant)
    fin = fiche.get("fin_fiction_s")
    # La premiere observation pose l'acteur sur le front courant. Ensuite sa
    # fin de travail est son dernier point d'avancement fictionnel : si le PJ
    # le laisse derriere lui, l'ecart grandit. Recalculer depuis cette ancre
    # evite de remultiplier la meme penalite a chaque polling.
    if fin is None and instant_fiction_s is not None:
        fin = float(instant_fiction_s)
        fiche["fin_fiction_s"] = fin
    ecart_h = 0.0
    if fin is not None and instant_fiction_s is not None:
        ecart_h = max(0.0, (float(instant_fiction_s) - float(fin)) / 3600.0)
    retard_penalise_h = max(0.0, ecart_h - HEURES_RETARD_GRACE)
    facteur_compute = facteur_de_charge(
        charge, MINUTES_COMPUTE_DEMI_ENERGIE)
    facteur_heures = math.pow(
        0.5, retard_penalise_h / HEURES_RETARD_DEMI_ENERGIE)
    return {
        "charge_compute_minutes": charge,
        "ecart_heures": ecart_h,
        "facteur_compute": facteur_compute,
        "facteur_heures": facteur_heures,
        "facteur_total": facteur_compute * facteur_heures,
    }


def ajouter_activation(fiche, compute_minutes, instant_fiction_s,
                       duree_monde_s, maintenant=None):
    """Ajoute le cout reel et avance la tete sur sa propre ligne de temps."""
    maintenant = time.time() if maintenant is None else float(maintenant)
    charge = charge_compute_decroissante(fiche, maintenant)
    fiche["compute_minutes"] = charge + max(0.0, float(compute_minutes or 0.0))
    fiche["compute_maj_mur_s"] = maintenant
    if instant_fiction_s is not None:
        debut = max(float(instant_fiction_s),
                    float(fiche.get("fin_fiction_s") or instant_fiction_s))
        fiche["fin_fiction_s"] = debut + max(0.0, float(duree_monde_s or 0.0))
    return mesurer_fatigue(fiche, instant_fiction_s, maintenant)


def _duree_rapport(chemin):
    try:
        with io.open(chemin, encoding="utf-8") as f:
            rapport = json.load(f)
        activation = rapport.get("_activation") or {}
        # ``duree_ms`` inclut l'orchestration locale. La fatigue demandee est
        # celle du compute modele : ``duree_api_ms``. Le repli ne sert qu'aux
        # anciens rapports qui ne distinguaient pas encore les deux.
        duree_compute = activation.get("duree_api_ms")
        if duree_compute is None:
            duree_compute = activation.get("duree_ms")
        return (max(0.0, float(duree_compute or 0.0)) / 60000.0,
                _epoch_iso(activation.get("cree_le")))
    except (OSError, ValueError, TypeError):
        return 0.0, None


def amorcer_fatigue_historique(etat, maintenant=None):
    """Reconstruit puis synchronise le registre runtime central."""
    version = int(etat.get("version_fatigue_acteurs") or 0)
    maintenant = time.time() if maintenant is None else float(maintenant)
    fatigue = etat.setdefault("fatigue_acteurs", {})
    fatigue_mj = etat.setdefault("fatigue_mj", {})
    # V3 remplace les rapports reussis par le runtime entier. On reconstruit
    # le compute sans perdre l'avance fictionnelle deja portee par les acteurs.
    if version < VERSION_FATIGUE_ACTEURS:
        for fiche in list(fatigue.values()) + list(fatigue_mj.values()):
            if isinstance(fiche, dict):
                fiche.pop("compute_minutes", None)
                fiche.pop("compute_maj_mur_s", None)
        etat["compute_evenements_vus"] = []
    from agents import compute as registre_compute
    vus = set(etat.get("compute_evenements_vus") or [])
    depuis = maintenant - 7 * 24 * 3600
    evenements = (registre_compute.evenements_historiques(depuis)
                  if version < VERSION_FATIGUE_ACTEURS
                  else registre_compute.lire_evenements())
    for entree in evenements:
        eid = entree.get("id")
        fin = float(entree.get("fin_mur_s") or 0.0)
        secondes = max(0.0, float(entree.get("duree_secondes") or 0.0))
        compte = str(entree.get("compte_pour") or entree.get("role") or "")
        if not eid or eid in vus or not compte or not fin or not secondes:
            continue
        cible = fatigue_mj if compte == "mj" or compte.startswith("mj-") else fatigue
        fiche = cible.setdefault(compte, {})
        charge_compute_decroissante(fiche, maintenant)
        age_h = max(0.0, (maintenant - fin) / 3600.0)
        fiche["compute_minutes"] += (secondes / 60.0) * math.pow(
            0.5, age_h / DEMI_VIE_CHARGE_COMPUTE_HEURES)
        vus.add(eid)
    etat["compute_evenements_vus"] = sorted(vus)
    etat["version_fatigue_acteurs"] = VERSION_FATIGUE_ACTEURS
