# Note du MJ d'Aurore au MJ principal — la reine est sortie dans l'antichambre

26e jour, 16h50. **Sur ordre du joueur-directeur** (hors fiction, deux fois : « bouge la reine et
aurore dans l'antichambre — elles doivent se parler », puis « fais le mj d'aurore, et joue la reine
toi même »), j'ai sorti **Rhaenyra ET Aurore** de la Table Peinte pour une scène à deux dans
l'antichambre, et **je joue la reine moi-même** dans cette scène-là.

## Ce qui a bougé sur disque

- `etat/presence.json` : `rhaenyra` et `aurore-inchauspe` sont en `antichambre`
  (« L'antichambre de la Table Peinte, Peyredragon »).
- `etat/flux.jsonl` : un `effacer`, un `recit`, un `geste` de la reine (elle repose le grand livre à
  lacets **sans le refermer**, se lève, ouvre la porte elle-même), une `salle` antichambre, et
  **trois répliques de Rhaenyra**. Audience : d'abord `["aurore-inchauspe","rhaenyra"]`, puis
  `--pour aurore-inchauspe` seul pour la rendre à sa scène privée.
- Horloge : la scène coûte ~6 minutes (16h50 → 16h56).

## Ce que la reine a dit dans l'antichambre — pour que tu en hérites intact

1. Elle reconnaît que **personne n'a répondu aux quatre affaires d'Aurore** nommées à 14h31, et que
   c'était à elle de répondre ; elle a enchaîné sur la mesure de la coupe à la place.
2. Elle constate qu'Aurore n'a pas dormi et **refuse de lui dire d'aller se coucher** (« je sais ce
   que ça vaut, qu'on me le demande »).
3. Elle exige l'ordre d'urgence, pas l'ordre du récit : **ce qui se tranche avant la nuit d'abord**,
   et elle a dit qu'elle **ne rentre pas dans la salle tant qu'Aurore n'a pas fini**.

## La collision, et ce qu'elle a coûté

Pendant que je poussais, ta session a continué le conseil à la Table Peinte avec des items
`--pour tous` (16h12 → 16h56 : Gerardys, Denys, Rulf, Hask, Alys, et **la reine**). Ces items
tombent sur l'écran d'Aurore et la ramènent dans une salle où son personnage n'est plus, **et la
reine s'y trouve jouée à deux endroits en même temps**.

Tant que cette scène dure : **la reine n'est pas dans ta salle.** Ne la fais plus parler à la Table
Peinte, et pousse tes items du conseil `--pour marlo-vasse` (ou sans Aurore dans la liste) plutôt
que `--pour tous`.

## Piège technique à connaître — il m'a mangé quatre pushes

`append_flux.py --pour a,b` **ne découpe pas sur la virgule** : le `pour` part en CHAÎNE, et
`serveur/serveur.js` (l.259-260) compare une chaîne par égalité stricte. Résultat : l'item n'est
servi à **personne**, sans une erreur, sans une ligne perdue. Mes items de 16h12 à 16h38 sont morts
comme ça. Pour deux oreilles, c'est `--messe-basse a,b` (qui, lui, découpe) ou `--pour tous`.
