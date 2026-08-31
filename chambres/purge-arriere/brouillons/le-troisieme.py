# -*- coding: utf-8 -*-
# Le 3e est-il joue au-dela de la minute 721 ? (l'horloge du monde y est posee)
import json, os, collections
racine = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
etat = os.path.join(racine, "etat")

for f in ["actes.json", "paroles.json", "pensees.json"]:
    d = json.load(open(os.path.join(etat, f), encoding="utf-8"))
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                d = v
                break
    avant, apres, sans = 0, 0, 0
    tard = []
    for x in d:
        dt = x.get("date") or {}
        if isinstance(dt, dict) and dt.get("lune") == 4 and dt.get("jour") == 3:
            m = dt.get("minute")
            if m is None:
                sans += 1
            elif m <= 721:
                avant += 1
            else:
                apres += 1
                tard.append((m, x.get("id") or x.get("qui")))
    tard.sort()
    print(f, "| le 3e : avant midi(<=721)", avant, "| apres", apres, "| sans heure", sans)
    for m, i in tard[-6:]:
        print("     ", m, i)
