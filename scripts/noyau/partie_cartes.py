# -*- coding: utf-8 -*-
"""
partie_cartes.py — la vue JOUEUR d'une partie, en cartes (docs/partie.md, v0).

Ce que l'écran « Le conseil » montre, et rien d'autre : des FRONTS (un par
blocage adverse posé contre nous), des PILES sous chaque front (nos ordres,
les questions qui les suspendent, les gestes faits, les pièces engagées), le
DECK (nos pièces : en main, en route, se remet, posées, détruites) et nos
DESSEINS. Tout est une carte, et chaque carte porte son type, son apparence
et son pied. Aucun id nu ne doit atteindre l'écran : `titre` est toujours
rempli.

PAS DE BROUILLARD ICI, et c'est une décision du 3e jour de la 9e lune. Le
brouillard reste entier dans la CHRONIQUE — ce que le joueur apprend d'un
capitaine essoufflé, d'une rumeur fausse, d'un chiffre arrondi en sa faveur.
Mais le plateau n'est pas dans la fiction : c'est l'abstraction que le MJ et le
joueur partagent pour jouer la partie, et aux échecs on voit les pièces d'en
face. La v0 servait l'ennemi seulement par ce qu'il avait posé contre nous ;
l'adversaire jouait alors des coups que personne ne voyait jamais et le plateau
ne bougeait pas — ce n'est pas de la tension, c'est un solitaire contre un
processus caché. La position complète est donc servie, des deux camps.

CE QUI A CHANGÉ se dit exactement, sans deviner : le jsonl est append-only,
donc chaque coup porte un numéro qui ne recule pas. `vu` est le dernier numéro
que ce joueur a vu ; tout objet touché par une ligne postérieure porte
`neuf: true`. C'est la liste précise, pas une approximation, et elle survit à un
rechargement comme à deux jours d'absence.

Lecture seule : rien ici ne change la position ni n'écrit dans etat/.
"""
import io
import json
import os

from partie_greffe import RACINE, JOURS_PAR_TOUR, adverse, liste

TYPES = {"cible": "🎯", "verrou": "🔒", "clef": "🗝️", "action": "⚔️",
         "piece": "📦", "question": "❓", "frappe": "💥"}

_NOMS = None


def _noms():
    """id → nom en clair, lu une fois dans etat/personnages.json, lieux.json, dragons.json."""
    global _NOMS
    if _NOMS is None:
        _NOMS = {}
        for fichier in ("personnages.json", "lieux.json", "dragons.json"):
            try:
                with io.open(os.path.join(RACINE, "etat", fichier), encoding="utf-8") as f:
                    d = json.load(f)
            except Exception:
                continue
            d = d if isinstance(d, list) else next((v for v in d.values() if isinstance(v, list)), [])
            for x in d:
                if isinstance(x, dict) and x.get("id") and x.get("nom"):
                    _NOMS.setdefault(str(x["id"]), x["nom"])
    return _NOMS


def nom(pid):
    """Un nom en clair ; à défaut l'id rendu lisible, majuscule en tête — jamais un id nu."""
    if not pid:
        return ""
    n = _noms().get(str(pid))
    if n:
        return n
    s = str(pid).replace("-", " ").replace("_", " ").strip()
    return s[:1].upper() + s[1:]


def titre(p, rid):
    """Le texte de la ligne, sinon l'id rendu lisible — jamais un id nu."""
    rid = str(rid)
    for reg in (p.ressources, p.etats, p.blocages, p.cles, p.maillons, p.menaces):
        x = reg.get(rid)
        if x and x.get("texte"):
            return x["texte"].strip().rstrip(".")
    return nom(rid)


_DRAGONS = ("caraxes", "syrax", "meleys", "vermax", "vhagar", "sunfyre", "tessarion",
            "dreamfyre", "seasmoke", "moondancer", "arrax", "tyraxes", "vermithor",
            "silverwing", "sheepstealer", "cannibal", "grey-ghost")


def genre_piece(r, rid):
    """Le sous-emoji d'une pièce : dit par la ligne (`genre`) ou deviné du nom."""
    g = r.get("genre")
    if g in ("dragon", "nef", "troupe", "or", "homme", "lieu"):
        return {"dragon": "🐉", "nef": "⛵", "troupe": "⚔️", "or": "💰", "homme": "👤", "lieu": "🏰"}[g]
    s = (rid + " " + (r.get("texte") or "")).lower()
    if any(d in s for d in _DRAGONS):
        return "🐉"
    if any(k in s for k in ("coque", "galer", "nef", "barque", "flotte")):
        return "⛵"
    if any(k in s for k in ("ost", "lance", "garnison", "guet", "compagnie", "hommes", "arch")):
        return "⚔️"
    if any(k in s for k in ("cassette", "bourse", "dragons d'or", "deniers", "hask")):
        return "💰"
    if r.get("tenu_par") and str(r["tenu_par"]) == rid:
        return "👤"
    return "📦"


def touches(p):
    """id → numéro de la DERNIÈRE ligne qui l'a touché, à quelque titre que ce
    soit : posé, arbitré, engagé, visé, levé. Sert à dire ce qui est neuf sans
    rien stocker de plus que le jsonl, qui est déjà l'histoire complète."""
    out = {}
    for l in p.lignes:
        n = int(l.get("n") or 0)
        vises = [l.get("id"), l.get("sur"), l.get("cible"), l.get("etat"), l.get("realise")]
        vises += liste(l.get("ouvre")) + liste(l.get("engage")) + liste(l.get("avec")) + liste(l.get("pieces"))
        for x in vises:
            if x:
                out[str(x)] = max(out.get(str(x), 0), n)
    return out


# ---------------------------------------------------------------- les pièces
def carte_piece(p, rid):
    r = p.ressources[rid]
    app, droite = "libre", "libre"
    if r.get("detruite"):
        app, droite = "detruite", "détruite"
    elif r.get("en_attente"):
        app, droite = "route", "attend l'arbitre"
    elif int(r.get("arrive_tour") or 0) > p.tour:
        n = (int(r["arrive_tour"]) - p.tour) * JOURS_PAR_TOUR
        app, droite = "route", "dans %d j" % n
    elif int(r.get("gel_jusqu") or 0) > p.tour:
        n = (int(r["gel_jusqu"]) - p.tour) * JOURS_PAR_TOUR
        app, droite = "remet", "se remet · %d j" % n
    elif r["engagee_par"]:
        app, droite = "posee", "posée"
    nb = (" · %s" % r["nombre"]) if r.get("nombre") else ""
    t = titre(p, rid) if r.get("texte") else nom(rid)
    visee = [m for m in p.menaces.values() if m["cible"] == rid and not m["realisee"] and not m["tombee"]]
    # RIEN QUI SE RÉPÈTE AILLEURS. Le lieu a sauté (tout est à Peyredragon, il
    # s'imprimait sur chaque carte), et « tenue par » aussi quand le titre le
    # dit déjà : « Caraxes, monté par Daemon · tenue par Daemon Targaryen ».
    porteur = nom(r["tenu_par"]) if r.get("tenu_par") and str(r["tenu_par"]) != rid else ""
    if porteur:
        # On compare le NOM SEUL, avant la virgule des titres (« Corlys
        # Velaryon, le Serpent de Mer ») : autrement « le Serpent de Mer » fait
        # doublon avec « les coques du Serpent de Mer » et l'on perdrait Corlys.
        for mot in porteur.split(",")[0].split():
            if len(mot) >= 4 and mot.lower() in t.lower():
                porteur = ""
                break
    # LE GENRE EST LE SIGNE DE LA CARTE, plus un préfixe du titre. Depuis que le
    # texte ne s'ouvre qu'au survol, un 📦 générique rendait les quinze pièces
    # indiscernables : c'est le dragon, la nef ou la bourse qu'on doit
    # reconnaître sans lire.
    return {"id": rid, "type": "piece", "emoji": genre_piece(r, rid), "camp": r["camp"],
            "titre": "%s%s" % (t, nb),
            "corps": "",
            "pied": {"gauche": porteur, "droite": droite},
            "apparence": app, "visee": bool(visee),
            "source": r.get("source") or "",
            "engagee_par": list(r["engagee_par"])}


# ---------------------------------------------------------------- les piles
def _ruban(p, k, kid):
    if k["suspendue_par"]:
        return "❓ suspendu"
    if k.get("tenue"):
        return "✅ tenu, blocage tombé"
    if int(k.get("prete_tour") or 0) > p.tour:
        return "⏳ prêt dans %d j" % ((int(k["prete_tour"]) - p.tour) * JOURS_PAR_TOUR)
    manque = p._pieces_libres(k["camp"], k["engage"], kid) if k["engage"] else []
    return "⚠️ sans ressource" if manque else "✅ tient"


def _questions_sur(p, cible_id):
    """Les lignes `justifier` encore ouvertes sur une pièce : une carte ❓ chacune."""
    out = []
    for l in p.lignes:
        if l.get("coup") != "justifier" or str(l.get("sur")) != str(cible_id):
            continue
        cible = p.cles.get(cible_id) or p.menaces.get(cible_id) or p.etats.get(cible_id)
        if cible is not None and cible.get("suspendue_par") == l.get("n"):
            out.append({"id": "q%s" % l.get("n"), "type": "question", "emoji": TYPES["question"],
                        "camp": l.get("camp"), "titre": l.get("texte", ""),
                        "corps": "",
                        "pied": {"gauche": nom(l.get("par")) if l.get("par") else "", "droite": ""},
                        "apparence": "question", "n": l.get("n")})
    return out


def _sans_la_cible(titre_ordre, titre_cible):
    """« Caraxes contre « Garde la rade » » posé SOUS « Garde la rade » lit deux
    fois la même chose. On coupe la queue à l'affichage : les ordres écrits
    avant ce nettoyage la portent dans le jsonl, et un jsonl ne se réécrit
    pas."""
    queue = " contre « %s »" % titre_cible
    if titre_ordre.endswith(queue):
        return titre_ordre[:-len(queue)].strip() or titre_ordre
    return titre_ordre


def _pile_clef(p, kid, camp, titre_cible=""):
    k = p.cles[kid]
    carte = {"id": kid, "type": "clef", "emoji": TYPES["clef"], "camp": camp,
             "titre": _sans_la_cible(titre(p, kid), titre_cible), "corps": "",
             "pied": {"gauche": "", "droite": _ruban(p, k, kid)},
             "apparence": "clef", "sous": []}
    carte["sous"] += _questions_sur(p, kid)
    for mid, m in sorted(p.maillons.items(), key=lambda kv: kv[1].get("n") or 0):
        if m["realise"] == kid:
            carte["sous"].append({"id": mid, "type": "action", "emoji": TYPES["action"], "camp": m["camp"],
                                  "titre": titre(p, mid), "corps": "",
                                  "pied": {"gauche": nom(m.get("qui")), "droite": m.get("etat", "")},
                                  "apparence": "action"})
    # Les pièces engagées NE SONT PLUS des cartes filles : elles répétaient mot
    # pour mot ce que le pied de l'ordre et la rangée « Posées » disaient déjà,
    # sur trois niveaux d'indentation. Elles se nomment au pied, et une seule
    # fois.
    # ... et seulement CE QUE LE TITRE NE DIT PAS. Un ordre laissé sans nom
    # porte déjà le nom de sa pièce : le répéter au pied fait deux fois la même
    # ligne, l'une sous l'autre.
    # LA PIÈCE ENGAGÉE REVIENT EN CARTE, et c'est un retour en arrière assumé.
    # Je les avais transformées en une ligne de pied pour tuer un doublon avec
    # la rangée « Posées » ; ce doublon n'en était pas un. Voir la carte POSÉE
    # SUR le front est tout le propos du plateau — on met des cartes sur des
    # cartes, et l'engagement se lit à l'endroit où il a lieu. Ce qui restait à
    # corriger, c'était la répétition du TITRE, pas la carte.
    for pc in k["engage"]:
        if pc in p.ressources:
            carte["sous"].append(carte_piece(p, pc))
    return carte


def _chaine(p, eid, vus=None):
    """De ce qu'un front barre jusqu'au trône : « la porte › la capitale › le
    trône ». C'est la SEULE chose que la colonne des états cibles disait d'utile —
    elle la disait loin de la décision, en arbre figé qui ne bougeait jamais.
    Ici elle est sur le front, à l'endroit où l'on choisit d'y poser une pièce."""
    vus = vus or set()
    out = []
    while eid and eid not in vus and eid in p.etats:
        vus.add(eid)
        out.append(titre(p, eid))
        eid = p.etats[eid].get("sert")
    return out


def _front_verrou(p, bid, camp):
    b = p.blocages[bid]
    qui, pourquoi = p.prevaut(bid)
    droite = ""
    if int(b.get("prete_tour") or 0) > p.tour:
        droite = "dans %d j" % ((int(b["prete_tour"]) - p.tour) * JOURS_PAR_TOUR)
    tete = {"id": bid, "type": "verrou", "emoji": TYPES["verrou"], "camp": b["camp"],
            "titre": titre(p, bid),
            "corps": ", ".join(carte_piece(p, pc)["titre"] for pc in b["engage"] if pc in p.ressources),
            "pied": {"gauche": "", "droite": droite},
            "apparence": "verrou"}
    contre = adverse(b["camp"])     # qui répond à ce blocage, quel que soit le camp qui l'a posé
    pile = [_pile_clef(p, kid, contre, tete["titre"])
            for kid, k in sorted(p.cles.items(), key=lambda kv: kv[1].get("n") or 0)
            if bid in k["ouvre"] and k["camp"] == contre and not k["retiree"]]
    return {"id": bid, "sur": b["sur"], "sur_titre": titre(p, b["sur"]),
            "chaine": _chaine(p, b["sur"]),
            "prevaut": qui, "pourquoi": pourquoi, "tete": tete, "pile": pile}


def _front_frappe(p, mid, camp):
    m = p.menaces[mid]
    n = (int(m["arrive_tour"]) - p.tour + 1) * JOURS_PAR_TOUR
    tete = {"id": mid, "type": "frappe", "emoji": TYPES["frappe"], "camp": m["camp"],
            "titre": titre(p, mid) or ("frappe sur " + titre(p, m["cible"])),
            "corps": "vise " + titre(p, m["cible"]),
            "pied": {"gauche": "", "droite": "atterrit dans %d j" % max(n, 0)},
            "apparence": "route" if not m.get("suspendue_par") else "question"}
    tete_sous = _questions_sur(p, mid)
    pile = [{"id": bid, "type": "clef", "emoji": TYPES["clef"], "camp": camp,
             "titre": titre(p, bid), "corps": "", "apparence": "clef",
             "pied": {"gauche": "", "droite": "✅ protège"},
             "sous": [carte_piece(p, pc) for pc in p.blocages[bid]["engage"] if pc in p.ressources]}
            for bid, b in p.blocages.items() if b["sur"] == mid and not b["tombe"] and b["camp"] == camp]
    return {"id": mid, "sur": m["cible"], "sur_titre": titre(p, m["cible"]),
            "chaine": [],
            "prevaut": m["camp"] if not pile else camp, "pourquoi": "frappe en route",
            "tete": tete, "pile": tete_sous + pile}


# ---------------------------------------------------------------- la vue
def _marquer_neuf(objet, tou, vu):
    """Pose `neuf` sur toute carte du paquet dont l'id a été touché après `vu`.

    `vu` à zéro veut dire « pas de marque-page » — première ouverture, ou siège
    qui n'a jamais regardé cette partie — et alors RIEN n'est neuf : on ne peut
    pas avoir manqué ce dont on n'a jamais eu d'avant. Sans cette porte, la
    première ouverture marquait les trente-neuf cartes du plateau."""
    seuil = int(vu) if vu else None
    if isinstance(objet, dict):
        if objet.get("id") is not None and "type" in objet:
            objet["neuf"] = seuil is not None and int(tou.get(str(objet["id"]), 0)) > seuil
        for v in objet.values():
            _marquer_neuf(v, tou, vu)
    elif isinstance(objet, list):
        for v in objet:
            _marquer_neuf(v, tou, vu)
    return objet


def vue(p, camp="noir", vu=0):
    ennemi = adverse(camp)

    # LES DEUX CAMPS. Un front est un blocage ou une frappe encore debout, d'où
    # qu'il vienne : ce qu'ils tiennent contre nous ET ce que nous tenons contre
    # eux. Sans les seconds, on ne voit pas sa propre pression.
    fronts = []
    for bid, b in sorted(p.blocages.items(), key=lambda kv: kv[1].get("n") or 0):
        if not b["tombe"]:
            f = _front_verrou(p, bid, adverse(b["camp"]))
            f["camp"] = b["camp"]
            f["contre_nous"] = (b["camp"] == ennemi)
            fronts.append(f)
    for mid, m in sorted(p.menaces.items(), key=lambda kv: kv[1].get("n") or 0):
        if not m["realisee"] and not m["tombee"]:
            f = _front_frappe(p, mid, adverse(m["camp"]))
            f["camp"] = m["camp"]
            f["contre_nous"] = (m["camp"] == ennemi)
            fronts.append(f)

    # Ce qui s'oppose à un dessein s'oppose aussi à celui qu'il SERT : un
    # obstacle posé sur « la porte est acquise » barre la route du trône, et
    # dire « rien ne s'y oppose encore » sur la racine serait un mensonge.
    def _obstacles(eid, cp, vus=None):
        vus = vus or set()
        if eid in vus:
            return 0
        vus.add(eid)
        n = sum(1 for f in fronts if str(f["sur"]) == str(eid) and f["camp"] != cp)
        for cid, c in p.etats.items():
            if str(c.get("sert") or "") == str(eid) and not c.get("sorti"):
                n += _obstacles(cid, cp, vus)
        return n

    cibles = []
    for eid, e in p.etats.items():
        if e.get("sorti"):
            continue
        cp = e["camp"]
        obstacles = _obstacles(eid, cp)
        if e.get("vrai"):
            corps, app = "acquis", "vrai"
        elif e.get("vrai") is False:
            corps, app = "constaté faux", "faux"
        elif not e.get("deck"):
            corps, app = "entre au deck dans %d j" % ((int(e["arrive_tour"]) - p.tour) * JOURS_PAR_TOUR), "route"
        elif obstacles:
            corps, app = ("%d chose%s s'y oppose%s" % (obstacles, "s" if obstacles > 1 else "",
                                                       "nt" if obstacles > 1 else "")), "cible"
        else:
            corps, app = "rien ne s'y oppose encore", "cible"
        cibles.append({"id": eid, "type": "cible", "emoji": TYPES["cible"], "camp": cp,
                         "titre": titre(p, eid), "corps": corps,
                         "pied": {"gauche": ("sert " + titre(p, e["sert"])) if e.get("sert") else "",
                                  "droite": ""},
                         "apparence": app, "sous": _questions_sur(p, eid)})

    deck = {"main": [], "route": [], "remet": [], "posees": [], "detruites": []}
    eux = []
    ou = {"libre": "main", "route": "route", "remet": "remet", "posee": "posees", "detruite": "detruites"}
    for rid, r in sorted(p.ressources.items(), key=lambda kv: kv[0]):
        c = carte_piece(p, rid)
        (deck[ou[c["apparence"]]] if r["camp"] == camp else eux).append(c)

    dernier_camp = p.lignes[-1]["camp"] if p.lignes else ennemi
    trait = camp if dernier_camp in (ennemi, "arbitre") else ennemi
    dernier = int(p.lignes[-1].get("n") or 0) if p.lignes else 0
    return _marquer_neuf(
        {"partie": os.path.splitext(os.path.basename(p.chemin))[0], "camp": camp,
         "tour": p.tour, "jours": (p.tour - 1) * JOURS_PAR_TOUR, "jours_par_tour": JOURS_PAR_TOUR,
         "trait": trait, "trone": p.tenu_par(),
         "vu": int(vu or 0), "dernier": dernier,
         "cibles": cibles, "fronts": fronts, "deck": deck, "eux": eux,
         "consignes": dict(p.consignes)},
        touches(p), vu)
