# 🧠 Brains / Commandant — ⏸️ STUB (feuille de route)

## Intention

L'intelligence de commandement, SANS forêt de if/else : le commandant pense
dans un **vocabulaire de manœuvres** (le livre, en donnée —
[doctrine/manoeuvres/](../../doctrine/manoeuvres/CLAUDE.md)) et un **arbitre
générique unique** choisit. Ajouter de l'intelligence tactique = ajouter une
entrée au livre, jamais une branche à l'arbitre.

Le commandement est un **PROCESSUS PARALLÈLE, pas un état du soldat** : le
commandant reste un homme (sa machine soldat garde son corps, sa peur, son
tempo ~0,5 Hz) ; le rôle d'état-major tourne à côté, au tempo du commandement
(~0,1 Hz + déclencheur de SAILLANCE : un fait de situation qui bascule
brutalement force une délibération immédiate), et ne produit que des PAROLES.

## Les cinq étages (chacun produit des choses NOMMÉES en français)

1. **Croyances** — la carte de bataille crue (tas formes/orientations,
   couverture, posture). Déjà construite.
2. **Déductions** (`estimation.js`) — l'appréciation de situation : des faits
   dérivés nommés, purs sur la Représentation (`flancGaucheEnnemiOuvert`,
   `rapportEffectifs`, `ennemiLocalise`, `partInconnueDeLaZone`…).
   Un fait déduit de croyances périmées est FAUX pour de bonnes raisons.
3. **Projections** (`projection.js`) — le what-if par un MOTEUR UNIQUE sur
   six axes standard : temps, exposition, gainDePosition, coutFatigue,
   risqueDesordre, gainInformation. Une manœuvre ne fournit que sa GÉOMÉTRIE.
4. **Scores** (`arbitre.js`) — utilité = Σ poids × axe. Poids en trois
   couches : posture (agression/défense/retraite), personnalité du
   commandant (offsets seedés — ❤️ traits, deux chefs diffèrent), état cru de
   l'unité (fatigue, désordre). AUCUN cas spécial : quand l'ennemi n'est pas
   localisé, gainInformation domine → `ratisser` gagne mécaniquement.
5. **Engagement** (`arbitre.js`) — hystérésis (~+30 % pour détrôner la
   manœuvre engagée), ré-appréciation à deux vitesses (lente + saillance),
   mémoire des échecs (malus temporaire), verbalisation via langage/decrire :
   « leur flanc gauche est ouvert : débordez par la gauche ! » (bulle).

## Frontières

- Le rôle n'émet QUE des paroles (ordres 📯) — jamais d'intention motrice :
  le corps appartient à la machine soldat du même homme.
- Les faits d'estimation et les critères de phases sont des GARDES nommées —
  jamais de code inline, même règle que les machines.
- Les poids se règlent EN REGARDANT : la viz état-major (🖥️) fait partie de
  la tranche 1, pas des finitions.

## Croissance attendue

Hiérarchie (le général : même arbitre, livre d'armée, ordres adressés à des
capitaines — du langage jusqu'en bas), rapports entendus dans l'estimation,
moral de l'unité dans les poids, feintes et doctrine adverse.
