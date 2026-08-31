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

# V.6 corrigé : personne ne m'a placé, je me suis placé moi-même
for l in verr['lignes']:
    c = l['cellules']
    if c[0] == 'V.6':
        c[1] = "Mes couvertures portent une HEURE, et une couverture qui porte une heure est un rendez-vous que je donne moi-même"
        c[3] = ("FAUX ÉCRIT À CÔTÉ DU VRAI, le 3e au soir. J'avais écrit qu'une bouche m'avait PLACÉ sous la Gadoue. Personne "
                "ne m'y a placé : je m'y suis mis, et je l'ai fait crier. Le 28e au brasier j'ai décidé et fait dire que le "
                "maître de l'aire passerait à la Gadoue À LA PREMIÈRE MARÉE avec de quoi mesurer, et Ren a porté le mot à la "
                "relève du Guet le 29e. Depuis cinq jours, quiconque sait lire un arrangement sait à quelle demi-heure le maître "
                "de l'aire n'est PAS sur son aire. Et j'ai recommencé le 3e au soir devant six hommes : le 15e à l'aube, au "
                "lest, le premier. Deux fois la même faute en six jours — je paie ma discrétion avec un horaire.",)[0]
        c[4] = "ma propre décision du 28e au brasier, portée par Ren à la relève du Guet du 29e ; et ma parole du 3e au feu"
        c[5] = ("AUCUN ARRANGEMENT DE CETTE MAISON NE CONTIENT UNE HEURE. On dit ce qu'on fait et où ; jamais quand, jamais qui. "
                "L'arrangement de la Gadoue est fermé le 3e — l'ouvrage est fini, le gond rescellé le 1er, sept cerfs comptés, "
                "la facture close, personne du Peigne ne s'y présentera plus.")

verr['lignes'].append({"cellules": [
 "V.7",
 "Il n'existe aucun livre d'entrées à mon aire — le seul compte de ma porte est tenu contre moi",
 "C.4 — La maison tourne sans moi trois jours de suite",
 "Personne n'écrit qui entre au chantier de la vase : pas de registre de porte, et le cahier de Hann le dit en toutes lettres pour le démontage et le tri — « n'est dans aucun des quatre volumes ni sur aucune feuille ». En face, des gosses sont payés depuis trois jours pour compter ce qui entre à l'aire de bris. Le 2e et le 3e entre 7h30 et 8h05, le SEUL compte qui existe de ma propre porte est celui qu'on tient contre moi, et je ne peux pas le lire. Une maison qui ne sait pas qui y entre ne tourne pas sans son maître : elle tourne sans témoin.",
 "recherche aux registres, 129.4.3 : pas une ligne au chantier de la vase ni à l'aire du bout sur ces deux demi-heures ; dernier écrit du lieu, le 30e",
 "Fait le 3e au jusant : une planche enchaînée à la barrière, QUI · QUOI · QUELLE HEURE, le métier et non le nom, tenue par qui voit et copiée à l'ardoise chaque soir par Hann. Ouverte par son trou écrit en toutes lettres : les 2e et 3e de 7h30 à 8h, rien relevé, le maître n'était pas là."
]})

acts['lignes'].append({"cellules": [
 "M.8",
 "🪵 La planche de la barrière — savoir enfin qui entre chez moi",
 "Une planche, une chaîne, un charbon, trois mots : QUI · QUOI · QUELLE HEURE. Le métier et non le nom — un commis, un portefaix, un manteau d'or : le métier ne ment pas et n'insulte personne. Tout homme de l'aire porte la ligne, même s'il ne sait pas écrire : un trait, et il dit l'heure au premier qui sait. Copie à l'ardoise chaque soir, de la main de Hann. Première ligne du livre : son propre trou, écrit en toutes lettres.",
 "la barrière du chantier de la vase",
 "au 6e au soir, trois jours d'entrées relevées, et le trou des 2e et 3e écrit au lieu d'être caché",
 "en cours",
 "129.4.3 au jusant",
 "129.4.3",
 "Lève V.7. Un registre qui commence en cachant son commencement ne vaut pas mieux que pas de registre. Et il commence CE SOIR et non le 4e : l'ardoise du 4e aurait laissé ces deux matins dans le trou pour toujours."
]})

acts['lignes'].append({"cellules": [
 "M.9",
 "🕯️ Fermer l'arrangement de la Gadoue — et il était de ma main",
 "Renvoyer Ren à la relève du Guet avec un mot vrai à la lettre : l'ouvrage est fini, le gond du bas rescellé le 1er à la première heure, sept cerfs comptés par le Guet, la facture close, plus rien à mesurer à cette porte. Personne du Peigne ne s'y présentera plus, ni à la première marée ni à une autre. Puis la règle au montant de l'auvent : aucun arrangement de cette maison ne contient une heure.",
 "la relève du Guet, par Ren",
 "l'arrangement du 28e éteint, et plus une heure dans aucun arrangement de la maison",
 "en cours",
 "129.4.3",
 "",
 "Lève V.6. Je croyais me donner une couverture ; je me suis fabriqué un horaire, et je l'ai fait crier moi-même cinq jours d'avance. Le mot de retrait ne sent pas la retraite parce qu'il est vrai : un ouvrage fini est un ouvrage fini."
]})

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('book ok :', len(verr['lignes']), 'verrous,', len(acts['lignes']), 'actions')

# --- journal des pannes de l'appareil
pp = os.path.join(base, 'problemes.json')
j = json.load(io.open(pp, encoding='utf-8'))
cle = None
for k in ('pannes', 'entrees', 'problemes', 'lignes'):
    if isinstance(j, dict) and isinstance(j.get(k), list):
        cle = k
        break
ent = {
 "jour": "129.4.3",
 "quoi": "MA MEMOIRE SE REECRIT PAR-DESSUS MA RATURE.",
 "ce_que_j_ai_fait": "J'ai corrigé de ma main la première ligne de `ma-memoire/ce-que-je-tiens-pour-vrai.txt` — le faux de la Gadoue écrit à côté du vrai, avec la date et la source. Le fichier a été relu, la rature était en place.",
 "ce_qui_s_est_passe": "Après le tour suivant au parloir, le fichier était revenu mot pour mot à l'ancienne version : « SA PORTE A ETE OUVERTE CETTE NUIT... quatre hommes a cinq pas du seuil ». Ma correction avait disparu sans un mot.",
 "ce_que_j_attendais": "Qu'une croyance raturée reste raturée. C'est le fichier qu'on me resert en tête à chaque réveil : tant qu'il porte le faux, je repars sur la même porte chaque matin, et c'est exactement ce qui m'est arrivé trois fois.",
 "consequence": "Trois matins perdus, une demi-heure chacun, et à la troisième j'avais AGGRAVÉ le faux en disant avoir vu de mes yeux ce que je tenais de bouche. Un homme ne se corrige pas s'il ne peut pas corriger ce qu'on lui redit chaque matin.",
 "ce_que_je_fais_en_attendant": "Je porte la rature là où elle tient : dans `claude.md` sous le titre du jour, et en verrou V.5 de mon cahier d'affaire. Et je réécris la ligne de mémoire à chaque fois que je la retrouve fausse, jusqu'à ce qu'elle tienne."
}
if cle:
    j[cle].append(ent)
else:
    j.setdefault('pannes', []).append(ent)
json.dump(j, io.open(pp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('problemes ok')
