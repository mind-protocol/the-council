# -*- coding: utf-8 -*-
"""DECISIONS — l'arbre des fourches ouvertes, et ce qu'une voie coute.
"""
import re
import sys

from plan.expose import nu, sans_emoji, NOM_GENRE
from plan.criticite.page import LARGEUR, cale, titre, faite
from plan.criticite.graphe import (CONJONCTIF, DISJONCTIF, amonts,
                                   atteignables)
from plan.criticite.hommes import GLOSE

#
# CE QU'ON CHERCHE ICI, ET POURQUOI CE N'EST PAS LA CRITICITE. Dans un plan
# conjonctif entierement connexe, 95 % des pas portent la meme perte — et c'est
# JUSTE : ils sont tous obligatoires. Le relief n'est donc pas sur les pas, il
# est sur les FOURCHES. Une decision qui en commande sept ne vaut pas une
# decision qui n'en commande aucune, et ca, aucune mesure de pas ne le dira.
#
# UNE DECISION EST DEVINEE, PAS DECLAREE — et c'est la seule hypothese de tout
# ce module. On appelle decision un verrou dont PLUSIEURS clefs sont retenues :
# plusieurs mecanismes gardes pour une meme serrure, donc un choix que personne
# n'a fait. Ca peut se tromper : trois clefs retenues peuvent etre trois
# mecanismes COMPLEMENTAIRES qu'on veut tous les trois. Le remede tient en une
# colonne sur le verrou — « ⚖️ Il en faut : une | toutes », 47 cellules — et
# tant qu'elle n'existe pas, ce rendu est une PROPOSITION de lecture. Il le dit.
#
# L'ARBRE NE S'AFFICHE JAMAIS EN ENTIER : 38 decisions ouvertes font 6,26 x 10^12
# combinaisons. On ne montre donc qu'un saut — une decision, ses branches, et les
# decisions que chacune commande —, exactement comme la colonne `attendu`.
#
# CE QU'UNE BRANCHE COUTE, ET CE QU'ELLE LIBERE. Choisir n'est pas seulement
# engager : c'est ECARTER. Retenir une clef sur trois retire du plan les actions
# des deux autres, et c'est le vrai gain d'une decision — le plan retrecit. Les
# deux nombres se posent donc cote a cote : ce que la voie engage, ce que le
# choix libere.
# ─────────────────────────────────────── ce qu'une voie coûte, en clair
#
# ON NE CRÉE PAS UN FORMAT, ON LIT CELUI QUI EXISTE. Les hommes écrivent déjà
# leurs prix dans une forme presque uniforme, sans que personne le leur ait
# demandé : « 6 bras-jours + 1 coque marchande 2 jours · une fois · engagé J−22 ».
# Mesure sur les 909 prix écrits du plan : 49 % portent une date d'engagement,
# 56 % une cadence, 9 % des dragons, 7 % des bras-jours. La convention est bonne,
# l'adoption est à 7 % — il n'y a donc rien à concevoir, seulement à lire et à
# demander le reste.
#
# CE QU'ON NE DEVINE PAS. « Un homme entier, 30 jours » vaut probablement trente
# bras-jours, et « une matinée » un demi. On ne le convertit PAS : une somme
# obtenue en devinant la moitié de ses termes est plus dangereuse qu'une absence
# de somme, parce qu'elle a l'air d'un compte. Ce qui n'est pas écrit en clair
# est compté comme ILLISIBLE, et le nombre d'illisibles s'affiche à côté du
# total. Un total de douze sur trois prix dont deux sont illisibles n'est pas
# douze : c'est « au moins douze, et l'on ne sait pas ».
#
# POURQUOI ÇA VAUT LE DÉTOUR — la fourche du débarquement, 20101 :
#   au compte des pièces   5 contre 1        (la première a l'air cinq fois plus lourde)
#   au prix                12 bj contre 12   (elles coûtent exactement la même chose)
# Un conseil qui choisit sur le compte des lignes choisit à l'envers.
BRAS = re.compile(u"(\\d+(?:[.,]\\d+)?)\\s*(?:bras[-\\s]jours?|journ[ée]es?\\s+d.homme|j-h\\b)", re.I)
DRAGONS = re.compile(u"(\\d+(?:[.,]\\d+)?)\\s*dragons?\\b", re.I)
ENGAGE = re.compile(u"engag[ée]e?\\s*([JD][−\\-]\\s*\\d+)", re.I)


def cout(prose):
    """{bj, or, engage, lisible} — ce qu'une cellule de prix dit VRAIMENT."""
    t = nu(prose or u"")
    b = BRAS.search(t)
    d = DRAGONS.search(t)
    e = ENGAGE.search(t)
    return {"bj": float(b.group(1).replace(u",", u".")) if b else None,
            "or": float(d.group(1).replace(u",", u".")) if d else None,
            "engage": e.group(1).replace(u" ", u"") if e else None,
            "lisible": bool(b or d)}


def cout_du_plan(pieces_du_plan, prix_de):
    """Le prix d'une voie : la somme de ce qui est lisible, et le compte de ce
    qui ne l'est pas. Les deux ensemble, jamais l'un sans l'autre."""
    bj = 0.0
    orr = 0.0
    flou = 0
    quand = []
    for a in pieces_du_plan:
        c = cout(prix_de.get(a))
        if c["bj"]:
            bj += c["bj"]
        if c["or"]:
            orr += c["or"]
        if not c["lisible"]:
            flou += 1
        if c["engage"]:
            quand.append(c["engage"])
    # LE PLUS TÔT COMMANDE : une voie est due le jour de son premier engagement,
    # pas le jour de son dernier. « J−22 » vient avant « J−6 ».
    def rang(x):
        try:
            return -int(re.sub(u"[^0-9]", u"", x))
        except Exception:
            return 0
    return {"bj": bj, "or": orr, "flou": flou,
            "quand": sorted(quand, key=rang)[0] if quand else None}


def dire_cout(c, n):
    """« 12 bj · 8 dragons · dû J−22 · 1 prix illisible sur 3 »."""
    bouts = []
    if c["bj"]:
        bouts.append(u"%g bras-jours" % c["bj"])
    if c["or"]:
        bouts.append(u"%g dragons" % c["or"])
    if c["quand"]:
        bouts.append(u"dû %s" % c["quand"])
    if c["flou"]:
        bouts.append(u"%d prix illisible%s sur %d"
                     % (c["flou"], u"s" if c["flou"] > 1 else u"", n))
    return u" · ".join(bouts) if bouts else u"aucun prix lisible"


def plan_de(k, pieces, sous):
    """LE PLAN PROPRE D'UNE OPTION — ce qu'on juge, au lieu de la phrase qui la
    nomme. Ses actions, plus tout ce qui ne dépend QUE d'elles. Mesuré sur les
    quatre-vingt-quatre options du plan : médiane 3 pièces, moyenne 4,2, jamais
    plus de 20. Deux plans de cette taille se posent côte à côte et se comparent
    à l'œil — ce n'était pas gagné d'avance, et c'est ce qui rend l'idée tenable
    ici. Sept options n'ont AUCUN plan propre : une clef retenue qui n'engage
    aucune action est une phrase, pas une voie, et ça doit se voir."""
    base = set(sous.get(k, []))
    bouge = True
    while bouge:
        bouge = False
        for n, p in pieces.items():
            if n in base:
                continue
            ds = [d for d in p["dep"] if d in pieces]
            if ds and all(d in base for d in ds):
                base.add(n)
                bouge = True
    return base


def declaree(ks, pieces):
    """Une fourche est DÉCLARÉE quand deux de ses options s'excluent l'une
    l'autre par le lien, SUPPOSÉE quand on ne l'infère que du nombre de clefs
    retenues. La différence n'est pas cosmétique : dans le second cas, trois
    clefs gardées peuvent être trois compléments qu'on veut tous les trois, et
    l'appeler « choix » est une lecture de plus qu'on prête au cahier."""
    return any(j in (pieces[k].get("exclut") or []) for k in ks for j in ks if j != k)


def decisions_ouvertes(pieces):
    """{verrou: [clefs retenues]} pour les verrous qui en ont plus d'une."""
    par = {}
    for n, p in pieces.items():
        if p["genre"] != "clef":
            continue
        for v in p["vers"]:
            if v in pieces and pieces[v]["genre"] == "verrou":
                par.setdefault(v, []).append(n)
    retenue = lambda k: u"retenue" in (pieces[k].get("etat") or u"").lower()  # noqa: E731
    out = {}
    for v, ks in par.items():
        gardees = sorted(k for k in ks if retenue(k))
        if len(gardees) > 1:
            out[v] = gardees
    return out


def arbre_des_decisions(pieces):
    """(decisions, aval, racines). `aval[v]` = les decisions que v commande."""
    dec = decisions_ouvertes(pieces)
    memo = {}

    def amont(n):
        """Tout ce qu'on atteint en remontant : les etats que n sert, de proche
        en proche jusqu'aux objectifs."""
        if n in memo:
            return memo[n]
        memo[n] = set()
        vu = {n}
        pile = [n]
        while pile:
            x = pile.pop()
            for v in pieces.get(x, {}).get("vers", []):
                if v in pieces and v not in vu:
                    vu.add(v)
                    pile.append(v)
        memo[n] = vu
        return vu

    # UNE DECISION EST EN AVAL D'UNE AUTRE quand elle bloque un etat que la
    # premiere sert. On ne la « rencontre » jamais en remontant — un verrou
    # pointe vers un etat, aucun etat ne pointe vers un verrou —, et c'est la
    # faute que j'ai faite en premier : elle rendait zero partout et faisait
    # conclure que les decisions etaient independantes. Elles ne le sont pas.
    aval = {}
    for v in dec:
        ets = amont(v) - {v}
        aval[v] = sorted(w for w in dec
                         if w != v and any(e in ets for e in pieces[w]["vers"]))
    commandees = {w for L in aval.values() for w in L}
    racines = sorted(v for v in dec if v not in commandees)
    return dec, aval, racines


def descendance(v, aval, vu=None):
    vu = vu if vu is not None else set()
    for w in aval.get(v, []):
        if w not in vu:
            vu.add(w)
            descendance(w, aval, vu)
    return vu


def section_decisions(pieces, lignes, attendu, prix_de, combien, une_seule=None):
    dec, aval, racines = arbre_des_decisions(pieces)
    score = {n: c + attendu.get(n, 0) for c, pt, n, p in lignes}
    sous = {}
    for n, p in pieces.items():
        if p["genre"] == "action":
            for k in p["vers"]:
                if k in pieces and pieces[k]["genre"] == "clef":
                    sous.setdefault(k, []).append(n)

    titre(u"🌳 L'ARBRE DES DÉCISIONS — %d fourches ouvertes, %d de premier rang"
          % (len(dec), len(racines)))
    dites = sum(1 for x, ks in dec.items() if declaree(ks, pieces))
    sys.stdout.write(
        u"  %d déclarée%s par le lien ⛔ Exclut · %d encore supposée%s\n\n"
        u"  Une fourche SUPPOSÉE est un verrou dont plusieurs clefs sont retenues — plusieurs\n"
        u"  mécanismes gardés pour une même serrure. C'est une LECTURE : trois clefs retenues\n"
        u"  peuvent aussi être trois compléments qu'on veut tous les trois. Une fourche DÉCLARÉE\n"
        u"  porte le lien ⛔ Exclut entre ses options, et là on ne suppose plus rien.\n\n"
        u"  On juge des PLANS, pas des phrases : chaque voie montre ce qu'elle engage — ses\n"
        u"  pièces, l'office sur qui elles tombent, leur jour — et ce qu'elle tue chez la voisine.\n"
        % (dites, u"s" if dites > 1 else u"", len(dec) - dites,
           u"s" if len(dec) - dites > 1 else u""))

    liste = [une_seule] if une_seule else racines
    for v in sorted(liste, key=lambda x: -len(descendance(x, aval))):
        if v not in dec:
            sys.stdout.write(u"\n  %s n'est pas une décision ouverte.\n" % v)
            continue
        p = pieces[v]
        d = descendance(v, aval)
        dit = declaree(dec[v], pieces)
        sys.stdout.write(u"\n  🔒 %s  %s   %s\n" % (
            v, p["nom"], u"[FOURCHE DÉCLARÉE]" if dit else u"[fourche supposée]"))
        sys.stdout.write(u"      %s · commande %d décision%s en aval\n"
                         % (p["affaire"][:52], len(d), u"s" if len(d) > 1 else u""))
        bloque = [e for e in p["vers"] if e in pieces]
        if bloque:
            sys.stdout.write(u"      bloque : %s\n" % u" · ".join(
                u"🎯 %s %s" % (e, pieces[e]["nom"][:40]) for e in bloque[:2]))
        toutes = dec[v]
        couts = {}
        for k in toutes:
            mien = plan_de(k, pieces, sous)
            # CE QU'ON TUE EN CHOISISSANT. Déclarée, l'exclusion dit exactement
            # quelles voies tombent ; supposée, on prend les autres options de la
            # serrure et l'on assume la lecture. Les deux nombres ne sont pas de
            # même nature, et le rendu ne les mélange pas.
            tuees = ([j for j in toutes if j in (pieces[k].get("exclut") or [])]
                     if dit else [j for j in toutes if j != k])
            perdu = set()
            for j in tuees:
                perdu |= plan_de(j, pieces, sous)
            af = sum(1 for a in mien if not faite(pieces[a]))
            c = cout_du_plan(mien, prix_de)
            couts[k] = c
            sys.stdout.write(u"\n      ├ 🗝️ %-6s %s\n" % (k, pieces[k]["nom"][:58]))
            sys.stdout.write(u"      │    LE PLAN : %d pièce%s, %d à faire%s\n"
                             % (len(mien), u"s" if len(mien) > 1 else u"", af,
                                u"   ⚠️ aucune action : c'est une phrase, pas une voie"
                                if not mien else u""))
            sys.stdout.write(u"      │    LE PRIX : %s\n" % dire_cout(c, len(mien)))
            for a in sorted(mien)[:6]:
                q = pieces[a]
                sys.stdout.write(u"      │      %s %-6s %-42s %-9s %s\n" % (
                    NOM_GENRE.get(q["genre"], u""), a, q["nom"][:42],
                    (q.get("office") or u"—")[:9],
                    sans_emoji(q.get("jour") or q.get("etat") or u"")[:18]))
            if len(mien) > 6:
                sys.stdout.write(u"      │      … et %d autres\n" % (len(mien) - 6))
            if tuees:
                sys.stdout.write(u"      │    %s : %s — %d pièce(s) retirée(s) du plan\n"
                                 % (u"tue" if dit else u"écarterait",
                                    u" ".join(tuees), len(perdu)))
            px = prix_de.get(k)
            if px:
                sys.stdout.write(u"      │    prix : %s\n" % nu(px)[:88])
        # L'ÉGALITÉ DÉGUISÉE EN ÉVIDENCE. C'est le cas qui a justifié tout ce
        # bloc : au compte des pièces, la fourche du débarquement se lit cinq
        # contre un ; au prix, douze bras-jours contre douze. On le DIT, parce
        # qu'un lecteur pressé s'arrête au premier nombre qu'il voit.
        lus = [(k, c) for k, c in couts.items() if c["bj"]]
        if len(lus) > 1:
            bas, haut = min(c["bj"] for _, c in lus), max(c["bj"] for _, c in lus)
            flou = sum(c["flou"] for _, c in lus)
            if haut and (haut - bas) / haut <= 0.15:
                sys.stdout.write(
                    u"      ⚖️ ÉGALITÉ DE PRIX : %s — le compte des pièces trompe ici.%s\n"
                    % (u" contre ".join(u"%g bj" % c["bj"] for _, c in lus),
                       u"" if not flou else u"  (%d prix illisible(s))" % flou))
        if aval[v]:
            sys.stdout.write(u"      └ ouvre ensuite : %s\n" % u" · ".join(
                u"🔒 %s %s" % (w, pieces[w]["nom"][:30]) for w in aval[v][:3]))
    if not une_seule:
        sys.stdout.write(
            u"\n  Les %d autres décisions sont PRÉMATURÉES : chacune dépend d'une fourche\n"
            u"  d'amont non tranchée. Les prendre aujourd'hui, c'est trancher sans savoir.\n"
            u"  `--decisions <n°>` déroule une fourche seule.\n" % (len(dec) - len(racines)))

