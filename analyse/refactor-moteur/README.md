# Dossier de référence du refactor du moteur

Sortie du **lot 0** de [`docs/bataille/refactor-complet-moteur.md`](../../docs/bataille/refactor-complet-moteur.md) :
ce que le moteur rendait au moment où le refactor a commencé, pour qu'un
déplacement de blocs se voie.

Posé le **26 août 2026**, sur `master` à `133878c` plus les modifications en
cours.

## Ce qu'il contient

| Fichier | Ce que c'est |
|---|---|
| `etalon-depart.json` | copie de `ecrans/modules/bataille/etalon-moteur.json` au moment de la reprise |
| `releve-220s.txt` | la même condition poussée à 220 s, pour voir ce qui se passe *après* la fenêtre de l'étalon |

La condition est celle du banc : 150 hommes, « La porte de la Gadoue », graine
20161219, pas de 0,05 s, ni peuple ni tournée. Elle se rejoue par

```bash
node ecrans/modules/bataille/banc-moteur.js
```

## L'étalon a été reposé, et il faut savoir pourquoi

L'étalon en place datait du **24 août**. Sept fichiers de la chaîne avaient
changé depuis (`mesures`, `roster`, `1-corps`, `corps-adapt`, `reflexion-adapt`,
`commandement`, `bataille2d`), au fil des trois derniers commits — géographie de
Port-Réal unifiée, dragons et commandement enrichis, croisement de vingtaines.
Le banc rendait donc 29 relevés en désaccord : un étalon périmé, pas une
régression introduite par le refactor.

On l'a reposé sur l'état du 26 août. **C'est cet état-là qui fait foi pour la
suite** : à partir du lot 1, toute extraction doit rendre l'égalité exacte, et un
écart non nul est une faute du refactor, jamais une tolérance à élargir.

## Ce que le relevé de départ dit — et il ne dit rien de bon

Sur 100 s comme sur 220 s, dans la condition du banc :

- **0 mort, 0 blessé, 0 fuyard** ;
- la porte de la Gadoue descend de 9000 à **900 points de bois, et s'y arrête** :
  un `porte-abimee`, jamais de `porte-cede` ni de `porte-enfoncee` ;
- aucun `contact`, aucun `premier-sang`, aucun `chef-tombe` ;
- 99 hommes en colonne et 99 qui tiennent, à la fin comme au début.

L'étalon du 24 août, lui, portait 6 morts, 3 blessés, le contact, le premier
sang, la porte enfoncée à la hache et le verrou ouvert. **Le fer ne se touche
plus.** Doubler la durée n'y change rien : ce n'est pas une bataille devenue
lente, c'est une bataille qui s'arrête.

Ce défaut est **antérieur au refactor** et il n'est pas de son ressort immédiat.
Il est noté ici parce que c'est exactement ce que le lot 0 demande de relever
avant de déplacer quoi que ce soit, et parce qu'il tombe dans le périmètre
annoncé des lots 2 et 3 :

> « Fermer les derniers mètres est un mouvement physique ; aucun combattant ne
> s'arrête à 5–10 m parce que l'état `engager` a été atteint. »
> — *validation du lot 3 : « contact réellement fermé jusqu'à la portée »*

**Conséquence pratique pour la suite.** Tant que le contact ne se ferme pas,
l'étalon ne mesure plus le combat : il mesure une marche, une porte frappée une
fois, et des ordres qui circulent. C'est suffisant pour valider une extraction —
ce que le lot 1 demande — et insuffisant pour valider un changement de modèle du
combat. Le premier lot qui touche au contact devra donc reposer une condition où
le fer se touche, et non se contenter de l'égalité de celle-ci.

## Ce que le lot 0 n'a pas fait

- Les métriques manquantes (téléports, collisions, densité, A* calculés,
  distance P90 au chef, combattants arrêtés hors portée, décisions et
  communications) **ne sont pas encore instrumentées**. Le journal de décision
  existe désormais (`moteur/commun/traces.js`), mais rien ne lui écrit encore :
  c'est le premier vrai travail des lots suivants.
- C5, C6, le ratissage, le messager et l'entrée de bâtiment n'ont **pas** été
  relevés séparément : seule la condition du banc l'a été.
