# -*- coding: utf-8 -*-
# Où se tient chacun DANS le château, à la minute près — et par où il y va.
#
# Le problème que ceci corrige : `etat/presence.json` était un instantané. On y
# posait quelqu'un dans la grande salle le 20 à 17h, et il y était encore deux
# jours plus tard, debout, la nuit comprise. Rien ne le faisait bouger, parce
# que rien ne le savait en mouvement.
#
# La règle ici : LA POSITION NE SE STOCKE PAS, ELLE SE CALCULE.
#   - `etat/routines.json` donne à chacun sa journée, en bandes horaires. Une
#     bande n'est PAS une position : c'est une DESTINATION. À l'heure dite,
#     l'homme part vers cette salle.
#   - `etat/chemins.json` donne la topologie du château et le coût en minutes
#     de chaque pas. Le trajet se parcourt vraiment : entre deux salles, on est
#     dans l'escalier, et l'on peut y être croisé.
#   - `etat/presence.json` cesse d'être la vérité et devient une pile
#     d'EXCEPTIONS DATÉES : une scène pose quelqu'un quelque part, ça vaut le
#     temps que ça vaut (`jusqu_a`, ou la péremption), puis il repart de
#     lui-même vers sa routine — il ne clignote pas.
#
# Invariant : personne ne paraît dans une salle sans avoir traversé celles
# d'entre.
#
# Deux exceptions à la routine, et elles ne sont pas des cas particuliers : ce
# sont les bornes de ce que la simulation a le droit de décider.
#
#   1. UN JOUEUR N'A PAS D'EMPLOI DU TEMPS. Le personnage d'un joueur ne se
#      déplace QUE sur ce qu'une scène a constaté ; son exception ne périme
#      jamais et aucune bande horaire ne le tire ailleurs. Un PJ qu'un horaire
#      ramène à table est un PJ qu'on a pris à son joueur. Jamais constaté nulle
#      part = position inconnue, et on le dit (le navigateur retombe alors sur
#      ce que le flux lui montre) — on ne devine pas.
#
#   2. LA SALLE D'UN JOUEUR EST GELÉE. Tant qu'un joueur s'y tient, ceux que la
#      scène y a mis n'en repartent pas d'eux-mêmes, quelle que soit l'heure.
#      La scène possède la pièce. Sans cette règle, un conseiller s'éclipse au
#      milieu d'une phrase parce que sa bande a changé, et le joueur voit son
#      interlocuteur disparaître sans que personne l'ait décidé.
#
#   3. UNE OMBRE N'A PAS DE DESTINATION, ELLE A UN CORPS. Une fiche peut porter
#      `suit: <personnage_id>` avec le modèle `ombre` : la bande `@suit` ne
#      désigne alors aucune salle, et la position se RECOPIE de celle du suivi,
#      état compris — dans l'escalier avec lui s'il y est, et non arrêtée à
#      l'arrivée. Hors de cette bande (la nuit), l'ombre reprend son dortoir :
#      un coureur suit sa maîtresse du lever au coucher, pas jusque dans son
#      lit. Si le corps est introuvable, l'ombre l'est aussi — c'est la seule
#      réponse honnête, et non un repli sur un endroit plausible.
#
# D'où trois passes dans `resoudre`, dans cet ordre : les joueurs d'abord —
# c'est leur position qui dit quelles salles sont gelées —, puis tous les
# autres, puis les ombres, qui ont besoin que leur corps soit déjà posé. La
# troisième passe se répète quelques tours pour l'ombre d'une ombre, et
# s'arrête net : deux qui se suivraient l'un l'autre ne font pas tourner le
# moteur en rond, ils restent introuvables tous les deux.
#
# Usage :
#   python scripts/presence.py                  — l'état du château maintenant
#   python scripts/presence.py --a 22:380       — à telle heure (jour:minute)
#   python scripts/presence.py --ou rhaenyra    — une personne, sa journée
#   python scripts/presence.py --chemin a b     — le chemin et son coût
#   python scripts/presence.py --audit          — les fantômes de presence.json
import json, io, os, sys, heapq

racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JOURS_PAR_LUNE = 30
LUNES_PAR_AN = 12
PEREMPTION = 240          # une exception sans terme vaut un quart, puis lâche


# ------------------------------------------------------------------ lecture

def _lire(nom, defaut):
    try:
        return json.load(io.open(os.path.join(racine, "etat", nom),
                                 encoding="utf-8"))
    except Exception:
        return defaut


def charger():
    routines = _lire("routines.json", {})
    chemins = _lire("chemins.json", {})
    presence = (_lire("presence.json", {}) or {}).get("presence") or {}
    return routines, chemins, presence


def date_monde():
    m = _lire("monde.json", {})
    return m.get("date") or {"annee": 129, "lune": 1, "jour": 1, "minute": 0}


def absolu(d):
    """Une date du monde en minutes absolues. Calendrier : 12 lunes de 30 jours."""
    if not d:
        return None
    n = ((d.get("annee", 0) * LUNES_PAR_AN + d.get("lune", 1) - 1) * JOURS_PAR_LUNE
         + d.get("jour", 1) - 1)
    return n * 1440 + int(d.get("minute", 0) or 0)


def heure(minute):
    return "%dh%02d" % ((minute // 60) % 24, minute % 60)


# ------------------------------------------------------- la carte des pas

class Chateau(object):
    """Le graphe des salles : qui touche quoi, et en combien de minutes."""

    def __init__(self, chemins):
        self.alias = chemins.get("alias") or {}
        self.voisins = {}
        for a in chemins.get("aretes") or []:
            x, y, cout = self.vrai(a[0]), self.vrai(a[1]), int(a[2])
            self.voisins.setdefault(x, {})[y] = cout
            self.voisins.setdefault(y, {})[x] = cout

    def vrai(self, salle):
        """Résout les alias : `appartements` et `appartements-reine` sont une salle."""
        return self.alias.get(salle, salle)

    def connait(self, salle):
        return self.vrai(salle) in self.voisins

    def chemin(self, depart, arrivee):
        """Dijkstra. Retourne [(salle, minute d'arrivée), …], départ inclus à 0.

        Deux salles qu'aucune arête ne relie (le bourg d'un autre château, une
        salle de passage jamais inscrite) : on rend le saut nu, coût zéro. On ne
        ment pas sur un chemin qu'on ne connaît pas, on avoue qu'on ne le tient
        pas — c'est `--audit` qui le signale, pas la fiction qui le paie.
        """
        depart, arrivee = self.vrai(depart), self.vrai(arrivee)
        if depart == arrivee:
            return [(depart, 0)]
        if depart not in self.voisins or arrivee not in self.voisins:
            return [(depart, 0), (arrivee, 0)]
        vus, file, avant = {}, [(0, depart)], {}
        while file:
            cout, ici = heapq.heappop(file)
            if ici in vus:
                continue
            vus[ici] = cout
            if ici == arrivee:
                break
            for voisin, pas in self.voisins[ici].items():
                if voisin not in vus:
                    heapq.heappush(file, (cout + pas, voisin))
                    if voisin not in avant or cout + pas < vus.get(voisin, 1 << 30):
                        avant.setdefault(voisin, ici)
        if arrivee not in vus:
            return [(depart, 0), (arrivee, 0)]
        route, ici = [], arrivee
        while ici != depart:
            route.append(ici)
            ici = avant[ici]
        route.append(depart)
        route.reverse()
        etapes, t = [(depart, 0)], 0
        for i in range(1, len(route)):
            t += self.voisins[route[i - 1]][route[i]]
            etapes.append((route[i], t))
        return etapes

    def duree(self, depart, arrivee):
        return self.chemin(depart, arrivee)[-1][1]


# ---------------------------------------------------- la journée de chacun

def modele_de(routines, pid):
    fiche = (routines.get("gens") or {}).get(pid)
    if not fiche:
        return None, None
    modele = (routines.get("modeles") or {}).get(fiche.get("modele"))
    return fiche, modele


def piece_de_bande(bande, fiche, modele):
    """Résout @dortoir / @poste / @suit avec ce que la personne a en propre.

    `@suit` ne désigne pas un lieu mais QUELQU'UN : une ombre n'a pas de
    destination à elle, elle a un corps à suivre. On rend un marqueur que
    `resoudre` remplacera une fois la position du suivi connue.
    """
    salle = bande.get("salle")
    if salle == "@suit":
        cible = fiche.get("suit") or modele.get("suit")
        return {"suit": cible} if cible else {"salle": None, "lieu": None}
    for jeton, cle in (("@dortoir", "dortoir"), ("@poste", "poste")):
        if salle == jeton:
            p = fiche.get(cle) or modele.get(cle) or {}
            return {"salle": p.get("salle"), "lieu": p.get("lieu")}
    return {"salle": salle, "lieu": bande.get("lieu")}


def destination(routines, pid, minute_du_jour):
    """Où cette personne VEUT être à cette minute du jour, et depuis quand."""
    fiche, modele = modele_de(routines, pid)
    if not modele:
        return None, None
    bandes = modele.get("bandes") or []
    for b in bandes:
        if b.get("de", 0) <= minute_du_jour < b.get("a", 1440):
            return piece_de_bande(b, fiche, modele), b.get("de", 0)
    return (piece_de_bande(bandes[-1], fiche, modele), bandes[-1].get("de", 0)) \
        if bandes else (None, None)


def bande_precedente(routines, pid, debut):
    """La destination d'avant : c'est de là qu'il part."""
    fiche, modele = modele_de(routines, pid)
    bandes = (modele or {}).get("bandes") or []
    if not bandes:
        return None
    avant = [b for b in bandes if b.get("a", 1440) <= debut]
    b = avant[-1] if avant else bandes[-1]      # sinon la dernière de la veille
    return piece_de_bande(b, fiche, modele)


# ------------------------------------------------------- les exceptions

def joueurs():
    """Les personnages tenus par un JOUEUR — roster à deux, journal à un.

    Ils sont hors routine : un joueur n'a pas d'emploi du temps. Personne ne
    décide à sa place qu'il est l'heure de descendre manger.
    """
    ids = set()
    for x in _lire("joueurs.json", []) or []:
        if isinstance(x, dict) and x.get("personnage_id"):
            ids.add(x["personnage_id"])
    seul = (_lire("journal.json", {}) or {}).get("personnage_joueur_id")
    if seul:
        ids.add(seul)
    return ids


def exception_valide(ov, t, peremption):
    """Une exception de scène tient-elle encore à la minute t ?

    Sans `date`, elle est posée à la main et ne périme jamais (les fers, une
    consigne). Avec `jusqu_a`, elle tient jusque-là. Sinon elle vaut un quart,
    puis la personne repart vers sa journée.
    """
    if not ov:
        return False
    if not ov.get("date"):
        return True
    debut = absolu(ov["date"])
    if t < debut:
        return False        # elle n'a pas encore eu lieu : elle ne dit rien
    fin = absolu(ov.get("jusqu_a")) if ov.get("jusqu_a") else debut + peremption
    return t < fin


# ------------------------------------------------------- la résolution

def ou_est(pid, quand, routines, chateau, presence, peremption=PEREMPTION,
           pj=None, gele=None):
    """Où est cette personne à cette date — arrêtée quelque part, ou en chemin.

    Rend {salle, lieu, etat: "arrete"|"en-chemin", source, …}. En chemin :
    `de`, `vers`, `arrive_dans` (minutes), et `salle` = la dernière franchie,
    c'est-à-dire là où on le croiserait.
    """
    t = absolu(quand)
    minute_du_jour = t % 1440
    ov = presence.get(pid)

    # Une exception n'est pas un ORDRE, c'est une OBSERVATION : le flux constate
    # que l'homme a parlé dans cette pièce, donc il y est déjà — on ne le fait
    # pas marcher vers un endroit où on vient de le voir. Le chemin, lui, se
    # paie à la sortie : quand l'exception tombe, il repart de LÀ.
    # UN JOUEUR N'A PAS D'EMPLOI DU TEMPS. Sa position vient de ce que la scène
    # a constaté, et de rien d'autre : elle ne périme pas, et aucune routine ne
    # vient le déplacer. Un personnage joueur qu'un horaire ramène à table est
    # un personnage qu'on a pris à son joueur.
    pj = joueurs() if pj is None else pj
    if pid in pj:
        # Une observation ne vaut pas AVANT d'avoir eu lieu : interrogé sur une
        # heure antérieure, on ne rejoue pas le présent dans le passé. On ne
        # garde pas d'historique de position — donc on ne sait pas, et on le dit.
        if ov and (not ov.get("date") or t >= absolu(ov["date"])):
            return {"salle": chateau.vrai(ov.get("salle")), "lieu": ov.get("lieu"),
                    "etat": "arrete",
                    "source": "pose" if not ov.get("date") else "scene"}
        return None     # jamais constaté, ou pas encore : on ne devine pas

    if exception_valide(ov, t, peremption):
        return {"salle": chateau.vrai(ov.get("salle")), "lieu": ov.get("lieu"),
                "etat": "arrete", "source": "pose" if not ov.get("date") else "scene"}

    # LA SALLE D'UN JOUEUR EST GELÉE. Tant qu'un joueur s'y tient, ceux que la
    # scène y a mis n'en repartent pas d'eux-mêmes : la scène possède la pièce.
    # Sans cette règle, un conseiller s'éclipse au milieu d'une phrase parce que
    # son horaire dit qu'il est l'heure — et le joueur voit son interlocuteur
    # disparaître sans que personne l'ait décidé.
    if ov and gele and chateau.vrai(ov.get("salle")) in gele:
        return {"salle": chateau.vrai(ov.get("salle")), "lieu": ov.get("lieu"),
                "etat": "arrete", "source": "gelee"}

    but, debut = destination(routines, pid, minute_du_jour)
    source = "routine"
    # Une ombre ne marche pas vers un endroit : elle est où est son corps. On
    # ne calcule donc aucun chemin — `resoudre` recopiera la position du suivi,
    # état compris (dans l'escalier avec lui s'il y est).
    if but and but.get("suit"):
        return {"etat": "suit", "suit": but["suit"], "source": "ombre",
                "salle": None, "lieu": None}
    if not but:
        # Ni routine ni exception valide : on ne sait pas, et on le dit.
        if ov:
            return {"salle": chateau.vrai(ov.get("salle")), "lieu": ov.get("lieu"),
                    "etat": "arrete", "source": "perime"}
        return None
    parti = t - (minute_du_jour - debut)         # l'heure où la bande a commencé
    if minute_du_jour < debut:                   # bande de la veille
        parti -= 1440
    # Il part de sa dernière position connue : la pièce où la scène l'a laissé
    # si elle est plus récente que le début de la bande, sinon sa bande d'avant.
    fin_ov = None
    if ov and ov.get("date"):
        fin_ov = absolu(ov.get("jusqu_a")) if ov.get("jusqu_a") \
            else absolu(ov["date"]) + peremption
    if fin_ov is not None and parti < fin_ov <= t:
        origine = {"salle": ov.get("salle"), "lieu": ov.get("lieu")}
        parti = fin_ov
    else:
        origine = bande_precedente(routines, pid, debut) or but

    etapes = chateau.chemin(origine.get("salle"), but.get("salle"))
    total = etapes[-1][1]
    ecoule = t - parti
    if ecoule < 0:
        # Il n'est pas encore parti (exception datée du futur, bande mal bornée) :
        # il est là où il était.
        return dict(origine, etat="arrete", source=source)
    if ecoule >= total:
        return dict(but, salle=chateau.vrai(but.get("salle")),
                    etat="arrete", source=source)

    passees = [s for s, m in etapes if m <= ecoule]
    prochaine = [s for s, m in etapes if m > ecoule][0]
    return {"salle": passees[-1], "lieu": None, "etat": "en-chemin",
            "source": source, "de": etapes[0][0], "vers": but.get("salle"),
            "vers_lieu": but.get("lieu"), "prochaine": prochaine,
            "arrive_dans": total - ecoule}


def resoudre(quand=None, presence=None):
    """Tout le château à cette date. C'est la fonction que le reste appelle.

    `presence` permet de passer les exceptions qu'on tient en mémoire plutôt que
    celles du disque — `append_flux.py` les a sous la main avant de les écrire.
    """
    routines, chemins, du_disque = charger()
    presence = du_disque if presence is None else presence
    chateau = Chateau(chemins)
    quand = quand or date_monde()
    peremption = routines.get("peremption_minutes", PEREMPTION)
    gens = set(presence) | set(routines.get("gens") or {})
    pj = joueurs()

    # Deux passes, et l'ordre n'est pas négociable : les joueurs d'abord, parce
    # que c'est leur position qui dit quelles salles sont gelées pour tous les
    # autres. Faire l'inverse reviendrait à geler d'après un état pas encore
    # calculé.
    out = {}
    for pid in sorted(gens & pj):
        ou = ou_est(pid, quand, routines, chateau, presence, peremption, pj, None)
        if ou:
            out[pid] = ou
    gele = {o.get("salle") for o in out.values()
            if o.get("etat") == "arrete" and o.get("salle")}

    for pid in sorted(gens - pj):
        ou = ou_est(pid, quand, routines, chateau, presence, peremption, pj, gele)
        if ou:
            out[pid] = ou

    # Troisième passe : LES OMBRES. Elles n'ont pas de destination à elles, on
    # recopie donc la position de leur corps — état compris : une ombre est
    # dans l'escalier avec celui qu'elle suit, pas arrêtée à l'arrivée.
    # On répète tant que ça bouge, pour qu'une ombre d'ombre se pose aussi, et
    # l'on s'arrête net au bout de quelques tours : deux qui se suivent l'un
    # l'autre ne doivent pas faire tourner le moteur en rond.
    for _ in range(4):
        reste = [pid for pid, o in out.items() if o.get("etat") == "suit"]
        if not reste:
            break
        for pid in reste:
            corps = out.get(out[pid]["suit"])
            if not corps or corps.get("etat") == "suit":
                continue
            out[pid] = dict(corps, source="ombre", suit=out[pid]["suit"])
    # Un corps qu'on n'a pas su placer (un joueur jamais constaté) : son ombre
    # est introuvable aussi, et c'est la seule réponse honnête — on ne sait pas
    # où elle est parce qu'on ne sait pas où il est.
    for pid in [p for p, o in out.items() if o.get("etat") == "suit"]:
        del out[pid]
    return out


# ------------------------------------------------------------------ sortie

def noms():
    d = {}
    for p in _lire("personnages.json", []) or []:
        d[p.get("id")] = p.get("nom")
    return d


def dire(ou):
    if ou["etat"] == "arrete":
        return "%-22s (%s)" % (ou.get("salle") or "?", ou["source"])
    return "en chemin : %s -> %s, passe %s, arrive dans %d min" % (
        ou["de"], ou["vers"], ou["salle"], ou["arrive_dans"])


def main():
    args = sys.argv[1:]
    routines, chemins, presence = charger()
    chateau = Chateau(chemins)

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
        ou_moi = resoudre(quand).get(_lire("journal.json", {})
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
        cle = ou["salle"] if ou["etat"] == "arrete" else \
            "~ %s -> %s" % (ou["de"], ou["vers"])
        par_salle.setdefault(cle, []).append((N.get(pid, pid), ou))
    for cle in sorted(par_salle):
        gens = par_salle[cle]
        print("  %-24s %s" % (cle, ", ".join(n for n, _ in gens)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
