# 📯 Container Social

## Intention

La cognition-à-cognition, médiée par le monde physique. Un ordre n'est pas une écriture dans le cerveau du destinataire : c'est un message émis par une Décision, transporté physiquement (voix, messager, tambour), qui arrive — ou pas — comme un percept. Il peut être mal entendu, arriver en retard, ou jamais.

## Responsabilités

- Hiérarchie : qui commande qui. Structure d'autorité, distincte des liens affectifs (futurs).
- Ordres : émission par les chefs, format, interprétation. Un ordre est une donnée, pas un appel de fonction.
- Transmission : le canal physique — portée de voix, délais, atténuation, messagers. Interroge le container 🌍 Monde (Index spatial) pour savoir qui peut entendre quoi.

## Frontières

- Ne modifie jamais directement une Représentation mentale : la livraison passe par la Perception du destinataire (container 🧠 Cognition).
- Ne décide pas du contenu des ordres (ça, c'est la Décision du chef) ni de leur effet (ça, c'est la Cognition du subordonné).

## Reçoit / Fournit

- Reçoit du container 🧠 Cognition (Décision d'un chef) : ordres à émettre.
- Reçoit du container 🌍 Monde (Index spatial) : portées, positions, obstacles au son.
- Recevra du container ⚙️ Physique : les lois acoustiques (`acoustique/portee-voix.js`, première passe écrite : `quiEntend` rend les corps à portée) — qui peut entendre une parole. ⏸️ Pas encore câblé ici : aujourd'hui c'est le bootstrap qui les consomme (`quiEntend` de l'instance, pour la parole depuis la carte) ; la Transmission les reprendra.
- Fournit au container 🧠 Cognition (Perception du destinataire) : messages délivrés comme percepts.

## Modules

- `unites.js` — ✅ la vérité sociale : unité `{chef, ordreDrill, forme}`. L'`ordreDrill` (chef en tête) EST les habitudes du drill ; la `forme` est un vocabulaire OUVERT (`rangs` aujourd'hui, colonne/cercle/coin demain) que la doctrine (🧠) interprète.
- `ordres.js` — ✅ LE FORMAT : un ordre est de la PAROLE — vocabulaire fermé de verbes (`EN_FORMATION`, `REPOS`) + références SYMBOLIQUES (`locuteur`, lieu nommé, unité), JAMAIS de coordonnées. La résolution spatiale se fait chez le RÉCEPTEUR contre ses croyances (🧠) — c'est ce qui garde tout dynamique, et permettra de mal comprendre. Le récepteur reçoit `{ordre, emetteur}`. `enTexte()` = ce que les bulles crient.
- Transmission — ⏸️ à venir : l'ordre est injecté en direct par le bootstrap (échafaudage). Elle consultera les lois acoustiques de ⚙️ (`acoustique/portee-voix.js`, stub prêt) et sa viz existe déjà : les bulles (🖥️ `presentation.dire()`).

## Observables

| Feature | Mécanique | Viz |
|---|---|---|
| `unite-drill` | ordreDrill = les habitudes avant/arrière rendues mécaniques | calque `formation` (via doctrine 🧠) |
| `forme-ouverte` | la forme cible, donnée au niveau unité | calque `formation` |

## Croissance attendue

Canaux multiples (étendards, cors, tambours), chaînes de relais, déformation des messages, rumeurs, reconnaissance ami/ennemi, liens de camaraderie, largeur de forme adaptée à l'espace (décision du chef).
