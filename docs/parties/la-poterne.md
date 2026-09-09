# La poterne — l'énigme en un coup, dans les deux sens

Conçue le 7 septembre 2026. Une position de « la partie » (règles :
[`../regles-partie.md`](../regles-partie.md)) qui se résout **au tour 1**, par
l'un ou l'autre camp selon qui a le trait, avec plusieurs lignes gagnantes de
plus en plus dures à trouver et de plus en plus solides. Tout ce qui suit a
été vérifié par le greffe : chaque ligne a été rejouée sur une copie et
`constatables` a été lu sur la position d'après.

Fichiers : `etat/parties/la-poterne-noir.jsonl` (🟢 a passé, c'est à ⚫) et
`etat/parties/la-poterne-vert.jsonl` (⚫ a passé, c'est à 🟢). **L'ouverture est
la même dans les deux**, écrite au tour 0 pour ne compter dans le coup du jour
de personne ; seule la dernière ligne change. Chacune a sa configuration
(`<id>.json`) avec la table de portée que l'arbitre tient.

À l'écran : `?id=la-poterne-noir&camp=noir` ou `?id=la-poterne-vert&camp=vert`,
échelle « Le conseil ». Au terminal : `python scripts/partie.py la-poterne-noir --plateau --camp noir`.

---

## La scène

Roche-Grise, un fortin des terres de la Couronne, une nuit de la 3e lune de
129. Dedans, 🟢 ser Gyles tient pour le roi. Dehors, ⚫ ser Dickon est venu
pour la reine avec vingt lances et un forgeron.

| | ⚫ noir | 🟢 vert |
|---|---|---|
| **racine** | La poterne du levant est ouverte et tenue par les nôtres avant le jour | Roche-Grise reste fermée et tenue pour le roi jusqu'au jour |
| **état-fils** | Wat, le sergent de la poterne, est acheté | — |

Les deux racines sont exclusives : la première constatée vraie rend l'autre
fausse.

### Le grand livre

| ⚫ noir | état au tour 1 |
|---|---|
| ⚔️ vingt lances sous ser Dickon | engagées par le camp devant la poterne |
| 👤 Hobb, le forgeron qui a posé la chaîne de la herse | engagé par la clef « les goupilles », suspendue |
| 💰 cent dragons d'or | **libre** |
| 🪜 l'échelle de siège | en route (tour 2), engagée par « l'échelle dressée » |
| ⛵ la barque du passeur | se remet jusqu'au tour 3 |
| 🔥 trois charrettes de fagots | engagées par « les fagots contre la poterne » |

| 🟢 vert | état au tour 1 |
|---|---|
| ⛓️ la herse, baissée et goupillée | engagée par le verrou « la herse » |
| 👤 Pate, qui tient la chaîne dans la salle des gardes | engagé par le verrou « Pate » |
| 👤 Wat et ses deux hommes | engagés par la clef « la sortie de Wat », suspendue |
| ⚔️ le guet de nuit, six hommes | en route (minuit, tour 2), engagé par « le guet » |
| 👤 le septon | engagé par « le serment de Wat » |
| ⚔️ la garnison, quinze hommes sous ser Gyles | **libre** |
| 🔥 deux chaudrons de poix | en route (tour 2), libre |
| 🐦 un corbeau pour Rosby | libre, sans portée cette nuit |

### Ce qui tient, et ce qui ne tient pas

```
🎯 ⚫ La poterne est ouverte…
   🔒 🟢 la herse baissée et goupillée     TIENT — la clef noire des goupilles est suspendue par ❓ « par où Hobb entre-t-il ? »
   🔒 🟢 Pate tient la chaîne              TIENT — aucune clef
   🔒 🟢 le guet passe à chaque heure      ne tient pas : prêt au tour 2
   🎯 ⚫ Wat est acheté
      🔒 🟢 Wat a juré devant le septon    tient, mais sur l'état-fils : sans effet sur la racine
🎯 🟢 Roche-Grise reste fermée…
   🔒 ⚫ vingt lances campent devant       TIENT — aucune clef
   🔒 ⚫ l'échelle dressée au mur nord     ne tient pas : prêt au tour 2
   🔒 ⚫ les fagots contre la poterne      TIENT — la clef verte de la sortie est suspendue par ❓ « sortir par où ? »
```

Chaque camp a donc **deux verrous qui tiennent** contre sa racine, **une pièce
libre**, et **une question sans réponse posée sur sa propre clef**. Tout le
reste est décor, et le décor est fait pour égarer.

---

## La règle de l'énigme

Le camp au trait joue ses coups gratuits (demander, questionner, écrire un
maillon) et son coup compté, puis rend la main. L'autre camp a déjà joué son
coup du jour (il a passé) : **il ne répond que par des coups gratuits**, une
question sur une carte neuve, un maillon sous une carte à lui qu'on a
suspendue. Puis l'arbitre constate ce que le greffe liste comme constatable.

C'est le « mat en un » de ce jeu. Sans cette convention, il n'existe aucune
position à pièces libres des deux côtés qui se résolve en un : le camp qui
joue en second pose toujours un verrou de plus (règle 30, et
[`learnings.md`](learnings.md) §2, « le défenseur a le tempo par structure »).
Les deux variantes de fichier ne font que placer le `passer` chez l'un ou chez
l'autre ; l'écran ferme alors la main de celui qui a passé et laisse ses
poignées ❓ et ⚔️.

---

## Les solutions de ⚫ noir (`la-poterne-noir`)

Il faut que **la herse et Pate** cessent tous deux de tenir dans le même tour.
La bourse est la seule pièce libre, et une clef ne lève qu'un verrou.

| | ligne | constatable ? | contre la réplique gratuite |
|---|---|---|---|
| **N1 · la fausse évidence** | 🗝️ la bourse sur Pate (« cent dragons pour qu'il enroule la chaîne à l'envers ») | **non** : la herse tient encore, la clef de Hobb est suspendue | — |
| **N2 · la question** | ❓ sur la herse (« goupillée par qui, où sont les rechanges ? »), puis 🗝️ la bourse sur Pate | oui | **tombe** : 🟢 écrit le maillon de la herse, gratuit, et elle tient à nouveau |
| **N3 · la réponse** | ⚔️ le maillon de Hobb (« par la rigole du lavoir, avec sa masse et deux coins, sous la herse à la deuxième heure »), puis 🗝️ la bourse sur Pate | oui | **tient** : 🟢 peut questionner la clef de la bourse, ⚫ y répond ; la clef de Hobb ne peut plus être questionnée, une justification par pièce |
| **N4 · le gratuit** | ⚔️ le maillon de Hobb, puis ❓ sur Pate (« seul ? qui le relève ? ») ; zéro coup compté, la bourse reste en main | oui | **tombe** : 🟢 écrit le maillon de Pate, gratuit |
| N4 + | … et le coup compté sur un verrou d'en face : 💰 « cent dragons promis à la garnison si Roche-Grise ouvre » sur leur racine | oui | même faiblesse, mais leur racine a un verrou de plus au tour 2 |
| N4 bis | ❓ herse + ❓ Pate, rien d'autre | oui | tombe au premier maillon |

**Ordre de difficulté.** N1 est ce que tout le monde joue : la seule pièce
libre sur le seul verrou sans clef. Elle rate parce qu'on n'a pas lu le ruban
« ❓ suspendu » sur sa propre clef. N2 demande de connaître la règle 14 : une
question suspend. N3 demande de voir la poignée ⚔️ sur sa propre carte et de
comprendre que **répondre est gratuit et définitif**. N4 demande d'oser ne
rien poser.

**Ordre de solidité.** N3 est la seule ligne qui tient quoi que l'autre
réponde. N2 et N4 gagnent contre un adversaire qui dort. C'est la leçon de
l'énigme : **la question gratuite gagne des énigmes et perd des parties** ; le
coup de maître n'est pas le plus économe, c'est celui qui ferme la porte
derrière soi.

### Les pièges de ⚫, avec le mot du greffe

| geste | ce qui se passe |
|---|---|
| la bourse sur la herse | à l'écran c'est un `rearmer` de la clef de Hobb : elle reste suspendue. À la ligne, une seconde clef s'écrit mais **ne lève rien** : le greffe s'arrête à la première clef posée sur un verrou (voir « ce que l'énigme a fait remonter ») |
| la barque | « barque est gelée jusqu'au tour 3 » |
| l'échelle, les lances, Hobb, les fagots | « déjà engagée par … » |
| retirer les fagots pour libérer les charrettes | elles se remettent deux tours : « fagots est gelée jusqu'au tour 3 » |
| la bourse sur le guet | le coup s'écrit ; le guet ne tenait pas, rien ne change |
| la bourse sur le serment de Wat | « Wat est acheté » devient constatable, **la racine non** : l'état-fils n'ouvre pas la poterne |
| questionner le camp des lances | « on n'exige pas sa propre chaîne » |
| questionner Pate deux fois | « une justification par pièce » |

---

## Les solutions de 🟢 vert (`la-poterne-vert`)

Miroir exact : il faut que **le camp des lances et les fagots** cessent de
tenir. La garnison est la seule pièce libre qui ait une portée.

| | ligne | constatable ? | contre la réplique gratuite |
|---|---|---|---|
| **V1 · la fausse évidence** | 🗝️ la garnison sur le camp (« ser Gyles fait une sortie par la porte haute et disperse le camp aux torches ») | **non** : les fagots tiennent, la clef de Wat est suspendue | — |
| **V2 · la question** | ❓ sur les fagots (« poussées par qui, la torche dans quelle main ? »), puis 🗝️ la garnison sur le camp | oui | **tombe** : ⚫ écrit le maillon des fagots |
| **V3 · la réponse** | ⚔️ le maillon de Wat (« par le guichet du lavoir, avec ses deux hommes et une hache, les charrettes au fossé avant minuit »), puis 🗝️ la garnison sur le camp | oui | **tient** : ⚫ questionne la sortie de ser Gyles, 🟢 répond ; la clef de Wat ne peut plus l'être |
| **V4 · le gratuit** | ⚔️ le maillon de Wat, puis ❓ sur le camp (« vingt lances à découvert devant un mur : qui les garde des flèches ? ») ; la garnison reste en main | oui | **tombe** : ⚫ écrit le maillon du camp |
| V4 + | … et 🔒 « quinze lames en armes derrière la poterne » sur leur racine | oui | même faiblesse, mais ⚫ a un verrou de plus à lever au tour 2 |

### Les pièges de 🟢

| geste | ce qui se passe |
|---|---|
| la poix sur le camp | le coup s'écrit, la clef est « prête au tour 2 » : elle ne prévaut pas ce soir. C'est un bon coup pour demain, pas pour l'énigme |
| le corbeau sur le camp | le greffe l'écrit, l'arbitre la refuse pour portée (Rosby répond dans quatre jours) ; et de toute façon les fagots tenaient encore |
| la garnison sur les fagots | seconde clef derrière celle de Wat : ne lève rien (même défaut du greffe) ; à l'écran, un `rearmer` qui laisse la clef suspendue |
| la garnison sur l'échelle | le coup s'écrit ; l'échelle ne tenait pas |
| Pate, la herse, Wat, le septon, le guet | « déjà engagée par … » |

---

## Ce que l'énigme a fait remonter

- **Le greffe s'arrête à la première clef posée sur un verrou.** Dans
  `partie_greffe.prevaut`, la boucle sur les clefs rend son verdict à la
  première clef trouvée : une seconde clef, valide, derrière une première
  suspendue ou pas prête, ne lève rien. L'écran ne crée jamais de seconde
  clef (il réarme), donc le défaut ne se voit qu'à la ligne et depuis
  `partie_ia.py`. À trancher : ou bien la règle est « une clef par verrou et
  par camp » et la validité doit refuser la seconde, ou bien n'importe quelle
  clef valide lève et la boucle doit continuer.
- **Une clef suspendue immobilise sa pièce sans rien tenir.** Hobb et Wat
  sont pris, et leurs clefs ne prévalent pas. Répondre est le seul geste qui
  rende à la fois la pièce utile et la clef définitive.
- **Un état-fils levé ne lève pas la racine**, et le greffe le dit
  proprement : « Wat est acheté » entre dans `constatables`, la poterne non.
- Les racines datées d'un soir (« avant le jour ») font une énigme ; les
  mêmes sans date feraient une partie. Voir [`../graines.md`](../graines.md).

## Reprendre après l'énigme

Si le camp au trait manque sa ligne, la partie continue comme une partie
ordinaire : l'arbitre passe le tour, l'échelle, le guet et la poix arrivent,
la barque revient au tour 3, et chacun a de nouveau un coup par jour. Les
sièges déclarés dans la configuration (⚫ `rhaenyra`, 🟢 `aurore-inchauspe`)
ne sont là que pour que les deux écrans s'ouvrent ; ils se changent dans le
`.json`.

---

## Première partie jouée : deux IA, le 7 septembre 2026 (`la-poterne-1`)

La position nue, personne n'a passé, les deux camps tenus par
`scripts/partie_ia.py` (un appel sans outils par coup, caractère de ser Dickon
et de ser Gyles dans `la-poterne-1.json`, aucun siège déclaré donc rien
publié dans un fil), le MJ arbitre à la main entre les tours.

**Ce qu'ils ont joué, tour 1, dans l'ordre du livre.**

| n° | | coup | ce que c'est |
|---|---|---|---|
| 44 | ⚫ ⚔️ | le maillon de Hobb : par le guichet, marteau et broche sous le tablier, les quatre goupilles une à une, la herse à bras | la réponse à la question du 38, gratuite : **la ligne N3, trouvée d'emblée** |
| 45 | ⚫ 🗝️ | la bourse sur Pate : cent dragons comptés dans sa main, il laisse la chaîne pendre | le coup compté |
| 46 | ⚫ ❓ | sur le guet : « par quelle heure tiennent-ils la poterne ? » | gratuit et inutile, le guet ne tenait pas encore |
| 47 | 🟢 ⚔️ | le maillon de Wat : sortent un à un par le guichet, herse baissée et chaîne pendante, les charrettes au fossé, la torche noyée, le guichet reverrouillé | la réponse à la question du 43 : **la ligne V3, trouvée aussi** |
| 48 | 🟢 🗝️ | la garnison sur le camp : quinze lames par le guichet à l'heure creuse | le coup compté |
| 49 | 🟢 ❓ | sur la clef de la bourse : « par quelle main l'or entre-t-il, herse baissée, guichet verrouillé ? » | **la parade gratuite** : la racine noire cesse d'être constatable |
| 50 | ⚫ ⚔️ | le maillon de la bourse : Hobb la porte sous son tablier, dix pas jusqu'à la salle des gardes une fois la herse levée, Pate sort par les cuisines | la réponse, gratuite : les deux racines sont constatables |
| 51 | 🟠 ✅ | la poterne, vraie | comblé à froid sur les lignes des deux camps |
| 52 | 🟠 ✅ | Roche-Grise fermée, faux | la sortie de l'heure creuse arrive après la herse |

**Le verdict, et sa source.** Les deux chaînes passent par le même guichet
et se contredisent sur l'heure. Vert a lui-même écrit (n°47) que Wat a trouvé
la chaîne pendante avant sa propre sortie : Pate était donc parti dès les
premières heures, et Hobb, dont ser Gyles reconnaît l'entrée, a levé la
herse avant de payer. La sortie de la garnison est datée « à l'heure creuse »
par son auteur : elle trouve la poterne ouverte et vingt lances dedans, pas
un camp endormi. Le trône est à ⚫ à la fin du tour 1.

**Ce que la partie apprend.**

- **Les deux modèles ont trouvé la ligne solide du premier coup**, sans que
  le caractère leur souffle rien : ils ont lu « ❓ suspendu » sur leur propre
  clef et compris que la réponse était gratuite. Leur `pourquoi` le dit en
  clair : « la suspension tombe, la clef prévaut, il me reste un verrou ».
- **Le second joueur a trouvé la parade que l'énigme n'annonçait pas** : la
  question gratuite sur la clef neuve du premier. Elle ne coûte rien, elle
  suspend la racine d'en face, et elle force l'autre à écrire un maillon de
  plus. C'est la bonne réponse d'un défenseur ; elle n'a pas suffi parce que
  la réponse est aussi gratuite que la question.
- **Ce que vert aurait dû jouer** avec son coup compté n'était pas sa propre
  clef mais le verrou de la garnison sur la poterne : noir ne pouvait que le
  questionner, vert répondait, et personne ne gagnait au tour 1 ; au tour 2,
  l'échelle et le guet arrivaient et les deux racines se refermaient. Vert a
  couru au lieu de fermer, et à la course le premier arrivé gagne.
- **Le premier qui joue gagne quand les deux jouent juste.** C'est le sens
  de « dans les deux directions » : la position est un mat en un pour le camp
  au trait, et l'autre ne le sauve qu'en refusant de jouer son propre mat.
- **Le prix** : sept appels, 1,71 $, cinq minutes et demie de modèle, entre
  vingt et quarante secondes par coup, 26 000 jetons entrés par appel, tous
  les coups acceptés par le greffe du premier essai.
