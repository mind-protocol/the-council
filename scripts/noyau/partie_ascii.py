#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
partie_ascii.py — le plateau au terminal.

Le pendant texte de l'onglet « Le conseil » : la MÊME vue que sert
partie_cartes.vue(), rendue en lignes au lieu de l'être en div. Ce module ne
connaît aucune règle et n'ouvre aucun fichier — il dessine ce qu'on lui donne,
et c'est ce qui garantit que le terminal et l'écran ne divergeront pas.

    python scripts/partie.py <partie> --plateau [--camp <camp>]

**UN SEUL ARBRE, du trône jusqu'aux pièces.** La v1 rendait quatre sections —
les états, les fronts, nos pièces, les leurs — et l'on n'y voyait plus quel
verrou barrait quel état : le lien était ÉCRIT (« sur « … » », « → v-portes »)
au lieu d'être DESSINÉ, ce qui est exactement ce qu'un plateau doit faire.
Tout ce qui se rattache à quelque chose pend donc sous lui, par un trait :

    👑 le trône
    └─🎯 la reine est assise            ⚫
      └─🎯 une porte est acquise        ⚫
        └─🔒 les sept portes fermées    🟢 PRÉVAUT
          └─🗝️ Meleys au-dessus         ❓ suspendu
            └─🐉 meleys

Ne restent hors de l'arbre que les pièces libres — celles qui ne sont
accrochées à rien, ce qui est leur définition même.

Pas de bordure droite, pas de colonne alignée à droite : un emoji vaut deux
colonnes dans un terminal et une dans le compte de Python, si bien que tout
cadre fermé se décale d'autant d'emojis qu'il contient. Le dessin est ancré à
gauche, où le décalage ne se voit pas.
"""
from partie_greffe import EMOJI_CAMP

LARGEUR = 100
FOURCHE, DERNIER, TUYAU, VIDE = "├─", "└─", "│ ", "  "
GRAS, FIN = "[1m", "[0m"


def _g(t, gras=True):
    """Le gras du terminal. Il ne s'écrit QUE sur ce qu'on recopie — les ids —
    et sur les titres de bloc : un plateau où tout est gras n'a plus de relief.
    Éteint hors d'un terminal (`--plateau > fichier`), où ce ne seraient que
    des caractères parasites au milieu du texte."""
    return "%s%s%s" % (GRAS, t, FIN) if gras and t else t


def _court(t, n):
    t = " ".join((t or "").split())
    return t if len(t) <= n else t[:n - 1] + "…"


def _plier(t, n):
    """Le texte coupé aux mots, en autant de morceaux qu'il faut. Sert au mode
    entier : un plateau qui élide un titre oblige à rouvrir le jsonl pour
    savoir ce qu'il disait, ce qui est exactement ce qu'un plateau doit éviter."""
    mots, lignes, ligne = " ".join((t or "").split()).split(), [], ""
    for m in mots:
        if ligne and len(ligne) + 1 + len(m) > n:
            lignes.append(ligne)
            ligne = m
        else:
            ligne = (ligne + " " + m).strip()
    return lignes + ([ligne] if ligne else [])


def _camp(c):
    return "%s %s" % (EMOJI_CAMP[c], c) if c else "personne"


def _regle(titre="", largeur=LARGEUR, gras=True):
    if not titre:
        return "─" * largeur
    return "── %s " % _g(titre, gras) + "─" * max(0, largeur - len(titre) - 4)


# ------------------------------------------------------------------ statuts
# Un signe par état, TOUJOURS le même. Le greffe dit « faite », « posée »,
# « dans 4 j » chacun à sa façon, au milieu du porteur de la pièce ; en colonne
# et signés, ils se lisent sans être lus. C'est aussi ce qui lève l'ambiguïté
# de ⚔️, qui vaut à la fois pour une action et pour une troupe : une action est
# ✅ ou ⏳, une troupe est 📍 ou 🖐.
SIGNES = ((u"faite", u"✅ faite"), (u"a_faire", u"⏳ à faire"), (u"à faire", u"⏳ à faire"),
          (u"attend l'arbitre", u"⚖️ attend l'arbitre"), (u"détruite", u"💀 détruite"),
          (u"se remet", u"❄️ se remet"), (u"dans ", u"🕐 dans "), (u"posée", u"📍 posée"),
          (u"libre", u"🖐 libre"))


def _statut(texte):
    """Le pied droit d'une carte, signé. Ce qui porte déjà son signe (les
    rubans d'une clé : ✅ tient, ❓ suspendu) passe sans être retouché."""
    t = (texte or "").strip()
    if not t or t[0] in u"✅❓⏳⚠️📍🕐❄️💀⚖️🖐":
        return t
    for cle, signe in SIGNES:
        if t.startswith(cle):
            return signe + t[len(cle):]
    return t


def _pluriel(n, mot, feminin=False):
    return u"%d %s%s" % (n, mot, (u"e" if feminin and False else u"") + (u"s" if n > 1 else u""))


def _decomptes(vue, gras=True):
    """La position en chiffres, sur une ligne. Un plateau dit où sont les
    choses ; il ne disait pas COMBIEN il y en a, et c'est ce qu'on regarde en
    premier quand on reprend une partie après deux jours."""
    camp = vue.get("camp")
    fronts = vue.get("fronts") or []
    contre_nous = len([f for f in fronts if f.get("contre_nous")])
    cles = [c for f in fronts for c in (f.get("pile") or []) if c.get("type") == "clef"]
    suspendues = len([c for c in cles if u"suspendu" in (c.get("pied", {}).get("droite") or "")])
    deck = vue.get("deck") or {}
    engagees = len([c for lot in deck.values() for c in lot if c.get("engagee_par")])
    a_nous = [c for lot in deck.values() for c in lot]
    questions = len([1 for c in _toutes(vue) if c.get("type") == "question"])
    actions = [c for c in _toutes(vue) if c.get("type") == "action"]
    a_faire = len([c for c in actions if (c.get("pied", {}).get("droite") or "") != u"faite"])
    morceaux = [
        u"🔒 %d contre nous · %d contre eux" % (contre_nous, len(fronts) - contre_nous),
        u"🗝️ %s%s" % (_pluriel(len(cles), u"posée"),
                      (u" · %s" % _pluriel(suspendues, u"suspendue")) if suspendues else u""),
        u"⚔️ %s%s" % (_pluriel(len(actions), u"action"),
                      (u" · %d à faire" % a_faire) if a_faire else u""),
        u"❓ %s" % _pluriel(questions, u"question"),
        u"📦 %d à nous · %s" % (len(a_nous), _pluriel(engagees, u"engagée")),
    ]
    # pliée à la largeur : une ligne de comptes qui dépasse est une ligne qu'on
    # ne lit pas, et le terminal la couperait n'importe où
    out, ligne = [], u" position "
    for m in morceaux:
        if len(ligne) + len(m) + 3 > LARGEUR:
            out.append(ligne)
            ligne = u"           "
        ligne += u"  " + m
    return out + [ligne]


def _toutes(vue):
    """Toutes les cartes de la position, à quelque profondeur qu'elles soient."""
    def sous(c):
        yield c
        for x in c.get("sous") or []:
            for y in sous(x):
                yield y
    for c in (vue.get("cibles") or []):
        for y in sous(c):
            yield y
    for f in (vue.get("fronts") or []):
        for y in sous(f["tete"]):
            yield y
        for c in f.get("pile") or []:
            for y in sous(c):
                yield y


# ------------------------------------------------------------------ l'arbre
class _Noeud(object):
    """Ce qui se dessine : un signe, un nom, un texte, une mention à droite,
    et ce qui pend dessous. L'arbre est bâti une fois, rendu une fois."""

    def __init__(self, emoji, nom, texte, mention="", neuf=False, camp=None,
                 gras=True, entier=False):
        self.emoji, self.nom, self.texte = emoji, nom, texte
        self.mention, self.neuf, self.camp, self.gras = mention, neuf, camp, gras
        self.entier = entier
        self.fils = []

    def ajouter(self, n):
        self.fils.append(n)
        return n

    def lignes(self, prefixe="", branche="", largeur=LARGEUR):
        marque = "•" if self.neuf else " "
        # LA COULEUR DU CAMP D'ABORD, SUR CHAQUE CARTE. Elle n'était portée que
        # par les états ; un verrou, une clé, une pièce ne disaient pas à qui
        # ils étaient, et il fallait remonter la branche pour le deviner.
        drapeau = EMOJI_CAMP[self.camp] if self.camp else " "
        tete = "%s%s%s%s%s %s" % (marque, prefixe, branche, drapeau, self.emoji,
                                  _g(self.nom, self.gras))
        nu = len(tete) - (len(GRAS) + len(FIN) if (self.gras and self.nom) else 0)
        dessous = prefixe + ("" if not branche else (VIDE if branche == DERNIER else TUYAU))
        if self.entier:
            # rien n'est perdu. Une carte qui TIENT garde sa ligne — replier ce
            # qui n'avait pas besoin de l'être doublerait la hauteur du plateau
            # pour rien ; seul ce qui déborde passe dessous, aligné.
            queue = ("   " + self.mention) if self.mention else ""
            if nu + 2 + len(self.texte) + len(queue) <= largeur:
                out = ["%s  %s%s" % (tete, self.texte, queue)]
            else:
                out = ["%s%s" % (tete, queue)]
                marge = " " + dessous + ("│ " if self.fils else "  ") + "   "
                out += [marge + x for x in _plier(self.texte, max(20, largeur - len(marge)))]
        else:
            mention = _court(self.mention, max(0, largeur - nu - 25))
            corps = _court(self.texte, max(20, largeur - nu - len(mention) - 5))
            out = ["%s  %s%s" % (tete, corps, ("   " + mention) if mention else "")]
        for i, f in enumerate(self.fils):
            out += f.lignes(dessous, DERNIER if i == len(self.fils) - 1 else FOURCHE, largeur)
        return out


def _engagees(vue):
    """Les pièces rangées par CE QUI LES ENGAGE. Une pièce engagée n'est pas une
    mention au pied d'un verrou : c'est un corps posé là, et elle doit pendre
    dessous comme le reste. Sans cet index, les pièces d'en face restaient
    noyées dans le texte de leur verrou (donc tronquées avec lui), et une pièce
    engagée mais encore EN ROUTE ne se voyait qu'en réserve — c'est-à-dire à
    l'endroit exact où elle n'est pas."""
    par = {}
    for c in [x for lot in (vue.get("deck") or {}).values() for x in lot] + (vue.get("eux") or []):
        for qui in c.get("engagee_par") or []:
            par.setdefault(str(qui), []).append(c)
    return par


def _carte_en_noeud(c, mention=None, engagees=None, gras=True, entier=False):
    """Une carte de la vue, avec ce qu'elle empile (`sous`) et ce qu'elle engage.

    `mention` à None : on la déduit des pieds de la carte. `mention` à "" : la
    carte n'en porte AUCUNE — c'est le cas des états, dont le pied dit « sert
    X », déjà écrit par la place dans l'arbre et qui mangeait toute la largeur.
    """
    pieds = [x for x in (c.get("pied", {}).get("gauche"),
                         _statut(c.get("pied", {}).get("droite"))) if x]
    # L'ID NE SE TRONQUE JAMAIS : tous les coups se jouent par id, et un plateau
    # dont on ne peut pas recopier « n-caisse-v-oreill… » dans une commande n'est
    # pas un plateau. C'est le titre qui cède la place, jamais le nom.
    n = _Noeud(c.get("emoji", "·"), c.get("id") or "",
               c.get("titre") or "",
               " · ".join(pieds) if mention is None else mention, c.get("neuf"),
               camp=c.get("camp"), gras=gras, entier=entier)
    if c.get("corps"):
        n.texte = "%s — %s" % (n.texte, c["corps"]) if n.texte else c["corps"]
    deja = set()
    for s in c.get("sous") or []:
        deja.add(str(s.get("id")))
        n.ajouter(_carte_en_noeud(s, engagees=engagees, gras=gras, entier=entier))
    for piece in (engagees or {}).get(str(c.get("id")), []):
        if str(piece.get("id")) not in deja:
            n.ajouter(_carte_en_noeud(piece, engagees=engagees, gras=gras, entier=entier))
    return n


def _front_en_noeud(f, engagees=None, gras=True, entier=False):
    """Un front : le verrou, sa mention de préséance, ce qu'il engage, et la
    pile de ce qu'on lui a opposé — chacun avec ses propres pièces dessous."""
    n = _carte_en_noeud(f["tete"], "%s PRÉVAUT — %s" % (EMOJI_CAMP[f.get("prevaut")],
                                                        f.get("pourquoi") or ""), engagees, gras, entier)
    for c in f.get("pile") or []:
        n.ajouter(_carte_en_noeud(c, engagees=engagees, gras=gras, entier=entier))
    return n


def _arbre(vue, gras=True, entier=False):
    """Le trône, les racines de chaque camp, et sous chaque état ce qui le
    barre puis ce qu'il sert. C'est le plateau entier en un seul objet."""
    racine = _Noeud("👑", "le trône", "", "à " + _camp(vue.get("trone")), gras=gras, entier=entier)
    engagees = _engagees(vue)

    fronts = {}
    for f in vue.get("fronts") or []:
        fronts.setdefault(str(f.get("sur")), []).append(f)
    enfants = {}
    for c in vue.get("cibles") or []:
        enfants.setdefault(str(c.get("sert") or ""), []).append(c)

    def poser(c, parent, vus):
        if c["id"] in vus:            # un `sert` circulaire ne doit pas boucler
            return
        vus = vus | {c["id"]}
        # plus de camp en mention à droite : il est maintenant devant le signe
        n = parent.ajouter(_carte_en_noeud(c, "", engagees, gras, entier))
        for f in fronts.get(str(c["id"]), []):
            n.ajouter(_front_en_noeud(f, engagees, gras, entier))
        for fils in enfants.get(str(c["id"]), []):
            poser(fils, n, vus)

    poses = set()
    for c in enfants.get("", []):     # les racines : un état qui ne sert rien
        poser(c, racine, poses)
        poses.add(c["id"])
    # ce qui pend d'un état absent de la vue (sorti du deck) ne doit pas disparaître
    connus = set(str(c["id"]) for c in vue.get("cibles") or [])
    for cle, lot in enfants.items():
        if cle and cle not in connus:
            for c in lot:
                poser(c, racine, set())
    # un front sur autre chose qu'un état (une clé, une frappe) n'a pas de branche
    orphelins = [f for f in (vue.get("fronts") or []) if str(f.get("sur")) not in connus]
    for f in orphelins:
        racine.ajouter(_front_en_noeud(f, engagees, gras, entier))
    return racine


# ------------------------------------------------------------------ pièces
def _libres(vue, gras=True, entier=False):
    """Ce qui n'est accroché nulle part : la main de chaque camp, et rien d'autre.
    Une pièce posée est déjà DANS l'arbre, sous la clé qui l'engage."""
    def nues(lot):
        # engagée = déjà dans l'arbre, sous ce qui l'engage ; la réserve ne
        # montre que ce qui n'est retenu par rien
        return [c for c in lot if not c.get("engagee_par")]

    out = []
    for titre, lot in (("EN MAIN", nues((vue.get("deck") or {}).get("main") or [])),
                       ("EN ROUTE", nues((vue.get("deck") or {}).get("route") or [])),
                       ("SE REMET", nues((vue.get("deck") or {}).get("remet") or [])),
                       # d'en face on montre le libre ET ce qui arrive : un renfort
                       # à quatre jours n'est engagé par rien, donc il ne pend nulle
                       # part dans l'arbre — sans cette ligne il disparaissait du
                       # plateau, alors que c'est ce qu'on doit voir venir.
                       ("CHEZ EUX, LIBRES", nues([c for c in (vue.get("eux") or [])
                                                  if c.get("apparence") == "libre"])),
                       ("CHEZ EUX, EN ROUTE", nues([c for c in (vue.get("eux") or [])
                                                    if c.get("apparence") == "route"])),
                       ("CHEZ EUX, SE REMET", nues([c for c in (vue.get("eux") or [])
                                                    if c.get("apparence") == "remet"])),
                       ("PERDUES", ((vue.get("deck") or {}).get("detruites") or [])
                        + [c for c in (vue.get("eux") or []) if c.get("apparence") == "detruite"])):
        if not lot:
            continue
        out.append("")
        out.append("  %s (%d)" % (titre, len(lot)))
        for c in lot:
            large = 34 if not entier else max(
                [34] + [len(x.get("titre") or "") for x in lot])
            out.append("    %s%s %-*s %s" % (EMOJI_CAMP[c.get("camp")], c.get("emoji", "📦"),
                                              large, _court(c.get("titre"), large),
                                              _court(" · ".join(
                                                  x for x in (c.get("pied", {}).get("gauche"),
                                                              _statut(c.get("pied", {}).get("droite")))
                                                  if x), 44)))
    return out


# ------------------------------------------------------------ ce qui est acquis
def _tenues(vue, gras=True, entier=False):
    """Les clés dont tous les blocages sont tombés. Elles ne sont plus dans
    l'arbre — leur front a disparu avec le verrou — et sans ce bloc, sur un duel
    gagné, on ne voyait plus par quoi il avait été gagné."""
    lot = vue.get("tenues") or []
    if not lot:
        return []
    out = ["", _regle("✅ TENUES — leur blocage est tombé, leurs pièces sont rendues", gras=gras)]
    large = max([20] + [len(k.get("id") or "") for k in lot])
    for k in lot:
        i = k.get("id") or ""
        # le padding se compte sur l'id NU : le gras l'entoure de codes qui ne
        # prennent pas de place à l'écran mais en prendraient dans un %-20s
        nom = _g(i, gras) + " " * (large - len(i))
        out.append(("  %s %s  %s" % (EMOJI_CAMP[k.get("camp")], nom,
                                     k.get("titre") if entier
                                     else _court(k.get("titre"), LARGEUR - large - 8))).rstrip())
    return out


TITRES_SIGNALE = {
    "constatables": "mûrs à constater — rien ne les bloque plus (l'arbitre tranche, pas le greffe)",
    "branches_mortes": "demandées, accordées, engagées par rien depuis deux tours",
    "inactifs": "n'ont rien joué que passer depuis trois tours",
    "menaces": "atterrissent",
    "parees": "parées : elles attendent un tour",
    "parades_tenues": "parades tenues : la frappe tombe",
    "arrivees": "arrivées", "degeles": "dégelées", "etats_arrives": "entrés au deck",
}


def _signale(vue, gras=True, entier=False):
    """Ce que le greffe a porté au dernier passage de tour. Ce ne sont ni des
    coups ni des verdicts — c'est ce qu'il a VU, et qu'on oublie de regarder."""
    sig = vue.get("signale") or {}
    if not sig:
        return []
    out = ["", _regle("⏭️ AU DERNIER PASSAGE DU TOUR", gras=gras)]
    for cle in ("constatables", "menaces", "parees", "parades_tenues",
                "arrivees", "degeles", "etats_arrives", "inactifs", "branches_mortes"):
        lot = sig.get(cle)
        if not lot:
            continue
        out.append("  %s %s" % (_g(cle, gras) + " " * max(0, 16 - len(cle)), TITRES_SIGNALE.get(cle, "")))
        joint = " · ".join(str(x) for x in lot)
        if entier:
            out += ["      " + x for x in _plier(joint, LARGEUR - 8)]
        else:
            out.append("      " + _court(joint, LARGEUR - 8))
    return out


# ------------------------------------------------------------------ entrée
def plateau(vue, gras=True, entier=False):
    """Rend la vue de partie_cartes.vue() en lignes de texte.

    `entier` : rien n'est élidé — les titres se replient sous leur carte au
    lieu d'être coupés d'un « … ». Plus haut, mais on n'a jamais à rouvrir le
    jsonl pour savoir ce qu'une carte disait.
    """
    out = [_regle(),
           " %s · tour %d · jour du monde +%d" % (vue["partie"], vue["tour"], vue["jours"]),
           " trait à %s · vu par %s" % (_camp(vue.get("trait")), _camp(vue.get("camp"))),
           " deck      " + " · ".join("%s %d/%d" % (EMOJI_CAMP[c], d["pris"], d["max"])
                                      for c, d in sorted((vue.get("decks") or {}).items())),
           ] + _decomptes(vue, gras) + [
           _regle(), ""]
    out += _arbre(vue, gras, entier).lignes()
    libres = _libres(vue, gras, entier)
    if libres:
        out += ["", _regle("📦 LIBRES — accrochées à rien", gras=gras)] + libres
    out += _tenues(vue, gras, entier) + _signale(vue, gras, entier)
    if vue.get("consignes"):
        out += ["", _regle("📋 CONSIGNES", gras=gras)]
        for pid, t in vue["consignes"].items():
            out.append("  %-20s %s" % (_court(pid, 20), _court(t, 70)))
    return out
