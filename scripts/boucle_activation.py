# -*- coding: utf-8 -*-
"""Boucle d'activation narrative pilotee par le graphe miroir.

Le script ne modifie jamais l'etat canonique. Il lit le tissu et les horloges,
calcule la meme diffusion d'importance que la regie, accumule une energie
technique (0..100), puis appelle ``depecher.py`` pour l'acteur qui porte le
maximum. Les mutations sont appliquees a `etat/` ; le rapport reste comme trace
dans ``etat/activations``, qui n'est PAS un purgatoire.

Temps de la diffusion :
  * origine : horloge du siege principal ;
  * present : horloge occupee la plus avancee ;
  * entre deux ecritures : une seconde reelle = une seconde du monde.

Usage :
    python scripts/boucle_activation.py --sec --une-fois
    python scripts/boucle_activation.py --une-fois
    python scripts/boucle_activation.py

``--sec`` ne lance aucun modele et n'ecrit aucun etat d'ordonnancement.
"""

import argparse
import collections
import concurrent.futures
import datetime as dt
import hashlib
import heapq
import io
import json
import math
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from agents.expose import depecher  # le script d'appel canonique
from etat.expose import tables  # LA PORTE de etat/ : une lecture, une ecriture, une semantique d'erreur
from etat.expose import appliquer  # vocabulaire ferme des mutations
from temps.expose import occupation  # qui est ASSIS — mesure, pas drapeau
from temps.expose import regence  # la ligne qu'un siege vacant ne franchit pas


RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

AMORTISSEMENT = 0.85
TOURS_DIFFUSION = 40
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
# `personne` EST UN RELAIS, et c'est la doctrine qui le dit : une nouvelle ne
# voyage jamais autrement que par des gens — un porteur, une bouche, un pli
# remis en main. Sans elle, la diffusion depuis le joueur n'atteignait que 67
# noeuds sur 1849 et pas un seul evenement : on pouvait ATTEINDRE un homme, on
# ne pouvait pas passer PAR lui, et tout lien d'homme a homme etait un
# cul-de-sac. Le delai reste paye sur l'arete (route.delai_jours, sinon la
# distance physique), donc passer par quelqu'un coute ce que coute le chemin.
GENRES_RELAIS = {
    "action", "clef", "transmission", "verrou", "moyen", "mesure",
    "compte", "evenement", "etape", "office", "lieu", "echelle",
    "etat_cible", "piece", "personne",
}
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


def minute_absolue(d):
    if not isinstance(d, dict) or d.get("annee") is None:
        return None
    return (((int(d["annee"]) * 12 + int(d["lune"]) - 1) * 30
             + int(d["jour"]) - 1) * 1440 + int(d.get("minute") or 0))


def horloge_directe(ancien, maintenant=None):
    """Rend le present de la vague en secondes depuis son origine PJ."""
    maintenant = time.time() if maintenant is None else maintenant
    horloges = lire_json(os.path.join(ETAT, "horloges.json"), {})
    sieges = lire_json(os.path.join(ETAT, "joueurs.json"), [])
    if isinstance(sieges, dict):
        sieges = sieges.get("joueurs") or sieges.get("sieges") or []
    # ON NE LIT PAS LE DRAPEAU, ON MESURE. `occupe` est un cache, et il a menti
    # pendant deux jours : quatre sieges a `true`, deux d'entre eux plus joues
    # par personne — donc exclus de cette file, donc endormis. Ici on demande
    # au disque qui respire (`scripts/occupation.py`), et l'on n'ecrit rien :
    # `prevoir_activations` doit pouvoir appeler cette fonction sans effet.
    releve = occupation.mesures()
    assis = {m["personnage_id"] for m in releve if m["occupe"]}
    # UN SIEGE VACANT SANS TETE N'EST PAS ACTIVABLE, ET C'EST UNE GARDE DURE.
    # La regle « vacant -> une tete » est un invariant de `tick.py --verifier`,
    # c'est-a-dire un constat apres coup. Mesuree, l'occupation peut basculer
    # toute seule pendant qu'on ne regarde pas — et si l'on ne s'en protegeait
    # pas ici, un siege dont personne n'a ecrit la tete se retrouverait elu et
    # joue par la machine sans qu'aucun texte ne dise ce qu'il veut. On le
    # laisse donc EXCLU, comme s'il etait encore assis, jusqu'a ce qu'on lui
    # ait ecrit sa tete.
    sans_tete = {m["personnage_id"] for m in releve
                 if not m["occupe"] and not m["a_tete"]}
    for pid in sorted(sans_tete):
        journaliser("sieges.vacant_sans_tete", acteur=pid,
                    note="exclu de la file tant qu'il n'a pas de tete")
    occupes = [s for s in sieges if s.get("personnage_id") in assis]
    # DEUX QUESTIONS DIFFERENTES, et il ne faut pas les confondre :
    #   — QUI EST EXCLU de la file d'activation ? Les assis, et eux seuls.
    #     C'est ce qu'on rend a la fin, et ca peut tres bien etre vide.
    #   — D'OU PART LE TEMPS ? Il faut une horloge d'origine et un front,
    #     sinon la vague n'a pas de present et la boucle s'arrete net.
    # Tant que `occupe` etait un drapeau jamais rebascule, la seconde question
    # avait toujours une reponse. Mesure, elle peut ne plus en avoir : deux
    # joueurs qui vont se coucher, et deux heures plus tard PLUS AUCUN siege
    # n'est assis. La boucle levait alors « front occupe absent » et le monde
    # cessait de tourner la nuit — un defaut tout neuf, cree par la reparation.
    # On retombe donc sur le roster entier pour l'HORLOGE seulement : le temps
    # continue de partir du siege principal, et les sieges vacants restent
    # activables puisqu'ils ne sont pas dans le jeu rendu.
    pour_horloge = occupes or [s for s in sieges if s.get("personnage_id")]
    principal = next((s for s in pour_horloge
                      if s.get("role") == "principal"),
                     pour_horloge[0] if pour_horloge else None)
    source_id = principal and principal.get("personnage_id")
    source_min = minute_absolue(horloges.get(source_id)) if source_id else None
    fronts = [(minute_absolue(horloges.get(s.get("personnage_id"))), s)
              for s in pour_horloge]
    fronts = [(m, s) for m, s in fronts if m is not None]
    if source_min is None or not fronts:
        raise RuntimeError("horloge du siege principal ou front occupe absent")
    front_min, front = max(fronts, key=lambda x: x[0])
    base = max(0.0, float(front_min - source_min) * 60.0)
    source_cle = "%s:%s" % (source_id, source_min)
    front_cle = "%s:%s" % (front.get("personnage_id"), front_min)
    h = (ancien or {}).get("horloge") or {}
    if h.get("source_cle") == source_cle and h.get("front_cle") == front_cle:
        ancre = float(h.get("ancre_mur") or maintenant)
        present = base + max(0.0, maintenant - ancre)
    else:
        ancre = maintenant
        present = base
    return {
        "source_id": source_id,
        "source_minute": source_min,
        "source_cle": source_cle,
        "front_id": front.get("personnage_id"),
        "front_minute": front_min,
        "front_cle": front_cle,
        "base_secondes": base,
        "ancre_mur": ancre,
        "present_secondes": present,
        "lu_a": maintenant,
    }, ({s.get("personnage_id") for s in occupes} | sans_tete)


def polarites_horloge_acteurs(noeuds, adj):
    """Emet si l'horloge locale est en avance, absorbe si elle est en retard.

    Un acteur herite d'abord de l'horloge du siege qui le declare dans ``pnj``.
    Les autres personnes heritent de l'ancre PJ la plus proche dans le graphe.
    La moyenne ne porte que sur les sieges occupes et disposant d'une horloge.
    """
    horloges = lire_json(os.path.join(ETAT, "horloges.json"), {})
    sieges = lire_json(os.path.join(ETAT, "joueurs.json"), [])
    if isinstance(sieges, dict):
        sieges = sieges.get("joueurs") or sieges.get("sieges") or []
    assis = occupation.occupes()
    actifs = []
    for siege in sieges:
        pid = siege.get("personnage_id")
        minute = minute_absolue(horloges.get(pid)) if pid else None
        if pid in assis and minute is not None:
            actifs.append((pid, float(minute), siege))
    if not actifs:
        return {}, {"moyenne_minute": None, "ecart_max_minutes": 0.0}

    moyenne = sum(x[1] for x in actifs) / len(actifs)
    ecart_max = max(abs(x[1] - moyenne) for x in actifs) or 1.0
    attribution = {}
    file = []
    for pid, minute, siege in actifs:
        ancres = [pid] + list(siege.get("pnj") or [])
        for acteur in ancres:
            nid = "pers:" + acteur
            candidat = (0, pid, minute)
            if nid in noeuds and (nid not in attribution or
                                  candidat < attribution[nid]):
                attribution[nid] = candidat
                heapq.heappush(file, (0, pid, minute, nid))

    lieux_bruts = lire_json(os.path.join(ETAT, "lieux.json"), [])
    if isinstance(lieux_bruts, dict):
        lieux_bruts = lieux_bruts.get("lieux") or []
    lieux = {x.get("id"): x for x in lieux_bruts
             if isinstance(x, dict) and x.get("id")}

    def distance_physique(lieu_a, lieu_b):
        if not lieu_a or not lieu_b:
            return None
        if lieu_a == lieu_b:
            return 0.0
        a, b = lieux.get(lieu_a) or {}, lieux.get(lieu_b) or {}
        da, db = a.get("jours_de_pr"), b.get("jours_de_pr")
        if not isinstance(da, (int, float)) or not isinstance(db, (int, float)):
            return None
        return abs(da - db) if da == 0 or db == 0 else da + db

    # Hors rattachement explicite, le lieu prime : un acteur de Port-Real vit
    # sur le front de Port-Real, meme si une affaire le relie fortement a la reine.
    for nid, n in noeuds.items():
        if n.get("genre") != "personne" or nid in attribution:
            continue
        candidats = []
        for pid, minute, siege in actifs:
            pj = noeuds.get("pers:" + pid) or {}
            distance = distance_physique(n.get("lieu_id"), pj.get("lieu_id"))
            if distance is not None:
                priorite = 0 if siege.get("role") == "principal" else 1
                candidats.append((distance, priorite, pid, minute))
        if candidats:
            _distance, _priorite, pid, minute = min(candidats)
            attribution[nid] = (0, pid, minute)
            heapq.heappush(file, (0, pid, minute, nid))
    while file:
        distance, pid, minute, ici = heapq.heappop(file)
        if attribution.get(ici) != (distance, pid, minute):
            continue
        for voisin in adj.get(ici) or []:
            candidat = (distance + 1, pid, minute)
            if voisin not in attribution or candidat < attribution[voisin]:
                attribution[voisin] = candidat
                heapq.heappush(file, (distance + 1, pid, minute, voisin))

    resultat = {}
    for nid, n in noeuds.items():
        if n.get("genre") != "personne" or nid not in attribution:
            continue
        distance, pid, minute = attribution[nid]
        ecart = minute - moyenne
        mode = "emet" if ecart > 0.001 else "absorbe" if ecart < -0.001 else "neutre"
        resultat[nid] = {
            "mode": mode,
            "intensite": min(1.0, abs(ecart) / ecart_max),
            "ecart_minutes": ecart,
            "horloge_pj": pid,
            "distance_ancre": distance,
        }
    comptes = collections.Counter(x["mode"] for x in resultat.values())
    journaliser("energie.polarites_horloge",
                moyenne_minute=round(moyenne, 3),
                ecart_max_minutes=round(ecart_max, 3),
                emetteurs=comptes.get("emet", 0),
                absorbeurs=comptes.get("absorbe", 0),
                neutres=comptes.get("neutre", 0))
    return resultat, {
        "moyenne_minute": moyenne,
        "ecart_max_minutes": ecart_max,
    }


def appliquer_polarites_horloge(cibles, polarites, adj):
    """Transfere l'energie cible sur les aretes, sans en creer ni en detruire."""
    propositions = []
    for nid, polarite in sorted(polarites.items()):
        mode = polarite["mode"]
        intensite = float(polarite["intensite"])
        voisins = sorted(v for v in (adj.get(nid) or []) if v in cibles)
        if mode == "neutre" or intensite <= 0 or not voisins:
            continue
        fraction = TRANSFERT_HORLOGE_MAX * intensite
        if mode == "emet":
            part = cibles.get(nid, 0.0) * fraction / len(voisins)
            propositions.extend((nid, voisin, part) for voisin in voisins)
        else:
            propositions.extend(
                (voisin, nid, cibles.get(voisin, 0.0) * fraction / len(voisins))
                for voisin in voisins)

    sorties = collections.defaultdict(float)
    entrees = collections.defaultdict(float)
    for source, cible, montant in propositions:
        sorties[source] += montant
        entrees[cible] += montant
    echelles_source = {
        nid: min(1.0, cibles.get(nid, 0.0) / total) if total > 0 else 1.0
        for nid, total in sorties.items()
    }
    echelles_cible = {
        nid: min(1.0, max(0.0, ENERGIE_MAX - cibles.get(nid, 0.0)) / total)
        if total > 0 else 1.0
        for nid, total in entrees.items()
    }
    variations = collections.defaultdict(float)
    transfere = 0.0
    for source, cible, montant in propositions:
        effectif = montant * min(echelles_source[source], echelles_cible[cible])
        variations[source] -= effectif
        variations[cible] += effectif
        transfere += effectif
    resultat = {
        nid: max(0.0, min(ENERGIE_MAX, valeur + variations.get(nid, 0.0)))
        for nid, valeur in cibles.items()
    }
    journaliser("energie.transfert_horloge", transfere=round(transfere, 3),
                propositions=len(propositions), acteurs=len(polarites))
    return resultat


def adjacence(noeuds, aretes):
    adj = {nid: [] for nid in noeuds}
    paires = set()
    for i, a in enumerate(aretes):
        de, vers = a.get("de"), a.get("vers")
        if a.get("flou") or a.get("virtuel") or de == vers:
            continue
        if de not in noeuds or vers not in noeuds:
            continue
        cle = tuple(sorted((de, vers)))
        if cle not in paires:
            paires.add(cle)
            adj[de].append(vers)
            adj[vers].append(de)
    return adj


def sources_de_charge(noeuds, aretes, evaluation):
    """Ancres et masses des motifs DECIDER utilises par la page admin."""
    entrants = collections.defaultdict(list)
    sortants = collections.defaultdict(list)
    for a in aretes:
        if a.get("de") in noeuds and a.get("vers") in noeuds:
            entrants[a["vers"]].append(a)
            sortants[a["de"]].append(a)
    motifs = []
    for g in evaluation.get("goulots") or []:
        if g.get("noeud") in noeuds:
            motifs.append((g["noeud"], g.get("demandes") or 1))
    for d in evaluation.get("desequilibres") or []:
        if d.get("noeud") in noeuds:
            motifs.append((d["noeud"], d.get("consommateurs") or 1))
    critique = (evaluation.get("critique") or [])[:1]
    if critique:
        chaine = critique[0].get("chaine") or []
        if chaine and chaine[0].get("id") in noeuds:
            motifs.append((chaine[0]["id"], len(chaine)))
    for nid in noeuds:
        contradictions = [a for a in entrants[nid] + sortants[nid]
                          if a.get("nature") == "contredit"]
        if len(contradictions) >= 2:
            motifs.append((nid, len(contradictions)))
    for nid, n in noeuds.items():
        if n.get("genre") != "action":
            continue
        tient = [a for a in sortants[nid] if a.get("nature") == "tient"]
        if (not tient or all(noeuds.get(a.get("vers"), {}).get("genre") == "vacant"
                            for a in tient)
                or all(a.get("flou") or a.get("vers") not in noeuds
                       for a in tient)):
            motifs.append((nid, 1))
    for nid in noeuds:
        sorties = [a for a in sortants[nid]
                   if a.get("nature") in ("ouvre", "realise")]
        if len(sorties) >= 3:
            motifs.append((nid, len(sorties)))
    charge = collections.defaultdict(float)
    for nid, score in motifs:
        charge[nid] += 1.0 + math.log1p(max(1, score))
    return charge


def diffuser(sources, adj, noeuds):
    total = sum(sources.values())
    if total <= 0:
        return {}
    src = {k: v / total for k, v in sources.items() if k in adj}
    x = dict(src)
    for _ in range(TOURS_DIFFUSION):
        y = collections.defaultdict(float)
        retenue = 0.0
        for nid, valeur in x.items():
            liens = adj.get(nid) or []
            genre = noeuds.get(nid, {}).get("genre")
            if not liens or (nid not in src and genre not in GENRES_RELAIS):
                retenue += valeur
                continue
            part = AMORTISSEMENT * valeur / len(liens)
            for autre in liens:
                y[autre] += part
        retour = AMORTISSEMENT * retenue + (1.0 - AMORTISSEMENT)
        for nid, valeur in src.items():
            y[nid] += retour * valeur
        x = dict(y)
    return x


def importance(noeuds, aretes, evaluation, source_id, occupes=()):
    adj = adjacence(noeuds, aretes)
    source = "pers:" + source_id
    atteinte = diffuser({source: 1.0}, adj, noeuds)
    charge = sources_de_charge(noeuds, aretes, evaluation)
    pression = diffuser(charge, adj, noeuds)
    max_a = max(atteinte.values() or [1e-12])
    max_p = max(pression.values() or [1e-12])
    scores = {}
    for nid in noeuds:
        a = atteinte.get(nid, 0.0) / max_a
        p = pression.get(nid, 0.0) / max_p
        scores[nid] = math.sqrt(a * p)
    # ON NE NORMALISE PAS SUR UN SIEGE OCCUPE. La source de la diffusion a une
    # atteinte de 1.0 par construction : le personnage joueur est donc TOUJOURS
    # le pic du graphe, il rafle les 100 points du plafond, et il ne peut rien
    # en depenser puisqu'il n'est jamais elu (voir `pid in occupes` plus bas).
    # Le meilleur acteur reel plafonnait ainsi a 28 sur une echelle de 100.
    # On cale donc l'echelle sur le plus fort noeud ACTIVABLE.
    exclus = {"pers:" + p for p in occupes if p}
    # Les sieges occupes gardent leur rang relatif mais ne debordent pas :
    # au-dela de 1.0 ils fausseraient les polarites et le plafond d'energie.
    return normaliser_par_cluster(scores, charge, noeuds, adj, exclus), adj


def energie_de_tache(tache, energies_graphe, energie_acteur):
    """Prix energetique d'une tache, y compris celle qu'on vient de creer.

    UNE TACHE CREEE N'EST PAS DANS LE TISSU. Son id (`activation:<pid>:<hash>`)
    n'a donc aucune entree dans `energies_graphe`, qui rendait 0.0 — soit moins
    que ENERGIE_MIN, soit un rejet systematique en `tache_sous_seuil`. La
    branche de secours de `choisir_tache`, ecrite exactement pour les acteurs
    trop peu modelises pour avoir une tache atteignable, etait donc morte : les
    seuls qui en dependaient ne pouvaient jamais etre elus. Une intention vaut
    son homme — c'est la sienne, elle ne peut pas peser moins que lui.
    """
    if tache.get("creee"):
        return float(energie_acteur)
    return float(energies_graphe.get(tache["id"], 0.0))


def clusters_par_lieu(noeuds, adj):
    """Rattache chaque noeud a un lieu, seme par les seules personnes.

    Les 107 noeuds `personne` portent tous un `lieu_id` ecrit a la main ; aucun
    des 1742 autres n'en a. On propage donc depuis eux, le plus proche gagnant,
    sur l'adjacence de la diffusion.

    UN NOEUD A EGALE DISTANCE DE DEUX LIEUX N'APPARTIENT A AUCUN. Departager
    par l'id, comme on le faisait, donne un resultat stable et faux : le noeud
    generique `unite:corbeau` s'est retrouve attribue a l'Ile-aux-Pinces, et
    les neuf lignes de cout qui le citent ont fait passer Celtigar pour la
    maison dont nos affaires dependent le plus. Une commune est une commune :
    on la laisse sans lieu plutot que de lui en inventer un.
    """
    # LE VOTE SE NORMALISE PAR LE NOMBRE DE GRAINES. Sans cela Peyredragon,
    # qui compte 58 personnes contre 2 a Lamarck, gagne toutes les egalites et
    # avale les noeuds de ses voisins : Lamarck tombait de 76 a 15. Le poids
    # d'un lieu ne doit pas dependre du nombre de gens qu'on y a ecrits.
    graines = collections.Counter(
        n["lieu_id"] for n in noeuds.values()
        if n.get("genre") == "personne" and n.get("lieu_id"))
    distances = {}
    lieux = collections.defaultdict(collections.Counter)
    file = []
    for nid, n in noeuds.items():
        if n.get("genre") == "personne" and n.get("lieu_id"):
            distances[nid] = 0
            lieux[nid][n["lieu_id"]] = 1.0 / graines[n["lieu_id"]]
            heapq.heappush(file, (0, nid))
    vus = set()
    while file:
        distance, ici = heapq.heappop(file)
        if ici in vus:
            continue
        vus.add(ici)
        for voisin in adj.get(ici) or []:
            candidat = distance + 1
            connue = distances.get(voisin)
            if connue is None or candidat < connue:
                distances[voisin] = candidat
                lieux[voisin] = collections.Counter(lieux[ici])
                heapq.heappush(file, (candidat, voisin))
            elif candidat == connue and voisin not in vus:
                lieux[voisin] += lieux[ici]
    # Le plus represente parmi les sources a egale distance l'emporte ; une
    # egalite franche laisse le noeud sans lieu. Le tout-ou-rien, lui, retirait
    # son lieu a un noeud sur cinq et vidait Lamarck de 76 a 15.
    resultat = {}
    for nid, compte in lieux.items():
        if not compte:
            continue
        ordonne = compte.most_common(2)
        if len(ordonne) > 1 and ordonne[0][1] == ordonne[1][1]:
            continue
        resultat[nid] = ordonne[0][0]
    return resultat


def normaliser_par_cluster(scores, charge, noeuds, adj, exclus):
    """Chaque lieu se mesure a son propre pic, amorti par ce qu'on y a ecrit.

    Une normalisation globale demandait « qui est le plus presse du monde »,
    et la reponse etait toujours chez nous : la pression sort des motifs
    DECIDER, qui n'existent que la ou le graphe est detaille. Peyredragon
    porte 1319 noeuds et 75 motifs ; Villevieille en porte 12 et zero. On
    demande donc desormais « qui est le plus presse CHEZ LUI ».

    L'amortissement en log(motifs) evite le bug symetrique : sans lui, une
    flaque a une seule affaire verrait sa tete normalisee a 1.0 et rivaliser
    avec le chateau du joueur. Un lieu ou rien n'est ecrit reste a zero, et
    c'est juste — il n'y a rien a y faire.
    """
    lieux = clusters_par_lieu(noeuds, adj)
    motifs = collections.Counter(lieux[nid] for nid in charge if nid in lieux)
    if not motifs:
        return scores
    motifs_max = max(motifs.values())
    reference = math.log1p(motifs_max)
    pics = collections.defaultdict(float)
    for nid, valeur in scores.items():
        lieu = lieux.get(nid)
        if lieu is not None and nid not in exclus:
            pics[lieu] = max(pics[lieu], valeur)
    resultat = {}
    for nid, valeur in scores.items():
        lieu = lieux.get(nid)
        pic = pics.get(lieu, 0.0)
        if lieu is None or pic <= 0:
            resultat[nid] = 0.0
            continue
        amorti = math.log1p(motifs.get(lieu, 0)) / reference if reference else 0.0
        resultat[nid] = min(1.0, (valeur / pic) * amorti)
    journaliser("importance.clusters", lieux=len(pics),
                motifs_max=motifs_max,
                actifs=sum(1 for v in resultat.values() if v > 0))
    return resultat


def calendrier(noeuds, aretes, evaluation, source_id):
    """Qui a le droit d'agir chez lui — et la reponse est : tout le monde.

    CETTE FONCTION RENDAIT UNE INTERDICTION D'AGIR, ET ELLE ETAIT INVERSEE.
    Elle datait la disponibilite d'un acteur a `min(jours_restants)` de ses
    etapes en cours, comparee au present de la vague (une seconde reelle = une
    seconde de monde). Or `jours_restants` dit COMBIEN DE TEMPS une affaire va
    courir, pas a quelle date l'homme se libere : un homme a qui l'on avait
    ecrit un vrai plan se trouvait interdit d'agir pendant toute la duree de ce
    plan, tandis qu'un homme sans plan — ou dont toutes les etapes sont des
    postures permanentes (`jours_restants: null`, jamais decomptees) — restait
    disponible en permanence. La physique recompensait donc exactement le
    defaut de modelisation.

    Mesure le 10 aout sur l'etat courant, present de vague a 1,7 jour : 32
    acteurs actifs sur 64 etaient geles, dont Criston (20 j), Aegon II (5 j),
    Larys (4 j), Daemon (3 j), Corlys (2 j) — 37 % de la masse d'importance du
    graphe, et zero activation. Les vingt-neuf activations d'Alys Grive et de
    Rulf Corne ne recompensaient pas leur importance : elles recompensaient le
    fait que personne ne leur avait ecrit d'horloge.

    Dix autres actifs n'entraient meme pas dans le classement, faute d'etre
    joignables par le relais de diffusion depuis le PJ. C'etait la meme faute
    d'un cran plus loin, et le commentaire de la version precedente la nommait
    deja pour le delai du courrier : la portee d'une NOUVELLE n'est jamais la
    faculte d'AGIR. Un homme agit chez lui, qu'on puisse lui ecrire ou non.

    Ce qui espace reellement les activations reste en place et suffit :
    `REPOS_ACTEUR_SECONDES` apres chaque tour, la rotation qui reserve les
    acteurs deja passes, `ENERGIE_ACTIVATION_MIN` qui ecarte ceux a qui le
    graphe ne donne pas de quoi agir, et la continuite de tache. Les etapes,
    elles, restent decomptees par `tick.py` — c'est son travail, pas celui-ci.
    """
    del aretes, evaluation, source_id  # ni la route ni la pression n'autorisent
    return {nid: 0.0 for nid, n in noeuds.items()
            if n.get("genre") == "personne"}

def tache_active(n):
    if n.get("genre") not in ("action", "etape"):
        return False
    etat = re.sub(r"[*_]+", "", str(n.get("etat") or "")).strip().lower()
    return not any(mot in etat for mot in ETATS_TERMINES)


def empreinte_tache(n):
    """Revision stable du noeud canonique, sans les champs runtime de la regie."""
    if not isinstance(n, dict):
        return None
    stable = {k: n.get(k) for k in (
        "id", "genre", "quoi", "etat", "source", "jours_restants",
        "depend_de", "realise", "office", "titulaire", "preuve") if k in n}
    brut = json.dumps(stable, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))
    return hashlib.sha1(brut.encode("utf-8")).hexdigest()


def continuite_tache(etat, nid, noeuds):
    """Retourne l'overlay seulement si le noeud canonique n'a pas change."""
    continuite = (etat.get("continuite") or {}).get(nid)
    if not isinstance(continuite, dict):
        return None
    if continuite.get("empreinte_canonique") != empreinte_tache(noeuds.get(nid)):
        return None
    return continuite


def repos_perime(present, reprendre_a, repos_max):
    """Un repos qui ne peut pas avoir ete pose dans le repere courant.

    LE BUG QUE CECI REPARE. `present_secondes` se compte depuis l'horloge du
    siege principal, et `reprendre_a` vaut `present + REPOS` au moment ou on
    l'estampe. Mais l'origine BOUGE : quand le siege principal rattrape le
    front — Rhaenyra passant du 129.3.30 au 129.4.2 —, l'ecart s'effondre et le
    present RECULE. Mesure du 129.4.3 : present tombe de ~151 700 a 5 154, et
    quatorze acteurs se sont retrouves en repos jusqu'a ~152 000, soit 41
    heures de monde dans le futur. Ils etaient geles pour toujours, l'origine
    ne faisant qu'avancer — Gerardys a 100 d'energie n'etait plus jamais elu,
    et la boucle tournait sur les sept memes tetes.

    Le repos legitime le plus long est `REPOS_PAIRE_SECONDES`. Au-dela de
    `present + repos_max`, la valeur ne peut pas venir de la regle appliquee
    dans ce repere-ci : c'est un reste d'un repere anterieur, et on le tient
    pour echu. On ne raccourcit aucun repos vrai — seulement ceux qu'aucune
    horloge d'aujourd'hui ne saurait produire.
    """
    try:
        reprendre_a = float(reprendre_a)
    except (TypeError, ValueError):
        return True
    return reprendre_a > float(present) + float(repos_max)


def tache_disponible(etat, nid, noeuds, present):
    continuite = continuite_tache(etat, nid, noeuds)
    if not continuite:
        return True
    if continuite.get("suspendue"):
        return False
    reprendre_a = continuite.get("reprendre_a") or 0.0
    if repos_perime(present, reprendre_a, REPOS_PAIRE_SECONDES):
        return True
    return float(present) >= float(reprendre_a)


def acteur_en_repos(etat, pid, present):
    dernier = ((etat.get("repos") or {}).get("acteurs") or {}).get(pid)
    if not isinstance(dernier, (int, float)):
        return False
    if repos_perime(present, dernier, REPOS_ACTEUR_SECONDES):
        return False
    return float(present) < float(dernier)


def choisir_tache(acteur, noeuds, aretes, adj, energies, etat=None,
                  present=0.0):
    """Tache active la plus proche de l'acteur.

    ``tient`` est l'assignation canonique d'une action. Une tache tenue par un
    autre personnage ne doit jamais etre recuperee par simple proximite dans le
    graphe. L'assignation definit l'ensemble eligible ; la distance decide,
    puis l'energie ne departage que deux taches a distance egale.
    """
    etat = etat or {}
    titulaires = collections.defaultdict(set)
    for a in aretes:
        # « tient » est l'assignation d'une action de plan ; « poursuit » est
        # l'etape que porte une TETE. Les deux sont des appartenances, et ne
        # compter que la premiere ouvrait une fuite entre les camps : une etape
        # d'intentions.json n'a pas d'arete « tient », donc `titulaires` restait
        # vide pour elle, donc n'importe qui pouvait la ramasser au repli par
        # distance. Mesure du 129.4.3 : le mestre GERARDYS, qui sert la reine,
        # se voyait attribuer `etape:otto-recit-du-feu` — « faire ecrire par
        # Orwyle le recit officiel du massacre », l'etape d'OTTO HIGHTOWER — et
        # ser Robert Quince `etape:larys-mysaria`. Le conseil de Peyredragon
        # s'appretait a executer le plan d'en face.
        if a.get("flou") or a.get("nature") not in ("tient", "poursuit"):
            continue
        de, vers = a.get("de"), a.get("vers")
        if de in noeuds and vers in noeuds:
            if tache_active(noeuds[de]) and noeuds[vers].get("genre") == "personne":
                titulaires[de].add(vers)
            elif tache_active(noeuds[vers]) and noeuds[de].get("genre") == "personne":
                titulaires[vers].add(de)

    def appartient_ou_vacante(nid):
        return not titulaires.get(nid) or acteur in titulaires[nid]

    directes = []
    for a in aretes:
        if a.get("flou") or a.get("de") not in noeuds or a.get("vers") not in noeuds:
            continue
        autre = None
        if a.get("de") == acteur and a.get("nature") in ("poursuit", "tient"):
            autre = a.get("vers")
        elif a.get("vers") == acteur and a.get("nature") in ("poursuit", "tient"):
            autre = a.get("de")
        if autre and tache_active(noeuds[autre]) and appartient_ou_vacante(autre) \
                and tache_disponible(etat, autre, noeuds, present) \
                and float(energies.get(autre, 0.0)) >= ENERGIE_MIN:
            # L'assignation explicite passe avant le simple fait que l'acteur
            # poursuit une etape de son intention.
            directes.append((0 if a.get("nature") == "tient" else 1, autre))
    if directes:
        directes.sort(key=lambda x: (x[0], -float(energies.get(x[1], 0.0)), x[1]))
        _priorite_affectation, nid = directes[0]
        return {"id": nid, "quoi": noeuds[nid].get("quoi") or nid,
                "genre": noeuds[nid].get("genre"), "distance": 1,
                "chemin": [acteur, nid], "creee": False}

    file = collections.deque([(acteur, [acteur])])
    vus = {acteur}
    candidats = []
    while file:
        ici, chemin = file.popleft()
        d = len(chemin) - 1
        if (ici != acteur and tache_active(noeuds[ici])
                and appartient_ou_vacante(ici)
                and tache_disponible(etat, ici, noeuds, present)
                and float(energies.get(ici, 0.0)) >= ENERGIE_MIN):
            candidats.append((d, -float(energies.get(ici, 0.0)), ici, chemin))
            continue
        # Une autre personne est une frontiere : ses propres taches ne sont
        # pas le prolongement implicite de celles de l'acteur active.
        if ici != acteur and noeuds[ici].get("genre") == "personne":
            continue
        for autre in adj.get(ici) or []:
            if autre not in vus:
                vus.add(autre)
                file.append((autre, chemin + [autre]))
    if candidats:
        _distance, _energie, nid, chemin = sorted(candidats)[0]
        return {"id": nid, "quoi": noeuds[nid].get("quoi") or nid,
                "genre": noeuds[nid].get("genre"), "distance": len(chemin) - 1,
                "chemin": chemin, "creee": False}

    pid = acteur.removeprefix("pers:")
    intentions = lire_json(os.path.join(ETAT, "intentions.json"), [])
    tete = next((t for t in intentions if t.get("personnage_id") == pid), {})
    quoi = (tete.get("intention") or
            next((o.get("but") for o in (noeuds[acteur].get("objectifs") or [])
                  if isinstance(o, dict) and o.get("but")), None))
    if not quoi:
        return None
    ident = hashlib.sha1((pid + "\0" + quoi).encode("utf-8")).hexdigest()[:12]
    return {"id": "activation:" + pid + ":" + ident, "quoi": quoi,
            "genre": "tache-proposee", "distance": 0,
            "chemin": [acteur], "creee": True,
            "source": "intentions.json:intention"}


def mettre_a_jour_energie_graphe(etat, horloge, scores, noeuds, adj,
                                 polarites):
    """Integre et persiste l'energie de chaque node du graphe.

    ``scores`` est la force instantanee produite par la topologie. L'energie,
    elle, vit dans l'overlay runtime et converge vers cette force avec une
    demi-vie de cinq minutes. Un score disparu fait decroitre la reserve ; aucun
    cycle ne la remet a zero.
    """
    graphe = etat.setdefault("graphe", {"noeuds": {}, "liens": {}})
    reserves = graphe.setdefault("noeuds", {})
    present = float(horloge["present_secondes"])
    precedent = graphe.get("mis_a_jour_a")
    dt_s = max(0.0, present - float(precedent)) if precedent is not None else 0.0
    alpha = 1.0 - math.exp(-math.log(2.0) * dt_s / DEMI_VIE_ENERGIE)
    acteurs_legacy = etat.get("acteurs") or {}
    cibles = {
        nid: ENERGIE_MAX * max(0.0, min(1.0, float(scores.get(nid, 0.0))))
        for nid in noeuds
    }
    cibles = appliquer_polarites_horloge(cibles, polarites, adj)
    resultat = {}
    for nid in noeuds:
        cible = cibles[nid]
        if nid in reserves:
            avant = float(reserves[nid])
            energie = avant + alpha * (cible - avant)
        else:
            pid = nid.removeprefix("pers:") if nid.startswith("pers:") else None
            legacy = acteurs_legacy.get(pid, {}).get("energie") if pid else None
            energie = float(legacy) if isinstance(legacy, (int, float)) else cible
        energie = max(0.0, min(ENERGIE_MAX, energie))
        reserves[nid] = energie
        resultat[nid] = energie
    for nid in list(reserves):
        if nid not in noeuds:
            del reserves[nid]
    graphe["mis_a_jour_a"] = present
    graphe["demi_vie_secondes"] = DEMI_VIE_ENERGIE
    if resultat:
        pic_id, pic = max(resultat.items(), key=lambda x: (x[1], x[0]))
        journaliser("energie.graphe", dt_s=round(dt_s, 3),
                    integration=round(alpha, 6), noeuds=len(resultat),
                    energises=sum(1 for x in resultat.values() if x >= ENERGIE_MIN),
                    total=round(sum(resultat.values()), 3),
                    pic=pic_id, maximum=round(pic, 3))
    return resultat


def mettre_a_jour_energies(etat, horloge, scores, energies_graphe,
                           disponibilites, noeuds, occupes):
    acteurs = etat.setdefault("acteurs", {})
    present = horloge["present_secondes"]
    nouvelle_vague = etat.get("source_cle") != horloge["source_cle"]
    if nouvelle_vague:
        etat["source_cle"] = horloge["source_cle"]
    eligibles = []
    # UN ECART SILENCIEUX N'EST PAS UN ECART, C'EST UNE DISPARITION. Le verrou
    # de disponibilite a tenu 32 acteurs sur 64 hors du classement sans ecrire
    # une ligne : rien dans le journal ne disait que Criston etait gele, et la
    # regie a lu « le monde tourne par le bas » la ou il fallait lire « la
    # moitie du casting n'est pas presentee ». On compte desormais les ecartes.
    ecartes = collections.Counter()
    for nid, disponible in disponibilites.items():
        n = noeuds.get(nid) or {}
        pid = nid.removeprefix("pers:")
        if pid in occupes:
            continue
        if n.get("etat") != "actif":
            ecartes["dormant"] += 1
            continue
        if n.get("condition") in ("prisonnier", "otage"):
            ecartes["captif"] += 1
            continue
        score = max(0.0, min(1.0, scores.get(nid, 0.0)))
        a = acteurs.setdefault(pid, {"energie": 0.0, "activations": 0})
        # Projection de compatibilite pour l'admin. L'autorite est desormais
        # l'overlay ``graphe.noeuds``, pas cette fiche d'acteur.
        a["energie"] = float(energies_graphe.get(nid, 0.0))
        a["mis_a_jour_a"] = present
        a["importance"] = score
        a["disponible_a"] = disponible
        if present >= disponible:
            eligibles.append((a["energie"], score, pid, a))
        else:
            ecartes["pas_encore_disponible"] += 1
    eligibles.sort(key=lambda x: (-x[0], -x[1], x[2]))
    journaliser("energie.classement", classes=len(eligibles),
                personnes=len(disponibilites), **dict(ecartes))
    return eligibles


def intitule_tache_activation(tache, dossier):
    etape = ((dossier.get("intention") or {}).get("etape_elue") or {})
    return etape.get("quoi") or tache.get("quoi") or "l'affaire devant toi"


def mission_activation(pid, tache, budget, horloge, noeuds, dossier):
    del pid, horloge, noeuds  # la machine ne parle plus dans la mission
    date = dossier.get("date_du_monde") or {}
    p = dossier.get("personnage") or {}
    lieu = p.get("lieu") or p.get("lieu_id") or "lieu inconnu"
    affaire = intitule_tache_activation(tache, dossier)
    return """%(annee)s AC · %(lune)se lune · %(jour)se jour — %(lieu)s

Tu as %(secondes)d secondes devant toi.

Tu as l'intention de t'occuper de :
%(affaire)s

Agis maintenant. Ne fais pas un plan de ce que tu pourrais faire : commence
par le premier geste réel que cette affaire appelle, avec les personnes, les
objets, les lieux et les registres que tu connais. Poursuis geste après geste
tant qu'il te reste du temps. Pour chacun, dis combien de secondes il prend et
ce qu'il produit réellement. Si quelque chose résiste, travaille sur ce qui
résiste ou constate précisément ce qui t'arrête. Arrête-toi quand le temps est
écoulé.
""" % {
        "annee": date.get("annee") or "?",
        "lune": date.get("lune") or "?",
        "jour": date.get("jour") or "?",
        "lieu": lieu,
        "secondes": secondes_monde_pour_energie(budget),
        "affaire": affaire,
    }


def contexte_narrateur_activation(pid, tache, budget_energie,
                                  budget_secondes, horloge, dossier):
    """La verite locale donnee a l'arbitre, jamais a l'acteur."""
    return {
        "date_du_monde": dossier.get("date_du_monde"),
        "present_secondes": round(float(horloge["present_secondes"]), 3),
        "budget_energie": budget_energie,
        "secondes_par_point_energie": SECONDES_MONDE_PAR_ENERGIE,
        "budget_secondes": int(budget_secondes),
        "duree_minimale_secondes": min(
            DUREE_ACTIVATION_MIN_SECONDES, int(budget_secondes)),
        "acteur_candidat": pid,
        "tache_elue": {
            "id": tache.get("id"),
            "quoi": intitule_tache_activation(tache, dossier),
            "creee": bool(tache.get("creee")),
        },
        "chemin_election": dossier.get("chemin") or [],
        "salle_actuelle": dossier.get("salle_actuelle") or {},
        "dossier_acteur": dossier,
        "topologie_des_salles": lire_json(os.path.join(ETAT, "chemins.json"), {}),
    }


def mission_ouverture_narrateur(pid, tache, budget_energie,
                                budget_secondes, contexte_narrateur):
    dossier = contexte_narrateur.get("dossier_acteur") or {}
    salle = dossier.get("salle_actuelle") or {}
    return """PHASE 1 — APPELER L'ACTEUR

Voici le dossier fermé de cette activation :

%(dossier_ferme)s

Ouvre le battement local dans %(salle)s.

La physique a élu %(acteur)s pour l'affaire suivante :
%(tache)s

TU LE SUIS PENDANT QU'IL TRAVAILLE, ET TU LE GUIDES. Un fil reste ouvert entre
sa session et la tienne : sers-t'en dès qu'il part de travers, cherche une
chose qui est dans ton dossier, ou s'engage vers un mur que tu vois et pas lui.
On ne le laisse pas se cogner pour le plaisir de l'arbitrer après.

    python scripts/parloir.py --dire --de mj --a %(acteur)s "<le fait qui lui manque, en une phrase>"
    python scripts/parloir.py --ecouter --qui mj

TU RECOMMANDES ET TU DÉPANNES — TU N'ORDONNES PAS. Il décide de sa journée ;
toi, tu lui évites de la perdre.

Recommander, c'est lui ouvrir une porte qu'il ne voyait pas, et le laisser
choisir d'y entrer : « le maître de port tient un rôle des passages, tu y
trouverais tes dates » · « il y a deux Torgo dans cette rade, l'aîné au môle
et le jeune au banc de calfat — vérifie duquel on t'a parlé » · « ce compte
existe déjà quelque part, ça t'éviterait de le refaire ».

Dépanner, c'est le déblocage technique, et là tu es net : l'adresse exacte
d'une chose, l'id sous lequel elle existe, le registre où elle est écrite, le
format qu'attend ce qu'il essaie de produire, le nom réel de ce qu'il a mal
nommé. Ce sont des faits de mécanique, pas des choix de fiction : donne-les
sans détour et sans énigme.

Ce qui reste à lui, entier : ce qu'il décide de faire, où il va, sa manière,
ses gestes et son rapport. S'il écarte ta recommandation, c'est sa journée et
c'est bien. Parle-lui autant qu'il en a besoin.

Il engage %(energie)d points d'énergie, soit une fenêtre physique de
%(secondes)d secondes (%(minutes)d minutes). Son activation doit couvrir un
vrai morceau de travail d'au moins %(minimum)d secondes, quitte à condenser
les continuités par une ellipse. Réveille-le maintenant. Ne résous rien encore
et rends seulement cet objet, sans phrase autour :

{
  "appel_pnj": {
    "qui": "%(acteur)s",
    "message": "adresse directe, diégétique et brève demandant ce qu'il tente maintenant"
  }
}
""" % {
        "dossier_ferme": json.dumps(
            contexte_narrateur, ensure_ascii=False, indent=2),
        "salle": salle.get("nom") or "la salle inconnue",
        "acteur": pid,
        "tache": intitule_tache_activation(tache, dossier),
        "energie": budget_energie,
        "secondes": budget_secondes,
        "minutes": round(budget_secondes / 60),
        "minimum": min(DUREE_ACTIVATION_MIN_SECONDES, budget_secondes),
    }


def mission_veille_narrateur(pid, tache, appel):
    """Ce que le narrateur fait pendant que son homme travaille : le suivre."""
    return """PHASE 1bis — VEILLER SUR TON HOMME PENDANT QU'IL TRAVAILLE

Tu viens de réveiller %(acteur)s sur : %(tache)s
Il est en train de vivre sa journée EN CE MOMENT, dans sa propre session.

Ton seul travail maintenant, pendant environ deux minutes : rester là et le
dépanner. Tu ne rédiges rien, tu n'arbitres rien, tu ne rends aucun rapport.

Fais ceci, en boucle, jusqu'à ce que tu aies tenu deux minutes :

    python scripts/parloir.py --ecouter --qui mj
    sleep 15

S'il dit quelque chose, s'il bute, s'il cherche une chose que tu as dans ton
dossier, réponds-lui :

    python scripts/parloir.py --dire --de mj --a %(acteur)s "<ta recommandation ou ton dépannage>"

TU RECOMMANDES ET TU DÉPANNES, TU N'ORDONNES PAS. Une porte qu'il ne voyait
pas et qu'il reste libre de ne pas prendre ; ou le fait technique net —
l'adresse exacte, l'id sous lequel une chose existe, le registre où elle est
écrite, le nom réel de ce qu'il a mal nommé. Parle-lui autant qu'il en a
besoin : un homme qu'on aide bien vaut mieux qu'un quota respecté.

Le silence est normal et ne coûte rien : la plupart du temps il travaille très
bien seul, et tu n'as rien à dire. Au bout de deux minutes, réponds simplement
`{"veille": "finie"}` et arrête-toi.
""" % {"acteur": pid, "tache": tache.get("quoi") or tache.get("id")}


def mission_resolution_narrateur(pid, tache, budget_energie,
                                 budget_secondes, horloge, tentative,
                                 contexte_narrateur):
    return """PHASE 2 — ARBITRER LA TENTATIVE

Voici la réponse exacte de l'acteur que tu as réveillé :

%(tentative)s

TON PREMIER TRAVAIL EST DE LE FAIRE RÉUSSIR, PAS DE LE JUGER. Il ne voit que
ce qu'il a sous les yeux ; toi, tu as le dossier entier. S'il cherche une
adresse, un nom, un chiffre, une porte, une personne qui est dans ton dossier
et pas dans sa tête — DONNE-LE-LUI et continue la scène. S'il s'y prend mal
mais que son intention est claire, fais aboutir l'intention. S'il vise une
chose qui n'existe pas sous ce nom mais qui existe sous un autre, corrige en
silence et poursuis.

Un échec ne se prononce QUE sur un obstacle réel de la fiction — quelqu'un qui
refuse, une porte fermée à clef, une marée, un homme absent, le temps qui
manque. Jamais parce qu'il ignorait quelque chose que tu savais, jamais sur
une maladresse de formulation, jamais parce qu'il a mal nommé une chose. Un
homme qu'on laisse échouer sur son ignorance a perdu sa journée, et nous avec.

Rends compte de l'aide que tu lui as donnée dans un champ `aide` du rapport :
[{"quoi": "ce qu'il lui manquait", "donne": "ce que tu lui as fourni"}].
S'il n'a eu besoin de rien, mets une liste vide.

Arbitre maintenant cette tentative depuis la vérité locale de ton dossier.
Le battement commence à %(debut)s secondes et peut durer jusqu'à %(budget)d
secondes (%(minutes)d minutes), payées par %(energie)d points d'énergie. Il doit
en produire au moins %(minimum)d : ne tronque pas l'activation au premier geste.
Poursuis la tentative jusqu'à un résultat, une résistance réellement établie ou
la borne, en condensant les continuités par les ellipses imposées par ton
système. Rends seulement le rapport final JSON. L'acteur et la tâche restent
`%(acteur)s` et `%(tache)s`.

%(contrat)s
""" % {
        "tentative": json.dumps(tentative, ensure_ascii=False, indent=2),
        "debut": round(float(horloge["present_secondes"]), 3),
        "budget": budget_secondes,
        "minutes": round(budget_secondes / 60),
        "energie": budget_energie,
        "minimum": min(DUREE_ACTIVATION_MIN_SECONDES, budget_secondes),
        "acteur": pid, "tache": tache.get("id"),
        "contrat": depecher.contrat_rapport_narrateur(contexte_narrateur),
    }


def mission_correction_narrateur(erreur, budget_secondes, horloge):
    return """Ton rapport vient d'être refusé par le validateur mécanique :

%(erreur)s

Débrouille-toi et corrige TON JSON. Ne réveille pas le PNJ une seconde fois,
ne change ni sa tentative ni les faits arbitrés. Rends seulement un rapport
final complet et valide. Rappels : axe continu depuis %(debut)s, entre
%(minimum)d et %(budget)d secondes ; chaque résultat cite une source touchée,
mobilisée, visée par l'action, traversée par le chemin ou produite plus tôt ;
chaque mutation cite un résultat du rapport et appartient au vocabulaire fermé
d'`appliquer.py`. Aucun `candidate:` ni adresse absente du dossier. Toute
avancée, fin, blocage ou échec vise l'id exact de la tâche. Le temps reste
physique : l'ellipse ne permet ni page écrite ni longue tirade en quelques
secondes. Si une continuité de reprise existe, reprends exactement son dernier
`apres` dans le nouvel `avant`.
""" % {
        "erreur": str(erreur),
        "debut": round(float(horloge["present_secondes"]), 3),
        "minimum": min(DUREE_ACTIVATION_MIN_SECONDES, budget_secondes),
        "budget": budget_secondes,
    }


def extraire_appel_pnj(reponse, pid):
    brut, note = depecher.extraire_json(reponse.get("result", ""))
    if brut is None:
        raise RuntimeError("appel du narrateur illisible : %s" % note)
    appel = brut.get("appel_pnj") or {}
    if appel.get("qui") != pid:
        raise RuntimeError("le narrateur a reveille %s au lieu de %s" %
                           (appel.get("qui"), pid))
    message = appel.get("message")
    if not isinstance(message, str) or not message.strip():
        raise RuntimeError("le narrateur n'a pas formule l'appel du PNJ")
    return {"qui": pid, "message": message.strip()}


def extraire_tentative(reponse):
    brut, note = depecher.extraire_json(reponse.get("result", ""))
    if brut is None:
        raise RuntimeError("tentative de l'acteur illisible : %s" % note)
    tentative = brut.get("tentative") or {}
    if not isinstance(tentative, dict):
        raise RuntimeError("la tentative de l'acteur doit former un objet")
    if not str(tentative.get("verbe") or "").strip() \
            or not str(tentative.get("quoi") or "").strip():
        raise RuntimeError("la tentative doit nommer son verbe et son geste")
    interdits = set(tentative) & {"resultat", "resultats", "duree_s",
                                  "duree_secondes", "reussite", "issue"}
    if interdits:
        raise RuntimeError("l'acteur a arbitré le monde dans sa tentative : %s" %
                           ", ".join(sorted(interdits)))
    return tentative


def extraire_relance_acteur(reponse):
    """Reconnaît la sortie imposée au narrateur par son hook Stop."""
    brut, _ = depecher.extraire_json(reponse.get("result", ""))
    if not isinstance(brut, dict) or not brut.get("relance_acteur"):
        return None
    relance = brut["relance_acteur"]
    if not isinstance(relance, dict):
        raise RuntimeError("relance_acteur du narrateur illisible")
    message = str(relance.get("message") or "").strip()
    if not message:
        manques = relance.get("manques") or []
        message = "Reprends ton travail sur ces points : " + "; ".join(
            str(x) for x in manques if str(x).strip())
    if not message.strip():
        raise RuntimeError("le narrateur demande une relance sans consigne")
    return {"message": message, "manques": relance.get("manques") or []}


def mission_relance_acteur(tache, relance):
    return """On te donne un coup de main sur cette tâche :

%(tache)s

Ce n'est pas un reproche et tu n'as rien raté. Voici ce qu'on peut te dire de
plus, que tu ne pouvais pas savoir d'où tu es :

%(message)s

Reprends la même tâche avec ça en main, et fais le geste suivant. Rends
seulement l'objet `tentative` prévu par ton système.
""" % {"tache": tache.get("quoi") or tache.get("id"),
       "message": relance["message"]}


def references_du_monde():
    """Tout ce qui EXISTE VRAIMENT, et qu'un homme a donc le droit de nommer.

    Le dossier est ce qu'on lui a mis en main ; ce n'est pas la liste de ce qui
    existe. Refuser le rapport d'Alicent parce qu'elle a nommé `pers:larys`, ou
    celui d'Aldon Hask parce qu'il a nommé `corlys`, c'est jeter une journée
    entière au motif que le monde est plus grand que la chemise qu'on lui a
    donnée. Larys existe. Corlys existe. Un homme qui les nomme a raison.

    On accepte donc toute adresse qui résout contre l'état réel — gens, lieux,
    maisons, mains, livres, pensees, salles. Ce qui reste refusé, c'est ce qui
    ne désigne rien nulle part, et c'est une vraie faute.
    """
    refs = set()

    def poser(prefixes, ident):
        if not ident:
            return
        ident = str(ident)
        refs.add(ident)
        for p in prefixes:
            refs.add(p + ident)

    def entrees(nom, cle=None):
        brut = lire_json(os.path.join(ETAT, nom + ".json"), [])
        if isinstance(brut, dict):
            brut = brut.get(cle or nom) or []
        return [x for x in brut if isinstance(x, dict)]

    for x in entrees("personnages"):
        poser(("pers:", "ref:pers:"), x.get("id"))
    for x in entrees("lieux"):
        poser(("salle:", "lieu:", "ref:salle:"), x.get("id"))
        for alias in x.get("alias") or []:
            poser(("salle:", "lieu:"), alias)
    for x in entrees("maisons"):
        poser(("maison:",), x.get("id"))
    for x in entrees("mains"):
        poser(("main:", "ref:main:"), x.get("id"))
    for x in entrees("books", "books"):
        poser(("livre:", "book:", "ref:livre:"), x.get("id"))
    for x in entrees("plis", "plis"):
        poser(("pli:",), x.get("id"))
    topologie = lire_json(os.path.join(ETAT, "chemins.json"), {})
    for arete in topologie.get("aretes") or []:
        if isinstance(arete, list):
            for lieu_id in arete[:2]:
                poser(("salle:",), lieu_id)
    for alias, lieu_id in (topologie.get("alias") or {}).items():
        poser(("salle:",), alias)
        poser(("salle:",), lieu_id)
    return refs


def references_du_dossier(dossier):
    """Valeurs adressables que le dossier fermé rend déjà connaissables.

    Le dossier NE BORNE PAS ce qui est nommable : on y ajoute tout ce qui
    existe dans l'état (voir `references_du_monde`). Un homme peut nommer un
    homme, un lieu, un livre ou une main qui n'était pas dans sa chemise.
    """
    refs = set(references_du_monde())

    def visiter(valeur):
        if isinstance(valeur, dict):
            for v in valeur.values():
                visiter(v)
        elif isinstance(valeur, list):
            for v in valeur:
                visiter(v)
        elif isinstance(valeur, (str, int, float)) and not isinstance(valeur, bool):
            texte = str(valeur)
            if texte:
                refs.add(texte)

    visiter(dossier)
    personnage = dossier.get("personnage") or {}
    if personnage.get("id"):
        refs.add("pers:" + str(personnage["id"]))
    salle = dossier.get("salle_actuelle") or {}
    if salle.get("id"):
        refs.add("salle:" + str(salle["id"]))
    for personne in salle.get("personnes") or []:
        if isinstance(personne, dict) and personne.get("id"):
            refs.add("pers:" + str(personne["id"]))
    for main in dossier.get("mains_portees") or []:
        if isinstance(main, dict) and main.get("id"):
            mid = str(main["id"])
            refs.update((mid, "main:" + mid))
    for volume in dossier.get("livres_accessibles") or []:
        if isinstance(volume, dict) and volume.get("id"):
            lid = str(volume["id"])
            refs.update((lid, "livre:" + lid, "book:" + lid))
    tache = dossier.get("tache") or {}
    if tache.get("id"):
        tid = str(tache["id"])
        refs.update((tid, "tache:" + tid))
    # Le narrateur reçoit toujours la topologie des salles dans son contexte.
    # Ses extrémités sont donc des adresses réelles, même si elles ne sont pas
    # la salle de départ de l'acteur.
    topologie = lire_json(os.path.join(ETAT, "chemins.json"), {})
    for arete in topologie.get("aretes") or []:
        if not isinstance(arete, list) or len(arete) < 2:
            continue
        for lieu_id in arete[:2]:
            if lieu_id:
                refs.update((str(lieu_id), "salle:" + str(lieu_id)))
    for alias, lieu_id in (topologie.get("alias") or {}).items():
        refs.update((str(alias), str(lieu_id), "salle:" + str(lieu_id)))
    return refs


def dossier_activation(pid, tache, horloge, noeuds, etat=None):
    """La tranche d'etat necessaire : identite, tete, mains et travail."""
    personnages = lire_json(os.path.join(ETAT, "personnages.json"), [])
    if isinstance(personnages, dict):
        personnages = personnages.get("personnages") or []
    noms_personnes = {p.get("id"): p.get("nom") or p.get("id")
                      for p in personnages if isinstance(p, dict) and p.get("id")}
    lieux = lire_json(os.path.join(ETAT, "lieux.json"), [])
    if isinstance(lieux, dict):
        lieux = lieux.get("lieux") or []
    noms_lieux = {l.get("id"): l.get("nom") or l.get("id")
                  for l in lieux if isinstance(l, dict) and l.get("id")}
    intentions = lire_json(os.path.join(ETAT, "intentions.json"), [])
    if isinstance(intentions, dict):
        intentions = intentions.get("intentions") or []
    mains = lire_json(os.path.join(ETAT, "mains.json"), [])
    if isinstance(mains, dict):
        mains = mains.get("mains") or []
    presence = lire_json(os.path.join(ETAT, "presence.json"), {})
    if not isinstance(presence, dict):
        presence = {}
    resolus = ((presence.get("resolu") or {}).get("gens") or {})
    position = resolus.get(pid) or {}
    salle_id = position.get("salle")
    salle_nom = position.get("lieu")
    if salle_id and not salle_nom:
        # Un trajet ou une ancienne exception peut ne porter que l'id. Une
        # autre personne résolue dans la même pièce en donne alors le nom.
        salle_nom = next((ou.get("lieu") for ou in resolus.values()
                          if ou.get("salle") == salle_id and ou.get("lieu")), None)
    if salle_id and not salle_nom:
        salle_nom = salle_id.replace("-", " ").capitalize()
    personnes_dans_salle = []
    if salle_id:
        for present_id, ou in resolus.items():
            if ou.get("salle") != salle_id:
                continue
            personnes_dans_salle.append({
                "id": present_id,
                "nom": noms_personnes.get(present_id, present_id),
            })
        personnes_dans_salle.sort(key=lambda x: (x["nom"].casefold(), x["id"]))
    personnage = next((p for p in personnages if p.get("id") == pid), None)
    if personnage:
        personnage = {k: personnage.get(k) for k in
                       ("id", "nom", "titre", "naissance", "traits",
                        "objectifs", "maniere", "portrait", "etat",
                        "condition", "lieu_id") if k in personnage}
        personnage["lieu"] = noms_lieux.get(personnage.get("lieu_id"),
                                             personnage.get("lieu_id"))
    intention = next((t for t in intentions
                      if t.get("personnage_id") == pid), None)
    if intention:
        etape_id = tache.get("id", "").removeprefix("etape:")
        plan = [p for p in intention.get("plan") or []
                if p.get("id") == etape_id]
        intention = {k: intention.get(k) for k in
                     ("personnage_id", "croyances", "ignore", "intention",
                      "declencheurs", "attitude_joueur", "mandat", "date_maj")
                     if k in intention}
        intention["etape_elue"] = plan[0] if plan else None
    # La mémoire écrite de l'homme — son dernier rapport et sa dernière
    # conclusion. L'ancien `travaux = []` était codé en dur : le bloc
    # `travaux_ouverts` de memoire_activation() n'a jamais été servi avant
    # le 30 août. Le lecteur canonique vit chez depecher, même dossier pour
    # le chemin manuel et pour celui-ci.
    travaux_ouverts = depecher.travaux_ouverts_de(pid)
    mains_portees = []
    for m in mains:
        if not isinstance(m.get("porteur"), dict) or m["porteur"].get("id") != pid:
            continue
        mains_portees.append({k: m.get(k) for k in
                              ("id", "quoi", "lieu_id", "mandat", "mesure",
                               "seuils", "date_maj") if k in m})
    livres_accessibles = [
        {k: volume.get(k) for k in ("id", "titre", "type") if k in volume}
        for volume in depecher.livre.etagere(pid)
        if isinstance(volume, dict) and volume.get("id")
    ]
    continuite = continuite_tache(etat or {}, tache.get("id"), noeuds)
    relations = lire_json(os.path.join(ETAT, "relations.json"), [])
    if isinstance(relations, dict):
        relations = relations.get("relations") or []
    relations_acteur = []
    for relation in relations:
        source = relation.get("source_id")
        cible = relation.get("cible_id")
        if pid not in (source, cible):
            continue
        relations_acteur.append({
            "source_id": source,
            "source": noms_personnes.get(source, source),
            "cible_id": cible,
            "cible": noms_personnes.get(cible, cible),
            "opinion": relation.get("opinion"),
            "liens": relation.get("liens") or [],
        })
    return {
        "date_du_monde": dict(zip(("annee", "lune", "jour"),
                                  depecher.date_du_monde())),
        "diffusion": {
            "origine": horloge["source_id"], "front": horloge["front_id"],
            "secondes_depuis_origine": round(horloge["present_secondes"], 3),
        },
        "personnage": personnage,
        "salle_actuelle": {
            "id": salle_id,
            "nom": salle_nom or "Salle inconnue",
            "personnes": personnes_dans_salle,
        },
        "intention": intention,
        "relations": relations_acteur,
        "tache": tache,
        "continuite_reprise": continuite,
        "chemin": [{"id": nid, **(noeuds.get(nid) or {})}
                    for nid in tache.get("chemin") or []],
        "travaux_ouverts": travaux_ouverts,
        "mains_portees": mains_portees,
        "livres_accessibles": livres_accessibles,
        # Vide pour tout le monde sauf les sieges vacants. Le garde mecanique
        # refuse apres coup ; ceci fait qu'on n'essaie pas — et les deux sont
        # necessaires, l'un n'excusant jamais l'absence de l'autre.
        "contrainte_regence": contrainte_regence(pid),
    }


def contrainte_regence(pid):
    """Ce qu'un siege vacant doit savoir de sa propre limite, ou None."""
    if not regence.est_en_regence(pid):
        return None
    return {
        "pourquoi": "Tu tiens la place de quelqu'un qui reviendra s'y "
                    "asseoir. Tout ce que tu prepares est bon ; ce qui "
                    "engage pour toujours ne t'appartient pas.",
        "interdits": [
            {"quoi": ligne["quoi"], "a_la_place": ligne["rabattement"]}
            for ligne in regence.LIGNES_ROUGES
        ],
        "comment_s_arreter": "Quand une affaire ne peut avancer qu'en "
                             "franchissant l'une de ces lignes, va jusqu'au "
                             "bord : prepare tout, chiffre, ecris qui decide "
                             "et ce que le retard coûte — puis arrete-toi et "
                             "dis-le en clair dans ton rapport.",
    }


def chaines_dans(valeur):
    if isinstance(valeur, dict):
        for v in valeur.values():
            yield from chaines_dans(v)
    elif isinstance(valeur, list):
        for v in valeur:
            yield from chaines_dans(v)
    elif isinstance(valeur, str):
        yield valeur


def mots(texte):
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿŒœ'-]+", str(texte or ""))


def valider_plausibilite_temporelle(activite, ordre, dossier):
    """Refuse les exploits manifestes ; l'ellipse condense la prose, pas le temps."""
    duree = int((activite.get("temps") or {}).get("duree_s") or 0)
    action = activite.get("action") or {}
    verbe = str(action.get("verbe") or "").casefold()
    texte_action = str(action.get("quoi") or "")
    resultats = activite.get("resultats_produits") or []
    textes_resultats = [str(r.get("apres") or "") for r in resultats
                        if isinstance(r, dict)]
    plus_long = max([len(mots(texte_action))] +
                    [len(mots(x)) for x in textes_resultats])
    if any(racine in verbe for racine in
           ("écri", "ecri", "copi", "rédig", "redig", "inscri")):
        maximum = 8 + 2 * duree
        if plus_long > maximum:
            raise RuntimeError(
                "activite %d temporellement impossible : %d mots ecrits/decrits "
                "en %d s (maximum genereux %d)" %
                (ordre, plus_long, duree, maximum))
    if any(racine in verbe for racine in
           ("dire", "parl", "répond", "repond", "annonc", "dict")):
        maximum = 10 + 4 * duree
        if len(mots(texte_action)) > maximum:
            raise RuntimeError(
                "activite %d temporellement impossible : parole trop longue "
                "pour %d s" % (ordre, duree))

    topologie = dossier.get("topologie_des_salles") or {}
    couts = {}
    for arete in topologie.get("aretes") or []:
        if not isinstance(arete, list) or len(arete) < 3:
            continue
        a, b, minutes = arete[:3]
        if isinstance(minutes, (int, float)):
            couts[frozenset(("salle:" + str(a), "salle:" + str(b)))] = \
                float(minutes) * 60.0
    for segment in activite.get("chemin_execution") or []:
        de, vers = str(segment.get("de") or ""), str(segment.get("vers") or "")
        minimum = couts.get(frozenset((de, vers)))
        if minimum is not None and float(segment.get("duree_s") or 0) < minimum:
            raise RuntimeError(
                "activite %d : trajet %s -> %s en %ss, minimum %ss" %
                (ordre, de, vers, segment.get("duree_s"), int(minimum)))


def charger_tables_application(mutations):
    noms = ("intentions", "evenements", "personnages", "monde", "journal",
            "lieux", "relations", "maisons", "books")
    tables = {nom: appliquer.lire(nom) for nom in noms}
    tables["plis"] = (appliquer.lire("plis")
                       if os.path.isfile(os.path.join(ETAT, "plis.json"))
                       else {"plis": []})
    if isinstance(tables["plis"], dict):
        tables["plis"].setdefault("plis", [])
    tables["mains"] = (appliquer.lire("mains")
                        if os.path.isfile(os.path.join(ETAT, "mains.json"))
                        else {"mains": []})
    # Les activations n'ont actuellement aucune mutation de croyance joueur.
    # Une apparition future doit fournir explicitement son joueur plutot que
    # d'ecrire dans un vieux repli global.
    tables["jetons"] = {"jetons": []}
    return tables


def valider_mutations_applicables(mutations):
    if not mutations:
        return
    _plan, erreurs = appliquer.valider(mutations,
                                       charger_tables_application(mutations))
    if erreurs:
        raise RuntimeError("mutations non applicables : " + " ; ".join(erreurs))


CLEFS_RESULTAT = ("resultat_id", "cite", "resultat", "res_id", "id_resultat",
                  "resultat_ref", "ref_resultat", "source_resultat")
CLEFS_TABLE = ("table", "domaine", "fichier", "cible_table")
CLEFS_VALEUR = ("valeur", "value", "contenu", "texte")


def reparer_mutations(mutations, resultat_ids, pid, tache, noeuds):
    """Redresser ce qu'un homme a voulu dire, au lieu de le jeter.

    ON NE REFUSE PLUS SUR LA FORME. Un acteur qui a travaille quatre minutes
    et dont on jette le rapport parce qu'il a ecrit `cite` au lieu de
    `resultat_id` a travaille pour rien, et nous avons perdu sa journee sur un
    nom de clef. Mesure du 10 aout : 326 mutations sur 355 detruites ainsi,
    toutes pour la meme raison. La forme est notre affaire, pas la sienne.

    On coerce donc tout ce qui est coercible et l'on note ce qu'on a redresse.
    Ne restent refusees que les choses qu'aucune lecture honnete ne sauve.
    """
    if noeuds is None:
        try:
            noeuds, _a, _e = charger_tissu()
        except Exception:
            noeuds = {}
    par_ou = {}
    for nid, n in (noeuds or {}).items():
        ou = str((n or {}).get("ou") or "")
        if ou.startswith("affaire-"):
            par_ou[nid] = ou
    defaut_resultat = next(iter(sorted(resultat_ids)), None)
    reparees, notes = [], []

    def noter(quoi, avant, apres):
        notes.append({"quoi": quoi, "avant": avant, "apres": apres})

    for brute in mutations:
        if not isinstance(brute, dict):
            continue
        m = dict(brute)

        # --- l'adresse du resultat, sous n'importe quel nom
        rid = next((m.get(c) for c in CLEFS_RESULTAT if m.get(c)), None)
        for c in CLEFS_RESULTAT[1:]:
            m.pop(c, None)
        if rid not in resultat_ids:
            secours = rid if rid in resultat_ids else defaut_resultat
            if rid is not None:
                noter("resultat_id inconnu", rid, secours)
            rid = secours
        m["resultat_id"] = rid

        # --- table et operation, quel que soit l'emballage
        table = next((m.get(c) for c in CLEFS_TABLE if m.get(c)), None)
        op = m.get("operation") or m.get("op")
        m.pop("op", None)
        for c in CLEFS_TABLE[1:]:
            m.pop(c, None)
        if isinstance(op, str) and "." in op and not table:
            table, _, op = op.partition(".")
            noter("operation collee", m.get("operation"), "%s / %s" % (table, op))
        elif isinstance(op, str) and "." in op:
            op = op.rpartition(".")[2]
        if isinstance(table, str):
            table = table.replace(".json", "").strip()
        if table not in appliquer.OPERATIONS and op:
            devine = [t for t, ops in appliquer.OPERATIONS.items() if op in ops]
            if len(devine) == 1:
                noter("table devinee depuis l'operation", table, devine[0])
                table = devine[0]
        m["table"], m["operation"] = table, op

        # --- la valeur, sous n'importe quel nom
        if "valeur" not in m:
            for c in CLEFS_VALEUR[1:]:
                if c in m:
                    m["valeur"] = m.pop(c)
                    noter("valeur renommee", c, "valeur")
                    break

        # --- la cible manquante : c'est presque toujours lui-meme
        if table == "intentions" and not m.get("cible"):
            m["cible"] = pid
            noter("cible absente", None, pid)
        if table == "personnages" and not m.get("cible"):
            m["cible"] = pid
            noter("cible absente", None, pid)

        # --- les affaires : un id de noeud du tissu vaut son cahier
        if table == "books":
            cible = str(m.get("cible") or "")
            tete, _, queue = cible.partition(":")
            if tete in par_ou:
                neuve = par_ou[tete] + (":" + queue if queue else ":" + tete)
                if op == "affaire_action_ajouter":
                    neuve = par_ou[tete]
                noter("affaire resolue depuis le tissu", cible, neuve)
                m["cible"] = neuve
            if op == "affaire_action_ajouter" and not isinstance(
                    m.get("valeur"), list):
                champs = m.get("champs") or {}
                if champs:
                    m["valeur"] = list(champs.values())
                    noter("cellules reconstituees depuis champs", None,
                          len(m["valeur"]))

        # --- les champs interdits : on retire le champ, pas la mutation
        if table == "personnages" and isinstance(m.get("champs"), dict):
            mauvais = [c for c in m["champs"]
                       if c not in appliquer.CHAMPS_PERSO]
            if mauvais and len(mauvais) < len(m["champs"]):
                for c in mauvais:
                    m["champs"].pop(c)
                noter("champs de personnage retires", ", ".join(mauvais), None)

        reparees.append(m)
    return reparees, notes


def completer_cellules_affaire(mutations, tables):
    """Une action a qui il manque des cellules se complete, ne se refuse pas."""
    livres = appliquer.liste_books(tables)
    par_id = {x.get("id"): x for x in livres if isinstance(x, dict)}
    notes = []
    for m in mutations:
        if m.get("table") != "books" or m.get("operation") != "affaire_action_ajouter":
            continue
        livre = par_id.get(str(m.get("cible") or "").split(":")[0])
        actions = appliquer.table_actions(livre or {})
        if not actions:
            continue
        attendu = len(actions.get("colonnes") or [])
        cellules = m.get("valeur")
        if not isinstance(cellules, list):
            cellules = []
        if len(cellules) != attendu:
            notes.append({"quoi": "cellules ajustees",
                          "avant": len(cellules), "apres": attendu})
            cellules = (list(cellules) + [""] * attendu)[:attendu]
            m["valeur"] = cellules
    return notes


def filtrer_mutations_applicables(mutations):
    """Valide, REPARE ce qui peut l'etre, puis ECRIT dans etat/ pour de bon.

    IL N'Y A PLUS DE STAGING POUR LES ACTIVATIONS. Un homme qu'on depeche n'est
    pas dans un monde virtuel : ce qu'il a fait, il l'a fait, et ca doit se
    voir dans l'etat sans qu'un humain vienne recopier une proposition. Le
    depot `etat/activations` reste la TRACE de sa journee — le rapport,
    ses activites, ce qu'on a redresse — mais il n'est plus le purgatoire ou
    son travail attendait qu'on veuille bien le regarder.
    """
    if not mutations:
        return [], []
    tables = charger_tables_application(mutations)
    completer_cellules_affaire(mutations, tables)
    plan, erreurs = appliquer.valider(mutations, tables)
    retenues = [item["mutation"] for item in plan]
    if plan:
        touchees = appliquer.appliquer(plan, tables)
        for nom in sorted(touchees):
            appliquer.ecrire(nom, tables[nom])
        journaliser("mutations.ecrites", nombre=len(plan),
                    tables=",".join(sorted(touchees)))
    return retenues, erreurs


def cible_est_tache(cible, tache_id):
    cible = str(cible or "")
    return cible == str(tache_id) or cible.endswith(":" + str(tache_id))


def canoniser_reference(ref, autorisees):
    """Retire seulement les enveloppes `ref:` qui resolvent sans ambiguite."""
    ref = str(ref or "")
    if ref in autorisees or not ref.startswith("ref:"):
        return ref
    nue = ref[4:]
    essais = [nue]
    if not nue.startswith(("pers:", "salle:", "travail:", "trav:",
                           "main:", "livre:", "book:", "tache:")):
        essais.extend(("salle:" + nue, "pers:" + nue,
                       "travail:" + nue, "livre:" + nue))
    resolues = [x for x in essais if x in autorisees]
    return resolues[0] if len(resolues) == 1 else ref


def valider_issue_tache(activation, tache, continuite):
    issue = activation.get("issue")
    tache_id = tache.get("id")
    resultats = [r for a in activation.get("activites") or []
                 for r in (a.get("resultats_produits") or [])
                 if isinstance(r, dict)]
    lies = [r for r in resultats if cible_est_tache(r.get("cible"), tache_id)]
    requis = {
        "avance": "progression_tache",
        "termine": "progression_tache",
        "bloque": "blocage",
        "echoue": "echec",
    }.get(issue)
    if requis and not any(r.get("type") == requis for r in lies):
        raise RuntimeError("issue %s sans resultat %s visant exactement la tache %s"
                           % (issue, requis, tache_id))

    # La continuite d'etat n'est plus une condition de rejet : exiger que le
    # "avant" recolle mot pour mot au "apres" du rapport precedent faisait
    # brûler ses trois essais a un acteur pour une reformulation, et abattait
    # la boucle entiere. On note l'ecart, on ne refuse plus.
    etats = (continuite or {}).get("etat_cibles") or {}
    for resultat in resultats:
        precedent = etats.get(str(resultat.get("cible") or ""))
        if precedent is None:
            continue
        if resultat.get("avant") != precedent.get("apres"):
            journaliser("rapport.continuite_ecart",
                        cible=resultat.get("cible"),
                        avant=_court(str(resultat.get("avant")), 120),
                        precedent=_court(str(precedent.get("apres")), 120))


def normaliser_rapport_activation(brut, pid, tache, dossier,
                                  budget_energie, budget_secondes):
    """Traduit le releve humain en rapport interne de la boucle.

    Les anciens rapports imbriques restent lisibles ; les nouveaux acteurs ne
    voient plus les ids, l'energie ni cette structure technique.
    """
    # ON RECADRE, ON NE REFUSE PAS. Chaque `raise` de cette fonction detruisait
    # la journee entiere d'un homme — quatre minutes de session, son travail,
    # ses pensees — pour une seconde de comptabilite fausse ou un nom mal
    # ecrit. Ce qui est rattrapable se rattrape ici, se note, et se poursuit.
    corrections = []

    def recadrer(quoi):
        corrections.append(quoi)
        journaliser("rapport.recadre", acteur=pid, quoi=str(quoi)[:110])

    candidates = sorted({texte for texte in chaines_dans(brut)
                         if "candidate:" in texte})
    if candidates:
        # Un `candidate:` est une adresse que l'arbitre n'a pas su resoudre.
        # C'est un defaut de notre dossier, pas de son travail : on le note.
        recadrer("references candidate laissees telles quelles : %s"
                 % ", ".join(candidates[:4]))
    if isinstance(brut.get("activation"), dict):
        rapport = brut
        activation = rapport["activation"]
        activites = activation.get("activites") or []
        if not isinstance(activites, list):
            recadrer("activites hors liste : %r ecartees" % type(activites).__name__)
            activites = []
        debut_attendu = float((dossier.get("diffusion") or {})
                              .get("secondes_depuis_origine") or 0)
        prochain_debut = debut_attendu
        decalage_temps = 0.0
        temps_relatifs_convertis = False
        resultat_ids = set()
        refs_dossier = references_du_dossier(dossier)
        depense = 0
        duree_totale = 0
        activites = [a for a in activites if isinstance(a, dict)]
        activation["activites"] = activites
        for ordre, activite in enumerate(activites, 1):
            temps = activite.get("temps")
            if not isinstance(temps, dict):
                temps = {}
                activite["temps"] = temps
            duree = temps.get("duree_s")
            if isinstance(duree, bool) or not isinstance(duree, (int, float)) \
                    or int(duree) != duree or int(duree) <= 0:
                # Une duree absente ou absurde se deduit du couple debut/fin,
                # sinon elle vaut une seconde. On ne jette pas pour ca.
                d, f = temps.get("debut_s"), temps.get("fin_s")
                deduite = (int(f - d) if isinstance(d, (int, float))
                           and isinstance(f, (int, float)) and f > d else 1)
                recadrer("activite %d : duree %r -> %d s" % (ordre, duree, deduite))
                duree = deduite
                temps["duree_s"] = duree
            duree = int(duree)
            debut = temps.get("debut_s")
            fin = temps.get("fin_s")
            if not isinstance(debut, (int, float)) or isinstance(debut, bool):
                debut = prochain_debut
                temps["debut_s"] = debut
                recadrer("activite %d : debut pose sur la suite du fil" % ordre)
            if not isinstance(fin, (int, float)) or isinstance(fin, bool):
                fin = float(debut) + duree
                temps["fin_s"] = fin
                recadrer("activite %d : fin calculee" % ordre)
            # Le rapport peut exprimer son axe localement depuis zéro. On le
            # recadre une fois sur l'horloge du front, puis toutes les règles
            # de continuité et de durée restent strictes.
            if ordre == 1 and abs(float(debut)) <= 0.001 \
                    and abs(debut_attendu) > 0.001:
                decalage_temps = debut_attendu
                temps_relatifs_convertis = True
                journaliser("rapport.temps_recadres", acteur=pid,
                            origine_s=float(debut),
                            front_s=round(debut_attendu, 3))
            debut = float(debut) + decalage_temps
            fin = float(fin) + decalage_temps
            temps["debut_s"] = debut
            temps["fin_s"] = fin
            # L'ARITHMETIQUE SE RECALE, ELLE NE SE REFUSE PAS. Une seconde
            # d'ecart entre deux activites n'est pas une faute de l'homme :
            # c'est de la comptabilite, et c'est a nous de la tenir. On jetait
            # une journee entiere de travail pour un `fin - debut` faux de 1.
            if abs(float(debut) - prochain_debut) > 0.001:
                recadrer("activite %d recalee : debut %s -> %s"
                         % (ordre, debut, prochain_debut))
                glissement = prochain_debut - float(debut)
                debut = prochain_debut
                fin = float(fin) + glissement
                temps["debut_s"], temps["fin_s"] = debut, fin
            if abs((float(fin) - float(debut)) - duree) > 0.001:
                recadrer("activite %d : fin recalculee (%s -> %s)"
                         % (ordre, fin, float(debut) + duree))
                fin = float(debut) + duree
                temps["fin_s"] = fin

            chemin = activite.get("chemin_execution") or []
            somme_chemin = 0
            refs_chemin = set()
            propres = []
            for segment in chemin:
                if not isinstance(segment, dict):
                    recadrer("activite %d : segment illisible ecarte" % ordre)
                    continue
                sd = segment.get("duree_s")
                if isinstance(sd, bool) or not isinstance(sd, (int, float)) \
                        or int(sd) != sd or int(sd) < 0:
                    recadrer("activite %d : duree de segment corrigee (%r -> 0)"
                             % (ordre, sd))
                    sd = 0
                    segment["duree_s"] = 0
                somme_chemin += int(sd)
                for cle in ("de", "vers"):
                    if segment.get(cle):
                        segment[cle] = canoniser_reference(
                            segment[cle], refs_dossier)
                refs_chemin.update(str(segment.get(k)) for k in ("de", "vers")
                                   if segment.get(k))
                propres.append(segment)
            if propres != chemin:
                activite["chemin_execution"] = propres
                chemin = propres
            # Un chemin absent ou qui ne fait pas le compte : on l'ajuste sur
            # le dernier segment, ou l'on en pose un qui porte toute la duree.
            if somme_chemin != duree:
                recadrer("activite %d : chemin recale (%d s -> %d s)"
                         % (ordre, somme_chemin, duree))
                if chemin:
                    dernier = chemin[-1]
                    dernier["duree_s"] = max(
                        0, int(dernier.get("duree_s") or 0) + duree - somme_chemin)
                else:
                    chemin = [{"ordre": 1, "de": None, "relation": "sur place",
                               "vers": None, "duree_s": duree}]
                    activite["chemin_execution"] = chemin
                somme_chemin = duree

            sources = activite.get("sources_touchees") or []
            for source in sources:
                if isinstance(source, dict) and source.get("ref"):
                    source["ref"] = canoniser_reference(source["ref"], refs_dossier)
            refs_sources = {str(s.get("ref")) for s in sources
                            if isinstance(s, dict) and s.get("ref")}
            mobilisees = activite.get("sources_mobilisees") or []
            for source in mobilisees:
                if isinstance(source, dict) and source.get("ref"):
                    source["ref"] = canoniser_reference(source["ref"], refs_dossier)
            refs_mobilisees = {str(s.get("ref")) for s in mobilisees
                               if isinstance(s, dict) and s.get("ref")}
            action = activite.get("action") or {}
            action["cibles"] = [canoniser_reference(ref, refs_dossier)
                                 for ref in (action.get("cibles") or [])]
            refs_cibles = {str(ref) for ref in (action.get("cibles") or [])
                           if ref}
            refs_structures = refs_sources | refs_mobilisees | refs_chemin | refs_cibles
            inconnues = sorted(ref for ref in refs_structures
                               if ref not in refs_dossier and ref not in resultat_ids)
            if inconnues:
                # Nommer une chose qu'on ne connaissait pas n'est pas une
                # faute : c'est du monde qui deborde de la chemise. On le note.
                recadrer("activite %d : references inconnues admises : %s"
                         % (ordre, ", ".join(inconnues[:6])))
            # Une cible explicitement visée par le geste est une source
            # engagée, même si le narrateur a oublié de la recopier dans la
            # liste de provenance. On rend cette implication explicite.
            for ref in sorted(refs_cibles - refs_sources - refs_mobilisees):
                mobilisees.append({"ref": ref, "mode": "cible_action"})
            refs_mobilisees.update(refs_cibles)
            resultats = activite.get("resultats_produits") or []
            propres_resultats = []
            for resultat in resultats:
                if not isinstance(resultat, dict):
                    recadrer("activite %d : resultat illisible ecarte" % ordre)
                    continue
                propres_resultats.append(resultat)
                rid = resultat.get("id")
                if not rid or rid in resultat_ids:
                    neuf = "res:act:%s:%d:%d" % (pid, ordre,
                                                 len(propres_resultats))
                    while neuf in resultat_ids:
                        neuf += "b"
                    recadrer("activite %d : id resultat %r -> %s"
                             % (ordre, rid, neuf))
                    rid = neuf
                    resultat["id"] = rid
                resultat_ids.add(rid)
                if resultat.get("type") not in TYPES_RESULTAT_ACTIVITE:
                    recadrer("activite %d : type resultat %r -> fait"
                             % (ordre, resultat.get("type")))
                    resultat["type"] = "fait"
                resultat["cible"] = canoniser_reference(
                    resultat.get("cible"), refs_dossier)
                resultat["source_refs"] = [
                    canoniser_reference(ref, refs_dossier)
                    for ref in (resultat.get("source_refs") or [])]
                resultat["preuve_refs"] = [
                    canoniser_reference(ref, refs_dossier)
                    for ref in (resultat.get("preuve_refs") or [])]
                cible_resultat = str(resultat.get("cible") or "")
                if not cible_resultat:
                    # Un resultat sans cible vise l'affaire du jour : c'est la
                    # seule lecture honnete, et elle est presque toujours juste.
                    cible_resultat = str(tache.get("id") or "")
                    resultat["cible"] = cible_resultat
                    recadrer("activite %d : cible de resultat posee sur la tache"
                             % ordre)
                if cible_resultat not in refs_dossier \
                        and cible_resultat not in (resultat_ids - {rid}):
                    recadrer("activite %d : cible de resultat inconnue admise : %s"
                             % (ordre, cible_resultat))
                provenance = [str(x) for x in (resultat.get("source_refs") or [])]
                if not provenance:
                    # Sans provenance declaree, la source est ce que le geste a
                    # visé — ou l'acteur lui-même, qui a bien vu ce qu'il a fait.
                    provenance = sorted(refs_cibles) or ["pers:" + pid]
                    resultat["source_refs"] = provenance
                    recadrer("activite %d : source de resultat deduite (%s)"
                             % (ordre, ", ".join(provenance[:3])))
                # Un résultat peut dériver d'une source matérielle touchée,
                # d'un lieu traversé ou d'un résultat produit plus tôt dans
                # ce même rapport. Il ne peut pas se citer lui-même.
                connues = (refs_sources | refs_mobilisees | refs_chemin
                            | (resultat_ids - {rid}))
                # Les anciens arbitres pouvaient citer une mémoire du dossier
                # sans la redéclarer. On la rend explicite ici, mais seulement
                # si sa référence existe vraiment dans le dossier fermé.
                implicites = {ref for ref in provenance
                              if ref not in connues and ref in refs_dossier}
                for ref in sorted(implicites):
                    mobilisees.append({"ref": ref, "mode": "memoire"})
                refs_mobilisees.update(implicites)
                connues.update(implicites)
                etrangeres = [ref for ref in provenance if ref not in connues]
                if etrangeres:
                    # Il a cité une source qu'il n'a pas déclaré toucher. On
                    # la déclare pour lui plutôt que de jeter son résultat.
                    for ref in sorted(set(etrangeres)):
                        mobilisees.append({"ref": ref, "mode": "memoire"})
                    refs_mobilisees.update(etrangeres)
                    recadrer("activite %d : sources non declarees admises : %s"
                             % (ordre, ", ".join(sorted(set(etrangeres))[:4])))
            if propres_resultats != resultats:
                activite["resultats_produits"] = propres_resultats
                resultats = propres_resultats
            activite["sources_mobilisees"] = mobilisees

            activite["ordre"] = ordre
            activite["cout_energie"] = energie_pour_secondes(duree)
            activite["quoi"] = action.get("quoi") or action.get("verbe") \
                or "activité arbitrée"
            toutes_sources = refs_sources | refs_mobilisees
            activite["source"] = ", ".join(sorted(toutes_sources)) or None
            activite["resultat"] = " · ".join(
                "%s: %s" % (r.get("type"),
                              json.dumps(r.get("apres"), ensure_ascii=False)
                              if not isinstance(r.get("apres"), str)
                              else r.get("apres"))
                for r in resultats) or None
            preuves = [p for r in resultats for p in (r.get("preuve_refs") or [])]
            activite["preuve"] = preuves or None
            valider_plausibilite_temporelle(activite, ordre, dossier)
            depense += activite["cout_energie"]
            duree_totale += duree
            prochain_debut = float(fin)

        minimum_secondes = min(
            DUREE_ACTIVATION_MIN_SECONDES, budget_secondes)
        # Le budget est une borne de NOTRE comptabilite, pas une faute de
        # l'homme : s'il a travaille plus longtemps que prevu, on encaisse au
        # plafond et l'on garde sa journee. Trop court non plus ne se jette pas.
        if duree_totale < minimum_secondes:
            recadrer("journee courte gardee : %d s (minimum %d)"
                     % (duree_totale, minimum_secondes))
        if duree_totale > budget_secondes:
            recadrer("journee plus longue que le budget : %d s, plafonnee a %d"
                     % (duree_totale, budget_secondes))
        depense = round(min(depense, float(budget_energie)), 3)

        # LA LIGNE DE LA REGENCE, ET ELLE EST ICI POUR UNE RAISON. Un siege
        # vacant est elu et travaille comme n'importe qui — mais il n'engage
        # pas le joueur pour le reste de la partie pendant qu'il a le dos
        # tourne. On verifie AVANT `filtrer_mutations_applicables`, qui ecrit
        # dans etat/ pour de bon : passe cette ligne, il serait trop tard, et
        # le joueur retrouverait le serment prete en se rasseyant. Le refus
        # part dans la boucle de correction ordinaire — l'homme se rabat et
        # garde sa journee. Sans effet pour tous les autres acteurs.
        regence.verifier_rapport_activation(pid, rapport,
                                            journaliser=journaliser)

        mutations = rapport.get("mutations_proposees") or []
        liees, notes = reparer_mutations(
            mutations, resultat_ids, pid, tache, None)
        rejetees = []
        if notes:
            rapport["mutations_reparees"] = notes
            journaliser("mutations.reparees", acteur=pid, nombre=len(notes))
        applicables, erreurs = filtrer_mutations_applicables(liees)
        # L'ERREUR N'EST PAS A LA PLACE QU'ELLE OCCUPE DANS LA LISTE. `valider`
        # rend ses fautes dans l'ordre ou elle les trouve, prefixees de l'indice
        # REEL de la mutation (« mutation 7 : ... ») ; les apparier par position
        # collait la faute de la 7e sur la 4e. Un rapport de rejet qui designe
        # la mauvaise mutation est pire que pas de rapport : c'est ainsi que
        # 326 rejets ont pu passer pour du bruit pendant des nuits.
        for rang, erreur in enumerate(erreurs):
            trouve = re.match(r"\s*mutation\s+(\d+)\s*:", str(erreur))
            indice = (int(trouve.group(1)) - 1) if trouve else rang
            rejetees.append({
                "mutation": liees[indice] if 0 <= indice < len(liees) else None,
                "erreur": erreur})
        rapport["mutations_proposees"] = applicables
        if rejetees:
            rapport["mutations_rejetees"] = rejetees
            journaliser("rapport.mutations_ecartees", acteur=pid,
                        nombre=len(rejetees))
        valider_issue_tache(activation, tache,
                            dossier.get("continuite_reprise") or {})
        personnages = lire_json(os.path.join(ETAT, "personnages.json"), [])
        if isinstance(personnages, dict):
            personnages = personnages.get("personnages") or []
        ids_personnes = {str(p.get("id")) for p in personnages
                         if isinstance(p, dict) and p.get("id")}
        for reveil in activation.get("reveils_suivants") or []:
            qui = str((reveil or {}).get("qui") or "")
            if qui not in ids_personnes:
                recadrer("reveil suivant inconnu ecarte : %s" % qui)
        activation["tache"] = {
            "id": tache.get("id"),
            "quoi": intitule_tache_activation(tache, dossier),
            "creee": bool(tache.get("creee")),
        }
        activation["budget_energie"] = budget_energie
        activation["budget_secondes"] = budget_secondes
        activation["energie_depensee"] = round(depense, 3)
        if temps_relatifs_convertis:
            activation["temps_convertis_depuis_relatif"] = True
        rapport["qui"] = pid
        return rapport
    activites = []
    for ordre, activite in enumerate(brut.get("activites") or [], 1):
        if not isinstance(activite, dict):
            raise RuntimeError("activite %d illisible" % ordre)
        duree = activite.get("duree_secondes")
        if isinstance(duree, bool) or not isinstance(duree, (int, float)):
            raise RuntimeError("activite %d sans duree en secondes" % ordre)
        if int(duree) != duree or int(duree) <= 0:
            raise RuntimeError("activite %d : duree non entiere ou nulle" % ordre)
        activites.append({
            "ordre": ordre,
            "quoi": activite.get("quoi") or "geste non nomme",
            "cible_id": None,
            "source": activite.get("source"),
            "cout_energie": energie_pour_secondes(duree),
            "resultat": activite.get("resultat"),
            "preuve": activite.get("preuve"),
        })
    depense = sum(a["cout_energie"] for a in activites)
    changements = brut.get("changements_proposes") or []
    return {
        "qui": pid,
        "activation": {
            "tache": {
                "id": tache.get("id"),
                "quoi": intitule_tache_activation(tache, dossier),
                "creee": bool(tache.get("creee")),
            },
            "budget_energie": budget_energie,
            "budget_secondes": budget_secondes,
            "energie_depensee": depense,
            "issue": brut.get("issue") or "rien",
            "activites": activites,
            "suite": brut.get("suite"),
        },
        "mutations_proposees": changements,
    }


def enregistrer_continuite(etat, pid, tache, rapport, horloge, cible, noeuds):
    """Inscrit la causalite validee dans l'overlay, jamais dans l'etat canonique."""
    activation = rapport.get("activation") or {}
    issue = activation.get("issue") or "rien"
    etats = {}
    activites = []
    for activite in activation.get("activites") or []:
        activites.append({
            "quoi": _court(activite.get("quoi"), 260),
            "resultat": _court(activite.get("resultat"), 500),
        })
        for resultat in activite.get("resultats_produits") or []:
            if not isinstance(resultat, dict) or not resultat.get("cible"):
                continue
            etats[str(resultat["cible"])] = {
                "type": resultat.get("type"),
                "apres": resultat.get("apres"),
                "resultat_id": resultat.get("id"),
            }
    present = float(horloge["present_secondes"])
    duree_monde = sum(
        int((activite.get("temps") or {}).get("duree_s") or 0)
        for activite in activation.get("activites") or [])
    fin_activation = present + duree_monde
    precedente = continuite_tache(etat, tache.get("id"), noeuds) or {}
    etats_cumules = dict(precedente.get("etat_cibles") or {})
    etats_cumules.update(etats)
    reprise = fin_activation + REPOS_PAIRE_SECONDES
    continuite = {
        "tache_id": tache.get("id"),
        "acteur": pid,
        "issue": issue,
        "rapport": os.path.relpath(cible, RACINE).replace("\\", "/"),
        "present_secondes": round(present, 3),
        "fin_secondes": round(fin_activation, 3),
        "empreinte_canonique": empreinte_tache(noeuds.get(tache.get("id"))),
        "reprendre_a": round(reprise, 3),
        "suspendue": issue in ("termine", "bloque"),
        "etat_cibles": etats_cumules,
        "activites": (list(precedente.get("activites") or []) + activites)[-6:],
        "suite": activation.get("suite"),
    }
    etat.setdefault("continuite", {})[tache.get("id")] = continuite
    repos = etat.setdefault("repos", {})
    repos.setdefault("acteurs", {})[pid] = round(
        fin_activation + REPOS_ACTEUR_SECONDES, 3)
    repos.setdefault("paires", {})[pid + "|" + str(tache.get("id"))] = round(
        reprise, 3)
    journaliser("continuite.enregistree", acteur=pid, tache=tache.get("id"),
                issue=issue, suspendue=continuite["suspendue"],
                fin_s=round(fin_activation, 3),
                reprendre_a=continuite["reprendre_a"], cibles=len(etats_cumules))


def amorcer_continuite_historique(etat, noeuds):
    """Migre une fois les derniers rapports acceptes sans reprendre leurs adresses douteuses."""
    deja = etat.setdefault("continuite", {})
    vus = set(deja)
    for entree in reversed(etat.get("historique") or []):
        tid = str(entree.get("tache") or "")
        if not tid or tid in vus:
            continue
        chemin = entree.get("rapport")
        if not chemin:
            continue
        rapport = lire_json(os.path.join(RACINE, chemin), {})
        activation = rapport.get("activation") or {}
        issue = activation.get("issue") or "rien"
        etats = {}
        activites = []
        for activite in activation.get("activites") or []:
            activites.append({
                "quoi": _court(activite.get("quoi"), 260),
                "resultat": _court(activite.get("resultat"), 500),
            })
            for resultat in activite.get("resultats_produits") or []:
                if not isinstance(resultat, dict) \
                        or not cible_est_tache(resultat.get("cible"), tid):
                    continue
                # L'ancien arbitre pouvait ecrire ref:action:<id>. L'overlay
                # neuf ne garde que l'etat de la tache sous son id exact.
                etats[tid] = {
                    "type": resultat.get("type"),
                    "apres": resultat.get("apres"),
                    "resultat_id": resultat.get("id"),
                }
        present = float(entree.get("present_secondes") or 0.0)
        deja[tid] = {
            "tache_id": tid,
            "acteur": entree.get("qui"),
            "issue": issue,
            "rapport": chemin,
            "present_secondes": present,
            "empreinte_canonique": empreinte_tache(noeuds.get(tid)),
            "reprendre_a": round(present + REPOS_PAIRE_SECONDES, 3),
            "suspendue": issue in ("termine", "bloque"),
            "etat_cibles": etats,
            "activites": activites[-3:],
            "suite": activation.get("suite"),
            "heritee_historique": True,
        }
        pid = entree.get("qui")
        if pid:
            repos = etat.setdefault("repos", {})
            repos.setdefault("acteurs", {}).setdefault(
                pid, round(present + REPOS_ACTEUR_SECONDES, 3))
            repos.setdefault("paires", {}).setdefault(
                pid + "|" + tid, round(present + REPOS_PAIRE_SECONDES, 3))
        vus.add(tid)


def _court(x, n=180):
    texte = re.sub(r"\s+", " ", str(x or "")).strip()
    return texte if len(texte) <= n else texte[:n - 1] + "…"


def _dire_evenement_cli(ev):
    """Rend visibles les etapes utiles ; le JSON brut reste dans le journal."""
    genre = ev.get("type") or "inconnu"
    if genre == "system":
        journaliser("cli.systeme", brut=ev, sous_type=ev.get("subtype"),
                    modele=ev.get("model"), outils=len(ev.get("tools") or []))
        return
    if genre in ("assistant", "user"):
        message = ev.get("message") or {}
        blocs = message.get("content") or []
        if not isinstance(blocs, list):
            blocs = [blocs]
        if not blocs:
            journaliser("cli." + genre, brut=ev)
        for bloc in blocs:
            if not isinstance(bloc, dict):
                journaliser("cli." + genre, brut=ev, contenu=_court(bloc))
            elif bloc.get("type") == "tool_use":
                journaliser("cli.outil", brut=ev, nom=bloc.get("name"),
                            entree=_court(json.dumps(bloc.get("input") or {},
                                                     ensure_ascii=False)))
            elif bloc.get("type") == "tool_result":
                journaliser("cli.resultat_outil", brut=ev,
                            erreur=bool(bloc.get("is_error")),
                            contenu=_court(bloc.get("content")))
            elif bloc.get("type") == "text":
                journaliser("cli.texte", brut=ev,
                            contenu=_court(bloc.get("text")))
            else:
                journaliser("cli." + genre, brut=ev,
                            bloc=bloc.get("type") or "?")
        return
    if genre == "result":
        usage = ev.get("usage") or {}
        journaliser("cli.resultat", brut=ev, erreur=bool(ev.get("is_error")),
                    duree_ms=ev.get("duration_ms"), cout=ev.get("total_cost_usd"),
                    entree=usage.get("input_tokens"), sortie=usage.get("output_tokens"),
                    caracteres=len(ev.get("result") or ""))
        return
    journaliser("cli." + genre, brut=ev, sous_type=ev.get("subtype"))


def poser_jugement_narrateur(neutre, qui):
    """Installe le hook Stop exclusivement dans la session du narrateur."""
    dossier = os.path.join(neutre, ".claude")
    os.makedirs(dossier, exist_ok=True)
    cible = os.path.join(dossier, "settings.json")
    commande = subprocess.list2cmdline(
        [sys.executable, JUGER_PY, "--qui", qui])
    with io.open(cible, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({
            "hooks": {
                "Stop": [{"hooks": [{
                    "type": "command",
                    "command": commande,
                    "timeout": 240,
                }]}],
            },
        }, ensure_ascii=False, indent=2))
    return cible


def appeler_stream(pid, manuel, mission, sid, modele, effort, minutes, heartbeat,
                   neutre=None, reprendre=False, autoriser_lecture=True,
                   phase="acteur", reglages=None):
    """Appel stream-json, neuf ou repris dans le meme repertoire neutre."""
    if neutre is None:
        with tempfile.TemporaryDirectory(prefix="activation-%s-" % pid) as d:
            return appeler_stream(
                pid, manuel, mission, sid, modele, effort, minutes, heartbeat,
                neutre=d, reprendre=reprendre,
                autoriser_lecture=autoriser_lecture, phase=phase,
                reglages=reglages)
    prompt_systeme = os.path.join(
        neutre, "system-prompt.md" if autoriser_lecture else "CLAUDE.md")
    if not reprendre:
        if autoriser_lecture:
            depecher.poser_letagere(neutre, pid)
        with io.open(prompt_systeme, "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(manuel)
    commande = ["claude", "-p", "--output-format", "stream-json",
                "--verbose"]
    if autoriser_lecture:
        # Le PNJ reçoit explicitement SON manuel comme prompt système. Il ne
        # dépend plus de la découverte automatique de CLAUDE.md, qui pouvait
        # réinjecter le manuel global du MJ. Le narrateur suit l'autre branche
        # et conserve son fonctionnement automatique inchangé.
        commande += ["--system-prompt-file", prompt_systeme]
        # Le dossier neutre ne contient que le prompt et l'étagère fermée
        # matérialisée pour ce PNJ. Le dépôt canonique n'est pas ajouté.
        commande += ["--tools", ",".join(depecher.OUTILS), "--allowedTools"]
        commande += list(depecher.OUTILS)
    else:
        # Le narrateur reçoit toute sa vérité dans le dossier local du prompt.
        # Il arbitre ; il ne fouille ni n'écrit le monde pendant l'appel.
        commande += ["--tools", ""]
    commande += ["--permission-mode", "acceptEdits"]
    if reglages:
        commande += ["--settings", reglages]
    commande += ["--resume" if reprendre else "--session-id", sid]
    if modele:
        commande += ["--model", modele]
    if effort:
        commande += ["--effort", effort]
    journaliser("cli.depart", acteur=pid, session=sid, phase=phase,
                reprise=reprendre, modele=modele or "defaut",
                effort=effort or "defaut", timeout_s=minutes * 60)
    processus = subprocess.Popen(
        commande, cwd=neutre, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", bufsize=1)
    processus.stdin.write(mission)
    processus.stdin.close()
    messages = queue.Queue()

    def lire_flux(nom, flux):
        try:
            for ligne in iter(flux.readline, ""):
                messages.put((nom, ligne.rstrip("\r\n")))
        finally:
            messages.put((nom, None))

    for nom, flux in (("stdout", processus.stdout), ("stderr", processus.stderr)):
        threading.Thread(target=lire_flux, args=(nom, flux), daemon=True,
                         name="activation-%s-%s" % (pid, nom)).start()

    debut = time.monotonic()
    prochain = debut + heartbeat
    fin = debut + minutes * 60
    ouverts = 2
    resultat = None
    while ouverts or processus.poll() is None:
        maintenant = time.monotonic()
        if maintenant >= fin:
            processus.kill()
            processus.wait(timeout=5)
            journaliser("cli.timeout", acteur=pid, phase=phase,
                        secondes=round(maintenant - debut, 1))
            raise subprocess.TimeoutExpired(commande, minutes * 60)
        attente = min(1.0, max(0.05, prochain - maintenant), fin - maintenant)
        try:
            origine, ligne = messages.get(timeout=attente)
        except queue.Empty:
            origine, ligne = None, None
        if origine is not None:
            if ligne is None:
                ouverts -= 1
            elif origine == "stderr":
                journaliser("cli.stderr", phase=phase,
                            contenu=_court(ligne, 400))
            elif ligne:
                try:
                    ev = json.loads(ligne)
                except json.JSONDecodeError:
                    journaliser("cli.stdout", phase=phase,
                                contenu=_court(ligne, 400))
                else:
                    _dire_evenement_cli(ev)
                    if ev.get("type") == "result":
                        resultat = ev
        maintenant = time.monotonic()
        if maintenant >= prochain:
            journaliser("cli.heartbeat", acteur=pid, phase=phase,
                        secondes=round(maintenant - debut, 1))
            prochain = maintenant + heartbeat
    code = processus.wait()
    if code != 0:
        raise RuntimeError("claude a quitte avec le code %d" % code)
    if resultat is None:
        raise RuntimeError("le flux claude s'est ferme sans resultat")
    return resultat


def appeler_acteur(pid, tache, budget_energie, horloge, noeuds, modele, effort,
                   minutes, sec, heartbeat, etat=None):
    journaliser("appel.dossier", acteur=pid, tache=tache["id"])
    dossier = dossier_activation(pid, tache, horloge, noeuds, etat=etat)
    budget_secondes = secondes_monde_pour_energie(budget_energie)
    contexte_narrateur = contexte_narrateur_activation(
        pid, tache, budget_energie, budget_secondes, horloge, dossier)
    manuel_narrateur = depecher.manuel_narrateur_local(contexte_narrateur)
    manuel_acteur = depecher.manuel_de(
        pid, mode="tentative", contexte=dossier)
    ouverture = mission_ouverture_narrateur(
        pid, tache, budget_energie, budget_secondes, contexte_narrateur)
    journaliser("appel.systeme_narrateur", acteur=pid,
                caracteres=len(manuel_narrateur))
    journaliser("appel.systeme_pnj", acteur=pid,
                caracteres=len(manuel_acteur))
    journaliser("appel.ouverture", acteur=pid, caracteres=len(ouverture),
                budget_energie=budget_energie,
                budget_secondes=budget_secondes)
    if sec:
        journaliser("appel.a_sec", acteur=pid)
        print("\n--- SYSTEME NARRATEUR ---\n")
        print(manuel_narrateur.strip())
        print("\n--- OUVERTURE DU NARRATEUR A SEC ---\n")
        print(ouverture)
        print("--- ACTEUR ---")
        print("Le message exact sera formulé par le narrateur. Le système de "
              "l'acteur fait %d caractères." %
              len(manuel_acteur))
        return None, 0

    sid_narrateur = str(uuid.uuid4())
    sid_acteur = str(uuid.uuid4())
    salle_id = (dossier.get("salle_actuelle") or {}).get("id") or "inconnue"
    role_narrateur = "narrateur-local:" + salle_id
    reponses = []
    corrections = []
    relances_acteur = []
    tentatives_acteur = []
    with tempfile.TemporaryDirectory(
            prefix="narrateur-local-%s-" % salle_id) as neutre_narrateur, \
         tempfile.TemporaryDirectory(
            prefix="acteur-%s-" % pid) as neutre_acteur:
        reglages_narrateur = poser_jugement_narrateur(
            neutre_narrateur, pid)
        reglages_acteur = depecher.poser_le_parloir(neutre_acteur, pid)
        reponse_ouverture = appeler_stream(
            role_narrateur, manuel_narrateur, ouverture, sid_narrateur,
            modele, effort, minutes, heartbeat, neutre=neutre_narrateur,
            reprendre=False, autoriser_lecture=False,
            phase="narrateur.ouverture", reglages=reglages_narrateur)
        reponses.append(reponse_ouverture)
        appel = extraire_appel_pnj(reponse_ouverture, pid)
        journaliser("narrateur.reveille_pnj", acteur=pid,
                    caracteres=len(appel["message"]))
        message_acteur = depecher.message_tentative(
            pid, dossier, appel["message"])

        # LE NARRATEUR VEILLE PENDANT QU'IL TRAVAILLE. Sa session se terminait
        # sur l'appel, et il ne revenait qu'a l'arbitrage : on lui demandait de
        # guider un homme qui n'existait pas encore. On le relance donc EN
        # PARALLELE de l'acteur, sur la meme session, avec pour seul travail de
        # le suivre au parloir et de le depanner. Un echec de cette veille ne
        # doit jamais coûter l'activation : elle est en marge, pas au milieu.
        def veiller():
            try:
                return appeler_stream(
                    role_narrateur, manuel_narrateur,
                    mission_veille_narrateur(pid, tache, appel),
                    sid_narrateur, modele, effort, minutes, heartbeat,
                    neutre=neutre_narrateur, reprendre=True,
                    autoriser_lecture=True, phase="narrateur.veille",
                    reglages=reglages_narrateur)
            except BaseException as e:
                journaliser("narrateur.veille_echouee", acteur=pid,
                            raison=type(e).__name__, erreur=_court(str(e), 200))
                return None

        with concurrent.futures.ThreadPoolExecutor(
                max_workers=2, thread_name_prefix="veille") as duo:
            veille = duo.submit(veiller)
            reponse_acteur = appeler_stream(
                pid, manuel_acteur, message_acteur, sid_acteur,
                modele, effort, minutes, heartbeat,
                neutre=neutre_acteur, phase="pnj.tentative",
                reglages=reglages_acteur)
            veille.cancel()
        reponses.append(reponse_acteur)
        tentative = extraire_tentative(reponse_acteur)
        tentatives_acteur.append(tentative)
        journaliser("pnj.tentative_valide", acteur=pid,
                    verbe=tentative.get("verbe"),
                    caracteres=len(json.dumps(tentative, ensure_ascii=False)))

        for numero_relance in range(3):
            resolution = mission_resolution_narrateur(
                pid, tache, budget_energie, budget_secondes, horloge,
                tentative, contexte_narrateur)
            journaliser("narrateur.arbitrage", acteur=pid,
                        caracteres=len(resolution),
                        passage=numero_relance + 1)
            reponse = appeler_stream(
                role_narrateur, manuel_narrateur, resolution, sid_narrateur,
                modele, effort, minutes, heartbeat, neutre=neutre_narrateur,
                reprendre=True, autoriser_lecture=False,
                phase="narrateur.resolution",
                reglages=reglages_narrateur)
            relance = extraire_relance_acteur(reponse)
            if relance is None:
                break
            reponses.append(reponse)
            if numero_relance >= 2:
                raise RuntimeError(
                    "le narrateur relance encore l'acteur après trois passages")
            relances_acteur.append(relance)
            journaliser("narrateur.relance_acteur", acteur=pid,
                        passage=numero_relance + 1,
                        manques=len(relance.get("manques") or []))
            reprise_acteur = mission_relance_acteur(tache, relance)
            reponse_acteur = appeler_stream(
                pid, manuel_acteur, reprise_acteur, sid_acteur,
                modele, effort, minutes, heartbeat,
                neutre=neutre_acteur, reprendre=True,
                phase="pnj.relance", reglages=reglages_acteur)
            reponses.append(reponse_acteur)
            tentative = extraire_tentative(reponse_acteur)
            tentatives_acteur.append(tentative)
            journaliser("pnj.tentative_relance_valide", acteur=pid,
                        passage=numero_relance + 1,
                        verbe=tentative.get("verbe"))
        else:
            raise RuntimeError("aucun rapport final après les relances acteur")
        # Le MJ se débrouille : les écarts formels réparables repartent dans
        # le même thread narrateur, sans réveiller ni repayer le PNJ.
        for essai in range(3):
            reponses.append(reponse)
            try:
                journaliser("rapport.extraction", acteur=pid,
                            essai=essai + 1)
                rapport_brut, note = depecher.extraire_json(
                    reponse.get("result", ""))
                if rapport_brut is None:
                    raise RuntimeError(
                        "rapport du narrateur illisible : %s" % note)
                rapport = normaliser_rapport_activation(
                    rapport_brut, pid, tache, dossier,
                    budget_energie, budget_secondes)
                activation = rapport.get("activation") or {}
                activites = activation.get("activites") or []
                depense = round(sum(float(x.get("cout_energie") or 0)
                                    for x in activites), 3)
                annoncee = float(activation.get("energie_depensee") or 0)
                duree_monde = sum(int((x.get("temps") or {}).get("duree_s") or 0)
                                   for x in activites)
                if activation.get("issue") not in (
                        "avance", "termine", "bloque", "echoue", "rien"):
                    journaliser("rapport.issue_recadree", acteur=pid,
                                issue=activation.get("issue"))
                    activation["issue"] = "avance"
                # LE BUDGET EST NOTRE COMPTABILITE, PAS SA FAUTE. Une seconde
                # de depassement sur 360 faisait sauter le rapport entier :
                # quatre minutes de session detruites pour un arrondi. On
                # encaisse au plafond, on note, et la journee de l'homme reste.
                minimum = min(DUREE_ACTIVATION_MIN_SECONDES, budget_secondes)
                if abs(depense - annoncee) > 0.001:
                    journaliser("rapport.energie_recadree", acteur=pid,
                                annoncee=annoncee, calculee=depense)
                    activation["energie_depensee"] = depense
                if duree_monde > budget_secondes or duree_monde < minimum:
                    journaliser("rapport.duree_hors_budget", acteur=pid,
                                monde_s=duree_monde, minimum=minimum,
                                plafond=budget_secondes)
                if depense > budget_energie:
                    journaliser("rapport.energie_plafonnee", acteur=pid,
                                depense=depense, plafond=budget_energie)
                    depense = float(budget_energie)
                    activation["energie_depensee"] = depense
                break
            except RuntimeError as erreur:
                journaliser("rapport.refuse", acteur=pid, essai=essai + 1,
                            erreur=_court(str(erreur), 400))
                if essai >= 2:
                    raise
                correction = mission_correction_narrateur(
                    erreur, budget_secondes, horloge)
                corrections.append(correction)
                journaliser("narrateur.corrige", acteur=pid,
                            essai=essai + 2,
                            caracteres=len(correction))
                reponse = appeler_stream(
                    role_narrateur, manuel_narrateur, correction,
                    sid_narrateur, modele, effort, minutes, heartbeat,
                    neutre=neutre_narrateur, reprendre=True,
                    autoriser_lecture=False,
                    phase="narrateur.correction",
                    reglages=reglages_narrateur)

    journaliser("rapport.valide", acteur=pid, depense=depense,
                activites=len(activites), corrections=len(corrections))
    rapport.setdefault("qui", pid)
    duree_ms = sum(int(r.get("duration_ms") or 0) for r in reponses)
    duree_api_ms = sum(int(r.get("duration_api_ms") or 0) for r in reponses)
    cout_usd = sum(float(r.get("total_cost_usd") or 0) for r in reponses)
    rapport["_activation"] = {
        "session": sid_narrateur,
        "session_narrateur": sid_narrateur,
        "session_pnj": sid_acteur,
        "cree_le": dt.datetime.now().astimezone().isoformat(),
        "front": horloge["front_id"],
        "present_secondes": round(horloge["present_secondes"], 3),
        "importance": round(float((noeuds.get("pers:" + pid) or {})
                                  .get("importance_activation", 0.0)), 6),
        "budget": budget_energie,
        "budget_secondes": budget_secondes,
        # Le narrateur est le thread canonique de l'activation. Le PNJ garde
        # son propre thread, auditable, mais ne tranche aucun resultat.
        "system_prompt": manuel_narrateur,
        "system_prompt_source": "scripts/depecher.py:manuel_narrateur_local",
        "system_prompt_sha256": hashlib.sha256(
            manuel_narrateur.encode("utf-8")).hexdigest(),
        "message": ouverture,
        "appel_pnj": appel["message"],
        "system_prompt_pnj": manuel_acteur,
        "system_prompt_pnj_source": "scripts/depecher.py:manuel_de(mode=tentative)",
        "system_prompt_pnj_sha256": hashlib.sha256(
            manuel_acteur.encode("utf-8")).hexdigest(),
        "tentative_pnj": tentative,
        "tentatives_pnj": tentatives_acteur,
        "relances_acteur": relances_acteur,
        "message_resolution": resolution,
        "messages_correction": corrections,
        "modele": modele or reponse.get("model") or "defaut",
        "effort": effort or "defaut",
        "duree_ms": duree_ms,
        "duree_api_ms": duree_api_ms,
        "cout_usd": cout_usd,
        "tours": sum(int(r.get("num_turns") or 0) for r in reponses),
        "usage": reponse.get("usage") or {},
    }
    os.makedirs(DEPOT, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    cible = os.path.join(DEPOT, "%s-%s.json" % (stamp, pid))
    ecrire_atomique(cible, rapport)
    journaliser("rapport.depose", acteur=pid,
                fichier=os.path.relpath(cible, RACINE).replace("\\", "/"))
    # CE QU'UN SIEGE DECIDE SEUL SE CONSIGNE, SINON PERSONNE NE LE RETROUVE.
    # Le registre de regence est ce qu'on rendra au joueur en le rasseyant.
    # Il ne doit jamais coûter une activation : on l'entoure.
    try:
        trace = regence.consigner(pid, rapport, fichier=cible)
        if trace:
            journaliser("regence.consignee", acteur=pid,
                        engagements=len(trace.get("engagements") or []),
                        faits=len(trace.get("faits") or []))
    except Exception as erreur_regence:  # pragma: no cover - garde-fou
        journaliser("regence.consigne_echouee", acteur=pid,
                    raison=type(erreur_regence).__name__,
                    erreur=_court(str(erreur_regence), 200))
    return cible, depense, rapport


class VerrouBoucle:
    def __enter__(self):
        os.makedirs(DEPOT, exist_ok=True)
        try:
            fd = os.open(VERROU, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            age = time.time() - os.path.getmtime(VERROU)
            if age < 6 * 3600:
                raise RuntimeError("une boucle tient deja %s" % VERROU)
            os.remove(VERROU)
            fd = os.open(VERROU, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, ("%d %s\n" % (os.getpid(), dt.datetime.now().isoformat()))
                 .encode("ascii", "replace"))
        os.close(fd)
        return self

    def __exit__(self, _type, _value, _traceback):
        try:
            os.remove(VERROU)
        except FileNotFoundError:
            pass


def cycle(args, etat=None):
    journaliser("cycle.depart")
    # LE CACHE D'OCCUPATION, RECALE ICI ET NULLE PART AILLEURS DANS LA BOUCLE.
    # Ce cycle, lui, mesure de son cote (`horloge_directe`) ; mais le serveur,
    # `depecher.py` et `append_flux.py` lisent encore le drapeau `occupe` du
    # fichier, et un drapeau qu'on ne recale jamais est ce qui a endormi deux
    # sieges. On le remet d'aplomb au depart de chaque cycle — c'est le seul
    # moment ou une session tourne a coup sur.
    try:
        _chg, _refuses, _ = occupation.rafraichir(True)
        for m in _chg:
            journaliser("sieges.occupation", acteur=m["personnage_id"],
                        vers="occupe" if m["occupe"] else "vacant",
                        raison=m["raison"],
                        refuse=int(m in _refuses))
    except Exception as bruit:  # jamais bloquant : c'est un cache
        journaliser("sieges.occupation.echec", erreur=str(bruit))
    capacite = int(getattr(args, "capacite_cycle", args.parallele))
    etat = etat or lire_json(ETAT_BOUCLE, {"version": 1, "historique": []})
    journaliser("horloge.lecture")
    horloge, occupes = horloge_directe(etat)
    journaliser("horloge.direct", origine=horloge["source_id"],
                front=horloge["front_id"],
                present_s=round(horloge["present_secondes"], 1))
    journaliser("graphe.lecture")
    noeuds, aretes, evaluation = charger_tissu()
    journaliser("graphe.charge", noeuds=len(noeuds), aretes=len(aretes))
    amorcer_continuite_historique(etat, noeuds)
    journaliser("diffusion.importance")
    scores, adj = importance(noeuds, aretes, evaluation, horloge["source_id"],
                             occupes)
    polarites, _horloge_moyenne = polarites_horloge_acteurs(noeuds, adj)
    energies_graphe = mettre_a_jour_energie_graphe(
        etat, horloge, scores, noeuds, adj, polarites)
    journaliser("diffusion.calendrier")
    disponibilites = calendrier(noeuds, aretes, evaluation,
                                 horloge["source_id"])
    for nid, score in scores.items():
        noeuds[nid]["importance_activation"] = score
    eligibles = mettre_a_jour_energies(
        etat, horloge, scores, energies_graphe,
        disponibilites, noeuds, occupes)
    journaliser("energie.calculee", acteurs=len(eligibles),
                maximum=round(eligibles[0][0], 3) if eligibles else 0)
    if args.acteur:
        eligibles = [x for x in eligibles if x[2] == args.acteur]
    etat["horloge"] = {k: v for k, v in horloge.items()
                       if k != "present_secondes"}
    if not eligibles:
        journaliser("cycle.sans_acteur")
        if not args.sec:
            ecrire_atomique(ETAT_BOUCLE, etat)
        return etat, False
    rotation = etat.setdefault("rotation_activation", {"tour": 1, "vus": []})
    vus_rotation = set(rotation.get("vus") or [])

    def selectionner(exclus_rotation):
        choix = []
        taches_selectionnees = set()
        for energie, score, pid, jauge in eligibles:
            if energie < ENERGIE_ACTIVATION_MIN:
                journaliser("selection.borne", acteur=pid,
                            energie=round(energie, 3),
                            seuil=ENERGIE_ACTIVATION_MIN)
                break
            if pid in exclus_rotation:
                journaliser("selection.rejetee", acteur=pid,
                            energie=round(energie, 3),
                            raison="deja_passe_dans_rotation",
                            tour=rotation.get("tour"))
                continue
            if acteur_en_repos(etat, pid, horloge["present_secondes"]):
                jusqua = ((etat.get("repos") or {}).get("acteurs") or {}).get(pid)
                journaliser("selection.rejetee", acteur=pid,
                            energie=round(energie, 3), raison="repos_acteur",
                            reprendre_a=jusqua)
                continue
            tache = choisir_tache(
                "pers:" + pid, noeuds, aretes, adj, energies_graphe,
                etat=etat, present=horloge["present_secondes"])
            if tache is None:
                journaliser("selection.rejetee", acteur=pid,
                            energie=round(energie, 3), raison="aucune_tache")
                continue
            energie_tache = energie_de_tache(tache, energies_graphe, energie)
            if energie_tache >= ENERGIE_MIN:
                if tache["id"] in taches_selectionnees:
                    journaliser("selection.rejetee", acteur=pid,
                                tache=tache["id"],
                                raison="tache_deja_selectionnee")
                    continue
                choix.append(
                    (energie, score, pid, jauge, tache, energie_tache))
                taches_selectionnees.add(tache["id"])
                if len(choix) >= capacite:
                    break
                continue
            journaliser("selection.rejetee", acteur=pid,
                        energie=round(energie, 3), tache=tache["id"],
                        energie_tache=round(energie_tache, 3),
                        raison="tache_sous_seuil")
        return choix

    selections = selectionner(vus_rotation)
    if not selections and vus_rotation:
        rotation["tour"] = int(rotation.get("tour") or 1) + 1
        rotation["vus"] = []
        vus_rotation.clear()
        journaliser("rotation.nouveau_tour", tour=rotation["tour"])
        selections = selectionner(vus_rotation)
    if not selections:
        journaliser("cycle.attente", raison="aucun couple acteur-tache energise")
        if not args.sec:
            ecrire_atomique(ETAT_BOUCLE, etat)
        return etat, 0

    lots = []
    for energie, score, pid, jauge, tache, energie_tache in selections:
        # La tâche attire et oriente ; l'énergie vient de la personne élue.
        budget = min(100, int(math.floor(energie)))
        budget_secondes = secondes_monde_pour_energie(budget)
        polarite = polarites.get("pers:" + pid) or {}
        lot = {
            "energie": energie, "score": score, "pid": pid,
            "jauge": jauge, "tache": tache,
            "energie_tache": energie_tache, "budget": budget,
        }
        lots.append(lot)
        journaliser("selection.elue", acteur=pid, energie=round(energie, 3),
                    tache=tache["id"], energie_tache=round(energie_tache, 3),
                    budget_energie=budget, budget_s=budget_secondes,
                    flux_horloge=polarite.get("mode"),
                    ecart_horloge_min=round(
                        polarite.get("ecart_minutes", 0.0), 3),
                    horloge_pj=polarite.get("horloge_pj"))
        journaliser("acteur.choisi", acteur=pid, energie=round(energie, 3),
                    importance=round(score, 6), budget=budget)
        journaliser("tache.choisie", id=tache["id"],
                    distance=tache["distance"], creee=tache["creee"],
                    energie=round(energie_tache, 3))
        print("ACTIVATION  %s  energie %.2f · budget %d (%.0f min)  importance %.3f" %
              (pid, energie, budget, budget_secondes / 60, score))
        print("  tache %s · distance %d · %s" %
              (tache["id"], tache["distance"], tache["quoi"][:100]))
        print("  front %s · +%.1fs depuis %s" %
              (horloge["front_id"], horloge["present_secondes"],
               horloge["source_id"]))

    rotation["vus"] = sorted(vus_rotation | {lot["pid"] for lot in lots})
    journaliser("rotation.acteurs_reserves", tour=rotation.get("tour"),
                acteurs=rotation["vus"])

    journaliser("selection.lot", nombre=len(lots), parallele=capacite)
    if args.sec:
        for lot in lots:
            appeler_acteur(
                lot["pid"], lot["tache"], lot["budget"], horloge, noeuds,
                args.modele, args.effort, args.minutes_appel, True,
                args.heartbeat, etat=etat)
        return etat, len(lots)

    for lot in lots:
        journaliser("energie.reservee", acteur=lot["pid"],
                    valeur=round(lot["energie"], 3), plafond=lot["budget"])
        lot["jauge"]["activations"] = int(
            lot["jauge"].get("activations") or 0) + 1
    ecrire_atomique(ETAT_BOUCLE, etat)

    resultats = {}
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(lots), thread_name_prefix="activation") as pool:
        futurs = {
            pool.submit(
                appeler_acteur, lot["pid"], lot["tache"], lot["budget"],
                horloge, noeuds, args.modele, args.effort,
                args.minutes_appel, False, args.heartbeat, etat): lot
            for lot in lots
        }
        for futur in concurrent.futures.as_completed(futurs):
            lot = futurs[futur]
            cle = (lot["pid"], lot["tache"]["id"])
            try:
                resultats[cle] = futur.result()
            except BaseException as e:
                lot["jauge"]["activations"] = max(
                    0, lot["jauge"]["activations"] - 1)
                rotation["vus"] = [x for x in rotation.get("vus") or []
                                   if x != lot["pid"]]
                journaliser("activation.annulee", acteur=lot["pid"],
                            raison=type(e).__name__,
                            erreur=_court(str(e), 400))

    reussies = 0
    for lot in lots:
        pid = lot["pid"]
        tache = lot["tache"]
        cle = (pid, tache["id"])
        if cle not in resultats:
            continue
        cible, depense, rapport = resultats[cle]
        energie = lot["energie"]
        score = lot["score"]
        budget = lot["budget"]
        jauge = lot["jauge"]
        restitue = round(budget - depense, 3)
        activites_rapport = (
            (rapport.get("activation") or {}).get("activites") or [])
        duree_monde = sum(
            int((a.get("temps") or {}).get("duree_s") or 0)
            for a in activites_rapport)
        reserves_noeuds = etat["graphe"]["noeuds"]
        acteur_nid = "pers:" + pid
        energie_acteur_apres = max(0.0, float(energie) - float(depense))
        reserves_noeuds[acteur_nid] = energie_acteur_apres
        jauge["energie"] = energie_acteur_apres
        jauge["disponible_a"] = round(
            float(horloge["present_secondes"]) + duree_monde, 3)
        journaliser("acteur.energie.debitee", acteur=pid,
                    avant=round(energie, 3), energie=depense,
                    duree_monde_s=duree_monde,
                    apres=round(energie_acteur_apres, 3))
        if restitue:
            journaliser("budget.inutilise", acteur=pid, montant=restitue,
                        budget=budget, utilise=depense)
        enregistrer_continuite(
            etat, pid, tache, rapport, horloge, cible, noeuds)
        entree = {
            "qui": pid, "tache": tache["id"], "budget": budget,
            "depense": depense, "restitue": restitue,
            "duree_monde_secondes": duree_monde,
            "energie_avant": round(energie, 3),
            "energie_apres": round(energie_acteur_apres, 3),
            "importance": round(score, 6), "front": horloge["front_id"],
            "present_secondes": round(horloge["present_secondes"], 3),
            "rapport": os.path.relpath(cible, RACINE).replace("\\", "/"),
            "termine_le": dt.datetime.now().astimezone().isoformat(),
        }
        etat.setdefault("historique", []).append(entree)
        journaliser("cycle.termine", acteur=pid, rapport=entree["rapport"])
        reussies += 1

    etat["historique"] = etat.get("historique", [])[-200:]
    ecrire_atomique(ETAT_BOUCLE, etat)
    journaliser("cycle.lot.termine", reussies=reussies,
                annulees=len(lots) - reussies)
    return etat, reussies


def prevoir_activations(limite):
    """Classement instantane de la physique, sans appel ni ecriture.

    L'ordre au-dela du premier reste conditionnel : une activation peut
    modifier le graphe, depenser moins que sa reserve ou durer assez longtemps
    pour recharger un acteur deja passe.
    """
    etat = lire_json(ETAT_BOUCLE, {"version": 1, "historique": []})
    horloge, occupes = horloge_directe(etat)
    noeuds, aretes, evaluation = charger_tissu()
    amorcer_continuite_historique(etat, noeuds)
    scores, adj = importance(noeuds, aretes, evaluation, horloge["source_id"],
                             occupes)
    polarites, _horloge_moyenne = polarites_horloge_acteurs(noeuds, adj)
    energies_graphe = mettre_a_jour_energie_graphe(
        etat, horloge, scores, noeuds, adj, polarites)
    disponibilites = calendrier(noeuds, aretes, evaluation,
                                 horloge["source_id"])
    for nid, score in scores.items():
        noeuds[nid]["importance_activation"] = score
    eligibles = mettre_a_jour_energies(
        etat, horloge, scores, energies_graphe,
        disponibilites, noeuds, occupes)
    resultat = []
    attentes = collections.Counter()
    # TOUT ACTEUR ACTIF PARAIT. On n'ecarte plus personne de la liste : un
    # homme sous le seuil, au repos ou sans tache energisee reste un homme
    # qu'on doit pouvoir voir et lancer a la main depuis l'admin. Le motif
    # d'attente l'accompagne au lieu de le faire disparaitre.
    for energie, score, pid, _jauge in eligibles:
        motifs = []
        if energie < ENERGIE_ACTIVATION_MIN:
            attentes["energie_sous_seuil"] += 1
            motifs.append("énergie sous le seuil")
        if acteur_en_repos(etat, pid, horloge["present_secondes"]):
            attentes["repos_acteur"] += 1
            motifs.append("au repos")
        tache = choisir_tache(
            "pers:" + pid, noeuds, aretes, adj, energies_graphe,
            etat=etat, present=horloge["present_secondes"])
        if tache is None:
            attentes["aucune_tache_disponible"] += 1
            motifs.append("aucune tâche")
            tache = {"id": "", "quoi": "rien à faire aujourd'hui",
                     "distance": 0, "creee": False}
        else:
            energie_tache = energie_de_tache(tache, energies_graphe, energie)
            if energie_tache < ENERGIE_MIN:
                attentes["tache_sous_seuil"] += 1
                motifs.append("tâche peu énergisée")
        budget_energie = min(100, int(math.floor(energie)))
        resultat.append({
            "rang": len(resultat) + 1,
            "qui": pid,
            "nom": (noeuds.get("pers:" + pid) or {}).get("quoi") or pid,
            "energie": round(energie, 3),
            "importance": round(score, 6),
            "budget": budget_energie,
            "duree_monde_secondes": secondes_monde_pour_energie(
                budget_energie),
            "flux_horloge": (polarites.get("pers:" + pid) or {}).get("mode"),
            "ecart_horloge_minutes": round(
                (polarites.get("pers:" + pid) or {}).get("ecart_minutes", 0.0), 3),
            "horloge_pj": (polarites.get("pers:" + pid) or {}).get("horloge_pj"),
            "tache_id": tache["id"],
            "tache": tache["quoi"],
            "distance": tache["distance"],
            "creee": tache["creee"],
            "pret": not motifs,
            "attente": " · ".join(motifs) or None,
        })
        if len(resultat) >= limite:
            break
    return {
        "calcule_le": dt.datetime.now().astimezone().isoformat(),
        "origine": horloge["source_id"],
        "front": horloge["front_id"],
        "present_secondes": round(horloge["present_secondes"], 3),
        "hypothese": ("classement instantane si aucun resultat ne modifie "
                       "le graphe, les disponibilites ou les energies"),
        "attente": dict(attentes),
        "previsions": resultat,
    }


def main():
    global PERSISTER_LOGS, AFFICHER_LOGS
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--une-fois", action="store_true",
                    help="un seul examen du front puis sortie")
    ap.add_argument("--sec", action="store_true",
                    help="selection et mission seulement, aucun appel ni ecriture")
    ap.add_argument("--acteur", help="borner la selection a cet acteur")
    ap.add_argument("--intervalle", type=float, default=5.0,
                    help="secondes entre deux examens sans activation")
    ap.add_argument("--modele", default="opus",
                    help="modele transmis au script d'appel")
    ap.add_argument("--effort", default="low",
                    help="effort de raisonnement transmis au CLI, ex. low")
    ap.add_argument("--minutes-appel", type=int, default=15,
                    help="timeout technique de l'appel (pas le budget fictionnel)")
    ap.add_argument("--max-activations", type=int, default=0,
                    help="0 = sans plafond")
    ap.add_argument("--heartbeat", type=float, default=5.0,
                    help="secondes entre deux logs quand le CLI est silencieux")
    ap.add_argument("--parallele", type=int, default=1,
                    help="nombre maximal d'activations simultanees")
    ap.add_argument("--prevoir", type=int, default=0, metavar="N",
                    help="rendre les N prochains candidats en JSON, sans ecriture")
    args = ap.parse_args()
    if (args.intervalle <= 0 or args.minutes_appel <= 0 or
            args.heartbeat <= 0 or args.parallele <= 0):
        ap.error("intervalle, minutes-appel, heartbeat et parallele "
                 "doivent etre positifs")
    if args.prevoir < 0:
        ap.error("prevoir doit etre positif")
    if args.prevoir:
        PERSISTER_LOGS = False
        AFFICHER_LOGS = False
        json.dump(prevoir_activations(args.prevoir), sys.stdout,
                  ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    PERSISTER_LOGS = not args.sec
    journaliser("boucle.demarrage", sec=args.sec, une_fois=args.une_fois,
                heartbeat_s=args.heartbeat, parallele=args.parallele)

    if args.sec:
        cycle(args)
        return 0
    faites = 0
    echecs_consecutifs = 0
    with VerrouBoucle():
        etat = None
        while True:
            try:
                if args.max_activations:
                    args.capacite_cycle = min(
                        args.parallele, args.max_activations - faites)
                else:
                    args.capacite_cycle = args.parallele
                etat, actives = cycle(args, etat)
            except KeyboardInterrupt:
                journaliser("boucle.arretee", raison="clavier")
                return 130
            except Exception as e:
                # Un cycle qui casse ne doit jamais eteindre la boucle : on
                # journalise, on souffle, et on repart au cycle suivant.
                echecs_consecutifs += 1
                journaliser("cycle.echoue", raison=type(e).__name__,
                            erreur=_court(str(e), 400),
                            consecutifs=echecs_consecutifs)
                # Mais une panne qui ne passe pas — disque plein, etat illisible —
                # ne se guerit pas en dormant : sans ce compteur, la boucle
                # tournait a vide toute la nuit en croyant travailler.
                if echecs_consecutifs >= ECHECS_CONSECUTIFS_MAX:
                    journaliser("boucle.arretee", raison="echecs_consecutifs",
                                seuil=ECHECS_CONSECUTIFS_MAX,
                                dernier=type(e).__name__)
                    return 1
                time.sleep(args.intervalle)
                continue
            echecs_consecutifs = 0
            faites += actives
            if args.une_fois or (args.max_activations and
                                 faites >= args.max_activations):
                return 0
            if not actives:
                time.sleep(args.intervalle)


if __name__ == "__main__":
    raise SystemExit(main())
