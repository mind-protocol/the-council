# -*- coding: utf-8 -*-
"""Les vues : où l'on se place pour regarder Peyredragon, et ce qu'on en tire.

Aucune caméra n'est posée en coordonnées : chacune se déduit du site — le
château, le quai, le sommet —, si bien qu'un changement de relief déplace les
points de vue avec lui.

    python scripts/materialisation/vues.py            toutes les vues
    python scripts/materialisation/vues.py rade cime  celles qu'on nomme
    python scripts/materialisation/vues.py --vite     moitié de définition
"""
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import peyredragon as P
import rendu as Rd
import lieux as Li

SORTIE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "captures", "peyredragon")

D = (math.cos(P.RADE), math.sin(P.RADE))         # vers la rade
T = (-D[1], D[0])                                # en travers


def au(base, avant=0.0, cote=0.0, haut=0.0):
    """Un point posé par rapport au site : tant de mètres au large, tant de côté."""
    return (base[0] + D[0] * avant + T[0] * cote,
            base[1] + D[1] * avant + T[1] * cote, haut)


def cadre(centre, rayon):
    return (centre[0] - rayon, centre[1] - rayon, centre[0] + rayon, centre[1] + rayon)


CH, QU, SO = P.CHATEAU, P.QUAI, P.SOMMET
A = P.ASSISE
_RAMPE = P._lacets()
_SUR_LA_RAMPE = _RAMPE[int(len(_RAMPE) * 0.55)]
_LA_PORTE = P._monde(P.PORTE)
_PLACE, _DEGAGE = Li.place_libre()
import programme as Prog
_PLAN = Prog.plan()
_LA_GRANDE_SALLE = next(c for c in _PLAN["corps"] if c["id"] == "grande-salle")["milieu"]
# on se met en face, à quarante mètres, le dos au donjon
_CENTRE = (sum(q[0] for q in _PLAN["facade"]) / len(_PLAN["facade"]),
           sum(q[1] for q in _PLAN["facade"]) / len(_PLAN["facade"]))
_DANS_LA_COUR = (_CENTRE[0] * 0.55 + _LA_GRANDE_SALLE[0] * 0.45,
                 _CENTRE[1] * 0.55 + _LA_GRANDE_SALLE[1] * 0.45)

VUES = {
    "rade": dict(
        oeil=au(QU, 950, -430, 165), cible=au(CH, 0, 0, A + 25), champ=34,
        cadre=cadre(au(CH, 400, 0)[:2], 1700), maille=340, brume=9000,
        quoi="Depuis la rade : ce qu'on voit en arrivant par la mer."),
    "ile": dict(
        oeil=au(P.ILE, 6900, -4300, 1950), cible=(SO[0] + 300, SO[1] - 200, 300), champ=40,
        cadre=cadre(P.ILE, 3900), maille=360, brume=26000,
        quoi="L'île entière, de trois quarts : le Dragonmont, l'éperon, le château."),
    "chateau": dict(
        oeil=au(CH, 640, 300, A + 250), cible=au(CH, 0, 0, A + 20), champ=36,
        cadre=cadre(au(CH, 250, 0)[:2], 800), maille=380, brume=2800,
        quoi="L'enceinte et la montée, de près : la porte de mer et le bourg."),
    "cime": dict(
        oeil=(SO[0] + 200, SO[1] + 1900, 1150), cible=(SO[0], SO[1], 560), champ=42,
        cadre=cadre(SO, 2000), maille=340, brume=6000, bourg=False,
        quoi="Le Dragonmont depuis le nord : la caldeira ouverte au levant."),
    "porte": dict(
        # on ne devine pas où se tient l'homme : on le met SUR la rampe, à
        # hauteur d'yeux, au jalon que le tracé en lacets lui donne.
        oeil=(_SUR_LA_RAMPE[0], _SUR_LA_RAMPE[1], _SUR_LA_RAMPE[2] + 34),
        cible=(_LA_PORTE[0], _LA_PORTE[1], A + 6), champ=44,
        cadre=cadre(au(CH, 180, 0)[:2], 520), maille=380, brume=1600,
        quoi="Au-dessus de la montée : les lacets, la porte de mer, la courtine."),
    "lieux": dict(
        # tout le château nommé : c'est la vue qui prouve que chaque salle du
        # plan a bien un volume ici, et pas seulement une ligne dans un fichier.
        oeil=au(CH, 420, -320, A + 560), cible=au(CH, 0, 0, A + 10), champ=32,
        cadre=cadre(au(CH, 120, 0)[:2], 560), maille=380, brume=9000,
        noms="tous",
        quoi="Le château nommé : les trente-quatre lieux du plan, posés."),
    "dessous": dict(
        # la roche ôtée : les six salles taillées sous l'assise, à leur vraie
        # profondeur. Une coupe n'en ouvrirait que celles qu'elle traverse.
        oeil=au(CH, 300, 470, A + 210), cible=au(CH, -20, -10, A - 24), champ=34,
        cadre=cadre(au(CH, 60, 0)[:2], 460), maille=200, brume=9000,
        mer=False, calque="dessous", noms="dessous",
        quoi="La roche ôtée : cachots, cellier, étuves, archive, galeries."),
    "cour": dict(
        # dans la cour, à hauteur d'homme, tourné vers les corps de logis :
        # la caméra se pose au plus grand vide et vise la grande salle, dont
        # `programme.py` sait où elle est.
        oeil=(_DANS_LA_COUR[0], _DANS_LA_COUR[1], A + 1.7),
        cible=(_LA_GRANDE_SALLE[0], _LA_GRANDE_SALLE[1], A + 9), champ=62,
        cadre=cadre(au(CH, 60, 0)[:2], 420), maille=360, brume=2200,
        soleil=(0.26, -0.40, 0.88),
        quoi="Dans la cour : les corps de logis, leurs vis, le pavage."),
    "trois-quarts": dict(
        # de trois quarts et de près : la seule vue qui montre les tourelles
        # d'escalier saillant sur les façades, et les mâchicoulis du hourd
        oeil=au(CH, 320, 210, A + 96), cible=au(CH, -20, -10, A + 16), champ=38,
        cadre=cadre(au(CH, 90, 0)[:2], 460), maille=420, brume=2400,
        soleil=(0.42, -0.52, 0.74),
        quoi="De trois quarts : tourelles d'escalier, mâchicoulis, appareil."),
    "programme": dict(
        # d'aplomb sur la cour : c'est là qu'un plan de château se lit
        oeil=(CH[0], CH[1] - 1.0, A + 560), cible=(CH[0], CH[1], A), champ=42,
        cadre=cadre(au(CH, 40, 0)[:2], 340), maille=420, brume=99000,
        haut=(D[0], D[1], 0), soleil=(0.34, -0.46, 0.82),
        quoi="Le plan architecturé, d'aplomb : l'anneau de corps contre la courtine."),
    "zenith": dict(
        oeil=(CH[0], CH[1] - 1.0, A + 1350), cible=(CH[0], CH[1], A), champ=30,
        cadre=cadre(au(CH, 220, 0)[:2], 700), maille=400, brume=99000,
        haut=(D[0], D[1], 0),
        quoi="À l'aplomb du château : le plan de l'enceinte, pour la mesure."),
}


def _reperes(quoi):
    """Les points à nommer, et leur texte — jamais un nom qu'on invente ici."""
    out = []
    if quoi == "tous":
        out += Li.reperes_reels()
    for L in Li.lieux():
        if L["id"] in Li.SCHEMATIQUE:
            continue
        if quoi == "dessous" and L["etage"] != "dessous":
            continue
        if quoi == "cour" and (L["dehors"] or L["etage"] == "dessous"):
            continue
        x, y, z = L["ou"]
        haut = 8.0 if L["etage"] != "dessous" else 2.0
        out.append(((x, y, z + haut), L["nom"]))
    return out


def rendre_vue(nom, vite=False):
    v = VUES[nom]
    t0 = time.time()
    maille = v["maille"] // 2 if vite else v["maille"]
    taille = (960, 540) if vite else (1800, 1012)
    print("%-9s %s" % (nom, v["quoi"]))
    tris, mat = P.batir(v["cadre"], maille, avec_bourg=v.get("bourg", True),
                        avec_mer=v.get("mer", True), coupe=v.get("coupe"),
                        avec_sol=v.get("sol", True))
    print("          %d facettes, maille de %.0f m" % (
        len(tris), (v["cadre"][2] - v["cadre"][0]) / maille))
    cam = Rd.Camera(v["oeil"], v["cible"], v["champ"], v.get("haut", (0, 0, 1)))
    calque = None
    if v.get("calque") == "dessous":
        calque = Li.taille_sous_roche()
    img = Rd.rendre(tris, mat, cam, taille=taille, brume=v["brume"], calque=calque,
                    soleil=v.get("soleil", (0.52, -0.66, 0.54)))
    if v.get("noms"):
        img = Rd.nommer(img, cam, _reperes(v["noms"]),
                        taille=15 if vite else 19, ecart=20 if vite else 26)
    os.makedirs(SORTIE, exist_ok=True)
    chemin = os.path.join(SORTIE, nom + ".png")
    img.save(chemin)
    print("          %s  (%.0f s)" % (chemin, time.time() - t0))
    return chemin


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    vite = "--vite" in sys.argv
    print("rive à %.0f m du milieu | assise à %.0f m | quai à %.0f m du château"
          % (P._RIVE, P.ASSISE, math.hypot(QU[0] - CH[0], QU[1] - CH[1])))
    print("plus grand vide de la cour : %.0f m de dégagement" % _DEGAGE)
    for nom in (args or list(VUES)):
        if nom not in VUES:
            print("vue inconnue :", nom, "—", ", ".join(VUES))
            continue
        rendre_vue(nom, vite)
