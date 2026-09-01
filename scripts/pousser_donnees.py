# -*- coding: utf-8 -*-
"""Valide, commit et pousse un snapshot cohérent de `etat/` et `chambres/`.

Sans `--vraiment`, affiche seulement ce qui partirait.
"""
import argparse
import datetime
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
NOYAU = os.path.join(ICI, "noyau")
if NOYAU not in sys.path:
    sys.path.insert(0, NOYAU)

import git_donnees


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vraiment", action="store_true",
                    help="crée le commit et le pousse")
    ap.add_argument("--sans-push", action="store_true",
                    help="avec --vraiment : crée le commit local seulement")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--message", default=None)
    a = ap.parse_args(argv)

    if not git_donnees.index_propre(RACINE):
        raise SystemExit(
            "REFUS : l'index contient déjà des changements préparés. "
            "Committez-les ou déstagez-les avant le snapshot des données.")

    branche = git_donnees.lancer(
        RACINE, "branch", "--show-current").stdout.strip()
    if not branche:
        raise SystemExit("REFUS : HEAD détachée ; aucune branche à pousser.")

    modifies = git_donnees.changements(RACINE)
    if not modifies:
        print("DONNEES — rien à sauvegarder")
        return 0

    tous = git_donnees.fichiers(RACINE)
    erreurs = []
    # Le dépôt porte quelques archives historiques vides antérieures à cette
    # commande. Elles ne doivent pas empêcher tout futur snapshot ; en revanche
    # chaque fichier neuf ou modifié doit être lisible avant de partir.
    for relatif in modifies:
        try:
            git_donnees.valider(os.path.join(RACINE, relatif))
        except (OSError, ValueError) as exc:
            erreurs.append(str(exc))
            if len(erreurs) >= 20:
                break
    if erreurs:
        raise SystemExit("REFUS : données invalides :\n  " + "\n  ".join(erreurs))

    print("DONNEES — %d changement(s) sur %s" % (len(modifies), branche))
    for chemin in modifies[:20]:
        print("  " + chemin)
    if len(modifies) > 20:
        print("  ... et %d autre(s)" % (len(modifies) - 20))
    if not a.vraiment:
        print("APERÇU SEUL — relancez avec --vraiment pour commit + push")
        return 0

    head_avant = git_donnees.lancer(
        RACINE, "rev-parse", "HEAD").stdout.strip()
    avant = git_donnees.photographie(RACINE, tous)
    try:
        git_donnees.ajouter(RACINE)
        apres = git_donnees.photographie(RACINE, tous)
        mouvants = [p for p in tous if avant[p] != apres[p]]
        if mouvants:
            git_donnees.destager(RACINE)
            raise SystemExit(
                "REFUS : %d fichier(s) ont changé pendant la capture ; "
                "aucun commit créé. Relancez quand les écritures sont calmes.\n  %s"
                % (len(mouvants), "\n  ".join(mouvants[:20])))

        head_apres = git_donnees.lancer(
            RACINE, "rev-parse", "HEAD").stdout.strip()
        if head_apres != head_avant:
            git_donnees.destager(RACINE)
            raise SystemExit(
                "REFUS : HEAD a changé pendant la capture ; aucun commit "
                "créé. Relancez sur la nouvelle version.")

        stages = git_donnees.lancer(
            RACINE, "diff", "--cached", "--name-only").stdout.splitlines()
        intrus = [p for p in stages if not git_donnees.inclus(p)]
        if intrus:
            git_donnees.destager(RACINE)
            raise SystemExit("REFUS : fichiers hors données dans l'index :\n  "
                             + "\n  ".join(intrus))
        if not stages:
            print("DONNEES — aucune différence à committer")
            return 0

        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        message = a.message or ("data: snapshot partie " + date)
        git_donnees.lancer(RACINE, "commit", "-m", message)
    except Exception:
        if git_donnees.lancer(RACINE, "diff", "--cached", "--quiet",
                              check=False).returncode != 0:
            git_donnees.destager(RACINE)
        raise

    commit = git_donnees.lancer(
        RACINE, "rev-parse", "--short", "HEAD").stdout.strip()
    print("COMMIT — %s" % commit)
    if not a.sans_push:
        git_donnees.lancer(RACINE, "push", a.remote, "HEAD")
        print("PUSH — %s/%s" % (a.remote, branche))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
