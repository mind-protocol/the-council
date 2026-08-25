# -*- coding: utf-8 -*-
"""LA PRISE DE PLACE — ce qu'une maison fait du terrain qu'elle a derrière.

    python scripts/monde/annexes.py    (après usages.py, avant degager_voirie.py)

POURQUOI. La pose donne à chaque maison un rectangle de gabarit, et s'arrête là.
Or personne ne laisse un fond de parcelle vide : on y met un appentis, un bûcher,
une resserre, une écurie, un mur de cour. C'est ce qui manque au tissu — le fond
d'îlot reste en friche alors qu'il devrait être un fouillis de remises, et le
plan montre des rangs propres séparés par du rien.

CE QU'ON FAIT. Pour chaque bâtiment, on mesure le terrain LIBRE autour de lui —
derrière, à gauche, à droite —, on retranche ce qu'il faut laisser pour passer,
et l'on décide s'il prend et de combien. Trois colonnes s'ajoutent au bâti :

    ann_f   ce qu'il prend au FOND, en mètres (la remise, le bûcher)
    ann_g   ce qu'il prend à GAUCHE (l'appentis contre le mur mitoyen)
    ann_d   ce qu'il prend à DROITE

CE QUI DÉCIDE, et ce n'est pas le hasard seul :

  • LE MÉTIER. Une forge veut son charbon à l'abri, un entrepôt veut sa cour, un
    marchand veut sa resserre. Un taudis n'a rien à ranger et pas les moyens du
    bois. La table `APPETIT` dit qui prend, et jusqu'où.
  • LA PLACE. On ne prend que ce qui est libre, et l'on garde toujours un jour
    de dégagement — sans quoi l'annexe se colle au voisin et l'on ne passe plus.
  • JAMAIS SUR LA RUE. Le devant est sacré : une annexe pousse au fond et sur
    les flancs, jamais vers la chaussée. C'est la règle qui garde le front de
    rue lisible, et c'est aussi ce qui empêche l'annexe de manger le chemin.

CE QUE ÇA NE FAIT PAS. Aucune maison ne bouge, aucun rang ne change : les rangs
sont l'ancrage des affectations (`scripts/affecter.py`). On n'ajoute que trois
nombres par bâtiment ; c'est `plan_ville.py` qui en tire des morceaux de
silhouette, et ils se soudent au parent puisqu'ils lui appartiennent.
"""
import json, io, math, os, sys
from collections import Counter

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")
PREFIXE = sys.argv[1] if len(sys.argv) > 1 else "portreal"

CHEMIN = os.path.join(MONDE, PREFIXE + ".bati.json")
B = json.load(io.open(CHEMIN, encoding="utf-8"))
G = json.load(io.open(os.path.join(MONDE, PREFIXE + ".graph.json"), encoding="utf-8"))
C = {n: i for i, n in enumerate(B["_colonnes"])}

if "ann_f" in C or "mur_d" in C:
    sys.exit("Ce bâti porte déjà ses annexes. Relance usages.py pour repartir.")
for besoin in ("usage", "cat"):
    if besoin not in C:
        sys.exit("  %s manque : lance d'abord usages.py." % besoin)

# --- qui prend, et jusqu'où -------------------------------------------------
# (part de ceux qui prennent, fond max en m, flanc max en m)
# Un artisan encombre : il lui faut du bois, de l'eau, de la matière et un
# endroit pour la puanteur. Un taudis n'a ni bien ni bois pour le couvrir.
APPETIT = {
    "forge":         (0.95, 15.0, 4.0),
    "tannerie":      (0.98, 19.0, 4.5),
    "teinturerie":   (0.95, 17.0, 4.0),
    "poterie":       (0.95, 16.0, 4.0),
    "brasserie":     (0.92, 15.0, 4.0),
    "boulangerie":   (0.88, 10.0, 3.5),
    "abattoir":      (0.95, 19.0, 4.5),
    "corderie":      (0.92, 18.0, 4.0),
    "voilerie":      (0.90, 15.0, 4.0),
    "moulin":        (0.72, 10.0, 3.5),
    "entrepot":      (0.92, 20.0, 5.0),
    "chantier-bois": (0.95, 22.0, 5.0),
    "echoppe":       (0.72, 9.0, 3.0),
    "taverne":       (0.78, 11.0, 3.5),
    "auberge":       (0.88, 15.0, 4.0),
    "ecurie":        (0.92, 17.0, 4.5),
    "etuve":         (0.80, 11.0, 3.5),
    "manse":         (0.88, 19.0, 5.0),
    "maison-officier": (0.84, 15.0, 4.0),
    "maison":        (0.68, 11.0, 3.0),
    "cabane":        (0.52, 7.0, 2.5),
    "taudis":        (0.26, 5.0, 1.8),
}
DEFAUT = (0.55, 8.0, 2.5)

JOUR = 0.6          # le dégagement qu'on laisse toujours autour de l'annexe
MINI = 1.4          # sous quoi ce n'est plus une remise mais une niche
BORD_RUE = 1.0      # on ne s'approche jamais de la chaussée de moins que ça
SOI = 2.0           # l'épaisseur de sa propre coquille dans la trame


def melange(k):
    """un tirage stable par bâtiment : même maison, même appétit"""
    h = (k*2654435761 + 1013904223) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h*1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFFFF)/4294967296.0


# --- la trame de ce qui est déjà pris ---------------------------------------
print("… le sol déjà pris")
CEL = 1.0
xs = [r[C["x"]] for r in B["bati"]]
ys = [r[C["y"]] for r in B["bati"]]
X0, Y0 = min(xs) - 40, min(ys) - 40
NX = int((max(xs) + 40 - X0)/CEL) + 1
NY = int((max(ys) + 40 - Y0)/CEL) + 1
# DEUX TRAMES, PAS UNE. Une annexe ne veut savoir qu'une chose — « est-ce
# libre ? » — mais un MUR DE CLÔTURE en veut deux : il doit REJOINDRE une
# maison, donc il lui faut trouver du bâti ; et il ne doit jamais franchir une
# rue, donc il lui faut la reconnaître. Confondues, on ne peut ni l'un ni l'autre.
MURS_BAT = bytearray(NX*NY)
MURS_RUE = bytearray(NX*NY)


def marque(x, y, buf):
    i, j = int((x - X0)/CEL), int((y - Y0)/CEL)
    if 0 <= i < NX and 0 <= j < NY:
        buf[j*NX + i] = 1


def marque_rectangle_local(x, y, ca, sa, u0, u1, v0, v1):
    """Réserve une annexe acceptée avant de traiter la maison suivante."""
    nu = max(1, int((u1 - u0)/CEL) + 1)
    nv = max(1, int((v1 - v0)/CEL) + 1)
    for iu in range(nu + 1):
        for iv in range(nv + 1):
            u = u0 + (u1 - u0)*iu/nu
            v = v0 + (v1 - v0)*iv/nv
            marque(x + u*ca - v*sa, y + u*sa + v*ca, MURS_BAT)


for r in B["bati"]:
    a = math.radians(r[C["cap"]] or 0.)
    ca, sa = math.cos(a), math.sin(a)
    f, p = r[C["facade_m"]]/2., r[C["profondeur_m"]]/2.
    nf = max(2, int(r[C["facade_m"]]/CEL)) + 1
    np_ = max(2, int(r[C["profondeur_m"]]/CEL)) + 1
    for u in range(nf + 1):
        for v in range(np_ + 1):
            dx = -f + 2*f*u/nf
            dy = -p + 2*p*v/np_
            marque(r[C["x"]] + dx*ca - dy*sa, r[C["y"]] + dx*sa + dy*ca, MURS_BAT)

# la chaussée : une annexe n'y pousse jamais, et l'on s'en écarte encore un peu
for a in G["aretes"]:
    if a.get("couche") != "L1-surface":
        continue
    t = a.get("trace") or []
    w = (a.get("largeur_m") or 3)/2. + BORD_RUE
    nw = max(1, int(w/CEL))
    for u, v in zip(t, t[1:]):
        L = math.hypot(v[0] - u[0], v[1] - u[1])
        n = max(1, int(L/CEL))
        for k in range(n + 1):
            x = u[0] + (v[0] - u[0])*k/n
            y = u[1] + (v[1] - u[1])*k/n
            for di in range(-nw, nw + 1):
                for dj in range(-nw, nw + 1):
                    if math.hypot(di, dj)*CEL <= w:
                        marque(x + di*CEL, y + dj*CEL, MURS_RUE)
print("   %d x %d cases de %.0f m" % (NX, NY, CEL))


def _case(x, y):
    i, j = int((x - X0)/CEL), int((y - Y0)/CEL)
    return (j*NX + i) if (0 <= i < NX and 0 <= j < NY) else None

def libre(x, y):
    k = _case(x, y)
    return k is not None and not MURS_BAT[k] and not MURS_RUE[k]

def sur_bati(x, y):
    k = _case(x, y)
    return k is not None and MURS_BAT[k]

def sur_rue(x, y):
    k = _case(x, y)
    return k is not None and MURS_RUE[k]


def place(x, y, ca, sa, du, dv, larg, portee):
    """Jusqu'où l'on peut s'étendre dans cette direction, en mètres.

    On avance par demi-mètre en sondant TOUTE la largeur de l'annexe : une
    remise ne se faufile pas, elle a besoin de son emprise entière. On s'arrête
    au premier pas qui touche quelque chose, et l'on retranche le jour.
    """
    # les axes du monde pour la direction d'extension et sa perpendiculaire
    ex, ey = du*ca - dv*sa, du*sa + dv*ca
    px, py = -ey, ex

    def degage(s2):
        for t in (-0.5, -0.25, 0.0, 0.25, 0.5):
            if not libre(x + ex*s2 + px*larg*t, y + ey*s2 + py*larg*t):
                return False
        return True

    # ON FRANCHIT D'ABORD SA PROPRE COQUILLE. La trame fait un mètre et l'on
    # arrondit à la case : l'emprise du bâtiment déborde donc d'un demi-mètre
    # au-delà de son mur, et la sonde partie du mur se cognait dans SA PROPRE
    # maison au premier pas. Résultat mesuré : dix-neuf mille bâtiments
    # « sans place » qui avaient tout le fond de parcelle devant eux, et un
    # pour cent de prise au lieu de la moitié de la ville.
    s = 0.0
    while s < SOI and not degage(s + 0.5):
        s += 0.5
    if s >= SOI:
        return 0.0          # quelque chose est vraiment collé au mur
    depart = s
    while s < portee + depart:
        if not degage(s + 0.5):
            break
        s += 0.5
    return max(0.0, s - depart - JOUR)


# --- on prend ---------------------------------------------------------------
print("… la prise de place")
compte = Counter()
gagne = 0.0
ANN = []
for k, r in enumerate(B["bati"]):
    a = math.radians(r[C["cap"]] or 0.)
    ca, sa = math.cos(a), math.sin(a)
    f, p = r[C["facade_m"]]/2., r[C["profondeur_m"]]/2.
    x, y = r[C["x"]], r[C["y"]]
    part, fond_max, flanc_max = APPETIT.get(r[C["usage"]], DEFAUT)
    d = melange(k)
    if d > part:
        ANN.append((0.0, 0.0, 0.0))
        compte["rien"] += 1
        continue
    # le tirage sert deux fois : qui prend, et combien. On le décale pour ne pas
    # corréler l'un à l'autre.
    e = melange(k + 7919)
    # LE FOND — c'est là que va la remise. On sonde depuis l'arrière (dv = +p).
    xf = x - sa*p
    yf = y + ca*p
    fond = place(xf, yf, ca, sa, 0.0, 1.0, r[C["facade_m"]]*0.8, fond_max + JOUR)
    fond = min(fond, fond_max) * (0.45 + 0.55*e)
    if fond < MINI:
        fond = 0.0
    # LES FLANCS — l'appentis, plus étroit, et seulement si le fond n'a rien pris
    # ou si le métier encombre vraiment.
    g = dd = 0.0
    if flanc_max >= 2.0 and (fond == 0.0 or part > 0.7):
        xg, yg = x - ca*f, y - sa*f
        xd, yd = x + ca*f, y + sa*f
        g = place(xg, yg, ca, sa, -1.0, 0.0, r[C["profondeur_m"]]*0.6, flanc_max + JOUR)
        dd = place(xd, yd, ca, sa, 1.0, 0.0, r[C["profondeur_m"]]*0.6, flanc_max + JOUR)
        g = min(g, flanc_max) * (0.4 + 0.6*melange(k + 104729))
        dd = min(dd, flanc_max) * (0.4 + 0.6*melange(k + 15485863))
        if g < MINI: g = 0.0
        if dd < MINI: dd = 0.0
    ANN.append((round(fond, 1), round(g, 1), round(dd, 1)))
    if fond or g or dd:
        compte["prend"] += 1
        gagne += (fond*r[C["facade_m"]]*0.8 + (g + dd)*r[C["profondeur_m"]]*0.6)
        # Sans cette réservation, deux maisons dos à dos pouvaient chacune
        # mesurer le même terrain comme libre et y pousser l'une dans l'autre.
        if fond:
            marque_rectangle_local(x, y, ca, sa, -f*.40, f*.40, p, p + fond)
        if g:
            marque_rectangle_local(x, y, ca, sa, -f - g, -f, -p*.30, p*.30)
        if dd:
            marque_rectangle_local(x, y, ca, sa, f, f + dd, -p*.30, p*.30)
    else:
        compte["pas la place"] += 1

# --- LES MURS DE CLÔTURE ----------------------------------------------------
# Entre deux maisons du même front, il reste souvent trois ou six mètres. Ce
# n'est pas assez pour bâtir, c'est bien assez pour un MUR : on ferme la cour
# sur la rue, et le front redevient continu. C'est ce qui fait qu'une rue
# médiévale est un couloir et non une file d'objets posés.
#
# Le mur suit la LIGNE DE FAÇADE, donc il est parallèle à la voirie. Il part du
# bord droit de la maison et cherche la suivante ; on ne le note qu'à DROITE,
# sans quoi chaque intervalle serait muré deux fois — une fois par chacun de
# ses voisins.
MUR_MAX = 14.0      # au-delà, ce n'est plus une cour mais un terrain
MUR_MIN = 1.2       # en deçà, les maisons se touchent déjà
EPAISSEUR = 0.6

print("… les murs de clôture")
MUR = []
nmur = 0
for k, r in enumerate(B["bati"]):
    a = math.radians(r[C["cap"]] or 0.)
    ca, sa = math.cos(a), math.sin(a)
    f, p = r[C["facade_m"]]/2., r[C["profondeur_m"]]/2.
    # le bord droit de la façade, en coordonnées du monde
    bx = r[C["x"]] + f*ca + p*sa
    by = r[C["y"]] + f*sa - p*ca
    s_ = 0.0
    trouve = 0.0
    # on franchit d'abord sa propre coquille, comme pour les annexes
    while s_ < SOI and sur_bati(bx + ca*(s_ + 0.5), by + sa*(s_ + 0.5)):
        s_ += 0.5
    depart = s_
    while s_ - depart < MUR_MAX:
        s_ += 0.5
        qx, qy = bx + ca*s_, by + sa*s_
        if sur_rue(qx, qy):
            break                      # un mur ne barre jamais une rue
        if sur_bati(qx, qy):
            trouve = s_ - depart       # on a rejoint le voisin
            break
    if MUR_MIN <= trouve <= MUR_MAX:
        MUR.append(round(trouve, 1))
        nmur += 1
    else:
        MUR.append(0.0)
print("   %d murs de clôture (%.0f %% des maisons)" % (nmur, 100.*nmur/len(B["bati"])))

B["_colonnes"] = B["_colonnes"] + ["ann_f", "ann_g", "ann_d", "mur_d"]
for r, (fo, g, dd), mu in zip(B["bati"], ANN, MUR):
    r.append(fo)
    r.append(g)
    r.append(dd)
    r.append(mu)
io.open(CHEMIN, "w", encoding="utf-8").write(
    json.dumps(B, ensure_ascii=False, separators=(",", ":")))

n = len(B["bati"])
print()
print("  %s" % os.path.relpath(CHEMIN, RACINE))
print("  %d batiments prennent de la place (%.0f %%)" % (compte["prend"], 100.*compte["prend"]/n))
print("  %d n'y ont pas droit, %d n'ont pas la place"
      % (compte["rien"], compte["pas la place"]))
print("  emprise gagnee : %.2f ha" % (gagne/1e4))
print()
print("  puis : degager_voirie.py, portes.py, marche.py --cache, plan_ville.py")
