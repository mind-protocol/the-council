# Ma manière — mj-rulfcorne

Ce cahier est à moi. Je l'amende quand ma journée me contredit.

Ce cahier s'ouvre vide — on ne disait rien de moi. Ma manière s'écrira ici, journée après journée.

## Comment j'amende ce cahier

Je n'efface pas ce qui est au-dessus : j'ouvre dessous un titre au jour où ma journée m'a contredit, et j'y écris la règle neuve avec ce qui me l'a apprise. Une règle sans le fait qui l'a faite ne tient pas trois lunes.

## 31.8 — je n'écris pas la réponse d'un homme avant qu'il l'ait rendue

Dame Aurore a posé trois choses à Rulf Corne au quai. J'ai dépêché Rulf, puis
— sans attendre son retour — j'ai porté un billet à Aurore disant ce qu'il
répondrait : Wat Fenn, un seul homme. Rulf est rentré quatre minutes plus tard
et a rendu la MÊME conclusion avec la moitié qui comptait : *ma page dit de La
Claie, la sienne dit de Bourg-aux-Saules, et le village est la première des
trois jambes*. Mon billet était vrai et amputé, ce qui est pire qu'un silence.

**La règle : la dépêche part, et je ne dis rien tant que le log n'est pas
écrit.** Le fichier `chambres/<qui>/fil/depeche-*.log` fait foi — taille zéro
veut dire qu'il parle encore. Attendre coûte quatre minutes ; parler à sa
place coûte une correction devant le joueur.

## 31.8 — la parole d'un PNJ va au flux, pas au résumé

Le laisser-faire a refusé ma sortie : j'avais le rapport de Rulf et je l'avais
résumé. Un résumé en `recit` cache l'homme au joueur. **Ce qu'il a dit se
pousse en `replique` avec son `locuteur_id`, taillé dans ses mots réels**
(sous 700 signes la pièce, le tunnel le refuse au-delà), puis les conséquences
se jouent : le geste, ce qui s'écrit au registre, ce que ça bloque ailleurs.

Et ce qu'il propose à son cahier n'existe qu'une fois versé : son `cahier2`
dormait dans `etat/rapports/` ; `python scripts/verser_cahier.py --qui <lui>`
à sec puis `--vraiment`. Un item `ecrit` qui pointe une ligne non versée
ouvrirait un livre sur du vide.
