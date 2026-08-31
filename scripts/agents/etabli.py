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


def comptes_d_etabli(mj):
    """Les trois comptes REELS de la table du MJ — (propositions, echus,
    billets). La seule arithmetique d'etabli : le mot (etabli_de) et le
    battement de la boucle (veiller_etabli) la partagent — jamais deux
    calculs qui divergent. Calcule ICI, par le lanceur, hors sandbox
    (habitant.md : le MJ est un travailleur ; son brief est son etabli).

    Les comptes sont REELS, jamais estimes : les fichiers du staging
    (etat/staging/, les propositions a depouiller), les fils echus de SON
    en-souffrance (j_attends + on_attend_de_moi dont la date — demande_le,
    ou depuis pour ce qu'on attend de lui — a plus de ECHEANCE_JOURS jours
    du monde), et ses billets non lus (chambre.non_lus).
    """
    # LE STAGING EST AU MJ PRINCIPAL SEUL (mesure du 31.8 : les comptes
    # rendaient (19,0,0) pour TOUTES les zones — chaque arbitre se serait
    # reveille pour un tas qui ne le concerne pas). Les autres arbitres ne
    # comptent que leur propre table : fils echus et billets.
    propositions = 0
    if mj == "mj":
        staging = os.path.join(RACINE, "etat", "staging")
        try:
            propositions = sum(1 for n in os.listdir(staging)
                               if os.path.isfile(os.path.join(staging, n)))
        except OSError:
            propositions = 0
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


def etabli_de(mj):
    """LE MOT d'etabli du MJ. Le mot ne dit que les nombres et l'ordre de
    traitement ; ses affaires, il les a deja dans sa chambre (books/)."""
    propositions, echus, billets = comptes_d_etabli(mj)
    return (u"ÉTABLI — ta table t'attend : %d propositions au staging, "
            u"%d fils en souffrance échus, %d billets non lus. "
            u"Tes affaires sont dans ta chambre (books/). Traite dans "
            u"l'ordre : mesures d'une passe ; mutations dans l'ordre de tes "
            u"\"Réalise\" ; ce qui porte \"Qui: <autre>\" part en billet, tu "
            u"ne l'exécutes pas ; les décisions remontent en billet à dev. "
            u"Écris tes items de flux dans brouillons/flux-a-pousser.jsonl."
            % (propositions, echus, billets))


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


def veiller_etabli(mj="mj", de="boucle", minutes=COOLDOWN_ETABLI_MINUTES):
    """LE BATTEMENT historique, un seul MJ : si sa table porte quelque chose
    — memes comptes que son mot d'etabli — et qu'aucun etabli n'est recent,
    son etabli part detache. Rend les comptes si lance, None sinon.
    Gradue, jamais bloquant : l'appelant enveloppe dans son try/except.
    La boucle appelle desormais veiller_etablis (tous les MJ de joueurs)."""
    propositions, echus, billets = comptes_d_etabli(mj)
    if propositions + echus + billets <= 0:
        return None
    if etabli_recent(mj, minutes):
        return None
    lancer_etabli_detache(mj, de)
    return {"propositions": propositions, "echus": echus,
            "billets": billets}


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
    """Le battement etendu : pour chaque MJ de joueur, un etabli part si sa
    table porte quelque chose (les comptes) OU si ce jour de fiction n'a pas
    encore eu son etabli (la cadence). Le cooldown reel vaut dans les deux
    cas. Rend {mj: comptes} des lancements, None si aucun."""
    lances = {}
    jour = _jour_du_monde()
    for mj in arbitres_de_joueurs():
        propositions, echus, billets = comptes_d_etabli(mj)
        table_vide = propositions + echus + billets <= 0
        if table_vide and _jour_marque(mj) == jour:
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
