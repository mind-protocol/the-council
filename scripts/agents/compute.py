# -*- coding: utf-8 -*-
"""COMPUTE — registre central du temps reel consomme par les agents.

Une entree mesure uniquement le temps passe DANS le fournisseur, verrou de
session deja acquis. Les attentes de verrou ne comptent pas; les echecs et les
expirations comptent. Un fichier par appel rend l'ecriture sure entre process.
"""
import glob
import datetime as dt
import io
import json
import os
import time
import uuid


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
DEPOT = os.path.join(RACINE, ".agents-runtime", "compute")
WORK_MAP = os.path.join(RACINE, ".agents-runtime", "compute-work-map")


def _normaliser_identite_travail(identity):
    if identity is None:
        return None
    if not isinstance(identity, dict):
        raise ValueError("work_identity doit etre un objet explicite")
    requis = ("work_id", "attempt_id", "attempt_number", "effect_key")
    manquants = [champ for champ in requis if identity.get(champ) in (None, "")]
    if manquants:
        raise ValueError("work_identity incomplet: %s" % ", ".join(manquants))
    try:
        uuid.UUID(str(identity["work_id"]))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("work_id doit etre un UUID")
    attempt_number = identity["attempt_number"]
    if not isinstance(attempt_number, int) or isinstance(attempt_number, bool) \
            or attempt_number < 1:
        raise ValueError("attempt_number doit etre un entier positif")
    return {
        "work_id": str(identity["work_id"]),
        "attempt_id": str(identity["attempt_id"]),
        "attempt_number": attempt_number,
        "effect_key": str(identity["effect_key"]),
    }


def _ecrire_bordereau(event_id, identity):
    os.makedirs(WORK_MAP, exist_ok=True)
    cible = os.path.join(WORK_MAP, str(event_id) + ".json")
    temporaire = cible + ".tmp-%d-%s" % (os.getpid(), uuid.uuid4().hex)
    contenu = {str(event_id): dict(identity)}
    with io.open(temporaire, "w", encoding="utf-8", newline="\n") as f:
        json.dump(contenu, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(temporaire, cible)
    return cible


def enregistrer(role, compte_pour, session_id, provider, debut_s, fin_s,
                succes, erreur=None, work_identity=None):
    os.makedirs(DEPOT, exist_ok=True)
    identity = _normaliser_identite_travail(work_identity)
    entree = {
        "id": str(uuid.uuid4()),
        "role": str(role or "inconnu"),
        "compte_pour": str(compte_pour or role or "inconnu"),
        "session": str(session_id or ""),
        "provider": str(provider or "inconnu"),
        "debut_mur_s": float(debut_s),
        "fin_mur_s": float(fin_s),
        "duree_secondes": max(0.0, float(fin_s) - float(debut_s)),
        "succes": bool(succes),
        "erreur": None if succes else str(erreur or "echec")[:240],
    }
    if identity:
        entree.update(identity)
    cible = os.path.join(DEPOT, entree["id"] + ".json")
    temporaire = cible + ".tmp-%d" % os.getpid()
    with io.open(temporaire, "w", encoding="utf-8", newline="\n") as f:
        json.dump(entree, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(temporaire, cible)
    if identity:
        entree["work_bordereau"] = _ecrire_bordereau(entree["id"], identity)
    return entree


def lire_evenements():
    resultat = []
    for chemin in glob.glob(os.path.join(DEPOT, "*.json")):
        try:
            with io.open(chemin, encoding="utf-8") as f:
                d = json.load(f)
            if d.get("id") and d.get("fin_mur_s") is not None:
                resultat.append(d)
        except (OSError, ValueError, TypeError):
            continue
    return resultat


def _instant(texte):
    try:
        return dt.datetime.fromisoformat(
            str(texte).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError, OverflowError):
        return None


def _role_du_projet(chemin):
    nom = os.path.basename(os.path.dirname(chemin))
    marque_chambre = "-chambres-"
    marque_zone = "-le-conseil-zones-"
    if marque_chambre in nom:
        return nom.split(marque_chambre, 1)[1]
    if marque_zone in nom:
        return nom.split(marque_zone, 1)[1]
    return None


def _segments_transcript(chemin, role, depuis_s):
    starts, ends = [], []
    try:
        with io.open(chemin, encoding="utf-8", errors="replace") as f:
            for ligne in f:
                try:
                    d = json.loads(ligne)
                except ValueError:
                    continue
                instant = _instant(d.get("timestamp"))
                if instant is None:
                    continue
                if d.get("type") == "queue-operation" \
                        and d.get("operation") == "dequeue":
                    if not starts or instant - starts[-1] > 2.0:
                        starts.append(instant)
                elif d.get("type") == "assistant" and (
                        (d.get("message") or {}).get("stop_reason")
                        in ("end_turn", "stop_sequence")):
                    ends.append(instant)
    except OSError:
        return []
    session = os.path.splitext(os.path.basename(chemin))[0]
    resultat = []
    for i, debut in enumerate(starts):
        suivant = starts[i + 1] if i + 1 < len(starts) else float("inf")
        fins = [x for x in ends if debut <= x < suivant]
        if not fins:
            continue  # un run encore ouvert n'est pas facture avant sa fin
        fin = max(fins)
        if fin < depuis_s:
            continue
        resultat.append({
            "id": "transcript:%s:%.3f" % (session, debut),
            "role": role, "compte_pour": role, "session": session,
            "provider": "claude", "debut_mur_s": debut,
            "fin_mur_s": fin, "duree_secondes": max(0.0, fin - debut),
            "succes": True, "source": "transcript",
        })
    return resultat


def evenements_transcripts(depuis_s):
    magasin = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    patrons = (
        os.path.join(magasin, "*-chambres-*", "*.jsonl"),
        os.path.join(magasin, "*-le-conseil-zones-*", "*.jsonl"),
    )
    resultat, vus = [], set()
    for patron in patrons:
        for chemin in glob.glob(patron):
            if os.path.getmtime(chemin) < depuis_s:
                continue
            role = _role_du_projet(chemin)
            if not role:
                continue
            for entree in _segments_transcript(chemin, role, depuis_s):
                if entree["id"] not in vus:
                    vus.add(entree["id"])
                    resultat.append(entree)
    return resultat


def evenements_activations_legacy(depuis_s):
    """Rapports anterieurs au registre central; attribution agregee a l'acteur."""
    resultat = []
    depot = os.path.join(RACINE, "etat", "activations")
    for chemin in glob.glob(os.path.join(depot, "*.json")):
        if os.path.basename(chemin) == "boucle.json":
            continue
        try:
            with io.open(chemin, encoding="utf-8") as f:
                rapport = json.load(f)
            meta = rapport.get("_activation") or {}
            fin = _instant(meta.get("cree_le")) or os.path.getmtime(chemin)
            if fin < depuis_s:
                continue
            duree = float(meta.get("duree_ms") or 0.0) / 1000.0
            pid = rapport.get("qui")
            if not pid or duree <= 0:
                continue
            resultat.append({
                "id": "activation-legacy:" + os.path.basename(chemin),
                "role": pid, "compte_pour": pid,
                "session": str(meta.get("session") or ""),
                "provider": "legacy", "debut_mur_s": fin - duree,
                "fin_mur_s": fin, "duree_secondes": duree,
                "succes": True, "source": "activation-legacy",
            })
        except (OSError, ValueError, TypeError):
            continue
    return resultat


def evenements_historiques(depuis_s):
    """Backfill borne : transcripts directs + anciens rapports de boucle."""
    resultat = evenements_transcripts(depuis_s)
    resultat.extend(evenements_activations_legacy(depuis_s))
    resultat.extend(lire_evenements())
    uniques = {}
    for entree in resultat:
        uniques[entree["id"]] = entree
    return list(uniques.values())
