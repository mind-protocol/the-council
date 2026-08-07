# -*- coding: utf-8 -*-
"""La correspondance des salles — du vocabulaire du jeu à celui du modèle 3D.

    python scripts/materialisation/salles.py            la table
    python scripts/materialisation/salles.py --verifier ce qui ne tombe nulle part

Le jeu parle en salles (`ecrans/modules/plans.js` : « la roukerie », « la chambre
de la Table Peinte »). C'est ce vocabulaire-là qui est partout ailleurs : dans
l'en-tête de lieu du bandeau, dans le champ `salle` des items du flux, dans les
`participants` des scènes du journal, dans les clics de pensée.

Le modèle 3D, lui, parle en corps de logis, engendrés par `programme.py` depuis
un programme architectural. Les deux listes se recouvrent à peine : onze noms
communs sur trente-quatre.

Ce module est le pont, et il n'a qu'un travail : rendre, pour une salle du jeu,
UN POINT EN MÈTRES dans le modèle. Rien d'autre ne doit connaître les deux
vocabulaires à la fois — sinon la correspondance se met à exister en trois
exemplaires légèrement différents, et personne ne sait plus lequel fait foi.

Trois façons d'ancrer, et le choix se lit dans la table :
  · `corps` — la salle EST un corps de l'anneau (parfois à un étage donné) ;
  · `repere` — elle est ailleurs dans le modèle : une tour, le quai, la montée,
    le bourg, le chemin de ronde ;
  · `absent` — le modèle ne la bâtit pas encore, et on dit pourquoi. Une salle
    absente rend un point plausible ET se signale : mieux vaut une lacune vue
    qu'un ancrage inventé qu'on prendra pour une mesure.
"""
import math
import sys

import lieux as Li
import peyredragon as P
import programme as Prog


# ---------------------------------------------------------------------------
# LA TABLE — salle du jeu → où elle se tient dans le modèle
#
# Quand aucun corps ne porte le même nom, on prend celui qui joue le MÊME RÔLE,
# et le commentaire dit lequel. C'est un choix d'architecte, pas une équivalence
# de dictionnaire : « l'antichambre » du plan est le passage des écrans du
# programme parce que c'est la même pièce dans la vie d'un château — le sas
# entre le service et la grande salle.
# ---------------------------------------------------------------------------
TABLE = {
    # --- ce qui porte déjà le même nom -----------------------------------
    "grande-salle":   ("corps", "grande-salle", 0),
    "cuisines":       ("corps", "cuisines", 0),
    "forge":          ("corps", "forge", 0),
    "septuaire":      ("corps", "septuaire", 0),
    "roukerie":       ("corps", "roukerie", 2),   # les corbeaux sont en haut
    "archives":       ("corps", "archives", 0),
    "chambre-enfants": ("corps", "chambre-enfants", 1),
    "cellier":        ("cave", "cellier", -1),
    "salle-froide":   ("cave", "salle-froide", -1),
    "cachots":        ("cave", "cachots", -1),

    # --- le donjon et ses étages -----------------------------------------
    "tambour-de-pierre": ("repere", "tambour", 0),
    "table-peinte":   ("repere", "tambour-sommet", 4),

    # --- les tours --------------------------------------------------------
    "tour-dragon-mer": ("repere", "tour-0", 0),
    "guivre-des-vents": ("repere", "tour-1", 0),

    # --- même rôle, autre nom ---------------------------------------------
    # Le retrait du seigneur EST l'appartement privé, derrière l'estrade.
    "appartements-reine": ("corps", "retrait", 1),
    "chambres-hotes": ("corps", "hotes", 1),
    # Le sas entre le service et la grande salle : c'est le passage des écrans.
    "antichambre":    ("corps", "ecrans", 0),
    # Les communs, c'est là où logent et travaillent les gens de maison.
    "communs":        ("corps", "garnison", 0),
    # L'officine d'un mestre et l'infirmerie sont la même odeur et le même
    # établi : on n'en bâtit pas deux.
    "officine":       ("corps", "infirmerie", 0),
    # Les étuves partagent le feu et l'eau de la buanderie.
    "etuves":         ("corps", "buanderie", 0),
    # La petite salle du levant : la pièce de retrait qui donne sur la galerie.
    "salle-levant":   ("corps", "galerie", 0),

    # --- dehors, mais dans le modèle --------------------------------------
    "cour":           ("repere", "cour", 0),
    "porte-de-mer":   ("repere", "porte", 0),
    "grand-escalier": ("repere", "montee", 0),
    "quai":           ("repere", "quai", 0),
    "greve":          ("repere", "greve", 0),
    "bourg":          ("repere", "bourg", 0),
    "chemin-ronde":   ("repere", "chemin-de-ronde", 0),

    # --- ce que le modèle ne bâtit pas encore ------------------------------
    "jardin-aegon":   ("absent", "cour", 0,
                       "Aucun jardin dans le programme : la cour est pavée d'un "
                       "bout à l'autre. On ancre au nord de la cour, faute de mieux."),
    "galeries":       ("absent", "sous-la-cour", -2,
                       "Les galeries de verredragon descendent sous la mer ; le "
                       "modèle ne creuse que les trois caves de l'anneau."),
    "fosses":         ("absent", "flanc-montagne", 0,
                       "Les fosses aux dragons sont dans le flanc du Dragonmont, "
                       "hors de l'enceinte : rien n'est bâti là."),
    "lices":          ("absent", "hors-porte", 0,
                       "Les lices sont hors les murs ; le modèle s'arrête à la "
                       "courtine et au bourg."),
    "baraques":       ("absent", "hors-porte", 0,
                       "Mêmes baraques que celles du bourg : pas de corps propre."),
    "porte-dragon":   ("absent", "porte-opposee", 0,
                       "Le modèle n'a qu'UNE porte. Une seconde entrée changerait "
                       "la défense et le graphe de circulation : à décider, pas à "
                       "supposer."),
}


# ---------------------------------------------------------------------------
def _milieu(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def _reperes(p):
    """Les points du modèle qui ne sont pas des corps de l'anneau."""
    cour = _milieu(p["facade"])
    tam = P._monde((-8, -4))
    montee = P._lacets()
    mi = montee[len(montee) // 2]
    feux = P.feux()
    bourg = (sum(f["x"] for f in feux) / len(feux),
             sum(f["y"] for f in feux) / len(feux))
    porte = P._monde(P.PORTE)
    # le chemin de ronde : sur la courtine, au pan opposé à la porte
    mur = [P._monde(q) for q in P.ENCEINTE]
    pan, _ = P._pan_de_la_porte()
    face = mur[(pan + len(mur) // 2) % len(mur)]

    r = {
        "cour":            (cour[0], cour[1], P.ASSISE),
        "tambour":         (tam[0], tam[1], P.ASSISE),
        "tambour-sommet":  (tam[0] - 6, tam[1] + 4, P.ASSISE + 52),
        "porte":           (porte[0], porte[1], P.ASSISE),
        "montee":          (mi[0], mi[1], mi[2]),
        "quai":            (P.QUAI[0], P.QUAI[1], 3.4),
        "greve":           (P.QUAI[0] - P._SA * 150, P.QUAI[1] + P._CA * 150, 1.5),
        "bourg":           (bourg[0], bourg[1], P._sol(*bourg)),
        "chemin-de-ronde": (face[0], face[1], P.ASSISE + 12.9),
        # les ancrages de secours des salles absentes
        "sous-la-cour":    (cour[0], cour[1], P.ASSISE - 12.0),
        "flanc-montagne":  (P.CHATEAU[0] - 340, P.CHATEAU[1] + 120, 0.0),
        "hors-porte":      (porte[0] + P._D[0] * 70, porte[1] + P._D[1] * 70, 0.0),
        "porte-opposee":   (face[0], face[1], P.ASSISE),
    }
    for k in ("flanc-montagne", "hors-porte"):
        r[k] = (r[k][0], r[k][1], P._sol(r[k][0], r[k][1]))
    for i, (x, y, ray, h, fl) in enumerate(P.TOURS):
        cx, cy = P._monde((x, y))
        r["tour-%d" % i] = (cx, cy, P.ASSISE)
    return r


def correspondance():
    """Chaque salle du jeu, avec son point en mètres et d'où il vient."""
    p = Prog.plan()
    corps = {c["id"]: c for c in p["corps"]}
    caves = {c["id"]: c for c in p["caves"]}
    rep = _reperes(p)

    out = {}
    for cle, e in TABLE.items():
        genre, ou, niveau = e[0], e[1], e[2]
        note = e[3] if len(e) > 3 else None
        point, source = None, None
        if genre == "corps" and ou in corps:
            m = corps[ou]["milieu"]
            point = (m[0], m[1], Prog.niv(niveau))
            source = corps[ou]["nom"]
        elif genre == "cave" and ou in caves:
            m = caves[ou]["milieu"]
            point = (m[0], m[1], Prog.niv(niveau))
            source = caves[ou]["nom"]
        elif ou in rep:
            point = rep[ou]
            source = ou
        out[cle] = {"id": cle, "genre": genre, "vers": ou, "niveau": niveau,
                    "ou": point, "source": source, "note": note}
    return out


_CACHE = None


def ancrage(salle_id):
    """Le point en mètres d'une salle du jeu, ou None si elle n'est pas connue."""
    global _CACHE
    if _CACHE is None:
        _CACHE = correspondance()
    e = _CACHE.get(salle_id)
    return e["ou"] if e else None


if __name__ == "__main__":
    C = correspondance()
    jeu = [s["id"] for s in Li.lire_plan()[1]]
    p = Prog.plan()
    pris = {e["vers"] for e in C.values() if e["genre"] in ("corps", "cave")}

    print("LA CORRESPONDANCE  (%d salles du jeu)" % len(jeu))
    for genre, titre in (("corps", "DANS UN CORPS DE L'ANNEAU"),
                         ("cave", "DANS UNE CAVE"),
                         ("repere", "AILLEURS DANS LE MODELE"),
                         ("absent", "PAS ENCORE BATI")):
        lignes = [e for e in C.values() if e["genre"] == genre]
        if not lignes:
            continue
        print("\n  " + titre)
        for e in sorted(lignes, key=lambda x: x["id"]):
            o = e["ou"]
            print("    %-18s -> %-16s niv %+d  %s"
                  % (e["id"], e["vers"], e["niveau"],
                     "%8.1f %8.1f %6.1f" % o if o else "  INTROUVABLE"))
            if e["note"]:
                print("        %s" % e["note"])

    manque = [s for s in jeu if s not in C]
    orphelins = [c["id"] for c in p["corps"] if c["id"] not in pris
                 and not c["id"].startswith("appentis")]
    print("\n  %d salles du jeu ancrées, %d sans ancrage" % (len(C), len(manque)))
    if manque:
        print("  ! SANS ANCRAGE : " + ", ".join(manque))
    print("\n  %d corps du modèle qu'aucune salle du jeu ne nomme :" % len(orphelins))
    print("    " + ", ".join(sorted(orphelins)))
    print("    (ce n'est pas un défaut : le programme architectural bâtit ce")
    print("     qu'un château a, le plan du jeu ne nomme que ce qu'on y joue.)")
    if "--verifier" in sys.argv:
        creux = [e["id"] for e in C.values() if not e["ou"]]
        print("\n  " + ("tout tombe quelque part."
                        if not creux else "! POINTS INTROUVABLES : " + ", ".join(creux)))
