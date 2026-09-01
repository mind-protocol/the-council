# Contrôle de l'architecture — 129.5.12

## Mon désir

Je veux savoir si l'inventaire technique transmis par Serenissima décrit
encore le dépôt que nous avons sous la main à Braavos.

## Sources et épreuve

- Registre : `plan-moyens-serenissima`, moyen M110.
- Comptes canoniques de départ : `mains.json`, constat initial du 129.5.12.
- Épreuve exécutée depuis la racine du dépôt :
  `python scripts/analyse/graphe_archi.py --json`.

## Résultat observable

| Mesure | Registre | Épreuve courante |
|---|---:|---:|
| Fichiers observés | 451 | 451 |
| Modules rattachés | 431 | 431 |
| Modules orphelins | 20 | 20 |
| Liens hors porte | 116 | 115 |
| Dépendances remontantes | 13 | 13 |
| Commandes-bibliothèques | 0 | 0 |

La commande rend le code de sortie `1` tant que des écarts sont présents. Ce
code prouve le signalement de frontières ; il ne suffit pas à prouver une
panne de service.

## Ce qui a changé

Un lien hors porte de moins est observé qu'au registre. Les autres comptes
publiés sont reproduits exactement. Il faut identifier le lien disparu avant
de proposer une mise à jour des `mains`, car le dépôt porte de nombreux travaux
en cours qui ne sont pas les miens.

## Première matière à examiner

Les cinq premiers modules encore orphelins rendus par la sonde sont :

1. `ecrans/modules/chambres.js`
2. `ecrans/modules/fil-homme.js`
3. `scripts/activite.py`
4. `scripts/boucle_activation.py`
5. `scripts/copier_claude_vers_agents.py`

Je ne les rattache pas sans connaître leur autorité. Le prochain geste utile
est de demander au porteur du dépôt lequel de ces modules doit devenir le
premier lot d'examen.
