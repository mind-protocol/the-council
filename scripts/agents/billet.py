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

PAS DE GARDE DE CREUX ICI, et c'est voulu. Un billet ne propose pas :
quelqu'un t'a ecrit, tu te reveilles — l'anachronisme
accepte que ce moment de ta vie se joue maintenant.
"""
import os

from agents import chambre
from agents.depeche.brief import date_du_monde
from etat.expose import tables  # LA PORTE : lecture qui plante, ecriture atomique

MINUTES = 15  # le budget du reveil caste — celui de depecher.py --minutes


class CanalAbime(Exception):
    """Le canal de la paire ne se lit pas. On ne repart JAMAIS a vide."""


def deposer(de, a, texte, contexte_id=None, ref=None):
    """Appose une entree au canal canonique de la paire ; rend son chemin.

    UN BILLET NE DOIT JAMAIS POUVOIR EFFACER UNE CORRESPONDANCE, et jusqu'au
    129.4.4 il le pouvait — trouve par mj-aurore, qui a vu le precurseur en
    direct (OSError [Errno 22] pendant qu'alicent ecrivait dans le meme canal)
    et qui tenait deja le temoin dans son journal du 129.4.3 : « curseur .lu a
    221 pour un canal de 21 entrees ». Ce n'etait pas un curseur trop grand,
    c'etait un canal devenu trop court.

    LE MECANISME, en trois lignes qui etaient toutes les trois ici :
      1. lire-modifier-REECRIRE sans atomicite : l'ecriture tronquait le
         fichier avant de le remplir, donc un lecteur simultane tombait sur du
         JSON invalide. Ecrire a quelqu'un le REVEILLE et il repond — deux
         plumes sur un canal est le mode normal de cette maison, pas le cas rare.
      2. `except ValueError: d = {}` : la lecture qui tombait sur ce fichier
         saisi en plein vol ne s'arretait pas, elle repartait d'un dict VIDE.
      3. la reecriture posait alors le canal entier reduit a UNE entree. Sans
         exception, sans trace, sans que ni l'expediteur ni le destinataire
         puisse s'en apercevoir.

    CE QUI LES REMPLACE, et c'est la doctrine deja ecrite de la porte
    (noyau/tables.py, points 1 et 4) : un JSON corrompu PLANTE, une ecriture est
    ATOMIQUE. Un canal illisible coute desormais UN billet, bruyamment ; il
    coutait toute une correspondance, en silence. C'est le meme arbitrage que
    d'habitude : ce qui echoue fort et etroit plutot que large et muet.

    CE QUI RESTE OUVERT ET N'EST PAS CORRIGE ICI (verrou D.20) : deux depots
    vraiment simultanes lisent tous deux N entrees et posent tous deux N+1 —
    le second billet ecrase le premier. L'atomicite ne ferme pas cette
    course-la ; seul un canal en APPEND (une entree par ligne, jamais relu pour
    etre reecrit) la ferme pour de bon. Un billet perdu, ce n'est pas un canal
    perdu : la difference est de trois ordres de grandeur, et c'est pour ca que
    la moitie ci-dessus part aujourd'hui sans attendre l'autre.
    """
    fichier = chambre.canal(de, a)
    d = tables.lire(fichier, {}) if os.path.exists(fichier) else {}
    if not isinstance(d, dict):
        # Lisible mais pas un canal : une liste nue, un nombre, `null`. On ne
        # devine pas ce que l'homme voulait — et surtout on ne l'ecrase pas.
        raise CanalAbime(
            u"%s se lit mais n'est pas un canal (JSON de type %s au lieu d'un "
            u"objet {canal, entrees}). Le billet de %s a %s n'est pas depose : "
            u"repare le fichier a la main, rien n'a ete ecrit par-dessus."
            % (fichier, type(d).__name__, de, a))
    d.setdefault("canal", sorted((de, a)))
    annee, lune, jour = date_du_monde()
    entree = {
        "de": de,
        "date": {"annee": annee, "lune": lune, "jour": jour},
        "texte": texte,
    }
    if contexte_id is not None:
        entree["contexte_id"] = str(contexte_id)
    if ref:
        entree["ref"] = str(ref)
    d.setdefault("entrees", []).append(entree)
    tables.ecrire(fichier, d)
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


def ecrire(de, a, texte, modele=None, minutes=MINUTES, contexte_id=None,
           ref=None):
    """Le geste entier : depose le billet, puis reveille le destinataire en
    cast. Rend (chemin_du_canal, {cast, log, session})."""
    fichier = deposer(de, a, texte, contexte_id=contexte_id, ref=ref)
    return fichier, _reveiller(a, modele=modele, minutes=minutes)
