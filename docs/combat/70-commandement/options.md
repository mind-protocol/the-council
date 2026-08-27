# Options

## 1. Ce que c'est

La bibliothèque des actions tactiques réellement possibles depuis l'état courant —
générale, close, et indépendante de qui est en face.

## 2. Ce qu'il possède

- **Le catalogue des actions**, petit et clos, le même pour tout le monde : tenir
  la position, avancer sur un objet, contourner par un côté, se replier sur un
  appui, rompre le contact, renforcer un voisin, prendre ou tenir un seuil,
  envoyer reconnaître, changer de forme, changer d'allure, attendre un délai
  déterminé, demander (des ordres, un renfort, une permission).
- **Les conditions d'ouverture** de chaque action, exprimées sur l'état courant :
  une action est ouverte ou fermée, et quand elle est fermée on sait **pourquoi**
  — pas les hommes, pas le terrain, pas le temps, interdit par l'ordre courant,
  objet inconnu.
- **Le paramétrage d'une action** : son objet, sa borne, sa part de forces
  engagée. C'est là que vit la variété, pas dans le nombre de verbes.
- **La compatibilité avec l'ordre courant** : une option qui contredit l'ordre
  reçu n'est pas supprimée, elle est marquée comme telle. Un chef a le droit de
  désobéir, il n'a pas le droit de ne pas savoir qu'il désobéit.
- **La liste des options fermées et de leur raison**, conservée, parce qu'un
  chef qui ne pouvait rien faire est une information et pas un vide.

## 3. Ce qu'il lit

- Du socle : mesures, horloge.
- Du monde : le terrain et la navigation, pour savoir si un objet est atteignable
  et à quel coût ; les seuils.
- De l'unité : ce dont ses corps sont capables — forme, allure, cohésion,
  effectif réel des siens qu'il commande.
- De la transmission : l'ordre courant, et les canaux ouverts (une option
  « demander » n'existe que si un canal existe).
- Des croyances et de l'estimation : pour savoir si un objet est **connu** de lui.

Il ne lit **rien de l'état réel adverse**. Une option ne se ferme jamais parce
que l'ennemi est fort : elle se ferme parce que le chef n'a pas les moyens, pas
le terrain, ou pas la connaissance.

## 4. Ce qu'il produit

- **Les options ouvertes maintenant**, chacune avec son paramétrage possible.
- **Les options fermées et leur cause.**
- **Le marquage de conformité** à l'ordre courant.
- **Le coût d'entrée** de chaque option : ce qu'il faut engager pour la commencer,
  sans rien dire de ce qu'elle produira — ça, c'est la projection.

## 5. Invariants

- **Le catalogue ne dépend pas de l'ennemi.** Une sonde extérieure refuse toute
  option dont l'ouverture est conditionnée par le type du corps adverse. Il n'y a
  pas de « réponse à la cavalerie » : il y a « changer de forme », dont un chef
  qui croit voir de la cavalerie fera peut-être quelque chose.
- Il y a **toujours au moins une option ouverte**, ne serait-ce que tenir ou
  demander. Un chef sans option est un défaut de ce module.
- Toute option ouverte est exécutable : elle se traduit en un ordre du vocabulaire
  de la couche 60, sans reste.
- La génération est reproductible : mêmes entrées, mêmes options, même paramétrage.
- Aucune option n'est produite pour un objet que le chef ne connaît pas.

## 6. Ce qu'il ne fait pas

- **Il n'évalue pas.** Aucun score, aucun classement, aucune préférence. Ouvertes
  ou fermées, c'est tout.
- **Il ne projette pas** ce que l'option donnerait.
- **Il ne choisit pas.**
- **Il ne contient aucune doctrine par type d'ennemi.** C'est l'interdit central
  de la fiche : une bibliothèque qui se ramifie par nature adverse devient un
  arbre de recettes, grossit sans fin, et déguise en tactique ce qui n'est qu'une
  table de correspondances.
- **Il ne connaît pas la mission d'armée.** Ce qu'un objectif général rend
  souhaitable appartient à la couche 80 ; ici, on dit seulement ce qui est
  possible.
- **Il ne filtre pas par vraisemblance narrative.** Une option ouverte mais
  absurde reste ouverte : c'est la projection qui la disqualifiera, et ce rejet
  se lira dans la trace.

## 7. Ce que l'ancien moteur faisait mal ici

**Ce module n'existait pas.** Aucun chef n'énumérait jamais ce qu'il pouvait
faire : **il n'existait aucun chemin de code par lequel un chef change son ordre
depuis un renseignement**, et **les cinq endroits qui posaient un ordre le
recevaient tous de l'extérieur du moteur** — un scénario, une interface.

La mesure en aval le confirme sans ambiguïté : **zéro ordre adapté sur quinze
chefs**, et sur une bataille entière **deux changements d'ordre d'unité
seulement**, aux instants exacts où le scénario les posait.

Il n'y a donc rien à corriger ici, seulement un piège à ne pas retrouver. Le
raccourci naturel, quand on part de zéro, est d'écrire directement la règle
utile — « face à de la cavalerie, resserrer » — parce qu'elle produit un
comportement visible tout de suite. C'est ce qui rebâtit une doctrine par type
d'ennemi au lieu d'une bibliothèque, et ce qui redonne un moteur dont le
comportement vient de sa table et non de ses croyances. La conformité à cette
fiche se mesure autrement : **quelle part des changements d'ordre est causée par
un fait arrivé au chef.** Sur l'ancien moteur, cette part valait zéro.
