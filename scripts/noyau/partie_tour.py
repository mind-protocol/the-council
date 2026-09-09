# -*- coding: utf-8 -*-
"""
partie_tour.py — ce qui se passe au PASSAGE DU TOUR d'une partie (mj-partie.md §4-§5).

Sorti de partie_greffe.py le 3.9 : le greffe applique les coups un à un ; ici
vit ce qui n'appartient à aucun coup et tombe au changement de tour — ce que
la ligne `tour` annonce (`ligne`) et ce qu'elle applique (`appliquer`). Les
deux lisent la même position, dans le même ordre, pour que ce qui est annoncé
soit exactement ce qui est fait.

Quatre règles alignées le 3.9 sur le duel de 50 tours :
- une parade tient UN tour, puis la frappe tombe (règle 7 : un heurt se tranche,
  il ne se neutralise pas neuf tours) — sauf arbitrage avant ;
- le greffe LISTE les états constatables, pour que constater cesse de dépendre
  de l'attention de l'arbitre ;
- un camp muet trois tours d'affilée est signalé, comme une branche morte ;
- (dans le greffe) un maillon qui répond à un justifier ne compte pas.
"""


def _g():
    import partie_greffe as g
    return g


TOURS_MUET = 3   # passer (ou rien) trois tours de suite : le camp est signalé inactif


def tolerees(p):  # regle: branche-morte
    """Une pièce qui a figuré une fois dans un engage, un avec, un qui ou une
    consigne n'est jamais une branche morte (le guetteur et le septon d'essai-1)."""
    liste, vues = _g().liste, set()
    for x in p.lignes:
        for pc in (liste(x.get("engage")) + liste(x.get("avec"))
                   + liste(x.get("pieces")) + liste(x.get("qui"))):
            vues.add(pc)
    return vues


def _en_l_air(p, tour):
    """Les menaces vivantes dont l'heure est passée, en trois tas : atterrissent,
    parées pour de bon (deuxième tour de parade), parées ou suspendues (attendent)."""
    tombent, attendent, parees = [], [], []
    for mid, m in p.menaces.items():
        if m["realisee"] or m["tombee"] or m["arrive_tour"] >= tour:  # regle: menace-datee
            continue
        if m.get("suspendue_par"):  # regle: menace-suspendue-attend
            attendent.append(mid)
        elif p._protegee(mid):  # regle: parade-un-tour
            (parees if m.get("paree_tour") else attendent).append(mid)
        else:
            tombent.append(mid)
    return tombent, parees, attendent


def constatables(p):  # regle: greffe-liste-arbitre-constate
    """Les états au deck, non constatés, que rien n'empêche plus : tous leurs
    blocages sont tombés ou levés par une clé qui prévaut ; ou, sans blocage,
    une clé valide les sert. Une liste, pas un verdict : l'arbitre constate."""
    out = []
    for eid, e in p.etats.items():
        if not e.get("deck") or e.get("vrai") is not None:
            continue
        blocs = [bid for bid, b in p.blocages.items() if b["sur"] == eid]
        if blocs:
            if all(p.blocages[b]["tombe"] or p.prevaut(b)[0] == e["camp"] for b in blocs):
                out.append(eid)
            continue
        for kid, k in p.cles.items():
            if (k.get("sert") == eid and k["camp"] == e["camp"] and not k["retiree"]
                    and not k.get("tenue") and not k["suspendue_par"]
                    and k.get("prete_tour", 0) <= p.tour
                    and not p._pieces_libres(k["camp"], k["engage"], kid)):
                out.append(eid)
                break
    return out


def inactifs(p, tour):  # regle: greffe-liste-arbitre-constate, reponse-gratuite
    """Les camps qui n'ont rien joué d'autre que passer sur les TOURS_MUET derniers tours."""
    g = _g()
    if tour <= TOURS_MUET:
        return []
    out = []
    for camp in p.camps():
        joues = [x for x in p.lignes if x.get("camp") == camp and x.get("coup") in g.COUPS_COMPTES
                 and not x.get("repond") and tour - TOURS_MUET <= int(x.get("tour") or 0) < tour]
        if all(x.get("coup") == "passer" for x in joues):
            out.append(camp)
    return out


def ligne(p, tour):  # regle: passage-du-tour, coup-tour
    """Ce que la ligne `tour` annonce, calculé sur la position AVANT le passage."""
    g = _g()
    tombent, parees, attendent = _en_l_air(p, tour)
    frappees = set(p.menaces[m]["cible"] for m in tombent)
    tol = tolerees(p)
    return {
        "arrivees": [rid for rid, r in p.ressources.items()
                     if r.get("arrive_tour") == tour and not r.get("en_attente")],
        "degeles": [rid for rid, r in p.ressources.items() if r.get("gel_jusqu") == tour],
        "menaces": tombent,
        "parees": attendent,
        "parades_tenues": parees,
        "etats_arrives": [eid for eid, e in p.etats.items()
                          if e.get("arrive_tour") == tour and not e.get("sorti")],
        "constatables": constatables(p),
        "inactifs": inactifs(p, tour),
        "branches_mortes": [rid for rid, r in p.ressources.items()  # regle: branche-morte
                            if not r["engagee_par"] and not r.get("detruite")
                            and not r.get("en_attente") and rid not in frappees
                            and r.get("arrive_tour", 0) + 2 <= tour and rid not in tol],
        "jours": g.JOURS_PAR_TOUR,
    }


def appliquer(p, l):  # regle: passage-du-tour
    """Le passage du tour sur la position : états datés au deck, menaces qui
    atterrissent, parades qui tiennent (la frappe tombe, l'écran est rendu, la
    pièce qui frappait rentre gelée un tour), premières parades marquées."""
    g = _g()
    p.tour = int(l.get("tour") or p.tour + 1)
    for e in p.etats.values():
        if e.get("arrive_tour") and not e.get("sorti") and int(e["arrive_tour"]) <= p.tour:  # regle: deck-calendrier
            e["deck"] = True
    tombent, parees, attendent = _en_l_air(p, p.tour)
    for mid in tombent:
        p._realiser_menace(mid, None)
    for mid in parees:  # regle: parade-un-tour, defenseur-tient
        m = p.menaces[mid]
        m["tombee"], m["paree_tenue"] = True, p.tour
        p._liberer(mid, g.GEL_FRAPPE)
        p._menace_finie(mid)
    for mid in attendent:
        m = p.menaces[mid]
        if not m.get("suspendue_par") and not m.get("paree_tour"):
            m["paree_tour"] = p.tour
