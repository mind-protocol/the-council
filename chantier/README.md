# Le chantier — les affaires de Barralfond

Ici vivent les affaires qui portent sur le **moteur** : le code de `ecrans/`, de
`scripts/`, de `serveur/`. Elles s'écrivent dans le format d'affaire de la
maison — 🏰 l'affaire · 🎯 l'état cible · 🔒 le verrou · 🗝️ la clef · ⚔️ l'action ·
🔨 le moyen · 🪶 l'office — parce que c'est le seul format qu'on ait qui oblige à
la **remontée** : une action qui ne remonte à aucun état cible n'a pas de raison
démontrée, et un refacto sans cette règle s'étale jusqu'à ce qu'on l'abandonne.

**Pourquoi un fichier à part et non `etat/books.json`.** Parce que `books.json`
est joué : `tick.py --verifier` le contrôle, `couverture.py` en régénère les
registres, et le `/books` du joueur l'ouvre. Une affaire de refacto qui y entre
devient un volume que la reine peut lire, et un cahier de plus à tenir dans une
partie. Les deux stocks ont le même schéma et pas la même durée de vie.

**La ligne qui ne bouge pas :** les architectes touchent au moteur, jamais à
l'état joué. Le grain de la réalité se retaille ; les vivants, les serments et
les nefs ne se retaillent pas depuis Barralfond. Ce pouvoir-là est celui du
joueur, et il a déjà son mode — « Intervention ».

## Ce que donne chaque salle

| salle | ce qu'on y a sous la main |
|---|---|
| **La Souche** | les affaires ouvertes : ce qu'on veut atteindre, ce qui l'empêche, ce qui le lèverait. On y vient savoir pourquoi on travaille. |
| **Le Lit des Racines** | la nappe entière : de n'importe quel fil on remonte à tout ce qui s'y accroche. C'est d'ici que sortent les verrous que personne n'avait vus. |
| **L'Établi** | les outils et la matière ouverte. C'est ici que la chose se fait, et qu'elle se rend finie. |
| **Le Bassin noir** | l'eau qui montre ce que donne un changement. Ce qui en ressort est tenu, et l'on sait de combien. |
| **L'Arbre des Âges** | les anneaux : chaque état passé du monde. Ce qu'on a déjà tenté, la forme qui avait tenu, et ce qu'il en est resté. |

## Les cinq, et ce que chacun rapporte

- **Sarn Vieux-Sang** — le précédent qui épargne une journée à quelqu'un, avec la
  forme qui avait tenu.
- **Bren Racine-Grise** — la liste entière des accroches, adresses comprises, et
  celle que le nom ne laissait pas deviner.
- **Ygga Main-de-Pierre** — l'ouvrage fini, éprouvé au Bassin, la ligne au cahier
  déjà écrite.
- **Toll Œil-Noir** — le chiffre qui tranche ; et quand il ne tombe pas juste, la
  cause et l'heure du chiffre juste.
- **Wenna la Nommeuse** — le mot juste, avec les deux qu'elle a écartés, pour
  qu'on n'y revienne pas dans un mois.

Ils sont PNJ du siège `nicolas-reynolds`. La Règle Zéro tient : on les dépêche
par `scripts/depecher.py`, on n'écrit pas leurs répliques.

## Plage de numérotation

`90000`–`99999`, réservée au chantier, pour qu'aucune adresse ne collisionne avec
les cahiers joués.
