# L'arbitre — couche 5

## 1. Ce que c'est

La couche qui **ne pense pas** : elle élit. Laquelle des quatre tient les jambes,
laquelle tient les bras, à cet instant, et pourquoi.

## 2. Ce qu'il possède

- l'**élection courante** : un tenant pour les jambes, un tenant pour les bras,
  chacun avec la couche gagnante, la force retenue, la barre franchie ;
- la **trace d'arbitrage** : les quatre prétendants avec leur force, ceux qui se
  sont abstenus, la barre, l'écart, et le motif du gagnant ;
- l'**inertie** : depuis combien de battements le tenant tient, et de combien il
  faut le dépasser pour le déloger.

## 3. Ce qu'il lit

Les quatre couches — corps, réflexion, interprétation, envie — et rien d'autre.
Pas la perception, pas le monde, pas la mémoire, pas l'unité. **L'arbitre est
aveugle à la bataille**, et c'est ce qui le rend vérifiable.

## 4. Ce qu'il produit

Deux élections par battement, jamais moins, et la trace qui les explique. Cette
trace est la **source unique** de ce que l'homme est réputé penser : l'écran, les
sondes et l'observation la lisent, personne n'en écrit une seconde.

## 5. Invariants

- **Rien ne contourne l'arbitre.** Aucun chemin ne déplace un homme ni ne lui
  fait porter un coup sans passer par une élection. Une sonde compare le nombre
  de gestes émis au nombre d'élections : l'écart attendu est zéro.
- **Une abstention n'est pas un zéro.** Une couche qui ne rend rien est retirée
  des prétendants ; une couche qui rend une force nulle concourt avec zéro. Les
  deux ne doivent jamais être confondues, et ça vaut d'abord pour la barre.
- **L'inertie : le tenant garde la main contre un peu plus fort que lui.** Il
  faut un écart franc pour le déloger, sinon un homme change d'avis à chaque
  battement et rien de ce qu'il fait n'est lisible.
- Aucun tirage : à prétendants identiques, même élection. Les égalités se
  tranchent par un ordre fixe des couches, pas par l'urne.
- Toute élection cite sa barre, même quand la barre est absente.

## 6. Ce qu'il ne fait pas

- Il ne **fabrique aucune option** : il n'a pas de geste de secours à lui. Si les
  quatre s'abstiennent — ce qui ne devrait pas arriver, le corps répondant
  toujours —, il le déclare au lieu d'inventer.
- Il ne **corrige aucun prétendant** : il ne rehausse pas une force jugée trop
  basse, ne plafonne pas une envie, ne réécrit pas une direction.
- Il ne **lit rien du monde** pour vérifier si le gagnant est réalisable. Un
  geste impossible est élu comme un autre, et c'est le monde qui le refusera.
- Il ne parle pas à l'unité, ne signale pas une rupture, ne compte pas les
  déroutes.
- Il ne garde **aucun historique long** : quelques battements d'inertie, pas une
  biographie.

## 7. Ce que l'ancien moteur faisait mal ici

Trois défauts, tous mesurés, et ils se tiennent.

**Il était contournable par construction.** L'arbitre était consulté à la
**236e ligne d'une cascade de 855, comportant 38 sorties anticipées** : tout ce
qui retournait avant lui le contournait sans qu'aucune règle ne s'y oppose.

**Il confondait absence et zéro.** Quand la couche 3 manquait, il retenait une
barre de **zéro** au lieu du **0,50** d'un ordre ordinaire. Comme cette couche
n'était calculée que pour 135 hommes sur 239, **43 % de l'armée était arbitrée
comme n'ayant reçu aucun ordre alors que tous en avaient un**.

**Sa décision n'était pas ce qu'on montrait.** La pensée affichée d'un homme
était posée depuis **56 endroits** ; **46 nommaient la branche de code** qui
venait de le déplacer, **10 seulement une vraie couche**. Résultat : **plus d'un
homme sur quatre affichait une pensée contredisant l'élection de l'arbitre.** Le
corps tenait les jambes 28,7 % du temps, l'écran le disait 1,4 % du temps.

Après réparation de la couche 3 : disponible pour 97,9 % des hommes, dispersion
au chef (P90) de 92,5 m à 68,8 m, vintaines groupées de 90 % à 97 %, et les
premières déroutes réelles — **6 contre 0**. Un arbitre juste ne suffit pas :
il faut qu'on ne puisse pas s'en passer, et qu'il reçoive tous ses prétendants.
