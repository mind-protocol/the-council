# L'identité d'un combattant

## 1. Ce que c'est

Ce qui distingue un homme des deux mille autres et **ne change pas de toute la
bataille** : son camp, son métier, son arme, sa trempe, ses gestes acquis.

## 2. Ce qu'il possède

- l'**identifiant stable** de l'homme, posé une fois, jamais réattribué ;
- son **camp** et son **métier** (piquier, archer, cavalier, servant, tambour) ;
- son **arme** et sa portée d'emploi, au sens de ce qu'il sait en faire ;
- sa **trempe** : ce qu'il supporte avant de céder, ce qu'il faut pour le
  décider, sa main dominante, son biais dans un rang ;
- ses **acquis** : le répertoire fermé de gestes que ce métier-là lui a mis dans
  les jambes et dans les bras.

Personne d'autre n'écrit ces champs. Ils sont posés à la naissance de l'homme et
relus jusqu'à sa mort.

## 3. Ce qu'il lit

`10-socle` seulement : la forme déclarée d'un homme, et la dérivation stable qui
transforme un identifiant en valeurs. Rien de `20` ni de `30` — l'identité est
antérieure au monde.

## 4. Ce qu'il produit

Une fiche en lecture seule, répondant à trois questions et pas davantage : de
quel camp est cet homme, de quel métier, et ce qu'il sait faire. Les quatre
couches, l'arbitre et la mémoire s'y adossent sans jamais la modifier.

## 5. Invariants

- **Aucun tirage.** Tout ce qui varie d'un homme à l'autre est *dérivé* de son
  identifiant, jamais tiré. Deux cuissons de la même graine donnent les mêmes
  hommes ; ajouter un homme ne décale pas les autres.
- Un identifiant, un homme, pour toute la bataille — y compris après sa mort.
- La fiche est **immuable** : une sonde qui compare l'identité au premier pas et
  au dernier doit trouver zéro écart.
- Tout champ d'un homme appartient soit à cette fiche (immuable), soit à une
  couche, soit à la mémoire, soit au monde. **Aucune quatrième catégorie.**

## 6. Ce qu'il ne fait pas

- Il ne porte **aucun état** : ni fatigue, ni peur, ni blessure, ni moral, ni
  position, ni allure. Tout ce qui bouge appartient à un autre propriétaire.
- Il ne porte **pas l'appartenance à une unité** : ça vit en `50-unite`, et
  l'homme n'a pas le droit de le savoir depuis ici.
- Il ne porte **ni l'ordre reçu, ni le chef** : c'est la mémoire.
- Il ne décide rien, ne compare rien, n'a pas d'avis sur un ennemi.
- Il n'offre aucun sac à champs libres. Un besoin nouveau ouvre soit un champ
  déclaré ici, soit un module ; jamais une clef ajoutée en passant.

## 7. Ce que l'ancien moteur faisait mal ici

Il n'y avait pas d'identité. Un homme portait **174 champs distincts, écrits
depuis 229 endroits**, et **aucun endroit unique ne disait ce qu'un homme
possède**. Il n'existait donc aucun moyen de savoir si un champ était constant,
courant, ou mort : la seule façon de l'apprendre était de relire les 229
endroits.

Deux conséquences payées comptant : une comparaison portant sur un nom de champ
qui n'existait pas est passée inaperçue, et une donnée censée changer est restée
figée toute la bataille sans qu'aucun compte le montre.

La séparation « immuable ici, courant ailleurs » est la première marche : sans
elle, aucune des fiches suivantes ne peut prétendre à un écrivain unique.
