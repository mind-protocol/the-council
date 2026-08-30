# Objectif

## 1. Ce que c'est

Ce que l'armée cherche à obtenir cette nuit-là : un ou plusieurs buts finaux
pondérés, ce qu'on accepte d'y perdre, le temps dont on dispose, et les endroits
dont la possession compte.

## 2. Ce qu'il possède

- **Les buts finaux**, chacun avec un **poids**. Il y en a plusieurs, et ils se
  contredisent : tenir la porte, prendre le pont, sauver le seigneur. Le poids
  dit lequel l'emporte quand il faut choisir, et c'est la seule chose qui rende
  un arbitrage possible.
- **Les pertes acceptables**, déclarées avant le premier pas et par but : ce
  qu'on est prêt à dépenser pour l'obtenir. Une armée sans plafond de pertes ne
  renonce jamais.
- **Le temps disponible** : l'horizon au-delà duquel le but ne vaut plus rien —
  la marée, le jour qui se lève, la colonne de secours qu'on sait en route.
- **Les zones dont la possession compte**, avec leur poids : ce qu'il faut tenir,
  ce qu'il faut prendre, ce qu'on peut abandonner sans que le but tombe.
- **L'état de chaque but** : poursuivi, atteint, abandonné, avec motif et instant.

## 3. Ce qu'il lit

Le socle, pour la mesure du temps de bataille et les identités. Le monde, pour
savoir de quoi une zone est faite. Le commandement, pour l'état des croyances de
ses commandants — **et seulement celles-là**.

Il ne lit rien au-dessus de lui, et il ne lit pas l'état réel du camp adverse :
un général est aveugle comme les autres, et ses buts sont pesés sur ce que ses
commandants lui ont rapporté.

## 4. Ce qu'il produit

- **Que vaut cette situation ?** — l'avancement de chaque but, sa valeur restante
  compte tenu du temps consommé et des pertes déjà payées.
- **Quel but l'emporte ici ?** — l'arbitrage pondéré, avec son motif, quand deux
  buts réclament la même force.
- **Un signalement** quand un but est atteint, devient impossible, ou change de
  rang. Il ne sait pas qui écoute.

## 5. Invariants

- Tout but a un poids, un plafond de pertes et un horizon. Un but sans les trois
  est un souhait, et la sonde le refuse.
- Un but atteint ou abandonné ne redevient jamais poursuivi de lui-même ; il
  faut un nouveau but, daté.
- La somme des pertes engagées par les missions ne dépasse pas le plafond du but
  qu'elles servent, ou l'objectif l'a explicitement relevé et l'a tracé.
- Toute zone qui compte est nommée et pesée ; une zone tenue « parce qu'on y est »
  n'est pas un objectif.

## 6. Ce qu'il ne fait pas

- **Il ne donne aucun ordre.** Un but n'est pas une instruction : il ne nomme
  personne, ne dit aucun chemin, ne fixe aucune formation. Ce qui atterrit sur
  quelqu'un est une mission, et c'est un autre module.
- **Il ne répartit pas les forces.** Savoir combien d'hommes vont où est
  l'affaire de l'allocation ; l'objectif dit seulement ce que ça vaut.
- **Il ne connaît pas les unités.** Ni leurs effectifs, ni leur cohésion, ni leur
  position. S'il lui faut ces choses pour peser, il les reçoit du commandement
  sous forme de croyances, avec leur âge.
- **Il ne se met pas à jour tout seul sur le réel.** Une zone perdue reste tenue
  dans ses comptes tant qu'aucun rapport ne l'a dit. C'est le brouillard, et il
  vaut au sommet comme en bas.
- **Il ne planifie pas dans le temps.** Aucune séquence d'étapes, aucun « d'abord
  ceci puis cela » : l'ordonnancement naît des missions et de leurs conditions.

## 7. Ce que l'ancien moteur faisait mal ici

**Il n'existait aucun niveau « général ».** Aucun objectif stratégique n'était
déclaré nulle part : ni but pondéré, ni plafond de pertes, ni horizon, ni zone
dont la possession compte. Tous les ordres venaient d'un scénario écrit à
l'avance, donc rien ne pouvait être réévalué en cours de nuit — un but devenu
inutile restait poursuivi jusqu'au bout du script.

Faute d'objectif, aucune des grandeurs de cette fiche n'a jamais été mesurée sur
le moteur précédent : il n'y avait pas de chiffre à relever, seulement un
scénario à dérouler.
