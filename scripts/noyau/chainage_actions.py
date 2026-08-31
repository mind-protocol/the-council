# -*- coding: utf-8 -*-
"""Chaînage entre les actions de travail et les faits de `actes.json`."""
import io
import json
import os
import re
import glob

import bibliotheque
import histoire

RELATIONS = {"produit", "preuve", "bloque", "modifie", "annule"}
NUMERO = re.compile(r"^\d{3,6}$")
def valider_reference(acte):
    u"""Valide les trois champs ensemble ; un acte sans lien reste valide."""
    presents = [k in acte for k in ("action_id", "affaire_id", "relation_action")]
    if not any(presents):
        return
    if not all(presents):
        raise ValueError("action_id, affaire_id et relation_action vont ensemble")
    if not NUMERO.match(str(acte.get("action_id") or "")):
        raise ValueError("action_id doit être un numéro global de 3 à 6 chiffres")
    if not str(acte.get("affaire_id") or "").startswith("affaire-"):
        raise ValueError("affaire_id doit nommer le livre affaire-* source")
    if acte.get("relation_action") not in RELATIONS:
        raise ValueError("relation_action inconnue : %s" % acte.get("relation_action"))


def _lire(chemin, defaut):
    try:
        with io.open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defaut


def index_actions(etat):
    out = {}
    livres = list(bibliotheque.charger(etat))
    racine = os.path.dirname(os.path.abspath(etat))
    locaux = (glob.glob(os.path.join(racine, "chambres", "*", "books",
                                     "affaire-*.json")) +
              glob.glob(os.path.join(racine, "chambres", "*", "livres",
                                     "affaire-*.json")))
    for chemin in locaux:
        livre = _lire(chemin, None)
        if isinstance(livre, dict):
            livres.append(livre)
    for livre in livres:
        ident = livre.get("id") or ""
        if not ident.startswith("affaire-"):
            continue
        for numero in histoire._index(livre, u"⚔️ Actions"):
            out.setdefault(str(numero), set()).add(ident)
    return out


def completer_depuis_contexte(acte, etat, contexte_id=None):
    u"""Ajoute le lien quand le call travaille directement sur une action.

    ``LE_CONSEIL_CONTEXTE`` est posé par depecher.py. Un contexte qui vise un
    état, un verrou ou un moyen ne force aucun lien ; seul un numéro présent
    dans la table Actions est assez précis pour être déduit sans jugement.
    """
    copie = dict(acte)
    if any(k in copie for k in ("action_id", "affaire_id", "relation_action")):
        return copie
    brut = contexte_id
    if brut is None:
        brut = os.environ.get("LE_CONSEIL_CONTEXTE")
    numero = str(brut or "").strip()
    if not NUMERO.match(numero):
        return copie
    affaires = index_actions(etat).get(numero, set())
    if len(affaires) != 1:
        return copie
    copie.update({"action_id": numero,
                  "affaire_id": next(iter(affaires)),
                  "relation_action": "preuve"})
    return copie


def auditer(etat):
    u"""Rend les liens explicites invalides ; un acte sans lien reste valide."""
    actes = _lire(os.path.join(etat, "actes.json"), [])
    actions = index_actions(etat)
    erreurs = []
    for acte in actes if isinstance(actes, list) else []:
        try:
            valider_reference(acte)
        except ValueError as e:
            erreurs.append("%s : %s" % (acte.get("id") or "(sans id)", e))
            continue
        aid = acte.get("action_id")
        if aid is None:
            continue
        aid = str(aid)
        affaire = acte.get("affaire_id")
        if affaire not in actions.get(aid, set()):
            erreurs.append("%s : action %s absente de %s" %
                           (acte.get("id") or "(sans id)", aid, affaire))
    return erreurs
