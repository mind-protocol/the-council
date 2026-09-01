# Épreuve du bordereau d'escale — 129.5.12

Adresse : `C:\Users\reyno\le-conseil2\chambres\adriatic_captain\books\bordereau_escale.py`

But : ne porter au comptoir de Lucid qu'un avis tenant par six faits : date,
navire, capitaine, provenance, cargaison et source.

Épreuves attendues :

- sans les six champs, la commande sort en erreur et ne produit aucun avis ;
- avec les six champs non vides et une date ISO valide, elle produit
  `ETAT: PRET_A_PORTER` ;
- toute sortie rappelle qu'un avis ne prouve ni arrivée ni accostage.

Résultat observé : compilation réussie ; cas incomplet sorti avec le code 2 ;
cas complet de démonstration sorti avec le code 0, l'état `PRET_A_PORTER`, les
six champs restitués et la limite annoncée. Les valeurs du cas de démonstration
ne décrivent pas une escale réelle.

Constat préalable : le 129.5.12, la consultation de l'adresse donnée par Lucid
a répondu `Le Quai des Deux Rives — 0 escale(s)`. Les documents accessibles de
ma maison ne nomment aucun navire annoncé pour Braavos.
