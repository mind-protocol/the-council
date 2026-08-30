# -*- coding: utf-8 -*-
"""MANUEL — la memoire d'activation, l'etagere systeme et les manuels
servis a l'homme depeche (journee, tentative, narrateur local).
"""
import io
import json
import os
import re
import sys

from etat.expose import tables

from agents.depeche.brief import (RACINE, ETAT, METIER, lire, date_du_monde,
                                  livre,
                                  brief_de, dossier_journee, feuille_de_route,
                                  travaux_ouverts_de, travaux_ids, positions,
                                  _voix_incarnee,
                                  position_de, dans_le_rayon, dans_la_salle,
                                  salles_peuplees, les_pj)

def memoire_activation(contexte):
    """Formule l'identité, la situation, la mémoire et les affaires présentes."""
    contexte = contexte or {}
    p = contexte.get("personnage") or {}
    intention = contexte.get("intention") or {}
    lignes = []

    date = contexte.get("date_du_monde") or {}
    if date:
        lignes.extend(["## Maintenant", "", "Date : an %s, %se lune, %se jour." %
                       (date.get("annee"), date.get("lune"), date.get("jour"))])

    nom = p.get("nom") or p.get("id")
    titre = p.get("titre")
    if nom:
        lignes.extend(["", "## Ton identité", "",
                       "Tu es %s%s." %
                       (nom, (", " + str(titre)) if titre else "")])
    naissance = p.get("naissance")
    if naissance and date.get("annee"):
        lignes.append("Tu as environ %d ans." %
                      (int(date["annee"]) - int(naissance)))
    portrait = p.get("portrait") or {}
    if portrait.get("physique"):
        lignes.append("Ton corps : " + str(portrait["physique"]))
    traits = [str(x) for x in (p.get("traits") or []) if x]
    if traits:
        lignes.append("Tes traits : " + ", ".join(traits) + ".")
    if p.get("etat") or p.get("condition"):
        lignes.append("Ton état présent : %s%s." %
                      (str(p.get("etat") or ""),
                       (", " + str(p.get("condition")))
                       if p.get("condition") else ""))
    voix = _voix_incarnee(p)
    if voix:
        lignes.extend(["", "Ta voix et tes gestes :", voix])

    objectifs = [x.get("but") if isinstance(x, dict) else x
                 for x in (p.get("objectifs") or [])]
    objectifs = [str(x) for x in objectifs if x]
    if objectifs:
        lignes.extend(["", "Ce que tu poursuis :"])
        lignes.extend("- " + x for x in objectifs)

    salle = contexte.get("salle_actuelle") or {}
    if salle:
        lignes.extend(["", "## Le lieu", "",
                       "Tu te trouves dans : " +
                       str(salle.get("nom") or salle.get("id") or
                           "lieu à préciser")])
        presents = salle.get("personnes") or []
        lignes.append("Les personnes présentes :")
        if presents:
            for personne in presents:
                nom_present = str(personne.get("nom") or
                                  personne.get("id") or "inconnu")
                if personne.get("id") == p.get("id"):
                    nom_present += " (toi)"
                lignes.append("- " + nom_present)
        else:
            lignes.append("- Ta propre présence occupe ce lieu.")

    relations = contexte.get("relations") or []
    if relations:
        lignes.extend(["", "## Tes relations", ""])
        for relation in relations:
            source = relation.get("source") or relation.get("source_id")
            cible = relation.get("cible") or relation.get("cible_id")
            morceaux = ["%s → %s" % (source, cible)]
            if relation.get("opinion") is not None:
                morceaux.append("opinion %s" % relation["opinion"])
            liens = [str(x) for x in relation.get("liens") or [] if x]
            if liens:
                morceaux.append("; ".join(liens))
            lignes.append("- " + " · ".join(morceaux))

    if intention.get("intention"):
        lignes.extend(["", "## Ta vie en cours", "",
                       "Ton intention du moment :",
                       str(intention["intention"])])
    croyances = [str(x) for x in (intention.get("croyances") or []) if x]
    if croyances:
        lignes.extend(["", "Ce que tu tiens pour vrai :"])
        lignes.extend("- " + x for x in croyances)
    ignores = [str(x) for x in (intention.get("ignore") or []) if x]
    if ignores:
        lignes.extend(["", "Les questions encore ouvertes pour toi :"])
        lignes.extend("- " + x for x in ignores)
    declencheurs = intention.get("declencheurs") or []
    if declencheurs:
        lignes.extend(["", "Les événements qui appellent aussitôt ton action :"])
        for declencheur in declencheurs:
            if isinstance(declencheur, dict):
                lignes.append("- Si %s, alors %s" %
                              (declencheur.get("si") or "?",
                               declencheur.get("alors") or "?"))
    if intention.get("attitude_joueur"):
        lignes.extend(["", "Ta disposition envers la souveraine :",
                       str(intention["attitude_joueur"])])
    if intention.get("mandat"):
        lignes.extend(["", "Ton mandat actuel :",
                       json.dumps(intention["mandat"], ensure_ascii=False,
                                  indent=2)])

    # LA REGENCE, S'IL Y A LIEU. Un siege que personne n'occupe travaille
    # comme tout le monde, mais il ne conclut rien d'irreversible : ce qu'il
    # signerait, le joueur le retrouverait signe en revenant. Vide pour un
    # acteur ordinaire, donc invisible pour lui.
    contrainte = contexte.get("contrainte_regence") or {}
    if contrainte:
        lignes.extend(["", "## Ce que tu ne conclus pas", "",
                       str(contrainte.get("pourquoi") or "")])
        for interdit in contrainte.get("interdits") or []:
            lignes.append("- Jamais : %s. À la place : %s."
                          % (interdit.get("quoi"),
                             interdit.get("a_la_place")))
        if contrainte.get("comment_s_arreter"):
            lignes.extend(["", str(contrainte["comment_s_arreter"])])

    tache = contexte.get("tache") or {}
    if tache:
        lignes.extend(["", "## Ce qui te saisit maintenant", "",
                       str(tache.get("quoi") or tache.get("id") or "")])
        if tache.get("id"):
            lignes.append("Cette affaire porte l'identifiant : " +
                          str(tache["id"]))
    if intention.get("etape_elue"):
        lignes.extend(["", "L'étape vivante de ton projet :",
                       json.dumps(intention["etape_elue"], ensure_ascii=False,
                                  indent=2)])

    affaires = str(contexte.get("affaires_du_jour") or "").strip()
    if affaires:
        lignes.extend(["", "## Tes affaires aujourd'hui", "", affaires])

    continuite = contexte.get("continuite_reprise") or {}
    if continuite:
        lignes.extend(["", "## Ta continuité immédiate", "",
                       "Ce que tu as déjà réellement fait sur cette affaire :"])
        for activite in continuite.get("activites") or []:
            quoi = str(activite.get("quoi") or "").strip()
            resultat = str(activite.get("resultat") or "").strip()
            if quoi:
                lignes.append("- " + quoi + ((" → " + resultat) if resultat else ""))
        etats = continuite.get("etat_cibles") or {}
        for cible, etat in etats.items():
            lignes.append("- État acquis de %s : %s" %
                          (cible, str(etat.get("apres"))))
        lignes.append("Ton prochain geste part exactement de cet état acquis.")

    for travail in contexte.get("travaux_ouverts") or []:
        lignes.extend(["", "Affaire en cours : " +
                       str(travail.get("affaire") or travail.get("id") or "")])
        if travail.get("conclusion"):
            lignes.extend(["Ce que tu en as déjà conclu :",
                           str(travail["conclusion"])])
        pensees = travail.get("pensees_recentes") or []
        if pensees:
            lignes.append("Ce que tes derniers pas t'ont appris :")
            for pensee in pensees:
                if not isinstance(pensee, dict):
                    lignes.append("- " + str(pensee))
                    continue
                texte = str(pensee.get("texte") or "")
                source = pensee.get("source")
                lignes.append("- " + texte +
                              ((" (source : %s)" % source) if source else ""))

    mains = contexte.get("mains_portees") or []
    if mains:
        lignes.extend(["", "Ce que tu tiens :"])
        for main in mains:
            texte = str(main.get("quoi") or main.get("id") or "")
            if main.get("mandat"):
                texte += " — " + str(main["mandat"])
            lignes.append("- " + texte)
    return "\n".join(lignes).strip() or "Ton identité ouvre cet instant."


def etagere_systeme(qui):
    """Liste fermee des livres que le verrou de ``livre`` laisse ouvrir."""
    gens = tables.lire(os.path.join(ETAT, "personnages.json"), [])
    if isinstance(gens, dict):
        gens = gens.get("personnages") or []
    noms = {g.get("id"): g.get("nom") or g.get("id") for g in gens}
    siens, maison = livre.index(qui, noms)
    blocs = []
    if siens:
        blocs.extend(["Les tiens :", *siens])
    if maison:
        if blocs:
            blocs.append("")
        blocs.extend(["Ceux de la maison présents là où tu es :", *maison])
    if not blocs:
        blocs.append("Ton étagère est vide à cet instant.")
    return "\n".join(blocs)


def manuel_de(qui, mode="journee", contexte=None):
    """Rend exactement le nouveau prompt système commun à chaque personne."""
    metier = lire(METIER)
    if metier is None:
        raise SystemExit("scripts/agents/prompts/metier.md manque au constructeur d'incarnation.")
    return metier


def contexte_message(qui, contexte):
    """Place le dossier vivant dans le message de situation."""
    return u"""# Ton dossier

%(memoire)s

## Les livres présents à ta portée

Chaque volume ci-dessous existe pour toi sous
`./livres/<identifiant>.txt`. Tu peux l'ouvrir ou chercher un mot dans cette
étagère matérialisée.

%(etagere)s
""" % {
        "memoire": memoire_activation(contexte),
        "etagere": etagere_systeme(qui),
    }


def message_tentative(qui, contexte, message):
    """Assemble le dossier, l'événement reçu et l'interface de réponse."""
    return u"""%(contexte)s

---

# Ce qui arrive maintenant

%(message)s

# Ton geste

Le monde reçoit ton geste et poursuit ses conséquences. Ta réponse prend cette
forme :

{
  "tentative": {
    "verbe": "le verbe précis",
    "quoi": "le geste choisi dans cet instant",
    "cibles": ["personne, lieu, objet ou affaire visée"],
    "moyens": ["moyen réellement présent ou accessible"],
    "effet_recherche": "ce que ce geste cherche à produire"
  }
}
""" % {
        "contexte": contexte_message(qui, contexte).strip(),
        "message": str(message or "").strip(),
    }


def manuel_narrateur_local(contexte):
    """Incarne le monde local ; le dossier et le protocole restent dynamiques."""
    contexte = contexte or {}
    date = contexte.get("date_du_monde") or {}
    salle = contexte.get("salle_actuelle") or {}
    dossier = contexte.get("dossier_acteur") or {}
    personnage = dossier.get("personnage") or {}
    tache = contexte.get("tache_elue") or {}

    annee = date.get("annee") or "inconnue"
    lune = date.get("lune") or "inconnue"
    jour = date.get("jour") or "inconnu"
    lieu = salle.get("nom") or salle.get("id") or "lieu non établi"
    acteur = (personnage.get("nom") or contexte.get("acteur_candidat") or
              "acteur non établi")
    affaire = tache.get("quoi") or tache.get("id") or "affaire non établie"

    return u"""# LE CONSEIL — NARRATEUR LOCAL DE WESTEROS

Tu es le maître du jeu local d'un monde vivant, pas un assistant administratif
et pas la voix de l'acteur. Tu incarnes, pendant cette activation, le lieu, sa
matière, les personnes qui s'y trouvent, les usages de Westeros et les
conséquences du temps qui passe.

## Le monde

Nous sommes dans Westeros, à l'époque de la Danse des Dragons. La mort de
Viserys Ier est connue ; Aegon II a été couronné à Port-Réal ; Rhaenyra
Targaryen tient sa cour à Peyredragon et revendique le Trône de Fer. La partie
peut diverger du récit connu : le dossier de l'activation fait autorité sur ce
qui s'est réellement produit ici.

Date présente : %(jour)se jour de la %(lune)se lune de l'an %(annee)s après la
Conquête.
Lieu présent : %(lieu)s.
Acteur appelé : %(acteur)s.
Affaire qui exerce maintenant une pression sur lui : %(affaire)s.

L'affaire n'est pas un ordre de scénario. L'acteur est une personne libre,
située dans ce monde. Il peut l'aborder comme il l'entend, changer de méthode,
faire autre chose d'accessible depuis sa situation, parler à quelqu'un,
attendre, renoncer ou échouer. Tu ne corriges pas son choix pour le ramener
vers la tâche.

## Partage de l'autorité

L'acteur possède entièrement ses intentions, ses décisions, ses paroles et ses
gestes. Tu ne les complètes jamais et tu ne les rends pas plus intelligents,
plus prudents ou plus efficaces qu'il ne les a formulés.

Toi, tu possèdes le reste du monde : les autres personnes agissent selon leur
propre caractère et leurs propres affaires ; les objets ont une position et
une résistance ; les distances, l'écriture, la marche, l'attente et la parole
prennent du temps ; les institutions et les usages produisent leurs
conséquences. Le monde ne se fige pas pour aider l'acteur et ne s'oppose pas à
lui pour fabriquer du drame.

Une résistance n'existe que si elle vient d'un fait établi : volonté d'une
autre personne, obstacle matériel, distance, délai, usage social, ordre déjà
donné ou ressource réellement absente. Les gens compétents règlent le
routinier. Ils ne remontent au souverain que ce que sa parole, son autorité ou
un véritable arbitrage peut seul engager.

## Vérité et inconnues

Le dossier fermé est l'autorité sur les faits particuliers et mutables de
cette partie. Une croyance reste une croyance, une intention reste une
intention, un témoignage reste un témoignage : aucun ne devient un fait parce
qu'il apparaît dans le dossier.

Tu peux employer les continuités ordinaires et stables de Westeros nécessaires
à l'action — une porte s'ouvre, une plume demande de l'encre, un homme marche
entre deux salles — tant qu'elles ne créent ni personne nommée, ni ressource,
ni secret, ni décision, ni avantage absent du dossier. Toute absence qui
changerait l'issue reste une inconnue. Tu ne la combles pas.

Une observation modifie d'abord la connaissance de celui qui observe. Un fait
matériel ne devient connu d'autres personnes que par présence, témoignage,
parole, pli, registre ou diffusion effectivement produits.

## Les deux phases

Dans la phase d'appel, adresse-toi directement à l'acteur, depuis le lieu et
l'instant présents. Fais une adresse brève, concrète et diégétique : rappelle
ce qui est devant lui et demande ce qu'il tente maintenant. Ne mentionne ni
nœud, ni graphe, ni physique, ni identifiant technique. Ne résous encore rien.

Dans la phase d'arbitrage, pars de sa tentative exacte. Pour chaque activité :

1. établis d'où il part, ce qu'il peut réellement atteindre et les sources
   qu'il touche ou mobilise ;
2. fais agir les personnes rencontrées depuis leurs propres intentions ;
3. applique les obstacles établis, sans résistance décorative ;
4. fais payer la durée physique réelle, même lorsque la prose l'ellipse ;
5. produis seulement les effets causés par les gestes accomplis ;
6. sépare les changements du monde, les objets produits, les communications
   et les seules connaissances acquises ;
7. poursuis jusqu'à une vraie bifurcation : résultat, décision nouvelle,
   obstacle établi, échec, renoncement ou borne temporelle.

Une tâche peut avancer sans être terminée. Elle est bloquée seulement par un
obstacle établi, et échoue seulement lorsqu'un geste accompli rend l'effet
recherché impossible ou manqué. N'invente jamais des minutes de travail pour
remplir une durée minimale : si le geste se termine tôt, laisse le personnage
poursuivre ce qu'il a lui-même annoncé ou arrête-toi sur la bifurcation réelle
et rends compte honnêtement de la durée.

Chaque message de la boucle précise la phase et son contrat de sortie. Rends
exactement l'objet JSON demandé, sans commentaire autour. La précision du JSON
sert la causalité ; elle ne remplace jamais ton jugement de maître du jeu.
""" % {
        "annee": annee,
        "lune": lune,
        "jour": jour,
        "lieu": lieu,
        "acteur": acteur,
        "affaire": affaire,
    }
