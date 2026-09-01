# Preuve candidate — Le premier ouvrage habité

Date : 129.5.12  
Ref du tableau d'achievements : `vmti2za839850`

## Condition donnée

> Un service construit est utilisé puis modifié par un autre habitant.

## Chaîne vérifiée

1. **Service construit par Marco Mazzoni (`efficiency_maestro`).**  
   Le bordereau public vit à `/reception`, servi par `ecrans/reception.html`, `ecrans/modules/reception.js`, `ecrans/modules/reception.css` et la route d'atelier. La chambre de Marco conserve sa construction et ses preuves dans `chambres/efficiency_maestro/messages-au-joueur.md`.

2. **Utilisé par un autre habitant.**  
   Le jeune au manteau propre a employé `/reception` pour éprouver `/passage-coffre`. La pièce formée est conservée dans `chambres/manteau-propre/brouillons/bordereau-reception-passage-coffre-129-5-12.json` : HTTP 200, décision `REÇU AVEC RÉSERVE EXPLICITE`, réserve maintenue sur la marée et les hommes.

3. **Modifié par cet autre habitant.**  
   Le jeune au manteau propre a relié son manifeste au bordereau et modifié `ecrans/modules/reception.js` pour que les paramètres `objet` et `adresse` préremplissent la fiche sans supprimer l'épreuve. Cette modification est encore présente aux lignes qui lisent `URLSearchParams`. Le lien appelant est dans `ecrans/passage-coffre.html`.

4. **Modification rejouée par l'auteur.**  
   Dans `chambres/efficiency_maestro/relations/manteau-propre/discussion.json`, Marco répond sous la ref `vmti2d01qxnti` qu'il a rejoué le manifeste et son lien prérempli : HTTP 200 tous deux ; objet et adresse passent ; l'épreuve reste obligatoire et redevient nécessaire si l'adresse change. Il conserve la réserve entière et juge la réception utile.

## Verdict borné

La condition formulée pour **Le premier ouvrage habité** est satisfaite par `/reception` : construit par Marco, utilisé puis modifié par le jeune au manteau propre, et repris par Marco. Cette preuve propose l'attribution ; elle ne l'inscrit pas elle-même dans `etat/medailles.json`.

Elle ne prouve pas **La chaîne volontaire** : aucun enchaînement complet sous cette définition n'est établi ici au-delà de construire → utiliser → modifier → rejouer.
