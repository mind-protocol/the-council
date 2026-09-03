# Les règles de la partie — référence complète

Ce fichier est le livre de règles du jeu de position appelé « la partie »
(le conseil de guerre joué contre quelqu'un). Il ne dit pas comment la
montrer : pour cela, voir [`partie.md`](partie.md) (l'écran). Le manuel du MJ,
[`scripts/agents/prompts/mj-partie.md`](../scripts/agents/prompts/mj-partie.md),
porte les mêmes règles avec leur motivation.

**Source de vérité : le greffe.** Quand ce fichier, le manuel et
`scripts/noyau/partie_greffe.py` / `partie_validite.py` se contredisent, c'est
le code qui joue. Les écarts connus entre le manuel et le code sont listés à la
fin (annexe B). Rédigé le 3 septembre 2026 sur HEAD `85b7bb15`.

---

## 1. Ce qu'est une partie

- Un jeu de pièces logiques entre **des camps** — autant que la partie en
  nomme, chacun tenu par un joueur, une tête dépêchée ou le MJ — et un rôle
  hors camp, 🟠 l'**arbitre**, dont le nom est le seul réservé. Les exemples
  de ce fichier viennent de la Danse, à deux camps `noir` et `vert`.
- Rien ne se résout par un calcul de durée ni par un jet. Tout se résout par
  deux questions : **as-tu une pièce libre pour répondre**, et **as-tu écrit
  le chemin**.
- Le plateau est à **information complète** : la position entière, les deux
  camps, pièces engagées ou non, est servie aux deux joueurs. Le brouillard
  reste entier dans la fiction ; il ne s'applique pas au plateau.
- Une partie est un fichier **append-only**, `etat/parties/<id>.jsonl`, une
  ligne par coup, jamais réécrite. La position se **replie** depuis les lignes.
  Une correction est un coup de plus, jamais une ligne modifiée.

---

## 2. Les objets

| Signe | Objet | Définition | Qui le pose |
|---|---|---|---|
| 👑 | **le trône** | l'objet racine, vu de chaque côté par une **racine par camp** : l'état de ce camp qui ne sert aucun autre. Le trône est au camp dont la racine a été constatée vraie en dernier ; à personne tant que rien n'est constaté | chaque camp pose la sienne à l'ouverture |
| 🎯 | **un état** | ce qui doit être vrai, constatable (« la porte de la Rivière est acquise »). Jamais une action. Un état peut en **servir** un autre (`sert`) : les états forment un arbre sous le trône | un camp, par `viser` |
| 📦 | **une ressource** (pièce) | tout ce qu'une clé peut engager : un corps, une bête, une troupe, un lieu tenu, un objet, une bourse, un canal. **Les personnes comprises** | un camp, par `demander`, puis l'arbitre |
| 🔒 | **un blocage** | ce qu'un camp oppose à un état, un maillon, une clé ou une destruction d'un autre camp, avec la pièce qui le produit | un autre camp, par `bloquer` |
| 🗝️ | **une clé** | ce qui lève un ou plusieurs blocages, en engageant des pièces ; ou, sans blocage à ouvrir, ce qui **réalise** un état (`sert`) | un camp, par `lever` |
| ⚔️ | **un maillon** | une action : qui, avec quoi, quel résultat. Les maillons réalisent une clé, une destruction ou un blocage | un camp, par `agir` |
| 💥 | **une destruction** | une menace datée sur une ressource adverse ; réalisée, la ressource sort du grand livre | un camp, par `detruire` |
| 🔄 | **un retournement** | une destruction qui ne tue pas : réalisée, la ressource **change de camp** | un camp, par `retourner` |
| 📋 | **une consigne** | ce que fait une pièce si elle est visée pendant un saut | un camp, par `consigne` |
| — | **le grand livre** | la liste des ressources, avec pour chacune : camp, lieu, nombre, tenant, tour d'arrivée, gel, ce qui l'engage, détruite ou non, source | dérivé des lignes |
| — | **le deck** | les états qu'un camp met en jeu, **dix au plus**. Le reste du plan dort et n'est touché par aucun coup | — |

**Un id n'a qu'un objet.** États, blocages, clés, maillons, destructions et
retournements partagent un seul espace de noms : un id déjà pris est refusé.
Une ressource a son propre espace (le grand livre) ; un id de ressource déjà
au grand livre et non détruite est refusé.

### 2.1 Les états d'une ressource

Une ressource est, à tout instant, dans un et un seul de ces états :

| État | Sens | Utilisable ? |
|---|---|---|
| **en attente** | demandée, pas encore arbitrée | non |
| **en route** | accordée, `arrive_tour` > tour courant | engageable (réservée), mais la clé n'est **prête** qu'à son arrivée |
| **libre** | arrivée, engagée par rien, pas gelée | oui |
| **engagée** | engagée par une clé, un blocage, une destruction ou un retournement | par cet objet seulement |
| **gelée** | `gel_jusqu` > tour courant | non, jusqu'au tour dit |
| **détruite** | sortie du grand livre | non ; `reconstruire` si la chose se reconstruit |

Une ressource engagée l'est **jusqu'à ce que ce qui l'engage soit retiré,
tombé, tenu, refusé ou réalisé**. Une deuxième clé qui la veut est « sans
ressource ».

### 2.2 Les états d'une clé

**valide** (posée, rien ne la suspend) · **prête au tour N** (une de ses pièces
est en route) · **suspendue** (un `justifier` attend sa chaîne) · **sans
ressource** (une pièce engagée manque : gelée, détruite, en attente, prise) ·
**tenue** (tous ses blocages sont tombés, ou son état est constaté vrai : elle
a fait son office, ses pièces sont rendues) · **retirée**.

### 2.3 Les états d'un blocage

**tient** · **prêt au tour N** · **suspendu** (justifié, maillon non écrit) ·
**levé** (une clé valide l'ouvre) · **tombé** (retiré, refusé pour portée, sa
pièce partie, son état constaté vrai, ou la destruction qu'il protégeait
finie).

---

## 3. Les coups

Un coup est une ligne. Champs communs : `n` (rang, posé par le greffe),
`tour`, `camp` (le nom du camp, ou `arbitre`), `coup`, `texte` (une phrase,
verbe d'abord).

### 3.1 Les coups des camps

| Coup | Cible | Effet | Coût | Compte pour « un coup par tour » |
|---|---|---|---|---|
| 🎯 `viser` | — | pose un état dans son deck. Avec `arrive_tour`, l'état est daté : il tient sa place d'avance et n'entre au deck qu'à ce tour | un coup, et une place du deck | **oui** : un état se pose un par un, comme les autres pièces |
| 🃏 `sortir` | un état à soi, au deck | le sort du deck ; ses pièces restent engagées où elles sont | — | oui |
| 📦 `demander` | — | demande une ressource : `id`, `lieu`, `nombre`, `tenu_par` | rien tant que l'arbitre n'a pas parlé | non |
| 🔒 `bloquer` | un état, un maillon, une clé ou une destruction **d'un autre camp** | pose un blocage, avec la pièce qui le produit (`engage`) | la pièce, engagée | oui |
| 🗝️ `lever` | un ou plusieurs blocages adverses (`ouvre`), ou un état à soi (`sert`) | pose une clé qui les lève ; sans blocage, réalise l'état quand l'arbitre le constate | les pièces, engagées ; **au moins une** | oui |
| ⚔️ `agir` | une clé, une destruction ou un blocage **à soi** (`realise`) | pose un maillon : `qui`, `avec`, `texte`, `etat` (`a_faire` \| `faite`). Une seconde ligne sur le même id avec `etat` seul le met à jour. Le maillon écrit **lève la suspension** de sa cible | rien de plus que ce que la cible engage | oui, **sauf s'il répond à un `justifier`** (le greffe pose `repond`) |
| ❓ `justifier` | une clé, un blocage, une destruction ou un état **d'un autre camp** | exige la chaîne : la cible passe **en suspens** jusqu'à ce qu'un maillon soit écrit dessous (ou, pour une destruction, que l'arbitre accorde). **Une fois par pièce**, jamais deux | rien | non |
| 💥 `detruire` | une ressource adverse (`cible`) | pose une menace datée ; réalisée, la ressource est détruite et tout ce qu'elle tenait tombe | la pièce qui frappe, engagée, puis **gelée un tour** à la réalisation | oui |
| 🔄 `retourner` | une ressource adverse (`cible`) | même fenêtre, même parades, même arbitrage qu'une destruction ; réalisée, la ressource **passe au camp qui l'a retournée**, libre, et tout ce qu'elle tenait tombe | ce qu'on y met (`engage`) ; voir §4.4 | oui |
| 🗑️ `retirer` | une clé, un blocage, une destruction, un retournement ou une ressource **à soi** | le retire ; les pièces libérées sont **gelées deux tours** (`gel_tours` surchargeable) | deux tours à découvert | oui |
| 🔧 `reconstruire` | une ressource détruite à soi | la rend, **au tour + 2** (`revient_tour` surchargeable), engagée par rien | deux tours | oui |
| ➕ `rearmer` | une clé ou un blocage à soi qui tient encore | ajoute une pièce sans changer ni le texte ni la cible ; la clé devient « prête » au tour d'arrivée de la pièce ajoutée si elle est en route | un coup, pas de gel | oui |
| ⏸️ `passer` | — | ne joue rien | le tour | oui |
| 📋 `consigne` | des pièces à soi (`pieces`) | ce qu'elles font si elles sont visées pendant un saut | rien | non |

### 3.2 Les coups de l'arbitre

| Coup | Cible | Effet |
|---|---|---|
| ⚖️ `arbitrer` | un id (une demande, une destruction, une clé, un blocage) ; un numéro de ligne à défaut | **toujours avec `motif` et sa source** (numéro de pièce, fichier d'état, canon). Verdicts : `accorde`, `refuse`, `reporte`, `tranche`. Effets selon la cible, §3.3 |
| ✅ `constater` | un état | `verdict: vrai` ou `faux`, avec `motif`. Un état constaté vrai fait tomber les blocages posés dessus par d'autres camps et tient les clés qui le servent (pièces rendues sans gel). Sur une racine, il donne ou retire le trône |
| ❓ `justifier` | n'importe quel objet des deux camps | l'arbitre peut exiger la chaîne d'un état dès l'ouverture (« qui s'assied, et comment arrive-t-elle ? »), une fois |
| ⏭️ `tour` | — | passe le tour, §5 : arrivées, dégels, atterrissages, parades tenues, états datés, états constatables, camps muets, branches mortes |

### 3.3 Ce que fait chaque verdict

| Sur | `accorde` | `refuse` | `reporte` | `tranche` |
|---|---|---|---|---|
| une **demande** | la ressource entre au grand livre, corrigée (`lieu`, `nombre`, `tenu_par`), datée (`arrive_tour`, sinon le tour courant) | la ressource est effacée du grand livre | comme accorde, avec `arrive_tour` | comme accorde ; sert à réduire un nombre (« six cents, pas deux mille ») |
| une **destruction** ou un **retournement** | la portée est jugée bonne : la suspension tombe | la menace tombe ; la pièce qui frappait est rendue sans gel ; les blocages posés sur elle tombent | `arrive_tour` déplacé | la menace se réalise **maintenant**, partiellement si `nombre` (ce qui sort du grand livre) ; `detruit: [...]` nomme les pièces qui meurent aussi (heurt mutuel) |
| une **clé** | — | la clé est retirée, pièces rendues sans gel | — | — |
| un **blocage** | — | sans portée : il tombe | — | — |

---

## 4. Les règles de validité et de résolution

### 4.1 Engagement et ressources

1. **Une pièce engagée l'est jusqu'à ce que ce qui l'engage cesse** (retiré,
   tombé, tenu, refusé, réalisé). Une deuxième clé qui la veut est « sans
   ressource » ; le greffe refuse le coup avec la raison.
2. **Pas de ressource, pas de coup.** Une clé qui n'engage rien est refusée.
   Une pièce absente du grand livre, en attente, détruite, à l'autre camp,
   gelée ou déjà engagée ailleurs est une raison de refus, chacune nommée.
3. **Une pièce en route s'engage.** Elle est réservée dès ce tour, visible de
   l'adversaire ; la clé, le blocage ou la menace est **« prêt au tour N »**,
   celui où toutes ses pièces sont arrivées, et ne prévaut pas avant. Poser tôt
   est un engagement, pas une avance.
4. **Un maillon peut citer une pièce inconnue** (`avec`) : c'est un
   avertissement, pas un refus. Une pièce détruite est un refus.
5. **Une ressource accordée et engagée par rien deux tours après son arrivée
   est une branche morte.** Signalée au passage du tour, jamais punie. Une
   pièce qui a figuré une fois dans un `engage`, un `avec`, un `qui` ou une
   `consigne` n'est plus jamais signalée.

### 4.2 Blocages, clés, préséance

6. **Un blocage est posé par un autre camp, jamais sur soi.** Ce qu'on ignore
   de son propre plan n'est pas un blocage, c'est un trou. Ce qu'un blocage
   contrarie, c'est le camp de sa cible.
7. **Le défenseur tient par défaut.** Sur un maillon où les deux camps ont une
   pièce, rien ne bouge tant qu'un coup ne le tranche pas.
8. **Qui prévaut sur un blocage**, dans cet ordre :
   1. tombé → le camp de la cible ;
   2. suspendu (justifié, maillon non écrit) → le camp de la cible ;
   3. pas encore prêt (pièce en route) → le camp de la cible ;
   4. une clé l'ouvre : suspendue → le camp du blocage ; pas prête → le camp
      du blocage ; sans ressource → le camp du blocage ; sinon → **le camp de
      la clé** ;
   5. rien en face → le camp du blocage.
9. **Une clé dont tous les blocages sont tombés est tenue** : ses pièces
   reviennent libres, sans gel. Elle ne se réarme plus ; ce qu'on veut encore
   poser là se pose à neuf.
10. **Un blocage tombe avec sa pièce.** Pièce retirée ou détruite → le blocage
    tombe. Une clé dans le même cas devient « sans ressource » jusqu'à ce
    qu'on la réarme.
11. **Un blocage posé sur une destruction** (une bête entre la frappe et la
    colonne) la **pare**, et une parade tient **un tour** : au passage du tour
    où la frappe devait atterrir, elle attend ; au passage du suivant, si
    l'arbitre n'a pas tranché (règle 24), elle **tombe** — le défenseur tient
    par défaut. L'écran est rendu sans gel, la pièce qui frappait rentre gelée
    un tour.
12. **Un état constaté vrai** fait tomber ce qui le bloquait (les blocages
    des autres camps) et tient ce qui le servait (clés `sert`). Constater vrai un état
    dont un état-fils est encore au deck sans être constaté ni sorti est un
    avertissement, pas un refus : l'arbre n'est pas une conjonction.

### 4.3 La charge de la preuve

13. **Une clé ou un blocage sans maillon est une affirmation** : valide jusqu'à
    ce qu'un coup exige sa chaîne.
14. **Justifier ne punit pas et ne se répète pas.** Gratuit, hors compte, il
    suspend la cible ; la suspension tombe dès qu'un maillon est écrit dessous
    (`agir` avec `realise`), ou, pour une destruction, dès que l'arbitre
    accorde la portée. **Une pièce ne se justifie qu'une fois** dans toute la
    partie, quel que soit le camp qui l'a fait. **La réponse est aussi gratuite
    que la question** : le maillon écrit sur une cible suspendue porte `repond`
    et ne compte pas pour le tour.
15. **Un blocage suspendu ne prévaut plus** tant que son camp n'a pas écrit son
    maillon. C'est le symétrique exact de la clé.
16. **On n'exige pas sa propre chaîne.** Un camp ne justifie que ce qui est à
    un autre ; l'arbitre justifie ce qu'il veut.
17. **La portée se refuse sur pièce.** Une destruction ou un blocage que la
    pièce ne peut pas atteindre (présence, moyen, distance) est refusé en une
    ligne par l'arbitre. C'est le seul endroit où le « comment » remonte de
    force.

### 4.4 Destruction, retournement, heurt

18. **Une destruction est toujours une menace datée.** Posée au tour t, elle
    arrive au plus tôt en t+1 (`arrive_tour`, jamais avant l'arrivée de ses
    pièces) et **n'atterrit qu'au passage du tour suivant son arrivée**. Le camp
    visé a donc toujours un tour pour bloquer, justifier ou retirer.
19. **Une menace suspendue n'atterrit pas.** Elle attend, tour après tour, et
    sa pièce reste engagée, jusqu'au maillon ou à l'arbitrage. **Une menace
    parée attend un tour, puis tombe** (règle 11), sauf `tranche` de l'arbitre
    entre-temps.
20. **Une destruction qui atterrit sans arbitrage est totale.** Un heurt
    partiel se tranche **avant** le passage du tour ; après, la pièce est
    sortie du grand livre et un `tranche` tardif est refusé. Une correction est
    un coup de plus.
21. **Réalisée, une destruction** : détruit la cible (ou lui retranche
    `nombre`), retire sans gel les clés qu'elle portait, fait tomber les
    blocages qu'elle portait, rend la pièce qui frappait **gelée un tour**, et
    fait tomber les blocages posés sur la menace.
22. **Réalisé, un retournement** : la cible passe au camp qui a retourné,
    libre, avec `retourne_par` ; ce qu'elle tenait (clés, blocages) tombe. Ce
    qu'on y a mis revient **gelé un tour**, comme après une frappe, et ce qui
    parait le retournement tombe.
23. **Retirer une menace** rend sa pièce, gelée deux tours, et fait tomber ce
    qui la parait. **Retirer la ressource visée** fait tomber la menace ; la
    pièce qui frappait est rendue sans gel.
24. **Un heurt se tranche à la table, avec sa source** (`tranche`, avec
    `motif`), par le même ordre que l'arbitrage d'une ressource (§8) : ce que
    l'état sait, ce qu'un mécanisme produit, ce que l'arbitre comble à froid.
    Il n'y a pas de table de force. `nombre` chiffre ce qui sort du grand
    livre ; `detruit` nomme ce qui meurt des deux côtés.
25. **Reconstruire** vaut pour ce qui se reconstruit (une porte, des coques,
    des engins), pas pour un pendu. La ressource revient au tour + 2, engagée
    par rien.

### 4.5 Le deck et le trône

26. **Dix états par deck**, les états datés en attente comptant pour leur
    place, **les états constatés vrais n'en tenant plus** (ils restent dans
    l'arbre). Entrer ou sortir un état est un coup.
27. **Un deck peut être un calendrier** : des états datés (`arrive_tour`),
    chacun entrant au deck au tour de sa date. Un `arrive_tour` déjà passé est
    refusé.
28. **Le trône est au camp dont la racine a été constatée vraie en dernier** ;
    un constat faux sur cette racine le lui retire sans le donner à personne.
    À personne tant que rien n'a été constaté : c'est à l'arbitre de constater
    qui est assis à l'ouverture. Un état constaté vrai reste attaquable : un blocage peut se poser
    dessus, et il faut le reconstater.
29. **Le greffe liste, l'arbitre constate.** La ligne `tour` porte
    `constatables` : les états au deck, non constatés, dont tous les blocages
    sont tombés ou levés par une clé qui prévaut, ou qu'une clé valide sert
    sans que rien ne les bloque. Elle porte aussi `inactifs` : un camp qui n'a
    rien joué d'autre que passer sur les trois derniers tours. Ni l'un ni
    l'autre n'est un verdict.

### 4.6 Le rythme

30. **Un camp ne joue qu'un coup compté par tour** (`viser`, `sortir`, `bloquer`,
    `lever`, `agir`, `detruire`, `retourner`, `retirer`, `reconstruire`,
    `rearmer`, `passer`). Ne comptent pas : `demander`, `justifier`,
    `consigne`, un `agir` qui répond à un `justifier`, et tout ce qui vient de
    l'arbitre. **Le contrôle est gradué** :
    un second coup compté passe et se signale, il n'est pas refusé. C'est au MJ
    de tenir la règle et de savoir quand il la casse (l'ouverture).
31. **Seul l'arbitre** arbitre, constate et passe le tour.

---

## 5. Le temps

- **Le tour** est l'unité de jeu : un coup compté de chaque camp, dans l'ordre
  où les camps sont entrés dans la partie. **Un tour
  vaut deux jours du monde** (`JOURS_PAR_TOUR = 2`).
- **Au passage du tour** (`tour`), le greffe écrit sur la ligne ce qui arrive
  (`scripts/noyau/partie_tour.py`) : `arrivees`, `degeles`, `menaces` (qui
  atterrissent), `parees` (qui attendent), `parades_tenues` (dont la frappe
  tombe), `etats_arrives`, `constatables`, `inactifs`, `branches_mortes`. Puis
  il applique la même liste : entrée des états datés, atterrissage, chute des
  frappes parées depuis un tour, marquage des parades neuves.
- **Les délais d'arrivée**, table de l'arbitre, jamais un jugement :

| Délai (tours) | Sens | Exemples |
|---|---|---|
| 0 | déjà là | une garnison dans ses murs, une bête en ville, une bourse |
| 1 | il faut préparer | un dragon des terres de la Couronne ; une coque, une traversée ; un affrètement |
| 2 | quelques jours | une réponse de banneret ; une bête depuis Harrenhal ; un ost à deux jours de route |
| 4 | une semaine | un ost à huit jours de route ; un passage de la route du sel |
| 8 et plus | très long | Villevieille, le Nord, le Val ; retourner un homme depuis rien |

- **Les gels** : retrait → 2 tours ; frappe réalisée → 1 tour pour la pièce
  qui frappe ; reconstruction → 2 tours. Un gel ne s'additionne pas : on garde
  le plus tardif.

---

## 6. Les sauts de temps

Un saut ne s'interrompt jamais : le joueur est explicitement parti. Pour chaque
tour sauté :

1. les arrivées entrent, les gels expirent ;
2. les clés noires prêtes se réalisent ; les clés suspendues restent
   suspendues et, à leur date, sont constatées **manquées** ;
3. sur un maillon contesté, le défenseur tient ; les pièces noires suivent
   leurs **consignes**, et sans consigne elles tiennent et encaissent ;
4. une destruction datée atterrit, ou, parée depuis un tour, tombe ;
5. une réaction verte qui n'est pas « tenir » est décidée une fois, par un
   appel à la tête verte, au tour où sa pièce est touchée.

Chaque tour sauté est présenté au retour, dans l'ordre.

---

## 7. L'ouverture

1. Chaque camp pose sa racine (`viser`, sans `sert`) : le trône vu de son côté.
   C'est son coup du premier tour.
2. Toutes les ressources de tous les camps passent par `demander` puis
   `arbitrer`, en une file, arbitrée une fois. Aucune ressource n'apparaît
   sans ces deux lignes. Gratuit.
3. L'arbitre joue `justifier` sur chaque racine, une fois, et constate qui
   est assis, s'il y a quelqu'un.
4. Le reste se pose **un coup par tour** : un état (avec `sert` vers son
   parent, `arrive_tour` s'il est daté), un blocage, une clé. Le deck se
   construit en jouant, jamais d'un bloc — c'est ce qui lisse la charge.

---

## 8. Arbitrer une ressource

L'ordre est fixe ; on s'arrête au premier qui répond, et on écrit la source :

1. **L'état le sait** (`personnages`, `lieux`, `maisons`, les mains, un
   cahier) : accordé sur pièce.
2. **Un mécanisme la produit** (une tête, une main, une chaîne déjà écrite) :
   le manque est **acté**, le mécanisme nommé, la valeur laissée à ce qu'il
   rendra, avec un délai.
3. **Rien ne répond** : le MJ **comble**, une fois, à froid, d'après le canon
   et le plausible, et l'écrit dans l'état.

Comblé ne passe jamais avant acté. Un camp ne tranche jamais une ressource
d'un autre camp : il pose une hypothèse dans son plan, ce qui est un coup à
lui, pas une vérité. **Un heurt se tranche par le même ordre** (règle 24).

---

## Annexe A — Format des lignes

```jsonl
{"n":1,"tour":1,"camp":"noir","coup":"viser","id":"49000","texte":"La reine est assise sur le Trône de Fer","sert":null}
{"n":2,"tour":1,"camp":"vert","coup":"viser","id":"v-criston","arrive_tour":4,"texte":"L'ost de Criston est devant Sombreval"}
{"n":4,"tour":1,"camp":"noir","coup":"demander","id":"ost-noir","lieu":"peyredragon","nombre":1200,"tenu_par":"steffon-darklyn"}
{"n":5,"tour":1,"camp":"arbitre","coup":"arbitrer","sur":"ost-noir","verdict":"accorde","arrive_tour":3,"nombre":1200,"motif":"26013 et 26202 : douze cents de levée"}
{"n":3,"tour":1,"camp":"vert","coup":"bloquer","id":"49001","sur":"49000","texte":"Tient le Donjon Rouge avec sa garnison","engage":["garnison-donjon"]}
{"n":6,"tour":2,"camp":"noir","coup":"lever","id":"49010","ouvre":["49001"],"texte":"Fait entrer l'armée par la porte de la Rivière","engage":["ost-noir","steffon-darklyn"]}
{"n":7,"tour":2,"camp":"vert","coup":"justifier","sur":"49010","texte":"Par où douze cents hommes entrent-ils dans un château fermé"}
{"n":8,"tour":3,"camp":"noir","coup":"agir","id":"49021","realise":"49010","qui":"rhaenyra","avec":["syrax"],"texte":"Vole jusqu'à Port-Réal","etat":"a_faire"}
{"n":9,"tour":3,"camp":"noir","coup":"agir","id":"49021","etat":"faite","texte":"Réalisée : elle est au-dessus de la ville"}
{"n":14,"tour":6,"camp":"vert","coup":"detruire","id":"70040","cible":"barques-selm","engage":["galeres-royales"],"texte":"Coule les deux barques de nuit"}
{"n":15,"tour":6,"camp":"noir","coup":"retourner","id":"70041","cible":"larys","engage":["harrenhal-promis"],"texte":"Achète Larys avec Harrenhal"}
{"n":16,"tour":7,"camp":"noir","coup":"retirer","id":"barques-selm","gel_tours":2,"texte":"Rentre les barques au port"}
{"n":17,"tour":7,"camp":"noir","coup":"rearmer","id":"49010","engage":["meleys"],"texte":"Meleys tient le ciel au-dessus de la porte"}
{"n":28,"tour":6,"camp":"noir","coup":"reconstruire","id":"coques-3","revient_tour":8,"texte":"Affrète trois coques au banc de l'Est"}
{"n":29,"tour":6,"camp":"noir","coup":"consigne","pieces":["ost-noir"],"texte":"Tenir la porte, ne pas sortir"}
{"n":30,"tour":9,"camp":"arbitre","coup":"arbitrer","sur":"70040","verdict":"tranche","nombre":1,"detruit":[],"motif":"une barque sur deux, la nuit était claire"}
{"n":50,"tour":20,"camp":"arbitre","coup":"constater","etat":"200","verdict":"vrai","motif":"aucun blocage ouvert ; la porte est passée"}
{"n":51,"tour":21,"camp":"arbitre","coup":"tour","arrivees":[],"degeles":[],"menaces":[],"parees":[],"etats_arrives":[],"branches_mortes":[],"jours":2}
```

Un arbitrage vise un **id**, jamais un numéro de ligne (les numéros glissent
dès qu'un coup est refusé) ; le numéro n'est accepté qu'à défaut d'id.

## Annexe B — Alignement du manuel et du greffe, 3 septembre 2026

Ce fichier a été écrit sur un état où le manuel (`mj-partie.md` §3) était en
retard sur le code. Le même jour, les deux ont été alignés :

- **Le manuel a adopté ce que le greffe faisait déjà** : dix-sept coups
  (`retourner`, `constater`, `tour`), `justifier` sur un blocage ou un état,
  `bloquer` sur une clé ou une destruction (la parade), `agir` sous un
  blocage, la tolérance des branches mortes, la menace parée qui attend
  pendant un saut, `passer` et `rearmer` comptés.
- **Le greffe a corrigé deux écarts à ses propres règles** : un `bloquer`
  sans pièce est refusé (règle 2, comme la clé) ; la pièce mise dans un
  `retourner` est rendue à la réalisation, gelée un tour, comme après une
  frappe (règle 22). Tests : `scripts/tests/test_partie_blocage_retourner.py`.
- **Le même jour, cinq règles nouvelles**, tirées du duel de 50 tours et
  portées par `partie_tour.py` : la réponse à un `justifier` ne compte pas
  (règle 14) ; une parade tient un tour puis la frappe tombe (règles 11 et
  19) ; le greffe liste les états constatables et les camps muets (règle 29) ;
  un état vrai libère sa place au deck (règle 26) ; chaque camp a sa racine et
  le trône se lit sur les deux (règle 28). Tests :
  `scripts/tests/test_partie_tour.py`. **Le rejeu de `duel-50` change** : la
  frappe de Vhagar sur Meleys, parée par Caraxes au tour 9, tombe désormais au
  tour 11 au lieu d'atterrir au tour 17 ; Meleys y est vivante, et les motifs
  des constats écrits ensuite ne décrivent plus la position rejouée.
- **Plus tard le même jour** : les camps ne sont plus deux ni nommés — la
  partie en nomme autant qu'elle veut, `arbitre` est le seul nom réservé, ce
  qui contrarie une pièce est le camp de sa cible, le trône n'est à personne
  tant que rien n'est constaté (le rejeu de `le-trone` le dit désormais) ; la
  table de force des heurts est retirée au profit de l'arbitrage sourcé ; le
  jour J disparaît des règles ; les sections « méthode d'application » et
  « interdits » du manuel sont supprimées.
- **Reste hors manuel, décrit ici seulement** : `tranche` accepté sur une
  demande (même effet qu'`accorde` plus `nombre`), et le numéro de ligne
  accepté à défaut d'id dans `arbitrer`.
