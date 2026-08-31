# -*- coding: utf-8 -*-
import json, os
racine = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
d = json.load(open(os.path.join(racine, "etat", "evenements.json"), encoding="utf-8"))
for x in d:
    dt = x.get("date") or x.get("date_prevue") or {}
    if isinstance(dt, dict) and dt.get("lune") == 4 and (dt.get("jour") or 0) > 3:
        if not str(x.get("id", "")).startswith("prog-"):
            print(dt, "|", x.get("id"), "|", str(x.get("titre") or x.get("resume") or "")[:120])
            print("   clefs:", list(x))
