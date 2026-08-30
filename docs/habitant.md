# Le modèle habitant — chambres, réveils, arbitres

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

- **Tout ce qui pense est un habitant** : les hommes, les MJ de zone, le MJ du
  joueur. Même machinerie de réveil, même chambre, mêmes canaux. Le joueur est
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
chambres/<id>/                     hommes ET mj (mj, mj-peyredragon, mj-portreal…)
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
ce qui doit devenir vrai passe par la porte (`tables`, versements, staging) — la
garde `porte-etat` le tient déjà mécaniquement. Une chambre peut se tromper sur le
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

## 3. Les verbes — l'accès de l'homme au monde

Un homme en journée a trois verbes vers son arbitre, symétriques des boutons du
joueur (prouvé nécessaire : 3/3 réveils d'essai, son premier geste de communication
fut `parloir --dire --a mj`) :

**Le lexique est UNIQUE et c'est celui du joueur** (normalisé le 31.8 — un seul
nom par geste, l'homme et le joueur font les mêmes) :

| geste | ce que c'est | résolution |
|---|---|---|
| **PARLER** — « Maître Hask, … » | une parole adressée | vers un arbitre : call ; vers un homme : billet au canal + réveil cast |
| **AGIR** — « je pars sur mon cheval », « je déplace ce livre » | un geste qui engage le monde (absorbe l'ancien TENTER **et** FAIRE) | l'arbitre tranche en coulisse — issue incertaine : il décide ; mutation mécanique : proposition → staging |
| **PENSER** — « et si la roue… » | **un réveil de soi-même** : la pensée est un cast à soi — sa session vit ce moment intérieur, le vécu et la conclusion se déposent chez lui | aucun arbitre : ça reste en chambre (prévoir librement) |
| **QUESTION** — « l'histoire de ceci ? » | demander ce que le monde dit | l'arbitre répond **depuis l'état seulement** — Règle Zéro intacte |
| **INTERVENTION** — la main par-dessus | hors fiction : on répare, on ne joue pas | réservé au siège de régie (joueur/dev), jamais un geste d'homme dépêché |

Les billets entre hommes entrent dans le brief **en percept** — « Hask t'a écrit :
"…" » — jamais comme une invitation à ouvrir un fichier (leçon des essais : 2/2
ignorée sous la pression de l'élan).

## 4. Le runtime — la règle en quatre lignes

> **Tout le monde peut appeler tout le monde, n'importe quand, en parallèle.**
> **Les sessions sont de la mémoire ; la mémoire supporte le désordre** — c'est l'anachronisme.
> **La vérité n'a qu'un point de sérialisation : l'état** — empreintes, staging, la porte, l'arbitrage.
> **Chaque réveil porte son moment** — la date, le creux, « qui te réveille » : une étiquette, jamais un verrou.

Mesuré (trois réveils-jouets) : deux `--resume` concurrents sur la même session
réussissent tous deux, même id, transcript unique aux branches entrelacées — pas de
verrou natif, pas de crash. Pour un **arbitre**, l'entrelacement est son registre
d'audiences (le MJ est débottlenecké : tout le monde peut et doit lui parler à la
fois). Pour un **homme**, deux réveils simultanés sont deux moments de sa vie joués
en désordre — ce que l'anachronisme accepte déjà. Personne n'est sérialisé.

### Call et cast — la synchronicité se décide par arête, jamais par système

> **On APPELLE quand on a besoin de la réponse pour continuer** (sync — le `-p`
> imbriqué est le mécanisme d'attente, la réponse est un retour de commande).
> **On DÉPÊCHE quand on lance une vie** (détaché — la suite arrive par les canaux).

| arête | mode |
|---|---|
| lancer une journée, une activation | cast |
| écrire un billet à un absent | cast (et l'écriture RÉVEILLE le destinataire — le geste d'écrire est le réveilleur, aucun démon) |
| homme → MJ : TENTER / DEMANDER | **call** — le verdict revient sur stdout, dans le fil de sa pensée |
| MJ → homme : une réplique doit sortir (Règle Zéro) | **call** |
| MJ ↔ MJ avec besoin de réponse (passation…) | **call** |

Filet des cycles d'appels : les arêtes sync sont courtes et dirigées ; le timeout
du `-p` suffit.

### Les rôles

- **Un seul rôle MJ.** MJ = l'arbitre d'une zone, session continue (`--resume` —
  il tient ses fils, son réveil ne porte que « qui te réveille, et voici son mot »).
  **Zone = une ville** pour le moment (`mj-peyredragon`, `mj-portreal`…) — en
  anachronisme, un homme n'est pas « dans une salle », la zone-salle n'a pas de
  référent. La zone du joueur (`mj`) porte trois choses en plus : **le spectacle**
  (le flux), **la montre** (`append_flux` seul), **l'arbitrage final** (staging,
  canon). Quand la zone est la scène, le MJ du joueur absorbe le rôle : un seul
  arbitre par pièce.
- **Le guetteur meurt.** Le serveur (seul processus permanent) lance
  `claude -p --resume <mj>` sur le POST du joueur — le MJ du joueur est un habitant
  comme les autres. Le battement hors-acte devient un réveil de plus (élection ou
  cron). La supervision devient un siège : `claude --resume <mj>` en interactif
  quand le dev veut piloter, rendu en sortant.
- **L'élection (la boucle) reste le rattrapeur priorisé** : l'énergie du tissu élit
  qui vivre ; un message en attente pèse sur son destinataire. Le tick ne réveille
  personne : il propose.
- **Le MJ est un travailleur, pas seulement un guichet** (réalisation du 31.8) :
  il tient SES affaires d'arbitre — le staging à dépouiller, les relances dues
  (`en-souffrance.json` de sa chambre, déjà en usage), les inventions à graver,
  les annales en retard — et **la boucle l'élit comme tout le monde** : son
  énergie dans le tissu = ce qui pèse sur sa table. Un réveil-dispatch de MJ
  n'est pas une journée d'homme : son brief est son établi (« N propositions au
  staging, M fils à relancer »), et sa journée consiste à trancher, graver,
  relancer. Même chambre, mêmes fils, mêmes journées de travail — la symétrie
  habitant est complète.

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
| **L'isolation des hooks : `--restricted`** (mesuré le 30.8) | `--restricted --tools Bash,Read,Write…` ignore les settings user ET projet (zéro hook parasite au réveil-jouet, Bash vivant) — c'est le mode de lancement des habitants ; conséquence : aucun hook ne bat jamais chez un habitant, le vécu se dépose par le lanceur (`trace.deposer`), pas par hook Stop |
| Le billet-fichier ne suffit pas | 2/2 ignoré sous la pression de l'élan → billet en percept dans le brief |
| Le besoin homme→MJ est réel | 3/3 : premier geste = parloir vers l'arbitre |
| Le rapport JSON est un artefact RPC | il disparaît au profit des écrits de chambre + versements + une phrase |
| `--resume` interactif d'une session `-p` | à mesurer (une minute) — c'est le mécanisme du siège de supervision |

## 6. Le chantier — les étapes de l'implémentation

Chaque étape est commitable et se vérifie par un réveil-banc. Le code vit dans le
container `agents/` ; `chambres/` est de la donnée.

1. **`agents/chambre.py` + `agents/prompts/mj-zone.md`** — le domicile (chemin,
   ouvrir — claude.md seedé une fois —, canal canonique, non-lus) et le manuel de
   l'arbitre (électeur-greffier, jamais auteur, réponses depuis l'état). Rien ne
   casse. *(cast : délégable)*
2. **Le lancement** (`depeche/mission.py`) — pas-de-tir neutre conservé, chambre
   montée `--add-dir`, outils +Write/Edit, **neutralisation des hooks hérités**
   (mesurer `--setting-sources`), spawn détaché pour les casts. *(le point hooks se
   mesure d'abord)*
3. **Le brief** (`depeche/brief.py`) — section chambre au chemin absolu, billets en
   percept, claude.md perso joint au système, le gabarit JSON retiré. → **réveil-banc
   n°3** : le billet-percept est-il répondu ?
4. **Les verbes** (`metier.md` + `parloir.py` + le MJ de zone en session continue) —
   TENTER/FAIRE/DEMANDER en call (stdout), l'adresse `~mj-<ville>`, le narrateur de
   la boucle devient officiellement MJ de zone. → **réveil-banc n°4** : les verbes
   canalisent-ils ce que le parloir absorbait ? *(les manuels : ta voix — relecture
   avant commit)*
5. **Écrire = réveiller** — `--dire` spawn le destinataire détaché ; le serveur
   lance le MJ sur POST ; le guetteur s'éteint. → **réveil-banc n°5** : un ping-pong
   homme↔homme réel.
6. **Le vécu** (`agents/trace.py`, appelé par le lanceur — pas de hook : `--restricted` les ignore tous) — transcript + dépôt dans
   `fil/` ; `vecu.py --md` comme vue lisible. *(délégable)*
7. **Les migrations douces** — les fils `~mj` du parloir vers `relations/`, la
   dépêche manuelle branchée sur `chambre.ouvrir()` au premier réveil. *(délégable)*

Ce qui n'est PAS dans ce chantier : le lot 3 front (gate à trancher), le pont
`batailles` (les peaux), la boucle d'élection elle-même (elle sert telle quelle).
