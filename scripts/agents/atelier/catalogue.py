"""Noms explicites, sources canoniques et lecture du dernier essai."""
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
RUNTIME = RACINE / ".agents-runtime" / "atelier"
EQUIPE = {
    "sarn-vieux-sang": ("Sarn — Historien", "Retrouver les decisions et les essais precedents."),
    "bren-racine-grise": ("Bren — Analyste du code", "Identifier les causes et les vrais points d'appel."),
    "ygga-main-de-pierre": ("Ygga — Developpeuse", "Produire une modification et un essai reproductible."),
    "toll-oeil-noir": ("Toll — Testeur", "Verifier les resultats bruts et contredire les conclusions fragiles."),
    "wenna-la-nommeuse": ("Wenna — Documentaliste", "Rendre le resultat et sa prochaine etape comprehensibles."),
    "nicolas-lester-reynolds": ("Nicolas — Responsable du projet", "Choisir le resultat utile et les criteres de livraison."),
}
LIEUX = {
    "La Souche": "Tableau des travaux", "L'Etabli": "Developpement",
    "Le Bassin noir": "Banc de tests", "L'Arbre des Ages": "Historique Git",
    "Le Lit des Racines": "Analyse du code",
}
AFFAIRE = "affaire-migrer-la-bataille-vers-la-stack"
SOURCE = Path("analyse/branchement-90312/fixture-dddf6c8-parent")
BANC = Path("analyse/branchement-90312/comparer-ralliement.js")
PROFILS = {"court": (30, 1, 60), "reference": (1700, 600, 900)}


def lire_json(chemin):
    return json.loads(Path(chemin).read_text(encoding="utf-8-sig"))


def dossier(numero="90312"):
    if str(numero) != "90312":
        raise ValueError("Seul l'essai 90312 est equipe pour le moment.")
    chemin = RACINE / "etat/maisons/_sans-maison/documents/books" / (AFFAIRE + ".json")
    livre = lire_json(chemin)
    lignes = []
    for table in livre.get("tables", []):
        for ligne in table.get("lignes", []):
            cellules = ligne.get("cellules", [])
            if cellules and str(cellules[0]).strip().strip("* #") == str(numero):
                lignes.append({"table": table.get("titre"), "cellules": cellules})
    if len(lignes) != 1:
        raise ValueError(f"L'item {numero} doit avoir une seule source, trouve : {len(lignes)}.")
    return {
        "nom": "Comparer le ralliement avec et sans arbitre", "item": str(numero),
        "affaire_id": livre["id"], "affaire": livre["titre"], "cahier": str(chemin),
        "item_canonique": lignes[0], "source_code": str(RACINE / SOURCE),
        "banc": str(RACINE / BANC),
        "resultat_attendu": "Deux sorties completes et comparables, avec les decisions effectivement exercees.",
        "portee": "Essai du moteur historique de Barralfond ; la livraison du moteur courant reste distincte.",
    }


def dernier():
    base = RUNTIME / "90312"
    fichiers = sorted(base.glob("*/demande.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not fichiers:
        return None
    chemin = fichiers[0].parent
    resultat = chemin / "resultat.json"
    if resultat.exists():
        retour = lire_json(resultat)
    else:
        retour = {"statut": "sans_resultat_final", "demande": lire_json(fichiers[0]),
                  "conclusion": "Essai en cours ou interrompu ; aucune mesure validee."}
    return {**retour, "dossier_essai": str(chemin)}


def consignes(qui, contexte_id=None):
    if qui not in EQUIPE or (contexte_id and str(contexte_id) != "90312"):
        return ""
    commande = f'python "{RACINE / "scripts/atelier.py"}"'
    lignes = ["", "## Atelier de developpement — Barralfond", "",
              EQUIPE[qui][0] + " : " + EQUIPE[qui][1],
              "Les noms de travail sont Tableau des travaux, Analyse du code, Developpement, Banc de tests et Historique Git.",
              f"Pour l'item 90312, lis le dossier commun : `{commande} dossier 90312`.",
              f"Lis la derniere preuve : `{commande} resultat 90312`.",
              f"Lance les deux variantes ensemble : `{commande} essayer 90312 --profil court` ; "
              "le profil reference conserve l'exigence de 1700 hommes et 600 secondes.",
              "Le dossier d'essai conserve les sources, les donnees, la commande, les sorties et le verdict.",
              "Distingue mesure obtenue, effet observe et livraison. Une comparaison sans decision de ralliement reste non concluante.",
              "Une nouvelle tentative conserve les precedentes. Transmets le chemin du resultat par le parloir existant et verifie son recu."]
    resultat = dernier()
    if resultat:
        lignes.append("Dernier essai : " + resultat["statut"] + "; " + resultat["dossier_essai"])
        lignes.append("Conclusion technique : " + resultat["conclusion"])
    return "\n".join(lignes)

