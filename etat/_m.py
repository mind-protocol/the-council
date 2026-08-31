# -*- coding: utf-8 -*-
import glob
import io
import json
import os
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = "C:/Users/reyno/le-conseil2/etat/"

print("=== 22049 dans les books")
for f in glob.glob(P + "books/*.json"):
    try:
        s = open(f, encoding="utf-8").read()
    except Exception:
        continue
    if "22049" not in s:
        continue
    j = json.loads(s)
    for t in j.get("tables") or []:
        for lg in t.get("lignes") or []:
            c = lg.get("cellules") or []
            if c and "22049" in str(c[0]):
                print("  [%s] %s" % (os.path.basename(f)[:-5], t.get("titre")))
                for k, v in zip(t.get("colonnes") or [], c):
                    if str(v).strip():
                        print("     %-20s %s" % (k[:20], str(v)[:400]))

print("\n=== 'maree' / 'vive-eau' / 'morte-eau' ailleurs dans etat/")
for nom in ("actes.json", "paroles.json", "conclusions.json", "mains.json",
            "pensees.json"):
    try:
        j = json.load(open(P + nom, encoding="utf-8"))
    except Exception:
        continue
    lst = j if isinstance(j, list) else next(
        (v for v in j.values() if isinstance(v, list)), [])
    n = 0
    for x in lst:
        s = json.dumps(x, ensure_ascii=False).lower()
        if "vive-eau" in s or "vive eau" in s or "basse mer" in s or "pleine mer" in s:
            n += 1
            if n <= 3:
                print("  [%s] %s" % (nom, json.dumps(x, ensure_ascii=False)[:300]))
    print("  -> %s : %d entrees citant une maree" % (nom, n))
