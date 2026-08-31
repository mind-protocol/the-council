# -*- coding: utf-8 -*-
"""Retire les 16 faux `main.creee` émis pendant l'amorçage du 31.8.2026.

Un CALL déjà en vol a réconcilié le dépôt entre l'ajout du lecteur des mains
et la pose de l'empreinte qui devait précisément amorcer ces documents sans
événement. Les identifiants ci-dessous bornent la réparation : aucune autre
ligne du journal ne peut être touchée.
"""
import io
import json
import os
import uuid

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JOURNAL = os.path.join(RACINE, "etat", "histoire", "affaires.jsonl")
IDS = {
    "0c6b38d0ae64402496e728ac92e17705", "e375f713c701431b8d2335b2ca9cf48e",
    "669afe72ae9c4d2284fdfd9226855eb2", "f412785d8e62411886ef0b3dcb04b42d",
    "6a02b48032c3453bb567c18e251f11cd", "39caaaeb822b4b2383f8cd23085d16b2",
    "9d16623b6bf445a2a5f24bf0c58a228b", "cdf50ac0059842fda4b5f3a5945d71e1",
    "ddacdbbc27374c389377ac14296fee45", "a1a6c73a577447cebc7d0be9760be780",
    "57af039162cd456cb828a2add50cdeb8", "29a47f10535b413f881339bf072130d4",
    "4f7c47b65ef94ea5a0162761fd6f971b", "1d5a1cd80c95438ba747bdb2671b10f2",
    "dd678c95285b44439a1c659622cdd9e8", "052140b8457543dab5ff3b6cdf013297",
}


def main():
    gardees, trouvees = [], set()
    with io.open(JOURNAL, encoding="utf-8") as f:
        for brute in f:
            objet = json.loads(brute)
            ident = objet.get("transition_id")
            if ident not in IDS:
                gardees.append(brute)
                continue
            if objet.get("quoi") != "main.creee" \
                    or objet.get("outil") != "runtime:codex" \
                    or objet.get("quand") != "2026-08-31T15:46:21":
                raise RuntimeError("la transition bornée ne correspond plus : %s" % ident)
            trouvees.add(ident)
    manque = IDS - trouvees
    if manque:
        raise RuntimeError("transitions d'amorçage absentes : %s" % sorted(manque))
    temporaire = JOURNAL + ".%s.tmp" % uuid.uuid4().hex
    with io.open(temporaire, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(gardees)
    os.replace(temporaire, JOURNAL)
    print("%d faux événements d'amorçage retirés" % len(trouvees))


if __name__ == "__main__":
    main()
