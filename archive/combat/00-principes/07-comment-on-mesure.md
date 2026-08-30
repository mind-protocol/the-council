# Comment on mesure

**Ce qui n'est pas mesuré dérive.** Cette phrase gouverne le dossier entier, et
elle vaut d'abord pour l'architecture elle-même.

## Les trois instruments, et ce que chacun prouve

**L'étalon.** Une condition fixe, une graine tenue, un relevé d'issue. Il ne dit
pas si la bataille est *bonne* : il dit si elle est *la même*. C'est le filet des
déplacements de code, et l'attendu est zéro écart — jamais « à peu près ».

**Les sondes.** Des mesures de comportement prises **de l'extérieur**, en
regardant la troupe entre deux pas : téléports, corps dans le bâti, routes par
homme, densité, dispersion au chef, hommes arrêtés à portée d'un ennemi.

Une sonde qui vivrait *dans* le moteur devrait y être ajoutée — donc modifier ce
qu'on cherche justement à laisser intact pendant une extraction. **Une sonde
extérieure ne peut pas fausser l'étalon.**

**Les épreuves.** Des scènes complètes avec un verdict par critère. Elles disent
si le comportement est juste, pas s'il est identique.

## Quand l'étalon a le droit de bouger

Jamais pour une extraction. Uniquement pour un **changement de modèle voulu**, et
alors dans cet ordre :

1. prédire l'effet **avant** de mesurer ;
2. mesurer ;
3. expliquer l'écart ;
4. écrire un **nouveau critère de réussite** ;
5. seulement ensuite, reposer l'étalon.

Un étalon reposé sans critère neuf n'est plus un étalon : c'est un enregistrement
de ce qui s'est passé.

## Ce qu'un chiffre ne prouve pas

**Un relevé plus court n'est pas un relevé différent.** Deux comparaisons ont
rendu des longueurs différentes et laissé croire à une divergence ; c'étaient des
délais d'exécution dépassés. On ne conclut pas sur une mesure inachevée — il faut
capturer le code de sortie.

**Un zéro peut venir d'un effondrement** et non d'un accord.

**Une sonde peut comparer deux régimes différents.** L'une comparait la vitesse
de pointe de fantassins *en déroute* à celle de cavaliers *à la marche*, et
concluait que la cavalerie était trop lente. À état comparable, le rapport était
correct : **la sonde était fausse, pas le moteur.** Une sonde qui agrège sur tous
les états compare ce qui n'est pas comparable.

**Un onglet neuf ne prouve rien du cache.** Vérifier dans un navigateur sans
historique ne dit rien de ce que voit quelqu'un qui a déjà ouvert la page.

**Une condition où rien ne se passe ne mesure rien.** L'étalon du moteur
précédent portait une bataille où le fer ne se touchait jamais : la porte finissait
à son maximum de points, jamais frappée. Trois grandeurs — l'emprise du corps, la
létalité, la fermeture du contact — y étaient **non mesurables**, et aucun
changement les concernant n'était validable.

## Ce qu'il faut mesurer sur l'architecture elle-même

Pas seulement sur les batailles :

- aucune dépendance ne remonte une couche ;
- aucun module ne dépasse sa taille sans justification écrite ;
- aucune globale partagée ;
- un seul écrivain par donnée du tableau de propriété ;
- un seul manifeste, et tous les consommateurs le lisent.

Ces cinq-là sont des sondes comme les autres. Sans elles, les principes de ce
dossier auront la durée de vie de la table d'autorité qui les a précédés : elle
était juste, elle n'était vérifiée nulle part, et le code s'en est écarté sans
que personne le voie.
