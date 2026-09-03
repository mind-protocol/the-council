# 🧠 Cognition / Langage — ✅

## Intention

Le pont **parole ↔ math**, dans les deux sens. Les ordres sont du texte
(format 📯 `ordres.js`) et les croyances sont de la géométrie : ce module est
le SEUL endroit où l'un se traduit en l'autre. Fondamental pour les ordres
complexes des commandants : « débordez par la gauche de l'unité » n'est
soluble qu'avec une croyance de FORME (cap, largeur, première ligne) — la
gauche d'une unité est définie par SON orientation crue.

## Modules

- `resoudre-lieu.js` — **parole → math** : une référence symbolique
  (`locuteur`, `unite` + côté, `lieuNomme`…) + MES croyances → une géométrie
  `{pos, cap}` ou une zone. Héberge aussi LES IMPLICITES (ce que l'ordre ne
  dit pas, déduit par convention) : « en formation » nu → ma première ligne
  crue si nette et fraîche, sinon devant le locuteur, face à lui.
  Absorbe l'actuel `brains/soldat/interpretation.js`.
- `decrire.js` — **math → parole** : une croyance → du français. « une ligne
  d'environ 6 de front, orientée vers l'est », « un attroupement d'une
  vingtaine ». Consommateurs : étiquettes du calque perception,
  `objectifHumain` (fini les strings bricolées par compétence), et demain
  l'ÉMISSION du commandant (il formule ses ordres depuis sa carte mentale :
  émettre passe par `decrire`, recevoir par `resoudre` — symétrie complète).
- `repliques.js` — le RÉPERTOIRE de la parole flavor : des variantes par
  situation (rupture, assaut, curée, bavardage, défis…), en DONNÉE, registre
  Westeros assumé. Le tirage passe par le flux rng dédié des paroles. Consommateur :
  `cognition/paroles.js` (les déclencheurs).

## Frontières

- Ne lit QUE la Représentation (croyances) et le vocabulaire d'ordres (📯).
  Jamais le Monde : une résolution sur croyances périmées se trompe — c'est
  VOULU (c'est le mécanisme du « mal comprendre »).
- Fonctions PURES : croyances entrantes, géométrie/texte sortants. Le rng
  n'entre pas ici (l'à-peu-près viendra des croyances, pas du tirage).
- Une résolution peut ÉCHOUER (référence inconnue, croyance absente) — le
  retour null est un résultat, la compétence appelante en tire les
  conséquences (« je ne sais pas où c'est »).

## Croissance attendue

Côtés et flancs (`gauche/droite de X` via le cap cru), lieux nommés du
scénario (« le pont », « la colline »), distances qualitatives (« à une
portée de flèche »), degrés d'urgence dans la formulation, ambiguïtés
assumées (deux résolutions plausibles → on choisit, parfois mal).
