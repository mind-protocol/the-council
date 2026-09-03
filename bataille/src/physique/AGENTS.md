# ⚙️ Container Physique

## Intention

Bête et incorruptible. Elle ne sait pas ce qu'est un ordre, une peur ou une intention : elle prend des vitesses désirées et des forces, applique les lois (répulsion, non-pénétration), et écrit les positions. C'est le seul écrivain régulier du registre des corps (container 🌍 Monde).

## Responsabilités

- Forces : champs de répulsion légers (les murs repoussent, les hommes se repoussent) et coude-à-coude (les rangs se soudent — géométrie pure). Chaque force future (panique…) devient une entrée de plus ici.
- Collision : résolution dure — personne ne se traverse (cercle/cercle, cercle/rectangle). La répulsion douce influence, la collision interdit : deux mécanismes distincts, réglables indépendamment.
- Intégration : somme des forces → vitesse → position, à dt fixe. Écrit le registre des corps du container 🌍 Monde.

## Décisions actées

- ✅ **un corps en vol échappe aux lois du sol** : tant que `vol` est présent, ni répulsions, ni collisions, ni garde — l'air est vide. L'Intégration reste l'unique écrivain : elle écrit l'état de vol RÉALISABLE calculé par l'actuateur (🏃 `steering/vol.js` — les lois y vivent, l'écriture ici), z compris, à dt fixe, déterministe. Le retour au sol (atterrissage, chute) réintègre les lois normales — différé avec son consommateur.
- **La garde lit la LIVRÉE** (un fait du corps, comme le rayon) : deux livrées adverses se tiennent à distance de lance. C'est la menace de la pointe physicalisée en champ — l'interprétation ami/ennemi reste une croyance 🧠, et le raffinement futur (répulsion par la POINTE elle-même : cap + posture, qui gérerait les fausses livrées) est noté pour le jour où il aura un consommateur.

## Frontières

- Aucune notion de décision, d'équipe, ou d'état mental. Si une logique a besoin de savoir « pourquoi », elle n'a rien à faire ici.
- Déterministe : mêmes entrées, mêmes sorties, à toutes les vitesses de simulation.

## Reçoit / Fournit

- Reçoit du container 🏃 Action : vitesses désirées, impulsions.
- Reçoit du container 🌍 Monde : géométrie des murs (Terrain), voisinages (Index spatial).
- Reçoit du container ❤️ Corps : l'arme portée (`armeDe`) — la garde est asymétrique par arme (allonge, coût).
- Fournit au container 🌍 Monde : positions et vitesses écrites (Registre des corps) — avec le spawn du container 🖥️ Présentation, l'un des deux seuls points d'écriture.
- Fournit au container 🖥️ Présentation (calque forces) : vue debug du dernier tick — construite seulement si quelqu'un l'a lue au tick précédent (un tick de retard pour un calque ; quatre objets par corps et par tick épargnés quand personne ne regarde, mesuré 2 septembre 2026) — vitesses désirées, corrections de collision, portées des champs.
- Fournit au container 📯 Social (Transmission) et au bootstrap : les lois acoustiques (`acoustique/portee-voix.js`, première passe : `quiEntend` = les corps à portée, sans atténuation) — la propagation d'une parole est un fait physique. Reçoit pour cela le voisinage du container 🌍 Monde (`voisinsDans`). Premier consommateur réel : la boîte de parole de la page — ce qu'un homme dit depuis la carte est entendu de tous ceux à portée, et d'eux seuls.

## Observables

| Feature | Mécanique | Viz |
|---|---|---|
| `repulsion-douce` | murs et hommes repoussent, profil linéaire | calque `forces` (halos) |
| `collision-dure` | personne ne se traverse, relaxation itérative | calque `forces` (flash + fantôme) |
| `inertie` | vitesse qui converge sous `accelMax` — demi-tour en arc | calque `forces` (traînées ; vecteurs sur le sélectionné) |
| `cap-integre` | rotation BORNÉE (`rotationMax`) vers le cap désiré (🧠 via 🏃) ; sans désir : sens de marche, conservé à l'arrêt | calque `hommes` (la lance) |
| `marche-arriere-lente` | vitesse bornée quand elle s'oppose au cap — fuir vite exige de tourner le dos | calque `hommes` (le recul se voit lent, face à l'ennemi) |
| `repousse-gisants` | les morts repoussent doucement les vivants — on enjambe, on ne piétine pas (unidirectionnel) | calque `forces` (halo gris sur les gisants) |
| `choc-renverse` | quantité de mouvement conservée au choc de charge — le léger est renversé (posture `renverse`), pas le lourd | calque `hommes` (jeté à terre, arme lâchée) |
| `charge-montee` | le galop percute : Δv échangé au choc → renversés en chaîne, TRAUMA poussé vers ❤️ (la physiologie juge la gravité) ; le mort tombe de selle | calque `forces` (éclats) + calque `hommes` (renversés) |
| `attelage` | le cavalier est PORTÉ : hors forces/collisions, position/vitesse/cap = sa monture ; il VEUT, elle PORTE (sa vitesse désirée passe au corps qui la réalise) ; monture morte → à pied, monture renversée → cavalier à terre | calque `hommes` (l'ellipse et son cavalier ne font qu'un) |
| `curee-rattrapable` | un dos en fuite n'émet plus de garde (sa pointe ne menace personne) — le fuyard se rattrape, et la pointe adverse le pousse | la poursuite se VOIT (l'écart se referme) |
| `garde-de-lance` | livrées adverses repoussées à allonge + 20 cm (centre à centre) — la MESURE d'escrime ; la fente (🏃) la perce | calque `forces` (halos) + la distance des lignes se voit |
| `coude-a-coude` | côte à côte + caps parallèles → attraction latérale vers l'épaulement — FAITS géométriques, aucun flag « formation », aucune livrée ; les lignes ennemies (caps opposés) s'ignorent | calque `forces` (vecteur vert sur le sélectionné) |
| `acoustique` | portée de voix (murmure 2 m / parole 8 m / cri 25 m) : `quiEntend(pos, {intensite})` rend les corps à portée ; atténuation par les murs et bruit de mêlée à venir | `conduire.quiEntend(id)` en console ; calque `bulles` (viz de la chaîne 📯 à venir) |

## Croissance attendue

Poussée de masse (mêlée), friction, projections au sol, projectiles, transfert de quantité de mouvement.
