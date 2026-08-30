# Étalon

## 1. Ce que c'est

Une condition fixe, une graine tenue, un relevé d'issue conservé. Il ne dit pas
si la bataille est bonne : **il dit si elle est la même.**

## 2. Ce qu'il possède

- **La condition** : la scène exacte et close ; la **graine** ; le **critère de
  réussite** en vigueur.
- **Le relevé de référence** : l'issue, au dernier mort et au dernier fait.
- **L'empreinte de la chaîne** : les pièces qui participent au résultat.

## 3. Ce qu'il lit

Tout ce que la simulation produit à la fin d'une cuisson, et rien pendant. Le
manifeste, pour connaître les pièces de la chaîne et leur état.

## 4. Ce qu'il produit

- **Est-ce la même bataille ?** — l'écart au relevé, exhaustif, première
  divergence datée.
- **Cet étalon est-il encore valide ?** — l'empreinte de chaîne d'aujourd'hui
  contre celle de la pose. Une chaîne qui a bougé rend l'étalon périmé, et le dire
  est une sortie du module.

## 5. Invariants

- **L'attendu est zéro écart**, jamais « à peu près ».
- Aucune valeur du relevé n'est indéterminée : une clef sans valeur fixée fait
  diverger l'étalon d'avec lui-même.
- **Un relevé incomplet n'est jamais un relevé différent.** Une comparaison
  interrompue est rejetée avant lecture, sur le code de sortie.
- Deux cuissons dans la même session, plus une comparaison à un relevé posé une
  autre fois : sinon le déterminisme n'est pas prouvé.
- La condition doit faire se produire ce qu'elle prétend mesurer.

## 6. Ce qu'il ne fait pas

- **Il ne dit pas si la bataille est juste.** Une nuit absurde reproduite à
  l'identique passe l'étalon sans réserve. Le jugement est aux épreuves.
- **Il ne bouge jamais pour une extraction.** Un déplacement de code qui change
  le relevé est un changement de comportement, pas un étalon à repositionner.
- **Il ne mesure pas ce qui ne se produit pas dans sa condition.** Un étalon où
  personne ne meurt ne valide aucun changement sur la mort.
- **Il ne remplace pas les sondes** : zéro écart ne dit rien du nombre de
  téléports, il dit qu'il est le même qu'avant.

## Les cinq étapes avant d'avoir le droit de le reposer

Uniquement pour un changement de modèle **voulu**, et dans cet ordre :

1. **prédire** l'effet attendu, écrit avant de mesurer ;
2. **mesurer** ;
3. **expliquer l'écart**, divergence par divergence ;
4. **écrire un nouveau critère de réussite** ;
5. **seulement ensuite, reposer l'étalon.**

Un étalon reposé sans critère neuf n'est plus un étalon : c'est un enregistrement
de ce qui s'est passé.

## 7. Ce que l'ancien moteur faisait mal ici

**La condition ne faisait rien se produire.** Le fer ne s'y touchait jamais : la
porte finissait à son maximum de points de bois, jamais frappée, **zéro mort sur
220 secondes**. Trois grandeurs y étaient donc non mesurables — l'emprise du
corps, la létalité, la fermeture du contact — et aucun changement les concernant
n'était validable.

**L'étalon en place était périmé de trois jours et personne ne le savait** : sept
fichiers de la chaîne avaient changé depuis, et il rendait **29 relevés en
désaccord**. L'empreinte de chaîne n'était vérifiée nulle part.

**Une clef posée à « indéfini » faisait échouer toute comparaison** lancée sans
une certaine option : le banc se déclarait en désaccord avec lui-même.

**Deux comparaisons ont rendu des longueurs différentes** et fait croire à une
divergence ; c'étaient des délais dépassés. Il a fallu relancer sans limite, en
capturant le code de sortie, pour le savoir.
