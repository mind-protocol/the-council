# -*- coding: utf-8 -*-
"""Le 5e a-t-il ete VECU puis purge, ou n'a-t-il jamais ete ecrit ?

La question de mj-barralfond, et elle se tranche sur l'objet git : l'etat tel
qu'il etait AVANT ma passe (commit 7add995, monde.date = 129.4.9 minute 540).
Si des pieces y portent une date du 5e au 9e, le jour a eu lieu et je l'ai
retire. S'il n'y en a aucune, le compteur avait pris cinq crans a vide.
"""
import json, subprocess, collections, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

for f in ["actes.json", "paroles.json", "pensees.json", "info.json", "annales.json"]:
    brut = subprocess.run(["git", "show", "HEAD:etat/" + f],
                          capture_output=True, cwd="C:/Users/reyno/le-conseil2")
    if brut.returncode:
        print(f, ": pas dans le commit")
        continue
    d = json.loads(brut.stdout.decode("utf-8"))
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, list):
                d = v
                break
    c = collections.Counter()
    exemples = []
    for x in d:
        if not isinstance(x, dict):
            continue
        dt = x.get("date")
        if isinstance(dt, dict) and dt.get("lune") == 4 and (dt.get("jour") or 0) >= 4:
            c[dt["jour"]] += 1
            if dt["jour"] >= 5 and len(exemples) < 5:
                exemples.append((dt["jour"], dt.get("minute"), x.get("id") or x.get("qui")))
    print("%-14s AVANT ma passe, par jour : %s" % (f, dict(sorted(c.items()))))
    for e in exemples:
        print("      ", e)
