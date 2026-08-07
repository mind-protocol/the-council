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
- LA BOUCHE (docs/plis.md) : un homme qui se deplace porte TOUT ce qu'il sait.
  Le tick detecte les arrivees a partir de ce qui existe deja (evenements de la
  fenetre, etapes qui tombent) et sort le DIFFERENTIEL de croyances — jamais un
  verdict. Il ne recopie aucune croyance : le MJ arbitre ce qui se dit.
- Les plis (etat/plis.json, voir docs/plis.md) sont routes : un pli `en-route`
  dont `attendu_le` est echu passe `remis`, dans la main du destinataire NATUREL
  du lieu (le mestre), jamais dans celle du `pour`. `evenements.diffusion` reste
  en place a cote : c'est une coexistence, pas un remplacement.
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
# EXCEPTION : le plafond d'acteurs en 'orbite' est monte de 12 a 20 le 23e jour
# de la 3e lune, a l'ouverture du siege de Port-Real. Une seconde base a jouer,
# c'est une seconde poignee de gens qui pesent sans etre en scene ; les tenir en
# 'royaume' les rendrait sourds au joueur, ce qui est precisement le contraire
# de ce qu'on veut d'un reseau. docs/schema.md dit toujours ~12 et ne se
# modifie pas : c'est ici que la partie fait foi.
BUDGETS = {
    "scene":   {"acteurs": 5,  "croyances": 6, "etapes": 5, "declencheurs": 3},
    "orbite":  {"acteurs": 20, "croyances": 5, "etapes": 4, "declencheurs": 2},
    # un declencheur reste permis : sans lui, un lointain serait sourd au joueur
    "royaume": {"acteurs": None, "croyances": 3, "etapes": 2, "declencheurs": 1},
}

# Retard tolere de date_maj, en jours, avant qu'une tete soit dite en retard.
TOLERANCE_MAJ = {"scene": 1, "orbite": 3, "royaume": 15}

# Les acteurs lointains ne valent pas le calcul sur une fenetre courte.
FENETRE_ROYAUME = 5

GRAVITES = ("grave", "avertissement", "note")

# Les plis (docs/plis.md). Un pli est un OBJET : la rumeur et le temoin n'en
# sont pas, et restent a evenements.diffusion.
CANAUX_PLI = ("corbeau", "cavalier", "barque")
ETATS_PLI = ("en-route", "remis", "ouvert", "retenu", "perdu", "intercepte")
# Un pli remis est dans une main ; sans main, personne ne l'a lu.
ETATS_PLI_EN_MAIN = ("remis", "ouvert", "retenu")
# Retard tolere sur `attendu_le` avant qu'un pli en route soit dit egare.
TOLERANCE_PLI = 3
# Corbeau : environ le tiers du plein tarif, jamais moins d'un jour.
DIVISEUR_CORBEAU = 3

# LA BOUCHE — rapprochement de textes. On ne comprend pas le francais, on
# compare des mots rares : deux mots distinctifs partages suffisent a dire
# « ce fait a pu lui venir de la ». C'est une heuristique, assumee comme telle.
MOTS_COMMUNS = frozenset("""
alors apres aussi avait avant avec bien cela cette chose comme contre dans deux
elle encore entre etait etre faire fait fille homme jamais leur leurs mais meme
moins nous parce pour plus pourrait pouvoir quand quelque reine roi sans sera
serait seul sont sous suis tous tout toute toutes trois trop vers veut voir
votre vous celui ceux dont donc dire dit ete leurs pris peut sait savoir
""".split())
MOTS_PARTAGES_MINIMUM = 2

# LA RUMEUR — un incident de la table de guerre (docs/carte.md), pas une table
# de plus. Elle n'a pas de porteur nomme : elle saute de proche en proche.
# Echelle de certitude, du plus sur au plus trouble. Un saut degrade d'un cran.
CERTITUDES = ("sure", "rapportee", "rumeur")
# Plus lente que le cavalier : elle passe de bouche en bouche, elle s'arrete
# boire. Plein tarif x3/2, et jamais moins de deux jours pour un saut.
LENTEUR_RUMEUR = (3, 2)
SAUT_RUMEUR_MINIMUM = 2
# Au-dela, une place n'est plus « de proche en proche » : la rumeur y ira par
# un pli ou par une bouche, pas toute seule.
PORTEE_SAUT_RUMEUR = 3
# Plafond de voisins gagnes par rumeur et par fenetre — les `risque[]` ecrits
# par le MJ ne sont jamais plafonnes, ni un saut qui atteint le joueur.
VOISINS_PAR_RUMEUR = 3
# Silence tolere avant qu'une rumeur soit dite immobile — elle devrait avancer
# ou s'eteindre.
SILENCE_RUMEUR = {"vif": 5, "couve": 15}


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
        # Qui a une place dans la journee du chateau (etat/routines.json).
        self.routines = set((charger("routines", {}) or {}).get("gens") or {})
        # Les mains. Fichier absent = pas d'activites, et rien ne casse.
        brut = charger("activites", {})
        self.activites = brut.get("activites", []) if isinstance(brut, dict) else brut
        # Les livres poses dans les salles ou portes par quelqu'un (docs/books.md).
        # Fichier absent = pas de livres, et rien ne casse.
        brut = charger("books", [])
        self.books = brut.get("books", []) if isinstance(brut, dict) else brut
        # Le grand livre et la memoire verbale : sources possibles d'un savoir.
        self.actes = charger("actes", [])
        self.paroles = charger("paroles", [])
        # Le courrier. Fichier absent = pas de plis, et rien ne casse.
        brut = charger("plis", {})
        self.plis = brut.get("plis", []) if isinstance(brut, dict) else brut
        # La table de guerre. Une rumeur EST un incident (docs/carte.md) : on ne
        # cree pas de quatrieme table, on se sert de l'objet qui existe.
        brut = charger("jetons", {})
        pieces = brut.get("jetons", []) if isinstance(brut, dict) else brut
        self.incidents = [j for j in pieces if isinstance(j, dict)
                          and j.get("genre") == "incident"
                          and j.get("statut", "actif") == "actif"]

        self.date = self.monde.get("date") or {"annee": 0, "lune": 1, "jour": 1}
        self.aujourdhui = jour_absolu(self.date) or 0
        self.joueur = self.journal.get("personnage_joueur_id")

        # Les sieges (etat/joueurs.json) — technique, hors docs/schema.md.
        # `occupe` dit si quelqu'un est ASSIS dedans en ce moment. Un siege
        # alterne (on joue Rhaenyra, puis l'agent de Port-Real, jamais les deux
        # a la fois) bascule ce champ, et la regle qui en decoule est la seule
        # qui compte : un siege OCCUPE n'a pas de tete dans intentions.json —
        # elle appartient au joueur ; un siege VACANT en a une, sans quoi le
        # personnage cesse purement et simplement d'agir hors ecran.
        self.sieges = charger("joueurs", [])
        if not isinstance(self.sieges, list):
            self.sieges = []
        self.sieges_occupes = set()
        self.sieges_vacants = set()
        for siege in self.sieges:
            pid = siege.get("personnage_id")
            if not pid:
                continue
            (self.sieges_occupes if siege.get("occupe", True)
             else self.sieges_vacants).add(pid)
        # Partie seule sans roster : le journal fait foi.
        if not self.sieges and self.joueur:
            self.sieges_occupes.add(self.joueur)

        # lieux : id canonique et alias pointent vers le meme lieu
        self.lieu_par_id = {}
        self.fiche_lieu = {}
        for lieu in self.lieux:
            lid = lieu.get("id")
            if not lid:
                continue
            self.lieu_par_id[lid] = lid
            self.fiche_lieu[lid] = lieu
            for alias in lieu.get("alias") or []:
                self.lieu_par_id[alias] = lid

        self.perso_par_id = {p.get("id"): p for p in self.personnages
                             if p.get("id")}
        # index des mesures par adresse <activite_id>.<mesure_id> : c'est ce
        # que cite un `cout` d'etape de plan, et ce qui rend le si_bloque
        # arithmetique au lieu d'etre juge au doigt mouille.
        self.mesure_par_adresse = {}
        for act in self.activites:
            for mes in act.get("mesure") or []:
                if act.get("id") and mes.get("id"):
                    self.mesure_par_adresse[
                        "{}.{}".format(act["id"], mes["id"])] = (act, mes)
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


    # ------------------------------------------------------------- les plis

    def roukerie(self, lid):
        """Stock de corbeaux d'un lieu : {lieu d'origine: nombre}. {} si tu."""
        fiche = self.fiche_lieu.get(self.lieu(lid) or "") or {}
        stock = fiche.get("roukerie")
        return stock if isinstance(stock, dict) else {}

    def destinataire_naturel(self, lid):
        """A qui un pli est REMIS en arrivant la — jamais au 'pour'.

        Le mestre du lieu, la roukerie d'abord. A defaut, None : c'est au MJ
        de dire dans quelle main ca tombe, et la proposition le signale.
        """
        canon = self.lieu(lid)
        if not canon:
            return None
        candidats = []
        for pid in self.actifs_en(canon):
            titre = (self.perso_par_id.get(pid) or {}).get("titre") or ""
            bas = titre.lower()
            if "mestre" not in bas:
                continue
            # le gardien de la roukerie passe devant tout autre mestre
            candidats.append((0 if "roukerie" in bas else 1, pid))
        if not candidats:
            return None
        return sorted(candidats)[0][1]

    def depart_de(self, pli):
        """Lieu de depart d'un pli : `depuis`, sinon le lieu de l'expediteur."""
        if pli.get("depuis"):
            return self.lieu(pli["depuis"])
        perso = self.perso_par_id.get(pli.get("de"))
        return self.lieu((perso or {}).get("lieu_id"))


def jours_de_route(e, depuis, vers, canal):
    """Estimation en jours depuis les jours_de_pr. Rend None si on ne sait pas.

    Le corbeau vole en un tiers du temps (arrondi au superieur), le cavalier et
    la barque paient le plein tarif. Jamais moins d'un jour.
    """
    a = (e.fiche_lieu.get(e.lieu(depuis) or "") or {}).get("jours_de_pr")
    b = (e.fiche_lieu.get(e.lieu(vers) or "") or {}).get("jours_de_pr")
    if not isinstance(a, int) or not isinstance(b, int):
        return None
    plein = max(abs(a - b), 1)
    if canal == "corbeau":
        return max((plein + DIVISEUR_CORBEAU - 1) // DIVISEUR_CORBEAU, 1)
    return plein


# ------------------------------------------------------------- LA BOUCHE

def mots_rares(texte):
    """Les mots distinctifs d'un texte : sans accents, longs, hors banalites."""
    if not isinstance(texte, str):
        return set()
    plat = texte.lower()
    for a, b in (("àâä", "a"), ("éèêë", "e"), ("îï", "i"), ("ôö", "o"),
                 ("ùûü", "u"), ("ç", "c")):
        for lettre in a:
            plat = plat.replace(lettre, b)
    mot, mots = [], set()
    for car in plat:
        if car.isalnum():
            mot.append(car)
            continue
        if mot:
            mots.add("".join(mot))
            mot = []
    if mot:
        mots.add("".join(mot))
    return {m for m in mots if len(m) >= 5 and m not in MOTS_COMMUNS}


def se_recoupent(texte, autre, minimum=MOTS_PARTAGES_MINIMUM):
    """Deux textes parlent-ils vraisemblablement de la meme chose ?"""
    return len(mots_rares(texte) & mots_rares(autre)) >= minimum


def croyances_de(tete):
    return [c for c in (tete.get("croyances") or []) if isinstance(c, str)]


def echelle_de(tete):
    """Echelle declaree d'une tete ; 'orbite' par defaut faute de mieux."""
    ech = tete.get("echelle")
    return ech if ech in ECHELLES else "orbite"


def etapes_de(tete):
    """Les etapes de plan au format objet ; les chaines sont ignorees ici."""
    return [e for e in (tete.get("plan") or []) if isinstance(e, dict)]


# --------------------------------------------------- MAINS : l'arithmetique

def rythme_de(mesure):
    """(par, jours) en entiers. Un rythme illisible vaut 'ne bouge pas'."""
    r = mesure.get("rythme")
    if not isinstance(r, dict):
        return (0, 1)
    par = r.get("par", 0)
    jours = r.get("jours", 1)
    if not isinstance(par, int) or not isinstance(jours, int) or jours <= 0:
        return (0, 1)
    return (par, jours)


def borner(valeur, mesure):
    bas, haut = mesure.get("plancher"), mesure.get("plafond")
    if isinstance(bas, int) and valeur < bas:
        return bas, "plancher"
    if isinstance(haut, int) and valeur > haut:
        return haut, "plafond"
    return valeur, None


def au_plancher(mesure):
    bas = mesure.get("plancher")
    return isinstance(bas, int) and mesure.get("valeur") == bas


def decompter(mesure, jours):
    """Entiers seulement : total = par*n + reliquat, puis division plancher.

    Rend (valeur_apres, reliquat_apres, borne). Exact et sans derive, quelle
    que soit la decoupe des ticks — c'est tout l'interet du reliquat.
    """
    par, pas = rythme_de(mesure)
    depart = mesure.get("valeur")
    if not isinstance(depart, int):
        depart = 0
    reliquat = mesure.get("reliquat")
    if not isinstance(reliquat, int) or not 0 <= reliquat < pas:
        reliquat = 0
    total = par * jours + reliquat
    valeur, borne = borner(depart + total // pas, mesure)
    return valeur, total % pas, borne


def porteur_absent(e, act):
    """Un porteur mort ou absent ne produit plus, mais l'affaire coute encore."""
    p = act.get("porteur") or {}
    if p.get("type") != "personnage":
        return False
    perso = e.perso_par_id.get(p.get("id"))
    return perso is None or perso.get("etat") == "mort"


def couts_chiffres(etape):
    """Les couts qui CITENT une mesure : {mesure: <adresse>, quantite: <int>}.

    Un cout en clair ('des journees de seize heures') reste au jugement du MJ ;
    seuls ceux-la se verifient tout seuls.
    """
    return [c for c in (etape.get("cout") or [])
            if isinstance(c, dict) and c.get("mesure")]


def chiffrer_cout(etape, mesures_apres):
    """Ce qui manque pour tenir l'etape, adresse par adresse. [] = ca passe."""
    manque = []
    for c in couts_chiffres(etape):
        adresse = c["mesure"]
        besoin = c.get("quantite", 0)
        if adresse not in mesures_apres:
            manque.append({"mesure": adresse, "quantite": besoin,
                           "probleme": "adresse de mesure inconnue"})
            continue
        dispo = mesures_apres[adresse]
        if isinstance(besoin, int) and dispo < besoin:
            manque.append({"mesure": adresse, "quantite": besoin,
                           "disponible": dispo, "manque": besoin - dispo})
    return manque


def seuil_franchi(mesure_valeur, seuil):
    quand, borne = seuil.get("quand"), seuil.get("valeur")
    if not isinstance(borne, int):
        return False
    if quand == "sous":
        return mesure_valeur < borne
    if quand == "sur":
        return mesure_valeur > borne
    return False


# ------------------------------------------------------- garde d'ecriture

TABLES_MUTABLES = ("intentions", "evenements", "personnages", "monde",
                   "info", "actes", "paroles", "jetons", "annales",
                   "activites", "plis", "lieux")


# Les tables qui appartiennent a UN JOUEUR (voir scripts/appliquer.py). Le
# sceau doit porter sur le fichier que appliquer.py ecrira reellement.
CROYANCES = ("jetons", "vues", "objectifs")


def chemin_scelle(nom, joueur=None):
    if nom in CROYANCES and joueur:
        p = os.path.join(ETAT, "joueurs", joueur, nom + ".json")
        if os.path.isfile(p):
            return p
    return os.path.join(ETAT, nom + ".json")


def empreintes_etat(joueur=None):
    """Empreinte des tables au moment du calcul.

    Sert de garde a scripts/appliquer.py : si une table a bouge depuis, c'est
    qu'un autre ecrivain est passe et la proposition est perimee.
    """
    empreintes = {}
    for nom in TABLES_MUTABLES:
        chemin = chemin_scelle(nom, joueur)
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
        durs = [a for a in self.anomalies if a["gravite"] != "note"]
        print("Audit de etat/ — {} anomalie(s){}".format(
            len(durs),
            " + {} note(s) informative(s)".format(
                len(self.anomalies) - len(durs))
            if len(durs) != len(self.anomalies) else ""))
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

        if pid in e.sieges_occupes:
            r.dire("grave", pid,
                   "siege OCCUPE avec une entree dans intentions.json — "
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

    # actifs sans tete NI mains. Un actif sans tete n'est plus une anomalie
    # depuis activites.json : c'est un homme qui n'a rien a decider et dont
    # l'affaire tourne toute seule. Ce qui reste faux, c'est l'actif qui n'a
    # ni l'un ni l'autre — celui-la est un dormant qui s'ignore.
    porteurs = {(a.get("porteur") or {}).get("id") for a in e.activites
                if (a.get("porteur") or {}).get("type") == "personnage"}
    # Un temoin est un porteur legitime SANS tete : il n'a pas de projet, il a
    # vu quelque chose et il le raconte. Ne rien lui reprocher pour autant.
    temoins = temoins_des_incidents(e)
    # Quatrieme facon d'exister sans rien decider : avoir une PLACE DANS LA
    # JOURNEE (etat/routines.json). Un coureur, un garde, une fille de cuisine
    # ne poursuivent aucun plan et ne comptent aucun stock — ils tiennent un
    # poste, et le chateau tourne parce qu'ils y sont. Sans routine, en
    # revanche, un actif reste fige la ou une vieille scene l'a laisse : c'est
    # ca, le vrai defaut que ce controle doit attraper.
    for perso in e.personnages:
        pid = perso.get("id")
        if perso.get("etat") != "actif" or pid in e.sieges_occupes:
            continue
        if (pid not in vues and pid not in porteurs and pid not in temoins
                and pid not in e.routines):
            r.dire("avertissement", pid,
                   "personnage actif sans tete, ni mains, ni temoignage, ni "
                   "place dans la journee — "
                   "donne-lui une entree dans intentions.json (il decide) ou "
                   "dans activites.json (son affaire tourne seule), ou repasse-"
                   "le dormant")

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


# ------------------------------------------------------------- LA RUMEUR

def temoins_des_incidents(e):
    """Les gens nommes en `depuis` d'un relais : les temoins.

    Un temoin n'a PAS de tete dans intentions.json, et c'est voulu : il n'a pas
    de projet, il a vu quelque chose et il le raconte. Une tete coute du budget
    d'echelle et derive des qu'on ne la relit plus — on ne peuple pas la
    simulation de gens qui n'ont rien a poursuivre. S'il se met a en avoir un,
    il sera promu par les voies normales.
    """
    noms = set()
    for inc in e.incidents:
        for ent in inc.get("propage") or []:
            if isinstance(ent, dict) and ent.get("depuis") in e.perso_par_id:
                noms.add(ent["depuis"])
    return noms


def rang_certitude(valeur):
    """sure=2, rapportee=1, rumeur=0. Inconnu -> rapportee, au milieu."""
    try:
        return len(CERTITUDES) - 1 - CERTITUDES.index(valeur)
    except ValueError:
        return 1


def degrader(valeur):
    """Ce que devient une certitude apres un saut de bouche a oreille."""
    rang = rang_certitude(valeur)
    return CERTITUDES[len(CERTITUDES) - 1 - max(rang - 1, 0)]


def relais_de(incident):
    """Le foyer et tout ce qui a ete gagne, au meme format {ou, date, ...}."""
    relais = [{"ou": incident.get("ou"), "date": incident.get("date"),
               "certitude": incident.get("certitude"), "foyer": True,
               "ames": incident.get("ames")}]
    for ent in incident.get("propage") or []:
        if isinstance(ent, str):
            relais.append({"ou": ent, "date": None, "certitude": None})
        elif isinstance(ent, dict):
            relais.append(dict(ent))
    return [r for r in relais if r.get("ou")]


def saut_rumeur(e, depuis, vers):
    """Jours d'un saut de rumeur. Plus lent que le cavalier, par principe."""
    plein = jours_de_route(e, depuis, vers, "cavalier")
    if plein is None:
        return None
    haut, bas = LENTEUR_RUMEUR
    return max((plein * haut + bas - 1) // bas, SAUT_RUMEUR_MINIMUM)


def propager_rumeurs(e, fin, cible):
    """Ce qu'une rumeur gagne dans la fenetre. Le script n'ecrit aucune prose.

    Une rumeur n'a pas de porteur nomme : elle saute de proche en proche, et se
    deforme A CHAQUE SAUT. Le tick propose le saut, sa date et la certitude
    DEGRADEE d'un cran ; la `version` — ce qui se dit vraiment la-bas, de
    travers — est ecrite a la main par le MJ. C'est le seul endroit ou le
    brouillard se fabrique, et une machine n'a rien a y faire.

    Les places candidates ne sont pas tout le royaume : ce sont celles que le MJ
    a lui-meme portees en `risque[]`, plus les voisines a portee de voix d'une
    place deja gagnee (PORTEE_SAUT_RUMEUR jours de cavalier).
    """
    lieu_joueur = e.lieu((e.perso_par_id.get(e.joueur) or {}).get("lieu_id"))
    sauts, immobiles = [], []

    for inc in e.incidents:
        if inc.get("feu") == "eteint":
            continue
        relais = relais_de(inc)
        prises = {e.lieu(r["ou"]) for r in relais if e.lieu(r["ou"])}
        derniere = max([jour_absolu(r.get("date")) for r in relais
                        if jour_absolu(r.get("date")) is not None] or [None]
                       ) if any(jour_absolu(r.get("date")) is not None
                                for r in relais) else None

        # les craintes du MJ d'abord : c'est lui qui a dit ou ca peut prendre
        candidats = {}
        for crainte in inc.get("risque") or []:
            ou = crainte if isinstance(crainte, str) else (
                crainte.get("ou") if isinstance(crainte, dict) else None)
            canon = e.lieu(ou)
            if canon and canon not in prises:
                candidats[canon] = {
                    "raison": "risque",
                    "ames": (crainte.get("ames")
                             if isinstance(crainte, dict) else None),
                    "note": (crainte.get("note")
                             if isinstance(crainte, dict) else None),
                }
        # puis le voisinage immediat de ce qui a deja pris — mais seulement si
        # le feu est VIF. Une chose qui `couve` ne gagne pas de terrain toute
        # seule : elle n'ira que la ou le MJ a ecrit qu'elle risque de prendre.
        for lid in (e.fiche_lieu if inc.get("feu") == "vif" else ()):
            if lid in prises or lid in candidats:
                continue
            proche = min([jours_de_route(e, p, lid, "cavalier") or 99
                          for p in prises] or [99])
            if proche <= PORTEE_SAUT_RUMEUR:
                candidats[lid] = {"raison": "voisin", "ames": None,
                                  "note": None}

        propres = []
        for vers, quoi in sorted(candidats.items()):
            # la source la plus favorable : celle qui l'y amene le plus tot
            meilleur = None
            for r in relais:
                depuis = e.lieu(r["ou"])
                depart = jour_absolu(r.get("date"))
                if not depuis or depart is None:
                    continue
                jours = saut_rumeur(e, depuis, vers)
                if jours is None:
                    continue
                arrivee = depart + jours
                if meilleur is None or arrivee < meilleur[0]:
                    meilleur = (arrivee, depuis, r)
            if meilleur is None or meilleur[0] > fin:
                continue
            arrivee, depuis, source = meilleur
            propres.append({
                "incident_id": inc.get("id"),
                "nom": inc.get("nom"),
                "feu": inc.get("feu"),
                "depuis": depuis,
                "vers": vers,
                "date": date_de(arrivee),
                "en_retard": arrivee < e.aujourdhui,
                "certitude_source": source.get("certitude")
                                    or inc.get("certitude"),
                "certitude_proposee": degrader(source.get("certitude")
                                               or inc.get("certitude")),
                "raison": quoi["raison"],
                "ames_estimees": quoi["ames"],
                "note_du_mj": quoi["note"],
                "atteint_le_joueur": bool(lieu_joueur) and vers == lieu_joueur,
                "contenu_a_ecrire": (
                    "le MJ ecrit ce qui se dit LA-BAS, deforme d'un cran — "
                    "le script n'invente aucune prose"),
            })

        # Une rumeur ne prend pas dix places d'un coup : les craintes ecrites
        # par le MJ passent toutes, le voisinage est plafonne aux plus proches.
        # Sans ce plafond, une fenetre de six jours propose vingt sauts et le MJ
        # ne les relit plus — ce qui revient a ne rien proposer du tout.
        propres.sort(key=lambda s: jour_absolu(s["date"]) or 0)
        garde, voisins = [], 0
        for s in propres:
            if s["raison"] == "voisin":
                if voisins >= VOISINS_PAR_RUMEUR and not s["atteint_le_joueur"]:
                    continue
                voisins += 1
            garde.append(s)
        sauts.extend(garde)

        # une rumeur qui n'a pas bouge depuis longtemps : elle ment sur elle-meme
        toleree = SILENCE_RUMEUR.get(inc.get("feu"))
        if toleree is not None and derniere is not None:
            silence = e.aujourdhui - derniere
            if silence > toleree:
                immobiles.append({
                    "incident_id": inc.get("id"),
                    "nom": inc.get("nom"),
                    "feu": inc.get("feu"),
                    "silence_jours": silence,
                    "derniere_prise": date_de(derniere),
                })

    sauts.sort(key=lambda s: jour_absolu(s["date"]) or 0)
    return sauts, immobiles


def sans_accents(texte):
    plat = (texte or "").lower()
    for a, b in (("àâä", "a"), ("éèêë", "e"), ("îï", "i"), ("ôö", "o"),
                 ("ùûü", "u"), ("ç", "c"), ("-", " "), ("'", " ")):
        for lettre in a:
            plat = plat.replace(lettre, b)
    return plat


def lieu_cite(e, texte):
    """Le lieu nomme dans un texte d'etape, s'il y en a un de reconnaissable.

    Heuristique assumee : on cherche le nom (ou l'id) d'un lieu connu dans la
    phrase. C'est le seul moyen de deviner qu'une etape fait VOYAGER quelqu'un
    sans inventer un journal de deplacements.
    """
    plat = sans_accents(texte)
    if not plat:
        return None
    for lid, fiche in e.fiche_lieu.items():
        for etiquette in [fiche.get("nom") or "", lid]:
            aiguille = sans_accents(etiquette)
            if len(aiguille) >= 5 and aiguille in plat:
                return lid
    return None


def detecter_bouches(e, a_resoudre, tombent):
    """Qui arrive ou, et ce qu'il apporte que personne sur place ne sait.

    Deux sources, toutes deux DEJA presentes dans le tick — on branche ce qui
    existe, on n'invente pas de table :
    1. un evenement de la fenetre qui se tient quelque part, dont un acteur
       n'est pas encore sur place : il faudra bien qu'il y vienne ;
    2. une etape de plan qui tombe et dont le texte nomme un autre lieu.

    Le script sort le DIFFERENTIEL de croyances, jamais un verdict : il ne
    recopie rien, ne reecrit aucune tete. Un homme qui sait ne raconte pas tout,
    et ment parfois — c'est au MJ de dire ce qui se dit.
    """
    arrivees = {}       # (personnage, lieu) -> entree

    def noter(pid, vers, source, indice, quand):
        tete = e.intention_par_id.get(pid)
        if tete is None or pid == e.joueur:
            return          # sans tete, rien a porter ; le joueur a sa bouche
        canon = e.lieu(vers)
        ici = e.lieu((e.perso_par_id.get(pid) or {}).get("lieu_id"))
        if not canon or canon == ici:
            return          # deja sur place : personne n'arrive
        cle = (pid, canon)
        if cle in arrivees:
            return
        if source == "etape":
            # le lieu n'est que CITE dans la phrase : il peut n'y envoyer qu'un
            # homme, ou en parler sans y aller. A verifier d'un coup d'oeil.
            indice = "{}  [lieu seulement cite — verifie qu'il y va]".format(
                indice)
        arrivees[cle] = {
            "personnage_id": pid,
            "echelle": echelle_de(tete),
            "de": ici,
            "vers": canon,
            "source": source,
            "indice": indice,
            "date": quand,
        }

    for ev in a_resoudre:
        if not ev.get("lieu_id"):
            continue
        for pid in ev.get("acteurs") or []:
            noter(pid, ev["lieu_id"], "evenement", ev.get("id"), ev.get("date"))
    for s in tombent:
        vers = lieu_cite(e, s.get("quoi") or "")
        if vers:
            noter(s["personnage_id"], vers, "etape", s.get("quoi"),
                  s.get("date_estimee"))

    # ce que les tetes DEJA sur place tiennent pour vrai, lieu par lieu
    su_sur_place = {}
    for tete in e.intentions:
        pid = tete.get("personnage_id")
        lid = e.lieu((e.perso_par_id.get(pid) or {}).get("lieu_id"))
        if lid:
            su_sur_place.setdefault(lid, []).append((pid, croyances_de(tete)))

    lieu_joueur = e.lieu((e.perso_par_id.get(e.joueur) or {}).get("lieu_id"))

    bouches = []
    for (pid, vers), entree in sorted(arrivees.items()):
        tete = e.intention_par_id[pid]
        sur_place = su_sur_place.get(vers, [])
        apporte, deja = [], []
        for croyance in croyances_de(tete):
            porteurs = [autre for autre, sues in sur_place if autre != pid
                        and any(se_recoupent(croyance, s) for s in sues)]
            if porteurs:
                deja.append({"croyance": croyance, "su_par": sorted(porteurs)})
            else:
                apporte.append(croyance)
        entree["apporte"] = apporte
        entree["deja_su_sur_place"] = deja
        entree["tetes_sur_place"] = sorted(a for a, _ in sur_place if a != pid)
        # Le drapeau joueur est reserve aux arrivees SURES (source evenement).
        # Le cout d'un faux positif est asymetrique : bruyant chez le joueur,
        # inoffensif ailleurs. Une arrivee deduite d'une etape reste grise.
        entree["arrive_chez_le_joueur"] = (
            bool(lieu_joueur) and vers == lieu_joueur
            and entree["source"] == "evenement")
        bouches.append(entree)
    return bouches


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


CLES_BOOK = {"id", "lieu_id", "salle_id", "acteur_id", "prive",
             "titre", "sous_titre", "type", "couleur",
             "colonnes", "lignes", "pages"}

# Les genres de volume connus de ecrans/modules/books.js. Un type inventé ne
# casse rien — le livre s'affiche sans teinte — mais il ne donne pas la couleur
# qu'on croyait avoir demandée.
TYPES_BOOK = {"registre", "carnet", "plan", "memento", "dossier", "regle",
              "oeuvre"}


def verifier_books(e, r):
    """Les livres : ce qui les empeche de s'afficher, ou les fait doubler.

    Le module ecrans/modules/books.js ne lit QUE le format de docs/books.md.
    Une cle inventee ne fait pas d'erreur a l'ecran : elle est ignoree en
    silence, et le MJ croit avoir ecrit quelque chose qui n'existe pas.
    """
    vus, titres = set(), {}
    for livre in e.books:
        bid = livre.get("id")
        etiq = "book {}".format(bid or "?")
        if not bid:
            r.dire("grave", etiq, "livre sans id")
            continue
        if bid in vus:
            r.dire("grave", etiq, "deux livres portent cet id")
        vus.add(bid)

        titre = (livre.get("titre") or "").strip().lower()
        if titre and titre in titres and titres[titre] != bid:
            r.dire("avertissement", etiq,
                   "meme titre que {!r} — deux onglets identiques a l'ecran ; "
                   "une session a sans doute recree ce que l'autre avait ecrit"
                   .format(titres[titre]))
        if titre:
            titres.setdefault(titre, bid)

        pose, porte = livre.get("salle_id"), livre.get("acteur_id")
        if not pose and not porte:
            r.dire("grave", etiq, "ni salle_id ni acteur_id : ce livre n'est "
                                  "nulle part, il ne s'affichera jamais")
        if pose and porte:
            r.dire("grave", etiq, "salle_id ET acteur_id : un livre est pose "
                                  "ou porte, jamais les deux")
        if porte and not e.perso_par_id.get(porte):
            r.dire("grave", etiq, "acteur_id inconnu : {!r}".format(porte))
        if pose and livre.get("lieu_id") and not e.lieu(livre["lieu_id"]):
            r.dire("grave", etiq, "lieu_id inconnu : {!r}".format(livre["lieu_id"]))
        if pose and not livre.get("lieu_id"):
            r.dire("avertissement", etiq,
                   "salle_id sans lieu_id : le livre suivra le joueur de "
                   "chateau en chateau")

        genre = livre.get("type")
        if genre is not None and str(genre).lower() not in TYPES_BOOK:
            r.dire("avertissement", etiq,
                   "type inconnu : {!r} — le livre s'affichera sans teinte ; "
                   "genres connus : {} (voir docs/books.md)"
                   .format(genre, ", ".join(sorted(TYPES_BOOK))))

        inconnues = sorted(set(livre) - CLES_BOOK)
        if inconnues:
            r.dire("grave", etiq, "cles hors format, ignorees a l'ecran : {} "
                                  "(voir docs/books.md)".format(", ".join(inconnues)))

        colonnes = livre.get("colonnes") or []
        lignes = livre.get("lignes") or []
        if lignes and not colonnes:
            r.dire("avertissement", etiq, "des lignes sans colonnes : le tableau "
                                          "s'affichera sans en-tete")
        for n, ligne in enumerate(lignes, 1):
            cellules = ligne if isinstance(ligne, list) else (ligne or {}).get("cellules")
            if cellules is None:
                r.dire("grave", etiq, "ligne {} sans `cellules`".format(n))
                continue
            if colonnes and len(cellules) != len(colonnes):
                r.dire("grave", etiq,
                       "ligne {} : {} cellules pour {} colonnes"
                       .format(n, len(cellules), len(colonnes)))
        if not lignes and not (livre.get("pages") or []) and not colonnes:
            r.dire("note", etiq, "livre vide : ni colonnes, ni lignes, ni pages")


def verifier_activites(e, r):
    """Les mains : ce qui empeche l'arithmetique d'etre juste."""
    vus = set()
    for act in e.activites:
        aid = act.get("id")
        etiq = "activite {}".format(aid or "?")
        if not aid:
            r.dire("grave", etiq, "activite sans id")
            continue
        if aid in vus:
            r.dire("grave", etiq, "id d'activite en double")
        vus.add(aid)

        p = act.get("porteur") or {}
        if p.get("type") == "personnage":
            perso = e.perso_par_id.get(p.get("id"))
            if perso is None:
                r.dire("grave", etiq,
                       "porteur inconnu : {!r}".format(p.get("id")))
            elif perso.get("etat") == "mort":
                r.dire("avertissement", etiq,
                       "le porteur {} est mort — l'affaire ne remonte plus "
                       "rien, et c'est peut-etre voulu".format(p.get("id")))
        elif p.get("type") == "lieu" and p.get("id") and not e.lieu(p["id"]):
            r.dire("grave", etiq, "lieu porteur inconnu : {!r}".format(p["id"]))
        elif not p.get("type"):
            r.dire("avertissement", etiq, "aucun porteur declare")

        if act.get("lieu_id") and not e.lieu(act["lieu_id"]):
            r.dire("grave", etiq,
                   "lieu_id inconnu : {!r}".format(act["lieu_id"]))

        mesures = act.get("mesure") or []
        if not mesures:
            r.dire("grave", etiq, "aucune mesure — une activite sans compteur "
                                  "ne produit rien et ne sert a rien")
        if len(mesures) > 3:
            r.dire("avertissement", etiq,
                   "{} mesures (3 au plus) — decoupe l'affaire en deux"
                   .format(len(mesures)))

        ids_mesure = set()
        for mes in mesures:
            mid = mes.get("id")
            sous = "{} / {}".format(etiq, mid or "?")
            if not mid:
                r.dire("grave", sous, "mesure sans id")
                continue
            if mid in ids_mesure:
                r.dire("grave", sous, "id de mesure en double dans l'activite")
            ids_mesure.add(mid)

            if not isinstance(mes.get("valeur"), int):
                r.dire("grave", sous, "valeur absente ou non entiere — tout "
                                      "est en entiers, jamais en flottants")
            rythme = mes.get("rythme")
            if not isinstance(rythme, dict):
                r.dire("grave", sous, "rythme absent : la mesure ne bougera "
                                      "jamais")
            else:
                par, pas = rythme.get("par"), rythme.get("jours", 1)
                if not isinstance(par, int):
                    r.dire("grave", sous, "rythme.par non entier")
                if not isinstance(pas, int) or pas <= 0:
                    r.dire("grave", sous, "rythme.jours doit etre un entier > 0")
                elif not isinstance(mes.get("reliquat", 0), int) or \
                        not 0 <= mes.get("reliquat", 0) < pas:
                    r.dire("avertissement", sous,
                           "reliquat hors de [0, {}[ — tick.py le remettra "
                           "droit au prochain calcul".format(pas))
            bas, haut = mes.get("plancher"), mes.get("plafond")
            if isinstance(bas, int) and isinstance(haut, int) and bas > haut:
                r.dire("grave", sous, "plancher au-dessus du plafond")
            for d in mes.get("depend_de") or []:
                if d not in e.mesure_par_adresse:
                    r.dire("grave", sous,
                           "depend_de pointe dans le vide : {!r}".format(d))

        for seuil in act.get("seuils") or []:
            sid = seuil.get("id")
            sous = "{} / seuil {}".format(etiq, sid or "?")
            if seuil.get("mesure_id") not in ids_mesure:
                r.dire("grave", sous, "mesure_id inconnu dans cette activite : "
                                      "{!r}".format(seuil.get("mesure_id")))
            if seuil.get("quand") not in ("sous", "sur"):
                r.dire("grave", sous, "'quand' doit valoir 'sous' ou 'sur'")
            if not isinstance(seuil.get("valeur"), int):
                r.dire("grave", sous, "valeur de bascule non entiere")
            if seuil.get("promeut") not in ("orbite", "scene"):
                r.dire("grave", sous, "'promeut' doit valoir 'orbite' ou 'scene'")
            if not seuil.get("affaire"):
                r.dire("avertissement", sous,
                       "aucune 'affaire' ecrite a froid — le jour ou le seuil "
                       "saute, tu improviseras la bifurcation")

            # un seuil franchi doit avoir donne une tete au porteur ;
            # un seuil retombe ne doit plus en couter une.
            if p.get("type") != "personnage" or not p.get("id"):
                continue
            tete = e.intention_par_id.get(p["id"])
            mes = next((m for m in mesures
                        if m.get("id") == seuil.get("mesure_id")), None)
            if mes is None or not isinstance(mes.get("valeur"), int):
                continue
            encore = seuil_franchi(mes["valeur"], seuil)
            if seuil.get("franchi_le") and tete is None:
                r.dire("grave", sous,
                       "seuil franchi le {} et {} n'a toujours pas de tete en "
                       "'{}' — la crise ne se joue nulle part".format(
                           seuil["franchi_le"], p["id"], seuil.get("promeut")))
            elif seuil.get("franchi_le") and not encore:
                r.dire("avertissement", sous,
                       "la mesure est repassee du bon cote mais franchi_le "
                       "tient toujours — remets-le a null")
            elif not seuil.get("franchi_le") and encore:
                r.dire("avertissement", sous,
                       "la mesure est du mauvais cote sans que franchi_le soit "
                       "pose — le prochain tick le posera")


def verifier_plis(e, r):
    """Le courrier : ce qui traine, ce qui vole sans oiseau, ce qui n'a pas de main."""
    vus = set()
    # corbeaux en vol, par (lieu de depart, destination)
    en_vol = {}
    for pli in e.plis:
        pid = pli.get("id")
        etiq = "pli {}".format(pid or "?")
        if not isinstance(pli, dict) or not pid:
            r.dire("grave", etiq, "pli sans id")
            continue
        if pid in vus:
            r.dire("grave", etiq, "id de pli en double")
        vus.add(pid)

        if pli.get("canal") not in CANAUX_PLI:
            r.dire("grave", etiq, "canal {!r} hors {} — la rumeur et le temoin "
                                  "ne sont pas des objets, ils restent a "
                                  "evenements.diffusion".format(pli.get("canal"),
                                                                CANAUX_PLI))
        etat = pli.get("etat")
        if etat not in ETATS_PLI:
            r.dire("grave", etiq, "etat {!r} hors {}".format(etat, ETATS_PLI))
        if not pli.get("porte"):
            r.dire("grave", etiq, "'porte' vide — un pli sans texte fige ne "
                                  "porte rien et ne peut pas arriver perime")
        for champ in ("de", "pour"):
            if pli.get(champ) and pli[champ] not in e.perso_par_id:
                r.dire("grave", etiq, "{} inconnu : {!r}".format(champ,
                                                                 pli[champ]))
        if pli.get("vers") and not e.lieu(pli["vers"]):
            r.dire("grave", etiq, "'vers' inconnu : {!r}".format(pli["vers"]))
        if pli.get("depuis") and not e.lieu(pli["depuis"]):
            r.dire("grave", etiq, "'depuis' inconnu : {!r}".format(pli["depuis"]))
        if pli.get("main") and pli["main"] not in e.perso_par_id:
            r.dire("grave", etiq, "'main' inconnue : {!r}".format(pli["main"]))

        # un pli en main sans main : personne ne l'a, et personne ne l'a lu
        if etat in ETATS_PLI_EN_MAIN and not pli.get("main"):
            r.dire("grave", etiq,
                   "{} sans 'main' — un pli est toujours dans la main de "
                   "quelqu'un ; dis qui l'a".format(etat))
        if etat == "en-route" and pli.get("main"):
            r.dire("avertissement", etiq,
                   "en route et pourtant dans une main ({}) — s'il chemine, "
                   "'main' doit etre null".format(pli["main"]))

        attendu = jour_absolu(pli.get("attendu_le"))
        parti = jour_absolu(pli.get("parti_le"))
        if attendu is None:
            r.dire("grave", etiq, "attendu_le absent ou illisible")
        elif parti is not None and attendu < parti:
            r.dire("grave", etiq, "attendu le {} alors qu'il est parti le {}"
                   .format(fmt(pli["attendu_le"]), fmt(pli["parti_le"])))
        elif etat == "en-route":
            retard = e.aujourdhui - attendu
            if retard > TOLERANCE_PLI:
                r.dire("avertissement", etiq,
                       "toujours en route, attendu le {} il y a {} jours "
                       "(monde {}) — remis, retenu, ou perdu ?".format(
                           fmt(pli["attendu_le"]), retard, fmt(e.date)))

        # les corbeaux : un oiseau ne vole que vers la ou il est ne
        if pli.get("canal") == "corbeau" and etat == "en-route":
            depuis = e.depart_de(pli)
            vers = e.lieu(pli.get("vers"))
            if depuis is None:
                r.dire("avertissement", etiq,
                       "corbeau sans lieu de depart connu (ni 'depuis', ni "
                       "lieu_id lisible pour {!r}) — stock invérifiable"
                       .format(pli.get("de")))
            elif vers:
                en_vol[(depuis, vers)] = en_vol.get((depuis, vers), 0) + 1

    for (depuis, vers), nb in sorted(en_vol.items()):
        stock = e.roukerie(depuis)
        if not stock:
            continue        # roukerie non tenue : on ne reproche rien
        reste = stock.get(vers)
        if reste is None:
            r.dire("avertissement", "roukerie {}".format(depuis),
                   "{} corbeau(x) en vol vers {} alors que la roukerie n'y "
                   "eleve aucun oiseau — un corbeau ne vole que vers la ou il "
                   "est ne".format(nb, vers))
        elif not isinstance(reste, int) or reste < 0:
            r.dire("grave", "roukerie {}".format(depuis),
                   "stock vers {} a {!r} — un envoi de trop a ete consomme"
                   .format(vers, reste))

    for lid, fiche in sorted(e.fiche_lieu.items()):
        stock = fiche.get("roukerie")
        if stock is None:
            continue
        if not isinstance(stock, dict):
            r.dire("grave", "roukerie {}".format(lid),
                   "'roukerie' doit etre un objet {lieu_id: nombre}")
            continue
        for origine, nb in sorted(stock.items()):
            if not e.lieu(origine):
                r.dire("grave", "roukerie {}".format(lid),
                       "lieu d'origine inconnu : {!r}".format(origine))
            if not isinstance(nb, int) or nb < 0:
                r.dire("grave", "roukerie {}".format(lid),
                       "stock vers {} non entier ou negatif : {!r}".format(
                           origine, nb))


def verifier_rumeurs(e, r):
    """Les incidents qui servent de rumeurs. En gravite 'note', jamais bloquant.

    Deux fautes, et ce sont les deux seules qu'une machine sache voir :
    une rumeur qui n'a pas bouge depuis longtemps (elle devrait avancer ou
    s'eteindre), et une fiabilite qui n'a pas decru en se propageant — un fait
    ne devient jamais plus sur en passant de bouche en bouche.
    """
    for inc in e.incidents:
        iid = inc.get("id", "?")
        etiq = "rumeur {}".format(iid)
        if inc.get("ou") and not e.lieu(inc["ou"]):
            r.dire("grave", etiq, "foyer inconnu : {!r}".format(inc["ou"]))

        relais = relais_de(inc)
        dates = [jour_absolu(x.get("date")) for x in relais]
        dates = [d for d in dates if d is not None]
        toleree = SILENCE_RUMEUR.get(inc.get("feu"))
        if toleree is not None and dates:
            silence = e.aujourdhui - max(dates)
            if silence > toleree:
                r.dire("note", etiq,
                       "'{}' et rien de neuf depuis {} jours (tolerance {}) — "
                       "une rumeur avance ou s'eteint ; passe-la en 'couve' ou "
                       "'eteint', ou fais-lui gagner un endroit".format(
                           inc.get("feu"), silence, toleree))

        depart = rang_certitude(inc.get("certitude"))
        for ent in inc.get("propage") or []:
            if not isinstance(ent, dict) or not ent.get("ou"):
                continue
            # Un relais dont le `depuis` nomme QUELQU'UN n'est plus du bouche a
            # oreille : c'est une parole d'autorite, avec un nom dessus — le
            # deuxieme porteur, pas le troisieme. Il n'est donc pas tenu de
            # decroitre. `certitude` mesure la confiance de qui entend, pas la
            # verite : une proclamation fausse peut etre 'rapportee' sans que
            # rien ne cloche.
            if ent.get("depuis") in e.perso_par_id:
                continue
            if ent.get("certitude") is None:
                r.dire("note", etiq,
                       "le relais {} n'a pas de 'certitude' — il herite du foyer "
                       "et la rumeur ne se degrade jamais".format(ent["ou"]))
                continue
            if rang_certitude(ent["certitude"]) >= depart:
                r.dire("note", etiq,
                       "le relais {} est aussi sur ({}) que le foyer ({}) — une "
                       "chose ne devient pas plus vraie en passant de bouche en "
                       "bouche".format(ent["ou"], ent["certitude"],
                                       inc.get("certitude")))
            if not e.lieu(ent["ou"]):
                r.dire("grave", etiq,
                       "relais en lieu inconnu : {!r}".format(ent["ou"]))


def sources_possibles(e, pid):
    """Tout ce qui a PU apprendre quelque chose a ce personnage.

    HEURISTIQUE, et il faut la lire comme telle (docs/plis.md, « la bouche ») :
    on ne sait pas relire le francais, on rassemble les textes auxquels il a eu
    acces et on cherchera un recoupement de mots rares. Sont retenus :
      - les entrees de diffusion LIVREES qui le nomment, ou livrees a son lieu ;
      - les plis qu'il a en main, ou qui lui sont adresses et arrives ;
      - les actes qu'il a commis, dont il est dit `connu_de`, ou qui se sont
        produits sous ses yeux (meme lieu) ;
      - les paroles dont il est locuteur, destinataire ou temoin ;
      - les croyances des autres tetes presentes au meme endroit (la bouche).
    """
    lid = e.lieu((e.perso_par_id.get(pid) or {}).get("lieu_id"))
    textes = []

    for ev in e.evenements:
        for ent in ev.get("diffusion") or []:
            if not isinstance(ent, dict) or ent.get("livree") is not True:
                continue
            if pid in (ent.get("qui") or []) or (
                    ent.get("ou") and lid and e.lieu(ent["ou"]) == lid):
                textes.append(ent.get("version") or "")

    for pli in e.plis:
        if not isinstance(pli, dict) or pli.get("etat") not in ETATS_PLI_EN_MAIN:
            continue
        if pli.get("main") == pid or pli.get("pour") == pid:
            textes.append(pli.get("porte") or "")

    for acte in e.actes:
        if not isinstance(acte, dict):
            continue
        connu = acte.get("connu_de") or []
        vu = (acte.get("acteur_id") == pid or pid in connu or "tous" in connu
              or (lid and acte.get("lieu_id")
                  and e.lieu(acte["lieu_id"]) == lid))
        if vu:
            textes.append("{} {}".format(acte.get("quoi") or "",
                                         acte.get("description") or ""))

    for parole in e.paroles:
        if not isinstance(parole, dict):
            continue
        if pid in (parole.get("locuteur_id"), parole.get("destinataire_id")) \
                or pid in (parole.get("temoins") or []):
            textes.append(parole.get("contenu") or "")

    # LE TEMOIN et la rumeur : ce qu'un incident a apporte ICI. Un relais qui a
    # pris a son lieu lui est parvenu, et un relais dont il est lui-meme le
    # `depuis` est une chose qu'il a vue et racontee. Un temoin n'a pas de tete
    # (c'est voulu) : sans cette branche, ce qu'il apporte ne justifierait
    # jamais rien, et l'heuristique crierait au faux positif sur des faits
    # parfaitement portes.
    for inc in e.incidents:
        propre = inc.get("contenu") or ""
        if lid and e.lieu(inc.get("ou")) == lid:
            textes.append(propre)
        for ent in inc.get("propage") or []:
            if isinstance(ent, str):
                if lid and e.lieu(ent) == lid:
                    textes.append(propre)
                continue
            if not isinstance(ent, dict):
                continue
            arrive = lid and e.lieu(ent.get("ou")) == lid
            porte = ent.get("depuis") == pid
            if arrive or porte:
                textes.append(ent.get("contenu") or propre)

    if lid:
        for autre in e.intentions:
            aid = autre.get("personnage_id")
            if aid == pid:
                continue
            if e.lieu((e.perso_par_id.get(aid) or {}).get("lieu_id")) == lid:
                textes.extend(croyances_de(autre))

    return [t for t in textes if t]


def verifier_croyances_sans_porteur(e, r):
    """« Aucune croyance sans porteur » — en gravite 'note', jamais bloquante.

    C'est la garde de fond de la refonte : un fait n'entre dans une tete que
    parce que quelqu'un ou quelque chose l'y a porte. La verification exacte
    demanderait de comprendre le sens ; on se contente d'un recoupement de mots
    rares, et sur l'etat d'avant la refonte elle criera beaucoup — c'est attendu.
    Elle ne compte pas dans le code de sortie et sort sous 'NOTE'.
    """
    for tete in e.intentions:
        pid = tete.get("personnage_id")
        croyances = croyances_de(tete)
        if not pid or not croyances:
            continue
        textes = sources_possibles(e, pid)
        orphelines = [c for c in croyances
                      if not any(se_recoupent(c, t) for t in textes)]
        if not orphelines:
            continue
        r.dire("note", pid,
               "{}/{} croyance(s) sans porteur repere (heuristique de mots "
               "rares — ni pli, ni bouche sur place, ni acte, ni parole, ni "
               "diffusion livree ne les explique) : {}".format(
                   len(orphelines), len(croyances),
                   " | ".join(c[:70] for c in orphelines)))


def verifier_couts_chiffres(e, r):
    """Un cout d'etape qui cite une mesure doit citer une mesure qui existe."""
    for tete in e.intentions:
        for etape in etapes_de(tete):
            for c in couts_chiffres(etape):
                if c["mesure"] not in e.mesure_par_adresse:
                    r.dire("grave", "{} / {}".format(
                        tete.get("personnage_id"), etape.get("id")),
                        "cout cite une mesure inconnue : {!r}".format(
                            c["mesure"]))
                elif not isinstance(c.get("quantite"), int):
                    r.dire("avertissement", "{} / {}".format(
                        tete.get("personnage_id"), etape.get("id")),
                        "cout chiffre sans 'quantite' entiere : {!r}".format(
                            c["mesure"]))


def verifier_sieges(e, r):
    """Le siege vacant doit avoir une tete ; l'occupe ne doit pas en avoir.

    C'est la garde des sieges alternes. On quitte Rhaenyra pour jouer l'agent
    de Port-Real : elle redevient un PNJ, donc elle a besoin d'une tete, sans
    quoi elle passe la lune a ne rien faire pendant qu'on regarde ailleurs —
    et l'on ne s'en apercoit qu'en revenant s'asseoir, trois lunes trop tard.
    Le symetrique (une tete sous un siege occupe) est deja dit par
    verifier_intentions : le MJ jouerait le personnage du joueur.
    """
    for pid in sorted(e.sieges_vacants):
        if pid not in e.intention_par_id:
            r.dire("grave", pid,
                   "siege VACANT sans tete dans intentions.json — ce "
                   "personnage n'agira pas hors ecran tant qu'on ne lui en "
                   "ecrit pas une")
        perso = e.perso_par_id.get(pid)
        if perso is not None and perso.get("etat") != "actif":
            r.dire("avertissement", pid,
                   "siege vacant dont la fiche est '{}' — un siege qu'on "
                   "reprendra un jour reste actif".format(perso.get("etat")))
    for pid in sorted(e.sieges_occupes | e.sieges_vacants):
        if pid not in e.perso_par_id:
            r.dire("grave", pid,
                   "siege pour un personnage absent de personnages.json")
    if e.sieges and e.joueur and e.joueur in e.sieges_vacants:
        r.dire("avertissement", "journal",
               "journal.personnage_joueur_id vaut '{}' alors que son siege "
               "est marque vacant".format(e.joueur))


def verifier_affectations(e, r):
    """Les adresses physiques donnees en jeu tiennent-elles encore ?

    Une affectation joint une chose de la fiction a un batiment du monde
    engendre (voir scripts/affecter.py). Le monde se regenere ; l'affectation,
    non. Une cible disparue ne casse rien a l'ecran — elle ment en silence, et
    l'on continue de calculer des distances sur un batiment qui n'existe plus.
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import affecter
    except ImportError:
        return
    L = affecter.charger_liens()
    if not L["affectations"]:
        return
    try:
        # `verifier` ouvre lui-meme le monde nomme par CHAQUE affectation : le
        # batiment doit exister encore, et dans le bon monde. Un monde absent
        # se signale au lieu de faire taire toute la verification.
        maux = affecter.verifier(L)
    except SystemExit:
        return                       # pas de monde engendre : rien a verifier
    for mal in maux:
        r.dire("avertissement", "affectations", mal)


def verifier(e):
    r = Rapport()
    if not e.joueur:
        r.dire("avertissement", "journal",
               "personnage_joueur_id absent — impossible de proteger sa tete")
    verifier_sieges(e, r)
    verifier_intentions(e, r)
    verifier_evenements(e, r)
    verifier_personnages(e, r)
    verifier_activites(e, r)
    verifier_books(e, r)
    verifier_plis(e, r)
    verifier_couts_chiffres(e, r)
    verifier_rumeurs(e, r)
    verifier_croyances_sans_porteur(e, r)
    verifier_affectations(e, r)
    r.imprimer()
    # Les 'note' sont informatives : elles ne font pas echouer l'audit. La
    # croyance sans porteur crie fort sur l'etat d'avant la refonte, et ce
    # n'est pas une raison de bloquer le jeu.
    return 1 if [a for a in r.anomalies if a["gravite"] != "note"] else 0


# ----------------------------------------------------------- MODE B : tick

def calculer(e, cible, restriction, joueur=None):
    """Ce qui tombe entre monde.date et cible. Aucune decision, du calcul."""
    fin = jour_absolu(cible)
    jours = fin - e.aujourdhui
    fenetre = {"de": e.date, "a": cible, "jours": jours}

    # --- LES MAINS D'ABORD (docs/schema.md : activites.json)
    # La boucle des activites tourne AVANT celle des absents, parce que sa
    # sortie est son entree : un `cout` d'etape qui cite une adresse de mesure
    # se verifie contre la valeur d'APRES decompte, pas celle d'avant.
    mesures_apres = {}       # adresse -> valeur apres la fenetre
    activites, franchissements = [], []
    for act in e.activites:
        aid = act.get("id")
        absent = porteur_absent(e, act)
        lignes = []
        for mes in act.get("mesure") or []:
            adresse = "{}.{}".format(aid, mes.get("id"))
            par, _pas = rythme_de(mes)
            # une mesure gelee par une dependance au plancher ne bouge pas —
            # elle n'est pas remise a zero, et son reliquat est conserve
            gelee = [d for d in (mes.get("depend_de") or [])
                     if d in e.mesure_par_adresse
                     and au_plancher(e.mesure_par_adresse[d][1])]
            # porteur mort ou parti : ce qui produit s'arrete, ce qui coute
            # continue. C'est ainsi qu'une affaire pourrit toute seule.
            muet = absent and par > 0
            if gelee or muet:
                valeur = mes.get("valeur")
                reliquat = mes.get("reliquat", 0)
                borne = None
            else:
                valeur, reliquat, borne = decompter(mes, jours)
            mesures_apres[adresse] = valeur
            ligne = {
                "adresse": adresse,
                "quoi": mes.get("quoi"),
                "unite": mes.get("unite"),
                "avant": mes.get("valeur"),
                "apres": valeur,
                "reliquat_apres": reliquat,
            }
            if gelee:
                ligne["gelee_par"] = gelee
            if muet:
                ligne["porteur_absent"] = True
            if borne:
                ligne["bute_sur"] = borne
            lignes.append(ligne)

            for seuil in act.get("seuils") or []:
                if seuil.get("mesure_id") != mes.get("id"):
                    continue
                etait = bool(seuil.get("franchi_le"))
                est = seuil_franchi(valeur, seuil)
                if est == etait:
                    continue
                franchissements.append({
                    "activite_id": aid,
                    "seuil": seuil.get("id"),
                    "adresse": adresse,
                    "sens": "franchi" if est else "retombe",
                    "quand": seuil.get("quand"),
                    "borne": seuil.get("valeur"),
                    "valeur": valeur,
                    "porteur": act.get("porteur"),
                    "promeut": seuil.get("promeut"),
                    "affaire": seuil.get("affaire"),
                    "date": cible,
                })
        activites.append({
            "id": aid,
            "quoi": act.get("quoi"),
            "porteur": act.get("porteur"),
            "porteur_absent": absent,
            "mandat": act.get("mandat"),
            "mesures": lignes,
        })

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

    # --- LE COURRIER : ce qui arrive (docs/plis.md)
    # Rien n'atteint personne sans porteur. Un pli echu est REMIS, dans la main
    # du destinataire naturel du lieu — le mestre —, jamais dans celle du `pour`.
    plis_remis, plis_en_route = [], []
    for pli in e.plis:
        if not isinstance(pli, dict) or pli.get("etat") != "en-route":
            continue
        quand = jour_absolu(pli.get("attendu_le"))
        if quand is None:
            continue
        entree = {
            "id": pli.get("id"),
            "canal": pli.get("canal"),
            "de": pli.get("de"),
            "pour": pli.get("pour"),
            "vers": pli.get("vers"),
            "attendu_le": pli.get("attendu_le"),
            "scelle": pli.get("scelle"),
        }
        if quand > fin:
            entree["jours_encore"] = quand - fin
            plis_en_route.append(entree)
            continue
        main = e.destinataire_naturel(pli.get("vers"))
        entree["main"] = main
        entree["porte"] = pli.get("porte")
        entree["en_retard"] = quand < e.aujourdhui
        if main is None:
            entree["probleme"] = ("aucun destinataire naturel a {} — dis dans "
                                  "quelle main le pli tombe".format(
                                      pli.get("vers")))
        elif main == pli.get("pour"):
            # ca arrive (le pour EST le mestre) ; on le dit, ce n'est pas une faute
            entree["main_est_le_pour"] = True
        plis_remis.append(entree)
    plis_remis.sort(key=lambda x: jour_absolu(x["attendu_le"]) or 0)
    plis_en_route.sort(key=lambda x: jour_absolu(x["attendu_le"]) or 0)

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
            # Un cout peut CITER une mesure : {mesure, quantite}. Alors il se
            # verifie ici, contre la valeur d'apres decompte, et le si_bloque
            # se declenche par arithmetique. Un cout en clair reste au MJ.
            manque = chiffrer_cout(etape, mesures_apres)
            if manque:
                commun["cout_non_couvert"] = manque
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

    # --- LA BOUCHE : qui arrive, et ce qu'il apporte que personne ne sait ici
    bouches = detecter_bouches(e, a_resoudre, tombent)

    # --- LA RUMEUR : ce qui saute de proche en proche, sans porteur nomme
    rumeurs, rumeurs_immobiles = propager_rumeurs(e, fin, cible)

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
    for a in activites:
        for m in a["mesures"]:
            if m["apres"] == m["avant"] and \
                    m["reliquat_apres"] == 0 and "gelee_par" not in m:
                continue
            mutations.append({
                "table": "activites",
                "cible": a["id"],
                "operation": "mesure",
                "mesure": m["adresse"].split(".", 1)[1],
                "champs": {"valeur": m["apres"],
                           "reliquat": m["reliquat_apres"]},
                "pourquoi": "{} jour(s) ecoule(s){}".format(
                    jours,
                    " — gelee, la mesure ne bouge pas" if "gelee_par" in m
                    else ""),
            })
    for f in franchissements:
        mutations.append({
            "table": "activites",
            "cible": f["activite_id"],
            "operation": "seuil",
            "seuil": f["seuil"],
            "champs": {"franchi_le": cible if f["sens"] == "franchi" else None},
            "pourquoi": "{} {} {} (valeur {})".format(
                f["adresse"], f["quand"], f["borne"], f["valeur"]),
        })
    for s in avancent:
        mutations.append({
            "table": "intentions",
            "cible": s["personnage_id"],
            "operation": "etape",
            "etape": s["etape"],
            "champs": {"jours_restants": s["jours_restants_apres"]},
            "pourquoi": "{} jour(s) ecoule(s)".format(jours),
        })
    for p in plis_remis:
        champs = {"etat": "remis"}
        if p.get("main"):
            champs["main"] = p["main"]
        mutations.append({
            "table": "plis",
            "cible": p["id"],
            "operation": "pli",
            "champs": champs,
            "pourquoi": "arrive a {} le {}{}".format(
                p["vers"], fmt(p["attendu_le"]),
                "" if p.get("main")
                else " — SANS MAIN : pose-la toi-meme avant d'appliquer"),
        })
    for s in rumeurs:
        # `contenu` reste NUL a dessein : appliquer.py refusera le lot tant que
        # le MJ n'aura pas ecrit ce qui se dit la-bas. C'est la garde qui
        # empeche une machine de fabriquer du brouillard.
        mutations.append({
            "table": "jetons",
            "cible": s["incident_id"],
            "operation": "incident_propage",
            "valeur": {
                "ou": s["vers"],
                "date": s["date"],
                "certitude": s["certitude_proposee"],
                "ames": s["ames_estimees"],
                "depuis": s["depuis"],
                "contenu": None,
            },
            "pourquoi": "saute de {} ({} -> {}) — ECRIS le 'contenu' : ce qui "
                        "se dit la-bas, deforme. Sans lui, le lot est refuse."
                        .format(s["depuis"], s["certitude_source"],
                                s["certitude_proposee"]),
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
        "joueur": joueur,
        "empreintes": empreintes_etat(joueur),
        "avertissement": "Proposition — le MJ arbitre et applique lui-meme "
                         "dans etat/*.json. Ce fichier n'est pas de l'etat.",
        "fenetre": fenetre,
        "activites": activites,
        "seuils_franchis": franchissements,
        "acteurs_simules": [t.get("personnage_id") for t in simules],
        "acteurs_sautes_royaume": sorted(
            t.get("personnage_id") for t in sautes),
        "postures_permanentes": postures,
        "evenements_a_resoudre": a_resoudre,
        "nouvelles_a_livrer": nouvelles,
        "nouvelles_conditionnelles": conditionnelles,
        "bouches": bouches,
        "rumeurs_qui_sautent": rumeurs,
        "rumeurs_immobiles": rumeurs_immobiles,
        "plis_remis": plis_remis,
        "plis_encore_en_route": plis_en_route,
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

    # Les mains d'abord — c'est l'ordre de la boucle, et l'ordre de lecture.
    if prop.get("activites"):
        print("\nLes mains ({}) — ou en sont les choses :".format(
            len(prop["activites"])))
        for a in prop["activites"]:
            p = a.get("porteur") or {}
            qui = p.get("id") or "personne"
            print("  {:<26} ({}{})".format(
                a["id"], qui, ", ABSENT" if a.get("porteur_absent") else ""))
            for m in a["mesures"]:
                fleche = "{} -> {}".format(m["avant"], m["apres"])
                notes = []
                if m.get("gelee_par"):
                    notes.append("gelee par " + ", ".join(m["gelee_par"]))
                if m.get("porteur_absent"):
                    notes.append("ne produit plus, faute de porteur")
                if m.get("bute_sur"):
                    notes.append("bute sur le " + m["bute_sur"])
                print("      {:<34} {:>14} {} {}".format(
                    m["adresse"], fleche, m.get("unite") or "",
                    "— " + " ; ".join(notes) if notes else ""))

    if prop.get("seuils_franchis"):
        print("\nSEUILS ({}) :".format(len(prop["seuils_franchis"])))
        for s in prop["seuils_franchis"]:
            if s["sens"] == "retombe":
                print("  [retombe] {}.{} — la crise est close, redescends le"
                      " porteur d'echelle".format(s["activite_id"], s["seuil"]))
                continue
            p = s.get("porteur") or {}
            print("  [FRANCHI] {}.{} — {} {} {} (valeur {})".format(
                s["activite_id"], s["seuil"], s["adresse"], s["quand"],
                s["borne"], s["valeur"]))
            if p.get("type") == "personnage" and p.get("id"):
                print("      porteur : {} -> promouvoir en '{}'".format(
                    p["id"], s["promeut"]))
            else:
                # Un lieu ou une maison ne monte pas l'escalier. La crise est
                # reelle et n'a aucune bouche pour la dire : c'est au MJ de lui
                # en trouver une, ou d'assumer que le joueur l'apprenne trop tard.
                print("      porteur : {} — RIEN A PROMOUVOIR. La crise n'a "
                      "personne pour la porter :".format(
                          p.get("id") or "personne"))
                print("      donne-lui une bouche, ou laisse le joueur "
                      "l'apprendre trop tard (c'est une option, pas un bug).")
            print("      affaire : {}".format(s["affaire"]))

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

    if prop.get("bouches"):
        print("\nLes bouches ({}) — qui arrive, et ce qu'il porte dans la tete :"
              .format(len(prop["bouches"])))
        for b in prop["bouches"]:
            print("  {} : {} -> {} ({} {}){}".format(
                b["personnage_id"], b["de"] or "?", b["vers"], b["source"],
                b["indice"],
                "   << ARRIVE CHEZ LE JOUEUR" if b["arrive_chez_le_joueur"]
                else ""))
            if b["arrive_chez_le_joueur"]:
                print("      -> une entree info.json, avec une bouche et un "
                      "visage. Pas une croyance qui se recopie en silence.")
            if not b["apporte"]:
                print("      n'apporte rien qu'on ne sache deja ici.")
            for croyance in b["apporte"]:
                print("      + {}".format(croyance[:150]))
            if b["deja_su_sur_place"]:
                print("      ({} croyance(s) deja sue(s) sur place)".format(
                    len(b["deja_su_sur_place"])))
        print("      Le script ne recopie RIEN : a toi de dire ce qui se dit, "
              "ce qui se tait, et ce qui se ment.")

    if prop.get("rumeurs_qui_sautent") or prop.get("rumeurs_immobiles"):
        print("\nLes rumeurs ({} saut(s)) — de proche en proche, sans porteur :"
              .format(len(prop.get("rumeurs_qui_sautent") or [])))
        for s in prop.get("rumeurs_qui_sautent") or []:
            print("  {} {} : {} -> {} ({}, {} -> {}){}".format(
                fmt(s["date"]), s["incident_id"], s["depuis"], s["vers"],
                s["raison"], s["certitude_source"], s["certitude_proposee"],
                "   << ATTEINT LE JOUEUR" if s["atteint_le_joueur"] else ""))
            if s["atteint_le_joueur"]:
                print("      -> une entree info.json : source de bouche a "
                      "oreille, fiabilite basse. Personne ne l'a apportee.")
            if s["note_du_mj"]:
                print("      ta crainte : {}".format(s["note_du_mj"]))
        if prop.get("rumeurs_qui_sautent"):
            print("      ECRIS le 'contenu' de chaque saut dans les mutations : "
                  "une rumeur se deforme A CHAQUE bouche, et le script n'invente "
                  "aucune prose. Sans contenu, appliquer.py refuse le lot.")
        for i in prop.get("rumeurs_immobiles") or []:
            print("  [immobile] {} ({}) — rien de neuf depuis {} jours (derniere "
                  "prise {}) : fais-la avancer ou eteins-la.".format(
                      i["incident_id"], i["feu"], i["silence_jours"],
                      fmt(i["derniere_prise"])))

    if prop.get("plis_remis") or prop.get("plis_encore_en_route"):
        print("\nLe courrier — plis remis ({}) :".format(
            len(prop.get("plis_remis") or [])))
        for p in prop.get("plis_remis") or []:
            print("  {} {:<24} {} de {} pour {} -> {}{}".format(
                fmt(p["attendu_le"]), p["id"], p["canal"], p["de"], p["pour"],
                p["vers"], " (EN RETARD)" if p.get("en_retard") else ""))
            if p.get("main"):
                print("      remis en main de {} — ce n'est pas {} qui le "
                      "sait, c'est lui.".format(p["main"], p["pour"]))
            else:
                print("      {}".format(p.get("probleme")))
        for p in prop.get("plis_encore_en_route") or []:
            print("  [en route] {} vers {}, encore {} jour(s)".format(
                p["id"], p["vers"], p["jours_encore"]))

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


def tick(e, cible, restriction, joueur=None):
    if jour_absolu(cible) < e.aujourdhui:
        sys.exit("cible {} anterieure a monde.date {} — le tick n'avance "
                 "que dans un sens".format(fmt(cible), fmt(e.date)))
    prop = calculer(e, cible, restriction, joueur)
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
    ap.add_argument("--joueur", default=None, metavar="ID",
                    help="personnage_id dont les croyances (jetons, vues, "
                         "objectifs) seront scellees et appliquees. Inscrit "
                         "dans la proposition ; appliquer.py le reprend.")
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

    return tick(e, cible, set(args.acteur), args.joueur)


if __name__ == "__main__":
    sys.exit(main())
