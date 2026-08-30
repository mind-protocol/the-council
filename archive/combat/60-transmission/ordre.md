# Ordre

## 1. Ce que c'est

Un résultat attendu de quelqu'un, borné par des contraintes — jamais un itinéraire
ni une liste de coordonnées.

## 2. Ce qu'il possède

- **La forme d'un ordre**, déclarée en un seul endroit : un verbe, un objet, des
  contraintes, une échéance, un émetteur, un destinataire, une date d'émission.
- **Le vocabulaire des verbes**, petit et clos : tenir, prendre, gagner, suivre,
  couvrir, rompre le contact, se joindre à, attendre. On n'ajoute pas un verbe
  pour un cas particulier ; on ajoute un complément.
- **La précision par compléments** : l'objet (un lieu, un corps, une direction),
  la contrainte (jusqu'à telle heure, sans franchir telle limite, sans engager),
  l'échéance, et ce qu'il faut faire si l'objet a disparu.
- **Le cycle de vie d'un ordre**, et lui seul en écrit l'état : *émis* (rédigé,
  pas encore parti), *porté* (confié à un canal), *reçu* (le destinataire l'a
  compris), *remplacé* (un ordre plus récent du même émetteur le couvre),
  *périmé* (son échéance est passée), *impossible* (le destinataire constate que
  l'objet n'existe plus ou ne peut pas être atteint).
- **La règle de préséance** : entre deux ordres reçus, c'est la date d'émission
  qui tranche, jamais l'ordre d'arrivée.

## 3. Ce qu'il lit

Du socle : identité stable, horloge, mesures. Du monde : les identités de lieux
et de seuils, pour que l'objet d'un ordre désigne quelque chose qui existe. De
l'unité : l'identité d'un groupe et son chef courant, pour savoir à qui un ordre
s'adresse.

Il ne lit rien de 70 ni de 80. **Un ordre ne connaît pas le raisonnement qui l'a
produit** — sinon la transmission dépendrait du commandement.

## 4. Ce qu'il produit

- **Un ordre rédigé**, ou refusé : un verbe hors vocabulaire ou un objet
  inexistant ne devient pas un ordre.
- **L'ordre courant d'un destinataire** : celui qui fait foi maintenant.
- **La comparaison de deux ordres** : lequel prime, et si le second remplace ou
  seulement complète.

## 5. Invariants

- Un destinataire a **au plus un ordre courant**. Les autres sont remplacés,
  périmés ou impossibles, jamais en attente silencieuse.
- Aucun ordre ne contient de trajectoire. Une sonde extérieure vérifie qu'aucun
  ordre ne porte de suite de points.
- Tout passage d'état est daté et gardé.
- Un ordre *impossible* remonte à son émetteur comme un fait.

## 6. Ce qu'il ne fait pas

- **Il ne décide rien** : ni le verbe, ni le destinataire, ni le moment. Un
  autre décide ; lui rédige et tient l'état.
- **Il ne transporte pas.** Passer de *émis* à *porté* est le travail du canal ;
  l'ordre en enregistre le résultat.
- **Il n'exécute pas** : ce que l'unité en fait appartient à la couche 50.
- **Il ne juge pas de la faisabilité.** Seul le destinataire peut déclarer
  *impossible*.
- **Il ne se réécrit pas pour arranger la scène.** Un ordre mal choisi tient
  jusqu'à ce qu'un autre le remplace.

## 7. Ce que l'ancien moteur faisait mal ici

L'ordre existait, mais **rien à l'intérieur du moteur n'en produisait**. Les cinq
endroits qui posaient un ordre le recevaient tous de l'extérieur — un scénario,
une interface. Il n'existait aucun chemin de code par lequel un ordre naisse d'un
renseignement.

Mesuré sur une bataille entière : les ordres d'unité **ne changeaient que deux
fois**, aux instants exacts où le scénario les posait, et l'on ne comptait **qu'un
seul changement d'ordre littéral** après l'ouverture. Le cycle de vie décrit ici
n'avait jamais lieu.

Le cas le plus instructif est celui de l'unité à qui l'on disait « marchez sur
cette porte » : elle a **gardé cet ordre inchangé du début à la fin, et reculé
quand même**. Ce n'est pas la décision qui a failli, c'est le mouvement — et l'on
ne répare pas un défaut de mouvement en réécrivant l'ordre.
