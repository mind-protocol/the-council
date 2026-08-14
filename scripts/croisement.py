# -*- coding: utf-8 -*-
# CROISEMENT — de quelle taille est le frottement entre deux camps, jour par jour.
#
# CE N'EST PAS UNE CHAINE LOGIQUE, C'EST UNE ESTIMATION. On ne demande pas si
# un ost peut passer, ni qui gagnerait : on demande OU ET QUAND deux choses se
# frolent, et de quelle taille. Chaque actif de la table de guerre est un point
# avec un rayon et un poids ; deux actifs qui se recouvrent font des points.
#
# CE QUI EST MESURE, ET NON DECLARE. Aucune table de rayons ecrite a la main —
# c'etait la premiere version de ce script et elle etait fausse deux fois : elle
# ne couvrait que les neuf actifs militaires en ignorant les douze plis, les
# huit incidents et les trois oreilles, et elle posait des vitesses au doigt
# mouille. Ici :
#
#   * LA POSITION vient de `Geo.lieux` (ecrans/modules/geo.js), coordonnees 2-D
#     reelles tirees des provinces du mod AGOT. Un incident porte meme son
#     `point` en clair. `jours_de_pr` ne sert plus de coordonnee — deux places
#     a cinq jours de Port-Real dans deux directions opposees ne sont pas
#     voisines, et c'est exactement l'erreur qu'on retire.
#   * LA VITESSE se regresse sur les donnees : distance geometrique divisee par
#     `jours_de_pr`, place par place. Elle rend ~9 u/jour par terre et ~17 par
#     mer — soit, sans que personne l'ait ecrit nulle part, que la mer va deux
#     fois plus vite que la terre.
#   * LE RAYON D'UN ACTIF est sa vitesse multipliee par son AGE : un actif qu'on
#     n'a pas revu depuis dix jours s'etale de dix jours de route. C'est une
#     carte de croyances : ce qu'on n'a pas regarde recemment est flou, et le
#     flou grandit tout seul.
#   * UN INCIDENT DIT SA PROPRE VITESSE. Son `propage[]` porte des endroits
#     DATES : distance divisee par jours ecoules, mediane. Une rumeur n'a pas
#     besoin qu'on lui invente une portee, elle l'a deja parcourue.
#
# TROIS COLONNES, JAMAIS UNE. Un chiffre unique melangerait « je suis fort » et
# « je suis en danger » :
#     COUVERTURE  mes actifs sur mes places      — ma flotte pres de ma ville
#     MENACE      leurs actifs sur mes places    — ce qui me tombe dessus
#     CONTACT     mes actifs sur les leurs       — la ou ca se touche
#
# Usage :
#     python scripts/croisement.py --contre maison-hightower
#     python scripts/croisement.py --contre maison-hightower --jours 45
#     python scripts/croisement.py --contre maison-hightower --vrai
#     python scripts/croisement.py --contre maison-baratheon --detail
import argparse
import collections
import io
import json
import math
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
GEO = os.path.join(RACINE, "ecrans", "modules", "geo.js")

# Le noyau de recouvrement. Triangulaire et non gaussien : il se corrige a la
# main, et personne n'a jamais eu besoin d'une gaussienne pour dire que deux
# choses sont proches. C'est le SEUL nombre arbitraire du fichier.
def recouvrement(distance, rayon_a, rayon_b):
    somme = rayon_a + rayon_b
    if somme <= 0:
        return 0.0
    return max(0.0, 1.0 - distance / somme)


def lire(nom, defaut):
    p = nom if os.path.isabs(nom) else os.path.join(ETAT, nom)
    try:
        with io.open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (IOError, OSError, ValueError):
        return defaut


def geo_lieux():
    with io.open(GEO, encoding="utf-8", errors="replace") as fh:
        s = fh.read()
    m = re.search(r'"lieux"\s*:\s*(\{.*?\})\s*[,}]', s, re.S)
    if not m:
        raise SystemExit("geo.js ne porte pas de bloc `lieux` — relancer carte_geo.py")
    return {k: tuple(v) for k, v in json.loads(m.group(1)).items()}


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def en_jours(d):
    if not isinstance(d, dict) or d.get("annee") is None:
        return None
    return ((d["annee"] * 12 + d.get("lune", 1) - 1) * 30) + d.get("jour", 1) - 1


def depuis_jours(n):
    n = int(n)
    jour = n % 30 + 1
    reste = n // 30
    return {"annee": reste // 12, "lune": reste % 12 + 1, "jour": jour}


def dire(d):
    return "{}.{}.{}".format(d["annee"], d["lune"], d["jour"])


# ------------------------------------------------------------- les vitesses

def calibrer(G, lieux):
    """La vitesse ne se pose pas : elle se regresse sur ce qui est deja ecrit.

    Une place a une distance geometrique de Port-Real et un `jours_de_pr`. Le
    rapport des deux est une vitesse observee. On separe par TYPE DE PLACE —
    une ile ne se rejoint pas a pied — et l'on prend la mediane, qui encaisse
    un lieu mal date sans que tout le modele parte de travers.
    """
    origine = G.get("port-real")
    par_voie = collections.defaultdict(list)
    for lid, l in lieux.items():
        j = l.get("jours_de_pr")
        if lid not in G or not isinstance(j, (int, float)) or j <= 0:
            continue
        v = distance(G[lid], origine) / float(j)
        par_voie["mer" if l.get("type") == "ile" else "terre"].append(v)
    out = {}
    for voie, vs in par_voie.items():
        vs.sort()
        out[voie] = vs[len(vs) // 2]
    if "terre" not in out:
        out["terre"] = 9.0
    out.setdefault("mer", out["terre"] * 2)
    return out


def vitesse_mesuree(actif, G, vitesses):
    """Ce que CET actif a reellement parcouru, quand son histoire le dit.

    Un incident porte `propage[]` : des endroits dates. Distance divisee par
    jours ecoules, mediane des sauts. Tout le reste retombe sur la calibration
    generale — mer si l'actif est une flotte ou tient une ile, terre sinon.
    """
    depart = position(actif, G)
    t0 = en_jours(actif.get("date"))
    mesures = []
    if depart and t0 is not None:
        for p in actif.get("propage") or []:
            cible = p.get("ou") or p.get("lieu")
            pt = (tuple(p["point"]) if isinstance(p.get("point"), list)
                  else G.get(cible))
            t1 = en_jours(p.get("date"))
            if pt and t1 is not None and t1 > t0:
                mesures.append(distance(depart, pt) / float(t1 - t0))
    if mesures:
        mesures.sort()
        return mesures[len(mesures) // 2]
    if actif.get("genre") in ("flotte", "dragon"):
        return vitesses["mer"]
    return vitesses["terre"]


def position(actif, G):
    if isinstance(actif.get("point"), list) and len(actif["point"]) == 2:
        return tuple(actif["point"])
    return G.get(actif.get("ou"))


# ---------------------------------------------------------------- les actifs

def poids(actif):
    """Une force quand il y en a une, sinon un. Une oreille ne pese pas des
    hommes : elle pese d'etre la, et une seule suffit a changer une affaire."""
    f = actif.get("force")
    return float(f) if isinstance(f, (int, float)) and f > 0 else 1.0


def recueillir(jetons, G, vitesses, vrai):
    out = []
    for x in jetons:
        if x.get("statut") in ("clos", "resolu", "perime"):
            continue
        if not vrai and x.get("certitude") == "rumeur":
            # Le mode `--su` garde ce que le joueur croit tenir, y compris de
            # travers ; il ne garde pas ce qu'il tient pour une rumeur nue.
            continue
        p = position(x, G)
        if not p:
            continue
        out.append({
            "id": x.get("id"), "nom": x.get("nom") or x.get("id"),
            "genre": x.get("genre"), "camp": (x.get("camp") or "").lower(),
            "point": p, "poids": poids(x),
            "t0": en_jours(x.get("date")),
            "vitesse": vitesse_mesuree(x, G, vitesses),
            "certitude": x.get("certitude"),
        })
    return out


def mouvements(traits, G, vitesses):
    """Ce qui BOUGE est un trait, pas un jeton : la table pose les positions et
    trace les deplacements a part. Un trait porte son depart, son arrivee et sa
    date ; la duree se deduit de la distance et de la vitesse de sa voie."""
    out = []
    for t in traits:
        if t.get("genre") not in ("marche", "mer", "vol", "attaque", "retraite"):
            continue
        a, b = G.get(t.get("de")), G.get(t.get("vers"))
        t0 = en_jours(t.get("date"))
        if not a or not b or t0 is None:
            continue
        v = vitesses["mer"] if t["genre"] in ("mer", "vol") else vitesses["terre"]
        out.append({
            "id": t.get("id"), "nom": t.get("nom") or t.get("id"),
            "camp": (t.get("camp") or "").lower(),
            "a": a, "b": b, "t0": t0, "duree": max(1.0, distance(a, b) / v),
            "vitesse": v, "poids": 1.0, "genre": t.get("genre"),
        })
    return out


def etat_du_jour(actif, jour, diametre):
    """Ou il est ce jour-la, et de combien il est flou.

    LE FLOU NE GRANDIT QUE POUR CE QU'ON NE TIENT PAS POUR SUR. C'est la
    `certitude` de la marque qui commande, et non son genre : une position
    `sure` est une position, elle vaut un jour de route et rien de plus ; une
    position `rapportee` s'etale d'un jour de route par jour ecoule depuis
    qu'on l'a vue. C'est la definition meme d'une carte de croyances, et ca
    evite une liste de genres ecrite a la main.

    Passe le diametre du theatre, la marque ne dit plus rien : on la rend
    PERDUE DE VUE plutot que de la faire toucher tout le monde.
    """
    age = max(1.0, (jour - actif["t0"]) if actif["t0"] is not None else 1.0)
    if actif.get("certitude") == "sure":
        age = 1.0
    rayon = actif["vitesse"] * age
    if rayon > diametre:
        return None
    return actif["point"], rayon


def marches_des_plans(G, vitesses, vrai):
    """CE QUI MARCHE SUR NOUS, DEPUIS LES PLANS D'EN FACE.

    Un plan adverse ne peut pas vivre sur la table de guerre du joueur : cette
    table est une carte de CROYANCES, et y poser un ost que personne n'a vu
    serait trahir le brouillard au premier coup d'oeil. Sa place est dans
    `plans.json`, qui n'est servi par aucune route du serveur.

    Une piece qui marche porte quatre champs, et pas un de plus :
        de_lieu · vers_lieu · arrive_le · force
    Sans `vers_lieu`, une piece est une intention et ne bouge rien — c'est
    exactement l'etat de Hightower et de Baratheon avant aujourd'hui : deux
    plans entiers, dix-neuf actions, et aucune destination. Le script ne les
    inventera pas ; il montre leur absence en rendant une colonne plate.

    En mode `--su` elles ne comptent pas : le joueur ne voit que ce qu'il a mis
    sur sa propre table.
    """
    if not vrai:
        return []
    brut = lire("plans.json", {})
    plans = brut.get("plans", []) if isinstance(brut, dict) else brut
    out = []
    for pl in plans:
        camp = (pl.get("camp") or "vert").lower()
        for fam in ("etats_cibles", "actions", "verrous", "clefs"):
            for x in pl.get(fam) or []:
                a = G.get(x.get("de_lieu"))
                b = G.get(x.get("vers_lieu"))
                t1 = en_jours(x.get("arrive_le"))
                if not b or t1 is None:
                    continue
                v = vitesses["mer"] if x.get("voie") == "mer" else vitesses["terre"]
                if not a:
                    a = b
                    duree = 1.0
                else:
                    duree = max(1.0, distance(a, b) / v)
                out.append({
                    "id": x.get("id"), "nom": x.get("quoi") or x.get("id"),
                    "camp": camp, "a": a, "b": b, "t0": t1 - duree,
                    "duree": duree, "vitesse": v, "genre": "plan",
                    "poids": float(x.get("force") or 1),
                })
    return out


def etat_mouvement(m, jour):
    if jour < m["t0"]:
        return None
    part = min(1.0, (jour - m["t0"]) / m["duree"])
    p = (m["a"][0] + (m["b"][0] - m["a"][0]) * part,
         m["a"][1] + (m["b"][1] - m["a"][1]) * part)
    return p, m["vitesse"]


def places_du_camp(lieux, maisons_du_camp):
    return {lid for lid, l in lieux.items() if l.get("controle_id") in maisons_du_camp}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contre", required=True, help="maison ou camp d'en face")
    ap.add_argument("--siege", default="rhaenyra")
    ap.add_argument("--jours", type=int, default=40)
    ap.add_argument("--vrai", action="store_true",
                    help="tout ce qui est ecrit, et non ce que le siege croit")
    ap.add_argument("--detail", action="store_true", help="les couples qui font le score")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    G = geo_lieux()
    brut = lire("lieux.json", [])
    brut = brut.get("lieux", brut) if isinstance(brut, dict) else brut
    lieux = {l["id"]: l for l in brut if isinstance(l, dict) and l.get("id")}
    vitesses = calibrer(G, lieux)

    table = lire(os.path.join(ETAT, "joueurs", args.siege, "jetons.json"), {})
    jetons = table.get("jetons", []) if isinstance(table, dict) else table
    traits = table.get("traits", []) if isinstance(table, dict) else []

    maisons = lire("maisons.json", [])
    maisons = maisons.get("maisons", maisons) if isinstance(maisons, dict) else maisons
    cible = next((m for m in maisons if m.get("id") == args.contre), None)
    # `maisons.json` ne porte pas de champ `camp` : il porte une allegeance
    # AFFICHEE et une allegeance REELLE. On lit l'affichee — c'est ce que le
    # siege peut savoir, et la reelle est precisement ce qu'on n'a pas le droit
    # de montrer. `--vrai` seul autorise la seconde.
    def camp_de(m):
        return ((m.get("allegeance_reelle") if args.vrai else None)
                or m.get("allegeance_affichee") or "neutre").lower()
    camp_adverse = camp_de(cible or {})
    maisons_miennes = {m["id"] for m in maisons if camp_de(m) == "noir"}

    actifs = recueillir(jetons, G, vitesses, args.vrai)
    bouges = mouvements(traits, G, vitesses) +         marches_des_plans(G, vitesses, args.vrai)
    miens = [a for a in actifs if a["camp"] == "noir"] + \
            [m for m in bouges if m["camp"] == "noir"]
    leurs = [a for a in actifs if a["camp"] == camp_adverse] + \
            [m for m in bouges if m["camp"] == camp_adverse]

    mes_places = [(lid, G[lid]) for lid in places_du_camp(lieux, maisons_miennes)
                  if lid in G]
    rayon_place = vitesses["terre"]  # une place rayonne d'une journee de route

    # LE DIAMETRE DU THEATRE — la borne au-dela de laquelle une position ne dit
    # plus rien. Un actif dont le flou depasse la scene entiere n'est pas
    # partout : il est PERDU DE VUE, et il sort du compte au lieu de le
    # dominer. Sans cette borne le contact montait indefiniment, chaque jour
    # d'ignorance elargissant tout le monde jusqu'a ce que tout touche tout.
    tous_points = [p for _, p in mes_places] +         [x["point"] for x in actifs if x.get("point")]
    diametre = max((distance(a, b) for a in tous_points for b in tous_points),
                   default=1.0)

    monde = lire("monde.json", {}).get("date") or {"annee": 129, "lune": 1, "jour": 1}
    j0 = en_jours(monde)

    def pose(x, jour):
        if "a" in x:
            return etat_mouvement(x, jour)
        return etat_du_jour(x, jour, diametre)

    lignes = []
    for k in range(args.jours + 1):
        jour = j0 + k
        couverture = menace = contact = 0.0
        couples = []
        for x in miens:
            e = pose(x, jour)
            if not e:
                continue
            px, rx = e
            for lid, pl in mes_places:
                couverture += recouvrement(distance(px, pl), rx, rayon_place) \
                    * math.sqrt(x["poids"])
            for y in leurs:
                f = pose(y, jour)
                if not f:
                    continue
                py, ry = f
                r = recouvrement(distance(px, py), rx, ry)
                if r > 0:
                    v = r * math.sqrt(x["poids"] * y["poids"])
                    contact += v
                    couples.append((v, x["nom"], y["nom"]))
        for y in leurs:
            f = pose(y, jour)
            if not f:
                continue
            py, ry = f
            for lid, pl in mes_places:
                menace += recouvrement(distance(py, pl), ry, rayon_place) \
                    * math.sqrt(y["poids"])
        couples.sort(reverse=True)
        lignes.append({"date": dire(depuis_jours(jour)),
                       "couverture": round(couverture, 1),
                       "menace": round(menace, 1),
                       "contact": round(contact, 1),
                       "couples": couples[:3]})

    if args.json:
        print(json.dumps({"contre": args.contre, "camp": camp_adverse,
                          "vitesses": vitesses, "jours": lignes},
                         ensure_ascii=False, indent=1))
        return 0

    print("CROISEMENT — {} (camp {}) vu du siege de {}".format(
        args.contre, camp_adverse, args.siege))
    print("  vitesses regressees sur lieux.json : terre {:.1f} u/j · mer {:.1f} u/j"
          .format(vitesses["terre"], vitesses["mer"]))
    print("  {} actifs a moi · {} a eux · {} de mes places · theatre {:.0f} u"
          .format(len(miens), len(leurs), len(mes_places), diametre))
    print("  estimation, pas une chaine logique : ou et quand ca se frole, et de"
          " quelle taille.")
    print()
    print("  {:<12} {:>10} {:>8} {:>8}   {}".format(
        "jour", "couverture", "menace", "contact", "ce qui se touche"))
    for l in lignes:
        quoi = ""
        if l["couples"]:
            v, a, b = l["couples"][0]
            quoi = "{} / {}".format(a[:26], b[:26])
        print("  {:<12} {:>10} {:>8} {:>8}   {}".format(
            l["date"], l["couverture"], l["menace"], l["contact"], quoi))
    pic = max(lignes, key=lambda l: l["contact"])
    print()
    print("PIC DE CONTACT : {} a {}".format(pic["contact"], pic["date"]))
    for v, a, b in pic["couples"]:
        print("   {:6.1f}  {}  <->  {}".format(v, a[:34], b[:34]))
    if pic["contact"] == 0:
        print("   AUCUN CONTACT SUR LA FENETRE. Rien de ce camp n'approche rien")
        print("   de ce qui est a nous : leur plan se joue ailleurs, entierement.")
    if args.detail:
        print()
        print("LES ACTIFS RETENUS")
        for x in miens + leurs:
            print("   {:<6} {:<9} poids {:>6.0f}  v {:>5.1f}  {}".format(
                x["camp"], x.get("genre") or "?", x["poids"], x["vitesse"],
                x["nom"][:44]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
