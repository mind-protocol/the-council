# -*- coding: utf-8 -*-
# Dessine la nappe : un SVG par affaire, depuis les registres.
#
# POURQUOI PAS DE FICHIER DE NAPPE. Chaque piece existe deja une fois, dans son
# registre par type (books.json). Un etat/nappe.json qui reporterait les memes
# numeros, les memes noms et les memes aretes serait une seconde verite, et deux
# verites divergent au premier conseil. Ce script ne sauvegarde donc rien : il
# LIT les registres et DESSINE. Le SVG est jetable ; on le refait quand la table
# a bouge, et il ne peut pas mentir sur ce que disent les feuillets.
#
# CE QUI SE SAUVEGARDE QUAND MEME. La POSE — l'endroit ou une main a pousse une
# piece pendant une seance. Ca, aucun registre ne le porte, et c'est la seule
# chose que ce script accepte de lire ailleurs : etat/nappe-pose.json, facultatif,
# {"220": [x, y]}. Sans lui, la disposition se calcule : la chaine est un arbre.
#
# Usage :
#     python scripts/figures/nappe.py                      toutes les affaires
#     python scripts/figures/nappe.py --affaire "Prise de Port-Real"
#     python scripts/figures/nappe.py --sortie ecrans/nappes
import io, json, os, sys, unicodedata

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import bibliotheque

racine = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────── lecture des registres
REGISTRES = {
    "etat":   ("plan-etats-cibles", u"🎯 N°",  u"🏷️ L'état",   u"⬆️ Sert"),
    "verrou": ("plan-verrous",      u"🔒 N°",  u"🏷️ Le verrou", u"⛔ Bloque"),
    "clef":   ("plan-clefs",        u"🗝️ N°", u"🏷️ La clef",   u"🔓 Ouvre"),
    "action": ("plan-actions",      u"⚔️ N°",  u"🏷️ L'action",  u"🗝️ Réalise"),
}
INVENTAIRES = {
    "moyen":  ("plan-moyens",  u"🧰 N°", u"🏷️ Le moyen"),
    "office": ("plan-offices", u"🪶 N°", u"🏷️ L'office"),
}


def nu(s):
    """Le texte nu : sans gras d'appui, sans tirets d'arborescence, sans emoji."""
    s = s.replace(u"**", u"")
    for c in (u"　", u"└", u"　"):
        s = s.replace(c, u" ")
    s = u"".join(c for c in s if unicodedata.category(c) != "So" and c not in u"️")
    return u" ".join(s.split())


def col(livre, entete):
    try:
        return livre["colonnes"].index(entete)
    except ValueError:
        for i, c in enumerate(livre["colonnes"]):
            if nu(c).lower() == nu(entete).lower():
                return i
    raise SystemExit(u"colonne « %s » absente de %s" % (entete, livre["id"]))


def charger():
    livres = {b["id"]: b for b in bibliotheque.charger(
        os.path.join(racine, "etat"))}
    pieces, inventaire = {}, {}

    for genre, (bid, cnum, cnom, cvers) in REGISTRES.items():
        b = livres.get(bid)
        if not b:
            continue
        inum, inom, ivers = col(b, cnum), col(b, cnom), col(b, cvers)
        iaff = col(b, u"🏰 Affaire") if u"🏰 Affaire" in b["colonnes"] else None
        for l in b["lignes"]:
            c = l["cellules"]
            num = nu(c[inum])
            if not num:
                continue
            pieces[num] = {
                "num": num, "genre": genre, "nom": nu(c[inom]),
                "vers": nu(c[ivers]).split()[0] if nu(c[ivers]) not in (u"—", u"") else None,
                "affaire": nu(c[iaff]) if iaff is not None else u"",
                "cellules": [nu(x) for x in c],
                "livre": b,
            }
        if genre == "action":
            for l in b["lignes"]:
                c = l["cellules"]
                num = nu(c[inum])
                if num in pieces:
                    pieces[num]["office"] = nu(c[col(b, u"🪶 Office")])
                    pieces[num]["moyens"] = [m for m in nu(c[col(b, u"🧰 Moyens")]).split(u"·") if m.strip()]

    for genre, (bid, cnum, cnom) in INVENTAIRES.items():
        b = livres.get(bid)
        if not b:
            continue
        inum, inom = col(b, cnum), col(b, cnom)
        for l in b["lignes"]:
            c = l["cellules"]
            inventaire[nu(c[inum])] = {"num": nu(c[inum]), "genre": genre, "nom": nu(c[inom])}

    pose = {}
    p = os.path.join(racine, "etat", "nappe-pose.json")
    if os.path.exists(p):
        pose = json.load(io.open(p, encoding="utf-8"))
    return pieces, inventaire, pose


# ─────────────────────────────────────────────── les formes
# La forme dit la nature, et rien d'autre. Meme dessin qu'a la main : on doit
# reconnaitre un verrou d'un etat cible sans lire un mot.
def tuile(x, y, w=170, h=52, c=14):        # affaire : huit cotes
    return u"M%g,%g L%g,%g L%g,%g L%g,%g L%g,%g L%g,%g L%g,%g L%g,%g Z" % (
        x - w / 2 + c, y - h / 2, x + w / 2 - c, y - h / 2, x + w / 2, y - h / 2 + c,
        x + w / 2, y + h / 2 - c, x + w / 2 - c, y + h / 2, x - w / 2 + c, y + h / 2,
        x - w / 2, y + h / 2 - c, x - w / 2, y - h / 2 + c)


def rect(x, y, w=190, h=58):               # etat cible
    return u"M%g,%g h%g v%g h%g Z" % (x - w / 2, y - h / 2, w, h, -w)


def hexa(x, y, w=176, h=58):               # verrou : six pans, brule au fer
    a = w / 2.0
    b = h / 2.0
    return u"M%g,%g L%g,%g L%g,%g L%g,%g L%g,%g L%g,%g Z" % (
        x - a, y, x - a + 22, y - b, x + a - 22, y - b, x + a, y, x + a - 22, y + b, x - a + 22, y + b)


def losange(x, y, w=196, h=64):            # clef
    return u"M%g,%g L%g,%g L%g,%g L%g,%g Z" % (x, y - h / 2, x + w / 2, y, x, y + h / 2, x - w / 2, y)


def barrette(x, y, w=186, h=34):           # action
    return u"M%g,%g h%g v%g h%g Z" % (x - w / 2, y - h / 2, w, h, -w)


FORME = {"affaire": tuile, "etat": rect, "verrou": hexa, "clef": losange, "action": barrette}
REMPLI = {"affaire": "#efe4cb", "etat": "#e6ddc6", "verrou": "#3a3230",
          "clef": "#e9dcc0", "action": "#efe9db", "moyen": "#dfe6df", "office": "#dcdfe9"}
ENCRE = {"verrou": "#f0e6d6"}


def coupe(s, n):
    """Le texte ecrit sur une piece : deux lignes au plus, comme a la craie."""
    mots, lignes, cur = s.split(), [], u""
    for m in mots:
        if len(cur) + len(m) + 1 <= n:
            cur = (cur + u" " + m).strip()
        else:
            lignes.append(cur)
            cur = m
        if len(lignes) == 2:
            break
    if cur and len(lignes) < 2:
        lignes.append(cur)
    if len(lignes) == 2 and len(u" ".join(mots)) > sum(len(x) for x in lignes) + 1:
        lignes[1] = lignes[1][:n - 1].rstrip() + u"…"
    return lignes


def ech(s):
    return (s.replace(u"&", u"&amp;").replace(u"<", u"&lt;").replace(u">", u"&gt;"))


# ─────────────────────────────────────────────── mise en nappe
RANGS = {"affaire": 0, "etat": 1, "verrou": 2, "clef": 3, "action": 4}
HAUT = {"affaire": 90, "etat": 210, "verrou": 340, "clef": 470, "action": 590}
PAS = 46          # entre deux barrettes empilees
MARGE_G = 260     # bord gauche : les moyens
MARGE_D = 260     # bord droit : les offices


def dessiner(affaire, pieces, inventaire, pose):
    dedans = {n: p for n, p in pieces.items() if p["affaire"] == affaire}
    if not dedans:
        return None

    enfants = {}
    for n, p in dedans.items():
        enfants.setdefault(p["vers"], []).append(n)
    for k in enfants:
        enfants[k].sort()

    racines = sorted([n for n, p in dedans.items() if p["genre"] == "etat"],
                     key=lambda n: int(n) if n.isdigit() else 0)

    place, x = {}, MARGE_G + 140

    def poser(n, gauche):
        """Place la piece n et sa descendance ; renvoie la largeur occupee."""
        p = dedans[n]
        fils = [f for f in enfants.get(n, []) if f in dedans]
        if not fils:
            place[n] = (gauche + 110, HAUT[p["genre"]])
            return 240
        pris, g = 0, gauche
        for f in fils:
            w = poser(f, g)
            g += w
            pris += w
        centre = gauche + pris / 2.0
        place[n] = (centre, HAUT[p["genre"]])
        return pris

    for r in racines:
        x += poser(r, x)

    # les actions d'une meme clef s'empilent au lieu de s'etaler
    for cl in [n for n, p in dedans.items() if p["genre"] == "clef"]:
        actes = [a for a in enfants.get(cl, []) if a in dedans]
        if len(actes) > 1 and cl in place:
            cx = place[cl][0]
            for i, a in enumerate(actes):
                place[a] = (cx, HAUT["action"] + i * PAS)

    for n, xy in pose.items():
        if n in place:
            place[n] = tuple(xy)

    largeur = max([xy[0] for xy in place.values()] or [800]) + 200 + MARGE_D
    hauteur = max([xy[1] for xy in place.values()] or [600]) + 140

    cites_m = sorted({m for p in dedans.values() for m in p.get("moyens", [])
                      if m in inventaire})
    cites_o = sorted({p.get("office", u"") for p in dedans.values()} & set(inventaire))
    hauteur = max(hauteur, 200 + 56 * max(len(cites_m), len(cites_o)))

    S = []
    A = S.append
    A(u'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %g %g" width="%g" height="%g" font-family="Georgia,serif">'
      % (largeur, hauteur, largeur, hauteur))
    A(u'<defs><filter id="toile"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3"/>'
      u'<feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope="0.05"/>'
      u'</feComponentTransfer><feComposite operator="in" in2="SourceGraphic"/></filter></defs>')
    A(u'<rect width="%g" height="%g" fill="#f6f1e4"/>' % (largeur, hauteur))
    A(u'<rect width="%g" height="%g" fill="#000" filter="url(#toile)" opacity="0.5"/>' % (largeur, hauteur))

    # les deux bords, traces a la craie
    A(u'<line x1="%g" y1="30" x2="%g" y2="%g" stroke="#b9ad92" stroke-width="2" stroke-dasharray="9 7"/>'
      % (MARGE_G - 30, MARGE_G - 30, hauteur - 30))
    A(u'<line x1="%g" y1="30" x2="%g" y2="%g" stroke="#b9ad92" stroke-width="2" stroke-dasharray="9 7"/>'
      % (largeur - MARGE_D + 30, largeur - MARGE_D + 30, hauteur - 30))
    A(u'<text x="40" y="52" font-size="17" letter-spacing="2" fill="#8a7f66">LES MOYENS</text>')
    A(u'<text x="%g" y="52" font-size="17" letter-spacing="2" fill="#8a7f66">LES OFFICES</text>' % (largeur - MARGE_D + 62))
    A(u'<text x="%g" y="46" font-size="26" text-anchor="middle" fill="#3c342a" letter-spacing="1">%s</text>'
      % ((largeur) / 2.0, ech(affaire.upper())))

    # ficelles vers les bords : une action va chercher son jeton et son carre
    bord = {}
    for i, m in enumerate(cites_m):
        bord[m] = (130, 96 + i * 56)
    for i, o in enumerate(cites_o):
        bord[o] = (largeur - 130, 96 + i * 56)

    for n, p in dedans.items():
        if p["genre"] != "action" or n not in place:
            continue
        ax, ay = place[n]
        for cible in list(p.get("moyens", [])) + [p.get("office", u"")]:
            if cible in bord:
                bx, by = bord[cible]
                A(u'<path d="M%g,%g C%g,%g %g,%g %g,%g" fill="none" stroke="#9c8f74" '
                  u'stroke-width="1.4" opacity="0.75"/>'
                  % (ax, ay, (ax + bx) / 2.0, ay, (ax + bx) / 2.0, by, bx, by))

    # l'aplomb : la chaine causale
    for n, p in dedans.items():
        if p["vers"] in place and n in place:
            x1, y1 = place[p["vers"]]
            x2, y2 = place[n]
            A(u'<path d="M%g,%g C%g,%g %g,%g %g,%g" fill="none" stroke="#6b5f4a" stroke-width="2.2"/>'
              % (x1, y1 + 26, x1, (y1 + y2) / 2.0, x2, (y1 + y2) / 2.0, x2, y2 - 22))

    def piece(x, y, genre, num, nom, sous=u""):
        f = FORME[genre](x, y)
        A(u'<path d="%s" fill="%s" stroke="#4a4033" stroke-width="2"/>' % (f, REMPLI[genre]))
        enc = ENCRE.get(genre, "#2f2a22")
        A(u'<text x="%g" y="%g" font-size="11" text-anchor="middle" fill="%s" opacity="0.75">%s</text>'
          % (x, y - (20 if genre != "action" else 10), enc, ech(num)))
        lg = coupe(nom, 26 if genre != "action" else 30)
        for i, l in enumerate(lg):
            A(u'<text x="%g" y="%g" font-size="%g" text-anchor="middle" fill="%s">%s</text>'
              % (x, y - 2 + i * 14 + (0 if len(lg) > 1 else 5), 13 if genre != "action" else 12, enc, ech(l)))
        if sous:
            A(u'<text x="%g" y="%g" font-size="10" text-anchor="middle" fill="%s" opacity="0.7">%s</text>'
              % (x, y + 24, enc, ech(sous)))

    # la tuile de l'affaire, au centre haut
    piece(largeur / 2.0, HAUT["affaire"], "affaire", u"", affaire)

    for n, p in dedans.items():
        if n not in place:
            continue
        x, y = place[n]
        sous = u""
        if p["genre"] == "clef":
            sous = p["cellules"][-2] if len(p["cellules"]) > 2 else u""
        if p["genre"] == "action":
            sous = p["cellules"][-2]
        piece(x, y, p["genre"], p["num"], p["nom"], sous)

    for cle, (bx, by) in bord.items():
        inv = inventaire[cle]
        if inv["genre"] == "moyen":
            A(u'<circle cx="%g" cy="%g" r="27" fill="%s" stroke="#4a4033" stroke-width="2"/>' % (bx, by, REMPLI["moyen"]))
        else:
            A(u'<rect x="%g" y="%g" width="58" height="46" rx="3" fill="%s" stroke="#4a4033" stroke-width="3"/>'
              % (bx - 29, by - 23, REMPLI["office"]))
        A(u'<text x="%g" y="%g" font-size="11" text-anchor="middle" fill="#2f2a22">%s</text>' % (bx, by + 4, ech(cle)))
        for i, l in enumerate(coupe(inv["nom"], 18)):
            A(u'<text x="%g" y="%g" font-size="11" text-anchor="middle" fill="#4a4033">%s</text>'
              % (bx, by + 42 + i * 13, ech(l)))

    A(u'<text x="40" y="%g" font-size="11" fill="#8a7f66">La nappe montre ; le registre fait foi. '
      u'Dessinee depuis les registres — rien ici n\'a ete saisi deux fois.</text>' % (hauteur - 20))
    A(u'</svg>')
    return u"\n".join(S)


def slug(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = u"".join(c for c in s if not unicodedata.combining(c))
    return u"-".join(u"".join(c if c.isalnum() else u" " for c in s).split())


if __name__ == "__main__":
    args = sys.argv[1:]
    sortie = os.path.join(racine, "ecrans", "nappes")
    if "--sortie" in args:
        i = args.index("--sortie")
        sortie = args[i + 1]
        args = args[:i] + args[i + 2:]
    filtre = None
    if "--affaire" in args:
        i = args.index("--affaire")
        filtre = args[i + 1]

    pieces, inventaire, pose = charger()
    affaires = sorted({p["affaire"] for p in pieces.values() if p["affaire"]})
    if filtre:
        affaires = [a for a in affaires if slug(filtre) in slug(a)]
    if not os.path.isdir(sortie):
        os.makedirs(sortie)

    for a in affaires:
        svg = dessiner(a, pieces, inventaire, pose)
        if not svg:
            continue
        f = os.path.join(sortie, slug(a) + ".svg")
        io.open(f, "w", encoding="utf-8").write(svg)
        n = len([1 for p in pieces.values() if p["affaire"] == a])
        sys.stdout.write("%-34s %3d pieces -> %s\n" % (slug(a), n, os.path.relpath(f, racine)))
