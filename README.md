# Le Conseil

Jdr narratif type Crusader Kings 3 dans l'univers de House of the Dragon, joué en session Claude Code : Claude est le MJ, le monde vit dans des fichiers JSON. Départ : 129 AC, mort de Viserys I — la Danse des Dragons commence. Le canon suit son cours… sauf si vos actes le dévient. Vous ne savez que ce que vos corbeaux, vos gens et les rumeurs vous rapportent — avec délai, et déformation.

**Ce que ça fait de jouer, raconté du côté du joueur : [`docs/experience.md`](docs/experience.md).**
**Des parties à ouvrir, du siège de clerc à la Danse entière : [`docs/parties.md`](docs/parties.md).**

## Lancer une partie

Ouvrir une session Claude Code dans ce dossier et dire **« on joue »**. S'il n'y a pas de partie en cours (`etat/journal.json` sans `maison_joueur_id`), Claude ouvre la création de maison ; sinon il reprend la scène où elle en était.

Le jeu s'affiche dans une page servie par `serveur/serveur.js` (port 3129, entrée « jeu » de `.claude/launch.json`, lancée par l'outil preview_start) :

```bash
node serveur/serveur.js
```

## Ce que vous voyez

Un écran plein, deux panneaux. À droite **le fil**, qui coule tout seul : les phrases tombent une par une, quelques secondes d'écart, comme si on vous racontait la scène en direct. À gauche tout ce qui vous situe : la date au jour ET à la minute, le lieu précis, et les **visages des présents** — celui qui parle s'illumine, celui qui se tait longtemps s'estompe, et revient à son premier mot.

**Pas de menus d'options. Jamais.** En bas, un champ de saisie qui ne se désactive jamais — même pendant que le MJ écrit la suite. Sept boutons changent ce que votre phrase *est* :

| | ce que ça fait |
|---|---|
| **Parler** | vos mots sortent de votre bouche ; la salle les entend et s'en souviendra |
| **Agir** | vous faites quelque chose ; l'issue est incertaine et on ne vous dit pas vos chances |
| **Question** | hors fiction : « où en est-on ? ». Le temps s'arrête, personne ne vous entend |
| **Penser** | vous pesez la situation. Gratuit, silencieux, et le seul endroit où vous avez une vue claire |
| **Coulisses** | vous parlez *de* la partie, pas dedans. Rien n'entre dans l'état ; on peut décerner une médaille idiote |
| **Laisser faire** | vous vous écartez, le MJ tient votre personnage — décisions comprises — dans votre style |
| **Intervention** | vous réparez, développez ou réécrivez la fiction elle-même. Là, rien ne vous est refusé |

Un fanion **« Améliorer »** à côté du bouton d'envoi : vous tapez `elel part demai`, la ligne se remplace **en place** par « — Elle part demain. » Le sens ne bouge pas, votre orthographe n'existe plus.

À côté : un bouton **Couper** (quand une tranche est trop longue et que vous voulez reprendre la parole), deux **curseurs de narrateur** (*explication* et *guidage*), et **Vos desseins** dans la colonne — vos objectifs, nés d'une promesse ou d'une menace en scène, jamais d'un menu.

## Comment ça tourne

- **Le flux** — `etat/flux.jsonl`, append-only : le MJ y pousse des items (récit, réplique, geste, salle, brève, pensée…) via `scripts/append_flux.py`, la page les joue en stream. Le joueur POSTe ses actions dans `etat/inbox/`, le MJ les guette avec `scripts/guetteur.sh`. Une vingtaine de types d'items, un module JS chacun dans `ecrans/modules/`.
- **Le temps** — `monde.date` porte jour ET minute ; chaque item coûte sa `duree`. Un conseil de quarante répliques prend une heure, pas un après-midi. `scripts/tick.py` calcule ce qui tombe (horloges de plan, événements, nouvelles à livrer) et écrit une proposition dans `etat/staging/` ; `scripts/appliquer.py` l'applique après validation. Le tick n'écrit jamais dans `etat/` tout seul.
- **Le brouillard** — la vérité du monde et ce que le joueur en sait sont deux choses. Les nouvelles arrivent en retard et déformées (`etat/info.json`) ; la carte (`etat/jetons.json`, `etat/vues.json`) porte des croyances, pas des positions réelles, avec leur `certitude` — la pièce se délave et se troue. Les PNJ subissent le même brouillard : leurs têtes vivent dans `etat/intentions.json` et ne changent que par une nouvelle reçue.
- **Les trois boucles** — les **mains** (`etat/mains.json` : ce qui avance sans qu'on décide, pure arithmétique), les **absents** (`etat/intentions.json` : ce qu'on apprend, ce à quoi on réagit, ce qu'on poursuit), la **salle** (à chaque battement on élit qui a la plus forte raison d'agir — et « rien » est une réponse valable). Plus la boucle des **pensées** : un conseiller ne parle que s'il a réellement appris quelque chose ce jour-là (`etat/pensees.json`), et il n'a le temps d'apprendre que dans les **creux** que sa journée lui laisse.
- **Les acteurs jouent leur propre journée** — aucune parole de PNJ n'est écrite de la main du MJ. On dépêche l'homme (`scripts/depecher.py`), il vit sa journée dans sa propre session, et il rentre avec ce qu'il a trouvé — y compris de quoi vous contredire. `scripts/parloir.py` permet de lui parler *pendant* qu'il travaille : ~23 s aller-retour.
- **Le décor** — plusieurs échelles commutables : le royaume (table peinte, filtres Armes · Dragons · Plis · Plan · Liens · Têtes), la ville, le terrain (`etat/terrain.json` — les formations vues du dessus, le rapport de force lisible sans chiffre), le château salle par salle (`ecrans/modules/plans.js`), les livres (`etat/books.json` — ouvrables pour de vrai, posés sur une table ou portés par quelqu'un), et un monde 3D (`ecrans/monde3d.html`) où lieux et corps ont une adresse physique (`etat/corps.json`, `scripts/affecter.py`, `scripts/marche.py` pour les distances réelles en mètres, en pas et en minutes).
- **Les annales** — `etat/annales.json` : ce que l'Histoire retient. Une ligne rouge et or barre le fil, coiffée de « Il s'est passé ». C'est acquis ; aucune scène future ne peut le contredire.
- **Les sièges** — `etat/joueurs.json` : plusieurs personnages jouables, chacun avec son inbox, son horloge et ses croyances. On s'assied et on se relève avec `scripts/sieges.py` ; un siège quitté doit avoir une tête, sinon il dort. À deux joueurs, un MJ par joueur, partagé par casting et non par pièce (voir `CLAUDE.md`).

## Structure

- `CLAUDE.md` — manuel du MJ, chargé par Claude à chaque session.
- `docs/schema.md` — source de vérité du format des données. **Ne jamais le modifier.**
- `docs/experience.md` — la même chose vue du joueur : ce qu'on voit, ce qu'on tape, ce que ça fait.
- `docs/parties.md` — idées de parties : sièges à ouvrir, angles, campagnes.
- `docs/metier.md` — le manuel qu'on met entre les mains d'un homme qu'on dépêche.
- Notes de conception : `carte.md`, `books.md`, `corps.md`, `mains.md`, `travaux.md`, `plis.md`, `plans-den-face.md`, `journees.md`, `sieges.md`, `boucle-acteurs.md`, `decoupage.md`, `ouvrir-une-maison.md`.
- Prompts de sessions annexes : `session-moteur.md` (le calcul), `siege-voix.md` (le second joueur). Les journées d'hommes vivent dans `boucle-acteurs.md`.
- `etat/*.json` — l'état du monde : monde, maisons, personnages, relations, lieux, événements, info (ce que le joueur sait), paroles, actes, intentions (têtes des PNJ — jamais montrées), mains, travaux, plis, jetons, vues, books, annales, journal.
- `ecrans/` — la page de jeu (`jeu.html`, `jeu.css`) découpée en modules JS (`ecrans/modules/`, un type d'item = un module), le monde 3D, les portraits, la console d'admin.
- `serveur/serveur.js` — sert la page, le flux, les entités, la carte, les livres, les voix ; reçoit les actions du joueur.
- `scripts/` — outils du MJ : `append_flux.py`, `tick.py`, `appliquer.py`, `ajouter.py`, `veille.py`, `sieges.py`, `guetteur.sh`, `depecher.py`, `parloir.py`, `presence.py`, `evaluer.py`, `dossier.py`, génération de portraits, de voix et de chansons, monde 3D et distances.

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

```bash
python scripts/veille.py mj
```

```bash
python scripts/dossier.py --sur <id>
```
