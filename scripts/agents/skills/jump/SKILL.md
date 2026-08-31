---
name: jump-scene
description: Résoudre un Jump du MJ depuis la complétion du sous-graphe causal jusqu'aux mises à jour des PNJ et au jeu immédiat d'une unique scène cible.
---

# Jump — fermer le chemin critique et jouer une scène

Utilise ce skill uniquement quand le brief porte le mode `jump`. Le bloc
`ROUTAGE` donne l'unique événement cible, son sous-graphe et le numéro de
contexte MJ. Le Jump n'est pas une décision du personnage joueur : le MJ
résout les décisions et les tests qui verrouillent la scène.

## Contrat de sortie

- Un seul événement cible et une seule scène jouée.
- La cible est située au moins 24 heures après la date de départ du Jump.
- Aucune question, option ou décision préparatoire remontée au joueur.
- Au plus trois PNJ dépêchés sur la coupe critique entière.
- Aucune parole ni décision de PNJ inventée par le MJ.
- Toutes les dépêches et tous les messages portent le `contexte_id` du Jump.
- La scène substantielle est poussée dans le flux avant de rendre la main.
- Le flux reste vivant pendant le travail et la montre atteint réellement la
  date de la cible.
- Une tranche intermédiaire n'est jamais une fin : le même réveil poursuit le
  Jump jusqu'à l'événement appliqué et la scène jouée.
- Ne rends pas la main au milieu du Jump, même après avoir poussé une tranche
  visible ou reçu un premier retour.

Un `contexte_id` absent est un verrou technique : crée ou répare d'abord le
moment MJ de l'événement. Ne dépêche jamais un homme hors contexte.

Les 24 heures sont un minimum dur, y compris quand un identifiant d'événement
est demandé explicitement. Un événement plus proche reste un jalon causal à
résoudre pendant l'avancée ; il ne devient pas une seconde scène de Jump. Ne
décale jamais sa date canonique pour satisfaire ce seuil. S'il doit être joué
avant, rends-le à `Play` ou `Advance`. S'il n'existe aucune cible admissible,
le Jump refuse de partir.

## 1. Compléter le sous-graphe

Relis le graphe de la cible fournie :

```bash
python scripts/graphe_causal.py --event <event_id>
```

Si `complet` est faux, traite chaque entrée de `trous` selon son `type`. Le
trou est une lacune de modèle, pas une permission d'inventer un fait.

- `condition_non_adressee` : crée une condition causale explicite à évaluer.
- `cause_absente` ou `evenement_isole` : déclare une racine seulement si
  l'absence d'antécédent encodé est bien le fait à représenter.
- `extremite_absente` : retrouve l'adresse canonique manquante dans la source ;
  ne remplace jamais un identifiant inconnu par une personne ou un objet
  vraisemblable.
- `inference_a_confirmer` : trouve la preuve explicite, ou conserve
  explicitement le statut d'inférence et transforme son issue en test ou en
  arbitrage MJ. Ne la présente pas comme un fait établi.

Pour les compléments mécaniques, examine d'abord l'aperçu, puis écris :

```bash
python scripts/graphe_causal.py --event <event_id> --completer
python scripts/graphe_causal.py --event <event_id> --completer --vraiment
```

Les compléments vivent dans
`chambres/mj/graphe-causal-complements.json`. Toute correction manuelle y
conserve le type épistémique, sa source et `resout_trou`; elle ne modifie pas
`etat/tissu` pour maquiller la trajectoire. Relance l'extraction après chaque
passe. Le graphe est prêt quand chaque trou est soit fermé par une adresse
réelle, soit porté explicitement par un test ou un arbitrage MJ. Une inconnue
qui peut changer l'issue ne disparaît jamais sous une racine de convenance.

## 2. Élire la coupe critique

Pars de l'événement et remonte seulement jusqu'aux premières décisions ou
tests non résolus qui empêchent de jouer la scène maintenant. Cette frontière
est la coupe critique. Ignore l'amont déjà résolu et les branches qui ne
changent ni l'arrivée, ni le lieu, ni les présents, ni l'enjeu immédiat.

Pour chaque verrou de la coupe, désigne son solveur :

- un PNJ si la réponse est un fait de son domaine ou sa propre décision ;
- le MJ si c'est un test de monde, un hasard, une collision entre sources ou
  une décision d'arbitrage ;
- jamais le joueur.

Regroupe plusieurs questions chez le même homme lorsqu'elles appartiennent à
la même affaire. Garde au plus trois hommes au total. Si la scène exige plus
de trois voix, la coupe n'est pas assez proche de l'événement : rapproche-la.

## 3. Dépêcher les hommes

Initialise d'abord la petite file temporaire du Jump avec les hommes élus :

```bash
python scripts/jump_beats.py --initialiser --event <event_id> --contexte <contexte_id> --ref <ref_joueur> --homme <id> [--homme <id>]
```

Compose une seule mission courte qui nomme, pour chaque homme, sa question
fermable, avec l'objet, la date et ce qu'elle verrouille. Chacun ne répond
qu'à la ligne qui porte son nom. Demande un fait ou sa décision, jamais la
réplique que la scène voudrait entendre. Lance ensuite toute la coupe dans
**une seule commande parallèle**, avec au plus trois `--qui` et `--front 3`.
Ne fais jamais trois commandes successives : le temps de la coupe est celui
du retour le plus lent, pas la somme des trois. `--beats-jump` fait joindre à
chaque réponse jusqu'à trois battements courts, déjà écrits par son auteur et
rattachés au sous-graphe :

```bash
python scripts/depecher.py --qui <id_1> [--qui <id_2>] [--qui <id_3>] --front 3 --contexte <contexte_id> --ref <ref_joueur> --mode reponse --beats-jump --event-jump <event_id> --mission "<id_1>: <question exacte>. <id_2>: <question exacte>. Chacun répond seulement à sa ligne."
```

Attends le retour de cette commande unique avant d'arbitrer. Un silence, une
fourchette ou un désaccord reste une donnée. N'invente pas la réponse manquante
et ne lance pas une journée entière. Si aucun homme n'est nécessaire, passe
directement à l'arbitrage MJ.

### Meubler pendant les appels

Après le retour parallèle, pousse au plus un beat préparé avant l'arbitrage :

```bash
python scripts/jump_beats.py --pousser --contexte <contexte_id> --ref <ref_joueur>
```

La file choisit mécaniquement le premier beat encore disponible. Le MJ n'en
réécrit ni la parole ni le geste : son auteur est conservé dans le flux avec
les nœuds causaux qui l'autorisent. Une file vide rend `null`, ce n'est pas un
motif pour fabriquer un beat.

Ne laisse pas l'écran mort pendant les lectures, dépêches et arbitrages. Pousse
au fur et à mesure de courtes tranches de continuité : le lieu, la lumière, la
matière déjà présente, le bruit, la montre, une attente physiquement vraie ou
le déplacement déjà engagé. Ces tranches peuvent avancer de quelques minutes
avec leur `duree`, mais elles ne révèlent jamais la régie, le graphe ou les
tests au joueur. Elles ne font parler ni agir un PNJ sans retour réel et ne
font pas agir le personnage joueur.

Une tranche de décor est un maintien de scène, pas la sortie du Jump. Après
l'avoir poussée, reprends immédiatement le travail causal dans le même réveil.

Le meublage doit aussi donner envie d'attendre la suite. Sème des sous-entendus
et des signes excitants tirés de ce qui est déjà vrai dans le graphe, les
sources ou les retours : une place laissée vide pour un nom attendu, un chiffre
qui ne tombe pas encore juste, une marque déplacée sur la carte, une échéance
physique qui approche, deux objets dont le rapprochement annonce une collision,
un bruit ou une absence dont le sens deviendra clair dans la scène cible. Fais
sentir l'enjeu sans l'expliquer et montre la conséquence avant d'en donner la
cause.

Chaque signe doit pouvoir être relié à un nœud, une condition ou un fait réel.
N'invente ni présage omniscient, ni faux danger, ni réaction secrète d'un PNJ
pour rendre l'attente plus spectaculaire. Une bonne amorce promet la scène
cible ; elle n'ouvre pas un nouveau fil narratif et ne révèle pas son verdict.

## 4. Arbitrer et écrire le résultat

Avant d'écrire le verdict, expire ce qui n'a pas été utilisé : un beat préparé
avant l'arbitrage ne doit jamais être recyclé après que la situation a changé.

```bash
python scripts/jump_beats.py --fermer --contexte <contexte_id> --ref <ref_joueur>
```

Résous les tests du monde et les contradictions depuis les sources et les
règles existantes. Pour chaque nœud de la coupe, écris un verdict bref :
`résolu`, `échoué` ou `dévié`, avec sa source, sa date et l'effet sur la cible.
Porte le résultat dans le complément causal ou dans la source canonique qui
possède réellement cette décision. Ne change pas rétroactivement la réponse
d'un homme.

Réextrais le graphe. Il doit maintenant donner un chemin causal lisible
jusqu'à l'événement et aucune décision de joueur. Si une branche échoue,
applique sa déviation déjà modélisée ; à défaut, le MJ arbitre la conséquence
la plus locale et la consigne comme telle. L'événement cible peut changer de
forme, mais le Jump ne saute pas vers l'événement suivant.

## 5. Mettre les PNJ concernés à jour

Une fois l'arbitrage écrit, informe chaque PNJ dont les croyances, le mandat,
la date ou le travail changent. Ce sont des messages du monde, pas des
instructions de dialogue :

```bash
python scripts/parloir.py --dire --sans-reveil --de mj --a <id> --contexte <contexte_id> --ref <ref_joueur> "<fait ou décision datée qui change son travail>"
```

Informe aussi un acteur affecté qui n'a pas été dépêché si le verdict change
ce qu'il doit faire. `--sans-reveil` est obligatoire ici : la notification
reste dans son canal jusqu'à son prochain réveil naturel et ne lance aucune
`journee`. Elle ne doit donc produire ni accusé de réception, ni ping-pong de
billets, ni nouvelle branche du Jump. N'envoie ni résumé général, ni message
au joueur par cette porte. Si sa réaction est indispensable à la scène,
obtiens-la par une dépêche `--mode reponse` comprise dans la limite des trois
hommes ; sinon il poursuivra hors champ à son prochain réveil.

## 6. Avancer jusqu'à la cible

Calcule d'abord ce qui tombe jusqu'à la date exacte de l'événement :

```bash
python scripts/tick.py --jusqu-a <annee.lune.jour>
```

Lis le calcul, puis applique dans les propriétaires canoniques les mains, les
échéances, diffusions, actes et effets qui se produisent avant ou avec la
cible. Les événements compris dans les 24 premières heures sont donc traités
comme jalons intermédiaires du chemin causal, jamais comme nouvelles scènes
cibles. Mets l'événement cible à l'état résolu lorsqu'il s'est effectivement
produit. Ne marque jamais comme accompli ce que la coupe a fait échouer ou
dévier. Le joueur ne reçoit que ce qui peut réellement lui parvenir.

La clock doit avancer pour de vrai : les petites tranches font progresser les
minutes par leur `duree`, puis la première tranche de transition vers la cible
porte sa `date` complète, minute comprise. Ne te contente jamais de raconter
que le temps a passé en laissant `monde.date` avant la cible. Vérifie après la
poussée que l'heure estampillée dans le flux a atteint la date de l'événement.

## 7. Jouer immédiatement la scène

Pousse la première tranche avec la date complète de la cible afin que
`append_flux.py` place la montre, puis joue la scène en items courts. Les mots
des PNJ viennent uniquement de leurs retours réels ; le MJ fournit le lieu,
les gestes, le rythme et les conséquences.

La sortie minimale contient un item substantiel parmi `recit`, `replique`,
`geste`, `evenement`, `salle`, `table` ou `marque`. Joue l'enjeu produit par
la trajectoire, pas un rapport sur la préparation. Un décor d'attente, une
porte qui s'ouvre, un « ils arrivent » ou une mise à jour d'état ne suffisent
pas : continue sans rendre la main jusqu'au battement où l'événement se joue
réellement. Alors seulement, rends la main au joueur. Ne prépare, ne résout et
ne joue aucun événement suivant.

## Garde finale

Avant de finir, vérifie : graphe fermé ou inconnue explicitement arbitrée,
trois PNJ maximum, retours réels, résultats écrits, PNJ affectés informés,
événement appliqué, scène visible dans le flux, aucune décision joueur et
aucun second événement entamé. Si l'un de ces points manque, le Jump est en
cours : poursuis-le dans ce même réveil au lieu de conclure ou d'annoncer une
suite.
