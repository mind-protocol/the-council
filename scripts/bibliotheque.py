# -*- coding: utf-8 -*-
"""Stockage commun des livres, compatible avec le monolithe et les volumes.

Le dossier n'est actif que si ``etat/books/_ordre.json`` existe. Cela permet
de migrer les lecteurs avant les écrivains sans jamais deviner quelle copie
fait foi. Une bibliothèque activée est stricte : volume absent, identifiant
dupliqué ou fichier dont l'id ne correspond pas à son nom font échouer la
lecture au lieu de retomber silencieusement sur ``books.json``.
"""
import io
import copy
import json
import os
import re


NOM_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
MANIFESTE = "_ordre.json"


class BibliothequeInvalide(ValueError):
    pass


class BibliothequeModifiee(RuntimeError):
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


def _index(livres):
    if not isinstance(livres, list):
        raise BibliothequeInvalide("la bibliothèque doit porter une liste")
    ids = []
    par_id = {}
    for livre in livres:
        if not isinstance(livre, dict) or not NOM_ID.fullmatch(str(livre.get("id") or "")):
            raise BibliothequeInvalide("chaque volume doit porter un id utilisable comme fichier")
        ident = livre["id"]
        if ident in par_id:
            raise BibliothequeInvalide("identifiant de volume en double : %s" % ident)
        ids.append(ident)
        par_id[ident] = livre
    return ids, par_id


def _ecrire_atomique(chemin, valeur):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    temporaire = chemin + ".tmp"
    with io.open(temporaire, "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False, indent=1)
    os.replace(temporaire, chemin)


class Session:
    """Une lecture suivie d'une écriture optimiste.

    Dans le monolithe, toute écriture concurrente fait refuser le lot. Dans le
    dossier, seuls les volumes réellement changés par cette session sont
    comparés : deux mains peuvent donc écrire deux cahiers différents sans se
    recouvrir.
    """

    def __init__(self, etat):
        self.etat = etat
        self.livres = charger(etat)
        self._avant = copy.deepcopy(self.livres)

    def sauver(self):
        dossier, manifeste, monolithe = _chemins(self.etat)
        ids_avant, avant = _index(self._avant)
        ids_voulus, voulus = _index(self.livres)
        courants_liste = charger(self.etat)
        ids_courants, courants = _index(courants_liste)

        if not os.path.isfile(manifeste):
            if courants_liste != self._avant:
                raise BibliothequeModifiee(
                    "etat/books.json a changé depuis la lecture — rien écrit")
            _ecrire_atomique(monolithe, self.livres)
            self._avant = copy.deepcopy(self.livres)
            return

        touches = {i for i in set(avant) | set(voulus) if avant.get(i) != voulus.get(i)}
        ordre_touche = ids_avant != ids_voulus
        if ordre_touche and ids_courants != ids_avant:
            raise BibliothequeModifiee(
                "books/_ordre.json a changé depuis la lecture — rien écrit")
        conflits = [i for i in touches if courants.get(i) != avant.get(i)]
        if conflits:
            raise BibliothequeModifiee(
                "volume modifié depuis la lecture : %s — rien écrit" % conflits[0])

        # Les nouveaux fichiers existent avant d'entrer au manifeste. Les
        # anciens en sortent avant d'être supprimés. Un lecteur ne rencontre
        # donc jamais une adresse annoncée sans fichier derrière elle.
        for ident in ids_voulus:
            if ident in touches:
                _ecrire_atomique(os.path.join(dossier, ident + ".json"), voulus[ident])
        if ordre_touche:
            _ecrire_atomique(manifeste, ids_voulus)
        for ident in ids_avant:
            if ident not in voulus:
                os.remove(os.path.join(dossier, ident + ".json"))
        self._avant = copy.deepcopy(self.livres)


def ouvrir(etat):
    return Session(etat)
