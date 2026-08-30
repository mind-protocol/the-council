# -*- coding: utf-8 -*-
"""TACHES — choisir la tache d'un acteur, et mettre a jour les energies
(du graphe, des acteurs) entre deux passages de la boucle.
"""
import collections
import hashlib
import math
import os
import time

from agents.activation.socle import (ENERGIE_MAX, ENERGIE_MIN,
                                     DEMI_VIE_ENERGIE,
                                     ENERGIE_ACTIVATION_MIN, ETAT,
                                     lire_json, journaliser)
from agents.activation.horloges import appliquer_polarites_horloge
from agents.activation.graphe import (tache_active, tache_disponible,
                                      acteur_en_repos, empreinte_tache,
                                      continuite_tache, energie_de_tache,
                                      clusters_par_lieu,
                                      normaliser_par_cluster, calendrier)

def choisir_tache(acteur, noeuds, aretes, adj, energies, etat=None,
                  present=0.0):
    """Tache active la plus proche de l'acteur.

    ``tient`` est l'assignation canonique d'une action. Une tache tenue par un
    autre personnage ne doit jamais etre recuperee par simple proximite dans le
    graphe. L'assignation definit l'ensemble eligible ; la distance decide,
    puis l'energie ne departage que deux taches a distance egale.
    """
    etat = etat or {}
    titulaires = collections.defaultdict(set)
    for a in aretes:
        # « tient » est l'assignation d'une action de plan ; « poursuit » est
        # l'etape que porte une TETE. Les deux sont des appartenances, et ne
        # compter que la premiere ouvrait une fuite entre les camps : une etape
        # d'intentions.json n'a pas d'arete « tient », donc `titulaires` restait
        # vide pour elle, donc n'importe qui pouvait la ramasser au repli par
        # distance. Mesure du 129.4.3 : le mestre GERARDYS, qui sert la reine,
        # se voyait attribuer `etape:otto-recit-du-feu` — « faire ecrire par
        # Orwyle le recit officiel du massacre », l'etape d'OTTO HIGHTOWER — et
        # ser Robert Quince `etape:larys-mysaria`. Le conseil de Peyredragon
        # s'appretait a executer le plan d'en face.
        if a.get("flou") or a.get("nature") not in ("tient", "poursuit"):
            continue
        de, vers = a.get("de"), a.get("vers")
        if de in noeuds and vers in noeuds:
            if tache_active(noeuds[de]) and noeuds[vers].get("genre") == "personne":
                titulaires[de].add(vers)
            elif tache_active(noeuds[vers]) and noeuds[de].get("genre") == "personne":
                titulaires[vers].add(de)

    def appartient_ou_vacante(nid):
        return not titulaires.get(nid) or acteur in titulaires[nid]

    directes = []
    for a in aretes:
        if a.get("flou") or a.get("de") not in noeuds or a.get("vers") not in noeuds:
            continue
        autre = None
        if a.get("de") == acteur and a.get("nature") in ("poursuit", "tient"):
            autre = a.get("vers")
        elif a.get("vers") == acteur and a.get("nature") in ("poursuit", "tient"):
            autre = a.get("de")
        if autre and tache_active(noeuds[autre]) and appartient_ou_vacante(autre) \
                and tache_disponible(etat, autre, noeuds, present) \
                and float(energies.get(autre, 0.0)) >= ENERGIE_MIN:
            # L'assignation explicite passe avant le simple fait que l'acteur
            # poursuit une etape de son intention.
            directes.append((0 if a.get("nature") == "tient" else 1, autre))
    if directes:
        directes.sort(key=lambda x: (x[0], -float(energies.get(x[1], 0.0)), x[1]))
        _priorite_affectation, nid = directes[0]
        return {"id": nid, "quoi": noeuds[nid].get("quoi") or nid,
                "genre": noeuds[nid].get("genre"), "distance": 1,
                "chemin": [acteur, nid], "creee": False}

    file = collections.deque([(acteur, [acteur])])
    vus = {acteur}
    candidats = []
    while file:
        ici, chemin = file.popleft()
        d = len(chemin) - 1
        if (ici != acteur and tache_active(noeuds[ici])
                and appartient_ou_vacante(ici)
                and tache_disponible(etat, ici, noeuds, present)
                and float(energies.get(ici, 0.0)) >= ENERGIE_MIN):
            candidats.append((d, -float(energies.get(ici, 0.0)), ici, chemin))
            continue
        # Une autre personne est une frontiere : ses propres taches ne sont
        # pas le prolongement implicite de celles de l'acteur active.
        if ici != acteur and noeuds[ici].get("genre") == "personne":
            continue
        for autre in adj.get(ici) or []:
            if autre not in vus:
                vus.add(autre)
                file.append((autre, chemin + [autre]))
    if candidats:
        _distance, _energie, nid, chemin = sorted(candidats)[0]
        return {"id": nid, "quoi": noeuds[nid].get("quoi") or nid,
                "genre": noeuds[nid].get("genre"), "distance": len(chemin) - 1,
                "chemin": chemin, "creee": False}

    pid = acteur.removeprefix("pers:")
    intentions = lire_json(os.path.join(ETAT, "intentions.json"), [])
    tete = next((t for t in intentions if t.get("personnage_id") == pid), {})
    quoi = (tete.get("intention") or
            next((o.get("but") for o in (noeuds[acteur].get("objectifs") or [])
                  if isinstance(o, dict) and o.get("but")), None))
    if not quoi:
        return None
    ident = hashlib.sha1((pid + "\0" + quoi).encode("utf-8")).hexdigest()[:12]
    return {"id": "activation:" + pid + ":" + ident, "quoi": quoi,
            "genre": "tache-proposee", "distance": 0,
            "chemin": [acteur], "creee": True,
            "source": "intentions.json:intention"}


def mettre_a_jour_energie_graphe(etat, horloge, scores, noeuds, adj,
                                 polarites):
    """Integre et persiste l'energie de chaque node du graphe.

    ``scores`` est la force instantanee produite par la topologie. L'energie,
    elle, vit dans l'overlay runtime et converge vers cette force avec une
    demi-vie de cinq minutes. Un score disparu fait decroitre la reserve ; aucun
    cycle ne la remet a zero.
    """
    graphe = etat.setdefault("graphe", {"noeuds": {}, "liens": {}})
    reserves = graphe.setdefault("noeuds", {})
    present = float(horloge["present_secondes"])
    precedent = graphe.get("mis_a_jour_a")
    dt_s = max(0.0, present - float(precedent)) if precedent is not None else 0.0
    alpha = 1.0 - math.exp(-math.log(2.0) * dt_s / DEMI_VIE_ENERGIE)
    acteurs_legacy = etat.get("acteurs") or {}
    cibles = {
        nid: ENERGIE_MAX * max(0.0, min(1.0, float(scores.get(nid, 0.0))))
        for nid in noeuds
    }
    cibles = appliquer_polarites_horloge(cibles, polarites, adj)
    resultat = {}
    for nid in noeuds:
        cible = cibles[nid]
        if nid in reserves:
            avant = float(reserves[nid])
            energie = avant + alpha * (cible - avant)
        else:
            pid = nid.removeprefix("pers:") if nid.startswith("pers:") else None
            legacy = acteurs_legacy.get(pid, {}).get("energie") if pid else None
            energie = float(legacy) if isinstance(legacy, (int, float)) else cible
        energie = max(0.0, min(ENERGIE_MAX, energie))
        reserves[nid] = energie
        resultat[nid] = energie
    for nid in list(reserves):
        if nid not in noeuds:
            del reserves[nid]
    graphe["mis_a_jour_a"] = present
    graphe["demi_vie_secondes"] = DEMI_VIE_ENERGIE
    if resultat:
        pic_id, pic = max(resultat.items(), key=lambda x: (x[1], x[0]))
        journaliser("energie.graphe", dt_s=round(dt_s, 3),
                    integration=round(alpha, 6), noeuds=len(resultat),
                    energises=sum(1 for x in resultat.values() if x >= ENERGIE_MIN),
                    total=round(sum(resultat.values()), 3),
                    pic=pic_id, maximum=round(pic, 3))
    return resultat


def mettre_a_jour_energies(etat, horloge, scores, energies_graphe,
                           disponibilites, noeuds, occupes):
    acteurs = etat.setdefault("acteurs", {})
    present = horloge["present_secondes"]
    nouvelle_vague = etat.get("source_cle") != horloge["source_cle"]
    if nouvelle_vague:
        etat["source_cle"] = horloge["source_cle"]
    eligibles = []
    # UN ECART SILENCIEUX N'EST PAS UN ECART, C'EST UNE DISPARITION. Le verrou
    # de disponibilite a tenu 32 acteurs sur 64 hors du classement sans ecrire
    # une ligne : rien dans le journal ne disait que Criston etait gele, et la
    # regie a lu « le monde tourne par le bas » la ou il fallait lire « la
    # moitie du casting n'est pas presentee ». On compte desormais les ecartes.
    ecartes = collections.Counter()
    for nid, disponible in disponibilites.items():
        n = noeuds.get(nid) or {}
        pid = nid.removeprefix("pers:")
        if pid in occupes:
            continue
        if n.get("etat") != "actif":
            ecartes["dormant"] += 1
            continue
        if n.get("condition") in ("prisonnier", "otage"):
            ecartes["captif"] += 1
            continue
        score = max(0.0, min(1.0, scores.get(nid, 0.0)))
        a = acteurs.setdefault(pid, {"energie": 0.0, "activations": 0})
        # Projection de compatibilite pour l'admin. L'autorite est desormais
        # l'overlay ``graphe.noeuds``, pas cette fiche d'acteur.
        a["energie"] = float(energies_graphe.get(nid, 0.0))
        a["mis_a_jour_a"] = present
        a["importance"] = score
        a["disponible_a"] = disponible
        if present >= disponible:
            eligibles.append((a["energie"], score, pid, a))
        else:
            ecartes["pas_encore_disponible"] += 1
    eligibles.sort(key=lambda x: (-x[0], -x[1], x[2]))
    journaliser("energie.classement", classes=len(eligibles),
                personnes=len(disponibilites), **dict(ecartes))
    return eligibles

