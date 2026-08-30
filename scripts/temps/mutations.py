# -*- coding: utf-8 -*-
"""MUTATIONS — la redaction des mutations proposees, et rien d'autre.

CE QUE CE MODULE POSSEDE : la transcription des resultats de la fenetre en
mutations STRICTEMENT arithmetiques (horloges decomptees, seuils poses,
plis remis, sauts de rumeur sans contenu, nouvelles marquees livrees).
Extrait de fenetre.py pour tenir la limite des 500 lignes — c'etait la phase
la plus detachable : elle ne lit pas l'etat, elle ne lit que les paniers.

CE QU'IL REFUSE : le narratif. Ce qu'une etape tombee PRODUIT, c'est au MJ
de l'ecrire a la main dans la proposition avant scripts/appliquer.py ; le
`contenu` d'un saut de rumeur reste NUL a dessein.

CONSOMMATEURS : fenetre.py (calculer() l'appelle en avant-derniere phase).
"""
from temps.calendrier import fmt


def rediger(mains, franchissements, avancent, plis_remis, rumeurs,
                     nouvelles, jours, cible):
    """Les mutations proposees : STRICTEMENT ce qui est arithmetique.

    Les horloges qui se decomptent et les nouvelles qui se marquent livrees.
    Rien de narratif : ce qu'une etape tombee PRODUIT, c'est au MJ de l'ecrire
    a la main dans ce meme fichier avant de lancer scripts/appliquer.py.
    """
    mutations = []
    for a in mains:
        for m in a["mesures"]:
            if m["apres"] == m["avant"] and \
                    m["reliquat_apres"] == 0 and "gelee_par" not in m:
                continue
            mutations.append({
                "table": "mains",
                "cible": a["id"],
                "operation": "mesure",
                "mesure": m["adresse"].split(".", 1)[1],
                "champs": {"valeur": m["apres"],
                           "reliquat": m["reliquat_apres"]},
                "pourquoi": "{} jour(s) ecoule(s){}".format(
                    jours,
                    " — gelee, la mesure ne bouge pas" if "gelee_par" in m
                    else ""),
            })
    for f in franchissements:
        mutations.append({
            "table": "mains",
            "cible": f["main_id"],
            "operation": "seuil",
            "seuil": f["seuil"],
            "champs": {"franchi_le": cible if f["sens"] == "franchi" else None},
            "pourquoi": "{} {} {} (valeur {})".format(
                f["adresse"], f["quand"], f["borne"], f["valeur"]),
        })
    for s in avancent:
        mutations.append({
            "table": "intentions",
            "cible": s["personnage_id"],
            "operation": "etape",
            "etape": s["etape"],
            "champs": {"jours_restants": s["jours_restants_apres"]},
            "pourquoi": "{} jour(s) ecoule(s)".format(jours),
        })
    for p in plis_remis:
        champs = {"etat": "remis"}
        if p.get("main"):
            champs["main"] = p["main"]
        mutations.append({
            "table": "plis",
            "cible": p["id"],
            "operation": "pli",
            "champs": champs,
            "pourquoi": "arrive a {} le {}{}".format(
                p["vers"], fmt(p["attendu_le"]),
                "" if p.get("main")
                else " — SANS MAIN : pose-la toi-meme avant d'appliquer"),
        })
    for s in rumeurs:
        # `contenu` reste NUL a dessein : appliquer.py refusera le lot tant que
        # le MJ n'aura pas ecrit ce qui se dit la-bas. C'est la garde qui
        # empeche une machine de fabriquer du brouillard.
        mutations.append({
            "table": "jetons",
            "cible": s["incident_id"],
            "operation": "incident_propage",
            "valeur": {
                "ou": s["vers"],
                "date": s["date"],
                "certitude": s["certitude_proposee"],
                "ames": s["ames_estimees"],
                "depuis": s["depuis"],
                "contenu": None,
            },
            "pourquoi": "saute de {} ({} -> {}) — ECRIS le 'contenu' : ce qui "
                        "se dit la-bas, deforme. Sans lui, le lot est refuse."
                        .format(s["depuis"], s["certitude_source"],
                                s["certitude_proposee"]),
        })
    for n in nouvelles:
        mutations.append({
            "table": "evenements",
            "cible": n["evenement_id"],
            "operation": "diffusion_livree",
            "index": n["diffusion_index"],
            "pourquoi": "nouvelle parvenue le {}".format(fmt(n["date"])),
        })
    return mutations
