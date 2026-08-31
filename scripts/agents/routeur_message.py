# -*- coding: utf-8 -*-
"""ROUTEUR MESSAGE — deuxieme couche apres le selecteur de contexte.

Le selecteur ne joue rien. Ce routeur prend son artefact valide : toute action
va au MJ, et une parole va aussi directement aux hommes selectionnes, chacun
dans la session stable de l'item d'affaire que ``routes_hommes`` lui attribue.
Les hommes travaillent d'abord ; le MJ recoit ensuite l'action exacte et le
bilan des routes deja servies, afin de ne pas les depecher une seconde fois.
"""
import concurrent.futures

from agents import mj
from agents.depeche.mission import depecher


def est_une_parole(action):
    mode = str(action.get("mode") or "").casefold()
    genre = str(action.get("type") or "").casefold()
    return mode in ("dire", "parler") or genre == "parler"


def _mission_directe(joueur, texte, route, ref=None):
    provenance = (u" --contexte %s --ref %s"
                  % (route["contexte_id"], ref)
                  if ref else u" --contexte %s" % route["contexte_id"])
    return (u"MESSAGE DU JOUEUR, RECU DIRECTEMENT DANS TON CONTEXTE `%s`.\n"
            u"REF D'ORIGINE : `%s`.\n"
            u"%s vient de parler. Ses mots exacts :\n"
            u"« %s »\n\n"
            u"Tu es route ici parce que cette parole touche l'etat cible `%s`. "
            u"Reagis depuis ta tete, tes sources et ton travail dans cette "
            u"affaire. N'invente pas la parole d'un autre et ne demande pas "
            u"au MJ de redire ce message. Si tu reponds au joueur, ta reponse "
            u"n'existe pour lui QUE si tu l'envoies maintenant par :\n"
            u"python scripts/parloir.py --dire --de %s --a %s%s \"<tes mots>\"\n"
            u"Cette porte la rend directement dans son flux web et la copie "
            u"dans le flux du MJ. Ta reponse finale de session, seule, ne lui "
            u"parvient pas."
            % (route["contexte_id"], ref or u"—", joueur, texte,
               route["pointeur"], route["homme"], joueur, provenance))


def _servir_route(joueur, texte, route, modele=None, ref=None):
    ok = depecher(
        route["homme"], _mission_directe(joueur, texte, route, ref=ref),
        modele, None, False, attendre=True,
        contexte_id=route["contexte_id"], ref=ref, mode="discussion")
    return {"homme": route["homme"],
            "pointeur": route["pointeur"],
            "contexte_id": route["contexte_id"],
            "servi": bool(ok)}


def router_message(document, action, modele=None):
    """Sert les routes d'une action, puis appelle le MJ sur cette seule ref."""
    joueur = str(document.get("joueur_id") or action.get("joueur_id") or "")
    ref = str(document.get("ref") or action.get("ref") or "")
    selection = document.get("selection") or {}
    est_jump = str(action.get("mode") or "").casefold() == "jump"
    routes = (list(selection.get("routes_hommes") or [])
              if est_une_parole(action) else [])
    retours = []
    if routes:
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(4, len(routes))) as pool:
            appels = [pool.submit(_servir_route, joueur,
                                  str(action.get("texte") or ""), route,
                                  modele, ref)
                       for route in routes]
            for route, appel in zip(routes, appels):
                try:
                    retours.append(appel.result())
                except Exception as exc:
                    retours.append({"homme": route.get("homme"),
                                    "pointeur": route.get("pointeur"),
                                    "contexte_id": route.get("contexte_id"),
                                    "servi": False,
                                    "erreur": "%s: %s" %
                                              (type(exc).__name__, str(exc))})

    contexte_mj = {
        "ref": ref,
        "decision": selection.get("decision"),
        "pointeurs": selection.get("pointeurs") or [],
        "creation": selection.get("creation"),
        "joueurs_concernes": selection.get("joueurs_concernes") or [],
        "routes_hommes": retours,
        "consigne": ("Les hommes marques `servi:true` ont deja recu le "
                     "message dans leur session d'item. Ne les depeche pas "
                     "une seconde fois pour cette parole ; lis leur fil ou "
                     "leur retour, puis mets leur reaction en scene."),
    }
    if est_jump:
        contexte_mj = {
            "ref": ref,
            "decision": "jump",
            "jump": ((document.get("contexte_fourni") or {}).get("jump")),
            "consigne": (
                "JUMP 1 : le skill système jump-scene est injecté dans ce "
                "réveil. Exécute son processus complet sur cet événement et "
                "ce contexte_id, meuble le flux pendant les appels, avance "
                "réellement la clock et ne rends pas la main avant que "
                "l'événement soit appliqué et sa scène jouée. Aucune décision "
                "préparatoire ne remonte au joueur."),
        }
    resultat_mj = mj.appeler_mj(
        joueur, "", u"JOUEUR", modele=modele,
        refs=[ref] if ref else None, routage=contexte_mj)
    return {"parole": est_une_parole(action), "jump": est_jump,
            "hommes": retours,
            "mj": {"appele": True,
                   "resultat": str(resultat_mj or "")[-500:]}}
