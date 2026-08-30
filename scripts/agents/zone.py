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
SEL = uuid.uuid5(uuid.NAMESPACE_URL, "le-conseil/zones/v1")

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
        return (json.loads(out).get("result") or u"").strip()
    raise RuntimeError("ni --session-id ni --resume n'ont abouti pour %s" % mj)


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
    ap.add_argument("texte", nargs="*",
                    help="son mot (defaut : va lire l'inbox et le flux)")
    a = ap.parse_args()
    mot = u" ".join(a.texte) or MOT_DU_POST
    print(appeler_zone(a.qui, a.de, mot, u"POST", modele=a.modele))
