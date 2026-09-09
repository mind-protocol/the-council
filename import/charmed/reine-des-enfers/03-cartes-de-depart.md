# Les cartes de départ — « La Reine des Enfers »

Règle du 6.9 : un `demander` de camp ne porte ni `lieu` ni `tenu_par` ; la
phrase les dit, l'`arbitrer` les écrit. Les lignes ci-dessous sont dans
cette forme. `genre` est l'emoji de la pièce ; `arrive_tour` celui de
l'arbitrage.

---

## 1. Le bien — ⚫ onze

### 🧊 `piper`
```jsonl
{"camp":"bien","coup":"demander","id":"piper","genre":"🧊","texte":"Piper Halliwell, au manoir — elle fige, elle fait exploser ; elle a pleuré Prue ; elle a perdu une deuxième sœur sans qu'elle soit morte"}
{"camp":"arbitre","coup":"arbitrer","sur":"piper","verdict":"accorde","arrive_tour":1,"lieu":"manoir","nombre":1,"motif":"canon 4x19-4x20 : au manoir, entière"}
```
**Portée** : *fige ce qui n'est pas de haut rang (la cour, Lazare, un vampire, un démon envoyé) ; ne fige ni Cole, ni la Voyante, ni Phoebe. Fait exploser : vainc un démon de la cour, un vampire ; blesse Lazare sans le vaincre ; ne touche ni Cole ni la Voyante. Clef sur tout état du bien ; pièce du retournement de Phoebe (sa sœur). Mortelle. Cole ne la frappe pas devant Phoebe sans le payer.*

### ✨ `paige`
```jsonl
{"camp":"bien","coup":"demander","id":"paige","genre":"✨","texte":"Paige Matthews, au manoir — elle s'orbe, appelle les objets ; elle a vu Cole avant tout le monde, et elle ne lui pardonne rien"}
{"camp":"arbitre","coup":"arbitrer","sur":"paige","verdict":"accorde","arrive_tour":1,"lieu":"manoir","nombre":1,"motif":"canon 4x16-4x19"}
```
**Portée** : *s'orbe hors d'une frappe, orbe une sœur ou un innocent hors de portée (parade) ; appelle un objet — le tonique des mains de Phoebe, une potion à lancer. Pièce du retournement de Phoebe. Moitié être de lumière : un vampire la tourne (retournement, 4 tours), une flèche la gèle. Mortelle.*

### 🕊️ `leo`
```jsonl
{"camp":"bien","coup":"demander","id":"leo","genre":"🕊️","texte":"Leo Wyatt, au manoir — il s'orbe, il soigne ; Phoebe est encore sa protégée : il l'entend si elle l'appelle"}
{"camp":"arbitre","coup":"arbitrer","sur":"leo","verdict":"accorde","arrive_tour":1,"lieu":"manoir","nombre":1,"motif":"canon : il reste l'être de lumière des trois, même de celle qui règne en bas"}
```
**Portée** : *pare une frappe sur une sœur ou un innocent, une à la fois ; ne soigne pas les morts. Le seul chemin vers Phoebe qui ne descende pas par la cour : clef ou pièce du retournement de Phoebe (il l'entend, il monte la chercher si elle appelle). Ne frappe pas. Ne peut pas entrer à l'appartement de Cole sans y être appelé (portée de l'appartement).*

### 📖 `livre`
```jsonl
{"camp":"bien","coup":"demander","id":"livre","genre":"📖","texte":"le Livre des Ombres, au grenier — les sorts, les recettes, ce que les aïeules savent d'un enfant né du mal"}
{"camp":"arbitre","coup":"arbitrer","sur":"livre","verdict":"accorde","arrive_tour":1,"lieu":"grenier","nombre":1,"motif":"canon"}
```
**Portée** : *clef sur un état du bien où un sort ou une recette existe ; répond à une question ; verrou sur une clef adverse que son savoir contredit. Ne frappe jamais. Aucune main du mal ne le prend — Phoebe retournée pourrait, et c'est un coup de Cole à quatre tours.*

### 🔱 `sort-des-trois`
```jsonl
{"camp":"bien","coup":"demander","id":"sort-des-trois","genre":"🔱","texte":"le sort du Pouvoir des Trois — la seule chose qui vainc une Source ; il faut les trois voix, et l'une d'elles règne en bas"}
{"camp":"arbitre","coup":"arbitrer","sur":"sort-des-trois","verdict":"accorde","arrive_tour":1,"lieu":"grenier","nombre":1,"motif":"canon 4x20 et 4x21 : il vainc Cole, puis consume la Voyante par l'enfant. INERTE tant que Phoebe n'est pas revenue"}
```
**Portée** : *frappe qui vainc une Source — Cole, ou la Voyante couronnée (par l'enfant en elle) — et tout démon supérieur. Exige les trois sœurs libres, vivantes et du bien à la pose : tant que Phoebe est à Cole, l'arbitre refuse. Ne se consume pas ; gelé un tour après la frappe.*

### 🧪 `potion`
```jsonl
{"camp":"bien","coup":"demander","id":"potion","genre":"🧪","texte":"une potion brassée d'après le Livre, dans la cuisine — de quoi vaincre un démon de la cour ou un vampire ; elle frappe une fois"}
{"camp":"arbitre","coup":"arbitrer","sur":"potion","verdict":"accorde","arrive_tour":2,"lieu":"cuisine","nombre":1,"motif":"brasser prend un tour. Convention 2 : elle FRAPPE, elle ne pare pas, et l'arbitre la consume en tranchant"}
```
**Portée** : *frappe qui vainc un démon de la cour, un vampire, un démon envoyé ; ne touche ni Cole, ni la Voyante, ni Lazare, ni Phoebe. Se consume à l'atterrissage (l'arbitre tranche `detruit`). Jamais en parade. Paige la lance.*

### 🚔 `darryl`
```jsonl
{"camp":"bien","coup":"demander","id":"darryl","genre":"🚔","texte":"Darryl Morris — il trouve les innocents avant les démons, il les cache, il ne se bat pas"}
{"camp":"arbitre","coup":"arbitrer","sur":"darryl","verdict":"accorde","arrive_tour":1,"lieu":"san-francisco","nombre":1,"motif":"canon"}
```
**Portée** : *clef qui trouve et met à l'abri un innocent (verrou sur une frappe visant un innocent, avec délai) ; ne frappe pas, ne touche aucun démon. Mortel : la cour peut le frapper.*

### 👵 `grams`
```jsonl
{"camp":"bien","coup":"demander","id":"grams","genre":"👵","texte":"Grams, invoquée au grenier — elle sait ce que les aïeules pensent d'un enfant né du mal, et elle parle à Phoebe comme personne"}
{"camp":"arbitre","coup":"arbitrer","sur":"grams","verdict":"accorde","arrive_tour":2,"lieu":"grenier","nombre":1,"motif":"une invocation, un tour"}
```
**Portée** : *répond une fois, vrai ; clef sur un état du bien où un savoir manque ; pièce du retournement de Phoebe (elle la lignée). Ne frappe pas, ne pare pas ; repart deux tours après usage.*

### ☁️ `fondateurs`
```jsonl
{"camp":"bien","coup":"demander","id":"fondateurs","genre":"☁️","texte":"les Fondateurs — ils savent ce qu'est l'enfant ; ils répondent par Leo, lentement"}
{"camp":"arbitre","coup":"arbitrer","sur":"fondateurs","verdict":"accorde","arrive_tour":3,"lieu":"en-haut","nombre":1,"motif":"deux tours"}
```
**Portée** : *répond à une question ; clef sur un état du bien qui touche l'enfant (ce qu'il est, ce qu'on peut en faire) ; jamais une frappe, jamais un verrou. Chaque appel expose Leo à un rappel d'un tour.*

### 🫀 `l-homme-en-cole`
```jsonl
{"camp":"bien","coup":"demander","id":"l-homme-en-cole","genre":"🫀","texte":"ce qui reste de l'homme en Cole — il aime Phoebe, il lutte contre l'essence, il ne la laissera pas mourir ; c'est au bien, et c'est dans le corps de l'ennemi"}
{"camp":"arbitre","coup":"arbitrer","sur":"l-homme-en-cole","verdict":"accorde","arrive_tour":1,"lieu":"appartement","nombre":1,"motif":"canon 4x14-4x20 : Cole lutte jusqu'au bout, et c'est ce qui le perd. Une pièce du BIEN logée chez Cole : il ne peut pas l'engager, il peut la détruire (l'essence l'emporte : quatre tours, la Voyante aide)"}
```
**Portée** : *pièce du retournement de Phoebe (elle voit l'homme, pas le trône) ; verrou sur une frappe de Cole visant une sœur ou un innocent devant Phoebe (il hésite) ; clef sur « Cole hésite » qui ouvre une clef de Cole. Ne frappe pas. Cole peut la détruire — l'essence l'emporte — en quatre tours, deux avec la Voyante ; détruite, Cole ne hésite plus et le retournement de Phoebe passe à six tours.*

### 🏠 `manoir`
```jsonl
{"camp":"bien","coup":"demander","id":"manoir","genre":"🏠","texte":"le manoir Halliwell — le seul endroit où Phoebe est chez elle ; ce qui s'y dit, elle l'entend autrement"}
{"camp":"arbitre","coup":"arbitrer","sur":"manoir","verdict":"accorde","arrive_tour":1,"lieu":"san-francisco","nombre":1,"motif":"canon ; un lieu, ne bouge pas"}
```
**Portée** : *un lieu. Pièce du retournement de Phoebe si elle y vient (une clef de Leo ou de Paige l'y amène) ; verrou sur une clef de Cole qui la tient à l'appartement. Ne frappe pas. La cour peut y entrer (Cole y shimmere) ; Lazare aussi.*

### À demander en cours de partie
| Pièce | Condition | Délai | Portée |
|---|---|---|---|
| 🧪 `potion-2` | — | +1 | comme `potion` |
| 🦇 `reine-des-vampires` | le bien la cherche (une clef avec Darryl ou le Livre) | +4 | *frappe Cole (elle veut le trône) — le blesse, ne le vainc pas ; retourne Paige (4 tours) si Paige l'approche ; meurt par le sort des trois ou par Cole ; ne sert que qui la lâche* |
| ⚰️ `enterrement-de-lazare` | Lazare vaincu une fois | +1 | *clef à deux pièces (Piper, Paige) qui retire Lazare du plateau pour de bon* |
| 🍼 `ce-que-l-enfant-est` | les Fondateurs ou Grams ont répondu | +2 | *savoir : verrou sur la clef du tonique (Phoebe cesse de boire si elle sait) ; verrou sur le retournement de l'enfant par la Voyante (Phoebe refuse)* |

## 2. Cole, la Source — 🟢 huit

### 👑 `cole-source`
```jsonl
{"camp":"cole","coup":"demander","id":"cole-source","genre":"👑","texte":"Cole Turner, la Source — couronné ce soir par le Grimoire ; il flambe, il règne, il aime Phoebe et il lutte"}
{"camp":"arbitre","coup":"arbitrer","sur":"cole-source","verdict":"accorde","arrive_tour":1,"lieu":"appartement","nombre":1,"motif":"canon 4x19 fin"}
```
**Portée** : *frappe qui vainc tout ce qui n'est pas une Halliwell ni la Voyante — un innocent, Leo, Darryl, un vampire, la cour d'un autre ; frappe Piper ou Paige (l'arbitre refuse devant Phoebe tant que « l'homme en Cole » existe). Ne frappe JAMAIS Phoebe. Ne se fige pas, aucune potion ne le touche ; seul le sort des trois le vainc. Clef sur tout état de Cole ; parade sur le retournement de Phoebe (sa parole à elle) ; retourne Phoebe de nouveau si elle est revenue (8 tours). Détruit « l'homme en Cole » en quatre tours, deux avec la Voyante.*

### 💍 `phoebe`
```jsonl
{"camp":"cole","coup":"demander","id":"phoebe","genre":"💍","texte":"Phoebe Halliwell, reine des Enfers — elle a choisi Cole devant ses sœurs ; elle porte son fils ; elle a bu le tonique une fois. Elle aime encore ses sœurs, et elle hésite"}
{"camp":"arbitre","coup":"arbitrer","sur":"phoebe","verdict":"accorde","arrive_tour":1,"lieu":"appartement","nombre":1,"motif":"canon 4x19 fin. Pièce de Cole, RETOURNABLE par le bien en quatre tours (Piper, Paige, Leo, Grams, le manoir, l'homme en Cole) ; deux si Cole tue un innocent qu'elle avait sauvé ou lève la main sur une sœur devant elle ; six si elle boit le tonique après la pose"}
```
**Portée** : *prémonition (pare une frappe sur Cole qu'elle a vue venir — la seule parade de Cole contre le sort des trois, une fois) ; lévitation. Clef sur les états de Cole ; verrou sur une clef du bien qui la concerne (elle refuse). Aucun camp ne la frappe : Cole ne veut pas, le bien ne peut pas (l'arbitre refuse), la Voyante seulement pour l'enfant. Retournée par le bien, elle revient avec ses pouvoirs et le Pouvoir des Trois existe à l'instant.*

### 👹 `la-cour`
```jsonl
{"camp":"cole","coup":"demander","id":"la-cour","genre":"👹","texte":"la cour des Enfers — huit démons de rang moyen qui servent qui est assis ; ils frappent, ils tiennent, ils changent de maître avec le trône"}
{"camp":"arbitre","coup":"arbitrer","sur":"la-cour","verdict":"accorde","arrive_tour":1,"lieu":"enfers","nombre":8,"motif":"canon 4x20-4x21 ; nombre 8 : une frappe du bien en tue un nombre. Passe au camp de qui est couronné (retournement gratuit de l'arbitre au constat d'un couronnement)"}
```
**Portée** : *verrou sur un état du bien ; frappe sur un innocent, Darryl, Leo hors du manoir ; frappe sur Piper ou Paige hors du manoir. Se figent, explosent, meurent par potion — un nombre, jamais la bande. Tiennent Phoebe à l'appartement (parade sur son retournement). Changent de camp avec le trône.*

### ⛪ `pretre-noir`
```jsonl
{"camp":"cole","coup":"demander","id":"pretre-noir","genre":"⛪","texte":"le prêtre noir — il a marié Cole et Phoebe en noce sombre ; il sait couronner, il ne frappe pas"}
{"camp":"arbitre","coup":"arbitrer","sur":"pretre-noir","verdict":"accorde","arrive_tour":1,"lieu":"enfers","nombre":1,"motif":"canon 4x15, 4x19"}
```
**Portée** : *clef sur « Phoebe règne » (le lien de la noce sombre : parade sur son retournement, une fois) ; clef de couronnement (avec le Grimoire, devant la cour) pour QUI le tient — la Voyante peut le retourner en deux tours. Ne frappe pas ; se fige ; meurt par potion ou par Piper.*

### 📕 `grimoire`
```jsonl
{"camp":"cole","coup":"demander","id":"grimoire","genre":"📕","texte":"le Grimoire — il a couronné Cole ce soir ; il couronnera qui le tient devant la cour"}
{"camp":"arbitre","coup":"arbitrer","sur":"grimoire","verdict":"accorde","arrive_tour":1,"lieu":"enfers","nombre":1,"motif":"canon 4x19 ; ne touche pas le Livre des Ombres"}
```
**Portée** : *clef de couronnement pour qui le tient, avec le prêtre noir, devant la cour ; sert « je suis assis ». La Voyante peut le retourner (2 tours) ; le bien peut le détruire (une frappe des trois, ou Paige qui l'appelle et Piper qui l'explose — deux pièces). Ne frappe pas.*

### ⚰️ `lazare`
```jsonl
{"camp":"cole","coup":"demander","id":"lazare","genre":"⚰️","texte":"un démon Lazare — chaque frappe le tue, et il revient ; on ne s'en défait qu'en l'enterrant"}
{"camp":"arbitre","coup":"arbitrer","sur":"lazare","verdict":"accorde","arrive_tour":3,"lieu":"enfers","nombre":1,"motif":"canon 4x15. Vaincu, il se redemande au tour suivant à délai 0 (règle propre) ; enterré par une clef à deux pièces du bien, il ne revient plus"}
```
**Portée** : *frappe sur Piper, Paige, Leo, un innocent — hors du manoir ou dedans ; verrou sur un état du bien (il occupe). Toute frappe le vainc, et il revient au tour suivant, sauf enterré. Se fige.*

### 🏢 `appartement`
```jsonl
{"camp":"cole","coup":"demander","id":"appartement","genre":"🏢","texte":"l'appartement de Cole — le trône au-dessus de la ville ; Phoebe y vit, la cour y monte, Leo n'y entre pas sans être appelé"}
{"camp":"arbitre","coup":"arbitrer","sur":"appartement","verdict":"accorde","arrive_tour":1,"lieu":"san-francisco","nombre":1,"motif":"canon 4x20 : c'est là que Cole tombe"}
```
**Portée** : *un lieu. Verrou sur une clef du bien qui atteint Phoebe (il faut y être appelé, ou y entrer de force — une clef avec Paige qui s'orbe) ; parade sur le retournement de Phoebe tant qu'elle y est. Le sort des trois s'y dit (4x20). Ne bouge pas.*

### 🩸 `demon-envoye`
```jsonl
{"camp":"cole","coup":"demander","id":"demon-envoye","genre":"🩸","texte":"un démon envoyé — ce que la Source envoie tuer un innocent que Phoebe a sauvé, pour qu'elle apprenne ; ou une sœur, hors de sa vue"}
{"camp":"arbitre","coup":"arbitrer","sur":"demon-envoye","verdict":"accorde","arrive_tour":2,"lieu":"enfers","nombre":1,"motif":"canon 4x20. Une frappe sur un innocent que Phoebe avait sauvé, si elle l'apprend, ramène son retournement à deux tours : c'est le prix de Cole, et il le sait"}
```
**Portée** : *frappe un innocent, Darryl, Leo hors du manoir, une sœur hors du manoir. Se fige, explose, meurt par potion. Se redemande, un tour.*

## 3. La Voyante — 🔵 six

### 🐍 `voyante`
```jsonl
{"camp":"voyante","coup":"demander","id":"voyante","genre":"🐍","texte":"la Voyante — elle a fait la Source dans Cole, elle a fait boire Phoebe ; elle veut l'enfant, et le trône après"}
{"camp":"arbitre","coup":"arbitrer","sur":"voyante","verdict":"accorde","arrive_tour":1,"lieu":"enfers","nombre":1,"motif":"canon 4x13-4x21"}
```
**Portée** : *répond à une question ; verrou sur une clef du bien ou de Cole qui repose sur ce qu'elle voit avant ; clef qui fait boire Phoebe (verrou sur son retournement, +2 tours par prise) ; retourne l'enfant en elle (4 tours, dès le tour 6, avec le consentement de Phoebe ou un rituel de la cour) ; aide Cole à détruire « l'homme en Cole » (deux tours au lieu de quatre) — si elle le veut ; retourne le prêtre noir et le Grimoire (2 tours). Ne frappe pas, ne se fige pas, aucune potion ; le sort des trois la vainc — et l'enfant en elle la consume au premier sort.*

### 🍷 `tonique`
```jsonl
{"camp":"voyante","coup":"demander","id":"tonique","genre":"🍷","texte":"le tonique — ce qu'elle fait boire à Phoebe « pour l'enfant » : chaque coupe tourne l'enfant au mal et tient la mère"}
{"camp":"arbitre","coup":"arbitrer","sur":"tonique","verdict":"accorde","arrive_tour":1,"lieu":"appartement","nombre":1,"motif":"canon 4x19-4x20"}
```
**Portée** : *clef qui fait boire Phoebe — verrou sur le retournement de Phoebe par le bien (+2 tours par prise, l'arbitre reporte) et clef sur « l'enfant est mûr » ; ne frappe pas. Tombe si Phoebe sait ce qu'il est (« ce que l'enfant est », Grams, les Fondateurs) ou si Paige l'appelle hors de ses mains.*

### 🍼 `l-heritier`
```jsonl
{"camp":"voyante","coup":"demander","id":"l-heritier","genre":"🍼","texte":"l'enfant de la Source, en Phoebe — il n'est à personne tant qu'il est en elle ; le tonique le tourne ; la Voyante sait le prendre"}
{"camp":"arbitre","coup":"arbitrer","sur":"l-heritier","verdict":"accorde","arrive_tour":1,"lieu":"phoebe","nombre":1,"motif":"canon 4x20-4x21. Tenu au grand livre par la Voyante parce que c'est elle qui le VISE — il suit le corps de Phoebe : il ne s'engage que par un retournement de la Voyante (elle le prend en elle, 4 tours, dès le tour 6), et il est aussi la marche de Cole « mon fils est né du mal ». Aucun camp ne le frappe"}
```
**Portée** : *ne s'engage que par le retournement de la Voyante (dès le tour 6, quand il est mûr : trois toniques bus ou six tours). Pris par elle : sa racine ; et le sort des trois dit sur elle le fait exploser avec elle. En Phoebe : sert la racine de Cole ; Phoebe revenue au bien l'emporte avec elle, et il n'est plus à personne du mal. Aucun camp ne le frappe.*

### 🕯️ `rituel-de-la-cour`
```jsonl
{"camp":"voyante","coup":"demander","id":"rituel-de-la-cour","genre":"🕯️","texte":"le rituel qui fait passer l'enfant d'un ventre à l'autre — devant la cour, avec le consentement de la mère ou ce qui en tient lieu"}
{"camp":"arbitre","coup":"arbitrer","sur":"rituel-de-la-cour","verdict":"accorde","arrive_tour":6,"lieu":"enfers","nombre":1,"motif":"canon 4x21 ; l'enfant est mûr au tour 6"}
```
**Portée** : *pièce qui s'engage AVEC la Voyante dans le retournement de l'enfant ; sans lui, refusé. Tombe si Phoebe refuse en connaissance (« ce que l'enfant est ») ou si Piper fige la cour pendant le rituel.*

### 👁️ `ce-qu-elle-voit`
```jsonl
{"camp":"voyante","coup":"demander","id":"ce-qu-elle-voit","genre":"👁️","texte":"ce que la Voyante voit — la chute de Cole, le jour où Phoebe doute, le sort dit : elle le sait avant"}
{"camp":"arbitre","coup":"arbitrer","sur":"ce-qu-elle-voit","verdict":"accorde","arrive_tour":1,"lieu":"enfers","nombre":1,"motif":"canon : sa vision, en pièce, pour qu'elle puisse la poser sans engager sa personne"}
```
**Portée** : *verrou sur une clef ou une frappe de Cole ou du bien (elle l'a vue venir, elle prévient qui elle veut) ; clef qui MONTRE à Phoebe un innocent tué par Cole (ramène le retournement du bien à deux tours — c'est sa trahison, 4x20) ; répond à une question. Ne frappe pas.*

### 🦇 (à demander) `reine-des-vampires`
Même pièce que celle que le bien peut demander : celui des deux qui la
demande le premier l'a, l'autre non. Délai 4. La Voyante s'en sert contre
Cole ; le bien aussi ; elle mord Paige dans les deux cas.

## 4. Les états proposés

**Le bien** (la racine au tour 1 ; un par tour ensuite) :
```jsonl
{"camp":"bien","coup":"viser","id":"b-racine","signe":"🕯️","texte":"Au vingtième tour, Phoebe est revenue de son plein gré, il n'y a plus de Source sur le trône des Enfers, et Piper, Phoebe et Paige sont vivantes, ensemble et du côté du bien"}
{"camp":"bien","coup":"viser","id":"b-phoebe","sert":"b-racine","signe":"💧","texte":"Phoebe est revenue au manoir de son plein gré, et le Pouvoir des Trois existe de nouveau"}
{"camp":"bien","coup":"viser","id":"b-innocent","sert":"b-phoebe","signe":"🙏","texte":"Un innocent que Cole voulait mort est vivant, et Phoebe sait qui l'a sauvé"}
{"camp":"bien","coup":"viser","id":"b-tonique","sert":"b-phoebe","signe":"🚫","texte":"Phoebe ne boit plus le tonique, parce qu'elle sait ce qu'il fait à l'enfant"}
{"camp":"bien","coup":"viser","id":"b-lazare","sert":"b-racine","signe":"⚰️","texte":"Lazare est enterré"}
{"camp":"bien","coup":"viser","id":"b-cole","sert":"b-racine","signe":"🔱","texte":"Cole, la Source, est vaincu par le sort des trois"}
{"camp":"bien","coup":"viser","id":"b-enfant","sert":"b-racine","signe":"🍼","texte":"L'enfant n'est à personne du mal : la Voyante ne l'a pas pris"}
{"camp":"bien","coup":"viser","id":"b-trone","sert":"b-racine","signe":"🪑","texte":"Le trône des Enfers est vide : personne n'a été couronné après Cole"}
```

**Cole** (l'IA pose les siens ; pour l'arbitre et Radio) :
```jsonl
{"camp":"cole","coup":"viser","id":"c-racine","signe":"👑","texte":"Au vingtième tour, je suis assis sur le trône des Enfers, Phoebe règne à mes côtés, et mon fils est à naître ou né du mal"}
{"camp":"cole","coup":"viser","id":"c-reine","sert":"c-racine","signe":"💍","texte":"Phoebe règne à mes côtés, et elle l'a choisi"}
{"camp":"cole","coup":"viser","id":"c-soeurs","sert":"c-racine","signe":"🚪","texte":"Piper et Paige n'atteignent plus Phoebe : le manoir et l'appartement sont deux mondes"}
{"camp":"cole","coup":"viser","id":"c-homme","sert":"c-racine","signe":"🔥","texte":"L'homme en moi s'est tu : l'essence règne seule"}
{"camp":"cole","coup":"viser","id":"c-fils","sert":"c-racine","signe":"🍼","texte":"Mon fils naît du mal, en Phoebe, et de personne d'autre"}
```

**La Voyante** :
```jsonl
{"camp":"voyante","coup":"viser","id":"v-racine","signe":"🐍","texte":"Au vingtième tour, l'enfant de la Source est en moi, et c'est moi qui suis assise sur le trône des Enfers"}
{"camp":"voyante","coup":"viser","id":"v-mur","sert":"v-racine","signe":"🍷","texte":"L'enfant est mûr : Phoebe a bu trois fois, ou six jours ont passé"}
{"camp":"voyante","coup":"viser","id":"v-enfant","sert":"v-racine","signe":"🍼","texte":"L'enfant est en moi"}
{"camp":"voyante","coup":"viser","id":"v-cole","sert":"v-racine","signe":"🕳️","texte":"Cole est tombé, et je n'y suis pour rien qu'on puisse dire"}
{"camp":"voyante","coup":"viser","id":"v-couronne","sert":"v-racine","signe":"📕","texte":"Le prêtre noir m'a couronnée avec le Grimoire, devant la cour"}
```

## 5. Le calendrier et le compte des mains

| Tour | Arrive au bien | Arrive à Cole | Arrive à la Voyante | Ce qui se ferme |
|---|---|---|---|---|
| 1 | piper, paige, leo, livre, sort-des-trois (inerte), darryl, l-homme-en-cole, manoir | cole-source, phoebe, la-cour, pretre-noir, grimoire, appartement | voyante, tonique, l-heritier, ce-qu-elle-voit | **c-racine constatée VRAIE** |
| 2 | potion, grams | demon-envoye | — | — |
| 3 | fondateurs | lazare | — | — |
| 4 | *innocent-1* (demandé à l'ouverture, daté par l'arbitre) | — | — | — |
| 5 | — | — | — | un retournement de Phoebe posé au 1 atterrit au plus tôt ici |
| 6 | — | — | rituel-de-la-cour | l'enfant est mûr : la Voyante peut poser |
| 8 | — | — | — | la reine des vampires, si demandée au 4, arrive |
| 10 | *innocent-2* | — | — | — |
| 20 | — | — | — | fin : trois racines constatées |

**Les innocents sont des pièces datées par l'arbitre** : le bien les demande
à l'ouverture (l'arbitre ne demande pas, il arbitre), et l'arbitre les
accorde à leur date (`innocent-1` au 4, `innocent-2` au 10), avec cette
portée : *un mortel que Cole veut mort et que Phoebe connaît. Le bien
le sauve (clef avec Darryl, Paige, Leo) ; Cole ou son démon le frappe ; s'il
meurt après avoir été sauvé et que Phoebe l'apprend (une clef de la Voyante,
ou une pièce du bien qui le lui dit), le retournement de Phoebe passe à deux
tours. Ne frappe pas, ne pare pas.* C'est la seule entorse au « pas de front
des innocents » de Charmed 2, et elle est le moteur canonique du retour de
Phoebe.

**Onze pièces au bien, huit à Cole, six à la Voyante.** Le bien a le nombre ;
Cole a le trône et l'initiative ; la Voyante a le temps (rien à défendre
avant le 6) et l'information. Le bien n'a AUCUNE frappe utile avant le retour
de Phoebe — c'est voulu.

## 6. Les lignes de jeu qu'on voit d'ici

**Le bien.** Tour 1 : racine. Tour 2 : retourner Phoebe (Piper, Paige, Leo
— trois pièces, ou deux ; l'arbitre veut au moins Leo, seul canal). Arrive 3,
atterrit au passage du 5 si rien ne le repousse. Cole va reporter (le
tonique, +2 par prise ; la cour ; sa parole) : compter six à huit tours. Le
bien doit donc en parallèle **fermer le tonique** (Grams ou les Fondateurs
disent ce que l'enfant est → `b-tonique`) et **sauver l'innocent du 4**, que
Cole voudra mort. Si Cole le tue après, Phoebe revient en deux tours. Tour
8-10 : Phoebe revenue, le sort des trois sur Cole à l'appartement, la Voyante
ne pare pas si l'enfant n'est pas encore à elle… ou pare parce qu'elle en a
besoin vivant jusqu'au 6. Puis l'enfant : la Voyante le retourne dès le 6 ;
`ce-que-l-enfant-est` fait tomber le rituel si Phoebe refuse.

**Cole.** Garder Phoebe : le tonique (mais c'est la pièce de la Voyante — il
doit lui demander), la cour à l'appartement, sa parole. Tuer « l'homme en
Cole » (quatre tours, deux avec la Voyante — elle voudra bien : un Cole sans
homme tue les innocents, ce qui fait revenir Phoebe, ce qui l'arrange). Tenir
Piper et Paige loin : Lazare, la cour, un démon envoyé — hors de la vue de
Phoebe. Sa faute possible : tuer l'innocent lui-même.

**La Voyante.** Faire boire trois fois avant le 6 (trois clefs). Poser le
retournement de l'enfant au 6 avec le rituel ; il atterrit au passage du 9.
Pendant ce temps, laisser le bien travailler Cole ; MONTRER l'innocent mort
à Phoebe le jour où elle a intérêt à ce que Cole tombe ; ne rien parer sur
Cole après le 9. Retourner le prêtre noir et le Grimoire (deux tours
chacun) pour le couronnement. Sa faute possible : prendre l'enfant trop tôt
et devenir la cible du sort des trois avant que Cole soit tombé.
