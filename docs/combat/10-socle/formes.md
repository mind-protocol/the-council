# `10-socle/formes` — ce qu'un objet échangé contient

## Ce que c'est

La déclaration, en un seul endroit, de la forme de chaque objet qui traverse une
frontière de module : un fait, un ordre, un message, une mission, une intention
de geste, une trace de décision — et la forme des entités qui ont une identité :
un homme, une unité.

## Ce qu'il possède

Les formes elles-mêmes : la liste des champs, ce que chacun veut dire, lesquels
sont obligatoires, et le vocabulaire fermé des champs qui en ont un.

## Ce qu'il lit

Rien.

## Ce qu'il produit

- de quoi **construire** un objet d'une forme donnée, avec ses valeurs par défaut ;
- de quoi **vérifier** qu'un objet respecte sa forme, en rendant la liste de ce
  qui cloche — jamais un simple oui ou non ;
- une **version** portée par chaque objet, pour qu'une marque exportée hier se
  relise demain.

## Invariants

- **Une forme est déclarée ici et nulle part ailleurs.** Un module qui ajoute un
  champ à un objet échangé change la forme, donc ce fichier — pas discrètement,
  chez lui.
- **La vérification mord pendant le développement et les mesures ; elle note et
  laisse passer en partie.** Une bataille ne s'arrête pas pour un champ vide, mais
  le défaut se lit dans le journal au lieu de se perdre.
- **Un vocabulaire fermé reste petit.** Sept genres de geste, trois formes de
  mission, cinq sources de fait. La précision vient des compléments, pas du
  nombre de mots.
- Certaines vérifications sont des **interdits d'architecture** et pas des
  contrôles de type : un ordre qui contient des positions individuelles est
  refusé, parce que ce n'est plus un ordre mais une télécommande.

## Ce qu'il ne fait pas

- Il ne stocke aucun objet : il dit leur forme, il ne les collectionne pas.
- Il ne convertit pas, ne migre pas, ne répare pas un objet mal formé.
- Il ne connaît ni bataille, ni acteur, ni règle de jeu.

## Ce que l'ancien moteur faisait mal ici

Le module de formes **existait** — construction, vérification et version pour six
objets échangés — et **rien ne l'utilisait**. Il a été écrit, puis posé sur
l'étagère, et le code a continué de fabriquer ses objets à la main.

Ce que ça a coûté, mesuré : un champ de fraîcheur d'ordre a été comparé sous un
nom qui n'existait pas, si bien qu'on comparait deux valeurs indéfinies. Le
compte avait l'air juste — **93 % des hommes portaient un ordre** — mais c'était
toujours le même ordre, jamais mis à jour. Une forme déclarée aurait attrapé ça à
l'écriture.

Et plus largement : un homme portait **174 champs écrits depuis 229 endroits**,
sans aucun endroit disant ce qu'un homme possède. Un module de décision produisait
un champ que personne ne lisait, et il a vécu ainsi indéfiniment — un objet
anonyme ne signale jamais ses membres morts.
