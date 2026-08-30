# `10-socle/horloge` — le temps de bataille

## Ce que c'est

Le temps de la simulation : un compteur de pas, jamais une lecture de l'heure.

## Ce qu'il possède

L'instant courant en secondes de bataille, le pas fixe, et le numéro du
battement.

## Ce qu'il lit

Rien.

## Ce qu'il produit

- l'instant courant ;
- l'avance d'un pas ;
- les **calendriers de décision** : de quoi dire si tel acteur doit délibérer à ce
  battement, avec une phase dérivée de son identité pour que tous ne décident pas
  dans le même.

## Invariants

- **Le pas est fixe.** La physique bat à cadence constante ; ce qui doit être
  moins fréquent l'est par un calendrier, jamais par un pas variable.
- **Aucune horloge de plateforme n'entre dans la simulation.** Rien qui dépende
  de la vitesse de la machine, d'un temps réel écoulé, ou de l'ordre d'arrivée
  d'un réseau.
- **Les décisions lentes ont un rythme déclaré**, pas un rythme subi. Un acteur
  qui décide « quand il se trouve que le code passe par là » n'a pas de rythme.
- La phase de chaque acteur est **dérivée de son identifiant** : reproductible,
  et sans consommer l'urne.

## Ce qu'il ne fait pas

- Il ne décide pas qui délibère : il dit seulement si l'échéance est atteinte.
- Il ne mesure aucune durée de calcul. Le temps d'exécution appartient à
  l'observation, jamais à la simulation.
- Il ne connaît ni le jour ni l'heure du monde de jeu. Le temps de bataille et le
  temps de la partie sont deux choses, et les mélanger rend une condition
  irreproductible.

## Ce que l'ancien moteur faisait mal ici

Le pas fixe existait et tenait. Ce qui manquait, c'est la **deuxième moitié** :
les calendriers de décision.

Mesuré : le calcul d'une couche de délibération était enfoui à la 680ᵉ ligne
d'une cascade de 855, si bien que seuls les hommes dont le battement descendait
jusque-là l'obtenaient — 135 sur 239, alors que les 239 avaient tout ce qu'il
fallait. **Le rythme d'une couche était le chemin de code, pas une échéance.**

L'autre leçon est une condition de reproductibilité : une simulation qui lit une
donnée du monde extérieur en cours de route — une heure de jeu, un état de partie
— ne cuit pas la même nuit deux jours de suite. La condition de mesure doit être
close, et l'ancien banc l'avait compris en refusant de charger la ville.
