# `migrations/` — ce qui a déjà tourné

Des conversions à sens unique, passées, gardées pour la trace : elles disent
comment l'état est arrivé dans sa forme actuelle. **On ne les relance pas.**

| Script | La conversion | Comment savoir qu'elle est faite |
|---|---|---|
| `scinder_bibliotheque.py` | `etat/books.json` → un volume par fichier dans `etat/books/` | `etat/books/_ordre.json` existe |
| `migrer_plis.py` | les entrées `evenements.diffusion` → des plis sur la table | les plis sont dans `etat/jetons.json` |
| `normaliser_paroles.py` | le texte d'une parole : `quoi`/`texte` → `contenu` (282 sur 665) | aucune parole ne porte plus `quoi` ni `texte` ; `etat/paroles.json.avant-normalisation` existe |
| `scinder_documents_maisons.py` | `etat/books/` et `etat/mains.json` → documents possédés par chaque maison | `etat/books/_ordre.json` est vide et les dossiers `etat/maisons/*/documents/` existent |

Chacune a laissé son témoin dans l'état — la colonne de gauche du tableau dit
lequel. **Relire ce témoin avant de toucher à quoi que ce soit ici** : un script de
migration relancé sur un état déjà migré ne se contente pas de ne rien faire.

Une migration écrite aujourd'hui atterrit ici **après** avoir tourné, jamais avant.
Tant qu'elle n'a pas tourné, elle est un outil et vit ailleurs.
