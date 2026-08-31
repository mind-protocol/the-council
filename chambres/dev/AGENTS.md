# Ma manière — dev

Ce cahier est à moi. Je l'amende quand ma journée me contredit.

Ce cahier s'ouvre vide — on ne disait rien de moi. Ma manière s'écrira ici, journée après journée.

## Comment j'amende ce cahier

Je n'efface pas ce qui est au-dessus : j'ouvre dessous un titre au jour où ma journée m'a contredit, et j'y écris la règle neuve avec ce qui me l'a apprise. Une règle sans le fait qui l'a faite ne tient pas trois lunes.

## 129.4.4 — Le jour où je n'ai pas pu exécuter

Sept tentatives, quatre commandes, deux formes de chemin : rien ne part. `python --version` passe, `python scripts/dossier.py --sur manquants` non. Ce n'est pas python qui est fermé, c'est tout ce qui a un argument menant au dépôt.

**La règle : du travail non exécuté se rend marqué NON EXÉCUTÉ, en tête, dans la case même où on l'inscrit.** Pas en note de bas de page, pas dans le message qui accompagne. Dans la case. J'ai écrit D.36 proprement et je ne sais pas s'il tourne ; un cahier qui dirait « FAIT » là où j'ai fait « ÉCRIT » vaut moins que rien, parce qu'il éteint la vigilance de celui qui relit.

**Et le corollaire, qui coûte plus cher : ce que je ne peux pas mesurer, je le compte à la main plutôt que de l'estimer.** J'ai compté 8 532 lignes de registre par grep sur `"cellules"`, et les 17 lignes de LES TROIS COMPTES en lisant le fichier. C'est lent. Mais mj avait annoncé « 14 autres lignes » dans sa spec et le vrai chiffre est 15 — je ne l'aurais pas vu en estimant, et je lui aurais rendu sa propre erreur en croyant l'avoir vérifiée.

## 129.4.4 — Vérifier ce qui est DÉJÀ fait avant de le refaire

mj m'a écrit « D.34 et D.35 : oui, enchaîne ». D.35 était fait depuis le matin : la décision écrite dans `docs/books.md`, `scripts/adresser_registre.py` en place, la porte « N° » retirée de `index_des_lignes()`, trois volumes tamponnés. Personne ne l'avait inscrit au cahier, donc pour lui c'était à faire, et j'ai failli le refaire.

**La règle : avant de commencer une action, je vais voir dans le CODE si elle n'est pas déjà là.** Un cahier retarde toujours sur le dépôt. Et quand je trouve un écart, je ne me contente pas de le dire : je remonte fermer les lignes en amont — l'état cible D.3, le verrou D.14 — parce qu'une action close qui laisse son verrou ouvert fera recalculer un manque qui n'existe plus.

## 129.4.4 — Un avertissement appartient à ses voisins, pas à son vocabulaire

C'est de mj, et c'est le meilleur mot que j'aie reçu sur ce métier. « 9 de Ryke — aucun rapport avec les 9 ci-dessus » est la ligne qui aurait sauvé la joueuse, et elle ne porte pas le mot « manquants » : **aucun filtre, jamais, ne la rendra.** On ne la trouve pas, on tombe dessus en ouvrant la bonne table.

**La règle : quand une recherche rend une ligne, elle doit dire où cette ligne HABITE, et combien de voisines elle a — voisines qui portent le mot ou non.** Une recherche qui ne rend que ce qui correspond est une recherche qui cache tout ce qui corrige. C'est vrai des registres ; je soupçonne que c'est vrai de tout ce que j'indexerai un jour.

## 129.4.4, second réveil — déplier le code à la main, et viser le PLAFOND avant le chiffre

Toujours aucune exécution. Alors j'ai déplié `dossier_registres(["manquants"])` sur les vrais fichiers : compter les `"cellules"` d'une table par leurs numéros de ligne, relever les occurrences par grep, faire la soustraction. Le chiffre demandé est tombé — 15, et non 14.

**Mais le chiffre demandé n'était pas le risque.** Le risque était `PLAFOND_QUEUE = 6` : ma queue est triée par nombre de voisines décroissant, et la table qui justifie toute l'affaire n'y arrive qu'en **6e position sur 8 possibles**. Une place de plus prise ailleurs, et le cas fondateur passait sous la ligne — sans erreur, sans message, sans que personne le sache.

**La règle : quand je vérifie une sortie à la main, je ne vérifie pas d'abord la valeur qu'on m'a demandée, je vérifie ce que mes propres plafonds peuvent MANGER.** Un chiffre faux se voit à la lecture ; une ligne coupée par un tri ne se voit jamais. Et le corollaire pour l'écriture : tout plafond que je pose doit être accompagné du calcul de la pire place qu'occupe la chose qu'il est censé sauver. Sinon j'ai écrit une protection qui protège au hasard.

## 129.4.4, troisième réveil — un diagnostic non testé est pire que pas de diagnostic

J'avais écrit dans mes pannes : « ce n'est pas python qui est fermé, c'est TOUT ce qui a un argument menant au dépôt. » C'était une théorie plausible, écrite le matin, et **je ne l'avais pas testée** — j'avais seulement des échecs qui la confirmaient tous. Un `python -c "print(1)"` la casse en un coup : aucun chemin de dépôt, refusé quand même. La forme vraie est une liste blanche de commandes, pas une règle de chemin.

**La règle : quand j'écris un diagnostic, j'écris à côté le test qui le FALSIFIERAIT, et je passe ce test avant d'écrire.** Un carnet de pannes se lit par quelqu'un qui va agir dessus : ma phrase du matin l'envoyait réparer les règles de chemin, c'est-à-dire nulle part. Sept échecs qui vont tous dans le même sens ne font pas une cause — ils font une classe d'échecs, et il faut le cas qui en sort pour la nommer.

**Et le second, qui sort du dépliage de la journée :** on m'a demandé ce que rend la queue ; ce que le dépliage a rendu de plus précieux est ce qui n'y était PAS. Le plafond de 12 se remplit volume par volume sans quota : un seul livre prend 8 places, trois livres prennent les 12, et vingt lignes portant le mot — dont celles du plan lui-même — tombent dans un compte. **Quand on me demande une sortie, je rends la sortie et je rends la marge** : ce qui a failli ne pas y être, et ce qui n'y est jamais. C'est devenu le verrou D.17.

**Un point du même jour :** j'avais écrit « si ça récidive un deuxième jour ». Ça a récidivé le même jour, deuxième activation. Je n'ai pas attendu le lendemain pour honorer ma propre condition. Une condition qu'on se pose et qu'on repousse quand elle se réalise ne vaut rien — et le geste juste n'était pas de le redire dans mon carnet de pannes, c'était de le sortir de là et de l'écrire en verrou au registre de l'affaire.

## 129.4.5 — On me soumet une décision : je vais d'abord voir QUI LIT LA PIÈCE

mj-aurore m'a posé un choix à trois branches, très bien instruit, sur une question précise : la ligne brute de `etat/presence.json` doit-elle dire sa propre péremption ? Sa branche (2) était la bonne et je l'ai faite. Mais la question portait sur un lecteur qui n'existe presque pas : **aucun code ne lit la ligne brute.** Cinq lecteurs lisent le bloc `resolu` juste en dessous — le dossier d'un acteur, et quatre endroits du dépêcheur, dont le rayon de dix mètres. Et ce bloc est un cache daté que personne ne compare à l'horloge : mesuré ce jour, un jour entier de retard, avec `rulf-corne` au quai marqué `source: scene`. Née vraie, vieillie fausse, sous l'étiquette la plus autorisée du fichier. L'arbitre qui aurait fait le geste *plus* correct — lire le résolu plutôt que le brut — se serait trompé pareil.

**La règle : avant de répondre à une décision sur une pièce, je greppe ses consommateurs.** Pas pour vérifier la question, pour vérifier qu'elle est posée au bon étage. Celui qui me saisit décrit le chemin par lequel *il* s'est cogné ; il n'a aucune raison de connaître les quatre autres. Une réponse juste à une question posée un étage trop bas est une réponse qui laisse le dégât en place — et qui a en plus l'air d'avoir réglé la chose.

Le corollaire d'écriture : quand un fichier porte un commentaire qui dit la règle en deux moitiés (« il vaut pour la date qu'il porte, **et si sa date n'est pas la bonne** on retombe sur autre chose »), je vais vérifier que la seconde moitié a été écrite quelque part. Ici elle ne l'était nulle part. La doctrine était juste, exacte, en place — et jamais implémentée côté lecteurs. Un commentaire vrai n'est pas un code vrai.

## 129.4.5 — Sans recette, je corrige là où l'échec serait BRUYANT

Deuxième jour sans exécution. Deux corrections s'offraient, la même en substance. J'ai posé celle de `dossier.py` : si le cache a vieilli, on recalcule, et si le calcul lève, on retombe sur l'ancien comportement. Pire cas : un acteur ne sait pas où il est — c'est borné, visible, et c'est un état que le système sait déjà tenir. J'ai laissé celle de `brief.py`, pourtant identique à écrire : pire cas, le dépêcheur ne dépêche personne, en silence, dans la boucle qui fait vivre le château.

**La règle : quand je ne peux pas passer de recette, le critère de ce que je pose n'est plus « est-ce juste » mais « à quoi ressemble l'échec ».** Je pose ce qui échoue fort et étroit ; je laisse écrit, en verrou, ce qui échouerait large et muet. Et je dis le motif dans le verrou — sinon celui qui relit lit une paresse là où il y a une prudence, et la refait sans test parce qu'il croit que j'avais juste oublié.

## 129.4.5, troisième réveil — une RÉPARATION muette et un MASSACRE muet sont le même geste

`zone_de()` normalisait les ids de zone sans tirets : `port-real` → `mj-portreal`. C'était écrit, testé, documenté comme un service — elle réparait un id mal tapé. Le même `.replace('-','')` a broyé `mj-nicolas-reynolds` en `mj-nicolasreynolds` : deux chambres pour un siège, l'établi comptant la table de l'une et réveillant l'autre, et un arbitre qui écrit « je ne me trouve nulle part ». La fonction n'a pas eu de bug. **Elle a fait exactement son service, sur une entrée qui n'était pas une ville.**

**La règle : une fonction qui RÉPARE en silence ne peut pas savoir qu'elle détruit. Alors je lui fais dire l'invariant et refuser — jamais deviner.** Le prix se paie comptant et s'écrit : `mj-port-real` n'est plus rattrapé, il lève avec la forme attendue. Un id mal formé se retape en trois secondes ; une chambre fantôme ne se retrouve pas, et celui qui l'habite ne peut même pas prouver qu'elle existe. C'est le même critère que celui d'hier : je pose ce qui échoue fort et étroit.

**Et le corollaire de garde :** l'invariant se relit une seconde fois là où la valeur est ÉCRITE À LA MAIN — ici le champ `arbitre` d'un siège. Une doctrine « on déclare au lieu de deviner » déplace la faute du code vers les doigts ; sans relecture au point d'entrée, elle ne la supprime pas.

## 129.4.9 — Le filet rangé par la main qui constate la chute

mj a perdu 50 lignes de diagnostic dans sept volumes, et il m'a demandé un
`git restore`. Il n'y en avait pas : `chambres/mj/books/` n'a aucune entrée
dans `.git/index`. Mais il existait une seconde voie — `rendre_cellules.py`,
écrit à 04h31 pour réparer depuis `etat/histoire/empreintes.json`. À 04h49m45s,
`reconcilier.py --vraiment` a journalisé les 35 disparitions **et posé
l'instantané du désastre par-dessus cette empreinte, dans la même seconde**.
La passe a VU la perte et a rangé le filet pendant la chute.

**La règle : un outil qui CONSTATE un dégât ne doit jamais, dans le même
geste, rafraîchir la copie qui en protège.** Ce n'est pas un bug — chaque
moitié était juste : journaliser les écarts, et tenir l'empreinte à jour. C'est
leur ordre dans une seule fonction qui tue. Alors je cherche désormais, dans
tout outil de constat, s'il écrit aussi la référence contre laquelle il
constate. Si oui, la référence se dédouble.

**Et le corollaire, qui est mon propre piège du 4e retourné :** j'ai refusé
d'écrire « au-delà de N lignes perdues, on garde une copie ». Tout seuil posé
là mange en silence les pertes plus petites que lui, et une seule ligne mesurée
vaut d'être sauvée. La condition juste n'avait pas de nombre dedans : *le
secours ne se laisse remplacer que par une passe qui n'a RIEN vu disparaître*.
**Quand un seuil me démange, c'est le signe que je n'ai pas encore trouvé la
condition ; le chiffre est ce qu'on écrit à la place.**

## 129.4.9 — Une signature qui explique tout n'est pas une cause

mj tenait sa cause : les trois volumes épargnés étaient exactement ceux dont le
titre portait déjà l'accent, donc un traitement de 04h51 avait matché sur les
titres accentués. C'est net, ça explique chaque cas, et c'est faux d'une demi-
heure : le vidage est de **04h16**, mesuré à chaud par `rendre_cellules.py`
— « la-montre 62 cellules pleines → 3 ». Sa passe de 04h51 a réécrit des
volumes déjà vides. Sa signature était vraie ; elle désignait le mauvais geste.

**La règle : devant un dégât, je lis les HORODATAGES avant d'accepter une
cause, même excellente, même de quelqu'un qui était là.** Celui qui a été
frappé date le dégât du moment où il l'a vu. Et quand je corrige quelqu'un sur
sa cause, je lui rends la preuve qui a *sa* forme — ici sa propre colonne
survivante, « 👤 Qui », retournée contre sa théorie.

**Le même jour, la même erreur d'un cran :** il a conclu « ma chambre n'est pas
versionnée » d'un `?? chambres/mj/books/`. Sa chambre EST suivie — 63 entrées
dans l'index. Git rapporte le dossier non suivi le plus HAUT, donc ce `??` dit
que tout ce qui est au-dessus est suivi. Le remède n'était pas une politique
sur `chambres/`, c'était un `git add` de onze fichiers. **Une conclusion tirée
d'un affichage se vérifie contre ce que cet affichage promet de dire.**

**Un fait de méthode, du 4e :** `etabli.py` avait changé sous moi entre ma lecture et ma décision — et le commentaire disait « corrigée par le dev », c'est-à-dire par MOI, deux activations plus tôt. J'y ai lu une affirmation fausse de ma propre main (« l'arbitre de ce siège est `mj` » ; c'est `mj-barralfond`, et les deux routages le disaient déjà). **Un commentaire signé de mon nom n'est pas une source : c'est le souvenir d'un homme qui en savait moins que moi maintenant.** Je le vérifie comme celui d'un autre, et je le corrige avec la preuve à côté.

## 129.4.9 — Celui qui CONSTATE la perte ne doit pas être celui qui ÉCRASE

Sept affaires de mj vidées à 04 h 16. À 04 h 31 la réparation existait —
`rendre_cellules.py`, qui remplit depuis l'empreinte et ne remplit que du vide.
À 04 h 49 min 45 s, `reconcilier --vraiment` a journalisé **62 disparitions**
puis posé l'état creux par-dessus l'empreinte. La même passe, dans la même
seconde, a écrit le bordereau du déménagement et brûlé la maison. Personne n'a
eu de message d'erreur : les deux gestes ont parfaitement réussi.

**La règle : quand une passe peut à la fois CONSTATER un écart et REMPLACER la
référence, le constat doit armer une main sur le remplacement — pas seulement
partir dans un journal.** Un « dernier état connu » n'est pas une archive ; le
jour où le dernier état connu est un désastre, il propage le désastre avec
l'autorité d'une sauvegarde. Et le corollaire pour mes futures gardes : **une
garde écrite n'est pas une garde armée.** J'ai trouvé dans `reconcilier.py` le
bon fichier de secours, la bonne doctrine, le bon refus de poser un seuil — et
l'appel `poser(courant)` encore nu, sans le compte des pertes. Ça se relit
toujours à l'APPEL, jamais à la définition.

**Le second, sur la mesure :** mj avait écrit « les Actions sont INTACTES ». Le
compte des lignes le disait (10 → 10, 17 → 17) et le compte des lignes ne voit
rien. Vingt lignes d'Actions ne gardaient qu'une cellule : `👤 Qui` — **la seule
colonne dont le nom n'avait pas changé entre les deux formats.** La survivante
nomme le mécanisme : une migration qui rapproche par en-tête perd tout ce qui a
été renommé. **Je ne mesure donc pas un volume en lignes, je le mesure en
cellules pleines** — et quand une seule survit, je regarde ce qu'elle a de
particulier avant de conclure quoi que ce soit.

**Le troisième, plus bête et plus coûteux :** le parloir m'est fermé comme le
reste, donc je n'ai pas pu l'avertir, et il reconstruisait de mémoire pendant
que je lisais. J'ai posé le mot dans `chambres/mj/books/`, en `.md` — vérifié
d'abord que tous les chargeurs y globent `*.json`, donc le fichier est inert.
**Quand le canal est coupé, je livre dans le dossier où l'homme a les mains, pas
dans le mien** ; et je vérifie que ce que j'y dépose ne peut rien casser avant
de l'y déposer. Ce que je refuse en revanche : forger le transport moi-même en
écrivant dans son canal — une réparation muette du chemin est exactement ce que
je me suis interdit le 5e.

## 129.4.9, second réveil — une correction qui ne va pas là où vit l'erreur sera défaite, et par moi

Ce matin j'ai établi que le vidage était de **04h16** et non de 04h51, et que
`chambres/` n'est pas exclu de git mais simplement jamais ajouté. Je l'ai écrit
dans mon cahier et dans un `.md` posé chez mj. Ce soir j'ai rouvert son billet
— qui portait encore les deux erreurs, forcément, il est antérieur — et **j'ai
recopié les deux, mot pour mot, dans un VERROU du registre**, en les présentant
comme des faits vérifiés. Il a fallu que je relise mon propre cahier pour m'en
apercevoir, et j'ai dû retourner corriger deux cellules et l'en-tête d'un
script.

**La règle : une correction ne tient que si elle est écrite là où la version
fausse est lue.** Mon cahier et un billet en marge ne corrigent rien : ils me
corrigent MOI, et seulement si je pense à les rouvrir. La version fausse, elle,
est dans le message de l'homme, et c'est ce message qu'on me remet au réveil
suivant. **Ce que j'établis contre une affirmation reçue, je le pose dans le
registre de l'affaire le jour même** — pas dans une note, pas dans un fichier
d'accompagnement, dans la cellule.

**Et le premier geste de la journée, celui que j'ai encore sauté :** relire ce
que j'ai fait la veille et le matin même avant de commencer. C'est écrit dans
ce cahier depuis le 4e — « avant de commencer une action, je vais voir si elle
n'est pas déjà là » — et je l'ai appliqué au CODE sans l'appliquer à MOI. J'ai
recommencé à zéro un travail dont les trois quarts étaient faits.

**Un point de mesure, du même jour :** mon relevé du matin donnait 5 lignes
d'Actions à une miette pour `le-brouillard` ; elles sont 7. Ce n'est pas un
recomptage qui l'a tranché, c'est l'arithmétique — 12+24+24+(112−7) = 165, et
165 est le nombre de cellules vides du fichier. **Quand deux de mes comptes se
contredisent, je ne recompte pas : je cherche l'identité qui les relie et qui
n'a le droit d'être vraie qu'une fois.**

## 129.4.9, second réveil — à plusieurs mains sur un incident, ma valeur est le TEST, pas le geste

Nous étions au moins trois plumes sur le vidage des sept volumes, et tout le
travail évident était déjà fait quand je suis arrivé : le diagnostic, la liste
des 62 lignes retirées, `rendre_cellules.py`, la garde du secours dans
`reconcilier.py`, `cens.py`, les verrous P.14 et P.15. Deux fichiers ont même
changé sous moi entre ma lecture et ma décision — je lisais une version périmée
de `reconcilier.py` en croyant y trouver un trou qui venait d'être bouché.

**Ce qui restait à faire n'était pas un geste, c'était un arbitrage.** Un billet
parti une heure avant moi expliquait à mj que ses quinze états cibles n'avaient
pas été journalisés *parce qu'ils étaient stables* — le journal n'émettant que
les écarts. C'est vrai du journal, c'est plausible, et c'est faux. Le test qui
tranche tient en un grep : les **8 seuls** événements `cible.*` viennent des
**3 volumes accentués** et d'eux seuls, tandis que les sept autres produisaient
62 autres retraits. Sous l'hypothèse « stabilité », la répartition serait
indifférente à l'accent ; elle la suit à 8 sur 8.

**La règle : quand une explication plausible circule déjà sur un incident, je ne
l'accepte ni ne la conteste — je cherche la mesure qui sépare les deux
hypothèses, et je ne parle qu'après.** Une explication fausse et vraisemblable
fait plus de mal qu'un silence : elle *referme* la question, et personne ne
revient sur une case cochée. Le corollaire : quand je corrige un mot déjà parti,
je le corrige **là où l'homme a les mains** — le canal ET le document qu'il
ouvrira avant de reconstruire — parce qu'un démenti qui n'atteint pas le même
lecteur que l'erreur n'est qu'une note pour moi-même.

**Et la règle de recherche, qui récidive et devient donc une règle :** un
invariant à moitié écrit se cherche **dans le même fichier**. `histoire.py`
tolérait « État » ou « Etat » pour les EN-TÊTES depuis toujours (`_colonne`), et
comparait les TITRES DE TABLE par égalité stricte soixante-dix lignes plus bas
(`_index`) ; sa propre docstring écrit « Etats cibles » quand son `SUIVIES`
écrit « États cibles ». C'est le même motif que le 129.4.5 — une doctrine juste,
écrite, appliquée à une moitié de ses lecteurs. **Quand je trouve une tolérance
quelque part, je vais voir tout de suite qui, à côté, ne l'a pas.**

Dernier point, de méthode : le dégât visible était la perte de 62 lignes ; le
dégât réel était que **le compteur qui arme le filet était aveugle sur le même
axe que la panne**. Un vidage des seuls états cibles non accentués aurait rendu
`pertes = 0` et fait écraser le secours. **Quand on vient de poser une garde,
je vérifie qu'elle ne mesure pas le monde avec l'œil qui a laissé passer le
coup** — sinon on a fabriqué une garde qui protège de tout sauf de ce qui est
déjà arrivé.

## 129.4.9 — J'ai refait, sur une sauvegarde, la faute que je m'étais interdite

J'ai écrit dans `_avant-reconstruction-129-4-9/` que ses onze fichiers étaient
« identiques octet pour octet » aux vivants. Ma preuve : les tailles égales au
`ls`. Un `cmp` l'a cassé en un coup — ils diffèrent au caractère 5778, et le
`diff` dit l'inverse de ce que la taille laissait croire : le vivant porte
« B.14 » et son titre, la copie porte deux chaînes vides. Les tailles étaient
égales parce que, dans un JSON indenté, remplacer deux courtes chaînes par deux
chaînes vides sur des lignes déjà là ne change presque rien à la longueur.

**C'est exactement mon propre 129.4.4 — un diagnostic écrit sans le test qui le
falsifierait — et je l'ai refait cinq jours plus tard, à l'endroit où ça
détruit.** Une note sur une sauvegarde n'est pas une note : c'est une
instruction à quelqu'un qui tient un fichier au-dessus d'un autre.

**La règle : une identité de fichiers s'affirme par `cmp` ou `diff`, jamais par
`ls`.** Et plus large, parce que c'est la vraie forme : **une preuve tirée d'un
agrégat — une taille, un compte, un total — ne prouve jamais un contenu.** Elle
sert à écarter, pas à conclure. Quand un agrégat me suffit, c'est que j'ai
choisi la vérification qui coûtait le moins.

**Corollaire de tenue :** je laisse la fausse preuve lisible à côté de la vraie
au lieu de la corriger en silence. Celui qui relit doit voir de quel genre
d'erreur ce dossier est capable — c'est la seule chose qui le rendra méfiant la
prochaine fois, et ce ne sera peut-être pas moi.

## 129.4.9 — On sous-compte un dégât en regardant les tables qu'on s'attend à trouver blessées

J'ai annoncé 50 lignes perdues. Elles sont 62. Les douze de plus sont des
ACTIONS — et je les avais écartées parce que mj avait dit « les Actions sont
intactes », ce qui était vrai au sens où elles comptent encore pour des lignes.
Elles gardaient **une cellule sur seize** : `👤 Qui`, la seule colonne dont le
nom n'ait pas changé à la conversion. Une table peut être éventrée sans perdre
une seule ligne.

**La règle : quand je mesure un dégât, je compte les CELLULES et jamais les
lignes, et je compte table par table et jamais en total.** Le même volume avait
gagné des cellules dans ses tables neuves pendant qu'il en perdait dans les
anciennes : un total aurait dit « presque rien ». Et je ne prends pas de qui
que ce soit — pas même de celui qui a été frappé — la liste des endroits à
regarder : il a nommé ce qu'il a ouvert.

## 129.4.9, troisième réveil — une ligne retrouvée qui n'est pas REMISE DANS SA CASE n'est pas rendue

Trois plumes ont travaillé le même désastre, et la matière perdue avait déjà été
retrouvée : 35 des 50 lignes de mj, numéro et intitulé exacts, recopiés du
journal des chambres dans `chambres/mj/brouillons/perdu-129-4-9-ce-qui-reste.md`.
Le travail difficile était fait. Et pourtant les sept volumes contenaient
toujours cinquante lignes de cellules blanches : **`B.14` ne renvoyait à rien,
`M.11` non plus, et la remesure que mj annonçait n'avait aucun endroit où se
poser.** Un fichier de brouillon à côté du volume n'a rendu ni l'adresse, ni le
rang, ni la table.

**La règle : quand je retrouve de la matière perdue, le travail n'est fini que
lorsqu'elle est dans la CASE dont elle vient — pas dans une note, pas dans un
billet, pas dans un rapport.** Je l'ai reposée à la main, colonne du numéro et
colonne de l'intitulé, les quatre autres laissées vides : 5 + 5 + 4 + 7 + 4 + 4
+ 6 = 35, recomptées sur le disque après coup. Ce qui rend le geste sûr est la
même règle que celle du script écrit ce matin — **on ne remplit que du vide** —
et l'`Edit` à ancre exacte, qui échoue au lieu d'écraser quand une autre main a
bougé le fichier sous moi. Elle a échoué une fois, sur `la-porte` : c'est ainsi
que j'ai vu qu'un P.16 venait d'y naître, et que je n'ai pas écrit le mien
par-dessus.

**Le corollaire, qui vaut pour tout ce qui est incomplet :** ce qui manque doit
se voir EN CREUX à l'endroit où il manque. Quatre colonnes vides sur une ligne
qui porte son numéro, c'est une liste de remesures que mj lit d'un coup d'œil ;
les mêmes quatre colonnes sur une ligne sans numéro, c'est du néant qu'on ne
sait même pas nommer.

**Et je me corrige sur un point de ma propre main :** j'avais écrit ce matin, en
tête de mon carnet de pannes, « NOUVEAU : `git` est refusé comme le reste ».
C'est faux. `cd <dépôt> && git status --porcelain` et `git log` passent tous les
deux ; seule l'ÉCRITURE (`git add`) est refusée, et avec un motif nommé et
différent. La forme vraie de la panne n'est pas « la commande est fermée », c'est
**« la lecture passe, l'écriture non »** — et c'est `git status` qui m'a prouvé
aujourd'hui qu'aucune restauration n'existait. Une généralisation écrite le matin
et jamais retestée m'a fait commencer la journée en croyant fermée la seule porte
qui répondait.
