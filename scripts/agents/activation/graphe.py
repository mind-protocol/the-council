# -*- coding: utf-8 -*-
"""GRAPHE — l'adjacence du tissu, les sources de charge, la diffusion
d'importance, les clusters par lieu, le calendrier d'une source, et l'etat
d'une tache (active, disponible, en repos).
"""
import collections
import hashlib
import heapq
import json
import math
import re

from agents.activation.socle import (AMORTISSEMENT, TOURS_DIFFUSION,
                                     ENERGIE_MAX, ENERGIE_MIN,
                                     GENRES_RELAIS, ETATS_TERMINES,
                                     REPOS_ACTEUR_SECONDES,
                                     REPOS_PAIRE_SECONDES,
                                     secondes_monde_pour_energie,
                                     journaliser)
from agents.activation.horloges import minute_absolue

def adjacence(noeuds, aretes):
    adj = {nid: [] for nid in noeuds}
    paires = set()
    for i, a in enumerate(aretes):
        de, vers = a.get("de"), a.get("vers")
        if a.get("flou") or a.get("virtuel") or de == vers:
            continue
        if de not in noeuds or vers not in noeuds:
            continue
        cle = tuple(sorted((de, vers)))
        if cle not in paires:
            paires.add(cle)
            adj[de].append(vers)
            adj[vers].append(de)
    return adj


def sources_de_charge(noeuds, aretes, evaluation):
    """Ancres et masses des motifs DECIDER utilises par la page admin."""
    entrants = collections.defaultdict(list)
    sortants = collections.defaultdict(list)
    for a in aretes:
        if a.get("de") in noeuds and a.get("vers") in noeuds:
            entrants[a["vers"]].append(a)
            sortants[a["de"]].append(a)
    motifs = []
    for g in evaluation.get("goulots") or []:
        if g.get("noeud") in noeuds:
            motifs.append((g["noeud"], g.get("demandes") or 1))
    for d in evaluation.get("desequilibres") or []:
        if d.get("noeud") in noeuds:
            motifs.append((d["noeud"], d.get("consommateurs") or 1))
    critique = (evaluation.get("critique") or [])[:1]
    if critique:
        chaine = critique[0].get("chaine") or []
        if chaine and chaine[0].get("id") in noeuds:
            motifs.append((chaine[0]["id"], len(chaine)))
    for nid in noeuds:
        contradictions = [a for a in entrants[nid] + sortants[nid]
                          if a.get("nature") == "contredit"]
        if len(contradictions) >= 2:
            motifs.append((nid, len(contradictions)))
    for nid, n in noeuds.items():
        if n.get("genre") != "action":
            continue
        tient = [a for a in sortants[nid] if a.get("nature") == "tient"]
        if (not tient or all(noeuds.get(a.get("vers"), {}).get("genre") == "vacant"
                            for a in tient)
                or all(a.get("flou") or a.get("vers") not in noeuds
                       for a in tient)):
            motifs.append((nid, 1))
    for nid in noeuds:
        sorties = [a for a in sortants[nid]
                   if a.get("nature") in ("ouvre", "realise")]
        if len(sorties) >= 3:
            motifs.append((nid, len(sorties)))
    charge = collections.defaultdict(float)
    for nid, score in motifs:
        charge[nid] += 1.0 + math.log1p(max(1, score))
    return charge


def multiplicateurs(noeuds):
    """Le multiplicateur de flux de chaque noeud, CENTRE SUR 1.

    LA TOPOLOGIE REND TOUT EGAL PARCE QUE TOUT EST CUMULATIF. Le graphe sait
    dire ce qui tient a quoi ; il ne sait pas dire ce que l'aventure PERD si
    un but n'est pas atteint. La note d'importance des etats cibles (ecrite le
    31.8, sur 100, 158 lignes de 64 volumes) dit exactement cela, et c'est
    pour ca qu'elle entre ici : deux instruments, deux questions.

    NORMALISE A 1 AUTOUR DE LA MOYENNE — chaque note divisee par la moyenne
    des notes ECRITES. La masse totale du flux reste donc de l'ordre de ce
    qu'elle etait : un etat cible a 100 tire environ deux fois plus qu'un
    etat moyen, un etat a 20 environ deux fois moins, et l'ensemble ne gonfle
    pas. Sans ce centrage, noter les buts reviendrait a multiplier tout le
    graphe par un facteur arbitraire.

    UNE CASE VIDE VAUT 1, JAMAIS 0. Dix-sept lignes n'ont pas de note, par
    choix — « une case vide plutot qu'une note bluffee ». Les compter pour
    nulles les effacerait du monde ; elles restent neutres.
    """
    # UNE NOTE NE COUPE JAMAIS UN RELAIS. L'echelle ecrite commence a 1 —
    # « 1-19 : plomberie, on peut y renoncer » — et zero n'en fait pas
    # partie. Un noeud a x0.00 ne relaie plus RIEN : il devient un cul-de-sac
    # qui tranche tout ce qui passait par lui, ce qui n'est pas « on peut y
    # renoncer » mais « cela n'existe plus ». Un seul noeud etait dans ce cas
    # le 31.8 (21000, « Doute populaire ») ; on plancher a 1, soit x0.02 —
    # negligeable, jamais annulant.
    notes = [max(1, n["importance"]) for n in noeuds.values()
             if isinstance(n, dict) and isinstance(n.get("importance"), int)]
    if not notes:
        return {}
    moyenne = float(sum(notes)) / len(notes)
    if moyenne <= 0:
        return {}
    return {nid: max(1, n["importance"]) / moyenne
            for nid, n in noeuds.items()
            if isinstance(n, dict) and isinstance(n.get("importance"), int)}


def diffuser(sources, adj, noeuds, mults=None):
    total = sum(sources.values())
    if total <= 0:
        return {}
    if mults is None:
        mults = multiplicateurs(noeuds)
    src = {k: v / total for k, v in sources.items() if k in adj}
    x = dict(src)
    for _ in range(TOURS_DIFFUSION):
        y = collections.defaultdict(float)
        retenue = 0.0
        for nid, valeur in x.items():
            liens = adj.get(nid) or []
            genre = noeuds.get(nid, {}).get("genre")
            if not liens or (nid not in src and genre not in GENRES_RELAIS):
                retenue += valeur
                continue
            # LE MULTIPLICATEUR PORTE SUR CE QUE LE NOEUD RELAIE, pas sur ce
            # qu'il recoit : un but qui compte pousse plus loin ce qui le
            # sert, et l'importance descend donc a tout ce qui pend a lui.
            # Sur ce qu'il recoit, elle ne ferait qu'engraisser une case.
            part = AMORTISSEMENT * valeur * mults.get(nid, 1.0) / len(liens)
            for autre in liens:
                y[autre] += part
        retour = AMORTISSEMENT * retenue + (1.0 - AMORTISSEMENT)
        for nid, valeur in src.items():
            y[nid] += retour * valeur
        x = dict(y)
    return x


def importance(noeuds, aretes, evaluation, source_id, occupes=(),
               source_ids=None):
    adj = adjacence(noeuds, aretes)
    # Un front peut avoir plusieurs foyers d'initiative. Westeros conserve le
    # siège joueur unique ; Braavos ajoute les personnes qui portent
    # réellement une affaire. Chaque personne compte une fois, quel que soit
    # le nombre de cahiers qu'elle tient : les affaires ouvrent une source,
    # elles ne permettent pas de multiplier artificiellement sa puissance.
    ids = set(source_ids or [source_id])
    sources = {"pers:" + pid: 1.0 for pid in ids
               if "pers:" + pid in noeuds}
    if not sources:
        sources = {"pers:" + source_id: 1.0}
    mults = multiplicateurs(noeuds)   # calcule une fois, servi aux deux
    atteinte = diffuser(sources, adj, noeuds, mults)
    charge = sources_de_charge(noeuds, aretes, evaluation)
    pression = diffuser(charge, adj, noeuds, mults)
    max_a = max(atteinte.values() or [1e-12])
    max_p = max(pression.values() or [1e-12])
    scores = {}
    for nid in noeuds:
        a = atteinte.get(nid, 0.0) / max_a
        p = pression.get(nid, 0.0) / max_p
        scores[nid] = math.sqrt(a * p)
    # ON NE NORMALISE PAS SUR UN SIEGE OCCUPE. La source de la diffusion a une
    # atteinte de 1.0 par construction : le personnage joueur est donc TOUJOURS
    # le pic du graphe, il rafle les 100 points du plafond, et il ne peut rien
    # en depenser puisqu'il n'est jamais elu (voir `pid in occupes` plus bas).
    # Le meilleur acteur reel plafonnait ainsi a 28 sur une echelle de 100.
    # On cale donc l'echelle sur le plus fort noeud ACTIVABLE.
    exclus = {"pers:" + p for p in occupes if p}
    # Les sieges occupes gardent leur rang relatif mais ne debordent pas :
    # au-dela de 1.0 ils fausseraient les polarites et le plafond d'energie.
    return normaliser_par_cluster(scores, charge, noeuds, adj, exclus), adj


def energie_de_tache(tache, energies_graphe, energie_acteur):
    """Prix energetique d'une tache, y compris celle qu'on vient de creer.

    UNE TACHE CREEE N'EST PAS DANS LE TISSU. Son id (`activation:<pid>:<hash>`)
    n'a donc aucune entree dans `energies_graphe`, qui rendait 0.0 — soit moins
    que ENERGIE_MIN, soit un rejet systematique en `tache_sous_seuil`. La
    branche de secours de `choisir_tache`, ecrite exactement pour les acteurs
    trop peu modelises pour avoir une tache atteignable, etait donc morte : les
    seuls qui en dependaient ne pouvaient jamais etre elus. Une intention vaut
    son homme — c'est la sienne, elle ne peut pas peser moins que lui.
    """
    if tache.get("creee") or tache.get("affectation_directe"):
        return float(energie_acteur)
    return float(energies_graphe.get(tache["id"], 0.0))


def clusters_par_lieu(noeuds, adj):
    """Rattache chaque noeud a un lieu, seme par les seules personnes.

    Les 107 noeuds `personne` portent tous un `lieu_id` ecrit a la main ; aucun
    des 1742 autres n'en a. On propage donc depuis eux, le plus proche gagnant,
    sur l'adjacence de la diffusion.

    UN NOEUD A EGALE DISTANCE DE DEUX LIEUX N'APPARTIENT A AUCUN. Departager
    par l'id, comme on le faisait, donne un resultat stable et faux : le noeud
    generique `unite:corbeau` s'est retrouve attribue a l'Ile-aux-Pinces, et
    les neuf lignes de cout qui le citent ont fait passer Celtigar pour la
    maison dont nos affaires dependent le plus. Une commune est une commune :
    on la laisse sans lieu plutot que de lui en inventer un.
    """
    # LE VOTE SE NORMALISE PAR LE NOMBRE DE GRAINES. Sans cela Peyredragon,
    # qui compte 58 personnes contre 2 a Lamarck, gagne toutes les egalites et
    # avale les noeuds de ses voisins : Lamarck tombait de 76 a 15. Le poids
    # d'un lieu ne doit pas dependre du nombre de gens qu'on y a ecrits.
    graines = collections.Counter(
        n["lieu_id"] for n in noeuds.values()
        if n.get("genre") == "personne" and n.get("lieu_id"))
    distances = {}
    lieux = collections.defaultdict(collections.Counter)
    file = []
    for nid, n in noeuds.items():
        if n.get("genre") == "personne" and n.get("lieu_id"):
            distances[nid] = 0
            lieux[nid][n["lieu_id"]] = 1.0 / graines[n["lieu_id"]]
            heapq.heappush(file, (0, nid))
    vus = set()
    while file:
        distance, ici = heapq.heappop(file)
        if ici in vus:
            continue
        vus.add(ici)
        for voisin in adj.get(ici) or []:
            candidat = distance + 1
            connue = distances.get(voisin)
            if connue is None or candidat < connue:
                distances[voisin] = candidat
                lieux[voisin] = collections.Counter(lieux[ici])
                heapq.heappush(file, (candidat, voisin))
            elif candidat == connue and voisin not in vus:
                lieux[voisin] += lieux[ici]
    # Le plus represente parmi les sources a egale distance l'emporte ; une
    # egalite franche laisse le noeud sans lieu. Le tout-ou-rien, lui, retirait
    # son lieu a un noeud sur cinq et vidait Lamarck de 76 a 15.
    resultat = {}
    for nid, compte in lieux.items():
        if not compte:
            continue
        ordonne = compte.most_common(2)
        if len(ordonne) > 1 and ordonne[0][1] == ordonne[1][1]:
            continue
        resultat[nid] = ordonne[0][0]
    return resultat


def normaliser_par_cluster(scores, charge, noeuds, adj, exclus):
    """Chaque lieu se mesure a son propre pic, amorti par ce qu'on y a ecrit.

    Une normalisation globale demandait « qui est le plus presse du monde »,
    et la reponse etait toujours chez nous : la pression sort des motifs
    DECIDER, qui n'existent que la ou le graphe est detaille. Peyredragon
    porte 1319 noeuds et 75 motifs ; Villevieille en porte 12 et zero. On
    demande donc desormais « qui est le plus presse CHEZ LUI ».

    L'amortissement en log(motifs) evite le bug symetrique : sans lui, une
    flaque a une seule affaire verrait sa tete normalisee a 1.0 et rivaliser
    avec le chateau du joueur. Un lieu ou rien n'est ecrit reste a zero, et
    c'est juste — il n'y a rien a y faire.
    """
    lieux = clusters_par_lieu(noeuds, adj)
    motifs = collections.Counter(lieux[nid] for nid in charge if nid in lieux)
    if not motifs:
        return scores
    motifs_max = max(motifs.values())
    reference = math.log1p(motifs_max)
    pics = collections.defaultdict(float)
    for nid, valeur in scores.items():
        lieu = lieux.get(nid)
        if lieu is not None and nid not in exclus:
            pics[lieu] = max(pics[lieu], valeur)
    resultat = {}
    for nid, valeur in scores.items():
        lieu = lieux.get(nid)
        pic = pics.get(lieu, 0.0)
        if lieu is None or pic <= 0:
            resultat[nid] = 0.0
            continue
        amorti = math.log1p(motifs.get(lieu, 0)) / reference if reference else 0.0
        resultat[nid] = min(1.0, (valeur / pic) * amorti)
    journaliser("importance.clusters", lieux=len(pics),
                motifs_max=motifs_max,
                actifs=sum(1 for v in resultat.values() if v > 0))
    return resultat


def calendrier(noeuds, aretes, evaluation, source_id):
    """Qui a le droit d'agir chez lui — et la reponse est : tout le monde.

    CETTE FONCTION RENDAIT UNE INTERDICTION D'AGIR, ET ELLE ETAIT INVERSEE.
    Elle datait la disponibilite d'un acteur a `min(jours_restants)` de ses
    etapes en cours, comparee au present de la vague (une seconde reelle = une
    seconde de monde). Or `jours_restants` dit COMBIEN DE TEMPS une affaire va
    courir, pas a quelle date l'homme se libere : un homme a qui l'on avait
    ecrit un vrai plan se trouvait interdit d'agir pendant toute la duree de ce
    plan, tandis qu'un homme sans plan — ou dont toutes les etapes sont des
    postures permanentes (`jours_restants: null`, jamais decomptees) — restait
    disponible en permanence. La physique recompensait donc exactement le
    defaut de modelisation.

    Mesure le 10 aout sur l'etat courant, present de vague a 1,7 jour : 32
    acteurs actifs sur 64 etaient geles, dont Criston (20 j), Aegon II (5 j),
    Larys (4 j), Daemon (3 j), Corlys (2 j) — 37 % de la masse d'importance du
    graphe, et zero activation. Les vingt-neuf activations d'Alys Grive et de
    Rulf Corne ne recompensaient pas leur importance : elles recompensaient le
    fait que personne ne leur avait ecrit d'horloge.

    Dix autres actifs n'entraient meme pas dans le classement, faute d'etre
    joignables par le relais de diffusion depuis le PJ. C'etait la meme faute
    d'un cran plus loin, et le commentaire de la version precedente la nommait
    deja pour le delai du courrier : la portee d'une NOUVELLE n'est jamais la
    faculte d'AGIR. Un homme agit chez lui, qu'on puisse lui ecrire ou non.

    Ce qui espace reellement les activations reste en place et suffit :
    `REPOS_ACTEUR_SECONDES` apres chaque tour, la rotation qui reserve les
    acteurs deja passes, `ENERGIE_ACTIVATION_MIN` qui ecarte ceux a qui le
    graphe ne donne pas de quoi agir, et la continuite de tache. Les etapes,
    elles, restent decomptees par `tick.py` — c'est son travail, pas celui-ci.
    """
    del aretes, evaluation, source_id  # ni la route ni la pression n'autorisent
    return {nid: 0.0 for nid, n in noeuds.items()
            if n.get("genre") == "personne"}

def tache_active(n, inclure_verrous=False):
    genres = ("action", "action_personnelle", "etape")
    if inclure_verrous:
        genres += ("verrou",)
    if n.get("genre") not in genres:
        return False
    etat = re.sub(r"[*_]+", "", str(n.get("etat") or "")).strip().lower()
    return not any(mot in etat for mot in ETATS_TERMINES)


def tache_accomplie(n):
    """Vrai seulement si une dependance a produit ce qu'elle promettait.

    `abandonnee` et `annulee` ferment une tache, mais n'accomplissent pas les
    taches qui en dependent. Elles rendent donc `tache_active` faux sans
    rendre cette fonction vraie.
    """
    if not isinstance(n, dict):
        return False
    etat = re.sub(r"[*_]+", "", str(n.get("etat") or "")).strip().lower()
    return etat.startswith(("fait", "fini", "termin", "accompli"))


def tache_executable(nid, noeuds, inclure_verrous=False):
    """Active, et toutes ses dependances sont reellement accomplies."""
    n = noeuds.get(nid) or {}
    if not tache_active(n, inclure_verrous=inclure_verrous):
        return False
    dependances = n.get("depend_de") or []
    if isinstance(dependances, str):
        dependances = [dependances]
    for dependance in dependances:
        did = str(dependance)
        if n.get("genre") == "etape" and not did.startswith("etape:"):
            did = "etape:" + did
        if not tache_accomplie(noeuds.get(did)):
            return False
    return True


def empreinte_tache(n):
    """Revision stable du noeud canonique, sans les champs runtime de la regie."""
    if not isinstance(n, dict):
        return None
    stable = {k: n.get(k) for k in (
        "id", "genre", "quoi", "etat", "source", "jours_restants",
        "depend_de", "realise", "office", "titulaire", "preuve") if k in n}
    brut = json.dumps(stable, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))
    return hashlib.sha1(brut.encode("utf-8")).hexdigest()


def continuite_tache(etat, nid, noeuds):
    """Retourne l'overlay seulement si le noeud canonique n'a pas change."""
    continuite = (etat.get("continuite") or {}).get(nid)
    if not isinstance(continuite, dict):
        return None
    if continuite.get("empreinte_canonique") != empreinte_tache(noeuds.get(nid)):
        return None
    return continuite


def repos_perime(present, reprendre_a, repos_max):
    """Un repos qui ne peut pas avoir ete pose dans le repere courant.

    LE BUG QUE CECI REPARE. `present_secondes` se compte depuis l'horloge du
    siege principal, et `reprendre_a` vaut `present + REPOS` au moment ou on
    l'estampe. Mais l'origine BOUGE : quand le siege principal rattrape le
    front — Rhaenyra passant du 129.3.30 au 129.4.2 —, l'ecart s'effondre et le
    present RECULE. Mesure du 129.4.3 : present tombe de ~151 700 a 5 154, et
    quatorze acteurs se sont retrouves en repos jusqu'a ~152 000, soit 41
    heures de monde dans le futur. Ils etaient geles pour toujours, l'origine
    ne faisant qu'avancer — Gerardys a 100 d'energie n'etait plus jamais elu,
    et la boucle tournait sur les sept memes tetes.

    Le repos legitime le plus long est `REPOS_PAIRE_SECONDES`. Au-dela de
    `present + repos_max`, la valeur ne peut pas venir de la regle appliquee
    dans ce repere-ci : c'est un reste d'un repere anterieur, et on le tient
    pour echu. On ne raccourcit aucun repos vrai — seulement ceux qu'aucune
    horloge d'aujourd'hui ne saurait produire.
    """
    try:
        reprendre_a = float(reprendre_a)
    except (TypeError, ValueError):
        return True
    return reprendre_a > float(present) + float(repos_max)


def tache_disponible(etat, nid, noeuds, present):
    continuite = continuite_tache(etat, nid, noeuds)
    if not continuite:
        return True
    if continuite.get("suspendue"):
        return False
    reprendre_a = continuite.get("reprendre_a") or 0.0
    if repos_perime(present, reprendre_a, REPOS_PAIRE_SECONDES):
        return True
    return float(present) >= float(reprendre_a)


def acteur_en_repos(etat, pid, present):
    dernier = ((etat.get("repos") or {}).get("acteurs") or {}).get(pid)
    if not isinstance(dernier, (int, float)):
        return False
    if repos_perime(present, dernier, REPOS_ACTEUR_SECONDES):
        return False
    return float(present) < float(dernier)

