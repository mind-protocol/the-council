# -*- coding: utf-8 -*-
"""
partie_greffe.py — le repli d'une partie et ses règles (mj-partie.md, §3 à §5).

Pourquoi cette pièce est séparée de scripts/partie.py : elle ne connaît ni le
terminal, ni les livres, ni la présentation. Elle lit un jsonl append-only,
tient le grand livre, dit si un coup est recevable et pourquoi, applique un
coup, passe un tour. Ce qui se LIT (chaîne, pièce, grand livre, état) est dans
partie_lecture.py ; ce qui se MONTRE ou se CHERCHE, dans scripts/partie.py.
Une règle du jeu se change ici et nulle part ailleurs.
"""
import io
import json
import os

import partie_ecriture  # le verrou, la relecture du disque, l'append (A6/A10/A11)
import partie_tour      # ce qui tombe au passage du tour (annonce et application)
import partie_validite  # la recevabilité d'un coup, séparée pour rester lisible

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSSIER = os.path.join(RACINE, "etat", "parties")
JOURS_PAR_TOUR = 2  # un tour = deux jours du monde (mj-partie.md §4)  # regle: tour-deux-jours
DECK_MAX = 10
GEL_RETRAIT = 2  # regle: gels
GEL_FRAPPE = 1
TOURS_RECONSTRUCTION = 2
ARBITRE = "arbitre"   # le seul nom réservé : les camps sont ceux que la partie nomme, autant qu'elle veut
COUPS = ("viser", "sortir", "demander", "arbitrer", "bloquer", "lever", "agir",
         "justifier", "detruire", "retourner", "retirer", "reconstruire",
         "rearmer", "passer", "consigne", "constater", "tour")
# Ceux qui comptent pour « un coup par camp et par tour » : ni l'arbitre, ni ce
# qui ne coûte rien (demander, justifier, consigne). `viser` compte depuis le
# 3.9 : un état cible se pose un par un, comme les autres pièces, pour lisser
# la charge — dix états d'un bloc à l'ouverture, personne ne les lit.
COUPS_COMPTES = ("viser", "sortir", "bloquer", "lever", "agir", "detruire", "retourner",  # regle: un-coup-par-tour
                 "retirer", "reconstruire", "rearmer", "passer")
class _Emojis(dict):
    PALETTE = ("🔵", "🔴", "🟡", "🟣", "🟤", "⚪")

    def __missing__(self, camp):
        # un camp sans emoji attitré en reçoit un, distinct, dans l'ordre d'arrivée
        pris = set(self.values())
        self[camp] = next((e for e in self.PALETTE if e not in pris), "🔸")
        return self[camp]


EMOJI_CAMP = _Emojis({"noir": "⚫", "vert": "🟢", "arbitre": "🟠"})
EMOJI_COUP = {"viser": "🎯", "sortir": "🃏", "demander": "📦", "arbitrer": "⚖️",
              "bloquer": "🔒", "lever": "🗝️", "agir": "⚔️", "justifier": "❓",
              "detruire": "💥", "retourner": "🔄", "retirer": "🗑️",
              "reconstruire": "🔧", "rearmer": "➕",
              "passer": "⏸️", "consigne": "📋", "constater": "✅", "tour": "⏭️"}


def adverse(camp):
    """Compatibilité pour la partie à deux camps de la Danse. Le greffe ne s'en
    sert plus : ce qui s'oppose à une pièce, c'est le camp de sa CIBLE (`camp_de`)."""
    return "vert" if camp == "noir" else "noir"


def liste(x):
    if x is None:
        return []
    return list(x) if isinstance(x, (list, tuple)) else [x]


def au_deck(e, tour, reserve=False):  # regle: deck-calendrier
    """Un état est au deck s'il y est entré ; un état daté (deck vert = calendrier,
    mj-partie.md §2) n'y est qu'à partir de son tour. `reserve` compte aussi la
    place qu'il tient d'avance."""
    if e.get("sorti"):
        return False
    if int(e.get("arrive_tour") or 0) > tour:
        return bool(reserve)
    return True


def config(chemin):
    """Les réglages propres à UNE partie : `etat/parties/<id>.json` s'il existe
    (`coups_par_camp`, `sieges`, `coups_interdits`, `camps` — les camps déclarés
    d'avance, que `Partie.camps()` fond avec ceux des lignes pour qu'un camp qui
    n'a pas encore visé ait déjà sa place), sinon `_courante.json` quand elle
    la nomme, sinon rien. Ici et non dans la vue : le greffe s'en sert pour
    refuser un coup qu'une partie a sorti du jeu."""
    nom = os.path.splitext(os.path.basename(chemin))[0]
    for fichier, garde in ((os.path.join(DOSSIER, nom + ".json"), False),
                           (os.path.join(DOSSIER, "_courante.json"), True)):
        try:
            with io.open(fichier, encoding="utf-8") as f:
                c = json.load(f)
            if not garde or c.get("partie") == nom:
                return c
        except Exception:
            continue
    return {}


# ---------------------------------------------------------------- le repli
class Partie(object):
    """La position, repliée depuis les lignes. Rien ici n'est écrit à la main."""

    def __init__(self, chemin):
        self.chemin = chemin
        self.lignes = []
        self.tour = 1
        self.etats = {}       # id -> {camp, texte, sert, deck, vrai}
        self.ressources = {}  # id -> {camp, lieu, nombre, tenu_par, arrive_tour,
                              #        gel_jusqu, engagee_par:[], detruite, en_attente:n}
        self.blocages = {}    # id -> {camp, sur, engage, texte, tombe}
        self.cles = {}        # id -> {camp, ouvre:[], engage, texte, suspendue_par, retiree}
        self.maillons = {}    # id -> {camp, realise, qui, avec, etat, texte}
        self.menaces = {}     # id -> {camp, cible, engage, arrive_tour, realisee, tombee}
        self.consignes = {}   # piece -> texte
        self.avertissements = []
        self._config = None
        if os.path.exists(chemin):
            with io.open(chemin, "r", encoding="utf-8") as f:
                partie_ecriture.rattraper(self, f.read().split("\n"), 0)
        for c in self.camps():
            EMOJI_CAMP[c]   # amorce la palette dans l'ordre des camps : sinon la
            # couleur d'un camp sans emoji attitre dependait de l'ordre des lectures

    # ---- validité --------------------------------------------------------
    def verifier(self, l):
        """Rend la liste des refus (partie_validite.py). Vide = le coup est recevable."""
        return partie_validite.verifier(self, l)

    def _pieces_libres(self, camp, pieces, par):
        return partie_validite.pieces_libres(self, camp, pieces, par)

    def configuration(self):
        """`config(self.chemin)`, lue une fois par partie chargée."""
        if self._config is None:
            self._config = config(self.chemin)
        return self._config

    def camps(self):  # regle: trait-ordre-d-entree
        """Les camps de la partie, dans l'ordre où ils sont entrés ; jamais
        l'arbitre. Puis ceux que la configuration déclare (`camps`) et qui
        n'ont encore rien joué : sans eux, le second joueur d'une partie
        neuve n'avait pas de deck ni de trait, et l'écran le murait (B3)."""
        out = []
        for x in self.lignes:
            c = x.get("camp")
            if c and c != ARBITRE and c not in out:
                out.append(c)
        for c in liste(self.configuration().get("camps")):
            if isinstance(c, dict):
                c = c.get("id") or c.get("camp")
            if c and isinstance(c, str) and c != ARBITRE and c not in out:
                out.append(c)
        return out

    def camp_de(self, cible):  # regle: blocage-par-un-autre-camp
        """Le camp d'un objet, quel qu'il soit — c'est lui que contrarie ce qui
        se pose sur cet objet."""
        for reg in (self.etats, self.blocages, self.cles, self.maillons, self.menaces, self.ressources):
            if cible in reg:
                return reg[cible]["camp"]
        return None

    def _lignes_visees(self, sur):  # regle: arbitrage-vise-un-id
        """Un arbitrage vise une ligne par son numéro, ou la dernière ligne qui porte cet id."""
        out = []
        for s in liste(sur):
            # l'id d'abord (un id de pièce est souvent tout en chiffres), le numéro de ligne sinon
            trouve = [x for x in self.lignes if str(x.get("id")) == str(s)
                      and x.get("coup") in ("demander", "detruire", "retourner", "lever", "bloquer")]
            if trouve:
                out.append(trouve[-1])
            elif isinstance(s, int) or (isinstance(s, str) and s.isdigit()):
                out += [x for x in self.lignes if x.get("n") == int(s)]
        return out

    # ---- application ----------------------------------------------------
    def _engager(self, pieces, par):
        for p in liste(pieces):
            r = self.ressources.get(p)
            if r is not None and par not in r["engagee_par"]:
                r["engagee_par"].append(par)

    def _prete_tour(self, pieces):  # regle: piece-en-route-s-engage
        """Le tour où toutes ces pièces sont arrivées : une pièce en route s'engage
        dès maintenant (réservée, visible de l'adversaire), mais la clé ne vaut
        qu'à ce tour-là — mj-partie.md §4."""
        t = self.tour
        for p in liste(pieces):
            r = self.ressources.get(p)
            if r is not None:
                t = max(t, int(r.get("arrive_tour") or 0))
        return t

    def _tomber(self, bid, gel=0):  # regle: cle-tenue
        """Un blocage tombe (retiré, sans portée, sa pièce partie). Une clé qui
        n'ouvrait plus que des blocages tombés a fait son office : elle est
        *tenue*, ses pièces reviennent sans gel — mj-partie.md règle 10."""
        b = self.blocages[bid]
        b["tombe"] = True
        self._liberer(bid, gel)
        for kid, k in self.cles.items():
            if bid in k["ouvre"] and not k["retiree"] and not k.get("tenue") \
                    and all(self.blocages.get(o, {}).get("tombe") for o in k["ouvre"]):
                k["tenue"] = True
                self._liberer(kid, 0)

    def _menace_finie(self, mid):  # regle: parade-un-tour
        """Une destruction tombée ou réalisée n'a plus rien à parer : les blocages
        posés SUR elle (une bête entre la frappe et la colonne) tombent sans gel
        et rendent leurs pièces."""
        for bid, b in self.blocages.items():
            if b["sur"] == mid and not b["tombe"]:
                self._tomber(bid)

    def _protegee(self, mid):  # regle: parade-un-tour, blocage-suspendu-ne-prevaut-plus
        """Une parade tient si un blocage vivant est posé sur la menace — et
        pas suspendu : questionné sans maillon, il ne pare pas plus qu'il ne
        prévaut (A4 de l'audit du 7.9)."""
        return any(b["sur"] == mid and not b["tombe"] and not b.get("suspendue_par")
                   for b in self.blocages.values())

    def _liberer(self, par, gel):  # regle: engage-jusqu-a-chute, gels
        for r in self.ressources.values():
            if par in r["engagee_par"]:
                r["engagee_par"].remove(par)
                if gel:
                    r["gel_jusqu"] = max(r.get("gel_jusqu", 0), self.tour + gel)

    def _appliquer(self, l):
        """Applique une ligne au rejeu : ne lève JAMAIS. Une ligne fausse écrite
        à la main (un id inconnu, un champ absent) devient un avertissement, et
        la partie reste lisible (A10). `ecrire` passe par `_appliquer_brut`
        pour que la faute se voie AVANT d'écrire."""
        try:
            self._appliquer_brut(l)
        except Exception as e:  # noqa: BLE001 — c'est le point : tout, sauf planter
            self.avertissements.append("ligne %s (%s %s) inapplicable, ignorée : %s"
                                       % (l.get("n"), l.get("camp"), l.get("coup"), e))

    def _appliquer_brut(self, l):
        coup, camp = l.get("coup"), l.get("camp")
        self.tour = max(self.tour, int(l.get("tour") or self.tour))   # le rejeu garde le max : vieux fichiers
        if coup == "viser":  # regle: coup-viser
            arrive = int(l.get("arrive_tour") or 0)
            self.etats[l["id"]] = {"camp": camp, "texte": l.get("texte", ""), "signe": l.get("signe"),
                                   "sert": l.get("sert"), "vrai": None,
                                   "arrive_tour": arrive or None,
                                   "deck": arrive <= self.tour}
        elif coup == "sortir":  # regle: coup-sortir
            e = self.etats.get(l.get("id"))
            if e is None:
                raise KeyError("sortir : état %s inconnu" % l.get("id"))
            e["deck"] = False
            e["sorti"] = True
        elif coup == "demander":  # regle: coup-demander, ressource-demandee-puis-arbitree
            self.ressources[l["id"]] = {"camp": camp, "lieu": l.get("lieu"),
                                        "nombre": l.get("nombre"), "tenu_par": l.get("tenu_par"),
                                        "arrive_tour": self.tour, "gel_jusqu": 0,
                                        "engagee_par": [], "detruite": False,
                                        "en_attente": l.get("n"), "texte": l.get("texte", ""),
                                        # le genre dit par la ligne : il était lu par la
                                        # vue et jamais porté ici — un champ mort
                                        "genre": l.get("genre")}
        elif coup == "arbitrer":  # regle: coup-arbitrer
            for src in self._lignes_visees(l.get("sur")):
                if src.get("coup") == "demander":  # regle: verdict-sur-demande
                    r = self.ressources.get(src["id"])
                    if not r:
                        continue
                    if l.get("verdict") == "refuse":
                        del self.ressources[src["id"]]
                    else:
                        r["en_attente"] = None
                        for k in ("lieu", "nombre", "tenu_par", "genre"):
                            if l.get(k) is not None:
                                r[k] = l[k]
                        r["arrive_tour"] = int(l.get("arrive_tour") or self.tour)
                        r["source"] = l.get("motif")
                elif src.get("coup") in ("detruire", "retourner"):  # regle: verdict-sur-menace
                    m = self.menaces.get(src["id"])
                    if m:
                        if l.get("verdict") == "refuse":  # regle: portee-refusee-sur-piece
                            m["tombee"] = True
                            self._liberer(src["id"], 0)
                            self._menace_finie(src["id"])
                        elif l.get("verdict") == "accorde":
                            m["suspendue_par"] = None     # la portée est jugée bonne : la suspension tombe
                        elif l.get("verdict") == "reporte":
                            m["arrive_tour"] = int(l.get("arrive_tour") or self.tour + 1)
                        elif l.get("verdict") == "tranche":  # regle: heurt-tranche-a-la-table
                            self._realiser_menace(src["id"], l.get("nombre"))
                            for rid in liste(l.get("detruit")):   # heurt mutuel : la pièce qui frappait meurt aussi
                                r = self.ressources.get(rid)
                                if r:
                                    r["detruite"] = True
                                    for par in list(r["engagee_par"]):
                                        if par in self.cles:
                                            self.cles[par]["retiree"] = True
                                            self._liberer(par, 0)
                                        elif par in self.blocages:
                                            self._tomber(par)
                                    r["engagee_par"] = []
                elif src.get("coup") == "lever" and l.get("verdict") == "refuse":  # regle: verdict-sur-cle, portee-refusee-sur-piece
                    if src["id"] in self.cles:
                        self.cles[src["id"]]["retiree"] = True
                        self._liberer(src["id"], 0)
                elif src.get("coup") == "bloquer" and l.get("verdict") == "refuse":  # regle: verdict-sur-blocage, portee-refusee-sur-piece
                    if src["id"] in self.blocages:
                        self._tomber(src["id"])   # sans portée : il tombe
        elif coup == "bloquer":  # regle: coup-bloquer
            self.blocages[l["id"]] = {"camp": camp, "sur": l.get("sur"), "texte": l.get("texte", ""), "signe": l.get("signe"),
                                      "engage": liste(l.get("engage")), "tombe": False, "n": l.get("n"),
                                      "prete_tour": self._prete_tour(l.get("engage"))}
            self._engager(l.get("engage"), l["id"])
        elif coup == "lever":  # regle: coup-lever
            self.cles[l["id"]] = {"camp": camp, "ouvre": liste(l.get("ouvre")), "texte": l.get("texte", ""), "signe": l.get("signe"),
                                  "sert": l.get("sert"),
                                  "engage": liste(l.get("engage")), "suspendue_par": None,  # regle: cle-sans-maillon-affirmation
                                  "retiree": False, "n": l.get("n"),
                                  "prete_tour": self._prete_tour(l.get("engage"))}
            self._engager(l.get("engage"), l["id"])
        elif coup == "agir":  # regle: coup-agir
            m = self.maillons.get(l.get("id"))
            if m and l.get("etat") and not l.get("realise"):
                m["etat"] = l["etat"]
            else:
                self.maillons[l["id"]] = {"camp": camp, "realise": l.get("realise"), "qui": l.get("qui"), "signe": l.get("signe"),
                                          "avec": liste(l.get("avec")), "etat": l.get("etat", "faite"),   # `a_faire` : lignes d'avant le 6.9 seulement
                                          "texte": l.get("texte", ""), "n": l.get("n")}
            cible = l.get("realise") or (m or {}).get("realise")
            k = (self.cles.get(cible) or self.menaces.get(cible)
                 or self.blocages.get(cible))
            if k and k.get("suspendue_par"):  # regle: justifier-suspend
                k["suspendue_par"] = None      # la chaîne est écrite : la suspension tombe
        elif coup == "justifier":  # regle: coup-justifier
            sur = l.get("sur")
            # UN BLOCAGE SE JUSTIFIE AUSSI (mesure du duel de 50 tours, 3.9) :
            # sans lui, le defenseur affirmait gratuitement — « le roi est chez
            # les Hightower » tenait un etat sans que personne puisse exiger par
            # quelle poterne il etait sorti. Le blocage etait la piece la moins
            # chere du jeu, et c'est la plus forte.
            cible = (self.cles.get(sur) or self.menaces.get(sur)
                     or self.blocages.get(sur) or self.etats.get(sur))
            if cible is not None:
                cible["suspendue_par"] = l.get("n")  # regle: justifier-suspend, blocage-suspendu-ne-prevaut-plus
                cible["justifiee"] = l.get("n")      # une seule fois par pièce  # regle: justifier-une-fois
        elif coup == "rearmer":  # regle: coup-rearmer
            i = l.get("id")
            cible = self.cles.get(i) or self.blocages.get(i)
            if cible is None:
                raise KeyError("rearmer : %s n'est ni une clé ni un blocage" % i)
            for pc in liste(l.get("engage")):
                if pc not in cible["engage"]:
                    cible["engage"].append(pc)
            self._engager(l.get("engage"), i)
            cible["prete_tour"] = max(cible.get("prete_tour", 0), self._prete_tour(l.get("engage")))
        elif coup in ("detruire", "retourner"):  # regle: coup-detruire, coup-retourner
            # RETOURNER EST UNE DESTRUCTION QUI NE TUE PAS (mesure du duel de 50
            # tours, defaut 2 : Larys s'est vendu au tour 22 et restait « une
            # piece vert », inengageable ; il a fallu poser une piece neuve et
            # le meme homme figurait deux fois au grand livre). Meme fenetre,
            # meme reponse possible, meme arbitrage — seul l'effet differe : la
            # piece change de camp au lieu de sortir du jeu.
            self.menaces[l["id"]] = {"camp": camp, "cible": l.get("cible"), "texte": l.get("texte", ""), "signe": l.get("signe"),
                                     "genre": coup,
                                     "engage": liste(l.get("engage")),
                                     # posée au tour t, elle arrive au plus tôt en t+1 et atterrit
                                     # en entrant en t+2 : le camp visé a toujours son tour pour répondre
                                     "arrive_tour": max(int(l.get("arrive_tour") or self.tour + 1),  # regle: menace-datee
                                                        self._prete_tour(l.get("engage"))),
                                     "realisee": False, "tombee": False, "suspendue_par": None, "n": l.get("n")}
            self._engager(l.get("engage"), l["id"])
        elif coup == "retirer":  # regle: coup-retirer
            i = l["id"]
            gel = int(l.get("gel_tours", GEL_RETRAIT))
            if i in self.cles:
                self.cles[i]["retiree"] = True
                self._liberer(i, gel)
            elif i in self.blocages:
                self._tomber(i, gel)     # retiré par son camp : même prix qu'une clé
            elif i in self.menaces:  # regle: retirer-une-menace
                self.menaces[i]["tombee"] = True     # on rappelle sa frappe : la pièce revient, gelée
                self._liberer(i, gel)
                self._menace_finie(i)
            elif i in self.ressources:
                r = self.ressources[i]
                r["gel_jusqu"] = max(r.get("gel_jusqu", 0), self.tour + gel)
                for par in list(r["engagee_par"]):
                    if par in r["engagee_par"]:
                        r["engagee_par"].remove(par)
                    if par in self.blocages:
                        self._tomber(par)   # un blocage sans sa pièce ne bloque plus  # regle: blocage-tombe-avec-sa-piece
                    elif par in self.cles:  # regle: blocage-tombe-avec-sa-piece
                        # la clef garde son id mais perd la pièce : « sans
                        # ressource » jusqu'au réarmement — sans ça, le gel
                        # passé, elle redevenait valide sur une pièce que
                        # personne n'engageait plus (A1 de l'audit du 7.9)
                        k = self.cles[par]
                        k["engage"] = [x for x in k["engage"] if x != i]
                    elif par in self.menaces:  # regle: retirer-le-frappeur
                        # on retire la pièce qui frappe : la frappe tombe avec
                        # elle, sinon elle atterrissait sans personne (A2)
                        m = self.menaces[par]
                        if not m["realisee"] and not m["tombee"]:
                            m["tombee"] = True
                            self._liberer(par, 0)
                            self._menace_finie(par)
                for mid, m in self.menaces.items():
                    if m["cible"] == i and not m["realisee"] and not m["tombee"]:  # regle: retirer-une-menace
                        m["tombee"] = True
                        self._liberer(mid, 0)   # la pièce qui frappait est rendue
                        self._menace_finie(mid)
        elif coup == "reconstruire":  # regle: coup-reconstruire, reconstruire-ce-qui-se-reconstruit
            r = self.ressources.get(l.get("id"))
            if r is None:
                raise KeyError("reconstruire : pièce %s inconnue" % l.get("id"))
            r["detruite"] = False
            r["arrive_tour"] = int(l.get("revient_tour") or self.tour + TOURS_RECONSTRUCTION)
            r["engagee_par"] = []
        elif coup == "consigne":
            for p in liste(l.get("pieces")):
                self.consignes[p] = l.get("texte", "")
        elif coup == "constater":  # regle: coup-constater
            e = self.etats.get(l.get("etat"))
            if e:
                e["vrai"] = (l.get("verdict") == "vrai")
                e["constat"] = l.get("motif")
                e["suspendue_par"] = None   # le constat répond à la question, vrai ou faux  # regle: question-sur-etat-sans-reponse
                if e["vrai"]:  # regle: etat-vrai-libere
                    # l'état est acquis : ce qui le bloquait est passé, ce qui le
                    # servait a fait son office — les pièces reviennent sans gel
                    for bid, b in self.blocages.items():
                        if b["sur"] == l["etat"] and not b["tombe"] and b["camp"] != e["camp"]:
                            self._tomber(bid)
                    for kid, k in self.cles.items():
                        if k.get("sert") == l["etat"] and not k["retiree"] and not k.get("tenue"):
                            k["tenue"] = True
                            self._liberer(kid, 0)
        elif coup == "tour":  # regle: coup-tour
            partie_tour.appliquer(self, l)

    def _realiser_menace(self, mid, nombre):
        m = self.menaces[mid]
        if m["realisee"] or m["tombee"]:  # regle: atterrissage-total
            # Règle 12 : atterrie sans arbitrage, une destruction est TOTALE. Un
            # « tranche » d'après coup ne peut plus la rendre partielle — sans ce
            # garde-fou, la pièce sortait du grand livre au passage du tour, puis
            # se voyait retrancher un nombre : « 1100 · DÉTRUITE », les deux à la
            # fois. Après l'atterrissage, une correction est un coup de plus.
            return
        m["realisee"] = True
        m["realisee_tour"] = self.tour
        cible = self.ressources.get(m["cible"])
        if cible and m.get("genre") == "retourner":  # regle: retournement-realise
            # Il passe a l'autre camp, entier : ce qu'il tenait pour les siens
            # tombe, et il redevient libre pour qui l'a retourne.
            for par in list(cible["engagee_par"]):
                if par in self.cles:
                    self.cles[par]["retiree"] = True
                    self._liberer(par, 0)
                elif par in self.blocages:
                    self._tomber(par)
            cible["engagee_par"] = []
            cible["camp"] = m["camp"]
            cible["retourne_par"] = m["n"]   # puis le sort d'une frappe : pièce rendue, gelée un tour
        elif cible:  # regle: destruction-realisee
            if nombre is not None and cible.get("nombre"):
                cible["nombre"] = max(0, int(cible["nombre"]) - int(nombre))
                if cible["nombre"] > 0:
                    m["partielle"] = nombre
            if not m.get("partielle"):
                cible["detruite"] = True
                for par in list(cible["engagee_par"]):
                    # ce qui reposait sur la pièce tombe
                    if par in self.cles:
                        self.cles[par]["retiree"] = True
                        self._liberer(par, 0)
                    elif par in self.blocages:  # regle: blocage-tombe-avec-sa-piece
                        self._tomber(par)
                cible["engagee_par"] = []
        for p in m["engage"]:
            r = self.ressources.get(p)
            if r:
                if mid in r["engagee_par"]:
                    r["engagee_par"].remove(mid)
                r["gel_jusqu"] = max(r.get("gel_jusqu", 0), self.tour + GEL_FRAPPE)  # regle: gels
        self._menace_finie(mid)

    # ---- écrire ----------------------------------------------------------
    def ecrire(self, l):
        """Vérifie, applique, puis écrit — sous verrou, le `n` relu sur disque
        (partie_ecriture.py). Rend la liste des refus ; vide = c'est au livre."""
        return partie_ecriture.ecrire(self, l)

    # ---- lectures --------------------------------------------------------
    def prevaut(self, bid):  # regle: preseance-blocage, etats-blocage, etats-cle
        """Qui prévaut sur un blocage : le camp d'une clé valide qui l'ouvre, sinon le camp du blocage."""
        b = self.blocages[bid]
        contre = self.camp_de(b["sur"]) or b["camp"]    # le camp que ce blocage contrarie
        if b["tombe"]:
            return contre, "tombé"
        if b.get("suspendue_par"):  # regle: blocage-suspendu-ne-prevaut-plus
            # Symetrique de la cle suspendue : tant que le defenseur n'a pas
            # ecrit son maillon, son blocage ne tient pas la position.
            return contre, "blocage suspendu par ❓ %s" % b["suspendue_par"]
        if b.get("prete_tour", 0) > self.tour:  # regle: piece-en-route-s-engage
            return contre, "blocage prêt au tour %d" % b["prete_tour"]
        for kid, k in self.cles.items():
            if bid in k["ouvre"] and not k["retiree"] and not k.get("tenue"):
                if k["suspendue_par"]:
                    return b["camp"], "clé %s suspendue par ❓ %s" % (kid, k["suspendue_par"])
                if k.get("prete_tour", 0) > self.tour:
                    return b["camp"], "clé %s prête au tour %d" % (kid, k["prete_tour"])
                manque = self._pieces_libres(k["camp"], k["engage"], kid)  # vide = sans ressource  # regle: blocage-tombe-avec-sa-piece
                if manque:
                    return b["camp"], "clé %s sans ressource : %s" % (kid, manque[0])
                return k["camp"], "levé par 🗝️ %s" % kid
        # « rien en face » disait le motif — faux dès que le verrou est posé sur
        # une clef : en face, il y a la clef et ses pièces. Ce que le motif veut
        # dire, c'est qu'aucune clef ne LÈVE ce verrou ; on le dit.
        return b["camp"], "aucune clef ne le lève"  # regle: defenseur-tient

    def racine(self, camp=None):  # regle: trone-derniere-racine
        """La racine d'un camp : son état qui ne sert aucun autre — le trône vu de
        son côté (§2). Sans camp, celle du premier camp entré."""
        camp = camp or (self.camps() or [None])[0]
        r = [eid for eid, e in self.etats.items() if not e.get("sert") and e["camp"] == camp]
        return r[0] if r else None

    def tenu_par(self):  # regle: trone-derniere-racine
        """Le trône est au camp dont la racine a été constatée vraie en dernier ;
        un constat faux sur cette racine le lui retire. À personne (None) tant que
        rien n'est constaté — c'est à l'arbitre de constater qui est assis."""
        racines = set(self.racine(c) for c in self.camps())
        tenant = None
        for x in self.lignes:
            if x.get("coup") == "constater" and x.get("etat") in racines:
                camp = self.etats[x["etat"]]["camp"]
                if x.get("verdict") == "vrai":
                    tenant = camp
                elif tenant == camp:
                    tenant = None
        return tenant
