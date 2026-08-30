# Dragons réalistes — modèle de vol et de feu

> **Statut.** Ce document est un modèle d'ingénierie pour le banc d'épreuves de
> `/bataille`, pas une vérité canonique et pas un changement de l'état de la
> partie. Le canon ne donne ni masse, ni envergure, ni courbe de poussée de
> Syrax. Les nombres ci-dessous sont donc des hypothèses explicites et
> remplaçables.

## 1. Ce que la partie sait déjà

Le registre local donne une mesure de vol pour **Meleys** : 40 miles par heure
en aile posée, 60 en pressant pendant une heure au plus, et 1 000 pieds pour la
reconnaissance (`etat/books/affaire-voir-venir.json`, entrée 43022). Le même
registre précise que ces chiffres valent pour Meleys sous Rhaenys et qu'ils ne
doivent pas être transférés sans mesure à un autre couple dragon/cavalier.

Il ferme aussi l'emploi ordinaire de Syrax en reconnaissance. L'épreuve décrite
ici est donc un **banc mécanique hors récit** : elle emploie Syrax parce que
c'est la monture de Rhaenyra, mais n'envoie pas la reine en mission dans l'état
canonique.

Le canon publié décrit Syrax comme une dragonne adulte, montée par Rhaenyra
depuis l'enfance, sans dimensions numériques utilisables. Toute précision au
mètre ou à la tonne serait donc une invention si elle n'était pas étiquetée
comme telle.

## 2. Gabarit de travail de Syrax

| Grandeur | Valeur nominale | Plage à tester | Pourquoi |
|---|---:|---:|---|
| longueur totale | 28 m | 24–32 m | adulte imposante, mais pas de la classe de Vhagar |
| envergure | 36 m | 32–40 m | ailes larges nécessaires au vol lent et au portage |
| surface alaire effective | 360 m² | 300–430 m² | aile membraneuse large, faible allongement |
| masse en vol | 8,0 t | 6–10 t | squelette pneumatisé et corps moins dense qu'un reptile terrestre |
| Rhaenyra + selle | 105 kg | 90–125 kg | 1,3 % de la masse nominale : faible, mais pas nul pour le centrage |
| charge alaire | 218 N/m² | 170–330 N/m² | `m g / S` |
| allongement | 3,6 | 3–5 | `b² / S`, ailes larges plutôt que planeur fin |

Cette masse place Syrax très au-delà des animaux volants connus. Les travaux sur
les ptérosaures géants montrent justement que le lancement et la puissance
disponible deviennent les contraintes dominantes à grande taille. Un dragon de
huit tonnes exige donc au moins une anatomie extraordinairement pneumatisée, des
tissus très supérieurs aux muscles connus et une source d'énergie fictive. Le
modèle cherche une dynamique cohérente **après l'envol** ; il ne prétend pas
rendre cette biologie possible.

Avec `ρ = 1,225 kg/m³` et `C_Lmax = 2,0`, la vitesse de décrochage vaut :

```text
V_décrochage = sqrt(2 m g / (ρ S C_Lmax)) ≈ 13,3 m/s ≈ 48 km/h
```

On retient donc :

- croisière calme : **18 m/s** (65 km/h, proche des 40 mph mesurés sur Meleys) ;
- reconnaissance : **18–22 m/s** ;
- vol battu d’attente : **3,2–6 m/s**, pendant moins de dix secondes ;
- vol pressé : **27 m/s** (97 km/h) pendant une durée limitée ;
- piqué : plafond nominal **55 m/s** (198 km/h), imposé par la traînée et non
  par un plafond arbitraire de l'interface.

Les mesures radar sur 138 espèces d'oiseaux trouvent des vitesses équivalentes
de 8 à 23 m/s et confirment que la charge alaire compte davantage que la seule
masse. Syrax se place volontairement au bord supérieur de ce domaine en
croisière, puis sort du domaine biologique connu en vol pressé.

La vitesse de décrochage vaut pour une aile qui demande à sa translation de
porter le poids. Elle n’interdit pas un régime propulsé quasi stationnaire :
Syrax redresse le corps, accélère ses battements jusqu’à **0,42 Hz** et dévie
une masse d’air vers le bas. Avec une aire battue effective de 600 m², la
théorie idéale du disque actuateur donne une vitesse induite proche de 7,3 m/s
et une puissance minimale d’environ 0,57 MW. La dépense réelle serait nettement
supérieure ; ce régime reste donc bref et sert à établir un cap, pas à attendre
indéfiniment au-dessus du champ de bataille.

### 2.1 Profils comparatifs de 129 AC

Le banc ne prétend pas connaître des dimensions que le canon ne donne pas. Il
utilise en revanche deux relations publiées pour choisir les extrêmes : Vhagar
est le plus grand dragon vivant en 129 AC et mesure près du gabarit de Balerion ;
Arrax est déjà monté par Lucerys et Vhagar est décrite comme cinq fois plus
grande que lui. Moondancer n'est pas retenue comme « plus petit dragon en état
de combattre » : en 129 AC elle n'est pas encore jugée assez grande pour porter
Baela. Les valeurs suivantes sont donc des **profils d'ingénierie**, ajustables,
et non des mensurations canoniques.

| profil | masse | longueur | envergure | surface alaire | charge alaire | jet / souffle |
|---|---:|---:|---:|---:|---:|---:|
| Syrax, contrôle D2 | 8,0 t | 28 m | 36 m | 360 m² | 218 N/m² | 65 m / 2,55 s |
| Vhagar, D2b | 42 t | 67 m | 82 m | 1 800 m² | 229 N/m² | 115 m / 3,4 s |
| Arrax, D2c | 2,2 t | 15 m | 22 m | 125 m² | 173 N/m² | 38 m / 1,7 s |

L'aire alaire croît presque comme le carré de la longueur afin de ne pas faire
exploser artificiellement la charge alaire de Vhagar. La masse croît moins vite
que le cube d'un reptile plein : les trois profils supposent le même allègement
pneumatique fictif. Les conséquences dynamiques sont appliquées partout :

- Vhagar bat lentement (**0,12 Hz** en croisière), accélère latéralement deux
  fois moins que Syrax, établit son passage sur 500 m et ne tient à faible allure
  que brièvement, à 6–8 m/s ;
- Arrax bat vite (**0,48 Hz**), accepte une forte banque, freine et reprend son
  cap rapidement, mais doit tirer plus bas et ne lit qu'un couloir court ;
- le poids affiché et le pic de force au battement sont recalculés à partir de
  la masse de chaque profil, au lieu de conserver les 78,5 kN de Syrax ;
- portée, ouverture, pente, température centrale, flux thermique et durée du
  souffle alimentent la même intersection géométrique 3D avec le sol.

Ce choix rend l'expérience falsifiable : si Vhagar ne montre qu'une silhouette
agrandie, ou si Arrax conserve la même trajectoire et la même empreinte que
Syrax, le profil n'est pas correctement propagé dans le moteur.

## 3. Battement, force et continuité de la vitesse

### Fréquence

Pour un vol efficace, les oiseaux et animaux nageurs se placent souvent dans
une bande de Strouhal `St = f A / U` voisine de 0,2–0,4. Avec une vitesse
`U = 18 m/s`, une excursion verticale d'extrémité d'aile `A ≈ 18 m` et
`St = 0,24` :

```text
f = St U / A ≈ 0,24 Hz
période ≈ 4,2 s
```

Le banc emploie donc **0,24 Hz en croisière**, jusqu'à **0,35 Hz** pendant une
relance ou une sortie d'attaque. La relation allométrique classique
`f ∝ m^-1/6` et les modèles plus récents fondés sur `sqrt(m) / surface d'aile`
vont dans le même sens : une très grande bête bat lentement.

### Forces

Le poids nominal est `W = m g = 78,5 kN`. En palier, la portance moyenne sur un
cycle reste égale à ce poids. Le battement déplace cependant la force entre
portance et poussée :

| Régime | force aérodynamique moyenne | pic au coup d'aile | poussée horizontale utile |
|---|---:|---:|---:|
| croisière | 78–85 kN | 105–120 kN | 8–14 kN en moyenne |
| relance | 85–100 kN | 130–150 kN | 30–60 kN au coup d'aile |
| montée | 95–115 kN | 150–175 kN | composante surtout verticale |

À 18 m/s, avec une finesse de l'ordre de 7, la traînée est voisine de 11 kN et
la puissance mécanique minimale de `D × V ≈ 200 kW`. Avec les pertes induites,
le profil des ailes et les accélérations du battement, le budget de croisière
du modèle est **0,3–0,5 MW mécaniques**. Un passage pressé peut dépasser 1 MW.

### Pas d'à-coups de translation

La force bat ; la masse du dragon filtre. Il serait faux de faire gagner cinq
mètres par seconde instantanément à chaque coup d'aile. En vol établi :

- la vitesse air oscille de **±3 à 5 %** autour de sa moyenne ;
- le centre de masse monte et descend de **0,5 à 1,5 m** ;
- l'assiette et l'ouverture des ailes rendent le battement visible avant que la
  trajectoire ne le devienne ;
- une demande de vitesse traverse un filtre de 2 à 4 secondes, puis la traînée
  limite la relance.

L'animation peut donc accentuer l'ouverture des ailes et l'ombre, mais ne doit
pas déplacer le dragon en dents de scie.

## 4. Altitude, piqué et vitesse au sol

L'état cinématique minimal est :

```text
[x, y, z, vitesse_air, cap, inclinaison, pente, phase_aile]
```

Le vent est un vecteur séparé. La vitesse au sol est la projection horizontale
de la vitesse air plus le vent :

```text
V_sol = |V_air cos(γ) · direction_cap + V_vent|
```

Quand Syrax perd une hauteur `Δh`, une fraction `η` de l'énergie potentielle
devient vitesse et le reste devient traînée, turbulence et déformation :

```text
V_air² = min(V_limite², V_entrée² + 2 g η Δh)
η = 0,45 au piqué nominal
V_limite = 55 m/s
```

Ainsi, une entrée à 18 m/s suivie d'une perte de 300 m donne 54,5 m/s avant le
plafond de traînée. Une ressource reconvertit ensuite cette vitesse en altitude ;
elle ne remet pas instantanément Syrax à sa vitesse de croisière.

Le rayon d'un virage coordonné fournit un garde-fou de voilure fixe :

```text
R = V² / (g tan φ)
```

À 18 m/s et 35° d'inclinaison, ce minimum vaut 47 m. Mais Syrax n'est pas une
fusée, ni même un avion : battement dissymétrique, torsion du corps et queue
ajoutent une accélération latérale bornée. Le modèle emploie donc :

```text
ω = (g tan φ + a_battement) / V
|a_battement| ≤ 6,5 m/s²
```

À 25 m/s et 60° dans une manœuvre d'attaque, le rayon limite descend ainsi vers
27 m sans autoriser un pivot sur place **à cette vitesse**. Lorsque Syrax arrive
près du point d’entrée sans avoir encore le bon cap, elle change de régime :
freinage jusqu’à 3,2–6 m/s, banque sous 10°, portance produite par les battements
et lacet du corps presque sur place. Cette tenue est plafonnée à neuf secondes ;
si la fenêtre ne s’ouvre pas, elle reprend de l’allure vers une autre entrée au
lieu de dessiner des petits cercles. L'orbite de reconnaissance reste bien
plus large — **150 à 230 m de rayon** — parce qu'elle privilégie la stabilité,
la vue de la cavalière et une banque modérée.

## 5. Construire des paths 3D qui restent courbes

Le path n'est pas une ligne 2D à laquelle on ajoute une hauteur après coup. La
simulation produit des états 3D par guidage, puis le rendu relie les échantillons
par des cubiques de Hermite (convertibles en Bézier). Chaque segment conserve
ainsi la tangente d'entrée, la tangente de sortie et l'altitude.

Règles communes :

1. limiter l'inclinaison, y ajouter l'accélération latérale bornée du battement,
   puis en déduire la vitesse de rotation ;
2. viser un **point futur** de la cible, pas sa position passée ;
3. filtrer les consignes d'altitude et de vitesse ;
4. interdire aux splines de dépasser `z = 0` — Catmull-Rom sans garde peut
   traverser le sol entre deux points pourtant valides ;
5. enregistrer `[x,y,z]` dans la trace afin que la couleur de la ligne puisse
   montrer l'altitude réellement calculée.

### Scénario A — reconnaissance d'une colonne mobile

- cible prédite 6 à 10 secondes en avant ;
- centre d'orbite qui glisse vers cette cible prédite ;
- rayon `R_orbite = clamp(135 + 0,10 z, 150, 230) m` ;
- altitude nominale 300 m (environ 1 000 pieds) ;
- tangente d'orbite prioritaire, correction radiale secondaire ;
- une boucle complète dure environ 55 à 70 secondes selon le rayon.

Le résultat est une boucle vivante : si la colonne avance, l'orbite n'est pas
un cercle fixé au décor, mais une courbe légèrement étirée qui la suit.

### Scénario B — Dracarys en passage oblique

Trois portes pilotent la courbe, sans téléportation :

1. **entrée**, 220–260 m d'altitude, 18–22 m/s ;
2. **mise en piqué**, vers un point prédit devant la tête de colonne ;
3. **tir**, 35–50 m au-dessus du sol, 35–45 m/s ;
4. **sortie**, virage de 30–40° puis ressource progressive.

Le feu dure 2 à 3 secondes. Le point visé continue d'avancer pendant ce temps,
ce qui courbe légèrement la trace au sol. Une attaque parfaitement rectiligne
sur une cible mobile paraîtrait mécanique et ferait porter tout le mouvement à
la colonne.

### Scénarios suivants

- vent de travers : orbite décentrée et vitesse au sol différente selon le
  côté de la boucle ;
- attaque parallèle à une colonne : longue trace, exposition accrue aux tirs ;
- attaque perpendiculaire : trace courte, moins d'hommes touchés, sortie plus
  sûre ;
- cible dispersée : Syrax doit choisir une concentration et ne peut pas
  « peindre » tout le terrain ;
- ressource interrompue : vérifier qu'une consigne impossible produit un large
  virage bas plutôt qu'un demi-tour instantané.

## 6. Forme et température du feu

Le souffle est modélisé comme un jet turbulent combustible, pas comme un
cylindre ni comme une succession de boules. Valeurs nominales :

| Grandeur | Valeur |
|---|---:|
| durée continue | 2,5 s |
| longueur visible maximale | 55 m (45–65 m selon régime) |
| rayon à la gueule | 0,8 m |
| rayon à 55 m | 6,3 m |
| température du noyau | 1 950–2 050 K |
| puissance chimique indicative | 70–130 MW |
| combustible fictif équivalent | 1,5–3 kg/s à 45 MJ/kg |

Les températures adiabatiques calculées pour des flammes méthane-air passent
d'environ 1 555 K à 2 012 K quand le mélange s'approche de la stœchiométrie. Le
noyau nominal à 2 000 K est donc un ordre de grandeur de flamme, pas celui d'un
plasma. Le combustible et l'oxydant de Syrax restent fictifs.

Avec `s` la distance à la gueule, `r` la distance à l'axe, `L` la longueur du
jet et `T_a` la température ambiante :

```text
R(s) = 0,8 + 0,10 s

T_c(s) = T_a + (T_0 - T_a)
         · exp[-max(0, s - 0,25 L) / (0,65 L)]

T(s,r,t) = T_a + [T_c(s) - T_a]
           · max(0, 1 - (r / R(s))²)^0,35
           · B(t)
```

`B(t)` est une enveloppe lissée : montée en 0,25 s, plateau, extinction en
0,35 s. La longueur visible peut pulser de 8 à 12 % avec la pression du souffle,
mais le jet reste continu.

Rendu conseillé :

- blanc-jaune : plus de 1 700 K, petit noyau ;
- jaune-orange : 1 200–1 700 K ;
- rouge sombre et fumée : 700–1 200 K ;
- sous 700 K : chaleur résiduelle au sol, pas une flamme opaque.

## 7. Impact, splatter et trace thermique

Le cône 3D est intersecté avec le plan `z = 0`. Tant que sa longueur n'atteint
pas le sol, aucune marque n'est déposée. Le calcul ne projette pas un triangle
2D : il coupe chaque disque perpendiculaire à l'axe du jet. Pour une section à
la distance `s`, de rayon `R(s)`, dont le centre est à la hauteur `z_c`, et un
axe incliné de `θ` vers le sol :

```text
v = -z_c / cos(θ)

si |v| > R(s) : la section ne touche pas le sol
sinon : demi-largeur au sol = sqrt(R(s)² - v²)
```

L'union de ces cordes donne exactement la larme allongée visible. La
température de chaque cellule emploie alors la vraie distance 3D à l'axe
`r = sqrt(u² + v²)`, et non sa seule distance latérale au path. Des gouttes
secondaires sont projetées depuis le bord et l'extrémité : c'est le
**splatter**. Elles sont visuelles et n'ajoutent aucune dose hors du cône.

Chaque cellule de sol accumule une dose :

```text
dose += max(0, (T - 550 K) / 1 450 K)² · dt
```

Après le passage, la température visuelle décroît sur deux constantes de temps :

```text
T_sol(t) = T_a + (T_pic - T_a)
           · [0,72 exp(-t/12 s) + 0,28 exp(-t/90 s)]
```

La braise disparaît ; la carbonisation reste. La trace visible encode donc à
la fois le présent (orange = encore chaud) et l'histoire (noir = dose reçue).
Les corps sont de vrais soldats de `Bataille2d`. La dose thermique devient une
perte de PV dans le système commun ; une chute passe par la fonction ordinaire
de blessure et avertit les voisins. Le splatter reste seulement visuel et ne
crée jamais de dégât hors de l'intersection calculée.

## 8. Paramètres du premier banc

Le banc `/bataille` expose une épreuve intégrée, sans ville, en deux temps :

- **D1 — Reconnaissance** : Syrax et sa cavalière suivent une colonne mobile
  sur une boucle dynamique ; altitude, vitesse air, vitesse sol, inclinaison,
  force de battement et trace 3D sont visibles ;
- **D2 — Syrax contre armée** : attaque immédiate de six masses, sans boucle de
  reconnaissance, puis ralliement, piqué, jet conique et nouvelle cible ;
- **D2b — Vhagar contre la même armée** : même placement, mêmes soldats, même
  fuite et même décision tactique, avec le profil lourd et le feu élargi ;
- **D2c — Arrax contre la même armée** : mêmes conditions encore, avec davantage
  de maniabilité mais un couloir et une empreinte nettement plus petits.

Dans les quatre cas, la boucle ne se termine pas : les attaques se succèdent
tant que la simulation avance.

Il n'existe aucun replacement entre ces états. Position, cap, vitesse et
vitesse verticale restent continus ; le plus grand pas réellement tracé est
affiché dans les sondes afin qu'une téléportation ne puisse pas se cacher dans
une jolie courbe.

### Même visualisation que le banc de bataille

Le terrain et les soldats sont dessinés par `Bataille2d` lui-même : mêmes corps,
mêmes états colorés, même hit-test et mêmes fiches au survol que les autres
épreuves. La couche dragon est une surimpression transparente limitée à ce que
le moteur 2D ne porte pas — altitude, path, chaleur, flamme et silhouette. Son
repère local est transformé dans les coordonnées monde avant dessin ; il ne
possède donc ni seconde scène ni seconde caméra. La page applique le même
`vue = [x, y, largeur, hauteur]`, le même zoom vers le pointeur et le même glissé.
« Retrouver la scène » recalcule la boîte englobante du dragon, des combattants,
du path et des zones déjà traitées ; il ne remet ni le temps ni la simulation à
zéro.

La côte obéit au même contrat. Sa courbe visible et l’interdiction mécanique de
l’eau viennent toutes deux de `terrain.eau`, au seuil 0,5. `Bataille2d.libre()`
ne répond vrai qu’après avoir chargé à la fois le masque du bâti et celui de
l’eau : un homme en armure ne peut donc ni être posé dans l’eau, ni la choisir
comme direction de fuite. D1 et D2 refusent en outre leur mise en place si un
seul combattant tombe hors du sol sec.

### Choisir une cible, puis la suivante

L'objectif « tout brûler » ne se formule pas comme « prendre l'homme le plus
proche ». Un dragon et sa cavalière lisent des **masses** et construisent un
passage qui engage leur inertie pour plusieurs dizaines de secondes. Le banc
évalue donc, autour d'ancres humaines espacées, plusieurs orientations reliant
les masses visibles. Le couloir prévisionnel dépend du profil : **178 m** pour
Syrax, **273 m** pour Vhagar et **124 m** pour Arrax. Sa largeur évolue
respectivement de 12 à 18 m, 20 à 34 m et 8 à 12 m. Il représente la distance
parcourue pendant le souffle plus la portée utile devant le dragon. Ce couloir
sert uniquement à la décision ; l'empreinte et les dégâts restent calculés
ensuite par `intersectionConeSol()`.

La valeur d'un couloir additionne les combattants encore debout en donnant
moins de poids à ceux qui ont déjà reçu une forte dose. Elle est ensuite
réduite par deux coûts : l'angle que le dragon doit reprendre et la proximité
excessive qui ne laisse pas assez de place pour établir le piqué. Une zone déjà
traitée reçoit enfin une forte décote. Cela produit la priorité suivante :

1. beaucoup de corps encore rentables dans la future empreinte ;
2. plusieurs masses séparées mais alignées dans le même passage ;
3. une approche que le dragon peut réellement construire depuis son cap ;
4. une zone fraîche avant le reliquat d'une zone déjà parcourue.

Le verrou est temporel : la cible choisie reste celle du ralliement, du piqué,
du souffle et de la sortie. La zone est inscrite comme traitée quand le souffle
se coupe, mais la prochaine cible n'est élue qu'une fois la ressource achevée.
Un groupe qui se disperse peut déplacer le point suivi ; il ne peut pas faire
sauter le choix vers une autre masse au milieu du passage. Lorsque toutes les
zones fraîches ont été parcourues, les survivants peu exposés des anciennes
zones redeviennent les meilleurs candidats : « tout brûler » n'est donc ni un
tour unique ni une liste scriptée.

Le choix stratégique ne commande pas l'instant exact du feu. Une fois sous son
altitude de tir — 34 m pour Syrax, 58 m pour Vhagar, 28 m pour Arrax — le dragon
relit la bande réellement située devant son cap. Si une petite masse rentable
entre dans sa portée opportuniste propre, il souffle immédiatement : l'occasion
remplace la condition fragile « être exactement au barycentre ». La banque
pendant le souffle est elle aussi propre au profil ; elle permet une correction
de quelques mètres vers l'étape suivante, pas un lacet irréalisable. D2, D2b et
D2c commencent directement par cette construction d'attaque, sans boucle de
reconnaissance préalable.

### D3 — « tout brûler » sur une ville

D3 conserve exactement la cinématique de Vhagar de D2b, mais remplace les
soldats par des secteurs de cinquante mètres agrégés depuis les contours bâtis
encore combustibles. Leur valeur combine surface, charge combustible et état
du feu. Soixante-quatre ancres spatialement distinctes et douze caps candidats
permettent de comparer des bandes de `273 m` sans confondre des dizaines de
milliers de contours proches avec autant de décisions de vol.

Une bande stratégique ne déclenche pas le feu. Vhagar doit encore la rejoindre
par sa courbe continue, piquer sous `58 m`, puis trouver devant son cap une
occasion comprise dans sa portée de `245 m` et sa demi-largeur de `11 m`.
Après le souffle, les secteurs attaqués sont décotés et le cadastre courant est
relu : les toits déjà brûlés disparaissent de la valeur, les prises ne valent
plus qu’un tiers et les embrasements un dixième. Le passage suivant est donc
choisi depuis la position, le cap et l’altitude réellement atteints, jamais par
replacement ni par liste de waypoints.

### Rupture de la colonne

Dans D1, le survol ne force pas `etat = deroute` dans le banc dragon. Il fournit au
système de fuite commun trois observations d'unité : part des hommes qui voient
la menace, capacité de riposte perçue, fermeture de la trajectoire autour
d'eux. `Bataille2d.jugerRuptureUnite()` conserve ce jugement, fait céder
l'arrière d'abord, puis fait passer chaque départ par l'unique `rompre()` du
moteur. La contagion, la pensée et la course restent donc celles des soldats.
Dans D2, la boucle de repérage est supprimée, pas la peur : l'alignement direct
fait croître la fermeture perçue et alimente le même jugement collectif. Une
armée sans riposte contre un dragon ennemi rompt donc normalement avant le
premier feu ; l'approche, le rugissement et la flamme continuent en parallèle à
passer par les entrées sensorielles communes. Aucun délai de courage n'est
ajouté pour faciliter le tir du dragon.

Au moment précis où il rompt, chaque combattant compare la puissance qu'il
croit encore avoir autour de lui à celle qui l'écrase. Une graine dérivée de
son identité stable transforme cette sévérité en l'une de deux conduites :

- **regroupement** : il cherche une masse amie encore debout, recalcule sa
  trajectoire vers elle et reste immédiatement accessible au ralliement ;
- **dispersion** : il conclut que personne ne peut le protéger, prend un cap
  personnel loin du danger et ne le corrige que lentement. Plus la défaite lui
  paraît absolue, plus l'inertie qui retarde un éventuel ralliement est longue.

Les angles et les décalages de cible sont pseudo-aléatoires mais propres à
chaque `debugId` : deux hommes ne fuient plus sur le même rayon, tandis qu'un
rejeu identique produit exactement les mêmes choix et les mêmes directions.

La forme du mécanisme vient de
[`le-repli-la-fuite-et-la-couardise.md`](../recherche/le-repli-la-fuite-et-la-couardise.md) :
la rupture est un fait d'unité et un jugement qui précède généralement les
pertes. Les bornes numériques qui convertissent ce jugement en progression de
la cascade restent une hypothèse du banc, explicitement non sourcée.

Ce qu'il faut regarder avant d'ajouter des règles de mortalité :

1. la vitesse ne saute pas à chaque battement ;
2. le rayon du virage grandit avec la vitesse ;
3. le piqué transforme bien la hauteur perdue en vitesse ;
4. le feu n'atteint le sol que lorsque la géométrie le permet ;
5. la trace reste après la disparition de la flamme ;
6. l'orbite suit la colonne au lieu de tourner autour d'un point mort.
7. la colonne rompt globalement avant la première flamme ;
8. au moins deux passages de feu sont produits sans aucun saut du path.

## Sources techniques

- Alerstam et al., [Flight Speeds among Bird Species: Allometric and
  Phylogenetic Effects](https://pmc.ncbi.nlm.nih.gov/articles/PMC1914071/),
  *PLOS Biology*, 2007 — vitesses mesurées et charge alaire.
- Pennycuick, [Wingbeat frequency of birds in steady cruising flight: new data
  and improved predictions](https://pubmed.ncbi.nlm.nih.gov/9319516/),
  *Journal of Experimental Biology*, 1996 — fréquence et allométrie.
- Nudds, Taylor & Thomas, [Tuning of Strouhal number for high propulsive
  efficiency accurately predicts how wingbeat frequency and stroke amplitude
  relate and scale with size and flight speed in birds](https://pmc.ncbi.nlm.nih.gov/articles/PMC1691825/),
  *Proceedings of the Royal Society B*, 2004 — bande de Strouhal et fréquence.
- Gazzola et al., [Universal wing- and fin-beat frequency scaling](https://pmc.ncbi.nlm.nih.gov/articles/PMC11152310/),
  *Nature*, 2024 — relation masse, surface et fréquence.
- Witton & Habib, [On the Size and Flight Diversity of Giant Pterosaurs, the
  Use of Birds as Pterosaur Analogues and Comments on Pterosaur Flightlessness](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0013982),
  *PLOS ONE*, 2010 — contraintes de lancement et limites des analogies aviaires.
- NASA, [Presumed PDF Modeling of Early Flame Propagation](https://ntrs.nasa.gov/api/citations/20050198897/downloads/20050198897.pdf?attachment=true),
  2005 — températures adiabatiques méthane-air selon la richesse du mélange.
- NIST, [Evaluation of Models for Predicting Flame Lengths and Flame Heights](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir5904.pdf),
  NISTIR 5904 — longueur visible des jets turbulents et rôle de la suie.
