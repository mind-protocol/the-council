# -*- coding: utf-8 -*-
import json, io, os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(base, 'books', 'affaire-marlo-vasse.json')
d = json.load(io.open(p, encoding='utf-8'))

verr = acts = buts = None
for t in d['tables']:
    if 'Verrous' in t['titre']:
        verr = t
    if t['titre'].endswith('Actions'):
        acts = t
    if 'Ce que je veux' in t['titre']:
        buts = t

for l in verr['lignes']:
    c = l['cellules']
    if c[0] == 'V.8':
        c[5] = ("LEVÉ le 3e au soir, et pas comme je le croyais. Sirel Quintaine avait recompté avant moi et m'a écrit le même "
                "soir : elle ne réclame pas les quatre-vingt-cinq cerfs en or. Elle prend à la place ma main et mon jour au bas "
                "de sa feuille de prix — une feuille que deux mains signent devient un usage de la Néra, une feuille tenue seule "
                "reste le tarif d'une prêteuse. J'ai dit oui, à trois conditions qui ne lui coûtent rien : une unité vérifiable "
                "seul par ligne (la brasse, jamais le rouleau) ; LA DATE DU COMPTE et non la date de la feuille en tête ; et "
                "sous la ligne du rouleau, la place d'une seconde longueur mesurée par une autre main. La dette reste écrite : "
                "je la paie en encre, pas en or, et c'est une dette quand même.")
    if c[0] == 'V.10':
        c[3] = (c[3] + " || ET LE NOM N'EXISTE PAS À TROUVER : leur seule ligne connue, celle du 22, porte une destination "
                "fausse que le sergent de la porte de Fer ne sait pas attribuer. Ils achètent le bois sans nom et reçoivent des "
                "lances sous un faux destinataire. Sirel Quintaine me l'écrit tout net : l'absence de nom EST ce qu'ils "
                "achètent, cinq jours de plus n'y feront rien.")
        c[5] = ("Je cesse de payer pour un nom que personne ne vend. Ce qu'il me faut n'est pas leur nom, c'est LEUR COMPTE : "
                "quarante bras, deux galères et une quille achètent du bois et paient comptant. Sirel a porté son tarif à leur "
                "grille et s'engage par écrit — tout bois du lot qui y part, part À MON PRIX ET SOUS MON NOM, son cinquième "
                "reste un cinquième. Je leur fais porter un devis VRAI, daté du jour du compte, copie gardée sur l'aire, et pas "
                "une pièce de plus que ce qui sera sur l'aire ce matin-là.")

for l in buts['lignes']:
    c = l['cellules']
    if c[0] == 'C.6':
        c[2] = ("Deux mains me paient et je n'ai juré à aucune. JE RENONCE AU NOM et je change de preuve : le chantier du bout "
                "achète l'absence de nom, c'est son commerce, et personne ne me le vendra. Ce que je veux désormais est ce qui "
                "se vérifie : par où leur cordage descend — une seule corderie entre les deux bouts de ce bord d'eau, et c'est "
                "la nôtre — et ce que ma propre aussière porte estampé sur son toron.")
        c[3] = ("un compte de quinzaine obtenu de ma corderie partenaire sans avoir prononcé un nom ; et la marque de l'aussière "
                "lue, écrite sur la planchette, avec l'endroit où elle a été coupée")

acts['lignes'].append({"cellules": [
 "M.12",
 "🖋️ Signer la feuille de prix de la Néra — mes quatre-vingt-cinq cerfs payés en encre",
 "Recevoir Sirel Quintaine sous l'auvent, faire l'addition devant moi, et signer de ma main et de mon jour au bas de sa feuille. Trois conditions, aucune ne lui coûte un sou : UNE — chaque ligne porte une unité qu'un homme vérifie seul, le bordé à la brasse (41 sous) et jamais au rouleau, la journée d'homme en sous. DEUX — en tête de feuille : toute ligne porte LA DATE DU COMPTE et non la date de la feuille ; si les deux diffèrent, on recompte ou on écrit pourquoi. TROIS — sous la ligne du rouleau, la place d'une seconde longueur mesurée par une autre main. Ses deux fautes du jour restent datées dessus, et j'écris les miennes à côté.",
 "sous l'auvent du chantier de la vase",
 "deux mains et deux jours au bas de la même feuille, et un bordé vendu à la brasse par une bouche qui n'est pas la mienne",
 "à faire",
 "129.4.4",
 "",
 "Lève V.8 sans sortir un sou. Mon total du 25e est antérieur au sien du 3e et elle me le reconnaît par écrit : le barème n'est plus dans deux têtes, il devient un usage. Et la règle de la date du compte, qui est née de ma propre faute d'aujourd'hui, vaudra à elle seule mes quatre-vingt-cinq cerfs pour le premier qui la lira."
]})

acts['lignes'].append({"cellules": [
 "M.13",
 "📐 Un devis VRAI porté à la grille du chantier du bout",
 "Douze membrures — dix saines de portée au-delà de quatre pas, deux roussies au pied — et un rouleau de vingt-six brasses, au barème signé : cent quarante-trois cerfs. Daté DU JOUR DU COMPTE, recompté le matin même, copie gardée sur l'aire avant qu'il sorte, et pas une pièce de plus que ce qui est sur l'aire ce matin-là. Porté à la grille derrière les entrepôts à sel, où le tarif de Sirel est déjà passé — à mon prix et sous mon nom, son cinquième reste un cinquième.",
 "la grille du chantier du bout, derrière les entrepôts à sel",
 "un devis sorti avec sa copie gardée, et un acheteur qui compte douze membrures là où mon papier en promet douze",
 "à faire",
 "129.4.5",
 "",
 "C'est la première feuille qui sort de chez moi sous les trois règles neuves : copie gardée (M.4), date du compte, unité vérifiable. Ils achètent du bois et paient comptant ; j'ai l'auvent vide le 7e et quatre bras sans ouvrage. Je n'ai pas besoin de savoir qui les paie pour leur vendre douze membrures — il faut seulement que mon compte tombe juste le jour où on le vérifie."
]})

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')
