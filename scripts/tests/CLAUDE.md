# `tests/` — ce qui se vérifie sans toucher au monde

```bash
python -m unittest discover -s scripts/tests -p "test_*.py"
```

| Fichier | Ce qu'il couvre |
|---|---|
| `test_bibliotheque.py` | le stockage des livres : le repli sur le monolithe, le manifeste, l'écriture concurrente |
| `test_plan_modele.py` | le plan visible d'un siège : étagères, mesures, brouillons |
| `test_mesures.py` | les adresses de mesure : ce qu'un cahier cite vs ce que l'état tient |
| `test_corriger_plan.py` | la correction par fragment : unique, ambigu, idempotent |
| `essai_occupation.py` | 30 cas d'occupation et d'invariants, sur un `etat/` jetable |
| `incendie-ville.test.mjs` | l'incendie de ville, côté JavaScript |

**Rien ne touche le vrai dépôt.** `essai_occupation.py` détourne `occupation.ETAT`
vers un dossier temporaire ; les tests unitaires travaillent en `TemporaryDirectory`.
Un test qui lit `etat/` pour de vrai est un test qui tombera le jour où la partie
avance — et qui, un jour, écrira.

**Ne JAMAIS vérifier un script en l'important.** Beaucoup agissent au chargement :
`seed_flux.py` réinitialise le flux, `exporter_plan.py` réécrit `exports/`,
`bataille.py` cuit une bataille. Un balayage d'imports détruit une partie en cours.
Ce qu'on peut faire sans risque : `python -m compileall -q scripts/`, l'évaluation
statique des expressions de racine, ces tests-ci, et les commandes en lecture seule
une par une.

`test_corriger_plan.py` importe `corriger_plan` par un chemin explicite vers
`../plan/` : c'est le seul test qui atteint un module hors racine et hors `noyau/`.
