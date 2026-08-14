# Les trois chaînes — et la ville tombe dans l'écart

C'était la structure de l'ancien fichier et c'est la seule chose qu'on garde
intacte, parce qu'elle est juste. **Trois chaînes, trois défauts différents, et
aucun n'est une erreur : chacun est une conséquence de la façon dont on l'a
construite.**

← [le dossier](README.md) · [les arcs](arcs.md)

---

## 1. L'assaut est SOURD par construction

Criston a retiré les cors, les couleurs et la chaîne **pour que ce soit
réaliste**. Il a donc rendu son propre corps injoignable.

> **Mesuré, et ce n'était pas ça.** Un ordre ne met pas vingt secondes à
> traverser : un coureur va du chef d'une aile à une escouade de la même aile,
> **six mètres et quatre secondes en médiane**, et il n'est jamais déclaré mort
> de la nuit. La chaîne ne casse pas par le porteur — elle casse **par le
> destinataire** : sous cinq hommes une escouade cesse d'être un repère, le
> coureur n'a plus où aller, et l'ordre s'évapore sans une ligne. Sur
> `essai.reference`, les quatre seuls ordres perdus de la nuit sont les quatre
> exemplaires du **repli de Cole**, portés vers son aile en train de fondre.
> Le corps de Criston n'est pas sourd : il est joignable tant qu'il tient, et
> injoignable exactement au moment où il aurait fallu le rappeler.

## 2. La défense est LENTE par construction

Chaque renfort est une dépense, chaque dépense demande l'approbation d'Otto, et
Otto n'approuve rien sans le chiffre que l'exercice est censé produire. **La
boucle est fermée sur elle-même et personne dans la nuit ne la voit.**

## 3. L'ARBITRAGE est AVEUGLE par construction — et c'est le neuf

**Dix-neuf clercs à tablettes de cire, pour deux mille cinq cents hommes sur six
cent treize mètres.** Un homme est mort quand un clerc le dit. Donc :

- **la plupart des morts ne sont jamais prévenus** et continuent de se battre ;
- **certains vivants sont comptés morts** parce qu'un clerc a noté un rang ;
- **les dix-neuf tablettes ne s'accordent pas**, et une seule sera copiée au
  net ;
- et **le compte de la porte est le seul chiffre que quiconque lira jamais.**

C'est le défaut le plus grave des trois et c'est le seul qui survive à la nuit.
Les deux autres coûtent des hommes ; **celui-là coûte l'année suivante.**

---

# L'horloge de la nuit

Deux heures, et elles n'ont pas le même sujet. La porte n'occupe que la
première.

> ⚠⚠ **ET LES CUISSONS D'AVANT LE 14 AOÛT NE VALENT RIEN.** `PORTE_OUVERTE_ESSAI`
> était resté à `true` : la porte du four s'ouvrait à l'instant zéro. Ce n'était
> pas un raccourci de deux minutes, c'était la doctrine entière — la branche
> « verrou ouvert » est au deuxième rang de la cascade des têtes et avale la
> consigne, l'appui, le déclencheur et le `sans piller` de tous les corps de
> cette porte. Personne ne désignait de front à la Gadoue, la garnison ne se
> resserrait jamais sur la brèche, et les annales sortaient avec **zéro
> `ordre-deforme`, zéro `declencheur-tombe`, une seule `initiative` et sept
> coureurs**. Drapeau retiré, la même nuit rend 5, 5, 14 et 54.
>
> ⚠ **Cette table est la forme VOULUE, pas la cuisson.** `--duree 600` cuit
> **dix minutes** de bataille, pas deux heures : tout ce qui suit s'y produit
> comprimé d'un facteur douze. Pour obtenir la nuit telle qu'elle est écrite
> ici, il faut `--duree 7200`, et la cuisson coûte alors de l'ordre de
> **quatre-vingts minutes** au lieu de cinq. **Mesuré sur la cuisson à 600 s** :
> première porte à 86 s, quatrième à 416 s, `roi-averti` à 355 s — soit
> **4 min 28 s entre la première porte qui cède et le Donjon qui l'apprend**,
> et non le quart d'heure de la table.

| Heure | Ce qui se passe | Ce que le sac émet |
|---|---|---|
| **0h00** | cinq corps posés, le jour est tombé | *(rien — et ce silence est une donnée)* |
| **0h08** | le centre touche le premier | `contact` · `premier-sang` |
| **0h09** | Poix est déclaré mort au milieu de son rang | `chef-tombe` (nommé) |
| **0h08→0h30** | **l'heure creuse** — la porte ne bouge pas | `escouade-rompt` · `ralliement` |
| **0h30** | Vantre arrive par le flanc, avec les outils | `ordre` · `contact` |
| **0h38** | la porte cède | `porte-cede` |
| **0h44** | les faux gueux traversent tout le monde | `escouade-rompt` en série |
| **0h47** | la porte est enfoncée | `porte-enfoncee` |
| **0h47→1h05** | le quartier se vide — **et il se vide pour de bon** | `peur-gagne` · `rumeur-gagne` |
| **1h05→1h40** | six cents mètres de rue, en colonne | `assaut-au-donjon` |
| **1h40** | l'anneau | `contact` · `tete-tombe` |
| **2h00** | on sonne la fin, et le compte | `issue` |
| **2h20** | **la ville apprend que c'était un exercice** | `ville-avertie` *(à écrire)* |
