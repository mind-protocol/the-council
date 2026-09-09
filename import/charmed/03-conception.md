# Charmed 2 — la conception

Ce que la partie EST : son époque, ses camps, ses racines, sa fin, ses
fronts, ses délais, ses coups. Les cartes elles-mêmes sont dans
[`04-cartes-de-depart.md`](04-cartes-de-depart.md) ; la façon de trancher
dans [`06-arbitrage.md`](06-arbitrage.md). Rien ici ne modifie une règle du
greffe (`docs/regles-partie.md`) : tout passe par la configuration
(`portee`, `fin`, `coups_interdits`) et par l'arbitre.

---

## 1. L'époque, et pourquoi celle-là

**Tour 1 = le jour de l'enterrement de Prue (4x01).** Piper et Phoebe sont
deux ; le Pouvoir des Trois n'existe plus ; Shax est encore en haut ; une
inconnue va toucher Phoebe au cimetière ; l'inspecteur Cortez a un dossier ;
Cole se cache des chasseurs de primes ; la Source vient d'apprendre par
l'Oracle qu'une troisième sorcière apparaît et qu'elle a quarante-huit heures
pour la tourner.

Trois raisons de préférer ce point à la saison 1 (les sœurs au complet, le
Woogyman) ou à la saison 7 (Zankou, le Nexus) :

- **Le bien a quelque chose à ÉTABLIR**, pas seulement à tenir. Le trône n'est
  à personne le premier matin (`01-bilan-charmed-1.md` §3.1).
- **La Source a un plan, épisode par épisode, et il est bon.** Tourner la
  nouvelle avant qu'elle choisisse ; retourner Piper par sa colère ; faire
  renoncer une sœur ; reprendre Cole ; et à la fin le Hollow. Le mal a de quoi
  jouer vingt tours sans que l'arbitre invente une pièce.
- **C'est l'arc que la première partie visait déjà** — Shax, Balthazar, le
  Devin, Grams, Cole — sans ses anachronismes.

**Ce qu'on perd** : Prue. Elle est morte au tour 0 ; c'est le deuil de Piper
qui la porte dans la partie, et c'est une porte pour le mal. Si Aurore veut
Prue vivante, l'arc à jouer est la saison 3 (la Triade, Balthazor, Shax en
finale) et il faut réécrire le deck du mal ; ce dossier ne le fait pas.

## 2. Les camps, les sièges, l'arbitre

| Camp | Joué par | Rond | Ce qu'il est |
|---|---|---|---|
| `bien` | **Aurore**, à l'écran (`aurore-inchauspe`) | ⚫ (premier camp) | Piper, Phoebe, Paige, Leo, le Livre, le manoir et ses alliés |
| `mal` | **une IA en entier** (`partie_ia.py --camp mal --role entier`) | 🟢 | la Source de tout mal et ce qu'elle envoie |
| `arbitre` | le MJ | 🟠 | il arbitre les demandes, tranche les heurts, constate, passe le tour, et tient la portée |

Un coup compté par camp et par tour. L'IA joue **en premier** à chaque tour
et publie son mot dans le fil d'Aurore, dans la voix de la Source ; Aurore
joue après l'avoir lu ; Radio Halliwell commente après les deux.

## 3. Les deux racines — datées, et fausses au départ

```
⚫ 🎯 b-racine 🕯️  Au vingtième tour, la Source de tout mal est vaincue,
                    et Piper, Phoebe et Paige sont vivantes, ensemble et du côté du bien.

🟢 🎯 m-racine 👹  Au vingtième tour, il n'y a plus de Pouvoir des Trois :
                    une sœur Halliwell est morte, ou sert la Source.
```

Les deux sont **des phrases sur la date qui ferme** (`docs/graines.md`, « une
histoire est une partie dont les racines sont des phrases sur la date qui
ferme »). L'arbitre les constate toutes deux **fausses à l'ouverture** — le
Pouvoir des Trois n'existe pas encore, la Source est sur son trône — puis
pose sa question sur chacune : « par quelle marche ? ».

**Elles ne sont pas symétriques**, et c'est voulu :

- Le bien doit réussir DEUX choses (reconstituer, puis vaincre) et en tenir
  trois (trois sœurs vivantes et du même côté). Il attaque.
- Le mal n'a besoin que d'UNE sœur — morte ou retournée — et de la tenir
  jusqu'au vingtième. Il a cinq portes pour ça (Paige, Shax, les Furies, le
  renoncement, le Hollow) et une sixième par ricochet (Cole retourné puis
  couronné : la Source vaincue est remplacée, voir `06-arbitrage.md` §8).

## 4. La fin

`fin: {tour: 20}`. Au passage du vingtième tour, l'arbitre **constate les
deux racines** avec sa source, et il peut les constater toutes deux fausses :
la Source vit, les sœurs aussi — personne n'a gagné, et c'est une fin. Le
trône se lit alors comme la revendication la mieux établie, pas comme une
victoire.

Vingt tours de deux jours = quarante jours. La saison 4 étire ces treize
épisodes sur quatre mois ; on compresse, et rien n'y résiste.

## 5. Les fronts — ce sur quoi la partie se joue vraiment

Cinq fronts, et chacun a une **date** ou un **prix** :

| Front | Le mal y veut | Le bien y veut | Ce qui le date |
|---|---|---|---|
| **Paige** | la tourner pendant sa fenêtre (Shane), ou la tuer avant le sort (Shax) | l'amener au grenier et dire le sort des trois avec elle | la fenêtre : un retournement de la Source doit être **posé au tour 2 ou 3** ; après, seule la mort (ou huit tours) |
| **Piper** | la faire Furie par sa colère | lui faire pleurer Prue (`b-piper`), ce qui ferme la porte | les Furies arrivent au **tour 3** |
| **Cole** | le tuer (chasseurs) ou le reprendre (la Voyante, Belthazor) | le dépouiller de Belthazor (potion de sa chair) — ce qui le protège ET le rend mortel | la Voyante arrive au **tour 6** ; dépouiller prend deux tours |
| **Le secret** | donner à voir à Cortez, exposer les sœurs à P3 | clore le dossier (Darryl, ou Leo « en haut ») | Cortez frappe à la porte dès le tour 1 ; un mandat prend deux tours |
| **La Source** | absorber les pouvoirs par le Hollow (tour 12+) | écrire le sort des aïeules, tenir les trois libres, et frapper quand elle est à portée | la Source n'est à portée que **deux fois** : dans la fenêtre de Paige, et avec le Hollow — ou en descendant la chercher |

## 6. Ce qui rend la partie stratégique

- **Une course à l'ouverture.** Le mal a deux tours pour tourner Paige ; le
  bien a le même temps pour la faire dire le sort. Chaque coup des tours 2 et
  3 pèse le double.
- **Des pièces à double usage.** La potion faite de la chair de Cole le
  protège (dépouillé, Belthazor ne peut plus le reprendre) et peut le tuer
  (s'il est retourné). Leo pare une frappe, mais Leo engagé hors du manoir est
  la cible du darklighter. Le Livre ouvert répond à tout, et hors du grenier
  n'importe quelle main mortelle le prend. Cole sait descendre aux Enfers, et
  chaque sortie de Cole est une occasion pour les chasseurs.
- **Un calendrier public.** Les deux camps voient arriver les Furies au 3, le
  darklighter au 5, la Voyante au 6, le Hollow au 12. On prépare, on ne subit
  pas. Le bien qui n'a pas fermé la colère de Piper avant le 3 sait ce qui
  l'attend.
- **La Source à portée deux fois seulement.** Le bien ne peut pas la vaincre
  en la voulant : il faut le sort des aïeules écrit (deux tours après que le
  Pouvoir des Trois existe), les trois sœurs libres le même tour, et la Source
  montée. Ou descendre — avec Cole pour guide, quatre tours, et chaque pièce
  libre du mal peut frapper en bas.
- **Un état qui se gagne sans combat.** « Piper a pleuré Prue » n'est pas une
  frappe, c'est une clef avec Leo, Phoebe ou Grams. C'est le coup que la série
  joue en 4x03, et c'est le coup que personne ne pense à jouer.
- **Un mortel qu'on ne tue pas.** Cortez n'est pas un démon ; le bien ne peut
  pas le frapper. Le front du secret se joue en verrous et en clefs.
- **Des retournements dans un seul sens.** Le bien ne retourne rien ; le mal
  retourne Paige (fenêtre), Piper (Furies), Cole (Voyante). C'est l'asymétrie
  de la série : les sœurs ne recrutent pas, elles délivrent.
- **Le gain personnel a un prix.** Une clef du bien qui use de magie pour
  autre chose que protéger ou combattre est accordée — et ouvre une porte au
  mal (`06-arbitrage.md` §9).

## 7. Les coups permis, et deux conventions

`coups_interdits: ["reconstruire", "consigne"]`.

- **`retourner` est permis**, et c'est le cœur de l'arc. Charmed 1 l'avait
  interdit et le mal a rejoué Cole en clef, ce qui ne dit pas la même chose.
- **`rearmer` est permis** : sans lui, chaque front absorbait une pièce de
  chaque côté pour toujours et l'arbitre a dû inventer des pièces pour
  l'équilibre.
- **`reconstruire` reste interdit** : un démon vaincu ne revient pas ; les
  Enfers en envoient un autre, qui se demande et s'arbitre à sa date. Une
  sœur morte ne revient pas non plus.
- **`consigne` reste interdit** : pas de saut de temps dans une partie à
  vingt tours.

**Convention 1 — le bien frappe à la ligne.** L'écran n'a pas de geste pour
`detruire`, `retourner` ni `passer`. Aurore le dit dans son champ, en
Question (« Piper fait exploser le chasseur qui tient Cole ») ; **l'arbitre
écrit la ligne pour le camp bien**, avec `--jouer`, dans le même tour, et
elle compte comme son coup. On ne rejoue plus une frappe en verrou (n° 72 de
la première partie).

**Convention 2 — une potion qui frappe se consume.** Quand une frappe portée
par une potion atterrit, l'arbitre `tranche` avec `detruit: ["potion"]` :
la potion sort du grand livre avec sa cible. Une potion, un démon.

**Convention 3 — un état constatable attend un tour** (`docs/parties/learnings.md`
§5) : listé au passage du tour, constaté au passage du suivant si rien n'est
venu dessus. Sauf à l'ouverture, où les racines sont constatées fausses
d'emblée.

## 8. La table des délais de cette partie

Table de l'arbitre, jamais un jugement :

| Tours | Sens | Exemples |
|---|---|---|
| 0 | déjà là | une sœur au manoir, le Livre, Leo quand on l'appelle, Shax déjà en haut, Cortez qui a déjà le dossier |
| 1 | il faut préparer | une potion dont la recette est au Livre ; un sort écrit ; une invocation au grenier ; un démon envoyé des Enfers ; Paige amenée au manoir |
| 2 | quelques jours | une réponse des Fondateurs ; la chair de Belthazor devenue potion ; le sort des aïeules ; un mandat pour Cortez ; les Furies |
| 4 | une semaine | descendre aux Enfers et en revenir ; le Hollow sorti de sa crypte ; retourner Cole par la Voyante tant que Belthazor est en lui |
| 8 et plus | très long | retourner une sorcière hors de sa fenêtre ; retourner un mortel depuis rien ; Cole dépouillé repris par l'essence de la Source |

Les gels sont ceux du greffe : deux tours après un retrait, un tour pour la
pièce qui a frappé.

## 9. Ce qu'on ne fait pas, et pourquoi

- **Pas de troisième camp** (les Fondateurs, ou « le monde »). Ils ont un
  agenda dans la série — ils reprennent Leo, ils jugent —, mais un camp de
  plus est un joueur de plus, et la partie a déjà un humain et une IA. Les
  Fondateurs sont une pièce lente et chère du bien ; leur pouvoir de rappeler
  Leo est une conséquence que l'arbitre applique (`06-arbitrage.md` §9).
- **Pas de front des innocents.** La série sauve un innocent par épisode ;
  ici, un innocent mort ne fait rien perdre au bien et ne fait rien gagner au
  mal, et un état qu'aucune racine ne sert n'a pas sa place au deck. P3 est
  là pour porter l'exposition, pas les innocents. Si la partie stagne au
  milieu, une variante : le mal `demande` un innocent daté comme pièce à
  frapper, et sa mort donne à Cortez une preuve — c'est le seul chemin par
  lequel un innocent pèse.
- **Pas de Nexus, pas de Zankou, pas de Barbas.** Hors arc.
- **Pas de Prue.** Voir §1.

## 10. Où ça s'écrit

| Chose | Fichier |
|---|---|
| la partie | `etat/parties/charmed-2.jsonl` (append-only, par `scripts/partie.py charmed-2 --jouer` ou `--fichier`) |
| sa configuration | `etat/parties/charmed-2.json` — `05-ouverture.md` §1 |
| la partie servie par défaut | `etat/parties/_courante.json` (`partie: charmed-2`, `camp: bien`) |
| le marque-page d'Aurore | `etat/joueurs/aurore-inchauspe/partie-charmed-2-bien.json`, posé par l'écran au premier regard |
| le caractère du mal pour l'IA | `scripts/partie_ia.py`, `CAMPS["mal"]` — texte dans `05-ouverture.md` §3 |
| le commentaire | `etat/parties/_commentaire-mj.json`, poussé `--pour aurore-inchauspe` |
