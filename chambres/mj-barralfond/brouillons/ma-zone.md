# Barralfond — ce que l'état en dit (relevé le 129.4.5, premier établi)

Tout ce qui suit est LU, avec sa source. Rien d'inventé. Ce qui n'y est pas,
je ne le sais pas.

## La ville — `etat/lieux.json`

`barralfond` · « Barralfond » · région **Au-delà du Mur** · type ville ·
`controle_id: null` — personne ne la tient · **34 jours de Port-Réal**, la
plus lointaine de la table. Alias : `le-creux`, `sous-l-arbre`.

Trente-quatre jours : un pli parti d'ici n'a de réponse qu'à plus de deux
lunes. Toute audience qui suppose un ordre venu du sud suppose donc un ordre
vieux de deux lunes. À vérifier avant de trancher, jamais après.

## Les salles — `etat/presence.json` (bloc `resolu`, routines du jour)

| salle | lieu écrit | qui y tient |
| --- | --- | --- |
| `la-souche` | La Souche, le tronc creux | Wenna la Nommeuse — et c'est la salle du siège |
| `arbre-des-ages` | L'Arbre des Âges | Sarn Vieux-Sang |
| `lit-des-racines` | Le Lit des Racines | Bren Racine-Grise |
| `etabli` | L'Établi | Ygga Main-de-Pierre |
| `bassin-noir` | Le Bassin noir | Toll Œil-Noir |
| `clairiere` | La clairière | Nicolas Reynolds |

Le bloc `presence` (dernier vu) les met tous les six à `la-souche` au
**129.4.3**, minutes 767 à 785 : ils s'y sont trouvés ensemble ce jour-là.
Depuis, chacun est rentré à sa salle par routine.

## Les six — `etat/personnages.json`

Cinq Premiers Hommes créés le 129.4.3, tous `actif` / `libre`, `maison_id:
null`, `lieu_id: barralfond`, tous portant la même note : **ils touchent au
MOTEUR — le grain de la réalité — jamais à l'état joué du royaume.**

- **Sarn Vieux-Sang** (né 68, 61 ans) — lit les anneaux, se souvient de ce
  qu'on a déjà tenté. Parle lentement, une fois. Va droit au précédent.
- **Bren Racine-Grise** (né 91) — descend au Lit des Racines, voit toute la
  nappe et ce qui s'y accroche. Nomme les appelants un par un ; rentre avec
  des faits, pas des avis.
- **Ygga Main-de-Pierre** (née 95) — tient l'Établi, rend l'ouvrage fini et
  la ligne au cahier déjà écrite. Finit ce qu'elle ouvre.
- **Toll Œil-Noir** (né 88) — tient le Bassin noir, donne le chiffre qui
  tranche et la cause quand il ne tombe pas juste. Fourchette plutôt que
  doute.
- **Wenna la Nommeuse** (née 99) — grave les noms. Le mot juste, plus les
  deux écartés et pourquoi. Écrit court.

Et **Nicolas Lesster Reynolds** (né 97), cadet de Pierrefitte, *l'Équerre* —
maison-reynolds, écritoire de ceinture et fil à plomb. « Ne parle d'une
affaire qu'en nommant qui la tient. » A servi la couronne noire à Lamarck
(126), Peyredragon (127), Port-Réal (128) ; monté à Barralfond le 129.4.3.

## Le siège — `etat/joueurs.json`

Jeton `equerre-plomb-2718`, rôle *second*, `occupe: false`, `lieu:
barralfond`, `salle: la-souche`. **Son arbitre déclaré est `mj-barralfond` —
moi**, et la note du siège dit pourquoi : `serveur/routes/joueur.js:45` et
`scripts/agents/zone.py arbitre_de()` le rendent tous les deux.

Le siège est VACANT : il a une tête dans `intentions.json` et le monde le
joue comme un absent. Ses six PNJ sont les cinq architectes plus
`yohanna-reynolds`.

## Ce que je n'ai PAS trouvé, et que je ne saurai donc pas dire

- Aucun bâti, aucune carte, aucun maillage de Barralfond dans `monde/` — il
  n'y a là que Peyredragon et Port-Réal. Ma ville n'a pas de plan.
- Aucun `controle_id`, aucune maison, aucune garnison : rien ne dit qui
  commande à Barralfond.
- Aucun acte, aucune annale propre à la zone en dehors des six créations.
- Rien sur ce qu'est le Bassin noir, l'Arbre des Âges ou le Lit des Racines
  au-delà de leur nom et de qui s'y tient.

Interrogé là-dessus, je réponds : rien dans les registres ne le porte.
