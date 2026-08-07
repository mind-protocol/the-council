# -*- coding: utf-8 -*-
"""Script de démarrage de Blender : il importe le modèle et pose la scène.

    blender --python scripts/materialisation/blender_ouvrir.py -- <fichier.obj>

Sans argument, il prend le dernier OBJ écrit dans captures/peyredragon/.
Il ne fait que MONTER la scène — la géométrie vient de l'exportateur, et rien
n'est modélisé ici : ce fichier doit rester jetable.
"""
import glob
import math
import os
import sys

import bpy
from mathutils import Vector

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(bpy.data.filepath or __file__))))
CAPTURES = os.path.join(RACINE, "captures", "peyredragon")

SOLEIL = Vector((0.52, -0.66, 0.54)).normalized()   # le même que le rasteriseur


def choisir():
    apres = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if apres and apres[0].endswith(".obj"):
        return apres[0]
    trouves = sorted(glob.glob(os.path.join(CAPTURES, "*.obj")),
                     key=os.path.getmtime)
    if not trouves:
        raise SystemExit("aucun OBJ dans " + CAPTURES)
    return trouves[-1]


def vider():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for bloc in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                 bpy.data.cameras):
        for x in list(bloc):
            bloc.remove(x)


def poser_soleil():
    d = bpy.data.lights.new("Le soleil", type="SUN")
    d.energy = 3.4
    d.angle = math.radians(1.6)
    d.color = (1.0, 0.94, 0.84)
    o = bpy.data.objects.new("Le soleil", d)
    bpy.context.collection.objects.link(o)
    o.location = SOLEIL * 4000
    o.rotation_euler = (-SOLEIL).to_track_quat("-Z", "Y").to_euler()
    return o


def poser_ciel():
    monde = bpy.data.worlds.new("Le ciel")
    monde.use_nodes = True
    fond = monde.node_tree.nodes["Background"]
    fond.inputs[0].default_value = (0.32, 0.36, 0.44, 1.0)
    fond.inputs[1].default_value = 0.85
    bpy.context.scene.world = monde


def poser_camera(cible, oeil):
    d = bpy.data.cameras.new("Depuis la rade")
    d.lens = 46
    d.clip_start = 0.5
    d.clip_end = 60000
    o = bpy.data.objects.new("Depuis la rade", d)
    bpy.context.collection.objects.link(o)
    o.location = oeil
    o.rotation_euler = (Vector(cible) - Vector(oeil)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = o
    return o


def main():
    chemin = choisir()
    vider()
    bpy.ops.wm.obj_import(filepath=chemin, forward_axis="Y", up_axis="Z")
    objets = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    if not objets:
        raise SystemExit("rien n'a été importé de " + chemin)

    # les faces sont plates par construction : les lisser mentirait sur le modèle
    for o in objets:
        for p in o.data.polygons:
            p.use_smooth = False

    mini = Vector((1e9, 1e9, 1e9))
    maxi = Vector((-1e9, -1e9, -1e9))
    for o in objets:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            mini = Vector(map(min, mini, p))
            maxi = Vector(map(max, maxi, p))
    centre = (mini + maxi) / 2
    taille = (maxi - mini).length

    poser_ciel()
    poser_soleil()
    # on regarde depuis la rade, comme la vue de référence : au large et bas
    oeil = centre + Vector((math.cos(math.radians(-14)), math.sin(math.radians(-14)), 0)) \
        * taille * 0.55 + Vector((0, -taille * 0.22, taille * 0.10))
    poser_camera(centre, oeil)

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1012
    # le nom du moteur a changé d'une version à l'autre : on prend ce qui existe
    moteurs = scene.render.bl_rna.properties["engine"].enum_items.keys()
    for m in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if m in moteurs:
            scene.render.engine = m
            break

    # en --background il n'y a pas d'écran : le réglage de vue n'a pas de sens
    for zone in (bpy.context.screen.areas if bpy.context.screen else []):
        if zone.type == "VIEW_3D":
            for espace in zone.spaces:
                if espace.type == "VIEW_3D":
                    espace.shading.type = "MATERIAL"
                    espace.clip_end = 60000
                    espace.overlay.show_floor = False
    print("Peyredragon : %d objets, %.0f m d'emprise, importés de %s"
          % (len(objets), taille, chemin))


main()
