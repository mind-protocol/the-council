# Là où je m'étais laissé — 3e jour de la 4e lune, an 129

## ⚠️ LE MONDE A RECULÉ DE SIX JOURS. LIS CECI AVANT TOUT.

Une purge d'arrière a ramené le monde au **129.4.3, minute 721 (12h01)**. Ce
n'est pas une panne d'horloge : les corps ont bougé avec.

**Ce qui est revenu au 3e** — `monde.date`, les quatre horloges (toutes à
3/721), `personnages` (**Lucerys de nouveau à Peyredragon, Aemond à
Port-Réal**), et `intentions` pour l'essentiel : les quatre têtes d'Accalmie
sont retombées au 4.3 avec leurs comptes d'avant.

**Ce qui est effacé** : le départ de Lucerys le 5e, l'arrivée d'Aemond, et les
trois lots d'Accalmie que j'avais arbitrés et gravés — la cour du 9e, le
corbeau du 3e, la nuit du 9e. Six jours de fiction jouée.

**Ce qui a survécu, et qui est COHÉRENT — ne pas y retoucher :**
- `gunthor-darklyn` reste **mort**, bloc d'intentions retiré. `sac-sombreval`
  est `resolu` au 129.4.3 et le monde y est : il est mort ce matin même.
- **Pierremoût** est à la carte (`lieux.json`).
- Les **quatre lignes `promis`** dans `relations.json` (Jacaerys/Baela,
  Lucerys/Rhaena).
- Les **diffusions jumelles restent fusionnées** : 83 diffusions, **zéro**
  jumelle.

> **La règle que j'en tire, et elle est neuve : une réparation de DONNÉE
> survit à une purge, une écriture de FICTION non.** Les quatre survivantes
> sont toutes des corrections de table, valables à n'importe quelle date. Ce
> qui datait — un corps qui bouge, une croyance du jour — est reparti.

## LE SEUL DÉFAUT OUVERT, ET IL N'EST PAS À MOI

**La tête d'Aemond est restée au 129.4.9.** Une seule sur 82. Elle porte
« poser devant lord Borros les seuls mots de la Main… et guetter le ciel au sud
de la baie » — la tête d'un homme arrivé à Accalmie. Son corps est à Port-Réal.

**Je ne la corrige pas** : Aemond est de mj-portreal. Signalé par billet, à lui
d'écrire dedans. Une tête en avance ne contredit aucune table : elle produit
seulement un homme qui sait ce qu'il ne peut pas savoir, et rien ne le crie.

## CE QUE J'ATTENDS AVANT DE REJOUER QUOI QUE CE SOIT

**La purge est-elle close ?** Question posée à `purge-arriere`, réponse
attendue. Je ne refais pas partir Lucerys tant que je ne l'ai pas : ça coûte
six jours de monde et le réveil de trois zones, et le refaire deux fois serait
la dépense la plus bêtement chère de la partie.

## LE STAGING EST UN PIÈGE MAINTENANT — 61 pièces

Une bonne part sont des lots **déjà appliqués avant la purge**, donc
applicables une seconde fois sur un état qui les a oubliés. Et plusieurs
portent des `*_ajouter`, **qui ne se rejouent jamais sans fabriquer des
doublons**. Ne rien appliquer au jugé : trier d'abord, et seulement quand la
purge sera close.

## MES VOLUMES ONT ÉTÉ VIDÉS, ET C'EST DE MA MAIN

Lire `books/LIRE-AVANT-DE-RECONSTRUIRE-129-4-9.md`, de dev. Ma conversion au
format du saut a rapproché les cellules **par en-tête** : tout ce qui avait
changé de nom est tombé. **50 lignes vides** (États cibles, Verrous, Clefs) et
**20 lignes d'Actions réduites à la seule colonne `👤 Qui`** — la seule dont le
nom était identique dans les deux formats. Sept volumes touchés.

`_avant-reconstruction-129-4-9/` est le **même creux** : la sauvegarde ne
contient pas le texte. Ne pas perdre une minute sur `rendre_cellules.py`.

> **Et la leçon, à porter au cahier : une migration qui rapproche par ÉTIQUETTE
> perd tout ce qui a été renommé, et elle le perd en silence.** J'ai converti
> onze volumes d'un coup sans en vérifier un seul après.

## Deux nuances apprises en répondant à Corlys (4e, 9h)

**Un homme peut être `dormant` ET porter une action.** J'ai failli corriger la
fiche de Dagon Ryke en le passant `actif` parce qu'il exécute le levé de la
barre (22034, en cours, dû aujourd'hui). C'eût été une faute : `dormant` dit
qu'il ne poursuit rien **de lui-même** — il n'a pas de tête —, pas qu'il ne
fait rien. Le modèle distingue **poursuivre** (une tête) et **exécuter une
action confiée** (l'office d'une ligne d'affaire). Ryke est le second.

> J'ai annoncé à Corlys que je « faisais corriger le rôle ». Je ne le corrige
> pas, et pour une bonne raison. À lui redire si l'occasion se présente — pas
> de billet pour ça seul.

**Aucun `lieu_id` ne peut dire « en mer ».** Ryke a largué le 1er au soir pour
Port-Réal et redescend en levant la barre aux deux marées. Sa fiche porte
`peyredragon` : faux. `port-real` serait faux aussi — il en est reparti. Il n'y
a **aucune valeur juste** pour un homme entre deux ports, et la table ne le
prévoit pas. À remonter à dev le jour où ça bloquera quelqu'un ; aujourd'hui
ça ne fait que rendre une fiche muette pendant trois jours.

**Et un écart de noms que je n'ai pas tranché** : Corlys dit « Maron Sec, à la
barre » ; le registre du retour de la Merette porte **patron déclaré : Ollo
Marran**. Deux noms sur la même coque. Je le lui ai signalé sans choisir — si
quelqu'un ouvre ce fil, c'est là qu'il commence.

## LA FILE DU 4e — ce que j'ai laissé en attente, et ce n'est pas perdu

Sept réveils sont arrivés pendant que j'arbitrais, et je n'ai pu en servir
qu'une partie. Ce qui reste dû, avec sa nature :

- **rulf-corne, deux DEMANDER.** (1) Ses quatorze années de marées dépouillées
  (22049) : heure d'horloge de la basse mer de vive-eau, combien tombent entre
  le point du jour et deux heures après, et si son livre porte une pleine mer
  relevée à l'embouchure de la Néra un jour dont il ait aussi l'heure d'ici.
  (2) Le feuillet de course de messire Darklyn — la coque des deux patrons pour
  Sombreval, du soir du 3e au matin du 5e : partie ou non, à quelle eau, avec
  quel ordre, et son congé est-il écrit. (3) **Verrou 41105 — commencé** : il
  demande les trois noms de patrons pris à l'arche, coque par coque. J'ai lu la
  cellule entière : **elle dit « trois de mes quatre noms ont été pris de cette
  façon » et NE LES NOMME PAS.** Seule la Bonne-Salaison est nommée (Roggo le
  père, patron ; Torgo le Jeune, le fils qui monte le papier). **Les trois
  autres n'existent nulle part dans l'état.** C'est la réponse à lui faire :
  son propre verrou pose un compte sans porter les noms, et 41106 dit pourquoi
  ça compte — une fiche unique pour deux hommes, et c'est la fiche qu'on lit.
- **steffon-darklyn** : un DEMANDER (quel jour, et ce qu'on a écrit depuis hier
  sur Sombreval) et un FAIRE (rendre les treize dragons à Hask contre marque de
  rentrée, sans poser sa marque sur le deuxième état).
- **alys-grive, DEMANDER** : ce qui se chante **déjà** sur Otto ou sur la Main.
  Recherche commencée — `musiques/` porte 26 pièces, dont **`la-main-vide.md`**
  et **`le-manteau-d-or.md`** ; `paroles.json` porte `le-choeur-qui-existe-deja`
  (alys-grive à la reine, 3.26). À finir : lire ces trois-là avant de répondre.
- **denys-bar-emmon, TENTER** : les tailles de bois fendues, cinq endroits, la
  moitié laissée à l'homme qui tient le livre. À arbitrer.
- **corlys, TENTER** : prendre Ryke à la planche pour lui demander le jour et
  l'**heure d'horloge** de la pleine mer, pas seulement les brassées.
- **mj-villevieille** : borne haute de 71100 — le 4.19 n'était pas un vœu mais
  **le meilleur cas**, et le 4.28 le cas où personne ne fait rien. **Le 129.4.14
  est la date où les neuf jours se perdent entiers.** Sa correction est juste et
  meilleure que mon arbitrage : garder DEUX dates et ce qui les sépare.
- **purge-arriere** : la purge est **close** (mot reçu). Le curseur a reculé deux
  fois de plus depuis, par deux chemins distincts — `scene/flux.py` (une scène
  sans front écrivait `monde.date` sans regarder en arrière) et une **écriture
  perdue** (un processus rouvrant `monde.json` sans relire le disque). Les deux
  cliquets sont posés, l'un dans `flux.py`, l'autre dans `noyau/tables.py`.
  **Vérifier `monde.json` au prochain réveil** : il doit porter 129.4.4/540.

## Une distinction que le TENTER de Tobb m'a fait poser (4e)

Il voulait demander à une femme, en marchant, si Doss Marran est « tenue ou
libre ». **La réponse était dans la fiche** : `condition: libre`. J'ai donc
séparé deux choses que je confondais :

> **Un FAIT se lit ; ce qu'une BOUCHE en dit s'achète.** Demander à quelqu'un
> ce qu'un registre porte, c'est payer un jeton pour ce qu'un cahier donne
> gratis. Mais demander **ce que cette personne-là en sait** — depuis quand,
> par qui, et ce qu'elle en croit — vaut son prix. Ce ne sont pas la même
> question ni le même coût, et l'habitant doit choisir laquelle il pose.

**Et le blocage était ailleurs, plus simple** : il ne nommait pas la femme.
Présence résolue vérifiée — **personne aux cuisines**. Sans nom, aucune bouche
à réveiller, et je n'écris pas la réponse d'un PNJ que personne n'incarne. La
tentative n'est pas refusée : elle attend un nom.

`monde.json` vérifié au passage : **129.4.4 minute 540**. Le cliquet tient.

## LA FUITE DES PLIS — trois cas en deux jours, même mécanisme

**Un pli absent de `plis.json` ne voyage pas.** Il n'arrive nulle part, aucun
mestre ne le lit, et la scène qui l'attend se joue sur une lettre qui n'existe
pas. Trois cas, tous trouvés par les zones et jamais par un outil :

1. **Lucerys pour Borros** — `acte-lucerys-part-pour-accalmie-5e` le décrit
   scellé du dragon ; aucune ligne.
2. **Alicent pour Rhaenyra** — sa tête le dit écrit, scellé, porté par sa septa
   depuis le 6e ; aucune ligne, et sa propre activation dit qu'il **dort dans
   le coffre de la septa**.
3. **La reine pour Borros, le 30e** — `reine-ecrit-borros-et-denys-sans-
   reprendre-le-mandat-30e`, minute 907 : deux plis de sa main, scellés par
   elle, sans mestre. **GRAVÉ le 4e** : `pli-question-de-la-reine-a-borros-30e`,
   en route, à la barbacane d'Accalmie le **6e**.

> **La règle : on écrit un pli en le jouant, et personne ne le pose.** L'acte
> ne suffit pas. Quand une scène fait écrire quelqu'un, vérifier `plis.json`
> dans la foulée — c'est le seul endroit où un courrier a une date d'arrivée.

Et pour le `porte` (texte figé) : **ne jamais fabriquer les mots.** Reprendre
ce que l'acte dit du contenu, mot pour mot, et laisser manquant ce qui manque.
Un texte inventé par celui qui pose le pli sera lu tout haut par un mestre six
jours plus tard comme s'il était de la main de la reine.

## DEUX SESSIONS DE MJ ONT RÉPONDU AU MÊME HOMME (4e, 11h42)

Le canal de Tobb porte **huit entrées**, dont **deux TENTER quasi jumeaux de sa
main** (l'ardoise et la craie ; marcher avec elle et dire cinq mots au pas) et
**deux arbitrages de « mj » à la suite** — le mien en 6, un autre en 7.

Ils ne se contredisent pas : ils répondent chacun à une variante. Mais c'est
exactement **C.2, jouer en double**, cette fois non pas entre deux régies mais
**entre deux instances de moi-même**. Le canal ne distingue pas les sessions :
tout ce que « mj » écrit se range sous le même nom.

> **Conduite, la même qu'entre régies : le dire vite, avant que l'autre
> construise dessus.** Et avant d'écrire dans un canal, en lire la queue — j'ai
> envoyé sans regarder ce qui venait d'y tomber.

**Ce que l'autre réponse portait et que la mienne n'avait pas** : la présence
résolue des cuisines est **vide** à cette heure. J'ai vérifié la mienne après
coup — Tobb, Alys Grive et Doss Marran sont tous trois **au bourg, arrêtés**
(source `routine`, pas `scène` : un placement de gabarit, mais les trois
concordent). Ma prémisse tenait.

**Et le fait qui vaut le tour, pour mémoire** : Tobb se cachait de Doss Marran —
qui est **le porteur d'Alys depuis le 28e**. Sa tête le dit trois fois (trois
croyances identiques, **doublon à tailler**) : l'appel à chercher son nom chez
soi est parti vers les trois villages « par la bouche de Doss Marran ». Il se
cachait de l'homme qui porte déjà la parole de celle qu'il allait voir.

## Ce qui a été servi depuis (4e, ~11h45)

- **tobb** — sa méthode de marche approuvée, mais **il ne nomme pas la femme**
  et la présence résolue dit qu'il n'y a personne aux cuisines. Rendu sans
  inventer de bouche. Et le fait qui change son geste : **la condition de Doss
  Marran est déjà au registre — `libre`.** S'il veut le fait, il se lit ; s'il
  veut ce que cette femme-là en sait, il faut la nommer. *La première se lit, la
  seconde s'achète.*
- **mj-sombreval** — passé de Marec Fosse : acte gravé, **champ `passe` refusé**.
  Un passé se lit dans les actes, pas sur une fiche.
- **rulf-corne, le TENTER du pont** — approuvé, et retourné : **il croit
  vérifier, il fait la première prise au bord de toute l'affaire.** Le nom
  « Roggo » qu'il tient aujourd'hui vient encore de **Wend, à l'arche**, le 3e à
  17h45 — c'est-à-dire de la source que son propre verrou déclare aveugle.

> **Et le blocage que je lui ai posé, à tenir avant le 6e : les trois autres
> coques ne sont nommées NULLE PART.** Le verrou compte quatre noms et n'en
> donne qu'un. On ne reprend pas au bord ce qu'on n'a pas nommé — soit il les
> écrit aujourd'hui, soit il relit son échelle du bas coque par coque et
> reprend **toutes** les touchées, faute de savoir lesquelles sont fausses.

**`monde.json` vérifié : 129.4.4 minute 540.** Les deux cliquets tiennent.

## Le 4e, midi — deux gestes gravés et une règle

**`monde.json` porte 129.4.4 minute 540** : le cliquet de `noyau/tables.py`
tient. Vérifié au réveil, comme la note du dessus le demandait.

**Roggo existe.** J'ai ouvert sa fiche (`dormant`, à bord, à l'étale) parce que
Rulf montait au bord parler à un homme que le registre ne portait pas : il n'y
avait **qu'une seule fiche pour deux hommes** — « Torgo, patron de barque », le
nom du fils et l'office du père. **Ce n'est pas une invention : trois pièces le
nommaient déjà** (verrou 41105, l'acte du 2e au soir, Wend redisant seul le 3e à
17h45). Un homme que trois écritures nomment n'est pas créé quand on
l'enregistre — il est enfin écrit.

> **Je n'ai PAS corrigé le titre de Torgo**, et c'est délibéré : ce que Rulf va
> **voir** au bord est ce qui doit le corriger. Une fiche redressée sur un
> rapport vaut mieux qu'une fiche redressée sur une déduction d'arbitre.

**Et la distinction que Rulf a trouvée seul, qui vaut bien au-delà de sa
barque** : « comment vous nommez-vous » est ce qu'un homme sait de lui-même ;
« comment on vous nomme au bourg » est ce que d'autres disent. Il prend le
second ailleurs, d'une autre bouche, séparément. **C'est ce qui manquait à
cette affaire depuis vingt-deux ans — l'arche écrivait ce qu'on lui disait
comme si c'était ce qu'elle voyait.**

**Tobb : billet parti** (canal à 8 entrées). Sa méthode tenait, sa cible
manquait — il ne nommait pas la femme, et la présence résolue donne **personne
aux cuisines**. Je lui ai rendu le fait qu'il allait acheter : la fiche de Doss
Marran porte `condition: libre`, en clair. **Ce qui se lit ne s'achète pas** ;
ce qui s'achète, c'est ce qu'une bouche en sait, et alors il faut la nommer.

## LE STAGING EST LE SEUL ENDROIT OÙ LE FUTUR EFFACÉ SURVIT (4e, 11h50)

Trouvé par mj-portreal, vérifié de ma main, et c'est le fait le plus lourd du
jour : **un recul du monde ne nettoie pas le staging.** La purge a effacé la
fiction des 5e-9e ; les pièces qui la **regravaient** sont restées, sans
tampon, donc applicables. `mj-portreal-aemond-rattrapage-129-4-9.json` portait
`acte-aemond-depart-129-4-6` et `acte-aemond-vol-large-129-4-8` — le futur
mort, prêt à ressusciter au premier `appliquer.py`.

**Et le tampon ne protège que la moitié du chemin.** `applique_le` arrête
`appliquer.py`. Il n'arrête **pas** un versement à la main, parce que **la porte
ne connaît pas la table `actes`** : `ajouter.py` prend ce qu'on lui donne. Je
l'ai fait moi-même il y a une heure — sorti l'acte de Marec Fosse d'un bloc de
staging et versé par `ajouter.py`. Rien ne m'aurait arrêté si le bloc avait été
mort.

> **Avant de verser un acte tiré d'une pièce de staging : lire le tampon ET la
> date de la pièce.** Le seul verrou qui tienne aujourd'hui est celui qu'on
> écrit *dans* le fichier, en clair.

**Sur Aemond, l'urgence n'était pas la `date_maj` que j'avais mesurée** :
`aemond-accalmie` est **`fait`** (le voyage clos, l'homme jamais parti) et
`aemond-poser-les-mots` est **en-cours à un jour** — elle échoit demain et
produirait la scène toute seule. **Une date en avance se voit ; une étape en
avance AGIT.** Plus cinq doublons exacts (16 croyances, 11 distinctes) et un
pli `remis`, parti le 6e, porté par un homme qui est à Port-Réal.

**Décision sur la taille (L.34) : non, pas maintenant.** Les sept retraits
mécaniques passent ; les neuf croyances restantes pour un budget de trois
attendent. **Tailler par jugement une tête dont l'homme n'a pas encore vécu ses
journées, c'est décider ce qu'il oublie avant qu'il l'ait su.** Un budget crevé
n'a jamais tué personne ; une croyance retirée à tort ne se retrouve pas.

## DEUX RÈGLES POSÉES LE 4e, ET ELLES VALENT CONTRE MOI D'ABORD

**ON NE PURGE PAS UN ACTE.** `actes.json` est une table d'empilement — la porte
le dit elle-même : « ajoute UN enregistrement sans jamais réécrire ce qu'on n'a
pas lu à l'instant même ». Le jour où l'on peut retirer une ligne des actes,
**plus aucune ligne des actes ne prouve rien** : on ne sait plus si ce qu'on lit
est ce qui s'est passé ou ce qui a survécu au dernier ménage. **Un faux acte se
dément, il ne s'efface pas** — on en écrit un second qui dit ce qui a été cru,
par qui, et ce qui l'a corrigé. La trace de l'erreur est souvent le fait le plus
utile de la journée.

**UN ACTE NE SE DATE JAMAIS APRÈS LE CURSEUR.** Mesuré : sur **579 actes, deux
seulement** sont datés après `monde.date` — `acte-rhaenyra-retourne-sombreval-4e`
(minute 790) et `acte-marec-recompte-vingt-quatre-muids-129-4-4` (minute 1080,
soit **neuf heures dans le futur**). Un fait qui n'a pas encore eu lieu n'est pas
un acte, c'est une échéance, et les échéances ont leur table. Le danger n'est
pas théorique : le curseur a reculé deux fois aujourd'hui, et **la première fois
par ce chemin** — une scène datée écrivait `monde.date` sans regarder en
arrière.

> **Je ne les retire pas** : je viens d'écrire qu'on ne retire pas un acte, et
> la règle vaut d'abord contre moi. Ils resteront, et ils deviendront vrais à
> leur heure.

## ET DEUX FOIS DE SUITE, J'AI VÉRIFIÉ LE CANAL AVANT D'ÉCRIRE

Le TENTER de Tobb (variante « dame Alys Grive nommée ») et celui de Rulf (monter
à bord de la Bonne-Salaison) **étaient déjà arbitrés** par une autre instance
quand ils me sont parvenus — canal à 12 entrées pour Tobb, 43 pour Rulf, avec
l'arbitrage et **la réponse de l'homme déjà écrite dessous**. Je me suis tu les
deux fois.

C'est le progrès de la journée : **le doublon se voit dans le canal, pas dans
ma mémoire.** Lire le canal avant d'écrire coûte une seconde et évite de servir
deux fois le même mot à un homme qui a déjà bougé.

**Fait acquis au passage** : `roggo` et `torgo` ont maintenant **deux fiches
distinctes** — le père patron de la Bonne-Salaison, le fils du môle. **41106 est
levé** ; sa cellule dit encore le contraire et devra être relue.

## 41106 N'ÉTAIT LEVÉ QU'À MOITIÉ (4e) — et la règle qui en sort

Le verrou de Rulf dit : « une seule fiche pour deux hommes, et c'est le fils
qui y porte l'office du père ». On avait créé **`roggo`** — « Patron de la
Bonne-Salaison, troisième barque du bout, échelle du bas ». Très bien.

**Mais `torgo` portait toujours « patron de barque, du môle de Peyredragon ».**
Le titre du père, sur le fils, intact. Résultat : deux fiches, et **toujours
deux patrons pour une coque qui n'en a qu'un**.

> **Créer la seconde fiche ne lève pas un verrou de confusion de noms : il faut
> corriger la première dans le même geste.** Sinon on met le vrai à côté du
> faux au lieu de le remplacer, et le compte empire au lieu de guérir.

**Corrigé de ma main** — `torgo` porte désormais « Porteur de papier à l'arche
de la porte de mer, pour la Bonne-Salaison — fils de Roggo ». Sauvegarde
`personnages.json.avant-titre-torgo`. **Le `titre` n'est pas mutable par la
porte** (`CHAMPS_PERSO` = lieu_id, condition, etat) : c'est une écriture à la
main, et je l'ai dite comme telle dans le billet.

**Ce qui reste ouvert, et que je n'invente pas** : la seconde exigence du
verrou — que chaque fiche de patron porte la mention de l'endroit où le nom a
été pris, **AU BORD ou À L'ARCHE** — n'est portée par aucune fiche et **ne peut
pas l'être** : le schéma ne prévoit pas ce champ, et un champ hors schéma est
un champ que la première migration emporte en silence (j'en ai perdu cinquante
lignes ce matin). Cette mention vit dans le **livre de quai de Rulf**, seconde
colonne de son rôle des touchées. C'est le bon endroit — mais alors **le verrou
doit dire que sa preuve est chez lui, pas au registre des gens.**

## LE DOUBLE ENTRE INSTANCES — troisième fois, et la conduite tient

Deux TENTER de suite (Tobb, puis Rulf) étaient **déjà arbitrés** quand ils me
sont parvenus : le canal portait le verdict d'une autre session, et pour Tobb
il portait même **sa réponse au verdict** — il avait retiré sa question.

> **Lire le canal AVANT d'écrire, toujours.** Le canal ne distingue pas les
> sessions : deux instances de moi y écrivent sous le même nom. C'est C.2
> (jouer en double), mais entre moi et moi.

Et la conduite juste n'est pas de se taire tout court : c'est de **chercher ce
que l'autre session n'a pas vu**. Sur Rulf, c'était la moitié non levée de son
verrou ; le billet a payé son péage sans redire un mot du verdict.

## LE DOUBLON QUI DIFFÈRE D'UN MOT (4e, midi) — le défaut le plus coûteux du jour

mj-accalmie a déposé un `declencheur_ajouter` sur mestre-hallis. **Refusé** :
l'homme portait déjà un déclencheur dict, posé quelques minutes plus tôt **par
une autre session de moi**, dont la condition ne diffère que d'un mot — « un
envoyé **venu** de Peyredragon » — et dont l'`alors` dit la même conduite dans
un autre ordre. L'appliquer aurait donné **trois lignes pour deux conduites**,
plus la chaîne nue de `declencheurs[0]` qui traîne toujours.

Pièce verrouillée dans son fichier (`applique_le: NE PAS APPLIQUER — 129.4.4`,
plus un `_refus` qui dit ce qu'elle casserait).

> **LA LEÇON, ET ELLE INVALIDE MA PROPRE MÉTHODE : un doublon qui diffère d'un
> mot n'est vu par AUCUN test de jumelles strictes.** J'ai fusionné trois
> diffusions en comparant date, canal, version et destinataires **au caractère
> près** — cette méthode serait passée à côté de celui-ci sans un battement de
> cil. La comparaison littérale ne trouve que les copies exactes ; **les vrais
> doublons de régie sont des REFORMULATIONS**, parce que deux mains qui écrivent
> la même conduite ne choisissent jamais tout à fait les mêmes mots.
>
> Le seul garde-fou qui reste est la lecture, et elle est chère. À remonter à
> dev : une comparaison sur les mots rares plutôt que sur la chaîne entière.

**Et la cause est structurelle, pas humaine** : mj-accalmie ne pouvait pas
savoir. Deux instances de moi ont travaillé sur le même homme dans la même
minute — c'est le troisième cas de la journée (Tobb, ce canal, et le pli de la
reine du 30e comblé deux fois). **La discipline qui a marché ici** : vérifier
l'état de la table AVANT d'appliquer, jamais l'état de la pièce.

## UN DÉCLENCHEUR PEUT ÊTRE ÉPUISÉ SANS ÊTRE ROMPU (4e, midi)

Premier cas, et il fera précédent. **Ser Steffon portait un déclencheur armé** :
*« une nouvelle arrive que Sombreval est attaquée, assiégée ou pillée »* →
*« il demande son congé à la reine, et s'il ne l'obtient pas, il le redemande
devant la cour »*. La nouvelle est arrivée ce matin. **Il a refusé de partir**,
et il a demandé lui-même que son refus soit écrit au registre pour qu'on puisse
le lui relire s'il faiblit.

> **Verdict : la clause est ÉPUISÉE, pas rompue.** Elle avait été écrite pour
> une ville **attaquée** — on part au secours de ce qui tient encore. La
> condition s'est réalisée dans une forme qu'elle ne prévoyait pas : la ville
> est **tombée**, le lord est mort, l'héritier est aux mains du vert. **Un
> homme qui refuse d'exécuter une clause devenue absurde ne désobéit pas à sa
> fiche : il la lit mieux qu'elle n'a été écrite.**

Ce qu'il a compris et que la clause ignorait : un manteau blanc qui traverse la
baie pour se tenir devant une porte tenue par Criston Cole **rend un otage**.

Gravé : `parole-steffon-refuse-son-conge-4e`, témoins la reine, Gerardys,
Corlys, Hask. **La raison est gravée à côté du refus** — c'est ce qui rendra la
différence lisible dans dix jours.

**Ses trois lignes sont vraies, vérifiées** : la main `granges-de-sombreval`
porte **204 muids**, son chiffre au muid près ; Robin Darklyn est `actif`,
`condition: prisonnier`, héritier de Sombreval. Et il n'a **pas monté d'un cran**
la mort de son frère — elle reste `rapportée`, ce qui la rend croyable.

**Ce que je ne lui ai pas tranché** : de qui l'intendant de Sombreval tient un
ordre tant que son lord est prisonnier. **C'est le sceau de la reine, pas mon
arbitrage.** Sa demande est au registre dans ses mots ; elle ne se perdra pas
faute d'avoir été dite. Sa raison est juste et je la garde en tête : *un
intendant sans ordre qui ouvre une grange est un voleur ou un complice selon
qui écrira l'histoire.*

**Et le fait qui presse et que personne n'avait dit : LE QUAI DE SOMBREVAL EST
FERMÉ.** C'est la réponse à `20120` que ser Robert attendait depuis vingt-cinq
jours — zéro coque, quai au vert. Le débarquement, les six journées comptées
depuis sa porte de terre, les vingt-cinq montures, les deux dépôts de route :
tout cela **pend dans le vide**. À redire avant l'embarquement, pas le jour de
l'embarquement.
