# -*- coding: utf-8 -*-
import json
p = 'books/affaire-daeron.json'
d = json.load(open(p, encoding='utf-8'))
act = [t for t in d['tables'] if 'Actions' in t['titre']][0]

AJOUT = (" || REPRIS LE 12e AU SOIR, et la demande precisee a lord Ormund : que le conge soit leve, "
         "copie et paraphe DATE D'AUJOURD'HUI — et s'il n'y en a pas eu, que L'ABSENCE soit attestee, "
         "datee d'aujourd'hui, dans les memes formes. Les deux reponses valent. Ollo m'a explique "
         "pourquoi la date compte plus que le contenu : une case vide ne vaut que tant qu'elle reste "
         "vide, il a vu DEUX FOIS cette lune une main sans office en remplir apres coup, et le jour ou "
         "un nom sera porte au 19e les deux papiers s'accorderont FAUSSEMENT — l'ecart sera efface par "
         "l'ecriture meme qui semblera le resoudre. Une absence constatee est la seule chose que "
         "personne ne peut remplir apres coup, pourvu qu'on la constate AVANT.")

# fondre ma ligne en double dans D.12, puis la retirer
mienne = [l for l in act['lignes'] if l['cellules'][0] == 'D.10'
          and 'attester' in l['cellules'][1]]
assert len(mienne) == 1, len(mienne)
for l in act['lignes']:
    if l['cellules'][0] == 'D.12':
        l['cellules'][8] += AJOUT
        if not l['cellules'][6]:
            l['cellules'][6] = 'le 12e, pas demain'
act['lignes'].remove(mienne[0])

refs = [l['cellules'][0] for l in act['lignes']]
doubles = {r for r in refs if refs.count(r) > 1}
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('lignes:', len(act['lignes']), '| doublons restants:', doubles or 'aucun')
