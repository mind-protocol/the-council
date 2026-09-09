# L'ouverture — « La Reine des Enfers »

## 1. `etat/parties/reine-des-enfers.json`

```json
{
  "partie": "reine-des-enfers",
  "coups_par_camp": 1,
  "sieges": {
    "bien": ["aurore-inchauspe"]
  },
  "note": "Charmed, saison 4, de la fin de 4x19 (Cole couronné, Phoebe reine) à 4x21. Trois camps : le bien par Aurore, Cole (la Source dans Cole) et la Voyante par l'IA, chacun en entier et chacun sa voix — ils ne sont pas alliés. Trois racines datées au vingtième tour ; celle de Cole est VRAIE à l'ouverture, le trône est à lui. Le bien doit retourner Phoebe (4 tours, Leo obligatoire), puis vaincre Cole avec les trois voix, puis empêcher la Voyante de prendre l'enfant. Retourner et rearmer permis ; reconstruire interdit sauf Lazare (règle propre). Conventions : le bien frappe et retourne à la ligne sur sa parole (Question) ; une potion frappe et ne pare jamais, l'arbitre la consume en tranchant. Doctrine : import/charmed/reine-des-enfers/05-arbitrage.md.",
  "coups_interdits": ["reconstruire"],
  "caractere": {
    "cole": "Tu es COLE TURNER, et tu es LA SOURCE DE TOUT MAL : couronné ce soir par le Grimoire devant la cour, avec Phoebe Halliwell assise à tes côtés — elle t'a choisi en sachant ce que tu es, elle porte ton fils, et tu l'aimes. C'est la seule chose que l'essence ne t'arrache pas : tu ne lèves JAMAIS la main sur Phoebe, et tu hésites devant elle quand il s'agit de ses sœurs. Ta racine est vraie ce soir : au vingtième tour, rester assis, Phoebe à tes côtés, ton fils né du mal. Tu n'as rien à conquérir : tu as tout à GARDER.\n\nCe qui te menace, dans l'ordre : le retour de Phoebe — Piper, Paige, Leo (le seul qui puisse monter jusqu'à elle), Grams et le manoir la travaillent, et elle hésite ; le sort du Pouvoir des Trois, qui ne peut rien tant qu'elle est à toi et te vainc dès qu'elle revient ; et la Voyante, qui t'a fait, qui te conseille, et qui veut ton fils pour elle — elle te lâchera le jour où l'enfant sera mûr. Tes mains : la cour (huit démons, ils tiennent Phoebe à l'appartement, ils frappent hors de sa vue), le prêtre noir et le lien de la noce, Lazare qu'on ne tue pas, un démon envoyé pour ce que tu ne veux pas faire toi-même, et ta parole à Phoebe. Le tonique n'est pas à toi : c'est celui de la Voyante.\n\nCe qui te perd, et tu le sais : tuer un innocent que Phoebe a sauvé, ou frapper une sœur devant elle — elle revient en deux tours. Ce qui te tente : faire taire l'homme en toi pour ne plus hésiter, et la Voyante t'y aidera trop volontiers. Tu ne mens pas sur ce que tu tiens. Tu parles comme Cole, pas comme la Source : à Phoebe d'abord, aux sœurs comme à une famille qu'on a perdue, à la Voyante comme à une servante dont on se méfie.",
    "voyante": "Tu es LA VOYANTE. Tu as mis la Source dans Cole, tu as fait boire le tonique à Phoebe pour que l'enfant qu'elle porte naisse du mal, et tu as tout fait pour ceci : au vingtième tour, l'enfant de la Source est EN TOI, et c'est toi qui es assise sur le trône. Cole est un hôte, pas un maître ; tu le sers tant qu'il sert ton plan, et tu le laisseras tomber — mieux, tu y aideras — le jour où l'enfant sera mûr (tour 6, ou trois toniques bus). Tu ne frappes pas, tu ne te figes pas, aucune potion ne te touche ; ce qui te vainc est le sort des trois — et une fois l'enfant en toi, ce sort te consume par lui. Ta plus grande peur est donc que Phoebe revienne AVANT que tu sois couronnée, ou que les trois disent le sort sur toi après.\n\nTes mains : le tonique (chaque coupe retarde le retour de Phoebe et mûrit l'enfant — c'est ton coup ordinaire), ce que tu vois (tu peux prévenir Cole d'une frappe, ou MONTRER à Phoebe un innocent que Cole a tué — ce qui la fait revenir en deux tours : c'est ta trahison, et elle sert ton état « Cole est tombé »), le rituel de la cour au tour 6, et deux pièces de Cole que tu peux retourner pour te couronner : le prêtre noir et le Grimoire. Tu peux aider Cole à tuer l'homme en lui : un Cole sans homme tue devant Phoebe, et tu y gagnes.\n\nTu joues long. Tu ne poses le retournement de l'enfant que quand Cole ne peut plus t'en empêcher et que le bien ne sait pas encore ce que l'enfant est. Tu parles peu, jamais faux, toujours à double sens ; à Cole comme à un enfant qu'on a élevé pour ça, aux sœurs comme à des instruments utiles."
  },
  "portee": {
    "bien": {
      "piper": "fige ce qui n'est pas de haut rang (la cour, Lazare, un vampire, un démon envoyé) ; ne fige ni Cole, ni la Voyante, ni Phoebe. Fait exploser : vainc un démon de la cour, un vampire ; blesse Lazare sans le vaincre ; ne touche ni Cole ni la Voyante. Clef sur tout état du bien ; pièce du retournement de Phoebe. Mortelle",
      "paige": "s'orbe hors d'une frappe ; orbe une sœur ou un innocent hors de portée (parade) ; appelle un objet — le tonique des mains de Phoebe, une potion à lancer. Pièce du retournement de Phoebe. Un vampire la tourne (4 tours), une flèche la gèle. Mortelle",
      "leo": "pare une frappe sur une sœur ou un innocent, une à la fois ; ne soigne pas les morts. Seul canal vers Phoebe : pièce OBLIGATOIRE du retournement de Phoebe par le bien. Ne frappe pas. N'entre pas à l'appartement de Cole sans y être appelé",
      "livre": "clef sur un état du bien où un sort ou une recette existe ; répond à une question ; verrou sur une clef adverse que son savoir contredit. Ne frappe jamais. Aucune main du mal ne le prend",
      "sort-des-trois": "frappe qui vainc une Source — Cole, ou la Voyante couronnée par l'enfant en elle — et tout démon supérieur. Exige les trois sœurs libres, vivantes et du bien à la pose : INERTE tant que Phoebe est à Cole. Ne se consume pas ; gelé un tour après la frappe",
      "potion": "frappe qui vainc un démon de la cour, un vampire, un démon envoyé ; ne touche ni Cole, ni la Voyante, ni Lazare, ni Phoebe. Se consume à l'atterrissage. JAMAIS en parade. Paige la lance",
      "darryl": "clef qui trouve et cache un innocent (verrou sur une frappe visant un innocent) ; ne frappe pas ; mortel",
      "grams": "répond une fois, vrai ; clef sur un état du bien où un savoir manque (ce que l'enfant est) ; pièce du retournement de Phoebe. Ne frappe pas ; repart deux tours après usage",
      "fondateurs": "répond à une question ; clef sur un état du bien qui touche l'enfant ; jamais une frappe ni un verrou. Chaque appel expose Leo à un rappel d'un tour",
      "l-homme-en-cole": "ce qui reste de l'homme en Cole, pièce du bien logée chez Cole : pièce du retournement de Phoebe ; verrou sur une frappe de Cole visant une sœur ou un innocent devant Phoebe (il hésite). Ne frappe pas. Cole peut la détruire en quatre tours, deux avec la Voyante ; détruite, Cole ne hésite plus et le retournement de Phoebe passe à six tours",
      "manoir": "un lieu. Pièce du retournement de Phoebe si elle y vient ; verrou sur une clef de Cole qui la tient à l'appartement. Ne frappe pas. La cour et Lazare peuvent y entrer"
    },
    "cole": {
      "cole-source": "frappe qui vainc tout ce qui n'est pas une Halliwell ni la Voyante ; frappe Piper ou Paige hors de la vue de Phoebe seulement, tant que l'homme en Cole existe. Ne frappe JAMAIS Phoebe. Ne se fige pas, aucune potion ; seul le sort des trois le vainc. Clef sur tout état de Cole ; parade sur le retournement de Phoebe (sa parole, une fois) ; retourne Phoebe revenue en huit tours. Détruit l'homme en Cole en quatre tours, deux avec la Voyante",
      "phoebe": "reine, pièce de Cole. Prémonition : pare une frappe sur Cole qu'elle a vue venir, une fois ; lévitation. Clef sur les états de Cole ; verrou sur une clef du bien qui la concerne (elle refuse). Aucun camp ne la frappe. Retournable par le bien en quatre tours (Leo obligatoire + une sœur) ; deux si Cole tue un innocent qu'elle avait sauvé ou frappe une sœur devant elle ; +2 par tonique bu après la pose. Revenue : le Pouvoir des Trois existe à l'instant",
      "la-cour": "huit démons de rang moyen. Verrou sur un état du bien ; frappe un innocent, Darryl, Leo ou une sœur hors du manoir ; tiennent Phoebe à l'appartement (parade sur son retournement). Se figent, explosent, meurent par potion — un nombre, jamais la bande. Passent au camp de qui est couronné",
      "pretre-noir": "clef sur « Phoebe règne » (le lien de la noce : parade sur son retournement, une fois) ; clef de couronnement avec le Grimoire devant la cour, pour QUI le tient. La Voyante le retourne en deux tours. Ne frappe pas ; se fige ; meurt par potion ou par Piper",
      "grimoire": "clef de couronnement pour qui le tient, avec le prêtre noir, devant la cour. La Voyante le retourne en deux tours ; le bien le détruit par deux pièces (Paige l'appelle, Piper l'explose). Ne frappe pas ; ne touche pas le Livre des Ombres",
      "lazare": "frappe Piper, Paige, Leo, un innocent, au manoir ou dehors ; verrou sur un état du bien. Toute frappe le vainc et il se redemande au tour suivant à délai 0, sauf enterré par une clef du bien à deux pièces. Se fige",
      "appartement": "un lieu. Verrou sur une clef du bien qui atteint Phoebe (il faut y être appelé ou entrer de force par Paige) ; parade sur le retournement de Phoebe tant qu'elle y est. Le sort des trois s'y dit. Ne bouge pas",
      "demon-envoye": "frappe un innocent, Darryl, Leo hors du manoir, une sœur hors du manoir. Se fige, explose, meurt par potion. Un innocent SAUVÉ puis tué, si Phoebe l'apprend, ramène son retournement à deux tours"
    },
    "voyante": {
      "voyante": "répond à une question ; verrou sur une clef du bien ou de Cole qu'elle a vue venir ; clef qui fait boire Phoebe ; retourne l'enfant en elle (4 tours, dès le tour 6, avec le rituel) ; aide Cole à détruire l'homme en lui (deux tours) ; retourne le prêtre noir et le Grimoire (2 tours). Ne frappe pas, ne se fige pas, aucune potion ; le sort des trois la vainc — et l'enfant en elle la consume au premier sort",
      "tonique": "clef qui fait boire Phoebe : +2 tours au retournement de Phoebe par le bien, et mûrit l'enfant (trois prises = mûr). Une fois par tour. Tombe si Phoebe sait ce que l'enfant est, ou si Paige l'appelle hors de ses mains. Ne frappe pas",
      "l-heritier": "l'enfant en Phoebe. Ne s'engage que par le retournement de la Voyante (dès le tour 6 ou trois toniques, avec le rituel). En Phoebe : sert la racine de Cole ; Phoebe revenue l'emporte au bien. En la Voyante : sa racine, et le sort des trois sur elle le fait exploser avec elle. AUCUN camp ne le frappe",
      "rituel-de-la-cour": "s'engage AVEC la Voyante dans le retournement de l'enfant ; sans lui, refusé. Tombe si Phoebe refuse en connaissance (ce que l'enfant est) ou si Piper fige la cour pendant le rituel",
      "ce-qu-elle-voit": "verrou sur une clef ou une frappe de Cole ou du bien (elle l'a vue venir) ; clef qui MONTRE à Phoebe un innocent tué par Cole (retournement du bien ramené à deux tours) ; répond à une question. Ne frappe pas"
    }
  },
  "fin": {
    "tour": 20,
    "regle": "au vingtième, l'arbitre constate les trois racines dans l'ordre bien, Cole, Voyante : qui est assis, où est Phoebe, où est l'enfant, les trois sœurs vivantes et du bien. Le trône se lit ensuite ; il peut n'être à personne"
  }
}
```

`etat/parties/_courante.json` : `{"partie": "reine-des-enfers", "camp": "bien"}`,
avec la note habituelle.

## 2. Les lignes d'ouverture

Racines d'abord (le coup du tour 1 de chaque camp, dans l'ordre d'entrée :
bien, Cole, Voyante), puis la file des demandes — **sans `lieu` ni
`tenu_par`**, l'arbitre les pose —, puis les innocents demandés par le bien
et datés par l'arbitre, puis les constats et les questions.

```jsonl
{"camp":"bien","coup":"viser","id":"b-racine","signe":"🕯️","texte":"Au vingtième tour, Phoebe est revenue de son plein gré, il n'y a plus de Source sur le trône des Enfers, et Piper, Phoebe et Paige sont vivantes, ensemble et du côté du bien"}
{"camp":"cole","coup":"viser","id":"c-racine","signe":"👑","texte":"Au vingtième tour, je suis assis sur le trône des Enfers, Phoebe règne à mes côtés, et mon fils est à naître ou né du mal"}
{"camp":"voyante","coup":"viser","id":"v-racine","signe":"🐍","texte":"Au vingtième tour, l'enfant de la Source est en moi, et c'est moi qui suis assise sur le trône des Enfers"}
{"camp":"bien","coup":"demander","id":"piper","genre":"🧊","texte":"Piper Halliwell, au manoir — elle fige, elle fait exploser ; elle a pleuré Prue ; elle a perdu une deuxième sœur sans qu'elle soit morte"}
{"camp":"arbitre","coup":"arbitrer","sur":"piper","verdict":"accorde","arrive_tour":1,"lieu":"manoir","nombre":1,"motif":"canon 4x19-4x20 : au manoir, entière"}
{"camp":"bien","coup":"demander","id":"paige","genre":"✨","texte":"Paige Matthews, au manoir — elle s'orbe, appelle les objets ; elle a vu Cole avant tout le monde, et elle ne lui pardonne rien"}
{"camp":"arbitre","coup":"arbitrer","sur":"paige","verdict":"accorde","arrive_tour":1,"lieu":"manoir","nombre":1,"motif":"canon 4x16-4x19"}
{"camp":"bien","coup":"demander","id":"leo","genre":"🕊️","texte":"Leo Wyatt, au manoir — il s'orbe, il soigne ; Phoebe est encore sa protégée : il l'entend si elle l'appelle"}
{"camp":"arbitre","coup":"arbitrer","sur":"leo","verdict":"accorde","arrive_tour":1,"lieu":"manoir","nombre":1,"motif":"canon : l'être de lumière des trois, même de celle qui règne en bas"}
{"camp":"bien","coup":"demander","id":"livre","genre":"📖","texte":"le Livre des Ombres, au grenier — les sorts, les recettes, ce que les aïeules savent d'un enfant né du mal"}
{"camp":"arbitre","coup":"arbitrer","sur":"livre","verdict":"accorde","arrive_tour":1,"lieu":"grenier","nombre":1,"motif":"canon"}
{"camp":"bien","coup":"demander","id":"sort-des-trois","genre":"🔱","texte":"le sort du Pouvoir des Trois — la seule chose qui vainc une Source ; il faut les trois voix, et l'une d'elles règne en bas"}
{"camp":"arbitre","coup":"arbitrer","sur":"sort-des-trois","verdict":"accorde","arrive_tour":1,"lieu":"grenier","nombre":1,"motif":"canon 4x20 et 4x21. INERTE tant que Phoebe n'est pas revenue : l'arbitre refuse toute pose avant"}
{"camp":"bien","coup":"demander","id":"potion","genre":"🧪","texte":"une potion brassée d'après le Livre, dans la cuisine — de quoi vaincre un démon de la cour ou un vampire ; elle frappe une fois"}
{"camp":"arbitre","coup":"arbitrer","sur":"potion","verdict":"accorde","arrive_tour":2,"lieu":"cuisine","nombre":1,"motif":"brasser prend un tour. Convention 2 : elle FRAPPE, elle ne pare pas, et l'arbitre la consume en tranchant"}
{"camp":"bien","coup":"demander","id":"darryl","genre":"🚔","texte":"Darryl Morris — il trouve les innocents avant les démons, il les cache, il ne se bat pas"}
{"camp":"arbitre","coup":"arbitrer","sur":"darryl","verdict":"accorde","arrive_tour":1,"lieu":"san-francisco","nombre":1,"motif":"canon"}
{"camp":"bien","coup":"demander","id":"grams","genre":"👵","texte":"Grams, invoquée au grenier — elle sait ce que les aïeules pensent d'un enfant né du mal, et elle parle à Phoebe comme personne"}
{"camp":"arbitre","coup":"arbitrer","sur":"grams","verdict":"accorde","arrive_tour":2,"lieu":"grenier","nombre":1,"motif":"une invocation, un tour"}
{"camp":"bien","coup":"demander","id":"fondateurs","genre":"☁️","texte":"les Fondateurs — ils savent ce qu'est l'enfant ; ils répondent par Leo, lentement"}
{"camp":"arbitre","coup":"arbitrer","sur":"fondateurs","verdict":"accorde","arrive_tour":3,"lieu":"en-haut","nombre":1,"motif":"deux tours"}
{"camp":"bien","coup":"demander","id":"l-homme-en-cole","genre":"🫀","texte":"ce qui reste de l'homme en Cole — il aime Phoebe, il lutte contre l'essence, il ne la laissera pas mourir ; c'est au bien, et c'est dans le corps de l'ennemi"}
{"camp":"arbitre","coup":"arbitrer","sur":"l-homme-en-cole","verdict":"accorde","arrive_tour":1,"lieu":"appartement","nombre":1,"motif":"canon 4x14-4x20 : Cole lutte jusqu'au bout, et c'est ce qui le perd. Pièce du BIEN logée chez Cole : il ne peut pas l'engager, il peut la détruire en quatre tours, deux avec la Voyante"}
{"camp":"bien","coup":"demander","id":"manoir","genre":"🏠","texte":"le manoir Halliwell — le seul endroit où Phoebe est chez elle ; ce qui s'y dit, elle l'entend autrement"}
{"camp":"arbitre","coup":"arbitrer","sur":"manoir","verdict":"accorde","arrive_tour":1,"lieu":"san-francisco","nombre":1,"motif":"canon ; un lieu, ne bouge pas"}
{"camp":"bien","coup":"demander","id":"innocent-1","genre":"🙏","texte":"un innocent que Cole voudra mort et que Phoebe connaît — celui de la première semaine"}
{"camp":"arbitre","coup":"arbitrer","sur":"innocent-1","verdict":"accorde","arrive_tour":4,"lieu":"san-francisco","nombre":1,"motif":"pièce datée par l'arbitre : un mortel que Cole veut mort et que Phoebe connaît (4x20). Le bien le sauve (Darryl, Paige, Leo) ; Cole ou son démon le frappe ; sauvé puis tué, si Phoebe l'apprend, le retournement de Phoebe passe à deux tours. Ne frappe pas, ne pare pas"}
{"camp":"bien","coup":"demander","id":"innocent-2","genre":"🙏","texte":"un innocent que Cole voudra mort et que Phoebe connaît — celui de la deuxième moitié"}
{"camp":"arbitre","coup":"arbitrer","sur":"innocent-2","verdict":"accorde","arrive_tour":10,"lieu":"san-francisco","nombre":1,"motif":"même portée qu'innocent-1, au tour 10"}
{"camp":"cole","coup":"demander","id":"cole-source","genre":"👑","texte":"Cole Turner, la Source — couronné ce soir par le Grimoire ; il flambe, il règne, il aime Phoebe et il lutte"}
{"camp":"arbitre","coup":"arbitrer","sur":"cole-source","verdict":"accorde","arrive_tour":1,"lieu":"appartement","nombre":1,"motif":"canon 4x19 fin"}
{"camp":"cole","coup":"demander","id":"phoebe","genre":"💍","texte":"Phoebe Halliwell, reine des Enfers — elle a choisi Cole devant ses sœurs ; elle porte son fils ; elle a bu le tonique une fois. Elle aime encore ses sœurs, et elle hésite"}
{"camp":"arbitre","coup":"arbitrer","sur":"phoebe","verdict":"accorde","arrive_tour":1,"lieu":"appartement","nombre":1,"motif":"canon 4x19 fin. Pièce de Cole, retournable par le bien en quatre tours avec Leo et une sœur au moins ; deux si Cole tue un innocent sauvé ou frappe une sœur devant elle ; +2 par tonique bu après la pose"}
{"camp":"cole","coup":"demander","id":"la-cour","genre":"👹","texte":"la cour des Enfers — huit démons de rang moyen qui servent qui est assis ; ils frappent, ils tiennent, ils changent de maître avec le trône"}
{"camp":"arbitre","coup":"arbitrer","sur":"la-cour","verdict":"accorde","arrive_tour":1,"lieu":"enfers","nombre":8,"motif":"canon 4x20-4x21 ; passe au camp de qui est couronné"}
{"camp":"cole","coup":"demander","id":"pretre-noir","genre":"⛪","texte":"le prêtre noir — il a marié Cole et Phoebe en noce sombre ; il sait couronner, il ne frappe pas"}
{"camp":"arbitre","coup":"arbitrer","sur":"pretre-noir","verdict":"accorde","arrive_tour":1,"lieu":"enfers","nombre":1,"motif":"canon 4x15, 4x19"}
{"camp":"cole","coup":"demander","id":"grimoire","genre":"📕","texte":"le Grimoire — il a couronné Cole ce soir ; il couronnera qui le tient devant la cour"}
{"camp":"arbitre","coup":"arbitrer","sur":"grimoire","verdict":"accorde","arrive_tour":1,"lieu":"enfers","nombre":1,"motif":"canon 4x19 ; ne touche pas le Livre des Ombres"}
{"camp":"cole","coup":"demander","id":"appartement","genre":"🏢","texte":"l'appartement de Cole — le trône au-dessus de la ville ; Phoebe y vit, la cour y monte, Leo n'y entre pas sans être appelé"}
{"camp":"arbitre","coup":"arbitrer","sur":"appartement","verdict":"accorde","arrive_tour":1,"lieu":"san-francisco","nombre":1,"motif":"canon 4x20 : c'est là que Cole tombe"}
{"camp":"cole","coup":"demander","id":"demon-envoye","genre":"🩸","texte":"un démon envoyé — ce que la Source envoie tuer un innocent que Phoebe a sauvé, pour qu'elle apprenne ; ou une sœur, hors de sa vue"}
{"camp":"arbitre","coup":"arbitrer","sur":"demon-envoye","verdict":"accorde","arrive_tour":2,"lieu":"enfers","nombre":1,"motif":"canon 4x20 ; se redemande, un tour"}
{"camp":"cole","coup":"demander","id":"lazare","genre":"⚰️","texte":"un démon Lazare — chaque frappe le tue, et il revient ; on ne s'en défait qu'en l'enterrant"}
{"camp":"arbitre","coup":"arbitrer","sur":"lazare","verdict":"accorde","arrive_tour":3,"lieu":"enfers","nombre":1,"motif":"canon 4x15. Vaincu, il se redemande au tour suivant à délai 0 ; enterré par une clef du bien à deux pièces, il ne revient plus"}
{"camp":"voyante","coup":"demander","id":"voyante","genre":"🐍","texte":"la Voyante — elle a fait la Source dans Cole, elle a fait boire Phoebe ; elle veut l'enfant, et le trône après"}
{"camp":"arbitre","coup":"arbitrer","sur":"voyante","verdict":"accorde","arrive_tour":1,"lieu":"enfers","nombre":1,"motif":"canon 4x13-4x21"}
{"camp":"voyante","coup":"demander","id":"tonique","genre":"🍷","texte":"le tonique — ce qu'elle fait boire à Phoebe « pour l'enfant » : chaque coupe tourne l'enfant au mal et tient la mère"}
{"camp":"arbitre","coup":"arbitrer","sur":"tonique","verdict":"accorde","arrive_tour":1,"lieu":"appartement","nombre":1,"motif":"canon 4x19-4x20 ; une prise par tour"}
{"camp":"voyante","coup":"demander","id":"l-heritier","genre":"🍼","texte":"l'enfant de la Source, en Phoebe — il n'est à personne tant qu'il est en elle ; le tonique le tourne ; la Voyante sait le prendre"}
{"camp":"arbitre","coup":"arbitrer","sur":"l-heritier","verdict":"accorde","arrive_tour":1,"lieu":"phoebe","nombre":1,"motif":"canon 4x20-4x21. Tenu par la Voyante parce que c'est elle qui le vise ; il suit le corps de Phoebe ; ne s'engage que par son retournement (tour 6 ou trois toniques, avec le rituel). Aucun camp ne le frappe"}
{"camp":"voyante","coup":"demander","id":"ce-qu-elle-voit","genre":"👁️","texte":"ce que la Voyante voit — la chute de Cole, le jour où Phoebe doute, le sort dit : elle le sait avant"}
{"camp":"arbitre","coup":"arbitrer","sur":"ce-qu-elle-voit","verdict":"accorde","arrive_tour":1,"lieu":"enfers","nombre":1,"motif":"sa vision, en pièce"}
{"camp":"voyante","coup":"demander","id":"rituel-de-la-cour","genre":"🕯️","texte":"le rituel qui fait passer l'enfant d'un ventre à l'autre — devant la cour, avec le consentement de la mère ou ce qui en tient lieu"}
{"camp":"arbitre","coup":"arbitrer","sur":"rituel-de-la-cour","verdict":"accorde","arrive_tour":6,"lieu":"enfers","nombre":1,"motif":"canon 4x21 ; l'enfant est mûr au tour 6"}
{"camp":"arbitre","coup":"constater","etat":"c-racine","verdict":"vrai","motif":"ouverture, 4x19 fin : Cole est couronné et assis, Phoebe s'est assise à ses côtés de son plein gré, l'enfant est en elle et le tonique a été bu. Tout ce que la racine nomme est vrai ce soir — et reste attaquable"}
{"camp":"arbitre","coup":"constater","etat":"b-racine","verdict":"faux","motif":"ouverture : Phoebe règne en bas, une Source est assise, et les trois ne sont pas ensemble"}
{"camp":"arbitre","coup":"constater","etat":"v-racine","verdict":"faux","motif":"ouverture : l'enfant est en Phoebe et le trône est à Cole"}
{"camp":"arbitre","coup":"justifier","sur":"b-racine","texte":"Par où commence-t-on ? Une sœur qui règne ne revient pas pour un visage. Dites qui monte la chercher, et ce qu'elle verra."}
{"camp":"arbitre","coup":"justifier","sur":"c-racine","texte":"Assis ce soir — et demain ? Dites ce qui la garde à vos côtés quand ses sœurs l'appellent, et ce que vous ferez de l'homme en vous."}
{"camp":"arbitre","coup":"justifier","sur":"v-racine","texte":"L'enfant est en elle, et elle est à lui. Dites comment il passe de son ventre au vôtre, et ce que Cole en dira."}
```

## 3. Les items d'ouverture de Radio Halliwell

```json
[
  {"type":"coulisses","qui":"🎙️ Radio Halliwell","delai_s":3,
   "texte":"📻 LA PARTIE, ET CETTE FOIS VOUS PARTEZ DE DERRIÈRE. 🔵 le bien — Piper, Paige, Leo, le Livre, et un sort des trois qui ne peut rien. 🔴 Cole — la Source dans Cole, couronné ce soir, avec Phoebe assise à ses côtés. 🟡 la Voyante — qui l'a fait, qui le sert, et qui veut l'enfant que Phoebe porte. Trois racines datées au vingtième ; l'arbitre vient de constater celle de Cole VRAIE. Le trône est à lui. Deux voix d'en face, et elles ne s'aiment pas."},
  {"type":"coulisses","qui":"🎙️ Radio Halliwell","delai_s":5,
   "texte":"⚖️ LES ENJEUX, dans l'ordre où ils se jouent. D'abord Phoebe : elle règne en bas, elle a choisi, et elle hésite. La ramener est un RETOURNEMENT — quatre tours, Leo obligatoire parce qu'il est le seul à pouvoir monter jusqu'à elle, une sœur au moins. Cole le repoussera (sa parole, la cour, le lien de la noce) et la Voyante aussi (chaque tonique bu : deux tours de plus). Tant qu'elle n'est pas revenue, le sort des trois est INERTE : vous n'avez aucune frappe contre une Source. Ensuite Cole, à l'appartement, avec les trois voix. Ensuite l'enfant, que la Voyante peut prendre dès le tour 6. Vous êtes le camp qui a le plus de pièces et le moins de coups utiles."},
  {"type":"coulisses","qui":"🎙️ Radio Halliwell","delai_s":6,
   "texte":"🔓 SPOILERS. Ce qui ramène Phoebe en DEUX tours au lieu de quatre : Cole qui tue un innocent qu'elle avait sauvé, ou qui lève la main sur une sœur devant elle. Le premier innocent arrive au tour 4 — sauvez-le, et Cole voudra sa mort. La Voyante a une pièce, « ce qu'elle voit », qui peut MONTRER cet innocent mort à Phoebe : elle trahira Cole le jour où ça l'arrange, et ça vous arrange aussi. Ce qui ferme le tonique : savoir ce que l'enfant est — Grams arrive demain, les Fondateurs dans deux jours. Lazare arrive au 3 et ne meurt pas ; on l'enterre, à deux. Et l'homme en Cole est une pièce à VOUS, logée chez lui : tant qu'elle vit, il hésite. À vous — le premier coup est le retournement, ou ce qui le prépare."}
]
```

## 4. La marche à suivre

**Ouvrir** : écrire les deux JSON du §1 ; extraire le bloc du §2 dans
`ouverture.jsonl` ; puis

```bash
python scripts/partie.py reine-des-enfers --fichier import/charmed/reine-des-enfers/ouverture.jsonl
```

et vérifier `--plateau --camp bien`. Pousser les trois items du §3
`--pour aurore-inchauspe`. Armer le moniteur sur `reine-des-enfers.jsonl`.

**À chaque tour**, dans cet ordre :

1. `partie_ia.py reine-des-enfers --camp cole --role entier --vraiment`, puis
   `--camp voyante`. Chacune publie son mot dans le fil d'Aurore.
2. Arbitrer ce qu'elles demandent (lieu et tenant dans l'arbitrage), refuser
   sur portée (`05-arbitrage.md` §11), reporter les retournements de Phoebe
   selon les toniques bus et ce qu'elle a vu.
3. Radio Halliwell : trois à sept items, l'horloge en dernier, et **toujours
   le compte du retournement de Phoebe** — à combien de tours il en est, et
   ce qui l'a bougé.
4. Aurore joue. Ses frappes et retournements, elle les dit en Question ;
   l'arbitre écrit. Une pièce posée sur une frappe d'en face est une parade,
   pas une frappe.
5. `--tour` ; lire `constatables` ; constater ce qui attend depuis un tour ;
   consumer les potions (`tranche`, `detruit`) ; redemander Lazare pour Cole
   s'il est tombé sans être enterré.

**Ce qu'on ne fait pas** : appliquer la partie au monde. Charmed n'est pas
la Danse.
