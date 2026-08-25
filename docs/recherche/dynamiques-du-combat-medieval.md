# Dynamiques réelles du combat médiéval

> Note de recherche — état des connaissances historiques et archéologiques utiles au modèle.
> Rédigée pour répondre à des questions précises de conception : taille des groupes, formations,
> proportion d'hommes réellement engagés, comportement des non-engagés, rythme des combats,
> recul et repli partiel.
>
> **Avertissement de méthode.** Aucune de ces questions n'a de réponse « établie ». On ne dispose
> d'aucun témoignage à hauteur d'homme pour une bataille médiévale. Ce qu'on a : des chroniques
> écrites par des clercs, souvent après coup, qui décrivent le *quoi* et presque jamais le *comment* ;
> de l'archéologie funéraire ; et un raisonnement de plausibilité à partir de l'endurance humaine,
> de la psychologie du combat et de guerres mieux documentées. Chaque section distingue donc
> **ce qui est attesté**, **ce qui est déduit**, et **ce qui est contesté**.

---

## 0. Le raisonnement central, en une page

Tout le reste découle d'une contradiction que les sources imposent :

| Fait | Source |
|---|---|
| Les batailles durent **des heures** | Végèce : 2–3 h « d'ordinaire ». Bouvines : 3 h de mêlée. Azincourt : ≤ 3 h. Hastings : ~9 h. Towton : ~10 h. César à Ilerda : 5 h de combat continu entre cohortes. |
| Le vainqueur perd **très peu** | Grèce hoplitique (Krentz) : ~5 % des vainqueurs, ~14 % des vaincus. Rome : ~5 % de morts chez le vainqueur, même après des heures (Cynoscéphales 700, Magnésie 350, Pydna 100, Pharsale 230). Médiéval : consensus 5–10 % vainqueur, 10–30 % vaincu. Courtrai 1302 : ~100–300 Flamands morts contre au moins la moitié de 2 500 chevaliers français. |
| Un homme en armure ne peut pas se battre à pleine intensité plus de **~90 secondes** | Étude physiologique 2024 sur le combat médiéval sportif : 3 rounds de 90 s (4 min 30 de combat effectif) → FC moyenne 170 bpm (90 % de FCmax), pic 193, lactate 1,0 → 8,2 mmol/L pour un seuil à 2,9. Dégradation mesurable de la vitesse des frappes dès le round 3. |

**Ces trois faits sont incompatibles avec l'image du duel continu.**

Le calcul de Sabin le rend brutal : supposons que seuls 5 % des hommes soient au premier rang, qu'ils
frappent une fois toutes les 5 secondes, et que **moins de 1 %** des coups tue. Chaque armée perdrait
alors 5 % de morts **toutes les dix minutes**. Or 5 % est le total du vainqueur pour toute la bataille.
Le taux réel de coups portés efficacement est donc inférieur d'au moins un ordre de grandeur à celui
d'un échange continu.

**Conclusion structurante : pendant l'immense majorité d'une bataille, l'immense majorité des hommes
ne frappe personne et n'est frappée par personne.** La bataille est faite de longues attentes tendues
ponctuées de brèves bouffées de violence — et, à la fin, d'un massacre unilatéral.

C'est exactement l'objectif de ressenti du projet : chaque homme tient à sa peau, et cela se voit
dans la statistique.

---

## 1. Taille des groupes

### 1.1 Le groupe primaire : 3 à 25 hommes

C'est l'échelle où vit la cohésion. La science militaire moderne distingue le **moral** (l'attachement
à la cause : il amène l'homme sur le champ de bataille) de la **cohésion** (l'attachement à ses
camarades : elle l'y maintient). La cohésion se fabrique dans un groupe en face-à-face, petit.

Unités médiévales attestées à cette échelle :

| Unité | Effectif | Détail |
|---|---|---|
| **Lance fournie** (France, ordonnance de 1445) | **6** | 1 homme d'armes, 1 coutilier, 1 page, 3 archers. |
| **Lance** (Bourgogne, ordonnance d'Abbeville 1471, reprise en 1472 et 1473) | **9** | 1 homme d'armes, 1 coustillier, 1 page non-combattant, 3 archers montés, 3 fantassins (arbalétrier, couleuvrinier, piquier). |
| **Conroi** | **6 à 25** cavaliers | Unité d'entraînement *et* de combat des chevaliers. Ils s'entraînent ensemble et chargent ensemble. |
| **Vintaine** (Angleterre, commissions of array) | **20** | 19 hommes commandés par le vingtième, le *vintenar*. Équivalent moderne : la section / le peloton. |

**Pour le projet : 50 hommes par camp, c'est 2 à 3 conrois, ou 2 à 3 vintaines.** C'est-à-dire
précisément l'échelle du groupe primaire. Le modèle social peut donc être concret : chaque homme a
un chef immédiat et une poignée de voisins qu'il connaît, et c'est tout.

### 1.2 Le groupe tactique : 50 à 200

- **Centaine** (Angleterre) : 5 vintaines = **100 hommes** sous un *centenar*, lequel est monté
  même quand ses hommes sont à pied — parce qu'il doit voir et se déplacer.
- **Bannière** : le groupe de gens d'armes autour de la bannière d'un banneret, de dix à quelques
  dizaines d'hommes. La bannière est un point de ralliement **et un signal visuel** : sa chute est
  une information qui se propage.
- **Chambre** bourguignonne : 6 lances = 54 hommes. **Escadre** : 4 chambres.

### 1.3 La bataille : 500 à plusieurs milliers

La *bataille* (angl. *battle*, *ward*) est une division d'armée entièrement **ad hoc** : sa taille
dépend du besoin, pas d'un tableau d'effectifs. Une armée de campagne est typiquement rangée en
**trois batailles** : avant-garde, corps de bataille, arrière-garde. Dans chaque bataille, la
cavalerie est répartie en conrois / bannières, l'infanterie forme un bloc séparé subdivisé de même.

Ordres de grandeur :

- **Compagnie d'ordonnance** (1445) : 100 lances = 600 hommes. 15 compagnies = 9 000 hommes dont
  6 000 combattants.
- **Bouvines (1214)** : la première ligne de l'aile droite française « occupait 1 040 pas en travers
  du champ de bataille » (≈ 750–900 m).
- **Courtrai (1302)** : ~10 000 fantassins flamands en trois grandes divisions plus un corps de
  réserve derrière.

---

## 2. Ligne ou pas ligne ?

**Oui, la ligne — mais pas le rectangle propre du XVIIIᵉ siècle.**

### 2.1 L'attestation la plus nette : Bouvines, 1214

Guillaume le Breton rapporte l'ordre donné par frère Guérin, évêque élu de Senlis, qui range l'aile
droite française. C'est probablement le passage le plus utile de toute la littérature médiévale pour
notre problème :

> « Le champ est large ; étendez-vous à travers le champ **en ligne droite**, de peur que les ennemis
> ne vous coupent. **Il ne convient pas qu'un chevalier se fasse un bouclier d'un autre chevalier** ;
> mais tenez-vous de telle sorte que vous puissiez **tous combattre sur une seule ligne**. »

Trois choses en une phrase :

1. La ligne est **voulue**.
2. La tendance naturelle des hommes est de **se mettre derrière quelqu'un d'autre**.
3. Le commandement doit **lutter activement** contre cette tendance.

Le même passage indique que Guérin, avant la bataille, avait **trié ses hommes** : il « avait déplacé
vers l'arrière ceux qu'il savait craintifs et sans ardeur », et placé en première ligne ceux dont il
était sûr. Les hommes ne sont pas interchangeables, et les chefs le savaient.

### 2.2 Géométrie

| Grandeur | Valeur | Remarque |
|---|---|---|
| Front par homme, ordre serré | **0,45–0,9 m** | 18 pouces (boucliers verrouillés, cas extrême) à 3 pieds. Les calculs sur Azincourt utilisent 27 pouces ≈ 0,69 m. |
| Front par homme, ordre lâche | **~1,35 m** | Largeur de file romaine estimée ; laisse la place de reculer et de laisser passer un blessé. |
| Profondeur usuelle | **4 à 16 rangs** | Azincourt : les hommes d'armes anglais sur **4 rangs** (Tito Livio, Pseudo-Elmham) — très peu profond. |
| Colonne suisse | **56 × 20** | Reconstitution du contingent de Zurich, 1443 : ~51 m de front sur 43 m de profondeur. |
| Carré de piques | **10 × 10** | ~100 hommes. |
| Rangs pouvant réellement employer leur arme | **3 à 5** | Au-delà, les piques sont tenues « au port », verticales, pour ne pas blesser les amis devant. |

### 2.3 Ce que la ligne est réellement

Pas une entité, mais **une chaîne de sous-unités** (conrois, vintaines, bannières) chacune dotée de
sa cohésion locale. Elle est poreuse, elle a des intervalles, elle plie. Les avancées et les reculs
sont **locaux** : sur un front de plusieurs centaines de mètres, un sous-groupe qui avance ou recule
de quelques mètres ne compromet pas l'ensemble.

Corollaire pour le modèle : **il ne faut pas modéliser « une ligne », il faut modéliser des grappes
qui se comportent comme une ligne tant que la cohésion tient.** La ligne doit être un résultat, pas
une contrainte.

---

## 3. Proportion d'hommes réellement engagés

### 3.1 La contrainte géométrique

Seul le premier rang peut frapper (deux si les armes sont longues).

| Profondeur | Fraction au contact |
|---|---|
| 4 rangs | 25 % |
| 8 rangs | 12,5 % |
| 16 rangs | 6 % |
| Colonne suisse, 20 rangs | 5 % |

À Azincourt, l'écrasante majorité des Français n'a jamais touché un Anglais.

### 3.2 La contrainte psychologique (déduite, et contestée)

Goldsworthy soutient qu'au sein même du premier rang, **au moins trois quarts** des hommes
« combattaient davantage dans le but de rester en vie que dans celui de tuer l'ennemi ». Son image :

> une ligne d'hommes au contact, la majorité combattant très prudemment, tirant le maximum de
> protection de leur bouclier, surveillant leur adversaire, ne portant qu'occasionnellement un coup
> faible, exposant aussi peu que possible leur bras et leur flanc droits. Une minorité combat bien
> plus agressivement.

**Réserve importante.** Cet argument est bâti par analogie sur le *ratio of fire* de S. L. A. Marshall
(1947), dont on sait aujourd'hui que la méthode est douteuse voire fabriquée. Devereaux souligne en
outre que rien ne garantit qu'un résultat portant sur des armes à feu se transpose aux armes de contact.

**Ce qu'on garde :** l'idée qu'une **minorité fait l'essentiel du travail létal** est indépendamment
soutenue par les sources médiévales elles-mêmes — le tri de Guérin à Bouvines, la mortalité élevée
des centurions romains qui combattaient en permanence au premier rang, la place des porte-enseignes
et des chefs subalternes dans le déclenchement des assauts. **Ce qu'on abandonne :** le chiffre
« trois quarts », qui n'a pas de base empirique.

### 3.3 Chiffre de travail

À un instant donné, dans une formation engagée : **~10–25 % des hommes sont au contact**, et parmi
eux une minorité seulement porte des coups sérieux. Soit de l'ordre de **5 à 10 % de l'armée en
train de frapper**, à tout moment. Le reste attend — ce qui ne veut pas dire qu'il ne fait rien.

---

## 4. Comportement des hommes non engagés

C'est probablement la section la plus riche pour le simulateur, parce que ces hommes sont la
majorité et qu'ils déterminent l'issue.

### 4.1 Pousser — et tuer les siens

Le comportement le plus meurtrier de toute l'histoire de la bataille médiévale. À Azincourt, les
rangs arrière français poussent pour avoir leur part du combat : ils renversent leurs propres
hommes de tête, les privent de la possibilité de reculer, et les poussent sur les armes anglaises.
Des hommes meurent étouffés sous des tas de leurs propres camarades.

Ce n'est ni de la lâcheté ni de la stupidité : c'est de la **physique des foules**. La recherche
moderne donne des seuils utilisables tels quels :

- **2–3 pers./m²** : l'écoulement commence à se dégrader.
- **4–5 pers./m²** : contacts involontaires, le risque monte nettement.
- **5–6 pers./m²** : le mouvement volontaire est perdu ; la foule se comporte comme un fluide ;
  risque d'asphyxie par compression.
- Au-delà : **effondrement progressif** — un homme tombe, les autres basculent dans le trou, effet
  domino. Ondes d'arrêt-redémarrage, montées de pression qui se propagent.

> **Le mécanisme de mort est un problème de physique, pas de comportement.**

Cela donne une règle de modèle très nette : **la capacité de reculer est une ressource.** Quand la
densité derrière un homme dépasse un seuil, il la perd, et son taux de mortalité fait un bond.
C'est ce qui explique Cannes et Azincourt, et c'est pourquoi une attaque de flanc ou de dos est si
dévastatrice — pas seulement par le choc psychologique, mais parce qu'elle **tasse les victimes les
unes contre les autres** et leur retire la « distance de sécurité ».

### 4.2 Encourager

À Zama, Polybe note que les *principes* soutenaient leurs camarades « en les acclamant, non en les
poussant » — et il présente les acclamations de cette seconde ligne **non encore engagée** comme
décisives dans l'effondrement psychologique de la ligne adverse. À Bouvines, Guérin est présent
« non pas pour combattre, certes, mais pour encourager et inspirer les troupes ».

### 4.3 Lancer

Les rangs arrière conservent leurs armes de jet plus longtemps que les hommes de tête, qui ont les
mains prises. À Chéronée, Plutarque décrit un flux constant de javelots depuis les rangs arrière
romains pendant le contact. (Zhmodikov généralise ; Devereaux conteste — voir § 5.4.)

### 4.4 Attendre sous tension — et la différence entre « derrière » et « en réserve »

Distinction capitale, due à Ardant du Picq et reprise par Sabin :

- Les hommes des **rangs arrière de la même formation** ne sont **pas** protégés du stress. Ils sont
  à quelques mètres de l'ennemi, ils doivent se préparer à une charge à tout moment, ils surveillent
  le ciel pour les projectiles. Ils s'usent presque comme ceux de devant.
- Les hommes d'une **formation distincte tenue en arrière** sont, eux, hors de « la sphère de
  tension morale ». C'est là toute la valeur du système romain à lignes multiples.

> « Les meilleures tactiques, les meilleures dispositions étaient celles qui facilitaient le plus une
> succession d'efforts en assurant la relève par rangs des unités en action, n'engageant réellement
> que les unités nécessaires et gardant le reste en soutien ou en réserve **hors de la sphère
> immédiate de tension morale**. » — Ardant du Picq

Pour le modèle : la **distance à l'ennemi** doit moduler l'accumulation de fatigue nerveuse, même
sans contact.

### 4.5 S'esquiver par l'arrière

César, au Sambre, décrit des hommes qui **s'éclipsent depuis l'arrière** de cohortes en difficulté.
Les colonnes napoléoniennes se rompaient de même par l'arrière, pas par l'avant.

> **Une formation ne se dissout pas par le point où elle est frappée, mais par le point d'où l'on
> peut partir sans être vu.**

### 4.6 Ne jamais s'engager du tout

Des divisions entières peuvent rester spectatrices. À Azincourt, la troisième bataille française
n'entre jamais au contact et se disperse. À Ilipa, le centre punique regarde ses ailes se faire
détruire plutôt que d'avancer.

### 4.7 Piller, capturer

Incitation spécifiquement médiévale et très forte : **une rançon est une fortune**. À Bouvines, il
est explicitement noté du comte de Saint-Pol qu'il traverse les ennemis « ne capturant personne » —
la remarque n'aurait aucun sens si capturer n'était pas la norme. Capturer un homme, c'est sortir
du combat avec lui.

### 4.8 Se retirer pour souffler

À Azincourt, les hommes d'armes anglais combattent un moment puis **se replient pour se reposer**.
Voir § 5.

---

## 5. Rythme : durée des engagements et des pauses

### 5.1 Le problème

3 heures de bataille, ~90 secondes d'endurance à pleine intensité. Il n'y a pas de lecture littérale
possible. Une « bataille » est **une longue séquence d'épisodes** : escarmouches, chocs, manœuvres,
retraits, pauses.

### 5.2 Ce que les sources disent explicitement

**Bouvines, 1214** — l'attestation médiévale la plus directe d'un cycle désengagement / repos /
réengagement, au niveau de l'unité :

> Le comte de Saint-Pol, **s'étant retiré un peu à l'écart**, tellement fatigué des coups innombrables
> qu'il avait reçus et donnés, **se reposa un moment, le visage tourné vers les ennemis**.

puis, après avoir dégagé un de ses chevaliers :

> Et ainsi, **après avoir repris son souffle un court moment**, il avança de nouveau avec ses propres
> chevaliers (**qui s'étaient reposés entre-temps**), au milieu des ennemis.

Trois détails valent de l'or pour le modèle : le repos est **court** ; il se fait **face à l'ennemi**,
pas dos tourné ; et il est **collectif** — l'unité entière souffle, pas seulement le chef.

**Forum Gallorum, 43 av. J.-C.** (Appien), sur deux légions vétéranes :

> lorsqu'ils étaient accablés de fatigue, ils **s'écartaient les uns des autres un bref instant pour
> reprendre haleine, comme dans les jeux gymniques**, puis se ruaient de nouveau à la rencontre.

*Réserve :* Devereaux considère ce passage comme un morceau littéraire très travaillé — Appien écrit
deux siècles après, et dépeint des soldats délibérément surhumains. À ne pas prendre comme
description standard.

**Azincourt, 1415** : les Anglais combattent un temps puis se replient pour se reposer.

### 5.3 Données physiologiques dures

Étude de cas 2024 (analyse cinématique + lactate + fréquence cardiaque, combat médiéval sportif en
armure) :

| Mesure | Valeur |
|---|---|
| Format | 3 rounds de **90 s**, 45 s de repos |
| Combat effectif cumulé | **4 min 30** |
| FC moyenne en round | 170 bpm = **90 % de FCmax** |
| FC max atteinte | 193 bpm (au-delà de la FC max théorique du sujet) |
| Lactate : repos → fin R1 → R2 → R3 | 1,0 → 4,70 → 6,90 → **8,20 mmol/L** (seuil : 2,9) |
| Dégradation | Chute mesurable de la vitesse des frappes dès le round 3 ; posture qui se relève |

**À retenir : le combat en armure à pleine intensité est une activité de l'ordre de la minute et
demie, pas de l'heure.** Un homme peut y revenir plusieurs fois, mais dégradé à chaque fois, et il
récupère lentement.

### 5.4 Le désaccord scientifique — et pourquoi il compte pour nous

Deux modèles s'affrontent. **Ils sont d'accord sur le fait que les hommes ne frappent pas en
continu.** Ils divergent sur *l'amplitude* et la *durée* des pauses.

**Modèle « macro-pulse » (Sabin, Goldsworthy, Zhmodikov)**

- L'état par défaut d'une mêlée prolongée est un **face-à-face à distance de sécurité**, hors de
  portée d'arme : assez près pour s'injurier et s'échanger des projectiles, pas assez pour se
  toucher.
- Le contact arrive par **poussées locales et brèves**, déclenchées par les « vrais combattants » et
  les chefs subalternes. La bouffée s'arrête quand un camp a le dessous : ses hommes reculent en
  brandissant leurs armes pour dissuader la poursuite.
- Les lignes peuvent se séparer de plusieurs dizaines de mètres.
- Ce modèle explique bien : la durée, la faiblesse des pertes du vainqueur, le fait qu'une ligne
  puisse être « repoussée » de centaines de mètres sans rompre, et l'intérêt du système de relève
  par lignes.

**Modèle « micro-pulse seulement » (Devereaux)**

- Une fois au contact, les lignes **restent en contact** (à quelques mètres) ; elles sortent et
  rentrent constamment de la **mesure** (portée d'arme, 1–2 m) — un pas en avant, un pas en arrière,
  en accordéon.
- Les vrais désengagements sont rares, demandent un ordre explicite, et sont le plus souvent des
  déroutes.
- Arguments : le serment romain de ne pas quitter son *ordo* ; le fait que des unités entières
  **jettent leurs javelots** au moment du contact (absurde si l'on comptait se redésengager pour
  les relancer) ; le fait que les sources décrivent constamment des *poussées* mais presque jamais
  des *accalmies* ; à Zama, le seul vrai retrait général est **ordonné à la trompette** par Scipion.
- Devereaux note honnêtement que l'argument d'impossibilité physique de Sabin est avancé **sans
  données expérimentales**.

**Position de travail pour le simulateur.** Deux échelles de temps emboîtées :

| Niveau | Amplitude | Durée | Statut |
|---|---|---|---|
| **Micro-pulse** — entrée / sortie de mesure | 1–2 m | 1–5 s | Quasi certain. À implémenter en dur. |
| **Macro-lull** — les lignes se séparent | 10–30 m | 30 s – quelques minutes | Contesté. **Doit émerger** du modèle (fatigue + peur + perte des meneurs), pas être codé en dur. |

C'est un excellent test pour le simulateur : *si le macro-lull apparaît tout seul, le modèle a
capturé quelque chose de réel ; s'il faut le forcer, c'est qu'il manque une variable.*

---

## 6. Recul, repli partiel, retraite feinte

### 6.1 Reculer n'est pas rompre

Céder du terrain est **normal** et constitue le signe visible de qui a l'ascendant moral. C'est un
état continu, pas un état binaire.

Amplitudes attestées :

- Les lignes romaines se déplacent de **centaines de mètres** au cours d'un engagement.
- Les Helvètes reculent **d'un mille** après avoir eu le dessous, puis reprennent le combat depuis
  une position en hauteur.
- À Cannes, le centre punique passe de convexe à concave **sans rompre**.
- Même une phalange de piquiers peut **reculer face à l'ennemi** et ensuite l'emporter (Sellasie).

### 6.2 Le mécanisme

Chaque bouffée de corps-à-corps se termine par un camp qui recule d'un mètre ou deux. **Si c'est
toujours le même camp qui cède, l'accumulation de ces micro-reculs déplace la ligne** et finit par
avoir un effet à l'échelle de la bataille. Le « repoussement » n'est pas une poussée physique : c'est
une statistique de micro-décisions individuelles.

### 6.3 La condition de possibilité : le jeu derrière soi

Un homme ne peut se dérober que s'il y a de la place derrière lui. « Il y avait habituellement assez
de jeu dans les formations d'infanterie pour permettre aux hommes du premier rang de s'écarter de
leurs adversaires sans buter immédiatement sur l'homme de derrière. »

Quand ce jeu disparaît — troupes trop serrées, poussée de l'arrière, encerclement — les hommes ne
peuvent plus ni employer correctement leurs armes ni reculer d'un pas qui tourne mal.
**C'est précisément là que commence le massacre unilatéral.**

### 6.4 La retraite feinte

Hastings, 1066 : selon Guillaume de Poitiers et la tapisserie de Bayeux, des cavaliers normands
simulent la fuite ; des sections du mur de boucliers anglais rompent les rangs pour poursuivre ; les
Normands font demi-tour et les taillent en pièces. (Le débat historiographique porte sur le point de
savoir si le premier repli fut accidentel et si seuls les suivants furent délibérés.)

Deux enseignements pour le modèle, symétriques :

1. Un repli partiel est **une arme**, à condition de pouvoir se rallier et faire demi-tour — ce qui
   exige une cohésion élevée.
2. **Poursuivre un ennemi qui recule est la manière dont une ligne victorieuse se détruit elle-même.**

---

## 7. Comment une ligne casse, et où meurent les hommes

### 7.1 La rupture est discontinue

> « Ce type de face-à-face dynamique ponctué d'épisodes de corps-à-corps pouvait continuer un certain
> temps jusqu'à ce qu'un camp perde enfin sa capacité de résister, **rompant ainsi les liens de
> dissuasion mutuelle** et encourageant les troupes adverses à se ruer en avant et à commencer à
> tuer pour de bon, leur tension et leur peur rongeantes désormais libérées et converties en une
> orgie de soif de sang. »

Déclencheurs : brèche dans la ligne, choc psychologique (mort du chef), ou simple **accumulation**
de pertes et de fatigue. Le passage d'un état à l'autre n'est pas graduel.

À Zama, la première ligne carthaginoise s'effondre **parce que la seconde ne monte pas la soutenir** :
l'effondrement est psychologique, pas attritionnel. Les mercenaires refluent sur leur propre seconde
ligne, qui refuse de s'ouvrir, et se font massacrer par leurs employeurs.

### 7.2 L'asymétrie des pertes

| | Vainqueur | Vaincu |
|---|---|---|
| Batailles hoplitiques (Krentz) | ~5 % | ~14 % |
| Batailles romaines | ~5 % de morts | souvent > 50 % tués ou capturés |
| Consensus médiéval | 5–10 % | 10–30 %, parfois bien pire |
| Courtrai 1302 | ~100–300 morts flamands | ≥ 50 % de 2 500+ chevaliers français |
| Hastings 1066 | ~15 % | ~30 % |

**L'essentiel des morts survient après la rupture, dans la poursuite, par-derrière.**

### 7.3 L'archéologie le confirme

**Towton, 1461** (charnier de Towton Hall, découvert en 1996 ; 38 à 43 corps analysés)

- **113 blessures sur 28 crânes** — une moyenne de **4 blessures par tête**, très au-delà de ce qui
  était nécessaire pour tuer. Répartition : 73 par arme tranchante, 28 par arme contondante,
  12 perforantes.
- Seulement **43 blessures post-crâniennes** sur l'ensemble des corps. Le crâne concentre tout.
- **70 %** des grandes blessures crâniennes pénétrantes sont **frontales** : confrontation face à
  face — mais le nombre de coups par tête indique des hommes achevés alors qu'ils étaient déjà à
  terre ou sans défense.

**Visby, 1361** (Gotland ; 1 185 individus, fouilles Thordeman 1919–1929)

- Blessures concentrées sur les **bras, les jambes et les crânes** — le torse était protégé par la
  cotte de mailles et le bouclier.
- ~450 blessures par armes tranchantes, ~120 par armes perforantes.
- **Prédominance des jambes**, à l'inverse de Towton. On frappe les jambes d'un homme qui fuit, ou
  d'un homme qu'on domine.

Les deux profils diffèrent parce que les situations tactiques diffèrent : Towton = hommes d'armes en
armure achevés au corps-à-corps après la rupture ; Visby = milice locale rattrapée et abattue.
**Le profil de blessures est une signature du scénario de mort.** C'est un test possible du
simulateur : la distribution des coups qu'il produit doit ressembler à l'une ou l'autre selon le
scénario.

### 7.4 Se rendre

Comportement spécifiquement médiéval, et à part entière : **un chevalier vaut plus vivant.**

- Bouvines : Ferrand, « presque sans vie du fait de la longue durée du combat, **se rendit
  spécifiquement à Hugues de Maleveine et à son frère Jean** ». La reddition est adressée à un
  individu nommé : c'est un contrat, pas un abandon.
- Poitiers 1356 : le roi Jean II, son fils, 17 grands seigneurs, 13 comtes, 5 vicomtes et une
  centaine de chevaliers notables capturés. Rançon royale : trois millions d'écus.
- Azincourt 1415 : Henri V ordonne l'exécution des prisonniers ; **seuls les plus riches, les plus
  rançonnables, survivent.**

Pour le modèle : « se rendre » est une action dont la valeur dépend de **qui je suis** et de **qui
est en face**. Un homme du commun face à un homme du commun n'a pas cette option.

---

## 8. Le commandement après le contact

- **Il perd le contrôle.** À Bouvines, le combat s'engage à droite « le roi lui-même, à ce que je
  suppose, l'ignorant ».
- **Ce qui reste : la présence et la voix.** Guérin est là « non pas pour combattre, certes, mais
  pour encourager et inspirer les troupes ». Les porte-enseignes qui jettent leur enseigne vers
  l'ennemi pour forcer leurs camarades à avancer sont l'archétype de l'ordre médiéval au contact.
- **Ce qui se décide avant : le rangement.** Le vrai levier du chef est le tri des hommes et la
  disposition de la ligne, avant le premier choc.
- **La réserve.** Muret 1213 (Simon de Montfort) et Bouvines montrent des chefs conservant et
  engageant une réserve montée au bon moment.
- **La relève de ligne est rare et difficile.** Le système romain à trois lignes est inhabituel.
  Les armées médiévales, en général, **ne savent pas échanger leurs lignes**. À Azincourt la seconde
  bataille française s'entasse sur la première, sans moyen d'interpénétration — et c'est sa ruine.

---

## Sources

**Études modernes**

- Philip Sabin, « The Face of Roman Battle », *Journal of Roman Studies* 90 (2000), p. 1–17.
  [PDF](https://gwern.net/doc/history/2000-sabin.pdf) · [Cambridge Core](https://www.cambridge.org/core/journals/journal-of-roman-studies/article/abs/face-of-roman-battle/CC48A3F1CC4230C15D76CA4EE2D8EEA7)
- Adrian Goldsworthy, *The Roman Army at War, 100 BC – AD 200* (1996), ch. 4–6.
- Alexander Zhmodikov, « Roman Republican Heavy Infantrymen in Battle (IV–II centuries BC) »,
  *Historia* 49/1 (2000).
- Bret Devereaux, « Intermission: Battle Pulses », *A Collection of Unmitigated Pedantry*,
  18 déc. 2025 — [lien](https://acoup.blog/2025/12/18/intermission-battle-pulses/)
- Bret Devereaux, « Pre-Modern Armies for Worldbuilders, Part IVb: Cohesion », 24 juil. 2026 —
  [lien](https://acoup.blog/2026/07/24/collections-pre-modern-armies-for-worldbuilders-part-ivb-cohesion/)
- John Keegan, *The Face of Battle* (1976), chapitre sur Azincourt.
- Ardant du Picq, *Études sur le combat* (posth. 1880).
- Peter Krentz, « Casualties in Hoplite Battles », *GRBS* 26/1 (1985), p. 13–20.
- J. F. Verbruggen, *The Art of Warfare in Western Europe during the Middle Ages* (trad. angl. 1997).
- Sean McGlynn, « The Myths of Medieval Warfare », De Re Militari —
  [lien](https://deremilitari.org/2013/06/the-myths-of-medieval-warfare/)
- Anne Curry, *Agincourt: A New History* (2005) — révision des effectifs (≈ 12 000 Français contre
  7 000–9 000 Anglais).
- Clifford J. Rogers, « The Battle of Agincourt », in *The Hundred Years War (Part II)* (Brill, 2008).

**Sources primaires**

- Guillaume le Breton, *Gesta Philippi Augusti*, ch. 181–190 (Bouvines, 1214), trad. C. J. Rogers
  et al., De Re Militari —
  [lien](https://deremilitari.org/2025/01/battle-of-bouvines-1214-gesta-philipi-augusti/)
- Guillaume de Poitiers, *Gesta Guillelmi* (Hastings) ; tapisserie de Bayeux.
- Végèce, *De re militari*, III.9 ; Tite-Live ; Polybe ; César, *BG* / *BC* ; Appien, *BC* 3.68 ;
  Plutarque, *Aem.*
- Jean de Bueil, *Le Jouvencel* (v. 1466), éd. Craig Taylor, Boydell & Brewer, 2020.

**Archéologie**

- V. Fiorato, A. Boylston, C. Knüsel (dir.), *Blood Red Roses: The Archaeology of a Mass Grave from
  the Battle of Towton, A.D. 1461* (2000). Rapport ostéologique :
  [Towton Battlefield Society](https://towton.org.uk/wp-content/uploads/2022/05/osteological_analysis_towton_hall_and_towton_battlefield.pdf)
- Bengt Thordeman, *Armour from the Battle of Wisby, 1361* (1939) ; section blessures par
  B. E. Ingelmark.
- « Medieval Battle Injuries: What Archaeology Can Tell Us », Medievalists.net, mars 2024 —
  [lien](https://www.medievalists.net/2024/03/medieval-battle-injuries/)

**Physiologie et foules**

- « Kinematic and Physiological Analysis of Medieval Combat Sport Using Motion Analysis, Blood
  Lactate Measurement, and Heart Rate Monitoring: A Case Study », PMC11174425 —
  [lien](https://pmc.ncbi.nlm.nih.gov/articles/PMC11174425/)
- « Crowd collapses and crushes », synthèse des seuils de densité —
  [Wikipedia](https://en.wikipedia.org/wiki/Crowd_collapses_and_crushes)

**Organisation**

- Ordonnance de Charles VII, 26 mai 1445 (compagnies d'ordonnance) —
  [Herodote.net](https://www.herodote.net/26_mai_1445-evenement-14450526.php)
- Ordonnance d'Abbeville (1471) et suivantes, Charles le Téméraire — lances de 9 hommes,
  chambres de 6 lances, escadres de 4 chambres.
