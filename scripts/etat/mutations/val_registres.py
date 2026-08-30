# -*- coding: utf-8 -*-
"""VAL_REGISTRES - valider les mutations des books (affaires) et des mains.

Deux branches de l'ancien valider() de scripts/appliquer.py (lot 2) : meme
code, meme ordre de refus ; `return CONTINUE` remplace le `continue`.
"""
from etat.mutations.vocabulaire import (  # noqa: E501
    CHAMPS_MAIN, CHAMPS_MAIN_REQUIS, CHAMPS_MESURE, CHAMPS_SEUIL, CONTINUE, ECHELLES, TYPES_PORTEUR, liste_books, prochaine_ligne_action, table_actions)
from etat.expose import tables as porte  # LA PORTE de etat/

def valider_books(i, m, op, cible, champs, faute, plan, tables):
    """Les affaires des books. Rend CONTINUE (gere) ou (avant, apres)."""
    avant, apres = None, None
    livres = liste_books(tables)
    par_livre = {x.get("id"): x for x in livres if isinstance(x, dict)}
    if op == "affaire_ajouter":
        v = m.get("valeur") or {}
        if not str(cible or "").startswith("affaire-"):
            faute(i, "une affaire neuve a un id prefixe `affaire-`")
            return CONTINUE
        if cible in par_livre:
            faute(i, "l'affaire {!r} existe deja".format(cible))
            return CONTINUE
        if not str(v.get("titre") or "").strip():
            faute(i, "une affaire neuve doit porter un titre")
            return CONTINUE
        par_livre[cible] = {"id": cible}  # le lot suivant peut la viser
        plan.append({"n": i, "mutation": m, "avant": None,
                     "apres": {"affaire_ouverte": cible,
                               "titre": v["titre"]}})
        return CONTINUE
    livre = par_livre.get(str(cible or "").split(":")[0])
    if livre is None:
        faute(i, "affaire inconnue : {!r}".format(cible))
        return CONTINUE
    actions = table_actions(livre)
    if actions is None:
        faute(i, "l'affaire {!r} n'a pas de table d'actions"
              .format(livre.get("id")))
        return CONTINUE
    colonnes = actions.get("colonnes") or []
    if op == "affaire_action_ajouter":
        cellules = m.get("valeur")
        if not isinstance(cellules, list) or len(cellules) != len(colonnes):
            faute(i, "une action prend exactement {} cellules, {} recues"
                  .format(len(colonnes),
                          len(cellules) if isinstance(cellules, list)
                          else "aucune"))
            return CONTINUE
        plan.append({"n": i, "mutation": m, "avant": None,
                     "apres": {"action_ajoutee": livre.get("id"),
                               "quoi": str(cellules[1])[:60]}})
        return CONTINUE
    if op == "affaire_action":
        numero = str(cible or "").partition(":")[2]
        ligne = prochaine_ligne_action(actions, numero)
        if ligne is None:
            faute(i, "action {!r} introuvable dans {}"
                  .format(numero, livre.get("id")))
            return CONTINUE
        inconnues = [c for c in champs if c not in colonnes]
        if inconnues:
            faute(i, "colonne inconnue : {}".format(", ".join(inconnues)))
            return CONTINUE
        if not champs:
            faute(i, "aucune colonne a modifier")
            return CONTINUE
        plan.append({"n": i, "mutation": m,
                     "avant": {c: ligne["cellules"][colonnes.index(c)]
                               for c in champs},
                     "apres": dict(champs)})
        return CONTINUE

    return avant, apres


def valider_mains(i, m, op, cible, champs, faute, plan, personnages, mains, lieux, maisons):
    """Les mains : mesures, seuils, ajouts. Rend CONTINUE ou (avant, apres)."""
    avant, apres = None, None
    if op == "main_ajouter":
        v = m.get("valeur")
        if not isinstance(v, dict):
            faute(i, "main a ajouter : 'valeur' doit etre l'objet main")
            return CONTINUE
        manquants = [c for c in CHAMPS_MAIN_REQUIS if not v.get(c)]
        if manquants:
            faute(i, "main a ajouter incomplete, il manque : {}".format(
                ", ".join(manquants)))
            return CONTINUE
        if cible is not None and cible != v["id"]:
            faute(i, "'cible' {!r} ne correspond pas a l'id {!r}".format(
                cible, v["id"]))
            return CONTINUE
        if v["id"] in mains:
            faute(i, "une main {} existe deja — patche-la".format(v["id"]))
            return CONTINUE
        porteur = v["porteur"]
        if not isinstance(porteur, dict) or \
                porteur.get("type") not in TYPES_PORTEUR:
            faute(i, "porteur.type hors {}".format(TYPES_PORTEUR))
            return CONTINUE
        tables_porteur = {"personnage": personnages, "maison": maisons,
                          "lieu": lieux}[porteur["type"]]
        if porteur.get("id") is not None \
                and porteur["id"] not in tables_porteur:
            faute(i, "porteur {} inconnu : {!r} — une affaire sans "
                     "porteur s'ecrit id: null, pas avec un nom "
                     "faux".format(porteur["type"], porteur["id"]))
            return CONTINUE
        if v["lieu_id"] not in lieux:
            faute(i, "lieu_id inconnu : {!r}".format(v["lieu_id"]))
            return CONTINUE
        mesures = v.get("mesure")
        if not isinstance(mesures, list) or not 1 <= len(mesures) <= 3:
            faute(i, "une main porte 1 a 3 mesures, jamais plus "
                     "(docs/schema.md)")
            return CONTINUE
        souci = None
        vus = set()
        for mes in mesures:
            if not isinstance(mes, dict) or not mes.get("id") \
                    or not mes.get("quoi"):
                souci = "mesure incomplete (id et quoi requis)"
            elif mes["id"] in vus:
                souci = "id de mesure double : {}".format(mes["id"])
            elif not isinstance(mes.get("valeur"), int) \
                    or isinstance(mes.get("valeur"), bool):
                souci = ("mesure {} : 'valeur' doit etre un entier — "
                         "les mains ne connaissent pas les "
                         "flottants".format(mes["id"]))
            else:
                rythme = mes.get("rythme")
                if not isinstance(rythme, dict) or \
                        not isinstance(rythme.get("par"), int):
                    souci = ("mesure {} : rythme.par entier requis, "
                             "sinon la mesure ne bougera jamais et "
                             "la main est morte".format(mes["id"]))
                elif not isinstance(rythme.get("jours", 1), int) \
                        or rythme.get("jours", 1) < 1:
                    souci = ("mesure {} : rythme.jours doit etre un "
                             "entier > 0".format(mes["id"]))
            if souci:
                break
            vus.add(mes["id"])
        if souci:
            faute(i, souci)
            return CONTINUE
        for s in (v.get("seuils") or []):
            if not isinstance(s, dict) or s.get("mesure_id") not in vus:
                souci = ("seuil {!r} : mesure_id absent de cette "
                         "main".format(
                             (s or {}).get("id") if isinstance(s, dict)
                             else s))
                break
            if s.get("promeut") and s["promeut"] not in ECHELLES:
                souci = "seuil {} : promeut {!r} hors {}".format(
                    s.get("id"), s["promeut"], ECHELLES)
                break
        if souci:
            faute(i, souci)
            return CONTINUE
        mains[v["id"]] = v
        plan.append({"n": i, "mutation": m, "avant": None, "apres": {
            "main_ajoutee": v["id"],
            "porteur": porteur.get("id"),
            "mesures": [x["id"] for x in mesures],
            "seuils": len(v.get("seuils") or []),
        }})
        return CONTINUE
    act = mains.get(cible)
    if act is None:
        faute(i, "aucune main {!r}".format(cible))
        return CONTINUE
    if op == "mesure":
        mes = next((x for x in (act.get("mesure") or [])
                    if x.get("id") == m.get("mesure")), None)
        if mes is None:
            faute(i, "aucune mesure {!r} dans {}".format(
                m.get("mesure"), cible))
            return CONTINUE
        mauvais = [c for c in champs if c not in CHAMPS_MESURE]
        if mauvais:
            faute(i, "champs de mesure interdits : {} (seuls {} se "
                     "posent par mutation)".format(
                         ", ".join(mauvais), "/".join(CHAMPS_MESURE)))
            return CONTINUE
        pasentier = [c for c in champs
                     if not isinstance(champs[c], int)]
        if pasentier:
            faute(i, "{} doit etre un entier — les mains ne "
                     "connaissent pas les flottants".format(
                         ", ".join(pasentier)))
            return CONTINUE
        avant = {c: mes.get(c) for c in champs}
        apres = dict(champs)
    elif op == "seuil":
        seuil = next((s for s in (act.get("seuils") or [])
                      if s.get("id") == m.get("seuil")), None)
        if seuil is None:
            faute(i, "aucun seuil {!r} dans {}".format(
                m.get("seuil"), cible))
            return CONTINUE
        mauvais = [c for c in champs if c not in CHAMPS_SEUIL]
        if mauvais:
            faute(i, "champs de seuil interdits : {}".format(
                ", ".join(mauvais)))
            return CONTINUE
        avant = {c: seuil.get(c) for c in champs}
        apres = dict(champs)
    else:
        mauvais = [c for c in champs if c not in CHAMPS_MAIN]
        if mauvais:
            faute(i, "champs d'main interdits : {}".format(
                ", ".join(mauvais)))
            return CONTINUE
        avant = {c: act.get(c) for c in champs}
        apres = dict(champs)

    return avant, apres
