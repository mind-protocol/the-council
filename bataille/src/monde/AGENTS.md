# 🌍 Container Monde

## Intention

Être la vérité objective et unique de la simulation : la géométrie du terrain, les positions et vitesses réelles des corps. Ce qui est ici EST vrai — les croyances, elles, vivent dans le container 🧠 Cognition.

## Modules

- `registre.js` — sait **qui existe** : les corps `{id, pos, vel, rayon, livree}`, en mètres. Un corps peut porter `personnage` : l'id de la fiche du jeu qu'il incarne, posé par le scénario — l'affectation d'un objet narratif à un objet physique. Le moteur ne le lit pas ; c'est par lui qu'un siège trouve son corps et parle d'où il est.
- `terrain.js` — sait **ce qui bloque** : obstacles immobiles (maisons rectangulaires) posés sur le plan, et masques de villes cuites.
- `terrain-masque.js` — le « pathmap » d'une ville cuite (le-conseil2) : grille 1 bit/case (1 m), bit = bâti. Lu, jamais énuméré en entier — les requêtes rendent des rectangles de case (même contrat que les obstacles posés).
- `navgrid.js` — sait **par où passer** : projection navigable du terrain, cache local à la demande, support de l'A*.
- `expose.js` — la seule porte d'entrée.
- `chaleur.js` — ✅ sait **ce qui a brûlé** — la trace thermique au sol (grille ~2 m de doses ((T−545)/1455)²·dt), déposée par l'acte souffler (🏃, puits comme les coups vers ❤️), vieillie par la phase index ; la braise refroidit à deux constantes (12 s / 90 s, au rendu), la carbonisation RESTE. Un fait du monde, rendu — perceivable demain.
- `index-spatial.js` — sait **qui est où** : grille de hachage (plan infini, cases occupées seulement). SÉMANTIQUE DE SNAPSHOT : reconstruit une fois par tick (phase « index », après l'Intégration) avec des copies — tout le monde décide sur la même photo. Résultats en ordre stable (tri par id, déterminisme).

## Décisions actées

- **Le plan est infini** : pas de bords, pas de « taille de map ». La zone 50×20 m est une donnée du scénario (zone de flânerie du random walk), pas du terrain.
- **La livrée est physique** : l'appartenance se VOIT (`livree` dans le registre, comme `rayon`). Aucun tag logique `equipe` — l'interprétation « ami/ennemi » est une croyance de la 🧠 Cognition. Rend possibles plus tard : confusion, fausses livrées.
- **Changement de scénario = jeter et refabriquer**, jamais de `reset()` en place (correct par construction, pas de contamination inter-scénarios). Le registre et le terrain ignorent le concept de scénario ; c'est le bootstrap qui compose.
- **Mutation en place** de pos/vel (perfo) ; la protection des lecteurs est la discipline de l'expose, pas des copies.
- **Itérations en ordre stable** (ordre d'insertion) : le déterminisme de la sim en dépend.

- **La masse et le gabarit sont des faits du corps** (comme le rayon) : masse tirée en distribution au spawn ; gabarit ('homme'/'cheval') = la silhouette QUE L'ON VOIT — le rendu et la perception la lisent, jamais un type ailleurs.
- ✅ **le VOL est optionnel sur le corps** (`vol: {z, vz, vitesseAir, banque, pente, phaseAile}`, absent = au sol) : une seule instance canonique par entité, pas d'entité parallèle — perception, rendu et index lisent le même registre. Écrit par l'Intégration (⚙️) comme pos/vel/cap. Un corps en vol sort des forces et collisions au sol ; son gabarit ('dragon') SE VOIT — la portée de détection croît avec la taille apparente (envergure/distance), c'est ce qui fait qu'un dragon se voit sur tout le théâtre (✅ passe peur). **Un seul canal canonique** : le ciel reste dans l'index — le snapshot porte les faits qui SE VOIENT (`rayon`, `z`, `vitesse`), et les distances VRAIES (3D, `voisinsDans` z compris) font qu'un corps en vol n'est jamais « à côté » de personne — ni un contact, ni une cible de flèche, ni un tas avec le sol.
- **L'ATTELAGE est un fait physique du Monde** : « qui est en selle sur quoi » (`atteler`/`montureDe`/`desatteler`). Écrit au chargement (🖥️/bootstrap) et vidé par ⚙️ quand la monture tombe ; ⚙️ asservit le porté à sa monture.

- **La ville est un MASQUE, le dessin est ailleurs** : la vérité du terrain urbain (Port-Réal) est le masque bitmap cuit par le-conseil2 (`portreal.masque.bin`, 1 m/case) ; le plan cuit (`plan2d.json`, chemins SVG) ne sert QUE la viz (🖥️ calque terrain). Les fichiers restent dans LEUR dépôt — pas de copie, une source canonique, servie par le montage du serveur de dev (`outils/montages.mjs`, seul endroit qui connaît le chemin machine). Le bootstrap charge (fetch), `demarrer` compose — la composition reste synchrone.
- **Repère monde sur la ville = repère du plan cuit, Y INVERSÉ** (le plan a l'Y vers le nord ; le monde garde le sud en bas — `inverserY` déclaré par le scénario). La porte de la Gadoue est à (3384, ~2990).
- ⏸️ DIFFÉRÉ — **la carte du commandant sur masque** : `carte: scenario.maisons` (rectangles) nourrit la ligne de barrage ; sur la ville, la carte seedée reste VIDE — le barrage ne « connaît pas le pays ». Le jour venu : une lecture grossière du masque (cases 4–8 m) comme savoir seedé.

## Frontières

- Passif : ne décide rien, ne bouge rien. Il répond à des requêtes.
- Exactement deux écrivains sur le registre des corps : l'Intégration (container ⚙️ Physique, chaque tick) et le spawn (container 🖥️ Présentation, drag & drop). Tout le reste lit. Cette règle est mécanique dans `expose.js` : aucun autre moyen d'écrire n'existe.
- Le container 🧠 Cognition ne le lit jamais directement — toujours à travers la Perception (filtrée, bornée).

## Reçoit / Fournit

- Reçoit du container ⚙️ Physique : les nouvelles positions (Intégration).
- Reçoit du container 🖥️ Présentation : les spawns (drag & drop).
- Fournit au container 🧠 Cognition (Perception) : lectures filtrées et bornées.
- Fournit au container 🧠 Cognition (Perception) : voisinages (Index spatial, snapshot du tick).
- Fournit au container 📯 Social (Transmission) : portées, positions (Index spatial) — à venir.
- Fournit au container 🏃 Action (Pathfinding) : la NavGrid.
- Fournit au container ⚙️ Physique (Forces) : géométrie des murs, voisinages.
- Fournit au container 🖥️ Présentation (Rendu) : tout l'état, en lecture.

## Observables

| Feature | Mécanique | Viz |
|---|---|---|
| `registre-corps` | positions et vitesses réelles des corps | calque `hommes` |
| `livree-physique` | l'appartenance se VOIT — couleur = livrée | calque `hommes` |
| `cap` | l'orientation du corps, écrite par l'Intégration (⚙️) | calque `hommes` (la lance) |
| `nom-panache` | on reconnaît les gens ; le chef se voit de loin | calque `hommes` + calque `perception` |
| `terrain-obstacles` | maisons immobiles qui bloquent | calque `terrain` |
| `terrain-masque` | la ville cuite bloque (1 bit/m²) : spawn refusé, murs répulsifs, navgrid — la porte laisse passer | calque `terrain` (cases du masque au zoom, SUR le dessin du plan : l'écart se voit) |
| `navgrid` | cases libres/bloquées, cache matérialisé à la demande | calque `navgrid` |
| `index-spatial-snapshot` | grille de hachage, photo figée par tick | calque `index` |

## Croissance attendue

Types de terrain et coûts (boue, pente), portes et passages, objets posés, lignes de vue précalculées, zones nommées, grille grossière pour les requêtes longue portée (transmission).
