# Les journées — comment la ville se met à bouger

Le mouvement de Port-Réal ne se scripte pas et ne se simule pas. Il sort de
trois choses, et il n'y en a pas de quatrième :

1. **un besoin**, pas une jauge — sept lignes disent ce qu'un rôle fait de sa
   journée ;
2. **une adresse**, résolue au **bâtiment** et jamais à la personne ;
3. **un déphasage** tiré de l'identité par hachage — donc stable et gratuit.

Et la règle qui commande tout, la même que `scripts/presence.py` tient pour le
château : **la position ne se stocke pas, elle se calcule.**

## Les trois horloges

Il ne faut jamais les confondre.

| horloge | cadence | ce qui s'y passe | état gardé |
|---|---|---|---|
| l'image | 60 Hz | évaluer ~5 000 positions : des interpolations | **aucun** |
| la minute de jeu | quand le flux avance | on **lit** l'heure, on ne la simule pas | aucun |
| le jour | `tick.py` | les stocks, les seuils | l'état |

`ou(corps, minute)` est une **fonction pure**. Rien ne tourne en arrière-plan,
rien ne se sauvegarde, rien ne se rattrape : le joueur avance de trois heures
ou de trois jours, la ville est cohérente à l'instant d'après.

Le seul calcul un peu dense est la **journée** d'un corps — ses trois à cinq
sorties. Une fois par corps et par jour, gardée tant que sa cellule est chargée.

## Ce qui se passe où

| pièce | rôle |
|---|---|
| `scripts/monde/usages.py` | pose la **porte** de chaque bâtiment (colonnes `porte_x`, `porte_y`, `voie`) |
| `scripts/monde/besoins.py` | la **table des besoins** et les **adresses** de chaque bâtiment → `monde/portreal.besoins.json` |
| `ecrans/modules/monde/journee.js` | `journee()`, `chemin()` (A\*), `ou()` — tout le mouvement, côté page |
| `/monde/besoins` | sert la table et les adresses |

## La porte — sans elle, personne ne sort

Le graphe câblait 3 702 bâtiments sur 48 377 (les arêtes `entree`, de
`hall:<index>` vers la rue) : **un sur treize**. Les autres n'avaient aucun
point de contact avec la chaussée — un habitant y naissait au milieu de son mur.

`usages.py` calculait pourtant déjà la projection sur la rue, pour classer le
site ; elle était jetée aussitôt. On la garde, en projetant sur le **segment**
et non sur des points échantillonnés (trois points par segment suffisent à
classer une rue, pas à poser une porte).

Résultat sur les 48 377 bâtiments : **aucun sans voie**, distance
bâtiment → porte **médiane 7,4 m**, p90 11,7 m, max 48,5 m (69 bâtiments
au-delà de 40 m — des fonds d'îlot, et c'est juste).

## Les adresses — résolues au bâtiment

« Où Wat prend-il son eau ? » — au puits le plus proche de **son bâtiment**.
Donc 48 377 résolutions faites une fois, jamais 400 000. Et l'on y gagne ce qui
rend une ville lisible : **Wat va toujours au même puits**, on finit par
reconnaître les visages du coin de la rue.

À vol d'oiseau, et c'est voulu : l'**adresse** se choisit sur ce qu'on voit du
seuil, le **chemin** se calcule ensuite sur les rues.

| service | lieux | portée médiane | p90 |
|---|---|---|---|
| puits | 411 | **54 m** | 305 m |
| boulangerie | 956 | 36 m | 173 m |
| taverne | 1 141 | 101 m | 379 m |
| marché | 14 | 389 m | 728 m |
| septuaire | 59 | 151 m | 581 m |
| étuve | 43 | 286 m | 729 m |

## La table des besoins

Sept lignes pour quatre cent mille journées. Chacune porte : où l'on va,
combien de fois, le centre de la fenêtre horaire, sa **largeur**, la durée sur
place, et à qui elle s'applique (rang, âge, jours, `part`).

**La largeur est le seul vrai réglage du système.** À zéro, quarante ménages
sortent à six heures pile et la ville est un mécanisme d'horlogerie. Trop large,
la journée s'aplatit et il n'y a plus d'heure de pointe. Entre les deux, il y a
une foule.

`part` est le garde-fou contre l'absurde arithmétique : accorder l'étuve à toute
la ville une fois la semaine, c'est 1 300 personnes par étuve et par jour, et
quatre habitants sur dix qui se lavent en même temps le mardi. Le tirage vient
du même hachage que les heures — donc le même homme va aux étuves les mêmes
semaines, ce qui est exactement ce qu'on veut.

## Le chemin — sur les rues

A\* sur les 18 314 arêtes de surface, avec un coût par genre : une ruelle se
marche moins vite qu'une artère, et c'est ce qui fait que les flux prennent les
grandes rues. Un tas binaire, pas un tableau retrié.

**La topologie se lit dans la géométrie** : `/voirie` est une route de dessin,
elle ne transporte ni `de` ni `vers`. Deux arêtes qui partagent une extrémité
sont voisines — les coordonnées sont écrites au décimètre, la clef est donc
exacte. 18 314 arêtes donnent 15 586 nœuds, bâtis en 300 ms.

Un chemin se calcule **une fois par couple de bâtiments** et se met en cache.
Comme l'adresse est résolue au bâtiment, une cellule n'en demande qu'une
poignée.

**L'horaire se décide sur une estimation, la géométrie sur le vrai chemin** :
le vol d'oiseau majoré d'un tiers suffit à savoir si quelqu'un est en route, et
ça évite de calculer un A\* pour un homme qui dort. Sans cette séparation, un
passage à quatre heures du matin coûtait 21 secondes ; il coûte zéro.

## Le splatter de rue

Rien à voir avec le semis des domiciles, qui dit où l'on **loge** et ne bouge
jamais. Ici on marche :

- **latéral** : à moins de la moitié de la largeur de la voie moins une épaule.
  La largeur est dans la donnée (artère 8 m, rue 4,2, ruelle 2, quai 14) — une
  ruelle ne tient pas deux hommes de front, et ça doit se voir ;
- **le côté** : on tient sa droite, par hachage. Sans quoi deux flux inverses se
  traversent et la rue a l'air d'un banc de poissons ;
- **la vitesse** : 66 à 90 m/min selon l'identité. Un vieux, un enfant et un
  portefaix chargé ne marchent pas à la même allure ;
- **l'arrêt** : `sur-place` n'est pas de la circulation, c'est un tas immobile
  qui se résorbe. La file du puits à six heures est ce qu'on veut voir, et elle
  ne s'anime pas ;
- **le z** vient du **tracé**, qui porte la pente — jamais de l'étage du
  domicile, sans quoi le marcheur flotte au-dessus de la chaussée.

## Ce qu'on mesure

Cellule `11-3` (le cœur de la ville, 6 613 corps), 1 500 corps observés :

- **3,8 sorties par personne et par jour**, calculées en 3 ms pour 400 corps ;
- un passage horaire : **180 ms à froid** (les chemins se calculent), **5 ms à
  chaud** ;
- les 24 heures d'une journée entière, cache compris : **1,7 s**.

La courbe : rien avant six heures, la pointe de l'eau et du pain à 6-7 h, le
creux du milieu de journée, la reprise de midi, les tavernes de 20 à 22 h, et
plus rien après.

## La page d'essai — `/foule`

```bash
node serveur/serveur.js
```

puis `http://localhost:3129/foule`. Un point par habitant, vu du dessus, sur le
tracé des rues. La couleur dit **ce qu'on fait**, pas qui l'on est : gris
sourd chez soi, or en rue, bleu arrivé (la file du puits, l'étal, l'atelier).
Glisser pour se déplacer, molette pour approcher, réglages de vitesse (1 à
1 800 minutes de jeu par seconde réelle) et de rayon chargé.

Elle est en 2D et sans three.js à dessein : ce qu'on juge ici n'est pas le
rendu mais le **mouvement**, et une erreur de position saute aux yeux au lieu
de se cacher derrière une silhouette.

**Le journal.** La page verse dans `monde/journaux/foule-<horodatage>.jsonl`
(route `POST /foule/journal`), automatiquement dès 4 000 lignes en attente. On
n'y écrit **pas une position par image** — ce seraient des millions de lignes
qui ne disent rien — mais les **changements d'état** : untel part vers le
puits, untel y arrive, untel rentre. Une ligne porte l'heure, la cellule,
l'index, le rôle, l'âge, le sexe, le bâtiment, l'action et la position.

Rien de tout cela n'entre dans `etat/` : ce n'est pas de la partie, c'est de la
mesure.

## Ce qui manque encore

- **Les rondes du guet** sont écrites dans `besoins.py` (clé `rondes`) mais
  `journee.js` ne les joue pas : ce sont les seuls à devoir circuler après le
  couvre-feu, quand plus rien d'autre ne bouge. C'est le prochain morceau.
- **Le premier et le dernier tronçon d'un trajet** vont de la porte à l'axe de
  la rue : le marcheur y est donc légitimement à plusieurs mètres de l'axe
  (17 sur 44 marcheurs mesurés à 6 h 30). C'est la traversée du seuil, pas une
  erreur — mais si l'on veut des trottoirs francs, c'est là qu'il faudra
  raccorder proprement.
- **Le soir entre 16 h et 19 h est vide** : le labeur finit à 15 h 30 et la
  taverne n'ouvre qu'à 20 h. Il manque une ligne à la table.
- **Aucun rendu** : `journee.js` dit où sont les gens, personne ne les dessine
  encore.
