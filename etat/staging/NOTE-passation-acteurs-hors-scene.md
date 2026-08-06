# Passation — modèle des acteurs hors scène (6 août 2026, 129 AC 3e lune 18e jour)

Écrite par une session de travail **non canonique**, qui a refondu le modèle de simulation
des PNJ pendant que la partie se jouait. Cette session n'écrira plus dans `etat/`.
À lire une fois, puis supprimer.

## Le format a changé — relire `docs/schema.md`

- `intentions.json` : nouveaux champs `echelle` ("scene" | "orbite" | "royaume"), `ignore`
  (ce que le PNJ ne sait pas et qui explique sa conduite), `declencheurs` ({si, alors, une_fois}),
  et un `plan` dont chaque étape est un objet horlogé : `id`, `quoi`, `etat`, `jours_restants`
  (`null` = posture permanente), `depend_de`, `cout`, `si_bloque`, `accompli` (trace optionnelle
  sur une étape close). Budgets par échelle dans le schéma.
- `evenements.json` : nouveau champ `diffusion` — qui apprend la chose, quand, déformée comment.
  C'est le brouillard côté PNJ. **Les croyances d'un PNJ ne changent que par une diffusion échue.**
- `lieux.json` : nouveau champ `alias`. `repaire-aux-corneilles`↔`repos-des-freux`,
  `griffes`↔`ile-aux-pinces`, `sharp-point`↔`pointe-aigue` — les deux familles d'ids sont valides.
- Calendrier acté : 12 lunes de 30 jours.
- `CLAUDE.md` : nouvelle section « Les acteurs hors scène », et « Advance » fait désormais tourner
  DEUX boucles — la salle (élection), puis la boucle hors scène (conséquences) décrite juste après.

## Ce qui a été écrit dans `etat/` par cette session

- `intentions.json` : **entièrement réécrit**. 21 têtes au nouveau format, dont une nouvelle
  (`steffon-darklyn`, qui était `actif` sans tête). Puis réconcilié avec la partie jusqu'au 18e jour.
- `evenements.json` : `diffusion` ajoutée sur `vol-rhaenyra-sombreval`, `recit-darklyn-du-feu`,
  `deposition-steffon`, `couronnement-rhaenyra`. Rien d'autre touché.
- `lieux.json` : `alias` sur trois lieux.

## Ce qui attend un arbitrage de la session canonique

- **Le 19, la nouvelle du couronnement atteint Port-Réal** (corbeau, fiabilité 80). Elle arme le
  déclencheur d'Otto : déchéance proclamée, prix sur les têtes, offre de pardon retirée.
  Otto croit toujours que c'est **Daemon** qui a brûlé la colonne du 16 — le corbeau de Rosby
  disait « on dit Caraxès », à 40 de fiabilité. Personne aux Verts ne sait que la reine a volé.
- **Orwyle** : sa tête était fausse et a été refaite. Il a quitté Port-Réal le 14, deux jours avant
  le feu : il ignore la colonne brûlée, Sombreval, la déposition. Son second déclencheur s'arme
  dès qu'il l'apprend — ses conditions seront périmées avant d'avoir été lues.
- **Gunthor Darklyn** : `gunthor-sacre` est en `bloque`, son `si_bloque` s'est appliqué (frère envoyé).
- Conséquence non écrite à la main : le coût « la plume d'Orwyle » du récit officiel d'Otto est
  devenu introuvable, son `si_bloque` reprend la main — un scribe écrit, le sceau affirme.

## Les outils

    python scripts/tick.py --verifier          # audit de cohérence, en début de session
    python scripts/tick.py --jusqu-a 129.3.21  # ce qui tombe dans la fenêtre
    python scripts/tick.py --jours 3 --acteur otto --acteur criston

    python scripts/appliquer.py <fichier>              # blanc : ce qui changerait
    python scripts/appliquer.py <fichier> --vraiment   # écrit

`tick.py` n'écrit QUE dans `etat/staging/` et ne décide rien. `appliquer.py` est son pendant :
il applique les `mutations_proposees` d'une proposition — le tick y rédige d'office l'arithmétique
(horloges, nouvelles livrées), tu ajoutes les tiennes à la main dans la même liste. Vocabulaire
fermé, validation intégrale avant toute écriture, refus si l'état a bougé depuis le calcul,
et marquage contre la double application. L'audit passe à 0 anomalie au moment de cette passation.

**Corrigé au passage** : la diffusion était livrée quel que soit le statut de l'événement. Un
événement `annule` diffusait quand même sa nouvelle, et un `a-venir` faisait arriver la nouvelle
d'une chose qui n'avait pas eu lieu. Désormais : `resolu` → livrable, `a-venir` → suspendue
jusqu'à ton arbitrage, `devie`/`annule` → jamais.

## Une proposition DÉJÀ APPLIQUÉE — ne la rejoue pas

`PROPOSITION-diffusion-canon-aval.json` a été **appliquée** (elle porte son `applique_le` ;
`appliquer.py` refusera de la repasser). Elle a ajouté 13 entrées de `diffusion` à six événements
canon en aval qui n'en avaient aucune : `mort-lucerys` (4), `sac-sombreval` (3), `sang-et-fromage` (2),
`prise-harrenhal` (2), `chute-otto` (1), `ralliement-trident` (1). Seul `evenements.json` a été écrit.

Deux d'entre eux arrivent à Peyredragon **en deux temps** — une première nouvelle partielle et fausse,
puis la confirmation quatre jours plus tard : pour Lucerys, d'abord un corbeau sec de Borros disant
seulement qu'Arrax n'a pas reparu, puis ce que les pêcheurs ramènent, et avec ça le nom d'Aemond.

**Rien de tout cela n'est engagé** : ces événements sont `a-venir`, donc leur diffusion est suspendue
et ne partira jamais si le joueur les fait dévier. Il y a 32 entrées de diffusion en tout dans
`evenements.json`, dont 6 rattachées à des événements déjà `resolu` — celles-là, elles, attendent
vraiment ta livraison. Les quatre du couronnement en particulier : la première arme le déclencheur
d'Otto le 19.
