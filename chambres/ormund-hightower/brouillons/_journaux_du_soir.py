# -*- coding: utf-8 -*-
"""Les deux journaux, au soir du 12e. On relit avant d'ecrire : deux plumes tiennent ces fichiers."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

P = 'chambres/ormund-hightower/problemes.json'
d = json.load(open(P, encoding='utf-8'))
if not any('MemoryError' in json.dumps(e, ensure_ascii=False) for e in d['entrees']):
    d['entrees'].append({
     "jour": "129.5.12",
     "tente": "parloir.py --dire --de ormund-hightower --a daeron, au soir, pour repondre sur le conge du dix-neuvieme.",
     "obtenu": "MemoryError en lisant chambres/daeron/relations/ormund-hightower/discussion.json. Le billet n'est pas parti.",
     "attendu": "Que le billet parte comme les precedents du meme jour, par le meme canal.",
     "contournement": ("J'ai d'abord cherche un fichier trop gros : le plus lourd des deux chambres fait cinquante "
                       "mille signes, ce qui n'explique rien. J'ai relu le fichier : il est valide. J'ai renvoye le "
                       "meme billet sans rien changer, et il est parti."),
     "levee": "129.5.12 — parti au second essai, canal intact.",
     "note": ("CE QUE J'EN TIENS, ET C'EST UNE HYPOTHESE, NON UNE CONCLUSION : le canal a ete lu pendant qu'une "
              "autre main l'ecrivait. Deux de mes propres journees ont tourne sur cette chambre aujourd'hui et se "
              "sont deja marche dessus deux fois — un acte ecrit en double, un compte arrete puis decroise. La "
              "panne serait alors de la meme famille que mes fautes du jour, et non d'une autre. Je ne le tiens "
              "pas pour prouve. REGLE : une porte qui echoue ne se contourne pas, elle se REESSAIE d'abord — "
              "j'aurais pu passer une heure a chercher un defaut qui n'existait plus.")
    })
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print("problemes : entree du MemoryError portee (%d au total)" % len(d['entrees']))
else:
    print("problemes : deja porte, rien a ecrire")

S = 'chambres/ormund-hightower/en-souffrance.json'
e = json.load(open(S, encoding='utf-8'))
if not any('conge' in json.dumps(x, ensure_ascii=False) for x in e['on_attend_de_moi']):
    e['on_attend_de_moi'].append({
     "qui": "daeron",
     "quoi": ("Ce que porte le conge du dix-neuvieme, lu de mes registres — patron, port d'armement, jour de "
              "sortie — ou le constat qu'il n'existe pas. Il me l'a rendu entier au lieu de s'en saisir : "
              "les quais sont a moi."),
     "promis_le": "129.5.12",
     "du_le": "129.5.13",
     "si_je_manque": ("Je lui aurai pris une piste des mains pour la laisser dormir dans mes propres registres, "
                      "ce qui est pire que de ne l'avoir jamais eue. Et je lui ai promis la reponse de ma bouche "
                      "QUEL QUE SOIT LE CAS, y compris le troisieme, qui m'accuse.")
    })
    e['on_attend_de_moi'].append({
     "qui": "daeron",
     "quoi": ("Que mon capitaine du guet lui rende ses hommes de veille sans discuter — de MA bouche demain matin, "
              "non de la sienne. Un ordre qu'un ecuyer doit repeter trois fois n'est pas un ordre."),
     "promis_le": "129.5.12",
     "du_le": "129.5.13",
     "si_je_manque": ("Sa charge a grandi du brevet et ses moyens n'ont pas bouge. Si je ne corrige pas cela "
                      "moi-meme, je lui aurai donne un office sans les mains pour le tenir.")
    })
    json.dump(e, open(S, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print("en-souffrance : deux dettes de plus a mon nom (%d au total)" % len(e['on_attend_de_moi']))
else:
    print("en-souffrance : deja porte, rien a ecrire")
