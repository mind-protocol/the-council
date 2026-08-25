# Les gardes et patrouilles de ville — le poste, la tournée, le couvre-feu, et ce qu'un guet ne peut pas faire

> Quatrième dossier, après [`dynamiques-du-combat-medieval.md`](dynamiques-du-combat-medieval.md),
> [`le-tir.md`](le-tir.md) et [`le-repli-la-fuite-et-la-couardise.md`](le-repli-la-fuite-et-la-couardise.md).
> **Son envers est le cinquième** : [`le-vol-les-bandes-et-le-recel.md`](le-vol-les-bandes-et-le-recel.md),
> qui décrit ce qui passe entre les mailles du dispositif décrit ici — et pourquoi ce n'est presque
> jamais le guet qui l'arrête.
>
> **Qualité de preuve : meilleure que celle du tir, moindre que celle de la mêlée.** On dispose ici
> de quelque chose que les trois autres n'avaient pas — **des textes normatifs conservés** : le
> Statut de Winchester (1285), les ordonnances du guet parisien depuis 1254, les registres de
> métiers. Ce sont des sources de premier ordre, mais elles disent **ce qui était prescrit**, jamais
> ce qui se faisait. Le contrepoids vient des archives judiciaires (Gauvard) et des plaintes des
> autorités contre leur propre guet, qui sont, elles, le meilleur témoignage sur la pratique.
>
> Règle du dossier voisin, maintenue : **quand deux chiffres se contredisent, les deux sont ici,
> avec l'écart** — et il y a ici un écart de 1 à 17 qui décide de tout (§ 2).
>
> Ce dossier sert deux choses à la fois : la vie ordinaire de la ville (`monde/journee.js`,
> `monde/besoins.py`) et **l'exercice de la porte de la Gadoue** (`docs/bataille/`), dont le sujet
> est précisément un Guet qui n'a jamais tenu une muraille.
>
> **Le § 2 bis a été ajouté après coup, et il corrige le reste.** Le dossier a d'abord été
> écrit sur le modèle de la ville COMMUNALE — le guet bourgeois de corvée —, et Port-Réal y
> paraissait aberrant. Il ne l'est pas : c'est une ville ROMAINE, et c'était l'étalon qui était
> faux. Lire le § 2 bis avant d'utiliser un chiffre du § 2 pour juger notre modèle.

---

## 0. Le raisonnement central, en une page

Trois faits, et le troisième explique les deux premiers :

| Fait | Ce qui le porte |
|---|---|
| Le guet d'une grande ville est **minuscule** | Paris, ~200 000 âmes : **40 sergents à pied et 20 à cheval**. Un homme pour 3 300 habitants. |
| Il est **notoirement inefficace** | Gauvard : les sergents « s'endorment, jouent aux cartes, se laissent corrompre ». Cologne, 1452 : il faut instituer des sergents *pour faire respecter le service de guet*. |
| Et pourtant les villes tiennent la nuit | — |

**La résolution est le couvre-feu, et c'est le fait le plus important du dossier.** On ne garde pas
une ville en la surveillant : **on la vide, et l'on garde ce qui reste.** Formulé net par Exbalin :

> Le couvre-feu était une manière de compenser la faiblesse numérique des forces de l'ordre. En
> vidant la ville de sa circulation, il facilitait les rondes des quelques gardes.

C'est-à-dire que la chaîne va dans l'autre sens que celui qu'on croit : ce n'est pas le guet qui
produit l'ordre nocturne, **c'est l'ordre nocturne qui rend le guet possible**. La cloche, les
portes fermées, les chaînes tendues en travers des rues, les tavernes closes — voilà l'appareil.
Les soixante hommes ne sont que ce qui circule dedans.

**Deuxième conséquence, et elle est du même ordre : le guet ne trouve pas le crime, on le lui
crie.** Le mécanisme légal anglais s'appelle la *hue and cry* — quiconque voit un forfait doit
crier, et **tout homme valide qui entend est tenu de se joindre à la poursuite**, de ville en ville
et de comté en comté, jusqu'à ce que le coupable soit livré au shérif. Le corps qui poursuit n'est
donc pas le guet : c'est la rue entière, réquisitionnée par un cri.

**Et le troisième fait est le prix des deux premiers : dehors la nuit, c'est le délit.** La
personne trouvée dans la rue après la cloche est en droit un *communis noctivagus* — un vagabond
nocturne, « moralement désordonné, légalement suspect, et passible d'arrestation immédiate ».
Depuis 1285 en Angleterre, **l'acte de marcher la nuit est criminalisé indépendamment de toute
activité illicite**. Un guet n'a donc pas à établir un fait : il a à établir une *heure* et une
*absence de raison*. C'est une police de la présence, pas de l'acte.

> **Ce que ça change pour nous, en une phrase.** Notre modèle a des hommes qui patrouillent une
> ville qui ne dort jamais. L'histoire décrit l'inverse : une ville qu'on éteint, et des hommes qui
> vérifient qu'elle est éteinte.
>
> ⚠ Ceci décrit la ville **communale**. Pour l'effectif et le statut des hommes, Port-Réal
> relève d'un autre modèle — voir le **§ 2 bis**. Le couvre-feu, lui, vaut pour les deux :
> Rome fermait ses portes comme les autres.

---

## 1. Deux corps, jamais un — le poste et la tournée

Toutes les villes documentées séparent la même paire, sous des noms différents. C'est la structure
la plus stable du dossier.

| | Paris | Angleterre | Ce que c'est |
|---|---|---|---|
| **Le fixe** | *guet assis* | *ward* | Des postes tenus. Fourni par **les bourgeois et les maîtres de métier**, en corvée, à tour de rôle. |
| **Le mobile** | *guet royal* | *watch* | Une petite troupe soldée qui **fait la ronde** — et dont une part de la mission est de **vérifier que les bourgeois sont à leur poste**. |

Deux choses à ne pas manquer là-dedans.

**Le gros de l'effectif est le fixe, et il n'est pas professionnel.** À Paris, le guet assis est
fourni chaque soir par les métiers : une soixantaine d'hommes convoqués au Grand Châtelet à la
tombée du jour, répartis en postes. Ce ne sont pas des gardes : c'est un boulanger, un tonnelier,
un mercier, qui ont leur tour ce soir-là.

**Le mobile sert d'abord à surveiller le fixe.** Les sergents à cheval « font les rondes de poste
en poste, vérifiant que les bourgeois y sont ». La patrouille n'est donc pas d'abord une recherche
de malfaiteurs — c'est une **inspection de son propre dispositif**, ce qui en dit long sur la
confiance qu'on lui portait.

### 1.1 Les nombres du fixe, et leur forme

Le quota anglais du Statut de Winchester (1285) est explicite et c'est le texte le plus cité :

> Que des guets soient tenus **du jour de l'Ascension au jour de la Saint-Michel** ; **six hommes à
> chaque porte** dans chaque cité, **douze hommes** dans chaque bourg, **six ou quatre** dans chaque
> ville selon le nombre d'habitants, veillant continuellement toute la nuit **du coucher au lever du
> soleil**.

Trois choses en une phrase :

1. **Le quota est par PORTE, pas par ville** — l'unité de garde est le point d'entrée, pas la
   surface.
2. **C'est saisonnier.** De l'Ascension à la Saint-Michel : en gros de mai à fin septembre. ⚠ Ce
   point est attesté dans le texte et rarement commenté ; on ne sait pas d'après nos sources si les
   villes gardaient malgré tout l'hiver par coutume propre. **On le note comme une singularité, pas
   comme une règle générale.**
3. **La borne horaire est astronomique**, pas horlogère : du coucher au lever. Elle bouge donc de
   plusieurs heures dans l'année, ce qui est cohérent avec le § 3.

Paris, mêmes formes, chiffres différents : **huit postes de six hommes** en 1364 (ordonnance de
Jean II le Bon), aux points qui commandent — le Châtelet, la cour du Palais, des carrefours choisis.

---

## 2. L'écart de 1 à 17, et comment il se résout

Voici tout ce qu'on a trouvé de chiffré, ramené au même dénominateur. **C'est le tableau le plus
utile du dossier, et le plus piégeux.**

| Ville, date | Effectif | Population | Un homme pour |
|---|---|---|---|
| **Paris, guet royal** (depuis 1254) | 40 à pied + 20 à cheval = **60** | ~200 000 | **~3 300** |
| **Paris, guet assis** (ordre de grandeur) | ~60 convoqués chaque soir | ~200 000 | ~3 300 |
| **Paris, les deux ensemble** | ~120 | ~200 000 | **~1 700** |
| Paris, 1364 | 8 postes × 6 = 48 fixes | | |
| Paris, 1750 (pour mémoire) | 4 lieutenants, 8 exempts, 139 archers dont 39 montés, + 149 cavaliers | | |
| **Angleterre, Winchester 1285** | 6 par porte / 12 par bourg | — | *quota, pas un ratio* |
| Londres, Aldgate 1377 | 8 hommes / 1 500 âmes | | **188** — ⚠ voir § 10 |
| **Port-Réal, notre modèle** | ~2 000 manteaux d'or | 400 000 | **200** |

**L'écart entre 3 300 et 188 est d'un facteur 17, et il ne se résout pas en choisissant un camp.**
Il se résout en constatant que **les deux chiffres ne comptent pas la même chose** :

- **60, à Paris, c'est le noyau soldé et permanent.** Il tourne toutes les nuits de l'année.
- **6 par porte, à Winchester, c'est un quota de corvée saisonnier.** Multiplié par les portes d'une
  cité, il donne un effectif d'une nuit — pas une force debout. Et les hommes qui le remplissent
  sont derrière un étal le lendemain matin.

**Ce qui est robuste malgré l'écart** : dans toutes les configurations, l'effectif tenant la ville à
une minute donnée se compte en **dizaines**, pas en milliers, pour des villes de dizaines à des
centaines de milliers d'âmes. C'est le seul ordre de grandeur qu'on puisse utiliser sans se tromper.

---

## 2 bis. L'AUTRE MODÈLE — Rome, et c'est celui de Port-Réal

> **Section ajoutée après coup, et elle corrige le dossier.** Tout ce qui précède décrit la ville
> **communale** : une bourgeoisie qui se garde elle-même par corvée, avec un mince noyau soldé
> par-dessus. Sur cet étalon, notre Guet paraissait aberrant — seize fois trop dense (§ 9.2c, dans
> sa première version). **L'aberration était dans l'étalon.** Il existe un autre modèle de police
> urbaine, plus ancien, mieux documenté, et c'est celui auquel Port-Réal ressemble trait pour trait.

### 2bis.1 Ce qu'Auguste a fait, et pourquoi ça nous concerne

Rome n'a jamais eu de guet bourgeois. Après les incendies qui ravagent la ville, **Auguste crée les
*vigiles* en 6 de notre ère** : un corps **payé, permanent, casernné, à plein temps**. Rien de la
corvée, rien du tour de rôle, rien des exemptions qu'on plaide — l'État paie, donc l'habitant ne
veille pas.

| | Effectif | Ce qu'on en sait |
|---|---|---|
| Les vigiles, mise en place | **7 cohortes**, une pour **deux des quatorze régions** de Rome | l'unité de garde est le QUARTIER, pas la porte |
| Cohorte, chiffre bas (Ostia Antica) | 560 hommes — 7 centuries de 80 | **3 920 en tout** |
| Cohorte, chiffre haut | 1 000 hommes | **7 000 en tout** |
| Doublement, vers 205 apr. J.-C. (Rainbird) | 1 120 par cohorte | **7 840** |
| Le tout premier corps (av. la réforme) | **600 esclaves** | on a commencé par des hommes qu'on possédait |

⚠ **L'écart entre 3 920 et 7 000 n'est pas tranché**, et les deux chiffres circulent. Il ne change
pas l'ordre de grandeur, qui est le seul point : **des milliers d'hommes payés pour une ville d'un
million**, là où Paris en payait soixante pour deux cent mille.

### 2bis.2 Les trois étages, et c'est la vraie leçon

Rome ne tient pas sa capitale avec un corps mais avec **trois, empilés, de nature différente** :

| Corps | Combien | Qui | Pour quoi |
|---|---|---|---|
| **Les vigiles** | 3 920 à 7 840 | des **affranchis**, puis des hommes libres et des pérégrins | la nuit, le feu, la rue |
| **Les cohortes urbaines** | 3 puis 4 cohortes de **500**, portées à 1 000 puis **1 500** | des soldats, payés **moitié moins que les prétoriens et moitié plus qu'un légionnaire** | l'ordre lourd, **l'émeute** |
| **Les prétoriens** | — | la garde de l'empereur | l'empereur |

Et le commandement dit tout du rang de chacun : le *praefectus vigilum* est **équestre**, le
*praefectus urbi* est **sénatorial** — et de ce fait au-dessus même du préfet du prétoire. Les
cohortes urbaines ont d'ailleurs été créées *pour faire contrepoids* aux prétoriens dans la ville.
On ne confie pas la même chose aux mêmes gens, et l'on s'arrange pour qu'aucun des trois ne puisse
tout.

### 2bis.3 Ce que faisaient les vigiles — et c'est notre § 4 mot pour mot

- **Le feu d'abord.** C'est leur raison d'être. Seaux, crochets, pics, échelles, cordes, **pompes à
  bras** (les *siphones*, décrites par Héron d'Alexandrie), et des couvertures matelassées — les
  *centones* — trempées d'eau ou de vinaigre.
- **La ronde de nuit, ensuite.** Ils patrouillent la ville chaque nuit et **arrêtent les suspects
  pour les présenter au préfet urbain** : ils sont le début de la chaîne, jamais le bout — la même
  chose exactement que le guet anglais qui remet ses ivrognes au constable (§ 4).
- **Le menu fretin qu'on n'invente pas** : ils surveillent les vêtements aux thermes, ils courent
  après les esclaves fugitifs, et **ils inspectent les bâtiments pour vérifier qu'il y a de l'eau**.
- **Les postes.** Une *castra* par cohorte, et des **excubitoria** — des postes avancés dans le
  quartier. C'est le poste et la tournée du § 1, deux siècles avant Paris, et sans la corvée.
- **Ce qui paie.** Après trois ans, le *frumentum publicum* — le grain gratuit — et pour les
  affranchis de rang inférieur, **la citoyenneté**. On ne les paie pas seulement en monnaie : on les
  paie en devenant quelqu'un.

**Le métier n'a pas changé entre Rome et Londres. C'est le PAYEUR qui a changé**, et tout en découle
— l'effectif, le statut des hommes, et à qui ils obéissent.

### 2bis.4 Où tombe Port-Réal — mesuré

Compté dans le monde cuit (`monde/gens/`, 401 866 corps) : **2 032 hommes du guet, 41 sergents,
6 capitaines — 2 079 manteaux d'or.** Le chiffre canon est deux mille, fixé par **Daemon Targaryen
lui-même quand il commandait le Guet en 104-105 AC** : c'est lui qui a porté l'effectif à ce nombre
et donné les manteaux dorés. La génération le reproduit à 4 % près, vingt-quatre ans après.

| | Effectif | Population | Un homme pour |
|---|---|---|---|
| Paris, guet royal | 60 | 200 000 | 3 300 |
| Paris, les deux couches | ~120 | 200 000 | 1 700 |
| **Rome, vigiles** (chiffre bas) | 3 920 | ~1 000 000 | **255** |
| **PORT-RÉAL, le Guet** | **2 079** | **401 866** | **193** |
| Rome, vigiles (chiffre haut) | 7 000 | ~1 000 000 | 143 |

**Port-Réal tombe à l'intérieur de la fourchette romaine.** Ce n'est pas une coïncidence de
division : c'est la même institution — payée, permanente, casernée, chargée du feu et de la nuit,
recrutée en bas de l'échelle. **Port-Réal est Rome, pas Paris.**

### 2bis.5 Et l'étage qui manque

C'est la trouvaille qui vaut le détour, et elle ne se voit qu'une fois le modèle romain posé.

| Étage romain | Ce que Port-Réal a | Compté |
|---|---|---|
| Les vigiles | **le Guet** | 2 079 |
| **Les cohortes urbaines** | **RIEN** | **0** |
| Les prétoriens | la garde du Donjon, la Garde Royale | 165 + 7 |

**Il n'y a pas d'étage de l'émeute.** On passe directement des manteaux d'or à la maison du roi. Ce
que Rome tenait avec quinze cents à six mille soldats d'un corps distinct, payé autrement et
commandé par un sénateur, Port-Réal ne le tient avec personne — et la seule autre force armée de la
ville est **privée** : 1 064 gardes de maison, comptés dans le même monde cuit, qui répondent à des
maisons et non à la Couronne.

**C'est la catastrophe de la Danse écrite d'avance.** En 130 AC, la ville s'émeut et prend d'assaut
la Fosse aux Dragons ; entre la foule et le Donjon Rouge il n'y a que le Guet, c'est-à-dire un corps
de veilleurs de nuit et de pompiers. Le chiffre de deux mille n'est pas trop grand : **c'est le zéro
d'à côté qui est le problème.**

---

## 3. L'horloge — le couvre-feu, puis une seule veille

### 3.1 Le couvre-feu ne tombe pas à la même heure partout

| Lieu | Heure |
|---|---|
| France, généralement (Exbalin) | entre **16-17 h** (vêpres) et **19 h** selon la saison |
| Paris, XIVᵉ | les cloches sonnent à **21 h**, gagnant les quartiers l'un après l'autre |
| Londres | dehors interdit après **20 h l'été, 21 h l'hiver** |
| Wangen (Alsace) | portes closes **une demi-heure après l'Angélus** |

**Retenir : ça se règle sur le jour et sur la cloche, jamais sur un chiffre.** Le mot lui-même le
dit — *couvre-feu*, « couvre le feu » : on couvre les braises, on rentre, on ferme. Ce qui suit
n'est pas une heure, c'est un régime.

### 3.2 Ce que le couvre-feu ferme, dans l'ordre

1. **Les portes de la ville.** § 6.
2. **Les tavernes.** La cloche du soir commande « la fermeture des portes de la cité, la fermeture
   des tavernes », et l'extinction des feux.
3. **Les rues elles-mêmes** — à Paris, des habitants font tendre **des chaînes à l'entrée de leur
   rue**, ou y posent de fortes portes. C'est de l'auto-défense de quartier, pas un dispositif
   royal, et c'est ce qui fait qu'une ville médiévale n'est pas un réseau ouvert la nuit mais une
   collection de culs-de-sac.
4. **Le droit de marcher.** § 4.

### 3.3 La veille est nocturne, et essentiellement d'un seul tenant

C'est le point où notre modèle s'écarte le plus (§ 9), donc il vaut d'être posé net :

- Paris : le service va **« depuis le couvre-feu jusqu'au lever du soleil »**.
- Winchester : **« du coucher au lever du soleil »**.
- Angleterre moderne : les guetteurs patrouillent **de 21 ou 22 heures jusqu'à l'aube**, et
  **proclament les heures** en tournant.

Le vocabulaire anglais fait la coupure lui-même : *watch and ward* — **le guet est la nuit, la garde
est le jour**. Ce sont deux services distincts, de nature et d'effectif différents, et le grand est
celui de la nuit. On ne trouve nulle part trois quarts égaux se relayant sur vingt-quatre heures :
c'est une figure de police moderne.

---

## 4. Ce qu'un guet fait réellement

Rangé par fréquence probable, du plus ordinaire au plus rare — c'est-à-dire à peu près l'inverse de
ce qu'on imagine.

| Ce qu'il fait | Détail |
|---|---|
| **Il regarde le feu** | La menace numéro un d'une ville de bois. C'est ce qui a fait glisser le métier du guetteur de tour (*Türmer*) de l'ennemi vers l'incendie. Il signale la direction : **drapeau rouge le jour, lanterne la nuit**. |
| **Il fait respecter le couvre-feu** | Un couvre-feu « informel », qui empêche de circuler **ceux qui n'ont pas de raison**. |
| **Il demande la lumière** | Celui qui doit sortir la nuit doit **crier sa présence et porter une lanterne**. Un homme sans lumière est présumé de mauvaise intention — Kathryn Warner : « surtout s'il omet de porter une lumière ». |
| **Il vérifie les portes closes** | Celles de la ville, et celles des maisons. |
| **Il ramasse** | Ivrognes, vagabonds, noctambules — qu'il **remet aux constables**. Il n'est pas au bout de la chaîne, il est au début. |
| **Il proclame l'heure** | Un guet est aussi une horloge parlante. Dans certaines villes le veilleur au beffroi « sonne le quart d'heure ». |
| **Il crie au secours** | Sa fonction en cas de vrai trouble n'est pas de le régler : c'est de donner l'alarme (§ 7). |

**Ce qu'il ne fait pas : de l'enquête.** Rien dans les sources ne décrit un guet qui cherche un
coupable. Il constate une présence à une heure interdite, et il livre.

### 4.1 Ce qu'il porte

- Le règlement anglais prescrit la **hallebarde** ; **peu s'y conformaient**, l'arme convenant mal à
  la marche.
- Ce qui est réellement décrit : un **bâton** (le *bil*, long manche à fer courbe), une **lanterne**,
  une **corne** pour l'alarme.
- Au XVIIIᵉ, la panoplie s'est réduite à **la lanterne et le bâton**.

**Trois objets, et deux d'entre eux ne sont pas des armes.** C'est la description la plus exacte de
ce qu'est un guet : un homme qui voit, un homme qu'on entend, et de quoi cogner en dernier recours.

---

## 5. Ce qu'un guet ne peut pas faire — et c'est le meilleur de la matière

Toute cette section vient des plaintes des autorités contre leur propre guet. **C'est la source la
plus fiable du dossier**, parce que personne n'a d'intérêt à inventer l'incompétence de ses agents.

### 5.1 Il dort, il boit, il joue

- Gauvard, sur Paris : les sergents **s'endorment, jouent aux cartes, se laissent corrompre par les
  malfaiteurs**.
- Cologne, **1452** : il faut **instituer des sergents pour faire respecter le service de guet**.
  Un corps chargé de surveiller le corps chargé de surveiller.
- Beaucoup préféraient **jouer aux dés dans les salles de garde** plutôt que veiller.
- Angleterre, **1617** : des guetteurs s'introduisent dans une maison et **y restent à boire et à
  fumer toute la nuit**.
- Rapports de **1609 et 1640** : des constables **libèrent le guet tôt le matin** — c'est-à-dire
  précisément **à l'heure où le plus grand danger était redouté**.
- Shakespeare fait du guet un ressort comique dans *Beaucoup de bruit pour rien*. Ça ne prouve rien
  en soi, mais ça mesure la réputation.

### 5.2 Il se laisse acheter

- **1641** : le guetteur Edward Gardener prend **deux shillings** pour laisser filer une femme.
- D'autres réclament de l'argent **simplement pour laisser passer**.

### 5.3 Il ne peut rien contre qui est au-dessus de lui

L'anecdote la plus éclairante du dossier. Londres, **1641** : Lord Feilding, arrêté à une heure du
matin, s'indigne et jure de « **calotter l'oreille** » du constable. La défense du constable est
parfaite et dit tout du problème :

> Il est impossible de distinguer un lord d'un autre homme par l'extérieur d'un carrosse.

**Le guet est aveugle au rang tant qu'il n'a pas ouvert la portière — et il n'a pas le droit de
l'ouvrir sans risque.** C'est là que se loge toute la scène jouable : chaque arrestation nocturne
est un pari sur qui est dedans.

### 5.4 Et la rue n'est pas de son côté

Gauvard, sur les réseaux de solidarité urbains des XIVᵉ-XVᵉ siècles : la violence citadine se règle
dans un tissu de voisinage, de parentèle et de métier qui **se referme contre l'intervention
extérieure**. Un sergent qui saisit un homme dans sa propre rue ne saisit pas un individu : il
touche à un réseau, qui répond.

> ⚠ **Réserve honnête** : nous n'avons pas pu lire le texte de Gauvard, seulement sa notice et des
> résumés. La direction de l'argument est sûre, le détail ne l'est pas. À creuser avant d'en tirer
> une règle chiffrée.

### 5.5 Personne ne veut le faire

- Villes allemandes : **ceux qui avaient de l'influence l'utilisaient pour s'exempter**, ou
  trouvaient des substituts. **Göttingen** impose des **tours de guet supplémentaires en punition**
  — le service est donc une peine, ce qui dit exactement ce qu'on en pensait.
- Angleterre : dès les années 1660, se faire remplacer devient courant ; à la fin du XVIIᵉ le guet
  de nuit est **« virtuellement une force entièrement rémunérée »**. En **1737** l'obligation de
  service est officiellement convertie en **impôt**, et le salaire fixé à **treize livres l'an**.

**La corvée se transforme donc partout en salaire, par évaporation.** Et c'est exactement la
transition que notre Port-Réal a déjà faite — sans jamais avoir eu l'étape d'avant (§ 9).

### 5.6 Les exemptions, à Paris, sont un document social à elles seules

Le guet est **obligatoire jusqu'à soixante ans**. En sont dispensés :

- les **jurés** élus, pendant leur mandat ;
- des métiers entiers à titre permanent — **orfèvres, tonneliers, armuriers, imagiers, sculpteurs,
  archers, chapeliers de plumes de paon, marchands**, qui ont plaidé être « établis pour servir le
  roi, l'Église, les chevaliers et gentilshommes » ;
- les **bouchers** et divers métiers de luxe ;
- **les fous, les malades qu'on vient de saigner, et les maris dont la femme est en couches.**

Et la sanction est réglée : le bourgeois empêché doit **prévenir le chevalier du guet le soir même,
en envoyant une femme de sa maison** ; faute de quoi, amende ou saisie.

> Le chapelier de plumes de paon dispensé de guet parce qu'il sert les gentilshommes est, à lui
> seul, une scène de conseil.

---

## 6. Les portes et les clefs

L'objet le plus chargé du dispositif, et le seul qui produise un geste tous les soirs.

- **Les clefs sont confiées à un petit nombre d'hommes nommés**, responsables de fermer la ville à
  la nuit tombée.
- Le geste est cérémoniel et il change la main : le portier **remet les clefs au magistrat** (le
  *Schultheiss*) — et **à partir de cet instant, plus personne n'entre ni ne sort jusqu'au
  lendemain**.
- Ce sont des objets physiques et lourds : des clefs de plus de deux livres, de près de deux pieds
  de long.
- De jour, la porte est un **point de contrôle** : on y paie un péage, on y inspecte les
  marchandises, **on y interroge les étrangers**. Les corps de garde et les tours se **louent** même
  à des ermites, des recluses et des officiers de la ville.

**Et le point le plus utile de tout le dossier pour l'exercice de la Gadoue** — Allemagne, bas Moyen
Âge :

> Les portes lourdes des postes d'entrée devaient être fermées par des **citoyens triés**, non par
> les mercenaires, **par méfiance envers ces derniers**.

C'est-à-dire : **on ne confie pas la clef à la troupe payée.** La ville se méfie de ses propres
défenseurs professionnels exactement là où la trahison serait décisive. Toute prise de ville par
l'intérieur passe par cette serrure-là, et les contemporains le savaient.

---

## 7. Le bruit — le vrai réseau

Le guet est trop peu nombreux pour couvrir une ville. Ce qui la couvre, c'est **le son**.

- **La cloche est l'infrastructure.** Le son « atteignait tout le monde à l'intérieur des murs
  simultanément » — un réseau à diffusion totale et à latence nulle, ce qu'aucun coureur ne fait.
  Les habitants **apprenaient à distinguer** les sonneries du travail, du commerce, du gouvernement,
  de l'urgence et de l'office.
- **Le tocsin** — sonnerie rapide et irrégulière — appelle la milice au feu ou à l'attaque.
- **Et sonner sans droit est un crime capital.** Florence, règlement de **1355** sur la cloche
  *Martinella* : la sonnerie non autorisée des cloches civiques est **traitée comme une trahison**.
  Le canal est si puissant qu'on protège l'accès au clocher comme on protège une porte.
- **La corne** est l'échelon du dessous : celle du guetteur, celle du Türmer, qui donne l'alarme au
  feu et en indique la direction.
- **La clameur** est l'échelon humain : la *hue and cry*, qui transforme les passants en poursuivants
  (§ 0).

**Quatre étages d'un même système : le cri, la corne, la cloche, le tocsin.** C'est la chaîne de
commandement réelle d'une ville la nuit, et le guet n'en est qu'un émetteur parmi d'autres.

---

## 8. Quand ça bascule — le guet, la milice, et la muraille

Le guet de ville n'est pas une troupe, mais il est **le point de contact** entre la ville et sa
défense. Ce que les sources disent de ce basculement :

- **La milice est large et armée chez elle.** Selon les villes, **entre 5 % et 30 % de la population
  sont citoyens de plein droit**, obligés de servir dans la milice et **de garder armes et harnois à
  leur domicile**.
- **Elle se rassemble par rue.** « Un citoyen n'avait qu'à faire quelques pas hors de sa porte pour
  rejoindre son capitaine de rue ou de quartier. » L'organisation est **géographique** : un capitaine
  de haut rang par quartier, un notable local par rue — disposition qui **garde le pouvoir en place
  maître de l'urgence**.
- **Les effectifs de muraille sont maigres.** Nuremberg, **1449-50** : **cent-huit hommes gardaient
  seuls les ouvrages extérieurs**, d'autres garnissant tours et portes.
- **Les mercenaires coûtent cher et ne sont pas de confiance** (§ 6).

**Pour la porte de la Gadoue, ce dossier confirme la prémisse et lui donne sa matière.** Le
[`README`](../bataille/README.md) pose un Guet « qui a passé sa vie à peser des tonneaux et à casser
des têtes de fêtards ». Les sources vont plus loin que ça : un guet historique **joue aux dés dans
son corps de garde**, se fait **relever trop tôt par son propre constable à l'heure du danger**, et
compte dans ses rangs tous ceux qui n'ont pas eu les moyens de s'exempter. Ce n'est pas une troupe
médiocre — **c'est une institution dont la médiocrité était connue, écrite, et légiférée contre**.

---

## 9. Ce que ça dit de notre modèle — après mesure

Mesuré sur `scripts/monde/besoins.py` (`VEILLES`, `RONDES`) et `ecrans/modules/monde/journee.js`
(`quart()`, `journee()`), état du 25 août 2026.

### 9.1 Ce que le modèle a déjà juste — et ce n'est pas rien

1. **Le poste avant la tournée.** `VEILLES["guet"]` donne `tours=3, duree=38` sur un quart de 480
   minutes : **114 minutes en ronde, 366 au poste — 24 % dehors, 76 % dedans.** C'est exactement le
   partage historique entre le fixe et le mobile, et le commentaire du code (« entre deux tours, on
   est AU POSTE — c'est l'état par défaut ») énonce la bonne règle. **Rien à changer ici.**
2. **L'heure qui flotte.** Le code écrit : « une ronde qui passe à heure fixe est une ronde qu'on
   attend au coin de la rue ». Aucune source ne le contredit, et l'inspection de poste en poste du
   guet royal suppose précisément l'imprévisibilité. **Juste.**
3. **Le circuit pris dans les adresses du poste** — puits, échoppe, taverne, marché. Le guet passe
   où sont les gens, et **la taverne est bien la cible principale** (fermeture au couvre-feu). Le
   modèle a eu raison sans le savoir.
4. **On ne patrouille pas seul** (`patrouilles=12`, qui donne des paires à ~27 hommes de quart par
   corps de garde). Conforme à tout ce qu'on a lu ; le guet est toujours un groupe.

### 9.2 Trois écarts mesurés

**a) La ronde n'est pas une ronde : c'est une station.** `besoins.py` écrit noir sur blanc qu'« une
ronde n'a pas de but, elle a un CIRCUIT ». Le code fait autre chose : `quart()` pousse une étape à
**un seul `bat`**, et `journee.js` la joue en `route` puis `sur-place` jusqu'à `fin`. Un homme du
guet marche donc jusqu'à une taverne et **y reste trente-huit minutes**, immobile, dispersé dans un
disque de 4 mètres. **À l'écran il est indiscernable d'un homme qui boit.** L'intention est écrite,
elle n'est pas implémentée : il faudrait une étape à plusieurs `bat` successifs.

**b) Trois quarts égaux sur vingt-quatre heures.** `quarts=[[360,480],[840,480],[1320,480]]` : 6-14 h,
14-22 h, 22-6 h. Un tiers de l'effectif dehors à midi comme à trois heures du matin. **Le guet
historique est nocturne** (*watch and ward*, § 3.3) ; la garde de jour existe mais elle est d'une
autre nature et d'un autre volume. Notre découpage est celui d'un commissariat, pas d'un guet.

**c) ~~Notre Guet est seize fois plus dense que la police de Paris.~~ — RETIRÉ.**

> ⚠ **Cette section affirmait un écart de 1 à 16 avec Paris et laissait entendre un défaut de
> génération. C'était faux, et pour la raison la plus bête : le mauvais étalon.** Deux mille manteaux
> d'or est **canon**, et daté de Daemon Targaryen commandant le Guet en 104-105 AC ; la génération le
> reproduit à 2 079, soit +4 %. Comparé aux vigiles de Rome plutôt qu'au guet de Paris, Port-Réal
> tombe **dans la fourchette** — un homme pour 193, contre un pour 143 à 255. Voir **§ 2 bis**, écrit
> pour cette raison.
>
> **Ce qu'il fallait relever à la place**, et qui est un vrai écart : **l'étage de l'émeute n'existe
> pas** (§ 2bis.5). Rome tenait sa capitale à trois corps ; nous en avons deux, et le manquant est
> précisément celui qui aurait servi en 130.

Ce qui restait juste dans l'ancienne rédaction, et qu'on garde : **le Guet de Port-Réal n'est pas un
guet médiéval**, et il ne faut pas raisonner sur lui avec ces intuitions-là. Corollaire réjouissant :
**il est assez nombreux pour tenir une porte**, ce que l'exercice de la Gadoue met à l'épreuve.

### 9.3 Ce qui manque, par ordre d'effet

1. **Le couvre-feu. C'est la pièce absente, et c'est la même figure que le « signal d'arrière » du
   dossier fuite** : le mécanisme dont dépend tout le reste et que le moteur n'a pas. Aujourd'hui
   `journee()` fait sortir les corps selon leurs `besoins` à toute heure, et **rien ne vide jamais la
   rue**. Or c'est le couvre-feu qui rend le guet possible (§ 0). Ce qu'il faudrait : une heure de
   couvre-feu par lieu, qui coupe les besoins nocturnes — et alors **un homme dehors la nuit devient
   un fait**, ce qu'il n'est pas aujourd'hui.
2. **Le noctivague, qui découle du précédent.** Tant que tout le monde peut être dehors, le guet
   n'a rien à voir. Dès qu'il y a couvre-feu, croiser quelqu'un est un **événement** : on demande la
   lanterne, on demande la raison, et l'on décide. C'est la plus petite scène jouable que ce dossier
   rende possible, et elle ne coûte qu'une heure dans une table.
3. **La clameur.** Le vrai réseau est le son (§ 7), et nous n'avons **ni cri, ni corne, ni cloche**.
   C'est ce qui manque pour qu'un événement de rue atteigne qui que ce soit — y compris le joueur.
4. ~~**La corvée.**~~ **— RETIRÉ, et remplacé par le point ci-dessous.** Cette entrée réclamait un
   guet assis : le boulanger qui a son tour ce soir, l'exemption qu'on plaide, le remplaçant qu'on
   paie. **Port-Réal n'a pas cette institution et ne doit pas l'avoir** : c'est une ville romaine, où
   l'État paie et où l'habitant ne veille donc jamais (§ 2 bis). L'ajouter aurait été greffer une
   commune française sur une capitale impériale — la faute même que le § 2 bis vient corriger.
4bis. **L'étage de l'émeute, qui n'existe pas** (§ 2bis.5). Entre 2 079 manteaux d'or et les 172
   hommes de la maison du roi, il n'y a **rien** ; la seule autre force de la ville est privée
   (1 064 gardes de maison, qui répondent à des maisons). Rome tenait sa capitale à trois corps de
   nature et de commandement différents, précisément pour qu'aucun ne puisse tout. **C'est le manque
   le plus lourd du modèle**, et il ne se comble pas en ajoutant des hommes : il se joue. Qui appelle
   la seconde force, avec quel or, et de qui est-elle ? Le jour où quelqu'un pose cette question dans
   la salle, on aura la Danse en une réplique.
5. **La geôle au bout de l'arrestation.** `corps-de-garde` et `geole` existent tous les deux dans
   `peupler.py`, et **rien ne les relie**. Historiquement le corps de garde *est* la cellule : les
   *watch houses* londoniens servaient de point de rassemblement, d'abri, **et de cachot jusqu'au
   jugement du matin**.
6. **Le guet ne produit aucun fait.** Il passe, et il ne se passe jamais rien. Il ne demande jamais
   une lanterne, ne ferme jamais une taverne, ne signale jamais un feu, n'arrête personne, ne remet
   jamais une clef. **C'est une présence sans événement** — et c'est, mot pour mot, le même défaut
   que les trois dossiers précédents relèvent ailleurs : le moteur sait tenir un état, il ne sait pas
   émettre.

---

## 10. Ce qu'on a écarté

Ce dossier a rencontré deux chiffres trop nets pour être vrais. On les note pour qu'ils ne
reviennent pas par une autre porte.

**Les signaux du guet de nuit florentin, 1415.** On lit — *une sonnerie longue = rien à signaler,
deux brèves = suspect, trois rapides = feu, un son continu = attaque armée*, attribués aux
*Statuti della Guardia Notturna* — et c'est exactement ce dont un moteur rêve. **Écarté.** Une seule
source le porte, un site d'agrégation ; le moteur de recherche nous l'a ensuite renvoyé en écho
depuis cette même page, ce qui n'est pas une confirmation. Et l'article de medievalists.net
consacré aux cloches comme réseau urbain, qui aurait dû le citer, **ne le connaît pas** — il
documente en revanche le règlement florentin de **1355** sur la *Martinella*. Ce qui reste vrai
autour : les villes avaient bien des codes de sonnerie distincts, et sonner sans droit était un
crime grave.

**Aldgate, 1377 : huit guetteurs pour plus de 1 500 âmes.** Même provenance, même écho. **Écarté
comme ratio**, gardé comme ordre de grandeur d'un *quota de quartier* — ce qui est cohérent avec
le quota de Winchester (six par porte) et ne dit rien d'une densité de population.

**La leçon de méthode**, et elle vaut pour les prochains dossiers : **un chiffre qui arrange
parfaitement le modèle est un chiffre à vérifier deux fois.** Les deux écartés ici sont précisément
ceux qu'on aurait implémentés le jour même.

---

## Sources

Consultées le 25 août 2026. **Deux ancrages savants nommés et vérifiables** — Claude Gauvard, citée
par Arnaud Exbalin (Université Paris Nanterre) dans *The Conversation* ; et David Eltis,
*Nottingham Medieval Studies* v.33 (1989), via De Re Militari. Le reste est de la littérature
secondaire, des textes normatifs en édition en ligne, et de la vulgarisation. Les noms qui y
figurent — **Jean Verdon, Simone Delattre, Alain Cabantous, Élisabeth Crouzet-Pavan, Carlo M.
Cipolla, Kathryn Warner** — sont cités par ces pages et n'ont pas été lus dans le texte.

**Textes normatifs et notices**

- [Statutes Project — *1285: 13 Edward 1: The Statute of Winchester*](https://statutes.org.uk/site/the-statutes/thirteenth-century/1285-13-edward-1-the-statute-of-winchester/)
- [Wikipédia — *Statute of Winchester*](https://en.wikipedia.org/wiki/Statute_of_Winchester)
- [Wikipédia — *Hue and cry*](https://en.wikipedia.org/wiki/Hue_and_cry)
- [Wikipédia — *Guet royal*](https://fr.wikipedia.org/wiki/Guet_royal)
- [Wikipédia — *Curfew bell*](https://en.wikipedia.org/wiki/Curfew_bell)
- [Wikipédia — *Tocsin*](https://en.wikipedia.org/wiki/Tocsin)
- [Britannica — *Watch-and-ward system*](https://www.britannica.com/topic/watch-and-ward-system)

**Études et articles de fond**

- [Arnaud Exbalin, *Le couvre-feu permanent : une histoire longue du confinement nocturne*, The Conversation](https://theconversation.com/le-couvre-feu-permanent-une-histoire-longue-du-confinement-nocturne-152003)
- [Claude Gauvard, *Violence citadine et réseaux de solidarité. L'exemple français aux XIVe et XVe siècles*, Annales ESC 1993 (Persée)](https://www.persee.fr/doc/ahess_0395-2649_1993_num_48_5_279202)
- [Claude Gauvard, *Violence et ordre public au Moyen Âge*, Picard 2005 — compte rendu (OpenEdition)](https://journals.openedition.org/chs/1218)
- [David Eltis, *Towns and Defence in Later Medieval Germany* (De Re Militari)](https://deremilitari.org/2014/03/towns-and-defence-in-later-medieval-germany/)
- [Brewminate — *Keeping Watch: Order and Law Enforcement in Late Medieval and Early Modern England*](https://brewminate.com/keeping-watch-order-and-law-enforcement-in-late-medieval-and-early-modern-england/)
- [Medievalists.net — *The Bell Tower as Urban Infrastructure*](https://www.medievalists.net/2026/06/bell-tower-medieval/)
- [ResearchGate — *A brief examination of warfare by medieval urban militias in Central and Northern Europe*](https://www.researchgate.net/publication/349300158_A_brief_examination_of_warfare_by_medieval_urban_militias_in_Central_and_Northern_Europe)

**Rome — les vigiles et les cohortes urbaines (§ 2 bis)**

- [Ostia Antica — *Vigiles: introduction*](https://www.ostia-antica.org/dict/topics/caserma/intro.htm) — le plus détaillé, et il nomme l'analyse de **John Rainbird** sur le doublement de 205
- [World History Encyclopedia — *Vigiles*](https://www.worldhistory.org/Vigiles/)
- [World History Encyclopedia — *Cohortes Urbanae*](https://www.worldhistory.org/Cohortes_Urbanae/)
- [Wikipédia — *Cohortes urbanae*](https://en.wikipedia.org/wiki/Cohortes_urbanae)
- [Britannica — *Vigiles*](https://www.britannica.com/topic/vigiles)
- [A Wiki of Ice and Fire — *City Watch of King's Landing*](https://awoiaf.westeros.org/index.php/City_Watch_of_King%27s_Landing) — les deux mille de Daemon, 104-105 AC
- [A Wiki of Ice and Fire — *Daemon Targaryen*](https://awoiaf.westeros.org/index.php/Daemon_Targaryen)

**Vulgarisation — utilisée pour le détail matériel, jamais pour un chiffre seul**

- [Histoires de Paris — *Les chevaliers du guet*](https://www.histoires-de-paris.fr/chevalier-guet/)
- [Histoires de Paris — *Le couvre-feu du Moyen Âge*](https://www.histoires-de-paris.fr/couvre-feu-moyen-age/)
- [Police parisienne au Moyen Âge](http://grande-boucherie.chez-alice.fr/Police-parisienne.htm)
- [CKSA — *Medieval Cities at Night: When Towns Literally Locked Themselves In*](https://www.cksa.com/history/medieval-cities-at-night-when-towns-literally-locked-themselves-in/)
- [History Medieval (Substack) — *After the Bell: Nightwalkers, Curfews, and the Policed Darkness of the 14th-Century Town*](https://historymedieval.substack.com/p/after-the-bell-nightwalkers-curfews)
- [Second.wiki — *Türmer* (tower keeper)](https://second.wiki/wiki/tc3bcrmer)
- [French Moments — *Fortified city gates of Alsace*](https://frenchmoments.eu/city-gates-of-alsace/)
- [Wikipédia — *City gate*](https://en.wikipedia.org/wiki/City_gate)

**Écartées** — voir § 10 : [History Uncovered — *The Medieval Night Watchman*](https://history-uncovered.com/articles/the-medieval-night-watchman-guardian-of-sleeping-cities), source unique des signaux florentins de 1415 et du ratio d'Aldgate 1377.
