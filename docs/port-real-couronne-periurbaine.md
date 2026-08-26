# La couronne périurbaine de Port-Réal

> **Statut : état cible et contrat d'implémentation.**  
> Ce document décrit ce que les environs de Port-Réal doivent devenir, comment
> on les construit et ce qui prouve qu'une tranche est terminée. Il ne décrit
> pas l'état actuel comme s'il était déjà juste. Les nombres historiques sont
> des ordres de grandeur ; les nombres de formes à produire sont des budgets de
> conception, révisables seulement après une comparaison visuelle et mesurée.

---

## 0. La phrase qui commande tout

**À l'échelle de `/bataille`, Port-Réal ne doit pas être une ville posée dans
du vide, mais le centre d'un paysage entièrement occupé à la nourrir, la
chauffer, la vider et la relier à la mer.**

Cela interdit quatre raccourcis :

1. une route régionale ne peut pas être un trait qui ne dessert rien ;
2. un champ ne peut pas être un aplat décoratif sans parcelles ni accès ;
3. un bâtiment visible ne peut pas être absent du masque de collision ;
4. un port ne peut pas être une série de jetées propres posées sur une côte
   inchangée.

La cible est une **géographie causale** : chaque forme existe parce qu'elle
dessert, draine, produit, protège, stocke ou transborde quelque chose.

---

## 1. Ce que nous avons aujourd'hui

### 1.1 Mesure au commit `ce8d4bd`

| Élément | État actuel |
|---|---:|
| Emprise régionale affichée | 7,92 × 4,98 km |
| Surface approximative intramuros | 7,02 km² |
| Silhouettes bâties intramuros | 48 555 |
| Routes régionales | 5 |
| Grandes zones de terrain | 7 |
| Lieux régionaux | 4 |
| Toits régionaux engendrés | 81 |
| Houppiers régionaux engendrés | 95 |
| Quais / appontements / bassins | 4 / 4 / 2 |

Le contraste **48 555 / 81** explique l'impression de vide. Les cinq routes
ont désormais une géométrie courbe, mais la campagne qu'elles traversent ne
possède pas encore la densité d'occupation d'une grande capitale.

### 1.2 Dette technique qui passe avant la densification

Les 81 toits régionaux sont aujourd'hui cuits dans `plan.region.bourgs`. Ils
sont dessinés, mais ils ne passent pas par la même chaîne que le bâti urbain :

```text
toit régional ──► SVG
              ╳► masque de collision
              ╳► graphe d'accès
```

Cette divergence est acceptable pour un essai visuel de quelques signes ; elle
est interdite pour l'état cible. Avant de multiplier les toits, les bâtiments
régionaux doivent produire **une seule géométrie finale**, consommée par :

- le dessin de la carte ;
- le masque de collision ;
- les entrées et dessertes du graphe ;
- les tests qui comparent ces trois projections.

---

## 2. Modèle historique retenu

Port-Réal n'a pas un équivalent unique. La transposition retenue combine :

- la masse et la fonction politique de Paris ou Constantinople ;
- l'estuaire et le ravitaillement maritime de Londres ;
- un climat tempéré maritime plus doux, autorisant vigne, vergers et une longue
  saison maraîchère, sans faire de toute la Couronne une Méditerranée sèche.

### 2.1 Les anneaux fonctionnels

Les distances sont comptées depuis la courtine. Elles se déforment le long des
routes, de la Néra et du rivage : ce ne sont pas des cercles géométriques.

| Distance | Fonction dominante | Formes attendues |
|---|---|---|
| 0–100 m | Défense et circulation | fossé, talus, chemin du mur, portes, terrains volontairement dégagés |
| 100–800 m | Faubourgs et services | maisons-rues, auberges, écuries, marchés aux bêtes, jardins, cimetières, métiers encombrants |
| 0,5–3 km | Production fraîche | maraîchage, vergers, vignes, prés, moulins, canaux, fermes, manoirs et maisons religieuses |
| 3–12 km | Ravitaillement régional | villages, grands champs céréaliers, pâtures, bois exploités, routes de marché |
| au-delà | Logistique de masse | grain, bois, pierre, sel et denrées conservables par mer, fleuve et grands chemins |

Un hinterland de marché médiéval ordinaire peut déjà porter à 8–12,5 km ; une
mégapole ne se nourrit pas de ce seul anneau. La couronne détaillée dit ce qui
doit arriver frais. La carte du royaume dit d'où viennent les volumes.

### 2.2 Ce que le sol doit raconter

- Les fonds humides portent prés, pâture, roseaux, drainage et chemins sur levée.
- Les terres profondes portent des blocs céréaliers divisés en longues lanières.
- Les sillons ne sont pas des rayures droites : les attelages produisent des
  lignes légèrement courbes et des retours en S.
- Les pentes bien exposées portent vigne, vergers et clos.
- Les bois proches sont gérés, coupés et parcourus ; ce ne sont pas des forêts
  intactes posées comme des taches.
- Les produits périssables et lourds se rapprochent de la ville selon le coût
  du transport : légumes, lait, foin et bois court près des portes ; grain et
  troupeaux plus loin ; denrées de masse sur l'eau.

### 2.3 Ce que le port doit raconter

Le front d'eau est une succession d'initiatives et de reprises, pas un ouvrage
unique :

- revêtements de bois puis portions de pierre ;
- petites propriétés de quai aux largeurs inégales ;
- terre gagnée par étapes sur la vase ;
- escaliers d'eau, cales, grèves d'échouage et appontements ;
- bassins étroits entretenus, chenaux, pieux et brise-courants ;
- entrepôts et ateliers immédiatement derrière leur quai ;
- chantiers, corderies, poisson, sel, grain et bois séparés par usage.

La côte urbaine doit donc changer de forme avec le port. Ajouter des traits sur
la côte sans produire de terre-plein, de bassin ou de propriété riveraine ne
compte pas comme une amélioration portuaire.

---

## 3. Emprise et cadrages cibles

### 3.1 Deux emprises, pas un compromis

La région doit avoir une emprise complète plus vaste sans rapetisser Port-Réal
à l'ouverture.

| Nom | Coordonnées source | Dimensions | Usage |
|---|---|---:|---|
| `cadrage_initial` | `[-125,-65,535,350]` | 7,92 × 4,98 km | ouverture actuelle de `/bataille` |
| `emprise_detaillee` | `[-1000,-1050,1500,1350]` | 30 × 28,8 km | pan, zoom arrière, armées et routes d'approche |

`1 unité source = 12 m`. Le premier cadrage reste centré sur la ville. Le
second laisse environ douze kilomètres de paysage praticable autour de la
courtine et devient visible en dézoomant ou en se déplaçant. Il contient Rosby
à une vraie distance régionale, le cours amont de la Néra et assez de baie pour
que Port-Réal soit un site d'estuaire plutôt qu'une ville collée au bord du
cadre. Le rendu ne doit plus déduire son cadrage initial des seules bornes du
plan.

### 3.2 Enveloppes d'interaction

Trois niveaux évitent de payer la même précision partout :

| Niveau | Étendue | Précision et autorité |
|---|---|---|
| `coeur` | ville + 1 km | sol, eau et obstacles à 1 m ; graphe complet |
| `couronne` | reste de l'emprise détaillée | relief à 30 m ; futurs obstacles tuilés à 1–2 m ; routes et bâtiments solides |
| `horizon` | au-delà | symboles et axes de la carte du royaume, non jouables dans `/bataille` |

Un objet n'est jamais rendu comme un bâtiment dans une enveloppe jouable s'il
n'y est pas solide. À l'horizon, il doit être rendu comme un signe de bourg ou
de paysage, pas comme un toit à l'échelle des hommes.

### 3.3 Contrat topographique

- `monde/portreal.terrain.json` reste l'autorité fine du cœur à 10 m.
- `monde/portreal.region-terrain.json` couvre 30 × 28,8 km à 30 m.
- Dans le cœur, chaque nœud régional recopie le raster fin ; hors du cœur, le
  raccord se fait progressivement sur 900 m.
- Les massifs, vallons et niveaux demandés vivent dans
  `scripts/ville/port-real-region.json` ; le raster est entièrement dérivé.
- Les courbes régionales du plan sont extraites de ce raster aux niveaux 5,
  10, 20, 30, 40, 55, 70, 85, 100 et 120 m. Les ovales indicatifs dessinés à
  la main ne constituent jamais l'autorité finale.
- Toute grande route doit rester sous 10 % de pente instantanée, sauf ouvrage
  ou lacet explicitement décrit.

### 3.4 Contrat d'occupation dérivée

- `scripts/monde/occupation_region.py` lit le relief régional ; il ne possède
  ni altitude ni hydrographie concurrente.
- Les cinq grandes routes et les lieux nommés restent écrits à la main. Chaque
  axe reçoit une part minimale du semis rural afin que la seule plaine la plus
  plate ne capte pas toute l'occupation.
- Les champs forment des blocs de lanières parallèles orientés principalement
  par les courbes de niveau, et secondairement par la route la plus proche.
- Les bois occupent les hauteurs, les pentes et les terrains éloignés des
  routes ; les fermes prennent les sols secs et accessibles.
- Chaque ferme rejoint une grande route par un A* régional à 120 m. L'eau est
  infranchissable et la pente est un coût mesuré, pas un effet graphique.
- La sortie `monde/portreal.region-occupation.json` est dérivée et recuite
  automatiquement avant le plan 2D.

---

## 4. Inventaire mesurable de l'état cible

Ces budgets décrivent la **couronne détaillée**, hors des 48 555 silhouettes
intramuros. Ils empêchent de déclarer la tâche finie après quelques symboles.

### 4.1 Occupation du sol

| Famille | Budget cible |
|---|---:|
| Lanières agricoles lisibles | 350–650 |
| Blocs de lanières céréalières | 45–80 |
| Jardins maraîchers | 25–45 |
| Vergers et clos viticoles | 20–35 |
| Prés et pâtures | 12–24 |
| Bois gérés, taillis et réserves | 6–12 |
| Étangs, viviers et bassins ruraux | 3–8 |

Au moins **90 % du sol terrestre** de `l'emprise_detaillee` reçoit un usage.
Dans le premier kilomètre hors les murs, cette couverture atteint **97 %** :
un terrain peut être dégagé, en friche, boueux ou pollué, mais jamais seulement
« vide ».

### 4.2 Peuplement

| Famille | Budget cible |
|---|---:|
| Toits extramuros solides | 2 500–4 500 |
| Faubourgs nommés | 5 minimum, un par grande porte routière |
| Bourgs et hameaux détachés | 6–12 |
| Fermes ou cours isolées | 80–160 |
| Domaines religieux, hospitaliers ou seigneuriaux | 5–10 |
| Cimetières extramuros | 3–6 |

Un faubourg n'est pas un cercle de maisons autour d'un point. C'est un ruban
épais le long d'une route, interrompu par des cours, jardins, murs de domaine,
carrefours et marchés.

### 4.3 Circulation et eau

| Famille | Budget cible |
|---|---:|
| Grandes routes historiques | 5, écrites à la main |
| Chemins charretiers secondaires | 25–45 |
| Sentiers et dessertes de parcelle | 60–120, visibles seulement au bon zoom |
| Ponts, gués et ponceaux | 8–16 |
| Fossés de drainage nommés ou structurants | 3–6 |
| Biefs ou canaux de moulin | 2–4 |
| Moulins à eau ou à vent | 6–12 |

Aucun chemin secondaire n'est semé avant les parcelles qu'il dessert. Le
générateur part des accès nécessaires et rejoint le réseau existant ; il ne
dessine jamais une toile aléatoire pour « faire campagne ».

### 4.4 Port

| Famille | Budget cible |
|---|---:|
| Propriétés ou unités de front d'eau | 12–20 |
| Quais et débarcadères actifs | 8–14 |
| Cales et grèves d'échouage | 2–4 |
| Bassins, anses ou chenaux entretenus | 3–6 |
| Terrasses gagnées sur la vase | 3–6 générations lisibles |
| Entrepôts et ateliers portuaires | 100–250 toits |

Les nombres simultanés ne recopient pas les 36 états archéologiques successifs
d'un même quai londonien. Ils traduisent une propriété essentielle : un grand
front portuaire médiéval est **morcelé, réparé et construit par étapes**.

---

## 5. Les invariants durs

### 5.1 Géographie

1. Une route terrestre ne traverse jamais l'eau sans ouvrage typé.
2. Un quai ou appontement peut avancer sur l'eau seulement si son type
   l'autorise et si son départ touche un terre-plein ou un autre ouvrage.
3. Une maison ne coupe ni route, ni fossé, ni rive active.
4. Un moulin reçoit une énergie réelle : pente, courant ou vent exposé.
5. Un terrain humide ne reçoit pas le même semis qu'un coteau sec.
6. Les grandes routes partent des sept portes qui existent, pas d'un point
   approché dans l'enceinte.

### 5.2 Une seule géométrie, plusieurs projections

```text
source manuelle + graine + règles
              │
              ▼
      géométrie finale par zone
        │          │          │
        ▼          ▼          ▼
      dessin      masque     graphe
```

- Les polygones de toit finaux sont soudés et arrondis **avant** dessin et
  rasterisation.
- L'eau qui remplit le rendu produit aussi l'obstacle hydraulique.
- La largeur routière lue par les unités est celle qui réserve l'espace entre
  les façades.
- Un test doit retrouver zéro cellule de bâtiment dessinée libre au
  pathfinding, dans la ville comme hors les murs.

### 5.3 Déterminisme et reprise

- Chaque zone possède une graine explicite et stable.
- Une cuisson de zone ne réécrit pas les autres zones.
- À source et version identiques, deux cuissons ont le même hash.
- Une correction manuelle se fait dans la source, jamais dans le JSON cuit.
- Les sorties générées par zone peuvent être supprimées et reconstruites sans
  perdre un nom, une route ou une décision humaine.

---

## 6. Où vit l'autorité

### 6.1 Arborescence cible

```text
scripts/ville/
  port-real-region.json                 invariants globaux et index des zones
  port-real-region-zones/
    00-eaux-et-relief.json              côte, Néra, marais, pentes
    10-port.json                         bassins, fronts, cales, usages nommés
    20-est-fer-rosby.json                porte de Fer, route et faubourg oriental
    30-nord-route-royale.json            cultures, vigne, relais, domaines
    40-ouest-rose-lion-dieux.json        grands faubourgs occidentaux
    50-sud-nera-gue.json                 prés bas, drainage, gué et moulins
  engendrer_region_port_real.py          parcelles, dessertes, toits, sillons
  assembler_region_port_real.py          fusion contrôlée des sorties de zones

monde/                                  dérivé, régénérable
  portreal.region/
    00-eaux-et-relief.json
    10-port.json
    ...
  portreal.region.json                  assemblage servi aux fours
```

Le découpage en fichiers de zone ne change pas l'autorité :
`port-real-region.json` garde la version, l'emprise, l'ordre des couches, les
graines et les références. Les fichiers de zone portent les décisions locales.

### 6.2 Ce qui est écrit à la main

| Toujours manuel | Pourquoi |
|---|---|
| côte, fleuve, chenaux principaux | leur topologie commande tout le reste |
| relief structurant et zones inondables | le générateur doit les subir |
| portes, grandes routes et franchissements | continuité historique et narrative |
| limites et usages nommés des zones | décision de monde, pas bruit visuel |
| bourgs, domaines, cimetières et marchés nommés | lieux adressables par le jeu |
| bassins, propriété du front d'eau, grands quais | histoire et fonction du port |
| monuments et bâtiments singuliers | identité, scène et persistance |
| budgets, exclusions et graine de chaque zone | résultat voulu et reproductibilité |

### 6.3 Ce qui est engendré

| Toujours procédural | À partir de quoi |
|---|---|
| subdivision en parcelles | limite de zone, pente, eau et accès |
| lanières, sillons et rangs d'arbres | forme et usage de la parcelle |
| dessertes secondaires | portes de parcelle vers le réseau existant |
| maisons ordinaires et dépendances | fronts de route, cours et densité locale |
| arbres individuels et haies | bois/limites déjà décidés |
| entrepôts ordinaires d'un lot portuaire | front, profondeur, usage et accès |
| petites variations de quai | unité riveraine manuelle et phase de reprise |

### 6.4 Ce qui est hybride

- **Faubourg** : axe, carrefours, places et domaines à la main ; parcelles,
  cours et bâti ordinaire engendrés.
- **Village** : site, rue principale, église/manoir et nombre de feux à la main ;
  toits et jardins engendrés.
- **Port** : côte, bassins, propriétés et usages à la main ; revêtements,
  bâtiments ordinaires et petites cales engendrés.
- **Champ ouvert** : contour et orientation à la main ; lanières et sillons
  engendrés.

La règle de partage est simple : **la main décide ce qui porte un nom, change
la topologie ou peut devenir une scène ; le générateur produit la répétition
matérielle à l'intérieur de cette décision.**

---

## 7. Les zones de travail

Les boîtes ci-dessous sont des boîtes de recherche ; les masques finaux seront
des polygones sans recouvrement. Les couches transversales — eau, routes et
relief — les traversent mais n'appartiennent qu'à `00-eaux-et-relief`.

### Z00 — Eaux, relief et grands axes

**Étendue : toute `emprise_detaillee`. Priorité absolue.**

Produit :

- repère canonique explicite : **x vers l'est, y vers le nord**, sans retourner
  les données géographiques ;
- projection nord-en-haut commune au SVG, aux canvas, aux clics, aux survols,
  aux captures et aux couches de simulation ;
- côte définitive, lit et plaine d'inondation de la Néra ;
- pentes et ruptures utiles au semis ;
- cinq routes et tous leurs franchissements ;
- emprises défensives autour de la courtine ;
- masque terre/eau commun au dessin et au déplacement.

Sortie : aucune maison. Cette tranche est finie lorsque la Néra est au sud,
Rosby au nord-est et que toute zone suivante
peut demander « terre, pente, humidité, distance à l'eau, distance à une route »
et recevoir une réponse stable. Le même point monde doit tomber sur le même
pixel dans le fond, les hommes, le feu et le pointeur.

### Z10 — Rive et port

**Boîte de travail : `[190,190,430,330]`.**

Contenu attendu :

- rive de la Gadoue, quais au grain, aux marchands, aux poissons et royal ;
- 12–20 unités riveraines inégales ;
- terre-pleins successifs, cales, grèves, pieux et bassins ;
- 100–250 entrepôts, ateliers et dépendances ;
- corderie, chantier, halage, poisson, sel et grain lisibles par leur forme ;
- une route continue derrière le front d'eau, reliée à la ville.

Pourquoi d'abord : c'est l'endroit où eau, sol, route, bâtiment, graphe et
masque doivent tous être justes. S'il passe, le contrat technique est prouvé.

### Z20 — Est, porte de Fer et route de Rosby

**Boîte de travail : `[350,-850,1150,250]`, hors Z10.**

Contenu attendu :

- faubourg de la porte de Fer, continu sur 500–900 m puis desserré ;
- auberges, écuries, marchands de charroi et jardins proches ;
- terres de Rosby plus régulières, domaines et fermes plus riches ;
- route principale, 5–9 chemins charretiers et dessertes de parcelles ;
- Rosby comme vrai bourg, non comme une étiquette entourée de 34 signes.

### Z30 — Nord et route royale

**Boîte de travail : `[-260,-1050,700,80]`.**

Contenu attendu :

- relais royal, marchés ou espaces d'assemblée et grandes écuries ;
- vergers, clos viticoles et cultures sur les pentes bien exposées ;
- un domaine religieux ou hospitalier avec jardins et cimetière ;
- moulins à vent si le relief et l'exposition les justifient ;
- bois de la route royale découpé en taillis, réserves et clairières exploitées.

### Z40 — Ouest, Rose, Lion et Dieux

**Boîte de travail : `[-1000,-150,130,300]`.**

Contenu attendu :

- les faubourgs les plus épais, parce que trois grands axes s'y rencontrent ;
- marché aux chevaux, auberges, maréchaux, parcs et prés de halte ;
- moulins de la Rose comme hameau productif ;
- vergers du Lion et grandes cultures plus loin ;
- carrefours et chemins de traverse reliant les routes entre elles sans passer
  par l'intérieur de la ville.

### Z50 — Sud-ouest, Néra et gué

**Boîte de travail : `[-1000,220,600,1050]`, hors Z10.**

Contenu attendu :

- prés bas, pâture, roseaux et terrains périodiquement noyés ;
- 3–6 fossés de drainage, levées, ponceaux et chemins saisonniers ;
- gué placé sur la bathymétrie, non au bout arbitraire d'une route ;
- biefs, moulins à eau, viviers et petites exploitations sur les terres sèches ;
- habitat rare dans le mouillé, dense seulement sur levées et carrefours.

---

## 8. Ordre de réalisation

Le travail ne se fait **ni entièrement par type**, car on obtiendrait pendant
des mois une carte de champs sans habitants, **ni entièrement zone par zone**,
car l'eau et les routes seraient redéfinies cinq fois. L'ordre est hybride :

1. les invariants transversaux une fois ;
2. une zone verticale complète à la fois ;
3. les générateurs réutilisables améliorés au passage, jamais avant leur
   premier besoin réel.

### Phase 0 — Outillage sans changement visuel

1. Unifier la projection nord-en-haut sans changer les coordonnées du monde.
2. Écrire un schéma validable de `port-real-region.json` et des fichiers de zone.
3. Créer `engendrer_region_port_real.py --zone <id>`.
4. Déplacer le `semis_regional()` actuel hors de `plan_ville.py` et reproduire
   exactement les 81 toits et 95 arbres : test de parité, pas amélioration.
5. Produire une sortie indépendante par zone et un assemblage déterministe.
6. Ajouter un rapport de cuisson : surfaces, formes, accès, erreurs et hash.

**Sortie de phase :** même image qu'avant, architecture nouvelle, hash stable.

### Phase 1 — Contrat physique régional

1. Fixer d'abord Z00 seul sur 30 × 28,8 km : côte, Néra, baie, grands massifs
   de relief et cinq routes, sans ajouter une maison.
2. Lire les mêmes polygones d'eau pour le dessin et l'obstacle ; le raster fin
   de la ville garde l'autorité dans le cœur, les polygones prennent le relais
   dans la couronne.
3. Étendre ensuite le masque sous forme de tuiles, au lieu d'un rectangle dense
   de 30 × 28,8 km chargé d'un bloc.
4. Rasteriser les bâtiments régionaux finaux dans les tuiles.
5. Introduire les dessertes régionales dans le graphe.
6. Tester dessin/masque/graphe sur l'actuelle poignée de bâtiments.

**Sortie de phase :** zéro toit régional visible mais franchissable.

### Phase 2 — Z10, le port comme tranche pilote

Réaliser la zone entière : côte, propriétés, terre-pleins, bassins, routes,
entrepôts, obstacles, noms et tests. Ne pas ouvrir une autre zone avant que le
port passe tous les seuils du § 10.

### Phase 3 — Z40, les grands faubourgs occidentaux

Le générateur apprend ici les rubans bâtis, cours, jardins, marchés, écuries et
transitions de densité. Cette phase remplace le vide le plus visible à gauche
de la ville.

### Phase 4 — Z50, les prés bas de la Néra

Le générateur apprend le drainage, les levées, les parcelles humides et les
moulins. Cette phase interdit définitivement les routes arbitraires dans l'eau.

### Phase 5 — Z20, Fer et Rosby

Le générateur réemploie les faubourgs mais produit une occupation plus riche,
des domaines plus réguliers et un véritable bourg de Rosby.

### Phase 6 — Z30, route royale et nord

Le générateur ajoute vigne, vergers, domaines, taillis et relief productif.

### Phase 7 — Assemblage et recul

1. Comparer les coutures entre zones.
2. Ajouter seulement les chemins nécessaires aux relations interzones.
3. Régler le cadrage initial et le dézoom complet.
4. Poser les noms qui ont survécu à la géographie, pas avant.
5. Faire la passe de cohérence avec la carte du royaume.

---

## 9. Un incrément de travail normal

Chaque incrément doit être assez petit pour être comparé avant/après, mais
assez vertical pour produire un morceau vrai.

Exemple : « les moulins de la Rose ».

1. **Décider à la main** le ruisseau ou le vent, le site, la route et le nombre
   de moulins.
2. **Engendrer** les parcelles, biefs secondaires, cours, dépendances et toits.
3. **Assembler** la seule zone Z40.
4. **Cuire** plan, graphe et masque.
5. **Mesurer** accès, collisions, eau, nombre de formes et coût de rendu.
6. **Comparer visuellement** trois cadrages : région, faubourg, bâtiment.
7. **Accepter ou corriger la source** ; ne jamais retoucher la sortie cuite.

CLI cible :

```powershell
python scripts/ville/engendrer_region_port_real.py --zone 40-ouest --rapport
python scripts/ville/assembler_region_port_real.py --zone 40-ouest
python scripts/monde/pipeline.py --lieu port-real --seulement plan --bavard
python scripts/ville/verifier_region_port_real.py --zone 40-ouest
```

`--zone` ne signifie pas « ignorer les invariants » : il lit Z00 et les sorties
validées voisines, puis n'écrit que sa propre sortie.

---

## 10. Critères d'acceptation

### 10.1 Pour chaque zone

Une zone n'est `faite` que si les huit lignes passent ensemble :

| Contrôle | Seuil |
|---|---|
| Schéma | zéro champ inconnu, zéro référence manquante |
| Déterminisme | même hash sur deux cuissons consécutives |
| Eau | zéro route terrestre dans l'eau hors ouvrage |
| Bâti / masque | zéro cellule de toit dessinée libre |
| Accès | 100 % des bâtiments solides ont une entrée reliée ou une exclusion expliquée |
| Couverture | au moins 90 % du sol reçoit un usage ; 97 % dans le premier km |
| Visuel | lisible aux trois cadrages, sans trait diagnostic dominant |
| Performance | pas plus de 20 % d'augmentation du temps de rendu par zone pilote |

Les budgets de formes du § 4 sont vérifiés en plus. Être dans la fourchette ne
suffit pas si les formes ne racontent rien ; en sortir exige une décision
écrite dans le rapport de zone.

### 10.2 Pour l'ensemble

- Les cinq grandes routes se prolongent sans rupture de la porte à leur
  destination régionale.
- Les faubourgs décroissent en densité au lieu de s'arrêter sur une ligne.
- Chaque chemin secondaire dessert une parcelle, un lieu ou un ouvrage.
- Le port modifie effectivement la rive et possède une arrière-zone bâtie.
- Les prés bas ont drainage et franchissements ; les coteaux ont un usage lié
  à leur exposition ; les bois ont accès et limites d'exploitation.
- À l'ouverture, Port-Réal reste le sujet principal ; au dézoom, elle devient
  le centre d'un système lisible.
- La vue `ville` et `/bataille` consomment la même géométrie et la même palette.

### 10.3 Budget de rendu

Les milliers de formes répétées sont regroupées en chemins par famille et par
zone. La cible est :

- moins de 30 éléments SVG supplémentaires au premier cadrage ;
- données régionales ajoutées au plan : moins de 1,2 Mo non compressé ;
- aucun élément DOM par arbre, sillon ou toit ordinaire ;
- chargement différé possible des tuiles hors `cadrage_initial`.

Si ces seuils ne tiennent pas, on simplifie la projection, jamais la géographie
source.

---

## 11. Ce qu'on ne fera pas

- Semer des lignes aléatoires pour suggérer des chemins.
- Ajouter des milliers de maisons purement visuelles.
- Dessiner des champs avec une mosaïque Voronoï sans histoire parcellaire.
- Faire varier la côte indépendamment du masque d'eau.
- Donner une adresse narrative à un bâtiment procédural ordinaire.
- Écrire à la main chaque toit, arbre, sillon ou entrepôt.
- Lancer la génération de toutes les zones avant d'avoir validé une tranche
  verticale complète.
- Corriger un défaut local par une exception dans le rendu.
- Étendre le masque actuel en un immense rectangle dense si des tuiles vides
  peuvent ne pas exister.

---

## 12. Première série de commits proposée

Chaque ligne doit pouvoir être relue et validée seule.

| Ordre | Commit | Changement visible |
|---:|---|---|
| 1 | `Projeter Port-Réal nord en haut` | Néra au sud, Rosby au nord-est |
| 2 | `Définir le schéma des zones périurbaines` | aucun |
| 3 | `Extraire le semis régional du four du plan` | aucun, parité exacte |
| 4 | `Cuire les obstacles régionaux par tuiles` | aucun, contrat physique |
| 5 | `Recomposer la rive et les propriétés du port` | côte et bassins |
| 6 | `Bâtir l'arrière-port et ses dessertes` | première zone complète |
| 7 | `Engendrer les faubourgs de la Rose et du Lion` | ouest densifié |
| 8 | `Drainer les prés bas de la Néra` | eau, moulins, chemins sur levée |
| 9 | `Bâtir la route de Fer jusqu'à Rosby` | est et bourg cohérents |
| 10 | `Cultiver la route royale` | nord, vergers, vigne et taillis |
| 11 | `Assembler la couronne de Port-Réal` | coutures, cadrages, noms |

Le commit 3 est le verrou. Avant lui, on peut améliorer eau, champs et routes ;
on ne doit pas multiplier les bâtiments solides.

---

## 13. Sources de comparaison

Ces sources justifient la structure générale, pas chaque nombre de notre cible.

- Jan Frolík et al., **« Empty space in Central European medieval towns »** :
  jardins périphériques, arrière de parcelles, vigne et espaces productifs
  intramuros.  
  <https://www.cambridge.org/core/journals/urban-history/article/empty-space-in-central-european-medieval-towns-through-an-interdisciplinary-perspective/BFE26C81EB0F5D3BE4E4519F96802C18>
- Tom Williamson, **« Beyond Urban Hinterlands »** : hinterlands de marché,
  formes dictées par relief et communications, influence urbaine sur les
  régimes agricoles.  
  <https://www.cambridge.org/core/journals/cambridge-archaeological-journal/article/beyond-urban-hinterlands-political-ecology-urban-metabolism-and-extended-urbanization-in-medieval-england/D95DFDE9C0DA61CD694ECE4D8BEDC5C9>
- Guy Fourquin, **Les campagnes de la région parisienne à la fin du Moyen Âge** :
  plaines céréalières, vignobles et bois exploités par la demande parisienne.  
  <https://www.persee.fr/doc/rural_0014-2182_1964_num_15_1_1146_t1_0092_0000_1>
- Historic England, **systèmes médiévaux de champs** : lanières, billons,
  sillons en S, tournières, prés et bois périphériques.  
  <https://historicengland.org.uk/listing/the-list/list-entry/1418427>
- Historic England, **Three Quays** : successions de revêtements de bois,
  propriétés et reprises du front d'eau du XIIe au XIVe siècle.  
  <https://historicengland.org.uk/listing/the-list/list-entry/1484184>
- Institut für Geschichte des ländlichen Raumes, **agriculture des deux côtés
  des murs de Constantinople** : production fraîche locale et logistique
  lointaine d'une mégapole.  
  <https://journals.univie.ac.at/index.php/rhy/article/view/5768>
- Institut de Cultura de Barcelona, **Rec Comtal** : canal, moulins, jardins
  irrigués, drainage et usages artisanaux.  
  <https://bcnroc.ajuntament.barcelona.cat/jspui/bitstream/11703/93849/1/19475.pdf>
- Institute of Historical Research, **Feeding the City** : agriculture
  commercialisée, grain et combustible du Londres médiéval.  
  <https://archives.history.ac.uk/ihrcms/projects/research/feeding-the-city2.html>

---

## 14. Décision de départ

La première action est la migration de projection nord-en-haut. Une fois ses
alignements validés, la prochaine action n'est pas de dessiner une nouvelle
parcelle mais de réaliser les deux chantiers d'outillage suivants :

1. schéma et fichiers de zones ;
2. extraction à rendu identique du semis actuel.

Ce travail donne une prise stable. Après lui, le port devient la première zone
à transformer réellement, parce qu'il oblige immédiatement le dessin, l'eau,
le sol, le graphe et le masque à dire la même chose.
