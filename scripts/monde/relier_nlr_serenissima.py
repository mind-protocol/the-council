#!/usr/bin/env python3
"""Ouvrir une relation entre Nicolas Lester Reynolds et chaque Serenissima.

La relation vit dans les chambres : une fiche subjective de chaque cote, un
curseur de lecture par personne et un seul ``discussion.json`` canonique pour
la paire. L'ouverture ne pretend ni qu'ils se sont rencontres, ni qu'ils ont
deja une opinion l'un de l'autre.
"""

import argparse
import json
from pathlib import Path

from importer_relations_serenissima import citoyens


RACINE = Path(__file__).resolve().parents[2]
CHAMBRES = RACINE / "chambres"
NLR_ID = "nicolas-lester-reynolds"
NLR_NOM = "Nicolas Lester Reynolds"
DATE = "129.5.12"


def fiche(nom):
    return (
        "# %s — ce que j'en retiens\n\n"
        "*Canal ouvert le %s à Braavos pour permettre un premier contact. "
        "Je n'ai encore rien écrit de cette personne.*\n"
    ) % (nom, DATE)


def ecrire_absent(chemin, contenu, verifier):
    if chemin.exists():
        return False
    if verifier:
        raise ValueError("fichier absent : %s" % chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8", newline="\n")
    return True


def nombre_entrees(canal):
    if not canal.is_file():
        return 0
    donnees = json.loads(canal.read_text(encoding="utf-8-sig"))
    if not isinstance(donnees, dict) or not isinstance(donnees.get("entrees"), list):
        raise ValueError("canal invalide : %s" % canal)
    return len(donnees["entrees"])


def relier(verifier=False):
    personnes, _ = citoyens()
    nlr = CHAMBRES / NLR_ID
    if not nlr.is_dir():
        raise ValueError("chambre NLR absente : %s" % nlr)

    comptes = {"personnes": len(personnes), "fiches": 0, "agents": 0,
               "curseurs": 0, "canaux": 0, "canaux_repares": 0}
    for autre_id, personne in sorted(personnes.items()):
        autre = personne["dossier"]
        cote_nlr = nlr / "relations" / autre_id
        cote_autre = autre / "relations" / NLR_ID
        premier_id, second_id = sorted((NLR_ID, autre_id))
        premier = nlr if premier_id == NLR_ID else autre
        canal = premier / "relations" / second_id / "discussion.json"

        contenu_nlr = fiche(personne["nom"])
        contenu_autre = fiche(NLR_NOM)
        for base, contenu in ((cote_nlr, contenu_nlr),
                              (cote_autre, contenu_autre)):
            comptes["fiches"] += ecrire_absent(base / "claude.md", contenu,
                                                verifier)
            comptes["agents"] += ecrire_absent(base / "AGENTS.md", contenu,
                                                verifier)

        if not canal.exists():
            contenu = json.dumps(
                {"canal": [premier_id, second_id], "entrees": []},
                ensure_ascii=False,
                indent=1,
            ) + "\n"
            comptes["canaux"] += ecrire_absent(canal, contenu, verifier)
        else:
            donnees = json.loads(canal.read_text(encoding="utf-8-sig"))
            if donnees.get("canal") != [premier_id, second_id]:
                if verifier:
                    raise ValueError("identite de canal invalide : %s" % canal)
                # Certains premiers billets ont conserve l'underscore du nom
                # de dossier. L'etat et le routeur emploient le CitizenId
                # normalise ; on repare uniquement l'adresse, jamais l'histoire.
                donnees["canal"] = [premier_id, second_id]
                canal.write_text(
                    json.dumps(donnees, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
                comptes["canaux_repares"] += 1

        lu = str(nombre_entrees(canal))
        for base in (cote_nlr, cote_autre):
            comptes["curseurs"] += ecrire_absent(base / ".lu", lu, verifier)

    return comptes


def main():
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--verifier", action="store_true")
    args = analyseur.parse_args()
    comptes = relier(verifier=args.verifier)
    print(
        "OK %(personnes)d Serenissima ; fiches=%(fiches)d agents=%(agents)d "
        "canaux=%(canaux)d canaux_repares=%(canaux_repares)d "
        "curseurs=%(curseurs)d" % comptes
    )


if __name__ == "__main__":
    main()
