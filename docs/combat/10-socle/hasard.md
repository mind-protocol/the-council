# `10-socle/hasard` — l'urne

## Ce que c'est

La source unique de tout aléa de la simulation.

## Ce qu'il possède

L'état interne du générateur, et lui seul. Personne ne le lit, personne ne le
recopie, personne n'en fabrique un second.

## Ce qu'il lit

Rien. C'est la couche zéro.

## Ce qu'il produit

- un tirage entre 0 et 1 ;
- la pose d'une graine, et la garantie qu'une même graine rejoue la même suite ;
- un compte des tirages consommés, pour l'observation.

## Invariants

- **Une seule urne.** Aucun module ne tire ailleurs, et surtout pas via un
  générateur de plateforme.
- **La suite est reproductible.** Même graine, même suite, dans n'importe quel
  environnement — pas seulement dans la session courante.
- **L'ordre des tirages fait partie du résultat.** Ajouter, retirer ou déplacer
  un tirage rebat tout ce qui suit. Un changement qui se croit neutre mais
  déplace un tirage ne l'est pas.
- Le compte des tirages est une mesure comme une autre : deux cuissons de la
  même condition doivent en consommer exactement autant.

## Ce qu'il ne fait pas

- Il ne distribue pas de lois : pas de normale, pas de tirage pondéré, pas de
  mélange de liste. Ceux qui en ont besoin les composent chez eux, à partir du
  tirage nu, et restent responsables de l'ordre dans lequel ils consomment.
- Il ne connaît aucune notion de bataille, d'homme ni de temps.
- Il ne se ressème pas tout seul en cours de partie.

## Ce que l'ancien moteur faisait mal ici

Rien de mesuré à sa charge : l'urne unique existait, elle se ressemait
correctement, et deux cuissons d'une même condition rendaient la même bataille à
chaque vérification.

Le piège qu'il faut retenir n'est pas dans l'urne mais **autour** d'elle. Ce qui
peut dériver d'une identité stable — le biais d'un homme dans son rang, sa main
dominante, sa trempe — ne doit pas consommer l'urne : dérivé de l'identifiant, il
donne de la variété à deux mille corps sans rendre la nuit irreproductible.
L'ancien moteur le faisait déjà, et c'est le bon geste.

Le second piège est un ordre de chargement : l'urne doit être posée **avant tout
ce qui tire**. Une vérification l'exigeait explicitement, ce qui veut dire que
quelqu'un s'y était déjà brûlé.
