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
 "V.13",
 "Ces quarante brasses sont le cordage REFUSÉ À LA COURONNE sous son propre sceau — et elles dorment chez moi",
 "C.6 — Je sais qui achète, et par quelle porte l'argent entre",
 "La commande est passée sous le sceau et le filin a été refusé MALGRÉ le sceau : sans cordage, ni levage ni halage devant Sombreval. Ce sont ces brasses-là qui sont sur mon aire, apportées le jour où Sabbe et Ren sont arrivés, données et non achetées, l'estampe du preneur coupée au ras du toron. J'allais les faire recommettre et y faire remettre la marque À MON NOM : j'aurais fait graver mon nom sur le seul objet que ma maison ait refusé à la Couronne, la semaine où la Couronne le cherche. On ne l'affranchit pas en la marquant — on la signe.",
 "la commande sous sceau et le refus malgré le sceau ; la marque d'âme qui rend la corde à la corderie sous la Néra",
 "Rien de tout cela n'est du siège d'un maître de bris : c'est une affaire de sceau. Je prépare, j'écris ce qui manque, et je laisse l'acte entier à celui dont c'est le siège. Ce qui lui est noté au clair : la corde est identifiée et immobile sur mon aire, sa marque de preneur ôtée avant d'y entrer, son fil d'âme la rend à la corderie de la maison — et chaque jour d'attente est un jour où elle reste chez un homme qui n'a rien à voir avec le sceau. Qu'on me dise à qui la remettre, elle part le jour même, sans heure annoncée."
]})

verr['lignes'].append({"cellules": [
 "V.14",
 "Ma règle est plus jeune que mon mou, et une règle qui cache sa date date celui qui l'a écrite",
 "C.4 — La maison tourne sans moi trois jours de suite",
 "La règle du cordage — tout filin s'ouvre à la main avant d'être mis en prise — est vraie et elle sauvera un dos. Mais cette corde a été ouverte AVANT que la règle existe : qui reconstruit les dates trouve un mou antérieur à la ligne qui l'autorise. J'ai ouvert le livre de la barrière par son trou, en toutes lettres, et je n'ai pas appliqué le même à mon propre montant.",
 "l'ordre des dates : la corde ouverte à la chandelle du 3e, la règle écrite après",
 "Fait : la règle est datée au montant — ÉCRITE LE 3e AU SOIR — et porte dessous, de la même main, que LE PREMIER FILIN A ÉTÉ OUVERT AVANT ELLE."
]})

for l in acts['lignes']:
    c = l['cellules']
    if c[0] == 'M.16':
        c[1] = "🪢 Une déclaration de provenance — ni leur perte à réclamer, ni ma question"
        c[2] = ("RETIRÉ : ni recommettre, ni marque à mon nom, ni sortie à la première heure. La corde ne bouge pas et ne se "
                "nettoie pas ; elle reste intacte et portée sur la planche de la barrière comme tout ce qui est sur l'aire. "
                "À la place, ce qui est de mon métier et n'accuse personne : une DÉCLARATION DE PROVENANCE — les mesures, les "
                "marques, la date d'entrée, le mode d'entrée (donnée, non achetée), et en toutes lettres CE QUE JE NE SAIS PAS, "
                "d'où elle vient avant mon aire. Trois copies : une clouée au montant, une gardée sur l'aire, une portée "
                "ouverte à la corderie. Ils y liront leur fil sans que je le leur reproche.")
        c[4] = "trois copies datées, et la corde toujours à sa place, décrite, immobile, sans une marque neuve dessus"
        c[6] = "129.4.4"
        c[8] = ("Deux pièges évités le 3e au soir. UN : faire recommettre et remettre leur marque à mon nom ne nettoie pas le "
                "titre — ça met MON nom dessus le jour même où sa provenance devient une question, et c'est du cordage refusé "
                "à la Couronne sous le sceau (V.13). DEUX : arriver avec leur perte a une seconde lecture gratuite — ou bien "
                "on nous a volés, ou bien TU NOUS ACCUSES DE L'AVOIR FOURNIE — et je n'ai aucune explication à donner de "
                "comment leur corde marquée est arrivée chez moi qui ne soit pas un nom. Une déclaration ne réclame rien et "
                "n'accuse personne : elle date.")
    if c[0] == 'M.17':
        c[2] = (c[2] + " || ET LA RÈGLE PORTE SA PROPRE DATE ET SON TROU : « ÉCRITE LE 3e AU SOIR ; LE PREMIER FILIN A ÉTÉ "
                "OUVERT AVANT ELLE. » Sans ça, la règle date celui qui l'a écrite.")
        c[8] = (c[8] + " || Et AUCUNE HEURE nulle part : j'avais annoncé le maître et le second sortant à la première heure "
                "par la rue — un arrangement avec une heure, dit devant témoins, qui vide l'aire de ses deux têtes au moment "
                "où quatre bras désœuvrés y arrivent. C'était la Gadoue mot pour mot, cinq jours plus tard. Rien ne part à une "
                "heure dite, et Hann ne quitte pas l'aire le même jour que moi.")

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')
