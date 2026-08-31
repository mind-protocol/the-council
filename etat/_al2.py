# -*- coding: utf-8 -*-
import io
import json
import os
import sys
import time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = "C:/Users/reyno/le-conseil2/etat/"
lx = json.load(open(P + "lieux.json", encoding="utf-8"))
ll = lx if isinstance(lx, list) else lx.get("lieux", [])
print("pierremout :", [l for l in ll if l.get("id") == "pierremout"] or "ABSENT")
print("lieux.json ecrit a :", time.strftime("%H:%M:%S",
      time.localtime(os.path.getmtime(P + "lieux.json"))))
print("heure courante     :", time.strftime("%H:%M:%S"))
it = json.load(open(P + "intentions.json", encoding="utf-8"))
te = it if isinstance(it, list) else (it.get("intentions") or it.get("tetes") or [])
t = [x for x in te if x.get("personnage_id") == "alicent"]
if t:
    print("\nalicent — ignore :")
    for i in (t[0].get("ignore") or []):
        print("  -", str(i)[:220])
