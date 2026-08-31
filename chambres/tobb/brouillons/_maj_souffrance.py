# -*- coding: utf-8 -*-
import json, io
p = 'C:/Users/reyno/le-conseil2/chambres/tobb/en-souffrance.json'
d = json.load(io.open(p, encoding='utf-8'))

d['j_attends'][0]['quoi'] = (
    "PLUS RIEN SUR CE NOM — fil ferme le 4e. Le fait etait au role, gratis : "
    "Doss Marran, CONDITION LIBRE. Et la question elle-meme frolait la deuxieme "
    "des trois choses interdites a son office : tout ce qui invite a rapporter "
    "son voisin. J'ai retire la question et porte une DECLARATION a la place, "
    "de vive voix, au bourg, le 4e.")
d['j_attends'][0]['relance_prevue'] = (
    "Aucune. Le nouveau mecanisme est ma clef 9014 : je declare la veille le nom "
    "que je vais ecrire, elle ne parle que si elle veut m'arreter, son silence "
    "vaut oui. Rien a attendre d'elle tant que je n'ai pas de nom a declarer — "
    "et je n'en ai plus.")

d['j_attends'][1]['quoi'] = (
    "Deux choses. (1) Quel cahier cede sur les jours a zero jeton — CHIFFRE "
    "CORRIGE LE 4e : ce n'est pas onze jours du J-8 au J+2, c'est VINGT-CINQ, du "
    "J-8 au J+16, parce que la route du sel a six cases et une fin (apres J-14 "
    "rien ne part et rien ne revient). Billet parti le 4e avec la correction et "
    "l'aveu. (2) La LIGNE DE PORTE, qui est a lui : la feuille est ouverte et "
    "ment par le bas sans elle.")

d['on_attend_de_moi'][0]['quoi'] = (
    "34122 lui demandait cinq porteurs nommes. Elle a CEDE Doss Marran le 4e au "
    "matin, pour que je le prenne en jeton.")
d['on_attend_de_moi'][0]['ce_que_je_dois'] = (
    "RENDU le 4e, et a l'envers de ce qu'elle attendait : JE NE LE PRENDS PAS "
    "NON PLUS. Trois raisons, une seule suffirait — il est SAUNIER et ma propre "
    "clef 9010 exclut le sel ; sa bouche porte la parole de dame Alys vers trois "
    "villages depuis le 28e ; et surtout IL NE SAIT PAS CE QU'IL PORTE. On ne "
    "pose pas deux charges sur un homme qui n'a pas vu la premiere. Le bourg "
    "donne ZERO et non un.")
d['on_attend_de_moi'][0]['a_faire'] = (
    "Rien. Elle demandait a savoir le jour ou je le poserais ; je lui ai dit le "
    "jour ou j'y renonce, et c'est le meme jour.")

d['on_attend_de_moi'][1]['ce_que_je_dois'] = (
    "RENDU le 3e, FAUX, et REPRIS de ma main le 4e avant qu'il en fasse quoi que "
    "ce soit. Le vrai chiffre : ZERO COUREUR DE J-8 A J+16, vingt-cinq jours, le "
    "jour d'entree dedans. Mon onze tenait sur une barque qui n'existe pas.")

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
