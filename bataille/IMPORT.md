# D'où vient ce dossier

Copié le **1er septembre 2026** depuis `C:\Users\reyno\batailles`, au commit
`c1000e5` (30 août 2026, « La prise de Port-Réal tourne : 2200 ms par seconde de
sim tombent sous 900 »).

**168 fichiers suivis, sans le `.git`** : l'historique du moteur n'a pas été
repris, la copie arrive comme un ajout unique. Le dépôt d'origine existe
toujours et a été **gelé** — voir la note en tête de son `CLAUDE.md`. À partir
d'ici, `la-companie/bataille` fait foi.

## `ordre-de-bataille.json` — le contrat d'entrée, remonté à côté de son preneur

Il vivait dans `archive/bataille/`, seul rescapé du moteur supprimé de ce dépôt
le 30 août. Il est ici parce que [coding/PROPOSITION-moteur-appele.md](coding/PROPOSITION-moteur-appele.md),
§3, le désigne comme point de départ du branchement : le contrat et son preneur
sont désormais dans le même dossier.

⚠ **Sa FORME vaut, pas ses chiffres.** Effectifs, livrées, armes, postures,
terrain, portes : la structure est la bonne. Les valeurs avaient été relevées
sur un moteur qui a été supprimé, ainsi que les rapports d'écart qu'elles
citaient (`docs/bataille/*.md`, partis avec lui). Rien ne lit ce fichier
aujourd'hui, et il ne fait foi sur rien.

## Ce qui n'a pas été fait

- **`bataille/.claude/launch.json` est ignoré** : seul le `launch.json` de la
  racine compte. Pour servir le moteur (`outils/serveur.mjs`, port 4173), il
  faut ajouter l'entrée à la racine.
- **Deux `CLAUDE.md` cohabitent** dans l'arbre. Celui-ci décrit les 8 containers
  et sa propre manière de travailler ; il ne s'applique pas à la racine.
- **Le couplage reste à écrire.** Le conseil produit, le moteur consomme, et
  rien ne les relie encore.

## Correctif du même jour

Le premier passage utilisait `git archive`, qui ne prend que les fichiers
**suivis** : deux fichiers non commités du dépôt gelé manquaient et ont été
copiés à part — `coding/PROPOSITION-moteur-appele.md` (la proposition
d'intégration elle-même, non suivie là-bas) et `.claude/launch.json` modifié.
Total réel dans `bataille/` : **171 fichiers** — 168 suivis, plus la
proposition non suivie, plus `ordre-de-bataille.json` remonté de l'archive, plus
ce fichier.
