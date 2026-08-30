# Bâti

## 1. Ce que c'est

Les bâtiments comme **objets** : ce qu'ils sont, à quoi ils servent, par où l'on
y entre, ce qu'il y a dedans et qui s'y trouve — jamais comme obstacle physique,
qui est l'affaire du terrain.

## 2. Ce qu'il possède

- **L'inventaire des bâtiments** : identité stable, nom, usage déclaré (maison,
  forge, grange, corps de garde, échoppe, temple), et à qui il appartient.
- **L'empreinte déclarée** de chacun : son emprise au sol et sa hauteur. Il la
  **déclare** ; c'est le terrain qui l'inscrit comme infranchissable. Une seule
  autorité sur le mur, et ce n'est pas celle-ci.
- **Ses ouvertures** : la liste des seuils qui le desservent, et vers quoi chacun
  donne. Le seuil lui-même — sa largeur, sa capacité, son état — appartient au
  module des seuils.
- **L'intérieur**, au minimum utile : combien de corps y tiennent, s'il est
  cloisonné en pièces reliées par des seuils intérieurs, et si l'on y voit dehors.
- **L'occupation** : combien de corps s'y trouvent à cet instant, et lesquels.

## 3. Ce qu'il lit

Le socle (mesures, identité, formes). Le terrain, pour situer une empreinte et
savoir sur quoi elle est posée.

Il ne lit ni les seuils, ni le mouvement : ce sont eux qui viennent lui demander.

## 4. Ce qu'il produit

- **Qu'y a-t-il ici ?** — le bâtiment couvrant un point, s'il y en a un.
- **Par où entre-t-on ?** — les seuils desservant ce bâtiment, avec ce vers quoi
  ils donnent.
- **Reste-t-il de la place ?** — l'occupation courante face à la capacité.
- **Qui est dedans ?** — le bâti répond franchement ; la couche 30 décide si le
  demandeur avait le droit de savoir.
- **Un signalement** quand un bâtiment change d'état : plein, vidé, effondré, pris.

## 5. Invariants

- Un corps est dedans ou dehors, jamais les deux, jamais entre. L'état
  intermédiaire est *sur le seuil*, et il appartient au module des seuils.
- L'occupation ne dépasse jamais la capacité. Un homme refusé reste dehors, avec
  la raison du refus.
- Tout bâtiment a au moins un seuil, ou il est déclaré aveugle et personne n'y
  entre jamais. Un bâtiment sans issue et sans déclaration est une faute que la
  sonde signale.
- L'empreinte déclarée ici et l'infranchissable inscrit là-bas coïncident. Une
  sonde extérieure les compare ; deux vérités sur un mur, c'est un mur qui se
  traverse un jour sur mille.

## 6. Ce qu'il ne fait pas

- **Il ne décide pas de la franchissabilité.** Il déclare une emprise ; le
  terrain répond aux questions. Un module qui interroge le bâti pour savoir s'il
  peut avancer s'est trompé de porte.
- **Il ne fait entrer personne.** Entrer est une suite de pas à travers un seuil,
  écrite par le mouvement. Le bâti constate une occupation ; il ne l'assigne pas.
- **Il ne pose jamais de position intérieure.** Ni à l'entrée, ni à la sortie, ni
  « pour simplifier ». C'est la faute exacte qui a coûté le plus cher ici.
- **Il ne simule pas l'intérieur.** Pas de vie propre, pas de mobilier, pas de
  parcours autre que par les seuils intérieurs déclarés.
- **Il ne tient pas la valeur tactique d'un bâtiment.** Qu'une grange soit un bon
  point d'appui est un jugement de commandement.
- **Il ne détruit rien de sa propre initiative.** Un incendie vient des dangers ;
  le bâti enregistre et signale.

## 7. Ce que l'ancien moteur faisait mal ici

Sur **23 900 relevés**, **zéro homme vivant dans le bâti** : la géométrie était
unifiée, et le grief qu'on portait contre elle était infondé.

Le vrai défaut était à la frontière. **L'entrée dans un bâtiment ne téléportait
pas** — elle posait un point intérieur et l'homme y marchait, ce qui est la règle
qu'on veut garder. Mais la **sortie calait la position sur le seuil à 55 cm près,
hors du point de passage unique** : un second écrivain de position, court,
discret, invisible à une sonde qui ne regardait que les téléports. Une exception
de 55 cm ne se relève pas ; c'est pourquoi on ne compte pas les exceptions, on
interdit les écrivains.
