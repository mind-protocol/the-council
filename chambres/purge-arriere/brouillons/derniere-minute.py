# -*- coding: utf-8 -*-
# La derniere minute ECRITE du monde, toutes tables du joue confondues.
import json, os
racine = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
etat = os.path.join(racine, "etat")
pire = None
for f in ["actes.json", "paroles.json", "info.json", "annales.json", "plis.json", "pensees.json"]:
    d = json.load(open(os.path.join(etat, f), encoding="utf-8"))
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, list):
                d = v
                break
    for x in d:
        if not isinstance(x, dict):
            continue
        dt = x.get("date")
        if not isinstance(dt, dict) or dt.get("annee") != 129:
            continue
        cle = (dt.get("lune") or 0, dt.get("jour") or 0, dt.get("minute") or 0)
        if pire is None or cle > pire[0]:
            pire = (cle, f, x.get("id") or x.get("qui"))
print("derniere piece ecrite :", pire)
