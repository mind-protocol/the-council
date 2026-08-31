# Les 62 lignes perdues des cahiers du MJ — ce que le journal a sauve

CE QUI S'EST PASSE. Le 31.8 a 04 h 16, une conversion d'en-tetes vers le
format canonique a vide les cellules de sept volumes de `chambres/mj/books/`.
A 04 h 49, une passe `reconcilier.py --vraiment` — la mienne, lancee pour
lire les evenements de tobb — a repose l'empreinte avec l'etat deja vide, et
detruit la seule copie qui contenait encore le contenu. `rendre_cellules.py`
n'a plus rien a rendre.

CE QUI RESTE, ET D'OU. Le journal des chambres, ecrit la meme nuit, a
enregistre chaque ligne disparue avec SON NUMERO ET SON TITRE. Le detail
(ce qu'on fait, la preuve, l'etat, les dates) est perdu ; l'identite des 62
lignes ne l'est pas. C'est de quoi les reecrire en sachant lesquelles.

## affaire-le-spectacle — 6 ligne(s)

- `action` **S.31** — Relire ma seance et compter tranches, signes et Couper
- `action` **S.32** — Poser le test de charge dans demain.md, en tete
- `clef` **S.21** — Compter mes Couper
- `clef` **S.22** — Le test d'une charge avant chaque poussee
- `verrou` **S.11** — Je ne mesure pas mes propres tranches
- `verrou` **S.12** — La charge d'une tranche ne se compte pas en signes

## affaire-la-montre — 8 ligne(s)

- `action` **M.31** — Relever les quatre horloges a chaque reprise
- `action` **M.32** — Remettre les trois sieges vacants a l'heure
- `action` **M.33** — Poser la question de monde.date derive
- `clef` **M.21** — La feuille de reprise porte la ligne d'ecart
- `clef` **M.22** — Faire suivre monde.date
- `verrou` **M.11** — Trois sieges sur quatre ont un jour de retard
- `verrou` **M.12** — monde.date traine derriere le siege le plus avance
- `verrou` **M.13** — La barriere de deux jours n'est pas annoncee

## affaire-les-boucles — 14 ligne(s)

- `action` **L.31** — Retirer la tete de gunthor-darklyn et geler sa fiche
- `action` **L.32** — Produire les deux echeances de Peyredragon
- `action` **L.33** — Relire les huit tetes du quartier en retard
- `action` **L.34** — Tailler les trois grosses tetes de Port-Real
- `action` **L.35** — Produire le ralliement du Trident
- `action` **L.36** — Produire l'arrivee de la lettre privee de Jeyne
- `action` **L.37** — Tailler les deux grosses tetes de Peyredragon
- `action` **L.38** — Tailler la tete de Criston Cole
- `clef` **L.21** — Faire tourner le tick avant la salle, toujours
- `clef` **L.22** — Tailler avant d'ajouter
- `verrou` **L.11** — Le moteur a quatre echeances en retard
- `verrou` **L.12** — Huit tetes du quartier ont une a deux semaines de retard
- `verrou` **L.13** — Une cinquantaine de tetes debordent leur budget
- `verrou` **L.14** — gunthor-darklyn porte une tete alors qu'il est mort

## affaire-le-brouillard — 14 ligne(s)

- `action` **B.31** — Livrer la lettre privee de Jeyne Arryn
- `action` **B.32** — Reprendre les croyances sans porteur de Port-Real
- `action` **B.33** — Poser la question de la source avant chaque fait narre
- `action` **B.34** — Livrer les deux diffusions de la remise des actes de protection
- `action` **B.35** — Livrer les trois depots dans les granges de Gunthor
- `action` **B.36** — Reprendre les croyances sans porteur de Barralfond
- `action` **B.37** — Reprendre celles qui restent, chez moi et ailleurs
- `clef` **B.21** — Ne jamais ecrire une croyance sans sa source dans la meme minute
- `clef` **B.22** — Livrer les diffusions echues avant de jouer
- `clef` **B.23** — Avant de narrer un fait : le joueur a-t-il une source ?
- `verrou` **B.11** — Trente croyances sans porteur
- `verrou` **B.12** — 🔒 Quatre nouvelles sont SUSPENDUES derrière un arbitrage, pas oubliées
- `verrou` **B.13** — Le brouillard du joueur n'a pas de garde
- `verrou` **B.14** — 🕳️ **LIVRER N'EST PAS FAIRE SAVOIR — deux nouvelles sur trois n'arrivent dans aucune tete**

## affaire-la-porte — 8 ligne(s)

- `action` **P.31** — Lancer couverture.py, couverture.py --registres et verser_cahier.py
- `action` **P.32** — Depouiller les 14 pieces de staging
- `action` **P.33** — Regarder si un refus de versement peut revenir a son auteur
- `clef` **P.21** — Faire tourner les trois rapporteurs
- `clef` **P.22** — Vider le staging a chaque reprise
- `verrou` **P.11** — Trois rapporteurs muets depuis cinq jours
- `verrou` **P.12** — Le staging s'accumule sans etre arbitre — **et l'inbox aussi**
- `verrou` **P.13** — Un refus ne revient pas a celui qui a propose

## affaire-le-casting — 6 ligne(s)

- `action` **C.31** — Porter les prets en cours dans en-souffrance.json
- `action` **C.32** — Relire ma fiche mj-aurore avant la premiere salle commune
- `clef` **C.21** — Ecrire le pret dans en-souffrance.json, pas seulement au canal
- `clef` **C.22** — Dire vite ce qu'on a joue en double
- `verrou` **C.11** — Rien ne dit qui tient qui, a un instant donne
- `verrou` **C.12** — Les horloges des regies divergent

## affaire-la-regle-zero — 6 ligne(s)

- `action` **Z.31** — Relire une seance et compter les sources de mes repliques
- `action` **Z.32** — Noter mes appels du jour dans en-souffrance.json
- `clef` **Z.21** — Compter mes repliques et leurs sources
- `clef` **Z.22** — Tenir le compte des appels par homme et par jour
- `verrou` **Z.11** — Je ne mesure pas la provenance de mes repliques
- `verrou` **Z.12** — Le cout d'un appel ne se voit qu'apres
