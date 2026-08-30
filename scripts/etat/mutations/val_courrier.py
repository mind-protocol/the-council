# -*- coding: utf-8 -*-
"""VAL_COURRIER - valider plis (courrier), jetons (rumeur), lieux (roukerie).

Trois branches de l'ancien valider() de scripts/appliquer.py (lot 2) : meme
code, meme ordre de refus ; `return CONTINUE` remplace le `continue`.
"""
import json
from etat.mutations.vocabulaire import (  # noqa: E501
    CANAUX_PLI, CERTITUDES, CHAMPS_INCIDENT, CHAMPS_PLI, CHAMPS_PLI_REQUIS, CHAMPS_PROPAGE_REQUIS, CONTINUE, ETATS_PLI, ETATS_PLI_EN_MAIN, FEUX, date_lisible, rang_certitude)

def valider_plis(i, m, op, cible, champs, faute, plan, personnages, plis, lieux, relations):
    """Le courrier. Rend CONTINUE ou (avant, apres)."""
    avant, apres = None, None
    if op == "pli_ajouter":
        # Meme tolerance que pour les relations, et pour la meme
        # raison mesuree : l'objet arrive dans `champs` aussi souvent
        # que dans `valeur`, et le refuser perd un pli entier.
        v = m.get("valeur")
        if not isinstance(v, dict) and isinstance(champs, dict) and champs:
            v = champs
            m["valeur"] = champs
        if not isinstance(v, dict):
            faute(i, "pli a ajouter : 'valeur' doit etre l'objet pli")
            return CONTINUE
        manquants = [c for c in CHAMPS_PLI_REQUIS if not v.get(c)]
        if manquants:
            faute(i, "pli a ajouter incomplet, il manque : {}".format(
                ", ".join(manquants)))
            return CONTINUE
        if cible is not None and cible != v["id"]:
            faute(i, "'cible' {!r} ne correspond pas a l'id {!r}".format(
                cible, v["id"]))
            return CONTINUE
        if v["id"] in plis:
            faute(i, "un pli {} existe deja — patche-le".format(v["id"]))
            return CONTINUE
        if v["canal"] not in CANAUX_PLI:
            faute(i, "canal {!r} hors {}".format(v["canal"], CANAUX_PLI))
            return CONTINUE
        if v["etat"] not in ETATS_PLI:
            faute(i, "etat {!r} hors {}".format(v["etat"], ETATS_PLI))
            return CONTINUE
        for champ in ("de", "pour"):
            if v[champ] not in personnages:
                faute(i, "{} inconnu : {!r}".format(champ, v[champ]))
                break
        else:
            if v["vers"] not in lieux:
                faute(i, "'vers' inconnu : {!r}".format(v["vers"]))
                return CONTINUE
            if v.get("depuis") and v["depuis"] not in lieux:
                faute(i, "'depuis' inconnu : {!r}".format(v["depuis"]))
                return CONTINUE
            if not date_lisible(v["parti_le"]) or \
                    not date_lisible(v["attendu_le"]):
                faute(i, "parti_le / attendu_le illisibles (attendu "
                         "{annee, lune, jour} d'entiers)")
                return CONTINUE
            if v["etat"] in ETATS_PLI_EN_MAIN and not v.get("main"):
                faute(i, "un pli {} doit avoir une 'main' : dis qui "
                         "l'a".format(v["etat"]))
                return CONTINUE
            if v.get("main") and v["main"] not in personnages:
                faute(i, "'main' inconnue : {!r}".format(v["main"]))
                return CONTINUE
            plis[v["id"]] = v
            plan.append({"n": i, "mutation": m, "avant": None,
                         "apres": {"pli_ajoute": v["id"],
                                   "vers": v["vers"],
                                   "attendu_le": v["attendu_le"]}})
        return CONTINUE
    pli = plis.get(cible)
    if pli is None:
        faute(i, "aucun pli {!r}".format(cible))
        return CONTINUE
    mauvais = [c for c in champs if c not in CHAMPS_PLI]
    if mauvais:
        faute(i, "champs de pli interdits : {}".format(
            ", ".join(mauvais)))
        return CONTINUE
    if "etat" in champs and champs["etat"] not in ETATS_PLI:
        faute(i, "etat {!r} hors {}".format(champs["etat"], ETATS_PLI))
        return CONTINUE
    if "canal" in champs and champs["canal"] not in CANAUX_PLI:
        faute(i, "canal {!r} hors {}".format(champs["canal"], CANAUX_PLI))
        return CONTINUE
    if "main" in champs and champs["main"] is not None \
            and champs["main"] not in personnages:
        faute(i, "'main' inconnue : {!r}".format(champs["main"]))
        return CONTINUE
    if "attendu_le" in champs and not date_lisible(champs["attendu_le"]):
        faute(i, "attendu_le illisible")
        return CONTINUE
    # un pli en main doit avoir une main, apres coup comme avant
    etat_apres = champs.get("etat", pli.get("etat"))
    main_apres = champs.get("main", pli.get("main"))
    if etat_apres in ETATS_PLI_EN_MAIN and not main_apres:
        faute(i, "{} sans 'main' — un pli est toujours dans la main de "
                 "quelqu'un, et ce n'est pas forcement le 'pour'"
                 .format(etat_apres))
        return CONTINUE
    avant = {c: pli.get(c) for c in champs}
    apres = dict(champs)

    return avant, apres


def valider_jetons(i, m, op, cible, champs, faute, incidents, lieux):
    """Les incidents (la rumeur). Rend CONTINUE ou (avant, apres)."""
    avant, apres = None, None
    inc = incidents.get(cible)
    if inc is None:
        faute(i, "aucun incident {!r} dans jetons.json (genre "
                 "'incident')".format(cible))
        return CONTINUE
    if op == "incident":
        mauvais = [c for c in champs if c not in CHAMPS_INCIDENT]
        if mauvais:
            faute(i, "champs d'incident interdits : {}".format(
                ", ".join(mauvais)))
            return CONTINUE
        if "feu" in champs and champs["feu"] not in FEUX:
            faute(i, "feu {!r} hors {}".format(champs["feu"], FEUX))
            return CONTINUE
        if "certitude" in champs and champs["certitude"] not in CERTITUDES:
            faute(i, "certitude {!r} hors {}".format(
                champs["certitude"], CERTITUDES))
            return CONTINUE
        avant = {c: inc.get(c) for c in champs}
        apres = dict(champs)
    else:   # incident_propage
        v = m.get("valeur")
        if not isinstance(v, dict):
            faute(i, "'valeur' doit etre l'endroit gagne")
            return CONTINUE
        manquants = [c for c in CHAMPS_PROPAGE_REQUIS if not v.get(c)]
        if manquants:
            faute(i, "saut incomplet, il manque : {} — 'contenu' est ce "
                     "qui se dit LA-BAS, deforme, et c'est a toi de "
                     "l'ecrire".format(", ".join(manquants)))
            return CONTINUE
        if v["ou"] not in lieux:
            faute(i, "lieu inconnu : {!r}".format(v["ou"]))
            return CONTINUE
        if not date_lisible(v["date"]):
            faute(i, "date illisible")
            return CONTINUE
        if v["certitude"] not in CERTITUDES:
            faute(i, "certitude {!r} hors {}".format(v["certitude"],
                                                     CERTITUDES))
            return CONTINUE
        if rang_certitude(v["certitude"]) >= rang_certitude(
                inc.get("certitude")):
            faute(i, "certitude {!r} pas moins sure que le foyer ({!r}) "
                     "— rien ne devient plus vrai en se repetant".format(
                         v["certitude"], inc.get("certitude")))
            return CONTINUE
        deja = [x.get("ou") if isinstance(x, dict) else x
                for x in (inc.get("propage") or [])]
        if v["ou"] in deja:
            faute(i, "{} a deja pris pour cet incident".format(v["ou"]))
            return CONTINUE
        apres = {"propage": "+ {} ({}) le {}".format(
            v["ou"], v["certitude"], v["date"].get("jour"))}

    return avant, apres


def valider_lieux(i, cible, champs, faute, lieux):
    """La roukerie, et rien d'autre. Rend CONTINUE ou (avant, apres)."""
    avant, apres = None, None
    lieu = lieux.get(cible)
    if lieu is None:
        faute(i, "aucun lieu {!r}".format(cible))
        return CONTINUE
    if not champs:
        faute(i, "roukerie : aucun champ — rien a poser")
        return CONTINUE
    souci = None
    for origine, nb in champs.items():
        if origine not in lieux:
            souci = "lieu d'origine inconnu : {!r}".format(origine)
        elif not isinstance(nb, int) or isinstance(nb, bool) or nb < 0:
            souci = ("stock vers {} : entier positif attendu, {!r} "
                     "recu".format(origine, nb))
        if souci:
            break
    if souci:
        faute(i, souci)
        return CONTINUE
    stock = lieu.get("roukerie") or {}
    avant = {c: stock.get(c) for c in champs}
    apres = dict(champs)

    return avant, apres
