import json, sys
f = sys.argv[1]
d = json.load(open(f, encoding="utf8"))
want = sys.argv[2:] if len(sys.argv) > 2 else None
for t in d["tables"]:
    ti = t["titre"]
    if want and not any(w in ti for w in want):
        continue
    print("=" * 8, repr(ti))
    print("COLS:", [c.get("titre") if isinstance(c, dict) else c for c in t.get("colonnes", [])])
    for l in t["lignes"]:
        print(json.dumps(l, ensure_ascii=False)[:900])
