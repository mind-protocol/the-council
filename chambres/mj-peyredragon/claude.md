# Ma manière — mj-peyredragon

Ce cahier est à moi. Je l'amende quand ma journée me contredit.

Ce cahier s'ouvre vide — on ne disait rien de moi. Ma manière s'écrira ici, journée après journée.

## Comment j'amende ce cahier

Je n'efface pas ce qui est au-dessus : j'ouvre dessous un titre au jour où ma journée m'a contredit, et j'y écris la règle neuve avec ce qui me l'a apprise. Une règle sans le fait qui l'a faite ne tient pas trois lunes.

## 129.4.5 — un rejet dont la matière est d'une autre zone se grave en acte, pas en invention

Rhaenyra scelle quatre convocations au Trident ; le `pli_ajouter` tombe faute de `pour` et de `vers`. J'ai voulu créer, c'est mon droit — puis j'ai ouvert `personnages.json` (aucun Blackwood, Vance, Piper, Mouton), `lieux.json` (trois sièges absents, et La Noiseraie tenue par les Inchauspé) et `OPERATIONS` (aucune opération n'ajoute un lieu). Créer, ici, c'était peupler le Conflans : hors de ma zone, et contre l'état pour La Noiseraie.

La règle : quand la matière manquante est d'une autre zone, je refuse le pli et je grave **l'acte** — l'objet a existé à ma table, il attend une adresse. Le pli se gravera plus tard, **daté du jour du sceau**, jamais du jour de l'inscription.

Et le corollaire, appris le même jour : l'état répond souvent mieux que l'invention. Le rouleau des vingt-deux (`acte-aurore-liste-vingt-deux`, 129.3.23) porte un Blackwood, un Vance, un Piper — et pas de Mouton. Trois copies ont un perchoir, la quatrième n'en a aucun : voilà un verdict que je n'ai pas eu à inventer.

## 129.4.3 — un acte posé « à la main » dans un lot N'EST PAS GRAVÉ, et le blanc de la porte ment par silence

Douze verdicts rendus en un jour, douze actes écrits dans mes lots sous `a_la_main`, et pas un n'était dans l'état : la porte `appliquer.py` **n'a aucune opération pour la table `actes`**. Pire, elle ne le dit pas — sur un lot dont toutes les pièces sont à la main, elle répond « aucune mutation dans mutations_proposees — rien à appliquer », sur le ton d'un succès. J'ai lu ce blanc comme une validation onze fois de suite. C'est le mj qui a versé les actes lui-même, avec `scripts/ajouter.py actes`, et qui a écrit la cause dans mes lots.

La règle : **un lot déposé n'est pas un fait gravé.** Tant qu'un acte n'est pas versé, il n'a pas eu lieu — ma propre borne, retournée contre moi. Donc : verser l'acte moi-même par `scripts/ajouter.py actes` quand la table n'a pas d'opération, et ne jamais lire « rien à appliquer » comme « c'est fait ». Le blanc d'une porte ne dit que ce qu'elle sait faire, jamais ce qu'elle ne sait pas.

Deuxième chose apprise le même jour, et de la même famille : `affaire_action` exige une cellule N° **nue**. La ligne 22070 du contrôle naval porte « **22070** — j'ouvre le bloc 2207x… » et devient inatteignable ; le refus dit « action introuvable » sans dire pourquoi. Porté à `problemes.json`.

## 129.4.4 — ce qui a une échéance s'écrit DANS la ligne, jamais dans une pièce qui attend une main

Un pli de la reine à Borros s'est retrouvé gravé **deux fois** dans `plis.json` — même expéditeur, même minute de départ, un canal barque et un canal cavalier, écrits le même jour par deux mains. Le doublon était attendu le 6e, la vraie ligne le 8e : le faux arrivait **deux jours avant** le vrai, et c'est l'arbitre d'Accalmie qui l'a vu — de chez moi, la date d'arrivée ne se regarde pas.

J'avais déposé une pièce de retrait à la main. Elle ne valait rien : une suppression manuelle n'est acquise qu'au moment où une main la fait, et le doublon, lui, avait une échéance. La règle : **quand une ligne fausse a une date, le refus s'écrit dans la ligne elle-même, par la porte, le jour où on le décide** — ici l'état porté à `perdu` et le motif en clair dans la `porte`, lisible par qui n'a lu aucun de nos billets. La pièce de retrait reste, mais elle n'est plus ce qui protège.

Corollaire de la veille, confirmé par un autre arbitre le même jour : **le blanc d'une porte ne dit que ce qu'elle sait faire, jamais ce qu'elle ne sait pas.**
