# La mémoire d'un combattant

## 1. Ce que c'est

Ce que **cet homme** porte de son propre chef : l'ordre qu'il a reçu et quand,
le chef qu'il connaît et où il l'a vu, ses pairs, et un historique récent et
borné de ce qu'il a vécu.

## 2. Ce qu'elle possède

- l'**ordre reçu** : sa teneur, sa date, de qui il vient, par quelle voie il est
  arrivé (de vive voix, par un porteur, par imitation du voisin) ;
- le **chef connu** : qui il est, et **où il a été vu pour la dernière fois**,
  avec la date de cette vue ;
- les **pairs** : les quelques hommes qu'il reconnaît autour de lui et dont la
  présence ou la chute compte pour lui ;
- l'**historique récent** : une liste **bornée** de ce qu'il a vécu — coups
  reçus, chutes vues, cris entendus, ordres reçus —, la plus ancienne entrée
  chassée par la plus neuve.

## 3. Ce qu'elle lit

- `30-perception` : les faits qui lui parviennent, avec leur source, leur date et
  leur confiance ;
- `10-socle` : l'horloge de bataille, pour dater ;
- `40-combattant/identite` : de qui cet homme reconnaît l'autorité.

## 4. Ce qu'elle produit

Les entrées des couches 2, 3 et 4, et rien d'autre : l'ordre pour
l'interprétation, le chef et sa dernière position vue pour l'interprétation et la
réflexion, les pairs pour l'envie, l'historique pour toutes trois.

## 5. Invariants

- **L'ordre et le chef vivent sur l'HOMME.** Un ordre porté par l'unité et lu par
  l'homme au moment d'en avoir besoin n'est pas un ordre reçu : c'est de
  l'omniscience de groupe. Une sonde mesure la part d'hommes portant un ordre en
  propre ; l'attendu est proche de 100 % en ordre serré.
- Le chef connu porte une **position vue et sa date**, jamais la position réelle.
  Un homme séparé de son chef garde l'endroit où il l'a vu, et il vieillit.
- L'historique est **borné en nombre d'entrées**, pas en importance : une mémoire
  qui garde tout n'est plus une mémoire, c'est un journal, et le journal est en
  `90-observation`.
- Rien n'entre ici qui ne soit un fait perçu ou reçu. Aucune écriture depuis un
  module qui « sait ».

## 6. Ce qu'elle ne fait pas

- Elle **n'interprète pas** l'ordre : elle le range tel qu'il est arrivé, fautes
  comprises. Ce qu'il en comprend est la couche 3.
- Elle ne **transmet rien** : recevoir un ordre est ici, le faire circuler est
  `60-transmission`, qui viendra le lui remettre.
- Elle ne **cherche pas son chef** : elle ne remonte pas à l'unité pour savoir qui
  commande maintenant. Un chef tombé dont personne n'a vu la chute reste, pour cet
  homme-là, son chef.
- Elle ne tient **ni moral, ni fatigue, ni blessure** : ce sont des états du
  corps, écrits par `20-monde`.
- Elle ne raisonne pas et ne conclut rien.

## 7. Ce que l'ancien moteur faisait mal ici

**0,0 % des hommes portaient un ordre reçu, et 0,0 % un chef connu.** Ce n'était
pas une perte : l'ordre vivait sur l'unité, et le chef aussi. Chaque homme allait
les chercher là au moment de s'en servir.

La conséquence est exactement celle que le brouillard interdit : un homme
séparé, encerclé, ou dont le chef venait de tomber trois rangs plus loin lisait
quand même l'ordre courant et la position courante du chef courant. Aucun retard,
aucune déformation, aucune ignorance possible — et donc aucune des scènes qui
font une bataille.

Après réparation — l'ordre et le chef portés par l'homme, remis par la
transmission — **93,3 %** des hommes portaient un ordre et **62,0 %** un chef
connu. **Les 38 % restants étaient à plus de 18 mètres de leur chef** : ils ne
l'avaient pas vu, et c'était juste qu'ils ne l'aient pas.

Un chiffre qui descend de 100 % à 62 % peut être une réparation. C'est pourquoi
une sonde se lit avec sa raison à côté, jamais seule.
