# -*- coding: utf-8 -*-
"""Extraire le sous-graphe causal amont d'un événement, ou de tous.

Le tissu brut mélange plusieurs sens : ``A depend_de B`` est écrit A -> B,
mais causalement B précède A. Cette lecture normalise chaque nature avant de
parcourir l'amont et rend les absences comme des trous typés, jamais comme des
arêtes inventées.
"""
import argparse
import collections
import hashlib
import io
import json
import os
import re
import sys
import unicodedata


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TISSU = os.path.join(RACINE, "etat", "tissu")
COMPLEMENTS = os.path.join(RACINE, "chambres", "mj",
                           "graphe-causal-complements.json")


# True : l'arête brute doit être retournée pour exprimer cause -> conséquence.
NATURES = {
    "amont": (False, "cause"),
    "realise": (False, "production"),
    "sert": (False, "soutien"),
    "ouvre": (False, "leve_verrou"),
    "bloque": (False, "obstacle"),
    "depend_de": (True, "prerequis"),
    "attend": (True, "prerequis_attendu"),
    "devie": (False, "condition_deviation"),
}


def _lire_json(chemin):
    with io.open(chemin, encoding="utf-8") as fichier:
        return json.load(fichier)


def _lire_jsonl(chemin):
    resultat = []
    with io.open(chemin, encoding="utf-8") as fichier:
        for ligne in fichier:
            if ligne.strip():
                resultat.append(json.loads(ligne))
    return resultat


def _charger_complements(racine=RACINE):
    chemin = os.path.join(racine, "chambres", "mj",
                          "graphe-causal-complements.json")
    if not os.path.exists(chemin):
        return {"noeuds": {}, "aretes": []}
    donnees = _lire_json(chemin)
    if not isinstance(donnees, dict):
        raise ValueError("compléments causaux invalides : objet JSON attendu")
    return {
        "noeuds": donnees.get("noeuds") or {},
        "aretes": donnees.get("aretes") or [],
    }


def charger_tissu(racine=RACINE):
    dossier = os.path.join(racine, "etat", "tissu")
    noeuds = _lire_json(os.path.join(dossier, "noeuds.json"))
    aretes = _lire_jsonl(os.path.join(dossier, "aretes.jsonl"))
    complements = _charger_complements(racine)
    doubles = set(noeuds).intersection(complements["noeuds"])
    if doubles:
        raise ValueError("nœuds causaux déjà présents dans le tissu : %s" %
                         ", ".join(sorted(doubles)[:5]))
    noeuds.update(complements["noeuds"])
    aretes.extend(complements["aretes"])
    return noeuds, aretes


def _id_trou(type_, evenement, texte, source):
    matiere = "\x1f".join(str(x or "") for x in
                           (type_, evenement, texte, source))
    empreinte = hashlib.sha1(matiere.encode("utf-8")).hexdigest()[:12]
    return "trou:{}:{}".format(type_.replace("_", "-"), empreinte)


def _trou(type_, evenement, texte, source, **details):
    t = {"id": _id_trou(type_, evenement, texte, source),
         "type": type_, "event": evenement, "texte": texte,
         "source": source}
    t.update({k: v for k, v in details.items() if v is not None})
    return t


def normaliser(noeuds, aretes):
    """Rend les arêtes cause->conséquence et les trous déjà observables."""
    sorties = []
    trous = collections.defaultdict(list)
    resolus = {a.get("resout_trou") for a in aretes if a.get("resout_trou")}
    for rang, brute in enumerate(aretes):
        nature = brute.get("nature")
        if nature not in NATURES:
            continue
        inverse, type_lien = NATURES[nature]
        brut_de, brut_vers = brute.get("de"), brute.get("vers")

        # Une condition en prose est connue, mais elle n'a aucun nœud. La
        # transformer en cause ferait précisément disparaître le trou.
        if nature == "devie" and (brute.get("flou") or brut_de == "?"):
            if brut_vers in noeuds and noeuds[brut_vers].get("genre") == "evenement":
                trou = _trou(
                    "condition_non_adressee", brut_vers,
                    brute.get("texte") or "condition sans adresse",
                    brute.get("source"), nature=nature, rang_arete=rang,
                    attendu="un nœud ou un événement portant cette condition")
                if trou["id"] not in resolus:
                    trous[brut_vers].append(trou)
            continue

        de, vers = ((brut_vers, brut_de) if inverse else (brut_de, brut_vers))
        absents = [x for x in (de, vers) if not x or x == "?" or x not in noeuds]
        if absents:
            cible = vers if vers in noeuds else (brut_vers if brut_vers in noeuds else None)
            if cible and noeuds[cible].get("genre") == "evenement":
                trous[cible].append(_trou(
                    "extremite_absente", cible,
                    brute.get("texte") or "arête causale sans ses deux extrémités",
                    brute.get("source"), nature=nature, absentes=absents,
                    attendu="une adresse résolue pour chaque extrémité"))
            continue

        edge = {
            "de": de,
            "vers": vers,
            "nature": nature,
            "type": type_lien,
            "source": brute.get("source"),
            "texte": brute.get("texte") or "",
            "sens_brut": {"de": brut_de, "vers": brut_vers},
        }
        for cle in ("epistemique", "conditionnel", "justification", "date"):
            if brute.get(cle) is not None:
                edge[cle] = brute[cle]
        sorties.append(edge)

        epistemique = str(brute.get("epistemique") or "").lower()
        if "inf" in epistemique:  # inférence / infere, accents ou non
            trous[vers].append(_trou(
                "inference_a_confirmer", vers,
                brute.get("texte") or "lien causal inféré",
                brute.get("source"), de=de, nature=nature,
                attendu="une preuve explicite ou le maintien assumé comme inférence"))
    return sorties, trous


def _slug(texte, limite=52):
    plat = unicodedata.normalize("NFD", str(texte or ""))
    plat = "".join(c for c in plat if unicodedata.category(c) != "Mn")
    plat = re.sub(r"[^a-z0-9]+", "-", plat.lower()).strip("-")
    return (plat[:limite].rstrip("-") or "sans-libelle")


def proposer_complements(graphes, noeuds):
    """Traduit les trous observés en nœuds explicites, sans deviner de cause."""
    par_id = {}
    for graphe in graphes:
        for trou in graphe.get("trous") or []:
            par_id.setdefault(trou["id"], trou)

    nouveaux_noeuds, nouvelles_aretes = {}, []
    for trou in sorted(par_id.values(), key=lambda t: t["id"]):
        evenement = trou["event"]
        suffixe = trou["id"].rsplit(":", 1)[-1]
        if trou["type"] == "condition_non_adressee":
            ident = "condition:{}:{}-{}".format(
                evenement[3:] if evenement.startswith("ev:") else evenement,
                _slug(trou["texte"]), suffixe[:8])
            nouveaux_noeuds[ident] = {
                "genre": "condition_causale",
                "ou": "chambres/mj/graphe-causal-complements",
                "quoi": trou["texte"],
                "source": trou.get("source"),
                "statut": "a_evaluer",
            }
            nouvelles_aretes.append({
                "de": ident, "vers": evenement, "nature": "devie",
                "source": "chambres/mj/graphe-causal-complements",
                "flou": False, "texte": trou["texte"],
                "resout_trou": trou["id"], "conditionnel": True,
            })
        elif trou["type"] in ("cause_absente", "evenement_isole"):
            ident = "racine:{}".format(
                evenement[3:] if evenement.startswith("ev:") else evenement)
            description = (noeuds.get(evenement) or {}).get("quoi") or evenement
            nouveaux_noeuds[ident] = {
                "genre": "racine_causale",
                "ou": "chambres/mj/graphe-causal-complements",
                "quoi": "Point de départ déclaré : " + description,
                "statut": "aucun_antecedent_encode",
            }
            nouvelles_aretes.append({
                "de": ident, "vers": evenement, "nature": "amont",
                "source": "chambres/mj/graphe-causal-complements",
                "flou": False,
                "texte": "Racine déclarée — aucun antécédent causal encodé",
                "resout_trou": trou["id"], "racine_declaree": True,
            })
    return {"noeuds": nouveaux_noeuds, "aretes": nouvelles_aretes}


def ecrire_complements(complements, chemin=COMPLEMENTS):
    dossier = os.path.dirname(chemin)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    existants = {"noeuds": {}, "aretes": []}
    if os.path.exists(chemin):
        donnees = _lire_json(chemin)
        existants = {
            "noeuds": donnees.get("noeuds") or {},
            "aretes": donnees.get("aretes") or [],
        }
    noeuds = dict(existants["noeuds"])
    noeuds.update(complements["noeuds"])
    aretes, vues = [], set()
    for arete in existants["aretes"] + complements["aretes"]:
        cle = (arete.get("resout_trou"), arete.get("de"),
               arete.get("vers"), arete.get("nature"))
        if cle not in vues:
            vues.add(cle)
            aretes.append(arete)
    rendu = {
        "schema": "graphe-causal-complements/1",
        "_note": ("Compléments explicites produits par graphe_causal.py. "
                  "Une racine déclare l'absence d'antécédent encodé ; "
                  "elle n'invente pas une cause."),
        "noeuds": noeuds,
        "aretes": aretes,
    }
    with io.open(chemin, "w", encoding="utf-8", newline="\n") as fichier:
        json.dump(rendu, fichier, ensure_ascii=False, indent=2)
        fichier.write("\n")
    return chemin


def _dedoublonner_trous(trous):
    vus, resultat = set(), []
    for trou in trous:
        cle = json.dumps(trou, ensure_ascii=False, sort_keys=True)
        if cle not in vus:
            vus.add(cle)
            resultat.append(trou)
    return resultat


def extraire(event, noeuds, aretes):
    cible = event if str(event).startswith("ev:") else "ev:" + str(event)
    if cible not in noeuds or noeuds[cible].get("genre") != "evenement":
        raise ValueError("événement inconnu : %s" % event)

    causales, trous_directs = normaliser(noeuds, aretes)
    entrantes = collections.defaultdict(list)
    sortantes = collections.defaultdict(list)
    for edge in causales:
        entrantes[edge["vers"]].append(edge)
        sortantes[edge["de"]].append(edge)

    visites, retenues, pile = set(), [], [(cible, 0)]
    profondeur = 0
    while pile:
        noeud, niveau = pile.pop()
        profondeur = max(profondeur, niveau)
        if noeud in visites:
            continue
        visites.add(noeud)
        for edge in entrantes.get(noeud, []):
            retenues.append(edge)
            pile.append((edge["de"], niveau + 1))

    trous = []
    for ident in sorted(visites):
        trous.extend(trous_directs.get(ident, []))
        if noeuds[ident].get("genre") != "evenement":
            continue
        amont = entrantes.get(ident, [])
        if not amont:
            type_ = "evenement_isole" if not sortantes.get(ident) else "cause_absente"
            trous.append(_trou(
                type_, ident,
                "aucune cause adressée ne mène à cet événement",
                "graphe-causal", attendu="au moins une cause explicite, un prérequis ou une racine déclarée"))

    # Une même arête peut être rencontrée par deux branches qui se rejoignent.
    uniques, edges_vues = [], set()
    for edge in retenues:
        cle = (edge["de"], edge["vers"], edge["nature"], edge.get("source"))
        if cle not in edges_vues:
            edges_vues.add(cle)
            uniques.append(edge)
    trous = _dedoublonner_trous(trous)
    natures = collections.Counter(e["type"] for e in uniques)
    types_trous = collections.Counter(t["type"] for t in trous)

    return {
        "event": cible,
        "complet": not trous,
        "noeuds": [dict({"id": ident}, **noeuds[ident])
                    for ident in sorted(visites)],
        "aretes": sorted(uniques, key=lambda e: (e["vers"], e["de"], e["nature"])),
        "trous": trous,
        "stats": {
            "noeuds": len(visites),
            "aretes": len(uniques),
            "profondeur_max": profondeur,
            "liens_par_type": dict(sorted(natures.items())),
            "trous_par_type": dict(sorted(types_trous.items())),
        },
    }


def extraire_tous(noeuds, aretes):
    ids = sorted(ident for ident, n in noeuds.items()
                 if n.get("genre") == "evenement")
    graphes = [extraire(ident, noeuds, aretes) for ident in ids]
    trous = collections.Counter()
    for graphe in graphes:
        trous.update(graphe["stats"]["trous_par_type"])
    return {
        "schema": "graphe-causal/1",
        "mode": "tous",
        "graphes": graphes,
        "stats": {
            "evenements": len(graphes),
            "complets": sum(1 for g in graphes if g["complet"]),
            "incomplets": sum(1 for g in graphes if not g["complet"]),
            "trous_par_type": dict(sorted(trous.items())),
        },
    }


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    choix = ap.add_mutually_exclusive_group(required=True)
    choix.add_argument("--event", help="id avec ou sans le préfixe ev:")
    choix.add_argument("--tous", action="store_true")
    ap.add_argument("--completer", action="store_true",
                    help="proposer les nœuds qui ferment les trous")
    ap.add_argument("--vraiment", action="store_true",
                    help="avec --completer, écrire les compléments dans la chambre MJ")
    ap.add_argument("--compact", action="store_true")
    ap.add_argument("--sortie", help="écrire aussi le JSON dans ce fichier")
    args = ap.parse_args(argv)

    noeuds, aretes = charger_tissu()
    try:
        if args.tous:
            rendu = extraire_tous(noeuds, aretes)
        else:
            graphe = extraire(args.event, noeuds, aretes)
            rendu = {"schema": "graphe-causal/1", "mode": "event",
                     "graphes": [graphe], "stats": graphe["stats"]}
    except ValueError as exc:
        ap.error(str(exc))
    if args.completer:
        proposition = proposer_complements(rendu["graphes"], noeuds)
        rendu = {
            "schema": "graphe-causal-completion/1",
            "mode": "application" if args.vraiment else "apercu",
            "cible": COMPLEMENTS,
            "ajouts": proposition,
            "stats": {
                "noeuds": len(proposition["noeuds"]),
                "aretes": len(proposition["aretes"]),
                "ecrit": bool(args.vraiment),
            },
        }
        if args.vraiment:
            ecrire_complements(proposition)
    texte = json.dumps(rendu, ensure_ascii=False,
                       separators=(",", ":") if args.compact else None,
                       indent=None if args.compact else 2)
    if args.sortie:
        with io.open(args.sortie, "w", encoding="utf-8", newline="\n") as fichier:
            fichier.write(texte + "\n")
    print(texte)
    return 0
