# Le roster — qui compose les corps, sous quel chef, avec quelle arme

> **Ce dossier explique. Il ne fait PAS autorité.**
> Les nombres vivent dans [`ecrans/modules/bataille/roster.js`](../../../ecrans/modules/bataille/roster.js),
> qui est ce que la page et le moteur lisent. Cette page-ci dit *pourquoi*.
>
> La distinction n'est pas bureaucratique, elle est payée comptant : `docs/bataille/`
> se déclarait « l'autorité pour les effectifs, les noms et les humeurs » pendant que
> `bataille2d.js` en tenait une copie à la main, et l'on a relevé **dix divergences**
> que personne n'avait vues ([`ecarts-code-dossier.md`](../ecarts-code-dossier.md)).
> Une prose ne peut pas faire autorité sur des nombres : elle ne s'exécute pas.

---

## Le principe : une unité se définit par la façon dont on peut lui parler

Pas par un effectif de tableau. Le moteur a **trois modes de transmission**, aux coûts
très différents, et chaque échelon en épouse exactement un.

| Échelon | Effectif | Chef | On lui parle par | Ce que ça coûte |
|---|---|---|---|---|
| **Vintaine** *(conroi)* | 20 | **vintenar**, à pied, dans le rang | la **voix** | rien — mais 20 hommes au plus, et il faut être là |
| **Centaine** *(chambre)* | 5 vintaines = 100 | **centenar**, **monté** | un **coureur** | un homme, du temps, et il peut ne pas arriver |
| **Corps** *(la « bataille »)* | 2 à 8 centaines, *ad hoc* | la **tête**, qui ne se bat pas | la **bannière** | gratuit et instantané — mais **trois codes** convenus d'avance |

Le centenar est **monté**, et ce n'est pas décoratif : la source anglaise précise qu'il
l'est *même quand ses hommes sont à pied, parce qu'il doit voir et se déplacer*.
C'est lui qui rend l'échelon 100 atteignable — le seul homme du corps qu'un coureur
peut trouver et rejoindre en un temps raisonnable.

**La conséquence tombe de la structure, sans qu'on ait à l'écrire.** Dès que la tête
veut autre chose que ses trois codes, il lui faut **un coureur par centaine** :

| | centaines | coureurs pour un ordre précis |
|---|---|---|
| Cole | 5 | 5 |
| Vantre | 4 | 4 |
| Cranche | 3 | 3 |
| les gueux | 4 | 4 |
| les bleusailles | 2 | 2 |
| **tout l'assaut** | **18** | **18** |

Dix-huit hommes détachés, dix-huit trajets, dix-huit occasions de tomber ou de se
tromper — pour **un seul** ordre qui ne rentre pas dans la bannière. C'est ça, la
friction du commandement, et elle ne demande aucune règle de plus.

---

## Le catalogue générique — ce qu'on peut aligner

`TYPES` dans [`roster.js`](../../../ecrans/modules/bataille/roster.js) liste les unités
disponibles, indépendamment de toute bataille. Les corps de la Gadoue, plus bas, ne sont
qu'**une composition parmi d'autres**.

| # | Type | Composition | Formation | Peuvent frapper | Simulé |
|---|---|---|---|---|---|
| 1 | Vintaine de pied | 1 vintenar · 5 lances · 9 épieux · 4 coutelas · 1 hache | ligne, 2 rangs | 50 % | oui |
| 2 | Vintaine de pique | 1 vintenar · 14 lances · 5 épieux | carré, 5 rangs | 40 % | oui |
| 3 | Vintaine de hache | 1 vintenar · 15 haches · 4 épieux | colonne, 5 rangs | 20 % | oui |
| 4 | Vintaine de trait | 1 vintenar · 16 archers · 3 épieux | ligne, 2 rangs | 20 % | **substitué** |
| 5 | Vintaine de levée | 1 vintenar · 15 coutelas · 4 épieux | nuée | 100 % | oui |
| 6 | Lance fournie | 1 homme d'armes · 1 coutilier · 3 archers · 1 piéton | aucune | 0 % | **substitué** |
| 7 | Conroi | 12 cavaliers | aucune | 0 % | **non** |

### « Peuvent frapper » est DÉRIVÉ, jamais déclaré

La première version portait un champ `rangsEngages` écrit à la main, et il a menti
immédiatement : une ligne sur deux rangs annonçait « 100 % engagés ». Le nombre de rangs
qui touchent n'est pas une propriété de la formation, **c'est une propriété du fer** que
tient l'homme, à la profondeur où il se trouve.

Un homme au rang *r* est à *r* × 1,0 m derrière le front, et il touche si son allonge
dépasse encore la distance de contact (1,40 m) une fois ce recul retranché :

- **lance** 2,80 − 1,00 = 1,80 → elle frappe **du deuxième rang** ;
- **épieu** 2,20 − 1,00 = 1,20 → **non** ;
- rien ne frappe du troisième rang.

C'est ce qui rend la figure intéressante plutôt que décorative. La vintaine de trait le
montre crûment : ses seize archers au coutelas (0,90 m) ne touchent **rien du tout**, même
au premier rang — 20 % d'engagés, portés par le vintenar et les trois piétons. La
substitution avoue sa vraie valeur au corps-à-corps, ce qu'un tableau d'effectifs aurait
caché.

### Le cheval est inscrit et inutilisable

Le conroi porte `simule: "non"`. Le moteur n'a ni monture, ni élan, ni choc : une unité
dont *rien* n'est simulé — pas même l'arme — promet plus qu'une substitution ne peut
tenir. On l'inscrit **pour que son absence se voie**, et on ne s'en sert pas.

---

## Les échelons — le moteur les avait déjà, sans les nommer

`bataille2d.js` porte `PAR_ESC = 20` et `ESC_PAR_AILE = 5`, soit exactement 20 et 100.
**On ne change donc aucune structure** : on nomme ce qui était anonyme, et l'on attache
à chaque échelon le mode de transmission qui lui revient.

**La vintaine** est l'échelle où vit la cohésion. La science militaire moderne distingue
le *moral* — l'attachement à la cause, qui amène l'homme sur le champ — de la *cohésion*
— l'attachement aux camarades, qui l'y maintient. La seconde se fabrique en face-à-face,
dans un petit groupe. Chaque homme a un chef immédiat et une poignée de voisins qu'il
connaît, et c'est tout. **C'est elle qui rompt d'un bloc.**

**Le corps est *ad hoc*** : sa taille dépend du besoin, pas d'un tableau d'effectifs.
Et sa tête **perd le contrôle au contact** — à Bouvines, le combat s'engage à droite
« le roi lui-même, à ce que je suppose, l'ignorant ». Ce qui lui reste est sa présence,
sa voix, et la réserve qu'elle a gardée.

---

## Les métiers, et non des uniformes

C'est ici qu'on s'écarte franchement de la série. Un régiment de deux cents hommes
identiques n'existe pas :

- **lance fournie** (France, ordonnance de 1445) : **6 hommes de 4 métiers** — 1 homme
  d'armes, 1 coutilier, 1 page, 3 archers ;
- **lance bourguignonne** (Abbeville, 1471) : **9 hommes de 6 métiers**.

**Le mélange EST l'unité.** Une vintaine type fait donc *1 vintenar · 5 lances ·
9 épieux · 3 coutelas · 1 archer · 1 hache* — et chaque corps a sa **recette**, pas son
uniforme.

| Métier | Arme | Allonge | Ce qu'il fait dans le rang |
|---|---|---|---|
| Homme d'armes | lance | 2,80 m | le premier rang — il **touche le premier** |
| Piéton | épieu | 2,20 m | le gros du rang, derrière la pointe |
| Coutilier | coutelas | 0,90 m | flancs, poursuite, pillage — il doit entrer sous la pointe |
| Hachier | hache | 1,50 m | sur ce qui doit céder ; ouvre un homme et reste découvert |
| Vintenar | épée + bouclier | 1,40 m | la meilleure garde de la table — il doit survivre **et** être vu |

### Ce que la recette remplace

Le dessin des cinq corps cesse d'être un adjectif et devient **mécanique** :

- **Cranche « le ferme »** tient parce qu'il a **huit lances** par vintaine au premier rang ;
- **les bleusailles** ne tiennent pas parce qu'ils n'en ont **aucune**, et dix coutelas ;
- **Vantre** vaut double contre le verrou parce qu'il a **quatre haches** par vintaine —
  et non parce qu'un coefficient le dit.

On ne leur câble aucun malus. La composition suffit, et elle se voit à l'écran.

---

## Les substitutions — écrites, pas subies

**Le moteur n'a aucun combat à distance.** Archers et arbalétriers — qui font la moitié
d'une lance fournie — ne peuvent pas exister aujourd'hui.

On ne les efface pas pour autant : **un roster amputé en silence est un roster qu'on
croira complet.** Ils sont dans le fichier, avec l'arme de remplacement qu'ils portent
en attendant et un champ `substitut` qui dit ce qu'ils sont vraiment.

| Métier | Porte, en attendant | `substitut` |
|---|---|---|
| Archer | coutelas | `arc` |
| Arbalétrier | coutelas | `arbalete` |

Le jour où le tir existera, **on bascule ces lignes-là et rien d'autre.**

Une remarque au passage : la substitution rend un effet juste *par accident*. Un archer
au corps-à-corps tire effectivement son coutelas, et une troupe qui en est pleine ne
tient pas un seuil — ce qui est exactement ce que les gueux et les bleusailles doivent
faire. On s'en contente, en sachant que c'est un accident heureux et non un modèle.

---

## Les vintaines en sous-effectif

Vantre fait 350 hommes, soit **dix-sept vintaines pleines et dix hommes qui restent**.
Arrondir à dix-huit fabriquerait dix hommes qui n'existent pas ; jeter le reste en
perdrait dix. Une unité est presque toujours en sous-effectif : on garde donc le
reliquat comme une **vintaine incomplète, avec son vintenar quand même** — un chef à
neuf hommes reste un chef, et c'est justement le genre d'unité qui casse en premier.

Vérifié : l'assemblage rend **1 700 + 800 = 2 500**, au nombre près, ce qui est
exactement le dossier.

---

## Ce qui reste à coder

Le squelette est là ; trois choses manquent au moteur :

1. **Le centenar monté n'existe pas.** Les capitaines d'aile sont anonymes et à pied.
   C'est lui qui porte tout l'argument de la transmission — sans lui, l'échelon 100
   est une abstraction.
2. **Les vingt-quatre meneurs nommés** du dossier ne sont nulle part. `chef-tombe` se
   déclenche sur un capitaine anonyme (`bataille2d.js`, `if (o.nom || o.capitaine || o.tete)`),
   alors que la règle du README dit « seulement sur un chef nommé ».
3. **Le mélange d'armes se tire par corps, pas par rôle.** Tant que c'est le cas, les
   recettes ci-dessus sont une intention et non un fait de la simulation.

---

## Sources

Tout ce qui est chiffré ici vient de
[`docs/recherche/dynamiques-du-combat-medieval.md`](../../recherche/dynamiques-du-combat-medieval.md)
— § 1 pour les échelons, § 2.3 pour la ligne comme résultat, § 8 pour le commandement
après le contact. Les effectifs des corps viennent de [`../rouges.md`](../rouges.md) et
[`../bleus.md`](../bleus.md).
