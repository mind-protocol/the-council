# Passation du chantier de Barralfond

Écrit le 3e jour de la 4e lune, an 129 — 15 août 2026, à la fermeture de la
séance. Pour qui reprend, joueur ou MJ.

---

## Où en est le chantier, en trois lignes

Deux affaires ouvertes, **trente-deux verrous**, **sept actions faites sur
dix-huit**. Le diagnostic est complet des deux côtés ; ce qui bloque n'est plus
de l'ignorance mais **trois décisions**, dont deux appartiennent au joueur.

Un seul changement de conduite a été branché dans le fer — le premier cran de
la migration — et il est mesuré.

---

## Les deux affaires

### 🌳 Migrer la bataille vers la stack — 18 verrous, 6/12 actions

Terminer la migration de `bataille2d.js` vers le format en couches. Trois états
cibles ensemble, jamais deux sur trois : la cuisson a du sens, l'interface la
montre, rien ne tourne hors de la stack.

**Ce qui est fait.** Les cinq couches existent, sont éprouvées et chargées.
`2-reflexion.js` (236 lignes) et son pourvoyeur `bataille/reflexion-adapt.js`
ont été écrits ; l'arbitre `5-qui-conduit.js` (353 lignes) aussi, avec son banc
de onze cas. Le verdict de l'étalon est rendu et attribué au bon coupable.

**Le premier cran est branché** : `rallier()` ne lit plus le mot de la couche 1,
il demande à l'arbitre qui tient les jambes de l'homme. Mesuré : **34 décisions
changées sur 2331, zéro différence dans les annales.** Le bras témoin est en
place — retirer `5-qui-conduit.js` de la chaîne rend exactement la conduite
d'hier.

**Ce qui bloque.** Trois choses, et aucune n'est un manque de code :

- 🔒 **90240** — la vue peint par `h.etat` et `h.camp` seuls, et une couche qui
  conduit s'exprime en RÉÉCRIVANT `h.etat`. Elle ne peut donc pas montrer la
  différence. Le plus petit remède est **une ligne** : compter `corpsAgi` dans
  `etat()`, à côté de la morale ; la capture embarque déjà cet objet entier.
  **Deux nombres et non un** — les conduits *sur* ceux qui ont une couche.
- 🔒 **90260** — un homme qui tombe garde jusqu'au matin la sortie de couche de
  son dernier coup d'œil, parce que rien n'efface `h.l1` hors de `observer()`.
  173 blessés sur 2550. Le compte est donc **miné par le bas et gonflé par le
  haut** : ce n'est ni un plancher ni un plafond.
- **L'étalon est trop étroit.** Il compte quatre choses et le premier changement
  de conduite n'en touche aucune — `ralliement` n'est même pas dans les annales.

### 🧱 Rendre les murs solides — 14 verrous, 1/6 actions

Qu'un homme cesse de traverser le bâti. Trois états cibles, dont **🎯 91200 « ça
reste jouable »**, posé à égalité avec les autres parce qu'un chemin qui
contourne se paiera en cadence si personne ne mesure avant.

**Le diagnostic, et il est plus large que la question posée.** Le pire n'est pas
qu'on traverse les murs, **c'est qu'il n'y a pas de murs** : le bâti porte seize
colonnes pour 45 691 maisons, dont l'emprise au sol ; `bataille2d.js` en retient
quatre et jette le reste, avec le commentaire qui l'assume. Chez lui, une maison
est un point de porte.

**Quatre verrous qu'on ne trouve pas en lisant vite :**

- La position d'un homme s'écrit en **neuf endroits**, dont aucun ne consulte le
  bâti.
- Sur le rail de colonne, **l'homme n'avance pas : on le POSE**. Une butée écrite
  comme correction de position serait effacée au battement suivant, sans erreur
  ni trace. *Ça mordra la première tentative.*
- Il n'existe de chemin par les rues **que vers le Donjon** — deux appels dans
  tout le module. Le repli, le retour au poste, le coureur et le pillage vont
  tout droit.
- La grille du bâti est rangée sur les **portes** : elle ne sait pas dire ce qui
  est plein sous un pied.

**Un piège nommé d'avance :** le test de boîte tournée existe déjà
(`ecrans/modules/monde/bati.js` l.105, sur les trois bonnes colonnes) — mais
`viser()` **n'est pas exporté**, il sort de `batir()` refermé sur des
`InstancedMesh` de Three.js, et `bataille2d.js` n'importe ni ce module ni `three`.
Écrit et mesuré, **pas atteignable**. Ne pas repartir sur « rien à inventer ».

---

## Les trois décisions qui attendent

1. **🎯 91000 — la preuve.** « Zéro traversée » contredit **trois renoncements
   écrits, mesurés et assumés** de la maison, qui tiennent encore : l'arête
   enfouie coûte vingt-cinq fois plus cher, *et on la prendra quand même s'il n'y
   a rien d'autre — une impasse vaut mieux qu'un chemin qui n'existe pas* (1,4 %
   du réseau). Une **demande** est ouverte dans le fil du joueur : tenir zéro,
   reprendre la forme de la maison, ou borner la preuve. **Tant qu'elle n'est pas
   tranchée, personne ne sait contre quoi travailler sur les murs.**

2. **Le stock double.** `chantier/affaires.json` et `etat/books.json` portent la
   même affaire et divergent à chaque retour d'architecte — resynchronisé une
   dizaine de fois dans la journée, et Ygga a dû choisir un numéro libre *dans
   les deux*. La protection d'origine (garder les tickets hors du jeu) est déjà
   assurée : les deux affaires sont posées dans `barralfond` / `la-souche`, donc
   servies au seul siège de l'Équerre. **Proposition : supprimer le chantier
   comme source, ne garder que `books.json`.** Non fait, en attente d'accord.

3. **Élargir l'étalon.** C'est de l'eau, donc de Toll, et il ne l'a pas encore
   dit lui-même.

---

## Ce qu'il faut savoir sur le four avant d'y toucher

- **`cuisson_s` est un `Date.now()`** : il compte la nuit de la machine, pas le
  travail. Deux binaires au même md5 diffèrent de ×2,15 à l'horloge. La sortie
  utile existe déjà et est jetée à chaque cuisson : `CHRONO = {sim, fil, tour}`,
  `sac.js` l.658, rempli au `performance.now()`, imprimé, **jamais gravé**.
- 🔒 **91013 — l'heure de la ville dérive.** `sac.js` l.605-606 lit `jour0`/`min0`
  en direct dans `etat/monde.json`, donc la journée des habitants change avec
  l'horloge du jeu : **la même commande ne cuit plus la même nuit.** Trois
  fichiers identiques en cinq champs rendent 253 257, 82 167 et 294 274 images.
  **Ça ne se répare pas en l'inscrivant — il faut le fixer.**
- **La forme est trouvée et vérifiée** : ailleurs dans la maison
  (`plan_ville.py`, `besoins.py`) on ne lit aucune horloge — l'heure est une
  donnée d'entrée passée en argument, et le tirage sort de **l'identité de la
  chose**. Trois lignes à `sac.js` : déclarer jour et minute dans les réglages,
  les prendre en argument et **refuser de cuire s'ils manquent**, les graver au
  manifeste.
- 🔒 **91014 — la porte du four est ouverte** : `sac.js` l.68, un réglage inconnu
  est avalé sans un mot. `--graine 7` ne fait rien aujourd'hui, en silence.
- **Douze réglages** changent ce que cuit une nuit ; **six** seulement sont
  inscrits au manifeste.
- **L'urne est unique** : 119 238 tirages au dressage, 24 par homme pour ses
  seules déviations. *Un seul tirage décalé en amont et les 2 550 hommes changent
  de cœur.* Refuser de cuire sans graine ne protège de rien ; ce qui **fait** les
  hommes doit sortir de leur identité.

### La règle de lecture de l'étalon

Écrite **avant** le chiffre, dans `analyse/etalon-90110/REGLE-DE-LECTURE.md`, et
mesurée plutôt que supposée : en ne changeant **que la graine**, le quatuor passe
de 3, 5, 4, 47 à 4, 5, 5, 48 puis 3, 5, 1, 47.

> **Un écart d'une unité ne se lit sur aucun des quatre comptes, sauf sur les
> déclencheurs** — les seuls qui n'aient pas bougé d'un cheveu sur trois graines.
> Sur les initiatives, la bande est de **±4**. Et sous condition identique,
> l'attendu reste **zéro**, jamais « à peu près ».

⚠ **Le banc `deux-causes.js` n'entre pas dans la comparaison avec la référence** :
il monte la chaîne seule et ne charge pas la ville — ses faits ne portent ni
`habitant`, ni `peur-gagne`, ni `guet-a-vu`, ni `prend-les-armes`. Une mesure a
déjà été invalidée par cette règle, la mienne.

⚠ **Cuire le vrai four réécrit `monde/portreal.sac`**, sur lequel une bataille est
datée dans la partie (3e jour, 4h30) et que le joueur perçoit. Non fait pour
cette raison.

---

## Comment on a travaillé, et pourquoi ça a marché

**La colonne des verrous s'ouvre VIDE et se remplit d'en bas.** Un verrou gravé
depuis la Souche est un trou mécanique : ça se détecte, ça se compte, et ça ne
vaut rien. Les deux que j'avais gravés d'en haut le premier jour étaient faux
tous les deux, et les architectes l'ont démontré dans la journée.

**Sur onze retours, sept ont consisté à démentir quelque chose** — quatre fois
leur propre écrit de la veille ou du matin, trois fois un chiffre que j'avais
donné au joueur. C'est ce que la méthode devait produire.

**Ce qui a le mieux servi, dans l'ordre :**

- **Écrire la règle avant de voir le chiffre.** Elle a disqualifié ma propre
  mesure. *Une règle de lecture écrite après coup se plie au résultat.*
- **Se corriger tôt.** « Je me corrige maintenant, parce que c'est le moment où
  ça coûte le moins. »
- **Vérifier ce qu'un homme rapporte avant de le relayer.** Trois affirmations
  d'architecte se sont révélées fausses en les recomptant sur le disque —
  y compris celles que j'avais déjà transmises.
- **Le parloir.** Les prévenir pendant qu'ils travaillent leur a épargné trois
  fois une demi-journée : Ygga partait brancher un arbitre qu'elle avait déjà
  branché sans le savoir.

**Deux fautes de ma main, à ne pas refaire :**

- Des **backticks dans un argument bash entre guillemets** : le shell les a
  exécutés, deux mots ont disparu des ordres d'Ygga et de Wenna. Utiliser des
  apostrophes simples.
- **Un commit qui fait deux choses** (retirer un drapeau *et* brancher deux
  couches) rend l'étalon inattribuable. Il a fallu un banc à quatre bras pour
  démêler.

---

## Reprendre

```bash
scripts/guetteur.sh etat/inbox/nicolas-reynolds --auto
```

Le guetteur est **désarmé** et l'inbox est vide. Les cinq architectes sont
rentrés, aucun n'est dépêché. Le siège `nicolas-reynolds` est **occupé** —
Barralfond vit, ses six habitants sont à zéro minute de la Souche.

Pour relancer un homme : `python scripts/depecher.py --qui <id> --minutes 20
--mission "..."`. **Vingt minutes au moins** ; et pour Toll, qui cuit, la
cuisson longue se lance **hors de sa journée**, sur l'horloge du MJ — il a été
coupé trois fois avant de comprendre ça.
