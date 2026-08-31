# -*- coding: utf-8 -*-
"""Copie chaque CLAUDE.md du depot dans son AGENTS.md frere.

Le contenu est copie octet pour octet. Une cible identique n'est pas reecrite ;
une cible differente, y compris le AGENTS.md racine historique, est remplacee.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile


RACINE = Path(__file__).resolve().parents[3]
DOSSIERS_IGNORES = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build",
}


def sources_de(racine: Path):
    """Rend les CLAUDE.md du depot, dans un ordre stable."""
    trouves = []
    for dossier, sous_dossiers, fichiers in os.walk(racine, followlinks=False):
        sous_dossiers[:] = sorted(
            d for d in sous_dossiers
            if d.casefold() not in DOSSIERS_IGNORES
        )
        for nom in fichiers:
            if nom.casefold() == "claude.md":
                trouves.append(Path(dossier) / nom)
    return sorted(trouves, key=lambda p: str(p.relative_to(racine)).casefold())


def _remplacer(cible: Path, contenu: bytes):
    """Pose une cible complete, sans fenetre ou elle serait tronquee."""
    temporaire = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="wb", dir=cible.parent, prefix=".AGENTS.", suffix=".tmp",
                delete=False) as flux:
            temporaire = Path(flux.name)
            flux.write(contenu)
            flux.flush()
            os.fsync(flux.fileno())
        os.replace(temporaire, cible)
    finally:
        if temporaire is not None and temporaire.exists():
            temporaire.unlink()


def synchroniser(racine=RACINE, verifier=False):
    """Synchronise les miroirs et rend un compte exploitable par les bancs."""
    racine = Path(racine).resolve()
    if not racine.is_dir():
        raise ValueError("racine introuvable : %s" % racine)

    copies = []
    identiques = []
    divergents = []
    for source in sources_de(racine):
        cible = source.with_name("AGENTS.md")
        contenu = source.read_bytes()
        actuel = cible.read_bytes() if cible.is_file() else None
        if actuel == contenu:
            identiques.append(cible)
            continue
        divergents.append(cible)
        if not verifier:
            _remplacer(cible, contenu)
            copies.append(cible)

    return {
        "racine": racine,
        "sources": len(copies) + len(identiques) if not verifier
                   else len(divergents) + len(identiques),
        "copies": copies,
        "identiques": identiques,
        "divergents": divergents,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--racine", type=Path, default=RACINE,
                    help="depot a parcourir (defaut : la racine courante du projet)")
    ap.add_argument("--verifier", action="store_true",
                    help="n'ecrit rien et sort en 1 si un miroir diverge")
    a = ap.parse_args(argv)
    try:
        compte = synchroniser(a.racine, verifier=a.verifier)
    except (OSError, ValueError) as erreur:
        ap.exit(2, "erreur : %s\n" % erreur)

    if a.verifier:
        for chemin in compte["divergents"]:
            print("DESYNCHRONISE %s" % chemin.relative_to(compte["racine"]))
        print("%d CLAUDE.md · %d miroir(s) desynchronise(s)" % (
            compte["sources"], len(compte["divergents"])))
        return 1 if compte["divergents"] else 0

    print("%d CLAUDE.md · %d AGENTS.md copie(s) · %d deja identique(s)" % (
        compte["sources"], len(compte["copies"]), len(compte["identiques"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
