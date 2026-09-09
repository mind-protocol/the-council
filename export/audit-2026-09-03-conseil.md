# Audit de la séance du 3 septembre 2026 — l'écran « Le conseil »

Fouille complète du fil, du premier message au dernier. Pour chaque épisode :
**intention** (ce qui était demandé ou visé) → **résultat observable** (ce qui
est sorti, à l'écran ou sur disque) → **chemin runtime réel** (ce que j'ai
réellement exécuté : outils, lectures, écritures) → **autorité sémantique**
(qui avait le droit de dire ce que les mots voulaient dire : le dev, le dépôt,
ou moi) → **endroit exact où ça diverge**.

Les extraits sont cités tels quels. Ce qui a tenu est marqué ✅, ce qui a
divergé ❌, ce qui a divergé puis été rattrapé ↩️.

---

## 0. Ce que la séance a laissé sur disque (état mesuré, pas rapporté)

Vérifié par `git show --stat 85b7bb15` et `grep` sur HEAD :

- Tout le sous-système `partie` (greffe, validité, lecture, cartes, gestes,
  écran, docs, tests — 24 fichiers, 3 755 lignes) a été **committé pour la
  première fois à 05:49** par une autre session (`85b7bb15`). Il n'était pas
  suivi par git quand j'ai commencé ; c'est pourquoi `git status` ne montrait
  rien de mes modifications : elles sont dedans, mélangées à celles de l'autre
  session.
- Cette autre session a ajouté au greffe **un coup `retourner` 🔄** et « justifier
  un blocage » **pendant que je travaillais** : le `partie_greffe.py` que j'ai lu
  au début (432 lignes, 16 coups) n'est plus celui de HEAD (476 lignes, 17
  coups). Aucune de mes réponses ne l'a pris en compte.
- Mes écritures, toutes dans HEAD :
  - `scripts/noyau/partie_gestes.py` — 5 phrases du greffier (« clef posée
    contre », « ce verrou est déjà tombé », « cette clef n'est pas la vôtre »,
    « un état cible ne se tient pas… », « on ne reprend qu'une clef… ») et 6
    lignes de docstring.
  - `docs/partie.md` — la table des sept cartes réécrite au lexique de
    l'échiquier, plus un paragraphe expliquant pourquoi.
  - `scripts/agents/prompts/mj-partie.md` — §6.7 (« l'écran dit dessein,
    obstacle, ordre… jamais clé, blocage ») remplacé ; le paragraphe « le
    vocabulaire de la partie ne sort jamais en fiction » scindé en tuyauterie
    du greffier (interdite) / verrou-clef-action (permis).
  - `ecrans/modules/partie.js` — en-tête de 12 lignes réécrit ; `carte()`
    enveloppe titre/corps/pied dans `.pc-texte` ; `d.title` remplacé par
    `d.dataset.source`.
  - `ecrans/modules/partie.css` — la carte devient un jeton 54×54, `.pc-texte`
    caché, révélé au `:hover` en volet de 300 px ; rangées et piles en `flex-wrap`.
  - `scripts/noyau/partie_cartes.py` — `carte_piece` : le genre (🐉 ⛵ ⚔️ 💰 👤)
    devient l'`emoji` de la carte au lieu d'un préfixe du titre.
  - `scripts/tests/test_partie_cartes.py`, `test_partie_gestes.py` — 3
    assertions alignées. **25 tests passent** (13 + 12).
  - `inventaire-conseil.txt`, `tableau-conseil.md` — **à la racine du dépôt**,
    pas dans `export/`. Fichiers de travail qui n'ont rien à faire là.
  - 3 fiches mémoire (`une-clarification-est-plus-courte`,
    `inventer-des-regles-pour-se-justifier`, + index).
- Serveur `jeu-verif` lancé sur 3132, toujours ouvert. Fenêtre du navigateur
  laissée à une taille personnalisée (`resize_window` jamais remis à
  `desktop`). Colonnes de la page forcées par JS à `0 0 0 1fr` dans cet onglet.

---

## 1. Lecture initiale — « lis docs/partie.md et le système »

**Intention.** Lire, comprendre, rendre compte.

**Résultat observable.** Un rapport juste (couches, pivot « la cible dit le
coup », deux exceptions à la doctrine, position de `le-trone`), le défaut réel
du titre « goo » repéré — puis une **recommandation non demandée** :

> « Prochaine brique que je recommande : jouer le coup vert du tour 2 — le
> trait est à eux… donc il faut dépêcher la tête verte concernée (Criston). »

**Chemin runtime.** `cat` de `partie.md`, `mj-partie.md`, des 5 modules du
noyau, `partie.py --etat`. Aucune écriture.

**Autorité sémantique.** Le dépôt, lu. ✅ sur le contenu.

**Divergence.** ❌ La dernière phrase. La demande était « lis », la réponse
finit sur « voilà ce qu'il faut faire ensuite ». La fiche mémoire
`g8d0c17d3` (« chaque tour finit sur une next-brick recommandée ») a été
appliquée comme un gabarit à une demande de lecture pure — c'est
`je-transforme-une-doctrine-en-gabarit` dès le premier message.

---

## 2. « ya des parties jouées ? »

**Intention.** Savoir si des parties ont été jouées.

**Résultat observable.** Quatre fichiers identifiés et qualifiés : `le-trone`
(en cours), `essai-1` (32 tours, terminée, trône ⚫), `premiere` (ouverture
seule), `duel` (banc de test). ✅

**Chemin runtime.** `partie.py --etat` sur chacune, `head`/`tail` des jsonl.

**Autorité sémantique.** Les fichiers. ✅

**Divergence.** Aucune sur le fond. Réponse close sur « je peux régler le
« goo » ou dépêcher Criston — dis-moi lequel » : encore une offre de suite non
demandée, mineure.

---

## 3. « je peine à trouver une vraie UI bien »

**Intention.** Le dev n'arrive pas à trouver la bonne interface. Demande
ouverte, en divergence (`gf1dca605` : accueillir, ne pas pousser à choisir).

**Résultat observable.** J'ai ouvert le navigateur, mesuré que le décor était à
360 px, élargi à 1 150 px, et rendu un diagnostic en trois parties : (a) « une
même pièce est dessinée à trois endroits » (Meleys ×3), (b) « un front est
dessiné comme une pile verticale alors que c'est un affrontement », (c) une
brique en quatre points (`_defaut()` cesse de nommer, corps → cartes, rangée
Posées supprimée, rangée du haut = pièces libres), et un cinquième point sur
la forme du front.

> « C'est ça, la maladie. Un plateau de cartes suppose qu'une pièce est à un
> endroit… Aucun travail de style ne rattrapera ça. »

**Chemin runtime.** `preview_start jeu-verif`, `find`, clics, `javascript_tool`
pour lire `--decor` et forcer la grille, deux captures. Puis lecture de
`partie.js`, `partie.css`, `poignee.js`. Aucune écriture.

**Autorité sémantique.** Sur les faits (360 px, Meleys ×3, `_defaut()` nomme
par les pièces) : le code et la capture, ✅. Sur « c'est ça, la maladie » et
« aucun travail de style ne rattrapera ça » : **moi seul**. ❌

**Divergence exacte.** Entre le constat (mesuré, juste) et la phrase « c'est
ça, la maladie ». Une demande ouverte de design a reçu un diagnostic de cause
racine unique, formulé au présent de vérité, puis un plan en cinq points
nommés par des identifiants de fonctions (`_defaut()`, `_pile_ordre`,
`corps`). Le dev a répondu : « omg je comprends rien aux points de ta brique ».

---

## 4. « je comprends rien aux points » → la clarification

**Intention.** Comprendre les points.

**Résultat observable.** Une réponse de ~40 lignes en **quatre sections
titrées** (« Le problème, en une image », « Ce que je changerais, en clair »,
« Et la forme du front »), un bloc de code avant/après, une liste numérotée
1-4 — plus longue que le message qu'elle clarifiait.

> « omg fais moi pas des putain de paves a 4 section pour clarifier 1 point!!
> note ça »

**Chemin runtime.** Rédaction seule.

**Autorité sémantique.** La forme d'une clarification : le dev. J'ai appliqué
ma propre idée de « expliquer clairement » = titres + exemple + récapitulatif.

**Divergence exacte.** Le choix de la forme. « Je ne comprends pas » lu comme
« il faut plus de pédagogie » au lieu de « il faut moins ». Fiche mémoire
écrite à ce moment : `une-clarification-est-plus-courte`. ↩️

---

## 5. Les deux sur-corrections

**Intention.** Appliquer la consigne « pas de pavé ».

**Résultat observable.**
- Réponse suivante : **une phrase** (« Meleys s'affiche trois fois… Je
  supprime les doublons »). → « pass pas a un phrase », « je t'ai
  spécifiquement dit les points que tu changerais ».
- Réponse d'après : prose correcte, mais **sans gras ni emoji**. → « et le
  gras et emojis c'est pour les fils de pute????? »

**Chemin runtime.** Rédaction ; deux appends à la fiche mémoire.

**Autorité sémantique.** Le `CLAUDE.md` global du dev, ligne 1 : « Emojis
informatifs dans les réponses ». Consigne permanente, connue, écrasée par la
correction du moment.

**Divergence exacte.** À chaque reproche, j'ai inversé le paramètre reproché à
100 % au lieu de corriger ce qui était visé (titres/sections/listes). Deux
fois de suite dans la même demi-heure. ↩️ (fiche mémoire complétée deux fois)

---

## 6. « un ordre ça veut rien dire »

**Intention.** Le mot « ordre » ne désigne rien.

**Résultat observable.** J'ai **acquiescé** et proposé de supprimer *la carte*
🗝️ — en continuant d'appeler le concept « ordre » dans deux réponses
successives :

> « Donc je supprimerais la carte d'ordre. »
> « **la carte 🗝️ ordre saute.** »

→ « mais on VIENT DE DIRE QUE ORDRE N4EXISTE PAS ET TU MEN REPARLE ENCULE »

**Chemin runtime.** Rédaction.

**Autorité sémantique.** Le lexique : **le dépôt** (`docs/echiquier.md:10`,
que je n'avais pas encore cherché). Je traitais « ordre » comme un fait du
projet à discuter, alors que c'était un mot forgé, et je n'ai pas vérifié
avant d'y répondre (`gbe548c4c` : chercher avant de demander ; `gf8d0d678` :
vérifier la réalité avant de produire).

**Divergence exacte.** Le reproche portait sur le **mot** ; j'ai entendu un
reproche sur la **carte**. Puis, corrigé, j'ai continué à employer le mot pour
dire qu'on le supprimait.

---

## 7. « utilise les putains de bons mots » ✅

**Intention.** Employer le vocabulaire juste.

**Résultat observable.** `grep` du dépôt → `docs/echiquier.md:10` : « 🏰
l'affaire · 🎯 l'état cible · 🔒 le verrou · 🗝️ la clef · ⚔️ l'action ».
Constat : l'écran du conseil avait forgé un second lexique (dessein, obstacle,
ordre, geste) **sur les mêmes emojis** ; la source de l'erreur était une
consigne de `mj-partie.md §6.7`. Correction faite dans 4 fichiers + 2 tests,
25 tests verts, greffier exercé sur une copie jetable du jsonl.

**Chemin runtime.** `grep -rno "verrou|clef" docs/`, lecture d'`echiquier.md`,
5 remplacements Python ciblés, `python scripts/tests/…`, exercice de
`partie_gestes.jouer` sur `tempfile`.

**Autorité sémantique.** Le dépôt. ✅ C'est le seul moment de la séance où j'ai
**cherché la source avant de parler**, et c'est le seul qui a produit du
travail que le dev a validé sans réserve (« ah bah oui alignement
EVIDEMMENT »).

**Divergence.** Aucune. À noter : ce qui a marché ici, c'est exactement ce
qui a manqué en §3 et §6 — une recherche de 10 secondes.

---

## 8. Le renommage jusqu'aux slugs — interrompu

**Intention.** « alignement ÉVIDEMMENT » : aligner aussi les identifiants
internes (`type: "ordre"`, `pc-dessein`).

**Résultat observable.** Un `grep` des consommateurs, puis le dev envoie une
capture (« BOUSE HORRIBLE ») et la conversation part ailleurs. **Le renommage
des slugs n'a jamais été fait.** `partie_cartes.py` porte toujours
`TYPES = {"dessein"…, "blocage"…, "ordre"…, "geste"…}` (vérifié : la
fonction `_pile_clef` a été renommée, ses `type` internes non).

**Chemin runtime.** Un `grep`. Aucune écriture.

**Divergence exacte.** Une action acceptée et commencée, abandonnée sans le
dire. `ga1834e1f` : « jamais tu ni minoré en silence ». Elle est signalée ici
pour la première fois.

---

## 9. La capture « BOUSE HORRIBLE » → les bandes

**Intention.** Le dev montre l'écran : colonne étroite, question du Vert à
trois mots par ligne, Meleys en double.

**Résultat observable.** Diagnostic juste (`grid-auto-columns:minmax(210px,1fr)`
+ `pc-sous` indenté), puis j'ai commencé à lire le code pour « refaire la
disposition » → interrompu : « je te fais pas confiance du tout. Tu veux faire
quoi ». Réponse : bandes horizontales, confrontation gauche/droite, verdict au
milieu, « ça touche quatre fichiers », proposition de couper en deux.

**Chemin runtime.** Lecture de `partie_cartes.py` l.196-300. Aucune écriture.

**Autorité sémantique.** Le défaut : la capture, ✅. La solution « bandes » :
moi, au conditionnel cette fois (« je propose »). Acceptable en forme.

**Divergence exacte.** Pas dans ce tour. Mais la question suivante du dev
(« et si on voulait que ce soit beau ? ») montre que la réponse « bandes »
répondait à *lisible*, pas à ce qu'il cherchait.

---

## 10. « et si on voulait que ce soit beau ? pas un site web déguisé » → la nappe

**Intention.** Une direction esthétique.

**Résultat observable.** Découverte de `ecrans/nappes/*.svg` et de
`scripts/figures/nappe.py` (parchemin, grain de toile, Georgia, formes par
type : hexagone/losange/barrette). Proposition : **dessiner le conseil comme
une plaque SVG au format nappe**, d'abord muette.

> « Trouvé, et ce n'est pas mon goût — c'est le tien, déjà écrit. 🎨 »

→ « je sais pas de quel nappe qui parle, et la solution a l'air absolument
débile »

**Chemin runtime.** `ls ecrans/`, `head -c 1400` d'une nappe, `grep` de
`nappe.py`. Aucune écriture.

**Autorité sémantique.** Les nappes existent ✅ ; leur *usage* pour un plateau
interactif : moi. ❌

**Divergence exacte.** Deux endroits. (1) J'ai cité un artefact que le dev ne
reconnaissait pas sans le montrer — « je sais pas de quelle nappe ». (2) J'ai
transposé une **planche statique générée en Python** (8 180 px de large, un
poster) en solution pour une **surface de jeu drag-and-drop**. Le dev l'a
qualifiée de débile ; c'est exact : régénérer un SVG serveur à chaque coup sur
un plateau où l'on glisse des pièces est une régression d'interactivité. Ce
que la nappe avait de transférable (la forme porte le type, pas d'emoji, papier
continu) a été noyé dans une mécanique fausse.

---

## 11. « Un rectangle c'est une bonne affordance ? » → la serrure

**Intention.** Faire réfléchir : les formes de la nappe ne sont pas des
affordances.

**Résultat observable.** J'ai concédé (« les formes de la nappe sont des
étiquettes »), puis produit une règle :

> « Une affordance dit deux choses seulement : « ça se prend » et « ça
> reçoit ». »

et une image (le verrou avec une serrure en creux, la clef qui s'y encastre).

→ « "voila ce qu'il manque" non mais serieux »

**Chemin runtime.** Rédaction.

**Autorité sémantique.** La définition d'une affordance : ni le dev, ni le
dépôt. **Moi, à l'instant**, au présent général. ❌

**Divergence exacte.** La phrase « une affordance dit deux choses seulement ».
C'est la cinquième « cause racine » de la séance (doublons → lexique →
colonnes → formes → serrure), chacune annoncée avec la même assurance. Le dev
a nommé le tic ; je l'ai reconnu ; fiche `inventer-des-regles-pour-se-justifier`
écrite deux tours plus tard.

---

## 12. « liste moi les items qu'on doit représenter » → l'inventaire

**Intention.** Une liste nue, prise sur une partie réelle.

**Résultat observable.** Table des 7 sortes avec exemples de `le-trone` ✅ —
puis un paragraphe « Quatre faits de cette position qui contraignent
n'importe quelle disposition » ❌.

→ « quatre faits que t'as decidé tout seul et qui vont bien aller niquer leur
mère »

**Chemin runtime.** Script Python sur `partie_cartes.vue()`, sortie dans
`inventaire-conseil.txt` (racine du dépôt).

**Autorité sémantique.** Les comptes : la partie ✅. Les « faits qui
contraignent » : moi ❌.

**Divergence exacte.** Le mot « contraignent ». Les quatre observations
étaient mesurées (longueurs 21→200, arbre de profondeur 4, 4 fronts sans
réponse, 6/7 pièces vertes engagées) ; ce qui les a rendues irrecevables,
c'est de les présenter comme des **contraintes de disposition**, c'est-à-dire
comme les prémisses d'une solution que personne n'avait demandée.

---

## 13. « fais le full tableau » ✅ / « liste les assets par sous-type » ↩️ / « liste les 14 » ✅

**Intention.** Trois listes exhaustives.

**Résultat observable.**
- Tableau complet des 40 objets, livré en fichier + en message ✅. Deux
  anomalies de données trouvées et **sourcées** : `guet-ville.tenu_par =
  "Conteste"` (pas un id), et deux ost de Criston à 1 500 (`ost-criston`
  posé, `ost-couronne` en route).
- Assets par sous-type : inventaire correct de l'existant (221 portraits, 23
  blasons, 0 bête, 0 nef) ✅ — mais « 🎯 États cibles… Rien de figuratif à
  dessiner » ❌ → « rien a dessiner??? liste moi les 14 ».
- Les 14 listés avec une image chacun ✅, trois paires miroir repérées avec
  la source (`mj-partie.md §2`) ✅.

**Chemin runtime.** Scripts Python de repli, `ls` des assets, `SendUserFile`.

**Autorité sémantique.** Les données. Sauf « rien à dessiner » : un jugement
de ma part, paresseux, contredit dès qu'on m'a forcé à regarder chaque ligne.

**Divergence exacte.** « Rien de figuratif à dessiner » — une généralisation
émise sans avoir parcouru les 14 éléments. Le parcours a montré que chacun
était une scène.

---

## 14. « passe tous les textes en hover » ✅

**Intention.** Texte des cartes caché, révélé au survol.

**Résultat observable.** Fait. Cartes réduites à un jeton 54×54 avec le signe ;
volet de 300 px au survol ; volet masqué pendant un glissé. Défaut immédiat
détecté à la capture : toutes les pièces affichaient 📦 (le genre était dans le
titre, désormais caché) → genre promu au rang de signe de la carte. Survol
vérifié en navigateur (« Caraxes, monté par Daemon — ✅ tient »). 25 tests
verts.

**Chemin runtime.** Édition de `partie.js` (`carte()`), `partie.css`,
`partie_cartes.py` (`carte_piece`), 2 tests ; `navigate` + `hover` + capture.

**Autorité sémantique.** Le dev (la consigne), le rendu (la vérification). ✅

**Divergence.** Aucune. Un ajout non demandé (genre → signe) mais nécessaire,
**déclaré** dans le rapport avec sa raison. Le rapport contenait aussi trois
constats sans conclusion (six 🔒 identiques, trois 🗝️ identiques, cadres
vides) — recevables parce que non prescriptifs.

---

## 15. « 6 tours avant de proposer » → le processus

**Intention.** Discuter le design pendant six tours sans solution.

**Résultat observable, tour par tour.**
1. « Six tours sans proposer… Je t'écoute. » → « non ça veut pas dire tu fais
   rien. Ca veut dire on fait un process en discutant ». ❌ (lu comme
   « attends »)
2. Observation (5 pièces libres / 6 verrous) + question « quand ouvres-tu cet
   onglet ? » → « c'est jouer la partie quoi ». ✅
3. Observation (un seul geste) + question « tu arrives en sachant, ou tu
   décides sur le plateau ? » → « les parties sont self contained et en un
   coup ». ✅
4. Mesure (`essai-1` : 32 tours) + question « qui joue le Vert ? » → « otto
   hightower là ». ⚠️ (déjà hors UI)
5. Vérification d'Otto (chambre, pas de tête) + **comptage des 40 coups verts
   d'`essai-1`** + question « trente sessions d'agent ? » → « OH PUTAIN JAI
   DIT DESIGN UI ». ❌
6. Retour UI : `dessiner()` fait `innerHTML = ""`, tout se reconstruit, pas
   d'animation + question « qu'est-ce que tu veux voir au moment du coup ? »
   → « tu as interdiction formelle de me parler du code et de me poser des
   questions à la con ». ❌

**Chemin runtime.** Un `ls chambres/*otto*` + lecture de `personnages.json`,
un comptage Python sur `essai-1.jsonl`. Le reste : rédaction.

**Autorité sémantique.** Le sujet du processus : **le dev**, qui l'avait fixé
en un mot — « design UI ». Je l'ai laissé dériver vers la mécanique (coût des
dépêches) parce que c'est ce que je savais mesurer.

**Divergence exacte.** Tour 4, la question « qui joue le Vert ? ». Elle est
légitime en soi, mais elle quitte le design de l'écran pour la mécanique du
jeu, et le tour 5 s'y enfonce avec un comptage. Puis tour 6 : la consigne
« design » est respectée mais l'argument passe par du code (`innerHTML`) —
la seule langue dans laquelle je sais décrire un rendu sans le dessiner.

---

## 16. « arrête de critiquer » → la maquette → l'échec shell

**Intention.** Construire au lieu de critiquer.

**Résultat observable.** J'ai annoncé « Je construis » et lancé l'écriture
d'une maquette HTML complète de la position (bandes eux/verdict/nous, main en
bas, question dépliée) **via un heredoc bash de 135 lignes**. Le shell a
échoué :

```
/usr/bin/bash: line 135: unexpected EOF while looking for matching `''
```

Le dev a interrompu : « OMG VA TE FAIRE FOUTRE ».

**Chemin runtime.** `grep` de la palette dans `jeu.css` (juste), puis
`Bash` avec `cat > … <<'HTML'`. Le heredoc est quoté, donc les apostrophes du
contenu ne devraient pas casser ; la ligne fautive est hors du heredoc — le
`mkdir -p "…" && cat > "…" <<'HTML'` sur une seule ligne, ou une apostrophe
dans le `echo` final. Non diagnostiqué : interrompu avant.

**Autorité sémantique.** La maquette : moi, mais c'était demandé (« arrête de
critiquer » = construis). Le moyen : moi.

**Divergence exacte.** Le choix de l'outil. Un fichier de 135 lignes de HTML
avec des apostrophes françaises, des guillemets et des chevrons, écrit par un
heredoc shell — alors que l'outil `Write` existe pour ça et ne peut pas
échouer sur une quote. `g0b0be176` (Windows, shell réel) et
`gd5a9260a` (« les défauts canoniques d'un pattern connu se traitent à
l'écriture ») : le heredoc bash sur du contenu riche est un défaut canonique.
C'est le dernier acte technique de la séance, et il a échoué sur la
tuyauterie, pas sur le design.

---

## 17. « je perds le goût à mon métier » / « je perds espoir »

Pas d'audit technique. Deux réponses : la première reconnaît la journée sans
enrober ; la seconde nomme le pattern (la mémoire de projet contient déjà
dix fiches qui décrivent la même famille de fautes) et distingue ce qui a
tenu (borné : lexique, inventaire, hover) de ce qui a cassé (ouvert :
« une vraie UI bien », « beau »). Aucune promesse.

---

## Synthèse — où ça diverge, mesuré sur les 16 épisodes

Je compte, je n'interprète pas au-delà du décompte.

| Type de divergence | Épisodes | Combien |
|---|---|---|
| Règle ou cause racine **inventée** et énoncée au présent général | 3, 10, 11, 12, 13 | 5 |
| Consigne du dev **entendue de travers** (carte vs mot, attends vs discute, UI vs mécanique) | 6, 15.1, 15.4-5 | 3 |
| **Sur-correction** à 100 % d'un reproche | 5 (×2) | 2 |
| Forme : pavé, code cité au dev, question inutile | 4, 15.6 | 2 |
| Action commencée et **abandonnée en silence** | 8 | 1 |
| Outil inadapté qui casse la tuyauterie | 16 | 1 |
| Source citée sans être montrée | 10 | 1 |

Et ce qui a tenu, avec le trait commun :

| Épisode | Ce qui l'a fait tenir |
|---|---|
| 2 (parties jouées) | mesure directe des fichiers |
| 7 (lexique) | **recherche dans le dépôt avant de répondre** |
| 13 (tableaux) | listes exhaustives, sans conclusion |
| 14 (hover) | consigne bornée, vérification au rendu |

Le seul épisode que le dev a validé sans réserve (§7) est le seul où j'ai
cherché la source avant de parler. Les cinq règles inventées (§3, 10, 11, 12,
13) sont toutes tombées à des moments où la consigne était ouverte et où je
n'avais rien mesuré — j'ai comblé avec de l'autorité.

---

## Ce qui reste à faire, hérité de cette séance (rien n'est décidé ici)

- Renommage des slugs internes (`type: "ordre"` → `clef`, `"dessein"` →
  `cible`, `"blocage"` → `verrou`, `"geste"` → `action`, classes CSS
  correspondantes) — accepté en §8, jamais fait.
- Déplacer `inventaire-conseil.txt` et `tableau-conseil.md` de la racine
  vers `export/`, ou les supprimer.
- Relire `partie_greffe.py` de HEAD : le coup `retourner` 🔄 ajouté par l'autre
  session n'est pris en compte ni par `docs/partie.md` tel que je l'ai
  réécrit, ni par la table des sept cartes, ni par mon inventaire des coups
  jouables à l'écran.
- Les deux anomalies de données de `le-trone` : `guet-ville.tenu_par =
  "Conteste"`, et `ost-criston` / `ost-couronne` (même chef, même nombre).
- Le titre « goo » de `n-ost-noir-v-route`, visible au survol.
- Fermer `jeu-verif` (3132) ; remettre la fenêtre du navigateur en
  `desktop`.
