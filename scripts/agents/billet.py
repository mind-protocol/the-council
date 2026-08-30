# -*- coding: utf-8 -*-
"""BILLET — ecrire = reveiller (docs/habitant.md §4 et pas 5).

L'arete « ecrire un billet a un absent » est un CAST, et l'ecriture EST le
reveilleur : aucun demon, aucun tick — le geste de poser le billet au canal
de la paire lance la vie du destinataire, detachee. Son brief lui sert le
billet EN PERCEPT (« Untel t'a ecrit : "…" », mission.py) : le depot vient
donc AVANT le lancement, et le curseur n'avance qu'au depart pris.

Le canal est celui de chambre.canal : le discussion.json canonique de la
paire, meme format que les canaux poses a la main (de, date, texte — l'heure
quand on la sait). RIEN dans chambres/ ne fait foi : un billet est de la
parole, pas de la verite.

PAS DE GARDE DE CREUX ICI, et c'est voulu : la garde de depecher (« aucun
creux — il travaille ») protege la boucle d'activation, qui propose. Un
billet ne propose pas : quelqu'un t'a ecrit, tu te reveilles — l'anachronisme
accepte que ce moment de ta vie se joue maintenant.
"""
import io
import json
import os

from agents import chambre
from agents.depeche.brief import date_du_monde

MINUTES = 15  # le budget du reveil caste — celui de depecher.py --minutes


def deposer(de, a, texte):
    """Appose une entree au canal canonique de la paire ; rend son chemin."""
    fichier = chambre.canal(de, a)
    d = {}
    if os.path.exists(fichier):
        try:
            with io.open(fichier, encoding="utf-8") as f:
                d = json.load(f)
        except ValueError:
            d = {}
    if not isinstance(d, dict):
        d = {}
    d.setdefault("canal", sorted((de, a)))
    annee, lune, jour = date_du_monde()
    d.setdefault("entrees", []).append({
        "de": de,
        "date": {"annee": annee, "lune": lune, "jour": jour},
        "texte": texte,
    })
    with io.open(fichier, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=2))
    return fichier


def _reveiller(qui, modele=None, minutes=MINUTES):
    """Le reveil caste du destinataire — la machinerie de mission.appeler
    (attendre=False), SANS la garde de creux de depecher (voir l'en-tete).
    Rend {cast, log, session}. Imports tardifs : la porte lie billet avant
    d'avoir fini, et depeche est deja charge a l'heure ou l'on ecrit."""
    from agents.depeche.brief import (brief_de, dossier_journee,
                                      identifiant_de_session)
    from agents.depeche.manuel import manuel_de
    from agents.depeche.mission import mission, appeler
    date = date_du_monde()
    sid = identifiant_de_session(qui, date)
    brief = brief_de(qui) or u""
    contexte = dossier_journee(qui, brief)
    manuel = manuel_de(qui, mode="journee", contexte=contexte)
    texte = mission(qui, brief, u"", contexte=contexte)
    rep = appeler(qui, manuel, texte, sid, modele, minutes, attendre=False)
    # Le depart a pris : son reveil a tout vu — les billets sont lus.
    chambre.marquer_lus(qui)
    return rep


def ecrire(de, a, texte, modele=None, minutes=MINUTES):
    """Le geste entier : depose le billet, puis reveille le destinataire en
    cast. Rend (chemin_du_canal, {cast, log, session})."""
    fichier = deposer(de, a, texte)
    return fichier, _reveiller(a, modele=modele, minutes=minutes)
