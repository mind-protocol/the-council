# Allocation

## 1. Ce que c'est

La répartition des forces entre les missions : qui reçoit quoi, ce qui reste
libre, et **ce qu'on choisit de ne pas engager.**

## 2. Ce qu'il possède

- **Le registre d'affectation** : pour chaque force disponible, la mission
  qu'elle sert, ou rien. Une force sert au plus une mission à la fois.
- **La force disponible telle qu'elle est CRUE** : effectif, fraîcheur, cohésion,
  distance à la zone — recopiés des croyances du commandement avec leur âge et
  leur confiance, jamais lus dans l'unité.
- **La part libre** : ce qui n'est affecté à rien et n'est pas non plus en
  réserve constituée.
- **Le motif de chaque affectation et de chaque retrait**, avec l'instant.

## 3. Ce qu'il lit

L'objectif, pour les poids et les plafonds de pertes. La mission, pour savoir ce
qu'une mission réclame et si elle tient encore. Le commandement, pour les
croyances sur ses propres forces. Le monde, pour les distances et les temps de
route.

## 4. Ce qu'il produit

- **Qui peut prendre cette mission ?** — les forces éligibles, avec ce que
  chacune coûterait à retirer d'ailleurs.
- **La répartition** : l'affectation proposée pour l'ensemble des missions
  ouvertes, arbitrée par le poids des buts servis.
- **Ce qui reste** : la part libre, chiffrée, à tout instant.
- **Un signalement** quand une mission ne peut pas être dotée, quand une force
  se libère, quand la part libre passe sous ce qui a été déclaré nécessaire.

## 5. Invariants

- Aucune force n'est affectée à deux missions. Un seul écrivain sur le registre,
  et une sonde le vérifie ; deux affectations sur le même effectif est la faute
  qui rend un compte de bataille faux sans rien casser.
- Toute mission ouverte est dotée ou explicitement déclarée **non dotée**, avec
  son motif. Une mission qui traîne sans force n'existe pas dans le fait.
- Une mission close libère sa force au même instant.
- La part libre est toujours calculable et jamais négative.
- **Tout engager est un choix, jamais un défaut.** Une répartition qui laisse
  zéro libre porte un motif écrit, comme les autres.
- Toute affectation s'appuie sur une croyance datée ; aucune n'est fondée sur
  l'état réel d'une unité.

## 6. Ce qu'il ne fait pas

- **Il ne commande rien.** Affecter n'est pas ordonner : la force affectée ne
  bouge que quand la mission lui est transmise et reçue. Une affectation faite et
  jamais transmise doit se voir comme telle.
- **Il ne découpe pas les unités.** Il répartit ce qui existe comme corps
  constitués ; scinder ou fusionner appartient à la couche 50, et se demande.
- **Il ne juge pas de la valeur d'un but.** Il applique les poids qu'on lui
  donne ; il ne les révise pas parce qu'une mission est commode à doter.
- **Il ne tient pas la réserve.** Garder, déplacer, engager est un autre module,
  et la part libre n'est pas une réserve : c'est du non-affecté.
- **Il ne compense pas une mauvaise croyance.** Si le commandement le croit
  riche de trois cents hommes qu'il n'a plus, il alloue trois cents hommes — et
  c'est le sujet, pas un défaut.
- **Il ne réessaie pas indéfiniment.** Une mission qu'il ne peut pas doter est
  signalée une fois, avec le manque ; c'est l'objectif qui arbitre ensuite.

## 7. Ce que l'ancien moteur faisait mal ici

**Il n'existait aucune allocation**, parce qu'il n'existait aucun niveau
« général » ni aucune mission à doter : les forces étaient placées par le
scénario écrit à l'avance, une fois pour toutes, et rien ne les redistribuait en
cours de nuit.

Il n'y avait donc ni registre d'affectation, ni part libre, ni motif de retrait —
et par conséquent **aucune double affectation à détecter et aucun manque à
signaler**. Le coût d'un retrait, le délai entre la libération d'une force et son
réemploi, la part de l'armée jamais engagée : **ces points n'ont pas été
mesurés.**
