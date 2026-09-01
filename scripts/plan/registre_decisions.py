# -*- coding: utf-8 -*-
"""Réception append-only des lignes du registre de collaboration.

Une proposition porte séparément ``geste_contributif``,
``resultat_sous_jacent`` et ``decision_reception``. Une réception validée
n'est recevable que si le résultat sous-jacent dit explicitement qu'il a été
vérifié. Le blanc est le mode par défaut ; ``--vraiment`` écrit après toutes
les gardes, par la bibliothèque commune.
"""
import io
import json
import os
import re
import sys
import unicodedata

import bibliotheque
from etat.expose import tables


REGISTRE = "registre-decisions-collaboration"
TABLE = "Décisions"


def _mots(texte):
    brut = unicodedata.normalize("NFD", str(texte or ""))
    sans_accents = "".join(c for c in brut if unicodedata.category(c) != "Mn")
    return re.findall(r"[A-Z]+", sans_accents.upper())


def reception_validee(texte):
    return any(m in {"VALIDE", "VALIDEE", "VALIDATION"} for m in _mots(texte))


def resultat_explicitement_verifie(texte):
    mots = _mots(texte)
    for i, mot in enumerate(mots):
        if mot in {"VERIFIE", "VERIFIEE"}:
            return i == 0 or mots[i - 1] != "NON"
    return False


def valider(proposition):
    requis = ("geste_contributif", "resultat_sous_jacent",
              "decision_reception", "ligne")
    manquants = [champ for champ in requis if champ not in proposition]
    if manquants:
        return "champs manquants : %s" % ", ".join(manquants)
    if not isinstance(proposition["ligne"], list):
        return "ligne doit être une liste de cellules"
    if reception_validee(proposition["decision_reception"]) and not \
            resultat_explicitement_verifie(proposition["resultat_sous_jacent"]):
        return ("une réception VALIDÉE exige un résultat sous-jacent "
                "explicitement VÉRIFIÉ ; un accès ou un envoi réussi ne suffit pas")
    return None


def _table(livre, titre):
    for table in livre.get("tables") or []:
        if table.get("titre") == titre:
            return table
    return None


def preparer(livres, proposition):
    erreur = valider(proposition)
    if erreur:
        return "refus", erreur
    ident = proposition.get("livre") or REGISTRE
    titre = proposition.get("table") or TABLE
    livre = next((b for b in livres if b.get("id") == ident), None)
    if livre is None:
        return "refus", "registre introuvable : %s" % ident
    table = _table(livre, titre)
    if table is None:
        return "refus", "table introuvable : %s" % titre
    ligne = proposition["ligne"]
    colonnes = table.get("colonnes") or []
    if len(ligne) != len(colonnes):
        return "refus", "la ligne a %d cellules ; la table en attend %d" % (
            len(ligne), len(colonnes))
    if any((l.get("cellules") if isinstance(l, dict) else l) == ligne
           for l in table.get("lignes") or []):
        return "deja", table
    return "poser", table


def main(args=None):
    args = list(sys.argv[1:] if args is None else args)
    if not args or "--help" in args or "-h" in args:
        print("usage : recevoir_decision.py <proposition.json> [--vraiment]")
        return 0
    vraiment = "--vraiment" in args
    chemin = next((a for a in args if not a.startswith("--")), None)
    if not chemin or not os.path.isfile(chemin):
        print("proposition introuvable : %s" % (chemin or "—"))
        return 2
    with io.open(chemin, encoding="utf-8") as fichier:
        proposition = json.load(fichier)
    session = bibliotheque.ouvrir(tables.ETAT)
    action, detail = preparer(session.livres, proposition)
    if action == "refus":
        print("REFUS — RIEN N'A ÉTÉ ÉCRIT : %s" % detail)
        return 1
    if action == "deja":
        print("déjà présent à l'identique — rien à écrire")
        return 0
    if not vraiment:
        print("BLANC — ligne recevable ; rien n'a été écrit")
        return 0
    detail.setdefault("lignes", []).append({"cellules": list(proposition["ligne"])})
    session.sauver()
    print("REÇU — une ligne ajoutée à %s / %s" % (
        proposition.get("livre") or REGISTRE, proposition.get("table") or TABLE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
