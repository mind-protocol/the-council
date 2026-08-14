# -*- coding: utf-8 -*-
"""Le conflit qui tombe AUJOURD'HUI : le vers porteur de 41223 est la chanson que je lache ce soir."""
import json, shutil, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = 'etat/books.json'
shutil.copy(P, P + '.avant-verrou-maree')
books = json.load(open(P, encoding='utf-8'))
livre = next(e for e in books if e['id'] == 'affaire-role-des-bouches')

def tab(t):
    return next(x for x in livre['tables'] if x['titre'] == t)

ver = tab("\U0001f512 Verrous")
act = tab("⚔️ Actions")
ver['lignes'] = [l for l in ver['lignes'] if l['cellules'][0].replace('*','').strip() != '66003']
act['lignes'] = [l for l in act['lignes'] if l['cellules'][0].replace('*','').strip() != '66023']

ver['lignes'].insert(2, {'cellules': [
 '**66003**',
 "⏳ Le vers qui doit porter les ordres est la chanson que je lâche ce soir — **et après ce soir il ne m'appartient plus**",
 '66000',
 "⚡ 41223 doit coudre quatre versions sur « le vers de *La marée*, **déjà repris au port** », et son vers ordinaire est arrêté au mot **« le jour tient »**. Elle est **à faire**, due J−26, sans date au calendrier. Or **LA MARÉE N'ATTEND PAS SA GRÂCE sort ce soir**, aux cuisines d'abord puis au bourg, comme la reine l'a voulu. Une chanson lâchée est lâchée : \U0001f5dd️ 6010 l'écrit — *on ne la corrige plus, aucun sceau ne la rattrape*. **Dès demain, c'est le bourg qui aura fixé le vers ordinaire, et non moi.** Si le mot qui sort ce soir n'est pas celui-là, les trois autres versions de 41223 ne seront plus des variantes invisibles : elles seront des fautes qu'on remarque.",
 "⚡ 41223, cellule « Ce qu'on fait » : le vers ordinaire est « le jour tient », et la ligne est à l'état **à faire**. \U0001f5dd️ 6010, cellule du prix : « ON NE LA CORRIGE PLUS ». Et mon intention du jour, portée devant témoins : la marée sort aux cuisines avant la salle.",
 "Le mot **« le jour tient »** est dans la bouche du bourg ce soir, et aucun des trois autres n'a été chanté une seule fois. Alors 41223 garde ses trois versions, et ne coûte plus qu'une demi-journée d'écriture.",
]})

act['lignes'].insert(1, {'cellules': [
 '**66023**',
 "\U0001f30a Fixer le vers ordinaire de *La marée* **avant** de la donner aux cuisines",
 '66010',
 "Une demi-heure, seule, avant de descendre : relire ⚡ 41223, prendre son mot ordinaire — **« le jour tient »** — et le coudre dans le vers de marée de LA MARÉE N'ATTEND PAS SA GRÂCE. Puis chanter **cette version-là et pas une autre**, ce soir et tous les soirs, aux cuisines comme au bourg. Je n'écris rien dans le cahier de mestre Gerardys : je fais seulement en sorte que ce qu'il y a écrit reste vrai demain.",
 'Peyredragon — le bourg, puis les cuisines',
 'O10 — Alys Grive', 'M15',
 "Le texte de la marée dans mon sac ; le mot ordinaire de ⚡ 41223",
 "**Une demi-heure de ma main — zéro dragon** · une fois · engagé le 2e de la 4e lune.\n\nPrix hors monnaie : **le vers ordinaire cesse d'être ordinaire pour moi**, et je ne pourrai plus jamais le changer pour une raison de chant. Une chanson vient de perdre une syllabe au profit d'un ordre.",
 '—',
 "Le mot « le jour tient » repris au bourg dans les trois soirs, et aucune autre version chantée",
 'à faire', '',
 "**C'est le seul de mes conflits qui tombe aujourd'hui** : les autres sont en J−n et le calendrier est à blanc. Dit seul et tout de suite, avant la feuille à deux mains.",
 "**ce soir, avant les cuisines** — 2e de la 4e lune",
]})

json.dump(books, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('pose : verrou 66003 + action 66023')
