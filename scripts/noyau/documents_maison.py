# -*- coding: utf-8 -*-
"""Documents possedes par les maisons.

Chaque maison tient sa bibliotheque et ses mesures sous
``etat/maisons/<maison>/documents/``. Les lecteurs techniques agregeront ces
sources ; un habitant ne recoit que les chemins de sa maison.
"""
import io
import json
import os


DOCUMENTS = "documents"
LIVRES = "books"
MAINS = "mains.json"
MANIFESTE = "_ordre.json"
SANS_MAISON = "_sans-maison"


class DocumentsMaisonInvalides(ValueError):
    pass


def _lire(chemin):
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


def _registre_maisons(etat):
    chemin = os.path.join(etat, "maisons.json")
    if not os.path.isfile(chemin):
        return []
    maisons = _lire(chemin)
    if isinstance(maisons, dict):
        maisons = maisons.get("maisons") or []
    return maisons if isinstance(maisons, list) else []


def ids_maisons(etat, inclure_sans_maison=False):
    ids = [m.get("id") for m in _registre_maisons(etat)
           if isinstance(m, dict) and m.get("id")]
    return ids + ([SANS_MAISON] if inclure_sans_maison else [])


def dossier(etat, maison_id):
    return os.path.join(etat, "maisons", str(maison_id), DOCUMENTS)


def dossier_livres(etat, maison_id):
    return os.path.join(dossier(etat, maison_id), LIVRES)


def chemins(etat, maison_id):
    """Les documents attribues, tous accessibles aux membres pour le moment."""
    base = dossier(etat, maison_id)
    if not os.path.isdir(base):
        return []
    trouves = []
    main = os.path.join(base, MAINS)
    if os.path.isfile(main):
        trouves.append(main)
    livres = dossier_livres(etat, maison_id)
    if os.path.isdir(livres):
        trouves.extend(os.path.join(livres, nom)
                       for nom in sorted(os.listdir(livres))
                       if nom.endswith(".json") and nom != MANIFESTE
                       and os.path.isfile(os.path.join(livres, nom)))
    return trouves


def maison_de(etat, personnage_id):
    chemin = os.path.join(etat, "personnages.json")
    if not os.path.isfile(chemin):
        return None
    personnages = _lire(chemin)
    if isinstance(personnages, dict):
        personnages = personnages.get("personnages") or []
    personnage = next((p for p in personnages
                        if isinstance(p, dict) and p.get("id") == personnage_id), None)
    if personnage and personnage.get("maison_id"):
        return personnage["maison_id"]

    # Les gens de maison sans lignage explicite (maitre des deniers, geolier,
    # sergent) sont rattaches par le document qu'ils portent. Ce lien est
    # stable apres la migration et ne change pas lorsqu'ils voyagent.
    candidates = set()
    for maison_id in ids_maisons(etat):
        base = dossier_livres(etat, maison_id)
        manifeste = os.path.join(base, MANIFESTE)
        if os.path.isfile(manifeste):
            for ident in _ordre(manifeste):
                livre = _lire(os.path.join(base, ident + ".json"))
                if (livre.get("acteur_id") == personnage_id
                        or personnage_id in (livre.get("lecteurs") or [])):
                    candidates.add(maison_id)
        main = os.path.join(dossier(etat, maison_id), MAINS)
        if os.path.isfile(main):
            for entree in (_lire(main).get("mains") or []):
                porteur = entree.get("porteur") or {}
                if porteur.get("type") == "personnage" \
                        and porteur.get("id") == personnage_id:
                    candidates.add(maison_id)
    return next(iter(candidates)) if len(candidates) == 1 else None


def documents_pour(etat, personnage_id):
    maison_id = maison_de(etat, personnage_id)
    return maison_id, chemins(etat, maison_id) if maison_id else []


def livres_pour(etat, personnage_id):
    maison_id = maison_de(etat, personnage_id)
    if not maison_id:
        return []
    base = dossier_livres(etat, maison_id)
    manifeste = os.path.join(base, MANIFESTE)
    if not os.path.isfile(manifeste):
        return []
    return [_lire(os.path.join(base, ident + ".json"))
            for ident in _ordre(manifeste)]


def _domaines(etat):
    return ids_maisons(etat, inclure_sans_maison=True)


def _documents_mains(etat):
    for maison_id in _domaines(etat):
        chemin = os.path.join(dossier(etat, maison_id), MAINS)
        if os.path.isfile(chemin):
            yield maison_id, chemin, _lire(chemin)


def charger_mains(etat):
    resultat, vus = [], set()
    for maison_id, chemin, brut in _documents_mains(etat):
        if not isinstance(brut, dict) or brut.get("maison_id") != maison_id:
            raise DocumentsMaisonInvalides(
                "%s doit porter maison_id=%s" % (chemin, maison_id))
        for main in brut.get("mains") or []:
            ident = main.get("id") if isinstance(main, dict) else None
            if not ident:
                raise DocumentsMaisonInvalides("main sans id dans %s" % chemin)
            if ident in vus:
                raise DocumentsMaisonInvalides("main en double : %s" % ident)
            vus.add(ident)
            copie = dict(main)
            copie.setdefault("maison_id", maison_id)
            resultat.append(copie)
    return resultat


def _ordre(chemin):
    ordre = _lire(chemin)
    if not isinstance(ordre, list) or not all(isinstance(i, str) for i in ordre):
        raise DocumentsMaisonInvalides("%s doit porter une liste d'ids" % chemin)
    if len(ordre) != len(set(ordre)):
        raise DocumentsMaisonInvalides("id de livre en double dans %s" % chemin)
    return ordre


def sources_livres(etat):
    sources = {}
    for maison_id in _domaines(etat):
        base = dossier_livres(etat, maison_id)
        manifeste = os.path.join(base, MANIFESTE)
        if not os.path.isfile(manifeste):
            continue
        for ident in _ordre(manifeste):
            chemin = os.path.join(base, ident + ".json")
            if not os.path.isfile(chemin):
                raise DocumentsMaisonInvalides("volume absent : %s" % chemin)
            livre = _lire(chemin)
            if not isinstance(livre, dict) or livre.get("id") != ident:
                raise DocumentsMaisonInvalides(
                    "%s ne porte pas l'id %s" % (chemin, ident))
            if ident in sources:
                raise DocumentsMaisonInvalides("livre en double : %s" % ident)
            sources[ident] = chemin
    return sources


def manifestes_livres(etat):
    """maison_id -> (chemin, ordre), y compris les bibliotheques vides."""
    resultat = {}
    for maison_id in _domaines(etat):
        chemin = os.path.join(dossier_livres(etat, maison_id), MANIFESTE)
        if os.path.isfile(chemin):
            resultat[maison_id] = (chemin, _ordre(chemin))
    return resultat


def charger_livres(etat):
    sources = sources_livres(etat)
    return [_lire(chemin) for chemin in sources.values()]


def chemins_source(etat):
    result = []
    for maison_id in _domaines(etat):
        base = dossier_livres(etat, maison_id)
        manifeste = os.path.join(base, MANIFESTE)
        if os.path.isfile(manifeste):
            result.append(manifeste)
    result.extend(sources_livres(etat).values())
    result.extend(chemin for _maison, chemin, _brut in _documents_mains(etat))
    return result
