# `10-socle/identite` — les identifiants

## Ce que c'est

L'attribution d'identifiants stables aux acteurs — hommes, unités, ordres, faits,
messages — et la dérivation de valeurs reproductibles à partir de ceux-ci.

## Ce qu'il possède

Les compteurs, et la fonction qui dérive un nombre d'un identifiant.

## Ce qu'il lit

Rien.

## Ce qu'il produit

- un identifiant neuf pour une famille donnée ;
- une valeur **dérivée** d'un identifiant : toujours la même pour le même
  identifiant, sans consommer l'urne.

## Invariants

- **Un identifiant est stable pour toute la durée d'une bataille**, y compris
  après une mort : une trace, une marque ou un journal doivent pouvoir désigner
  un homme qui n'est plus là.
- **Il est reproductible.** Rejouer la même condition rend les mêmes
  identifiants, dans le même ordre. Sans ça, aucune trace ne se compare d'une
  cuisson à l'autre.
- **Une dérivation ne consomme pas l'urne.** C'est ce qui permet de donner à deux
  mille corps une variété individuelle sans rendre la nuit irreproductible.
- Un identifiant ne porte aucun sens : ni le camp, ni le rang, ni l'ordre
  d'arrivée. Ce qui a un sens se lit dans les données, pas dans la clef.

## Ce qu'il ne fait pas

- Il ne tient aucun registre des acteurs vivants : il attribue, il ne collectionne
  pas.
- Il ne fabrique pas de clef composite « camp:rang:numéro ». Fabriquer une clef
  de texte des centaines de milliers de fois par image est une dépense pure —
  une leçon déjà payée ailleurs dans ce dépôt, où le même geste coûtait neuf
  secondes par image.
- Il ne réutilise jamais un identifiant libéré.

## Ce que l'ancien moteur faisait mal ici

Rien de mesuré à sa charge sur le principe : les identifiants étaient stables
pendant un rejeu, et les biais individuels d'un homme — sa place dans son rang,
sa main dominante — étaient bien dérivés de son identifiant sans toucher à
l'urne. C'est le bon geste, et il est repris tel quel.

Ce qui manquait est ailleurs, et c'est le sujet de la fiche voisine sur les
formes : un identifiant stable ne sert à rien si l'objet qu'il désigne n'a pas de
forme déclarée. Un homme portait **174 champs distincts, écrits depuis 229
endroits**, et aucun endroit unique ne disait ce qu'un homme possède.
