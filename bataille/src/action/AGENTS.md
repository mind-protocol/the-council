# 🏃 Container Action

## Intention

Le traducteur : intentions abstraites (« aller là », « suivre lui ») → grandeurs physiques concrètes (vitesses désirées, impulsions). Il grossira avec les types d'actes, mais son contrat de sortie vers le container ⚙️ Physique reste minuscule et stable.

## Responsabilités

- Pathfinding : A* sur la NavGrid (container 🌍 Monde), cache des chemins, re-calcul quand la cible change.
- Steering : suivi du chemin — produit la vitesse désirée vers le waypoint courant, modulée par la vitesse max effective (container ❤️ Corps). Le REFUS de la monture (`steering/refus-monture.js`) est un réflexe d'actuation : jugé sur le RÉEL devant le cheval (comme l'acte de frapper juge sur les corps réels) — le cavalier veut, la monture refuse une masse hérissée.
- Actes : les actions non-locomotrices. `frapper(cible)` — l'intention NOMME, la lance JUGE : allonge + arc du cap sur le corps réel, réarmement ~1,5 s, un coup peut rater. Coûts vers ❤️ (locomotion, engagement, posture tenue). Frapper/tirer vivent encore dans l'expose (legacy) ; `actes/` démarre avec le souffle du dragon — les extractions suivront.
- Vol — ✅ (`steering/vol.js`) : l'actuateur des corps volants — intention de vol ({capVoulu, zVoulue, regime}) → ÉTAT DE VOL réalisable du tick, borné par le profil (❤️ dragons.js) : virage coordonné ω = (g·tanφ + a_batt)/V, vol lent battu (lacet propulsé), altitude filtrée, vitesse filtrée à plancher non-catapulte. Fonction PURE ; ⚙️ écrit. Régimes pique/souffle/sortie : ⏸️ passe intelligence. Lois gardées du banc du Conseil — feuille de route : [🧠 brains/dragon/CLAUDE.md](../cognition/brains/dragon/CLAUDE.md).
- Souffler — ✅ (`actes/souffler.js`) : l'acte de feu — le cône 3D incliné coupé EXACTEMENT par le sol (cordes des disques, jamais un triangle 2D — tant que la géométrie ne permet pas, RIEN ne se dépose), température par distance 3D à l'axe, enveloppe B(t), halo turbulent ~3,2 m pour les corps exposés ; brûlures (dose) vers ❤️, trace vers 🌍 (chaleur), effort vers ❤️. L'intention nomme l'occasion (crue), le cône juge qui brûle (réel) — même partage que frapper. Le vol continue pendant le jet (régime souffle, correction de quelques degrés).

## Frontières

- N'écrit jamais une position : il propose des vitesses désirées, le container ⚙️ Physique dispose.
- Ne choisit jamais quoi faire : il exécute des Intentions. Si une intention est irréalisable (pas de chemin), il le signale — le container 🧠 Cognition en tirera les conséquences.

## Reçoit / Fournit

- Reçoit du container 🧠 Cognition : intentions.
- Reçoit du container 🌍 Monde (NavGrid) : réponses aux requêtes de chemin.
- Reçoit du container ❤️ Corps : vitesse max effective.
- Fournit au container ⚙️ Physique : vitesses désirées, impulsions, états de vol réalisables (`volsDesires`).
- Reçoit du container ❤️ Corps : le profil d'oiseau porté (`oiseauDe`) — l'actuateur de vol s'y borne.
- Fournit au container ❤️ Corps : coûts des actes.
- Fournit au container 🧠 Cognition : signalement des intentions irréalisables.
- Fournit au container 🖥️ Présentation (calque debug) : chemins et cibles courants.

## Observables

| Feature | Mécanique | Viz |
|---|---|---|
| `acte-frapper` | la cible est nommée, l'allonge et l'arc décident — ami compris ; la FENTE porte le corps en avant le temps du geste | calque `coups` (le trait de pointe, chaud si porté, gris si dans le vide) + calque `hommes` (flash du touché) |
| `refus-monture` | le RÉFLEXE du cheval : pointes levées adverses dans la fenêtre de regard (pique plein, épée peu) → freinage continu + dérobade vers le côté le moins hérissé — les murs de piques TIENNENT sans une règle de plus | calque `hommes` (chevron orangé vers la fenêtre refusée) |
| `train-de-monture` | l'intention porte un `train` ('pas'/'trot'/'galop') : le cavalier parle à sa monture — la vitesse max est PAR CORPS ; à pied le mot est ignoré | la charge SE VOIT (8 m/s vs 1,4) |
| `acte-tirer` | la volée sur une ZONE crue : cadence par arc, flèche puisée (refus à vide), dispersion en cône, la flèche touche QUI est là — ami compris | calque `coups` (trait fin pâle, croix d'impact) |
| `pathfinding-astar` | chemin trouvé sur la navgrid | calque `chemins` |
| `suivi-chemin` | waypoint courant, vitesse désirée | calque `chemins` |
| `lissage-chemin` | string-pulling : crans 45° → vrais coins | — |
| `echec-intention` | signalement d'une intention irréalisable | — |
| `vol-banque` | l'intention de vol bornée par le profil : virage coordonné banqué, vol lent battu, altitude et vitesse filtrées, piqué énergétique (interception du plan de tir, la hauteur devient vitesse) — l'état réalisable écrit par ⚙️ | calque `dragon` (silhouette battante, ombre portée par z, path coloré par altitude, altimètre) |

## Croissance attendue

Vocabulaire d'actes (combat, escalade, transport), files d'actions, interruptions, échecs d'exécution remontés proprement au container 🧠 Cognition.
