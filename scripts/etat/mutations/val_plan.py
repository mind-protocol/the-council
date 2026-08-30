# -*- coding: utf-8 -*-
"""VAL_PLAN - valider les mutations d'intentions : tetes, etapes, croyances.

Une branche de l'ancien valider() de scripts/appliquer.py (lot 2) : meme code,
meme ordre de refus ; `return CONTINUE` remplace le `continue` d'origine.
"""
import json
from etat.mutations.vocabulaire import (  # noqa: E501
    BUDGETS, CHAMPS_ETAPE, CHAMPS_TETE, CHAMPS_TETE_REQUIS, CONTINUE, ECHELLES, ETATS_ETAPE, ETATS_ETAPE_VIVANTS, date_lisible, normaliser_date)

def valider_tete_neuve(v, cible, tetes, personnages, joueur, ids_etapes):
    """Une tete neuve est-elle recevable ? Rend un message, ou None si oui.

    Tout est verifie ici : rien n'est ecrit avant que le lot entier passe.
    """
    if not isinstance(v, dict):
        return "tete a ajouter : 'valeur' doit etre l'objet intention complet"
    manquants = [c for c in CHAMPS_TETE_REQUIS if not v.get(c)]
    if manquants:
        return "tete a ajouter incomplete, il manque : {}".format(
            ", ".join(manquants))

    pid = v["personnage_id"]
    if cible is not None and cible != pid:
        return ("'cible' {!r} ne correspond pas au personnage_id {!r} de la "
                "tete".format(cible, pid))
    if pid in tetes:
        return ("une tete existe deja pour {} — patche-la (tete, etape, "
                "croyance_ajouter), ne la recree pas".format(pid))
    if pid not in personnages:
        return "personnage inconnu de personnages.json : {!r}".format(pid)
    if joueur and pid == joueur:
        return ("{} est le personnage joueur — sa tete appartient au joueur et "
                "n'a jamais d'entree dans intentions.json".format(pid))

    if v["echelle"] not in ECHELLES:
        return "echelle {!r} hors {}".format(v["echelle"], ECHELLES)
    if not date_lisible(v["date_maj"]):
        return "date_maj illisible (attendu {annee, lune, jour} d'entiers)"
    for liste in ("croyances", "ignore"):
        if v.get(liste) is not None and not isinstance(v.get(liste), list):
            return "{} doit etre une liste".format(liste)
    if not isinstance(v["plan"], list):
        return "plan doit etre une liste d'etapes"

    vus = set()
    for etape in v["plan"]:
        if not isinstance(etape, dict):
            return ("plan : etape en simple texte — il faut un objet horloge "
                    "(id, quoi, etat, jours_restants)")
        eid = etape.get("id")
        if not eid or not etape.get("quoi"):
            return "plan : etape sans id ou sans quoi"
        if eid in ids_etapes or eid in vus:
            return "id d'etape deja pris : {}".format(eid)
        vus.add(eid)
        if etape.get("etat") not in ETATS_ETAPE:
            return "etape {} : etat {!r} hors {}".format(
                eid, etape.get("etat"), ETATS_ETAPE)
        if "jours_restants" not in etape:
            return ("etape {} : jours_restants requis (entier, ou null pour "
                    "une posture permanente)".format(eid))
        jr = etape["jours_restants"]
        if jr is not None and not isinstance(jr, int):
            return "etape {} : jours_restants doit etre un entier ou null".format(
                eid)

    decl = v.get("declencheurs") or []
    if not isinstance(decl, list):
        return "declencheurs doit etre une liste"
    for d in decl:
        if not isinstance(d, dict) or not d.get("si") or not d.get("alors"):
            return "declencheur sans 'si' ou sans 'alors'"

    # budgets de l'echelle — la table est dans docs/schema.md
    budget = BUDGETS[v["echelle"]]
    trop = []
    n_croyances = len(v.get("croyances") or [])
    if n_croyances > budget["croyances"]:
        trop.append("{} croyances pour {}".format(n_croyances,
                                                  budget["croyances"]))
    vivantes = [e for e in v["plan"] if e.get("etat") in ETATS_ETAPE_VIVANTS]
    if len(vivantes) > budget["etapes"]:
        trop.append("{} etapes vivantes pour {}".format(len(vivantes),
                                                        budget["etapes"]))
    if len(decl) > budget["declencheurs"]:
        trop.append("{} declencheurs pour {}".format(len(decl),
                                                     budget["declencheurs"]))
    if trop:
        return "budget '{}' depasse : {}".format(v["echelle"], " ; ".join(trop))
    return None




def valider_intentions(i, m, op, cible, champs, faute, plan, tetes, personnages, joueur, ids_etapes):
    """Tetes, etapes, croyances. Rend CONTINUE ou (avant, apres)."""
    avant, apres = None, None
    if op == "tete_ajouter":
        v = m.get("valeur")
        souci = valider_tete_neuve(v, cible, tetes, personnages,
                                   joueur, ids_etapes)
        if souci:
            faute(i, souci)
            return CONTINUE
        # la tete neuve devient patchable par la suite du meme lot
        tetes[v["personnage_id"]] = v
        ids_etapes.update(e["id"] for e in v["plan"])
        plan.append({"n": i, "mutation": m, "avant": None, "apres": {
            "tete_ajoutee": v["personnage_id"],
            "echelle": v["echelle"],
            "croyances": len(v.get("croyances") or []),
            "etapes": len(v["plan"]),
            "declencheurs": len(v.get("declencheurs") or []),
        }})
        return CONTINUE
    tete = tetes.get(cible)
    if tete is None:
        faute(i, "aucune tete pour {!r}".format(cible))
        return CONTINUE
    if op == "etape":
        etapes = {e.get("id"): e for e in (tete.get("plan") or [])
                  if isinstance(e, dict)}
        etape = etapes.get(m.get("etape"))
        if etape is None:
            faute(i, "{} n'a pas d'etape {!r}".format(
                cible, m.get("etape")))
            return CONTINUE
        mauvais = [c for c in champs if c not in CHAMPS_ETAPE]
        if mauvais:
            faute(i, "champs d'etape interdits : {}".format(
                ", ".join(mauvais)))
            return CONTINUE
        if "etat" in champs and champs["etat"] not in ETATS_ETAPE:
            faute(i, "etat d'etape {!r} hors {}".format(
                champs["etat"], ETATS_ETAPE))
            return CONTINUE
        if "jours_restants" in champs:
            jr = champs["jours_restants"]
            if jr is not None and not isinstance(jr, int):
                faute(i, "jours_restants doit etre un entier ou null")
                return CONTINUE
        avant = {c: etape.get(c) for c in champs}
        apres = dict(champs)
    elif op == "etape_ajouter":
        v = m.get("valeur")
        if not isinstance(v, dict) or not v.get("id") or not v.get("quoi"):
            faute(i, "etape a ajouter incomplete (id et quoi requis)")
            return CONTINUE
        if v["id"] in ids_etapes:
            faute(i, "id d'etape deja pris : {}".format(v["id"]))
            return CONTINUE
        ids_etapes.add(v["id"])
        apres = {"etape_ajoutee": v["id"]}
    elif op == "tete":
        mauvais = [c for c in champs if c not in CHAMPS_TETE]
        if mauvais:
            faute(i, "champs de tete interdits : {}".format(
                ", ".join(mauvais)))
            return CONTINUE
        if "echelle" in champs and champs["echelle"] not in ECHELLES:
            faute(i, "echelle {!r} hors {}".format(
                champs["echelle"], ECHELLES))
            return CONTINUE
        if "date_maj" in champs:
            propre = normaliser_date(champs["date_maj"])
            if propre is None:
                faute(i, "date_maj illisible : {!r} (attendu "
                         "{{annee, lune, jour}} d'entiers)".format(
                             champs["date_maj"]))
                return CONTINUE
            champs["date_maj"] = propre
        avant = {c: tete.get(c) for c in champs}
        apres = dict(champs)
    elif op.startswith("declencheur"):
        v = m.get("valeur")
        courant = tete.get("declencheurs") or []
        if op.endswith("ajouter"):
            if not isinstance(v, dict) or not v.get("si") \
                    or not v.get("alors"):
                faute(i, "declencheur incomplet : 'si' (la condition, "
                         "en clair) et 'alors' (ce qu'il fait) sont "
                         "requis")
                return CONTINUE
            if any(d.get("si") == v["si"] for d in courant
                   if isinstance(d, dict)):
                faute(i, "{} a deja un declencheur sur cette "
                         "condition".format(cible))
                return CONTINUE
            apres = {"declencheurs": "+ si " + v["si"][:60]}
        else:
            if not isinstance(v, str) or not any(
                    d.get("si") == v for d in courant
                    if isinstance(d, dict)):
                faute(i, "aucun declencheur de {} sur cette condition "
                         "(donne le 'si' exact)".format(cible))
                return CONTINUE
            apres = {"declencheurs": "- si " + v[:60]}
    else:  # croyance_* / ignore_*
        liste = "croyances" if op.startswith("croyance") else "ignore"
        v = m.get("valeur")
        if not isinstance(v, str) or not v.strip():
            faute(i, "valeur textuelle requise")
            return CONTINUE
        courant = tete.get(liste) or []
        if op.endswith("retirer") and v not in courant:
            faute(i, "{} n'a pas cette entree dans {}".format(cible, liste))
            return CONTINUE
        apres = {liste: ("+ " if op.endswith("ajouter") else "- ") + v}

    return avant, apres
