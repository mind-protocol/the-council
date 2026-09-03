# 🧠 Doctrine / Manœuvres — ⏸️ STUB (feuille de route)

## Intention

Le LIVRE du commandant : un vocabulaire de manœuvres apprises (« déborder
par la gauche », « reculer de dix pas », « ratisser », « refuser le flanc »),
historiquement littéral (les livres de drill). **Une manœuvre est une
DONNÉE** — le pendant commandement de `doctrine/formes/` : un fichier par
manœuvre, le vocabulaire est fermé mais croissant, chaque ajout est une
décision d'archi.

## Format d'une manœuvre

```js
{
  nom: 'deborder-gauche',
  applicabilite: ['ennemiLocalise', 'flancGaucheEnnemiOuvert', …], // FAITS nommés (estimation)
  geometrie: (situation) => …,   // la SEULE fonction : où elle enverrait
                                 // l'unité, par quel chemin — le projecteur
                                 // générique en dérive les six axes
  poids: { … },                  // biais d'utilité propres (optionnels)
  phases: [
    { ordre: …,                  // une PHRASE du langage 📯
      succes: 'nomDeGarde', echec: 'nomDeGarde', patience: 30 },
  ],
}
```

## Règles (les garde-fous anti-if/else)

- `geometrie` est la seule fonction d'une manœuvre — PURE, petite. Pas
  d'évaluateur libre : les axes sont projetés par le moteur unique.
- Les critères de phases (`succes`/`echec`) sont des NOMS de faits/gardes,
  justifiables et affichables — jamais du code inline. Même discipline que
  les transitions des machines : la pente « mini-langage de script » est
  le risque connu, ces règles sont la digue.
- Les ordres des phases sont du TEXTE (format 📯) : références symboliques
  et relatives (« la gauche de l'unité ennemie » — résolue par CHAQUE
  récepteur contre SA forme crue), quantités en mots (« dix pas »).

## Modules

- `livre.js` — ✅ LE livre : la liste des manœuvres apprises. Ajouter une
  entrée ici (et son fichier) est TOUTE la dépense.
- `ratisser.js` — ✅ la première entrée : phases former → balayer les secteurs
  vierges (couverture, biais de rumeur directionnelle) → rompre (« Repos ! »,
  croyance infirmée). `contactSubi` l'interrompt — succès de la chasse.
- `charger.js` — ✅ la conclusion de la chasse : ennemi LOCALISÉ → former →
  « Chargez ! ». Succès = la mêlée VUE (`auContact`) ; échec = l'ennemi
  perdu → tenir les rangs, et le ratissage redevient applicable de lui-même.
- Prévus : `deborder-gauche.js`, `deborder-droite.js`, `reculer.js`,
  `se-reformer.js`, `tenir.js` — pures additions, l'arbitre ne change pas.

## Décision actée

- **Le repos est une CONCLUSION, jamais un abandon** : sur échec, patience ou
  inapplicabilité, l'arbitre fait crier « En formation ! » — une unité qui
  vient de subir le contact TIENT LES RANGS, elle ne part pas discuter.
