# -*- coding: utf-8 -*-
"""
partie_gestes.py — ce que le joueur FAIT à l'écran, traduit en coup de greffier.

L'écran ne connaît pas le vocabulaire du greffe : il n'a que des cartes et un
geste, « je pose celle-ci sur celle-là ». C'est ici qu'on décide de quel coup
il s'agit, ET C'EST LA CIBLE QUI LE DIT :

    une pièce 📦 sur un verrou 🔒 adverse     → `lever`    (une clef neuve)
    une pièce 📦 sur une de nos clefs 🗝️      → `rearmer`  (on renforce)
    une pièce 📦 sur une frappe 💥 adverse    → `bloquer`  (on protège)
    une carte à nous ramenée au deck          → `retirer`  (et la pièce se remet)
    « le jour passe »                         → `tour`     (par l'arbitre)

Rien d'autre n'est jouable en v1 : viser, demander, détruire, justifier et
arbitrer restent au MJ, qui les écrit à la ligne. Un geste qu'on ne sait pas
traduire est REFUSÉ EN CLAIR, jamais deviné — poser un dragon sur un état cible ne
veut rien dire, et lui inventer un sens ferait un coup que le joueur n'a pas
voulu.

Ce module N'ÉCRIT QUE DANS LE JSONL DE LA PARTIE, par `Partie.ecrire`, qui
vérifie d'abord. Rien dans `etat/` ne bouge : ce qu'un coup change dans le monde
reste au MJ (mj-partie.md, « le récap des écritures »).

Les refus sortent du greffe avec des ids nus ; on les rhabille de leurs titres
avant de les rendre, parce qu'ils s'affichent tels quels sous la carte.
"""
import re

import partie_cartes
import partie_validite
from partie_greffe import GEL_RETRAIT, JOURS_PAR_TOUR, adverse, liste


def _id_libre(p, camp, base):
    """Un id neuf, lisible, jamais pris : « n-caraxes-v-portes »."""
    b = re.sub(r"[^a-z0-9]+", "-", str(base).lower()).strip("-")[:32] or "coup"
    i = "%s-%s" % (camp[0], b)
    n = 1
    while partie_validite.id_pris(p, i) or i in p.ressources:
        n += 1
        i = "%s-%s-%d" % (camp[0], b, n)
    return i


def _lisible(p, message):
    """Le même refus, ses ids remplacés par ce qu'ils sont en clair."""
    mots = sorted(set(re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{1,40}", str(message))),
                  key=len, reverse=True)
    out = str(message)
    for m in mots:
        if not partie_validite.id_pris(p, m) and m not in p.ressources:
            continue
        t = partie_cartes.titre(p, m)
        if t and t != m:
            out = out.replace(m, "« %s »" % t)
    return out


def _defaut(p, pieces, cible):
    """Le titre d'une clef sans nom. Il NE RÉPÈTE PAS le verrou : la carte est
    posée dessous, on vient de le lire."""
    return ", ".join(partie_cartes.titre(p, x) for x in pieces)


def _refus(p, motifs):
    return {"ok": False, "refus": [_lisible(p, m) for m in motifs], "ligne": None}


def _ecrire(p, ligne, dit):
    avant = len(p.avertissements)
    refus = p.ecrire(ligne)
    if refus:
        return _refus(p, refus)
    return {"ok": True, "refus": [], "ligne": p.lignes[-1], "dit": dit,
            "avertissements": [_lisible(p, a) for a in p.avertissements[avant:]]}


# ------------------------------------------------------------------- poser
def poser(p, camp, pieces, sur, texte=""):
    """Une ou plusieurs pièces posées sur une carte. La cible dit le coup."""
    pieces = [x for x in liste(pieces) if x]
    if not pieces:
        return _refus(p, ["il faut une pièce : c'est elle qui paie le coup"])
    for pc in pieces:
        if pc not in p.ressources:
            return _refus(p, ["%s n'est pas au grand livre : le mestre doit l'y porter d'abord" % pc])
    sur = str(sur or "")
    texte = (texte or "").strip()
    ennemi = adverse(camp)

    b = p.blocages.get(sur)
    if b is not None and b["camp"] == ennemi:
        if b["tombe"]:
            return _refus(p, ["ce verrou est déjà tombé"])
        # Une clef existe-t-elle déjà contre lui ? On renforce, plutôt que d'en
        # ouvrir un second qui dirait la même chose avec un autre nom.
        for kid, k in p.cles.items():
            if sur in k["ouvre"] and k["camp"] == camp and not k["retiree"] and not k.get("tenue"):
                return _ecrire(p, {"camp": camp, "coup": "rearmer", "id": kid, "engage": pieces},
                               "renfort porté à « %s »" % partie_cartes.titre(p, kid))
        i = _id_libre(p, camp, "%s-%s" % (pieces[0], sur))
        return _ecrire(p, {"camp": camp, "coup": "lever", "id": i, "ouvre": [sur],
                           "engage": pieces, "texte": texte or _defaut(p, pieces, sur)},
                       "clef posée contre « %s »" % partie_cartes.titre(p, sur))

    if b is not None and b["camp"] == camp:
        return _ecrire(p, {"camp": camp, "coup": "rearmer", "id": sur, "engage": pieces},
                       "renfort porté à « %s »" % partie_cartes.titre(p, sur))

    k = p.cles.get(sur)
    if k is not None:
        if k["camp"] != camp:
            return _refus(p, ["cette clef n'est pas la vôtre"])
        return _ecrire(p, {"camp": camp, "coup": "rearmer", "id": sur, "engage": pieces},
                       "renfort porté à « %s »" % partie_cartes.titre(p, sur))

    m = p.menaces.get(sur)
    if m is not None and m["camp"] == ennemi:
        if m["realisee"] or m["tombee"]:
            return _refus(p, ["cette frappe n'est plus en route"])
        i = _id_libre(p, camp, "garde-%s" % sur)
        return _ecrire(p, {"camp": camp, "coup": "bloquer", "id": i, "sur": sur,
                           "engage": pieces,
                           "texte": texte or "on couvre %s" % partie_cartes.titre(p, m["cible"])},
                       "garde posée devant « %s »" % partie_cartes.titre(p, m["cible"]))

    if sur in p.etats:
        return _refus(p, ["un état cible ne se tient pas avec une pièce : posez-la sur "
                          "le verrou qui s'y oppose"])
    if sur in p.ressources:
        return _refus(p, ["on n'engage pas une pièce sur une autre pièce"])
    return _refus(p, ["cette carte ne se joue pas"])


# --------------------------------------------------------------- reprendre
def reprendre(p, camp, sur):
    """Une carte à nous ramenée au deck : ce qui la tenait est libéré, et la
    pièce se remet — deux tours (mj-partie.md, la règle du retrait)."""
    sur = str(sur or "")
    reg = next((r for r in (p.cles, p.blocages, p.menaces) if sur in r), None)
    if reg is None:
        return _refus(p, ["on ne reprend qu'une clef, une garde ou une frappe à soi"])
    if reg[sur]["camp"] != camp:
        return _refus(p, ["ce n'est pas le vôtre"])
    return _ecrire(p, {"camp": camp, "coup": "retirer", "id": sur},
                   "« %s » repris — les pièces se remettent %d jours"
                   % (partie_cartes.titre(p, sur), GEL_RETRAIT * JOURS_PAR_TOUR))


# --------------------------------------------------------------------- jour
def jour(p):
    """Le jour passe. C'est l'arbitre qui le fait : les frappes atterrissent,
    les pièces arrivent, les gels tombent — et il faut que ça se voie."""
    return _ecrire(p, {"camp": "arbitre", "coup": "tour"}, "le jour a passé")


# ------------------------------------------------------------------- entrée
def jouer(p, geste):
    """L'entrée unique : `{quoi, camp, pieces|piece, sur, texte}`."""
    geste = geste or {}
    quoi = geste.get("quoi")
    camp = geste.get("camp") or "noir"
    if camp not in ("noir", "vert"):
        return _refus(p, ["camp inconnu"])
    if quoi == "poser":
        return poser(p, camp, geste.get("pieces") or geste.get("piece"),
                     geste.get("sur"), geste.get("texte"))
    if quoi == "reprendre":
        return reprendre(p, camp, geste.get("sur"))
    if quoi == "jour":
        return jour(p)
    return _refus(p, ["geste inconnu"])
