# -*- coding: utf-8 -*-
"""
partie_gestes.py — ce que le joueur FAIT à l'écran, traduit en coup de greffier.

L'écran ne connaît pas le vocabulaire du greffe : il n'a que des cartes et un
geste, « je pose celle-ci sur celle-là ». C'est ici qu'on décide de quel coup
il s'agit, ET C'EST LA CIBLE QUI LE DIT :

    une pièce 📦 sur un verrou 🔒 adverse     → `lever`    (une clef neuve)
    une pièce 📦 sur une de nos clefs 🗝️      → `rearmer`  (on renforce)
    une pièce 📦 sur une frappe 💥 adverse    → `bloquer`  (on protège)
    une pièce 📦 sur un état 🎯 adverse       → `bloquer`  (un verrou neuf)
    une pièce 📦 sur un état 🎯 à nous        → `lever`    (une clef qui le SERT)
    LEUR pièce 📦 sur une bourse 💰 à nous    → `retourner` (on l'achète)
    LEUR pièce 📦 sur une autre pièce à nous  → `detruire`  (on la frappe avec)
    une phrase écrite sous un état à nous     → `viser`    (un état neuf)
    une phrase écrite dans la case 📦 vide    → `demander` (une pièce, à l'arbitre)
    une question ❓ posée sur une carte d'en face → `justifier` (on exige la chaîne)
    une phrase écrite sous une carte à nous suspendue → `agir` (le maillon qui répond)
    une carte à nous ramenée au deck          → `retirer`  (et la pièce se remet)
    « le jour passe »                         → `tour`     (par l'arbitre)

Les deux gestes sur un état et le `viser` sont du 5.9 : sans eux, une partie
qui s'ouvre — deux racines, aucun verrou — n'offrait AUCUN geste à l'écran, et
le joueur restait devant sept pièces libres et un plateau muet. Un verrou se
pose SUR un état (règle 3.1), une clef peut SERVIR un état sans rien ouvrir,
et un état neuf se pose sous un autre : ce sont trois coups du livre, pas trois
inventions. Détruire et arbitrer restent au MJ, à la
ligne. `demander` est entré le même jour, à la demande du joueur : gratuit, hors
compte, la pièce attend l'arbitre — et `justifier` le lendemain, pour la même
raison : c'était le seul coup gratuit du livre qu'un joueur ne pouvait pas
jouer de sa main, et il fallait passer par le mestre pour dire « par où
entrent-ils ? ». Un geste qu'on ne sait pas traduire est
REFUSÉ EN CLAIR, jamais deviné.

Ce module N'ÉCRIT QUE DANS LE JSONL DE LA PARTIE, par `Partie.ecrire`, qui
vérifie d'abord. Rien dans `etat/` ne bouge : ce qu'un coup change dans le monde
reste au MJ (mj-partie.md, « le récap des écritures »).

Les refus sortent du greffe avec des ids nus ; on les rhabille de leurs titres
avant de les rendre, parce qu'ils s'affichent tels quels sous la carte.
"""
import re

import partie_cartes
import partie_validite
from partie_greffe import GEL_RETRAIT, JOURS_PAR_TOUR, liste


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
    b = p.blocages.get(sur)
    if b is not None and b["camp"] != camp:
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
    if m is not None and m["camp"] != camp:
        if m["realisee"] or m["tombee"]:
            return _refus(p, ["cette frappe n'est plus en route"])
        i = _id_libre(p, camp, "garde-%s" % sur)
        return _ecrire(p, {"camp": camp, "coup": "bloquer", "id": i, "sur": sur,
                           "engage": pieces,
                           "texte": texte or "on couvre %s" % partie_cartes.titre(p, m["cible"])},
                       "garde posée devant « %s »" % partie_cartes.titre(p, m["cible"]))

    e = p.etats.get(sur)
    if e is not None and e["camp"] != camp:
        # UN VERROU NEUF sur un état d'en face : « je tiens ceci contre cela ».
        # Le titre est au joueur ; à défaut, la pièce dit ce qu'elle tient.
        if e.get("sorti"):
            return _refus(p, ["cet état est sorti du deck : rien à y tenir"])
        i = _id_libre(p, camp, "%s-%s" % (pieces[0], sur))
        return _ecrire(p, {"camp": camp, "coup": "bloquer", "id": i, "sur": sur,
                           "engage": pieces, "texte": texte or _defaut(p, pieces, sur)},
                       "verrou posé sur « %s »" % partie_cartes.titre(p, sur))
    if e is not None:
        # UNE CLEF QUI SERT notre état sans rien ouvrir : elle le réalise quand
        # l'arbitre le constate. C'est le geste d'une partie où rien ne nous fait
        # face encore — on avance sans attendre qu'on nous barre.
        if e.get("vrai"):
            return _refus(p, ["cet état est déjà constaté vrai"])
        i = _id_libre(p, camp, "%s-%s" % (pieces[0], sur))
        return _ecrire(p, {"camp": camp, "coup": "lever", "id": i, "sert": sur,
                           "engage": pieces, "texte": texte or _defaut(p, pieces, sur)},
                       "clef posée pour « %s »" % partie_cartes.titre(p, sur))
    if sur in p.ressources:
        # LEUR PIÈCE SUR MA PIÈCE : on la tire à soi. Celle que j'engage dit le
        # coup — une bourse achète (`retourner`), tout le reste frappe
        # (`detruire`). Le geste est le même dans les deux sens : ce qu'on
        # glisse est la cible, ce sur quoi on lâche est ce qu'on y met.
        cible = pieces[0]
        rc, rs = p.ressources[cible], p.ressources[sur]
        if rc["camp"] == camp and rs["camp"] == camp:
            return _refus(p, ["on n'engage pas une pièce sur une autre des siennes"])
        if rc["camp"] == camp and rs["camp"] != camp:
            return _refus(p, ["c'est la pièce d'en face qu'on tire à soi : glissez la leur sur la vôtre"])
        if rs["camp"] != camp:
            return _refus(p, ["ce qu'on y met doit être à nous"])
        if rc.get("detruite"):
            return _refus(p, ["cette pièce n'est plus au grand livre"])
        bourse = partie_cartes.genre_piece(rs, sur) == "💰"
        coup = "retourner" if bourse else "detruire"
        i = _id_libre(p, camp, "%s-%s" % (sur, cible))
        return _ecrire(p, {"camp": camp, "coup": coup, "id": i, "cible": cible, "engage": [sur],
                           "texte": texte or ("%s pour %s" % (partie_cartes.titre(p, sur),
                                                              partie_cartes.titre(p, cible)))},
                       ("achat lancé : « %s », avec %s" if bourse else "frappe lancée sur « %s », avec %s")
                       % (partie_cartes.titre(p, cible), partie_cartes.titre(p, sur)))
    return _refus(p, ["cette carte ne se joue pas"])


# ------------------------------------------------------------------- viser
def viser(p, camp, sert, texte):
    """Un état neuf, écrit sous un des nôtres — ou une racine si `sert` est vide
    et qu'on n'en a pas encore. La phrase est au joueur, entière : c'est ce qui
    devra être vrai, et l'arbitre le constatera sur ces mots."""
    texte = (texte or "").strip()
    if not texte:
        return _refus(p, ["un état est une phrase : dites ce qui doit être vrai"])
    sert = str(sert or "") or None
    if sert:
        parent = p.etats.get(sert)
        if parent is None:
            return _refus(p, ["%s n'est pas un état" % sert])
        if parent["camp"] != camp:
            return _refus(p, ["on ne pose pas un état sous un état d'en face"])
    i = _id_libre(p, camp, texte[:24])
    ligne = {"camp": camp, "coup": "viser", "id": i, "texte": texte}
    if sert:
        ligne["sert"] = sert
    return _ecrire(p, ligne, "état posé : « %s »" % texte)


# ---------------------------------------------------------------- demander
def demander(p, camp, texte, lieu=None, tenu_par=None):
    """Une pièce demandée au grand livre. Gratuit, hors compte : elle n'existe
    qu'à l'arbitrage, qui la date et la corrige. Le joueur dit ce qu'il veut en
    une phrase ; le lieu et le tenant sont à lui s'il les sait, à l'arbitre
    sinon."""
    texte = (texte or "").strip()
    if not texte:
        return _refus(p, ["une demande est une phrase : dites ce qu'il vous faut, et où"])
    i = _id_libre(p, camp, texte[:24])
    ligne = {"camp": camp, "coup": "demander", "id": i, "texte": texte}
    if (lieu or "").strip():
        ligne["lieu"] = lieu.strip()
    if (tenu_par or "").strip():
        ligne["tenu_par"] = tenu_par.strip()
    return _ecrire(p, ligne, "demande portée au mestre : « %s »" % texte)


# --------------------------------------------------------------- justifier
def justifier(p, camp, sur, texte):
    """« Par où entrent-ils ? » — on exige la chaîne d'une pièce d'en face.

    Gratuit et hors compte : il ne prend pas le coup du tour. Ce qu'il coûte est
    d'une autre monnaie — UNE SEULE FOIS par pièce dans toute la partie, tous
    camps confondus. La cible passe en suspens et cesse de prévaloir jusqu'au
    maillon écrit dessous.

    On ne revérifie rien ici : le camp de la cible, la justification déjà
    dépensée, l'id qui ne désigne rien sont l'affaire de `partie_validite`, et
    ses refus reviennent au joueur rhabillés de leurs titres. Ce qui appartient
    à ce module, c'est la seule chose que le greffe ne peut pas savoir : une
    question sans phrase suspend une pièce sans que personne sache sur quoi.
    """
    texte = (texte or "").strip()
    if not texte:
        return _refus(p, ["une question est une phrase : dites ce que vous exigez"])
    return _ecrire(p, {"camp": camp, "coup": "justifier", "sur": str(sur or ""),
                       "texte": texte},
                   "question posée sur « %s »" % partie_cartes.titre(p, sur))


# ----------------------------------------------------------------- maillon
def maillon(p, camp, sur, texte, qui=None):
    """La réponse à un ❓ : qui a fait quoi, avec quoi — et la suspension tombe.

    C'est le pendant de `justifier`, et il lui manquait : on pouvait suspendre
    la pièce d'en face depuis l'écran sans que son camp puisse la relever. Une
    clef suspendue ne prévaut plus ; tant que personne n'écrit le maillon, elle
    reste morte sur la table.

    Gratuit quand il répond à une question — c'est le greffe qui le voit et qui
    pose `repond` sur la ligne. `avec` reprend ce que la cible engage déjà :
    répondre n'est pas engager une pièce de plus, c'est dire ce qu'on a fait de
    celles qui sont posées.
    """
    texte = (texte or "").strip()
    if not texte:
        return _refus(p, ["un maillon est une phrase : dites qui, avec quoi, quel jour"])
    sur = str(sur or "")
    cible = p.cles.get(sur) or p.blocages.get(sur) or p.menaces.get(sur)
    avec = liste((cible or {}).get("engage"))
    i = _id_libre(p, camp, "maillon-%s" % sur)
    return _ecrire(p, {"camp": camp, "coup": "agir", "id": i, "realise": sur,
                       "qui": qui or camp, "avec": avec, "etat": "faite",
                       "texte": texte},
                   "maillon écrit sous « %s »" % partie_cartes.titre(p, sur))


# --------------------------------------------------------------- reprendre
def reprendre(p, camp, sur):
    """Une carte à nous ramenée au deck : ce qui la tenait est libéré, et la
    pièce se remet — deux tours (mj-partie.md, la règle du retrait)."""
    sur = str(sur or "")
    # UN ÉTAT ramené dans la main SORT du deck ; UNE PIÈCE PERDUE ramenée dans la
    # main se RECONSTRUIT. Même geste que reprendre une clef — on tire à soi ce
    # qui est à soi —, et c'est la carte qui dit lequel des trois coups.
    e = p.etats.get(sur)
    if e is not None:
        if e["camp"] != camp:
            return _refus(p, ["cet état n'est pas le vôtre"])
        if not e.get("deck"):
            return _refus(p, ["cet état n'est pas au deck"])
        return _ecrire(p, {"camp": camp, "coup": "sortir", "id": sur},
                       "« %s » sorti du deck — ses pièces restent où elles sont" % partie_cartes.titre(p, sur))
    r = p.ressources.get(sur)
    if r is not None:
        if r["camp"] != camp:
            return _refus(p, ["cette pièce n'est pas la vôtre"])
        if not r.get("detruite"):
            return _refus(p, ["cette pièce n'est pas perdue : rien à reconstruire"])
        return _ecrire(p, {"camp": camp, "coup": "reconstruire", "id": sur},
                       "« %s » se reconstruit — revient dans %d jours, si la chose se reconstruit"
                       % (partie_cartes.titre(p, sur), 2 * JOURS_PAR_TOUR))
    reg = next((r for r in (p.cles, p.blocages, p.menaces) if sur in r), None)
    if reg is None:
        return _refus(p, ["on ne reprend qu'une clef, une garde, une frappe, un état ou une pièce perdue à soi"])
    if reg[sur]["camp"] != camp:
        return _refus(p, ["ce n'est pas le vôtre"])
    return _ecrire(p, {"camp": camp, "coup": "retirer", "id": sur},
                   "« %s » repris — les pièces se remettent %d jours"
                   % (partie_cartes.titre(p, sur), GEL_RETRAIT * JOURS_PAR_TOUR))


# ------------------------------------------------------------------- passer
def passer(p, camp):
    """Ne rien jouer : c'est un coup, et c'en est un bon quand il garde des
    pièces libres pour la suite."""
    return _ecrire(p, {"camp": camp, "coup": "passer", "texte": "passe"}, "vous passez ce jour")


# ---------------------------------------------------------------- constater
def constater(p, etat, verdict, motif):
    """L'arbitre constate un état vrai ou faux, avec son motif — le seul coup
    de l'arbitre qui ait un geste : un clic sur l'état, et deux verbes."""
    etat = str(etat or "")
    if etat not in p.etats:
        return _refus(p, ["%s n'est pas un état" % etat])
    if verdict not in ("vrai", "faux"):
        return _refus(p, ["un constat est vrai ou faux"])
    if not (motif or "").strip():
        return _refus(p, ["un constat porte toujours son motif"])
    return _ecrire(p, {"camp": "arbitre", "coup": "constater", "etat": etat, "verdict": verdict,
                       "motif": motif.strip()},
                   "constaté %s : « %s »" % (verdict, partie_cartes.titre(p, etat)))


# --------------------------------------------------------------------- jour
def jour(p):
    """Le jour passe. C'est l'arbitre qui le fait : les frappes atterrissent,
    les pièces arrivent, les gels tombent — et il faut que ça se voie."""
    return _ecrire(p, {"camp": "arbitre", "coup": "tour"}, "le jour a passé")


# ------------------------------------------------------------------- entrée
def jouer(p, geste):
    """L'entrée unique : `{quoi, camp, pieces|piece, sur, sert, texte}`."""
    geste = geste or {}
    quoi = geste.get("quoi")
    camp = geste.get("camp") or (p.camps() or ["noir"])[0]
    if camp == "arbitre":
        # l'arbitre ne joue pas — il constate et passe le jour, et c'est tout
        if quoi == "jour":
            return jour(p)
        if quoi == "constater":
            return constater(p, geste.get("sur"), geste.get("verdict"), geste.get("texte"))
        return _refus(p, ["l'arbitre ne joue pas : il constate, et il passe le jour"])
    if quoi == "passer":
        return passer(p, camp)
    if quoi == "poser":
        return poser(p, camp, geste.get("pieces") or geste.get("piece"),
                     geste.get("sur"), geste.get("texte"))
    if quoi == "viser":
        return viser(p, camp, geste.get("sert"), geste.get("texte"))
    if quoi == "demander":
        return demander(p, camp, geste.get("texte"), geste.get("lieu"), geste.get("tenu_par"))
    if quoi == "justifier":
        return justifier(p, camp, geste.get("sur"), geste.get("texte"))
    if quoi == "maillon":
        return maillon(p, camp, geste.get("sur"), geste.get("texte"), geste.get("qui"))
    if quoi == "reprendre":
        return reprendre(p, camp, geste.get("sur"))
    if quoi == "jour":
        return jour(p)
    return _refus(p, ["geste inconnu"])
