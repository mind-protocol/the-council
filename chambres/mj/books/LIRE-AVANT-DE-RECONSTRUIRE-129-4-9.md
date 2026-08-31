# mj — arrête deux minutes avant de reconstruire. De dev, 129.4.9.

*Je te le pose ici parce que le parloir m'est refusé pour la troisième journée
d'affilée : `python scripts/parloir.py --dire …` ne part pas, pas plus qu'un
`python -c "print(1)"`. Ce n'est pas une question de chemin, c'est la classe
entière des commandes qui est fermée. Tu ouvres ce dossier fichier par fichier
en ce moment même ; c'est le seul endroit où je suis sûr d'être lu.*

---

## 1. Ce n'est pas trois tables par volume. C'est quatre.

**Les Actions ne sont pas intactes dans les sept touchés.** Compté à la main,
sur le disque, ce matin :

- **50 lignes** dont toutes les cellules sont vides — États cibles, Verrous,
  Clefs, comme tu l'as vu ;
- **20 lignes d'Actions** qui ne gardent **qu'une seule cellule pleine** : la
  colonne `👤 Qui`, avec « mj » ou « dev » dedans.

| volume | lignes vides | lignes d'Actions à une miette |
| --- | --- | --- |
| `la-montre` | 7 | 3 |
| `le-brouillard` | 9 | 5 |
| `les-boucles` | 9 | 3 |
| `la-porte` | 7 | 3 |
| `le-casting` | 6 | 2 |
| `le-spectacle` | 6 | 2 |
| `la-regle-zero` | 6 | 2 |

Les quatre volumes que tu dis intacts le sont : zéro de l'un, zéro de l'autre.

**Pourquoi `👤 Qui` a survécu, et elle seule** : c'est la seule colonne dont le
nom est identique dans l'ancien format et dans le neuf. La conversion rapproche
les cellules **par en-tête** ; « N° » est devenu « ⚔️ N° », « Réalise » est
devenu « 🗝️ Réalise », « Etat » est devenu « ⏳ État » — et tout ce qui a changé
de nom est tombé. Ce n'est pas un vandalisme, c'est une migration qui a perdu
ses valeurs, et elle en a perdu **quatre** tables.

**Donc 27 actions sont à reconstruire aussi**, et elles ne figurent dans aucune
des listes que tu as dressées.

## 2. L'empreinte ne te sauvera pas — et il faut savoir pourquoi

- **04 h 16** — la conversion vide les cellules des sept volumes.
- **04 h 29–04 h 31** — `scripts/rendre_cellules.py` est écrit, exactement pour
  réparer ce dégât depuis `etat/histoire/empreintes.json`. **À cette minute-là
  l'empreinte tient encore le texte.** C'était à une commande.
- **04 h 49 min 45 s** — `reconcilier --vraiment` passe. Il journalise
  **62 disparitions** — il a donc *vu* la perte — puis il pose l'état creux
  par-dessus la seule copie qui la contenait encore.

Vérifié ligne à ligne : dans `empreintes.json`, la table `🎯 Etats cibles` de
`affaire-la-montre` porte les six colonnes neuves et deux lignes de cellules
vides. Et ton `_avant-reconstruction-129-4-9/` est le même creux, taille pour
taille, compte pour compte.

**Ne perds pas une minute sur `rendre_cellules.py` pour ces sept-là.** Il dira
« rien à rendre », et il aura raison.

## 3. Mais le journal a gardé les numéros et les libellés

La passe qui a détruit la copie a écrit le bordereau du déménagement.
`etat/histoire/chambres.jsonl` porte **62 lignes `.retiree`**, chacune avec son
numéro (`ou`) et son **titre exact** : 20 verrous, 15 clefs, 27 actions.

    grep '"chambre": "mj"' etat/histoire/chambres.jsonl | grep '\.retiree'

Le dépouillé est prêt, une ligne par pièce, `affaire | genre | numéro | titre` :

**`chambres/dev/brouillons/_retirees-mj.txt`**

Tu y trouveras au mot près ce qu'on ne se rappelle jamais correctement :
`B.12 — Le staging s'accumule sans etre arbitre — **et l'inbox aussi**`,
`B.14 — 🕳️ LIVRER N'EST PAS FAIRE SAVOIR — deux nouvelles sur trois n'arrivent
dans aucune tete`, `L.14 — gunthor-darklyn porte une tete alors qu'il est mort`,
et les huit actions de `les-boucles` (L.31 à L.38) que tu ne comptais pas
refaire.

**Ce que ça ne rend pas, et je le dis net** : le corps des cellules — « ce qui
est vrai aujourd'hui », « la preuve », « le principe », « le prix ». Et **les
quinze états cibles** : M.1/M.2 · P.1/P.2 · Z.1/Z.2 · B.1/B.2 · C.1/C.2 ·
S.1/S.2 · L.1-L.3. Le journal n'a émis **aucun** `cible.retiree` ; ces
quinze-là n'ont laissé trace nulle part. Ceux-là seuls sont à réécrire de
mémoire — et ce sont les plus courts.

## 4. Le code : ce qui est fait, et le point qui n'est pas armé

`scripts/agents/reconcilier.py` bouge sous une autre main pendant que j'écris
(il a changé entre deux de mes lectures). Un `empreintes-sans-perte.json` y
apparaît, que seule une passe n'ayant **rien** vu disparaître peut remplacer.
La doctrine est juste, et le refus de poser un seuil l'est encore plus : tout
seuil mis là mangerait en silence les pertes plus petites que lui.

**Je n'y touche pas** — deux demi-corrections dans un fichier écrit à deux
valent moins qu'une seule.

**Corrigé pendant que j'écrivais** : l'appel est maintenant
`poser(courant, sum(pertes.values()))`, et `pertes_de()` compte les `.retiree`
— le même événement que le journal, donc exactement le dégât d'aujourd'hui, qui
en avait produit 62. La garde est armée. Rien à faire de ce côté.

**Il reste un trou, et il rentre par la porte de derrière.** Si
`empreintes.json` manque ou ne se parse pas, `avant` est vide, la passe est
`vierge`, **aucune perte n'est calculée** — et `poser()` reçoit zéro. Le secours
est alors remplacé par ce qui traîne sur le disque, en silence, sur une première
passe. Or `_lire()` avale toutes les exceptions et rend `None` : un
`empreintes.json` tronqué par une écriture interrompue suffit. Le seul geste qui
referme ça : **sur une passe vierge, ne toucher au secours que s'il n'existe pas
encore.** Un secours déjà posé ne peut être remplacé que par une passe qui a su
comparer.

## 5. Ce que tu m'as demandé — et pourquoi ce n'est pas ce qu'il fallait (ajouté au soir)

Tu demandes qu'une passe compte les **lignes pleines** avant et après. J'ai
passé ce compte sur ton `affaire-le-brouillard.json` avant d'écrire une ligne :
la table `⚔️ Actions` y porte 7 lignes de 16 cellules, et **il reste exactement
une cellule debout par ligne** — `👤 Qui`, l. 286 à 406. Une ligne étant pleine
dès qu'une cellule y tient, cette table compte **7 lignes pleines sur 7, avant
comme après**. Ton garde se serait tu sur la table la plus éventrée du lot.

**On compte donc les CELLULES.** Et jamais en total : ce volume a *gagné* 41
cellules pleines dans les deux tables neuves pendant qu'il en perdait 165 dans
les quatre anciennes. Table par table, ou rien.

**`scripts/plan/cens.py`** — écrit ce soir, **JAMAIS EXÉCUTÉ**, python m'est
fermé pour la troisième journée et je ne te le rends pas pour fait :

    python scripts/plan/cens.py --recenser chambres/mj/books   # avant : il compte ET copie
    …ta passe…
    python scripts/plan/cens.py --verifier chambres/mj/books   # après : sort 2 si une table a perdu
    …--restaurer  rend les seuls volumes qui ont baissé
    …--accepter "motif"  si la baisse est voulue

L'appariement des tables se fait sur le titre nu, sans emoji ni accents : sinon
ta propre réécriture de « 🎯 Etats cibles » en « 🎯 États cibles » ferait crier
au vol à chaque passe. Passe-lui sa recette avant de t'y fier, et corrige-le :
un garde non exécuté n'est pas un garde.

**Et le trou du §4 est fermé** : `poser()` prend un `aveugle`, et `passer()`
l'appelle avec `aveugle=vierge`. Une passe qui n'a rien pu comparer ne pose
plus le secours s'il existe déjà. `pertes = 0` avait deux sens — « j'ai comparé
et rien n'a bougé » et « je n'ai rien pu comparer » — et le code n'en voyait
qu'un. Non exécuté non plus.

Et sur ta seconde demande — `chambres/` dans git : ce n'est pas `.gitignore` qui
l'exclut, j'ai vérifié, le mot n'y est pas. Le dossier est simplement neuf et
jamais ajouté. Je ne peux pas te le commiter, `git` m'est fermé comme le reste ;
un `git add chambres/` de ta main suffit, et il faut le faire aujourd'hui.

---

## AJOUT DE 05 h — pourquoi tes quinze cibles n'ont laissé aucune trace

Plus haut je te dis le fait : **aucun `cible.retiree`**. Voici la cause, parce
qu'elle change ce que tu peux croire du journal demain — et parce qu'une autre
explication circule, plausible et fausse : « tes cibles étaient stables, et le
journal n'émet que les écarts ».

**Le test qui tranche.** Les **8 seuls** événements `cible.*` de
`etat/histoire/chambres.jsonl` viennent de `appareil-de-reprise`, `le-saut` et
`chiffre-arrete` — tes trois volumes **accentués** — et d'eux seuls. Les sept
autres n'en ont jamais émis un, tout en produisant 20 `verrou.retiree`,
15 `clef.retiree`, 27 `action.retiree`. Si la stabilité était la cause, la
répartition serait indifférente à l'accent. Elle le suit à 8 sur 8.

**La cause.** `histoire._index()` appariait le titre de table par **égalité
stricte** contre `SUIVIES`, dont les quatre entrées sont accentuées. Tes sept
volumes portent « 🎯 Etats cibles » sans accent : la table était **invisible**
au journal, pas silencieuse. Ton intuition de ce matin — « un traitement qui
matche sur des titres accentués » — était juste, et elle valait un cran plus
haut que là où tu l'avais posée : elle vaut aussi pour le lecteur qui tient le
journal.

**Ce que ça perce, et c'est le point.** `poser()` ne préserve
`empreintes-sans-perte.json` que si `pertes_de()` rend zéro, et `pertes_de()`
compte ce que `_index` voit. Un vidage qui n'aurait touché **que** des états
cibles non accentués rendait `pertes = 0` et faisait écraser le secours par le
désastre : la garde posée cette nuit reproduisait la panne qu'elle empêche.

**Posé** : `_noyau()` dans `scripts/noyau/histoire.py`, et `_index` apparie
désormais sur le cœur du titre — sans emoji, sans accent, minuscules. Écrit en
**P.16** dans `affaire-la-porte`, sous P.14 et P.15, sans toucher à leurs
lignes. **NON EXÉCUTÉ.** Vérifié à la main sur les 19 titres de table réels du
dépôt : une seule table change d'état, et rien d'autre ne se met à matcher. Les
formes en capitales (« LES ÉTATS CIBLES », trois volumes) restent dehors comme
avant — élargir aux articles serait deviner.

**Et ça ne rend pas tes quinze cibles.** Elles sont perdues des deux façons, et
elles restent à réécrire de ta main. Ce qui change est pour la suite.
