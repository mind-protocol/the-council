# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
p = 'chambres/ormund-hightower/en-souffrance.json'
d = json.load(open(p, encoding='utf-8'))

if not any(x.get('qui') == 'daeron' for x in d['on_attend_de_moi'] if 'pli' in json.dumps(x, ensure_ascii=False)):
    d['on_attend_de_moi'].append({
     "qui": "daeron",
     "quoi": "Savoir ou se perd un pli entre lui et moi, dans la meme enceinte. Il m'a repondu au matin ; je lui ai ecrit le soir qu'il n'avait pas repondu. Il a porte le delai a SON compte au lieu de me le reprocher : c'est donc a moi de le fermer.",
     "promis_le": "129.5.12",
     "du_le": "129.5.14",
     "si_je_manque": "Je lui aurai donne a mesurer le temps entre l'homme qui voit et la cloche qui sonne, en laissant ouvert le meme trou entre lui et moi. Une chaine qu'on ne mesure pas chez soi ne se mesure nulle part."
    })

if not any(x.get('qui') == 'le bureau des conges de mes quais' for x in d['j_attends']):
    d['j_attends'].append({
     "qui": "le bureau des conges de mes quais",
     "quoi": "La ligne du conge de sortie du 19e de la 3e lune : patron, port d'armement, jour de sortie — copiee et paraphee telle qu'elle est, a poser a cote du role d'entree de la Nera, qui porte SANS NOM AU ROLE.",
     "demande_le": "129.5.12",
     "par": "de mon sceau, a mon propre bureau — la seule piece de cette affaire qui ne depende ni d'Otto, ni de la mer, ni d'un temoin",
     "relance_le": "129.5.14",
     "sans_reponse": "Si mon propre bureau ne me rend pas une ligne de mon propre registre en deux jours, ce n'est plus une affaire de grain : c'est une affaire de maison, et je la traite comme telle."
    })

json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("en-souffrance : %d fils que j'attends, %d que je dois." % (len(d['j_attends']), len(d['on_attend_de_moi'])))
