# La porte de la Gadoue — distribution

Le décor humain du sac. Ce fichier ne décrit ni le format ni le four : il dit
**qui est là, ce qu'il veut, et combien d'hommes il tient**. Tout le reste vit
dans `scripts/monde/sac.js` et `ecrans/modules/bataille2d.js`.

---

## Le cadre — 130 AC, la Lune des Trois Rois

**Deux ans après l'ouverture des Sept Chandelles.** Rhaenyra a fui Port-Réal,
les Hightower ne sont pas encore rentrés, et la ville n'a plus de roi — donc
elle en a trois. C'est le seul moment de la Danse où un chef de rue peut lever
neuf mille hommes dans Port-Réal et marcher sur le Donjon Rouge sans que rien
ne l'en empêche : il n'y a personne au-dessus.

**Pourquoi celui-là et pas un autre.** La géométrie était déjà écrite : le sac
part de **la porte de la Gadoue** et vise **le Donjon Rouge**. C'est l'axe du
port vers la colline d'Aegon — l'axe des émeutes, jamais celui d'une armée
étrangère. Une armée qui vient de dehors n'entre pas par là ; une armée qui
naît dedans n'entre que par là. Le camp d'en face était donc décidé par le
plan avant qu'on en parle.

Si tu veux l'autre cadre — **une armée régulière qui débarque du Néra**, avec
chaîne de commandement, machines et bannières —, la distribution ci-dessous se
transpose : on garde les six corps, on remplace les meneurs de rue par des
chevaliers bannerets, et on gagne la discipline qu'on perd ici. Dis-le et je la
réécris.

**Ce qui est canon et ne doit pas bouger** : la Lune des Trois Rois, Ser Perkin
la Puce, Trystane Feufidèle, le Berger. Tout ce qui est nommé plus bas est de
l'invention posée dessous — c'est-à-dire de l'arrière-plan déjà vrai, comme le
reste du dépôt.

> *Écho, et il est volontaire :* la troupe rivale des Sept Chandelles s'appelle
> **les Trois Rois**. En 128 c'est un nom de mimes. En 130 c'est l'état de la
> ville. Personne ne le fait remarquer.

---

---

## V1 — trois gestes, et rien d'autre

Tout ce fichier décrit une chose qui se manipule par **une seule porte** :
`scripts/bataille.py`.

```bash
python scripts/bataille.py
```

Dit où l'on en est : quel sac est cuit, ce qu'il contient, et si elle a lieu.

**1. Cuire.** Ça produit `monde/portreal.sac.*` — les itinéraires, les
annales, la nappe. C'est du monde engendré : régénérable, bête, et **ça ne
concerne encore personne**.

```bash
python scripts/bataille.py --cuire --hommes 9500 --duree 600
```

**2. Dater.** C'est le geste qui la fait exister dans la partie. Il écrit
`etat/bataille.json`, et il est réversible.

```bash
python scripts/bataille.py --dater 3 1200
```

**3. Jouer.** Il n'y a rien à faire. Dès qu'un siège marche dans la ville, le
serveur demande à `croiser.js` ce que ce pas-là perçoit, et le dépose dans le
sac de balade — vu, entendu, ou trouvé par terre. Le MJ le lit avec le reste.

```bash
python scripts/bataille.py --recit        # ce qui s'y est passé, en clair
python scripts/bataille.py --eteindre     # elle n'a plus lieu
```

**La séparation est le point.** Le sac est un fait du monde ; sa date est une
décision de jeu. On peut donc cuire pendant une séance sans rien changer à la
séance, en refaire dix, et décider après coup si — et quand — ça a eu lieu.
Tant que `etat/bataille.json` n'existe pas, tout ce mécanisme coûte un `if`.

---

## La règle qui commande toute cette liste

À neuf mille cinq cents hommes en escouades de vingt, **il y a quatre cent
soixante-quinze escouades**. Le module sait déjà écrire `chef-tombe` par
escouade — soit quatre cent soixante-quinze lignes d'annales que personne ne
lira jamais.

**Le nom est donc la seule unité de lisibilité du sac.** Trois étages, et pas
un de plus :

| Étage | Combien | Ce que les annales en font |
|---|---|---|
| **Les corps** | 6 nommés | tout : leur avance, leur arrêt, leur rupture, leur mort |
| **Les meneurs** | 24 nommés | leur chute est un fait ; leur escouade est une phrase |
| **Le reste** | 9 470 | des chiffres, jamais des lignes |

Corollaire pour le four : `chef-tombe` ne doit se déclencher **que sur un chef
nommé**. Un chef d'escouade anonyme qui tombe est un mort de plus, rien
d'autre. C'est une ligne à changer, et c'est la différence entre un document et
un journal de débogage.

---

# LE CAMP D'EN FACE — la Rue

**Neuf mille cinq cents. Aucune chaîne de commandement.** Ce n'est pas une
armée : ce sont six foules qui vont dans la même direction pour six raisons
différentes, et deux d'entre elles n'obéissent à personne. C'est exactement ce
que le module sait simuler et qu'une armée régulière lui interdirait.

## Le roi — Trystane Feufidèle

**Seize ans. Écuyer. Bâtard de Viserys, à ce qu'on dit, et il ne le dit pas
lui-même.** Couronné sur la place aux Poissons il y a onze jours, avec une
couronne de fer-blanc que Perkin a fait faire chez un ferblantier de la Gadoue.

- **Il veut qu'on le croie.** Pas régner — être cru. Il n'a jamais eu autre
  chose que sa mère pour le croire, et elle est morte.
- **Il craint de se retrouver seul dans une pièce avec Perkin**, parce qu'alors
  il n'y a plus de foule pour tenir le mensonge debout, et ils le savent tous
  les deux.
- **Manière** : il parle par phrases qu'on lui a apprises, et elles ne tiennent
  pas dans sa bouche. Trois mots trop hauts, puis un mot d'enfant. Quand il
  improvise, il est bon — et c'est ce qui terrifie Perkin.
- **Dans le sac** : il n'est **pas** à la porte. Il est porté à trois cents pas
  en arrière, sur une charrette, avec quarante hommes autour. Il ne se bat
  jamais. **S'il meurt, tout s'arrête** — c'est la seule condition de fin qui ne
  passe pas par le verrou.

## Ser Perkin la Puce — le centre, 2 400 hommes

**Chevalier errant, la cinquantaine, jamais eu un pouce de terre.** Il a
adoubé deux cents hommes du ruisseau en trois jours, sur la place, avec la même
épée, et pas un ne lui a demandé de quel droit.

- **Il veut être Main du Roi.** Pas riche : *nommé*. Trente ans qu'on lui dit
  monsieur en oubliant le ser.
- **Il craint le jour où la foule s'apercevra qu'il ne lui a rien donné.** Il
  compte en jours, et il en est à onze.
- **Manière** : doux, raisonnable, appelle tout le monde « mon bon ». Il ne
  hausse jamais la voix — ce qui, au milieu d'une émeute, s'entend de plus loin
  que les cris.
- **Dans le sac** : le corps du centre, celui qui frappe la porte. Il est
  **derrière**, au troisième rang, et c'est un fait de caractère : il n'a
  jamais été au premier rang de rien.

## Ser Wat Crochet — le port, 1 800 hommes

**Débardeur, trente-neuf ans, adoubé il y a neuf jours.** Une main en moins
depuis un cordage, remplacée par ce qui lui vaut son nom.

- **Il veut la porte de la Gadoue elle-même** — le péage, les registres, ce
  qu'on prend sur chaque tonneau qui entre. Il sait exactement combien ça fait
  par jour ; il l'a vu passer vingt ans.
- **Il craint Perkin**, et il a raison.
- **Manière** : chiffré, court, jure par métier. Il donne les distances en
  brasses et le temps en marées, ce que personne d'autre ne comprend.
- **Dans le sac** : il arrive **par les quais**, donc en flanc, donc en retard.
  Son corps est le seul qui ait des outils : masses, coins, cordages. Contre le
  verrou, ses hommes valent double.

## Ser Ronnel Sans-Maison — l'aile ferme, 900 hommes

**Trente-quatre ans. Le seul vrai chevalier de toute cette armée**, et le seul
qui ait honte d'y être. Sa maison l'a renié il y a six ans pour une affaire
dont il ne parle pas et qui n'est pas celle qu'on raconte.

- **Il veut que ça se passe proprement.** Pas gagner : que ça ne devienne pas
  un massacre, parce qu'il sait ce que devient une ville prise par une foule.
- **Il craint de croiser quelqu'un qui le reconnaisse.** Il porte un heaume
  fermé par temps clair.
- **Manière** : courtois avec les gueux, ce qui les met mal à l'aise. Il dit
  « je vous prie » à des hommes qu'il envoie mourir.
- **Dans le sac** : **le seul corps qui ne rompt pas.** Sa morale plancher est
  posée au-dessus du seuil de déroute. Quand tout le reste flue, ses neuf cents
  tiennent — et c'est lui qui rend la bataille lisible, parce qu'un lecteur a
  besoin d'un point fixe.

## Marda la Boiteuse — la Gadoue, 1 200 hommes

**Cabaretière, cinquante-deux ans, une hanche prise depuis l'hiver.** Elle
n'est pas adoubée et elle a refusé de l'être. Ce sont ses rues qui la suivent,
pas Perkin.

- **Elle veut son fils.** Le guet l'a pris il y a deux lunes pour une affaire
  de trois barils, et personne n'a plus rien dit depuis. Elle marche pour
  ouvrir des cachots, pas pour prendre un château.
- **Elle craint de gagner** — parce qu'il faudra nourrir douze cents personnes
  le lendemain matin, et elle est la seule de toute cette armée à y avoir pensé.
- **Manière** : parle aux hommes comme à des clients qui doivent de l'argent.
  Coupe Perkin sans s'en apercevoir.
- **Dans le sac** : ses douze cents connaissent le quartier. **Ils ne suivent
  pas la colonne** : ils passent par les ruelles, arrivent par trois côtés, et
  s'arrêtent net devant le poste du guet — l'objectif de Marda n'est pas la
  porte.

## Frère Vaugrain — les cendres, 2 000 hommes

**Frère mendiant, âge inconnu, envoyé par le Berger** — qui, lui, est sur la
colline de Rhaenys et n'a pas approuvé grand-chose.

- **Il veut que ça brûle**, au sens propre, et il ne s'en cache pas. Le péché
  de la ville est un fait matériel pour lui, comme une poutre pourrie.
- **Il ne craint rien de ce qui est ici.** C'est ce qui le rend incontrôlable.
- **Manière** : ne répond jamais à une question. Il répond par un verset, et
  celui qui a posé la question croit avoir eu une réponse.
- **Dans le sac** : **ses deux mille n'entendent aucun ordre.** Ils marchent au
  cantique — vitesse fixe, pas de reformation, pas de déroute, pas d'arrêt. Ils
  arrivent quand ils arrivent, et ils traversent les autres corps s'il le faut.
  C'est le corps qui casse toutes les formations, y compris les siennes.

## Petit Tam — les enfants de la Gadoue, 1 200 hommes

**Dix-neuf ans, débardeur comme son père.** Ce n'est pas un chef : c'est
seulement celui qu'on a le plus entendu crier, avant-hier.

- **Il veut qu'on le regarde.** C'est tout, et c'est assez pour mille deux
  cents morts.
- **Il craint d'avoir l'air d'avoir peur**, ce qui l'empêchera de donner le
  seul ordre juste de la journée.
- **Manière** : hurle des choses que personne n'a décidées, et douze cents
  personnes les font.
- **Dans le sac** : **le corps qui panique.** Seuil de déroute très bas, mais
  reprise rapide — ils fuient de cinquante pas puis reviennent, trois fois.
  C'est eux qui alimentent la couche de peur des habitants ; c'est eux qu'on
  retrouve dans les rues de Culpucier.

---

# LE CAMP DE LA PORTE — la Couronne

**Cent vingt-cinq hommes à la porte et à l'anneau du donjon**, dans le sac
d'aujourd'hui. C'est trop peu et c'est vrai : il n'y a personne pour ordonner
qu'il y en ait davantage.

## Ser Damon Beurrepré — la garde de la porte, 45 hommes

**Capitaine du poste de la Gadoue, quarante-cinq ans, quatorze ans de guet.**

- **Il veut soixante hommes de plus**, et il les a demandés **par écrit, trois
  fois, en douze jours**. Les trois requêtes existent. Personne ne les a lues.
- **Il craint d'avoir raison**, et il a raison depuis trois semaines.
- **Manière** : administratif jusqu'au bout. Il compte à voix haute pendant que
  ça arrive.
- **Dans le sac** : **il meurt dans les quarante premières secondes**, et c'est
  le point de tout ce personnage. Les quarante-cinq de la porte ne sont pas une
  défense, ce sont les quarante-cinq lignes qu'on écrira ensuite. La troisième
  requête est datée de l'avant-veille.

## Lord Ardrian Roseval — châtelain du Donjon Rouge

**Soixante et un ans. Il a tenu ce château sous deux rois et une reine, et il
n'a juré à aucun des trois.**

- **Il veut rendre le Donjon intact** à qui restera debout. Les tapisseries, le
  puits, les livres. C'est sincère et c'est monstrueux.
- **Il craint de choisir.** Il a passé sa vie à ne pas le faire et ça lui a
  très bien réussi.
- **Manière** : parle par inventaires. Quand on lui annonce neuf mille hommes,
  il demande combien de portes.
- **Dans le sac** : c'est lui qui décide si l'anneau des quatre-vingts se
  resserre ou tient. **Il ne le décide jamais à temps.**

## Dame Elyanne de Rosby — soixante et onze ans

**Elle ne partira pas.** Sa litière est prête depuis six jours, dans la cour,
et elle n'y monte pas.

- **Elle veut mourir chez elle**, et le Donjon est chez elle depuis quarante ans.
- **Elle ne craint rien**, ce qui fait d'elle la seule personne à qui Roseval
  ne peut pas mentir.
- **Manière** : brève, drôle, cruelle. Elle appelle Trystane « le ferblantier ».
- **Dans le sac** : rien. C'est le point : elle est **la raison** pour laquelle
  l'anneau tient, et elle ne tire pas un coup.

## Lord Ronard Boisdur — vingt-neuf ans

**Il est pour qu'on ouvre.**

- **Il veut négocier**, c'est-à-dire survivre avec sa maison et ses terres.
- **Il craint qu'on ouvre trop tard pour que ça compte.**
- **Manière** : raisonnable, chiffré, et il a raison sur les chiffres. C'est ce
  qui rend le personnage dangereux plutôt que méprisable.
- **Dans le sac** : la seule variable qui puisse ouvrir le verrou **sans le
  casser**. Une porte ouverte de l'intérieur donne une bataille entièrement
  différente pour zéro pv de porte, et c'est la bifurcation la moins chère du
  modèle.

## Le septon Marris — la Foi

- **Il veut que la Foi ne soit pas nommée dans ce qui va arriver.** Le Berger
  est un septon, et Marris le sait depuis le début.
- **Il craint la vérité** sur ce que la Foi a laissé prêcher.
- **Manière** : consolant, précis, sans une once de tendresse réelle.

## Les meneurs — les vingt-quatre noms

Ceux dont la chute est une ligne. Six par corps du côté de la Rue, six du côté
de la Couronne. On ne les développe pas : ils ont **un nom, un métier, et une
phrase** — c'est tout ce qu'il faut pour qu'une mort soit lisible.

**La Rue** — Bec-de-Lièvre (tanneur) · Sers Nolle (adoubé mardi, ne sait pas
tenir une épée) · la Ferrande (poissonnière, trois fils dans le corps de Marda)
· Hoy le Muet · Ser Ambroise Dent-d'Or (usurier, finance Perkin, marche pour
surveiller son argent) · Tam le Vieux (le père du Petit Tam, venu le chercher).

**La Couronne** — sergent Vullard (trente et un ans de guet, refuse de courir)
· sergent Cosse · Hallis le Fauconnier (tient l'anneau nord) · Ser Emmon Cierge
· la Pie (femme d'armes, seule de l'anneau à avoir déjà vu une émeute) · Gaunt
le Portier (a la clef, et il l'a sur lui).

---

# LES GENS DE LA VILLE

La couche de peur passe sur **quatre cent deux mille habitants**. Aucun n'a de
fiche, et c'est très bien. Mais un fait qui tombe sur un numéro n'est pas une
scène : il en faut **huit avec une adresse**, pour que `peur-gagne` ait
quelqu'un sur qui tomber.

| Qui | Où | Ce qu'il fait quand ça arrive |
|---|---|---|
| **Mestre Ottyn**, apothicaire | au coin de la rue des Sœurs | il ne ferme pas. Il sait ce qui va arriver dans son échoppe dans une heure, et il l'attend. |
| **Nonne la lavandière**, trois enfants | deuxième étage, place aux Poissons | elle compte trois fois et il en manque un. Elle **remonte vers le bruit**. |
| **le vieux Wex**, sourd | sur le pas de sa porte | il ne bouge pas. Il ne bougera pas. |
| **Cateline la sage-femme** | quelque part entre les deux | elle va **vers** la bataille depuis le début, et elle est en train d'accoucher quelqu'un. |
| **Rob l'écailler** | son étal, porte de la Gadoue | il sauve son étal avant sa femme, et il le sait déjà. |
| **les deux Nayle**, frères, quatorze et onze ans | partout | ils **suivent** l'armée. Ils trouvent ça magnifique. |
| **Sœur Jenn**, du septuaire de la Gadoue | à contre-courant | elle ouvre les portes du septuaire et hurle qu'on y entre. Deux cents y entrent. |
| **la Veuve**, receleuse, rue des Sœurs | derrière ses volets | elle ne sort pas et elle achète. Dès ce soir. |

> **La Veuve est celle des Sept Chandelles**, deux ans plus tard, au même
> numéro. C'est un crochet vers l'autre partie et il reste **facultatif** :
> rien du sac n'en dépend. Le jour où on le tire, la troupe est dans cette
> ville pendant que ça se passe — mais on ne l'importe pas, on le joue.

---

## Ce que ça demande au four

Cinq choses, et aucune n'est grosse :

1. **Les corps existent.** `dresser()` fabrique un seul bloc d'assaut ; il en
   faut six, avec chacun son effectif, son point de départ et son comportement.
   C'est le seul vrai chantier de la liste.
2. **Trois comportements de corps, pas un.** *ferme* (Ronnel : plancher de
   morale), *sourd* (Vaugrain : n'entend aucun ordre, ne rompt pas), *versatile*
   (Tam : rompt tôt, revient vite). Les trois autres sont l'ordinaire.
3. **`chef-tombe` ne s'écrit que sur un nommé.** Sinon quatre cent
   soixante-quinze lignes de bruit.
4. **Deux fins qui ne passent pas par le verrou** : Trystane tué, ou Boisdur
   qui ouvre. Le second surtout — il coûte trois lignes et double le nombre de
   batailles différentes que le sac peut produire.
5. **Les huit habitants sont des positions fixes** dans le plan, marquées, que
   `peur-gagne` teste en premier. Un fait qui tombe sur Nonne vaut cent faits
   qui tombent sur des points.

*(1 et 3 sont faits. Reste 2, 4, 5.)*

---
---

# LES ARCS

**Aucun de ces arcs n'est scripté, et il ne faut pas qu'ils le soient.** Ils
sont tous des CONSÉQUENCES de la mise en place — six têtes qui ne se parlent
pas, un flanc à trois cents mètres, une nuée collée à la ville, une porte de
six mètres. On ne les déclenche jamais : on les reconnaît dans le flux quand
ils arrivent, et s'ils n'arrivent pas, c'est une information sur le modèle et
non un accident à rattraper.

## L'horloge de la nuit

Quatre heures, et elles n'ont pas le même sujet. La porte n'occupe que la
première ; tout ce qui compte se passe après elle.

| Heure | Ce qui se passe | Ce que le sac émet |
|---|---|---|
| **0h00** | six corps posés, le jour tombe | *(rien — et ce silence est une donnée)* |
| **0h12** | le centre touche le premier | `contact` · `premier-sang` |
| **0h14** | Beurrepré tombe au milieu de son rang | `chef-tombe` (nommé) |
| **0h12→0h40** | **l'heure creuse** — la porte ne bouge pas | `escouade-rompt` · `ralliement` |
| **0h40** | Crochet arrive par le flanc, avec les outils | `ordre` · `contact` |
| **0h55** | la porte cède | `porte-cede` |
| **1h05** | Vaugrain traverse tout le monde | `escouade-rompt` en série |
| **1h10** | la porte est enfoncée | `porte-enfoncee` |
| **1h10→1h30** | le quartier se vide | `peur-gagne` · `rumeur-gagne` |
| **1h30→2h30** | six cents mètres de rue, en colonne | `assaut-au-donjon` |
| **2h30** | **le premier coureur atteint le Donjon** | `roi-averti` *(à écrire)* |
| **3h20** | l'anneau | `contact` · `tete-tombe` |
| **4h00** | l'aube, et le compte | `issue` |

## Les six arcs

### I. L'heure creuse — et c'est le meilleur

**De 0h12 à 0h40, la porte ne bouge quasiment pas, et personne ne comprend
pourquoi.** L'arithmétique est pourtant simple : trois mille points de porte,
sept hommes de front, onze points par homme et par seconde. **Trente-neuf
secondes**, si le front est plein.

Il ne l'est jamais. Chaque tête n'envoie qu'UNE aile presser — les autres sont
en réserve — et il y a six têtes qui délibèrent chacune sur son horloge.
Résultat : à un instant donné, trois ou quatre hommes cognent, pas sept, et
ceux qui attendent perdent leur morale à regarder tomber les leurs.

**Ce que ça produit à lire** : une demi-heure de gens qui meurent sur un seuil
sans le faire céder. C'est l'image la plus vraie d'un assaut, et elle est
gratuite — elle tombe de six horloges qui ne battent pas ensemble.

### II. Le flanc qui n'arrive pas

Crochet est à **trois cents mètres** avec les masses, les coins et les
cordages. Sans lui, la porte tient. Avec lui, elle tombe en quelques minutes.

**Il ne sait pas qu'on l'attend, et personne ne peut le lui dire.** Aucun
signal ne traverse trois cents mètres de rive dans cette armée — c'est la même
asymétrie que le plancher du Grenier, et elle produit la même chose. Le seul
moyen de le presser est d'aller le chercher, c'est-à-dire de perdre un homme
et vingt minutes.

**Le battement à ne pas manquer** : l'écart entre `porte-cede` et l'arrivée de
Crochet. S'il est court, la mise en place est bonne. S'il est de vingt minutes,
c'est que le centre est mort pour rien — et ça, ce n'est pas un bug, c'est
l'histoire.

### III. Vaugrain traverse

**Deux mille hommes qui n'entendent aucun ordre, qui ne rompent pas, et qui
arrivent quand ils arrivent.** Ils ne contournent pas : ils passent au travers.

Ce corps est le seul qui puisse **remplir le front tout seul**, parce qu'il ne
connaît pas la réserve. Il est aussi le seul qui puisse **boucher
définitivement** le seuil en y entassant du monde qui ne recule jamais.

Les deux issues sont bonnes, et on ne choisit pas laquelle : c'est l'heure de
son arrivée qui décide, et son heure ne dépend que de la distance qu'on lui a
donnée au départ.

### IV. La ville s'en aperçoit

`porte-enfoncee` est le seul fait qui change d'échelle. Avant lui, la bataille
tient dans deux cents mètres. Après, **quatre cent deux mille personnes** sont
dans le calcul.

Et la peur passe par les RUES, pas à vol d'oiseau. Une rue qui se vide dans un
sens pendant que le guet y monte dans l'autre est ce que cette couche sait
produire de mieux ; il faut la regarder arriver et ne pas la commenter.

### V. Les six cents mètres

De la porte au Donjon il y a **613 mètres de rue**, et une colonne s'y étire.
C'est là que l'armée cesse d'être une armée :

- **Marda décroche.** Elle n'a jamais marché pour le château : elle marche pour
  un cachot. Douze cents personnes quittent la colonne sans avoir désobéi à
  quiconque — personne ne leur avait rien ordonné.
- **Tam se délie.** Une escouade sans ordre frais entre dans un bâtiment. Elle
  en ressort quatre à huit minutes plus tard, chargée. **Et le bâtiment a un
  numéro.**
- **Ronnel tient**, et c'est le seul point fixe qu'un lecteur ait dans toute
  cette page.

### VI. L'anneau, et l'homme qui ne décide pas

Quatre-vingts hommes en cercle à vingt-six mètres du Donjon, et Roseval qui
n'ordonne jamais à temps de le resserrer. **Ce n'est pas de la lâcheté : c'est
une chaîne administrative qui demande la permission.** Elle est lente par
construction, comme celle de l'assaut est sourde par construction.

Trois chaînes, trois défauts différents. La ville tombe dans l'écart.

## Les huit nœuds de tension

Ceux qu'on peut jouer. Chacun est un **écart entre deux horloges**, jamais un
jet de dés.

1. **La porte contre le flanc.** Le centre peut-il tenir jusqu'à Crochet ?
2. **Le seuil contre la réserve.** Six têtes, une seule aile pressée chacune —
   à quel moment deux corps poussent-ils en même temps, par hasard ?
3. **La bannière contre le nombre.** Un capitaine tombe, son aile perd sa
   morale d'un coup. Le prochain ordre mettra vingt secondes à arriver par
   coureur — et le coureur peut mourir.
4. **La déroute contre le ralliement.** Une aile rompt, un chef vivant à moins
   de quinze mètres la ramène. « L'aile de l'ouest a rompu deux fois et s'est
   reformée une fois » est la meilleure ligne que ce moteur sache écrire.
5. **Vaugrain contre tout le monde.** Son heure d'arrivée, et elle n'est
   négociable par personne.
6. **La rue qui se vide contre le guet qui monte.** Les deux à la même minute,
   dans la même rue.
7. **L'heure où le roi apprend.** Le fait le plus précieux du fichier : l'écart
   entre `porte-cede` et `roi-averti`. **Vingt minutes de ville qui sait avant
   que le pouvoir ne sache.**
8. **Boisdur contre Roseval.** Une porte qui s'ouvre de l'intérieur ne coûte
   pas un point de verrou, et change la bataille entière.

---
---

# CE QUI PARVIENT AUX JOUEURS

**La règle est déjà écrite ailleurs et elle vaut ici sans un mot de plus :**
avant de narrer un fait, ont-ils une source pour le savoir ? Un fait de la
bataille n'arrive au joueur que si l'un de ses trois était à portée, à cette
minute-là.

Le tuyau existe : c'est **la balade**. Elle produit déjà un pas tous les vingt
mètres, daté et situé ; le sac produit des centaines de faits datés et situés.
`serveur/croiser.js` ne fait que joindre les deux, par une fonction pure de
(où, quand) — comme `journee.js` répond `ou(corps, minute)`.

## Trois portées, parce qu'un homme n'a pas qu'un sens

| | quoi | ce qu'on en dit |
|---|---|---|
| **vu** | c'est en train d'arriver, et c'est dans la rue | tout : qui, quoi, à combien de pas |
| **entendu** | c'est en train d'arriver, loin | **rien** — un fracas et un quartier. C'est le seul canal qui tourne au coin d'une rue |
| **trace** | c'est déjà arrivé et ça a laissé quelque chose | ce qu'on trouve par terre, et **depuis combien de temps** |

La troisième est la bonne. Une porte défoncée reste défoncée ; un blessé qui
respire est encore là au matin, à une adresse, et il sait quel ordre il avait
reçu. **Ça ne s'entend pas, ça ne s'invente pas : ça se voit en passant.**

## La table EST le système

Un type de fait, trois nombres — portée à l'œil, portée à l'oreille, durée de
la trace. Rien d'autre. **Tout comportement qu'on ajoutera — un pillard, un
porteur d'ordre, une barricade — devient perceptible en écrivant SA LIGNE**, et
la balade n'a pas à être retouchée. C'est le seul endroit à toucher, et c'est
délibéré.

Les chiffres sont des mesures, pas des réglages : une porte bardée de fer qu'on
enfonce s'entend à sept cents mètres dans une ville de nuit ; un homme qui
tombe ne s'entend pas à quarante.

## Ce qui se lève arrête la marche

Le manuel le dit — « alors on arrête de marcher » — et ça ne pouvait pas rester
à la main du MJ : quand le joueur traverse un assaut, ses jambes doivent
s'arrêter à l'instant où il le voit, pas trois pas plus loin. Un fait `vu` de la
liste `ARRETENT` coupe la balade, ferme le sac, et la page cesse d'avancer.

## Pas de fichier, pas de bataille

`etat/bataille.json` dit QUAND le sac tombe dans la partie :

```json
{ "sac": "portreal", "debut": { "jour": 3, "minute": 1200 } }
```

Sans lui, `croiser.autour()` rend `null` au premier test et ne lit rien — le cas
normal. **Une bataille cuite n'est pas une bataille en cours tant qu'un MJ ne
l'a pas datée**, et c'est pour ça que l'ancre est dans `etat/` et non dans le
monde engendré.

Ce que ça donne, mesuré sur le sac actuel :

```
devant la porte, à la minute du contact
   vu      : porte-enfoncée à 0 pas | blessé à 5 pas | chef-tombe à 5 pas | contact
   arrêt   : oui
à 300 m, même minute
   entendu : porte-enfoncée (Le port et ses hangars)      ← le quartier, rien d'autre
devant la porte, une heure plus tard
   traces  : porte-enfoncée depuis 60 min | trois blessés à 5 et 10 pas, depuis 60 min
```

---
---

# LE NARRATIF

Ce qui entoure la nuit. Rien ici ne se simule : c'est ce qu'un MJ raconte
autour du fichier, et c'est ce qui fait qu'on lit un document au lieu d'un
journal.

## Pourquoi ça a lieu, en une phrase

**Parce qu'il n'y a personne au-dessus.** Rhaenyra a fui, les Hightower ne sont
pas rentrés, et pendant onze jours Port-Réal a découvert qu'un trône vide n'est
pas une menace : c'est une place. Perkin l'a prise le premier parce qu'il est
le seul à avoir compris que ça ne durerait pas.

## Les trois jours d'avant

**Le onzième jour avant.** Perkin adoube deux cents hommes du ruisseau sur la
place aux Poissons, avec la même épée, en un après-midi. Personne ne lui
demande de quel droit. **C'est le moment où l'affaire devient possible**, et
c'est un moment de théâtre, pas de guerre.

**Le neuvième.** Trystane est couronné. La couronne est en fer-blanc et sort de
chez un ferblantier de la Gadoue, qui n'a pas été payé et qui le dira à
quelqu'un. **Un roi qu'on a fait à crédit.**

**Le troisième.** Ser Damon Beurrepré écrit sa troisième demande de renfort.
Elle est datée, elle est enregistrée, et elle sera retrouvée. C'est le seul
document de toute cette histoire qui accuse quelqu'un, et il n'accuse personne
en particulier — ce qui est pire.

**La veille.** Marda apprend que son fils n'est plus au poste de la Gadoue. On
ne lui dit pas où il est. Elle décide de marcher, et douze cents personnes
décident avec elle sans qu'on leur ait rien demandé.

## La nuit

Elle a un sujet, et ce n'est pas la porte : **c'est que personne ne commande.**

Six hommes croient mener la même chose et mènent six choses différentes.
Perkin veut un titre. Crochet veut un péage. Ronnel veut que ça se passe
proprement. Marda veut un cachot. Vaugrain veut du feu. Tam veut qu'on le
regarde. Ils marchent tous vers la même porte et **aucun d'eux ne veut la même
ville derrière.**

En face, quatre personnes enfermées dans un château discutent de savoir s'il
faut ouvrir, et un homme de soixante et un ans qui a survécu à deux rois en ne
choisissant jamais s'aperçoit qu'il va devoir choisir. Il ne le fera pas.

Entre les deux, **quatre cent deux mille personnes** qui n'ont rien demandé, et
dont huit ont un nom.

## Le matin

C'est là que le sac devient jouable, et c'est le vrai produit de tout ce
travail. À l'aube il y a, dans les rues, entre la porte et le Donjon :

- **des blessés vivants, immobiles, à des adresses précises.** Chacun sait quel
  ordre il avait reçu, qui était son chef, et où allait son aile. On peut les
  aider, les dépouiller, les interroger, les dénoncer.
- **des bâtiments où des soldats sont entrés**, avec leur numéro, leur heure
  d'entrée et leur heure de sortie.
- **des habitants qui ont vu**, et dont certains mentiront.
- **une couronne de fer-blanc** quelque part, qui n'a pas été payée.

Le MJ ne lit pas une simulation : il lit **une liste de bouches à faire
parler**. C'est ça, « traversable ».

## Où la troupe est là-dedans — et c'est facultatif

Si l'on tire le crochet vers les Sept Chandelles, deux ans ont passé et rien
n'a changé pour eux : le Grenier est toujours rue des Sœurs, entre la colline
de Visenya et la porte de la Gadoue. **C'est-à-dire à un bon millier de pas de
la porte qu'on enfonce** — assez loin pour qu'on n'y voie rien, assez près pour
qu'on entende, et exactement sur le chemin de ceux qui refluent.

> Le chiffre au pas près attend que `lieu:le-grenier` soit réparé : son
> affectation pointe aujourd'hui hors du monde engendré.

Trois choses tombent toutes seules, et aucune ne demande qu'on écrive quoi que
ce soit de neuf :

1. **Ils jouent ce soir-là.** Sept chandelles au bord de la scène, trois cents
   personnes debout, et la salle entend le bruit avant de comprendre. La foule
   est la couverture — sauf que cette fois elle sort en courant.
2. **Le Grenier est sur le chemin.** Une escouade déliée entre dans un bâtiment
   numéroté ; il n'y a aucune raison que ce ne soit pas celui-là. **Et la cave
   a trois serrures.**
3. **Un porteur d'ordre est un objet de vol.** Un homme qui court entre deux
   rangs de la chaîne, avec de l'information dedans, interceptable et
   corruptible. C'est le seul acteur de toute la bataille qui transforme la
   nuit en coup possible au lieu d'une toile de fond.

Et la Veuve est derrière ses volets, rue des Sœurs, à ne pas sortir. **Elle
achète dès ce soir**, et elle achètera moins cher que d'habitude, parce que
tout le monde vend en même temps.

---

## Les douze noms — posés

Ils sont dans `etat/corps.json`, sous `affectations`, et ils ont donc des
mètres : toute distance entre deux d'entre eux est désormais un FAIT et non une
estimation.

| Nom | Bât. | Usage | Ce que ça sert |
|---|---|---|---|
| **Le poste de la Gadoue** | 13382 | corps-de-garde | les 45 de Beurrepré, et ses trois demandes de renfort |
| **La geôle du Crochet** | 20405 | geole | où est le fils de Marda — **au-delà du Donjon** |
| **Le corps de garde de l'ouest** | 26189 | corps-de-garde | ce que Marda prend en premier, et il n'y est pas |
| **La Corde Mouillée** | 141 | taverne | premier carrefour dedans — le soulèvement s'y est décidé |
| **Le septuaire de la Gadoue** | 27136 | septuaire-quartier | sœur Jenn ouvre les portes, deux cents entrent |
| **Le ferblantier de la Gadoue** | 16215 | forge | la couronne de fer-blanc, jamais payée |
| **L'échoppe de mestre Ottyn** | 2671 | echoppe | **le milieu exact** des 613 mètres |
| **Le Dernier Degré** | 20367 | taverne | dernier carrefour avant la montée |
| **La forge du Degré** | 20375 | forge | même carrefour — où une foule s'arme |
| **Le hangar d'aval** | 39758 | entrepot | d'où part Crochet, avec les masses et les coins |
| **Le hangar de la grève** | 4 | entrepot | d'où part Vaugrain |
| **La Boiteuse** | 26219 | taverne | le cabaret de Marda — ses rues à elle |

> **L'index est volatil, la position ne l'est pas.** Une première tentative a
> posé trois noms pendant que `portreal.bati.json` était réécrit ; les index ont
> glissé et les noms ont atterri sur des maisons quelconques. Ils ont été
> défaits. La passe qui a réussi résout les cibles **par usage et par position**
> au dernier moment, et vérifie que le fichier de bâti n'a pas bougé entre le
> début et la fin. Après toute régénération : `affecter.py --verifier`, et
> reposer ce qui a glissé.

**Ce que les mètres disent, maintenant qu'on peut les mesurer :**

| De | À | |
|---|---|---|
| le poste de la Gadoue | la geôle du Crochet | **855 pas · 8 minutes de marche** |
| le corps de garde de l'ouest | la geôle du Crochet | **880 pas** — l'erreur de Marda, en distance |
| le poste de la Gadoue | l'échoppe de mestre Ottyn | 401 pas · 4 minutes |

**Deux cadeaux de la géométrie, que personne n'avait écrits :**

1. **La geôle est trente-cinq mètres DERRIÈRE le Donjon Rouge.** Marda ne marche
   pas sur un château, elle marche sur un cachot — et pour l'atteindre il faut
   avoir traversé toute la bataille, dépassé la porte, remonté les six cents
   mètres, et franchi l'anneau. Son arc est le plus long de la nuit et c'est le
   plan qui l'a décidé.
2. **Il y a un second corps de garde à cent quarante mètres à l'ouest.** Elle le
   prend en premier, parce qu'il est le plus proche et qu'on lui a dit « au
   poste ». Son fils n'y est pas. Elle perd vingt minutes et douze cents
   personnes s'arrêtent avec elle.

**Deux choses restent en suspens, et elles ne sont pas de la bataille :**

- **`lieu:le-grenier` a bougé.** Il pointait hors du monde engendré ; il résout
  maintenant sur un entrepôt de quinze mètres de façade **dans « Le port et ses
  hangars », juste hors les murs** — alors que `docs/troupe.md` le veut rue des
  Sœurs, entre la colline de Visenya et la porte. La taille va, le quartier
  non. Ce n'est pas à la bataille de trancher où habite la troupe.
- **`personnage:ostor-bray` porte le monde `port-real`**, qui n'existe pas
  (c'est `portreal`). Un tiret de trop, et l'affectation est morte.

## Ce qui reste ouvert, et qu'on ne tranche pas d'avance

Si Trystane meurt ou s'il parle. Si Boisdur ouvre, et si c'est à temps. Ce que
Marda trouve dans le cachot. Si Ronnel est reconnu. Et lequel des huit
habitants ment le lendemain.
