# Le Conseil

Jdr narratif type Crusader Kings 3 dans l'univers de House of the Dragon, joué en session Claude Code : Claude est le MJ, le monde vit dans des fichiers JSON. Départ : 129 AC, mort de Viserys I — la Danse des Dragons commence. Le canon suit son cours… sauf si vos actes le dévient. Vous ne savez que ce que vos corbeaux, vos gens et les rumeurs vous rapportent — avec délai, et déformation.

## Lancer une partie

Ouvrir une session Claude Code dans ce dossier et dire **« on joue »**. S'il n'y a pas de partie en cours (`etat/journal.json` sans `maison_joueur_id`), Claude ouvre la création de maison ; sinon il reprend la scène où elle en était.

Le jeu s'affiche dans une page servie par `serveur/serveur.js` (port 3129, entrée « jeu » de `.claude/launch.json`, lancée par l'outil preview_start) :

```bash
node serveur/serveur.js
```

Au bas du fil, une barre permanente : **Parler**, **Agir**, **Attendre**, **Question** (hors fiction), **Penser** (peser la situation, gratuit), **Coulisses** (hors univers), **Laisser faire** (le MJ tient votre personnage). Pas de menus d'options : on écrit ce qu'on veut.

## Comment ça tourne

- **Le flux** — `etat/flux.jsonl`, append-only : le MJ y pousse des items (récit, réplique, geste, salle, brève, pensée…) via `scripts/append_flux.py`, la page les joue en stream. Le joueur POSTe ses actions dans `etat/inbox/`, le MJ les guette avec `scripts/guetteur.sh`.
- **Le temps** — `monde.date` porte jour ET minute ; chaque item coûte sa `duree`. `scripts/tick.py` calcule ce qui tombe (horloges de plan, événements, nouvelles à livrer) et écrit une proposition dans `etat/staging/` ; `scripts/appliquer.py` l'applique après validation. Le tick n'écrit jamais dans `etat/` tout seul.
- **Le brouillard** — la vérité du monde et ce que le joueur en sait sont deux choses. Les nouvelles arrivent en retard et déformées (`etat/info.json`) ; la carte (`etat/jetons.json`, `etat/vues.json`) porte des croyances, pas des positions réelles. Les PNJ subissent le même brouillard : leurs têtes vivent dans `etat/intentions.json` et ne changent que par une nouvelle reçue.
- **Le décor** — plusieurs échelles commutables : le royaume (table peinte), la ville, le terrain (`etat/terrain.json`), le château (plans de `ecrans/modules/plans.js`), les livres (`etat/books.json`), et un monde 3D (`ecrans/monde3d.html`) où lieux et corps ont une adresse physique (`etat/corps.json`, `scripts/affecter.py`, `scripts/marche.py` pour les distances réelles).
- **Les sièges** — `etat/joueurs.json` : plusieurs personnages jouables, chacun avec son inbox, son horloge et ses croyances. On s'assied et on se relève avec `scripts/sieges.py` ; un siège quitté doit avoir une tête, sinon il dort. À deux joueurs, un MJ par joueur (voir `CLAUDE.md`).

## Structure

- `CLAUDE.md` — manuel du MJ, chargé par Claude à chaque session.
- `docs/schema.md` — source de vérité du format des données (ne jamais le modifier). Autres notes de conception à côté : `carte.md`, `books.md`, `corps.md`, `activites.md`, `plis.md`, `journees.md`.
- `etat/*.json` — l'état du monde : monde, maisons, personnages, relations, lieux, événements, info (ce que le joueur sait), paroles, actes, intentions (têtes des PNJ — jamais montrées), annales, journal.
- `ecrans/` — la page de jeu (`jeu.html`, `jeu.css`) découpée en modules JS (`ecrans/modules/`, un type d'item = un module), les portraits et les templates de widgets.
- `serveur/serveur.js` — sert la page, le flux, les entités, et reçoit les actions du joueur.
- `scripts/` — outils du MJ : `append_flux.py`, `tick.py`, `appliquer.py`, `ajouter.py`, `veille.py`, `sieges.py`, `guetteur.sh`, génération de portraits et de voix, monde 3D.

## Commandes utiles

```bash
python scripts/tick.py --verifier
```

```bash
python scripts/tick.py --jours 1
```

```bash
python scripts/sieges.py
```
