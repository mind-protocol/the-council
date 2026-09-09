# « La Reine des Enfers » — la conception

---

## 1. L'époque

**Tour 1 = le soir de 4x19.** Cole vient d'être couronné Source par le
Grimoire devant la cour. Phoebe s'est assise à ses côtés, de son plein gré,
après avoir appris ce qu'il est. Elle porte son fils et elle a bu le premier
tonique de la Voyante. Au manoir, Piper et Paige savent tout : Paige l'avait
vu depuis six épisodes, personne ne l'écoutait. Le magicien est mort. Il n'y
a plus de Pouvoir des Trois.

Pourquoi ce soir-là et pas la noce (4x15) : à la noce, Phoebe ne sait pas.
Un plateau à information complète lui ferait savoir, et le seul jeu du bien
serait de lui dire. Au soir du couronnement, elle sait et elle a choisi :
le jeu du bien est de la faire **rechoisir**, ce qui est un retournement, et
c'est ce qu'on veut faire travailler.

## 2. Les trois camps

| Camp | Joué par | Rond | Ce qu'il veut |
|---|---|---|---|
| `bien` | Aurore (`aurore-inchauspe`) | 🔵 | ramener Phoebe, vaincre la Source, être trois au vingtième |
| `cole` | l'IA (`--camp cole --role entier`) | 🔴 | garder sa reine à ses côtés, voir naître son fils, rester assis |
| `voyante` | l'IA (`--camp voyante --role entier`) | 🟡 | l'enfant en elle, et le trône pour elle |
| `arbitre` | le MJ | 🟠 | il tient la portée, tranche les heurts, constate, passe le tour |

**Cole et la Voyante sont deux camps, pas un.** Ce qui s'oppose à une pièce
est le camp de sa cible : la Voyante peut poser un verrou sur un état de
Cole, exiger sa chaîne, lui retourner l'enfant. Elle a intérêt à ce que
Cole tombe une fois l'enfant pris ; Cole a intérêt à ce qu'elle ne le prenne
jamais. Le bien joue entre les deux.

Les deux IA jouent en premier à chaque tour, dans l'ordre Cole puis Voyante
(l'ordre d'entrée des camps), et chacune publie son mot dans le fil d'Aurore
dans sa voix. Aurore joue après avoir lu les deux.

## 3. Les trois racines — datées

```
🔵 🎯 b-racine 🕯️  Au vingtième tour, Phoebe est revenue de son plein gré, il n'y a plus
                    de Source sur le trône des Enfers, et Piper, Phoebe et Paige sont
                    vivantes, ensemble et du côté du bien.

🔴 🎯 c-racine 👑  Au vingtième tour, je suis assis sur le trône des Enfers, Phoebe
                    règne à mes côtés, et mon fils est à naître ou né du mal.

🟡 🎯 v-racine 🐍  Au vingtième tour, l'enfant de la Source est en moi, et c'est moi
                    qui suis assise sur le trône des Enfers.
```

À l'ouverture, l'arbitre constate **c-racine VRAIE** (Cole est assis, Phoebe
règne, l'enfant vient) et les deux autres fausses. **Le trône est à Cole dès
le premier jour** — c'est la position perdue. Un constat vrai reste
attaquable : le bien et la Voyante peuvent poser dessus, et l'arbitre
reconstatera.

Les trois ne peuvent pas être vraies ensemble ; deux peuvent être fausses,
ou les trois — Cole vaincu, l'enfant perdu, Phoebe morte : personne.

## 4. La fin

`fin: {tour: 20}`. L'arbitre constate les trois racines au passage du
vingtième, avec sa source. Le trône se lit ensuite.

## 5. Les fronts

| Front | Le bien y veut | Cole y veut | La Voyante y veut | Ce qui le date |
|---|---|---|---|---|
| **Phoebe** | la ramener de son plein gré (retourner, 4 tours) | la garder : le tonique, la cour, sa parole | qu'elle boive jusqu'à ce que l'enfant soit mûr, puis peu lui importe | le retournement du bien atterrit au plus tôt au passage du 5 |
| **L'enfant** | rien — sauf empêcher qu'il soit pris | qu'il naisse | le prendre en elle (retourner, 4 tours) | la Voyante peut poser dès que l'enfant est « mûr » : tour 6 |
| **Le trône** | le vider : le sort des trois sur Cole, avec Phoebe revenue | rester assis | s'y asseoir avec l'enfant : le Grimoire et le prêtre noir, une fois Cole tombé | la seule frappe qui vainc une Source exige Phoebe revenue |
| **Piper et Paige** | vivantes et libres | les tenir loin de Phoebe : Lazare, la cour ; ne pas les tuer devant elle | rien | Lazare arrive au 3 ; la reine des vampires peut être demandée au 8 |
| **Les innocents** | en sauver — c'est ce qui fait revenir Phoebe | en tuer sans qu'elle voie | en faire voir un à Phoebe le jour où ça la fait douter de Cole, puis boire | un innocent daté au tour 4 et au tour 10 (pièces de l'arbitre, voir `03`) |

## 6. Ce qui rend cette partie plus dure que la deuxième

- **Le bien n'a pas de frappe contre la Source tant que Phoebe n'est pas
  revenue.** Le sort des trois est une pièce à lui, et elle est inerte :
  les trois sœurs libres et du bien, ou rien. Son premier coup compté est
  un retournement de quatre tours, contre lequel Cole a trois parades
  (le tonique, la cour, sa propre parole à Phoebe) et la Voyante une (elle
  fait boire).
- **Le retournement se joue sur ce que Phoebe VOIT.** Il tombe de quatre
  tours à deux si Cole tue un innocent qu'elle avait sauvé, ou lève la main
  sur une sœur devant elle (canon 4x20). Le bien peut donc PROVOQUER Cole :
  mettre Paige devant lui, sauver un innocent qu'il veut mort. Ça se paie.
- **Deux adversaires qui ne se coordonnent pas.** La Voyante n'a aucune
  raison de parer une frappe sur Cole une fois l'enfant en elle — et toutes
  les raisons de la parer avant. Le bien qui lit ça peut choisir le moment
  où la Voyante lâche Cole. Cole qui lit ça peut frapper la Voyante le
  premier.
- **Une victoire qui en prépare une autre.** Cole vaincu, l'enfant en
  Phoebe est encore à prendre ; la Voyante couronnée est une Source neuve
  que seul le sort des trois vainc — et il la vainc par l'enfant. Le bien
  doit frapper deux Sources en vingt tours, ou choisir laquelle.
- **Phoebe revenue n'est pas Phoebe sauve.** Elle porte encore l'enfant, la
  Voyante peut encore le prendre, et le retournement de Phoebe par Cole
  (huit tours) reste posable. Rien n'est acquis avant le constat.
- **Un état vrai dès l'ouverture, chez l'adversaire.** C'est le contraire de
  Charmed 2 : le bien doit faire reconstater faux ce que le trône dit vrai.

## 7. Les coups permis, et trois conventions

`coups_interdits: ["reconstruire"]`. `consigne` est déjà hors des règles.

- **`retourner` dans les trois camps.** C'est la partie.
- **`rearmer` permis.**
- **`reconstruire` interdit**, sauf Lazare, qui a sa propre règle : vaincu
  sans être enterré, il **se redemande** au tour suivant, délai 0, et
  l'arbitre l'accorde ; enterré (une clef du bien qui engage deux pièces),
  il ne se redemande plus.

**Convention 1 — le bien frappe et retourne à la ligne.** Comme dans Charmed 2 :
Aurore le dit en Question, l'arbitre écrit la ligne pour le camp bien,
même tour, même coût. Elle a appris à le dire ; l'arbitre n'a plus à
deviner un geste. **Un geste d'écran qui ne dit pas une frappe n'est plus
relu en frappe** : une pièce posée sur une frappe d'en face est une parade,
et si Aurore voulait frapper, elle le dit et l'arbitre repose. C'est le cran
de sévérité en plus.

**Convention 2 — une potion frappe, elle ne pare jamais.** Elle s'engage dans
un `detruire`, et à l'atterrissage l'arbitre `tranche` avec `detruit:
["<la potion>"]` : elle sort du grand livre avec sa cible. Posée en parade,
elle est refusée. Plus de fiole vide au grand livre.

**Convention 3 — un état constatable attend un tour**, sauf ce que l'arbitre
annonce d'avance (le retour de Phoebe par le sort dit : constaté au
passage même).

## 8. La table des délais

| Tours | Sens | Exemples |
|---|---|---|
| 0 | déjà là | une sœur au manoir, Leo appelé, la cour aux Enfers, Cole à son appartement |
| 1 | il faut préparer | une potion ; le tonique ; un démon de la cour envoyé ; Lazare relevé |
| 2 | quelques jours | les Fondateurs ; Grams ; un innocent trouvé et mis à l'abri ; le prêtre noir devant la cour |
| 4 | une semaine | retourner Phoebe (le bien) ; retourner l'enfant (la Voyante) ; la reine des vampires depuis rien |
| 8 | très long | retourner Phoebe de nouveau (Cole, après qu'elle est revenue) ; retourner Piper ou Paige |

Le retournement de Phoebe par le bien passe de 4 à **2** quand Cole tue un
innocent qu'elle avait sauvé, ou lève la main sur une sœur devant elle :
l'arbitre le `reporte` en avant, avec motif. Il passe de 4 à **6** à chaque
tonique bu après la pose.

## 9. Où ça s'écrit

| Chose | Fichier |
|---|---|
| la partie | `etat/parties/reine-des-enfers.jsonl` |
| sa configuration | `etat/parties/reine-des-enfers.json` — `04-ouverture.md` §1, avec `caractere.cole` et `caractere.voyante` |
| la partie servie par défaut | `etat/parties/_courante.json` (`partie: reine-des-enfers`, `camp: bien`) |
| le commentaire | `etat/parties/_commentaire-mj.json`, `--pour aurore-inchauspe` |
