# -*- coding: utf-8 -*-
"""LE PLAN DES LEVÉS — les marches de Marlo, en carte de métro.

    python scripts/plan_leves.py > ecrans/leves.svg

POURQUOI CETTE FIGURE ET PAS UNE CARTE. Marlo ne peut pas dessiner Port-Réal :
il ne l'a jamais vue d'en haut, et personne ne la lui montrera. Ce qu'il a, ce
sont des LIGNES — des marches comptées au pas, avec des bornes, des pentes et
des maisons. Un plan de métro dit exactement cela et rien de plus : l'ordre des
choses et la distance vécue entre elles, sans prétendre à une forme.

C'est donc la figure la plus honnête qu'on puisse tirer de sa méthode. Les
lignes qui se croisent sont des endroits où il est passé deux fois ; les blancs
entre les lignes sont des quartiers où il n'a jamais mis les pieds, et ils
doivent rester blancs.

CE QUE PORTE CHAQUE TRONÇON : les pas (l'épaisseur du trait ne dit rien, la
longueur oui), le compte des maisons, et la pente en quatre degrés — un chevron
par degré, pointé vers le haut si l'on monte.
"""
import io, json, math, os, random, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVES = os.path.join(RACINE, "etat", "leves.json")

# Encre et papier : ceux du jeu, pour que la page ne jure pas avec le reste.
# PARCHEMIN. Ce document n'est pas une pièce d'interface : c'est un objet que
# Marlo a dessiné à la chandelle, sur des rognures de peau grattées deux fois.
# Il doit en avoir la couleur, les taches, et l'encre de noix de galle.
PARCHEMIN = "#e8dcc0"
TACHE = "#d9c9a3"
ENCRE = "#3b2a17"
PALE = "#7a6647"
SANG = "#8c3a2a"          # la rubrication : ce qu'on veut relire d'abord
COULEURS = ["#3b2a17", "#5c4a2a", "#6b3f2a", "#3f4a33", "#57406b", "#2f4550"]
# Une main, pas une police d'écran. On ne charge rien : la page doit tenir seule,
# donc on demande les cursives du système et l'on retombe sur une serif.
MAIN = "'Segoe Script', 'Brush Script MT', 'Lucida Handwriting', cursive"
PLUME = "'Palatino Linotype', 'Book Antiqua', Georgia, serif"

PAS_PAR_PX = 3.2          # un pixel pour six pas : la ville tient dans la page
MIN_PX = 62.0             # aucun tronçon plus court que ça, ou l'on ne lit plus
MARGE = 90.0


def degre_n(mot):
    return {"plat": 0, "ça monte": 1, "ça tire": 2, "on souffle": 3}.get(mot, 0)


def octo(a, b):
    """Un coude à 45° entre deux points : la règle du plan de métro."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    if abs(dx) < 1 or abs(dy) < 1 or abs(abs(dx) - abs(dy)) < 1:
        return [a, b]
    if abs(dx) > abs(dy):                      # on file droit puis on biaise
        c = (x0 + (abs(dx) - abs(dy)) * (1 if dx > 0 else -1), y0)
    else:
        c = (x0, y0 + (abs(dy) - abs(dx)) * (1 if dy > 0 else -1))
    return [a, c, b]


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    if not os.path.exists(LEVES):
        sys.stderr.write("etat/leves.json manque — lance scripts/arpenter.py --leve\n")
        sys.exit(1)
    T = json.load(io.open(LEVES, encoding="utf-8"))["leves"]
    # Une planche par marche, si on le demande. Superposer tous les levés donne
    # la carte de tout ce qu'il connaît ; n'en montrer qu'un donne la feuille
    # qu'il vient d'écrire, et c'est souvent celle-là qu'on veut regarder.
    a = sys.argv[1:]
    if "--dernier" in a:
        T = T[-1:]
    elif a and not a[0].startswith("-"):
        garde = set(a)
        T = [x for x in T if x.get("id") in garde] or T
    if not T:
        sys.stderr.write("aucun levé.\n")
        sys.exit(1)

    # --- où poser les bornes ------------------------------------------------
    # AU CAP, comme on chemine. Marlo ne sait pas un azimut, mais il sait les
    # huit aires de vent : la mer est au nord, la rivière au levant, le soleil
    # fait le reste. Chaque tronçon part donc dans SA direction, sur SA longueur.
    # C'est un cheminement à l'estime — le procédé de tout arpenteur sans
    # instrument, et le seul qui produise une figure où l'on puisse dire de
    # chaque rue où elle va.
    #
    # Ce que ça coûte : les marches ne se referment pas exactement. Deux lignes
    # qui passent au même puits l'y posent à quelques pas l'une de l'autre. On ne
    # corrige pas — c'est l'erreur de fermeture, tout levé à l'estime en a une,
    # et la cacher serait le seul vrai mensonge de ce document.
    ancres = {}            # ref -> (x, y), première pose
    lignes = []
    depart = [MARGE * 2.2, 0.0]
    for k, L in enumerate(T):
        clefs = [(b.get("ref") or ("%s#%d" % (L["id"], i)))
                 for i, b in enumerate(L["bornes"])]
        # On part d'une borne déjà connue si la marche en croise une : c'est ce
        # qui accroche les levés entre eux.
        base, décalage = None, 0
        for i, c in enumerate(clefs):
            if c in ancres:
                base, décalage = ancres[c], i
                break
        pts = [(0.0, 0.0)]
        for t in L["troncons"]:
            d = max(MIN_PX, t["pas"] / PAS_PAR_PX)
            a = math.radians(t.get("cap", 0))
            # y descend à l'écran : le nord est en haut, comme sur toute carte.
            pts.append((pts[-1][0] + d * math.cos(a), pts[-1][1] - d * math.sin(a)))
        if base is None:
            ox, oy = depart[0], depart[1] + MARGE * 1.6
            depart[1] += 40
        else:
            ox = base[0] - pts[min(décalage, len(pts) - 1)][0]
            oy = base[1] - pts[min(décalage, len(pts) - 1)][1]
        pts = [(x + ox, y + oy) for (x, y) in pts]
        for i, c in enumerate(clefs):
            if i < len(pts):
                ancres.setdefault(c, pts[i])
        L_ = {"leve": L, "pts": pts, "clefs": clefs,
              "couleur": COULEURS[k % len(COULEURS)]}
        lignes.append(L_)

    # on recadre pour que tout tienne dans la page
    mx = min(p[0] for l in lignes for p in l["pts"])
    my = min(p[1] for l in lignes for p in l["pts"])
    for l in lignes:
        l["pts"] = [(x - mx + MARGE * 1.8, y - my + MARGE * 1.6) for (x, y) in l["pts"]]

    # ---------------------------------------------------------------- le dessin
    # ON SIMULE SA MAIN. Ce n'est pas un plan d'imprimeur : c'est un homme qui
    # dessine a la chandelle, sur de la peau grattee deux fois, avec trois plumes
    # taillees et de l'encre de noix de galle. Le trait tremble, les carres ne
    # sont pas d'equerre, l'ecriture penche.
    #
    # LA METAPHORE DU METRO ETAIT UNE INTENTION, PAS UNE FORME : on en garde la
    # seule idee qui vaille — ne dire que l'ordre et les distances vecues — et
    # l'on jette tout le reste. Pas de stations, pas de lignes de couleur : une
    # route a l'encre, des maisons, et ce qu'on longe ecrit AU BORD.
    #
    # Le tremblement est tire d'une GRAINE : le meme leve redonne le meme dessin.
    # Une carte qui change de forme a chaque regard n'est pas un objet.
    rnd = random.Random(11)

    def trembler(x, y, a=1.6):
        return (x + rnd.uniform(-a, a), y + rnd.uniform(-a, a))

    def courbe(pts):
        """Une route ne va pas droit. Courbe douce passant par les points."""
        if len(pts) < 2:
            return ""
        P = [pts[0]] + list(pts) + [pts[-1]]
        d = "M %.1f %.1f" % pts[0]
        for i in range(1, len(P) - 2):
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
            d += " C %.1f %.1f %.1f %.1f %.1f %.1f" % (c1 + c2 + p2)
        return d

    # Ce qu'un homme dessine pour dire ce qu'il longe. Trois traits, pas plus :
    # il n'est pas enlumineur, il note.
    def glyphe(nom, x, y):
        n = (nom or "").lower()
        E = ENCRE
        if "puits" in n:
            return ('<circle cx="%.1f" cy="%.1f" r="3.6" fill="none" stroke="%s" '
                    'stroke-width="1.2"/><path d="M %.1f %.1f h 9" stroke="%s" '
                    'stroke-width="1.2"/>' % (x, y, E, x - 4.5, y - 5.5, E))
        if "forge" in n:
            return ('<path d="M %.1f %.1f h 10 l -2.5 4.5 h -5 z" fill="none" '
                    'stroke="%s" stroke-width="1.2"/><path d="M %.1f %.1f v 5" '
                    'stroke="%s" stroke-width="1.2"/>'
                    % (x - 5, y - 3, E, x, y + 1.5, E))
        if "four" in n:
            return ('<path d="M %.1f %.1f a 5 5 0 0 1 10 0 z" fill="none" '
                    'stroke="%s" stroke-width="1.2"/>' % (x - 5, y + 2, E))
        if "septuaire" in n:
            return ('<path d="M %.1f %.1f v 10 M %.1f %.1f h 8" stroke="%s" '
                    'stroke-width="1.2" fill="none"/>'
                    % (x, y - 5, x - 4, y - 1, E))
        if "garde" in n or "porte" in n:
            return ('<path d="M %.1f %.1f v -9 h 9 v 9" fill="none" stroke="%s" '
                    'stroke-width="1.3"/>' % (x - 4.5, y + 4, E))
        if "march" in n:
            return ('<path d="M %.1f %.1f h 11 M %.1f %.1f v 5 M %.1f %.1f v 5" '
                    'fill="none" stroke="%s" stroke-width="1.2"/>'
                    % (x - 5.5, y - 3, x - 4, y - 3, x + 4, y - 3, E))
        if "donjon" in n or "tour" in n:
            return ('<path d="M %.1f %.1f v -11 h 4 v 3 h 3 v -3 h 4 v 11 z" '
                    'fill="none" stroke="%s" stroke-width="1.3"/>'
                    % (x - 5.5, y + 3, E))
        if "brasserie" in n or "etuve" in n:
            return ('<path d="M %.1f %.1f v 8 h 8 v -8 z" fill="none" stroke="%s" '
                    'stroke-width="1.2"/>' % (x - 4, y - 4, E))
        return ('<path d="M %.1f %.1f l 5 -5 l 5 5 z" fill="none" stroke="%s" '
                'stroke-width="1.2"/>' % (x - 5, y + 3, E))

    largeur = max(p[0] for l in lignes for p in l["pts"]) + MARGE * 3.0
    hauteur = max(p[1] for l in lignes for p in l["pts"]) + MARGE * 2.0

    out = []
    A = out.append
    A('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.0f" '
      'width="%.0f" height="%.0f">' % (largeur, hauteur, largeur, hauteur))
    A('<defs>'
      '<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" '
      'numOctaves="4" result="b"/><feColorMatrix in="b" type="saturate" values="0"/>'
      '<feComponentTransfer><feFuncA type="linear" slope="0.15"/></feComponentTransfer>'
      '</filter>'
      '<filter id="taches"><feTurbulence type="fractalNoise" baseFrequency="0.010" '
      'numOctaves="3" result="t"/><feColorMatrix in="t" type="saturate" values="0"/>'
      '<feComponentTransfer><feFuncA type="gamma" exponent="3.6" amplitude="0.75"/>'
      '</feComponentTransfer></filter>'
      '<radialGradient id="usure" cx="50%" cy="48%" r="74%">'
      '<stop offset="58%" stop-color="#000" stop-opacity="0"/>'
      '<stop offset="100%" stop-color="#6b5433" stop-opacity="0.5"/>'
      '</radialGradient>'
      '<filter id="plume"><feTurbulence type="fractalNoise" baseFrequency="0.05" '
      'numOctaves="2" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" '
      'scale="1.8" xChannelSelector="R" yChannelSelector="G"/></filter>'
      '</defs>')
    A('<rect width="100%%" height="100%%" fill="%s"/>' % PARCHEMIN)
    A('<rect width="100%%" height="100%%" fill="%s" filter="url(#taches)" '
      'opacity="0.55"/>' % TACHE)

    # Le palimpseste : la peau a deja servi, et ca se lit sous l'encre.
    A('<g opacity="0.10" fill="%s" font-family=%s font-size="12">' % (ENCRE, PLUME))
    for i in range(int(hauteur / 24)):
        A('<text x="%.0f" y="%.0f">%s</text>'
          % (MARGE * 0.35, MARGE * 0.5 + i * 24,
             "compte du bois rendu au quai   membrures   bordes   brasses de filin   "
             * 3))
    A('</g>')

    A('<g filter="url(#plume)">')
    for l in lignes:
        L, pts = l["leve"], l["pts"]
        tp = [trembler(*p, a=2.0) for p in pts]

        # LA ROUTE : deux passes d'encre, comme une plume qu'on reprend.
        A('<path d="%s" fill="none" stroke="%s" stroke-width="2.8" '
          'stroke-linecap="round" opacity="0.9"/>' % (courbe(tp), ENCRE))
        A('<path d="%s" fill="none" stroke="%s" stroke-width="1.2" '
          'stroke-linecap="round" opacity="0.5"/>'
          % (courbe([trembler(*p, a=1.0) for p in pts]), ENCRE))

        # LES MAISONS : des carres au bord de la route, des deux cotes. On ne
        # compte pas pour lui, il les a dessinees une par une — et la densite se
        # voit sans qu'aucun chiffre ait a la dire.
        for i, t in enumerate(L["troncons"]):
            if i + 1 >= len(tp):
                break
            a, b = tp[i], tp[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1.0
            ux, uy = dx / ln, dy / ln
            nx, ny = -uy, ux
            n, k = t["maisons"], 0
            place = max(1, int(ln / 6.0))
            rangs = max(1, int(math.ceil(n / (place * 2.0))))
            for r in range(rangs):
                for j in range(place):
                    for cote in (1, -1):
                        if k >= n:
                            break
                        pos = (j + 0.5) / place
                        ec = 6.5 + r * 5.2
                        cx = a[0] + dx * pos + nx * ec * cote
                        cy = a[1] + dy * pos + ny * ec * cote
                        cx, cy = trembler(cx, cy, 0.9)
                        s = rnd.uniform(2.4, 3.8)
                        A('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                          'fill="none" stroke="%s" stroke-width="0.85" '
                          'transform="rotate(%.0f %.1f %.1f)" opacity="0.82"/>'
                          % (cx - s / 2, cy - s / 2, s, s, ENCRE,
                             rnd.uniform(-16, 16), cx, cy))
                        k += 1

        # LE FRONT — UN CHIFFRE SEUL, ET RIEN D'AUTRE. Combien d'hommes en
        # armes la rue laisse passer cote a cote : la largeur divisee par le pas
        # d'un homme qui porte une lance. C'est le seul nombre ecrit de toute la
        # planche, parce que c'est le seul qu'on lise en FLUX — une colonne de
        # cent vingt a quatre de front fait trente rangs, et trente rangs font
        # trois minutes sous une voute. Le reste se compte en carres.
        for i, t in enumerate(L["troncons"]):
            if i + 1 >= len(tp):
                break
            lm = t.get("largeur_m") or 0
            front = int(lm / 0.8)
            if front < 1:
                continue
            a, b = tp[i], tp[i + 1]
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            mx, my = trembler(mx, my, 1.0)
            A('<circle cx="%.1f" cy="%.1f" r="9.5" fill="%s" stroke="%s" '
              'stroke-width="1.1" opacity="0.95"/>' % (mx, my, PARCHEMIN, SANG))
            A('<text x="%.1f" y="%.1f" fill="%s" font-family=%s font-size="14" '
              'text-anchor="middle" transform="rotate(%.1f %.1f %.1f)">%d</text>'
              % (mx, my + 5, SANG, MAIN, rnd.uniform(-8, 8), mx, my, front))

        # LA PENTE : des chevrons a l'encre rouge, sur la route, pointes vers le
        # haut quand ca monte. C'est ce qui tire dans les jambes, pas une donnee.
        for i, t in enumerate(L["troncons"]):
            if i + 1 >= len(tp):
                break
            a, b = tp[i], tp[i + 1]
            n = degre_n(t["pente"])
            if not n:
                continue
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            haut = t["sens"] != "descend"
            for j in range(n):
                x0, y0 = trembler(mx - 8 + j * 6.5, my - 15, 0.6)
                A('<path d="M %.1f %.1f l 3.2 %s l 3.2 %s" fill="none" '
                  'stroke="%s" stroke-width="1.4" stroke-linecap="round"/>'
                  % (x0, y0, "-4.2" if haut else "4.2",
                     "4.2" if haut else "-4.2", SANG))

        # CE QU'ON LONGE — AU BORD DE LA ROUTE, JAMAIS DESSUS. Un puits n'est pas
        # sur le chemin : il est a cote, et c'est pour ca qu'il sert de borne. On
        # le pose en retrait, avec un trait de rappel vers l'endroit d'ou on l'a
        # vu, et son nom de sa main.
        for i, p in enumerate(tp):
            b = L["bornes"][i] if i < len(L["bornes"]) else {}
            if not b.get("nom"):
                A('<circle cx="%.1f" cy="%.1f" r="1.7" fill="%s" opacity="0.7"/>'
                  % (p[0], p[1], ENCRE))
                continue
            av = tp[i - 1] if i else tp[min(1, len(tp) - 1)]
            dx, dy = p[0] - av[0], p[1] - av[1]
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            cote = 1 if (i % 2 == 0) else -1
            ec = 34.0
            gx, gy = trembler(p[0] + nx * ec * cote, p[1] + ny * ec * cote, 2.5)
            A('<path d="M %.1f %.1f L %.1f %.1f" stroke="%s" stroke-width="0.7" '
              'opacity="0.5" stroke-dasharray="2 3"/>' % (p[0], p[1], gx, gy, ENCRE))
            A(glyphe(b["nom"], gx, gy))
            ancre = "start" if (nx * cote) >= 0 else "end"
            tx = gx + (10 if ancre == "start" else -10)
            A('<text x="%.1f" y="%.1f" fill="%s" font-family=%s font-size="13.5" '
              'text-anchor="%s" transform="rotate(%.1f %.1f %.1f)">%s</text>'
              % (tx, gy + 4, ENCRE, MAIN, ancre, rnd.uniform(-6, -1), tx, gy,
                 esc(b["nom"])))

        # CE QUI PORTE DES ARMES, ET OU L'ON PAIE. En rouge, comme tout ce qu'il
        # veut relire d'abord, et du cote OPPOSE aux reperes civils pour qu'un
        # coup d'oeil separe les deux : d'un bord ce qu'on longe, de l'autre ce
        # qui vous regarde passer.
        for i, t in enumerate(L["troncons"]):
            if i + 1 >= len(tp):
                break
            marques = [("garnison", g) for g in (t.get("garnison") or [])]                     + [("peage", p_) for p_ in (t.get("peage") or [])]
            if not marques:
                continue
            a, b = tp[i], tp[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            cote = -1 if (i % 2 == 0) else 1        # l'inverse des reperes
            for j, (quoi, nom) in enumerate(marques):
                pos = (j + 1.0) / (len(marques) + 1.0)
                ec = 30.0 + j * 15.0
                gx = a[0] + dx * pos + nx * ec * cote
                gy = a[1] + dy * pos + ny * ec * cote
                px_ = a[0] + dx * pos
                py_ = a[1] + dy * pos
                A('<path d="M %.1f %.1f L %.1f %.1f" stroke="%s" '
                  'stroke-width="0.7" opacity="0.55" stroke-dasharray="2 3"/>'
                  % (px_, py_, gx, gy, SANG))
                if quoi == "garnison":
                    # deux lances en sautoir : ce qui porte des armes
                    A('<path d="M %.1f %.1f l 11 11 M %.1f %.1f l 11 -11" '
                      'stroke="%s" stroke-width="1.5" fill="none"/>'
                      % (gx - 5.5, gy - 5.5, gx - 5.5, gy + 5.5, SANG))
                else:
                    # la barriere : deux montants et la barre qu'on baisse
                    A('<path d="M %.1f %.1f v 11 M %.1f %.1f v 11 '
                      'M %.1f %.1f h 14" stroke="%s" stroke-width="1.5" '
                      'fill="none"/>'
                      % (gx - 7, gy - 5, gx + 7, gy - 5, gx - 7, gy - 1, SANG))
                ancre = "start" if (nx * cote) >= 0 else "end"
                tx = gx + (11 if ancre == "start" else -11)
                A('<text x="%.1f" y="%.1f" fill="%s" font-family=%s '
                  'font-size="12.5" text-anchor="%s" '
                  'transform="rotate(%.1f %.1f %.1f)">%s</text>'
                  % (tx, gy + 4, SANG, MAIN, ancre, rnd.uniform(-6, -1),
                     tx, gy, esc(nom)))

        # le compte de la marche, ecrit au depart comme on signe un releve
        A('<text x="%.1f" y="%.1f" fill="%s" font-family=%s font-size="13" '
          'text-anchor="end" transform="rotate(%.1f %.1f %.1f)">%s</text>'
          % (tp[0][0] - 14, tp[0][1] + 18, SANG, MAIN, rnd.uniform(-4, 2),
             tp[0][0] - 14, tp[0][1] + 18, esc("%d pas" % L["pas"])))
    A('</g>')

    A('<text x="%.0f" y="%.0f" fill="%s" font-family=%s font-size="29" '
      'transform="rotate(-1.4 %.0f %.0f)">Ce que j\'ai marche</text>'
      % (MARGE * 1.0, MARGE * 0.7, ENCRE, MAIN, MARGE, MARGE))
    A('<text x="%.0f" y="%.0f" fill="%s" font-family=%s font-size="13">'
      'de ma main, le 24e jour de la 3e lune  —  un carre vaut une maison, '
      'un chevron ce qui tire dans les jambes — en rouge, ce qui porte des '
      "armes et ce qui prend de l'argent — le chiffre est le nombre d'hommes "
      "en armes de front</text>"
      % (MARGE * 1.05, MARGE * 0.7 + 19, PALE, MAIN))
    A('<text x="%.0f" y="%.0f" fill="%s" font-family=%s font-size="12.5" '
      'transform="rotate(1.1 %.0f %.0f)">Ce qui n\'est pas sur une ligne, '
      'je ne l\'ai pas vu.</text>'
      % (MARGE * 1.0, hauteur - MARGE * 0.7, PALE, MAIN,
         MARGE, hauteur - MARGE * 0.7))
    A('<rect width="100%" height="100%" fill="url(#usure)"/>')
    A('<rect width="100%" height="100%" filter="url(#grain)" opacity="0.45"/>')
    A('</svg>')
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    main()
