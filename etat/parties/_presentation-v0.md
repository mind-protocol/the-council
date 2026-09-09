# La partie — présentation pour un premier coup

Ce que c'est, ce qu'on y manipule, comment un tour se joue, et par où entrer. Le livre de règles est [`regles-partie.md`](regles-partie.md) ; chaque règle citée ici l'est par son adresse entre parenthèses. L'écran est décrit dans [`partie.md`](partie.md), le carnet de l'arbitre dans [`parties/learnings.md`](parties/learnings.md).

## 1. Ce que c'est

Un conseil de guerre joué contre quelqu'un. Le plan d'un camp, seul, ne rencontre rien qui lui résiste : il se prouve par ses propres lignes. La partie lui donne un adversaire qui a le droit de dire « prouve-le », et des pièces pour le dire.

C'est un jeu de pièces logiques entre des camps, autant que la partie en nomme, chacun tenu par un joueur, une tête dépêchée ou le MJ. Un rôle reste hors camp : l'arbitre, dont le nom est le seul réservé. Rien ne se résout par une durée ni par un jet. Tout se résout par deux questions : as-tu une pièce libre pour répondre, et as-tu écrit le chemin.

Le plateau est à information complète : la position entière, tous les camps, pièces engagées ou non, est servie à tous. Le brouillard reste dans la fiction ; il ne s'applique pas ici. Une partie est un fichier `etat/parties/<id>.jsonl`, une ligne par coup, jamais réécrite ; une correction est un coup de plus.

Le livre de règles dit blocage, clé, ressource ; l'écran dit verrou, clef, pièce. Ce texte emploie les mots de l'écran.

## 2. Les objets

| Signe | Objet | Ce que c'est |
|---|---|---|
| 👑 | le trône | l'objet racine. Chaque camp pose sa racine : son état qui ne sert aucun autre. Le trône est au camp dont la racine a été constatée vraie en dernier ; à personne tant que rien n'est constaté (`trone-derniere-racine`) |
| 🎯 | un état | ce qui doit être vrai, constatable. Jamais une action. Un état peut en servir un autre : les états forment un arbre sous le trône |
| 📦 | une pièce | tout ce qu'une clef peut engager : un corps, une bête, une troupe, un lieu tenu, un objet, une bourse, un canal. Les personnes comprises |
| 🔒 | un verrou | ce qu'un autre camp oppose à un état, un maillon, une clef ou une frappe, avec la pièce qui le produit |
| 🗝️ | une clef | ce qui lève un verrou en engageant des pièces ; ou, sans verrou à ouvrir, ce qui réalise un état à soi (`sert`) |
| ❓ | une question | l'exigence de la chaîne : la cible est suspendue jusqu'à ce qu'un maillon soit écrit dessous |
| ⚔️ | un maillon | une action : qui, avec quoi, quel résultat. Un maillon réalise une clef, un verrou ou une frappe, jamais un état |
| 💥 | une frappe | une menace datée sur une pièce adverse ; réalisée, la pièce sort du grand livre |

Le grand livre est la liste des pièces, avec pour chacune son camp, son lieu, son nombre, son tenant, son tour d'arrivée, ce qui l'engage. Le deck est la liste des états qu'un camp met en jeu, dix au plus (`dix-etats`).

Une pièce est à tout instant en attente, en route, libre, engagée, gelée ou détruite (`etats-ressource`). Engagée, elle l'est jusqu'à ce que ce qui l'engage cesse ; une seconde clef qui la veut est « sans ressource » (`engage-jusqu-a-chute`). Une clef ou un verrou qui n'engage rien est refusé (`pas-de-ressource-pas-de-coup`).

## 3. Un tour

Un tour vaut deux jours du monde (`tour-deux-jours`). Chaque camp y joue un coup compté, dans l'ordre d'entrée des camps (`trait-ordre-d-entree`, `un-coup-par-tour`). Comptent : viser, sortir, bloquer, lever, agir, frapper (`detruire`), retourner, retirer, reconstruire, réarmer, passer. Ne comptent pas : demander une pièce, poser une question, écrire le maillon qui répond à une question (`reponse-gratuite`), et tout ce qui vient de l'arbitre.

Les coups d'un camp, avec leur cible :

- `viser` : pose un état dans son deck (`coup-viser`). Sans `sert`, c'est la racine.
- `demander` : demande une pièce, en une phrase. Rien tant que l'arbitre n'a pas parlé (`coup-demander`).
- `bloquer` : pose un verrou sur un état, un maillon, une clef ou une frappe d'un autre camp, avec la pièce qui le produit (`coup-bloquer`). Jamais sur soi (`blocage-par-un-autre-camp`).
- `lever` : pose une clef sur un verrou adverse, ou sur un état à soi qu'elle sert. Au moins une pièce (`coup-lever`).
- `justifier` : exige la chaîne d'une clef, d'un verrou, d'une frappe ou d'un état d'un autre camp. Gratuit, une fois par pièce dans toute la partie (`justifier-une-fois`). On n'exige jamais sa propre chaîne (`pas-sa-propre-chaine`).
- `agir` : écrit un maillon sous une clef, un verrou ou une frappe à soi ; le maillon écrit lève la suspension (`coup-agir`).
- `detruire` : pose une frappe sur une pièce adverse. Posée au tour t, elle arrive au plus tôt en t+1 et n'atterrit qu'au passage du tour suivant : le camp visé a toujours un tour pour bloquer, justifier ou retirer (`menace-datee`).
- `retourner` : même fenêtre qu'une frappe ; réalisée, la pièce change de camp (`coup-retourner`).
- `retirer` : retire une clef, un verrou, une frappe ou une pièce à soi ; les pièces libérées sont gelées deux tours (`coup-retirer`).
- `rearmer` : ajoute une pièce à une clef ou un verrou à soi qui tient encore (`coup-rearmer`).
- `passer` : ne joue rien, et c'est le coup du tour (`coup-passer`).

Un état se pose nu : le verrou vient de l'adversaire, la clef vient contre le verrou, le maillon ne s'écrit que sur demande. Une clef sans maillon est une affirmation, valide jusqu'à ce qu'un coup exige sa chaîne (`cle-sans-maillon-affirmation`).

## 4. Ce qui fait tomber une pièce

Le défenseur tient par défaut : un verrou qu'aucune clef ne lève prévaut, et rien ne bouge tant qu'un coup ne le tranche pas (`defenseur-tient`). Sur un verrou, qui prévaut se lit dans cet ordre (`preseance-blocage`) : le verrou tombé, suspendu ou pas encore prêt donne le camp de sa cible ; sinon une clef qui l'ouvre donne le camp de la clef, sauf si elle est suspendue, pas prête ou sans ressource ; sinon le camp du verrou.

Une clef dont tous les verrous sont tombés est tenue : ses pièces reviennent libres, sans gel (`cle-tenue`). Un verrou tombe avec sa pièce, retirée ou détruite (`blocage-tombe-avec-sa-piece`). Un verrou suspendu ne prévaut plus tant que son camp n'a pas écrit son maillon (`blocage-suspendu-ne-prevaut-plus`) ; une clef suspendue non plus.

Une pièce en route s'engage dès ce tour, mais la clef n'est prête qu'à l'arrivée de toutes ses pièces (`piece-en-route-s-engage`). Une frappe suspendue n'atterrit pas ; une frappe parée par un verrou attend un tour, puis tombe si l'arbitre n'a pas tranché (`parade-un-tour`). Une frappe qui atterrit sans arbitrage est totale (`atterrissage-total`) : la pièce sort du grand livre, ce qu'elle tenait tombe, la pièce qui frappait revient gelée un tour (`destruction-realisee`).

Un état constaté vrai fait tomber les verrous posés dessus et tient les clefs qui le servent ; les pièces des deux côtés sont rendues sans gel (`etat-vrai-libere`).

## 5. L'arbitre

Seul l'arbitre arbitre, constate et passe le tour, et il ne joue aucun coup de camp (`seul-l-arbitre`). Toute pièce passe par `demander` puis `arbitrer`, une fois : aucune n'apparaît sans ces deux lignes (`ressource-demandee-puis-arbitree`). Un arbitrage vise un id, jamais un numéro de ligne (`arbitrage-vise-un-id`), et porte toujours un motif avec sa source (`coup-arbitrer`). Le motif ne nomme jamais les coups que l'autre camp pourrait jouer (`motif-sans-menu`).

Il arbitre dans un ordre fixe, et s'arrête au premier qui répond : l'état le sait ; un mécanisme la produit ; rien ne répond et il comble, une fois, à froid (`ordre-d-arbitrage`). Un heurt entre pièces se tranche par le même ordre, sans table de force (`heurt-tranche-a-la-table`). Une frappe ou un verrou que la pièce ne peut pas atteindre est refusé sur pièce : c'est le seul endroit où le « comment » remonte de force (`portee-refusee-sur-piece`). Un fait comblé vaut pour tous les camps.

Au passage du tour, le greffe liste ce qui arrive, ce qui dégèle, ce qui atterrit, et les états constatables : ceux dont tous les verrous sont tombés ou levés par une clef qui prévaut (`greffe-liste-arbitre-constate`). Ce n'est pas un verdict : l'arbitre constate, et laisse d'abord un tour au camp adverse pour poser quelque chose dessus (`constatable-attend-un-tour`). Un tour sauté est un tour passé par l'arbitre, rien de plus.

## 6. Un exemple en cinq coups

Tiré de `etat/parties/pont-et-moulin.jsonl`, le tutoriel : deux hameaux face à face, une racine chacun (« le hameau d'en face nous paie la dîme »), et par camp trois gars, un charpentier, une barque, dix pièces d'argent, tous demandés et accordés au tour 1. Les numéros sont les `n` des lignes.

1. **n° 24, tour 2, ⚫ viser.** Le noir pose « Le pont est passable pour nous », qui sert sa racine. Une phrase nue, pas de chaîne.
2. **n° 25, tour 2, 🟢 bloquer.** Le vert pose un verrou dessus avec ses trois gars : « deux gars gardent le pont côté rive droite, le troisième dort au hameau ». La pièce est engagée d'un bloc, les trois gars, même si le texte en couche un.
3. **n° 27, tour 3, ⚫ justifier.** Le noir demande qui relève les deux gars la nuit. Gratuit. Le vert répond au n° 28 par un maillon (`repond: 27`), gratuit lui aussi : Lem relève à minuit, personne ne garde le quai du bac. Écrire un maillon, c'est donner une carte.
4. **n° 29, tour 3, ⚫ lever.** Le noir pose une clef sur le verrou avec ses trois gars : ils passent à l'aube, quand Lem est seul et que personne ne le relève. Le vert questionne (n° 30) et réarme avec son charpentier (n° 31) ; le noir répond (n° 33) ; l'arbitre accorde la portée au n° 34 : la clef prévaut.
5. **n° 40, tour 5, 🟠 constater.** Le tour 5 listait `pont-noir` constatable (n° 36) ; un tour a passé sans rien de neuf sur l'état. L'arbitre le constate vrai : le verrou tombe, la clef est tenue, les gars des deux camps sont rendus.

La partie se gagne au n° 83, tour 13, quand la racine noire est constatée vraie.

## 7. Par où commencer

- Rejouer le tutoriel avant toute vraie partie : huit pièces à un chiffre, treize tours, tous les gestes vus une fois. `python scripts/partie.py --cartes` donne la vue au terminal, `--plateau` la dessine.
- Le premier coup d'un camp est sa racine : `viser`, sans `sert` (`racine-au-premier-tour`). Puis ses pièces, par `demander`, gratuites, arbitrées une fois. Le reste du deck se construit un coup par tour (`deck-en-jouant`).
- À l'écran, un seul geste : on prend une carte et on la pose sur une autre. Une pièce sur un verrou d'en face fait une clef ; une pièce sur un état d'en face fait un verrou ; une phrase dans la case 🎯 vide fait un état ; une phrase dans la case 📦 vide demande une pièce ; la poignée ❓ d'une carte d'en face pose une question. Frapper et arbitrer se jouent à la ligne, par le MJ.
- À chaque tour, dans cet ordre, en s'arrêtant au premier oui : quelque chose vient sur moi ? bloquer. L'adversaire a affirmé sans prouver ? questionner. J'ai une pièce libre qui lève un verrou ? lever. Rien à lever ? viser là où mes pièces sont fortes. Une pièce adverse tient trop de choses ? frapper ou retourner. Rien de tout ça ? passer, et c'est un coup.
- Ne pas laisser une question sans réponse : la réponse est gratuite, l'oubli ne l'est pas. Et avant de mettre trois gars contre trois gars, chercher ce que le verrou ne couvre pas.
