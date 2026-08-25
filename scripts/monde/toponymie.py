# -*- coding: utf-8 -*-
"""TOPONYMIE — projeter les noms humains sur la ville calculée.

La géométrie reste dans ``<ville>.graph.json`` et ``<ville>.rues.json``. Ce
module ajoute la couche qui manquait entre « un nœud à 2705, 2466 » et « la
place des Trois-Seaux » :

* les grands axes conservent leur nom sur chaque arête de voirie ;
* les noms d'usage sont ancrés sur de vrais carrefours du graphe ;
* le plan 2D reçoit la géométrie, la position d'étiquette et l'importance de
  chaque toponyme ;
* le même catalogue reste lisible par les systèmes futurs (messagers, ordres,
  recherche des siens) sans dépendre du rendu SVG.

Le catalogue versionné de ``scripts/ville/`` est la source humaine. Ce script
ne choisit aucun nom : il vérifie et projette vers les sorties de ``monde/``.

    python scripts/monde/toponymie.py --lieu port-real
    python scripts/monde/toponymie.py --lieu port-real --appliquer
"""
import argparse
import io
import json
import math
import os
import sys
import tempfile
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MONDE = os.path.join(RACINE, "monde")
PREFIXES = {"port-real": "portreal", "peyredragon": "peyredragon"}
CATALOGUES = {
    "portreal": os.path.join(RACINE, "scripts", "ville", "port-real-toponymie.json"),
}


def lire(chemin):
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


def normaliser(texte):
    """Une clef de comparaison, jamais un nom à montrer."""
    texte = unicodedata.normalize("NFKD", str(texte or ""))
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    return (texte.casefold().replace("’", "'").replace("œ", "oe")
            .replace("-", " ").replace("'", " ").strip())


def chemin_catalogue(prefixe):
    return CATALOGUES.get(prefixe, os.path.join(
        RACINE, "scripts", "ville", prefixe + "-toponymie.json"))


def catalogue(prefixe):
    chem = chemin_catalogue(prefixe)
    return lire(chem) if os.path.exists(chem) else None


def _uniques(items, champ, quoi):
    vus = {}
    for item in items:
        valeur = normaliser(item.get(champ))
        if not valeur:
            raise ValueError("%s sans %s" % (quoi, champ))
        if valeur in vus:
            raise ValueError("%s %s en double : %s" % (quoi, champ, item.get(champ)))
        vus[valeur] = item
    return vus


def verifier_catalogue(cat):
    axes = cat.get("axes") or []
    reperes = cat.get("reperes") or []
    _uniques(axes, "id", "axe")
    _uniques(axes, "nom", "axe")
    _uniques(reperes, "id", "repère")
    _uniques(reperes, "nom", "repère")
    for r in reperes:
        if not r.get("ancre_noeud"):
            raise ValueError("repère sans ancre_noeud : " + r["nom"])
        if int(r.get("importance") or 0) not in (1, 2, 3):
            raise ValueError("importance hors de 1..3 : " + r["nom"])
        if not r.get("genre") or not r.get("statut"):
            raise ValueError("genre/statut manquant : " + r["nom"])
    return axes, reperes


def enrichir_rues(rues, prefixe, strict=True):
    """Ajoute le catalogue à une projection de rues, sans casser son format.

    ``reperes`` reste l'annuaire historique nom -> nœud attendu par le serveur.
    Les informations plus riches vivent dans ``reperes_meta``.
    """
    cat = catalogue(prefixe)
    if not cat:
        return rues
    axes, reperes = verifier_catalogue(cat)
    par_nom = {normaliser(a["nom"]): a for a in axes}
    rencontres = set()
    for ar in rues.get("aretes", []):
        brut = ar.get("n")
        axe = par_nom.get(normaliser(brut)) if brut else None
        if not axe:
            continue
        ar["n"] = axe["nom"]
        ar["axe"] = axe["id"]
        rencontres.add(axe["id"])
    manquent = [a["nom"] for a in axes if a["id"] not in rencontres]
    if strict and manquent:
        raise ValueError("axes absents des arêtes nommées : " + ", ".join(manquent))

    noeuds = rues.setdefault("noeuds", {})
    annuaire = rues.setdefault("reperes", {})
    meta = rues.setdefault("reperes_meta", {})
    adj = {}
    for ar in rues.get("aretes", []):
        adj.setdefault(ar.get("de"), []).append(ar)
        adj.setdefault(ar.get("vers"), []).append(ar)

    for rep in reperes:
        ancre = rep["ancre_noeud"]
        p = noeuds.get(ancre)
        if not p:
            raise ValueError("ancre absente du réseau : %s (%s)" % (ancre, rep["nom"]))
        if strict and len(adj.get(ancre, ())) < 3:
            raise ValueError("l'ancre n'est pas un carrefour : %s (%s)" %
                             (ancre, rep["nom"]))
        attendus = {normaliser(n) for n in rep.get("sur", [])}
        presents = {normaliser(ar.get("n")) for ar in adj.get(ancre, ()) if ar.get("n")}
        if strict and not attendus.issubset(presents):
            raise ValueError("axe absent à %s : %s" %
                             (rep["nom"], ", ".join(sorted(attendus - presents))))
        cle = "toponyme:" + rep["id"]
        noeuds[cle] = list(p)
        annuaire[rep["nom"]] = cle
        meta[rep["nom"]] = dict(rep)

    rues["axes"] = [dict(a) for a in axes]
    source = os.path.relpath(chemin_catalogue(prefixe), RACINE).replace("\\", "/")
    rues["toponymie"] = {"version": cat.get("version", 1),
                           "source": source,
                           "axes": len(axes), "reperes_locaux": len(reperes)}
    return rues


def _coudre(segments):
    """Recoud les arêtes d'un axe en polylignes à partir de leurs vrais nœuds."""
    par_noeud = {}
    for i, (de, vers, _p, _q) in enumerate(segments):
        par_noeud.setdefault(de, []).append(i)
        par_noeud.setdefault(vers, []).append(i)
    vus, lignes = set(), []
    # Les extrémités d'abord : un axe simple sort ainsi en une seule ligne.
    ordre = sorted(range(len(segments)),
                   key=lambda i: min(len(par_noeud[segments[i][0]]),
                                     len(par_noeud[segments[i][1]])))
    for depart in ordre:
        if depart in vus:
            continue
        de, vers, p, q = segments[depart]
        vus.add(depart)
        ligne, courant = [p, q], vers
        while True:
            suite = [i for i in par_noeud.get(courant, ()) if i not in vus]
            if not suite:
                break
            i = suite[0]
            a, b, pa, pb = segments[i]
            vus.add(i)
            if a == courant:
                ligne.append(pb); courant = b
            else:
                ligne.append(pa); courant = a
        lignes.append(ligne)
    return lignes


def _alleger(points, epsilon=1.5):
    """Douglas-Peucker : les coupures à chaque porte ne doivent pas gonfler le plan."""
    if len(points) < 3:
        return points
    garde = [False] * len(points)
    garde[0] = garde[-1] = True
    pile = [(0, len(points) - 1)]
    while pile:
        i, j = pile.pop()
        ax, ay = points[i]; bx, by = points[j]
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy)
        pire, k = 0.0, -1
        for m in range(i + 1, j):
            px, py = points[m]
            d = (math.hypot(px - ax, py - ay) if n < 1e-9 else
                 abs(dy * px - dx * py + bx * ay - by * ax) / n)
            if d > pire:
                pire, k = d, m
        if pire > epsilon and k > 0:
            garde[k] = True
            pile.extend(((i, k), (k, j)))
    return [p for p, g in zip(points, garde) if g]


def _longueur(ligne):
    return sum(math.dist(a, b) for a, b in zip(ligne, ligne[1:]))


def _point_a(ligne, distance):
    reste = max(0.0, distance)
    for a, b in zip(ligne, ligne[1:]):
        lg = math.dist(a, b)
        if reste <= lg or lg <= 1e-9:
            t = 0.0 if lg <= 1e-9 else reste / lg
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            if angle > 90: angle -= 180
            if angle < -90: angle += 180
            return x, y, angle
        reste -= lg
    a, b = ligne[-2], ligne[-1]
    return b[0], b[1], math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _chemin(lignes):
    morceaux = []
    for ligne in lignes:
        if len(ligne) < 2:
            continue
        morceaux.append("M" + "L".join("%.1f %.1f" % (p[0], p[1]) for p in ligne))
    return "".join(morceaux)


def axes_du_plan(rues):
    noeuds = rues.get("noeuds", {})
    par_id = {a["id"]: a for a in rues.get("axes", [])}
    groupes = {ident: [] for ident in par_id}
    genres = {ident: set() for ident in par_id}
    for ar in rues.get("aretes", []):
        ident = ar.get("axe")
        p, q = noeuds.get(ar.get("de")), noeuds.get(ar.get("vers"))
        if ident not in groupes or not p or not q:
            continue
        groupes[ident].append((ar["de"], ar["vers"], (p[0], p[1]), (q[0], q[1])))
        genres[ident].add(ar.get("g") or "rue")
    out = []
    for ident, meta in par_id.items():
        bruts = _coudre(groupes.get(ident, [])) if groupes.get(ident) else []
        lignes = [_alleger(l) for l in bruts if len(l) >= 2]
        if not lignes:
            continue
        principale = max(lignes, key=_longueur)
        fraction = float(meta.get("etiquette_fraction") or .52)
        x, y, angle = _point_a(principale, _longueur(principale) * fraction)
        item = dict(meta)
        item.update({
            "genres": sorted(genres[ident]),
            "longueur_m": round(sum(_longueur(l) for l in bruts), 1),
            "d": _chemin(lignes),
            "trace": [[[round(x, 1), round(y, 1)] for x, y in l] for l in lignes],
            "x": round(x, 1), "y": round(y, 1), "angle": round(angle, 1)
        })
        out.append(item)
    return sorted(out, key=lambda a: (-int(a.get("importance") or 1), a["nom"]))


def reperes_du_plan(rues):
    out = []
    meta = rues.get("reperes_meta", {})
    for nom, cle in rues.get("reperes", {}).items():
        p = rues.get("noeuds", {}).get(cle)
        if not p:
            continue
        genre_brut = cle.split(":")[0]
        # Les regards sont des nœuds techniques nommés, pas des lieux où un
        # habitant donne rendez-vous. L'ancien filtre exact laissait passer
        # ``regard-surface``.
        if genre_brut.startswith("regard") or normaliser(nom).startswith("regard de "):
            continue
        m = meta.get(nom) or {}
        item = {"nom": nom, "x": round(p[0], 1), "y": round(p[1], 1),
                "genre": m.get("genre") or genre_brut,
                "importance": int(m.get("importance") or 3),
                "statut": m.get("statut") or "repere-majeur"}
        for champ in ("id", "sur", "raison", "ancre_noeud"):
            if champ in m:
                item[champ] = m[champ]
        out.append(item)
    # Les petits d'abord, afin qu'un repère majeur soit peint par-dessus si les
    # deux se touchent.
    return sorted(out, key=lambda r: (r["importance"], r["nom"]))


def enrichir_plan(plan, rues, prefixe):
    if not catalogue(prefixe):
        return plan
    plan["axes"] = axes_du_plan(rues)
    plan["reperes"] = reperes_du_plan(rues)
    plan["toponymie"] = dict(rues.get("toponymie") or {})
    return plan


def _ecrire_atomique(chemin, donnees):
    dossier = os.path.dirname(os.path.abspath(chemin))
    fd, tmp = tempfile.mkstemp(prefix=os.path.basename(chemin) + ".",
                               suffix=".tmp", dir=dossier)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, chemin)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    ap = argparse.ArgumentParser(description="Vérifier et projeter la toponymie")
    ap.add_argument("--lieu", default="port-real")
    ap.add_argument("--rues", default=None)
    ap.add_argument("--plan", default=None)
    ap.add_argument("--appliquer", action="store_true")
    a = ap.parse_args()
    prefixe = PREFIXES.get(a.lieu, a.lieu)
    chem_rues = a.rues or os.path.join(MONDE, prefixe + ".rues.json")
    chem_plan = a.plan or os.path.join(MONDE, prefixe + ".plan2d.json")
    if not catalogue(prefixe):
        print("pas de catalogue : " + chemin_catalogue(prefixe))
        return 1
    rues = enrichir_rues(lire(chem_rues), prefixe, strict=True)
    plan = enrichir_plan(lire(chem_plan), rues, prefixe)
    cat = catalogue(prefixe)
    locaux = len(cat.get("reperes") or [])
    print("%s : %d axes, %d repères locaux, %d repères affichables" %
          (a.lieu, len(plan.get("axes") or []), locaux, len(plan.get("reperes") or [])))
    if prefixe == "portreal" and locaux != 50:
        raise ValueError("Port-Réal doit porter exactement 50 repères locaux")
    if a.appliquer:
        _ecrire_atomique(chem_rues, rues)
        _ecrire_atomique(chem_plan, plan)
        print("projections mises à jour : %s, %s" %
              (os.path.basename(chem_rues), os.path.basename(chem_plan)))
    else:
        print("vérification seule; ajouter --appliquer pour écrire")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
