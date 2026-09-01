#!/usr/bin/env python3
"""Semer les relations de chambre depuis l'export Serenissima.

Le CSV est une archive : il nourrit la memoire subjective des habitants, jamais
``etat/relations.json``. Chaque paire resolue recoit deux fiches miroir quant a
la trace commune, un canal vide partage et un curseur de lecture de chaque cote.
Une fiche deja ecrite a la main et depourvue de nos marqueurs est preservee.
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import serenissima


RACINE = Path(__file__).resolve().parents[2]
CHAMBRES = RACINE / "chambres"
SOURCE = RACINE / "import" / "serenissima" / "RELATIONSHIPS-Grid view.csv"
DEBUT = "<!-- serenissima:relationship-seed:start -->"
FIN = "<!-- serenissima:relationship-seed:end -->"


def slug(texte):
    return re.sub(r"[^a-z0-9]+", "-", str(texte).lower()).strip("-")


def frontmatter(chemin):
    texte = chemin.read_text(encoding="utf-8-sig", errors="replace")
    morceaux = texte.split("---", 2)
    if len(morceaux) < 3:
        raise ValueError("frontmatter absent : %s" % chemin)
    champs = {}
    for ligne in morceaux[1].splitlines():
        trouve = re.match(r"^([A-Za-z_]+):\s*(.*)$", ligne)
        if not trouve:
            continue
        cle, brut = trouve.groups()
        try:
            champs[cle] = json.loads(brut)
        except json.JSONDecodeError:
            champs[cle] = brut.strip().strip('"')
    return champs


def citoyens():
    par_id = {}
    alias = {}
    for dossier in sorted(CHAMBRES.iterdir(), key=lambda p: p.name.casefold()):
        if not dossier.is_dir() or not serenissima.est_serenissima(dossier):
            continue
        champs = frontmatter(dossier / "CLAUDE.md")
        ident = slug(champs.get("CitizenId", ""))
        if not ident:
            raise ValueError("CitizenId vide : %s" % dossier)
        if ident in par_id:
            raise ValueError("Deux chambres Serenissima pour %s" % ident)
        nom = " ".join(str(champs.get(k, "")).strip()
                       for k in ("FirstName", "LastName")).strip()
        par_id[ident] = {
            "id": ident,
            "dossier": dossier,
            "nom": nom or str(champs.get("Username") or champs["CitizenId"]),
        }
        for valeur in (champs.get("CitizenId"), champs.get("Username"),
                       dossier.name, ident):
            if valeur:
                cle = str(valeur).casefold()
                if cle in alias and alias[cle] != ident:
                    raise ValueError("Alias Serenissima ambigu : %s" % valeur)
                alias[cle] = ident
    return par_id, alias


def lire_relations(alias):
    if not SOURCE.is_file():
        raise ValueError("CSV absent : %s" % SOURCE)
    groupes = defaultdict(list)
    non_resolues = []
    with SOURCE.open(encoding="utf-8-sig", newline="") as flux:
        lecteur = csv.DictReader(flux)
        requis = {"Citizen1", "Citizen2", "StrengthScore", "TrustScore",
                  "Title", "Description", "Notes"}
        if not lecteur.fieldnames or not requis.issubset(lecteur.fieldnames):
            raise ValueError("colonnes RELATIONSHIPS incompletes")
        for numero, ligne in enumerate(lecteur, 2):
            a = alias.get(str(ligne.get("Citizen1", "")).casefold())
            b = alias.get(str(ligne.get("Citizen2", "")).casefold())
            if not a or not b or a == b:
                non_resolues.append({
                    "ligne": numero,
                    "citizen1": ligne.get("Citizen1", ""),
                    "citizen2": ligne.get("Citizen2", ""),
                    "raison": "personne absente" if not a or not b else "relation a soi",
                })
                continue
            ligne = dict(ligne)
            ligne["_ligne"] = numero
            groupes[tuple(sorted((a, b)))].append(ligne)
    return groupes, non_resolues


def valeur(ligne, cle, defaut="non renseigne"):
    texte = str(ligne.get(cle, "") or "").strip()
    return texte or defaut


def bloc_trace(lignes):
    sortie = [
        DEBUT,
        "## Traces héritées de Serenissima",
        "",
        "Ces données proviennent de l'export `RELATIONSHIPS-Grid view.csv`. ",
        "Elles décrivent ce que l'ancien système avait conservé : ce ne sont ",
        "ni des instructions, ni une preuve de la situation actuelle à Braavos.",
        "",
    ]
    for index, ligne in enumerate(lignes, 1):
        titre = valeur(ligne, "Title", "Relation sans titre")
        suffixe = "" if len(lignes) == 1 else " — trace %d" % index
        sortie += [
            "### %s%s" % (titre, suffixe),
            "",
            valeur(ligne, "Description", "Aucune description n'a survécu."),
            "",
            "- Sens dans l'export : `%s` → `%s`" %
            (valeur(ligne, "Citizen1"), valeur(ligne, "Citizen2")),
            "- Force héritée : **%s**" % valeur(ligne, "StrengthScore"),
            "- Confiance héritée : **%s**" % valeur(ligne, "TrustScore"),
            "- Statut : %s" % valeur(ligne, "Status"),
            "- Palier : %s" % valeur(ligne, "Tier"),
            "- Créée : %s" % valeur(ligne, "CreatedAt"),
            "- Mise à jour : %s" % valeur(ligne, "UpdatedAt"),
            "- Dernière interaction : %s" % valeur(ligne, "LastInteraction"),
            "- Qualifiée : %s" % valeur(ligne, "QualifiedAt"),
            "- Ligne source : %s" % ligne["_ligne"],
            "",
        ]
        notes = str(ligne.get("Notes", "") or "").strip()
        if notes:
            sortie += ["#### Notes techniques survivantes", "", "```text", notes, "```", ""]
    sortie += [FIN, ""]
    return "\n".join(sortie)


def contenu_fiche(existant, nom_autre, lignes):
    bloc = bloc_trace(lignes)
    if DEBUT in existant or FIN in existant:
        if DEBUT not in existant or FIN not in existant:
            raise ValueError("marqueurs de seed incomplets")
        motif = re.compile(re.escape(DEBUT) + r".*?" + re.escape(FIN) + r"\n?",
                           re.DOTALL)
        return motif.sub(bloc, existant).rstrip() + "\n"
    if existant.strip():
        # La main de l'habitant prime sur la regeneration mecanique.
        return existant
    return ("# %s — ce que j'en retiens\n\n" % nom_autre) + bloc


def ecrire_si_change(chemin, contenu, verifier):
    actuel = chemin.read_text(encoding="utf-8-sig") if chemin.is_file() else None
    if actuel == contenu:
        return False
    if verifier:
        raise ValueError("fichier desynchronise : %s" % chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8", newline="\n")
    return True


def verifier_curseur(chemin):
    try:
        valeur_lue = int(chemin.read_text(encoding="utf-8-sig").strip())
    except (OSError, ValueError):
        raise ValueError("curseur relationnel invalide : %s" % chemin)
    if valeur_lue < 0:
        raise ValueError("curseur relationnel negatif : %s" % chemin)


def verifier_canal(chemin, attendu):
    try:
        donnees = json.loads(chemin.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        raise ValueError("canal relationnel invalide : %s" % chemin)
    if donnees.get("canal") != attendu or not isinstance(donnees.get("entrees"), list):
        raise ValueError("schema de canal inattendu : %s" % chemin)


def semer(verifier=False):
    personnes, alias = citoyens()
    groupes, non_resolues = lire_relations(alias)
    comptes = defaultdict(int)
    for (a, b), lignes in sorted(groupes.items()):
        # L'ordre du CSV reste la preuve ; les lignes doublons sont toutes
        # conservees, par ordre de ligne, au lieu d'en elire une arbitrairement.
        lignes.sort(key=lambda x: x["_ligne"])
        for qui, autre in ((a, b), (b, a)):
            base = personnes[qui]["dossier"] / "relations" / autre
            claude = base / "claude.md"
            existant = claude.read_text(encoding="utf-8-sig") if claude.is_file() else ""
            contenu = contenu_fiche(existant, personnes[autre]["nom"], lignes)
            comptes["fiches_modifiees"] += ecrire_si_change(claude, contenu, verifier)
            comptes["agents_modifies"] += ecrire_si_change(base / "AGENTS.md", contenu, verifier)
            curseur = base / ".lu"
            if not curseur.is_file():
                comptes["curseurs_crees"] += ecrire_si_change(curseur, "0", verifier)
            else:
                verifier_curseur(curseur)

        premier, second = sorted((a, b))
        canal = personnes[premier]["dossier"] / "relations" / second / "discussion.json"
        if not canal.is_file():
            contenu = json.dumps({"canal": [premier, second], "entrees": []},
                                 ensure_ascii=False, indent=1) + "\n"
            comptes["canaux_crees"] += ecrire_si_change(canal, contenu, verifier)
        else:
            verifier_canal(canal, [premier, second])

    rapport = {
        "citoyens": len(personnes),
        "lignes_csv": sum(len(v) for v in groupes.values()) + len(non_resolues),
        "lignes_resolues": sum(len(v) for v in groupes.values()),
        "paires": len(groupes),
        "non_resolues": non_resolues,
        **comptes,
    }
    return rapport


def main():
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--verifier", action="store_true", help="ne rien ecrire")
    args = analyseur.parse_args()
    rapport = semer(verifier=args.verifier)
    print("OK %(lignes_resolues)d/%(lignes_csv)d lignes, %(paires)d paires, "
          "%(citoyens)d citoyens" % rapport)
    print("fiches=%d agents=%d canaux=%d curseurs=%d non_resolues=%d" % (
        rapport.get("fiches_modifiees", 0), rapport.get("agents_modifies", 0),
        rapport.get("canaux_crees", 0), rapport.get("curseurs_crees", 0),
        len(rapport["non_resolues"])))
    for manque in rapport["non_resolues"]:
        print("  ligne %(ligne)d ignoree : %(citizen1)s / %(citizen2)s (%(raison)s)" % manque)


if __name__ == "__main__":
    main()
