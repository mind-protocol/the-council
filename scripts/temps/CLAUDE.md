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
| `gardes/` | les 19 vérificateurs + `Rapport` + `verifier()` — voir `gardes/__init__.py` |
| `fenetre.py` | `calculer()` en phases nommées + `tick()` — le cœur du mode B |
| `resume.py` | la proposition en français, pour le MJ |
| `occupation.py`* | qui est ASSIS — mesuré, pas drapeau *(encore à la racine scripts/, lot 2)* |
| `presence.py`* | qui est à portée — le quartier *(idem)* |
| `regence.py`* | ce qu'un siège vacant peut faire *(idem)* |
| `evaluer.py`* | qui a du temps — la feuille de route *(idem)* |

La commande `scripts/tick.py` est une **façade** : argparse + appels aux
modules. Son chemin et sa CLI (`--verifier`, `--jours`, `--jusqu-a`,
`--acteur`, `--joueur`, `--json`) sont gelés pour l'éternité.

## Décisions actées

- **D-a (scelle.py)** : le vocabulaire d'état (staging) — `TABLES_MUTABLES`,
  `CROYANCES`, l'écriture scellée — est **candidat à `etat/` le jour où un
  second écrivain apparaît**. Pas avant : rien sans consommateur réel.
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

- **Lecture seule sur `etat/`**, une seule écriture (`scelle.ecrire_proposition`),
  refusée hors `etat/`.
- Les gardes **signalent, ne réparent jamais** ; les notes n'entrent pas dans
  le code de sortie.
- Aucune prose machinale : la `version` d'une rumeur, le contenu d'un saut,
  c'est le MJ qui l'écrit — `appliquer.py` refuse un lot sans contenu.

## Consommateurs

`appliquer.py` (BUDGETS, empreintes), `migrations/migrer_plis.py` (Etat,
plis), `boucle_activation.py` / `sieges.py` / `regence.py` (occupation,
regence), `serveur/domaine/activations.js` (`--verifier --json` →
/admin/sante), `scripts/tests/essai_occupation.py` (les invariants de
`verifier_occupation`).
