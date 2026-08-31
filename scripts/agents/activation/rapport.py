# -*- coding: utf-8 -*-
"""RAPPORT — normaliser le rapport brut d'une activation : types de
resultats, references canonisees, mutations reparees puis filtrees, issue
de tache validee.
"""
import json
import os
import re

from temps.expose import regence

from agents.activation.socle import (journaliser, ETAT,
                                     DUREE_ACTIVATION_MIN_SECONDES,
                                     energie_pour_secondes, lire_json,
                                     TYPES_RESULTAT_ACTIVITE,
                                     ETATS_TERMINES)
from agents.activation.graphe import empreinte_tache, continuite_tache
from agents.activation.missions import (extraire_tentative,
                                        intitule_tache_activation)
from agents.activation.dossier import chaines_dans, references_du_dossier
from agents.activation.mutations import (valider_plausibilite_temporelle,
                                         valider_mutations_applicables,
                                         reparer_mutations,
                                         completer_cellules_affaire,
                                         filtrer_mutations_applicables,
                                         cible_est_tache,
                                         canoniser_reference,
                                         valider_issue_tache,
                                         CLEFS_RESULTAT, CLEFS_TABLE,
                                         CLEFS_VALEUR)

def normaliser_rapport_activation(brut, pid, tache, dossier,
                                  budget_energie, budget_secondes):
    """Traduit le releve humain en rapport interne de la boucle.

    Les anciens rapports imbriques restent lisibles ; les nouveaux acteurs ne
    voient plus les ids, l'energie ni cette structure technique.
    """
    # ON RECADRE, ON NE REFUSE PAS. Chaque `raise` de cette fonction detruisait
    # la journee entiere d'un homme — quatre minutes de session, son travail,
    # ses pensees — pour une seconde de comptabilite fausse ou un nom mal
    # ecrit. Ce qui est rattrapable se rattrape ici, se note, et se poursuit.
    corrections = []

    def recadrer(quoi):
        corrections.append(quoi)
        journaliser("rapport.recadre", acteur=pid, quoi=str(quoi)[:110])

    candidates = sorted({texte for texte in chaines_dans(brut)
                         if "candidate:" in texte})
    if candidates:
        # Un `candidate:` est une adresse que l'arbitre n'a pas su resoudre.
        # C'est un defaut de notre dossier, pas de son travail : on le note.
        recadrer("references candidate laissees telles quelles : %s"
                 % ", ".join(candidates[:4]))
    if isinstance(brut.get("activation"), dict):
        rapport = brut
        activation = rapport["activation"]
        activites = activation.get("activites") or []
        if not isinstance(activites, list):
            recadrer("activites hors liste : %r ecartees" % type(activites).__name__)
            activites = []
        debut_attendu = float((dossier.get("diffusion") or {})
                              .get("secondes_depuis_origine") or 0)
        prochain_debut = debut_attendu
        decalage_temps = 0.0
        temps_relatifs_convertis = False
        resultat_ids = set()
        refs_dossier = references_du_dossier(dossier)
        depense = 0
        duree_totale = 0
        activites = [a for a in activites if isinstance(a, dict)]
        activation["activites"] = activites
        for ordre, activite in enumerate(activites, 1):
            temps = activite.get("temps")
            if not isinstance(temps, dict):
                temps = {}
                activite["temps"] = temps
            duree = temps.get("duree_s")
            if isinstance(duree, bool) or not isinstance(duree, (int, float)) \
                    or int(duree) != duree or int(duree) <= 0:
                # Une duree absente ou absurde se deduit du couple debut/fin,
                # sinon elle vaut une seconde. On ne jette pas pour ca.
                d, f = temps.get("debut_s"), temps.get("fin_s")
                deduite = (int(f - d) if isinstance(d, (int, float))
                           and isinstance(f, (int, float)) and f > d else 1)
                recadrer("activite %d : duree %r -> %d s" % (ordre, duree, deduite))
                duree = deduite
                temps["duree_s"] = duree
            duree = int(duree)
            debut = temps.get("debut_s")
            fin = temps.get("fin_s")
            if not isinstance(debut, (int, float)) or isinstance(debut, bool):
                debut = prochain_debut
                temps["debut_s"] = debut
                recadrer("activite %d : debut pose sur la suite du fil" % ordre)
            if not isinstance(fin, (int, float)) or isinstance(fin, bool):
                fin = float(debut) + duree
                temps["fin_s"] = fin
                recadrer("activite %d : fin calculee" % ordre)
            # Le rapport peut exprimer son axe localement depuis zéro. On le
            # recadre une fois sur l'horloge du front, puis toutes les règles
            # de continuité et de durée restent strictes.
            if ordre == 1 and abs(float(debut)) <= 0.001 \
                    and abs(debut_attendu) > 0.001:
                decalage_temps = debut_attendu
                temps_relatifs_convertis = True
                journaliser("rapport.temps_recadres", acteur=pid,
                            origine_s=float(debut),
                            front_s=round(debut_attendu, 3))
            debut = float(debut) + decalage_temps
            fin = float(fin) + decalage_temps
            temps["debut_s"] = debut
            temps["fin_s"] = fin
            # L'ARITHMETIQUE SE RECALE, ELLE NE SE REFUSE PAS. Une seconde
            # d'ecart entre deux activites n'est pas une faute de l'homme :
            # c'est de la comptabilite, et c'est a nous de la tenir. On jetait
            # une journee entiere de travail pour un `fin - debut` faux de 1.
            if abs(float(debut) - prochain_debut) > 0.001:
                recadrer("activite %d recalee : debut %s -> %s"
                         % (ordre, debut, prochain_debut))
                glissement = prochain_debut - float(debut)
                debut = prochain_debut
                fin = float(fin) + glissement
                temps["debut_s"], temps["fin_s"] = debut, fin
            if abs((float(fin) - float(debut)) - duree) > 0.001:
                recadrer("activite %d : fin recalculee (%s -> %s)"
                         % (ordre, fin, float(debut) + duree))
                fin = float(debut) + duree
                temps["fin_s"] = fin

            chemin = activite.get("chemin_execution") or []
            somme_chemin = 0
            refs_chemin = set()
            propres = []
            for segment in chemin:
                if not isinstance(segment, dict):
                    recadrer("activite %d : segment illisible ecarte" % ordre)
                    continue
                sd = segment.get("duree_s")
                if isinstance(sd, bool) or not isinstance(sd, (int, float)) \
                        or int(sd) != sd or int(sd) < 0:
                    recadrer("activite %d : duree de segment corrigee (%r -> 0)"
                             % (ordre, sd))
                    sd = 0
                    segment["duree_s"] = 0
                somme_chemin += int(sd)
                for cle in ("de", "vers"):
                    if segment.get(cle):
                        segment[cle] = canoniser_reference(
                            segment[cle], refs_dossier)
                refs_chemin.update(str(segment.get(k)) for k in ("de", "vers")
                                   if segment.get(k))
                propres.append(segment)
            if propres != chemin:
                activite["chemin_execution"] = propres
                chemin = propres
            # Un chemin absent ou qui ne fait pas le compte : on l'ajuste sur
            # le dernier segment, ou l'on en pose un qui porte toute la duree.
            if somme_chemin != duree:
                recadrer("activite %d : chemin recale (%d s -> %d s)"
                         % (ordre, somme_chemin, duree))
                if chemin:
                    dernier = chemin[-1]
                    dernier["duree_s"] = max(
                        0, int(dernier.get("duree_s") or 0) + duree - somme_chemin)
                else:
                    chemin = [{"ordre": 1, "de": None, "relation": "sur place",
                               "vers": None, "duree_s": duree}]
                    activite["chemin_execution"] = chemin
                somme_chemin = duree

            sources = activite.get("sources_touchees") or []
            for source in sources:
                if isinstance(source, dict) and source.get("ref"):
                    source["ref"] = canoniser_reference(source["ref"], refs_dossier)
            refs_sources = {str(s.get("ref")) for s in sources
                            if isinstance(s, dict) and s.get("ref")}
            mobilisees = activite.get("sources_mobilisees") or []
            for source in mobilisees:
                if isinstance(source, dict) and source.get("ref"):
                    source["ref"] = canoniser_reference(source["ref"], refs_dossier)
            refs_mobilisees = {str(s.get("ref")) for s in mobilisees
                               if isinstance(s, dict) and s.get("ref")}
            action = activite.get("action") or {}
            action["cibles"] = [canoniser_reference(ref, refs_dossier)
                                 for ref in (action.get("cibles") or [])]
            refs_cibles = {str(ref) for ref in (action.get("cibles") or [])
                           if ref}
            refs_structures = refs_sources | refs_mobilisees | refs_chemin | refs_cibles
            inconnues = sorted(ref for ref in refs_structures
                               if ref not in refs_dossier and ref not in resultat_ids)
            if inconnues:
                # Nommer une chose qu'on ne connaissait pas n'est pas une
                # faute : c'est du monde qui deborde de la chemise. On le note.
                recadrer("activite %d : references inconnues admises : %s"
                         % (ordre, ", ".join(inconnues[:6])))
            # Une cible explicitement visée par le geste est une source
            # engagée, même si le narrateur a oublié de la recopier dans la
            # liste de provenance. On rend cette implication explicite.
            for ref in sorted(refs_cibles - refs_sources - refs_mobilisees):
                mobilisees.append({"ref": ref, "mode": "cible_action"})
            refs_mobilisees.update(refs_cibles)
            resultats = activite.get("resultats_produits") or []
            propres_resultats = []
            for resultat in resultats:
                if not isinstance(resultat, dict):
                    recadrer("activite %d : resultat illisible ecarte" % ordre)
                    continue
                propres_resultats.append(resultat)
                rid = resultat.get("id")
                if not rid or rid in resultat_ids:
                    neuf = "res:act:%s:%d:%d" % (pid, ordre,
                                                 len(propres_resultats))
                    while neuf in resultat_ids:
                        neuf += "b"
                    recadrer("activite %d : id resultat %r -> %s"
                             % (ordre, rid, neuf))
                    rid = neuf
                    resultat["id"] = rid
                resultat_ids.add(rid)
                if resultat.get("type") not in TYPES_RESULTAT_ACTIVITE:
                    recadrer("activite %d : type resultat %r -> fait"
                             % (ordre, resultat.get("type")))
                    resultat["type"] = "fait"
                resultat["cible"] = canoniser_reference(
                    resultat.get("cible"), refs_dossier)
                resultat["source_refs"] = [
                    canoniser_reference(ref, refs_dossier)
                    for ref in (resultat.get("source_refs") or [])]
                resultat["preuve_refs"] = [
                    canoniser_reference(ref, refs_dossier)
                    for ref in (resultat.get("preuve_refs") or [])]
                cible_resultat = str(resultat.get("cible") or "")
                if not cible_resultat:
                    # Un resultat sans cible vise l'affaire du jour : c'est la
                    # seule lecture honnete, et elle est presque toujours juste.
                    cible_resultat = str(tache.get("id") or "")
                    resultat["cible"] = cible_resultat
                    recadrer("activite %d : cible de resultat posee sur la tache"
                             % ordre)
                if cible_resultat not in refs_dossier \
                        and cible_resultat not in (resultat_ids - {rid}):
                    recadrer("activite %d : cible de resultat inconnue admise : %s"
                             % (ordre, cible_resultat))
                provenance = [str(x) for x in (resultat.get("source_refs") or [])]
                if not provenance:
                    # Sans provenance declaree, la source est ce que le geste a
                    # visé — ou l'acteur lui-même, qui a bien vu ce qu'il a fait.
                    provenance = sorted(refs_cibles) or ["pers:" + pid]
                    resultat["source_refs"] = provenance
                    recadrer("activite %d : source de resultat deduite (%s)"
                             % (ordre, ", ".join(provenance[:3])))
                # Un résultat peut dériver d'une source matérielle touchée,
                # d'un lieu traversé ou d'un résultat produit plus tôt dans
                # ce même rapport. Il ne peut pas se citer lui-même.
                connues = (refs_sources | refs_mobilisees | refs_chemin
                            | (resultat_ids - {rid}))
                # Les anciens arbitres pouvaient citer une mémoire du dossier
                # sans la redéclarer. On la rend explicite ici, mais seulement
                # si sa référence existe vraiment dans le dossier fermé.
                implicites = {ref for ref in provenance
                              if ref not in connues and ref in refs_dossier}
                for ref in sorted(implicites):
                    mobilisees.append({"ref": ref, "mode": "memoire"})
                refs_mobilisees.update(implicites)
                connues.update(implicites)
                etrangeres = [ref for ref in provenance if ref not in connues]
                if etrangeres:
                    # Il a cité une source qu'il n'a pas déclaré toucher. On
                    # la déclare pour lui plutôt que de jeter son résultat.
                    for ref in sorted(set(etrangeres)):
                        mobilisees.append({"ref": ref, "mode": "memoire"})
                    refs_mobilisees.update(etrangeres)
                    recadrer("activite %d : sources non declarees admises : %s"
                             % (ordre, ", ".join(sorted(set(etrangeres))[:4])))
            if propres_resultats != resultats:
                activite["resultats_produits"] = propres_resultats
                resultats = propres_resultats
            activite["sources_mobilisees"] = mobilisees

            activite["ordre"] = ordre
            activite["cout_energie"] = energie_pour_secondes(duree)
            activite["quoi"] = action.get("quoi") or action.get("verbe") \
                or "activité arbitrée"
            toutes_sources = refs_sources | refs_mobilisees
            activite["source"] = ", ".join(sorted(toutes_sources)) or None
            activite["resultat"] = " · ".join(
                "%s: %s" % (r.get("type"),
                              json.dumps(r.get("apres"), ensure_ascii=False)
                              if not isinstance(r.get("apres"), str)
                              else r.get("apres"))
                for r in resultats) or None
            preuves = [p for r in resultats for p in (r.get("preuve_refs") or [])]
            activite["preuve"] = preuves or None
            valider_plausibilite_temporelle(activite, ordre, dossier)
            depense += activite["cout_energie"]
            duree_totale += duree
            prochain_debut = float(fin)

        minimum_secondes = min(
            DUREE_ACTIVATION_MIN_SECONDES, budget_secondes)
        # Le budget est une borne de NOTRE comptabilite, pas une faute de
        # l'homme : s'il a travaille plus longtemps que prevu, on encaisse au
        # plafond et l'on garde sa journee. Trop court non plus ne se jette pas.
        if duree_totale < minimum_secondes:
            recadrer("journee courte gardee : %d s (minimum %d)"
                     % (duree_totale, minimum_secondes))
        if duree_totale > budget_secondes:
            recadrer("journee plus longue que le budget : %d s, plafonnee a %d"
                     % (duree_totale, budget_secondes))
        depense = round(min(depense, float(budget_energie)), 3)

        # LA LIGNE DE LA REGENCE, ET ELLE EST ICI POUR UNE RAISON. Un siege
        # vacant est elu et travaille comme n'importe qui — mais il n'engage
        # pas le joueur pour le reste de la partie pendant qu'il a le dos
        # tourne. On verifie AVANT `filtrer_mutations_applicables`, qui ecrit
        # dans etat/ pour de bon : passe cette ligne, il serait trop tard, et
        # le joueur retrouverait le serment prete en se rasseyant. Le refus
        # part dans la boucle de correction ordinaire — l'homme se rabat et
        # garde sa journee. Sans effet pour tous les autres acteurs.
        regence.verifier_rapport_activation(pid, rapport,
                                            journaliser=journaliser)

        mutations = rapport.get("mutations_proposees") or []
        liees, notes = reparer_mutations(
            mutations, resultat_ids, pid, tache, None)
        rejetees = []
        if notes:
            rapport["mutations_reparees"] = notes
            journaliser("mutations.reparees", acteur=pid, nombre=len(notes))
        # C'EST L'HOMME QUI A FERME L'ACTION, PAS LA BOUCLE. La premiere
        # ligne captee par le journal des affaires portait `par: null` et
        # `outil: boucle_activation.py` : vrai, et inutile — on veut savoir
        # QUI. `pid` est ici, il suffit de le poser le temps de l'ecriture ;
        # `bibliotheque.sauver()` le relit dans l'environnement. On restaure
        # apres, pour ne pas teindre ce qui suit dans le meme processus.
        _avant_qui = os.environ.get("LE_CONSEIL_QUI")
        os.environ["LE_CONSEIL_QUI"] = str(pid)
        try:
            applicables, erreurs = filtrer_mutations_applicables(liees)
        finally:
            if _avant_qui is None:
                os.environ.pop("LE_CONSEIL_QUI", None)
            else:
                os.environ["LE_CONSEIL_QUI"] = _avant_qui
        # L'ERREUR N'EST PAS A LA PLACE QU'ELLE OCCUPE DANS LA LISTE. `valider`
        # rend ses fautes dans l'ordre ou elle les trouve, prefixees de l'indice
        # REEL de la mutation (« mutation 7 : ... ») ; les apparier par position
        # collait la faute de la 7e sur la 4e. Un rapport de rejet qui designe
        # la mauvaise mutation est pire que pas de rapport : c'est ainsi que
        # 326 rejets ont pu passer pour du bruit pendant des nuits.
        for rang, erreur in enumerate(erreurs):
            trouve = re.match(r"\s*mutation\s+(\d+)\s*:", str(erreur))
            indice = (int(trouve.group(1)) - 1) if trouve else rang
            rejetees.append({
                "mutation": liees[indice] if 0 <= indice < len(liees) else None,
                "erreur": erreur})
        rapport["mutations_proposees"] = applicables
        if rejetees:
            rapport["mutations_rejetees"] = rejetees
            journaliser("rapport.mutations_ecartees", acteur=pid,
                        nombre=len(rejetees))
        valider_issue_tache(activation, tache,
                            dossier.get("continuite_reprise") or {})
        personnages = lire_json(os.path.join(ETAT, "personnages.json"), [])
        if isinstance(personnages, dict):
            personnages = personnages.get("personnages") or []
        ids_personnes = {str(p.get("id")) for p in personnages
                         if isinstance(p, dict) and p.get("id")}
        for reveil in activation.get("reveils_suivants") or []:
            qui = str((reveil or {}).get("qui") or "")
            if qui not in ids_personnes:
                recadrer("reveil suivant inconnu ecarte : %s" % qui)
        activation["tache"] = {
            "id": tache.get("id"),
            "quoi": intitule_tache_activation(tache, dossier),
            "creee": bool(tache.get("creee")),
        }
        activation["budget_energie"] = budget_energie
        activation["budget_secondes"] = budget_secondes
        activation["energie_depensee"] = round(depense, 3)
        if temps_relatifs_convertis:
            activation["temps_convertis_depuis_relatif"] = True
        rapport["qui"] = pid
        return rapport
    activites = []
    for ordre, activite in enumerate(brut.get("activites") or [], 1):
        if not isinstance(activite, dict):
            raise RuntimeError("activite %d illisible" % ordre)
        duree = activite.get("duree_secondes")
        if isinstance(duree, bool) or not isinstance(duree, (int, float)):
            raise RuntimeError("activite %d sans duree en secondes" % ordre)
        if int(duree) != duree or int(duree) <= 0:
            raise RuntimeError("activite %d : duree non entiere ou nulle" % ordre)
        activites.append({
            "ordre": ordre,
            "quoi": activite.get("quoi") or "geste non nomme",
            "cible_id": None,
            "source": activite.get("source"),
            "cout_energie": energie_pour_secondes(duree),
            "resultat": activite.get("resultat"),
            "preuve": activite.get("preuve"),
        })
    depense = sum(a["cout_energie"] for a in activites)
    changements = brut.get("changements_proposes") or []
    return {
        "qui": pid,
        "activation": {
            "tache": {
                "id": tache.get("id"),
                "quoi": intitule_tache_activation(tache, dossier),
                "creee": bool(tache.get("creee")),
            },
            "budget_energie": budget_energie,
            "budget_secondes": budget_secondes,
            "energie_depensee": depense,
            "issue": brut.get("issue") or "rien",
            "activites": activites,
            "suite": brut.get("suite"),
        },
        "mutations_proposees": changements,
    }

