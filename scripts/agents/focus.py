# -*- coding: utf-8 -*-
"""FOCUS — la veille des zones : les journees d'hommes partent sur les
etats cibles les plus charges du tissu.

NE LE 31.8, corrige dans l'heure : la premiere passe reveillait les
NARRATEURS en leur demandant de depecher — le dev a tranche : « l'idee
c'est de lancer des hommes sur leurs journees plutot ». La couche
narrateur saute ; la boucle depeche DIRECTEMENT (depecher.py --cast), et
la mission du jour porte le focus.

La matiere qui decide est le graphe lui-meme : les reserves d'energie des
noeuds `etat_cible` (overlay etat/activations/boucle.json), routees vers
les zones par les PERSONNES du tissu — a distance <= 3 du noeud,
ponderees 1/distance. AUCUNE table d'adresses plan->zone : le tissu
suffit. Par zone servie : l'etat cible ou elle pese le plus, et ses
hommes ranges par (distance au fil, reserve d'energie) — `--hommes N`
en depeche N par zone (defaut 1).

CADENCE par homme (marqueur en chambre, 60 min reelles) : une journee en
cast vit sans nous, on ne re-depeche pas un homme dont la journee court.

A blanc par defaut : tout se montre, rien ne part. `--vraiment` envoie.
"""
import argparse
import collections
import io
import json
import os
import subprocess
import sys
import time

from agents import chambre
from agents import zone
from agents.depeche.brief import RACINE

TISSU = os.path.join(RACINE, "etat", "tissu")
ETAT_BOUCLE = os.path.join(RACINE, "etat", "activations", "boucle.json")

PROFONDEUR_ROUTAGE = 3      # distance max noeud -> personne dans le tissu
PROFONDEUR_AUTOUR = 2       # distance max pour les verrous/clefs du brief
CADENCE_FOCUS_MINUTES = 60  # minutes REELLES entre deux veilles d'un meme narrateur
MARQUEUR_FOCUS = ".derniere-veille-focus"


def _lire_json(chemin, defaut):
    try:
        return json.load(io.open(chemin, encoding="utf-8"))
    except (IOError, OSError, ValueError):
        return defaut


def charger_graphe():
    """Le tissu (noeuds, adjacence) et les reserves d'energie de l'overlay."""
    noeuds = _lire_json(os.path.join(TISSU, "noeuds.json"), {})
    adj = collections.defaultdict(set)
    try:
        with io.open(os.path.join(TISSU, "aretes.jsonl"), encoding="utf-8") as f:
            for ligne in f:
                if not ligne.strip():
                    continue
                a = json.loads(ligne)
                if a.get("flou") or a.get("virtuel"):
                    continue
                d, v = a.get("de"), a.get("vers")
                if d in noeuds and v in noeuds and d != v:
                    adj[d].add(v)
                    adj[v].add(d)
    except (IOError, OSError):
        pass
    boucle = _lire_json(ETAT_BOUCLE, {})
    reserves = dict(((boucle.get("graphe") or {}).get("noeuds") or {}))
    # Un etat cible garde sa reserve brute : c'est elle qui choisit le chemin
    # critique. Pour les hommes seulement, l'ordre de depart suit l'energie
    # effective deja calculee par la boucle (calcul recent + avance fiction).
    for pid, fiche in (boucle.get("acteurs") or {}).items():
        if isinstance(fiche, dict) and fiche.get("energie") is not None:
            reserves["pers:" + pid] = float(fiche["energie"])
    return noeuds, adj, reserves


def etats_cibles_charges(noeuds, reserves, n):
    """Les n noeuds etat_cible les plus charges en energie."""
    rangs = sorted(((float(reserves[nid]), nid) for nid, x in noeuds.items()
                    if x.get("genre") == "etat_cible" and nid in reserves),
                   key=lambda t: -t[0])
    return rangs[:n]


def _voisinage(nid, adj, profondeur):
    """{noeud: distance} jusqu'a `profondeur`, sans le noeud lui-meme."""
    vus, front, dist = {nid}, {nid}, {}
    for d in range(1, profondeur + 1):
        front = {v for f in front for v in adj[f]} - vus
        vus |= front
        for v in front:
            dist[v] = d
    return dist


def routage(nid, noeuds, adj, reserves):
    """Poids par ville pour un noeud : personnes actives a distance <= 3,
    ponderees 1/distance. Rend (Counter ville->poids, {ville: [hommes]}),
    les hommes ranges par (distance au fil, reserve d'energie) — l'ordre
    dans lequel on les depeche."""
    poids = collections.Counter()
    bruts = collections.defaultdict(list)
    for v, d in _voisinage(nid, adj, PROFONDEUR_ROUTAGE).items():
        x = noeuds.get(v) or {}
        if x.get("genre") != "personne" or x.get("etat") != "actif":
            continue
        ville = x.get("lieu_id")
        if not ville or x.get("condition") in ("prisonnier", "otage"):
            continue
        pid = v[5:] if v.startswith("pers:") else v
        poids[ville] += 1.0 / d
        bruts[ville].append((d, -float(reserves.get(v, 0.0)), pid))
    hommes = {ville: [pid for _, _, pid in sorted(rangs)]
              for ville, rangs in bruts.items()}
    return poids, hommes


def autour(nid, noeuds, adj, reserves, n=3):
    """Les verrous et clefs les plus charges a distance <= 2 de l'etat cible."""
    proches = []
    for v in _voisinage(nid, adj, PROFONDEUR_AUTOUR):
        x = noeuds.get(v) or {}
        if x.get("genre") in ("verrou", "clef") and v in reserves:
            proches.append((float(reserves[v]), v, x))
    proches.sort(key=lambda t: -t[0])
    return proches[:n]


def assignations(top=5):
    """Route chaque narrateur vers SON etat cible du top.

    Pour chaque ville touchee par un noeud du top, le narrateur est
    `zone.arbitre_de(<un homme de la ville>)` — la seule fabrique, joueur
    absorbe compris. Un narrateur tire l'etat cible ou SA ville pese le
    plus (energie x poids) ; une ville sans poids ce tour reste en silence.
    """
    noeuds, adj, reserves = charger_graphe()
    cibles = etats_cibles_charges(noeuds, reserves, top)
    meilleurs = {}  # mj -> (score, energie, nid, noeud, hommes_de_sa_ville)
    for energie, nid in cibles:
        poids, hommes = routage(nid, noeuds, adj, reserves)
        for ville, p in poids.items():
            try:
                mj = zone.arbitre_de(hommes[ville][0])
            except SystemExit:
                continue  # ville dont l'id ne fait pas une zone : on passe
            score = energie * p
            if score > meilleurs.get(mj, (0.0,))[0]:
                meilleurs[mj] = (score, energie, nid, noeuds[nid],
                                 hommes[ville])
    return meilleurs, noeuds, adj, reserves


def mission_de_focus(nid, noeud, noeuds, adj, reserves):
    """La consigne du jour d'un homme : le fil, dans les mots du monde."""
    lignes = [
        u"Le fil le plus charge de ton camp aujourd'hui : « %s » (%s)."
        % ((noeud.get("quoi") or u"").strip(), noeud.get("ou") or u"?"),
    ]
    charges = autour(nid, noeuds, adj, reserves)
    if charges:
        lignes.append(u"Ce qui le tient ou le debloque :")
        for e, vid, x in charges:
            lignes.append(u"  - %s : « %s »"
                          % (x.get("genre"), (x.get("quoi") or u"").strip()))
    lignes.append(u"Avance CE fil aujourd'hui, de ta place et avec tes "
                  u"moyens — le reste de ta journee suit.")
    return u"\n".join(lignes)


def _journee_recente(pid):
    chemin = os.path.join(chambre.chemin(pid), MARQUEUR_FOCUS)
    try:
        age_min = (time.time() - os.path.getmtime(chemin)) / 60.0
    except OSError:
        return None
    return age_min if age_min < CADENCE_FOCUS_MINUTES else None


def _marquer_journee(pid):
    try:
        io.open(os.path.join(chambre.chemin(pid), MARQUEUR_FOCUS),
                "w", encoding="utf-8").write(str(time.time()))
    except OSError:
        pass  # un marqueur qui manque ne vaut pas une journee perdue


def _depecher_en_cast(pid, mission):
    """`depecher.py --qui pid --mission ... --cast` — la commande canonique,
    en sous-processus comme de la main du dev (CREATE_NO_WINDOW : le spam
    de terminaux du 31.8)."""
    sans_fenetre = ({"creationflags": 0x08000000} if os.name == "nt" else {})
    r = subprocess.run(
        [sys.executable, os.path.join(RACINE, "scripts", "depecher.py"),
         "--qui", pid, "--mission", mission, "--cast"],
        cwd=RACINE, capture_output=True, text=True,
        encoding="utf-8", errors="replace", **sans_fenetre)
    if r.returncode != 0:
        print(u"  DEPECHE EN ECHEC (%s) : %s"
              % (pid, (r.stderr or r.stdout or u"").strip()[-300:]))
        return False
    return True


def veille(top=5, vraiment=False, forcer=False, seule=None, par_zone=1):
    """Une passe : calcule les focus, depeche les journees dues. Rend le
    nombre de journees parties (0 a blanc). `seule` borne a UNE zone,
    `par_zone` borne le nombre d'hommes depeches par zone — le lancement
    graduel : un homme, on observe, puis les autres."""
    meilleurs, noeuds, adj, reserves = assignations(top)
    # Le focus est une source de NOUVELLES journees automatiques : il respecte
    # les deux portes. --forcer reste le geste explicite qui les franchit.
    from agents.activation.fatigue import (
        amorcer_fatigue_historique, capacite_acteur, capacite_zone,
        mettre_a_jour_porte)
    etat_activation = _lire_json(
        ETAT_BOUCLE, {"version": 1, "historique": []})
    amorcer_fatigue_historique(etat_activation)
    if seule:
        seule = zone.zone_de(seule)
        if seule not in meilleurs:
            print(u"%s n'a aucun focus ce tour (zones servies : %s)"
                  % (seule, u", ".join(sorted(meilleurs)) or u"aucune"))
            return 0
        meilleurs = {seule: meilleurs[seule]}
    partis = 0
    for mj in sorted(meilleurs):
        score, energie, nid, noeud, hommes = meilleurs[mj]
        print(u"%-18s <- [%s] %.1f — hommes du fil : %s"
              % (mj, nid, energie, u", ".join(hommes[:6])))
        mission = mission_de_focus(nid, noeud, noeuds, adj, reserves)
        for pid in hommes[:max(1, par_zone)]:
            cap_homme, _charge_homme = capacite_acteur(etat_activation, pid)
            homme_ouvert = mettre_a_jour_porte(
                etat_activation, "acteurs", pid, cap_homme)
            cap_mj, _charge_mj, _comptes = capacite_zone(
                etat_activation, mj)
            mj_ouvert = mettre_a_jour_porte(
                etat_activation, "zones", mj, cap_mj)
            if not forcer and (not homme_ouvert or not mj_ouvert):
                print(u"  %s : capacité fermée (homme %.0f %%, MJ %.0f %%), silence"
                      % (pid, cap_homme * 100, cap_mj * 100))
                continue
            age = None if forcer else _journee_recente(pid)
            if not vraiment:
                print(u"  (a blanc) %s partirait avec :" % pid)
                print(u"\n".join(u"    | " + l for l in mission.split(u"\n")))
                continue
            if age is not None:
                print(u"  %s : journee il y a %d min, silence" % (pid, age))
                continue
            if _depecher_en_cast(pid, mission):
                _marquer_journee(pid)
                partis += 1
                print(u"  %s : journee partie en cast" % pid)
    if not meilleurs:
        print("aucun etat cible charge ne touche une zone habitee.")
    return partis


def main():
    ap = argparse.ArgumentParser(
        description="la veille des zones : un etat cible charge par narrateur")
    ap.add_argument("--top", type=int, default=5,
                    help="profondeur du classement des etats cibles (defaut 5)")
    ap.add_argument("--vraiment", action="store_true",
                    help="reveiller pour de bon (sans quoi : a blanc)")
    ap.add_argument("--intervalle", type=float, default=0,
                    help="minutes reelles entre deux passes (0 = une passe)")
    ap.add_argument("--forcer", action="store_true",
                    help="ignorer la cadence de veille (marqueur en chambre)")
    ap.add_argument("--zone", default=None, metavar="mj-sombreval",
                    help="borner la passe a cette seule zone (id ou ville)")
    ap.add_argument("--hommes", type=int, default=1,
                    help="journees depechees par zone et par passe (defaut 1)")
    a = ap.parse_args()
    if a.top <= 0:
        ap.error("--top doit etre positif")
    if a.intervalle and not a.vraiment:
        ap.error("une boucle a blanc ne montre rien de neuf : --vraiment, "
                 "ou une passe seche sans --intervalle")
    while True:
        veille(a.top, a.vraiment, a.forcer, a.zone, a.hommes)
        if not a.intervalle:
            return 0
        time.sleep(a.intervalle * 60)
