# -*- coding: utf-8 -*-
"""Scinde la bibliotheque et les mesures entre les maisons.

Sans ``--vraiment`` : imprime seulement la repartition. La migration refuse
un etat deja scinde et ne retire les anciennes sources qu'apres relecture de
toutes les nouvelles copies.
"""
import argparse
import io
import json
import os
import sys

import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from etat.expose import tables
import documents_maison


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ETAT = os.path.join(RACINE, "etat")
BOOKS = os.path.join(ETAT, "books")


def lire(chemin):
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


def index_par_id(liste):
    return {x.get("id"): x for x in liste if isinstance(x, dict) and x.get("id")}


def preparer():
    ordre = lire(os.path.join(BOOKS, "_ordre.json"))
    livres = [lire(os.path.join(BOOKS, ident + ".json")) for ident in ordre]
    maisons = index_par_id(lire(os.path.join(ETAT, "maisons.json")))
    personnages = index_par_id(lire(os.path.join(ETAT, "personnages.json")))
    lieux = index_par_id(lire(os.path.join(ETAT, "lieux.json")))
    boites = index_par_id(lire(os.path.join(ETAT, "boites.json")))
    mains_brut = lire(os.path.join(ETAT, "mains.json"))
    mains = mains_brut.get("mains") or [] if isinstance(mains_brut, dict) else mains_brut

    def controle(lieu_id):
        return (lieux.get(lieu_id) or {}).get("controle_id")

    def maison_personne(qui):
        p = personnages.get(qui) or {}
        return p.get("maison_id") or controle(p.get("lieu_id"))

    def maison_livre(livre):
        boite = boites.get(livre.get("boite")) or {}
        candidats = [
            livre.get("maison_id"),
            maison_personne(livre.get("acteur_id")),
            maison_personne(boite.get("acteur_id")),
            controle(livre.get("lieu_id")),
            controle(boite.get("lieu_id")),
        ]
        lecteurs = {maison_personne(q) for q in (livre.get("lecteurs") or [])}
        lecteurs.discard(None)
        if len(lecteurs) == 1:
            candidats.append(next(iter(lecteurs)))
        return next((x for x in candidats if x in maisons),
                    documents_maison.SANS_MAISON)

    def maison_main(main):
        p = main.get("porteur") or {}
        candidats = [main.get("maison_id")]
        if p.get("type") == "personnage":
            candidats.append(maison_personne(p.get("id")))
        elif p.get("type") == "lieu":
            candidats.append(controle(p.get("id")))
        candidats.append(controle(main.get("lieu_id")))
        return next((x for x in candidats if x in maisons),
                    documents_maison.SANS_MAISON)

    domaines = list(maisons) + [documents_maison.SANS_MAISON]
    livres_par = {mid: [] for mid in domaines}
    mains_par = {mid: [] for mid in domaines}
    for livre in livres:
        mid = maison_livre(livre)
        copie = dict(livre)
        copie["maison_id"] = mid
        livres_par[mid].append(copie)
    for main in mains:
        mid = maison_main(main)
        copie = dict(main)
        copie["maison_id"] = mid
        mains_par[mid].append(copie)
    return ordre, livres_par, mains_par


def appliquer(ordre, livres_par, mains_par):
    if any(os.path.isdir(documents_maison.dossier(ETAT, mid))
           for mid in livres_par):
        raise SystemExit("migration deja commencee : un dossier documents existe")

    for mid in livres_par:
        base = documents_maison.dossier_livres(ETAT, mid)
        os.makedirs(base, exist_ok=False)
        ids = [livre["id"] for livre in livres_par[mid]]
        tables.ecrire(os.path.join(base, "_ordre.json"), ids, indent=1)
        for livre in livres_par[mid]:
            tables.ecrire(os.path.join(base, livre["id"] + ".json"), livre, indent=1)
        tables.ecrire(os.path.join(documents_maison.dossier(ETAT, mid), "mains.json"), {
            "maison_id": mid, "mains": mains_par[mid]}, indent=1)

    # Relecture complete avant de retirer la source partagee.
    sources = documents_maison.sources_livres(ETAT)
    nouvelles_mains = documents_maison.charger_mains(ETAT)
    if set(sources) != set(ordre):
        raise RuntimeError("la copie des livres n'est pas complete")
    if len(nouvelles_mains) != sum(len(x) for x in mains_par.values()):
        raise RuntimeError("la copie des mains n'est pas complete")

    racine_verifiee = os.path.abspath(BOOKS)
    if os.path.commonpath([racine_verifiee, os.path.abspath(ETAT)]) != os.path.abspath(ETAT):
        raise RuntimeError("cible books hors de etat")
    tables.ecrire(os.path.join(BOOKS, "_ordre.json"), [], indent=1)
    for ident in ordre:
        cible = os.path.abspath(os.path.join(BOOKS, ident + ".json"))
        if os.path.commonpath([racine_verifiee, cible]) != racine_verifiee:
            raise RuntimeError("volume hors de books : %s" % ident)
        os.remove(cible)
    os.remove(os.path.join(ETAT, "mains.json"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vraiment", action="store_true")
    args = ap.parse_args()
    ordre, livres_par, mains_par = preparer()
    print("%d livres · %d mains" % (len(ordre), sum(len(x) for x in mains_par.values())))
    for mid in livres_par:
        print("%-28s %3d livres · %2d mains" %
              (mid, len(livres_par[mid]), len(mains_par[mid])))
    if not args.vraiment:
        print("simulation — relancer avec --vraiment")
        return
    appliquer(ordre, livres_par, mains_par)
    print("documents scindes par maison ; anciennes sources retirees")


if __name__ == "__main__":
    main()
