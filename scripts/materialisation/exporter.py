# -*- coding: utf-8 -*-
"""Sortir le modèle vers Blender : un OBJ, son MTL, et rien d'autre.

    python scripts/materialisation/exporter.py            l'île entière
    python scripts/materialisation/exporter.py --pres     le château de près
    python scripts/materialisation/exporter.py --maille 700 --rayon 1200

Les mètres sont les mètres : une unité Blender vaut un mètre, et le modèle
arrive à sa place dans le repère du monde — pas recentré, pas remis à l'échelle.
Recentrer serait commode et faux : les vues, les distances et les altitudes
citées ailleurs ne vaudraient plus rien.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import formes as F
import peyredragon as P
import palette as Pal

SORTIE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "captures", "peyredragon")


def ecrire_mtl(chemin, matieres):
    """Une matière par nom, avec la couleur que le rasteriseur lui donne."""
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("# Peyredragon — les matières du modèle\n")
        for nom in sorted(set(matieres)):
            (r, v, b), rug = Pal.MATIERES.get(nom, Pal.MATIERES["roche"])
            f.write("\nnewmtl %s\n" % nom)
            f.write("Kd %.4f %.4f %.4f\n" % (r / 255.0, v / 255.0, b / 255.0))
            f.write("Ks %.3f %.3f %.3f\n" % ((rug * 0.35,) * 3))
            f.write("Ns %.1f\n" % (8 + rug * 120))
            f.write("d 1.0\nillum 2\n")


def ecrire_obj(chemin, tris, matieres):
    """Les sommets sont dédoublonnés : sans ça l'OBJ pèse trois fois son poids."""
    plats = tris.reshape(-1, 3)
    cle = np.round(plats.astype(np.float64), 3)
    _, premier, inverse = np.unique(cle, axis=0, return_index=True,
                                    return_inverse=True)
    sommets = plats[premier]
    faces = inverse.reshape(-1, 3) + 1

    ordre = np.argsort(matieres.astype(str), kind="stable")
    mtl = os.path.basename(chemin).replace(".obj", ".mtl")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("# Peyredragon, 1:1 — une unité vaut un mètre\n")
        f.write("mtllib %s\n" % mtl)
        # Blender est en Z vers le haut comme nous : rien à permuter.
        for s in sommets:
            f.write("v %.3f %.3f %.3f\n" % (s[0], s[1], s[2]))
        courante = None
        for i in ordre:
            m = matieres[i]
            if m != courante:
                f.write("\ng %s\nusemtl %s\n" % (m, m))
                courante = m
            a, b, c = faces[i]
            f.write("f %d %d %d\n" % (a, b, c))
    return len(sommets), len(faces)


def exporter(cadre, maille, nom, bourg=True):
    t0 = time.time()
    # La mer du rasteriseur va à 260 km pour que son bord ne se voie pas à
    # l'horizon. Exportée telle quelle, elle donne une scène de 735 km dans
    # laquelle Blender ne cadre plus rien : on en découpe un carré utile.
    tris, mat = P.batir(cadre, maille, avec_bourg=bourg, avec_mer=False)
    demi = max(cadre[2] - cadre[0], cadre[3] - cadre[1]) * 0.9
    milieu = ((cadre[0] + cadre[2]) / 2, (cadre[1] + cadre[3]) / 2)
    eau = F.prisme([(milieu[0] - demi, milieu[1] - demi),
                    (milieu[0] + demi, milieu[1] - demi),
                    (milieu[0] + demi, milieu[1] + demi),
                    (milieu[0] - demi, milieu[1] + demi)], -0.2, 0.0, "mer")
    tris, mat = F.joindre((tris, mat), eau)
    os.makedirs(SORTIE, exist_ok=True)
    obj = os.path.join(SORTIE, nom + ".obj")
    ecrire_mtl(obj.replace(".obj", ".mtl"), mat)
    nv, nf = ecrire_obj(obj, tris, mat)
    print("%s : %d sommets, %d faces, %d matières  (%.0f s)"
          % (obj, nv, nf, len(set(mat)), time.time() - t0))
    return obj


if __name__ == "__main__":
    args = sys.argv[1:]
    def opt(nom, defaut):
        return type(defaut)(args[args.index(nom) + 1]) if nom in args else defaut

    if "--pres" in args:
        centre = (P.CHATEAU[0] + (P.QUAI[0] - P.CHATEAU[0]) * 0.35,
                  P.CHATEAU[1] + (P.QUAI[1] - P.CHATEAU[1]) * 0.35)
        rayon = opt("--rayon", 700.0)
        maille = opt("--maille", 560)
        nom = "peyredragon-chateau"
    else:
        centre = P.ILE
        rayon = opt("--rayon", 3400.0)
        maille = opt("--maille", 620)
        nom = "peyredragon-ile"
    nom = opt("--sortie", nom)
    exporter((centre[0] - rayon, centre[1] - rayon,
              centre[0] + rayon, centre[1] + rayon), maille, nom)
