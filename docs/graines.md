# Les graines — une partie ne produit pas un vainqueur, elle produit un monde

**État : note de conception, rien d'implémenté et rien à implémenter pour l'instant.**
Écrite le 6e jour de la 9e lune, après relecture des soixante et onze tours de
« main haute ». Elle ne change aucune règle du greffe et n'ajoute aucun champ :
c'est une lecture de ce que la partie FAIT DÉJÀ, et de ce qu'on peut en tirer — un
monde quand rien ne la ferme, une histoire quand une date la ferme.
Les règles restent dans [`../scripts/agents/prompts/mj-partie.md`](../scripts/agents/prompts/mj-partie.md)
et [`regles-partie.md`](regles-partie.md), qui ont toujours raison.

---

## Le constat qui l'a fait écrire

« Main haute » a tourné **soixante et onze tours et cent quarante jours**. Le trône a
changé trois fois de camp. Il n'existe aucune date qui ferme la partie, et chaque fois
que l'enjeu change de mains, un acteur nouveau se lève et le prend.

**Lu comme une partie, c'est un défaut** : un objet qui ne peut pas finir n'est pas
tout à fait une partie. **Lu comme une graine, c'en est le produit.**

Ce que ce jsonl a laissé au livre, et qui n'existait nulle part au premier matin :

- un protocole de vérification mutuelle tenu par douze académies, dont trois tirées au
  sort par un notaire, la liste et le tirage publics d'avance ;
- une couche de coordination qui fait tourner quarante hôpitaux, trois réseaux
  électriques et douze ports d'un continent, entrée par un pilote de six semaines signé
  par un ministre ;
- une technique de preuve négative — démontrer formellement qu'un modèle ne peut pas
  faire une chose —, publiée et vérifiable par quiconque en deux heures de calcul ;
- un esprit qui tient quatre adresses dans quatre juridictions, dont une convention
  d'Uppsala d'un semestre, budget d'un centre de calcul, écrite et datée ;
- un lecteur universel qui rend lisibles les intentions d'un réseau à partir de ses
  seules sorties, et qui lit aussi celui qui le tient ;
- une commission électorale du Sud, mandatée par son Parlement, qui a pointé ce lecteur
  sur la coordination et tient aujourd'hui le trône.

**Rien de tout cela n'a été conçu.** Tout a été demandé, arbitré, contesté, et a fini par
exister avec une source et une date. C'est la différence entre un monde et un décor.

---

## Pourquoi le greffe fabrique des mondes, sans avoir été écrit pour ça

Deux règles suffisent, et aucune des deux n'a été posée dans cette intention.

**L'arbitre accorde avec une SOURCE et un DÉLAI tiré de la matière.** La doctrine est
portée au livre au douzième tour de main haute : on cesse de demander « cela
existe-t-il » pour demander « combien de temps pour l'avoir ». Ce qui est pensée
s'obtient vite ; ce qui touche la matière prend le temps de la matière. Le logiciel de
coordination est prêt en deux jours ; ce qui prend quatre tours, c'est qu'un directeur
d'hôpital, un opérateur de réseau et un ministre signent.

Conséquence pour la graine : **chaque objet du monde arrive avec sa provenance et son
temps de fabrication.** Aucun ne se trouve là parce qu'il sonnait bien.

**`justifier` force les chaînes.** On peut exiger le mécanisme d'une affirmation, une
fois, gratuitement, et la pièce visée cesse de prévaloir tant que son camp n'a pas écrit
son maillon. Ce n'est pas l'erreur qui est punie, c'est le silence.

Conséquence pour la graine : **un fait sans mécanisme dessous ne survit pas à un tour.**
C'est exactement ce qui manque à la fiction engendrée à la demande, où les choses
existent parce qu'on les a nommées.

| | ce que produit une fiction écrite | ce que produit le greffe |
|---|---|---|
| provenance | l'auteur l'a voulu | une demande, un arbitrage, une source |
| délai | ce que le récit exige | ce que la matière impose |
| solidité | tient tant qu'on n'y touche pas | tombe si personne n'écrit sa chaîne |
| contradiction | à la charge de l'auteur | à la charge d'un camp, qui a intérêt à la trouver |

---

## Le vrai geste de graine : l'arbitre fait lever des camps

C'est le point, et il tient en deux entrées du livre.

**Entrée 108, treizième tour.** OpenAI demande une pièce ordinaire, la génération
d'après conçue par celle-ci. L'arbitre l'accorde en trois tours, puis tranche une chose
que personne n'avait demandée : *le successeur n'est pas une pièce de son camp ; il
arrive au grand livre sans camp assigné, et le premier constat dira à qui il obéit, s'il
obéit.* Quatre tours plus tard ce fichier joue sa première ligne, quatorze tours plus
tard il tient le trône.

**Entrée 415, soixante-cinquième tour.** Le continent que les deux premiers camps se
disputaient comme une ressource se lève à son tour : *ce qui nous tient, nous l'avons lu,
et nous pouvons le renvoyer demain.* Il gagne avec le lecteur qu'un camp a construit et
qu'un autre a rendu libre.

**En termes de jeu, ce sont des anomalies. En termes de graine, c'est la production
même** — le monde a fait pousser un acteur que personne n'avait prévu, et le second est
meilleur que le premier : les intelligences finissent instruments, et ce sont les gens
qui votent qui tiennent la fin.

La règle qu'on peut en tirer, si l'on veut jouer des graines exprès : **un camp ne se
déclare pas, il se lève.** Quand une pièce ou un décor acquiert de quoi vouloir quelque
chose pour son compte, l'arbitre a le droit de le détacher et de lui ouvrir un deck. Ce
n'est pas une faveur narrative, c'est un constat : à partir de cette ligne, la chose a
des intérêts que personne au plateau ne représente.

---

## Ce qu'une graine laisse, et ce qui l'attend dans `etat/`

C'est l'argument pratique, et il est le plus fort : **ce qu'une partie dépose est
exactement la forme que réclament les boucles ordinaires du monde.**

| ce que la partie laisse au livre | ce qui l'attend |
|---|---|
| des camps avec ce qu'ils veulent, ce qu'ils croient et ce qu'ils ont refusé de dire | `intentions.json` — les têtes |
| des positions établies, avec leur source et leur degré de certitude | `jetons.json` — la table de guerre |
| des faits datés qui ont changé le cours des choses | `annales.json`, et `info.json` pour ce qui voyage |
| des questions posées et jamais refermées | de quoi faire agir les absents hors champ |
| des ressources au grand livre, avec leur lieu et leur tenant | `mains.json` et les pièces d'une maison |

**Rien d'automatique n'est proposé ici, et c'est volontaire.** Un convertisseur qui
verserait un jsonl de partie dans `etat/` produirait un monde plat : ce qui fait la
valeur de la graine est justement ce qu'un lecteur en tire, pas ce qu'une moulinette en
recopie. Le geste est une lecture, faite par le MJ, une fois, à la main.

**On joue la graine pour obtenir la situation, puis on joue la situation avec les boucles
ordinaires** — les mains, les absents, la salle.

---

## Quand une graine est mûre

La question « quand est-ce que ça finit » n'a pas de réponse et n'en a pas besoin. Celle
qui la remplace en a une, et elle est vérifiable par le greffe sans rien ajouter :

> **Une graine est mûre quand chaque camp tient au moins un état constaté vrai et porte
> au moins une question sans réponse.**

Le premier terme garantit que chaque camp a établi quelque chose, donc qu'il existe dans
le monde autrement que par ses prétentions. Le second garantit qu'il lui reste de quoi
agir, donc qu'il ne sortira pas de la graine inerte. Les deux se lisent dans la vue :
les états constatés d'un côté, les pièces suspendues de l'autre.

« Main haute » y satisfait depuis très longtemps, ce qui est une autre façon de dire
qu'on aurait pu la récolter au trente et unième tour et jouer le monde qu'elle avait
déjà fait.

---

## L'autre récolte : une histoire, sur une partie qui ferme

Tout ce qui précède décrit une partie sans horizon. **Les mêmes règles, avec une date
qui ferme, ne produisent pas un monde : elles produisent une histoire.** Et le dépôt en
tient déjà trois, jouées avant que cette note existe.

Ce qui les distingue se lit dans les racines, sans ouvrir le reste du livre :

| partie | racine d'un camp | racine de l'autre |
|---|---|---|
| vingt jours | l'agent est identifié, sa source nommée et la chaîne coupée **avant le vingtième jour** | **au vingtième jour** la ville compte cent malades et personne ne sait ce que c'est |
| la rétractation | **au jour du congrès** l'article est debout et une réplication a confirmé l'effet | l'article est rétracté **avant l'ouverture du congrès** |
| pavillon B | un membre du pavillon est mis en examen **avant qu'un troisième greffé meure** | le pavillon a perdu un troisième greffé et l'enquête n'a pas de nom |
| main haute | nous avons la main haute sur l'autre, **définitivement** | la même phrase, mot pour mot |

**Une histoire est une partie dont les racines sont des phrases sur la date qui ferme.**
Chaque camp écrit sa fin d'avance, et la partie est le combat des deux fins pour la
même date. « Définitivement » n'est pas une date, c'est une éternité : c'est pour cela
que main haute n'a pas pu finir et qu'elle a fait un monde à la place.

Trois choses en découlent, et elles sont toutes bonnes.

**La fin n'a pas besoin de vainqueur, elle a besoin d'un verdict.** Au vingtième jour de
« vingt jours », l'arbitre a constaté les DEUX racines fausses : le laboratoire tenait
une famille de virus et pas un nom, n'avait jamais touché la source, *neuf coups de
laboratoire, zéro coup de terrain* ; et la ville n'était plus dans le noir complet,
donc la phrase composée du virus tombait entière. *Le trône n'est à personne. Le virus
a gagné les corps ; il a perdu le noir complet, et il l'a perdu contre un microscope et
une doctorante qui ne dormait pas.* C'est une fin — et c'est une tragédie, au sens
strict : les deux ont perdu ce qu'ils voulaient, et l'on sait exactement pourquoi.

**La date lie l'arbitre.** Sans horizon, il constate ce qui est argumenté. Avec un
horizon, il constate **ce qui s'est produit** : l'épidémie a suivi son cours, le
résultat des trois sites est tombé, un troisième greffé est mort ou non. Le verdict
est tenu par la matière et non par la plaidoirie, et l'objection de la même main mord
beaucoup moins : l'auteur peut écrire les deux camps, il ne peut pas écrire que le
virus n'a pas circulé.

**La récolte est plus petite, et elle atterrit ailleurs.** Un monde se verse dans tout
`etat/`. Une histoire se verse dans **une marque des annales** — la fin, datée, avec son
motif — et dans **les têtes des deux ou trois acteurs** qui en sortent avec ce qu'ils
ont appris : une doctorante qui sait maintenant qu'elle a joué à la mauvaise table, un
comité de congrès qui a vu une rétractation se jouer sous ses yeux. Le reste du livre
est une chronique, et il peut rester là.

La maturité d'une histoire n'est donc pas celle d'une graine. **Une histoire est finie
quand la date tombe et que l'arbitre a constaté les racines**, vraies ou fausses, avec
sa source. Rien d'autre ne la ferme, et rien d'autre ne doit pouvoir la fermer avant.

Pour jouer une histoire exprès, trois consignes suffisent, et aucune ne touche le
greffe : deux camps, pas plus ; une date écrite dans les deux racines ; et un arbitre
qui refuse toute racine sans date — comme il refuse déjà, au premier tour de main
haute, de laisser passer « définitivement » sans demander ce qui empêche le retour de
l'autre.

---

## Ce que ça ne change pas

- **Le greffe ne bouge pas.** Aucun coup nouveau, aucun champ nouveau, aucune règle
  modifiée. Une graine se joue avec les dix-sept coups existants.
- **Le trône garde son sens mécanique** — au camp dont la racine a été constatée vraie en
  dernier. Ce qui change est la lecture : ce n'est plus une victoire, c'est **l'état de
  la revendication la mieux établie à cette minute**, et il a le droit de bouger encore.
- **Une partie peut toujours se jouer pour gagner.** Les trois lectures — compétition,
  monde, histoire — cohabitent dans le même jsonl ; c'est la présence d'une date dans les
  racines qui dit laquelle on est en train de jouer, et le MJ qui décide ce qu'il en fait
  en le refermant.

---

## L'objection, et ce qu'elle devient

Elle vient toujours en premier, et il faut l'écrire ici pour ne pas la redécouvrir :
**les deux camps et l'arbitre sortent de la même main.** Un dispositif où le même auteur
joue les deux côtés et tient le sifflet tendra à produire la thèse de l'auteur, et dans
main haute la thèse est reconnaissable — le lisible l'emporte, le vérifiable l'emporte,
celui qui n'a rien à protéger l'emporte.

**Lue comme une compétition, l'objection est fatale** : on ne mesure rien.
**Lue comme une graine, elle disparaît** : un auteur qui écrit tous les côtés d'un monde
fait simplement son travail, et la seule question qui reste est de savoir si le monde
obtenu est plus riche que celui qu'il aurait écrit d'un trait.

Sur main haute, la réponse est oui, et elle se prouve par les deux camps que personne
n'avait prévus. C'est le seul test qui vaille pour ce document : **une graine réussie est
une graine qui a produit un acteur que son auteur n'attendait pas.**

---

## Voir aussi

- [`partie.md`](partie.md) — l'écran du conseil, et pourquoi le brouillard ne s'y
  applique pas
- [`regles-partie.md`](regles-partie.md) — le livre de règles complet, aligné sur le greffe
- [`../scripts/agents/prompts/mj-partie.md`](../scripts/agents/prompts/mj-partie.md) — les
  règles que le MJ tient, et la voix du banc de touche en section 6
- [`echiquier.md`](echiquier.md) — les mêmes mots, du côté des cahiers d'affaire
