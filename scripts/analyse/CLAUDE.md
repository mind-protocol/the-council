# `analyse/` — mesurer à froid, et les bancs d'essai

On ne joue pas ici. Ces scripts LISENT l'état et rendent un chiffre, un rapport ou
une simulation ; aucun n'écrit dans `etat/`. On les sort quand on doute d'un
dispositif, pas au tour de jeu.

| Script | Ce qu'il mesure |
|---|---|
| `bilan.py` | six chiffres, le même jour de la semaine prochaine — l'écart du plan |
| `mesurer.py` | la part des répliques du jour sans trace d'aucune pensée. Un seul chiffre, et c'est voulu |
| `parvenir.py` | est-ce que ça va atteindre le joueur ? à quel point ? quand ? |
| `croisement.py` | où et quand deux camps se frôlent, et de quelle taille |
| `croise.js` | ce qui parvient à un siège LÀ OÙ IL EST, sans qu'il ait marché |
| `verif_plan.js` | les plans de château, mesurés : deux noms qui se marchent dessus |
| `exporter_aurore.py` | tout ce qui touche un personnage, en `.txt` dans `export/` |
| `scorer_activation_hightower.py` | la cadence d'activation d'une maison |
| `chercher_activation_hightower.py` | cherche les paramètres, en lecture seule |
| `simuler_reveil_maisons.py` | combien de tours pour réveiller les grandes maisons |

**Un banc rejoue le vrai code, il ne le réécrit pas.** `simuler_reveil_maisons.py`
rejoue EXACTEMENT l'élection de `boucle_activation.cycle` — même diffusion
d'importance, même énergie, mêmes polarités — mais n'appelle aucun modèle et
n'écrit rien. Un banc qui réimplémente la mécanique mesure sa copie, pas le jeu.

**Un compteur d'occurrences n'est pas une mesure.** `mesurer.py` a été taillé de
six chiffres à un seul : les cinq autres comptaient des lignes sans savoir ce
qu'elles valaient. Avant d'ajouter un chiffre ici, dire ce qu'il ferait changer.

`bilan.py` est le seul du dossier inscrit au registre des rapporteurs
(`../noyau/rapporteurs.py`, tous les 14 jours) : son chemin y est écrit en dur.
