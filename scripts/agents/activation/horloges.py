# -*- coding: utf-8 -*-
"""HORLOGES — la minute absolue, l'horloge directe du monde, et les
polarites d'horloge des acteurs.
"""
import collections
import heapq
import os
import time

from etat.expose import tables
from temps.expose import occupation

from agents.activation.socle import (TRANSFERT_HORLOGE_MAX, ENERGIE_MAX,
                                     ETAT, ETAT_BOUCLE, journaliser,
                                     lire_json)

def minute_absolue(d):
    if not isinstance(d, dict) or d.get("annee") is None:
        return None
    return (((int(d["annee"]) * 12 + int(d["lune"]) - 1) * 30
             + int(d["jour"]) - 1) * 1440 + int(d.get("minute") or 0))


def date_civile_acteur(pid, horloge, horloges=None):
    """Rend l'heure civile locale de l'acteur au debut de son activation.

    Les horloges persistantes appartiennent aux sieges. La selection a deja
    calcule de quel siege l'acteur herite et le porte dans ``horloge_pj`` ; un
    siege activable garde toutefois sa propre horloge en priorite. Le temps
    ecoule depuis l'ancrage de la vague s'ajoute a cette heure locale, sans
    ajouter une seconde fois l'ecart entre le siege principal et le front.
    """
    if horloges is None:
        horloges = lire_json(os.path.join(ETAT, "horloges.json"), {})
    horloges = horloges if isinstance(horloges, dict) else {}
    horloge = horloge if isinstance(horloge, dict) else {}
    ancres = (pid, horloge.get("horloge_pj"), horloge.get("front_id"),
              horloge.get("source_id"))
    ancre = next((horloges.get(a) for a in ancres
                  if a and isinstance(horloges.get(a), dict)), None)
    if ancre is None or minute_absolue(ancre) is None:
        return None

    present = float(horloge.get("present_secondes") or 0.0)
    base = float(horloge.get("base_secondes") or 0.0)
    ecoulees = max(0.0, present - base)
    minute = minute_absolue(ancre) + int(ecoulees // 60.0)
    jour_absolu, minute_du_jour = divmod(minute, 1440)
    mois_absolu, jour_zero = divmod(jour_absolu, 30)
    annee, lune_zero = divmod(mois_absolu, 12)
    return {
        "annee": annee,
        "lune": lune_zero + 1,
        "jour": jour_zero + 1,
        "minute": minute_du_jour,
    }


def horloge_directe(ancien, maintenant=None, source_force=None,
                    front_force=None):
    """Rend le present explicite de la vague depuis son origine PJ.

    Le mur mesure le compute, jamais la fiction. Seuls les lots reussis
    augmentent `commis_secondes`; attendre dix minutes devant un processus ne
    fait donc plus passer dix minutes dans le monde.
    """
    maintenant = time.time() if maintenant is None else maintenant
    horloges = lire_json(os.path.join(ETAT, "horloges.json"), {})
    sieges = lire_json(os.path.join(ETAT, "joueurs.json"), [])
    if isinstance(sieges, dict):
        sieges = sieges.get("joueurs") or sieges.get("sieges") or []
    # ON NE LIT PAS LE DRAPEAU, ON MESURE. `occupe` est un cache, et il a menti
    # pendant deux jours : quatre sieges a `true`, deux d'entre eux plus joues
    # par personne — donc exclus de cette file, donc endormis. Ici on demande
    # au disque qui respire (`scripts/occupation.py`), et l'on n'ecrit rien :
    # `prevoir_activations` doit pouvoir appeler cette fonction sans effet.
    releve = occupation.mesures()
    assis = {m["personnage_id"] for m in releve if m["occupe"]}
    # UN SIEGE VACANT SANS TETE N'EST PAS ACTIVABLE, ET C'EST UNE GARDE DURE.
    # La regle « vacant -> une tete » est un invariant de `tick.py --verifier`,
    # c'est-a-dire un constat apres coup. Mesuree, l'occupation peut basculer
    # toute seule pendant qu'on ne regarde pas — et si l'on ne s'en protegeait
    # pas ici, un siege dont personne n'a ecrit la tete se retrouverait elu et
    # joue par la machine sans qu'aucun texte ne dise ce qu'il veut. On le
    # laisse donc EXCLU, comme s'il etait encore assis, jusqu'a ce qu'on lui
    # ait ecrit sa tete.
    sans_tete = {m["personnage_id"] for m in releve
                 if not m["occupe"] and not m["a_tete"]}
    for pid in sorted(sans_tete):
        journaliser("sieges.vacant_sans_tete", acteur=pid,
                    note="exclu de la file tant qu'il n'a pas de tete")
    occupes = [s for s in sieges if s.get("personnage_id") in assis]
    # DEUX QUESTIONS DIFFERENTES, et il ne faut pas les confondre :
    #   — QUI EST EXCLU de la file d'activation ? Les assis, et eux seuls.
    #     C'est ce qu'on rend a la fin, et ca peut tres bien etre vide.
    #   — D'OU PART LE TEMPS ? Il faut une horloge d'origine et un front,
    #     sinon la vague n'a pas de present et la boucle s'arrete net.
    # Tant que `occupe` etait un drapeau jamais rebascule, la seconde question
    # avait toujours une reponse. Mesure, elle peut ne plus en avoir : deux
    # joueurs qui vont se coucher, et deux heures plus tard PLUS AUCUN siege
    # n'est assis. La boucle levait alors « front occupe absent » et le monde
    # cessait de tourner la nuit — un defaut tout neuf, cree par la reparation.
    # On retombe donc sur le roster entier pour l'HORLOGE seulement : le temps
    # continue de partir du siege principal, et les sieges vacants restent
    # activables puisqu'ils ne sont pas dans le jeu rendu.
    roster_horloge = [s for s in sieges if s.get("personnage_id")]
    pour_horloge = occupes or roster_horloge
    # Un front local explicite reste son ancre même lorsque son siège devient
    # vacant : l'occupation décide qui peut être activé, pas quelle ville la
    # vague est en train de faire vivre.
    principal = next((s for s in roster_horloge
                      if s.get("personnage_id") == source_force), None)
    if principal is None:
        principal = next((s for s in pour_horloge
                          if s.get("role") == "principal"),
                         pour_horloge[0] if pour_horloge else None)
    source_id = principal and principal.get("personnage_id")
    source_min = minute_absolue(horloges.get(source_id)) if source_id else None
    candidats_front = list(pour_horloge)
    if principal and principal not in candidats_front:
        candidats_front.append(principal)
    fronts = [(minute_absolue(horloges.get(s.get("personnage_id"))), s)
              for s in candidats_front]
    fronts = [(m, s) for m, s in fronts if m is not None]
    if source_min is None or not fronts:
        raise RuntimeError("horloge du siege principal ou front occupe absent")
    front = next((s for _m, s in fronts
                  if s.get("personnage_id") == front_force), None)
    if front is None:
        front_min, front = max(fronts, key=lambda x: x[0])
    else:
        front_min = minute_absolue(horloges.get(front.get("personnage_id")))
    base = max(0.0, float(front_min - source_min) * 60.0)
    source_cle = "%s:%s" % (source_id, source_min)
    front_cle = "%s:%s" % (front.get("personnage_id"), front_min)
    h = (ancien or {}).get("horloge") or {}
    if h.get("source_cle") == source_cle and h.get("front_cle") == front_cle:
        commis = max(0.0, float(h.get("commis_secondes") or 0.0))
    else:
        commis = 0.0
    present = base + commis
    return {
        "source_id": source_id,
        "source_minute": source_min,
        "source_cle": source_cle,
        "front_id": front.get("personnage_id"),
        "front_minute": front_min,
        "front_cle": front_cle,
        "base_secondes": base,
        "commis_secondes": commis,
        "present_secondes": present,
        "lu_a": maintenant,
    }, ({s.get("personnage_id") for s in occupes} | sans_tete)


def commettre_lot_horloge(horloge, durees_reussies):
    """Avance une vague parallele de sa duree la plus longue, jamais la somme."""
    durees = [max(0.0, float(x or 0.0)) for x in durees_reussies]
    avance = max(durees) if durees else 0.0
    horloge["commis_secondes"] = (
        max(0.0, float(horloge.get("commis_secondes") or 0.0)) + avance)
    horloge["present_secondes"] = (
        float(horloge.get("base_secondes") or 0.0)
        + horloge["commis_secondes"])
    return avance


def polarites_horloge_acteurs(noeuds, adj):
    """Emet si l'horloge locale est en avance, absorbe si elle est en retard.

    Un acteur herite d'abord de l'horloge du siege qui le declare dans ``pnj``.
    Les autres personnes heritent de l'ancre PJ la plus proche dans le graphe.
    La moyenne ne porte que sur les sieges occupes et disposant d'une horloge.
    """
    horloges = lire_json(os.path.join(ETAT, "horloges.json"), {})
    sieges = lire_json(os.path.join(ETAT, "joueurs.json"), [])
    if isinstance(sieges, dict):
        sieges = sieges.get("joueurs") or sieges.get("sieges") or []
    assis = occupation.occupes()
    actifs = []
    for siege in sieges:
        pid = siege.get("personnage_id")
        minute = minute_absolue(horloges.get(pid)) if pid else None
        if pid in assis and minute is not None:
            actifs.append((pid, float(minute), siege))
    if not actifs:
        return {}, {"moyenne_minute": None, "ecart_max_minutes": 0.0}

    moyenne = sum(x[1] for x in actifs) / len(actifs)
    ecart_max = max(abs(x[1] - moyenne) for x in actifs) or 1.0
    attribution = {}
    file = []
    for pid, minute, siege in actifs:
        ancres = [pid] + list(siege.get("pnj") or [])
        for acteur in ancres:
            nid = "pers:" + acteur
            candidat = (0, pid, minute)
            if nid in noeuds and (nid not in attribution or
                                  candidat < attribution[nid]):
                attribution[nid] = candidat
                heapq.heappush(file, (0, pid, minute, nid))

    lieux_bruts = lire_json(os.path.join(ETAT, "lieux.json"), [])
    if isinstance(lieux_bruts, dict):
        lieux_bruts = lieux_bruts.get("lieux") or []
    lieux = {x.get("id"): x for x in lieux_bruts
             if isinstance(x, dict) and x.get("id")}

    def distance_physique(lieu_a, lieu_b):
        if not lieu_a or not lieu_b:
            return None
        if lieu_a == lieu_b:
            return 0.0
        a, b = lieux.get(lieu_a) or {}, lieux.get(lieu_b) or {}
        da, db = a.get("jours_de_pr"), b.get("jours_de_pr")
        if not isinstance(da, (int, float)) or not isinstance(db, (int, float)):
            return None
        return abs(da - db) if da == 0 or db == 0 else da + db

    # Hors rattachement explicite, le lieu prime : un acteur de Port-Real vit
    # sur le front de Port-Real, meme si une affaire le relie fortement a la reine.
    for nid, n in noeuds.items():
        if n.get("genre") != "personne" or nid in attribution:
            continue
        candidats = []
        for pid, minute, siege in actifs:
            pj = noeuds.get("pers:" + pid) or {}
            distance = distance_physique(n.get("lieu_id"), pj.get("lieu_id"))
            if distance is not None:
                priorite = 0 if siege.get("role") == "principal" else 1
                candidats.append((distance, priorite, pid, minute))
        if candidats:
            _distance, _priorite, pid, minute = min(candidats)
            attribution[nid] = (0, pid, minute)
            heapq.heappush(file, (0, pid, minute, nid))
    while file:
        distance, pid, minute, ici = heapq.heappop(file)
        if attribution.get(ici) != (distance, pid, minute):
            continue
        for voisin in adj.get(ici) or []:
            candidat = (distance + 1, pid, minute)
            if voisin not in attribution or candidat < attribution[voisin]:
                attribution[voisin] = candidat
                heapq.heappush(file, (distance + 1, pid, minute, voisin))

    resultat = {}
    for nid, n in noeuds.items():
        if n.get("genre") != "personne" or nid not in attribution:
            continue
        distance, pid, minute = attribution[nid]
        ecart = minute - moyenne
        mode = "emet" if ecart > 0.001 else "absorbe" if ecart < -0.001 else "neutre"
        resultat[nid] = {
            "mode": mode,
            "intensite": min(1.0, abs(ecart) / ecart_max),
            "ecart_minutes": ecart,
            "horloge_pj": pid,
            "distance_ancre": distance,
        }
    comptes = collections.Counter(x["mode"] for x in resultat.values())
    journaliser("energie.polarites_horloge",
                moyenne_minute=round(moyenne, 3),
                ecart_max_minutes=round(ecart_max, 3),
                emetteurs=comptes.get("emet", 0),
                absorbeurs=comptes.get("absorbe", 0),
                neutres=comptes.get("neutre", 0))
    return resultat, {
        "moyenne_minute": moyenne,
        "ecart_max_minutes": ecart_max,
    }


def appliquer_polarites_horloge(cibles, polarites, adj):
    """Transfere l'energie cible sur les aretes, sans en creer ni en detruire."""
    propositions = []
    for nid, polarite in sorted(polarites.items()):
        mode = polarite["mode"]
        intensite = float(polarite["intensite"])
        voisins = sorted(v for v in (adj.get(nid) or []) if v in cibles)
        if mode == "neutre" or intensite <= 0 or not voisins:
            continue
        fraction = TRANSFERT_HORLOGE_MAX * intensite
        if mode == "emet":
            part = cibles.get(nid, 0.0) * fraction / len(voisins)
            propositions.extend((nid, voisin, part) for voisin in voisins)
        else:
            propositions.extend(
                (voisin, nid, cibles.get(voisin, 0.0) * fraction / len(voisins))
                for voisin in voisins)

    sorties = collections.defaultdict(float)
    entrees = collections.defaultdict(float)
    for source, cible, montant in propositions:
        sorties[source] += montant
        entrees[cible] += montant
    echelles_source = {
        nid: min(1.0, cibles.get(nid, 0.0) / total) if total > 0 else 1.0
        for nid, total in sorties.items()
    }
    echelles_cible = {
        nid: min(1.0, max(0.0, ENERGIE_MAX - cibles.get(nid, 0.0)) / total)
        if total > 0 else 1.0
        for nid, total in entrees.items()
    }
    variations = collections.defaultdict(float)
    transfere = 0.0
    for source, cible, montant in propositions:
        effectif = montant * min(echelles_source[source], echelles_cible[cible])
        variations[source] -= effectif
        variations[cible] += effectif
        transfere += effectif
    resultat = {
        nid: max(0.0, min(ENERGIE_MAX, valeur + variations.get(nid, 0.0)))
        for nid, valeur in cibles.items()
    }
    journaliser("energie.transfert_horloge", transfere=round(transfere, 3),
                propositions=len(propositions), acteurs=len(polarites))
    return resultat

