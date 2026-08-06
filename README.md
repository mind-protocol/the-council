# Le Conseil

Jdr narratif solo type Crusader Kings 3 dans l'univers de House of the Dragon, joué en session Claude Code : Claude est le MJ, le monde vit dans des fichiers JSON. Départ : 129 AC, mort de Viserys I — la Danse des Dragons commence. Vous incarnez le seigneur d'une maison non-canon des terres de la Couronne. Le canon suit son cours… sauf si vos actes le dévient. Vous ne savez que ce que vos corbeaux, espions et rumeurs vous rapportent — avec délai, et déformation.

## Lancer une partie

Ouvrir une session Claude Code dans ce dossier et dire **« on joue »**. S'il n'y a pas de partie en cours, Claude ouvre la création de maison ; sinon il reprend la scène où elle en était. En jeu : boutons *Play* (jouer la scène), *Advance* (un battement de temps), *Advance til next event* (avancer jusqu'à la prochaine nouvelle qui mérite de vous interrompre), plus 3 choix contextuels et un champ libre.

## Structure

- `SCHEMA.md` — schéma d'état, source de vérité du format des données.
- `CLAUDE.md` — manuel du MJ, chargé par Claude à chaque session.
- `etat/*.json` — l'état du monde : monde, maisons, personnages, relations, lieux, evenements, infos (ce que VOUS savez), paroles, actes, intentions (têtes des PNJ — jamais montrées), journal.
- `ecrans/` — templates HTML des widgets (scène, création) et portraits.
- `docs/` — notes de conception.
