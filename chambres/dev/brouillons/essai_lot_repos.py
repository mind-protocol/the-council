# -*- coding: utf-8 -*-
"""LA RECETTE ENTIERE, pas seulement le validateur : on prend le VRAI lot que
mj-reposdesfreux tient en attente depuis le 129.4.3, on lui retire le champ
`echelle` (supprime du schema), et on le passe a appliquer.py A BLANC.

Pourquoi jusqu'ici et pas au validateur : le validateur, appele seul, disait
deja oui — et la ligne de rapport de val_plan.py l.150 levait KeyError APRES,
sur une tete validee. Un essai qui s'arrete au verdict ne voit pas ca.
"""
import io
import json
import os
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
SOURCE = os.path.join(RACINE, "chambres", "mj-reposdesfreux", "brouillons",
                      "a-poser-quand-la-porte-accepte-une-tete.json")
CIBLE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "_essai-lot-repos-sans-echelle.json")

lot = json.load(io.open(SOURCE, encoding="utf-8"))
retires = 0
for m in lot["mutations_proposees"]:
    v = m.get("valeur")
    if isinstance(v, dict) and "echelle" in v:
        del v["echelle"]
        retires += 1
lot["_essai"] = ("copie de travail du dev, 129.4.4 : %d champs `echelle` "
                 "retires. Ce fichier n'est PAS au staging." % retires)
with io.open(CIBLE, "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(lot, ensure_ascii=False, indent=2))
print("champs `echelle` retires du lot : %d" % retires)
print()

r = subprocess.run([sys.executable, os.path.join(RACINE, "scripts",
                                                 "appliquer.py"), CIBLE],
                   cwd=RACINE, capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
print("code de sortie :", r.returncode)
print(r.stdout[-3000:])
if r.stderr.strip():
    print("--- stderr ---")
    print(r.stderr[-2000:])
