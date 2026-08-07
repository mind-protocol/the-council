# -*- coding: utf-8 -*-
"""La palette : de quoi les choses sont faites, et de quelle couleur.

À part, et sans dépendance lourde, pour une raison précise : le Python embarqué
de Blender n'a pas PIL. Si ces couleurs vivaient dans `rendu.py`, bâtir la
scène dans Blender obligerait à importer le rasteriseur — donc PIL — pour lire
une table de seize teintes. Une seule source pour les matières, importable des
deux côtés.
"""
import numpy as np

MATIERES = {
    "mer":       ((22, 34, 46),   0.10),
    "haut-fond": ((38, 56, 62),   0.12),
    "greve":     ((108, 100, 88), 0.50),
    "roche":     ((58, 53, 51),   0.38),
    "basalte":   ((44, 41, 42),   0.34),
    "cendre":    ((70, 65, 62),   0.44),
    "herbe":     ((62, 70, 48),   0.42),
    "lande":     ((74, 71, 56),   0.44),
    "coulee":    ((46, 39, 39),   0.26),
    "pierre":    ((49, 46, 50),   0.46),   # la pierre valyrienne, noire et lisse
    "taille":    ((88, 84, 80),   0.52),   # la pierre de taille, celle du quai
    "toit":      ((70, 62, 64),   0.44),
    "chaume":    ((104, 88, 62),  0.52),
    "mur-bourg": ((118, 110, 98), 0.55),
    "bois":      ((78, 62, 46),   0.45),
    "quai":      ((100, 94, 86),  0.52),
    # La face d'une coupe n'est pas une surface du monde : c'est le trait du
    # dessinateur. Elle s'éclaire donc à plat, quel que soit le soleil, sinon
    # une section tournée à l'ombre revient toute noire et ne montre rien.
    "coupe":     ((156, 148, 136), 0.00),
}
PLATES = {"coupe"}
CIEL_HAUT = np.array([44, 52, 66], np.float32)
CIEL_BAS = np.array([132, 128, 122], np.float32)
BRUME = np.array([118, 118, 116], np.float32)


# ---------------------------------------------------------------------------
# L'APPAREIL — les matières qui se lisent assise par assise
#
# Ce qui manque le plus de près, ce n'est pas la forme : c'est le JOINT. Une
# façade sans appareil n'a pas d'échelle — on ne sait pas si le mur fait trois
# mètres ou trente. On ne le taille pas en géométrie (une assise tous les 35 cm
# sur six cents mètres de façade, c'est des millions de facettes) : le
# rasteriseur le peint au pixel, à partir de la position monde qu'il calcule
# déjà pour les ombres.
# ---------------------------------------------------------------------------
APPAREILLEES = {"pierre", "taille", "quai", "mur-bourg", "coupe"}
ASSISE_M = 0.36          # la hauteur d'une assise, en mètres
BLOC_M = 0.86            # la longueur d'un bloc courant
JOINT_M = 0.035          # la largeur du joint creux
