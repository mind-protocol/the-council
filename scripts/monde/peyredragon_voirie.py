# -*- coding: utf-8 -*-
"""La voirie de Peyredragon — de quoi ALLER quelque part, à pied.

    python scripts/monde/peyredragon_voirie.py   (après peyredragon.py,
                                                  avant peyredragon_usages.py)

Le bourg avait six tronçons : le grand escalier, la rue du bourg, trois chemins
sans nom et le quai. Six polylignes qui ne se touchaient nulle part, sans
longueur, sans altitude, sans raison. Un A* là-dessus ne relie rien, et les huit
cent huit corps de Peyredragon restaient sur leur seuil pendant que les quatre
cent mille de Port-Réal allaient au puits.

Ce qui manquait n'était pas des rues : c'étaient les RACCORDS. Les quatre
chemins du bourg sont bien les axes le long desquels `materialisation/
peyredragon.py` a semé les soixante-sept feux — les maisons les bordent, à neuf
ou quatorze mètres. Mais aucun ne rejoignait le quai, ni l'escalier, ni son
voisin. On les reprend donc tels quels, on les taille là où ils entrent dans la
mer, et on les COUD : la place du pied de l'escalier, le chemin de grève, les
deux raccords de traverse.

Le château n'avait rien du tout. Il en reçoit deux cours — celle qui longe la
courtine et celle qui tourne autour du Tambour —, quatre traverses entre les
deux, et la porte de mer par où l'escalier arrive.

TROIS RÈGLES qu'on ne négocie pas :

  · TOUT EN MÈTRES, dans le repère du monde 3D (coin sud-ouest, +x levant,
    +y nord). Le décalage avec la matérialisation est (3000, 2500), et il n'est
    écrit qu'ici, dans `peyredragon.py` et dans `peyredragon_chateau.py`.

  · LE RELIEF FAIT AUTORITÉ. L'altitude de chaque point de tracé se prend dans
    `monde/peyredragon.terrain.json` — une rue suit le sol, elle ne le corrige
    pas. Deux exceptions écrites en clair : le quai est une plate-forme bâtie à
    3,4 m, et l'assise du château est arasée à 124 m.

  · AUCUNE ARÊTE SANS RAISON. Une raison n'est pas un commentaire technique :
    c'est ce qu'un homme du bourg répondrait si on lui demandait pourquoi ce
    passage existe. Le `genre` en découle — là où la pente passe 22 %, on ne
    monte pas une charrette, on taille des degrés, et `journee.js` compte alors
    l'escalier deux fois plus cher que l'artère.

Rejouable : le script REMPLACE toute la couche L1-surface du graphe et laisse
les repères (`noeuds`) intacts — c'est d'eux que `peyredragon_usages.py` tire le
quai, la porte et le sommet.
"""
import io
import json
import math
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")
sys.path.insert(0, os.path.join(RACINE, "scripts", "materialisation"))

import peyredragon as P            # noqa: E402

# Le repère : la matérialisation compte depuis le milieu de l'île, le monde 3D
# depuis le coin sud-ouest. Même décalage qu'en trois autres endroits, et
# nulle part ailleurs.
DECALAGE = (3000.0, 2500.0)

ASSISE = 124.0        # l'assise arasée du château — le relief y est taillé
PONT_QUAI = 3.4       # le tablier du quai : de la pierre posée sur l'eau

# Au-delà de cette pente, une charrette ne passe plus : on taille des degrés.
PENTE_DEGRES = 0.22
# Un tronçon plus long que ça n'a pas de nœud au milieu, et deux voisins de
# palier doivent alors marcher jusqu'au carrefour pour se rejoindre.
PAS_M = 32.0


def L(p):
    """Du repère de la matérialisation à celui du monde 3D."""
    return (p[0] + DECALAGE[0], p[1] + DECALAGE[1])


# ---------------------------------------------------------------------------
# LE SOL — le relief, et lui seul
# ---------------------------------------------------------------------------
T = json.load(io.open(os.path.join(MONDE, "peyredragon.terrain.json"),
                      encoding="utf-8"))
RES, NX, NY, ZG = T["res_m"], T["nx"], T["ny"], T["z"]


def sol(x, y):
    """L'altitude du terrain, bilinéaire sur la grille de 10 m."""
    u, v = x / RES, y / RES
    i, j = int(math.floor(u)), int(math.floor(v))
    i = max(0, min(NX - 2, i)); j = max(0, min(NY - 2, j))
    fu, fv = u - i, v - j
    a, b = ZG[j][i], ZG[j][i + 1]
    c, d = ZG[j + 1][i], ZG[j + 1][i + 1]
    return ((a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv)


# ---------------------------------------------------------------------------
# LE BOURG — les quatre chemins semés de feux, et ce qui les coud
# ---------------------------------------------------------------------------
# `q(u, v)` est EXACTEMENT le repère dans lequel `materialisation/peyredragon.py`
# a posé les soixante-sept feux : u le long de la rive depuis le milieu du quai,
# v vers l'intérieur des terres. Les reprendre ici n'est pas une commodité —
# c'est la seule façon d'avoir des rues devant lesquelles les maisons ont
# vraiment leur façade.
_UX, _UY = -P._SA, P._CA


def q(u, v):
    return L((P.QUAI[0] + _UX * u - P._D[0] * v,
              P.QUAI[1] + _UY * u - P._D[1] * v))


# Le pied de l'escalier : c'est là que tout se noue, et c'est la porte du
# village. `_lacets()` y fait arriver la montée du château.
PLACE = q(0, 26)


def _lacets():
    """Le grand escalier, tel que la matérialisation le taille dans la roche."""
    return [(x + DECALAGE[0], y + DECALAGE[1], z) for (x, y, z) in P._lacets()]


# ---------------------------------------------------------------------------
# LE CHÂTEAU — deux cours, quatre traverses, une porte
# ---------------------------------------------------------------------------
ENCEINTE = [L(P._monde(p)) for p in P.ENCEINTE]
CENTRE = (sum(p[0] for p in ENCEINTE) / len(ENCEINTE),
          sum(p[1] for p in ENCEINTE) / len(ENCEINTE))
TAMBOUR = L(P._monde((-8, -4)))       # le donjon, rayon 31
SEUIL = L(P._monde(P.PORTE))          # la porte de mer, dans l'épaisseur du mur

RETRAIT = 16.0        # ce qu'on laisse entre la cour et le pied de la courtine
RAYON_COUR = 44.0     # la cour du Tambour : hors d'atteinte d'un jet de toit
RAYON_DONJON = 31.0   # le mur du Tambour lui-même : sa porte est dessus


def _cour_haute():
    """La cour qui longe la courtine — on la parcourt sans jamais la toucher."""
    pts = []
    for (x, y) in ENCEINTE:
        d = math.hypot(x - CENTRE[0], y - CENTRE[1])
        f = (d - RETRAIT) / d
        pts.append((CENTRE[0] + (x - CENTRE[0]) * f,
                    CENTRE[1] + (y - CENTRE[1]) * f))
    return pts + pts[:1]              # elle se referme : c'est un tour de cour


# Huit pans et pas douze : les quatre traverses partent des diagonales, et il
# faut qu'elles tombent sur un SOMMET de la cour. À douze pans, elles tombaient
# entre deux — la cour du Tambour se retrouvait détachée du reste du château, et
# personne dans le donjon ne pouvait plus sortir.
def _cour_tambour(n=8):
    return [(TAMBOUR[0] + math.cos(2 * math.pi * k / n) * RAYON_COUR,
             TAMBOUR[1] + math.sin(2 * math.pi * k / n) * RAYON_COUR)
            for k in range(n)] + [(TAMBOUR[0] + RAYON_COUR, TAMBOUR[1])]


COUR_HAUTE = _cour_haute()
COUR_TAMBOUR = _cour_tambour()


def _plus_proche(p, pts):
    return min(pts, key=lambda z: (z[0] - p[0]) ** 2 + (z[1] - p[1]) ** 2)


# ---------------------------------------------------------------------------
# LA TABLE DES VOIES — une ligne, une raison
# ---------------------------------------------------------------------------
# (clef, nom, genre, largeur, sommets, raison, altitude imposée ou None)
#
# Les sommets sont DONNÉS, et le script n'en retire aucun : il ne fait qu'en
# ajouter entre deux quand l'écart passe PAS_M. C'est ce qui garantit qu'un
# raccord tombe sur un carrefour existant et non à trente mètres de là.
def _voies():
    V = []

    def v(clef, nom, genre, largeur, sommets, raison, z=None, plancher=None):
        # `z` impose une altitude, `plancher` un minimum : le débarcadère part
        # du tablier du quai et rejoint la roche, il ne plonge pas sous l'eau
        # parce que le relief, lui, y est encore à moins un.
        V.append(dict(clef=clef, nom=nom, genre=genre, largeur=largeur,
                      sommets=[tuple(s) for s in sommets], raison=raison, z=z,
                      plancher=plancher))

    # --- l'eau, la pierre posée dessus, et la place --------------------------
    v("quai", "Le quai", "quai", 26.0, [q(-78, 0), q(0, 0), q(78, 0)],
      "Cent cinquante pas de pierre en travers de la rade : tout ce qui entre "
      "à Peyredragon et tout ce qui en sort passe par ce bord-là.",
      z=PONT_QUAI)
    v("debarcadere", "Le débarcadère", "rue", 8.0, [q(0, 0), PLACE],
      "Du bord de l'eau au pied des degrés : vingt-six pas, et c'est tout ce "
      "qui sépare une barque du château.", plancher=PONT_QUAI)
    v("place-sud", None, "rue", 5.0, [PLACE, q(-40, 30)],
      "La place du pied se vide vers le sud, du côté des séchoirs et de la "
      "grève basse.")
    v("place-nord", None, "rue", 5.0, [PLACE, q(40, 30)],
      "La place du pied se vide vers le nord, du côté des maisons hautes.")

    # --- la rue du bourg, l'axe du village -----------------------------------
    v("rue-du-bourg", "La rue du bourg", "rue", 5.0,
      [q(-70, 55), q(0, 62), q(80, 58)],
      "La seule rue où deux hommes se croisent sans se ranger : elle passe "
      "derrière les maisons du bord et tient le village d'un bout à l'autre.")
    v("raccord-bourg", None, "ruelle", 3.5, [q(-40, 30), q(-70, 55)],
      "On coupait déjà par là entre deux séchoirs pour gagner la rue : à "
      "force, le passage s'est fait tout seul.")
    v("raccord-haute", None, "ruelle", 3.5, [q(80, 58), q(90, 36)],
      "Le bout de la rue du bourg butait sur le talus ; on l'a rabattu sur la "
      "rue Haute plutôt que de redescendre à la place.")

    # --- la rue Haute : on monte vers le nord, le long de la falaise ---------
    v("rue-haute", "La rue Haute", "rue", 5.0,
      [q(40, 30), q(90, 36), q(150, 44), q(250, 74), q(330, 120)],
      "Elle suit la crête au-dessus de la rade parce qu'il n'y a pas d'autre "
      "sol : à main droite c'est le vide, à main gauche c'est la roche.")

    # --- la grève et la ruelle des saleurs, au sud ---------------------------
    v("chemin-greve", "Le chemin de grève", "ruelle", 4.0,
      [q(-40, 30), q(-115, 62), q(-190, 96)],
      "L'estran est plat et il ne se laboure pas : on y marche depuis toujours "
      "pour aller aux salines sans monter par le bourg.")
    v("ruelle-saleurs", "La ruelle des Saleurs", "ruelle", 3.5,
      [q(-190, 96), q(-120, 128), q(-40, 150)],
      "Ce qui pue se met sous le vent, et sous le vent c'est en haut : la "
      "ruelle grimpe parce que les tanneurs n'ont pas eu le choix du sol.")

    # --- le grand escalier ---------------------------------------------------
    v("grand-escalier", "Le grand escalier", "escalier", 7.0, _lacets(),
      "Cent vingt mètres de dénivelé entre la rade et la porte : on ne les "
      "monte pas droit, on les monte en lacets, et on les monte à pied.")

    # --- la porte, puis les cours -------------------------------------------
    haut = _lacets()[0]
    entree = _plus_proche(SEUIL, COUR_HAUTE)
    v("porte-de-mer", "La porte de mer", "rue", 6.0,
      [(haut[0], haut[1]), SEUIL, entree],
      "La porte : elle donne sur les degrés qu'elle commande, et sur rien "
      "d'autre — c'est pour cela qu'on l'a percée là.",
      z=ASSISE)
    v("cour-haute", "Le tour de cour", "rue", 6.0, COUR_HAUTE,
      "On fait le tour des murs sans les toucher : à moins de seize pas de la "
      "courtine, ce qui tombe du chemin de ronde tombe sur vous.",
      z=ASSISE)
    v("cour-tambour", "La cour du Tambour", "rue", 5.0, COUR_TAMBOUR,
      "La cour tourne autour du donjon parce que le donjon est au milieu : "
      "tout ce qui sert la maison de la reine passe par ce rond-là.",
      z=ASSISE)

    # quatre traverses entre les deux cours — jamais dans l'axe des portes,
    # pour qu'un cheval lancé n'aille pas droit sur le Tambour
    for k, (nom, raison) in enumerate((
        (None, "La traverse du levant : de la cour du Tambour au pied du "
               "chemin de ronde, par où monte la relève."),
        (None, "La traverse du septentrion : elle mène aux cuisines et à ce "
               "qu'on y porte quatre fois le jour."),
        (None, "La traverse du couchant : les baraques d'un côté, la forge de "
               "l'autre, et les hommes qui vont de l'une à l'autre."),
        (None, "La traverse du midi : la grande salle donne dessus, et c'est "
               "par là qu'on entre quand on est attendu."))):
        a = math.pi / 4 + k * math.pi / 2
        p0 = (TAMBOUR[0] + math.cos(a) * RAYON_COUR,
              TAMBOUR[1] + math.sin(a) * RAYON_COUR)
        v("traverse-%d" % k, nom, "ruelle", 4.0,
          [p0, _plus_proche(p0, COUR_HAUTE)], raison, z=ASSISE)

    # la porte du Tambour : sur son mur, pas au milieu de la salle
    v("seuil-tambour", None, "ruelle", 3.0,
      [(TAMBOUR[0] + RAYON_COUR, TAMBOUR[1]),
       (TAMBOUR[0] + RAYON_DONJON, TAMBOUR[1])],
      "Treize pas entre la cour et le seuil du Tambour : c'est la longueur "
      "qu'il faut pour qu'un homme se fasse voir avant d'arriver.", z=ASSISE)

    # --- les deux bouts du château qui ne touchent aucune cour --------------
    v("descente-fosses", "La descente des fosses", "escalier", 5.0,
      [_plus_proche((4571.7, 2196.7), COUR_HAUTE), (4571.7, 2183.0)],
      "On n'y monte que pour les bêtes, et l'on n'y monte pas à cheval : ce "
      "qui vit au fond de la roche ne supporte pas le bruit des fers.",
      z=ASSISE)
    v("abord-baraques", None, "ruelle", 4.0,
      [_plus_proche((4356.9, 2095.7), COUR_HAUTE), (4370.0, 2095.0)],
      "Le rang des baraques est adossé au mur du couchant : on y accède par "
      "le bout, faute d'avoir laissé de la place devant.", z=ASSISE)
    return V


# ---------------------------------------------------------------------------
# LA FABRIQUE — sommets, altitude, nœuds, arêtes
# ---------------------------------------------------------------------------
def _densifier(sommets):
    """On ajoute des points entre deux sommets, on n'en retire jamais."""
    out = [(sommets[0][0], sommets[0][1])]
    for a, b in zip(sommets, sommets[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(math.ceil(d / PAS_M)))
        for k in range(1, n + 1):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def batir():
    aretes = []
    noeuds_vus = {}
    compte = {}

    def clef(p):
        return "%d:%d" % (round(p[0] * 10), round(p[1] * 10))

    def nommer(p):
        c = clef(p)
        if c not in noeuds_vus:
            noeuds_vus[c] = "pv%d" % len(noeuds_vus)
        return noeuds_vus[c]

    for voie in _voies():
        # les lacets arrivent déjà avec leur altitude taillée ; les autres la
        # prennent au relief, puis on la lisse pour qu'une rue ne tressaute pas
        # sur une grille de dix mètres.
        brut = voie["sommets"]
        if len(brut[0]) > 2:
            pts = [(x, y, z) for (x, y, z) in brut]
        else:
            pts = _densifier(brut)
            zs = [voie["z"] if voie["z"] is not None else sol(x, y) for x, y in pts]
            if voie["z"] is None:
                for _ in range(2):
                    zs = [zs[0]] + [(zs[i - 1] + 2 * zs[i] + zs[i + 1]) / 4
                                    for i in range(1, len(zs) - 1)] + [zs[-1]]
                if voie["plancher"] is not None:
                    zs = [max(z, voie["plancher"]) for z in zs]
            pts = [(x, y, z) for (x, y), z in zip(pts, zs)]

        # une arête par tronçon entre deux points : c'est ce qui donne au A* des
        # carrefours où bifurquer plutôt qu'une polyligne de mille mètres.
        for a, b in zip(pts, pts[1:]):
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            if d < 0.05:
                continue
            dz = b[2] - a[2]
            pente = dz / d
            genre = voie["genre"]
            if genre in ("rue", "ruelle") and abs(pente) > PENTE_DEGRES:
                genre = "escalier"
            compte[voie["clef"]] = compte.get(voie["clef"], 0) + 1
            aretes.append({
                "id": "%s.%d" % (voie["clef"], compte[voie["clef"]] - 1),
                "de": nommer(a), "vers": nommer(b),
                "genre": genre, "couche": "L1-surface",
                "largeur_m": voie["largeur"],
                "longueur_m": round(d, 1),
                "pente": round(pente, 3),
                "raison": voie["raison"],
                "trace": [[round(a[0], 1), round(a[1], 1), round(a[2], 1)],
                          [round(b[0], 1), round(b[1], 1), round(b[2], 1)]],
                "nom": voie["nom"],
                "visibilite": "publique",
                "acces": "public",
                "etat": "ouvert",
            })
    return aretes, noeuds_vus


def main():
    aretes, noeuds = batir()
    chemin = os.path.join(MONDE, "peyredragon.graph.json")
    G = json.load(io.open(chemin, encoding="utf-8"))
    # On remplace TOUTE la couche de surface et l'on ne touche à rien d'autre :
    # les repères du graphe (le quai, la porte, le sommet) servent à
    # `peyredragon_usages.py`, et ce n'est pas notre affaire.
    G["aretes"] = [a for a in G.get("aretes", []) if a.get("couche") != "L1-surface"]
    G["aretes"].extend(aretes)
    G["_voirie"] = ("La couche L1-surface est engendrée par "
                    "scripts/monde/peyredragon_voirie.py — ne pas l'éditer à la "
                    "main. Les repères (noeuds) viennent de "
                    "scripts/monde/peyredragon.py.")
    io.open(chemin, "w", encoding="utf-8").write(
        json.dumps(G, ensure_ascii=False, separators=(",", ":")))

    total = sum(a["longueur_m"] for a in aretes)
    print("Voirie de Peyredragon — %d arêtes, %d carrefours, %.0f m de voies"
          % (len(aretes), len(noeuds), total))
    par = {}
    for a in aretes:
        g = par.setdefault(a["genre"], [0, 0.0])
        g[0] += 1; g[1] += a["longueur_m"]
    for g, (n, m) in sorted(par.items(), key=lambda t: -t[1][1]):
        print("   %-10s %4d arêtes %8.0f m" % (g, n, m))
    print("  -> %s" % chemin)


if __name__ == "__main__":
    main()
