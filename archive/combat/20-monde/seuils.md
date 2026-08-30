# Seuils

## 1. Ce que c'est

Une porte n'est pas un décor : c'est un **passage topologique** entre deux
espaces, avec une largeur, une capacité et un état — et le seul endroit du monde
où une foule se met en file.

## 2. Ce qu'il possède

- **L'inventaire des seuils** : porte, portail, brèche, poterne, gué, pont,
  échelle, passage intérieur. Chacun relie exactement **deux espaces** nommés, et
  dit lesquels.
- **Sa largeur utile**, en mètres — d'où découle combien d'hommes de front y
  passent.
- **Sa capacité d'écoulement** : combien de corps le franchissent par seconde, au
  mieux, dans un sens. Une porte n'a pas un débit infini parce qu'elle est
  ouverte.
- **Son état** : ouvert, fermé, barré, forcé, encombré, effondré — et depuis
  quand.
- **Son occupation courante** : qui est en train de franchir, et dans quel sens.
- **La file** : qui attend, dans quel ordre, et depuis combien de temps.

## 3. Ce qu'il lit

Le socle (mesures, horloge de bataille, identité). Le terrain, pour la géométrie
de l'ouverture. Le bâti, pour savoir ce que le seuil dessert.

## 4. Ce qu'il produit

- **Puis-je engager ce franchissement ?** — oui, non, ou pas maintenant, avec le
  motif et le délai attendu.
- **Le débit courant** et le temps d'attente estimé, pour qui doit décider s'il
  vaut mieux contourner.
- **Un signalement** à chaque changement d'état : forcé, barré, encombré, dégagé.
- **La conduite du franchissement** : la suite de points par lesquels un corps
  passe l'ouverture, remise au mouvement.

## 5. Invariants

- **Entrer, c'est franchir au fil des pas.** Le seuil ne pose jamais une position,
  ni à l'entrée, ni à la sortie, ni sur l'ouverture elle-même. Il rend un chemin
  court ; le mouvement l'exécute, et lui seul écrit une position.
- Le débit observé ne dépasse jamais la capacité déclarée. Une sonde extérieure
  compte les franchissements par seconde et le vérifie.
- Un seuil fermé ou barré n'est franchi par personne. Aucun cas particulier, y
  compris pour un homme en déroute — surtout pour lui.
- Un corps est d'un côté, de l'autre, ou en train de franchir. Le troisième état
  a une durée non nulle et se voit.
- Deux sens opposés dans une ouverture étroite se gênent, et cette gêne se lit
  dans le débit, pas dans une règle spéciale.

## 6. Ce qu'il ne fait pas

- **Il n'assigne aucune position intérieure.** Jamais. C'est l'interdit fondateur
  de cette fiche.
- **Il ne décide pas qui passe le premier.** Il tient la file ; l'ordre de priorité
  lui est remis par l'unité ou le commandement. Le seuil ne connaît aucun grade.
- **Il ne route personne.** Choisir *cette* porte plutôt qu'une autre appartient à
  la navigation. Le seuil répond sur lui-même.
- **Il ne force pas une porte.** Enfoncer est un acte, avec un coût et un
  résultat : ça vient de la collision et des dangers ; le seuil enregistre le
  changement d'état.
- **Il ne modélise pas l'écrasement.** Ce que fait une masse compressée devant une
  ouverture est mesuré par la densité ; le seuil ne fournit que le goulot.
- **Il ne se souvient pas de qui est passé.** L'historique est de l'observation.

## 7. Ce que l'ancien moteur faisait mal ici

Le grief attendu n'était pas le bon : **l'entrée dans un bâtiment ne téléportait
pas** — elle posait un point intérieur et l'homme y marchait, ce qui est le
comportement correct.

La faute était à la sortie : elle **calait la position sur le seuil à 55 cm près,
hors du point de passage unique**. Un franchissement au fil des pas d'un côté, un
recalage autoritaire de l'autre. Rien ne l'interdisait, rien ne le mesurait, et
l'écart était trop petit pour qu'une sonde à téléports le voie.

La capacité d'écoulement, elle, **n'a pas été mesurée** sur l'ancien moteur : la
condition d'étalon ne poussait jamais assez de monde dans une ouverture pour
qu'un débit se manifeste.
