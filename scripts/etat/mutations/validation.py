# -*- coding: utf-8 -*-
"""VALIDATION - valider(), le cadre : indexes, dispatch par table, plan/erreurs.

L'ancien valider() de scripts/appliquer.py (lot 2), la boucle et ses gardes
communes ; chaque table est validee par sa branche, devenue fonction dans
val_plan / val_registres / val_courrier / val_social. Une branche rend la
sentinelle CONTINUE (mutation traitee : faute ou plan) ou (avant, apres) pour
le plan.append commun. Rien n'est ecrit ici : le plan DECRIT, il ne change rien.
"""
from etat.mutations.val_plan import valider_intentions
from etat.mutations.val_registres import valider_books, valider_mains
from etat.mutations.val_courrier import valider_plis, valider_jetons, valider_lieux
from etat.mutations.val_social import (valider_evenements, valider_personnages,
                                       valider_relations, valider_monde)
from etat.mutations.vocabulaire import (  # noqa: E501
    CONTINUE, OPERATIONS, liste_jetons, liste_simple)
from etat.mutations.lecture import liste_mains, liste_plis, par_id

def valider(mutations, tables):
    """Rend (plan, erreurs). Le plan decrit ce qui changerait, sans rien changer."""
    plan, erreurs = [], []
    tetes = par_id(tables["intentions"], "personnage_id")
    evenements = par_id(tables["evenements"])
    personnages = par_id(tables["personnages"])
    mains = par_id(liste_mains(tables["mains"]))
    plis = par_id(liste_plis(tables["plis"]))
    incidents = par_id([j for j in liste_jetons(tables["jetons"])
                        if isinstance(j, dict) and j.get("genre") == "incident"])
    lieux = par_id(tables["lieux"])
    # alias compris : la couche carte impose ses propres ids (docs/schema.md)
    for lieu in tables["lieux"]:
        for alias in lieu.get("alias") or []:
            lieux.setdefault(alias, lieu)
    maisons = par_id(liste_simple(tables.get("maisons"), "maisons"))
    relations = liste_simple(tables.get("relations"), "relations")
    # une relation n'a pas d'id : elle se designe par le couple oriente
    couples = {(r.get("source_id"), r.get("cible_id")): r for r in relations
               if isinstance(r, dict)}
    joueur = (tables.get("journal") or {}).get("personnage_joueur_id")
    # tous les ids d'etapes du fichier — grossit au fil du lot, pour qu'une
    # etape ajoutee deux fois dans la meme proposition soit refusee aussi.
    ids_etapes = {e.get("id") for t in tables["intentions"]
                  for e in (t.get("plan") or [])
                  if isinstance(e, dict) and e.get("id")}

    def faute(i, message):
        erreurs.append("mutation {} : {}".format(i, message))

    for i, m in enumerate(mutations, 1):
        if not isinstance(m, dict):
            faute(i, "n'est pas un objet")
            continue
        table, op = m.get("table"), m.get("operation")
        if table not in OPERATIONS:
            faute(i, "table inconnue : {!r}".format(table))
            continue
        if op not in OPERATIONS[table]:
            faute(i, "operation {!r} inconnue pour la table {}".format(op, table))
            continue
        cible = m.get("cible")
        champs = m.get("champs") or {}
        avant, apres = None, None

        if table == "books":
            r = valider_books(i, m, op, cible, champs, faute, plan, tables)
        elif table == "intentions":
            r = valider_intentions(i, m, op, cible, champs, faute, plan, tetes, personnages, joueur, ids_etapes)
        elif table == "evenements":
            r = valider_evenements(i, m, op, cible, champs, faute, evenements)
        elif table == "mains":
            r = valider_mains(i, m, op, cible, champs, faute, plan, personnages, mains, lieux, maisons)
        elif table == "plis":
            r = valider_plis(i, m, op, cible, champs, faute, plan, personnages, plis, lieux, relations)
        elif table == "jetons":
            r = valider_jetons(i, m, op, cible, champs, faute, incidents, lieux)
        elif table == "lieux":
            r = valider_lieux(i, cible, champs, faute, lieux)
        elif table == "personnages":
            r = valider_personnages(i, m, op, cible, champs, faute, plan, mutations, tetes, personnages, lieux, maisons)
        elif table == "relations":
            r = valider_relations(i, m, op, champs, faute, plan, personnages, couples)
        else:
            r = valider_monde(i, champs, faute, tables)
        if r is CONTINUE:
            continue
        avant, apres = r

        plan.append({"n": i, "mutation": m, "avant": avant, "apres": apres})

    return plan, erreurs
