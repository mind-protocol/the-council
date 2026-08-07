# Les plis — le courrier comme objets du monde

Note de conception + spécification de `etat/plis.json`. Complément de
`docs/schema.md` (qui reste la référence normative des autres tables et que ce
document ne remplace pas).

## Pourquoi

`evenements.diffusion` est un calendrier de téléportation à retard : on écrit
d'avance « le 24, Untel saura ceci », et la nouvelle arrive sans qu'aucun objet
ni aucun corps n'ait fait la route. Rien ne peut donc être intercepté, retenu,
perdu, ni lu par le mauvais homme — et rien n'arrive périmé.

Un pli est l'objet. Il part d'une main, il voyage, il est remis dans une autre
main. **Le filtrage des nouvelles devient une position d'objet, pas une règle.**

Deux conséquences qu'on tient pour acquises :

- **`porte` est un TEXTE FIGÉ au départ**, et volontairement pas un
  `evenement_id` qu'on relirait à l'arrivée. Un papier ne se met pas à jour : il
  arrive périmé, et c'est ainsi que le brouillard se tient sans avoir à simuler
  de déformation.
- **`main` n'est pas `pour`.** Un pli « remis à Peyredragon » est dans la main du
  mestre Gerardys, pas dans celle de la reine. Ce que la reine sait, elle le sait
  quand le mestre monte l'escalier — et un mestre peut traîner, ouvrir, ou taire.

## Coexistence avec `diffusion`

`evenements.diffusion` **reste en place et fonctionnel**. Les deux mécanismes
tournent côte à côte pendant la transition : `tick.py` continue de proposer les
nouvelles à livrer, et route en plus les plis. Rien n'est retiré tant que le
propriétaire n'a pas appliqué la migration lui-même.

## etat/plis.json

Racine : `{"plis": [ … ]}`. Une liste nue est acceptée aussi par les scripts.

Un pli :

- `id` — kebab-case, unique.
- `canal` — `"corbeau"` | `"cavalier"` | `"barque"`. Un pli est un OBJET : ni
  `rumeur` ni `temoin` n'en sont (ceux-là restent de la `diffusion`).
- `scelle` — bool. Un pli scellé qui arrive descellé est une histoire à lui seul.
- `porte` — le texte figé au départ. Ce que le papier DIT, tel qu'il a été écrit.
- `de` — personnage_id de l'expéditeur.
- `pour` — personnage_id du destinataire voulu.
- `vers` — lieu_id de destination.
- `depuis` — lieu_id de départ (facultatif). Absent, on le déduit du `lieu_id`
  de `de` — ce qui suffit tant que l'expéditeur n'a pas bougé depuis.
- `parti_le`, `attendu_le` — `{annee, lune, jour}`, calendrier de 12 lunes de
  30 jours comme partout.
- `etat` — `"en-route"` | `"remis"` | `"ouvert"` | `"retenu"` | `"perdu"` |
  `"intercepte"`.
- `main` — personnage_id qui l'a EN CE MOMENT. `null` tant qu'il vole ou
  chevauche. Posé à la remise.

Champ libre toléré et jamais lu par les scripts : `note`.

## Les délais

Depuis `lieux.jours_de_pr` (jours de route depuis Port-Réal), la distance entre
deux places s'estime par la différence des deux valeurs, au minimum un jour :

- `corbeau` — environ le tiers du plein tarif (arrondi au supérieur, minimum 1).
- `cavalier` — plein tarif.
- `barque` — plein tarif.

`attendu_le` est écrit à l'envoi et ne bouge plus : c'est une prévision, pas une
promesse. Un pli qui traîne au-delà se signale à `--verifier`.

## Le stock de corbeaux — `lieux.roukerie`

Champ facultatif de `lieux.json` : `roukerie: {<lieu_id d'origine>: <nombre>}`.

**Un corbeau ne vole que vers là où il a été élevé.** Le stock d'un lieu A se lit
donc « A détient N oiseaux nés en B, qui ne savent voler que vers B ».

- Écrire de A vers B par corbeau consomme un oiseau de `lieux[A].roukerie[B]` —
  le stock de la DESTINATION, tenu chez l'expéditeur.
- On n'en regagne que quand l'autre bout en renvoie un : B écrivant à A rend un
  oiseau à `lieux[A].roukerie[B]`. Une correspondance à sens unique se tarit.
- `cavalier` et `barque` n'ont pas cette limite, et paient le plein tarif.

Un lieu sans champ `roukerie` n'est pas contraint : c'est un lieu dont on n'a pas
encore tenu les comptes, pas un lieu sans corbeaux.

## Ce que fait `scripts/tick.py`

À chaque fenêtre, les plis `en-route` dont `attendu_le` est échu passent
`en-route` → `remis`, `main` = le **destinataire naturel du lieu** :

1. le mestre présent sur place (titre contenant « mestre », la roukerie d'abord),
2. à défaut, rien : `main` reste `null` et la proposition le signale — au MJ de
   dire dans quelle main ça tombe.

Ce n'est JAMAIS le `pour` : c'est tout l'intérêt. Le script ne décide rien de
plus, et n'écrit que sous `etat/staging/`.

`--verifier` signale :

- un pli `en-route` dont l'échéance est dépassée depuis plus de 3 jours ;
- un corbeau parti d'un lieu dont la roukerie n'a pas (ou plus) d'oiseau pour la
  destination ;
- un pli `remis` (ou `ouvert`) sans `main`.

## Vocabulaire de mutation

Fermé, comme le reste (`scripts/appliquer.py` fait autorité) :

    {table: "plis", cible: <pli_id>, operation: "pli",
     champs: {etat | main | attendu_le | canal | scelle | porte}}

    {table: "plis", operation: "pli_ajouter", valeur: <objet pli complet>}

    {table: "lieux", cible: <lieu_id>, operation: "roukerie",
     champs: {<lieu_id d'origine>: <entier >= 0>}}

## La bouche — le deuxième porteur

Trois porteurs, et pas un de plus : **le pli, la bouche, la rumeur**. Le pli est
un objet et porte UNE chose, figée. La bouche est un homme, et **un homme qui se
déplace porte tout ce qu'il sait** — ses `croyances` entières, y compris ce
qu'il croit à tort, y compris ce qu'il ne dira pas.

La bouche ne demande **aucune donnée neuve** : `personnages.lieu_id` bouge déjà,
et les têtes ont déjà leurs `croyances`. On branche ce qui existe.

### Détecter les arrivées

`tick.py` ne tient pas de journal de déplacements — il déduit les arrivées de ce
qui est déjà dans le tick :

1. **Un événement de la fenêtre** qui se tient quelque part, dont un `acteur`
   n'est pas encore sur place : il faudra bien qu'il y vienne. Source la plus
   sûre (`source: "evenement"`).
2. **Une étape de plan qui tombe** et dont le texte nomme un lieu connu, autre
   que celui où l'acteur se trouve (`source: "etape"`). **Heuristique** : le
   lieu est seulement CITÉ dans la phrase — un homme peut parler de Peyredragon
   sans y aller, ou n'y envoyer qu'un valet. La sortie le dit en toutes lettres,
   et c'est au MJ de trancher d'un coup d'œil.

Seul un personnage qui a une tête dans `intentions.json` est un porteur : sans
tête, il n'a rien à porter. Le personnage joueur est exclu — sa bouche est à lui.

### Ce que le tick sort : le différentiel, pas le verdict

Pour chaque arrivée, la clé `bouches` de la proposition donne : qui, d'où, vers
où, par quel indice — puis **`apporte`** : celles de ses croyances qu'aucune tête
déjà présente sur place ne tient (rapprochement par mots rares, voir plus bas),
et `deja_su_sur_place` pour le reste, avec qui le sait.

**Le script ne recopie AUCUNE croyance et ne réécrit aucune tête.** Un homme qui
sait ne raconte pas tout, et ment parfois : ce qui se dit, ce qui se tait et ce
qui se déforme est un arbitrage du MJ, qui ajoute ses mutations à la main
(`croyance_ajouter` sur les têtes qui l'auront cru).

### Le joueur est un cas à part

Un porteur qui arrive dans le lieu de `journal.personnage_joueur_id` est signalé
distinctement (`arrive_chez_le_joueur`). Il n'en sort **jamais** une croyance qui
se recopie en silence : il en sort une entrée `info.json`, avec une bouche, un
visage et une fiabilité — quelqu'un est entré, essoufflé, et a parlé.

### `--verifier` : « aucune croyance sans porteur »

La garde de fond de la refonte, en gravité **`note`** : elle s'imprime sous un
bandeau `NOTE` distinct et **ne compte pas dans le code de sortie**. Sur l'état
d'avant la refonte elle crie beaucoup, et c'est attendu.

**Heuristique, assumée comme telle** : on ne sait pas relire le français. Pour
chaque tête, on rassemble tous les textes auxquels le personnage a eu accès —

- les entrées de `diffusion` **livrées** qui le nomment, ou livrées à son lieu ;
- les plis qu'il a en `main`, ou qui lui sont adressés et arrivés ;
- les actes qu'il a commis, dont il est dit `connu_de` (ou `"tous"`), ou qui se
  sont produits sous ses yeux (même lieu) ;
- les paroles dont il est locuteur, destinataire ou témoin ;
- les croyances des autres têtes présentes au même endroit (la bouche) ;

— et on cherche un **recoupement de mots rares** : au moins deux mots d'au moins
cinq lettres, hors banalités, partagés entre la croyance et un de ces textes.
Une croyance qui ne recoupe rien est dite « sans porteur repéré ».

Faux positifs attendus : une croyance reformulée dans d'autres mots que sa
source, un savoir d'éducation (« ce qu'un seigneur sait de naissance »), une
déduction propre au personnage. Faux négatifs attendus : deux textes qui partagent
des noms propres sans parler du même fait. C'est un détecteur d'oubli, pas un juge.

## La rumeur — le troisième porteur, celui qui n'a pas de nom

Le pli est un objet et porte une chose, figée. La bouche est un homme et porte
tout ce qu'il sait. **La rumeur n'a pas de porteur nommé** : elle saute de lieu
en lieu et **se déforme à chaque saut**, au lieu d'être écrite d'avance avec sa
fiabilité comme le fait `diffusion`.

### Une rumeur EST un incident — pas de quatrième table

L'objet existe déjà : l'`incident` de la table de guerre (`etat/jetons.json`,
`docs/carte.md`). Un foyer (`ou`), les endroits gagnés (`propage[]`, datés, avec
leurs âmes et leur `certitude`), ceux qu'on craint (`risque[]`), un `contenu` en
toutes lettres, un `feu` (`vif` · `couve` · `eteint`). C'est exactement la forme
d'une rumeur, et elle se dessine déjà toute seule sur la table.

Il manquait deux choses, ajoutées comme **champs facultatifs sur une entrée de
`propage[]`** — aucune table neuve, et le module de rendu les ignore :

- **`contenu`** — la version du propos **tel qu'il se dit là-bas**. Sans lui, un
  relais hérite du texte du foyer et la rumeur voyage sans se déformer, ce qui
  est précisément le défaut de `diffusion`.
- **`depuis`** — d'où le saut est parti : un lieu (bouche à oreille anonyme) ou
  **une personne** (une parole d'autorité — voir « Où finit la rumeur et où
  commence la bouche » plus bas). Utile pour lire la chaîne de dégradation, et
  pour que le MJ voie par où c'est passé.

La fiabilité, elle, n'avait besoin de rien : la `certitude` existe déjà par
relais. Elle sert d'échelle à trois crans — `sure` → `rapportee` → `rumeur` —
et **un saut la dégrade d'un cran**. En dessous de `rumeur`, on ne descend plus :
c'est le plancher du trouble.

### La propagation dans `tick.py`

À chaque fenêtre, pour chaque incident `actif` qui n'est pas `eteint` :

- **Délai** : plein tarif cavalier entre les deux places (écart des
  `jours_de_pr`), multiplié par 3/2 et jamais moins de 2 jours. Une rumeur est
  **plus lente qu'un cavalier** — elle passe de bouche en bouche et s'arrête
  boire.
- **Source** : le relais déjà pris qui l'amène le plus tôt (le foyer en fait
  partie), pas forcément le foyer.
- **Où elle peut aller** : les `risque[]` écrits par le MJ — c'est lui qui a dit
  où ça peut prendre — plus, **si le feu est `vif` seulement**, le voisinage à
  3 jours de cavalier d'une place déjà gagnée. Une chose qui `couve` ne gagne
  pas de terrain toute seule.
- **Plafond** : 3 voisins par rumeur et par fenêtre, les plus proches. Les
  `risque[]` ne sont jamais plafonnés, ni un saut qui atteint le joueur. Sans ce
  plafond, six jours proposaient vingt et un sauts — et une proposition qu'on ne
  relit plus vaut une proposition vide.
- **Ce que le script écrit** : le saut, sa date, sa source, et la certitude
  **dégradée**. Et une mutation `incident_propage` dont le **`contenu` est laissé
  à `null`** : `appliquer.py` refuse le lot tant que le MJ n'a pas écrit ce qui
  se dit là-bas. **Le script n'invente aucune prose** — c'est le seul endroit du
  jeu où le brouillard se fabrique, et une machine n'a rien à y faire. Le refus
  vérifie aussi que la certitude a bien décru, et qu'un endroit ne prend pas deux
  fois.

### Une rumeur qui atteint le joueur

Signalée à part (`atteint_le_joueur`), comme une bouche. Elle devient une entrée
`info.json` avec sa source de **bouche à oreille** et une **fiabilité basse** :
personne ne l'a apportée, personne ne peut la confirmer, et c'est tout son
intérêt. Jamais un fait, jamais un chiffre sûr.

### `--verifier`

Deux notes (gravité `note`, non bloquantes, sous le bandeau `NOTE`) :

- **rumeur immobile** — rien de neuf depuis plus de 5 jours pour un feu `vif`,
  15 pour un feu qui `couve`. Une rumeur avance ou s'éteint ; celle qui fait ni
  l'un ni l'autre ment sur son propre `feu`.
- **fiabilité qui n'a pas décru** — un relais aussi sûr (ou plus) que le foyer.
  Un relais sans `certitude` du tout est signalé aussi : il hérite du foyer, donc
  ne se dégrade jamais.

### Où finit la rumeur et où commence la bouche

`depuis` trace la frontière entre le troisième porteur et le deuxième, et c'est
la distinction la plus importante de cette section.

- **`depuis` nomme un LIEU** — du bouche à oreille anonyme. Personne ne répond de
  ce qui se dit ; la certitude **doit** décroître d'un cran, et `--verifier` le
  réclame.
- **`depuis` nomme une PERSONNE** (un id de `personnages.json`) — ce n'est plus
  une rumeur. C'est une **parole d'autorité**, avec un nom dessus : le deuxième
  porteur, la bouche. Elle est **exemptée** du contrôle de décroissance.

Ser Criston qui fait crier tout haut que la femme couronnée à Peyredragon est
celle qui les a brûlés n'affaiblit pas le propos en le reprenant : il l'endosse.
Et **`certitude` mesure la confiance de qui entend, pas la vérité** — une
proclamation entièrement fausse peut être `rapportee` sans que rien ne cloche,
parce qu'on croit celui qui la crie.

Conséquence pratique : quand un relais est adossé à quelqu'un, écris son id dans
`depuis`. C'est ce qui distingue « on dit à Port-Réal que… » de « Criston fait
dire que… », et les deux n'ont ni le même démenti possible ni le même poids.

### Le témoin — un porteur sans tête, et c'est voulu

Un témoin est le cas limite de la frontière ci-dessus : **un `depuis` qui nomme
une personne qui n'a pas de tête dans `intentions.json`**. Il est admis comme
relais nommé d'un incident, et rien de plus.

**On ne lui donne PAS de tête minimale.** Une tête coûte du budget d'échelle et
se met à dériver dès qu'on ne la relit plus — or un témoin n'a pas de projet : il
a vu quelque chose, et il le raconte. Peupler `intentions.json` de gens qui n'ont
rien à poursuivre, c'est payer de l'attention de MJ pour du décor. S'il se met à
avoir un projet, il sera promu par les voies normales, comme n'importe qui.

Ce que ça implique, et qui est implémenté :

- **Il est exempté de la décroissance** comme toute parole d'autorité : il a un
  nom, ce n'est plus du bouche à oreille anonyme.
- **Ce qu'il apporte compte comme porteur.** L'heuristique « croyance sans
  porteur » verse à son corpus le `contenu` de tout relais arrivé au lieu du
  personnage, et de tout relais dont il est lui-même le `depuis`. Sans cette
  branche, un fait parfaitement porté par un témoin nommé serait crié comme
  orphelin.
- **Son absence de tête n'est JAMAIS une anomalie.** Le contrôle « personnage
  actif sans tête ni mains » l'épargne, et les budgets d'échelle ne comptent que
  les têtes — il n'y pèse donc rien, par construction.

## Les trois porteurs — bilan

| | porteur | ce qu'il porte | déformation | où ça vit |
| --- | --- | --- | --- | --- |
| **le pli** | nommé, un objet | UN texte figé au départ | aucune — il arrive périmé | `etat/plis.json` |
| **la bouche** | nommé, un homme | TOUT ce qu'il sait | ce qu'il tait et ce qu'il ment (au MJ) | `intentions.croyances` + `personnages.lieu_id` |
| **la rumeur** | aucun | un propos qui court | un cran de `certitude` par saut | `etat/jetons.json`, genre `incident` |
| *(le témoin)* | nommé, sans tête | ce qu'il a vu | aucune — il l'endosse | un relais d'incident dont le `depuis` le nomme |

Le témoin n'est pas un quatrième porteur : c'est le point où la rumeur cesse
d'être anonyme sans devenir pour autant un acteur qu'on simule.

**Ce qui est couvert** : l'écrit qui voyage et peut être retenu, perdu, lu par le
mauvais homme ; l'homme qui arrive et vide son sac ; le bruit qui gagne de
proche en proche en se dégradant. Les trois sont tenus par `tick.py`, aucun
n'écrit de prose, et tous passent par `etat/staging/`.

**Ce qui reste à `diffusion`** : les nouvelles qu'un MJ veut poser à date fixe
sans se soucier de la route, et tout l'existant, qui continue de tourner. Le
canal `temoin` n'en fait plus partie : il est couvert par le relais nommé.

**Ce qu'il faudrait pour retirer `diffusion` un jour** — la première condition
est tombée, il en reste trois :

1. ~~**Un porteur pour le témoin.**~~ **Réglé** : le témoin est un relais nommé
   d'incident, sans tête et sans budget. Aucune mécanique neuve n'a été
   nécessaire — la frontière rumeur/bouche le couvrait déjà.
2. **La livraison qui écrit les croyances.** Aujourd'hui la `diffusion` livrée
   entre dans les `croyances` ; avec les trois porteurs, c'est un arbitrage du MJ
   à chaque arrivée. Tant que c'est à la main, `diffusion` reste plus commode
   pour les nouvelles de masse — et c'est la vraie raison de sa survie.
3. **La migration du reste** : `scripts/migrer_plis.py` couvre les canaux
   d'objet ; il faudrait son équivalent pour convertir les entrées `rumeur` en
   incidents, et les `temoin` en relais nommés — ce dernier cas est désormais
   une conversion mécanique, puisque la cible existe.
4. **Le jour où plus aucune entrée `diffusion` non livrée ne reste**, retirer le
   champ du schéma et la boucle de `tick.py` — pas avant : une nouvelle en vol
   qu'on jette est une information que le monde perd.

## Migration

`scripts/migrer_plis.py` convertit les entrées `evenements.diffusion` de canal
`corbeau`/`cavalier`/`barque` en plis, et écrit sa sortie dans `etat/staging/`.
Il ne touche jamais `etat/`. `rumeur` et `temoin` sont laissés à `diffusion` :
ce ne sont pas des objets.
