# Les livres — `etat/books.json`

Un **livre** est un OBJET du monde : un registre posé sur une table, un carnet
qu'on porte sous le bras. Il porte du JSON, il se consulte à l'écran sous
l'échelle « Les livres » du décor, et il n'existe QUE s'il est inscrit ici.
Un registre qu'on décrit en scène sans l'écrire dans ce fichier n'a pas été
ouvert : le joueur ne pourra jamais y lire une ligne.

Ce fichier est technique — comme `routines.json`, `presence.json` et
`horloges.json` — et vit donc hors de `docs/schema.md`, qu'on ne modifie
jamais. Le format ci-dessous est celui que lit `ecrans/modules/books.js`, et
**lui seul**. Il est vérifié par `python scripts/tick.py --verifier`.

## Le fichier

Un tableau, un objet par livre. Rien d'autre à la racine.

```json
[
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
]
```

## Les clés — il n'y en a pas d'autres

| clé | rôle |
| --- | --- |
| `id` | kebab-case, unique. C'est lui qui permet de remplacer un livre au lieu d'en créer un deuxième. |
| `lieu_id` | le château où il se trouve (`lieux.json`). Obligatoire pour un livre posé. |
| `salle_id` | la salle où il est POSÉ (`ecrans/modules/plans.js`). |
| `acteur_id` | ou la personne qui le PORTE (`personnages.json`). **`salle_id` ou `acteur_id`, jamais les deux.** |
| `prive` | `true` : un carnet que son porteur ne montre à personne — seul le joueur qui le porte le voit. |
| `titre` | ce qui s'affiche sur l'onglet. |
| `sous_titre` | une ligne : de quelle main, ouvert quand, devant qui. |
| `type` | facultatif — le genre du volume (voir la table ci-dessous). Il écrit son mot en petites capitales à côté du titre et **préremplit la teinte** de la tranche et de l'onglet. |
| `couleur` | facultatif — pour forcer la teinte contre celle du type. N'importe quelle couleur CSS (`#8a6a1f`, `var(--sang)`). À réserver au volume qui ne ressemble à aucun autre : sans elle, le type suffit. |
| `colonnes` | [] les en-têtes du tableau. |
| `lignes` | [] `{cellules: [...], note}` — **autant de cellules que de colonnes**, sinon le tableau se décale. `note` pend sous la dernière colonne, en marge. |
| `pages` | [] du texte suivi, affiché sous le tableau. Un livre peut n'avoir que des pages. |

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
