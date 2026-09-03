# ⏱️ Container Orchestration

## Intention

Posséder le temps et l'ordre d'exécution. Aucun autre container ne sait « quand » : celui-ci cadence les phases de la simulation (cognition, action, physique…) à pas de temps fixe, et sépare strictement le temps simulé du temps réel.

## Responsabilités

- Horloge : dt fixe, pause, multiplicateurs (x1/x2/x5). Le multiplicateur joue sur le *nombre de pas par frame*, jamais sur la taille du pas — la physique est identique à toutes les vitesses.
- Pipeline : liste ordonnée et explicite des phases exécutées à chaque tick. L'ordre des phases est une décision d'architecture, pas un accident.

## Frontières

- Ne contient aucune logique métier : il appelle, il ne décide pas.
- Les autres containers ne connaissent jamais le temps réel (ms, requestAnimationFrame) — uniquement le dt qu'on leur passe.

## Reçoit / Fournit

- Reçoit du container 🖥️ Présentation : commandes pause / vitesse (transport).
- Fournit à tous les containers : la cadence (tick, dt).

## Observables

| Feature | Mécanique | Viz |
|---|---|---|
| `pause` | arrêt du temps simulé | ui `transport` |
| `multiplicateur-vitesse` | x1/x2/x5 — nombre de pas par frame | ui `transport` |
| `dt-fixe` | la taille du pas ne change jamais, seul leur nombre varie | — |
| `ordre-des-phases` | les 6 phases du tick, dans l'ordre décidé | — |

## Croissance attendue

Cadences différenciées par phase (la cognition tourne moins souvent que la physique), budgets de calcul, replay déterministe.
