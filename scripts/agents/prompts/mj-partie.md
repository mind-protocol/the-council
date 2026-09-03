# La partie — le conseil de guerre joué contre quelqu'un

Manuel du MJ. Ce document dit ce qu'est une partie, comment elle s'écrit, et
comment elle s'applique au monde. Il ne remplace ni la Règle Zéro, ni le
brouillard, ni la discipline d'écriture d'état : il leur donne un amont. En cas
de conflit avec `docs/schema.md`, le schéma a raison.

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
  à personne tant que rien n'est constaté. Tout camp lève, agit et sert ses
  états : il n'y a pas de camp défenseur par nature.
- **Un camp.** La partie en nomme autant qu'elle veut — deux dans la Danse,
  davantage si d'autres maisons entrent au jeu —, chacun tenu par un joueur,
  une tête dépêchée ou le MJ. Le seul nom réservé est 🟠 `arbitre` : hors
  camp, il arbitre, constate, justifie et passe le tour, et ne joue jamais un
  coup de camp. Ce qui s'oppose à une pièce, c'est le camp de sa cible ; les
  « autres camps » sont tous ceux qui ne sont pas le sien.
- **Un état.** Ce qui doit être vrai, constatable : « la porte de la Rivière
  est acquise ». Jamais une action.
- **Un blocage.** Ce que l'autre camp oppose à un état ou à un maillon précis :
  une garnison dedans, un Guet payé, une bête au-dessus de la rade. **Un blocage
  est posé par l'autre camp, jamais par soi-même.** Ce qu'on ignore n'est pas
  un blocage, c'est un trou, écrit *à mesurer*.
- **Une clé.** Ce qui lève un blocage : un résultat précis (« Vhagar n'est pas
  au-dessus de la rade ce matin-là ») ou le mécanisme qui le produit. Une clé
  engage des pièces.
- **Un maillon.** Une action : une ressource, un gars nommé qui fait un truc
  précis, un résultat. Les maillons réalisent une clé. Une clé sans maillon est
  une affirmation ; elle est valide tant que personne n'exige la chaîne.
- **Une ressource.** Tout ce qu'une clé peut engager : un corps, une bête, une
  troupe, un lieu tenu, un objet, une bourse, un canal. **Tout se demande et
  s'arbitre, les personnes comprises** : une ligne, une source, et l'arbitre
  dit où elle est. Ce n'est pas une formalité, c'est ce qui met la pièce au
  grand livre avec son lieu et sa date.
- **Le grand livre.** La liste des ressources posées, avec pour chacune son
  camp, son lieu, son nombre, son état (libre, engagée, gelée, détruite) et sa
  source. Il vit dans la partie elle-même : chaque ressource y entre par une
  ligne.
- **Le deck.** Les états qu'un camp met en jeu, **dix au plus**. Le reste du
  plan existe, dort, et n'est touché par aucun coup ni aucun saut. **Un deck
  peut être un calendrier** : des états datés (un ost devant une ville, une
  bête qui arrive, un prétendant qui se proclame), chacun entrant au deck au
  tour de sa date, comme une pièce qui arrive. C'est ce qui donne à un camp
  tenu sans appel une existence, et au saut de temps de quoi tourner.

---

## 3. Les coups

Un coup est une ligne. Il n'y en a que dix-sept sortes, et un camp ne joue qu'un
coup par tour. Ne comptent pas : les arbitrages, et ce qui ne coûte rien —
demander, justifier, consigne. **Viser compte** : un état cible se pose un par
un, comme les autres pièces, un par tour — c'est ce qui lisse la charge, dix
états d'un bloc ne se lisent pas. Le greffe **signale** un second coup dans le
tour, il ne le refuse pas : c'est au MJ de tenir la règle, et de savoir quand
il la casse.

| Coup | Qui | Ce qu'il fait | Ce qu'il coûte |
|---|---|---|---|
| 🎯 **viser** | un camp | pose un état dans son deck ; avec `arrive_tour`, l'état est daté et n'entre au deck qu'à ce tour (la place est tenue d'avance) | un coup, et une place du deck |
| 🃏 **sortir** | un camp | sort un état du deck ; ses pièces restent engagées où elles sont | un coup |
| 📦 **demander** | un camp | demande une ressource : id, lieu, nombre, tenant | rien tant que l'arbitre n'a pas parlé |
| ⚖️ **arbitrer** | l'arbitre | accorde, corrige (nombre, lieu, tenant), reporte (« arrive dans N tours »), ou refuse, **avec sa source**. Sur une destruction suspendue, « accorde » juge la portée bonne et lève la suspension ; « refuse » la fait tomber | — |
| 🔒 **bloquer** | l'autre camp | pose un blocage sur un état, un maillon, une clé ou une destruction adverse, avec la pièce qui le produit ; posé sur une destruction, il la **pare** | la pièce, engagée |
| 🗝️ **lever** | un camp | pose une clé contre un blocage, avec les pièces engagées ; sans blocage à ouvrir, elle **réalise** un état (`sert`) et est tenue quand l'arbitre le constate vrai | les pièces, engagées |
| ⚔️ **agir** | un camp | pose un maillon sous une clé, une destruction ou un blocage à soi : qui, avec quoi, résultat ; ou le réalise. Le maillon écrit lève la suspension d'un « justifier » — **et ne compte pas pour le tour quand il y répond** | rien de plus que ce que la clé engage |
| ❓ **justifier** | l'autre camp ou l'arbitre | exige la chaîne d'une clé, d'un blocage ou d'un état, ou la portée d'une destruction ; la pièce visée passe *en suspens* et ne prévaut plus | rien |
| 💥 **détruire** | un camp | vise une ressource adverse ; à la réalisation elle sort du grand livre pour toujours, avec ce qu'elle engageait | la pièce qui frappe, engagée, puis **gelée un tour** |
| 🔄 **retourner** | un camp | vise une ressource adverse comme une destruction (même fenêtre, mêmes parades, même arbitrage) ; à la réalisation elle **change de camp**, libre, et ce qu'elle tenait tombe | ce qu'on y met, engagé, puis **gelé un tour** |
| 🗑️ **retirer** | un camp | retire une clé, un blocage, une destruction à soi, ou une ressource ; les pièces libérées sont **gelées deux tours** | deux tours à découvert |
| 🔧 **reconstruire** | un camp | rend une ressource détruite si elle se reconstruit (une porte, des coques, des engins ; pas un pendu) ; **revient dans deux tours** | deux tours |
| ➕ **réarmer** | un camp | ajoute une pièce à une clé ou un blocage qui tient déjà, sans le retirer ; ni le texte ni la cible ne changent | un coup, pas de gel |
| ⏸️ **passer** | un camp | ne joue rien | le tour |
| 📋 **consigne** | un camp | avant un saut : ce que fait chaque pièce si elle est visée (tenir, retirer, justifier par Untel) | rien |
| ✅ **constater** | l'arbitre | dit un état vrai ou faux, avec sa source ; vrai, il fait tomber ce qui le bloquait et tient ce qui le servait. Sur la racine, il donne le trône | — |
| ⏭️ **tour** | l'arbitre | passe le tour : arrivées, dégels, atterrissages, parades tenues, états datés, **états constatables**, camps muets, branches mortes | deux jours du monde |

### Les règles de validité

1. **Une pièce engagée l'est jusqu'à ce que la clé qui l'engage soit retirée,
   écartée ou tenue.** Une deuxième clé qui la veut est « sans ressource ».
   Meleys ne montre pas la côte la veille et ne tient pas la rade le matin.
2. **Pas de ressource, pas de coup.** Une clé ou un blocage qui n'engage rien
   n'est pas un coup ; le greffe le refuse. Un blocage sans pièce tiendrait
   « rien en face » et ne pourrait jamais tomber par sa pièce.
3. **Un blocage est posé par l'autre camp.** Le miroir est automatique : la clé
   d'un camp est le blocage de l'autre, et le repli l'écrit des deux côtés.
4. **Le défenseur tient par défaut.** Sur un maillon où les deux camps ont une
   pièce, rien ne bouge tant qu'un coup ne le tranche pas.
5. **Justifier ne punit pas, et ne se répète pas.** Une clé sans maillon est
   valide jusqu'à ce qu'un coup exige sa chaîne. **Une pièce ne se justifie
   qu'une fois** : le coup est gratuit, il ne doit pas être répétable. L'arbitre
   peut jouer « justifier » sur un état dès l'ouverture (« qui s'assied, et
   comment arrive-t-elle ? »), une fois. **Un blocage se justifie comme une clé**
   (mesure du duel de 50 tours) : suspendu, il ne prévaut plus tant que son camp
   n'a pas écrit son maillon — sans quoi le défenseur affirmait gratuitement.
   **Et la réponse est aussi gratuite que la question** : le maillon écrit en
   réponse à un « justifier » ne compte pas pour le tour (le greffe le marque
   `repond`). Sans cela, chaque clé contestée coûtait deux tours à qui l'avait posée.
6. **La portée se refuse sur pièce.** Une destruction ou un blocage que la pièce
   ne peut pas atteindre (présence, moyen, distance) est refusé en une ligne.
   C'est le seul endroit où le « comment » remonte de force.
7. **Un heurt se tranche à la table, avec sa source.** Quand deux pièces se
   touchent, l'arbitre `tranche` comme il arbitre une ressource, dans le même
   ordre et en s'arrêtant au premier qui répond : ce que l'état sait (les
   nombres au grand livre, les fiches, les cahiers) ; ce qu'un mécanisme
   produit (une tête dépêchée, une main, une chaîne déjà écrite) ; et à défaut
   ce qu'il comble à froid, une fois, d'après le canon et le plausible. Il n'y
   a pas de table de force : un `tranche` porte `nombre` pour ce qui sort du
   grand livre, `detruit` pour ce qui meurt des deux côtés, et `motif`.
   **Une parade est un heurt, et elle tient UN tour** : un blocage posé sur une
   destruction la retient au passage du tour où elle devait atterrir ; au
   passage du tour suivant, si l'arbitre n'a pas tranché, la frappe **tombe**
   (le défenseur tient par défaut, règle 4) — l'écran est rendu sans gel, la
   pièce qui frappait rentre gelée un tour. Sans cela, une bête est restée
   neuf tours figée au-dessus d'une autre, et personne n'a rien joué.
8. **Une ressource demandée et engagée par rien deux tours après son arrivée est
   une branche morte.** Signalée, pas punie — et jamais pour une pièce qui a
   figuré une fois dans un `engage`, un `avec`, un `qui` ou une `consigne`.
9. **Dix états par deck.** Entrer ou sortir un état est un coup. **Un état constaté vrai
   ne tient plus de place** : il reste dans l'arbre avec ses effets, mais il a
   fait son office. Sans cela, dix états acquis coûtaient dix coups à sortir.
14. **Le greffe liste ce qui est constatable, l'arbitre constate.** Au passage
    du tour, `constatables` nomme les états au deck, non constatés, dont tous
    les blocages sont tombés ou levés par une clé qui prévaut — ou qu'une clé
    valide sert sans que rien ne les bloque. C'est une liste, pas un verdict :
    constater reste à l'arbitre, avec sa source. Et `inactifs` nomme un camp
    qui n'a rien joué d'autre que passer trois tours de suite — signalé, pas
    puni, comme une branche morte.
10. **Un blocage tombe avec sa pièce.** Quand la pièce qui porte un blocage est
    retirée ou détruite, le blocage tombe. Une clé dans le même cas est
    « sans ressource » jusqu'à ce qu'on la réarme. **Et une clé dont tous les
    blocages sont tombés est *tenue*** : elle a fait son office, ses pièces
    reviennent libres, sans gel — on ne paie pas deux tours pour un blocage que
    l'adversaire a levé lui-même. Elle ne se réarme plus ; ce qu'on veut encore
    poser là se pose à neuf. Même sort pour **un blocage posé sur une destruction**
    (une bête entre la frappe et la colonne) : la frappe tombée ou réalisée, il
    tombe et rend sa pièce sans gel. Et **un état constaté vrai** fait tomber ce
    qui le bloquait et tient ce qui le servait.
12. **Une destruction qui atterrit sans arbitrage est totale.** L'arbitre qui veut
    un heurt partiel (règle 7) le **tranche avant** le passage du tour où elle
    atterrit ; après, la pièce est sortie du grand livre, et une correction est un
    coup de plus.
13. **Un retournement est une destruction qui ne tue pas.** Même fenêtre,
    mêmes parades (bloquer, justifier, retirer la cible), même arbitrage.
    Réalisé : la pièce passe au camp qui l'a retournée, libre ; ce qu'elle
    tenait tombe ; ce qu'on y a mis revient, gelé un tour.
11. **Un id n'a qu'un objet.** Un blocage, une clé, un maillon ou une
    destruction dont l'id est déjà pris est refusé : le fichier est append-only,
    une réécriture silencieuse y serait invisible. Une correction est un coup de
    plus (retirer, reposer sous un autre id).

---

## 4. Le temps

- **Le tour** est l'unité du joueur : un coup de chaque camp. Il ne voit que des
  tours : « arrive dans deux », « gel deux », « prête au tour 15 ».
- **Un tour vaut deux jours du monde.** Constante, écrite ici et dans
  `scripts/noyau/partie_greffe.py`, portée par l'arbitre seul. Le monde avance
  de deux jours par tour joué ou sauté.
- **Les délais d'arrivée**, table de l'arbitre, jamais un jugement :

| Délai | Sens | Exemples |
|---|---|---|
| 0 | déjà là | une garnison dans ses murs, une bête en ville, une bourse |
| 1 | il faut préparer (deux jours) | un dragon n'importe où dans les terres de la Couronne ; une coque, une traversée ; un affrètement |
| 2 | quelques jours | une réponse de banneret ; une bête depuis Harrenhal par le nord ; un ost sur deux jours de route |
| 4 | une semaine | un ost sur huit jours de route ; un passage de la route du sel |
| 8 et plus | très long | Villevieille, le Nord, le Val ; deux passages du sel et une seconde oreille ; retourner un homme depuis rien |

- **Une pièce en route s'engage.** Une clé, un blocage ou une destruction
  peut engager une pièce qui n'est pas encore arrivée : la pièce est réservée
  dès ce tour, visible de l'adversaire, et la clé est **« prête au tour N »**,
  celui où toutes ses pièces sont là. Elle ne lève rien avant ; l'adversaire
  peut la justifier ou la bloquer dès qu'elle est posée. Poser tôt est un
  engagement, pas une avance.
- **Les gels** : deux tours après un retrait, un tour après une destruction
  réalisée, deux tours pour une reconstruction.
- **Une destruction est toujours une menace datée.** Posée au tour t, elle
  arrive au plus tôt en t+1 et n'atterrit qu'en entrant en t+2 : le camp visé a
  toujours son tour pour bloquer, justifier ou retirer. Reportée par l'arbitre,
  elle atterrit au tour dit.

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
{"n":4,"tour":1,"camp":"noir","coup":"demander","id":"ost-noir","lieu":"peyredragon","nombre":1200,"tenu_par":"steffon-darklyn"}
{"n":5,"tour":1,"camp":"arbitre","coup":"arbitrer","sur":"ost-noir","verdict":"accorde","arrive_tour":3,"nombre":1200,"motif":"26013 et 26202 : douze cents de levée, Steffon commande la marche"}
{"n":3,"tour":1,"camp":"vert","coup":"bloquer","id":"49001","sur":"49000","texte":"Tient le Donjon Rouge avec sa garnison","engage":["garnison-donjon"]}
{"n":2,"tour":1,"camp":"vert","coup":"viser","id":"v-criston","arrive_tour":4,"texte":"L'ost de Criston est devant Sombreval"}
{"n":6,"tour":2,"camp":"noir","coup":"lever","id":"49010","ouvre":"49001","texte":"Fait entrer l'armée par la porte de la Rivière","engage":["ost-noir","steffon-darklyn"]}
{"n":7,"tour":2,"camp":"vert","coup":"justifier","sur":"49010","texte":"Par où douze cents hommes entrent-ils dans un château fermé ; la chaîne depuis les fosses"}
{"n":8,"tour":3,"camp":"noir","coup":"agir","id":"49021","realise":"49010","qui":"rhaenyra","avec":["syrax"],"texte":"Vole jusqu'à Port-Réal","etat":"a_faire"}
{"n":9,"tour":3,"camp":"noir","coup":"agir","id":"49021","etat":"faite","texte":"Réalisée : elle est au-dessus de la ville"}
{"n":14,"tour":6,"camp":"vert","coup":"detruire","id":"70040","cible":"barques-selm","engage":["galeres-royales"],"texte":"Coule les deux barques de nuit"}
{"n":15,"tour":7,"camp":"noir","coup":"retirer","id":"barques-selm","gel_tours":2,"texte":"Rentre les barques au port"}
{"n":16,"tour":8,"camp":"noir","coup":"retourner","id":"70041","cible":"larys","engage":["harrenhal-promis"],"texte":"Achète Larys avec Harrenhal"}
{"n":28,"tour":6,"camp":"noir","coup":"reconstruire","id":"coques-3","revient_tour":8,"texte":"Affrète trois coques au banc de l'Est"}
{"n":50,"tour":20,"camp":"arbitre","coup":"constater","etat":"200","verdict":"vrai","motif":"aucun blocage ouvert ; la porte est passée"}
```

Le champ `engage` nomme des ids du grand livre. Un id inconnu du grand livre
rend la ligne « sans ressource ». **Un arbitrage vise un id** (la demande, la
destruction, la clé ou le blocage qu'il tranche), jamais un numéro de ligne :
les numéros glissent dès qu'un coup est refusé. Un « tranche » peut porter
`detruit: [...]` pour un heurt mutuel, et `nombre` pour une destruction
partielle. Le champ `sur` d'un blocage peut être un état
ou un maillon : c'est là que se lit « posé sur quel maillon ». L'arbitre écrit
toujours `motif` avec sa source (numéro de pièce, fichier d'état, canon).

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

