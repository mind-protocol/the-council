# -*- coding: utf-8 -*-
"""DOSSIER — les references du monde et du dossier servies a l'activation,
le dossier d'une activation, et la contrainte de regence.
"""
import io
import json
import os
import re

from agents.expose import depecher  # le script d'appel canonique
from etat.expose import tables
from temps.expose import regence
from temps.expose import presence as presence_calc  # la position se CALCULE

from agents.activation.socle import RACINE, ETAT, lire_json, journaliser
from agents.activation.horloges import minute_absolue
from agents.activation.graphe import continuite_tache

def references_du_monde():
    """Tout ce qui EXISTE VRAIMENT, et qu'un homme a donc le droit de nommer.

    Le dossier est ce qu'on lui a mis en main ; ce n'est pas la liste de ce qui
    existe. Refuser le rapport d'Alicent parce qu'elle a nommé `pers:larys`, ou
    celui d'Aldon Hask parce qu'il a nommé `corlys`, c'est jeter une journée
    entière au motif que le monde est plus grand que la chemise qu'on lui a
    donnée. Larys existe. Corlys existe. Un homme qui les nomme a raison.

    On accepte donc toute adresse qui résout contre l'état réel — gens, lieux,
    maisons, mains, livres, pensees, salles. Ce qui reste refusé, c'est ce qui
    ne désigne rien nulle part, et c'est une vraie faute.
    """
    refs = set()

    def poser(prefixes, ident):
        if not ident:
            return
        ident = str(ident)
        refs.add(ident)
        for p in prefixes:
            refs.add(p + ident)

    def entrees(nom, cle=None):
        brut = lire_json(os.path.join(ETAT, nom + ".json"), [])
        if isinstance(brut, dict):
            brut = brut.get(cle or nom) or []
        return [x for x in brut if isinstance(x, dict)]

    for x in entrees("personnages"):
        poser(("pers:", "ref:pers:"), x.get("id"))
    for x in entrees("lieux"):
        poser(("salle:", "lieu:", "ref:salle:"), x.get("id"))
        for alias in x.get("alias") or []:
            poser(("salle:", "lieu:"), alias)
    for x in entrees("maisons"):
        poser(("maison:",), x.get("id"))
    for x in entrees("mains"):
        poser(("main:", "ref:main:"), x.get("id"))
    for x in entrees("books", "books"):
        poser(("livre:", "book:", "ref:livre:"), x.get("id"))
    for x in entrees("plis", "plis"):
        poser(("pli:",), x.get("id"))
    topologie = lire_json(os.path.join(ETAT, "chemins.json"), {})
    for arete in topologie.get("aretes") or []:
        if isinstance(arete, list):
            for lieu_id in arete[:2]:
                poser(("salle:",), lieu_id)
    for alias, lieu_id in (topologie.get("alias") or {}).items():
        poser(("salle:",), alias)
        poser(("salle:",), lieu_id)
    return refs


def references_du_dossier(dossier):
    """Valeurs adressables que le dossier fermé rend déjà connaissables.

    Le dossier NE BORNE PAS ce qui est nommable : on y ajoute tout ce qui
    existe dans l'état (voir `references_du_monde`). Un homme peut nommer un
    homme, un lieu, un livre ou une main qui n'était pas dans sa chemise.
    """
    refs = set(references_du_monde())

    def visiter(valeur):
        if isinstance(valeur, dict):
            for v in valeur.values():
                visiter(v)
        elif isinstance(valeur, list):
            for v in valeur:
                visiter(v)
        elif isinstance(valeur, (str, int, float)) and not isinstance(valeur, bool):
            texte = str(valeur)
            if texte:
                refs.add(texte)

    visiter(dossier)
    personnage = dossier.get("personnage") or {}
    if personnage.get("id"):
        refs.add("pers:" + str(personnage["id"]))
    salle = dossier.get("salle_actuelle") or {}
    if salle.get("id"):
        refs.add("salle:" + str(salle["id"]))
    for personne in salle.get("personnes") or []:
        if isinstance(personne, dict) and personne.get("id"):
            refs.add("pers:" + str(personne["id"]))
    for main in dossier.get("mains_portees") or []:
        if isinstance(main, dict) and main.get("id"):
            mid = str(main["id"])
            refs.update((mid, "main:" + mid))
    for volume in dossier.get("livres_accessibles") or []:
        if isinstance(volume, dict) and volume.get("id"):
            lid = str(volume["id"])
            refs.update((lid, "livre:" + lid, "book:" + lid))
    tache = dossier.get("tache") or {}
    if tache.get("id"):
        tid = str(tache["id"])
        refs.update((tid, "tache:" + tid))
    # Le narrateur reçoit toujours la topologie des salles dans son contexte.
    # Ses extrémités sont donc des adresses réelles, même si elles ne sont pas
    # la salle de départ de l'acteur.
    topologie = lire_json(os.path.join(ETAT, "chemins.json"), {})
    for arete in topologie.get("aretes") or []:
        if not isinstance(arete, list) or len(arete) < 2:
            continue
        for lieu_id in arete[:2]:
            if lieu_id:
                refs.update((str(lieu_id), "salle:" + str(lieu_id)))
    for alias, lieu_id in (topologie.get("alias") or {}).items():
        refs.update((str(alias), str(lieu_id), "salle:" + str(lieu_id)))
    return refs


def dossier_activation(pid, tache, horloge, noeuds, etat=None):
    """La tranche d'etat necessaire : identite, tete, mains et travail."""
    personnages = lire_json(os.path.join(ETAT, "personnages.json"), [])
    if isinstance(personnages, dict):
        personnages = personnages.get("personnages") or []
    noms_personnes = {p.get("id"): p.get("nom") or p.get("id")
                      for p in personnages if isinstance(p, dict) and p.get("id")}
    lieux = lire_json(os.path.join(ETAT, "lieux.json"), [])
    if isinstance(lieux, dict):
        lieux = lieux.get("lieux") or []
    noms_lieux = {l.get("id"): l.get("nom") or l.get("id")
                  for l in lieux if isinstance(l, dict) and l.get("id")}
    intentions = lire_json(os.path.join(ETAT, "intentions.json"), [])
    if isinstance(intentions, dict):
        intentions = intentions.get("intentions") or []
    mains = lire_json(os.path.join(ETAT, "mains.json"), [])
    if isinstance(mains, dict):
        mains = mains.get("mains") or []
    presence = lire_json(os.path.join(ETAT, "presence.json"), {})
    if not isinstance(presence, dict):
        presence = {}
    # `resolu` EST UN CACHE, ET IL A UNE DATE : on la compare a l'horloge avant
    # de s'en servir. Mesure le 129.4.5 : le monde au 5e minute 540, le cache
    # date du 4e minute 540 — un jour entier de retard, servi tel quel a un
    # acteur comme la piece ou il se tient et les gens qui l'entourent. Trop
    # vieux, on ne degrade pas vers la ligne brute (qui ment de la meme facon,
    # en plus vieux) : ON RECALCULE, c'est le seul repli qui dise le vrai.
    resolus, _retard = presence_calc.resolu_de(presence)
    if not resolus:
        try:
            resolus = presence_calc.resoudre()
        except Exception:
            resolus = ((presence.get("resolu") or {}).get("gens") or {})
    position = resolus.get(pid) or {}
    salle_id = position.get("salle")
    salle_nom = position.get("lieu")
    if salle_id and not salle_nom:
        # Un trajet ou une ancienne exception peut ne porter que l'id. Une
        # autre personne résolue dans la même pièce en donne alors le nom.
        salle_nom = next((ou.get("lieu") for ou in resolus.values()
                          if ou.get("salle") == salle_id and ou.get("lieu")), None)
    if salle_id and not salle_nom:
        salle_nom = salle_id.replace("-", " ").capitalize()
    personnes_dans_salle = []
    if salle_id:
        for present_id, ou in resolus.items():
            if ou.get("salle") != salle_id:
                continue
            personnes_dans_salle.append({
                "id": present_id,
                "nom": noms_personnes.get(present_id, present_id),
            })
        personnes_dans_salle.sort(key=lambda x: (x["nom"].casefold(), x["id"]))
    personnage = next((p for p in personnages if p.get("id") == pid), None)
    if personnage:
        personnage = {k: personnage.get(k) for k in
                       ("id", "nom", "titre", "naissance", "traits",
                        "objectifs", "maniere", "portrait", "etat",
                        "condition", "lieu_id") if k in personnage}
        personnage["lieu"] = noms_lieux.get(personnage.get("lieu_id"),
                                             personnage.get("lieu_id"))
    intention = next((t for t in intentions
                      if t.get("personnage_id") == pid), None)
    if intention:
        etape_id = tache.get("id", "").removeprefix("etape:")
        plan = [p for p in intention.get("plan") or []
                if p.get("id") == etape_id]
        intention = {k: intention.get(k) for k in
                     ("personnage_id", "croyances", "ignore", "intention",
                      "declencheurs", "attitude_joueur", "mandat", "date_maj")
                     if k in intention}
        intention["etape_elue"] = plan[0] if plan else None
    # La mémoire écrite de l'homme — son dernier rapport et sa dernière
    # conclusion. L'ancien `travaux = []` était codé en dur : le bloc
    # `travaux_ouverts` de memoire_activation() n'a jamais été servi avant
    # le 30 août. Le lecteur canonique vit chez depecher, même dossier pour
    # le chemin manuel et pour celui-ci.
    travaux_ouverts = depecher.travaux_ouverts_de(pid)
    mains_portees = []
    for m in mains:
        if not isinstance(m.get("porteur"), dict) or m["porteur"].get("id") != pid:
            continue
        mains_portees.append({k: m.get(k) for k in
                              ("id", "quoi", "lieu_id", "mandat", "mesure",
                               "seuils", "date_maj") if k in m})
    livres_accessibles = [
        {k: volume.get(k) for k in ("id", "titre", "type") if k in volume}
        for volume in depecher.livre.etagere(pid)
        if isinstance(volume, dict) and volume.get("id")
    ]
    continuite = continuite_tache(etat or {}, tache.get("id"), noeuds)
    relations = lire_json(os.path.join(ETAT, "relations.json"), [])
    if isinstance(relations, dict):
        relations = relations.get("relations") or []
    relations_acteur = []
    for relation in relations:
        source = relation.get("source_id")
        cible = relation.get("cible_id")
        if pid not in (source, cible):
            continue
        relations_acteur.append({
            "source_id": source,
            "source": noms_personnes.get(source, source),
            "cible_id": cible,
            "cible": noms_personnes.get(cible, cible),
            "opinion": relation.get("opinion"),
            "liens": relation.get("liens") or [],
        })
    return {
        "date_du_monde": dict(zip(("annee", "lune", "jour"),
                                  depecher.date_du_monde())),
        "diffusion": {
            "origine": horloge["source_id"], "front": horloge["front_id"],
            "secondes_depuis_origine": round(horloge["present_secondes"], 3),
        },
        "personnage": personnage,
        "salle_actuelle": {
            "id": salle_id,
            "nom": salle_nom or "Salle inconnue",
            "personnes": personnes_dans_salle,
        },
        "intention": intention,
        "relations": relations_acteur,
        "tache": tache,
        "continuite_reprise": continuite,
        "chemin": [{"id": nid, **(noeuds.get(nid) or {})}
                    for nid in tache.get("chemin") or []],
        "travaux_ouverts": travaux_ouverts,
        "mains_portees": mains_portees,
        "livres_accessibles": livres_accessibles,
        # Vide pour tout le monde sauf les sieges vacants. Le garde mecanique
        # refuse apres coup ; ceci fait qu'on n'essaie pas — et les deux sont
        # necessaires, l'un n'excusant jamais l'absence de l'autre.
        "contrainte_regence": contrainte_regence(pid),
    }


def contrainte_regence(pid):
    """Ce qu'un siege vacant doit savoir de sa propre limite, ou None."""
    if not regence.est_en_regence(pid):
        return None
    return {
        "pourquoi": "Tu tiens la place de quelqu'un qui reviendra s'y "
                    "asseoir. Tout ce que tu prepares est bon ; ce qui "
                    "engage pour toujours ne t'appartient pas.",
        "interdits": [
            {"quoi": ligne["quoi"], "a_la_place": ligne["rabattement"]}
            for ligne in regence.LIGNES_ROUGES
        ],
        "comment_s_arreter": "Quand une affaire ne peut avancer qu'en "
                             "franchissant l'une de ces lignes, va jusqu'au "
                             "bord : prepare tout, chiffre, ecris qui decide "
                             "et ce que le retard coûte — puis arrete-toi et "
                             "dis-le en clair dans ton rapport.",
    }


def chaines_dans(valeur):
    if isinstance(valeur, dict):
        for v in valeur.values():
            yield from chaines_dans(v)
    elif isinstance(valeur, list):
        for v in valeur:
            yield from chaines_dans(v)
    elif isinstance(valeur, str):
        yield valeur


def mots(texte):
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿŒœ'-]+", str(texte or ""))

