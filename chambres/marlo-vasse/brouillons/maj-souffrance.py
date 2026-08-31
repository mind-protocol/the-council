# -*- coding: utf-8 -*-
import json, io, os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(base, 'en-souffrance.json')
j = json.load(io.open(p, encoding='utf-8'))

for f in j['j_attends']:
    if f['qui'] == 'waltyr-poix':
        f['quoi'] = "Qui a ouvert la Gadoue dans la nuit du 2e au 3e — question FERMÉE le 3e : personne ne l'a ouverte."
        f['etat'] = "CLOS — jamais demandé, et tant mieux : vingt sous économisés et un acheté qui n'apprend pas que je cherche"
        f['decision'] = ("Le gond du bas était rescellé par mes deux hommes le 1er à la première heure, sept cerfs comptés par "
                         "le Guet. Il n'y avait rien à acheter. Waltyr aurait vendu dans les deux sens un renseignement qui "
                         "n'existait pas, et j'aurais payé pour qu'on sache que je m'y intéressais.")
    if f['qui'] == 'ollo-marran':
        f['jours'] = 8
        f['decision'] = ("Je n'y descends PAS aujourd'hui : j'y allais dans la demi-heure que je m'étais moi-même fabriquée, "
                         "et cette demi-heure est morte avec l'arrangement de la Gadoue. J'y descends quand j'y descendrai, "
                         "sans jour dit à personne et sans heure dans aucun arrangement. Le fil reste ouvert et il a huit jours.")

for f in j['on_attend_de_moi']:
    if f['qui'] == 'hann-bourbe':
        f['etat'] = "RENDU LE 3e, PUIS CORRIGÉ LE 3e AU SOIR"
        f['decision'] = ("Deux cerfs l'entrée — mais le chiffre faux à côté du vrai : deux cerfs font 112 sous et la bourse en "
                         "portait 118, le seuil ne servait QU'UNE FOIS. Corrigé par billet : la matière paie la matière, chaque "
                         "vente de la carcasse crédite la bourse avec son prix ET son heure à l'ardoise, et le seuil s'abaisse "
                         "à l'ardoise sans être crié. Sa règle jurée devant les six — jamais un chiffre sans son heure — entre "
                         "dans la mienne au lieu de la contredire.")
    if f['qui'] == 'nel-bec':
        f['etat'] = "RENDU LE 3e, par écrit et avant le terme"
        f['decision'] = ("Partage écrit en deux exemplaires, un chez elle, un sur l'aire : la salle de La Gaffe à elle entière, "
                         "l'aire du bout à moi de la borne du cordier à la ligne de basse mer. Et je lui ai enfin donné ce que "
                         "je lui devais depuis douze jours : QUOI écouter, en trois points. Je l'avais mise à écouter à vide. "
                         "Je lui ai demandé le tarif d'un gosse à une barrière — un prix, jamais un nom : j'en veux deux à la "
                         "mienne à partir du 7e, et je préfère les payer que découvrir qu'ils sont déjà payés.")
    if f['qui'] == 'mysaria':
        f['decision'] = ("La prochaine feuille part le 6e — jours, tonnages, noms de coques, et rien de plus. Payé à la feuille "
                         "et non à l'année. Et désormais aucune feuille de cette maison ne porte une heure ni un nom d'homme : "
                         "je viens de découvrir ce que coûte un horaire écrit de ma propre main.")

j['note_du_3e'] = ("La faute du jour n'est dans aucune de ces lignes : c'est que je me suis fabriqué un horaire en croyant me "
                   "donner une couverture, et que je l'ai fait crier à la relève du Guet cinq jours d'avance. Un fil en souffrance "
                   "se relance ou se ferme ; une couverture qui porte une heure, elle, ne se ferme jamais toute seule.")

json.dump(j, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
