# La carte des données

Ce document est **dérivé** : il recense, donnée par donnée, ce que les 53 fiches
de ce dossier déclarent — qui est l'écrivain unique, qui lit, et de quelle
nature est la donnée. Il ne décide rien : chaque ligne se vérifie contre la
fiche qu'elle cite, et une ligne fausse se corrige dans la fiche d'abord.
Établi le 2026-08-27 par dépouillement intégral ; à refaire après toute retouche
des sections « Ce qu'il possède / lit / produit ».

Il est aussi autre chose : [`sondes`](90-observation/sondes.md) exige « un seul
écrivain par donnée du **tableau de propriété** » — tableau qu'aucun module ne
possédait et qui n'existait nulle part. Le voici. La sonde a désormais quoi
lire, et le premier passage du tableau relève **quinze propriétés contestées et
un mécanisme jamais défini** (en fin de document).

La nature d'une donnée reprend le cycle du jeu : **vérité** (l'état du monde,
un seul écrivain, personne d'autre), **croyance** (ce qu'un acteur en sait —
daté, sourcé, faillible), **intention** (ce qu'un acteur veut — révocable,
peut échouer), **référence** (formes, barèmes, vocabulaires — sans état, même
réponse toujours), **hors-jeu** (l'observation — lit tout, n'écrit rien
dedans). ⚠ marque une propriété contestée entre fiches, ❓ un écrivain que la
fiche ne déclare pas.

---

## Vérité — un seul écrivain, et le monde fait foi

| donnée | écrivain | lecteurs déclarés | |
|---|---|---|---|
| géométrie du sol, obstacles, franchissabilité (3 états), coût du pas | [terrain](20-monde/terrain.md) | bâti, seuils, navigation, mouvement, contact, dangers, densité, portées, vue, ouïe… | |
| inventaire des bâtiments, ouvertures, intérieur, occupation | [bati](20-monde/bati.md) | seuils, navigation, dangers, vue, ouïe | ⚠ l'empreinte est *déclarée* ici mais *inscrite* au terrain — double vérité assumée par la fiche, fragile |
| inventaire des seuils, largeur, débit, état, file | [seuils](20-monde/seuils.md) | navigation, mouvement, contact, densité, dangers, estimation… | ⚠ le lien bâtiment↔seuil est écrit des deux côtés (bâti possède « ses » seuils, seuils sait ce qu'il dessert) |
| graphe de circulation, routes calculées, invalidation | [navigation](20-monde/navigation.md) | mouvement, projection, options, porteur | ❓ « groupe conducteur » : notion utilisée, définie nulle part ; ❓ qui déclenche la reconstruction du graphe |
| position, orientation, vitesse, état de marche de chaque corps | [mouvement](20-monde/mouvement.md) | tout ce qui perçoit ; cohésion | ⚠ l'orientation est aussi revendiquée par vue |
| plafond d'allure d'un corps | [mouvement](20-monde/mouvement.md) **et** [densite](20-monde/densite.md) | — | ⚠ deux écrivains déclarés, articulation non écrite |
| emprise, état de contact, pression | [contact](20-monde/contact.md) | coup, densité, ouïe | ⚠ cinq fiches citent « la collision », module qui n'existe pas ; l'équivalence contact = collision n'est déclarée nulle part |
| vie, blessures, mort, résolution d'un coup | [coup](20-monde/coup.md) | rupture, chef, mouvement (plafond) | ⚠ « nulle part ailleurs » — contredit par dangers (« la collision seule écrit vie et blessure ») et par mesures (possède « points de vie ») |
| densité en un point, issues, marge de recul | [densite](20-monde/densite.md) | vue, mouvement, réflexion, rendu | |
| dangers actifs, propagation, quatre émissions, atteinte au décor | [dangers](20-monde/dangers.md) | portées, vue, ouïe, terrain/bâti/seuils (inscription) | ⚠ « atteinte au décor » possédée ici alors que « le propriétaire inscrit » — registre ou état, non tranché |
| émissions sonores en cours, bruit de fond | [ouie](30-perception/ouie.md) | canal | ❓ possédé ou dérivé du monde ? la fiche lit contact, mouvement, dangers pour le produire sans trancher |

## Identité — la vérité sociale, posée une fois

| donnée | écrivain | lecteurs déclarés | |
|---|---|---|---|
| identifiant, camp, métier, arme, trempe, main, acquis d'un homme | [identite (40)](40-combattant/identite.md) | les 4 couches, l'arbitre, la mémoire, cohésion, allure, chef, rupture | ⚠ le répertoire fermé de gestes est aussi possédé par corps ; ⚠ la « portée d'emploi de l'arme » heurte « un seul barème » de portées |
| identifiant, membres, parent, rang, camp d'une unité | [identite (50)](50-unite/identite.md) | chef, forme, cohésion, allure, rupture, détachement, commandement | ⚠ sort un détaché de la liste, ce que detachement interdit (« un détaché reste membre ») |
| chef courant, ordre de succession, fait de succession | [chef](50-unite/chef.md) | forme, cohésion, rupture, allure, ordre, porteur | |
| état de détachement (messager, éclaireur…), terme, compte | [detachement](50-unite/detachement.md) | forme, cohésion, observation — qui ne le déclarent pas en retour | ⚠ porteur (60) est un détaché sans lien déclaré avec ce module |

## Croyance — daté, sourcé, faillible

| donnée | écrivain | lecteurs déclarés | |
|---|---|---|---|
| champ de vision, hauteur d'œil, paliers de distinction | [vue](30-perception/vue.md) | rendu | ⚠ orientation : écrite par mouvement, « possédée » ici ; ❓ les modificateurs (fatigue, âge, perchoir) promis par portées n'y figurent pas |
| faits produits (vue, ouïe), « je ne vois rien », silence anormal | [vue](30-perception/vue.md), [ouie](30-perception/ouie.md) | remis à la mémoire du témoin | ❓ le contenu compris d'un ordre crié n'est ni possédé ni produit nulle part — tension connue, toujours ouverte |
| mémoire d'un homme : ordre reçu, chef connu, pairs, historique borné | [memoire](40-combattant/memoire.md) | interprétation, réflexion, envie | ⚠ l'ordre reçu y est *écrit par la couche 60* — écriture descendante sans mécanisme déclaré |
| carte d'un commandant : positions crues, intervalles, zones inconnues, âge et confiance | [croyances](70-commandement/croyances.md) | estimation, options, projection, décision, objectif, allocation | ✅ seule donnée du dossier avec écrivain unique nommé et incontesté (« personne d'autre ne l'écrit ») |
| estimation : rapport de force cru, menace, vulnérabilité, inconnues décisives | [estimation](70-commandement/estimation.md) | options, projection, décision | |
| ce que le porteur croit de son destinataire, ce qu'il a vu en route | [porteur](60-transmission/porteur.md) | canal, croyances (au retour) | |
| force disponible telle que crue (recopie datée des croyances) | [allocation](80-conduite/allocation.md) | réserve | ✅ la recopie est déclarée comme telle — le bon geste |

## Intention — révocable, et peut échouer

| donnée | écrivain | lecteurs déclarés | |
|---|---|---|---|
| propositions des couches 1-4 (mot du corps, issue, barre, envie) | [corps](40-combattant/corps.md), [reflexion](40-combattant/reflexion.md), [interpretation](40-combattant/interpretation.md), [envie](40-combattant/envie.md) | l'arbitre, et lui seul | ❓ le répertoire d'issues de la réflexion n'est pas déclaré fermé, et recoupe celui du corps (« se ranger », « se dégager ») |
| élection, trace d'arbitrage, inertie | [arbitre](40-combattant/arbitre.md) | geste, écran, sondes | ❓ ce qui est produit quand les quatre s'abstiennent |
| intention de geste, remise au monde | [geste](40-combattant/geste.md) | le monde, et lui seul | ⚠ « sa raison » est déclarée possédée mais recopiée de l'arbitrage |
| forme demandée, assignations, écart de forme | [forme](50-unite/forme.md) | mémoire des hommes (contrainte remise), cohésion | ⚠ **l'ancre** : possédée par forme, « lue dans identite/chef », niée par identite — trois fiches, aucune d'accord |
| allure du guide, règle d'adaptation | [allure](50-unite/allure.md) | le guide | |
| état de rupture (4 états), usure, seuil, hystérésis | [rupture](50-unite/rupture.md) | commandement, observation | ⚠ lit « l'état vital via identite (50) », qui déclare ne pas lire le monde |
| forme d'un ordre, vocabulaire clos des verbes, cycle de vie, préséance | [ordre](60-transmission/ordre.md) | décision (rédige), mission, mémoire | ⚠ l'état *porté/remis* est aussi écrit par message et par canal — trois écrivains ; ⚠ « l'ordre courant d'un homme » disputé entre ordre (60), memoire (40) et forme (50) |
| message : forme, contenu, versions émise/remise, statut, altérations | [message](60-transmission/message.md) | croyances, mémoire | ⚠ les altérations « viennent du canal et du porteur » tout en étant possédées ici |
| course du porteur, son état, sa conduite d'échec | [porteur](60-transmission/porteur.md) | canal, détachement (jamais déclaré) | |
| choix, justification, pondération du chef, prochain examen | [decision](70-commandement/decision.md) | conduite, trace | ⚠ « la trace complète, produite ici » — que trace-de-decision (90) attribue à l'acteur en n'en possédant que la forme et le recueil |
| engagements entre chefs, réallocation bornée | [coordination](70-commandement/coordination.md) | croyances des deux chefs | ❓ qui écrit le « fait reçu » dans les croyances de l'autre |
| buts, poids, pertes acceptables, horizon | [objectif](80-conduite/objectif.md) | mission, allocation, réserve | ❓ qui pose les buts initiaux (scénario ? joueur ?) — hors moteur, non déclaré |
| missions (3 formes), conditions, état | [mission](80-conduite/mission.md) | allocation, réserve, transmission | ⚠ « libère la force qu'elle immobilisait » — dans un registre que seule allocation écrit |
| registre d'affectation, part libre | [allocation](80-conduite/allocation.md) | réserve, conduite | |
| composition de la réserve, conditions d'engagement | [reserve](80-conduite/reserve.md) | allocation | ❓ qui écrit le passage part libre → réserve constituée ; ❓ qui décide de la constituer |

## Référence — sans état, même réponse toujours

| donnée | écrivain | lecteurs déclarés | |
|---|---|---|---|
| formes des objets échangés, vocabulaires fermés, versions | [formes](10-socle/formes.md) | tous | ❓ la liste exacte des formes possédées n'est pas énumérée |
| état du générateur, graine, compte des tirages | [hasard](10-socle/hasard.md) | coup, navigation, canal, message, porteur, propagation | |
| instant, pas, numéro de battement, calendriers de décision | [horloge](10-socle/horloge.md) | tous | ⚠ la dérivation depuis un identifiant est aussi revendiquée par identite (10) |
| compteurs d'identifiants, fonction de dérivation | [identite (10)](10-socle/identite.md) | tous | |
| anneaux d'événements et de décisions, dernière décision par acteur | [journal](10-socle/journal.md) | observation | ❓ « de quoi signaler » : cité par la moitié du monde sans jamais nommer ce module |
| la liste des modules, leur couche, leur rang, les ensembles | [manifeste](10-socle/manifeste.md) | étalon, sondes, câblage | |
| grandeurs d'homme (allures, allonges, épaules…) | [mesures](10-socle/mesures.md) | tous | ⚠ « points de vie » heurte la propriété de coup |
| barème des portées, facteurs de conditions, fraction de confiance, effet des obstacles | [portees](30-perception/portees.md) | vue, ouïe, canal, chef | ❓ seule fiche sans « Ce qu'il produit » : l'interface n'est déclarée nulle part |
| forme du fait, vieillissement, comparaison de deux faits | [fait](30-perception/fait.md) | vue, ouïe, mémoire, croyances | |
| catalogue des canaux, ce que chacun déforme, accusés | [canal](60-transmission/canal.md) | coordination, décision, mission | |
| catalogue clos des options d'un chef | [options](70-commandement/options.md) | projection, décision | ❓ « le même pour tous » — possédé ici ou référence partagée, non déclaré |

## Hors-jeu — lit tout, n'écrit rien dedans

| donnée | écrivain | lecteurs déclarés | |
|---|---|---|---|
| conditions d'étalon, relevés de référence, empreinte de chaîne | [etalon](90-observation/etalon.md) | — | |
| marques (six blocs recopiés, coupe déclarée) | [marque](90-observation/marque.md) | — | |
| listes d'affichage, états d'affichage, empreinte servie | [rendu](90-observation/rendu.md) | — | ❓ empreinte servie vs empreinte de chaîne : même donnée ou deux ? |
| définitions des sondes, relevés, plafonds | [sondes](90-observation/sondes.md) | — | |
| forme et recueil des traces de décision | [trace-de-decision](90-observation/trace-de-decision.md) | rendu | ⚠ conflit avec decision (70) ; ❓ le « score » d'une option figure dans la trace alors qu'options dit « aucun score » et que projection ne pondère pas — aucun module ne l'écrit |

---

## Les quinze propriétés contestées

Relevées ci-dessus au fil des tables, regroupées ici parce que c'est la liste
de travail : chacune se tranche en corrigeant une ou deux fiches, et chacune
est exactement le genre de divergence que la sonde « un seul écrivain » devra
refuser.

1. **La collision n'existe pas** — citée par densité, dangers, mouvement,
   seuils, terrain ; c'est contact, mais aucune fiche ne le dit.
2. **Vie et blessures** — coup, dangers (via « la collision ») et mesures
   (« points de vie ») : trois prétendants.
3. **Le plafond d'allure** — mouvement et densité le possèdent tous deux.
4. **L'orientation d'un corps** — écrite par mouvement, « possédée » par vue.
5. **L'ancre d'une unité** — possédée par forme, lue « chez » identite/chef,
   niée par identite.
6. **Détaché : membre ou pas** — identite le sort de la liste, detachement
   l'y garde. Contradiction frontale.
7. **Le statut remis/porté** — écrit par ordre, message et canal.
8. **L'ordre courant d'un homme** — ordre (60) en écrit seul l'état, memoire
   (40) le possède, forme (50) y « remet » des contraintes.
9. **Le répertoire fermé de gestes** — corps et identite (40).
10. **La portée d'emploi de l'arme** — identite (40) contre « un seul barème ».
11. **Les altérations d'un message** — possédées par message, produites par
    canal et porteur.
12. **La trace de décision** — « produite ici » (decision, 70) contre « la
    forme et le recueil » (trace-de-decision, 90).
13. **Le score d'une option** — présent dans la trace, désavoué par options et
    projection : écrivain introuvable.
14. **Part libre → réserve** — la bascule n'a pas d'écrivain entre allocation
    et reserve ; même trou pour la libération qu'opère mission.
15. **La dérivation depuis un identifiant** — horloge et identite (10).

## Le mécanisme jamais défini : la remise

Le motif le plus lourd n'est pas une contestation locale, il est systémique.
La règle de dépendance interdit de lire vers le haut ; les fiches la
contournent partout par le même geste, jamais défini : **la remise** — une
couche haute écrit dans une donnée d'une couche basse, ou une couche basse
« rend sans destinataire ».

- perception (30) *remet* un fait à la mémoire du témoin (40) ;
- geste (40) *remet* l'intention au monde (20) ;
- transmission (60) *remet* l'ordre reçu à la mémoire (40) ;
- contact et densité (20) *remettent* correction et plafond au mouvement (20),
  qui ne les déclare pas en lecture ;
- coordination (70) fait entrer des faits dans les croyances de l'autre chef ;
- forme (50) *remet* une contrainte « comme élément de l'ordre » d'un homme.

Six occurrences, zéro définition : ni qui appelle qui, ni ce qu'une remise a
le droit de contenir, ni comment elle respecte la règle de dépendance. C'est
la moitié montante du cycle vérité → croyance → intention → vérité, et elle
passe sous le tapis pendant que la moitié descendante (la lecture) a une règle
vérifiable par script. Tant que la remise n'a pas sa fiche de principe — au
même rang que [la règle de dépendance](00-principes/01-regle-de-dependance.md)
— chaque flèche montante du système repose sur une convention orale.
