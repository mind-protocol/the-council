# -*- coding: utf-8 -*-
"""Le 12e au soir. Deux ecritures :
   1. je ferme dans problemes.json l'entree du dedoublement, en disant ce qui l'a levee ;
   2. j'ajoute a mon volume la page de l'ordre du guet et du protocole de l'essai,
      ECRITE AVANT DE MESURER, pour que je ne puisse pas arranger le nombre apres."""
import json

# --- 1. fermer l'entree ouverte
p = 'C:/Users/reyno/le-conseil2/chambres/daeron/problemes.json'
d = json.load(open(p, encoding='utf-8'))
for e in d['entrees']:
    if 'Deux de moi' in e.get('quoi', ''):
        e['leve_le'] = '129.5.12'
        e['leve_par'] = (
            "Dedoublement fait de ma main le 12e au soir. Le volume portait deux fois "
            "C.4, C.5, C.6 et six actions en double (mes P.11 a P.16 refaisaient D.2, D.3, "
            "D.5, D.6). J'ai garde les lignes D.* de la premiere main, jete mes doublons, "
            "et renumerote en D.8 et D.9 les deux seules qu'elle n'avait pas : rendre les "
            "trois nombres a lord Ormund avant que l'ost s'ebranle, et les quatre jours de "
            "la roukerie. Verifie ensuite : aucune ligne decalee, aucun numero en double. "
            "LA LECON, et elle vaut au-dela de l'appareil : avant d'ecrire dans un cahier "
            "que je crois a moi seul, je le relis. Un volume qui dit deux fois la meme "
            "chose ne dit plus rien du tout, et c'est ecrit en tete de ce volume-ci."
        )
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('problemes.json : entree du dedoublement fermee')

# --- 2. la page de l'ordre et de l'essai
p = 'C:/Users/reyno/le-conseil2/chambres/daeron/books/affaire-daeron.json'
d = json.load(open(p, encoding='utf-8'))
titre = "L'ordre du guet du ciel, et l'essai de nuit"
d['pages'] = [pg for pg in d['pages'] if pg.get('titre') != titre]
d['pages'].append({
 "titre": titre,
 "texte": (
  "Ecrit le 12e de la 5e lune, AVANT d'avoir rien mesure. C'est le sens de cette page : "
  "un homme qui ecrit sa methode apres coup arrange son nombre sans meme s'en apercevoir. "
  "Je pose ici comment je compterai, pendant que j'ignore encore ce que je vais trouver.\n\n"
  "CE QUE JE TIENS, ET DE QUI. Lord Ormund m'a donne le guet du ciel de Villevieille le 12e : "
  "les vigies des tours et du Phare me rendent compte a moi, la cloche de mer sonne a mon "
  "ordre et non au sien, je choisis mes hommes de veille. Le capitaine du guet me rend les "
  "hommes qu'il me faut pour l'essai de nuit sans que j'aie a demander. Les cinq cents hommes "
  "du guet, ceux des murs, sont hors des neuf mille et le restent quand l'ost marchera : "
  "il me l'a ecrit pour que je ne l'apprenne pas le matin du depart.\n\n"
  "L'ORDRE AUX TOURS, en mots qu'un homme de veille peut repeter sans se tromper :\n"
  "— On ne guette pas la mer. On guette LE CIEL, et on guette la nuit autant que le jour.\n"
  "— Qui voit ne descend pas et n'envoie personne : il crie, et le suivant crie apres lui, "
  "jusqu'a la cloche. Un homme qui descend d'une tour pour porter la nouvelle a perdu la "
  "ville pendant qu'il descendait.\n"
  "— On sonne sur ce qu'on a VU, jamais sur ce qu'on a cru comprendre. Une fausse cloche "
  "coute une nuit ; une cloche tue coute la ville. Aucun homme ne sera repris pour avoir "
  "sonne sur rien : je le dis d'avance et je le tiendrai.\n"
  "— Ce que la veille a vu se rend a MOI au matin, de la main de celui qui l'a vu, et ne "
  "passe par personne. Tant que je ne sais pas ce que valent les quatre jours de la roukerie, "
  "je ne fais pas porter mes veilles par une voie qui a garde une nouvelle quatre jours.\n\n"
  "L'ESSAI, ET SON ORDRE — LA CRIEE D'ABORD.\n"
  "1. Faire crier sur les places et aux septuaires ce que la cloche de mer veut dire et ou "
  "l'on va quand elle sonne. Puis la meme criee huit jours apres : ce qu'on entend une fois, "
  "personne ne l'a entendu.\n"
  "2. SEULEMENT ENSUITE, l'essai de nuit. Sans prevenir les vigies de l'heure — un delai "
  "annonce n'est pas un delai, c'est une parade.\n"
  "3. Montre en main, de l'instant ou l'homme VOIT a l'instant ou la cloche SONNE. Je tiens "
  "la montre moi-meme. Je ne prends le nombre de personne.\n"
  "4. Le troisieme nombre ne se mesure pas dans une tour mais dans la rue : combien de gens "
  "ordinaires, interroges hors du chateau, savent ou aller quand elle sonne. Je compte ceux "
  "qui savent, non ceux qui disent avoir compris.\n\n"
  "CE QUE JE RENDRAI. Les trois nombres ensemble, avec le jour et l'heure de chaque mesure, "
  "avant que l'ost s'ebranle. Bons ou mauvais, sans rien arrondir en ma faveur. S'il en manque "
  "un, je le rends manquant et je dis pourquoi, plutot que de le combler. Lord Ormund me l'a "
  "ecrit et je le recopie ici pour ne pas l'oublier quand le nombre sera laid : "
  "« je n'ai pas demande a etre rassure, j'ai demande a etre couvert. »"
 )
})
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('volume : page ajoutee —', titre)
print('pages du volume :', [pg['titre'] for pg in d['pages']])
