# src/ — Les containers

L'architecture est organisée en **8 containers** (dossiers de niveau 1). Chaque container a son propre CLAUDE.md qui décrit son intention, ses responsabilités, ses frontières et ses liens.

| Container | Dossier | Intention en une ligne |
|---|---|---|
| ⏱️ **Orchestration** | [orchestration/](orchestration/CLAUDE.md) | Possède le temps et l'ordre d'exécution des phases |
| 🌍 **Monde** | [monde/](monde/CLAUDE.md) | La vérité objective : terrain, positions réelles des corps |
| 🧠 **Cognition** | [cognition/](cognition/CLAUDE.md) | Le cerveau de chaque homme : perception → représentation → décision → intentions |
| 📯 **Social** | [social/](social/CLAUDE.md) | La cognition-à-cognition médiée par le physique : hiérarchie, ordres, transmission |
| ❤️ **Corps** | [corps/](corps/CLAUDE.md) | L'état physiologique interne : stamina, blessures, traits |
| 🏃 **Action** | [action/](action/CLAUDE.md) | Le traducteur : intentions abstraites → vitesses désirées concrètes |
| ⚙️ **Physique** | [physique/](physique/CLAUDE.md) | Bête et incorruptible : forces, collisions, intégration — seul écrivain régulier des positions |
| 🖥️ **Présentation** | [presentation/](presentation/CLAUDE.md) | Fenêtre et télécommande : rendu, UI, inspecteur — la sim tourne headless sans elle |

## Hors containers

- `infra/` — transverse minimal : `rng.js` (aléatoire seedé, unique source de hasard — aucun `Math.random()` ailleurs).
- `main.js` — le bootstrap : SEUL fichier qui connaît tous les containers, compose par injection (aucun container n'en importe un autre), possède la boucle de frame.
- `scenarios/` — pure donnée (seed, zone, maisons, unités, oiseaux), un fichier par scénario, aides partagées dans `generer.js`, catalogue dans `index.js`. Charger = composer un monde neuf.
- `params.js` — constantes transverses, unités SI.

## La boucle principale

🌍 Monde → 🧠 Perception → 🧠 Représentation → 🧠 Décision → 🧠 Intention → 🏃 Action → ⚙️ Physique → 🌍 Monde

## Règles transverses

- **Deux frontières strictes autour de la 🧠 Cognition** : elle ne voit le 🌍 Monde qu'à travers sa Perception, elle n'agit que par Intentions.
- **Deux seuls écrivains** sur le registre des corps (🌍 Monde) : l'Intégration (⚙️ Physique, chaque tick) et le spawn (🖥️ Présentation, drag & drop). Tout le reste lit.
- **Unités en mètres partout** — seule la caméra (🖥️ Présentation) connaît les pixels.
- **Déterminisme** : dt fixe, RNG seedé. Même seed → même scène, à toutes les vitesses.
- **Les ordres sont des percepts** : le 📯 Social ne modifie jamais directement une représentation mentale — la livraison passe par la Perception du destinataire.
