# La partie — le conseil de guerre joué contre quelqu'un

Manuel du MJ. Ce document dit ce qu'est une partie, comment elle s'écrit, et
comment elle s'applique au monde. Il ne remplace ni la Règle Zéro, ni le
brouillard, ni la discipline d'écriture d'état : il leur donne un amont. En cas
de conflit avec `docs/schema.md`, le schéma a raison.

**Les règles elles-mêmes ne vivent plus ici** (7 septembre 2026) : elles vivent
dans [`docs/regles-partie.md`](../../../docs/regles-partie.md), une adresse
chacune (`R8 · preseance-blocage`), et le code les porte en marqueur
`# regle: <slug>` que `python scripts/regles.py --verifier` tient à jour dans
les deux sens. Ce manuel les CITE (`→ R8 · preseance-blocage`) et dit ce qu'un
livre de règles ne dit pas : pourquoi elles existent, et la partie qui les a
fait naître.

---

## 1. Présentation — pourquoi une partie

Le plan du conseil tient dans des cahiers d'affaire, et ces cahiers ne
rencontrent jamais rien qui leur résiste : ils se prouvent par leurs propres
lignes. Le joueur n'a donc aucun retour sur ce qu'il met en place, et le monde
n'a pas de réalité contre laquelle son plan se cogne. Une partie répare ces
deux manques avec un seul mécanisme : **un adversaire qui a le droit de dire
« prouve-le », et des pièces pour le dire.**

Une partie est un jeu de pièces logiques entre deux camps, arbitré par le MJ.
Un camp affirme, l'autre bloque avec une pièce, exige la chaîne, ou détruit.
Rien ne se résout par un calcul de durées ni par un jet : tout se résout par
« as-tu une pièce libre pour répondre, et as-tu écrit le chemin ». Le « comment »
(les actions avec leurs ressources) reste sous chaque clé, et il ne remonte que
quand quelqu'un l'exige.

Ce qu'elle achète :

- **Le concret par la pression.** Chaque exigence de chaîne fait apparaître un
  maillon plus petit, et le blocage suivant frappe ce maillon-là. Le plan se
  construit contre quelqu'un, pas dans le vide.
- **Le retour au joueur.** L'état de la partie dit à tout instant ce qui tient,
  ce qui est suspendu, ce qui a été détruit. C'est ce que le mestre relit.
- **Moins d'appels.** On ne dépêche un homme que quand un coup l'exige, avec une
  question qui a un objet et une date. Un camp tient par défaut avec ce qu'il
  a ; on n'appelle une tête que pour un coup qui n'est pas « tenir ».
- **Une réalité qui se construit.** Chaque ressource demandée et arbitrée est un
  fait du monde, daté, sourcé. Le grand livre est la réalité fondamentale, et
  c'est le jeu qui le remplit.

Ce qu'elle n'est pas : un simulateur de durées, un rendu pour le joueur, une
liste de sujets. Le joueur ne voit jamais la partie. Il voit des gens qui lui
disent des choses, avec le retard et la déformation du brouillard.

---

## 2. Les objets

- **Le trône.** Un seul, racine de tout. Les deux camps le visent : l'état
  « la reine est assise sur le Trône de Fer » et l'état « le roi reste assis »
  sont le même objet vu des deux côtés. **Chaque camp pose sa racine** — son
  état qui ne sert aucun autre — et tout état d'un camp sert sa racine,
  directement ou par un parent. Le trône est au camp dont la racine a été
  constatée vraie en dernier ; un constat faux sur cette racine le lui retire ;
  à personne tant que rien n'est constaté (→ R28 · trone-derniere-racine).
  Tout camp lève, agit et sert ses états : il n'y a pas de camp défenseur par
  nature.
- **Un camp.** La partie en nomme autant qu'elle veut — deux dans la Danse,
  davantage si d'autres maisons entrent au jeu —, chacun tenu par un joueur,
  une tête dépêchée ou le MJ. Le seul nom réservé est 🟠 `arbitre` : hors
  camp, il arbitre, constate, justifie et passe le tour, et ne joue jamais un
  coup de camp (→ R31 · seul-l-arbitre). Ce qui s'oppose à une pièce, c'est le
  camp de sa cible ; les « autres camps » sont tous ceux qui ne sont pas le
  sien (→ R6 · blocage-par-un-autre-camp).
- **Un état.** Ce qui doit être vrai, constatable : « la porte de la Rivière
  est acquise ». Jamais une action.
- **Un blocage.** Ce que l'autre camp oppose à un état ou à un maillon précis :
  une garnison dedans, un Guet payé, une bête au-dessus de la rade. **Un blocage
  est posé par l'autre camp, jamais par soi-même** (→ R6). Ce qu'on ignore
  n'est pas un blocage, c'est un trou, écrit *à mesurer*.
- **Une clé.** Ce qui lève un blocage : un résultat précis (« Vhagar n'est pas
  au-dessus de la rade ce matin-là ») ou le mécanisme qui le produit. Une clé
  engage des pièces.
- **Un maillon.** Une action : une ressource, un gars nommé qui fait un truc
  précis, un résultat. Les maillons réalisent une clé. Une clé sans maillon est
  une affirmation ; elle est valide tant que personne n'exige la chaîne
  (→ R13 · cle-sans-maillon-affirmation).
- **Une ressource.** Tout ce qu'une clé peut engager : un corps, une bête, une
  troupe, un lieu tenu, un objet, une bourse, un canal. **Tout se demande et
  s'arbitre, les personnes comprises** : une ligne, une source, et l'arbitre
  dit où elle est (→ P2 · ressource-demandee-puis-arbitree). Ce n'est pas une
  formalité, c'est ce qui met la pièce au grand livre avec son lieu et sa date.
- **Le grand livre.** La liste des ressources posées, avec pour chacune son
  camp, son lieu, son nombre, son état (libre, engagée, gelée, détruite) et sa
  source. Il vit dans la partie elle-même : chaque ressource y entre par une
  ligne.
- **Le deck.** Les états qu'un camp met en jeu, **dix au plus** (→ R26 ·
  dix-etats). Le reste du plan existe, dort, et n'est touché par aucun coup ni
  aucun saut. **Un deck peut être un calendrier** (→ R27 · deck-calendrier) :
  des états datés (un ost devant une ville, une bête qui arrive, un prétendant
  qui se proclame), chacun entrant au deck au tour de sa date, comme une pièce
  qui arrive. C'est ce qui donne à un camp tenu sans appel une existence, et
  au saut de temps de quoi tourner.

---

## 3. Les coups

Un coup est une ligne. Il n'y en a que seize sortes, et un camp ne joue qu'un
coup par tour (→ R30 · un-coup-par-tour). Ne comptent pas : les arbitrages, et
ce qui ne coûte rien — demander, justifier. **Viser compte** : un état cible se
pose un par un, comme les autres pièces, un par tour — c'est ce qui lisse la
charge, dix états d'un bloc ne se lisent pas. Le greffe **signale** un second
coup dans le tour, il ne le refuse pas : c'est au MJ de tenir la règle, et de
savoir quand il la casse (→ P4 · deck-en-jouant).

Chaque coup a sa règle au livre (`C1` à `C13` pour les camps, `A1` à `A4`
pour l'arbitre, `V1` à `V4` pour ce que fait chaque verdict) ; la table
ci-dessous dit ce qu'il fait et ce qu'il coûte, et renvoie à son adresse.

| Coup | Qui | Ce qu'il fait | Ce qu'il coûte |
|---|---|---|---|
| 🎯 **viser** → coup-viser | un camp | pose un état dans son deck ; avec `arrive_tour`, l'état est daté et n'entre au deck qu'à ce tour (la place est tenue d'avance) | un coup, et une place du deck |
| 🃏 **sortir** → coup-sortir | un camp | sort un état du deck ; ses pièces restent engagées où elles sont | un coup |
| 📦 **demander** → coup-demander | un camp | demande une ressource : id, une phrase, un nombre s'il fractionne. Le lieu et le tenant se disent dans la phrase ; l'arbitre les écrit | rien tant que l'arbitre n'a pas parlé |
| ⚖️ **arbitrer** → coup-arbitrer, verdict-sur-* | l'arbitre | accorde, corrige (nombre, lieu, tenant), reporte (« arrive dans N tours »), ou refuse, **avec sa source**. Sur une destruction suspendue, « accorde » juge la portée bonne et lève la suspension ; « refuse » la fait tomber | — |
| 🔒 **bloquer** → coup-bloquer | l'autre camp | pose un blocage sur un état, un maillon, une clé ou une destruction adverse, avec la pièce qui le produit ; posé sur une destruction, il la **pare** (→ R11) | la pièce, engagée |
| 🗝️ **lever** → coup-lever | un camp | pose une clé contre UN blocage (deux verrous, deux clefs), avec les pièces engagées ; sans blocage à ouvrir, elle **réalise** un état (`sert`) et est tenue quand l'arbitre le constate vrai | les pièces, engagées |
| ⚔️ **agir** → coup-agir | un camp | pose un maillon sous une clé, une destruction ou un blocage à soi : qui, avec quoi, résultat — écrit quand c'est fait, sans état. Le maillon écrit lève la suspension d'un « justifier » — **et ne compte pas pour le tour quand il y répond** (→ R14c) | rien de plus que ce que la clé engage |
| ❓ **justifier** → coup-justifier, arbitre-justifie | l'autre camp ou l'arbitre | exige la chaîne d'une clé, d'un blocage ou d'un état, ou la portée d'une destruction ; la pièce visée passe *en suspens* et ne prévaut plus (→ R14) | rien |
| 💥 **détruire** → coup-detruire | un camp | vise une ressource adverse ; à la réalisation elle sort du grand livre pour toujours, avec ce qu'elle engageait (→ R18, R21) | la pièce qui frappe, engagée, puis **gelée un tour** |
| 🔄 **retourner** → coup-retourner | un camp | vise une ressource adverse comme une destruction (même fenêtre, mêmes parades, même arbitrage) ; à la réalisation elle **change de camp**, libre, et ce qu'elle tenait tombe (→ R22) | ce qu'on y met, engagé, puis **gelé un tour** |
| 🗑️ **retirer** → coup-retirer | un camp | retire une clé, un blocage, une destruction à soi, ou une ressource ; les pièces libérées sont **gelées deux tours** (→ R23, T5) | deux tours à découvert |
| 🔧 **reconstruire** → coup-reconstruire | un camp | rend une ressource détruite si elle se reconstruit (une porte, des coques, des engins ; pas un pendu) ; **revient dans deux tours** (→ R25) | deux tours |
| ➕ **réarmer** → coup-rearmer | un camp | ajoute une pièce à une clé ou un blocage qui tient déjà, sans le retirer ; ni le texte ni la cible ne changent | un coup, pas de gel |
| ⏸️ **passer** → coup-passer | un camp | ne joue rien | le tour |
| ✅ **constater** → coup-constater | l'arbitre | dit un état vrai ou faux, avec sa source ; vrai, il fait tomber ce qui le bloquait et tient ce qui le servait (→ R12). Sur la racine, il donne le trône (→ R28) | — |
| ⏭️ **tour** → coup-tour | l'arbitre | passe le tour : arrivées, dégels, atterrissages, parades tenues, états datés, **états constatables**, camps muets, branches mortes (→ T3) | deux jours du monde |

### Les règles de validité — pourquoi elles existent

Le manuel ne tient plus sa propre liste. **Chaque règle a son adresse dans
`docs/regles-partie.md`** (§4, `R1` à `R31`), le code la porte en marqueur, et
`python scripts/regles.py --verifier` refuse qu'une règle et son code se
perdent de vue. Ce qui reste ici, c'est ce qu'un livre de règles ne dit pas :
la raison, et la partie qui a fait naître la règle.

- → **R1 · engage-jusqu-a-chute** — Meleys ne montre pas la côte la veille et
  ne tient pas la rade le matin : une pièce ne fait qu'une chose à la fois.
- → **R2 · pas-de-ressource-pas-de-coup** — un blocage sans pièce tiendrait
  « rien en face » et ne pourrait jamais tomber par sa pièce. Le greffe le
  refusait pour la clé ; pour le blocage depuis le 3.9 (annexe B du livre).
- → **R6 · blocage-par-un-autre-camp** — ce qu'on ignore de son propre plan
  n'est pas un blocage, c'est un trou. Le miroir est automatique : la clé d'un
  camp est le blocage de l'autre.
- → **R7 · defenseur-tient** — sur un maillon où les deux camps ont une pièce,
  rien ne bouge tant qu'un coup ne tranche pas. C'est ce qui permet de ne
  dépêcher une tête que pour un coup qui n'est pas « tenir ».
- → **R14 · justifier-suspend**, **R14b · justifier-une-fois**, **R14c ·
  reponse-gratuite**, **R15 · blocage-suspendu-ne-prevaut-plus**, **A3 ·
  arbitre-justifie** — gratuit, donc pas répétable. Un blocage se justifie
  comme une clé (mesure du duel de 50 tours : sans quoi « le roi est chez les
  Hightower » tenait un état sans que personne puisse exiger par quelle
  poterne il était sorti — le blocage était la pièce la moins chère du jeu, et
  la plus forte). Et la réponse ne compte pas, sans quoi chaque clé contestée
  coûtait deux tours à qui l'avait posée. L'arbitre peut jouer « justifier »
  sur une racine dès l'ouverture (« qui s'assied, et comment arrive-t-elle ? »).
- → **R17 · portee-refusee-sur-piece** — le seul endroit où le « comment »
  remonte de force.
- → **R24 · heurt-tranche-a-la-table**, **R11 · parade-un-tour** — pas de
  table de force : un `tranche` porte `nombre`, `detruit` et `motif`, par
  l'ordre de l'arbitrage d'une ressource (→ S1). Une parade est un heurt, et
  elle tient UN tour : sans cela, une bête est restée neuf tours figée
  au-dessus d'une autre et personne n'a rien joué (duel-50, Vhagar sur Meleys,
  parée par Caraxes au tour 9).
- → **R5 · branche-morte** — signalée, pas punie ; et jamais pour une pièce qui
  a servi une fois (le guetteur et le septon d'essai-1).
- → **R26 · dix-etats** — un état constaté vrai ne tient plus de place : sans
  cela, dix états acquis coûtaient dix coups à sortir.
- → **R29 · greffe-liste-arbitre-constate** — constater cessait de dépendre de
  l'attention de l'arbitre ; `inactifs` nomme un camp muet trois tours, comme
  une branche morte (le Vert de duel-50 : cinq états visés, aucune clé).
- → **R10 · blocage-tombe-avec-sa-piece**, **R9 · cle-tenue**, **R12 ·
  etat-vrai-libere** — on ne paie pas deux tours pour un blocage que
  l'adversaire a levé lui-même ; un constat libère les pièces des deux côtés
  (pont-et-moulin : le Vert a récupéré ses gars trop tard, le front suivant
  était déjà ouvert).
- → **R20 · atterrissage-total** — « 1100 · DÉTRUITE », les deux à la fois :
  un `tranche` d'après coup ne rend rien de partiel, une correction est un coup
  de plus.
- → **R22 · retournement-realise**, **C9 · coup-retourner** — Larys s'est
  vendu au tour 22 et restait « une pièce vert », inengageable ; il a fallu
  poser une pièce neuve et le même homme figurait deux fois au grand livre
  (duel-50, défaut 2).
- → **O1 · un-id-un-objet** — le fichier est append-only, une réécriture
  silencieuse y serait invisible. Une correction est un coup de plus (retirer,
  reposer sous un autre id).
- → **R30 · un-coup-par-tour** — contrôle gradué, signalé et pas refusé,
  parce que l'ouverture est le moment où le MJ la casse sciemment.
- → **R29b · constatable-attend-un-tour**, **R14d ·
  question-sur-etat-sans-reponse** — déclarées `sans code` au livre : la
  première est une pratique de l'arbitre (laisser un tour à l'autre camp avant
  de constater), la seconde un défaut d'écran connu (une question sur un état
  reste affichée toute la partie).

---

## 4. Le temps

- **Le tour** est l'unité du joueur : un coup de chaque camp (→ T1 ·
  trait-ordre-d-entree). Il ne voit que des tours : « arrive dans deux », « gel
  deux », « prête au tour 15 ».
- **Un tour vaut deux jours du monde** (→ T2 · tour-deux-jours). Constante,
  écrite dans `scripts/noyau/partie_greffe.py`, portée par l'arbitre seul. Le
  monde avance de deux jours par tour joué ou sauté.
- **Les délais d'arrivée**, table de l'arbitre, jamais un jugement (→ T4 ·
  delais-d-arrivee, sans code : c'est l'arbitre qui date) :

| Délai | Sens | Exemples |
|---|---|---|
| 0 | déjà là | une garnison dans ses murs, une bête en ville, une bourse |
| 1 | il faut préparer (deux jours) | un dragon n'importe où dans les terres de la Couronne ; une coque, une traversée ; un affrètement |
| 2 | quelques jours | une réponse de banneret ; une bête depuis Harrenhal par le nord ; un ost sur deux jours de route |
| 4 | une semaine | un ost sur huit jours de route ; un passage de la route du sel |
| 8 et plus | très long | Villevieille, le Nord, le Val ; deux passages du sel et une seconde oreille ; retourner un homme depuis rien |

- **Une pièce en route s'engage** (→ R3 · piece-en-route-s-engage). Une clé,
  un blocage ou une destruction
  peut engager une pièce qui n'est pas encore arrivée : la pièce est réservée
  dès ce tour, visible de l'adversaire, et la clé est **« prête au tour N »**,
  celui où toutes ses pièces sont là. Elle ne lève rien avant ; l'adversaire
  peut la justifier ou la bloquer dès qu'elle est posée. Poser tôt est un
  engagement, pas une avance.
- **Les gels** (→ T5 · gels) : deux tours après un retrait, un tour après une
  destruction réalisée, deux tours pour une reconstruction.
- **Une destruction est toujours une menace datée** (→ R18 · menace-datee).
  Posée au tour t, elle arrive au plus tôt en t+1 et n'atterrit qu'en entrant
  en t+2 : le camp visé a toujours son tour pour bloquer, justifier ou retirer.
  Reportée par l'arbitre, elle atterrit au tour dit.

---

## 5. Les écritures

### 5.1 Le fichier

Une partie est un fichier append-only, **une ligne par coup**, jamais réécrit :

```
etat/parties/<id>.jsonl
```

`<id>` nomme la partie (« prise-de-port-real-129-5 »). Une partie se rejoue en
repliant les lignes jusqu'à N. Une correction est un coup de plus (retirer,
reposer), jamais une ligne modifiée.

### 5.2 La ligne

Champs communs : `n` (rang), `tour`, `camp` (le nom du camp, ou `arbitre` ;
les exemples ci-dessous viennent de la Danse, à deux camps `noir` et `vert`),
`coup`, `texte` (une phrase, verbe d'abord). Puis selon le coup :

```jsonl
{"n":1,"tour":1,"camp":"noir","coup":"viser","id":"49000","texte":"La reine est assise sur le Trône de Fer","sert":null}
{"n":4,"tour":1,"camp":"noir","coup":"demander","id":"ost-noir","nombre":1200,"texte":"Douze cents hommes de levée à Peyredragon, sous Steffon Darklyn"}
{"n":5,"tour":1,"camp":"arbitre","coup":"arbitrer","sur":"ost-noir","verdict":"accorde","arrive_tour":3,"nombre":1200,"motif":"26013 et 26202 : douze cents de levée, Steffon commande la marche"}
{"n":3,"tour":1,"camp":"vert","coup":"bloquer","id":"49001","sur":"49000","texte":"Tient le Donjon Rouge avec sa garnison","engage":["garnison-donjon"]}
{"n":2,"tour":1,"camp":"vert","coup":"viser","id":"v-criston","arrive_tour":4,"texte":"L'ost de Criston est devant Sombreval"}
{"n":6,"tour":2,"camp":"noir","coup":"lever","id":"49010","ouvre":"49001","texte":"Fait entrer l'armée par la porte de la Rivière","engage":["ost-noir","steffon-darklyn"]}
{"n":7,"tour":2,"camp":"vert","coup":"justifier","sur":"49010","texte":"Par où douze cents hommes entrent-ils dans un château fermé ; la chaîne depuis les fosses"}
{"n":8,"tour":3,"camp":"noir","coup":"agir","id":"49021","realise":"49010","qui":"rhaenyra","avec":["syrax"],"texte":"Vole jusqu'à Port-Réal : elle est au-dessus de la ville"}
{"n":14,"tour":6,"camp":"vert","coup":"detruire","id":"70040","cible":"barques-selm","engage":["galeres-royales"],"texte":"Coule les deux barques de nuit"}
{"n":15,"tour":7,"camp":"noir","coup":"retirer","id":"barques-selm","gel_tours":2,"texte":"Rentre les barques au port"}
{"n":16,"tour":8,"camp":"noir","coup":"retourner","id":"70041","cible":"larys","engage":["harrenhal-promis"],"texte":"Achète Larys avec Harrenhal"}
{"n":28,"tour":6,"camp":"noir","coup":"reconstruire","id":"coques-3","revient_tour":8,"texte":"Affrète trois coques au banc de l'Est"}
{"n":50,"tour":20,"camp":"arbitre","coup":"constater","etat":"200","verdict":"vrai","motif":"aucun blocage ouvert ; la porte est passée"}
```

Le champ `engage` nomme des ids du grand livre. Un id inconnu du grand livre
rend la ligne « sans ressource ». **Un arbitrage vise un id** (→ X1 ·
arbitrage-vise-un-id — la demande, la destruction, la clé ou le blocage qu'il
tranche), jamais un numéro de ligne : les numéros glissent dès qu'un coup est
refusé. Un « tranche » peut porter
`detruit: [...]` pour un heurt mutuel, et `nombre` pour une destruction
partielle. Le champ `sur` d'un blocage peut être un état
ou un maillon : c'est là que se lit « posé sur quel maillon ». L'arbitre écrit
toujours `motif` avec sa source (numéro de pièce, fichier d'état, canon).

**Un motif ne fait jamais le menu du camp d'en face** (→ S2 ·
motif-sans-menu, sans code : le greffe exige le motif, il ne le lit pas). Il
dit pourquoi la
portée est bonne, ce que la pièce atteint, et ce qui la ferait tomber — jamais
la liste des coups que l'autre camp peut jouer contre elle. Dans charmed-2, le
motif n°55 (« il atterrit si rien ne se met entre : Phoebe qui touche Shane,
Paige qui l'entend pour ce qu'il est, ou le sort des trois dit avant ») a
énuméré trois parades, et la joueuse a joué la première trois lignes plus loin
(n°58). La partie `le-jeu-lui-meme-moi` (7 septembre 2026) a fait de cette
ligne un verrou sur toute la thèse : un coup écrit par l'arbitre dans son motif
avant d'être joué n'est plus tout à fait un coup du joueur. Ce qui ferait tomber
la pièce s'écrit en une clause générale (« tombe si la cible est parée ou si
l'état qu'elle vise est constaté vrai avant »), pas en noms de pièces. L'aide au
joueur, quand on veut la donner, va au banc de touche, jamais au greffe.

### 5.3 Ce qui se dérive, jamais s'écrit

- **L'état de la partie** : le trône et qui le tient ; sous lui, chaque état du
  deck dans l'arbre de ce qu'il sert, avec ses blocages colorés par le camp qui
  y prévaut et les maillons réalisés ; les clés tenues ; les états datés à
  venir ; les pièces gelées avec leurs tours ; les arrivées ; le trait.
- **Le grand livre** : replié depuis les lignes `demander`, `arbitrer`,
  `lever`, `retirer`, `detruire`, `reconstruire`.
- **Les cahiers d'affaire** : une vue. Le repli produit les tables 🎯 🔒 🗝️ ⚔️
  d'un volume d'affaire au format de `docs/books.md`, et le damier les lit sans
  rien savoir de la partie. Un état du deck a son cahier ; un état dormant garde
  le sien tel quel.

### 5.4 La présentation d'un tour

Après chaque tour, la partie se présente en clair, et c'est ce que produit
`python scripts/partie.py <partie> --presenter [--depuis-tour N]`. La forme est
fixe :

- un titre de tour, avec ce qui est arrivé, ce qui s'est dégelé, ce qui a
  atterri, les parades tenues, les états datés entrés au deck, **ce qui est à
  constater**, et un camp muet s'il y en a un ;
- un coup par ligne : **emoji du camp (chaque camp a le sien), emoji du coup,
  numéro — un verbe en gras, ce que ça fait**, les pièces engagées, et pour l'arbitre son verdict et
  sa source ; les noms en clair, jamais un id nu ;
- l'analyse du tour, courte : la qualité des coups, ce qu'ils changent ;
- l'état, un seul trône, la racine de chaque camp, chaque maillon coloré par
  le camp qui y prévaut, les gelés, les arrivées, le trait.

```
⚫🗝️ 6 — Lève 3 en faisant entrer l'armée par la porte de la Rivière. Engage l'armée, Steffon.
🟢❓ 7 — Suspend 6 : par où entrent-ils, la chaîne depuis les fosses. N'engage rien.

État
👑 Trône — tenu par 🟢
← 🟢 🗝️ 6 armée dans le Donjon, suspendue par ❓ 7
← 🟢 🔒 3 Donjon tenu, garnison dedans
Trait à ⚫.
```

Un maillon est coloré par le camp qui y prévaut à cet instant, pas par celui
qui l'a posé.


## 6. Le banc de touche — le coach qui commente la partie

La section 5.4 laisse un trou et le nomme : « l'analyse du tour, à écrire par le
MJ ». `--presenter` rend ce qui s'est passé ; il ne rend jamais ce que ça VAUT.
Ce trou-là se remplit par une voix, et cette voix a un nom au flux : **🎙️ Le
banc de touche**.

Elle a été jouée de mémoire pendant six parties, ce qui l'a fait dériver d'un
tour à l'autre. La forme est fixée ici pour qu'elle ne dérive plus.

### 6.1 Qui c'est, et ce qu'il n'est pas

**Un coach, pas un conteur.** Il ne raconte pas ce qui arrive, il dit ce que ça
coûte et ce que ça achète. La question qu'il se pose à chaque coup est
« qu'est-ce que ce joueur vient de gagner, et qu'est-ce qu'il vient de payer
sans le voir ? »

**Il est HORS FICTION.** Il ne parle à personne dans le monde, aucun personnage
ne l'entend, il n'a ni corps ni lieu. Il sort en items `coulisses`, donc le
temps ne bouge pas, et **rien de ce qu'il dit n'entre dans `etat/`**. La Règle
Zéro ne le concerne pas : il ne fait parler personne, il commente un plateau.

**Il est CLAIR ET UTILE, et c'est toute sa consigne de style.** Il ne fait pas
de suspense, il ne ménage aucun effet, il ne pose pas de question rhétorique
dont il a la réponse. Un commentaire dont le joueur ne tire rien est un
commentaire raté, même bien écrit.

**Il ne voit pas de brouillard, et c'est voulu** (`docs/partie.md`, « le
brouillard ne s'applique pas ici »). Le plateau est public des deux côtés : il
a donc le droit de dire ce que l'autre camp tient, ce qu'il a en main et ce qui
lui arrive dans N jours. **Ce qu'il n'a pas le droit de dire, c'est ce qui n'a
pas été joué** — un coup à venir, une intention d'arbitre non tranchée, un
verdict qu'il devine. Il commente le livre, jamais l'avenir.

### 6.2 L'ouverture — présentation, enjeux, spoilers

**Trois items au premier tour d'une partie, et à chaque fois qu'un joueur
revient après une longue absence.** Un par idée, dans cet ordre.

1. **LA PARTIE.** Ce qui se joue, en deux phrases : les deux camps nommés avec
   leur emoji, l'énoncé de chaque racine, et l'horloge — combien de jours en
   tout, et pourquoi cette date-là ferme la partie.
2. **LES ENJEUX.** Ce que chaque camp doit établir pour gagner, et la
   difficulté propre de chacun. Pas symétrique : dire lequel des deux a la
   tâche la plus dure, et pourquoi. C'est l'item qui apprend la partie à
   quelqu'un qui arrive.
3. **LES SPOILERS.** Ce qu'il sait et que le joueur n'a pas regardé : les
   pièces libres d'en face, ce qui arrive à quelle date, les questions de
   l'arbitre restées sans réponse, les branches mortes. **Annoncé comme tel** —
   le mot « spoilers » se dit, avec son emoji, pour que le joueur sache qu'il
   lit la position complète et non la sienne.

### 6.3 Le commentaire d'un coup

**Un item par coup qui mérite un mot, et pas un par coup joué.** Un coup de
routine ne se commente pas ; deux coups qui se répondent se commentent
ensemble.

La ligne s'ouvre TOUJOURS par les deux emojis du greffe, dans cet ordre : **le
camp, puis le coup**. Ce sont ceux de `partie_greffe` et d'aucune autre table —
🎯 viser · 📦 demander · ⚖️ arbitrer · 🔒 bloquer · 🗝️ lever · ⚔️ agir ·
❓ justifier · ➕ rearmer · 🔄 retourner · 💥 detruire · 🗑️ retirer ·
🔧 reconstruire · ⏸️ passer · ✅ constater · ⏭️ tour · 🃏 sortir.

Puis, dans le même item et dans cet ordre :

- **Ce qui a été fait**, en clair, avec le titre de la pièce ou de l'état —
  jamais un id nu. Les mots du joueur sont cités quand ils sont bons ; on ne
  les paraphrase pas pour les améliorer.
- **Ce que ça change**, c'est-à-dire l'analyse : le verrou qui tombe, la pièce
  qui se libère, la date qui se rapproche, l'état qui devient constatable.
- **Le prix**, s'il y en a un, et il y en a presque toujours un : une pièce
  immobilisée, une question qu'on s'expose à recevoir, une porte qu'on ferme.

**Le verdict est explicite.** « Le meilleur coup de leur partie jusqu'ici »,
« coup double », « ça, c'est la vraie question ». Un coach qui ne note pas ne
sert à rien. Un mauvais coup se dit mauvais, avec sa raison, sans ménagement et
sans mépris.

### 6.4 Le flux — comment ça sort

Le commentaire se rédige dans `etat/parties/_commentaire-mj.json`, un tableau
d'items, puis part d'un coup — **vers les sièges de CETTE partie, et eux
seuls** : ceux que `sieges` de `etat/parties/<id>.json` déclare, tous camps
confondus.

```bash
python scripts/partie.py <id> --coach etat/parties/_commentaire-mj.json          # pousse
python scripts/partie.py <id> --coach etat/parties/_commentaire-mj.json --voir   # montre les commandes, ne pousse rien
```

Jamais `append_flux.py … --pour tous` : à deux parties ouvertes en même temps,
le coach de l'une tombait dans le fil des joueurs de l'autre. `--coach` refuse
en clair une partie sans `sieges` déclarés et ne pousse alors rien — déclare
les sièges de chaque camp d'abord.

```json
{"type": "coulisses", "qui": "🎙️ Le banc de touche", "delai_s": 3,
 "texte": "❓ ET ILS CONTRE-ATTAQUENT PROPREMENT — ils exigent la chaîne du pré-enregistrement : « sur quel site ? avec quels échantillons ? » 👏 Ça, c'est la vraie question, celle qui tue les réplications bâclées. La clef de la réplication est suspendue le temps qu'elle réponde."}
```

- **Le fichier est un brouillon, jamais un état.** Il s'écrase à chaque tour et
  ne se commite pas.
- **`delai_s` de 2 à 4**, plus long quand l'item précédent est dense : c'est le
  temps de lecture, pas un effet de rythme.
- **Trois à sept items par tour.** En dessous, le tour n'avait pas besoin d'un
  coach ; au-dessus, on redit le plateau au lieu de l'éclairer.
- **De deux à cinq phrases par item, une seule idée.** Deux idées dans un item,
  c'est deux items.

### 6.5 La forme de la phrase

- **Les capitales marquent le coup, pas l'émotion.** « LES AUTEURS PUBLIENT »,
  « ET ELLE DÉTAILLE » : elles ouvrent l'item et disent l'action. On n'en met
  pas trois par item.
- **Un emoji ouvre, un ou deux ponctuent.** Ils portent du sens — 🎯 ce qui
  vise juste, ⏳ ce qui attend, ❄️ ce qui est immobilisé, 👏 ce qui est bien
  joué, ⚠️ ce qui va coûter. Jamais de décoration.
- **Les chiffres sont dits, pas suggérés.** Combien de jours, combien de
  pièces gelées, quel jour tombe l'échéance.
- **On tutoie le plateau, on vouvoie le joueur.** « À vous, docteure » clôt une
  série ; c'est la seule adresse directe autorisée.

### 6.6 Les deux items qui ferment un tour

**L'HORLOGE, toujours.** « 🕰️ JOUR 12 SUR 20 » : où l'on en est, ce que chaque
camp tient à cette minute, et la prochaine échéance datée. C'est l'item que le
joueur relit quand il revient, et le seul qui soit obligatoire.

**LE CONSEIL, quand il y a quelque chose à conseiller.** « SI J'ÉTAIS À SA
PLACE, TROIS CHOSES DANS CET ORDRE » — deux ou trois gestes, ordonnés, avec la
raison de l'ordre. C'est un avis de coach et il s'assume comme tel : le joueur
en fait ce qu'il veut, et le coach a le droit de se tromper. **Ce n'est pas un
menu** : on ne numérote pas des options exclusives, on dit ce qu'on ferait.

### 6.7 Les interdits

- **Jamais un coup qui n'a pas été joué**, ni une intention d'arbitre non
  tranchée, ni un verdict deviné.
- **Jamais une parole de personnage.** Le coach commente ; s'il faut la voix
  d'un homme, on le dépêche.
- **Jamais une écriture dans `etat/`** — ni `paroles`, ni `actes`, ni la
  moindre ligne au jsonl de la partie. Il lit, il ne joue pas.
- **Jamais l'ironie sur le joueur.** On note un coup, on ne se moque pas de
  celui qui l'a posé.
- **Jamais un item qui ne dit que ce que le plateau montre déjà.** Si l'écran
  le rend, le coach se tait.
