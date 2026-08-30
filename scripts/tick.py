"""Moteur arithmetique du hors-scene : ce qui tombe, et rien de plus.

Usage :
    python scripts/tick.py --verifier
        Audit de coherence de etat/ (intentions, evenements, diffusion, lieux).
        Sort en code 1 des qu'il y a une anomalie, 0 sinon.

    python scripts/tick.py --jours 3
    python scripts/tick.py --jusqu-a 129.3.20
        Calcule la fenetre depuis monde.date jusqu'a la cible, ecrit une
        PROPOSITION dans etat/tick-<AAAAMMJJ-HHMMSS>.json, et imprime
        un resume lisible.

    python scripts/tick.py --jours 3 --acteur daemon --acteur corlys
        Restreint le calcul a ces acteurs (repetable).

Le script ne decide RIEN. Il lit etat/ et n'ecrit que sous etat/ :
le MJ seul relit, arbitre et applique dans etat/*.json. Un seul ecrivain.

Reference normative du format : docs/schema.md. Calendrier : 12 lunes de
30 jours. Ce qui n'y est pas tranche l'est ici, au plus simple :
- Budget d'etapes : on compte le plan VIVANT (etapes `en-cours` ou `bloque`).
  Une etape `fait` ou `abandonne` ne charge plus la tete.
- Une etape dont `jours_restants` vaut null est une posture permanente : elle
  ne tombe jamais, ne se decompte jamais, et n'apparait dans aucun des trois
  paniers d'etapes (seulement dans le compte du resume).
- Une etape dont un `depend_de` n'est pas `fait` voit son horloge arretee :
  elle passe en attente, sans consommer les jours de la fenetre.
- Retard tolere d'une tete avant rafraichissement : 1 jour (scene), 3 jours
  (orbite), 15 jours (royaume).
- Un plan encore ecrit en chaines de caracteres (format d'avant les etapes
  horlogees) est signale, jamais reparé.
- LA BOUCHE (docs/plis.md) : un homme qui se deplace porte TOUT ce qu'il sait.
  Le tick detecte les arrivees a partir de ce qui existe deja (evenements de la
  fenetre, etapes qui tombent) et sort le DIFFERENTIEL de croyances — jamais un
  verdict. Il ne recopie aucune croyance : le MJ arbitre ce qui se dit.
- Les plis (etat/plis.json, voir docs/plis.md) sont routes : un pli `en-route`
  dont `attendu_le` est echu passe `remis`, dans la main du destinataire NATUREL
  du lieu (le mestre), jamais dans celle du `pour`. `evenements.diffusion` reste
  en place a cote : c'est une coexistence, pas un remplacement.
"""
import argparse
import collections
import hashlib
import io
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# LES PENSEES NE SE CALCULENT PLUS ICI, et `travaux.py` a disparu avec son
# excitation. Un compteur ne pouvait pas dire ce qu'un homme a appris : ce qui
# le dit, c'est sa JOURNEE — le quartier ou il se tient, les creux qu'elle lui
# laisse, les sources a portee de ces creux. C'est `presence.py` qui le mesure
# et `evaluer.py` qui en tire la feuille de route.
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from temps.expose import occupation  # qui est ASSIS — mesure, pas drapeau
# La regence (docs/regence.md) : ce qu'un siege vacant peut faire et ce qu'il
# doit rendre. Branche ici pour la seule garde — clause posee, passation due.
from temps.expose import regence
from etat.expose import tables  # LA PORTE de etat/

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
STAGING = ETAT

# L'echelle mesuree sur le quartier et ses budgets vivent dans temps/bouche.py.
from temps.bouche import (ECHELLES, BUDGETS,  # noqa: E402,F401
                          TOLERANCE_MAJ, FENETRE_ROYAUME)

# Les plis (docs/plis.md) : les constantes du courrier vivent desormais dans
# temps/lecture.py, a cote de jours_de_route et des methodes plis d'Etat.
from temps.lecture import (CANAUX_PLI, ETATS_PLI,  # noqa: E402,F401
                           ETATS_PLI_EN_MAIN, TOLERANCE_PLI, DIVISEUR_CORBEAU)

# LA BOUCHE — le rapprochement de textes vit dans temps/bouche.py.
from temps.bouche import MOTS_COMMUNS, MOTS_PARTAGES_MINIMUM  # noqa: E402,F401

# LA RUMEUR vit dans temps/rumeur.py (decoupage du container temps).
from temps.rumeur import (CERTITUDES, LENTEUR_RUMEUR,  # noqa: E402,F401
                          SAUT_RUMEUR_MINIMUM, PORTEE_SAUT_RUMEUR,
                          VOISINS_PAR_RUMEUR, SILENCE_RUMEUR)


# ------------------------------------------------------------------- dates
# Demenage dans temps/calendrier.py (decoupage du container temps).

from temps.calendrier import (JOURS_PAR_LUNE, LUNES_PAR_AN,  # noqa: E402,F401
                              jour_absolu, date_de, fmt, lire_date)


# ---------------------------------------------------------------- lecture

# Demenage dans temps/lecture.py (decoupage du container temps).
from temps.lecture import charger, Etat, jours_de_route  # noqa: E402,F401


# ------------------------------------------------------------- LA BOUCHE
# Demenage dans temps/bouche.py (decoupage du container temps).

from temps.bouche import (mots_rares, se_recoupent,  # noqa: E402,F401
                          croyances_de, _dans_le_quartier, echelle_de,
                          etapes_de)


# --------------------------------------------------- MAINS : l'arithmetique
# Demenage dans temps/mains.py (decoupage du container temps).

from temps.mains import (rythme_de, borner, au_plancher,  # noqa: E402,F401
                         decompter, porteur_absent, couts_chiffres,
                         chiffrer_cout, seuil_franchi)


# ------------------------------------------------------- garde d'ecriture

# Demenage dans temps/scelle.py (decoupage du container temps).
from temps.scelle import (TABLES_MUTABLES, CROYANCES,  # noqa: E402,F401
                          chemin_scelle, empreintes_etat, ecrire_proposition)


# ------------------------------------------------------- MODE A : verifier
# Demenage dans temps/gardes/ (decoupage du container temps).

from temps.gardes import (GRAVITES, Rapport, verifier,  # noqa: E402,F401
                          verifier_intentions, verifier_mains,
                          verifier_couts_chiffres, verifier_etats_du_plan,
                          verifier_rapporteurs, CLES_BOOK, CLES_BOITE,
                          TYPES_BOOK, verifier_pensees, qui_a_du_temps,
                          verifier_books, verifier_boites, sources_possibles,
                          verifier_croyances_sans_porteur, verifier_evenements,
                          verifier_personnages, verifier_plis,
                          verifier_rumeurs, verifier_occupation, siege_par_id,
                          verifier_sieges, verifier_audiences,
                          verifier_affectations, verifier_registres_derives,
                          verifier_activations)

# ------------------------------------------------------------- LA RUMEUR
# Demenage dans temps/rumeur.py (decoupage du container temps).

from temps.rumeur import (temoins_des_incidents,  # noqa: E402,F401
                          rang_certitude, degrader, relais_de,
                          saut_rumeur, propager_rumeurs, sans_accents,
                          lieu_cite, detecter_bouches, cycles)


# ----------------------------------------------------------- MODE B : tick

def calculer(e, cible, restriction, joueur=None):
    """Ce qui tombe entre monde.date et cible. Aucune decision, du calcul."""
    fin = jour_absolu(cible)
    jours = fin - e.aujourdhui
    fenetre = {"de": e.date, "a": cible, "jours": jours}

    # --- LES MAINS D'ABORD (docs/schema.md : mains.json)
    # La boucle des mains tourne AVANT celle des absents, parce que sa
    # sortie est son entree : un `cout` d'etape qui cite une adresse de mesure
    # se verifie contre la valeur d'APRES decompte, pas celle d'avant.
    mesures_apres = {}       # adresse -> valeur apres la fenetre
    mains, franchissements = [], []
    for act in e.mains:
        aid = act.get("id")
        absent = porteur_absent(e, act)
        lignes = []
        for mes in act.get("mesure") or []:
            adresse = "{}.{}".format(aid, mes.get("id"))
            par, _pas = rythme_de(mes)
            # une mesure gelee par une dependance au plancher ne bouge pas —
            # elle n'est pas remise a zero, et son reliquat est conserve
            gelee = [d for d in (mes.get("depend_de") or [])
                     if d in e.mesure_par_adresse
                     and au_plancher(e.mesure_par_adresse[d][1])]
            # porteur mort ou parti : ce qui produit s'arrete, ce qui coute
            # continue. C'est ainsi qu'une affaire pourrit toute seule.
            muet = absent and par > 0
            if gelee or muet:
                valeur = mes.get("valeur")
                reliquat = mes.get("reliquat", 0)
                borne = None
            else:
                valeur, reliquat, borne = decompter(mes, jours)
            mesures_apres[adresse] = valeur
            ligne = {
                "adresse": adresse,
                "quoi": mes.get("quoi"),
                "unite": mes.get("unite"),
                "avant": mes.get("valeur"),
                "apres": valeur,
                "reliquat_apres": reliquat,
            }
            if gelee:
                ligne["gelee_par"] = gelee
            if muet:
                ligne["porteur_absent"] = True
            if borne:
                ligne["bute_sur"] = borne
            lignes.append(ligne)

            for seuil in act.get("seuils") or []:
                if seuil.get("mesure_id") != mes.get("id"):
                    continue
                etait = bool(seuil.get("franchi_le"))
                est = seuil_franchi(valeur, seuil)
                if est == etait:
                    continue
                franchissements.append({
                    "main_id": aid,
                    "seuil": seuil.get("id"),
                    "adresse": adresse,
                    "sens": "franchi" if est else "retombe",
                    "quand": seuil.get("quand"),
                    "borne": seuil.get("valeur"),
                    "valeur": valeur,
                    "porteur": act.get("porteur"),
                    "promeut": seuil.get("promeut"),
                    "affaire": seuil.get("affaire"),
                    "date": cible,
                })
        mains.append({
            "id": aid,
            "quoi": act.get("quoi"),
            "porteur": act.get("porteur"),
            "porteur_absent": absent,
            "mandat": act.get("mandat"),
            "mesures": lignes,
        })

    # --- quels acteurs on simule
    simules, sautes = [], []
    for tete in e.intentions:
        pid = tete.get("personnage_id")
        if not pid or pid == e.joueur:
            continue
        if restriction and pid not in restriction:
            continue
        if echelle_de(tete) == "royaume" and jours < FENETRE_ROYAUME:
            sautes.append(tete)
        else:
            simules.append(tete)

    # --- evenements a resoudre
    a_resoudre = []
    for ev in e.evenements:
        if ev.get("statut") != "a-venir":
            continue
        quand = jour_absolu(ev.get("date_prevue"))
        if quand is None or quand > fin:
            continue
        a_resoudre.append({
            "id": ev.get("id"),
            "date": ev.get("date_prevue"),
            "type": ev.get("type"),
            "importance": ev.get("importance"),
            "description": ev.get("description"),
            "lieu_id": ev.get("lieu_id"),
            "acteurs": ev.get("acteurs") or [],
            "conditions": ev.get("conditions") or [],
            "diffusion": ev.get("diffusion") or [],
            "en_retard": quand < e.aujourdhui,
        })
    a_resoudre.sort(key=lambda x: jour_absolu(x["date"]) or 0)

    # --- nouvelles a livrer
    # Le statut de l'evenement commande : on ne livre que ce qui a EU LIEU.
    #   resolu   -> livrable
    #   a-venir  -> conditionnel, l'echeance tombe dans la fenetre mais le MJ
    #               n'a pas encore arbitre : la nouvelle ne part qu'apres
    #   devie / annule -> jamais. La chose ne s'est pas produite.
    nouvelles, conditionnelles = [], []
    for ev in e.evenements:
        statut = ev.get("statut")
        if statut in ("devie", "annule"):
            continue
        for i, ent in enumerate(ev.get("diffusion") or []):
            if not isinstance(ent, dict) or ent.get("livree") is True:
                continue
            quand = jour_absolu(ent.get("date"))
            if quand is None or quand > fin:
                continue
            ou = ent.get("ou")
            qui = list(ent.get("qui") or [])
            deduit = False
            if not qui and ou:
                qui = e.actifs_en(ou)
                deduit = True
            touche = bool(e.joueur) and (
                e.joueur in qui
                or (ou and e.lieu(ou) is not None
                    and e.lieu(ou) == e.lieu(
                        (e.perso_par_id.get(e.joueur) or {}).get("lieu_id"))))
            entree = {
                "evenement_id": ev.get("id"),
                "diffusion_index": i,
                "date": ent.get("date"),
                "canal": ent.get("canal"),
                "fiabilite": ent.get("fiabilite"),
                "version": ent.get("version"),
                "ou": ou,
                "qui": qui,
                "qui_deduit": deduit,
                "touche_joueur": touche,
                "en_retard": quand < e.aujourdhui,
            }
            if statut == "resolu":
                nouvelles.append(entree)
            else:
                entree["depend_de_evenement"] = ev.get("id")
                entree["statut_evenement"] = statut
                conditionnelles.append(entree)
    nouvelles.sort(key=lambda x: jour_absolu(x["date"]) or 0)
    conditionnelles.sort(key=lambda x: jour_absolu(x["date"]) or 0)

    # --- LE COURRIER : ce qui arrive (docs/plis.md)
    # Rien n'atteint personne sans porteur. Un pli echu est REMIS, dans la main
    # du destinataire naturel du lieu — le mestre —, jamais dans celle du `pour`.
    plis_remis, plis_en_route = [], []
    for pli in e.plis:
        if not isinstance(pli, dict) or pli.get("etat") != "en-route":
            continue
        quand = jour_absolu(pli.get("attendu_le"))
        if quand is None:
            continue
        entree = {
            "id": pli.get("id"),
            "canal": pli.get("canal"),
            "de": pli.get("de"),
            "pour": pli.get("pour"),
            "vers": pli.get("vers"),
            "attendu_le": pli.get("attendu_le"),
            "scelle": pli.get("scelle"),
        }
        if quand > fin:
            entree["jours_encore"] = quand - fin
            plis_en_route.append(entree)
            continue
        main = e.destinataire_naturel(pli.get("vers"))
        entree["main"] = main
        entree["porte"] = pli.get("porte")
        entree["en_retard"] = quand < e.aujourdhui
        if main is None:
            entree["probleme"] = ("aucun destinataire naturel a {} — dis dans "
                                  "quelle main le pli tombe".format(
                                      pli.get("vers")))
        elif main == pli.get("pour"):
            # ca arrive (le pour EST le mestre) ; on le dit, ce n'est pas une faute
            entree["main_est_le_pour"] = True
        plis_remis.append(entree)
    plis_remis.sort(key=lambda x: jour_absolu(x["attendu_le"]) or 0)
    plis_en_route.sort(key=lambda x: jour_absolu(x["attendu_le"]) or 0)

    # --- etapes : tombent, avancent, ou attendent
    tombent, avancent, attendent = [], [], []
    postures = 0
    fait = set()
    for tete in e.intentions:
        for etape in etapes_de(tete):
            if etape.get("etat") == "fait" and etape.get("id"):
                fait.add(etape["id"])

    for tete in simules:
        pid = tete.get("personnage_id")
        ech = echelle_de(tete)
        for etape in etapes_de(tete):
            if etape.get("etat") != "en-cours":
                continue
            commun = {
                "personnage_id": pid,
                "echelle": ech,
                "etape": etape.get("id"),
                "quoi": etape.get("quoi"),
                "cout": etape.get("cout") or [],
                "si_bloque": etape.get("si_bloque"),
            }
            # Un cout peut CITER une mesure : {mesure, quantite}. Alors il se
            # verifie ici, contre la valeur d'apres decompte, et le si_bloque
            # se declenche par arithmetique. Un cout en clair reste au MJ.
            manque = chiffrer_cout(etape, mesures_apres)
            if manque:
                commun["cout_non_couvert"] = manque
            bloquants = [d for d in (etape.get("depend_de") or [])
                         if d not in fait]
            if bloquants:
                attendu = dict(commun)
                attendu["depend_de_non_fait"] = bloquants
                attendu["jours_restants"] = etape.get("jours_restants")
                attendent.append(attendu)
                continue
            reste = etape.get("jours_restants", "absent")
            if reste is None:
                postures += 1
                continue
            if not isinstance(reste, int):
                # horloge absente ou illisible : le MJ doit la poser
                sans = dict(commun)
                sans["jours_restants"] = None if reste == "absent" else reste
                sans["probleme"] = "horloge absente ou illisible"
                attendent.append(sans)
                continue
            if reste - jours <= 0:
                tombee = dict(commun)
                tombee["jours_restants"] = reste
                tombee["date_estimee"] = date_de(
                    e.aujourdhui + max(reste, 0))
                tombent.append(tombee)
            else:
                suite = dict(commun)
                suite["jours_restants"] = reste
                suite["jours_restants_apres"] = reste - jours
                avancent.append(suite)
    # Un acteur 'royaume' n'est pas rafraichi sur une fenetre courte, mais une
    # echeance ne se perd jamais : le coffre d'or promis pour demain tombe
    # demain, meme si la tete de celui qui l'apporte n'est pas repassee en revue.
    for tete in sautes:
        for etape in etapes_de(tete):
            if etape.get("etat") != "en-cours":
                continue
            if [d for d in (etape.get("depend_de") or []) if d not in fait]:
                continue
            reste = etape.get("jours_restants")
            if not isinstance(reste, int) or reste - jours > 0:
                continue
            tombent.append({
                "personnage_id": tete.get("personnage_id"),
                "echelle": "royaume",
                "etape": etape.get("id"),
                "quoi": etape.get("quoi"),
                "cout": etape.get("cout") or [],
                "si_bloque": etape.get("si_bloque"),
                "jours_restants": reste,
                "date_estimee": date_de(e.aujourdhui + max(reste, 0)),
                "malgre_saut": True,
            })

    tombent.sort(key=lambda x: jour_absolu(x["date_estimee"]) or 0)

    # --- LA BOUCHE : qui arrive, et ce qu'il apporte que personne ne sait ici
    bouches = detecter_bouches(e, a_resoudre, tombent)

    # --- LA RUMEUR : ce qui saute de proche en proche, sans porteur nomme
    rumeurs, rumeurs_immobiles = propager_rumeurs(e, fin, cible)

    # --- declencheurs a evaluer (le MJ seul juge)
    declencheurs = []
    for tete in simules:
        pid = tete.get("personnage_id")
        for d in (tete.get("declencheurs") or []):
            if not isinstance(d, dict):
                continue
            declencheurs.append({
                "personnage_id": pid,
                "echelle": echelle_de(tete),
                "si": d.get("si"),
                "alors": d.get("alors"),
                "une_fois": d.get("une_fois"),
            })

    # --- tetes en retard une fois la fenetre franchie
    rafraichir = []
    for tete in simules:
        maj = jour_absolu(tete.get("date_maj"))
        ech = echelle_de(tete)
        if maj is None or fin - maj > TOLERANCE_MAJ[ech]:
            rafraichir.append({
                "personnage_id": tete.get("personnage_id"),
                "echelle": ech,
                "date_maj": tete.get("date_maj"),
                "retard_apres_fenetre": None if maj is None else fin - maj,
            })

    # --- mutations proposees : STRICTEMENT ce qui est arithmetique
    # Les horloges qui se decomptent et les nouvelles qui se marquent livrees.
    # Rien de narratif : ce qu'une etape tombee PRODUIT, c'est au MJ de l'ecrire
    # a la main dans ce meme fichier avant de lancer scripts/appliquer.py.
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

    # --- LES PENSEES : ce que chacun a touche, et s'il a de quoi parler.
    # Apres les mains (dont elle peut lire les mesures) et avant la salle, dont
    # elle est l'entree : un conseiller qui n'a rien touche n'a rien a dire, et
    # la boucle d'election doit le savoir avant d'elire qui que ce soit.
    pensees = qui_a_du_temps(e)

    return {
        "genere_le": datetime.now().isoformat(timespec="seconds"),
        "joueur": joueur,
        "empreintes": empreintes_etat(joueur),
        "avertissement": "Proposition — le MJ arbitre et applique lui-meme "
                         "dans etat/*.json. Ce fichier n'est pas de l'etat.",
        "fenetre": fenetre,
        "mains": mains,
        "seuils_franchis": franchissements,
        "travaux": pensees,
        "acteurs_simules": [t.get("personnage_id") for t in simules],
        "acteurs_sautes_royaume": sorted(
            t.get("personnage_id") for t in sautes),
        "postures_permanentes": postures,
        "evenements_a_resoudre": a_resoudre,
        "nouvelles_a_livrer": nouvelles,
        "nouvelles_conditionnelles": conditionnelles,
        "bouches": bouches,
        "rumeurs_qui_sautent": rumeurs,
        "rumeurs_immobiles": rumeurs_immobiles,
        "plis_remis": plis_remis,
        "plis_encore_en_route": plis_en_route,
        "etapes_qui_tombent": tombent,
        "etapes_qui_avancent": avancent,
        "etapes_en_attente": attendent,
        "declencheurs_a_evaluer": declencheurs,
        "tetes_a_rafraichir": rafraichir,
        "mutations_proposees": mutations,
    }


# Demenage dans temps/resume.py (decoupage du container temps).
from temps.resume import resumer  # noqa: E402,F401


def tick(e, cible, restriction, joueur=None):
    if jour_absolu(cible) < e.aujourdhui:
        sys.exit("cible {} anterieure a monde.date {} — le tick n'avance "
                 "que dans un sens".format(fmt(cible), fmt(e.date)))
    prop = calculer(e, cible, restriction, joueur)
    base = "tick-{}".format(datetime.now().strftime("%Y%m%d-%H%M%S"))
    nom, n = base + ".json", 1
    while os.path.isfile(os.path.join(STAGING, nom)):   # deux ticks a la seconde
        n += 1
        nom = "{}-{}.json".format(base, n)
    chemin = ecrire_proposition(nom, prop)
    resumer(prop, chemin)
    return 0


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Moteur arithmetique du hors-scene (lit etat/, "
                    "n'ecrit que dans etat/)")
    ap.add_argument("--verifier", action="store_true",
                    help="audit de coherence de etat/ (code 1 si anomalie)")
    ap.add_argument("--json", dest="en_json", action="store_true",
                    help="avec --verifier : l'audit en JSON, pour /admin/sante")
    ap.add_argument("--jours", type=int,
                    help="taille de la fenetre depuis monde.date")
    ap.add_argument("--jusqu-a", dest="jusqu_a", metavar="129.3.20",
                    help="date cible de la fenetre")
    ap.add_argument("--acteur", action="append", default=[], metavar="ID",
                    help="restreint le calcul a cet acteur (repetable)")
    ap.add_argument("--joueur", default=None, metavar="ID",
                    help="personnage_id dont les croyances (jetons, vues, "
                         "objectifs) seront scellees et appliquees. Inscrit "
                         "dans la proposition ; appliquer.py le reprend.")
    args = ap.parse_args()

    e = Etat()

    if args.verifier:
        if args.jours is not None or args.jusqu_a:
            sys.exit("--verifier ne se combine pas avec --jours / --jusqu-a")
        return verifier(e, args.en_json)

    if args.jours is not None and args.jusqu_a:
        sys.exit("choisir --jours OU --jusqu-a, pas les deux")
    if args.jours is not None:
        if args.jours < 0:
            sys.exit("--jours doit etre positif")
        cible = date_de(e.aujourdhui + args.jours)
    elif args.jusqu_a:
        cible = lire_date(args.jusqu_a)
    else:
        ap.print_help()
        return 0

    return tick(e, cible, set(args.acteur), args.joueur)


if __name__ == "__main__":
    sys.exit(main())
