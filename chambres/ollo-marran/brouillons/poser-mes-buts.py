# -*- coding: utf-8 -*-
import json, io
p = 'books/affaire-ollo-marran.json'
d = json.load(io.open(p, encoding='utf-8'))
neufs = [
    ["C.4", u"Rien ne me nomme par ecrit",
     u"Aucun feuillet, aucun gage, aucun recu, aucune date ne porte mon nom dans l'affaire du chantier du bout — et je refuse ceux qu'on m'offre, meme donnes de bonne foi.",
     u"le refus ecrit du gage de Sirel Quintaine, 129.4.3"],
    ["C.5", u"La case vide ne se remplit plus d'une main sans office",
     u"Toute case 'pour qui' ou 'payeur' laissee ouverte a la cloture est barree au trait, et ne se rouvre que d'une main d'office sous le paraphe du maitre de port.",
     u"la formule portee en tete du feuillet courant du registre du bureau"],
    ["C.6", u"Ma place tient, et Doss n'en sait rien",
     u"Je garde mon poste au bureau des roles, et rien de ce qui passe sous ma plume n'arrive a mon frere aine, qui parle maintenant pour vingt et un hommes devant la reine.",
     u"aucun mot du role sorti de ma bouche vers Peyredragon"],
]
for t in d['tables']:
    if t['titre'].endswith(u'Ce que je veux'):
        deja = set()
        for l in t['lignes']:
            deja.add(l['cellules'][0])
        for n in neufs:
            if n[0] not in deja:
                t['lignes'].append({"cellules": n})
        print([l['cellules'][0] for l in t['lignes']])
json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
