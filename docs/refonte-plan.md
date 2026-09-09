# La refonte — le plan, et son épreuve : Venise dans Venise

Écrit le 9 septembre 2026, après la relecture consignée dans
[`refonte-points-forts.md`](refonte-points-forts.md). Ce document dit **dans
quel ordre on démonte**, et **à quoi on saura que c'est fait**.

Les quarante invariants à emporter sont dans l'autre document et ne sont pas
répétés ici. Celui-ci ne parle que du chantier.

---

## 1. L'épreuve

Une refonte qui se juge sur une intention se juge sur rien. L'épreuve est
celle-ci, et elle est binaire :

> **Venise et Westeros vivent dans deux paquets séparés, servis par le même
> moteur, et l'on passe de l'un à l'autre par un menu. Aucun des deux ne peut
> nommer l'autre. Le moteur ne peut nommer ni l'un ni l'autre.**

Elle a été choisie parce qu'elle n'est pas hypothétique : les deux mondes sont
**déjà** dans le dépôt, fondus l'un dans l'autre sans que rien ne le déclare.
Elle a donc la propriété qu'on demande à une épreuve : elle échoue aujourd'hui,
pour des raisons qu'on peut compter.

### Les assertions à tenir

Chacune est vérifiable par une commande, sans jugement.

| # | Assertion | Comment on la vérifie |
|---|---|---|
| E1 | Deux paquets existent, chacun complet | `mondes/venise/` et `mondes/westeros/` portent chacun `etat/`, `chambres/`, `manifeste.json`, `manuel.md` |
| E2 | Westeros ne connaît pas Venise | `grep -ril "braavos\|serenissima\|ducat" mondes/westeros/` rend zéro |
| E3 | Venise ne connaît pas Westeros | `grep -ril "peyredragon\|targaryen\|rhaenyra\|dragon" mondes/venise/` rend zéro |
| E4 | Le moteur ne connaît aucun des deux | même grep, les deux vocabulaires, sur `scripts/` hors `scripts/mondes/`, `serveur/`, `ecrans/` : zéro |
| E5 | Chaque monde tient ses gardes seul | `CONSEIL_MONDE=venise python scripts/tick.py --verifier` sort 0, et de même pour `westeros` |
| E6 | Les horloges sont séparées | Venise n'est pas au 12e jour de la 5e lune de l'an 129 ; changer l'heure d'un monde ne bouge pas l'autre |
| E7 | Le menu bascule | `/moi` liste les deux mondes ; `/bascule-monde?vers=venise` sert Venise, avec ses lieux, ses visages, ses livres |
| E8 | Un homme dépêché reste chez lui | une journée d'homme lancée à Venise n'écrit aucun octet sous `mondes/westeros/` |
| E9 | Les sessions ne se croisent pas | deux personnages homonymes dans les deux mondes ont deux identifiants de session distincts |
| E10 | Le fil est propre | le flux de Venise ne contient aucun item de Westeros, et réciproquement |
| E11 | Le moteur passe ses tests sans monde | la suite de tests tourne sur un monde d'épreuve minuscule, ni Venise ni Westeros |
| E12 | Un troisième monde coûte un dossier | ajouter un monde vide et le voir au menu ne demande aucune modification de `scripts/`, `serveur/`, `ecrans/` |

**E12 est l'assertion décisive.** Les onze autres peuvent être obtenues en
déplaçant des fichiers. Seule la douzième prouve qu'on a construit une
mécanique et non rangé un placard.

---

## 2. Ce que l'épreuve révèle aujourd'hui

Mesuré le 9 septembre sur l'arbre de travail. Venise n'est pas « un peu »
présente : elle est majoritaire dans trois tables sur cinq.

| Ce qui est partagé | Part de Venise |
|---|---|
| `etat/personnages.json` | 154 fiches sur 280 |
| `chambres/` | 76 dossiers sur 313 |
| `etat/chemins.json`, les arêtes | 49 sur 193 |
| `etat/lieux.json` | `braavos` y est un lieu comme `peyredragon` |
| `etat/maisons.json` | `maison-serenissima` y est une maison, avec 26 volumes |
| `etat/flux.jsonl` | 140 items sur 12 720 |
| Fichiers Python nommant Venise | 27 |
| Fichiers d'écran ou de serveur la nommant | 10 |

Et le fait qui décide de tout le reste :

> **Un siège joueur vit déjà à Braavos** (`nicolas-lester-reynolds`, `lieu:
> "braavos"` dans `joueurs.json`), et son horloge est dans le même fichier que
> celle de Rhaenyra, calée sur le 12e jour de la 5e lune de l'an 129.

Venise tourne à l'heure des Targaryen. Ce n'est pas un défaut cosmétique : le
temps est la seule chose que le moteur possède en propre, et il est
aujourd'hui indexé par siège au lieu de l'être par monde. Tant que c'est le
cas, deux mondes ne peuvent pas exister, seulement deux décors dans un monde.

**Le point encourageant, et il est réel** : `chemins.json` fait déjà la
séparation qui compte. Braavos y est une composante connexe distincte, et la
règle « composante d'abord, durée ensuite » du quartier interdit déjà à un
homme de Venise d'être « à vingt minutes » de la Table Peinte. La topologie a
donc déjà la notion de monde, sous un autre nom. Le plan consiste largement à
remonter cette notion jusqu'en haut.

---

## 3. Le concept qui manque

> **Un monde est un paquet.** Le moteur n'en connaît aucun ; il en reçoit un.

Un paquet contient, et rien d'autre ne le contient :

```
mondes/<id>/
  manifeste.json      identité, calendrier, monnaie, titres, genres d'unités,
                      canaux de transmission, lieu de départ, siège par défaut
  etat/               monde, personnages, lieux, chemins, maisons, relations,
                      intentions, evenements, actes, paroles, info, annales,
                      flux.jsonl, joueurs, horloges, joueurs/<siege>/
  chambres/           une par habitant
  livres/             les volumes, par maison
  plans/              les plans de salles, la géométrie locale
  blasons/            les armes
  carte/              les cadrages, les bannières, la table peinte
  manuel.md           ce que le meneur doit savoir de CE monde
  voix.json           les timbres
```

Ce que le manifeste doit porter, parce que c'est exactement ce qui est en dur
dans le code aujourd'hui :

| Clef | Ce qu'elle remplace |
|---|---|
| `calendrier` | 12 lunes × 30 jours, gravé dans le schéma |
| `monnaie` | le tuple `("dragon","cerf","sol")` de `chiffrer.py` |
| `titres` | l'expression régulière `(ser|dame|lord|mestre…)` de `criticite/hommes.py` |
| `unites` | le dragon comme type de jeton, sa famille de filtre, son verbe, son canal |
| `canaux` | corbeau, cavalier, rumeur, et leurs vitesses |
| `offices` | les mots-clés d'attribution de `taches.js` et `reparer_renvois.py` |
| `signes` | la table d'emojis de `partie_signes.py` |
| `depart` | le lieu et le siège d'ouverture |

**Le moteur ne lit jamais une valeur de cette table en dur.** C'est la règle
qui rend E4 vérifiable mécaniquement, et E12 possible.

---

## 4. Les sept lots

Chaque lot dit ce qu'il change, ce qu'il prouve, et ce qu'il débloque. Ils
sont ordonnés : chacun suppose le précédent.

### Lot 0 — Le ménage, et le filet

Rien de structurant, mais rien ne se démonte proprement dans un dépôt qui
porte ses brouillons.

- Sortir les ~170 fichiers de travail de la racine, les instantanés manuels
  d'`etat/`, les cinq correctifs à usage unique, le dossier de transit d'août.
- Réparer `metier.md` : il est dupliqué mot pour mot, et se termine par un bloc
  étranger injecté dans chaque PNJ.
- Faire d'`AGENTS.md` un pointeur vers `CLAUDE.md` au lieu d'une copie.
- Supprimer le code mort nommé dans la relecture, et la branche de fournisseur
  inachevée.
- **Mettre dans `verifier.mjs` les deux tests serveur qui gardent le brouillard
  et la marche.** Ils existent, ils sont vérifiés par mutation, et ils ne
  tournent pas.
- Écrire les tests qui manquent là où le risque est : le calcul de fenêtre du
  tick, et les gardes qui verrouillent chaque écriture d'état.

**Prouvé par** : la suite verte, et une racine lisible.
**Débloque** : tout le reste. On ne déplace pas 189 Mo d'état sans filet.

### Lot 1 — Une racine, deux langues, une porte

Le lot dur, et le plus mécanique.

- `tables.py` lit la racine depuis l'environnement au lieu de son propre
  chemin de fichier. Une ligne.
- Migrer les 80 fichiers Python qui collent `etat` en dur sur une racine
  calculée. Un par commit, en commençant par ce qui écrit la mémoire du jeu.
- Supprimer le préambule de chemin recopié dans ~110 fichiers, au profit de
  la déclaration de paquets qui existe déjà mais ne sert pas.
- Côté serveur, faire passer les ~48 lectures de fichier recopiées dans les
  routes par la porte de `contexte.js`, et **résoudre la racine par requête**
  et non au chargement du module.
- `chambres/` et le dossier d'exécution suivent la même racine.

**Prouvé par** : E5 sur un monde d'épreuve minuscule, et la suite de tests qui
tourne sans jamais toucher le monde réel.
**Débloque** : E1, E8, E11.

### Lot 2 — Venise sort

Le déménagement proprement dit, une fois qu'il y a où déménager.

- Créer les deux paquets, et un troisième minuscule pour les tests.
- Répartir les tables partagées. C'est un travail de données, pas de code :
  154 fiches, 76 chambres, 49 arêtes, une maison, 140 items de flux.
- **Trancher le cas du siège à cheval.** Un joueur qui vit à Braavos et une
  reine qui vit à Peyredragon ne sont pas deux sièges du même monde. Soit
  Nicolas devient un siège de Venise et sort du roster de Westeros, soit l'on
  écrit ce qu'est un siège qui traverse, et ce que ça veut dire pour son
  horloge. La seconde option est un vrai sujet de jeu ; ce n'est pas le moment
  de le traiter. **Il part à Venise.**
- Les horloges deviennent par monde, puis par siège dans le monde. Venise se
  donne son propre calendrier dans son manifeste, et cesse d'être en 129 AC.
- Les importateurs de citoyens, les scripts de regroupement et de liaison
  descendent dans `scripts/mondes/venise/`, hors du moteur.

**Prouvé par** : E2, E3, E6, E10.
**Débloque** : le menu a enfin deux choses à proposer.

### Lot 3 — Les données sortent du code

Le verrou de l'écran, mesuré à quatre endroits.

- Les plans de salles quittent le JavaScript pour le paquet du monde. C'est le
  fichier où Braavos est fabriqué par un remplacement de texte sur
  Peyredragon ; il disparaît avec le lot.
- Le registre des lieux 3D, les cadrages nommés de la table peinte et la table
  de blasons deviennent des données servies.
- Le serveur sert la géométrie, l'héraldique et les cadrages du monde courant,
  et n'en connaît aucun.

**Prouvé par** : E4 sur `ecrans/` et `serveur/`, et E7 pour de vrai : le menu
change les visages, les plans et les bannières, pas seulement les noms.

### Lot 4 — Le vocabulaire de règles vient du monde

Le seul lot qui touche la sémantique, et le seul qui demande de réfléchir.

- Le dragon cesse d'être un type d'unité écrit dans le moteur. Il devient une
  entrée `unites` du manifeste, avec son glyphe, sa famille de filtre, son
  verbe et son canal. Une gondole vénitienne s'y déclare de la même façon.
- La monnaie, les titres, les mots-clés d'office, la table d'emojis de la
  partie suivent le même chemin.
- Le moteur gagne une notion qu'il n'a pas : **un genre d'unité**, avec ce
  qu'on peut en dire et ce qu'on peut en faire.

**Prouvé par** : E4 sur `scripts/`, et une partie jouée à Venise dont les
pièces parlent de ducats et de galères sans qu'une ligne de moteur ait bougé.

### Lot 5 — La doctrine et le décor se séparent

Sans ce lot, le menu change le monde et le meneur continue de se croire à
Peyredragon.

- La constitution est courte, stable, générique : les trois boucles, la Règle
  Zéro, l'autonomie, le brouillard, la montre, l'interdiction des menus.
- Les exemples, les noms, les manières, les usages de cour descendent dans le
  `manuel.md` du monde.
- Le manuel du meneur s'assemble : constitution, plus manuel du monde courant,
  plus les modules du moment. La conditionnalité qui existe déjà pour la
  partie devient la règle générale.
- Le manuel de l'homme dépêché est déjà presque générique ; il le devient
  entièrement.

**Prouvé par** : une scène jouée à Venise où personne ne dit « Votre Grâce »
sans qu'on l'ait demandé, et un prompt de meneur qui a maigri de moitié.

### Lot 6 — Le menu, et la vie des processus

Le lot visible, et le dernier, parce qu'il ne vaut rien sans les six autres.

- `/moi` liste les mondes ; `/bascule-monde?vers=` pose un cookie et
  redirige. C'est la copie exacte du menu des sièges, qui marche déjà.
- Les identifiants de session d'agents sont préfixés par le monde. Deux
  homonymes dans deux mondes cessent de partager une tête.
- Le plafond de sessions, la file d'appels et le journal d'exécution deviennent
  conscients du monde.
- **Basculer pendant qu'un homme travaille est refusé, avec le nom de qui
  travaille.** Ce n'est pas une limite technique, c'est la seule réponse
  honnête : une journée en cours appartient au monde où elle a commencé.

**Prouvé par** : E7, E9, E12.

---

## 5. L'ordre, et pourquoi

```
Lot 0  ménage et filet
  └─ Lot 1  une racine, une porte          ← le lot dur
       ├─ Lot 2  Venise sort                (données)
       │    └─ Lot 6  le menu               (visible)
       ├─ Lot 3  les données sortent du code
       └─ Lot 4  le vocabulaire vient du monde
            └─ Lot 5  doctrine contre décor
```

Trois raisons à cet ordre, et une seule compte vraiment.

- **Le lot 1 est un remaniement mécanique de plusieurs centaines de fichiers.**
  On ne le fait pas sans les tests du lot 0, et on ne le fait qu'une fois.
- **Les lots 3 et 4 sont indépendants du lot 2** et peuvent avancer en
  parallèle : l'un est de l'écran, l'autre du moteur.
- **Le lot 6 est en dernier**, contre l'envie. Un menu livré tôt donnerait
  deux décors dans un monde, avec une horloge commune et des sessions qui se
  marchent dessus. Ce serait pire que rien, parce que ça ressemblerait à une
  réussite.

**S'il faut voir le menu avant** : un processus de serveur par monde, chacun
avec sa racine, le menu se contentant de rediriger vers l'autre port. Cela
demande le lot 1 seul, ne bloque aucun lot suivant, et ne ment sur rien.

---

## 6. Ce qui reste commun, volontairement

Le but n'est pas de tout séparer. Ce qui suit est le moteur, et il n'a pas
d'univers :

- les trois boucles, la montre, le tick et ses gardes ;
- la présence calculée, le quartier, les creux ;
- les deux brouillards symétriques, et le pli comme objet ;
- le siège, le jeton, le tri par audience, le fil append-only ;
- la dépêche, le parloir, la chambre, le percept, le péage de la parole ;
- la criticité, les mains, les livres ;
- le plateau de la partie, ses coups et son greffe ;
- l'écran : le bus, le fil, la barre à sept modes, les échelles du décor.

**Un ajout à ce moteur qui nomme un monde est une régression**, et E4 le dit
sans discussion.

---

## 7. Les pièges nommés

Trouvés pendant la mesure. Chacun coûterait une journée s'il était découvert
en chemin.

1. **Le siège à cheval.** Tranché au lot 2 : Nicolas part à Venise. Si l'on
   veut un jour un personnage qui traverse, ça se conçoit exprès, et ça touche
   l'horloge.
2. **L'horloge est indexée par siège, pas par monde.** C'est la racine du
   problème du temps, et elle est dans un fichier de quatre clefs. Facile à
   changer, invisible tant qu'on ne le cherche pas.
3. **Les identifiants de session sont dérivés du nom et de la date.** Deux
   Marie dans deux mondes partagent une tête, en silence, sans erreur.
4. **La topologie fait déjà la moitié du travail.** Braavos est une composante
   connexe distincte. Ne pas refaire ce qui est fait ; s'en servir comme
   contrôle de cohérence pendant la répartition du lot 2.
5. **Le monde en 3D pèse 1,2 Go et se régénère.** Il ne descend pas dans le
   paquet : le paquet porte la recette et le témoin, pas la matière.
6. **La moitié des mentions de décor sont des commentaires.** Le grep de E2 à
   E4 doit les compter comme des échecs sur les données, et comme du bruit sur
   le code. Sinon on passe une semaine à réécrire des commentaires justes.
7. **`presence.json`, `pensees.json` et le flux sont relus en entier, souvent.**
   Séparer par monde les rend deux fois plus petits, ce qui masquera un moment
   le vrai problème de coût. Ne pas confondre les deux chantiers.

---

## 8. Ce que l'épreuve ne dit pas

Elle ne dit rien de la scalabilité ni de l'accessibilité, qui sont les deux
autres contraintes du chantier. C'est délibéré : ce sont des travaux
orthogonaux, avec leurs propres épreuves, et les mêler à celle-ci rendrait
chacune inconcluante.

- **Scalable** s'éprouve autrement : le fil servi sans être reparsé à chaque
  sondage, une politique de rétention, un plafond et un délai sur les appels
  d'agents. Le lot 1 les rend possibles, aucun ne les fait.
- **Accessible** s'éprouve au lecteur d'écran et au clavier seul : le fil
  annoncé, les trois panneaux nommés, le décor atteignable. Le lot 3, en
  sortant les données du code, rend le décor descriptible ; il ne le rend pas
  accessible.

Les deux méritent leur document et leur épreuve. Celui-ci s'arrête ici.
