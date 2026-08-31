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
| `test_salle.py` | le fil de salle et les relations : ce que la pièce entend, ce que le chuchotement ne laisse pas fuiter, le filtre « chambre existante » |
| `test_selecteur_contexte.py` | la première couche joueur : cinq items visibles, sièges présents, arbres, session sans reprise, héritage, ancrages stricts, création multi-sièges et séparation joueurs/PNJ ; corpus manuel des dix messages dans `donnees/selecteur_reine_10.json` |
| `test_routeur_message.py` | la deuxième couche : parole aux hommes par numéro brut de contexte puis MJ sur la ref exacte ; retour de parloir vers canal + web + flux MJ append-only, sans perdre une arrivée pendant le réveil ; les gestes ne partent pas aux hommes et deux actions en inbox ne sont pas confondues |
| `test_depeche_contextes.py` | les appels hommes : session stable et fil de chambre distincts par item d'affaire, transmission CLI et sûreté du chemin |
| `test_copier_claude_vers_agents.py` | le miroir récursif `CLAUDE.md` → `AGENTS.md`, l'écrasement et le mode de vérification sans écriture |
| `essai_occupation.py` | 30 cas d'occupation et d'invariants, sur un `etat/` jetable |

**Rien ne touche le vrai dépôt.** `essai_occupation.py` détourne `occupation.ETAT`
vers un dossier temporaire ; les tests unitaires travaillent en `TemporaryDirectory`.
Un test qui lit `etat/` pour de vrai est un test qui tombera le jour où la partie
avance — et qui, un jour, écrira.

**Ne JAMAIS vérifier un script en l'important.** Beaucoup agissent au chargement :
`seed_flux.py` réinitialise le flux, `exporter_plan.py` réécrit `exports/`.
Un balayage d'imports détruit une partie en cours.
Ce qu'on peut faire sans risque : `python -m compileall -q scripts/`, l'évaluation
statique des expressions de racine, ces tests-ci, et les commandes en lecture seule
une par une.

`test_corriger_plan.py` importe `corriger_plan` par un chemin explicite vers
`../plan/` : c'est le seul test qui atteint un module hors racine et hors `noyau/`.
