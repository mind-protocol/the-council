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
| ⏱️ **Arithmétique** | `tick.py` | Calcule le temps hors-scène ; ne décide et n'écrit jamais |
| 🧠 **Agents** | `depecher.py`, `sieges.py`, sessions PNJ | Les appels explicites aux personnes : point de vue, journée demandée, fil et brouillard |
| 🗣️ **Parloir** | `parloir.py`, canaux des chambres | Les billets entre habitants ; retour vers un joueur au web et au flux d'entrée MJ, sans canal de requête PNJ→MJ |
| 🎭 **MJ** | `scripts/agents/mj.py` + session continue + `CLAUDE.md` | Une seule autorité de jeu : met en scène et arbitre ; n'invente jamais une parole |
| 📜 **Flux & Rendu** | `append_flux.py`, `etat/flux.jsonl`, `serveur/`, `ecrans/modules/` | Ce que le joueur voit : append-only, curseur client, une page persistante |
| 📥 **Inbox & sélection** | `etat/inbox/`, `selectionner_contexte.py`, `.agents-runtime/contextes/` | Chaque acte du joueur ouvre une sélection jetable avant toute autorité de jeu |
| 📐 **Doctrine** | `docs/` | Les contrats : `schema.md` (format, intouchable), `agents/prompts/metier.md`, `carte.md`, les fiches de conception |

## Les modules par container

### 🗄️ État
- **Le monde vrai** : `monde.json`, `personnages.json`, `lieux.json`, `evenements.json`, `chemins.json`, `corps.json`, `presence.json` (résolu par `presence.py`).
- **Ce qui s'est passé** : `actes.json`, `paroles.json`, `annales.json` — avec `temoins`/`connu_de` exacts.
- **Ce que chacun croit** : `intentions.json` (têtes des absents), `info.json` (ce qui est parvenu au joueur), `jetons.json`/`vues.json` (la table de guerre, croyances datées), `diffusion` dans les événements.
- **Ce que chacun a écrit** : `books/` (un fichier par volume), `pensees.json`, `conclusions.json`, `rapports/` (le dernier rendu de chaque homme), `archive/travaux/` (les journées passées).
- **Les mesures** : `maisons/<id>/documents/mains.json`, agrégées par la porte commune — l'arithmétique sans opinion.
- **Les sièges** : `joueurs.json`, `joueurs/<id>/` (brouillard par siège), `voix.json`.
- **La trace des injections** : `depeches/` — le prompt réellement reçu par chaque session dépêchée, archivé avant l'appel.

### ⏱️ Arithmétique
- `tick.py` — horloges décomptées, échéances, diffusion à livrer, `--verifier` (les gardes : têtes en retard, `pour` absents, clés hors schéma).
- Satellites : `occupation.py`, `evaluer.py` (feuille de route : qui a du temps), `criticite.py` (l'ordre des cahiers), `presence.py` (le quartier).

### 🧠 Agents
- `depecher.py` — le chemin manuel : brief (`dossier_journee`), manuel système (`manuel_de`), session `claude -p`, retour (`verser_sur_le_champ`).
- Il n'existe plus de chemin automatique : une personne travaille uniquement après une dépêche ou un message explicite.
- `selectionner_contexte.py` — première couche d'un POST joueur : session neuve sans reprise, sérialisée par siège ; reçoit cinq items visibles, le contexte précédent, les joueurs dans la salle, les personnes nommées, les candidats classés et les arbres `action → clef → verrou → état` de toutes les pièces détectées. Son système décrit le modèle d'affaire et porte tous les états cibles et verrous. Les messages faibles héritent du contexte précédent, sauf si le message courant nomme une personne : le nom devient alors une contrainte de routage et interdit `continuer`. Les noms présents seulement dans le fil restent du contexte. Une sélection non vide doit ancrer chaque pointeur par une citation du fil ; un incident multi-sièges impose une proposition de création. `joueurs_concernes` et `hommes` (PNJ seulement) restent séparés. Chaque homme est associé à un pointeur dans `routes_hommes`. L'artefact `selection-contexte/4` est écrit sous `.agents-runtime/contextes/`.
- `agents/routeur_message.py` — deuxième couche : toute action va au MJ sur sa seule `ref`. Pour `dire|parler`, les hommes sélectionnés reçoivent auparavant les mots exacts par une dépêche contextuelle ; le numéro après `#` devient le `contexte_id` stable de leur session et de leur fil. `contexte_id` et la `ref` d'origine sont propagés ensemble dans le prompt, son archive, l'environnement du runtime, la trace de session, le canal du parloir, la réponse web et le spool MJ. Le bilan est joint au réveil MJ pour interdire une seconde dépêche du même homme.
- **La mémoire d'un agent est la greffe documentaire** : son brief porte ses travaux ouverts, ses quatre dernières pensées par travail et sa dernière conclusion écrite de sa main (`travaux_ouverts_de`, lecteur canonique unique pour les deux chemins). `intentions.json` ne porte pas sa mémoire — voir Propositions.

### 🗣️ Parloir
- `parloir.py --dire` — billet au canal canonique de deux chambres, puis réveil du destinataire.
- Un PNJ peut écrire à un autre habitant, jamais au MJ. Les appels synchrones vers `mj` exigent le marqueur interne `--joueur` posé par le front.
- Exception de transport, pas d'autorité : si le destinataire est un siège joueur occupé, il n'est pas casté. Le billet devient immédiatement une `reponse` privée dans `etat/flux.jsonl` et une copie append-only sous `.agents-runtime/mj/retours-parloir.jsonl`. Le canal, la réponse et la copie portent le même `contexte_id` et la même `ref`. Le MJ la consomme à son prochain réveil avec la marque « déjà affichée » ; les arrivées pendant son appel restent après son curseur.

### 🎭 MJ
- La session Claude qui tient le manuel (`CLAUDE.md`) : boucle d'élection de la salle, boucle hors-scène, boucle des mains — dans cet ordre.
- Ses gestes d'écriture passent par `ajouter.py` (une entrée à la fois), `append_flux.py` (le fil), ou directement par les fichiers d'`etat/`.
- À plusieurs joueurs, les sièges partagent le même MJ et le même canon.

### 📜 Flux & Rendu
- `append_flux.py` — estampe l'heure, avance la montre, refuse les murs (`tunnel.py`), inline les portraits.
- `serveur/serveur.js` (port 3129, unique) — sert `/scene` cumulé, `/entites`, la régie.
- `ecrans/modules/` — un type d'item = un module (galerie, paroles, gestes, carte, jetons, books, echiquier, terrain, ville…).

### 📥 Inbox & sélection
- La page POSTe → `etat/inbox/<siège>/action-*.json` ; le serveur spawn `scripts/selectionner_contexte.py --de <siège> --ref <ref>` en détaché.
- Le sélecteur ouvre toujours une session neuve (`reprendre=False`), mais hérite explicitement du dernier contexte résolu pour les messages faibles. Il choisit ou propose le contexte, sépare joueurs et PNJ concernés, puis écrit `.agents-runtime/contextes/<siège>/<ref>.json`.
- Le routeur sert ensuite les hommes d'une parole dans leurs sessions d'item, appelle le MJ sur la `ref` exacte et lui joint les routes déjà servies. Les autres actions vont seulement au MJ. L'action reste dans l'inbox jusqu'à ce que le MJ ait réellement écrit au flux.

### 📐 Doctrine
- `schema.md` — le format, jamais modifié par personne.
- `agents/prompts/metier.md` — le manuel qu'on met entre les mains d'un dépêché (autonome).
- Les fiches de conception : `mains.md`, `criticite.md`, `carte.md`, `books.md`, celle-ci.

## Les liens — scène, appels explicites et temps

**L'invariant du siège** (décision du 30, gravé aussi dans [`organisation.md`](organisation.md)) : un acteur — humain ou PNJ — est un **siège**. Quatre choses le font : un *point de vue servi* (la scène rendue / le brief), un *canal d'action* (l'inbox / les écrits + propositions), un *fil propre* (le flux par siège / le vécu), un *brouillard* (`info.json` / croyances + diffusion). Les deux anciennes boucles (« jeu » et « agents ») sont donc **la même boucle**, vue sous deux profils : le **profil scène** (cadence en minutes, rendu mis en scène) et le **profil journée** (cadence en journées, dossier). *Laisser faire* est la bascule de profil d'un siège humain.

```mermaid
flowchart LR
    subgraph BOUCLE["LA boucle des sièges — deux profils"]
        SJ["💺 siège · profil SCÈNE<br/>(le joueur)"] -->|"actes : POST 📥 inbox"| SC["🔎 sélecteur de contexte<br/>session neuve"]
        SC --> RT["📨 routeur · ref exacte"]
        RT -->|"toute action"| MJ["🎭 autorité de jeu"]
        RT -->|"parler · contexte_id"| H["🧠 hommes sélectionnés"]
        H -->|"retours déjà servis"| MJ
        MJ -->|"point de vue : 📜 flux (append_flux)"| SJ
        MJ -->|"point de vue : brief (dépêche explicite)"| SP["💺 siège · profil JOURNÉE<br/>(le PNJ en session)"]
        SP -->|"actes et écrits rendus"| E[(🗄️ État)]
        SP -->|"🗣️ billets"| AH["autres habitants"]
    end
    subgraph TEMPS["Boucle du temps (hors scène)"]
        T[⏱️ tick] -->|calcul lu par les habitants| E
    end
    SP -->|pensées, conclusions, cahiers| E
    E -->|"fil propre : flux par siège / vécu"| SJ
    E -->|"fil propre + greffe documentaire"| SP
    D[📐 Doctrine] -.->|"CLAUDE.md + mj-spectacle.md"| MJ
    D -.metier.md.-> SP
```

- **La boucle des sièges** : point de vue servi → actes → état → point de vue. Un habitant écrit directement ce qu'il est le mieux placé pour tenir.
- **Ce qui distingue les profils, et rien d'autre** : la cadence (minutes de scène / journées), le rendu (mise en scène / dossier), et la Règle Zéro (les paroles du PNJ sont protégées par la dépêche ; le joueur écrit les siennes librement).
- **Boucle du temps** : tick calcule ; les habitants jugent et écrivent ce que ce calcul produit pour leurs affaires.
- **Les joueurs multiples ne sont plus une boucle à part** : *n* sièges de profil scène, un seul MJ et un seul possesseur du temps.
- **Le vécu** (à venir — voir `organisation.md`, table des features) : le fil propre du profil journée, symétrique du flux par siège — un index chronologique ancré, jamais une source.

## Frontières strictes (les invariants qui font tenir le tout)

1. **Un fait n'existe que dans 🗄️ État.** La conversation du MJ, le parloir, le widget : tout est périssable — les fichiers ont toujours raison.
2. **Le brouillard limite ce qu'un siège sait, pas ce qu'il peut écrire** : son point de vue reste servi ; quand il agit, il peut modifier directement `etat/`.
3. **Le brouillard est par siège et par tête** : `info.json` et `diffusion` sont les seuls canaux par lesquels une croyance change. *(Frontière vraie pour les personnages, poreuse pour le parloir — voir Propositions.)*
4. **Le flux est append-only et la montre lui appartient** : `append_flux.py` est le seul à faire avancer `monde.date.minute`.
5. **La Règle Zéro** : le MJ n'écrit jamais la parole d'un PNJ — il dépêche.
6. **Autonomie des PNJ** : un PNJ ne demande au MJ ni permission, ni information, ni verdict. Il agit, cherche dans le monde ou conserve l'inconnu.

---

## Propositions

Numérotées dans l'ordre où je les poserais. ①② sont **posées** (30 août) ;
le reste est à décider.

### ① ✅ La greffe documentaire servie à l'entrée *(fait)*
`travaux_ouverts_de()` dans `depecher.py`. Un homme reprend
là où sa plume s'est arrêtée. Complément posé le même soir : `etat/depeches/`
archive le prompt réellement injecté, avant l'appel.

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

### ⑤ Un seul constructeur de dossier
`dossier_journee()` est le constructeur unique des dépêches explicites.

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
