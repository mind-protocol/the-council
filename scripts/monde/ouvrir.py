# -*- coding: utf-8 -*-
"""Régler les vues 3D à l'échelle d'une ville, à l'ouverture du fichier.

    blender monde/portreal.blend --python scripts/monde/ouvrir.py

Une vue 3D de Blender coupe à 1 000 m au repos. Port-Réal fait 5,3 km de large :
sans ce réglage, la moitié de la ville disparaît dès qu'on recule, et l'on croit
à un fichier incomplet.
"""
import bpy

CLIP_LOIN = 24000.0
CLIP_PRES = 0.4

n = 0
for ecran in bpy.data.screens:
    for aire in ecran.areas:
        if aire.type != "VIEW_3D":
            continue
        for espace in aire.spaces:
            if espace.type != "VIEW_3D":
                continue
            espace.clip_start = CLIP_PRES
            espace.clip_end = CLIP_LOIN
            espace.shading.type = "MATERIAL"      # les couches ont des couleurs
            espace.overlay.show_relationship_lines = False
            # on se pose au-dessus de la ville plutôt qu'au cube de départ
            espace.region_3d.view_location = (2700.0, 1800.0, 40.0)
            espace.region_3d.view_distance = 3800.0
            n += 1

print("[monde] %d vues réglées — clip %.0f m, ombrage matière" % (n, CLIP_LOIN))
print("[monde] Les collections sont dans l'outliner : éteins « L2 bati » et")
print("[monde] « 01 enceinte » pour voir les couches L3 et L5.")
