# -*- coding: utf-8 -*-
"""PLANCHES — le plan de la ville en images, à trois échelles, pour le REGARDER.

    python scripts/monde/planches.py                    tout, les trois échelles
    python scripts/monde/planches.py --sur donjon-rouge un lieu, les trois
    python scripts/monde/planches.py --echelle rue      une échelle seulement
    python scripts/monde/planches.py --grille           la trame de 100 m par-dessus

POURQUOI. `plan_ville.py` cuit deux mégaoctets de chemins SVG et dit combien de
signes il a écrits — ce qui ne dit RIEN de ce qu'on verra. Un monument à la
mauvaise échelle, une courtine qui coupe une rue, un quartier que le semis a
laissé vide, une emprise qui a mangé trois cents maisons de trop : tout cela est
invisible dans un compte de signes et saute aux yeux sur une planche. Or la
seule façon de regarder, jusqu'ici, était d'ouvrir la partie et de naviguer à la
molette — c'est-à-dire de ne jamais regarder.

TROIS ÉCHELLES, ET CE SONT CELLES DU CLIENT. `carte-ville.js` bascule ses
couches à 12 et à 1,2 mètre par pixel ; on reprend les mêmes seuils, sinon on
contrôle une carte que personne ne verra jamais :

    ville      la ville entière d'un coup      ~4 m/px   ce qui fait masse
    quartier   des carrés de 900 m             ~0,9 m/px le tissu, rue par rue
    rue        des carrés de 200 m             ~0,2 m/px la façade et la porte

DU SVG, PAS DU PNG, et ce n'est pas un pis-aller : c'est le format du plan lui-
même. Une planche s'ouvre au navigateur, se zoome sans bouillie, et pèse ce que
pèse un dessin. Aucune dépendance à installer — ce script ne sort jamais de la
bibliothèque standard.

La sortie va dans `dessins/planches/`, avec un `index.html` qui les enfile.
"""
import argparse
import json
import math
import os
import re

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PREFIXES = {"port-real": "portreal", "peyredragon": "peyredragon"}

# Les trois échelles : le côté du carré en mètres (None = la ville entière), et
# la largeur de l'image. C'est le rapport des deux qui donne le mètre par pixel,
# et c'est lui qui commande tout le reste.
ECHELLES = {
    "ville":    {"cote": None, "px": 1600},
    "quartier": {"cote": 900., "px": 1100},
    "rue":      {"cote": 200., "px": 1000},
}

# LA PALETTE EST CELLE DE LA NUIT, comme le jeu. Une planche claire est plus
# jolie et ment sur ce que le joueur verra : c'est le soir qu'on ouvre ce plan.
# Les valeurs sont recopiées de `ecrans/jeu.css` (`@media prefers-color-scheme:
# dark`) ; si l'une bouge là-bas, elle bouge ici — un contrôle qui ne montre pas
# les vraies couleurs ne contrôle rien.
SOL, EAU, NIVEAU = "#1b1712", "#1d2c33", "rgba(220,190,140,.16)"
MUR, MUR_TOUR, VOIE = "#6a6459", "#847d70", "#6d5c42"
BATI_TRAIT, ENCRE = "rgba(220,190,140,.22)", "#e8dcc8"
FAMILLES = {"institution": "#5e2622", "culte": "#4a4258", "civique": "#2f3f47",
            "commerce": "#3a3a2e", "artisanat": "#3d362c", "plaisir": "#442c33",
            "service": "#2f382c", "nuisance": "#2b2822", "habitat": "#2e2820"}
# La largeur des voies, en mètres — les mêmes proportions que la feuille de
# style, sans le plancher en pixels qui n'a de sens qu'à l'écran.
LARGES = {"artere": 11., "quai": 8., "rue": 6., "abord": 4., "ruelle": 3.,
          "escalier": 2.}


def lire(prefixe):
    chem = os.path.join(RACINE, "monde", prefixe + ".plan2d.json")
    if not os.path.exists(chem):
        raise SystemExit("pas de plan cuit : " + chem +
                         "\nlance d'abord  python scripts/monde/plan_ville.py")
    with open(chem, encoding="utf-8") as f:
        return json.load(f)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# --- où l'on braque la planche ----------------------------------------------
# On accepte un nom de repère, un identifiant de monument, ou deux nombres. Le
# nom se cherche SANS ACCENTS ET SANS CASSE : personne ne tape « La porte de la
# Gadoue » à la lettre près, et un outil qui l'exige n'est pas utilisé.
def _plat(s):
    s = str(s).lower()
    for a, b in zip("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc"):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "", s)


def viser(plan, quoi):
    """Rend (x, y, nom) — le point à cadrer, ou None."""
    if quoi is None:
        return None
    m = re.match(r"^\s*(-?[\d.]+)\s*[,; ]\s*(-?[\d.]+)\s*$", quoi)
    if m:
        return float(m.group(1)), float(m.group(2)), "%s, %s" % m.groups()
    cible = _plat(quoi)
    for r in plan.get("reperes") or []:
        if cible in (_plat(r["nom"]), _plat(r.get("genre", ""))):
            return r["x"], r["y"], r["nom"]
    # un monument : on prend le milieu de sa couche de bâti
    d = (plan.get("bati") or {}).get(quoi)
    if d:
        n = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)]
        xs, ys = n[0::2], n[1::2]
        nom = ((plan.get("types") or {}).get(quoi) or {}).get("nom", quoi)
        return (min(xs) + max(xs)) / 2., (min(ys) + max(ys)) / 2., nom
    raise SystemExit("cible inconnue : %s\nessaie un nom de repère, un type de "
                     "bâti (donjon-rouge), ou « x,y »." % quoi)


# --- tailler avant d'écrire --------------------------------------------------
# LE CADRAGE NE SUFFIT PAS. Un `viewBox` montre un carré de deux cents mètres,
# mais le fichier porte quand même les quarante mille silhouettes de la ville :
# la première série faisait 213 Mo pour cinquante-neuf planches, dont 99 % de
# chemins hors champ. On coupe donc à la source — un chemin cuit est une suite
# de sous-chemins (`M…`), chacun une silhouette ou une polyligne, et l'on ne
# garde que ceux dont la boîte touche le cadre.
#
# On ne découpe RIEN au ciseau : un bâtiment à cheval sur le bord est gardé
# entier, et le `viewBox` le coupe à l'affichage comme il l'a toujours fait. Une
# vraie découpe géométrique demanderait un rognage de polygones pour un gain
# nul — c'est de l'affichage, pas de la donnée.
_NOMBRE = re.compile(r"-?\d+(?:\.\d+)?")


def tailler(d, X, Y, W, H, marge=None):
    if not d:
        return d
    m = marge if marge is not None else max(W, H) * .12
    x0, y0, x1, y1 = X - m, Y - m, X + W + m, Y + H + m
    garde = []
    for bout in d.split("M"):
        if not bout:
            continue
        n = _NOMBRE.findall(bout)
        if len(n) < 2:
            continue
        xs = [float(v) for v in n[0::2]]
        ys = [float(v) for v in n[1::2]]
        if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
            continue
        garde.append(bout)
    return ("M" + "M".join(garde)) if garde else ""


# --- une planche -------------------------------------------------------------
def planche(plan, X, Y, W, H, px, titre, grille=False):
    """Une image, en mètres, cadrée sur [X, X+W] × [Y, Y+H]."""
    mpp = W / float(px)
    # LE GRAIN, COMME AU CLIENT : de loin les ruelles font un voile et le trait
    # des maisons fait du gris. On éteint les mêmes couches aux mêmes seuils.
    toile = mpp <= 2.
    trait = mpp <= 1.2
    o = ['<rect x="%g" y="%g" width="%g" height="%g" fill="%s"/>' % (X, Y, W, H, SOL)]
    coupe = lambda d: tailler(d, X, Y, W, H)
    if coupe(plan.get("cote")):
        o.append('<path d="%s" fill="%s"/>' % (coupe(plan["cote"]), EAU))
    for n in plan.get("niveaux") or []:
        if coupe(n["d"]):
            o.append('<path d="%s" fill="none" stroke="%s" stroke-width="%g"/>'
                     % (coupe(n["d"]), NIVEAU, max(1., mpp)))
    for g, d in (plan.get("voies") or {}).items():
        if not toile and g in ("ruelle", "abord", "escalier"):
            continue
        d = coupe(d)
        if d:
            o.append('<path d="%s" fill="none" stroke="%s" stroke-width="%g" '
                     'opacity=".55" stroke-linejoin="round" stroke-linecap="round"/>'
                     % (d, VOIE, max(LARGES.get(g, 3.), 1.4 * mpp)))
    for u, d in (plan.get("bati") or {}).items():
        cat = ((plan.get("types") or {}).get(u) or {}).get("cat", "habitat")
        d = coupe(d)
        if not d:
            continue
        o.append('<path d="%s" fill="%s"%s/>'
                 % (d, FAMILLES.get(cat, FAMILLES["habitat"]),
                    ' stroke="%s" stroke-width="%g"' % (BATI_TRAIT, .5 * mpp)
                    if trait else ""))
    r = plan.get("rempart") or {}
    if coupe(r.get("courtine")):
        o.append('<path d="%s" fill="none" stroke="%s" stroke-width="%g" '
                 'stroke-linejoin="round" stroke-linecap="round"/>'
                 % (coupe(r["courtine"]), MUR,
                    max(r.get("epaisseur_m") or 6., 2.2 * mpp)))
        if coupe(r.get("tours")):
            o.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%g"/>'
                     % (coupe(r["tours"]), MUR_TOUR, MUR, .6 * mpp))
    # LA TRAME EST LA MESURE, et c'est elle qui fait de la planche un contrôle
    # plutôt qu'une image : cent mètres au carré, posés sur des coordonnées
    # rondes, et l'on lit l'emprise d'un monument sans rien calculer.
    if grille:
        pas = 100. if mpp < 3 else 500.
        t = []
        x = math.ceil(X / pas) * pas
        while x < X + W:
            t.append("M%g %gV%g" % (x, Y, Y + H)); x += pas
        y = math.ceil(Y / pas) * pas
        while y < Y + H:
            t.append("M%g %gH%g" % (X, y, X + W)); y += pas
        o.append('<path d="%s" fill="none" stroke="%s" stroke-width="%g" '
                 'opacity=".22"/>' % ("".join(t), ENCRE, .6 * mpp))
    for p in (r.get("portes") or []):
        if X <= p["x"] <= X + W and Y <= p["y"] <= Y + H:
            o.append(_etiquette(p["x"], p["y"], p["nom"], mpp, "#c8a25e"))
    if mpp > .5:
        for q in plan.get("quartiers") or []:
            if X <= q["x"] <= X + W and Y <= q["y"] <= Y + H:
                o.append('<text x="%g" y="%g" fill="%s" opacity=".5" '
                         'font-family="Georgia,serif" font-size="%g" '
                         'text-anchor="middle">%s</text>'
                         % (q["x"], q["y"], ENCRE, 16 * mpp, esc(q["nom"])))
    o.append(_cartouche(X, Y, W, H, mpp, titre))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%g %g %g %g" '
            'width="%d" height="%d">%s</svg>'
            % (X, Y, W, H, px, int(round(px * H / W)), "".join(o)))


def _etiquette(x, y, nom, mpp, teinte):
    return ('<g><circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" '
            'stroke-width="%g"/><text x="%g" y="%g" fill="%s" '
            'font-family="Georgia,serif" font-size="%g" paint-order="stroke" '
            'stroke="%s" stroke-width="%g">%s</text></g>'
            % (x, y, 7 * mpp, teinte, 1.6 * mpp, x + 11 * mpp, y - 8 * mpp,
               ENCRE, 13 * mpp, SOL, 3.5 * mpp, esc(nom)))


def _cartouche(X, Y, W, H, mpp, titre):
    """Le titre, l'échelle et les coordonnées — sans quoi une planche n'est
    qu'une jolie image dont on ne sait pas d'où elle vient."""
    b = 10. ** math.floor(math.log10(W / 5.))          # une règle ronde
    b = b * (5 if W / 5. / b >= 5 else (2 if W / 5. / b >= 2 else 1))
    x0, y0 = X + W * .022, Y + H * .955
    return ('<g font-family="Georgia,serif" fill="%s">'
            '<text x="%g" y="%g" font-size="%g" paint-order="stroke" stroke="%s" '
            'stroke-width="%g">%s</text>'
            '<text x="%g" y="%g" font-size="%g" opacity=".7" paint-order="stroke" '
            'stroke="%s" stroke-width="%g">%.2f m/px — coin %d, %d — %d × %d m</text>'
            '<path d="M%g %gh%g" stroke="%s" stroke-width="%g"/>'
            '<text x="%g" y="%g" font-size="%g" text-anchor="middle" '
            'paint-order="stroke" stroke="%s" stroke-width="%g">%g m</text></g>'
            % (ENCRE,
               X + W * .022, Y + H * .05, 17 * mpp, SOL, 4 * mpp, esc(titre),
               X + W * .022, Y + H * .082, 12 * mpp, SOL, 3 * mpp,
               mpp, round(X), round(Y), round(W), round(H),
               x0, y0, b, ENCRE, 2.2 * mpp,
               x0 + b / 2., y0 - 6 * mpp, 12 * mpp, SOL, 3 * mpp, b))


# --- la série ----------------------------------------------------------------
def series(plan, cible, echelles, grille):
    """Rend [(nom_de_fichier, titre, svg)] — ce qu'il y a à écrire."""
    x0, y0, x1, y1 = plan["bornes"]
    out = []
    for nom in echelles:
        e = ECHELLES[nom]
        if e["cote"] is None:                      # la ville entière, une plaque
            out.append(("ville", "La ville entière",
                        planche(plan, x0, y0, x1 - x0, y1 - y0, e["px"],
                                "Port-Réal — la ville entière", grille)))
            continue
        c = e["cote"]
        if cible:                                  # cadré sur un point
            cx, cy, titre = cible
            out.append(("%s-%s" % (nom, _plat(titre)),
                        "%s — %s" % (titre, nom),
                        planche(plan, cx - c / 2., cy - c / 2., c, c, e["px"],
                                "%s — %g m de côté" % (titre, c), grille)))
            continue
        if nom == "rue":
            # PAS DE GRILLE COMPLÈTE À DEUX CENTS MÈTRES : ce serait cinq cents
            # planches dont personne n'ouvrirait la dixième. On ne tire que ce
            # qui se cherche — les repères et les monuments.
            for r in (plan.get("reperes") or []):
                out.append(("rue-%s" % _plat(r["nom"]), "%s — rue" % r["nom"],
                            planche(plan, r["x"] - c / 2., r["y"] - c / 2., c, c,
                                    e["px"], "%s — %g m de côté" % (r["nom"], c),
                                    grille)))
            continue
        j = 0
        y = y0
        while y < y1:
            i, x = 0, x0
            while x < x1:
                out.append(("%s-%02d-%02d" % (nom, i, j),
                            "%s %d-%d" % (nom, i, j),
                            planche(plan, x, y, c, c, e["px"],
                                    "%s — carré %d, %d" % (nom, i, j), grille)))
                i += 1; x += c
            j += 1; y += c
    return out


INDEX = """<!doctype html><meta charset="utf-8"><title>Planches — %s</title>
<style>body{background:#141210;color:#e8dcc8;font:15px Georgia,serif;margin:24px}
h1{font-weight:400;font-size:20px}h2{font-weight:400;font-size:15px;opacity:.7;
margin:28px 0 8px}a{color:#c8a25e}ul{columns:3;list-style:none;padding:0}
li{margin:.25em 0}p{opacity:.6;max-width:60em}</style>
<h1>Port-Réal — %d planches</h1>
<p>Cuit le %s. Chaque planche porte son échelle en mètres par pixel, le coin
qu'elle cadre et une règle. Ouvre-les dans un onglet : le SVG se zoome sans
bouillie.</p>%s"""


def main():
    ap = argparse.ArgumentParser(
        description="Le plan de la ville en planches, pour le regarder")
    ap.add_argument("--lieu", default="port-real")
    ap.add_argument("--sur", default=None,
                    help="un repère, un type de bâti (donjon-rouge), ou « x,y »")
    ap.add_argument("--echelle", action="append", choices=sorted(ECHELLES),
                    help="une seule échelle (répétable) ; par défaut les trois")
    ap.add_argument("--grille", action="store_true",
                    help="la trame de mesure par-dessus")
    ap.add_argument("--sortie", default=os.path.join("dessins", "planches"))
    a = ap.parse_args()

    prefixe = PREFIXES.get(a.lieu)
    if not prefixe:
        raise SystemExit("lieu inconnu : " + a.lieu)
    plan = lire(prefixe)
    cible = viser(plan, a.sur)
    echelles = a.echelle or ["ville", "quartier", "rue"]
    if cible and "ville" in echelles and len(echelles) > 1:
        pass                       # la ville entière reste utile comme repère

    dossier = os.path.join(RACINE, a.sortie)
    os.makedirs(dossier, exist_ok=True)
    faites = series(plan, cible, echelles, a.grille)
    par = {}
    for cle, titre, svg in faites:
        chem = os.path.join(dossier, cle + ".svg")
        with open(chem, "w", encoding="utf-8") as f:
            f.write(svg)
        par.setdefault(cle.split("-")[0], []).append((cle, titre))
    corps = "".join(
        "<h2>%s — %d</h2><ul>%s</ul>"
        % (g, len(v), "".join('<li><a href="%s.svg">%s</a></li>' % (c, esc(t))
                              for c, t in v))
        for g, v in par.items())
    import datetime
    with open(os.path.join(dossier, "index.html"), "w", encoding="utf-8") as f:
        f.write(INDEX % (esc(a.lieu), len(faites),
                         datetime.datetime.now().strftime("%d/%m %H:%M"), corps))
    for g, v in par.items():
        print("  %-9s %3d planches" % (g, len(v)))
    print("%s — %d planches, index.html" % (a.sortie, len(faites)))


if __name__ == "__main__":
    main()
