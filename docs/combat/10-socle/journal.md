# `10-socle/journal` — ce qui s'est passé, et pourquoi

## Ce que c'est

La mémoire de session des événements et des décisions. C'est là que se déposent
les traces que l'observation relit.

## Ce qu'il possède

Deux anneaux bornés — les événements et les décisions — et, à part, **la dernière
décision de chaque acteur**, quel que soit son âge.

## Ce qu'il lit

L'instant courant, pour dater. Rien d'autre.

## Ce qu'il produit

- l'inscription d'un **événement** : un message livré, une croyance qui bouge, un
  franchissement refusé, une forme non respectée. Court, fréquent, sans
  délibération derrière ;
- l'inscription d'une **décision**, au format déclaré dans les formes ;
- une lecture filtrée : par acteur, par tranche de temps, par genre, par option
  retenue ou écartée ;
- la liste des **réexamens manqués** — un acteur dont l'échéance est passée sans
  qu'il ait redécidé.

## Invariants

- **Les deux sortes ne se mélangent pas.** Un événement n'a pas d'auteur qui
  délibère ; une décision, si. Les confondre rend le filtrage inutilisable.
- **L'anneau est borné, et c'est la condition pour le laisser allumé.** Un
  journal qui fait tomber l'onglet est un journal qu'on éteint, et un journal
  éteint ne sert jamais le jour où il faudrait.
- **La dernière décision d'un acteur ne se perd jamais**, même poussée hors de
  l'anneau par le bavardage des autres. Sans ça, « que croyait-il » n'a pas de
  réponse au moment où on la pose.
- **On garde prioritairement la fin.** Ce qui explique une mauvaise décision est
  ce qui la précède de peu, pas l'ouverture de la bataille.
- Il n'écrit rien sur un disque. C'est de la mémoire de session.

## Ce qu'il ne fait pas

- Il ne juge pas ce qu'on lui donne : il n'écarte pas une trace mal formée, sinon
  il perdrait précisément celle qu'on aurait voulu lire.
- Il ne décide pas ce qui mérite d'être écrit. Celui qui signale décide.
- Il ne rend rien lisible pour un humain : la mise en forme appartient à
  l'observation.
- **Personne, dans la simulation, ne le connaît.** Un module signale ; le câblage
  se fait à la construction. Sinon la règle de dépendance tombe.

## Ce que l'ancien moteur faisait mal ici

Un journal de décision a été écrit, avec ses anneaux, son filtre à six critères
et sa liste des réexamens manqués. **Rien ne lui a jamais écrit.**

Pendant ce temps, la trace réellement affichée à l'écran était posée depuis
**cinquante-six endroits**, dont quarante-six nommaient la branche de code qui
venait de bouger l'homme plutôt que ce qui le conduisait. Il y avait donc deux
récits du même homme au même instant, et l'écran lisait le mauvais.

La leçon est de câblage, pas de conception : **un journal qui existe et que
personne n'alimente vaut exactement zéro**, et la seule façon de s'en apercevoir
est qu'une sonde compte ce qu'il reçoit.
