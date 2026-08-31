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

for l in verr['lignes']:
    c = l['cellules']
    if c[0] == 'V.9':
        c[3] = (c[3] + " || LU LE 3e AU SOIR, à douze pas de mon feu : L'ESTAMPE A ÉTÉ COUPÉE au ras du départ du toron, là "
                "où c'est écrit. Mes quarante brasses viennent d'une plus grande longueur et l'extrémité qui nommait le preneur "
                "a été ôtée AVANT d'arriver chez moi. Ce n'est pas une corde trouvée, c'est une corde nettoyée. Mais la maison "
                "double sa marque et celui qui a coupé l'ignorait : LE FIL DE COULEUR COURT DANS L'ÂME, INTACT — la marque de "
                "la corderie sous la Néra, celle de ma propre maison, entre mon aire et les entrepôts à sel.")
        c[5] = ("Je ne tiens pas un nom, je tiens la preuve qu'un nom a été retiré et l'endroit où il était écrit. Et je "
                "n'irai pas demander qui est parti avant son quinzième jour : cette question n'apprend rien sur le moment et "
                "tout plus tard — on y répond sans y penser et l'on s'en souvient le jour où le nom vaut quelque chose. Je "
                "n'achèterais pas le silence, j'achèterais un délai au prix d'un aveu. J'y vais avec LEUR PERTE : leur marque "
                "coupée sur leur propre corde. Ils chercheront eux-mêmes, avec plus d'entrain que moi, et me devront la réponse."
                )

verr['lignes'].append({"cellules": [
 "V.12",
 "La corde ouverte reste molle, et Hann vient de donner à Sabbe la raison d'aller la reprendre en main",
 "C.6 — Je sais qui achète, et par quelle porte l'argent entre",
 "Un filin commis dont on écarte les torons à la main garde le mou à cet endroit, et ça ne se rattrape pas en le roulant. J'ai ouvert l'aussière cette nuit. Or Hann a raturé le soir même, devant témoins — devant Sabbe ET devant Ren —, la dette de ce filin sur les gages de Sabbe : vingt-deux cerfs ramenés à neuf journées. Sabbe a donc toutes les raisons d'aller reprendre cette corde en main demain, et il trouvera le mou à l'endroit exact où l'estampe manque.",
 "le mou au départ du toron, et la rature des gages faite devant six hommes quelques heures avant que j'ouvre la corde",
 "Faire du mou une RÈGLE DE MAISON et non un secret : tout cordage qui entre sur cette aire est ouvert à la main avant d'être mis en prise ou prisé — torons écartés sur trois brasses au départ, l'âme regardée, le mou refait au commettage. C'est vrai, c'est du métier, ça sauvera un dos avant la fin du mois, et ça se dit sans le mot « je ». Hann la passe demain sur les trois filins du dépôt, dans l'ordre où ils sont rangés, celui-ci compris."
]})

acts['lignes'].append({"cellules": [
 "M.16",
 "🪢 Porter la corde à la corderie — leur perte, pas ma question",
 "Poser l'aussière sur leur table, montrer l'estampe coupée au ras du toron et leur fil de couleur intact dessous, dire d'où elle vient et quel jour elle est entrée sur l'aire, et repartir. Ne demander NI un nom, NI qui est parti avant son quinzième jour. Quelqu'un fait circuler de la corde de la maison sous leur marque avec le nom du preneur ôté : une corderie dont la marque se coupe ne vend plus un contrat à personne. Le tort est le leur, l'enquête sera la leur, et la réponse me sera portée pour que je n'aille pas la chercher ailleurs.",
 "la corderie sous la Néra",
 "une réponse rapportée sans que j'aie prononcé un nom ni une date de départ",
 "à faire",
 "129.4.4",
 "",
 "Remplace la demande de compte que je comptais faire, et la raison est de mon arbitre : demander qui est parti avant le quinzième jour n'apprend rien à personne sur le moment et tout plus tard. Un homme qui vient PRENDRE un renseignement laisse une trace de ce qu'il cherche ; un homme qui vient RENDRE une perte laisse une trace de ce qu'il a rendu."
]})

acts['lignes'].append({"cellules": [
 "M.17",
 "🧵 La règle du cordage — tout filin s'ouvre à la main avant d'être mis en prise",
 "Écrite au montant de l'auvent avec les autres, et SANS LE MOT « JE ». Tout cordage qui entre sur cette aire est ouvert à la main avant d'être mis en prise ou prisé : torons écartés sur trois brasses au départ, l'âme regardée, le mou refait au commettage. Un filin qui porte un homme se vérifie dedans et non dehors — une aussière neuve d'aspect peut être roussie à l'âme, et personne ne le voit jusqu'à ce qu'elle lâche sous une membrure. Hann la passe demain sur les trois filins du dépôt, dans l'ordre où ils sont rangés.",
 "au montant de l'auvent, puis le dépôt",
 "trois filins ouverts et notés, et le mou de l'aussière devenu un ouvrage de maison au lieu d'une fouille de nuit",
 "à faire",
 "129.4.4",
 "",
 "Lève V.12. La règle est vraie et elle sauvera un dos ; c'est aussi ce qui rend ordinaire la place que j'ai ouverte cette nuit. Une règle vraie qui me protège moi tout seul se dit sans le mot « je » — je donne la règle, jamais la place que j'y prends."
]})

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')
