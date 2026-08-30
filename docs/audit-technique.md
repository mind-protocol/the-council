# Audit technique — `le-conseil2` mesuré aux standards de `batailles`

**Deuxième passe, 30 du 8e mois 2026.** Première passe sur `690c4c2`, celle-ci sur `657cfb3` **plus l'arbre de travail** — un chantier de 223 suppressions, 115 fichiers neufs et 70 modifiés était en cours au moment de la mesure, et il applique l'essentiel du plan de la première passe. Ce qui suit distingue partout **ce qui est commité** (acquis) de **ce qui est dans l'arbre** (fait, pas encore tenu par l'historique).

Audit du **code** : pas la fiction, pas le contenu de `etat/`. L'étalon de comparaison est le dépôt voisin `C:\Users\reyno\batailles` — mêmes mains, même langue, même goût pour l'émergence, mais une discipline d'architecture *outillée*.

**Les chiffres de ce document sont rejouables** :

```bash
python scripts/analyse/audit_technique.py
```

Un écart entre cette sortie et le texte ci-dessous est un texte périmé, pas une mesure fausse. C'était la faiblesse de la première passe : un instantané en prose se démode en une journée dans un dépôt qui bouge tous les jours.

---

## 0. Ce qui a changé depuis la première passe

Sept des dix lignes du plan d'action sont faites ou engagées. Le tableau des cinq écarts devient :

| # | Écart de la 1re passe | État | Mesure aujourd'hui |
|---|---|---|---|
| 1 | Aucune contrainte outillée sur la taille | **⚙️ outillé, non commité** | `.claude/hooks/taille.js` en cliquet ; 59 fichiers > 500 l. (contre 61) ; le monolithe n'a pas bougé |
| 2 | Pas de frontière de module (globales, listes de scripts) | **🔴 aggravé** | `jeu.html` : **71 → 86 balises `<script>`** ; 110 IIFE / 24 ESM ; 64 globales |
| 3 | Le banc étalon n'est pas headless | **✅ résolu** | `node scripts/verifier.mjs` → **14 gardes vertes en 54,7 s**, sans serveur |
| 4 | Pas d'écrivain unique sur `etat/` | **🔶 porte posée, migration à faire** | `scripts/noyau/tables.py` existe ; **43 fichiers** écrivent encore hors porte — et c'est *le dépôt lui-même* qui le compte |
| 5 | Le dépôt porte ses sauvegardes | **✅ résolu** | **99 → 0** fichiers `*.avant-*` suivis ; `.gitignore` les ferme |

Deux constats de fond en sortent, et ils comptent plus que le tableau.

**Le premier confirme la thèse de la première passe.** Ce qui a été *outillé* a tenu ou progressé ; ce qui est resté en prose a dérivé. Le point 2 est la démonstration en direct : pendant que le dépôt se dotait d'un hook de taille, d'une porte d'état et d'une commande de vérification, `jeu.html` gagnait **quinze balises `<script>` de plus** — exactement la classe de défaut que `chaine.js` était né pour fermer. Rien ne surveillait ce compteur-là.

**Le second est une correction que je dois à la première passe.** Elle recommandait des garde-fous qui « ne demandent aucune décision d'architecture ». C'était vrai des sept premiers, faux du huitième : la porte d'état (§4) *est* une décision structurante, et elle a été prise — un JSON abîmé plante désormais, seule l'absence rend le défaut. Bien tranché, et documenté à l'endroit où la règle vit.

---

## 1. Taille et découpage — outillé, mais le cœur n'a pas bougé

### Ce que `batailles` fait

`.claude/hooks/check-file-size.js` signale après chaque `Write`/`Edit` tout fichier au-delà de 500 lignes. La limite n'est pas une hygiène, c'est ce qui force à nommer la pièce suivante avant qu'elle ne fonde dans la précédente : « les noms anticipent la croissance : dossier + nom précis (`forces/repulsions.js`, pas `forces.js`) ».

### Mesures

- **278 fichiers de code, 118 393 lignes** (était : 271 / 124 718 — le rangement de `scripts/` a supprimé 6 300 lignes mortes).
- **59 dépassent 500 lignes** (21 %), **20 dépassent 1 000**, **6 dépassent 2 000**.
- Les quatre plus gros : `ecrans/modules/bataille2d.js` (**10 511**), `scripts/tick.py` (3 214), `scripts/boucle_activation.py` (3 184), `scripts/monde/plan_ville.py` (2 494).
- Le monolithe, inchangé au chiffre près : **10 511 lignes**, **195 fonctions** au premier niveau, **158 champs distincts** sur l'objet `h`, et `soldat(h, dt)` toujours à **858 lignes**.

### Ce qui est fait

Le hook existe — `.claude/hooks/taille.js`, en **cliquet** : plafond d'un fichier = sa taille au dernier commit, 500 pour un fichier neuf, et il se tait quand un gros fichier maigrit. C'est la bonne forme, pour la bonne raison, et l'en-tête l'écrit. **Il n'est pas encore commité** : tant qu'il vit dans l'arbre de travail, il protège cette machine et pas le dépôt.

Le rangement de `scripts/` (commit `657cfb3`) est le vrai mouvement de cette passe : 37 commandes restent à la racine — celles qui sont *tapées*, dont les chemins sont écrits en dur dans les docs, les écrans et jusque dans les cahiers in-fiction — et le reste descend dans dix dossiers, **chacun avec son CLAUDE.md**. C'est la règle de `batailles` (« dossier + nom précis ») appliquée à un dépôt de 127 fichiers Python, et le commit signale les deux pièges trouvés en chemin (imports par nom nu, 34 racines calculées par `dirname(dirname(__file__))` qui cherchaient `etat/` *dans* `scripts/`).

### Ce qui reste

**1.1 — Commiter le hook.** Un garde-fou dans l'arbre de travail n'est pas un garde-fou.

**1.2 — `soldat()` (858 l.) reste le vrai chantier.** Quatre extractions ont été faites (navigation, identité, mouvement, topologie) : ce sont des *feuilles*. Aucune ne touche la fonction qui porte la décision, et c'est elle que `docs/combat/ARCHITECTURE.md` désigne dans sa couche `40-combattant`. Le banc étalon étant maintenant vert et headless (§3), **le filet existe enfin pour la faire** — c'est le changement de situation le plus important de cette passe. La prochaine extraction devrait être la cascade de `soldat()` en états nommés, pas une cinquième feuille.

**1.3 — `serveur/serveur.js` reste sans fiche.** Il ne figure plus dans les quatre plus gros parce que je le mesure désormais avec le reste, mais il pèse toujours 6 345 lignes et 59 chemins de route, et tout le raisonnement architectural du dépôt l'ignore. Le découper par famille de route (`/monde`, `/flux`, `/voix`, statique) est mécanique : ce sont des blocs disjoints. Deux bancs le couvrent déjà (`serveur-bibliotheque`, `serveur-piece-http`), ce qui rend l'opération sûre.

---

## 2. Frontières de module — le seul écart qui a empiré

C'est le point où l'audit doit être le plus net, parce que tout le reste a progressé.

### Mesures

| | 1re passe | aujourd'hui |
|---|---|---|
| balises `<script src=>` dans `jeu.html` | 71 | **86** (+15) |
| balises dans `bataille.html` | 14 | 14 |
| `?v=` écrits à la main | 12 | 10 |
| fichiers front en IIFE / en ESM | 97 / 24 | **110 / 24** |
| globales `window.*` distinctes | 67 | 64 |

Les quinze balises neuves de `jeu.html` sont dans l'arbre de travail (`git diff` : +19 lignes). Aucune n'est passée par `chaine.js`.

### Pourquoi c'est le point qui compte maintenant

`chaine.js` porte dans son en-tête le récit exact de ce qui recommence : huit listes de scripts avaient divergé en silence, « et l'on découvre six semaines plus tard que le banc jugeait un autre moteur que celui qu'on regarde ». Le manifeste a été écrit pour fermer cette classe de bug. Il coexiste toujours avec 100 balises en dur réparties sur deux pages, et la population de ces balises **augmente**.

L'en-tête de `hasard.js` justifie honnêtement le refus d'ESM : passer `type="module"` casserait l'ordre synchrone dont dépendent `carte-ville.js` et `capture.js`. C'est vrai, et c'est le piège : chaque module ajouté en style global rend la migration plus chère, ce qui la repousse, ce qui produit d'autres modules globaux. Le critère du dépôt, retourné contre lui — « l'architecture est ce qui rend la bonne chose moins chère que la mauvaise ».

### Recommandations

**2.1 — Faire du manifeste la seule source, y compris pour le HTML.** `chaine.js` sait déjà déclarer des ensembles (`moteur`, `scene`) et sait déjà se comporter différemment sous Node et sous navigateur. Qu'il **pose les balises** au lieu de coexister avec elles : un `<script src=".../chaine.js">` suivi d'un `BatailleChaine.poser("scene")`. Cela supprime 100 lignes en dur et rend la divergence structurellement impossible.

**2.2 — Une mesure `chaine` dans `verifier.mjs`.** C'est la leçon de cette passe, et elle est bon marché : *le compteur qui n'existe pas est celui qui dérive*. `verifier.mjs` a déjà la notion de **mesure** (un chiffre qui ne barre rien) — celle-ci tient en dix lignes : « N balises `<script>` hors manifeste ». Elle aurait montré le +15 le jour même.

**2.3 — Le `?v=` doit être calculé, jamais écrit.** Le serveur connaît la mtime du fichier qu'il sert ; qu'il pose un `ETag`, ou que `chaine.js` demande `?v=<mtime>` en posant la balise. Le commit `92d0de6` (« l'ecran montrait une bataille d'avant-hier ») a déjà payé cette dérive une fois.

**2.4 — Migrer vers ESM par la feuille.** Chaque pièce sortie dans `moteur/` peut naître en ESM *et* rester compatible : `chaine.js` utilise déjà le motif UMD. En faire la règle pour tout fichier neuf sous `moteur/` donne, à la fin de l'extraction, un moteur intégralement importable — sans jamais casser la page.

---

## 3. Vérification — résolu, et au-delà de ce qui était demandé

### Ce que `batailles` fait

`node coding/fumee.mjs` : headless, sans navigateur, sans serveur — posé comme une **propriété d'architecture, pas un accident**. Déterminisme bit-exact, équivalence des pas de temps, introspection obligatoire.

### Ce qui existe maintenant ici

```
$ node scripts/verifier.mjs
VERIFIER — 14 garde(s), 3 mesure(s)
  ok   banc-moteur      19.1s  ✓ 4 épreuve(s), toutes tenues
  ok   banc-monde       10.9s  ...
  ok   banc-tick         1.0s  Toutes les epreuves sont tenues.
  ok   tests-python      0.4s  OK
  ...
  Toutes les gardes tiennent (54.7 s).
```

Point par point contre la première passe :

- **`banc-moteur` tourne sans serveur.** Il mesure même deux cuissons dans la même session pour prouver que la graine se ressème, et se compare à l'étalon en annonçant les fichiers de la chaîne qui ont changé depuis. Le `TypeError: fetch failed` a disparu.
- **Une commande unique existe**, plus riche que ce qui était recommandé : la distinction **gardes** (un rouge barre la route) / **mesures** (elles disent un chiffre, elles ne barrent rien) est une bonne idée que `batailles` n'a pas — `fumee.mjs` n'a que des passes et des échecs, et range donc ses chiffres d'observation dans des tests qui n'ont pas d'avis à donner.
- **`banc-tick` existe** : la recommandation 3.3 (un étalon pour les 3 214 lignes de `tick.py`) est faite.
- **`package.json` et `pyproject.toml` existent**, avec `npm run verifier`. Le `package.json` fantôme du dossier utilisateur ne gouverne plus l'exécution de ce dépôt.
- **Un seul banc reste attaché à un serveur** — `banc-epreuve`, et il est déclaré **mesure**, pas garde : il ne barre pas la route. C'est un choix défendable, pas une dette.

Reste en l'état : **4 tests unitaires Python pour 127 fichiers**, et **59 `sys.path.insert`** (le rangement en a ajouté trois en remontant les imports). L'amorce de sept lignes décrite dans `657cfb3` est propre — elle n'expose que la racine et `noyau/` — mais elle reste répétée dans chaque fichier au lieu d'être résolue par le `pyproject.toml`, qui existe désormais.

### Recommandations

**3.1 — Commiter `verifier.mjs`, `package.json`, `pyproject.toml`, et les bancs headless.** Toute la §3 vit dans l'arbre de travail. C'est la chose la plus rentable à faire aujourd'hui : elle transforme une journée de travail en socle.

**3.2 — Brancher `verifier.mjs` sur un hook.** Il tient en 55 s : c'est trop long pour un `PostToolUse`, juste pour une fin de session (`Stop`) sur les seules gardes rapides. `batailles` lance sa fumée « après tout changement de sim » — ici, la même règle mérite d'être mécanique plutôt que mémorielle.

**3.3 — Remplacer les 59 `sys.path.insert` par le `pyproject.toml`.** Il est là ; l'amorce fait maintenant double emploi. C'est 59 fichiers qui perdent sept lignes chacun, et des imports qu'un outil peut enfin vérifier.

---

## 4. Écrivains de `etat/` — porte posée, sémantique tranchée, migration devant

### Mesures

- **`scripts/noyau/tables.py` existe** : `lire(nom, defaut)`, `ecrire(nom, valeur)` atomique, une seule implémentation.
- La sémantique est **tranchée et écrite** : *un JSON abîmé plante ; seule l'absence rend le défaut.* C'est la recommandation 4.2, adoptée dans le bon sens.
- Les **quatre `lire_json` divergents** sont devenus quatre délégations à la porte, chacune portant la même docstring qui raconte la divergence supprimée. La classe de bug la plus coûteuse de la première passe est fermée.
- **5 fichiers importent la porte ; 43 écrivent encore sans elle** — et ce dernier chiffre est produit par `tables.py --verifier`, branché dans `verifier.mjs` comme **mesure**, avec le commentaire juste : « ce chiffre ne doit que descendre — il se migre un fichier par commit, pas en un geste aveugle ».
- Les **6 scripts jetables** (`_alys_ouvre_cahier.py`, `_wenna_grave_90381.py`, …) sont supprimés.

C'est exactement la forme que la première passe demandait, avec une amélioration : la règle n'est pas seulement testable, elle est **comptée en continu et affichée à côté des gardes**. Un chiffre qui ne descend pas se voit.

### Recommandations

**4.1 — Migrer les 43, un par commit.** L'ordre naturel est celui du risque : d'abord ce qui écrit `books.json`, `annales.json`, `journal.json` — la mémoire du jeu — puis les périphériques.

**4.2 — Quand le compteur atteindra zéro, promouvoir `porte-etat` de mesure en garde.** C'est le geste qui transforme une convention en frontière, et c'est l'équivalent exact du `expose.js` de `batailles` (« aucun autre moyen d'écrire n'existe »). Le noter maintenant, dans `verifier.mjs`, pour que le jour venu ce ne soit pas une décision à reprendre.

---

## 5. Le dépôt lui-même — résolu pour les sauvegardes, les binaires restent

### Mesures

| | 1re passe | aujourd'hui |
|---|---|---|
| fichiers `*.avant-*` suivis | 99 (261 Mo) | **0** |
| binaires suivis | 451 (340 Mo) | 450 (**287 Mo**) |
| fichiers suivis | 2 923 | 2 839 |
| commits | 75 | 76 |

Le `.gitignore` ferme `*.avant-*`, `*.avant`, `*.bak` et `etat/activations/*.log.jsonl`, avec le raisonnement écrit au-dessus des lignes — la bonne pratique de ce dépôt, et l'endroit exact où elle doit vivre.

Reste : **287 Mo de binaires**, dont un `.m4a` de 42,6 Mo dans `docs/`, et un `.git` à 450 Mo qui garde l'historique des 99 sauvegardes. Le poids historique est acceptable ; ce qui comptait était que la centième n'arrive pas, et c'est acquis.

**5.1 — Les gros médias méritent un dossier ignoré ou du LFS.** 42,6 Mo de `.m4a` dans `docs/` alourdissent chaque clone pour un document que personne ne lit dans un terminal. Opération sans urgence.

**5.2 — Si les 261 Mo dans `.git` gênent un jour**, `git filter-repo` sur ces seuls chemins est l'opération à faire *une fois*, à froid, avec une copie du dossier de côté. Pas dans la foulée d'un audit.

---

## 6. Documentation — de 1 CLAUDE.md à 12

### Mesures

| | 1re passe | aujourd'hui |
|---|---|---|
| fichiers `CLAUDE.md` | 1 | **12** (racine + 10 dossiers de `scripts/` + …) |
| `CLAUDE.md` racine | 123 Ko | 123 Ko |
| `AGENTS.md` | 127 Ko, **diverge de 356 lignes** | 127 Ko, **diverge toujours de 356 lignes** |
| fiches `docs/combat/` | 63 | 64 |
| doc d'architecture réelle | absente | `docs/architecture.md` (arbre de travail) |

Deux vraies avancées :

- **Chaque dossier de `scripts/` a sa fiche** — intention, ce qui entre, ce qui sort. C'est la convention de `batailles` (« les pourquoi vivent dans les CLAUDE.md ; les fichiers code ne portent que les contrats »), appliquée là où il n'y avait aucune carte.
- **`docs/architecture.md`** décrit pour la première fois l'architecture *actuelle* (containers, modules réels, liens), en annonçant sa convention et, mieux, sa **différence de nature** avec `batailles` : ici, la moitié des « processus » sont des sessions LLM et la mémoire de tout le monde est le disque. C'est une décision actée, pas une imitation.

### Ce qui reste

**6.1 — `AGENTS.md` diverge toujours de `CLAUDE.md` de 356 lignes.** Deux documents d'instructions de ~125 Ko qui ne disent pas la même chose, et rien ne dit lequel fait foi. C'est le dernier point de la première passe resté intact, et c'est celui qui coûte le plus cher *par session* : chaque tour de jeu charge l'un ou l'autre. Générer `AGENTS.md` depuis `CLAUDE.md` (ou l'inverse) est un script de quinze lignes ; une **mesure** dans `verifier.mjs` (« N lignes de divergence ») coûte trois lignes et suffit déjà à empêcher que l'écart grandisse.

**6.2 — Découper le `CLAUDE.md` racine.** 123 Ko chargés à chaque session, quand `batailles` charge un index de 40 lignes et laisse chaque container porter le sien. Le mouvement est commencé (12 fiches) : il reste à *retirer* de la racine ce que les fiches disent déjà, ce qui est la moitié du bénéfice et n'a pas encore été fait — la racine n'a pas maigri d'un octet.

**6.3 — Le graphe n'est toujours pas généré depuis le code.** `batailles` régénère `coding/graph/ARCHITECTURE.md` depuis le câblage réel et **liste les écarts avec les CLAUDE.md**. Ici, `docs/architecture.md` et les 64 fiches de `docs/combat/` sont écrits à la main : ils décrivent une cible, et rien ne mesure la distance. La pièce manquante est modeste — `chaine.js` connaît déjà les fichiers du moteur et leur ordre ; un script qui en extrait les globales **posées** et **lues** émet le graphe réel et la liste des dépendances qui *remontent* (les violations de la loi n°1). C'est ce qui transformerait la doctrine des dix couches d'une intention en une mesure — et `verifier.mjs` existe désormais pour l'accueillir.

**6.4 — Les « pourquoi » restent dans les en-têtes de code.** `bataille2d.js` ouvre sur 57 lignes de doctrine, `hasard.js` sur 28, `chaine.js` sur 30, `tables.py` sur autant. La prose est excellente ; l'endroit reste discutable pour un fichier de 10 000 lignes que personne n'ouvre pour lire une décision. À chaque extraction, **déplacer** le pourquoi vers la fiche de couche et ne laisser que le contrat. Les 64 fiches existent, elles attendent ce contenu.

---

## 7. Ce qui est conforme, et qu'il ne faut pas casser

- **Le hasard est unique et rejouable** — `hasard.js` : un LCG, une graine, `semer()` au dressage, et `banc-moteur` prouve désormais *à chaque exécution* que deux cuissons d'une même session rendent la même bataille. Une fuite reste à fermer : le repli `H ? H.R() : Math.random()` de `corps-adapt.js:386`. S'il n'y a pas de hasard chargé, ça doit planter, pas dériver.
- **Les gardes à tolérance zéro** — « un écart non nul n'est pas une tolérance à élargir, c'est la reproductibilité qui est cassée ». Meilleure formulation que « test de fumée ».
- **La séparation gardes / mesures** de `verifier.mjs` est une idée que `batailles` gagnerait à reprendre.
- **Les annales** (« un comportement qui n'émet rien n'existe pas ») sont l'équivalent de l'`introspect()` obligatoire, appliqué aux *faits* — donc plus exigeant.
- **Les messages de commit** portent le raisonnement, les mesures, ce qui a été écarté, et jusqu'aux pièges trouvés en chemin. `657cfb3` explique même comment la vérification a été faite *sans rien exécuter d'écrivant*, après qu'une passe naïve a réinitialisé `etat/flux.jsonl` — et la leçon est écrite dans le CLAUDE.md du dossier concerné, pas seulement dans le commit.
- **Aucun secret en dur**, `.env` ignoré, clés lues par l'environnement.
- **Le français est tenu partout.**

---

## 8. Plan d'action — ce qui reste, dans l'ordre

| | Action | Coût | Débloque |
|---|---|---|---|
| **1** | **Commiter le chantier en cours** : `verifier.mjs`, bancs headless, `package.json`, `pyproject.toml`, hook `taille.js`, `.gitignore`, `tables.py` (§3.1, §1.1) | ~30 min | tout le reste ; une journée de travail devient un socle |
| **2** | Mesure `chaine` dans `verifier.mjs` : N balises `<script>` hors manifeste (§2.2) | ~20 min | l'écart qui vient d'empirer, visible le jour même |
| **3** | Mesure `agents-claude` : N lignes de divergence entre les deux manuels (§6.1) | ~10 min | empêche l'écart de grandir avant même de le résorber |
| **4** | `chaine.js` pose les balises ; `?v=` calculé par le serveur (§2.1, §2.3) | ~2 h | les 100 balises en dur, le cache périmé |
| **5** | Migrer les 43 écrivains vers la porte, un par commit ; puis promouvoir `porte-etat` en garde (§4.1, §4.2) | ~3 h étalées | la frontière mécanique sur `etat/` |
| **6** | Retirer du `CLAUDE.md` racine ce que les 12 fiches disent déjà (§6.2) | ~2 h | 123 Ko chargés à chaque session |
| **7** | `pyproject.toml` au lieu des 59 `sys.path.insert` (§3.3) | ~1 h | 59 fichiers × 7 lignes, des imports vérifiables |
| **8** | Le graphe généré depuis `chaine.js`, écarts listés, branché en mesure (§6.3) | ~4 h | rend la doctrine des dix couches mesurable |
| **9** | Découper `serveur/serveur.js` par famille de route (§1.3) | chantier | 6 345 lignes sans fiche ni frontière |
| **10** | Extraire `soldat()` (858 l.) en états nommés (§1.2) | chantier | le reste de l'architecture cible — **et le filet existe enfin** |

Les trois premières lignes tiennent en une heure. La dixième est le vrai sujet du dépôt, et la nouveauté de cette passe est qu'elle est **devenue faisable** : un étalon vert, headless, qui tourne en 55 secondes et refuse tout écart, est précisément ce qui manquait pour oser toucher une fonction de 858 lignes.

---

*Méthode : mesures produites par `scripts/analyse/audit_technique.py` (lecture seule, aucun script du dépôt importé) sur `657cfb3` du 30/8/2026, arbre de travail inclus et signalé comme tel. `node scripts/verifier.mjs` et `node ecrans/modules/bataille/banc-moteur.js` ont été exécutés pour établir §3. Les standards de comparaison sont les `CLAUDE.md` de `C:\Users\reyno\batailles` (racine, `src/`, containers) et son outillage `coding/` et `.claude/hooks/`.*
