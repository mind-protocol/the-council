# Tout acteur est un siège en puissance

Note de conception. Ce document dit **ce qui manque** pour qu'on puisse s'asseoir dans n'importe quel personnage de la partie, et **ce qui ne manque pas** — parce que la réponse est contre-intuitive.

---

## 1. Le constat : la mécanique est déjà générique, le dossier ne l'est pas

J'ai cherché où le nom d'un siège est écrit en dur. Il ne l'est nulle part.

`serveur/serveur.js` reconnaît un joueur par son jeton et sert ses croyances depuis `etat/joueurs/<id>/` (`cheminEtat`, `lireCroyance`). `scripts/append_flux.py` lit le roster pour décider l'audience d'un item. `scripts/tick.py` en tire ses deux gardes (`verifier_sieges`). `scripts/presence.py` sait déjà qu'**un joueur n'a pas d'emploi du temps** et le lit du roster. `scripts/veille.py` et `scripts/purger.py` balaient `etat/joueurs/` par itération. Aucun de ces six fichiers ne connaît le mot « rhaenyra », « aurore » ou « marlo ».

Autrement dit : **ouvrir un troisième siège n'a rien coûté au code. Il a coûté `docs/siege-voix.md` — 238 lignes écrites à la main — et 20 mutations collées une à une.**

L'état de la partie aujourd'hui :

| | nombre |
|---|---|
| personnages | 86 (59 actifs, 24 dormants) |
| têtes dans `intentions.json` | 53 — dont **9 `scene`**, 20 `orbite`, 24 `royaume` |
| voix engendrées | 74 |
| portraits SVG | 38 |
| sièges ouverts | **3** |

Le goulot n'est donc pas la tuyauterie. C'est qu'un siège demande aujourd'hui **une page de conception par personnage**, et qu'une page par personnage ne passe pas à l'échelle de 86.

---

## 2. Ce qu'un siège doit porter — le contrat en six lignes

Un joueur qui s'assoit a besoin de six choses, et pas d'une de plus. C'est la liste qui sert de spécification à tout le reste.

1. **Où je suis, à quelle minute.**
2. **Ce que je crois tenir du monde** — et avec quelle certitude.
3. **Ce que j'ignore** — non pas comme une lacune, mais comme le moteur : le brouillard qui explique ma conduite.
4. **Ce que je veux**, avec des échéances.
5. **Qui m'obéit, et qui me juge.**
6. **Ce que mon métier m'a appris** — gratuitement, sans qu'un PNJ me l'explique.

Le manuel pose déjà la sixième pour Rhaenyra, en prose, dans `CLAUDE.md` : *« Le personnage SAIT ce que sa vie lui a appris »*. Elle n'est écrite nulle part pour personne d'autre. C'est le vrai trou.

---

## 3. Cinq lignes sur six se DÉRIVENT — la tête est le dossier, à l'envers

Une tête d'`intentions.json` est exactement l'information dont un joueur a besoin, rangée pour le MJ. On s'assoit dedans en la retournant.

| Le siège doit porter | Ça existe déjà ici | Dérivation |
|---|---|---|
| Où je suis, quand | `personnages.lieu_id`, `presence.py`, `monde.date` | `horloges.json[<id>]` ← `monde.date` ; exception de présence posée au lieu réel |
| Ce que je crois du monde | `intentions[<id>].croyances` | → `joueurs/<id>/vues.json` (une croyance qui situe quelqu'un) et `jetons.json` (une croyance qui chiffre une force, une place, un pli). `certitude: rapportee` par défaut ; `sure` si un `actes.json` me compte dans ses `temoins` |
| Ce qui m'est parvenu, et par qui | `evenements.diffusion` livrées où `qui` me nomme ou `ou` = mon lieu | → entrées `info.json` avec `destinataire_id` (le champ existe déjà et n'est utilisé par personne) |
| Ce que j'ignore | `intentions[<id>].ignore` | recopié tel quel dans la fiche de prise en main — c'est ce qu'on donne au joueur comme tension, pas comme manque |
| Ce que je veux | `intentions[<id>].plan[]` étapes `en-cours` | → `objectifs.json` : `quoi` → `titre`, `jours_restants` → `echeance`, `cout` → `description`, `si_bloque` → ce que je perds |
| Ce qui me guette | `declencheurs[]` | → une ligne chacun dans la fiche : « si ceci arrive, je saute » |
| Ce que j'ai appris ces jours-ci | `travaux.json` où `qui` = moi | → mes pensées datées deviennent mon amont : je m'assois avec du travail en cours, pas à froid |
| Mes registres | `books.json` où `acteur_id` = moi | rien à faire : ils me suivent déjà, `prive: true` compris |
| Mes mains | `mains.json` où `porteur.id` = moi | rien à faire |
| Qui me juge | `relations.json` où `cible_id` = moi | → la fiche : les cinq opinions qui comptent |
| Qui m'obéit | roster `pnj[]` | à écrire (voir §4) |

**Rien de tout cela n'est un jugement.** C'est de la recopie avec changement de repère — exactement comme le tick est de l'arithmétique. Ça appartient donc à un script, pas à moi.

---

## 4. Ce qui ne se dérive pas : DEUX pages, et c'est tout le travail humain

### `metier.md` — ce que sa vie lui a mis dans la tête

Une demi-page, à la première personne du savoir : ce que ce personnage sait d'office et qu'on ne doit jamais lui faire découvrir. Pour Rulf Corne, vingt-deux ans de maître de port : il sait à l'œil ce qu'une coque tire chargée, il sait qu'un capitaine qui ment sur son port d'escale le fait toujours sur la même ligne du livre, il connaît le nom des onze patrons de la rade et lequel boit. Pour Gerardys : la forme d'une lettre qui engage, ce qu'un corbeau coûte, ce qu'on n'écrit jamais.

Sans cette page, un joueur assis dans Rulf Corne joue un touriste dans un port — et le MJ improvise son métier à chaud, c'est-à-dire mal.

### `charge.md` — ce que ce fauteuil peut MOUVOIR

Trois questions. Un siège qui n'y répond pas est un siège mort, et le script doit refuser de l'ouvrir sans qu'on le dise tout haut.

1. **Qui m'obéit ?** Au moins un nom qui exécute sans que je demande la permission. Sinon je ne peux que parler.
2. **Qu'est-ce que je tiens que personne d'autre ne tient ?** Un canal, un registre, une clef, une porte, un compte, une somme. Sinon je suis un témoin, pas un joueur.
3. **Qui peut me refuser ?** Sans personne au-dessus, le siège n'a pas d'enjeu ; avec seulement des gens au-dessus, il n'a pas de marge.

Le siège d'Aurore tient debout parce que ces trois réponses sont chiffrées : quatre corbeaux en propre, deux cents dragons pour l'année, un scribe deux jours par lune, un siège au conseil de sept heures — et la reine peut tout retirer.

### Et c'est ici que la chose devient élégante

**Un PNJ ne devient pas jouable : il devient CHARGÉ.** `charge.md` n'est pas une fiche d'administration, c'est le compte rendu d'une scène — celle où quelqu'un lui a donné les leviers. Aurore n'est pas devenue jouable parce qu'on a créé un dossier : elle l'est devenue le 22e, quand la reine a fait écrire l'office au registre.

Donc la règle : **ouvrir un siège est un acte de jeu.** Si le fauteuil ne meut rien, ce n'est pas au script de le réparer — c'est à une scène. On joue la scène, on écrit le mandat, et alors on s'assoit.

---

## 5. Le script — `scripts/sieges.py --ouvrir` / `--fermer`

On garde un seul script ; il gagne deux verbes.

```
python scripts/sieges.py --ouvrir rulf-corne            # blanc : dit ce qui serait écrit
python scripts/sieges.py --ouvrir rulf-corne --vraiment
```

Ce qu'`--ouvrir` fait, dans l'ordre :

1. **Refuse** si le personnage n'existe pas, est `mort`, ou a déjà un siège.
2. Engendre un jeton dans le style existant (`noyer-brasier-4417`) et ajoute l'entrée au roster, `occupe: false`.
3. Crée `etat/joueurs/<id>/` : `journal.json` (vide, `personnage_joueur_id` et `maison_joueur_id` renseignés), `vues.json` et `jetons.json` **dérivés des croyances**, `objectifs.json` **dérivé du plan**, `reglages.json` (défauts 50/50), et deux gabarits vides `metier.md` et `charge.md` avec leurs trois questions en commentaire.
4. Crée `etat/inbox/<id>/` et arme `etat/veille/<id>.json`.
5. Pose `etat/horloges.json[<id>]` = `monde.date`.
6. **N'assoit personne.** Le siège est ouvert, vacant, avec sa tête intacte — donc il continue d'agir. On s'y assoit ensuite par `--asseoir`, qui archive la tête comme aujourd'hui.
7. **Imprime les trous**, et c'est la moitié de la valeur du script :
   - pas de tête → rien à dériver, tout est à écrire
   - tête `royaume` (1-3 croyances) → « ce joueur va s'asseoir devant un monde vide, montez-le en `orbite` d'abord »
   - `metier.md` ou `charge.md` vide → « siège mort, jouez la scène qui le charge »
   - pas de portrait, pas de voix, pas de corps lié, pas de routine
   - aucun nom dans `pnj[]` → personne ne lui obéit

`--fermer <id>` fait le chemin inverse et **n'écrit rien dans `etat/`** : il dépose dans `etat/staging/` un **brouillon de tête** — objectifs `en-cours` → étapes horlogées, `vues`/`jetons` récents → croyances, événements résolus dont aucune diffusion ne l'a touché → `ignore`, derniers résumés de `journal.scenes` → `intention`, `relations` vers le joueur principal → `attitude_joueur`. Le MJ le relit, l'arbitre, l'applique. Un seul écrivain, comme partout ailleurs.

C'est le geste le plus dangereux du système — quitter Rhaenyra sans lui écrire de tête la met en sommeil pour trois lunes — et c'est aujourd'hui celui qui est le moins outillé.

---

## 6. Trois profondeurs, pas une

« Chaque acteur incarnable » ne veut pas dire 86 dossiers écrits d'avance. Ça veut dire que le coût d'en ouvrir un est connu et petit.

| Profondeur | Qui | Coût d'ouverture |
|---|---|---|
| **D'office** | les 9 têtes `scene` | la commande, plus les deux pages. **Une demi-heure.** |
| **Après montée** | les 20 têtes `orbite` | monter la tête à 4-6 croyances et 3-5 étapes, puis comme ci-dessus. **Une heure.** |
| **En friche** | les 24 têtes `royaume`, les 33 actifs sans tête, les 24 dormants | écrire une tête, souvent inventer la charge en scène. **Une session.** |

La bonne pente : on n'ouvre pas un siège parce qu'on peut, on l'ouvre parce que quelqu'un veut s'y asseoir — et alors il coûte une demi-heure au lieu de deux jours.

---

## 7. Le plafond réel, et il n'est pas technique

Un siège **ouvert** coûte six fichiers. Un siège **occupé** coûte une session de MJ éveillée — le manuel l'a déjà tranché : *« un joueur sans MJ éveillé est un joueur qui a quitté la partie sans le savoir »*. C'est là qu'est la limite, pas dans le roster.

Deux conséquences à tenir avant d'ouvrir le quatrième :

- **Le `pour` devient obligatoire partout.** `append_flux.py` le sait déjà et refuse d'hériter d'une audience à plusieurs joueurs. À quatre sièges, un item non déclaré n'est servi à personne — ce qui est le bon défaut, mais qui se voit vite.
- **Les listes `pnj[]` se croisent.** La règle du manuel — *un PNJ appartient à qui il RÉAGIT* — reste primaire et suffit. Les listes ne sont qu'un rattachement par défaut : il faut juste que `tick.py --verifier` signale un même PNJ inscrit sous deux sièges, et un siège occupé dont la liste est vide.

Recommandation : sièges ouverts sans limite, **trois ou quatre occupés au plus**.

---

## 8. Ce que ça change dans `CLAUDE.md`

Peu de chose, et c'est bon signe. La section « Les sièges — changer de personnage » gagne trois phrases :

- Tout personnage `actif` est un siège en puissance ; on l'ouvre par `sieges.py --ouvrir`, qui dérive son dossier de sa tête.
- Un siège n'est jouable que s'il meut quelque chose. Les trois questions de la charge sont le test, et la réponse s'obtient **en scène**, pas dans un fichier.
- Le personnage joueur sait ce que sa vie lui a appris : ce savoir s'écrit une fois, dans `etat/joueurs/<id>/metier.md`, et le MJ le lit avant de jouer sa première scène.

`docs/schema.md` n'est pas touché : le dossier de siège est technique, hors schéma, au même titre que `joueurs.json`, `horloges.json`, `presence.json` et `routines.json`.

---

## 9. Chantier — l'ordre, et ce que chaque pas achète

| # | Travail | Achète |
|---|---|---|
| 1 | `--ouvrir` : roster, dossier, inbox, veille, horloge, gabarits, **liste des trous** | ouvrir un siège cesse d'être un rite ; on voit ce qui manque avant de s'asseoir |
| 2 | La dérivation croyances → `vues`/`jetons` et plan → `objectifs` | le joueur s'assoit devant un monde peuplé au lieu d'une carte blanche |
| 3 | `--fermer` : brouillon de tête en staging | quitter un siège cesse d'être le geste qui peut casser la partie |
| 4 | Les deux gabarits `metier.md` / `charge.md` + le test du siège mort | on arrête d'ouvrir des fauteuils qui ne meuvent rien |
| 5 | Gardes `tick.py --verifier` : PNJ à deux sièges, siège occupé sans `pnj`, dossier incomplet | la faute se voit au tick au lieu de se voir en séance |
| 6 | Un siège ouvert pour de bon, en cobaye — `gerardys` ou `robert-quince`, tous deux `scene` | la preuve par l'usage : si ça prend plus d'une demi-heure, le §5 est faux |

Le pas 6 est le seul qui prouve quelque chose. Les cinq autres sont des hypothèses.
