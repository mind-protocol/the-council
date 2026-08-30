# -*- coding: utf-8 -*-
"""SOCLE — les constantes de la boucle, le journal, les lectures de base
(json atomique, tissu).
"""
import datetime as dt
import io
import json
import os
import re
import sys
import threading
import time

from etat.expose import tables  # LA PORTE de etat/

# Trois etages de plus qu'a la racine : scripts/agents/activation/.
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
ETAT = os.path.join(RACINE, "etat")
TISSU = os.path.join(ETAT, "tissu")
DEPOT = os.path.join(ETAT, "activations")
ETAT_BOUCLE = os.path.join(DEPOT, "boucle.json")
VERROU = os.path.join(DEPOT, ".boucle.lock")
JOURNAL = os.path.join(DEPOT, "boucle.log.jsonl")
JUGER_PY = os.path.join(RACINE, "scripts", "juger.py")
DEBUT_PROCESSUS = time.monotonic()
PERSISTER_LOGS = False
AFFICHER_LOGS = True
VERROU_LOG = threading.Lock()

# La physique de la diffusion vit dans `scripts/noyau/diffusion.json` et
# s'importe : deux implementations de la meme formule ont derive sans que
# personne le voie, et la page de regie a tourne des semaines sur une liste de
# relais dont `personne` etait absent. Ne recopier ces valeurs nulle part.
from diffusion import AMORTISSEMENT, TOURS_DIFFUSION, GENRES_RELAIS  # noqa: E402,F401

ENERGIE_MAX = 100.0
ENERGIE_MIN = 1.0
# Plancher d'ACTIVATION : on n'elit personne a qui l'on ne donne pas de quoi
# agir. A 1 point (30 secondes de monde) un homme ne fait que marcher — Sara a
# depense sa journee entiere a traverser une salle sans atteindre la cour.
ENERGIE_ACTIVATION_MIN = 10.0
SECONDES_MONDE_PAR_ENERGIE = 30
DUREE_ACTIVATION_MIN_SECONDES = 60
DEMI_VIE_ENERGIE = 300.0
ECHECS_CONSECUTIFS_MAX = 5
REPOS_ACTEUR_SECONDES = 15 * 60
REPOS_PAIRE_SECONDES = 60 * 60
TRANSFERT_HORLOGE_MAX = 0.5
ETATS_TERMINES = (
    "fait", "faite", "fini", "termine", "abandonn", "annul", "sans objet",
)
TYPES_RESULTAT_ACTIVITE = {
    "observation", "progression_tache", "variation_mesure", "deplacement",
    "objet_produit", "communication", "fait", "blocage", "echec",
}


def secondes_monde_pour_energie(energie):
    """Convertit la jauge abstraite en vraie tranche de travail fictionnelle."""
    return max(1, int(round(float(energie) * SECONDES_MONDE_PAR_ENERGIE)))


def energie_pour_secondes(secondes):
    """Prix énergétique d'une durée physique, conservé avec assez de précision."""
    return round(float(secondes) / SECONDES_MONDE_PAR_ENERGIE, 3)


def journaliser(evenement, brut=None, **champs):
    """Flux immediat lisible, plus l'evenement complet en JSONL."""
    ecoule = round(time.monotonic() - DEBUT_PROCESSUS, 3)
    record = {
        "a": dt.datetime.now().astimezone().isoformat(),
        "t_s": ecoule,
        "evenement": evenement,
    }
    record.update(champs)
    if brut is not None:
        record["brut"] = brut
    details = " · ".join("%s=%s" % (k, v) for k, v in champs.items())
    # UN GARDE-FOU QUI A BESOIN D'ECRIRE POUR SIGNALER QU'IL NE PEUT PLUS
    # ECRIRE N'EST PAS UN GARDE-FOU. Le 10 aout, une boucle de 4 h 10 est morte
    # au tour 20 : `cycle.echoue` avait bien attrape l'OSError du disque plein,
    # puis journaliser() a voulu poser la ligne d'erreur sur le meme disque.
    # Journaliser ne doit donc JAMAIS lever, quelle que soit la panne d'E/S.
    if AFFICHER_LOGS:
        try:
            print("[%7.3fs] %-24s%s" %
                  (ecoule, evenement, " · " + details if details else ""),
                  flush=True)
        except OSError:
            pass
    if not PERSISTER_LOGS:
        return
    try:
        with VERROU_LOG:
            os.makedirs(DEPOT, exist_ok=True)
            with io.open(JOURNAL, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        # Disque plein, chemin disparu, quota : la boucle continue en aveugle
        # plutot que de s'eteindre. Le flux stdout reste la trace de secours.
        pass


def lire_json(chemin, defaut):
    """Une seule porte, une seule semantique — voir `scripts/tables.py`.

    Il y avait quatre `lire_json` dans ce depot et quatre comportements devant
    un fichier corrompu : deux plantaient, deux repartaient en silence sur le
    defaut. C'est tranche une fois pour toutes — un JSON abime PLANTE, seule
    l'absence rend le defaut.
    """
    return tables.lire(chemin, defaut)


def ecrire_atomique(chemin, valeur):
    """Une seule implementation, dans `scripts/tables.py`."""
    return tables.ecrire(chemin, valeur)


def charger_tissu():
    noeuds = lire_json(os.path.join(TISSU, "noeuds.json"), {})
    aretes = []
    with io.open(os.path.join(TISSU, "aretes.jsonl"), encoding="utf-8") as f:
        for ligne in f:
            if ligne.strip():
                aretes.append(json.loads(ligne))
    evaluation = lire_json(os.path.join(TISSU, "evaluation.json"), {})
    return noeuds, aretes, evaluation



def _court(x, n=180):
    texte = re.sub(r"\s+", " ", str(x or "")).strip()
    return texte if len(texte) <= n else texte[:n - 1] + "…"
