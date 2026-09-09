# Charmed 3 — « La Reine des Enfers »

Le dossier de préparation de la troisième partie Charmed, à jouer avec le
système de partie du dépôt. Il ne contient aucun état ; le MJ recopie ce
qu'il faut dans `etat/parties/` le jour où il ouvre.

**Ce qu'on cherche** : faire monter Aurore en jeu, après une seconde partie
gagnée sans perdre un passage (`../07-analyse-charmed-2.md`). Trois choses
qu'elle n'a jamais eu à faire, et qui font toute cette partie :

- **ouvrir une position perdue** — une sœur est déjà de l'autre côté ;
- **retourner** — le bien n'a jamais retourné personne, ici c'est son premier
  coup obligé et il prend quatre tours ;
- **jouer contre deux camps qui ne s'aiment pas** — la Source dans Cole et
  la Voyante veulent deux choses différentes, et l'une trahira l'autre.

| Fichier | Ce qu'il contient |
|---|---|
| [`01-canon.md`](01-canon.md) | la référence série : de la fin de 4x13 à 4x22, ce que Cole, Phoebe et la Voyante ont réellement fait |
| [`02-conception.md`](02-conception.md) | l'époque, les trois camps, les trois racines datées, les fronts, ce qui rend la partie plus dure que la deuxième, les coups permis, les conventions, la table des délais |
| [`03-cartes-de-depart.md`](03-cartes-de-depart.md) | **les cartes de départ** : chaque pièce, sa ligne, son arbitrage, sa portée, sa note de jeu ; les états proposés ; le calendrier ; le compte des mains |
| [`04-ouverture.md`](04-ouverture.md) | `reine-des-enfers.json` avec les deux caractères, les lignes d'ouverture, les items de Radio Halliwell, la marche à suivre |
| [`05-arbitrage.md`](05-arbitrage.md) | la doctrine de l'arbitre : le retournement de Phoebe dans les deux sens, l'enfant, le tonique, la trahison de la Voyante, ce qu'on refuse d'emblée |
| `ouverture.jsonl` | les lignes du §2 de `04`, prêtes pour `--fichier` |

## Le choix en une phrase

**Tour 1 = le soir de 4x19 « We're Off to See the Wizard » : Cole est
couronné Source par le Grimoire, Phoebe a choisi de s'asseoir à ses côtés,
elle porte l'héritier, et la Voyante tient le tonique qu'elle lui fait
boire.** Vingt tours. Le bien (Aurore) doit ramener Phoebe de son plein gré,
puis vaincre la Source avec les trois voix, et arriver au vingtième avec trois
sœurs vivantes et du bien. Cole veut garder sa reine et voir naître son fils.
La Voyante veut l'enfant en elle et le trône pour elle. Les deux camps du mal
sont joués par l'IA, chacun avec sa voix, et **ils ne sont pas alliés**.

## Ce que ça coûte, et ce qu'il faut savoir

- **Deux appels d'IA par tour** au lieu d'un : environ 0,40 $ le tour, huit
  dollars la partie.
- **Les règles du 6.9 s'appliquent** : un `demander` de joueur ne porte ni
  `lieu` ni `tenu_par` (l'arbitre les pose), une clef lève un verrou, un
  maillon n'a pas d'état, pas de consigne. Les lignes d'ouverture de ce
  dossier sont écrites ainsi.
- **Les potions ne se posent plus en parade** (leçon de Charmed 2 : deux
  fioles consumées rejouées). Une potion FRAPPE, et l'arbitre la consume en
  tranchant. Convention 2 de `02-conception.md`.
- Les deux défauts d'écran de Charmed 2 (la case 🎯 qui date d'office, deux
  écritures simultanées avec le même numéro) ont chacun une tâche ouverte ;
  s'ils ne sont pas corrigés au moment d'ouvrir, l'arbitre compense comme il
  l'a fait — en reportant la menace adverse d'un tour, jamais en réécrivant.
