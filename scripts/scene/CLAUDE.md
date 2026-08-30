# `scene/` — 📜 le flux, l'inbox, la montre, les sièges

**L'intention.** La scène est LA PEAU : ce que le joueur voit et le fil qui le
lui apporte. Le flux (`etat/flux.jsonl`) est append-only et n'a qu'UNE plume ;
tout ce qui y entre passe par elle, estampé de l'heure, compté par le tunnel.

**La porte** : [`expose.py`](expose.py) — `from scene.expose import ...`,
jamais un module interne (docs/organisation.md §2). Particularité de ce
container : `flux.py` est un SCRIPT qui refuse l'import (l'importer pousserait
le flux et avancerait l'horloge) — la porte offre son **lancement**
(`pousser_flux`), jamais son import. Les autres containers ne lisent pas
cette porte : la peau se regarde, elle ne se consomme pas.

## Les modules (les commandes descendues, lot 2)

| module | ce qu'il possède | commande façade |
|---|---|---|
| `flux.py` | LA PLUME : audience déclarée, barrière des deux jours, présence suivie, horloges — un script au flux top-level assumé (~940 l. ; la coupe fine en fonctions est un vrai design, différée au lot-2-features) | `scripts/append_flux.py` |
| `flux_scribe.py` | les gestes d'écriture sans état de poussée : chemins de l'état, teinte et portrait d'un locuteur, montre d'un livre (toucher, extrait), l'heure, l'avancée de la date | — |
| `flux_ecrits.py` | deux avis du pousseur : les renvois `[texte](adresse)` doivent résoudre, ce qu'on ANNONCE doit être ÉCRIT | — |
| `tunnel.py` | le compteur qui refuse le mur : seuils (ITEM, TRANCHE, SUITE, VOIX, FILS), plafond dur (MUR), `--tunnel` pour le mur voulu | `scripts/tunnel.py` (module, pas de CLI) |
| `regie.py` | l'outil du MJ de Corneille : retrouver un moment dans le fil — les candidats, jamais le choix | `scripts/regie.py` |
| `seed_flux.py` | le beat d'ouverture (le conseil noir) — DESTRUCTIF, ne part que par `main()`, l'import est inerte | `scripts/seed_flux.py` |

`guetteur.sh` reste à la racine `scripts/` tel quel (shell, cité par le manuel).

## Frontières

- **Une seule plume du flux** (`flux.py`), append-only ; le flux ne se coupe
  qu'à la main. Les avis (tunnel, acteurs inconnus, renvois, écrits) nomment
  ce qui cloche ; seul le plafond dur du tunnel refuse.
- `sieges.py` vit désormais dans `agents/` (décision du 30, organisation.md §3 :
  les sièges sont la machinerie des acteurs, pas la peau).
- `flux.py` lit l'occupation et la régence par la porte de
  `temps/`, et les tables par la porte de `etat/`.
- `flux_scribe.py` lit `bibliotheque` par la porte de `plan/`.
