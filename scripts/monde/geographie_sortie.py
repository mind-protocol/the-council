# -*- coding: utf-8 -*-
# GEOGRAPHIE_SORTIE — generer() assemble la carte, ecrire() pose
# ecrans/modules/geo.js — la carte lit les mods CK3 et rend un module
# d'ecran, elle ne touche a rien d'autre. Matiere de scripts/carte_geo.py (lot 2).
import json
import math
import os
import re
import sys
import time

from monde.geographie import (
    SORTIE, REGIONS, FONDS, LIEUX, LIEUX_BAIE, BOURGS, ROUTES,
    PAS_TRAITS, PAS_ROUTES, PAS_RELIEF,
    trouver_mod, lire_definition, lire_default_map, lire_titres)
from monde.geographie_traces import (
    construire_grille, cadrer, contours, simplifier, chemin, point_interieur,
    reduire, lire_masque, dilater, tracer_route)

# ------------------------------------------------------------------ sortie

def generer(hauteur, tolerance):
    try:
        import numpy as np
    except ImportError:
        sys.exit("numpy manquant : pip install numpy")
    try:
        import PIL  # noqa: F401
    except ImportError:
        sys.exit("Pillow manquant : pip install Pillow")

    t0 = time.time()
    mod = trouver_mod()
    print(f"mod AGOT : {mod}")

    couleurs = lire_definition(mod)
    eau, interieures = lire_default_map(mod)
    prov_empire, prov_comte, comte_provinces = lire_titres(mod)
    print(f"{len(couleurs)} provinces, {len(eau)} d'eau dont "
          f"{len(interieures)} interieures, {len(prov_empire)} rattachees "
          f"a un empire ({time.time()-t0:.1f}s)")

    grille, packe, idx, noms_ids = construire_grille(
        mod, np, couleurs, prov_empire, eau, interieures)
    print(f"grille {grille.shape[1]}x{grille.shape[0]} ({time.time()-t0:.1f}s)")

    ids_westeros = {idx[c] for c, _, _ in REGIONS}
    boite = cadrer(np, grille, ids_westeros)
    x0, x1, y0, y1 = boite
    grille = grille[y0:y1, x0:x1]
    packe = packe[y0:y1, x0:x1]
    hg, lg = grille.shape
    print(f"cadre Westeros : {lg}x{hg} px de grille")

    # repere SVG : hauteur imposee, largeur deduite du ratio reel
    echelle = hauteur / hg
    largeur = round(lg * echelle, 1)

    def faire_transformer(f=1):
        """Un repere par grain de masque : un pixel reduit vaut f pixels."""
        def t(x, y):
            return (round(x * f * echelle, 1), round(y * f * echelle, 1))
        return t

    transformer = faire_transformer()

    # une unite SVG = 1/echelle pixels de grille
    eps = tolerance
    aire_min = (1.2 / echelle) ** 2      # on jette les ilots < ~1.2 unite²

    geo = {
        "viewBox": f"0 0 {largeur} {hauteur}",
        "largeur": largeur,
        "hauteur": hauteur,
        "regions": [],
        "fonds": {},
        "lieux": {},
    }

    # --- terre : toutes les regions de Westeros d'un seul tenant
    terre = np.isin(grille, list(ids_westeros))
    geo["terre"] = chemin(contours(np, terre), transformer, eps, aire_min)
    print(f"terre : {len(geo['terre'])//1024} Ko ({time.time()-t0:.1f}s)")

    # --- une region par empire
    for cle, nom, court in REGIONS:
        masque = grille == idx[cle]
        if not masque.any():
            print(f"  (region vide : {cle})")
            continue
        d = chemin(contours(np, masque), transformer, eps, aire_min)
        p = point_interieur(np, masque, transformer)
        geo["regions"].append({"id": cle[2:], "nom": nom, "court": court,
                               "d": d, "etiquette": p})
        print(f"  {nom:28s} {len(d)//1024:3d} Ko")

    # --- lacs et rivieres navigables : deja creuses dans la terre, on leur
    # donne leur propre trace pour les peindre autrement que l'ocean
    douce = grille == EAU_DOUCE
    geo["eaux"] = chemin(contours(np, douce), transformer, eps * 0.7,
                         aire_min * 0.35) if douce.any() else ""
    print(f"  {'lacs et rivieres':28s} {len(geo['eaux'])//1024:3d} Ko")

    # --- le relief : deux bandes tirees du heightmap, sur la terre seulement.
    # Ce n'est pas une carte topographique — c'est ce qu'un cartographe
    # ombrerait : ou le pays se souleve, et ou il devient infranchissable.
    terre_relief = reduire(np, terre, PAS_RELIEF)
    hm = os.path.join(mod, "map_data", "heightmap.png")
    if os.path.isfile(hm):
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        brut = np.asarray(Image.open(hm))[y0:y1, x0:x1].astype(np.float32)
        alt = reduire(np, brut, PAS_RELIEF, moyenne=True)
        del brut
        alt = alt[:terre_relief.shape[0], :terre_relief.shape[1]]
        sur_terre = alt[terre_relief]
        geo["relief"] = {}
        t_relief = faire_transformer(PAS_RELIEF)
        aire_relief = (2.5 / (echelle * PAS_RELIEF)) ** 2
        for nom, pct in (("collines", 62), ("montagnes", 88)):
            seuil = float(np.percentile(sur_terre, pct))
            masque = terre_relief & (alt >= seuil)
            geo["relief"][nom] = chemin(contours(np, masque), t_relief,
                                        eps * 2.2, aire_relief)
            print(f"  {nom:28s} {len(geo['relief'][nom])//1024:3d} Ko")
        del alt, sur_terre

    # --- les rivieres : rivers.png porte TOUT le reseau, y compris ce qui
    # n'est pas navigable et n'existe donc pas comme province d'eau. C'est la
    # couche qui donne son grain au pays entre deux places.
    riv = lire_masque(mod, "rivers.png", np, boite, PAS_TRAITS,
                      indices=range(0, 17))
    t_traits = faire_transformer(PAS_TRAITS)
    aire_traits = (0.35 / (echelle * PAS_TRAITS)) ** 2
    if riv is not None and riv.any():
        geo["rivieres"] = chemin(contours(np, riv), t_traits, eps * 1.6,
                                 aire_traits)
        print(f"  {'rivieres':28s} {len(geo['rivieres'])//1024:3d} Ko")

    # --- le reseau de routes du mod (canal alpha de mask-baronyroad.png).
    # Il ne sera pas dessine tel quel : pris au pixel non nul il couvre 8 % du
    # continent, et rendu entier c'est une toile d'araignee de 2,4 Mo ou plus
    # aucune place ne se lit. Il sert de SUBSTRAT : on n'en tire que les
    # grandes routes, plus bas, une fois les places connues.
    brut_routes = lire_masque(mod, "mask-baronyroad.png", np, boite, 1,
                              canal=3, seuil=200)
    reseau = None
    if brut_routes is not None:
        reseau = reduire(np, brut_routes.astype(np.float32), PAS_ROUTES,
                         moyenne=True) >= .30
        del brut_routes
        reseau = dilater(np, reseau, 2)   # refermer gues et ponts manquants

    # --- fonds hors Westeros (au-dela du Mur, cote d'Essos)
    for nom in sorted(set(FONDS.values())):
        ids = [idx[e] for e, n in FONDS.items() if n == nom and e in idx]
        masque = np.isin(grille, ids)
        if masque.any():
            geo["fonds"][nom] = chemin(contours(np, masque), transformer,
                                       eps * 1.6, aire_min * 4)

    # --- lieux : centre de la province qui porte le chateau (chef-lieu du
    # comte, soit sa premiere baronnie)
    manquants = []
    centres = {}                 # id -> (colonne, ligne) en pixels de source
    for lieu_id, comte in sorted(LIEUX.items()):
        provs = comte_provinces.get(comte)
        if not provs:
            manquants.append(f"{lieu_id} ({comte})")
            continue
        coul = couleurs.get(provs[0])
        lig, col = np.nonzero(packe == coul)
        if not len(lig):
            manquants.append(f"{lieu_id} (hors cadre)")
            continue
        centres[lieu_id] = (float(col.mean()), float(lig.mean()))
        geo["lieux"][lieu_id] = transformer(*centres[lieu_id])
    print(f"{len(geo['lieux'])}/{len(LIEUX)} lieux places "
          f"({time.time()-t0:.1f}s)")
    if manquants:
        print("  non places :", ", ".join(manquants))

    # --- les bourgs : les places intermediaires, meme calcul, mais elles
    # portent leur nom avec elles (elles n'existent dans aucune table de
    # l'etat, et n'ont donc rien a y aller chercher).
    geo["bourgs"] = []
    absents = []
    for bourg_id, (nom, comte) in BOURGS.items():
        provs = comte_provinces.get(comte)
        if not provs:
            absents.append(f"{bourg_id} ({comte})")
            continue
        coul = couleurs.get(provs[0])
        lig, col = np.nonzero(packe == coul)
        if not len(lig):
            absents.append(f"{bourg_id} (hors cadre)")
            continue
        centres[bourg_id] = (float(col.mean()), float(lig.mean()))
        geo["bourgs"].append({"id": bourg_id, "nom": nom,
                              "p": transformer(*centres[bourg_id])})
    print(f"{len(geo['bourgs'])}/{len(BOURGS)} bourgs places")
    if absents:
        print("  non places :", ", ".join(absents))

    # --- les grandes routes : on les fait suivre le reseau du mod d'une
    # place a l'autre. Ce qui sort n'est pas une droite entre deux chateaux :
    # c'est la chaussee reelle, avec ses detours autour des monts et ses
    # passages de gue.
    geo["routes"] = []
    if reseau is not None:
        t_routes = faire_transformer(PAS_ROUTES)
        for route_id, nom, etapes in ROUTES:
            pts = [centres[e] for e in etapes if e in centres]
            if len(pts) < 2:
                print(f"  route sautee (places manquantes) : {route_id}")
                continue
            suite = tracer_route(
                np, reseau,
                [(x / PAS_ROUTES, y / PAS_ROUTES) for x, y in pts])
            if not suite:
                print(f"  route introuvable sur le reseau : {route_id}")
                continue
            trace = simplifier([t_routes(x, y) for x, y in suite], eps * 3)
            d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in trace)
            geo["routes"].append({"id": route_id, "nom": nom, "d": d})
            print(f"  {nom:28s} {len(trace):4d} points, "
                  f"{len(d)//1024:2d} Ko")

    # --- les deux cadres : tout Westeros, et la baie de la Nera.
    # Le cadre du continent deborde a l'est : les places de la cote (Peyredragon,
    # l'Ile aux Griffes, Pointe-Massey) portent leur nom vers le large, et il
    # leur faut de la mer pour l'ecrire.
    geo["cadres"] = {
        "westeros": f"-8 0 {largeur + 48:.1f} {hauteur:.1f}",
    }
    pts = [geo["lieux"][i] for i in LIEUX_BAIE if i in geo["lieux"]]
    if pts:
        bx0 = min(p[0] for p in pts)
        bx1 = max(p[0] for p in pts)
        by0 = min(p[1] for p in pts)
        by1 = max(p[1] for p in pts)
        m = 0.30 * max(bx1 - bx0, by1 - by0)     # de l'air pour les noms
        bx0, bx1 = bx0 - m, bx1 + m
        by0, by1 = by0 - m, by1 + m
        geo["cadres"]["baie"] = (f"{bx0:.1f} {by0:.1f} "
                                 f"{bx1-bx0:.1f} {by1-by0:.1f}")
        print(f"cadre baie : {geo['cadres']['baie']}")

    ecrire(geo)
    total = os.path.getsize(SORTIE)
    print(f"OK -> {SORTIE} ({total//1024} Ko, {time.time()-t0:.1f}s)")


def ecrire(geo):
    entete = (
        "// geo.js — geometrie de Westeros, GENERE par scripts/carte_geo.py\n"
        "// Ne pas editer a la main : relancer le generateur.\n"
        "// Source : donnees de carte du mod AGOT (provinces, titres, mers).\n"
        '"use strict";\n'
        "window.Geo = "
    )
    corps = json.dumps(geo, ensure_ascii=False, separators=(",", ":"))
    with open(SORTIE, "w", encoding="utf-8") as fh:
        fh.write(entete + corps + ";\n")


