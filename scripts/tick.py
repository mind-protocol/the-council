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

GRAVITES = ("grave", "avertissement", "note")

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

class Rapport(object):
    def __init__(self):
        self.anomalies = []

    def dire(self, gravite, sujet, texte):
        # `imprimer` ne parcourt que GRAVITES : une gravite mal orthographiee
        # disparaissait sans un mot, et l'audit se croyait propre. On refuse
        # bruyamment plutot que de perdre l'anomalie.
        if gravite not in GRAVITES:
            raise ValueError(
                "gravite inconnue {!r} pour [{}] — attendu {}".format(
                    gravite, sujet, ", ".join(GRAVITES)))
        self.anomalies.append({"gravite": gravite, "sujet": sujet,
                               "texte": texte})

    def imprimer_json(self):
        # Meme audit, servi a l'ecran au lieu du terminal : `--verifier --json`
        # alimente /admin/sante. Le texte reste la source, on ne le reformate
        # pas — un panneau qui dit autre chose que le terminal ne vaut rien.
        durs = [a for a in self.anomalies if a["gravite"] != "note"]
        print(json.dumps({
            "anomalies": self.anomalies,
            "durs": len(durs),
            "notes": len(self.anomalies) - len(durs),
            "par_gravite": {g: len([a for a in self.anomalies
                                    if a["gravite"] == g]) for g in GRAVITES},
        }, ensure_ascii=False))

    def imprimer(self):
        durs = [a for a in self.anomalies if a["gravite"] != "note"]
        print("Audit de etat/ — {} anomalie(s){}".format(
            len(durs),
            " + {} note(s) informative(s)".format(
                len(self.anomalies) - len(durs))
            if len(durs) != len(self.anomalies) else ""))
        if not self.anomalies:
            print("  rien a signaler.")
            return
        for gravite in GRAVITES:
            lot = [a for a in self.anomalies if a["gravite"] == gravite]
            if not lot:
                continue
            print("\n== {} ({}) ==".format(gravite.upper(), len(lot)))
            for a in lot:
                print("  [{}] {}".format(a["sujet"], a["texte"]))


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


# ------------------------------------------------------------- LA RUMEUR
# Demenage dans temps/rumeur.py (decoupage du container temps).

from temps.rumeur import (temoins_des_incidents,  # noqa: E402,F401
                          rang_certitude, degrader, relais_de,
                          saut_rumeur, propager_rumeurs, sans_accents,
                          lieu_cite, detecter_bouches, cycles)


def verifier_evenements(e, r):
    """Echeances passees, diffusion en retard, lieux inconnus."""
    for ev in e.evenements:
        eid = ev.get("id", "?")
        if ev.get("lieu_id") and not e.lieu(ev["lieu_id"]):
            r.dire("grave", eid, "lieu_id inconnu : {!r}".format(ev["lieu_id"]))

        prevue = jour_absolu(ev.get("date_prevue"))
        if prevue is None:
            r.dire("grave", eid, "date_prevue absente ou illisible")
        elif ev.get("statut") == "a-venir" and prevue < e.aujourdhui:
            r.dire("avertissement", eid,
                   "encore 'a-venir' alors que son echeance {} est passee "
                   "(monde {}) — retard du moteur".format(
                       fmt(ev["date_prevue"]), fmt(e.date)))

        for i, ent in enumerate(ev.get("diffusion") or []):
            etiq = "{} / diffusion #{}".format(eid, i + 1)
            if not isinstance(ent, dict):
                r.dire("grave", etiq, "entree de diffusion illisible")
                continue
            ou, qui = ent.get("ou"), ent.get("qui") or []
            if not ou and not qui:
                r.dire("grave", etiq,
                       "ni 'ou' ni 'qui' — il faut au moins l'un des deux")
            if ou and not e.lieu(ou):
                r.dire("grave", etiq, "'ou' inconnu : {!r}".format(ou))
            for pid in qui:
                if pid not in e.perso_par_id:
                    r.dire("grave", etiq, "'qui' inconnu : {!r}".format(pid))
            quand = jour_absolu(ent.get("date"))
            if quand is None:
                r.dire("grave", etiq, "date absente ou illisible")
            elif quand <= e.aujourdhui and ent.get("livree") is not True:
                r.dire("avertissement", etiq,
                       "nouvelle due le {} et toujours pas livree "
                       "(monde {})".format(fmt(ent["date"]), fmt(e.date)))


def verifier_personnages(e, r):
    for perso in e.personnages:
        lid = perso.get("lieu_id")
        if lid and not e.lieu(lid):
            r.dire("grave", perso.get("id", "?"),
                   "lieu_id inconnu : {!r}".format(lid))


# `tenu_par` n'est PAS une place : c'est la main qui repond du volume. Un
# `acteur_id` deplace le livre avec son porteur ; `tenu_par` le laisse ou il
# est — sur la Table Peinte — et dit seulement sur quelle epaule il tombe.
# C'est ce qui permet de ranger un coffret de trente-sept affaires par homme
# au lieu d'une liste ou personne ne retrouve les siennes.
#
# `office` va avec, et ne fait pas double emploi : `tenu_par` dit QUI, `office`
# dit SOUS QUELLE CHARGE. Ser Robert en tient trois, Aldon Hask trois aussi —
# savoir qu'un cahier tombe sur lui ne dit pas encore de quel chapeau il le
# porte, ni quel sceau on regarde si l'affaire tourne mal.
CLES_BOOK = {"id", "lieu_id", "salle_id", "acteur_id", "boite", "prive",
             "lecteurs", "titre", "sous_titre", "type", "couleur", "embleme",
             "date_maj", "colonnes", "lignes", "pages", "tables", "tenu_par",
             "office"}

# Un coffret : etat/boites.json. Ni genre, ni colonnes, ni pages — une boite
# ne se lit pas, elle se pose et elle s'ouvre.
CLES_BOITE = {"id", "lieu_id", "salle_id", "acteur_id", "prive", "lecteurs",
              "titre", "sous_titre", "couleur", "embleme"}

# Les genres de volume connus de ecrans/modules/books.js. Un type inventé ne
# casse rien — le livre s'affiche sans teinte — mais il ne donne pas la couleur
# qu'on croyait avoir demandée.
TYPES_BOOK = {"registre", "carnet", "plan", "memento", "dossier", "regle",
              "oeuvre"}


def verifier_pensees(e, r):
    """PAS DE SOURCE, PAS DE PENSEE — la seule regle de l'ancien systeme qui
    meritait de survivre, et la seule qu'on verifie encore.

    Ce qu'on ne verifie plus, et pourquoi : l'excitation (un compteur qui
    montait sans sources et retombait d'un point par jour), le seuil de parole
    a 3, l'etat `mur` d'une conclusion, le marquage `servie` (11 pensees
    marquees sur 613 — il n'etait pas tenu et faisait croire a 98 % de perte).
    """
    connus = {p.get("id") for p in e.personnages if isinstance(p, dict)}
    sans_source = sans_date = inconnus = 0
    for p in getattr(e, "pensees", []) or []:
        if not isinstance(p, dict):
            continue
        if not (p.get("source") or "").strip():
            sans_source += 1
        if not p.get("date"):
            sans_date += 1
        if p.get("qui") and p.get("qui") not in connus:
            inconnus += 1
    if sans_source:
        r.dire("avertissement", "pensees",
               "{} pensee(s) sans source — une pensee qui ne vient de rien "
               "a ete inventee au moment de l'ecrire".format(sans_source))
    if sans_date:
        r.dire("avertissement", "pensees",
               "{} pensee(s) sans date".format(sans_date))
    if inconnus:
        r.dire("avertissement", "pensees",
               "{} pensee(s) attribuees a un inconnu de personnages.json"
               .format(inconnus))

    # UNE JOURNEE ENTIEREMENT FERMEE CHEZ UN HOMME FORT : il ne pensera jamais.
    # C'est peut-etre voulu — c'est le cout d'un mandat — mais il faut le voir.
    try:
        from temps.expose import presence
        q = presence.quartier()
        if q.get("vide"):
            r.dire("grave", "quartier",
                   "QUARTIER VIDE ({}) : personne ne pense et personne ne "
                   "bouge. Verifie horloges.json et presence.json."
                   .format(q["vide"]))
            return
        routines, chemins, _ = presence.charger()
        chateau = presence.Chateau(chemins)
        fiches, pj = (routines.get("gens") or {}), presence.joueurs()
        # Une ancre hors topologie n'ancre rien et se tait : le siege est
        # occupe, sa salle existe dans la fiction, et son quartier est vide.
        for a in q.get("ancres") or []:
            if a.get("hors_plan"):
                r.dire("grave", "quartier",
                       "{} est en '{}', salle absente de chemins.json : ce "
                       "siege n'atteint PERSONNE et son quartier est vide"
                       .format(a["qui"], a["salle"]))
        sans_routine, fermes = [], []
        for pid in q.get("dedans") or {}:
            if pid in pj:
                continue
            if pid not in fiches:
                sans_routine.append(pid)
            elif not presence.creux(pid, routines, chateau):
                fermes.append(pid)
        if sans_routine:
            r.dire("avertissement", "routines",
                   "{} tete(s) dans le quartier sans fiche de routine — leur "
                   "position retombera sur `perime`, c'est-a-dire inventee : {}"
                   .format(len(sans_routine), ", ".join(sorted(sans_routine))))
        if fermes:
            r.dire("note", "routines",
                   "{} journee(s) entierement fermees — ces hommes ne penseront "
                   "pas aujourd'hui : {}".format(len(fermes),
                                                 ", ".join(sorted(fermes))))
        # Une salle de routine absente de chemins.json rend des sauts nus a
        # cout zero, et c'est la faute qui mettait la cour verte dans la salle
        # de la reine.
        muettes = set()
        for pid, f in fiches.items():
            modele = (routines.get("modeles") or {}).get(f.get("modele")) or {}
            for b in modele.get("bandes") or []:
                s = presence.piece_de_bande(b, f, modele).get("salle")
                if s and not chateau.connait(s):
                    muettes.add(s)
        if muettes:
            r.dire("avertissement", "chemins",
                   "salle(s) de routine absentes de chemins.json (sauts nus a "
                   "cout 0) : {}".format(", ".join(sorted(muettes))))
    except Exception as exc:
        r.dire("avertissement", "quartier",
               "quartier incalculable : {}".format(str(exc)[:120]))


def qui_a_du_temps(e):
    """QUI DOIT UNE JOURNEE — ce que `convoquer.py` disait, mesure autrement.

    L'ancien le tirait d'un compteur d'excitation ; le neuf le tire de la
    journee elle-meme. Rendu dans la proposition du tick pour que le MJ sache
    qui depecher, apres les mains et avant la salle.
    """
    try:
        from temps.expose import presence
        from temps.expose import evaluer
        A, N = evaluer.lire_tissu()
        feuille = evaluer.force_narrative(A, N, lambda t="": None)
    except Exception as exc:
        return [{"erreur": str(exc)[:160]}]
    return [{"qui": l["qui"], "force": l["force"], "questions": l["questions"],
             "creux_total": l["creux_total"],
             "questions_posees": l["questions_posees"]}
            for l in feuille if l.get("questions")]


def verifier_books(e, r):
    """Les livres : ce qui les empeche de s'afficher, ou les fait doubler.

    Le module ecrans/modules/books.js ne lit QUE le format de docs/books.md.
    Une cle inventee ne fait pas d'erreur a l'ecran : elle est ignoree en
    silence, et le MJ croit avoir ecrit quelque chose qui n'existe pas.
    """
    vus, titres, emblemes = set(), {}, {}
    coffrets = set(c.get("id") for c in e.boites if isinstance(c, dict))
    for livre in e.books:
        bid = livre.get("id")
        etiq = "book {}".format(bid or "?")
        if not bid:
            r.dire("grave", etiq, "livre sans id")
            continue
        if bid in vus:
            r.dire("grave", etiq, "deux livres portent cet id")
        vus.add(bid)

        titre = (livre.get("titre") or "").strip().lower()
        if titre and titre in titres and titres[titre] != bid:
            r.dire("avertissement", etiq,
                   "meme titre que {!r} — deux onglets identiques a l'ecran ; "
                   "une session a sans doute recree ce que l'autre avait ecrit"
                   .format(titres[titre]))
        if titre:
            titres.setdefault(titre, bid)

        pose, porte = livre.get("salle_id"), livre.get("acteur_id")
        # Range dans un coffret : c'est LUI qui donne la place. Le volume n'a
        # donc plus de place a lui — et s'il en garde une, ce n'est pas un
        # doublon inoffensif : le serveur la remplace en silence, et l'on croit
        # avoir pose un registre la ou il n'est pas.
        boite = livre.get("boite")
        if boite:
            if boite not in coffrets:
                r.dire("grave", etiq, "boite inconnue : {!r} — ce livre n'est "
                                      "nulle part, il ne s'affichera jamais"
                                      .format(boite))
            propres = [k for k in ("salle_id", "acteur_id", "lieu_id", "prive")
                       if livre.get(k)]
            if propres:
                r.dire("grave", etiq,
                       "range dans une boite ET {} : la boite donne la place, "
                       "ces cles-la sont ecrasees en silence (voir docs/books.md)"
                       .format(", ".join(propres)))
        elif not pose and not porte:
            r.dire("grave", etiq, "ni salle_id ni acteur_id ni boite : ce livre "
                                  "n'est nulle part, il ne s'affichera jamais")
        if pose and porte:
            r.dire("grave", etiq, "salle_id ET acteur_id : un livre est pose "
                                  "ou porte, jamais les deux")
        if porte and not e.perso_par_id.get(porte):
            r.dire("grave", etiq, "acteur_id inconnu : {!r}".format(porte))

        # La main qui repond du volume. Elle ne le deplace pas — un cahier
        # d'affaire reste sur la table —, elle le RANGE : le coffret groupe ses
        # volumes par tenu_par. Un id faux ne casse rien a l'ecran, il fabrique
        # un homme de plus dans la liste, et c'est pire.
        tenu = livre.get("tenu_par")
        if tenu and not e.perso_par_id.get(tenu):
            r.dire("grave", etiq, "tenu_par inconnu : {!r}".format(tenu))
        if pose and livre.get("lieu_id") and not e.lieu(livre["lieu_id"]):
            r.dire("grave", etiq, "lieu_id inconnu : {!r}".format(livre["lieu_id"]))
        if pose and not livre.get("lieu_id"):
            r.dire("avertissement", etiq,
                   "salle_id sans lieu_id : le livre suivra le joueur de "
                   "chateau en chateau")

        # `prive` sans porteur ne reserve rien : un volume pose n'a pas de
        # proprietaire, et il s'ouvre a QUICONQUE entre dans le chateau. C'est
        # le piege silencieux du format — on marque un registre secret, on le
        # croit ferme, et les deux sieges de la maison le lisent. Le seul verrou
        # d'un volume pose, c'est `lecteurs`.
        lect = livre.get("lecteurs")
        if livre.get("prive") and not porte and not lect:
            r.dire("grave", etiq,
                   "prive sans acteur_id : un volume pose n'a pas de porteur, "
                   "donc ce prive ne ferme RIEN — tout le chateau l'ouvre. "
                   "Nomme ses lecteurs (voir docs/books.md)")
        if lect is not None:
            if not isinstance(lect, list) or not lect:
                r.dire("grave", etiq,
                       "lecteurs doit etre une liste non vide d'ids ; vide ou "
                       "mal formee, elle est ignoree et le livre s'ouvre a tous")
            else:
                for qui in lect:
                    if not e.perso_par_id.get(qui):
                        r.dire("grave", etiq,
                               "lecteurs : personnage inconnu {!r}".format(qui))

        # L'emblème et la teinte : on reconnaît un volume à sa forme avant de
        # lire son titre. Un livre neuf qui n'en a pas se noie dans trente
        # onglets gris — ce n'est pas une faute d'affichage, c'est une étagère
        # qu'on ne sait plus lire. Deux volumes sous le même signe se
        # confondent, ce qui est exactement le contraire du service rendu.
        emb = livre.get("embleme")
        if not emb:
            r.dire("avertissement", etiq,
                   "sans embleme : son onglet ne se reconnaitra qu'a la lecture")
        elif emb in emblemes:
            r.dire("avertissement", etiq,
                   "meme embleme {!r} que {!r} : deux onglets qu'on confondra"
                   .format(emb, emblemes[emb]))
        else:
            emblemes[emb] = bid
        if not livre.get("couleur"):
            r.dire("avertissement", etiq,
                   "sans couleur : il prendra la teinte de son genre, comme "
                   "tous ceux du meme type")

        genre = livre.get("type")
        if genre is not None and str(genre).lower() not in TYPES_BOOK:
            r.dire("avertissement", etiq,
                   "type inconnu : {!r} — le livre s'affichera sans teinte ; "
                   "genres connus : {} (voir docs/books.md)"
                   .format(genre, ", ".join(sorted(TYPES_BOOK))))

        inconnues = sorted(set(livre) - CLES_BOOK)
        if inconnues:
            r.dire("grave", etiq, "cles hors format, ignorees a l'ecran : {} "
                                  "(voir docs/books.md)".format(", ".join(inconnues)))

        # Un volume porte SOIT un tableau (colonnes/lignes), SOIT plusieurs
        # (tables[]). Une affaire en a plusieurs : ses etats cibles, ses verrous,
        # ses clefs et ses actions n'ont pas les memes colonnes.
        tables = livre.get("tables")
        if tables is not None and not isinstance(tables, list):
            r.dire("grave", etiq, "`tables` doit etre une liste de tableaux")
            tables = []
        if tables and (livre.get("colonnes") or livre.get("lignes")):
            r.dire("grave", etiq, "`tables` ET `colonnes`/`lignes` : le second "
                                  "couple ne sera pas affiche, choisissez")
        sections = ([{"titre": (t or {}).get("titre", ""),
                      "colonnes": (t or {}).get("colonnes") or [],
                      "lignes": (t or {}).get("lignes") or []} for t in (tables or [])]
                    or [{"titre": "", "colonnes": livre.get("colonnes") or [],
                         "lignes": livre.get("lignes") or []}])
        total = 0
        for s_i, sec in enumerate(sections, 1):
            ou = etiq if len(sections) == 1 else etiq + " tableau {}{}".format(
                s_i, " « " + sec["titre"] + " »" if sec["titre"] else "")
            colonnes, lignes = sec["colonnes"], sec["lignes"]
            total += len(lignes)
            if lignes and not colonnes:
                r.dire("avertissement", ou, "des lignes sans colonnes : le tableau "
                                            "s'affichera sans en-tete")
            for n, ligne in enumerate(lignes, 1):
                cellules = ligne if isinstance(ligne, list) else (ligne or {}).get("cellules")
                if cellules is None:
                    r.dire("grave", ou, "ligne {} sans `cellules`".format(n))
                    continue
                if colonnes and len(cellules) != len(colonnes):
                    r.dire("grave", ou,
                           "ligne {} : {} cellules pour {} colonnes"
                           .format(n, len(cellules), len(colonnes)))
        if not total and not (livre.get("pages") or [])                 and not any(s["colonnes"] for s in sections):
            r.dire("note", etiq, "livre vide : ni colonnes, ni lignes, ni pages")


def verifier_boites(e, r):
    """Les coffrets : ce qui les rend vides, doubles, ou ouverts a tous.

    Une boite ne se lit pas, elle se pose : ce qu'on verifie ici, c'est
    qu'elle est QUELQUE PART, qu'on la reconnait d'un coup d'oeil, et qu'elle
    ferme bien ce qu'elle a l'air de fermer.
    """
    vus, emblemes = set(), {}
    dedans = {}
    for livre in e.books:
        b = livre.get("boite")
        if b:
            dedans.setdefault(b, []).append(livre.get("id"))

    for boite in e.boites:
        bid = boite.get("id")
        etiq = "boite {}".format(bid or "?")
        if not bid:
            r.dire("grave", etiq, "coffret sans id")
            continue
        if bid in vus:
            r.dire("grave", etiq, "deux coffrets portent cet id")
        vus.add(bid)
        if not (boite.get("titre") or "").strip():
            r.dire("grave", etiq, "coffret sans titre : son onglet sera muet")

        pose, porte = boite.get("salle_id"), boite.get("acteur_id")
        if not pose and not porte:
            r.dire("grave", etiq, "ni salle_id ni acteur_id : ce coffret n'est "
                                  "nulle part, et rien de ce qu'il contient "
                                  "ne s'affichera")
        if pose and porte:
            r.dire("grave", etiq, "salle_id ET acteur_id : un coffret est pose "
                                  "ou porte, jamais les deux")
        if porte and not e.perso_par_id.get(porte):
            r.dire("grave", etiq, "acteur_id inconnu : {!r}".format(porte))
        if pose and boite.get("lieu_id") and not e.lieu(boite["lieu_id"]):
            r.dire("grave", etiq,
                   "lieu_id inconnu : {!r}".format(boite["lieu_id"]))
        if pose and not boite.get("lieu_id"):
            r.dire("avertissement", etiq,
                   "salle_id sans lieu_id : le coffret suivra le joueur de "
                   "chateau en chateau")

        lect = boite.get("lecteurs")
        if boite.get("prive") and not porte and not lect:
            r.dire("grave", etiq,
                   "prive sans acteur_id : un coffret pose n'a pas de porteur, "
                   "donc ce prive ne ferme RIEN — tout le chateau l'ouvre. "
                   "Nomme ses lecteurs (voir docs/books.md)")
        if lect is not None:
            if not isinstance(lect, list) or not lect:
                r.dire("grave", etiq,
                       "lecteurs doit etre une liste non vide d'ids ; vide ou "
                       "mal formee, elle est ignoree et le coffret s'ouvre a tous")
            else:
                for qui in lect:
                    if not e.perso_par_id.get(qui):
                        r.dire("grave", etiq,
                               "lecteurs : personnage inconnu {!r}".format(qui))

        emb = boite.get("embleme")
        if not emb:
            r.dire("avertissement", etiq,
                   "sans embleme : son onglet ne se reconnaitra qu'a la lecture")
        elif emb in emblemes:
            r.dire("avertissement", etiq,
                   "meme embleme {!r} que {!r} : deux onglets qu'on confondra"
                   .format(emb, emblemes[emb]))
        else:
            emblemes[emb] = bid

        inconnues = sorted(set(boite) - CLES_BOITE)
        if inconnues:
            r.dire("grave", etiq, "cles hors format, ignorees a l'ecran : {} "
                                  "(voir docs/books.md)".format(", ".join(inconnues)))

        combien = len(dedans.get(bid, []))
        if not combien:
            r.dire("avertissement", etiq,
                   "coffret vide : aucun livre ne le nomme — il ne s'affichera "
                   "pas, et c'est peut-etre un rangement laisse en chemin")
        elif combien == 1:
            r.dire("note", etiq,
                   "un seul volume dedans : une boite d'un volume est un onglet "
                   "de plus, pas un rangement")

    for bid in sorted(dedans):
        if bid not in vus:
            r.dire("grave", "boite {}".format(bid),
                   "{} livre(s) s'y rangent, et elle n'existe pas dans "
                   "etat/boites.json : ils sont nulle part"
                   .format(len(dedans[bid])))


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


def verifier_plis(e, r):
    """Le courrier : ce qui traine, ce qui vole sans oiseau, ce qui n'a pas de main."""
    vus = set()
    # corbeaux en vol, par (lieu de depart, destination)
    en_vol = {}
    for pli in e.plis:
        pid = pli.get("id")
        etiq = "pli {}".format(pid or "?")
        if not isinstance(pli, dict) or not pid:
            r.dire("grave", etiq, "pli sans id")
            continue
        if pid in vus:
            r.dire("grave", etiq, "id de pli en double")
        vus.add(pid)

        if pli.get("canal") not in CANAUX_PLI:
            r.dire("grave", etiq, "canal {!r} hors {} — la rumeur et le temoin "
                                  "ne sont pas des objets, ils restent a "
                                  "evenements.diffusion".format(pli.get("canal"),
                                                                CANAUX_PLI))
        etat = pli.get("etat")
        if etat not in ETATS_PLI:
            r.dire("grave", etiq, "etat {!r} hors {}".format(etat, ETATS_PLI))
        if not pli.get("porte"):
            r.dire("grave", etiq, "'porte' vide — un pli sans texte fige ne "
                                  "porte rien et ne peut pas arriver perime")
        for champ in ("de", "pour"):
            if pli.get(champ) and pli[champ] not in e.perso_par_id:
                r.dire("grave", etiq, "{} inconnu : {!r}".format(champ,
                                                                 pli[champ]))
        if pli.get("vers") and not e.lieu(pli["vers"]):
            r.dire("grave", etiq, "'vers' inconnu : {!r}".format(pli["vers"]))
        if pli.get("depuis") and not e.lieu(pli["depuis"]):
            r.dire("grave", etiq, "'depuis' inconnu : {!r}".format(pli["depuis"]))
        if pli.get("main") and pli["main"] not in e.perso_par_id:
            r.dire("grave", etiq, "'main' inconnue : {!r}".format(pli["main"]))

        # un pli en main sans main : personne ne l'a, et personne ne l'a lu
        if etat in ETATS_PLI_EN_MAIN and not pli.get("main"):
            r.dire("grave", etiq,
                   "{} sans 'main' — un pli est toujours dans la main de "
                   "quelqu'un ; dis qui l'a".format(etat))
        if etat == "en-route" and pli.get("main"):
            r.dire("avertissement", etiq,
                   "en route et pourtant dans une main ({}) — s'il chemine, "
                   "'main' doit etre null".format(pli["main"]))

        attendu = jour_absolu(pli.get("attendu_le"))
        parti = jour_absolu(pli.get("parti_le"))
        if attendu is None:
            r.dire("grave", etiq, "attendu_le absent ou illisible")
        elif parti is not None and attendu < parti:
            r.dire("grave", etiq, "attendu le {} alors qu'il est parti le {}"
                   .format(fmt(pli["attendu_le"]), fmt(pli["parti_le"])))
        elif etat == "en-route":
            retard = e.aujourdhui - attendu
            if retard > TOLERANCE_PLI:
                r.dire("avertissement", etiq,
                       "toujours en route, attendu le {} il y a {} jours "
                       "(monde {}) — remis, retenu, ou perdu ?".format(
                           fmt(pli["attendu_le"]), retard, fmt(e.date)))

        # les corbeaux : un oiseau ne vole que vers la ou il est ne
        if pli.get("canal") == "corbeau" and etat == "en-route":
            depuis = e.depart_de(pli)
            vers = e.lieu(pli.get("vers"))
            if depuis is None:
                r.dire("avertissement", etiq,
                       "corbeau sans lieu de depart connu (ni 'depuis', ni "
                       "lieu_id lisible pour {!r}) — stock invérifiable"
                       .format(pli.get("de")))
            elif vers:
                en_vol[(depuis, vers)] = en_vol.get((depuis, vers), 0) + 1

    for (depuis, vers), nb in sorted(en_vol.items()):
        stock = e.roukerie(depuis)
        if not stock:
            continue        # roukerie non tenue : on ne reproche rien
        reste = stock.get(vers)
        if reste is None:
            r.dire("avertissement", "roukerie {}".format(depuis),
                   "{} corbeau(x) en vol vers {} alors que la roukerie n'y "
                   "eleve aucun oiseau — un corbeau ne vole que vers la ou il "
                   "est ne".format(nb, vers))
        elif not isinstance(reste, int) or reste < 0:
            r.dire("grave", "roukerie {}".format(depuis),
                   "stock vers {} a {!r} — un envoi de trop a ete consomme"
                   .format(vers, reste))

    for lid, fiche in sorted(e.fiche_lieu.items()):
        stock = fiche.get("roukerie")
        if stock is None:
            continue
        if not isinstance(stock, dict):
            r.dire("grave", "roukerie {}".format(lid),
                   "'roukerie' doit etre un objet {lieu_id: nombre}")
            continue
        for origine, nb in sorted(stock.items()):
            if not e.lieu(origine):
                r.dire("grave", "roukerie {}".format(lid),
                       "lieu d'origine inconnu : {!r}".format(origine))
            if not isinstance(nb, int) or nb < 0:
                r.dire("grave", "roukerie {}".format(lid),
                       "stock vers {} non entier ou negatif : {!r}".format(
                           origine, nb))


def verifier_rumeurs(e, r):
    """Les incidents qui servent de rumeurs. En gravite 'note', jamais bloquant.

    Deux fautes, et ce sont les deux seules qu'une machine sache voir :
    une rumeur qui n'a pas bouge depuis longtemps (elle devrait avancer ou
    s'eteindre), et une fiabilite qui n'a pas decru en se propageant — un fait
    ne devient jamais plus sur en passant de bouche en bouche.
    """
    for inc in e.incidents:
        iid = inc.get("id", "?")
        etiq = "rumeur {}".format(iid)
        if inc.get("ou") and not e.lieu(inc["ou"]):
            r.dire("grave", etiq, "foyer inconnu : {!r}".format(inc["ou"]))

        relais = relais_de(inc)
        dates = [jour_absolu(x.get("date")) for x in relais]
        dates = [d for d in dates if d is not None]
        toleree = SILENCE_RUMEUR.get(inc.get("feu"))
        if toleree is not None and dates:
            silence = e.aujourdhui - max(dates)
            if silence > toleree:
                r.dire("note", etiq,
                       "'{}' et rien de neuf depuis {} jours (tolerance {}) — "
                       "une rumeur avance ou s'eteint ; passe-la en 'couve' ou "
                       "'eteint', ou fais-lui gagner un endroit".format(
                           inc.get("feu"), silence, toleree))

        depart = rang_certitude(inc.get("certitude"))
        for ent in inc.get("propage") or []:
            if not isinstance(ent, dict) or not ent.get("ou"):
                continue
            # Un relais dont le `depuis` nomme QUELQU'UN n'est plus du bouche a
            # oreille : c'est une parole d'autorite, avec un nom dessus — le
            # deuxieme porteur, pas le troisieme. Il n'est donc pas tenu de
            # decroitre. `certitude` mesure la confiance de qui entend, pas la
            # verite : une proclamation fausse peut etre 'rapportee' sans que
            # rien ne cloche.
            if ent.get("depuis") in e.perso_par_id:
                continue
            if ent.get("certitude") is None:
                r.dire("note", etiq,
                       "le relais {} n'a pas de 'certitude' — il herite du foyer "
                       "et la rumeur ne se degrade jamais".format(ent["ou"]))
                continue
            if rang_certitude(ent["certitude"]) >= depart:
                r.dire("note", etiq,
                       "le relais {} est aussi sur ({}) que le foyer ({}) — une "
                       "chose ne devient pas plus vraie en passant de bouche en "
                       "bouche".format(ent["ou"], ent["certitude"],
                                       inc.get("certitude")))
            if not e.lieu(ent["ou"]):
                r.dire("grave", etiq,
                       "relais en lieu inconnu : {!r}".format(ent["ou"]))


def sources_possibles(e, pid):
    """Tout ce qui a PU apprendre quelque chose a ce personnage.

    HEURISTIQUE, et il faut la lire comme telle (docs/plis.md, « la bouche ») :
    on ne sait pas relire le francais, on rassemble les textes auxquels il a eu
    acces et on cherchera un recoupement de mots rares. Sont retenus :
      - les entrees de diffusion LIVREES qui le nomment, ou livrees a son lieu ;
      - les plis qu'il a en main, ou qui lui sont adresses et arrives ;
      - les actes qu'il a commis, dont il est dit `connu_de`, ou qui se sont
        produits sous ses yeux (meme lieu) ;
      - les paroles dont il est locuteur, destinataire ou temoin ;
      - les croyances des autres tetes presentes au meme endroit (la bouche).
    """
    lid = e.lieu((e.perso_par_id.get(pid) or {}).get("lieu_id"))
    textes = []

    for ev in e.evenements:
        for ent in ev.get("diffusion") or []:
            if not isinstance(ent, dict) or ent.get("livree") is not True:
                continue
            if pid in (ent.get("qui") or []) or (
                    ent.get("ou") and lid and e.lieu(ent["ou"]) == lid):
                textes.append(ent.get("version") or "")

    for pli in e.plis:
        if not isinstance(pli, dict) or pli.get("etat") not in ETATS_PLI_EN_MAIN:
            continue
        if pli.get("main") == pid or pli.get("pour") == pid:
            textes.append(pli.get("porte") or "")

    for acte in e.actes:
        if not isinstance(acte, dict):
            continue
        connu = acte.get("connu_de") or []
        vu = (acte.get("acteur_id") == pid or pid in connu or "tous" in connu
              or (lid and acte.get("lieu_id")
                  and e.lieu(acte["lieu_id"]) == lid))
        if vu:
            textes.append("{} {}".format(acte.get("quoi") or "",
                                         acte.get("description") or ""))

    for parole in e.paroles:
        if not isinstance(parole, dict):
            continue
        if pid in (parole.get("locuteur_id"), parole.get("destinataire_id")) \
                or pid in (parole.get("temoins") or []):
            textes.append(parole.get("contenu") or "")

    # LE TEMOIN et la rumeur : ce qu'un incident a apporte ICI. Un relais qui a
    # pris a son lieu lui est parvenu, et un relais dont il est lui-meme le
    # `depuis` est une chose qu'il a vue et racontee. Un temoin n'a pas de tete
    # (c'est voulu) : sans cette branche, ce qu'il apporte ne justifierait
    # jamais rien, et l'heuristique crierait au faux positif sur des faits
    # parfaitement portes.
    for inc in e.incidents:
        propre = inc.get("contenu") or ""
        if lid and e.lieu(inc.get("ou")) == lid:
            textes.append(propre)
        for ent in inc.get("propage") or []:
            if isinstance(ent, str):
                if lid and e.lieu(ent) == lid:
                    textes.append(propre)
                continue
            if not isinstance(ent, dict):
                continue
            arrive = lid and e.lieu(ent.get("ou")) == lid
            porte = ent.get("depuis") == pid
            if arrive or porte:
                textes.append(ent.get("contenu") or propre)

    if lid:
        for autre in e.intentions:
            aid = autre.get("personnage_id")
            if aid == pid:
                continue
            if e.lieu((e.perso_par_id.get(aid) or {}).get("lieu_id")) == lid:
                textes.extend(croyances_de(autre))

    return [t for t in textes if t]


def verifier_croyances_sans_porteur(e, r):
    """« Aucune croyance sans porteur » — en gravite 'note', jamais bloquante.

    C'est la garde de fond de la refonte : un fait n'entre dans une tete que
    parce que quelqu'un ou quelque chose l'y a porte. La verification exacte
    demanderait de comprendre le sens ; on se contente d'un recoupement de mots
    rares, et sur l'etat d'avant la refonte elle criera beaucoup — c'est attendu.
    Elle ne compte pas dans le code de sortie et sort sous 'NOTE'.
    """
    for tete in e.intentions:
        pid = tete.get("personnage_id")
        croyances = croyances_de(tete)
        if not pid or not croyances:
            continue
        textes = sources_possibles(e, pid)
        orphelines = [c for c in croyances
                      if not any(se_recoupent(c, t) for t in textes)]
        if not orphelines:
            continue
        r.dire("note", pid,
               "{}/{} croyance(s) sans porteur repere (heuristique de mots "
               "rares — ni pli, ni bouche sur place, ni acte, ni parole, ni "
               "diffusion livree ne les explique) : {}".format(
                   len(orphelines), len(croyances),
                   " | ".join(c[:70] for c in orphelines)))


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


def verifier_occupation(e, r):
    """L'IMPOSSIBLE QUE PERSONNE NE VOYAIT : un drapeau qui ne ment pas tout seul.

    L'invariant historique — occupe -> pas de tete, vacant -> une tete — est
    tenu par la coherence interne du fichier. Il ne dit RIEN quand le fichier
    entier est perime : quatre sieges a `occupe: true`, deux joueurs partis
    depuis la veille, et l'etat reste parfaitement coherent avec lui-meme
    pendant que deux personnages cessent d'exister — ni joues par un humain,
    ni actives par la machine, qui les exclut justement parce qu'ils sont
    marques occupes.

    On confronte donc le fichier au DEHORS : l'age de la veille de sa session
    et le contenu de son inbox (voir `scripts/occupation.py`). Quatre fautes.
    """
    if not e.mesures_sieges:
        return
    for pid in sorted(e.mesures_sieges):
        m = e.mesures_sieges[pid]
        drapeau = e.sieges_drapeau.get(pid, True)

        # 1. Le cache a derive. Grave dans le sens « marque occupe, plus
        #    personne » : c'est le siege qui dort. Simple avertissement dans
        #    l'autre sens — un siege marque vacant que quelqu'un vient de
        #    reveiller sera correctement joue, il est juste mal etiquete.
        if drapeau and not m["occupe"]:
            r.dire("grave", pid,
                   "siege marque `occupe` dans joueurs.json alors que plus "
                   "rien n'y respire ({}) — il n'est ni joue par un humain ni "
                   "active par la boucle, donc il DORT. "
                   "python scripts/sieges.py --rafraichir --vraiment"
                   .format(m["raison"]))
        elif not drapeau and m["occupe"]:
            r.dire("avertissement", pid,
                   "siege marque vacant alors qu'il respire ({}) — cache "
                   "perime (python scripts/sieges.py --rafraichir --vraiment)"
                   .format(m["raison"]))

        # 2. Ce que la fiche RACONTE contre ce qu'on mesure. La note de
        #    nicolas-reynolds disait « VACANT pour l'instant » sous un
        #    `occupe: true` : deux verites dans la meme entree, et c'est la
        #    prose qu'on croit en relisant.
        #    On ne lit que les DECLARATIONS, c'est-a-dire les majuscules : ces
        #    notes crient ce qu'elles affirment (« VACANT pour l'instant »,
        #    « siege ALTERNE ») et parlent en minuscules du reste (« quand ce
        #    siege est occupe, Rhaenyra doit avoir une tete »). Chercher le
        #    mot sans egard a la casse rendrait toute prose coupable.
        note = str(siege_par_id(e, pid).get("note") or "")
        if "VACANT" in note and m["occupe"]:
            r.dire("avertissement", pid,
                   "la note de sa fiche dit VACANT mais le siege est mesure "
                   "assis ({}) — reecrivez la note ou levez-vous".format(
                       m["raison"]))
        if ("OCCUPE" in note or "OCCUPÉ" in note) and not m["occupe"]:
            r.dire("avertissement", pid,
                   "la note de sa fiche dit OCCUPE mais plus rien n'y respire "
                   "({})".format(m["raison"]))

        # 3. Un siege tenu occupe par un inbox qui ne bouge plus. La
        #    definition dit « au moins un fichier » et on ne la change pas —
        #    mais un inbox jamais vide est un `occupe: true` qui ne
        #    redescendra jamais, c'est-a-dire le meme defaut par une autre
        #    porte.
        if m["inbox_dormant"]:
            r.dire("avertissement", pid,
                   "siege tenu occupe par {} action(s) d'inbox dont la plus "
                   "recente date de {} — soit le joueur est parti sans qu'on "
                   "les traite, soit le guetteur est eteint".format(
                       m["inbox"], occupation.dire_age(m["inbox_age_s"])))

    # 4. Deux sieges d'une meme paire ALTERNEE assis en meme temps. Alterne
    #    veut dire : le meme humain, jamais les deux a la fois. C'est declare
    #    par `alterne_avec` dans l'entree du siege — et une note qui parle
    #    d'alternance sans ce champ n'est pas une declaration, c'est un
    #    souvenir.
    for siege in e.sieges:
        pid = siege.get("personnage_id")
        if not pid:
            continue
        pairs = siege.get("alterne_avec")
        if isinstance(pairs, str):
            pairs = [pairs]
        note = str(siege.get("note") or "")
        if not pairs:
            if "ALTERNE" in note.upper():
                r.dire("avertissement", pid,
                       "sa note dit que ce siege est ALTERNE mais son entree "
                       "ne porte pas `alterne_avec` — rien ne peut le "
                       "verifier")
            continue
        for autre in pairs:
            if pid in e.sieges_occupes and autre in e.sieges_occupes:
                r.dire("grave", pid,
                       "siege ALTERNE avec '{}' et tous deux mesures assis en "
                       "meme temps — c'est le meme joueur : l'un des deux est "
                       "un fantome ({} / {})".format(
                           autre,
                           (e.mesures_sieges.get(pid) or {}).get("raison"),
                           (e.mesures_sieges.get(autre) or {}).get("raison")))
            if autre not in e.sieges_drapeau:
                r.dire("avertissement", pid,
                       "`alterne_avec` designe '{}', qui n'est pas un siege"
                       .format(autre))


def siege_par_id(e, pid):
    for siege in e.sieges:
        if siege.get("personnage_id") == pid:
            return siege
    return {}


def verifier_sieges(e, r):
    """Le siege vacant doit avoir une tete ; l'occupe ne doit pas en avoir.

    C'est la garde des sieges alternes. On quitte Rhaenyra pour jouer l'agent
    de Port-Real : elle redevient un PNJ, donc elle a besoin d'une tete, sans
    quoi elle passe la lune a ne rien faire pendant qu'on regarde ailleurs —
    et l'on ne s'en apercoit qu'en revenant s'asseoir, trois lunes trop tard.
    Le symetrique (une tete sous un siege occupe) est deja dit par
    verifier_intentions : le MJ jouerait le personnage du joueur.
    """
    for pid in sorted(e.sieges_vacants):
        if pid not in e.intention_par_id:
            r.dire("grave", pid,
                   "siege VACANT sans tete dans intentions.json — ce "
                   "personnage n'agira pas hors ecran tant qu'on ne lui en "
                   "ecrit pas une")
        else:
            # LA CLAUSE DE REGENCE. Le garde mecanique de
            # `boucle_activation.py` refuse deja les rapports qui franchissent
            # la ligne, mais un homme qui l'ignore y va, se fait refuser et
            # perd un passage de correction a chaque fois. La clause dans sa
            # tete est ce qui evite le mur ; le garde est ce qui le rattrape
            # quand il l'oublie. On veut les deux.
            if not regence.clause_posee(e.intention_par_id.get(pid)):
                r.dire("avertissement", pid,
                       "siege vacant dont la tete ne porte pas la clause de "
                       "regence — il ignore ce qu'il ne doit pas conclure "
                       "(python scripts/regence.py --poser {} --vraiment)"
                       .format(pid))
        perso = e.perso_par_id.get(pid)
        if perso is not None and perso.get("etat") != "actif":
            r.dire("avertissement", pid,
                   "siege vacant dont la fiche est '{}' — un siege qu'on "
                   "reprendra un jour reste actif".format(perso.get("etat")))
    for pid in sorted(e.sieges_occupes | e.sieges_vacants):
        if pid not in e.perso_par_id:
            r.dire("grave", pid,
                   "siege pour un personnage absent de personnages.json")
    verifier_occupation(e, r)
    if e.sieges and e.joueur and e.joueur in e.sieges_vacants:
        r.dire("avertissement", "journal",
               "journal.personnage_joueur_id vaut '{}' alors que son siege "
               "est marque vacant".format(e.joueur))
    # Ce qu'un siege a decide seul et qu'on n'a pas encore rendu a celui qui
    # s'y rassoit. Ce n'est une faute pour personne tant qu'il est vacant ; ca
    # en devient une des qu'il est occupe, parce qu'alors le joueur joue sans
    # savoir ce qu'on a engage en son nom.
    for pid in sorted(e.sieges_occupes | e.sieges_vacants):
        _, en_attente = regence.compte_rendu(pid)
        if not en_attente:
            continue
        if pid in e.sieges_occupes:
            r.dire("avertissement", pid,
                   "{} decision(s) prises en regence jamais rendues a celui "
                   "qui s'y est rassis (python scripts/regence.py "
                   "--compte-rendu {})".format(len(en_attente), pid))
        franchies = sum(len(x.get("lignes_franchies") or [])
                        for x in en_attente)
        if franchies:
            r.dire("grave", pid,
                   "{} ligne(s) irreversible(s) franchies par ce siege en "
                   "regence — le garde a ete contourne, relisez son "
                   "registre".format(franchies))


def verifier_audiences(e, r):
    """A plusieurs, aucun item du flux ne doit etre sans audience.

    Un `pour` absent ne veut pas dire « pour tout le monde » : il veut dire
    « rien n'a ete declare ». Le serveur ne sert plus ces items-la passe le
    seuil (la ligne ou le dernier joueur s'est assis), donc ils ne fuitent
    plus — mais ils DISPARAISSENT, ce qui est un bug silencieux d'une autre
    espece : le MJ croit avoir pousse une scene que personne ne lit. On le dit
    ici, pendant que c'est encore reparable.
    """
    if len(e.sieges_occupes) < 2:
        return
    seuil = 0
    for j in e.sieges:
        seuil = max(seuil, j.get("depuis") or 0)
    chemin = os.path.join(RACINE, "etat", "flux.jsonl")
    orphelins = []
    try:
        with io.open(chemin, encoding="utf-8") as f:
            for i, ligne in enumerate(f):
                if not ligne.strip() or i < seuil:
                    continue
                try:
                    it = json.loads(ligne)
                except Exception:
                    continue
                if not it.get("pour"):
                    orphelins.append(i)
    except Exception:
        return
    if orphelins:
        r.dire("grave", "flux",
               "{} items du flux sans `pour` apres la ligne {} — ils ne sont "
               "servis a personne. Lignes : {}{}".format(
                   len(orphelins), seuil,
                   ", ".join(str(n) for n in orphelins[:8]),
                   "…" if len(orphelins) > 8 else ""))


def verifier_affectations(e, r):
    """Les adresses physiques donnees en jeu tiennent-elles encore ?

    Une affectation joint une chose de la fiction a un batiment du monde
    engendre (voir scripts/affecter.py). Le monde se regenere ; l'affectation,
    non. Une cible disparue ne casse rien a l'ecran — elle ment en silence, et
    l'on continue de calculer des distances sur un batiment qui n'existe plus.
    """
    try:
        from agents.expose import affecter
    except ImportError:
        return
    L = affecter.charger_liens()
    if not L["affectations"]:
        return
    try:
        # `verifier` ouvre lui-meme le monde nomme par CHAQUE affectation : le
        # batiment doit exister encore, et dans le bon monde. Un monde absent
        # se signale au lieu de faire taire toute la verification.
        maux = affecter.verifier(L)
    except SystemExit:
        return                       # pas de monde engendre : rien a verifier
    for mal in maux:
        r.dire("avertissement", "affectations", mal)


def verifier_registres_derives(e, r):
    """Un index ecrit a la main est un index qui va mentir.

    Les quatre registres par type — `plan-etats-cibles`, `plan-verrous`,
    `plan-clefs`, `plan-actions` — ne sont plus une seconde verite : ils sont
    DERIVES des cahiers d'affaire, par `python scripts/couverture.py
    --registres`. La regle du guide (« quand l'affaire et le registre se
    contredisent, c'est le registre qui a raison ») supposait un registre tenu ;
    il ne l'etait plus, 108 lignes contre 1312.

    Ce qu'on a paye pour l'apprendre : Le Sanglier avait renomme l'etat cible
    23000 dans son cahier, le registre portait toujours l'ancien nom, et sa
    propre liste de trous lui a resservi le nom perime le matin meme. Deux
    copies d'un plan n'est pas un defaut de proprete : c'est une machine a
    envoyer les hommes contre des fantomes.

    Sans cette garde, quelqu'un y posera une ligne de bonne foi dans six
    semaines — et la nuit du 31e sera a refaire a l'identique. `plan-moyens` et
    `plan-offices` n'en sont pas : ce sont des SOURCES, pas des copies.
    """
    try:
        from plan.expose import couverture
    except ImportError:
        return
    try:
        ecarts, divergences = couverture.ecart_registres(e.books)
    except Exception as mal:                      # un index ne bloque pas l'audit
        r.dire("note", "registres", "impossible de recalculer : {}".format(mal))
        return
    if divergences:
        # ON LES NOMME, ON NE LES COMPTE PAS SEULEMENT. Une retouche a la main
        # du NOM d'une piece cree une divergence que la regle de conservation
        # reproduit fidelement : l'ecart se referme sur lui-meme et la
        # comparaison ne voit rien. La liste, elle, s'allonge — et c'est le seul
        # signe qu'on ait.
        r.dire("note", "registres",
               "{} nom(s) divergent(s) entre index et cahier, conserves tels "
               "quels : {} — si cette liste s'allonge, quelqu'un a ecrit dans "
               "un index (voir docs/echiquier.md)".format(
                   len(divergences), " · ".join(n for _, n in divergences)))
    for bid, a, n in ecarts:
        if a < 0:
            r.dire("avertissement", "registre {}".format(bid),
                   "titre non marque « calcule » — relancer "
                   "`python scripts/couverture.py --registres`")
        else:
            r.dire("avertissement", "registre {}".format(bid),
                   "ECRIT A LA MAIN, ou perime : {} ligne(s) sur le disque, {} "
                   "derivees des cahiers. Le cahier est la verite — reporter la "
                   "modification dans le cahier d'affaire, puis relancer "
                   "`python scripts/couverture.py --registres` (voir "
                   "docs/echiquier.md)".format(a, n))


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
        import rapporteurs
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


def verifier_activations(e, r):
    """Ce que la boucle d'activation a produit, et ce qui a ete jete.

    LE SILENCE DES REJETS EST LE PIRE DEFAUT QU'ON AIT EU. Le 10 aout, 326
    mutations sur 355 etaient refusees — 92 % — pour une seule et meme cause :
    le narrateur citait son resultat sous la clef `cite` quand le validateur
    lisait `resultat_id`. La boucle a tourne des nuits entieres en produisant
    presque rien, et rien nulle part ne le disait. Un taux de perte est une
    panne, pas une statistique : il doit crier des le premier tour.
    """
    depot = os.path.join(ETAT, "activations")
    if not os.path.isdir(depot):
        return

    # LE CUMUL DE TOUJOURS EST UNE MAUVAISE MESURE, et c'est la lecon du
    # 10 aout au soir : la panne `resultat_id` etait REPAREE, et le taux
    # affichait encore 78 % parce que les 326 rejets d'avant la reparation
    # dorment sur le disque et y dormiront toujours. Un taux qu'aucune
    # correction ne peut faire baisser ne signale plus rien.
    # On mesure donc la FENETRE RECENTE — c'est elle qui dit l'etat de la
    # boucle maintenant — et le cumul ne sort qu'en note, pour memoire.
    FENETRE = 25

    def depouiller(noms):
        retenues, rejetees, causes = 0, 0, {}
        for nom in noms:
            try:
                with io.open(os.path.join(depot, nom), encoding="utf-8") as fh:
                    rapport = json.load(fh)
            except (ValueError, OSError):
                continue
            if not isinstance(rapport, dict):
                continue
            retenues += len(rapport.get("mutations_proposees") or [])
            for jetee in rapport.get("mutations_rejetees") or []:
                rejetees += 1
                if isinstance(jetee, dict):
                    cause = str(jetee.get("erreur") or "sans cause")[:80]
                    causes[cause] = causes.get(cause, 0) + 1
        return retenues, rejetees, causes

    # Les rapports sont horodates dans leur nom : le tri alphabetique est
    # l'ordre chronologique, et on n'a pas a interroger le disque.
    noms = sorted(n for n in os.listdir(depot)
                  if n.endswith(".json") and n != "boucle.json")
    if not noms:
        return
    recents = noms[-FENETRE:]
    retenues, rejetees, causes = depouiller(recents)
    total = retenues + rejetees
    if not total:
        return
    part = 100.0 * rejetees / total
    niveau = "grave" if part >= 25 else ("avertissement" if part >= 5
                                         else "note")
    r.dire(niveau, "activations",
           "{} mutations sur {} jetees ({:.0f} %) sur les {} derniers "
           "rapports — la boucle produit {} changement(s) applicable(s)".format(
               rejetees, total, part, len(recents), retenues))
    for cause, combien in sorted(causes.items(), key=lambda x: -x[1])[:3]:
        r.dire(niveau, "activations",
               "  {} fois : {}".format(combien, cause))

    if len(noms) > len(recents):
        cum_ret, cum_rej, _ = depouiller(noms)
        cum_total = cum_ret + cum_rej
        if cum_total:
            r.dire("note", "activations",
                   "pour memoire, depuis le premier rapport : {} sur {} "
                   "jetees ({:.0f} %) en {} rapports — ce chiffre porte les "
                   "pannes deja reparees et ne baissera jamais".format(
                       cum_rej, cum_total, 100.0 * cum_rej / cum_total,
                       len(noms)))


def verifier(e, en_json=False):
    r = Rapport()
    if not e.joueur:
        r.dire("avertissement", "journal",
               "personnage_joueur_id absent — impossible de proteger sa tete")
    verifier_sieges(e, r)
    verifier_intentions(e, r)
    verifier_evenements(e, r)
    verifier_personnages(e, r)
    verifier_mains(e, r)
    verifier_pensees(e, r)
    verifier_books(e, r)
    verifier_registres_derives(e, r)
    verifier_rapporteurs(e, r)
    verifier_etats_du_plan(e, r)
    verifier_boites(e, r)
    verifier_plis(e, r)
    verifier_couts_chiffres(e, r)
    verifier_rumeurs(e, r)
    verifier_croyances_sans_porteur(e, r)
    verifier_affectations(e, r)
    verifier_activations(e, r)
    verifier_audiences(e, r)
    r.imprimer_json() if en_json else r.imprimer()
    # Les 'note' sont informatives : elles ne font pas echouer l'audit. La
    # croyance sans porteur crie fort sur l'etat d'avant la refonte, et ce
    # n'est pas une raison de bloquer le jeu.
    return 1 if [a for a in r.anomalies if a["gravite"] != "note"] else 0


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
