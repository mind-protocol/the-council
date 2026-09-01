# -*- coding: utf-8 -*-
"""LA PORTE du container 🧠 agents — depeche, parloir, affectation.

La regle (docs/organisation.md §2) : on n'entre dans un container que par sa
porte — `from agents.expose import ...`, jamais `import depecher`.
Ce fichier REEXPORTE ce que les importeurs consomment reellement aujourd'hui,
rien de plus.

Tant que le lot 2 n'a pas vide les commandes, importer cette porte execute
`affecter`, `parloir` et `depecher` — et, par leurs propres imports, les portes
`etat` et `temps`. C'est le comportement courant des importeurs actuels.
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
# Une seule porte vers les fournisseurs de CLI. Liee avant les lanceurs : ni
# la fiction ni les containers ne doivent savoir si Claude ou Codex repond.
from agents import runtime  # noqa: E402,F401
# Première couche des POST joueur : la présence physique route directement
# les paroles ; les gestes et la régie vont au MJ.
from agents import routeur_message  # noqa: E402,F401
from agents.routeur_message import main as routeur_message_main  # noqa: E402,F401
# Jump prépare un événement pour le MJ sans passer par le sélecteur ordinaire.
from agents import jump  # noqa: E402,F401
# Miroir des instructions Claude vers Codex. La matiere reste sous prompts/ ;
# la facade publique scripts/copier_claude_vers_agents.py passe par cette porte.
from agents.prompts import copier_claude_vers_agents  # noqa: E402,F401
from agents.prompts.copier_claude_vers_agents import main as copier_claude_vers_agents_main  # noqa: E402,F401
# Le vecu (habitant.md pas 6) : depouille un transcript -p et le depose dans
# fil/ — appele par le lanceur, jamais confie a un hook de fournisseur.
from agents import trace  # noqa: E402,F401 — lu par la facade scripts/vecu.py
# Pas 7 : les fils etat/parloir/ vers les canaux des chambres (une seule fois).
from agents import parloir_migration  # noqa: E402,F401 — lu par scripts/migrer_parloir.py
# La salle : ce qu'un habitant entend la ou il se tient. Lu par
# scene/flux.py au moment de la poussee — le seul endroit qui tienne a
# la fois la piece, la presence et le texte. Depend de `chambre`, lie
# juste au-dessus, et de rien d'autre.
from agents import salle  # noqa: E402,F401 — lu par scene/flux.py (le fil de salle)
# Descendue au lot 2 : le paquet agents/affectation/, plus la commande racine.
# Le nom `affecter` reste servi par la porte : c'est lui que la facade et les
# importeurs historiques demandent.
from agents import affectation  # noqa: E402,F401 — LE resolveur d'adresses ; lu par depecher, marche, tick
affecter = affectation
from agents.affectation import main as affecter_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : agents/parloir.py, plus la commande racine. Le
# hook-oreille est mort le 31.8.2026 : parloir n'est plus qu'un adressage
# (--dire entre habitants ; calls vers le MJ réservés au front joueur).
from agents import parloir  # noqa: E402,F401 — l'adressage de la parole
from agents.parloir import main as parloir_main  # noqa: E402,F401 — l'entree CLI de la facade
# Descendue au lot 2 : le paquet agents/depeche/, plus la commande racine.
from agents import depeche  # noqa: E402,F401 — relit cette porte : affecter deja lie
depecher = depeche  # l'ancien nom, que la facade publique demande
from agents.depeche import main as depecher_main  # noqa: E402,F401 — l'entree CLI de la facade
# Le reveil en CALL de l'unique MJ par le front joueur — session continue.
# Lie apres depeche : il relit agents.depeche.brief.
from agents import mj  # noqa: E402,F401 — lu par parloir et le serveur
from agents.mj import main as reveiller_main  # noqa: E402,F401
# Le pas 5 (habitant.md §4) : ecrire = reveiller — le billet au canal de la
# paire, puis le cast du destinataire. Lie apres depeche : il relit brief.
from agents import billet  # noqa: E402,F401 — lu par parloir (--dire vers un homme absent)
# Boucle d'activation pilotée par le graphe. Liée après depeche : son moteur
# réutilise la construction canonique des dossiers et les appels d'hommes.
from agents import activation  # noqa: E402,F401
boucle_activation = activation
from agents.activation import main as boucle_activation_main  # noqa: E402,F401
# Descendue au lot 2 : scripts/dossier.py -> agents/matiere.py (§7).
from agents import matiere  # noqa: E402,F401 — le dossier d'un sujet, rassemble
from agents.matiere import main as dossier_main  # noqa: E402,F401 — l'entree CLI de la facade

# Descendue le 31.8 : scripts/activite.py -> agents/activite.py — la loupe
# de debug des sessions de dev (qui a fait quoi, les appels, les refus).
from agents import activite  # noqa: E402,F401 — instrument de dev, hors du jeu
from agents.activite import main as activite_main  # noqa: E402,F401 — l entree CLI de la facade

# Descendue le 31.8 : scripts/reconcilier.py -> agents/reconcilier.py — le
# journal des affaires ecrites a la main, la ou aucune porte n emet.
from agents import reconcilier  # noqa: E402,F401 — les deux maisons des affaires
from agents.reconcilier import main as reconcilier_main  # noqa: E402,F401 — l entree CLI

# Descendue le 31.8 : remettre les cellules effacees par une reecriture,
# sans jamais ecraser ce qui est occupe.
from agents import rendre_cellules  # noqa: E402,F401
from agents.rendre_cellules import main as rendre_cellules_main  # noqa: E402,F401
