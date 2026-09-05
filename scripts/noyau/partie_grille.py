#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
partie_grille.py — la position en grille, l'échiquier plutôt que l'arbre.

L'arbre (partie_ascii.py) montre les LIENS : quoi pend sous quoi. Il ne montre
pas les CREUX — un état sur lequel personne n'a rien posé s'y lit comme une
feuille de plus, alors que c'est justement un endroit où l'on peut entrer.
Cette grille répond à l'autre question : où se touche-t-on, et qui est devant.

    une colonne = un point de contact (un état où quelque chose est posé)
    les rangs   = la profondeur : ce qui PRÉVAUT au contact, le contrecarré
                  derrière, les pièces engagées au fond, un rang par camp
    la réserve  = ce qui n'est engagé nulle part, hors grille, en bas

C'est la règle 8 (la préséance) qui décide du premier rang, et rien d'autre :
la grille ne juge pas, elle range ce que le greffe a déjà tranché.

**Un emoji vaut deux colonnes à l'écran et une seule pour len().** Un arbre
ancré à gauche s'en moque ; une grille à barres verticales se décale d'autant
d'emojis qu'elle contient. Toute la largeur passe donc par _larg().
"""
import unicodedata

from partie_greffe import EMOJI_CAMP

LARGEUR = 100
COLONNE = 26
GOUTTIERE = 13
INVISIBLES = (0xFE0E, 0xFE0F, 0x200D)


def _larg(t):
    """La largeur A L'ECRAN.

    Se lit par SEQUENCES et non par caracteres, sinon la grille se decale d'une
    colonne a chaque emoji du plan de base : U+2694 seul vaut une colonne, mais
    U+2694 U+FE0F — la meme epee, presentee en emoji — en vaut deux, et c'est
    la forme que le greffe ecrit partout. Le selecteur ne se compte donc pas :
    il PROMEUT le signe qui le precede."""
    t = t or ""
    n, i = 0, 0
    while i < len(t):
        c = t[i]
        suite = t[i + 1] if i + 1 < len(t) else ""
        i += 1
        if unicodedata.combining(c) or ord(c) in INVISIBLES:
            continue
        if suite and ord(suite) == 0xFE0F:      # presente en emoji : deux colonnes
            n += 2
            continue
        n += 2 if (unicodedata.east_asian_width(c) in "WF" or ord(c) >= 0x1F300) else 1
    return n


def _pose(t, large):
    """Le texte coupe a la largeur d'affichage, puis complete a la meme."""
    out = ""
    for c in t or "":
        if _larg(out + c) > large:
            break
        out += c
    return out + " " * max(0, large - _larg(out))


def _camp(c):
    return "%s %s" % (EMOJI_CAMP[c], c) if c else "personne"


def _piece(c):
    """Une piece en une case : son camp, son genre, son nom court, son nombre.

    Le nom est coupe au premier separateur — « Caraxes, monte par Daemon »
    devient « Caraxes » : dans une colonne de vingt-six, ce qui compte est de
    RECONNAITRE la piece, pas de la decrire, et son titre entier est dans
    l'arbre."""
    bouts = (c.get("titre") or c.get("id") or "").split(" · ")
    nb = (" " + bouts[-1]) if len(bouts) > 1 and bouts[-1].isdigit() else ""
    nom = bouts[0].split(",")[0].strip()
    for article in ("les ", "la ", "le ", "l'", "un ", "une "):
        if nom.lower().startswith(article):
            nom = nom[len(article):]
            break
    return "%s%s %s%s" % (EMOJI_CAMP[c.get("camp")], c.get("emoji") or "\U0001F4E6", nom, nb)


# ------------------------------------------------------------- les colonnes
def _engagees(vue):
    par = {}
    for c in [x for lot in (vue.get("deck") or {}).values() for x in lot] + (vue.get("eux") or []):
        for qui in c.get("engagee_par") or []:
            par.setdefault(str(qui), []).append(c)
    return par


def _sous(c):
    for s in c.get("sous") or []:
        yield s
        for y in _sous(s):
            yield y


def _colonne(vue, f, engagees):
    """Un front en colonne : l'etat vise, qui prevaut au contact, ce qui est
    contrecarre derriere, et les pieces de chaque camp au fond."""
    tete = f["tete"]
    pile = f.get("pile") or []
    cles = [c for c in pile if c.get("type") == "clef"]
    # LE PREMIER RANG EST CELUI QUI PREVAUT. Le greffe l'a deja tranche par la
    # regle 8 ; on ne fait que le mettre devant, et l'autre passe derriere.
    prevaut, derriere = tete, (cles[0] if cles else None)
    if cles and f.get("prevaut") != tete.get("camp"):
        prevaut, derriere = cles[0], tete

    pieces = {}
    for objet in [tete] + cles:
        for p in engagees.get(str(objet.get("id")), []):
            pieces.setdefault(p.get("camp"), []).append(p)
    questions = [c for c in pile + list(_sous(tete)) if c.get("type") == "question"]
    for k in cles:
        questions += [c for c in _sous(k) if c.get("type") == "question"]
    return {"sur": f.get("sur"), "sur_titre": f.get("sur_titre") or "",
            "prevaut": prevaut, "derriere": derriere, "pourquoi": f.get("pourquoi") or "",
            "questions": questions, "pieces": pieces, "contre_nous": f.get("contre_nous")}


def _colonne_clef(c, k, engagees):
    """Une cle posee sur un etat SANS blocage en face : un point de contact ou
    l'on est seul. La moitie adverse de la colonne est vide, et c'est la
    l'information — personne n'est venu."""
    pieces = {}
    for p in engagees.get(str(k.get("id")), []):
        pieces.setdefault(p.get("camp"), []).append(p)
    return {"sur": c.get("id"), "sur_titre": c.get("titre") or "",
            "prevaut": k, "derriere": None, "pourquoi": "rien en face",
            "questions": [x for x in _sous(k) if x.get("type") == "question"],
            "pieces": pieces, "contre_nous": None}


def colonnes(vue):
    """Les points de contact, dans l'ordre du greffe : les fronts d'abord, puis
    les etats qu'une cle sert sans que rien ne les bloque."""
    engagees = _engagees(vue)
    out = [_colonne(vue, f, engagees) for f in (vue.get("fronts") or [])]
    vus = set(str(c["sur"]) for c in out)
    for c in vue.get("cibles") or []:
        for k in _sous(c):
            if k.get("type") == "clef" and str(c.get("id")) not in vus:
                out.append(_colonne_clef(c, k, engagees))
                vus.add(str(c.get("id")))
    return out


def creux(vue):
    """CE QUE L'ARBRE NE MONTRE PAS : les etats sur lesquels rien n'est pose.
    Ce sont les endroits ou l'on peut entrer sans rien deloger — et pour un
    etat adverse, ceux qu'on laisse murir sans les contester."""
    pris = set(str(c["sur"]) for c in colonnes(vue))
    return [c for c in (vue.get("cibles") or []) if str(c.get("id")) not in pris]


# ---------------------------------------------------------------- le dessin
def _bande(gauche, cases, large=COLONNE):
    return " %s │ %s" % (_pose(gauche, GOUTTIERE), " │ ".join(_pose(x, large) for x in cases))


def _trait(cols, jonction="┼", trait="─", large=COLONNE):
    return " %s %s%s" % (trait * GOUTTIERE, jonction, jonction.join(trait * (large + 2) for _ in cols))


def _nom(c):
    if not c:
        return "·"
    return "%s%s %s" % (EMOJI_CAMP[c.get("camp")], c.get("emoji") or "", c.get("id") or "")


def _paquet(vue, cols, camps):
    out = [_bande("", [str(c["sur"]) for c in cols]),
           _bande("l'état", [c["sur_titre"] for c in cols]),
           _trait(cols),
           _bande("devant", [_nom(c["prevaut"]) for c in cols]),
           _bande("", ["— " + c["pourquoi"] for c in cols]),
           _bande("derrière", [_nom(c["derriere"]) for c in cols]),
           _bande("en suspens", [" ".join("❓" + (q.get("id") or "") for q in c["questions"]) or "·"
                                 for c in cols]),
           _trait(cols, jonction="╪", trait="═")]
    # LA LIGNE DE FRONT : un rang par camp, les pieces engagees seulement. Leur
    # masse se compare colonne par colonne sans qu'on ait a lire un chiffre.
    for camp in camps:
        out.append(_bande(_camp(camp), [" ".join(_piece(p) for p in c["pieces"].get(camp, [])) or "·"
                                        for c in cols]))
    return out


def _reserve(vue):
    """Ce qui n'est nulle part sur la grille : de quoi ouvrir une colonne neuve."""
    deck = vue.get("deck") or {}
    lots = [("%s dispo" % EMOJI_CAMP[vue.get("camp")],
             [c for c in (deck.get("main") or []) if not c.get("engagee_par")]),
            ("en route", [c for c in (deck.get("route") or []) if not c.get("engagee_par")]),
            ("eux, dispo", [c for c in (vue.get("eux") or [])
                            if c.get("apparence") == "libre" and not c.get("engagee_par")])]
    out = []
    for titre, lot in lots:
        if not lot:
            continue
        cases = [_piece(c) for c in lot]   # _piece porte déjà le nom : ne pas le redire
        ligne, suite = " %s │" % _pose(titre, GOUTTIERE), []
        for x in cases:
            if _larg(ligne) + _larg(x) + 3 > LARGEUR:
                suite.append(ligne)
                ligne = " %s │" % _pose("", GOUTTIERE)
            ligne += "  " + x
        out += suite + [ligne]
    return (["", " " + "─" * GOUTTIERE + "┴" + "─" * (LARGEUR - GOUTTIERE - 2)] + out) if out else []


def grille(vue, par_paquet=3):
    """La position en grille. Les colonnes se servent par paquets : au-dela de
    trois, la ligne depasse le terminal et la grille cesse d'etre lisible."""
    cols = colonnes(vue)
    trous = creux(vue)
    camps = sorted((vue.get("decks") or {}).keys())
    out = ["─" * LARGEUR,
           " %s · tour %s · vu par %s" % (vue.get("partie"), vue.get("tour"), _camp(vue.get("camp"))),
           " %d point%s de contact · %d état%s sans personne dessus"
           % (len(cols), "s" if len(cols) > 1 else "", len(trous), "s" if len(trous) > 1 else ""),
           "─" * LARGEUR]
    if not cols:
        out += ["", "  Aucun point de contact : les deux camps construisent côte à côte,",
                "  personne n'a rien posé contre personne. Il n'y a pas encore de partie."]
    for i in range(0, len(cols), par_paquet):
        out.append("")
        out += _paquet(vue, cols[i:i + par_paquet], camps)
    if trous:
        out += ["", " " + "─" * GOUTTIERE + "┴" + "─" * (LARGEUR - GOUTTIERE - 2)]
        for c in trous:
            out.append(" %s │  %s%s %-8s %s" % (_pose("sans personne", GOUTTIERE),
                                                EMOJI_CAMP[c.get("camp")], c.get("emoji") or "",
                                                c.get("id") or "",
                                                _pose(c.get("titre") or "", LARGEUR - 30)))
    out += _reserve(vue)
    return out
