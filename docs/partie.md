# Le conseil de guerre — l'écran de la partie

Note de conception de l'onglet « Le conseil » (`ecrans/modules/partie.js`). Les
règles du jeu, elles, vivent dans [`scripts/agents/prompts/mj-partie.md`](../scripts/agents/prompts/mj-partie.md)
et ne se changent pas ici. Le livre de règles complet, aligné sur le greffe,
est [`regles-partie.md`](regles-partie.md).

## Pourquoi des cartes, et pas une carte

La partie ne se joue pas sur une géographie : un lieu n'y décide de rien, il est
une mention au pied d'une pièce. Ce qui décide, c'est **ce que l'autre camp tient
contre nous** et **ce qu'on a de libre pour y répondre**. L'écran montre donc des
FRONTS — un par obstacle adverse — et un DECK toujours visible, et rien d'autre.

## Les sept cartes

| Signe | Carte | Ce que c'est | Où elle se tient |
|---|---|---|---|
| 🎯 | état cible | ce qu'on veut voir vrai | la colonne de gauche |
| 🔒 | verrou | ce que l'autre camp tient contre nous | en tête d'un front |
| 🗝️ | clef | ce qu'on a posé contre un verrou | sous lui, dans la pile |
| ❓ | question | ce qu'un conseiller demande avant d'exécuter | posée sur la clef qu'elle suspend |
| ⚔️ | action | ce qui a été fait, et par qui | sous la clef |
| 📦 | pièce | ce qu'on engage — 🐉 ⛵ ⚔️ 💰 👤 🏰 en sous-signe | le deck, ou empilée sous une clef |
| 💥 | frappe | ce qui vient sur une de nos pièces | son propre front |

**Ces mots ne sont pas choisis ici : ce sont ceux de l'échiquier**
([`echiquier.md`](echiquier.md)), donc ceux des cahiers d'affaire, de la
criticité et des registres que les hommes tiennent eux-mêmes. Le conseil en
avait forgé d'autres — dessein, obstacle, ordre, geste — **sur les mêmes
emojis**, si bien que 🗝️ voulait dire deux choses à deux onglets d'écart. Un
« ordre » ne désignait rien : c'était « clef » traduit du français vers le
français. Ce qui reste banni de l'écran, c'est la tuyauterie du greffier — gel,
deck, tour —, jamais un mot que la reine emploie.

Une carte a une seule anatomie : le signe en coin, un titre, une phrase, un pied
(à gauche qui la tient ou d'où elle vient, à droite son état).

## L'état se lit à la forme

nette = libre · empilée sous un front = posée · pointillée « dans 4 j » = en route ·
grisée « se remet » = gelée après un retrait ou une frappe · barrée = perdue. Sur
un ordre, un ruban : ✅ tient · ❓ suspendu · ⏳ prêt dans N jours · ⚠️ sans ressource.
**Aucun compteur, aucun numéro de tour** : les délais sont dits en jours du monde.

## Le brouillard — et pourquoi il ne s'applique PAS ici

**Décidé le 3e jour de la 9e lune, et c'est une exception assumée à la règle
cardinale de [`../CLAUDE.md`](../CLAUDE.md) « Vérité vs connaissance ».**

Le brouillard reste entier dans la CHRONIQUE : ce que le joueur apprend lui
arrive par des gens, avec le délai de la route et la déformation de la source —
un capitaine qui n'ose pas dire le chiffre des pertes, une rumeur qui enfle,
un compte arrondi en faveur de celui qui le donne. Rien de cela ne change.

**Mais le plateau n'est pas dans la fiction.** C'est l'abstraction que le MJ et
le joueur partagent pour jouer la partie, au même titre qu'un échiquier — et
aux échecs on voit les pièces d'en face. La v0 ne servait l'adversaire que par
ce qu'il avait posé contre nous ; à l'usage, l'adversaire jouait donc des coups
que personne ne voyait jamais et le plateau ne bougeait pas d'un tour à
l'autre. **Ce n'est pas de la tension, c'est un solitaire contre un processus
caché** — le brouillard n'a d'intérêt que là où l'ignorance est elle-même une
information et où l'on peut payer pour la lever ; il n'y avait ici ni l'un ni
l'autre.

La position complète est donc servie, les deux camps, pièces engagées ou non.

## Ce qui a changé depuis la dernière fois

Le jsonl est append-only, donc chaque coup porte un numéro qui ne recule
jamais : **un seul entier suffit à dire exactement ce qui est neuf.** Il vit
dans `etat/joueurs/<siège>/partie-<id>.json`, et toute carte touchée par une
ligne postérieure porte `neuf: true`.

Deux règles de tenue, chacune payée par un défaut constaté :

- **Le marque-page n'avance qu'au COUP du joueur**, jamais à la lecture. On a
  agi, donc on a regardé ; entre deux de ses coups, tout ce que l'autre camp a
  fait reste marqué. C'est ce qui évite un bouton « j'ai vu », et ce qui permet
  de revenir après deux jours d'absence et de voir en un regard ce qui a bougé.
- **Sans marque-page, rien n'est neuf.** Une première ouverture ne peut pas
  avoir manqué ce dont elle n'a jamais eu d'avant ; sans cette porte, elle
  marquait les trente-neuf cartes du plateau d'un coup. Ce premier regard POSE
  le marque-page sans rien signaler.

## Où ça vit

| Pièce | Rôle |
|---|---|
| `scripts/noyau/partie_cartes.py` | la vue : fronts, piles, deck, desseins, apparences, brouillard |
| `scripts/noyau/partie_gestes.py` | le geste traduit en coup : la CIBLE dit lequel, les refus rhabillés en clair |
| `scripts/partie.py --cartes [--camp <camp>]` | la même vue en JSON, au terminal (le premier camp de la partie sinon) |
| `serveur/domaine/partie.js` | quelle partie pour cette requête (`?id=`, sinon la plus récente) |
| `serveur/routes/partie.js` | `GET /partie`, `POST /partie/geste`, `POST /partie/jour` |
| `ecrans/modules/partie.js` `.css` | l'échelle « Le conseil » du décor |
| `scripts/tests/test_partie_cartes.py` | le banc de la vue, sur `scripts/tests/donnees/partie-duel.jsonl` |
| `scripts/tests/test_partie_gestes.py` | le banc des gestes, sur une copie jetable du même duel |

## Faire jouer un camp par un homme — essayé, mesuré, retiré

**Le 3e jour de la 9e lune.** On a essayé de faire jouer le camp vert par un
homme réveillé dans un espace de session dédié (`depecher.py --partie`) : sa
manière et les documents de sa maison au système, et pour tout message les
règles du manuel, la position, et la diff depuis son marque-page — **aucun
brief**. Otto Hightower a joué deux fois le même coup, un `justifier` sur la
clé Meleys, avec un argument juste tiré de la position.

**Ce qui l'a fait retirer, c'est le prix.** Premier essai : 347 000 jetons et
302 secondes pour un coup. Après avoir borné ses lectures et posé « tu as dix
secondes pour jouer » : 239 000 jetons et 120 secondes — **pour un coup
rigoureusement identique**, ce qui dit assez que les quatre minutes de lecture
n'achetaient rien. À quarante coups la partie, c'est dix millions de jetons
pour faire tourner un plateau.

**Et la cause n'est pas la taille de ce qu'on lui donne.** Le prompt entier
pesait 13 000 jetons ; il en a consommé 239 000. Le coût est dans le nombre de
tours d'outils — il TRAVAILLE quand on lui demande de JOUER, et une consigne de
rythme n'a fait que le raccourcir de moitié. Les trois réductions successives
(ses cahiers, `metier.md`, ses amendements de chambre) représentaient à elles
toutes moins de 5 % de sa consommation.

**Ce qu'il faudrait tenter avant de recommencer** : un appel SANS outils, dont
la seule sortie est la ligne de coup en réponse, le MJ l'écrivant au greffe.
C'est le seul levier de l'ordre de grandeur, et il coûte à l'homme de ne plus
appeler le script lui-même.

D'ici là, **le camp vert est joué par le MJ** : il tient par défaut sans appel, et l'on ne dépêche une tête verte
que pour un coup qui n'est pas « tenir ».

## Le geste (v1)

**Un seul geste, toujours le même : on prend une carte et on la pose sur une
autre.** Ce que ça VEUT DIRE, c'est la carte du dessous qui le dit — l'écran ne
connaît aucun nom de coup, il envoie « j'ai posé ceci sur cela » et
`partie_gestes.py` traduit :

| Ce qu'on pose | Sur quoi | Ce que le greffe écrit |
|---|---|---|
| une pièce 📦 | un obstacle 🔒 d'en face | `lever` — un ordre neuf, dont le titre est au joueur |
| une pièce 📦 | un obstacle 🔒 déjà tenu par un de nos ordres | `rearmer` — on renforce, on n'ouvre pas un doublon |
| une pièce 📦 | un de nos ordres 🗝️ | `rearmer` |
| une pièce 📦 | une frappe 💥 d'en face | `bloquer` — on couvre la pièce visée |
| une carte à nous | le deck | `retirer` — et ses pièces se remettent quatre jours |
| — | « Le jour passe » | `tour`, par l'arbitre |

Trois signes portent la règle, et il n'y en a pas un quatrième : ce qu'on peut
**prendre** se soulève au survol ; une carte en main **allume** ce qu'elle peut
atteindre et éteint le reste ; ce qui est **sous le curseur** s'épaissit. Un
dessein ne s'allume jamais — on ne tient pas un dessein avec un dragon, on lève
ce qui s'y oppose. C'est comme ça que la règle s'apprend, sans avoir à la lire.

**Un refus n'est jamais un silence.** Il revient en une phrase sous la barre, et
ses ids sont rhabillés de leurs titres : « ser Steffon Darklyn déjà engagée par
*Ser Steffon fait ouvrir la porte des Dieux* », jamais `steffon-darklyn déjà
engagée par n-steffon-darklyn-v-portes`. Le contrôle « un coup par camp et par
tour » reste **gradué** : le second coup passe et se dit, il ne se bloque pas.

## Ce que la v1 ne fait pas

**Rien n'écrit dans `etat/`.** Le seul fichier qui s'allonge est
`etat/parties/<id>.jsonl`, en append, par le greffier — qui vérifie d'abord. Ce
qu'un coup change dans le monde reste au MJ, qui l'applique par
`partie.py --ecritures`.

Cinq coups restent hors de l'écran : `viser` (poser un dessein), `demander` une
pièce, `detruire`, `justifier` et tout ce qui est `arbitrer`. Ils se jouent à la
ligne, par le MJ. La raison est la même pour les cinq : ils n'ont pas de geste
naturel sur un plateau de cartes, et leur donner un bouton ferait un menu — ce
qu'on s'interdit partout ailleurs.
