# -*- coding: utf-8 -*-
"""Contrat minimal des charges volontaires.

Ce module ne choisit jamais un porteur. Il valide un journal de gestes publics
(`proposer`, `prendre`, `partager`, `transmettre`) et en deduit qui repond de
quoi. Le journal reste la preuve ; l'etat rendu n'est qu'une projection.

Une transmission est une invitation tant que le destinataire ne fait pas lui-
meme un geste `prendre`. Jusque-la, le porteur precedent demeure responsable.
Le partage suit la meme regle et ajoute un porteur sans effacer le premier.
"""
from copy import deepcopy


GESTES = ("proposer", "prendre", "partager", "transmettre")
CHAMPS_CONTRAT = (
    "affaire_id", "piece_id", "engagement", "preuve_attendue",
    "dependances", "date", "limite_autorite",
)


class ChargeInvalide(ValueError):
    pass


def _texte(evenement, champ):
    valeur = evenement.get(champ)
    if not isinstance(valeur, str) or not valeur.strip():
        raise ChargeInvalide("%s est requis" % champ)
    return valeur.strip()


def _base(evenement):
    if not isinstance(evenement, dict):
        raise ChargeInvalide("un geste doit etre un objet")
    eid = _texte(evenement, "id")
    charge_id = _texte(evenement, "charge_id")
    acteur = _texte(evenement, "acteur_id")
    geste = _texte(evenement, "geste").lower()
    if geste not in GESTES:
        raise ChargeInvalide("geste inconnu : %s" % geste)
    return eid, charge_id, acteur, geste


def _projection_vide():
    return {"charges": {}, "evenements": {}}


def appliquer(projection, evenement):
    """Applique un geste et rend une nouvelle projection sans muter l'entree."""
    resultat = deepcopy(projection or _projection_vide())
    resultat.setdefault("charges", {})
    resultat.setdefault("evenements", {})
    eid, charge_id, acteur, geste = _base(evenement)

    precedent = resultat["evenements"].get(eid)
    if precedent is not None:
        if precedent == evenement:
            return resultat
        raise ChargeInvalide("id d'evenement deja employe : %s" % eid)

    charges = resultat["charges"]
    charge = charges.get(charge_id)

    if geste == "proposer":
        if charge is not None:
            raise ChargeInvalide("charge deja proposee : %s" % charge_id)
        contrat = {}
        for champ in CHAMPS_CONTRAT:
            if champ == "dependances":
                deps = evenement.get(champ)
                if not isinstance(deps, list):
                    raise ChargeInvalide("dependances doit etre une liste")
                contrat[champ] = deepcopy(deps)
            else:
                contrat[champ] = _texte(evenement, champ)
        charge = {
            "charge_id": charge_id,
            "proposee_par": acteur,
            "contrat": contrat,
            "porteurs": [],
            "parts": {},
            "partages_en_attente": {},
            "transmissions_en_attente": {},
            "historique": [eid],
        }
        charges[charge_id] = charge
    else:
        if charge is None:
            raise ChargeInvalide("charge inconnue : %s" % charge_id)

        if geste == "prendre":
            origine = evenement.get("origine")
            if origine:
                partage = charge["partages_en_attente"].get(origine)
                transmission = charge["transmissions_en_attente"].get(origine)
                invitation = partage or transmission
                if invitation is None:
                    raise ChargeInvalide("invitation inconnue : %s" % origine)
                if invitation["a"] != acteur:
                    raise ChargeInvalide("seul le destinataire peut accepter")
                if partage:
                    if acteur not in charge["porteurs"]:
                        charge["porteurs"].append(acteur)
                    charge["parts"][acteur] = partage["part"]
                    del charge["partages_en_attente"][origine]
                else:
                    ancien = transmission["de"]
                    if ancien in charge["porteurs"]:
                        charge["porteurs"].remove(ancien)
                    if acteur not in charge["porteurs"]:
                        charge["porteurs"].append(acteur)
                    if ancien in charge["parts"]:
                        charge["parts"][acteur] = charge["parts"].pop(ancien)
                    del charge["transmissions_en_attente"][origine]
            else:
                if charge["porteurs"]:
                    raise ChargeInvalide(
                        "une charge tenue se prend par une invitation de partage ou de transmission")
                charge["porteurs"].append(acteur)

        elif geste == "partager":
            if acteur not in charge["porteurs"]:
                raise ChargeInvalide("seul un porteur peut partager sa charge")
            destinataire = _texte(evenement, "a")
            part = _texte(evenement, "part")
            if destinataire == acteur:
                raise ChargeInvalide("on ne se partage pas une charge a soi-meme")
            charge["partages_en_attente"][eid] = {
                "de": acteur, "a": destinataire, "part": part,
            }

        elif geste == "transmettre":
            if acteur not in charge["porteurs"]:
                raise ChargeInvalide("seul un porteur peut transmettre sa charge")
            destinataire = _texte(evenement, "a")
            if destinataire == acteur:
                raise ChargeInvalide("on ne se transmet pas une charge a soi-meme")
            charge["transmissions_en_attente"][eid] = {
                "de": acteur, "a": destinataire,
            }

        charge["historique"].append(eid)

    resultat["evenements"][eid] = deepcopy(evenement)
    return resultat


def projeter(evenements):
    resultat = _projection_vide()
    for evenement in evenements:
        resultat = appliquer(resultat, evenement)
    return resultat

