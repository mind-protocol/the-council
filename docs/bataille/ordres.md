# Les ordres — ce qu'on dit, ce qui arrive, ce qu'on s'invente

Le vocabulaire tenait en trois mots — `avancer`, `tenir`, `repli` — et c'était
un choix, écrit dans le module : *« un vocabulaire d'ordres qui enfle est un
vocabulaire dont chaque mot cesse d'avoir des conséquences visibles »*.

L'objection est juste, et elle ne condamne pas la précision : **elle condamne la
liste de verbes.** On ne peut pas dire « gardez cette unité à deux cents pas »
avec un mot de plus dans une énumération. On le dit avec une PHRASE — et ce qui
la rend précise est exactement ce que la transmission lui arrache en premier.

---

## 1. Un ordre est une phrase

```js
{ verbe: "suivre",           // ce qu'on fait — cinq mots, fermés
  objet: {corps: "cole"},    // sur qui
  marge: 200,                // « à deux cents pas »
  declencheur: {porte: "…"}, // « quand elle cède » — l'ordre attend tout seul
  interdit: ["piller"],      // « sans »
  intention: "couvrir" }     // POURQUOI — la seule clef qui serve quand tout tombe
```

| Verbe | Ce que l'aile fait |
|---|---|
| `avancer` | marche sur la porte, puis sur le Donjon. **Seul verbe qui cogne**, avec `appuyer` |
| `tenir` | reste où elle est, se bat si on la joint |
| `repli` | décroche en ordre — ce n'est pas une déroute |
| `suivre` | se tient à `marge` d'un autre corps, **entre lui et le dehors** |
| `appuyer` | même chose à courte distance, et **relève les haches** quand elles tombent |

`suivre` est le seul comportement du module dont le but bouge : une aile qui
suit recule quand l'autre avance. C'est ce qui sépare une réserve d'un piquet.

`appuyer` existe pour une raison arithmétique, et elle est neuve : depuis que le
poste mord (`RIPOSTE`), les sept haches du seuil tombent une par une. Sans
personne pour prendre leur place, **une porte ne s'ouvre plus jamais.**

## 2. Ce qui porte la phrase, et ce qui la perd

**La bannière ne dit pas une phrase : elle lève un signal convenu d'avance.**
Trois codes — marcher, tenir, décrocher — et rien qui ait un objet, une
distance ou une réserve. Conséquence, et c'est le cœur du chantier : *dès que la
tête veut quelque chose de précis, la bannière ne lui sert plus à rien et il
faut un homme.* La précision se paie en portage, et le portage peut tomber.

**Le coureur porte une COPIE, et il l'abîme.** On compte ses mètres — doublés
quand il traverse du monde. Tous les `EPREUVE_M` = **35 m**, il perd une
subordonnée, et toujours dans le même ordre :

> `interdit` → `declencheur` → `marge` → `objet` → *(le verbe survit toujours)*

Une phrase perd ses subordonnées avant son verbe. Les nombres, eux, ne
disparaissent pas d'un coup : ils s'arrondissent d'abord, et de travers.

> Vantre envoie à sa deuxième aile : **appuyer la 1re aile à 80 pas**.
> L'homme part au déploiement, les ailes sont encore étalées ; il arrive
> avec : **appuyer la 1re aile**. Elle se collera ou elle traînera, au
> jugé, parce que personne ne lui a dit à combien.

⚠ **C'EST UN PHÉNOMÈNE DE DÉPLOIEMENT, ET RIEN D'AUTRE.** Mesuré sur
`essai.reference` (1 700 hommes, 600 s) : cinquante trajets appariés, **distance
médiane 6,4 m**, cinq seulement au-dessus des 35 m, et **quarante-sept des
cinquante départs ont lieu avant la trentième seconde**. La raison est
structurelle : un coureur ne traverse pas la ville, il va du chef d'une aile à
une escouade de CETTE aile. Tant que le corps est étalé sur sa position de
départ, ça fait de vrais mètres ; dès qu'il s'est resserré sur sa porte, le chef
et ses escouades sont à six mètres l'un de l'autre et plus rien ne s'abîme de la
nuit. Un trajet de 627 m existe pourtant dans le lot — le cas long EXISTE, il
n'a simplement jamais été cherché.

**Le déclencheur ne se transmet pas — il attend.** `{declencheur: {porte}}` met
l'ordre en réserve dans la tête de l'escouade, qui se remet à regarder. Le jour
où la porte cède, elle part : sans coureur, sans bannière, sans que personne ait
eu à penser à elle. C'est le seul ordre de toute la nuit qui ne puisse pas se
perdre — **à condition qu'elle voie la chose arriver** (`VUE_DECLENCHEUR`,
160 m). Une escouade à qui l'on nomme une porte qu'elle ne peut pas voir
attendra la nuit entière, et elle aura raison.

> **Mesuré, et ça a demandé deux corrections.** La Gadoue cède à 154,25 s et
> cinq escouades partent à **154,30 s** — cinq centièmes de seconde, sans un
> homme sur les routes. Mais c'étaient les cinq de Cole, seul corps déployé à
> 109 m de sa porte : Cranche est à 214 m de la sienne, Vantre et les gueux
> plus loin encore, et **pas un de leurs déclencheurs ne tombait de la nuit**.
> L'ordre partait en réserve, l'aile gardait le `tenir` de son déploiement, et
> elle n'avait aucun moyen d'approcher ce qu'on lui avait nommé.
>
> La réserve reçoit donc maintenant **son objet et sa marge en même temps que
> son déclencheur**, et elle prend la posture d'attente qui va avec : elle SUIT
> la première aile à quatre-vingt-dix pas, ce qui la porte à portée de vue du
> seuil sans la mettre dans la presse. Le mécanisme n'a pas changé — il avait
> un défaut de géométrie, pas de principe.

**On n'envoie un ordre qu'une fois.** C'est la règle « rien ne remonte » lue à
l'envers : la tête ne sait pas que son aile a dérivé, donc elle ne la rappelle
pas à l'ordre. Sans ce compteur (`e.vu`), un chef qui s'invente quelque chose
divergeait de son aile, la divergence relançait un coureur, le coureur le
remettait en ligne — et l'on obtenait un télégraphe : **soixante-dix hommes sur
les routes pour quinze escouades, et pas une décision qui tienne trente
secondes.** Mesuré, puis corrigé.

## 3. Ce qu'un chef s'invente quand rien n'arrive

Il descend un escalier de trois marches et s'arrête à la première qui le porte.

1. **La consigne** — ce qu'on lui a dit AVANT la nuit. Elle ne se transmet
   jamais, elle est déjà dans sa tête au premier pas, et c'est le seul ordre qui
   arrive toujours à destination. Petit Wend en a une, et elle dit littéralement
   *gardez-vous à deux cents pas de Cole*.
2. **L'intention** — le POURQUOI du dernier ordre reçu. Quand cet ordre devient
   **impossible** — l'aile qu'il devait suivre est tombée sous cinq hommes, donc
   elle n'est plus un repère —, il ne reste pas planté devant un mort : il refait
   un verbe depuis le motif. `entrer` → avancer, `couvrir` → tenir, `durer` → repli.
3. **Son tempérament** — l'humeur de son corps, lue pour ce qu'elle dit du
   silence. C'est la définition même d'un homme qu'on a cessé de commander.

| Corps | Attend (médiane) | Puis fait |
|---|---|---|
| Cole, Vantre (ordinaires) | 25 s | il avance |
| Cranche, l'aile ferme | 56 s | il tient, indéfiniment |
| Petit Wend, le versatile | 129 s | il décroche |
| les faux gueux, le sourd | jamais | il continue son premier ordre jusqu'au bout |

⚠ **CE N'EST PLUS UN TABLEAU, ET LA MÉDIANE N'EST PLUS LA VALEUR.** `SILENCE`
est déposé : ce qu'un chef supporte de silence se demande à
[`survival-stack/4-envie.js`](../../ecrans/modules/survival-stack/4-envie.js),
**homme par homme**, avec son tempérament et ce qu'il a autour de lui. Les
chiffres ci-dessus sont les médianes de chaque corps, calibrées sur l'ancien
tableau ; l'écart interdécile va du simple au sextuple, et surtout **les signaux
du moment déplacent le centre** : un chef dont la bannière est à terre et dont
l'aile a fondu ne tient plus que quatre secondes là où il en tenait vingt-cinq.
Un homme abandonné décide vite, ce qu'un seuil en secondes ne pouvait pas dire.

Même histoire pour `APPETIT`, le tableau du pillage, parti au même endroit — et
il était **cassé en silence** depuis que `humeur` a été dissoute dans la couche
du corps : indexé sur un champ qui n'existait plus, il rendait la valeur
« ordinaire » pour tout le monde. Cranche pillait comme les autres, et le corps
de Petit Wend ne se dissolvait plus. `BRULE` avait la même fêlure.

**Être sous sa bannière, c'est n'être pas seul** : le compteur du silence ne
monte que pour ceux qu'on a réellement perdus de vue. Ce test doit passer AVANT
toute sortie de la boucle de transmission — posé plus bas, il ne s'exécutait
jamais pour une escouade déjà servie, tout le corps de Cranche se mettait à
tenir au bout d'une minute, sa porte ne tombait plus, et rien ne disait pourquoi.

## 4. Ce que les annales en disent

Quatre faits, tous au niveau 3, aspect `commandement` :

- `ordre-deforme` — ce que le coureur vient de perdre, et ce qu'il portera
- `declencheur-tombe` — l'escouade qui n'attendait que ça
- `initiative` — le chef qui décide seul, **avec son motif** : sans lui on relit
  au matin une armée qui désobéit sans qu'on sache jamais pourquoi
- `ordre-sans-personne` — **le coureur arrive et ne trouve plus personne.** Sous
  cinq hommes, une escouade cesse d'être un repère : le porteur n'a plus de
  destination, il rentre dans la colonne, et l'ordre s'évapore. C'était un
  `return` muet — 54 coureurs partis, 50 arrivés, zéro fait pour expliquer les
  quatre. Les quatre portaient **le repli de Criston Cole**, à 403,3 s, vers les
  escouades de son aile en train de fondre. *L'ordre de retraite d'un corps qui
  s'effondre se perd parce que le corps s'effondre* — c'est le meilleur fait de
  la nuit, et il n'était écrit nulle part.

Et le fait `ordre` porte désormais **`sourd`** quand aucune escouade de l'aile
ne peut l'entendre : la tête des faux gueux ordonne comme les autres, et sa
parole meurt dans sa bouche. Trois lignes sur quinze, dans la première cuisson.
La tête, elle, n'en saura jamais rien — c'est « rien ne remonte ».

Et `ordre`, `coureur-part`, `coureur-arrive`, `coureur-tombe` portent désormais
la phrase entière au lieu du verbe nu.

## 5. Ce qui n'est pas fait

- **Rien ne remonte, toujours.** Pas d'accusé de réception, pas de compte rendu,
  et la tête ne voit pas plus loin que son propre rang. « Gardez cette unité à
  deux cents pas » se donne, mais personne ne saura jamais si c'est tenu.
- **Pas de bouche-à-oreille latéral** : deux ailes qui se touchent ne se
  repassent pas un ordre.
- `relever` n'existe pas — `appuyer` en fait office.
- L'`interdit` ne connaît qu'un mot, `piller`. C'est le seul qui morde, parce
  que c'est la seule chose qu'un homme fasse sans qu'on la lui dise.
