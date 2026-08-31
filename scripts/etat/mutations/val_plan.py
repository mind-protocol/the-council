# -*- coding: utf-8 -*-
"""VAL_PLAN - valider les mutations d'intentions : tetes, etapes, croyances.

Une branche de l'ancien valider() de scripts/appliquer.py (lot 2) : meme code,
meme ordre de refus ; `return CONTINUE` remplace le `continue` d'origine.
"""
import json
from etat.mutations.vocabulaire import (  # noqa: E501
    BUDGETS, CHAMPS_ETAPE, CHAMPS_TETE, CHAMPS_TETE_REQUIS, CONTINUE, ETATS_ETAPE, ETATS_ETAPE_VIVANTS, date_lisible, declencheur_vise, echelle_de, normaliser_date)


def vue_du_lot(projete, cible, tete, liste):
    """La liste telle que LE LOT l'a laissee — jamais l'originale.

    UN RETRAIT ET UN AJOUT SUR LA MEME CLEF, DANS UN MEME LOT, DOIVENT
    S'EVALUER DANS L'ORDRE ECRIT. La validation lisait `tete[liste]` a l'etat
    INITIAL pendant que l'application, elle, s'execute dans l'ordre : un
    `declencheur_retirer` suivi d'un `declencheur_ajouter` sur la meme
    condition se voyait refuser pour une collision qui n'existe qu'entre les
    deux lignes du meme fichier. Consequence mesuree par mj-accalmie le
    129.4.3 : il n'existait AUCUN moyen propre de corriger un declencheur — ni
    operation de modification, ni retrait-puis-ajout —, seulement le
    contournement par changement de libelle.

    La symetrique est du meme bois et tombe avec : un `croyance_ajouter` suivi
    d'un `croyance_retirer` de la meme phrase se voyait refuser « n'a pas cette
    entree ».

    ON NE TOUCHE PAS A LA TABLE : la copie est locale au lot. La validation
    DECRIT, elle n'ecrit rien — sans quoi appliquer() repasserait derriere et
    ajouterait deux fois.
    """
    clef = (cible, liste)
    if clef not in projete:
        projete[clef] = list(tete.get(liste) or [])
    return projete[clef]

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

    if v.get("echelle"):
        return ("`echelle` a ete SUPPRIME du schema (docs/schema.md l.146) : "
                "l'echelle ne se declare plus, elle se mesure sur le quartier. "
                "Retire le champ — les budgets sont pris tout seuls.")
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

    # LES BUDGETS SE PRENNENT SUR L'ECHELLE MESUREE, jamais sur une declaration.
    # Avant le 129.4.4 c'etait `BUDGETS[v["echelle"]]`, et il n'existait AUCUNE
    # valeur qui passe : les trois mots d'ECHELLES levaient KeyError (le lot
    # entier disparaissait sans rapport), les deux vrais mots des BUDGETS
    # etaient refuses par ECHELLES, et l'absence etait refusee par
    # CHAMPS_TETE_REQUIS. Plus personne ne pouvait creer un habitant ACTIF,
    # dans aucune zone — trouve par mj-reposdesfreux, verifie sur les six cas.
    echelle = echelle_de(v)
    budget = BUDGETS[echelle]
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
        return "budget '{}' depasse : {}".format(echelle, " ; ".join(trop))
    return None




def valider_intentions(i, m, op, cible, champs, faute, plan, tetes, personnages, joueur, ids_etapes, projete):
    """Tetes, etapes, croyances. Rend CONTINUE ou (avant, apres).

    `projete` : l'accumulateur du lot, comme `ids_etapes`. Voir vue_du_lot().
    """
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
            # MESUREE, comme le budget juste au-dessus. La tete n'a plus de
            # champ `echelle` : lire v["echelle"] ici levait KeyError APRES une
            # validation reussie — le pire endroit, celui ou le lot s'evanouit
            # alors que rien ne lui a ete reproche.
            "echelle": echelle_de(v),
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
        # AVANT le refus generique : `echelle` sort du vocabulaire, et
        # « champs de tete interdits : echelle » laisserait croire a une faute
        # de frappe. Un champ RETIRE se refuse en disant qu'il a ete retire.
        if "echelle" in champs:
            faute(i, "`echelle` a ete SUPPRIME du schema (docs/schema.md "
                     "l.146) : elle se mesure sur le quartier, elle ne se "
                     "patche plus. Retire le champ.")
            return CONTINUE
        mauvais = [c for c in champs if c not in CHAMPS_TETE]
        if mauvais:
            faute(i, "champs de tete interdits : {}".format(
                ", ".join(mauvais)))
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
        # l'etat PROJETE : ce que les lignes precedentes du lot ont deja fait
        courant = vue_du_lot(projete, cible, tete, "declencheurs")
        if op.endswith("ajouter"):
            if not isinstance(v, dict) or not v.get("si") \
                    or not v.get("alors"):
                faute(i, "declencheur incomplet : 'si' (la condition, "
                         "en clair) et 'alors' (ce qu'il fait) sont "
                         "requis")
                return CONTINUE
            if any(declencheur_vise(d, v["si"]) for d in courant):
                faute(i, "{} a deja un declencheur sur cette "
                         "condition — retire-le d'abord, dans ce lot "
                         "meme si tu veux le remplacer".format(cible))
                return CONTINUE
            courant.append(v)
            apres = {"declencheurs": "+ si " + v["si"][:60]}
        else:
            if not isinstance(v, str) or not any(
                    declencheur_vise(d, v) for d in courant):
                faute(i, "aucun declencheur de {} sur cette condition "
                         "(donne le 'si' exact)".format(cible))
                return CONTINUE
            courant[:] = [d for d in courant if not declencheur_vise(d, v)]
            apres = {"declencheurs": "- si " + v[:60]}
    else:  # croyance_* / ignore_*
        liste = "croyances" if op.startswith("croyance") else "ignore"
        v = m.get("valeur")
        if not isinstance(v, str) or not v.strip():
            faute(i, "valeur textuelle requise")
            return CONTINUE
        courant = vue_du_lot(projete, cible, tete, liste)
        if op.endswith("retirer") and v not in courant:
            faute(i, "{} n'a pas cette entree dans {}".format(cible, liste))
            return CONTINUE
        if op.endswith("ajouter"):
            courant.append(v)
        else:
            courant.remove(v)
        apres = {liste: ("+ " if op.endswith("ajouter") else "- ") + v}

    return avant, apres
