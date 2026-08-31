# -*- coding: utf-8 -*-
"""Petite file temporaire des beats prepares par les PNJ d'un Jump."""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import threading


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
DEPOT = os.path.join(RACINE, ".agents-runtime", "mj", "jump-beats")
TYPES = {"replique", "geste", "recit"}
_VERROU_FILE = threading.Lock()


def _duree_minutes(valeur):
    """Accepte un entier ou une durée textuelle commençant par un nombre."""
    if valeur in (None, ""):
        return 1
    if isinstance(valeur, (int, float)):
        return int(valeur)
    trouve = re.search(r"-?\d+", str(valeur))
    return int(trouve.group(0)) if trouve else 1


def chemin(contexte_id, ref, depot=None):
    nom = re.sub(r"[^a-zA-Z0-9_-]", "-", "%s-%s" % (contexte_id, ref))
    return os.path.join(depot or DEPOT, nom + ".json")


def lire(contexte_id, ref, depot=None):
    try:
        with io.open(chemin(contexte_id, ref, depot), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError, TypeError):
        return None


def _ecrire(document, depot=None):
    dossier = depot or DEPOT
    os.makedirs(dossier, exist_ok=True)
    cible = chemin(document["contexte_id"], document["ref"], dossier)
    tmp = cible + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(document, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, cible)


def initialiser(event_id, contexte_id, ref, hommes=None, noeuds=None,
                depot=None):
    if not event_id or not contexte_id or not ref:
        raise ValueError("event, contexte et ref sont requis")
    if noeuds is None:
        from plan.expose import graphe_causal
        tous, aretes = graphe_causal.charger_tissu()
        graphe = graphe_causal.extraire(event_id, tous, aretes)
        noeuds = [n.get("id") for n in graphe.get("noeuds", [])]
    document = {
        "version": "jump-beats/1", "event_id": str(event_id),
        "contexte_id": str(contexte_id), "ref": str(ref),
        "hommes": list(dict.fromkeys(str(x) for x in (hommes or []))),
        "noeuds": [str(x) for x in noeuds if x], "beats": []}
    if not document["noeuds"]:
        raise ValueError("le sous-graphe causal est vide")
    _ecrire(document, depot)
    return document


def ajouter(event_id, contexte_id, ref, auteur, beats, depot=None):
    # Les hommes de la coupe reviennent en parallèle dans le même processus.
    # Cette section ne protège que le read-modify-write de leur petite file ;
    # elle ne sérialise aucun appel LLM.
    with _VERROU_FILE:
        document = lire(contexte_id, ref, depot)
        if not document or document.get("event_id") != str(event_id):
            raise ValueError("file Jump absente ou autre evenement")
        if document["hommes"] and str(auteur) not in document["hommes"]:
            raise ValueError("auteur hors de la coupe critique")
        permis, ajoutes = set(document["noeuds"]), []
        for brut in beats or []:
            attaches = [str(x) for x in brut.get("noeuds", [])]
            texte = re.sub(r"\s+", " ", str(brut.get("texte") or "")).strip()
            if brut.get("type") not in TYPES or not texte or not attaches \
                    or any(x not in permis for x in attaches):
                continue
            beat = {"id": "beat-%03d" % (len(document["beats"]) + 1),
                    "auteur": str(auteur), "type": brut["type"],
                    "texte": texte[:700], "noeuds": attaches,
                    "duree": min(15, max(0, _duree_minutes(brut.get("duree")))),
                    "statut": "en-attente"}
            document["beats"].append(beat)
            ajoutes.append(beat)
            if len(ajoutes) == 3:
                break
        _ecrire(document, depot)
        return ajoutes


def pousser(contexte_id, ref, depot=None, commande=None, pour=None):
    document = lire(contexte_id, ref, depot)
    beat = next((b for b in (document or {}).get("beats", [])
                 if b.get("statut") == "en-attente"), None)
    if not beat:
        return None
    item = {"type": beat["type"], "texte": beat["texte"],
            "duree": beat["duree"], "contexte_id": str(contexte_id),
            "ref": str(ref)}
    if beat["type"] == "replique":
        item["locuteur_id"] = beat["auteur"]
    else:
        item["acteur_id"] = beat["auteur"]
    commande = commande or [sys.executable,
                             os.path.join(RACINE, "scripts", "append_flux.py")]
    arguments = commande + [json.dumps(item, ensure_ascii=False)]
    if pour:
        arguments.extend(["--pour", str(pour)])
    subprocess.run(arguments,
                   cwd=RACINE, check=True)
    beat["statut"] = "pousse"
    _ecrire(document, depot)
    return item


def fermer(contexte_id, ref, depot=None):
    document = lire(contexte_id, ref, depot)
    for beat in (document or {}).get("beats", []):
        if beat.get("statut") == "en-attente":
            beat["statut"] = "expire"
    if document:
        _ecrire(document, depot)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    action = ap.add_mutually_exclusive_group(required=True)
    action.add_argument("--initialiser", action="store_true")
    action.add_argument("--pousser", action="store_true")
    action.add_argument("--fermer", action="store_true")
    action.add_argument("--lister", action="store_true")
    ap.add_argument("--event"); ap.add_argument("--contexte", required=True)
    ap.add_argument("--ref", required=True); ap.add_argument("--homme", action="append", default=[])
    ap.add_argument("--pour")
    a = ap.parse_args()
    if a.initialiser:
        rendu = initialiser(a.event, a.contexte, a.ref, a.homme)
    elif a.pousser:
        rendu = pousser(a.contexte, a.ref, pour=a.pour)
    elif a.fermer:
        fermer(a.contexte, a.ref); rendu = {"fermee": True}
    else:
        rendu = lire(a.contexte, a.ref) or {}
    print(json.dumps(rendu, ensure_ascii=False, indent=2))
