# -*- coding: utf-8 -*-
"""
partie_lecture.py — ce qui se LIT d'une partie : la chaîne d'une pièce, la fiche
d'une ressource, le grand livre, l'état, la relecture.

Séparé de partie_greffe.py (le repli et les règles) parce qu'aucune de ces
fonctions ne change la position : elles la parcourent et la rendent en texte.
Une règle du jeu se change dans partie_greffe ; une façon de la montrer, ici.
Chaque fonction prend la partie repliée (`p`) en premier argument.
"""
from partie_greffe import DECK_MAX, EMOJI_CAMP, EMOJI_COUP, JOURS_PAR_TOUR, adverse, liste


def chaine(p, cible):
    """Tout ce qui se rattache à un id : état, blocage, clé, maillon, pièce."""
    out = []
    if cible in p.etats:
        e = p.etats[cible]
        out.append("🎯 %s %s — %s%s" % (EMOJI_CAMP[e["camp"]], cible, e["texte"],
                                        " · VRAI" if e["vrai"] else ""))
        for bid, b in p.blocages.items():
            if b["sur"] == cible:
                out += ["   " + x for x in chaine(p, bid)]
    elif cible in p.blocages:
        b = p.blocages[cible]
        qui, pourquoi = p.prevaut(cible)
        out.append("🔒 %s %s — %s · sur %s · %s [%s]" % (EMOJI_CAMP[b["camp"]], cible, b["texte"], b["sur"],
                                                      pourquoi, EMOJI_CAMP[qui]))
        for kid, k in p.cles.items():
            if cible in k["ouvre"] and not k["retiree"]:
                out += ["   " + x for x in chaine(p, kid)]
    elif cible in p.cles:
        k = p.cles[cible]
        etat = ("suspendue par ❓ %s" % k["suspendue_par"] if k["suspendue_par"]
                else "tenue, blocage tombé" if k.get("tenue") else "retirée" if k["retiree"] else "valide")
        out.append("🗝️ %s %s — %s · ouvre %s · engage %s · %s" % (
            EMOJI_CAMP[k["camp"]], cible, k["texte"], ", ".join(k["ouvre"]), ", ".join(k["engage"]), etat))
        for mid, m in p.maillons.items():
            if m["realise"] == cible:
                out.append("   ⚔️ %s — %s · %s · avec %s [%s]" % (
                    mid, m["texte"], m.get("qui") or "?", ", ".join(m["avec"]) or "—", m["etat"]))
                for bid, b in p.blocages.items():
                    if b["sur"] == mid:
                        out += ["      " + x for x in chaine(p, bid)]
    elif cible in p.ressources:
        out += piece(p, cible)
    else:
        out.append("rien ne s'appelle %s" % cible)
    return out

def piece(p, rid):
    r = p.ressources.get(rid)
    if not r:
        return ["pièce inconnue : %s" % rid]
    etat = []
    if r.get("en_attente"):
        etat.append("attend l'arbitrage (ligne %s)" % r["en_attente"])
    if r.get("detruite"):
        etat.append("DÉTRUITE")
    if r.get("arrive_tour", 0) > p.tour:
        etat.append("arrive au tour %d" % r["arrive_tour"])
    if r.get("gel_jusqu", 0) > p.tour:
        etat.append("gelée jusqu'au tour %d" % r["gel_jusqu"])
    if r["engagee_par"]:
        etat.append("engagée par " + ", ".join(r["engagee_par"]))
    if not etat:
        etat.append("libre")
    out = ["📦 %s %s — %s · %s%s · %s" % (EMOJI_CAMP[r["camp"]], rid, r.get("lieu") or "?",
                                        ("%s · " % r["nombre"]) if r.get("nombre") else "",
                                        r.get("tenu_par") or "", " · ".join(etat))]
    if r.get("source"):
        out.append("   source : %s" % r["source"])
    for par in r["engagee_par"]:
        if par in p.cles:
            k = p.cles[par]
            out.append("   🗝️ %s — %s (ouvre %s)" % (par, k["texte"], ", ".join(k["ouvre"])))
        elif par in p.blocages:
            out.append("   🔒 %s — %s (sur %s)" % (par, p.blocages[par]["texte"], p.blocages[par]["sur"]))
        elif par in p.menaces:
            out.append("   💥 %s — %s (cible %s)" % (par, p.menaces[par]["texte"], p.menaces[par]["cible"]))
    for mid, m in p.maillons.items():
        if rid in m["avec"] or m.get("qui") == rid:
            out.append("   ⚔️ %s — %s [%s]" % (mid, m["texte"], m["etat"]))
    for mid, m in p.menaces.items():
        if m["cible"] == rid and not m["realisee"] and not m["tombee"]:
            out.append("   ⚠️ visée par 💥 %s au tour %d" % (mid, m["arrive_tour"]))
    if rid in p.consignes:
        out.append("   📋 consigne : " + p.consignes[rid])
    return out

def grand_livre(p):
    out = []
    for camp in ("noir", "vert"):
        out.append("%s %s" % (EMOJI_CAMP[camp], camp))
        for rid, r in sorted(p.ressources.items()):
            if r["camp"] == camp:
                out += ["  " + x for x in piece(p, rid)[:1]]
    return out

def _sous(p, eid, prof, out):
    """Ce qui pend à un état : ses blocages (colorés par qui y prévaut), les clés
    qui les ouvrent, les maillons réalisés, puis les états qui le servent —
    « sous lui, la chaîne des blocages et des clés » (mj-partie.md §5.3)."""
    ind = "   " * prof
    for bid, b in sorted(p.blocages.items(), key=lambda kv: -(kv[1].get("n") or 0)):
        if b["sur"] != eid:
            continue
        qui, pourquoi = p.prevaut(bid)
        out.append("%s← %s 🔒 %s %s — %s" % (ind, EMOJI_CAMP[qui], bid, b["texte"], pourquoi))
        for kid, k in p.cles.items():
            if bid in k["ouvre"] and not k["retiree"] and not k.get("tenue"):
                for mid, m in sorted(p.maillons.items()):
                    if m["realise"] == kid and m["etat"] == "faite":
                        out.append("%s   ← %s ⚔️ %s %s — réalisé" % (ind, EMOJI_CAMP[m["camp"]], mid, m["texte"]))
    for cid, e in p.etats.items():
        if e.get("sert") != eid or not e.get("deck"):
            continue
        feu = " · VRAI" if e.get("vrai") else (" · faux" if e.get("vrai") is False else "")
        feu += " · en question ❓ %s" % e["suspendue_par"] if e.get("suspendue_par") else ""
        out.append("%s🎯 %s %s — %s%s" % (ind, EMOJI_CAMP[e["camp"]], cid, e["texte"], feu))
        _sous(p, cid, prof + 1, out)


def etat(p):
    out = []
    racine = p.racine()
    tenu = p.tenu_par()
    out.append("Tour %d · jour du monde +%d" % (p.tour, (p.tour - 1) * JOURS_PAR_TOUR))
    out.append("👑 Trône — tenu par %s" % EMOJI_CAMP[tenu])
    if racine:
        _sous(p, racine, 0, out)
        for kid, k in sorted(p.cles.items(), key=lambda kv: -(kv[1].get("n") or 0)):
            if k["retiree"] or k.get("tenue") or k["ouvre"]:
                continue   # une clé sans blocage : une affirmation nue, on la montre à part
            qui = k["camp"] if not k["suspendue_par"] else adverse(k["camp"])
            out.append("← %s 🗝️ %s %s — n'ouvre rien%s" % (
                EMOJI_CAMP[qui], kid, k["texte"],
                " · suspendue par ❓ %s" % k["suspendue_par"] if k["suspendue_par"] else ""))
    tenues = [kid for kid, k in p.cles.items() if k.get("tenue")]
    if tenues:
        out.append("Tenues (leur blocage est tombé, pièces rendues) : " + " · ".join(tenues))
    a_venir = ["%s (tour %d)" % (eid, e["arrive_tour"]) for eid, e in p.etats.items()
               if e.get("arrive_tour") and not e.get("deck") and not e.get("sorti")]
    if a_venir:
        out.append("États datés à venir : " + " · ".join(a_venir))
    menaces = ["💥 %s → %s au tour %d" % (mid, m["cible"], m["arrive_tour"])
               for mid, m in p.menaces.items() if not m["realisee"] and not m["tombee"]]
    if menaces:
        out.append("Menaces : " + " · ".join(menaces))
    gel = ["%s (%d)" % (rid, r["gel_jusqu"] - p.tour) for rid, r in p.ressources.items()
           if r.get("gel_jusqu", 0) > p.tour]
    if gel:
        out.append("Gelés : " + " · ".join(gel))
    arr = ["%s (tour %d)" % (rid, r["arrive_tour"]) for rid, r in p.ressources.items()
           if r.get("arrive_tour", 0) > p.tour and not r.get("en_attente")]
    if arr:
        out.append("Arrivées : " + " · ".join(arr))
    att = [rid for rid, r in p.ressources.items() if r.get("en_attente")]
    if att:
        out.append("À arbitrer : " + " · ".join(att))
    deck = {c: [e for e, x in p.etats.items() if x["camp"] == c and x.get("deck")] for c in ("noir", "vert")}
    out.append("Deck : ⚫ %d/%d · 🟢 %d/%d" % (len(deck["noir"]), DECK_MAX, len(deck["vert"]), DECK_MAX))
    dernier = p.lignes[-1]["camp"] if p.lignes else "vert"
    trait = "noir" if dernier in ("vert", "arbitre") else "vert"
    out.append("Trait aux %ss." % ("Noir" if trait == "noir" else "Vert"))
    return out

def relire(p, depuis=1):
    out = []
    for l in p.lignes:
        if (l.get("n") or 0) < depuis:
            continue
        e = EMOJI_CAMP.get(l.get("camp"), "?") + EMOJI_COUP.get(l.get("coup"), "?")
        texte = l.get("texte") or l.get("motif") or ""
        extra = ""
        if l.get("coup") == "arbitrer":
            extra = " [%s%s]" % (l.get("verdict"), " · tour %s" % l["arrive_tour"] if l.get("arrive_tour") else "")
        if l.get("engage"):
            extra += " · engage " + ", ".join(liste(l["engage"]))
        out.append("%s %s — %s%s" % (e, l.get("n"), texte, extra))
    return out


