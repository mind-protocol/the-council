# -*- coding: utf-8 -*-
import json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "books", "affaire-purge-arriere.json")
d = json.load(open(p, encoding="utf-8"))
for t in d["tables"]:
    print("== TABLE :", t["titre"])
    print("   colonnes :", t["colonnes"])
    for i, l in enumerate(t["lignes"]):
        c = l["cellules"]
        print("   [%d] %s | %s | etat=%r" % (i, c[0], c[1][:60], c[5] if len(c) > 5 else "-"))
