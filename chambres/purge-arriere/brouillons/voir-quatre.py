# -*- coding: utf-8 -*-
import json, os, collections
racine = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
etat = os.path.join(racine, "etat")

ev = json.load(open(os.path.join(etat, "evenements.json"), encoding="utf-8"))
for x in ev:
    if x.get("id") in ("emissaire-lucerys", "emissaire-jacaerys", "mort-lucerys"):
        print(x["id"], "| statut:", x.get("statut"), "| prevu:", x.get("date_prevue"))

print()
pen = json.load(open(os.path.join(etat, "pensees.json"), encoding="utf-8"))
if isinstance(pen, dict):
    for k, v in pen.items():
        if isinstance(v, list):
            pen = v
            break
c = collections.Counter()
for x in pen:
    dt = x.get("date") or {}
    if isinstance(dt, dict) and dt.get("lune") == 4 and (dt.get("jour") or 0) > 3:
        c[x.get("personnage_id") or x.get("qui") or "?"] += 1
print("pensees du 4e, par tete :", dict(c))
print("clefs d'une pensee :", list(pen[-1]))

print()
ac = json.load(open(os.path.join(etat, "actes.json"), encoding="utf-8"))
c = collections.Counter()
for x in ac:
    dt = x.get("date") or {}
    if isinstance(dt, dict) and dt.get("lune") == 4 and (dt.get("jour") or 0) > 3:
        c[x.get("lieu_id") or "?"] += 1
print("actes du 4e, par lieu :", dict(c))
