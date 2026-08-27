# L'architecture du système de combat

Ce document présente **la solution** : le modèle retenu, les décisions qui le
constituent, les options écartées et pourquoi, et comment s'y retrouver.

Les fiches de module disent *ce que chaque pièce fait*. Celui-ci dit *pourquoi
les pièces sont celles-là*, et ce qu'on a refusé en chemin.

---

## 1. Le problème qu'on résout

Le moteur précédent tenait dans un fichier de onze mille lignes. Il marchait — il
produisait des batailles — et il était devenu impossible à faire évoluer. Les
symptômes mesurés dans une seule session de diagnostic :

| symptôme | mesure |
|---|---|
| aucune forme déclarée | un homme portait **174 champs**, écrits depuis **229 endroits** |
| l'état éparpillé | **65 variables libres** au niveau du fichier |
| l'ordre des opérations invisible | la fonction du battement faisait **855 lignes** avec **38 sorties anticipées** |
| la délibération contournée par construction | l'arbitre était consulté à la **236ᵉ** ligne de cette cascade |
| une couche de décision selon le chemin pris | calculée à la **680ᵉ** ligne, elle manquait à **104 hommes sur 239** |
| conséquence directe | **43 %** de l'armée était arbitrée comme n'ayant reçu aucun ordre |
| ce que l'écran racontait | **46** des **56** endroits qui écrivaient une pensée nommaient une branche de code, pas une cause |
| les chargements divergents | **huit** listes de scripts, dont deux avaient dérivé sans que personne le sache |
| la mesure qui ne mesurait rien | la condition d'étalon était une bataille où **le fer ne se touchait jamais** |

**Aucun de ces défauts n'est une faute de programmation.** Ce sont des
conséquences mécaniques d'une architecture absente : quand ajouter à un fichier
coûte moins cher que créer un module, tout finit dans le fichier ; quand rien ne
déclare une forme, les fautes de forme se découvrent à l'exécution ; quand rien
ne mesure la structure, la structure dérive.

**L'architecture est ce qui rend la bonne chose moins chère que la mauvaise.**
C'est le critère auquel toutes les décisions ci-dessous répondent.

---

## 2. La solution en une page

Un empilement de **dix couches numérotées**, où la dépendance ne va que dans un
sens, et où chaque donnée a un propriétaire unique.

```mermaid
flowchart TB
    S["10 · socle<br/><i>hasard, horloge, mesures, identité, formes, journal, manifeste</i>"]
    M["20 · monde<br/><i>terrain, bâti, seuils, navigation, mouvement, contact, coup, densité, dangers</i>"]
    P["30 · perception<br/><i>portées, vue, ouïe, fait</i>"]
    C["40 · combattant<br/><i>identité, 5 couches, mémoire, geste</i>"]
    U["50 · unité<br/><i>identité, chef, forme, cohésion, allure, rupture, détachement</i>"]
    T["60 · transmission<br/><i>ordre, message, porteur, canal</i>"]
    K["70 · commandement<br/><i>croyances, estimation, options, projection, décision, coordination</i>"]
    G["80 · conduite<br/><i>objectif, mission, allocation, réserve</i>"]
    O["90 · observation<br/><i>sondes, étalon, trace, rendu, marque</i>"]

    S --> M --> P --> C --> U --> T --> K --> G
    O -. lit tout, n'écrit rien .-> S
    O -. .-> G
```

Trois lois gouvernent l'ensemble :

- **La dépendance ne remonte jamais.** Un module ne lit que des couches — et, dans
  sa couche, des rangs — strictement inférieurs. Ce qu'il ne peut pas importer,
  il le **reçoit** en argument sans savoir d'où ça vient.
- **Chaque donnée a un écrivain unique.** Les autres la lisent, ou lui remettent
  une **intention**. Le propriétaire décide de ce qui arrive.
- **Nul acteur ne lit ce qu'il n'a pas perçu.** Ce qui monte au-dessus de la
  perception, ce sont des croyances : datées, sourcées, faillibles.

---

## 3. Les décisions structurantes

### 3.1 · Le découpage se fait par couche de dépendance, pas par acteur

**Décision.** Les modules sont rangés par ce dont ils dépendent, et le rangement
est la règle de dépendance elle-même.

**Pourquoi.** Le document précédent découpait par **acteur** — général,
commandant, unité, combattant, monde. C'est une belle carte mentale et un mauvais
découpage de code : elle proposait deux fichiers nommés « mouvement », un pour le
monde et un pour l'unité, alors que la fonction qui déplace un corps sert tout le
monde — les hommes, les guides, les coureurs, les fuyards. **Elle ne coupe pas là
où le code se coupe.**

Une couche numérotée, elle, se vérifie par un script : toute dépendance qui
remonte est refusée. C'est la seule formulation qui ne demande pas de jugement.

**Écarté.** Le découpage par acteur (garde son rôle : c'est le vocabulaire du
domaine, pas l'arborescence du code). Le découpage par « feature ». Le découpage
par phase du battement — qui ferait dépendre l'arborescence d'un ordre
d'exécution qu'on veut pouvoir changer.

**Coût accepté.** Un lecteur qui cherche « tout ce qui concerne un chef » doit
regarder dans trois couches. On l'accepte : c'est le prix d'une frontière qui
tient.

### 3.2 · Des fabriques et de l'injection, pas des classes ni des globales

**Décision.** Un module est une fabrique : elle reçoit ce dont elle a besoin et
rend un objet de fonctions. Aucune globale, aucun héritage, aucun singleton.

**Pourquoi.** Ce qu'on veut d'un module, c'est qu'on puisse le **construire seul**
pour le mesurer. Une fabrique qui reçoit ses dépendances se teste avec des
doublures ; un module qui va chercher une globale ne se teste qu'en montant le
moteur entier.

**Écarté — l'héritage et le polymorphisme par entité.** L'objection n'est pas la
performance : c'est la **lisibilité de l'ordre**. Le défaut le plus coûteux du
moteur précédent était que l'ordre des opérations d'un battement était invisible,
noyé dans une cascade de 855 lignes. Répartir cette logique en méthodes sur des
objets rendrait cet ordre **encore moins visible**, pas plus. Une simulation à
deux mille cinq cents corps veut des passes explicites sur des données, pas du
dispatch par entité.

**Écarté — un système entités-composants.** Il résout le stockage et l'itération,
qui ne sont pas nos problèmes. Il rend en revanche l'**autorité diffuse** : dans
un tel système, n'importe quel système écrit n'importe quel composant, ce qui est
exactement le défaut qu'on répare. On garde son bon côté — des passes sur des
données — sans son modèle de propriété.

**Ce qu'on prend quand même des classes.** Les entités qui ont une identité et
des invariants — un homme, une unité, un ordre — ont **une forme déclarée en un
seul endroit** ([`10-socle/formes`](10-socle/formes.md)). Pas pour du
polymorphisme : pour qu'il existe un endroit unique disant ce qu'un homme
possède, au lieu de 174 champs poussés depuis 229 sites.

### 3.3 · Un homme ne se déplace pas : il remet une intention

**Décision.** Un combattant produit une **intention de geste** — marcher dans
cette direction, à cette allure, pour cette raison — et la remet au monde. Le
monde applique l'accélération, teste le bâti, résout les contacts, et décide de
la position.

**Pourquoi.** C'est ce qui rend racontables, sans une ligne de code qui les
raconte, la bousculade, la venelle trop étroite, la masse trop dense. L'homme
peut vouloir et **ne pas obtenir** — et c'est le sujet du jeu.

C'est aussi ce qui rend l'invariant tenable : **une seule fonction au monde écrit
une position.** Pas « en général » : une. C'est la différence entre « la traversée
de mur est rare » et « la traversée de mur est impossible ».

**Le piège que ça n'évite pas tout seul.** Le moteur précédent tenait cet
invariant pour la position — et avait un **second écrivain de la vitesse**, caché
dans une branche de déroute, qui contournait le plafond d'accélération et le
bonus de monture. Personne ne le savait. Un écrivain unique n'est vrai que s'il
est **vérifié** : c'est une sonde, pas une intention.

### 3.4 · L'ordre du battement est déclaré, pas subi

**Décision.** Un battement est une suite de passes explicites, écrite en un seul
endroit. Ce qui doit être moins fréquent l'est par un **calendrier de décision**,
jamais parce que le code passe ou ne passe pas par là.

```
1. horloge          avancer d'un pas
2. monde            index spatial, conséquences encore actives
3. transmission     livrer les messages arrivés à portée
4. perception       produire les faits dus à ce battement
5. mémoires         assimiler faits, souvenirs, ordres reçus
6. délibérations    celles dont l'échéance est atteinte, et elles seules
7. transmission     propager les ordres nouveaux
8. unités           intentions collectives
9. combattants      arbitrer, produire une intention de geste
10. monde           mouvement, contact, coup, densité, seuils
11. signalements    faits, traces, mesures
12. agrégats        état des unités et des commandants pour le battement suivant
```

**Pourquoi.** Dans le moteur précédent, une couche de délibération était calculée
à la 680ᵉ ligne de la cascade : **seuls les hommes dont le battement descendait
jusque-là l'obtenaient** — 135 sur 239, alors que les 239 avaient tout ce qu'il
fallait. Et comme cette couche fixait la barre que les autres prétendants
devaient franchir, **43 % de l'armée décidait sans barre**, donc comme n'ayant
reçu aucun ordre.

Ce n'était pas un bug : c'était la conséquence d'un ordre implicite. Un ordre
déclaré rend ce défaut impossible à écrire.

**Coût accepté.** Une passe coûte un parcours de plus. On le paie : c'est moins
cher qu'une couche dont la disponibilité dépend du chemin.

### 3.5 · Ce qui monte est une croyance, jamais la vérité

**Décision.** Au-dessus de la perception, personne ne lit l'état du monde. Un
chef lit **ses croyances** : datées, sourcées, avec une confiance qui décroît, et
un **intervalle** quand il s'agit d'un effectif.

**Pourquoi.** Un acteur qui décide sur des croyances fausses prend des décisions
fausses **et a raison de les prendre**. C'est ce qui rend une bataille
racontable.

**Le défaut à ne pas reproduire.** Le moteur précédent tenait très bien la moitié
perception : croyances signées, datées, vieillissantes, et une sonde confirmait
qu'un chef ne voyait pas à travers les murs. Ce qui manquait, c'est un
**consommateur**. Le seul module qui déduisait une posture depuis les croyances
écrivait son résultat dans un champ **que personne ne lisait**, et il n'existait
aucun chemin pour qu'un chef change son ordre depuis un renseignement.

Mesuré : quarante et une observations typées transmises, plus de quatre cents
communications entre chefs — et **zéro ordre adapté sur quinze chefs**.

**Un brouillard sans décision au travers est un ornement coûteux.**

### 3.6 · Le déterminisme est une contrainte dure

**Décision.** À condition identique et graine tenue, la bataille est exactement
la même. Une seule urne, dans le socle ; aucune horloge de plateforme ; l'ordre
des tirages fait partie du résultat.

**Pourquoi.** Sans lui, **aucune mesure ne prouve rien** : on ne peut ni comparer
un avant et un après, ni rejouer un défaut, ni distinguer une amélioration d'un
tirage heureux.

Sa conséquence la plus utile : **un déplacement de code doit rendre l'égalité
exacte.** Si l'on déplace sans intention de changer et que la bataille diffère,
c'est qu'on a changé quelque chose sans le savoir. C'est le seul filet qui rende
un démantèlement sûr — il a tenu quatre fois de suite sur le moteur précédent.

**Coût accepté, et il est réel.** Ajouter, retirer ou déplacer un tirage rebat
tout ce qui suit. Une réorganisation qui semble gratuite ne l'est pas si elle
déplace un tirage — et cela a suffi, en pratique, à reporter un changement qu'on
croyait cosmétique.

### 3.7 · L'observation est une couche, et elle n'écrit rien

**Décision.** Sondes, étalon, traces, rendu et marques forment une couche qui lit
tout et n'écrit rien dans la simulation. Personne, en dessous, ne la connaît : un
module **signale**, le câblage se fait à la construction.

**Pourquoi.** Une sonde qui vivrait dans le moteur devrait y être ajoutée — donc
modifier ce qu'on cherche justement à laisser intact pendant un déplacement. Une
sonde extérieure **ne peut pas fausser l'étalon**, et c'est ce qui la rend
utilisable pendant un démantèlement.

Et parce que la dépendance ne remonte pas : si un module d'unité connaissait
l'écrivain des annales, la couche 50 dépendrait de la couche 90. C'est exactement
ce qui est arrivé, et personne ne l'a vu passer.

**Ce qu'on y ajoute et qui n'existait pas : les sondes d'architecture.** Aucune
dépendance qui remonte, aucun module hors taille, aucune globale, un seul
écrivain par donnée, un seul manifeste. Sans elles, tout ce document a la durée
de vie de la table d'autorité qui l'a précédé — juste, vérifiée nulle part, et
contredite par le code sans que personne le remarque.

---

## 4. Comment les modules sont organisés

### Le nommage

`<couche>/<module>.md`, et le numéro de couche est la règle de dépendance. À
l'intérieur d'une couche, les modules ont un **rang** déclaré au manifeste : un
module ne lit que des rangs inférieurs au sien. L'ordre du monde, par exemple :
terrain, bâti, seuils, navigation, mouvement, contact, coup, densité, dangers.

Sans ce rang, la règle serait trouée exactement là où le code est le plus dense.

### Le gabarit

Chaque fiche a sept sections, et l'ordre n'est pas décoratif : *ce que c'est*,
*ce qu'il possède*, *ce qu'il lit*, *ce qu'il produit*, *ses invariants*, **ce
qu'il ne fait pas**, et *ce que l'ancien moteur faisait mal ici*.

La sixième est celle qui empêche un module de grossir : c'est la liste écrite de
ce qu'il refuse. La septième est la raison d'être du dossier — elle ne contient
que des chiffres relevés, ou la phrase disant que le point n'a pas été mesuré.

### Où chercher quoi

| la question | la fiche |
|---|---|
| qu'y a-t-il à cet endroit du sol ? | [`20-monde/terrain`](20-monde/terrain.md) |
| par où passe un groupe ? | [`20-monde/navigation`](20-monde/navigation.md) |
| qui écrit une position ? | [`20-monde/mouvement`](20-monde/mouvement.md) |
| pourquoi cet homme fait-il ça ? | [`40-combattant/arbitre`](40-combattant/arbitre.md) |
| que sait cet homme ? | [`40-combattant/memoire`](40-combattant/memoire.md) |
| qui commande cette unité ? | [`50-unite/chef`](50-unite/chef.md) |
| pourquoi le groupe ralentit-il ? | [`50-unite/allure`](50-unite/allure.md) |
| que croit ce chef ? | [`70-commandement/croyances`](70-commandement/croyances.md) |
| pourquoi a-t-il choisi ça ? | [`70-commandement/decision`](70-commandement/decision.md) |
| comment le sait-on ? | [`90-observation/trace-de-decision`](90-observation/trace-de-decision.md) |

---

## 5. Voir l'architecture à l'œuvre

### Un ordre qui descend

Le général révise sa conduite et crée une **mission** : contrôler cette place,
avec ses conditions de succès et d'abandon ([`80-conduite/mission`](80-conduite/mission.md)).

Un commandant la reçoit. Il consulte **ses croyances** — jamais l'état du monde —,
en tire une estimation, énumère les **options** réellement ouvertes, en projette
quelques-unes sur un horizon grossier, en choisit une, et écrit **pourquoi**
([`70-commandement/decision`](70-commandement/decision.md)).

Sa décision devient un **ordre littéral** : un résultat et des contraintes,
jamais une liste de coordonnées. Un canal l'achemine — voix, signe, ou porteur
qui cherche une identité mobile et peut mourir en chemin
([`60-transmission/porteur`](60-transmission/porteur.md)).

L'unité destinataire le reçoit et le transforme en **contraintes de forme** et en
route de groupe. Chaque homme en garde **sa propre copie datée** : ce qu'on lui a
dit, et quand — pas ce qu'on dit maintenant à sa place.

Ses couches délibèrent, l'arbitre élit laquelle tient les jambes, et il en sort
**une intention de geste**. Le monde décide de ce qui arrive.

**Neuf couches, et à chaque étage la chose peut se déformer, se retarder, ou ne
pas arriver.** C'est le sujet, pas un défaut.

### Une perception qui monte

Un homme voit quelque chose. La perception produit un **fait** : auteur, date,
lieu, sens, source, confiance, et un intervalle si c'est un effectif.

Le fait entre dans **sa** mémoire, et nulle part ailleurs. S'il est chef, il
entre aussi dans ses croyances, avec son âge et sa confiance. S'il rencontre un
pair, il peut le lui transmettre — et le fait devient *rapporté*, avec ce que
cela coûte en fiabilité.

**Rien ne remonte automatiquement.** Un commandant qui n'a pas de témoin ne sait
rien, et il décidera quand même.

---

## 6. Ce que cette architecture ne résout pas

Il faut le dire, sinon elle promet plus qu'elle ne tient.

- **Elle ne rend pas le comportement juste.** Elle rend les fautes locales et
  nommées. Un moteur parfaitement découpé peut produire une bataille absurde.
- **Elle ne remplace pas les mesures.** Chaque loi de ce document est un vœu tant
  qu'une sonde ne la vérifie pas. C'est la leçon la plus chère du moteur
  précédent : sa table d'autorité était juste et n'était appliquée nulle part.
- **Elle a neuf frontières douteuses**, listées dans
  [`00-principes/08-tensions-connues.md`](00-principes/08-tensions-connues.md).
  Quand l'implémentation résiste à l'une d'elles, c'est probablement la fiche qui
  a tort.
- **Elle ne dit rien du rendu ni de l'interface**, au-delà de ce qui doit être
  visible pour diagnostiquer.
- **Elle ne dit pas dans quel ordre construire.** Ce n'est pas un plan de
  travail.
