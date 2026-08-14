# La régence — un siège vacant qui joue tout seul

Note de mécanique. Ce document dit **comment un siège que personne n'occupe agit dans le monde**, **la seule chose qu'il n'a pas le droit de faire**, et **ce qu'il rend au joueur qui se rassoit dedans**.

---

## 1. Ce qui existait déjà, et qui ne manquait pas

La reconnaissance a d'abord servi à ne pas écrire un second moteur. Voici ce que les fichiers disent — pas la doctrine, les fichiers.

**Un siège vacant était déjà éligible.** `scripts/boucle_activation.py` élit ses acteurs sur le tissu (`etat/tissu/`), et la seule exclusion qu'il connaisse est `pid in occupes` (`horloge_directe`, `importance`, `mettre_a_jour_energies`). Un siège n'est donc écarté **que tant qu'il est assis**.

> **Depuis le 10 août, `occupes` ne sort plus du champ `occupe` de `etat/joueurs.json` : il se MESURE** — veille de la session de moins de deux heures réelles, ou inbox non vide (`scripts/occupation.py`). Le champ n'est plus qu'un cache. La raison est exactement l'inverse de ce qu'on lisait ici : un drapeau qu'on oublie de rebasculer n'exclut pas seulement un siège assis, il exclut aussi **un siège que plus personne ne tient**, et celui-là dort. Voir [`docs/occupation.md`](occupation.md).
 Mesuré : avec les quatre sièges assis, la file compte 32 acteurs et aucun siège ; Rhaenyra rendue vacante, elle entre **première de la file, à 100 points d'énergie**, au-dessus du seuil d'activation de 10.

**Sa tête était déjà obligatoire.** `scripts/sieges.py` refuse de quitter un siège sans entrée dans `intentions.json`, et `tick.py --verifier` (`verifier_sieges`, plus la garde symétrique dans `verifier_intentions`) tient les deux invariants : occupé + tête = faute grave, vacant sans tête = faute grave.

**Il y avait déjà un validateur mécanique.** Dans `appeler_acteur`, la boucle `for essai in range(3)` appelle `normaliser_rapport_activation` ; tout `RuntimeError` levé là déclenche `mission_correction_narrateur` et renvoie l'arbitre corriger son JSON, sans réveiller ni repayer le PNJ. C'est le point d'accroche, et il n'y en a pas d'autre.

**Ce qui manquait, donc, tenait en deux choses :** une ligne qu'un siège ne franchit pas, et une passation.

---

## 2. Pourquoi une ligne, et pourquoi seulement pour les sièges

Un homme de maison qui se trompe coûte une journée. Un **siège** qui se trompe engage le joueur pour le reste de la partie : il retrouverait, en revenant s'asseoir, un serment prêté, une fille mariée, une bataille perdue, un homme pendu. Ce n'est pas rattrapable par une scène ; c'est la partie qui a changé de forme pendant qu'il regardait ailleurs.

Les sept lignes, écrites dans `scripts/regence.py` (`LIGNES_ROUGES`) :

| code | ce qui est interdit | ce qu'il fait à la place |
|---|---|---|
| `serment` | prêter ou rompre un serment, un hommage, une allégeance | préparer la forme, réunir les témoins, fixer une date |
| `mariage` | conclure un mariage, des fiançailles, promettre une main | sonder, chiffrer la dot, écrire le projet au registre |
| `bataille` | livrer bataille, donner l'assaut, engager le combat | poster, reconnaître, chiffrer, tenir la position |
| `mort` | faire tuer, exécuter, mettre à mort | arrêter, garder au cachot, instruire, écrire le chef d'accusation |
| `trahison` | déclarer une trahison, changer de camp, livrer quelqu'un | recueillir, vérifier, écrire ce qu'on soupçonne |
| `reddition` | se rendre, capituler, déposer les armes | tenir, compter, ouvrir un pourparler qui n'engage rien |
| `place-forte` | céder, livrer ou ouvrir une place forte | barrer, doubler le guet, préparer l'évacuation des gens |

**Chaque interdit porte son rabattement, et ce n'est pas de la politesse.** Un garde-fou qui dit seulement non renvoie l'acteur dans le mur au passage suivant : il perd un essai de correction à chaque fois, et au troisième l'activation entière est jetée. Le rabattement est ce qui fait que le refus produit une journée de travail au lieu d'une journée perdue.

---

## 3. Deux gardes, et l'un n'excuse jamais l'autre

**Dans sa tête — pour qu'il n'essaie pas.** `regence.py --poser <id> --vraiment` écrit dans son entrée d'`intentions.json` une `croyance` et un `declencheur`, et rien d'autre : ce sont des champs de `docs/schema.md`, aucun champ n'est inventé. Le déclencheur dit ce qu'il fait quand une affaire bute sur la ligne — il s'arrête au bord, prépare tout, note à qui la décision revient et ce que le retard coûte.

La même contrainte est aussi posée dans son dossier d'activation (`dossier_activation` → `contrainte_regence`), rendue en clair dans le manuel que reçoit l'acteur (`depecher.memoire_activation`, section « Ce que tu ne conclus pas ») et visible dans le dossier fermé de l'arbitre. Elle est **vide pour tout le monde sauf un siège vacant** : un acteur ordinaire ne voit rien de tout cela.

**À la validation — pour le rattraper quand il oublie.** `regence.verifier_rapport_activation(pid, rapport)` est appelé dans `normaliser_rapport_activation`, **avant** `filtrer_mutations_applicables` — c'est-à-dire avant que la moindre mutation touche `etat/`. Passé cette ligne il serait trop tard : les activations écrivent directement dans l'état, il n'y a plus de purgatoire de staging.

Ce qu'il lit, et rien d'autre : le verbe et ce que l'acteur dit avoir fait (`activites[].action`), l'état qu'il déclare produit (`resultats_produits[].quoi|apres`), son blocage, la suite qu'il annonce, et les mutations qu'il propose. **Il ne lit ni ses sources ni son dossier** : citer un serment dans un registre n'est pas en prêter un.

---

## 4. La détection est lexicale, et voici jusqu'où elle va

Le rapport d'activation est de la prose française arbitrée par le narrateur. Il n'y a rien d'autre à lire — pas de champ « j'ai prêté serment ». La détection est donc une affaire de motifs, avec deux correctifs :

- **Les évitements.** Une marque de négation, de report ou de mise en hypothèse **immédiatement avant** la formule (à deux mots près) classe l'occurrence comme *évitée* au lieu de *franchie*. « Il n'a pas prêté serment », « elle refuse de livrer bataille », « elle garde pour la reine la décision d'épouser » passent — et c'est exactement ce qu'on veut lire d'une régence bien jouée. L'ancrage compte autant que la liste : chercher « ne » n'importe où dans la fenêtre innocenterait « il refuse de fuir **et donne l'assaut** ».
- **Les citations.** Un verbe de parole suivi d'une complétive dans les 30 caractères qui précèdent (« le registre dit que Borros a rompu son serment ») classe aussi en évitée. C'est le point le plus permissif du dispositif, et c'est assumé : la clause dans sa tête est le premier garde, et un refus coûte un essai de correction, pas la partie.

**Mesures.** Sur les 107 rapports d'activation réellement produits par la partie (`etat/staging/activations/`) : **0 faux positif**. Sur un jeu de 19 phrases qui franchissent pour de bon, une par ligne au moins : **19 détectées**. Sur 11 phrases voisines qui ne franchissent pas : **11 laissées passer**.

**Ce qu'elle ne saura jamais faire :** une périphrase inventive (« il donne sa parole d'homme lige », « la place changera de bannière au matin ») passe. C'est pourquoi la clause dans sa tête n'est pas décorative — elle est le garde qui comprend, et la détection celui qui compte. Ajouter un motif à `LIGNES_ROUGES` est une ligne de code, et le fichier d'essai du dépôt sert à vérifier qu'on ne casse rien.

---

## 5. Ce qu'on hérite en se rasseyant

Chaque activation d'un siège vacant est consignée dans **`etat/joueurs/<id>/regence.jsonl`** (append-only, une ligne par activation) : la date du monde, la tâche, l'issue, ce qu'il a fait, **ce qui engage désormais** (ce qu'il a communiqué, ce qu'il a produit, et toute mutation touchant `plis`, `relations`, `evenements`, `books`, `mains`), les lignes évitées, les lignes franchies s'il en reste, et le chemin du rapport complet.

`python scripts/sieges.py --asseoir <id> --vraiment` **rend cette liste au joueur** et l'écrit dans `etat/joueurs/<id>/regence-<horodatage>.md`, puis pose une ligne `passation` dans le registre : ce qui a été rendu ne sera pas rendu deux fois. Quatre sections, dans cet ordre : ce qui a été fait · ce qui vous engage désormais · ce qu'il a laissé pour vous (les lignes où il s'est arrêté, c'est-à-dire les décisions qui vous reviennent) · et, s'il y a lieu, l'alerte des lignes franchies malgré la garde.

Ce n'est pas un résumé narratif. C'est une liste de faits datés avec leurs sources, faite pour être relue avant de rejouer.

---

## 6. Les gardes de `tick.py --verifier`

Aux deux invariants qui existaient (occupé + tête = grave ; vacant sans tête = grave) s'ajoutent :

- **avertissement** — siège vacant dont la tête ne porte pas la clause de régence ;
- **avertissement** — siège désormais occupé dont des décisions de régence n'ont jamais été rendues ;
- **grave** — lignes irréversibles franchies malgré la garde, inscrites au registre.

---

## 7. Les commandes

```bash
python scripts/regence.py                       # les sièges en régence, leur clause, ce qu'ils doivent
python scripts/regence.py --clause <id>         # la clause, sans rien écrire
python scripts/regence.py --poser <id> --vraiment
python scripts/regence.py --verifier <rapport.json>   # passer un rapport au crible
python scripts/regence.py --compte-rendu <id>   # la passation, sans la marquer remise
python scripts/sieges.py --asseoir <id> --vraiment    # rend et marque la passation
```

---

## 8. Ce qu'on n'a pas fait, et ce qu'il faut savoir

- **Le budget d'échelle ne change pas.** Un siège vacant est un acteur d'`intentions.json` comme un autre ; son échelle décide de son coût de simulation, et rien dans la régence ne la relève.
- **L'origine de la diffusion se déplace.** `horloge_directe` prend pour source le siège `principal` **parmi les occupés** : vacant, Rhaenyra cède l'origine au premier siège assis, et le calendrier de disponibilité change avec elle. C'est le comportement existant, pas un effet de la régence — mais il explique qu'en la libérant, la file passe de 32 à 18 acteurs disponibles.
- **Tous les sièges vacants à la fois n'est pas un cas supporté.** Sans un seul siège assis, `horloge_directe` lève « horloge du siège principal ou front occupé absent » et la boucle s'arrête. Une partie sans joueur n'a pas de présent : on n'a pas cherché à lui en donner un.
- **Un siège vacant peut monopoliser la file.** Il entre haut (100 points chez Rhaenyra) parce que la normalisation se cale sur le plus fort nœud activable et qu'il n'est plus exclu. La rotation (`rotation_activation`) l'empêche d'être élu deux fois dans le même tour ; on n'a pas ajouté de bride supplémentaire avant d'avoir vu tourner la chose.

---

## 9. Proposition pour `CLAUDE.md` — à relire avant d'insérer

Ce paragraphe n'a **pas** été appliqué. Il se placerait dans « Les sièges — changer de personnage », après « Écrire la tête d'un siège qu'on quitte est un acte de jeu, pas une formalité. »

> ### Un siège vacant joue tout seul — mais il n'engage rien pour toujours
>
> Une tête ne suffisait pas : elle disait ce qu'il veut, elle ne le faisait pas agir. **Un siège vacant entre désormais dans la file d'activation comme n'importe quel acteur** — même énergie, même fenêtre, même tâche élue, même rapport déposé et mêmes mutations écrites. Il n'en était exclu que parce qu'il était assis ; il ne l'est plus dès qu'on se lève. C'est ce qui empêche un personnage qu'on quitte de dériver en sommeil pendant que son horloge, elle, continue d'avancer.
>
> **Il a le droit de tout faire, sauf sept choses.** Pas de serment prêté ni rompu, pas de mariage, pas de bataille livrée, pas de mort ordonnée, pas de trahison déclarée, pas de reddition, pas de place forte cédée. Ce ne sont pas des actes qu'on préférerait éviter : ce sont ceux que le joueur retrouverait **faits** en se rasseyant, et qu'aucune scène ne défait. Devant l'une d'elles, le siège va jusqu'au bord — il prépare, il chiffre, il écrit à qui la décision revient et ce que le retard coûte — puis il s'arrête et le dit.
>
> Cette limite est écrite dans sa tête (`python scripts/regence.py --poser <id> --vraiment` : une croyance, un déclencheur, rien hors schéma) **et** vérifiée mécaniquement quand son rapport est validé, avant que rien ne touche `etat/`. Un rapport qui franchit est refusé et l'acteur se rabat, sans perdre sa journée.
>
> **Ce qu'il décide seul se consigne, et se rend.** Chaque activation en régence entre dans `etat/joueurs/<id>/regence.jsonl` avec sa date, ses faits et ce qui engage désormais. `python scripts/sieges.py --asseoir <id> --vraiment` rend la liste au joueur, l'écrit en clair dans son dossier, et marque la passation : ce qui a été rendu ne l'est pas deux fois. Le joueur reprend son siège en sachant ce qu'il hérite — y compris ce qu'il n'aurait pas décidé, ce qui reste le sujet.
>
> Mécanisme complet, mesures et limites : [`docs/regence.md`](docs/regence.md).
