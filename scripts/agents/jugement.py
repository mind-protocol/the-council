# -*- coding: utf-8 -*-
# JUGEMENT — la descente lot 2 de scripts/juger.py, qui reste la facade
# gelee (docs/organisation.md §7 : juger.py -> agents/jugement.py) : le
# hook Stop de .claude/settings.json tape ce chemin-la.
# -*- coding: utf-8 -*-
# JUGER — hook Stop du NARRATEUR, jamais de l'acteur.
#
# Il relit le rapport que le narrateur vient d'etablir sur la tentative. Si
# l'acteur est sous le seuil, il bloque la fin du narrateur et lui demande de
# rendre un objet `relance_acteur`. La boucle Python transmet ensuite cette
# relance dans le fil propre de l'acteur.
#
# ─────────────────────────────────────────────────────────────────────────────
# LE JUGE N'EST PAS LUI. Un homme qui se note lui-meme a la fin de sa journee
# se donne 8. On appelle donc un juge separe, par la porte globale, et on lui donne
# ce que l'homme a REELLEMENT OUVERT — ses Read, ses Grep, tires du
# transcript — et pas seulement ce qu'il raconte avoir fait. C'est la que se
# voit la difference entre un homme qui est alle au banc et un homme qui a
# raisonne depuis sa table.
#
# ON NE RENVOIE JAMAIS UNE NOTE. Une note ne se corrige pas ; une liste de
# « non » si. La relance porte les questions auxquelles il a repondu non, en
# toutes lettres, et rien d'autre — pas de chiffre, pas de reproche.
#
# DEUX RELANCES AU PLUS. Au-dela on brule sa journee en boucle pour gagner un
# point. Le compte se tient par session dans etat/juges/, et
# `stop_hook_active` sert de second filet : sans plafond, un hook Stop qui
# bloque est une boucle infinie, et c'est la faute classique de ce mecanisme.
#
# Usage (le hook le fait tout seul ; ces formes servent a l'essayer) :
#     python scripts/juger.py --sec --transcript <fichier.jsonl>
#     echo '<charge du hook>' | python scripts/juger.py
import argparse
import io
import json
import os
import re
import sys
import tempfile
import uuid

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Un etage de plus qu'a la racine : scripts/agents/ (voir scripts/CLAUDE.md).
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPTES = os.path.join(RACINE, "etat", "juges")

SEUIL = int(os.environ.get("LE_CONSEIL_JUGE_SEUIL", "7"))
RELANCES_MAX = int(os.environ.get("LE_CONSEIL_JUGE_RELANCES", "2"))
MODELE = os.environ.get("LE_CONSEIL_JUGE_MODELE", "sonnet")

# LES DIX sont posees au narrateur et nomment toujours leur sujet : l'acteur,
# sa tache ou les resultats arbitres. Aucun « la reponse » sans referent.
QUESTIONS = [
    (u"tache", u"L'acteur a-t-il identifie la tache exacte que le narrateur "
               u"lui a confiee ?"),
    (u"but", u"L'acteur a-t-il vise un resultat precis qui ferait avancer "
             u"cette tache ?"),
    (u"place_tache", u"Ce qu'a fait l'acteur sert-il la place de cette tache "
                     u"dans le plan de son lord ?"),
    (u"plan", u"L'acteur a-t-il formule un plan d'action concret ?"),
    (u"suivi", u"L'acteur a-t-il suivi ce plan ou l'a-t-il adapte a un fait "
               u"rencontre ?"),
    (u"action", u"L'acteur est-il effectivement passe a l'action, au lieu de "
                u"seulement commenter ou preparer ?"),
    (u"avancement", u"Les gestes de l'acteur ont-ils produit au moins un "
                    u"avancement concret de la tache ?"),
    (u"competence", u"L'acteur a-t-il montre une competence propre a son "
                    u"office pour obtenir cet avancement ?"),
    (u"suite", u"Si la tache reste ouverte, l'acteur a-t-il determine sa "
               u"prochaine action precise ?"),
    (u"mieux", u"L'acteur a-t-il cherche ce qu'il pouvait faire en plus, "
               u"autrement ou mieux ?"),
]


def _compte(session):
    os.makedirs(COMPTES, exist_ok=True)
    return os.path.join(COMPTES, "%s.n" % re.sub(r"[^A-Za-z0-9_.-]", "_",
                                                 session or "sans-session"))


def relances_faites(session):
    p = _compte(session)
    if not os.path.exists(p):
        return 0
    try:
        return int(io.open(p, encoding="utf-8").read().strip() or 0)
    except ValueError:
        return 0


def noter_relance(session):
    n = relances_faites(session) + 1
    with io.open(_compte(session), "w", encoding="utf-8") as f:
        f.write(u"%d" % n)
    return n


def depouiller(transcript, plafond=24000):
    """Ce que l'homme a REELLEMENT fait, tire de son transcript.

    Deux choses, et pas une de plus : la liste de ce qu'il a ouvert (ses
    appels d'outil, dans l'ordre), et son dernier message — son rapport. Le
    reste de sa reflexion ne regarde pas le juge : on note une journee, pas
    une facon de penser.
    """
    ouvert, dernier = [], u""
    if not transcript or not os.path.exists(transcript):
        return ouvert, dernier
    with io.open(transcript, encoding="utf-8", errors="replace") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                d = json.loads(ligne)
            except ValueError:
                continue
            if d.get("type") == "item.completed":
                item = d.get("item") or {}
                if item.get("type") == "agent_message" and item.get("text"):
                    dernier = item["text"]
                elif item.get("type") in ("command_execution", "mcp_tool_call",
                                          "file_change"):
                    cible = (item.get("command") or item.get("name") or
                             item.get("path") or "")
                    ouvert.append(u"%s %s" % (item.get("type"),
                                               str(cible)[:120]))
                continue
            msg = d.get("message") or {}
            if d.get("type") != "assistant" and msg.get("role") != "assistant":
                continue
            contenu = msg.get("content")
            if isinstance(contenu, str):
                dernier = contenu
                continue
            for bloc in (contenu or []):
                if not isinstance(bloc, dict):
                    continue
                if bloc.get("type") == "text" and bloc.get("text", "").strip():
                    dernier = bloc["text"]
                elif bloc.get("type") == "tool_use":
                    e = bloc.get("input") or {}
                    cible = (e.get("file_path") or e.get("path") or
                             e.get("pattern") or e.get("command") or u"")
                    ouvert.append(u"%s %s" % (bloc.get("name"),
                                              str(cible)[:120]))
    return ouvert, dernier[-plafond:]


def charge_du_juge(qui, ouvert, dernier):
    liste = u"\n".join(u"%2d. [%s] %s" % (i + 1, c, t)
                       for i, (c, t) in enumerate(QUESTIONS))
    return u"""Tu controles le narrateur local qui vient d'arbitrer l'activation
de l'acteur « %(qui)s ». Tu juges la performance de L'ACTEUR depuis les gestes,
les sources et les resultats que le narrateur a etablis. Tu ne juges ni le
style du JSON ni la prose du narrateur.

RAPPORT DU NARRATEUR :
─────────────────────────────────────────────────────────────────
%(dernier)s
─────────────────────────────────────────────────────────────────

LES DIX QUESTIONS. Reponds pour l'acteur, par oui ou non. Un oui vaut un point ;
il lui faut %(seuil)d points pour que son activation passe.

%(liste)s

Ne confonds jamais une activite racontee avec un avancement : `avancement` est
oui seulement si un resultat produit modifie concretement la tache. Une
preparation peut valoir `plan` ou `action` sans valoir `avancement`.

TA REPONSE EST UN OBJET JSON NU, sans phrase avant ni apres, sans bloc de
code autour :

{
  "reponses": {"tache": true, "plan": false, ...},
  "manques": [
    "<pour CHAQUE non : ce qui manque, en une phrase, adressee a lui,
      concrete et actionnable — ce que l'acteur doit faire ensuite>"
  ]
}

Les clefs de `reponses` sont exactement les dix codes entre crochets.
`manques` ne contient QUE les non, dans l'ordre des questions.
""" % {"qui": qui, "dernier": dernier or u"(rien)",
       "liste": liste, "seuil": SEUIL}


def juger(qui, ouvert, dernier):
    """Rend (note, manques). Une panne du juge rend (None, []) : on ne
    relance JAMAIS sur un juge muet — un outil casse ne doit pas faire
    recommencer sa journee a un homme qui l'a bien faite."""
    charge = charge_du_juge(qui, ouvert, dernier)
    try:
        from agents.expose import runtime as agent_runtime
        with tempfile.TemporaryDirectory(prefix="juge-agent-") as neutre:
            out = agent_runtime.appeler(
                role="juge:%s" % qui,
                manuel=(u"Tu es un juge indépendant. Tu ne modifies aucun "
                        u"fichier et tu rends uniquement l'objet JSON demandé."),
                message=charge, session_id=str(uuid.uuid4()), modele=MODELE,
                timeout=180, cwd=neutre, add_dirs=[], tools=[],
                reprendre=False, ecriture=False)
        t = (out.get("result") or "").strip()
        t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t).strip()
        d = json.loads(t[t.find("{"):t.rfind("}") + 1])
    except Exception:
        return None, []
    rep = d.get("reponses") or {}
    note = sum(1 for c, _ in QUESTIONS if rep.get(c) is True)
    return note, [m for m in (d.get("manques") or []) if m]


def relance(manques, note, reste):
    return (u"Tu es le NARRATEUR, pas l'acteur. N'ameliore pas toi-meme sa "
            u"tentative et ne fabrique aucun nouveau resultat. Son activation "
            u"est a %(note)d/%(total)d. Rends uniquement cet objet JSON :\n\n"
            u"{\n  \"relance_acteur\": {\n"
            u"    \"message\": \"adresse directe a l'acteur lui disant ce "
            u"qu'il doit reprendre\",\n"
            u"    \"manques\": %(manques)s\n  }\n}\n\n"
            u"Transforme les manques en consignes de travail precises. La "
            u"boucle transmettra ce message dans le fil de l'acteur. Il reste "
            u"%(reste)d relance(s) apres celle-ci."
            % {"note": note, "total": len(QUESTIONS),
               "manques": json.dumps(manques, ensure_ascii=False),
               "reste": reste})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sec", action="store_true",
                    help="montre le depouillement et la charge, n'appelle pas le juge")
    ap.add_argument("--transcript", default=None)
    ap.add_argument("--qui", default="cet homme")
    a = ap.parse_args()

    charge = {}
    if not a.transcript:
        brut = sys.stdin.read() if not sys.stdin.isatty() else ""
        try:
            charge = json.loads(brut) if brut.strip() else {}
        except ValueError:
            charge = {}

    transcript = a.transcript or charge.get("transcript_path")
    session = charge.get("session_id") or (a.transcript or "sec")
    qui = a.qui if a.qui != "cet homme" else (
        os.environ.get("LE_CONSEIL_QUI") or "cet homme")

    ouvert, dernier = depouiller(transcript)

    # Le narrateur a deja transforme le refus en demande de relance : laisser
    # cette reponse sortir vers la boucle, sinon le hook se bloquerait lui-meme.
    try:
        objet_dernier = json.loads(re.sub(
            r"^```(?:json)?\s*|\s*```$", "", dernier.strip()))
    except Exception:
        objet_dernier = {}
    if isinstance(objet_dernier, dict) and (
            objet_dernier.get("relance_acteur") or
            objet_dernier.get("appel_pnj")):
        return

    if a.sec:
        print(u"OUVERT (%d) :" % len(ouvert))
        for o in ouvert[:40]:
            print(u"  · %s" % o)
        print(u"\nRAPPORT : %d caracteres" % len(dernier))
        print(u"\n" + u"─" * 70 + u"\nCHARGE DU JUGE\n" + u"─" * 70)
        print(charge_du_juge(qui, ouvert, dernier)[:4000])
        return

    # Le second filet, avant tout appel : `stop_hook_active` dit que c'est
    # NOUS qui l'avons relance. Sans ce garde-fou, un Stop qui bloque est une
    # boucle infinie — et elle coute une session entiere avant qu'on la voie.
    faites = relances_faites(session)
    if charge.get("stop_hook_active") and faites >= RELANCES_MAX:
        return
    if faites >= RELANCES_MAX:
        return

    note, manques = juger(qui, ouvert, dernier)
    if note is None:          # juge muet : on laisse passer, jamais l'inverse
        return
    if note >= SEUIL or not manques:
        return

    noter_relance(session)
    print(json.dumps({"decision": "block",
                      "reason": relance(manques, note,
                                        RELANCES_MAX - faites - 1)},
                     ensure_ascii=False))
