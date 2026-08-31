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
import hashlib
import io
import json
import os
import time
import uuid

from agents import chambre
from agents.depeche.brief import date_du_monde
from etat.expose import tables  # LA PORTE : lecture qui plante, ecriture directe

MINUTES = 15  # le budget du reveil caste — celui de depecher.py --minutes
DEDUP_SECONDES = 60
DEDUP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), ".agents-runtime", "transport-dedup")


class CanalAbime(Exception):
    """Le canal de la paire ne se lit pas. On ne repart JAMAIS a vide."""


class _VerrouCanal(object):
    """Petit verrou inter-processus : depot, test et marque forment un geste."""

    def __init__(self, fichier):
        empreinte = hashlib.sha256(fichier.encode("utf-8")).hexdigest()
        self.chemin = os.path.join(DEDUP, empreinte + ".lock")

    def __enter__(self):
        os.makedirs(DEDUP, exist_ok=True)
        limite = time.time() + 10
        while True:
            try:
                fd = os.open(self.chemin, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.chemin) > 30:
                        os.remove(self.chemin)
                        continue
                except OSError:
                    continue
                if time.time() >= limite:
                    raise RuntimeError("verrou du canal occupe depuis 10 secondes")
                time.sleep(.02)

    def __exit__(self, *_):
        try:
            os.remove(self.chemin)
        except OSError:
            pass


def _empreinte(de, a, texte, contexte_id, ref):
    matiere = json.dumps([str(de), str(a), str(texte),
                          str(contexte_id) if contexte_id is not None else None,
                          str(ref) if ref else None], ensure_ascii=False,
                         separators=(",", ":"))
    return hashlib.sha256(matiere.encode("utf-8")).hexdigest()


def _memoire_ephemere(fichier):
    nom = hashlib.sha256(fichier.encode("utf-8")).hexdigest() + ".json"
    return os.path.join(DEDUP, nom)


def _est_deja_la(entrees, de, texte, contexte_id, ref):
    """Une ref est une cle d'envoi durable ; sans ref, garde anti-retry 60 s."""
    contexte = str(contexte_id) if contexte_id is not None else None
    if ref:
        return any(e.get("de") == de and e.get("texte") == texte
                   and e.get("contexte_id") == contexte
                   and e.get("ref") == str(ref) for e in entrees)
    return False


def _marques_recentes(fichier, maintenant):
    chemin = _memoire_ephemere(fichier)
    try:
        with io.open(chemin, encoding="utf-8") as f:
            marques = json.load(f)
    except (OSError, ValueError):
        marques = {}
    marques = {k: v for k, v in marques.items()
               if isinstance(v, (int, float))
               and maintenant - v <= DEDUP_SECONDES}
    return chemin, marques


def _retry_recent(fichier, empreinte, maintenant):
    _, marques = _marques_recentes(fichier, maintenant)
    return maintenant - marques.get(empreinte, 0) <= DEDUP_SECONDES


def _marquer_envoi(fichier, empreinte, maintenant):
    chemin, marques = _marques_recentes(fichier, maintenant)
    marques[empreinte] = maintenant
    temporaire = chemin + ".%s.tmp" % uuid.uuid4().hex
    with io.open(temporaire, "w", encoding="utf-8", newline="\n") as f:
        json.dump(marques, f, ensure_ascii=False, sort_keys=True)
    os.replace(temporaire, chemin)


def deposer(de, a, texte, contexte_id=None, ref=None, statut=False):
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

    Le verrou inter-processus ferme aussi la course de deux depots simultanes.
    Sous ce meme verrou, une ref deja vue est idempotente pour toujours ; sans
    ref, une empreinte identique est ignoree pendant 60 secondes seulement.
    Ainsi un retry de transport ne parle et ne reveille qu'une fois, sans rendre
    impossible une vraie repetition plus tard dans la scene.
    """
    fichier = chambre.canal(de, a)
    with _VerrouCanal(fichier):
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
        entrees = d.setdefault("entrees", [])
        empreinte = _empreinte(de, a, texte, contexte_id, ref)
        maintenant = time.time()
        recent = _retry_recent(fichier, empreinte, maintenant)
        if _est_deja_la(entrees, de, texte, contexte_id, ref) or recent:
            return (fichier, False) if statut else fichier
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
        entrees.append(entree)
        tables.ecrire(fichier, d)
        _marquer_envoi(fichier, empreinte, maintenant)
    return (fichier, True) if statut else fichier


def _reveiller(qui, modele=None, minutes=MINUTES, contexte_id=None,
               ref=None, de=None):
    """Le reveil caste du destinataire — la machinerie de mission.appeler
    (attendre=False), SANS la garde de creux de depecher (voir l'en-tete).
    Rend {cast, log, session}. Imports tardifs : la porte lie billet avant
    d'avoir fini, et depeche est deja charge a l'heure ou l'on ecrit."""
    from agents.depeche.brief import (brief_de, dossier_journee,
                                      identifiant_de_session)
    from agents.depeche.manuel import manuel_de
    from agents.depeche.mission import mission, appeler
    date = date_du_monde()
    sid = identifiant_de_session(qui, date, contexte_id=contexte_id)
    brief = brief_de(qui) or u""
    contexte = dossier_journee(qui, brief)
    if contexte_id is not None:
        from agents.depeche.contexte_affaire import focaliser
        contexte = focaliser(contexte, contexte_id)
    manuel = manuel_de(qui, mode="journee", contexte=contexte)
    texte = mission(qui, brief, u"", contexte=contexte,
                    contexte_id=contexte_id, ref=ref, billet_de=de)
    rep = appeler(qui, manuel, texte, sid, modele, minutes, attendre=False,
                  contexte_id=contexte_id, ref=ref)
    # Le depart a pris : ce reveil a vu le canal qui l'a provoque. Un reveil
    # focalise ne consomme plus en silence les billets de tous les autres.
    chambre.marquer_lu(qui, de) if de else chambre.marquer_lus(qui)
    return rep


def ecrire(de, a, texte, modele=None, minutes=MINUTES, contexte_id=None,
           ref=None):
    """Le geste entier : depose le billet, puis reveille le destinataire en
    cast. Rend (chemin_du_canal, {cast, log, session})."""
    fichier, nouveau = deposer(de, a, texte, contexte_id=contexte_id, ref=ref,
                               statut=True)
    if not nouveau:
        return fichier, {"duplicate": True, "cast": False}
    return fichier, _reveiller(a, modele=modele, minutes=minutes,
                               contexte_id=contexte_id, ref=ref, de=de)
