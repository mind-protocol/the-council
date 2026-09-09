# Bilan de Charmed 1 — sept tours, 94 lignes, et ce qu'on en tire

Source : `etat/parties/charmed.jsonl` (n° 1 à 94), `etat/parties/charmed.json`,
les items « mal · entier (IA) » et « 🎙️ Radio Halliwell » du flux d'Aurore,
`docs/parties.md` §VI. Jouée les 5 et 6 septembre 2026 : le bien par Aurore
à l'écran, le mal par `partie_ia.py --role entier`, le MJ arbitre.

---

## 1. Ce qui s'est passé, tour par tour

| Tour | Le mal (IA) | Le bien (Aurore) | L'arbitre |
|---|---|---|---|
| 1 | racine « le monde entier est contrôlé par le mal » + trois marches d'un bloc (Pouvoir des Trois brisé, Livre pris, Nexus éveillé) ; sept pièces | racine « l'équilibre est maintenu » + trois états d'un bloc ; huit pièces-gestes | constate la racine du bien VRAIE dès l'ouverture, celle du mal fausse ; deux questions |
| 2 | tente de **retourner Cole** par Balthazar → refusé (coup interdit) ; rejoue une clef « Balthazar tient Phoebe à l'écart » | deux questions, puis **passe** | accorde au mal l'Ombre et une sorcière « pour l'équilibre des mains » |
| 3 | répond à la question (maillon « Cole se tait, Phoebe garde le secret ») ; clef « le Grimoire appelle le Livre par son miroir » ; demande Shax (t4), Barbas (t8), Zankou (t12) | demande potion-2, Pouvoir des Trois, Grams, manoir ; verrou « la potion vainc Balthazar » sur m-trois | accorde tout ; **11 pièces du bien en branche morte** |
| 4 | clef « l'Ombre éveille le Nexus » | verrou « Phoebe récite la formule vue en prémonition » sur m-nexus | **constate m-livre VRAI** : le Livre est aux Enfers ; b-livre faux ; racine du bien fausse — le trône n'est à personne |
| 5 | clef « le Grimoire lit la formule au miroir » contre le verrou de Phoebe | question « comment tu peux la voir dans le Livre » ; verrou « Grams donne la formule de rappel » sur m-livre | — |
| 6 | maillon « le Devin entend la prémonition avant Phoebe » (gratuit) ; **frappe : Shax sur Prue**, atterrit au passage du 8 | question « par quelle porte » ; verrou « le Pouvoir des Trois récite le rappel » sur m-livre | constate m-livre FAUX (le Livre revient), b-livre vrai, **m-nexus VRAI**, b-nexus faux |
| 7 | maillon « Shax entre par la porte que Prue ouvre » (gratuit) ; clef « le Grimoire retient le Livre par le miroir » contre les deux verrous | *(pas encore joué)* | — |

Position au 7 : une marche du mal vraie (le Nexus), une deuxième en balance
(le Livre, verrou contre clef), une frappe vivante sur Prue, le trône à
personne. La partie était bien engagée pour le mal.

## 2. Ce qui a marché, et qu'on garde

- **La voix de la Source dans le fil.** L'IA rend, avec chaque coup, un mot
  à son adversaire dans sa voix (« Nommez-le, je vous en prie : j'aime savoir
  ce que vous dépensez »). C'est le meilleur de la partie : Aurore joue
  contre quelqu'un. On garde `--role entier` et le mot publié en coulisses.
- **La question gratuite comme arme du bien.** Ses trois questions (comment
  Cole tient Phoebe, comment le Livre sort, par quelle porte Shax) ont
  chaque fois suspendu la pièce d'en face et forcé le mal à écrire — et
  chaque réponse a donné une carte (la porte ouverte par Prue). C'est le jeu
  tel que `docs/parties/learnings.md` §2 le décrit.
- **Le calendrier des Enfers.** Shax au 4, Barbas au 8, Zankou au 12 : des
  corps forts et datés qui donnent au mal une raison de frapper à date. On
  garde le principe, avec les bons démons.
- **Radio Halliwell.** Le banc de touche a trouvé sa voix pour cette partie ;
  le nom reste.
- **La table de portée** (`portee` de la configuration) : c'est elle qui a
  permis à l'arbitre de refuser des coups sans règle nouvelle. On la garde,
  on la resserre.

## 3. Les six défauts, et ce qu'on en fait

### 3.1 Le bien n'avait rien à faire

Sa racine était **constatée vraie au tour 1**. Un camp qui tient déjà ce
qu'il veut ne joue que des parades ; Aurore a passé au 2, et onze de ses
pièces étaient en branche morte au 3. Le manuel le dit ailleurs (`docs/parties.md`
§VI) : « un bien dont la racine était vraie sans mesure n'avait rien à
jouer ».

**Charmed 2 :** la racine du bien est **fausse à l'ouverture et datée** — le
Pouvoir des Trois est à reconstituer (Paige), et la Source est à vaincre
avant le vingtième tour. Le bien a trois choses à ÉTABLIR et deux à tenir.

### 3.2 Les pièces du bien étaient des gestes, pas des gens

« utiliser le pouvoir de Prue », « regarder dans le Livre ». Conséquence
absurde : Shax a frappé **la télékinésie de Prue** (n° 85, `cible:
pouvoir-prue`) et non Prue. Et Leo, Cole, les Fondateurs n'ont jamais été
engagés parce qu'un geste n'a pas de raison d'être posé s'il n'y a rien à
faire.

**Charmed 2 :** **les sœurs sont les pièces**, avec leurs pouvoirs dans la
portée. Une sœur engagée est occupée ; une sœur frappée meurt (ou Leo la
pare) ; une sœur retournée change de camp. C'est ce que la série fait.

### 3.3 Trois saisons dans la même pièce

Prue vivante (saisons 1–3) avec Cole et Balthazar (3–4), le Devin — la
Voyante (4), Barbas (1, 2, 5, 7), Zankou et l'éveil du Nexus (7), l'Ombre du
Nexus (1). Aucune de ces choses n'est fausse ; c'est leur coexistence qui ne
tient pas. Le Nexus a donné au mal une marche que la Source n'a jamais visée
dans l'arc où Shax et Balthazar existent.

**Charmed 2 :** **un arc, une saison, un point de départ** — 4x01, le
lendemain de l'enterrement de Prue. Chaque pièce des Enfers est celle que la
Source a réellement envoyée dans ces treize épisodes, dans l'ordre où elle
les a envoyées. `02-canon.md` est la référence ; `06-arbitrage.md` dit
comment l'arbitre s'en sert pour refuser.

### 3.4 Le Livre pris par un « miroir » — la protestation d'Aurore était juste

Ligne 53, Aurore : « comment sort le livre des ombres du grenier ? comment
la source passe le bouclier de protection du livre qui se protège contre le
mal ? » L'IA a répondu par une invention élégante (le Grimoire « appelle son
miroir », aucune main ne touche le Livre) et l'arbitre l'a acceptée (n° 76).
Dans la série, le Livre **ne quitte le grenier que par une main** — celle
d'une sœur, d'un mortel, ou d'un être qui n'est pas du mal —, et il repousse
physiquement toute main démoniaque. Le Grimoire n'a jamais eu ce pouvoir ;
il sert au couronnement d'une Source.

**Charmed 2 :** la portée du Livre est écrite noir sur blanc dans la
configuration, et la doctrine de l'arbitre (`06-arbitrage.md` §1) liste les
SEULES façons canoniques de le faire sortir : une sœur qui l'emporte (4x03),
une sœur passée au mal, un mortel, un démon du plan astral (Abraxas, 2x01).

### 3.5 Les coups interdits ont tordu le jeu

Sans `retourner`, le mal a perdu **l'arc entier de Cole** au tour 2 (refus
n° 46) et l'a rejoué en clef, ce qui ne dit plus la même chose. Sans
`rearmer`, un front absorbait une pièce de chaque côté pour toujours, et il
a fallu inventer des pièces pour l'équilibre. Et parce que `detruire` n'a
pas de geste à l'écran, Aurore a « vaincu » Balthazar par un **verrou** (n° 72)
au lieu d'une frappe — le plateau ne dit pas ce qu'elle a fait.

**Charmed 2 :** `retourner` et `rearmer` sont **permis** — l'arc de la saison
4 est fait de retournements (Paige, Piper en Furie, Cole). `reconstruire` et
`consigne` restent hors jeu (un démon vaincu ne revient pas : les Enfers en
envoient un autre ; pas de saut de temps). Et une **convention** pour le bien
à l'écran : vaincre un démon = `detruire`, écrit à la ligne par l'arbitre sur
la parole d'Aurore, même tour, même coût (`03-conception.md` §7).

### 3.6 L'équilibre a été rattrapé en cours de route

Deux pièces ajoutées au mal au tour 2, quatre au bien au tour 3, « pour
l'équilibre des mains ». Ce n'est pas une faute — c'est le signe que
l'ouverture n'avait pas été comptée.

**Charmed 2 :** les mains sont comptées d'avance (`04-cartes-de-depart.md`
§5) : douze pièces au bien, douze au mal, dont cinq datées de chaque côté
pour que la position bouge sans que l'arbitre ait à combler.

## 4. Deux choses qu'Aurore a faites et qui dictent la conception

- **Elle a joué canon.** La potion pour Balthazar, la formule de Grams pour
  rappeler le Livre, le Pouvoir des Trois qui récite : ses coups sont ceux
  de la série. Quand la partie l'est aussi, ses coups seront acceptés sans
  débat, et c'est le mal qui devra s'aligner.
- **Elle joue par questions et par verrous, pas par états.** Elle n'a posé
  aucun état en sept tours et n'a levé aucun verrou. Le deck du bien doit donc
  lui être **proposé** (pas imposé : viser reste son coup), et Radio Halliwell
  doit dire, à chaque tour, quel état est à un coup d'être constatable.
