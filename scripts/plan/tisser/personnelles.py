# -*- coding: utf-8 -*-
"""Projeter les affaires personnelles des habitants dans le tissu dérivé.

Les cahiers de ``chambres/<personne>/books`` ne font pas foi sur le monde,
mais ils font foi sur la liste de travail personnelle servie à leur siège.
Leurs codes courts (C.1, V.1, K.1, P.1) sont donc namespacés par personne et
par fichier : deux habitants peuvent posséder P.1 sans collision.
"""
import glob
import io
import json
import os
import re
import unicodedata


CODE = re.compile(r"\b([A-Z][A-Z0-9]*(?:\.\d+)+)\b")


def _plat(texte):
    texte = unicodedata.normalize("NFD", str(texte or ""))
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", texte.lower()).strip()


def _nu(texte):
    return re.sub(r"\*", "", str(texte or "")).strip()


def _colonne(d, *mots):
    for cle, valeur in d.items():
        cle_plate = _plat(cle)
        if any(mot in cle_plate for mot in mots):
            return str(valeur or "")
    return ""


def _genre(titre):
    titre = _plat(titre)
    if "action" in titre:
        return "action_personnelle"
    if "verrou" in titre:
        return "verrou_personnel"
    if "clef" in titre or "cle " in titre:
        return "clef_personnelle"
    if ("etat" in titre and ("cible" in titre or "vise" in titre)) \
            or "ce que je veux" in titre:
        return "etat_cible_personnel"
    return None


def _personnage(candidats, connus):
    for candidat in candidats:
        formes = (candidat, candidat.replace("_", "-"))
        for forme in formes:
            if forme in connus:
                return forme
    return None


def charger_affaires_personnelles(racine, personnages=()):
    """Charge les affaires au premier niveau des chambres, jamais les archives."""
    connus = {str(p.get("id")) for p in personnages or []
             if isinstance(p, dict) and p.get("id")}
    motif = os.path.join(racine, "chambres", "*", "books", "affaire-*.json")
    affaires = []
    for chemin in sorted(glob.glob(motif)):
        chambre = os.path.basename(os.path.dirname(os.path.dirname(chemin)))
        if chambre == "mj":
            continue
        with io.open(chemin, encoding="utf-8") as fichier:
            livre = json.load(fichier)
        if not isinstance(livre, dict) or livre.get("type") not in ("affaire", "plan"):
            continue
        suffixe = str(livre.get("id") or "")
        if suffixe.startswith("affaire-"):
            suffixe = suffixe[len("affaire-"):]
        pid = _personnage((chambre, suffixe), connus)
        if not pid:
            continue
        copie = dict(livre)
        copie["_personnage_id"] = pid
        copie["_cle_personnelle"] = os.path.splitext(os.path.basename(chemin))[0]
        copie["_chemin_chambre"] = chemin
        affaires.append(copie)
    return affaires


def id_affaire(livre):
    return "perso:{}:{}".format(livre["_personnage_id"],
                                 livre["_cle_personnelle"])


FAMILLE = {
    "etat_cible_personnel": "etat",
    "verrou_personnel": "verrou",
    "clef_personnelle": "clef",
    "action_personnelle": "action",
}


def id_piece(livre, code, genre):
    return "{}:{}:{}".format(id_affaire(livre), FAMILLE[genre], code)


def _index(livre, lignes):
    index = {}
    for genre, code, _d, _cellules in lignes:
        index.setdefault(code, {})[genre] = id_piece(livre, code, genre)
    return index


def _resoudre(index, reference, genres):
    candidats = index.get(reference) or {}
    for genre in genres:
        if genre in candidats:
            return candidats[genre]
    return next(iter(candidats.values()), None)


def _lignes(livre):
    for table in livre.get("tables") or []:
        genre = _genre(table.get("titre"))
        if not genre:
            continue
        colonnes = table.get("colonnes") or []
        for ligne in table.get("lignes") or []:
            cellules = ligne.get("cellules") if isinstance(ligne, dict) else ligne
            if not isinstance(cellules, list) or not cellules:
                continue
            codes = CODE.findall(_nu(cellules[0]))
            if codes:
                yield genre, codes[0], dict(zip(colonnes, cellules)), cellules


def noeuds_affaires_personnelles(affaires):
    noeuds = []
    adresses = set()
    for livre in affaires or []:
        affaire = id_affaire(livre)
        if affaire in adresses:
            raise ValueError("affaire personnelle dupliquée : %s" % affaire)
        adresses.add(affaire)
        noeuds.append({
            "id": affaire, "genre": "affaire_personnelle",
            "ou": "chambre:" + livre["_personnage_id"],
            "quoi": livre.get("titre") or livre.get("id"),
            "local": True, "autorite": "personnelle",
            "personnage_id": livre["_personnage_id"],
            "livre_id": livre.get("id"), "namespace": "personnel",
        })
        lignes = list(_lignes(livre))
        index = _index(livre, lignes)
        for genre, code, d, cellules in lignes:
            adresse = id_piece(livre, code, genre)
            if adresse in adresses:
                raise ValueError("pièce personnelle dupliquée : %s" % adresse)
            adresses.add(adresse)
            libelle = (_colonne(d, "l etat vise", "l etat cible", "le verrou",
                                "la clef", "l action", "action")
                       or (cellules[1] if len(cellules) > 1 else code))
            proprietes = {
                "id": adresse, "genre": genre,
                "ou": "chambre:{}:{}".format(livre["_personnage_id"],
                                               livre.get("id")),
                "quoi": libelle, "local": True,
                "autorite": "personnelle", "namespace": "personnel",
                "personnage_id": livre["_personnage_id"],
                "livre_id": livre.get("id"), "code_local": code,
                "etat": _colonne(d, "etat", "statut"),
                "jour_du": _colonne(d, "jour du", "jour du"),
            }
            if genre == "action_personnelle":
                proprietes["depend_de"] = []
                for ref in CODE.findall(_colonne(d, "depend")):
                    cible = _resoudre(index, ref, (
                        "action_personnelle", "clef_personnelle",
                        "verrou_personnel", "etat_cible_personnel"))
                    if cible:
                        proprietes["depend_de"].append(cible)
            noeuds.append(proprietes)
    return noeuds


def aretes_affaires_personnelles(affaires):
    aretes = []

    def arc(de, vers, nature, source, texte=""):
        aretes.append({
            "de": de, "vers": vers, "nature": nature, "source": source,
            "texte": _nu(texte)[:110], "flou": False, "local": True,
            "autorite": "personnelle",
        })

    for livre in affaires or []:
        pid = livre["_personnage_id"]
        personne, affaire = "pers:" + pid, id_affaire(livre)
        lignes = list(_lignes(livre))
        index = _index(livre, lignes)
        arc(personne, affaire, "porte", "chambres/personnelles/porteur",
            livre.get("id"))
        for genre, code, d, _cellules in lignes:
            piece = index[code][genre]
            arc(affaire, piece, "decoupe", "chambres/personnelles/contenu", code)
            if genre == "etat_cible_personnel":
                arc(personne, piece, "porte", "chambres/personnelles/buts", code)
            elif genre == "action_personnelle":
                arc(personne, piece, "tient", "chambres/personnelles/actions", code)

            relations = []
            if genre == "verrou_personnel":
                relations.append(("bloque", _colonne(d, "ce qu il bloque", "bloque")))
            elif genre == "clef_personnelle":
                relations.append(("ouvre", _colonne(d, "ouvre", "leve")))
            elif genre == "action_personnelle":
                relations.extend([
                    ("realise", _colonne(d, "realise", "etat vise", "objectif")),
                    ("depend_de", _colonne(d, "depend")),
                ])
            for nature, valeur in relations:
                for reference in CODE.findall(valeur):
                    priorites = {
                        "bloque": ("etat_cible_personnel",),
                        "ouvre": ("verrou_personnel",),
                        "realise": ("etat_cible_personnel", "clef_personnelle"),
                        "depend_de": ("action_personnelle", "clef_personnelle",
                                      "verrou_personnel", "etat_cible_personnel"),
                    }[nature]
                    cible = _resoudre(index, reference, priorites)
                    if cible and cible != piece:
                        arc(piece, cible, nature,
                            "chambres/personnelles/structure", valeur)
    return aretes
