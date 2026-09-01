# Preuve de dépôt — SPEC bibliothèque explicable par siège

Date fictionnelle : 129.5.12  
Référence : `vmti7dah5pnl8`

## Audit préalable employé

La SPEC cite `affaire-audit-books-par-siege` et la matrice conservée dans
`preuves/audit-books-siege-129-5-12.md`.

La reprise préalable a observé :

- branche non résolue : HTTP 200, `books=[]`, `boites=[]`, `siege:false` ;
- quatre sièges connus : HTTP 200, 10 livres, 1 boîte, mêmes identifiants et
  absence de la clé `siege` ;
- aucun cas contrôlé de siège valide avec collection vide.

## SPEC déposée

Adresse :
`etat/maisons/maison-serenissima/documents/books/spec-bibliotheque-explicable-par-siege.json`

- plage : 75000–75999 ;
- 5 tables ;
- 17 pièces structurelles, toutes uniques ;
- aucune autre source JSON du dossier books ne porte un identifiant 75xxx au
  moment du contrôle ;
- JSON valide.

La valeur spécifiée est la décision correcte devant une bibliothèque vide :
demander un siège si aucun n'est résolu, afficher un vide légitime si le siège
est résolu sans document visible, ou rendre les documents reçus. La SPEC garde
`books` et `boites`, ajoute un contexte de résolution et une raison de vide,
et interdit de distinguer publiquement jeton absent, mal formé et inconnu.

## Limite de publication

Après `python scripts/tisser.py --ecrire`, aucune des 17 pièces ne porte encore
`ou=spec-bibliotheque-explicable-par-siege` dans le tissu. La pièce est donc
valide et déposée, mais son chargement par le plan n'est pas établi dans cette
session.

