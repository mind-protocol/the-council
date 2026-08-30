# -*- coding: utf-8 -*-
"""NOTE — la note d'un etat cible, et l'echelle qui s'y regle.
"""
import io
import json
import os

from plan.expose import nu
from plan.criticite.graphe import POIDS

#
# ON NE SAISIT PAS UN POIDS, ON DONNE UNE NOTE SUR DIX. Un poids est un nombre
# de machine : personne ne sait dire si le Trone « vaut 12 » ou « vaut 40 », et
# celui qui l'ecrirait le prendrait au hasard puis n'oserait plus y toucher. Une
# note sur dix est un jugement d'homme, et elle se defend en une phrase.
#
# L'ECHELLE SE REGLE SUR LE GRAPHE, ET C'EST TOUT LE POINT. Une note portee en
# poids lineaire (1 a 10) ne pese RIEN contre la topologie : une chaine qui sert
# huit etats bat un objectif note 10 tout seul, et l'on aurait donne au joueur un
# volant qui ne tourne pas. On mesure donc d'abord ce que le graphe amplifie
# deja — l'ecart entre le cahier le plus lourd et le cahier median, a notes
# egales — et l'on cale l'echelle dessus :
#
#     note 5  ->  1          la neutralite, ce que valent les choses aujourd'hui
#     note 10 ->  A          A = amplitude structurelle du plan
#     note 0  ->  1/A        poids(note) = A ** ((note - 5) / 5)
#
# Autrement dit : passer un objectif de 5 a 10 lui donne exactement le poids que
# la topologie donne, a elle seule, au plus gros cahier contre un cahier moyen.
# Une main d'homme pese alors autant qu'une position dans le graphe, ni plus ni
# moins. Et quand le plan change de forme, l'echelle suit — d'ou « adaptative ».
#
# SEULS LES OBJECTIFS FINAUX PORTENT UNE NOTE, et les autres etats valent ZERO.
# Ce n'est pas une economie de saisie : un etat intermediaire n'a pas de valeur
# propre, il vaut ce qu'il sert. Lui laisser 1 revenait a payer deux fois la meme
# chose, et c'est ce qui faisait remonter la plomberie au-dessus du but.
NOTE_NEUTRE = 5.0
AMPLITUDE_MIN, AMPLITUDE_MAX = 3.0, 20.0


def objectifs_finaux(pieces):
    """Les etats cibles qui ne servent aucun autre etat : le bout des chaines."""
    et = {n for n, p in pieces.items() if p["genre"] == "etat"}
    return sorted(n for n in et
                  if not [v for v in pieces[n]["vers"] if v in et])


def amplitude(pieces, lignes):
    """Ce que le graphe amplifie tout seul : le cahier le plus lourd contre le
    median, a notes egales. Bornee, parce qu'un plan de trois cahiers donnerait
    un rapport absurde et qu'un plan tres plat rendrait la note inoperante."""
    par = {}
    for c, pt, n, p in lignes:
        par[p["affaire"]] = par.get(p["affaire"], 0) + c
    v = sorted(x for x in par.values() if x > 0)
    if len(v) < 4:
        return AMPLITUDE_MIN
    med = v[len(v) // 2]
    return max(AMPLITUDE_MIN, min(AMPLITUDE_MAX, (v[-1] / med) if med else AMPLITUDE_MIN))


def poids_des_etats(pieces, ampli=None):
    """(poids par etat, nombre de notes saisies).

    Sans fichier, ou tant qu'aucune note n'est ecrite, TOUT VAUT 1 comme avant :
    on ne change pas la mesure sous les pieds de quelqu'un qui n'a rien demande.
    Des qu'une note existe, on bascule dans le regime des objectifs finaux — les
    notes portent, les etats intermediaires valent zero."""
    brut = {}
    if os.path.exists(POIDS):
        try:
            brut = json.load(io.open(POIDS, encoding="utf-8"))
        except Exception:
            brut = {}
    notes = brut.get("notes") if isinstance(brut.get("notes"), dict) else {}
    # L'ANCIENNE FORME RESTE LISIBLE : un fichier de nombres nus est pris pour des
    # poids directs. On ne casse pas ce que quelqu'un aurait deja ecrit a la main.
    directs = {k: v for k, v in brut.items()
               if not k.startswith(u"_") and isinstance(v, (int, float))}
    etats = [n for n, p in pieces.items() if p["genre"] == "etat"]
    if not notes:
        return {n: float(directs.get(n, 1)) for n in etats}, len(directs)
    a = ampli or AMPLITUDE_MIN
    fins = set(objectifs_finaux(pieces))
    poids = {}
    for n in etats:
        if n not in fins:
            poids[n] = 0.0            # il vaut ce qu'il sert, pas plus
            continue
        note = float(notes.get(n, NOTE_NEUTRE))
        poids[n] = round(a ** ((note - NOTE_NEUTRE) / NOTE_NEUTRE), 3)
    return poids, len([n for n in notes if n in fins])


def masse(ok, poids):
    return sum(w for n, w in poids.items() if ok.get(n))


def portee(n, pieces, poids, cache):
    """Les etats cibles qu'une piece sert, en remontant. Ensemble, pas somme de
    chemins : un losange compterait deux fois le meme etat."""
    if n in cache:
        return cache[n]
    cache[n] = set()          # coupe les cycles
    vus = set()
    p = pieces.get(n)
    if p:
        if p["genre"] == "etat":
            vus.add(n)
        for v in p["vers"]:
            if v in pieces:
                vus |= portee(v, pieces, poids, cache)
    cache[n] = vus
    return vus

