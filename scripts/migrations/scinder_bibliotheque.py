# -*- coding: utf-8 -*-
"""Transforme ``etat/books.json`` en un volume JSON par fichier.

Sans ``--vraiment``, ne fait qu'inspecter la source. À l'activation, le
manifeste est écrit en dernier : tant qu'il manque, tous les lecteurs gardent
le monolithe pour unique autorité.
"""
import argparse
import hashlib
import io
import json
import os
import shutil
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import bibliotheque
from etat.expose import tables  # LA PORTE de etat/


def lire_octets(chemin):
    # binaire a dessein : l'empreinte sha256 porte sur les octets, pas le JSON
    with open(chemin, "rb") as f:
        return f.read()


def ecrire_json(chemin, valeur):
    tables.ecrire(chemin, valeur, indent=1)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vraiment", action="store_true",
                   help="crée et active etat/books/")
    args = p.parse_args()

    etat = os.path.join(RACINE, "etat")
    monolithe = os.path.join(etat, "books.json")
    dossier = os.path.join(etat, "books")
    manifeste = os.path.join(dossier, bibliotheque.MANIFESTE)
    if os.path.isfile(manifeste):
        raise SystemExit("bibliothèque déjà scindée : %s" % manifeste)
    if os.path.exists(dossier):
        raise SystemExit("dossier books/ déjà présent sans manifeste — inspection manuelle requise")

    source = lire_octets(monolithe)
    livres = json.loads(source.decode("utf-8-sig"))
    ordre, par_id = bibliotheque._index(livres)
    empreinte = hashlib.sha256(source).hexdigest()
    print("%d volumes valides · sha256 %s" % (len(ordre), empreinte[:16]))
    if not args.vraiment:
        print("simulation — relancer avec --vraiment pour activer etat/books/")
        return

    preparation = dossier + ".en-preparation-%d" % os.getpid()
    os.makedirs(preparation)
    try:
        for ident in ordre:
            ecrire_json(os.path.join(preparation, ident + ".json"), par_id[ident])
        if lire_octets(monolithe) != source:
            raise RuntimeError("etat/books.json a changé pendant la copie — rien activé")
        os.replace(preparation, dossier)
        # Le manifeste est le seul commutateur d'autorité. Il vient en dernier.
        bibliotheque._ecrire_atomique(manifeste, ordre)
    except Exception:
        if os.path.isdir(preparation):
            shutil.rmtree(preparation)
        raise

    relus = bibliotheque.charger(etat)
    if relus != livres:
        raise RuntimeError("la relecture scindée diffère de la source")
    print("activée : etat/books/_ordre.json · %d volumes" % len(relus))


if __name__ == "__main__":
    main()
