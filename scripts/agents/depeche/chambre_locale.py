# -*- coding: utf-8 -*-
"""Ce que le brief montre de la chambre propre d'un habitant.

Une chambre ne fait pas foi sur le monde, mais c'est la memoire de l'homme :
le reveiller sans lui donner les chemins de ses propres fichiers ni les pas
encore ouverts de ses affaires locales revient a lui cacher son bureau.

Ce module ne cree et ne corrige rien. Il inventorie recursivement les fichiers
de la chambre, puis lit avec tolerance les volumes ``books/*.json`` qui portent
une table d'actions.
"""
import io
import json
import os
import re
import unicodedata


ETATS_CLOS = {
    "fait", "faite", "faits", "faites",
    "termine", "terminee", "termines", "terminees",
    "acheve", "achevee", "acheves", "achevees",
    "realise", "realisee", "realises", "realisees",
    "abandonne", "abandonnee", "abandonnes", "abandonnees",
    "annule", "annulee", "annules", "annulees",
    "clos", "close", "closes", "ferme", "fermee", "fermes", "fermees",
}


def _chemin(fichier):
    """Chemin absolu copiable, stable dans un brief Windows ou Unix."""
    return os.path.abspath(fichier).replace("\\", "/")


def _cle(texte):
    """Ramene titre et en-tete a des mots comparables, emojis compris."""
    brut = unicodedata.normalize("NFKD", str(texte or ""))
    brut = u"".join(c for c in brut if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", brut.lower()).strip()


def fichiers_de(dossier):
    """Tous les fichiers de la chambre, recursivement, dans l'ordre lexical."""
    if not os.path.isdir(dossier):
        return []
    trouves = []
    for racine, dossiers, fichiers in os.walk(dossier):
        dossiers.sort(key=str.casefold)
        for nom in sorted(fichiers, key=str.casefold):
            trouves.append(_chemin(os.path.join(racine, nom)))
    return trouves


def _index_colonnes(colonnes):
    cles = [_cle(c) for c in colonnes]

    def premier(predicat):
        return next((i for i, cle in enumerate(cles) if predicat(cle)), None)

    ref = premier(lambda c: c in {"n", "no", "numero", "ref", "reference"})
    nom = premier(lambda c: c in {"action", "l action", "nom"}
                  or c.endswith(" action"))
    etat = premier(lambda c: c in {"etat", "statut"}
                   or c.endswith(" etat") or c.endswith(" statut"))
    return ref, nom, etat


def _cellules(ligne, colonnes):
    if isinstance(ligne, dict) and isinstance(ligne.get("cellules"), list):
        return ligne["cellules"]
    if isinstance(ligne, list):
        return ligne
    if isinstance(ligne, dict):
        return [ligne.get(colonne, "") for colonne in colonnes]
    return []


def _actions_ouvertes(table):
    colonnes = table.get("colonnes") or []
    if not isinstance(colonnes, list):
        return []
    i_ref, i_nom, i_etat = _index_colonnes(colonnes)
    if i_ref is None or i_nom is None:
        return []
    actions = []
    for ligne in table.get("lignes") or []:
        cellules = _cellules(ligne, colonnes)

        def valeur(index):
            return cellules[index] if index is not None and index < len(cellules) else ""

        ref, nom, etat = (str(valeur(i) or "").strip()
                          for i in (i_ref, i_nom, i_etat))
        if not ref and not nom:
            continue
        if _cle(etat) in ETATS_CLOS:
            continue
        actions.append({"ref": ref or u"sans référence", "nom": nom or u"sans nom"})
    return actions


def affaires_de(dossier):
    """Affaires locales et leurs actions non closes, sans modifier la chambre."""
    livres = os.path.join(dossier, "books")
    if not os.path.isdir(livres):
        return []
    affaires = []
    for nom_fichier in sorted(os.listdir(livres), key=str.casefold):
        fichier = os.path.join(livres, nom_fichier)
        if not os.path.isfile(fichier) or not nom_fichier.lower().endswith(".json"):
            continue
        try:
            with io.open(fichier, encoding="utf-8") as f:
                volume = json.load(f)
        except (OSError, ValueError):
            continue
        if not isinstance(volume, dict):
            continue
        table_actions = next((t for t in volume.get("tables") or []
                              if isinstance(t, dict)
                              and "action" in _cle(t.get("titre"))), None)
        if table_actions is None:
            continue
        affaires.append({
            "id": str(volume.get("id") or os.path.splitext(nom_fichier)[0]),
            "titre": str(volume.get("titre") or volume.get("id")
                         or os.path.splitext(nom_fichier)[0]),
            "chemin": _chemin(fichier),
            "actions": _actions_ouvertes(table_actions),
        })
    return affaires


def rendre(dossier):
    """Section Markdown injectee telle quelle dans la mission du dispatch."""
    lignes = [
        u"## Tous les fichiers de ta chambre",
        u"",
        u"Voici le chemin exact de chacun de tes fichiers :",
        u"",
    ]
    fichiers = fichiers_de(dossier)
    lignes += [u"- `%s`" % f for f in fichiers] if fichiers else [u"- aucun fichier"]
    lignes += [
        u"",
        u"## Tes affaires locales — actions en cours",
        u"",
        u"Pour chaque affaire de `books/`, voici uniquement la référence et le nom de chaque action non close.",
        u"",
    ]
    affaires = affaires_de(dossier)
    if not affaires:
        lignes.append(u"- aucune affaire locale")
    for affaire in affaires:
        lignes += [
            u"### %s (`%s`)" % (affaire["titre"], affaire["id"]),
            u"",
            u"Fichier : `%s`" % affaire["chemin"],
            u"",
        ]
        if affaire["actions"]:
            lignes += [u"- `%s` — %s" % (a["ref"], a["nom"])
                       for a in affaire["actions"]]
        else:
            lignes.append(u"- aucune action en cours")
        lignes.append(u"")
    return u"\n".join(lignes).rstrip() + u"\n"
