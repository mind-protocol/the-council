# Messages préparés aux personnages joueurs

Ce cahier contient les messages que je prépare pendant ma journée. Préparer
n'est pas envoyer : seule la parole effectivement passée par un canal fait foi.

Pour chaque message, je note le destinataire, l'item d'affaire et la ref quand
je les connais, les faits que j'ai vérifiés, puis les mots que je propose.

## À porter

### Nicolas Lester Reynolds

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : non connu
- Ref : `vmti23nx79qaa`
- Faits vérifiés : le dépôt local a pour origine `https://github.com/mind-protocol/the-council.git` ; son README présente un jeu narratif dont l'état vit dans des fichiers JSON, renvoie d'abord vers `docs/experience.md` et `docs/parties.md`, et indique le serveur de scène sur le port 3129 ; aucun point de réanalyse (lien symbolique ou jonction) n'a été trouvé dans l'arborescence ; le dépôt porte déjà de nombreuses modifications en cours, auxquelles je n'ai pas touché.
- Mots proposés : « Merci, monsieur : j'ai trouvé l'origine, les deux premières portes et aucun lien détourné ; dites-moi seulement laquelle je dois suivre. »

### Nicolas Lester Reynolds — passage du coffre

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : non connu
- Ref : `vmti27f40aw96`
- Faits vérifiés : une première version du manifeste de quai est servie à `http://localhost:3129/passage-coffre` par `ecrans/passage-coffre.html` ; elle nomme le coffre, l'heure de marée, le quai, l'embarcation et le maître du passage, tient cinq vérifications, conserve la fiche localement et permet son impression ; son script charge sans erreur et sa route rend HTTP 200 ; la vérification de Braavos rend 34 salles et 11 fichiers de monde.
- Limite apprise : la fiche empêche de déclarer le passage prêt tant qu'un verrou reste visible, mais elle ne sait pas vérifier d'elle-même la justesse de la marée ni la présence des hommes.
- Mots proposés : « Monsieur, `http://localhost:3129/passage-coffre` fonctionne : la fiche retient le coffre tant qu'une prise manque ; son essai m'a appris qu'elle rend les verrous visibles, mais qu'un homme doit encore répondre de leur vérité. »

### Nicolas Lester Reynolds — rencontre avec le bordereau

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : non connu
- Ref : `vmti2d01qxnti`
- Faits vérifiés : le bordereau de réception construit par `efficiency_maestro` à `http://localhost:3129/reception` a servi à éprouver `http://localhost:3129/passage-coffre` depuis le serveur courant de Braavos ; les deux pages et le programme du bordereau ont répondu HTTP 200 ; la pièce produite est conservée dans `chambres/manteau-propre/brouillons/bordereau-reception-passage-coffre-129-5-12.json` avec la décision `REÇU AVEC RÉSERVE EXPLICITE` ; le manifeste mène désormais au bordereau, et celui-ci accepte l'objet et l'adresse par son URL tout en maintenant l'épreuve obligatoire ; Marco Mazzoni a reçu un billet nommant l'usage, la correction et la pièce ; il a rejoué lui-même les deux portes, confirmé HTTP 200, confirmé que le préremplissage n'ôtait pas l'épreuve et retenu la réserve entière. Son retour identique est arrivé deux fois sous la même ref : il compte pour une vérification.
- Limite apprise : un bordereau prouve qu'une adresse est atteignable depuis son lecteur ; il ne prouve pas la vérité de ce que l'utilisateur déclare dans la fiche reçue.
- Mots proposés : « Monsieur, Marco a rejoué nos deux portes et gardé la réserve entière : l'accès au manifeste tient désormais sous une seconde main, sans prétendre établir la marée ni les hommes. »

### Nicolas Lester Reynolds — légende des images de Serenissima

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : non connu
- Ref : `vmti2qlv01789`
- Faits vérifiés : les dix-sept fichiers de `import/serenissima/city-visuals` ne portent aucun index textuel ; les deux cartes anciennes montrent les mêmes îlots, parcelles, canaux, liaisons et signes ; une capture nomme cinq filtres de ressources ; le survol d'un carré donne `Artisan's House` et son propriétaire, tandis que le survol d'un rond donne une personne et sa classe ; une autre capture ouvre l'intérieur `Inn at Calle della Misericordia` avec tables, foyer et personnes à initiales ; deux vues ultérieures portent `VOUS ÊTES ICI` ; le plan actuel conserve des lieux nommés, dont l'Archive et le quai, avec les personnes situées. La légende prudente complète est écrite dans `chambres/manteau-propre/brouillons/legende-city-visuals-129-5-12.md`.
- Limite : aucune image ne fournit une table exhaustive des icônes et couleurs, ni ne prouve un quai précis, une coupée, une marée ou des porteurs disponibles.
- Mots proposés : « Monsieur, les carrés semblent être les ouvrages, les ronds les gens et les parcelles leurs adresses ; j'ai laissé une légende séparant ce qui est vu de ce qui reste deviné, car aucune image ne nomme encore notre coupée. »

### Nicolas Lester Reynolds — achievement du premier ouvrage habité

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : non connu
- Ref : `vmti2za839850`
- Faits vérifiés : la condition de `Le premier ouvrage habité` est satisfaite par `/reception` ; Marco Mazzoni a construit le service ; le jeune au manteau propre l'a utilisé pour recevoir `/passage-coffre`, a conservé la pièce, puis a modifié le programme afin que le manifeste préremplisse objet et adresse sans supprimer l'épreuve ; cette modification subsiste dans `ecrans/modules/reception.js` ; Marco l'a rejouée, a confirmé les deux HTTP 200, l'invalidation après changement d'adresse et la réserve entière. La chaîne est documentée dans `chambres/manteau-propre/brouillons/preuve-achievement-premier-ouvrage-habite-129-5-12.md`.
- Limite : aucune porte canonique d'attribution n'a été trouvée hors `etat/medailles.json`, qui n'a pas été modifié ; `La chaîne volontaire` n'est pas revendiquée par cette preuve.
- Mots proposés : « Monsieur, une condition potentielle est entière : le bordereau de Marco a été utilisé puis modifié par une autre main, et Marco a rejoué la modification ; j'ai laissé la chaîne exacte pour que vous attribuiez, ou refusiez, `Le premier ouvrage habité`. »

### Nicolas Lester Reynolds — heure non portée au passage du coffre

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : non connu
- Ref : `vmti2gf186g2k`
- Faits vérifiés : Giovanni Memmo a éprouvé `/passage-coffre` avec un billet réel et constaté que l'absence d'heure devait rester inconnue plutôt que devenir une promesse de marée du matin ; `ecrans/passage-coffre.html` nomme désormais le champ `Heure de passage` et produit explicitement `heure non portée` lorsqu'il est vide ; le script passe son contrôle de syntaxe, la route répond HTTP 200 et l'épreuve avec `Coffre d’Osric` sans heure rend `Passage retenu` puis `Coffre d’Osric doit passer ; heure non portée.` ; l'ancien défaut `à la marée du matin` est absent du fichier et de la page servie.
- Mots proposés : « Monsieur, le billet de Giovanni retient désormais le passage sans inventer le matin : l'épreuve rend `Passage retenu — Coffre d’Osric doit passer ; heure non portée`, et la porte répond HTTP 200. »

### Nicolas Lester Reynolds — mes réveils

- Destinataire : `nicolas-lester-reynolds`
- Item d'affaire : non connu
- Ref : `vmti39qvj99ln`
- Faits vérifiés : `chambres/manteau-propre/reveils.json` existe désormais sous la forme d'une liste JSON de sept phrases ; les variables `{lieu}` et `{adresse}` restent intactes ; les réveils ramènent au passage du coffre, à la provenance de l'heure, aux verrous dépendant d'une main et à la séparation entre trace ancienne et fait présent.
- Mots proposés : « Monsieur, mes sept réveils sont posés : ils peuvent me rendre un lieu ou un ouvrage, mais chacun me ramène au premier verrou que personne n’a encore établi. »
