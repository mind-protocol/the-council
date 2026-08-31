# -*- coding: utf-8 -*-
import json, io, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
p = 'books/affaire-tobb.json'
d = json.load(io.open(p, encoding='utf-8'))

JOUR = "4e de la 4e lune"
maj = {
    "P.5": ("faite", "Fait le 4e, et par le bon verbe : un TENTER, pas un DEMANDER, "
            "parce que l'issue ne dependait pas de moi. Le verdict m'a rendu le fait "
            "que je n'avais pas — Doss Marran est au bourg, et il est le porteur de "
            "dame Alys. Ma question du 3e etait restee sans reponse six fois ; celle-ci "
            "a rendu plus que ce que je demandais."),
    "P.6": ("faite", "Le TENTER du 4e au matin : aborder dame Alys au bourg avec le nom "
            "ecrit sur une ardoise plutot que prononce, et l'effacer du pouce devant "
            "elle. Le geste est passe. Ce qu'il a change n'est pas ce que j'attendais : "
            "je n'ai pas eu besoin de la question."),
    "P.7": ("faite", "Trois billets le 4e, a trois personnes qui ne sont pas mon arbitre : "
            "dame Aurore (le nom qu'elle m'avait cede n'etait a prendre pour personne), "
            "dame Alys (l'aveu que je lorgnais son porteur, alors que le taire ne me "
            "coutait rien), le maitre des roles (mon chiffre du 3e etait faux de "
            "quatorze jours, et c'est moi qui l'ai trouve)."),
    "T.1": ("faite", "La feuille est ouverte a la voute du role, en retard et dit comme "
            "tel, avec TROIS colonnes et non deux. Corrigee le 4e sur deux points "
            "graves : la route du sel n'est pas une roue (six passages, un dernier), "
            "et le plancher est le 27e et non le 28e. Un dos de feuille ouvert : "
            "'ce qu'on lui prend deja', avec le mot JAMBES ou BIENS contre chaque nom."),
    "T.2": ("faite", "Rendu le 3e a ONZE jours — faux. REPRIS de ma main le 4e avant "
            "qu'il en fasse quoi que ce soit : ZERO COUREUR DU J-8 AU J+16, vingt-cinq "
            "jours, le jour d'entree dedans. Rendu en J-n et sans l'ancre, en deux "
            "branches, sans dire lequel des cahiers cede : ce n'est pas mon office."),
    "T.3": ("faite", "Rendu ZERO, avec la raison. Je cherchais deux noms le 2e, j'en "
            "rendais un le 3e, je rends zero le 4e — et chaque fois avec une raison de "
            "plus. Un compte qui descend de deux a un a zero n'est pas un compte qui se "
            "degrade : c'est un compte qui devient vrai. Le bourg ne donne aucun nom, "
            "et il faut chercher hors du bourg."),
}

n = 0
for t in d.get('tables', []):
    if 'Actions' not in t.get('titre', ''):
        continue
    cols = t['colonnes']
    i_ref = 0
    i_etat = cols.index("⏳ État") if "⏳ État" in cols else None
    i_fait = cols.index("📅 Jour fait") if "📅 Jour fait" in cols else None
    i_note = cols.index("📝 Note") if "📝 Note" in cols else None
    for lg in t['lignes']:
        c = lg['cellules']
        ref = c[i_ref]
        if ref in maj:
            etat, note = maj[ref]
            if i_etat is not None:
                c[i_etat] = etat
            if i_fait is not None:
                c[i_fait] = JOUR
            if i_note is not None:
                c[i_note] = note
            n += 1

json.dump(d, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('actions closes :', n)
