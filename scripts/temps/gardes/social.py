# -*- coding: utf-8 -*-
"""GARDES DU SOCIAL — evenements, personnages, courrier, rumeurs.

CE QUE CE MODULE POSSEDE : les verificateurs de ce qui CIRCULE entre les gens
— les evenements (echeances passees, diffusion en retard, lieux inconnus),
les personnages (lieux qui existent), les plis (ce qui traine, ce qui vole
sans oiseau, ce qui n'a pas de main) et les roukeries, les rumeurs (une chose
ne devient jamais plus vraie en passant de bouche en bouche).

CE QU'IL REFUSE : ecrire, et proposer — la propagation vit dans rumeur.py, ici
on ne fait que constater ce qui cloche.

CONSOMMATEURS : gardes/__init__.py (verifier() les appelle dans l'ordre).
"""
from temps.calendrier import jour_absolu, fmt
from temps.lecture import (CANAUX_PLI, ETATS_PLI, ETATS_PLI_EN_MAIN,
                           TOLERANCE_PLI)
from temps.rumeur import relais_de, rang_certitude, SILENCE_RUMEUR


def verifier_evenements(e, r):
    """Echeances passees, diffusion en retard, lieux inconnus."""
    for ev in e.evenements:
        eid = ev.get("id", "?")
        if ev.get("lieu_id") and not e.lieu(ev["lieu_id"]):
            r.dire("grave", eid, "lieu_id inconnu : {!r}".format(ev["lieu_id"]))

        prevue = jour_absolu(ev.get("date_prevue"))
        if prevue is None:
            r.dire("grave", eid, "date_prevue absente ou illisible")
        elif ev.get("statut") == "a-venir" and prevue < e.aujourdhui:
            r.dire("avertissement", eid,
                   "encore 'a-venir' alors que son echeance {} est passee "
                   "(monde {}) — retard du moteur".format(
                       fmt(ev["date_prevue"]), fmt(e.date)))

        for i, ent in enumerate(ev.get("diffusion") or []):
            etiq = "{} / diffusion #{}".format(eid, i + 1)
            if not isinstance(ent, dict):
                r.dire("grave", etiq, "entree de diffusion illisible")
                continue
            ou, qui = ent.get("ou"), ent.get("qui") or []
            if not ou and not qui:
                r.dire("grave", etiq,
                       "ni 'ou' ni 'qui' — il faut au moins l'un des deux")
            if ou and not e.lieu(ou):
                r.dire("grave", etiq, "'ou' inconnu : {!r}".format(ou))
            for pid in qui:
                if pid not in e.perso_par_id:
                    r.dire("grave", etiq, "'qui' inconnu : {!r}".format(pid))
            quand = jour_absolu(ent.get("date"))
            if quand is None:
                r.dire("grave", etiq, "date absente ou illisible")
            elif quand <= e.aujourdhui and ent.get("livree") is not True:
                r.dire("avertissement", etiq,
                       "nouvelle due le {} et toujours pas livree "
                       "(monde {})".format(fmt(ent["date"]), fmt(e.date)))


def verifier_personnages(e, r):
    for perso in e.personnages:
        lid = perso.get("lieu_id")
        if lid and not e.lieu(lid):
            r.dire("grave", perso.get("id", "?"),
                   "lieu_id inconnu : {!r}".format(lid))


def verifier_plis(e, r):
    """Le courrier : ce qui traine, ce qui vole sans oiseau, ce qui n'a pas de main."""
    vus = set()
    # corbeaux en vol, par (lieu de depart, destination)
    en_vol = {}
    for pli in e.plis:
        pid = pli.get("id")
        etiq = "pli {}".format(pid or "?")
        if not isinstance(pli, dict) or not pid:
            r.dire("grave", etiq, "pli sans id")
            continue
        if pid in vus:
            r.dire("grave", etiq, "id de pli en double")
        vus.add(pid)

        if pli.get("canal") not in CANAUX_PLI:
            r.dire("grave", etiq, "canal {!r} hors {} — la rumeur et le temoin "
                                  "ne sont pas des objets, ils restent a "
                                  "evenements.diffusion".format(pli.get("canal"),
                                                                CANAUX_PLI))
        etat = pli.get("etat")
        if etat not in ETATS_PLI:
            r.dire("grave", etiq, "etat {!r} hors {}".format(etat, ETATS_PLI))
        if not pli.get("porte"):
            r.dire("grave", etiq, "'porte' vide — un pli sans texte fige ne "
                                  "porte rien et ne peut pas arriver perime")
        for champ in ("de", "pour"):
            if pli.get(champ) and pli[champ] not in e.perso_par_id:
                r.dire("grave", etiq, "{} inconnu : {!r}".format(champ,
                                                                 pli[champ]))
        if pli.get("vers") and not e.lieu(pli["vers"]):
            r.dire("grave", etiq, "'vers' inconnu : {!r}".format(pli["vers"]))
        if pli.get("depuis") and not e.lieu(pli["depuis"]):
            r.dire("grave", etiq, "'depuis' inconnu : {!r}".format(pli["depuis"]))
        if pli.get("main") and pli["main"] not in e.perso_par_id:
            r.dire("grave", etiq, "'main' inconnue : {!r}".format(pli["main"]))

        # un pli en main sans main : personne ne l'a, et personne ne l'a lu
        if etat in ETATS_PLI_EN_MAIN and not pli.get("main"):
            r.dire("grave", etiq,
                   "{} sans 'main' — un pli est toujours dans la main de "
                   "quelqu'un ; dis qui l'a".format(etat))
        if etat == "en-route" and pli.get("main"):
            r.dire("avertissement", etiq,
                   "en route et pourtant dans une main ({}) — s'il chemine, "
                   "'main' doit etre null".format(pli["main"]))

        attendu = jour_absolu(pli.get("attendu_le"))
        parti = jour_absolu(pli.get("parti_le"))
        if attendu is None:
            r.dire("grave", etiq, "attendu_le absent ou illisible")
        elif parti is not None and attendu < parti:
            r.dire("grave", etiq, "attendu le {} alors qu'il est parti le {}"
                   .format(fmt(pli["attendu_le"]), fmt(pli["parti_le"])))
        elif etat == "en-route":
            retard = e.aujourdhui - attendu
            if retard > TOLERANCE_PLI:
                r.dire("avertissement", etiq,
                       "toujours en route, attendu le {} il y a {} jours "
                       "(monde {}) — remis, retenu, ou perdu ?".format(
                           fmt(pli["attendu_le"]), retard, fmt(e.date)))

        # les corbeaux : un oiseau ne vole que vers la ou il est ne
        if pli.get("canal") == "corbeau" and etat == "en-route":
            depuis = e.depart_de(pli)
            vers = e.lieu(pli.get("vers"))
            if depuis is None:
                r.dire("avertissement", etiq,
                       "corbeau sans lieu de depart connu (ni 'depuis', ni "
                       "lieu_id lisible pour {!r}) — stock invérifiable"
                       .format(pli.get("de")))
            elif vers:
                en_vol[(depuis, vers)] = en_vol.get((depuis, vers), 0) + 1

    for (depuis, vers), nb in sorted(en_vol.items()):
        stock = e.roukerie(depuis)
        if not stock:
            continue        # roukerie non tenue : on ne reproche rien
        reste = stock.get(vers)
        if reste is None:
            r.dire("avertissement", "roukerie {}".format(depuis),
                   "{} corbeau(x) en vol vers {} alors que la roukerie n'y "
                   "eleve aucun oiseau — un corbeau ne vole que vers la ou il "
                   "est ne".format(nb, vers))
        elif not isinstance(reste, int) or reste < 0:
            r.dire("grave", "roukerie {}".format(depuis),
                   "stock vers {} a {!r} — un envoi de trop a ete consomme"
                   .format(vers, reste))

    for lid, fiche in sorted(e.fiche_lieu.items()):
        stock = fiche.get("roukerie")
        if stock is None:
            continue
        if not isinstance(stock, dict):
            r.dire("grave", "roukerie {}".format(lid),
                   "'roukerie' doit etre un objet {lieu_id: nombre}")
            continue
        for origine, nb in sorted(stock.items()):
            if not e.lieu(origine):
                r.dire("grave", "roukerie {}".format(lid),
                       "lieu d'origine inconnu : {!r}".format(origine))
            if not isinstance(nb, int) or nb < 0:
                r.dire("grave", "roukerie {}".format(lid),
                       "stock vers {} non entier ou negatif : {!r}".format(
                           origine, nb))


def verifier_rumeurs(e, r):
    """Les incidents qui servent de rumeurs. En gravite 'note', jamais bloquant.

    Deux fautes, et ce sont les deux seules qu'une machine sache voir :
    une rumeur qui n'a pas bouge depuis longtemps (elle devrait avancer ou
    s'eteindre), et une fiabilite qui n'a pas decru en se propageant — un fait
    ne devient jamais plus sur en passant de bouche en bouche.
    """
    for inc in e.incidents:
        iid = inc.get("id", "?")
        etiq = "rumeur {}".format(iid)
        if inc.get("ou") and not e.lieu(inc["ou"]):
            r.dire("grave", etiq, "foyer inconnu : {!r}".format(inc["ou"]))

        relais = relais_de(inc)
        dates = [jour_absolu(x.get("date")) for x in relais]
        dates = [d for d in dates if d is not None]
        toleree = SILENCE_RUMEUR.get(inc.get("feu"))
        if toleree is not None and dates:
            silence = e.aujourdhui - max(dates)
            if silence > toleree:
                r.dire("note", etiq,
                       "'{}' et rien de neuf depuis {} jours (tolerance {}) — "
                       "une rumeur avance ou s'eteint ; passe-la en 'couve' ou "
                       "'eteint', ou fais-lui gagner un endroit".format(
                           inc.get("feu"), silence, toleree))

        depart = rang_certitude(inc.get("certitude"))
        for ent in inc.get("propage") or []:
            if not isinstance(ent, dict) or not ent.get("ou"):
                continue
            # Un relais dont le `depuis` nomme QUELQU'UN n'est plus du bouche a
            # oreille : c'est une parole d'autorite, avec un nom dessus — le
            # deuxieme porteur, pas le troisieme. Il n'est donc pas tenu de
            # decroitre. `certitude` mesure la confiance de qui entend, pas la
            # verite : une proclamation fausse peut etre 'rapportee' sans que
            # rien ne cloche.
            if ent.get("depuis") in e.perso_par_id:
                continue
            if ent.get("certitude") is None:
                r.dire("note", etiq,
                       "le relais {} n'a pas de 'certitude' — il herite du foyer "
                       "et la rumeur ne se degrade jamais".format(ent["ou"]))
                continue
            if rang_certitude(ent["certitude"]) >= depart:
                r.dire("note", etiq,
                       "le relais {} est aussi sur ({}) que le foyer ({}) — une "
                       "chose ne devient pas plus vraie en passant de bouche en "
                       "bouche".format(ent["ou"], ent["certitude"],
                                       inc.get("certitude")))
            if not e.lieu(ent["ou"]):
                r.dire("grave", etiq,
                       "relais en lieu inconnu : {!r}".format(ent["ou"]))
