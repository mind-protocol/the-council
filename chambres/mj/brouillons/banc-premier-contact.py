# -*- coding: utf-8 -*-
"""LE PREDICAT DE PREMIER CONTACT, X.24 — deux corps vivants de camps opposes
dans le meme lieu_id. Ne lit que la verite : personnages.json, jamais les
jetons de croyance d'un siege."""
import io
import json
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = "C:/Users/reyno/le-conseil2/etat/"
pers = json.load(open(P + "personnages.json", encoding="utf-8"))
pl = pers if isinstance(pers, list) else pers.get("personnages", [])
NOIR = {"maison-targaryen-noir", "maison-velaryon", "maison-inchauspe",
        "maison-reynolds", "maison-bar-emmon", "maison-celtigar",
        "maison-massey", "maison-staunton"}
VERT = {"maison-targaryen-vert", "maison-hightower", "maison-rosby",
        "maison-stokeworth", "maison-strong"}


def camp(p):
    m = p.get("maison_id")
    return "noir" if m in NOIR else ("vert" if m in VERT else None)


par_lieu = {}
for p in pl:
    if p.get("etat") != "actif":
        continue
    c = camp(p)
    if not c or not p.get("lieu_id"):
        continue
    par_lieu.setdefault(p["lieu_id"], {"noir": [], "vert": []})[c].append(p["id"])

trouve = False
for lieu, d in sorted(par_lieu.items()):
    if d["noir"] and d["vert"]:
        trouve = True
        print("*** PREMIER CONTACT ***  lieu :", lieu)
        print("    noirs :", ", ".join(d["noir"]))
        print("    verts :", ", ".join(d["vert"]))
if not trouve:
    print("aucun contact — lieux occupes :", len(par_lieu))
