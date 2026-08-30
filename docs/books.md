# Les livres — `etat/books/`

Un **livre** est un OBJET du monde : un registre posé sur une table, un carnet
qu'on porte sous le bras. Il porte du JSON, il se consulte à l'écran sous
l'échelle « Les livres » du décor, et il n'existe QUE s'il est inscrit ici.
Un registre qu'on décrit en scène sans l'écrire dans ce fichier n'a pas été
ouvert : le joueur ne pourra jamais y lire une ligne.

Ce fichier est technique — comme `routines.json`, `presence.json` et
`horloges.json` — et vit donc hors de `docs/schema.md`, qu'on ne modifie
jamais. Le format ci-dessous est celui que lit `ecrans/modules/books/`, et
**lui seul** — `lecture.js` pour la forme d'un volume, `portee.js` pour où il
est et qui l'ouvre. Il est vérifié par `python scripts/tick.py --verifier`.

## Le stockage

Chaque volume vit dans `etat/books/<id>.json`. `etat/books/_ordre.json` est la
liste ordonnée de leurs identifiants et la seule autorité sur l'ordre de
l'étagère. Le nom du fichier et le champ `id` doivent être identiques.

Le vieux tableau `etat/books.json` reste lisible uniquement tant que le
manifeste `_ordre.json` n'existe pas. Dès que ce manifeste est présent, le
dossier est l'unique source de vérité : une copie partielle ou un retour
silencieux au monolithe est interdit.

Un fichier de volume porte un objet, sans tableau englobant :

```json
{
    "id": "registre-des-plis",
    "lieu_id": "peyredragon",
    "salle_id": "table-peinte",
    "titre": "Ce qui est parti depuis la mort du père",
    "sous_titre": "Registre tenu par le mestre Gerardys",
    "type": "registre",
    "colonnes": ["Par quoi", "Où", "Ce qui a été dit"],
    "lignes": [
      { "cellules": ["Lettre", "Rosby", "…"], "note": "Deux plis envoyés." }
    ],
    "pages": ["Du texte suivi, quand le tableau ne suffit pas."]
}
```

## Les clés — il n'y en a pas d'autres

| clé | rôle |
| --- | --- |
| `id` | kebab-case, unique. C'est lui qui permet de remplacer un livre au lieu d'en créer un deuxième. |
| `lieu_id` | le château où il se trouve (`lieux.json`). Obligatoire pour un livre posé. |
| `salle_id` | la salle où il est POSÉ (`ecrans/modules/plans.js`). |
| `acteur_id` | ou la personne qui le PORTE (`personnages.json`). **`salle_id` ou `acteur_id`, jamais les deux.** |
| `boite` | ou le COFFRET où il est rangé (`etat/boites.json`). C'est alors la boîte qui donne la place : le volume n'a ni `salle_id`, ni `acteur_id`, ni `lieu_id`, ni `prive` à lui. Voir « Les boîtes » plus bas. |
| `prive` | `true` : un carnet que son porteur ne montre à personne — seul le joueur qui le porte le voit. **Sans `acteur_id` il ne veut rien dire** : un volume posé n'a pas de porteur, donc pas de propriétaire à qui le réserver. C'est `lecteurs` qu'il lui faut. |
| `tenu_par` | facultatif — la MAIN qui répond du volume (`personnages.json`). Ce n'est pas une place : le cahier ne bouge pas, il reste où sa boîte le pose. Ça ne ferme rien non plus — qui peut l'ouvrir reste l'affaire de `lecteurs` et du lieu. Ça RANGE : la carte du coffret groupe ses volumes par main, dans l'ordre où les mains paraissent, et ce qui n'a pas de `tenu_par` tombe sous « Sur personne » à la fin — une affaire ouverte que personne ne porte se voit alors sans qu'on la cherche. |
| `lecteurs` | [] les seuls qui puissent l'ouvrir (`personnages.json`). Ça ne DONNE rien — le volume garde ses règles de lieu — ça retire : qui n'y est pas nommé ne le voit pas, et le serveur ne le lui envoie pas. Pour le registre où vivent les noms, posé sur une table où deux sièges entrent. |
| `office` | facultatif — **sous quelle charge** le volume est tenu, mot pour mot comme au registre des offices. Ne fait pas double emploi avec `tenu_par`, qui dit seulement QUI : ser Robert en tient trois, Aldon Hask trois aussi, et savoir qu'un cahier tombe sur eux ne dit pas de quel chapeau ils le portent — ni quel sceau on regarderait si l'affaire tournait mal. S'affiche sous le titre dans la liste d'un coffret. Une charge réelle sans ligne au registre se note « (hors registre) » : c'est une information, pas un oubli. |
| `titre` | ce qui s'affiche sur l'onglet. |
| `sous_titre` | une ligne : de quelle main, ouvert quand, devant qui. |
| `type` | facultatif — le genre du volume (voir la table ci-dessous). Il écrit son mot en petites capitales à côté du titre et **préremplit la teinte** de la tranche et de l'onglet. |
| `couleur` | facultatif — pour forcer la teinte contre celle du type. N'importe quelle couleur CSS (`#8a6a1f`, `var(--sang)`). À réserver au volume qui ne ressemble à aucun autre : sans elle, le type suffit. |
| `colonnes` | [] les en-têtes du tableau. |
| `lignes` | [] `{cellules: [...], note}` — **autant de cellules que de colonnes**, sinon le tableau se décale. `note` pend sous la dernière colonne, en marge. |
| `tables` | [] **plusieurs tableaux dans un même volume** : `{titre, colonnes, lignes}`. Exclusif avec `colonnes`/`lignes` — l'un ou l'autre, jamais les deux. Le `titre` s'affiche au-dessus de sa grille. |
| `pages` | [] du texte suivi, affiché sous les tableaux. Un livre peut n'avoir que des pages. |

## Un volume à plusieurs tableaux — `tables`

Un **registre** n'a qu'un tableau : c'est une seule sorte de chose, rangée. Une
**affaire** en a plusieurs, et pas par confort — ses états cibles se jugent à
leur preuve, ses verrous à ce qui les lèverait, ses clefs à leur prix, ses
actions à leur office et à leur échéance. Ce ne sont pas les mêmes colonnes, et
les entasser dans une grille commune obligerait à une colonne fourre-tout —
c'est-à-dire à l'endroit où l'on cesse d'écrire ce qui gêne.

```json
{
  "id": "affaire-vierge-01",
  "tables": [
    { "titre": "🏰 L'OUVERTURE", "colonnes": ["Le champ", "Ce qu'on y écrit"],
      "lignes": [{ "cellules": ["LE NOM", "…"] }] },
    { "titre": "🎯 LES ÉTATS CIBLES", "colonnes": ["N°", "L'état"], "lignes": [] }
  ]
}
```

`colonnes`/`lignes` reste la forme courte du volume qui n'a qu'un tableau ;
**les deux ensemble sont une faute** — le second couple ne s'affiche pas, et le
vérificateur le dit. Un tableau vide (colonnes réglées, aucune ligne) s'affiche
quand même : il dit où l'on n'a pas encore écrit.

## Les genres — `type`

Sept, pas un de plus : une étagère où chaque volume a sa couleur n'a plus de
couleurs. Le genre dit ce qu'on vient chercher dedans, pas de quelle main il
est écrit.

| `type` | ce que c'est | teinte |
| --- | --- | --- |
| `registre` | ce qu'un office TIENT, ligne à ligne, au fur et à mesure : ce qui est parti, ce qui est dû, qui tient quoi. | brun d'encre |
| `carnet` | une main privée qui se parle à elle-même. Presque toujours `acteur_id` + `prive`. | violet |
| `plan` | ce qu'on projette et qui n'est pas encore fait : étapes, leurres, chemins. | braise |
| `memento` | ce qu'on consulte pour se rappeler une chose stable — les habitudes de la maison, les repères, ce qui tourne tout seul. | vert |
| `dossier` | ce qu'on croit savoir de quelqu'un ou de quelque chose, avec la bouche dont on le tient. | bleu |
| `regle` | ce qui fait loi : règles du gouvernement, instructions données, ce qu'on dit aux gens. | sang |
| `oeuvre` | ce qui se chante ou se lit pour lui-même — une épopée, une chronique. | or |

Un `type` absent est normal : le livre s'affiche sans mot ni teinte. Un `type`
inconnu fait la même chose — en silence à l'écran, en avertissement au
vérificateur.

**Toute autre clé est ignorée en silence à l'écran.** C'est le piège : rien
n'échoue, la page s'affiche, et l'on croit avoir écrit quelque chose qui
n'existe pas. `tick.py --verifier` les signale.

## Où un livre se lit

- **Posé** (`salle_id`) : c'est un meuble de la maison. Consultable de tout le
  château, avec son adresse écrite sous l'onglet — « Reste à la chambre de la
  Table Peinte ». On ne cache pas un registre de maison à ceux qui y vivent.
- **Porté** (`acteur_id`) : il suit son porteur. Le sien est toujours à portée ;
  celui d'un autre ne s'ouvre que s'il est dans la salle — et jamais s'il est
  `prive`.
- **Réservé** (`lecteurs`) : par-dessus les deux règles précédentes, et sans
  jamais les desserrer. Le carnet des yeux reste posé sur la Table Peinte et ne
  quitte pas la chambre ; simplement, deux personnes seulement l'y ouvrent.

**Le tri se fait au SERVEUR, pas à l'écran.** `GET /books` ne sert à chaque
siège que ce qu'il peut ouvrir : ses carnets, ce qui est posé ou porté dans le
château où il se trouve, et rien de ce qui nomme d'autres `lecteurs`. Ce qui
n'est pas montré n'est pas non plus envoyé — un brouillard qui ne tient que
dans l'affichage s'ouvre avec la console du navigateur. Corollaire : **sans
jeton de siège, l'étagère est close** (`{books: [], siege: false}`), et la page
le dit au lieu d'annoncer qu'il n'y a rien à lire.

## Les boîtes — `etat/boites.json`

Vingt registres posés sur la même table donnent vingt onglets, et vingt onglets
ne se lisent plus : on ne cherche plus un volume, on balaie une rangée. Une
**boîte** est la réponse, et c'est un objet du monde comme le reste — un
coffret sur la Table Peinte, une layette qu'on porte sous le bras. On la pose
où l'on pose un livre, on l'ouvre, on y prend un volume.

Un tableau, un objet par coffret, rien d'autre à la racine.

```json
[
  {
    "id": "boite-gouvernement",
    "lieu_id": "peyredragon",
    "salle_id": "table-peinte",
    "titre": "Le gouvernement",
    "sous_titre": "Qui tient quoi, à quoi on le juge, de quoi on dispose.",
    "embleme": "⚜️",
    "couleur": "var(--book-regle)"
  }
]
```

Ses clés — il n'y en a pas d'autres : `id`, `lieu_id`, `salle_id`, `acteur_id`,
`prive`, `lecteurs`, `titre`, `sous_titre`, `embleme`, `couleur`. Elles ont
exactement le sens qu'elles ont sur un livre. Pas de `type` (une boîte n'a pas
de genre), pas de `colonnes`, de `lignes` ni de `pages` : **une boîte ne se lit
pas, elle s'ouvre.**

**Une boîte donne sa PLACE à ce qu'elle contient.** Un volume s'y range en
portant `boite: "<id>"`, et il perd alors toute place à lui : ni `salle_id`, ni
`acteur_id`, ni `lieu_id`, ni `prive` — il prend ceux du coffret. C'est ce qui
rend le rangement utile : on descend vingt registres à la roukerie en déplaçant
une boîte, et l'on ferme vingt volumes d'un coup en fermant le couvercle. Le
seul verrou qui reste au volume est `lecteurs`, et il **s'ajoute** à celui de la
boîte — un coffret peut fermer plus que le volume, jamais moins.

La résolution se fait au SERVEUR, avant le tri du brouillard, pour la raison qui
vaut partout ici : un volume rangé n'a plus de place propre, donc un tri qui ne
regarderait que le livre le laisserait passer à tout le monde.

À l'écran, la tranche du haut mêle **les coffrets et les volumes qui traînent à
côté** — une table de travail porte des boîtes ET des registres posés dessus, et
rien n'oblige à ranger. Un coffret prend le rang de son volume le plus frais ;
l'ouvrir déplie une seconde tranche, celle de son contenu. Une boîte vide ne
s'affiche pas.

Ce que dit `tick.py --verifier` : coffret nulle part, sans titre, sans emblème,
emblèmes doublés, `prive` sans porteur, `boite` qui ne renvoie à rien, volume
qui garde une place à lui en plus de sa boîte, coffret vide ou d'un seul volume
(un coffret d'un volume est un onglet de plus, pas un rangement).

## Les marques — ce qu'on lit d'une ligne sans ouvrir le volume

**Il n'y a rien à écrire pour les obtenir, et c'est le point.** La carte d'un
coffret portait, sur chacune de ses trente-huit lignes, le même mot de genre
(« Plan ») et le même début de sous-titre (« Affaire ouverte à la Table Peinte
le 26e jour de la 3e lune… »). Une colonne qui dit la même chose sur toutes les
lignes n'aide personne à choisir : elle occupe la place où devrait se lire ce
qui les distingue. Ce qui les distingue est DÉJÀ dans les volumes — on le
remonte, on ne le recopie pas. Une marque écrite à la main serait une seconde
vérité à tenir, et elle mentirait au premier changement.

Trois marques, dans cet ordre, et pas une de plus :

| marque | d'où elle vient | ce qu'elle dit |
| --- | --- | --- |
| **le pilier** | la ligne `PILIER` de l'ouverture du volume | à quoi l'affaire sert — c'est elle qui porte la couleur |
| **l'avancement** | la colonne `⏳ État` de la table `⚔️` du volume | `3 / 19` — ce qui est fait sur ce qui est écrit |
| **l'alarme** | la même colonne | `n bloquées`, ou `rien d'écrit` quand le volume est ouvert et vide |

**Le pilier est le PREMIER nommé dans la phrase**, pas le premier d'une liste :
un volume nomme volontiers les autres piliers pour dire ce qu'il n'est pas. Cinq
valeurs — les quatre piliers de la maison, plus « les trois piliers » pour les
garants —, et un volume qui ne sait pas dire le sien n'en reçoit pas : l'absence
est alors l'information, comme « sur personne » l'est pour la main.

**Le rouge appartient à la faute.** Les quatre teintes de pilier l'évitent, et
seule `bloquée` le prend. Une palette où la couleur d'alarme sert aussi de
couleur de rangement n'alarme plus.

**Un pilier s'empoigne** : le cliquer ne fait qu'une chose — ne garder que lui,
les mains conservées, avec « Tout revoir » pour rendre le coffret. C'est ce qui
sépare une marque d'une étiquette ; une couleur qu'on ne peut pas saisir ne sert
qu'à décorer. Un pilier qui ne garderait rien se relâche de lui-même plutôt que
de laisser une carte vide.

Conséquence pour le MJ : **on ne tient pas les marques, on tient les volumes.**
Une action qui passe à `faite` dans la table `⚔️` d'un cahier change son compte
dans la liste à la lecture suivante, sans qu'on touche à rien d'autre. Et un
volume dont l'ouverture ne sait pas dire son pilier se voit dans la liste, ce
qui est exactement l'épreuve que le guide des affaires demande.

## L'idée — ce qu'il y aurait à faire, sous chaque affaire

La vue « Les sujets » (le coffret `boite-sujets`, 38 volumes `affaire-*`) porte
un interrupteur **💡 idée**. Éteint par défaut, son état retenu en
`localStorage` : allumé, il pose **sous chaque affaire, en retrait, une ligne** —
son idée principale, dans le gabarit de l'échiquier (*afin d'atteindre X, faire Y
aurait effet Z*), avec la lampe et le filet de sa famille, braise pour ce qui
tient à la parole de la reine, vert pour ce qui est du travail de conseil.

**Rien n'est recalculé ici.** La route `/echiquier` dérive déjà les missions des
six registres du plan et range dans chaque affaire son `idee` ; les livres
rapprochent par `livre_id`, l'appariement affaire↔volume que le serveur a déjà
fait, et par rien d'autre. Une affaire sans mission n'affiche rien ; un volume
qu'aucune affaire dérivée ne rejoint non plus — et c'est une information : sur
les 38 cahiers du coffret, **32 portent une idée** — les six autres sont des
affaires dont la chaîne ne réclame rien ou dont le cahier n'a pas de tables.

**L'idée principale se choisit par mesure, jamais par jugement**, dans cet
ordre : la force de l'effet d'abord — lever le dernier verrou d'un état cible bat
lever un verrou sur deux, qui bat porter une action sous une clef ; puis la
portée, à force égale, celle qui remonte au plus d'états cibles ; puis le coût,
à égalité encore, celle qui ne coûte qu'un mot au registre. **Une seule ligne par
affaire** : trente-huit fois trois idées seraient exactement le mur que cette
maison appelle le tunnel.

## Les notes du joueur — le volume qui n'est pas du monde

Un dernier onglet ferme l'étagère, et il n'est PAS dans ce fichier : **« Vos
notes »**. Une zone de texte, toujours à portée quelle que soit la salle, où le
joueur écrit ce qu'il veut. Elle se garde toute seule (le serveur écrit dès que
la main s'arrête) et elle est rendue **telle quelle** : ni JSON, ni colonnes, ni
mise en forme, ni gras d'appui — ce qu'il tape est ce qui est gardé.

Un fichier de texte par siège, `etat/joueurs/<personnage_id>/notes.txt`, écrit
et relu par le serveur (`GET`/`POST /notes`) ; sans roster, `etat/notes.txt`.
Le brouillard vaut ici aussi : les notes de la reine ne sont pas celles de sa
maîtresse de la voix.

**Le MJ n'y touche jamais, et ne s'en sert jamais.** Ce n'est ni un livre du
monde, ni une croyance, ni une parole : personne dans la salle ne l'écrit,
aucun PNJ ne le lit, rien de ce qui s'y trouve n'a eu lieu. C'est le bloc-notes
du joueur, pas une entrée d'état.

## Discipline entre sessions

Une seule règle, et elle suffit :

- **Avant d'écrire un livre, relire `etat/books.json` en entier.** À deux MJ,
  l'autre a pu créer le même pendant que vous écriviez. Deux livres de même
  titre donnent deux onglets identiques à l'écran.
- **On remplace par `id`, on n'ajoute pas.** Pour compléter un livre existant,
  on écrase son entrée ; on ne pousse pas un second objet avec un id voisin.
- **Un livre généré depuis l'état ne se recopie pas à la main** (le mémento des
  routines, par exemple) : on relance son script, sinon il ment dès la
  première routine changée.
- **`python scripts/tick.py --verifier` avant de jouer.** Il dit les id
  doublés, les titres doublés, les clés hors format, les lignes qui ne font pas
  le compte des colonnes, les porteurs et les lieux inconnus.
