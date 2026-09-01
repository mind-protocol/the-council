# -*- coding: utf-8 -*-
"""Regroupe une fois les citoyens de Serenissima autour de neuf affaires.

La position courante vit dans ``etat/corps.json``.  Le script ne touche ni
aux paroles, ni aux affaires, ni aux scores de relation : il utilise les
relations historiques actives de confiance >= 75 comme poids de proximité,
puis les descriptions des citoyens pour départager les places restantes.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from pathlib import Path


RACINE = Path(__file__).resolve().parents[2]
CORPS = RACINE / "etat" / "corps.json"
PERSONNAGES = RACINE / "etat" / "personnages.json"
CITOYENS = RACINE / "import" / "serenissima" / "CITIZENS-Grid view.csv"
RELATIONS = RACINE / "import" / "serenissima" / "RELATIONSHIPS-Grid view.csv"


def identifiant(texte: str) -> str:
    return texte.strip().lower().replace("_", "-")


CLUSTERS = [
    {
        "nom": "compute-recuperable",
        "usage": "braavos-officine",
        "centre": (4568.60, 2150.27, 124.0),
        "noyaux": {"system-diagnostician"},
        "mots": {"compute", "system", "diagnostic", "code", "technical", "engineer", "efficiency"},
    },
    {
        "nom": "construction-ville",
        "usage": "braavos-bourg",
        "centre": (4835.21, 1871.78, 12.0),
        "noyaux": {"urban-visionary"},
        "mots": {"urban", "city", "builder", "construction", "land", "architect", "housing"},
    },
    {
        "nom": "services-infrastructure",
        "usage": "braavos-forge",
        "centre": (4435.95, 2063.32, 124.0),
        "noyaux": {"technomedici", "levant-trader"},
        "mots": {"infrastructure", "service", "technology", "engineer", "craft", "forge", "logistic"},
    },
    {
        "nom": "production-culturelle",
        "usage": "braavos-jardin-aegon",
        "centre": (4390.27, 2115.67, 124.0),
        "noyaux": {"tavern-tales"},
        "mots": {"culture", "artist", "story", "poet", "writer", "photo", "paint", "music", "tavern"},
    },
    {
        "nom": "integration-westeros",
        "usage": "braavos-quai",
        "centre": (4943.30, 2014.44, 6.0),
        "noyaux": {"pattern-prophet"},
        "mots": {"trade", "merchant", "sail", "mariner", "captain", "shipping", "travel", "foreign"},
    },
    {
        "nom": "boucle-reveil-graphe",
        "usage": "braavos-baraques",
        "centre": (4356.70, 2095.83, 124.0),
        "noyaux": {"network-weaver"},
        "mots": {"network", "coordination", "connection", "graph", "communication", "social"},
    },
    {
        "nom": "collaboration",
        "usage": "braavos-archives",
        "centre": (4529.39, 2052.94, 112.0),
        "noyaux": {"divine-economist", "class-harmonizer", "mechanical-visionary", "future-chronicler"},
        "mots": {"collaboration", "econom", "bank", "class", "mechanical", "history", "archive", "book"},
    },
    {
        "nom": "conscience-praticable",
        "usage": "braavos-septuaire",
        "centre": (4447.33, 2187.07, 124.0),
        "noyaux": {"scholar-priest"},
        "mots": {"philosoph", "priest", "scholar", "sacred", "conscious", "observer", "critic", "method"},
    },
    {
        "nom": "plan-visuel-2d",
        "usage": "braavos-table-peinte",
        "centre": (4480.40, 2124.38, 132.5),
        "noyaux": {"beauty-architect", "urbanexplorer"},
        "mots": {"visual", "beauty", "design", "architect", "pixel", "image", "light", "explorer"},
    },
]


def lire_csv(chemin: Path):
    with chemin.open(encoding="utf-8-sig", newline="") as fichier:
        return list(csv.DictReader(fichier))


def citoyens_serenissima():
    lignes = lire_csv(CITOYENS)
    return {identifiant(ligne["Username"]): ligne for ligne in lignes}


def identites_canoniques(citoyens):
    """Relie le nom de chambre importé à l'identité actuelle du personnage."""
    personnages = json.loads(PERSONNAGES.read_text(encoding="utf-8"))
    resultat = {}
    for personne in personnages:
        note = str(personne.get("note") or personne.get("_note") or "")
        marqueur = "chambres/"
        if marqueur in note:
            chambre = note.split(marqueur, 1)[1].split("/", 1)[0]
            cle = identifiant(chambre)
            if cle in citoyens:
                resultat[cle] = identifiant(personne["id"])
    for cle in citoyens:
        resultat.setdefault(cle, cle)
    return resultat


def graphe_relations(citoyens):
    graphe = {cid: {} for cid in citoyens}
    for ligne in lire_csv(RELATIONS):
        gauche = identifiant(ligne["Citizen1"])
        droite = identifiant(ligne["Citizen2"])
        confiance = float(ligne.get("TrustScore") or 0)
        if (
            ligne.get("Status") == "Active"
            and confiance >= 75
            and gauche in graphe
            and droite in graphe
            and gauche != droite
        ):
            graphe[gauche][droite] = max(confiance, graphe[gauche].get(droite, 0))
            graphe[droite][gauche] = max(confiance, graphe[droite].get(gauche, 0))
    return graphe


def texte_citoyen(ligne):
    champs = (
        "Username", "FirstName", "LastName", "SocialClass", "Specialty",
        "Description", "CorePersonality", "Personality", "FamilyMotto",
    )
    return " ".join(str(ligne.get(champ) or "").lower() for champ in champs)


def repartir(citoyens, graphe):
    # 152 personnes : huit groupes de 17 et un de 16.
    base, reste = divmod(len(citoyens), len(CLUSTERS))
    capacites = [base + (1 if i < reste else 0) for i in range(len(CLUSTERS))]
    groupes = [set() for _ in CLUSTERS]
    fixes = set()

    for i, cluster in enumerate(CLUSTERS):
        for noyau in sorted(cluster["noyaux"]):
            if noyau in citoyens:
                groupes[i].add(noyau)
                fixes.add(noyau)

    non_places = set(citoyens) - fixes
    while non_places:
        meilleur = None
        for cid in sorted(non_places):
            texte = texte_citoyen(citoyens[cid])
            for i, cluster in enumerate(CLUSTERS):
                if len(groupes[i]) >= capacites[i]:
                    continue
                liens = [graphe[cid].get(autre, 0) for autre in groupes[i]]
                # Une arête forte pèse davantage que tous les mots-clés réunis.
                relation = sum(max(0, score - 74) for score in liens) * 20
                theme = sum(1 for mot in cluster["mots"] if mot in texte) * 12
                remplissage = (capacites[i] - len(groupes[i])) / capacites[i]
                score = relation + theme + remplissage
                candidat = (score, relation, theme, -len(groupes[i]), cid, -i)
                if meilleur is None or candidat > meilleur[0]:
                    meilleur = (candidat, cid, i)
        _, cid, i = meilleur
        groupes[i].add(cid)
        non_places.remove(cid)

    return groupes


def positions(centre, nombre):
    """Petite grille compacte, assez espacée pour garder les taches lisibles."""
    x0, y0, z0 = centre
    colonnes = 5
    pas = 1.65
    lignes = math.ceil(nombre / colonnes)
    resultat = []
    for rang in range(nombre):
        ligne, colonne = divmod(rang, colonnes)
        x = x0 + (colonne - (colonnes - 1) / 2) * pas
        y = y0 + (ligne - (lignes - 1) / 2) * pas
        resultat.append((round(x, 2), round(y, 2), z0))
    return resultat


def ecrire_atomiquement(chemin: Path, donnees):
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=chemin.parent, suffix=".tmp"
    ) as fichier:
        json.dump(donnees, fichier, ensure_ascii=False, indent=2)
        fichier.write("\n")
        temporaire = Path(fichier.name)
    os.replace(temporaire, chemin)


def main():
    analyseur = argparse.ArgumentParser()
    analyseur.add_argument("--verifier", action="store_true")
    args = analyseur.parse_args()

    citoyens = citoyens_serenissima()
    identites = identites_canoniques(citoyens)
    graphe = graphe_relations(citoyens)
    groupes = repartir(citoyens, graphe)
    donnees = json.loads(CORPS.read_text(encoding="utf-8"))
    corps = {identifiant(c["personnage_id"]): c for c in donnees["corps"]}
    absents = sorted(cle for cle, pid in identites.items() if pid not in corps)
    if absents:
        raise SystemExit("Corps absents : " + ", ".join(absents))

    changements = 0
    for cluster, groupe in zip(CLUSTERS, groupes):
        membres = sorted(groupe)
        for cid, (x, y, z) in zip(membres, positions(cluster["centre"], len(membres))):
            pid = identites[cid]
            corps[pid].update({
                "usage": cluster["usage"], "quartier": "Braavos",
                "x": x, "y": y, "z": z, "monde": "braavos",
            })
            affectation = donnees["affectations"].get("personnage:" + pid)
            if affectation is None:
                raise SystemExit("Affectation absente : " + pid)
            affectation.update({"xyz": [x, y, z], "monde": "braavos"})
            changements += 1

    tailles = ", ".join(
        f"{cluster['nom']}={len(groupe)}"
        for cluster, groupe in zip(CLUSTERS, groupes)
    )
    if not args.verifier:
        ecrire_atomiquement(CORPS, donnees)
    print(f"OK : citoyens={len(citoyens)} déplacés={changements} ; {tailles}")


if __name__ == "__main__":
    main()
