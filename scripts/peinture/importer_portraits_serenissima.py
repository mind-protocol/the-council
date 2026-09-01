#!/usr/bin/env python3
"""Restaurer les portraits Serenissima encore présents dans l'histoire Git.

Les JPG historiques restent dans leur dépôt d'origine. Le Conseil n'en garde
qu'un médaillon SVG léger, avec l'image recadrée et embarquée en WebP, au format
déjà servi par ``/portraits/<id>.svg``.
"""

import argparse
import csv
import io
import json
import re
import shutil
import subprocess
from pathlib import Path

import medaillons


RACINE = Path(__file__).resolve().parents[2]
CSV = RACINE / "import" / "serenissima" / "CITIZENS-Grid view.csv"
CIBLE = RACINE / "ecrans" / "portraits"
ARCHIVE = CIBLE / "archive"
COMMIT = "f3dee54a03910a1173842ef2b03d45e67b0ebb63"
DOSSIER_GIT = "public/images/citizens"


def slug(texte):
    return re.sub(r"[^a-z0-9]+", "-", str(texte).lower()).strip("-")


def git(source, *arguments):
    return subprocess.check_output(["git", "-C", str(source), *arguments])


def portraits_historiques(source):
    noms = git(source, "ls-tree", "-r", "--name-only", COMMIT, "--", DOSSIER_GIT)
    chemins = noms.decode("utf-8", errors="strict").splitlines()
    return {
        Path(chemin).stem.casefold(): chemin
        for chemin in chemins
        if Path(chemin).suffix.casefold() in {".jpg", ".jpeg", ".png", ".webp"}
    }


def personnages():
    gens = json.loads((RACINE / "etat" / "personnages.json").read_text(encoding="utf-8-sig"))
    return {p["id"]: p for p in gens if isinstance(p, dict) and p.get("id")}


def importer(source, verifier=False):
    images = portraits_historiques(source)
    gens = personnages()
    with CSV.open(encoding="utf-8-sig", newline="") as flux:
        citoyens = list(csv.DictReader(flux))

    rapport = {"citoyens": len(citoyens), "trouves": 0, "importes": 0,
               "deja_peints": 0, "manquants": []}
    for citoyen in citoyens:
        pid = slug(citoyen.get("CitizenId"))
        username = str(citoyen.get("Username") or "").strip()
        chemin_git = images.get(username.casefold())
        if not chemin_git:
            rapport["manquants"].append(pid)
            continue
        rapport["trouves"] += 1
        if pid not in gens:
            raise ValueError("citoyen historique absent de l'état : %s" % pid)
        sortie = CIBLE / (pid + ".svg")
        if sortie.is_file() and b"data:image" in sortie.read_bytes():
            rapport["deja_peints"] += 1
            continue
        if verifier:
            raise ValueError("médaillon Serenissima absent : %s" % sortie)

        brut = git(source, "show", "%s:%s" % (COMMIT, chemin_git))
        webp = medaillons.medaillon(io.BytesIO(brut))
        contenu = medaillons.svg(pid, gens[pid].get("nom", pid), webp)
        if sortie.is_file():
            ARCHIVE.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sortie, ARCHIVE / sortie.name)
        sortie.write_text(contenu, encoding="utf-8", newline="\n")
        rapport["importes"] += 1
    return rapport


def main():
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--source", type=Path,
                           default=Path(r"C:\Users\reyno\serenissima"))
    analyseur.add_argument("--verifier", action="store_true")
    args = analyseur.parse_args()
    rapport = importer(args.source, verifier=args.verifier)
    print("OK : %(trouves)d/%(citoyens)d portraits historiques ; "
          "importés=%(importes)d déjà_peints=%(deja_peints)d manquants=%(reste)d" % {
              **rapport, "reste": len(rapport["manquants"]),
          })
    if rapport["manquants"]:
        print("Sans portrait historique : " + ", ".join(rapport["manquants"]))


if __name__ == "__main__":
    main()
