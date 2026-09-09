# Charmed 2 — analyse stratégique de la partie

Jouée le 6 septembre 2026 au soir, vingt tours, 165 lignes
(`etat/parties/charmed-2.jsonl`). Le bien par Aurore à l'écran, le mal par
`partie_ia.py --role entier` (dix-neuf appels, environ 3,5 $), le MJ arbitre.
Résultat : **le bien gagne, racine vraie au vingtième, celle du mal fausse.**

Ce fichier lit la partie comme une partie : ce que chaque camp a gagné et
payé à chaque coup, où elle s'est décidée, et ce que ça dit du jeu. Le bilan
des défauts d'outillage est dans le `README.md` ; ici on parle de coups.

---

## 1. La partition — vingt tours en une table

| Tour | ⚫ Le bien (Aurore) | 🟢 Le mal (la Source) | Ce qui bascule |
|---|---|---|---|
| 1 | racine | racine | trône à personne |
| 2 | ❓ sur le retournement de Paige ; 🗝️ Phoebe « voit la Source dans Shane » sous sa racine | 🔄 **retourner Paige** par Shane (fenêtre) ; répond au ❓ par un maillon | le premier front s'ouvre sur la bonne pièce des deux côtés |
| 3 | 🎯 « 3 » (erreur, sorti par l'arbitre) ; ➕ Fondateurs sur la clef de Phoebe | 🔄 **Furies sur Piper** (arrive 7) | le mal ouvre un second front au lieu d'exiger la chaîne du premier |
| 4 | 🔒 **sort des trois en parade sur Shax** | 💥 **Shax sur Paige** | passage 3→4 : le retournement de Paige tombe (Shane démasqué) |
| 5 | 🎯 « le Pouvoir des Trois est reconstitué » | 🔄 **Voyante sur Cole** (arrive 10) | passage 5→6 : Shax dispersé, l'état constaté vrai au même passage |
| 6 | 🎯 « Piper a pleuré Prue » (daté au 8 par l'écran) | 🗝️ l'Oracle nomme Piper (réponse à l'arbitre) | la Source rejoue Paige : refusé, la fenêtre est morte |
| 7 | 📦 potion de la chair de Cole ; 🗝️ **Piper contre la piétaille** | 🔒 **piétaille sur « Piper a pleuré »** | l'arbitre décale les Furies au 8 pour compenser la date de l'écran |
| 8 | ⚔️ maillon (un paquet par soir) ; 🗝️ **Leo a vu la larme** | ❓ sur l'état, ❓ sur la clef — aucun coup compté | passage 8→9 : « Piper a pleuré » VRAI, **les Furies tombent** |
| 9 | 🎯 « Cole est dépouillé » | 💥 **piétaille sur P3** | le mal change d'angle : frapper là où il n'y a pas de parade |
| 10 | 🗝️ **Phoebe jette la potion** | 🎯 « une sœur a renoncé » | passage 10→11 : Cole dépouillé VRAI, **la Voyante tombe**, P3 ferme |
| 11 | ❓ sur le renoncement ; 📦 **sort des aïeules** ; 🗝️ le Livre l'écrit | 🎯 « le Hollow a bu le Pouvoir des Trois » | numéro 106 en double : deux écritures simultanées |
| 12 | ❓ sur la crypte ; passe | 🗝️ **la Voyante ouvre la crypte** ; maillon (douze contre le seuil) | le Hollow est à prendre |
| 13 | ➕ le sort des aïeules dans la clef du Livre (erreur, libéré par l'arbitre) | 💥 **le Hollow sur Paige**, porté par la Source | **la Source est au manoir** — à portée |
| 14 | 🔒 **Cole prend le Hollow** en parade | 🗝️ « le prix de Cole » (chasseurs) sous le renoncement | 4x13 en place |
| 15 | ➕ **le sort des aïeules sur la frappe** (lu en frappe par l'arbitre) | 🔄 Furies sur Piper, refusé (constat acquis) | passage 15→16 : **la Source sort du grand livre** |
| 16 | 🔒 potion sur les douze (mauvaise fiole, reposée) | 💥 piétaille sur Cole | le mal n'a plus de racine, il vise le constat final |
| 17 | 🔒 sort des trois « tue les chasseurs » (lu en frappe) | 💥 **darklighter sur Paige** (arrive 19) | le mal l'avoue : « ma racine est hors d'atteinte » |
| 18 | 🔒 Piper devant Cole | 🗝️ douze lames pour Cole (clef, sans effet) | passage 18→19 : les chasseurs meurent |
| 19 | 🔒 Paige s'orbe devant la flèche | 🗝️ Furies devant Cole, refusé (elles se figent) | — |
| 20 | ⚔️ maillon ; 🗝️ **Leo ramène Paige au manoir** | ❓ sur la parade ; maillon du tir | passage 20→21 : b-racine VRAIE, m-racine FAUSSE |

Cinq passages ont décidé la partie, et tous les cinq vont au bien : 3→4,
5→6, 8→9, 10→11, 15→16. Le mal n'a gagné aucun passage.

## 2. Où la partie s'est jouée — trois moments

### 2.1 Le tour 3 : la faute d'ouverture du mal

Au tour 2, le mal a joué le meilleur coup possible — le retournement de Paige
dans sa fenêtre, avec exactement les deux pièces que la portée exige — et le
bien a répondu par une **affirmation nue** : une clef sous sa racine disant
que Phoebe a vu la Source sous le visage de Shane. Cette clef n'était pas
posée SUR le retournement ; mécaniquement, elle ne parait rien. Elle
n'affirmait qu'une chose, que la portée de Shane rendait mortelle pour le
mal : *Phoebe l'a touché.*

Le mal avait le tour 3 pour exiger la chaîne — « comment Phoebe
approche-t-elle Shane, à South Bay, en un jour ? » — gratuitement, et la clef
serait passée en suspens jusqu'au maillon. Il a préféré **ouvrir un second
front** (les Furies). L'arbitre avait annoncé sa règle : une clef non
contestée au passage du tour vaut ce qu'elle dit. Au passage 3→4, Shane est
tombé, et avec lui la seule chance de retourner Paige en moins de huit tours.

**La leçon vaut pour tout le jeu** : contre une affirmation qui vous tue, la
question gratuite passe avant tout coup compté. Le mal a su le faire plus
tard (tours 8 et 20) ; il ne l'a pas fait quand ça comptait.

### 2.2 Le tour 4 : le coup double du bien

Shax envoyé sur Paige, avec un piège annoncé — que Leo pare, et le
darklighter du tour 5 le tue. Aurore n'a pris ni Leo ni Paige : elle a posé
**le sort des trois en parade**, ce qui est 4x01 à la lettre. Le heurt tranché
sur cette source a donné : Shax dispersé, Paige intacte, et — parce que les
trois venaient de dire le sort ensemble — **le Pouvoir des Trois constaté
vrai au même passage**. Un coup compté, deux fronts fermés, l'état que sa
racine exigeait en premier, et le piège du darklighter éventé sans qu'on y
touche.

C'est le meilleur coup de la partie : il ne pare pas, il **résout**. La
différence entre les deux est celle que le manuel cherche depuis
`pont-et-moulin` : « la clef qui gagne contourne le verrou, elle ne le force
pas ».

### 2.3 Les tours 13 à 15 : la fin telle que la série l'écrit

Le mal a joué sa fin correctement : la crypte au 12, le Hollow porté par la
Source au 13, ciblant Paige — la plus neuve, celle dont l'orbe pare et dont
la voix manque au sort. Mais porter le Hollow au manoir, c'est **se mettre à
portée**, et l'arbitre l'avait écrit dans la portée de la Source dès
l'ouverture. Le bien avait préparé exactement ce qu'il fallait, deux tours
avant : le sort des aïeules demandé au 11, écrit par le Livre, arrivé au 13.

Le tour 14 (Cole, humain, prend le Hollow en face d'elle) et le tour 15 (les
trois disent le sort pendant que Cole tient) sont 4x13 mot pour mot, et la
partie les a produits **sans que personne ne les récite** : la portée de
Cole disait qu'un mortel peut porter le Hollow, celle du Hollow qu'il dévore
son porteur, celle du sort qu'il exige les trois libres. Le joueur a lu les
cartes et a trouvé l'épisode.

## 3. Le jeu du bien — ce qu'Aurore a fait de juste, et ce qu'elle a payé

**Ce qu'elle a fait de juste.**

- **Elle a joué par états**, ce qu'elle n'avait pas fait dans Charmed 1 : le
  Pouvoir des Trois au 5, Piper au 6, Cole au 9. Chaque état posé a été
  constaté vrai dans les deux tours. Trois états, trois constats, zéro état
  mort au deck.
- **Elle a répondu à chaque question, et vite.** Les deux questions du tour 8
  (sur l'état et sur la clef) ont eu leur maillon et leur clef le tour même ;
  celle du tour 20 aussi. Dans Charmed 1, une question sans réponse avait
  coûté le Livre.
- **Elle a préparé la fin avant qu'elle vienne.** Le sort des aïeules demandé
  au 11, deux tours avant le Hollow, alors que rien ne l'y forçait encore.
  C'est le coup qui a rendu le 15 possible.
- **Elle n'a jamais exposé Leo.** Le darklighter, arrivé au 5, n'a rien eu à
  frapper de toute la partie : Leo est resté au manoir jusqu'au dernier
  tour, et c'est Paige, Piper et le sort qui ont paré. Le piège annoncé par
  la Source au tour 4 n'a pas fonctionné une seule fois.

**Ce qu'elle a payé.**

- **Six coups comptés sur vingt sont partis de travers**, rattrapés par
  l'arbitre : l'état « 3 » (t3), le sort des aïeules réarmé dans une clef
  (t13), le même sort posé en parade pour dire une frappe (t15), la potion
  consumée deux fois (t16, t18), le sort des trois posé en verrou pour tuer
  les chasseurs (t17). Aucun n'a coûté de position, parce que l'arbitre a
  lu l'intention et l'a écrite à la ligne — mais c'est un tiers des coups.
  La cause est double : l'écran n'a pas de geste de frappe, et le grand
  livre montrait « libre » des potions consumées.
- **P3.** Fermé au tour 10 sans parade, et c'était le bon choix : parer
  devant deux cents témoins aurait donné à Cortez sa preuve. Le club est la
  seule pièce du bien perdue de la partie.
- **Un coup passé** (t12), alors que le renoncement du mal pouvait recevoir
  un verrou. Sans conséquence, parce que le mal n'a jamais eu de main pour
  tenir cet état.

## 4. Le jeu du mal — l'IA a joué juste et perdu quand même

**Ce qu'elle a fait de juste.**

- **L'ouverture** : Paige dans sa fenêtre dès le tour 2, avec Shane. Le
  plateau ne permettait rien de mieux.
- **Le calendrier** : chaque pièce datée a été jouée le tour de son arrivée
  — les Furies au 3, la Voyante au 5 (engagée en route), le Hollow au 12-13.
  Elle n'a laissé aucune pièce en branche morte utile.
- **La lecture du plan adverse** : au tour 7, elle a vu que « Piper a pleuré
  Prue » était le seul coup qui cassait les Furies, et elle a posé son
  verrou dessus avant que l'état entre au deck. Au tour 9, elle a frappé P3
  là où aucune parade n'existait sans coût. Au tour 13, elle a choisi Paige
  pour le Hollow, pour la bonne raison (l'orbe et la troisième voix).
- **La voix.** Ses mots dans le fil ont été francs, courts, et ont chaque
  fois dit le piège en face (« un Leo en parade est un Leo qu'une flèche
  peut tuer », « je vous dis pourquoi maintenant »). C'est ce que Charmed 1
  avait de meilleur, et ça a tenu.

**Ce qui l'a fait perdre.**

- **Le tempo du tour 3** (§2.1). Tout part de là.
- **Les questions au mauvais moment.** Deux questions gratuites au tour 8 et
  aucun coup compté : c'était bien vu, mais deux tours trop tard — le bien
  avait déjà la pièce (Leo) et le maillon prêts. Au tour 3, une seule
  question aurait suffi.
- **La clef comme menace.** Trois fois (t14, t16, t18), le mal a posé « le
  prix de Cole » en CLEF sous le renoncement — une menace écrite en clef,
  qui ne tue personne et ne fait renoncer personne. Chaque fois, l'arbitre
  a dû rappeler qu'une clef ne prend rien. Trois coups comptés pour zéro
  effet, dans les six derniers tours.
- **Deux coups refusés par constat acquis** : les Furies rejouées sur Piper
  (t15) et devant Cole (t19), alors que l'état qui les bornait était vrai
  depuis le tour 8. L'IA ne relit pas bien les constats anciens ; elle
  relit ce qui s'est joué depuis son dernier coup.
- **La structure de sa racine.** « Une sœur morte ou servant la Source »
  exige une pièce que le bien tient et pare à volonté. Une fois la Source
  vaincue, le mal n'avait plus RIEN qui serve sa racine — il l'a dit
  lui-même au tour 17 — et il a joué trois tours pour casser le constat
  adverse au lieu de servir le sien.

## 5. Ce que la partie dit du jeu

**L'équilibre était bon, et il penche.** Cinq passages décisifs, tous au
bien. Le bien a plus de parades (quatre pièces) que le mal n'a de frappes
utiles (Shax, le Hollow, les chasseurs, la piétaille), et chaque parade du
bien a été un heurt tranché sur la série — donc en faveur de ce que la
série fait, donc en faveur du bien. Un mal qui joue juste perd contre un
bien qui joue canon. C'est fidèle ; ce n'est pas serré.

Trois réglages possibles pour Charmed 3, sans règle nouvelle :

1. **Une fenêtre plus longue pour Paige** (posé au 2, 3 ou 4) : le mal aurait
   eu le tour 3 pour questionner ET le tour 4 pour reposer.
2. **Un darklighter qui frappe Paige à mort** (moitié être de lumière — la
   série est ambiguë) : la parade de Leo cesserait d'être gratuite.
3. **Le Hollow au 10 au lieu du 12** : le bien n'aurait pas eu ses deux tours
   de préparation ; le sort des aïeules demandé au 11 serait arrivé trop
   tard. C'est le réglage qui change le plus, et il est canon (rien ne date
   le Hollow).

**La question gratuite reste l'arme la plus rentable** — dans les deux
sens. Le bien en a joué cinq, toutes utiles (t2, t6, t11, t12, et le
maillon qui répond) ; le mal en a joué quatre, deux trop tard, deux
inutiles. La partie s'est jouée sur une question non posée au tour 3.

**Un état constaté vrai libère et verrouille à la fois.** « Piper a pleuré
Prue » a fait tomber les Furies au tour 8 ET a rendu irrecevables leurs deux
retours (t15, t19). Trois coups du mal annulés par un seul constat. C'est le
mécanisme le plus fort du greffe, et le bien l'a compris avant le mal :
poser l'état, le servir, le faire constater — puis ne plus y penser.

**La portée fait tout.** Aucun arbitrage de cette partie n'a eu à combler
à froid : chaque refus (huit) a cité une ligne de `portee` ou un épisode.
Le mal a été refusé sur portée cinq fois, le bien deux fois (les fioles) plus
une par duplicata. La table de portée écrite avant la partie est ce qui a
permis d'arbitrer vingt tours sans une seule contestation de fond.

## 6. Les trois coups à retenir

1. **⚫🔒 t4 — le sort des trois en parade sur Shax.** Un coup qui résout au
   lieu de parer, et qui fait constater un état en passant.
2. **🟢🔒 t7 — la piétaille sur « Piper a pleuré Prue ».** Le mal lit le
   plan adverse et bloque le silence dont Piper a besoin, avec sa pièce la
   plus jetable. Le meilleur coup du mal, battu par le meilleur maillon du
   bien (« un paquet par soir »).
3. **⚫➕ t15 — le sort des aïeules posé sur la frappe du Hollow.** Un geste
   d'écran qui ne dit pas ce qu'il veut dire, et qui dit quand même la fin
   de 4x13 : trois voix pendant que Cole tient. Le coup de la partie, et la
   preuve qu'il manque un geste de frappe à l'écran.
