# -*- coding: utf-8 -*-
"""CLI - la commande `python scripts/appliquer.py` : resume lisible et main().

L'ancienne section main de scripts/appliquer.py (lot 2) : les trois gardes
(empreintes, validation, atomicite) s'enchainent ici, dans cet ordre.
La facade racine ne fait que rappeler ce main par la porte etat/expose.
"""
from etat.mutations.validation import valider
from etat.mutations.application import appliquer, ecrire
import argparse
from datetime import datetime
import io
import json
import os
import sys
from etat.mutations.vocabulaire import (  # noqa: E501
    liste_books)
from etat.mutations.lecture import ETAT, STAGING, chemin_table, empreinte, lire
from etat.expose import tables as porte  # LA PORTE de etat/

def resumer(plan):
    for ligne in plan:
        m = ligne["mutation"]
        tete = "  {:>3}. {} {}".format(ligne["n"], m["table"],
                                       m.get("cible") or "")
        print("{} — {}".format(tete, m["operation"]))
        if ligne["avant"]:
            print("        avant : {}".format(
                json.dumps(ligne["avant"], ensure_ascii=False)))
        if ligne["apres"]:
            print("        apres : {}".format(
                json.dumps(ligne["apres"], ensure_ascii=False)))
        if m.get("pourquoi"):
            print("        motif : {}".format(m["pourquoi"]))


def main():
    a = argparse.ArgumentParser(
        description="Applique une proposition de etat/ a etat/*.json.")
    a.add_argument("proposition",
                   help="nom du fichier dans etat/ (ou chemin complet)")
    a.add_argument("--vraiment", action="store_true",
                   help="ecrire pour de bon (sans quoi : blanc)")
    a.add_argument("--forcer", action="store_true",
                   help="passer outre les empreintes et le deja-applique")
    a.add_argument("--joueur", default=None,
                   help="personnage_id du joueur dont on ecrit les croyances "
                        "(jetons, vues, objectifs). Requis des que la racine "
                        "est archivee.")
    args = a.parse_args()

    chemin = args.proposition
    if not os.path.isfile(chemin):
        chemin = os.path.join(STAGING, args.proposition)
    if not os.path.isfile(chemin):
        sys.exit("proposition introuvable : {}".format(args.proposition))
    with io.open(chemin, encoding="utf-8") as f:
        prop = json.load(f)

    mutations = prop.get("mutations_proposees") or []
    if not mutations:
        sys.exit("aucune mutation dans 'mutations_proposees' — rien a appliquer.")

    if prop.get("applique_le") and not args.forcer:
        sys.exit("proposition deja appliquee le {} — --forcer pour recommencer."
                 .format(prop["applique_le"]))

    # A QUI sont les croyances de ce lot : --joueur prime, sinon celui que
    # tick.py a inscrit dans la proposition au moment du calcul. Les deux
    # scripts doivent sceller et ecrire le MEME fichier.
    joueur = args.joueur or prop.get("joueur")
    if args.joueur and prop.get("joueur") and args.joueur != prop["joueur"]:
        sys.exit("REFUS : proposition calculee pour '{}', vous appliquez avec "
                 "--joueur '{}'.".format(prop["joueur"], args.joueur))

    # garde 1 : l'etat n'a pas bouge depuis le calcul
    derives = [nom for nom, sceau in (prop.get("empreintes") or {}).items()
               if empreinte(nom, joueur) != sceau]
    if derives:
        message = ("l'etat a change depuis le calcul de cette proposition : {}. "
                   "Un autre ecrivain est passe — relance le tick."
                   .format(", ".join(sorted(derives))))
        if not args.forcer:
            sys.exit("REFUS : " + message)
        print("AVERTISSEMENT (forcé) : " + message + "\n")

    # journal n'est jamais mutable : il sert a proteger la tete du joueur.
    tables = {nom: lire(nom) for nom in
              ("intentions", "evenements", "personnages", "monde", "journal",
               "lieux", "relations", "maisons")}
    # plis.json est facultatif : une partie d'avant le courrier tourne encore
    if os.path.isfile(os.path.join(ETAT, "plis.json")):
        tables["plis"] = lire("plis")
    else:
        tables["plis"] = {"plis": []}
    if isinstance(tables["plis"], dict):
        tables["plis"].setdefault("plis", [])
    # jetons.json : la table de guerre, ou vivent les incidents (la rumeur).
    # C'est une CROYANCE : elle appartient au joueur, pas au monde. Sans
    # --joueur et sans repli racine, chemin_table refuse bruyamment plutot que
    # d'ecrire dans un fichier que le jeu ne relira jamais.
    # On ne resout le chemin QUE si le lot y touche : une proposition sans
    # incident ne doit pas reclamer un --joueur dont elle n'a que faire.
    if any(m.get("table") == "jetons" for m in mutations):
        tables["jetons"] = lire("jetons", joueur)
    else:
        racine_jetons = os.path.join(ETAT, "jetons.json")
        tables["jetons"] = (lire("jetons") if os.path.isfile(racine_jetons)
                            else {"jetons": []})
    # mains.json est facultatif : une partie sans mains tourne tres bien
    tables["mains"] = (lire("mains")
                           if os.path.isfile(
                               os.path.join(ETAT, "mains.json"))
                           else {"mains": []})
    # books.json : les registres et les affaires. Facultatif comme les mains —
    # mais s'il n'est pas charge ici, liste_books() le voit VIDE : la validation
    # d'un affaire_ajouter passe alors sur une liste fantome, la mutation
    # s'ecrit nulle part, et ecrire() casse sur une cle absente.
    # Les books par LA PORTE de plan/ — paresseusement : etat est rang 0,
    # ce module ne charge le container plan qu'au moment d'appliquer.
    from plan.expose import bibliotheque
    session_livres = bibliotheque.ouvrir(ETAT)
    tables["books"] = session_livres.livres

    # garde 2 : tout valider avant de rien ecrire
    plan, erreurs = valider(mutations, tables)
    print("Proposition : {}".format(os.path.basename(chemin)))
    print("{} mutation(s), {} valide(s), {} en erreur\n".format(
        len(mutations), len(plan), len(erreurs)))
    resumer(plan)
    if erreurs:
        print("\n== ERREURS ({}) — rien n'a ete ecrit ==".format(len(erreurs)))
        for e in erreurs:
            print("  " + e)
        return 1

    if not args.vraiment:
        print("\nBlanc : rien n'a ete ecrit. Relance avec --vraiment pour appliquer.")
        return 0

    # garde 3 : ecriture atomique, puis marquage de la proposition
    touchees = appliquer(plan, tables)
    for nom in sorted(touchees):
        if nom == "books":
            try:
                session_livres.sauver()
            except bibliotheque.BibliothequeModifiee as exc:
                print("\nREFUS : {}".format(exc))
                return 1
        else:
            ecrire(nom, tables[nom], joueur)
    prop["applique_le"] = datetime.now().isoformat(timespec="seconds")
    porte.ecrire(chemin, prop)

    print("\nApplique. Tables ecrites : {}".format(", ".join(sorted(touchees))))
    print("Verifie la coherence : python scripts/tick.py --verifier")
    return 0
