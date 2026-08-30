# -*- coding: utf-8 -*-
"""ECHEANCES — le jour, les statuts, l'echelle relative J−N, et les
registres annexes (offices, moyens) lus a plat.
"""
import io
import json
import os
import re
import sys

from plan.expose import (nu, sans_emoji, marque, blocs,  # noqa: F401
                         NUM, MO, NOM_GENRE, EST_MO, NERA, etiquette)
from plan.expose import genre_de as C_genre  # noqa: F401
# Les tables de la descente et le motif du « fait » vivent chez le chargeur :
# un seul lecteur du graphe, une seule verite — y compris pour ses constantes.
from plan.expose import ATTENDU as C_ATTENDU, RANG as C_RANG  # noqa: F401
from plan.expose import FINI as C_FINI, premier_mot as C_premier_mot  # noqa: F401
from plan.expose import tete_ornee as C_tete_ornee  # noqa: F401
from plan.expose import numero_de as C_numero_de  # noqa: F401
# LE SEUL point de contact du paquet avec jours_relatifs (container temps) :
# les autres modules reprennent JR d'ici, pour que le lien reste unique.
from temps.expose import jours_relatifs as JR  # noqa: F401 — LA PORTE de temps/
import plan_modele as PM  # noqa: F401

# Trois etages de plus qu'a la racine : scripts/plan/etat_du_plan/.
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

# ─────────────────────────────────────────────── le jour, et les echeances
def aujourdhui():
    m = json.load(io.open(os.path.join(RACINE, "etat", "monde.json"), encoding="utf-8"))
    return m.get("date") or {}


def rang(annee, lune, jour):
    """Un numero de jour, pour comparer. Une lune vaut trente jours, douze l'an :
    approximation assumee — seul l'ecart entre deux dates nous interesse, et
    toutes les echeances du plan tiennent dans deux lunes."""
    return ((annee * 12) + lune) * 30 + jour


# « avant le 4e de la 4e », « le 4e jour de la 4e lune » : jour ET lune. Le mot
# entre les deux nombres est libre — « 4e jour de la 4e » s'ecrit aussi souvent
# que « 4e de la 4e », et l'oublier faisait lire le second nombre comme la lune
# courante : une echeance a venir devenait vingt-deux jours de retard.
DATE_LUNE = re.compile(r"(?:avant\s+)?le\s+(\d{1,2})e(?:\s+\w+)?\s+de\s+la\s+(\d{1,2})e", re.I)
# « avant le 30e », « avant le 28e au soir » : jour seul, dans la lune courante.
DATE_JOUR = re.compile(r"(?:avant|le)\s+le?\s*(\d{1,2})e", re.I)
# `voir` SANS limite de mot armait la lecture de dependance sur « sans avoir
# ete employee », et le nombre le plus proche etait pris pour un renvoi : les
# « 266 cerfs de Sirel » sont devenus une reference pendante de 64020. Un mot
# de dependance doit etre un MOT.
DEPEND = re.compile(u"apr[eè]s|d[eé]pend\\s+de|\\bvoir\\b", re.I)

# CE QUI EST CLOS — et la table l'ignorait. Elle a ete ecrite quand la colonne
# d'etat etait de la prose ; depuis la normalisation elle ne porte plus que six
# mots, et trois n'y figuraient pas. « faite » ne tombait dans aucun motif et
# ressortait « ? » : cinquante-six actions rendues s'affichaient comme si l'on
# ne savait pas ou elles en etaient.
FINI_ETAT = (u"faite", u"close", u"abandonnée")
STATUTS = [(u"^faite$", u"faite"), (u"^close$", u"close"),
           (u"^abandonn", u"abandonnée"),
           (u"tenu", u"tenu"), (u"bloqu", u"bloqué"), (u"en cours", u"en cours"),
           (u"retenue", u"retenue"), (u"à étudier|a etudier", u"à étudier"),
           (u"à faire|a faire", u"à faire")]


def statut_de(texte):
    t = sans_emoji(texte or u"").lower()
    for motif, nom in STATUTS:
        if re.search(motif, t):
            return nom
    return u"—" if not t else u"?"


def echeance_de(texte, date):
    """(rang, libelle) si la cellule porte une date lisible, sinon None."""
    t = nu(texte or u"")
    m = DATE_LUNE.search(t)
    if m:
        j, l = int(m.group(1)), int(m.group(2))
        return rang(date.get("annee", 0), l, j), u"%de jour de la %de lune" % (j, l)
    m = DATE_JOUR.search(t)
    if m:
        # Un jour NU ne dit pas sa lune. Le prendre pour la lune courante etait
        # juste vingt-neuf jours sur trente et faux le trentieme : au premier de
        # la quatrieme lune, « avant le 27e » devenait « dans vingt-six jours »
        # alors qu'il voulait dire « il y a quatre jours ». On retient donc
        # l'occurrence la PLUS PROCHE d'aujourd'hui, lune precedente comprise.
        j = int(m.group(1))
        a, l0 = date.get("annee", 0), date.get("lune", 0)
        ici = rang(a, l0, date.get("jour", 0))
        r, l = min(((rang(a, l0 + d, j), l0 + d) for d in (-1, 0, 1)),
                   key=lambda x: abs(x[0] - ici))
        return r, u"%de jour de la %de lune" % (j, l)
    return None


# ─────────────────────────────────────────────── l'echelle relative J−N
# Le chargeur de `couverture.py` ne retient qu'une poignee de colonnes, et les
# J−N vivent ailleurs : dans « Ce qu'on fait » (335 cellules), dans le cout
# (466), dans la note (83), dans l'office (24). On refait donc ici une passe
# de LECTURE SEULE sur les tables d'actions, avec la grammaire de
# `jours_relatifs.py` — la meme que celle qu'ecrit `dater_plan.py`, pour que
# le lecteur et l'ecrivain ne divergent jamais.
def relatives(livres):
    """{numero: (forme, colonne d'ou elle vient)} pour tout ce qui porte un J−N."""
    out = {}
    for b in livres:
        for t in (b.get("tables") or []):
            g = (C_genre((t or {}).get("titre") or u"")
                 or C_genre(b.get("titre") or u""))
            if g != "action":
                continue
            cols = (t or {}).get("colonnes") or []
            idx = {sans_emoji(nu(c)).strip().lower(): i for i, c in enumerate(cols)}
            for l in (t.get("lignes") or []):
                cel = [nu(x) for x in ((l if isinstance(l, list)
                                        else l.get("cellules")) or [])]
                if not cel:
                    continue
                m = C_numero_de(cel[0] or u"")
                if not m:
                    continue
                f, source = JR.candidat({k: cel[i] for k, i in idx.items()
                                         if i < len(cel)})
                if f:
                    out.setdefault(m.group(1), (f, source))
    return out


# L'ECHELLE, ACCESSIBLE AUX DETECTEURS SANS CHANGER LEUR SIGNATURE. `missions_de`
# est appelee a deux arguments par `criticite.py` et `depecher.py` : leur imposer
# un troisieme pour une seule regle serait payer le detecteur au prix de ses
# appelants. On memorise donc l'echelle une fois — posee par le __main__ qui a
# deja les livres en main, relue toute seule pour qui ne les a pas.
_REL = None


def echelle(livres=None):
    global _REL
    if _REL is None:
        if livres is None:
            livres = PM.charger()["livres"]
        _REL = relatives(livres)
    return _REL


def amont_de(texte):
    """Les pieces qu'une cellule dit attendre. On ne lit les numeros que si un
    mot de dependance est present : sinon « 220 » serait un jour, un compte
    d'hommes, ou n'importe quoi."""
    if not DEPEND.search(nu(texte or u"")):
        return []
    return sorted(set(NUM.findall(nu(texte))))


# ─────────────────────────────────────────────── les registres annexes
def colonne(livre, motif):
    for i, c in enumerate(livre.get("colonnes") or []):
        if re.search(motif, sans_emoji(c), re.I):
            return i
    return None


def registre(livres, ident, motif_cle):
    """{numero: valeur} pour une colonne d'un registre a plat (moyens, offices)."""
    b = next((x for x in livres if x.get("id") == ident), None)
    if not b:
        return {}
    i = colonne(b, motif_cle)
    if i is None:
        return {}
    out = {}
    for l in b.get("lignes") or []:
        c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
        if len(c) > max(1, i):
            m = MO.search(c[0])
            if m:
                out[m.group(1)] = c[i]
    return out

