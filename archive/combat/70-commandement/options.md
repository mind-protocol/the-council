# Options

## 1. Ce que c'est

La bibliothèque des actions tactiques réellement possibles depuis l'état courant —
générale, close, et indépendante de qui est en face.

## 2. Ce qu'il possède

- **Le catalogue des actions**, petit, clos, le même pour tous : tenir, avancer
  sur un objet, contourner, se replier, rompre le contact, renforcer un voisin,
  prendre ou tenir un seuil, reconnaître, changer de forme ou d'allure, demander.
- **Les conditions d'ouverture** : une action est ouverte ou fermée, et fermée on
  sait **pourquoi** — pas les hommes, pas le terrain, pas le temps, objet inconnu.
- **Le paramétrage** : objet, borne, part de forces engagée. C'est là que vit la
  variété, pas dans le nombre de verbes.
- **La compatibilité avec l'ordre courant** : une option qui le contredit n'est
  pas supprimée, elle est marquée. Un chef a le droit de désobéir, pas celui
  d'ignorer qu'il désobéit.
- **Les options fermées et leur raison** : ne rien pouvoir est une information.

## 3. Ce qu'il lit

Du socle : mesures, horloge. Du monde : le terrain, la navigation et les seuils,
pour savoir si un objet est atteignable et à quel coût. De l'unité : ce dont ses
corps sont capables — forme, allure, cohésion, effectif réel de ceux qu'il
commande. De la transmission : l'ordre courant et les canaux ouverts, car
« demander » n'existe que si un canal existe. Des croyances et de l'estimation :
pour savoir si un objet lui est **connu**.

Il ne lit **rien de l'état réel adverse**. Une option ne se ferme jamais parce
que l'ennemi est fort : elle se ferme parce que le chef n'a pas les moyens, pas
le terrain, ou pas la connaissance.

## 4. Ce qu'il produit

- **Les options ouvertes**, chacune avec son paramétrage possible.
- **Les options fermées et leur cause**, et le marquage de conformité à l'ordre.
- **Le coût d'entrée** : ce qu'il faut engager pour commencer.

## 5. Invariants

- **Le catalogue ne dépend pas de l'ennemi.** Une sonde refuse toute option dont
  l'ouverture est conditionnée par le type du corps adverse. Pas de « réponse à la
  cavalerie » : « changer de forme », dont un chef fera peut-être quelque chose.
- Il y a **toujours au moins une option ouverte**, ne serait-ce que tenir ou
  demander ; un chef sans option est un défaut de ce module.
- Toute option ouverte se traduit en un ordre de la couche 60, sans reste.
  Génération reproductible ; aucune option pour un objet qu'il ne connaît pas.

## 6. Ce qu'il ne fait pas

- **Il n'évalue pas** : aucun score, aucun classement, aucune préférence. Il ne
  projette pas ce que l'option donnerait, et **il ne choisit pas**.
- **Il ne contient aucune doctrine par type d'ennemi.** C'est l'interdit central
  de la fiche : une bibliothèque qui se ramifie par nature adverse devient un
  arbre de recettes et déguise en tactique une table de correspondances.
- **Il ne connaît pas la mission d'armée** : ce qu'un objectif général rend
  souhaitable appartient à la couche 80.
- **Il ne filtre pas par vraisemblance narrative.** Une option absurde reste
  ouverte : la projection la disqualifiera, et ce rejet se lira dans la trace.

## 7. Ce que l'ancien moteur faisait mal ici

**Ce module n'existait pas.** Aucun chef n'énumérait ce qu'il pouvait faire :
**il n'existait aucun chemin de code par lequel un chef change son ordre depuis un
renseignement**, et **les cinq endroits qui posaient un ordre le recevaient tous
de l'extérieur du moteur** — un scénario, une interface.

La mesure en aval le confirme : **zéro ordre adapté sur quinze chefs**, et sur
une bataille entière **deux changements d'ordre d'unité seulement**, aux instants
exacts où le scénario les posait.

Il n'y a donc rien à corriger ici, seulement un piège à ne pas retrouver. Le
raccourci naturel, quand on part de zéro, est d'écrire la règle utile — « face à
de la cavalerie, resserrer » — parce qu'elle produit un comportement visible tout
de suite. C'est ainsi qu'on rebâtit une doctrine par type d'ennemi, et qu'on
obtient un moteur dont le comportement vient de sa table et non de ses croyances.
La conformité se mesure autrement : **quelle part des changements d'ordre est
causée par un fait arrivé au chef.** Elle valait zéro.
