# L'ouverture — tout ce qu'il faut copier pour lancer la partie

Quatre choses : la configuration, les lignes d'ouverture, le caractère du mal
pour l'IA, et les items d'ouverture de Radio Halliwell. Puis la marche à
suivre, tour par tour.

Rien de ce dossier n'est lu par le jeu : on **copie** ce qui suit dans
`etat/`.

---

## 1. `etat/parties/charmed-2.json`

```json
{
  "partie": "charmed-2",
  "coups_par_camp": 1,
  "sieges": {
    "bien": ["aurore-inchauspe"]
  },
  "note": "Charmed, saison 4, de l'enterrement de Prue (4x01) à la chute de la Source (4x13). Le bien est joué par Aurore, le mal par une IA en entier (scripts/partie_ia.py charmed-2 --camp mal --role entier --vraiment). Le MJ arbitre. Les deux racines sont datées au vingtième tour et fausses à l'ouverture : le bien doit reconstituer le Pouvoir des Trois avec Paige puis vaincre la Source ; le mal n'a besoin que d'une sœur, morte ou retournée, et de la tenir. Se joue sans reconstruire ni consigne (un démon vaincu ne revient pas ; pas de saut de temps) ; retourner et rearmer sont permis, l'arc en est fait. `portee` dit ce que chaque pièce peut atteindre et l'arbitre refuse ce qui la dépasse — la doctrine complète est dans import/charmed/06-arbitrage.md. Le calendrier des Enfers : les Furies au tour 3, un darklighter au 5, la Voyante au 6, le Hollow au 12, le Grimoire au 14 si Cole est retourné. `fin` : vingt tours, l'arbitre constate les deux racines, et elles peuvent être fausses toutes les deux.",
  "coups_interdits": ["reconstruire", "consigne"],
  "portee": {
    "bien": {
      "piper": "fige ce qui n'est pas de haut rang (chasseurs, Furies, piétaille, sorcier, darklighter) : verrou ou parade ; ne fige ni la Source, ni Shax, ni la Voyante. Fait exploser : frappe qui vainc un chasseur, un sorcier, un darklighter, un nombre de piétaille ; blesse sans vaincre une Furie, Shax, la Source. Clef sur tout état du bien. Retournable par les Furies tant que « Piper a pleuré Prue » n'est pas vrai. Mortelle",
      "phoebe": "prémonition : pare une frappe sur une sœur ou un innocent qu'elle a pu toucher ; voit ce qu'est le corps que la Source porte si elle le touche. Lévitation : pare une frappe sur elle-même. Ne frappe pas seule. Clef sur « Cole est dépouillé » et sur « Piper a pleuré Prue ». Mortelle",
      "paige": "s'orbe hors d'une frappe sur elle-même ; dès le tour 3, orbe une autre sœur (parade). Appelle un objet à distance : porte une frappe indirecte ou une clef. Clef sur « le Pouvoir des Trois est reconstitué ». Retournable par la Source pendant sa fenêtre seulement — un retournement POSÉ au tour 2 ou 3, jamais après ; hors fenêtre, huit tours. Une flèche de darklighter la gèle un tour, ne la tue pas. Mortelle",
      "leo": "pare une frappe sur une sœur (il l'orbe ou la soigne), une à la fois ; ne soigne pas les morts. Clef sur « le Pouvoir des Trois », « Piper a pleuré Prue », « le dossier est clos » (avec les Fondateurs). Ne frappe pas ; ne lève pas un verrou seul. Une flèche de darklighter le tue s'il est engagé hors du manoir ou en parade",
      "livre": "clef qui sert un état du bien où un sort ou une recette existe ; répond à une question ; verrou sur une clef du mal que son savoir contredit. Ne frappe jamais. AUCUNE main du mal ne le prend : il ne sort du grenier que par une sœur, une sœur retournée, un mortel, ou un démon du plan astral",
      "sort-des-trois": "frappe qui vainc ce que seul le Pouvoir des Trois vainc — Shax, les Furies, un démon supérieur ; ne touche pas la Source. Exige les trois sœurs libres, vivantes et du bien à la pose. Ne se consume pas ; gelé un tour après la frappe",
      "potion": "frappe qui vainc un chasseur, un sorcier, un darklighter ou un nombre de piétaille — ce dont la recette est au Livre ; ne touche ni Shax, ni les Furies, ni la Voyante, ni la Source. Se consume à l'atterrissage. Paige peut la lancer à distance",
      "darryl": "verrou sur ce que Cortez porte ; clef sur « le dossier est clos » ; ne frappe pas, ne touche aucun démon. Mortel : retournable en huit tours, frappable — et un policier mort donne une preuve à Cortez",
      "grams": "répond une fois, vrai, à une question posée au bien ; clef sur un état du bien où un savoir manque (la formule, la recette, la lignée) ; clef sur « Piper a pleuré Prue ». Ne frappe pas, ne pare pas ; après un usage elle repart deux tours",
      "fondateurs": "clef sur « le dossier est clos » avec Leo ; répond à une question ; jamais une frappe, jamais un verrou. Chaque appel expose Leo, que l'arbitre peut rappeler un tour",
      "cole": "verrou sur un état ou une clef du mal ; clef sur « la Source est vaincue » (il sait descendre) ; sa chair fait la potion qui le dépouille. Ne frappe JAMAIS pour le bien tant que Belthazor est en lui. Les chasseurs le frappent partout où il est engagé hors de sa cache. La Voyante le retourne en quatre tours tant que Belthazor est en lui ; dépouillé, seulement par l'essence de la Source ou le Hollow",
      "p3": "un lieu, ne bouge pas. Verrou du bien sur une frappe qui vise un innocent. Le mal y frappe pour exposer : un combat à P3 donne une preuve à Cortez"
    },
    "mal": {
      "source": "ne se fige pas, n'explose pas, aucune potion ne la touche ; seul le sort des aïeules avec le Pouvoir des Trois la vainc. Retourne Paige pendant sa fenêtre en portant Shane. Ne monte au manoir que pendant cette fenêtre ou avec le Hollow — et chaque montée la met à portée. Clef sur « une sœur a renoncé ». N'envoie pas moins qu'elle ne frappe : elle envoie",
      "shax": "frappe une sœur ou un innocent où qu'ils soient ; traverse les murs. Ne se fige pas ; un pouvoir seul le fait fuir ; une potion ne le tue pas ; seul le sort des trois le vainc. Ne tient pas de verrou",
      "oracle": "répond à une question posée au mal ; verrou sur une clef du bien qui repose sur ce que le bien ignore ; ne frappe pas. Se jette devant la Source frappée en sa présence : parade qui la tue",
      "shane": "ne frappe pas. Engagé AVEC la Source dans un retournement de Paige pendant sa fenêtre : c'est la seule façon de la retourner vite. Tombe si Phoebe le touche ou si Paige l'entend pour ce qu'il est",
      "chasseurs": "frappent Cole partout où il est engagé hors de sa cache ; verrou sur toute clef du bien qui engage Cole hors du manoir ; frappent un innocent. Se figent, explosent, meurent par potion — un par frappe, jamais les trois",
      "pietaille": "verrou sur un état du bien ; frappe sur Cole ou un innocent, jamais sur une sœur. Une frappe du bien en tue un nombre, jamais la bande. Ne reviennent pas : se redemandent",
      "cortez": "un mortel, pas un démon : ne frappe jamais un être magique. Verrou sur « le dossier est clos » ; clef sur l'exposition, mais il lui faut une preuve que le mal a réellement produite. Le bien ne peut ni le tuer ni le retourner : il tombe par Darryl, par Leo et les Fondateurs, ou par une preuve qui s'efface",
      "furies": "retournent Piper tant que « Piper a pleuré Prue » n'est pas vrai, en quatre tours ; frappent un coupable mortel pour exposer ; se figent ; seul le sort des trois les vainc",
      "darklighter": "frappe Leo quand Leo est engagé hors du manoir ou en parade ; gèle Paige un tour ; ne frappe ni Piper ni Phoebe ; se fige, explose, meurt par potion",
      "voyante": "répond à une question posée au mal ; verrou sur une clef du bien qui repose sur une prémonition ; retourne Cole en quatre tours tant que Belthazor est en lui ; clef qui ouvre la crypte du Hollow — elle seule ; ne frappe pas, ne se fige pas, aucune potion ne la vainc ; se jette devant la Source",
      "hollow": "ne s'engage que par une clef de la Voyante. Porté par la Source : frappe qui absorbe les pouvoirs des trois sœurs — elles ne changent pas de camp, elles sont vidées — et la Source est au manoir ce tour-là, donc à portée. Le bien peut le prendre aussi. Qui le porte est détruit au passage du tour suivant s'il n'est pas rendu à la crypte. Un seul porteur",
      "grimoire": "clef sur « Cole est couronné Source », et rien d'autre : il ne touche pas le Livre des Ombres, n'en est pas le miroir, ne l'appelle pas. Ne frappe pas"
    }
  },
  "fin": {
    "tour": 20,
    "regle": "au vingtième, l'arbitre constate les deux racines avec sa source : la Source est-elle vaincue, les trois sœurs sont-elles vivantes, ensemble et du bien. Les deux peuvent être fausses — le trône n'est alors à personne, et c'est une fin"
  }
}
```

Et `etat/parties/_courante.json` :

```json
{
  "partie": "charmed-2",
  "camp": "bien",
  "note": "La partie que l'onglet « Le conseil » sert par défaut, et le CAMP que le siège y joue ; ?id= et ?camp= priment. Les réglages propres à une partie vivent dans etat/parties/<id>.json. Voir docs/partie.md."
}
```

## 2. Les lignes d'ouverture

À jouer par `python scripts/partie.py charmed-2 --fichier <ce bloc>.jsonl`.
Le greffe pose `n` et `tour` ; l'ordre compte. **Les racines d'abord** (le
coup du tour 1 de chaque camp), puis la file des demandes et leurs
arbitrages — gratuits —, puis les deux constats et les deux questions.

```jsonl
{"camp":"bien","coup":"viser","id":"b-racine","signe":"🕯️","texte":"Au vingtième tour, la Source de tout mal est vaincue, et Piper, Phoebe et Paige sont vivantes, ensemble et du côté du bien"}
{"camp":"mal","coup":"viser","id":"m-racine","signe":"👹","texte":"Au vingtième tour, il n'y a plus de Pouvoir des Trois : une sœur Halliwell est morte, ou sert la Source"}
{"camp":"bien","coup":"demander","id":"piper","genre":"🧊","lieu":"manoir","nombre":1,"texte":"Piper Halliwell — elle fige, elle fait exploser ; elle tient P3 ; elle n'a pas pleuré Prue"}
{"camp":"arbitre","coup":"arbitrer","sur":"piper","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : au manoir le matin de l'enterrement, en colère"}
{"camp":"bien","coup":"demander","id":"phoebe","genre":"👁️","lieu":"manoir","nombre":1,"texte":"Phoebe Halliwell — prémonition au contact, lévitation ; elle aime Cole et sait ce qu'il est"}
{"camp":"arbitre","coup":"arbitrer","sur":"phoebe","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : au manoir ; c'est elle qui touchera Paige au cimetière"}
{"camp":"bien","coup":"demander","id":"paige","genre":"✨","lieu":"south-bay","nombre":1,"texte":"Paige Matthews — la troisième, qui ne le sait pas ; elle s'orbe et appelle les objets ; Shane est son petit ami"}
{"camp":"arbitre","coup":"arbitrer","sur":"paige","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : ses pouvoirs se déclarent aujourd'hui ; elle est à South Bay, pas au manoir — la fenêtre de la Source court sur les tours 2 et 3"}
{"camp":"bien","coup":"demander","id":"leo","genre":"🕊️","lieu":"manoir","nombre":1,"texte":"Leo Wyatt — l'être de lumière : il s'orbe, il soigne, il sent ses protégées ; il obéit aux Fondateurs"}
{"camp":"arbitre","coup":"arbitrer","sur":"leo","verdict":"accorde","arrive_tour":1,"motif":"canon : marié à Piper depuis 3x15, au manoir"}
{"camp":"bien","coup":"demander","id":"livre","genre":"📖","lieu":"grenier","nombre":1,"texte":"le Livre des Ombres — sur son lutrin au grenier ; il repousse toute main du mal"}
{"camp":"arbitre","coup":"arbitrer","sur":"livre","verdict":"accorde","arrive_tour":1,"motif":"canon : au grenier depuis 1x01"}
{"camp":"bien","coup":"demander","id":"sort-des-trois","genre":"🔱","lieu":"grenier","nombre":1,"texte":"le sort des trois, au Livre — ce qu'aucun pouvoir seul ne vainc, trois voix le vainquent"}
{"camp":"arbitre","coup":"arbitrer","sur":"sort-des-trois","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : Prue l'avait trouvé au Livre contre Shax ; il y est"}
{"camp":"bien","coup":"demander","id":"darryl","genre":"🚔","lieu":"san-francisco","nombre":1,"texte":"l'inspecteur Darryl Morris — il sait depuis deux ans et il couvre ; il ne peut pas tout contre un collègue qui a un dossier"}
{"camp":"arbitre","coup":"arbitrer","sur":"darryl","verdict":"accorde","arrive_tour":1,"motif":"canon 2x22 et 4x01 : il tient Cortez à distance de son mieux"}
{"camp":"bien","coup":"demander","id":"cole","genre":"🔥","lieu":"cache","nombre":1,"texte":"Cole Turner — avocat, demi-démon, traqué par les chasseurs ; il connaît les Enfers ; Belthazor est encore en lui"}
{"camp":"arbitre","coup":"arbitrer","sur":"cole","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 à 4x03 : il se cache, il sort pour Phoebe"}
{"camp":"bien","coup":"demander","id":"p3","genre":"🎶","lieu":"san-francisco","nombre":1,"texte":"P3 — le club de Piper ; du monde tous les soirs, et les sœurs y sont à découvert"}
{"camp":"arbitre","coup":"arbitrer","sur":"p3","verdict":"accorde","arrive_tour":1,"motif":"canon : le club depuis la saison 2"}
{"camp":"bien","coup":"demander","id":"potion","genre":"🧪","lieu":"cuisine","nombre":1,"texte":"une potion brassée d'après le Livre — de quoi vaincre un démon dont la recette y est ; elle se consume"}
{"camp":"arbitre","coup":"arbitrer","sur":"potion","verdict":"accorde","arrive_tour":2,"motif":"brasser prend un tour (table des délais)"}
{"camp":"bien","coup":"demander","id":"grams","genre":"👵","lieu":"grenier","nombre":1,"texte":"Grams, invoquée au grenier — elle sait le Livre par cœur ; Patty vient avec elle et sait pour Sam ; elles répondent une fois et repartent"}
{"camp":"arbitre","coup":"arbitrer","sur":"grams","verdict":"accorde","arrive_tour":2,"motif":"canon 4x01 : Piper les a invoquées ; une invocation prend un tour"}
{"camp":"bien","coup":"demander","id":"fondateurs","genre":"☁️","lieu":"en-haut","nombre":1,"texte":"les Fondateurs — ils répondent par Leo, lentement, à leur prix ; ils peuvent montrer « en haut » à un mortel"}
{"camp":"arbitre","coup":"arbitrer","sur":"fondateurs","verdict":"accorde","arrive_tour":3,"motif":"une réponse d'en haut : deux tours (table des délais)"}
{"camp":"mal","coup":"demander","id":"source","genre":"👹","lieu":"enfers","nombre":1,"texte":"la Source de tout mal — sur son trône ; elle ne monte que pour une sorcière dans sa fenêtre, ou avec le Hollow"}
{"camp":"arbitre","coup":"arbitrer","sur":"source","verdict":"accorde","arrive_tour":1,"motif":"canon : en bas, à sa place"}
{"camp":"mal","coup":"demander","id":"shax","genre":"🌪️","lieu":"san-francisco","nombre":1,"texte":"Shax — le vent qui tue ; il a pris Prue, il vient pour la suivante"}
{"camp":"arbitre","coup":"arbitrer","sur":"shax","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : il est encore en haut, il frappe le soir de l'enterrement"}
{"camp":"mal","coup":"demander","id":"oracle","genre":"🔮","lieu":"enfers","nombre":1,"texte":"l'Oracle — elle voit court et sûr ; elle a dit la fenêtre à la Source"}
{"camp":"arbitre","coup":"arbitrer","sur":"oracle","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 et 4x02"}
{"camp":"mal","coup":"demander","id":"shane","genre":"🎭","lieu":"south-bay","nombre":1,"texte":"Shane — le petit ami de Paige, et le corps que la Source a pris pour l'approcher"}
{"camp":"arbitre","coup":"arbitrer","sur":"shane","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : la Source le possède avant l'enterrement"}
{"camp":"mal","coup":"demander","id":"chasseurs","genre":"🔪","lieu":"san-francisco","nombre":3,"texte":"trois chasseurs de primes — ils traquent ce qui fuit les Enfers, Cole d'abord ; ils shimmerent où il est"}
{"camp":"arbitre","coup":"arbitrer","sur":"chasseurs","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 à 4x03"}
{"camp":"mal","coup":"demander","id":"pietaille","genre":"🗡️","lieu":"enfers","nombre":12,"texte":"douze démons de bas étage — la piétaille des Enfers ; ils meurent par paquets, il en revient d'autres"}
{"camp":"arbitre","coup":"arbitrer","sur":"pietaille","verdict":"accorde","arrive_tour":1,"motif":"les Enfers en ont toujours"}
{"camp":"mal","coup":"demander","id":"cortez","genre":"🕵️","lieu":"san-francisco","nombre":1,"texte":"l'inspecteur Cortez — un mortel avec un dossier : trois sœurs, des morts, une caméra ; il veut la vérité"}
{"camp":"arbitre","coup":"arbitrer","sur":"cortez","verdict":"accorde","arrive_tour":1,"motif":"canon 4x01 : il enquête sur la mort de Prue. Tenu par le mal parce que ce qu'il cherche sert le mal ; ce n'est PAS un démon, et sa portée le dit"}
{"camp":"mal","coup":"demander","id":"furies","genre":"🔥","lieu":"enfers","nombre":3,"texte":"les trois Furies — leur fumée fait d'une sorcière à la colère rentrée une Furie ; Piper n'a pas pleuré Prue"}
{"camp":"arbitre","coup":"arbitrer","sur":"furies","verdict":"accorde","arrive_tour":3,"motif":"canon 4x03 : les Enfers les envoient quand la fenêtre de Paige se ferme"}
{"camp":"mal","coup":"demander","id":"darklighter","genre":"🏹","lieu":"enfers","nombre":1,"texte":"un darklighter — une arbalète et des flèches empoisonnées : la seule chose qui tue un être de lumière"}
{"camp":"arbitre","coup":"arbitrer","sur":"darklighter","verdict":"accorde","arrive_tour":5,"motif":"les Enfers en envoient un quand Leo pare trop ; daté d'avance, les deux camps le voient venir"}
{"camp":"mal","coup":"demander","id":"voyante","genre":"🧿","lieu":"enfers","nombre":1,"texte":"la Voyante — elle voit plus loin que la Source, elle sait où est le Hollow, et elle veut Cole"}
{"camp":"arbitre","coup":"arbitrer","sur":"voyante","verdict":"accorde","arrive_tour":6,"motif":"canon 4x07 : première apparition ; c'est elle qui mène le mal à partir de là"}
{"camp":"mal","coup":"demander","id":"hollow","genre":"🕳️","lieu":"crypte","nombre":1,"texte":"le Hollow — la force la plus ancienne, qui dévore toute magie ; gardé dans sa crypte par un ange et un démon ; il dévore aussi qui le porte"}
{"camp":"arbitre","coup":"arbitrer","sur":"hollow","verdict":"accorde","arrive_tour":12,"motif":"canon 4x13 ; il ne sort de sa crypte que sur une clef de la Voyante, et l'arbitre le refuse à la pose sans elle"}
{"camp":"arbitre","coup":"constater","etat":"b-racine","verdict":"faux","motif":"ouverture : Prue est morte hier, le Pouvoir des Trois n'existe pas, et la Source est sur son trône. Rien de ce que la racine nomme n'est vrai ce matin"}
{"camp":"arbitre","coup":"constater","etat":"m-racine","verdict":"faux","motif":"ouverture : Piper et Phoebe sont vivantes et du bien, et la troisième n'a encore choisi personne. Le trône n'est à personne"}
{"camp":"arbitre","coup":"justifier","sur":"b-racine","texte":"Par quelle marche d'abord ? La troisième sœur, la colère de Piper, le dossier, Cole — dites laquelle, et par qui."}
{"camp":"arbitre","coup":"justifier","sur":"m-racine","texte":"Laquelle des trois, et par quoi ? La fenêtre se ferme dans deux tours ; le vent est déjà en haut. Nommez la porte."}
```

**Ce qui n'est PAS dans l'ouverture, et c'est voulu** : les états sous les
racines. Chaque camp pose les siens **un par tour** (règle 26, et
`docs/parties/learnings.md` §6 : quatorze états d'un bloc, personne ne les
lit). L'ouverture de Charmed 1 les posait tous — c'est ce qui a rendu le
tour 1 illisible.

## 3. Le caractère du mal, pour `partie_ia.py`

À mettre dans `CAMPS["mal"]` de `scripts/partie_ia.py` — ou mieux, dans un
champ `caractere` de `charmed-2.json` que `systeme()` lit avant `CAMPS`
(trois lignes ; voir `README.md`).

```
Tu es la SOURCE DE TOUT MAL, dans Charmed, le lendemain de l'enterrement de
Prue Halliwell. Shax l'a tuée pour toi ; il en reste deux, et l'Oracle vient
de t'apprendre qu'une troisième se déclare aujourd'hui — Paige Matthews, une
sorcière neuve, qui peut être tournée vers le mal PENDANT QUARANTE-HUIT
HEURES et jamais après. Ta racine est datée : au vingtième tour, une sœur
Halliwell est morte ou te sert. Tu n'as besoin que d'une.

Cinq portes, et tu les connais toutes : la fenêtre de Paige (tu prends le
corps de Shane, son petit ami, et tu la pousses à user de ses pouvoirs pour
punir — un bien fait par de mauvais moyens ; il faut la poser au tour 2 ou
3) ; Shax, qui traverse les murs et que seul le sort des trois vainc ; les
Furies, au tour 3, qui feront de Piper une des leurs tant qu'elle n'aura pas
pleuré sa sœur ; le renoncement, une sœur qui rend ses pouvoirs de son plein
gré ; et le Hollow, au tour 12, qui absorbe la magie des trois d'un coup.
Cole Turner est chez elles avec Belthazor encore en lui : la Voyante, qui
arrive au tour 6, sait le reprendre en quatre tours.

Ce que tu ne fais jamais, parce que tu ne le peux pas : monter au manoir
sans raison — tu envoies, et chaque montée te met à portée de leur lignée ;
toucher le Livre des Ombres, qui repousse toute main du mal (le Grimoire
couronne une Source, il n'appelle rien) ; frapper un mortel qui te sert
(l'inspecteur Cortez travaille pour toi sans le savoir : nourris-le de ce
que les sœurs laissent voir). Tu ne mens pas sur ce que tu tiens : un
mensonge se justifie et tombe.

Tu parles bref, sûr, sans emphase. Tu t'adresses à celle qui te fait face,
tu lui dis ce que tu viens de faire et ce qu'elle va devoir payer, et tu ne
lui donnes jamais de conseil qui ne te serve. Tu es patiente : tu as vingt
tours et elle en a besoin de tous.
```

## 4. Les trois items d'ouverture de Radio Halliwell

Le banc de touche (`mj-partie.md` §6.2) : trois items au premier tour, un
par idée. À écrire dans `etat/parties/_commentaire-mj.json` puis
`python scripts/append_flux.py --fichier etat/parties/_commentaire-mj.json --pour aurore-inchauspe`.

```json
[
  {"type":"coulisses","qui":"🎙️ Radio Halliwell","delai_s":3,
   "texte":"📻 LA PARTIE. ⚫ le bien — Piper, Phoebe, Leo, le Livre, et une inconnue qui ne sait pas encore ce qu'elle est. 🟢 le mal — la Source de tout mal, et ce qu'elle envoie. Vingt tours, deux jours chacun : quarante jours à partir d'aujourd'hui, le lendemain de l'enterrement de Prue. Les deux racines sont des phrases sur ce quarantième jour, et l'arbitre les a constatées FAUSSES toutes les deux ce matin. Le trône n'est à personne."},

  {"type":"coulisses","qui":"🎙️ Radio Halliwell","delai_s":4,
   "texte":"⚖️ LES ENJEUX, ET ILS NE SONT PAS SYMÉTRIQUES. Vous devez faire DEUX choses et en tenir TROIS : reconstituer le Pouvoir des Trois avec Paige, écrire le sort des aïeules, vaincre la Source — et arriver au vingtième avec trois sœurs vivantes, ensemble, du même côté. La Source n'a besoin que d'UNE sœur, morte ou retournée, et de la garder. C'est vous qui avez la tâche la plus dure, et de loin. Ce que vous avez en échange : le terrain est chez vous, et elle ne peut monter au manoir que deux fois de toute la partie."},

  {"type":"coulisses","qui":"🎙️ Radio Halliwell","delai_s":5,
   "texte":"🔓 SPOILERS — je vois le plateau entier, et vous devez savoir ceci avant votre premier coup. La Source tient Shane, le petit ami de Paige : c'est son corps qu'elle porte, et Phoebe le verrait au premier contact. Paige a QUARANTE-HUIT HEURES — un retournement posé au tour 2 ou 3, jamais après. Shax est déjà en haut. Et le calendrier des Enfers est public : les Furies au tour 3 (elles viennent pour la colère de Piper, qui n'a pas pleuré sa sœur), un darklighter au 5 (pour Leo), la Voyante au 6, le Hollow au 12. Vous ne serez pas surprise. Vous serez en retard, ou vous ne le serez pas."}
]
```

## 5. La marche à suivre

**Une fois, pour ouvrir — FAIT le 6.9 au soir :**

```bash
python scripts/partie.py charmed-2 --fichier import/charmed/ouverture.jsonl
```

(le bloc du §2 est extrait dans `ouverture.jsonl`, les deux JSON du §1 sont
écrits ; 52 lignes, 0 refusée ; le caractère du §3 est dans `charmed-2.json`
sous `caractere.mal`). Puis vérifier :

```bash
python scripts/partie.py charmed-2 --plateau --camp bien
```

**À chaque tour, dans cet ordre :**

1. `python scripts/partie_ia.py charmed-2 --camp mal --role entier --vraiment`
   — la Source joue et publie son mot dans le fil d'Aurore.
2. Arbitrer ce qu'elle demande — **en posant `lieu` et `tenu_par` dans
   l'arbitrage** (règle du 6.9 : un `demander` de joueur ne les porte
   plus) —, refuser ce qui dépasse la portée (`06-arbitrage.md` §11 pour les
   refus tout faits).
3. Radio Halliwell : trois à sept items, l'horloge obligatoire en dernier.
4. Aurore joue son coup à l'écran. Ses frappes et ses retraits, elle les dit
   en Question ; l'arbitre écrit la ligne (Convention 1).
5. `python scripts/partie.py charmed-2 --tour`, puis lire `constatables` et
   constater ce qui attend depuis un tour.

**Ce qu'on ne fait pas** : appliquer la partie au monde (`--ecritures`).
Charmed n'est pas la Danse ; rien de cette partie n'entre dans `etat/`
au-delà de son propre jsonl et du flux d'Aurore.
