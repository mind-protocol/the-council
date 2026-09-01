"""Vue en lecture seule des affaires et des mains d'une maison.

La sortie est toujours reconstruite depuis le manifeste, les cahiers et
``mains.json``. Elle n'est donc jamais un registre concurrent.
"""

import argparse
import json
from pathlib import Path


RACINE = Path(__file__).resolve().parents[2]


def lire(chemin):
    with chemin.open(encoding="utf-8-sig") as source:
        return json.load(source)


def texte(cellule):
    return str(cellule or "").replace("**", "").strip()


def table(cahier, mot):
    mot = mot.casefold()
    return next((t for t in cahier.get("tables", [])
                 if mot in t.get("titre", "").casefold()), None)


def index_colonne(t, *mots):
    for i, colonne in enumerate(t.get("colonnes", [])):
        nom = colonne.casefold()
        if any(m.casefold() in nom for m in mots):
            return i
    return None


def cellule(ligne, index):
    cellules = ligne.get("cellules", [])
    return texte(cellules[index]) if index is not None and index < len(cellules) else "absent"


def ouverture(cahier, champ):
    t = table(cahier, "ouverture")
    if not t:
        return "absent"
    for ligne in t.get("lignes", []):
        cellules = ligne.get("cellules", [])
        if cellules and champ.casefold() in texte(cellules[0]).casefold():
            return texte(cellules[1]) if len(cellules) > 1 and texte(cellules[1]) else "absent"
    return "absent"


def cartographie(maison_id):
    base = RACINE / "etat" / "maisons" / maison_id / "documents"
    livres = base / "books"
    ordre = lire(livres / "_ordre.json")
    mains_doc = lire(base / "mains.json")
    mains = {}
    for main in mains_doc.get("mains", []):
        affaire = main.get("affaire_id") or main.get("livre_id") or main.get("affaire")
        if affaire:
            mains.setdefault(affaire, []).append(main)

    resultat = []
    for identifiant in ordre:
        cahier = lire(livres / (identifiant + ".json"))
        cibles = table(cahier, "états cibles")
        actions = table(cahier, "actions")
        lignes_actions = []
        if actions:
            numero = index_colonne(actions, "n°")
            qui = index_colonne(actions, "qui")
            office = index_colonne(actions, "office", "rôle exercé")
            depend = index_colonne(actions, "dépend")
            etat = index_colonne(actions, "état")
            for ligne in actions.get("lignes", []):
                lignes_actions.append({
                    "numero": cellule(ligne, numero),
                    "titulaire": cellule(ligne, qui),
                    "office": cellule(ligne, office),
                    "depend_de": cellule(ligne, depend),
                    "etat": cellule(ligne, etat),
                })

        main_cahier = cahier.get("tenu_par") or "absent"
        office_cahier = cahier.get("office") or "absent"
        mains_affaire = mains.get(identifiant, [])
        resultat.append({
            "affaire": identifiant,
            "titre": cahier.get("titre") or "absent",
            "objet": ouverture(cahier, "objet"),
            "etats_cibles": [cellule(l, 0) for l in cibles.get("lignes", [])] if cibles else [],
            "titulaire_cahier": main_cahier,
            "office_cahier": office_cahier,
            "mains_mesurees": mains_affaire,
            "actions": lignes_actions,
            "dependances_actions": sorted({a["depend_de"] for a in lignes_actions
                                            if a["depend_de"] not in ("absent", "", "—")}),
        })
    return {"maison_id": maison_id, "source": "vue dérivée à la lecture", "affaires": resultat}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--maison", default="maison-serenissima")
    args = parser.parse_args()
    print(json.dumps(cartographie(args.maison), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
