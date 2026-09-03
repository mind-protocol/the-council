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

import partie_validite  # la recevabilité d'un coup, séparée pour rester lisible

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSSIER = os.path.join(RACINE, "etat", "parties")
JOURS_PAR_TOUR = 2  # un tour = deux jours du monde (mj-partie.md §4)
DECK_MAX = 10
GEL_RETRAIT = 2
GEL_FRAPPE = 1
TOURS_RECONSTRUCTION = 2
CAMPS = ("noir", "vert", "arbitre")
COUPS = ("viser", "sortir", "demander", "arbitrer", "bloquer", "lever", "agir",
         "justifier", "detruire", "retourner", "retirer", "reconstruire",
         "rearmer", "passer", "consigne", "constater", "tour")
# Ceux qui comptent pour « un coup par camp et par tour » : ni l'arbitre, ni ce
# qui ne coûte rien (viser à l'ouverture, demander, justifier, consigne).
COUPS_COMPTES = ("sortir", "bloquer", "lever", "agir", "detruire", "retourner",
                 "retirer", "reconstruire", "rearmer", "passer")
EMOJI_CAMP = {"noir": "⚫", "vert": "🟢", "arbitre": "🟠"}
EMOJI_COUP = {"viser": "🎯", "sortir": "🃏", "demander": "📦", "arbitrer": "⚖️",
              "bloquer": "🔒", "lever": "🗝️", "agir": "⚔️", "justifier": "❓",
              "detruire": "💥", "retourner": "🔄", "retirer": "🗑️",
              "reconstruire": "🔧", "rearmer": "➕",
              "passer": "⏸️", "consigne": "📋", "constater": "✅", "tour": "⏭️"}


def adverse(camp):
    return "vert" if camp == "noir" else "noir"


def liste(x):
    if x is None:
        return []
    return list(x) if isinstance(x, (list, tuple)) else [x]


def au_deck(e, tour, reserve=False):
    """Un état est au deck s'il y est entré ; un état daté (deck vert = calendrier,
    mj-partie.md §2) n'y est qu'à partir de son tour. `reserve` compte aussi la
    place qu'il tient d'avance."""
    if e.get("sorti"):
        return False
    if int(e.get("arrive_tour") or 0) > tour:
        return bool(reserve)
    return True


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
        if os.path.exists(chemin):
            with io.open(chemin, "r", encoding="utf-8") as f:
                for brut in f:
                    brut = brut.strip()
                    if not brut:
                        continue
                    ligne = json.loads(brut)
                    self.lignes.append(ligne)
                    self._appliquer(ligne)

    # ---- validité --------------------------------------------------------
    def verifier(self, l):
        """Rend la liste des refus (partie_validite.py). Vide = le coup est recevable."""
        return partie_validite.verifier(self, l)

    def _pieces_libres(self, camp, pieces, par):
        return partie_validite.pieces_libres(self, camp, pieces, par)

    def _lignes_visees(self, sur):
        """Un arbitrage vise une ligne par son numéro, ou la dernière ligne qui porte cet id."""
        out = []
        for s in liste(sur):
            # l'id d'abord (un id de pièce est souvent tout en chiffres), le numéro de ligne sinon
            trouve = [x for x in self.lignes if str(x.get("id")) == str(s)
                      and x.get("coup") in ("demander", "detruire", "lever", "bloquer")]
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

    def _prete_tour(self, pieces):
        """Le tour où toutes ces pièces sont arrivées : une pièce en route s'engage
        dès maintenant (réservée, visible de l'adversaire), mais la clé ne vaut
        qu'à ce tour-là — mj-partie.md §4."""
        t = self.tour
        for p in liste(pieces):
            r = self.ressources.get(p)
            if r is not None:
                t = max(t, int(r.get("arrive_tour") or 0))
        return t

    def _tomber(self, bid, gel=0):
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

    def _menace_finie(self, mid):
        """Une destruction tombée ou réalisée n'a plus rien à parer : les blocages
        posés SUR elle (une bête entre la frappe et la colonne) tombent sans gel
        et rendent leurs pièces."""
        for bid, b in self.blocages.items():
            if b["sur"] == mid and not b["tombe"]:
                self._tomber(bid)

    def _protegee(self, mid):
        return any(b["sur"] == mid and not b["tombe"] for b in self.blocages.values())

    def _liberer(self, par, gel):
        for r in self.ressources.values():
            if par in r["engagee_par"]:
                r["engagee_par"].remove(par)
                if gel:
                    r["gel_jusqu"] = max(r.get("gel_jusqu", 0), self.tour + gel)

    def _appliquer(self, l):
        coup, camp = l.get("coup"), l.get("camp")
        self.tour = max(self.tour, int(l.get("tour") or self.tour))
        if coup == "viser":
            arrive = int(l.get("arrive_tour") or 0)
            self.etats[l["id"]] = {"camp": camp, "texte": l.get("texte", ""),
                                   "sert": l.get("sert"), "vrai": None,
                                   "arrive_tour": arrive or None,
                                   "deck": arrive <= self.tour}
        elif coup == "sortir":
            self.etats[l["id"]]["deck"] = False
            self.etats[l["id"]]["sorti"] = True
        elif coup == "demander":
            self.ressources[l["id"]] = {"camp": camp, "lieu": l.get("lieu"),
                                        "nombre": l.get("nombre"), "tenu_par": l.get("tenu_par"),
                                        "arrive_tour": self.tour, "gel_jusqu": 0,
                                        "engagee_par": [], "detruite": False,
                                        "en_attente": l.get("n"), "texte": l.get("texte", "")}
        elif coup == "arbitrer":
            for src in self._lignes_visees(l.get("sur")):
                if src.get("coup") == "demander":
                    r = self.ressources.get(src["id"])
                    if not r:
                        continue
                    if l.get("verdict") == "refuse":
                        del self.ressources[src["id"]]
                    else:
                        r["en_attente"] = None
                        for k in ("lieu", "nombre", "tenu_par"):
                            if l.get(k) is not None:
                                r[k] = l[k]
                        r["arrive_tour"] = int(l.get("arrive_tour") or self.tour)
                        r["source"] = l.get("motif")
                elif src.get("coup") == "detruire":
                    m = self.menaces.get(src["id"])
                    if m:
                        if l.get("verdict") == "refuse":
                            m["tombee"] = True
                            self._liberer(src["id"], 0)
                            self._menace_finie(src["id"])
                        elif l.get("verdict") == "accorde":
                            m["suspendue_par"] = None     # la portée est jugée bonne : la suspension tombe
                        elif l.get("verdict") == "reporte":
                            m["arrive_tour"] = int(l.get("arrive_tour") or self.tour + 1)
                        elif l.get("verdict") == "tranche":
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
                elif src.get("coup") == "lever" and l.get("verdict") == "refuse":
                    if src["id"] in self.cles:
                        self.cles[src["id"]]["retiree"] = True
                        self._liberer(src["id"], 0)
                elif src.get("coup") == "bloquer" and l.get("verdict") == "refuse":
                    if src["id"] in self.blocages:
                        self._tomber(src["id"])   # sans portée : il tombe
        elif coup == "bloquer":
            self.blocages[l["id"]] = {"camp": camp, "sur": l.get("sur"), "texte": l.get("texte", ""),
                                      "engage": liste(l.get("engage")), "tombe": False, "n": l.get("n"),
                                      "prete_tour": self._prete_tour(l.get("engage"))}
            self._engager(l.get("engage"), l["id"])
        elif coup == "lever":
            self.cles[l["id"]] = {"camp": camp, "ouvre": liste(l.get("ouvre")), "texte": l.get("texte", ""),
                                  "sert": l.get("sert"),
                                  "engage": liste(l.get("engage")), "suspendue_par": None,
                                  "retiree": False, "n": l.get("n"),
                                  "prete_tour": self._prete_tour(l.get("engage"))}
            self._engager(l.get("engage"), l["id"])
        elif coup == "agir":
            m = self.maillons.get(l.get("id"))
            if m and l.get("etat") and not l.get("realise"):
                m["etat"] = l["etat"]
            else:
                self.maillons[l["id"]] = {"camp": camp, "realise": l.get("realise"), "qui": l.get("qui"),
                                          "avec": liste(l.get("avec")), "etat": l.get("etat", "a_faire"),
                                          "texte": l.get("texte", ""), "n": l.get("n")}
            cible = l.get("realise") or (m or {}).get("realise")
            k = (self.cles.get(cible) or self.menaces.get(cible)
                 or self.blocages.get(cible))
            if k and k.get("suspendue_par"):
                k["suspendue_par"] = None      # la chaîne est écrite : la suspension tombe
        elif coup == "justifier":
            sur = l.get("sur")
            # UN BLOCAGE SE JUSTIFIE AUSSI (mesure du duel de 50 tours, 3.9) :
            # sans lui, le defenseur affirmait gratuitement — « le roi est chez
            # les Hightower » tenait un etat sans que personne puisse exiger par
            # quelle poterne il etait sorti. Le blocage etait la piece la moins
            # chere du jeu, et c'est la plus forte.
            cible = (self.cles.get(sur) or self.menaces.get(sur)
                     or self.blocages.get(sur) or self.etats.get(sur))
            if cible is not None:
                cible["suspendue_par"] = l.get("n")
                cible["justifiee"] = l.get("n")      # une seule fois par pièce
        elif coup == "rearmer":
            i = l["id"]
            cible = self.cles.get(i) or self.blocages.get(i)
            for pc in liste(l.get("engage")):
                if pc not in cible["engage"]:
                    cible["engage"].append(pc)
            self._engager(l.get("engage"), i)
            cible["prete_tour"] = max(cible.get("prete_tour", 0), self._prete_tour(l.get("engage")))
        elif coup in ("detruire", "retourner"):
            # RETOURNER EST UNE DESTRUCTION QUI NE TUE PAS (mesure du duel de 50
            # tours, defaut 2 : Larys s'est vendu au tour 22 et restait « une
            # piece vert », inengageable ; il a fallu poser une piece neuve et
            # le meme homme figurait deux fois au grand livre). Meme fenetre,
            # meme reponse possible, meme arbitrage — seul l'effet differe : la
            # piece change de camp au lieu de sortir du jeu.
            self.menaces[l["id"]] = {"camp": camp, "cible": l.get("cible"), "texte": l.get("texte", ""),
                                     "genre": coup,
                                     "engage": liste(l.get("engage")),
                                     # posée au tour t, elle arrive au plus tôt en t+1 et atterrit
                                     # en entrant en t+2 : le camp visé a toujours son tour pour répondre
                                     "arrive_tour": max(int(l.get("arrive_tour") or self.tour + 1),
                                                        self._prete_tour(l.get("engage"))),
                                     "realisee": False, "tombee": False, "suspendue_par": None, "n": l.get("n")}
            self._engager(l.get("engage"), l["id"])
        elif coup == "retirer":
            i = l["id"]
            gel = int(l.get("gel_tours", GEL_RETRAIT))
            if i in self.cles:
                self.cles[i]["retiree"] = True
                self._liberer(i, gel)
            elif i in self.blocages:
                self._tomber(i, gel)     # retiré par son camp : même prix qu'une clé
            elif i in self.menaces:
                self.menaces[i]["tombee"] = True     # on rappelle sa frappe : la pièce revient, gelée
                self._liberer(i, gel)
                self._menace_finie(i)
            elif i in self.ressources:
                r = self.ressources[i]
                r["gel_jusqu"] = max(r.get("gel_jusqu", 0), self.tour + gel)
                for par in list(r["engagee_par"]):
                    r["engagee_par"].remove(par)
                    if par in self.blocages:
                        self._tomber(par)   # un blocage sans sa pièce ne bloque plus
                for mid, m in self.menaces.items():
                    if m["cible"] == i and not m["realisee"] and not m["tombee"]:
                        m["tombee"] = True
                        self._liberer(mid, 0)   # la pièce qui frappait est rendue
                        self._menace_finie(mid)
        elif coup == "reconstruire":
            r = self.ressources[l["id"]]
            r["detruite"] = False
            r["arrive_tour"] = int(l.get("revient_tour") or self.tour + TOURS_RECONSTRUCTION)
            r["engagee_par"] = []
        elif coup == "consigne":
            for p in liste(l.get("pieces")):
                self.consignes[p] = l.get("texte", "")
        elif coup == "constater":
            e = self.etats.get(l.get("etat"))
            if e:
                e["vrai"] = (l.get("verdict") == "vrai")
                e["constat"] = l.get("motif")
                if e["vrai"]:
                    # l'état est acquis : ce qui le bloquait est passé, ce qui le
                    # servait a fait son office — les pièces reviennent sans gel
                    for bid, b in self.blocages.items():
                        if b["sur"] == l["etat"] and not b["tombe"] and b["camp"] != e["camp"]:
                            self._tomber(bid)
                    for kid, k in self.cles.items():
                        if k.get("sert") == l["etat"] and not k["retiree"] and not k.get("tenue"):
                            k["tenue"] = True
                            self._liberer(kid, 0)
        elif coup == "tour":
            self.tour = int(l.get("tour") or self.tour + 1)
            for e in self.etats.values():
                if e.get("arrive_tour") and not e.get("sorti") and int(e["arrive_tour"]) <= self.tour:
                    e["deck"] = True       # l'état daté entre au deck à son tour
            for mid, m in self.menaces.items():
                protegee = self._protegee(mid)
                # Une destruction atterrit au passage du tour SUIVANT son tour
                # d'arrivée : le camp visé a toujours un tour pour bloquer,
                # justifier ou retirer (mj-partie.md §4, « une menace datée »).
                if not m["realisee"] and not m["tombee"] and m["arrive_tour"] < self.tour \
                        and not m.get("suspendue_par") and not protegee:
                    self._realiser_menace(mid, None)

    def _realiser_menace(self, mid, nombre):
        m = self.menaces[mid]
        if m["realisee"] or m["tombee"]:
            # Règle 12 : atterrie sans arbitrage, une destruction est TOTALE. Un
            # « tranche » d'après coup ne peut plus la rendre partielle — sans ce
            # garde-fou, la pièce sortait du grand livre au passage du tour, puis
            # se voyait retrancher un nombre : « 1100 · DÉTRUITE », les deux à la
            # fois. Après l'atterrissage, une correction est un coup de plus.
            return
        m["realisee"] = True
        m["realisee_tour"] = self.tour
        cible = self.ressources.get(m["cible"])
        if cible and m.get("genre") == "retourner":
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
            cible["retourne_par"] = m["n"]
            return
        if cible:
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
                    elif par in self.blocages:
                        self._tomber(par)
                cible["engagee_par"] = []
        for p in m["engage"]:
            r = self.ressources.get(p)
            if r:
                if mid in r["engagee_par"]:
                    r["engagee_par"].remove(mid)
                r["gel_jusqu"] = max(r.get("gel_jusqu", 0), self.tour + GEL_FRAPPE)
        self._menace_finie(mid)

    # ---- écrire ----------------------------------------------------------
    def ecrire(self, l):
        refus = self.verifier(l)
        if refus:
            return refus
        l = dict(l)
        l["n"] = (self.lignes[-1]["n"] + 1) if self.lignes else 1
        l.setdefault("tour", self.tour if l["coup"] != "tour" else self.tour + 1)
        if l["coup"] == "tour":
            l["tour"] = self.tour + 1
            l["arrivees"] = [rid for rid, r in self.ressources.items()
                             if r.get("arrive_tour") == l["tour"] and not r.get("en_attente")]
            l["degeles"] = [rid for rid, r in self.ressources.items() if r.get("gel_jusqu") == l["tour"]]
            l["menaces"] = [mid for mid, m in self.menaces.items()
                            if not m["realisee"] and not m["tombee"] and m["arrive_tour"] < l["tour"]
                            and not m.get("suspendue_par") and not self._protegee(mid)]
            l["parees"] = [mid for mid, m in self.menaces.items()
                           if not m["realisee"] and not m["tombee"] and m["arrive_tour"] < l["tour"]
                           and (m.get("suspendue_par") or self._protegee(mid))]
            l["etats_arrives"] = [eid for eid, e in self.etats.items()
                                  if e.get("arrive_tour") == l["tour"] and not e.get("sorti")]
            frappees = set(self.menaces[m]["cible"] for m in l["menaces"])
            l["branches_mortes"] = [rid for rid, r in self.ressources.items()
                                    if not r["engagee_par"] and not r.get("detruite")
                                    and not r.get("en_attente") and rid not in frappees
                                    and r.get("arrive_tour", 0) + 2 <= l["tour"]
                                    and rid not in self._jamais_engagees_tolerees()]
            l["jours"] = JOURS_PAR_TOUR
        if os.path.dirname(self.chemin):
            os.makedirs(os.path.dirname(self.chemin), exist_ok=True)
        with io.open(self.chemin, "a", encoding="utf-8") as f:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
        self.lignes.append(l)
        self._appliquer(l)
        return []

    def _jamais_engagees_tolerees(self):
        # Une pièce déjà engagée une fois dans la partie n'est pas une branche
        # morte. `qui` compte autant que `avec` : le guetteur et le septon
        # d'essai-1 n'ont jamais figuré que là, et se voyaient signalés morts
        # le tour même où ils réalisaient un maillon.
        vues = set()
        for x in self.lignes:
            for p in (liste(x.get("engage")) + liste(x.get("avec"))
                      + liste(x.get("pieces")) + liste(x.get("qui"))):
                vues.add(p)
        return vues

    # ---- lectures --------------------------------------------------------
    def prevaut(self, bid):
        """Qui prévaut sur un blocage : le camp d'une clé valide qui l'ouvre, sinon le camp du blocage."""
        b = self.blocages[bid]
        if b["tombe"]:
            return adverse(b["camp"]), "tombé"
        if b.get("suspendue_par"):
            # Symetrique de la cle suspendue : tant que le defenseur n'a pas
            # ecrit son maillon, son blocage ne tient pas la position.
            return adverse(b["camp"]), "blocage suspendu par ❓ %s" % b["suspendue_par"]
        if b.get("prete_tour", 0) > self.tour:
            return adverse(b["camp"]), "blocage prêt au tour %d" % b["prete_tour"]
        for kid, k in self.cles.items():
            if bid in k["ouvre"] and not k["retiree"] and not k.get("tenue"):
                if k["suspendue_par"]:
                    return b["camp"], "clé %s suspendue par ❓ %s" % (kid, k["suspendue_par"])
                if k.get("prete_tour", 0) > self.tour:
                    return b["camp"], "clé %s prête au tour %d" % (kid, k["prete_tour"])
                manque = self._pieces_libres(k["camp"], k["engage"], kid)
                if manque:
                    return b["camp"], "clé %s sans ressource : %s" % (kid, manque[0])
                return k["camp"], "levé par 🗝️ %s" % kid
        return b["camp"], "rien en face"

    def racine(self):
        r = [eid for eid, e in self.etats.items() if not e.get("sert") and e["camp"] == "noir"]
        return r[0] if r else (list(self.etats)[0] if self.etats else None)

    def tenu_par(self):
        """Le trône est à qui l'arbitre a constaté en dernier, sur la racine seule ; au Vert sinon."""
        racine = self.racine()
        for x in reversed(self.lignes):
            if x.get("coup") == "constater" and x.get("etat") == racine:
                camp = self.etats[racine]["camp"]
                return camp if x.get("verdict") == "vrai" else adverse(camp)
        return "vert"
