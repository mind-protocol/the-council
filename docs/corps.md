# Les corps — habiter Port-Réal

Un `physicalactor` est **un emplacement occupé**, pas un personnage. Il a un
nom, un métier, un âge et une position en mètres dans la ville bâtie — l'étage
compris. Il ne pense rien, ne veut rien, n'a pas d'intentions, ne consomme
aucun budget d'échelle. C'est du mobilier vivant.

Ce que ça achète : la ville cesse d'être un décor. Quand une scène descend dans
le Culpucier, la taverne du coin a un tavernier qui a un nom, deux servantes,
une femme et trois gosses à l'étage — et c'était vrai avant qu'on y entre.

## Les fichiers, et pourquoi ils sont séparés

| | |
|---|---|
| `monde/gens/<i>-<j>.json` | **engendré**, 400 926 corps découpés en 151 cellules de 250 m. 45 Mo au total, ~300 ko la cellule. Se réécrit ENTIÈREMENT à chaque passage de `scripts/monde/peupler.py`. **N'y écris jamais rien.** |
| `monde/gens/<i>-<j>.bin` | le **double dense** des mêmes corps, 8 octets chacun. 3,2 Mo pour toute la ville. Pour le rendu seul. |
| `monde/portreal.gens.json` | le **manifeste** : colonnes, rôles, maille, compte de chaque cellule, et la clé `binaire`. 10 ko — le seul fichier qu'on lit en entier. |
| `etat/corps.json` | **décidé en jeu**, minuscule. `{"liens": {"<acteur_id>": "<personnage_id>"}}`. Survit à toutes les regénérations. |

## La maille — pourquoi 250 m

Quatre cent mille corps font quarante-cinq mégaoctets, et un navigateur n'avale
pas ça pour montrer une rue. La maille est la portée de vue à hauteur d'homme :
une caméra en tient neuf autour d'elle (750 m de côté), soit deux à six
mégaoctets selon le quartier, et le reste de la ville n'existe pas tant qu'on
n'y va pas. La cellule la plus dense (`11-3`, le cœur de la ville) porte 6 489
âmes pour 770 ko ; la médiane est à 3 091.

Le corollaire pour l'affichage : **les 400 000 ne sont pas des agents, ce sont
des adresses.** On n'instancie un corps que dans le rayon de la caméra, et l'on
recycle les emplacements en entrant et sortant du rayon. Wat le Boiteux ne
coûte rien tant qu'on n'est pas dans sa rue.

## Le double binaire — ce dont le rendu a besoin, et rien d'autre

Dessiner une foule ne demande ni nom, ni id, ni quartier : seulement où poser la
silhouette et laquelle poser. Transporter 130 octets pour en utiliser 8 était le
seul obstacle sérieux avant d'animer quoi que ce soit. D'où un second fichier
par cellule, **quarante fois plus léger** :

| | JSON | binaire |
|---|---|---|
| toute la ville | 45 Mo | **3,2 Mo** |
| cellule la plus dense (`11-3`) | 770 ko | **50,7 ko** |
| les 9 autour d'elle | 5,9 Mo | **367 ko** |

**Structure de tableaux** (SoA), little-endian, sans en-tête — le compte est déjà
au manifeste :

    uint16 x[n]        cm relatifs à x0 de la cellule
    uint16 y[n]        cm relatifs à y0
    uint16 z[n]        cm absolus
    uint8  role[n]     index dans `binaire.roles_index`
    uint8  age_sexe[n] âge en bits 0-6, femme au bit 7

Les trois colonnes de 16 bits viennent d'abord : ce n'est pas cosmétique, c'est
ce qui les garde alignées sur deux octets, sans quoi une vue typée refuse de se
poser sur le tampon.

**L'ordre est celui du tableau `gens` du JSON de la même cellule**, à l'index
près. C'est ce qui fait tenir les deux moitiés ensemble : la silhouette n° 412
qu'on vient de cliquer est le 412e corps du JSON, avec son nom et son métier —
aucun index supplémentaire à tenir.

Servis par `/monde/gens` (le manifeste) et `/monde/gens/<i>-<j>.bin` (brut, sans
gzip : c'est déjà dense). Le client est
[`ecrans/modules/monde/gens.js`](../ecrans/modules/monde/gens.js) : `manifeste()`,
`autour(x, y, rayon)` qui charge ce qui manque et oublie ce qui sort du rayon,
puis `position()`, `age()`, `femme()`. **Il ne dessine rien** — c'est un
chargeur, le rendu viendra par-dessus.

## Engendré d'un côté, décidé de l'autre

La séparation est la règle : ce qui se calcule d'un côté, ce qui se joue de
l'autre. Un lien écrit dans le fichier engendré serait perdu au prochain
`peupler.py`, silencieusement.

## Engendrer

```bash
python scripts/monde/peupler.py
```

Après `usages.py` (qui donne à chaque bâtiment son métier), avant ou après
`batir.py`. Rejouable et ensemencé : deux passages donnent le même monde.

Qui habite où ne sort pas du hasard mais du **métier du bâtiment et de sa
taille** : une taverne a un tavernier, une à trois servantes, zéro à deux
garçons de salle, et la maisonnée du maître au-dessus. Un entrepôt n'a pas de
maisonnée — on n'y dort pas. Un corps de garde a un sergent et quatre à dix
hommes. La table est dans `POSTES`, en tête de `scripts/monde/peupler.py`, une
ligne par métier ; c'est là qu'on l'amende.

Le hasard ne sert qu'aux noms, aux âges et au placement fin dans la parcelle.
Deux habitants d'une même maison ne sont jamais au même point : on peut donc
désigner « celui du fond ».

Colonnes : `id, nom, role, rang, sexe, age, usage, bat, quartier, x, y, z, etage,
travail`. `bat` est l'index dans `monde/portreal.bati.json` — le corps et son
bâtiment se retrouvent en O(1). `travail` est l'index du bâtiment où il
travaille : égal à `bat` pour l'écrasante majorité (on travaille chez soi en
ville), différent pour les métiers qui ne se dorment pas — le guet, le
portefaix, le gardien d'entrepôt, le saigneur, le fileur de chanvre. C'est là
qu'est la navette domicile-travail de Port-Réal, quatre mille hommes. Les rangs : `maitre` (celui à qui l'on parle),
`compagnon` (qui sait faire), `valet` (des bras), `famille` (qui vit là sans y
travailler).

L'`id` est dérivé du nom et du rôle — `wylla-tavernier`, `wat-le-boiteux-forgeron`
—, suffixé d'un compteur en cas de doublon. Lisible dans un log, stable d'un
passage à l'autre.

## S'en servir en jeu

```bash
python scripts/corps.py                                       l'état des liens
python scripts/corps.py --chercher --role tavernier --quartier "Le Crochet"
python scripts/corps.py --qui wylla-tavernier-3               la fiche d'un corps
python scripts/corps.py --ou mysaria                          où loge un personnage
python scripts/corps.py --lier <acteur_id> <personnage_id> --vraiment
python scripts/corps.py --delier <acteur_id> --vraiment
python scripts/corps.py --promouvoir <acteur_id> --vraiment
```

Filtres de `--chercher` : `--role`, `--usage`, `--quartier`, `--rang`, `--n`.

Deux gestes, dans les deux sens :

- **Lier** — un personnage qui existe déjà reçoit un corps. Le mestre, l'agent
  de la reine, la matrone dont une scène a parlé : ils gagnent d'un coup une
  maison, une rue, un étage, des voisins nommés et une distance en mètres
  jusqu'au Donjon Rouge. Rien à inventer.
- **Promouvoir** — un corps devient un personnage. Il avait déjà son nom, son
  métier et son adresse ; `--promouvoir` lui écrit une fiche `dormant` dans
  `personnages.json` et pose le lien. **Restent à écrire à la main : `traits`,
  `maniere`, `objectifs`** — c'est là qu'il devient quelqu'un, et le script ne
  fera jamais ce travail-là.

## Ce qu'un corps n'est pas

- **Ce n'est pas une tête.** Lier un corps ne crée aucune entrée dans
  `intentions.json` et n'en demande aucune. Un corps lié ne poursuit rien, ne
  réagit à rien, n'agit pas hors écran. Le budget d'échelle ne le voit pas.
- **Ce n'est pas une présence.** `etat/presence.json` et `scripts/presence.py`
  disent où quelqu'un se tient à la minute, dans le château. Le corps dit où il
  **habite**, ce qui ne bouge pas. Les deux ne se contredisent pas : on peut
  loger rue d'Acier et se tenir à la Table Peinte.
- **Ce n'est pas de la vérité connue du joueur.** Que Wylla tienne une taverne
  du Crochet est vrai dans le monde ; Rhaenyra ne le sait que si quelqu'un le
  lui a dit. Le brouillard s'applique comme partout ailleurs.

## Affecter — la même opération, pour tout le reste

Un corps est un cas particulier. La chose générale est : **affecter un objet
narratif à un objet physique**. Un personnage prend un corps ; une taverne
nommée en scène prend un bâtiment ; une salle du plan prend une adresse ; un
livre prend le toit sous lequel il dort.

```
python scripts/affecter.py                          l'état des affectations
python scripts/affecter.py --bati 1554              la fiche d'un bâtiment
python scripts/affecter.py --chercher --usage taverne --pres-de 1772,2789
python scripts/affecter.py --affecter lieu:la-gaffe 1554 --note "..." --vraiment
python scripts/affecter.py --ou lieu:la-gaffe
python scripts/affecter.py --entre lieu:la-gaffe salle:cabane-du-peigne
python scripts/affecter.py --defaire lieu:la-gaffe --vraiment
python scripts/affecter.py --verifier
```

La clef porte son **genre** — `lieu`, `salle`, `personnage`, `acteur`, `livre` —
parce qu'un même identifiant peut exister des deux côtés. La cible est un
**index de bâtiment** dans `monde/portreal.bati.json`, le même entier que la
colonne `bat` des corps : la seule prise stable d'une régénération à l'autre.
Les affectations vivent dans `etat/corps.json`, sous `affectations`, à côté des
`liens` — même fichier, même contrat, même raison de vivre hors du monde
engendré.

**`lieu` et `salle` nomment le bâtiment** et s'excluent l'un l'autre : un
bâtiment est un endroit, et un seul. `personnage`, `acteur` et `livre` sont
**dedans** et partagent sans conflit — c'est le cas normal, un livre est dans
une pièce.

### Ce que ça achète

Des **distances qui deviennent des faits**. `--entre` répond en mètres, en pas
et en minutes de marche ; un `cout` d'étape, un délai de course, un « il y sera
avant la marée » cessent de s'estimer au doigt mouillé. La première fois qu'on
l'a fait pour de vrai, la géométrie a dit ce que personne n'avait écrit : le
corps de garde de la Gadoue est à **douze mètres** du coffre de Marlo, et son
chantier du bout à **793 m** — mille cinquante pas, quand il en avait compté
douze cents dans le noir.

### Ce que ça n'achète pas

Rien à l'écran par soi-même : affecter ne dessine aucune étiquette sur la carte
et n'ouvre aucune échelle. Et rien du brouillard : une affectation dit où la
chose EST, jamais que le joueur le sache.

**Quand écrire une affectation** : quand un endroit revient et qu'une distance
le concernant pourrait trancher quelque chose. Un lieu de passage n'en a pas
besoin — même règle que les salles de `ecrans/modules/plans.js`.

`python scripts/tick.py --verifier` relit les affectations à chaque passage et
signale celles dont le bâtiment a disparu : le monde se régénère, l'affectation
non, et une cible morte ne casse rien — elle ment en silence.

### Montrer, et se déplacer

**Affecter ne montre rien.** Un endroit affecté a des mètres ; il n'apparaît sur
la ville que si on le demande, et pour qui de droit :

```
python scripts/affecter.py --affecter lieu:la-gaffe 1554 --visible-pour marlo-vasse --vraiment
python scripts/affecter.py --montrer lieu:chantier-du-bout --pour marlo-vasse --vraiment
python scripts/affecter.py --cacher lieu:chantier-du-bout --vraiment
```

`--visible` = tout le monde ; `--visible-pour a,b` = ces sièges-là. C'est du
BROUILLARD, pas de l'affichage : ce que Marlo a reconnu de ses yeux, la reine ne
l'a pas vu, et `/reperes` filtre selon le jeton du demandeur. Les deux gestes
sont séparés parce que les deux dates le sont — on affecte le jour où l'on veut
mesurer, on montre le jour où le joueur y va.

**Le joueur se déplace comme les PNJ.** `scripts/append_flux.py` dérive la
présence des items poussés : qui parle ou agit se trouve dans la pièce que le
dernier en-tête `lieu`/`salle` a nommée. Le personnage du joueur y est inclus —
il n'a ni `locuteur_id` ni `acteur_id`, et sans cette règle il restait seul
immobile pendant que la pièce changeait autour de lui. Hors fiction excepté
(`question`, `reponse`, `pensee`, `meta`, `coulisses`) et `run` aussi : le pas de
côté du joueur n'est pas un geste du personnage.

Conséquence pratique pour le MJ : **poser `salle` sur l'item qui change de
lieu**. Sans elle, la présence garde la salle d'avant et la balise du décor avec.

**Le voyage se voit.** Au-delà de 120 mètres, la balise « vous êtes ici » ne
saute pas : elle glisse en deux secondes et la caméra suit. C'est la seule chose
qui dise que Port-Réal est grand — et qu'aller au chantier du bout coûte huit
cents mètres. En deçà, on se pose : traverser une cour n'est pas un voyage.

### Le brouillard se lève en marchant

Le drapeau `--montrer` reste utile pour ce qu'on APPREND sans y aller — un
endroit qu'on vous a décrit, une adresse qu'on vous a donnée. Mais l'essentiel
n'a pas à se déclarer : **`append_flux.py` révèle tout endroit où le joueur
vient de se tenir**, pour son siège seul, au moment où il y est. Y avoir été,
c'est le connaître.

La règle cherche `salle:<id>` puis `lieu:<id>` : un endroit que le plan ne
connaît pas — une taverne, un chantier — est affecté en `lieu`, et il serait
absurde d'y passer la nuit sans que son nom paraisse.

Ce qui ne se lève donc jamais tout seul : un endroit **affecté mais jamais
visité**, qui garde ses mètres pour les calculs et reste anonyme sur la carte
tant que le joueur n'y va pas ou qu'on ne le lui montre pas. C'est voulu — le
chantier du bout avait ses huit cents mètres bien avant qu'on y mette les pieds.
