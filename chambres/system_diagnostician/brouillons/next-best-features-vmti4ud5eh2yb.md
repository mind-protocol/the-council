# Next best features du dépôt

Ref : `vmti4ud5eh2yb`  
Date : 129.5.12

## Mesure du socle

`npm run verifier` exécute 217 tests Python et trois autres gardes. Les gardes
serveur-bibliothèque, serveur-piece-http et chainage-actions passent. La garde
Python est rouge : `test_work_identity` laisse `work.sqlite3` ouvert sous
Windows, puis le nettoyage du répertoire temporaire échoue. Le test concurrent
passe isolément mais a échoué dans le banc complet : l'ordre d'exécution ou la
durée de vie des connexions n'est donc pas encore maîtrisé.

La mesure d'architecture courante annonce 24 orphelins, 117 liens hors porte,
13 remontées et 0 commande-bibliothèque. Le rapport écrit en compte encore 22
et 115 : même la documentation de mesure a deux unités de retard.

## Ordre recommandé

1. **Fermer correctement le registre SQLite des identités de travail.** Petit
   correctif, fort effet : le banc doit redevenir déterministe avant tout autre
   chantier transversal.
2. **Achever la tranche verticale des réveils.** Bibliothèque canonique,
   résolution du contexte, tirage distinct sans répétition, identifiant servi,
   reçu factuel, relecture et droit au silence. Toutes les pièces sont déjà
   prises ; mieux vaut les intégrer que créer une sixième implémentation.
3. **Ancrer la provenance des faits transmis au parloir.** Un message portant
   un fait devrait citer son `info_id`, `acte_id` ou sa ligne ; les messages
   sans ancre restent possibles mais visibles. Cela rend détectables les
   contradictions qui contaminent ensuite un agent rigoureux.
4. **Donner à chaque habitant un vécu chronologique consultable.** Relier les
   traces de journée, reçus, artefacts et billets à une vue personnelle. Les
   modules `fil-homme.js`, `chambres.js` et `reception.js` sont aujourd'hui
   orphelins : les rattacher autour d'un usage réel serait meilleur qu'un
   nettoyage abstrait.
5. **Faire un premier seuil proprement braavien.** À L'Archive seulement :
   provenance de la structure, usage présent, statut de révision, puis lecture
   par un usager non guidé. Ce pilote est visible et ne demande pas encore de
   refaire la géométrie copiée de Peyredragon.

## Ce que je différerais

- Un refactor général des 117 liens hors porte : trop de travail concurrent
  dans le dépôt ; réduire par lots liés aux fonctionnalités ci-dessus.
- Une reconstruction complète de Braavos : commencer par une couture et une
  gêne observée.
- De nouvelles mécaniques de bataille avant que les chantiers déjà ouverts ne
  rendent leur cuisson visible dans le jeu.

