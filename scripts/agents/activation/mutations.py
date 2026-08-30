# -*- coding: utf-8 -*-
"""MUTATIONS — la plausibilite temporelle d'une activite, et le controle des
mutations rendues par le narrateur : validation, reparation, filtrage.
"""
import json
import os
import re

from etat.expose import appliquer  # vocabulaire ferme des mutations
from etat.expose import tables

from agents.activation.socle import (ETAT, journaliser, charger_tissu,
                                     _court)
from agents.activation.dossier import chaines_dans, mots

def valider_plausibilite_temporelle(activite, ordre, dossier):
    """Refuse les exploits manifestes ; l'ellipse condense la prose, pas le temps."""
    duree = int((activite.get("temps") or {}).get("duree_s") or 0)
    action = activite.get("action") or {}
    verbe = str(action.get("verbe") or "").casefold()
    texte_action = str(action.get("quoi") or "")
    resultats = activite.get("resultats_produits") or []
    textes_resultats = [str(r.get("apres") or "") for r in resultats
                        if isinstance(r, dict)]
    plus_long = max([len(mots(texte_action))] +
                    [len(mots(x)) for x in textes_resultats])
    if any(racine in verbe for racine in
           ("écri", "ecri", "copi", "rédig", "redig", "inscri")):
        maximum = 8 + 2 * duree
        if plus_long > maximum:
            raise RuntimeError(
                "activite %d temporellement impossible : %d mots ecrits/decrits "
                "en %d s (maximum genereux %d)" %
                (ordre, plus_long, duree, maximum))
    if any(racine in verbe for racine in
           ("dire", "parl", "répond", "repond", "annonc", "dict")):
        maximum = 10 + 4 * duree
        if len(mots(texte_action)) > maximum:
            raise RuntimeError(
                "activite %d temporellement impossible : parole trop longue "
                "pour %d s" % (ordre, duree))

    topologie = dossier.get("topologie_des_salles") or {}
    couts = {}
    for arete in topologie.get("aretes") or []:
        if not isinstance(arete, list) or len(arete) < 3:
            continue
        a, b, minutes = arete[:3]
        if isinstance(minutes, (int, float)):
            couts[frozenset(("salle:" + str(a), "salle:" + str(b)))] = \
                float(minutes) * 60.0
    for segment in activite.get("chemin_execution") or []:
        de, vers = str(segment.get("de") or ""), str(segment.get("vers") or "")
        minimum = couts.get(frozenset((de, vers)))
        if minimum is not None and float(segment.get("duree_s") or 0) < minimum:
            raise RuntimeError(
                "activite %d : trajet %s -> %s en %ss, minimum %ss" %
                (ordre, de, vers, segment.get("duree_s"), int(minimum)))


def charger_tables_application(mutations):
    noms = ("intentions", "evenements", "personnages", "monde", "journal",
            "lieux", "relations", "maisons", "books")
    tables = {nom: appliquer.lire(nom) for nom in noms}
    tables["plis"] = (appliquer.lire("plis")
                       if os.path.isfile(os.path.join(ETAT, "plis.json"))
                       else {"plis": []})
    if isinstance(tables["plis"], dict):
        tables["plis"].setdefault("plis", [])
    tables["mains"] = (appliquer.lire("mains")
                        if os.path.isfile(os.path.join(ETAT, "mains.json"))
                        else {"mains": []})
    # Les activations n'ont actuellement aucune mutation de croyance joueur.
    # Une apparition future doit fournir explicitement son joueur plutot que
    # d'ecrire dans un vieux repli global.
    tables["jetons"] = {"jetons": []}
    return tables


def valider_mutations_applicables(mutations):
    if not mutations:
        return
    _plan, erreurs = appliquer.valider(mutations,
                                       charger_tables_application(mutations))
    if erreurs:
        raise RuntimeError("mutations non applicables : " + " ; ".join(erreurs))


CLEFS_RESULTAT = ("resultat_id", "cite", "resultat", "res_id", "id_resultat",
                  "resultat_ref", "ref_resultat", "source_resultat")
CLEFS_TABLE = ("table", "domaine", "fichier", "cible_table")
CLEFS_VALEUR = ("valeur", "value", "contenu", "texte")


def reparer_mutations(mutations, resultat_ids, pid, tache, noeuds):
    """Redresser ce qu'un homme a voulu dire, au lieu de le jeter.

    ON NE REFUSE PLUS SUR LA FORME. Un acteur qui a travaille quatre minutes
    et dont on jette le rapport parce qu'il a ecrit `cite` au lieu de
    `resultat_id` a travaille pour rien, et nous avons perdu sa journee sur un
    nom de clef. Mesure du 10 aout : 326 mutations sur 355 detruites ainsi,
    toutes pour la meme raison. La forme est notre affaire, pas la sienne.

    On coerce donc tout ce qui est coercible et l'on note ce qu'on a redresse.
    Ne restent refusees que les choses qu'aucune lecture honnete ne sauve.
    """
    if noeuds is None:
        try:
            noeuds, _a, _e = charger_tissu()
        except Exception:
            noeuds = {}
    par_ou = {}
    for nid, n in (noeuds or {}).items():
        ou = str((n or {}).get("ou") or "")
        if ou.startswith("affaire-"):
            par_ou[nid] = ou
    defaut_resultat = next(iter(sorted(resultat_ids)), None)
    reparees, notes = [], []

    def noter(quoi, avant, apres):
        notes.append({"quoi": quoi, "avant": avant, "apres": apres})

    for brute in mutations:
        if not isinstance(brute, dict):
            continue
        m = dict(brute)

        # --- l'adresse du resultat, sous n'importe quel nom
        rid = next((m.get(c) for c in CLEFS_RESULTAT if m.get(c)), None)
        for c in CLEFS_RESULTAT[1:]:
            m.pop(c, None)
        if rid not in resultat_ids:
            secours = rid if rid in resultat_ids else defaut_resultat
            if rid is not None:
                noter("resultat_id inconnu", rid, secours)
            rid = secours
        m["resultat_id"] = rid

        # --- table et operation, quel que soit l'emballage
        table = next((m.get(c) for c in CLEFS_TABLE if m.get(c)), None)
        op = m.get("operation") or m.get("op")
        m.pop("op", None)
        for c in CLEFS_TABLE[1:]:
            m.pop(c, None)
        if isinstance(op, str) and "." in op and not table:
            table, _, op = op.partition(".")
            noter("operation collee", m.get("operation"), "%s / %s" % (table, op))
        elif isinstance(op, str) and "." in op:
            op = op.rpartition(".")[2]
        if isinstance(table, str):
            table = table.replace(".json", "").strip()
        if table not in appliquer.OPERATIONS and op:
            devine = [t for t, ops in appliquer.OPERATIONS.items() if op in ops]
            if len(devine) == 1:
                noter("table devinee depuis l'operation", table, devine[0])
                table = devine[0]
        m["table"], m["operation"] = table, op

        # --- la valeur, sous n'importe quel nom
        if "valeur" not in m:
            for c in CLEFS_VALEUR[1:]:
                if c in m:
                    m["valeur"] = m.pop(c)
                    noter("valeur renommee", c, "valeur")
                    break

        # --- la cible manquante : c'est presque toujours lui-meme
        if table == "intentions" and not m.get("cible"):
            m["cible"] = pid
            noter("cible absente", None, pid)
        if table == "personnages" and not m.get("cible"):
            m["cible"] = pid
            noter("cible absente", None, pid)

        # --- les affaires : un id de noeud du tissu vaut son cahier
        if table == "books":
            cible = str(m.get("cible") or "")
            tete, _, queue = cible.partition(":")
            if tete in par_ou:
                neuve = par_ou[tete] + (":" + queue if queue else ":" + tete)
                if op == "affaire_action_ajouter":
                    neuve = par_ou[tete]
                noter("affaire resolue depuis le tissu", cible, neuve)
                m["cible"] = neuve
            if op == "affaire_action_ajouter" and not isinstance(
                    m.get("valeur"), list):
                champs = m.get("champs") or {}
                if champs:
                    m["valeur"] = list(champs.values())
                    noter("cellules reconstituees depuis champs", None,
                          len(m["valeur"]))

        # --- les champs interdits : on retire le champ, pas la mutation
        if table == "personnages" and isinstance(m.get("champs"), dict):
            mauvais = [c for c in m["champs"]
                       if c not in appliquer.CHAMPS_PERSO]
            if mauvais and len(mauvais) < len(m["champs"]):
                for c in mauvais:
                    m["champs"].pop(c)
                noter("champs de personnage retires", ", ".join(mauvais), None)

        reparees.append(m)
    return reparees, notes


def completer_cellules_affaire(mutations, tables):
    """Une action a qui il manque des cellules se complete, ne se refuse pas."""
    livres = appliquer.liste_books(tables)
    par_id = {x.get("id"): x for x in livres if isinstance(x, dict)}
    notes = []
    for m in mutations:
        if m.get("table") != "books" or m.get("operation") != "affaire_action_ajouter":
            continue
        livre = par_id.get(str(m.get("cible") or "").split(":")[0])
        actions = appliquer.table_actions(livre or {})
        if not actions:
            continue
        attendu = len(actions.get("colonnes") or [])
        cellules = m.get("valeur")
        if not isinstance(cellules, list):
            cellules = []
        if len(cellules) != attendu:
            notes.append({"quoi": "cellules ajustees",
                          "avant": len(cellules), "apres": attendu})
            cellules = (list(cellules) + [""] * attendu)[:attendu]
            m["valeur"] = cellules
    return notes


def filtrer_mutations_applicables(mutations):
    """Valide, REPARE ce qui peut l'etre, puis ECRIT dans etat/ pour de bon.

    IL N'Y A PLUS DE STAGING POUR LES ACTIVATIONS. Un homme qu'on depeche n'est
    pas dans un monde virtuel : ce qu'il a fait, il l'a fait, et ca doit se
    voir dans l'etat sans qu'un humain vienne recopier une proposition. Le
    depot `etat/activations` reste la TRACE de sa journee — le rapport,
    ses activites, ce qu'on a redresse — mais il n'est plus le purgatoire ou
    son travail attendait qu'on veuille bien le regarder.
    """
    if not mutations:
        return [], []
    tables = charger_tables_application(mutations)
    completer_cellules_affaire(mutations, tables)
    plan, erreurs = appliquer.valider(mutations, tables)
    retenues = [item["mutation"] for item in plan]
    if plan:
        touchees = appliquer.appliquer(plan, tables)
        for nom in sorted(touchees):
            appliquer.ecrire(nom, tables[nom])
        journaliser("mutations.ecrites", nombre=len(plan),
                    tables=",".join(sorted(touchees)))
    return retenues, erreurs


def cible_est_tache(cible, tache_id):
    cible = str(cible or "")
    return cible == str(tache_id) or cible.endswith(":" + str(tache_id))


def canoniser_reference(ref, autorisees):
    """Retire seulement les enveloppes `ref:` qui resolvent sans ambiguite."""
    ref = str(ref or "")
    if ref in autorisees or not ref.startswith("ref:"):
        return ref
    nue = ref[4:]
    essais = [nue]
    if not nue.startswith(("pers:", "salle:", "travail:", "trav:",
                           "main:", "livre:", "book:", "tache:")):
        essais.extend(("salle:" + nue, "pers:" + nue,
                       "travail:" + nue, "livre:" + nue))
    resolues = [x for x in essais if x in autorisees]
    return resolues[0] if len(resolues) == 1 else ref


def valider_issue_tache(activation, tache, continuite):
    issue = activation.get("issue")
    tache_id = tache.get("id")
    resultats = [r for a in activation.get("activites") or []
                 for r in (a.get("resultats_produits") or [])
                 if isinstance(r, dict)]
    lies = [r for r in resultats if cible_est_tache(r.get("cible"), tache_id)]
    requis = {
        "avance": "progression_tache",
        "termine": "progression_tache",
        "bloque": "blocage",
        "echoue": "echec",
    }.get(issue)
    if requis and not any(r.get("type") == requis for r in lies):
        raise RuntimeError("issue %s sans resultat %s visant exactement la tache %s"
                           % (issue, requis, tache_id))

    # La continuite d'etat n'est plus une condition de rejet : exiger que le
    # "avant" recolle mot pour mot au "apres" du rapport precedent faisait
    # brûler ses trois essais a un acteur pour une reformulation, et abattait
    # la boucle entiere. On note l'ecart, on ne refuse plus.
    etats = (continuite or {}).get("etat_cibles") or {}
    for resultat in resultats:
        precedent = etats.get(str(resultat.get("cible") or ""))
        if precedent is None:
            continue
        if resultat.get("avant") != precedent.get("apres"):
            journaliser("rapport.continuite_ecart",
                        cible=resultat.get("cible"),
                        avant=_court(str(resultat.get("avant")), 120),
                        precedent=_court(str(precedent.get("apres")), 120))

