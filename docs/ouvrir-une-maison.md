# Ouvrir une maison — le process

`docs/plans-den-face.md` dit ce qu'est un plan d'en face et pourquoi on l'écrit.
Ce fichier-ci dit **comment on ouvre une maison de bout en bout**, dans quel ordre,
et où l'on s'arrête. Il vaut pour Rosby comme pour les Verts.

Une maison « ouverte », c'est : des gens qui ont un nom et une charge, des chiffres
qui tiennent, des têtes qui poursuivent quelque chose, et — pour les seules maisons
qui le méritent — un plan dérivé de ces têtes. Rien de plus.

## 0. Le tri — trois paliers, pas dix-neuf maisons

La faute qui guette est d'appliquer le gabarit complet aux dix-neuf maisons du
tableau. Le tri se fait par la règle des mains : **par quelle bouche, ou par quel
empêchement, cette maison atteindra-t-elle le joueur cette lune ?**

| Palier | Ce qu'on écrit | Ce qu'on n'écrit pas |
|---|---|---|
| **A** — elle touche le joueur cette lune | gens + ressources + têtes + plan complet dans `plans.json` | — |
| **B** — elle pèse, mais de loin | chef + une tête `royaume` + ressources | pas de plan, pas de mains |
| **C** — décor | fiche maison + un chef dormant | ni tête, ni plan, ni mains |

Un palier n'est pas un jugement de valeur, c'est un budget. Une maison monte de
palier le jour où une nouvelle la met sur la route du joueur, et redescend quand
elle en sort — même geste que l'échelle d'une tête.

**Ligne de partage à ne pas rater** : `plans.json` est pour ce qui n'est PAS à nous.
Une maison dont un siège est joué (Inchauspé, Reynolds) n'y entre jamais — elle a
besoin de volumes lisibles dans `books.json`, pas d'un plan tenu secret au joueur
qui l'incarne.

## La chaîne — palier A, six étapes

L'ordre n'est pas négociable : chaque étape se nourrit de la précédente, et sauter
la 1 fabrique du décor au lieu de dériver du monde.

### 1. Récolter le canon — avant d'écrire une ligne

Relever dans `etat/evenements.json` les événements `canon` à venir dont la maison
est acteur, avec leurs `conditions` de déviation. Ce sont ses **états cibles datés**
et ses **verrous**, déjà rédigés par l'Histoire. On ne part jamais de la page blanche,
et un plan qui ignore le canon de sa propre maison sera contredit par le tick.

Sortie : une note de travail dans le scratchpad — cibles datées, conditions, sources.

### 2. Les gens — trois à cinq, jamais davantage

- **le chef** — qui décide ;
- **celui qui conteste à l'intérieur** — héritier, cadet, veuve, castellan ambitieux ;
- **un homme de métier** qui tient l'argent, les hommes, ou la porte.

Le troisième est celui qui rend la maison jouable : c'est par lui qu'un chiffre
sortira, et c'est lui qu'on dépêchera. Une maison sans homme de métier ne produit
que des opinions.

Sortie : `personnages.json` (fiches, `maniere`, `condition`), `relations.json` pour
les liens qui comptent au joueur.

### 3. Les ressources — les chiffres avant les intentions

`maisons.json` d'abord : or, revenus, levées, nefs, `suzerain_id`, `controle_id` des
places tenues. Ces chiffres décident ce que ses étapes peuvent coûter — les écrire
après le plan, c'est écrire un plan qu'elle n'a pas les moyens de tenir.

`mains.json` **seulement si** sa mesure doit atteindre le joueur par un chiffre dit
en scène, un `cout` qui bloque un plan, ou une crise qui monte l'escalier. Sinon
c'est la pente du tableur.

### 4. Les têtes — `intentions.json`

Une par acteur retenu à l'étape 2, échelle honnête (`orbite` par défaut ; `scene`
seulement si elle entre dans la salle). Avec, sans exception :

- des **croyances** qui portent leur source et leur date ;
- un **`ignore`** — ce qu'elle ne sait pas et qui explique sa conduite ;
- des **étapes chiffrées**, avec `cout` et `si_bloque` écrit à froid ;
- des **déclencheurs** armés sur le joueur — c'est la seule façon dont un lointain
  lui répond ;
- les entrées de **`diffusion`** qui lui feront changer d'avis, avec leurs dates de route.

### 5. Le plan — dérivé des têtes, dépêché, jamais rédigé de ma main

**On dépêche.** Un plan adverse écrit par le MJ est un plan qui perd, parce qu'il
sort de sa tête et pas de celle du chef :

```bash
python scripts/depecher.py --qui <chef> --mission "dérive ton plan depuis ce que tu crois et ce que tu peux : états cibles datés, verrous, clefs, actions, tensions"
```

L'homme rentre avec ce qu'il a trouvé, y compris ce qui nous contrarie. On verse,
on ne réécrit pas. Puis on met en forme dans `etat/plans.json` :

- une **plage d'ids** réservée par maison (71000 Hightower ; 72000, 73000… ensuite) ;
- chaque pièce porte sa **`source`** — quelle tête, quelle date de maj ;
- chaque verrou porte sa **`portee_pour_nous`** et la route de `diffusion` par
  laquelle on pourrait l'apprendre ;
- `resonance` et `ce_que_ca_engendre_chez_nous` accrochent le plan au nôtre — un
  plan d'en face sans résonance n'a rien à faire dans le fichier.

### 6. Les gardes — avant de passer à la suivante

```bash
python scripts/evaluer.py --murs --portees --sourds
python scripts/tick.py --verifier
```

Une maison n'est ouverte que quand les trois passent. `--murs` attrape le verrou
sans route de fuite, `--portees` la pièce qu'on ne peut pas apprendre, `--sourds`
l'acteur qu'aucune nouvelle n'atteint.

## Paliers B et C — la version courte

- **B** : étapes 1, 2 (le chef seul), 3, puis une tête `royaume` — une intention,
  une ou deux étapes, aucun déclencheur. Pas de plan, pas de mains, pas de dépêche.
- **C** : `maisons.json` et une fiche de chef dormant. Rien dans `intentions.json`.

## L'ordre de la série

1. **Rosby**, puis **Stokeworth** — faux neutres, un jour de route de Port-Réal,
   sur le chemin de l'ost, et sans port : ce qui marche sur Sombreval mange chez eux.
2. **Targaryen vert** — l'adversaire principal, et il n'a toujours aucun plan :
   Hightower est un pilier du camp, pas sa cour.
3. **Velaryon** — O13 en dépend et n'a pas répondu.
4. **Baratheon** — la seule vraie neutre du tableau, 8 000 levées.

**Rosby se fait en pilote complet**, les six étapes, pour mesurer ce qu'une maison
coûte avant d'en lancer trois autres. Si le pilote tient, Stokeworth suit dans le
même moule.

## Trois dettes, à solder avant la série

Elles coûtent moins cher maintenant qu'après quatre plans écrits :

- **La route de fuite doit devenir un champ obligatoire du verrou**, au même rang
  que `bloque`, réclamé par `tick.py --verifier`. Aujourd'hui elle est « planifiée
  à l'écriture » et rien ne la contrôle : un verrou sans route est un mur invisible,
  et l'on n'en verra les dégâts que dans trois lunes.
- **`equilibre` et `contredit` n'ont pas de domicile** : on ne peut pas encore
  demander « qu'est-ce qui contredit ceci ? » à travers les deux camps.
- **L'ouverture traverse plusieurs tables**, et c'est le goulot réel de cette
  chaîne : elle doit créer un personnage, écrire `relations.json` et
  `mains.json`, et muter le champ `declencheurs` d'une tête existante. Or ouvrir
  une maison fait exactement ces quatre choses. Les quatre premières ouvertures
  ont toutes fini par un bloc « à la main » — c'est-à-dire par la perte des gardes
  que le script existe pour donner.

## Le test d'arrêt

Une maison est ouverte quand on peut répondre à ces quatre questions sans rien
inventer :

1. Qui parle pour elle, et de quoi vit-il ?
2. Que veut-elle cette lune, et qu'est-ce qui l'en empêche ?
3. Par quelle nouvelle apprendra-t-elle ce que le joueur vient de faire, et en
   combien de jours ?
4. Par quelle bouche le joueur apprendra-t-il qu'elle a bougé ?

Si la quatrième n'a pas de réponse, la maison n'est pas de palier A — elle est de
palier B, et l'on vient d'écrire trop.
