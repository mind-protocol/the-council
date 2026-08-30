# -*- coding: utf-8 -*-
"""Genere la geometrie de la carte de Westeros a partir du mod AGOT.

Usage :
    python scripts/carte_geo.py                 -> ecrans/modules/geo.js
    python scripts/carte_geo.py --hauteur 620   (hauteur du viewBox)
    python scripts/carte_geo.py --tolerance 0.5 (simplification, unites SVG)

Outil de BUILD, lance a la main : il lit les donnees du mod AGOT installe
(Steam workshop 2962333032) et fige le resultat dans un fichier JS. Le jeu
ne depend jamais du mod ni de CK3 a l'execution — seulement de geo.js.

Chaine :
1. common/landed_titles : pile de blocs -> province -> (empire, royaume, comte)
2. map_data/definition.csv : province -> couleur RGB dans provinces.png
3. map_data/default.map : zones maritimes, lacs, rivieres navigables
4. map_data/provinces.png (9216x6144) : PLEINE resolution, chaque pixel
   devient l'id de sa region, puis cadre sur Westeros
5. suivi de contour (crack following) sur chaque masque -> polygones exacts,
   frontieres communes rigoureusement identiques entre regions voisines
6. simplification Douglas-Peucker -> chemins SVG

Trois couches de detail viennent des autres masques du mod, chacune avec son
propre sous-echantillonnage (elles n'ont pas besoin du pixel) :
  map_data/rivers.png          -> le reseau de rivieres, meme les non navigables
  map_data/mask-baronyroad.png -> les ROUTES (canal alpha) : c'est le chemin
                                  qui relie Port-Real a Castral Roc
  map_data/heightmap.png       -> le relief, en deux bandes (collines, monts)

Le repere de sortie : viewBox cale sur Westeros, hauteur donnee par
--hauteur, largeur deduite du ratio reel du continent.

Doc : docs/carte.md
"""
import argparse
import json
import math
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJET = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SORTIE = os.path.join(PROJET, "ecrans", "modules", "geo.js")

CANDIDATS_MOD = [
    r"C:\Program Files (x86)\Steam\steamapps\workshop\content\1158310\2962333032",
    r"C:\Program Files (x86)\Steam\steamapps\workshop\content\1158310",
]

# provinces.png (9216x6144) est lu a PLEINE resolution : une fois cadre sur
# Westeros, cela fait ~6 px de source par unite SVG, et la cote peut donc etre
# simplifiee a 0,22 unite sans jamais inventer de detail. Le cout est en
# memoire (une table de correspondance de 16 Mo remplace le np.unique, qui
# doublait l'empreinte), pas en temps.
PAS = 1

# Les autres masques n'ont pas besoin du pixel : chacun son facteur de
# reduction, applique par blocs (max pour les traits fins, moyenne pour le
# relief) apres cadrage. 2 => ~3 px par unite, 8 => ~0,75.
PAS_TRAITS = 2                  # rivieres
PAS_ROUTES = 2                  # routes
PAS_RELIEF = 8                  # heightmap

# Les grandes regions, telles que le mod les nomme (rang empire), avec leur
# nom francais, un nom court pour les etiquettes de la carte, et l'ordre
# d'affichage.
REGIONS = [
    ("e_the_north",        "Le Nord",                  "Le Nord"),
    ("e_the_wall",         "Le Mur",                   "Le Mur"),
    ("e_the_vale",         "Le Val d'Arryn",           "Le Val"),
    ("e_the_riverlands",   "Le Conflans",              "Le Conflans"),
    ("e_the_iron_islands", "Les Îles de Fer",          "Îles de Fer"),
    ("e_the_westerlands",  "Les Terres de l'Ouest",    "L'Ouest"),
    ("e_the_crownlands",   "Les Terres de la Couronne", "La Couronne"),
    ("e_the_reach",        "Le Bief",                  "Le Bief"),
    ("e_the_stormlands",   "Les Terres de l'Orage",    "L'Orage"),
    ("e_dorne",            "Dorne",                    "Dorne"),
]
# Terres hors Westeros gardees en fond discret (decoupees au cadre).
FONDS = {"e_beyond_the_wall": "au_dela", "e_narrow_sea": "essos",
         "e_daoryrdembos": "essos"}

# Les lieux de etat/lieux.json -> comte du mod qui porte leur chateau.
LIEUX = {
    "port-real": "c_kings_landing",
    "peyredragon": "c_dragonstone",
    "lamarck": "c_high_tide",
    "rosby": "c_rosby",
    "stokeworth": "c_stokeworth",
    "sombreval": "c_duskendale",
    "repaire-aux-corneilles": "c_rooks_rest",
    "griffes": "c_claw_isle",
    "pointe-massey": "c_stonedance",
    "sharp-point": "c_sharp_point",
    "sweetport-sound": "c_sweetport_sound",
    "cracfosse": "c_dyre_den",
    "accalmie": "c_storms_end",
    "harrenhal": "c_harrenhal",
    "villevieille": "c_oldtown",
    "vivesaigues": "c_riverrun",
    "les-eyrie": "c_the_eyrie",
    "castral-roc": "c_casterly_rock",
    "winterfell": "c_winterfell",
}

# La vignette du plateau est cadree sur la baie de la Nera — la ou se joue
# la Danse. La grande table, elle, montre tout Westeros.
LIEUX_BAIE = ["port-real", "peyredragon", "lamarck", "rosby", "stokeworth",
              "sombreval", "repaire-aux-corneilles", "griffes",
              "pointe-massey", "sharp-point", "sweetport-sound",
              "cracfosse"]

# Les BOURGS — les places intermediaires. Elles ne sont dans aucune table de
# l'etat : elles n'ont ni allegeance, ni bannieres, ni pieces de guerre. Elles
# sont la pour qu'une route ait des etapes, et n'apparaissent qu'a la loupe
# (voir carte.js). L'ossature est le chemin de Port-Real a Castral Roc, par
# les deux voies : la route de l'Or au sud du Lac-Dieu, la route de la Riviere
# par Harrenhal, Vivesaigues et la Dent d'Or.
#     id  ->  (nom francais, comte du mod)
BOURGS = {
    # --- les terres de la Couronne, en sortant de Port-Real
    "hayford":        ("Hayford", "c_hayford"),
    "les-andouillers": ("Les Andouillers", "c_antlers"),
    "corne-de-truie": ("Corne-de-Truie", "c_sows_horn"),
    "gue-cerf":       ("Gué-Cerf", "c_rollingford"),
    "brumaie":        ("Brumaie", "c_brownhollow"),
    # --- le Conflans : Harrenhal, le Lac-Dieu, la route du nord
    "viergetang":     ("Viergétang", "c_maidenpool"),
    "les-salines":    ("Les Salines", "c_saltpans"),
    "darry":          ("Darry", "c_darry"),
    "hautcoeur":      ("Hautcœur", "c_high_heart"),
    "pierremou":      ("Pierremoû", "c_stoney_sept"),
    "foiremarche":    ("Foiremarché", "c_fairmarket"),
    "pierhaie":       ("Pierhaie", "c_stone_hedge"),
    "arbre-aux-corbeaux": ("Arbre-aux-Corbeaux", "c_raventree"),
    "les-jumeaux":    ("Les Jumeaux", "c_the_twins"),
    "atranta":        ("Atranta", "c_atranta"),
    "chutes-culbuteur": ("Chutes-du-Culbuteur", "c_tumblers_falls"),
    # --- les terres de l'Ouest : la fin du chemin
    "antre-profond":  ("Antre-Profond", "c_deep_den"),
    "dent-d-or":      ("La Dent d'Or", "c_the_golden_tooth"),
    "sarsfield":      ("Sarsfield", "c_sarsfield"),
    "castamere":      ("Castamere", "c_castamere"),
    "croix-boeuf":    ("Croix-Bœuf", "c_oxcross"),
    "port-lannis":    ("Port-Lannis", "c_lannisport"),
    "kayce":          ("Kayce", "c_kayce"),
    "corcrag":        ("Corcrag", "c_crakehall"),
    # --- ce qui borde la route au sud et au nord, pour situer le reste
    "pont-amer":      ("Pont-l'Amer", "c_bitterbridge"),
    "hautjardin":     ("Hautjardin", "c_highgarden"),
    "port-blanc":     ("Port-Blanc", "c_white_harbor"),
    "les-portes-lune": ("Les Portes de la Lune", "c_gates_of_the_moon"),
    "goeleville":     ("Goëville", "c_gulltown"),
    "pyk":            ("Pyk", "c_pyke"),
    "estermont":      ("Estermont", "c_estermont"),
    "lancehelion":    ("Lancehélion", "c_sunspear"),
}

# Les GRANDES ROUTES. Le mod porte le reseau capillaire entier — chaque
# baronnie a ses chemins, et pose 8 % du continent en chaussee : rendu tel
# quel, c'est une toile d'araignee ou plus rien ne se lit. On ne garde donc
# que les routes qui portent un nom, et on les fait SUIVRE le reseau reel :
# chaque etape est cherchee de proche en proche sur le masque du mod (voir
# `tracer_route`). Une route n'est pas une droite entre deux chateaux.
#     id, nom affiche, la suite des places traversees (ids de LIEUX ou BOURGS)
ROUTES = [
    ("route-or", "La route de l'Or",
     ["port-real", "hayford", "antre-profond", "port-lannis", "castral-roc"]),
    ("route-riviere", "La route de la Rivière",
     ["port-real", "pierremou", "vivesaigues", "dent-d-or", "sarsfield",
      "port-lannis"]),
    ("route-royale", "La route Royale",
     ["port-real", "corne-de-truie", "darry", "les-jumeaux", "winterfell"]),
    ("route-rose", "La route de la Rose",
     ["port-real", "pont-amer", "hautjardin", "villevieille"]),
    ("route-sombreval", "La route de Sombreval",
     ["port-real", "rosby", "stokeworth", "sombreval", "viergetang"]),
]


# ------------------------------------------------------------------ le mod

def trouver_mod():
    """Dossier du mod AGOT : premier candidat qui porte une carte de Westeros."""
    candidats = []
    for c in CANDIDATS_MOD:
        if os.path.isdir(c) and os.path.isfile(
                os.path.join(c, "map_data", "definition.csv")):
            candidats.append(c)
        elif os.path.isdir(c):
            candidats += [os.path.join(c, d) for d in os.listdir(c)]
    for c in candidats:
        defcsv = os.path.join(c, "map_data", "definition.csv")
        if not os.path.isfile(defcsv):
            continue
        with open(defcsv, encoding="utf-8", errors="replace") as fh:
            tete = fh.read(20000)
        if "winterfell" in tete.lower():
            return c
    sys.exit("mod AGOT introuvable — verifier CANDIDATS_MOD")


def lire_definition(mod):
    """definition.csv -> {province_id: couleur RGB packee}."""
    couleurs = {}
    with open(os.path.join(mod, "map_data", "definition.csv"),
              encoding="utf-8", errors="replace") as fh:
        for ligne in fh:
            parts = ligne.split(";")
            if len(parts) < 4 or not parts[0].strip().isdigit():
                continue
            try:
                pid, r, g, b = (int(parts[0]), int(parts[1]),
                                int(parts[2]), int(parts[3]))
            except ValueError:
                continue
            couleurs[pid] = (r << 16) | (g << 8) | b
    return couleurs


def lire_default_map(mod):
    """default.map -> (toutes les provinces d'eau, les eaux interieures).

    Les eaux interieures (lacs et rivieres navigables) sont creusees dans la
    terre comme les mers, mais recoivent leur propre trace pour pouvoir etre
    peintes autrement que l'ocean.
    """
    eau, interieures = set(), set()
    with open(os.path.join(mod, "map_data", "default.map"),
              encoding="utf-8", errors="replace") as fh:
        for ligne in fh:
            m = re.match(r"\s*(\w+)\s*=\s*(RANGE|LIST)\s*\{([^}]*)\}", ligne)
            if not m:
                continue
            cle, mode, vals = m.group(1), m.group(2), m.group(3).split()
            if cle not in ("sea_zones", "lakes", "river_provinces"):
                continue
            if mode == "RANGE" and len(vals) == 2:
                ids = set(range(int(vals[0]), int(vals[1]) + 1))
            else:
                ids = {int(v) for v in vals}
            eau |= ids
            if cle in ("lakes", "river_provinces"):
                interieures |= ids
    return eau, interieures


def lire_titres(mod):
    """landed_titles -> {province: (empire, comte)} et {comte: [provinces]}.

    Parcours a pile : on empile le nom de chaque bloc ouvert, et tout
    `province = N` rencontre est attribue aux ancetres e_ et c_ courants.
    """
    prov_empire, prov_comte, comte_provinces = {}, {}, {}
    dossier = os.path.join(mod, "common", "landed_titles")
    re_bloc = re.compile(r"^\s*([a-zA-Z0-9_\-]+)\s*=\s*\{")
    re_prov = re.compile(r"^\s*province\s*=\s*(\d+)")
    for fichier in sorted(os.listdir(dossier)):
        if not fichier.endswith(".txt"):
            continue
        pile = []
        with open(os.path.join(dossier, fichier), encoding="utf-8-sig",
                  errors="replace") as fh:
            for ligne in fh:
                ligne = ligne.split("#", 1)[0]
                if not ligne.strip():
                    continue
                m = re_bloc.match(ligne)
                if m:
                    pile.append(m.group(1))
                    pile.extend([""] * (ligne.count("{") - 1))
                else:
                    mp = re_prov.match(ligne)
                    if mp:
                        pid = int(mp.group(1))
                        emp = next((n for n in pile if n.startswith("e_")), None)
                        cte = next((n for n in reversed(pile)
                                    if n.startswith("c_")), None)
                        if emp:
                            prov_empire[pid] = emp
                        if cte:
                            prov_comte[pid] = cte
                            comte_provinces.setdefault(cte, []).append(pid)
                    pile.extend([""] * ligne.count("{"))
                for _ in range(ligne.count("}")):
                    if pile:
                        pile.pop()
    return prov_empire, prov_comte, comte_provinces




# Les traces et la sortie vivent dans geographie_traces.py et
# geographie_sortie.py (meme container) ; l'import vient APRES les
# constantes et le lecteur du mod, qu'ils relisent pendant leur chargement.
from monde.geographie_sortie import generer, ecrire  # noqa: E402


def main():
    ap = argparse.ArgumentParser(
        description="Genere ecrans/modules/geo.js depuis le mod AGOT")
    ap.add_argument("--hauteur", type=float, default=620.0,
                    help="hauteur du viewBox en unites SVG (defaut 620)")
    ap.add_argument("--tolerance", type=float, default=0.22,
                    help="simplification Douglas-Peucker, en unites SVG")
    args = ap.parse_args()
    generer(args.hauteur, args.tolerance)


