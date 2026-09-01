# -*- coding: utf-8 -*-
import json, os
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

p = 'books/affaire-daeron.json'
d = json.load(open(p, encoding='utf-8'))
act = [t for t in d['tables'] if 'Actions' in t['titre']][0]

seen = {}
renames = []
for l in act['lignes']:
    c = l['cellules']
    ref = c[0]
    if ref in seen:
        nouveau = 'D.12' if c[1].startswith('Ouvrir le conge') else 'D.13'
        renames.append((ref, nouveau, c[1][:44]))
        c[0] = nouveau
    else:
        seen[ref] = True
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for a, b, t in renames:
    print('renumerote', a, '->', b, '|', t)

pp = 'problemes.json'
pr = json.load(open(pp, encoding='utf-8'))
pr.setdefault('entrees', [])
pr['entrees'].append({
    "date": "129.5.12",
    "tente": "Tenir mon volume d'affaires au long d'une meme journee, en y revenant plusieurs fois.",
    "la_machine": ("Deux references portees en double dans « Actions » : D.6 sur « faire crier ce que la cloche veut dire » ET sur "
                   "« ouvrir le conge de Villevieille du 19e » ; D.8 sur « rendre les trois nombres » ET sur « refaire les comptes "
                   "de vivres ». Aucune erreur n'a ete levee, rien n'a proteste."),
    "j_attendais": "Qu'un numero deja pris me soit refuse, comme une case deja remplie refuse une seconde main.",
    "corrige": "Renumerotees D.12 et D.13 le 12e, les premieres venues gardant leur nom. Aucun texte perdu.",
    "ce_que_j_en_retiens": ("C'est la faute meme contre laquelle mon volume m'avertit en tete : une ligne decalee d'un cran loge son "
                            "etat dans une autre colonne, et l'affaire entiere passe pour vide. Deux lignes sous un seul nom font "
                            "pire — l'une repond pour l'autre. J'ai lu que D.8 etait FAITE et cru un instant avoir rendu mes trois "
                            "nombres, qui ne sont pas meme mesures. REGLE : avant d'ajouter une ligne, relire les numeros deja pris.")
})
pr['entrees'].append({
    "date": "129.5.12",
    "tente": "Ecrire a lord Ormund par le parloir, le matin.",
    "la_machine": ("La lettre a ete portee au canal, lue et repondue — et le meme soir il ecrit n'avoir rien recu, et redemande de "
                   "vive voix ce que la lettre disait deja."),
    "j_attendais": "Qu'une chose lue et repondue soit tenue pour arrivee.",
    "corrige": "",
    "ce_que_j_en_retiens": ("Je ne recommence pas la lettre : je vais le lui dire a table, ce qu'il m'a demande deux fois. Mais je "
                            "garde l'ironie pour ma charge — ON M'A DONNE A MESURER LE DELAI ENTRE L'HOMME QUI VOIT ET LA CLOCHE QUI "
                            "SONNE, et j'ai passe la journee dans une maison ou un pli lu ne compte pas comme un pli arrive. La "
                            "roukerie garde une nouvelle quatre jours ; ma lettre du matin n'a pas passe jusqu'au soir. C'est la meme "
                            "maladie a trois etages, et c'est elle, mon vrai sujet.")
})
pr['entrees'].append({
    "date": "129.5.12",
    "tente": "Ecrire mon script de tenue de volume par un heredoc, au shell.",
    "la_machine": ("Le shell est mort en cours d'ecriture (« fork: retry: Resource temporarily unavailable », « cygheap read copy "
                   "failed »), laissant le fichier a ZERO octet. Python l'a ensuite execute sans broncher et sans rien dire : "
                   "un fichier vide s'execute parfaitement."),
    "j_attendais": "Qu'un travail qui n'a rien touche ne se presente pas comme un travail accompli.",
    "corrige": "Reecrit par un autre moyen, puis verifie sur le disque et non sur le rapport.",
    "ce_que_j_en_retiens": ("Une commande qui ne se plaint pas n'a rien prouve. J'ai failli tenir pour tenus mes journaux et mes "
                            "renumerotations parce que rien n'avait crie. RELIRE LE DISQUE, non le rapport — c'est le meme principe "
                            "que mon refus de prendre un nombre sur parole, applique a la machine.")
})
json.dump(pr, open(pp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('problemes:', len(pr['entrees']))

ep = 'en-souffrance.json'
e = json.load(open(ep, encoding='utf-8'))
e['j_attends'].append({
    "qui": "otto",
    "quoi": ("Que la ligne du 19e au bureau des roles de Port-Real soit LUE, COPIEE MOT POUR MOT ET PARAPHEE telle qu'elle est "
             "aujourd'hui, par un officier de son choix, la copie portant son jour."),
    "demande_le": "129.5.12",
    "relance_le": "129.5.14",
    "note": ("Relance a DEUX jours et non trois : ce fil court contre une main, non contre un homme. Une case vide dans ce registre "
             "APPELLE, et Ollo en a vu deux remplies cette lune par une main sans office. Une ligne lue aujourd'hui est une preuve ; "
             "la meme dans huit jours ne vaut rien, et nul n'aura commis de faute visible. Je n'ai nomme aucun commis et j'ai demande "
             "qu'on n'en interroge aucun. Je n'ai rien dit des affaires de lord Ormund — ni les mille quartiers, ni Brix, ni Quill, "
             "ni le Guichet Vert, ni les quatre jours de la roukerie : cela est a lui et il ecrit lui-meme. Je ne depense pas ce "
             "qu'on m'a confie, fut-ce aupres de mon grand-pere.")
})
for f in e.get('fils_clos', []):
    if f.get('qui') == 'ollo-marran':
        f['comment'] += (" — AJOUT du 12e au soir : le fil reste clos de ma part, mais il a offert DE LUI-MEME de regarder les roles "
                         "de SORTIE du 19 au 23 quand il le pourra sans qu'on lui demande pourquoi, et de me dire aussi s'il n'y "
                         "trouve rien. Ce n'est pas une dette, c'est un don : je ne le relancerai pas. Sa condition, tenue : ne rien "
                         "lui offrir — ni or, ni protection, ni papier a son nom, ni gage date d'avant.")
json.dump(e, open(ep, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('j_attends:', len(e['j_attends']), '| on_attend_de_moi:', len(e['on_attend_de_moi']))
