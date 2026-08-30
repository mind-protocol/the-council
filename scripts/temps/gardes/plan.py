# -*- coding: utf-8 -*-
"""GARDES DU PLAN — les tetes, les mains, les couts, et les producteurs.

CE QUE CE MODULE POSSEDE : les verificateurs de ce qui FAIT AVANCER le jeu —
les intentions (une tete par actif, budgets, retards, dependances), les mains
(l'arithmetique doit pouvoir etre juste), les couts chiffres, la colonne
d'etat du plan (six mots, pas un de plus), et les rapporteurs (un producteur
muet depuis sa cadence est une panne, jamais une statistique).

CE QU'IL REFUSE : ecrire, reparer, ou juger le contenu narratif.

CONSOMMATEURS : gardes/__init__.py (verifier() les appelle dans l'ordre).
"""
import collections
import json
import os
import sys

from temps.calendrier import jour_absolu, fmt
from temps.bouche import BUDGETS, TOLERANCE_MAJ, echelle_de, etapes_de
from temps.mains import couts_chiffres, seuil_franchi
from temps.rumeur import temoins_des_incidents, cycles


def verifier_intentions(e, r):
    """Une tete par actif, une seule, dans les budgets, a jour."""
    vues = set()
    ids_etapes = {}          # id d'etape -> [personnage_id]
    depend = {}              # id d'etape -> [ids requis]

    for tete in e.intentions:
        pid = tete.get("personnage_id")
        if not pid:
            r.dire("grave", "intentions",
                   "entree sans personnage_id : {}".format(
                       json.dumps(tete, ensure_ascii=False)[:80]))
            continue
        if pid in vues:
            r.dire("grave", pid, "deux entrees d'intentions pour ce personnage")
        vues.add(pid)

        if pid in e.sieges_occupes:
            r.dire("grave", pid,
                   "siege OCCUPE avec une entree dans intentions.json — "
                   "sa tete appartient au joueur, elle doit disparaitre")
        perso = e.perso_par_id.get(pid)
        if perso is None:
            r.dire("grave", pid, "tete pour un personnage inconnu de "
                                 "personnages.json")
        elif perso.get("etat") == "mort":
            r.dire("grave", pid, "tete pour un personnage mort")
        elif perso.get("etat") != "actif":
            r.dire("avertissement", pid,
                   "tete pour un personnage {} — actif ou rien".format(
                       perso.get("etat")))

        # L'ECHELLE NE SE DECLARE PLUS : elle se mesure sur la topologie. Un
        # champ `echelle` qui traine est un reste de l'ancien systeme, et il
        # ment des que l'homme a bouge — on le signale pour qu'on le retire.
        if tete.get("echelle") is not None:
            r.dire("avertissement", pid,
                   "champ `echelle` perime — l'echelle se mesure desormais sur "
                   "le quartier (docs/boucle-acteurs.md), retire-le")
        budget = BUDGETS[echelle_de(tete)]
        ech_dite = echelle_de(tete)

        n_croyances = len(tete.get("croyances") or [])
        if n_croyances > budget["croyances"]:
            r.dire("avertissement", pid,
                   "{} croyances pour un budget de {} ({})".format(
                       n_croyances, budget["croyances"], ech_dite))

        plan = tete.get("plan") or []
        chaines = [p for p in plan if not isinstance(p, dict)]
        if chaines:
            r.dire("avertissement", pid,
                   "{}/{} etape(s) de plan encore en simple texte, sans "
                   "horloge ni cout ni si_bloque".format(len(chaines),
                                                         len(plan)))
        etapes = etapes_de(tete)
        vivantes = [x for x in etapes
                    if x.get("etat") in ("en-cours", "bloque")]
        if len(vivantes) > budget["etapes"]:
            r.dire("avertissement", pid,
                   "{} etapes vivantes pour un budget de {} ({})".format(
                       len(vivantes), budget["etapes"], ech_dite))

        decl = tete.get("declencheurs") or []
        if len(decl) > budget["declencheurs"]:
            r.dire("avertissement", pid,
                   "{} declencheurs pour un budget de {} ({})".format(
                       len(decl), budget["declencheurs"], ech_dite))
        for i, d in enumerate(decl):
            if not isinstance(d, dict) or not d.get("si") or not d.get("alors"):
                r.dire("grave", pid,
                       "declencheur #{} sans 'si' ou sans 'alors'".format(i + 1))

        for etape in etapes:
            eid = etape.get("id")
            if not eid:
                r.dire("grave", pid, "etape sans id : {!r}".format(
                    str(etape.get("quoi"))[:60]))
                continue
            ids_etapes.setdefault(eid, []).append(pid)
            depend[eid] = [x for x in (etape.get("depend_de") or [])]
            if etape.get("etat") == "en-cours" and "jours_restants" not in etape:
                r.dire("avertissement", pid,
                       "etape '{}' en-cours sans horloge (mettre un entier, "
                       "ou null pour une posture permanente)".format(eid))

        # tete en retard : date_maj trop vieille pour son echelle
        maj = jour_absolu(tete.get("date_maj"))
        if maj is None:
            r.dire("avertissement", pid, "date_maj absente ou illisible")
        else:
            retard = e.aujourdhui - maj
            toleree = TOLERANCE_MAJ[ech_dite]
            if retard > toleree:
                r.dire("avertissement", pid,
                       "tete en retard de {} jours (maj {}, monde {}, "
                       "tolerance {} en {})".format(retard, fmt(tete["date_maj"]),
                                                    fmt(e.date), toleree,
                                                    ech_dite))

    # actifs sans tete NI mains. Un actif sans tete n'est plus une anomalie
    # depuis mains.json : c'est un homme qui n'a rien a decider et dont
    # l'affaire tourne toute seule. Ce qui reste faux, c'est l'actif qui n'a
    # ni l'un ni l'autre — celui-la est un dormant qui s'ignore.
    porteurs = {(a.get("porteur") or {}).get("id") for a in e.mains
                if (a.get("porteur") or {}).get("type") == "personnage"}
    # Un temoin est un porteur legitime SANS tete : il n'a pas de projet, il a
    # vu quelque chose et il le raconte. Ne rien lui reprocher pour autant.
    temoins = temoins_des_incidents(e)
    # Quatrieme facon d'exister sans rien decider : avoir une PLACE DANS LA
    # JOURNEE (etat/routines.json). Un coureur, un garde, une fille de cuisine
    # ne poursuivent aucun plan et ne comptent aucun stock — ils tiennent un
    # poste, et le chateau tourne parce qu'ils y sont. Sans routine, en
    # revanche, un actif reste fige la ou une vieille scene l'a laisse : c'est
    # ca, le vrai defaut que ce controle doit attraper.
    for perso in e.personnages:
        pid = perso.get("id")
        if perso.get("etat") != "actif" or pid in e.sieges_occupes:
            continue
        if (pid not in vues and pid not in porteurs and pid not in temoins
                and pid not in e.routines):
            r.dire("avertissement", pid,
                   "personnage actif sans tete, ni mains, ni temoignage, ni "
                   "place dans la journee — "
                   "donne-lui une entree dans intentions.json (il decide) ou "
                   "dans mains.json (son affaire tourne seule), ou repasse-"
                   "le dormant")

    # ids d'etapes dupliques
    for eid, porteurs in sorted(ids_etapes.items()):
        if len(porteurs) > 1:
            r.dire("grave", "intentions",
                   "id d'etape '{}' porte {} fois ({})".format(
                       eid, len(porteurs), ", ".join(porteurs)))

    # depend_de pendants
    for eid, requis in sorted(depend.items()):
        for req in requis:
            if req not in ids_etapes:
                r.dire("grave", "intentions",
                       "etape '{}' depend de '{}', qui n'existe pas".format(
                           eid, req))

    # cycles de dependances
    for cycle in cycles(depend):
        r.dire("grave", "intentions",
               "cycle de dependances : {}".format(" -> ".join(cycle)))

    # PLUS DE PLAFOND D'ACTEURS, et c'est le point : ce n'est pas le NOMBRE de
    # tetes qui coute, c'est ou elles sont. Vingt tetes au loin pesent moins que
    # huit dans la salle. Ce qui borne le jeu n'est plus un quota pose a la
    # main, c'est le quartier — il se resserre tout seul sur ce que le joueur
    # peut atteindre. On rend donc le compte pour qu'on le voie, sans le juger.
    par_ech = collections.Counter(echelle_de(t) for t in e.intentions)
    r.dire("note", "intentions",
           "{} tete(s) dans le quartier, {} au loin".format(
               par_ech.get("quartier", 0), par_ech.get("au loin", 0)))


def verifier_mains(e, r):
    """Les mains : ce qui empeche l'arithmetique d'etre juste."""
    vus = set()
    for act in e.mains:
        aid = act.get("id")
        etiq = "main {}".format(aid or "?")
        if not aid:
            r.dire("grave", etiq, "main sans id")
            continue
        if aid in vus:
            r.dire("grave", etiq, "id d'main en double")
        vus.add(aid)

        p = act.get("porteur") or {}
        if p.get("type") == "personnage":
            perso = e.perso_par_id.get(p.get("id"))
            if perso is None:
                r.dire("grave", etiq,
                       "porteur inconnu : {!r}".format(p.get("id")))
            elif perso.get("etat") == "mort":
                r.dire("avertissement", etiq,
                       "le porteur {} est mort — l'affaire ne remonte plus "
                       "rien, et c'est peut-etre voulu".format(p.get("id")))
        elif p.get("type") == "lieu" and p.get("id") and not e.lieu(p["id"]):
            r.dire("grave", etiq, "lieu porteur inconnu : {!r}".format(p["id"]))
        elif not p.get("type"):
            r.dire("avertissement", etiq, "aucun porteur declare")

        if act.get("lieu_id") and not e.lieu(act["lieu_id"]):
            r.dire("grave", etiq,
                   "lieu_id inconnu : {!r}".format(act["lieu_id"]))

        mesures = act.get("mesure") or []
        if not mesures:
            r.dire("grave", etiq, "aucune mesure — une main sans compteur "
                                  "ne produit rien et ne sert a rien")
        if len(mesures) > 3:
            r.dire("avertissement", etiq,
                   "{} mesures (3 au plus) — decoupe l'affaire en deux"
                   .format(len(mesures)))

        ids_mesure = set()
        for mes in mesures:
            mid = mes.get("id")
            sous = "{} / {}".format(etiq, mid or "?")
            if not mid:
                r.dire("grave", sous, "mesure sans id")
                continue
            if mid in ids_mesure:
                r.dire("grave", sous, "id de mesure en double dans l'main")
            ids_mesure.add(mid)

            if not isinstance(mes.get("valeur"), int):
                r.dire("grave", sous, "valeur absente ou non entiere — tout "
                                      "est en entiers, jamais en flottants")
            rythme = mes.get("rythme")
            if not isinstance(rythme, dict):
                r.dire("grave", sous, "rythme absent : la mesure ne bougera "
                                      "jamais")
            else:
                par, pas = rythme.get("par"), rythme.get("jours", 1)
                if not isinstance(par, int):
                    r.dire("grave", sous, "rythme.par non entier")
                if not isinstance(pas, int) or pas <= 0:
                    r.dire("grave", sous, "rythme.jours doit etre un entier > 0")
                elif not isinstance(mes.get("reliquat", 0), int) or \
                        not 0 <= mes.get("reliquat", 0) < pas:
                    r.dire("avertissement", sous,
                           "reliquat hors de [0, {}[ — tick.py le remettra "
                           "droit au prochain calcul".format(pas))
            bas, haut = mes.get("plancher"), mes.get("plafond")
            if isinstance(bas, int) and isinstance(haut, int) and bas > haut:
                r.dire("grave", sous, "plancher au-dessus du plafond")
            for d in mes.get("depend_de") or []:
                if d not in e.mesure_par_adresse:
                    r.dire("grave", sous,
                           "depend_de pointe dans le vide : {!r}".format(d))

        for seuil in act.get("seuils") or []:
            sid = seuil.get("id")
            sous = "{} / seuil {}".format(etiq, sid or "?")
            if seuil.get("mesure_id") not in ids_mesure:
                r.dire("grave", sous, "mesure_id inconnu dans cette main : "
                                      "{!r}".format(seuil.get("mesure_id")))
            if seuil.get("quand") not in ("sous", "sur"):
                r.dire("grave", sous, "'quand' doit valoir 'sous' ou 'sur'")
            if not isinstance(seuil.get("valeur"), int):
                r.dire("grave", sous, "valeur de bascule non entiere")
            if seuil.get("promeut") not in ("orbite", "scene"):
                r.dire("grave", sous, "'promeut' doit valoir 'orbite' ou 'scene'")
            if not seuil.get("affaire"):
                r.dire("avertissement", sous,
                       "aucune 'affaire' ecrite a froid — le jour ou le seuil "
                       "saute, tu improviseras la bifurcation")

            # un seuil franchi doit avoir donne une tete au porteur ;
            # un seuil retombe ne doit plus en couter une.
            if p.get("type") != "personnage" or not p.get("id"):
                continue
            tete = e.intention_par_id.get(p["id"])
            mes = next((m for m in mesures
                        if m.get("id") == seuil.get("mesure_id")), None)
            if mes is None or not isinstance(mes.get("valeur"), int):
                continue
            encore = seuil_franchi(mes["valeur"], seuil)
            if seuil.get("franchi_le") and tete is None:
                r.dire("grave", sous,
                       "seuil franchi le {} et {} n'a toujours pas de tete en "
                       "'{}' — la crise ne se joue nulle part".format(
                           seuil["franchi_le"], p["id"], seuil.get("promeut")))
            elif seuil.get("franchi_le") and not encore:
                r.dire("avertissement", sous,
                       "la mesure est repassee du bon cote mais franchi_le "
                       "tient toujours — remets-le a null")
            elif not seuil.get("franchi_le") and encore:
                r.dire("avertissement", sous,
                       "la mesure est du mauvais cote sans que franchi_le soit "
                       "pose — le prochain tick le posera")


def verifier_couts_chiffres(e, r):
    """Un cout d'etape qui cite une mesure doit citer une mesure qui existe."""
    for tete in e.intentions:
        for etape in etapes_de(tete):
            for c in couts_chiffres(etape):
                if c["mesure"] not in e.mesure_par_adresse:
                    r.dire("grave", "{} / {}".format(
                        tete.get("personnage_id"), etape.get("id")),
                        "cout cite une mesure inconnue : {!r}".format(
                            c["mesure"]))
                elif not isinstance(c.get("quantite"), int):
                    r.dire("avertissement", "{} / {}".format(
                        tete.get("personnage_id"), etape.get("id")),
                        "cout chiffre sans 'quantite' entiere : {!r}".format(
                            c["mesure"]))


def verifier_etats_du_plan(e, r):
    """La colonne d'etat d'une action ne porte QU'UN MOT, pris dans six.

    Elle a ete un champ de recit pendant une lune : deux cents signes de prose
    datee la ou `etat_du_plan.py` attend un mot, dix-sept pieces ecrivant
    « fait » de six facons, et la date de realisation noyee dans le texte —
    donc rien qui se compte, donc personne capable de dire ce qui a ete fait
    cette lune. Sans cette garde, la prose y revient en trois jours : elle
    revient toujours, parce qu'un homme qui a quelque chose a dire l'ecrit la
    ou il regarde. Ce qu'il a a dire va desormais en `📝 Note`, et la date en
    `📅 Jour fait`.
    """
    try:
        from plan.expose import couverture
    except ImportError:
        return
    VOC = (u"\u00e0 faire", u"en cours", u"bloqu\u00e9e", u"faite", u"close",
           u"abandonn\u00e9e")
    for livre in e.books:
        bid = str(livre.get("id") or "")
        if not bid.startswith(("affaire-", "nera-")):
            continue
        for t in (livre.get("tables") or []):
            g = (couverture.genre_de((t or {}).get("titre") or "")
                 or couverture.genre_de(livre.get("titre") or ""))
            if g != "action":
                continue
            cols = (t or {}).get("colonnes") or []
            i = couverture.col(cols, u"^\u00e9tat$|^etat$|o\u00f9 \u00e7a en est|ou ca en est")
            if i is None:
                continue
            for ligne in (t.get("lignes") or []):
                c = [couverture.nu(x) for x in ((ligne if isinstance(ligne, list)
                                                 else (ligne or {}).get("cellules")) or [])]
                if len(c) < 2 or not c[0] or not c[1] or i >= len(c):
                    continue
                m = couverture.NUM.search(c[0])
                if not m or c[i] in VOC:
                    continue
                r.dire("grave", "plan {}".format(m.group(1)),
                       "etat hors vocabulaire : {!r}. Six valeurs et pas une de "
                       "plus — a faire / en cours / bloquee / faite / close / "
                       "abandonnee. La prose va en « Note », la date en « Jour "
                       "fait » : `python scripts/plan/normaliser_etats.py`"
                       .format(c[i][:70]))


def verifier_rapporteurs(e, r):
    """Le seul verificateur qui ne regarde pas l'etat : il regarde LES AUTRES.

    « Le derive a derive » et « le producteur est mort » sont deux faits
    differents, et le second est le seul invisible. Le 24 aout 2026,
    `couverture.py` etait mort depuis des jours — un `re.search` sans bornes de
    mot, un KeyError — et les quatre registres derives du plan avaient cesse
    d'etre regeneres. La garde `verifier_registres_derives` faisait pourtant son
    travail : elle signalait l'ecart de lignes. Mais elle le disait en
    AVERTISSEMENT, au milieu de quatre-vingt-dix autres, et quand elle-meme
    n'arrivait pas a recalculer elle le disait en NOTE, la severite la plus
    basse du rapport. Un outil qui se tait ressemble exactement a un outil qui
    n'a rien a dire.

    D'ou cette garde-ci, et sa gravite : un ecart de lignes peut etre normal —
    on vient d'ecrire dans un cahier sans avoir relance. UN PRODUCTEUR QUI N'A
    PAS ABOUTI DEPUIS SA CADENCE NE L'EST JAMAIS. Le battement se pose a la fin
    du chemin de succes (voir scripts/noyau/rapporteurs.py) ; un script qui plante ne
    bat pas, et l'absence de battement est tout le mecanisme.

    Les cadences sont en JOURS REELS et non en jours de jeu : ce sont des
    cadences d'outillage, elles se comptent en temps de developpeur.
    """
    try:
        from plan.expose import rapporteurs
    except ImportError:
        return
    try:
        lignes = rapporteurs.etat()
    except Exception as mal:
        r.dire("grave", "rapporteurs",
               "le registre des battements est illisible : {} — plus personne ne "
               "surveille les producteurs derives".format(mal))
        return
    for x in lignes:
        if not x["muet"]:
            continue
        if x["age"] is None:
            r.dire("grave", "rapporteur {}".format(x["qui"]),
                   "N'A JAMAIS BATTU. {} — nul ne sait s'il tourne encore. "
                   "`{}`".format(x["quoi"], x["commande"]))
        else:
            r.dire("grave", "rapporteur {}".format(x["qui"]),
                   "MUET DEPUIS {:.0f} JOUR(S), cadence {} — {} n'est donc plus "
                   "a jour, et rien d'autre ne le dit. `{}`"
                   .format(x["age"], x["jours"], x["quoi"], x["commande"]))
