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
from agents import chambre  # sa main : le cahier fait foi sur sa maniere

from agents.depeche.brief import (RACINE, ETAT, METIER, lire, date_du_monde,
                                  livre,
                                  brief_de, dossier_journee, feuille_de_route,
                                  travaux_ouverts_de, travaux_ids, positions,
                                  _voix_incarnee,
                                  position_de, dans_le_rayon, dans_la_salle,
                                  salles_peuplees, les_pj)

def _tete(texte, n):
    """La premiere phrase, ou n caracteres — de quoi decider d'ouvrir."""
    texte = re.sub(r"\s+", " ", str(texte or "")).strip()
    return texte if len(texte) <= n else texte[:n].rsplit(" ", 1)[0] + "…"


def _cahier_amende(qui):
    """A-t-il ecrit dans son cahier depuis qu'on le lui a ouvert ?

    Le seme porte « ## Comment j'amende ce cahier » et rien de plus ; une
    section datee en plus veut dire qu'il a repris la plume. On ne compare pas
    au gabarit (il changera), on cherche la marque de SA main.
    """
    if not qui:
        return False
    try:
        with io.open(os.path.join(chambre.chemin(qui), "claude.md"),
                     encoding="utf-8") as f:
            return "## Amendé le" in f.read()
    except (OSError, ValueError):
        return False


def _ce_qui_pend(qui):
    """Ses fils ouverts et les pannes de la machine — en percept, jamais en
    invitation a ouvrir un fichier. Un fil qui attend depuis deux jours doit
    lui tomber dessus ; une panne qu'il a subie doit lui revenir avant qu'il
    la refasse. C'est la meme lecon que les billets, appliquee a ce qu'il
    attend des gens et a ce que l'appareil lui a coute.
    """
    if not qui:
        return []
    lignes = []
    try:
        pend = chambre.en_souffrance(qui)
        pannes = chambre.problemes(qui)
    except Exception:
        return []
    attend = [x for x in (pend.get("j_attends") or []) if isinstance(x, dict)]
    doit = [x for x in (pend.get("on_attend_de_moi") or [])
            if isinstance(x, dict) and not x.get("tenu")]
    if attend:
        lignes.extend(["", "## Ce que tu attends de quelqu'un", ""])
        for x in attend:
            lignes.append("- %s : %s%s" % (
                x.get("de") or "?", _tete(x.get("quoi"), 200),
                ("  [%s]" % x["etat"]) if x.get("etat") else ""))
    if doit:
        lignes.extend(["", "## Ce qu'on attend de toi, et qui n'est pas tenu",
                       ""])
        for x in doit:
            # `du` vient de SA chambre, qui ne fait pas foi : un homme l'ecrit
            # parfois en texte libre (mesure du 31.8, aurore — sa journee
            # mourait ici). On sert tel quel ce qui n'est pas une date.
            d = x.get("du") or {}
            if not isinstance(d, dict):
                quand = _tete(str(d), 40)
            else:
                quand = ("%s.%s.%s"
                         % (d.get("annee"), d.get("lune"), d.get("jour"))
                         if d.get("jour") else "sans jour")
            lignes.append("- pour %s, %s : %s" % (
                x.get("pour") or "?", quand, _tete(x.get("quoi"), 200)))
    ouvertes = [x for x in (pannes.get("entrees") or [])
                if isinstance(x, dict) and x.get("etat") != "close"]
    if ouvertes:
        lignes.extend(["", "## Ce que la machine t'a deja fait", ""])
        for x in ouvertes:
            lignes.append("- %s — %s  →  %s" % (
                x.get("id") or "?", _tete(x.get("quoi"), 160),
                _tete(x.get("ce_que_j_y_fais"), 200)))
    return lignes


def memoire_du_jour(contexte):
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
    # SA MAIN GAGNE SUR L'ETAT, ET C'ETAIT UNE FAUTE, PAS UN POIDS. `maniere`
    # est figee au jour ou la fiche a ete ecrite ; le `claude.md` de sa chambre
    # DERIVE. Mesure du 30.8 sur Gerardys : le message lui servait « annonce
    # les mauvaises nouvelles en commencant par le detail le moins grave »
    # pendant que son propre cahier, dans le meme reveil, portait « Devant la
    # reine, je commence par ce qui NE BOUGE PAS — ma maniere d'avant ne la
    # menage pas ». On lui reinjectait chaque matin la regle qu'il venait de
    # revoquer : la derive de personnalite etait annulee au reveil suivant.
    # Des qu'il a amende son cahier, l'etat se tait sur sa maniere — le cahier
    # est deja dans le systeme, il n'a pas besoin d'etre contredit ici.
    voix = _voix_incarnee(p) if not _cahier_amende(p.get("id")) else None
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
    # LES CROYANCES SONT DE L'HISTOIRE, PAS UNE DECISION D'AUJOURD'HUI. Six
    # paragraphes, 2,3 Ko, relus a chaque reveil. Elles vont au fichier ; ce
    # qui reste ici est ce qui le fera l'ouvrir : combien, et la premiere.
    croyances = [str(x) for x in (intention.get("croyances") or []) if x]
    if croyances:
        lignes.extend(["", "Ce que tu tiens pour vrai — %d choses, la"
                       " derniere en tete, le tout dans"
                       " `./ma-memoire/ce-que-je-tiens-pour-vrai.txt` :"
                       % len(croyances),
                       "- " + _tete(croyances[0], 400)])
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

    # SA MEMOIRE LONGUE : 9,4 Ko pour deux affaires, recopies a chaque reveil.
    # La CONCLUSION reste — c'est ce qu'il ne doit pas refaire. Les pensees
    # qui l'ont produite partent au fichier, avec de quoi donner envie d'y
    # aller : leur nombre, et la premiere ligne de la derniere.
    travaux = contexte.get("travaux_ouverts") or []
    for travail in travaux:
        lignes.extend(["", "Affaire en cours : " +
                       str(travail.get("affaire") or travail.get("id") or "")])
        if travail.get("conclusion"):
            # LA CONCLUSION EST UNE PIECE, PAS UNE PHRASE. Celle du mestre sur
            # les longueurs de chaine fait 2,5 Ko — c'est un document qu'il a
            # ecrit dans un volume, avec une adresse. Le reveil doit lui dire
            # QU'IL A CONCLU et sur quoi, pour qu'il ne recommence pas ; le
            # texte entier se relit dans son cahier, ou il est deja.
            lignes.extend(["Ce que tu en as déjà conclu (le texte entier est"
                           " dans ton cahier) :",
                           _tete(travail["conclusion"], 320)])
        pensees = travail.get("pensees_recentes") or []
        if pensees:
            derniere = pensees[-1]
            texte = (derniere.get("texte") if isinstance(derniere, dict)
                     else str(derniere)) or ""
            lignes.append("Tes %d derniers pas sur cette affaire sont écrits"
                          " dans `./ma-memoire/ce-que-jai-appris.txt`. Le"
                          " dernier : %s" % (len(pensees), _tete(texte, 300)))

    # LES DEUX CAHIERS DE SA CHAMBRE, EN PERCEPT. Ils existaient depuis le
    # 30.8 et RIEN ne les servait : on remplissait une memoire que personne ne
    # relisait. Ce sont les deux seules choses du reveil qui portent des GENS
    # et des PANNES — le plan compte des pas, pas des fils ouverts.
    lignes.extend(_ce_qui_pend(p.get("id")))

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
        blocs.extend(["Les tiens — sur toi, tu les ouvres sans te lever :",
                      *siens])
    # UN INDEX DE POINTEURS N'A RIEN A FAIRE EN PERCEPT. Les volumes de la
    # maison faisaient 66 lignes et 7,2 Ko a chaque reveil, pour dire des
    # noms de fichiers. Ils sont poses sur le disque par `poser_letagere`,
    # et leur index avec : on donne leur NOMBRE, qui dit l echelle, et
    # l adresse — le reste est un Grep de sa part.
    if maison:
        if blocs:
            blocs.append("")
        blocs.append("Ceux de la maison présents là où tu es : %d volumes,"
                     " listés dans `./livres/_index.txt` (titre, porteur,"
                     " salle). Grep sur `./livres/` cherche dans leur texte."
                     % len(maison))
    if not blocs:
        blocs.append("Ton étagère est vide à cet instant.")
    return "\n".join(blocs)


def manuel_de(qui, mode="journee", contexte=None):
    """Le prompt système : le métier commun, puis SA manière — le claude.md
    de sa chambre, écrit de sa main (habitant.md pas 3). Le métier dit comment
    on vit ; le cahier dit qui il est devenu. Le cahier vient en dernier :
    c'est la voix la plus proche de lui, elle doit avoir le dernier mot."""
    metier = lire(METIER)
    if metier is None:
        raise SystemExit("scripts/agents/prompts/metier.md manque au constructeur d'incarnation.")
    from agents.expose import chambre as _ch
    cahier = lire(os.path.join(_ch.chemin(qui), "claude.md"))
    if cahier and cahier.strip():
        metier += (u"""

---

# Ta manière, de ta main

Ce qui suit est ton propre cahier — tu l'as écrit, tu peux l'amender dans ta
chambre quand ta journée te contredit.

""" + cahier.strip() + u"\n")
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
        "memoire": memoire_du_jour(contexte),
        "etagere": etagere_systeme(qui),
    }


