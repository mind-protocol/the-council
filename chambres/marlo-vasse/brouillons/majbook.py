# -*- coding: utf-8 -*-
import json, io, os
p = os.path.join(os.path.dirname(__file__), '..', 'books', 'affaire-marlo-vasse.json')
b = json.load(io.open(p, encoding='utf-8'))

etats = {
 'P.1': ('faite', '129.4.3', "Lu. Ce qu'on disait de moi : pratique, discret, compte juste. Je tiens les trois — mais la discrétion m'a coûté une feuille et six journées de mon second, et je l'ai écrit sous le titre du jour."),
 'P.2': ('faite', '129.4.3', "Quatre phrases en « je » sous le semé, et trois règles datées du 3e sous leur fait."),
 'P.3': ('faite', '129.4.3', "Proposé au monde par --faire le 3e : les deux bourses dans l'emplanture, l'or vieux de la reine et les pièces neuves du 21e, et pourquoi je ne paie jamais l'aire en neuves."),
 'P.4': ('faite', '129.4.3', "Trois buts posés, chacun avec sa preuve."),
 'P.5': ('faite', '129.4.3', "« Le 3e de la 4e lune » — trois règles, chacune avec le fait qui me l'a apprise : la feuille perdue, la troisième demande de Hann, la fausse monnaie."),
 'P.6': ('faite', '129.4.3', "Mes lignes sous les dix : M.1 à M.4."),
 'P.7': ('faite', '129.4.3', "problemes.json : deux entrées, dont le --tenter cassé à 180 secondes qui sort en code 0. en-souffrance.json : six fils, trois que j'attends, trois qu'on attend de moi."),
 'P.8': ('faite', '129.4.3', "Demandé l'état de ma caisse au 3e, avec sa date. Réponse : 772 sous, 13 cerfs 44, un cerf fait 56 sous — et ma question portait un fait faux que l'arbitre a relevé : les 266 cerfs du lot ne sont jamais rentrés sur l'aire."),
 'P.9': ('faite', '129.4.3', "--faire : la proclamation du seuil de deux cerfs sur le billot du feu, devant les six. --tenter : six cerfs sortis du lest de l'emplanture."),
 'P.10': ('faite', '129.4.3', "Billet à hann-bourbe, le 3e : le chiffre, le mur, et ce que j'ai à corriger dans son compte."),
}

for t in b['tables']:
    if t['titre'] == '⚔️ Actions':
        cols = t['colonnes']
        i_etat, i_fait, i_note = cols.index('⏳ État'), cols.index('📅 Jour fait'), cols.index('📝 Note')
        for l in t['lignes']:
            n = l['cellules'][0]
            if n in etats:
                e, j, note = etats[n]
                l['cellules'][i_etat] = e
                l['cellules'][i_fait] = j
                anc = l['cellules'][i_note]
                l['cellules'][i_note] = (anc + ' || ' if anc else '') + note
        t['lignes'] += [
         {'cellules': ['M.1', "🪙 Tenir le seuil des deux cerfs et le compter",
           "Une ligne par entrée de matière engagée par Hann seul, portée le soir même à l'ardoise de l'aire. Quand la bourse de la matière descend sous deux cerfs, je la remonte ou je retire le seuil tout haut — jamais en silence.",
           "Le chantier de la vase", "l'ardoise de l'aire tient le compte de la bourse de la matière",
           "en cours", "chaque soir jusqu'au 15e", "",
           "Dit sur le billot le 3e. La bourse de la matière ne se mêle jamais à la paie, sauf le jour où la paie manque : ce jour-là Hann prend dans la matière avant de faire attendre un homme."]},
         {'cellules': ['M.2', "🌊 Une coque sur l'aire à la vive-eau du 15e",
           "Reconnaître avant le 15e où la mer pose les coques : trois des quatre dernières sont montées à un jour de la vive-eau et aucun des quatre volumes ne porte de date de marée. Y être le premier.",
           "la grève basse et l'aire du bout", "une coque engagée, écrite, avant le 15e",
           "en cours", "129.4.15", "",
           "Onze jours. Si la coque ne vient pas ou qu'un autre y est avant moi, la règle de marée reste acquise et se revend telle quelle : une règle de marée vaut plus longtemps qu'une carcasse."]},
         {'cellules': ['M.3', "🚪 Savoir qui a ouvert la Gadoue la nuit du 2e au 3e",
           "Compter les dégâts de mes pieds AVANT de payer personne : le gond arraché dit de quel côté on a poussé, donc si c'était pour entrer ou pour sortir. Puis descendre au bureau du port sans dire le nom d'Ollo Marran.",
           "la porte de la Gadoue, puis le bureau du port", "je sais le sens de la poussée, et je n'ai demandé à personne qui pourrait me faire fermer la porte",
           "en cours", "129.4.3 avant la nuit", "",
           "Waltyr Poix est acheté, donc il vend dans les deux sens : il vient en dernier, et je lui demande un prix, jamais un nom."]},
         {'cellules': ['M.4', "📄 Une copie sur l'aire de tout ce qui sort de l'auvent",
           "Rien ne quitte l'auvent avant que l'aire en garde une copie — ardoise ou double de la main de Hann. C'est lui qui l'a demandé et il a raison : sa feuille était bonne, elle est dans un manteau au Crochet et il ne nous en reste pas une ligne.",
           "sous l'auvent", "chaque feuille sortie a son double sur l'aire",
           "en cours", "à partir du 4e", "",
           "Coût : ce que je note à la chandelle devient lisible par un autre. C'est le prix, et je le paie — la discrétion protège un secret, elle ne doit pas manger le registre."]},
        ]
    if t['titre'] == '🎯 Ce que je veux':
        t['lignes'] += [
         {'cellules': ['C.4', "La maison tourne sans moi trois jours de suite",
           "Hann engage, paie et refuse seul sous ses seuils, et personne sur l'aire n'attend une parole de moi pour travailler. Deux seuils dits tout haut : deux cerfs à la sortie depuis le 26e, deux cerfs à l'entrée depuis le 3e.",
           "trois jours d'absence, et à mon retour l'ardoise est tenue et personne n'est parti"]},
         {'cellules': ['C.5', "Les six sont payés jusqu'à la vive-eau du 15e",
           "990 sous de gages du 4e au 14e contre 772 en caisse : 218 sous qui n'existent pas. Ils doivent venir d'ailleurs que du bris, et avant le 12e au soir.",
           "aucun des six n'a attendu sa journée, et la caisse n'est pas tombée à sec"]},
         {'cellules': ['C.6', "Je sais qui achète, et par quelle porte l'argent entre",
           "Deux mains me paient et je n'ai juré à aucune. Je veux le quai par où l'or entre — ou, à défaut, la corde : quarante brasses d'un seul tenant ne se vendent pas à l'étal, il faut un nom au registre pour l'enlever.",
           "un nom de contrat aux corderies du port, et ce nom n'est pas celui de Sabbe"]},
        ]

json.dump(b, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
