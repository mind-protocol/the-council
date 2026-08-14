# La criticité — ce que le plan perd si ce pas-là rate

`scripts/criticite.py`. Note de fonctionnement pour le MJ : le POURQUOI, ce que
les nombres disent et ne disent pas, et l'erreur qu'ils évitent. Le raisonnement
long est dans l'en-tête du script, qui reste la source ; ce document dit ce
qu'on en fait à la table.

**Tous les chiffres cités ici sont datés du 13 août 2026** (1er jour de la 4e
lune, an 129, au monde). Une autre session joue pendant qu'on lit : refaire la
mesure avant de s'appuyer dessus coûte une commande.

---

## La question du matin n'est pas « qu'est-ce que ça débloque »

La mesure qui vient d'elle-même est la **portée** : la masse d'états cibles
qu'un pas sert en aval. Elle répond « c'est gros derrière », et ce n'est pas la
question. Trois actions qui réalisent la même clef ont chacune une portée
énorme et ne valent rien séparément — on peut en perdre deux sans rien perdre du
tout. La question est **contrefactuelle** : on retire la pièce, on recalcule ce
qui reste atteignable, on fait la différence. Un pas substituable tombe alors à
zéro tout seul, sans qu'on ait eu à le diviser par son nombre de frères.

Les deux nombres s'impriment côte à côte, et **l'écart entre eux EST la
redondance**. Portée haute et perte nulle : quelqu'un d'autre peut le faire.
Portée nulle : le pas ne mène nulle part, et c'est une autre maladie.

Le troisième nombre, **attendu**, est d'une autre nature : le poids de ce qui,
dans un AUTRE cahier, nomme cette pièce dans son `⛓️ Dépend de`. **Un saut,
jamais une cascade.** C'est un homme à prévenir, pas un travail à sécuriser — et
la section suivante dit pourquoi cette distinction a coûté la moitié du plan.

**Ce que la perte ne sait pas faire, et il faut le savoir avant de s'en servir :
elle ne discrimine pas à l'intérieur d'une chaîne.** Les actions sont
conjonctives — il les faut toutes —, donc les onze pas d'une même colonne
portent tous la même valeur. Elle classe les AFFAIRES, pas les gestes. Demander
à la colonne « perte » par lequel des onze commencer, c'est lui demander ce
qu'elle n'a jamais prétendu dire ; c'est `etat_du_plan.py --du` qui tient les
dates, et l'œil qui tranche entre les deux colonnes.

**Un verrou se mesure aussi**, et l'y avoir laissé longtemps dehors était une
faute de vocabulaire prise pour une règle. On ne « rate » pas un verrou : on le
lève. Mais l'arithmétique est identique au signe près du récit, et la colonne se
lit alors **« tant qu'il tient »** — ce que cet empêchement coûte au plan. Sans
lui, le registre des verrous était le seul des quatre à n'afficher aucun
chiffre, alors que c'est LA table où l'on vient demander lequel de ces
empêchements coûte le plus cher. Un état cible, lui, n'a pas de perte : il a son
poids et son atteignabilité, et c'est tout ce qu'on lui demande.

**Un seul nombre est saisi à la main dans tout le calcul** : le poids des états
cibles, dans `etat/poids-etats.json`. Le fichier n'existe pas aujourd'hui — tout
vaut donc 1, et le script le dit en tête de chaque sortie (« poids saisis à la
main : 0 »). C'est le seul endroit où un jugement humain sur ce qui compte a sa
place ; tout le reste se dérive du graphe, donc ne peut pas mentir plus
longtemps que lui.

Au 13 août : **1320 pièces, 138 états cibles dont 118 atteignables**, 812 pas
dont la perte coûte quelque chose, 168 substituables, 202 orphelins. En écartant
ce qui est déjà fait (`--restant`) : 768, 162, 191.

## Le `⛓️ Dépend de` requalifié — et ce que la confusion coûtait

**À l'intérieur d'un cahier, « dépend de » ORDONNE un travail** : on ne charge
pas avant d'avoir affrété. C'est un prérequis dur, il bloque. **D'un cahier à
l'autre, il SIGNALE une coordination** : « l'autre nous doit ça ». Ce n'est pas
une horloge, et le traiter comme telle propage la dépendance à toute l'affaire,
de proche en proche, jusqu'à boucler.

La mesure, au 13 août : **424 dépendances internes, 72 qui traversent**. Ces
soixante-douze suffisent à nouer **90 pièces de 19 cahiers en une seule grappe
circulaire**, et à faire tomber les états cibles atteignables de **118 à 86**.
Une session qui aurait pris le raccourci — « une dépendance est une dépendance »
— aurait conclu que le tiers du plan est mort, et l'aurait dit à la reine.

Le script tourne donc en `--dep interne` par défaut, et l'on peut voir l'autre
lecture d'une commande :

```
python scripts/criticite.py --dep toutes    # dedans ET dehors bloquent
python scripts/criticite.py --dep interne   # le défaut : dedans bloque, dehors se compte
python scripts/criticite.py --sans-dep      # la colonne ignorée
```

Ce qui traverse ne disparaît pas pour autant : il ressort en colonne
**« attendu »**, et l'on somme la criticité propre de ceux qui attendent, pas
leur nombre — dix pièces sans conséquence pèsent moins qu'une seule qui tient un
état.

## Les cercles — la seule trouvaille que les détecteurs ne pouvaient pas faire

Une action qui dépend du verrou qu'elle est censée lever ne se lèvera jamais, et
**aucun des six détecteurs de `couverture.py` ne le voit, parce que chaque ligne
prise seule est bien formée**. Ça ne se trouve qu'en essayant d'ATTEINDRE
quelque chose : le point fixe s'arrête, et l'on cherche pourquoi. C'est le même
enseignement que le test de traversée — on valide un graphe en essayant d'aller
quelque part, pas en comptant ses composantes.

Ce sont les composantes fortement connexes du graphe de prérequis. Le script les
imprime **avant** le classement, et ce n'est pas de la mise en page : **tant
qu'un cercle tient, tout ce qui pend derrière vaut zéro**, et le classement
mentirait par omission.

Au 13 août, en `--dep interne`, il en reste **un seul** : `🎯 28000 → 🎯 40000 →
🎯 5000` — le coût connu attend le commandement, qui attend le compte, qui
attend le coût. Trois états cibles, trois cahiers, et personne ne l'avait vu. En
`--dep toutes`, la grande grappe des 90 pièces s'y ajoute, ce qui est l'autre
façon de dire la même chose que la section précédente.

`python scripts/criticite.py --pourquoi 100` déroule la chaîne d'une pièce
inatteignable jusqu'à la boucle, et marque l'endroit où elle se referme.

## Où ça se voit

**La page `/pas`** — six onglets : Les pas · Les idées · Les cercles · Par
affaire · Par homme · Les états cibles. C'est la vue de travail.

**Trois colonnes ajoutées aux registres, dans les livres du jeu** — `📉 Perte`,
`📡 Portée`, `⏳ Attendu`, posées sur les seuls tableaux d'adresse et seulement
sur les lignes qui ont un score. Elles ne sont PAS écrites dans `books.json` et
ne doivent jamais l'être : `couverture.py` régénère les registres à quatre
colonnes exactement pour qu'ils ne portent rien de volatil, et un score bouge à
chaque action cochée. Le calcul se fait à l'ouverture, l'écran l'ajoute par
numéro. **Le volume qu'on copie, qu'on imprime, qu'on emporte reste celui qui
est écrit — c'est la lecture qui est augmentée, pas le livre.**

**L'onglet `⚖️ Les pas`**, un volume synthétique de l'étagère, au même titre que
« Vos notes » : personne ne l'écrit dans la fiction, il ne se range dans aucun
coffret, il se refait à chaque dessin et n'a donc rien à périmer. Il existe
parce que la question « par quoi commencer » se pose **le nez dans les
registres**, et qu'un lien qu'on ne voit pas depuis l'endroit où l'on travaille
n'est pas un lien. Sans criticité chargée il n'apparaît pas du tout, ce qui vaut
mieux qu'un onglet vide.

## Le classement des idées

`missions_de()` savait déjà proposer, par affaire, ce qu'il faudrait écrire pour
que la chaîne tienne — « afin d'atteindre X, faire Y aurait effet Z ». Ce qui
est neuf est qu'**une idée porte désormais la criticité de la pièce qu'elle
vise**. On n'a pas réécrit les détecteurs : une seconde définition du trou, et
les deux divergeraient dans la semaine. On prend les idées telles qu'elles
sortent et l'on y colle un nombre. **Une idée ne vaut pas par la gravité de son
défaut : elle vaut par ce que la pièce qu'elle débloque tient.**

**Les ruptures restent en tête, et il faut dire pourquoi, sinon quelqu'un
« corrigera » ce tri dans six semaines.** Une rupture est une chaîne cassée au
milieu — une action qui désigne une clef qui n'existe dans aucun cahier. Comme
elle ne remonte à aucun état cible, sa pièce vaut **zéro au contrefactuel**,
mécaniquement et justement : on ne peut pas chiffrer ce qui manque. Trier sur le
seul score les enterrerait donc TOUTES, au fond de la liste, alors que c'est le
test disqualifiant du guide — une action dont la remontée est impossible n'a pas
de raison stratégique démontrée. Le score classe ce qui est bien formé ; il ne
peut rien dire de ce qui ne l'est pas.

## La réserve d'un homme dépêché

`scripts/depecher.py:ses_trous()` montre cinq trous à l'homme qu'on envoie
vivre sa journée. **Cette réserve est désormais rangée par criticité** (perte +
attendu) au lieu du barème `force()` écrit à la main, qui mélangeait deux axes
et ne savait rien du plan hors du cahier qu'il regardait. Si le calcul échoue,
on retombe sur `force()` et l'homme part quand même : une dépêche ne tombe
jamais pour un défaut de cette greffe.

Ce qui n'a pas bougé d'un pouce, et qui compte plus que le tri :

- **RIEN NE S'ÉCRIT DANS `intentions.json`.** Le script détecte ; les hommes
  décident.
- **On donne la matière, jamais la décision.** Ce ne sont pas des ordres de la
  reine : ce sont les trous de son propre cahier, qu'un homme compétent voit
  comme on voit un compte qui ne tombe pas juste.
- **Il prend ce que sa journée peut porter**, et laisse le reste. Le nombre de
  trous montrés est borné à cinq pour cette raison, pas pour tenir dans l'écran.

### Les deux canaux du dehors — ce qui ne passait par aucun chemin

Le routage ne tenait que sur `tenu_par`, et c'était trop étroit : un homme
répond de pas écrits sous SON office dans le cahier d'un autre, et il tient des
moyens que d'autres engagent sans que son nom soit sur la ligne. `--charge`
mesurait ces deux colonnes depuis toujours sans que rien ne les lui porte —
Gerardys aveugle à 54 %, lord Corlys à 100 %. `sa_charge_ailleurs()` et
`on_lattend()` les portent désormais, et `criticite.charge_de()` est la porte :
une seule définition, jamais une seconde côté dépêche.

**On a d'abord essayé de les faire passer par `missions_de`, et ça donne zéro.**
268 missions sur 44 cahiers, aucune ne tombant sur l'office d'un autre : un trou
vise un verrou ou une clef, et ni l'un ni l'autre ne porte d'office. « Sa charge
ailleurs » n'est pas un ensemble de défauts, c'est un ensemble d'**affectations**
— l'unité est le pas non fait, pas le trou.

**A et B se font, C se répond**, et c'est la borne qui tient tout. Un homme
n'écrit jamais dans le cahier d'un autre : sur sa charge il va voir le tenant,
sur ce qu'on lui tire il envoie un mot. C'est ce qui permet d'élargir ce qu'un
homme VOIT sans toucher à ce qu'est un cahier — la question que `depecher.py`
laissait ouverte depuis le début.

Trois places au sien, un bloc de trois lignes par canal, groupé par cahier et
jamais listé pas par pas : Gerardys porte 133 pas qui tirent sur ses moyens, et
un tri fusionné de cinq lignes ferait disparaître son propre cahier sous la
charge des autres.

Deux gardes à ne pas perdre : le filtre « non fait » est **au demandeur**, pas
dans la mesure — `--charge` dit comment un homme pèse sur le plan, pas ce qui
lui reste ; et si `lecteurs` apparaît un jour sur une affaire (les 43 portent
`null` aujourd'hui), ces deux canaux doivent le respecter — on donne le pas et
le cahier où il tombe, jamais le contenu d'un volume qu'il n'a pas le droit
d'ouvrir.

**La mesure devient fausse en même temps qu'elle est réparée.** Une fois les
deux canaux branchés, `aveugle` ne mesure plus rien pour un titulaire : il ne
reste à 100 % que les *sources* — un homme qui tient un moyen et rien d'autre,
qu'on ne dépêche pas — et le siège du joueur, dont le canal est la `pensee`. Les
trois colonnes de gauche gardent leur sens ; la quatrième est en train de
devenir un vestige.

## CE DISPOSITIF VAUT POUR LES JOUEURS AUTANT QUE POUR LES PNJ

C'est la partie de ce document qu'on oublie, parce qu'un tableau de charge a
l'air d'un outil de régie. Il ne l'est pas : **un personnage joueur tient des
cahiers comme les autres** — `tenu_par` porte son identifiant — **et répond d'un
office.** Sa réserve existe donc, se calcule pareil, et ne pas la regarder ne la
fait pas disparaître : elle produit seulement un joueur qui décide sans savoir
ce que sa propre maison attend de lui.

Au 13 août : Rhaenyra tient *Une présence à demeure dans Port-Réal*, un cahier,
**16 de criticité sur 11 pas**, rien ailleurs, rien qu'on lui tire. Aurore
Inchauspé en tient trois — *Ce qui part, et par où*, les deux retournements —,
**387 de criticité sur 92 pas dans ses cahiers, 86 de plus qui tombent sur son
office O03 dans le cahier d'un autre, 105 encore où l'on tire sur un moyen
qu'elle tient sans que son nom soit sur la ligne : un tiers de ce qui la
concerne ne lui parvient par aucun chemin.** Ce sont les chiffres d'un
conseiller ordinaire, et c'est exactement le point.

### Comment ça lui parvient sans casser la fiction

Trois canaux, et **pas un de plus. Jamais un menu, jamais un tableau, jamais
« le plan recommande ».** Aucun de ces trois n'est une règle neuve : ils sont
déjà écrits dans le manuel, et il s'agit de s'y raccorder plutôt que d'inventer
une quatrième porte.

**Par un battement de `pensee`.** C'est le canal principal, et le mode « Penser »
est fait pour lui : le manuel y demande déjà « ce qu'elle sait qui compte
maintenant » avec ses chiffres et ses horloges, « ce qui s'offre », « ce que
chacune coûte », et **« ce qu'elle ignore et qui déciderait »**. Les trous de son
propre cahier tombent dans cette dernière case sans qu'on force rien. Elle les
voit comme un homme compétent voit un compte qui ne tombe pas juste — pas comme
une liste de tâches servie par une machine. La formulation est la sienne : « je
n'ai toujours pas de nom pour tenir la porte, et c'est la seule chose qui
manque », jamais « le pas 7020 est le plus débloquant ». Le contenu vient du
calcul ; **la phrase vient d'elle.**

**Par la bouche d'un conseiller qui rapporte.** C'est ce que le manuel dit déjà
de la boucle des mains, et ça vaut ici mot pour mot : le joueur ne voit pas un
compteur, il voit quelqu'un qui lui dit un chiffre, avec sa manière et son
intérêt à le dire de travers. Le brouillard s'applique au RAPPORT, pas au
calcul. Et « Ce qui est délégué ne remonte plus » garde toute sa force : un trou
qui tombe dans le domaine d'un délégataire **ne remonte pas au joueur** parce
que le script l'a trouvé — il est déjà fait quand le joueur l'apprend, en une
ligne, au passé.

**Par les livres qu'il peut ouvrir lui-même.** Son cahier est sur l'étagère, et
l'onglet `⚖️ Les pas` avec lui. Voir ci-dessous.

### L'onglet `⚖️ Les pas` est ouvrable par le joueur : c'est VOULU, et voici la borne

Il faut trancher, parce que la question va revenir. **La réponse est oui, c'est
voulu — et la fuite réelle est ailleurs que là où on la craint.**

Ce que l'onglet contient est **le plan de sa propre maison** : les cahiers que
ses gens tiennent, les états qu'elle poursuit, les empêchements qu'on lui a
rapportés. Le brouillard protège ce que le personnage ne peut PAS savoir — les
`intentions`, les allégeances réelles, les positions qui ne lui sont pas
parvenues. Il n'a jamais eu pour fonction de cacher à une reine ce que ses
propres clercs ont écrit dans ses propres registres, et le lui cacher
produirait la faute que le manuel nomme ailleurs : lui faire découvrir une
évidence de son métier.

**Ce qui n'est pas légitime, ce n'est pas le contenu, ce sont les nombres.**
Personne dans la fiction ne parle en « perte 15 » ; c'est une vue de machine, et
elle n'a pas de bouche. D'où la borne, qui est dure : **le joueur peut lire la
colonne, le MJ ne la cite JAMAIS.** Aucun PNJ n'énonce un score, aucune `pensee`
n'en porte un, aucune narration ne s'y adosse. Ce qui passe en fiction est ce
que le nombre a fait comprendre, dit en mots de la maison — « tout tient à ce
nom d'officier », « ces trois-là, on peut en perdre deux ». Le nombre est un
instrument de lecture posé sur la table du joueur, comme la table peinte est un
instrument de travail : on s'en sert, on ne le récite pas.

**Et il y a une vraie fuite, qu'il faut nommer au lieu de la couvrir.** Le
volume se construit à partir de TOUTES les pièces chargées, sans filtre de
siège ni de `lecteurs` : au 13 août, 42 affaires, dont les cahiers de la Néra
qui appartiennent à un autre siège et des cahiers de PNJ que le personnage ne
tient pas. Rhaenyra, qui n'en tient qu'un, y lit les quarante-deux. Ce n'est pas
une décision, c'est un filtre qui n'a pas été écrit — et tant qu'il ne l'est
pas, **le MJ traite l'onglet comme une vue de régie que le joueur peut ouvrir à
ses risques, et ne s'appuie sur rien de ce qu'il y aurait vu.** Ce qui entre
dans la fiction reste ce qui est passé par une pensée, une bouche ou un cahier
qu'il tient.

### Ça sert aussi à juger la partie, côté MJ

Un joueur dont les cahiers portent une criticité élevée et **zéro pas fait
depuis trois lunes est une information sur la partie**, pas un défaut du script.
Ça se lit sans ambiguïté : soit le monde ne lui a jamais dit ce qui pendait à
lui — et c'est une faute de MJ, réparable par un battement de pensée ou un
conseiller qu'on dépêche —, soit il l'a su et a choisi autre chose, et alors
c'est du jeu : il faut que ça lui coûte, visiblement, par un empêchement qui
mord et non par un rappel à l'ordre. `--charge <son id>` sépare les deux cas en
une commande, parce qu'il distingue ce qu'il voit de ce qu'aucun chemin ne lui
porte.

Le même tableau juge le casting hors joueur, et c'est là qu'il fait mal :
Gerardys est **aveugle à 82 %** de ce qui le concerne (141 vus contre 185 sur
son office ailleurs et 496 tirés sur ses moyens), Corlys et Jacaerys à 100 % —
ils ne tiennent aucun cahier et le plan attend d'eux 62 et 94 de criticité. Ce
n'est pas un bug de routage : c'est une mesure de ce que `tenu_par` ne sait pas
faire, prise avant d'élargir la réserve d'un homme aux affaires qu'il ne tient
pas, ce qui redéfinirait ce qu'est un cahier.

## Ce qu'on sait de travers, à ce jour

- **`etat/poids-etats.json` n'existe pas**, donc les 138 états cibles pèsent
  tous 1 — la capitale tenue vaut autant qu'un point de débarquement. Tous les
  classements ci-dessus sont exacts à cette hypothèse près, et elle est fausse.
  C'est le seul endroit du dispositif qui attend un jugement humain, et il
  l'attend toujours.
- **Un score dérivé de ce qui est ÉCRIT mesure la rédaction autant que
  l'importance.** L'*Ambassade du Nord* porte 420 de criticité sur 39 pas ; elle
  est peut-être la plus critique du plan, ou seulement la mieux rédigée. Le
  nombre de pas s'affiche à côté pour que le gonflement se voie, et le script le
  dit sous sa propre table. Ce n'est pas une garde, c'est un aveu.
- **La colonne « perte » ne départage pas deux pas d'une même chaîne.** Redit
  ici parce que c'est la mauvaise lecture la plus naturelle, et la seule qui
  fasse prendre une décision de travers.
- **Le prix ne rentre pas dans le calcul, et n'y rentrera pas.** La colonne
  `💰 Ce qu'elle coûte` est de la prose, portée par la clef, et l'on ne divise
  pas par de la prose. Elle s'imprime telle quelle sous les premières lignes ;
  l'échéance non plus n'y entre pas, parce que deux nombres mous multipliés font
  une fausse précision.
- **Les jointures entre registres sont devinées, et dites en clair** : « moi »
  aux registres des moyens est la reine, les titres et les gloses au tiret sont
  coupés, un prénom seul se replie sur le nom complet quand l'un préfixe
  l'autre. Chacune de ces devinettes a déjà produit un fantôme — ser Steffon
  compté en deux moitiés dont aucune n'était la sienne, le castellan absent du
  tableau. Elles sont réparées ; d'autres restent à trouver.
- **649 de criticité pèsent sur 181 pas dont l'office est nommé en clair sans
  numéro**, et 164 sur 55 pas qui n'ont pas d'office du tout. Ce second chiffre
  est le seul qui n'ait personne pour le porter.
