# La boucle des acteurs — déplacement, creux, questions

Spécification de refonte. **Remplace** `docs/travaux.md` (l'excitation), le champ
`echelle` de `intentions.json` (les budgets 5/20/∞), et `scripts/convoquer.py`
(qui doit une journée). Format de données : la ligne à porter dans
`docs/schema.md` est en fin de document.

---

## 0. Ce qui ne va pas, mesuré

Trois systèmes réglaient l'importance d'un acteur, et ils se marchaient dessus :
l'**échelle** (à la main), l'**excitation** (un compteur), la **force
narrative** (le graphe). Trois mesures pour une question.

Quatre chiffres relevés le 9 août sur l'état courant, avant d'écrire une ligne :

**(a) L'échelle est redondante — le graphe la connaît déjà.** `POIDS_ECHELLE`
(6/3/1) pèse dans `force_narrative`. En le retirant, le classement des dix
premiers ne bouge quasiment pas :

```
sans échelle   avec        qui                échelle
    46          49         steffon-darklyn    orbite
    33          36         rulf-corne         orbite
    27          33         aldon-hask         scene
    27          30         gerardys           orbite
    23          26         corlys             orbite     (+1 rang)
    21          27         robert-quince      scene
```

L'échelle ne mesure rien que les arêtes ne disent mieux : elle *recopie à la
main* ce que le tissu calcule. Sur les 15 premiers, 6 sont en `orbite` et 1 en
`royaume` — l'échelle et la force se contredisent déjà, et c'est la force qui a
raison.

**(b) La distribution des questions est un mur, pas une pente.** 53 têtes,
51 questions : `24 × 0 · 19 × 1 · 9 × 3 · 1 × 5`. Les paliers en valeur absolue
(`(40,5) (20,3) (10,1) (0,0)`) sont calibrés sur *cette* population. Médiane de
la force sans échelle : **7**. Moyenne 10, max 46. Une population de 12 têtes
s'effondrerait à zéro question pour tout le monde.

**(c) Presque personne n'a de journée.** 53 têtes, **25 ont une routine**, 28
n'en ont pas. Et 9 fiches de routine n'ont pas de tête. Les deux tables ne se
connaissent pas.

**(d) La distance en minutes ne veut rien dire hors du graphe des salles.**
`Chateau.chemin()` rend honnêtement un saut nu à coût **0** quand deux salles ne
sont reliées par aucune arête (`presence.py:126`). `chemins.json` ne porte que
les **34 salles de Peyredragon** ; Port-Réal n'y est pas. Résultat mesuré : dix-huit
personnes à « 0 minute » de la reine, dont Marlo Vasse au chantier de la Vase, à
Port-Réal.

> **Un quartier défini en minutes de marche placerait tout Port-Réal dans la
> salle du levant.** C'est le point qui décide de la section 1.

---

## 1. Comment se déplace-t-il ?

**Réponse : à la main, et seulement dans le quartier du joueur.**

Une bande horaire est un fait d'auteur. Rien ici ne s'infère — l'inférence ne
crée jamais un trajet, jamais une destination, jamais une activité.

### 1.1 Le quartier — deux conditions, jamais une

```
quartier(joueur) = { p : composante(salle(p)) == composante(salle(joueur))
                         ET duree(salle(joueur), salle(p)) <= RAYON_MINUTES }
```

La **composante connexe** d'abord, la durée ensuite. C'est la mesure (d) qui
l'impose : sans le test de composante, un coût de 0 rendu par un saut nu fait
entrer tout le reste du monde. Une salle absente de `chemins.json`, une salle
inconnue, une position non résolue → **hors quartier**, et on le dit.

- `RAYON_MINUTES = 20` à l'essai. Sur la topologie actuelle, ça couvre
  Peyredragon entier (max mesuré : ~15 min jusqu'au bourg) et exclut Port-Réal
  par la composante, pas par la distance. C'est voulu : le rayon devient mordant
  le jour où le château grandit, la composante mord tout de suite.
- **Un second siège occupé définit son propre quartier.** Le quartier est
  l'union des quartiers des sièges occupés (`joueurs.json`, `occupe`). Aurore à
  Port-Réal fait vivre le chantier de la Vase, la reine ne le fait pas.
- Le quartier se recalcule à chaque tick. Il n'est jamais stocké.

### 1.2 Hors quartier : il ne bouge pas

Aucun chemin, aucun escalier, aucune bande. `presence.resoudre()` ne le résout
pas et ne rend **rien** pour lui — pas une position par défaut, pas un « il
doit être à son poste ». Sa dernière position connue reste ce qu'elle est.

C'est aussi une économie réelle : sur 51 personnes résolues aujourd'hui, 14 le
sont par la source `perime` — c'est-à-dire par une exception morte, faute de
routine. Ce sont des positions inventées par défaut.

**Ce qui continue hors quartier :** les échéances. Une étape de plan dont
l'horloge tombe se produit quand même, comme aujourd'hui (`malgre_saut`). Le
quartier gèle la *position*, jamais le *calendrier*.

### 1.3 Dans le quartier : la routine, et les défauts sont manuels

Inchangé pour l'essentiel — `routines.json` et `presence.py` tiennent déjà la
bonne doctrine (une bande est une destination, on traverse vraiment, la salle
d'un joueur est gelée, un joueur n'a pas d'emploi du temps).

Deux ajouts :

- **Une activité donne son déplacement à la main.** Une bande peut porter
  `pourquoi` (ce qu'il y fait) et `ferme: true` (rien ne peut l'en tirer : il
  n'a pas de creux pendant cette bande, voir §2). Sans `ferme`, la bande est
  une simple destination et le temps y est disponible.
- **Un défaut de routine se déclare, il ne se devine pas.** Un homme du quartier
  sans fiche dans `routines.gens` est signalé par `--verifier`, jamais comblé
  par un modèle plausible. Aujourd'hui il retombe en silence sur `perime`.

---

## 2. À quoi réfléchit-il ?

**Réponse : dans les creux de sa boucle, et le nombre de questions se mesure sur
le graphe.**

C'est la pièce neuve, et elle remplace l'excitation en entier — plus de seuil de
parole à 3, plus de −1 par jour sans source, plus de `travaux.json`.

### 2.1 Le creux — ce que la routine ne dit pas

`presence.resoudre()` gagne une seconde sortie, pure et calculée dans la même
passe :

```
creux(p, jour) = 1440
               − Σ durée des bandes `ferme`
               − Σ minutes passées en chemin (déjà calculées par Dijkstra)
               − sommeil (la bande @dortoir est `ferme` d'office)
```

Un creux est un **intervalle**, pas un total : `[{de, a, salle}]`. C'est le
`salle` qui compte — une question posée pendant qu'il est à la roukerie n'a pas
les mêmes sources qu'une question posée au bourg.

Trois conséquences qui font le sujet :

- **Un homme sans creux ne pense pas ce jour-là.** Le castellan dont la journée
  est pavée de bandes fermées n'a aucune question, quelle que soit sa force.
  C'est ça, le coût d'un mandat : on l'occupe.
- **Un homme hors quartier n'a pas de creux** (il n'a pas de journée). Il ne
  pense pas non plus. C'est le budget qui se resserre tout seul sur ce que le
  joueur peut atteindre.
- Les creux sont **la seule ressource** que les questions consomment. Plus de
  `AFFAIRES_PAR_JOUR = 2` posé à la main : deux travaux tenaient parce que la
  journée n'en contenait pas plus. Maintenant la journée le dit elle-même.

### 2.2 La force — mesurée sur le graphe, et sur rien d'autre

`force_narrative` reste, moins l'échelle :

```
force = 1 × min(actions tenues, 12)
      + 5 × actions sur le chemin critique
      + 6 si l'homme tient un moyen saturé (≥ 20 demandes)
      + 2 × déclencheurs
      + min(croyances, 5)
```

`POIDS_ECHELLE` est **supprimé** — mesure (a). Les autres poids restent à
l'essai, en un bloc en tête de `evaluer.py`.

### 2.3 Le budget — en rangs, pas en seuils

C'est le « rééquilibrage par le graphe ». Les paliers absolus deviennent des
**quantiles sur la population du moment**, calculés parmi les seuls acteurs qui
ont un creux (donc dans le quartier) :

| rang dans la population éligible | questions |
|---|---|
| top 10 % | 5 |
| 10–30 % | 3 |
| 30–60 % | 1 |
| reste | 0 |

Le total de questions devient donc **proportionnel à la salle**, pas à la
taille du monde. Sur l'état courant (≈ 40 éligibles à Peyredragon), ça donne
environ 4×5 + 8×3 + 12×1 = **56 questions**, du même ordre que les 51
d'aujourd'hui — mais réparties sur ceux qui sont là, et stables si le casting
double ou fond de moitié.

Deux gardes :

- **Un plancher, pas un plafond.** Si moins de 6 acteurs sont éligibles, les
  quantiles dégénèrent : on retombe sur « les 3 plus forts ont 3 questions,
  les autres 1 ». Sinon un huis clos à quatre donnerait 5 questions à l'un et 0
  aux trois autres.
- **La force ne crée pas de creux.** Un homme fort et occupé ne pense pas. La
  force répartit un budget de temps existant, elle n'en fabrique pas.

### 2.4 Une question consomme un creux

Une question = un intervalle de creux consommé, avec sa salle. La sortie du
calcul est une **feuille de route par homme** :

```json
{"qui": "gerardys", "force": 30, "questions": 3, "creux_total": 410,
 "questions_posees": [
   {"de": 390, "a": 480, "salle": "roukerie"},
   {"de": 660, "a": 720, "salle": "table-peinte"},
   {"de": 1020, "a": 1140, "salle": "@dortoir"}]}
```

C'est exactement ce que `depecher.py` attend déjà : il sait sélectionner par
salle (`--salle`), par rayon (`--autour --rayon`) et par front (`--front`). Il
cesse de lire `convoquer.py` et lit cette feuille.

---

## 3. Quels résultats produit-il ?

**Réponse : ce qui retombe des questions, daté et sourcé — et rien ne se tient
en table.**

`travaux.json` disparaît (12 entrées aujourd'hui, dont **11 en `mur`** : la
table était devenue un cimetière de conclusions mûres jamais versées).

### 3.1 Ce qui survit de la chaîne

La contrainte d'entrée reste, et c'est la seule chose de `docs/travaux.md` qui
mérite de survivre :

> **Pas de source, pas de pensée.** Une pensée naît de quelque chose que l'homme
> a réellement touché — un registre, un homme écouté, une mesure qui a bougé, un
> pli arrivé.

Ce qui change : la source n'est plus déclarée d'avance dans `travaux.sources[]`.
Elle est **ce qui est à portée du creux** — les livres posés dans la salle
(`books.json`, `salle_id`), les gens qui s'y trouvent au même moment
(`presence`), les mesures dont il est porteur (`mains.json`). Le creux dit où
il est ; l'état dit ce qu'il y a là. On cesse de tenir une liste de courses à la
main.

### 3.2 Les trois sorties d'une journée

Une session dépêchée rend, dans `etat/staging/travaux/<qui>.json` (dépôt
inchangé — `verser_travaux.py` continue de le lire) :

1. **`journal[]`** — ses étapes horodatées. Inchangé.
2. **`pensees[]`** — datées, **sourcées**, rattachées à un creux et non plus à
   un `travail_id`. C'est ce qui supprime le raccrochage manuel d'ids que
   `depecher.travaux_ids()` existait pour réparer.
3. **`cahier2[]`** — les changements de registre en coordonnées exactes.
   Inchangé, et c'est le seul maillon que `mesurer.py` sait vérifier
   exactement.

**Les conclusions.** Plus d'état `mur` calculé par un compteur : une conclusion
est écrite ou elle ne l'est pas. Quand elle l'est, elle part dans `books.json`
et devient lisible par le joueur. C'est déjà la doctrine, et c'est la seule
partie qui marchait.

### 3.3 Ce que la salle en fait

Inchangé et central : **la salle LIT les pensées pour écrire ses phrases.**
`dossier.py --sur <id>` garde sa section « ce qu'il a en tête », alimentée par
les pensées du jour au lieu de `travaux.json`. On distille, on ne dévide pas.

Le marquage `servie` **disparaît**. Mesure de `mesurer.py` : 11 pensées marquées
sur 121 — le marquage n'était pas tenu, et son absence a fait croire à 91 % de
perte. Ce qu'on garde, c'est le seul chiffre qui portait quelque chose : **la
part des répliques du jour qui ne portent la trace d'aucune pensée** (40 % à la
dernière mesure). Il reste dans `mesurer.py`, sur les pensées du jour.

---

## 4. Ce qui disparaît, ce qui reste

| | |
|---|---|
| **Supprimé** | `etat/travaux.json` · `scripts/travaux.py` · `scripts/convoquer.py` · `scripts/verser_travaux.py` · `scripts/appliquer_travaux.py` · `docs/travaux.md` · `docs/session-travail.md` · le champ `intentions.echelle` · `POIDS_ECHELLE` · les budgets d'échelle de `schema.md` · la table d'échelle de `tick.py` · le marquage `servie` |
| **Modifié** | `presence.py` (portier de quartier + sortie `creux`) · `evaluer.py` (force sans échelle, budget en rangs) · `depecher.py` (lit la feuille de route, plus `convoquer`) · `dossier.py` (pensées du jour) · `mesurer.py` (le seul chiffre qui restait) · `tick.py --verifier` · `evaluer.pour_la_regie()` · `admin.html` |
| **Intact** | `routines.json` · `chemins.json` · le dépôt `staging/travaux/` · `books.json` · `mains.json` · `intentions.json` moins un champ · `tisser.py` et tout le tissu |

**À noter :** l'onglet régie affiche déjà la force, la présence, les convocations
et le camp d'en face (`admin.html:246, 273, 295`). Le tableau « servi ✅ /
affiché ❌ » est périmé — cette passe a déjà été faite. Ce qu'il reste à faire
sur `admin.html`, c'est de remplacer les convocations par les **creux** et
d'afficher le quartier.

---

## 5. Ce que `--verifier` doit attraper après

- une tête **dans le quartier sans fiche de routine** — elle retombera sur
  `perime`, c'est-à-dire sur une position inventée (14 cas aujourd'hui) ;
- une **fiche de routine sans tête** (9 cas aujourd'hui) ;
- une **salle de routine absente de `chemins.json`** — elle rendra des sauts nus
  à coût 0, et c'est la faute (d) ;
- une **journée entièrement fermée** chez un homme à forte force : il ne pensera
  jamais, et c'est peut-être voulu — mais il faut le voir ;
- une **pensée sans source ou sans date** ;
- un **quartier vide** : aucun siège occupé résolu, donc personne ne pense.

---

## 6. Ordre d'exécution

1. **`presence.py`** — composante connexe, portier de quartier, sortie `creux`.
   Testable seul : `python scripts/presence.py --quartier` doit exclure
   Port-Réal et rendre ~40 personnes à Peyredragon.
2. **`evaluer.py`** — retirer `POIDS_ECHELLE`, passer `PALIERS` en quantiles sur
   les seuls éligibles, produire la feuille de route. Test de non-régression :
   le top 6 doit rester steffon-darklyn, rulf-corne, aldon-hask, gerardys,
   corlys, robert-quince.
3. **`depecher.py`** — lire la feuille, retirer `a_convoquer()` et
   `travaux_ids()`.
4. **Suppressions** — les cinq scripts, la table, les deux docs, le champ.
5. **`CLAUDE.md`** — réécrire « La boucle des pensées », « Casting dynamique »
   et les budgets d'échelle. C'est le plus gros morceau de prose.
6. **`admin.html`** — les creux à la place des convocations, le quartier en tête.

---

## 7. La ligne pour `docs/schema.md`

`travaux.json` sort de la source de vérité. `intentions.json` perd `echelle`.
Rien n'entre : `routines.json`, `chemins.json` et `presence.json` sont déjà
déclarés techniques et hors schéma, et les creux sont **calculés, jamais
stockés** — comme la position, et pour la même raison.

> **Le seul changement à porter dans `docs/schema.md`** : retirer le champ
> `echelle` de la fiche `intentions.json` et le tableau des budgets par échelle
> qui la suit, en renvoyant à ce document pour ce qui les remplace.
