# node_id=code:l2:le-conseil:depecher-narrateur-local-python-v1 | node_name=CodeDefinition - Le Conseil local narrator in Westeros v1 | graph=l2:mind-kernel
# -*- coding: utf-8 -*-
# DEPECHER — envoyer un homme vivre sa journee, dans une session a lui.
#
# La piece qui manquait au bout de docs/session-travail.md : `convoquer.py` dit
# QUI doit une journee et redige son brief ; celui-ci le DEPECHE pour de bon,
# par `claude -p`, et rapporte ce qu'il a trouve.
#
# ─────────────────────────────────────────────────────────────────────────────
# POURQUOI ON NE LANCE PAS L'APPEL DEPUIS LE DEPOT. Mesure du 9 aout, deux
# appels identiques a un mot pres :
#
#     depuis le depot          89 051 jetons de contexte
#     depuis ailleurs          31 000 jetons de contexte
#
# La difference, c'est CLAUDE.md — le manuel du MJ, ses modes, son rendu, sa
# discipline d'ecriture d'etat — charge d'office par la decouverte automatique,
# et dont un sergent au role n'a pas l'usage. Huit fois le prix pour lire des
# regles d'affichage qui ne le concernent pas. On lance donc depuis un
# repertoire neutre, hors du depot, et l'on rouvre le depot par `--add-dir` :
# il garde ses yeux, il perd le manuel.
#
# C'est cette mesure, et elle seule, qui a fait scinder CLAUDE.md. `docs/
# metier.md` est la moitie qui parle a un homme : ce qu'il apporte, le peage
# avant d'ouvrir la bouche, les deux jets, comment il parle. Il est AUTONOME —
# son lexique de pied resout les cinq mots qu'il avait herites du manuel — et
# c'est lui, et rien d'autre, qu'on met dans le prompt systeme.
#
# ─────────────────────────────────────────────────────────────────────────────
# L'HOMME A DES MAINS — decision du 9 aout, et elle enterre la regle du seul
# ecrivain. Read, Grep, Glob et Bash. Le pretendu verrou d'avant etait une
# fiction : la regle `Bash(python .../parloir.py:*)` n'a jamais tenu, et Hask
# a lance ls, cat, wc et python -c toute sa journee sans que rien l'arrete.
# On avait donc deja le risque et pas le benefice ; desormais c'est assume.
#
# Ce que ca coute, et il faut le savoir : deux sessions peuvent ecrire le meme
# fichier en meme temps, et la derniere gagne. Ce qui protege l'etat n'est
# plus l'impuissance de l'homme, c'est `scripts/ajouter.py` (une entree a la
# fois, jamais un tableau reecrit) et `scripts/veille.py` (ce que l'autre a
# touche). Sa reponse FINALE reste son rapport, et c'est ce script qui la pose
# dans etat/rapports/ ET la verse aussitot dans etat/travaux.json.
#
# ─────────────────────────────────────────────────────────────────────────────
# LA SESSION EST STABLE PAR HOMME ET PAR JOUR DE JEU. uuid5 sur
# « le-conseil/<homme>/<annee>.<lune>.<jour> » : deterministe, donc
# retrouvable sans registre a tenir, et neuve a chaque jour de jeu. C'est la
# bonne maille — la doctrine donne DEUX travaux par journee d'homme, et l'on
# veut que le second se souvienne de ce que le premier a trouve le matin, sans
# heriter de la veille.
#
# Mesure, pas supposition : `--session-id` REFUSE un id deja vu
# (« Session ID ... is already in use »). On tente donc --session-id, et l'on
# retombe sur --resume, qui reprend en place et rend le meme id.
#
# Usage :
#     python scripts/depecher.py --qui le-sanglier
#     python scripts/depecher.py --tous
#     python scripts/depecher.py --qui sara --sec      montre tout, n'appelle pas
#     python scripts/depecher.py --qui sara --mission "..."   consigne du jour
import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livre  # le tri des volumes vit la-bas, et nulle part ailleurs
import affecter  # LE resolveur d'adresses : on ne relit plus `xyz` a la main

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
DEPOT_RAPPORTS = os.path.join(ETAT, "rapports")
METIER = os.path.join(RACINE, "docs", "metier.md")
MANUEL_MJ = os.path.join(RACINE, "CLAUDE.md")

# Le sel de l'espace de noms. Le changer rend toutes les sessions orphelines
# d'un coup : c'est le seul geste qui reparte de zero proprement.
# v2 force une session neuve après le passage au prompt système explicite :
# reprendre une session v1 conserverait précisément le contexte global pollué.
SEL = uuid.uuid5(uuid.NAMESPACE_URL, "le-conseil/depeches/v5")

OUTILS = ["Read", "Grep", "Glob", "Bash"]

# LE PARLOIR — sa bouche, quand on lui parle pendant sa journee. Il l'appelle
# par Bash, qu'il a desormais en entier (voir l'en-tete).
PARLOIR_PY = os.path.join(RACINE, "scripts", "parloir.py").replace("\\", "/")
OUTIL_PARLOIR = "Bash(python %s:*)" % PARLOIR_PY

def lire(chemin, defaut=None):
    if not os.path.exists(chemin):
        return defaut
    with io.open(chemin, encoding="utf-8") as f:
        return f.read()


def date_du_monde():
    """Le jour LE PLUS AVANCE des sieges occupes — pas `monde.date`.

    `monde.date` porte l'horloge la moins avancee : c'est celle du siege
    principal, et elle ne bouge que quand LUI joue. Les autres sieges avancent
    la leur par `append_flux.py`, chacun a son rythme. Mesure du 129.4.1 :
    monde au 3.30 pendant que les trois sieges occupes etaient au 4.1 — un
    homme depeche sur `monde.date` aurait revecu le 30e une seconde fois, et
    ses pensees seraient tombees, datees d'hier, a cote de celles d'hier.

    On prend donc le maximum, jamais le minimum : une journee deja vecue ne se
    rejoue pas, tandis qu'un homme depeche un jour trop tot est simplement en
    avance sur le siege qui traine.
    """
    m = json.loads(lire(os.path.join(ETAT, "monde.json"), "{}"))
    d = m.get("date", {})
    jours = [(d.get("annee", 0), d.get("lune", 0), d.get("jour", 0))]
    joueurs = json.loads(lire(os.path.join(ETAT, "joueurs.json"), "[]"))
    if isinstance(joueurs, dict):
        joueurs = joueurs.get("joueurs", [])
    occupes = set()
    for j in joueurs or []:
        if isinstance(j, dict) and j.get("occupe") and not j.get("regie"):
            occupes.add(j.get("personnage_id") or j.get("id"))
    horloges = json.loads(lire(os.path.join(ETAT, "horloges.json"), "{}"))
    for qui, h in (horloges or {}).items():
        if qui in occupes and isinstance(h, dict):
            jours.append((h.get("annee", 0), h.get("lune", 0), h.get("jour", 0)))
    return max(jours)


def identifiant_de_session(qui, date):
    """Stable par homme et par jour de jeu. Deterministe : aucun registre."""
    return str(uuid.uuid5(SEL, "%s/%d.%d.%d" % ((qui,) + date)))


_FEUILLE = {}


def feuille_de_route():
    """Qui a du temps aujourd'hui, combien de questions, et DANS QUELLE SALLE.

    Remplace `convoquer.py` en entier. L'ancien disait qui « doit une journee »
    d'apres un compteur d'excitation qui montait sans sources et retombait d'un
    point par jour ; le neuf lit ce que la journee dit d'elle-meme — le
    quartier, les creux, la force sur le graphe (`evaluer.force_narrative`).

    Une entree : {qui, force, questions, creux_total, questions_posees:[{de, a,
    salle}]}. C'est la salle qui compte autant que la duree : une question
    posee a la roukerie n'a pas les memes sources qu'une posee au bourg.
    """
    if _FEUILLE:
        return _FEUILLE
    try:
        sys.path.insert(0, os.path.join(RACINE, "scripts"))
        import evaluer
        A, N = evaluer.lire_tissu()
        for l in evaluer.force_narrative(A, N, lambda t="": None):
            _FEUILLE[l["qui"]] = l
    except Exception as e:
        _FEUILLE["__erreur__"] = {"qui": "__erreur__", "motif": str(e)[:160]}
    return _FEUILLE


def _heure(m):
    return "%dh%02d" % ((int(m) // 60) % 24, int(m) % 60)


def brief_de(qui):
    """Sa journee telle que l'etat la dit : ses creux, ce qu'il sait deja.

    PAS DE SOURCE, PAS DE PENSEE — la contrainte d'entree est la seule chose de
    l'ancien systeme qui meritait de survivre. Ce qui change : la source n'est
    plus declaree d'avance dans une liste de courses tenue a la main. Elle est
    CE QUI EST A PORTEE DU CREUX — les livres poses dans la salle, les gens qui
    s'y trouvent au meme moment, les mesures dont il est porteur. Le creux dit
    ou il est ; l'etat dit ce qu'il y a la.
    """
    l = feuille_de_route().get(qui) or {}
    pensees = [p for p in _liste_etat("pensees.json", "pensees")
               if p.get("qui") == qui]
    concl = [c for c in _liste_etat("conclusions.json", "conclusions")
             if c.get("qui") == qui]
    livres = _liste_etat("books.json", "books")

    out = ["== SA JOURNEE — ce que l'etat en dit"]
    if not l:
        out.append("  Aucune tete dans intentions.json : il n'a pas de journee.")
        return "\n".join(out)
    if not l.get("creux"):
        out.append("  AUCUN CREUX aujourd'hui (%s). Il ne pense pas : il"
                   " travaille, et travailler est une action visible."
                   % (l.get("hors_quartier") or "journee fermee"))
        return "\n".join(out)

    out.append("  force %s sur le graphe · %d minutes libres · %d question(s)"
               % (l.get("force"), l.get("creux_total") or 0,
                  l.get("questions") or 0))
    out.append("")
    out.append("  SES CREUX — quand il a le temps, et OU il se tient alors :")
    par_salle = {}
    for c in l.get("questions_posees") or l.get("creux") or []:
        out.append("    %s -> %s  %-20s %4d min%s" % (
            _heure(c["de"]), _heure(c["a"]), c["salle"], c["minutes"],
            "   (%s)" % c["pourquoi"] if c.get("pourquoi") else ""))
        par_salle.setdefault(c["salle"], 0)
    # CE QUI EST A PORTEE DE CES SALLES-LA : les livres qu'on peut y ouvrir.
    a_portee = [b for b in livres if b.get("salle_id") in par_salle]
    sien = [b for b in livres if b.get("acteur_id") == qui]
    if a_portee or sien:
        out.append("")
        out.append("  CE QU'IL PEUT TOUCHER SANS SORTIR DE SES CREUX :")
        for b in sien:
            out.append("    (sur lui) %s — %s" % (b.get("id"), b.get("titre")))
        for b in a_portee:
            out.append("    [%s] %s — %s" % (b.get("salle_id"), b.get("id"),
                                             b.get("titre")))
    if concl:
        out.append("")
        out.append("  CE QU'IL A DEJA CONCLU, de sa main (ne pas le refaire) :")
        for c in concl:
            out.append("    %s  → %s" % (c.get("affaire"),
                                         c.get("livre") or "aucun cahier"))
    if pensees:
        def rang(p):
            d = p.get("date") or {}
            return (d.get("annee", 0), d.get("lune", 0), d.get("jour", 0))
        recentes = sorted(pensees, key=rang, reverse=True)[:8]
        out.append("")
        out.append("  CE QU'IL SAIT DEJA (%d pensees, les %d dernieres) — pour"
                   " qu'il ne retrouve pas ce qu'il a deja trouve :"
                   % (len(pensees), len(recentes)))
        for p in recentes:
            out.append("    · %s" % re.sub(r"\s+", " ",
                                           str(p.get("texte") or ""))[:220])
    return "\n".join(out)


def _liste_etat(nom, cle):
    donnees = json.loads(lire(os.path.join(ETAT, nom), "[]"))
    if isinstance(donnees, dict):
        donnees = donnees.get(cle) or []
    return donnees if isinstance(donnees, list) else []


def _voix_incarnee(personnage):
    """Garde l'empreinte personnelle et coupe l'ancienne doctrine ajoutée.

    Plusieurs ``maniere`` ont reçu au fil du jeu un même manuel de conduite.
    Le prompt neuf conserve la voix écrite avant ces ajouts universels.
    """
    texte = str((personnage or {}).get("maniere") or "").strip()
    marqueurs = (
        " Se debrouille seul", " Se débrouille seul", " Competent :",
        " Compétent :", " OUVRE PAR :", " DEUXIEME PHRASE",
        " REPRIS,", " AUCUNE ",
    )
    coupures = [texte.find(m) for m in marqueurs if texte.find(m) >= 0]
    if coupures:
        texte = texte[:min(coupures)].strip()
    return texte


def _relations_de(qui, noms):
    relations = _liste_etat("relations.json", "relations")
    resultat = []
    for relation in relations:
        source = relation.get("source_id")
        cible = relation.get("cible_id")
        if qui not in (source, cible):
            continue
        resultat.append({
            "source_id": source,
            "source": noms.get(source, source),
            "cible_id": cible,
            "cible": noms.get(cible, cible),
            "opinion": relation.get("opinion"),
            "liens": relation.get("liens") or [],
        })
    return resultat


def _affaires_du_brief(brief):
    """Extrait du brief les affaires vécues, avant son ancien mode d'emploi."""
    texte = str(brief or "")
    debut = texte.find("POURQUOI ON LE CONVOQUE")
    fin = texte.find("CE QU'IL RAPPORTE")
    if debut >= 0:
        texte = texte[debut:fin if fin > debut else None]
    texte = texte.replace("ce qu'il n'a pas encore touche :",
                          "ses prochaines sources :")
    texte = texte.replace("ce qu’il n’a pas encore touché :",
                          "ses prochaines sources :")
    return texte.strip(" =\n")


def dossier_journee(qui, brief):
    """Rassemble l'identité et la situation vivante d'une journée."""
    personnages = _liste_etat("personnages.json", "personnages")
    noms = {p.get("id"): p.get("nom") or p.get("id")
            for p in personnages if isinstance(p, dict) and p.get("id")}
    personnage = next((p for p in personnages if p.get("id") == qui), {})
    personnage = {k: personnage.get(k) for k in
                   ("id", "nom", "titre", "naissance", "traits", "objectifs",
                    "maniere", "portrait", "etat", "condition", "lieu_id")
                   if k in personnage}

    intentions = _liste_etat("intentions.json", "intentions")
    intention = next((i for i in intentions
                      if i.get("personnage_id") == qui), {})
    intention = {k: intention.get(k) for k in
                 ("personnage_id", "croyances", "ignore", "intention",
                  "declencheurs", "attitude_joueur", "mandat", "date_maj")
                 if k in intention}

    presence = json.loads(lire(os.path.join(ETAT, "presence.json"), "{}"))
    resolus = ((presence.get("resolu") or {}).get("gens") or {}) \
        if isinstance(presence, dict) else {}
    position = resolus.get(qui) or {}
    salle_id = position.get("salle")
    presents = [{"id": pid, "nom": noms.get(pid, pid)}
                for pid, ou in resolus.items() if salle_id and
                ou.get("salle") == salle_id]
    presents.sort(key=lambda p: (p["nom"].casefold(), p["id"]))

    return {
        "date_du_monde": dict(zip(("annee", "lune", "jour"),
                                   date_du_monde())),
        "personnage": personnage,
        "salle_actuelle": {
            "id": salle_id,
            "nom": position.get("lieu") or salle_id or personnage.get("lieu_id"),
            "personnes": presents,
        },
        "intention": intention,
        "relations": _relations_de(qui, noms),
        "affaires_du_jour": _affaires_du_brief(brief),
    }


def a_convoquer():
    """Qui vaut d'etre depeche aujourd'hui : ceux a qui la journee laisse du
    temps, les plus forts d'abord. Un homme sans creux n'est pas convocable —
    il ne penserait pas, il ferait semblant."""
    f = feuille_de_route()
    ayants = [l for l in f.values() if l.get("questions")]
    ayants.sort(key=lambda l: -l.get("force", 0))
    return [l["qui"] for l in ayants]


def les_pj():
    """Les sieges OCCUPES. On ne depeche jamais un personnage joueur : sa tete
    appartient a quelqu'un, et la faire vivre par une session serait parler a
    sa place. C'est une exclusion DURE — il n'y a pas de drapeau pour la
    lever, parce qu'il n'y a pas de cas ou l'on voudrait."""
    j = json.loads(lire(os.path.join(ETAT, "joueurs.json"), "[]"))
    if isinstance(j, dict):
        j = j.get("joueurs") or j.get("sieges") or []
    return {s.get("personnage_id") or s.get("id")
            for s in j if s.get("occupe")}


def salles_peuplees():
    """{salle: [ids]} d'apres les positions RESOLUES par scripts/presence.py.
    On ne lit pas `presence` brut : c'est le declaratif, `resolu` est ce qui
    tient compte des deplacements."""
    d = json.loads(lire(os.path.join(ETAT, "presence.json"), "{}"))
    gens = ((d.get("resolu") or {}).get("gens") or {})
    par_salle = {}
    for qui, ou in gens.items():
        par_salle.setdefault(ou.get("salle"), []).append(qui)
    return par_salle


def dans_la_salle(salle):
    """Qui depecher dans cette salle. Rend (a_depecher, pj_ecartes)."""
    gens = sorted(salles_peuplees().get(salle, []))
    pj = les_pj()
    return [q for q in gens if q not in pj], [q for q in gens if q in pj]


def positions():
    """{personnage_id: (x, y, z)} — en metres reels, comme partout ici.

    Deux chemins, dans cet ordre. Le corps PROPRE d'abord (`etat/corps.json`,
    `corps[]`), qui est une adresse a lui. Sinon la position de la SALLE ou il
    se tient, prise dans les `affectations` : c'est une approximation assumee
    et c'est la bonne — deux hommes dans la meme piece sont a portee de voix,
    et c'est tout ce qu'un rayon de dix metres cherche a dire.

    Un corps EMPRUNTE (`liens`) n'est pas resolu ici : ses coordonnees vivent
    dans `monde/gens/`, qui pese quatre cent mille ames et se regenere. Ces
    gens-la retombent sur la position de leur salle, ce qui suffit.
    """
    C = json.loads(lire(os.path.join(ETAT, "corps.json"), "{}"))
    P = json.loads(lire(os.path.join(ETAT, "presence.json"), "{}"))
    af = C.get("affectations") or {}
    gens = ((P.get("resolu") or {}).get("gens") or {})

    ou = {}
    for c in (C.get("corps") or []):
        if c.get("x") is not None:
            ou[c["personnage_id"]] = (c["x"], c["y"], c.get("z") or 0)
    for qui, p in gens.items():
        if qui in ou:
            continue
        s = p.get("salle")
        # Une salle du plan que le monde a creusee a des metres SANS qu'aucune
        # affectation ne l'ait dit : c'est `affecter.adresse` qui le sait, et
        # c'est ce qui sortait trente-deux personnes du rayon en silence.
        xyz = affecter.adresse(s) if s else None
        if xyz:
            ou[qui] = xyz
    return ou


def position_de(cible, ou):
    """La cible d'un rayon : quelqu'un, ou une salle."""
    if cible in ou:
        return ou[cible]
    return affecter.adresse(cible)


def dans_le_rayon(cible, metres):
    """Rend (a_depecher, pj_ecartes, sans_position).

    `sans_position` n'est pas du bruit : ce sont des gens qui sont peut-etre
    la et que le rayon ne peut pas voir, faute d'adresse physique pour leur
    salle. On les NOMME — un rayon qui les tairait donnerait une salle a
    moitie vide sans le dire, et l'on croirait avoir depeche tout le monde.
    """
    ou = positions()
    centre = position_de(cible, ou)
    if centre is None:
        raise SystemExit(
            u"« %s » n'a pas d'adresse physique — ni corps, ni salle affectee.\n"
            u"  python scripts/affecter.py    pour lui en donner une" % cible)

    P = json.loads(lire(os.path.join(ETAT, "presence.json"), "{}"))
    tous = ((P.get("resolu") or {}).get("gens") or {})
    pj = les_pj()
    dedans, ecartes, aveugles = [], [], []
    for qui in sorted(tous):
        p = ou.get(qui)
        if p is None:
            aveugles.append(qui)
            continue
        d = sum((a - b) ** 2 for a, b in zip(p, centre)) ** 0.5
        if d > metres:
            continue
        (ecartes if qui in pj else dedans).append(qui)
    return dedans, ecartes, aveugles


def travaux_ids(qui):
    """LES CREUX DE SA JOURNEE, a la place des identifiants d'affaires.

    On lui demandait de raccrocher chaque pensee a un `travail_id` — et faute
    de le lui donner, il en inventait un que rien ne rattrapait ensuite. Une
    pensee se rattache desormais a un CREUX : une heure et une salle, deux
    choses qu'il vit et qu'il n'a aucune raison d'inventer.
    """
    l = feuille_de_route().get(qui) or {}
    creux = l.get("questions_posees") or l.get("creux") or []
    if not creux:
        return (u"    (aucun creux aujourd'hui — tu n'as pas le temps de "
                u"penser : tu travailles, et travailler se voit)")
    return u"\n".join(u"    %s-%s  %-20s %4d min" % (
        _heure(c["de"]), _heure(c["a"]), c["salle"], c["minutes"])
        for c in creux)


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
    gens = json.loads(lire(os.path.join(ETAT, "personnages.json"), "[]"))
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
        raise SystemExit("docs/metier.md manque au constructeur d'incarnation.")
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

def contrat_rapport_narrateur(contexte):
    """Contrat mécanique donné seulement à la phase d'arbitrage."""
    present = float((contexte or {}).get("present_secondes") or 0)
    minimum = int((contexte or {}).get("duree_minimale_secondes") or 1)
    return u"""## Contrat du rapport

Une activité est un geste continu entre deux bifurcations. Condense toute
continuité routinière ; conserve sa durée physique. Découpe seulement si une
décision, une résistance, un témoin, un lieu, une ressource, une connaissance
ou un résultat change.

Types de résultats : observation, progression_tache, variation_mesure,
deplacement, objet_produit, communication, fait, blocage, echec.

Rends uniquement :
{
  "qui": "acteur_id",
  "activation": {
    "tache": {"id": "tache_id", "quoi": "...", "creee": false},
    "issue": "avance|termine|bloque|echoue|rien",
    "activites": [{
      "id": "act:<acteur>:<ordre>",
      "ordre": 1,
      "temps": {"debut_s": %(present)s, "duree_s": 1, "fin_s": %(present_plus_un)s},
      "action": {"verbe": "...", "quoi": "...", "cibles": ["ref:canonique"]},
      "chemin_execution": [{"ordre": 1, "de": "ref:depart", "relation": "...", "vers": "ref:arrivee", "duree_s": 1}],
      "sources_touchees": [{"ref": "ref:canonique", "mode": "voit|entend|lit|parle|manipule|parcourt|mesure"}],
      "sources_mobilisees": [{"ref": "ref:connue", "mode": "memoire|intention|croyance|mandat|cible_action"}],
      "resultats_produits": [{
        "id": "res:<activite>:1", "type": "observation",
        "cible": "ref:canonique", "avant": null, "apres": "...",
        "portee": "connaissance_acteur", "source_refs": ["ref:canonique"],
        "preuve_refs": [], "certitude": "constate"
      }],
      "blocage": null
    }],
    "suite": null,
    "reveils_suivants": []
  },
  "mutations_proposees": []
}

Contraintes : les activités sont ordonnées, continues et sans chevauchement.
Leur durée totale est comprise entre %(minimum)d secondes et le budget. Chaque
chemin totalise exactement la durée de son activité. Écrire, parler, marcher,
chercher et manipuler prennent réellement du temps ; l'ellipse économise la
prose, jamais les secondes.

Toute adresse vient du dossier. Aucun préfixe `candidate:`. Chaque résultat a
des `source_refs`, présentes dans les sources touchées ou mobilisées, le
chemin, la cible de l'action ou un résultat antérieur. Une continuité reprend
mot pour mot son dernier `apres` dans `avant`.

Une issue `avance` ou `termine` produit un `progression_tache` visant l'id exact
de `tache_elue`; `bloque` produit un `blocage`; `echoue`, un `echec`.

Les mutations sont seulement proposées. CHACUNE PORTE EXACTEMENT CETTE FORME,
et le nom des clés n'est pas négociable — une mutation qui cite son résultat
sous une autre clé que `resultat_id` est jetée sans être lue :

{
  "resultat_id": "res:act:<acteur>:1",
  "table": "intentions",
  "operation": "croyance_ajouter",
  "cible": "<id visé dans cette table>",
  "valeur": "<la valeur, pour les opérations qui en prennent une>",
  "champs": {"<champ>": "<valeur>"}
}

`resultat_id` reprend MOT POUR MOT l'`id` d'un `resultats_produits` du présent
rapport : une mutation qui ne se rattache pas à un résultat déclaré n'a pas eu
lieu. `valeur` ou `champs` selon l'opération, jamais un autre nom. Pas de clé
`cite`, `domaine`, `op`, `personnage_id` ni `table.operation` collés en un seul
mot : la table et l'opération sont deux clés distinctes.

Opérations admises, par table :
  intentions   etape, etape_ajouter, tete, tete_ajouter, croyance_ajouter,
               croyance_retirer, ignore_ajouter, ignore_retirer,
               declencheur_ajouter, declencheur_retirer
  books        affaire_ajouter, affaire_action_ajouter, affaire_action
  evenements   diffusion_livree, diffusion_ajouter, evenement
  personnages  personnage, personnage_ajouter
  monde        monde
  mains        mesure, seuil, main, main_ajouter
  plis         pli, pli_ajouter
  lieux        roukerie
  jetons       incident_propage, incident
  relations    relation, relation_ajouter

Aucune autre table n'existe. Ne propose rien que ta journée n'ait réellement
produit.

Les affaires, dont la `cible` a une forme stricte :
  books.affaire_ajouter          cible = `affaire-<nom-en-kebab>` (neuf),
                                 valeur = {"titre": "..."}
  books.affaire_action_ajouter   cible = `affaire-<...>` (l'affaire entière),
                                 valeur = la LISTE des cellules, une par
                                 colonne de sa table d'actions, dans l'ordre
  books.affaire_action           cible = `affaire-<...>:<n° de l'action>`,
                                 champs = {"<intitulé exact de colonne>": "..."}

Le numéro d'une action est celui de sa première cellule dans le cahier, jamais
l'id d'un nœud du tissu. Une affaire à toi — ce que tu poursuis et qui n'est
écrit nulle part — s'ouvre par `affaire_ajouter`.

Ta tête, dont la forme est aussi stricte, et où l'on se trompe toujours de la
même façon. « Voici ce que je poursuis maintenant », en une phrase, N'EST PAS
une étape : c'est `tete`. Une `etape` patche une étape QUI EXISTE DÉJÀ dans ton
plan, et il faut la nommer par son id :
  intentions.tete            cible = ton id, champs = {"intention": "..."} —
                             la phrase de ce que tu poursuis. Autres champs
                             admis : echelle, attitude_joueur, date_maj.
                             JAMAIS de `valeur` en texte libre.
  intentions.etape           cible = ton id, `etape` = l'id EXACT d'une étape
                             de ton plan (le dossier te le donne),
                             champs = {"etat"|"jours_restants"|"quoi"|"cout"|
                             "si_bloque"|"depend_de"|"accompli": ...}.
                             Sans clé `etape`, la mutation est jetée.
  intentions.etape_ajouter   cible = ton id, valeur = {"id": "<kebab neuf>",
                             "quoi": "..."} — les deux sont requis.
  intentions.croyance_ajouter  cible = ton id, valeur = la croyance en clair.

`cible` est TOUJOURS un personnage_id qui a déjà une tête — jamais un id
d'étape, jamais un id d'affaire. Si tu n'as pas de tête, tu n'en fabriques pas
une par `etape` : c'est `tete_ajouter`, et il faut alors personnage_id,
echelle, croyances, intention, plan et date_maj.

Les relations, où l'on oublie toujours de dire QUI regarde QUI. Une relation
est dirigée et ses deux bouts vivent DANS `valeur`, jamais dans `cible` :
  relations.relation_ajouter  valeur = {"source_id": "<celui qui juge>",
                              "cible_id": "<celui qui est jugé>",
                              "opinion": <entier de -100 à +100>,
                              "liens": [...], "connue_du_joueur": true|false}
  relations.relation          mêmes `source_id` et `cible_id` dans `valeur`
                              pour désigner la relation, puis les champs à
                              changer. La relation doit déjà exister, et le
                              sens compte : A→B n'est pas B→A.
Aucun autre champ n'est admis. Une opinion hors des bornes, ou un `liens` qui
n'est pas une liste, fait jeter la mutation entière.
""" % {
        "present": json.dumps(present),
        "present_plus_un": json.dumps(present + 1),
        "minimum": minimum,
    }


def _mission_historique(qui, brief, consigne):
    depot = os.path.join(RACINE, "").replace("\\", "/")
    gens = json.loads(lire(os.path.join(ETAT, 'personnages.json'), '[]'))
    if isinstance(gens, dict):
        gens = gens.get('personnages', [])
    noms = {g.get('id'): g.get('nom') or g.get('id') for g in gens}
    siens, maison = livre.index(qui, noms)
    etagere = u"""
════════════════════════════════════════════════════════════════════════
CE QUE TU PEUX OUVRIR — ton etagere, et rien de plus

Cette liste est CLOSE. Un volume qui n'y est pas ne t'est pas refuse : il
n'existe pas pour toi. Tu ne le cherches pas, tu ne le devines pas, tu ne
demandes pas pourquoi il n'y est pas. Les carnets des autres, ce qui est
range chez la reine, ce que d'autres yeux se reservent — tu n'en sais rien.

Ils sont POSES A COTE DE TOI, un fichier par volume, dans ./livres/ :
    Read  ./livres/<identifiant>.txt      pour en ouvrir un
    Grep  ... --path ./livres             pour chercher dans tous a la fois

N'ouvre JAMAIS etat/books.json : il porte les volumes de toute la maison,
il fait deux millions de signes, et tu y perdrais ta journee entiere.

%(siens)s%(maison)s
""" % {
        "siens": (u"  LES TIENS — tu les portes, ils sont toujours a portee\n"
                  + u"\n".join(siens) + u"\n\n") if siens else u"",
        "maison": (u"  CEUX DE LA MAISON — poses ou portes la ou tu es\n"
                   + u"\n".join(maison)) if maison else
                  u"  (rien d'autre que les tiens)",
    }
    return u"""%(brief)s
%(etagere)s
════════════════════════════════════════════════════════════════════════
CE QUI EST A TOI AUJOURD'HUI

Le depot est ouvert en lecture a cette adresse : %(depot)s

CE QUI EST GROS, ON LE FOUILLE — ON NE LE LIT PAS. Trois fichiers pesent
plus qu'une journee d'homme : etat/books.json (2 Mo — tu as ton etagere,
n'y touche pas), etat/paroles.json (570 ko), etat/actes.json (400 ko).
Sur les deux derniers : Grep un nom, une date, un mot, et Read seulement
autour de ce que tu as trouve. Un Read entier de l'un d'eux te coute ta
journee et ne te rend rien.

Le reste de etat/ se lit normalement.
`python scripts/dossier.py --sur <sujet>` n'est PAS a ta portee :
tu n'as que des yeux, lis les fichiers.

TON RAPPORT NE SE POSE PAS SUR LE DISQUE PAR TA MAIN : ta derniere reponse
suffit, un autre l'y met. Le brief ci-dessus dit
« dans etat/rapports/... » — ignore cette phrase-la, et cela seulement.

LE PARLOIR — ON PEUT T'ADRESSER LA PAROLE PENDANT TA JOURNEE.

Si quelqu'un te parle, sa phrase te tombera dessus au milieu de ton travail,
sans que tu l'aies demandee. Ce n'est pas une note de service : c'est
quelqu'un qui s'adresse a toi. Tu lui reponds comme dans une piece — court,
dans ta langue, avec ce que tu as sous la main a cet instant :

    python %(parloir)s --dire --de %(qui)s --a mj "..."

Puis tu reprends ton travail exactement ou tu l'avais laisse. Trois choses :
· tu ne reponds que si l'on t'a parle — on ne dit pas bonjour au vide ;
· ce qui se dit au parloir ne remplace PAS ton rapport final, et n'en
  dispense pas : ta journee se rend comme d'habitude, en JSON, a la fin ;
· ce qu'on t'y apprend est une source comme une autre — si ca t'apprend
  quelque chose, ca devient une pensee, avec « au parloir » pour source.

TA DERNIERE REPONSE EST TON RAPPORT, et elle ne contient QUE lui : un objet
JSON, sans phrase avant, sans phrase apres, sans bloc de code autour.

{
  "qui": "%(qui)s",
  "journal": [
    {"heure": "7h00", "duree": 20, "lieu": "<ou tu TRAVAILLES>",
     "quoi": "<ce que tu fais, a la troisieme personne>",
     "resultat": "<ce que ca t'a donne, en clair et chiffre>"},
    {"heure": "7h20", "duree": 15, "de": "<d'ou>", "a": "<vers ou>",
     "quoi": "<il descend au bourg, sa canne sous le bras>", "resultat": "—"}
  ],
  "travaux": [
    {"travail_id": "<un des identifiants donnes plus bas, EXACTEMENT>",
     "dernier_travail": %(aujourdhui)s,
     "pensees": [{"date": %(aujourdhui)s,
                  "source": "<ce que tu as touche, en clair>",
                  "texte": "<ce que ca t'a appris>"}],
     "conclusion": null}
  ],
  "cahier2": [
    {"livre": "...", "table": "...", "ligne": "...", "colonne": "...",
     "valeur": "..."}
  ]
}

TROIS CHOSES QUI FONT REJETER UNE JOURNEE ENTIERE, et qu'on ne devine pas :
· `travail_id` doit etre un identifiant de la liste ci-dessous, au signe pres ;
· chaque pensee porte sa `date`, en objet, et c'est %(aujourdhui)s ;
· la `conclusion` est DANS le travail qu'elle conclut, jamais a la racine —
  et elle reste `null` tant qu'elle n'est pas mure.

TES IDENTIFIANTS DE TRAVAIL — recopie-les au signe pres, on ne les devine pas :
%(travaux_ids)s

DEUX SORTES DE PAS, ET ELLES NE SE CONFONDENT PAS :
· un pas de TRAVAIL porte `lieu` — c'est la que tu cherches quelque chose ;
· un pas de MARCHE porte `de` et `a`, sans `lieu` — c'est toi qui te
  deplaces, son `resultat` peut valoir « — » et personne ne t'en tiendra
  rigueur. Un homme qui marche n'a pas echoue.

UNE PENSEE A CHAQUE PAS DE TRAVAIL. C'est la regle du jour et elle est
ferme : tout pas qui porte un `lieu` doit donner AU MOINS une pensee dans
`travaux`, avec sa `source` qui renvoie a ce pas-la. Un pas de travail sans
pensee est un pas SEC — tu es alle quelque part chercher quelque chose et tu
n'en rapportes rien —, et il se compte contre toi. Si la source n'a
reellement rien donne, ce n'est pas un pas sec : c'est une pensee qui dit ce
que tu as cherche, ou tu l'as cherche, et pourquoi ce n'etait pas la. Un
« non » etabli est un resultat ; un silence n'en est pas un.

Une matinee entiere dans vingt-deux ans de relevés donne beaucoup : ecris
autant de pensees qu'elle en a donnees. La rarete porte sur les AFFAIRES
touchees, jamais sur ce que tu en apprends.

LES BORNES, et elles sont dures :
· DEUX affaires touchees au plus dans la journee. Pas trois.
· PAS DE SOURCE, PAS DE PENSEE. Une pensee sans quelque chose que tu as
  reellement touche aujourd'hui n'existe pas. C'est la seule regle que ce
  rapport fait respecter mecaniquement.
· Tu inventes largement la MATIERE — des gens, des prix, des rancunes, un
  nom qu'on te donne au banc. Tu n'inventes JAMAIS le VERDICT : ce que la
  source pouvait rendre, elle le rend, et « rien » est une reponse honnete
  qui se journalise comme les autres.
· Une `conclusion` est de TA main, en toutes lettres, et elle part dans
  ton cahier. Tant qu'elle n'est pas mure, elle reste `null`.
· Rien de ce que tu n'as pas appris ne t'est connu. Ton brief est la
  totalite de ce que tu sais.

%(consigne)s""" % {
        "brief": brief, "depot": depot, "qui": qui, "etagere": etagere,
        "parloir": PARLOIR_PY,
        "travaux_ids": travaux_ids(qui),
        "aujourdhui": json.dumps(
            dict(zip(("annee", "lune", "jour"), date_du_monde()))),
        "consigne": (u"CE QU'ON TE DEMANDE EN PLUS AUJOURD'HUI\n" + consigne
                     if consigne else u""),
    }


# ─────────────────────────────────────────────── ce que son plan montre
# LES TROUS DE SES PROPRES CAHIERS. Ce n'est pas une file de demandes qu'on lui
# assigne : c'est ce qu'un homme competent voit en ouvrant son cahier, et sur
# quoi il travaille sans qu'on le lui ordonne. Le manuel pose « pas de source,
# pas de pensee » — ceci EST une source, au meme titre qu'un registre depouille.
#
# LA BORNE EST DURE : le schema donne trois a cinq etapes a une tete du
# quartier, et le plus charge des hommes porte quatre-vingts trous. On lui en
# montre CINQ, les plus debloquants, et il prend ce qu'il peut porter. Ce qu'il
# laisse reste ; un homme qui laisse vingt trous ouverts trois lunes durant est
# une information sur lui, pas un defaut d'ici.
#
# RIEN NE S'ECRIT : ni ici, ni dans `intentions.json`. Il ecrit son etape de sa
# main, pendant sa session. On lui donne la matiere, jamais la decision.
#
# La derivation n'est pas refaite ici : elle vient d'`etat_du_plan.py`, qui la
# tient de `couverture.py` — un seul lecteur du graphe, une seule verite.
#
# ─── CE QUI RANGE LES CINQ, ET POURQUOI CA A CHANGE ──────────────────────────
#
# C'etait `force()`, un bareme ecrit a la main : 0 pour une rupture, 1 pour « le
# seul verrou qui l'en separe », 1+N pour « un verrou sur N », 20 pour une
# action, 60 pour le reste. Il classe la GRAVITE DU DEFAUT, et il ne connait du
# plan que le cahier qu'il regarde. Deux trous egalement « seuls verrous » y
# sont donc a egalite, meme quand l'un tient onze etats cibles et l'autre zero.
#
# On les range desormais par ce que la piece visee TIENT REELLEMENT —
# `criticite.py`, perte plus ce qu'on lui doit ailleurs. C'est la seule mesure
# qui traverse les trente-six cahiers, et c'est tout l'interet : les cinq lignes
# qu'un homme lit le matin sont les cinq qui ouvrent le plus de plan, et non les
# cinq dont le defaut se decrit le plus gravement.
#
# LES RUPTURES RESTENT EN TETE, ET CE N'EST PAS UNE POLITESSE ENVERS L'ANCIEN
# BAREME. Une chaine cassee au milieu ne remonte a aucun etat cible : sa piece
# vaut donc ZERO au contrefactuel, par construction. Ranger sur le seul score
# les enterrerait toutes — la mesure dirait « sans consequence » de ce qui est
# precisement le plus casse. Le guide est net : une action qui ne remonte a rien
# n'a pas de raison strategique demontree, elle se supprime ou se requalifie.
# On garde donc deux etages : les ruptures d'abord, le score ensuite.
#
# CE QUE CA NE FAIT PAS. Le routage ne bouge pas : un homme ne voit que les
# cahiers dont il est `tenu_par`. Le score sait pourtant dire quelle piece tombe
# sur QUEL office, ce qui permettrait de lui montrer ce qui est de sa charge
# dans les cahiers d'un autre — c'est le gain suivant, et il est plus gros que
# celui-ci. Il attend une decision : ouvrir la reserve d'un homme aux affaires
# qu'il ne tient pas, c'est changer ce qu'est un cahier.
TROUS_MONTRES = 5


def _scores():
    """{numero: perte + attendu}. Vide si le calcul echoue — on retombe alors
    sur `force()`, et l'homme part quand meme."""
    try:
        import criticite
        from couverture import charger as _ch
        _, pieces, _, _ = _ch()
        lignes, _base, _poids, _s, _m, dehors = criticite.calculer(pieces)
        crit = {n: c for c, pt, n, p in lignes}
        # `dehors` porte ce qui, dans un AUTRE cahier, attend cette piece : on
        # l'ajoute a sa perte, parce qu'un homme doit voir ce qu'il fait
        # attendre ailleurs autant que ce qu'il bloque chez lui.
        att = {n: sum(crit.get(m, 0) for m in ms) for n, ms in dehors.items() if ms}
        return {n: crit.get(n, 0) + att.get(n, 0) for n in set(crit) | set(att)}
    except Exception as e:
        sys.stderr.write(u"  (criticite indisponible, on retombe sur force() : %s)\n" % e)
        return {}


import re as _re
_NUM_ACTE = _re.compile(r"\d{3,6}")


def _rang(m, scores, force):
    """Les ruptures d'abord, puis le plus debloquant. Le numero de la piece se
    lit sur la clef de l'acte, qui l'y a deja mis (`clef/28017`, `office/220`)."""
    if not scores:
        return (force(m), m["acte"])
    rupture = 0 if m.get("nature") == "rupture" else 1
    ns = _NUM_ACTE.findall(m.get("acte") or u"")
    return (rupture, -(scores.get(ns[0], 0) if ns else 0), m["acte"])


def ses_trous(qui, combien=TROUS_MONTRES):
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import etat_du_plan as plan
        from couverture import charger, nu
        _, pieces, _, affaires = charger()
        siennes = [b for b in affaires if (b.get("tenu_par") or u"") == qui]
        tout = []
        for b in siennes:
            nom = nu(b["titre"])
            for m in plan.missions_de(nom, pieces):
                # CE QUI N'EST PAS DE SON RESSORT NE PART PAS AVEC LUI. « Deux
                # plans, ou un seul ? » est une décision de maison ; la poser à
                # un homme dépêché, c'est lui donner un travail qu'il ne peut
                # pas faire et occuper la première ligne de sa réserve avec.
                # Elle reste au conseil, dans `etat_du_plan.py --qui`.
                if m["acte"].startswith(u"registre/"):
                    continue
                tout.append((m, nom))
        scores = _scores()
        tout.sort(key=lambda x: _rang(x[0], scores, plan.force))
        if not tout:
            return u""
        lignes = [u"%d. %s\n   (%s)" % (i, plan.phrase(m), nom)
                  for i, (m, nom) in enumerate(tout[:combien], 1)]
        reste = (u"\n\nLe plan en montre %d autres sur tes affaires. Elles attendront."
                 % (len(tout) - combien)) if len(tout) > combien else u""
        return (u"\n## Ce que ton plan montre, ce matin\n\n"
                u"Tes cahiers portent des trous que personne ne t'a demandé de "
                u"combler — c'est ton affaire, et tu les vois comme on voit un "
                u"compte qui ne tombe pas juste. Les plus débloquants d'abord :\n\n"
                + u"\n".join(lignes) + reste
                + u"\n\nPrends ce que ta journée peut porter, et laisse le reste. "
                  u"Ce ne sont pas des ordres : ce sont les trous du plan. Ce que "
                  u"tu en fais s'écrit de ta main, dans tes pensées et ton "
                  u"cahier.\n")
    except Exception as e:
        # Une dépêche ne tombe JAMAIS pour un défaut de cette greffe : sans ses
        # trous, l'homme part quand même, et la raison se lit sur la sortie.
        sys.stderr.write(u"  (trous indisponibles pour %s : %s)\n" % (qui, e))
        return u""


# ─────────────────────── CE QUI TOMBE SUR LUI HORS DE SES CAHIERS
#
# LE ROUTAGE NE TENAIT QUE SUR `tenu_par`, ET C'ETAIT TROP ETROIT. Un homme
# repond de pas ecrits noir sur blanc sous SON office, dans le cahier d'un
# autre ; et il tient des moyens que d'autres engagent sans que son nom soit sur
# la ligne. Personne ne les lui cachait — aucun chemin ne les lui portait. Sur
# les vingt-six titulaires, la mesure disait Gerardys aveugle a 54 % et lord
# Corlys a 100 %.
#
# ─── CE QU'ON A ESSAYE D'ABORD, ET QUI DONNE ZERO ────────────────────────────
#
# Passer ces deux canaux par `missions_de`, comme le seau des cahiers. Mesure :
# 268 missions sur 44 cahiers, dont ZERO tombant sur l'office d'un autre. Un
# trou vise un verrou ou une clef, et NI L'UN NI L'AUTRE NE PORTE D'OFFICE —
# seules les actions en ont un. La ou une mission vise bien une action, cette
# action est du cahier qu'on regarde, donc de son propre tenant.
#
# « Sa charge ailleurs » n'est donc pas un ensemble de defauts : c'est un
# ensemble d'AFFECTATIONS. Un pas de l'office de Corlys pose dans le cahier de
# maitre Rulf et parfaitement redige ne produit aucun trou — et c'est pourtant
# exactement ce que Corlys doit savoir. L'unite est le PAS, non fait.
#
# ─── LA BORNE QUI TIENT TOUT ─────────────────────────────────────────────────
#
# A ET B SE FONT, C SE REPOND. C'est la reponse a la question que ce fichier
# laissait ouverte depuis le debut — « ouvrir la reserve d'un homme aux affaires
# qu'il ne tient pas, c'est changer ce qu'est un cahier ». On ne l'ouvre pas :
# on ajoute deux canaux d'une AUTRE NATURE. Un homme n'ecrit jamais dans le
# cahier d'un autre ; sur sa charge il va voir le tenant, sur ce qu'on lui tire
# il envoie un mot. Sans cette borne, deux mains ecrivent la meme ligne et l'on
# perd la seule chose que `tenu_par` garantissait.
#
# ─── DES PLACES FIXES, PARCE QUE LE VOLUME LE COMMANDE ───────────────────────
#
# Gerardys porte 133 pas qui tirent sur ses moyens. Fusionner les trois seaux
# dans un seul tri de cinq lignes ferait disparaitre SON cahier sous la charge
# des autres, ce qui est exactement l'inverse du but. Donc : 3 places au sien,
# un bloc de 3 lignes par canal, plafonne en dur. Le tunnel ne se contourne pas
# parce que la matiere est bonne.
TROUS_AILLEURS = 3

# « faite », « close », « ✅ faite », « FAITE le 3e j. de la 4e lune… » : la
# colonne d'etat est de la prose, et un homme y ecrit sa preuve a la suite du
# mot. On teste donc le DEBUT, jamais l'egalite.
_FAIT = _re.compile(u"^\\s*\\**\\s*(faites?|faits?|closes?|✅)", _re.I)


def _restants(paquet):
    """Les pas d'un seau qui restent à faire, le plus lourd en tête. Un pas fait
    ne tire plus rien : il n'a rien à faire dans une réserve."""
    return [(s, n, p) for s, n, p in paquet
            if p.get("genre") == "action" and not _FAIT.match(p.get("etat") or u"")]


def _par_cahier(paquet):
    """Groupé par cahier, les cahiers les plus lourds d'abord. On ne liste pas
    des pas : on nomme des VOLUMES, avec le compte et le poids dedans."""
    par = {}
    for s, n, p in paquet:
        d = par.setdefault(p.get("affaire") or u"— hors cahier —",
                           {"s": 0.0, "n": 0, "tete": None})
        d["s"] += s
        d["n"] += 1
        if d["tete"] is None:
            d["tete"] = p            # le paquet arrive déjà trié par poids
    return sorted(par.items(), key=lambda x: -x[1]["s"])


def sa_charge_ailleurs(qui, combien=TROUS_AILLEURS):
    """Les pas dont SON office répond, dans le cahier d'un autre. Ça se FAIT :
    il va voir le tenant du volume, et le pas est à lui."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import criticite
        _vu, sien, _tire = criticite.charge_de(qui)
        groupes = _par_cahier(_restants(sien))
        if not groupes:
            return u""
        lignes = [u"- **%s** — %d pas sous ton office. Le plus lourd : « %s »"
                  % (a, d["n"], (d["tete"] or {}).get("nom", u"?"))
                  for a, d in groupes[:combien]]
        reste = (u"\n\nIl y en a dans %d autre(s) cahier(s)." % (len(groupes) - combien)
                 if len(groupes) > combien else u"")
        return (u"\n## Ta charge, dans les cahiers des autres\n\n"
                u"Ces pas-là portent TON office. Le cahier est à un autre, le "
                u"travail est à toi — et personne ne te l'a dit jusqu'ici, "
                u"parce qu'aucun chemin ne te le portait.\n\n"
                + u"\n".join(lignes) + reste
                + u"\n\nTu vas voir le tenant du volume, et vous réglez. **Tu "
                  u"n'écris pas dans le cahier d'un autre** : ce qui s'y change "
                  u"se change par sa main, ou par la tienne s'il te la donne.\n")
    except Exception as e:
        sys.stderr.write(u"  (charge ailleurs indisponible pour %s : %s)\n" % (qui, e))
        return u""


def on_lattend(qui, combien=TROUS_AILLEURS):
    """Les pas qui engagent un moyen qu'il tient, sans que son nom soit sur la
    ligne. Ça se RÉPOND : ce n'est pas son travail, c'est quelqu'un qui attend."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import criticite
        _vu, _sien, tire = criticite.charge_de(qui)
        groupes = _par_cahier(_restants(tire))
        if not groupes:
            return u""
        # AGREGE PAR DEMANDEUR, JAMAIS LISTE. Les 133 pas de Gerardys en clair
        # sont un mur ; ce qui l'interesse est QUI attend et SUR QUOI.
        lignes = []
        for a, d in groupes[:combien]:
            ms = u" ".join((d["tete"] or {}).get("moyens") or []) or u"—"
            lignes.append(u"- **%s** — %d pas engagent ce que tu tiens (%s)"
                          % (a, d["n"], ms))
        reste = (u"\n\nEt %d autre(s) cahier(s) attendent de même."
                 % (len(groupes) - combien) if len(groupes) > combien else u"")
        return (u"\n## Ce qu'on attend de toi sans te l'avoir demandé\n\n"
                u"Ces cahiers-là engagent un moyen dont tu réponds. **Ce n'est "
                u"pas ton travail** : ce sont des gens bloqués par toi, qui ne "
                u"savent peut-être pas qu'ils t'attendent.\n\n"
                + u"\n".join(lignes) + reste
                + u"\n\nTu réponds — un mot, une heure, un refus net. Ce que tu "
                  u"ne peux pas donner, dis-le tout de suite plutôt que de le "
                  u"laisser attendre.\n")
    except Exception as e:
        sys.stderr.write(u"  (ce qu'on lui tire indisponible pour %s : %s)\n" % (qui, e))
        return u""


def mission(qui, brief, consigne, contexte=None):
    """Donne l'interface du jour ; l'identité et le contexte vivent au système."""
    depot = os.path.join(RACINE, "").replace("\\", "/")
    aujourdhui = dict(zip(("annee", "lune", "jour"), date_du_monde()))
    contexte = contexte or dossier_journee(qui, brief)
    ajout = (u"\n## L'élan particulier de ce jour\n\n" + consigne.strip() + u"\n"
             if consigne and consigne.strip() else u"")
    # Ses cahiers d'abord — c'est ce dont il répond. Puis ce qui tombe sur lui
    # de dehors, et qu'aucun chemin ne lui portait.
    ajout = ses_trous(qui) + sa_charge_ailleurs(qui) + on_lattend(qui) + ajout
    return u"""%(contexte)s

---

# Cette journée

Ton contexte vivant est déjà auprès de toi. Le dépôt %(depot)s matérialise le
monde que tes yeux et tes mains peuvent consulter. Ton étagère se trouve dans
`./livres/`, un fichier par volume. `Read`, `Grep` et `Glob` servent à toucher
ces sources ; `Grep` localise un passage dans les grands journaux avant sa
lecture.

Le parloir apporte une parole au milieu de ton travail. Lorsqu'une parole y
arrive, cette commande porte ta réponse dans la pièce :

    python %(parloir)s --dire --de %(qui)s --a mj "..."

Puis ta journée continue depuis ce nouvel échange.

## Ton rapport

Ta dernière réponse prend exactement la forme de cet objet JSON :

{
  "qui": "%(qui)s",
  "journal": [
    {
      "heure": "7h00",
      "duree": 20,
      "lieu": "lieu du geste",
      "quoi": "geste accompli, à la troisième personne",
      "resultat": "fait obtenu ou absence précisément établie"
    }
  ],
  "travaux": [
    {
      "travail_id": "identifiant exact donné plus bas",
      "dernier_travail": %(aujourdhui)s,
      "pensees": [
        {
          "date": %(aujourdhui)s,
          "source": "personne, lieu, objet ou registre touché",
          "texte": "ce que cette rencontre a appris"
        }
      ],
      "conclusion": null
    }
  ],
  "cahier2": [
    {
      "livre": "...",
      "table": "...",
      "ligne": "...",
      "colonne": "...",
      "valeur": "..."
    }
  ]
}

Une marche porte `de` et `a` à la place de `lieu`. Une découverte porte sa
source et sa date. Une conclusion mûre prend place dans l'affaire qu'elle
conclut. Les changements de registre prennent leurs coordonnées dans
`cahier2`.

Tes identifiants de travail :

%(travaux_ids)s
%(ajout)s""" % {
        "depot": depot,
        "parloir": PARLOIR_PY,
        "qui": qui,
        "aujourdhui": json.dumps(aujourdhui, ensure_ascii=False),
        "travaux_ids": travaux_ids(qui),
        "ajout": ajout,
        "contexte": contexte_message(qui, contexte).strip(),
    }


def poser_letagere(neutre, qui):
    """Materialise ses volumes en fichiers, un par volume, dans son dossier.

    C'EST LE SELECTEUR, ET IL EST PHYSIQUE. On aurait pu lui donner le
    lecteur en Bash et lui dire de s'en servir ; mais un outil qu'on autorise
    par motif de commande se contourne, et une consigne ne verrouille rien.
    La ou il travaille, il n'EXISTE que ce qu'il peut ouvrir. Le carnet de la
    reine n'est pas refuse : il n'est pas la.

    Effet de bord heureux : Grep sur ./livres/ lui donne la recherche
    plein-texte de son etagere, ce qui est exactement le geste d'un homme qui
    cherche dans ses registres — et qui evite les 547 000 jetons de
    etat/books.json, ou il s'est noye pendant huit minutes.
    """
    dossier = os.path.join(neutre, "livres")
    os.makedirs(dossier)
    n = 0
    for b in livre.etagere(qui):
        with io.open(os.path.join(dossier, "%s.txt" % b.get("id")), "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(livre.rendre(b, large=True))
        n += 1
    return n


def poser_le_parloir(neutre, qui):
    """Le hook qui lui met une oreille. Rend le chemin du fichier de reglages.

    UN HOOK N'EST PAS UNE HORLOGE : il bat apres chaque appel d'OUTIL, et
    seulement la. Un homme qui reflechit longtemps sans rien ouvrir n'entend
    rien pendant ce temps. En pratique cela suffit — sa journee entiere est
    faite de Read et de Grep —, mais c'est la limite du procede et il faut la
    connaitre avant de s'etonner d'un silence.

    Le matcher est `*` a dessein : on veut l'entendre au plus tot, pas
    seulement quand il lit. Le cout est nul tant que personne ne lui parle —
    `parloir.py --ecouter` n'ecrit RIEN sans message neuf, et un hook muet
    n'entre pas dans le contexte.
    """
    d = os.path.join(neutre, ".claude")
    os.makedirs(d, exist_ok=True)
    cible = os.path.join(d, "settings.json")
    py = sys.executable.replace("\\", "/")
    ecoute = "%s %s --ecouter --qui %s --hook" % (py, PARLOIR_PY, qui)
    with io.open(cible, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({
            "env": {"LE_CONSEIL_QUI": qui},
            "hooks": {
                "PostToolUse": [{"matcher": "*", "hooks": [
                    {"type": "command", "command": ecoute, "timeout": 15}]}],
            }}, ensure_ascii=False, indent=2))
    return cible


def appeler(qui, manuel, texte, sid, modele, minutes, parloir=True):
    """Tente --session-id ; retombe sur --resume si l'id a deja servi.

    LE MANUEL PASSE PAR --system-prompt-file. Windows plafonne une ligne a
    32 767 caracteres ; le fichier garde donc le prompt hors des arguments,
    mais sans le faire passer pour un CLAUDE.md decouvert automatiquement.
    L'homme recoit explicitement SON manuel systeme et n'herite plus de celui
    du MJ lorsque le depot est rouvert par --add-dir.

    Le repertoire est hors du depot : la decouverte remonte l'arborescence, un
    sous-dossier de le-conseil2 aurait retrouve le manuel du MJ par-dessus.
    """
    neutre = tempfile.mkdtemp(prefix="depeche-%s-" % qui)
    poser_letagere(neutre, qui)
    prompt_systeme = os.path.join(neutre, "system-prompt.md")
    with io.open(prompt_systeme, "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(manuel)
    # LE FIL PORTE LA SESSION, PAS L'HOMME. Deux dépêches du même acteur
    # peuvent tourner en même temps — la mienne et celle de la boucle
    # d'activation, le 9 août — et sous un seul nom elles se volaient les
    # messages. Le jeton vient de l'identifiant de session : deterministe,
    # donc retrouvable, et distinct par instance.
    identite = qui
    if parloir:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import parloir as _p
        identite = _p.ouvrir_instance(qui, sid.replace("-", "")[:8],
                                      os.path.basename(neutre), minutes)
    reglages = poser_le_parloir(neutre, identite) if parloir else None

    outils = list(OUTILS) + ([OUTIL_PARLOIR] if parloir else [])
    base = ["claude", "-p", "--output-format", "json",
            "--system-prompt-file", prompt_systeme,
            "--add-dir", RACINE, "--allowedTools"] + outils
    if reglages:
        # Le hook doit etre charge sans dependre de la reconnaissance du
        # repertoire neutre comme projet.
        base += ["--settings", reglages]
    base += ["--permission-mode", "acceptEdits"]
    if modele:
        base += ["--model", modele]

    dernier = u""
    try:
        for tentative in (["--session-id", sid], ["--resume", sid]):
            # La mission passe par stdin pour la meme raison que le manuel par
            # un fichier : 11 ko d'argument s'ajoutent a tout le reste.
            r = subprocess.run(base + tentative, cwd=neutre,
                               input=texte.encode("utf-8"),
                               capture_output=True, timeout=minutes * 60)
            out = r.stdout.decode("utf-8", "replace")
            err = r.stderr.decode("utf-8", "replace")
            if "already in use" in out + err:
                continue  # la session existe deja : on la reprend en place
            if not out.strip():
                raise RuntimeError((err or "aucune sortie").strip()[:400])
            return json.loads(out)
        raise RuntimeError("ni --session-id ni --resume n'ont abouti : %s"
                           % dernier[:200])
    finally:
        # SA SESSION EST FINIE : ELLE N'ECOUTE PLUS. Sans ce `finally`, une
        # depeche morte laisse son instance ouverte, et l'on continue de lui
        # parler dans un fil que plus personne ne lit — trois orphelines
        # tramaient deja apres les essais du 9 aout.
        if parloir and identite != qui:
            try:
                import parloir as _p
                _p.fermer_instance(identite)
            except Exception:
                pass


def extraire_json(texte):
    """Sa reponse DEVRAIT etre du JSON nu. On tolere un bloc de code ou une
    phrase autour : un homme qui a bien travaille ne doit pas voir sa journee
    jetee pour trois backticks."""
    t = (texte or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t).strip()
    try:
        return json.loads(t), None
    except Exception:
        pass
    d, f = t.find("{"), t.rfind("}")
    if d >= 0 and f > d:
        try:
            return json.loads(t[d:f + 1]), u"JSON degage d'un texte enrobe"
        except Exception as e:
            return None, u"illisible : %s" % e
    return None, u"aucun objet JSON dans la reponse"


def depecher(qui, consigne, modele, minutes, sec):
    date = date_du_monde()
    sid = identifiant_de_session(qui, date)
    brief = brief_de(qui)
    # LA GARDE PORTE SUR CE QUI EMPECHE SA JOURNEE, pas sur un mot du dossier.
    # Elle cherchait « CONVOCATION », que l'ancien brief tenait de
    # `convoquer.py` ; le brief neuf calcule les creux lui-meme et ne l'ecrit
    # plus — la garde etait donc toujours vraie et PLUS PERSONNE NE PARTAIT.
    # Les deux vrais motifs sont les deux sorties precoces de `brief_de`.
    empeche = None
    if not brief:
        empeche = u"aucun dossier"
    elif u"Aucune tete dans intentions.json" in brief:
        empeche = u"pas de tete dans intentions.json"
    elif u"AUCUN CREUX" in brief:
        empeche = u"aucun creux aujourd'hui — il travaille, il ne pense pas"
    if empeche:
        print(u"  %-18s ne part pas — %s" % (qui, empeche))
        return False
    contexte = dossier_journee(qui, brief)
    manuel = manuel_de(qui, mode="journee", contexte=contexte)
    texte = mission(qui, brief, consigne, contexte=contexte)

    if sec:
        print(u"═" * 72)
        print(u"%s   session %s" % (qui, sid))
        print(u"  prompt système : %d caractères (nouvelle version seule)"
              % len(manuel))
        print(u"  mission        : %d caracteres" % len(texte))
        print(u"  outils         : %s" % " ".join(OUTILS))
        print(u"  lance depuis   : un repertoire neutre, --add-dir %s" % RACINE)
        print(u"─" * 72)
        print(texte)
        return True

    debut = time.time()
    try:
        rep = appeler(qui, manuel, texte, sid, modele, minutes)
    except Exception as e:
        print(u"  %-18s ECHEC — %s" % (qui, e))
        return False

    rapport, note = extraire_json(rep.get("result", ""))
    u_ = rep.get("usage", {}) or {}
    jetons = (u_.get("input_tokens", 0) + u_.get("cache_read_input_tokens", 0)
              + u_.get("cache_creation_input_tokens", 0))

    if rapport is None:
        brut = os.path.join(DEPOT_RAPPORTS, "%s.brut.txt" % qui)
        _poser(brut, rep.get("result", ""))
        print(u"  %-18s RAPPORT ILLISIBLE (%s) — brut dans %s"
              % (qui, note, os.path.relpath(brut, RACINE)))
        return False

    rapport.setdefault("qui", qui)
    rapport["_depeche"] = {
        "session": sid, "date_jeu": "%d.%d.%d" % date,
        "jetons": jetons, "secondes": round(time.time() - debut),
    }
    cible = os.path.join(DEPOT_RAPPORTS, "%s.json" % qui)
    _poser(cible, json.dumps(rapport, ensure_ascii=False, indent=2))
    verse = verser_sur_le_champ(rapport, qui, date)

    p = sum(len(t.get("pensees", []) or []) for t in rapport.get("travaux", []) or [])
    print(u"  %-18s %2d pensee(s) [%d versee(s)] · %2d etape(s) · %s · %5d j. · %3ds → %s%s"
          % (qui, p, verse, len(rapport.get("journal", []) or []),
             u"conclusion" if rapport.get("conclusion") else u"—",
             jetons, rapport["_depeche"]["secondes"],
             os.path.relpath(cible, RACINE), u"  [%s]" % note if note else u""))
    return True


# ─────────────────────────────────────────────────────────────────────────────
# VERSER SUR LE CHAMP — il n'y a plus de guichet.
#
# Un homme rentrait, son rapport tombait dans `etat/rapports/`, et il y
# restait jusqu'a ce que quelqu'un lance `verser_travaux.py`. Trois fois dans la
# meme journee ses pensees sont restees a la porte : le depot ne portait pas
# l'identifiant de l'affaire, `verser` ne trouvait rien a rapprocher, et le
# travail d'une session entiere dormait dans un dossier que personne ne relit.
#
# Le rapport reste ecrit dans `etat/rapports/` — c'est la trace de sa journee et
# elle ne se jette pas — mais l'etat, lui, bouge tout de suite. Quand l'homme
# rentre d'une affaire qui n'existait pas encore, ON L'OUVRE avec le titre qu'il
# lui donne lui-meme : ce qu'il a travaille aujourd'hui est ce qu'il dit avoir
# travaille, et pas ce que le MJ avait prevu de lui faire travailler.
def verser_sur_le_champ(rapport, qui, date):
    """Ses pensees entrent dans `pensees.json`, a plat, datees et sourcees.

    Plus d'affaire a retrouver ni d'id a raccrocher : c'etait tout le travail
    de l'ancien guichet, et c'est ce qui le faisait rater. Une pensee porte son
    auteur, son jour, sa source et la salle ou il se tenait — et c'est assez
    pour que `dossier.py` la retrouve.

    PAS DE SOURCE, PAS DE PENSEE : une pensee sans source est REFUSEE ici, pas
    signalee plus tard. C'est la seule regle de l'ancien systeme qui meritait
    de survivre, et elle ne vaut que si elle mord a l'entree.
    """
    chemin = os.path.join(ETAT, "pensees.json")
    try:
        with io.open(chemin, encoding="utf-8") as fh:
            T = json.load(fh)
    except Exception:
        T = {"pensees": []}
    liste = T.setdefault("pensees", []) if isinstance(T, dict) else T
    quand = {"annee": date[0], "lune": date[1], "jour": date[2]}
    l = feuille_de_route().get(qui) or {}
    creux = l.get("questions_posees") or l.get("creux") or []
    salle_defaut = creux[0]["salle"] if creux else None

    vus = {((p.get("texte") or "")[:60], p.get("qui")) for p in liste
           if isinstance(p, dict)}
    pose, sans_source = 0, 0
    for bloc in rapport.get("travaux") or []:
        for x in bloc.get("pensees") or []:
            texte = (x.get("texte") or "").strip()
            if not texte:
                continue
            if not (x.get("source") or "").strip():
                sans_source += 1
                continue
            if (texte[:60], qui) in vus:
                continue
            liste.append({"qui": qui, "date": x.get("date") or dict(quand),
                          "source": x.get("source"), "texte": texte,
                          "salle": x.get("salle") or salle_defaut,
                          "affaire": bloc.get("affaire")})
            vus.add((texte[:60], qui))
            pose += 1
    if pose:
        _poser(chemin, json.dumps(T, ensure_ascii=False, indent=1) + "\n")

    # Une conclusion ne se calcule pas : elle est ecrite ou elle ne l'est pas.
    if rapport.get("conclusion"):
        pc = os.path.join(ETAT, "conclusions.json")
        try:
            with io.open(pc, encoding="utf-8") as fh:
                C = json.load(fh)
        except Exception:
            C = {"conclusions": []}
        C.setdefault("conclusions", []).append({
            "qui": qui, "date": dict(quand),
            "affaire": (rapport.get("travaux") or [{}])[0].get("affaire"),
            "livre": rapport.get("livre"),
            "texte": rapport["conclusion"]})
        _poser(pc, json.dumps(C, ensure_ascii=False, indent=1) + "\n")

    if sans_source:
        print(u"  (%d pensee(s) refusee(s) : pas de source, pas de pensee)"
              % sans_source)
    return pose


def _poser(chemin, contenu):
    d = os.path.dirname(chemin)
    if not os.path.isdir(d):
        os.makedirs(d)
    with io.open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenu)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qui", action="append", default=[],
                    help="un homme, repetable")
    ap.add_argument("--tous", action="store_true",
                    help="tous ceux qui doivent une journee")
    ap.add_argument("--salle", action="append", default=[],
                    help="toute une salle, PJ exclus — repetable")
    ap.add_argument("--salles", action="store_true",
                    help="dire quelles salles sont peuplees, et s'en tenir la")
    ap.add_argument("--autour", action="append", default=[],
                    help="tous ceux a portee de quelqu'un ou d'une salle")
    ap.add_argument("--rayon", type=float, default=10.0,
                    help="la portee en metres reels (defaut 10)")
    ap.add_argument("--front", type=int, default=4,
                    help="combien partent ensemble (1 = en file)")
    ap.add_argument("--mission", default="",
                    help="consigne du jour, en plus de son brief")
    ap.add_argument("--modele", default=None,
                    help="opus | sonnet | fable — defaut : celui de la session")
    ap.add_argument("--minutes", type=int, default=15,
                    help="delai avant abandon d'un homme")
    ap.add_argument("--sec", action="store_true",
                    help="montre tout, n'appelle rien, ne coute rien")
    a = ap.parse_args()

    if a.salles:
        pj = les_pj()
        print(u"LES SALLES PEUPLEES")
        for s, g in sorted(salles_peuplees().items(),
                           key=lambda x: (-len(x[1]), x[0] or u"")):
            if not s:
                continue
            hors = [q for q in g if q not in pj]
            print(u"  %-24s %2d a depecher%s" % (
                s, len(hors),
                u"   (%d PJ ecarte(s))" % (len(g) - len(hors))
                if len(g) - len(hors) else u""))
        return

    # On additionne les cibles, sans jamais retenir quelqu'un deux fois : la
    # meme personne peut etre nommee et se trouver dans une salle demandee.
    gens, vus = [], set()
    ecartes, aveugles = [], []
    autour = []
    for c in a.autour:
        d, e, av = dans_le_rayon(c, a.rayon)
        autour += d
        ecartes += e
        aveugles += av
        print(u"  a %g m de %s : %d homme(s)%s"
              % (a.rayon, c, len(d), u" + %d PJ" % len(e) if e else u""))
    if aveugles:
        # On ne tait jamais ce qu'on n'a pas pu voir.
        print(u"  sans adresse physique, donc hors du rayon quoi qu'il arrive :"
              u"\n    %s" % u", ".join(sorted(set(aveugles))))
    for source in (list(a.qui),
                   a_convoquer() if a.tous else [],
                   [q for s in a.salle for q in dans_la_salle(s)[0]],
                   autour):
        for q in source:
            if q not in vus:
                vus.add(q)
                gens.append(q)
    for s in a.salle:
        ecartes += dans_la_salle(s)[1]
    # Un PJ nomme a la main est ecarte comme les autres : la regle ne se
    # contourne pas en le demandant explicitement.
    pj = les_pj()
    nommes_pj = [q for q in gens if q in pj]
    gens = [q for q in gens if q not in pj]
    ecartes += nommes_pj
    if ecartes:
        print(u"  PJ ecarte(s), on ne les joue jamais : %s"
              % u", ".join(sorted(set(ecartes))))
    if not gens:
        raise SystemExit("Personne. --qui <homme>, --salle <salle>, --tous, "
                         "ou --salles pour voir.")

    date = date_du_monde()
    print(u"DEPECHER — le %d.%d.%d · %d homme(s)%s"
          % (date + (len(gens), u" · A SEC" if a.sec else u"")))
    ok = 0
    if a.sec or a.front <= 1 or len(gens) == 1:
        for qui in gens:
            if depecher(qui, a.mission, a.modele, a.minutes, a.sec):
                ok += 1
    else:
        # ILS PARTENT ENSEMBLE. Une journee d'homme se paie en minutes ; sept
        # en file en prendraient sept fois, et une salle entiere ne se
        # depecherait jamais. Ils n'ont rien a se dire, ne partagent aucun
        # fichier et n'ecrivent nulle part : chacun a son dossier, sa session
        # et son etagere, et le seul ecrivain reste ce processus-ci, a la fin.
        # `--front 1` rend la file a qui veut suivre un echec a la trace.
        import concurrent.futures as cf
        print(u"  (%d de front)" % min(a.front, len(gens)))
        with cf.ThreadPoolExecutor(max_workers=a.front) as pool:
            envoyes = {pool.submit(depecher, q, a.mission, a.modele,
                                   a.minutes, False): q for q in gens}
            for fini in cf.as_completed(envoyes):
                try:
                    if fini.result():
                        ok += 1
                except Exception as e:
                    print(u"  %-18s ECHEC — %s" % (envoyes[fini], e))
    if not a.sec:
        print(u"\n%d/%d rentres. Leurs pensees sont versees ; leurs changements "
              u"de registre sont des PROPOSITIONS." % (ok, len(gens)))
        print(u"  python scripts/verser_cahier.py             # a sec, montre tout")
        print(u"  python scripts/verser_cahier.py --vraiment  # ecrit dans books.json")


if __name__ == "__main__":
    main()
