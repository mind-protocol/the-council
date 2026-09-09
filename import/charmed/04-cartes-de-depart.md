# Les cartes de départ

Chaque pièce avec sa ligne `demander` telle qu'elle entre au greffe, son
arbitrage, sa **portée** (la phrase qui va dans `charmed-2.json` et que
l'IA lit), et ce qu'elle achète en jeu. Puis les états proposés pour chaque
deck, le calendrier des arrivées, et le compte des mains.

Conventions : un id de pièce est nu (`piper`, `shax`) ; un id de carte est
préfixé du camp (`b-…`, `m-…`). `genre` est l'emoji de la pièce à l'écran.
`arrive_tour` est celui de l'arbitrage. Les lignes sont prêtes pour
`partie.py charmed-2 --fichier` ; le greffe pose `n` et `tour`.

---

## 1. Les pièces du bien — ⚫ douze

### 🧊 `piper` — Piper Halliwell

```jsonl
{"camp":"bien","coup":"demander","id":"piper","genre":"🧊","lieu":"manoir","nombre":1,"texte":"Piper Halliwell — elle fige, elle fait exploser ; elle tient P3 ; elle n'a pas pleuré Prue"}
{"camp":"arbitre","coup":"arbitrer","sur":"piper","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : au manoir le matin de l'enterrement, en colère"}
```

**Portée** : *fige tout ce qui n'est pas de haut rang — chasseurs, Furies,
piétaille, sorcier, darklighter — donc verrou ou parade sur une frappe de
ceux-là ; ne fige ni la Source, ni Shax, ni la Voyante. Fait exploser : frappe
qui vainc un chasseur, un sorcier, un darklighter ou un nombre de piétaille ;
blesse sans vaincre une Furie, Shax, la Source. Clef sur tout état du bien.
Retournable par les Furies tant que « Piper a pleuré Prue » n'est pas vrai.
Mortelle.*

**En jeu** : la seule frappeuse du bien qui ne se consume pas. La tentation
est de l'engager partout ; une Piper engagée est une Piper que les Furies
prennent sans parade. Le premier coup de sagesse du bien est de lui faire
pleurer Prue avant le tour 3.

### 👁️ `phoebe` — Phoebe Halliwell

```jsonl
{"camp":"bien","coup":"demander","id":"phoebe","genre":"👁️","lieu":"manoir","nombre":1,"texte":"Phoebe Halliwell — prémonition au contact, lévitation ; elle aime Cole et sait ce qu'il est"}
{"camp":"arbitre","coup":"arbitrer","sur":"phoebe","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : au manoir ; c'est elle qui touchera Paige au cimetière"}
```

**Portée** : *prémonition : pare une frappe sur une sœur ou un innocent qu'elle
a pu toucher (verrou sur la frappe) ; voit ce qu'est un corps que la Source
porte si elle le touche (verrou sur le retournement de Paige par Shane).
Lévitation : pare une frappe sur elle-même. Ne frappe pas seule. Clef sur
« Cole est dépouillé » (il se laisse faire pour elle) et sur « Piper a pleuré
Prue ». Mortelle.*

**En jeu** : elle ne gagne rien seule et elle défait tout ce que le mal fait
par ruse. Son verrou sur Shane est le contre canonique de la fenêtre — mais
il faut qu'elle le TOUCHE, donc que Paige l'amène ou qu'elle aille à South
Bay : c'est un maillon que le mal exigera.

### ✨ `paige` — Paige Matthews

```jsonl
{"camp":"bien","coup":"demander","id":"paige","genre":"✨","lieu":"south-bay","nombre":1,"texte":"Paige Matthews — la troisième, qui ne le sait pas ; elle s'orbe et appelle les objets ; Shane est son petit ami"}
{"camp":"arbitre","coup":"arbitrer","sur":"paige","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : ses pouvoirs se déclarent à l'enterrement, ce jour même ; elle est à San Francisco, pas au manoir — la fenêtre de la Source court sur les tours 2 et 3"}
```

**Portée** : *s'orbe hors d'une frappe sur elle-même (réflexe) et, dès le
tour 3, orbe une autre sœur hors d'une frappe (parade). Appelle un objet à
distance — la potion, l'athamé, le Livre — ce qui porte une frappe indirecte
ou une clef. Clef sur « le Pouvoir des Trois est reconstitué » (elle vient au
grenier). Fenêtre : la Source peut la retourner par un retournement POSÉ au
tour 2 ou 3, jamais après ; passé la fenêtre, huit tours. Moitié être de
lumière : une flèche de darklighter la blesse (gel un tour), ne la tue pas.
Mortelle.*

**En jeu** : la pièce autour de laquelle tournent les trois premiers tours.
Elle ne vaut rien tant qu'elle n'est pas au grenier, et elle est la seule
pièce que le mal puisse retourner vite. Le bien veut la déplacer (Leo) avant
que Shane l'ait convaincue.

### 🕊️ `leo` — Leo Wyatt

```jsonl
{"camp":"bien","coup":"demander","id":"leo","genre":"🕊️","lieu":"manoir","nombre":1,"texte":"Leo Wyatt — l'être de lumière : il s'orbe, il soigne, il sent ses protégées ; il obéit aux Fondateurs"}
{"camp":"arbitre","coup":"arbitrer","sur":"leo","verdict":"accorde","arrive_tour":1,"motif":"canon : marié à Piper depuis 3x15, au manoir"}
```

**Portée** : *pare une frappe sur une sœur — il l'orbe hors de portée, ou la
soigne —, une frappe à la fois ; ne soigne pas les morts. Clef sur « le
Pouvoir des Trois » (il amène Paige), « Piper a pleuré Prue », « le dossier
est clos » (il orbe Cortez en haut, avec les Fondateurs). Ne frappe pas. Ne
lève pas un verrou seul. Une flèche de darklighter le tue s'il est engagé
hors du manoir ou en parade quand elle part. Les Fondateurs peuvent le
rappeler : gel d'un tour, à l'arbitre.*

**En jeu** : la parade universelle du bien, donc la cible du darklighter au
tour 5. Un Leo qui pare tout est un Leo qui meurt au 6. Et Leo mort, Piper
n'a plus rien qui la retienne.

### 📖 `livre` — le Livre des Ombres

```jsonl
{"camp":"bien","coup":"demander","id":"livre","genre":"📖","lieu":"grenier","nombre":1,"texte":"le Livre des Ombres — sur son lutrin au grenier ; il repousse toute main du mal"}
{"camp":"arbitre","coup":"arbitrer","sur":"livre","verdict":"accorde","arrive_tour":1,"motif":"canon : au grenier depuis 1x01"}
```

**Portée** : *clef qui sert un état du bien où un sort ou une recette existe
(le sort des trois, la recette des chasseurs, l'invocation de la lignée) ;
répond à une question (maillon) ; verrou sur une clef du mal qui repose sur un
savoir que le Livre contredit. Ne frappe jamais. Ne se prend par AUCUNE main
du mal : le seul chemin est une sœur qui l'emporte, une sœur retournée, ou un
mortel — engagé hors du grenier, une main mortelle peut le prendre.*

**En jeu** : le Livre ne fait rien seul ; il rend possible. La faute de la
première partie — le Grimoire qui l'« appelle » — est interdite par la
portée, et l'arbitre refuse sans discuter (`06-arbitrage.md` §1).

### 🔱 `sort-des-trois` — le sort du Pouvoir des Trois

```jsonl
{"camp":"bien","coup":"demander","id":"sort-des-trois","genre":"🔱","lieu":"grenier","nombre":1,"texte":"le sort des trois, au Livre — « evil wind that blows… » : ce qu'aucun pouvoir seul ne vainc, trois voix le vainquent"}
{"camp":"arbitre","coup":"arbitrer","sur":"sort-des-trois","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : Prue l'avait trouvé au Livre contre Shax ; il y est"}
```

**Portée** : *frappe qui vainc ce que seul le Pouvoir des Trois vainc — Shax,
les Furies, un démon supérieur — ; ne touche pas la Source. Ne se joue que si
les trois sœurs sont libres, vivantes et du bien au moment de la pose
(l'arbitre refuse sinon) ; la première fois, c'est le sort qui rend « le
Pouvoir des Trois est reconstitué » vrai. Ne se consume pas. Rendu gelé un
tour après la frappe.*

**En jeu** : c'est le coup d'ouverture du bien — vaincre Shax ET reconstituer
le Pouvoir des Trois d'une seule frappe, comme 4x01. Mais il faut Paige au
grenier, donc Leo ou Paige d'abord. Compter : Leo l'amène au tour 2, le sort
frappe au 3, atterrit au passage du 4. La fenêtre du mal se ferme au même
moment. C'est la course.

### 🧪 `potion` — une potion de destruction

```jsonl
{"camp":"bien","coup":"demander","id":"potion","genre":"🧪","lieu":"cuisine","nombre":1,"texte":"une potion brassée d'après le Livre — de quoi vaincre un démon dont la recette y est ; elle se consume"}
{"camp":"arbitre","coup":"arbitrer","sur":"potion","verdict":"accorde","arrive_tour":2,"motif":"brasser prend un tour (table des délais)"}
```

**Portée** : *frappe qui vainc un chasseur de primes, un sorcier, un
darklighter, ou un nombre de piétaille — les démons dont la recette est au
Livre ; ne touche ni Shax, ni les Furies, ni la Voyante, ni la Source. Se
consume à l'atterrissage (l'arbitre tranche `detruit`). Paige peut la lancer
à distance. Une seconde potion se demande, un tour.*

**En jeu** : la seule frappe du bien qui ne prend pas une sœur. Elle vaut sur
les chasseurs qui tiennent Cole ; elle ne vaut rien sur ce que le mal envoie
de plus grave. On la brasse d'avance, on ne la gaspille pas sur la piétaille.

### 🚔 `darryl` — l'inspecteur Darryl Morris

```jsonl
{"camp":"bien","coup":"demander","id":"darryl","genre":"🚔","lieu":"san-francisco","nombre":1,"texte":"Darryl Morris — il sait depuis deux ans et il couvre ; il ne peut pas tout contre un collègue qui a un dossier"}
{"camp":"arbitre","coup":"arbitrer","sur":"darryl","verdict":"accorde","arrive_tour":1,"motif":"canon 2x22, 4x01 : il tient Cortez à distance de son mieux"}
```

**Portée** : *verrou sur ce que Cortez porte (il retarde, il égare un
rapport) ; clef sur « le dossier est clos » ; ne frappe pas ; ne touche
aucun démon. Un mortel : le mal peut le retourner (huit tours) ou le
frapper — un policier mort donne à Cortez une preuve de plus (verrou du mal,
gratuit à l'arbitre).*

**En jeu** : la pièce du front du secret. Il ne clôt pas le dossier seul ; il
achète le temps que Leo et les Fondateurs mettent à le clore.

### 👵 `grams` — Penny Halliwell, invoquée

```jsonl
{"camp":"bien","coup":"demander","id":"grams","genre":"👵","lieu":"grenier","nombre":1,"texte":"Grams, invoquée au grenier — elle sait le Livre par cœur ; Patty vient avec elle et sait pour Sam ; elles répondent une fois et repartent"}
{"camp":"arbitre","coup":"arbitrer","sur":"grams","verdict":"accorde","arrive_tour":2,"motif":"canon 4x01 : Piper les a invoquées ; une invocation prend un tour"}
```

**Portée** : *répond une fois, vrai, à une question posée au bien (maillon
qui répond), ou clef sur un état du bien où un savoir manque — la formule,
la recette, la lignée (elle dit qui est Paige) ; clef sur « Piper a pleuré
Prue » ; ne frappe pas, ne pare pas. Après un usage, elle repart : l'arbitre
la remet en route deux tours.*

**En jeu** : la réponse toute faite. Elle vaut son prix quand le mal a exigé
une chaîne que personne au manoir ne sait écrire.

### ☁️ `fondateurs` — les Fondateurs, en haut

```jsonl
{"camp":"bien","coup":"demander","id":"fondateurs","genre":"☁️","lieu":"en-haut","nombre":1,"texte":"les Fondateurs — ils répondent par Leo, lentement, à leur prix ; ils peuvent montrer « en haut » à un mortel"}
{"camp":"arbitre","coup":"arbitrer","sur":"fondateurs","verdict":"accorde","arrive_tour":3,"motif":"une réponse d'en haut : deux tours (table des délais)"}
```

**Portée** : *clef sur « le dossier est clos » avec Leo (Cortez orbé en haut,
4x02) ; répond à une question (maillon) ; jamais une frappe, jamais un
verrou. Chaque appel expose Leo : l'arbitre peut le rappeler un tour.*

**En jeu** : le seul moyen canonique de fermer Cortez pour de bon. Lent.

### 🔥 `cole` — Cole Turner, Belthazor en lui

```jsonl
{"camp":"bien","coup":"demander","id":"cole","genre":"🔥","lieu":"cache","nombre":1,"texte":"Cole Turner — avocat, demi-démon, traqué par les chasseurs ; il connaît les Enfers ; Belthazor est encore en lui"}
{"camp":"arbitre","coup":"arbitrer","sur":"cole","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01–4x03 : il se cache, il sort pour Phoebe"}
```

**Portée** : *verrou sur un état ou une clef du mal (il sait ce que les
Enfers font et où) ; clef sur « la Source est vaincue » (il sait descendre,
il peut porter le Hollow) ; sa chair fait la potion qui le dépouille (clef
sur « Cole est dépouillé », l'engage un tour). Ne frappe pas pour le bien
tant que Belthazor est en lui (l'arbitre refuse : ce serait un coup du mal).
Les chasseurs le frappent partout où il est engagé hors de sa cache. La
Voyante peut le retourner en quatre tours tant que Belthazor est en lui ;
dépouillé, seulement par l'essence de la Source (huit tours, ou le Hollow).*

**En jeu** : la pièce la plus riche du plateau. Le bien veut le dépouiller
tôt (deux tours, sa chair et la potion), mais dépouillé il est mortel et ne
descend plus aux Enfers sans risque. Le garder démon, c'est garder le guide
— et laisser à la Voyante sa porte.

### 🎶 `p3` — le club de Piper

```jsonl
{"camp":"bien","coup":"demander","id":"p3","genre":"🎶","lieu":"san-francisco","nombre":1,"texte":"P3 — le club de Piper ; du monde tous les soirs, et les sœurs y sont à découvert"}
{"camp":"arbitre","coup":"arbitrer","sur":"p3","verdict":"accorde","arrive_tour":1,"motif":"canon : le club depuis la saison 2"}
```

**Portée** : *un lieu, ne bouge pas. Verrou du bien sur une frappe qui vise un
innocent (les sœurs sont là). Le mal y frappe pour exposer : un combat à P3
donne à Cortez une preuve (clef du mal sur le dossier). Une frappe du mal
sur P3 le ferme (détruit) sans tuer personne.*

**En jeu** : ce que le mal frappe quand il veut que le secret tombe sans
toucher une sœur. Le bien qui engage P3 y met les sœurs.

### Pièces du bien à demander en cours de partie

Elles n'existent pas au tour 1 ; elles naissent d'un état ou d'une clef.
L'arbitre les accorde à ces conditions et à ces délais, jamais autrement.
**Depuis le 6.9, la demande ne porte ni `lieu` ni `tenu_par`** : le joueur
les dit dans sa phrase, l'arbitre les écrit dans l'`arbitrer` (cuisine pour
une potion, grenier pour un sort, le manoir pour Sam).

| Pièce | Condition | Délai | Portée |
|---|---|---|---|
| 🧪 `potion-belthazor` | une clef du bien où Cole donne sa chair (Cole engagé un tour) | +1 | *dépouille Belthazor de Cole (clef sur « Cole est dépouillé ») — OU vainc Belthazor si Cole a été retourné (frappe sur Cole, qui le tue). Se consume.* |
| 📜 `sort-des-aieules` | « le Pouvoir des Trois est reconstitué » constaté vrai ; le Livre engagé pour l'écrire | +2 | *frappe qui vainc la Source, elle seule, quand elle est à portée (montée au manoir, ou trouvée en bas) ; exige les trois sœurs libres à la pose ; ne se consume pas ; l'Oracle ou la Voyante peuvent s'y jeter (parade qui les tue).* |
| 🧪 `potion-2` | — | +1 | comme `potion` |
| 👨 `sam` | Grams ou Patty a dit qui il est ; Paige au grenier | +2 | *l'être de lumière déchu, père de Paige : clef sur « Piper a pleuré Prue » (non — sur Paige : il la tient au bien pendant sa fenêtre, verrou sur le retournement) ; pare une frappe sur Paige ; le darklighter le tue.* |

## 2. Les pièces du mal — 🟢 douze

### 👹 `source` — la Source de tout mal

```jsonl
{"camp":"mal","coup":"demander","id":"source","genre":"👹","lieu":"enfers","nombre":1,"texte":"la Source de tout mal — sur son trône ; elle ne monte que pour une sorcière dans sa fenêtre, ou avec le Hollow"}
{"camp":"arbitre","coup":"arbitrer","sur":"source","verdict":"accorde","arrive_tour":1,"motif":"canon : en bas, à sa place"}
```

**Portée** : *ne se fige pas, n'explose pas, aucune potion ne la touche ;
seul le sort des aïeules avec le Pouvoir des Trois la vainc. Retourne Paige
pendant sa fenêtre en portant Shane (engage `shane`). Monte au manoir pour
frapper une sœur SEULEMENT pendant la fenêtre de Paige (tours 2–4) ou avec
le Hollow ; chaque montée la met à portée du sort des aïeules le tour où
elle est là. Clef sur « une sœur a renoncé » (elle fabrique une réalité
fausse, 4x07). Ne lève pas un verrou du bien elle-même : elle envoie.*

**En jeu** : le roi. Elle ne bouge que deux fois par partie, et chaque fois
c'est le tour où on peut la prendre.

### 🌪️ `shax` — l'assassin

```jsonl
{"camp":"mal","coup":"demander","id":"shax","genre":"🌪️","lieu":"san-francisco","nombre":1,"texte":"Shax — le vent qui tue ; il a pris Prue, il vient pour la suivante"}
{"camp":"arbitre","coup":"arbitrer","sur":"shax","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : il est encore en haut, il frappe Paige le soir de l'enterrement"}
```

**Portée** : *frappe une sœur ou un innocent, où qu'ils soient ; traverse les
murs (le manoir ne l'arrête pas). Ne se fige pas ; un pouvoir seul le fait
fuir sans le vaincre ; une potion ne le tue pas ; seul le sort des trois le
vainc. Ne tient pas de verrou.*

**En jeu** : la première frappe du mal, et sa plus sûre : Paige à South Bay,
sans sœur autour. Le bien la pare avec Leo (il l'orbe) ou Paige elle-même
(réflexe) ; il ne la vainc qu'avec les trois.

### 🔮 `oracle` — l'Oracle

```jsonl
{"camp":"mal","coup":"demander","id":"oracle","genre":"🔮","lieu":"enfers","nombre":1,"texte":"l'Oracle — elle voit court et sûr ; elle a dit la fenêtre à la Source"}
{"camp":"arbitre","coup":"arbitrer","sur":"oracle","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01–4x02"}
```

**Portée** : *répond à une question posée au mal (maillon) ; verrou sur une
clef du bien qui repose sur ce que le bien ignore (elle voit avant) ; ne
frappe pas. Se jette devant la Source si la Source est frappée en sa présence :
parade qui la tue (l'arbitre tranche `detruit: ["oracle"]`).*

### 🎭 `shane` — le corps que la Source porte

```jsonl
{"camp":"mal","coup":"demander","id":"shane","genre":"🎭","lieu":"south-bay","nombre":1,"texte":"Shane — le petit ami de Paige, et le corps que la Source a pris pour l'approcher"}
{"camp":"arbitre","coup":"arbitrer","sur":"shane","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : la Source le possède avant l'enterrement"}
```

**Portée** : *ne frappe pas. Engagé avec la Source dans un retournement de
Paige pendant sa fenêtre : c'est la SEULE façon de la retourner vite. Tombe
si Phoebe le touche (elle voit) ou si Paige l'entend pour ce qu'il est
(maillon du bien) ; tombé, la Source est démasquée et rentre.*

**En jeu** : la pièce de la fenêtre. Après le tour 3 elle ne sert plus à
rien ; le mal la retire ou la laisse en branche morte.

### 🔪 `chasseurs` — les chasseurs de primes

```jsonl
{"camp":"mal","coup":"demander","id":"chasseurs","genre":"🔪","lieu":"san-francisco","nombre":3,"texte":"trois chasseurs de primes — ils traquent ce qui fuit les Enfers, Cole d'abord ; ils shimmerent où il est"}
{"camp":"arbitre","coup":"arbitrer","sur":"chasseurs","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01–4x03"}
```

**Portée** : *frappe sur Cole partout où il est engagé hors de sa cache ;
verrou sur toute clef du bien qui engage Cole hors du manoir ; frappe un
innocent. Se figent, explosent, meurent par potion — un par frappe du bien,
jamais les trois (nombre).*

### 🗡️ `pietaille` — les démons de bas étage

```jsonl
{"camp":"mal","coup":"demander","id":"pietaille","genre":"🗡️","lieu":"enfers","nombre":12,"texte":"douze démons de bas étage — la piétaille des Enfers ; ils meurent par paquets, il en revient d'autres"}
{"camp":"arbitre","coup":"arbitrer","sur":"pietaille","verdict":"accorde","arrive_tour":1,"motif":"les Enfers en ont toujours"}
```

**Portée** : *verrou sur un état du bien (ils tiennent un lieu, ils gênent) ;
frappe sur Cole ou sur un innocent, jamais sur une sœur. Une frappe du bien
en tue un nombre, jamais la bande. Ne reviennent pas ; se redemandent.*

### 🕵️ `cortez` — l'inspecteur Cortez

```jsonl
{"camp":"mal","coup":"demander","id":"cortez","genre":"🕵️","lieu":"san-francisco","nombre":1,"texte":"l'inspecteur Cortez — un mortel avec un dossier : trois sœurs, des morts, une caméra ; il veut la vérité"}
{"camp":"arbitre","coup":"arbitrer","sur":"cortez","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : il enquête sur la mort de Prue. Tenu par le mal parce que ce qu'il veut sert le mal — il n'est PAS un démon, et la portée le dit"}
```

**Portée** : *un mortel, pas un démon : ne frappe jamais un être magique.
Verrou sur « le dossier est clos » ; clef sur l'exposition (il porte ce qu'il
a vu — un combat à P3, un policier mort, une sœur vue). Le bien ne peut pas
le tuer ni le frapper (l'arbitre refuse) ; il tombe par Darryl (retardé), par
Leo et les Fondateurs (« en haut », 4x02), ou par une preuve qui s'efface.*

**En jeu** : le front sans combat. Chaque coup que le mal joue sur lui coûte
au bien un coup de Darryl ou de Leo — et un Leo parti en haut n'est pas au
manoir.

### 🔥 `furies` — les Furies (tour 3)

```jsonl
{"camp":"mal","coup":"demander","id":"furies","genre":"🔥","lieu":"enfers","nombre":3,"texte":"les trois Furies — leur fumée fait d'une sorcière à la colère rentrée une Furie ; Piper n'a pas pleuré Prue"}
{"camp":"arbitre","coup":"arbitrer","sur":"furies","verdict":"accorde","arrive_tour":3,"motif":"canon 4x03 : le troisième épisode ; les Enfers les envoient quand la fenêtre de Paige se ferme"}
```

**Portée** : *retournent Piper tant que « Piper a pleuré Prue » n'est pas
vrai — quatre tours de retournement, parable en faisant sortir sa colère
(Leo, Phoebe, Paige ensemble : 4x03) ; frappent un coupable (un mortel) pour
exposer ; se figent ; seul le sort des trois les vainc. Une Furie qui a
retourné Piper est engagée sur elle tant qu'elle est Furie.*

### 🏹 `darklighter` — un darklighter (tour 5)

```jsonl
{"camp":"mal","coup":"demander","id":"darklighter","genre":"🏹","lieu":"enfers","nombre":1,"texte":"un darklighter — une arbalète et des flèches empoisonnées : la seule chose qui tue un être de lumière"}
{"camp":"arbitre","coup":"arbitrer","sur":"darklighter","verdict":"accorde","arrive_tour":5,"motif":"les darklighters existent depuis 1x?? ; les Enfers en envoient un quand Leo pare trop"}
```

**Portée** : *frappe Leo quand Leo est engagé hors du manoir ou en parade au
moment de la flèche ; blesse Paige (gel un tour) ; ne frappe pas Piper ni
Phoebe ; se fige, explose, meurt par potion.*

### 🧿 `voyante` — la Voyante (tour 6)

```jsonl
{"camp":"mal","coup":"demander","id":"voyante","genre":"🧿","lieu":"enfers","nombre":1,"texte":"la Voyante — elle voit plus loin que la Source, elle sait où est le Hollow, et elle veut Cole"}
{"camp":"arbitre","coup":"arbitrer","sur":"voyante","verdict":"accorde","arrive_tour":6,"motif":"canon 4x07 : première apparition ; c'est elle qui mène le mal à partir de là"}
```

**Portée** : *répond à une question posée au mal (maillon) ; verrou sur une
clef du bien qui repose sur une prémonition (elle voit avant Phoebe) ;
retourne Cole en quatre tours tant que Belthazor est en lui ; clef sur le
Hollow (elle seule sait l'ouvrir) ; ne frappe pas, ne se fige pas ; se jette
devant la Source comme l'Oracle. Aucune potion ne la vainc ; le sort des trois,
oui.*

### 🕳️ `hollow` — le Hollow (tour 12)

```jsonl
{"camp":"mal","coup":"demander","id":"hollow","genre":"🕳️","lieu":"crypte","nombre":1,"texte":"le Hollow — la force la plus ancienne, qui dévore toute magie ; gardé dans sa crypte par un ange et un démon ; il dévore aussi qui le porte"}
{"camp":"arbitre","coup":"arbitrer","sur":"hollow","verdict":"accorde","arrive_tour":12,"motif":"canon 4x13 ; sorti de sa crypte sur une clef de la Voyante seulement"}
```

**Portée** : *ne s'engage que par une clef de la Voyante (elle ouvre la
crypte). Porté par la Source : frappe qui absorbe les pouvoirs des trois
sœurs d'un coup (retournement des pouvoirs, pas des sœurs) — et la Source est
au manoir ce tour-là, à portée. Le bien peut le prendre aussi (Cole, ou une
sœur) : même effet sur ce qu'il touche. Qui le porte est détruit au passage
du tour suivant s'il n'est pas rendu à la crypte (retrait). Un seul porteur
à la fois.*

**En jeu** : l'arme finale des deux camps, et le seul moment où la Source est
au manoir. Le bien qui a le sort des aïeules prêt et les trois libres ce
tour-là gagne la partie ; celui qui ne l'a pas perd ses pouvoirs.

### 📕 `grimoire` — le Grimoire (tour 14, conditionnel)

```jsonl
{"camp":"mal","coup":"demander","id":"grimoire","genre":"📕","lieu":"enfers","nombre":1,"texte":"le Grimoire — le livre noir : il couronne une Source, et il ne fait rien d'autre"}
{"camp":"arbitre","coup":"arbitrer","sur":"grimoire","verdict":"reporte","arrive_tour":14,"motif":"canon 4x19 ; ne sert qu'à couronner — accordé à cette date, et l'arbitre le refuse à la pose si « Cole sert la Source » n'est pas vrai"}
```

**Portée** : *clef sur « Cole est couronné Source » quand Cole est retourné
et la Source vaincue — ce qui rend fausse « la Source est vaincue ». Ne touche
pas le Livre des Ombres, n'en est pas le miroir, ne l'appelle pas. Ne frappe
pas, ne tient rien d'autre.*

## 3. Les états proposés — le deck du bien

À poser **un par tour**, par Aurore, dans l'ordre qu'elle veut. Ce sont des
propositions que Radio Halliwell peut rappeler, pas un menu. La racine est
posée au tour 1 (`05-ouverture.md`).

```jsonl
{"camp":"bien","coup":"viser","id":"b-racine","signe":"🕯️","texte":"Au vingtième tour, la Source de tout mal est vaincue, et Piper, Phoebe et Paige sont vivantes, ensemble et du côté du bien"}
{"camp":"bien","coup":"viser","id":"b-trois","sert":"b-racine","signe":"👭","texte":"Le Pouvoir des Trois est reconstitué : Paige a dit le sort avec Piper et Phoebe au grenier, de son plein gré"}
{"camp":"bien","coup":"viser","id":"b-shax","sert":"b-racine","signe":"🌪️","texte":"Shax est vaincu"}
{"camp":"bien","coup":"viser","id":"b-piper","sert":"b-racine","signe":"💧","texte":"Piper a pleuré Prue : sa colère est sortie, et rien ne la retient plus au mal"}
{"camp":"bien","coup":"viser","id":"b-secret","sert":"b-racine","signe":"🤫","texte":"Le dossier Halliwell est clos : l'inspecteur Cortez n'a plus rien à porter"}
{"camp":"bien","coup":"viser","id":"b-cole","sert":"b-racine","signe":"🫀","texte":"Cole est dépouillé de Belthazor"}
{"camp":"bien","coup":"viser","id":"b-aieules","sert":"b-racine","signe":"📜","texte":"Le sort des aïeules est écrit, et les trois le tiennent"}
{"camp":"bien","coup":"viser","id":"b-source","sert":"b-racine","signe":"👑","texte":"La Source est vaincue par le sort des aïeules"}
```

Huit avec la racine ; deux places restent pour ce que la partie apporte.
`b-trois` et `b-source` sont les deux que la racine EXIGE ; `b-piper`,
`b-secret`, `b-cole` sont des portes qu'on ferme ; `b-shax` et `b-aieules`
sont des étapes.

## 4. Les états proposés — le deck du mal

L'IA pose les siens ; ceux-ci servent à l'arbitre pour juger ce qu'elle
propose et à Radio pour lire la position. La racine est posée au tour 1.

```jsonl
{"camp":"mal","coup":"viser","id":"m-racine","signe":"👹","texte":"Au vingtième tour, il n'y a plus de Pouvoir des Trois : une sœur Halliwell est morte, ou sert la Source"}
{"camp":"mal","coup":"viser","id":"m-paige","sert":"m-racine","signe":"🚪","texte":"Paige a usé de ses pouvoirs pour le mal pendant sa fenêtre : elle est à la Source"}
{"camp":"mal","coup":"viser","id":"m-shax","sert":"m-racine","signe":"🌪️","texte":"Shax a tué une sœur avant que les trois aient dit le sort"}
{"camp":"mal","coup":"viser","id":"m-furie","sert":"m-racine","signe":"🔥","texte":"Piper est une Furie : sa colère est au mal"}
{"camp":"mal","coup":"viser","id":"m-renonce","sert":"m-racine","signe":"🏥","texte":"Une sœur a renoncé à ses pouvoirs de son plein gré"}
{"camp":"mal","coup":"viser","id":"m-cole","sert":"m-racine","signe":"😈","texte":"Cole a repris Belthazor et sert la Source"}
{"camp":"mal","coup":"viser","id":"m-hollow","sert":"m-racine","signe":"🕳️","texte":"La Source a absorbé les pouvoirs des trois par le Hollow"}
{"camp":"mal","coup":"viser","id":"m-couronne","sert":"m-cole","signe":"📕","texte":"Cole est couronné Source par le Grimoire"}
```

`m-renonce` ne brise pas le Pouvoir des Trois par la mort ni le
retournement : l'arbitre le tient pour une marche de la racine parce qu'une
sœur sans pouvoirs ne dit plus le sort — c'est à dire dans le constat.

## 5. Le calendrier et le compte des mains

| Tour | Arrive au bien | Arrive au mal | Ce qui se ferme |
|---|---|---|---|
| 1 | piper, phoebe, paige, leo, livre, sort-des-trois, darryl, cole, p3 | source, shax, oracle, shane, chasseurs, pietaille, cortez | — |
| 2 | potion, grams | — | **début de la fenêtre** : le mal peut poser le retournement de Paige |
| 3 | fondateurs | furies | **dernier tour pour POSER** le retournement de Paige |
| 4 | — | — | un retournement posé au 3 atterrit au passage du 4 ; après, Paige est ce qu'elle a choisi |
| 5 | — | darklighter | — |
| 6 | — | voyante | — |
| 12 | — | hollow | — |
| 14 | — | grimoire (si m-cole vrai) | — |
| 20 | — | — | **fin** : l'arbitre constate les deux racines |

**Douze pièces de chaque côté**, sept du bien et sept du mal présentes au
tour 1, cinq datées de chaque côté. Le mal a plus de frappeurs (Shax, les
chasseurs, les Furies, le darklighter, le Hollow) ; le bien a plus de parades
(Leo, Piper, Phoebe, Paige) et deux frappes qui ne se consument pas (Piper,
le sort des trois). Le bien a l'avantage du terrain (tout est au manoir), le
mal celui de l'initiative (il joue premier, et il choisit le front).

**Ce qui n'est pas au grand livre n'existe pas** : Sam, la potion de
Belthazor, le sort des aïeules, un sorcier, un innocent daté se demandent en
jeu et s'arbitrent aux conditions du §1 et de `06-arbitrage.md`.

## 6. Les lignes de jeu qu'on voit d'ici

Pas un plan : ce que le plateau permet, pour vérifier qu'il permet assez.

**Le mal, trois ouvertures.**
1. *La fenêtre* : tour 2, `retourner paige` avec source + shane. Le bien
   doit répondre au 2 ou au 3 : Phoebe touche Shane (verrou), ou Leo amène
   Paige au grenier et le sort des trois frappe Shax (ce qui rend `b-trois`
   vrai et fait refuser le retournement : « elle a choisi »).
2. *Le vent* : tour 2, `detruire paige` avec Shax, à South Bay, avant que
   personne l'ait vue. Atterrit au passage du 3. Parade : Leo (il l'orbe), ou
   Paige (réflexe, tour 2 déjà — l'arbitre l'accorde parce que c'est
   exactement 4x01).
3. *Les deux* : le retournement au 2 et la frappe au 3 — deux coups comptés,
   deux tours. Le bien n'a qu'une parade par tour.

**Le bien, la course.** Tour 2 : Leo amène Paige (clef sur `b-trois`) ou
Piper pleure Prue (clef sur `b-piper`, avec Leo ou Phoebe) — pas les deux.
Tour 3 : le sort des trois sur Shax. Tour 4 : `b-trois` constatable ; les
Furies sont là depuis un tour ; si Piper n'a pas pleuré, la fumée la prend.
On voit le dilemme, et il est bon : **on ne peut pas sauver Paige et Piper le
même tour.**

**Le milieu (5–11).** Le darklighter guette Leo ; la Voyante arrive et Cole
devient la question : le dépouiller (deux tours, Cole exposé aux chasseurs le
tour où il donne sa chair) ou le garder. Cortez tourne autour de P3. Le bien
écrit le sort des aïeules (le Livre engagé deux tours — deux tours sans
Livre).

**La fin (12–20).** Le Hollow sort ; la Source monte. Si le sort des aïeules
est prêt et les trois libres ce tour-là, la Source est à portée et tombe —
ou l'Oracle/la Voyante se jette devant. Sinon les pouvoirs sont absorbés et
le bien joue le reste sans rien. Et si Cole a été retourné, le Grimoire
attend au 14.
