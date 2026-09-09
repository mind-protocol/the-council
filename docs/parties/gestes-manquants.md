# Les coups qu'un joueur ne peut pas jouer à l'écran

6 septembre 2026. Non vérifié coup par coup : c'est le sujet de la partie à
venir, et chaque ligne est à contester.

**Le principe.** Le joueur ne joue qu'à l'écran. L'arbitre est le MJ, et il
joue à la ligne. Donc : **un coup de joueur qui n'a pas de geste à l'écran
n'existe pas pour le joueur.** Soit on lui donne un geste, soit on le retire
des règles. « Garder à la ligne » ne vaut que pour l'arbitre, ou avec une
raison écrite ici.

Les coups de l'arbitre ne sont pas concernés : `arbitrer`, `constater`,
`tour`, le `justifier` d'ouverture, les gels surchargés.

## À rendre jouable — six

| Coup | Ce qui manque | Le geste à donner |
|---|---|---|
| `viser` une racine | la case 🎯 n'existe que sous un parent | une case 🎯 au rang racine tant que le camp n'en a pas |
| `viser` daté | la bulle n'a pas de date | un champ « au jour N » dans la bulle, facultatif |
| `retirer` une pièce vivante | « reprendre » refuse une pièce non détruite | reprendre la pièce au deck : la frappe posée dessus tombe, règle 23 |
| `agir` sans question | la poignée ⚔️ n'apparaît que sur une carte suspendue | la poignée sur toute carte à soi |
| `demander` avec un nombre | l'écran n'envoie qu'une phrase | un champ nombre dans la bulle ; c'est lui qui fractionne une pièce |
| `retourner` sans bourse, `detruire` avec | le genre de la pièce choisit le verbe | la bulle demande le verbe quand la pièce n'est pas une bourse |

## À retirer des règles — quatre (fait le 6.9)

Retirés le jour même : la validité refuse les lignes neuves (`partie_validite.py`),
le greffe replie toujours les anciennes, le schéma de l'IA est celui des gestes,
et les deux livres sont à jour (`regles-partie.md` annexe B, `mj-partie.md`).

| Ce qui sort | Pourquoi ça peut sortir |
|---|---|
| `agir` avec `a_faire` puis `faite` | le greffe ne lit jamais cet état pour la préséance ; un maillon est écrit ou ne l'est pas |
| `lever` sur plusieurs verrous | une clef, un verrou ; deux verrous, deux clefs |
| `consigne` | ne sert que les sauts de temps ; sans consigne les pièces tiennent, ce qui est déjà le défaut. `charmed` l'a interdite sans manque |
| `lieu` et `tenu_par` sur `demander` côté joueur | c'est l'arbitre qui les pose en accordant, et c'est écrit ainsi |

## Ce que la partie devra établir

- que deux joueurs ouvrent et jouent `pont-et-moulin` en entier depuis l'écran,
  l'arbitre seul tenant la ligne ;
- que les quatre retraits ne rendent injouable aucune partie de `etat/parties/`
  au rejeu.

Racine proposée pour le camp concepteur : « Le 10 septembre, `pont-et-moulin`
est rejouée entière, ouverture comprise, par deux joueurs qui n'écrivent pas
une ligne au jsonl hors de l'écran. »

## L'impact des quatre retraits

Compté sur les 21 parties de `etat/parties/` et lu dans `scripts/noyau/`.
Une règle d'abord, qui vaut pour les quatre : **un retrait refuse les lignes
neuves, il ne cesse pas de lire les anciennes.** Sinon trois rejeux changent,
dont `charmed`, qui est en cours.

| Retrait | Usage réel | Ce qui en dépend dans le code | Ce qui casse si on retire | Verdict |
|---|---|---|---|---|
| `a_faire` / `faite` | 8 maillons `a_faire` sur ~90 joués, dans 3 parties (essai-1 : 5, pont-et-moulin : 2, enquête-vauthier : 1) ; 2 mises à jour « faite » par seconde ligne, essai-1 seulement. Tout le reste est `faite` d'office par la réponse à un ❓ | le greffe pose `a_faire` par défaut ; `partie_lecture` ne montre un maillon sous une clef que s'il est `faite` ; `partie_ascii` compte les « à faire » ; le schéma de l'IA porte l'enum ; `prevaut` ne le lit jamais | rien dans la préséance. Au rejeu d'essai-1, huit maillons annoncés paraissent réalisés. On perd la forme « j'annonce, puis je fais », qui n'a servi qu'au MJ jouant seul | **retirer.** Un maillon s'écrit quand c'est fait. Cinq fichiers à toucher, aucune règle de jeu |
| `lever` sur plusieurs verrous | **une** ligne sur 21 parties : charmed n° 94, jouée par l'IA du mal, une clef sur deux verrous du Livre | le greffe lit `ouvre` en liste ; une clef n'est tenue que quand **tous** ses verrous sont tombés ; le schéma de l'IA accepte la liste | si la validité refuse la ligne 94 au rejeu, la position de charmed change du tour 7 à aujourd'hui | **retirer pour les lignes neuves** : validité et schéma IA passent à un seul verrou, le greffe continue de replier les listes. Écrire la date de la règle |
| `consigne` | **une** ligne sur 21 : essai-1 n° 51, le guetteur « compte les galères », c'est-à-dire un ordre à une pièce, pas une consigne de saut | `partie_tour` : une pièce consignée n'est jamais branche morte ; `partie_cartes` et `ascii` l'affichent ; `charmed.json` la liste déjà en `coups_interdits`. **Les sauts de temps du livre (§6) n'existent nulle part dans le code** | essai-1 : le guetteur devient une branche morte signalée, rien d'autre. Et le §6 des règles perd sa seule mécanique, qu'il n'avait pas | **retirer**, et retirer le §6 avec elle ou le réécrire le jour où un saut sera codé. Le défaut « les pièces tiennent » est déjà ce que fait le greffe |
| `lieu` et `tenu_par` sur `demander`, côté joueur | massif : de 8 à 31 demandes par partie les portent, presque toutes. Mais elles ont été écrites à la ligne par le MJ ou par l'IA, jamais depuis l'écran, qui n'envoie qu'une phrase | le greffe les prend de la demande puis de l'arbitrage, l'arbitrage gagne ; la carte affiche le porteur ; le trône, les retournements et les frappes lisent `tenu_par` d'une **personne engagée** | rien au rejeu si le greffe garde les champs anciens. Le coût est pour l'arbitre : il doit poser lieu et tenant à chaque `accorde`, une quinzaine de fois par partie, au lieu de recopier | **retirer du coup joueur et du schéma IA, garder au greffe.** La phrase du joueur porte le lieu et le tenant en clair ; l'arbitre les écrit. C'est déjà la règle du §8 |

Deux choses que le compte révèle et qu'on n'avait pas vues :

- **L'IA joue comme un MJ, pas comme un joueur.** Son schéma accepte les
  listes, `a_faire`, la consigne, le lieu et le tenant. Si le principe est
  « un coup de joueur n'existe qu'à l'écran », le schéma de `partie_ia.py`
  doit être celui des gestes de l'écran, pas celui du greffe.
- **Le §6 sur les sauts de temps est une règle sans code.** Personne ne l'a
  jouée en 21 parties. Le retrait de la consigne le met à nu.
