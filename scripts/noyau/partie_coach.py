# -*- coding: utf-8 -*-
"""partie_coach.py — le banc de touche (mj-partie.md §6.4), poussé aux sièges
de LA partie, et à eux seuls.

`append_flux.py --pour tous` envoyait le coach d'une partie dans le fil des
joueurs de l'autre : à deux parties ouvertes en même temps (le cas depuis le
6.9), l'audience est celle que `sieges` de etat/parties/<id>.json déclare —
l'union des sièges de tous les camps, comme `partie_ia.publier` le fait déjà
pour le mot d'une IA. Sans siège déclaré, on refuse et l'on ne pousse rien.
"""
import os
import subprocess
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from partie_greffe import RACINE  # noqa: E402
import partie_cartes  # noqa: E402


def sieges_de_la_partie(p):
    """L'union des sièges de tous les camps, dits par `sieges` de
    etat/parties/<id>.json — dans l'ordre des camps, sans doublon."""
    out = []
    for c in (partie_cartes.config(p).get("sieges") or {}).values():
        for s in (c if isinstance(c, list) else [c]):
            if s and s not in out:
                out.append(s)
    return out


def commandes_coach(p, fichier):
    """Les commandes `append_flux.py --fichier <json> --pour <siege>`, une par
    siège déclaré. Vide si la partie n'en déclare aucun."""
    plume = os.path.join(RACINE, "scripts", "append_flux.py")
    return [[sys.executable, plume, "--fichier", fichier, "--pour", s] for s in sieges_de_la_partie(p)]


def coach(p, fichier, voir=False):
    """Pousser le commentaire du banc de touche (mj-partie.md §6.4) aux sièges
    de CETTE partie, et à eux seuls. `--pour tous` envoyait le coach d'une
    partie dans le fil des joueurs de l'autre (C6, 7.9) : à deux parties
    ouvertes, l'audience est celle que la configuration déclare. Sans siège
    déclaré, on refuse et l'on ne pousse rien. `voir` imprime les commandes
    sans les lancer."""
    if not os.path.isfile(fichier):
        print("coach : fichier introuvable — %s" % fichier)
        return 2
    commandes = commandes_coach(p, fichier)
    if not commandes:
        nom = os.path.splitext(os.path.basename(p.chemin))[0]
        print("coach : aucun siège déclaré dans etat/parties/%s.json (`sieges`) — rien poussé. "
              "Déclare les sièges de chaque camp avant de pousser un commentaire." % nom)
        return 2
    code = 0
    for cmd in commandes:
        siege = cmd[-1]
        if voir:
            print("  " + " ".join(cmd[1:]))
            continue
        r = subprocess.run(cmd, cwd=RACINE, capture_output=True, timeout=60,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if r.returncode == 0:
            print("coach : poussé au fil de %s" % siege)
        else:
            code = 2
            print("coach : ÉCHEC au fil de %s : %s" % (siege, (r.stderr or r.stdout).decode("utf-8", "replace")[-300:]))
    return code
