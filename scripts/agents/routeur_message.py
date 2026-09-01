# -*- coding: utf-8 -*-
"""ROUTEUR MESSAGE — une parole va aux habitants physiquement présents.

La pièce est déjà une adresse. À la minute du joueur, ``presence.resoudre``
dit qui partage réellement sa salle ; chaque habitant reçoit alors les mots
exacts par le canal canonique de la paire, et l'écriture le réveille.

Les gestes et les modes de régie restent du ressort du MJ. Jump conserve sa
préparation dédiée. Aucun classement d'affaire ni appel de sélection ne se
place entre le joueur et les gens devant lui.
"""
import argparse
import json
import os
import uuid

from agents import chambre
from etat.expose import tables
from temps.expose import presence


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SORTIES = os.path.join(RACINE, ".agents-runtime", "routages")


def est_une_parole(action):
    mode = str(action.get("mode") or "").casefold()
    genre = str(action.get("type") or "").casefold()
    return mode in ("dire", "parler") or genre == "parler"


def action_par_ref(personnage, ref):
    """Retrouve l'unique pièce d'inbox portant ``ref``."""
    dossier = os.path.join(RACINE, "etat", "inbox", str(personnage))
    trouves = []
    if os.path.isdir(dossier):
        for nom in sorted(os.listdir(dossier)):
            if not (nom.startswith("action-") and nom.endswith(".json")):
                continue
            chemin = os.path.join(dossier, nom)
            try:
                action = tables.lire(chemin, {})
            except (OSError, ValueError):
                continue
            if isinstance(action, dict) and str(action.get("ref") or "") == str(ref):
                trouves.append((chemin, action))
    if len(trouves) != 1:
        raise ValueError("ref %s trouvée %d fois dans l'inbox de %s" %
                         (ref, len(trouves), personnage))
    return trouves[0]


def _joueurs():
    donnees = tables.lire("joueurs.json", []) or []
    if isinstance(donnees, dict):
        donnees = donnees.get("joueurs") or []
    return {str(j.get("personnage_id") or j.get("id"))
            for j in donnees if isinstance(j, dict)
            and (j.get("personnage_id") or j.get("id"))}


def _date_du_joueur(personnage):
    horloges = tables.lire("horloges.json", {}) or {}
    monde = tables.lire("monde.json", {}) or {}
    return horloges.get(str(personnage)) or monde.get("date") or {
        "annee": 129, "lune": 1, "jour": 1, "minute": 0}


def _meme_piece(a, b):
    if a.get("salle") and b.get("salle"):
        return a.get("salle") == b.get("salle")
    return bool(a.get("lieu") and a.get("lieu") == b.get("lieu"))


def gens_presents(personnage, positions=None, joueurs=None):
    """Habitants non joueurs arrêtés dans la même pièce que le joueur."""
    personnage = str(personnage)
    positions = (presence.resoudre(_date_du_joueur(personnage))
                 if positions is None else positions)
    joueurs = _joueurs() if joueurs is None else set(joueurs)
    ici = (positions or {}).get(personnage)
    if not ici or ici.get("etat") == "en-chemin":
        return []
    resultat = []
    for pid, ou in sorted((positions or {}).items()):
        pid = str(pid)
        if (pid == personnage or pid in joueurs or not isinstance(ou, dict)
                or ou.get("etat") == "en-chemin" or not _meme_piece(ici, ou)):
            continue
        if chambre.existe(pid):
            resultat.append(pid)
    return resultat


def _ecrire_sortie(chemin, valeur):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    temporaire = chemin + ".%s.tmp" % uuid.uuid4().hex
    with open(temporaire, "w", encoding="utf-8", newline="\n") as flux:
        json.dump(valeur, flux, ensure_ascii=False, indent=2)
        flux.write("\n")
    os.replace(temporaire, chemin)


def chemin_sortie(personnage, ref):
    return os.path.join(SORTIES, str(personnage), "%s.json" % ref)


def _router_jump(personnage, ref, action, modele=None):
    from agents import jump, mj
    preparation = jump.preparer(str(action.get("texte") or ""),
                                joueurs=sorted(_joueurs()))
    routage = {
        "ref": ref,
        "decision": "jump",
        "jump": preparation,
        "consigne": (
            "JUMP 1 : le skill système jump-scene est injecté dans ce réveil. "
            "Exécute son processus complet sur cet événement et ce contexte_id, "
            "meuble le flux pendant les appels, avance réellement la clock et "
            "poursuis jusqu'à l'application de l'événement et au jeu de sa scène. "
            "Le joueur reçoit la scène accomplie."),
    }
    resultat = mj.appeler_mj(personnage, "", "JOUEUR", modele=modele,
                             refs=[ref], routage=routage)
    return {"mode": "jump", "mj": {"appele": True,
            "resultat": str(resultat or "")[-500:]}}


def _router_mj(personnage, ref, action, modele=None):
    from agents import mj
    routage = {
        "ref": ref,
        "decision": "direct",
        "consigne": "Cette action arrive directement du joueur, sans sélection intermédiaire.",
    }
    resultat = mj.appeler_mj(personnage, "", "JOUEUR", modele=modele,
                             refs=[ref], routage=routage)
    return {"mode": str(action.get("mode") or action.get("type") or "action"),
            "mj": {"appele": True,
                   "resultat": str(resultat or "")[-500:]}}


def _router_parole(personnage, ref, action, modele=None):
    from agents import billet
    texte = str(action.get("texte") or "")
    presents = gens_presents(personnage)
    retours = []
    for homme in presents:
        try:
            canal, reveil = billet.ecrire(
                personnage, homme, texte, modele=modele, ref=ref)
            retours.append({"homme": homme, "canal": canal,
                            "reveil": reveil, "servi": True})
        except Exception as exc:
            retours.append({"homme": homme, "servi": False,
                            "erreur": "%s: %s" %
                                      (type(exc).__name__, str(exc))})
    return {"mode": "parole", "presents": presents, "hommes": retours,
            "mj": {"appele": False}}


def router_ref(personnage, ref, modele=None):
    """Route une ref d'inbox et conserve un reçu hors fiction."""
    chemin_action, action = action_par_ref(personnage, ref)
    sortie = chemin_sortie(personnage, ref)
    document = {
        "version": "routage-presence/1",
        "joueur_id": str(personnage),
        "ref": str(ref),
        "action": os.path.abspath(chemin_action),
    }
    try:
        mode = str(action.get("mode") or "").casefold()
        if mode == "jump":
            document["routage"] = _router_jump(personnage, ref, action,
                                                 modele=modele)
        elif est_une_parole(action):
            document["routage"] = _router_parole(personnage, ref, action,
                                                   modele=modele)
            if any(r.get("servi") for r in document["routage"]["hommes"]):
                os.remove(chemin_action)
        else:
            document["routage"] = _router_mj(personnage, ref, action,
                                               modele=modele)
        _ecrire_sortie(sortie, document)
        return document
    except Exception as exc:
        document["erreur"] = "%s: %s" % (type(exc).__name__, str(exc))
        _ecrire_sortie(sortie, document)
        raise


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--de", required=True,
                    help="personnage du siège qui a posté")
    ap.add_argument("--ref", required=True,
                    help="référence exacte posée par POST /action")
    ap.add_argument("--modele", default=None)
    a = ap.parse_args(argv)
    print(json.dumps(router_ref(a.de, a.ref, modele=a.modele),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
