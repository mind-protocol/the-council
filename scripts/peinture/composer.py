#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""composer.py — poser une chanson sur la table, et l'ouvrir au bloc-notes.

Le MJ compose (concept, paroles au format Suno, prompt musical) ; ce script se
contente d'ecrire le .md et de l'ouvrir. Il ne touche jamais a `etat/` : une
chanson est hors univers, elle ne s'est pas produite dans la fiction.

Usage :
    python scripts/composer.py --titre "La Dette de Sombreval" \\
        --concept "..." --paroles paroles.txt --prompt "..." [--ouvrir]

Le prompt musical est BORNE A 800 CARACTERES : au-dela, le script refuse
d'ecrire plutot que de rendre un fichier que Suno tronquera en silence.
"""
import argparse
import os
import re
import subprocess
import sys
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSSIER = os.path.join(RACINE, "musiques")
MAX_PROMPT = 800


def ardoise(titre):
    """Un nom de fichier tenable : sans accents, sans espaces, sans surprise."""
    t = unicodedata.normalize("NFKD", titre)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return t or "chanson"


def texte_ou_fichier(v):
    """Un argument est soit le texte lui-meme, soit le chemin qui le porte."""
    if v and os.path.isfile(v):
        with open(v, encoding="utf-8") as f:
            return f.read().strip()
    return (v or "").strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--titre", required=True)
    ap.add_argument("--concept", default="", help="ce que la chanson raconte (texte ou fichier)")
    ap.add_argument("--paroles", default="", help="paroles au format Suno (texte ou fichier)")
    ap.add_argument("--prompt", default="", help="prompt musical Suno, 800 car. max (texte ou fichier)")
    ap.add_argument("--source", default="", help="d'ou vient la commande : la consigne du joueur")
    ap.add_argument("--dossier", default=DOSSIER)
    ap.add_argument("--ouvrir", action="store_true", help="ouvrir au bloc-notes")
    a = ap.parse_args()

    concept = texte_ou_fichier(a.concept)
    paroles = texte_ou_fichier(a.paroles)
    prompt = texte_ou_fichier(a.prompt)

    if len(prompt) > MAX_PROMPT:
        sys.exit("Prompt musical : %d caracteres, le plafond est %d. "
                 "Resserre-le plutot que de le laisser tronquer." % (len(prompt), MAX_PROMPT))

    os.makedirs(a.dossier, exist_ok=True)
    chemin = os.path.join(a.dossier, ardoise(a.titre) + ".md")

    lignes = ["# " + a.titre, ""]
    if a.source:
        lignes += ["> " + a.source.replace("\n", " "), ""]
    if concept:
        lignes += ["## Le concept", "", concept, ""]
    if paroles:
        lignes += ["## Paroles (format Suno)", "", "```", paroles, "```", ""]
    if prompt:
        lignes += ["## Prompt musical (Suno — %d/%d caracteres)" % (len(prompt), MAX_PROMPT),
                   "", "```", prompt, "```", ""]

    with open(chemin, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes))

    if a.ouvrir:
        try:
            if os.name == "nt":
                subprocess.Popen(["notepad.exe", chemin])
            else:
                subprocess.Popen(["xdg-open", chemin])
        except OSError as e:
            print("Ecrit, mais pas ouvert : %s" % e, file=sys.stderr)

    print(chemin)


