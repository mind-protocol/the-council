# -*- coding: utf-8 -*-
"""TRACE — le vecu d'un habitant, depose dans son fil/ (docs/habitant.md pas 6).

Une session Claude laisse un transcript dans son magasin ; la porte Codex
conserve son flux JSONL et son chemin dans le registre local. Ce module les
depouille sous un meme contrat et depose une version lisible dans
chambres/<qui>/fil/ : le
reveil (ce qu'on lui a dit), ses gestes (les outils, dans l'ordre), ses
paroles. C'est de la memoire, pas de la verite — la regle de geographie de
chambre.py s'applique.

POURQUOI PAS UN HOOK STOP. Le vecu appartient au contrat du jeu, pas a la
configuration locale d'un fournisseur. Le depot est donc fait PAR LE
LANCEUR : mission appelle `deposer()` apres un call, et en fin de cast.
"""
import glob
import io
import json
import os

from agents import chambre

MAGASIN = os.path.join(os.path.expanduser("~"), ".claude", "projects")
SESSIONS_RUNTIME = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), ".agents-runtime",
                                "sessions.json")
PLAFOND_TEXTE = 4000  # une parole tronquee reste lisible ; le transcript fait foi


def trouver(session_id, provider=None):
    """Le transcript de cette session, ou None — glob sur tout le magasin,
    car chaque pas-de-tir mkdtemp fait naitre un dossier de projet neuf."""
    if provider == "codex" or os.path.exists(SESSIONS_RUNTIME):
        try:
            with io.open(SESSIONS_RUNTIME, encoding="utf-8") as f:
                entree = (json.load(f).get(session_id) or {})
            chemin = entree.get("dernier_transcript")
            if chemin and os.path.exists(chemin):
                return chemin
        except (OSError, ValueError):
            pass
    c = glob.glob(os.path.join(MAGASIN, "*", session_id + ".jsonl"))
    return max(c, key=os.path.getmtime) if c else None


def depouiller_fil(transcript):
    """Les evenements du vecu, dans l'ordre : (genre, texte).

    genre : 'reveil' (ce qu'on lui a dit — chaque tour user), 'geste'
    (un outil, sa cible), 'parole' (un texte de lui), 'entendu' (ce que le
    parloir lui a repondu — une voix EN SA PRESENCE fait partie du vecu,
    un resultat d'outil ordinaire n'en fait pas partie). Plus complet que
    le lecteur d'archives, qui ne garde que le dernier mot :
    ici on garde la journee entiere, c'est de la memoire.
    """
    evenements = []
    oreilles = set()  # les tool_use dont le resultat est une voix (parloir)
    if not transcript or not os.path.exists(transcript):
        return evenements
    with io.open(transcript, encoding="utf-8", errors="replace") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                d = json.loads(ligne)
            except ValueError:
                continue
            if d.get("type") == "le_conseil.user":
                if str(d.get("message") or "").strip():
                    evenements.append(("reveil", str(d["message"])[:PLAFOND_TEXTE]))
                continue
            if d.get("type") == "item.completed":
                item = d.get("item") or {}
                if item.get("type") == "agent_message" and item.get("text"):
                    evenements.append(("parole", item["text"][:PLAFOND_TEXTE]))
                elif item.get("type") in ("command_execution", "mcp_tool_call",
                                          "file_change"):
                    cible = (item.get("command") or item.get("name") or
                             item.get("path") or item.get("id") or "")
                    evenements.append(("geste", u"%s %s" % (
                        item.get("type"), str(cible)[:160])))
                continue
            msg = d.get("message") or {}
            role = msg.get("role") or d.get("type")
            contenu = msg.get("content")
            if role == "user" and d.get("toolUseResult") is not None:
                for bloc in (contenu if isinstance(contenu, list) else []):
                    if not (isinstance(bloc, dict) and
                            bloc.get("type") == "tool_result" and
                            bloc.get("tool_use_id") in oreilles):
                        continue
                    t = bloc.get("content")
                    if isinstance(t, list):
                        t = u" ".join(x.get("text", "") for x in t
                                      if isinstance(x, dict))
                    if t and str(t).strip():
                        evenements.append(("entendu", str(t)[:PLAFOND_TEXTE]))
                continue
            if role == "user" and not d.get("toolUseResult"):
                if isinstance(contenu, str) and contenu.strip():
                    evenements.append(("reveil", contenu[:PLAFOND_TEXTE]))
                elif isinstance(contenu, list):
                    for bloc in contenu:
                        if isinstance(bloc, dict) and bloc.get("type") == "text" \
                                and bloc.get("text", "").strip():
                            evenements.append(("reveil", bloc["text"][:PLAFOND_TEXTE]))
            if role != "assistant" and d.get("type") != "assistant":
                continue
            if isinstance(contenu, str) and contenu.strip():
                evenements.append(("parole", contenu[:PLAFOND_TEXTE]))
                continue
            for bloc in (contenu or []):
                if not isinstance(bloc, dict):
                    continue
                if bloc.get("type") == "text" and bloc.get("text", "").strip():
                    evenements.append(("parole", bloc["text"][:PLAFOND_TEXTE]))
                elif bloc.get("type") == "tool_use":
                    e = bloc.get("input") or {}
                    cible = (e.get("file_path") or e.get("path") or
                             e.get("pattern") or e.get("command") or u"")
                    evenements.append(("geste", u"%s %s" % (
                        bloc.get("name"), str(cible)[:160])))
                    if "parloir" in str(cible):
                        oreilles.add(bloc.get("id"))
    return evenements


def deposer(qui, session_id, etiquette=None, transcript=None, provider=None,
            contexte_id=None, ref=None):
    """Depose le vecu de cette session dans chambres/<qui>/fil/.

    Idempotent : meme session -> meme fichier, reecrit (le transcript ne fait
    que grandir). `etiquette` est le moment du monde ('129.4.4') ; sans elle,
    le fichier ne porte que la session. Rend le chemin ecrit, ou None si le
    transcript est introuvable.
    """
    transcript = transcript or trouver(session_id, provider=provider)
    evenements = depouiller_fil(transcript)
    if not evenements:
        return None
    fil = chambre.fil(qui, contexte_id=contexte_id, creer=True)
    nom = u"%s-%s.md" % (etiquette or u"session", session_id[:8])
    chemin = os.path.join(fil, nom)
    lignes = [u"# Vécu de %s — %s" % (qui, etiquette or session_id[:8]),
              u"", u"session `%s`" % session_id]
    if contexte_id is not None:
        lignes.append(u"contexte `%s`" % contexte_id)
    if ref:
        lignes.append(u"origine `%s`" % ref)
    lignes.append(u"")
    for genre, texte in evenements:
        if genre == "entendu":
            lignes.append(u"")
            lignes.append(u"> 👂 %s" % texte.replace(u"\n", u"\n> "))
            lignes.append(u"")
        elif genre == "geste":
            lignes.append(u"- 🤚 `%s`" % texte)
        elif genre == "reveil":
            lignes.append(u"")
            lignes.append(u"> 📯 %s" % texte.replace(u"\n", u"\n> "))
            lignes.append(u"")
        else:
            lignes.append(u"")
            lignes.append(texte)
            lignes.append(u"")
    with io.open(chemin, "w", encoding="utf-8") as f:
        f.write(u"\n".join(lignes) + u"\n")
    return chemin
