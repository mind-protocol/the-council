# Les ancrages — les noms posés, et ce que le four attend encore

← [le dossier](README.md) · [le narratif](narratif.md)

---

## Les ancrages réels — vérifiés le 14 août

> ⚠ **Les « douze noms » de la version précédente de ce dossier n'ont jamais
> existé sur disque.** `etat/corps.json` n'a jamais porté « le poste de la
> Gadoue 13382 », « la geôle du Crochet 20405 » ni « le hangar d'aval 39758 » —
> le tableau, et les « 855 pas · 8 minutes » qui en découlaient, étaient une
> passe annoncée comme réussie et jamais enregistrée. Ne pas les recopier.

Ce qui EST dans `etat/corps.json` est meilleur, parce que c'est le décor de la
partie en cours et pas un décor écrit pour la bataille :

| Clef | Bât. | Usage | Ce que ça sert |
|---|---|---|---|
| `salle:porte-de-la-gadoue` | 81 | corps-de-garde | **c'est le poste de Waltyr Poix** — les 200 bleus |
| `salle:arche-de-waltyr` | 81 | corps-de-garde | le même bâtiment, vu de dessous l'arche |
| `lieu:la-gaffe` | 9381 | taverne | **Mag la Gaffe**, visible de `marlo-vasse` |
| `salle:chantier-de-la-vase` | 97 | — | **Marlo Vasse**, ses barrières et sa facture |
| `lieu:porte-de-fer` | 3406 | — | la porte de Vantre |
| `salle:bureau-du-port` | 37952 | — | le bureau du maître de port |
| `salle:etal-de-sirel` | 9567 | — | Sirel Quintaine |
| `livre:le-peigne` · `salle:cabane-du-peigne` | 83 | — | le cahier de Marlo, et où il dort |

**La repose après régénération est FAITE.** `affecter.py --reancrer` existe
désormais — écrit pour cette régénération-là, il relit `xyz` (la vraie adresse)
et redonne le rang (le raccourci), en cherchant d'abord **le bon métier** dans
un rayon de 150 m. Il a été passé : *« rien à replacer : tout est déjà en
place »*. Les 5 à 136 m que `--verifier` signale encore sont le **résidu
irréductible** du semis qui a bougé, pas une faute à corriger.

## Ce que les mètres disent — mesuré, pas estimé

| De | À | |
|---|---|---|
| la porte de la Gadoue | **La Gaffe** | **47 m — 62 pas, 1 minute** |
| la porte de la Gadoue | **le chantier de la Vase** | **60 m — 80 pas, 1 minute** |
| La Gaffe | le chantier de la Vase | 64 m — 85 pas |
| la porte de la Gadoue | le bureau du port | 575 m — 767 pas, 7 minutes |
| la porte de la Gadoue | **la porte de Fer** | **1 724 m — 2 299 pas, 21 minutes** |

**Les deux premières lignes sont le cadeau de la géométrie, et elles valent le
dossier entier.** Mag la Gaffe est à **soixante-deux pas** de la porte qu'on
enfonce, Marlo Vasse à **quatre-vingts**. Ce ne sont pas des voisins de
quartier : ils sont **dans** le premier contact, et à quatre-vingt-cinq pas l'un
de l'autre. Aucun des deux ne peut ne pas voir, et aucun des deux n'a été
prévenu. Personne n'avait écrit ça — c'est la mesure qui l'a dit.

**La cinquième ligne casse un arc**, voir ci-dessous.

## Deux choses en suspens, et elles ne sont pas de la bataille

- **`lieu:le-grenier` a bougé.** Il pointait hors du monde engendré ; il résout
  sur un entrepôt de quinze mètres de façade dans « Le port et ses hangars »,
  juste hors les murs — alors que `docs/troupe.md` le veut rue des Sœurs, entre
  la colline de Visenya et la porte. La taille va, le quartier non. **Ce n'est
  pas à la bataille de trancher où habite la troupe.**
- **`personnage:ostor-bray` porte le monde `port-real`**, qui n'existe pas
  (c'est `portreal`). Un tiret de trop, et l'affectation est morte.

---

## Ce que ça demande au four

| | | |
|---|---|---|
| 1 | **Les corps existent** — cinq au lieu de six, avec leurs effectifs | ✅ posé dans `bataille2d.js` |
| 2 | **Trois comportements** : *ferme* (Cranche), *sourd* (les faux gueux), *versatile* (les bleusailles) | ✅ |
| 3 | **`chef-tombe` ne s'écrit que sur un nommé** | ✅ |
| 4a | **Le roi renversé par son propre reflux** | ✅ inchangé — c'est la charrette |
| 4b | **Gaunt qui ouvre** — une fin qui ne passe pas par le verrou | ⬜ |
| 5 | **Les huit habitants en positions fixes**, testées en premier par `peur-gagne` | ✅ ils sortent aux annales, nommés et situés |
| 6 | **`roi-averti`** — l'heure où le pouvoir apprend | ✅ il existe |
| 7 | **`ville-avertie`** — l'heure où la ville apprend que c'était faux | ⬜ **c'est le nœud n° 7, et le seul qui manque** |

## Ce que la cuisson a rendu — 14 août, `--hommes 1700 --duree 600`

```
2546 corps, 150464 images, cuit en 284 s
issue : 238 morts, 546 fuyards, verrou ouvert
402 faits — 119 blesse · 59 blesse-tient · 56 ralliement · 46 blesse-succombe
            24 escouade-rompt · 16 ordre · 14 prend-les-armes · 7 habitant
            7 guet-a-vu · 6 peur-gagne · 5 coureur-part · 5 coureur-arrive
            5 escouade-sourde · 4 porte-cede · 4 porte-enfoncee · 4 nouveau-chef
            4 maison-brulee · 3 rumeur-gagne · 3 chef-tombe · 3 banniere-tombe
            2 banniere-relevee · 1 corps-ferme · 1 corps-sourd
            1 corps-versatile · 1 contact · 1 premier-sang · 1 roi-averti
```

**Les 2 546 corps sont le compte juste** : 1 700 rouges + 800 bleus + les
quarante de la Garde Royale autour du roi, qui **ne comptent dans aucun des deux
camps** — personne ne leur a assigné un côté, donc aucun arbitre ne peut statuer
sur eux. C'est un détail vrai, et il est gratuit.

**Ce que les annales confirment :**

- **Les trois humeurs mordent**, une ligne chacune au premier battement, avec
  les bons effectifs : *« Ser Ormond Cranche et ses 250 hommes ne rompront pas »*,
  *« le sergent Rous Cantel mène 400 hommes qui n'entendront aucun ordre de la
  nuit »*, *« Petit Wend mène 200 hommes qui partiront vite et reviendront vite »*.
- **`escouade-sourde` ×5** — les faux gueux traversent les autres corps cinq
  fois. C'est [l'arc III](arcs.md) qui se produit tout seul.
- **`ralliement` ×56 contre 24 `escouade-rompt`** : plus du double de
  reformations que de ruptures. À 1 700 hommes les chefs sont plus près de leurs
  ailes qu'à 2 500 — l'effectif a changé le grain de la nuit, pas seulement son
  échelle.
- **`chef-tombe` ×3 seulement**, tous nommés. La règle des noms tient.
- **`prend-les-armes` ×14** : des habitants rejoignent les rangs. Personne ne
  l'avait écrit, et **ils s'arment contre un ennemi qui n'existe pas.**
- **Les huit habitants sortent nommés, situés et attribués à une source** — *« à
  170 pas de la porte de la Gadoue — mestre Ottyn, apothicaire — il ne ferme pas
  … vu par un portefaix, un saigneur »*.

> **Un piège de la cuisson, et il a mordu une fois** : le four écrit
> « *X mène N hommes* ». Le `nom` d'un corps doit donc être **une personne**, pas
> un collectif — « les faux gueux mène 588 hommes » ne s'accorde pas. Le corps
> `gueux` porte désormais **le sergent Rous Cantel**.

## L'ordre de bataille est à deux endroits

Il vit dans `ecrans/modules/bataille2d.js`, bloc `CORPS`, et il cite ce dossier
comme autorité. **Les deux doivent s'accorder** : un effectif changé ici et pas
là-bas est le genre de défaut qui ne se voit qu'à la cuisson — c'est-à-dire sept
minutes plus tard.

```bash
python scripts/bataille.py --cuire --hommes 1700 --duree 600
python scripts/bataille.py --recit
```
