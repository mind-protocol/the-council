# -*- coding: utf-8 -*-
"""Nettoyer une source OSM pour 1305 — ce qui tient sept siècles, en mètres.

    python bataille/outils/osm/02_nettoyer.py --nom gelibolu

Lit <donnees>/osm/<nom>.osm.json (figé par 01_recuperer.py), sans réseau, et écrit
<donnees>/osm/<nom>.propre.json : une liste `sol` au vocabulaire du jeu, en
MÈTRES depuis le coin sud-ouest de l'emprise (x vers l'est, y vers le nord).
Aucun couloir n'est découpé : toute l'emprise passe, le cadrage est un pas
suivant.

Les règles, et pourquoi (toutes visibles dans REGLES, comptées à la sortie) :
- la côte, les plages, les falaises, les ruisseaux, les bois : de la
  géographie, elle tient ;
- les champs et les vergers : l'occupation agricole d'une péninsule change
  peu — gardés, en sachant que leurs limites sont d'aujourd'hui ;
- les pistes et sentiers, les routes tertiaires et non classées : c'est là
  qu'un chemin ancien survit, sous le tracé moderne ;
- les villages et hameaux : leurs sites sont anciens ; les lieux-dits (une
  fontaine, une crête, une ferme) sont des toponymes qu'une colonne nomme ;
- les bretelles des tertiaires et secondaires aussi : ce sont des bouts de la
  même route, et sans eux le réseau se casse en îlots ;
- REJETÉ : autoroutes, voies rapides et leurs bretelles, routes principales, rues
  résidentielles, voies de service, trottoirs, escaliers ; zones résidentielles,
  industrielles, militaires, décharges, cimetières, pelouses ; fossés, drains,
  barrages ; quartiers et places modernes.

OSM ne porte pas l'altitude : rien ici n'est un relief.
"""
import argparse, io, json, math, os, sys
from collections import Counter
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _travail import dossier_travail  # les intermédiaires vivent hors du dépôt

MOTEUR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # bataille/

# (famille, valeur) -> genre du jeu ; absent = rejeté.
REGLES = {
    ("natural", "coastline"): "cote", ("natural", "beach"): "greve", ("natural", "cliff"): "falaise",
    ("natural", "water"): "eau", ("natural", "wood"): "bois", ("natural", "scrub"): "lande",
    ("waterway", "stream"): "ru", ("waterway", "river"): "riviere",
    ("landuse", "forest"): "bois", ("landuse", "farmland"): "champ", ("landuse", "orchard"): "verger",
    ("landuse", "vineyard"): "vigne", ("landuse", "meadow"): "pre",
    ("highway", "track"): "piste", ("highway", "path"): "sentier", ("highway", "bridleway"): "sentier",
    ("highway", "tertiary"): "route", ("highway", "unclassified"): "route", ("highway", "secondary"): "route",
    # les bretelles des tertiaires et secondaires : sans elles, Bolayır est un
    # îlot de 136 sommets que rien ne relie au reste de la péninsule (mesuré)
    ("highway", "tertiary_link"): "route", ("highway", "secondary_link"): "route",
    ("place", "town"): "village", ("place", "village"): "village", ("place", "hamlet"): "village",
    ("place", "farm"): "lieu-dit", ("place", "locality"): "lieu-dit", ("place", "islet"): "ilot",
}
FAMILLES = ("highway", "natural", "waterway", "landuse", "place")


def cle(tags):
    for f in FAMILLES:
        if f in tags: return (f, tags[f])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nom", required=True)
    ap.add_argument("--donnees", help="dossier de travail (défaut : bataille/donnees/osm/<nom>/)")
    a = ap.parse_args()
    a.donnees = a.donnees or dossier_travail(a.nom)
    src = os.path.join(a.donnees, f"{a.nom}.osm.json")
    d = json.load(io.open(src, encoding="utf-8"))
    sud, ouest, nord, est = d["bbox"]
    kx = 111320 * math.cos(math.radians((sud + nord) / 2)); ky = 111320
    proj = lambda p: [round((p["lon"] - ouest) * kx, 1), round((p["lat"] - sud) * ky, 1)]

    sol, gardes, rejetes = [], Counter(), Counter()
    for e in d["elements"]:
        t = e.get("tags", {}); k = cle(t)
        if k is None: continue
        genre = REGLES.get(k)
        if genre is None:
            rejetes[k] += 1; continue
        if e["type"] == "node":
            pts = [proj(e)]
        elif e["type"] == "way" and e.get("geometry"):
            pts = [proj(p) for p in e["geometry"]]
        elif e["type"] == "relation":
            pts = [proj(p) for m in e.get("members", []) if m.get("geometry") for p in m["geometry"]]
        else:
            continue
        if not pts: continue
        entree = {"genre": genre, "points": pts, "osm": f'{e["type"]}/{e["id"]}', "tag": f"{k[0]}={k[1]}"}
        if t.get("name"): entree["nom"] = t["name"]
        sol.append(entree); gardes[genre] += 1

    out = {"_lisez_moi": "Source OSM nettoyée pour 1305 par bataille/outils/osm/02_nettoyer.py — règles dans le script. Mètres depuis le coin sud-ouest de l'emprise, y vers le nord.",
           "nom": a.nom, "bbox": d["bbox"], "source": os.path.basename(src), "recupere_le": d.get("recupere_le"),
           "origine": {"lat": sud, "lon": ouest}, "largeur_m": round((est - ouest) * kx), "hauteur_m": round((nord - sud) * ky),
           "gardes": dict(gardes), "rejetes": {f"{f}={v}": n for (f, v), n in rejetes.items()},
           "sol": sol}
    dst = os.path.join(a.donnees, f"{a.nom}.propre.json")
    with io.open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"{len(sol)} entrées gardées, {sum(rejetes.values())} rejetées, emprise {out['largeur_m']} x {out['hauteur_m']} m -> {os.path.relpath(dst, os.path.dirname(MOTEUR))}")
    print("  gardés  :", ", ".join(f"{g} {n}" for g, n in gardes.most_common()))
    print("  rejetés :", ", ".join(f"{f}={v} {n}" for (f, v), n in rejetes.most_common()))


if __name__ == "__main__":
    main()
