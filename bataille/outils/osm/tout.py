# -*- coding: utf-8 -*-
"""La chaîne OSM entière, dans l'ordre : retirer, nettoyer, relief, composer, cuire, chemins, ombrage.

    python bataille/outils/osm/tout.py --nom gelibolu --id gallipoli --bbox 40.38,26.55,40.56,26.76 --ville scripts/ville/gallipoli.tissu.json
    python bataille/outils/osm/tout.py --nom gelibolu --id gallipoli --depuis 4 --ville scripts/ville/gallipoli.tissu.json
    python bataille/outils/osm/tout.py --nom gelibolu --id gallipoli --bbox ... --jusqua 3

Chaque étape est un script numéroté de ce dossier, lançable seul ; celui-ci ne
fait que les appeler dans l'ordre et s'arrêter à la première qui échoue.

LES BROUILLONS SONT RANGÉS PAR EMPRISE : `bataille/donnees/osm/<nom>/` (la
réponse Overpass, la couche nettoyée, le relief, les tuiles) — un cache que
l'étape 1 ne retire pas deux fois (--forcer) et que l'étape 3 réutilise, et le
point de reprise de `--depuis`. Les SORTIES sont ailleurs : `etat/villes/<id>.json`,
`etat/chemins.json`, `bataille/donnees/ville/<id>.*`.
"""
import argparse, os, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
MOTEUR = os.path.dirname(os.path.dirname(ICI))
RACINE = os.path.dirname(MOTEUR)
sys.path.insert(0, ICI)
from _travail import dossier_travail  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nom", required=True, help="nom de l'emprise OSM (brouillons dans bataille/donnees/osm/<nom>/)")
    ap.add_argument("--id", required=True, help="id de la ville de l'état (etat/villes/<id>.json)")
    ap.add_argument("--bbox", help="sud,ouest,nord,est — requis si l'emprise n'a pas encore été retirée")
    ap.add_argument("--depuis", type=int, default=1, help="première étape à jouer (1-7)")
    ap.add_argument("--jusqua", type=int, default=7, help="dernière étape à jouer (1-7)")
    ap.add_argument("--pas", default="1", help="mètres par case à la cuisson")
    ap.add_argument("--pente", default="0.18", help="seuil de pente des collines (tangente)")
    ap.add_argument("--ville", help="tissu d'une ville engendrée (scripts/ville/<x>.tissu.json) versé aux étapes 4 et 5")
    ap.add_argument("--forcer", action="store_true", help="retirer l'OSM même si le cache existe")
    a = ap.parse_args()

    travail = dossier_travail(a.nom)
    if a.depuis <= 1 and not a.bbox and not os.path.exists(os.path.join(travail, f"{a.nom}.osm.json")):
        sys.exit(f"pas de cache OSM dans {os.path.relpath(travail, RACINE)} : --bbox est requis")
    print(f"brouillons : {os.path.relpath(travail, RACINE)}", flush=True)

    etapes = [
        (1, "01_recuperer.py", ["--nom", a.nom, "--sortie", travail] + (["--bbox", a.bbox] if a.bbox else []) + (["--forcer"] if a.forcer else [])),
        (2, "02_nettoyer.py", ["--nom", a.nom, "--donnees", travail]),
        (3, "03_relief.py", ["--nom", a.nom, "--donnees", travail]),
        (4, "04_composer.py", ["--nom", a.nom, "--id", a.id, "--pente", a.pente, "--donnees", travail] + (["--ville", a.ville] if a.ville else [])),
        (5, "05_cuire.py", ["--id", a.id, "--pas", a.pas, "--donnees", travail] + (["--nom", a.nom, "--ville", a.ville] if a.ville else [])),
        (6, "06_chemins.py", ["--id", a.id]),
        (7, "07_ombrage.py", ["--nom", a.nom, "--id", a.id, "--donnees", travail]),
    ]
    for n, script, args in etapes:
        if n < a.depuis or n > a.jusqua:
            continue
        print(f"\n── {n}/7 {script}", flush=True)
        r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ICI, script)] + args, cwd=RACINE)
        if r.returncode != 0:
            sys.exit(f"étape {n} ({script}) a échoué : code {r.returncode}")
    print("\n✓ chaîne complète")


if __name__ == "__main__":
    main()
