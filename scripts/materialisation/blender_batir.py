# -*- coding: utf-8 -*-
"""Bâtir Peyredragon DANS Blender — pas d'export, pas de fichier intermédiaire.

    blender --python scripts/materialisation/blender_batir.py
    blender --python scripts/materialisation/blender_batir.py -- --pres --maille 700

Le modèle est du Python : Blender embarque le même Python et le même numpy, il
n'y a donc aucune raison d'écrire un OBJ pour le relire ensuite. On appelle
directement `peyredragon.py`, et chaque morceau devient un objet nommé, avec
ses matières — le terrain, l'enceinte, les salles, le bourg, la montée, la mer.

Une unité vaut un mètre, et rien n'est recentré : l'assise est bien à 124 m.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

ICI = os.path.dirname(os.path.abspath(__file__))
if ICI not in sys.path:
    sys.path.insert(0, ICI)

import formes as F
import lieux as Li
import peyredragon as P
import palette as Pal

SOLEIL = Vector((0.52, -0.66, 0.54)).normalized()    # le même que le rasteriseur


# ---------------------------------------------------------------------------
def arguments():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    def opt(nom, defaut):
        return type(defaut)(a[a.index(nom) + 1]) if nom in a else defaut
    if "--pres" in a:
        centre = (P.CHATEAU[0] + (P.QUAI[0] - P.CHATEAU[0]) * 0.35,
                  P.CHATEAU[1] + (P.QUAI[1] - P.CHATEAU[1]) * 0.35)
        return centre, opt("--rayon", 700.0), opt("--maille", 560)
    return P.ILE, opt("--rayon", 3400.0), opt("--maille", 620)


def vider():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for bloc in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                 bpy.data.cameras, bpy.data.collections):
        for x in list(bloc):
            bloc.remove(x)


_MATIERES = {}


def matiere(nom):
    """Une matière Blender par matière du modèle, créée une seule fois."""
    if nom in _MATIERES:
        return _MATIERES[nom]
    (r, v, b), rug = Pal.MATIERES.get(nom, Pal.MATIERES["roche"])
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    if p:
        p.inputs["Base Color"].default_value = (r / 255.0, v / 255.0, b / 255.0, 1.0)
        p.inputs["Roughness"].default_value = float(np.clip(1.0 - rug, 0.12, 1.0))
        if nom == "mer":
            p.inputs["Roughness"].default_value = 0.08
            if "Transmission Weight" in p.inputs:
                p.inputs["Transmission Weight"].default_value = 0.35
    _MATIERES[nom] = m
    return m


def objet(nom, tris, matieres, collection):
    """Un corps du modèle → un objet Blender, facettes plates et matières."""
    if not len(tris):
        return None
    plats = np.asarray(tris, np.float32).reshape(-1, 3)
    # dédoublonner : sinon chaque sommet est écrit trois fois et le maillage
    # n'a plus une seule arête soudée — impossible d'y sélectionner un mur.
    _, premier, inverse = np.unique(np.round(plats.astype(np.float64), 3),
                                    axis=0, return_index=True, return_inverse=True)
    sommets = plats[premier]
    faces = inverse.reshape(-1, 3)

    maille = bpy.data.meshes.new(nom)
    maille.from_pydata(sommets.tolist(), [], faces.tolist())
    maille.validate(verbose=False)

    noms = sorted(set(matieres))
    for n in noms:
        maille.materials.append(matiere(n))
    rang = {n: i for i, n in enumerate(noms)}
    idx = np.array([rang[m] for m in matieres], np.int32)
    maille.polygons.foreach_set("material_index", idx)
    maille.polygons.foreach_set("use_smooth", np.zeros(len(idx), np.int8))
    maille.update()

    o = bpy.data.objects.new(nom, maille)
    collection.objects.link(o)
    return o


def groupe(nom):
    c = bpy.data.collections.new(nom)
    bpy.context.scene.collection.children.link(c)
    return c


# ---------------------------------------------------------------------------
def batir():
    centre, rayon, maille = arguments()
    cadre = (centre[0] - rayon, centre[1] - rayon,
             centre[0] + rayon, centre[1] + rayon)

    vider()
    c_sol = groupe("Le sol")
    c_pierre = groupe("Le château")
    c_dehors = groupe("Le dehors")

    morceaux = [
        ("Le terrain", F.grille(cadre[0], cadre[1], cadre[2], cadre[3], maille,
                                P.altitude, P.matiere_du_sol), c_sol),
        ("L'enceinte et les tours", P.chateau(), c_pierre),
        ("Les lieux du plan", Li.bati(), c_pierre),
        ("La montée", P.montee(), c_dehors),
        ("Le quai", P.quai(), c_dehors),
        ("Le bourg", P.bourg(), c_dehors),
        # la mer du rasteriseur va à 260 km pour cacher son bord à l'horizon ;
        # dans une scène 3D elle ne sert qu'à donner le niveau zéro.
        ("La mer", F.prisme([(centre[0] - rayon * 1.8, centre[1] - rayon * 1.8),
                             (centre[0] + rayon * 1.8, centre[1] - rayon * 1.8),
                             (centre[0] + rayon * 1.8, centre[1] + rayon * 1.8),
                             (centre[0] - rayon * 1.8, centre[1] + rayon * 1.8)],
                            -0.2, 0.0, "mer"), c_sol),
    ]
    faits = []
    for nom, (tris, mat), collection in morceaux:
        o = objet(nom, tris, mat, collection)
        if o:
            faits.append((nom, len(tris)))
            print("  %-26s %7d facettes" % (nom, len(tris)))
    return faits, centre, rayon


def reperer():
    """Un repère vide par lieu : on les retrouve dans l'outliner, par leur nom."""
    c = groupe("Les lieux nommés")
    for L in Li.lieux():
        if L["id"] in Li.SCHEMATIQUE:
            continue
        o = bpy.data.objects.new(L["nom"], None)
        o.empty_display_type = "PLAIN_AXES"
        o.empty_display_size = 6.0
        o.location = L["ou"]
        o["quoi"] = L["quoi"]
        o["etage"] = L["etage"] or ("dehors" if L["dehors"] else "cour")
        c.objects.link(o)
    for p, nom in Li.reperes_reels():
        o = bpy.data.objects.new(nom, None)
        o.empty_display_type = "PLAIN_AXES"
        o.empty_display_size = 10.0
        o.location = p
        c.objects.link(o)


def eclairer(centre, rayon):
    monde = bpy.data.worlds.new("Le ciel")
    monde.use_nodes = True
    fond = monde.node_tree.nodes["Background"]
    fond.inputs[0].default_value = (0.30, 0.35, 0.44, 1.0)
    # un ciel à 0.9 éclaire autant que le soleil : plus une ombre, plus un
    # relief, tout revient en gris. Le ciel donne l'ambiante, pas la lumière.
    fond.inputs[1].default_value = 0.28
    bpy.context.scene.world = monde
    vue_film = bpy.context.scene.view_settings
    vue_film.view_transform = "AgX" if "AgX" in [v.name for v in
        vue_film.bl_rna.properties["view_transform"].enum_items] else vue_film.view_transform
    vue_film.look = "AgX - Medium Contrast" if any(
        l.identifier == "AgX - Medium Contrast"
        for l in vue_film.bl_rna.properties["look"].enum_items) else vue_film.look

    d = bpy.data.lights.new("Le soleil", type="SUN")
    d.energy = 5.2
    d.angle = math.radians(1.4)
    d.color = (1.0, 0.94, 0.85)
    o = bpy.data.objects.new("Le soleil", d)
    bpy.context.scene.collection.objects.link(o)
    o.location = Vector((centre[0], centre[1], 0)) + SOLEIL * rayon * 2
    o.rotation_euler = (-SOLEIL).to_track_quat("-Z", "Y").to_euler()


def camera(nom, oeil, cible, lentille=46.0):
    d = bpy.data.cameras.new(nom)
    d.lens = lentille
    d.clip_start = 0.4
    d.clip_end = 80000
    o = bpy.data.objects.new(nom, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = oeil
    o.rotation_euler = (Vector(oeil) - Vector(cible)).to_track_quat("Z", "Y").to_euler()
    return o


def poser_cameras():
    """Les mêmes points de vue que les images : on doit pouvoir comparer."""
    D = (math.cos(P.RADE), math.sin(P.RADE))
    T = (-D[1], D[0])
    def au(base, avant=0.0, cote=0.0, haut=0.0):
        return (base[0] + D[0] * avant + T[0] * cote,
                base[1] + D[1] * avant + T[1] * cote, haut)
    A = P.ASSISE
    faites = [
        camera("Depuis la rade", au(P.QUAI, 950, -430, 165), au(P.CHATEAU, 0, 0, A + 25), 58),
        camera("Le château", au(P.CHATEAU, 640, 300, A + 250), au(P.CHATEAU, 0, 0, A + 20), 55),
        camera("Dans la cour", (Li.place_libre()[0][0], Li.place_libre()[0][1], A + 1.7),
               (P._monde(P.PORTE)[0], P._monde(P.PORTE)[1], A + 16), 28),
    ]
    bpy.context.scene.camera = faites[0]


def vue():
    for zone in (bpy.context.screen.areas if bpy.context.screen else []):
        if zone.type != "VIEW_3D":
            continue
        for espace in zone.spaces:
            if espace.type == "VIEW_3D":
                espace.shading.type = "MATERIAL"
                espace.clip_start = 0.4
                espace.clip_end = 80000
                espace.overlay.show_floor = False
                espace.overlay.show_axis_x = False
                espace.overlay.show_axis_y = False


def main():
    print("Peyredragon — on bâtit dans Blender, sans fichier intermédiaire")
    faits, centre, rayon = batir()
    reperer()
    eclairer(centre, rayon)
    poser_cameras()

    s = bpy.context.scene
    s.unit_settings.system = "METRIC"
    s.unit_settings.length_unit = "METERS"
    s.render.resolution_x = 1800
    s.render.resolution_y = 1012
    moteurs = s.render.bl_rna.properties["engine"].enum_items.keys()
    for m in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if m in moteurs:
            s.render.engine = m
            break
    vue()
    print("Peyredragon bâti : %d corps, %d facettes, assise à %.0f m"
          % (len(faits), sum(n for _, n in faits), P.ASSISE))


main()
