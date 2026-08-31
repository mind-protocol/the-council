import json, sys
f, num = sys.argv[1], sys.argv[2]
d = json.load(open(f, encoding="utf8"))
for t in d["tables"]:
    cols = [c.get("titre") if isinstance(c, dict) else c for c in t.get("colonnes", [])]
    for l in t["lignes"]:
        cel = l.get("cellules", [])
        if cel and num in str(cel[0]):
            print("TABLE:", t["titre"])
            for i, c in enumerate(cols):
                v = cel[i] if i < len(cel) else ""
                print("  -", c, "=", v)
            print("  --- autres clefs:", {k: v for k, v in l.items() if k != "cellules"})
