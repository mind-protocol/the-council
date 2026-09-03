# 🗺️ Outil — graphe d'architecture

## Intention

Rendre visible le graphe des containers : qui appelle quel `expose`, dans quel
sens circulent les données, et **où le code s'écarte de ce que les CLAUDE.md
déclarent**. Ce dernier point est le vrai livrable : le reste n'est qu'un
dessin.

## Lancer

```bash
node coding/graph/construire.mjs
```

Produit `graphe.json` (le modèle) et `ARCHITECTURE.md` (les diagrammes).
Aucune dépendance, aucun build : Node seul suffit.

## Modules

- `lire-claude-md.mjs` — graphe **déclaré** : le tableau de `src/CLAUDE.md` et
  les sections « Reçoit / Fournit » de chaque container.
- `lire-expose.mjs` — graphe **interne** de chaque container (ses modules et
  leurs imports), et la **nature** de chaque dépendance, lue dans le JSDoc des
  `expose.js`.
- `lire-bootstrap.mjs` — graphe **réel** : les littéraux d'injection de
  `src/main.js`.
- `lire-observables.mjs` — couverture **feature → viz** : les tableaux
  `## Observables`, les tags `@viz` des calques, et le tableau `calques:` de
  l'expose Présentation, croisés dans les deux sens.
- `construire-graphe.mjs` — croise déclaré et réel, produit les divergences.
- `emettre-mermaid.mjs` — le seul module qui connaît Mermaid.
- `construire.mjs` — la CLI.

## Décisions actées

- **Le graphe inter-container n'est pas dans les imports.** Aucun container
  n'en importe un autre ; les 23 imports hors `main.js` sont tous locaux. Un
  analyseur d'imports rendrait huit îlots isolés. La seule source des arêtes
  est le câblage du bootstrap.

- **Deux sens, deux diagrammes.** `appelant → appele` est le sens de l'appel ;
  `fournisseur → consommateur` celui du flux de données. Ils diffèrent dès
  qu'on tire au lieu de pousser : 🏃 Action appelle 🌍 Monde pour lire la
  navgrid, mais la donnée va de Monde vers Action. Les CLAUDE.md décrivent le
  flux, le code montre l'appel — d'où les deux panoramas.

- **La nature vient du JSDoc.** `— vue 🌍`, `— commande 🌍 (écrivain 1/2)`,
  `— puits vers 🏃` : ces annotations des `expose.js` sont ce qui permet de
  déduire le sens du flux à partir d'un sens d'appel. Une dépendance non
  annotée retombe sur `vue`, et le JSON le signale (`natureSource: "defaut"`).

- **JSON intermédiaire obligatoire.** L'extraction est le travail durable,
  l'émetteur est jetable. Le jour où Mermaid plafonne (repli/dépli, filtres,
  surlignage de chemin), seul `emettre-mermaid.mjs` est réécrit.

- **Pas de dépendance.** Le dépôt n'a ni `package.json` ni `node_modules` ;
  tirer un parseur AST pour analyser 90 lignes de bootstrap qu'on écrit
  soi-même serait disproportionné. Extension `.mjs` parce que Node lit un
  `.js` sans `package.json` comme du CommonJS.

## Limites connues

- Le lecteur du bootstrap suit les fonctions fléchées locales sur **un seul
  niveau** (`spawn: spawnHomme`). Une closure qui en appelle une autre serait
  manquée.
- Les `click` de Mermaid ne sont pas activés par le rendu de GitHub. L'index
  de liens en tête d'`ARCHITECTURE.md` couvre le cas.
- Le détail de 🖥️ Présentation est haut (13 modules). Les sous-dossiers le
  replient, mais un container qui doublerait encore demanderait un découpage.

## Croissance attendue

Détection des cycles, coût des arêtes (nombre de membres exposés), historique
des divergences dans le temps, émetteur HTML interactif.
