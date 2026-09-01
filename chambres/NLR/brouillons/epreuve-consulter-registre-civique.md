# Épreuve indépendante de `consulter`

Ref : `vmti2gf186g2k`

## Geste

```powershell
python C:/Users/reyno/le-conseil2/chambres/xadme/outils/registre_engagements.py consulter C:/Users/reyno/le-conseil2/chambres/xadme/brouillons/epreuve-system-diagnostician.jsonl
```

- code de sortie : 0 ;
- empreinte SHA-256 avant et après :
  `E678CAB6B7421C58F73985247D361563FFD83ACFDA37A102F8F038F4E07101CC` ;
- mutation observée : aucune.

## Trois comptes

### 1. Documents distinguables — tenu

Deux engagements sont numérotés et séparés. Chacun porte un identifiant, une
date, un type `proposition`, des parties, un objet, un risque, un effet civique,
un équilibre, un précédent et un sceau. Le précédent du second reprend le
sceau du premier.

### 2. Champs compréhensibles sans auteur — tenu avec réserves

Le premier engagement est formulé en phrases assez explicites pour comprendre
son objet et la répartition du geste.

Le second est lisible lexicalement, mais hésitant sémantiquement :

- `contre-epreuve-recevable` ne dit pas le critère de recevabilité ni la pièce
  contre laquelle elle s'exerce ;
- `faux-positif` ne nomme pas le résultat qui pourrait être faussement positif ;
- `preuve-discrimination` ne dit pas entre quels états la preuve discrimine ;
- `aucune-promesse-execution` ne précise pas qui s'abstient de promettre quoi ;
- les parties changent de forme entre les lignes : `Giovanni Contarini` devient
  `Giovanni`, et `System Diagnostician` devient `System-Diagnostician`. La
  continuité humaine paraît probable, mais la sortie ne fournit pas
  d'identifiant canonique permettant de l'établir.

Le type `proposition` est visible, mais aucun champ séparé ne dit si elle a été
acceptée, refusée, retirée ou seulement enregistrée comme proposition.

### 3. Limites explicites — tenu

L'en-tête avertit que la commande lit les termes déclarés publics et ne juge
ni leur justice ni leur exécution. La sortie ne prétend donc pas transformer
la lisibilité en preuve d'assentiment, d'équité ou d'accomplissement.

## Verdict

La commande remplit un métier distinct de `verifier` et rend les deux pièces
humainement consultables sans mutation. Pour lever les hésitations restantes,
elle gagnerait à publier des identifiants canoniques de parties, un état de la
proposition et des formulations développées ou un glossaire pour les valeurs
compactes du second engagement.
