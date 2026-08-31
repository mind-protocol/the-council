# -*- coding: utf-8 -*-
"""Porte commune des livres, désormais rangés par maison.

La lecture agrège ``etat/maisons/*/documents/books``. Le manifeste historique
``etat/books/_ordre.json`` reste un repli de migration vide ; toute écriture
nouvelle exige une ``maison_id`` connue et rejoint directement son fonds.
"""
import io
import copy
import json
import os
import re

from etat.expose import tables  # LA PORTE de etat/ : l'ecriture atomique et sa semantique d'erreur
import documents_maison


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
        locaux = [monolithe]
    else:
        locaux = [manifeste] + [os.path.join(dossier, i + ".json")
                                 for i in _ordre(manifeste)]
    return locaux + documents_maison.chemins_source(etat)


def _charger_locaux(etat):
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


def charger(etat):
    livres = _charger_locaux(etat) + documents_maison.charger_livres(etat)
    _index(livres)  # les ids restent globaux, meme si leurs sources sont scindees
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
    # indent=1 : sur un registre de 2 Mo, chaque espace compte.
    tables.ecrire(chemin, valeur, indent=1)


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
        self._manifestes_maisons = documents_maison.manifestes_livres(etat)

    def sauver(self):
        dossier, manifeste, monolithe = _chemins(self.etat)
        ids_avant, avant = _index(self._avant)
        ids_voulus, voulus = _index(self.livres)
        courants_liste = charger(self.etat)
        ids_courants, courants = _index(courants_liste)
        sources = documents_maison.sources_livres(self.etat)
        nouveaux = set(voulus) - set(avant)
        maisons_valides = set(documents_maison.ids_maisons(
            self.etat, inclure_sans_maison=True))
        maisons_nouvelles = {}
        for ident in nouveaux:
            maison_id = voulus[ident].get("maison_id")
            if maison_id not in maisons_valides:
                raise BibliothequeInvalide(
                    "un nouveau livre doit porter une maison_id connue : %s" % ident)
            maisons_nouvelles.setdefault(maison_id, []).append(ident)
        externes = set(sources) | nouveaux
        locaux_avant = [i for i in ids_avant if i not in externes]
        locaux_voulus = [i for i in ids_voulus if i not in externes]
        locaux_courants = [i for i in ids_courants if i not in externes]

        if not os.path.isfile(manifeste):
            if courants_liste != self._avant:
                raise BibliothequeModifiee(
                    "etat/books.json a changé depuis la lecture — rien écrit")
            _ecrire_atomique(monolithe, [voulus[i] for i in locaux_voulus])
            for ident in externes:
                if avant.get(ident) != voulus.get(ident):
                    _ecrire_atomique(sources[ident], voulus[ident])
            self._avant = copy.deepcopy(self.livres)
            return

        touches = {i for i in set(avant) | set(voulus) if avant.get(i) != voulus.get(i)}
        if any(i in externes and i not in voulus for i in externes):
            raise BibliothequeInvalide(
                "un document de maison ne se supprime pas par la bibliothèque globale")
        ordre_touche = locaux_avant != locaux_voulus
        if ordre_touche and locaux_courants != locaux_avant:
            raise BibliothequeModifiee(
                "books/_ordre.json a changé depuis la lecture — rien écrit")
        conflits = [i for i in touches if courants.get(i) != avant.get(i)]
        if conflits:
            raise BibliothequeModifiee(
                "volume modifié depuis la lecture : %s — rien écrit" % conflits[0])

        # Un livre neuf entre directement dans la bibliothèque de sa maison.
        # Le fichier existe avant le manifeste, comme pour la bibliothèque
        # historique ; une autre session qui a bougé ce manifeste fait refuser.
        manifestes_courants = documents_maison.manifestes_livres(self.etat)
        for maison_id in maisons_nouvelles:
            avant_manifeste = self._manifestes_maisons.get(maison_id)
            courant_manifeste = manifestes_courants.get(maison_id)
            if avant_manifeste != courant_manifeste:
                raise BibliothequeModifiee(
                    "documents de %s modifiés depuis la lecture — rien écrit"
                    % maison_id)
            base = documents_maison.dossier_livres(self.etat, maison_id)
            ordre_maison = [i for i in ids_voulus
                            if voulus[i].get("maison_id") == maison_id]
            for ident in maisons_nouvelles[maison_id]:
                _ecrire_atomique(os.path.join(base, ident + ".json"), voulus[ident])
            _ecrire_atomique(os.path.join(base, documents_maison.MANIFESTE),
                              ordre_maison)

        # Les nouveaux fichiers existent avant d'entrer au manifeste. Les
        # anciens en sortent avant d'être supprimés. Un lecteur ne rencontre
        # donc jamais une adresse annoncée sans fichier derrière elle.
        for ident in locaux_voulus:
            if ident in touches:
                _ecrire_atomique(os.path.join(dossier, ident + ".json"), voulus[ident])
        if ordre_touche:
            _ecrire_atomique(manifeste, locaux_voulus)
        for ident in locaux_avant:
            if ident not in locaux_voulus:
                os.remove(os.path.join(dossier, ident + ".json"))
        for ident in set(sources) & touches:
            _ecrire_atomique(sources[ident], voulus[ident])
        # LE JOURNAL DES AFFAIRES, ici et nulle part ailleurs : on tient
        # `avant` et `voulus`, donc le diff est deja fait — et c'est le SEUL
        # point que traversent les seize ecrivains Python et la route serveur.
        # Envelopped : un journal qui casserait une ecriture d'etat serait un
        # remede pire que le mal.
        try:
            import histoire
            histoire.journaliser(avant, voulus, self.etat)
        except Exception:
            pass
        self._avant = copy.deepcopy(self.livres)
        self._manifestes_maisons = documents_maison.manifestes_livres(self.etat)


def ouvrir(etat):
    return Session(etat)
