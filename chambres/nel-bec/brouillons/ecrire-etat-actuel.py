# -*- coding: utf-8 -*-
# Une ignorance ecrite en prose ne referme rien. Celle-la est devenue un verrou :
# je le dis a l'endroit ou j'avais ecrit l'ignorance.
import json, io, os

P = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "..", "..", "..", "etat", "books",
                                  "nera-les-portes.json"))
d = json.load(io.open(P, encoding="utf-8"))

VIEUX = (u"Je ne sais pas ce qui passe la Gadoue entre la nuit et le point du "
         u"jour : personne de chez moi n'y est encore.")
NEUF = (u"Je ne sais pas ce qui passe la Gadoue entre la nuit et le point du "
        u"jour : personne de chez moi n'y est, et personne n'y sera. "
        u"**Le 3e a midi j'ai cesse d'appeler ca une ignorance** : la nuit du 2e "
        u"au 3e la porte a ete ouverte a une heure ou elle ne l'avait pas ete en "
        u"quatorze mois, et ce qui n'etait qu'un blanc dans mon savoir est "
        u"devenu un empechement contre l'etat lui-meme. C'est le verrou 69004, "
        u"et sa clef 69013 ne veille pas la nuit : elle la lit dans la boue au "
        u"point du jour.")

n = 0
for t in d["tables"]:
    if not t["titre"].startswith(u"\U0001F3F0"):
        continue
    for l in t["lignes"]:
        c = l["cellules"]
        if u"ÉTAT ACTUEL" in c[0] and VIEUX in c[1]:
            c[1] = c[1].replace(VIEUX, NEUF)
            n += 1

json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("etat actuel repris : %d" % n)
