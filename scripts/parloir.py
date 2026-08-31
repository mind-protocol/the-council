# -*- coding: utf-8 -*-
"""PARLOIR — l'adressage de la parole.

LE HOOK-OREILLE EST MORT LE 31.8.2026 : plus personne n'entend en cours de
session. Une parole qui t'arrive est un BILLET au canal de la paire, servi en
percept au prochain reveil — et le geste d'ecrire est le reveilleur.

Usage :
    python scripts/parloir.py --dire --de mj --a le-sanglier "Reviens au quai"
    python scripts/parloir.py --tenter --de gerardys --a mj "je pars sur mon cheval"
    python scripts/parloir.py --dire --de mj --a tous "On ouvre la salle"
    python scripts/parloir.py --fils                      (les fils restants)

CE FICHIER EST UNE FACADE (docs/organisation.md §2) : la matiere vit dans le
container agents/, module parloir.py. Le chemin est gele — les manuels et
les missions archivees le citent tel quel.
"""
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# LA PORTE, jamais un module direct (docs/organisation.md §2).
from agents.expose import parloir as _parloir  # noqa: E402
from agents.expose import parloir_main as main  # noqa: E402,F401

nom_du_fil = _parloir.nom_du_fil
fils = _parloir.fils
TOUS = _parloir.TOUS

if __name__ == "__main__":
    main()
