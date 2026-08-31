# -*- coding: utf-8 -*-
"""APPLICATION - appliquer() mute les structures en memoire, ecrire() les pose.

L'ancienne section application de scripts/appliquer.py (lot 2) : le plan a
deja ete valide, ici on ne refuse plus, on execute - puis l'ecriture atomique
passe par la porte noyau/tables, table par table.
"""
from etat.mutations.vocabulaire import (  # noqa: E501
    COLONNES_AFFAIRE_NEUVE, charge_relation, declencheur_vise, liste_books, liste_jetons, liste_simple, prochaine_ligne_action, table_actions)
from etat.mutations.lecture import chemin_table, liste_mains, liste_plis, par_id
from etat.expose import tables as porte  # LA PORTE de etat/
import bibliotheque  # noyau : la session d'ecriture des livres scindes
from etat.mutations.lecture import ETAT

def appliquer(plan, tables):
    """Mute les structures en memoire. Rend l'ensemble des tables touchees."""
    touchees = set()
    tetes = par_id(tables["intentions"], "personnage_id")
    evenements = par_id(tables["evenements"])
    personnages = par_id(tables["personnages"])
    mains = par_id(liste_mains(tables["mains"]))
    plis = par_id(liste_plis(tables["plis"]))
    incidents = par_id([j for j in liste_jetons(tables["jetons"])
                        if isinstance(j, dict) and j.get("genre") == "incident"])
    lieux = par_id(tables["lieux"])
    for lieu in tables["lieux"]:
        for alias in lieu.get("alias") or []:
            lieux.setdefault(alias, lieu)
    relations = liste_simple(tables.get("relations"), "relations")
    couples = {(r.get("source_id"), r.get("cible_id")): r for r in relations
               if isinstance(r, dict)}

    for ligne in plan:
        m = ligne["mutation"]
        table, op = m["table"], m["operation"]
        cible, champs = m.get("cible"), m.get("champs") or {}
        touchees.add(table)

        if table == "books":
            livres = liste_books(tables)
            if op == "affaire_ajouter":
                v = m["valeur"]
                neuve = {
                    "id": cible,
                    "titre": v["titre"],
                    "sous_titre": v.get("sous_titre") or "",
                    "type": "plan",
                    "embleme": v.get("embleme") or "🗂️",
                    "couleur": v.get("couleur") or "#4a4a5a",
                    "pages": list(v.get("pages") or []),
                    "tables": [{"titre": titre, "colonnes": list(cols),
                                "lignes": []}
                               for titre, cols in COLONNES_AFFAIRE_NEUVE.items()],
                }
                if isinstance(tables.get("books"), dict):
                    tables["books"].setdefault("books", livres).append(neuve)
                else:
                    livres.append(neuve)
                continue
            livre = next((x for x in livres
                          if x.get("id") == str(cible or "").split(":")[0]), None)
            actions = table_actions(livre or {})
            if op == "affaire_action_ajouter":
                actions.setdefault("lignes", []).append(
                    {"cellules": list(m["valeur"])})
                continue
            if op == "affaire_action":
                colonnes = actions.get("colonnes") or []
                ligne = prochaine_ligne_action(
                    actions, str(cible or "").partition(":")[2])
                for colonne, valeur in champs.items():
                    ligne["cellules"][colonnes.index(colonne)] = valeur
                continue

        if table == "intentions":
            if op == "tete_ajouter":
                neuve = m["valeur"]
                tables["intentions"].append(neuve)
                tetes[neuve["personnage_id"]] = neuve
                continue
            tete = tetes[cible]
            if op == "etape":
                etape = next(e for e in tete["plan"] if e.get("id") == m["etape"])
                etape.update(champs)
            elif op == "etape_ajouter":
                tete.setdefault("plan", []).append(m["valeur"])
            elif op == "tete":
                tete.update(champs)
            elif op.startswith("declencheur"):
                tete.setdefault("declencheurs", [])
                if op.endswith("ajouter"):
                    tete["declencheurs"].append(m["valeur"])
                else:
                    # declencheur_vise() atteint AUSSI les entrees non-dict :
                    # une chaine tombee dans la liste etait increvable des
                    # deux cotes (mj-accalmie, 129.4.3).
                    tete["declencheurs"] = [
                        d for d in tete["declencheurs"]
                        if not declencheur_vise(d, m["valeur"])]
            else:
                liste = "croyances" if op.startswith("croyance") else "ignore"
                tete.setdefault(liste, [])
                if op.endswith("ajouter"):
                    tete[liste].append(m["valeur"])
                else:
                    tete[liste].remove(m["valeur"])
        elif table == "evenements":
            ev = evenements[cible]
            if op == "diffusion_livree":
                ev["diffusion"][m["index"]]["livree"] = True
            elif op == "diffusion_ajouter":
                ev.setdefault("diffusion", []).append(m["valeur"])
            else:
                ev.update(champs)
        elif table == "mains":
            if op == "main_ajouter":
                neuve = m["valeur"]
                liste_mains(tables["mains"]).append(neuve)
                mains[neuve["id"]] = neuve
                continue
            act = mains[cible]
            if op == "mesure":
                mes = next(x for x in act["mesure"]
                           if x.get("id") == m.get("mesure"))
                mes.update(champs)
            elif op == "seuil":
                seuil = next(s for s in act["seuils"]
                             if s.get("id") == m.get("seuil"))
                seuil.update(champs)
            else:
                act.update(champs)
        elif table == "plis":
            if op == "pli_ajouter":
                neuf = m["valeur"]
                liste_plis(tables["plis"]).append(neuf)
                plis[neuf["id"]] = neuf
            else:
                plis[cible].update(champs)
        elif table == "jetons":
            inc = incidents[cible]
            if op == "incident_propage":
                inc.setdefault("propage", []).append(m["valeur"])
            else:
                inc.update(champs)
        elif table == "lieux":
            lieux[cible].setdefault("roukerie", {}).update(champs)
        elif table == "personnages":
            if op == "personnage_ajouter":
                neuf = m["valeur"]
                liste_simple(tables["personnages"], "personnages").append(neuf)
                personnages[neuf["id"]] = neuf
            else:
                personnages[cible].update(champs)
        elif table == "relations":
            v = charge_relation(m, op, champs)
            source = m.get("source_id") or (v or {}).get("source_id")
            cible_r = m.get("cible_id") or (v or {}).get("cible_id")
            if op == "relation_ajouter":
                neuve = dict(v)
                neuve["source_id"], neuve["cible_id"] = source, cible_r
                liste_simple(tables["relations"], "relations").append(neuve)
                couples[(source, cible_r)] = neuve
            else:
                couples[(source, cible_r)].update(champs)
        else:
            tables["monde"].update(champs)

    return touchees


def ecrire(nom, donnees, joueur=None):
    """Ecriture atomique par la porte. Fins de ligne LF desormais — l'ancien
    newline="\\r\\n" n'etait justifie nulle part et divergeait du reste."""
    # LES LIVRES PASSENT PAR LEUR SESSION, JAMAIS PAR UN FICHIER. Depuis la
    # scission (`migrations/scinder_bibliotheque.py`), ecrire un monolithe
    # `etat/books.json` a cote de `etat/books/` creerait deux copies qui font
    # foi en meme temps — exactement ce que la fiche de `bibliotheque`
    # interdit. Sa `Session` compare volume par volume et refuse le lot si un
    # autre l'a touche entre-temps : c'est l'ecriture optimiste dont deux
    # plumes ont besoin.
    if nom == "books":
        session = bibliotheque.ouvrir(ETAT)
        session.livres = ((donnees.get("books") or donnees.get("livres") or [])
                          if isinstance(donnees, dict) else donnees)
        return session.sauver()
    porte.ecrire(chemin_table(nom, joueur), donnees)
