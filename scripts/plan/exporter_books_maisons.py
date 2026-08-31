# -*- coding: utf-8 -*-
"""Export texte exhaustif des documents des maisons noire et verte."""
import argparse
import io
import json
import os
import uuid


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
MAISONS = (
    ("noir", "maison-targaryen-noir"),
    ("vert", "maison-targaryen-vert"),
)


def _scalaire(valeur):
    if isinstance(valeur, str):
        return valeur
    return json.dumps(valeur, ensure_ascii=False)


def _rendre(valeur, retrait=0):
    """Rend toute la structure sans filtrer de champ ni resumer de valeur."""
    marge = " " * retrait
    lignes = []
    if isinstance(valeur, dict):
        for cle, contenu in valeur.items():
            etiquette = str(cle)
            if isinstance(contenu, (dict, list)):
                lignes.append("%s%s:" % (marge, etiquette))
                if contenu:
                    lignes.extend(_rendre(contenu, retrait + 2))
                else:
                    lignes.append("%s  %s" % (
                        marge, "{}" if isinstance(contenu, dict) else "[]"))
            else:
                texte = _scalaire(contenu)
                morceaux = texte.splitlines() or [""]
                lignes.append("%s%s: %s" % (marge, etiquette, morceaux[0]))
                lignes.extend("%s  %s" % (marge, ligne)
                              for ligne in morceaux[1:])
        return lignes
    if isinstance(valeur, list):
        for numero, contenu in enumerate(valeur, 1):
            if isinstance(contenu, (dict, list)):
                lignes.append("%s[%d]" % (marge, numero))
                lignes.extend(_rendre(contenu, retrait + 2))
            else:
                morceaux = _scalaire(contenu).splitlines() or [""]
                lignes.append("%s[%d] %s" % (marge, numero, morceaux[0]))
                lignes.extend("%s    %s" % (marge, ligne)
                              for ligne in morceaux[1:])
        return lignes
    return [marge + _scalaire(valeur)]


def rendre_document(document, maison_id, source):
    entete = [
        "=" * 100,
        "DOCUMENT DE MAISON — %s" % maison_id,
        "SOURCE — %s" % source.replace(os.sep, "/"),
        "=" * 100,
        "",
    ]
    return "\n".join(entete + _rendre(document)) + "\n"


def _ecrire_atomique(chemin, texte):
    temporaire = "%s.%s.tmp" % (chemin, uuid.uuid4().hex)
    with io.open(temporaire, "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)
    os.replace(temporaire, chemin)


def exporter(sortie):
    os.makedirs(sortie, exist_ok=True)
    total = 0
    index = ["EXPORT DES DOCUMENTS DE MAISON", "=" * 100, ""]
    for alias, maison_id in MAISONS:
        source = os.path.join(RACINE, "etat", "maisons", maison_id,
                              "documents", "books")
        if not os.path.isdir(source):
            raise OSError("dossier source absent : %s" % source)
        destination = os.path.join(sortie, alias)
        os.makedirs(destination, exist_ok=True)

        # Ces sous-dossiers ne contiennent que les sorties de cette commande :
        # retirer les anciens .txt empeche qu'un livre supprime reste exporte.
        for nom in os.listdir(destination):
            chemin = os.path.join(destination, nom)
            if nom.lower().endswith(".txt") and os.path.isfile(chemin):
                os.remove(chemin)

        fichiers = sorted(n for n in os.listdir(source)
                          if n.lower().endswith(".json"))
        index.append("%s — %d document(s)" % (maison_id, len(fichiers)))
        for nom in fichiers:
            chemin_source = os.path.join(source, nom)
            with io.open(chemin_source, encoding="utf-8") as f:
                document = json.load(f)
            relatif = os.path.relpath(chemin_source, RACINE)
            nom_sortie = os.path.splitext(nom)[0] + ".txt"
            _ecrire_atomique(
                os.path.join(destination, nom_sortie),
                rendre_document(document, maison_id, relatif))
            index.append("  %s/%s" % (alias, nom_sortie))
            total += 1
        index.append("")

    _ecrire_atomique(os.path.join(sortie, "000-index.txt"),
                     "\n".join(index) + "\n")
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sortie", default=os.path.join("export", "files"),
                    help="dossier de destination (defaut : export/files)")
    args = ap.parse_args()
    sortie = args.sortie
    if not os.path.isabs(sortie):
        sortie = os.path.join(RACINE, sortie)
    total = exporter(os.path.abspath(sortie))
    print("%d document(s) exporte(s) dans %s" % (total, sortie))


if __name__ == "__main__":
    main()
