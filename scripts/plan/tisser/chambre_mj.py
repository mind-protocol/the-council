# -*- coding: utf-8 -*-
"""Projeter les affaires de la chambre du MJ dans le tissu dérivé.

Le MJ fait exception à l'isolation ordinaire des chambres : ses affaires sont
une source de la projection graphique. Elles ne reçoivent toutefois jamais les
adresses numériques du monde. Chaque pièce locale est qualifiée par son livre,
afin que ``R.1`` ou ``T.01`` ne collisionne avec rien d'autre.
"""
import glob
import io
import json
import os
import re
import unicodedata


CODE_LOCAL = re.compile(r"\b([A-Z][A-Z0-9]*\.\d+)\b")
MJ_DEBUT = 80000
MJ_FIN = 89999
BLOC = 500


def _plat(texte):
    texte = unicodedata.normalize("NFD", str(texte or ""))
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", texte.lower()).strip()


def _nu(texte):
    return re.sub(r"\*", "", str(texte or "")).strip()


def _colonne(d, *mots):
    for cle, valeur in d.items():
        plat = _plat(cle)
        if any(mot in plat for mot in mots):
            return str(valeur or "")
    return ""


def _codes(texte):
    return CODE_LOCAL.findall(_nu(texte))


def _plage(livre):
    plage = livre.get("_plage_mj") or {}
    if plage.get("de") is None or plage.get("a") is None:
        raise ValueError("affaire MJ sans plage réservée : %s" % livre.get("id"))
    return int(plage["de"]), int(plage["a"])


def id_affaire(livre):
    debut, _ = _plage(livre)
    return str(debut)


def id_piece(livre, code, genre):
    """Adresse stable dans le bloc : la famille décide de la centaine."""
    debut, fin = _plage(livre)
    numero = int(code.split(".", 1)[1])
    if not 1 <= numero <= 99:
        raise ValueError("code local hors 1-99 : %s dans %s" %
                         (code, livre.get("id")))
    centaines = {
        "etat_cible_mj": 0,
        "moment_mj": 0,
        "verrou_mj": 100,
        "clef_mj": 200,
        "action_mj": 300,
        "tension_mj": 400,
        "piece_mj": 400,
    }
    adresse = debut + centaines.get(genre, 400) + numero
    if adresse > fin:
        raise ValueError("adresse MJ hors bloc : %s -> %s" % (code, adresse))
    return str(adresse)


def charger_affaires_mj(racine):
    """Toutes les affaires actives, jamais les archives ni les dossiers."""
    livres = os.path.join(racine, "chambres", "mj", "books")
    manifeste = os.path.join(livres, "_plages.json")
    with io.open(manifeste, encoding="utf-8") as fichier:
        reservations = json.load(fichier)
    plage_totale = reservations.get("plage") or {}
    if (plage_totale.get("de"), plage_totale.get("a"),
            plage_totale.get("taille_bloc")) != (MJ_DEBUT, MJ_FIN, BLOC):
        raise ValueError("_plages.json ne réserve pas exactement 80000-89999 par blocs de 500")
    attribuees = reservations.get("affaires") or {}
    intervalles = []
    for ident, plage in attribuees.items():
        debut, fin = int(plage.get("de", -1)), int(plage.get("a", -1))
        if debut < MJ_DEBUT or fin > MJ_FIN or fin - debut + 1 != BLOC:
            raise ValueError("bloc MJ invalide pour %s : %s-%s" %
                             (ident, debut, fin))
        intervalles.append((debut, fin, ident))
    for (_, fin, ident), (debut_suivant, _, ident_suivant) in zip(
            sorted(intervalles), sorted(intervalles)[1:]):
        if debut_suivant <= fin:
            raise ValueError("blocs MJ superposés : %s / %s" %
                             (ident, ident_suivant))

    motif = os.path.join(livres, "affaire-*.json")
    affaires = []
    for chemin in sorted(glob.glob(motif)):
        with io.open(chemin, encoding="utf-8") as fichier:
            livre = json.load(fichier)
        if isinstance(livre, dict) and livre.get("type") in ("affaire", "plan"):
            livre = dict(livre)
            if livre.get("id") not in attribuees:
                raise ValueError("affaire MJ sans bloc dans _plages.json : %s" %
                                 livre.get("id"))
            livre["_chemin_chambre"] = chemin
            livre["_plage_mj"] = attribuees[livre["id"]]
            affaires.append(livre)
    return affaires


def _genre(titre):
    titre = _plat(titre)
    if "action" in titre:
        return "action_mj"
    if "verrou" in titre:
        return "verrou_mj"
    if "clef" in titre:
        return "clef_mj"
    if ("etat" in titre and "cible" in titre) or "ce que je veux" in titre:
        return "etat_cible_mj"
    if "moment" in titre and "marquant" in titre:
        return "moment_mj"
    if "ne tient pas ensemble" in titre:
        return "tension_mj"
    return "piece_mj"


def _note_importance(d):
    brut = _colonne(d, "importance")
    m = re.search(r"\d{1,3}", brut)
    if not m:
        return None
    note = int(m.group())
    return note if 0 <= note <= 100 else None


def noeuds_affaires_mj(affaires):
    """Descripteurs de nœuds consommés par ``lecture.indexer``."""
    noeuds = []
    adresses = set()
    for livre in affaires or []:
        adresse_affaire = id_affaire(livre)
        if adresse_affaire in adresses:
            raise ValueError("adresse MJ dupliquée : %s" % adresse_affaire)
        adresses.add(adresse_affaire)
        noeuds.append({
            "id": adresse_affaire,
            "genre": "affaire_mj",
            "ou": "chambres/mj/books",
            "quoi": livre.get("titre") or livre.get("id"),
            "local": True,
            "autorite": "mj",
            "livre_id": livre.get("id"),
            "namespace": "mj",
            "plage": livre.get("_plage_mj"),
        })
        for table in livre.get("tables") or []:
            colonnes = table.get("colonnes") or []
            for ligne in table.get("lignes") or []:
                cellules = ligne.get("cellules") if isinstance(ligne, dict) else ligne
                if not isinstance(cellules, list) or not cellules:
                    continue
                codes = _codes(cellules[0])
                if not codes:
                    continue
                code = codes[0]
                d = dict(zip(colonnes, cellules))
                genre = _genre(table.get("titre"))
                adresse = id_piece(livre, code, genre)
                if adresse in adresses:
                    raise ValueError("adresse MJ dupliquée : %s (%s)" %
                                     (adresse, code))
                adresses.add(adresse)
                libelle = (_colonne(d, "l etat", "le verrou", "la clef",
                                    "l action", "action", "regle")
                           or (cellules[1] if len(cellules) > 1 else code))
                noeuds.append({
                    "id": adresse,
                    "genre": genre,
                    "ou": "chambre:mj:" + str(livre.get("id")),
                    "quoi": libelle,
                    "local": True,
                    "autorite": "mj",
                    "livre_id": livre.get("id"),
                    "code_local": code,
                    "adresse_mj": adresse,
                    "namespace": "mj",
                    "etat": _colonne(d, "etat", "statut"),
                    "jour_du": _colonne(d, "jour du", "jour du", "se produit"),
                    "importance": _note_importance(d),
                })
    return noeuds


def _index_pieces(affaires):
    par_livre, globales = {}, {}
    for noeud in noeuds_affaires_mj(affaires):
        code = noeud.get("code_local")
        if not code:
            continue
        par_livre.setdefault(noeud["livre_id"], {})[code] = noeud["id"]
        globales.setdefault(code, []).append(noeud["id"])
    return par_livre, globales


def _aliases_affaires(affaires):
    aliases = {}
    for livre in affaires:
        aid = id_affaire(livre)
        titre = str(livre.get("titre") or "")
        ident = str(livre.get("id") or "").replace("affaire-", "")
        formes = [titre, titre.split("—", 1)[0], ident.replace("-", " ")]
        for forme in formes:
            if _plat(forme):
                aliases.setdefault(_plat(forme), aid)
    return aliases


def _resoudre_codes(texte, livre, par_livre, globales):
    resultat = []
    for code in _codes(texte):
        locale = par_livre.get(livre.get("id"), {}).get(code)
        if locale:
            resultat.append(locale)
        elif len(globales.get(code, [])) == 1:
            resultat.append(globales[code][0])
    return resultat


def _evenements_dans(texte, ids_evenements):
    texte = str(texte or "")
    trouves = []
    for ident in sorted(ids_evenements, key=len, reverse=True):
        motif = r"(?<![a-z0-9-]){}(?![a-z0-9-])".format(re.escape(ident))
        if re.search(motif, texte, re.I):
            trouves.append("ev:" + ident)
    return trouves


def aretes_affaires_mj(affaires, evenements):
    """Arêtes locales et liens vers les événements canoniques existants."""
    affaires = affaires or []
    par_livre, globales = _index_pieces(affaires)
    aliases = _aliases_affaires(affaires)
    ids_evenements = {str(e.get("id")) for e in evenements or [] if e.get("id")}
    aretes = []

    def arc(de, vers, nature, source, texte="", flou=False, **proprietes):
        a = {"de": de, "vers": vers, "nature": nature, "source": source,
             "texte": _nu(texte)[:110], "flou": flou}
        a.update({k: v for k, v in proprietes.items() if v is not None})
        aretes.append(a)

    for livre in affaires:
        affaire = id_affaire(livre)
        for code, piece in par_livre.get(livre.get("id"), {}).items():
            arc(affaire, piece, "decoupe", "chambres/mj/contenu", texte=code,
                local=True, autorite="mj")

        for table in livre.get("tables") or []:
            colonnes = table.get("colonnes") or []
            titre = _plat(table.get("titre"))
            for ligne in table.get("lignes") or []:
                cellules = ligne.get("cellules") if isinstance(ligne, dict) else ligne
                if not isinstance(cellules, list):
                    continue
                d = dict(zip(colonnes, cellules))
                tete_codes = _codes(cellules[0] if cellules else "")
                tete = (par_livre.get(livre.get("id"), {}).get(tete_codes[0])
                        if tete_codes else None)

                if "affaires liees" in titre:
                    nature = _nu(cellules[0] if cellules else "") or "lie"
                    notre = _resoudre_codes(_colonne(d, "notre piece"), livre,
                                            par_livre, globales)
                    leur = _resoudre_codes(_colonne(d, "la leur"), livre,
                                           par_livre, globales)
                    cible_texte = _colonne(d, "l affaire", "affaire")
                    cible = aliases.get(_plat(cible_texte.replace("(chambre)", "")))
                    sources = notre or [affaire]
                    cibles = leur or ([cible] if cible else [])
                    pourquoi = _colonne(d, "pourquoi") or cible_texte
                    if cibles:
                        for de in sources:
                            for vers in cibles:
                                arc(de, vers, nature, "chambres/mj/affaires-liees",
                                    texte=pourquoi, local=True, autorite="mj")
                    else:
                        for de in sources:
                            arc(de, "?", nature, "chambres/mj/affaires-liees",
                                texte="{} — {}".format(cible_texte, pourquoi),
                                flou=True, local=True, autorite="mj")
                    continue

                if tete:
                    relations = []
                    if "action" in titre:
                        relations += [("realise", _colonne(d, "realise")),
                                      ("depend_de", _colonne(d, "depend de"))]
                    if "verrou" in titre:
                        relations.append(("bloque", _colonne(d, "bloque")))
                    if "clef" in titre:
                        relations.append(("ouvre", _colonne(d, "ouvre")))
                    for nature, valeur in relations:
                        for cible in _resoudre_codes(valeur, livre,
                                                     par_livre, globales):
                            arc(tete, cible, nature, "chambres/mj/structure",
                                texte=valeur, local=True, autorite="mj")

                    if "moment" in titre and "marquant" in titre:
                        source = _colonne(d, "evenement source")
                        for evenement in _evenements_dans(source, ids_evenements):
                            arc(tete, evenement, "depend_de",
                                "chambres/mj/moments", texte=source,
                                local=True, autorite="mj")

                if "liens causaux" in titre:
                    sources = _evenements_dans(_colonne(d, "de"), ids_evenements)
                    cibles = _evenements_dans(_colonne(d, "vers"), ids_evenements)
                    statut = _colonne(d, "statut du lien")
                    texte = "{} — {}".format(_colonne(d, "relation"),
                                              _colonne(d, "preuve"))
                    for de in sources:
                        for vers in cibles:
                            arc(de, vers, "amont", "chambres/mj/liens-causaux",
                                texte=texte, local=True, autorite="mj",
                                epistemique=statut,
                                conditionnel="condition" in _plat(statut))
    return aretes
