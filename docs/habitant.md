# Le modèle habitant — chambres, réveils, un seul MJ

Conçu le 30e jour de la 8e lune 2026, en une soirée : deux essais vécus (les réveils
de Gerardys), une mesure de concurrence, et sept inversions successives. Ce document
est la vérité du design ; le diagramme vivant est la page « Qui réveille qui »
(artifact), et le chantier d'implémentation est en fin de fiche.

---

## 1. Le mindset — l'homme cesse d'être un appel pour devenir un habitant

L'ancien modèle était une RPC : un prompt assemblé, une passe atomique, un rapport
JSON à parser, un répertoire jetable (`mkdtemp`). Le nouveau est presque le modèle
Unix : **chaque être pensant a un domicile, des fichiers qu'il reprend, des canaux
vers ceux qu'il connaît, et une session qui est sa mémoire.**

- **Tout ce qui pense est un habitant** : les hommes et l'unique MJ. Même
  machinerie de réveil, même chambre, mêmes canaux. Le joueur est
  l'exception qui confirme : sa « chambre » est son navigateur, sa session c'est lui.
- **La chronologie d'exécution est libre** (l'anachronisme) : on peut jouer la
  journée d'hier aujourd'hui, deux moments d'un même homme en parallèle. Ce n'est
  pas 100 % juste informationnellement — c'est good enough, et l'état réconcilie.
  Prouvé vécu : Gerardys ré-réveillé le même jour a trouvé « une autre main » —
  la sienne — dans le registre, et l'a confrontée sans drame.
- **Le travail est itératif** : on rature dans ses brouillons, on reprend, on ne
  rend que le propre. Le rapport JSON de fin de session disparaît : le retour d'une
  journée, c'est l'état de sa chambre plus ses versements — et sa **conclusion pour
  lui-même** : ce que la journée a changé, ce qu'il compte faire ensuite. Elle ne
  s'adresse à personne d'autre (toute parole au monde passe par un canal réel) ;
  elle s'écrit dans sa chambre (`demain.md`) et son prochain réveil s'ouvre dessus —
  « là où tu t'étais laissé ». La boucle de continuité est physique, décidé le 30.8.

## 2. La chambre — le domicile

```
chambres/<id>/                     habitants humains et unique MJ (`mj`)
   claude.md                       sa manière, DE SA MAIN — seedée une fois depuis la
                                   fiche, plus jamais touchée par nous ; sa dérive est
                                   la personnalité qui évolue (pour un MJ : son style)
   problemes.json                  les pannes de l'APPAREIL — semé vide, règle en tête
   en-souffrance.json              ses fils ouverts : ce qu'il attend de qui, et
                                   depuis quand ; ce qu'on attend de lui — semé vide
   fil/                            les traces de ses sessions — le vécu, relisible
                                   `<date>-salle.md` : ce qu'il a entendu là où
                                   il se tenait, écrit à la poussée du flux
   books/                          ses volumes, toujours sous sa main
   brouillons/                     l'itératif — ce qui mûrit avant de se verser
   relations/<autre>/
      claude.md                    ce que LUI retient de l'autre — subjectif,
                                   asymétrique (MA fiche sur toi ≠ ta fiche sur moi)
      discussion.json              le canal — canonique chez l'un des deux
                                   (ordre lexical des ids), l'autre y accède
```

**La seule règle, et elle est de géographie : rien dans `chambres/` ne fait foi.**
La chambre est de la mémoire et du caractère ; la vérité vit dans `etat/`, et tout
ce qui doit devenir vrai s'écrit dans `etat/`. Une chambre peut se tromper sur le
monde ; c'est même son droit.

**Les deux JSON sont une invention d'habitant, promue au template.** Le mestre
les a ouverts de sa propre main, sans que rien ne les lui demande, et ils tiennent
tous deux ce qu'aucune autre table ne tient. `problemes.json` sépare les pannes de
la MACHINE des empêchements du monde — ceux-là sont des verrous et vont au
registre ; ses deux entrées sont un versement refusé en silence et sept
coordonnées qui n'ont jamais atteint la file, et sa conclusion vaut d'être citée :
*« un refus se voit quand on regarde, une absence ne se voit même pas quand on
regarde »*. `en-souffrance.json` compte les GENS qui n'ont pas répondu et depuis
quand, là où le plan ne compte que des pas — *« ce n'est pas la même chose et cela
ne se calcule pas »*. On les sème donc **vides, avec leur règle en tête et pas une
entrée** : la doctrine est de nous, le contenu est de lui. Ils se lisent par
`chambre.problemes(qui)` et `chambre.en_souffrance(qui)`, et ce que le réveil en
sert va **en percept**, comme les billets — jamais en invitation à ouvrir un
fichier.

**Ce qui se dit devant lui entre chez lui, et la co-présence ouvre les relations.**
`agents/salle.py`, appelé par `scene/flux.py` au moment de la poussée — le seul
endroit qui tienne à la fois la pièce, la présence et le texte. Deux écritures, un
seul calcul (qui est dans la pièce), et **le filtre est la chambre** : on ne recopie
rien chez qui n'en a pas, et deux co-présents n'ouvrent une relation que s'ils en
ont une tous les deux. Sans ce filtre, un conseil de treize présents écrivait treize
copies de chaque réplique et ouvrait cent cinquante-six dossiers ; avec lui, la
charge grandit au rythme où l'on ouvre des chambres — et en ouvrir une devient un
geste qui a un effet. Mesuré sur un parc jouet : à 20 habitants un réveil lit ses 19
relations en 5,8 ms, à 100 en 19 ms.

Trois règles dures, tenues par `scripts/tests/test_salle.py` : **le chuchotement ne
fuite pas** (`--messe-basse` prime sur la pièce, le tiers présent n'en a pas une
ligne) ; **le hors-fiction n'est entendu de personne** (une `pensee` ne coûte pas
une minute justement parce que nul ne l'entend) ; **la fiche de relation porte un
constat daté, jamais un jugement** — elle est « ce que LUI retient de l'autre », lui
écrire une opinion serait tenir sa main. On accumule pendant la poussée et l'on
écrit une fois par chambre à la fin : item par item, quarante répliques dans une
salle de vingt feraient huit cents ouvertures de fichier dans la plume de l'horloge.

`chambres/` vit à la racine du dépôt, versionné comme `etat/` : la mémoire des
habitants fait partie de la partie. Les fils `~mj` d'`etat/parloir/` migrent vers
les `relations/` à mesure que les chambres s'ouvrent — une conversation n'est pas
de la vérité, elle n'avait rien à faire dans `etat/`.

## 3. Les gestes — le PNJ agit, le joueur demande l'arbitrage

Un PNJ en journée n'a aucun canal vers le MJ. Il lit ses sources, agit dans la
mesure de ses moyens et écrit ce qu'il a réellement accompli. Si l'issue dépend
d'un autre, du hasard ou d'un fait absent, il laisse la conséquence en attente
sans l'inventer. Les verbes synchrones vers `mj` appartiennent uniquement au
front d'un joueur et portent le marqueur technique `--joueur`.

| geste | ce que c'est | résolution |
|---|---|---|
| **PARLER** — « Maître Hask, … » | une parole adressée | billet à un habitant + réveil cast ; jamais vers le MJ pour un PNJ |
| **AGIR** — « je pars sur mon cheval », « je déplace ce livre » | un geste qui engage le monde | le PNJ écrit le geste accompli ; l'issue hors de sa portée reste en attente |
| **PENSER** — « et si la roue… » | un réveil de soi-même | ça reste en chambre, sans arbitre |
| **CHERCHER** — « l'histoire de ceci ? » | apprendre ce que le monde sait | lire une source ou écrire à une personne ; sinon conserver l'inconnu |
| **INTERVENTION** — la main par-dessus | hors fiction : on répare, on ne joue pas | réservé au siège de régie (joueur/dev), jamais un geste d'homme dépêché |

Les billets entre hommes entrent dans le brief **en percept** — « Hask t'a écrit :
"…" » — jamais comme une invitation à ouvrir un fichier (leçon des essais : 2/2
ignorée sous la pression de l'élan).

## 4. Le runtime — la règle en quatre lignes

> **Tout habitant peut écrire à tout habitant, n'importe quand, en parallèle.**
> **Les sessions sont de la mémoire ; la mémoire supporte le désordre** — c'est l'anachronisme.
> **La vérité vit dans l'état** — les habitants y écrivent directement.
> **Chaque réveil porte son moment** — la date, le creux, « qui te réveille » : une étiquette, jamais un verrou.

Mesuré (trois réveils-jouets) : deux `--resume` concurrents sur la même session
réussissent tous deux, même id, transcript unique aux branches entrelacées — pas de
verrou natif, pas de crash. Pour le **MJ**, l'entrelacement ne porte plus que
les audiences des joueurs. Pour un **homme**, deux réveils simultanés sont deux moments de sa vie joués
en désordre — ce que l'anachronisme accepte déjà. Personne n'est sérialisé.

### Call et cast — la synchronicité se décide par arête, jamais par système

> **On APPELLE quand on a besoin de la réponse pour continuer** (sync — le `-p`
> imbriqué est le mécanisme d'attente, la réponse est un retour de commande).
> **On DÉPÊCHE quand on lance une vie** (détaché — la suite arrive par les canaux).

| arête | mode |
|---|---|
| lancer une journée, une activation | cast |
| écrire un billet à un absent | cast (et l'écriture RÉVEILLE le destinataire — le geste d'écrire est le réveilleur, aucun démon) |
| joueur → MJ : geste du front | **call** — le verdict revient à l'interface |
| MJ → homme : une réplique doit sortir (Règle Zéro) | **call** |

Filet des cycles d'appels : les arêtes sync sont courtes et dirigées ; le timeout
du `-p` suffit.

Un appel d'homme peut nommer l'item d'affaire qu'il sert :

```bash
python scripts/depecher.py --qui gerardys --contexte 23030 --mission "..."
```

Le drapeau `--mode` choisit les instructions, sans changer l'identité de
session ni le contexte :

```bash
python scripts/depecher.py --qui gerardys --contexte 23030 \
  --mode reponse --mission "Quel est le chiffre ?"
```

- `reponse` : le résultat revient comme dernière réponse du call ;
- `discussion` : le résultat passe par la commande de canal fournie dans la
  demande ; le routeur des paroles choisit ce mode automatiquement ;
- `journee` : mode conservé par défaut.

Chaque chambre possède `messages-au-joueur.md`. En `journee`, l'habitant y
prépare les messages que ses affaires appellent, avec destinataire, contexte,
ref, faits vérifiés et mots proposés. Le cahier n'est pas un canal : rien de ce
qui y est écrit n'est encore dit. En `reponse` et `discussion`, l'entrée
pertinente est relue comme brouillon, ses faits sont revérifiés, puis le mode
applique sa règle de transport.

Les deux premiers modes sont des calls attendus : ils refusent `--cast`.

Le contexte désigne le **numéro de la pièce** dans une affaire générale.
`23030`, `#23030`, `n° 23030`, `Nº23030` et la forme Markdown `**23030**`
sont normalisés vers la même adresse canonique `23030`. Un nom de volume ou
`affaire-…#P.3` n'est pas une adresse ; deux numéros distincts dans la même
entrée sont refusés comme ambigus. Ce numéro est global : les affaires le
rendent dans leur première colonne `N°` et le plan refuse qu'il soit pris
ailleurs. Sans `--contexte`, la session reste celle de
l'homme pour le jour de jeu. Avec `--contexte`, elle est stable par couple
homme/item, même lorsque le jour change.
Chaque item possède aussi son propre fil sous
`chambres/<homme>/fil/contextes/<N°>/` : logs, vécu et mot de reprise ne se
mélangent plus avec ceux d'une autre affaire.

Le même numéro focalise le dossier : l'homme reçoit la pièce demandée, son
cahier source, son état, sa preuve attendue et la chaîne ascendante jusqu'à
l'état qu'elle sert. Ses autres trous, attentes et inventaires de chambre ne
sont pas injectés dans cet appel.

### Les rôles

- **Un seul MJ, nommé `mj`.** Sa session est continue (`--resume`) : il tient
  ses fils et son réveil ne porte que « qui te réveille, et voici son mot ».
  Le lieu d'un homme reste une donnée de fiction ; il ne fabrique ni autorité,
  ni session, ni chambre supplémentaire. Le MJ tient le spectacle et la montre.
- **Le guetteur meurt.** Le serveur (seul processus permanent) lance
  `claude -p --resume <mj>` sur le POST du joueur — l'unique MJ est un habitant
  comme les autres. La supervision devient un siège : `claude --resume <mj>` en interactif
  quand le dev veut piloter, rendu en sortant.
- **Aucune élection automatique.** Le tick ne réveille personne : il propose.
- **Le MJ se réveille seulement sur un POST joueur, un verbe du front marqué
  `--joueur`, ou une intervention de `dev`.** Une dépêche explicite appelle les
  hommes directement ; elle ne crée aucun narrateur géographique intermédiaire.
- **`dev` est un nom réservé** (31.8) : le développeur est un habitant adressable
  — sa chambre est `chambres/dev/`, on lui écrit un billet (`--a dev`), on lui
  assigne des actions (« Qui : dev »). Il n'est jamais dépêché (pas de fiche,
  pas de journée) : ses réveils sont ses sessions de travail réelles. Aucun
  personnage du monde ne peut porter cet id.

### Prévoir et rattraper — par destination d'écriture

> On **prévoit librement tout ce qui reste chez lui** (vécu, brouillons, mémoire,
> canaux) — c'est du capital, jamais du risque.
> On **ne rattrape que ce qui entre dans l'état** — la vérité se consolide à la
> demande, datée, arbitrée.

Une journée jouée que rien ne consomme n'est plus du travail jeté : c'est de la
mémoire de l'homme. Le speculatif capitalise ; seule la consolidation attend son
échéance.

## 5. Ce que les essais ont mesuré (et qui gouverne l'implémentation)

| leçon | mesure |
|---|---|
| Le pas-de-tir neutre gagne (variante B) | naître dans le dépôt coûte ~+50 k jetons/tour (le manuel racine remonte par la découverte) ET expose aux hooks du projet |
| La sandbox des calls n'a pas fait ses preuves (tranché le 31.8) | Le mode `--restricted` a été retiré : les habitants sont lancés avec accès au dépôt. Le vécu reste déposé par le lanceur (`trace.deposer`), car cette mémoire ne doit pas dépendre d'un hook de fournisseur. |
| Le billet-fichier ne suffit pas | 2/2 ignoré sous la pression de l'élan → billet en percept dans le brief |
| L'appel homme→MJ concentrait la dépendance | ancienne mesure : 3/3 premiers gestes allaient au MJ ; ce résultat motive désormais son retrait, pas sa conservation |
| Le rapport JSON est un artefact RPC | il disparaît au profit des écrits de chambre + versements + une phrase |
| `--resume` interactif d'une session `-p` | à mesurer (une minute) — c'est le mécanisme du siège de supervision |

## 6. Le chantier — les étapes de l'implémentation

Chaque étape est commitable et se vérifie par un réveil-banc. Le code vit dans le
container `agents/` ; `chambres/` est de la donnée.

1. **`agents/chambre.py` + `agents/mj.py`** — le domicile commun et le réveil
   de l'unique MJ, électeur-greffier, jamais auteur de la parole d'un PNJ.
2. **Le lancement** (`depeche/mission.py`) — chambre et dépôt accessibles,
   outils +Write/Edit, accès direct sans sandbox, spawn détaché pour les casts.
   Le hook-oreille du
   parloir, qui vivait en sursis par `--settings`, est mort le 31.8 : les canaux
   des chambres ont pris la relève — plus personne n'entend en cours de session.
3. **Le brief** (`depeche/brief.py`) — section chambre au chemin absolu, billets en
   percept, claude.md perso joint au système, le gabarit JSON retiré. → **réveil-banc
   n°3** : le billet-percept est-il répondu ?
4. **La frontière joueur/PNJ** (`metier.md` + `parloir.py` + `mj.py`) —
   les appels synchrones vers `mj` exigent `--joueur` ; un PNJ cherche, agit
   ou conserve l'inconnu sans réveiller le MJ.
5. **Écrire = réveiller** — `--dire` spawn le destinataire détaché ; le serveur
   lance le MJ sur POST ; le guetteur s'éteint. → **réveil-banc n°5** : un ping-pong
   homme↔homme réel.
6. **Le vécu** (`agents/trace.py`, appelé par le lanceur, indépendamment des hooks) — transcript + dépôt dans
   `fil/` ; `vecu.py --md` comme vue lisible. *(délégable)*
7. **Les migrations douces** — les fils `~mj` du parloir vers `relations/`, la
   dépêche manuelle branchée sur `chambre.ouvrir()` au premier réveil. *(délégable)*

Ce qui n'est PAS dans ce chantier : le lot 3 front (gate à trancher), le pont
`batailles` (les peaux), la boucle d'élection elle-même (elle sert telle quelle).
