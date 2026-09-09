# Charmed 2 — le dossier de préparation

Ce dossier prépare une **seconde partie Charmed**, à jouer avec le système de
partie du dépôt (`docs/regles-partie.md`, `scripts/partie.py`,
`scripts/partie_ia.py`). Il ne contient **aucun état** : rien ici n'est lu par
le greffe ni par l'écran. Ce sont des notes, des références et des lignes
prêtes à être jouées, que le MJ recopie dans `etat/parties/` le jour où il
ouvre la partie.

Ce qu'on corrige par rapport à la première (`etat/parties/charmed.jsonl`,
sept tours joués les 5 et 6 septembre 2026) tient en deux mots :
**plus conforme à la série, plus stratégique.** Le détail est dans le bilan.

| Fichier | Ce qu'il contient |
|---|---|
| [`01-bilan-charmed-1.md`](01-bilan-charmed-1.md) | ce que la première partie a montré, tour par tour, et les six défauts qu'on répare |
| [`02-canon.md`](02-canon.md) | la référence série pour l'arc choisi : personnages, pouvoirs, règles de la magie, ce que la Source a réellement fait, épisode par épisode |
| [`03-conception.md`](03-conception.md) | la partie elle-même : l'époque, les camps, les racines datées, les fronts, la table des délais, les coups permis, ce qui la rend stratégique |
| [`04-cartes-de-depart.md`](04-cartes-de-depart.md) | **les cartes de départ** : chaque pièce avec sa ligne `demander`, son arbitrage, sa portée et sa note de jeu ; les états proposés pour chaque deck ; le calendrier des arrivées |
| [`05-ouverture.md`](05-ouverture.md) | la configuration `charmed-2.json`, les lignes d'ouverture prêtes pour `--fichier`, le caractère du mal pour `partie_ia.py`, les trois items d'ouverture de Radio Halliwell, la marche à suivre |
| [`07-analyse-charmed-2.md`](07-analyse-charmed-2.md) | l'analyse stratégique de la partie jouée : la partition des vingt tours, les trois moments où elle s'est décidée, le jeu de chaque camp, ce que ça dit du jeu et trois réglages pour Charmed 3 |
| [`reine-des-enfers/`](reine-des-enfers/README.md) | **Charmed 3, « La Reine des Enfers »** : le dossier complet de la partie suivante — saison 4 fin, trois camps, Phoebe à ramener, l'enfant à disputer ; ouverture testée au greffe (61 lignes, 0 refusée) |
| [`06-arbitrage.md`](06-arbitrage.md) | la doctrine de l'arbitre pour cette partie : comment on tranche le Livre, Leo, la fenêtre de Paige, le Hollow, le secret, le gain personnel — et les réponses aux questions qu'Aurore a posées dans la première |

## Le choix en une phrase

**Saison 4, premier arc : de l'enterrement de Prue (4x01 « Charmed Again ») à
la chute de la Source (4x13 « Charmed and Dangerous »).** Vingt tours, deux
jours du monde par tour. Le bien (Aurore) doit **reconstituer** le Pouvoir
des Trois avec Paige, tenir le secret, et **vaincre la Source** avant le
vingtième tour ; le mal (une IA en entier, la Source) doit briser le Pouvoir
des Trois — tuer ou retourner une sœur — et il a pour cela exactement les
moyens que la série lui a donnés : la fenêtre des quarante-huit heures de
Paige, Shax, les Furies, les chasseurs de primes, la Voyante, le Hollow.

Les deux racines sont **datées** : au vingtième tour l'arbitre constate les
deux, et il peut les constater toutes deux fausses. C'est une histoire, pas un
monde (`docs/graines.md`).

## Résultat : JOUÉE ET GAGNÉE PAR LE BIEN, le 6 septembre 2026 au soir

Vingt tours, 165 lignes (`etat/parties/charmed-2.jsonl`). Le trône au bien
au passage du vingtième : la Source vaincue au tour 15 par le sort des
aïeules, Cole humain tenant le Hollow (4x13) ; trois sœurs vivantes, ensemble,
du bien. Les cinq portes du mal fermées dans l'ordre de la série : Shane
démasqué (t3), Shax dispersé et le Pouvoir des Trois reconstitué du même
geste (t5), les Furies sans colère à prendre (t8), la Voyante sans Belthazor
(t10), le Hollow rendu (t15). Aucune frappe n'a touché une sœur ; P3 a fermé.
Coût de l'IA du mal : dix-neuf appels, environ 3,5 $.

**Ce que la partie a appris, à reporter dans `06-arbitrage.md` et dans le
code** : (1) une potion consumée doit SORTIR du grand livre — laissée
« libre », elle a été rejouée deux fois ; il faut un verdict qui détruit la
pièce qui frappe sans toucher la cible (un `tranche` à `nombre: 0` détruit la
cible : greffe) ; (2) la case 🎯 date les états d'office (tâche ouverte) ;
(3) deux écritures simultanées donnent deux fois le même `n` (tâche
ouverte) ; (4) le geste « pièce sur une frappe d'en face » a servi trois fois
à dire une frappe du bien — la Convention 1 a tenu, mais un geste de frappe à
l'écran manque toujours.

## État à l'ouverture, le même soir

- `etat/parties/charmed-2.json` et `_courante.json` écrits d'après
  `05-ouverture.md` ; l'ouverture (`ouverture.jsonl`, 52 lignes) jouée sans
  refus ; le tour passé au 2.
- `scripts/partie_ia.py` lit désormais `caractere: {<camp>: "<texte>"}` dans
  la configuration de la partie avant sa table `CAMPS` — le caractère du mal
  du §3 de `05-ouverture.md` vit dans `charmed-2.json`, le script n'a plus à
  changer d'une partie à l'autre.
- Premier coup de la Source, tour 2 : le retournement de Paige par Shane
  (n° 54), portée jugée bonne (n° 55). Radio Halliwell a poussé ses trois
  items d'ouverture, le commentaire du coup et l'horloge dans le fil
  d'Aurore. **Le trait est au bien.**

**Une règle du même jour à connaître** (`docs/parties/gestes-manquants.md`,
6.9) : un `demander` de joueur ne porte plus `lieu` ni `tenu_par` — c'est
l'arbitre qui les pose en accordant. Les lignes de `04` et de
`ouverture.jsonl` les portent encore parce qu'elles ont été jouées avant ;
pour les pièces demandées en cours de partie (la potion de Belthazor, le
sort des aïeules, Sam), **le lieu va dans la phrase et dans l'arbitrage**.
Même jour : une clef lève UN verrou, un maillon n'a plus d'état, `consigne`
est sortie des règles.
