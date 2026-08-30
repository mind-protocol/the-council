# -*- coding: utf-8 -*-
"""FENETRE — ce qui tombe entre monde.date et la cible. Aucune decision.

CE QUE CE MODULE POSSEDE : le calcul de la fenetre, eclate en PHASES nommees
d'apres les sections de l'ancien calculer() — les commentaires de section sont
devenus leurs docstrings, on n'a pas perdu une ligne de pourquoi. calculer()
n'est plus qu'un sommaire qui les appelle dans l'ordre :

    les mains d'abord, acteurs simules, evenements a resoudre, nouvelles a
    livrer, le courrier, etapes, la bouche, la rumeur, declencheurs, tetes en
    retard, mutations proposees, les pensees.

Et tick() : la cible n'avance que dans un sens, la proposition s'ecrit dans
etat/tick-<horodatage>.json, le resume s'imprime.

Regles de calcul (ce que docs/schema.md ne tranche pas l'est ici, au plus
simple) :
- Budget d'etapes : on compte le plan VIVANT (etapes `en-cours` ou `bloque`).
  Une etape `fait` ou `abandonne` ne charge plus la tete.
- Une etape dont `jours_restants` vaut null est une posture permanente : elle
  ne tombe jamais, ne se decompte jamais, et n'apparait dans aucun des trois
  paniers d'etapes (seulement dans le compte du resume).
- Une etape dont un `depend_de` n'est pas `fait` voit son horloge arretee :
  elle passe en attente, sans consommer les jours de la fenetre.
- Retard tolere d'une tete avant rafraichissement : 1 jour (quartier),
  15 jours (au loin).
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

CE QU'IL REFUSE : decider. Il lit etat/ et n'ecrit qu'une PROPOSITION sous
etat/ : le MJ seul relit, arbitre et applique (scripts/appliquer.py).

CONSOMMATEURS : la facade scripts/tick.py (--jours / --jusqu-a).
"""
import os
import sys
from datetime import datetime

from temps.calendrier import jour_absolu, date_de, fmt
from temps.bouche import TOLERANCE_MAJ, FENETRE_ROYAUME, echelle_de, etapes_de
from temps.mains import (rythme_de, au_plancher, decompter, porteur_absent,
                         chiffrer_cout, seuil_franchi)
from temps.rumeur import detecter_bouches, propager_rumeurs
from temps import mutations
from temps.scelle import STAGING, empreintes_etat, ecrire_proposition
from temps.gardes.ecrits import qui_a_du_temps
from temps.resume import resumer


def _phase_mains(e, jours, cible):
    """LES MAINS D'ABORD (docs/schema.md : mains.json).

    La boucle des mains tourne AVANT celle des absents, parce que sa
    sortie est son entree : un `cout` d'etape qui cite une adresse de mesure
    se verifie contre la valeur d'APRES decompte, pas celle d'avant.

    Rend (mains, franchissements, mesures_apres) — mesures_apres est
    l'index adresse -> valeur apres la fenetre.
    """
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
    return mains, franchissements, mesures_apres


def _phase_acteurs(e, restriction, jours):
    """Quels acteurs on simule. Rend (simules, sautes)."""
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
    return simules, sautes


def _phase_evenements(e, fin):
    """Les evenements a resoudre dans la fenetre, en retard compris."""
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
    return a_resoudre


def _phase_nouvelles(e, fin):
    """Les nouvelles a livrer.

    Le statut de l'evenement commande : on ne livre que ce qui a EU LIEU.
      resolu   -> livrable
      a-venir  -> conditionnel, l'echeance tombe dans la fenetre mais le MJ
                  n'a pas encore arbitre : la nouvelle ne part qu'apres
      devie / annule -> jamais. La chose ne s'est pas produite.

    Rend (nouvelles, conditionnelles).
    """
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
    return nouvelles, conditionnelles


def _phase_courrier(e, fin):
    """LE COURRIER : ce qui arrive (docs/plis.md).

    Rien n'atteint personne sans porteur. Un pli echu est REMIS, dans la main
    du destinataire naturel du lieu — le mestre —, jamais dans celle du `pour`.

    Rend (plis_remis, plis_en_route).
    """
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
    return plis_remis, plis_en_route


def _phase_etapes(e, simules, sautes, jours, mesures_apres):
    """Les etapes : tombent, avancent, ou attendent.

    Un cout peut CITER une mesure : {mesure, quantite}. Alors il se verifie
    ici, contre la valeur d'apres decompte, et le si_bloque se declenche par
    arithmetique. Un cout en clair reste au MJ.

    Un acteur 'royaume' n'est pas rafraichi sur une fenetre courte, mais une
    echeance ne se perd jamais : le coffre d'or promis pour demain tombe
    demain, meme si la tete de celui qui l'apporte n'est pas repassee en revue.

    Rend (tombent, avancent, attendent, postures).
    """
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
    return tombent, avancent, attendent, postures


def _phase_declencheurs(simules):
    """Les declencheurs a evaluer (le MJ seul juge)."""
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
    return declencheurs


def _phase_retards(simules, fin):
    """Les tetes en retard une fois la fenetre franchie."""
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
    return rafraichir


def calculer(e, cible, restriction, joueur=None):
    """Ce qui tombe entre monde.date et cible. Aucune decision, du calcul."""
    fin = jour_absolu(cible)
    jours = fin - e.aujourdhui
    fenetre = {"de": e.date, "a": cible, "jours": jours}

    # --- LES MAINS D'ABORD (docs/schema.md : mains.json)
    mains, franchissements, mesures_apres = _phase_mains(e, jours, cible)

    # --- quels acteurs on simule
    simules, sautes = _phase_acteurs(e, restriction, jours)

    # --- evenements a resoudre
    a_resoudre = _phase_evenements(e, fin)

    # --- nouvelles a livrer
    nouvelles, conditionnelles = _phase_nouvelles(e, fin)

    # --- LE COURRIER : ce qui arrive (docs/plis.md)
    plis_remis, plis_en_route = _phase_courrier(e, fin)

    # --- etapes : tombent, avancent, ou attendent
    tombent, avancent, attendent, postures = _phase_etapes(
        e, simules, sautes, jours, mesures_apres)

    # --- LA BOUCHE : qui arrive, et ce qu'il apporte que personne ne sait ici
    bouches = detecter_bouches(e, a_resoudre, tombent)

    # --- LA RUMEUR : ce qui saute de proche en proche, sans porteur nomme
    rumeurs, rumeurs_immobiles = propager_rumeurs(e, fin, cible)

    # --- declencheurs a evaluer (le MJ seul juge)
    declencheurs = _phase_declencheurs(simules)

    # --- tetes en retard une fois la fenetre franchie
    rafraichir = _phase_retards(simules, fin)

    # --- mutations proposees : STRICTEMENT ce qui est arithmetique
    muts = mutations.rediger(mains, franchissements, avancent, plis_remis,
                             rumeurs, nouvelles, jours, cible)

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
        "mutations_proposees": muts,
    }


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
