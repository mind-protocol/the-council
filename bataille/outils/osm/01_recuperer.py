# -*- coding: utf-8 -*-
"""Récupérer un morceau d'OpenStreetMap — la source brute, mise en cache.

    python bataille/outils/osm/01_recuperer.py --nom gelibolu --bbox 40.38,26.55,40.56,26.76

Interroge Overpass (lecture publique, sans clé) sur une emprise sud,ouest,nord,est
en degrés, et fige la réponse telle quelle dans <sortie>/<nom>.osm.json : les
éléments avec leurs tags et leur géométrie (lon/lat), plus un en-tête qui dit
l'emprise, la requête et la date. Rien n'est interprété ici — ce fichier est une
SOURCE, comme le mod AGOT pour geographie.py, pas une couche du jeu. La lecture
(projection en mètres, choix de ce qui tient encore en 1305, format `sol` de
etat/villes/<id>.json) est le pas suivant et se fait sur le cache, sans réseau.

Ce qu'on demande : toute la voirie (highway), la côte, l'eau et les cours d'eau,
les bois, l'occupation du sol (landuse), les lieux habités (place). OSM ne porte
PAS l'altitude : le relief vient d'ailleurs.
"""
import argparse, datetime, io, json, math, os, sys
from collections import Counter
import requests
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _travail import dossier_travail  # les intermédiaires vivent hors du dépôt

MOTEUR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # bataille/
RACINE = os.path.dirname(MOTEUR)
MIROIRS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
ENTETE = {"User-Agent": "la-companie/0.1 (jeu ; reynolds.nicorr@gmail.com)"}


def requete(bbox):
    b = ",".join(f"{v:.5f}" for v in bbox)
    return f"""[out:json][timeout:120];
(
  way["highway"]({b});
  way["natural"~"^(coastline|water|wood|scrub|beach|cliff)$"]({b});
  relation["natural"="water"]({b});
  way["waterway"]({b});
  way["landuse"]({b});
  node["place"]({b});
  way["place"]({b});
);
out tags geom;"""


def longueur_m(geom):
    def lon_m(lat): return 111320 * math.cos(math.radians(lat))
    return sum(math.hypot((b["lon"] - a["lon"]) * lon_m(a["lat"]), (b["lat"] - a["lat"]) * 111320)
               for a, b in zip(geom, geom[1:]))


def inventaire(elements):
    km = Counter()
    for e in elements:
        t = e.get("tags", {})
        if e["type"] == "way" and "geometry" in e:
            cle = ("highway", t["highway"]) if "highway" in t else \
                  ("natural", t["natural"]) if "natural" in t else \
                  ("waterway", t["waterway"]) if "waterway" in t else \
                  ("landuse", t["landuse"]) if "landuse" in t else None
            if cle: km[cle] += longueur_m(e["geometry"]) / 1000
    lieux = [(t.get("name"), t.get("place")) for e in elements
             if e["type"] == "node" for t in [e.get("tags", {})] if t.get("place")]
    return km, lieux


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nom", required=True)
    ap.add_argument("--bbox", help="sud,ouest,nord,est en degrés — requis si le cache n'existe pas")
    ap.add_argument("--sortie", help="dossier de travail (défaut : bataille/donnees/osm/<nom>/)")
    ap.add_argument("--forcer", action="store_true", help="retirer même si le cache existe")
    a = ap.parse_args()
    a.sortie = a.sortie or dossier_travail(a.nom)
    deja = os.path.join(a.sortie, f"{a.nom}.osm.json")
    if os.path.exists(deja) and not a.forcer:
        print(f"cache présent : {os.path.relpath(deja, RACINE)} — rien retiré (--forcer pour relancer)"); return
    if not a.bbox: sys.exit("pas de cache pour ce nom : --bbox est requis")
    bbox = [float(v) for v in a.bbox.split(",")]
    if len(bbox) != 4 or not (bbox[0] < bbox[2] and bbox[1] < bbox[3]):
        sys.exit("bbox attendue : sud,ouest,nord,est avec sud<nord et ouest<est")
    q = requete(bbox)
    r = None
    for url in MIROIRS:  # le serveur public rend parfois 504 sous charge : on passe au miroir
        r = requests.post(url, data={"data": q}, headers=ENTETE, timeout=180)
        if r.status_code == 200: break
        print(f"{url} a répondu {r.status_code}", file=sys.stderr)
    if r is None or r.status_code != 200:
        sys.exit("aucun miroir Overpass n'a répondu 200")
    d = r.json()
    els = d["elements"]
    os.makedirs(a.sortie, exist_ok=True)
    chemin = os.path.join(a.sortie, f"{a.nom}.osm.json")
    doc = {"_lisez_moi": "Source brute OpenStreetMap (ODbL), figée par bataille/outils/osm/01_recuperer.py. Ne pas éditer : relancer.",
           "nom": a.nom, "bbox": bbox, "recupere_le": datetime.date.today().isoformat(),
           "generateur": d.get("generator"), "osm3s": d.get("osm3s"), "requete": q,
           "elements": els}
    with io.open(chemin, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    km, lieux = inventaire(els)
    print(f"{len(els)} éléments, {os.path.getsize(chemin)//1024} Ko -> {os.path.relpath(chemin, RACINE)}")
    for (fam, val), l in sorted(km.items(), key=lambda x: (x[0][0], -x[1])):
        print(f"  {fam:9s} {val:14s} {l:7.1f} km")
    print("  lieux habités :", ", ".join(f"{n} ({p})" for n, p in lieux if n))


if __name__ == "__main__":
    main()
