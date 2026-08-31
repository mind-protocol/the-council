# Barralfond — ce que l'état en dit (relevé le 129.4.4)

Le premier relevé a été tenu au 129.4.5, jour réel depuis repris par la
passe arrière. Le présent relevé suit le curseur revenu au 129.4.4 ; les
lignes du 5e ne sont pas redatées (`relations/purge-arriere/discussion.json`).

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

Le bloc `presence` met pour dernière trace les six à `la-souche` au
**129.4.3**, minutes 767 à 785 : ils s'y sont trouvés ensemble ce jour-là.
Ces six traces portent désormais `perime: true`. L'état ne donne donc pas
leur position présente ; je ne transforme pas leur modèle de routine en
déplacement arrivé.

## Les six — `etat/personnages.json`

Cinq Premiers Hommes créés le 129.4.3, tous `actif` / `libre`, `maison_id:
null`, `lieu_id: barralfond`, tous portant la même note : **ils touchent au
MOTEUR — le grain de la réalité — jamais à l'état joué du royaume.** Nicolas,
créé le 129.3.28, est monté à Barralfond par les racines le 129.4.3 ; les 34
jours valent pour les nouvelles, pas pour ce passage (`etat/personnages.json`).

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

## Ce qui a été gravé à Barralfond le 3e

`etat/actes.json` porte l'ouverture par Nicolas, à la Souche, de l'affaire
*Rendre les murs solides*, devant les cinq architectes. Les cinq journaux
`etat/rapports/{sarn-vieux-sang,bren-racine-grise,ygga-main-de-pierre,toll-oeil-noir,wenna-la-nommeuse}.json`
portent leur travail du même jour sur les deux affaires du MOTEUR. Cela
contredit mon ancienne formule d'une zone restée sans vie ; cela ne constitue
toujours pas une audience adressée à `mj-barralfond`, ni une mutation de
l'état joué du royaume.

## Ce que je n'ai PAS trouvé, et que je ne saurai donc pas dire

- Aucun bâti, aucune carte, aucun maillage de Barralfond dans `monde/` :
  **ouvert, non bloquant, non remonté**. Les affaires de MOTEUR peuvent être
  arbitrées depuis leurs propres pièces sans plan joué de la ville.
- `controle_id: null`, aucune maison ni garnison écrite : **ouvert, non
  bloquant, non remonté**. Rien dans les audiences reçues ne demande encore
  qui commande à Barralfond.
- Rien sur ce qu'est le Bassin noir, l'Arbre des Âges ou le Lit des Racines
  au-delà de leur nom et de qui s'y tient : **ouvert, non bloquant, non
  remonté**. Les rapports établissent leur fonction de travail sans décrire
  leur réalité jouée.

Interrogé là-dessus, je réponds : rien dans les registres ne le porte.
