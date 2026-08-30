# -*- coding: utf-8 -*-
"""LA PORTE du container 🧠 agents — depeche, activation, parloir, affectation.

La regle (docs/organisation.md §2) : on n'entre dans un container que par sa
porte — `from agents.expose import ...`, jamais `import depecher`.
Ce fichier REEXPORTE ce que les importeurs consomment reellement aujourd'hui,
rien de plus.

Tant que le lot 2 n'a pas vide les commandes, importer cette porte execute
`affecter`, `parloir`, `depecher` et `boucle_activation` — et, par leurs
propres imports, les portes `etat` et `temps`. C'est le comportement courant
des importeurs actuels, pas un effet nouveau.

L'ORDRE DES IMPORTS EST UNE CONTRAINTE : `depecher` et `boucle_activation`,
basculees sur cette porte, relisent `agents.expose` PENDANT son chargement ;
`affecter` (et `depecher` pour la boucle) doivent donc etre lies avant.
"""

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# Venue de scene/ (decision du 30, organisation.md §3 : les sieges sont la
# machinerie des acteurs, pas la peau) : s'asseoir, quitter, l'archive des tetes.
from agents import sieges  # noqa: E402,F401 — lu par la facade scripts/sieges.py
# Le modele habitant (docs/habitant.md §2) : le domicile d'un habitant —
# chemin, ouvrir (claude.md seede une fois), canal canonique, non-lus.
# Sans dependance interne : lie tot, sans contrainte d'ordre.
from agents import chambre  # noqa: E402,F401 — lu par depeche/mission (le montage --add-dir)
# Le vecu (habitant.md pas 6) : depouille un transcript -p et le depose dans
# fil/ — appele par le lanceur, jamais par hook (--restricted les ignore tous).
from agents import trace  # noqa: E402,F401 — lu par la facade scripts/vecu.py
# Descendue au lot 2 : le paquet agents/affectation/, plus la commande racine.
# Le nom `affecter` reste servi par la porte : c'est lui que la facade et les
# importeurs historiques demandent.
from agents import affectation  # noqa: E402,F401 — LE resolveur d'adresses ; lu par depecher, marche, tick
affecter = affectation
from agents.affectation import main as affecter_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : agents/parloir.py, plus la commande racine (les hooks
# PostToolUse tapent toujours scripts/parloir.py, la facade).
from agents import parloir  # noqa: E402,F401 — parler a un homme depeche ; lu par depecher
from agents.parloir import main as parloir_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : le paquet agents/depeche/, plus la commande racine.
from agents import depeche  # noqa: E402,F401 — relit cette porte : affecter deja lie
depecher = depeche  # l'ancien nom, que la facade et boucle_activation demandent
from agents.depeche import main as depecher_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : le paquet agents/activation/, plus la commande racine.
from agents import activation  # noqa: E402,F401 — relit cette porte : depecher deja lie
boucle_activation = activation  # l'ancien nom, que la facade et les bancs demandent
from agents.activation import main as boucle_activation_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : scripts/dossier.py -> agents/matiere.py (§7).
from agents import matiere  # noqa: E402,F401 — le dossier d'un sujet, rassemble
from agents.matiere import main as dossier_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : scripts/juger.py -> agents/jugement.py (§7). Le hook
# Stop tape toujours scripts/juger.py, la facade.
from agents import jugement  # noqa: E402,F401 — le juge separe, en claude -p
from agents.jugement import main as juger_main  # noqa: E402,F401 — l'entree CLI de la facade
