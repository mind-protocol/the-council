# -*- coding: utf-8 -*-
"""MIGRATION DU PARLOIR — les fils etat/parloir/ vers les canaux des chambres
(docs/habitant.md pas 7).

Une conversation n'est pas de la verite : elle n'avait rien a faire dans
etat/. Chaque fil <a>~<b>.jsonl devient le discussion.json du canal canonique
chambre.canal(a, b) ; les fils d'instance (<a>.<hex8>~<b>) se rabattent sur la
meme paire, fusionnes par leur horodatage.

LES CURSEURS SONT POSES A « TOUT LU » DES DEUX COTES : l'histoire migree est
de la memoire, pas des billets neufs — sans cela, soixante fils deverseraient
leurs percepts au prochain reveil de chacun.

Les fils vers `tous` ne migrent pas (une criee n'est pas une paire). Le
joueur migre comme les autres : sa « chambre » de session est son navigateur,
mais le canal doit bien vivre quelque part, et la geographie (rien dans
chambres/ ne fait foi) le couvre comme tout le monde.

A sec par defaut ; --vraiment ecrit les canaux, pose les curseurs, puis
SUPPRIME les fils migres et leurs curseurs (une seule source de verite —
le legacy part dans le meme geste).
"""
import io
import json
import os
import re

from agents import chambre

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
PARLOIR = os.path.join(RACINE, "etat", "parloir")
CURSEURS = os.path.join(PARLOIR, ".curseurs")

INSTANCE = re.compile(r"\.[0-9a-f]{8}$")


def _paires():
    """Les fils groupes par paire canonique : {(a, b): [chemins]}."""
    groupes = {}
    if not os.path.isdir(PARLOIR):
        return groupes
    for nom in sorted(os.listdir(PARLOIR)):
        if not nom.endswith(".jsonl"):
            continue
        brut = nom[:-6]
        cotes = brut.split("~")
        if len(cotes) != 2:
            continue
        a, b = (INSTANCE.sub("", c) for c in cotes)
        if "tous" in (a, b) or not a or not b:
            continue
        groupes.setdefault(tuple(sorted((a, b))), []).append(
            os.path.join(PARLOIR, nom))
    return groupes


def _entrees_de(chemins):
    """Toutes les entrees des fils d'une paire, fusionnees par horodatage."""
    entrees = []
    for chemin in chemins:
        with io.open(chemin, encoding="utf-8", errors="replace") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne:
                    continue
                try:
                    d = json.loads(ligne)
                except ValueError:
                    continue
                if isinstance(d, dict) and d.get("texte"):
                    entrees.append(d)
    entrees.sort(key=lambda e: e.get("t") or 0)
    return [{"de": INSTANCE.sub("", str(e.get("de") or "")),
             "t": e.get("t"),
             "texte": e["texte"]} for e in entrees]


def migrer(vraiment=False, dire=print):
    """Rend {canaux, entrees, fils} — ce qui a ete (ou serait) fait."""
    bilan = {"canaux": 0, "entrees": 0, "fils": 0}
    for (a, b), chemins in sorted(_paires().items()):
        neuves = _entrees_de(chemins)
        if not neuves:
            continue
        bilan["canaux"] += 1
        bilan["entrees"] += len(neuves)
        bilan["fils"] += len(chemins)
        dire("  %s ~ %s : %d entree(s) depuis %d fil(s)%s"
             % (a, b, len(neuves), len(chemins),
                "" if vraiment else "  [a sec]"))
        if not vraiment:
            continue
        canal = chambre.canal(a, b)  # ouvre les deux chambres au passage
        existantes = []
        if os.path.exists(canal):
            with io.open(canal, encoding="utf-8") as f:
                existantes = (json.load(f).get("entrees") or [])
        # L'histoire migree PRECEDE ce que les chambres ont deja echange.
        with io.open(canal, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"canal": [a, b], "entrees": neuves + existantes},
                      f, ensure_ascii=False, indent=1)
        for qui, autre in ((a, b), (b, a)):
            with io.open(os.path.join(chambre.chemin(qui), "relations",
                                      autre, ".lu"), "w",
                         encoding="utf-8", newline="\n") as f:
                f.write("%d" % (len(neuves) + len(existantes)))
        for chemin in chemins:
            os.remove(chemin)
            nom = os.path.basename(chemin)[:-6]
            if os.path.isdir(CURSEURS):
                for c in os.listdir(CURSEURS):
                    if c.startswith(nom + "."):
                        os.remove(os.path.join(CURSEURS, c))
    return bilan
