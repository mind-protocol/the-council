# -*- coding: utf-8 -*-
"""SELECTEUR DE CONTEXTE — premiere couche d'un message joueur.

Chaque message ouvre une session neuve, sans reprise. Le modele ne joue pas et
ne modifie rien : il choisit les pointeurs d'etats cibles qui donnent le bon
contexte au prochain metier, ainsi que les hommes concernes. Son resultat est
un artefact de routage sous ``.agents-runtime/contextes/``, jamais un fait de
la fiction et donc jamais une table d'``etat/``.
"""
import argparse
import io
import json
import math
import os
import re
import tempfile
import unicodedata
import uuid

from agents import portage, runtime


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
ETAT = os.path.join(RACINE, "etat")
SORTIES = os.path.join(RACINE, ".agents-runtime", "contextes")
DERNIERS_ITEMS = 5
MAX_ITEMS_DETECTES = 8

MOTS_VIDES = {
    "alors", "apres", "avec", "avant", "avoir", "cette", "comme", "dans",
    "elle", "elles", "encore", "entre", "etre", "fait", "faire", "leur",
    "leurs", "mais", "meme", "pour", "quand", "sans", "sera", "sont",
    "tout", "toute", "tous", "vous", "votre", "plus", "moins", "rien",
    "bien", "cela", "cest", "dont", "donc", "ainsi", "seulement", "une",
    "des", "les", "que", "qui", "aux", "ses", "son", "sur", "par",
    "aucun", "contre", "deux", "etat", "affaire", "jour", "matin", "message",
    "ordre", "part", "piece", "peinte", "question", "rentre", "retour",
    "scene", "table", "tenue", "ville", "format", "correctement",
}
MARQUEURS_CONTINUATION = (
    r"^\?+$", r"^tu es la\??$", r"^vous etes la\??$",
    r"^(?:okay |ok )?continue(?:z)?\b", r"^reprends?\b",
)
MOTS_SYSTEME = {
    "agent", "dispatch", "inbox", "flux", "routage", "session", "source",
    "requete", "reponse", "fichier", "canal", "historique", "reference",
}


def _lire_json(chemin, defaut):
    try:
        with io.open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError, TypeError):
        return defaut


def action_par_ref(personnage, ref):
    """Rend l'action exacte de ce POST, sans depouiller le reste de l'inbox."""
    for chemin, action in portage._actions_en_attente(personnage):
        if str(action.get("ref") or "") == str(ref or ""):
            return chemin, action
    raise ValueError("action %s introuvable dans l'inbox de %s" %
                     (ref, personnage))


def _pointeur(numero, piece):
    sources = piece.get("cahier_sources") or []
    volume = next((s.get("volume_id") for s in sources
                   if s.get("volume_id")), None)
    return "%s#%s" % (volume or "affaire-inconnue", numero)


def modele_du_plan(livres=None):
    """Le graphe de toutes les affaires, sans brouillard de siege."""
    from plan.expose import bibliotheque, plan_modele

    livres = (bibliotheque.charger(ETAT) if livres is None else livres)
    return plan_modele.construire_depuis_livres(livres, vue_de="selecteur")


def index_du_plan(livres=None, modele=None):
    """Tous les etats cibles et verrous, issus de l'autorite normalisee."""
    modele = modele or modele_du_plan(livres)
    etats, verrous = [], []
    for numero, piece in sorted((modele.get("pieces") or {}).items(),
                                key=lambda x: (str(x[1].get("affaire") or ""),
                                               len(str(x[0])), str(x[0]))):
        genre = piece.get("genre")
        if genre not in ("etat", "verrou"):
            continue
        ligne = {
            "pointeur": _pointeur(numero, piece),
            "numero": str(numero),
            "affaire": str(piece.get("affaire") or ""),
            "nom": str(piece.get("nom") or ""),
            "vers": [str(x) for x in (piece.get("vers") or [])],
        }
        (etats if genre == "etat" else verrous).append(ligne)
    return etats, verrous


def index_des_joueurs(joueurs=None):
    """Personnages portes par un siege, distincts des hommes simulés."""
    joueurs = (_lire_json(os.path.join(ETAT, "joueurs.json"), [])
               if joueurs is None else joueurs)
    if isinstance(joueurs, dict):
        joueurs = joueurs.get("joueurs") or []
    return [{"id": str(j.get("personnage_id") or ""),
             "nom": str(j.get("nom") or j.get("personnage_id") or ""),
             "role": str(j.get("role") or "joueur")}
            for j in joueurs if isinstance(j, dict)
            and j.get("personnage_id") and not j.get("regie")]


def index_des_hommes(personnages=None, joueurs=None):
    """Annuaire des PNJ canoniques ; aucun personnage de siege n'y entre."""
    personnages = (_lire_json(os.path.join(ETAT, "personnages.json"), [])
                    if personnages is None else personnages)
    if isinstance(personnages, dict):
        personnages = personnages.get("personnages") or []
    ids_joueurs = {j["id"] for j in index_des_joueurs(joueurs)}
    return [{"id": str(p.get("id") or ""),
             "nom": str(p.get("nom") or p.get("id") or ""),
             "titre": str(p.get("titre") or "")}
            for p in personnages if isinstance(p, dict) and p.get("id")
            and str(p.get("id")) not in ids_joueurs]


def joueurs_dans_la_salle(personnage, joueurs=None, presence=None):
    """Les sieges humains occupes physiquement dans la meme salle."""
    joueurs = (_lire_json(os.path.join(ETAT, "joueurs.json"), [])
               if joueurs is None else joueurs)
    presence = (_lire_json(os.path.join(ETAT, "presence.json"), {})
                if presence is None else presence)
    if isinstance(joueurs, dict):
        joueurs = joueurs.get("joueurs") or []
    positions = ((presence or {}).get("presence") or presence or {})
    ici = positions.get(personnage) or {}
    salle, lieu = ici.get("salle"), ici.get("lieu")

    def meme_piece(position):
        if salle and position.get("salle"):
            return position.get("salle") == salle
        return bool(lieu and position.get("lieu") == lieu)

    presents = []
    for joueur in joueurs:
        if not isinstance(joueur, dict) or not joueur.get("occupe"):
            continue
        pid = joueur.get("personnage_id")
        position = positions.get(pid) or {}
        if pid and meme_piece(position):
            presents.append({"id": str(pid),
                             "nom": str(joueur.get("nom") or pid),
                             "role": str(joueur.get("role") or "joueur")})
    return {"salle": salle, "lieu": lieu, "joueurs": presents}


def _normaliser(texte):
    texte = unicodedata.normalize("NFD", str(texte or "").casefold())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return " ".join(re.findall(r"[a-z0-9]+", texte))


def _mots(texte):
    return {m for m in _normaliser(texte).split()
            if len(m) >= 4 and m not in MOTS_VIDES and not m.isdigit()}


def message_faible(texte):
    """Un acquiescement ou rappel bref n'ouvre pas une nouvelle affaire."""
    normalise = _normaliser(texte)
    if not normalise:
        return True
    return any(re.search(marqueur, normalise)
               for marqueur in MARQUEURS_CONTINUATION)


def doit_continuer(texte, precedent, est_run_vide=False,
                   personnes_nommees=None):
    """Un nom dans le message courant prime sur sa forme conversationnelle.

    « Tu es là ? » continue ; « Gerardys, tu es là ? » adresse Gerardys et
    doit donc repasser par une vraie sélection de contexte et d'homme.
    """
    nommes = personnes_nommees or {"joueurs": [], "hommes": []}
    adresse_quelqu_un = bool((nommes.get("joueurs") or [])
                             or (nommes.get("hommes") or []))
    return (message_faible(texte) and not est_run_vide and bool(precedent)
            and not adresse_quelqu_un)


def creation_transversale_requise(texte, joueurs):
    """Repere un incident technique qui traverse au moins deux sieges."""
    normalise = _normaliser(texte)
    mots = set(normalise.split())
    if not (mots & MOTS_SYSTEME):
        return False
    cites = 0
    for joueur in joueurs:
        formes = {_normaliser(joueur.get("id")),
                  _normaliser(joueur.get("nom"))}
        if any(forme and forme in normalise for forme in formes):
            cites += 1
    return cites >= 2


def detecter_personnes(texte, hommes, joueurs):
    """Ids dont le nom ou l'id est effectivement cite dans les six messages."""
    normalise = _normaliser(texte)
    trouves = {"joueurs": [], "hommes": []}
    for cle, annuaire in (("joueurs", joueurs), ("hommes", hommes)):
        for personne in annuaire:
            formes = {_normaliser(personne.get("id")),
                      _normaliser(personne.get("nom"))}
            nom = _normaliser(personne.get("nom")).split()
            if nom:
                formes.add(nom[-1])
            if any(len(f) >= 4 and re.search(r"(?:^| )%s(?: |$)" % re.escape(f),
                                             normalise)
                   for f in formes if f):
                trouves[cle].append(personne["id"])
    return trouves


def texte_recent(personnage, action):
    visibles = portage._items_visibles_du_flux(personnage)
    textes = [str(action.get("texte") or "")]
    textes.extend(portage._texte_du_fil(item)
                  for _numero, item in visibles[-DERNIERS_ITEMS:])
    return "\n".join(x for x in textes if x)


def classer_pieces(texte_action, texte_fil, modele, pointeurs_precedents=None):
    """Classe les items par preuves lexicales, sans demander au LLM de chercher."""
    pieces = modele.get("pieces") or {}
    action_n, fil_n = _normaliser(texte_action), _normaliser(texte_fil)
    mots_action, mots_fil = _mots(texte_action), _mots(texte_fil)
    numeros = set(re.findall(r"(?<!\d)(\d{3,5})(?!\d)",
                             "%s\n%s" % (texte_action, texte_fil)))
    documents = {}
    for numero, piece in pieces.items():
        documents[str(numero)] = _mots("%s %s" %
                                        (piece.get("nom"), piece.get("affaire")))
    frequences = {}
    for mots_piece in documents.values():
        for mot in mots_piece:
            frequences[mot] = frequences.get(mot, 0) + 1
    total = max(1, len(documents))
    precedents = set(pointeurs_precedents or [])
    classement = []
    for numero, piece in pieces.items():
        numero = str(numero)
        score, raisons = 0.0, []
        if numero in numeros:
            score += 1000
            raisons.append("numero explicite")
        nom, affaire = _normaliser(piece.get("nom")), _normaliser(piece.get("affaire"))
        if len(nom) >= 12 and nom in action_n:
            score += 180
            raisons.append("libelle exact dans le message")
        elif len(nom) >= 12 and nom in fil_n:
            score += 70
            raisons.append("libelle exact dans le fil")
        if len(affaire) >= 8 and affaire in action_n:
            score += 120
            raisons.append("affaire nommee dans le message")
        elif len(affaire) >= 8 and affaire in fil_n:
            score += 45
            raisons.append("affaire nommee dans le fil")
        commun_action = documents[numero] & mots_action
        commun_fil = documents[numero] & mots_fil
        lexical = sum(1.0 + math.log((total + 1.0) /
                                     (frequences[m] + 1.0))
                      for m in commun_action) * 3.0
        lexical += sum(1.0 + math.log((total + 1.0) /
                                      (frequences[m] + 1.0))
                       for m in commun_fil) * 1.0
        if lexical:
            score += lexical
            raisons.append("mots rares: %s" % ", ".join(
                sorted(commun_action | commun_fil)[:6]))
        if _pointeur(numero, piece) in precedents:
            score += 35
            raisons.append("contexte precedent")
        if score >= 6:
            classement.append({"numero": numero, "score": round(score, 2),
                                "raisons": raisons})
    return sorted(classement,
                  key=lambda x: (-x["score"], len(x["numero"]), x["numero"]))


def detecter_pieces(texte, modele):
    """Compatibilite : items les mieux ancres dans un texte unique."""
    return [x["numero"] for x in
            classer_pieces(texte, "", modele)[:MAX_ITEMS_DETECTES]]


def candidats_etats(classement, modele, maximum=5):
    """Ramene le classement d'items aux etats cibles effectivement routables."""
    pieces = modele.get("pieces") or {}
    contributions = {}
    preuves = {}
    for item in classement:
        for racine in _racines_etat(item["numero"], pieces):
            contributions.setdefault(racine, []).append(item["score"])
            preuves.setdefault(racine, []).append({
                "item": item["numero"], "raisons": item["raisons"]})
    scores = {racine: round(sum(sorted(valeurs, reverse=True)[:3]), 2)
              for racine, valeurs in contributions.items()}
    ordonnes = sorted(scores, key=lambda n: (-scores[n], len(n), n))[:maximum]
    return [{"pointeur": _pointeur(n, pieces[n]), "numero": n,
             "nom": str(pieces[n].get("nom") or ""),
             "score": scores[n], "preuves": preuves[n][:4]}
            for n in ordonnes]


def _racines_etat(numero, pieces, chemin=None):
    chemin = set(chemin or [])
    if numero in chemin or numero not in pieces:
        return set()
    chemin.add(numero)
    piece = pieces[numero]
    if piece.get("genre") == "etat":
        return {numero}
    racines = set()
    for suivant in piece.get("vers") or []:
        racines |= _racines_etat(str(suivant), pieces, chemin)
    return racines


def _enfants(numero, genre, pieces):
    return [(n, p) for n, p in pieces.items()
            if p.get("genre") == genre and numero in
            [str(x) for x in (p.get("vers") or [])]]


def _piece_arbre(numero, piece):
    return {"numero": str(numero), "pointeur": _pointeur(numero, piece),
            "nom": str(piece.get("nom") or ""),
            "affaire": str(piece.get("affaire") or ""),
            "office": str(piece.get("office") or ""),
            "moyens": [str(x) for x in (piece.get("moyens") or [])],
            "etat": str(piece.get("etat") or "")}


def arbre_d_un_etat(numero, pieces):
    etat = pieces[numero]
    arbre = {"etat_cible": _piece_arbre(numero, etat), "verrous": []}
    for nv, verrou in _enfants(numero, "verrou", pieces):
        branche_v = _piece_arbre(nv, verrou)
        branche_v["clefs"] = []
        for nk, clef in _enfants(nv, "clef", pieces):
            branche_k = _piece_arbre(nk, clef)
            branche_k["actions"] = [_piece_arbre(na, action)
                                      for na, action in
                                      _enfants(nk, "action", pieces)]
            branche_v["clefs"].append(branche_k)
        arbre["verrous"].append(branche_v)
    return arbre


def arbres_des_detectes(detectes, modele):
    pieces = modele.get("pieces") or {}
    racines = set()
    for numero in detectes:
        racines |= _racines_etat(numero, pieces)
    return {"items_detectes": [_piece_arbre(n, pieces[n]) for n in detectes
                                if n in pieces],
            "arbres": [arbre_d_un_etat(n, pieces)
                        for n in sorted(racines, key=lambda x: (len(x), x))]}


def contexte_precedent(personnage, ref=None):
    """Dernier routage acheve de ce siege, hors artefact courant."""
    dossier = os.path.join(SORTIES, personnage)
    candidats = []
    try:
        noms = os.listdir(dossier)
    except OSError:
        return None
    for nom in noms:
        if not nom.endswith(".json") or nom == "%s.json" % ref:
            continue
        chemin = os.path.join(dossier, nom)
        document = _lire_json(chemin, {})
        selection = document.get("selection") if isinstance(document, dict) else None
        if not isinstance(selection, dict):
            continue
        if selection.get("decision") not in ("selection", "creation", "continuer"):
            continue
        try:
            date = os.path.getmtime(chemin)
        except OSError:
            continue
        candidats.append((date, document))
    return max(candidats, key=lambda x: x[0])[1] if candidats else None


def _selection_precedente(document):
    return (document or {}).get("selection") or {}


def manuel_selecteur(etats, verrous, hommes, joueurs=None):
    """Le systeme complet de cette session jetable."""
    lignes = [
        "# Selecteur de contexte du Conseil",
        "",
        "Tu ne joues pas, tu ne narres pas, tu n'arbitres pas et tu ne modifies rien.",
        "Pour le message joueur recu, choisis les pointeurs d'etats cibles qui",
        "definissent son contexte utile, puis les joueurs et PNJ concernes.",
        "Un verrou est un indice : remonte son champ -> vers vers l'etat cible.",
        "Reste etroit : un contexte principal, et seulement les appuis necessaires.",
        "N'invente aucun pointeur ni aucun id. `hommes` ne contient JAMAIS un joueur.",
        "",
        "## Modele d'une affaire",
        "Une affaire est un volume de travail oriente vers un ou plusieurs ETATS CIBLES.",
        "Un etat cible decrit ce qui doit devenir vrai et sert de pointeur de contexte.",
        "Un VERROU decrit ce qui bloque aujourd'hui et pointe par `vers` vers l'etat cible.",
        "Une CLEF est un mecanisme capable de lever un verrou et pointe vers ce verrou.",
        "Une ACTION est un travail concret, souvent porte par un office ou des hommes,",
        "et pointe vers la clef qu'elle realise. La chaine se lit donc :",
        "ACTION -> CLEF -> VERROU -> ETAT CIBLE.",
        "L'arbre joint au message est le voisinage complet des items detectes :",
        "il comprend notamment les actions et leurs offices. Les index globaux ci-dessous",
        "permettent de choisir un autre etat cible si l'arbre detecte ne suffit pas.",
        "Si aucun etat cible existant ne convient directement, tu DOIS proposer la",
        "creation d'un contexte, plutot que rabattre le message sur une affaire vague.",
        "Cette reponse ne cree encore rien dans les cahiers.",
        "Un message faible (??, continue, tu es la) continue le contexte",
        "precedent : il ne choisit jamais une nouvelle affaire.",
        "EXCEPTION DURE : si le message courant nomme un joueur ou un PNJ,",
        "ce nom est une adresse. Ne réponds jamais `continuer` : sélectionne",
        "un contexte et recopie chaque personne nommée dans la bonne liste ;",
        "chaque PNJ nommé doit aussi avoir sa route homme -> pointeur.",
        "Une selection doit citer, pour chaque pointeur, des mots exacts du message ou",
        "du fil et expliquer en quoi leur traitement avance precisement cet etat cible.",
        "",
        "Reponds en JSON pur, sans prose ni cloture markdown, sous UNE de ces formes :",
        "Pour chaque homme selectionne, `routes_hommes` associe son id a UN pointeur",
        "selectionne. Le script en extraira le numero brut et ouvrira sa session de",
        "travail propre a cet item. Ne mets aucune route pour un joueur.",
        '{"decision":"selection","pointeurs":["volume#numero"],"ancrages":[{"pointeur":"volume#numero","citation":"mots exacts","lien":"ce que leur traitement avance"}],"creation":null,"joueurs_concernes":["id"],"hommes":["id"],"routes_hommes":[{"homme":"id","pointeur":"volume#numero"}],"motif":"une phrase"}',
        '{"decision":"creation","pointeurs":[],"ancrages":[],"creation":{"titre":"...","etat_cible":"ce qui doit devenir vrai","raison":"pourquoi aucun contexte existant ne convient"},"joueurs_concernes":["id"],"hommes":["id"],"routes_hommes":[],"motif":"une phrase"}',
        '{"decision":"continuer","pointeurs":[],"ancrages":[],"creation":null,"joueurs_concernes":[],"hommes":[],"routes_hommes":[],"motif":"message de continuite"}',
        '{"decision":"aucun","pointeurs":[],"ancrages":[],"creation":null,"joueurs_concernes":[],"hommes":[],"routes_hommes":[],"motif":"aucun contenu et aucun contexte precedent"}',
        "",
        "## Etats cibles — tous les cahiers d'affaire",
    ]
    for p in etats:
        lignes.append("[%s] %s | %s" %
                      (p["pointeur"], p["affaire"], p["nom"]))
    lignes.extend(["", "## Verrous — tous les cahiers d'affaire"])
    for p in verrous:
        cible = ",".join(p["vers"]) or "—"
        lignes.append("[%s] %s | %s | -> %s" %
                      (p["pointeur"], p["affaire"], p["nom"], cible))
    lignes.extend(["", "## Joueurs — personnages portes par un siege"])
    for j in joueurs or []:
        lignes.append("[%s] %s | %s" % (j["id"], j["nom"], j["role"]))
    lignes.extend(["", "## Hommes — PNJ uniquement, ids canoniques"])
    for h in hommes:
        lignes.append("[%s] %s | %s" % (h["id"], h["nom"], h["titre"]))
    return "\n".join(lignes).strip() + "\n"


def message_enrichi(personnage, chemin_action, action, presents=None,
                     arbres=None, candidats=None, precedent=None,
                     continuation=False, creation_obligatoire=False,
                     personnes_detectees=None, personnes_nommees=None):
    """Le message exact et les cinq derniers items visibles de son fil."""
    presents = presents or {"salle": None, "lieu": None, "joueurs": []}
    arbres = arbres or {"items_detectes": [], "arbres": []}
    precedent_compact = None
    if precedent:
        precedent_compact = {"ref": precedent.get("ref"),
                             "selection": precedent.get("selection")}
    return ("MESSAGE JOUEUR\n"
            "joueur: %s\nref: %s\nmode: %s\nsource: %s\ntexte exact: %s\n\n"
            "CONTRAINTES DETERMINEES PAR LE SCRIPT\n"
            "continuation obligatoire: %s\ncreation obligatoire: %s\n\n"
            "CONTEXTE PRECEDENT RESOLU\n%s\n\n"
            "JOUEURS PRESENTS DANS LA SALLE\n%s\n\n%s\n\n"
            "PERSONNES NOMMEES DANS LE MESSAGE COURANT — ROUTAGE OBLIGATOIRE\n%s\n\n"
            "PERSONNES DETECTEES DANS LE MESSAGE OU LE FIL — CONTEXTE\n%s\n\n"
            "ETATS CIBLES CANDIDATS CLASSES\n%s\n\n"
            "ARBRES DES ITEMS DETECTES\n%s\n" % (
                personnage, action.get("ref") or "—",
                action.get("mode") or action.get("type") or "—",
                os.path.abspath(chemin_action),
                str(action.get("texte") or ""),
                "OUI" if continuation else "non",
                "OUI" if creation_obligatoire else "non",
                json.dumps(precedent_compact, ensure_ascii=False, indent=2),
                json.dumps(presents, ensure_ascii=False, indent=2),
                portage.fil_du_joueur(personnage, limite=DERNIERS_ITEMS),
                json.dumps(personnes_nommees or {"joueurs": [], "hommes": []},
                           ensure_ascii=False, indent=2),
                json.dumps(personnes_detectees or {"joueurs": [], "hommes": []},
                           ensure_ascii=False, indent=2),
                json.dumps(candidats or [], ensure_ascii=False, indent=2),
                json.dumps(arbres, ensure_ascii=False, indent=2)))


def _json_de_reponse(texte):
    brut = str(texte or "").strip()
    if brut.startswith("```"):
        brut = re.sub(r"^```(?:json)?\s*", "", brut, flags=re.I)
        brut = re.sub(r"\s*```$", "", brut)
    try:
        valeur = json.loads(brut)
    except ValueError:
        debut, fin = brut.find("{"), brut.rfind("}")
        if debut < 0 or fin <= debut:
            raise ValueError("le selecteur n'a pas rendu de JSON")
        valeur = json.loads(brut[debut:fin + 1])
    if not isinstance(valeur, dict):
        raise ValueError("la selection n'est pas un objet JSON")
    return valeur


def valider_selection(valeur, etats, hommes, joueurs=None, texte_source="",
                      precedent=None, continuation_requise=False,
                      creation_requise=False, personnes_requises=None):
    pointeurs_valides = {p["pointeur"] for p in etats}
    hommes_valides = {h["id"] for h in hommes}
    joueurs_valides = {j["id"] for j in (joueurs or [])}
    pointeurs_demandes = [str(x) for x in (valeur.get("pointeurs") or [])]
    hommes_demandes = [str(x) for x in (valeur.get("hommes") or [])]
    joueurs_demandes = [str(x) for x in
                         (valeur.get("joueurs_concernes") or [])]
    inconnus = [x for x in pointeurs_demandes if x not in pointeurs_valides]
    inconnus += [x for x in hommes_demandes if x not in hommes_valides]
    inconnus += [x for x in joueurs_demandes if x not in joueurs_valides]
    if inconnus:
        raise ValueError("ids ou pointeurs inconnus: %s" % ", ".join(inconnus))
    if set(hommes_demandes) & joueurs_valides:
        raise ValueError("un joueur ne peut pas etre rendu dans hommes")
    decision = str(valeur.get("decision") or "").casefold()
    if decision not in ("selection", "creation", "continuer", "aucun"):
        raise ValueError("decision inconnue ou absente")
    precedente = _selection_precedente(precedent)
    personnes_requises = personnes_requises or {"joueurs": [], "hommes": []}
    hommes_requis = set(personnes_requises.get("hommes") or [])
    joueurs_requis = set(personnes_requises.get("joueurs") or [])
    if continuation_requise:
        if not precedente:
            raise ValueError("continuation requise mais contexte precedent absent")
        return {
            "decision": "continuer",
            "pointeurs": list(precedente.get("pointeurs") or []),
            "ancrages": list(precedente.get("ancrages") or []),
            "creation": precedente.get("creation"),
            "joueurs_concernes": list(
                precedente.get("joueurs_concernes") or []),
            "hommes": list(precedente.get("hommes") or []),
            "routes_hommes": list(precedente.get("routes_hommes") or []),
            "heritage_ref": precedent.get("ref"),
            "motif": "Continuation du contexte precedent : %s" %
                     str(valeur.get("motif") or "message faible").strip(),
        }
    if decision == "continuer":
        if hommes_requis or joueurs_requis:
            raise ValueError("une personne nommee dans le message interdit "
                             "la simple continuation")
        if not precedente:
            raise ValueError("aucun contexte precedent a continuer")
        return valider_selection(valeur, etats, hommes, joueurs,
                                 texte_source, precedent, True,
                                 creation_requise)
    if creation_requise and decision != "creation":
        raise ValueError("ce message transversal exige la creation d'un contexte")

    pointeurs = pointeurs_demandes
    elus = hommes_demandes
    joueurs_elus = joueurs_demandes
    if not hommes_requis.issubset(set(elus)):
        raise ValueError("PNJ nomme absent de hommes: %s" % ", ".join(
            sorted(hommes_requis - set(elus))))
    if not joueurs_requis.issubset(set(joueurs_elus)):
        raise ValueError("joueur nomme absent de joueurs_concernes: %s" %
                         ", ".join(sorted(joueurs_requis - set(joueurs_elus))))
    creation = valeur.get("creation")
    if decision == "creation":
        if not isinstance(creation, dict):
            raise ValueError("une creation de contexte doit etre un objet")
        creation = {"titre": str(creation.get("titre") or "").strip(),
                    "etat_cible": str(creation.get("etat_cible") or "").strip(),
                    "raison": str(creation.get("raison") or "").strip()}
        if not creation["titre"] or not creation["etat_cible"]:
            raise ValueError("la creation exige un titre et un etat cible")
        pointeurs = []
        ancrages = []
        routes_hommes = []
    elif decision == "aucun":
        if pointeurs or creation or elus:
            raise ValueError("aucun ne peut contenir ni pointeur, creation ni homme")
        ancrages, creation = [], None
        routes_hommes = []
    else:
        if not pointeurs:
            raise ValueError("une selection exige au moins un pointeur")
        creation = None
        ancrages = valeur.get("ancrages") or []
        if not isinstance(ancrages, list):
            raise ValueError("ancrages doit etre une liste")
        par_pointeur = {}
        source_n = _normaliser(texte_source)
        propres = []
        for ancrage in ancrages:
            if not isinstance(ancrage, dict):
                raise ValueError("chaque ancrage doit etre un objet")
            pointeur = str(ancrage.get("pointeur") or "")
            citation = str(ancrage.get("citation") or "").strip()
            lien = str(ancrage.get("lien") or "").strip()
            if pointeur not in pointeurs or not citation or not lien:
                raise ValueError("ancrage incomplet ou hors selection")
            citation_n = _normaliser(citation)
            if len(citation_n) < 3 or citation_n not in source_n:
                raise ValueError("citation d'ancrage absente du message et du fil")
            par_pointeur[pointeur] = True
            propres.append({"pointeur": pointeur, "citation": citation,
                             "lien": lien})
        if any(p not in par_pointeur for p in pointeurs):
            raise ValueError("chaque pointeur selectionne exige un ancrage")
        ancrages = propres
        routes_brutes = valeur.get("routes_hommes") or []
        if not isinstance(routes_brutes, list):
            raise ValueError("routes_hommes doit etre une liste")
        routes_hommes = []
        for route in routes_brutes:
            if not isinstance(route, dict):
                raise ValueError("chaque route d'homme doit etre un objet")
            homme = str(route.get("homme") or "")
            pointeur = str(route.get("pointeur") or "")
            if homme not in elus or pointeur not in pointeurs:
                raise ValueError("route d'homme hors de la selection")
            numero = pointeur.rsplit("#", 1)[-1]
            if not numero.isdigit():
                raise ValueError("le pointeur route ne porte pas un id numerique")
            routes_hommes.append({"homme": homme, "pointeur": pointeur,
                                  "contexte_id": numero})
        hommes_routes = {r["homme"] for r in routes_hommes}
        if hommes_routes != set(elus):
            raise ValueError("chaque homme selectionne exige une route de contexte")
    return {
        "decision": decision,
        "pointeurs": list(dict.fromkeys(pointeurs)),
        "ancrages": ancrages,
        "creation": creation,
        "joueurs_concernes": list(dict.fromkeys(joueurs_elus)),
        "hommes": list(dict.fromkeys(elus)),
        "routes_hommes": routes_hommes,
        "motif": str(valeur.get("motif") or "").strip(),
    }


def chemin_sortie(personnage, ref):
    return os.path.join(SORTIES, personnage, "%s.json" % ref)


def _ecrire_sortie(chemin, valeur):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    temporaire = chemin + ".%s.tmp" % uuid.uuid4().hex
    with io.open(temporaire, "w", encoding="utf-8", newline="\n") as f:
        json.dump(valeur, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(temporaire, chemin)


def selectionner(personnage, ref, modele=None, timeout=180):
    # Chaque ref est une unité autonome. Deux messages peuvent donc traverser
    # simultanément le sélecteur et le routeur, jusque dans leurs appels MJ.
    # Les écritures de sortie restent isolées par ref ; aucun verrou de siège
    # ne transforme plus le second POST en attente du premier.
    def executer():
        chemin_action, action = action_par_ref(personnage, ref)
        # JUMP n'est pas un message à classer dans les affaires du joueur.
        # C'est une commande de régie : le script choisit une cible unique et
        # porte son graphe au MJ, sans payer un appel LLM de sélection.
        if str(action.get("mode") or "").casefold() == "jump":
            from agents import jump, routeur_message
            joueurs_jump = [j["id"] for j in index_des_joueurs()]
            preparation = jump.preparer(
                str(action.get("texte") or ""), joueurs=joueurs_jump)
            document = {
                "version": "selection-contexte/4",
                "joueur_id": personnage,
                "ref": ref,
                "action": os.path.abspath(chemin_action),
                "selection": {
                    "decision": "jump",
                    "pointeurs": (["mj#%s" % preparation["contexte_id"]]
                                   if preparation.get("contexte_id") else []),
                    "hommes": [], "routes_hommes": [],
                    "joueurs_concernes": [], "creation": None,
                    "ancrages": [],
                    "motif": "préparer un seul événement puis le jouer",
                },
                "contexte_fourni": {"jump": preparation},
                "appel": {"session_id": None, "provider": "script",
                          "model": None},
            }
            sortie = chemin_sortie(personnage, ref)
            _ecrire_sortie(sortie, document)
            try:
                document["routage"] = routeur_message.router_message(
                    document, action, modele=modele)
            except Exception as exc:
                document["routage"] = {
                    "erreur": "%s: %s" % (type(exc).__name__, str(exc))}
            _ecrire_sortie(sortie, document)
            return document
        plan = modele_du_plan()
        etats, verrous = index_du_plan(modele=plan)
        joueurs = index_des_joueurs()
        hommes = index_des_hommes(joueurs=[
            {"personnage_id": j["id"], "nom": j["nom"], "role": j["role"]}
            for j in joueurs])
        manuel = manuel_selecteur(etats, verrous, hommes, joueurs)
        presents = joueurs_dans_la_salle(personnage)
        precedent = contexte_precedent(personnage, ref)
        precedente = _selection_precedente(precedent)
        visibles = portage._items_visibles_du_flux(personnage)
        fil_texte = "\n".join(portage._texte_du_fil(item)
                                for _numero, item in
                                visibles[-DERNIERS_ITEMS:])
        texte_action = str(action.get("texte") or "")
        classement = classer_pieces(
            texte_action, fil_texte, plan,
            pointeurs_precedents=precedente.get("pointeurs") or [])
        candidats = candidats_etats(classement, plan)
        detectes = [x["numero"] for x in classement[:MAX_ITEMS_DETECTES]]
        detectes += [preuve["item"] for candidat in candidats
                     for preuve in candidat.get("preuves") or []]
        detectes = list(dict.fromkeys(detectes))
        arbres = arbres_des_detectes(detectes, plan)
        est_run_vide = (not texte_action.strip() and
                        str(action.get("type") or "").casefold() == "run")
        personnes_nommees = detecter_personnes(
            texte_action, hommes, joueurs)
        continuation = doit_continuer(
            texte_action, precedent, est_run_vide=est_run_vide,
            personnes_nommees=personnes_nommees)
        creation_obligatoire = creation_transversale_requise(
            texte_action, joueurs)
        personnes = detecter_personnes("%s\n%s" % (texte_action, fil_texte),
                                       hommes, joueurs)
        message = message_enrichi(
            personnage, chemin_action, action, presents=presents,
            arbres=arbres, candidats=candidats, precedent=precedent,
            continuation=continuation,
            creation_obligatoire=creation_obligatoire,
            personnes_detectees=personnes,
            personnes_nommees=personnes_nommees)
        session = str(uuid.uuid4())
        sortie = chemin_sortie(personnage, ref)
        try:
            with tempfile.TemporaryDirectory(prefix="le-conseil-selecteur-") as neutre:
                rep = runtime.appeler(
                    role="selecteur-contexte", manuel=manuel, message=message,
                    session_id=session, modele=modele, timeout=timeout, cwd=neutre,
                    add_dirs=[], tools=[], reprendre=False,
                    compte_pour=personnage)
            selection = valider_selection(
                _json_de_reponse(rep.get("result")), etats, hommes, joueurs,
                texte_source="%s\n%s" % (texte_action, fil_texte),
                precedent=precedent, continuation_requise=continuation,
                creation_requise=creation_obligatoire,
                personnes_requises=personnes_nommees)
            document = {
                "version": "selection-contexte/4",
                "joueur_id": personnage,
                "ref": ref,
                "action": os.path.abspath(chemin_action),
                "contexte_fourni": {
                    "presence": presents,
                    "contexte_precedent_ref": (precedent or {}).get("ref"),
                    "continuation_obligatoire": continuation,
                    "creation_obligatoire": creation_obligatoire,
                    "personnes_nommees_action": personnes_nommees,
                    "personnes_detectees": personnes,
                    "classement_items": classement[:MAX_ITEMS_DETECTES],
                    "candidats_etats": candidats,
                    "items_detectes": arbres.get("items_detectes") or [],
                    "arbres": arbres.get("arbres") or [],
                },
                "selection": selection,
                "appel": {"session_id": session,
                          "provider": rep.get("provider"),
                          "model": rep.get("model")},
            }
            _ecrire_sortie(sortie, document)
            try:
                from agents import routeur_message
                document["routage"] = routeur_message.router_message(
                    document, action, modele=modele)
            except Exception as exc:
                # La selection reste une preuve durable meme si un metier en
                # aval tombe. L'inbox conserve l'action : rien n'est perdu et
                # le diagnostic ne se fait jamais passer pour une selection.
                document["routage"] = {
                    "erreur": "%s: %s" % (type(exc).__name__, str(exc))}
            _ecrire_sortie(sortie, document)
            return document
        except Exception as exc:
            _ecrire_sortie(sortie, {
                "version": "selection-contexte/4",
                "joueur_id": personnage,
                "ref": ref,
                "action": os.path.abspath(chemin_action),
                "erreur": "%s: %s" % (type(exc).__name__, str(exc)),
                "appel": {"session_id": session},
            })
            raise

    return executer()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--de", required=True,
                    help="personnage du siege qui a poste")
    ap.add_argument("--ref", required=True,
                    help="reference exacte posee par POST /action")
    ap.add_argument("--modele", default=None)
    ap.add_argument("--timeout", type=float, default=180, metavar="SECONDES")
    a = ap.parse_args(argv)
    if a.timeout <= 0:
        ap.error("le timeout doit etre positif")
    document = selectionner(a.de, a.ref, modele=a.modele,
                            timeout=a.timeout)
    print(json.dumps(document, ensure_ascii=False, indent=2))
