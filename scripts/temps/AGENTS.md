# `temps/` — ⏱️ horloges, échéances, occupation, présence

**L'intention.** Le hors-scène est de l'arithmétique : ce qui tombe entre deux
dates, et rien de plus. Le container possède le calendrier, la fenêtre du tick,
l'audit de cohérence de `etat/`, et les mesures d'occupation et de présence.
**Le script ne décide RIEN** : il lit `etat/` et n'écrit que des PROPOSITIONS
sous `etat/` — le MJ seul relit, arbitre et applique.

**La porte** : [`expose.py`](expose.py) — `from temps.expose import ...`,
jamais un module interne (docs/organisation.md §2). L'ordre de ses imports est
une contrainte documentée en tête : les modules qui relisent la porte pendant
son chargement exigent que `occupation`, `presence` et `regence` soient liés
avant eux.

## Les modules (le découpage de tick.py, acté)

| module | ce qu'il possède |
|---|---|
| `calendrier.py` | dates absolues {annee, lune, jour} ↔ entier de jours, format, lecture CLI |
| `lecture.py` | `charger()`, la classe `Etat` et ses index, `jours_de_route`, constantes du courrier |
| `bouche.py` | mots rares (l'heuristique de recoupement), l'échelle mesurée sur le quartier, budgets |
| `mains.py` | l'arithmétique des mesures : rythmes, bornes, décomptes exacts, seuils, coûts chiffrés |
| `scelle.py` | empreintes des tables, chemin scellé, la SEULE écriture du tick |
| `rumeur.py` | propagation des incidents, détection des bouches (arrivées), témoins, cycles |
| `gardes/` | les 19 vérificateurs + `Rapport` + `verifier()` — 5 familles, voir `gardes/__init__.py` |
| `mutations.py` | la rédaction des mutations arithmétiques proposées (extrait de fenetre.py, limite 500) |
| `fenetre.py` | `calculer()` en phases nommées + `tick()` — le cœur du mode B |
| `resume.py` | la proposition en français, pour le MJ |
| `occupation.py` | qui est ASSIS — mesuré, pas drapeau *(descendu au lot 2 ; façade `scripts/occupation.py`)* |
| `presence.py` + `presence_quartier.py` | qui est où, à la minute — la résolution / le quartier du joueur, les creux, la CLI *(façade `scripts/presence.py`)* |
| `regence.py` + `regence_passation.py` | les sept lignes rouges et le crible / la clause, le registre de passation, la CLI *(façade `scripts/regence.py`)* |
| `disponibilite.py` + `disponibilite_regie.py` | qui a du temps — les questions 1-7 / la force narrative et la feuille de la régie *(la porte garde le nom historique `evaluer` ; façade `scripts/evaluer.py`)* |
| `reprise.py` | la feuille de reprise — les cinq questions d'un joueur qui se rassoit *(façade `scripts/reprise.py`)* |

La commande `scripts/tick.py` est une **façade** : argparse + appels aux
modules. Son chemin et sa CLI (`--verifier`, `--jours`, `--jusqu-a`,
`--acteur`, `--joueur`, `--json`) sont gelés pour l'éternité.

## Décisions actées

- **D-b (gardes/)** : conceptuellement du **banc** (lit tout, n'écrit rien) —
  **réexamen vers `bancs/` après le lot 2**. La tension est notée dans
  `gardes/__init__.py`, on ne déménage pas deux fois.
- **jours_relatifs.py n'est PAS fusionné dans calendrier.py** : son
  `rang(a, l, j)` vaut `((a*12)+l)*30+j`, sans le décalage −1 que
  `jour_absolu` applique — deux arithmétiques du même calendrier, décalées de
  31. Fusionner changerait les rangs cités par les cahiers ; il reste dans
  `noyau/`, et l'écart est documenté en tête de `calendrier.py`.
- **Le bruit de fond** (grain 3, co-présence → diffusion) atterrira dans
  `rumeur.py` — c'est la feature qui a tiré ce découpage
  (docs/organisation.md §5).

## Frontières

- **Lecture seule sur `etat/`** : le tick calcule et affiche ; les habitants
  écrivent eux-mêmes ce qu'ils produisent.
- Les gardes **signalent, ne réparent jamais** ; les notes n'entrent pas dans
  le code de sortie.
- Aucune prose machinale : la `version` d'une rumeur et le contenu d'un saut
  viennent d'un homme.

## Consommateurs

`sieges.py` / `regence.py` (occupation, regence),
`serveur/domaine/activations.js` (`--verifier --json` →
/admin/sante), `scripts/tests/essai_occupation.py` (les invariants de
`verifier_occupation`).
