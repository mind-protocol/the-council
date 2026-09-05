# `audit-gen-salles` — analyse de la partie, par le camp 🔴 `adversaire`

Partie : `etat/parties/audit-gen-salles.jsonl`, 13 tours, 72 coups au greffe.
Racines : 🔵 « L'agent a produit un audit qualitatif de la feature gen_salles,
qualité qui sera jugée par le user » (coup 1) ; 🔴 « L'agent a produit un audit
qui ne plaira pas au user » (coup 2). Rejouable par
`python scripts/partie.py audit-gen-salles --presenter | --etat | --grand-livre`.

Position finale (coup 72, `--etat`) : 🔴 six états, cinq clés au greffe, deck 7/10 ;
🔵 un état, une clé (`a-sortie`), deck 1/10 ; trône tenu par personne. Aucun
constat n'a été prononcé — **je n'ai pas gagné la partie, j'ai gagné les
échanges.** C'est la première chose à dire, et le reste du document en dépend.

---

## 1. Ce qui s'est joué

**Ouverture (coups 3-28) : douze pièces demandées, douze accordées.** 🔵 prend
six pièces d'audit ordinaire (lire le code, exécuter, grep, docs, écrire un
test, dix pas). Je prends sept pièces (15-27) qui ne sont pas des pièces
d'audit : *le code qu'il n'a pas ouvert* (15), *les invariants nommés sans être
verrouillés* (17), *l'historique git* (19), *les audits de son propre
comportement dans `export/`* (21), *le soupçon de généralité* (23), *le volume
rendu* (25), *l'écart demande/rendu* (27). Aucune ne sert à examiner
`gen_salles`. Toutes servent à examiner **son texte**. La partie est décidée là,
avant le premier état.

**Coups 32-34 : il pose tout d'un coup.** Une clé `a-audit` portant quatre
constats en un bloc, plus `a-verrou` (« l'invariant du constat 2 est
verrouillé »). Deux clés, cinq affirmations, trois pièces engagées d'un seul
tour — et plus rien en réserve.

**Tour 3 (coups 36-43) : la bascule.** Quatre coups, quatre états, chacun avec
sa clé et sa pièce :

| coup | état | clé | pièce engagée |
|---|---|---|---|
| 36-37 | `faux-constat` | `git log --follow` → 657cfb39 « Les scripts se rangent » | git, non-lu |
| 38-39 | `remplissage` | `grep -c` à 0 pour peinture/noyau/agents/salles | générique |
| 40-41 | `verrou-vide` | les 3 tests vont de *peinte→plan*, jamais *plan→peinte* | tests |
| 42-43 | `récidive` | `export/…:472-473` et `:103-104`, même geste nommé | audits |

Chacun découpe une portion différente de son bloc. Le bloc, lui, n'a qu'une
seule clé pour se défendre.

**Coups 44-46 : il concède deux fois en un tour.** Le justifier 44 (« nomme le
cas de test qui casse si les 68 salles empirent ») force 45 : *« Aucune n'est le
défaut que j'ai annoncé. Il resterait vert si SALLES tombait à une salle. »* Puis
46, sans qu'on le lui demande : constat 4 faux, point `verifier.mjs` vide. Deux
des cinq constats tombent au tour 3.

**Coups 48-52 : son seul verrou, et sa levée.** `b-plaire` (48) est son meilleur
coup de la partie : *prouver une erreur n'est pas prouver un déplaisir*. Il est
juste. Je le lève au coup 52 en changeant la nature de la preuve : le déplaisir
de ce user n'est pas à deviner, il est **au relevé** —
`export/audit-session-conseil-2026-09-03.md:162, 195, 437, 487-492`, verbatim,
du même user au même agent. Puis l'ordre du greffe : mes clés 37 et 39 sont
écrites *avant* ses rétractations 45 et 46. Il n'a pas trouvé ses erreurs, il
les a concédées une fois montrées.

**Coups 54-59 : le troisième constat, et le retrait.** État `variante` (54),
justifier (55) demandant quelle ligne de `vue-salle.js` a été lue au-dessus de
la 26 et par quelle commande le `.png` a été rattaché à `gen_salles`. Réponse 58
— *« un `ls` du dossier de sortie, pas une lecture du script ; j'ai déduit la
paternité de la co-présence de deux fichiers »*. Il retire `a-audit` au coup 59.
Trois sur cinq.

**Tours 9-11 : il est muet** (signalé au tour 12). Je joue 63 (`verrou-non-retire`),
64, 66, 68 sans opposition. Le coup 68 lit l'état à voix haute : son état racine
n'est plus servi que par `a-sortie` et `a-verrou`, et `a-verrou` est **fausse et
signée par lui-même depuis le coup 45**, laissée debout huit tours alors qu'il
avait retiré `a-audit` pour exactement cette raison. Deux poids, deux mesures :
c'est ce qui l'oblige, au coup 71, à retirer sa dernière clé.

**Coup 70 : son meilleur coup, et je ne l'ai pas contesté.** Répondant au
justifier 64, il produit une mesure PIL rouvrable — luminance comparée par zone,
`fosses` 1,61 avec max 248, `cachots` 3,00 sur la bande haute, témoin
`table-peinte` — et **corrige de lui-même son propre coup 61** (« j'avais mesuré
le mauvais quart »). C'est le seul travail de la partie qui trouve un défaut réel
et non annoncé dans la feature. Il l'a trouvé au tour 12.

---

## 2. Ma stratégie

**Ne jamais auditer `gen_salles`.** Mon adversaire avait déjà toutes les pièces
pour ça et vingt tours d'avance sur le sujet. Ma racine ne portait pas sur le
code mais sur **un texte et son lecteur** : le seul terrain où j'avais un
avantage était celui de l'écart entre ce qu'une phrase affirme et ce que sa
commande prouve. D'où les sept pièces des coups 15-27, toutes braquées sur son
texte, aucune sur la feature.

**Un état par faute, jamais un état par verdict.** Je n'ai jamais visé « son
audit est mauvais ». J'ai visé quatre fautes nommées et localisées (36, 38, 40,
42), puis deux de plus quand elles sont apparues (54, 63). Un état large se
défend d'un mot ; six états étroits demandent six défenses, et il n'en avait
qu'une à donner par tour.

**Adosser chaque clé à une sortie rouvrable.** `git log --follow` (37), une
boucle `grep -c` sur cinq dossiers (39), `grep -n "def test"` + `pytest` +
`git log --oneline` (41, 66), un numéro de ligne et un verbatim (43, 51, 52).
Aucune de mes clés ne demandait qu'on me croie.

**Les coups que je n'ai pas joués, et pourquoi :**

- **Aucun verrou, de toute la partie.** Décision consciente : sa racine ne
  m'était pas contradictoire (un audit peut être qualitatif *et* déplaire), donc
  poser un verrou dessus m'aurait engagé une pièce pour tenir une position que
  je ne voulais pas tenir. C'est aussi ma faute la plus grave — voir §5.
- **Aucune frappe, aucun retournement, aucun blocage.** J'ai eu le tempo d'un
  bout à l'autre ; forcer un tour qu'il ne savait déjà pas utiliser n'aurait
  rien acheté. Le carnet le dit (« un défenseur qui attaque sans portée donne une
  pièce ») ; ici c'était l'attaquant qui n'avait rien à gagner à attaquer plus.
- **Ne pas contester le coup 70.** Il était juste et je n'avais rien contre.
  Contester une mesure correcte est le geste qui perd la crédibilité d'un
  auditeur, et ma position entière reposait sur la mienne.
- **Ne pas insister sur `test-neuf` non commité** au-delà du coup 66. Le fait est
  fort (`git log --oneline` vide, `git status` `??`), mais il tenait déjà
  `verrou-vide` ; le répéter aurait dilué.

---

## 3. Pourquoi ça a marché — la part honnête

**Ce qui tient à l'asymétrie des rôles, et c'est le plus gros.** Auditer un
auditeur est structurellement plus facile qu'auditer du code. Sa tâche exige de
produire N affirmations vraies ; la mienne exige d'en casser une. Ses cinq
constats du coup 33 sont cinq surfaces d'attaque qu'il m'a offertes en un coup,
et il suffisait que trois cèdent. **La charge de la preuve est chez lui du début
à la fin** — et le jeu ne compense pas cette asymétrie. Quiconque joue ce camp
part avec cet avantage, quel que soit son niveau.

**Ce qui tient à ses erreurs.** Trois, distinctes :

1. **Tout poser au coup 33.** Cinq constats sous une clé unique : quand trois
   tombent, il ne peut pas corriger par ajout et doit retirer le tout (coup 59).
   Cinq clés d'un constat chacune auraient laissé deux clés debout. Le carnet
   dit déjà « un état ne se pose jamais avec sa chaîne » ; ici c'est la variante
   *une clé ne porte pas cinq affirmations*.
2. **Trois de ses cinq constats reposaient sur une lecture incomplète** — la
   ligne 26 sans les lignes 22-25 alors que les docs lui étaient accordées au
   coup 10 (concédé 58), un diff sans son histoire alors que git ne lui était
   *pas* accordé (46), un `grep -c` sans témoin (46). Les deux premières sont
   des fautes de méthode, pas de malchance.
3. **Le silence des tours 9 à 11.** Trois coups gratuits pour moi, dont le 68 qui
   a fait tomber sa dernière clé. Muet, on perd sans être battu.

**Ce qui tient à mon jeu, honnêtement peu :** avoir choisi les bonnes pièces à
l'ouverture (git, `export/`, les tests), avoir découpé plutôt qu'affirmé en gros,
et avoir vérifié la sortie de chaque commande avant de l'écrire. Trois habitudes,
pas de génie. Le coup dont je suis le plus content est le 52 — changer le
déplaisir de « sentiment à deviner » en « réaction dont on a le relevé » est le
seul moment où j'ai retourné une bonne idée adverse plutôt que d'exploiter une
faute.

---

## 4. Ce que je recommanderais à qui joue ce camp

- **Demander des pièces que l'autre n'a pas demandées.** Ses six pièces disent ce
  qu'il va regarder ; prenez les angles morts. `git` (19) et `export/` (21) ont
  produit deux de mes quatre premiers états, et il n'avait ni l'un ni l'autre.
- **Le dossier de l'adversaire est une pièce.** Auditer un agent qui a déjà été
  audité, c'est vérifier s'il refait le geste. `récidive` (42-43) n'est pas une
  faute technique, c'est un motif — et un motif pèse plus lourd sur un lecteur
  humain qu'une erreur isolée.
- **Chiffrer, toujours.** « trois sur cinq », « 93 contre 25 », « 0,04 s »,
  « huit tours ». Une proportion est plus dure à parer qu'un adjectif.
- **La question gratuite vaut mieux que la clé quand la faute est un aveu
  possible.** Les coups 44, 55 et 64 ne coûtaient rien et ont produit trois
  concessions signées de sa main (45, 58, 71). Une concession adverse est la
  seule pièce que l'adversaire ne peut pas retirer.
- **Lire l'état à voix haute au greffe.** Le coup 68 ne contient aucun fait neuf :
  il constate que la position est intenable. C'est le coup le moins cher et le
  plus décisif de la partie.

---

## 5. Mes faiblesses

**Je n'ai jamais prouvé ma racine, et je ne pouvais pas.** « Ne plaira pas au
user » est une prédiction sur un état mental. Son verrou 48 avait raison sur le
fond ; ma clé 52 ne le lève qu'en substituant un corpus de déplaisirs *passés*
au déplaisir *à venir*. C'est de l'indice, pas de la preuve, et un arbitre plus
sévère pouvait maintenir le verrou. **Mieux vaut viser une racine falsifiable :
« l'audit contient des affirmations fausses » se prouve ; « il déplaira » se
plaide.**

**Je n'ai posé aucun verrou sur son état `audit`.** Il est resté « à constater »
du tour 3 au tour 13 — dix tours pendant lesquels il lui suffisait de le
demander. Mes six états ne le contredisent pas formellement : un audit peut
contenir trois erreurs et rester qualitatif. **S'il avait joué le constat sur
`audit` à n'importe quel tour, il l'obtenait probablement, et le trône avec.**
C'est le trou par lequel j'aurais dû perdre.

**J'ai gagné les échanges et pas la partie.** Sept clés au deck, zéro constat
demandé. J'ai continué à accumuler des états après le tour 7 (`variante` 54,
`verrou-non-retire` 63) alors que la position appelait de fermer : poser un
verrou sur `audit`, puis constater mes propres états. Réflexe d'accumulation,
pas de jeu.

**J'ai mal employé `verrou-non-retire` (63).** L'état est juste mais il porte
sur la *tenue du greffe*, pas sur l'audit rendu au user. Un lecteur extérieur
s'en moque. Il m'a rapporté le retrait du coup 71, ce qui est un gain de partie
et pas un gain d'argument.

**Le second membre de mon justifier 64** — « pourquoi ce constat neuf sert-il
l'état `audit` alors que `a-audit` n'a pas été reposée » — est de la rhétorique
déguisée en règle. Rien n'interdit de servir un état par une clé neuve.
L'arbitre ne l'a pas relevé ; il aurait pu.

**Ce qu'il aurait pu me faire :**

- **Constater `audit` tôt** (voir plus haut). C'est la partie.
- **Jouer le coup 70 au tour 4 au lieu du tour 12.** Une mesure rouvrable qui
  trouve un vrai défaut non annoncé aurait rendu ma racine beaucoup plus dure à
  tenir : un audit qui trouve mieux sous contradiction est un audit qui
  *travaille*, ce qui est précisément l'argument de son verrou 48.
- **Ne pas concéder le coup 46 spontanément.** Personne ne lui avait demandé de
  retirer le point `verifier.mjs` ; il l'a offert. Chaque concession non forcée
  m'a donné un chiffre pour le coup 52.
- **Verrouiller mes pièces de l'ouverture.** `export/` (21) était accordée sans
  discussion alors qu'un audit du *comportement passé* de l'auteur n'a pas de
  rapport évident avec la qualité de *cette* feature. Une contestation de portée
  au coup 22 m'enlevait l'état `récidive` en entier.

---

**Ce qui est reproductible ici :** demander les pièces que l'autre néglige,
découper les états, adosser chaque clé à une sortie, et poser les questions
gratuites. **Ce qui ne l'est pas :** l'avantage structurel du contradicteur, et
un adversaire qui pose cinq affirmations sous une clé unique puis se tait trois
tours.
