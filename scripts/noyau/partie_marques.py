# -*- coding: utf-8 -*-
"""
partie_marques.py — ce que l'écran a le droit d'OFFRIR sur chaque carte.

La vue en cartes dit ce qu'une pièce EST. Elle ne disait pas ce qu'on peut en
faire de gratuit : exiger sa chaîne, ou répondre à celle qu'on exige de nous.
L'écran a besoin des deux pour poser ses poignées, et il ne doit les poser que
là où le greffe dirait oui — un bouton qui promet un coup refusé est pire que
pas de bouton.

Deux marques, et pas une de plus :

    questionnable   une clé, un blocage, une destruction ou un état D'EN FACE,
                    pas déjà justifié (`partie_validite`, branche `justifier`)
    suspendue       une clé, un blocage ou une destruction qu'un ❓ tient en
                    suspens, et que son camp peut relever d'un maillon
                    (`partie_greffe`, branche `agir`). Un ÉTAT suspendu n'y est
                    pas : aucun maillon ne lève sa suspension, c'est l'arbitre
                    qui tranche en constatant.

Elles se posent APRÈS la vue, sur l'arbre déjà bâti, et vivent ici plutôt que
dans `partie_cartes` — qui a passé les cinq cents lignes et ne peut plus que
maigrir (`.claude/hooks/taille.js`).
"""


def _objet(p, oid):
    return (p.cles.get(oid) or p.menaces.get(oid)
            or p.blocages.get(oid) or p.etats.get(oid))


def questionnable(p, camp, oid):  # regle: justifier-une-fois, pas-sa-propre-chaine
    """Peut-on encore exiger la chaîne de cette pièce ? Une fois par pièce,
    tous camps confondus, et jamais sur la sienne."""
    o = _objet(p, oid)
    return bool(o) and o["camp"] != camp and not o.get("justifiee")


def suspendue(p, camp, oid):
    """Cette pièce à NOUS attend-elle son maillon ? Un état n'est jamais de
    celles-là : sa suspension ne tombe que par l'arbitre."""
    o = (p.cles.get(oid) or p.menaces.get(oid) or p.blocages.get(oid))
    return bool(o) and o["camp"] == camp and bool(o.get("suspendue_par"))


def maillonnable(p, camp, oid):
    """Peut-on écrire un maillon sous cette pièce à NOUS sans qu'on l'ait
    demandé (6.9) ? Une clé, un blocage ou une destruction à soi, encore en
    jeu, pas suspendue (la suspendue a déjà sa poignée). Ça compte pour le
    jour et donne une carte à l'adversaire : c'est au joueur d'en décider."""
    o = (p.cles.get(oid) or p.menaces.get(oid) or p.blocages.get(oid))
    if not o or o["camp"] != camp or o.get("suspendue_par"):
        return False
    return not (o.get("retiree") or o.get("tombe") or o.get("tenue")
                or o.get("realisee") or o.get("tombee"))


def poser(vue, p, camp):
    """Marque toutes les cartes de la vue, en place, et la rend."""
    def marcher(objet):
        if isinstance(objet, dict):
            oid = objet.get("id")
            if oid is not None and "type" in objet:
                if questionnable(p, camp, str(oid)):
                    objet["questionnable"] = True
                # DE QUOI PEUT-ON ÉCRIRE LE MAILLON D'ICI ? De la carte
                # suspendue elle-même — et AUSSI de la question qui la
                # suspend, parce que c'est là que le joueur clique. Un joueur
                # qui veut répondre vise la question, pas la pièce : c'est le
                # geste naturel, et il ne menait nulle part.
                if suspendue(p, camp, str(oid)):
                    objet["suspendue"] = True
                    objet["repondre"] = str(oid)
                elif (objet.get("type") == "question" and objet.get("sur")
                      and suspendue(p, camp, str(objet["sur"]))):
                    objet["repondre"] = str(objet["sur"])
                elif maillonnable(p, camp, str(oid)):
                    objet["maillonnable"] = True
            for v in objet.values():
                marcher(v)
        elif isinstance(objet, list):
            for v in objet:
                marcher(v)
    marcher(vue)
    return vue
