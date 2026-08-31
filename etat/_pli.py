# -*- coding: utf-8 -*-
import io
import json
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = "C:/Users/reyno/le-conseil2/etat/"
pj = json.load(open(P + "plis.json", encoding="utf-8"))
lp = pj if isinstance(pj, list) else (pj.get("plis") or [])
for x in lp:
    if x.get("id") in ("pli-mots-de-la-main-accalmie",
                       "pli-couronnement-rhaenyra-3-borros-baratheon"):
        print(json.dumps(x, ensure_ascii=False, indent=1)[:1200])
        print("-" * 60)
