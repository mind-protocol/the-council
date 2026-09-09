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

**Chaque règle a une adresse** (7 septembre 2026) : un en-tête `**R8 ·
preseance-blocage**` — le numéro est l'ordre de lecture, le slug est l'adresse,
stable, celle que le manuel cite (`→ R8 · preseance-blocage`) et que le code
porte en commentaire (`# regle: preseance-blocage`) à l'endroit exact où il
l'applique ou la refuse. `python scripts/regles.py --verifier` tient les deux
bouts : une règle sans marqueur ou un marqueur sans règle est une faute, sauf
pour les règles déclarées `— sans code : <raison>` dans leur en-tête, qui sont
des pratiques de l'arbitre et non des vérifications du greffe. `--ecrire`
regénère sous chaque règle la ligne « où : … » (entre `<!-- ou:debut -->` et
`<!-- ou:fin -->`) : ne pas l'éditer à la main.

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
| — | **le grand livre** | la liste des ressources, avec pour chacune : camp, lieu, nombre, tenant, tour d'arrivée, gel, ce qui l'engage, détruite ou non, source | dérivé des lignes |
| — | **le deck** | les états qu'un camp met en jeu, **dix au plus**. Le reste du plan dort et n'est touché par aucun coup | — |

- **O1 · un-id-un-objet** — **Un id n'a qu'un objet.** États, blocages, clés,
  maillons, destructions et retournements partagent un seul espace de noms : un
  id déjà pris est refusé. Une ressource a son propre espace (le grand livre) ;
  un id de ressource déjà au grand livre et non détruite est refusé.
  <!-- ou:debut -->
  où : `partie_validite.py` (`id_pris`, `verifier`)
  <!-- ou:fin -->

### 2.1 Les états d'une ressource

- **O2 · etats-ressource** — Une ressource est, à tout instant, dans un et un
  seul de ces états, et chacun est une raison de refus nommée quand on veut
  l'engager :
  <!-- ou:debut -->
  où : `partie_validite.py` (`pieces_libres`), `partie_lecture.py` (`piece`)
  <!-- ou:fin -->

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

- **O3 · etats-cle** — **valide** (posée, rien ne la suspend) · **prête au
  tour N** (une de ses pièces est en route) · **suspendue** (un `justifier`
  attend sa chaîne) · **sans ressource** (une pièce engagée manque : gelée,
  détruite, en attente, prise) · **tenue** (tous ses blocages sont tombés, ou
  son état est constaté vrai : elle a fait son office, ses pièces sont rendues)
  · **retirée**.
  <!-- ou:debut -->
  où : `partie_greffe.py` (`prevaut`), `partie_lecture.py` (`chaine`)
  <!-- ou:fin -->

### 2.3 Les états d'un blocage

- **O4 · etats-blocage** — **tient** · **prêt au tour N** · **suspendu**
  (justifié, maillon non écrit) · **levé** (une clé valide l'ouvre) · **tombé**
  (retiré, refusé pour portée, sa pièce partie, son état constaté vrai, ou la
  destruction qu'il protégeait finie).
  <!-- ou:debut -->
  où : `partie_greffe.py` (`prevaut`)
  <!-- ou:fin -->

---

## 3. Les coups

Un coup est une ligne. Champs communs : `n` (rang, posé par le greffe),
`tour`, `camp` (le nom du camp, ou `arbitre`), `coup`, `texte` (une phrase,
verbe d'abord).

### 3.1 Les coups des camps

| Coup | Cible | Effet | Coût | Compte pour « un coup par tour » |
|---|---|---|---|---|
| 🎯 `viser` · **C1 · coup-viser** | — | pose un état dans son deck. Avec `arrive_tour`, l'état est daté : il tient sa place d'avance et n'entre au deck qu'à ce tour | un coup, et une place du deck | **oui** : un état se pose un par un, comme les autres pièces |
| 🃏 `sortir` · **C2 · coup-sortir** | un état à soi, au deck | le sort du deck ; ses pièces restent engagées où elles sont | — | oui |
| 📦 `demander` · **C3 · coup-demander** | — | demande une ressource : `id`, une phrase, `nombre` s'il fractionne. Le lieu et le tenant se disent dans la phrase ; c'est l'arbitre qui les écrit | rien tant que l'arbitre n'a pas parlé | non |
| 🔒 `bloquer` · **C4 · coup-bloquer** | un état, un maillon, une clé ou une destruction **d'un autre camp** | pose un blocage, avec la pièce qui le produit (`engage`) | la pièce, engagée | oui |
| 🗝️ `lever` · **C5 · coup-lever** | **un** blocage adverse (`ouvre`), ou un état à soi (`sert`) | pose une clé qui le lève ; sans blocage, réalise l'état quand l'arbitre le constate | les pièces, engagées ; **au moins une** | oui |
| ⚔️ `agir` · **C6 · coup-agir** | une clé, une destruction ou un blocage **à soi** (`realise`) | pose un maillon : `qui`, `avec`, `texte`. Un maillon s'écrit quand c'est fait ; il n'a pas d'état. Le maillon écrit **lève la suspension** de sa cible | rien de plus que ce que la cible engage | oui, **sauf s'il répond à un `justifier`** (le greffe pose `repond`) |
| ❓ `justifier` · **C7 · coup-justifier** | une clé, un blocage, une destruction ou un état **d'un autre camp** | exige la chaîne : la cible passe **en suspens** jusqu'à ce qu'un maillon soit écrit dessous (ou, pour une destruction, que l'arbitre accorde). **Une fois par pièce**, jamais deux | rien | non |
| 💥 `detruire` · **C8 · coup-detruire** | une ressource adverse (`cible`) | pose une menace datée ; réalisée, la ressource est détruite et tout ce qu'elle tenait tombe | la pièce qui frappe, engagée, puis **gelée un tour** à la réalisation | oui |
| 🔄 `retourner` · **C9 · coup-retourner** | une ressource adverse (`cible`) | même fenêtre, même parades, même arbitrage qu'une destruction ; réalisée, la ressource **passe au camp qui l'a retournée**, libre, et tout ce qu'elle tenait tombe | ce qu'on y met (`engage`) ; voir §4.4 | oui |
| 🗑️ `retirer` · **C10 · coup-retirer** | une clé, un blocage, une destruction, un retournement ou une ressource **à soi** | le retire ; les pièces libérées sont **gelées deux tours** (`gel_tours` surchargeable) | deux tours à découvert | oui |
| 🔧 `reconstruire` · **C11 · coup-reconstruire** | une ressource détruite à soi | la rend, **au tour + 2** (`revient_tour` surchargeable), engagée par rien | deux tours | oui |
| ➕ `rearmer` · **C12 · coup-rearmer** | une clé ou un blocage à soi qui tient encore | ajoute une pièce sans changer ni le texte ni la cible ; la clé devient « prête » au tour d'arrivée de la pièce ajoutée si elle est en route | un coup, pas de gel | oui |
| ⏸️ `passer` · **C13 · coup-passer** | — | ne joue rien | le tour | oui |
<!-- ou:debut -->
- `coup-viser` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-sortir` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-demander` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-bloquer` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-lever` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-agir` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-justifier` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-detruire` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-retourner` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-retirer` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-reconstruire` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-rearmer` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-passer` — où : `partie_gestes.py` (`passer`)
<!-- ou:fin -->

### 3.2 Les coups de l'arbitre

| Coup | Cible | Effet |
|---|---|---|
| ⚖️ `arbitrer` · **A1 · coup-arbitrer** | un id (une demande, une destruction, une clé, un blocage) ; un numéro de ligne à défaut | **toujours avec `motif` et sa source** (numéro de pièce, fichier d'état, canon). Verdicts : `accorde`, `refuse`, `reporte`, `tranche`. Effets selon la cible, §3.3 |
| ✅ `constater` · **A2 · coup-constater** | un état | `verdict: vrai` ou `faux`, avec `motif`. Un état constaté vrai fait tomber les blocages posés dessus par d'autres camps et tient les clés qui le servent (pièces rendues sans gel). Sur une racine, il donne ou retire le trône |
| ❓ `justifier` · **A3 · arbitre-justifie** | n'importe quel objet des deux camps | l'arbitre peut exiger la chaîne d'un état dès l'ouverture (« qui s'assied, et comment arrive-t-elle ? »), une fois |
| ⏭️ `tour` · **A4 · coup-tour** | — | passe le tour, §5 : arrivées, dégels, atterrissages, parades tenues, états datés, états constatables, camps muets, branches mortes |
<!-- ou:debut -->
- `coup-arbitrer` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `coup-constater` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
- `arbitre-justifie` — où : `partie_validite.py` (`verifier`)
- `coup-tour` — où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`), `partie_tour.py` (`ligne`)
<!-- ou:fin -->

### 3.3 Ce que fait chaque verdict

| Sur | `accorde` | `refuse` | `reporte` | `tranche` |
|---|---|---|---|---|
| une **demande** · **V1 · verdict-sur-demande** | la ressource entre au grand livre, corrigée (`lieu`, `nombre`, `tenu_par`), datée (`arrive_tour`, sinon le tour courant) | la ressource est effacée du grand livre | comme accorde, avec `arrive_tour` | comme accorde ; sert à réduire un nombre (« six cents, pas deux mille ») |
| une **destruction** ou un **retournement** · **V2 · verdict-sur-menace** | la portée est jugée bonne : la suspension tombe | la menace tombe ; la pièce qui frappait est rendue sans gel ; les blocages posés sur elle tombent | `arrive_tour` déplacé | la menace se réalise **maintenant**, partiellement si `nombre` (ce qui sort du grand livre) ; `detruit: [...]` nomme les pièces qui meurent aussi (heurt mutuel) |
| une **clé** · **V3 · verdict-sur-cle** | — | la clé est retirée, pièces rendues sans gel | — | — |
| un **blocage** · **V4 · verdict-sur-blocage** | — | sans portée : il tombe | — | — |
<!-- ou:debut -->
- `verdict-sur-demande` — où : `partie_greffe.py` (`_appliquer_brut`)
- `verdict-sur-menace` — où : `partie_greffe.py` (`_appliquer_brut`)
- `verdict-sur-cle` — où : `partie_greffe.py` (`_appliquer_brut`)
- `verdict-sur-blocage` — où : `partie_greffe.py` (`_appliquer_brut`)
<!-- ou:fin -->

---

## 4. Les règles de validité et de résolution

### 4.1 Engagement et ressources

1. **R1 · engage-jusqu-a-chute** — **Une pièce engagée l'est jusqu'à ce que
   ce qui l'engage cesse** (retiré, tombé, tenu, refusé, réalisé). Une deuxième
   clé qui la veut est « sans ressource » ; le greffe refuse le coup avec la
   raison.
   <!-- ou:debut -->
   où : `partie_validite.py` (`pieces_libres`), `partie_greffe.py` (`_liberer`)
   <!-- ou:fin -->
2. **R2 · pas-de-ressource-pas-de-coup** — **Pas de ressource, pas de coup.**
   Une clé ou un blocage qui n'engage rien est refusé. Une pièce absente du
   grand livre, en attente, détruite, à l'autre camp, gelée ou déjà engagée
   ailleurs est une raison de refus, chacune nommée.
   <!-- ou:debut -->
   où : `partie_validite.py` (`pieces_libres`)
   <!-- ou:fin -->
3. **R3 · piece-en-route-s-engage** — **Une pièce en route s'engage.** Elle est
   réservée dès ce tour, visible de l'adversaire ; la clé, le blocage ou la
   menace est **« prêt au tour N »**, celui où toutes ses pièces sont arrivées,
   et ne prévaut pas avant. Poser tôt est un engagement, pas une avance.
   <!-- ou:debut -->
   où : `partie_greffe.py` (`_prete_tour`, `prevaut`)
   <!-- ou:fin -->
4. **R4 · maillon-piece-inconnue** — **Un maillon peut citer une pièce
   inconnue** (`avec`) : c'est un avertissement, pas un refus. Une pièce
   détruite est un refus.
   <!-- ou:debut -->
   où : `partie_validite.py` (`verifier`)
   <!-- ou:fin -->
5. **R5 · branche-morte** — **Une ressource accordée et engagée par rien deux
   tours après son arrivée est une branche morte.** Signalée au passage du
   tour, jamais punie. Une pièce qui a figuré une fois dans un `engage`, un
   `avec` ou un `qui` n'est plus jamais signalée.
   <!-- ou:debut -->
   où : `partie_tour.py` (`tolerees`, `ligne`)
   <!-- ou:fin -->

### 4.2 Blocages, clés, préséance

6. **R6 · blocage-par-un-autre-camp** — **Un blocage est posé par un autre
   camp, jamais sur soi.** Ce qu'on ignore de son propre plan n'est pas un
   blocage, c'est un trou. Ce qu'un blocage contrarie, c'est le camp de sa
   cible.
   <!-- ou:debut -->
   où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`camp_de`)
   <!-- ou:fin -->
7. **R7 · defenseur-tient** — **Le défenseur tient par défaut.** Un blocage
   qu'aucune clé ne lève prévaut ; une frappe parée que l'arbitre ne tranche
   pas tombe. Rien ne bouge tant qu'un coup ne le tranche pas.
   <!-- ou:debut -->
   où : `partie_greffe.py` (`prevaut`), `partie_tour.py` (`appliquer`)
   <!-- ou:fin -->
8. **R8 · preseance-blocage** — **Qui prévaut sur un blocage**, dans cet ordre :
   1. tombé → le camp de la cible ;
   2. suspendu (justifié, maillon non écrit) → le camp de la cible ;
   3. pas encore prêt (pièce en route) → le camp de la cible ;
   4. une clé l'ouvre : suspendue → le camp du blocage ; pas prête → le camp
      du blocage ; sans ressource → le camp du blocage ; sinon → **le camp de
      la clé** ;
   5. aucune clef ne le lève → le camp du blocage.
   <!-- ou:debut -->
   où : `partie_greffe.py` (`prevaut`)
   <!-- ou:fin -->
9. **R9 · cle-tenue** — **Une clé dont tous les blocages sont tombés est
   tenue** : ses pièces reviennent libres, sans gel. Elle ne se réarme plus ;
   ce qu'on veut encore poser là se pose à neuf.
   <!-- ou:debut -->
   où : `partie_greffe.py` (`_tomber`)
   <!-- ou:fin -->
10. **R10 · blocage-tombe-avec-sa-piece** — **Un blocage tombe avec sa
    pièce.** Pièce retirée ou détruite → le blocage tombe. Une clé dans le
    même cas devient « sans ressource » jusqu'à ce qu'on la réarme.
    <!-- ou:debut -->
    où : `partie_validite.py` (`pieces_libres`), `partie_greffe.py` (`_appliquer_brut`, `_realiser_menace`, `prevaut`)
    <!-- ou:fin -->
11. **R11 · parade-un-tour** — **Un blocage posé sur une destruction** (une
    bête entre la frappe et la colonne) la **pare**, et une parade tient **un
    tour** : au passage du tour où la frappe devait atterrir, elle attend ; au
    passage du suivant, si l'arbitre n'a pas tranché (règle 24), elle
    **tombe** — le défenseur tient par défaut. L'écran est rendu sans gel, la
    pièce qui frappait rentre gelée un tour.
    <!-- ou:debut -->
    où : `partie_greffe.py` (`_menace_finie`, `_protegee`), `partie_tour.py` (`_en_l_air`, `appliquer`)
    <!-- ou:fin -->
12. **R12 · etat-vrai-libere** — **Un état constaté vrai** fait tomber ce qui
    le bloquait (les blocages des autres camps) et tient ce qui le servait
    (clés `sert`). Constater vrai un état dont un état-fils est encore au deck
    sans être constaté ni sorti est un avertissement, pas un refus : l'arbre
    n'est pas une conjonction.
    <!-- ou:debut -->
    où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
    <!-- ou:fin -->

### 4.3 La charge de la preuve

13. **R13 · cle-sans-maillon-affirmation** — **Une clé ou un blocage sans
    maillon est une affirmation** : valide jusqu'à ce qu'un coup exige sa
    chaîne.
    <!-- ou:debut -->
    où : `partie_greffe.py` (`_appliquer_brut`)
    <!-- ou:fin -->
14. **R14 · justifier-suspend** — **Justifier ne punit pas.** Gratuit, hors
    compte, il suspend la cible ; la suspension tombe dès qu'un maillon est
    écrit dessous (`agir` avec `realise`), ou, pour une destruction, dès que
    l'arbitre accorde la portée.
    <!-- ou:debut -->
    où : `partie_greffe.py` (`_appliquer_brut`)
    <!-- ou:fin -->
    - **R14b · justifier-une-fois** — **Une pièce ne se justifie qu'une fois**
      dans toute la partie, quel que soit le camp qui l'a fait.
      <!-- ou:debut -->
      où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`), `partie_marques.py` (`questionnable`)
      <!-- ou:fin -->
    - **R14c · reponse-gratuite** — **La réponse est aussi gratuite que la
      question** : le maillon écrit sur une cible suspendue porte `repond` et
      ne compte pas pour le tour.
      <!-- ou:debut -->
      où : `partie_validite.py` (`verifier`), `partie_tour.py` (`inactifs`), `partie_ecriture.py` (`ecrire`)
      <!-- ou:fin -->
    - **R14d · question-sur-etat-sans-reponse** — **Une question sur un état
      ne se lève que par le constat.** Aucun maillon ne s'écrit sous un état,
      et la suspension ne change rien à `constatables` ; c'est `constater`,
      vrai ou faux, qui l'efface (7.9, audit A8). Entre les deux, l'écran le
      montre « en question », et c'est juste : la question attend l'arbitre.
      <!-- ou:debut -->
      où : `partie_greffe.py` (`_appliquer_brut`)
      <!-- ou:fin -->
15. **R15 · blocage-suspendu-ne-prevaut-plus** — **Un blocage suspendu ne
    prévaut plus** tant que son camp n'a pas écrit son maillon. C'est le
    symétrique exact de la clé.
    <!-- ou:debut -->
    où : `partie_greffe.py` (`_protegee`, `_appliquer_brut`, `prevaut`)
    <!-- ou:fin -->
16. **R16 · pas-sa-propre-chaine** — **On n'exige pas sa propre chaîne.** Un
    camp ne justifie que ce qui est à un autre ; l'arbitre justifie ce qu'il
    veut.
    <!-- ou:debut -->
    où : `partie_validite.py` (`verifier`), `partie_marques.py` (`questionnable`)
    <!-- ou:fin -->
17. **R17 · portee-refusee-sur-piece** — **La portée se refuse sur pièce.**
    Une destruction ou un blocage que la pièce ne peut pas atteindre (présence,
    moyen, distance) est refusé en une ligne par l'arbitre. C'est le seul
    endroit où le « comment » remonte de force.
    <!-- ou:debut -->
    où : `partie_greffe.py` (`_appliquer_brut`)
    <!-- ou:fin -->

### 4.4 Destruction, retournement, heurt

18. **R18 · menace-datee** — **Une destruction est toujours une menace
    datée.** Posée au tour t, elle arrive au plus tôt en t+1 (`arrive_tour`,
    jamais avant l'arrivée de ses pièces) et **n'atterrit qu'au passage du tour
    suivant son arrivée**. Le camp visé a donc toujours un tour pour bloquer,
    justifier ou retirer.
    <!-- ou:debut -->
    où : `partie_greffe.py` (`_appliquer_brut`), `partie_tour.py` (`_en_l_air`)
    <!-- ou:fin -->
19. **R19 · menace-suspendue-attend** — **Une menace suspendue n'atterrit
    pas.** Elle attend, tour après tour, et sa pièce reste engagée, jusqu'au
    maillon ou à l'arbitrage. **Une menace parée attend un tour, puis tombe**
    (règle 11), sauf `tranche` de l'arbitre entre-temps.
    <!-- ou:debut -->
    où : `partie_tour.py` (`_en_l_air`)
    <!-- ou:fin -->
20. **R20 · atterrissage-total** — **Une destruction qui atterrit sans
    arbitrage est totale.** Un heurt partiel se tranche **avant** le passage du
    tour ; après, la pièce est sortie du grand livre et un `tranche` tardif est
    refusé. Une correction est un coup de plus.
    <!-- ou:debut -->
    où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_realiser_menace`)
    <!-- ou:fin -->
21. **R21 · destruction-realisee** — **Réalisée, une destruction** : détruit
    la cible (ou lui retranche `nombre`), retire sans gel les clés qu'elle
    portait, fait tomber les blocages qu'elle portait, rend la pièce qui
    frappait **gelée un tour**, et fait tomber les blocages posés sur la
    menace.
    <!-- ou:debut -->
    où : `partie_greffe.py` (`_realiser_menace`)
    <!-- ou:fin -->
22. **R22 · retournement-realise** — **Réalisé, un retournement** : la cible
    passe au camp qui a retourné, libre, avec `retourne_par` ; ce qu'elle
    tenait (clés, blocages) tombe. Ce qu'on y a mis revient **gelé un tour**,
    comme après une frappe, et ce qui parait le retournement tombe.
    <!-- ou:debut -->
    où : `partie_greffe.py` (`_realiser_menace`)
    <!-- ou:fin -->
23. **R23 · retirer-une-menace** — **Retirer une menace** rend sa pièce, gelée
    deux tours, et fait tomber ce qui la parait. **Retirer la ressource visée**
    fait tomber la menace ; la pièce qui frappait est rendue sans gel.
    <!-- ou:debut -->
    où : `partie_greffe.py` (`_appliquer_brut`)
    <!-- ou:fin -->
    - **R23b · retirer-le-frappeur** — **Retirer la pièce qui frappe fait
      tomber la frappe** (7.9, audit A2) : la pièce rentre gelée deux tours
      comme tout retrait, la menace est `tombee`, les autres pièces qu'elle
      engageait sont rendues sans gel et ce qui la parait tombe. Pas de
      ressource, pas de coup : une frappe sans frappeur n'atterrit pas.
      <!-- ou:debut -->
      où : `partie_greffe.py` (`_appliquer_brut`)
      <!-- ou:fin -->
24. **R24 · heurt-tranche-a-la-table** — **Un heurt se tranche à la table,
    avec sa source** (`tranche`, avec `motif`), par le même ordre que
    l'arbitrage d'une ressource (§8) : ce que l'état sait, ce qu'un mécanisme
    produit, ce que l'arbitre comble à froid. Il n'y a pas de table de force.
    `nombre` chiffre ce qui sort du grand livre ; `detruit` nomme ce qui meurt
    des deux côtés.
    <!-- ou:debut -->
    où : `partie_greffe.py` (`_appliquer_brut`)
    <!-- ou:fin -->
25. **R25 · reconstruire-ce-qui-se-reconstruit** — **Reconstruire** vaut pour
    ce qui se reconstruit (une porte, des coques, des engins), pas pour un
    pendu. La ressource revient au tour + 2, engagée par rien. Que la chose se
    reconstruise est un jugement de l'arbitre ; le délai et l'état de retour
    sont du greffe.
    <!-- ou:debut -->
    où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_appliquer_brut`)
    <!-- ou:fin -->

### 4.5 Le deck et le trône

26. **R26 · dix-etats** — **Dix états par deck**, les états datés en attente
    comptant pour leur place, **les états constatés vrais n'en tenant plus**
    (ils restent dans l'arbre). Entrer ou sortir un état est un coup.
    <!-- ou:debut -->
    où : `partie_validite.py` (`verifier`)
    <!-- ou:fin -->
27. **R27 · deck-calendrier** — **Un deck peut être un calendrier** : des
    états datés (`arrive_tour`), chacun entrant au deck au tour de sa date. Un
    `arrive_tour` déjà passé est refusé.
    <!-- ou:debut -->
    où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`au_deck`), `partie_tour.py` (`appliquer`)
    <!-- ou:fin -->
28. **R28 · trone-derniere-racine** — **Le trône est au camp dont la racine a
    été constatée vraie en dernier** ; un constat faux sur cette racine le lui
    retire sans le donner à personne. À personne tant que rien n'a été
    constaté : c'est à l'arbitre de constater qui est assis à l'ouverture. Un
    état constaté vrai reste attaquable : un blocage peut se poser dessus, et
    il faut le reconstater.
    <!-- ou:debut -->
    où : `partie_greffe.py` (`racine`, `tenu_par`)
    <!-- ou:fin -->
29. **R29 · greffe-liste-arbitre-constate** — **Le greffe liste, l'arbitre
    constate.** La ligne `tour` porte `constatables` : les états au deck, non
    constatés, dont tous les blocages sont tombés ou levés par une clé qui
    prévaut, ou qu'une clé valide sert sans que rien ne les bloque. Elle porte
    aussi `inactifs` : un camp qui n'a rien joué d'autre que passer sur les
    trois derniers tours. Ni l'un ni l'autre n'est un verdict.
    <!-- ou:debut -->
    où : `partie_tour.py` (`constatables`, `inactifs`)
    <!-- ou:fin -->
    - **R29b · constatable-attend-un-tour** — sans code : pratique de
      l'arbitre, pas vérification du greffe. Un état signalé `constatable` au
      passage du tour laisse un tour au camp adverse pour poser quelque chose
      dessus ; sans ça, le constat tombe avant que l'autre ait vu l'état
      (`docs/parties/learnings.md` §5).
      <!-- ou:debut -->
      où : sans code (la raison est dans l'en-tête)
      <!-- ou:fin -->

### 4.6 Le rythme

30. **R30 · un-coup-par-tour** — **Un camp ne joue qu'un coup compté par
    tour** (`viser`, `sortir`, `bloquer`, `lever`, `agir`, `detruire`,
    `retourner`, `retirer`, `reconstruire`, `rearmer`, `passer`). Ne comptent
    pas : `demander`, `justifier`, un `agir` qui répond à un `justifier`, et
    tout ce qui vient de l'arbitre. **Le contrôle est gradué** : un second
    coup compté passe et se signale, il n'est pas refusé. C'est au MJ de tenir
    la règle et de savoir quand il la casse (l'ouverture).
    <!-- ou:debut -->
    où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`module`)
    <!-- ou:fin -->
31. **R31 · seul-l-arbitre** — **Seul l'arbitre** arbitre, constate et passe
    le tour ; et l'arbitre ne joue aucun coup de camp. À l'écran, « le jour
    passe » est refusé à tout autre camp.
    <!-- ou:debut -->
    où : `partie_validite.py` (`verifier`), `partie_gestes.py` (`jouer`)
    <!-- ou:fin -->
32. **R32 · ligne-au-tour-courant** — **Une ligne de camp est datée du tour
    courant, ou elle n'est pas datée.** Un `tour` fourni sur tout coup autre
    que `tour` et différent du tour de la partie est refusé (7.9, audit A5) :
    seul le passage du tour déplace le tour (T3). Le rejeu, lui, garde le plus
    grand `tour` lu, pour les fichiers d'avant.
    <!-- ou:debut -->
    où : `partie_validite.py` (`verifier`)
    <!-- ou:fin -->

---

## 5. Le temps

- **T1 · trait-ordre-d-entree** — **Le tour** est l'unité de jeu : un coup
  compté de chaque camp, dans l'ordre où les camps sont entrés dans la partie ;
  le trait passe au camp qui suit le dernier coup compté.
  <!-- ou:debut -->
  où : `partie_greffe.py` (`camps`), `partie_lecture.py` (`trait`)
  <!-- ou:fin -->
- **T2 · tour-deux-jours** — **Un tour vaut deux jours du monde**
  (`JOURS_PAR_TOUR = 2`).
  <!-- ou:debut -->
  où : `partie_greffe.py` (`module`)
  <!-- ou:fin -->
- **T3 · passage-du-tour** — **Au passage du tour** (`tour`), le greffe écrit
  sur la ligne ce qui arrive (`scripts/noyau/partie_tour.py`) : `arrivees`,
  `degeles`, `menaces` (qui atterrissent), `parees` (qui attendent),
  `parades_tenues` (dont la frappe tombe), `etats_arrives`, `constatables`,
  `inactifs`, `branches_mortes`. Puis il applique la même liste : entrée des
  états datés, atterrissage, chute des frappes parées depuis un tour, marquage
  des parades neuves.
  <!-- ou:debut -->
  où : `partie_tour.py` (`ligne`, `appliquer`), `partie_ecriture.py` (`ecrire`)
  <!-- ou:fin -->
- **T4 · delais-d-arrivee** — sans code : c'est la table de l'arbitre, qui
  date `arrive_tour` en accordant ; le greffe prend la date telle quelle et
  n'en juge pas. **Les délais d'arrivée**, jamais un jugement :
  <!-- ou:debut -->
  où : sans code (la raison est dans l'en-tête)
  <!-- ou:fin -->

| Délai (tours) | Sens | Exemples |
|---|---|---|
| 0 | déjà là | une garnison dans ses murs, une bête en ville, une bourse |
| 1 | il faut préparer | un dragon des terres de la Couronne ; une coque, une traversée ; un affrètement |
| 2 | quelques jours | une réponse de banneret ; une bête depuis Harrenhal ; un ost à deux jours de route |
| 4 | une semaine | un ost à huit jours de route ; un passage de la route du sel |
| 8 et plus | très long | Villevieille, le Nord, le Val ; retourner un homme depuis rien |

- **T5 · gels** — **Les gels** : retrait → 2 tours ; frappe réalisée → 1 tour
  pour la pièce qui frappe ; reconstruction → 2 tours. Un gel ne s'additionne
  pas : on garde le plus tardif.
  <!-- ou:debut -->
  où : `partie_greffe.py` (`module`, `_liberer`, `_realiser_menace`)
  <!-- ou:fin -->

---

## 6. Les sauts de temps

Il n'y a pas de saut : un tour sauté est un tour passé par l'arbitre, avec ce
que `tour` fait déjà (arrivées, dégels, atterrissages, parades tenues). Une
pièce visée pendant l'absence de son camp tient et encaisse ; c'est le défaut
du greffe, et il n'y a rien à lui dire d'avance. La règle du saut et la
consigne qui l'accompagnait ont été retirées le 6 septembre 2026 : aucun code
ne les portait, et une seule ligne en 21 parties les avait invoquées.

---

## 7. L'ouverture

1. **P1 · racine-au-premier-tour** — sans code : le greffe lit la racine d'un
   camp comme son état sans `sert` (règle 28) et n'exige pas qu'elle soit
   posée au premier tour. Chaque camp pose sa racine (`viser`, sans `sert`) :
   le trône vu de son côté. C'est son coup du premier tour.
   <!-- ou:debut -->
   où : sans code (la raison est dans l'en-tête)
   <!-- ou:fin -->
2. **P2 · ressource-demandee-puis-arbitree** — Toutes les ressources de tous
   les camps passent par `demander` puis `arbitrer`, en une file, arbitrée une
   fois. Aucune ressource n'apparaît sans ces deux lignes : une pièce absente
   du grand livre ou en attente ne s'engage pas. Gratuit.
   <!-- ou:debut -->
   où : `partie_validite.py` (`pieces_libres`), `partie_greffe.py` (`_appliquer_brut`)
   <!-- ou:fin -->
3. **P3 · arbitre-justifie-les-racines** — sans code : pratique de l'arbitre
   à l'ouverture. Il joue `justifier` sur chaque racine, une fois, et constate
   qui est assis, s'il y a quelqu'un.
   <!-- ou:debut -->
   où : sans code (la raison est dans l'en-tête)
   <!-- ou:fin -->
4. **P4 · deck-en-jouant** — sans code : c'est la règle 30 qui porte le
   contrôle, et l'ouverture est le seul moment où le MJ la casse sciemment.
   Le reste se pose **un coup par tour** : un état (avec `sert` vers son
   parent, `arrive_tour` s'il est daté), un blocage, une clé. Le deck se
   construit en jouant, jamais d'un bloc — c'est ce qui lisse la charge.
   <!-- ou:debut -->
   où : sans code (la raison est dans l'en-tête)
   <!-- ou:fin -->

---

## 8. Arbitrer une ressource

- **S1 · ordre-d-arbitrage** — sans code : c'est le jugement de l'arbitre ;
  le greffe exige un `motif` (règle A1) et n'en lit pas le contenu. L'ordre
  est fixe ; on s'arrête au premier qui répond, et on écrit la source :
  1. **L'état le sait** (`personnages`, `lieux`, `maisons`, les mains, un
     cahier) : accordé sur pièce.
  2. **Un mécanisme la produit** (une tête, une main, une chaîne déjà
     écrite) : le manque est **acté**, le mécanisme nommé, la valeur laissée à
     ce qu'il rendra, avec un délai.
  3. **Rien ne répond** : le MJ **comble**, une fois, à froid, d'après le
     canon et le plausible, et l'écrit dans l'état.
  Comblé ne passe jamais avant acté. **Un heurt se tranche par le même
  ordre** (règle 24).
  <!-- ou:debut -->
  où : sans code (la raison est dans l'en-tête)
  <!-- ou:fin -->
- **S2 · motif-sans-menu** — sans code : une règle sur le texte du motif, que
  le greffe exige sans le lire. **Le motif ne nomme pas les coups de l'autre
  camp** (7 septembre 2026, `le-jeu-lui-meme-moi`). Il porte la source, la
  portée et la condition générale de chute d'une pièce ; il n'énumère jamais
  les parades, clefs ou questions que le camp adverse pourrait jouer — une
  telle liste est un menu, et un coup joué depuis un menu écrit par l'arbitre
  n'est plus un coup du joueur (charmed-2, n°55 puis n°58). L'aide au joueur
  va au banc de touche (`mj-partie.md` §6), jamais au greffe.
  <!-- ou:debut -->
  où : sans code (la raison est dans l'en-tête)
  <!-- ou:fin -->
- **S3 · camp-ne-tranche-pas-autrui** — Un camp ne tranche jamais une
  ressource d'un autre camp : il pose une hypothèse dans son plan, ce qui est
  un coup à lui, pas une vérité ; seul l'arbitre arbitre.
  <!-- ou:debut -->
  où : `partie_validite.py` (`verifier`)
  <!-- ou:fin -->

---

## Annexe A — Format des lignes

```jsonl
{"n":1,"tour":1,"camp":"noir","coup":"viser","id":"49000","texte":"La reine est assise sur le Trône de Fer","sert":null}
{"n":2,"tour":1,"camp":"vert","coup":"viser","id":"v-criston","arrive_tour":4,"texte":"L'ost de Criston est devant Sombreval"}
{"n":4,"tour":1,"camp":"noir","coup":"demander","id":"ost-noir","nombre":1200,"texte":"Douze cents hommes de levée à Peyredragon, sous Steffon Darklyn"}
{"n":5,"tour":1,"camp":"arbitre","coup":"arbitrer","sur":"ost-noir","verdict":"accorde","arrive_tour":3,"nombre":1200,"motif":"26013 et 26202 : douze cents de levée"}
{"n":3,"tour":1,"camp":"vert","coup":"bloquer","id":"49001","sur":"49000","texte":"Tient le Donjon Rouge avec sa garnison","engage":["garnison-donjon"]}
{"n":6,"tour":2,"camp":"noir","coup":"lever","id":"49010","ouvre":["49001"],"texte":"Fait entrer l'armée par la porte de la Rivière","engage":["ost-noir","steffon-darklyn"]}
{"n":7,"tour":2,"camp":"vert","coup":"justifier","sur":"49010","texte":"Par où douze cents hommes entrent-ils dans un château fermé"}
{"n":8,"tour":3,"camp":"noir","coup":"agir","id":"49021","realise":"49010","qui":"rhaenyra","avec":["syrax"],"texte":"Vole jusqu'à Port-Réal : elle est au-dessus de la ville"}
{"n":14,"tour":6,"camp":"vert","coup":"detruire","id":"70040","cible":"barques-selm","engage":["galeres-royales"],"texte":"Coule les deux barques de nuit"}
{"n":15,"tour":6,"camp":"noir","coup":"retourner","id":"70041","cible":"larys","engage":["harrenhal-promis"],"texte":"Achète Larys avec Harrenhal"}
{"n":16,"tour":7,"camp":"noir","coup":"retirer","id":"barques-selm","gel_tours":2,"texte":"Rentre les barques au port"}
{"n":17,"tour":7,"camp":"noir","coup":"rearmer","id":"49010","engage":["meleys"],"texte":"Meleys tient le ciel au-dessus de la porte"}
{"n":28,"tour":6,"camp":"noir","coup":"reconstruire","id":"coques-3","revient_tour":8,"texte":"Affrète trois coques au banc de l'Est"}
{"n":30,"tour":9,"camp":"arbitre","coup":"arbitrer","sur":"70040","verdict":"tranche","nombre":1,"detruit":[],"motif":"une barque sur deux, la nuit était claire"}
{"n":50,"tour":20,"camp":"arbitre","coup":"constater","etat":"200","verdict":"vrai","motif":"aucun blocage ouvert ; la porte est passée"}
{"n":51,"tour":21,"camp":"arbitre","coup":"tour","arrivees":[],"degeles":[],"menaces":[],"parees":[],"etats_arrives":[],"branches_mortes":[],"jours":2}
```

- **X1 · arbitrage-vise-un-id** — Un arbitrage vise un **id**, jamais un
  numéro de ligne (les numéros glissent dès qu'un coup est refusé) ; le numéro
  n'est accepté qu'à défaut d'id.
  <!-- ou:debut -->
  où : `partie_validite.py` (`verifier`), `partie_greffe.py` (`_lignes_visees`)
  <!-- ou:fin -->

**`signe`, facultatif, sur tout coup qui pose une carte** (`viser`, `bloquer`,
`lever`, `agir`, `detruire`, `retourner`) : UN emoji qui dit ce qu'est la chose
— 🗳️ une élection, 🚢 un port, 🔬 un résultat. Le greffe le garde sur l'objet ;
l'écran le préfère à sa devinette par le texte. Sans lui, la carte prend le
signe deviné, et à défaut celui de son type. Ajouté le 6.9 pour que chaque item
d'une partie ait un visage sans dépendre d'une table de mots.

```jsonl
{"n":52,"tour":9,"camp":"anthropic","coup":"viser","id":"a-election","sert":"a-ere","signe":"🗳️","texte":"Un pays a tenu une élection où chaque citoyen a pu vérifier son vote"}
```

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
- **Le 6 septembre 2026, quatre retraits** (`docs/parties/gestes-manquants.md`),
  sur le principe qu'un coup de joueur sans geste à l'écran n'existe pas pour
  le joueur : la `consigne` et le §6 des sauts ; la clef sur plusieurs
  verrous ; l'état `a_faire` / `faite` d'un maillon ; le lieu et le tenant
  écrits par un camp sur `demander`. La validité refuse les lignes neuves ;
  le greffe replie toujours les anciennes (une consigne dans `essai-1`, une
  clef double dans `charmed`, huit maillons `a_faire`), donc aucun rejeu ne
  bouge. Le schéma de l'IA (`partie_ia.py`) est devenu celui des gestes.
