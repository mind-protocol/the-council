# -*- coding: utf-8 -*-
"""Le plan visible d'un siege, normalise avant toute mesure ou presentation.

La frontiere n'est ni un prefixe d'identifiant, ni le nom d'un coffret : c'est
l'etagere que ce personnage peut effectivement ouvrir. Toutes les maisons
passent donc par la meme porte (`livre.etagere`). Parmi ces volumes visibles,
un cahier actif a une forme complete ; les autres volumes de plan sont des
brouillons explicites et ne contaminent pas le graphe mesure.

Lecture seule. Ce module n'ecrit jamais dans ``etat/``.
"""
import io
import json
import os
import re
import sys
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import couverture as C  # noqa: E402
import livre  # noqa: E402

FAIT = {"fait", "faite", "faits", "faites", "clos", "close", "closes", "termine", "terminee"}
BLOQUE = {"bloque", "bloquee", "suspendu", "suspendue", "abandonne", "abandonnee"}
EN_COURS = {"en cours", "engage", "engagee", "commence", "commencee"}
A_FAIRE = {"a faire", "pas fait", "pas faite", ""}
REF_ACTION = re.compile(r"\bactions?\s+([0-9]{3,5})\b", re.I)


def _sans_accent(texte):
    texte = C.sans_emoji(texte or u"").lower()
    return u"".join(c for c in unicodedata.normalize("NFD", texte)
                    if unicodedata.category(c) != "Mn")


def _tables_de(volume, genre):
    return [t for t in (volume.get("tables") or [])
            if C.genre_de((t or {}).get("titre") or u"") == genre]


def _ouverture(volume):
    return any(re.search(r"\bouverture\b", _sans_accent((t or {}).get("titre")), re.I)
               for t in (volume.get("tables") or []))


def _place(volume):
    return bool(volume.get("boite") or volume.get("acteur_id")
                or volume.get("lieu_id") or volume.get("salle_id"))


def est_volume_de_plan(volume):
    """Un candidat *affaire*, meme encore vide ou incomplet.

    ``type: plan`` couvre aussi des grilles privees et des cartes de travail.
    Une affaire se reconnait donc par son ouverture, par l'ancien prefixe qui
    permet de retrouver les brouillons sans ouverture, ou par au moins deux
    rangs du graphe causal. Ce dernier cas laisse une maison amorcer un cahier
    sans adopter le prefixe historique de Peyredragon.
    """
    volume = volume or {}
    if volume.get("type") != "plan":
        return False
    genres = {C.genre_de((t or {}).get("titre") or u"")
              for t in (volume.get("tables") or [])}
    rangs = genres & {"etat", "verrou", "clef", "action"}
    return (_ouverture(volume)
            or str(volume.get("id") or u"").startswith("affaire-")
            or len(rangs) >= 2)


def raisons_brouillon(volume):
    raisons = []
    if not _place(volume):
        raisons.append("sans place")
    if not _ouverture(volume):
        raisons.append("sans ouverture")
    if not _tables_de(volume, "etat"):
        raisons.append("sans table d'etats cibles")
    elif not any((t.get("lignes") or []) for t in _tables_de(volume, "etat")):
        raisons.append("sans etat cible")
    return raisons


def est_affaire_active(volume):
    return est_volume_de_plan(volume) and not raisons_brouillon(volume)


def personnage_par_defaut():
    try:
        with io.open(os.path.join(ETAT, "journal.json"), encoding="utf-8") as f:
            return (json.load(f) or {}).get("personnage_joueur_id")
    except (OSError, ValueError, TypeError):
        return None


def construire_depuis_livres(livres, vue_de=None):
    """Construit la vue canonique depuis une etagere deja autorisee."""
    visibles = list(livres or [])
    candidats = [b for b in visibles if est_volume_de_plan(b)]
    actifs = [b for b in candidats if est_affaire_active(b)]
    brouillons = [{"id": b.get("id"), "titre": b.get("titre") or b.get("id"),
                   "raisons": raisons_brouillon(b)}
                  for b in candidats if b not in actifs]

    # Le parseur voit toute l'etagere autorisee pour retrouver les registres de
    # moyens et d'offices. Le graphe actif, lui, ne garde que les pieces qu'un
    # cahier actif revendique par son titre. Une ligne de brouillon ou un index
    # sans cahier devient un diagnostic, jamais une piece active par accident.
    ids_actifs = {b.get("id") for b in actifs}
    # Les brouillons restent visibles au diagnostic mais leurs lignes ne
    # doivent pas gagner une collision ou un état dans le graphe actif.
    lecture = [b for b in visibles
               if b.get("id") in ids_actifs or not est_volume_de_plan(b)]
    _lus, pieces_lues, inventaire, _affaires_lues = C.charger(lecture)
    titres = {C.nu(b.get("titre")) for b in actifs}
    pieces = {n: p for n, p in pieces_lues.items() if p.get("affaire") in titres}

    collisions = []
    for n, p in pieces.items():
        sources = p.get("cahier_sources") or []
        uniques = {(s.get("volume_id"), s.get("table"), s.get("genre"), s.get("nom"))
                   for s in sources}
        if len(uniques) > 1:
            collisions.append({"numero": n, "sources": sources})

    lier_preuves(pieces)

    hors_affaire = sorted(n for n, p in pieces_lues.items()
                         if p.get("genre") in ("etat", "verrou", "clef", "action")
                         and not p.get("affaire"))
    return {
        "vue_de": vue_de,
        "livres": visibles,
        "affaires": actifs,
        "pieces": pieces,
        "inventaire": inventaire,
        "brouillons": brouillons,
        "pieces_hors_affaire": hors_affaire,
        "collisions": collisions,
    }


def _charger_json(nom):
    try:
        with io.open(os.path.join(ETAT, nom), encoding="utf-8") as f:
            return json.load(f) or []
    except (OSError, ValueError, TypeError):
        return []


def _texte_registre(entree):
    return u" ".join(str(entree.get(k) or u"")
                     for k in ("description", "quoi", "texte"))


def lier_preuves(pieces, actes=None, evenements=None):
    """Rattache les preuves canoniques qui citent explicitement une action.

    Le lien est volontairement strict : un nombre n'est une adresse du plan
    que si le registre dit ``action 22042``. Une ressemblance de prose ne vaut
    jamais preuve. L'absence de lien signifie « non rattaché », pas « faux ».
    """
    actes = _charger_json("actes.json") if actes is None else actes
    evenements = _charger_json("evenements.json") if evenements is None else evenements
    index = {}
    registres = [("actes", x) for x in actes]
    registres += [("evenements", x) for x in evenements if x.get("statut") == "resolu"]
    for registre, entree in registres:
        for n in set(REF_ACTION.findall(_texte_registre(entree))):
            index.setdefault(n, []).append({
                "registre": registre,
                "id": entree.get("id"),
                "date": entree.get("date") or entree.get("date_prevue"),
            })
    for n, p in pieces.items():
        if p.get("genre") == "action":
            p["preuves_canoniques"] = index.get(n, [])
    return index


def statut_declare(piece):
    brut = _sans_accent(piece.get("etat")).strip()
    mot = C.premier_mot(brut)
    if mot in FAIT:
        return "fait"
    if mot in BLOQUE or any(brut.startswith(x) for x in BLOQUE):
        return "bloque"
    if any(brut.startswith(x) for x in EN_COURS):
        return "en-cours"
    if brut in A_FAIRE or any(brut.startswith(x) for x in A_FAIRE if x):
        return "a-faire"
    return "inconnu"


def mesures(modele):
    pieces = modele.get("pieces") or {}
    genres = {g: 0 for g in ("etat", "verrou", "clef", "action")}
    for p in pieces.values():
        if p.get("genre") in genres:
            genres[p["genre"]] += 1
    actions = [p for p in pieces.values() if p.get("genre") == "action"]
    declaration = {k: 0 for k in ("fait", "en-cours", "bloque", "a-faire", "inconnu")}
    for p in actions:
        declaration[statut_declare(p)] += 1
    faites = [p for p in actions if statut_declare(p) == "fait"]
    preuves_documentees = sum(1 for p in faites
                              if (p.get("preuve") or u"").strip() not in (u"", u"—", u"-") )
    preuves_rattachees = sum(1 for p in faites if p.get("preuves_canoniques"))
    return {
        "structure": {
            "affaires_actives": len(modele.get("affaires") or []),
            "brouillons": len(modele.get("brouillons") or []),
            "collisions": len(modele.get("collisions") or []),
            "pieces_hors_affaire": len(modele.get("pieces_hors_affaire") or []),
            "genres": genres,
        },
        "declaration": {"actions": len(actions), **declaration},
        "preuves": {
            "actions_declarees_faites": len(faites),
            "preuve_documentee_dans_le_cahier": preuves_documentees,
            "preuve_rattachee_a_un_registre_canonique": preuves_rattachees,
        },
    }


def charger(vue_de=None):
    qui = vue_de or personnage_par_defaut()
    if not qui:
        raise ValueError("aucun personnage de vue; passer vue_de explicitement")
    return construire_depuis_livres(livre.etagere(qui), qui)


def resume(modele):
    return {
        "vue_de": modele.get("vue_de"),
        "affaires": len(modele.get("affaires") or []),
        "affaires_ids": [b.get("id") for b in (modele.get("affaires") or [])],
        "volumes_ids": [b.get("id") for b in (modele.get("livres") or [])],
        "pieces": len(modele.get("pieces") or {}),
        "brouillons": modele.get("brouillons") or [],
        "pieces_hors_affaire": modele.get("pieces_hors_affaire") or [],
        "collisions": modele.get("collisions") or [],
        "mesures": mesures(modele),
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vue-de", default=personnage_par_defaut())
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    m = charger(args.vue_de)
    r = resume(m)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(u"PLAN VISIBLE DE %s — %d affaire(s), %d piece(s), %d brouillon(s)"
              % (r["vue_de"], r["affaires"], r["pieces"], len(r["brouillons"])))
        for b in r["brouillons"]:
            print(u"  - %s : %s" % (b["titre"], u", ".join(b["raisons"])))
