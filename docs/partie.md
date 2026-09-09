# Le conseil de guerre — l'écran de la partie

Note de conception de l'onglet « Le conseil » (`ecrans/modules/partie.js`). Les
règles du jeu, elles, vivent dans [`scripts/agents/prompts/mj-partie.md`](../scripts/agents/prompts/mj-partie.md)
et ne se changent pas ici. Le livre de règles complet, aligné sur le greffe,
est [`regles-partie.md`](regles-partie.md). Ce qu'une partie laisse derrière elle quand
on cesse de la lire comme une compétition — un monde meublé quand rien ne la ferme, une
histoire quand une date la ferme — est dans [`graines.md`](graines.md).

## Pourquoi des cartes, et pas une carte

La partie ne se joue pas sur une géographie : un lieu n'y décide de rien, il est
une mention au pied d'une pièce. Ce qui décide, c'est **ce que l'autre camp tient
contre nous** et **ce qu'on a de libre pour y répondre**. L'écran montre donc des
FRONTS — un par obstacle adverse — et un DECK toujours visible, et rien d'autre.

## La carte en lignes (6.9)

**« Il n'y a pas moyen de savoir où les verrous et les clefs s'appliquent. »**
Les états vivaient dans une rangée en tête, les verrous dans des colonnes à
part, et rien ne reliait les uns aux autres : on lisait un verrou sans savoir
sur quoi il était posé. Le joueur a dessiné la réponse, et c'est le plateau :

```
E
  e   r r c   →   R V
  e   →   R V   →   r c
```

**Une ligne par état**, l'arbre par retrait — un enfant sous son parent,
décalé d'un cran, relié par un tiret. **Tout ce qui s'applique à l'état
s'écrit à sa droite, dans l'ordre de la chaîne** : les pièces, puis la clef
qu'elles produisent ; la pièce, puis le verrou qu'elle produit ; la pièce, puis
la clef qui lève ce verrou ; et ainsi de suite, une flèche entre chaque
maillon. **Toujours la pièce avant ce qu'elle produit**, clef comme verrou : la
pièce est la cause, la carte en est la conséquence. Chaque
maillon garde sa case vide s'il en a une — on pose sur l'état, sur un verrou
d'en face, sur une clef à nous — et la case 🎯 vide reste au bout de notre
racine. L'état tient sa place à gauche ; la chaîne se replie au rang du
dessous quand la largeur manque, une clef et ses pièces restant ensemble
(demandé le 6.9 au soir, quand une chaîne de quatre maillons sortait de l'écran).

Les **frappes**, posées sur des pièces et non sur des états, gardent leur front
en colonne. Les rangées d'états et les colonnes de verrous d'avant ont disparu.

## Les sept cartes

| Signe | Carte | Ce que c'est | Où elle se tient |
|---|---|---|---|
| 🎯 | état cible | ce qu'on veut voir vrai | la colonne de gauche |
| 🔒 | verrou | ce que l'autre camp tient contre nous | en tête d'un front |
| 🗝️ | clef | ce qu'on a posé contre un verrou | sous lui, dans la pile |
| ❓ | question | ce qu'un conseiller demande avant d'exécuter | posée sur la clef qu'elle suspend |
| ⚔️ | action | ce qui a été fait, et par qui | sous la clef |
| 📦 | pièce | ce qu'on engage — 🐉 ⛵ ⚔️ 💰 👤 🏰 en sous-signe | le deck, ou empilée sous une clef |
| 💥 | frappe | ce qui vient sur une de nos pièces | son propre front |

**Ces mots ne sont pas choisis ici : ce sont ceux de l'échiquier**
([`echiquier.md`](echiquier.md)), donc ceux des cahiers d'affaire, de la
criticité et des registres que les hommes tiennent eux-mêmes. Le conseil en
avait forgé d'autres — dessein, obstacle, ordre, geste — **sur les mêmes
emojis**, si bien que 🗝️ voulait dire deux choses à deux onglets d'écart. Un
« ordre » ne désignait rien : c'était « clef » traduit du français vers le
français. Ce qui reste banni de l'écran, c'est la tuyauterie du greffier — gel,
deck, tour —, jamais un mot que la reine emploie.

Une carte a une seule anatomie : le signe en coin, un titre, une phrase, un pied
(à gauche qui la tient ou d'où elle vient, à droite son état).

## La couleur dit le camp, la trame dit le type

**Essayé dans l'autre sens le 6.9, et renversé le même jour.** Le fond a dit le
type pendant quelques heures — rouge l'état, orange le verrou, jaune la clef,
bleu la pièce —, parce que sur un duel on cherchait, dans vingt-cinq cartes
rouges, laquelle était la clef et lequel le verrou. Puis « main haute » est
passée à quatre camps, et la question du plateau a changé : ce n'est plus
« qu'est-ce que c'est », c'est **« à qui c'est »**. Deux pixels de teinte à la
bordure ne répondent pas de l'autre bout de l'écran ; un fond coloré, si. Et une
couleur par camp s'étend à N camps sans rien changer, puisque ce sont les ronds
du greffe — ⚫ 🟢 puis 🔵 🔴 🟡 🟣 dans l'ordre d'entrée.

| Canal | Ce qu'il dit | Comment |
|---|---|---|
| le fond | le camp | lavé au tiers de la couleur du camp |
| la bordure | le camp | la même couleur, en trait plein de deux pixels |
| le médaillon | le type | un cercle de papier en haut à droite, cerclé de la couleur du camp, l'emoji du type au centre (`pc-sorte`) ; posé seulement si le grand signe au centre n'est pas déjà le type |
| le halo | le verdict | vert qui respire pour acquis, rouge sombre immobile pour tranché contre |

Une carte est donc d'une seule couleur pleine, celle de qui la tient. **Les
trames sont retirées** le même jour, à la demande du joueur : les sept motifs
de fond — cercles, croisillons, hachures, points, traits — chargeaient la
carte pour redire ce que le médaillon et la place dans la grille disaient
déjà. Le seul motif restant, les hachures d'une pièce « en creux », est devenu
un bord pointillé.

**Un constat ne repeint pas le fond**, et c'est vrai dans les deux sens de la
règle : un état acquis n'est pas doré, il garde la couleur de son camp. Le
verdict se dit au **halo**, qui est son canal, et à la bordure qui le double.
**Acquis : vert, et il respire** — l'or ne pouvait pas tenir ce rôle, il est la
couleur du joueur sur tout l'écran. C'est la seule chose qui bouge sur le
plateau, parce qu'un état qui passe à vrai est le seul événement d'une partie.
**Tranché contre : rouge sombre, immobile** — un état tranché contre n'attend
plus rien de personne.

La bordure perd sa couleur de camp quand un verdict la prend — mort, hors
d'atteinte, office —, et c'est la bonne préséance : à qui elle est importe
moins que ce qu'elle est devenue. **La légende**, en bas de l'écran, ne porte
plus de palette ni de trame : le signe et son nom, sur un fond neutre.

## L'état se lit à la forme

nette = libre · empilée sous un front, liseré or = posée · pointillée = en route ·
grisée « remet N j » = gelée après un retrait ou une frappe · barrée = perdue. Sur
un ordre, un ruban : ✅ tient · ❓ suspendu · ⏳ prêt dans N jours · ⚠️ sans ressource.
**Aucun compteur, aucun numéro de tour** : les délais sont dits en jours du monde.

**Ce qui ne se joue pas le dit au repos (6.9).** La lumière du glissé répond à
« où puis-je lâcher ceci ? » ; elle n'a jamais répondu à « qu'ai-je le droit de
prendre ? », qui est la question qu'on se pose devant un plateau immobile. Une
pièce gelée, engagée ailleurs, détruite ou qui attend son arbitrage avait donc
l'air d'une pièce libre jusqu'à l'essai. Elle porte maintenant trois signes du
même sens : lavis plus pâle, bord gris, curseur barré. **Pas de tireté** : le
tireté est rendu à « pas encore là », parce qu'il se lisait comme « suspendu »
et qu'une question qui suspend une clef paraissait suspendue elle-même. Une
question n'est d'ailleurs jamais marquée interdite : elle ne se joue pas, mais
elle est active.
**Une pièce EN ROUTE n'en est pas** — le greffe accepte qu'on l'engage d'avance
et la clef est simplement « prête au tour N » (règle 4.1.3). Le marquage se
tait pendant qu'on tient une carte : c'est alors la lumière des cases qui
parle, et deux langages à la fois ne se lisent pas.

**Deux joueurs par camp : la porte du coup du jour s'ouvre à deux (6.9).**
L'écran ferme la main d'un camp dès qu'il a joué son coup compté du tour. À
un humain et une IA par camp, l'un fermait l'autre. `_courante.json` peut dire
`coups_par_camp: 2` pour la partie qu'il nomme : la vue sert `coups_max`, la
porte compare à ce nombre, et le bandeau compte « 1 coup sur 2 ce jour ». Le
greffe, lui, continue de signaler à partir du second : c'est le contrôle gradué,
et le MJ reste celui qui le tient.

**Le bandeau ne dit que ce qui n'est pas l'ordinaire (6.9).** « libre » et
« posée » y étaient écrits sur presque chaque carte, pour redire ce que la forme
disait déjà — une carte pleine et prenable, une carte rangée sous ce qui
l'engage. Ils ne s'écrivent plus du tout. **Ce qui attend devient une horloge et
un nombre de jours**, écrit plus gros que le reste des statuts et sur fond
ambré, parce que c'est le seul chiffre du plateau : ⏳4 pour une pièce qui
arrive, ⏳6 pour une question qui suspend depuis six jours ou une demande que
l'arbitre n'a pas tranchée. Le
chiffre vient du greffe (`jours`, posé par `partie_cartes`) ; la phrase entière
reste dans le volet, à un survol, et le terminal garde ses propres signes.

## Le brouillard — et pourquoi il ne s'applique PAS ici

**Décidé le 3e jour de la 9e lune, et c'est une exception assumée à la règle
cardinale de [`../CLAUDE.md`](../CLAUDE.md) « Vérité vs connaissance ».**

Le brouillard reste entier dans la CHRONIQUE : ce que le joueur apprend lui
arrive par des gens, avec le délai de la route et la déformation de la source —
un capitaine qui n'ose pas dire le chiffre des pertes, une rumeur qui enfle,
un compte arrondi en faveur de celui qui le donne. Rien de cela ne change.

**Mais le plateau n'est pas dans la fiction.** C'est l'abstraction que le MJ et
le joueur partagent pour jouer la partie, au même titre qu'un échiquier — et
aux échecs on voit les pièces d'en face. La v0 ne servait l'adversaire que par
ce qu'il avait posé contre nous ; à l'usage, l'adversaire jouait donc des coups
que personne ne voyait jamais et le plateau ne bougeait pas d'un tour à
l'autre. **Ce n'est pas de la tension, c'est un solitaire contre un processus
caché** — le brouillard n'a d'intérêt que là où l'ignorance est elle-même une
information et où l'on peut payer pour la lever ; il n'y avait ici ni l'un ni
l'autre.

La position complète est donc servie, les deux camps, pièces engagées ou non.

## Ce qui a changé depuis la dernière fois

Le jsonl est append-only, donc chaque coup porte un numéro qui ne recule
jamais : **un seul entier suffit à dire exactement ce qui est neuf.** Il vit
dans `etat/joueurs/<siège>/partie-<id>.json`, et toute carte touchée par une
ligne postérieure porte `neuf: true`.

Deux règles de tenue, chacune payée par un défaut constaté :

- **Le marque-page n'avance qu'au COUP du joueur**, jamais à la lecture. On a
  agi, donc on a regardé ; entre deux de ses coups, tout ce que l'autre camp a
  fait reste marqué. C'est ce qui évite un bouton « j'ai vu », et ce qui permet
  de revenir après deux jours d'absence et de voir en un regard ce qui a bougé.
- **Sans marque-page, rien n'est neuf.** Une première ouverture ne peut pas
  avoir manqué ce dont elle n'a jamais eu d'avant ; sans cette porte, elle
  marquait les trente-neuf cartes du plateau d'un coup. Ce premier regard POSE
  le marque-page sans rien signaler.

## Où ça vit

| Pièce | Rôle |
|---|---|
| `scripts/noyau/partie_cartes.py` | la vue : fronts, piles, deck, desseins, apparences, brouillard |
| `scripts/noyau/partie_gestes.py` | le geste traduit en coup : la CIBLE dit lequel, les refus rhabillés en clair |
| `scripts/partie.py --cartes [--camp <camp>]` | la même vue en JSON, au terminal (le premier camp de la partie sinon) |
| `scripts/noyau/partie_ascii.py` | la même vue DESSINÉE, au terminal : `--plateau` |
| `serveur/domaine/partie.js` | quelle partie pour cette requête (`?id=`, sinon `_courante.json`), et QUEL CAMP (`?camp=`, sinon le `camp` de `_courante.json`, sinon le premier de la partie — plus jamais « noir » en dur) |
| `serveur/routes/partie.js` | `GET /partie`, `POST /partie/geste`, `POST /partie/jour` |
| `ecrans/modules/partie.js` `.css` | l'échelle « Le conseil » du décor : le serveur, la vue, le plateau |
| `ecrans/modules/partie-grille.js` | la carte, le geste, et la GRILLE : une ligne par objet avec ses pièces posées dedans |
| `scripts/tests/test_partie_cartes.py` | le banc de la vue, sur `scripts/tests/donnees/partie-duel.jsonl` |
| `scripts/tests/test_partie_gestes.py` | le banc des gestes, sur une copie jetable du même duel |
| `scripts/tests/test_partie_ascii.py` | le banc du plateau texte : rien de la vue ne doit manquer au dessin |

## Faire jouer un camp par un homme — essayé, mesuré, retiré

**Le 3e jour de la 9e lune.** On a essayé de faire jouer le camp vert par un
homme réveillé dans un espace de session dédié (`depecher.py --partie`) : sa
manière et les documents de sa maison au système, et pour tout message les
règles du manuel, la position, et la diff depuis son marque-page — **aucun
brief**. Otto Hightower a joué deux fois le même coup, un `justifier` sur la
clé Meleys, avec un argument juste tiré de la position.

**Ce qui l'a fait retirer, c'est le prix.** Premier essai : 347 000 jetons et
302 secondes pour un coup. Après avoir borné ses lectures et posé « tu as dix
secondes pour jouer » : 239 000 jetons et 120 secondes — **pour un coup
rigoureusement identique**, ce qui dit assez que les quatre minutes de lecture
n'achetaient rien. À quarante coups la partie, c'est dix millions de jetons
pour faire tourner un plateau.

**Et la cause n'est pas la taille de ce qu'on lui donne.** Le prompt entier
pesait 13 000 jetons ; il en a consommé 239 000. Le coût est dans le nombre de
tours d'outils — il TRAVAILLE quand on lui demande de JOUER, et une consigne de
rythme n'a fait que le raccourcir de moitié. Les trois réductions successives
(ses cahiers, `metier.md`, ses amendements de chambre) représentaient à elles
toutes moins de 5 % de sa consommation.

**Ce qu'il faudrait tenter avant de recommencer** : un appel SANS outils, dont
la seule sortie est la ligne de coup en réponse, le MJ l'écrivant au greffe.
C'est le seul levier de l'ordre de grandeur, et il coûte à l'homme de ne plus
appeler le script lui-même.

D'ici là, **le camp vert est joué par le MJ** : il tient par défaut sans appel, et l'on ne dépêche une tête verte
que pour un coup qui n'est pas « tenir ».

**Le 6.9, la tentative sans outils existe : `scripts/partie_ia.py`.** Un appel
`claude -p --tools ""`, sortie contrainte par un schéma JSON, aucune session
conservée. Le modèle reçoit les règles, le caractère de son camp et de sa
moitié — technique ou politique, l'autre moitié étant un humain qu'il ne doit
pas jouer —, le grand livre avec ses ids, le plateau texte de son camp et les
lignes jouées depuis son dernier coup ; il rend un coup, et c'est le script
qui vérifie par le greffe, rend le refus une fois, et n'écrit qu'avec
`--vraiment`.

**Mesuré le 6.9, sur `successeurs` (deux camps, un humain et une IA par camp,
un camp `monde` au deck calendrier tenu à la ligne) :**

| Appel | Jetons entrés | Secondes | Coût | Coup |
|---|---|---|---|---|
| dépêché avec outils (3.9) | 239 000 | 120 | — | identique deux fois |
| sans outils, lancé dans le dépôt | 56 000 | 15 à 19 | 0,44 à 0,58 $ | refusé puis accepté |
| sans outils, lancé dans un dossier vide | **18 552** | **15** | **0,20 $** | accepté, avec son signe |

**Les réglages d'une partie vivent dans `etat/parties/<id>.json`** (6.9) :
`coups_par_camp`, `sieges`. `_courante.json` ne garde que la partie et le camp
servis par défaut. Deux parties vivent en même temps — `successeurs` à deux
coups par camp, `charmed` à un —, et basculer la courante sur l'une faisait
tomber les réglages de l'autre.

**Le caractère d'un camp joué par l'IA vit aussi là, et seulement là** (6.9
au soir, `charmed-2` ; 7.9, audit C5) : `caractere: {<camp>: "<texte>"}`. La
table `CAMPS` codée dans `partie_ia.py` a été supprimée — elle décrivait
charmed-1 et aurait contredit toute partie qui aurait oublié d'écrire le
sien. Un camp sans caractère ne joue pas : `partie_ia.py` s'arrête avant
tout appel, code 2, et dit quelle config compléter.

**Le schéma de l'IA suit son rôle** (7.9, audit C4) : `technique` ne reçoit
ni viser, sortir, bloquer, justifier, detruire, retourner ; `politique` ne
reçoit ni demander, ni reconstruire (lever lui reste ouvert : le greffe ne
sait pas ce qu'est une pièce technique) ; `entier` reçoit tout. La phrase du
rythme — « tu joues en premier, ton partenaire humain après » — n'est dite
qu'aux deux moitiés ; le camp entier parle à son adversaire.

**Le banc de touche va aux sièges de la partie** (7.9, audit C6) :
`python scripts/partie.py <id> --coach etat/parties/_commentaire-mj.json`
pousse le commentaire vers l'union des `sieges` de la config, un
`append_flux.py --pour <siège>` par siège ; `--voir` imprime les commandes
sans rien pousser ; sans siège déclaré, refus en clair. Matière dans
`scripts/noyau/partie_coach.py`.

**Une partie peut sortir des coups du jeu** : `coups_interdits` dans sa
configuration. Le greffe les refuse en clair (« hors de cette partie »),
l'écran n'allume pas ce qui y mènerait, et l'IA reçoit un schéma sans eux.
`charmed` se joue sans retourner, reconstruire, réarmer ni consigne — les
quatre coups qu'on ne sait pas jouer d'un geste.

**Un camp joué seul par une IA** (`--role entier`, `charmed` : le mal contre
Aurore) joue tout — états, pièces, clefs, verrous, questions, frappes,
retournements — et son mot va dans le fil de son adversaire, dans sa voix,
sans dévoiler ce qu'il prépare. C'est la Source qui parle.

**Le rythme, décidé le 6.9 : les IA jouent en premier, et parlent dans le fil.**
À chaque tour, le MJ lance les deux appels avant que les humains ne jouent.
Chaque IA rend, avec son coup, un `mot` à son partenaire — ce qu'elle a fait,
ce qu'elle voit, ce qu'elle attend de lui, sans lui donner d'ordre — et le
script le publie dans le fil des sièges de son camp (`sieges` de
`_courante.json`), en coulisses : hors univers, zéro minute, rien dans l'état.
C'est leur seul canal, et l'humain joue après l'avoir lu. Une IA joue donc sans
savoir ce que son partenaire va faire, et le partenaire hérite du coup — c'est
le prix et le sujet d'un camp partagé.

Deux choses apprises en route. **Le dossier de lancement compte** : dans la
racine, `claude -p` charge le manuel du projet par-dessus le prompt, et l'appel
triple. **Le premier refus était une règle mal comprise**, pas un caprice : le
modèle a voulu répondre par un maillon à la question de l'arbitre sur sa
racine, or un maillon réalise une clef, un blocage ou une frappe, jamais un
état ; on y répond par une clef qui sert l'état. La règle est désormais dans
son brief, et le second essai l'a jouée juste. Le refus lui est rendu une fois ;
au second, le MJ joue à la ligne. À vingt mille jetons le coup, une partie de
quarante coups par IA coûte huit dollars.

## Le geste (v1)

**Les pièces posées sont DANS la grille.** Une ligne = un objet du plateau, et
les pièces qu'il engage sont rangées à sa suite, suivies d'une case vide quand
on peut encore y lâcher quelque chose. Elles n'étaient nulle part auparavant :
`partie_cartes.py` les retire des cartes filles d'une clef — elles y répétaient
son titre —, si bien que ce avec quoi on tenait un verrou ne se voyait pas.
**La case vide est la règle rendue visible** : là où il n'y en a pas, on ne peut
pas poser.

**L'aire a été retirée le 6.9.** C'étaient douze cases sans règle sous le
plateau, où l'on rangeait ce qu'on voulait pour y penser — un brouillon qui
vivait dans le navigateur et ne partait jamais au greffe, avec sa note sur
chaque pièce rangée. Elle contredisait ce que les cases doivent dire : **toute
case de l'écran est une case du jeu**, et là où il n'y en a pas, on ne pose
pas. Douze cases qui acceptaient tout, juste sous les cases qui n'acceptent que
le légal, enseignaient l'inverse de la règle qu'on voulait faire apprendre — et
elles prenaient la place du deck. **Toute pièce à nous se soulève toujours**,
libre ou non : ce qui est illégal se refuse au greffe, avec sa phrase, pas en
rendant la carte inerte.

**Un seul geste, toujours le même : on prend une carte et on la pose sur une
autre.** Ce que ça VEUT DIRE, c'est la carte du dessous qui le dit — l'écran ne
connaît aucun nom de coup, il envoie « j'ai posé ceci sur cela » et
`partie_gestes.py` traduit :

| Ce qu'on pose | Sur quoi | Ce que le greffe écrit |
|---|---|---|
| une pièce 📦 | un obstacle 🔒 d'en face | `lever` — un ordre neuf, dont le titre est au joueur |
| une pièce 📦 | un obstacle 🔒 déjà tenu par un de nos ordres | `rearmer` — on renforce, on n'ouvre pas un doublon |
| une pièce 📦 | un de nos ordres 🗝️ | `rearmer` |
| une pièce 📦 | une frappe 💥 d'en face | `bloquer` — on couvre la pièce visée |
| une pièce 📦 | un état 🎯 d'en face | `bloquer` — un verrou neuf, dont le titre est au joueur |
| une pièce 📦 | un état 🎯 à nous | `lever` — une clef qui le SERT, sans rien ouvrir |
| une phrase | la case 🎯 vide au bout de notre rangée | `viser` — un état neuf, sous la racine |
| une phrase | la case 📦 vide au bout de « En main » | `demander` — une pièce, qui attend l'arbitre ; gratuit |
| une phrase | la poignée ❓ d'une carte d'en face | `justifier` — on exige la chaîne ; gratuit, et une seule fois par pièce |
| une phrase | la poignée ⚔️ d'une carte à nous suspendue | `agir` — le maillon qui répond, et la suspension tombe ; gratuit |
| une carte à nous | le deck | `retirer` — et ses pièces se remettent quatre jours |
| — | « Le jour passe » | `tour`, par l'arbitre |

Trois signes portent la règle, et il n'y en a pas un quatrième : ce qu'on peut
**prendre** se soulève au survol ; une carte en main **allume** ce qu'elle peut
atteindre et éteint le reste ; ce qui est **sous le curseur** s'épaissit. Un
dessein ne s'allume jamais — on ne tient pas un dessein avec un dragon, on lève
ce qui s'y oppose. C'est comme ça que la règle s'apprend, sans avoir à la lire.

**UN COUP PAR JOUR, ET L'ÉCRAN NE LAISSE PLUS LE CASSER (6.9).** Le contrôle
était gradué partout : le greffe écrivait le second coup et se contentait de le
signaler. Sur « vingt jours », Aurore en a joué trois dans le même tour sans
rien voir, et l'arbitre a dû recompter après coup puis appliquer trois jours de
calendrier — une sanction qu'on subit deux tours plus tard, pour une règle
qu'on ignorait avoir cassée. **La règle se tient maintenant à l'endroit où on
la casse.** Dès que `coups_du_jour` marque un coup pour notre camp, aucune
carte ne se soulève, la case 🎯 refuse la phrase, et tout ce qui est encore au
plateau porte le gris de `pc-interdit`.

Le blocage est à deux portes, et les deux sont voulues. `PartieGrille.epuise`
éteint le geste, pour que le plateau DISE qu'il est fini ; le même test rouvre
dans `jouer`, sur l'unique chemin par lequel un coup part vers le greffe, pour
qu'aucune bulle laissée ouverte avant le premier coup n'y échappe. **Ce qui ne
compte pas reste entier** — demander une pièce, questionner une carte d'en
face, écrire le maillon qui répond : ce sont les seuls gestes d'un camp qui a
déjà joué, et c'est très bien qu'ils soient les derniers allumés.

**Le greffe, lui, reste gradué et le restera** : un MJ qui rattrape une ligne à
la main doit pouvoir écrire ce que la règle refuse. La dureté est une propriété
de l'écran du joueur, pas du livre.

**Un refus n'est jamais un silence.** Il revient en une phrase sous la barre, et
ses ids sont rhabillés de leurs titres : « ser Steffon Darklyn déjà engagée par
*Ser Steffon fait ouvrir la porte des Dieux* », jamais `steffon-darklyn déjà
engagée par n-steffon-darklyn-v-portes`. Le contrôle « un coup par camp et par
tour », lui, ne se dit plus : il se tient, et l'écran ne l'écrit nulle part
puisqu'il ne se casse plus.

## Plus de deux camps : la couleur est celle du joueur

**Le 6e jour de la 9e lune, sur « main haute » à quatre camps.** Les cartes
portaient déjà leur teinte — bleu, rouge, or, violet, dans l'ordre d'entrée des
camps, la même règle que l'emoji du greffe. Ce sont les LIBELLÉS qui supposaient
un duel, et ils mentaient dès le troisième camp :

- **une seule bande « EUX »**, nommée d'après sa première carte : « 🔴 EUX
  openai · 24 pièces » pour dix-sept pièces d'OpenAI, cinq du successeur et deux
  du continent. Il y a maintenant **un contenant par camp d'en face**, dans
  l'ordre des camps de la partie — le même cadre que le deck, coins ronds,
  même marge —, avec son rond et son nom pour tout bandeau, et le mot « main »
  dans le coin. Ni « EUX », qui ne désignait personne, ni compte de pièces, qui
  prenait la place pour rien. Le deck porte la même forme, avec « votre main »
  dans son coin, et la ligne « En main » qui coûtait une rangée a disparu. À
  deux camps, rien ne change que ces libellés.
- **« le trône est à eux », « on attend leur coup »** : à quatre, « eux » ne
  désigne personne, et c'est la seule chose qu'on cherche en revenant devant le
  plateau. La barre **nomme le camp**, avec son rond.
- **le lavis du trait** allumait toutes les bandes d'en face en rouge. Il va à
  la seule bande du camp qui doit jouer, **dans sa couleur** (`pc-a-lui`).
- le bord double du camp qui prévaut sur une pile ne connaissait que les
  teintes 1 à 3 : un quatrième camp ne pouvait pas prévaloir à l'écran. Ajouté.

Le greffe et la vue n'avaient rien à changer : `decks` porte les camps dans
l'ordre, `eux` porte le camp de chaque carte, et c'est de là que tout se tire.

## Ce que la v1 ne fait pas

**Rien n'écrit dans `etat/`.** Le seul fichier qui s'allonge est
`etat/parties/<id>.jsonl`, en append, par le greffier — qui vérifie d'abord. Ce
qu'un coup change dans le monde reste au MJ, qui l'applique par
`partie.py --ecritures`.

**Le maillon a suivi le ❓ le 5.9 au soir**, et il le fallait : on pouvait
suspendre la pièce d'en face d'un clic sans que son camp puisse la relever, ce
qui donnait à la question un pouvoir qu'elle n'a pas au livre. La poignée ⚔️
paraît sur NOS cartes suspendues (`suspendue`, posé par `partie_marques` avec
`questionnable`), ouvre la même bulle, et le greffe reconnaît de lui-même que le
maillon répond à la question — il pose `repond`, et le coup ne compte pas.

Deux coups restent hors de l'écran : `detruire` et tout ce qui est `arbitrer`.
Ils se jouent à la ligne, par le MJ.
La raison est la même : ils n'ont pas de geste naturel sur un plateau de cartes,
et leur donner un bouton ferait un menu — ce qu'on s'interdit partout ailleurs.

**`justifier` est entré le 5.9 par la poignée ❓**, et c'est le seul coup de
l'écran qui ne soit pas un glissé — parce qu'une question n'engage aucune pièce.
Elle se paie d'une autre monnaie : une seule fois par pièce dans toute la
partie. La poignée ne paraît qu'au survol d'une carte D'EN FACE, et seulement là
où le greffe dirait oui : `partie_cartes` pose `questionnable` du même jugement
que `partie_validite` — camp adverse, pas déjà justifiée. Ce n'est pas un menu
non plus : c'est la carte elle-même qu'on interroge, à l'endroit où elle est
posée.

**`viser` et le verrou sur un état sont entrés le 5.9**, sur une partie qui
s'ouvrait (`pavillon-b`) : deux racines, aucun verrou — et donc AUCUN geste
possible à l'écran, devant sept pièces libres. Un verrou se pose sur un état
(règle 3.1) et un état se pose sous un autre : ce sont deux coups du livre, et
ils ont un geste naturel — une pièce sur la case 🎯, une phrase dans la case 🎯
vide. Ce n'est pas un menu ; c'est une case de plus.
