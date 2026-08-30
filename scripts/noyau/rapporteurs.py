# -*- coding: utf-8 -*-
# Le registre des rapporteurs — qui doit tourner, et quand il a tourné pour la
# dernière fois SANS TOMBER.
#
# POURQUOI CE FICHIER EXISTE. Le 24 août 2026, `couverture.py` était mort depuis
# des jours. Un `re.search("ouverture", ...)` sans bornes de mot matchait à
# l'intérieur de « la c-ouverture de bois » ; le mémento était promu affaire ;
# `refaire()` mourait dessus sur un KeyError. Les quatre registres dérivés du
# plan avaient donc cessé d'être régénérés, et rien ne le disait.
#
# Ce n'est pas faute de garde. `verifier_registres_derives` existait déjà et
# faisait son travail : elle a signalé 645 lignes sur le disque contre 664
# dérivées des cahiers. Mais elle l'a dit en `avertissement`, au milieu de
# quatre-vingt-dix autres, et quand elle-même n'arrivait pas à recalculer, elle
# le disait en `note` — la sévérité la plus basse du rapport.
#
# LA LEÇON, ET ELLE EST GÉNÉRALE : « le dérivé a dérivé » et « le producteur est
# mort » sont deux faits différents, et le second est le seul invisible. Un écart
# de lignes peut être normal — on vient d'écrire dans un cahier et l'on n'a pas
# encore relancé. Un producteur qui n'a pas abouti depuis six jours n'est jamais
# normal, et personne ne le remarque, parce qu'un outil qui se tait ressemble
# exactement à un outil qui n'a rien à dire.
#
# Ce module ne mesure donc pas l'état : il mesure LE BATTEMENT DE CEUX QUI
# MESURENT. C'est le seul endroit du dépôt où l'on surveille la surveillance.
#
# COMMENT ON S'EN SERT — une ligne à la fin d'un producteur, sur le chemin du
# succès et nulle part ailleurs :
#
#     import rapporteurs; rapporteurs.battre("couverture", "47 couvertures")
#
# Un producteur qui plante ne bat pas, et c'est tout le mécanisme : on n'a rien
# à attraper, rien à envelopper dans un try. L'absence de battement EST le
# signal. Ne jamais battre « au cas où » avant que le travail soit écrit.
import io
import json
import os
import tempfile
import time

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FICHIER = os.path.join(RACINE, "etat", "rapporteurs.json")

# Ce qu'on attend, et à quelle cadence EN JOURS RÉELS — pas en jours de jeu.
# Ce sont des cadences d'outillage : elles se comptent en temps de développeur.
# La cadence est le délai au-delà duquel le silence devient une anomalie GRAVE.
# Elle est large à dessein : on ne veut pas d'un rapport qui crie tous les matins,
# on veut un rapport qui crie le jour où quelque chose est cassé depuis trop
# longtemps pour qu'on s'en souvienne.
ATTENDUS = [
    ("couverture", 3,
     "python scripts/couverture.py",
     "les couvertures d'affaire, recalculees depuis les cahiers"),
    ("couverture-registres", 3,
     "python scripts/couverture.py --registres",
     "les quatre registres derives du plan (etats-cibles, verrous, clefs, actions)"),
    ("verser-cahier", 3,
     "python scripts/verser_cahier.py --vraiment",
     "les changements de registre rapportes par les hommes depeches"),
    ("bilan", 14,
     "python scripts/analyse/bilan.py",
     "la mesure d'ecart du plan, et l'empreinte des pieces"),
    ("criticite", 7,
     "python scripts/criticite.py",
     "le classement des pas par contrefactuel"),
]


def _lire():
    if not os.path.exists(FICHIER):
        return {"passages": {}}
    try:
        return json.load(io.open(FICHIER, encoding="utf-8"))
    except Exception:
        # Un registre de battements illisible ne doit jamais faire tomber le
        # producteur qui vient y battre : on repart d'une page blanche, et la
        # garde criera d'elle-même au prochain audit.
        return {"passages": {}}


def _ecrire(d):
    dossier = os.path.dirname(FICHIER)
    fd, tmp = tempfile.mkstemp(dir=dossier, suffix=".tmp")
    os.close(fd)
    with io.open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=1))
    os.replace(tmp, FICHIER)


def battre(qui, quoi=u""):
    """Poser le battement d'un producteur QUI VIENT D'ABOUTIR.

    Se met a la toute fin du chemin de succes, apres l'ecriture. Jamais dans un
    `finally`, jamais avant le travail : le silence doit rester le signal.
    """
    d = _lire()
    d.setdefault("_lisez_moi", (
        u"Le battement des producteurs derives — ecrit par scripts/noyau/rapporteurs.py, "
        u"lu par tick.py --verifier. Un producteur qui plante ne bat pas ; c'est "
        u"l'absence de battement qui fait l'anomalie. Ne pas ecrire a la main."))
    d.setdefault("passages", {})
    d["passages"][qui] = {"quand": time.time(), "quoi": quoi}
    _ecrire(d)


def etat(maintenant=None):
    """Ce que chaque rapporteur attendu doit a l'heure qu'il est.

    Rend une liste de dicts : `qui`, `jours` (cadence), `age` en jours reels ou
    None s'il n'a JAMAIS battu, `muet` (bool), `commande`, `quoi`, `dernier_quoi`.
    Ne juge pas, ne trie pas, n'ecrit rien — c'est l'appelant qui decide de la
    gravite, comme partout ailleurs ici.
    """
    if maintenant is None:
        maintenant = time.time()
    passages = _lire().get("passages") or {}
    out = []
    for qui, jours, commande, quoi in ATTENDUS:
        p = passages.get(qui) or {}
        quand = p.get("quand")
        age = None if not quand else (maintenant - quand) / 86400.0
        out.append({
            "qui": qui,
            "jours": jours,
            "age": age,
            "muet": age is None or age > jours,
            "commande": commande,
            "quoi": quoi,
            "dernier_quoi": p.get("quoi") or u"",
        })
    return out
