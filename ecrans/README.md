# Écrans — mode d'emploi MJ

Templates de fragments HTML pour `show_widget` (pas de DOCTYPE/html/head/body ; fond transparent ; `sendPrompt` est fourni par l'hôte). Dupliquer le contenu, remplir, envoyer tel quel.

- **scene.html** — remplir chaque `<!-- SLOT: ... -->` : date (« Ne jour de la Ne lune, AAA AC »), lieu, tension (largeur `%` de la jauge = `etat/monde.json` → `tension`), portrait (`portraits/<id>.png`, le fallback SVG gère l'absence), nom + titre, réplique, narration (2-4 `<p>` max), et les 3 choix. Pour chaque choix : même texte dans le bouton et dans `sendPrompt('CHOIX: ...')`.
- **creation.html** — utilisable tel quel ; ajuster si besoin les options marquées `SLOT` (sièges, forces, faiblesses). Le bouton « Fonder la maison » valide (nom, siège, 2 forces, 1 faiblesse) puis envoie `CREATION: maison=... | siege=... | devise=... | blason=... | forces=... | faiblesse=...`.
- **Apostrophes** : dans tout `sendPrompt('...')`, échapper `'` en `\'` (ou utiliser `&rsquo;` dans le texte affiché).
- Garder les préfixes exacts : `CHOIX:`, `ACTION LIBRE:`, `MODE: play|advance|jump`, `CREATION:`.
- Thème clair/sombre automatique (`prefers-color-scheme`) ; aucune ressource externe — ne pas ajouter de CDN, fonts ou images distantes.

- `modules/partie.js` + `modules/partie.css` — « Le conseil » : la partie en cartes
  (fronts, piles, deck). UN SEUL GESTE — on prend une carte, on la pose sur une
  autre —, et c'est la carte du dessous qui dit ce que ça veut dire : l'écran ne
  connaît aucun nom de coup, le greffier traduit. Ce qui n'est pas jouable ne
  s'allume pas quand on tient une carte ; un refus revient en une phrase sous la
  barre. Voir [docs/partie.md](../docs/partie.md).
