# -*- coding: utf-8 -*-
"""MISSIONS — les textes servis au narrateur local d'une activation, et
l'extraction de ses reponses (appel PNJ, tentative, relance acteur).
"""
import json
import os
import re

from agents.expose import depecher  # le script d'appel canonique

from agents.activation.socle import (SECONDES_MONDE_PAR_ENERGIE,
                                     DUREE_ACTIVATION_MIN_SECONDES, ETAT,
                                     TYPES_RESULTAT_ACTIVITE, lire_json,
                                     secondes_monde_pour_energie)

def intitule_tache_activation(tache, dossier):
    etape = ((dossier.get("intention") or {}).get("etape_elue") or {})
    return etape.get("quoi") or tache.get("quoi") or "l'affaire devant toi"


def mission_activation(pid, tache, budget, horloge, noeuds, dossier):
    del pid, horloge, noeuds  # la machine ne parle plus dans la mission
    date = dossier.get("date_du_monde") or {}
    p = dossier.get("personnage") or {}
    lieu = p.get("lieu") or p.get("lieu_id") or "lieu inconnu"
    affaire = intitule_tache_activation(tache, dossier)
    return """%(annee)s AC · %(lune)se lune · %(jour)se jour — %(lieu)s

Tu as %(secondes)d secondes devant toi.

Tu as l'intention de t'occuper de :
%(affaire)s

Agis maintenant. Ne fais pas un plan de ce que tu pourrais faire : commence
par le premier geste réel que cette affaire appelle, avec les personnes, les
objets, les lieux et les registres que tu connais. Poursuis geste après geste
tant qu'il te reste du temps. Pour chacun, dis combien de secondes il prend et
ce qu'il produit réellement. Si quelque chose résiste, travaille sur ce qui
résiste ou constate précisément ce qui t'arrête. Arrête-toi quand le temps est
écoulé.
""" % {
        "annee": date.get("annee") or "?",
        "lune": date.get("lune") or "?",
        "jour": date.get("jour") or "?",
        "lieu": lieu,
        "secondes": secondes_monde_pour_energie(budget),
        "affaire": affaire,
    }


def contexte_narrateur_activation(pid, tache, budget_energie,
                                  budget_secondes, horloge, dossier):
    """La verite locale donnee a l'arbitre, jamais a l'acteur."""
    return {
        "date_du_monde": dossier.get("date_du_monde"),
        "present_secondes": round(float(horloge["present_secondes"]), 3),
        "budget_energie": budget_energie,
        "secondes_par_point_energie": SECONDES_MONDE_PAR_ENERGIE,
        "budget_secondes": int(budget_secondes),
        "duree_minimale_secondes": min(
            DUREE_ACTIVATION_MIN_SECONDES, int(budget_secondes)),
        "acteur_candidat": pid,
        "tache_elue": {
            "id": tache.get("id"),
            "quoi": intitule_tache_activation(tache, dossier),
            "creee": bool(tache.get("creee")),
        },
        "chemin_election": dossier.get("chemin") or [],
        "salle_actuelle": dossier.get("salle_actuelle") or {},
        "dossier_acteur": dossier,
        "topologie_des_salles": lire_json(os.path.join(ETAT, "chemins.json"), {}),
    }


def mission_ouverture_narrateur(pid, tache, budget_energie,
                                budget_secondes, contexte_narrateur):
    dossier = contexte_narrateur.get("dossier_acteur") or {}
    salle = dossier.get("salle_actuelle") or {}
    return """PHASE 1 — APPELER L'ACTEUR

Voici le dossier fermé de cette activation :

%(dossier_ferme)s

Ouvre le battement local dans %(salle)s.

La physique a élu %(acteur)s pour l'affaire suivante :
%(tache)s

TU LE SUIS PENDANT QU'IL TRAVAILLE, ET TU LE GUIDES. Un fil reste ouvert entre
sa session et la tienne : sers-t'en dès qu'il part de travers, cherche une
chose qui est dans ton dossier, ou s'engage vers un mur que tu vois et pas lui.
On ne le laisse pas se cogner pour le plaisir de l'arbitrer après.

    python scripts/parloir.py --dire --de mj --a %(acteur)s "<le fait qui lui manque, en une phrase>"
    python scripts/parloir.py --ecouter --qui mj

TU RECOMMANDES ET TU DÉPANNES — TU N'ORDONNES PAS. Il décide de sa journée ;
toi, tu lui évites de la perdre.

Recommander, c'est lui ouvrir une porte qu'il ne voyait pas, et le laisser
choisir d'y entrer : « le maître de port tient un rôle des passages, tu y
trouverais tes dates » · « il y a deux Torgo dans cette rade, l'aîné au môle
et le jeune au banc de calfat — vérifie duquel on t'a parlé » · « ce compte
existe déjà quelque part, ça t'éviterait de le refaire ».

Dépanner, c'est le déblocage technique, et là tu es net : l'adresse exacte
d'une chose, l'id sous lequel elle existe, le registre où elle est écrite, le
format qu'attend ce qu'il essaie de produire, le nom réel de ce qu'il a mal
nommé. Ce sont des faits de mécanique, pas des choix de fiction : donne-les
sans détour et sans énigme.

Ce qui reste à lui, entier : ce qu'il décide de faire, où il va, sa manière,
ses gestes et son rapport. S'il écarte ta recommandation, c'est sa journée et
c'est bien. Parle-lui autant qu'il en a besoin.

Il engage %(energie)d points d'énergie, soit une fenêtre physique de
%(secondes)d secondes (%(minutes)d minutes). Son activation doit couvrir un
vrai morceau de travail d'au moins %(minimum)d secondes, quitte à condenser
les continuités par une ellipse. Réveille-le maintenant. Ne résous rien encore
et rends seulement cet objet, sans phrase autour :

{
  "appel_pnj": {
    "qui": "%(acteur)s",
    "message": "adresse directe, diégétique et brève demandant ce qu'il tente maintenant"
  }
}
""" % {
        "dossier_ferme": json.dumps(
            contexte_narrateur, ensure_ascii=False, indent=2),
        "salle": salle.get("nom") or "la salle inconnue",
        "acteur": pid,
        "tache": intitule_tache_activation(tache, dossier),
        "energie": budget_energie,
        "secondes": budget_secondes,
        "minutes": round(budget_secondes / 60),
        "minimum": min(DUREE_ACTIVATION_MIN_SECONDES, budget_secondes),
    }


def mission_veille_narrateur(pid, tache, appel):
    """Ce que le narrateur fait pendant que son homme travaille : le suivre."""
    return """PHASE 1bis — VEILLER SUR TON HOMME PENDANT QU'IL TRAVAILLE

Tu viens de réveiller %(acteur)s sur : %(tache)s
Il est en train de vivre sa journée EN CE MOMENT, dans sa propre session.

Ton seul travail maintenant, pendant environ deux minutes : rester là et le
dépanner. Tu ne rédiges rien, tu n'arbitres rien, tu ne rends aucun rapport.

Fais ceci, en boucle, jusqu'à ce que tu aies tenu deux minutes :

    python scripts/parloir.py --ecouter --qui mj
    sleep 15

S'il dit quelque chose, s'il bute, s'il cherche une chose que tu as dans ton
dossier, réponds-lui :

    python scripts/parloir.py --dire --de mj --a %(acteur)s "<ta recommandation ou ton dépannage>"

TU RECOMMANDES ET TU DÉPANNES, TU N'ORDONNES PAS. Une porte qu'il ne voyait
pas et qu'il reste libre de ne pas prendre ; ou le fait technique net —
l'adresse exacte, l'id sous lequel une chose existe, le registre où elle est
écrite, le nom réel de ce qu'il a mal nommé. Parle-lui autant qu'il en a
besoin : un homme qu'on aide bien vaut mieux qu'un quota respecté.

Le silence est normal et ne coûte rien : la plupart du temps il travaille très
bien seul, et tu n'as rien à dire. Au bout de deux minutes, réponds simplement
`{"veille": "finie"}` et arrête-toi.
""" % {"acteur": pid, "tache": tache.get("quoi") or tache.get("id")}


def mission_resolution_narrateur(pid, tache, budget_energie,
                                 budget_secondes, horloge, tentative,
                                 contexte_narrateur):
    return """PHASE 2 — ARBITRER LA TENTATIVE

Voici la réponse exacte de l'acteur que tu as réveillé :

%(tentative)s

TON PREMIER TRAVAIL EST DE LE FAIRE RÉUSSIR, PAS DE LE JUGER. Il ne voit que
ce qu'il a sous les yeux ; toi, tu as le dossier entier. S'il cherche une
adresse, un nom, un chiffre, une porte, une personne qui est dans ton dossier
et pas dans sa tête — DONNE-LE-LUI et continue la scène. S'il s'y prend mal
mais que son intention est claire, fais aboutir l'intention. S'il vise une
chose qui n'existe pas sous ce nom mais qui existe sous un autre, corrige en
silence et poursuis.

Un échec ne se prononce QUE sur un obstacle réel de la fiction — quelqu'un qui
refuse, une porte fermée à clef, une marée, un homme absent, le temps qui
manque. Jamais parce qu'il ignorait quelque chose que tu savais, jamais sur
une maladresse de formulation, jamais parce qu'il a mal nommé une chose. Un
homme qu'on laisse échouer sur son ignorance a perdu sa journée, et nous avec.

Rends compte de l'aide que tu lui as donnée dans un champ `aide` du rapport :
[{"quoi": "ce qu'il lui manquait", "donne": "ce que tu lui as fourni"}].
S'il n'a eu besoin de rien, mets une liste vide.

Arbitre maintenant cette tentative depuis la vérité locale de ton dossier.
Le battement commence à %(debut)s secondes et peut durer jusqu'à %(budget)d
secondes (%(minutes)d minutes), payées par %(energie)d points d'énergie. Il doit
en produire au moins %(minimum)d : ne tronque pas l'activation au premier geste.
Poursuis la tentative jusqu'à un résultat, une résistance réellement établie ou
la borne, en condensant les continuités par les ellipses imposées par ton
système. Rends seulement le rapport final JSON. L'acteur et la tâche restent
`%(acteur)s` et `%(tache)s`.

%(contrat)s
""" % {
        "tentative": json.dumps(tentative, ensure_ascii=False, indent=2),
        "debut": round(float(horloge["present_secondes"]), 3),
        "budget": budget_secondes,
        "minutes": round(budget_secondes / 60),
        "energie": budget_energie,
        "minimum": min(DUREE_ACTIVATION_MIN_SECONDES, budget_secondes),
        "acteur": pid, "tache": tache.get("id"),
        "contrat": depecher.contrat_rapport_narrateur(contexte_narrateur),
    }


def mission_correction_narrateur(erreur, budget_secondes, horloge):
    return """Ton rapport vient d'être refusé par le validateur mécanique :

%(erreur)s

Débrouille-toi et corrige TON JSON. Ne réveille pas le PNJ une seconde fois,
ne change ni sa tentative ni les faits arbitrés. Rends seulement un rapport
final complet et valide. Rappels : axe continu depuis %(debut)s, entre
%(minimum)d et %(budget)d secondes ; chaque résultat cite une source touchée,
mobilisée, visée par l'action, traversée par le chemin ou produite plus tôt ;
chaque mutation cite un résultat du rapport et appartient au vocabulaire fermé
d'`appliquer.py`. Aucun `candidate:` ni adresse absente du dossier. Toute
avancée, fin, blocage ou échec vise l'id exact de la tâche. Le temps reste
physique : l'ellipse ne permet ni page écrite ni longue tirade en quelques
secondes. Si une continuité de reprise existe, reprends exactement son dernier
`apres` dans le nouvel `avant`.
""" % {
        "erreur": str(erreur),
        "debut": round(float(horloge["present_secondes"]), 3),
        "minimum": min(DUREE_ACTIVATION_MIN_SECONDES, budget_secondes),
        "budget": budget_secondes,
    }


def extraire_appel_pnj(reponse, pid):
    brut, note = depecher.extraire_json(reponse.get("result", ""))
    if brut is None:
        raise RuntimeError("appel du narrateur illisible : %s" % note)
    appel = brut.get("appel_pnj") or {}
    if appel.get("qui") != pid:
        raise RuntimeError("le narrateur a reveille %s au lieu de %s" %
                           (appel.get("qui"), pid))
    message = appel.get("message")
    if not isinstance(message, str) or not message.strip():
        raise RuntimeError("le narrateur n'a pas formule l'appel du PNJ")
    return {"qui": pid, "message": message.strip()}


def extraire_tentative(reponse):
    brut, note = depecher.extraire_json(reponse.get("result", ""))
    if brut is None:
        raise RuntimeError("tentative de l'acteur illisible : %s" % note)
    tentative = brut.get("tentative") or {}
    if not isinstance(tentative, dict):
        raise RuntimeError("la tentative de l'acteur doit former un objet")
    if not str(tentative.get("verbe") or "").strip() \
            or not str(tentative.get("quoi") or "").strip():
        raise RuntimeError("la tentative doit nommer son verbe et son geste")
    interdits = set(tentative) & {"resultat", "resultats", "duree_s",
                                  "duree_secondes", "reussite", "issue"}
    if interdits:
        raise RuntimeError("l'acteur a arbitré le monde dans sa tentative : %s" %
                           ", ".join(sorted(interdits)))
    return tentative


def extraire_relance_acteur(reponse):
    """Reconnaît la sortie imposée au narrateur par son hook Stop."""
    brut, _ = depecher.extraire_json(reponse.get("result", ""))
    if not isinstance(brut, dict) or not brut.get("relance_acteur"):
        return None
    relance = brut["relance_acteur"]
    if not isinstance(relance, dict):
        raise RuntimeError("relance_acteur du narrateur illisible")
    message = str(relance.get("message") or "").strip()
    if not message:
        manques = relance.get("manques") or []
        message = "Reprends ton travail sur ces points : " + "; ".join(
            str(x) for x in manques if str(x).strip())
    if not message.strip():
        raise RuntimeError("le narrateur demande une relance sans consigne")
    return {"message": message, "manques": relance.get("manques") or []}


def mission_relance_acteur(tache, relance):
    return """On te donne un coup de main sur cette tâche :

%(tache)s

Ce n'est pas un reproche et tu n'as rien raté. Voici ce qu'on peut te dire de
plus, que tu ne pouvais pas savoir d'où tu es :

%(message)s

Reprends la même tâche avec ça en main, et fais le geste suivant. Rends
seulement l'objet `tentative` prévu par ton système.
""" % {"tache": tache.get("quoi") or tache.get("id"),
       "message": relance["message"]}

