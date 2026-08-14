# L'exercice de la porte de la Gadoue

**129 AC, 4e lune.** La Couronne répète la chute de sa propre ville : deux mille
cinq cents hommes, une nuit, la porte de la Gadoue contre le Donjon Rouge. Le
Guet se coupe en deux, des arbitres comptent les morts à la craie, et personne
ne doit mourir.

Ce dossier dit **qui est là, ce qu'il veut, et combien d'hommes il tient**. Ni
le format ni le four : ceux-là vivent dans `scripts/monde/sac.js` et
`ecrans/modules/bataille2d.js`, qui citent ce dossier comme autorité pour les
effectifs, les noms et les humeurs.

| | |
|---|---|
| [`autorite.md`](autorite.md) | **Les six qui ne se battent pas** — Aegon, Otto, Orwyle, Cole, Aemond, Larys |
| [`rouges.md`](rouges.md) | **L'assaut, 1 700 hommes** — ceux qui jouent l'ennemi |
| [`bleus.md`](bleus.md) | **La défense, 800 hommes** — ceux qui tiennent |
| [`chaines.md`](chaines.md) | **Les trois chaînes**, et l'horloge de la nuit |
| [`ordres.md`](ordres.md) | **Ce qu'on dit, ce qui arrive, ce qu'on s'invente** — la grammaire des ordres |
| [`arcs.md`](arcs.md) | **Les six arcs** et les huit nœuds de tension |
| [`perception.md`](perception.md) | **Ce qui parvient aux joueurs** — vu, entendu, trace |
| [`narratif.md`](narratif.md) | **Le narratif** — pourquoi, les trois jours d'avant, la nuit, le matin |
| [`ancrages.md`](ancrages.md) | **Les noms posés**, les affectations, ce que ça demande au four |

**Ce qu'une cuisson rend à lire.** `sac.js` écrit, à côté des octets,
`monde/<nom>.annales.json` — chaque fait à son heure, à son lieu en pas depuis
un repère, avec qui l'a vu. C'est la source, et elle est complète. Pour n'en
lire qu'une part :

```bash
node scripts/monde/annales.js monde/<nom>.annales.json --niveau 2 --aspect commandement
```

Le **niveau** coupe en profondeur (1 le tournant · 2 ce qu'un rapport retient ·
3 la nuit telle qu'elle s'est jouée · 4 tout), l'**aspect** coupe en travers
(`commandement`, `ville`, `fer`, `nouvelles`, `ouvrages`, `issue`). `--liste`
dit ce que chacun contient ; les vues tombent dans `exports/`.

---

## Le cadre

**Aegon II est couronné depuis une lune. Rhaenyra est à Peyredragon avec ses
dragons, et personne à Port-Réal ne sait ce qui se passera quand elle viendra.**
Le Guet n'a jamais eu à tenir une muraille contre quoi que ce soit. La ville n'a
pas été assaillie depuis la Conquête, et les hommes qui la gardent ont passé
leur vie à peser des tonneaux et à casser des têtes de fêtards.

**Pourquoi celui-là et pas un autre.** Trois raisons, et la dernière est la
vraie :

1. **La géométrie était déjà écrite.** L'assaut part de la porte de la Gadoue et
   vise le Donjon Rouge : l'axe du port vers la colline d'Aegon, six cent treize
   mètres de rue. C'est l'axe par lequel une ville se prend depuis dedans.
2. **La date tombe dans la partie.** Le monde est au **129 AC, 4e lune, jour 2**.
   La Lune des Trois Rois est à dix-neuf mois ; l'exercice est à sept jours. Ce
   qui se joue en 130 n'est traversable par personne — celui-ci l'est ce soir.
3. **Il y a un siège dedans.** Marlo Vasse tient le chantier de la Vase, à
   Port-Réal. Mag la Gaffe tient une taverne **sous l'arche de la porte de la
   Gadoue**. Hann Bourbe est du chantier depuis toujours. Waltyr Poix est
   sergent du Guet **à cette porte-là**. L'exercice se passe sur leur pas de
   porte, et aucun d'eux n'a été prévenu — parce que prévenir la ville aurait
   gâché la mesure.

**Ce qui est canon et ne doit pas bouger** : Aegon II, Otto Hightower, Criston
Cole, Aemond, Larys Strong, le Grand Mestre Orwyle, Ser Luthor Largent
(Commandant du Guet). Tout ce qui est nommé ailleurs dans ce dossier est de
l'invention posée dessous — c'est-à-dire de l'arrière-plan déjà vrai, comme le
reste du dépôt.

> *Note de conception :* la version précédente plaçait une émeute en 130, neuf
> mille cinq cents hommes sans chaîne de commandement, sur le thème **« personne
> ne commande »**. Elle est dans l'historique git (`docs/bataille.md`, avant le
> découpage). Ce qu'on perd : Marda et son cachot, les deux mille sourds de
> Vaugrain, et le matin plein de blessés. Ce qu'on gagne est le sujet ci-dessous.

---

## Le sujet — et ce n'est plus le même

**Ce n'est pas « personne ne commande ». C'est « tout est commandé, tout est
écrit, et le compte est faux. »**

Un exercice produit un chiffre. Le chiffre part dans un rapport, le rapport
décide de la défense de Port-Réal pour l'année qui vient, et **le chiffre est
faux** — pas parce qu'on triche, mais parce que dix-neuf clercs à tablettes de
cire ne peuvent pas voir deux mille cinq cents hommes sur six cents mètres. Un
homme est mort quand un clerc le dit. **La plupart des morts ne sont jamais
prévenus.**

C'est ça qu'on joue. Pas une bataille : **une mesure ratée dont tout le monde va
se servir.**

---

## Les trois gestes

Tout ce dossier se manipule par **une seule porte** : `scripts/bataille.py`.

```bash
python scripts/bataille.py
```

Dit où l'on en est : quel sac est cuit, ce qu'il contient, et s'il a lieu.

**1. Cuire.** Ça produit `monde/portreal.sac.*` — les itinéraires, les annales,
la nappe. C'est du monde engendré : régénérable, bête, et **ça ne concerne
encore personne**.

```bash
python scripts/bataille.py --cuire --hommes 1700 --duree 600
```

> ⚠ **`--hommes` ne compte QUE l'assaut.** Le four prend ce nombre et
> **rescale les cinq corps proportionnellement** à leur somme (1 700) ; la
> garnison, elle, est câblée à part dans `bataille2d.js` (200 à la Gadoue, 100
> aux trois autres portes, 300 à l'anneau = 800). Passer `--hommes 2500` ne
> donne donc pas 2 500 hommes en tout mais **2 500 rouges contre 800 bleus**,
> et Cranche sort à 368 au lieu de 250. Les deux mille cinq cents de ce dossier
> sont **1 700 + 800**, et la commande juste est celle du dessus.

**2. Dater.** C'est le geste qui le fait exister dans la partie. Il écrit
`etat/bataille.json`, et il est réversible.

```bash
python scripts/bataille.py --dater 9 1200
```

**3. Jouer.** Il n'y a rien à faire. Dès qu'un siège marche dans la ville, le
serveur demande à `croiser.js` ce que ce pas-là perçoit, et le dépose dans le
sac de balade — vu, entendu, ou trouvé par terre. Le MJ le lit avec le reste.

```bash
python scripts/bataille.py --recit        # ce qui s'y est passé, en clair
python scripts/bataille.py --eteindre     # il n'a plus lieu
```

**La séparation est le point.** Le sac est un fait du monde ; sa date est une
décision de jeu. On peut donc cuire pendant une séance sans rien changer à la
séance, en refaire dix, et décider après coup si — et quand — ça a eu lieu.
Tant que `etat/bataille.json` n'existe pas, tout ce mécanisme coûte un `if`.

---

## La règle qui commande tout le dossier

À deux mille cinq cents hommes en escouades de vingt, **il y a cent vingt-cinq
escouades**. Le module sait écrire `chef-tombe` par escouade — soit cent
vingt-cinq lignes d'annales que personne ne lira.

**Le nom est donc la seule unité de lisibilité du sac.** Quatre étages, et pas
un de plus :

| Étage | Combien | Ce que les annales en font |
|---|---|---|
| **L'autorité** | 6 nommés | ils ne se battent pas et ils décident de tout |
| **Les commandants** | 5 rouges + 4 bleus | tout : leur avance, leur arrêt, leur rupture, leur « mort » |
| **Les meneurs** | 24 nommés | leur chute est un fait ; leur escouade est une phrase |
| **Le reste** | ~2 400 | des chiffres, jamais des lignes |

Corollaire pour le four : `chef-tombe` ne se déclenche **que sur un chef
nommé**. *(Fait.)*
