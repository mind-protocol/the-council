# Batailles

Simulateur de batailles médiévales. **Objectif : le réalisme par l'émergence** — des individus qui perçoivent, croient, se trompent, fatiguent, obéissent (ou pas) ; les comportements collectifs (mêlées, paniques, manœuvres) émergent, ils ne sont jamais scriptés au niveau global.

L'architecture est en 8 containers : voir [src/CLAUDE.md](src/CLAUDE.md) (index, boucle principale, règles transverses), puis le CLAUDE.md de chaque container. Elle se lit aussi en diagrammes : [coding/graph/ARCHITECTURE.md](coding/graph/ARCHITECTURE.md), généré depuis le câblage réel — mode d'emploi dans [coding/CLAUDE.md](coding/CLAUDE.md).

## Manière de travailler

### Le fond

- **Le réalisme passe par la physicalisation.** L'appartenance est une livrée qu'on VOIT, un ordre est un son qui porte (ou pas), une info circule physiquement et peut se perdre. Les cadences et variations individuelles sont des distributions (normales de préférence), pas des constantes.
- **Pas de grosse décision pour aller vite.** Une décision structurante (sémantique mémoire, snapshot, reset vs reconstruction…) se discute explicitement avant le code. Si on la diffère, on écrit QU'elle est différée, et ce qui est déjà acté pour le jour venu.
- **Rien sans consommateur réel.** On n'implémente pas ce dont personne n'a besoin encore (ex. : index spatial différé tant que les hommes ne se perçoivent pas). L'API étroite d'abord, l'optimisation quand le besoin existe.

### La forme

- **Architecture d'abord.** Modules, frontières et liens se discutent avant d'écrire du code. Le temps passé sur l'archi est un investissement assumé.
- **Étape par étape, validation entre chaque** : proposition → discussion → décision → exécution. Une brique à la fois.
- **Passes successives** : enveloppes d'abord (signatures documentées, corps en `à implémenter`), implémentation ensuite. La première passe est assumée imparfaite — on repasse.
- **Une viz pour chaque système.** Toute mécanique interne doit être observable dès sa création : calque de debug (les chemins A* existent depuis la première heure) ou inspecteur (`introspect()` est obligatoire sur tout brain — un module non observable est un bug).
- **Les « pourquoi » vivent dans les CLAUDE.md** des containers ; les fichiers code ne portent que les contrats, courts.
- **Les noms anticipent la croissance** : dossier + nom précis (`forces/repulsions.js`, pas `forces.js`). Max 500 lignes par fichier (hook).
- **Vérification headless** : la sim tourne sous Node sans navigateur (c'est une propriété d'archi, pas un accident). Test de fumée + déterminisme : même seed → même scène.
- **Tout en français** — code, commentaires, doc, commits (messages sans accents).

## Lancer

- Serveur de dev : `node outils/serveur.mjs 4173` (ou via `.claude/launch.json`), puis http://localhost:4173
- Vue d'architecture : `node coding/graph/construire.mjs` — régénère les diagrammes et liste les écarts entre le câblage et les CLAUDE.md
- Test de fumée : `node coding/fumee.mjs` — headless, déterminisme (même seed → même scène, bit-exact), dt fixe (x5 ≡ x1), introspection obligatoire. À lancer après tout changement de sim.
- La sim headless se compose depuis les exposes comme dans [src/main.js](src/main.js) — [coding/fumee.mjs](coding/fumee.mjs) en est l'exemple sans navigateur.
