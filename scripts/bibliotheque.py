# -*- coding: utf-8 -*-
"""Stockage commun des livres, compatible avec le monolithe et les volumes.

Le dossier n'est actif que si ``etat/books/_ordre.json`` existe. Cela permet
de migrer les lecteurs avant les écrivains sans jamais deviner quelle copie
fait foi. Une bibliothèque activée est stricte : volume absent, identifiant
dupliqué ou fichier dont l'id ne correspond pas à son nom font échouer la
lecture au lieu de retomber silencieusement sur ``books.json``.
"""
import io
import json
import os
import re


NOM_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
MANIFESTE = "_ordre.json"


class BibliothequeInvalide(ValueError):
    pass


def _chemins(etat):
    dossier = os.path.join(etat, "books")
    manifeste = os.path.join(dossier, MANIFESTE)
    monolithe = os.path.join(etat, "books.json")
    return dossier, manifeste, monolithe


def _lire_json(chemin):
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


def _ordre(manifeste):
    ordre = _lire_json(manifeste)
    if not isinstance(ordre, list) or not all(isinstance(i, str) for i in ordre):
        raise BibliothequeInvalide("books/_ordre.json doit être une liste d'identifiants")
    if len(ordre) != len(set(ordre)):
        raise BibliothequeInvalide("books/_ordre.json contient un identifiant en double")
    mauvais = [i for i in ordre if not NOM_ID.fullmatch(i)]
    if mauvais:
        raise BibliothequeInvalide("identifiant impropre à un nom de fichier : %s" % mauvais[0])
    return ordre


def est_scindee(etat):
    return os.path.isfile(_chemins(etat)[1])


def chemins_source(etat):
    """Tous les fichiers dont la date doit invalider un cache de lecture."""
    dossier, manifeste, monolithe = _chemins(etat)
    if not os.path.isfile(manifeste):
        return [monolithe]
    return [manifeste] + [os.path.join(dossier, i + ".json")
                          for i in _ordre(manifeste)]


def charger(etat):
    dossier, manifeste, monolithe = _chemins(etat)
    if not os.path.isfile(manifeste):
        livres = _lire_json(monolithe)
        if not isinstance(livres, list):
            raise BibliothequeInvalide("etat/books.json doit porter une liste")
        return livres

    livres = []
    for ident in _ordre(manifeste):
        chemin = os.path.join(dossier, ident + ".json")
        try:
            livre = _lire_json(chemin)
        except FileNotFoundError as exc:
            raise BibliothequeInvalide("volume absent : books/%s.json" % ident) from exc
        if not isinstance(livre, dict):
            raise BibliothequeInvalide("books/%s.json doit porter un objet" % ident)
        if livre.get("id") != ident:
            raise BibliothequeInvalide(
                "books/%s.json porte l'id %r" % (ident, livre.get("id")))
        livres.append(livre)
    return livres
