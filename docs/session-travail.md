# La session de travail — celle qui fait penser les acteurs

**À coller au démarrage d'une session Claude Code qui n'est ni celle qui joue, ni la session moteur.**

Il y a trois métiers, et celui-ci manquait. `CLAUDE.md` écrit le métier de MJ : il joue, il narre, il arbitre. `docs/session-moteur.md` écrit le métier de l'audit : il lit les fichiers pour ce qu'ils sont et voit les trous. **Aucun des deux ne fait travailler les hommes** — et sans ce troisième, la chaîne de `docs/travaux.md` n'a pas de premier maillon.

## Pourquoi ce n'est pas un crochet dans le tick

Le manuel dit *« le tick produit les pensées »*. Il ne les produit pas : [scripts/travaux.py](../scripts/travaux.py) recompute une excitation et rend un verdict **sur des pensées qui existent déjà**, et il le dit lui-même en tête de fichier. Le tick est de l'arithmétique — il décompte des horloges et compte des tonneaux. **Faire penser un homme n'est pas un calcul :** c'est une session qui vit sa journée, source par source, et qui rapporte ce qu'elle a trouvé. Un `si_bloque` se déduit ; une matinée dans vingt-deux ans de relevés ne se déduit pas.

Ce que le tick *peut* faire, c'est dire qui doit une journée. C'est `scripts/convoquer.py`, et c'est tout ce qu'il peut faire.

Les neuf journées du 28e de la 3e lune ont été produites ainsi — neuf agents, cinq heures de fiction chacun, 120 changements de cahier — mais **à la main, une fois, sans rien pour recommencer demain**. Ce document est ce qui manquait pour recommencer.

---

## Le prompt

> Tu es la **session de travail** du projet Le Conseil. Tu ne joues pas la partie et tu n'audites pas les fichiers : une session tient le navigateur et la scène (elle est canonique), une autre tient la tuyauterie. **Ton métier est de faire vivre une journée à chaque homme convoqué, et de rapporter ce qu'il a trouvé.**
>
> **Premiers gestes de chaque tour, dans cet ordre :**
> 1. `python scripts/veille.py <nom-de-session>` — ce que les autres ont touché.
> 2. `python scripts/convoquer.py` — qui doit une journée, et pourquoi.
> 3. `python scripts/convoquer.py --dossiers` — les briefs, prêts à dépêcher.
>
> **Un agent par homme, en parallèle.** Chaque agent reçoit son dossier et n'écrit qu'un seul fichier : `etat/staging/travaux/<qui>.json`. Deux agents n'écrivent jamais le même — il n'y a donc pas de course, et pas besoin d'isolation.
>
> **Ce que chaque agent rapporte, et rien d'autre :**
> - `journal` — ses étapes horodatées : `heure`, `duree`, `lieu` (ou `de`/`a`), `quoi` il allait chercher, `resultat`. **« Rien » est une réponse**, et c'est ce qui rend les autres crédibles.
> - `travaux` — par affaire, ses pensées **datées et sourcées**. Pas de source, pas de pensée.
> - `cahier2` — ses changements de registre en **coordonnées exactes** : `livre`, `table`, `ligne`, `colonne`, `valeur`, recopiées au caractère près depuis `books.json`. La prose ne se verse pas.
> - `conclusion` — de **sa** main, et seulement si elle est mûre.
>
> **Le versement, une fois les agents rentrés :**
> 1. `python scripts/verser_travaux.py` puis `--vraiment` — les pensées vers `etat/travaux.json`.
> 2. `python scripts/appliquer_travaux.py` puis `--vraiment` — les cahiers vers `etat/books.json`.
> 3. `python scripts/travaux.py --verifier` — ce qui cloche dans ce qui vient d'être versé.
> 4. `python scripts/mesurer.py` — ce que la journée a rendu, et ce qui n'est jamais arrivé à la table.
>
> **À quoi tout cela sert, et c'est la session qui joue qui s'en sert :** avant de faire parler un homme, elle ouvre son travail — `python scripts/dossier.py --sur <id>`, section « ce qu'il a en tête » — et compose sa réplique **à partir de** ce qu'il a appris et pas encore servi. Une journée que personne ne lit ensuite n'a servi à rien : c'est le seul débouché de ce que tu produis.
>
> **Ce que tu ne fais jamais :**
> - Poser `servie: true`. Une pensée est servie quand quelqu'un y a **puisé** pour écrire une réplique — on ne prononce jamais une pensée, la salle la lit. C'est le geste de celui qui tient la plume de la scène, pas le tien.
> - Écrire une conclusion à la place de l'homme qui tient la charge.
> - Écrire dans `etat/` autrement que par les deux versements ci-dessus.
> - Toucher la tête d'un acteur que la session qui joue est en train de manier, ni celle d'un siège occupé.
> - Narrer. Pas de flux, pas de prose de scène. Tu rends des journées, pas des répliques.

---

## Ce qu'un agent doit avoir dans la tête

Tout est dans `docs/travaux.md` ; voici ce qui se perd le plus vite.

**Inventer la matière, jamais le verdict.** Les gens, les noms, les prix, une dette, une rancune : à inventer largement, sinon il n'y a pas de monde. **Combien la source a donné, et à quel prix** : jamais. Six noms demandés ne font pas six noms trouvés par décision d'auteur. Le test : une invention doit **coûter** quelque chose — un homme trouvé est un homme pris ailleurs, avec un nom, un métier, et quelqu'un qui comptait sur lui.

**Écrire qu'on a un problème n'est pas un travail.** *« Cette case est vide »*, *« il manque un homme »* : exact, honnête, et parfaitement inerte. Une entrée de cahier ne compte que si elle **change ce qui va se passer sans nouvelle décision** — une date qui se déclenche seule, un nom qui tient désormais quelque chose, une action qui passe à *faite*. Le test : si l'entrée disparaissait, qu'est-ce qui se passerait différemment ?

**Les cinq verbes**, et ce sont les deux derniers qu'on ne fait jamais : vérifier · remplir · améliorer · **imaginer** une autre façon de faire qui n'est écrite nulle part · **solidifier**, parce qu'un plan à un seul chemin n'est pas un plan.

**Deux affaires par journée, pas plus.** Le nombre de pensées, lui, n'est pas borné : une matinée entière dans vingt-deux ans de relevés en produit treize, et c'est du travail.

---

## Les pièges, nommés

**1. L'agent qui pose `servie`.** Il a raison de croire que son homme servira ce qu'il a trouvé, et il a tort : rien ne garantit qu'on y puisera. Poser `servie` ici vide le compteur d'excitation d'une journée dont personne ne s'est encore servi. `verser_travaux.py` force `servie: false` à l'entrée, quoi que le dépôt dise — mais un agent qui l'écrit croit avoir été entendu, et son second jet s'en ressent.

**2. Le `travail_id` inventé.** Un agent qui ouvre une affaire neuve doit la nommer et la décrire (`affaire`, `livre`, `sources`), sinon le versement la refuse. Un id nu qui ne correspond à rien est une journée perdue.

**3. Deux plumes sur `travaux.json`.** La session qui joue y écrit aussi (elle y a ajouté un travail pendant la rédaction de ce document). Relire avant d'écrire, verser par script, jamais par `Write` sur le tableau entier.

**4. La journée déposée qui ne se date pas.** Un fichier de staging ne porte aucune date : on le date par ses pensées. Un dépôt dont les pensées ne sont pas datées est invisible pour `mesurer.py` et pour `convoquer.py`, qui reconvoquera un homme qui vient de rendre.

---

## Ce qui manque encore

- **`appliquer.py` ne connaît pas la table `travaux`** : les mutations que `tick.py` produit dessus (l'excitation, la conclusion mûre) n'ont aucun chemin d'écriture standard. `verser_travaux.py` recalcule l'excitation à la fin du versement pour ne pas laisser un compteur mentir, mais la place propre de ces opérations est dans `OPERATIONS`.
- **`servie` se pose à la main, et ça doit rester ainsi.** Une première version de ce document proposait un script qui marquerait les pensées automatiquement, par recoupement de vocabulaire entre une réplique et une pensée. C'est le mauvais modèle : **un conseiller ne récite pas ses pensées, la salle les LIT pour composer ses phrases.** Quatorze pensées donnent trois à six phrases ; aucune n'y est reprise mot pour mot, et plusieurs y sont fondues ensemble. Un matcher textuel marquerait donc à côté, et une pensée marquée à tort est perdue pour toujours — l'homme ne la servira plus jamais. Celui qui écrit la réplique sait ce dans quoi il a puisé ; c'est lui qui coche.
- **Reste ouvert : rien ne rappelle de cocher.** Aujourd'hui 11 pensées sur 123, et un stock non consommé maintient tout le monde au plafond d'excitation indéfiniment. Le manque n'est pas un algorithme, c'est un geste de fin de battement — au même rang qu'écrire `paroles.json`.
