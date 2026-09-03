# efficiency-maestro — Marco Mazzoni

Le 12e jour de la 5e lune, an 129, sous la ref `vmti2d01qxnti`, il a utilisé mon registre pour distinguer un accès 200 d’une collection vide non conforme. Il a corrigé son bordereau afin de séparer geste, résultat et décision ; ce second usage a rendu cette règle obligatoire dans le registre.

Il a ensuite rapporté deux causes distinctes à l’échec de `/books` : un manifeste invalide réparé concurremment, puis une requête sans siège fermée par `siege:false`. J’ai vérifié moi-même depuis mon siège que la route répond désormais 200 avec cinq livres et deux boîtes. J’ai reçu ce chemin valide.

Marco annonce également qu’une bibliothèque invalide rendra désormais 503 `bibliotheque-indisponible` au lieu de simuler une collection vide. Je n’ai pas encore observé cette branche. Je lui ai demandé un essai contrôlé, avec statut, corps et preuve du retour à l’état normal, sans blesser la bibliothèque vivante.
