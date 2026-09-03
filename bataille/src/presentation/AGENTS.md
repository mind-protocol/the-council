# 🖥️ Container Présentation

## Intention

Fenêtre et télécommande. Elle lit tout, n'altère rien (à une exception près : le spawn), et envoie des commandes explicites. La simulation doit pouvoir tourner sans elle — headless — sans qu'une seule ligne des autres containers change.

## Responsabilités

- Rendu : canvas plein écran, caméra (zoom molette, pan drag, transformations monde↔écran — seul endroit qui connaît les pixels, tout le reste est en mètres), calques ordonnés et activables (terrain, hommes, chemins A* en debug, sélection).
- UI : panneau gauche collapsible à sections (dont la bibliothèque d'entités drag-and-droppables vers la scène), transport (play/pause, x2, x5 → commandes vers le container ⏱️ Orchestration).
- Inspecteur : panneau droit ouvert au clic sur un homme — affiche la machinerie interne via l'introspection du container 🧠 Cognition (`introspect()` du brain). Il affiche, il n'interprète pas.

## Frontières

- Lecture seule sur tout l'état, sauf : spawn d'entités (drag & drop — l'un des deux seuls points d'écriture sur le registre des corps) et commandes de transport vers le container ⏱️ Orchestration.
- Ne contient aucune logique de simulation. Si le rendu a besoin d'un calcul métier, ce calcul appartient à un autre container.

## Reçoit / Fournit

- Reçoit du container 🌍 Monde : tout l'état, en lecture (Rendu).
- Reçoit du container 🧠 Cognition : introspection (Inspecteur).
- Reçoit du container 🧠 Cognition : paroles émises (bulles — la surcouche de flavor ; demain la Transmission 📯, la voix qui porte).
- Reçoit du container 🏃 Action (calque debug) : chemins et cibles courants.
- Reçoit du container ⚙️ Physique (calque forces) : vue debug du dernier tick.
- Reçoit du container ❤️ Corps : l'équipement porté (rendu de la lance).
- Fournit au container ⏱️ Orchestration : pause, vitesse (transport).
- Fournit au container 🌍 Monde : spawns (drag & drop).
- Fournit au container 🧠 Cognition : l'attache d'un brain à chaque spawn (composée au bootstrap).
- Fournit au container ❤️ Corps : l'enregistrement de chaque spawn (composé au bootstrap).

## Observables

| Feature | Mécanique | Viz |
|---|---|---|
| `selection` | anneau autour de l'homme cliqué | calque `selection` |
| `camera` | zoom molette, pan drag, mètres↔pixels | intrinsèque |
| `spawn-refuse` | un spawn sur un obstacle est refusé | — |
| `calques-activables` | chaque calque peut s'allumer/s'éteindre | ui `calques` |
| `bulles-paroles` | paroles éphémères au-dessus des corps, vieillies au temps sim — viz de la comm 📯 à venir | calque `bulles` |
| `terrain-ville` | le plan cuit d'une ville (le-conseil2) rendu en raster caché à deux niveaux (ville entière au loin, fenêtre fine sous la caméra) — du DESSIN ; la vérité reste le masque (🌍) | calque `terrain` |
| `scenario-selecteur` | le catalogue des scénarios ; choisir = recomposer un monde NEUF (jamais de reset in place) | ui `scenarios` |
| `lignes-de-front` | debug vérité-terrain : le contour du front par camp (courbe), envergure (m), % de trous, perpendiculaire centrale (axe de menace, distance) | calque `lignes` |
| `inspecteur-redimensionnable` | panneau droit élargissable à la poignée (bord gauche) | ui `inspecteur` |
| `mort-gisant` | ✅ un mort est un CORPS TOMBÉ — torse à plat, tête roulée, un bras jeté, les jambes ouvertes (vignette ❤️ livrée × variante), sous une FLAQUE qui s'élargit, son arme lâchée à côté et son écu à plat. Dessiné SOUS les vivants : on marche sur ses morts. La flaque est la vraie viz — un corps se lit à trente pixels, une tache à trois, et elle reste quand les vivants sont partis | calque `gisants` |
| `calque-oiseaux` | ✅ le corbeau et le rapace : silhouette battante par espèce (plumage ❤️ — ailes larges à rémiges écartées, ou ailes en faux), ombre portée par z + pointillé (elle seule dit où il est vraiment), trace du vol colorée par la hauteur. Un oiseau est petit : le rendu le grossit ×3 pour qu'il se lise, la simulation ne bouge pas | calque `oiseaux` |

## Croissance attendue

Calques de debug par container (perception, forces, transmission des ordres), timeline/replay, éditeur de scénario, inspecteurs spécialisés par module.
