# -*- coding: utf-8 -*-
"""Le 12e au soir : ce que j'ai demande ce soir et qui n'a pas encore de reponse."""
import json

p = 'C:/Users/reyno/le-conseil2/chambres/daeron/en-souffrance.json'
d = json.load(open(p, encoding='utf-8'))

nouveau = {
 "qui": "ormund-hightower",
 "quoi": ("Un homme NOMME qui reponde du jour ou une nouvelle de Villevieille part vers lui "
          "sur la route, arrete avec mestre Norren avant son depart. Sans cela j'ecrirai dans "
          "le vide pendant qu'il marchera."),
 "demande_le": "129.5.12",
 "relance_le": "129.5.13",
 "note": ("Demande le soir du 12e, avec la raison : sa roukerie a garde Sombreval quatre jours "
          "(pli a l'aube du 18e, criee le 22e). Tout corbeau que je lui enverrai passe par la "
          "meme cage et les memes mains — un feu vu la nuit du 3e le rejoindrait le 7e, a "
          "soixante lieues, le croyant tranquille. A RELANCER AVANT QU'IL MONTE A CHEVAL : "
          "apres, c'est trop tard et pour toute la campagne.")
}
if not any(e.get('quoi', '').startswith('Un homme NOMME') for e in d['j_attends']):
    d['j_attends'].append(nouveau)

for e in d['on_attend_de_moi']:
    if 'vigies' in str(e.get('qui', '')):
        e['note'] = ("Ordre ecrit le 12e au soir dans la page « L'ordre du guet du ciel, et "
                     "l'essai de nuit » de mon volume : on guette le ciel et non la mer ; qui "
                     "voit crie et ne descend pas ; on sonne sur ce qu'on a vu et nul ne sera "
                     "repris pour une fausse cloche ; ce que la veille a vu me revient de la "
                     "main de celui qui l'a vu, sans passer par personne. NON ENCORE PORTE AUX "
                     "TOURS : je n'ai pas de capitaine du guet a qui l'ecrire, et je ne "
                     "l'inventerai pas. Il se dira de ma bouche, en montant.")

json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("j'attends   :", len(d['j_attends']))
for e in d['j_attends']:
    print('   -', e['qui'], '|', e['quoi'][:72])
print("on attend de moi :", len(d['on_attend_de_moi']))
for e in d['on_attend_de_moi']:
    print('   -', e['qui'], '|', ('RENDU' if e.get('rendu_le') else 'ouvert'))
