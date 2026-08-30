# L'échiquier — le plan vu comme une position

La table peinte dit **où** porte la guerre. L'échiquier dit **comment** ce qu'on
a devient ce qu'on veut. C'est une échelle du décor comme les autres, ouverte
partout dès qu'il y a une affaire à lire — on décide dans l'escalier, on se
souvient au quai, et une ligne de jeu qu'on ne peut pas relire là où l'on est
n'est pas relue du tout.

Il ne parle que le vocabulaire de la maison, celui du guide « Comment on ouvre
une affaire » : 🏰 l'affaire · 🎯 l'état cible · 🔒 le verrou · 🗝️ la clef ·
⚔️ l'action · 🔨 le moyen · 🪶 l'office. Sept objets, pas un de plus, et leurs
signes viennent du guide.

**Il ne contient rien.** Tout est dérivé des `tables` des cahiers d'affaire, à
la lecture. Aucun fichier d'état, aucune écriture, jamais — une vue qui
recopierait le plan serait un mensonge en attente.

> **Cette phrase du guide n'est plus vraie, et c'est une décision de la maison,
> prise le 30e.** « Quand l'affaire et le registre se contredisent, c'est le
> registre qui a raison » supposait un registre TENU. Il ne l'est plus : 156
> lignes contre 1164, et la plupart des affaires les plus travaillées n'y ont
> pas une ligne. **Un seul plan désormais : les cahiers d'affaire sont la
> vérité, les registres par type deviennent dérivés** — régénérés depuis les
> cahiers, jamais écrits à la main, comme `couverture.py` régénère déjà les
> tables de trous. Le guide reste un objet de fiction et ne se corrige pas ;
> c'est ici qu'on note ce qui a changé.

> **Le damier est celui de CELUI QUI REGARDE, et il ne l'était pas.** La vue
> lisait `books.json` en entier, sans le tri de l'étagère, et ne reconnaissait
> un cahier d'affaire qu'à son id — `affaire-*`. Marlo Vasse, qui tient ses
> propres affaires à Port-Réal sous `nera-*`, y trouvait donc les quarante-deux
> plateaux du conseil de Peyredragon et pas un des siens. Deux règles
> remplacent cela, et elles valent pour toute maison qui tiendra un plan :
> — **on ne sert que ce que ce siège peut ouvrir dans les livres**, par le même
>   tri que `/books` (boîtes, `lecteurs`, `prive`, le château où l'on est) : un
>   plateau qu'on ne peut pas ouvrir n'est pas un plan qui est le sien ;
> — **un cahier d'affaire se reconnaît à sa FORME** — l'ouverture de l'affaire
>   et la table des états cibles —, jamais à son nom.
> Les moyens et les offices se récoltent de même : toute table portant une
> colonne « Le moyen » ou « L'office », où qu'elle soit posée, et non plus aux
> deux ids `plan-moyens` / `plan-offices` du Grand Plan de la reine.

## Ce qu'on y lit sans rien survoler

Un plateau = une affaire. Une colonne = un état cible. Quatre rangs de cases
sous une canopée : les états cibles forment un **arbre** (selon ce que chacun
sert), et les colonnes descendent de ses pieds.

Le damier est **muet** : des cases carrées et toutes égales, un jeton par pièce,
des traits entre les rangs. Ce qui se lit de loin est la FORME — quels rangs
sont pleins, quelles colonnes ne jouent pas, ce qui est levé et ce qui est posé,
où sont les buts et **combien on en voit**.

**Un état cible ne se voit que par les brèches de ses verrous.** Une dalle par
verrou ; la brèche s'ouvre quand une clef *retenue* est écrite contre ce
verrou-là, et pas avant. Un état à un verrou sans clef retenue est muré : on
sait qu'on le veut, on ne peut pas encore le lire. Ça interdit de se raconter un
plan — le joueur ne voit pas un but difficile, il voit un but qu'il ne peut pas
encore formuler.

Et l'épreuve du guide se passe toute seule : **une colonne qui ne descend
jusqu'à aucune action** a sa réglette rouge et son état porte le fanion. C'est
le *REMONTER* du livre — « si la remontée est impossible, l'action n'a pas de
raison stratégique démontrée » —, rendu visible sans que personne ait à le
mener.

Une action porte le **visage de son teneur**. C'est la seule chose qu'on veuille
savoir après « qu'est-ce qu'on fait » : qui le fait. Faute de teneur, elle garde
les épées — et l'absence saute aux yeux quand tous les voisins ont un visage.

## Ce que la bulle dit

Au survol : le signe, le nom, la description, puis **la conclusion** et **les
pas**, puis les maillons de la chaîne allumée. Un clic la retient.

Survoler allume la **chaîne causale** dans les deux sens : l'aval — tout ce qui
construit la pièce, jusqu'en bas — à pleine encre ; l'amont — ce à quoi elle
sert, jusqu'à la racine — à mi-voix. Le reste du plateau s'efface.

**La conclusion** nomme le premier maillon qui manque en descendant. Une pièce,
un coupable, une phrase. Elle ne résume pas : elle dit où ça casse.

**Un pas** dit ce qu'il y aurait à faire, dans un gabarit unique :

> Afin d'atteindre 🎯 Île tenable, retenir ou écarter 🗝️ Rendre des bouches au
> continent lèverait 🔒 Plus de bouches que de charge — le seul verrou qui l'en
> sépare.

Trois cases, dont deux se calculent : **X** en remontant l'arbre, **Z** en
regardant ce que l'acte débloquerait — et Z est honnête, « le seul verrou qui
l'en sépare » quand c'est vrai, « un verrou sur deux » quand ça ne suffit pas.
Une chose qui ne remplit pas les trois cases n'est pas un pas.

Six détecteurs seulement, et **tous adossés à une règle écrite du guide** : un
état veut un verrou, un verrou veut une clef, une clef se tranche, une action
veut un office. Rien d'inventé.

**Les pas se dédupliquent par l'ACTE**, jamais par le détecteur qui les trouve :
*retenir cette clef* est un acte unique, même si trois règles le désignent. Et
la 💡 se pose **une fois par acte**, sur la pièce que l'acte vise — nulle part
ailleurs. Les pièces en amont le disent dans leur bulle, ce qui est sa place.

## Ce qu'il ne fait pas, et pourquoi

**Il ne connaît pas les dates.** Rien que la topologie et l'état des nœuds. Le
croisement avec `monde.date` existe et vit ailleurs — `scripts/etat_du_plan.py`.

**Il n'écrit rien.** Ni dans les cahiers, ni dans `intentions.json`, ni nulle
part. Il détecte ; les hommes décident.

**Il n'assigne rien.** Ce qu'il trouve n'est pas une commande de la reine : c'est
**le bon sens de celui qui porte l'affaire**. Un homme compétent qui regarde son
propre cahier voit ces trous. On les lui met sous les yeux, on ne les lui donne
pas comme ordre.

**Un détecteur qui ne discrimine pas ne s'affiche pas.** « Ce verrou n'a pas de
rechange » tombait sur 32 verrous sur 33 : il ne dit rien et noie le reste. Il ne
se jette pas pour autant — il se **retourne et se dit une fois**, sur le blason
de l'affaire. Un fait vrai de presque tout le monde va au chapeau, jamais sur un
jeton.

## Les deux espèces de trous — et pourquoi celle-ci n'est que la seconde

C'est la distinction la plus importante de ce document, et elle est venue d'un
test raté : on a fermé la boucle à la main pour voir si elle se ferme, et elle
n'a rien fermé. Elle explique aussi pourquoi cette vue ne remplacera jamais un
homme dépêché.

**Le trou MÉCANIQUE se détecte.** « Ce verrou n'a pas de clef », « cette clef
n'est pas tranchée », « cette action ne nomme aucun office par son numéro ». Il
est exhaustif, il ne coûte rien à trouver, il se compte — et **il vaut peu**.
C'est de la tenue de registre. **Les six détecteurs de cette vue ne font que
ça, et ne feront jamais rien d'autre.**

**Le trou NARRATIF ne se détecte pas.** « Ce plan suppose que Bar Emmon dira
oui. » « Personne n'a vérifié si les officiers du Guet sont encore payés. »
Aucun graphe ne sort ça : il se trouve **en travaillant**, par un homme, dans sa
journée. C'est le seul qui déplace quelque chose.

**Et le trou narratif a déjà son nom dans la maison : c'est un VERROU.**
Définition du guide, mot pour mot — *le fait du monde qui empêche un état de
tenir*, avec son test : « si tout le reste était acquis et que ceci restait vrai,
l'état serait-il impossible ? ».

D'où la répartition, qui est la seule qui fasse tenir les deux :

```
    l'homme travaille  →  il trouve un empêchement  →  il écrit un 🔒 verrou
                                                             ↓
      le détecteur : « ce verrou n'a pas de clef »  →  🗝️ une clef  →  ⚔️ une action
```

**Le mécanique n'est pas le concurrent du narratif : il est son AVAL.** L'homme
apporte ce que le calcul ne peut pas trouver ; le calcul dit aussitôt ce qui
manque autour. Une vue qui prétendrait trouver les empêchements à la place des
hommes ne trouverait que des colonnes vides.

**Un seul de nos détecteurs commande un travail narratif** : « 🎯 état cible sans
aucun verrou — trouver ce qui empêche ». Celui-là ne se referme pas d'un trait de
plume : il faut dépêcher quelqu'un. Il ne devrait donc pas se présenter comme les
autres, entre deux corrections de registre.

### Le test de boucle du 30e — ce qu'il a montré

**La tuyauterie tient.** Un rapport d'Aldon Hask visait `affaire-ralliement-
population` avec `"table": "lignes"` — une coordonnée qui ne résout pas.
Corrigée en `⚔️ Actions`, `verser_cahier.py` est passé de 1 refus à **3 poses,
0 refus**, dans les bonnes cellules. Le verseur refuse plutôt que de rapprocher
au plus proche, et c'est la bonne conduite : une adresse approximative est du
travail perdu, pas une ligne écrite de travers.

**La boucle sémantique, non.** Comptes de trous avant et après : **identiques**.
Ce qu'il avait écrit était une mise à jour d'`⏳ État` — « payée et reçue, le
défaut de treize dragons est éteint » — sur une ligne qui avait déjà son teneur,
**et aucun détecteur ne regarde cette colonne**. Les détecteurs guettent des
manques de structure ; les hommes écrivent de la prose dans des colonnes
d'avancement. Les deux se croisaient sans se voir.

La leçon n'est pas qu'il faut de nouveaux détecteurs qui liraient la prose : ce
serait rendre au calcul ce qui appartient aux hommes. C'est que **ce qu'un homme
trouve doit s'écrire dans la structure** — une ligne de verrou, pas une phrase
dans une case d'état. C'est écrit en toutes lettres dans `scripts/agents/prompts/metier.md`,
section « Un empêchement trouvé s'écrit comme un VERROU », avec la coordonnée
exacte.

### Deux natures de trous — et le gabarit ne va qu'à la première

Nos premiers détecteurs disaient tous la même sorte de chose : **ce qui manque au
BOUT de la chaîne**. Pas de clef sous ce verrou, pas d'action sous cette clef,
pas d'office sous cette action. Le gabarit leur va parce que l'état cible est
connu — c'est même ce qu'on remonte pour écrire le *X*.

**Une seconde nature est apparue : la chaîne rompue AU MILIEU.** Une action qui
désigne la clef `21020`, laquelle n'est dans aucun cahier. Un verrou dont la
colonne « Bloque » porte le numéro d'une action. Une action qui ne désigne rien
du tout. Là, **X est introuvable par construction** : c'est précisément la
remontée qui est perdue. Les forcer dans la forme des pas ferait passer une
action sans raison stratégique démontrée pour un oubli d'écriture.

Elles ont donc leur propre forme, et leur propre nom — **rupture** :

> *Afin de rendre sa raison à* ⚔️ 🧺 Canal marchand, *retrouver la clef 21020
> qu'elle désigne lui rendrait sa remontée jusqu'à l'affaire — aujourd'hui elle
> ne remonte à rien.*

**Une rupture passe avant tout le reste** dans la réserve d'un homme (force 0).
C'est le test disqualifiant du guide, mot pour mot : « si la remontée est
impossible, l'action n'a pas de raison stratégique démontrée — elle se supprime
ou se requalifie ». Une action sans raison passe avant un office sans numéro.

**Et une rupture ne se répare JAMAIS au script.** Trois actions désignent la clef
`21020` : renumérotage ? clef supprimée ? doigt glissé depuis `21021` ?
Rapprocher au plus proche écrirait une **fausse raison stratégique** — pire que
l'absence, parce qu'elle ne se voit plus. Même règle que `verser_cahier.py` :
refuser plutôt que deviner. On détecte, un homme tranche.

### Ce que les onze détecteurs trouvent, au 30e

| | défaut | pièces | nature |
| --- | --- | --- | --- |
| 🔤 | office ou moyen nommé en clair | 477 | pas (au chapeau) |
| 🪢 | référence qui ne tient qu'au registre | 81 | rupture (au chapeau) |
| ↗️ | raccourci — le renvoi saute un rang | 77 | — (manière d'écrire) |
| ⚔️ | action que personne ne peut porter | 65 | pas |
| 🔒 | verrou qu'aucune clef n'ouvre | 48 | pas |
| 🏷️ | « fait » écrit de plusieurs façons | 21 | pas (au chapeau) |
| 🎯 | état qu'aucun verrou ne bloque | 8 | pas (à dépêcher) |
| 🗝️ | clef retenue qu'aucune action ne réalise | 6 | pas |
| ⚔️ | action qui ne remonte à aucun état cible | 5 | rupture |
| ⚔️ | action orpheline — elle ne désigne rien | 5 | rupture |
| 🔀 | erreur de genre — la colonne porte l'autre rang | 3 | rupture |
| ⛓️‍💥 | référence pendante — le numéro n'existe nulle part | 1 | rupture |

**Trois d'entre eux vont au chapeau et non sur les pièces.** Un fait vrai de
quatre cents pièces n'est pas quatre cents décisions : c'est une discipline à
reprendre d'un coup. La réserve d'un homme les porte en une ligne par cahier, et
la vue par homme les fond en une seule ligne pour tout le monde.

**Le raccourci n'est pas une faute.** 77 renvois sautent un rang — une action qui
désigne directement son état cible, sans passer par une clef. La chaîne monte
quand même ; elle est seulement plus courte que le guide ne la dessine. À cette
échelle, c'est une manière d'écrire, pas un accident : on la compte, on n'en fait
pas un pas.

### Les deux plans, mesurés — et ce que ça coûte de ne pas trancher

`couverture.py` lit **les deux plans à la fois** : les cahiers d'affaire ET les
six registres par type, indexés par le même numéro. La route `/echiquier`, elle,
ne lit que les cahiers depuis le 30e. Ce n'est pas un détail de tuyauterie :

- **81 renvois de cahier ne résolvent que par un registre.** L'action 21030
  désigne la clef 21020 : elle existe au registre `plan-clefs`, elle n'est dans
  aucun cahier. Pour `couverture.py`, la chaîne tient. Pour l'écran, elle pend.
  **Les deux ont raison sur leur propre plan**, et c'est exactement pourquoi il
  faut n'en garder qu'un.
- **145 pièces sur 1286 n'étaient analysées par personne** — le registre nommait
  leur affaire autrement que le cahier qui les porte (« Ralliement de la
  population » contre « Retournement des maisons hésitantes des terres de la
  Couronne »), et le premier livre lu gagnait. Elles tombaient dans le `miennes`
  de personne. Corrigé le 30e : le cahier a désormais le dernier mot sur son
  propre numéro, et il en reste 123, toutes venues des seuls registres.
- **`scripts/etat_du_plan.py --comparer`** dit l'écart entre les deux lecteurs en
  une commande. C'est le garde-fou, faute d'avoir pu les factoriser.

### Deux copies n'est pas un défaut de propreté

C'est **une machine à envoyer les hommes contre des fantômes**, et l'on en a la
démonstration datée.

Le Sanglier a renommé l'état cible `23000` dans son cahier : *Donjon ouvert* est
devenu **Le Donjon a changé de main sans combat dans les murs** — parce que toute
l'affaire tient à ce qu'on ne l'ouvre pas mais qu'on le déverrouille. Le registre
`plan-etats-cibles` portait toujours l'ancien nom. **Sa propre liste de trous,
servie le matin même, lui a resservi le nom périmé.** Un peu plus et il partait
travailler contre un objectif qui n'existe plus, sans que rien le lui dise.

Le mécanisme est bête et il est dans le code : les pièces sont indexées **par
numéro à travers tous les livres**, et le nom se pose au premier livre lu
(`setdefault`). Les six registres sont écrits avant les cahiers dans
`books.json` — **donc, pour les 96 pièces que les deux plans portent, c'est
toujours le nom du REGISTRE qui s'affiche**, dans `couverture.py` comme dans
`etat_du_plan.py`. Le correctif du 30e a donné le dernier mot au cahier sur
l'AFFAIRE d'une pièce ; il ne le lui a pas donné sur son NOM.

Ce n'est pas un cas isolé. Sur ces 96 pièces communes, **33 seulement sont
identiques** : 63 divergent sur au moins une colonne, et **10 divergent sur le
nom même**. Une pièce qui divergerait franchement se verrait ; ce sont les
autres qui coûtent — un nom raccourci, une preuve qui a perdu sa moitié, un
office passé de *À DÉSIGNER* au nom d'un homme.

Et la divergence n'est pas seulement du retard : c'est parfois **une autre
affaire sous le même numéro**. Le bloc `7000` porte au registre le *Soutien de
la population* de « La ville de Port-Réal » ; dans `affaire-vierge-04`, ces
mêmes numéros portent le Trident, Harrenhal et ses cages. `44001` est une
ACTION au registre et un VERROU dans le cahier de la présence à Port-Réal. Un
rapprochement au plus proche, ici, n'écrirait pas une approximation : il
écrirait un mensonge qui ne se voit plus.

### `plan-moyens` et `plan-offices` NE SONT PAS des copies — ils sortent du chantier

Quatre des six registres doublent le plan des cahiers. **Les deux autres sont des
SOURCES, et rien ne peut les dériver.** Six moyens et dix-sept offices n'existent
nulle part ailleurs ; **quarante-huit numéros M/O sont cités par les actions des
cahiers**, qui ne les définissent jamais. On ne dérive pas d'un vide : ces deux
registres restent **tenus à la main**, et la fusion ne les concerne pas. Que
personne ne vienne, dans six semaines, les « régénérer » par symétrie — il n'en
resterait rien.

Chantier séparé, et il est grave : **la numérotation M/O est déjà cassée.**
`M01`–`M08` et `O01` portent trois jeux de sens selon le livre — `plan-moyens`
(⛵ *Les voiles du Gosier* en M01), `nera-moyens` (🚪 *La porte de la Gadoue* en
M01), `emploi-des-moyens` (M01 = « LES DEUX », une troisième grille encore).
Trois univers, un seul espace de numéros : **tout index M/O global est faux
aujourd'hui.** À trancher à part, et pas par un script.

### Les registres dérivés seront plus PAUVRES que les cahiers, et c'est normal

Quatre colonnes de cahier n'ont aucun logis au registre : **`📍 Où`**,
**`⛓️ Dépend de`**, **`🚪 Ce que cela ferme`**, **`📅 Jour dû`**. Une dérivation
naïve les perdrait en silence. Elles ne se perdent pas : elles ne descendent pas.
**Un index n'a pas à tout porter** — il a à dire où la chose est écrite. Le jour
où quelqu'un comparera les deux et criera à la perte d'information, la réponse
est ici : c'est le cahier qu'on lit, et le registre qui pointe.

### Ce qui a été fait le 31e

- **Le cahier a le dernier mot sur le NOM**, dans `couverture.py` — donc aussi
  dans `etat_du_plan.py`, qui importe le même chargeur. Le fantôme du Sanglier
  est mort : `23000` s'affiche désormais partout sous son vrai nom. Zéro pièce
  affiche encore un nom de registre. Le genre, lui, n'est PAS touché : `44001`
  reste une action au registre et un verrou au cahier, parce que c'est une
  collision de numéro et non un nom périmé — elle se tranche par un homme.
- **Dix pièces mortes effacées des registres** : le bloc `2xxx` de « Défense de
  Peyredragon » (repris en `29xxx`), le bloc `3xxx` d'« Alliances du Nord »
  (repris en `33xxx`), et `7011` d'une « ville de Port-Réal » dissoute. Aucune
  n'était désignée de l'extérieur ; le compte de références pendantes n'a pas
  bougé (2, inchangé).
- **`21020` n'a PAS été descendue**, contre la première lecture. Mécaniquement
  c'était le cas d'école : trois actions de cahier la désignent. Mais ces trois
  actions — `21030`, `21031`, `21032` — portent dans leur propre prose la
  mention **« CÉDÉ AU 6000 »**, et le verrou que `21020` ouvre est mot pour mot
  le `6001` d'`affaire-opinion-populaire-port-real`. Descendre la clef, c'eût été
  réécrire dans le cahier un sujet que ses hommes en ont explicitement sorti. Ce
  qu'il faut n'est pas une descente mais un **repointage** de trois actions vers
  une clef `601x` — et lequel des sept est une décision de fiction. `21010` reste
  en place pour la même raison : l'effacer casserait la chaîne de `21020`.

### Les quatre registres sont DÉRIVÉS — `python scripts/couverture.py --registres`

Régénérés depuis les cahiers, titre marqué « calculé », jamais écrits à la main.
`plan-etats-cibles` 124 lignes · `plan-verrous` 278 · `plan-clefs` 264 ·
`plan-actions` 598 — là où les quatre n'en portaient que 98 à eux tous. L'index
dit enfin tout le plan au lieu d'en dire un douzième.

**Quatre colonnes, et une seule de sens** : le numéro, le nom, la définition
(`✅ Ce qui doit être vrai` · `📌 Ce qui est vrai aujourd'hui` · `💡 Le principe` ·
`📝 Ce qu'on fait`), l'affaire. La forme minimale — numéro, nom, affaire — pesait
un dixième et **tuait la recherche par contenu** : « quelle clef parle des
coques » ne rendait plus rien, et c'est ce pour quoi on ouvre un index. Tout le
reste — la preuve, le levé-quand, le prix, la dépendance, l'office, les moyens,
l'avancement, le `📍 Où` — sert à TRAVAILLER, donc reste au cahier.

**Et le vrai gain n'est pas les octets : ce qui reste est ce qui ne bouge presque
jamais.** Un nom et une définition changent rarement — Le Sanglier en a corrigé
cinq en une nuit et c'était un événement. Les colonnes retirées sont les plus
volatiles : un avancement bouge chaque jour, un office à chaque nomination.
**Moins l'index porte de choses qui changent, moins il a d'occasions de mentir.**
C'est la raison qui a fait dériver ces registres, poussée d'un cran.

**`tick.py --verifier` monte la garde** : tout registre qui s'écarte de ce que
les cahiers produisent est signalé, avec le geste de réparation — reporter la
modification dans le cahier, puis relancer. Sans elle, quelqu'un y écrira une
ligne de bonne foi dans six semaines et l'on refera cette nuit à l'identique.

Elle a failli avoir un trou, et c'est la comparaison qui l'a trouvé : **une main
qui retouche un NOM dans l'index y crée une divergence — et la règle de
conservation, qui refuse d'écraser un nom divergent, reproduit alors fidèlement
la retouche.** L'écart se referme sur lui-même. Or le nom est la colonne qui
compte : la faute payée le 30e était un nom. La garde a donc deux sorties — la
structure se compare, **les noms divergents se comptent et se nomment** à chaque
passage. Dix aujourd'hui ; le jour où la liste en portera onze, quelqu'un aura
écrit dans un index. Cinq façons de tricher ont été essayées contre elle — ligne
ajoutée, nom retouché, prose retouchée, colonne ajoutée, titre démarqué — et les
cinq laissent une trace.

**Ce qui n'entre pas dans l'index, et pourquoi :**

- **Les cahiers `nera-*`.** Ce sont ceux d'un AUTRE SIÈGE : le plan de la Néra a
  ses propres index dans `boite-plan-nera`. Verser ses 49 pièces dans l'index de
  la reine mélangerait deux plans que rien ne relie.
- **Les deux premières colonnes se prennent au RANG**, le numéro et le nom, quel
  que soit l'en-tête écrit au-dessus — `charger()` en fait déjà l'hypothèse. Le
  reste se transpose par en-tête : exact, puis les alias explicites, **et rien
  d'autre**. Pas de préfixe, pas d'inclusion, pas d'alias daté.

**Ce que le générateur REFUSE de toucher**, et redit à chaque passage — treize
lignes conservées telles quelles, transposées à la forme neuve pour que deux
formes ne cohabitent pas dans un même tableau :

- **sans cahier** (`21020`, `21010`) — aucune source ne les produit ;
- **genre différent** (`44001`) — un cahier porte bien le numéro, mais d'un autre
  rang : action ici, verrou là. C'est une collision d'adresse, et un homme
  tranche laquelle des deux la garde ;
- **nom divergent** (les dix du diff) — renommage légitime ou numéro recyclé se
  ressemblent trait pour trait et ne se distinguent pas au calcul. Écraser un
  recyclage, ce serait perdre la dernière trace d'une affaire entière.

### `genre_de` lisait la GLOSE et non le titre

Le cahier *L'entrée sans bataille* n'avait pas d'en-têtes fautifs : c'est **notre
lecteur qui se trompait de table.** Sa table « 🗝️ LES CLEFS — par quel mécanisme
**on lève un verrou** » était lue comme une table de VERROUS, parce qu'on
cherchait le mot n'importe où dans le titre et que les verrous passent avant les
clefs dans l'ordre des genres. Cinq clefs comptées en verrous, dans `charger()`
comme partout — d'où cinq « collisions de genre » qui n'existaient pas.

Une glose qui explique à quoi sert la chose **nomme forcément le rang du dessus**
— c'est le propre d'une bonne glose. Le genre se lit donc sur ce qui précède le
tiret, et l'on ne retombe sur la ligne entière que si cette tête ne dit rien
(« 🗝️ Clefs » n'a pas de tiret). Cinq lignes conservées de moins, et cinq pièces
enfin du bon rang partout ailleurs.

Reste **un** cahier hors format, et le générateur le nomme au lieu de deviner :
*Voir venir* écrit « ce qui est vrai **au matin du 30e** ». Pas d'alias daté —
ce sera « du 31e » demain, et le repli assez large pour l'attraper est celui qui
a fait atterrir l'avancement à la place du numéro. Ses verrous ont donc une
définition vide dans l'index ; **le cahier, lui, garde tout.** Aligner l'en-tête
la fera descendre au prochain passage.

**Le prix :** `books.json` passe de 2,65 à 3,08 Mo, +16 %. C'est le prix de la
recherche par contenu, et il a été payé en connaissance de cause.

### Les emblèmes en doublon

Quatre cahiers portent 🗂️ — `Le double feuillet d'Orwyle`, `Ce qu'on fait signer
au roi`, `Le grain payé avant d'être écrit`, `Le bois des tours brûlées`. Dans la
bascule de l'échiquier, une affaire n'est QUE son signe : quatre affaires
indistinguables. Ce sont, et ce n'est pas un hasard, les quatre qui n'ont pas
encore d'ouverture écrite — donc celles qu'aucune autre section ne regarde.
`tick.py --verifier` le signalait déjà ; `etat_du_plan.py --qui` le redit, parce
que c'est là qu'on regarde le plan.

## La gouttière franchissable — et pourquoi il n'y a pas de plateau des affaires

Le plateau s'arrêtait NET au bord du cahier. `pere()` traite un état qui sert un
état d'ailleurs comme une racine — la canopée se coupe sans rien dire —, et la
colonne `⛓️ Dépend de` n'était lue par personne, alors qu'elle porte à elle
seule tout le lien `attend` : **397 actions sur 611 y écrivent un numéro, dont
71 pointent hors du cahier.**

**La question posée était « un échiquier qui n'aurait que les affaires ». La
mesure a répondu non**, et c'est elle qui a décidé, pas le goût :

- **43 jetons, 158 traits de plan** (`sert` 138 · `attend` 48 · `découpe` 9,
  inverses fusionnés). En jetons c'est plus petit que le plus gros plateau
  actuel (56 pièces) ; en traits c'est **3,7 par jeton** contre ~1 ailleurs, avec
  des sommets à 16 voisins (*Le jour d'entrée*, *Entrée et déploiement de
  l'ost*). La règle « survoler allume la chaîne, le reste s'efface » ne sauve
  rien à cette densité : la chaîne d'un jeton de degré 16 est presque tout le
  plateau.
- **`partage` — 523 traits — n'est pas une arête de plan** mais un compte de
  ressource (« on se dispute le même office »). Il ne se dessine jamais.
- **Et surtout : le graphe des affaires BOUCLE quand celui des pièces ne boucle
  pas.** `attend` compte 7 cycles entre affaires et **zéro entre pièces** — 118
  pièces, 73 arcs, **trois rangs**, acyclique. Ouvert pièce à pièce, *Le jour
  d'entrée* ⚔️11039 attend ⚔️41022, et *Ce qui part* ⚔️41221 attend ⚔️11031 :
  quatre actions distinctes, deux cahiers en miroir parfait, aucune boucle.
  **Écraser deux cahiers en deux jetons fabrique un cycle qui n'est nulle part
  dans le plan.** Un plateau des affaires n'aurait pas montré une difficulté du
  monde : il aurait montré son propre écrasement.

D'où le geste retenu : **on ne monte pas d'un étage, on franchit le bord.**

- **Rien sur le damier.** Le calcul se fait pièce par pièce — c'est la seule
  échelle où il soit juste —, mais **rien n'en sort au niveau de la pièce** : on
  agrège, et l'on ne pose pas un signe de plus sur les cases.
- **Une rangée d'emblèmes dans le bandeau**, à côté du titre et de la tirette :
  les affaires à qui celle-ci tient, la plus liée d'abord, six au plus et un
  compte au-delà. Un clic ouvre ce plateau-là. Le survol dit le nom et à quel
  titre on y tient — « 9 pièces de là-bas qu'elle attend, 3 pièces d'ici qu'on y
  attend » —, **en comptes et jamais en pièces nommées** : la pièce exacte se lit
  au cahier, qui est à un clic.
- C'est la première navigation du jeu qui suive le **plan** au lieu d'une liste.
  La tirette aligne quarante et une affaires et ne sait rien de ce qui les relie.

**Deux versions écartées avant celle-là, et les deux méritent d'être écrites.**

1. **Un bandeau de 11×3 px dans la teinte du rang, posé sur le jeton** — première
   chose que le joueur ait dite en l'ouvrant : *je vois pas les liens*. « Muet »
   veut dire sans mot, pas invisible : le fanion fait 9 px de rouge vif et la
   lampe 14 px d'emoji, et l'on voit les deux de l'autre bout du damier.
2. **Un chevron plein, bien visible, un par pièce et par sens** — et là c'était
   l'inverse : ça se voyait très bien, et **ça pourrissait la vue**. Le damier
   porte déjà six teintes de rang, des dalles d'occlusion, des lampes, des
   fanions, des visages et cent traits de chaîne. Un signe de plus n'ajoutait pas
   de la lecture, il en retirait. Et il proposait la mauvaise chose : **remonter
   la chaîne causale d'affaire en affaire, pièce à pièce**, ce que personne ne
   fait à cette échelle.

La leçon tient en une phrase, et elle vaut au-delà de cet écran : **ce qu'on
voulait savoir n'était pas quelle PIÈCE sort, mais à quelles AFFAIRES celle-ci
tient.** Une information sur l'affaire se dit une fois, au chapeau, hors du
damier — jamais répartie sur ses cinquante jetons. C'est la même règle que
« un fait vrai de presque tout le monde va au chapeau », appliquée à la
topologie au lieu des défauts.

**Ce que ça pose aujourd'hui :** *Financement de la campagne* tient à sept
affaires, dont *État chiffré de ce qui est mobilisable* par treize arêtes. Le
graphe entier compte 217 pièces qui sortent de leur cahier — 191 `sert`, 191
`servie`, 82 `attendue`, 76 `attend` —, réduites à une rangée de six emblèmes
par plateau.

**Deux fautes trouvées en chemin, et elles ne se réparent pas au script.**
`découpe` est un lien écrit à la main, et deux paires se disent MÈRE des deux
côtés : *L'entrée au Donjon* (🎯 23000) ↔ *Isolement du Donjon Rouge* (🎯 12000),
et *L'entrée au Donjon* (🔒 23010) ↔ *L'homme de l'intérieur* (🎯 8000). Qui a
cédé ses numéros à qui est une décision de fiction — même règle que partout :
on détecte, un homme tranche.

## Ce que le MJ en fait

**À la reprise.** La feuille de reprise dit où l'on en est ; l'échiquier dit ce
qui manque au plan et chez qui. C'est la matière de la première pensée du
joueur, pas un récapitulatif à lui montrer.

**Avant de faire parler un conseiller.** Ouvrir son affaire et regarder ses
trous, c'est savoir ce qu'il a en tête sans le lui inventer. Un homme qui porte
quatorze verrous sans clef ne parle pas comme un homme dont la chaîne tient.

**Pour peser une décision en scène.** « Même *Murs tenus* acquis ne donnerait pas
*Île tenable* » est le genre de chose qu'un conseil met trois séances à s'avouer
et qu'un regard sur la canopée donne d'un coup.

**Jamais comme un tableau de bord montré au joueur.** Ce qui remonte à la table
passe par une bouche, avec sa manière et son intérêt à dire le chiffre de
travers.

## Ce qu'on sait de travers, à ce jour

- **Deux lecteurs du graphe.** `couverture.py` dérive les trous et les écrit
  dans les cahiers ; la route `/echiquier` les dérive à son tour. La maison a
  pourtant une règle — « un seul lecteur du graphe, une seule vérité ». Les deux
  divergent déjà, et l'écart se mesure : **197 actes ici, 164 là, 126 communs**
  au 30e. `scripts/etat_du_plan.py --comparer` le dit en une commande — c'est le
  garde-fou faute d'avoir pu factoriser les deux. Tant que ce n'est pas tranché,
  ils continueront de s'écarter.
- **La colonne d'état des clefs existait, c'est le lecteur qui était aveugle.**
  On a cru un moment que les cahiers n'en avaient pas. Elle s'y appelle
  `⚖️ Décision` — 201 *retenue*, 29 *à étudier*, 2 *écartée* — quand les
  registres écrivent `⚖️ Retenue`, et `couverture.py` ne connaissait que le
  second : il lisait donc un état pour **zéro clef sur 265**, et « clef retenue
  qu'aucune action ne réalise » ne pouvait plus se déclencher. Un détecteur qui
  ne trouve rien parce qu'il ne lit rien ne se distingue pas d'un plan sain :
  c'est la pire panne possible. Corrigé le 30e — le détecteur trouve 4 cas.
- **Les moyens et offices cités en clair** — *les nouvelles*, *le bourg*, *Mestre
  Gerardys* — lèvent un fanion « absent de son registre » qui n'a aucun pas à
  proposer. Le fait est vrai de **453 actions**, et on le disait deux fois : une
  action nommant un homme était comptée « que personne ne peut porter » ET
  « citée en clair », alors que quelqu'un la porte très bien — ce qui lui manque
  est un NUMÉRO, pas un homme. Le doublon est levé des deux côtés le 30e, et le
  fait est passé au chapeau de l'affaire, compté une fois. Reste la vraie
  question, qui est de données : faut-il écrire 453 numéros d'office, ou
  admettre qu'un office se cite par le nom de son titulaire ?
