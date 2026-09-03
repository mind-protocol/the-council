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
  question qui a un objet et une date. Le camp adverse tient par défaut avec ce
  qu'il a ; on n'appelle une tête verte que pour un coup qui n'est pas « tenir ».
- **Une réalité qui se construit.** Chaque ressource demandée et arbitrée est un
  fait du monde, daté, sourcé. Le grand livre est la réalité fondamentale, et
  c'est le jeu qui le remplit.

Ce qu'elle n'est pas : un simulateur de durées, un rendu pour le joueur, une
liste de sujets. Le joueur ne voit jamais la partie. Il voit des gens qui lui
disent des choses, avec le retard et la déformation du brouillard.

---

## 2. Les objets

- **Le trône.** Un seul, racine de tout. Les deux camps le visent : l'état
  « la reine est assise sur le Trône de Fer » et l'état « le trône est contrôlé
  par nous » sont le même objet vu des deux côtés. Tout état de la partie sert
  cet objet, directement ou par un parent.
- **Un camp.** ⚫ noir (le joueur et sa maison), 🟢 vert (l'adversaire, joué par
  le MJ selon le canon), 🟠 arbitre (le MJ, hors camp). Un même MJ joue le vert
  et arbitre ; il ne joue jamais le noir.
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
  plan existe, dort, et n'est touché par aucun coup ni aucun saut. **Le deck
  vert, c'est son calendrier** : ses états sont ses événements datés (l'ost de
  Criston devant Sombreval, Tessarion qui arrive, Aegon qui se proclame), et
  chacun entre au deck au tour de sa date, comme une pièce qui arrive. C'est ce
  qui donne au Vert une existence sans appel, et au saut de temps de quoi
  tourner.

---

## 3. Les coups

Un coup est une ligne. Il n'y en a que quatorze sortes, et un camp ne joue qu'un
coup par tour. Ne comptent pas : les arbitrages, et ce qui ne coûte rien —
viser, demander, justifier, consigne — sans quoi l'ouverture (§6.1) serait
impossible. Le greffe **signale** un second coup dans le tour, il ne le refuse
pas : c'est au MJ de tenir la règle, et de savoir quand il la casse.

| Coup | Qui | Ce qu'il fait | Ce qu'il coûte |
|---|---|---|---|
| 🎯 **viser** | un camp | pose un état dans son deck ; avec `arrive_tour`, l'état est daté et n'entre au deck qu'à ce tour (la place est tenue d'avance) | une place du deck |
| 🃏 **sortir** | un camp | sort un état du deck ; ses pièces restent engagées où elles sont | un coup |
| 📦 **demander** | un camp | demande une ressource : id, lieu, nombre, tenant | rien tant que l'arbitre n'a pas parlé |
| ⚖️ **arbitrer** | l'arbitre | accorde, corrige (nombre, lieu, tenant), reporte (« arrive dans N tours »), ou refuse, **avec sa source**. Sur une destruction suspendue, « accorde » juge la portée bonne et lève la suspension ; « refuse » la fait tomber | — |
| 🔒 **bloquer** | l'autre camp | pose un blocage sur un état ou sur un maillon précis, avec la pièce qui le produit | la pièce, engagée |
| 🗝️ **lever** | un camp | pose une clé contre un blocage, avec les pièces engagées ; sans blocage à ouvrir, elle **réalise** un état (`sert`) et est tenue quand l'arbitre le constate vrai | les pièces, engagées |
| ⚔️ **agir** | un camp | pose un maillon sous une clé ou sous une destruction : qui, avec quoi, résultat ; ou le réalise. Le maillon écrit lève la suspension d'un « justifier » | rien de plus que ce que la clé engage |
| ❓ **justifier** | l'autre camp ou l'arbitre | exige la chaîne d'une clé, ou la portée d'une destruction ; la pièce visée passe *en suspens* | rien |
| 💥 **détruire** | un camp | vise une ressource adverse ; à la réalisation elle sort du grand livre pour toujours, avec ce qu'elle engageait | la pièce qui frappe, engagée, puis **gelée un tour** |
| 🗑️ **retirer** | un camp | retire une clé, un blocage, une destruction à soi, ou une ressource ; les pièces libérées sont **gelées deux tours** | deux tours à découvert |
| 🔧 **reconstruire** | un camp | rend une ressource détruite si elle se reconstruit (une porte, des coques, des engins ; pas un pendu) ; **revient dans deux tours** | deux tours |
| ➕ **réarmer** | un camp | ajoute une pièce à une clé ou un blocage qui tient déjà, sans le retirer ; ni le texte ni la cible ne changent | un coup, pas de gel |
| ⏸️ **passer** | un camp | ne joue rien | le tour |
| 📋 **consigne** | un camp | avant un saut : ce que fait chaque pièce si elle est visée (tenir, retirer, justifier par Untel) | rien |

### Les règles de validité

1. **Une pièce engagée l'est jusqu'à ce que la clé qui l'engage soit retirée,
   écartée ou tenue.** Une deuxième clé qui la veut est « sans ressource ».
   Meleys ne montre pas la côte la veille et ne tient pas la rade le matin.
2. **Pas de ressource, pas de coup.** Une clé qui n'engage rien de nouveau n'est
   pas un coup ; l'arbitre la refuse.
3. **Un blocage est posé par l'autre camp.** Le miroir est automatique : la clé
   d'un camp est le blocage de l'autre, et le repli l'écrit des deux côtés.
4. **Le défenseur tient par défaut.** Sur un maillon où les deux camps ont une
   pièce, rien ne bouge tant qu'un coup ne le tranche pas.
5. **Justifier ne punit pas, et ne se répète pas.** Une clé sans maillon est
   valide jusqu'à ce qu'un coup exige sa chaîne. **Une pièce ne se justifie
   qu'une fois** : le coup est gratuit, il ne doit pas être répétable. L'arbitre
   peut jouer « justifier » sur un état dès l'ouverture (« qui s'assied, et
   comment arrive-t-elle ? »), une fois.
6. **La portée se refuse sur pièce.** Une destruction ou un blocage que la pièce
   ne peut pas atteindre (présence, moyen, distance) est refusé en une ligne.
   C'est le seul endroit où le « comment » remonte de force.
7. **Un heurt se tranche à la table, pas à l'œil.** Quand deux pièces se
   touchent, l'arbitre applique trois lignes et écrit sa raison :
   - **bête contre bête** : la plus grosse l'emporte ; deux contre une, heurt
     mutuel (les deux sortent du grand livre : `detruit` sur l'arbitrage) ;
   - **troupe contre bête posée** : destruction partielle, par centaines, et la
     bête gelée un tour ;
   - **troupe contre troupe** : la plus nombreuse l'emporte, sauf si l'autre
     est derrière un mur, auquel cas rien ne bouge.
   Une destruction partielle chiffre ce qui sort du grand livre, une fois.
8. **Une ressource demandée et engagée par rien deux tours après son arrivée est
   une branche morte.** Signalée, pas punie.
9. **Dix états par deck.** Entrer ou sortir un état est un coup.
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
11. **Un id n'a qu'un objet.** Un blocage, une clé, un maillon ou une
    destruction dont l'id est déjà pris est refusé : le fichier est append-only,
    une réécriture silencieuse y serait invisible. Une correction est un coup de
    plus (retirer, reposer sous un autre id).

---

## 4. Le temps

- **Le tour** est l'unité du joueur : un coup de chaque camp. Il ne voit que des
  tours : « arrive dans deux », « gel deux », « J au tour 15 ».
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
- **J se pose en tours avant le premier coup** qui en dépend. Un Guet payé
  « avant J » sans J posé est indécis, et l'arbitre le dit.
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

Champs communs : `n` (rang), `tour`, `camp` (`noir` | `vert` | `arbitre`),
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
  atterri et les états datés entrés au deck ;
- un coup par ligne : **emoji du camp, emoji du coup, numéro — un verbe en
  gras, ce que ça fait**, les pièces engagées, et pour l'arbitre son verdict et
  sa source ; les noms en clair, jamais un id nu ;
- l'analyse du tour, courte : la qualité des coups, ce qu'ils changent ;
- l'état, un seul trône, chaque maillon coloré par le camp qui y prévaut, les
  gelés, les arrivées, le trait.

```
⚫🗝️ 6 — Lève 3 en faisant entrer l'armée par la porte de la Rivière. Engage l'armée, Steffon.
🟢❓ 7 — Suspend 6 : par où entrent-ils, la chaîne depuis les fosses. N'engage rien.

État
👑 Trône — tenu par 🟢
← 🟢 🗝️ 6 armée dans le Donjon, suspendue par ❓ 7
← 🟢 🔒 3 Donjon tenu, garnison dedans
Trait aux Noirs.
```

Un maillon est coloré par le camp qui y prévaut à cet instant, pas par celui
qui l'a posé.

---

## 6. Méthode d'application dans le monde

### 6.1 Ouvrir une partie

1. **Le deck noir** vient des cahiers : dix états au plus, choisis avec la
   criticité (`scripts/criticite.py`) pour dire où l'on se bat. Chaque état
   emmène ses clés, ses actions, ses pièces telles qu'elles sont écrites : les
   actions « faites » sont des maillons réalisés, les « à faire » des maillons
   posés, les « bloquées » des maillons en suspens. Les colonnes *Avec quoi* et
   *Office* donnent les ressources à demander, en une file, arbitrée une fois.
2. **Le deck vert** vient d'abord de **leurs cahiers** — les Verts en ont,
   sous `etat/maisons/maison-targaryen-vert/documents/books/`, au même gabarit
   —, puis du canon et de l'état pour ce que leurs cahiers ne portent pas (le
   Donjon, le Guet, Vhagar, les galères, Larys, les places muettes, l'ost de
   Criston, Aegon). Dix blocages prêts à poser. C'est là que la Danse avance.
3. **Le trône** est posé une fois, et **J** en tours si le plan en dépend.
4. L'arbitre joue « justifier » sur le trône lui-même, une fois : qui s'assied,
   et comment arrive-t-elle.

### 6.2 Jouer en scène

- **La parole du joueur à la Table Peinte est un coup.** « L'armée entre par la
  porte de la Rivière » est une clé ; on l'écrit telle quelle, avec les pièces
  qu'elle engage, et on ne lui demande rien de plus.
- **« Justifier » est diégétique.** C'est le conseiller compétent qui demande
  « et la poterne ? ». Là seulement on dépêche un homme, **un**, avec une
  question qui a un objet et une date, par `scripts/depecher.py --contexte`. Sa
  réponse est la chaîne de maillons ; elle s'écrit comme des lignes `agir`,
  jamais comme une réplique inventée. La Règle Zéro s'applique entière.
- **Le Vert tient par défaut.** Un blocage avec une pièce déjà posée (une
  garnison, un Guet) se joue sans appel. Un coup vert qui n'est pas « tenir »
  (justifier, détruire, retirer, une clé neuve) demande une décision : on
  dépêche la tête verte concernée, une fois, avec le coup noir qu'elle doit
  répondre. Ce qu'elle rend est son coup.
- **Une seule pièce par battement.** La partie avance d'un coup par prise de
  parole, comme le flux : on ne pousse pas cinq coups d'un bloc.
- **Un tour à la fois, et l'on rend la main.** Le MJ joue un tour — le coup
  noir tel que le joueur l'a posé, le coup vert, les arbitrages qu'ils
  appellent, la ligne `tour` —, puis il **présente** ce tour dans le format de
  la section 5.4 et s'arrête. Jamais deux tours d'affilée sans que le joueur
  ait vu le premier. Un saut de temps est l'exception déclarée (6.5), et même
  là chaque tour sauté est présenté au retour, dans l'ordre.

### 6.3 Réaliser un coup dans l'état

Un coup posé n'écrit rien dans `etat/`. Un coup **réalisé** écrit, et c'est le
MJ qui l'écrit, par les portes ordinaires :

- un maillon réalisé → un acte (`scripts/ajouter.py actes`, avec témoins et
  `connu_de`), le déplacement dans `personnages.lieu_id`, la possession dans
  `lieux.controle_id` ou `maisons`, la dépense dans la caisse ; et un
  `programme` daté dans `evenements.json` si l'effet met du temps à aboutir ;
- une destruction réalisée → l'acte, et la ressource sortie du grand livre ; ce
  que le joueur en apprend passe par `info.json` avec son délai ;
- un arbitrage qui comble → le fait écrit dans l'état, daté, une fois (une bête
  qui couche quelque part, un nombre d'engins sur un mur) ;
- un état constaté vrai → la preuve écrite dans le cahier, et s'il change le
  cours des choses, une entrée aux annales.

Le monde avance de deux jours par tour ; `monde.date` et les horloges suivent,
par `tick.py`, qui lit les `programme` que la partie a datés.

**Le récap des écritures.** À la fin de chaque tour joué, et au retour d'un
saut, `python scripts/partie.py <partie> --ecritures --depuis-tour N` liste ce
que la partie demande d'écrire : les actes des maillons réalisés, les positions
qui ont changé, les faits comblés par l'arbitre, les pièces détruites ou
retirées, les états constatés. C'est une liste, pas une écriture : le MJ
l'applique par les portes ordinaires, et rien n'est réputé écrit tant que ce
n'est pas dans `etat/`.

### 6.4 Le brouillard

La partie est écrite en vérité entière : les coups verts y sont en clair. **Rien
de vert n'entre dans les vues, les jetons ou les cahiers du joueur sans une
source.** Un blocage vert que le joueur n'a aucun moyen de connaître (Larys sur
les portes) n'existe pour lui que par ses effets. Une destruction réalisée
arrive par une bouche, avec son retard : trois coques coulées à Sombreval se
savent le jour du corbeau. Le repli des cahiers ne recopie donc que le côté
noir et ce que le noir a appris.

### 6.5 Les sauts de temps

Un saut ne s'interrompt jamais : le joueur est explicitement parti. Pendant le
saut, pour chaque tour :

1. les arrivées entrent, les gels expirent ;
2. les clés noires prêtes se réalisent ; les clés suspendues restent suspendues
   et, à leur date, sont constatées **manquées** ;
3. sur un maillon contesté, le défenseur tient ; les pièces noires suivent leurs
   **consignes**, et sans consigne elles tiennent et encaissent ;
4. une destruction datée atterrit ou tombe ;
5. une réaction verte qui n'est pas « tenir » est décidée une fois, par un appel
   à la tête verte, au tour où sa pièce est touchée.

Au retour, le joueur trouve l'état de la partie tel qu'il est, et il l'apprend
par les voies ordinaires : « ce qui s'est fait sans vous » pour ses pièces, des
nouvelles datées pour ce que le Vert a fait, le silence pour ce qu'aucune source
ne rapporte. Un saut sans consigne et avec une clé suspendue revient avec des
trous ; c'est le prix du départ.

### 6.6 Arbitrer une ressource

L'ordre est fixe, on s'arrête au premier qui répond, et on écrit la source :

1. **L'état le sait** (`personnages`, `lieux`, `maisons`, les mains, un cahier) :
   accordé sur pièce.
2. **Un mécanisme la produit** (une tête, une main, une chaîne déjà écrite) : le
   manque est **acté**, le mécanisme nommé, la valeur laissée à ce qu'il rendra,
   avec un délai.
3. **Rien ne répond** : le MJ **comble**, une fois, à froid, d'après le canon et
   le plausible, et l'écrit dans l'état.

Comblé ne passe jamais avant acté. Et le joueur ne tranche jamais une ressource
adverse : il pose une hypothèse dans son plan, ce qui est un coup à lui, pas une
vérité.

### 6.7 Ce que le joueur voit

**Il voit tout son côté, et rien du leur qui ne lui soit parvenu.** Le décor a
un onglet « Le conseil » (`ecrans/modules/partie.js`, note :
[`docs/partie.md`](../../../docs/partie.md)) qui rend la position en cartes :
ses desseins, ses pièces — en main, en route, qui se remettent —, ses ordres, et
en face les obstacles que l'adversaire a posés contre lui. C'est la contrepartie
du reste : on ne peut pas demander à quelqu'un de jouer une position dont on lui
cache la moitié, et la moitié qu'on lui montre est la sienne.

Le brouillard n'a pas bougé pour autant, il s'est déplacé sur l'ennemi : un
obstacle vert n'apparaît que s'il a été rapporté, et son pied dit par qui ; une
pièce verte engagée dans rien contre nous n'apparaît pas du tout. Larys sur les
portes n'existe pour le joueur que par ses effets, exactement comme avant.

Et le vocabulaire de l'écran est **celui de l'échiquier**, pas un troisième
jeu de mots : 🎯 état cible, 🔒 verrou, 🗝️ clef, ⚔️ action, 📦 pièce, ❓ question.
Ce sont les mots des cahiers d'affaire, donc ceux que la reine et ses hommes
emploient déjà — les traduire en « dessein », « obstacle » et « ordre » revenait
à traduire du français vers du français, et « ordre » ne désignait rien. Ce qui
ne sort jamais, c'est la tuyauterie du greffier : gel, deck, tour. Les délais
sont en jours du monde.

Le reste lui parvient comme avant :

- le mestre qui relit ce qui tient, ce qui est suspendu, ce qui a été perdu,
  depuis l'état de la partie, dans sa langue ;
- ses cahiers repliés, dans les livres, avec les preuves des états constatés ;
- ses pensées quand il revient de loin ;
- les gens qui entrent avec une nouvelle, au rythme du brouillard.

Le vocabulaire du GREFFIER (coup, gel, deck, tour, blocage, maillon) ne sort
jamais en fiction. Un gel est un capitaine qui a besoin de deux jours pour
rembarquer ; un blocage est une garnison qu'on voit sur un mur ; « justifier »
est un conseiller qui pose la seule question qui compte. **Verrou, clef, action
et état cible, eux, se disent** : ce sont les mots des cahiers d'affaire, écrits
de la main des hommes, et un conseiller qui dit « ce verrou n'a pas de clef »
parle sa langue, pas celle de la machine.

---

## 7. Interdits

- Jamais un blocage posé sur soi-même, ni un problème qu'on se fabrique. Ce
  qu'on ignore est un trou.
- Jamais une ressource qui apparaît sans ligne `demander` et sans arbitrage.
- Jamais une valeur adverse tranchée par le joueur.
- Jamais une interruption pendant un saut.
- Jamais une réplique de PNJ écrite pour rendre un coup : la Règle Zéro tient
  dans la partie comme ailleurs. Une justification vient d'un homme dépêché ; un
  coup vert non trivial vient d'une tête verte dépêchée.
- Jamais la partie montrée au joueur, ni son vocabulaire en fiction.
- Jamais une ligne modifiée : une correction est un coup de plus.
