# -*- coding: utf-8 -*-
"""Régence : statut des sièges et lecture des passations historiques.

Un siège vacant n'est plus activé automatiquement. La matière conservée ici
sert aux dépêches explicites et à la remise des archives déjà écrites.
"""
from __future__ import print_function

import os

from temps.expose import occupation
from etat.expose import tables


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ETAT = os.path.join(RACINE, "etat")


def lire_json(chemin, defaut):
    return tables.lire(chemin, defaut)


def lire_table(nom, defaut):
    return lire_json(os.path.join(ETAT, nom + ".json"), defaut)


def sieges():
    roster = lire_table("joueurs", [])
    if isinstance(roster, dict):
        roster = roster.get("joueurs") or roster.get("sieges") or []
    return [s for s in roster
            if isinstance(s, dict) and s.get("personnage_id")]


def sieges_vacants():
    return occupation.vacants()


def sieges_occupes():
    return occupation.occupes()


def est_en_regence(pid):
    return bool(pid) and pid in sieges_vacants()


def nom_de(pid):
    for siege in sieges():
        if siege["personnage_id"] == pid:
            return siege.get("nom") or pid
    for personnage in lire_table("personnages", []) or []:
        if isinstance(personnage, dict) and personnage.get("id") == pid:
            return personnage.get("nom") or pid
    return pid


def date_du_monde():
    return (lire_table("monde", {}) or {}).get("date") or {}


def horloge_de(pid):
    return (lire_table("horloges", {}) or {}).get(pid) or date_du_monde()


def dire_date(date):
    if not date:
        return "date inconnue"
    return "an %s, %se lune, %se jour" % (
        date.get("annee"), date.get("lune"), date.get("jour"))


from temps.regence_passation import (  # noqa: E402,F401
    clause_croyance, clause_declencheur, clause_posee, tete_de,
    poser_clause, registre_de, lire_registre, compte_rendu,
    remettre, etat_des_regences, main)
