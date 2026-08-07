# La voix de la reine — siège du second joueur

Document de conception. Titulaire imposée : **Aurore Inchauspé**, maison Inchauspé (`aurore-inchauspe`, `maison-inchauspe`, siège `la-noiseraie`). Fichier compagnon : `etat/staging/20260806-160000-siege-voix.json` — rien de ce qui suit n'est écrit dans `etat/`.

Date de référence : **129 AC, 3e lune, 21e jour**. La scène d'entrée se joue au matin, dans la chambre de la Table Peinte.

---

## 0. Ce qu'est la charge

Un office qui n'existe dans aucun usage du Conseil restreint. Son domaine est **ce qui se dit hors de la reine, à l'échelle** — elle ne parle jamais à sa place en sa présence. Sa matière première tient en quatre choses : la version d'un fait, le nom qu'on donne à la chose, l'omission, et le placement des témoins.

Six canaux, tous exprimables dans l'énumération existante de `evenements.diffusion.canal`. Aucun champ nouveau, aucun changement de schéma.

| Canal | `canal` | Fiabilité | Portée | Délai | Révocable ? |
|---|---|---|---|---|---|
| L'acte scellé porté par un homme nommé, lu tout haut | `cavalier` / `barque` | ~90 | une salle, mais indiscutable | plein tarif (`jours_de_pr`) | non |
| Le corbeau particulier, écrit sur mesure par destinataire | `corbeau` | ~85 | qui l'on veut | `jours_de_pr` / 3 | non — et deux lettres contradictoires finissent sur la même table |
| Le héraut et les crieurs | `temoin` | ~80 | une ville | le soir même | oui, jusqu'au lendemain |
| Les chanteurs | `rumeur` | ~30 | le royaume | ×2 le plein tarif | **jamais** — ils improvisent |
| La chaire, les septons | `rumeur` | ~50 | le petit peuple | 6 à 10 jours | non — et le septon ajoute toujours sa phrase |
| Le spectacle : montrer bat dire | `temoin` | ~95 | ceux qui voient, puis tous | immédiat, puis lent | non — coûte une décision de la reine, pas de l'or |

**Les actions négatives sont la moitié du métier** : taire, laisser mourir une nouvelle plutôt que la démentir, démentir quand même, répondre aux Verts, et préempter — faire arriver sa propre version avant celle de l'adversaire chez le même destinataire.

---

## A. La titulaire

Arbitré hors de ce document. Rappel opérationnel seulement :

- `aurore-inchauspe`, 29 ans (née en 100 AC), fille aînée de `maison-inchauspe`, siège `la-noiseraie` (2 jours de Port-Réal, côte nord de la baie de la Néra, entre Rosby et Sombreval).
- **Le négoce, c'est l'encre** — le brou de noix, brune et tenace, bon marché, qui approvisionne les roukeries et les mestres de la moitié du royaume. Elle ne possède pas le message : elle possède le médium.
- **La pupille circulante** : élevée entre huit et dix-huit ans dans cinq maisons — Rosby, Stokeworth, Sombreval, Lamarck, et **l'Île-aux-Pinces** (Celtigar). Elle appelle les grands par le nom de leur nourrice et connaît leurs cuisines mieux que leurs armoiries.
- Fiche complète, blason, or et levées : `personnage_a_ajouter`, `maison_a_ajouter` et `lieu_a_ajouter` dans le fichier de staging, à coller à la main (le vocabulaire de `appliquer.py` ne crée ni personnage, ni maison, ni lieu).
- **Sa faille** : elle a été élevée chez des gens qui vont devoir choisir, et son père vend l'encre aux deux camps à deux jours de route de Port-Réal. Personne à cette table ne saura si elle est fidèle ou seulement bien placée. Cette tension ne se résout pas — c'est le moteur du siège.

---

## B. Ses agents, et leurs horloges

Cinq étapes vivantes, budget `scene` tenu (5 max). Quatre s'appuient sur des gens **qui existent déjà dans l'état** ; la cinquième est la sienne propre.

### 1. `denys-bar-emmon` — l'acte lu tout haut (déjà parti)
Second fils de lord Bar Emmon, dix-neuf ans, embarqué avec l'ambassade pour Sombreval. Sa consigne existante dit qu'il fera lire l'acte « sans l'embellir » — **personne n'a décidé de ce qu'on omettait**. C'est le premier agent, tout trouvé, et il est déjà hors de portée.
- Étape ajoutée : `voix-denys-rapporter-les-mots` — **3 jours** — rapporter, après la lecture, le chiffre que la place redit, le nom qu'on donne aux hommes brûlés, et si l'on dit *la reine* ou *le dragon*.
- Coût : deux jours de barque au retour ; **un homme qui écrive sous sa dictée** — il ne sait pas écrire et l'a dit lui-même deux fois à la reine.
- `si_bloqué` : il apprend par cœur les trois phrases entendues le plus souvent et ne rapporte que celles-là — exactes, incomplètes, sans dire lesquelles manquent.

### 2. `willa-sechoirs` — le bourg, retour immédiat
Porte-parole du bourg sous les murs, cinquantaine, donne toujours le chiffre avant l'opinion. C'est le public de proximité et le seul canal dont le retour arrive en une nuit.
- Étape ajoutée : `voix-willa-crier-au-bourg` — **2 jours** — faire crier la proclamation aux séchoirs et sur le quai aux deux marées, puis rapporter quel chiffre le bourg redit de lui-même, et lequel il a remplacé.
- Coût : deux soirs pris sur son ouvrage à la journée ; **et qu'on réponde enfin à sa question sur l'indemnité des porte-parole**, posée devant trois cents témoins le 19 et restée sans réponse.
- `si_bloqué` : elle le fait quand même cette fois-ci, le dit tout haut là où on l'entend, et envoie quelqu'un d'autre la prochaine.

### 3. `septa-marlow` — la chaire
Dormante ; le staging la promeut `actif` et lui donne une tête d'`orbite`. Neuf septons à portée de barque dans la baie. **La chaire ne s'achète pas, elle se convainc — et elle ajoute toujours sa phrase.**
- Étape d'Aurore : `voix-la-chaire` — **6 jours**, dépend de la proclamation.
- Étape de la septa : `marlow-porter-la-phrase` — **6 jours** — trois barques, neuf visites, 300 dragons d'aumône et de cire « qu'elle refusera d'appeler un paiement ».
- Coût pour Aurore : l'accord de Marlow, 300 dragons, **et la phrase que chaque septon ajoutera et qu'elle ne pourra pas retirer**.
- `si_bloqué` (Aurore) : elle achète les crieurs de trois places de marché — plus court, moins profond, à recommencer chaque lune. `si_bloqué` (Marlow) : elle lit au sept de Peyredragon seulement et laisse dire que la baie s'est tue ; elle ne mentira pas sur l'étendue.

### 4. `rulf-corne` — les onze coques
Maître de port depuis vingt-deux ans, incorruptible, n'a jamais prêté son livre à personne, pas même à un prince. Les onze coques étrangères louées en rade sont **onze équipages qui repartent vers onze ports** : le canal le plus rapide vers l'étranger, et le seul qui ne passe par aucun registre de mestre.
- Étape ajoutée : `voix-rulf-onze-coques` — **3 jours** — une copie de l'acte dans sa langue à chaque capitaine qui appareille, et le port de destination inscrit au livre.
- Coût : onze copies (deux scribes une journée, la cire et l'encre) ; **que la reine tienne le loyer promis le matin du 19 sur les neuf coques**.
- `si_bloqué` : les copies pas prêtes à la marée, il ne retient aucune coque — elles partent sans, il le note à la date, et il ne le répète pas.

### 5. `voix-releve-des-encres` — l'agent structurel, qui n'est qu'à elle
**Le renseignement sans espion.** Le livre de comptes de La Noiseraie dit quelle roukerie a commandé trois fois sa ration ce mois-ci : donc où l'on écrit beaucoup, donc où l'on prépare quelque chose. Il dit **où** et **depuis quand**, jamais **quoi** — c'est ce qui l'empêche de doubler un maître des chuchoteurs, et c'est pourquoi il est lent.
- **9 jours** : un pli à son père (deux jours d'aller, deux de retour par barque), et l'attente de sa réponse.
- Coût : le livre de comptes, qui n'a jamais quitté La Noiseraie ; que son frère accepte de copier trente-neuf lignes sans demander pourquoi ; **et son père, qui refusera si on lui laisse entendre que la reine le lira**.
- `si_bloqué` : elle se rabat sur les quatre dernières livraisons qu'elle a signées elle-même — quatre roukeries au lieu de trente-neuf, et **sans les dates**, ce qui ôte au relevé tout ce qui en faisait un avertissement.
- Ce qu'il porte déjà, de sa seule mémoire : Peyredragon a doublé sa ration cette lune ; **Repos-des-Freux a triplé la sienne en deux lunes.** (Le siège de Repos-des-Freux tombe à la 9e lune. Elle ne le sait pas et ne peut pas le savoir : elle a le chiffre, pas la cause.)

### Support — `aldon-hask` (optionnel)
Compteur des débarquements au quai, méticuleux, rancunier, dormant. Étape `voix-aldon-bruit-du-quai` proposée en posture permanente : à côté du compte des débarquements, la phrase que chaque équipage rapporte du feu et le chiffre de morts qu'il donne — nom du navire, port, date. **Cette mutation ne s'applique que s'il a une tête d'intentions** ; sinon la retirer du lot, `appliquer.py` refuserait l'ensemble.

---

## C. Le dispositif d'entrée — ce que la reine émet déjà sans le savoir

**Elle n'arrive pas pour demander une charge. Elle apporte l'écho.** La charge se crée toute seule à partir de ce que le conseil entend, ou ne se crée pas.

### Elle est déjà dans le château

Aucun voyage à jouer. Quatre raisons, toutes vraies en même temps :

1. **L'alibi.** La roukerie de Peyredragon prend son encre. La guerre a doublé la commande ; elle l'a portée elle-même, ce qu'elle n'avait jamais fait en onze ans de livraisons.
2. **La porte.** `gerardys`, dont toute l'intention est de tenir l'écrit de ce règne, et qui a fait partir dix-sept copies de la déposition dans la nuit du 17. Son premier allié n'est pas la reine : c'est un vieil homme qui manque de papier et qui n'a pas dormi depuis trois nuits. **C'est par sa bouche que la reine entend parler d'elle.**
3. **L'accès.** Lamarck était l'une de ses cinq maisons d'enfance. Elle est entrée dans une suite deux jours après le sacre, quand le château est encore plein de gens venus pour le couronnement et qui ne sont pas repartis.
4. **La faute.** Elle est venue **sans l'accord de son père**, qui livre toujours la Couronne verte à deux jours de route. Elle commence en faute vis-à-vis de sa propre maison, et cela se saura.

### Le lieu, l'heure, la salle

**Chambre de la Table Peinte, Peyredragon. 21e jour de la 3e lune, milieu de matinée.** Marée basse ; la coque de Denys Bar Emmon est partie à l'aube, on la voit encore de la fenêtre est. Sur la table : la lettre à Borros toujours pas signée depuis hier soir, et un jeu de copies que Gerardys n'a pas rangé.

Présents (ids réels, tous à Peyredragon) : `rhaenyra`, `gerardys`, `corlys`, `rhaenys`, `daemon`, `jacaerys`, `robert-quince`. Aurore entre derrière Gerardys, avec la futaille d'encre.

### Ce qu'elle apporte : trois choses émettent sans gouvernail

- **L'acte que Denys porte à Sombreval** pour le faire lire tout haut « sans l'embellir » — personne n'a décidé de ce qu'on omettait, et il est déjà en mer.
- **Le sacre du 18** — le plus fort des canaux, le spectacle, six cents témoins, déjà émis, et pas un seul placé exprès.
- **La route de Sombreval** — depuis cinq jours la nouvelle voyage seule, sans version et sans nom donné à la chose. **C'est le silence le plus coûteux de la partie.**

### Le registre de ses répliques

**Verbatim de route. Des noms de gens ordinaires. Chiffré. Jamais conclusif.** Elle rapporte, elle ne diagnostique pas : elle dit ce qu'elle a entendu et le nom de l'aubergiste, et c'est **Rhaenyra** qui tire la conclusion et qui décide qu'il faut quelqu'un pour ça. Aucune de ses répliques ne contient de recommandation. Aucune ne fait la leçon.

Matériau (à jouer, pas à réciter) :

> « À l'auberge du gué de Rosby, chez Hanna, on ne dit pas qu'elle a brûlé des soldats. On dit qu'elle a brûlé des hommes qui rentraient chez eux. »

> « Six arrêts en deux jours. Personne ne m'a parlé du couronnement. On m'a parlé du feu. Les deux nouvelles sont parties de la même côte à un jour d'écart ; une seule est arrivée. »

> « On n'appelle pas la chose. Ni bataille, ni justice, ni représailles. On dit *le feu de la route*, et on ne met ni roi ni reine dans la même phrase. Perrin le charron, qui roule mes futailles, ne saurait pas dire qui a brûlé qui. Il n'est pas le seul. »

> « Votre roukerie a pris le double de sa ration cette lune. Repos-des-Freux a triplé la sienne en deux. » — *pause* — « Je ne dis pas ce que ça veut dire. Je dis ce que j'ai livré. »

La démonstration entière du métier tient dans la deuxième : **le fait le plus important du règne a été distancé par le feu**, parce que le feu voyage seul et qu'une cérémonie a besoin qu'on la raconte. Aucun conseiller de Rhaenyra ne pense en ces termes.

Ces quatre choses entrent dans `info.json` — voir `info_a_ajouter` dans le staging. `source: "temoin"`, fiabilité 80 à 90 : **le témoignage est sûr quant aux propos, pas quant à ce qu'ils affirment.**

### Ce que chacun a à perdre, et l'objection qu'il lève

C'est une séance de travail. Chaque objection est technique d'abord, chiffrée, et atterrit sur quelqu'un.

| Qui | Ce qu'il perd | Son objection, chiffrée |
|---|---|---|
| `gerardys` | L'écrit du règne est à lui, et il vient de borner son propre mandat devant témoin pour durer | « Combien de corbeaux ? » Dix-sept sont partis le 17 ; il en reste **quatorze**, réservés aux lointains. Un corbeau par destinataire, écrit sur mesure, c'est trente lettres qu'il n'a pas les oiseaux de porter — et **deux lettres contradictoires sur la même table détruisent tout ce qu'il a signé depuis le 17**. Il est pour, et il a peur. |
| `corlys` | Les cales. Il appareille pour le Gosier — 90 nefs, 11 jours | « Six chanteurs, ce sont six places. » Les onze coques louées portent déjà **300 hommes de Cracfosse, 60 fers de lance manquants, le sel et le fil du bourg, et les copies.** Deux jours de mer par rotation. *Vos chanteurs ou mon fer.* |
| `robert-quince` | La sécurité et son mandat : murs, porte, quais, guet, **50 dragons par jour, 200 en urgence** | Douze hommes sont déjà pris sur la muraille pour la cour des requérants. Qui garde les crieurs ? Et **qui répond de ce qu'ils crient quand ils se trompent** ? Il a exclu de lui-même de son mandat « la parole à une maison » : il ne couvrira pas ça. |
| `daemon` | La parole publique, qui lui appartenait par le poignard et le feu | Aucune objection technique — le mépris. « On dit ce qu'on a fait, ou on ne le fait pas. » C'est le vrai rival de la charge, et il entretient déjà sa propre bouche à Port-Réal. |
| `jacaerys` | Rien — **il rend l'office nécessaire et il le dira** | Il s'envole le 4e jour de la 4e lune pour Les Eyrié puis Winterfell. Sept jours de vol, aucun corbeau pour le rattraper. « Quand lord Cregan me demandera devant ses hommes ce qui s'est passé sur cette route, je réponds quoi ? » |
| `rhaenys` | Rien, et c'est pourquoi elle frappe | **Le grief de fidélité** (voir ci-dessous). |

### Les deux griefs

**Le premier — une maison de négoce, pas d'épée.** Porté par `robert-quince` ou `corlys`, à une table de guerre : Inchauspé lève **quarante hommes**. Quarante. Anoblie depuis quatre générations, riche avant d'être noble, un nom qui ne sonne ni andal ni valyrien. On ne donne pas un office du Conseil restreint à des gens qui comptent des futailles.

**Le second — elle vend son encre aux deux camps.** Porté par `rhaenys`, qui en a le rang et la dureté. La Noiseraie est **à deux jours de Port-Réal** et livre toujours les roukeries de la Couronne verte ; le père d'Aurore n'a pas donné son accord à ce voyage et ne le donnera pas. Couper Port-Réal ruinerait sa maison **et la désignerait** : la Couronne saurait en une lune d'où vient la coupure. Élevée chez cinq maisons qui vont toutes devoir choisir.

**La femme a raison ET elle est suspecte. Ne pas résoudre.** Aurore ne se défend pas par un serment : elle répond par le chiffre — ce que la coupure coûte, en combien de jours on remonte à elle — puis propose l'inverse, et ne demande pas la permission de continuer.

### La bifurcation laissée à Rhaenyra

Pas « accepte / refuse ». Trois portes, et une question sous les trois.

- **(a) L'office existe et il est nommé tout haut devant le conseil.** Aurore peut donner des ordres à des porteurs. Daemon se cabre ; Gerardys perd la main sur l'écrit du règne ; le royaume apprend que Peyredragon a créé une charge pour ça.
- **(b) L'office existe sans nom**, payé sur l'or de la maison Inchauspé ou sur la cassette privée d'Elyn Sarnes. Aurore n'a autorité sur personne, doit tout mendier, et **elle est niable**. Le jour où l'on découvre le père, la reine n'a rien signé.
- **(c) L'office est refusé** et la charge retombe sur Gerardys, qui a dit lui-même, la nuit du 19, qu'il ne se voit plus se tromper au moment où il se trompe.

Sous les trois : **qui contresigne.** Et la décision doit atterrir sur un nom avec une échéance — Gerardys, avant vêpres, remet quatre corbeaux ou n'en remet pas ; le vol du soir part au crépuscule.

Demande chiffrée d'Aurore, à opposer aux objections : **3 000 dragons pour la première lune** sur les 40 000 de la cassette (600 aux six chanteurs, 400 aux crieurs de trois villes, 300 d'aumône et de cire pour la chaire, 700 de copies, de cire et de scribes, 1 000 de réserve), **quatre corbeaux sur quatorze**, **aucun homme d'armes, aucune coque de plus** — les onze coques louées portent déjà.

---

## D. La première proclamation — trois versions du même fait

Le fait : le 16e jour, sur la route de Sombreval, la reine sur Syrax a brûlé la tête d'une colonne royale de **douze cents hommes**, Vermax passant deux fois derrière elle ; la colonne est rompue, Sombreval sauvée, **une quarantaine de prisonniers** dont un officier.

**L'état du silence, au 21 :** cinq jours. La lettre de Gunthor Darklyn est partie le soir même par douze corbeaux ; elle a atteint la baie le 17, le Conflans le 20 — et là-bas elle compte déjà **trois mille hommes**. Toute réponse partie le 21 arrive dans la baie le 22 (**6 jours de retard sur le fait, 5 sur Darklyn**), à Accalmie le 24, à Rosby le 26 par cavalier, au Conflans vers le 1er ou le 2 de la 4e lune.

Délais, calculés sur les `jours_de_pr` réels depuis Peyredragon (corbeau ≈ /3, cavalier plein tarif, rumeur ×2) :

| Destination | `jours_de_pr` | Corbeau | Cavalier / barque | Chanteur |
|---|---|---|---|---|
| Sombreval | 3 | 1 j | 2 j | — |
| Pointe-Aigue, Île-aux-Pinces | 5 | 1 j | 2 j | — |
| Repos-des-Freux | 3 | 1 j | 3 j | — |
| Port-Réal | 0 (4 de Peyredragon) | 1 j | 4 j | — |
| Rosby | 1 (5 de Peyredragon) | 2 j | **5 j** | 10 j |
| Accalmie | 9 | **3 j** | 9 j | — |
| Vivesaigues (Conflans) | 16 | 5 j | — | **11 j** |

### Version A — les représailles assumées
> *« Douze cents hommes marchaient sur une ville qui m'avait juré. Je les ai brûlés. Ceux qui marcheront ensuite savent désormais ce qu'il en coûte. »*

- **Canaux** : l'acte scellé, porté et lu tout haut (`cavalier`/`barque`, **fiabilité 90**) ; le héraut au bourg (`temoin`, 80). Une phrase, la même pour tous : rien à écrire sur mesure.
- **Destinataires** : les cinq maisons de la baie, Rosby, Stokeworth, Port-Réal.
- **Coût en retard** : le plus faible. Elle peut partir dans l'heure — corbeaux le 21 au soir, baie le 22. **Mais revendiquer cinq jours après, c'est revendiquer une chose que le royaume a déjà jugée sans elle** : la version de Darklyn (« descendue du ciel pour sauver son vassal ») est plus flatteuse, et cette version-là l'écrase de sa propre main.
- **Ce qui se retournera** : elle devient l'agresseur du royaume par écrit et sous son sceau. Toute maison hésitante des Terres de l'Orage et du Conflans a désormais une pièce à produire. C'est l'acte que `borros-baratheon` fera lire tout haut devant Otto ; et c'est ce que Lucerys trouvera à Accalmie le 4e jour de la 4e lune.

### Version B — la justice sur des hommes en armes  *(retenue dans le staging)*
> *« Ce n'étaient pas des sujets. C'étaient douze cents hommes en armes qui marchaient sans déclaration sur une ville qui avait prêté serment. Ils ont été sommés. Ils n'ont pas répondu. Quarante d'entre eux sont vivants et nourris. »*

- **Canaux** : le corbeau particulier, écrit un par un (`corbeau`, **85**) — Sombreval, Pointe-Aigue, l'Île-aux-Pinces, Repos-des-Freux, **et Port-Réal en préemption** ; l'acte scellé porté à Rosby par un cavalier nommé (`cavalier`, **90**, arrivée le 26) ; le héraut au bourg le soir même (`temoin`, 80) ; six chanteurs vers le Conflans (`rumeur`, 30, arrivée 4e lune jour 2).
- **Coût en retard** : une demi-journée de scribes de plus que la version A — les lettres sur mesure ne se dictent pas en série. Départ au vol du soir du 21, baie le 22. **Retard net : 6 jours sur le fait, 5 sur Darklyn.**
- **Le piège central** : cinq lettres différentes sur le même fait. Celle de Pointe-Aigue nomme le fils ; celle de l'Île-aux-Pinces parle de protection ; celle de Repos-des-Freux rappelle une distance en jours ; celle de Rosby dit que la reine n'a pas encore compté Rosby parmi ceux qui n'ont pas répondu. **Ces gens se parlent.** Celtigar et Bar Emmon ont rembarqué ensemble.
- **Ce qui se retournera** : elle vient de fonder un principe — *marcher en armes sans déclaration sur une ville qui a prêté serment appelle le feu*. Daemon prendra Harrenhal au 20e jour de la 6e lune. Et surtout, la clause dit **« une ville qui a prêté serment »** : Rosby et Stokeworth n'ont pas prêté, n'ont ni répondu ni paru au sacre, et liront cela comme une menace datée. C'est cette clause exacte que Borros retournera le 30.

### Version C — le silence et la diversion
> On ne dit rien du feu. On crie autre chose, plus fort, le même jour : les sept dragons, la cour des requérants tenue le 19, « ceux qui montent », les six cents témoins du sacre.

- **Canaux** : les chanteurs (`rumeur`, 30) et la chaire (`rumeur`, 50) — les deux plus lents, les deux les moins révocables.
- **Coût en retard** : **il est total.** Ne pas répondre concède les quatre jours d'avance de Darklyn définitivement ; et la diversion elle-même met dix à onze jours à porter. Le chiffre de trois mille sera installé au Conflans **avant** qu'aucune autre phrase de Peyredragon n'y arrive.
- **Ce qui se retournera** : le silence laisse la version de Darklyn devenir la seule, et **c'est celle-là qu'on lira dans les annales** — y compris son chiffre. Pire : elle est flatteuse. La reine sera louée pour un fait qu'elle n'a pas raconté, ce qui la met en dette envers Sombreval, et lui ôte tout moyen d'en corriger le compte plus tard sans avoir l'air de se dédire.

---

## E. Ce qui lui revient — trois échos, 8 à 12 jours

Ils reviennent **par les mêmes routes et les mêmes gens** qu'Aurore a nommés au conseil, pour que le joueur reconnaisse les voix. Entrées prêtes dans le staging.

**Écho 1 — la chanson chantée de travers.** *4e lune, jour 1 (dix jours)*, à l'auberge du gué de Rosby, **chez Hanna**. Le refrain repris n'est pas celui qui a été écrit : « douze cents lances sans bannière » se chante mal, « **trois mille hommes sans sépulture** » se chante bien. Deux syllabes de moins. Un couplet que personne n'a composé dit que la reine est restée dans la cendre à regarder. Hanna dit qu'on la lui a apprise et qu'elle ne sait plus par qui. *Le chiffre de la chanson et celui de la lettre de Darklyn sont désormais le même, et il n'est plus rattrapable.* (`rosby`, `rumeur`, fiabilité 20.)

**Écho 2 — le septon qui ajoute sa morale.** *3e lune, jour 29 (huit jours)*, remonté la route de Stokeworth par **Perrin le charron**, celui qui roule les futailles d'encre. La phrase de l'acte a été lue en chaire à Pointe-Aigue et à Sweetport Sound, mot pour mot — puis suivie de celle du septon : *que les Sept n'ont pas donné le feu aux hommes pour trancher leurs querelles, et que ce qui a brûlé une armée brûlera un jour un champ de blé.* Perrin les rapporte cousues en une seule phrase, et personne ne sait plus laquelle vient de la reine. **La chaire sert à moitié** : on retient qu'elle avait le droit, et qu'elle est à craindre. (`stokeworth`, `rumeur`, 50.)

**Écho 3 — le seigneur qui cite l'acte contre elle.** *3e lune, jour 30 (neuf jours)*, à Accalmie. `borros-baratheon` fait relire l'acte tout haut dans sa grande salle, devant `otto` et ses gens, et s'arrête sur la clause : *une ville qui a prêté serment*. Il demande, tout haut, quelle ville des Terres de l'Orage a prêté serment à Rhaenyra — et ce que la reine ferait d'une colonne de **sa** maison marchant vers Sombreval. Personne ne répond ; l'acte reste ouvert sur la table. (`accalmie`, `temoin`, 95.)
Le joueur l'apprend **le 3e jour de la 4e lune** par un capitaine de Sweetport Sound qui tient d'un valet ce qui s'est dit à terre (`info-borros-cite-l-acte`, `rumeur`, 55) — **la veille du jour où Lucerys s'envole pour Accalmie.**

---

## F. Les objectifs de départ du second joueur

Six, tous nés d'une bouche ou d'une route, jamais d'un menu. Format `objectifs.json`, prêts dans `objectifs_a_ajouter`.

| id | titre | source | échéance |
|---|---|---|---|
| `obj-voix-charge-acceptee` | Faire exister la charge devant le conseil | vous-même | 3e lune, j. 21 |
| `obj-voix-dire-le-feu` | Dire enfin le feu de la route de Sombreval | `gerardys` | 3e lune, j. 22 |
| `obj-voix-rattraper-trois-mille` | Rattraper les trois mille | `gerardys` | 4e lune, j. 5 |
| `obj-voix-la-bouche-de-jace` | Donner au prince les mots qu'il portera au Nord | `jacaerys` | 4e lune, j. 4 |
| `obj-voix-l-encre-des-deux-camps` | Répondre de l'encre de son père | `rhaenys` | aucune |
| `obj-voix-payer-les-siens` | Payer ceux qui portent | vous-même | 4e lune, j. 21 |

Le cinquième n'a pas d'échéance et n'en aura jamais : trois issues, toutes coûteuses — couper et se ruiner en se désignant, continuer sans le dire et attendre qu'on le découvre, ou obtenir de la reine qu'elle ordonne elle-même de continuer, **ce qui met la reine dans la faute à la place de la maison**.

---

## Application

`etat/staging/20260806-160000-siege-voix.json` — **20 mutations**, plus quatre charges à coller à la main (`maison_a_ajouter`, `lieu_a_ajouter`, `personnage_a_ajouter`, `objectifs_a_ajouter`, `info_a_ajouter` : ces tables ne sont pas dans le vocabulaire fermé de `appliquer.py`).

Ordre : coller la maison, le lieu et le personnage **d'abord** — sans quoi `tete_ajouter` échoue sur « personnage inconnu » et annule le lot entier. Puis blanc, puis `--vraiment`, puis `tick.py --verifier`.

Pas d'`empreintes` : proposition écrite à la main, sans horloge calculée, la garde de fraîcheur ne s'applique pas. **Le lot suppose la version B.** Pour A ou C, remplacer les neuf diffusions de proclamation par celles décrites plus haut avant d'appliquer ; les trois échos de E dépendent eux aussi de la version retenue.
