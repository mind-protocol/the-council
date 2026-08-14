# -*- coding: utf-8 -*-
u"""jours_relatifs.py -- l'echelle J-N du plan, lue par une seule main.

POURQUOI CE FICHIER. Le plan de la Prise de Port-Real ne se date pas en jours
de lune : il se date A REBOURS du JOUR D'ENTREE, qui n'est pas arrete (verrou
11001 « La date n'existe pas » ; action 11026 « Poser la DATE DE TRAVAIL »,
toujours a faire). La clef 11110 en fait meme une regle de securite : « Aucune
date absolue dans un ecrit ». Les cahiers portent donc pres de cinq cents
actions datees en J-N -- et `etat_du_plan.py`, qui ne lisait que l'absolu, les
declarait « sans date ni amont ». Le rapport annoncait 588 orphelines sur 609 ;
il y en a 106.

CE QUE CE MODULE DONNE, ET RIEN DE PLUS :
  - `lire(cellule)`      : la forme relative que porte une cellule, ou None ;
  - `candidat(cellules)` : la date DUE d'une action, choisie entre ses colonnes ;
  - `canonique(f)`       : la forme d'ecriture unique, pour la colonne Jour du ;
  - `cherche_dans_etat()`: le jour J s'il existe quelque part dans l'etat ;
  - `lire_hypothese(t)`  : « 30e de la 4e lune » -> une date ;
  - `resoudre(f, J)`     : le rang absolu d'une forme, une fois J connu.

Il n'ecrit rien, et ne touche l'etat qu'en lecture.
"""
import io, json, os, re

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# -- la graphie du signe ---------------------------------------------------
# Les cahiers ecrivent le moins avec le SIGNE MOINS U+2212 (954 occurrences sur
# 987), jamais avec le trait d'union -- mais un homme qui tape vite en mettra
# un, et une regle qui ne l'accepte pas perd sa ligne en silence. On lit large,
# on ecrit etroit : U+2212 partout a l'ecriture.
# Le trait d'union reste EN DERNIER dans la classe, sinon « ‑-+ » se lit
# comme une plage de caracteres et `re` refuse le motif.
MOINS = u"−–—‐‑-"
SIGNE = u"+" + MOINS
MOINS_CANON = u"−"

RX_J = re.compile(u"J\\s*([" + SIGNE + u"])\\s*(\\d{1,3})", re.I)

# LA QUEUE DE CELLULE, et c'est la signature du plan : « ... — J-45 » en fin de
# « Ce qu'on fait ». Soixante-deux cellules l'emploient, et c'est la date DUE,
# quels que soient les J-N cites plus haut dans la phrase. Sans cette lecture,
# 11221 (« une affaire par passage, jusqu'a J-14 — J-45 ») rendait J-14, qui est
# la portee du role et non son terme. Elle prime sur tout le reste.
RX_QUEUE = re.compile(u"[—–-]\\s*J\\s*([" + SIGNE + u"])\\s*(\\d{1,3})\\s*[.·]?\\s*$",
                      re.I)

# « J-22 a J-18 » : une fourchette. C'est la FIN qui est l'echeance.
# LE SEPARATEUR NE PEUT PAS ETRE UN TIRET. Le cadratin est la ponctuation
# ordinaire de ces cahiers : « jusqu'a J-14 -- J-45 » se lisait alors comme une
# fourchette de trente et un jours, et 11221 s'affichait « J-45...J-14 » quand
# sa date due est J-45 tout court. Seuls les mots de liaison comptent.
RX_PLAGE = re.compile(u"J\\s*([" + SIGNE + u"])\\s*(\\d{1,3})\\s*"
                      u"(?:à|a|→|jusqu'à|jusqu'a)\\s*"
                      u"J\\s*([" + SIGNE + u"])\\s*(\\d{1,3})", re.I)

# « chaque huitieme jour a partir de J-35 », « chaque jour des J-36 » :
# recurrent, et non ponctuel -- le N est un DEBUT, pas un terme.
# LE CONNECTEUR EST OBLIGATOIRE. Sans lui, « relire chaque extrait ... J-50 »
# (11028) et « ce que chaque lieue coute ... J-45 » (11030) passaient pour des
# recurrences : « chaque » est trop courant en francais pour marquer une
# cadence a lui seul. C'est « a partir de » ou « des » qui la fait.
RX_RECUR = re.compile(u"((?:chaque|tous les|toutes les)[^.;·—]{0,50}?"
                      u"(?:à partir de|dès|des)\\s*"
                      u"J\\s*[" + SIGNE + u"]\\s*\\d{1,3})", re.I)

# Ce qui marque une echeance, par ordre de force : un « du » vaut mieux qu'un
# « engage », qui est la date ou l'on paie et non celle ou l'on rend.
RX_DU = re.compile(u"(?:d[uû]e?s?|avant|au plus tard|pour le|"
                   u"échéance|echeance)\\s*(?:à|a|le)?\\s*"
                   u"J\\s*([" + SIGNE + u"])\\s*(\\d{1,3})", re.I)
RX_ENGAGE = re.compile(u"engag[ée]e?s?\\s*(?:à|a)?\\s*"
                       u"J\\s*([" + SIGNE + u"])\\s*(\\d{1,3})", re.I)

# Les colonnes ou une date relative se cache, dans l'ordre ou on les croit.
# « Jour du » d'abord -- c'est son adresse ; « ce qu'elle coute » en dernier,
# parce qu'elle porte la date d'ENGAGEMENT, qui precede l'echeance d'un a trois
# jours et ne doit servir que faute de mieux.
COUT = u"ce qu'elle coûte"
ORDRE = [u"jour dû", u"jour du", u"note", u"ce qu'on fait",
         u"ce qu'on fait, et où", u"office", u"la preuve", u"l'action",
         u"où", u"avec quoi", u"état", u"etat", COUT]


def _signe(c):
    return -1 if c in MOINS else 1


def lire(cellule):
    u"""La forme relative d'une cellule : {n, fin, recurrent, libelle} ou None.

    `n` est signe : negatif avant l'entree (J-22 -> -22), positif apres
    (J+1 -> 1). `fin` n'est rempli que pour une fourchette. `recurrent` dit que
    `n` est un DEBUT et non un terme, et `libelle` garde alors la cadence
    exacte -- « chaque huitieme jour » n'est pas « chaque jour »."""
    t = cellule or u""
    if not t:
        return None
    m = RX_QUEUE.search(t)
    if m:
        return {"n": _signe(m.group(1)) * int(m.group(2)), "fin": None,
                "recurrent": False, "libelle": u""}
    m = RX_PLAGE.search(t)
    if m:
        a = _signe(m.group(1)) * int(m.group(2))
        b = _signe(m.group(3)) * int(m.group(4))
        return {"n": min(a, b), "fin": max(a, b), "recurrent": False, "libelle": u""}
    r = RX_RECUR.search(t)
    m = RX_DU.search(t) or RX_J.search(t)
    if not m:
        return None
    return {"n": _signe(m.group(1)) * int(m.group(2)), "fin": None,
            "recurrent": bool(r),
            "libelle": u" ".join(r.group(1).split()) if r else u""}


def candidat(cellules):
    u"""La date DUE d'une action, entre toutes ses colonnes.

    `cellules` : {en-tete minuscule sans emoji -> texte}. Rend (forme, colonne)
    ou (None, None)."""
    # 1. une marque d'echeance explicite, dans l'ordre des colonnes
    for k in ORDRE:
        v = cellules.get(k)
        if not v:
            continue
        if RX_QUEUE.search(v) or RX_PLAGE.search(v) or RX_DU.search(v) \
                or RX_RECUR.search(v):
            f = lire(v)
            if f:
                return f, k
    # 2. sinon un J-N nu, hors colonne de cout
    for k in ORDRE:
        if k == COUT:
            continue
        v = cellules.get(k)
        if v and RX_J.search(v):
            return lire(v), k
    # 3. en dernier recours la date d'ENGAGEMENT, qui n'est pas l'echeance
    v = cellules.get(COUT) or u""
    m = RX_ENGAGE.search(v) or RX_J.search(v)
    if m:
        return ({"n": _signe(m.group(1)) * int(m.group(2)), "fin": None,
                 "recurrent": False, "libelle": u""},
                COUT + u" (engagé)")
    return None, None


def texte(n):
    return u"J%s%d" % (MOINS_CANON if n < 0 else u"+", abs(n))


def canonique(f):
    u"""La forme d'ecriture unique de la colonne « Jour du » :

        J−22                          ponctuel
        J−22…J−18                     fourchette -- c'est la fin qui est due
        chaque huitième jour dès J−35  recurrent
    """
    if not f:
        return u""
    if f.get("fin") is not None and f["fin"] != f["n"]:
        return u"%s…%s" % (texte(f["n"]), texte(f["fin"]))
    if f.get("recurrent"):
        cadence = re.split(u"à partir de|dès|des\\b",
                           f.get("libelle") or u"chaque jour", 1, re.I)[0].strip()
        return u"%s dès %s" % (cadence or u"chaque jour", texte(f["n"]))
    return texte(f["n"])


# -- le jour d'entree ------------------------------------------------------
CLES = ("jour_dentree", "jour_d_entree", "jour_entree", "entree_port_real",
        "jour_j")
RX_DATE = re.compile(u"(\\d{1,2})e?\\s*(?:jour)?\\s*de\\s*la\\s*(\\d{1,2})e", re.I)


def rang(a, l, j):
    u"""Le meme calendrier que partout ailleurs : trente jours la lune, douze
    lunes l'an. Approximation assumee -- seul l'ecart nous interesse."""
    return ((a * 12) + l) * 30 + j


def _monde():
    return json.load(io.open(os.path.join(RACINE, "etat", "monde.json"),
                             encoding="utf-8"))


def cherche_dans_etat():
    u"""Le jour d'entree, s'il existe quelque part dans l'etat.

    On regarde, dans cet ordre : `monde.reperes`, puis un evenement de
    `evenements.json` dont l'id parle d'entree a Port-Real. Rend
    (date, d'ou elle vient), ou (None, la liste de ce qu'on a fouille)."""
    fouille = [u"etat/monde.json — reperes"]
    try:
        rep = (_monde().get("reperes") or {})
        for k in CLES:
            if isinstance(rep.get(k), dict) and rep[k].get("jour"):
                return rep[k], u"monde.reperes.%s" % k
    except Exception:
        pass
    fouille.append(u"etat/evenements.json — id d'entree a Port-Real")
    try:
        ev = json.load(io.open(os.path.join(RACINE, "etat", "evenements.json"),
                               encoding="utf-8"))
        for e in ev:
            i = str(e.get("id") or u"")
            if re.search(u"jour.?d.?entree|entree.?port.?r[eé]a?l", i, re.I) \
                    and (e.get("date_prevue") or {}).get("jour"):
                return e["date_prevue"], u"evenements.json/%s" % i
    except Exception:
        pass
    fouille.append(u"etat/books.json — affaire-jour-dentree : 11026 « Poser la "
                   u"DATE DE TRAVAIL » est toujours à faire, et le verrou 11001 "
                   u"« La date n'existe pas » n'est pas levé")
    return None, fouille


def lire_hypothese(texte_arg, date_monde=None):
    u"""« 30e de la 4e lune », « 4/30 », « 30 » (lune courante) -> une date."""
    d = date_monde or _monde().get("date") or {}
    t = (texte_arg or u"").strip()
    m = RX_DATE.search(t)
    if m:
        return {"annee": d.get("annee", 129), "lune": int(m.group(2)),
                "jour": int(m.group(1))}
    m = re.match(u"^(\\d{1,2})\\s*[/.\\-]\\s*(\\d{1,2})$", t)
    if m:
        return {"annee": d.get("annee", 129), "lune": int(m.group(1)),
                "jour": int(m.group(2))}
    m = re.match(u"^(\\d{1,2})$", t)
    if m:
        return {"annee": d.get("annee", 129), "lune": d.get("lune", 0),
                "jour": int(m.group(1))}
    return None


def nomme(r):
    u"""Un rang -> « 4e jour de la 5e lune »."""
    return u"%de jour de la %de lune" % (r % 30, (r // 30) % 12)


def resoudre(f, jour_j):
    u"""Le rang absolu d'une forme relative, une fois J connu. C'est la FIN
    d'une fourchette qui fait foi : la date ou l'on ne peut plus attendre."""
    if not f or not jour_j:
        return None
    n = f["fin"] if f.get("fin") is not None else f["n"]
    return rang(jour_j.get("annee", 0), jour_j.get("lune", 0),
                jour_j.get("jour", 0)) + n
