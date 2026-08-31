# « Occupé » se mesure — il ne se déclare pas

Note de mécanique. Ce document dit **pourquoi un booléen tenu à la main a endormi deux personnages sans que rien ne le voie**, **par quoi on l'a remplacé**, et **ce que la nouvelle règle refuse de faire même quand on le lui demande**.

---

## 1. Le défaut, et pourquoi il était invisible

`etat/joueurs.json` porte un champ `occupe` par siège. Il distingue un siège effectivement tenu d'un siège vacant ; aucun moteur automatique ne dépend plus de ce champ.

Le champ était tenu à la main, et personne ne l'avait rebasculé depuis le 9 août. Le 10 au matin, les quatre sièges étaient à `true` alors que deux n'étaient manifestement plus joués. **Ces deux-là n'étaient donc ni joués par un humain, ni activés par la machine : ils dormaient**, avec leur horloge qui continuait d'avancer.

Deux fiches se contredisaient elles-mêmes, ce qui aurait dû suffire à alerter :

- la note de `nicolas-reynolds` disait « **VACANT** pour l'instant : il a donc une tête dans intentions.json » — sous un `occupe: true`, et sans tête ;
- celle de `marlo-vasse` disait « siège **ALTERNE** : joué par le même joueur que Rhaenyra, **jamais en même temps** » — et les deux étaient à `true`.

**`tick.py --verifier` ne pouvait pas le voir**, et c'est le point important. Son invariant était *occupé → pas de tête, vacant → une tête*. Il mesure la cohérence du fichier **avec lui-même**. Or un fichier entièrement périmé est parfaitement cohérent avec lui-même. Il manquait une confrontation au **dehors**.

---

## 2. La définition arrêtée

> **« Occupé » veut dire ACTIF RÉCEMMENT. Ce n'est pas une déclaration, c'est une mesure.**

```
occupé  ⇔  (la veille de sa session date de moins de 2 heures réelles)
        OU (son inbox contient au moins une action non traitée)
```

Le seuil est **une constante nommée, dans un seul endroit** : `SEUIL_OCCUPATION_MINUTES` en tête de [`scripts/occupation.py`](../scripts/occupation.py) (surchargeable par `LE_CONSEIL_SEUIL_OCCUPATION_MINUTES` pour les essais). Deux heures : plus court, on rend vacant un joueur parti se faire un café ; plus long, on laisse dormir un siège une demi-journée.

Le champ `occupe` **reste écrit dans `etat/joueurs.json`**, mais seulement comme **cache**. Il se recale à chaque passage de `sieges.py`. Les lecteurs existants — `serveur/serveur.js`, `depecher.py`, `append_flux.py`, `parvenir.py`, `exporter_aurore.py` — n'ont rien à apprendre. `regence.py` et `tick.py` mesurent et ne dépendent plus du cache.

---

## 3. Quels fichiers de veille comptent, et pourquoi ceux-là

`etat/veille/` mélange des noms de session de toutes provenances : `aurore-inchauspe.json` (le siège), `mj.json` (l'unique MJ), d'anciens noms de régies `mj-*`, des noms courts abandonnés (`aurore.json`, `marlo.json`) et des bricoles (`fix-verif.json`). Un nom de session est libre : `veille.py <ce-que-je-veux>` crée le fichier.

**Règle : pour un siège, ne compte que la veille dont le nom est son `personnage_id`** — sauf si le siège déclare lui-même d'autres noms, dans un champ `veille: ["...", "..."]` de son entrée.

Pourquoi celle-là :

- Le signal voulu est « **la session de CE joueur respire** ». `personnage_id` est le seul nom dont on sache avec certitude à quel siège il appartient — et c'est de fait celui que les sessions arment (les quatre fichiers existent et sont à jour au bon rythme). [`docs/sieges.md`](sieges.md) le dit déjà pour l'ouverture d'un siège : « crée `etat/inbox/<id>/` et **arme `etat/veille/<id>.json`** ». La règle ne fait qu'assumer une convention qui était déjà écrite ailleurs.
- `mj.json` ne désigne aucun siège : l'unique MJ tient le monde pour tous. Le compter rendrait un siège occupé parce que l'arbitre travaille — exactement le mensonge qu'on répare.
- Les anciens fichiers `mj-*` sont des traces de régies retirées et ne comptent jamais implicitement.
- Les noms courts sont des veilles mortes. Les prendre au plus récent ne coûte rien aujourd'hui ; le jour où une session les réveille, ils ressusciteraient une mesure qui ne veut plus rien dire.

**Ce qui compte comme action d'inbox** : un fichier `*.json` non caché. `etat/inbox/marlo-vasse/.gardez` est un jalon qui tient le dossier dans git — il date du 7 août, et pris pour une action il aurait tenu ce siège occupé **pour toujours** : le défaut réparé, remis en place par la porte de service.

---

## 4. Deux marques de main, et pas plus

S'asseoir et se lever sont des gestes datés qui doivent battre la mesure le temps qu'elle rattrape :

| champ | posé par | effet |
|---|---|---|
| `assis_a` | `sieges.py --asseoir` | s'asseoir EST une présence : vaut comme un souffle jusqu'à ce que la session respire d'elle-même |
| `quitte_a` | `sieges.py --quitter` | tout signal **antérieur** à ce moment ne compte plus — sans quoi une veille vieille de trois minutes rallumerait le siège qu'on vient de quitter |

Ce sont des secondes epoch, écrites automatiquement. On n'y touche pas à la main.

---

## 5. Ce que le rafraîchissement refuse de faire

**Un rafraîchissement ne rend jamais vacant un siège qui n'a pas de tête dans `intentions.json`.** Il garde le cache tel quel et **écrit sur `stderr`** :

```
ERREUR occupation : le siege 'nicolas-reynolds' n'est plus actif (veille perimee (10 h))
mais n'a AUCUNE tete dans intentions.json. On le laisse marque occupe : le rendre
vacant empêcherait toute dépêche cohérente en son nom.
```

La raison est directe : une dépêche au nom d'un siège sans tête le ferait agir sans savoir ce qu'il veut. La sortie est écrite dans le message : lui écrire sa tête, puis `sieges.py --quitter <id> --vraiment`.

**Et la garde ne s'arrête pas au refus d'écrire.** Un cache est une commodité : les vérifications signalent tout siège vacant sans tête afin qu'aucune dépêche ne parte en son nom.

---

## 5 bis. La nuit — un défaut tout neuf, créé par la réparation

Tant qu'`occupe` était un drapeau jamais rebasculé, il y avait **toujours** au moins un siège assis. Mesuré, il peut n'y en avoir aucun : deux joueurs qui vont se coucher, et deux heures plus tard la boucle n'a plus d'origine de diffusion. Elle levait alors `horloge du siege principal ou front occupe absent` et **le monde cessait de tourner la nuit**.

`horloge_directe` sépare donc deux questions qu'on avait confondues :

- **qui est exclu de la file ?** — les assis, et eux seuls (plus les vacants sans tête). Ce jeu peut être vide.
- **d'où part le temps ?** — s'il n'y a aucun assis, on retombe sur le roster entier : l'origine reste le siège `principal`, le front reste l'horloge la plus avancée. Les sièges vacants continuent d'être activables, puisqu'ils ne sont pas dans le jeu rendu.

---

## 6. Ce que `tick.py --verifier` attrape désormais

Aux deux invariants historiques (occupé + tête = grave ; vacant sans tête = grave) s'ajoutent quatre confrontations au dehors, dans `verifier_occupation` :

| gravité | ce qui est attrapé |
|---|---|
| **grave** | siège marqué `occupe` alors que plus rien n'y respire — **il dort** |
| avertissement | siège marqué vacant alors qu'il respire (cache périmé, sans danger) |
| avertissement | la **note** de la fiche dit `VACANT` (ou `OCCUPÉ`) contre la mesure |
| **grave** | deux sièges d'une même paire `alterne_avec` mesurés assis **en même temps** — c'est le même humain : l'un des deux est un fantôme |
| avertissement | une note qui dit `ALTERNE` sans que l'entrée porte `alterne_avec` — rien ne peut le vérifier |
| avertissement | `alterne_avec` qui ne désigne pas un siège |
| avertissement | siège tenu occupé par un inbox **qui ne bouge plus** (actions jamais traitées, ou guetteur éteint) |

Les notes ne sont lues qu'en **majuscules**, et c'est délibéré : ces notes crient ce qu'elles affirment (« VACANT pour l'instant », « siège ALTERNE ») et parlent en minuscules du reste (« quand ce siège est occupé, Rhaenyra doit avoir une tête »). Chercher le mot sans égard à la casse rendrait toute prose coupable.

L'alternance est **déclarée**, jamais devinée : `alterne_avec: "rhaenyra"` dans l'entrée du siège. Une note qui parle d'alternance n'est pas une déclaration, c'est un souvenir.

---

## 7. Les commandes

```bash
python scripts/occupation.py                     # la mesure, siège par siège, avec ses raisons
python scripts/occupation.py --json              # la même, brute
python scripts/sieges.py                         # idem, plus les têtes et les fautes
python scripts/sieges.py --rafraichir            # ce qui serait recalé
python scripts/sieges.py --rafraichir --vraiment # recaler le cache
python scripts/tick.py --verifier                # les invariants
python scripts/tests/essai_occupation.py               # le harnais : 30 cas sur un etat/ jetable
```

Le harnais monte un `etat/` temporaire à chaque cas (veilles vieillies à la main par `os.utime`, inbox peuplée, marques posées) et ne touche jamais au dépôt. Il couvre la mesure, le `.gardez`, les veilles déclarées, `assis_a`/`quitte_a`, le refus d'écriture, l'atomicité de l'écriture, et les sept fautes de `verifier_occupation`. **Ajouter un cas avant de toucher au seuil ou aux règles de veille.**

`sieges.py --asseoir` / `--quitter` n'ont pas changé de sens : ils posent la marque de main, retirent ou exigent la tête, et laissent le rafraîchissement recaler `occupe`. Ils ne réécrivent plus le roster entier depuis une lecture vieille de trois étapes — les deux écritures relisent le fichier juste avant de poser, par `os.replace`, et ne touchent que leurs propres clefs.

---

## 8. Ce qu'on n'a pas fait

- **On n'a pas changé la définition de l'inbox.** « Au moins un fichier » est la règle arrêtée, et elle a un angle mort : un inbox qu'on ne vide jamais tient un siège occupé pour toujours. On ne l'a pas corrigée en douce (ce serait décider à la place du propriétaire) ; on l'a **rendue visible** par l'avertissement « inbox dormant ». Le jour où l'on veut trancher, c'est une ligne dans `mesurer`.
- **Le seuil ne s'adapte à rien.** Deux heures pour tout le monde, quel que soit le rythme de la partie.
- **Rien ne surveille en continu.** Le recalage a lieu lors d'un appel à `sieges.py`. Entre deux, le cache vieillit — et `tick.py --verifier` est là pour le dire.
- **Le serveur ne mesure pas.** Il lit le cache, comme avant. Une page ouverte pendant qu'un siège bascule verra l'ancienne valeur jusqu'au rechargement.

---

## 9. Proposition pour `CLAUDE.md` — à relire avant d'insérer

Ce paragraphe n'a **pas** été appliqué. Il se placerait dans « Les sièges — changer de personnage », juste après la phrase « Le champ `occupe` dit où l'on est assis en ce moment, et toute la règle en découle ».

> **« Occupé » ne se déclare pas : ça se mesure.** Un siège est occupé quand la veille de sa session date de moins de deux heures réelles, ou quand son inbox porte une action non traitée. Rien d'autre. Le champ `occupe` de `etat/joueurs.json` n'est plus qu'un cache de ce calcul, recalé à chaque passage de `scripts/sieges.py` — et `python scripts/sieges.py` affiche désormais la MESURE, avec l'âge de la veille et le compte de l'inbox, jamais le drapeau brut.
>
> **Pourquoi ça n'est pas un détail de tenue d'état.** Un drapeau oublié ment sur le siège réellement tenu et fausse les outils qui protègent la perspective du joueur.
>
> **Ce qui est refusé, même demandé.** Un rafraîchissement ne rend jamais vacant un siège sans tête : il garde le cache et crie. Écrivez-lui d'abord ce qu'il veut, croit et poursuit, puis `python scripts/sieges.py --quitter <id> --vraiment`.
>
> **Une paire alternée se DÉCLARE** — `alterne_avec: "<autre siège>"` dans l'entrée du siège, pas dans une note. Deux sièges alternés mesurés assis en même temps sont impossibles (c'est le même humain) et `tick.py --verifier` le dit en grave.
>
> Mécanisme complet, règle sur les fichiers de veille, mesures et limites : [`docs/occupation.md`](docs/occupation.md).
