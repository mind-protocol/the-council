# -*- coding: utf-8 -*-
"""
partie_journal.py — ce qui vient d'être joué, dit en clair, pour l'écran.

Le plateau montre une POSITION, et il marque ce qui a bougé depuis le
marque-page : un anneau rouge, une pastille, « ils viennent de jouer — un coup
de plus au livre ». Ce qu'il ne disait pas, c'est CE QU'ILS ONT JOUÉ — et à deux
joueurs, c'est tout ce qu'on veut savoir en revenant devant l'écran. On voyait
une carte neuve sous une racine sans savoir si elle venait d'être posée, d'être
renforcée ou d'être questionnée.

Le greffe le sait depuis toujours : `partie_lecture.relire` rend les lignes du
livre au terminal, avec leurs emojis. Ce module fait la même chose pour l'écran,
à une différence près qui est tout le travail : LES IDS SONT RHABILLÉS DE LEURS
TITRES, comme le sont les refus. « lever a-barque-aurore-dime-aurore » ne dit
rien à personne ; « pose une clef pour « Le hameau d'en face nous paie la dîme »,
avec la barque » se lit sans rien ouvrir.

Il ne juge rien, ne compte rien et n'écrit nulle part. C'est une lecture, et
elle vit hors de `partie_cartes` — qui a passé les cinq cents lignes et ne peut
plus que maigrir.
"""
import re

import partie_cartes

MAX = 8            # au-delà, on ne lit plus : on rouvre le livre
SANS_MARQUE = 3    # première ouverture : les trois derniers coups, pour situer
COUPE = 60         # un titre plus long qu'une ligne de carte ne se lit pas


def _t(p, rid, coupe=COUPE):
    """Le titre d'une pièce, jamais son id, et jamais plus long qu'une ligne."""
    t = partie_cartes.titre(p, rid) or str(rid or "")
    return t if len(t) <= coupe else t[:coupe - 1].rstrip() + "…"


def _dit(p, l):
    """Une ligne du livre, en une phrase, sans le camp — l'écran le porte déjà."""
    coup = l.get("coup")
    texte = (l.get("texte") or "").strip()
    if coup == "viser":
        return "pose un état : « %s »" % _t(p, l.get("id"), 90)
    if coup == "lever":
        ouvre = [x for x in (l.get("ouvre") or []) if x]
        if ouvre:
            return "pose une clef contre « %s »" % _t(p, ouvre[0])
        if l.get("sert"):
            return "pose une clef pour « %s »" % _t(p, l.get("sert"))
        return "pose une clef"
    if coup == "bloquer":
        sur = l.get("sur")
        m = p.menaces.get(sur)
        if m is not None:
            return "pare la frappe sur « %s »" % _t(p, m["cible"])
        return "pose un verrou sur « %s »" % _t(p, sur)
    if coup == "rearmer":
        return "renforce « %s »" % _t(p, l.get("id"))
    if coup == "agir":
        return "écrit le maillon de « %s »" % _t(p, l.get("realise"))
    if coup == "justifier":
        return "exige la chaîne de « %s »" % _t(p, l.get("sur"))
    if coup == "demander":
        return "demande %s" % _t(p, l.get("id"), 90)
    if coup == "arbitrer":
        return "%s %s" % (l.get("verdict") or "arbitre", _t(p, l.get("sur")))
    if coup == "constater":
        return "constate « %s » : %s" % (_t(p, l.get("etat")), l.get("verdict") or "")
    if coup == "retirer":
        return "reprend « %s »" % _t(p, l.get("id"))
    if coup == "detruire":
        return "frappe %s" % _t(p, l.get("cible"))
    if coup == "retourner":
        return "tente de retourner %s" % _t(p, l.get("cible"))
    if coup == "reconstruire":
        return "reconstruit %s" % _t(p, l.get("id"))
    if coup == "consigne":
        return "donne une consigne"
    if coup == "passer":
        return "passe son tour"
    if coup == "tour":
        return "le jour passe"
    return str(coup or "")


def _phrase(p, l):
    """La phrase, et ce qu'elle traîne : le texte du joueur, les pièces mises."""
    dit = _dit(p, l)
    texte = (l.get("texte") or "").strip()
    coup = l.get("coup")
    if texte and coup in ("lever", "bloquer", "rearmer", "agir", "justifier", "retirer"):
        dit += " : « %s »" % (texte if len(texte) <= 120 else texte[:119].rstrip() + "…")
    engage = [x for x in (l.get("engage") or []) if x]
    if engage:
        dit += " · avec " + ", ".join(_t(p, x, 40) for x in engage)
    return dit


def clair(p, texte):
    """Un motif du greffe, ses ids rhabilles de leurs titres.

    « leve par 🗝️ e-e-registre-t-t-bourse-e-un-nom » ne dit rien a personne, et
    c'est pourtant LE verdict d'un front — la seule ligne que le plateau ait a
    dire. Meme geste que pour les refus (`partie_gestes._lisible`) : on ne sert
    jamais un id nu a l'ecran."""
    out = str(texte or "")
    for mot in sorted(set(re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{3,60}", out)),
                      key=len, reverse=True):
        t = partie_cartes.titre(p, mot)
        if t and t != mot:
            out = out.replace(mot, "« %s »" % _t(p, mot, 42))
    return out


def journal(p, camp=None, vu=0, maximum=MAX):
    """Les derniers coups en clair, du plus ancien au plus récent.

    `vu` est le marque-page du siège : ce qui vient APRÈS est ce qu'il n'a pas
    vu, et c'est cela qu'on rend. Sans marque-page — première ouverture —, on
    rend les trois derniers coups : assez pour savoir où l'on tombe, pas assez
    pour tenir lieu de relecture.
    """
    lignes = [l for l in p.lignes if l.get("n")]
    if not lignes:
        return []
    vu = int(vu or 0)
    if vu:
        pris = [l for l in lignes if int(l["n"]) > vu]
    else:
        pris = lignes[-SANS_MARQUE:]
    # LES VERDICTS DU TOUR NE S'EFFACENT PAS QUAND ON JOUE. « Qu'est-ce qui a
    # ete accorde, et qu'est-ce qui a ete refuse ? » est la question qu'on se
    # pose EN JOUANT, pas seulement en revenant : un arbitrage decide de ce
    # qu'on a en main, et le marque-page l'effacait au premier coup joue. Ceux
    # du tour en cours restent donc, quel que soit le marque-page.
    ns = set(int(l["n"]) for l in pris)
    tour = lignes[-1].get("tour")
    pris = pris + [l for l in lignes
                   if l.get("tour") == tour and int(l["n"]) not in ns
                   and l.get("coup") in ("arbitrer", "constater")]
    pris.sort(key=lambda l: int(l["n"]))
    pris = pris[-int(maximum or MAX):]
    return [{"n": int(l["n"]), "tour": l.get("tour"), "camp": l.get("camp"),
             "coup": l.get("coup"), "nous": bool(camp) and l.get("camp") == camp,
             "dit": _phrase(p, l)}
            for l in pris]
