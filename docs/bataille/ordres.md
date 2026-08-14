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
quand il traverse du monde. Tous les `EPREUVE_M` = 80 m, il perd une
subordonnée, et toujours dans le même ordre :

> `interdit` → `declencheur` → `marge` → `objet` → *(le verbe survit toujours)*

Une phrase perd ses subordonnées avant son verbe. Les nombres, eux, ne
disparaissent pas d'un coup : ils s'arrondissent d'abord, et de travers.

> Cole envoie : **suivre Vantre à 265 pas sans piller**.
> L'homme court 180 m dans la presse ; il arrive avec : **suivre Vantre**.
> L'aile pillera, parce que personne ne lui a dit de ne pas le faire.

**Le déclencheur ne se transmet pas — il attend.** `{declencheur: {porte}}` met
l'ordre en réserve dans la tête de l'escouade, qui se remet à regarder. Le jour
où la porte cède, elle part : sans coureur, sans bannière, sans que personne ait
eu à penser à elle. C'est le seul ordre de toute la nuit qui ne puisse pas se
perdre — **à condition qu'elle voie la chose arriver** (`VUE_DECLENCHEUR`,
160 m). Une escouade à qui l'on nomme une porte qu'elle ne peut pas voir
attendra la nuit entière, et elle aura raison.

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

| Humeur | Attend | Puis fait |
|---|---|---|
| — (ordinaire) | 25 s | il avance |
| `ferme` | 60 s | il tient, indéfiniment |
| `versatile` | 150 s | il décroche |
| `sourd` | jamais | il continue son premier ordre jusqu'au bout |

**Être sous sa bannière, c'est n'être pas seul** : le compteur du silence ne
monte que pour ceux qu'on a réellement perdus de vue. Ce test doit passer AVANT
toute sortie de la boucle de transmission — posé plus bas, il ne s'exécutait
jamais pour une escouade déjà servie, tout le corps de Cranche se mettait à
tenir au bout d'une minute, sa porte ne tombait plus, et rien ne disait pourquoi.

## 4. Ce que les annales en disent

Trois faits neufs, tous au niveau 3, aspect `commandement` :

- `ordre-deforme` — ce que le coureur vient de perdre, et ce qu'il portera
- `declencheur-tombe` — l'escouade qui n'attendait que ça
- `initiative` — le chef qui décide seul, **avec son motif** : sans lui on relit
  au matin une armée qui désobéit sans qu'on sache jamais pourquoi

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
