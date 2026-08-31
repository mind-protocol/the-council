# -*- coding: utf-8 -*-
# PRESENCE_QUARTIER — le quartier du joueur, les creux de la journee, la CLI.
#
# La seconde moitie de l'ancien scripts/presence.py (lot 2) : le rayon en
# minutes de marche autour du joueur (docs/boucle-acteurs.md), les creux
# communs entre deux journees, la sortie lisible et le main de la commande.
# La carte des pas, les exceptions datees et la resolution minute par minute
# vivent dans presence.py, qui reexporte d'ici.
import json, io, os, sys, heapq  # noqa: F401 — le meme socle que presence.py

from etat.expose import tables  # LA PORTE de etat/ (lecture seule ici)
from temps.presence import (
    Chateau, PEREMPTION, RAYON_MINUTES, absolu, bande_precedente, charger, date_monde, exception_valide, heure, joueurs, modele_de, ou_est, piece_de_bande, resoudre)
# --------------------------------------------------- le quartier du joueur
#
# Un acteur ne se déplace, ne pense et ne travaille que dans le quartier d'un
# joueur. Hors quartier, il ne bouge pas : pas de chemin, pas de bande, pas de
# position par défaut — sa dernière position connue reste ce qu'elle est. Ce
# qui continue hors quartier, ce sont les ÉCHÉANCES : une horloge de plan qui
# tombe se produit quand même. Le quartier gèle la position, jamais le
# calendrier.
#
# Deux conditions, jamais une : la composante connexe D'ABORD, la durée
# ensuite. Sans le test d'îlot, un saut nu à coût 0 fait entrer tout le reste
# du monde — mesuré ce jour : trente-cinq personnes à 0 minute de la reine,
# la moitié de la cour verte comprise. Le rayon ne mordra que le jour où le
# château grandira ; l'îlot mord tout de suite.
#
# Le quartier se recalcule à chaque fois. Il n'est jamais stocké.

def ancres():
    """Les sièges qui ancrent le quartier, CHACUN À SON HEURE.

    Deux façons d'ancrer : être OCCUPÉ (la mesure de occupation.py), ou
    déclarer `laisser_faire: true` dans etat/joueurs.json — le laisser faire
    PERMANENT, décidé le 31.8 pour la reine : personne ne s'assoit, la machine
    la joue comme un absent, mais le monde fin (déplacements, creux, pensées)
    continue de se calculer autour d'elle. Sans cette ancre : aucun siège
    occupé, quartier vide, personne ne pense — un monde d'horloges sans
    intériorité, ce qui n'est pas ce qu'on veut observer.

    `monde.date` porte l'horloge la moins avancée (ce jour : 390, quand la
    reine est à 422 et Aurore à 1077). Résoudre tout le monde là-dessus rend
    None pour les trois sièges occupés, dont les positions sont datées du
    futur : le quartier serait vide et personne ne penserait. Chaque siège
    définit donc son quartier à SON présent, et le quartier est leur union.
    """
    horloges = tables.lire("horloges.json", {}) or {}
    defaut = date_monde()
    chateau = Chateau(tables.lire("chemins.json", {}))
    out = []
    for x in tables.lire("joueurs.json", []) or []:
        if not isinstance(x, dict) or not (x.get("occupe")
                                           or x.get("laisser_faire")):
            continue
        pid = x.get("personnage_id")
        if not pid or x.get("regie"):
            continue          # la régie n'a pas de corps : elle n'ancre rien
        quand = horloges.get(pid) or defaut
        ou = resoudre(quand).get(pid)
        if not (ou and ou.get("salle")):
            continue
        # UNE ANCRE HORS TOPOLOGIE N'ANCRE RIEN, ET SE TAIT. La scène pose le
        # joueur dans une salle que `chemins.json` ignore (le grenier du bourg,
        # une soupente) : son îlot est None, plus personne ne « se touche » avec
        # lui, et son quartier se vide sans que rien ne le dise. On le porte
        # donc dans la liste avec son défaut nommé, pour que `--quartier` et
        # `tick.py --verifier` le crient au lieu de rendre une salle déserte.
        out.append({"qui": pid, "salle": ou["salle"], "quand": quand,
                    "lieu": ou.get("lieu"),
                    "hors_plan": not chateau.connait(ou["salle"])})
    return out


def quartier(rayon=RAYON_MINUTES):
    """Qui est à portée d'un joueur, et par quel siège — l'union des quartiers.

    Rend {"ancres": [...], "dedans": {pid: {...}}, "dehors": {pid: motif}}.
    Un motif de rejet est toujours nommé : `ilot` (une autre ville), `loin`
    (trop de minutes), `hors-plan` (salle absente de chemins.json), `nulle-part`
    (position non résolue). On ne laisse jamais tomber quelqu'un en silence.
    """
    routines, chemins, presence = charger()
    chateau = Chateau(chemins)
    points = ancres()
    dedans, dehors = {}, {}
    if not points:
        return {"ancres": [], "dedans": {}, "dehors": {},
                "vide": "aucun siege occupe ou en laisser-faire n'a de position resolue"}

    vus = {}
    for a in points:
        for pid, ou in resoudre(a["quand"]).items():
            vus.setdefault(pid, {})[a["qui"]] = ou

    for pid, par_ancre in vus.items():
        meilleur, motif = None, "nulle-part"
        for a in points:
            ou = par_ancre.get(a["qui"])
            if not ou or not ou.get("salle"):
                continue
            if not chateau.connait(ou["salle"]):
                motif = "hors-plan" if motif == "nulle-part" else motif
                continue
            if not chateau.se_touchent(a["salle"], ou["salle"]):
                motif = "ilot" if motif in ("nulle-part", "hors-plan") else motif
                continue
            minutes = chateau.duree(a["salle"], ou["salle"])
            if minutes > rayon:
                motif = "loin"
                continue
            if meilleur is None or minutes < meilleur["minutes"]:
                meilleur = {"salle": ou["salle"], "etat": ou.get("etat"),
                            "source": ou.get("source"), "minutes": minutes,
                            "par": a["qui"], "quand": a["quand"]}
        if meilleur:
            dedans[pid] = meilleur
        else:
            dehors[pid] = motif
    return {"ancres": points, "dedans": dedans, "dehors": dehors}


# ------------------------------------------------------------ les creux
#
# Ce que la routine NE DIT PAS. Une journée fait 1440 minutes ; on en retire le
# sommeil, les bandes fermées (`ferme: true` — rien ne peut l'en tirer) et les
# minutes passées dans les escaliers, déjà comptées par Dijkstra. Ce qui reste
# est le temps où l'homme peut penser, lire un registre, écouter quelqu'un.
#
# Un creux est un INTERVALLE, pas un total, et son `salle` compte autant que sa
# durée : une question posée à la roukerie n'a pas les mêmes sources qu'une
# question posée au bourg. Le creux dit où il est ; l'état dit ce qu'il y a là.
#
# Trois conséquences qui font le sujet :
#   - un homme dont la journée est pavée de bandes fermées ne pense pas ce
#     jour-là, quelle que soit sa force. C'est ça, le coût d'un mandat : on
#     l'occupe.
#   - un homme hors quartier n'a pas de journée, donc pas de creux, donc pas de
#     pensée. Le budget se resserre tout seul sur ce que le joueur peut
#     atteindre.
#   - les creux sont la SEULE ressource que les questions consomment. Plus de
#     « deux travaux par jour » posé à la main : la journée le dit elle-même.

MINUTES_MINIMUM = 15      # sous un quart d'heure, on n'a le temps de rien


def creux(pid, routines=None, chateau=None, minimum=MINUTES_MINIMUM):
    """Les intervalles libres de sa journée : [{de, a, salle, minutes}].

    Le dortoir est fermé d'office — on ne pense pas en dormant, et une bande de
    sommeil qu'on laisserait ouverte donnerait à chacun huit heures de réflexion
    gratuite. Sans fiche de routine, la réponse est [] : pas de journée, pas de
    creux. On ne comble pas par un modèle plausible (voir `--verifier`).
    """
    if routines is None:
        routines, chemins, _ = charger()
        chateau = chateau or Chateau(chemins)
    # UN JOUEUR N'A PAS D'EMPLOI DU TEMPS, donc pas de creux à mesurer. Rhaenyra
    # porte une fiche `reine` dont personne ne se sert : `ou_est` la court-
    # circuite déjà. La compter ici la classerait parmi ceux qu'on dépêche pour
    # penser à sa place — c'est le joueur qui pense, et il n'a pas de budget.
    if pid in joueurs():
        return []
    fiche, modele = modele_de(routines, pid)
    if not modele:
        return []
    bandes = modele.get("bandes") or []
    out = []
    for i, b in enumerate(bandes):
        de, a = b.get("de", 0), b.get("a", 1440)
        piece = piece_de_bande(b, fiche, modele)
        if piece.get("suit"):
            continue                        # une ombre n'a pas de journée à elle
        # Le dortoir est fermé D'OFFICE mais pas de force : `ferme: false` le
        # rouvre. Le cas qui l'impose est le captif, dont la journée entière est
        # une bande `@dortoir` — sa cellule, pas son sommeil. Un homme aux fers
        # n'a rien d'autre que du temps, et le lui retirer serait le seul
        # endroit du jeu où l'emprisonnement rendrait quelqu'un plus occupé.
        ferme = b.get("ferme")
        if ferme is None:
            ferme = (b.get("salle") == "@dortoir")
        if ferme:
            continue
        salle = piece.get("salle")
        if not salle:
            continue
        # Les minutes de marche se paient en tête de bande : il n'est pas
        # disponible tant qu'il est dans l'escalier.
        avant = bande_precedente(routines, pid, de) or piece
        trajet = chateau.duree(avant.get("salle"), salle) \
            if chateau.se_touchent(avant.get("salle"), salle) else 0
        debut = de + trajet
        if a - debut >= minimum:
            out.append({"de": debut, "a": a, "salle": salle,
                        "minutes": a - debut,
                        "pourquoi": b.get("pourquoi")})
    return out


# ------------------------------------------------------------------ sortie

def noms():
    d = {}
    for p in tables.lire("personnages.json", []) or []:
        d[p.get("id")] = p.get("nom")
    return d


def dire(ou):
    if ou["etat"] == "arrete":
        return "%-22s (%s)" % (ou.get("salle") or "?", ou["source"])
    # Une ombre interrogée seule n'a pas encore de corps : `--audit` appelle
    # `ou_est` sans la troisième passe de `resoudre`, qui est celle qui recopie
    # la position du suivi. On le dit au lieu de tomber sur une clef absente.
    if ou["etat"] == "suit":
        return "suit %-17s (ombre, corps non resolu ici)" % ou.get("suit", "?")
    return "en chemin : %s -> %s, passe %s, arrive dans %d min" % (
        ou["de"], ou["vers"], ou["salle"], ou["arrive_dans"])


def main():
    args = sys.argv[1:]
    routines, chemins, presence = charger()
    chateau = Chateau(chemins)

    # --json : tout le château à cette minute, brut, pour qui n'est pas un
    # terminal. Le serveur s'en sert pour /presence — il lisait jusqu'ici
    # l'instantané `resolu` figé par la dernière poussée de flux, et un homme
    # n'était donc jamais en marche entre deux items. La position se calcule,
    # elle ne se stocke pas : c'est vrai ici aussi.
    if "--json" in args:
        quand = date_monde()
        # `--quand annee.lune.jour.minute` : l'heure d'un SIÈGE, pas celle du
        # monde. `monde.date` n'est que le minimum des fronts ; servir celle-là
        # à un joueur en avance le montrerait au château d'hier.
        if "--quand" in args:
            a, l, j, m = args[args.index("--quand") + 1].split(".")
            quand = {"annee": int(a), "lune": int(l), "jour": int(j), "minute": int(m)}
        elif "--a" in args:
            j, m = args[args.index("--a") + 1].split(":")
            quand = dict(quand, jour=int(j), minute=int(m))
        io.open(1, "w", encoding="utf-8", closefd=False).write(
            json.dumps({"date": quand, "gens": resoudre(quand)}, ensure_ascii=False))
        return 0

    if "--chemin" in args:
        i = args.index("--chemin")
        a, b = args[i + 1], args[i + 2]
        etapes = chateau.chemin(a, b)
        print(" -> ".join("%s (%d)" % (s, m) for s, m in etapes))
        print("%d minutes" % etapes[-1][1])
        return 0

    if "--chercher" in args:
        # Ce que coûte VRAIMENT « faites-le venir » : le page descend, l'homme
        # remonte. C'est la `duree` a poser sur l'item, et la raison pour
        # laquelle un conseil attend.
        quand = date_monde()
        pid = args[args.index("--chercher") + 1]
        ou_moi = resoudre(quand).get(tables.lire("journal.json", {})
                                     .get("personnage_joueur_id") or "")
        ici = args[args.index("--depuis") + 1] if "--depuis" in args else \
            (ou_moi or {}).get("salle")
        ou = resoudre(quand).get(pid)
        if not (ou and ici):
            print("On ne sait pas ou est %s, ou d'ou vous le faites chercher." % pid)
            return 1
        la = ou["salle"]
        aller, retour = chateau.duree(ici, la), chateau.duree(la, ici)
        print("%s est a %s (%s)." % (noms().get(pid, pid), la, ou["etat"]))
        print("Le page : %d min pour y aller. L'homme : %d min pour venir." %
              (aller, retour))
        print("Il est devant vous dans %d minutes." % (aller + retour))
        return 0

    if "--quartier" in args:
        N = noms()
        q = quartier()
        if q.get("vide"):
            print("QUARTIER VIDE — %s." % q["vide"])
            print("Personne ne pense, personne ne bouge. C'est un bug d'etat,")
            print("pas une situation : verifiez horloges.json et presence.json.")
            return 1
        print("Ancres — un siege occupe, son heure, sa salle :")
        for a in q["ancres"]:
            print("  %-20s %5s  %s%s" % (
                N.get(a["qui"], a["qui"]), heure(a["quand"]["minute"]),
                a["salle"],
                "   << HORS PLAN : ce siege n'atteint personne. Ajoute cette "
                "salle a chemins.json." if a.get("hors_plan") else ""))
        dedans = sorted(q["dedans"].items(), key=lambda kv: kv[1]["minutes"])
        print("\nDANS LE QUARTIER — %d personnes :" % len(dedans))
        for pid, d in dedans:
            print("  %3d min  %-24s %-22s (par %s)" % (
                d["minutes"], N.get(pid, pid), d["salle"], d["par"]))
        from collections import Counter
        print("\nDEHORS — %d personnes : %s" % (
            len(q["dehors"]),
            ", ".join("%s×%d" % (m, n)
                      for m, n in Counter(q["dehors"].values()).most_common())))
        for pid, m in sorted(q["dehors"].items(), key=lambda kv: kv[1]):
            print("  %-10s %s" % (m, N.get(pid, pid)))
        return 0

    if "--creux" in args:
        pid = args[args.index("--creux") + 1]
        c = creux(pid)
        if not c:
            print("%s n'a pas de creux — pas de fiche de routine, ou une journee"
                  " entierement fermee." % noms().get(pid, pid))
            return 1
        print("%s — %d creux, %d minutes libres :"
              % (noms().get(pid, pid), len(c), sum(x["minutes"] for x in c)))
        for x in c:
            print("  %5s -> %5s  %-22s %4d min%s" % (
                heure(x["de"]), heure(x["a"]), x["salle"], x["minutes"],
                "  (%s)" % x["pourquoi"] if x.get("pourquoi") else ""))
        return 0

    quand = date_monde()
    if "--a" in args:
        j, m = args[args.index("--a") + 1].split(":")
        quand = dict(quand, jour=int(j), minute=int(m))

    N = noms()
    if "--ou" in args:
        pid = args[args.index("--ou") + 1]
        print("%s — la journee du %d:%s" % (N.get(pid, pid), quand["jour"], "*"))
        for mn in range(0, 1440, 30):
            ou = ou_est(pid, dict(quand, minute=mn), routines, chateau, presence)
            print("  %5s  %s" % (heure(mn), dire(ou) if ou else "(inconnu)"))
        return 0

    if "--audit" in args:
        t = absolu(quand)
        per = routines.get("peremption_minutes", PEREMPTION)
        print("Audit de presence.json au %d:%d (%s)\n" %
              (quand["jour"], quand["minute"], heure(quand["minute"])))
        sans_routine, perimes = [], []
        for pid, ov in sorted(presence.items()):
            a_routine = pid in (routines.get("gens") or {})
            age = (t - absolu(ov["date"])) if ov.get("date") else None
            # Une exception datée du futur n'est pas périmée : la scène est en
            # avance sur l'horloge du monde, ce qui arrive et se rattrape seul.
            if not exception_valide(ov, t, per) and (age is None or age >= 0):
                perimes.append((pid, ov, age, a_routine))
            if not a_routine:
                sans_routine.append(pid)
        if perimes:
            print("PERIMES — poses il y a longtemps, plus personne ne les bouge :")
            for pid, ov, age, a_routine in perimes:
                ou = ou_est(pid, quand, routines, chateau, presence, per)
                print("  %-20s %-16s depuis %s  =>  %s" % (
                    N.get(pid, pid), ov.get("salle"),
                    ("%dh" % (age // 60)) if age is not None else "toujours",
                    dire(ou) if ou else "(inconnu)"))
        if sans_routine:
            print("\nSANS ROUTINE — rien ne les fera bouger :")
            for pid in sans_routine:
                print("  %s" % N.get(pid, pid))
        inconnues = set()
        for pid in sorted(set(presence) | set(routines.get("gens") or {})):
            ou = ou_est(pid, quand, routines, chateau, presence, per)
            if ou and ou.get("salle") and not chateau.connait(ou["salle"]):
                inconnues.add(ou["salle"])
        if inconnues:
            print("\nHORS TOPOLOGIE — salles absentes de chemins.json : %s"
                  % ", ".join(sorted(inconnues)))
        if not (perimes or sans_routine or inconnues):
            print("Rien a signaler.")
        return 0

    print("Peyredragon, jour %d, %s\n" % (quand["jour"], heure(quand["minute"])))
    par_salle = {}
    for pid, ou in resoudre(quand).items():
        # UNE EXCEPTION PEUT POSER QUELQU'UN HORS DU PLAN. `clerc-coll` est au
        # « grenier du bourg », qui existe dans la fiction et pas dans
        # etat/chemins.json : sa salle est nulle. On ne s'en cache pas — on
        # l'affiche sous son lieu, avec la mention. Trier None avec du texte
        # faisait tomber la regie entiere pour un seul homme mal range.
        cle = ou["salle"] if ou["etat"] == "arrete" else \
            "~ %s -> %s" % (ou["de"], ou["vers"])
        if not cle:
            cle = "(hors plan) %s" % (ou.get("lieu") or "?")
        par_salle.setdefault(cle, []).append((N.get(pid, pid), ou))
    for cle in sorted(par_salle):
        gens = par_salle[cle]
        print("  %-24s %s" % (cle, ", ".join(n for n, _ in gens)))
    return 0



