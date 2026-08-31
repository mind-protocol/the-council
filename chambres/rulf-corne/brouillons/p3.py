# -*- coding: utf-8 -*-
import json, io, os
p = os.path.join(os.path.dirname(__file__), '..', 'books', 'affaire-rulf-corne.json')
b = json.load(io.open(p, encoding='utf-8'))
NOTE = (u" TENU PAR LE MONDE le 3e de la 4e lune : acte "
        u"« acte-rulf-la-jambe-et-le-livre-107 » verse a la porte, et le champ "
        u"« passe » de ma fiche avec. An 107, commis de la barre, quarante et un "
        u"ans : jambe gauche prise entre le borde et le mole en degageant un "
        u"gamin sous une coque qui chassait sur son ancre. Le lendemain je lis "
        u"au registre du maitre de port d'alors qu'elle etait « au mouillage ». "
        u"J'ouvre mon propre livre ce jour-la. L'etat confirme au chiffre : "
        u"naissance en 66, vingt-deux ans de charge de 107 a 129 exactement. "
        u"Ma regle et ma faute ont le meme age.")
for t in b["tables"]:
    if t["titre"].startswith(u"⚔"):
        for l in t["lignes"]:
            c = l["cellules"]
            if c[0] == "P.3":
                c[5] = u"faite"
                c[7] = u"129-04-03"
                c[8] = c[8] + NOTE
with io.open(p, "w", encoding="utf-8") as f:
    json.dump(b, f, ensure_ascii=False, indent=1)
print(u"P.3 close")
