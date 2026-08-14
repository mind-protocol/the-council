# Les fils — ce qui court, et qui tient la plume dessus

Un **fil** est une affaire en cours qui porte un nom d'homme et une échéance. Il vit dans
`etat/joueurs/<personnage_id>/fils.json` — donc **par siège**, comme la table de guerre et les
croyances : les fils de la reine ne sont pas ceux d'Aurore, et aucun des deux ne voit ceux de
l'autre.

Le fil ne remplace ni `evenements.json` (le programme daté qui dit *quand* la chose tombe), ni
`objectifs.json` (les desseins du joueur, ce qu'il s'est engagé à faire), ni les registres de
`books.json` (où l'affaire est écrite pour de bon). Il ne porte qu'une chose, celle qui manquait :
**qui tient la plume sur cette affaire — le joueur, ou l'homme sur qui elle est tombée.**

## Le format

```json
{
  "_lisez_moi": "…",
  "fils": [
    {
      "id": "fil-quatre-sceaux",
      "titre": "Les quatre sceaux à poser",
      "detail": "murailles, relèves, nouvelles, bardesse",
      "sur": "gerardys",
      "echeance": { "annee": 129, "lune": 3, "jour": 30, "minute": 720 },
      "mode": "delegue",
      "statut": "en-cours",
      "remonte_si": ["parole", "cout", "froisse", "contredit"],
      "depuis": { "annee": 129, "lune": 3, "jour": 30, "minute": 560 },
      "dernier": "Datée de sa main à 9h20, devant la table."
    }
  ]
}
```

- `titre` — **ce qui se passe, et ce qu'on essaie d'obtenir**, dans la même phrase, séparés par un
  tiret. « Les quatre sceaux » ne se décide pas : on ne sait ni ce qui cloche ni ce qu'on veut.
  « Quatre charges tiennent sans sceau — les sceller avant midi » se décide. La règle vaut pour le
  rail comme pour le CLI : un titre qui ne nomme pas la difficulté ET la sortie est un titre qu'il
  faudra rouvrir pour comprendre, et le rail existe précisément pour ne pas avoir à le faire.
- `detail` — ce qui pèse et qu'on ne peut pas mettre dans le titre : le chiffre, la borne écrite,
  qui l'a dit. Deux lignes au plus, sous le titre, en marge.
- `sur` — l'id du personnage sur qui l'affaire est tombée. **Un fil sans `sur` ne se délègue pas** :
  il s'affiche « sans nom » et revient à la main du joueur. C'est le quatrième temps de la reine,
  rendu visible.
- `mode` — `joue` (le joueur le tient : ça se joue en scène, battement par battement) ou `delegue`
  (l'homme le tient : ça tourne hors champ et revient en UNE LIGNE au passé). Défaut : `joue`.
- `statut` — `en-cours` · `clos` · `perdu`. Un fil clos sort du rail au prochain chargement.
- `remonte_si` — les seules conditions qui autorisent un fil délégué à frapper. Voir plus bas.
- `dernier` — la dernière ligne rendue au passé, telle que le joueur l'a apprise. C'est ce qu'il lit
  sous le titre quand il survole.

## Ce que le mode change, et ce qu'il ne change pas

**Il ne change jamais le calcul.** La mesure avance pareil, l'échéance tombe pareil, le
`programme` de `evenements.json` se produit pareil. Le mode ne décide que de **par où ça passe** :

| | `joue` | `delegue` |
|---|---|---|
| Où ça se résout | en scène, devant le joueur | hors champ, dans la session de l'homme |
| Ce que le joueur voit | des répliques, des gestes, une bifurcation | une ligne au passé, déjà faite |
| Qui tranche | le joueur | l'homme, **selon SA tête** |
| Quand il reprend la main | toujours | seulement si `remonte_si` s'arme |

Le prix du `delegue` est écrit dans le manuel et il n'est pas négociable : **le délégataire peut mal
faire.** Il tranche selon sa tête, pas celle du joueur. Un mandat mal donné produit des décisions
qu'on n'aurait pas prises — c'est le sujet, pas un bug.

## La porte de sortie — les quatre conditions, et pas une de plus

Un fil délégué ne remonte au joueur **que** si l'une de ces quatre conditions est remplie :

- `parole` — la chose engage la parole du joueur (un serment, une promesse, une signature).
- `cout` — elle coûte un homme ou de l'or qu'on n'a pas.
- `froisse` — elle froisse quelqu'un de **nommé**.
- `contredit` — elle contredit un ordre antérieur du joueur.

Hors de ces quatre, elle est **déjà faite quand le joueur l'apprend**. Sans ce filtre, on récupère
tout et l'on n'a rien gagné : c'est la seule pièce de ce dispositif qui décide s'il sert à quelque
chose.

Quand la condition s'arme, le fil ne remonte **pas** dans le rail : il remonte **dans le fil de
scène**, en `demande`, dans la bouche de l'homme, avec son échéance et son coût — la forme que la
reine a imposée le 27e. Le rail est le tableau ; la scène reste la scène.

## Comment on bascule

**En scène, d'abord.** « Ser Robert, les murs sont à vous » EST la bascule : on écrit le mandat dans
les `intentions` du délégataire, et l'on passe le fil en `delegue`. Le rail ne fait que refléter ce
qui s'est dit à la table.

**Au rail, ensuite.** Un clic sur l'interrupteur POSTe `{type:"fil", fil_id, mode}` dans l'inbox du
siège, et le serveur écrit le mode dans `fils.json` sur-le-champ. Le MJ le voit à son tour de jeu et
en tire les conséquences : mandat écrit ou repris, et la scène qui va avec. **Le clic ne joue rien
tout seul** — il dit une intention, comme tout ce qui part de la barre.

Côté MJ : `python scripts/fils.py --qui <siege>` pour lire, `--poser`, `--mode`, `--clore` pour
écrire. Sans argument, il liste les fils de tous les sièges avec leur mode et leur retard.

## Ce qu'on n'écrit pas

Un fil par affaire que le joueur pourrait vouloir reprendre en main — pas un par tâche. Le grain
d'un château où il n'ira pas, la paie des palefreniers : ce sont des mains
(`docs/mains.md`), pas des fils. Le test avant d'en écrire un : *le joueur voudrait-il, un jour,
tenir la plume là-dessus lui-même ?* Si la réponse est non, c'est une main.
