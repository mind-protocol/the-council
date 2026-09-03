# ❤️ Container Corps

## Intention

L'état interne physiologique de chaque homme — ce qui n'est ni une position (container 🌍 Monde) ni une croyance (container 🧠 Cognition). Trois containers en dépendent, aucun ne le possède : c'est pourquoi il est autonome.

## Responsabilités

- Physiologie : stamina, souffle, blessures. Écrite par ce que l'homme fait (Actes, locomotion), lue par ce qu'il décide et peut faire.
- Traits & types d'unités : profils individuels (vitesses, seuils, équipement) — les paramètres qui différencient un piquier d'un archer, un vétéran d'une recrue.

## Frontières

- Ne décide rien : il constate. La fatigue ne fait pas fuir un homme — c'est sa Décision (container 🧠 Cognition) qui choisit de fuir parce qu'il se sent fatigué.
- Pas de position, pas de croyance : uniquement de l'état physiologique et des profils.

## Reçoit / Fournit

- Reçoit du container 🏃 Action (Actes, locomotion) : coûts (dépense de stamina, blessures).
- Reçoit du container 🖥️ Présentation : l'enregistrement de chaque spawn (composé au bootstrap).
- Fournit au container 🧠 Cognition (Décision) : fatigue, état ressenti.
- Fournit au container 🖥️ Présentation (Rendu) : l'équipement porté.
- Fournit au container 🏃 Action (Steering) : vitesse max effective, capacités réduites.
- Fournit au container ⚙️ Physique (Forces) : l'arme portée (`armeDe`) — la garde est asymétrique par arme (allonge, coût).

## Modules

- `armes.js` — ✅ LE CATALOGUE : une arme est une DONNÉE (allonge, arc, réarmement, coût de garde, silhouette) — jamais un if/else sur le type ailleurs. `lance` (défaut), `lanceLongue` (4,5 m — tenir à distance, lente, épuisante), `epee` (vive, large, sobre). Le BOUCLIER : une parade FRONTALE géométrique (arc couvert autour du cap → CLANG, pas de blessure) — un fait d'angle, pas un compteur.
- `equipement.js` — ✅ : le paquetage par homme `{arme, bouclier}`, seedé par le scénario (par unité). Vues : `armeDe` (🏃 l'acte, ⚙️ la garde, 🧠 le ressenti de sa portée), `bouclierDe` (🏃 juge la parade au coup), `equipementDe` (🖥️ — des chiffres de silhouette, jamais des types).
- `oiseaux.js` — ✅ LE CATALOGUE des oiseaux (le pendant volant d'armes.js) — deux profils en pure donnée (gabarit, régimes de vol, conduite de descente, plumage) : le CORBEAU qui suit l'armée et le RAPACE DE CHASSE qui se poste et fond. Jamais un if/else sur l'espèce ailleurs. Ce qui les sépare est dans les chiffres, jamais dans le graphe : [🧠 brains/oiseau/CLAUDE.md](../cognition/brains/oiseau/CLAUDE.md).
- `souffle.js` — ✅ : la RÉSERVE se dépense linéairement avec l'effort (coûts poussés par les Actes 🏃, en effort-secondes ; l'engagement plein la vide en ~45 s, la marche coûte `facteurMarche`), le repos récupère. Le RESSENTI — ce que lit la Décision — est une **SIGMOÏDE de la réserve, pas une barre** : long plateau frais, bascule brutale (~35 % de réserve), plateau épuisé. La phase `physiologie` (⏱️, après la physique) est LA phase du Corps.
- Blessures, Traits — ⏸️ à venir avec leurs consommateurs (passe combat).

## Décisions actées

- **Le ressenti est une fonction en S de la réserve** : les consommateurs (readiness, vitesse effective demain) ne voient jamais la réserve brute — un homme « tient » longtemps puis s'effondre vite, comme un vrai souffle.
- **LA MORT EST CONSTATÉE ICI** (au seuil de coups), jamais écrite ailleurs : sa manifestation physique est un GESTE (`gisant`) émis par la Cognition et écrit par la chaîne normale (🏃 → ⚙️ → 🌍). La mort SE VOIT, elle ne se sait pas — perception, physique et actes réagissent à la posture du corps, pas à un signal. Les cadavres restent sur le champ (V1 : traversables, hors du jeu des forces — les barricades de morts viendront) ; un mort ne prend plus de coups (pas d'acharnement compté).
- **LE FREESTYLE N'EXISTE PAS** : les flèches sont COMPTÉES (`carquois.js`, une botte par archer, seedée par le scénario). Le carquois vide est un FAIT que la machine 🧠 lit (garde `voleeFinie` → le couteau) — jamais une ressource infinie, jamais un cooldown déguisé. Le scénario décide de l'abondance, pas le code.
- **Le TRAUMA d'un choc est jugé ICI** (`subirChoc`) : ⚙️ pousse l'à-coup subi (Δv), la physiologie le convertit en coups — continu au-delà d'un cran (3 m/s). C'est ce qui fait TUER la charge : un demi-tonne au galop ≈ 2 coups sur 4 — un passage blesse, la répétition ou le fer achèvent.
- **Pas de portée minimale au tir** : on tire très bien sur un homme à 3 m — ce qui fait lâcher l'arc, c'est quelqu'un AU CONTACT de soi (garde `ennemiAuContact`), jamais un seuil de distance. La dispersion est un CÔNE : proportionnelle à la distance (~±6 m à 110 m).
- **LE FEU N'EXISTE PLUS** (1er septembre 2026) : le dragon est devenu corbeau et rapace, et la dose thermique est partie avec lui — `subirBrulure`, les paramètres `feu`, `monde/chaleur.js`, l'acte `souffler`. Ce qui vole ne blesse plus personne. Le VOL, lui, est resté entier : c'est ce qu'on voulait garder.
- **Les blessures réduisent la capacité** : malus de vitesse linéaire par coup, plancher (un blessé boite, il ne s'arrête pas) — la vue `facteurVitesseDe` sert le Steering (🏃), le câble déclaré depuis le premier jour.

## Observables

| Feature | Mécanique | Viz |
|---|---|---|
| `equipement-lance` | lance par défaut = l'orientation se voit | calque `hommes` |
| `armes-differenciees` | pique 4,5 m / épée : allonge, arc, réarmement, coût de garde PAR ARME — la garde ⚙️ est asymétrique (chacun craint la pointe ADVERSE) | calque `hommes` (longueurs) + calque `forces` (halos de garde par arme) |
| `bouclier-parade` | coup frontal dans l'arc couvert → CLANG, pas de blessure | calque `hommes` (le rond au bras) + calque `coups` (étincelle dorée) |
| `souffle-sigmoide` | réserve linéaire, ressenti en S — ~45 s d'engagement, bascule à ~35 % | inspecteur `souffle` |
| `blessures` | coups reçus comptés ; la vitesse baisse à chaque coup (plancher — on boite) | calque `hommes` (flash) + inspecteur `blessures` |
| `mort-gisant` | au seuil de coups : constat ❤️, geste `gisant`, cadavre figé sur le champ | calque `hommes` (cercle vidé, lance à terre) |
| `arc-et-carquois` | l'arc = un projecteur de ZONE (pas d'arme de mêlée) ; les flèches COMPTÉES par carquois — puiser refuse à vide | inspecteur `fleches` + calque `coups` (traits de volée) |

## Croissance attendue

X autres variables : chaleur, soif, douleur, charge portée, blessures localisées, récupération, effets de l'équipement sur la mobilité.
