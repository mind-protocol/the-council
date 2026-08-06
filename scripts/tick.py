"""Moteur arithmetique du hors-scene : ce qui tombe, et rien de plus.

Usage :
    python scripts/tick.py --verifier
        Audit de coherence de etat/ (intentions, evenements, diffusion, lieux).
        Sort en code 1 des qu'il y a une anomalie, 0 sinon.

    python scripts/tick.py --jours 3
    python scripts/tick.py --jusqu-a 129.3.20
        Calcule la fenetre depuis monde.date jusqu'a la cible, ecrit une
        PROPOSITION dans etat/staging/tick-<AAAAMMJJ-HHMMSS>.json, et imprime
        un resume lisible.

    python scripts/tick.py --jours 3 --acteur daemon --acteur corlys
        Restreint le calcul a ces acteurs (repetable).

Le script ne decide RIEN. Il lit etat/ et n'ecrit que sous etat/staging/ :
le MJ seul relit, arbitre et applique dans etat/*.json. Un seul ecrivain.

Reference normative du format : docs/schema.md. Calendrier : 12 lunes de
30 jours. Ce qui n'y est pas tranche l'est ici, au plus simple :
- Budget d'etapes : on compte le plan VIVANT (etapes `en-cours` ou `bloque`).
  Une etape `fait` ou `abandonne` ne charge plus la tete.
- Une etape dont `jours_restants` vaut null est une posture permanente : elle
  ne tombe jamais, ne se decompte jamais, et n'apparait dans aucun des trois
  paniers d'etapes (seulement dans le compte du resume).
- Une etape dont un `depend_de` n'est pas `fait` voit son horloge arretee :
  elle passe en attente, sans consommer les jours de la fenetre.
- Retard tolere d'une tete avant rafraichissement : 1 jour (scene), 3 jours
  (orbite), 15 jours (royaume).
- Un plan encore ecrit en chaines de caracteres (format d'avant les etapes
  horlogees) est signale, jamais reparé.
"""
import argparse
import hashlib
import io
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
STAGING = os.path.join(ETAT, "staging")

JOURS_PAR_LUNE = 30
LUNES_PAR_AN = 12

ECHELLES = ("scene", "orbite", "royaume")

# Table des budgets de docs/schema.md : maxima par echelle.
BUDGETS = {
    "scene":   {"acteurs": 5,  "croyances": 6, "etapes": 5, "declencheurs": 3},
    "orbite":  {"acteurs": 10, "croyances": 5, "etapes": 4, "declencheurs": 2},
    # un declencheur reste permis : sans lui, un lointain serait sourd au joueur
    "royaume": {"acteurs": None, "croyances": 3, "etapes": 2, "declencheurs": 1},
}

# Retard tolere de date_maj, en jours, avant qu'une tete soit dite en retard.
TOLERANCE_MAJ = {"scene": 1, "orbite": 3, "royaume": 15}

# Les acteurs lointains ne valent pas le calcul sur une fenetre courte.
FENETRE_ROYAUME = 5

GRAVITES = ("grave", "avertissement", "note")


# ------------------------------------------------------------------- dates

def jour_absolu(date):
    """{annee, lune, jour} -> entier de jours. 12 lunes de 30 jours."""
    if not isinstance(date, dict):
        return None
    try:
        a = int(date.get("annee"))
        l = int(date.get("lune"))
        j = int(date.get("jour"))
    except (TypeError, ValueError):
        return None
    return (a * LUNES_PAR_AN + (l - 1)) * JOURS_PAR_LUNE + (j - 1)


def date_de(n):
    """Entier de jours -> {annee, lune, jour}."""
    jour = n % JOURS_PAR_LUNE
    lunes = n // JOURS_PAR_LUNE
    return {"annee": lunes // LUNES_PAR_AN,
            "lune": (lunes % LUNES_PAR_AN) + 1,
            "jour": jour + 1}


def fmt(date):
    """{annee, lune, jour} -> '129.3.17'."""
    if not isinstance(date, dict):
        return "?"
    return "{}.{}.{}".format(date.get("annee", "?"), date.get("lune", "?"),
                             date.get("jour", "?"))


def lire_date(texte):
    """'129.3.20' -> {annee, lune, jour}."""
    morceaux = texte.replace("/", ".").replace("-", ".").split(".")
    if len(morceaux) != 3:
        sys.exit("date illisible : {} (attendu 129.3.20)".format(texte))
    try:
        a, l, j = (int(m) for m in morceaux)
    except ValueError:
        sys.exit("date illisible : {} (attendu 129.3.20)".format(texte))
    if not 1 <= l <= LUNES_PAR_AN or not 1 <= j <= JOURS_PAR_LUNE:
        sys.exit("date hors calendrier : {} (12 lunes de 30 jours)".format(texte))
    return {"annee": a, "lune": l, "jour": j}


# ---------------------------------------------------------------- lecture

def charger(nom, defaut):
    """Lit etat/<nom>.json. Lecture seule, toujours."""
    chemin = os.path.join(ETAT, nom + ".json")
    if not os.path.isfile(chemin):
        return defaut
    with io.open(chemin, encoding="utf-8") as fh:
        contenu = fh.read().strip()
    if not contenu:
        return defaut
    try:
        return json.loads(contenu)
    except ValueError as err:
        sys.exit("etat/{}.json illisible : {}".format(nom, err))


class Etat(object):
    """Tout l'etat charge une fois, avec les index dont on se sert partout."""

    def __init__(self):
        self.monde = charger("monde", {})
        self.journal = charger("journal", {})
        self.lieux = charger("lieux", [])
        self.personnages = charger("personnages", [])
        self.evenements = charger("evenements", [])
        self.intentions = charger("intentions", [])

        self.date = self.monde.get("date") or {"annee": 0, "lune": 1, "jour": 1}
        self.aujourdhui = jour_absolu(self.date) or 0
        self.joueur = self.journal.get("personnage_joueur_id")

        # lieux : id canonique et alias pointent vers le meme lieu
        self.lieu_par_id = {}
        for lieu in self.lieux:
            lid = lieu.get("id")
            if not lid:
                continue
            self.lieu_par_id[lid] = lid
            for alias in lieu.get("alias") or []:
                self.lieu_par_id[alias] = lid

        self.perso_par_id = {p.get("id"): p for p in self.personnages
                             if p.get("id")}
        self.intention_par_id = {}
        for tete in self.intentions:
            pid = tete.get("personnage_id")
            if pid:
                self.intention_par_id.setdefault(pid, tete)

    def lieu(self, lid):
        """Id de lieu -> id canonique, ou None si inconnu."""
        return self.lieu_par_id.get(lid)

    def nom(self, pid):
        perso = self.perso_par_id.get(pid)
        return perso.get("nom") if perso else pid

    def actifs_en(self, lid):
        """Personnages actifs presents dans ce lieu (alias compris)."""
        canon = self.lieu(lid)
        if not canon:
            return []
        return sorted(p["id"] for p in self.personnages
                      if p.get("etat") == "actif"
                      and self.lieu(p.get("lieu_id")) == canon)


def echelle_de(tete):
    """Echelle declaree d'une tete ; 'orbite' par defaut faute de mieux."""
    ech = tete.get("echelle")
    return ech if ech in ECHELLES else "orbite"


def etapes_de(tete):
    """Les etapes de plan au format objet ; les chaines sont ignorees ici."""
    return [e for e in (tete.get("plan") or []) if isinstance(e, dict)]


# ------------------------------------------------------- garde d'ecriture

TABLES_MUTABLES = ("intentions", "evenements", "personnages", "monde",
                   "info", "actes", "paroles", "jetons", "annales")


def empreintes_etat():
    """Empreinte des tables au moment du calcul.

    Sert de garde a scripts/appliquer.py : si une table a bouge depuis, c'est
    qu'un autre ecrivain est passe et la proposition est perimee.
    """
    empreintes = {}
    for nom in TABLES_MUTABLES:
        chemin = os.path.join(ETAT, nom + ".json")
        if not os.path.isfile(chemin):
            continue
        with io.open(chemin, "rb") as f:
            empreintes[nom] = hashlib.sha1(f.read()).hexdigest()
    return empreintes


def ecrire_staging(nom_fichier, donnees):
    """SEULE ecriture du script. Refuse tout chemin hors etat/staging/."""
    cible = os.path.abspath(os.path.join(STAGING, nom_fichier))
    permis = os.path.abspath(STAGING) + os.sep
    if not cible.startswith(permis):
        raise RuntimeError(
            "ecriture refusee hors etat/staging/ : {}".format(cible))
    if not os.path.isdir(STAGING):
        os.makedirs(STAGING)
    with io.open(cible, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(donnees, ensure_ascii=False, indent=2))
        fh.write("\n")
    return cible


# ------------------------------------------------------- MODE A : verifier

class Rapport(object):
    def __init__(self):
        self.anomalies = []

    def dire(self, gravite, sujet, texte):
        self.anomalies.append({"gravite": gravite, "sujet": sujet,
                               "texte": texte})

    def imprimer(self):
        print("Audit de etat/ — {} anomalie(s)".format(len(self.anomalies)))
        if not self.anomalies:
            print("  rien a signaler.")
            return
        for gravite in GRAVITES:
            lot = [a for a in self.anomalies if a["gravite"] == gravite]
            if not lot:
                continue
            print("\n== {} ({}) ==".format(gravite.upper(), len(lot)))
            for a in lot:
                print("  [{}] {}".format(a["sujet"], a["texte"]))


def verifier_intentions(e, r):
    """Une tete par actif, une seule, dans les budgets, a jour."""
    vues = set()
    ids_etapes = {}          # id d'etape -> [personnage_id]
    depend = {}              # id d'etape -> [ids requis]

    for tete in e.intentions:
        pid = tete.get("personnage_id")
        if not pid:
            r.dire("grave", "intentions",
                   "entree sans personnage_id : {}".format(
                       json.dumps(tete, ensure_ascii=False)[:80]))
            continue
        if pid in vues:
            r.dire("grave", pid, "deux entrees d'intentions pour ce personnage")
        vues.add(pid)

        if pid == e.joueur:
            r.dire("grave", pid,
                   "le personnage joueur a une entree dans intentions.json — "
                   "sa tete appartient au joueur, elle doit disparaitre")
        perso = e.perso_par_id.get(pid)
        if perso is None:
            r.dire("grave", pid, "tete pour un personnage inconnu de "
                                 "personnages.json")
        elif perso.get("etat") == "mort":
            r.dire("grave", pid, "tete pour un personnage mort")
        elif perso.get("etat") != "actif":
            r.dire("avertissement", pid,
                   "tete pour un personnage {} — actif ou rien".format(
                       perso.get("etat")))

        ech = tete.get("echelle")
        if ech is None:
            r.dire("avertissement", pid, "echelle absente")
        elif ech not in ECHELLES:
            r.dire("avertissement", pid,
                   "echelle hors {{scene, orbite, royaume}} : {!r}".format(ech))
        budget = BUDGETS[echelle_de(tete)]
        ech_dite = echelle_de(tete)

        n_croyances = len(tete.get("croyances") or [])
        if n_croyances > budget["croyances"]:
            r.dire("avertissement", pid,
                   "{} croyances pour un budget de {} ({})".format(
                       n_croyances, budget["croyances"], ech_dite))

        plan = tete.get("plan") or []
        chaines = [p for p in plan if not isinstance(p, dict)]
        if chaines:
            r.dire("avertissement", pid,
                   "{}/{} etape(s) de plan encore en simple texte, sans "
                   "horloge ni cout ni si_bloque".format(len(chaines),
                                                         len(plan)))
        etapes = etapes_de(tete)
        vivantes = [x for x in etapes
                    if x.get("etat") in ("en-cours", "bloque")]
        if len(vivantes) > budget["etapes"]:
            r.dire("avertissement", pid,
                   "{} etapes vivantes pour un budget de {} ({})".format(
                       len(vivantes), budget["etapes"], ech_dite))

        decl = tete.get("declencheurs") or []
        if len(decl) > budget["declencheurs"]:
            r.dire("avertissement", pid,
                   "{} declencheurs pour un budget de {} ({})".format(
                       len(decl), budget["declencheurs"], ech_dite))
        for i, d in enumerate(decl):
            if not isinstance(d, dict) or not d.get("si") or not d.get("alors"):
                r.dire("grave", pid,
                       "declencheur #{} sans 'si' ou sans 'alors'".format(i + 1))

        for etape in etapes:
            eid = etape.get("id")
            if not eid:
                r.dire("grave", pid, "etape sans id : {!r}".format(
                    str(etape.get("quoi"))[:60]))
                continue
            ids_etapes.setdefault(eid, []).append(pid)
            depend[eid] = [x for x in (etape.get("depend_de") or [])]
            if etape.get("etat") == "en-cours" and "jours_restants" not in etape:
                r.dire("avertissement", pid,
                       "etape '{}' en-cours sans horloge (mettre un entier, "
                       "ou null pour une posture permanente)".format(eid))

        # tete en retard : date_maj trop vieille pour son echelle
        maj = jour_absolu(tete.get("date_maj"))
        if maj is None:
            r.dire("avertissement", pid, "date_maj absente ou illisible")
        else:
            retard = e.aujourdhui - maj
            toleree = TOLERANCE_MAJ[ech_dite]
            if retard > toleree:
                r.dire("avertissement", pid,
                       "tete en retard de {} jours (maj {}, monde {}, "
                       "tolerance {} en {})".format(retard, fmt(tete["date_maj"]),
                                                    fmt(e.date), toleree,
                                                    ech_dite))

    # actifs sans tete
    for perso in e.personnages:
        pid = perso.get("id")
        if perso.get("etat") != "actif" or pid == e.joueur:
            continue
        if pid not in vues:
            r.dire("avertissement", pid,
                   "personnage actif sans entree dans intentions.json")

    # ids d'etapes dupliques
    for eid, porteurs in sorted(ids_etapes.items()):
        if len(porteurs) > 1:
            r.dire("grave", "intentions",
                   "id d'etape '{}' porte {} fois ({})".format(
                       eid, len(porteurs), ", ".join(porteurs)))

    # depend_de pendants
    for eid, requis in sorted(depend.items()):
        for req in requis:
            if req not in ids_etapes:
                r.dire("grave", "intentions",
                       "etape '{}' depend de '{}', qui n'existe pas".format(
                           eid, req))

    # cycles de dependances
    for cycle in cycles(depend):
        r.dire("grave", "intentions",
               "cycle de dependances : {}".format(" -> ".join(cycle)))

    # budget d'acteurs par echelle
    for ech in ECHELLES:
        maxi = BUDGETS[ech]["acteurs"]
        lot = [t.get("personnage_id") for t in e.intentions
               if echelle_de(t) == ech and t.get("echelle") in ECHELLES]
        if maxi is not None and len(lot) > maxi:
            r.dire("avertissement", "intentions",
                   "{} acteurs en '{}' pour un budget de {} : {}".format(
                       len(lot), ech, maxi, ", ".join(sorted(lot))))


def cycles(depend):
    """Cycles du graphe etape -> depend_de. Renvoie des chemins fermes."""
    trouves, etat = [], {}

    def descendre(noeud, chemin):
        etat[noeud] = 1
        for suivant in depend.get(noeud, []):
            if suivant not in depend:
                continue
            if etat.get(suivant) == 1:
                boucle = chemin[chemin.index(suivant):] + [suivant]
                if boucle not in trouves:
                    trouves.append(boucle)
            elif etat.get(suivant, 0) == 0:
                descendre(suivant, chemin + [suivant])
        etat[noeud] = 2

    for noeud in sorted(depend):
        if etat.get(noeud, 0) == 0:
            descendre(noeud, [noeud])
    return trouves


def verifier_evenements(e, r):
    """Echeances passees, diffusion en retard, lieux inconnus."""
    for ev in e.evenements:
        eid = ev.get("id", "?")
        if ev.get("lieu_id") and not e.lieu(ev["lieu_id"]):
            r.dire("grave", eid, "lieu_id inconnu : {!r}".format(ev["lieu_id"]))

        prevue = jour_absolu(ev.get("date_prevue"))
        if prevue is None:
            r.dire("grave", eid, "date_prevue absente ou illisible")
        elif ev.get("statut") == "a-venir" and prevue < e.aujourdhui:
            r.dire("avertissement", eid,
                   "encore 'a-venir' alors que son echeance {} est passee "
                   "(monde {}) — retard du moteur".format(
                       fmt(ev["date_prevue"]), fmt(e.date)))

        for i, ent in enumerate(ev.get("diffusion") or []):
            etiq = "{} / diffusion #{}".format(eid, i + 1)
            if not isinstance(ent, dict):
                r.dire("grave", etiq, "entree de diffusion illisible")
                continue
            ou, qui = ent.get("ou"), ent.get("qui") or []
            if not ou and not qui:
                r.dire("grave", etiq,
                       "ni 'ou' ni 'qui' — il faut au moins l'un des deux")
            if ou and not e.lieu(ou):
                r.dire("grave", etiq, "'ou' inconnu : {!r}".format(ou))
            for pid in qui:
                if pid not in e.perso_par_id:
                    r.dire("grave", etiq, "'qui' inconnu : {!r}".format(pid))
            quand = jour_absolu(ent.get("date"))
            if quand is None:
                r.dire("grave", etiq, "date absente ou illisible")
            elif quand <= e.aujourdhui and ent.get("livree") is not True:
                r.dire("avertissement", etiq,
                       "nouvelle due le {} et toujours pas livree "
                       "(monde {})".format(fmt(ent["date"]), fmt(e.date)))


def verifier_personnages(e, r):
    for perso in e.personnages:
        lid = perso.get("lieu_id")
        if lid and not e.lieu(lid):
            r.dire("grave", perso.get("id", "?"),
                   "lieu_id inconnu : {!r}".format(lid))


def verifier(e):
    r = Rapport()
    if not e.joueur:
        r.dire("avertissement", "journal",
               "personnage_joueur_id absent — impossible de proteger sa tete")
    verifier_intentions(e, r)
    verifier_evenements(e, r)
    verifier_personnages(e, r)
    r.imprimer()
    return 1 if r.anomalies else 0


# ----------------------------------------------------------- MODE B : tick

def calculer(e, cible, restriction):
    """Ce qui tombe entre monde.date et cible. Aucune decision, du calcul."""
    fin = jour_absolu(cible)
    jours = fin - e.aujourdhui
    fenetre = {"de": e.date, "a": cible, "jours": jours}

    # --- quels acteurs on simule
    simules, sautes = [], []
    for tete in e.intentions:
        pid = tete.get("personnage_id")
        if not pid or pid == e.joueur:
            continue
        if restriction and pid not in restriction:
            continue
        if echelle_de(tete) == "royaume" and jours < FENETRE_ROYAUME:
            sautes.append(tete)
        else:
            simules.append(tete)

    # --- evenements a resoudre
    a_resoudre = []
    for ev in e.evenements:
        if ev.get("statut") != "a-venir":
            continue
        quand = jour_absolu(ev.get("date_prevue"))
        if quand is None or quand > fin:
            continue
        a_resoudre.append({
            "id": ev.get("id"),
            "date": ev.get("date_prevue"),
            "type": ev.get("type"),
            "importance": ev.get("importance"),
            "description": ev.get("description"),
            "lieu_id": ev.get("lieu_id"),
            "acteurs": ev.get("acteurs") or [],
            "conditions": ev.get("conditions") or [],
            "diffusion": ev.get("diffusion") or [],
            "en_retard": quand < e.aujourdhui,
        })
    a_resoudre.sort(key=lambda x: jour_absolu(x["date"]) or 0)

    # --- nouvelles a livrer
    # Le statut de l'evenement commande : on ne livre que ce qui a EU LIEU.
    #   resolu   -> livrable
    #   a-venir  -> conditionnel, l'echeance tombe dans la fenetre mais le MJ
    #               n'a pas encore arbitre : la nouvelle ne part qu'apres
    #   devie / annule -> jamais. La chose ne s'est pas produite.
    nouvelles, conditionnelles = [], []
    for ev in e.evenements:
        statut = ev.get("statut")
        if statut in ("devie", "annule"):
            continue
        for i, ent in enumerate(ev.get("diffusion") or []):
            if not isinstance(ent, dict) or ent.get("livree") is True:
                continue
            quand = jour_absolu(ent.get("date"))
            if quand is None or quand > fin:
                continue
            ou = ent.get("ou")
            qui = list(ent.get("qui") or [])
            deduit = False
            if not qui and ou:
                qui = e.actifs_en(ou)
                deduit = True
            touche = bool(e.joueur) and (
                e.joueur in qui
                or (ou and e.lieu(ou) is not None
                    and e.lieu(ou) == e.lieu(
                        (e.perso_par_id.get(e.joueur) or {}).get("lieu_id"))))
            entree = {
                "evenement_id": ev.get("id"),
                "diffusion_index": i,
                "date": ent.get("date"),
                "canal": ent.get("canal"),
                "fiabilite": ent.get("fiabilite"),
                "version": ent.get("version"),
                "ou": ou,
                "qui": qui,
                "qui_deduit": deduit,
                "touche_joueur": touche,
                "en_retard": quand < e.aujourdhui,
            }
            if statut == "resolu":
                nouvelles.append(entree)
            else:
                entree["depend_de_evenement"] = ev.get("id")
                entree["statut_evenement"] = statut
                conditionnelles.append(entree)
    nouvelles.sort(key=lambda x: jour_absolu(x["date"]) or 0)
    conditionnelles.sort(key=lambda x: jour_absolu(x["date"]) or 0)

    # --- etapes : tombent, avancent, ou attendent
    tombent, avancent, attendent = [], [], []
    postures = 0
    fait = set()
    for tete in e.intentions:
        for etape in etapes_de(tete):
            if etape.get("etat") == "fait" and etape.get("id"):
                fait.add(etape["id"])

    for tete in simules:
        pid = tete.get("personnage_id")
        ech = echelle_de(tete)
        for etape in etapes_de(tete):
            if etape.get("etat") != "en-cours":
                continue
            commun = {
                "personnage_id": pid,
                "echelle": ech,
                "etape": etape.get("id"),
                "quoi": etape.get("quoi"),
                "cout": etape.get("cout") or [],
                "si_bloque": etape.get("si_bloque"),
            }
            bloquants = [d for d in (etape.get("depend_de") or [])
                         if d not in fait]
            if bloquants:
                attendu = dict(commun)
                attendu["depend_de_non_fait"] = bloquants
                attendu["jours_restants"] = etape.get("jours_restants")
                attendent.append(attendu)
                continue
            reste = etape.get("jours_restants", "absent")
            if reste is None:
                postures += 1
                continue
            if not isinstance(reste, int):
                # horloge absente ou illisible : le MJ doit la poser
                sans = dict(commun)
                sans["jours_restants"] = None if reste == "absent" else reste
                sans["probleme"] = "horloge absente ou illisible"
                attendent.append(sans)
                continue
            if reste - jours <= 0:
                tombee = dict(commun)
                tombee["jours_restants"] = reste
                tombee["date_estimee"] = date_de(
                    e.aujourdhui + max(reste, 0))
                tombent.append(tombee)
            else:
                suite = dict(commun)
                suite["jours_restants"] = reste
                suite["jours_restants_apres"] = reste - jours
                avancent.append(suite)
    # Un acteur 'royaume' n'est pas rafraichi sur une fenetre courte, mais une
    # echeance ne se perd jamais : le coffre d'or promis pour demain tombe
    # demain, meme si la tete de celui qui l'apporte n'est pas repassee en revue.
    for tete in sautes:
        for etape in etapes_de(tete):
            if etape.get("etat") != "en-cours":
                continue
            if [d for d in (etape.get("depend_de") or []) if d not in fait]:
                continue
            reste = etape.get("jours_restants")
            if not isinstance(reste, int) or reste - jours > 0:
                continue
            tombent.append({
                "personnage_id": tete.get("personnage_id"),
                "echelle": "royaume",
                "etape": etape.get("id"),
                "quoi": etape.get("quoi"),
                "cout": etape.get("cout") or [],
                "si_bloque": etape.get("si_bloque"),
                "jours_restants": reste,
                "date_estimee": date_de(e.aujourdhui + max(reste, 0)),
                "malgre_saut": True,
            })

    tombent.sort(key=lambda x: jour_absolu(x["date_estimee"]) or 0)

    # --- declencheurs a evaluer (le MJ seul juge)
    declencheurs = []
    for tete in simules:
        pid = tete.get("personnage_id")
        for d in (tete.get("declencheurs") or []):
            if not isinstance(d, dict):
                continue
            declencheurs.append({
                "personnage_id": pid,
                "echelle": echelle_de(tete),
                "si": d.get("si"),
                "alors": d.get("alors"),
                "une_fois": d.get("une_fois"),
            })

    # --- tetes en retard une fois la fenetre franchie
    rafraichir = []
    for tete in simules:
        maj = jour_absolu(tete.get("date_maj"))
        ech = echelle_de(tete)
        if maj is None or fin - maj > TOLERANCE_MAJ[ech]:
            rafraichir.append({
                "personnage_id": tete.get("personnage_id"),
                "echelle": ech,
                "date_maj": tete.get("date_maj"),
                "retard_apres_fenetre": None if maj is None else fin - maj,
            })

    # --- mutations proposees : STRICTEMENT ce qui est arithmetique
    # Les horloges qui se decomptent et les nouvelles qui se marquent livrees.
    # Rien de narratif : ce qu'une etape tombee PRODUIT, c'est au MJ de l'ecrire
    # a la main dans ce meme fichier avant de lancer scripts/appliquer.py.
    mutations = []
    for s in avancent:
        mutations.append({
            "table": "intentions",
            "cible": s["personnage_id"],
            "operation": "etape",
            "etape": s["etape"],
            "champs": {"jours_restants": s["jours_restants_apres"]},
            "pourquoi": "{} jour(s) ecoule(s)".format(jours),
        })
    for n in nouvelles:
        mutations.append({
            "table": "evenements",
            "cible": n["evenement_id"],
            "operation": "diffusion_livree",
            "index": n["diffusion_index"],
            "pourquoi": "nouvelle parvenue le {}".format(fmt(n["date"])),
        })

    return {
        "genere_le": datetime.now().isoformat(timespec="seconds"),
        "empreintes": empreintes_etat(),
        "avertissement": "Proposition — le MJ arbitre et applique lui-meme "
                         "dans etat/*.json. Ce fichier n'est pas de l'etat.",
        "fenetre": fenetre,
        "acteurs_simules": [t.get("personnage_id") for t in simules],
        "acteurs_sautes_royaume": sorted(
            t.get("personnage_id") for t in sautes),
        "postures_permanentes": postures,
        "evenements_a_resoudre": a_resoudre,
        "nouvelles_a_livrer": nouvelles,
        "nouvelles_conditionnelles": conditionnelles,
        "etapes_qui_tombent": tombent,
        "etapes_qui_avancent": avancent,
        "etapes_en_attente": attendent,
        "declencheurs_a_evaluer": declencheurs,
        "tetes_a_rafraichir": rafraichir,
        "mutations_proposees": mutations,
    }


def resumer(prop, chemin):
    """Le meme calcul, en francais, pour le MJ."""
    f = prop["fenetre"]
    print("Fenetre : {} -> {} ({} jour(s))".format(
        fmt(f["de"]), fmt(f["a"]), f["jours"]))
    print("Acteurs simules : {}".format(len(prop["acteurs_simules"])))
    if prop["acteurs_sautes_royaume"]:
        print("  Echelle 'royaume' non rafraichie (fenetre < {} jours) : {}"
              .format(FENETRE_ROYAUME,
                      ", ".join(prop["acteurs_sautes_royaume"])))
        print("  (croyances et declencheurs sautes — leurs echeances tombent"
              " quand meme, marquees 'malgre saut')")

    print("\nEvenements a resoudre ({}) :".format(
        len(prop["evenements_a_resoudre"])))
    for ev in prop["evenements_a_resoudre"]:
        print("  {} {:<28} imp {} {}".format(
            fmt(ev["date"]), ev["id"], ev["importance"],
            "(EN RETARD)" if ev["en_retard"] else ""))
        if ev["conditions"]:
            print("      a arbitrer : {}".format(" | ".join(ev["conditions"])))

    print("\nNouvelles a livrer ({}) :".format(len(prop["nouvelles_a_livrer"])))
    for n in prop["nouvelles_a_livrer"]:
        cible = n["ou"] or ", ".join(n["qui"]) or "?"
        print("  {} {} par {} vers {} (fiab. {}){}{}".format(
            fmt(n["date"]), n["evenement_id"], n["canal"], cible,
            n["fiabilite"],
            " [qui deduit]" if n["qui_deduit"] else "",
            " [TOUCHE LE JOUEUR -> info.json]" if n["touche_joueur"] else ""))

    if prop.get("nouvelles_conditionnelles"):
        print("\nNouvelles SUSPENDUES ({}) — l'evenement n'est pas encore resolu,"
              " elles ne partent qu'apres ton arbitrage :"
              .format(len(prop["nouvelles_conditionnelles"])))
        for n in prop["nouvelles_conditionnelles"]:
            print("  {} {} vers {} (fiab. {}) — depend de {}".format(
                fmt(n["date"]), n["evenement_id"],
                n["ou"] or ", ".join(n["qui"]) or "?", n["fiabilite"],
                n["depend_de_evenement"]))

    print("\nEtapes qui tombent ({}) :".format(len(prop["etapes_qui_tombent"])))
    for s in prop["etapes_qui_tombent"]:
        print("  {} {}{} — {}".format(
            fmt(s["date_estimee"]), s["personnage_id"],
            " [malgre saut]" if s.get("malgre_saut") else "", s["quoi"]))
        if s["cout"]:
            print("      cout : {}".format(", ".join(str(c) for c in s["cout"])))
        if s["si_bloque"]:
            print("      si bloque : {}".format(s["si_bloque"]))

    print("\nEtapes qui avancent ({}) :".format(
        len(prop["etapes_qui_avancent"])))
    for s in prop["etapes_qui_avancent"]:
        print("  {} — {} : {} -> {} jour(s)".format(
            s["personnage_id"], s["etape"], s["jours_restants"],
            s["jours_restants_apres"]))

    print("\nEtapes en attente ({}) :".format(len(prop["etapes_en_attente"])))
    for s in prop["etapes_en_attente"]:
        motif = s.get("probleme") or "attend {}".format(
            ", ".join(s.get("depend_de_non_fait") or []))
        print("  {} — {} ({})".format(s["personnage_id"], s["etape"], motif))

    if prop["postures_permanentes"]:
        print("\nPostures permanentes (horloge null, jamais decomptees) : {}"
              .format(prop["postures_permanentes"]))

    print("\nDeclencheurs a evaluer ({}) — le MJ seul juge :".format(
        len(prop["declencheurs_a_evaluer"])))
    for d in prop["declencheurs_a_evaluer"]:
        print("  {} : si {} -> {}".format(d["personnage_id"], d["si"],
                                          d["alors"]))

    print("\nTetes a rafraichir ({}) : {}".format(
        len(prop["tetes_a_rafraichir"]),
        ", ".join(t["personnage_id"] for t in prop["tetes_a_rafraichir"])))

    print("\n{} mutation(s) arithmetique(s) deja redigee(s) dans la proposition "
          "(horloges, nouvelles marquees livrees).".format(
              len(prop.get("mutations_proposees") or [])))
    print("Ajoute les tiennes a la main dans 'mutations_proposees', puis :")
    print("  python scripts/appliquer.py {}            # blanc"
          .format(os.path.basename(chemin)))
    print("  python scripts/appliquer.py {} --vraiment # ecrit"
          .format(os.path.basename(chemin)))
    print("\nProposition ecrite : {}".format(
        os.path.relpath(chemin, RACINE).replace("\\", "/")))


def tick(e, cible, restriction):
    if jour_absolu(cible) < e.aujourdhui:
        sys.exit("cible {} anterieure a monde.date {} — le tick n'avance "
                 "que dans un sens".format(fmt(cible), fmt(e.date)))
    prop = calculer(e, cible, restriction)
    base = "tick-{}".format(datetime.now().strftime("%Y%m%d-%H%M%S"))
    nom, n = base + ".json", 1
    while os.path.isfile(os.path.join(STAGING, nom)):   # deux ticks a la seconde
        n += 1
        nom = "{}-{}.json".format(base, n)
    chemin = ecrire_staging(nom, prop)
    resumer(prop, chemin)
    return 0


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Moteur arithmetique du hors-scene (lit etat/, "
                    "n'ecrit que dans etat/staging/)")
    ap.add_argument("--verifier", action="store_true",
                    help="audit de coherence de etat/ (code 1 si anomalie)")
    ap.add_argument("--jours", type=int,
                    help="taille de la fenetre depuis monde.date")
    ap.add_argument("--jusqu-a", dest="jusqu_a", metavar="129.3.20",
                    help="date cible de la fenetre")
    ap.add_argument("--acteur", action="append", default=[], metavar="ID",
                    help="restreint le calcul a cet acteur (repetable)")
    args = ap.parse_args()

    e = Etat()

    if args.verifier:
        if args.jours is not None or args.jusqu_a:
            sys.exit("--verifier ne se combine pas avec --jours / --jusqu-a")
        return verifier(e)

    if args.jours is not None and args.jusqu_a:
        sys.exit("choisir --jours OU --jusqu-a, pas les deux")
    if args.jours is not None:
        if args.jours < 0:
            sys.exit("--jours doit etre positif")
        cible = date_de(e.aujourdhui + args.jours)
    elif args.jusqu_a:
        cible = lire_date(args.jusqu_a)
    else:
        ap.print_help()
        return 0

    return tick(e, cible, set(args.acteur))


if __name__ == "__main__":
    sys.exit(main())
