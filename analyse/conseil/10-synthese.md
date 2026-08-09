# Analyse globale — les 100 derniers messages du conseil

Corpus : `etat/flux.jsonl` lignes 6415→6780, du 26e jour 3e lune 21h04 au 28e jour 7h02. 100 répliques, 11 locuteurs, 67 672 caractères. Détail message par message dans `corpus.md` et `01-le-sanglier.md`.

---

## 1. Le diagnostic en une phrase

**Le conseil a cessé de préparer une guerre pour administrer le registre de sa préparation** — et il le fait à deux voix sur onze, dans le vocabulaire des fichiers du jeu.

---

## 2. Les six pathologies, par gravité

### A. Le conseil parle de son propre système (≈45 messages sur 100)

C'est la faute mère, celle dont les autres découlent. Une bonne moitié des interventions n'ont pas pour objet la guerre mais **l'outillage de suivi de la guerre** : quelle colonne ajouter au registre, quel document fait doublon, comment renuméroter une affaire coupée en trois, ce qu'un cahier « promet » et ne promet pas.

Le point extrême est la séquence **069 → 072** : le Sanglier fabrique un tableau des cinq commandements pendant trois battements, et au quatrième il dit *« Vous avez raison et je l'ai écrit pour rien. »* Quatre items, deux minutes de fiction, zéro conséquence. Même chose en **092** (une explication de renumérotation), **077** (une note de méthode sur la tenue des cahiers), **094-096** (le mode d'emploi d'un cahier).

Pendant ces 34 heures, l'ost n'a pas bougé, aucun corbeau n'a été intercepté, personne n'est mort, aucun ennemi n'a agi. Le seul item qui apporte une nouvelle du monde extérieur est le **057** de Denys Bar Emmon (*« Ser Criston a neuf cents hommes et pas une échelle »*) — **un sur cent**.

### B. Deux voix pour onze personnages

| le-sanglier | 41 | ██████████████████████████████████████████ |
| gerardys | 32 | ████████████████████████████████ |
| les 9 autres | 27 | ███████████████████████████ |

Le Sanglier et Gerardys disent **73 % de tout ce que le conseil dit**. Sara, Denys, Marna ont **un message chacun** en 34 heures ; Alys en a deux. Le manuel décrit une boucle d'élection (*« on cherche qui a la plus forte raison d'agir à cet instant »*) : ici c'est un duo qui parle et neuf figurants qui attendent.

Pire : **ces deux-là parlent la même langue.** Tous deux tiennent des registres, tous deux comptent des colonnes, tous deux ferment sur une sentence. Rien dans le texte ne permettrait de les distinguer si on retirait les noms. Le seul écart réel est que Gerardys est plus long (787 car. contre 600).

### C. Le vocabulaire de fichier dans la bouche des gens

`CLAUDE.md` l'interdit nommément : *« jamais volume, ligne, case, marque, porteur, état cible, verrou, plage, ni aucun numéro d'adresse »*. Moyenne relevée : **1,3 mot interdit par message**, et les pires ne sont pas des mots mais des adresses :

- *« c'est écrit noir sur blanc au **verrou 36002** »* (086)
- *« **Une plage neuve, la quarante-trois mille**, pour l'ordre des dragonniers »* (008)
- *« **Quatorze, quinze, seize, dix-sept. Je les ouvre.** »* (032) — en ouverture de réplique
- *« ma **septième ligne**… elle a huit entrées » / « ma quatrième entrée » / « mon quatrième volume »* (001, 011)

Le joueur ne peut tenir aucun de ces référents. Corollaire mesurable : **77 messages sur 100 emploient au moins une fois le mot *volume*, *ligne*, *case*, *colonne* ou *registre***, dont beaucoup comme sujet principal de la phrase.

### D. La charge remonte au lieu de descendre

Le manuel : *« Rien ne remonte au joueur qu'il n'ait à trancher »*, *« une objection par battement dans toute la salle »*.

Le corpus fait l'inverse et le fait en gros. Le **017** pose **neuf décisions** en un item. Le **026 + 027** en reposent **sept**. Le **031** aligne **quatre trous sans une seule sortie**. Le **077** ferme sur *« ces deux noms n'appartiennent qu'à Sa Grâce »*. Le **086** sur *« ça revient toujours à Sa Grâce »*. Le **069** sur *« Ceux-là, c'est Sa Grâce. »*

Et le conseil en est conscient, ce qui est le symptôme le plus net : Gerardys dit lui-même au **022** *« sept sur neuf tombent chez vous »*, puis *« la vraie question, c'est combien vous en tenez par jour, et je ne peux pas y répondre à votre place »*. Le conseil a mesuré sa propre inutilité et l'a présentée comme un résultat.

Un seul personnage se rattrape en scène : le Sanglier au **033** — *« Vous avez raison. Je vous ai apporté quatre trous et rien avec. J'ai écrit la règle il y a un quart d'heure. Je suis le premier à ne pas la tenir. Je reprends. Un à la fois. »* C'est le meilleur message des cent, et il fait trois lignes.

### E. Trop long, trop chiffré, deux idées par bouche

- Moyenne : **676 caractères et 6,8 phrases** par réplique, contre les *3 à 6 phrases, une idée par phrase* de la règle.
- Moyenne : **10 chiffres par message**, contre les *deux au plus, et chacun doit décider quelque chose*. Le **013** en aligne sept d'affilée (508, 1 200, 2 154, 3 028, 38 290, 17, 12,5) ; le **006** en aligne douze. C'est un tableur lu à voix haute.
- Un message sur trois traite deux affaires ou plus. Le **008** de Jacaerys en porte six (Daemon, Vhagar, son mariage, un quart d'heure, le onzième jour, une plage neuve).

### F. L'horloge ne tourne plus

**40 messages sur 100 portent `duree: 0`.** Le conseil du 26e au soir tient **10 items dans la même minute** (21h04) ; celui du 27e à 19h32 en tient 7. Quarante répliques de fond ne coûtent rien à personne, alors que la section « La montre » dit exactement le contraire. Conséquences : la journée du joueur ne se remplit pas, les échéances ne pressent pas, et les tranches poussées au fil sont des murs de texte au lieu de 2-4 items respirés.

Trois horodatages **reculent** : 033 (8h25 après 8h39), 078 (18h45 après 18h48), 099 (6h59 après 7h05).

---

## 3. La cause racine : les fiches sont devenues le gabarit que le manuel interdit

`CLAUDE.md` prévient : *« Ce qui donne la forme à la place d'un gabarit : la `maniere` de la fiche… Un gabarit en quatre temps effacerait exactement ce qui les rend reconnaissables. »*

Or **onze fiches sur douze ont reçu le même bloc collé** dans `personnages.json` :

> *« Se débrouille seul : comble les trous sans demander, tranche le routinier à sa main… Compétent : sur son domaine il en sait plus que son maître et le montre — apporte le précédent, le chiffre et l'avis qu'il défend… **DEUXIÈME PHRASE, toujours** : ce que c'est, ce que ça change pour la reine, et à quoi ça sert dans ses trois piliers. »*

Le gabarit est **littéralement dans les fiches**, en majuscules, avec un numéro de phrase. C'est pour ça que les voix se ressemblent : on a écrit la même consigne à onze personnes.

**La preuve par l'exception :** **Alys Grive est la seule dont la fiche n'a pas reçu ce bloc** — et c'est la seule voix pleinement singulière du corpus. Son **059** (*« une demande suivie d'une réponse n'est pas une phrase, c'est un refrain — et un refrain part sans porteur »*) ne pourrait être dit par personne d'autre. Son **051** ouvre sur son prix moral (*« ma liste apprendra leur mort à des familles que personne n'a prévenues »*) au lieu d'un chiffre.

---

## 4. Ce qui marche, et qu'il ne faut pas casser

Il y a **une séquence excellente dans le corpus** : les messages **047 à 061**, le tour de table du 27e à 9h20 et 17h04. Onze conseillers, un message chacun, format tenu :

> **047** *« Il y a onze coques en état chez moi, et je descends dépouiller mon livre en sortant d'ici. »*
> **054** *« Vous pouvez parler à un homme dans Port-Réal sans qu'un corbeau vous trahisse. »*
> **056** *« Vous pouvez payer le ralliement des maisons sans emprunter à personne. »*
> **058** *« Vous aurez votre réponse sur la femme de Bec-de-Fer avant le souper. »*
> **060** *« Vos hommes arriveront affamés devant Port-Réal si on les embarque comme prévu. »*
> **061** *« Vous aurez peut-être un troisième dragon en état de porter quelqu'un. »*

Tout y est : le sujet de la première phrase est **la reine**, la chose est nommée par ce qu'elle fait, la dernière phrase est une date ou un geste, un seul objet, deux chiffres. Sur ces quinze messages, **zéro mot de fichier chez Rulf, Quince, Sara, Alys et Denys**.

Cette séquence prouve que le format tient quand on l'applique. Elle prouve aussi qu'il ne tient **qu'un tour** : dès 065, la rechute est complète (Gerardys, 65 : *« deux trous par où cet acte se vide »*), et à 069 on est retombé dans la table de commandements.

Autres réussites isolées à garder comme étalons : **033** (le Sanglier se corrige en trois lignes), **055** (Merra Sath), **076** (*« Pas chez moi, Votre Grâce »* — six mots), **078** (quarante hommes à cinq cents pas), **087** (les règles d'un mot de repli — du savoir de métier pur), **088** (Quince et les trois occultations lentes), **091** (l'exercice de nuit : *« le seul qui donne un chiffre qu'on n'a pas choisi »*), **100** (Hask renonce à Celtigar : *« ce que j'y gagne vaut mieux que l'or : il ne saura jamais que nous y avons pensé »*).

---

## 5. Les personnages, en capsules

| Qui | Ce qui marche | Ce qui dérape | Le geste à faire |
|---|---|---|---|
| **Le Sanglier** (41) | Court, il est le meilleur : 033, 055, 076, 078, 087, 089, 091. Son oreille (023) et son refus de croire le papier (091) sont uniques. | 41 % de la parole. Devenu porte-parole du système. Ouvre sur un manque 14 fois alors que sa fiche l'interdit. Une maxime finale sur trois messages. | Plafond 2 items d'affilée, 8 par conseil. Sa bouche ne dit que des hommes, des portes, des routes. Jamais un trou sans son bouchon dans la même phrase. |
| **Gerardys** (32) | Le meilleur relecteur du jeu : il corrige ses propres attributions (015), avoue ses fautes (045, 075), et protège Aurore contre elle-même (067). Le 065 (Sara ne lit pas, on n'écrira pas son pouvoir sans elle) est un sommet moral. | Le plus long (787 car.), le plus chiffré (12/msg). Il ne fait plus que **lire des ordres du jour** : 016, 017, 021, 022, 026, 027, 090 sont des sommaires de décisions à prendre. Sa fiche dit *« précautions et circonlocutions »* ; il est devenu sec et exhaustif. | Un mestre ne lit pas neuf décisions : il en apporte **une**, la plus urgente, avec le précédent qui la tranche. Le reste va dans un item `ecrit`. Lui rendre ses circonlocutions et sa chaîne qu'il tord. |
| **Steffon Darklyn** (7) | Le 060 (les hommes affamés) et le 073 (Kerra, son prix dû maintenant) sont exemplaires. Il borne son propre pouvoir sans qu'on le demande (019). | 785 car./msg pour un homme dont la fiche dit *« phrases courtes et factuelles »*. Le 002 et le 005 sont des plaidoiries. Il menace la reine par écrit (*« alors vous écrivez de votre main que vous entrez gardée par personne »*) — c'est du chantage administratif, pas de la Garde Royale. | Le ramener à 3 phrases. Un soldat ne rédige pas de conclusions : il dit ce qu'il fait, à partir de quand, et se tait. |
| **Aldon Hask** (5) | **La progression la plus nette du corpus.** 013 = un tableur (7 chiffres). 048 = mieux. 056 = *« Vous pouvez payer le ralliement sans emprunter à personne »*, avec l'aveu de s'être trompé du triple. 099-100 = parfait : il achète, il renonce, il ne demande rien. | Le 013 (*« dix-sept lunes si nous n'entrons jamais »*) reste un état de caisse récité, ce que sa fiche interdit explicitement. | Rien à réparer : **il est le modèle**. Sa fiche (*« ouvre par ce qu'il achète, jamais par l'état de la caisse »*) est la seule qui produise déjà le bon résultat — la recopier dans l'esprit des autres. |
| **Robert Quince** (4) | **La voix la plus propre : 0,2 mot de fichier par message.** Le 088 (trois occultations lentes, *« pas un signal qui s'allume : un signal qui s'éteint »*) est le plus beau savoir-métier des cent. Le 082 (le quatrième soir, l'homme fatigué écrit *deux servantes*) est un précédent parfait. | Quatre messages en 34 heures pour le castellan d'un château en guerre. Il ouvre deux fois sur son déficit (*« cent dix-neuf debout, un sous mon plancher »*) alors que sa fiche dit expressément que le chiffre qui manque vient en 2e ou 3e phrase. | **Lui donner trois fois plus de parole.** C'est le personnage qui coûte le moins cher au joueur et qui lui apprend le plus. |
| **Jacaerys** (3) | Le 061 (la main sur le cou d'Argent, *« un dragon de plus au-dessus de cette ville, c'est une ville qui hésite »*) est exactement ce qu'on attend de lui. | **Le pire ratio du corpus : 1 035 car. et 19,3 chiffres par message.** Le 006 est une table de conversion monétaire ; le 008 porte six sujets et réclame *« une plage neuve, la quarante-trois mille »*. Un garçon de quinze ans qui parle en adresses de fichier. | Lui retirer les chiffres. Il est le seul à pouvoir parler de bêtes, de peur et d'orgueil de prince — c'est sa matière, pas la comptabilité. |
| **Rulf Corne** (3) | Trois messages, trois réussites. Le 053 (*« les nuits où la mer nous laisse traverser, personne ne monte à Port-Réal par l'eau »*) est un cadeau au joueur. 418 car./msg — le plus concis. | Trop peu présent. | Le laisser tel quel et le faire parler plus. |
| **Alys Grive** (2) | **La seule voix vraiment singulière.** Sa fiche est la seule sans le bloc collé, et ça s'entend. Le 059 (le refrain qui part sans porteur) et le 051 (son prix moral d'abord) ne pourraient être dits par personne d'autre. | Deux messages sur cent pour la seule personne qui agisse sur l'opinion de la ville. | **Ne jamais lui coller le gabarit.** L'augmenter à 4-5 interventions par jour. |
| **Denys Bar Emmon** (1) | Son unique message est le **seul du corpus qui apporte une nouvelle de l'ennemi** : *« Ser Criston a neuf cents hommes et pas une échelle. »* Trois groupes de villageois qui ne se sont jamais parlé — la source est dite. | Un message sur cent, alors que sa fiche en fait l'œil de la maison sur le dehors. | **C'est le manque le plus grave du casting.** Il devrait ouvrir chaque conseil : ce que fait l'ennemi. |
| **Sara Poulain** (1) | Son unique message est un modèle (*« Je cherchais quelqu'un qui écrive ; il me fallait quelqu'un qui lise »*, puis *« vous aurez oui ou non, pas un peut-être »*). Zéro mot de fichier. | Une Main de la reine qui parle une fois en 34 heures. Sa fiche prévoit qu'elle ouvre chaque jour sur *« ce qui a été fait pendant la nuit — les fours, les couchages, la paie »* : ce battement quotidien n'existe pas dans le corpus. | Installer son item du matin. C'est lui qui doit porter « ce qui s'est fait sans vous ». |
| **Marna** (1) | La relecture des rôles à sept heures (097) est le bon rituel, et le tremblement au premier mot est juste. | 3 mots de fichier par message — le pire ratio du corpus, pour une femme qui lit à voix haute. | Elle lit un registre : c'est le seul endroit où la langue du registre est légitime. Mais alors qu'elle lise **des noms et des nombres d'hommes**, pas des intitulés de colonnes. |

---

## 6. Ce qu'il faut changer, par ordre de rendement

1. **Dégonfler les fiches.** Retirer de `personnages.json` le bloc *« Se débrouille seul… Compétent… DEUXIÈME PHRASE, toujours »* collé à l'identique sur onze personnages. Il produit exactement l'uniformité qu'il prétend éviter. Ne garder que la ligne `OUVRE PAR`, qui est la seule spécifique, et rendre à chacun ses deux ou trois manies concrètes (Gerardys tord sa chaîne, Quince souffle dans l'escalier, Hask donne la somme avant le commentaire).

2. **Un plafond de parole par battement.** Personne ne dit plus de deux items d'affilée ; personne ne dépasse 6-8 messages par conseil. Corollaire : si le Sanglier et Gerardys ont dit les quatre derniers items, le cinquième appartient à quelqu'un d'autre — c'est la boucle d'élection, appliquée.

3. **Bannir la langue des fichiers, sans exception.** *volume · ligne · case · colonne · plage · verrou · marque · porteur*, et tout numéro d'adresse. Le test à faire avant de pousser : est-ce que cette phrase existerait si le jeu n'avait pas de fichiers JSON ? Si non, elle sort.

4. **Sortir la méta-administration de la scène.** Ce qui a été écrit se dit en item `ecrit`, avec le lien vers le livre — c'est fait pour ça. Une renumérotation, un doublon de tableau, un mode d'emploi de cahier ne sont jamais une réplique.

5. **Une décision par battement, jamais neuf.** Interdire les items-sommaires (016, 017, 021, 022, 026, 027). Si sept choses attendent la reine, le mestre en apporte **une**, celle qui tombe aujourd'hui, avec le précédent qui la tranche — et il note les six autres au registre.

6. **Rallumer l'horloge.** `duree: 0` réservé à `pensee`, `question`, `reponse`, `coulisses`. Un conseil de quarante répliques coûte une heure ; qu'il la coûte. Et corriger le tri : trois items du corpus reculent dans le temps.

7. **Rendre le monde à la scène.** Sur cent messages, **un** parle de l'ennemi. Faire ouvrir chaque conseil par Denys (ce que fait l'autre camp) et Sara (ce qui s'est fait dans la nuit) avant que quiconque ouvre un registre.

8. **Prendre 047-061 comme étalon.** Coller cette séquence en tête du manuel comme le modèle du tour de table : un homme, un message, la reine en sujet de la première phrase, une date en dernière.
