# -*- coding: utf-8 -*-
"""VAL_SOCIAL - valider evenements, personnages, relations et monde.

Quatre branches de l'ancien valider() de scripts/appliquer.py (lot 2) : meme
code, meme ordre de refus ; `return CONTINUE` remplace le `continue`.
"""
import json
from etat.mutations.vocabulaire import (  # noqa: E501
    CHAMPS_EVENEMENT, CHAMPS_MONDE, CHAMPS_PERSO, CHAMPS_PERSO_REQUIS, CHAMPS_RELATION, CONTINUE, ETATS_PERSO, STATUTS_EVENEMENT, charge_relation)

def valider_evenements(i, m, op, cible, champs, faute, evenements):
    """Statut, effets, diffusion. Rend CONTINUE ou (avant, apres)."""
    avant, apres = None, None
    ev = evenements.get(cible)
    if ev is None:
        faute(i, "aucun evenement {!r}".format(cible))
        return CONTINUE
    if op == "diffusion_livree":
        diff = ev.get("diffusion") or []
        idx = m.get("index")
        if not isinstance(idx, int) or not 0 <= idx < len(diff):
            faute(i, "index de diffusion hors bornes : {!r}".format(idx))
            return CONTINUE
        if diff[idx].get("livree") is True:
            faute(i, "diffusion {} de {} deja livree".format(idx, cible))
            return CONTINUE
        apres = {"diffusion[{}].livree".format(idx): True}
    elif op == "diffusion_ajouter":
        v = m.get("valeur")
        if not isinstance(v, dict) or not v.get("date") \
                or not (v.get("ou") or v.get("qui")):
            faute(i, "diffusion a ajouter incomplete (date, et ou/qui)")
            return CONTINUE
        apres = {"diffusion": "+1 entree le {}".format(
            v["date"].get("jour"))}
    else:  # evenement
        mauvais = [c for c in champs if c not in CHAMPS_EVENEMENT]
        if mauvais:
            faute(i, "champs d'evenement interdits : {}".format(
                ", ".join(mauvais)))
            return CONTINUE
        if "statut" in champs and champs["statut"] not in STATUTS_EVENEMENT:
            faute(i, "statut {!r} hors {}".format(
                champs["statut"], STATUTS_EVENEMENT))
            return CONTINUE
        avant = {c: ev.get(c) for c in champs}
        apres = dict(champs)

    return avant, apres


def valider_personnages(i, m, op, cible, champs, faute, plan, mutations, tetes, personnages, lieux, maisons):
    """Fiches de personnages. Rend CONTINUE ou (avant, apres)."""
    avant, apres = None, None
    if op == "personnage_ajouter":
        v = m.get("valeur")
        if not isinstance(v, dict):
            faute(i, "personnage a ajouter : 'valeur' doit etre la fiche")
            return CONTINUE
        manquants = [c for c in CHAMPS_PERSO_REQUIS if not v.get(c)]
        if manquants:
            faute(i, "fiche incomplete, il manque : {}".format(
                ", ".join(manquants)))
            return CONTINUE
        if cible is not None and cible != v["id"]:
            faute(i, "'cible' {!r} ne correspond pas a l'id {!r}".format(
                cible, v["id"]))
            return CONTINUE
        if v["id"] in personnages:
            faute(i, "un personnage {} existe deja — patche-le".format(
                v["id"]))
            return CONTINUE
        if v["etat"] not in ETATS_PERSO:
            faute(i, "etat {!r} hors {}".format(v["etat"], ETATS_PERSO))
            return CONTINUE
        if v.get("lieu_id") and v["lieu_id"] not in lieux:
            faute(i, "lieu_id inconnu : {!r}".format(v["lieu_id"]))
            return CONTINUE
        if v.get("maison_id") and maisons and \
                v["maison_id"] not in maisons:
            faute(i, "maison_id inconnue : {!r}".format(v["maison_id"]))
            return CONTINUE
        # un homme qu'on cree actif doit avoir de quoi agir : c'est la
        # regle du casting dynamique, et tick.py --verifier la dira de
        # toute facon. Autant la dire ici, avant l'ecriture.
        if v["etat"] == "actif" and v["id"] not in tetes and \
                not any(mm.get("table") == "intentions"
                        and mm.get("operation") == "tete_ajouter"
                        and (mm.get("valeur") or {}).get(
                            "personnage_id") == v["id"]
                        for mm in mutations):
            faute(i, "{} est cree 'actif' sans tete dans ce lot : "
                     "donne-lui une entree dans intentions.json, ou "
                     "cree-le dormant".format(v["id"]))
            return CONTINUE
        personnages[v["id"]] = v
        plan.append({"n": i, "mutation": m, "avant": None, "apres": {
            "personnage_ajoute": v["id"],
            "nom": v.get("nom"),
            "etat": v["etat"],
            "lieu_id": v.get("lieu_id"),
        }})
        return CONTINUE
    perso = personnages.get(cible)
    if perso is None:
        faute(i, "aucun personnage {!r}".format(cible))
        return CONTINUE
    mauvais = [c for c in champs if c not in CHAMPS_PERSO]
    if mauvais:
        faute(i, "champs de personnage interdits : {}".format(
            ", ".join(mauvais)))
        return CONTINUE
    if "etat" in champs and champs["etat"] not in ETATS_PERSO:
        faute(i, "etat {!r} hors {}".format(champs["etat"], ETATS_PERSO))
        return CONTINUE
    avant = {c: perso.get(c) for c in champs}
    apres = dict(champs)

    return avant, apres


def valider_relations(i, m, op, champs, faute, plan, personnages, couples):
    """Relations orientees. Rend CONTINUE ou (avant, apres)."""
    avant, apres = None, None
    v = charge_relation(m, op, champs)
    source = m.get("source_id") or (v or {}).get("source_id")
    cible_r = m.get("cible_id") or (v or {}).get("cible_id")
    if not source or not cible_r:
        faute(i, "relation : 'source_id' et 'cible_id' requis — une "
                 "relation n'a pas d'id, elle se designe par le couple")
        return CONTINUE
    inconnu = [x for x in (source, cible_r) if x not in personnages]
    if inconnu:
        faute(i, "personnage inconnu : {}".format(", ".join(inconnu)))
        return CONTINUE
    if source == cible_r:
        faute(i, "une relation de {} vers lui-meme".format(source))
        return CONTINUE
    existante = couples.get((source, cible_r))
    if op == "relation_ajouter":
        if existante is not None:
            faute(i, "une relation {} -> {} existe deja — "
                     "patche-la".format(source, cible_r))
            return CONTINUE
        if not isinstance(v, dict):
            faute(i, "'valeur' doit etre l'objet relation")
            return CONTINUE
    else:
        if existante is None:
            faute(i, "aucune relation {} -> {} — la direction compte, "
                     "verifie le sens".format(source, cible_r))
            return CONTINUE
    mauvais = [c for c in (v or {})
               if c not in CHAMPS_RELATION + ("source_id", "cible_id")]
    if mauvais:
        faute(i, "champs de relation interdits : {}".format(
            ", ".join(mauvais)))
        return CONTINUE
    if "opinion" in (v or {}):
        o = v["opinion"]
        if not isinstance(o, int) or isinstance(o, bool) \
                or not -100 <= o <= 100:
            faute(i, "opinion : entier de -100 a +100, {!r} recu".format(o))
            return CONTINUE
    if "liens" in (v or {}) and not isinstance(v["liens"], list):
        faute(i, "liens : une liste")
        return CONTINUE
    if op == "relation_ajouter":
        couples[(source, cible_r)] = v
        plan.append({"n": i, "mutation": m, "avant": None, "apres": {
            "relation_ajoutee": "{} -> {}".format(source, cible_r),
            "opinion": v.get("opinion"),
            "liens": v.get("liens"),
        }})
        return CONTINUE
    avant = {c: existante.get(c) for c in champs}
    apres = dict(champs)

    return avant, apres


def valider_monde(i, champs, faute, tables):
    """La table monde. Rend CONTINUE ou (avant, apres)."""
    avant, apres = None, None
    mauvais = [c for c in champs if c not in CHAMPS_MONDE]
    if mauvais:
        faute(i, "champs de monde interdits : {}".format(
            ", ".join(mauvais)))
        return CONTINUE
    avant = {c: tables["monde"].get(c) for c in champs}
    apres = dict(champs)
    return avant, apres
