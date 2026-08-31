# `figures/` — ce que le mestre dessine pour y voir clair

Des SVG, sortis sur la sortie standard, à rediriger dans `ecrans/dessins/`. Rien
n'est écrit dans `etat/` : ces scripts LISENT et dessinent.

| Script | La figure | La question à laquelle elle répond |
|---|---|---|
| `figures.py roue` | la roue des journées | qui a du temps, et quand |
| `figures.py bannieres` | le rôle des bannières | qui tient quoi |
| `figure_forces.py` | des colonnes d'osts, de bêtes et de coques | combien contre combien |
| `nappe.py` | un SVG par affaire, depuis les registres | comment les pièces tiennent |

**La contrainte de forme, et elle n'est pas décorative.** Ce qui n'existe pas en
129 AC, ce n'est pas le diagramme : c'est l'abstraction fléchée. Les figures de
pensée de l'époque ont quatre formes et pas une de plus — l'ARBRE, la ROUE, les
COLONNES, la liste indentée. Une nouvelle figure prend l'une des quatre, ou ce
n'est pas une figure du mestre.

**Pas de fichier de nappe.** Chaque pièce existe déjà une fois, dans son registre
par type. Un `etat/nappe.json` qui reporterait les mêmes numéros serait une seconde
vérité — et deux vérités divergent. `nappe.py` dessine depuis les registres, à
chaque fois.
