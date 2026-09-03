# outils/osm — du monde réel à une ville de l'état

Une chaîne, sept étapes numérotées, un `tout.py` qui les enchaîne. Chaque
étape se lance seule et lit ce que la précédente a écrit dans le dossier de
l'emprise, `bataille/donnees/osm/<nom>/` (`_travail.py`) : les brouillons y
restent, rangés par emprise, et servent de cache — l'étape 1 ne retire pas deux
fois sans `--forcer`, l'étape 3 garde ses tuiles, `--depuis` reprend là. Les
sorties sont ailleurs : `etat/villes/<id>.json`, `etat/chemins.json`,
`bataille/donnees/ville/<id>.*`.

```bash
python bataille/outils/osm/tout.py --nom gelibolu --id gallipoli --bbox 40.38,26.55,40.56,26.76
```

| étape | écrit | source |
|---|---|---|
| `01_recuperer.py` | `<nom>.osm.json` — la réponse Overpass brute, figée | OSM (ODbL), sans clé ; miroir si 504 |
| `02_nettoyer.py` | `<nom>.propre.json` — ce qui tient en 1305, en mètres | règles lisibles dans `REGLES` |
| `03_relief.py` | `<nom>.relief.bin/.json` — altitude int16 décimètres, même repère | tuiles Terrarium (SRTM), cache `terrarium/` |
| `04_composer.py` | `etat/villes/<id>.json` — le `sol` au vocabulaire du calque | la mer depuis la côte, les collines depuis la pente |
| `05_cuire.py` | `donnees/ville/<id>.masque.*` et `.plan.json` | appelle `scripts/monde/cuire_ville.py` **au pas du mètre** |
| `06_chemins.py` | `etat/chemins.json` (places, minutes) et `donnees/ville/<id>.routes.json` (mètres, géométrie) | les places nommées en nœuds, les routes en arêtes |
| `07_ombrage.py` | `donnees/ville/<id>.ombrage.png` — le volume de la carte | le relief, en lumière rasante du nord-ouest |

**Une ville engendrée se VERSE dans la chaîne**, elle ne s'écrit pas à la main :

```bash
python bataille/outils/osm/tout.py --nom gelibolu --id gallipoli --depuis 4 \
       --ville scripts/ville/gallipoli.tissu.json
```

`--ville` prend le tissu qu'a produit `scripts/ville/engendrer_<x>.py` (mètres du
repère de `<nom>.propre.json`, y vers le nord) et, à l'étape 4, remplace
l'octogone de 120 m du village par son tracé, ses rues et ses toits ; la voirie
d'aujourd'hui est coupée à l'enceinte, parce que dedans ce sont les rues
engendrées qui valent. À l'étape 5, ses portes deviennent les percées du masque.
L'étape 6 reprend alors ces rues sans rien savoir d'elles : les ruelles de la
ville entrent dans le graphe de marche comme le reste.

## Ce qu'il faut savoir

- **Le fichier de ville porte le nom du LIEU.** `serveur/routes/carte.js` sert
  `etat/villes/<lieu_id du personnage assis>.json` : la péninsule est donc
  `gallipoli.json`, et il n'y a qu'un Gallipoli. Le tracé à la main du bourg est
  archivé dans `etat/archive/villes/gallipoli-place-main.json` ; sa cuisson au
  mètre dort sous `donnees/ville/gallipoli-bourg.*` : **plus personne ne la
  lit** depuis que l'assaut de rue est posé sur la vraie carte (voir `POSE`
  dans `src/scenarios/assaut-de-rue.js`, 2 septembre). On la garde parce
  qu'elle n'est PAS reproductible — sa source, `etat/villes/gallipoli-bourg.json`,
  n'existe plus ; seul le tracé archivé demeure. À supprimer le jour où l'on
  aura décidé qu'on ne rejouera jamais l'ancienne mise en scène.
  **Aucun `<id>-essai` ni
  `<id>-peninsule` ne survit à une passe** : deux fichiers pour un lieu, et
  `etat/chemins.json` cite des places que la carte servie n'a plus.

- **`faits`, `corps` et `acteurs` ne sont PAS de la géographie, et l'étape 4 ne
  les fabrique pas — elle les REPREND** au fichier qu'elle remplace, pour qu'une
  relance n'efface pas ce que le jeu y a mis. Leurs coordonnées sont dans le
  repère de l'ancien fichier : quand le repère change, l'étape le dit et il faut
  les replacer à la main. La géographie se relance, les croyances se replacent.
- **Chaque pièce du sol a un `id`** (kebab-case, dérivé du nom, sinon du genre
  et de l'id OSM) : `bolayir`, `kadi-cesmesi`, `route-way-61295384`. C'est ce
  qu'une présence nomme (`{salle: "bolayir", lieu: "gallipoli"}`) et ce que le
  plan cuit conserve.

- **Deux repères.** Les couches 1 à 3 ont l'y vers le NORD, en mètres depuis le
  coin sud-ouest de l'emprise. Les villes de l'état ont l'y vers le SUD, en
  unités de 5 m. Le retournement se fait une seule fois, dans `04_composer.py`.
- **OSM ne dit pas ce qu'il y a au sol ici.** Les aplats gardés couvrent moins
  de 1 % de l'emprise : en Thrace rurale, personne n'a dessiné les champs. Ce
  qu'OSM donne de fiable, c'est la structure — côte, voirie, eau, villages,
  toponymes. La couverture vient du relief (les pentes fortes deviennent
  `colline`) et du fond nu du calque pour le reste.
- **Ce qui est composé le dit.** L'étendue d'un village est un octogone de
  120 m autour du nœud OSM, et son `detail` l'annonce. Les champs et les bois
  ont les limites d'aujourd'hui.
- **Le relief sert au DESSIN, pas encore à la marche.** Le monde lit un masque
  à 1 bit ; l'étape 7 en tire l'ombrage que 🖥️ `presentation/calques/terrain.js`
  pose sous les routes, et les pentes fortes deviennent des `colline`. La pente
  comme coût de marche viendra quand un homme en aura besoin.
- **Un ombrage ne se voit que s'il a deux faces.** La palette du moteur est
  nocturne (sol `#1b1712`) : une ombre seulement noire n'a aucune marge et la
  carte reste plate. L'image porte donc le versant éclairé en blanc autant que
  le versant sombre en noir, et laisse le plat transparent.
- **Les sorties sont des sorties.** `etat/villes/<id>.json` composé ici ne
  s'édite pas : on corrige la règle dans l'étape, et on relance.
