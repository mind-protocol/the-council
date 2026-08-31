import json, io

p = "C:/Users/reyno/le-conseil2/chambres/marec-fosse/books/affaire-marec-fosse.json"
d = json.load(io.open(p, encoding="utf-8"))

tabs = d["tables"]
verrous = [i for i, t in enumerate(tabs) if t["titre"].strip().endswith("Verrous")]
print("tables verrous:", verrous)
if len(verrous) == 2:
    vieux, neuf = tabs[verrous[0]], tabs[verrous[1]]
    # la table neuve garde ses colonnes ; on lui ajoute la ligne du vieux
    # qui n'a pas d'equivalent (le lord prisonnier), renumerotee.
    garde = None
    for l in vieux["lignes"]:
        if "prisonnier de celui" in l["cellules"][1]:
            garde = l["cellules"][:]
    if garde:
        garde[0] = "V.5"
        neuf["lignes"].append({"cellules": garde})
    d["tables"] = [t for i, t in enumerate(tabs) if i != verrous[0]]
    json.dump(d, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("fusionne — une seule table de verrous, lignes:",
          [l["cellules"][0] for l in neuf["lignes"]])
else:
    print("rien a fusionner")
