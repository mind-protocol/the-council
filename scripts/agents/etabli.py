# -*- coding: utf-8 -*-
"""ETABLI — la table de travail du MJ-travailleur (docs/habitant.md).

Extrait de zone.py le 31.8 (limite des 500 lignes) : zone.py garde les
SESSIONS de zone (sel, manuel, appeler_zone), ici vit tout ce qui fait la
journee-etabli d'un arbitre — les comptes reels de sa table, son mot, le
cooldown, le lancement detache, la veille de la boucle, la cadence des MJ
de joueurs et le ramassage de l'auto-lancement (verbe AGIR). zone.py
reexporte ces noms : les importeurs historiques ne bougent pas.
"""
import io
import json
import os
import subprocess
import sys
import time

from agents import chambre
from agents.depeche.brief import RACINE, date_du_monde
from agents.depeche.chambre_locale import rendre as rendre_chambre_locale


def _en_jours(d):
    """Une date du monde en jours pleins — la formule de
    agents/activation/horloges.py (12 lunes de 30 jours), reprise a
    l'identique : une seule arithmetique de calendrier dans le depot."""
    return ((int(d.get("annee", 0)) * 12
             + int(d.get("lune", 0)) - 1) * 30 + int(d.get("jour", 0)))


# La regle est celle d'en-souffrance.json, gravee dans son gabarit
# (agents/chambre.py) : « un fil qu'on n'a pas relance depuis trois jours
# se relance ou se ferme ».
ECHEANCE_JOURS = 3


def arbitre_du_staging(d):
    """L'arbitre d'une proposition du staging. LE DESTINATAIRE DECLARE PRIME
    (`pour` — 16 propositions de mj-portreal disent `pour: mj`, on ne les
    detourne pas vers leur auteur) ; a defaut, le premier mot du champ
    `par` (ou `de`) quand c'est un id de zone — les auteurs signent souvent
    avec une parenthese (« mj-peyredragon (proposition d'un FAIRE ...) »).
    Tout le reste — champs absents, auteur qui n'est pas une zone — revient
    au MJ principal : le tas non signe est le sien."""
    for champ in ("pour", "par", "de"):
        mots = str(d.get(champ) or u"").split()
        tete = mots[0] if mots else u""
        if tete == "mj" or (tete.startswith("mj-") and "-" not in tete[3:]):
            return tete
    return "mj"


def staging_par_arbitre():
    """{arbitre: nombre de propositions} du staging, ROUTE par l'auteur.

    Le staging etait au MJ principal seul (pis-aller du 31.8 : le compte non
    route rendait le tas ENTIER a chaque zone — (19,0,0) partout). La donnee
    de routage existait pourtant : le champ `par` des propositions. Chaque
    zone compte desormais LES SIENNES ; l'illisible et le non-signe vont au
    MJ principal."""
    staging = os.path.join(RACINE, "etat", "staging")
    comptes = {}
    try:
        noms = os.listdir(staging)
    except OSError:
        return comptes
    for n in noms:
        c = os.path.join(staging, n)
        if not os.path.isfile(c) or not n.endswith(".json"):
            continue
        try:
            d = json.load(io.open(c, encoding="utf-8"))
        except (IOError, OSError, ValueError):
            d = {}
        mj = arbitre_du_staging(d if isinstance(d, dict) else {})
        comptes[mj] = comptes.get(mj, 0) + 1
    return comptes


def comptes_d_etabli(mj):
    """Les trois comptes REELS de la table du MJ — (propositions, echus,
    billets). La seule arithmetique d'etabli : le mot (etabli_de) et le
    battement de la boucle (veiller_etablis) la partagent — jamais deux
    calculs qui divergent. Calcule ICI, par le lanceur, hors sandbox
    (habitant.md : le MJ est un travailleur ; son brief est son etabli).

    Les comptes sont REELS, jamais estimes : les fichiers du staging
    ROUTES a lui (etat/staging/, champ `par` — staging_par_arbitre), les
    fils echus de SON en-souffrance (j_attends + on_attend_de_moi dont la
    date — demande_le, ou depuis pour ce qu'on attend de lui — a plus de
    ECHEANCE_JOURS jours du monde), et ses billets non lus (chambre.non_lus).
    """
    propositions = staging_par_arbitre().get(mj, 0)
    souffrance = chambre.en_souffrance(mj)
    aujourd_hui = _en_jours(dict(zip(("annee", "lune", "jour"),
                                     date_du_monde())))
    echus = 0
    for fil in ((souffrance.get("j_attends") or [])
                + (souffrance.get("on_attend_de_moi") or [])):
        if not isinstance(fil, dict):
            continue
        quand = fil.get("demande_le") or fil.get("depuis")
        if not isinstance(quand, dict):
            continue
        if aujourd_hui - _en_jours(quand) > ECHEANCE_JOURS:
            echus += 1
    return propositions, echus, len(chambre.non_lus(mj))


# --- LES ACTIONS ASSIGNEES (demande du dev, 31.8) -------------------------
#
# Les affaires des arbitres (ex. chambres/mj/books/affaire-les-grands-buts)
# portent une table d'actions avec un etat (« a faire », « en cours »,
# « bloquee », « faite ») et un assigne (colonne 👤 Qui — deja un id de
# zone dans les affaires du MJ : `mj-accalmie`, pas un nom de lieu). Toute
# action NON CLOSE doit arriver dans le brief de SON assigne : c'est le mot
# d'etabli qui la porte. « En cours » au sens du dev = non close (a faire,
# en cours, bloquee) — au 31.8 toutes les actions des grands buts sont
# « a faire » ; un filtre strict rendrait un brief vide.

ETATS_OUVERTS_ACTION = ("a faire", "en cours", "bloqu")


def _texte_cellule(c):
    return str(c or u"").replace(u"*", u"").strip()


def _colonne(cols, *mots):
    for i, c in enumerate(cols):
        if any(m in c for m in mots):
            return i
    return None


def actions_ouvertes():
    """Toutes les actions non closes des books des chambres d'arbitres
    (`mj`, `mj-*`), rendues [{ref, action, etat, ou, assigne, affaire,
    proprietaire}]. Une table compte si elle porte A LA FOIS une colonne
    d'etat et une colonne Qui ; un Qui vide ou non-zone retombe sur le
    proprietaire du book (l'affaire est chez lui, elle reste chez lui)."""
    import glob
    import unicodedata
    chambres_racine = os.path.join(RACINE, "chambres")
    trouvees = []
    for chemin in sorted(glob.glob(os.path.join(chambres_racine, "mj*",
                                                "books", "*.json"))):
        proprietaire = os.path.basename(os.path.dirname(
            os.path.dirname(chemin)))
        try:
            book = json.load(io.open(chemin, encoding="utf-8"))
        except (IOError, OSError, ValueError):
            continue
        for table in (book.get("tables") or []):
            cols = [str(c) for c in (table.get("colonnes") or [])]
            i_etat = _colonne(cols, u"État", u"Etat")
            i_qui = _colonne(cols, u"Qui")
            if i_etat is None or i_qui is None:
                continue
            i_action = _colonne(cols, u"L'action", u"action") or 1
            i_ou = _colonne(cols, u"Où", u"Ou ")
            for ligne in (table.get("lignes") or []):
                cel = ligne.get("cellules") or []
                if len(cel) <= max(i_etat, i_qui, i_action):
                    continue
                etat = unicodedata.normalize(
                    "NFKD", _texte_cellule(cel[i_etat]).lower())
                etat = u"".join(c for c in etat
                                if not unicodedata.combining(c))
                if not any(etat.startswith(x) or x in etat
                           for x in ETATS_OUVERTS_ACTION):
                    continue
                qui = _texte_cellule(cel[i_qui])
                assigne = qui if (qui == "mj" or qui.startswith("mj-")) \
                    else proprietaire
                trouvees.append({
                    "ref": _texte_cellule(cel[0]),
                    "action": _texte_cellule(cel[i_action]),
                    "etat": _texte_cellule(cel[i_etat]),
                    "ou": (_texte_cellule(cel[i_ou])
                           if i_ou is not None and len(cel) > i_ou else u""),
                    "assigne": assigne,
                    "affaire": book.get("id") or os.path.basename(chemin),
                    "proprietaire": proprietaire,
                })
    return trouvees


def _section_actions(mj):
    """La section du mot d'etabli : les actions non closes assignees a CE
    mj, d'ou qu'elles viennent (les affaires des autres arbitres aussi)."""
    miennes = [a for a in actions_ouvertes() if a["assigne"] == mj]
    if not miennes:
        return u""
    lignes = [u"", u"⚔️ TES ACTIONS EN COURS — les affaires des arbitres te "
              u"les assignent, elles t'attendent :"]
    for a in miennes:
        chez = (u"" if a["proprietaire"] == mj
                else u", chez %s" % a["proprietaire"])
        ou = (u" — %s" % a["ou"]) if a["ou"] else u""
        lignes.append(u"  - [%s] (%s%s, %s) %s%s"
                      % (a["ref"], a["affaire"], chez, a["etat"],
                         a["action"], ou))
    return u"\n".join(lignes)


def etabli_de(mj):
    """LE MOT d'etabli du MJ : comptes, ordre, actions assignees, puis son
    bureau explicite.

    Dire seulement « tes affaires sont dans books/ » laissait l'arbitre sans
    les chemins ni les pas a reprendre. Meme contrat que la depeche d'un
    homme : chaque fichier de sa chambre, puis ref + nom de chaque action non
    close, affaire locale par affaire locale.
    """
    propositions, echus, billets = comptes_d_etabli(mj)
    mot = (u"ÉTABLI — ta table t'attend : %d propositions au staging, "
           u"%d fils en souffrance échus, %d billets non lus. "
           u"Traite dans l'ordre : mesures d'une passe ; mutations dans "
           u"l'ordre de tes \"Réalise\" ; ce qui porte \"Qui: <autre>\" part "
           u"en billet, tu ne l'exécutes pas ; les décisions remontent en "
           u"billet à dev. Écris tes items de flux dans "
           u"brouillons/flux-a-pousser.jsonl."
           % (propositions, echus, billets))
    section = _section_actions(mj)
    if section:
        mot += u"\n" + section
    return mot + u"\n\n" + rendre_chambre_locale(chambre.chemin(mj)).rstrip()


# Le cooldown de l'etabli : la boucle bat toutes les quelques secondes, une
# journee d'etabli dure des minutes — sans ce garde-fou, chaque battement
# empilerait un MJ sur le precedent. Horodate REELLE (mtime du marqueur),
# jamais la date du monde : c'est du spam de processus qu'on borne, pas du
# temps de jeu.
MARQUEUR_ETABLI = ".dernier-etabli"
COOLDOWN_ETABLI_MINUTES = 30


def _marqueur_etabli(mj):
    return os.path.join(chambre.chemin(mj), "brouillons", MARQUEUR_ETABLI)


def etabli_recent(mj, minutes=COOLDOWN_ETABLI_MINUTES):
    """Un etabli a-t-il ete lance il y a moins de `minutes` (reelles) ?"""
    try:
        return (time.time() - os.path.getmtime(_marqueur_etabli(mj))
                ) < minutes * 60
    except OSError:
        return False


def marquer_etabli(mj):
    """Pose l'horodate du lancement — TOUT chemin qui lance un etabli la
    pose (boucle, a-lancer, commande directe) : le cooldown vaut pour tous."""
    chambre.ouvrir(mj)
    with io.open(_marqueur_etabli(mj), "w", encoding="utf-8",
                 newline="\n") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S") + u"\n")


def lancer_etabli_detache(mj, de):
    """Spawn DETACHE de `reveiller.py --qui <mj> --de <de> --etabli` — le
    motif de serveur/routes/action.js (detached, stdio ignore, windowsHide)
    et de mission.appeler (les drapeaux du cast). Marque le cooldown au
    depart, pas au retour : c'est le lancement qu'on espace."""
    marquer_etabli(mj)
    drapeaux = {}
    if os.name == "nt":  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP — detache SANS console visible (spam de terminaux du 31.8)
        drapeaux["creationflags"] = 0x08000000 | 0x00000200
    else:
        drapeaux["start_new_session"] = True
    subprocess.Popen(
        [sys.executable, os.path.join(RACINE, "scripts", "reveiller.py"),
         "--qui", mj, "--de", de, "--etabli"],
        cwd=RACINE, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, **drapeaux)


# --- LA CADENCE DES MJ DE JOUEURS (decide le 31.8) -----------------------
#
# La veille par comptes est REACTIVE : un arbitre a table vide n'etait
# jamais reveille, donc son plan se decomptait sans jamais se developper
# (le point (3) du narrateur : « sans lui, les deux plans ne se developpent
# pas, ils se decomptent »). S'ajoute donc UN etabli par JOUR DE FICTION,
# meme a table vide — pour les MJ DE JOUEURS seulement : `mj`, plus les
# arbitres DECLARES par un siege (champ `arbitre` de etat/joueurs.json).
# Les autres mj-<ville> restent sur les reveils evenementiels (billets,
# verbes, POST).
#
# CE QU'UN SIEGE DECLARE DOIT ETRE CE QUE SON JOUEUR ADRESSE (le 5e). Le
# siege de nicolas-reynolds declare `mj-barralfond` parce que c'est ce que
# les DEUX routages lui donnent deja — serveur/routes/joueur.js:45 et
# zone.arbitre_de(). Un champ `arbitre` qui ne serait l'arbitre de personne
# reveillerait chaque jour une chambre a qui rien n'arrive : la cadence
# tournerait a vide et le plan du siege se decompterait quand meme.

MARQUEUR_JOUR = ".dernier-etabli-jour"


def arbitres_de_joueurs():
    """Les MJ de joueurs : `mj`, plus tout arbitre DECLARE par un siege
    (champ `arbitre` de son entree etat/joueurs.json). ON NE DEVINE PAS PAR
    LE NOM — premiere version corrigee par le dev le 31.8 : elle promouvait
    `mj-nicolas-reynolds` parce que la chambre existait, alors que l'arbitre
    de ce siege est `mj-barralfond` (verifie le 5e : joueur.js:45 et
    zone.arbitre_de() le rendent tous les deux ; `mj` est l'arbitre du siege
    principal, pas de celui-la). Meme doctrine que le champ `veille` de
    occupation.py : le lien siege->arbitre se declare et se relit, il ne se
    deduit pas d'une convention de nommage."""
    from etat.expose import tables
    sieges = tables.lire(os.path.join(RACINE, "etat", "joueurs.json"), [])
    if isinstance(sieges, dict):
        sieges = sieges.get("joueurs") or sieges.get("sieges") or []
    vus = ["mj"]
    for s in sieges or []:
        if not isinstance(s, dict) or s.get("regie"):
            continue
        arbitre = str(s.get("arbitre") or "").strip()
        if not arbitre:
            continue
        # L'INVARIANT DES IDS DE ZONE, RELU ICI PARCE QUE CE CHAMP EST ECRIT
        # A LA MAIN (le 5e) : un id de zone ne porte qu'un tiret, celui de
        # `mj-`. Declarer `mj-nicolas-reynolds` remettrait la panne du
        # premier etabli — zone.zone_de() renormalise en chemin, on
        # compterait la table d'une chambre pour en reveiller une autre. On
        # ECARTE EN LE DISANT : une declaration fausse ne doit pas arreter la
        # boucle, mais elle ne doit pas non plus passer sans bruit.
        if arbitre != "mj" and (not arbitre.startswith("mj-")
                                or "-" in arbitre[3:]):
            sys.stderr.write(
                u"[etabli] siege %s : arbitre declare mal forme (%s) — un id "
                u"de zone ne porte qu'un tiret. Siege ecarte de la cadence.\n"
                % (s.get("personnage_id"), arbitre))
            continue
        if arbitre not in vus and os.path.isdir(chambre.chemin(arbitre)):
            vus.append(arbitre)
    return vus


def _jour_du_monde():
    return "%d.%d.%d" % tuple(date_du_monde())


def _jour_marque(mj):
    try:
        with io.open(os.path.join(chambre.chemin(mj), "brouillons",
                                  MARQUEUR_JOUR), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def _marquer_jour(mj, jour):
    chambre.ouvrir(mj)
    with io.open(os.path.join(chambre.chemin(mj), "brouillons",
                              MARQUEUR_JOUR), "w", encoding="utf-8",
                 newline="\n") as f:
        f.write(jour + u"\n")


def veiller_etablis(de="boucle", minutes=COOLDOWN_ETABLI_MINUTES):
    """Le battement des CADENCES — deux portes d'entree (revu le 31.8, soir :
    le STAGING ne se scrute plus ici, son depot reveille l'arbitre a la porte
    meme — noyau/tables.py, « le depot est un evenement, pas un etat ») :

    - MJ DE JOUEURS : comptes OU un etabli par jour de fiction meme a table
      vide (la cadence historique).
    - TOUTE ZONE avec des ACTIONS ASSIGNEES ouvertes (actions_ouvertes) :
      un etabli par JOUR DE FICTION, pas par battement — une action reste
      ouverte des jours, la reveiller toutes les 30 min serait une tempete.

    Le cooldown reel vaut pour tous. Rend {mj: comptes}, None si aucun."""
    lances = {}
    jour = _jour_du_monde()
    joueurs = arbitres_de_joueurs()
    try:
        assignes = sorted({a["assigne"] for a in actions_ouvertes()})
    except Exception as e:  # gradue : un book illisible ne tue pas la veille
        assignes = []
        sys.stderr.write(u"(veille : actions_ouvertes en echec — %s)\n"
                         % str(e)[:120])
    tous = list(joueurs)
    for mj in assignes:
        if mj not in tous and os.path.isdir(chambre.chemin(mj)):
            tous.append(mj)
    for mj in tous:
        propositions, echus, billets = comptes_d_etabli(mj)
        table_vide = propositions + echus + billets <= 0
        if table_vide:
            # Table vide : seule la cadence du jour reveille — les MJ de
            # joueurs (toujours), les zones a actions assignees (idem).
            if mj not in joueurs and mj not in assignes:
                continue
            if _jour_marque(mj) == jour:
                continue
        if etabli_recent(mj, minutes):
            continue
        _marquer_jour(mj, jour)
        lancer_etabli_detache(mj, de)
        lances[mj] = {"propositions": propositions, "echus": echus,
                      "billets": billets, "cadence_du_jour": table_vide}
    return lances or None


def ramasser_a_lancer(mj):
    """LE MJ S'AUTO-LANCE PAR LE VERBE AGIR — meme motif que le spool de
    flux : il ECRIT son geste dans SA chambre (brouillons/a-lancer.jsonl,
    un objet JSON par ligne) et c'est ICI, hors session, au retour de
    l'audience, que le lanceur le ramasse. Une ligne = un lancement ; un
    etabli recent laisse la ligne en place (le cooldown vaut pour tous les
    chemins) ; un geste illisible ou inconnu reste et se dit sur stderr —
    rien ne se perd en silence."""
    fichier = os.path.join(chambre.chemin(mj), "brouillons",
                           "a-lancer.jsonl")
    if not os.path.exists(fichier):
        return
    restes = []
    with io.open(fichier, encoding="utf-8", errors="replace") as f:
        lignes = [l.strip() for l in f if l.strip()]
    for ligne in lignes:
        try:
            item = json.loads(ligne)
            if not (isinstance(item, dict) and item.get("etabli")):
                restes.append(ligne)
                sys.stderr.write(u"(a-lancer %s : geste inconnu — %s)\n"
                                 % (mj, ligne[:80]))
            elif etabli_recent(mj):
                restes.append(ligne)
                sys.stderr.write(u"(a-lancer %s : etabli recent, la ligne "
                                 u"attend)\n" % mj)
            else:
                lancer_etabli_detache(mj, mj)
                sys.stderr.write(u"(a-lancer %s : etabli lance)\n" % mj)
        except Exception as e:
            restes.append(ligne)
            sys.stderr.write(u"(a-lancer %s : %s)\n" % (mj, str(e)[:120]))
    with io.open(fichier, "w", encoding="utf-8", newline="\n") as f:
        f.write(u"\n".join(restes) + (u"\n" if restes else u""))
