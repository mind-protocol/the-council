# -*- coding: utf-8 -*-
"""ZONE — le reveil en CALL du MJ de zone (docs/habitant.md §3-§4, pas 4).

Un homme en journee a trois verbes vers son arbitre — TENTER, FAIRE,
DEMANDER — et chacun est un APPEL : on a besoin du verdict pour continuer,
le `-p` imbrique est le mecanisme d'attente, la reponse est un retour de
commande (habitant.md §4, call et cast).

LA SESSION DU MJ EST SA MEMOIRE. Son identifiant est deterministe et SANS
date (uuid5 sur son id) : il ne repart jamais de zero, il tient ses fils,
son registre d'audiences. Deux audiences peuvent s'entrelacer dans son
transcript — c'est son registre, pas un desordre (mesure du 30.8 : deux
--resume concurrents reussissent tous deux). Chaque reveil ne porte que
deux choses : QUI le reveille, et VOICI SON MOT.

LE MJ DU JOUEUR (`mj`) EST LA ZONE DU JOUEUR : `appeler_zone` marche pour
lui a l'identique — aucun code special, aucune table d'adresses. Un id est
une zone s'il est `mj` ou commence par `mj-` ; c'est la meme convention que
`parloir.est_un_mj`, et la seule.

Le vecu du MJ vit dans sa session continue ; son depot au fil (trace) est
differe — un transcript qui grandit se depouillerait en double a chaque
audience.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid

from agents import chambre
from agents.depeche.brief import RACINE, OUTILS, lire, date_du_monde

# Le sel de l'espace de noms des sessions de zone. Le changer rend tous les
# MJ amnesiques d'un coup : c'est le seul geste qui reparte de zero.
SEL = uuid.uuid5(uuid.NAMESPACE_URL, "le-conseil/zones/v2")

MJ_ZONE_MD = os.path.join(RACINE, "scripts", "agents", "prompts",
                          "mj-zone.md")
# La couche de la zone du joueur (le spectacle, la montre, l'arbitrage
# final) : servie EN PLUS de mj-zone.md quand la zone est `mj`.
MJ_SPECTACLE_MD = os.path.join(RACINE, "scripts", "agents", "prompts",
                               "mj-spectacle.md")
MANUEL_MJ_RACINE = os.path.join(RACINE, "CLAUDE.md")
FLUX = os.path.join(RACINE, "etat", "flux.jsonl")

# PLUS DE PLAFOND SUR UNE SESSION (31.8). « Trois minutes est un verdict, pas
# une journee » supposait qu'un arbitre repond vite ; la mesure dit autre
# chose. Le 31.8, hann-bourbe a fait son P.10, pose sa question a
# mj-portreal, et la session de l'arbitre a ete tuee a 180 secondes : le
# traceback est remonte dans la pensee de l'homme, sa journee entiere est
# partie, zero octet ecrit.
#
# CE PLAFOND NE PROTEGEAIT DE RIEN. Un processus rend la main quand il a fini
# — le couperet n'evite aucune fuite, il coupe seulement du travail en cours.
# `None` = pas d'expiration. Les deux noms restent pour qui veut borner
# explicitement un appel.
MINUTES = None
ETABLI_MINUTES = None


def est_une_zone(qui):
    """La convention de parloir.est_un_mj, reprise telle quelle : `mj` ou
    `mj-<ville>` est une zone, tout le reste est quelqu'un."""
    return qui == "mj" or (qui or u"").startswith("mj-")


def zone_de(ville):
    """L'id de zone d'une ville, et LE SEUL endroit qui le fabrique : la
    partie ville se normalise SANS TIRETS — un lieu_id `port-real` donne
    `mj-portreal`, jamais `mj-port-real` (`mj-` reste le seul tiret).

    UN ID DE ZONE NE PORTE QU'UN TIRET, ET C'EST L'INVARIANT (tranche le 5e
    de la 4e lune apres la panne du premier etabli). Un id deja prefixe est
    DEJA forme : il se rend tel quel, il ne se refabrique pas. Et s'il porte
    un second tiret, ce n'est pas une ville a normaliser — c'est un nom
    d'homme qu'on prend pour une zone : `mj-nicolas-reynolds` devenait
    silencieusement `mj-nicolasreynolds`, donc DEUX chambres pour un siege,
    l'etabli comptant la table de l'une et reveillant l'autre. On refuse en
    le disant plutot que de deviner : un id mal forme se retape, une chambre
    fantome ne se retrouve pas. (Le prix assume : `mj-port-real` n'est plus
    repare en silence, il est refuse avec la forme attendue.)"""
    if ville == "mj":
        return "mj"
    if (ville or u"").startswith("mj-"):
        if "-" in ville[3:]:
            raise SystemExit(
                u"id de zone mal forme : %r — un id de zone ne porte qu'un "
                u"tiret, celui de `mj-`. Ecris `mj-%s`, ou passe le lieu_id "
                u"nu (`port-real`) et laisse zone_de le former."
                % (ville, ville[3:].replace("-", "")))
        return ville
    return "mj-%s" % (ville or u"").replace("-", "")


def identifiant_de_session(mj):
    """Stable par MJ, SANS date : sa session est sa memoire."""
    return str(uuid.uuid5(SEL, mj))


def _sain(nom):
    if not re.match(r"^[a-z0-9][a-z0-9_.\-]*$", nom or ""):
        raise SystemExit(u"identifiant de zone illisible : %r" % nom)
    return nom


def _lieu_de(qui, personnages):
    p = next((x for x in personnages
              if isinstance(x, dict) and x.get("id") == qui), {})
    return p.get("lieu_id")


def arbitre_de(qui):
    """L'arbitre de zone d'un homme, d'apres SA VILLE (personnages.json,
    `lieu_id` — la meme cle que dossier_journee).

    Quand la zone est celle du joueur, le MJ du joueur absorbe le role : un
    seul arbitre par piece (habitant.md, les roles). La ville du joueur est
    le lieu_id des sieges occupes. A defaut de ville connue : `mj`.
    """
    from etat.expose import tables
    donnees = tables.lire(os.path.join(RACINE, "etat", "personnages.json"), [])
    if isinstance(donnees, dict):
        donnees = donnees.get("personnages") or []
    ville = _lieu_de(qui, donnees)
    if not ville:
        return "mj"
    joueurs = tables.lire(os.path.join(RACINE, "etat", "joueurs.json"), [])
    if isinstance(joueurs, dict):
        joueurs = joueurs.get("joueurs") or joueurs.get("sieges") or []
    villes_joueur = {_lieu_de(j.get("personnage_id") or j.get("id"), donnees)
                     for j in joueurs
                     if isinstance(j, dict) and j.get("occupe")}
    if ville in villes_joueur:
        return "mj"
    return zone_de(ville)


def identifiants_de_charge(mj):
    """Comptes runtime qui appartiennent a la meme capacite de zone.

    Le MJ principal absorbe toutes les zones physiques des sieges joueurs;
    les autres arbitres n'ont qu'un nom. Le tri rend le registre stable.
    """
    mj = zone_de(mj)
    if mj != "mj":
        return [mj]
    from etat.expose import tables
    donnees = tables.lire(os.path.join(RACINE, "etat", "personnages.json"), [])
    if isinstance(donnees, dict):
        donnees = donnees.get("personnages") or []
    joueurs = tables.lire(os.path.join(RACINE, "etat", "joueurs.json"), [])
    if isinstance(joueurs, dict):
        joueurs = joueurs.get("joueurs") or joueurs.get("sieges") or []
    comptes = {"mj"}
    for joueur in joueurs:
        if not isinstance(joueur, dict):
            continue
        # Le siege principal demeure l'identite historique de `mj`, meme
        # lorsque l'occupation mesuree est momentanement vacante. Sans cela,
        # fermer la page ferait disparaitre d'un coup toute la charge comptee
        # hier sous `mj-peyredragon`.
        if not joueur.get("occupe") and joueur.get("role") != "principal":
            continue
        lieu = _lieu_de(
            joueur.get("personnage_id") or joueur.get("id"), donnees)
        if lieu:
            comptes.add(zone_de(lieu))
    return sorted(comptes)


def _manuel(mj):
    """Constitution racine pour le MJ principal, puis zone, spectacle et
    cahier personnel.

    `CLAUDE.md` est le Manuel du MJ canonique : Regle Zero, parloir, salle,
    discipline du flux. Il n'etait auparavant jamais servi aux sessions de
    zone, parce que leur cwd est neutre. On ne le donne qu'a `mj` : l'injecter
    a `mj-sombreval` ou `mj-portreal` leur attribuerait la partie et le joueur
    du principal. Le cahier de chambre reste dernier, comme dans manuel_de.
    """
    zone = lire(MJ_ZONE_MD)
    if zone is None:
        raise SystemExit("scripts/agents/prompts/mj-zone.md manque a la zone.")
    blocs = []
    if mj == "mj":
        constitution = lire(MANUEL_MJ_RACINE)
        if constitution is None:
            raise SystemExit("CLAUDE.md manque au MJ principal.")
        blocs.append(constitution)
    blocs.append(zone)
    if mj == "mj":
        spectacle = lire(MJ_SPECTACLE_MD)
        if spectacle is None:
            raise SystemExit(
                "scripts/agents/prompts/mj-spectacle.md manque a la zone du "
                "joueur.")
        blocs.append(spectacle)
    cahier = lire(os.path.join(chambre.chemin(mj), "claude.md"))
    if cahier and cahier.strip():
        blocs.append(u"# Ta maniere, de ta main\n\n" + cahier.strip())
    return u"\n\n---\n\n".join(blocs) + u"\n"


# L'ETABLI VIT DANS agents/etabli.py (extrait le 31.8, limite des 500
# lignes) : comptes, mot, cooldown, veille, cadence des MJ de joueurs,
# ramassage a-lancer. Reexporte ici pour les importeurs historiques
# (reveiller.py, activation/cli.py appellent zone.etabli_de,
# zone.veiller_etablis...).
from agents.etabli import (  # noqa: F401
    ECHEANCE_JOURS, COOLDOWN_ETABLI_MINUTES, MARQUEUR_ETABLI,
    comptes_d_etabli, etabli_de, etabli_recent, marquer_etabli,
    lancer_etabli_detache, veiller_etablis,
    arbitres_de_joueurs, ramasser_a_lancer)

_ramasser_a_lancer = ramasser_a_lancer  # l'ancien nom interne


def reveiller_en_cast(mj, de, mot):
    """Le reveil CAST d'une zone, hors CLI — billet au canal + spawn detache
    de reveiller.py : le motif de `parloir --dire` vers un MJ, offert aux
    lanceurs (le greffe des rejets d'activation l'appelle). Le mot voyage
    avec le reveil, donc marque lu ; la suite arrive par les canaux.

    PAS DE LIMITE DE CADENCE ICI (tranche par le dev le 31.8, apres la
    tempete de la nuit) : un throttle n'aurait fait que ralentir le meme
    ping-pong. La cause etait dans le CADRE du reveil, qui commandait un
    billet-reponse a chaque reveil ; la regle qui tient est celle du peage
    de la parole, dans _message et mj-zone.md — une correspondance FINIT."""
    from agents.expose import billet
    canal = billet.deposer(de, mj, mot)
    chambre.marquer_lu(mj, de)
    drapeaux = {}
    if os.name == "nt":  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP — detache SANS console visible (spam de terminaux du 31.8)
        drapeaux["creationflags"] = 0x08000000 | 0x00000200
    else:
        drapeaux["start_new_session"] = True
    subprocess.Popen(
        [sys.executable, os.path.join(RACINE, "scripts", "reveiller.py"),
         "--qui", mj, "--de", de, mot],
        cwd=RACINE, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, **drapeaux)
    return canal, True


def _message(de, mot, verbe, modes=None):
    """Le reveil ne porte que deux choses : qui te reveille, et voici son
    mot — plus l'etiquette du moment (habitant.md §4 : la date est une
    etiquette, jamais un verrou)."""
    if verbe == u"JOUEUR":
        message = (u"[JOUEUR] %s vient de parler ou d'agir — an %d, %de "
                   u"lune, %de jour.\n%s\n"
                   u"Ce reveil est une adresse de travail, pas une voix "
                   u"d'habitant a arbitrer. Traite toutes les ACTIONS du brief "
                   u"dans l'ordre et reponds au joueur dans son flux — jamais "
                   u"par billet ou parloir.\n"
                   u"SORTIE : `python scripts/append_flux.py '<json item>' "
                   u"--pour %s`, des qu'une tranche est prete, puis de nouveau "
                   u"plus tard dans le meme tour. Un refus se corrige avant "
                   u"l'appel suivant. `suites` reste facultatif.\n"
                   % ((de,) + date_du_monde() + (mot.strip(), de)))
        if u"run" in (modes or []):
            message += (
                u"RUN ACTIF — GARDE DE SORTIE : tu tiens le personnage a sa "
                u"place. Une transition, une porte qui s'ouvre, un rapport "
                u"annonce ou un homme qui attend ne sont PAS une reponse. "
                u"Continue jusqu'au contenu substantiel et a ses consequences. "
                u"Si un PNJ doit parler, depeche-le ou interroge sa session : "
                u"n'invente pas sa parole et n'arrete pas le run en attendant. "
                u"Rends la bride quand le battement substantiel est accompli ; "
                u"un item `suites` peut l'expliciter, mais n'est jamais requis.\n")
        return message
    return (u"[%s] %s te reveille — an %d, %de lune, %de jour.\n"
            u"Son mot : « %s »\n"
            u"Tu es l'arbitre : ce mot est la voix d'un autre — reponds en "
            u"arbitre, jamais dans sa pensee.\n"
            u"SI son mot appelle une reponse, elle ne lui parvient que par "
            u"billet (python scripts/parloir.py --dire --de <toi> --a %s "
            u"\"...\") — ce que tu ecris ici sans billet reste dans ton "
            u"registre. MAIS UN BILLET PAIE SON PEAGE : il porte un fait "
            u"nouveau, une decision, ou une question dont tu attends la "
            u"reponse pour agir — sinon TU TE TAIS. Jamais d'accuse, de "
            u"merci, de complement qui redit, de reformulation de ce que "
            u"l'autre sait : une correspondance qui n'a plus rien a "
            u"s'apprendre EST FINIE, et le silence est sa fin normale "
            u"(mesure du 31.8 : deux arbitres polis se sont reveilles l'un "
            u"l'autre seize fois en six minutes).\n"
            % ((verbe, de) + date_du_monde() + (mot.strip(), de)))


def appeler_zone(ville, de, mot, verbe, modele=None, minutes=MINUTES):
    """Reveille le MJ de zone en CALL et rend son verdict (stdout).

    `ville` accepte l'id de zone (`mj`, `mj-peyredragon`) ou le nom nu de la
    ville (`peyredragon`). Premier reveil = --session-id avec le manuel ;
    reveils suivants = --resume, meme id — sa session est sa memoire. Le
    motif du lancement est celui de depeche/mission.appeler : --restricted
    --tools (l'isolation mesuree), --add-dir depot + sa chambre, manuel par
    fichier, mot par stdin.
    """
    mj = _sain(zone_de(ville))
    sid = identifiant_de_session(mj)
    sa_chambre = chambre.ouvrir(mj)
    manuel = _manuel(mj)
    actions_joueur = (_actions_en_attente(de)
                      if verbe == u"JOUEUR" else [])
    modes_joueur = _modes_actions(actions_joueur)
    if verbe == u"JOUEUR":
        from agents import portage
        mot = portage.brief_message_joueur(de)
    texte = _message(de, mot, verbe, modes=modes_joueur)

    # LE PAS-DE-TIR EST STABLE, ET C'EST UNE CONDITION DE LA MEMOIRE (mesure
    # du 30.8, reveils-jouets du pas 4) : un --session-id n'est unique que
    # PAR REPERTOIRE de lancement — deux mkdtemp donnent deux sessions au
    # meme id, et le second reveil repartait de zero en silence. Un dossier
    # fixe par MJ, hors du depot (la decouverte de CLAUDE.md remonte
    # l'arborescence), rend le conflit d'id — donc le --resume.
    neutre = os.path.join(tempfile.gettempdir(), "le-conseil-zones", mj)
    os.makedirs(neutre, exist_ok=True)
    from agents.expose import runtime as agent_runtime
    debut_flux = _position_flux()
    appels = []

    def appeler_le_mj(message):
        rep = agent_runtime.appeler(
            role=mj, manuel=manuel, message=message, session_id=sid,
            modele=modele,
            timeout=(minutes * 60) if minutes else None, cwd=neutre,
            add_dirs=[RACINE, sa_chambre], tools=OUTILS, reprendre=None,
            env={"LE_CONSEIL_QUI": str(mj), "LE_CONSEIL_MJ": str(mj)})
        appels.append(rep)
        return rep

    rep = appeler_le_mj(texte)
    rapport_attendu = (_actions_exigent_replique(actions_joueur)
                       or _a_interroge_un_pnj(rep))
    rapport_cache = (rapport_attendu
                     and u"replique" not in _types_flux_depuis(debut_flux))
    if rapport_cache:
        rep = appeler_le_mj(
            u"[CONTINUER LE RUN — SORTIE REFUSEE] Tu as rendu la main avant "
            u"d'avoir accompli le laisser-faire. Reprends exactement ou tu "
            u"t'es arrete. Une "
            u"porte qui s'ouvre ou un rapport annonce n'est qu'une amorce. "
            u"Obtiens la parole des PNJ par depeche/parloir si elle est "
            u"necessaire. Si tu as deja obtenu leur rapport, un resume en "
            u"`recit` le cache au joueur : pousse au moins une `replique` "
            u"avec `locuteur_id`, tiree de leurs mots reels, puis joue ses "
            u"consequences. `suites` n'est pas obligatoire. N'efface pas les "
            u"items deja ecrits ; complete-les.")
        rapport_attendu = rapport_attendu or _a_interroge_un_pnj(rep)
    types_tour = _types_flux_depuis(debut_flux)
    if rapport_attendu and u"replique" not in types_tour:
        raise RuntimeError(
            "rapport invisible : aucune replique de PNJ n'a ete poussee")
    sys.stderr.write(u"(zone : %s, %s, session %s)\n" % (
        mj, rep.get("provider") or "agent", sid[:8]))
    # L'inbox est une file, pas une memoire. Le modele ne porte plus la
    # suppression : le lanceur connait exactement les pieces presentes AVANT
    # le tour et ne retire que celles-la, seulement apres un appel reussi a la
    # porte et une vraie ecriture constatee. Un POST arrive pendant la session
    # reste donc pour le reveil suivant.
    if (actions_joueur and types_tour
            and any(_a_pousse_flux(r) for r in appels)):
        _retirer_actions(actions_joueur)
    _ramasser_a_lancer(mj)
    return (rep.get("result") or u"").strip()


def _position_flux():
    try:
        return os.path.getsize(FLUX)
    except OSError:
        return 0


def _items_flux_depuis(position):
    """Items reellement ajoutes depuis le reveil, sans intermediaire."""
    try:
        with open(FLUX, "rb") as f:
            f.seek(position)
            brut = f.read().decode("utf-8", "replace")
    except OSError:
        return []
    items = []
    for ligne in brut.splitlines():
        try:
            item = json.loads(ligne)
            if isinstance(item, dict):
                items.append(item)
        except ValueError:
            continue
    return items


def _types_flux_depuis(position):
    return [item.get("type") for item in _items_flux_depuis(position)
            if item.get("type")]


def _a_pousse_flux(rep):
    return any("append_flux.py" in str(geste)
               for geste in (rep.get("gestes") or []))


def _actions_en_attente(personnage):
    dossier = os.path.join(RACINE, "etat", "inbox", _sain(personnage))
    if not os.path.isdir(dossier):
        return []
    return [os.path.join(dossier, nom) for nom in sorted(os.listdir(dossier))
            if nom.startswith("action-") and nom.endswith(".json")
            and os.path.isfile(os.path.join(dossier, nom))]


def _modes_actions(chemins):
    modes = []
    for chemin in chemins:
        try:
            with io.open(chemin, encoding="utf-8") as f:
                mode = (json.load(f) or {}).get("mode")
            if mode and mode not in modes:
                modes.append(str(mode))
        except Exception:
            continue
    return modes


def _actions_exigent_replique(chemins):
    motifs = (u"rapport", u"parole", u"replique", u"réplique")
    for chemin in chemins:
        try:
            with io.open(chemin, encoding="utf-8") as f:
                action = json.load(f) or {}
            texte = str(action.get("texte") or "").casefold()
            if action.get("mode") == "run" and any(m in texte for m in motifs):
                return True
        except Exception:
            continue
    return False


def _a_interroge_un_pnj(rep):
    gestes = u"\n".join(str(g) for g in (rep.get("gestes") or []))
    return "parloir.py" in gestes or "depecher.py" in gestes


def _retirer_actions(chemins):
    for chemin in chemins:
        try:
            os.remove(chemin)
        except FileNotFoundError:
            pass
def main():
    """L'entree de scripts/reveiller.py, la facade (habitant.md pas 5 : le
    guetteur meurt). Le serveur la spawn DETACHEE sur le POST du joueur — le
    MJ du joueur est un habitant comme les autres, son reveil est un appel.
    La supervision est un siege : `claude --resume <session mj>` quand le
    dev veut piloter, rendu en sortant."""
    import argparse
    ap = argparse.ArgumentParser(description=main.__doc__)
    ap.add_argument("--qui", default="mj",
                    help="la zone a reveiller (defaut : le MJ du joueur)")
    ap.add_argument("--de", required=True,
                    help="qui reveille — le personnage du siege qui a poste")
    ap.add_argument("--modele", default=None)
    # PLUS DE PLAFOND, ET LES DIX MINUTES ETAIENT DEJA UNE RUSTINE. Le 31.8
    # au matin j'avais releve ce reveil de 180 s a 600 parce qu'un MJ coupe
    # en plein tour ne rend rien au joueur, sans laisser de trace (le serveur
    # le spawn DETACHE et ne lit pas sa sortie). La bonne question n'etait
    # pas « a combien » : c'etait « de quoi ce plafond protege-t-il ». De
    # rien — un processus rend la main quand il a fini. Ce qu'il faisait, en
    # revanche, se mesure : une journee d'homme perdue le meme jour.
    # Defaut : pas d'expiration. Le drapeau reste, pour un banc qui veut
    # borner explicitement.
    ap.add_argument("--timeout", type=float, default=None, metavar="SECONDES",
                    help="borner l'appel a N secondes ; par defaut la session"
                         " n'expire pas")
    ap.add_argument("--etabli", action="store_true",
                    help="la journee-etabli : le mot est SON etabli (staging, "
                         "fils echus, billets), calcule ici, hors sandbox")
    ap.add_argument("texte", nargs="*",
                    help="son mot (defaut : va lire l'inbox et le flux)")
    a = ap.parse_args()
    if a.timeout is not None and a.timeout <= 0:
        ap.error("le timeout se compte en secondes et doit etre positif")
    minutes = (a.timeout / 60.0) if a.timeout else None
    if a.etabli:
        mj = _sain(zone_de(a.qui))
        marquer_etabli(mj)  # le cooldown vaut pour tous les chemins
        print(appeler_zone(mj, a.de, etabli_de(mj), u"ETABLI",
                           modele=a.modele, minutes=minutes))
    else:
        mot = u" ".join(a.texte)
        verbe = u"POST"
        if not mot:
            # D.34 — appeler_zone construit le brief court du message joueur :
            # inbox exacte, fin du fil avec numeros de lignes, trois adresses
            # de registres au plus.
            verbe = u"JOUEUR"
        print(appeler_zone(a.qui, a.de, mot, verbe, modele=a.modele,
                           minutes=minutes))
