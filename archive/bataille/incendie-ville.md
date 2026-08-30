# Incendie urbain — hypothèses de l’épreuve F1

Cette épreuve est un banc non canonique. Son état reste en mémoire et sa remise
à zéro repart de la graine `0x129ac`. Elle n’écrit rien dans `etat/`.

## Autorité géométrique

Chaque volume vient des contours SVG finaux de `portreal.plan2d.json`. Ce sont
les mêmes contours que la carte colore et que le masque de collision rasterise.
La distance entre deux bâtiments est la plus courte distance entre leurs bords,
jamais la distance entre leurs centres.

Le plan agrège les contours par usage. Quelques bâtiments à annexes disjointes
produisent plusieurs contours ; F1 traite alors chaque contour comme un volume
de feu. Cela surcompte moins de 2 % des usages concernés et évite d’inventer une
seconde géométrie.

## Matériaux inférés

- **Bois léger et chaume** : taudis et cabanes.
- **Pans de bois, torchis et tuiles** : maison, échoppe, taverne et autre bâti
  urbain ordinaire.
- **Forte charge combustible** : entrepôt, écurie, chantier de bois et charbon,
  corderie, voilerie, moulin, marché et grenier.
- **Atelier mixte** : foyer ou cuve maçonnée dans un bâtiment encore largement
  charpenté — forge, boulangerie, brasserie, tannerie, teinturerie, étuve,
  poterie et abattoir.
- **Maçonnerie à intérieur combustible** : manse, maison d’officier, septuaire,
  caserne, geôle et corps de garde.
- **Maçonnerie massive** : Donjon Rouge, Fosse aux Dragons et vieux septuaire.
- **Feu grégeois** : la Guilde des Alchimistes est volontairement un cas
  catastrophique distinct.
- **Inerte** : puits et fosses.

Les murs de torchis, les tuiles et la pierre ne sont pas du combustible. Ce
qui brûle est la charpente, les planchers, le mobilier et le contenu ; la classe
modifie donc la probabilité d’entrée du feu et son développement, pas seulement
sa couleur.

## Transmission locale

Un bâtiment en feu accumule chez ses voisins un hasard cumulatif :

```text
H20(d) = 3 exp(-d / 4,2)
P(allumage) = 1 - exp(-H)
```

Pour deux maisons ordinaires sèches exposées vingt minutes, cela donne environ
95 % au contact, 79 % à 3 m, 51 % à 6 m, 24 % à 10 m et 2,5 % à 20 m. Le calcul
s’arrête à 22 m ; au-delà, les brandons prennent le relais.

Le hasard n’est pas tiré à chaque image. Chaque volume possède un seuil stable
`-ln(1-U)` et les expositions successives s’additionnent jusqu’à le franchir.
Le résultat est indépendant du nombre d’images par seconde et les feux voisins
peuvent réellement se combiner.

La dose est multipliée par :

- la charge rayonnante et la surface du bâtiment source ;
- la susceptibilité du matériau cible ;
- une exposition aux ouvertures stable entre `0,75` et `1,35` ;
- l’alignement avec le vent ;
- l’humidité, fixée à `1` dans cette cuisson sèche.

Le vent fixé est un vent d’ouest de `7 m/s`, dirigé quatorze degrés vers le
sud : **O → ESE**. Dans son axe, le multiplicateur atteint environ trois ; à
contrevent il tombe vers `0,43`. L’hypothèse est une condition de comparaison,
pas une affirmation sur la circulation atmosphérique canonique de Port-Réal.

## Brandons

Un bâtiment pleinement embrasé émet des événements de brandons selon sa toiture
et son contenu. Leur distance suit une loi log-normale de médiane `35 m` ; la
majorité tombe entre dix et deux cents mètres. Un événement sur trois cents
ouvre une queue rare entre `300` et `800 m`.

Chaque atterrissage n’allume pas automatiquement sa cible : environ 32 % pour
le chaume sec, 26 % pour un stock exposé, 5,5 % pour un bâtiment urbain sous
tuiles, 1,5 % pour une construction maçonnée et 0,2 % pour une masse de pierre.
Les impacts répétés s’additionnent comme les expositions locales.

## Temps internes

Le chaume atteint le plein embrasement en environ 75 secondes et brûle quinze
minutes. Une maison ordinaire croît pendant quatre minutes puis brûle environ
45 minutes. Les stocks, ateliers et grands édifices brûlent plus longtemps ;
la maçonnerie massive peut garder des intérieurs en feu pendant deux heures.

Ces temps désignent le volume représenté par la carte, pas chaque pièce. Ils
sont assez lents pour qu’un front se lise et assez rapides pour qu’une cuisson
d’une heure révèle les coupe-feux urbains.

## D3 — apport direct du souffle de Vhagar

D3 remet le même moteur à zéro avec **zéro départ imposé**. Le moteur dragon
calcule d’abord son volume conique en 3D, puis son intersection avec `z=0` sous
forme de cordes espacées de `0,75 m`. F1 ne reconstruit aucun cône en plan : il
cherche les contours de toits réellement coupés par ces cordes et reçoit, pour
chaque coupe, la distance 3D à l’axe et la température correspondante.

Au-dessus de `545 K`, la dose directe ajoutée vaut :

```text
dH = ((T - 545) / (Tnoyau - 545))² × dt × 20 s⁻¹
     × susceptibilité du matériau × exposition aux ouvertures
```

Le facteur `20 s⁻¹` signifie qu’un toit de pans de bois traversé par le noyau
pendant `0,1–0,3 s` a de fortes chances de prendre, sans transformer la coupe
en certitude. La même exposition est multipliée par `0,35` pour la maçonnerie
charpentée et `0,08` pour la pierre massive. La dose franchit le même seuil
stable `-ln(1-U)` que les autres mécanismes : un passage tiède peut préparer un
toit qu’un second passage, un voisin ou un brandon finira d’allumer.

Les prises causées par Vhagar sont comptées séparément. Dès qu’un toit prend,
sa croissance, son rayonnement, sa combustion et ses brandons redeviennent
strictement ceux de F1. Ainsi, tout bâtiment hors du cône ne peut brûler que
par propagation secondaire.

La fumée est une couche de lecture, sans effet physique : les foyers proches
sont agrégés à l’échelle de l’écran et leur panache est étiré vers l’ESE selon
le vent fixe de `7 m/s`. Elle remplace les anciens halos circulaires ; les
contours colorés des toits restent l’autorité de l’état matériel.
