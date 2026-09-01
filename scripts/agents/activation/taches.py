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
                                     DEMI_VIE_ENERGIE, ETAT,
                                     lire_json, journaliser)
from agents.activation.horloges import appliquer_polarites_horloge
from agents.activation.fatigue import (instant_fictionnel_secondes,
                                       mesurer_fatigue)
from agents.activation.graphe import (tache_active, tache_executable,
                                      tache_disponible,
                                      acteur_en_repos, empreinte_tache,
                                      continuite_tache, energie_de_tache,
                                      clusters_par_lieu,
                                      normaliser_par_cluster, calendrier)

def choisir_tache(acteur, noeuds, aretes, adj, energies, etat=None,
                  present=0.0, amorcage_lieu=None, sur_verrous=False):
    """Tache active la plus proche de l'acteur.

    ``tient`` est l'assignation canonique d'une action. Une tache tenue par un
    autre personnage ne doit jamais etre recuperee par simple proximite dans le
    graphe. L'assignation definit l'ensemble eligible ; la distance decide,
    puis l'energie ne departage que deux taches a distance egale.
    """
    etat = etat or {}

    def unite_active(n):
        if sur_verrous and n.get("genre") != "verrou":
            return False
        return tache_active(n, inclure_verrous=sur_verrous)

    def unite_executable(nid):
        if not unite_active(noeuds.get(nid) or {}):
            return False
        return tache_executable(
            nid, noeuds, inclure_verrous=sur_verrous)
    titulaires = collections.defaultdict(set)
    affectations_declarees = set()

    # Un office ou un moyen est lui-meme tenu par des personnes. Une action
    # peut donc etre attribuee a O04 sans nommer Tobb et Nesse a chaque ligne.
    # On resout d'abord ce cran intermediaire, avant d'attribuer les taches.
    porteurs_intermediaires = collections.defaultdict(set)
    for a in aretes:
        if a.get("flou") or a.get("nature") != "tient":
            continue
        de, vers = a.get("de"), a.get("vers")
        if de not in noeuds or vers not in noeuds:
            continue
        if (noeuds[de].get("genre") in ("office", "moyen")
                and noeuds[vers].get("genre") == "personne"):
            porteurs_intermediaires[de].add(vers)
        elif (noeuds[vers].get("genre") in ("office", "moyen")
              and noeuds[de].get("genre") == "personne"):
            porteurs_intermediaires[vers].add(de)

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
            tache, porteur = None, None
            if unite_active(noeuds[de]):
                tache, porteur = de, vers
            elif unite_active(noeuds[vers]):
                tache, porteur = vers, de
            if tache:
                genre_porteur = noeuds[porteur].get("genre")
                if genre_porteur == "personne":
                    titulaires[tache].add(porteur)
                    affectations_declarees.add(tache)
                elif (a.get("nature") == "tient"
                      and genre_porteur in ("office", "moyen", "vacant")):
                    affectations_declarees.add(tache)
                    titulaires[tache].update(
                        porteurs_intermediaires.get(porteur) or ())

    # Celles qu'un `tient` renvoie vers un noeud `vacant` : l'ecriteau
    # « personne ne tient ceci » est une donnee, pas un trou.
    a_designer = set()
    for a in aretes:
        if a.get("flou") or a.get("nature") != "tient":
            continue
        de, vers = a.get("de"), a.get("vers")
        if de in noeuds and vers in noeuds:
            if noeuds[vers].get("genre") == "vacant":
                a_designer.add(de)
            elif noeuds[de].get("genre") == "vacant":
                a_designer.add(vers)

    # UNE ACTION A DESIGNER RETOMBE SUR LE PROPRIETAIRE DE SON AFFAIRE.
    #
    # Rendre le noeud `vacant` infranchissable (voir la frontiere du parcours
    # plus bas) a ferme la fuite : plus personne ne ramasse la charge d'autrui
    # en passant par l'ecriteau de sa vacance. Mais ca laissait ces actions
    # sans personne du tout — elles n'avancaient plus jamais, et c'est troquer
    # une injustice contre un immobilisme.
    #
    # Une action « a designer » n'est pourtant pas sans maitre : elle est DANS
    # une affaire, et une affaire a quelqu'un qui la porte. On le derive du
    # tissu au lieu de le declarer — le proprietaire est celui qui tient le
    # plus d'actions du meme `ou`. Mesure du 31.8 : `71026` (plan:hightower)
    # retombe sur OTTO, qui en tient quatre ; `76028` (plan:baratheon) sur
    # MESTRE HALLIS, qui en tient trois. Les deux sont justes, et aucun des
    # deux n'aurait pu la ramasser par distance.
    #
    # C'est une retombee, pas une assignation : elle ne s'ecrit nulle part, et
    # le jour ou quelqu'un est vraiment designe, son arete `tient` la remplace.
    proprietaires = {}
    par_affaire = {}
    for nid, porteurs in titulaires.items():
        ou = (noeuds.get(nid) or {}).get("ou")
        if not isinstance(ou, str) or ":" not in ou:
            continue
        compte = par_affaire.setdefault(ou, {})
        for p in porteurs:
            compte[p] = compte.get(p, 0) + 1
    for ou, compte in par_affaire.items():
        proprietaires[ou] = max(sorted(compte), key=lambda p: (compte[p], p))
    for nid, n in noeuds.items():
        if titulaires.get(nid) or not unite_active(n):
            continue
        if nid not in a_designer:
            continue
        maitre = proprietaires.get(n.get("ou"))
        if maitre:
            titulaires[nid] = {maitre}

    def appartient_ou_vacante(nid):
        # A Braavos, un verrou est un chantier collectif explicite. Un verrou
        # sans porteur n'est jamais une invitation implicite à toute la ville.
        if sur_verrous:
            return (nid in affectations_declarees
                    and acteur in titulaires.get(nid, set()))
        # Sans aucune affectation, le repli historique par proximite reste
        # permis. Mais une affectation explicite dont le titulaire n'a pas pu
        # etre resolu est un trou a reparer, pas une invitation a tous.
        if nid in affectations_declarees:
            return acteur in titulaires.get(nid, set())
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
        affectation_directe = bool(autre and a.get("nature") == "tient")
        if autre and unite_executable(autre) \
                and appartient_ou_vacante(autre) \
                and tache_disponible(etat, autre, noeuds, present) \
                and (float(energies.get(autre, 0.0)) >= ENERGIE_MIN
                     or (amorcage_lieu and affectation_directe)):
            # Lors de l'amorcage d'une ville, l'acteur recoit le seuil de
            # depart avant que son sous-graphe ait accumule de l'energie. Une
            # action qu'il tient explicitement doit heriter de cette prise ;
            # sinon la boucle ignore l'assignation et fabrique une tache
            # generique. `poursuit` ne beneficie pas de ce passage : seule
            # l'arete canonique `tient` autorise ce raccord direct.
            # L'assignation explicite passe avant le simple fait que l'acteur
            # poursuit une etape de son intention.
            directes.append((0 if affectation_directe else 1, autre,
                              affectation_directe))
    if directes:
        directes.sort(key=lambda x: (x[0], -float(energies.get(x[1], 0.0)), x[1]))
        _priorite_affectation, nid, affectation_directe = directes[0]
        return {"id": nid, "quoi": noeuds[nid].get("quoi") or nid,
                "genre": noeuds[nid].get("genre"), "distance": 1,
                "chemin": [acteur, nid], "creee": False,
                "affectation_directe": affectation_directe}

    file = collections.deque([(acteur, [acteur])])
    vus = {acteur}
    candidats = []
    while file:
        ici, chemin = file.popleft()
        d = len(chemin) - 1
        if (ici != acteur and unite_executable(ici)
                and appartient_ou_vacante(ici)
                and tache_disponible(etat, ici, noeuds, present)
                and float(energies.get(ici, 0.0)) >= ENERGIE_MIN):
            candidats.append((d, -float(energies.get(ici, 0.0)), ici, chemin))
            continue
        # DEUX FRONTIERES, ET LA SECONDE A COUTE UNE ELECTION.
        #
        # Une autre PERSONNE : ses propres taches ne sont pas le prolongement
        # implicite de celles de l'acteur active.
        #
        # Un noeud VACANT : c'est l'ecriteau qui dit « personne ne tient
        # ceci ». On n'herite pas d'une charge en passant par la marque de sa
        # vacance. Mesure du 31.8 : le tissu n'a qu'un seul noeud de ce genre,
        # `a_designer`, mais il porte 46 voisins et DEUX actions actives
        # pendantes — et 54 personnes sur 114 l'atteignent. Il servait donc de
        # moyeu a toutes les taches orphelines : au cycle a sec, Aurore
        # Inchauspe (un siege de joueur vacant) et Aldon Hask convergeaient
        # tous deux sur la meme action 76028, atteinte a distance 4 par ce
        # chemin exact — pers:aurore -> moyen:M18 -> piece:10025 ->
        # vacant:a_designer -> action:76028. Une action a designer se DESIGNE ;
        # elle ne se ramasse pas en passant.
        if ici != acteur and noeuds[ici].get("genre") in ("personne", "vacant"):
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

    # Le front Braavos ne fabrique plus une tâche générique et ne retombe pas
    # sur une action personnelle : sans verrou explicitement porté, personne
    # n'est réveillé. Le verrou est le contexte de travail, pas une étiquette
    # ajoutée après l'élection d'une action.
    if sur_verrous:
        return None

    pid = acteur.removeprefix("pers:")
    intentions = lire_json(os.path.join(ETAT, "intentions.json"), [])
    tete = next((t for t in intentions if t.get("personnage_id") == pid), {})
    quoi = (tete.get("intention") or
            next((o.get("but") for o in (noeuds[acteur].get("objectifs") or [])
                  if isinstance(o, dict) and o.get("but")), None))
    source = "intentions.json:intention"
    if not quoi and amorcage_lieu \
            and noeuds[acteur].get("lieu_id") == amorcage_lieu:
        quoi = ("Commencer par explorer sa situation à Braavos, relire sa "
                "chambre et les documents de sa maison, puis écrire ses "
                "premiers objectifs et la prochaine action vérifiable.")
        source = "activation:amorcage-braavos"
    if not quoi:
        return None
    ident = hashlib.sha1((pid + "\0" + quoi).encode("utf-8")).hexdigest()[:12]
    return {"id": "activation:" + pid + ":" + ident, "quoi": quoi,
            "genre": "tache-proposee", "distance": 0,
            "chemin": [acteur], "creee": True,
            "source": source}


def mettre_a_jour_energie_graphe(etat, horloge, scores, noeuds, adj,
                                 polarites, front=None):
    """Integre et persiste l'energie de chaque node du graphe.

    ``scores`` est la force instantanee produite par la topologie. L'energie,
    elle, vit dans l'overlay runtime et converge vers cette force avec une
    demi-vie de cinq minutes. Un score disparu fait decroitre la reserve ; aucun
    cycle ne la remet a zero.
    """
    graphe_racine = etat.setdefault("graphe", {"noeuds": {}, "liens": {}})
    # Deux fronts peuvent porter des horloges incompatibles. Partager leur
    # reserve faisait notamment lire a Braavos le dernier instant de Westeros
    # (600 s) alors que son propre present valait 0 s : dt tombait a zero et
    # les nouvelles connexions ne recevaient jamais leur energie. Chaque front
    # explicite possede donc son overlay ; l'absence de front conserve le
    # stockage historique de Westeros.
    if front:
        graphe = graphe_racine.setdefault("fronts", {}).setdefault(
            front, {"noeuds": {}, "liens": {}})
    else:
        graphe = graphe_racine
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
            # Un overlay neuf part de sa propre physique. Reprendre ici la
            # jauge legacy d'un autre front donnait 0 a un ancien actif de
            # Westeros et la cible courante aux nouveaux venus : l'historique
            # inversait alors le classement de Braavos.
            energie = (cible if front else
                       float(legacy) if isinstance(legacy, (int, float))
                       else cible)
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


def amorcer_sources_energie(etat, energies_graphe, source_ids, front,
                            present):
    """Donne une seule impulsion à chaque nouvelle source d'un front.

    Le registre persistant empêche une boucle répétée de recréer de l'énergie.
    Une personne déjà amorcée ne reçoit pas une seconde impulsion lorsqu'elle
    prend un cahier supplémentaire : c'est le porteur qui est source, pas le
    nombre d'affaires accumulées sur son nom.
    """
    registre = etat.setdefault("amorces_sources", {}).setdefault(front, {})
    graphe = etat.setdefault("graphe", {})
    if front:
        overlay = graphe.setdefault("fronts", {}).setdefault(
            front, {"noeuds": {}, "liens": {}})
        reserves = overlay.setdefault("noeuds", {})
    else:
        reserves = graphe.setdefault("noeuds", {})
    nouvelles = []
    for pid in sorted(set(source_ids or [])):
        if pid in registre:
            continue
        nid = "pers:" + pid
        valeur = max(float(energies_graphe.get(nid, 0.0)), ENERGIE_MIN)
        reserves[nid] = valeur
        energies_graphe[nid] = valeur
        registre[pid] = {"amorce_a": round(float(present), 3)}
        nouvelles.append(pid)
        journaliser("energie.source.amorcee", front=front, acteur=pid,
                    valeur=round(valeur, 3))
    return nouvelles


def mettre_a_jour_energies(etat, horloge, scores, energies_graphe,
                           disponibilites, noeuds, occupes,
                           maintenant_mur=None, lieu_force=None,
                           sources_energie=None):
    acteurs = etat.setdefault("acteurs", {})
    fatigue_acteurs = etat.setdefault("fatigue_acteurs", {})
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
        est_source = bool(sources_energie and pid in sources_energie)
        source_du_lieu = bool(
            est_source and lieu_force and n.get("lieu_id") == lieu_force)
        brute = float(energies_graphe.get(nid, 0.0))
        energise_du_lieu = bool(
            lieu_force and n.get("lieu_id") == lieu_force and brute > 0.0)
        if n.get("etat") != "actif" and not (
                source_du_lieu or energise_du_lieu):
            ecartes["dormant"] += 1
            continue
        if n.get("condition") in ("prisonnier", "otage"):
            ecartes["captif"] += 1
            continue
        score = max(0.0, min(1.0, scores.get(nid, 0.0)))
        a = acteurs.setdefault(pid, {"energie": 0.0, "activations": 0})
        # La reserve topologique reste intacte. La disponibilite effective
        # baisse seulement selon le calcul recent et le retard fictionnel.
        instant_fiction = instant_fictionnel_secondes(pid, horloge)
        mesure = mesurer_fatigue(
            fatigue_acteurs.setdefault(pid, {}), instant_fiction,
            maintenant_mur)
        # Le lieu ne crée aucune énergie. Il autorise seulement une source
        # déclarée (siège joueur ou porteur d'affaire) à sortir de l'état
        # dormant pour accomplir son premier réveil.
        if source_du_lieu:
            a["source_energie"] = lieu_force
        else:
            a.pop("source_energie", None)
        a.pop("amorcage_lieu", None)
        a["energie_brute"] = brute
        a["energie"] = brute * mesure["facteur_total"]
        a["charge_compute_minutes"] = mesure["charge_compute_minutes"]
        a["ecart_heures"] = mesure["ecart_heures"]
        a.pop("avance_heures", None)
        a["facteur_compute"] = mesure["facteur_compute"]
        a["facteur_heures"] = mesure["facteur_heures"]
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


