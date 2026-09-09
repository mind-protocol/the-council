# -*- coding: utf-8 -*-
"""
partie_validite.py — la recevabilité d'un coup (mj-partie.md §3, « les règles de validité »).

Séparé de partie_greffe.py parce que rien ici ne change la position : on lit la
partie repliée et l'on rend la liste des refus, avec leur raison. Le greffe
applique ; ce module dit si l'on a le droit. Une règle de validité se change ici,
une règle d'application dans le greffe. `verifier(p, l)` est la seule entrée ;
`pieces_libres` et `id_pris` sont ses outils, que le greffe réutilise pour
`prevaut`.
"""


def _c():
    # import tardif : le greffe importe ce module, on ne le charge qu'à l'appel
    import partie_greffe as g
    return g


def id_pris(p, i):  # regle: un-id-un-objet
    """Un id n'a qu'un objet : état, blocage, clé, maillon ou destruction."""
    return (i in p.blocages or i in p.cles or i in p.maillons
            or i in p.menaces or i in p.etats)


def pieces_libres(p, camp, pieces, par, vide=None):
    """`vide` : le refus si aucune pièce n'est donnée (« pas de ressource, pas de coup »)."""
    g = _c()
    if not g.liste(pieces):  # regle: pas-de-ressource-pas-de-coup, blocage-tombe-avec-sa-piece
        # Sans `vide` (prevaut, constatables) : une clef dont la pièce a été
        # retirée n'engage plus rien, et « rien » n'est pas une ressource.
        return [vide or "aucune pièce engagée (réarmer)"]
    refus = []
    for pc in g.liste(pieces):
        r = p.ressources.get(pc)
        if r is None:  # regle: etats-ressource, ressource-demandee-puis-arbitree
            refus.append("%s n'est pas au grand livre (demander, puis arbitrer)" % pc)
            continue
        if r.get("en_attente"):
            refus.append("%s attend son arbitrage (ligne %s)" % (pc, r["en_attente"]))
        elif r.get("detruite"):
            refus.append("%s est détruite" % pc)
        elif r["camp"] != camp:
            refus.append("%s est une pièce %s" % (pc, r["camp"]))
        elif r.get("gel_jusqu", 0) > p.tour:
            refus.append("%s est gelée jusqu'au tour %d" % (pc, r["gel_jusqu"]))
        elif r["engagee_par"] and par not in r["engagee_par"]:  # regle: engage-jusqu-a-chute
            refus.append("%s déjà engagée par %s" % (pc, ", ".join(r["engagee_par"])))
    return refus


def verifier(p, l):
    """Rend la liste des refus. Vide = le coup est recevable."""
    g = _c()
    liste = g.liste
    refus = []
    camp, coup = l.get("camp"), l.get("coup")
    if not camp or not isinstance(camp, str):
        refus.append("camp manquant : %r" % camp)
    elif camp == g.ARBITRE and coup not in ("arbitrer", "constater", "tour", "justifier"):  # regle: seul-l-arbitre
        refus.append("l'arbitre ne joue pas : il arbitre, constate, justifie et passe le tour")
    if coup not in g.COUPS:
        refus.append("coup inconnu : %r" % coup)
    # UNE PARTIE PEUT SORTIR DES COUPS DU JEU (`coups_interdits` de sa
    # configuration, 6.9 : charmed se joue sans retourner, reconstruire,
    # rearmer ni consigne). Le greffe les refuse en clair, comme un coup
    # inconnu — l'écran et l'IA n'ont pas à le savoir pour être justes.
    if coup in (g.config(p.chemin).get("coups_interdits") or []):
        refus.append("« %s » est hors de cette partie : elle se joue sans ce coup" % coup)
    # RETIRÉS DES RÈGLES LE 6.9 (docs/parties/gestes-manquants.md) : un coup de
    # joueur qui n'a pas de geste à l'écran n'existe pas pour le joueur. Le
    # greffe continue de REPLIER les lignes anciennes (le rejeu ne passe pas
    # ici) ; il refuse les neuves.
    if coup == "consigne":
        refus.append("la consigne est sortie des règles le 6.9 : sans consigne, une pièce tient, "
                     "et c'est déjà ce que fait le greffe")
    if coup == "lever" and len(g.liste(l.get("ouvre"))) > 1:
        refus.append("une clef lève UN verrou (règle du 6.9) : deux verrous, deux clefs")
    if coup == "agir" and l.get("etat"):
        refus.append("un maillon n'a plus d'état (règle du 6.9) : il s'écrit quand c'est fait")
    if coup == "demander" and camp != g.ARBITRE and (l.get("lieu") or l.get("tenu_par")):
        refus.append("le lieu et le tenant d'une pièce sont posés par l'arbitre en accordant "
                     "(règle du 6.9) : dites-les dans la phrase, pas dans la ligne")
    if coup != "tour" and l.get("tour") is not None:  # regle: ligne-au-tour-courant
        # Seul le greffe pose le tour (T3) : une ligne de camp datée d'un autre
        # tour faisait sauter la partie à ce tour sans qu'aucun ne passe (A5).
        try:
            if int(l["tour"]) != p.tour:
                refus.append("%s : la ligne est datée du tour %s et la partie est au tour %d ; "
                             "le tour ne se pose que par « tour »" % (coup, l["tour"], p.tour))
        except (TypeError, ValueError):
            refus.append("%s : tour %r n'est pas un nombre" % (coup, l["tour"]))
    if refus:
        return refus
    if coup in ("viser", "bloquer", "lever", "agir", "detruire", "retourner") and not l.get("id"):
        return ["%s : il faut un id" % coup]
    if coup in ("bloquer", "lever", "detruire", "retourner") and id_pris(p, l.get("id")):  # regle: un-id-un-objet
        return ["%s : l'id %s est déjà pris ; une correction est un coup de plus, jamais une réécriture" % (coup, l["id"])]
    if coup == "viser":  # regle: coup-viser
        # un état constaté vrai a fait son office : il ne tient plus de place (règle 9)
        deck = [e for e in p.etats.values() if e["camp"] == camp and not e.get("vrai")
                and g.au_deck(e, p.tour, reserve=True)]
        if len(deck) >= g.DECK_MAX:  # regle: dix-etats
            refus.append("deck %s plein (%d) : sortir un état d'abord" % (camp, g.DECK_MAX))
        if id_pris(p, l["id"]):
            refus.append("état %s déjà posé" % l["id"])
        if l.get("arrive_tour") is not None and int(l["arrive_tour"]) < p.tour:  # regle: deck-calendrier
            refus.append("viser : arrive_tour %s est déjà passé (tour %d)" % (l["arrive_tour"], p.tour))
    elif coup == "sortir":  # regle: coup-sortir
        e = p.etats.get(l.get("id"))
        if not e or e["camp"] != camp or not e["deck"]:
            refus.append("état %s n'est pas dans le deck %s" % (l.get("id"), camp))
    elif coup == "demander":  # regle: coup-demander
        if not l.get("id"):
            refus.append("demander : il faut un id de ressource")
        elif l["id"] in p.ressources and not p.ressources[l["id"]].get("detruite"):  # regle: un-id-un-objet
            refus.append("ressource %s déjà au grand livre" % l["id"])
    elif coup == "arbitrer":  # regle: coup-arbitrer
        if camp != "arbitre":  # regle: seul-l-arbitre, camp-ne-tranche-pas-autrui
            refus.append("seul l'arbitre arbitre")
        if not p._lignes_visees(l.get("sur")):  # regle: arbitrage-vise-un-id
            refus.append("arbitrer : rien ne s'appelle %s (id, ou numéro de ligne à défaut)" % l.get("sur"))
        if l.get("verdict") not in ("accorde", "refuse", "tranche", "reporte"):
            refus.append("verdict inconnu : %r" % l.get("verdict"))
        if not l.get("motif"):
            refus.append("un arbitrage porte toujours son motif et sa source")
        if l.get("arrive_tour") is not None and int(l["arrive_tour"]) < p.tour:
            # même garde que `viser` : une arrivée datée dans le passé faisait
            # vieillir la pièce d'avance et la signalait branche morte au tour
            # suivant, alors qu'elle venait d'être accordée.
            refus.append("arbitrer : arrive_tour %s est déjà passé (tour %d) ; "
                         "une arrivée se date au tour courant ou plus tard" % (l["arrive_tour"], p.tour))
        for src in p._lignes_visees(l.get("sur")):
            if src.get("coup") not in ("detruire", "retourner"):
                continue
            m = p.menaces.get(src["id"])
            if m and (m["realisee"] or m["tombee"]):  # regle: atterrissage-total
                # Règle 12 : après l'atterrissage, la pièce est sortie du grand
                # livre. Un « tranche » tardif ne la rend pas partielle, il ne
                # fait rien — et faire rien en silence est le pire des verdicts.
                refus.append("arbitrer : la destruction %s a déjà %s (tour %s) — règle 12, "
                             "un heurt partiel se tranche AVANT le passage du tour ; "
                             "après, une correction est un coup de plus"
                             % (src["id"], "atterri" if m["realisee"] else "été retirée",
                                m.get("realisee_tour") or "?"))
    elif coup == "bloquer":  # regle: coup-bloquer
        sur = l.get("sur")
        cible = (p.etats.get(sur) or p.maillons.get(sur) or p.cles.get(sur) or p.menaces.get(sur))
        if not cible:
            refus.append("bloquer : %s n'est ni un état, ni un maillon, ni une clé, ni une destruction" % sur)
        elif cible["camp"] == camp:  # regle: blocage-par-un-autre-camp
            refus.append("un blocage se pose sur l'autre camp, jamais sur soi")
        refus += pieces_libres(p, camp, l.get("engage"), l.get("id"),
                               "pas de ressource, pas de coup : un blocage engage la pièce qui le produit")
    elif coup == "lever":  # regle: coup-lever
        for b in liste(l.get("ouvre")):
            if b not in p.blocages:
                refus.append("lever : le blocage %s n'existe pas" % b)
            elif p.blocages[b]["camp"] == camp:
                refus.append("lever : %s est un blocage à soi" % b)
            elif p.blocages[b]["tombe"]:
                refus.append("lever : le blocage %s est déjà tombé" % b)
        refus += pieces_libres(p, camp, l.get("engage"), l.get("id"),
                               "pas de ressource, pas de coup : une clé engage au moins une pièce")
    elif coup == "agir":  # regle: coup-agir
        if l.get("id") in p.maillons and l.get("etat") and not l.get("realise"):
            if p.maillons[l["id"]]["camp"] != camp:
                refus.append("agir : le maillon %s n'est pas au camp %s" % (l["id"], camp))
        elif id_pris(p, l.get("id")):
            refus.append("agir : l'id %s est déjà pris" % l["id"])
        else:
            k = (p.cles.get(l.get("realise")) or p.menaces.get(l.get("realise"))
                 or p.blocages.get(l.get("realise")))
            if not k:
                refus.append("agir : %s n'est ni une clé, ni un blocage, ni une destruction"
                             % l.get("realise"))
            elif k["camp"] != camp:
                refus.append("agir : %s n'est pas au camp %s" % (l["realise"], camp))
            for pc in liste(l.get("avec")):  # regle: maillon-piece-inconnue
                r = p.ressources.get(pc)
                if r is None:
                    p.avertissements.append("maillon %s : %s n'est pas au grand livre" % (l.get("id"), pc))
                elif r.get("detruite"):
                    refus.append("agir : %s est détruite" % pc)
    elif coup == "justifier":  # regle: coup-justifier
        sur = l.get("sur")
        cible = (p.cles.get(sur) or p.menaces.get(sur)
                 or p.blocages.get(sur) or p.etats.get(sur))
        if cible is None:
            refus.append("justifier : %s n'est ni une clé, ni un blocage, ni une destruction, ni un état" % sur)
        else:
            if camp != "arbitre" and cible["camp"] == camp:  # regle: pas-sa-propre-chaine, arbitre-justifie
                refus.append("on n'exige pas sa propre chaîne")
            if cible.get("justifiee"):  # regle: justifier-une-fois
                refus.append("justifier : %s l'a déjà été (ligne %s) ; une justification par pièce" % (sur, cible["justifiee"]))
    elif coup == "rearmer":  # regle: coup-rearmer
        i = l.get("id")
        cible = p.cles.get(i) or p.blocages.get(i)
        if not cible:
            refus.append("réarmer : %s n'est ni une clé ni un blocage" % i)
        elif cible["camp"] != camp:
            refus.append("réarmer : %s n'est pas à %s" % (i, camp))
        elif cible.get("retiree") or cible.get("tombe") or cible.get("tenue"):
            refus.append("réarmer : %s est retiré, tombé ou tenu ; reposer" % i)
        refus += pieces_libres(p, camp, l.get("engage"), i, "réarmer : il faut la pièce qu'on ajoute")
    elif coup in ("detruire", "retourner"):  # regle: coup-detruire, coup-retourner
        verbe = "détruire" if coup == "detruire" else "retourner"
        prix = "la pièce qui frappe" if coup == "detruire" else "ce qu'on y met"
        r = p.ressources.get(l.get("cible"))
        if not r or r.get("detruite"):
            refus.append("%s : %s n'est pas une ressource posée" % (verbe, l.get("cible")))
        elif r["camp"] == camp:
            refus.append("%s : %s est une pièce à soi" % (verbe, l["cible"]))
        refus += pieces_libres(p, camp, l.get("engage"), l.get("id"), "%s : il faut %s" % (verbe, prix))
    elif coup == "retirer":  # regle: coup-retirer
        i = l.get("id")
        reg = next((r for r in (p.cles, p.blocages, p.menaces, p.ressources) if i in r), None)
        if reg is None:
            refus.append("retirer : %s n'est ni une clé, ni un blocage, ni une destruction, ni une pièce" % i)
        elif reg[i]["camp"] != camp:
            refus.append("retirer : %s n'est pas à %s" % (i, camp))
        elif reg is p.ressources and reg[i].get("detruite"):
            refus.append("retirer : %s est déjà détruite" % i)
    elif coup == "reconstruire":  # regle: coup-reconstruire, reconstruire-ce-qui-se-reconstruit
        r = p.ressources.get(l.get("id"))
        if not r or not r.get("detruite"):
            refus.append("reconstruire : %s n'est pas détruite" % l.get("id"))
        elif r["camp"] != camp:
            refus.append("reconstruire : %s n'est pas à %s" % (l["id"], camp))
    elif coup == "constater":  # regle: coup-constater
        if camp != "arbitre":
            refus.append("seul l'arbitre constate")
        if l.get("etat") not in p.etats:
            refus.append("constater : état %s inconnu" % l.get("etat"))
        elif l.get("verdict") == "vrai":
            # Contrôle gradué : l'arbre n'est pas une conjonction — un état peut
            # être vrai sans que tout ce qui le sert le soit —, mais le trône
            # constaté par-dessus deux états jamais tranchés doit se voir.
            parent = p.etats[l["etat"]]
            ouverts = [eid for eid, e in p.etats.items()  # regle: etat-vrai-libere
                       if e.get("sert") == l["etat"] and e["camp"] == parent["camp"]
                       and g.au_deck(e, p.tour) and e.get("vrai") is None]
            if ouverts:
                p.avertissements.append(
                    "constater %s vrai : %s le sert et n'est ni constaté ni sorti du deck"
                    % (l["etat"], ", ".join(ouverts)))
    elif coup == "tour":  # regle: coup-tour
        if camp != "arbitre":
            refus.append("seul l'arbitre passe le tour")
    if not refus and coup in g.COUPS_COMPTES and camp != g.ARBITRE and not l.get("repond"):  # regle: un-coup-par-tour, reponse-gratuite
        # « un camp ne joue qu'un coup par tour » (§3) : contrôle gradué, signalé
        # sans bloquer — l'ouverture pose dix états et leurs ressources d'un coup.
        # Un maillon qui répond à un ❓ (`repond`) ne compte pas.
        deja = [x for x in p.lignes if x.get("camp") == camp and x.get("coup") in g.COUPS_COMPTES
                and not x.get("repond") and int(x.get("tour") or 0) == p.tour]
        if deja:
            p.avertissements.append("%s joue un %de coup au tour %d (%s) : un coup par camp et par tour"
                                    % (camp, len(deja) + 1, p.tour, coup))
    return refus
