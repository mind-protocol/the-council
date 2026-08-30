# L'allure du guide

## 1. Ce que c'est

À quelle vitesse l'homme de tête mène le groupe. Elle **s'adapte à ce que le
groupe suit réellement** : le guide ralentit pour être suivi, et réaccélère quand
il l'est.

## 2. Ce qu'elle possède

- l'**allure courante** du guide : une fraction de son allure libre ;
- la **règle d'adaptation** : de combien elle descend, de combien elle remonte, et
  à quelle vitesse dans chaque sens ;
- la **raison** de l'allure courante : ce qui l'a fait descendre, et quand.

## 3. Ce qu'elle lit

- `50-unite/cohesion` : la **distribution complète** des distances au guide,
  déciles compris ;
- `50-unite/identite` : qui suit, et combien ils sont ;
- `40-combattant/identite` : le métier des suivants, qui décide de leur allure
  libre — une monture ne se règle pas sur un piquier ;
- `20-monde/terrain` : ce que le sol permet.

## 4. Ce qu'elle produit

Une allure, remise au guide comme contrainte de son ordre — comme la forme remet
une région. Le guide reste un homme : il en fait ce que ses couches veulent.

## 5. Invariants

- **Elle se règle sur la queue, pas sur le ventre.** Ce qu'on veut savoir, c'est
  si les derniers suivent ; une statistique qui ne les voit pas ne peut pas
  gouverner l'allure.
- **Elle remonte.** Toute règle qui descend doit avoir un chemin de retour
  explicite, borné en temps, et une sonde qui vérifie qu'il est emprunté. Une
  allure qui n'a jamais remonté au cours d'une bataille est un défaut, même si
  chaque descente était justifiée.
- Elle est **continue** : pas de saut d'un extrême à l'autre entre deux
  battements.
- L'allure courante porte toujours sa raison, datée.
- Elle ne descend jamais à zéro : un groupe qui ne peut plus avancer relève de la
  rupture, pas d'un ralentissement infini.

## 6. Ce qu'elle ne fait pas

- Elle **ne déplace pas le guide** et n'écrit aucune vitesse dans le monde : elle
  contraint une intention, le monde décide du reste.
- Elle ne **rappelle pas les traînards** ni ne les fait accélérer : elle n'agit que
  sur un homme, le guide.
- Elle ne **choisit pas la route** ni ne décide d'un arrêt.
- Elle ne **détache personne** pour aller chercher les égarés : c'est le
  détachement, et c'est une décision, pas une adaptation.
- Elle ne juge pas si le groupe tient encore.

## 7. Ce que l'ancien moteur faisait mal ici

L'allure du guide était bridée d'après le **7e décile** des distances à lui — donc
en ignorant les 30 % les plus éloignés, c'est-à-dire exactement les hommes dont la
question se posait.

Les deux moitiés du défaut se répondent. **Une unité pouvait s'étirer sur
157 mètres sans que ce décile bouge de plus de 6** : les égarés étaient dans la
part aveugle, et le guide continuait à pleine allure une troupe déjà rompue en
deux. Puis, **quand ils refluaient**, ils rentraient d'un coup dans le décile, le
seuil était franchi net, et **le guide tombait à 15 % de son allure — de 0,84 à
0,16 m/s — sans jamais remonter**.

Trois leçons, et ce sont les invariants ci-dessus : mesurer la queue et non le
ventre ; ne pas gouverner sur un seuil franchi d'un coup ; et **toujours écrire le
chemin de retour**. Une règle qui n'a qu'un sens finit par tout arrêter.
