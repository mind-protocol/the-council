# Compte, livre par livre et table par table, les lignes dont TOUTES les
# cellules sont vides — et celles qui ne gardent qu'une miette (un seul champ
# rempli), parce qu'une ligne a moitie vide ne se voit pas non plus.
import json, os, glob

BOOKS = os.path.join(os.path.dirname(__file__), "..", "..", "mj", "books")

for chemin in sorted(glob.glob(os.path.join(BOOKS, "*.json"))):
    d = json.load(open(chemin, encoding="utf-8"))
    print("==", os.path.basename(chemin))
    for t in d.get("tables", []):
        lignes = t.get("lignes", [])
        vides = 0
        miettes = 0
        for l in lignes:
            cs = [str(c).strip() for c in l.get("cellules", [])]
            pleines = [c for c in cs if c]
            if not pleines:
                vides += 1
            elif len(pleines) <= 1:
                miettes += 1
        etat = "OK"
        if vides == len(lignes) and lignes:
            etat = "CREUSE (toutes vides)"
        elif vides + miettes == len(lignes) and lignes:
            etat = "CREUSE (vides + miettes)"
        elif vides or miettes:
            etat = "PARTIELLE"
        print("   %-28s %2d lignes  vides=%d miettes=%d  %s"
              % (t.get("titre", "?"), len(lignes), vides, miettes, etat))
