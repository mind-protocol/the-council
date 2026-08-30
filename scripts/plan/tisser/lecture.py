# -*- coding: utf-8 -*-
"""LECTURE — le vocabulaire canonique des liens, la lecture des tables de
l'etat, la resolution des codes, et indexer() qui pose tous les noeuds.
"""
import collections
import json
import os
import re

import chiffrer  # la grammaire des couts

from etat.expose import tables  # LA PORTE de etat/

# Trois etages de plus qu'a la racine : scripts/plan/tisser/.
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
ETAT = os.path.join(RACINE, "etat")
SORTIE = os.path.join(ETAT, "tissu")


# LE VOCABULAIRE DES LIENS — seize natures, six familles. Il vit ICI parce que
# c'est le projecteur qui le pose : un script d'assessment qui lirait le tissu
# brut compterait 34 natures et raterait deux aretes sur 529 en cherchant
# `depend_de`. La lecon a deja ete payee sur `sterile()` — une definition
# ecrite deux fois diverge le jour meme.
CANON = {
    "realise": "realise", "réalise": "realise",
    "ouvre": "ouvre", "verrouille": "ouvre",
    "bloque": "bloque", "verrouillé_par": "bloque", "menacé_par": "bloque",
    "depend_de": "depend_de", "dépend_de": "depend_de",
    "sert": "sert", "servie_par": "sert$", "fournit": "sert",
    "garantit": "sert", "finance": "sert",
    "attend": "attend", "attendue_par": "attend$", "attendu_par": "attend$",
    "découpe": "decoupe", "découpée_par": "decoupe$", "partage": "decoupe",
    "lie": "lie",
    "coute": "coute", "coûte_à": "coute", "coute_chiffre": "coute_chiffre",
    "tient": "tient", "promeut": "promeut",
    "revele": "revele", "prévient": "revele", "surveille": "revele",
    "repond": "repond", "devie": "devie",
    "contredit": "contredit", "resonance": "resonance",
    "poursuit": "poursuit", "acteur_de": "acteur_de",
    "equilibre": "equilibre", "équilibre": "equilibre",
    "achemine": "achemine",
}

# `X$` : la meme arete, ecrite a l'envers. On la retourne — un graphe oriente
# qui garde les deux sens ment sur la moitie de ses fleches.
INVERSES = {"sert$": "sert", "attend$": "attend", "decoupe$": "decoupe"}

PIECE = re.compile(r"\b\d{3,6}\b")
MOYEN = re.compile(r"\bM\d{2,3}\b")
OFFICE = re.compile(r"\bO\d{2,3}\b")
HYPO = re.compile(r"\bH\d{1,2}\b")


def charger(nom, defaut):
    # Absent -> defaut ; corrompu -> plante (l'ancienne version avalait tout).
    d = tables.lire(nom, defaut)
    return d.get(nom, d) if isinstance(d, dict) else d


def grilles(livre):
    """Toutes les tables d'un volume, la sienne comprise."""
    out = []
    if livre.get("colonnes"):
        out.append((livre.get("titre") or "", livre["colonnes"],
                    livre.get("lignes") or []))
    for t in livre.get("tables") or []:
        if t.get("colonnes"):
            out.append((t.get("titre") or "", t["colonnes"],
                        t.get("lignes") or []))
    return out


# Les livres qui DEFINISSENT des moyens et des offices. Un M12 cite dans
# n'importe quel cahier designe celui de la sphere ou ce cahier vit — la
# reine et Aurore ont chacune leur M01, et ce ne sont pas les memes.
def registres_de(books):
    reg = {}
    for l in books:
        lid = l.get("id") or ""
        for titre, C, lignes in grilles(l):
            for r in lignes:
                tete = nu((r.get("cellules") or [""])[0])
                if MOYEN.fullmatch(tete) or OFFICE.fullmatch(tete):
                    reg.setdefault(lid, set()).add(tete)
    return reg


def sphere_de(lid):
    """A quelle sphere appartient un cahier. Les cahiers d'Aurore portent le
    prefixe `nera-` ou `affaire-` de son coffre ; le reste est a la reine."""
    return "nera" if str(lid).startswith("nera-") else "reine"


def resoudre_code(code, lid, registres):
    """Le livre de moyens/offices de la meme sphere, sinon le citant."""
    for rid, codes in registres.items():
        if code in codes and sphere_de(rid) == sphere_de(lid):
            return rid + ":" + code
    for rid, codes in registres.items():
        if code in codes:
            return rid + ":" + code
    return lid + ":" + code


def nommer(personnages):
    """nom en clair -> id. La colonne « Office » d'une action ecrit « Rulf
    Corne », pas « O07 » : sans cette table, 501 actions passaient pour sans
    titulaire alors que 54 seulement le sont. Un chiffre faux est pire qu'un
    chiffre absent — la lecon de `sterile()`, encore."""
    t = {}
    for p in personnages or []:
        if not isinstance(p, dict) or not p.get("id"):
            continue
        for forme in (p.get("nom") or "", p["id"].replace("-", " ")):
            k = plat_nom(forme)
            if len(k) > 4:
                t[k] = p["id"]
    return t


def plat_nom(t):
    import unicodedata as _u
    t = _u.normalize("NFD", str(t or ""))
    t = "".join(c for c in t if _u.category(c) != "Mn").lower()
    return re.sub(r"[^a-z ]+", " ", t).strip()


A_DESIGNER = re.compile(r"a *designer|a *nommer|case *vide", re.I)


def col(d, motif):
    """La cellule dont l'en-tete contient `motif` — les en-tetes portent des
    emoji et des accents, on ne peut pas les egaler."""
    for k, v in d.items():
        if motif in k:
            return str(v or "")
    return ""


def nu(t):
    return re.sub(r"\*", "", str(t or "")).strip()


# ------------------------------------------------------------ les noeuds

def indexer(books, intentions, mains, plans, evenements, personnages, plis=None):
    """Ce qui EXISTE, et sous quelle adresse. Une arete pointe ici ou pend."""
    noeuds = {}          # id -> {genre, ou, quoi}
    doubles = collections.Counter()

    def pose(ident, genre, ou, quoi, **proprietes):
        if not ident:
            return
        if ident in noeuds:
            n = noeuds[ident]
            genres = n.setdefault("genres", [n["genre"]])
            if genre not in genres:
                genres.append(genre)
                doubles[ident] += 1
            # Plusieurs sources peuvent décrire le même nœud (une personne
            # paraît dans intentions puis personnages). On enrichit la
            # projection sans écraser une valeur déjà connue par du vide.
            n.update({k: v for k, v in proprietes.items() if v is not None})
            if genre == "personne" and ou == "personnages":
                # L'intention a créé l'adresse la première, mais l'étiquette
                # d'une personne reste son nom ; son intention vit sur les
                # étapes reliées, pas à la place de son identité.
                n["ou"], n["quoi"] = ou, nu(quoi)[:70]
            return
        noeuds[ident] = {"genre": genre, "ou": ou, "quoi": nu(quoi)[:70]}
        noeuds[ident].update({k: v for k, v in proprietes.items()
                             if v is not None})

    for l in books:
        lid = l.get("id")
        for titre, C, lignes in grilles(l):
            for r in lignes:
                d = dict(zip(C, r.get("cellules") or []))
                tete = nu((r.get("cellules") or [""])[0])
                if not tete:
                    continue
                m = PIECE.fullmatch(tete)
                if m:
                    genre = ("action" if "Action" in titre else
                             "clef" if "Clef" in titre else
                             "verrou" if "Verrou" in titre else
                             "etat_cible" if "cible" in titre else "piece")
                    pose(tete, genre, lid, col(d, "🏷️") or col(d, "L'action"),
                         lieu=col(d, "📍 Où") or col(d, "Où"),
                         etat=(col(d, "⏳ État") or col(d, "🔎 État")
                               or col(d, "⏳ Où ça en est")))
                elif MOYEN.fullmatch(tete):
                    # Les moyens sont un espace de noms PAR LIVRE : M01 vaut
                    # les voiles du Gosier chez la reine et la porte de la
                    # Gadoue chez Aurore. On qualifie, sinon on melange deux
                    # mondes sous une meme adresse.
                    pose(lid + ":" + tete, "moyen", lid, col(d, "🏷️"))
                elif OFFICE.fullmatch(tete):
                    pose(lid + ":" + tete, "office", lid, col(d, "🏷️"))

    for t in intentions:
        pid = t.get("personnage_id")
        pose("pers:" + str(pid), "personne", "intentions", t.get("intention"))
        for e in t.get("plan") or []:
            if e.get("id"):
                pose("etape:" + e["id"], "etape", pid, e.get("quoi"),
                     etat=e.get("etat"), jours_restants=e.get("jours_restants"),
                     cout=e.get("cout"), depend_de=e.get("depend_de"))

    for a in mains:
        aid = a.get("id")
        pose("main:" + str(aid), "compte", "mains", a.get("quoi"))
        for mes in a.get("mesure") or []:
            pose("{}.{}".format(aid, mes.get("id")), "mesure", aid,
                 mes.get("quoi"))

    for e in evenements:
        pose("ev:" + str(e.get("id")), "evenement", "evenements",
             e.get("description"))

    for p in plis or []:
        pose("pli:" + str(p.get("id")), "transmission", "plis",
             p.get("porte"))

    for p in personnages:
        if p.get("id"):
            pose("pers:" + p["id"], "personne", "personnages", p.get("nom"),
                 etat=p.get("etat"), condition=p.get("condition"),
                 lieu_id=p.get("lieu_id"))

    for lx in charger("lieux", []):
        if isinstance(lx, dict) and lx.get("id"):
            pose("lieu:" + lx["id"], "lieu", "lieux", lx.get("nom"),
                 jours_de_pr=lx.get("jours_de_pr"), region=lx.get("region"),
                 type_lieu=lx.get("type"))

    for e in ("scene", "orbite", "royaume"):
        pose("echelle:" + e, "echelle", "schema", e)
    pose("neant", "rien", "schema", "ce qui ne coute rien")
    pose("a_designer", "vacant", "schema", "aucun titulaire — case ouverte")
    for u in chiffrer.UNITES + chiffrer.MONNAIE:
        pose("unite:" + u, "unite", "schema", u)

    for pl in plans:
        for fam, genre in (("etats_cibles", "etat_cible"), ("verrous", "verrou"),
                           ("clefs", "clef"), ("actions", "action")):
            for x in pl.get(fam) or []:
                pose(x.get("id"), genre, "plan:" + pl["id"], x.get("quoi"))

    return noeuds, doubles


# ------------------------------------------------------------- les aretes
