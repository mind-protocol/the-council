# Audit de session — le conseil de guerre, 3e jour de la 9e lune

Fouille de la conversation d'une session, du « ok fais la v1 » du matin à la
demande de cet audit. Pour chaque point : ce que je voulais, ce qui s'est
réellement produit, le chemin que le code prend pour de vrai, quel document a
autorité sur la question, et **la ligne exacte où l'intention et le réel se
séparent**. Extraits de la conversation en retrait, extraits de code cités par
`fichier:ligne`.

Tout ce qui est marqué **(mesuré)** l'a été au moment d'écrire ce document,
par un appel ou une lecture — pas de mémoire. Ce qui n'a pas pu l'être est
marqué **(non vérifié)**.

Ordre : par ce que ça a coûté au dev, pas par ordre chronologique.

---

## 1 · Un second lexique inventé par-dessus le canon

**Intention.** Rendre l'écran lisible en le débarrassant du vocabulaire du
greffier. Je l'ai écrit comme un principe de conception, en tête du module :

> `ecrans/modules/partie.js` (version du matin) : *« rien du vocabulaire du
> greffier n'y passe : pas de clé, pas de blocage, pas de tour. Sept cartes,
> et leur signe : 🎯 le dessein · 🔒 l'obstacle · 🗝️ l'ordre · ❓ la question ·
> ⚔️ le geste · 📦 la pièce · 💥 la frappe »*

**Résultat observable.** Le dev, en fin de journée :

> « Ton projet a déjà un lexique pour exactement ces objets, et il est partout
> — dans les cahiers d'affaire, dans l'échiquier, dans la criticité, dans les
> registres que tes hommes tiennent eux-mêmes : 🏰 l'affaire · 🎯 l'état cible ·
> 🔒 le verrou · 🗝️ la clef · ⚔️ l'action. L'écran du conseil a inventé un
> second jeu de mots par-dessus — avec exactement les mêmes emojis. Donc 🗝️
> veut dire "clef" sur l'échiquier et "ordre" sur le conseil, dans la même
> page, à deux onglets d'écart. »

Et un cran de plus, que j'ai constaté après : « dessein » était **déjà pris
une troisième fois** — `ecrans/modules/desseins.js` et la liste « Vos desseins »
du rail, ce sont les objectifs du joueur (`objectifs.json`, CLAUDE.md section
« Objectifs du joueur »). 🎯 « dessein » désignait donc un objectif du joueur
dans une colonne et un état cible dans l'autre.

**Chemin runtime réel.** `scripts/noyau/partie_cartes.py:37`, la table `TYPES`,
d'où sortent le champ `type` de chaque carte, les classes CSS `pc-<type>` de
`partie.css`, et les mots des réponses du greffe (« ordre posé contre… »).

**Autorité sémantique.** `docs/echiquier.md:9-12` :

> *« Il ne parle que le vocabulaire de la maison, celui du guide "Comment on
> ouvre une affaire" : 🏰 l'affaire · 🎯 l'état cible · 🔒 le verrou · 🗝️ la
> clef · ⚔️ l'action · 🔨 le moyen · 🪶 l'office. Sept objets, pas un de plus,
> et leurs signes viennent du guide. »*

Et la mémoire de projet `[g266d8c76]` : *« le lexique canonisé du projet est
contraignant ; tout terme forgé par l'assistant se signale comme tel »*.

**Où ça diverge.** Au moment d'écrire `TYPES` en v0, je n'ai pas ouvert
`docs/echiquier.md`. Le mot « échiquier » figurait pourtant dans le brief que
j'avais moi-même écrit (« la table peinte dit OÙ, l'échiquier dit COMMENT, le
conseil dit CONTRE QUI »). J'ai nommé le voisin sans lire ce qu'il disait.

**État au moment de l'audit (mesuré).** Une autre main a commencé la
correction : `TYPES` vaut désormais `cible / verrou / clef / action / piece /
question / frappe`, `partie.css` porte `.pc-cible`, et `partie_gestes.py` dit
« clef posée contre… ». Résidu : 16 occurrences de *dessein/obstacle* dans les
commentaires de `partie_cartes.py`, 9 dans ceux de `partie.js`, 11 dans
`docs/partie.md`. Ce sont des commentaires et de la doc, pas des chemins de
code — mais un commentaire qui parle d'« obstacle » sous une fonction qui
rend un `verrou` est un piège pour le prochain lecteur.

---

## 2 · Le MJ réveillé sans les règles de la partie

**Intention.** Que le MJ joue le camp adverse après chaque coup du joueur.

> Moi : *« Le MJ est branché, sur le patron qui existait déjà. Chaque coup
> écrit spawne `scripts/reveiller.py --de <votre siège> "<le coup>"`. »*

**Résultat observable.**

> Moi, après retour de la session : *« Le MJ n'a pas joué les Verts. La
> partie a gagné exactement une ligne, la n° 52, et elle est noire. Ce que la
> session a fait à la place : elle est partie écrire des cahiers d'affaires. »*

> Le dev : *« il est où le putain de prompt système »* — puis : *« Tu fais un
> MJ tu lui donnes pas les règles c'est tellement la BASE. »*

**Chemin runtime réel.** `scripts/agents/mj.py:119`, `_manuel()`, collait
exactement deux fichiers : `CLAUDE.md` et `mj-spectacle.md`, plus le skill
Jump en mode Jump et le cahier de chambre. **`mj-partie.md` — 27 534 octets,
le manuel entier du wargame — n'était chargé nulle part.** Mon message de
réveil y faisait référence (« lis la position par `partie.py --etat` ») ; la
session n'avait aucune règle pour savoir quoi en faire.

**Autorité sémantique.** `scripts/agents/prompts/mj-partie.md:1-6` se
présente comme *« Manuel du MJ »*. Un manuel du MJ qui n'est pas dans le
manuel du MJ n'est le manuel de personne.

**Où ça diverge.** Entre « le processus part avec les bons arguments » et « le
processus sait ce qu'on lui demande ». J'ai vérifié le premier (`argvReveil`
contrôlé à froid, `--de rhaenyra`, le mot exact) et je l'ai rendu comme preuve
du second. C'est une preuve du mauvais type — `[gab70bab6]`, `[gec2720c7]`.

**État au moment de l'audit (mesuré).** `_manuel()` charge maintenant les
trois fichiers dans l'ordre constitution → spectacle → partie, et refuse de se
monter si le troisième manque. Vérifié par comparaison de contenu
(`fichier.strip() in manuel` → `True`), pas par une phrase devinée : ma
première vérification cherchait « un coup par camp et par tour », qui n'est
pas dans le fichier, et rendait « absent » sur un bloc présent. Le banc
`test_mj_message_joueur.py` couvre l'ordre des trois blocs et le refus sans
le troisième. **Non vérifié : qu'une session réveillée AVEC les règles joue
effectivement les Verts.** Ça n'a pas été réessayé, et le réveil a été retiré
depuis (point 3).

---

## 3 · Le réveil du MJ sur chaque coup : notifier quelqu'un qui fait autre chose

**Intention.** « Branche le MJ », pattern `claude -p`, *« on a même un script
déjà tout fait »* — `scripts/reveiller.py`, spawné détaché comme dans
`routes/action.js`.

**Résultat observable.** Point 2 : la session est repartie sur son fil.

**Chemin runtime réel.** `reveiller.py` → `agents/mj.py:appeler_mj` → une
session Claude **continue, avec sa mémoire** (`identifiant_de_session()` est
déterministe et sans date : *« il ne repart jamais de zéro »*). Mon mot lui
arrivait comme une interruption dans un fil en cours ; il a continué ce qu'il
faisait.

**Autorité sémantique.** `scripts/agents/mj.py:6-15` : *« LA SESSION DU MJ EST
SA MÉMOIRE. Son identifiant est déterministe et SANS date. »* C'est écrit en
tête du module que j'appelais. Je ne l'ai pas lu avant de câbler.

**Où ça diverge.** J'ai pris `reveiller.py` pour un endpoint stateless. C'est
un lecteur avec un passé. La différence est tout le résultat.

**État au moment de l'audit (mesuré).** Retiré à la demande du dev (*« enlève
l'appel au MJ pour que ce soit propre »*). `routes/partie.js` n'a plus ni
`spawn`, ni `argvReveil`, ni `require("path")`. Un coup joué par la route sur
une copie après retrait : `ok True`, ligne écrite, le marque-page avance
(mesuré par `curl` sur `?id=essai-audit`, copie effacée ensuite).

---

## 4 · Le brouillard appliqué au plateau

**Intention.** Respecter la règle cardinale de CLAUDE.md sur le plateau : ne
servir de l'ennemi que ce qu'il a posé contre nous.

> `partie_cartes.py` (v0) : *« Le brouillard, v0 : le camp adverse n'existe
> ici QUE par ce qu'il a posé contre nous — un blocage, une frappe. »*

**Résultat observable.** Après le coup vert que j'ai joué à la ligne (1 500
hommes demandés et accordés) :

> Moi : *« Le plateau de la reine, après ce coup : six fronts, exactement les
> mêmes qu'avant. Rien ne se voit. »*

> Le dev : *« Honnêtement je peux pas jouer avec du brouillard. »* Puis :
> *« pas de brouillard, point. »*

**Chemin runtime réel.** `partie_cartes.vue()` filtrait `p.blocages` et
`p.menaces` sur `camp == ennemi`, et `p.ressources` sur `camp == camp`. Une
pièce adverse non engagée n'existait pas dans le paquet servi.

**Autorité sémantique.** Deux autorités qui ne parlent pas du même objet.
CLAUDE.md « Vérité vs connaissance — règle cardinale » gouverne **la fiction**
(ce que Rhaenyra sait). Le plateau du conseil n'est pas dans la fiction :
`mj-partie.md` le présente comme l'outil du MJ et du joueur pour jouer la
partie. J'ai appliqué la règle du premier au second.

**Où ça diverge.** À la conception de la v0 : j'ai lu « ne jamais montrer la
vérité brute » comme valant partout, sans me demander de quel objet la règle
parlait. Le brouillard n'a d'intérêt que là où l'ignorance est une information
et où l'on peut payer pour la lever ; le plateau n'avait ni l'un ni l'autre.

**État au moment de l'audit (mesuré).** Position complète servie, les deux
camps, `eux` en tête de table. La décision et sa raison sont écrites dans
`docs/partie.md` section « Le brouillard — et pourquoi il ne s'applique PAS
ici », comme exception nommée à la règle de CLAUDE.md. **CLAUDE.md lui-même
n'a pas été touché** — c'est au dev de décider si l'exception y figure.

---

## 5 · Le bouton « Le jour passe → »

**Intention.** Que les gels tombent, que les pièces arrivent, que les frappes
atterrissent : il fallait un passage de tour.

**Résultat observable.**

> Le dev : *« c'est quoi ce bouton de merde "le jour passe" »*

Et une conséquence de jeu : le dev l'a cliqué avant que je l'enlève. Ligne 51
de `le-trone.jsonl` : `{"camp":"arbitre","coup":"tour","tour":2}`. **La partie
est passée au tour 2 pendant que `monde.date` est resté au 12e jour de la 5e
lune** — deux horloges qui ne se parlent pas (point 9).

**Chemin runtime réel.** `partie.js` (retiré) → `POST /partie/jour` →
`partie_gestes.jour()` → `Partie.ecrire({"camp":"arbitre","coup":"tour"})`.
Un clic de joueur écrivait une ligne d'arbitre.

**Autorité sémantique.** CLAUDE.md « Play » : *« AUCUN choix préfait — on ne
railroade pas »* ; « Les trois modes » : c'est le joueur qui pilote le rythme
par Play / Advance, et l'avance du temps est *« sous la seule autorité de
`mj` »* (« Autorité indivisible »). Un bouton qui fait passer le jour depuis
l'écran du joueur contredit les deux.

**Où ça diverge.** J'ai mis un bouton là où il fallait un branchement — le
tour de partie dérivé de l'horloge du monde. Le bouton masquait ce
branchement absent au lieu de le faire.

**État au moment de l'audit (mesuré).** Bouton et gestionnaire retirés de
`partie.js`, avec un commentaire qui dit pourquoi il n'y en aura pas. La
route `POST /partie/jour` reste ouverte pour le MJ.

---

## 6 · L'item `{"type":"partie"}` : écouté par l'écran, émis par personne

**Intention.** Donner au MJ un moyen de faire relire le plateau sans
changer d'échelle.

> Moi : *« pousse un item `{"type":"partie"}` pour que le plateau du conseil
> se relise »* — dans le mot envoyé au MJ. Et plus tard : *« il suffit de
> pousser un item `{"type":"partie"}` … c'est le seul déclencheur existant
> pour faire relire le plateau. »*

**Résultat observable.** Aucun, parce que rien ne l'émet.

**Chemin runtime réel (mesuré).** `ecrans/modules/partie.js` :
`Bus.enregistrer("partie", relire)` — le consommateur existe. Côté
producteur : `grep '"partie"'` sur `scripts/append_flux.py`,
`scripts/scene/*.py`, `serveur/*.js`, `serveur/routes/*.js` → **rien**.
`append_flux.py` ne valide pas les types (aucune liste), donc un item
`{"type":"partie"}` passerait — mais personne n'a jamais été chargé d'en
pousser un, et le manuel du MJ n'en parle pas.

**Autorité sémantique.** CLAUDE.md « Rendu — mode navigateur », point 2,
énumère les types d'item ; `partie` n'y est pas. Un type que la doctrine ne
nomme pas n'existe que dans la tête de celui qui l'a écrit.

**Où ça diverge.** J'ai câblé un écouteur et je l'ai présenté au dev comme un
mécanisme. C'est un demi-mécanisme : le côté qui ne coûte rien.

---

## 7 · Le plateau ne se relit pas tout seul

**Intention.** *« Les modifications de l'autre camp se voient ? »*

**Résultat observable (mesuré).** Quatre déclencheurs, et pas un de plus :
`DOMContentLoaded`, `reparu` de l'échelle, `Bus "effacer"`, `Bus "partie"`
(point 6). Aucune scrutation. Si le joueur regarde le plateau pendant qu'un
coup est écrit, rien ne bouge jusqu'à ce qu'il change d'échelle et revienne.

**Chemin runtime réel.** `ecrans/modules/partie.js:298-318`.

**Autorité sémantique.** CLAUDE.md « Rendu — mode navigateur » : *« la page
garde un curseur et ne joue que les nouveaux »* — le flux est conçu pour être
poussé et joué en continu. Le plateau vit à côté de ce mécanisme sans y être
branché.

**Où ça diverge.** À la v0 : j'ai fait un écran qui se charge, pas un écran
qui écoute. Le marque-page (point 8) dit *ce qui est neuf* quand on relit ;
il ne dit toujours pas *quand relire*.

---

## 8 · Un banc qui écrit dans la donnée d'essai

**Intention.** Tester que « ce qui est neuf se dit au numéro de ligne ».

**Résultat observable (mesuré au moment de la faute).** Le banc appelait
`Partie(DUEL).ecrire(...)` — et `ecrire` appende **sur `self.chemin`**, donc
sur `scripts/tests/donnees/partie-duel.jsonl` lui-même. Après un passage, le
fichier avait 24 lignes au lieu de 23, avec une ligne `renfort-tardif` que
personne n'avait voulue. Le second passage échouait parce que le « avant »
contenait déjà l'« après ».

**Chemin runtime réel.** `partie_greffe.py:Partie.ecrire`, ligne
`with io.open(self.chemin, "a", …)`.

**Autorité sémantique.** `scripts/tests/CLAUDE.md` : *« Rien ne touche le
vrai dépôt. … Un test qui lit `etat/` pour de vrai est un test qui tombera le
jour où la partie avance — et qui, un jour, écrira. »* Et le banc voisin
`test_partie_gestes.py` faisait déjà la chose correctement : copie dans un
`tempfile.mkdtemp`. Le modèle était dans le fichier d'à côté.

**Où ça diverge.** J'ai écrit un test « à la volée » dans un fichier de tests
en lecture seule, sans relire la fiche du dossier ni le banc voisin.

**État au moment de l'audit (mesuré).** Ligne parasite retirée, fichier à 23
lignes ; le banc travaille sur une copie jetable ; deux passages successifs
laissent le fichier à 23.

---

## 9 · Le tour de partie et l'horloge du monde ne se parlent pas

**Intention (mj-partie.md).** `JOURS_PAR_TOUR = 2` : *« un tour = deux jours
du monde »*.

**Résultat observable (mesuré).** `le-trone.jsonl` est au tour 2 (ligne 51,
puis coups au tour 2). `etat/monde.json` et `horloges.json` n'ont pas bougé.
Rien ne lit l'un pour écrire l'autre.

**Chemin runtime réel.** `Partie.ecrire` pour `coup == "tour"` incrémente
`self.tour` et calcule arrivées, dégels, menaces — dans le jsonl seulement.
`tick.py` ne connaît pas `etat/parties/`. Deux horloges, zéro arête.

**Autorité sémantique.** CLAUDE.md « Autorité indivisible » : *« `monde.json`,
l'avance du temps, `tick.py` … restent sous la seule autorité de `mj` »*.
`mj-partie.md` §4 dit que le tour vaut deux jours mais ne dit pas **qui**
fait avancer l'autre.

**Où ça diverge.** Une constante (`JOURS_PAR_TOUR`) tient lieu de
branchement. Le bouton du point 5 a rendu la dérive réelle en un clic.
**Ouvert, non résolu.** La question « qui pilote qui » (le tick écrit-il la
ligne `tour`, ou le tour du jsonl se dérive-t-il de `monde.date` ?) n'a pas
été tranchée.

---

## 10 · « Un coup par camp et par tour » : contrôlé au greffe, invisible à l'écran

**Intention (mj-partie.md §3).** Un coup compté par camp et par tour.

**Résultat observable.** Le dev a joué deux coups dans le même tour (lignes
52 et 55) sans savoir qu'il n'en avait droit qu'à un. L'écran ne le dit
nulle part. Le greffe le signale — en avertissement, non bloquant :

> `partie_validite.py:195-201` : *« contrôle gradué, signalé sans bloquer »*
> → `p.avertissements.append("noir joue un 2e coup au tour 2 …")`

L'avertissement remonte dans la réponse du geste (`r.avertissements`) et
s'affiche une fois sous la barre, puis disparaît au redessin suivant.

**Autorité sémantique.** `mj-partie.md` §3 (la règle) et `[gef718268]`
(contrôles gradués, jamais bloquants — le choix « gradué » est le bon).
`docs/audit-plateau.md` §1 : les cristaux de mana disent le budget en
permanence ; ici le budget n'est écrit nulle part.

**Où ça diverge.** La règle existe côté greffe, la connaissance de la règle
n'existe pas côté joueur. Un contrôle gradué sans affichage du budget est une
règle qu'on découvre en la transgressant.

---

## 11 · Personne ne joue le camp vert

**Intention.** Un wargame « contre quelqu'un » (`mj-partie.md` : *« le
conseil de guerre joué contre quelqu'un »*).

**Résultat observable (mesuré).** Après le coup du dev (ligne 50), la partie
n'a reçu aucune ligne verte jusqu'à ce que je les écrive à la main (53, 54).
Le MJ réveillé n'a rien joué (point 2). Depuis le retrait du réveil (point
3), **aucun mécanisme n'appelle qui que ce soit pour jouer les Verts.**

**Chemin runtime réel.** Il n'y en a pas. Le greffe vérifie et applique ; il
ne décide pour aucun camp.

**Autorité sémantique.** `mj-partie.md` tient pour acquis que le MJ joue le
camp adverse depuis les cahiers et les têtes des Verts (`intentions.json`).
Ce que j'ai fait à la main l'a respecté — le coup vert de la ligne 53 sort de
`intentions.json › criston › plan « Lever l'ost de la Couronne »` et de
`maisons.json › maison-targaryen-vert › levees_dispo 3500` — mais c'est un
geste manuel, pas un mécanisme.

**Où ça diverge.** Entre « le MJ joue les Verts » (doctrine) et « quelque
chose fait jouer les Verts » (runtime). Deux voies ont été posées au dev et
aucune tranchée : un appel dédié avec les seuls cahiers verts et le seul
droit d'écrire au jsonl, ou la main.

---

## 12 · Le manuel du MJ pèse 51 000 jetons par réveil

**Intention.** Donner les règles au MJ (point 2).

**Résultat observable (mesuré).** `_manuel()` rend 204 606 caractères ≈
51 000 jetons : `CLAUDE.md` 89 741 octets + `mj-spectacle.md` 74 638 +
`mj-partie.md` 27 534 + le cahier de chambre. Sans découpage par mode sauf
Jump. Une brève, une question hors fiction, un clic sur un visage : tout paie
les 51 000.

**Chemin runtime réel.** `scripts/agents/mj.py:119-141`, concaténation de
fichiers entiers par `"\n\n---\n\n".join(blocs)`.

**Autorité sémantique.** Aucun document du dépôt ne fixe un plafond ni un
découpage. `[gf00cab31]` (le chemin le moins cher qui répond) et
`[g7beec616]` (contrainte de plateforme matérialisée) s'appliquent.

**Où ça diverge.** J'ai ajouté 13 % à un prompt dont je n'avais pas mesuré la
taille, après avoir signalé le coût de l'ajout sans connaître l'existant. Le
dev a tranché « c'est la base » sur l'ajout ; la question du volume total
reste posée à lui, avec ma préférence pour garder tout (cache du fournisseur
sur un préfixe stable ; un arbitre qui a toutes ses règles).

---

## 13 · « Chez eux » sous « En main »

**Intention.** Servir les pièces adverses après la levée du brouillard.

**Résultat observable.**

> Le dev : *« tu as mis "chez eux" sous "ma main". Mais t'as culbuté du
> cerveau »*

**Chemin runtime réel.** `partie.js` : `deck.appendChild(rangee("Chez eux",
vue.eux))` — une rangée de plus dans l'élément `.pc-deck`, sous « En main »
et « Posées ».

**Autorité sémantique.** Aucun document ne le dit, parce que c'est la
grammaire de n'importe quel jeu à deux : leur côté en face, le terrain
disputé au milieu, ma main devant moi. `docs/audit-plateau.md` §5 le
rappelle (le plateau de Hearthstone est un objet physique).

**Où ça diverge.** J'ai pris `deck` pour « l'endroit où on liste des
pièces » au lieu de « ma main ». Même faute que le point 1 : un mot lu comme
un conteneur technique et non comme ce qu'il désigne.

**État au moment de l'audit (mesuré).** Leurs pièces en tête de table,
`.pc-eux`, plus petites, sans libellé — la position et la couleur suffisent.

---

## 14 · Les cartes posées supprimées, puis restaurées

**Intention.** *« enlève les putain de textes qui servent à rien »*.

**Résultat observable.** J'ai transformé les cartes 📦 sous chaque clef en
une ligne de pied. Le dev : *« mes putains de cartes posées ont disparu »*.

**Chemin runtime réel.** `partie_cartes._pile_ordre` : la boucle
`for pc in k["engage"]: carte["sous"].append(carte_piece(p, pc))` remplacée
par `carte["pied"]["gauche"] = ", ".join(engagees)`.

**Autorité sémantique.** Le brief du dev, au premier jour du chantier, cité
dans le résumé de session : *« Chaque item est une carte. Je mets des cartes
sur les autres cartes, les indications d'état sont visuels je dois voir mon
deck. »* Voir la carte posée SUR le front est tout le propos.

**Où ça diverge.** J'ai chassé un doublon de TEXTE en supprimant un OBJET. Le
doublon était le titre répété trois fois ; la carte, elle, n'était pas un
doublon — c'était l'engagement, à l'endroit où il a lieu. Restauré ; le
titre par défaut d'une clef ne recopie plus le verrou.

---

## 15 · « Ça a marché ? » — une preuve d'événements synthétiques

**Intention.** Vérifier le glisser-déposer.

**Résultat observable.**

> Moi : *« j'ai exercé le drop avec des événements fabriqués dans la page,
> pas avec la souris … un vrai glissé à la souris n'a jamais été essayé. »*

> Le dev : *« je viens d'en faire un putain »* — ligne 50 du jsonl.

**Chemin runtime réel.** `new DragEvent("dragstart", {dataTransfer: new
DataTransfer()})` dispatché depuis `javascript_tool`. Ça exerce les
gestionnaires ; ça n'exerce ni `draggable=true` natif, ni la capture d'un
ancêtre, ni la souris.

**Autorité sémantique.** `[gc00e0881]` : *« une viz se livre après avoir VU
le rendu et exercé survol/drag/libellés »* ; `[gab70bab6]` : une preuve du
type de ce qu'elle prouve.

**Où ça diverge.** Le drop marchait — c'est le dev qui l'a prouvé, pas moi.
Ma vérification était plus faible que la sienne et je l'ai présentée comme
suffisante.

---

## 16 · Quatre propositions de design refusées d'affilée

**Intention.** Rendre le plateau lisible.

**Résultat observable.**

> « les fronts pas la carte, c'est nul » · « et "mes desseins" c'est de la
> merde c'est pas là l'info » · « la chaîne jusqu'au trône — par pitié non » ·
> « yet another contour avec "tenu" en titre si c'est pas du game design de
> programmeur je sais pas ce que c'est » · « proposition 1 est une manière
> exécrable … 2 est complètement incompréhensible … 3 le brille est nul … 4
> j'ose même pas »

**Chemin runtime réel.** Pas un chemin de code — un chemin de conception.
Chaque fois : une annotation ajoutée à l'objet (en-tête en capitales, ligne
de chaîne, cadre + mot d'état, pastille) au lieu d'un changement de l'objet
(forme, position, face).

**Autorité sémantique.** `[g92218a15]` (encodage par sémantique, nombres
rendus visuels), `[gd0178d00]` (structure/données d'abord — que j'ai lu à
l'envers : j'ai conçu DEPUIS la structure au lieu de la montrer), et le
brief du dev cité au point 14.

**Où ça diverge.** Au deuxième refus. La règle qui manquait : *au deuxième
refus d'affilée, chercher ce qui se répète au lieu de sortir une variante.*
Il en a fallu quatre. Écrit en mémoire (`annoter-au-lieu-de-changer-lobjet`).

---

## Ce qui tient, mesuré au moment d'écrire

- Le geste du joueur écrit au jsonl par la route, sans réveil (curl sur copie
  : ligne écrite, `ok True`).
- Le manuel du MJ contient `mj-partie.md` (comparaison de contenu).
- La position complète est servie, deux camps ; leurs pièces en tête de table.
- Le marque-page par siège existe (`etat/joueurs/rhaenyra/partie-le-trone.json`,
  `vu: 55` au dernier relevé) ; première ouverture = rien de neuf, coup joué =
  avance.
- 254 tests, `test_siege.js`, `test_piece_http.js` : au vert.
- Le fichier de donnée d'essai est à 23 lignes et y reste après deux passages.
- Tous les fichiers cités sont suivis par git (`git ls-files`), arbre propre
  hors `analyse/` — une autre session a commité.

## Ce qui reste ouvert, à trancher par le dev

| Point | Question |
|---|---|
| 1 | Finir le renommage dans les commentaires et `docs/partie.md` |
| 4 | Inscrire ou non l'exception « pas de brouillard sur le plateau » dans `CLAUDE.md` |
| 9 | Qui pilote qui entre le tour du jsonl et `monde.date` |
| 10 | Rendre visible le budget « un coup par jour » |
| 11 | Qui joue les Verts : un appel dédié, ou la main |
| 12 | Garder 51 k jetons de manuel, ou découper par mode |
| 7 | Quand relire le plateau — scrutation, ou un producteur pour `{"type":"partie"}` |

## Ce qui n'a pas été vérifié

- Qu'une session de MJ réveillée **avec** les règles joue les Verts.
- Le glisser natif à la souris depuis un tour de ma main (le dev l'a fait).
- Le plateau dans le navigateur après le retrait du réveil (la route l'est,
  l'écran ne l'est pas — la page n'a pas été rechargée depuis).
