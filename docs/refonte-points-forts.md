# La refonte — ce qu'on emporte, et ce que les quatre contraintes exigent

Relecture du dépôt faite le 9 septembre 2026, avant d'ouvrir la version
« cleane, mieux scalable, plus accessible, et hors GoT ». Trois passes
d'exploration (serveur et écran, moteur et état, agents PNJ), plus les docs de
conception (`experience.md`, `architecture.md`, `organisation.md`,
`audit-technique.md`, `habitant.md`, `sieges.md`, `parties.md`, `graines.md`).

Ce document ne propose pas d'architecture cible. Il dit **ce qui fait le jeu**
— les idées qu'une réécriture doit conserver telles quelles, sinon ce n'est
plus le même jeu — et **ce que chacune des quatre contraintes implique
concrètement**, mesuré sur le code d'aujourd'hui.

---

## 1. Ce qui fait le jeu — les invariants à emporter

### A. Du côté du joueur (ce qu'on sent en jouant)

1. **Pas de menus, jamais.** Un champ libre qui ne se désactive jamais, et sept
   boutons qui changent ce que la phrase *est* (Parler, Agir, Question, Penser,
   Coulisses, Laisser faire, Intervention). Le joueur agit par ses mots ; le MJ
   joue le monde, jamais les options du joueur. C'est la décision fondatrice
   de l'interface, et elle est indépendante du décor.
2. **Le fil coule.** Les items tombent un par un, quelques secondes d'écart,
   avec une avance de quelques lignes ; le joueur peut écrire pendant que le
   MJ calcule, et le monde peut l'interrompre. Bouton Couper : ce qui n'a pas
   été vu n'a pas eu lieu.
3. **La salle se constate, elle ne se déclare pas.** Qui parle est là ; qui se
   tait s'estompe puis se range dans « et N autres » ; il revient au premier
   mot. Aucune annonce d'entrée ou de sortie.
4. **Le temps coûte, et il est visible.** Une montre à la minute ; chaque type
   d'item a son prix ; Question, Penser et Coulisses valent zéro. « Un conseil
   de quarante répliques coûte une heure, pas un après-midi. »
5. **Le brouillard est le sujet.** Les nouvelles arrivent en retard et
   déformées ; la carte porte des croyances datées avec leur certitude, jamais
   la vérité ; un pli parti et jamais confirmé s'affiche « muet ». Les PNJ
   subissent le même brouillard et agissent sur ce qu'ils croyaient hier.
6. **Les conséquences ne sont jamais étiquetées.** Pas de « (−15 opinion) »,
   pas de « ce choix aura des conséquences ». Le prix est dans la phrase.
7. **Le routinier ne remonte pas.** Une compétence déléguée est permanente ; le
   délégataire tranche selon sa tête et rend compte au passé, en une ligne. Ce
   qui monte au joueur est une vraie bifurcation.
8. **La demande vient d'un personnage, pas du MJ** (le bloc `demande` :
   Accordé / Refusé / voies numérotées / Expliquer). C'est l'inverse exact du
   menu, et ça reste le seul endroit cliquable qui tranche quelque chose.
9. **Ce qui est écrit s'ouvre.** L'item `ecrit` mène au volume et à la ligne ;
   « un registre décrit en scène et non inscrit n'a pas été ouvert ».
10. **Les annales** : la mémoire longue, avec parcimonie, en ligne rouge et or.
    Ce que l'Histoire retient, opposable aux scènes suivantes.

### B. Le moteur (ce qui fait que le monde tourne sans qu'on l'écrive)

11. **La position se calcule, elle ne se stocke pas.** Routines = destinations
    par bande horaire ; topologie = arêtes en minutes de marche ;
    `presence.json` = exceptions datées seulement. Personne n'apparaît dans une
    salle sans traverser celles d'entre les deux.
12. **Le coût se mesure, il ne se déclare pas.** `echelle` a été supprimé au
    profit du **quartier** (composante connexe d'un siège occupé, puis vingt
    minutes au plus). La règle « composante D'ABORD, durée ensuite » a payé un
    bug précis (35 personnes « à zéro minute » de la Table Peinte) et doit
    survivre mot pour mot.
13. **Le creux est la seule ressource consommable.** 1440 minutes moins les
    bandes fermées, le sommeil, la marche ; un creux porte une heure ET une
    salle. Un homme sans creux ne pense pas. Ça a remplacé trois compteurs
    (`excitation`, `mur`, `servie`) qui ne mesuraient rien.
14. **Trois boucles, dans un ordre non négociable** : les mains (arithmétique
    entière avec report, aucune opinion), puis les absents (diffusion arrivée →
    déclencheurs → étapes à horloge → actes et nouvelles → tête réécrite), puis
    la salle (élection de celui qui a la plus forte raison d'agir, « rien »
    étant une réponse valable). Le tick calcule et n'écrit jamais.
15. **Deux brouillards symétriques et un seul canal de croyance** :
    `evenements.diffusion` côté PNJ, `info.json` côté joueur. Une croyance ne
    change que par une livraison arrivée ; le statut de l'événement verrouille
    la livraison.
16. **Vérité contre rapport.** La mesure est vraie ; ce qui remonte est une
    croyance, arrondie selon la `maniere` du porteur. Aucun compteur n'est
    jamais rendu à l'écran.
17. **Append-only partout, état replié.** Le flux et les parties sont des
    journaux de lignes immuables ; une correction est une ligne de plus ;
    l'écriture concurrente est réglée (verrou, relecture, `n` pris sur le
    disque).
18. **Le siège** : un acteur, humain ou PNJ, est un point de vue servi + un
    canal d'action + un fil propre + un brouillard. Siège occupé → pas de tête ;
    siège vacant → tête obligatoire. « Sieges.md » le mesure : six fichiers du
    moteur ne connaissent aucun nom de personnage — le goulot pour ouvrir un
    siège est éditorial, pas technique.
19. **Les règles adressées dans les deux sens** (`regles.py --verifier`) :
    chaque règle du livre a un slug, le code porte `# regle: <slug>` à la ligne
    exacte, et la vérification échoue si l'un des deux dérive.
20. **La partie** (plateau de pièces logiques, N camps, sans dé ni durée,
    information complète, deux questions : « as-tu une pièce libre » et
    « as-tu écrit le chemin ») est déjà **le sous-système le plus indépendant
    du décor** : joué sur une quinzaine de mondes différents, une seule table
    de mots-clés à sortir en données. Et `graines.md` dit ce qu'une partie
    laisse : un monde meublé dont chaque objet a une provenance et un délai.

### C. Les agents (ce qui fait que les PNJ ne sont pas des marionnettes)

21. **La Règle Zéro** — on n'écrit jamais la parole d'un PNJ, on le dépêche —
    doublée d'une garde de code (le MJ est relancé s'il a interrogé un PNJ sans
    pousser sa parole).
22. **La Règle d'Autonomie** — un PNJ ne demande au MJ ni permission, ni
    information, ni verdict — appliquée à la porte (appel PNJ→MJ refusé). Ça
    supprime le goulot central de tout système multi-agents à orchestrateur.
23. **Écrire = réveiller.** Pas de démon, pas de polling : déposer un billet
    est le réveil du destinataire. Coût zéro à l'inactivité.
24. **Le percept, pas le pointeur.** Mesuré deux fois sur deux : un agent
    n'ouvre pas le fichier qu'on lui indique. Donc « Untel t'a écrit : "…" »
    dans le texte, jamais « va lire tel fichier ». Même chose pour ce qu'on
    attend de lui et pour ses pannes.
25. **Le péage de la parole** : un billet porte un fait nouveau, une décision
    ou une question ; sinon on se tait. Une règle de contenu bat un throttle
    (mesuré : deux polis se sont réveillés seize fois en six minutes).
26. **La criticité comme ordonnanceur d'attention** : cinq trous sur quatre-
    vingts, classés par ce que le plan perd si ce pas rate, en trois seaux à
    places fixes.
27. **La continuité physique** : `demain.md` écrasé le soir, réinjecté le
    matin sous « Là où tu t'étais laissé » ; le cahier de sa main gagne sur la
    fiche d'état dès qu'il l'a amendé.
28. **Rien dans la chambre ne fait foi.** Mémoire et vérité séparées ; une
    chambre a le droit de se tromper ; un JSON cassé rend un gabarit vide,
    jamais un réveil raté.
29. **Le prompt archivé avant l'appel, réinjecté seulement si son empreinte a
    changé.** Sur un manuel de 180 Ko et des sessions qui vivent des semaines,
    c'est l'économie structurante.
30. **Le cliquet plutôt que la limite** (hooks de taille et de globales) : un
    garde-fou qu'on débranche ne garde rien ; le plafond d'un fichier est sa
    taille au dernier commit.

### D. Le serveur et l'écran (les petites décisions qui tiennent tout)

31. **Le tri par audience se fait au serveur, avec verrou par en bas** : un
    item sans `pour` n'est servi à personne au-delà de la ligne du dernier
    arrivé. Le défaut sûr est la fermeture. Testé par mutation.
32. **Le jeton est la serrure ET le siège** : sans jeton, liste vide, jamais
    « le flux public ».
33. **La hiérarchie de repli du `pour` en écriture** : la physique de la pièce
    d'abord, l'étiquette de scène ensuite, « on se ferme sur l'auteur » en
    dernier. Chaque branche porte le bug qui l'a payée.
34. **Fenêtre glissante + `debut`/`total`** : le curseur client compte sur le
    flux entier ; `?avant=N` remonte le passé par tranches.
35. **La réparation à la serviture** (portraits, figures) : on ne réécrit
    jamais un fichier append-only.
36. **Le bus à registre chaînable** : `enregistrer(type, fn)` compose au lieu
    d'écraser ; un module nouveau ne touche jamais au bus.
37. **`nav.js` : l'endroit comme adresse** dans l'URL, pile de navigation
    séparée de `history`. Réutilisable tel quel.
38. **`domaine/` ne connaît ni `req` ni `res`** ; `CONSEIL_RACINE` permet à
    tout test de monter une partie miniature dans un dossier temporaire.
39. **Une seule vérité physique lue par deux langues** (`diffusion.json` lu
    par Python et par le serveur) — parce que les deux avaient déjà divergé.
40. **Les commentaires portent la décision, le symptôme, la mesure.** C'est la
    meilleure documentation du dépôt, et de loin. Dans la refonte, ces
    « pourquoi » doivent vivre dans les fiches de container, pas dans des
    fichiers de mille lignes que personne n'ouvre.

---

## 2. Ce que les quatre contraintes exigent, mesuré

### « Cleane »

- **Le dépôt est un dépotoir** : ~170 `tmp*.json` à la racine (94 commités),
  `NUL`, `err.txt`, `sec.txt`, `dec.txt`, `msg.json`, `prev.json`,
  `patch_gemini.py` ; dans `etat/`, 26 instantanés `tick-*`, une quinzaine de
  `.avant-*` à côté des fichiers vivants, des `.py` et `.txt` de travail, cinq
  `correction-plan-*.json` jamais retirés, `archive/2026-08-10-staging/` à
  quarante fichiers.
- **Deux copies byte-identiques de chaque `CLAUDE.md` / `AGENTS.md`** (89 Ko à
  la racine, ×2), maintenues par un script dédié avec son test.
- **Trois moteurs d'agents** (dépêche, boucle d'activation, réveil MJ) qui ne
  partagent que `runtime.py` ; deux registres de mesure redondants (JSON par
  appel + SQLite d'idempotence) ; une branche Gemini inachevée avec un chemin
  absolu de cette machine.
- **`metier.md` est corrompu** : dupliqué mot pour mot (108 lignes = 2 × 54)
  et terminé par un bloc « Directive Évolutive / agent autotélique / cherche du
  pouvoir sur la simulation » injecté dans chaque PNJ.
- **Le préambule `sys.path` recopié dans ~40 fichiers** ; `noyau` importable
  sous deux noms ; une contrainte d'ordre d'import documentée dans
  `temps/expose.py` ; `scene/flux.py` est un script top-level de 1 070 lignes
  qui refuse d'être importé.
- **Dérive de schéma acceptée** : `paroles.json` a trois noms de champ pour le
  texte, deux pour le destinataire, cinquante `type` distincts et 174 entrées
  sans type.
- **Côté écran** : `jeu.css` fait 5 005 lignes en couches d'override (douze
  déclarations de `grid-template-columns`, seule la dernière compte) ; 77
  balises `<script>` globales dans un ordre significatif ; `admin.html` est une
  seconde application de 2 507 lignes hors modules ; du code mort
  (`routes/bataille.js`, `modules/melee.js`).
- **Ce qui a déjà été fait et qu'on garde** : façade / porte / fiche par
  container, `tables.py` comme porte de l'état, `verifier.mjs` avec gardes et
  mesures, les hooks à cliquet. `organisation.md` s'ouvre encore sur
  « proposition, rien n'est acté » alors que tout est implémenté.

### « Mieux scalable »

- **`/scene` relit et reparse 8,9 Mo à chaque sondage**, toutes les deux
  secondes, par siège. Pas de cache, pas d'index d'offsets, pas de tail. C'est
  le coût dominant et il croît avec la durée de la partie. Un index de lignes
  ou un flux poussé (SSE/WebSocket) est la première chose à refaire.
- **48 `JSON.parse(readFileSync)` recopiés, 14 lectures de corps POST sans
  limite de taille** ; `POST /verbe` bloque une requête jusqu'à 300 s ; neuf
  points de spawn Python dispersés sans file ni limite de concurrence.
- **Aucune politique de rétention** : 2 717 fichiers `compute/`, 2 449
  `depeches/`, 1 681 fichiers de fil, 1 225 `discussion.json`, 2 765 curseurs
  `.lu` ; `pensees.json` (1,2 Mo) relu intégralement à chaque brief.
- **Le plafond de quinze sessions est un sémaphore maison sur le système de
  fichiers** (~130 lignes, identité de naissance de PID par `ctypes`).
- **Aucun timeout d'agent, nulle part**, et des relances automatiques du MJ
  jusqu'à trois fois : un tour peut multiplier les appels sans plafond.
- **Le prompt MJ pèse ~180 Ko à chaque réveil** parce que doctrine et décor
  sont dans les mêmes fichiers.
- **Le goulot d'échelle des sièges est éditorial** : ouvrir un siège a coûté
  238 lignes de conception à la main. Le contrat d'un siège tient en six
  lignes ; c'est ça qu'il faut rendre déclaratif.
- **La couverture de test est inversée par rapport au risque** : la partie
  (le plus neuf, le plus isolé) a neuf fichiers de tests ; le calcul de fenêtre
  du tick et les vingt gardes qui verrouillent chaque écriture d'état n'en ont
  aucun ; zéro test d'écran sur 95 modules ; les deux tests serveur qui gardent
  le brouillard et la marche ne sont pas dans `verifier`.

### « Plus accessible »

- **Zéro landmark** (`main`, `nav`, `aside`), **zéro `aria-live`** sur un fil
  qui se peuple en continu, `tabindex` dans un seul module sur 95, tout le
  décor cliquable (salles, jetons, cases, cartes) en SVG ou `div` avec
  `onclick`, inatteignable au clavier.
- **Beaucoup d'information ne passe que par la couleur** (tranches de livres,
  halos de camp, teinte de portrait tirée du nom) sans doublage textuel. Pas de
  `prefers-contrast`, pas de réglage de taille de police exposé.
- **Ce qui existe déjà et qu'on garde** : thème sombre complet,
  `prefers-reduced-motion`, 31 règles de focus, 19 px sérif par défaut,
  raccourcis clavier dans seize modules, le fond de jour derrière le texte et
  jamais devant (« rien n'en abîme le contraste »).
- **Le geste d'accessibilité le moins cher et le plus rentable** : le fil est
  une liste d'items typés, donc un `role="log"` + `aria-live="polite"` sur le
  fil, un `role="listitem"` par item, et des landmarks sur les trois panneaux
  changent tout pour un lecteur d'écran sans toucher au rendu. Le clavier sur
  le décor est un vrai chantier, à faire échelle par échelle.
- **Le flux append-only typé est un atout d'accessibilité** : un item est déjà
  une donnée sémantique (récit, réplique avec locuteur, geste, pensée), il
  suffit de l'exposer.

### « Hors GoT »

Le verrouillage est **beaucoup plus localisé qu'on ne le craint**. Le cœur
narratif (`temps/`, `scene/`, `etat/`, le bus, le siège, le parloir, la
dépêche) est presque propre. Le décor est en dur à quatre endroits qui
comptent :

1. **Les données de monde dans du code** : `ecrans/modules/plans.js` (899
   lignes de plans de château, Braavos engendré par `replaceAll` sur
   Peyredragon), `serveur/monde3d.js` (registre `LIEUX3D`), les cadrages
   nommés de `carte.js`, la table de blasons de `blasons.js`. → Un manifeste de
   monde en données servies.
2. **Le vocabulaire de règles** : le dragon comme **type d'unité** dans
   `jetons.js`, `terrain.js`, `jeu.css` (famille de filtre, verbe « frapper au
   dragon », canal « porté par un dragon »), la monnaie dans `chiffrer.py`, les
   regex de titres et de dragons dans `plan/criticite/`, les mots-clés d'office
   dans `taches.js` et `reparer_renvois.py`. → C'est le seul point qui touche
   la sémantique et pas seulement les noms ; il faut une table de *genres*
   d'unités et de canaux fournie par le monde.
3. **Les prompts** : `CLAUDE.md` racine (la doctrine noyée dans les exemples
   Targaryen), `mj-spectacle.md` (75 Ko, règles d'écriture excellentes et
   génériques, chacune enseignée par un exemple daté), `mj-partie.md`,
   `concepteur.md` (entièrement Braavos). → Séparer la doctrine (générique) des
   exemples (par monde) ; le manuel du PNJ, `metier.md`, est déjà générique
   une fois nettoyé.
4. **Trente-deux pour cent de `scripts/`** (`monde/`, `materialisation/`,
   `ville/`, ~26 600 lignes) est la génération d'un seul monde en 3D, plus
   gros que le moteur narratif entier. → Un dépôt ou un plugin à part, pas un
   pair du moteur.

À cela s'ajoutent des restes de deux mondes cohabitant sans notion de
« monde » : 76 chambres vénitiennes dans `chambres/`, `maison-serenissima`,
la boucle d'activation couplée à Braavos, la table d'emojis de
`partie_signes.py` qui grossit à chaque partie. **La refonte doit introduire
la notion qui manque : un monde est un paquet** (lieux, topologie, maisons,
unités, monnaie, titres, calendrier, exemples de prompt, blasons), et le
moteur n'en connaît aucun.

Un test simple pour la version hors GoT : les parties déjà jouées hors
Westeros (`enquete-vauthier`, `la-ville-des-agents`, `le-chantier-des-agents`,
`local-a-velos`) et le siège d'Aurore ouvert « sans un champ nouveau » disent
que la mécanique tient. Ce qui manque est le paquetage, pas le moteur.

---

## 3. Ce qu'on ne reprend pas

- Le monolithe `admin.html`, les routes et modules morts, la branche Gemini.
- Les instantanés manuels dans `etat/` (git suffit) et les fichiers de travail
  à la racine.
- La boucle d'activation autonome telle quelle (énergie, fatigue à demi-vie) :
  ses idées (importance, horloges par acteur) peuvent revenir, pas son
  couplage à Braavos ni son verrou propre.
- Le double registre de mesure ; un seul journal d'appels avec rotation.
- Le sémaphore de sessions sur fichiers ; une file d'appels avec plafond et
  timeout par défaut, débrayable, pas absent.
- Le prompt de 180 Ko : la doctrine en une constitution courte et stable, le
  reste chargé par mode et par monde.
