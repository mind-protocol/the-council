#!/usr/bin/env python3
"""Importer en lot les citoyens Serenissima et les placer dans Braavos.

Seules les chambres portant le fichier sentinelle vide ``serenissima`` sont
considerees. Leurs fiches ``CLAUDE.md`` restent les sources immuables. Les ids
sont normalises en kebab-case, les anciennes latitude/longitude servent a
distribuer les corps, puis chaque point est contraint au contour d'une salle de
Braavos.
"""

import argparse
import hashlib
import json
import math
import os as _os
import re
import sys as _sys
from collections import Counter, defaultdict

# Le chemin des freres : scripts/ et scripts/noyau/.
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import tables
import serenissima


RACINE = _os.path.dirname(_d)
CHAMBRES = _os.path.join(RACINE, "chambres")
INTERIEURS = _os.path.join(RACINE, "monde", "braavos.interieurs.json")
EXCLUS = {"divine-economist"}  # importe separement, avec sa propre maison
MARQUEUR = "serenissima"

CLASSES = {
    "Popolani": "Habitant de Braavos",
    "Forestieri": "Voyageur établi à Braavos",
    "Nobili": "Notable braavien",
    "Cittadini": "Citoyen de Braavos",
    "Facchini": "Travailleur de Braavos",
    "Clero": "Clerc de Braavos",
    "Innovatori": "Inventeur de Braavos",
    "Ambasciatore": "Ambassadeur à Braavos",
    "Scientisti": "Savant de Braavos",
    "Artisti": "Artiste de Braavos",
}

MANIERES = {
    "Clero": "Parle avec gravité, part d'un geste concret et revient à ce qu'il engage dans l'âme.",
    "Nobili": "Parle avec l'assurance de qui s'attend à être écouté, mais choisit soigneusement ce qu'il engage.",
    "Ambasciatore": "Pèse chaque mot, distingue le fait de la position officielle et laisse toujours une porte ouverte.",
    "Scientisti": "Décompose les problèmes, demande des observations et corrige volontiers une conclusion trop rapide.",
    "Innovatori": "Parle par mécanismes, prototypes et conséquences pratiques, avec peu de patience pour les usages morts.",
    "Artisti": "Parle par images précises et cherche ce que les formes révèlent avant ce qu'elles décorent.",
    "Forestieri": "Parle en comparant les ports, les coutumes et les prix, attentif à ce qui trahit l'étranger.",
    "Cittadini": "Parle en personne habituée aux contrats, aux métiers et aux équilibres de la cité.",
    "Facchini": "Parle directement, compte l'effort réel et se méfie des ordres qui oublient le poids des choses.",
    "Popolani": "Parle sans cérémonie, depuis ce qu'il a vu, payé ou porté lui-même.",
}


def slug(texte):
    return re.sub(r"[^a-z0-9]+", "-", str(texte).lower()).strip("-")


def charger_json(chemin):
    with open(chemin, encoding="utf-8") as fichier:
        return json.load(fichier)


def frontmatter(chemin):
    with open(chemin, encoding="utf-8-sig", errors="replace") as fichier:
        texte = fichier.read()
    morceaux = texte.split("---", 2)
    if len(morceaux) < 3:
        return None
    champs = {}
    for ligne in morceaux[1].splitlines():
        trouve = re.match(r"^([A-Za-z_]+):\s*(.*)$", ligne)
        if not trouve:
            continue
        cle, brut = trouve.groups()
        try:
            champs[cle] = json.loads(brut)
        except json.JSONDecodeError:
            champs[cle] = brut.strip().strip('"')
    if not champs.get("CitizenId"):
        return None
    position = champs.get("Position", {})
    if isinstance(position, str):
        try:
            position = json.loads(position)
        except json.JSONDecodeError:
            position = {}
    champs["_position"] = position if isinstance(position, dict) else {}
    champs["_dossier"] = _os.path.basename(_os.path.dirname(chemin))
    return champs


def citoyens():
    trouves = []
    for dossier in sorted(_os.listdir(CHAMBRES), key=str.lower):
        marqueur = _os.path.join(CHAMBRES, dossier, MARQUEUR)
        if not _os.path.isfile(marqueur):
            continue
        if _os.path.getsize(marqueur) != 0:
            raise ValueError("Le marqueur doit etre vide : " + marqueur)
        chemin = _os.path.join(CHAMBRES, dossier, "CLAUDE.md")
        if not _os.path.isfile(chemin):
            continue
        fiche = frontmatter(chemin)
        if not fiche:
            continue
        fiche["_id"] = slug(fiche["CitizenId"])
        if fiche["_id"] not in EXCLUS:
            trouves.append(fiche)
    ids = [fiche["_id"] for fiche in trouves]
    doubles = [ident for ident, n in Counter(ids).items() if n > 1]
    if doubles:
        raise ValueError("Ids normalises en double : " + ", ".join(doubles))
    return trouves


def choisir_salle(fiche):
    identite = " ".join((fiche.get("CitizenId", ""), fiche.get("Username", ""),
                          fiche.get("_dossier", ""))).lower()
    classe = fiche.get("SocialClass", "")
    regles = [
        (("priest", "preacher", "clero", "sacred", "canon", "divine"), "septuaire"),
        (("captain", "mariner", "sailor", "navigator", "gondola", "adriatic",
          "aegean", "ionian", "istrian", "ligurian", "sea_"), "quai"),
        (("anchor", "builder", "architect", "stone", "glass", "mechanical"), "forge"),
        (("anatom", "diagnostic", "transmut", "experiment", "pattern", "system_"), "officine"),
        (("book", "chronicler", "diarist", "critic", "observer", "scholar"), "archives"),
        (("food", "coffee", "tavern", "kneader"), "cuisines"),
        (("painter", "poet", "photo", "beauty", "canvas", "rhythm"), "jardin-aegon"),
        (("bank", "invest", "econom", "wealth", "merchant", "trader"), "bourg"),
        (("doge", "consiglio", "diplomat", "ambassador"), "table-peinte"),
    ]
    for mots, salle in regles:
        if any(mot in identite for mot in mots):
            return "braavos-" + salle
    salle = {
        "Clero": "septuaire",
        "Nobili": "grande-salle",
        "Ambasciatore": "table-peinte",
        "Scientisti": "officine",
        "Innovatori": "forge",
        "Artisti": "jardin-aegon",
        "Forestieri": "chambres-hotes",
        "Cittadini": "archives",
        "Facchini": "baraques",
        "Popolani": "bourg",
    }.get(classe, "communs")
    return "braavos-" + salle


def dans_polygone(x, y, contour):
    dedans = False
    precedent = contour[-1]
    for courant in contour:
        x1, y1 = precedent
        x2, y2 = courant
        if ((y1 > y) != (y2 > y)) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            dedans = not dedans
        precedent = courant
    return dedans


def distance_portes(x, y, salle):
    return min((math.hypot(x - p["x"], y - p["y"]) for p in salle.get("portes", [])),
               default=999.0)


def positionner(fiche, salle, index, bornes_geo, deja):
    contour = salle["contour"]
    xs = [p[0] for p in contour]
    ys = [p[1] for p in contour]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    lat0, lat1, lng0, lng1 = bornes_geo
    pos = fiche.get("_position", {})
    lat, lng = pos.get("lat"), pos.get("lng")
    germe = int.from_bytes(hashlib.sha256(fiche["_id"].encode("utf-8")).digest()[:8], "big")
    u = ((lng - lng0) / (lng1 - lng0)) if isinstance(lng, (int, float)) and lng1 > lng0 else ((germe & 0xffff) / 65535)
    v = ((lat - lat0) / (lat1 - lat0)) if isinstance(lat, (int, float)) and lat1 > lat0 else (((germe >> 16) & 0xffff) / 65535)
    u = 0.15 + 0.70 * max(0.0, min(1.0, u))
    v = 0.15 + 0.70 * max(0.0, min(1.0, v))
    candidats = [(minx + u * (maxx - minx), miny + v * (maxy - miny))]
    cx, cy, z = salle["centre"]
    angle0 = (germe % 100000) / 100000 * math.tau
    rayon_max = max(1.0, min(maxx - minx, maxy - miny) * 0.38)
    for essai in range(1, 240):
        angle = angle0 + essai * 2.399963229728653
        rayon = min(rayon_max, 0.7 + 0.52 * math.sqrt(index + essai))
        candidats.append((cx + math.cos(angle) * rayon, cy + math.sin(angle) * rayon))
    # Les salles longues ou concaves offrent parfois peu de place autour de
    # leur centre. Une seconde passe balaie deterministement toute leur boite.
    for essai in range(240, 1240):
        digest = hashlib.sha256((fiche["_id"] + ":" + str(essai)).encode("utf-8")).digest()
        ru = int.from_bytes(digest[:4], "big") / 4294967295
        rv = int.from_bytes(digest[4:8], "big") / 4294967295
        candidats.append((minx + (0.05 + 0.90 * ru) * (maxx - minx),
                           miny + (0.05 + 0.90 * rv) * (maxy - miny)))
    for x, y in candidats:
        if not dans_polygone(x, y, contour) or distance_portes(x, y, salle) < 1.2:
            continue
        if all(math.hypot(x - ox, y - oy) >= 0.45 for ox, oy in deja):
            deja.append((x, y))
            return [round(x, 2), round(y, 2), float(z)]
    raise ValueError("Aucune place libre dans %s pour %s" % (salle["id"], fiche["_id"]))


def objets(fiche, salle_id, xyz):
    ident = fiche["_id"]
    prenom = str(fiche.get("FirstName", "")).strip()
    nom_famille = str(fiche.get("LastName", "")).strip()
    nom = (prenom + " " + nom_famille).strip() or str(fiche.get("Username") or fiche["CitizenId"])
    classe = str(fiche.get("SocialClass", ""))
    position = fiche.get("_position", {})
    source = fiche.get("airtable_record_id", "inconnu")
    note = ("Importe de Serenissima depuis chambres/%s/CLAUDE.md (Airtable %s) ; "
            "position d'origine lat %s, lng %s, reprojetee dans %s a Braavos."
            % (fiche["_dossier"], source, position.get("lat", "?"),
               position.get("lng", "?"), salle_id))
    personnage = {
        "id": ident,
        "nom": nom,
        "maison_id": "maison-serenissima",
        "titre": CLASSES.get(classe, (classe + " de Braavos").strip()),
        "naissance": None,
        "traits": [classe.lower()] if classe else [],
        "objectifs": [],
        "maniere": MANIERES.get(classe, "Parle depuis son métier et ce qu'il a vu lui-même."),
        "etat": "dormant",
        "lieu_id": "braavos",
        "condition": "libre",
        "canon": False,
        "note": note,
    }
    corps = {
        "personnage_id": ident,
        "bat": None,
        "usage": salle_id,
        "quartier": "Braavos",
        "role": CLASSES.get(classe, classe or "Habitant de Braavos"),
        "x": xyz[0], "y": xyz[1], "z": xyz[2],
        "monde": "braavos",
    }
    affectation = {"xyz": xyz, "monde": "braavos", "note": note}
    return personnage, corps, affectation


def preparer():
    fiches = citoyens()
    interieurs = charger_json(INTERIEURS)
    salles = {s["id"]: s for s in interieurs.get("salles", [])}
    affectees = defaultdict(list)
    for fiche in fiches:
        salle_id = choisir_salle(fiche)
        if salle_id not in salles:
            raise ValueError("Salle inconnue : " + salle_id)
        affectees[salle_id].append(fiche)
    positions = [f.get("_position", {}) for f in fiches]
    lats = [p["lat"] for p in positions if isinstance(p.get("lat"), (int, float))]
    lngs = [p["lng"] for p in positions if isinstance(p.get("lng"), (int, float))]
    bornes = (min(lats), max(lats), min(lngs), max(lngs))
    resultat = []
    for salle_id, groupe in sorted(affectees.items()):
        occupees = []
        for index, fiche in enumerate(sorted(groupe, key=lambda f: f["_id"])):
            xyz = positionner(fiche, salles[salle_id], index, bornes, occupees)
            resultat.append((fiche, salle_id, xyz, *objets(fiche, salle_id, xyz)))
    return resultat, salles


def upsert(liste, cle, valeurs):
    ids = {v[cle] for v in valeurs}
    liste[:] = [v for v in liste if v.get(cle) not in ids]
    liste.extend(valeurs)


def personnage_importe_compatible(actuel, attendu):
    """L'import pose une naissance ; le monde a ensuite le droit de l'eveiller.

    ``etat`` est le seul champ de cycle de vie que cet importeur ne possede
    plus apres la premiere ecriture. Tous les autres champs restent verifies
    exactement : autoriser un reveil ne doit pas masquer une derive d'identite.
    """
    if not isinstance(actuel, dict):
        return False
    if actuel.get("etat") not in {"dormant", "actif"}:
        return False
    return all(actuel.get(cle) == valeur for cle, valeur in attendu.items()
               if cle != "etat")


def verifier(resultat, salles):
    personnages = {p.get("id"): p for p in tables.lire("personnages")}
    corps_table = tables.lire("corps")
    corps = {c.get("personnage_id"): c for c in corps_table.get("corps", [])}
    routines = tables.lire("routines")
    erreurs = []
    for fiche, salle_id, xyz, personnage, corps_attendu, affectation in resultat:
        ident = fiche["_id"]
        if not personnage_importe_compatible(personnages.get(ident), personnage):
            erreurs.append(ident + ":personnage")
        if corps.get(ident) != corps_attendu:
            erreurs.append(ident + ":corps")
        if corps_table.get("affectations", {}).get("personnage:" + ident) != affectation:
            erreurs.append(ident + ":affectation")
        if routines.get("gens", {}).get(ident) != {"modele": "citoyens-" + salle_id}:
            erreurs.append(ident + ":routine")
        if not dans_polygone(xyz[0], xyz[1], salles[salle_id]["contour"]):
            erreurs.append(ident + ":hors-salle")
    if erreurs:
        raise SystemExit("Import incomplet : " + ", ".join(erreurs[:20]))
    repartition = Counter(salle for _, salle, *_ in resultat)
    print("OK %d citoyens places dans %d salles de Braavos" % (len(resultat), len(repartition)))
    for salle, compte in sorted(repartition.items()):
        print("  %-20s %3d" % (salle, compte))


def main():
    analyseur = argparse.ArgumentParser()
    analyseur.add_argument("--verifier", action="store_true", help="ne rien ecrire")
    args = analyseur.parse_args()
    nombre_manuels, changements = serenissima.synchroniser(CHAMBRES, verifier=args.verifier)
    if not args.verifier:
        print("%d manuels Serenissima synchronises (%d modifies)" %
              (nombre_manuels, changements))
    resultat, salles = preparer()
    if not args.verifier:
        personnages = tables.lire("personnages")
        corps_table = tables.lire("corps")
        routines = tables.lire("routines")
        etats_existants = {p.get("id"): p.get("etat") for p in personnages
                           if p.get("etat") in {"dormant", "actif"}}
        personnages_importes = [r[3] for r in resultat]
        for personnage in personnages_importes:
            if personnage["id"] in etats_existants:
                personnage["etat"] = etats_existants[personnage["id"]]
        upsert(personnages, "id", personnages_importes)
        upsert(corps_table.setdefault("corps", []), "personnage_id", [r[4] for r in resultat])
        for fiche, salle_id, xyz, personnage, corps, affectation in resultat:
            ident = fiche["_id"]
            corps_table.setdefault("affectations", {})["personnage:" + ident] = affectation
            routines.setdefault("gens", {})[ident] = {"modele": "citoyens-" + salle_id}
        for salle_id in sorted({r[1] for r in resultat}):
            routines.setdefault("modeles", {})["citoyens-" + salle_id] = {
                "nom": "Le jour des citoyens de Braavos — " + salles[salle_id]["nom"],
                "dortoir": {"salle": salle_id, "lieu": salles[salle_id]["nom"] + ", Braavos"},
                "bandes": [{"de": 0, "a": 1440, "salle": salle_id,
                             "lieu": salles[salle_id]["nom"] + ", Braavos"}],
            }
        tables.ecrire("personnages", personnages)
        tables.ecrire("corps", corps_table)
        tables.ecrire("routines", routines)
    verifier(resultat, salles)


if __name__ == "__main__":
    main()
