# Le découpage de la Prise de Port-Réal

Architecture du plan, et la méthode qui prouve qu'il ne manque rien. Ouvert le 26e jour de la 3e lune, an 129, à la Table Peinte.

Ce document est le **brief** : chaque titulaire y trouve le périmètre de son cahier, ce qu'il attend des autres, ce qu'il leur doit, et l'hypothèse qu'il a charge de guetter. Il ne remplace pas les cahiers de `etat/books.json` — il dit ce qu'on doit y écrire et pourquoi.

---

## 1. La méthode

La complétude ne se suppose pas, elle se **teste**. Cinq contrôles, chacun capable de faire apparaître un trou que les autres ne voient pas.

| # | Contrôle | Ce qu'il détecte |
|---|---|---|
| **C1** | **Couverture des fins** — chaque fin a ses conditions nécessaires identifiées | Une fin qu'on poursuit sans savoir de quoi elle est faite |
| **C2** | **Couverture des conditions** — chaque condition a au moins une affaire qui la produit | Une fin qui a un cahier dont le travail ne suffit pas causalement à l'obtenir |
| **C3** | **Couverture phase × acteur** — chaque interaction significative a un titulaire | Ce qui *nous arrive* plutôt que ce que *nous faisons* |
| **C4** | **Couverture des ruines** — chaque hypothèse critique a un observateur, un seuil et une décision | Un plan qui ne sait pas qu'il a cessé d'être viable |
| **C5** | **Couverture des dépendances** — chaque affaire déclare ses entrées et ce qu'elle débloque | Une affaire qui attend quelque chose que personne ne produit |

**C2 est le contrôle décisif.** « Chaque fin a un cahier » ne prouve rien : la chaîne à vérifier est *fin → conditions nécessaires → affaires → sorties observables*.

### Deux axes, et ils ne se mélangent pas

Les phases **ne partitionnent pas** les affaires : le secret, l'argent, le renseignement, le commandement et le soin traversent tout. Forcer une fonction permanente dans une phase produit un faux découpage.

- **Phases** — `AVANT` (avant le départ) · `MOUVEMENT` (le trajet) · `ARRIVÉE` (devant la ville) · `TRANSITION` (après la prise).
- **Fonctions persistantes** — `RENSEIGNEMENT` · `COMMANDEMENT` · `RESSOURCES` · `PROTECTION` · `INFORMATION` · `SOIN` · `SOUTIEN LOGISTIQUE`.

Une affaire porte **une phase dominante et zéro ou une fonction**. Une affaire à fonction non nulle vit dans toutes les phases par nature.

### Quatre familles

| Famille | Définition | Test |
|---|---|---|
| **MISSION** | Produit directement une condition de l'état final | Si elle réussit, une condition d'une fin devient vraie |
| **ENABLER** | Rend des missions possibles | Sa sortie est une **entrée** d'au moins deux missions |
| **ASSURANCE** | Détecte que le plan diverge ou devient impossible | Sa sortie est un **signal**, jamais un effet sur le monde |
| **CONTINGENCE / TRANSITION** | Répond aux bifurcations et à l'après | Elle ne s'exécute que si une condition se réalise, ou après la prise |

### Responsable ≠ exécutant

Deux colonnes distinctes, et c'est la correction la plus importante du modèle :

- **RESPONSABLE** — celui qui répond du résultat, tient le cahier et en écrit la conclusion. Il peut en porter quatre.
- **EXÉCUTANT** — celui dont les journées y passent. **Il ne peut pas en porter plus d'une à la fois** : une chaîne de travail occupe un homme.

Un responsable sans exécutant nommé est une affaire qui n'avancera pas, quel que soit le zèle du responsable.

---

## 2. Les onze fins, décomposées en conditions

`ce-quon-cherche-a-obtenir` donne les fins. Voici, pour chacune, **ce qui doit être vrai simultanément** pour qu'elle soit obtenue, et l'affaire qui produit chaque condition. Une condition sans affaire est un trou ; une condition produite par une affaire hors périmètre est une erreur de découpe.

### 📋 Le Compte — savoir ce qui est mobilisable
| Condition nécessaire | Produite par |
|---|---|
| Un chiffre par catégorie : hommes, coques, vivres, or, yeux | **5000** |
| Un porteur nommé par catégorie | **5000** |
| Le chiffre est daté et se refait à intervalle fixe | **5000** |
| Les forces de terre ont enfin un porteur *(trou déclaré au registre)* | **40000** |

### ⚓ Le Blocus — couper sans affamer
| Condition | Produite par |
|---|---|
| Le port est tenu | **22000** |
| Le fleuve est tenu | **22000** |
| La route du nord est fermée | **10000** |
| La population continue de manger | **13000** |
| Aucun renfort n'est détecté sur deux semaines | **31000** |

### 🏰 Le Ralliement — retourner les maisons
| Condition | Produite par |
|---|---|
| Savoir laquelle est retournable, et à quel prix | **21000**, entrée de **30000** |
| Une offre qui engage la parole de la reine | **21000** |
| Une bascule **publique** | **21000** |
| Le basculement ne coûte pas le secret | **32000** |

### 🗣️ La Rumeur — faire douter la ville
| Condition | Produite par |
|---|---|
| Des canaux dans la ville qui ne pointent pas vers nous | **6000** |
| Un contenu vérifiable par qui l'entend | **6000** |
| Un doute constaté **hors de nos propres canaux** | **6000** |
| Aucun canal ne remonte jusqu'à Peyredragon | **32000** |

### 🔑 Le Guet — les manteaux d'or
| Condition | Produite par |
|---|---|
| Un nom d'officier vivant et en poste | **7000** |
| Un contact établi avec lui | **7000** |
| Savoir ce qu'il veut, et ce qu'il craint | **7000** |
| Un canal sûr pour lui parler | **8000** *(la route du sel)* |

### 📆 Le Même Jour — les deux axes ensemble
| Condition | Produite par |
|---|---|
| Une date d'entrée fixée et connue des seuls responsables | **11000** |
| Chaque affaire a son **jour dû**, déduit à rebours de cette date | **11000** |
| Un moyen de décaler tout le monde en un geste si une pièce glisse | **11000** |
| Les ordres circulent assez vite pour que le décalage arrive à temps | **41000** |

### 🚪 La Porte Ouverte — entrer sans combat
| Condition | Produite par |
|---|---|
| Une porte physiquement ouvrable | **30000** |
| Quelqu'un pour l'ouvrir | **7000** |
| L'ost à portée **le même jour** | **20000** + **11000** |
| Le Guet neutre ou complice | **7000** |
| La ville qui ne se soulève pas au moment de l'entrée | **6000** + **13000** |
| Un ordre d'entrée écrit et un seuil de repli | **25000** + **36000** |

### 🕸️ Le Siège Isolé — le Donjon en poche
| Condition | Produite par |
|---|---|
| Aucune sortie possible | **12000** |
| Aucun secours par mer | **22000** |
| Aucun secours par terre | **10000** + **31000** |
| Le temps joue pour nous — on sait ce que le Donjon a en cave | **30000** |

### 🕯️ L'Homme de l'Intérieur
| Condition | Produite par |
|---|---|
| Un candidat avec un accès physique réel | **8000** |
| Un mobile — ce qu'il gagne, ce qu'il craint | **8000** |
| Un canal sûr, hors de toute roukerie | **8000** *(Nesse, la route du sel)* |
| Un signal convenu et testé des deux côtés | **8000** + **41000** |
| Rien ne lui est promis que la reine n'ait tranché | **24000** |

### 🏯 La Poterne — le Donjon sans assaut
| Condition | Produite par |
|---|---|
| L'homme de l'intérieur tient au jour dit | **8000** |
| Une équipe d'extraction | **23000** |
| Le noyau dur isolé du reste de la garnison | **12000** |
| Le verdict **déjà tranché** — l'action 23031 y est suspendue | **24000** |

### ⚖️ Le Verdict — le règne stable
| Condition | Produite par |
|---|---|
| Décision écrite et scellée **avant** la chute | **24000** |
| Connue du Conseil, et d'eux seuls | **24000** + **32000** |
| Exécutable — on tient les corps qu'elle vise | **37000** |
| Le royaume l'apprend dans notre version, la première | **34000** |
| Un an après, nos ordres sont toujours ceux qu'on exécute | **42000** |

**Résultat du contrôle C2** : quarante-huit conditions, toutes produites. Cinq d'entre elles sont produites par des affaires que le découpage précédent n'avait pas — **32000, 41000, 42000, 37000, 40000**. C'étaient des fins avec cahier dont le travail ne suffisait pas.

---

## 3. Les affaires — 32 cahiers

`R` = responsable (répond du résultat, écrit la conclusion) · `E` = exécutant (ses journées y passent).

### MISSIONS — 13

| Plage | Nom | Phase | Fonction | R | E |
|---|---|---|---|---|---|
| **4200** | Entrée sans bataille dans Port-Réal | ARRIVÉE | — | Aurore | Aurore |
| **6000** | Retournement de l'opinion populaire dans Port-Réal | AVANT→ARRIVÉE | INFORMATION | Alys Grive | Mysaria |
| **7000** | Identification et retournement du Guet des sept portes | AVANT | — | Aurore | ses yeux |
| **8000** | Recrutement d'un homme de l'intérieur du Donjon | AVANT | — | le Sanglier | Marna + Nesse |
| **10000** | Fermeture de la route terrestre du nord | ARRIVÉE | — | ser Robert | *à nommer* |
| **12000** | Isolement du Donjon Rouge de tout secours | ARRIVÉE | — | Denys Bar Emmon | *à nommer* |
| **13000** | Ravitaillement et ordre public de la ville coupée | ARRIVÉE→TRANSITION | — | Sara | Bry |
| **20000** | Déplacement de l'ost de Peyredragon à Port-Réal | MOUVEMENT | — | ser Robert | ser Steffon |
| **21000** | Retournement des maisons hésitantes des terres de la Couronne | AVANT | — | Jacaerys | Denys Bar Emmon |
| **22000** | Fermeture du port et du fleuve de Port-Réal | ARRIVÉE | — | Rulf Corne | Corlys |
| **23000** | Ouverture du Donjon Rouge sans assaut | ARRIVÉE | — | le Sanglier | *à nommer* |
| **25000** | Entrée et déploiement de l'ost dans les rues | ARRIVÉE | — | ser Steffon | ser Steffon |
| **34000** | Proclamation de la reine au royaume | TRANSITION | INFORMATION | Gerardys | Alys Grive |

### ENABLERS — 11

| Plage | Nom | Phase | Fonction | R | E |
|---|---|---|---|---|---|
| **5000** | État chiffré de ce qui est mobilisable | AVANT | RESSOURCES | Aldon Hask | Aldon Hask |
| **11000** | Synchronisation des affaires sur le jour d'entrée | *toutes* | COMMANDEMENT | Gerardys | Gerardys |
| **26000** | Plan de charge et de traversée de l'ost | MOUVEMENT | SOUTIEN LOG. | Aldon Hask | Rulf Corne |
| **27000** | Emploi des dragons au-dessus de Port-Réal | ARRIVÉE | — | Jacaerys | Jacaerys |
| **28000** | Financement de la campagne | *toutes* | RESSOURCES | Aldon Hask | *sous-clerc à nommer* |
| **29000** | Défense de Peyredragon pendant l'absence de l'ost | *toutes* | PROTECTION | ser Robert | Wend |
| **30000** | Relevé des murs, portes et garnison de Port-Réal | AVANT | RENSEIGNEMENT | Aurore | Marlo Vasse |
| **33000** | Ambassade du Nord, du Val et de Blancport | AVANT→MOUVEMENT | — | Jacaerys | Jacaerys |
| **35000** | Fenêtre de mer et de saison pour la traversée | MOUVEMENT | — | Rulf Corne | Rulf Corne |
| **40000** | Commandement et chaîne d'ordres pendant l'opération | *toutes* | COMMANDEMENT | la reine | ser Steffon |
| **41000** | Transmission des ordres et des nouvelles pendant l'opération | *toutes* | INFORMATION | Gerardys | Wend |

### ASSURANCE — 3

| Plage | Nom | Phase | Fonction | R | E |
|---|---|---|---|---|---|
| **31000** | Guet des osts verts et prévention du secours | *toutes* | RENSEIGNEMENT | Denys Bar Emmon | ses coureurs |
| **32000** | Protection du secret de l'entreprise | *toutes* | PROTECTION | le Sanglier | le Sanglier |
| **39000** | Veille des hypothèses, indicateurs et seuils du plan | *toutes* | COMMANDEMENT | Gerardys | Gerardys |

### CONTINGENCES ET TRANSITION — 5

| Plage | Nom | Phase | Fonction | R | E |
|---|---|---|---|---|---|
| **24000** | Décision sur le sort des vaincus et installation du règne | TRANSITION | — | Gerardys | Gerardys |
| **36000** | Conduite du repli si l'entrée échoue | ARRIVÉE | — | ser Steffon | ser Steffon |
| **37000** | Blessés, morts et prisonniers | ARRIVÉE→TRANSITION | SOIN | Gerardys | Sara |
| **38000** | Sûreté de la personne de la reine | *toutes* | PROTECTION | ser Steffon | *garde à nommer* |
| **42000** | Tenue de la capitale la première lune | TRANSITION | — | Sara | *à nommer* |

**Charge des responsables** : Gerardys 6, Hask 3, ser Robert 3, Jacaerys 3, le Sanglier 3, ser Steffon 3, Sara 2, Aurore 3, Rulf 2, Denys 2, Alys 1, la reine 1.
**Charge des exécutants** : aucune surcharge sauf **Gerardys (4 chaînes) et ser Steffon (4)** — à résoudre en leur donnant des exécutants, pas en coupant des affaires.
**Six exécutants restent à nommer** : c'est le vrai trou du plan, et il est de personnel, pas d'architecture.

---

## 4. Le contrôle phase × acteur

| | **Nous** | **La ville** | **Le Donjon** | **Les Verts au-dehors** | **Les neutres** |
|---|---|---|---|---|---|
| **AVANT** | 5000 · 28000 · 27000 · 29000 · 40000 | 30000 · 6000 | 30000 · 8000 | 31000 | 21000 · 33000 |
| **MOUVEMENT** | 20000 · 26000 · 35000 | 6000 | — | 31000 | 33000 |
| **ARRIVÉE** | 25000 · 22000 · 10000 · 11000 · 36000 | 7000 · 13000 | 12000 · 23000 · 4200 | 31000 | — |
| **TRANSITION** | 24000 · 34000 · 37000 · 38000 | 42000 · 13000 | 37000 | 31000 | 34000 |
| *transversal* | 32000 · 39000 · 41000 | | | | |

Vingt cases, toutes occupées, aucune par défaut.

---

## 5. Les hypothèses du plan — le mécanisme de contrôle

Une catastrophe listée n'est qu'une inquiétude. Ce qui la rend utile, c'est le quadruplet. **Ce tableau est le contenu du cahier 39000**, et son responsable le relit tout haut au conseil du premier jour de chaque lune.

| # | Hypothèse — ce que le plan suppose vrai | Indicateur | Seuil | Décision à reconsidérer | Observateur |
|---|---|---|---|---|---|
| **H1** | Aucun ost vert n'atteint Port-Réal avant nous | Position d'Ormund et de Criston, par les yeux | À moins de **12 jours de marche** | Avancer la date d'entrée, ou renoncer à l'entrée sans bataille | 31000 |
| **H2** | Otto ignore que nous préparons une entrée | Renforcement des portes ; arrestations en ville | **Une seule** arrestation d'un de nos contacts | Brûler le canal, replier sur la poterne seule | 32000 |
| **H3** | La ville a de quoi manger | Prix du pain aux marchés | **Doublement** | Ouvrir un convoi, ou relâcher le fleuve | 13000 |
| **H4** | La mer permet la traversée à la date fixée | Rapport de Rulf, trois jours avant | **Deux jours** de vent contraire | Décaler tout le monde par 11000 | 35000 |
| **H5** | Nous pouvons payer jusqu'au bout | Solde du livre de Hask | Moins de **30 jours** de campagne en caisse | Emprunter à Celtigar, ou raccourcir l'opération | 28000 |
| **H6** | Peyredragon tient sans l'ost | Le plancher dit tout haut chaque matin | Sous **120 hommes** | Ne pas embarquer la dernière vague | 29000 |
| **H7** | Le Guet n'obéit plus vraiment à Aegon | Un nom d'officier, et sa réponse | **Pas de nom au jour J−20** | Renoncer à la porte ouverte, revenir au siège long | 7000 |
| **H8** | Nesse peut porter et se taire | La réponse de Bec-de-Fer au premier pli | **Deux passages** sans réponse (16 jours) | Ouvrir un second canal | 8000 |
| **H9** | La reine est en état de conduire l'affaire | Sa condition, dite sans complaisance | *à fixer par elle* | Régence de Daemon, ou report | 38000 |
| **H10** | L'entrée peut se faire sans combat | Premiers rapports au point d'entrée | *seuil de repli à écrire* | Déclencher 36000 | 36000 |
| **H11** | Les dragons restent une menace, pas un emploi | Ce que la ville croit de nous | Une maison brûlée | Le ralliement est mort ; changer de fin | 27000 |

**H11 n'était dans aucune version précédente**, et c'est la plus dangereuse : le plan repose sur « ralliement plutôt que conquête », et un seul emploi mal jugé des dragons rend les fins *Ralliement* et *Rumeur* inatteignables du même coup.

---

## 6. Le graphe des dépendances

Lecture : `A → B` = A doit rendre avant que B puisse tenir son jour dû.

```
                            ┌──────────── 39000 veille des hypothèses ────────────┐
                            │            (observe tout, ne produit rien)          │
                            └────────────────────────────────────────────────────┘

5000 compte ──┬─→ 26000 charge ──→ 20000 marche ──┬─→ 25000 entrée ost ──→ 42000 tenue
              ├─→ 28000 argent ──→ (toutes)        │
              └─→ 40000 commandement ──────────────┘
                                                   ▲
35000 fenêtre de mer ──────────────────────────────┘

30000 relevé des murs ──┬─→ 7000 Guet ──┬─→ 4200 entrée sans bataille ──→ 25000
                        └─→ 8000 homme de l'intérieur ──→ 23000 poterne ──→ 24000 verdict
                                    ▲                          ▲
                        41000 transmission ──┘        12000 isolement ──┘

6000 opinion ──┬─→ 4200            22000 port+fleuve ──┬─→ 12000
21000 maisons ─┘                   10000 route ────────┘
33000 ambassade ──→ (renforce 21000, hors calendrier d'entrée)

24000 verdict ──→ 34000 proclamation ──→ 42000 tenue
37000 corps ────→ 24000 (exécutable)

32000 secret ──→ conditionne 6000, 7000, 8000, 21000  (son échec les tue toutes)
31000 guet des verts ──→ conditionne la DATE de tout   (H1)
11000 synchronisation ──→ tient le jour dû de toutes
36000 repli ← se déclenche depuis 25000, 4200, 23000
38000 sûreté ──→ conditionne la présence de la reine à l'entrée
29000 défense de Peyredragon ← contrainte sur 26000 (dernière vague)
27000 dragons ──→ appui de 22000 et 12000, MENACE sur 6000 et 21000 (H11)
```

**Trois affaires sont des points de rupture** — leur échec ne dégrade pas le plan, il l'annule :
- **32000** le secret — tue quatre missions d'un coup ;
- **11000** la synchronisation — sans elle, chaque affaire réussit un jour différent, ce qui équivaut à échouer ;
- **5000** le compte — rien en aval ne peut se calendariser sans lui, et c'est pour ça qu'il part le premier.

---

## 7. Deux règles de coupe, à inscrire en tête de chaque cahier

1. **Une action tient dans la journée d'un homme.** Si une ligne demande trois semaines et quatre corps de métier, ce n'est pas une action : c'est une affaire, et elle a droit à son cahier.
2. **Chaque action porte un nom et un jour dû**, le jour se déduisant à rebours du jour d'entrée (cahier 11000). Une action sans nom n'a pas été décidée ; une action sans jour ne se synchronise pas.

## 8. Ce que le découpage ne règle pas

- **Six exécutants ne sont pas nommés** (10000, 12000, 23000, 28000, 38000, 42000). C'est un manque de personnel, pas d'architecture — mais ces six affaires n'avanceront pas d'un jour tant qu'il dure.
- **Gerardys porte six responsabilités et quatre chaînes de travail.** Il faut lui prendre 34000 et 37000, ou lui donner un second.
- **La date d'entrée n'existe pas encore.** Tant que 11000 n'a pas posé un jour, tous les « jours dûs » sont vides et le plan reste une liste de sujets — ce qui est exactement le reproche d'origine.
