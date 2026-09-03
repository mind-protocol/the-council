# -*- coding: utf-8 -*-
"""Cuire la ville composée — masque et plan pour le moteur, au pas de la campagne.

    python bataille/outils/osm/05_cuire.py --id gelibolu-peninsule [--pas 5]

Ne fait rien de neuf : appelle scripts/monde/cuire_ville.py, qui est l'autorité
sur la cuisson (ce qui bloque, le masque 1 bit, le plan en mètres). Ce qu'on
décide ici, et seulement ici, c'est le PAS — et depuis le 2 septembre c'est
LE MÈTRE, pour toute l'emprise, campagne comprise.

On avait d'abord cuit à 5 m « parce que rien ne bloque un homme en rase
campagne », en gardant la ville au mètre dans une seconde cuisson. Deux
cartes pour un lieu, et un combat de rue qui perdait la finesse du mur. Le
mètre partout a été chiffré avant d'être adopté :

    17785 x 20040 m au mètre = 356 M de cases -> 36 s de cuisson, 44,5 Mo,
    43,5 Mo transférés en 102 ms, tas JS du navigateur à 59,6 Mo sur 4096.

Ce qui rend ça tenable n'est pas la compression : c'est que le masque du
moteur (monde/terrain-masque.js) ne construit AUCUN index. Il garde l'octet
brut et lit un bit par décalage — l'ouverture est en O(1), la taille ne coûte
que sa place. Une carte plus grande ne se paie donc qu'une fois.
"""
import argparse, io, json, os, subprocess, sys
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _travail import dossier_travail  # les intermédiaires vivent hors du dépôt

MOTEUR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # bataille/
RACINE = os.path.dirname(MOTEUR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--pas", type=float, default=5.0, help="mètres par case")
    ap.add_argument("--metres-par-unite", type=float, default=5.0)
    ap.add_argument("--nom", help="nom du cache OSM, pour lire la hauteur de l'emprise")
    ap.add_argument("--ville", help="tissu d'une ville engendrée : ses portes deviennent des percées du masque")
    ap.add_argument("--donnees", help="dossier de travail (défaut : bataille/donnees/osm/<nom>/)")
    a = ap.parse_args()
    if a.nom and not a.donnees:
        a.donnees = dossier_travail(a.nom)
    cmd = [sys.executable, "-X", "utf8", os.path.join(RACINE, "scripts", "monde", "cuire_ville.py"), a.id,
           "--pas", str(a.pas), "--metres-par-unite", str(a.metres_par_unite)]
    if a.ville:
        if not a.nom:
            sys.exit("--ville demande --nom (la hauteur de l'emprise vient de <nom>.propre.json)")
        prop = json.load(io.open(os.path.join(a.donnees, f"{a.nom}.propre.json"), encoding="utf-8"))
        tissu = json.load(io.open(a.ville, encoding="utf-8"))
        u, Ht = a.metres_par_unite, prop["hauteur_m"]
        for p in tissu["portes"]:   # mètres, y vers le nord → unités, y vers le sud
            x, y = p["ou"]
            cmd += ["--percer", f"{x / u:.2f},{(Ht - y) / u:.2f},{p['rayon_m'] / u:.2f},{p['nom']}"]
    r = subprocess.run(cmd, cwd=RACINE)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
