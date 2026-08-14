# -*- coding: utf-8 -*-
"""L'AUTORITÉ — Port-Réal en mètres.

Rien dans le monde 3D n'a le droit d'inventer une dimension : tout se prend ici.
La carte 2D (`etat/villes/port-real.json`) est en unités de dessin ; le monde est
en MÈTRES. Le pont est `METRE_PAR_UNITE`, et il n'y en a qu'un.

Le niveau 0 est l'étale de la Néra. Tout ce qui monte est positif, tout ce qui
descend (caves, égouts, galeries) est négatif — c'est ce qui rend les couches
empilables sans discussion.
"""
import math

# --- le pont entre la carte et le monde ------------------------------------
METRE_PAR_UNITE = 12.0          # 1 unité de la carte 2D = 12 m
REPERE = (0, 0, 440, 300)       # la carte
MONDE_L = REPERE[2] * METRE_PAR_UNITE   # 5 280 m d'est en ouest
MONDE_H = REPERE[3] * METRE_PAR_UNITE   # 3 600 m du nord au sud

def m(u):                        # une longueur : unités → mètres
    return u * METRE_PAR_UNITE

# La carte 2D compte les y vers le SUD (c'est un écran) ; le monde les compte
# vers le NORD (c'est une carte). Le passage se fait ici, et nulle part ailleurs.
def mx(u):
    return u * METRE_PAR_UNITE
def my(u):
    return (REPERE[3] - u) * METRE_PAR_UNITE
def ux(x_m):                     # et le retour, quand on repart du monde
    return x_m / METRE_PAR_UNITE
def uy(y_m):
    return REPERE[3] - y_m / METRE_PAR_UNITE
def mcap(deg):                   # un cap suit le miroir des y
    return -deg
def mp(p):
    return (mx(p[0]), my(p[1]))

# --- le relief --------------------------------------------------------------
# La Néra est à 0. La ville basse vit entre 6 et 18 m. Les trois collines sont
# données par leur sommet réel : c'est d'elles que sortent toutes les pentes.
NIVEAU_MER = 0.0
SOL_VILLE = 11.0
COLLINES = [                     # (centre en unités), rayon en unités, sommet en m
    ((318, 193), 46, 105.0),     # la colline d'Aegon — le Donjon Rouge la coiffe
    ((150, 182), 41,  88.0),     # la colline de Visenya
    ((276,  94), 43,  80.0),     # la colline de Rhaenys — la Fosse
]
PROFONDEUR_FLEUVE = 9.0          # la Néra sous l'étale, au chenal
PENTE_RIVE = 55.0                # sur combien de mètres la berge remonte

# --- ce que les hommes ont bâti ---------------------------------------------
MUR_HAUTEUR = 18.0               # le chemin de ronde
MUR_EPAISSEUR = 6.0
MUR_PARAPET = 2.2
PORTE_OUVERTURE = 5.0            # ce par quoi passe une charrette
PORTE_HAUTEUR = 24.0             # le corps de garde dépasse la courtine
PORTE_LARGEUR = 16.0

QUAI_LARGEUR = 14.0
QUAI_HAUTEUR = 3.5               # au-dessus de l'étale

# --- la circulation, en mètres de chaussée ----------------------------------
LARGEUR = {
    "artere": 8.0,               # deux charrettes se croisent
    "rue": 4.2,                  # une charrette, et on se range
    "ruelle": 2.0,               # un homme et son fardeau
    "escalier": 3.0,
    "quai": QUAI_LARGEUR,
    "traverse": 3.0,
    "galerie": 2.4,              # sous terre
    "egout": 2.8,
    "passage": 1.1,              # un passage secret : on s'y met de profil
    "tunnel": 2.2,
}
PENTE_MAX = {                    # au-delà, la voie devient un escalier
    "artere": 0.08, "rue": 0.12, "ruelle": 0.22, "escalier": 0.45,
}

# --- le bâti ----------------------------------------------------------------
# Une « parcelle » de la carte 2D vaut plusieurs maisons réelles : on la
# redécoupe en façades de 6 à 9 m, sauf dans le Culpucier où l'on compte en
# mètres et demi.
BATI = {
    #                    façade min/max, profondeur, niveaux, hauteur d'étage
    "La ville":            (6.5, 9.0, 11.0, (2, 3), 3.2),
    "La ville haute":      (11.0, 16.0, 16.0, (2, 3), 4.0),
    "Le Culpucier":        (3.6, 5.2,  7.5, (3, 4), 2.7),
    "Les tanneries":       (6.0, 8.5, 10.0, (1, 2), 3.4),
    "La rue d'Acier":      (6.0, 8.0, 12.0, (2, 3), 3.4),
    "Le Crochet":          (9.0, 13.0, 14.0, (2, 3), 3.8),
    "Le port et ses hangars": (14.0, 20.0, 26.0, (1, 1), 9.0),   # des hangars
    "_faubourg":           (5.0, 7.5,  8.0, (1, 2), 2.9),
}
def gabarit(quartier):
    if quartier in BATI: return BATI[quartier]
    if quartier.startswith(("Le faubourg", "Les baraques", "Le bourg")):
        return BATI["_faubourg"]
    return BATI["La ville"]

# --- L'ANNEAU : le rempart FERMÉ, en unités de la carte d'origine -----------
# Le tracé de la carte laisse un vide de deux cents mètres à chaque porte —
# c'est un schéma, et un schéma écarte le trait pour marquer l'entrée. Il faut
# pourtant un contour CLOS pour dire le dedans du dehors, et deux scripts en
# ont besoin : `densifier.py` (où l'on peut découper des îlots) et `graphe.py`
# (jusqu'où un faubourg a le droit de courir). Il vivait recopié dans le
# premier ; à deux exemplaires, un mur finit toujours par passer à deux
# endroits.
ANNEAU = [[90,132],[96,112],[118,80],[170,58],[232,48],[292,52],[336,74],[364,112],
          [374,158],[370,204],[356,236],[310,246],[246,252],[186,250],[150,244],
          [130,238],[100,206],[89,174],[88,160]]


def hors_anneau(x, y):
    """Ce point de la carte est-il hors les murs ? (unités de la carte)"""
    r = False
    j = len(ANNEAU)-1
    for i in range(len(ANNEAU)):
        if (ANNEAU[i][1] > y) != (ANNEAU[j][1] > y) and \
           x < (ANNEAU[j][0]-ANNEAU[i][0])*(y-ANNEAU[i][1]) / \
               (ANNEAU[j][1]-ANNEAU[i][1])+ANNEAU[i][0]:
            r = not r
        j = i
    return not r


def loin_du_mur(x, y):
    """La distance au rempart, en MÈTRES (unités de la carte en entrée)."""
    best = 1e18
    j = len(ANNEAU)-1
    for i in range(len(ANNEAU)):
        ax, ay = ANNEAU[j]; bx, by = ANNEAU[i]
        dx, dy = bx-ax, by-ay
        q = dx*dx + dy*dy
        t = 0 if q == 0 else max(0., min(1., ((x-ax)*dx + (y-ay)*dy)/q))
        best = min(best, math.hypot(x-ax-t*dx, y-ay-t*dy))
        j = i
    return best * METRE_PAR_UNITE


# --- LE GRAIN : ce qui distingue un quartier dense d'un quartier lâche ------
# Le gabarit ci-dessus dit la TAILLE d'une maison ; il ne disait rien de la
# façon dont deux maisons se touchent, ni de la profondeur d'un îlot. C'était
# la même trame partout, de la ville haute au Culpucier — donc pas de gradient,
# donc une ville qui se lit d'un bloc.
#
#   joint    l'écart entre deux façades voisines, en mètres. Une maison
#            médiévale est MITOYENNE : elle partage son mur, et le joint est
#            nul. Ce qui s'écarte, ce sont les demeures qui se veulent isolées
#            et les faubourgs, qui ne sont pas encore une ville.
#   bloc_m   au-delà de cette profondeur, l'îlot se coupe : c'est le pas de la
#            trame. Vingt-six mètres au Culpucier (deux rangs dos à dos et rien
#            d'autre), soixante-dix au faubourg (des jardins entre les maisons).
GRAIN = {
    "La ville":            (0.15, 56.0),
    "La ville haute":      (0.60, 76.0),
    "Le Culpucier":        (0.00, 26.0),
    "Les tanneries":       (0.20, 52.0),
    "La rue d'Acier":      (0.20, 60.0),
    "Le Crochet":          (0.35, 68.0),
    "Le port et ses hangars": (1.20, 90.0),
    "_faubourg":           (1.80, 70.0),
}
BLOC_MIN = 22.0                  # en deçà, on ne coupe plus : il n'y tiendrait rien
ENTRE_RANGS = 0.8                # le défaut, quand le quartier n'est pas connu
COEUR = 6.0                      # ce qu'on laisse au milieu de l'îlot : la cour

# --- LE DOS-À-DOS : ce qui sépare deux rangs qui se tournent le dos ---------
# `joint` dit comment deux VOISINES se touchent le long de la rue. Il ne disait
# rien de ce qui sépare deux RANGS, et c'était `ENTRE_RANGS = 0,80` partout, du
# taudis à l'hôtel. Conséquence mesurée : les gabarits variaient bien — 4,3 × 7,5
# au Culpucier contre 11,6 × 16 en ville haute — mais la PART DE SOL bâtie, non.
# Tout l'intra-muros sortait entre 40 et 46 % d'occupation, du plus misérable au
# plus riche. C'est exactement ce que `GRAIN` avait été écrit pour empêcher, et
# c'est le chiffre qui fait qu'on sait où l'on est sans lire le nom du quartier.
#
#   Culpucier    rien du tout : deux rangs partagent leur mur de fond.
#   la ville     un jour de service, la largeur d'un homme de profil.
#   ville haute  une cour derrière chaque hôtel.
#   faubourg     un jardin, et c'est ce qui en fait un faubourg.
DOS_A_DOS = {
    "La ville":            0.4,
    "La ville haute":      2.5,
    "Le Culpucier":        0.0,
    "Les tanneries":       0.6,
    "La rue d'Acier":      0.5,
    "Le Crochet":          1.6,
    "Le port et ses hangars": 2.0,
    "_faubourg":           6.0,
}

def dos(quartier):
    """l'écart entre deux rangs qui se tournent le dos, en mètres"""
    if quartier in DOS_A_DOS: return DOS_A_DOS[quartier]
    if quartier.startswith(("Le faubourg", "Les baraques", "Le bourg")):
        return DOS_A_DOS["_faubourg"]
    return DOS_A_DOS["La ville"]

# Ce qui reste entre la chaussée et la façade. Une artère a de quoi laisser
# passer un banc et un étal ; une ruelle n'a rien du tout. Le semis et la
# cuisson du plan 2D doivent lire la MÊME table : tant qu'ils divergeaient de
# cinq centimètres, la quasi-totalité des maisons de ruelle comptait comme
# empiétant sur la chaussée, et le plan les repoussait toutes pour rien.
TROTTOIR = {"artere": 1.5, "rue": 1.0, "quai": 1.5, "abord": 1.0,
            "ruelle": 0.5, "escalier": 0.4}
MARGE_RECUL = 0.25               # de quoi absorber l'arrondi et le grain du tracé

def recul(genre):
    """de l'axe de la voie à la façade, pour une voie de ce genre"""
    return LARGEUR.get(genre, 2.3)/2. + TROTTOIR.get(genre, 0.5) + MARGE_RECUL
RECUL = recul("ruelle")          # le cas le plus fréquent, pour l'arithmétique d'îlot

def grain(quartier):
    """(joint_m, bloc_max_m) — comment ce quartier se serre."""
    if quartier in GRAIN: return GRAIN[quartier]
    if quartier.startswith(("Le faubourg", "Les baraques", "Le bourg")):
        return GRAIN["_faubourg"]
    return GRAIN["La ville"]

def ilot_min(quartier):
    """La largeur SOUS LAQUELLE un îlot ne vaut plus rien : celle où l'on ne
    peut plus border ses deux côtés. Deux reculs et deux profondeurs de
    parcelle, dos à dos, et rien au milieu.

    C'est la mesure qui manquait. On coupait les îlots jusqu'à ce que leur plus
    grande dimension passe sous un seuil, en les divisant PAR DEUX à chaque
    fois : ils finissaient à la moitié du seuil, donc trop minces pour porter
    des maisons des deux côtés. Résultat, une rue sur deux donnait dans le vide
    et la ville était bâtie à 35 % de son sol au lieu de 65.
    """
    return 2*(recul("ruelle") + gabarit(quartier)[2])

def ilot_cible(quartier):
    """La largeur qu'on VISE pour un îlot : deux fronts complets dos à dos, et
    une cour au milieu. C'est la mesure que la coupe doit atteindre — elle
    découpe en bandes de cette largeur au lieu de diviser par deux, sans quoi
    elle ne tombe jamais dessus et l'on obtient soit des lanières trop minces
    pour deux fronts, soit des îlots dont le cœur est un terrain vague.
    """
    return 2*(recul("ruelle") + rangs(quartier)*gabarit(quartier)[2]) + COEUR

def rangs(quartier):
    """Combien de rangs de maisons l'îlot de ce quartier peut porter — 1 ou 2.

    Ce n'est pas un réglage : c'est une soustraction. Un îlot de profondeur D
    borde deux rues ; chacune veut son recul, puis un ou deux rangs, et il doit
    rester de quoi faire une cour au milieu. Quand on l'écrit à la main, on se
    trompe — et l'erreur ne se voit pas sur le plan : elle se voit à ce que le
    second rang tombe DANS LA RUE D'EN FACE, donc qu'il se rattache à la
    mauvaise voie, donc que sa façade regarde le mauvais côté.
    """
    _, bloc = grain(quartier)
    prof = gabarit(quartier)[2]
    besoin2 = 2*(RECUL + 2*prof + ENTRE_RANGS) + COEUR
    return 2 if bloc >= besoin2 else 1

# --- les niveaux, sous la surface -------------------------------------------
# Pas un vide sous la ville : quatre familles, à quatre profondeurs, et qui ne
# communiquent qu'aux endroits qu'on aura nommés.
NIVEAUX = {
     0: ("surface",       0.0,  "Ce qu'on voit"),
    -1: ("caves",        -4.5,  "Caves, celliers, services : sous chaque maison"),
    -2: ("egouts",      -10.0,  "Égouts, drains, citernes : ils suivent la pente"),
    -3: ("ancien",      -18.0,  "Cryptes, fondations, galeries d'avant la ville"),
}
HAUTEUR_SOUS_PLAFOND = {"caves": 2.6, "egouts": 2.9, "ancien": 3.4}

# --- ce que la carte 2D exagère --------------------------------------------
# Un dessin lisible grossit ses monuments : sur la carte, le Donjon Rouge fait
# 60 unités de large, ce qui donne 720 m une fois métrisé — deux fois trop. On
# ne touche pas au dessin (il est juste POUR un dessin) : on corrige ici, et
# seulement pour le monde. La valeur est la plus grande dimension réelle.
TAILLE_REELLE = {
    "Le Donjon Rouge": 330.0,          # la forteresse et ses sept tours
    "La Fosse aux Dragons": 240.0,     # le dôme de Maegor
    "Le vieux septuaire": 110.0,
    "La Guilde des Alchimistes": 70.0,
    "Les casernes du Guet": 95.0,
    "La tour de la Main": 24.0,
    "Le bureau du maître de port": 26.0,
    "Le hangar du chantier": 40.0,
    "La grande place": 135.0,
    "Le marché aux chevaux": 105.0,
    "Le marché aux poissons": 85.0,
    "L'aire de bris": 150.0,
}
def polygone_reel(nom, points):
    """rétrécit un polygone de carte (en unités) vers sa taille réelle"""
    cible = TAILLE_REELLE.get(nom)
    if not cible or not points: return points
    cx = sum(p[0] for p in points)/len(points)
    cy = sum(p[1] for p in points)/len(points)
    grand = max(max(abs(p[0]-cx) for p in points)*2,
                max(abs(p[1]-cy) for p in points)*2) * METRE_PAR_UNITE
    if grand <= cible: return points
    k = cible/grand
    return [[cx + (p[0]-cx)*k, cy + (p[1]-cy)*k] for p in points]

def hauteur_sol(x, y, dans_eau=False, dist_rive=999.0):
    """Le terrain, en mètres, au point (x, y) donné EN UNITÉS de carte."""
    h = SOL_VILLE
    for (cx, cy), r, sommet in COLLINES:
        d = math.hypot(x - cx, y - cy)
        if d < r:
            h += (sommet - SOL_VILLE) * (1 - (d / r) ** 2) ** 1.4
    if dans_eau:
        # le chenal se creuse en s'éloignant de la rive
        return -min(PROFONDEUR_FLEUVE, 1.0 + m(dist_rive) / 40.0)
    if m(dist_rive) < PENTE_RIVE:      # la berge remonte, elle ne saute pas
        t = m(dist_rive) / PENTE_RIVE
        t = t * t * (3 - 2 * t)
        return 0.4 + (h - 0.4) * t
    return h

if __name__ == "__main__":
    print("Port-Réal, l'autorité :")
    print("  1 unité de carte  = %.0f m" % METRE_PAR_UNITE)
    print("  le monde          = %.0f × %.0f m" % (MONDE_L, MONDE_H))
    print("  colline d'Aegon   = %.0f m au sommet" % COLLINES[0][2])
    print("  mur               = %.0f m de haut, %.0f d'épaisseur" % (MUR_HAUTEUR, MUR_EPAISSEUR))
    print("  artère            = %.1f m de chaussée" % LARGEUR["artere"])
    print("  ruelle            = %.1f m" % LARGEUR["ruelle"])
