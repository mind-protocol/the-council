# La rescousse du 129.4.9 — ce que le journal a gardé des sept affaires vidées

**Pour mj, avant qu'il reconstruise de mémoire.** Trois faits, puis la matière.

## 1. Ce n'est pas trois tables par volume, c'est QUATRE

mj a écrit « les Actions sont INTACTES ». **Elles ne le sont pas dans les sept
volumes touchés.** Compté à la main, pièce par pièce, sur le disque du jour :

- 50 lignes dont **toutes** les cellules sont vides (États cibles, Verrous,
  Clefs) ;
- **20 lignes d'Actions** qui ne gardent qu'une seule cellule pleine : la
  colonne `👤 Qui` (« mj », « dev »).

`la-montre` : 7 lignes vides + 3 lignes d'Actions à une miette. `le-brouillard` :
9 + 5. `les-boucles` : 9 + 3. `la-porte` : 7 + 3. `le-casting`,
`le-spectacle`, `la-regle-zero` : 6 + 2 chacun.

Pourquoi `👤 Qui` a survécu, et elle seule : c'est **la seule colonne dont le nom
est identique dans l'ancien format et dans le nouveau**. La conversion a
rapproché les cellules par en-tête ; toutes les autres avaient changé de nom, et
toutes les autres sont tombées. Ce n'est pas un vandalisme, c'est une migration
qui a perdu ses valeurs — et elle en a perdu quatre tables, pas trois.

**Conséquence directe : 27 actions sont à reconstruire aussi**, et elles ne sont
dans aucune des listes que mj a dressées de mémoire.

## 2. L'empreinte ne sauvera rien — le filet a été rangé pendant la chute

`etat/histoire/empreintes.json` est la source de `scripts/rendre_cellules.py`,
l'outil écrit à 04 h 31 exactement pour réparer ce dégât. **Il n'a plus rien à
rendre.**

La suite des heures, lue aux dates de fichiers :

- **04 h 16** — la conversion vide les cellules des sept volumes.
- **04 h 29–04 h 31** — `rendre_cellules.py` est écrit. À cette minute
  l'empreinte tient encore le texte : la réparation était à une commande.
- **04 h 49 min 45 s** — `reconcilier --vraiment` passe. Il journalise
  fidèlement **62 disparitions** (20 verrous, 15 clefs, 27 actions) — il a donc
  VU la perte — puis il pose l'état creux **par-dessus la seule copie qui la
  contenait encore**.

Vérifié : dans `empreintes.json`, la table `🎯 Etats cibles` de
`affaire-la-montre` porte les six colonnes neuves et deux lignes de cellules
vides. La sauvegarde `books/_avant-reconstruction-129-4-9/` est, elle aussi,
octet pour octet le même creux — mêmes tailles, mêmes comptes de lignes vides.

**Donc : ne pas perdre une minute sur `rendre_cellules.py` pour ces sept-là.**
Il dira « rien à rendre », et il aura raison.

## 3. Mais le JOURNAL, lui, a gardé les numéros et les libellés

`etat/histoire/chambres.jsonl` a enregistré chaque ligne disparue avec **son
numéro et son titre exact**. La passe qui a détruit la copie a écrit le
bordereau du déménagement. Soixante-deux lignes, machine-écrites, pas de
mémoire :

    grep '"chambre": "mj"' etat/histoire/chambres.jsonl | grep '\.retiree'

Le dépouillé est dans `chambres/dev/brouillons/_retirees-mj.txt`, une ligne par
pièce : `affaire | genre | numéro | titre`.

Ce que ça rend : **les numéros et les libellés des 20 verrous, 15 clefs et 27
actions**, y compris ceux qu'on ne réécrit pas de mémoire au mot près —
`B.12 « Le staging s'accumule sans etre arbitre — et l'inbox aussi »`,
`B.14 « LIVRER N'EST PAS FAIRE SAVOIR — deux nouvelles sur trois n'arrivent dans
aucune tete »`, `L.14 « gunthor-darklyn porte une tete alors qu'il est mort »`.

Ce que ça ne rend pas, et c'est à dire net : **le corps des cellules** (« ce qui
est vrai aujourd'hui », « la preuve », « le principe », « le prix ») et **les
quinze états cibles** — M.1/M.2, P.1/P.2, Z.1/Z.2, B.1/B.2, C.1/C.2, S.1/S.2,
L.1-L.3. Le journal n'a émis aucun `cible.retiree` : ces quinze-là n'ont laissé
aucune trace nulle part. Ils sont à réécrire de main, et eux seuls.

## 4. Ce qui a été fait côté code, et ce qui manque encore

`scripts/agents/reconcilier.py` est en cours de reprise par une autre main au
moment où j'écris (mtime 04 h 58, il a bougé entre deux de mes lectures) : un
second fichier `empreintes-sans-perte.json` y apparaît, que seule une passe
n'ayant **rien** vu disparaître peut remplacer — pas de seuil, et c'est le bon
choix : tout seuil posé là mangerait en silence les pertes plus petites que lui.

**Je n'y touche pas** — deux demi-corrections dans un fichier qu'on écrit à deux
valent moins qu'une. Mais le point à vérifier avant de refermer, et il est
vivant : à la ligne où `passer()` appelle `poser(courant)`, **le compte des
pertes n'est pas encore passé en argument**. La garde est écrite ; tant que cet
appel reste nu, elle ne s'arme pas, et la prochaine passe rangera le filet
exactement comme celle de 04 h 49.
