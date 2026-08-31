# -*- coding: utf-8 -*-
import json, io, os

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'books', 'affaire-marlo-vasse.json')
d = json.load(io.open(p, encoding='utf-8'))

verr = None
acts = None
for t in d['tables']:
    if 'Verrous' in t['titre']:
        verr = t
    if t['titre'].endswith('Actions'):
        acts = t

verr['lignes'].append({"cellules": [
 "V.5",
 "Un fait FAUX est en tête de ma propre mémoire et me relance chaque matin sur la même porte",
 "M.3 — Savoir qui a ouvert la Gadoue la nuit du 2e au 3e",
 "La Gadoue n'a jamais été forcée. Le gond du bas a été rescellé par MES deux hommes le 1er à la première heure, sept cerfs comptés par le Guet ; pas d'éclats, pas de corps, pas de lanterne. J'ai porté cette nouvelle trois matins, je me suis rétracté par écrit au milieu, et je suis revenu une troisième fois EN L'AGGRAVANT — la lanterne que je tenais de bouche, je disais l'avoir vue de mes yeux. La ligne est en tête de `ma-memoire/ce-que-je-tiens-pour-vrai.txt` : chaque réveil me la resert comme un fait, et je repars. Trois matins de mon temps, et mon arbitre a posé la borne : il ne répondra pas une quatrième fois.",
 "trois arbitrages du 3e sur la même porte, avec ma rétractation écrite au milieu ; le gond rescellé le 1er, sept cerfs au compte du Guet",
 "Fait : le faux est raturé et écrit à côté du vrai dans ma mémoire, le 3e. Une croyance qu'on ne rature pas dans le fichier où on la relit n'est pas corrigée, elle est seulement contredite."
]})

verr['lignes'].append({"cellules": [
 "V.6",
 "La nouvelle ne touche aucun livre : elle ne m'a pas renseigné, elle m'a placé",
 "C.6 — Je sais qui achète, et par quelle porte l'argent entre",
 "Aucun écrit de la ville ne porte cette porte forcée. Une nouvelle qui ne touche aucun livre a été portée par une bouche qui sait comment j'écris — donc quelqu'un de près. Et son seul effet réel est d'avoir mis le maître de l'aire SOUS UNE PORTE, seul, trois matins de suite, à la même demi-heure : le 2e de 7h33 à 8h03, et c'est au registre. Pendant ce temps l'aire est sans moi. Une histoire qui n'apprend rien mais qui place un homme à heure fixe n'est pas une nouvelle, c'est un rendez-vous pris à ma place.",
 "l'absence — cherchée du matin du 2e au jusant du 3e : ni acte, ni parole, ni rapport ne place un homme, un gosse, une heure auprès de moi ; le dernier écrit qui me concerne est le mien",
 "Savoir ce que les registres portent au chantier de la vase dans CETTE demi-heure-là, le 2e et le 3e. Le renseignement n'est pas dans la porte, il est dans ce qui se passe pendant que je n'y suis pas."
]})

for l in acts['lignes']:
    c = l['cellules']
    if c[0] == 'M.3':
        c[1] = "🚪 La Gadoue n'a pas été ouverte — savoir qui m'y envoie"
        c[2] = ("CLOSE PAR LE FAUX. Il n'y a pas de porte forcée : le gond du bas a été rescellé par mes deux hommes le 1er à "
                "la première heure, sept cerfs comptés par le Guet, et les dégâts que j'allais compter de mes pieds étaient ma "
                "propre facture. Je n'y retourne pas une quatrième fois. Ce qui reste ouvert n'est plus la porte, c'est la "
                "bouche : une nouvelle qui ne touche aucun livre, portée par quelqu'un qui sait comment j'écris, et dont le "
                "seul effet est de me tenir hors de mon aire à heure fixe trois matins de suite.")
        c[4] = "le faux raturé à côté du vrai dans ma mémoire, et ce que les registres portent AU CHANTIER pendant la demi-heure où j'étais sous la porte"
        c[5] = "faite"
        c[8] = ("Faite le 3e, et par le contraire de ce que j'y cherchais. V.5 et V.6 en sortent. Waltyr Poix ne sert plus à "
                "rien ici : on ne demande pas le prix d'une porte qui n'a pas bougé. Les trois pistes écrites que je laissais "
                "de côté restent, elles : la troupe des Deux Frères sous un titre réécrit par-dessus une couronne, les gosses "
                "payés depuis trois jours pour compter ce qui entre à l'aire — et celle qui me les signale est celle qui les "
                "tient —, et les trois métiers au comptoir de Mag qui demandent qui paie en pièces neuves. Ces trois-là "
                "touchent du papier ; la porte, non.")

acts['lignes'].append({"cellules": [
 "M.7",
 "🕰️ Mettre mes deux règles face à face avant qu'elles se cognent",
 "Hann a juré devant les six, à la pointe du jour, qu'il ne redirait plus un chiffre sans dire l'heure où il l'a relevé — et il l'a inaugurée en annonçant à voix haute les 990 sous de la caisse. Ma règle à moi, écrite au montant de l'auvent, dit que le seuil s'abaisse à l'ardoise et que l'ardoise fait foi : écrit, pas crié. Les deux réparent la même faute par les deux bouts. Je les rapproche moi-même, devant lui, sans le reprendre : SON heure entre dans MON ardoise. Toute somme portée à l'ardoise porte désormais l'heure du relevé, et rien de tout cela ne se dit debout sur l'aire.",
 "sous l'auvent, avec Hann",
 "une seule règle sur le montant, avec l'heure dedans, et plus un chiffre de caisse prononcé à voix haute",
 "à faire",
 "129.4.4",
 "",
 "Une règle jurée devant six hommes pèse plus lourd qu'une règle qu'on lit en marchant : je ne la casse pas, je l'avale. Et je ne le reprends pas devant les six — la sienne est bonne, c'est la mienne qui était muette sur l'heure."
]})

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')
