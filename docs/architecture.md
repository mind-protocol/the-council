# L'architecture du Conseil — containers, modules et liens

Même convention que `batailles/src/CLAUDE.md` : des **containers** à intention
d'une ligne, leurs **modules** réels (fichiers existants, pas de vœux), les
**liens** qui les traversent, et les frontières qui font que le système tient.
La différence de nature avec `batailles` : ici les « processus » sont pour
moitié des **sessions LLM** (le MJ, les dépêchés), et la mémoire de tout le
monde est **le disque** — jamais la conversation.

## Les huit containers

| Container | Où | Intention en une ligne |
|---|---|---|
| 🗄️ **État** | `etat/` | La seule vérité : un fait qui n'y est pas écrit n'existe pas |
| ⏱️ **Arithmétique** | `tick.py`, `appliquer.py`, `etat/staging/` | Possède le temps hors-scène ; calcule et propose, ne décide jamais |
| 🧠 **Agents** | `depecher.py`, `boucle_activation.py`, `sieges.py`, sessions PNJ | Les SIÈGES, humains comme PNJ : un point de vue servi, des actes reçus, un fil propre, un brouillard — deux profils (scène / journée), une machinerie |
| 🗣️ **Parloir** | `parloir.py`, `etat/parloir/`, hooks `PostToolUse` | Le fil régie↔agent pendant qu'une session vit — hors fiction |
| 🎭 **MJ** | session Claude + `CLAUDE.md`, demain `claude -p` + manuel par rôle | Une FAMILLE d'arbitres devant des sièges : principal ou de zone, interactif ou dépêché — élit, met en scène, arbitre ; n'invente jamais une parole |
| 📜 **Flux & Rendu** | `append_flux.py`, `etat/flux.jsonl`, `serveur/`, `ecrans/modules/` | Ce que le joueur voit : append-only, curseur client, une page persistante |
| 📥 **Inbox** | `etat/inbox/`, `guetteur.sh` | Les actes du joueur qui réveillent le MJ ; rien d'autre ne le réveille |
| 📐 **Doctrine** | `docs/` | Les contrats : `schema.md` (format, intouchable), `agents/prompts/metier.md`, `carte.md`, les fiches de conception |

## Les modules par container

### 🗄️ État
- **Le monde vrai** : `monde.json`, `personnages.json`, `lieux.json`, `evenements.json`, `chemins.json`, `corps.json`, `presence.json` (résolu par `presence.py`).
- **Ce qui s'est passé** : `actes.json`, `paroles.json`, `annales.json` — avec `temoins`/`connu_de` exacts.
- **Ce que chacun croit** : `intentions.json` (têtes des absents), `info.json` (ce qui est parvenu au joueur), `jetons.json`/`vues.json` (la table de guerre, croyances datées), `diffusion` dans les événements.
- **Ce que chacun a écrit** : `books/` (un fichier par volume), `pensees.json`, `conclusions.json`, `rapports/` (le dernier rendu de chaque homme), `archive/travaux/` (les journées passées).
- **Les mesures** : `mains.json`, `horloges.json`, `leves.json` — l'arithmétique sans opinion.
- **Les sièges** : `joueurs.json`, `joueurs/<id>/` (brouillard par siège), `voix.json`.
- **La trace des injections** : `depeches/` — le prompt réellement reçu par chaque session dépêchée, archivé avant l'appel.

### ⏱️ Arithmétique
- `tick.py` — horloges décomptées, échéances, diffusion à livrer, `--verifier` (les gardes : têtes en retard, `pour` absents, clés hors schéma).
- `appliquer.py` — le **vocabulaire fermé** des mutations : valide tout, refuse si l'empreinte a bougé, écrit atomiquement.
- `etat/staging/` — les propositions en attente d'arbitrage ; personne n'écrit l'état « en passant ».
- Satellites : `occupation.py`, `evaluer.py` (feuille de route : qui a du temps), `criticite.py` (l'ordre des cahiers), `presence.py` (le quartier).

### 🧠 Agents
- `depecher.py` — le chemin manuel : brief (`dossier_journee`), manuel système (`manuel_de`), session `claude -p`, retour (`verser_sur_le_champ`, `proposer_la_tete`).
- `boucle_activation.py` — le chemin automatique : mêmes briques, activation bornée à une tâche.
- **La mémoire d'un agent est la greffe documentaire** : son brief porte ses travaux ouverts, ses quatre dernières pensées par travail et sa dernière conclusion écrite de sa main (`travaux_ouverts_de`, lecteur canonique unique pour les deux chemins). `intentions.json` ne porte pas sa mémoire — voir Propositions.

### 🗣️ Parloir
- `parloir.py` — fils nommés `de~a.jsonl`, écoute par hook `PostToolUse` (bat après un appel d'outil, pas au temps).
- La règle : on transmet la **question** et les **faits**, jamais la réplique. Rien de ce qui s'y dit n'entre dans l'état par lui-même.

### 🎭 MJ
- La session Claude qui tient le manuel (`CLAUDE.md`) : boucle d'élection de la salle, boucle hors-scène, boucle des mains — dans cet ordre.
- Ses gestes d'écriture passent par `ajouter.py` (une entrée à la fois), `append_flux.py` (le fil), `appliquer.py` (les lots) ; `veille.py` avant d'écrire à deux plumes.
- À plusieurs joueurs : un MJ par joueur (`docs/sieges.md`), le principal garde `monde.json`, `tick.py`, le canon.

### 📜 Flux & Rendu
- `append_flux.py` — estampe l'heure, avance la montre, refuse les murs (`tunnel.py`), inline les portraits.
- `serveur/serveur.js` (port 3129, unique) — sert `/scene` cumulé, `/entites`, la régie.
- `ecrans/modules/` — un type d'item = un module (galerie, paroles, gestes, carte, jetons, books, echiquier, terrain, ville…).

### 📥 Inbox
- La page POSTe → `etat/inbox/<siège>/action-*.json` ; `guetteur.sh` (réarmé en premier geste du tour) réveille le MJ ; lecture de TOUT, traitement, suppression.

### 📐 Doctrine
- `schema.md` — le format, jamais modifié par personne.
- `agents/prompts/metier.md` — le manuel qu'on met entre les mains d'un dépêché (autonome).
- Les fiches de conception : `boucle-acteurs.md`, `mains.md`, `criticite.md`, `carte.md`, `books.md`, celle-ci.

## Les liens — une boucle à deux profils, plus le temps

**L'invariant du siège** (décision du 30, gravé aussi dans [`organisation.md`](organisation.md)) : un acteur — humain ou PNJ — est un **siège**. Quatre choses le font : un *point de vue servi* (la scène rendue / le brief), un *canal d'action* (l'inbox / les écrits + propositions), un *fil propre* (le flux par siège / le vécu), un *brouillard* (`info.json` / croyances + diffusion). Les deux anciennes boucles (« jeu » et « agents ») sont donc **la même boucle**, vue sous deux profils : le **profil scène** (cadence en minutes, rendu mis en scène) et le **profil journée** (cadence en journées, dossier). *Laisser faire* est la bascule de profil d'un siège humain.

```mermaid
flowchart LR
    subgraph BOUCLE["LA boucle des sièges — deux profils"]
        SJ["💺 siège · profil SCÈNE<br/>(le joueur)"] -->|"actes : POST 📥 inbox"| MJ["🎭 MJ<br/>principal / de zone<br/>interactif / dépêché"]
        MJ -->|"point de vue : 📜 flux (append_flux)"| SJ
        MJ -->|"point de vue : brief (depecher / activation)"| SP["💺 siège · profil JOURNÉE<br/>(le PNJ en session)"]
        SP -->|"actes : écrits rendus + tête proposée → staging"| MJ
        MJ <-->|"🗣️ parloir (hors fiction)"| SP
    end
    subgraph TEMPS["Boucle du temps (hors scène)"]
        T[⏱️ tick] -->|proposition| S[etat/staging]
        S -->|arbitrage MJ| AP[appliquer]
        AP -->|vocabulaire fermé + empreintes| E[(🗄️ État)]
    end
    SP -->|pensées, conclusions, cahiers| E
    E -->|"fil propre : flux par siège / vécu"| SJ
    E -->|"fil propre + greffe documentaire"| SP
    D[📐 Doctrine] -.->|"un manuel par rôle (metier.md, demain mj-zone.md)"| MJ
    D -.metier.md.-> SP
```

- **La boucle des sièges** : point de vue servi → actes → arbitrage → état → point de vue. Un siège ne parle jamais à l'état ; l'arbitre ne parle à un siège que par son point de vue. Vraie pour le joueur (c'était la « boucle de jeu ») comme pour le PNJ (c'était la « boucle des agents »).
- **Ce qui distingue les profils, et rien d'autre** : la cadence (minutes de scène / journées), le rendu (mise en scène / dossier), et la Règle Zéro (les paroles du PNJ sont protégées par la dépêche ; le joueur écrit les siennes librement).
- **Boucle du temps** : tick → staging → arbitrage → appliquer. Le tick ne décide rien ; appliquer ne juge rien ; le MJ fait les deux et n'écrit rien directement. Inchangée : le temps n'est pas un siège.
- **Les joueurs multiples ne sont plus une boucle à part** : *n* sièges de profil scène, un MJ par siège humain (parloir entre régies `mj` ↔ `mj-<joueur>`), un seul possesseur du temps.
- **Le vécu** (à venir — voir `organisation.md`, table des features) : le fil propre du profil journée, symétrique du flux par siège — un index chronologique ancré, jamais une source.

## Frontières strictes (les invariants qui font tenir le tout)

1. **Un fait n'existe que dans 🗄️ État.** La conversation du MJ, le parloir, le widget : tout est périssable — les fichiers ont toujours raison.
2. **Deux frontières autour de la cognition de TOUT siège** (le miroir exact de `batailles`, élargi par l'invariant du siège) : un siège ne voit le monde qu'à travers son point de vue servi (le brief + ses outils pour le PNJ ; `info.json` et le flux pour le joueur — c'était déjà vrai sans être dit) ; il n'agit sur l'état que par son canal d'actes (écrits rendus + propositions / inbox) — jamais d'écriture directe.
3. **Une seule porte d'écriture arbitrée** : tout ce qui mute des croyances ou des horloges passe par staging + `appliquer.py` (vocabulaire fermé, empreintes). `ajouter.py` pour les entrées simples. La réécriture de tableau à la main est l'exception qui perd les gardes.
4. **Le brouillard est par siège et par tête** : `info.json` et `diffusion` sont les seuls canaux par lesquels une croyance change. *(Frontière vraie pour les personnages, poreuse pour le parloir — voir Propositions.)*
5. **Le flux est append-only et la montre lui appartient** : `append_flux.py` est le seul à faire avancer `monde.date.minute`.
6. **La Règle Zéro** : le MJ n'écrit jamais la parole d'un PNJ — il dépêche.

---

## Propositions

Numérotées dans l'ordre où je les poserais. ①② sont **posées** (30 août) ;
le reste est à décider.

### ① ✅ La greffe documentaire servie à l'entrée *(fait)*
`travaux_ouverts_de()` dans `depecher.py`, branché dans les DEUX chemins
(le `travaux = []` de la boucle d'activation était codé en dur : aucun agent,
par aucun chemin, ne recevait ses propres écrits avant ça). Un homme reprend
là où sa plume s'est arrêtée. Complément posé le même soir : `etat/depeches/`
archive le prompt réellement injecté, avant l'appel.

### ② ✅ La tête tenue par proposition, plus par zèle *(fait)*
`proposer_la_tete()` au retour de chaque dépêche : `date_maj` seul en
mutation (l'arithmétique), la matière jointe pour que le MJ ajoute étapes et
croyances, empreinte sha1, un fichier par homme et par jour. Le coût de la
tenue passe de « penser à le faire » à « refuser de le faire ». Cause
traitée : treize têtes en retard au 30 août, `date_maj` gelé huit jours chez
un agent qui s'auto-corrigeait neuf fois par écrit.

### ③ L'ancre au parloir — fermer le blanchiment de connaissance
Le trou mesuré : une seule entrée `info.json` pour Hask contre ~30 faits
transmis au parloir. Gradué, jamais bloquant : `parloir.py --dire --de mj
--ancre <info_id|acte_id|ligne>` ; un fait du monde sans ancre est **marqué**
(`sans_ancre: true`) ; `parloir.py --audit` liste les faits non ancrés par
fil. Effet de bord : le bug Rulf (le MJ affirme puis contredit à 21 minutes
d'écart, l'agent bâtit sur la version fausse) devient détectable
mécaniquement — deux messages ancrés sur le même objet se comparent.

### ④ `intentions.json` rétrogradé en contrat machine
Ce que la machine exécute reste (plan + horloges + `si_bloque`,
`declencheurs`, `mandat`) ; ce que l'homme se rappelle sort (`croyances` →
cahiers et pensées, où c'est déjà). `date_maj` cesse de mimer la fraîcheur
d'une mémoire : il date un contrat. Touche `docs/schema.md` → sa propre
passe, avec migration.

### ⑤ Un seul constructeur de dossier pour les deux chemins
`dossier_journee()` (manuel) et `dossier_activation()` (boucle) recouvrent
80 % des mêmes lectures avec deux codes. ① a unifié les travaux ; finir le
geste — un seul builder, deux profils (journée / activation bornée) — pour
que le prochain champ ajouté ne manque plus jamais d'un côté. C'est le
défaut qui a produit ① : un champ existant, servi nulle part.

### ⑥ L'hygiène des snapshots `.avant-*`
Soixante-quinze `books.json.avant-*` à la racine d'`etat/`, et l'audit du
30 août a montré leur limite : trois snapshots d'`intentions.json`
identiques, aucun ne couvrant la fenêtre utile. Proposition : un
`scripts/sauver.py` unique (dossier `etat/archive/instantanes/<table>/`,
horodatage, motif obligatoire, rotation), et la racine d'`etat/` redevient
lisible. Purge des existants après vérification qu'aucun n'est le seul
porteur d'un état voulu.

### ⑦ Le détecteur de rétractation manquante *(dépend de ③)*
Sur le log du parloir ancré : un fait affirmé par le MJ puis contredit par
lui dans le même fil, sans message de rétractation adressé à l'agent entre
les deux → une ligne au rapport d'audit. Trois requêtes sur un log, pas de
l'IA. C'est la classe du bug Rulf : une croyance fausse entrée dans la
chaîne d'un agent rigoureux et jamais retirée.
