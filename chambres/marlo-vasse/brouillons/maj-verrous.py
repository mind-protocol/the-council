# -*- coding: utf-8 -*-
import json, io, os

p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'books', 'affaire-marlo-vasse.json')
d = json.load(io.open(p, encoding='utf-8'))

verrous = {
 "titre": "\U0001f512 Verrous",
 "colonnes": ["\U0001f512 N°", "\U0001f3f7️ Le verrou", "\U0001f3af Ce qu'il bloque",
              "⚠️ Ce qui est vrai aujourd'hui", "\U0001f441️ La preuve",
              "\U0001f5dd️ Ce qui le lèverait"],
 "lignes": [
  {"cellules": [
    "V.1",
    "L'ouvrage s'arrête le 7e, la paie court jusqu'au 14e",
    "C.5 — Les six sont payés jusqu'à la vive-eau du 15e",
    "Hann a mesuré le rebut le 3e au matin : SOIXANTE-TREIZE pièces, dix-huit journées d'homme. Quatre bras les abattent en quatre jours et demi — le 7e au soir l'auvent est vide. Restent huit jours à quatre-vingt-dix sous : SEPT CENT VINGT SOUS de gages pour des mains vides, et défense de descendre la carcasse sous la ligne d'eau. Je comptais l'argent ; le trou n'était pas dans la caisse, il est dans le bois.",
    "la mesure de Hann, 129.4.3 au matin, avant l'arrivée des six",
    "Les trente-deux journées du 7e au 14e vont à l'aire du bout : dévaser, creuser le ber, poser les cales pour la vive-eau du 15e. Le gage dort ou il prépare la coque : c'est le même argent."
  ]},
  {"cellules": [
    "V.2",
    "L'aire du bout n'est pas à moi avant le 6e au soir",
    "M.2 — Une coque sur l'aire à la vive-eau du 15e",
    "Le partage avec Sirel Quintaine — elle la salle de La Gaffe, moi l'aire du bout — n'est confirmé que le 6e au soir. Mes quatre bras y seraient le 7e au matin : UN JOUR de marge, et je lui dois onze dragons, ce qui ne fait pas de moi celui qui pose les conditions.",
    "ce qu'on attend de moi, sans jour : confirmer le partage du 6e au soir",
    "Confirmer le partage AVANT le 6e, par écrit et non de bouche, en rendant une part des onze dragons pour que le oui ne lui coûte rien à dire."
  ]},
  {"cellules": [
    "V.3",
    "Le seuil de deux cerfs ne peut s'exercer qu'une fois",
    "C.4 — La maison tourne sans moi trois jours de suite",
    "Deux cerfs font cent douze sous ; la bourse de la matière en porte cent dix-huit. Hann engage UNE entrée et derrière sa parole il n'y a plus rien. Je lui ai donné la forme d'un pouvoir et la substance d'un achat : à la deuxième entrée il redevient un homme qui vient me demander.",
    "le compte de l'arbitre, 129.4.3 : 112 contre 118",
    "La matière paie la matière : chaque pièce de refente qui sort de l'auvent crédite la bourse de son prix, copie sur l'aire. Le seuil cesse d'être ma bourse et devient un compte qui se remplit tout seul."
  ]},
  {"cellules": [
    "V.4",
    "J'ai dit tout haut l'heure, le lieu, et que j'y serais SEUL",
    "C.6 — Je sais qui achète, et par quelle porte l'argent entre",
    "Devant six hommes : le lest ne s'ouvre qu'à basse mer de vive-eau, et le 15e à l'aube j'y serai le premier. La règle est vraie — un pied et demi d'eau le reste du temps, des outils perdus dans la vase — et c'est ce qui la rend imparable : personne ne pourra me la reprocher, et personne ne l'oubliera. La cadence de Hann est clouée au flanc, du pont au lest, avec la date.",
    "ma propre parole au feu de l'aire, 129.4.3 au soir, six témoins",
    "Le lest ne s'ouvre JAMAIS à un homme seul — règle de sécurité, et Hann est le second nommé pour le 15e. Et ce qui doit être à moi n'y sera plus le jour où on l'ouvrira."
  ]}
 ]
}
d['tables'].insert(1, verrous)

acts = None
for t in d['tables']:
    if t['titre'].endswith('Actions'):
        acts = t

for l in acts['lignes']:
    c = l['cellules']
    if c[0] == 'M.1':
        c[8] = ("Dit sur le billot le 3e. CORRIGÉ le 3e au soir (V.3) : deux cerfs font 112 sous et la bourse en porte 118 "
                "— le seuil ne servait QU'UNE FOIS. Il tient désormais à ce qui sort de l'auvent : la refente vendue "
                "crédite la bourse de la matière, copie sur l'aire le soir même. La bourse ne se mêle jamais à la paie, "
                "sauf le jour où la paie manque : ce jour-là Hann prend dans la matière avant de faire attendre un homme.")
    if c[0] == 'M.2':
        c[2] = ("Reconnaître avant le 15e où la mer pose les coques : trois des quatre dernières sont montées à un jour "
                "de la vive-eau et aucun des quatre volumes ne porte de date de marée. ÊTRE LE PREMIER, ce n'est pas y être "
                "seul à l'aube : c'est que l'aire du bout soit dévasée, le ber creusé et les cales posées quand la coque "
                "cherche où s'échouer. Trente-deux journées de quatre bras, du 7e au 14e — les mêmes qui n'ont plus de bois.")
        c[8] = ("Onze jours. V.1 lui donne ses bras, V.2 lui donne son terrain : sans le partage confirmé avant le 6e, les "
                "quatre bras du 7e n'ont nulle part où aller. Si la coque ne vient pas, la règle de marée reste acquise et "
                "se revend telle quelle : une règle de marée vaut plus longtemps qu'une carcasse.")
    if c[0] == 'M.4':
        c[8] = ("Coût : ce que je note à la chandelle devient lisible par un autre. C'est le prix, et je le paie. "
                "La copie porte DÉSORMAIS UN PRIX : c'est elle qui crédite la bourse de la matière (V.3). Un double sans "
                "prix ne prouve qu'un mouvement ; avec le prix, il tient le seuil de Hann debout.")

acts['lignes'].append({"cellules": [
 "M.5",
 "⛏️ Les trente-deux journées vides portées à l'aire du bout",
 "Du 7e au 14e, les quatre bras ne cherchent plus de bois sous un auvent vide : ils dévasent l'aire du bout, creusent le ber à la ligne de basse mer et posent les cales. Hann tient la feuille des journées, copie sur l'aire chaque soir.",
 "l'aire du bout",
 "au 14e au soir, un ber creusé et calé, et pas un des quatre n'a chômé un jour payé",
 "à faire",
 "129.4.7",
 "",
 "Lève V.1. Sept cent vingt sous de gages cessent d'être une perte et deviennent l'avance de M.2."
]})
acts['lignes'].append({"cellules": [
 "M.6",
 "✍️ Le partage écrit avec Sirel Quintaine, avant le 6e",
 "Ne pas attendre le 6e au soir : lui porter le partage écrit — la salle de La Gaffe à elle, l'aire du bout à moi, bornes et dates — et rendre une part des onze dragons pour que le oui ne lui coûte rien à dire. Un prix, jamais une faveur.",
 "chez Sirel Quintaine",
 "deux exemplaires signés, un sur l'aire, avant le 6e au soir",
 "à faire",
 "129.4.5",
 "",
 "Lève V.2. Je lui dois onze dragons : c'est elle qui pose les conditions tant que je n'ai pas rendu. Rendre une part n'est pas une libéralité, c'est le prix de pouvoir demander."
]})

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', [t['titre'] for t in d['tables']], len(acts['lignes']))
