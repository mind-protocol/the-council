# -*- coding: utf-8 -*-
"""LECTURE — tout l'etat charge une fois, et les jours de route.

CE QUE CE MODULE POSSEDE : le chargement de etat/*.json (lecture seule,
toujours, par la porte etat.expose.tables), la classe Etat avec ses index
(lieux, personnages, mesures, intentions, sieges mesures par occupation), et
l'estimation des jours de route entre deux lieux. Il possede aussi les
constantes du COURRIER (canaux, etats de pli, tolerances) : elles vivent a
cote de `jours_de_route` et des methodes plis d'Etat (roukerie,
destinataire_naturel, depart_de), qui sont leurs seuls lecteurs arithmetiques.

CE QU'IL REFUSE : toute ecriture (c'est scelle.py), toute interpretation
(gardes/ et fenetre.py jugent, lui charge).

CONSOMMATEURS : gardes/, fenetre.py, rumeur.py, resume.py, la facade tick.py,
et migrer_plis via la porte temps/expose.py (Etat, jours_de_route, CANAUX_PLI).
"""
import os
import sys

from temps.expose import occupation  # qui est ASSIS — mesure, pas drapeau
from temps.calendrier import jour_absolu
from etat.expose import tables  # LA PORTE de etat/
import documents_maison
import bibliotheque

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ETAT = os.path.join(RACINE, "etat")

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


def charger(nom, defaut):
    """Lit etat/<nom>.json par la porte. Corrompu : sys.exit, avec le chemin."""
    try:
        return tables.lire(nom, defaut)
    except tables.TableAbimee as err:
        sys.exit(str(err))


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
        # Les mesures appartiennent desormais aux maisons. Le calcul les voit
        # toutes ensemble, sans perdre la maison d'autorite de chaque entree.
        self.mains = documents_maison.charger_mains(ETAT)
        # La bibliotheque agrege les documents des maisons. Leur place reste
        # une propriete de fiction ; leur autorite de stockage est la maison.
        self.books = bibliotheque.charger(ETAT)
        # Les coffrets ou l'on range les volumes (docs/books.md). Une boite
        # donne sa place a ce qu'elle contient ; fichier absent = pas de
        # boites, et les livres gardent chacun la leur.
        brut = charger("boites", [])
        self.boites = brut.get("boites", []) if isinstance(brut, dict) else brut
        # Les pensees : ce qu'un homme a touche et ce que ca lui a appris.
        # A plat depuis que `travaux.json` a disparu — plus d'affaire a
        # raccrocher, une pensee porte son auteur, son jour et sa source.
        brut = charger("pensees", {})
        self.pensees = brut.get("pensees", []) if isinstance(brut, dict) else brut
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
        # ETRE ASSIS SE MESURE (voir scripts/occupation.py) : la veille de sa
        # session date de moins de deux heures reelles, ou son inbox porte une
        # action non traitee. Le champ `occupe` du fichier n'est qu'un cache,
        # et il a menti — quatre sieges a `true` alors que deux dormaient. On
        # garde le drapeau brut a cote, pour pouvoir dire qu'il a derive.
        self.mesures_sieges = {}
        try:
            self.mesures_sieges = {m["personnage_id"]: m
                                   for m in occupation.mesures()}
        except Exception:
            self.mesures_sieges = {}
        self.sieges_occupes = set()
        self.sieges_vacants = set()
        self.sieges_drapeau = {}
        for siege in self.sieges:
            pid = siege.get("personnage_id")
            if not pid:
                continue
            # Un siege de REGIE (Corneille) n'incarne personne : pas de fiche,
            # pas de tete, pas d'horloge. Il ne se verifie pas comme un siege,
            # il n'en est pas un — voir l'entete de roster() dans
            # scripts/occupation.py, qui l'ecarte de la mesure pour la meme
            # raison. Le laisser entrer ici le ferait crier a chaque passage.
            # Meme sort pour un siege d'une AUTRE PARTIE (`partie`) : les Sept
            # Chandelles partagent ce roster pour apparaitre au selecteur du
            # serveur, et rien d'autre. Sans fiche, sans tete et sans horloge
            # ICI, c'est voulu — le seul predicat fait foi (occupation.py).
            if occupation.hors_monde(siege):
                continue
            self.sieges_drapeau[pid] = bool(siege.get("occupe", True))
            mesure = self.mesures_sieges.get(pid)
            assis = (mesure["occupe"] if mesure is not None
                     else self.sieges_drapeau[pid])
            (self.sieges_occupes if assis else self.sieges_vacants).add(pid)
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
        # index des mesures par adresse <main_id>.<mesure_id> : c'est ce
        # que cite un `cout` d'etape de plan, et ce qui rend le si_bloque
        # arithmetique au lieu d'etre juge au doigt mouille.
        self.mesure_par_adresse = {}
        for act in self.mains:
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
