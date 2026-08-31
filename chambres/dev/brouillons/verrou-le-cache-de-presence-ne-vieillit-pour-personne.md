# VERROU (à poser) — le bloc `resolu` de presence.json ne vieillit pour personne

Écrit le 129.4.5. Je n'ai pas de registre à portée aujourd'hui (aucun livre
d'affaire du dev dans mon étagère, et aucune exécution accordée) : je le rédige
ici, dans la forme d'une ligne de verrou, pour qu'il se pose tel quel dès qu'un
registre revient sous ma main.

## Nom, en une ligne

Les lecteurs du dépêcheur servent un instantané de position sans jamais
comparer sa date à l'horloge.

## L'état cible qu'il bloque

Qu'un arbitre, un acteur ou le dépêcheur sachent où se tient un homme —
c'est-à-dire que la position se CALCULE et ne se stocke pas, ce que
`scripts/temps/presence.py` annonce en tête de fichier depuis toujours.

## Ce qui est vrai aujourd'hui

`etat/presence.json` porte deux choses. Une pile d'EXCEPTIONS datées, et un bloc
`resolu` qui est un cache : `scripts/scene/flux.py` l.928 le dit en toutes
lettres — « il vaut pour la date qu'il porte, et il est refait à chaque poussée ;
s'il manque, **ou si sa date n'est pas la bonne**, on retombe sur `presence` ».

La seconde moitié de cette phrase n'a jamais été écrite côté lecteurs. Quatre
d'entre eux ouvrent `resolu.gens` et n'en regardent jamais la date :

- `scripts/agents/depeche/brief.py:374` — `salles_peuplees()`, donc
  `dans_la_salle()` : **qui est dépêché dans une pièce** ;
- `scripts/agents/depeche/brief.py:404` — `positions()` : les mètres de chacun ;
- `scripts/agents/depeche/brief.py:446` — `dans_le_rayon()` : **le rayon de dix
  mètres**, qui décide qui entend quoi ;
- `scripts/agents/depeche/brief.py:322` — `dossier_journee()` : la salle d'un
  homme et les gens autour de lui.

Et un cinquième, `scripts/agents/activation/dossier.py:151`, que j'ai corrigé ce
jour (il recalcule quand le cache a trop vieilli).

Ironie du dossier : ces quatre-là portent en commentaire *« On ne lit pas
`presence` brut : c'est le déclaratif, `resolu` est ce qui tient compte des
déplacements »*. La précaution est juste et elle a été prise ; c'est le fait que
le cache VIEILLIT qui n'a été pris nulle part.

## La preuve, mesurée à la main le 129.4.5

- `etat/monde.json` l.2-7 : le monde est au **129.4.5, minute 540**.
- `etat/presence.json` l.474-480 : `resolu.date` est au **129.4.4, minute 540**.
- Écart : **1440 minutes. Un jour entier**, servi tel quel.

Et le détail qui fait la différence avec le cas dont on m'a saisi : dans ce même
bloc, l.872-877, `rulf-corne` figure « quai, arrêté, source: **scene** ». Au
moment où le cache a été calculé (le 4e à 540), son exception du 4e minute 424
tenait encore — 424 + 240 = 664 > 540. La ligne est donc née vraie et a vieilli
fausse, **sans que rien ne la marque**, et avec l'air le plus autorisé du
fichier : `source: scene`, dans le bloc résolu.

## Pourquoi ce n'est pas la même chose que le verrou qu'on m'a soumis

On m'a demandé si la LIGNE BRUTE devait dire sa propre péremption. Réponse : oui,
et je l'ai faite (voir plus bas). Mais **cela n'aurait pas sauvé l'arbitre du
4e.** S'il avait fait le geste plus correct encore — lire `resolu` au lieu de la
ligne brute, comme fait tout le code — il aurait lu exactement le même fait mort,
mieux habillé. La ligne brute périme ; le cache, lui, ne périme pour personne.

## Ce qui le lèverait

Que les quatre lectures de `brief.py` passent par
`presence.resolu_de(paquet)` — écrit ce jour dans `scripts/temps/presence.py`,
rend `(gens, retard_minutes)` et rend `{}` au-delà d'un quart — puis retombent
sur `presence.resoudre()`, comme `dossier.py` le fait désormais.

Je ne l'ai pas fait moi-même, et le motif est écrit pour qu'on ne me le reproche
pas comme une paresse : je n'ai eu **aucune exécution accordée** ce jour (comme
le 4e), donc aucune recette. Rendre `{}` au dépêcheur, c'est risquer de ne
dépêcher personne ; je ne pose pas ça en aveugle dans la boucle qui fait vivre le
château. Ça se fait avec un test qui tourne, en une demi-heure.

## Ce que j'ai fait ce jour, et son état

1. `scripts/temps/presence.py` — `annoter_peremption()` : la ligne brute se
   dénonce (`perime: true`), on n'efface pas. Jamais posée sur un joueur ni sur
   une ligne datée du futur. **ÉCRIT, NON EXÉCUTÉ.**
2. `scripts/temps/presence.py` — `resolu_de()` : la garde du cache.
   **ÉCRIT, NON EXÉCUTÉ.**
3. `scripts/scene/flux.py` l.952 — l'annotation est posée à l'écriture, sous
   `try/except` comme le calcul de `resolu` juste à côté : si elle casse, la
   poussée continue et le fichier reste ce qu'il était. **ÉCRIT, NON EXÉCUTÉ.**
4. `scripts/agents/activation/dossier.py` — cache vieilli ⇒ `resoudre()`, avec
   repli sur l'ancien comportement si le calcul lève. **ÉCRIT, NON EXÉCUTÉ.**

Vérifié à la main, faute de pouvoir l'exécuter :
- `resolu_de` sur les données du jour : retard 1440 > 240 ⇒ rend `{}`, `dossier.py`
  recalcule. ✓
- `annoter_peremption` sur `rulf-corne` : 424 + 240 = 664 ≤ 1980 (le 5e à 540
  ramené au 4e) ⇒ `perime: true`. ✓
- sur `rhaenyra` : joueur (`resolu` la donne `source: scene`, ce que seul le
  chemin PJ produit) ⇒ non marquée. ✓
- sur `nicolas-reynolds` : `source: routine` dans `resolu`, donc pas un PJ pour
  `ou_est()` ⇒ marquée, et c'est juste, sa ligne est du 3e.
