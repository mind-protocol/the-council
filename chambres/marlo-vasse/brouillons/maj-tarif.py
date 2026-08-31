# -*- coding: utf-8 -*-
import json, io, os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(base, 'books', 'affaire-marlo-vasse.json')
d = json.load(io.open(p, encoding='utf-8'))

verr = acts = None
for t in d['tables']:
    if 'Verrous' in t['titre']:
        verr = t
    if t['titre'].endswith('Actions'):
        acts = t

verr['lignes'].append({"cellules": [
 "V.15",
 "Mon second vend sans tarif, et ça me coûte plus cher que tous mes trous de caisse",
 "C.4 — La maison tourne sans moi trois jours de suite",
 "Le 27e à la première marée, Hann a vendu neuf cerfs un rouleau qui faisait VINGT-SIX BRASSES au cordeau — deux fiches à une brasse, treize tours, Wat qui l'a roulé ne bronche pas. Au tarif signé, quarante et un sous la brasse, il valait mille soixante-six sous : DIX-NEUF CERFS. Dix cerfs laissés sur le billot en une matinée. Il n'a pas mal vendu contre un tarif : IL N'AVAIT PAS DE TARIF. Et son coût d'étape parlait de seize pour la paire quand elle en valait trente-huit. Un second sans barème ne se trompe pas de prix, il n'en a aucun — et c'est le maître qui le lui doit.",
 "sa mesure au cordeau du 3e au matin, contre le prix encaissé le 27e ; et le tarif Quintaine arrêté et signé du 3e",
 "OUI, donné le 3e au soir : il cloue la feuille de prix sous l'auvent et vend contre elle, à la brasse et jamais au rouleau, chaque pièce écrite avec sa portée. Il ne dit aucun prix — il LIT celui d'un autre, signé et daté, que n'importe qui peut recompter. Trois conditions : la date du compte au-dessus de la date de feuille ; la feuille périmée reste clouée dessous avec le jour où elle a cessé ; et ce qui n'a pas de ligne ne quitte pas l'auvent."
]})

acts['lignes'].append({"cellules": [
 "M.21",
 "📋 Le tarif cloué sous l'auvent — Hann lit un prix au lieu d'en dire un",
 "La feuille de prix Quintaine, signée et datée, clouée sous l'auvent dès demain. Vente à la brasse et jamais au rouleau, chaque pièce écrite avec sa portée. Trois conditions : la DATE DU COMPTE au-dessus de la date de feuille ; quand la suivante arrive, l'ancienne reste clouée dessous avec le jour où elle a cessé — on n'décroche pas un tarif, on l'empile ; et ce qui n'a pas de ligne sur la feuille ne quitte pas l'auvent tant qu'il n'en a pas une.",
 "sous l'auvent du chantier de la vase",
 "une vente faite par Hann seul, contre une ligne écrite, sans qu'il ait prononcé un prix de sa tête",
 "à faire",
 "129.4.4",
 "",
 "Lève V.15 sans un sou. C'est la deuxième fois qu'il le demande par un autre bout, et ma règle dit que je réponds à la deuxième, jamais à la troisième — j'en avais déjà laissé passer une. Et c'est exactement ce que j'ai acheté en signant : une feuille que deux mains signent devient un usage de la Néra, et elle le devient en étant clouée à des aires comme la mienne."
]})

acts['lignes'].append({"cellules": [
 "M.22",
 "📏 La seconde longueur écrite par Hann sur la ligne blanche de Quintaine",
 "La feuille porte sous la ligne du rouleau deux lignes blanches pour une longueur mesurée par une autre main que la sienne ou la mienne. La mesure de Hann du 3e au matin est exactement cela : vingt-six brasses, deux fiches à une brasse, treize tours, relevé au cordeau, Wat témoin. Qu'il l'écrive LUI-MÊME, de sa main, avec l'heure de son relevé comme il l'a juré devant les six.",
 "sous l'auvent, le 5e à la marée du matin",
 "deux longueurs écrites de deux mains sous la ligne du rouleau — un étalon au lieu d'une opinion",
 "à faire",
 "129.4.5",
 "",
 "Deux mesures font un étalon ; une seule fait encore une opinion. Tant que la deuxième ligne est vide, cette page ne sait pas ce qu'est un rouleau — et c'est la ligne de mon second qui le lui apprendra. Il sera là quand je signerai."
]})

for l in acts['lignes']:
    c = l['cellules']
    if c[0] == 'M.5':
        c[8] = (c[8] + " || CORRIGÉ par le compte de Hann le 3e au soir : avec deux bras au halage dès le 4e, le rebut le porte "
                "au 7e et non au 6e. Je prends son chiffre, il est meilleur que le mien. Il répond oui ou non le 6e, et quoi "
                "qu'il dise je ne redemande pas.")
    if c[0] == 'M.16':
        c[2] = (c[2] + " || ET PERSONNE N'Y TOUCHE : ni pour la vendre, ni pour la priser, ni pour la déplacer. La règle du "
                "cordage vaut pour les deux autres filins du dépôt, PAS pour celui-là. Ordre donné à Hann en propres termes.")

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')
