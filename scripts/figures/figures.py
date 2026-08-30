# -*- coding: utf-8 -*-
"""LES FIGURES DU MESTRE — ce qu'on dessine pour y voir clair.

    python scripts/figures/figures.py roue      > ecrans/dessins/roue-des-journees.svg
    python scripts/figures/figures.py bannieres > ecrans/dessins/role-des-bannieres.svg

POURQUOI CES DEUX-LÀ ET PAS UN ORGANIGRAMME. Ce qui n'existe pas en 129 AC, ce
n'est pas le diagramme : c'est l'abstraction fléchée. Les vraies figures de
pensée de l'époque ont quatre formes, et pas une de plus — l'ARBRE, la ROUE, les
COLONNES, la liste indentée. Un mestre en trace toute la journée ; il ne trace
jamais une boîte reliée à une autre boîte.

    roue      — les journées de route depuis Port-Réal. Le rayon est du TEMPS,
                l'angle est une vraie direction (prise de la carte). C'est la
                rose d'itinéraire : elle ne prétend pas être une carte, elle
                répond à « combien de jours, et de quel côté ».
    bannieres — ce que chaque maison montre et ce qu'elle peut lever. Des
                colonnes, et des lances comptées en traits : le rapport de force
                se lit à l'œil sans qu'on ait à additionner.

CE QUE CES FIGURES NE PORTENT PAS, et c'est la règle : rien que le joueur ne
puisse savoir. `allegeance_affichee` est ce qu'une maison MONTRE — jamais
`allegeance_reelle`, qui n'a rien à faire sur une feuille posée sur une table.
L'or d'une maison n'y est pas non plus : un trésor ne se compte pas de loin. Les
levées sont données pour ce qu'elles sont, l'estimation d'un mestre.

Elles sont DESSINÉES par quelqu'un, et c'est ce qui les sauve : un document a un
auteur, une date, et le droit de se tromper. Un tableau juste par construction
serait un panneau d'interface déguisé en parchemin.
"""
import io, json, math, os, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# L'encre et le papier de plan_leves.py : les feuilles d'une même maison doivent
# se ressembler, sans quoi la table a l'air d'un classeur.
PARCHEMIN = "#e8dcc0"
TACHE = "#d9c9a3"
ENCRE = "#3b2a17"
PALE = "#7a6647"
SANG = "#8c3a2a"
VERT = "#4a5c33"
MAIN = "'Segoe Script', 'Brush Script MT', 'Lucida Handwriting', cursive"
PLUME = "'Palatino Linotype', 'Book Antiqua', Georgia, serif"

# Ce que porte une bannière, à l'œil : la couleur du parti qu'on AFFICHE.
COULEUR_PARTI = {"noir": ENCRE, "vert": VERT, "neutre": PALE}


def charger(nom):
    with io.open(os.path.join(RACINE, "etat", nom), encoding="utf-8") as f:
        return json.load(f)


def liste(d, clef):
    return d if isinstance(d, list) else d.get(clef, [])


def coordonnees():
    """Les points de la carte peinte, pris dans `ecrans/modules/geo.js`.

    On ne recopie pas ces chiffres à la main : la carte est engendrée
    (scripts/carte_geo.py) et une copie divergerait au premier retracé.
    """
    s = io.open(os.path.join(RACINE, "ecrans", "modules", "geo.js"),
                encoding="utf-8").read()
    i = s.index('"lieux"')
    j = s.index("{", i)
    prof, k = 0, j
    while k < len(s):
        if s[k] == "{":
            prof += 1
        elif s[k] == "}":
            prof -= 1
            if prof == 0:
                break
        k += 1
    return json.loads(s[j:k + 1])


def echappe(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def feuille(largeur, hauteur, corps, titre, main):
    """Le parchemin : grain, taches, bord mangé. Une feuille, pas un panneau."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">
<defs>
  <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" result="b"/>
    <feColorMatrix in="b" type="saturate" values="0"/>
    <feComponentTransfer><feFuncA type="linear" slope="0.06"/></feComponentTransfer>
    <feComposite operator="in" in2="SourceGraphic"/></filter>
</defs>
<rect width="%d" height="%d" fill="%s"/>
<g opacity=".5"><ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="%s"/>
   <ellipse cx="%d" cy="%d" rx="42" ry="30" fill="%s"/></g>
<rect width="%d" height="%d" fill="%s" filter="url(#grain)"/>
<text x="%d" y="46" text-anchor="middle" font-family="%s" font-size="26" fill="%s">%s</text>
<text x="%d" y="68" text-anchor="middle" font-family="%s" font-size="12" font-style="italic" fill="%s">%s</text>
%s
</svg>""" % (largeur, hauteur, largeur, hauteur, largeur, hauteur, PARCHEMIN,
             int(largeur * .72), int(hauteur * .18), 90, 60, TACHE,
             int(largeur * .15), int(hauteur * .88), TACHE,
             largeur, hauteur, PARCHEMIN,
             largeur // 2, PLUME, ENCRE, echappe(titre),
             largeur // 2, PLUME, PALE, echappe(main), corps)


# ---------------------------------------------------------------------------
def roue():
    """La rose des journées : l'angle est vrai, le rayon est du temps."""
    lieux = liste(charger("lieux.json"), "lieux")
    maisons = {m["id"]: m for m in liste(charger("maisons.json"), "maisons")}
    pts = coordonnees()

    centre_id = "port-real"
    if centre_id not in pts:
        raise SystemExit("la carte ne connaît pas Port-Réal : rien à centrer.")
    cx0, cy0 = pts[centre_id]

    # On ne garde que ce qui a une place sur la carte ET un compte de journées.
    # Un lieu sans point ne peut pas porter de direction, et l'inventer serait
    # exactement le mensonge que cette figure évite.
    places = []
    for l in lieux:
        lid = l.get("id")
        j = l.get("jours_de_pr")
        p = pts.get(lid) or pts.get((l.get("alias") or [None])[0] if l.get("alias") else None)
        if not p or j is None or lid == centre_id:
            continue
        places.append((l, p, float(j)))
    if not places:
        raise SystemExit("aucun lieu situé ET compté : rien à dessiner.")

    # LE THÉÂTRE, ET LE RESTE. Winterfell est à quarante jours ; le mettre sur
    # la rose écraserait tout le reste contre le moyeu — Rosby, à un jour,
    # tomberait à neuf points du centre, illisible. Une rose d'itinéraire ne
    # couvre donc que la portée qui décide de quelque chose, et ce qui est
    # au-delà se met en marge, en toutes lettres. C'est ce que fait n'importe
    # quelle feuille de route : on dessine sa semaine, on écrit le reste.
    SEUIL = 10
    lointains = sorted([(l, j) for l, _, j in places if j > SEUIL],
                       key=lambda t: t[1])
    places = [t for t in places if t[2] <= SEUIL]
    if not places:
        raise SystemExit("rien à moins de %d jours : la rose serait vide." % SEUIL)

    jmax = max(j for _, _, j in places)
    L, H = 1000, 1000
    cx, cy = L / 2.0, H / 2.0 + 26
    rmax = 372.0
    par_jour = rmax / jmax

    out = []
    # LE PLACEMENT DES ÉTIQUETTES. Une rose se lit ou ne se lit pas : deux noms
    # l'un sur l'autre et la figure ne vaut plus rien. On tient donc la liste
    # des rectangles déjà posés, et chaque nom essaie ses positions dans l'ordre
    # jusqu'à en trouver une libre — d'abord vers l'extérieur, puis en montant
    # ou descendant, puis en s'éloignant du centre. Une lettre vaut environ sept
    # points de large à cette taille ; l'estimation suffit, on ne compose pas un
    # livre.
    poses = []

    def libre(x, y, w, h, ancre):
        gx = x - (w if ancre == "end" else 0)
        for ox, oy, ow, oh in poses:
            if gx < ox + ow and ox < gx + w and y - h < oy and oy - oh < y:
                return False
        return True

    def poser_texte(x, y, w, h, ancre):
        poses.append((x - (w if ancre == "end" else 0), y, w, h))

    # Les cercles des journées : une couronne par jour de route, chiffrée. C'est
    # la seule graduation de la figure, et elle est en TEMPS. Les chiffres se
    # posent EN PREMIER et se réservent leur place : ils sont l'échelle, et une
    # échelle qu'on chasse ne mesure plus rien.
    jour = 1
    while jour <= int(math.ceil(jmax)):
        r = jour * par_jour
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" '
                   'stroke-width="%s" stroke-dasharray="2 5" opacity=".65"/>'
                   % (cx, cy, r, PALE, "1.1" if jour % 5 else "1.8"))
        # Les chiffres descendent SOUS le moyeu : le nom du centre est écrit
        # au-dessus de son point, et deux textes au même endroit ne se lisent
        # ni l'un ni l'autre.
        tx, ty = cx + 5, cy + r - 5
        out.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="10" '
                   'fill="%s" opacity=".8">%d j</text>'
                   % (tx, ty, PLUME, PALE, jour))
        poser_texte(tx, ty, 22, 11, "start")
        jour += 1

    # Le centre se réserve sa place avant tout le monde : c'est le seul nom de
    # la feuille qu'on ne peut pas déplacer.
    poser_texte(cx, cy - 15, 96, 16, "middle")
    # La marge des lointains, elle aussi : elle s'écrit plus bas dans le code,
    # mais elle occupe le coin dès maintenant — sinon un nom de la rose vient
    # s'y coucher et les deux se mangent.
    if lointains:
        poser_texte(46, 118 + 19 * len(lointains) + 4, 230,
                    19 * len(lointains) + 22, "start")

    # Les rais de la rose : quatre directions, pour lire un angle sans règle.
    for ang, nom in ((-90, "Nord"), (0, "Est"), (90, "Sud"), (180, "Ouest")):
        a = math.radians(ang)
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                   'stroke-width="1" opacity=".35"/>'
                   % (cx, cy, cx + math.cos(a) * (rmax + 30),
                      cy + math.sin(a) * (rmax + 30), PALE))
        out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="%s" '
                   'font-size="11" font-style="italic" fill="%s">%s</text>'
                   % (cx + math.cos(a) * (rmax + 48),
                      cy + math.sin(a) * (rmax + 48) + 4, PLUME, PALE, nom))

    # Les places. L'angle sort de la carte, le rayon du compte de journées : une
    # place lointaine et une place proche dans la même direction se rangent
    # naturellement l'une derrière l'autre, comme sur la route.
    for l, (px, py), j in sorted(places, key=lambda t: t[2]):
        ang = math.atan2(py - cy0, px - cx0)
        r = j * par_jour
        x, y = cx + math.cos(ang) * r, cy + math.sin(ang) * r
        m = maisons.get(l.get("controle_id")) or {}
        c = COULEUR_PARTI.get(m.get("allegeance_affichee"), PALE)
        out.append('<circle cx="%.1f" cy="%.1f" r="5.5" fill="%s" stroke="%s" '
                   'stroke-width="1.2"/>' % (x, y, c, PARCHEMIN))

        nom = l.get("nom") or l.get("id")
        w, h = len(nom) * 7.0, 14.0
        droite = math.cos(ang) >= 0
        pose = None
        # D'abord du côté du large, puis de l'autre, puis au-dessus et
        # au-dessous ; en dernier ressort on s'écarte du centre, le long du
        # rayon — un nom repoussé vers l'extérieur reste juste, il dit toujours
        # la même direction.
        for ecart in (0, 13, -13, 26, -26, 39, -39):
            for droit in ((droite, not droite) if ecart == 0 else (droite,)):
                tx = x + (11 if droit else -11)
                ty = y + 4 + ecart
                ancre = "start" if droit else "end"
                if libre(tx, ty, w, h, ancre):
                    pose = (tx, ty, ancre)
                    break
            if pose:
                break
        if not pose:
            recul = 1.0
            while recul < 4:
                tx = cx + math.cos(ang) * (r + 22 * recul) + (11 if droite else -11)
                ty = cy + math.sin(ang) * (r + 22 * recul) + 4
                ancre = "start" if droite else "end"
                if libre(tx, ty, w, h, ancre):
                    pose = (tx, ty, ancre)
                    break
                recul += 1
            if not pose:
                pose = (x + (11 if droite else -11), y + 4,
                        "start" if droite else "end")
        tx, ty, ancre = pose
        poser_texte(tx, ty, w, h, ancre)
        # Le fil qui rattache le nom à son point, quand il a fallu l'écarter :
        # sans lui, un nom repoussé ment sur la place qu'il désigne.
        if abs(ty - (y + 4)) > 6 or abs(tx - x) > 26:
            out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
                       'stroke-width=".8" opacity=".45"/>'
                       % (x, y, tx - (3 if ancre == "start" else -3), ty - 4, PALE))
        out.append('<text x="%.1f" y="%.1f" text-anchor="%s" font-family="%s" '
                   'font-size="13" fill="%s">%s</text>'
                   % (tx, ty, ancre, MAIN, ENCRE, echappe(nom)))

    # Le centre, en dernier : il doit passer par-dessus les couronnes.
    out.append('<circle cx="%.1f" cy="%.1f" r="8" fill="%s"/>' % (cx, cy, SANG))
    out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="%s" '
               'font-size="15" fill="%s">Port-Réal</text>'
               % (cx, cy - 15, MAIN, SANG))

    # Ce qui est hors de portée : en marge, en toutes lettres. Un nom écrit
    # dans un coin dit mieux « c'est loin » qu'un point collé au bord.
    if lointains:
        ly = 118
        out.append('<text x="46" y="%d" font-family="%s" font-size="11" '
                   'font-style="italic" fill="%s">Au-delà de %d jours :</text>'
                   % (ly, PLUME, PALE, SEUIL))
        for l, j in lointains:
            ly += 19
            out.append('<text x="52" y="%d" font-family="%s" font-size="13" '
                       'fill="%s">%s <tspan fill="%s" font-family="%s" '
                       'font-size="11">%d j</tspan></text>'
                       % (ly, MAIN, ENCRE, echappe(l.get("nom") or l.get("id")),
                          PALE, PLUME, int(j)))

    out.append('<text x="%d" y="%d" text-anchor="middle" font-family="%s" '
               'font-size="11" font-style="italic" fill="%s">'
               'Le rayon est le temps, non la distance. Un corbeau met le tiers '
               'des jours d\'un cavalier.</text>' % (L // 2, H - 34, PLUME, PALE))
    out.append('<g font-family="%s" font-size="11" fill="%s">'
               '<circle cx="46" cy="%d" r="5" fill="%s"/><text x="58" y="%d">tient pour la reine</text>'
               '<circle cx="46" cy="%d" r="5" fill="%s"/><text x="58" y="%d">tient pour Aegon</text>'
               '<circle cx="46" cy="%d" r="5" fill="%s"/><text x="58" y="%d">n\'a rien montré</text></g>'
               % (PLUME, PALE, H - 96, ENCRE, H - 92, H - 76, VERT, H - 72,
                  H - 56, PALE, H - 52))

    return feuille(L, H, "\n".join(out), "Les journées du royaume",
                   "Comptées depuis Port-Réal, de la main du mestre Gerardys")


# ---------------------------------------------------------------------------
def bannieres():
    """Ce que chaque maison montre, et ce qu'elle peut lever."""
    maisons = liste(charger("maisons.json"), "maisons")
    lieux = {l["id"]: l for l in liste(charger("lieux.json"), "lieux")}

    rangs = [m for m in maisons if m.get("levees_max")]
    rangs.sort(key=lambda m: -(m.get("levees_max") or 0))

    L = 900
    haut, pas = 108, 46
    H = haut + pas * len(rangs) + 76
    plus = max((m.get("levees_max") or 0) for m in rangs) or 1
    barre = 300.0

    out = []
    out.append('<g font-family="%s" font-size="11" font-style="italic" fill="%s">'
               '<text x="46" y="%d">La maison</text>'
               '<text x="300" y="%d">Son siège</text>'
               '<text x="516" y="%d">Ce qu\'elle peut lever</text></g>'
               % (PLUME, PALE, haut - 14, haut - 14, haut - 14))
    out.append('<line x1="42" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1" '
               'opacity=".5"/>' % (haut - 8, L - 42, haut - 8, PALE))

    y = haut + 20
    for m in rangs:
        c = COULEUR_PARTI.get(m.get("allegeance_affichee"), PALE)
        siege = lieux.get(m.get("siege_id"), {}).get("nom") or m.get("siege_id") or "—"
        maxi = m.get("levees_max") or 0
        dispo = m.get("levees_dispo")

        out.append('<rect x="42" y="%d" width="5" height="22" fill="%s"/>'
                   % (y - 15, c))
        out.append('<text x="58" y="%d" font-family="%s" font-size="15" fill="%s">%s</text>'
                   % (y, MAIN, ENCRE, echappe(m.get("nom") or m.get("id"))))
        out.append('<text x="300" y="%d" font-family="%s" font-size="12" fill="%s">%s</text>'
                   % (y, PLUME, PALE, echappe(siege)))

        # La barre : ce qu'elle peut lever en tout, et — en plein — ce qu'elle a
        # sous la main. L'écart entre les deux est ce qui se voit d'un coup
        # d'œil, et c'est le seul chiffre qui décide quoi que ce soit.
        ltot = barre * maxi / plus
        out.append('<rect x="516" y="%d" width="%.1f" height="13" fill="none" '
                   'stroke="%s" stroke-width="1" opacity=".7"/>'
                   % (y - 11, ltot, PALE))
        if dispo:
            out.append('<rect x="516" y="%d" width="%.1f" height="13" fill="%s" '
                       'opacity=".85"/>' % (y - 11, barre * dispo / plus, c))
        out.append('<text x="%.1f" y="%d" font-family="%s" font-size="11" fill="%s">'
                   '%s%s</text>'
                   % (516 + ltot + 9, y, PLUME, PALE,
                      "{:,}".format(dispo).replace(",", " ") + " sur " if dispo else "",
                      "{:,}".format(maxi).replace(",", " ")))
        y += pas

    out.append('<text x="%d" y="%d" text-anchor="middle" font-family="%s" '
               'font-size="11" font-style="italic" fill="%s">'
               'Le trait plein est ce qu\'elle tient sous la main ; le trait vide, '
               'ce qu\'elle lèverait en vidant ses villages.</text>'
               % (L // 2, H - 40, PLUME, PALE))
    out.append('<text x="%d" y="%d" text-anchor="middle" font-family="%s" '
               'font-size="11" font-style="italic" fill="%s">'
               'Ces comptes sont d\'un mestre, non d\'un intendant : ils se '
               'trompent, et de plus en plus loin d\'ici.</text>'
               % (L // 2, H - 22, PLUME, SANG))

    return feuille(L, H, "\n".join(out), "Le rôle des bannières",
                   "Ce que chacun MONTRE — 129 AC, 3e lune")


FIGURES = {"roue": roue, "bannieres": bannieres}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in FIGURES:
        raise SystemExit("figures connues : %s" % ", ".join(sorted(FIGURES)))
    sys.stdout.write(FIGURES[sys.argv[1]]())
