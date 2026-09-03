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
| `test_routeur_message.py` | la première couche directe : présence physique, exclusion des sièges joueurs et des marcheurs, parole par billet-réveil sans MJ, gestes et jump au MJ, reçu durable et consommation étroite de la ref ; retour de parloir vers canal + web + flux MJ append-only |
| `test_flux_transport.py` | la plume unique : empreinte sans estampilles, fenêtre anti-retry et verrou entre deux processus d'écriture |
| `test_git_donnees.py` | snapshot data-only : périmètre, exclusions des verrous/caches, validation JSONL et détection d'une écriture concurrente |
| `test_runtime_agents.py` | runtime multi-fournisseur et garde basse : 15 slots globaux, refus atomique du 16e, adoption d'une réservation CAST sans double comptage, nettoyage des PID recyclés |
| `test_depeche_contextes.py` | les appels hommes : session stable et fil de chambre distincts par item d'affaire, transmission CLI et sûreté du chemin |
| `test_copier_claude_vers_agents.py` | le miroir récursif `CLAUDE.md` → `AGENTS.md`, l'écrasement et le mode de vérification sans écriture |
| `test_comptoir_moyens.py` | le contrat de comparaison M110 : conformité, dérive, sources des deux valeurs et registre incomplet |
| `test_partie_cartes.py` | la vue joueur d'une partie : le brouillard sur l'ennemi, les apparences des cartes, le compte des obstacles en descendant, aucun id nu — sur `donnees/partie-duel.jsonl`, noms posés à la main |
| `test_partie_gestes.py` | les gestes du joueur : ce qu'une carte posée sur une carte devient au grand livre, le renfort au lieu du doublon, la reprise qui gèle, les refus en clair — sur une COPIE jetable du même duel, parce que ce module écrit |
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
