# -*- coding: utf-8 -*-
"""GARDES DES ECRITS — pensees, livres, coffrets, croyances sans porteur.

CE QUE CE MODULE POSSEDE : les verificateurs de ce qui S'ECRIT et se lit dans
le monde — les pensees (pas de source, pas de pensee), les livres et coffrets
de docs/books.md (cles hors format, prive qui ne ferme rien, emblemes qui se
confondent), et qui a du temps aujourd'hui (la feuille de route d'evaluer.py,
lue par le tick). La croyance sans porteur vit dans croyances.py.

CE QU'IL REFUSE : comprendre le francais — le recoupement de mots rares est
une heuristique, assumee comme telle.

CONSOMMATEURS : gardes/__init__.py (verifier()), et fenetre.py
(qui_a_du_temps, l'entree de la salle).
"""
import json
import os
import sys

from temps.bouche import croyances_de, se_recoupent


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
