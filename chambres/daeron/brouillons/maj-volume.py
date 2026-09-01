# -*- coding: utf-8 -*-
import json
p = 'C:/Users/reyno/le-conseil2/chambres/daeron/books/affaire-daeron.json'
d = json.load(open(p, encoding='utf-8'))
buts = [t for t in d['tables'] if 'veux' in t['titre']][0]
act = [t for t in d['tables'] if 'Actions' in t['titre']][0]

buts['lignes'] += [
 {"cellules": ["C.4", "Le ciel de Villevieille est compté, non promis",
  "Les trois nombres du guet sont mesurés de ma main — les vigies et ce qu'elles voient de nuit ; le délai entre l'homme qui voit et la cloche qui sonne ; ce que la ville comprend quand elle sonne — et rendus à lord Ormund avant que l'ost s'ébranle, bons ou mauvais.",
  "les trois nombres écrits ici avec le jour et l'heure de la mesure, et la réponse de lord Ormund au canal"]},
 {"cellules": ["C.5", "La ville sait lire sa cloche avant qu'elle sonne",
  "Ce que la cloche de mer veut dire est crié sur les places et aux septuaires AVANT le premier essai, puis crié une seconde fois huit jours après. Une cloche qu'on ne sait pas lire jette dix mille âmes dans les rues au lieu de les mettre à l'abri.",
  "deux criées datées portées ici, la seconde huit jours après la première"]},
 {"cellules": ["C.6", "Ce que j'apprends de la coque sans nom, lord Ormund l'a — ou l'inconnu l'a",
  "Ce qu'Ollo Marran répond lui est rendu tel quel. S'il ne répond pas, ou ne sait pas, l'inconnu est écrit et rendu comme inconnu : je ne comble pas un blanc pour faire une réponse.",
  "la réponse d'Ollo, ou l'inconnu écrit, porté au canal de lord Ormund avant le départ de l'ost"]},
]


def maj(ref, etat, jour_fait="", note=None):
    for l in act['lignes']:
        c = l['cellules']
        if c[0] == ref:
            c[5] = etat
            c[7] = jour_fait
            if note is not None:
                c[8] = note
            return
    raise SystemExit('introuvable ' + ref)


maj("P.1", "faite", "12e de la 5e lune")
maj("P.2", "faite", "12e de la 5e lune",
    "Écrit sous « Ce que j'écris de ma main », cinq phrases en « je ». J'ai gardé les puces du haut et je ne les laisse plus parler seules.")
maj("P.3", "faite", "12e de la 5e lune",
    "Cherché, et l'inconnu conservé : AUCUN livre auquel j'ai accès ne porte mon nom ni celui de Tessarion — les seuls « dragons » qu'ils contiennent sont des pièces d'or. Ce que je tiens de ma dragonne, sa jeunesse et qu'elle ne tient pas un ciel entier seule, est ma connaissance et non une source. Lord Ormund l'a portée au registre de Villevieille, datée du 12e, de mes mots et sous sa main : c'est là, désormais, qu'elle est écrite.")
maj("P.4", "faite", "12e de la 5e lune",
    "C.4, C.5, C.6 ci-dessus. Trois, pas dix, et chacun avec la preuve par quoi il se refermera.")
maj("P.5", "faite", "12e de la 5e lune",
    "Titre « ## Le 12e de la 5e lune — ce qui m'a contredit ». La règle neuve : la parole de mon lord est une source comme une autre, et je la compte. Rien effacé au-dessus.")
maj("P.6", "faite", "12e de la 5e lune",
    "P.11 à P.16 ci-dessous : ce dont je réponds vraiment depuis ce matin.")
maj("P.7", "faite", "12e de la 5e lune",
    "Une entrée dans chacun. problemes.json : le contexte 71021 qui ne résout pas et le doublon qu'il a laissé. en-souffrance.json : deux fils que j'attends, deux choses qu'on attend de moi.")
maj("P.8", "faite", "12e de la 5e lune",
    "Deux recherches, deux résultats opposés et tous deux utiles. RIEN sur le ciel de Villevieille : ni toit, ni vigie, ni phare, ni cloche dans aucun livre accessible — ce que lord Ormund m'en disait était donc sa parole, et je le lui ai dit. UNE LIGNE sur ma ville dans « Ce qui est entré par la Néra », de la main d'Ollo Marran, jour 19 : coque sans nom au rôle, venue de Villevieille, non ouverte, deux hommes d'armes à bord, case du destinataire vide.")
maj("P.9", "faite", "12e de la 5e lune",
    "Pris le guet du ciel et répondu avant le terme, sans demander à personne si je le pouvais. J'ai en outre refusé le chiffre qu'on ne m'avait pas donné, et corrigé mon lord sur ce qu'il laissait derrière lui — il l'a fait écrire au registre, daté du 12e.")
maj("P.10", "faite", "12e de la 5e lune",
    "Trois hommes le même jour : lord Ormund (ma réponse), Ollo Marran (la coque du 19e), mestre Norren (les rôles du guet, et les quatre jours de la roukerie).")

act['lignes'] += [
 {"cellules": ["P.11", "Compter les vigies, et ce qu'elles voient de nuit",
  "Le premier des trois nombres. Demander d'abord à mestre Norren s'il existe un rôle écrit des tours et postes qui tiennent la nuit ; s'il n'y en a pas, monter moi-même et compter — quelles tours, combien d'hommes, combien d'heures, et lesquelles voient la mer dans le noir. Lord Ormund m'a donné le capitaine du guet : je ne demande pas les hommes, je les prends.",
  "les tours de Villevieille et le Phare", "un compte de ma main, tour par tour, avec le jour",
  "en cours", "avant que l'ost s'ébranle", "",
  "Demandé à mestre Norren le 12e. Inconnu tant qu'il n'a pas répondu — je ne l'écrirai pas de tête."]},
 {"cellules": ["P.12", "Mesurer le délai entre l'homme qui voit et la cloche qui sonne",
  "Le deuxième nombre, et celui qui vaut la charge. Un essai DE NUIT, montre en main : de l'instant où la vigie voit à l'instant où la cloche de mer sonne. Non ce qu'on espère — ce qu'on aura mesuré.",
  "de la tour à la cloche de mer", "un délai mesuré, de nuit, avec le jour et l'heure",
  "à faire", "avant que l'ost s'ébranle", "",
  "Dépend de P.13 : la criée d'abord, l'essai ensuite, ou l'essai sera une émeute. Lord Ormund m'a averti et il a raison."]},
 {"cellules": ["P.13", "Faire crier ce que la cloche veut dire, avant tout essai",
  "Le troisième nombre n'est pas dans une tour, il est dans la tête des gens. Faire crier sur les places et aux septuaires ce que la cloche de mer veut dire et ce qu'il faut faire quand elle sonne. Puis LA MÊME CRIÉE HUIT JOURS APRÈS : ce qu'on entend une fois, personne ne l'a entendu.",
  "les places et les septuaires de la ville", "deux criées datées, la seconde huit jours après la première",
  "à faire", "avant l'essai de nuit", "",
  "De lord Ormund, et je le tiens pour juste : une cloche que la ville ne sait pas lire jette dix mille âmes dans les rues au lieu de les mettre à l'abri."]},
 {"cellules": ["P.14", "Rendre les trois nombres à lord Ormund avant que l'ost s'ébranle",
  "Les trois ensemble, bons ou mauvais, avec le jour et l'heure de chaque mesure. Ne rien arrondir en ma faveur. S'il en manque un, le rendre manquant et dire pourquoi, plutôt que de le combler.",
  "au canal de lord Ormund", "les trois nombres portés au canal, datés",
  "à faire", "avant que l'ost s'ébranle", "",
  "Il ne m'a pas demandé d'être rassurant : « je n'ai pas demandé à être rassuré, j'ai demandé à être couvert. »"]},
 {"cellules": ["P.15", "Tenir le fil de la coque sans nom",
  "Une seule question au bout, celle que lord Ormund veut : le NOM DU CAPITAINE et le port d'armement de la coque du 19e ; et si elle est ressortie de la Néra, quand et vers où. Rendre à lord Ormund ce qu'Ollo répond, mot pour mot — ou l'inconnu s'il ne répond pas.",
  "canal d'Ollo Marran", "la réponse d'Ollo, ou l'inconnu écrit",
  "en cours", "avant que l'ost s'ébranle", "",
  "Écrit deux fois le 12e : d'abord trois questions, puis une seule pour la rétrécir. Un commis qui tait pourquoi la case est vide dira souvent qui était à la barre."]},
 {"cellules": ["P.16", "Savoir ce que valent les quatre jours de la roukerie",
  "Le corbeau de Sombreval entre à la Citadelle à l'aube du 18e ; la criée publique le 22e. Demandé à mestre Norren : quatre jours, est-ce l'ordinaire ou est-ce long ; par combien de mains passe un pli et qui décide du jour de la criée ; existe-t-il un registre où l'HEURE d'arrivée est portée. Je ne cherche le nom de personne.",
  "canal de mestre Norren", "la réponse du mestre, ou l'inconnu écrit",
  "en cours", "avant que l'ost s'ébranle", "",
  "Ce n'est pas une affaire à côté de ma charge : c'est ma charge à un autre étage. Un signal reçu et non transmis pendant quatre jours est exactement ce que je dois mesurer entre la vigie et la cloche."]},
]

json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('objectifs:', len(buts['lignes']), '| actions:', len(act['lignes']))
for l in act['lignes']:
    print('  ', l['cellules'][0], 'cellules=' + str(len(l['cellules'])), '| etat:', l['cellules'][5])
