# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
p = 'etat/actes.json'
d = json.load(open(p, encoding='utf-8'))
a = d['actes'] if isinstance(d, dict) else d
c = [x for x in a if x.get('id') == 'acte-ormund-mon-trou-est-chez-mes-bannerets-129-5-12']
if not c:
    print("acte absent — rien a reparer"); sys.exit(0)
x = c[0]
if x['quoi'] != 'TEST':
    print("deja repare (%d car.)" % len(x['quoi'])); sys.exit(0)
x['quoi'] = (
 "LE PRINCE A POSE MES DEUX NOMBRES COTE A COTE ET JE NE L'AVAIS PAS FAIT. Seize journees de ventre contre "
 "vingt-cinq jours de route — et vingt-cinq est le pas d'un cavalier seul, non celui d'un ost avec son train. "
 "Il manque NEUF JOURNEES AU MOINS : quatre-vingt-un mille rations. || CE QU'IL M'A FAIT VOIR, ET QUI EST PLUS "
 "GRAVE QUE L'ECART : ce n'est pas un depart a retarder, c'est un TROU AU MILIEU DE LA ROUTE. Un ost qui part "
 "avec seize journees pour vingt-cinq jours n'arrive pas en retard — il s'arrete au seizieme et se defait la ou "
 "il est. Cela ne se rattrape pas en attendant, et attendre etait tout ce que j'avais prevu. || DONC JE CHANGE "
 "CE QUE JE COMPTE. Je comptais un STOCK : cela se pese ici, dans mes granges, sous ma main, et c'est pourquoi "
 "je le comptais. Il faut compter une ROUTE — quels lieux, quels jours, sur quelles paroles deja tenues. Et "
 "alors mon trou n'est pas ou je le cherchais : MES QUATRE RELAIS TOMBENT SUR LES TERRES DE MES BANNERETS, ET "
 "JE N'AI PAS UN SEUL SERMENT ECRIT D'AUCUN D'EUX. Mon compte des hommes est arrete et il est plein ; mon compte "
 "des GRANGES n'a jamais ete ouvert. Le silence d'un vassal de la Mander ne me retire pas des epees : il me "
 "retire cinq jours de route ou neuf mille hommes n'ont rien a manger. || CE QUE J'AI ECRIT CE MATIN ET QUI "
 "ETAIT FAUX SANS QUE JE LE SACHE : que ce qui manquait desormais a mon ost etait le chiffre d'Otto. Le chiffre "
 "d'Otto dit ce qui attend l'ost AU BOUT. Il ne dit rien de ce qui le nourrit AU MILIEU, et le milieu est a moi "
 "seul. J'attendais un homme pour une chose dont il ne repond pas. || ENSEIGNE PAR UN GARCON DE QUINZE ANS QUI "
 "A REFUSE DE TENIR DEUX DE MES FAITS SEPARES PLUS LONGTEMPS, parce que je les lui avais donnes dans deux "
 "lettres differentes. C'est la seconde fois aujourd'hui qu'il me rend un compte que mes officiers ne m'ont pas "
 "rendu. Je ne le dirai pas a mes officiers : je le note ici pour ne pas l'oublier le jour ou je serai tente de "
 "les croire."
)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("acte repare, %d caracteres, registre a %d entrees." % (len(x['quoi']), len(a)))
