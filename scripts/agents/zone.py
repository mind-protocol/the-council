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
import time
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

# LE FILET DES CYCLES (habitant.md §4) : les aretes sync sont courtes et
# dirigees ; le timeout du -p suffit. Trois minutes est un verdict, pas
# une journee.
MINUTES = 3

# L'ETABLI, lui, EST une journee (habitant.md : le MJ est un travailleur) :
# trancher, graver, relancer ne tient pas dans le filet d'un verdict.
ETABLI_MINUTES = 8


def est_une_zone(qui):
    """La convention de parloir.est_un_mj, reprise telle quelle : `mj` ou
    `mj-<ville>` est une zone, tout le reste est quelqu'un."""
    return qui == "mj" or (qui or u"").startswith("mj-")


def zone_de(ville):
    """L'id de zone d'une ville, et LE SEUL endroit qui le fabrique : la
    partie ville se normalise SANS TIRETS — un lieu_id `port-real` donne
    `mj-portreal`, jamais `mj-port-real` (`mj-` reste le seul tiret).
    Accepte l'id deja prefixe (`mj-...`) et le renormalise a l'identique."""
    if ville == "mj":
        return "mj"
    nom = ville[3:] if (ville or u"").startswith("mj-") else (ville or u"")
    return "mj-%s" % nom.replace("-", "")


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


def _manuel(mj):
    """mj-zone.md, puis mj-spectacle.md si la zone est celle du joueur (le
    meme role plus trois charges — habitant.md, les roles), puis le claude.md
    de SA chambre — sa maniere, de sa main, en dernier : la voix la plus
    proche de lui a le dernier mot (meme coupe que manuel_de)."""
    manuel = lire(MJ_ZONE_MD)
    if manuel is None:
        raise SystemExit("scripts/agents/prompts/mj-zone.md manque a la zone.")
    if mj == "mj":
        spectacle = lire(MJ_SPECTACLE_MD)
        if spectacle is None:
            raise SystemExit(
                "scripts/agents/prompts/mj-spectacle.md manque a la zone du "
                "joueur.")
        manuel += u"\n\n---\n\n" + spectacle
    cahier = lire(os.path.join(chambre.chemin(mj), "claude.md"))
    if cahier and cahier.strip():
        manuel += (u"\n\n---\n\n# Ta maniere, de ta main\n\n"
                   + cahier.strip() + u"\n")
    return manuel


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
    if os.name == "nt":  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        drapeaux["creationflags"] = 0x00000008 | 0x00000200
    else:
        drapeaux["start_new_session"] = True
    subprocess.Popen(
        [sys.executable, os.path.join(RACINE, "scripts", "reveiller.py"),
         "--qui", mj, "--de", de, "--etabli"],
        cwd=RACINE, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, **drapeaux)


def veiller_etabli(mj="mj", de="boucle", minutes=COOLDOWN_ETABLI_MINUTES):
    """LE BATTEMENT : la boucle d'activation appelle ceci a chaque passage
    (agents/activation/cli.py). Si la table du MJ porte quelque chose —
    memes comptes que le mot d'etabli — et qu'aucun etabli n'est recent,
    son etabli part detache. Rend les comptes si lance, None sinon.
    Gradue, jamais bloquant : l'appelant enveloppe dans son try/except."""
    propositions, echus, billets = comptes_d_etabli(mj)
    if propositions + echus + billets <= 0:
        return None
    if etabli_recent(mj, minutes):
        return None
    lancer_etabli_detache(mj, de)
    return {"propositions": propositions, "echus": echus,
            "billets": billets}


def _ramasser_a_lancer(mj):
    """LE MJ S'AUTO-LANCE PAR LE VERBE AGIR — meme motif que le spool de
    flux : son sandbox bloque python (mesure du 31.8), donc il ECRIT son
    geste dans SA chambre (brouillons/a-lancer.jsonl, un objet JSON par
    ligne) et c'est ICI, hors sandbox, au retour de l'audience, que le
    lanceur le ramasse. Une ligne = un lancement ; un etabli recent laisse
    la ligne en place (le cooldown vaut pour tous les chemins) ; un geste
    illisible ou inconnu reste et se dit sur stderr — rien ne se perd en
    silence."""
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


def _message(de, mot, verbe):
    """Le reveil ne porte que deux choses : qui te reveille, et voici son
    mot — plus l'etiquette du moment (habitant.md §4 : la date est une
    etiquette, jamais un verrou)."""
    return (u"[%s] %s te reveille — an %d, %de lune, %de jour.\n"
            u"Son mot : « %s »\n"
            u"Tu es l'arbitre : ce mot est la voix d'un autre — reponds en "
            u"arbitre, jamais dans sa pensee.\n"
            % ((verbe, de) + date_du_monde() + (mot.strip(),)))


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
    texte = _message(de, mot, verbe)

    # LE PAS-DE-TIR EST STABLE, ET C'EST UNE CONDITION DE LA MEMOIRE (mesure
    # du 30.8, reveils-jouets du pas 4) : un --session-id n'est unique que
    # PAR REPERTOIRE de lancement — deux mkdtemp donnent deux sessions au
    # meme id, et le second reveil repartait de zero en silence. Un dossier
    # fixe par MJ, hors du depot (la decouverte de CLAUDE.md remonte
    # l'arborescence), rend le conflit d'id — donc le --resume.
    neutre = os.path.join(tempfile.gettempdir(), "le-conseil-zones", mj)
    os.makedirs(neutre, exist_ok=True)
    prompt_systeme = os.path.join(neutre, "system-prompt.md")
    with io.open(prompt_systeme, "w", encoding="utf-8", newline="\n") as f:
        f.write(manuel)

    base = ["claude", "-p",
            "--system-prompt-file", prompt_systeme,
            "--add-dir", RACINE, "--add-dir", sa_chambre,
            "--restricted", "--tools", ",".join(OUTILS),
            "--output-format", "json",
            "--permission-mode", "acceptEdits"]
    if modele:
        base += ["--model", modele]

    for tentative in (["--session-id", sid], ["--resume", sid]):
        r = subprocess.run(base + tentative, cwd=neutre,
                           input=texte.encode("utf-8"),
                           capture_output=True, timeout=minutes * 60)
        out = r.stdout.decode("utf-8", "replace")
        err = r.stderr.decode("utf-8", "replace")
        if "already in use" in out + err:
            continue  # sa session existe deja : on la reprend — sa memoire
        if not out.strip():
            raise RuntimeError((err or "aucune sortie du MJ de zone")
                               .strip()[:400])
        sys.stderr.write(u"(zone : %s, session %s %s)\n"
                         % (mj, sid[:8],
                            u"nouvelle" if tentative[0] == "--session-id"
                            else u"reprise"))
        _pousser_le_spool(mj)
        _ramasser_a_lancer(mj)
        return (json.loads(out).get("result") or u"").strip()
    raise RuntimeError("ni --session-id ni --resume n'ont abouti pour %s" % mj)


def _pousser_le_spool(mj):
    """LE LANCEUR POUSSE AU FLUX — meme motif que le vecu (trace.deposer).

    Mesure du 31.8 : le sandbox du reveil -p a bloque `python append_flux.py`
    au MJ — sa reponse, ecrite et prete, est restee prisonniere d'un fichier.
    Le MJ ecrit donc ses items dans SA chambre (brouillons/flux-a-pousser.jsonl,
    un item JSON par ligne, l'audience en clef `pour`) et c'est ICI, hors
    sandbox, que la porte se passe. Le spool est vide apres la poussee ; un
    item illisible reste en place et se dit sur stderr — rien ne se perd en
    silence."""
    spool = os.path.join(chambre.chemin(mj), "brouillons",
                         "flux-a-pousser.jsonl")
    if not os.path.exists(spool):
        return
    restes = []
    with io.open(spool, encoding="utf-8", errors="replace") as f:
        lignes = [l.strip() for l in f if l.strip()]
    for ligne in lignes:
        try:
            item = json.loads(ligne)
            audience = item.get("pour") or "tous"
            if isinstance(audience, list):
                audience = ",".join(audience)
            r = subprocess.run(
                [sys.executable, os.path.join(RACINE, "scripts",
                                              "append_flux.py"),
                 ligne, "--pour", str(audience)],
                cwd=RACINE, capture_output=True, timeout=60)
            if r.returncode != 0:
                restes.append(ligne)
                sys.stderr.write(u"(spool %s : refus — %s)\n" % (
                    mj, r.stdout.decode("utf-8", "replace").strip()[:160]))
        except Exception as e:
            restes.append(ligne)
            sys.stderr.write(u"(spool %s : %s)\n" % (mj, str(e)[:120]))
    with io.open(spool, "w", encoding="utf-8", newline="\n") as f:
        f.write(u"\n".join(restes) + (u"\n" if restes else u""))


MOT_DU_POST = (u"je viens d'agir — mon action t'attend dans l'inbox, "
               u"et ma parole au flux.")


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
    ap.add_argument("--etabli", action="store_true",
                    help="la journee-etabli : le mot est SON etabli (staging, "
                         "fils echus, billets), calcule ici, hors sandbox")
    ap.add_argument("texte", nargs="*",
                    help="son mot (defaut : va lire l'inbox et le flux)")
    a = ap.parse_args()
    if a.etabli:
        mj = _sain(zone_de(a.qui))
        marquer_etabli(mj)  # le cooldown vaut pour tous les chemins
        print(appeler_zone(mj, a.de, etabli_de(mj), u"ETABLI",
                           modele=a.modele, minutes=ETABLI_MINUTES))
    else:
        mot = u" ".join(a.texte) or MOT_DU_POST
        print(appeler_zone(a.qui, a.de, mot, u"POST", modele=a.modele))
