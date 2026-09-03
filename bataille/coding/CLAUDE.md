# coding/ — l'outillage

## Intention

Les outils qui servent à **travailler sur** la simulation, jamais à la faire
tourner. Rien ici n'est importé par `src/` : la sim doit rester exécutable si
ce dossier disparaît.

- `graph/` — extrait le graphe d'architecture et le compare aux CLAUDE.md.
  Détail d'implémentation dans [graph/CLAUDE.md](graph/CLAUDE.md).
- `vecu.mjs` — diagnostic comportemental : court un scénario headless et
  imprime le VÉCU des machines (temps par état, bascules par transition,
  état-major) pour le chef + deux hommes tirés au sort (seedé).
  `node coding/vecu.mjs [dureeS] [id-scenario]`. À lancer quand un
  comportement « passe trop de temps quelque part » — les barres le montrent.
- `fumee.mjs` — test de fumée headless : déterminisme bit-exact, invariance
  à la vitesse (dt fixe), introspection obligatoire, snapshot vivant. Sa
  composition REFLÈTE `src/main.js` sans la Présentation : un changement de
  câblage du bootstrap le casse bruyamment — le mettre à jour fait partie du
  changement. Le lancer après toute modification de la sim.

## Comment une session utilise le graphe

### Quand le lancer

```bash
node coding/graph/construire.mjs
```

- **Au début d'une session qui touche à l'architecture** : le tableau des
  divergences dit en dix lignes où en est vraiment le projet, sans lire les
  neuf CLAUDE.md.
- **Après tout changement de câblage** dans `src/main.js` — une dépendance
  injectée ajoutée, retirée ou renommée.
- **Après avoir édité une section « Reçoit / Fournit » ou « Observables »**
  d'un CLAUDE.md, ou ajouté/retiré un calque.
- **Avant de proposer un changement de frontière** entre containers : le
  panorama montre ce que la frontière porte réellement aujourd'hui.

Inutile de le lancer après un changement qui reste à l'intérieur d'un
container : l'outil ne lit que les frontières et le câblage.

### Lire la sortie

`ARCHITECTURE.md` contient **deux panoramas dont les flèches vont dans des sens
différents**, et les confondre mène à des contresens :

- **« qui appelle quel expose »** — le sens de l'appel. C'est la vérité du
  code. 🏃 Action pointe vers 🌍 Monde parce qu'Action appelle `monde.navgrid`.
- **« flux de données »** — le sens de la donnée. Le même lien s'y inverse :
  la navgrid va de Monde vers Action. C'est le sens que décrivent les sections
  « Reçoit / Fournit », et celui de la boucle principale.

Une vue se tire (l'appel remonte le flux), une commande et un puits se
poussent (l'appel suit le flux). La forme du trait le dit : `-->` vue,
`==>` commande, `-.->` puits.

### Que faire de chaque divergence

Une divergence n'est **pas** automatiquement un bug. Trois types sur cinq ne
demandent aucune action.

| Type | Ce que ça dit | Réaction attendue |
|---|---|---|
| `container-non-implemente` | Un CLAUDE.md sans `expose.js` | **Rien.** C'est la feuille de route, pas une dette. |
| `declare-non-cable` | Un contrat écrit, jamais branché | **Rien par défaut** — « rien sans consommateur réel ». Ne pas implémenter un container pour faire tomber la ligne. |
| `puits-mort` | Câblé, mais le corps est vide | À traiter le jour où le consommateur existe. D'ici là, le TODO est la bonne réponse. |
| `cable-non-declare` | Le code est en avance sur la doc | **Corriger la doc, pas le code** : ajouter la ligne « Reçoit / Fournit » dans les CLAUDE.md des deux containers. |
| `declaration-unilaterale` | Un seul des deux pairs déclare le lien | Ajouter la ligne manquante chez le pair. |
| `feature-sans-viz` | Une mécanique déclarée sans représentation | La dette de viz assumée (« une viz pour chaque système »). À résorber quand on retouche le feature ; jamais en fermant les yeux (retirer la ligne). |
| `viz-calque-inconnu`, `calque-non-branche` | Un Observable pointe un calque absent ou débranché | Corriger tout de suite : le fichier, l'import, ou la ligne du tableau. |
| `viz-non-revendiquee`, `viz-orpheline`, `calque-sans-viz` | Les tags `@viz` et les tableaux Observables ne se recoupent pas | Aligner le `@viz` du calque et la ligne du tableau — les deux doivent dire la même chose. |

Les deux derniers sont les seuls qui appellent une correction immédiate, et
elle se fait toujours **dans les CLAUDE.md**. Si un `cable-non-declare`
révèle un lien qu'on ne veut pas, alors c'est le câblage de `main.js` qu'on
change — mais c'est une décision d'architecture, à discuter avant, pas un
nettoyage.

## Règles

- **`graphe.json` et `ARCHITECTURE.md` sont des sorties.** Ne jamais les
  éditer à la main : la modification serait écrasée au prochain lancement.
  Pour changer un diagramme, on change l'émetteur.
- **Une session qui modifie le câblage relance l'outil** et mentionne les
  divergences nouvelles dans sa réponse. Un lien qui apparaît sans être
  déclaré est une décision d'archi qui a échappé à la discussion.
- **Un nouveau feature arrive avec sa ligne Observables et sa viz** — c'est
  la règle « une viz pour chaque système », rendue mécanique : le slug dans le
  tableau du container, le tag `@viz` sur le calque qui le montre. Les refs
  `inspecteur` et `ui` sont déclaratives (le contrôle statique ne vérifie que
  les `calque`) ; et un ✓ statique ne prouve pas que la viz montre VRAIMENT la
  mécanique — le calque chemins affiche le chemin lissé sans montrer l'effet
  du lissage. L'œil reste juge.
- Les conventions du dépôt s'appliquent ici aussi : français partout, max
  500 lignes par fichier, les « pourquoi » dans les CLAUDE.md.
