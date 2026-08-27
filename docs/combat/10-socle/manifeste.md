# `10-socle/manifeste` — la seule liste

## Ce que c'est

La déclaration unique de tous les modules du moteur : leur couche, leur ordre de
chargement, ce que chacun reçoit, et ce que chacun est censé rendre.

## Ce qu'il possède

La liste, et les raisons de son ordre. Le motif de chaque rang est écrit à côté
du rang — c'est ce qui empêche le suivant de déplacer une ligne « pour ranger ».

## Ce qu'il lit

Rien. Il ne charge rien non plus : il dit quoi, dans quel ordre, et pour qui.
Chaque consommateur charge à sa façon.

## Ce qu'il produit

- la liste ordonnée des modules d'un **ensemble** donné — la simulation nue, la
  page de scène, le jeu ;
- ce que chaque module est censé poser, pour qu'on puisse vérifier une chaîne
  montée ;
- la liste de ce qui **manque**, nommément, plutôt qu'une erreur au premier appel.

## Invariants

- **Une seule liste.** Tout consommateur la lit : le jeu, la page d'épreuves, les
  bancs, les outils de mesure. Aucune exception, jamais une liste de secours.
- **Un ensemble contient toujours la simulation nue, dans le même ordre.** On
  n'ajoute pas un fichier à un ensemble : on le déclare une fois avec les
  ensembles auxquels il appartient.
- **Ce qui manque se nomme.** Une chaîne incomplète doit dire quel morceau
  manque, pas tomber trois couches plus bas sur une valeur indéfinie.
- Le manifeste porte la **couche** de chaque module : c'est lui qui rend
  vérifiable la règle de dépendance.

## Ce qu'il ne fait pas

- Il ne résout aucune dépendance : c'est un ordre, pas un graphe. Écrire un
  résolveur ici serait remplacer une règle lisible par une mécanique qui a l'air
  maligne.
- Il ne charge pas, ne met pas en cache, ne surveille pas.
- Il ne connaît aucune notion de bataille.

## Ce que l'ancien moteur faisait mal ici

**Il y avait huit listes.** Le four en tenait une, la page de jeu une autre, la
page d'épreuves une troisième, les outils d'analyse les suivantes.

Deux avaient déjà dérivé sans que personne le sache. Une couche de délibération
manquait au four : elle était donc chargée par le jeu, et **aucune mesure ne la
voyait tourner**. Un module de composition manquait au jeu alors que le moteur le
lisait : le jeu prenait un chemin dégradé en silence. Et un même module n'était
pas au même rang dans deux listes.

Une liste qui diverge ne fait pas tomber la page. Elle fabrique une chaîne que
personne ne mesure, et l'on découvre six semaines plus tard que le banc jugeait
un autre moteur que celui qu'on regarde.

Le second piège est jumeau, et il a mordu le même jour : **ce qui est servi à un
navigateur est mis en cache par son URL.** Le code changeait, l'URL non, et le
joueur voyait l'ancien moteur pendant que les mesures en ligne de commande —
qui lisent le disque — voyaient le nouveau. Il y avait de surcroît deux
empreintes en série : bouger la seconde sans la première ne servait à rien.
L'empreinte doit **dériver du contenu**, jamais être tenue à la main.
