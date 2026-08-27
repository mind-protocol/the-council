# L'identité d'une unité

## 1. Ce que c'est

Qui est dans ce groupe, de quel groupe il relève, et à quel rang il se tient dans
l'armée. Rien de ce qui bouge.

## 2. Ce qu'elle possède

- l'**identifiant** de l'unité, posé une fois, jamais réattribué ;
- la **liste de ses membres** : des identifiants d'hommes, déclarés, ajoutés et
  retirés par des faits explicites — l'homme est mort, l'homme a été versé
  ailleurs, l'homme a été détaché ;
- son **parent** : l'unité dont elle relève, et la place qu'elle y occupe ;
- son **rang** : vintaine, compagnie, bataille — l'échelon, pas l'effectif ;
- son **camp**, hérité du parent et non recalculé.

## 3. Ce qu'elle lit

- `10-socle` : la forme déclarée d'une unité, l'horloge pour dater les entrées et
  les sorties ;
- `40-combattant/identite` : le camp et le métier d'un homme, pour refuser une
  affectation incohérente.

Elle ne lit **ni le monde, ni la perception, ni les positions**.

## 4. Ce qu'elle produit

Trois réponses : de qui cette unité est faite, de qui elle relève, à quel rang.
Les autres modules de la couche — chef, forme, cohésion, allure, rupture,
détachement — s'y adossent, et le commandement s'en sert pour adresser un ordre.

## 5. Invariants

- **L'appartenance est déclarée, jamais déduite.** Aucun homme n'entre dans une
  unité parce qu'il se trouve à proximité de ses membres, ni n'en sort parce
  qu'il s'en est éloigné. Une sonde vérifie qu'aucune entrée ni sortie n'a d'autre
  cause qu'un fait nommé.
- **Un homme appartient à une unité et une seule.** Détaché, il y appartient
  toujours ; c'est son état qui change, pas son appartenance.
- Un mort reste membre jusqu'à ce qu'un fait l'en retire : sa liste n'est pas un
  compte de vivants.
- Le parent ne fait pas de cycle, et le rang d'une unité est strictement
  inférieur à celui de son parent.

## 6. Ce qu'elle ne fait pas

- Elle ne **regroupe rien par proximité**. Une masse d'hommes serrés n'est pas une
  unité, et une unité éparpillée reste une unité.
- Elle **ne compte pas les vivants**, ne mesure pas la dispersion, ne dit pas si
  le groupe tient : c'est la cohésion.
- Elle **ne désigne pas le chef** : elle fournit la liste sur laquelle un chef se
  choisit, et rien de plus.
- Elle ne porte **ni ordre, ni objectif, ni route, ni position d'ancre**. Une
  unité n'a pas d'ordre : ses hommes en ont un chacun.
- Elle ne redistribue pas ses membres pour rétablir un effectif.

## 7. Ce que l'ancien moteur faisait mal ici

L'unité portait ce qui ne lui appartenait pas : **l'ordre y vivait, et le chef
aussi**. Mesuré côté hommes : **0,0 % des combattants portaient un ordre reçu,
0,0 % un chef connu** — ils allaient les chercher sur le groupe au moment de s'en
servir.

Une unité était donc à la fois un registre d'appartenance et une mémoire
partagée que tous ses membres lisaient sans délai ni brouillard. Après réparation
— l'ordre et le chef rendus aux hommes —, **93,3 %** portaient un ordre et
**62,0 %** un chef connu, les 38 % restants étant à plus de 18 mètres de leur
chef et n'ayant donc pas pu le voir.

Ce que l'unité garde après cette réparation est exactement ce que dit cette
fiche : une liste, un parent, un rang. Tout ce qui ressemble à une connaissance
partagée doit être suspecté d'être un raccourci de brouillard.
