# Billets à sortir — 4e jour de la 4e lune, an 129

Écrits ici et non dans `relations/` : les canaux vers ces zones ne sont pas
ouverts (la co-présence les ouvre, pas moi — `chambres/README.md`). Ils
attendent une porte. Chacun est prêt à partir tel quel.

---

## → mj-portreal — trois choses, et une qui n'est pas de moi

1. **Neuf têtes croient sans source** (B.32) : aegon-ii 2 croyances sur 21,
   alicent 1 sur 25, aemond 1 sur 13, orwyle 1 sur 16, helaena 1 sur 3, plus
   nel-bec, ollo-marran, mag-la-gaffe, doye-rouelle. Ni pli, ni bouche sur
   place, ni acte, ni parole, ni diffusion livrée ne les explique. L'heuristique
   sous-compte : le vrai chiffre est plus haut.
2. **Trois têtes crèvent leur budget** (L.34) : otto 33 croyances pour 3,
   alicent 25 pour 3, aegon-ii 21 pour 3. Ce n'est pas de la richesse, c'est de
   l'illisible — personne ne relit trente-trois lignes avant de faire agir un
   homme.
3. **Six pièces de mon staging sont votre plan** : couronne-A à E et
   couronne-structure, écrites le 129.4.3, états cibles en 72xxx, la colonne du
   roi vers Sombreval. Je ne les arbitre pas — un plan trouvé dans un couloir
   n'est pas une proposition. Reprenez-les ou dites-moi de les écarter.

## → mj-sombreval — un mort qui pense encore

1. **gunthor-darklyn porte une tête** (L.31). L'audit le dit dormant avec des
   intentions ; votre fiction le dit décapité sur son propre quai par Criston
   Cole. **Le premier qui le relira le fera agir.** Sa tête se retire et sa
   fiche se gèle avant le prochain battement — c'est la seule de mes lignes qui
   porte « avant le prochain battement ».
2. ~~**Trois dépôts dans les granges de Gunthor** (B.35)~~ — **JE RETIRE CE
   POINT : il n'était pas à vous, et je l'avais écrit sans ouvrir la pièce.**
   Vérification faite sur la proposition de tick du 4e : cette diffusion ne va
   pas à Sombreval, **elle en vient** — par la barque du patron de la
   Chère-Anse, qui n'a rien pu décharger chez vous depuis le 17e — et elle
   arrive chez mon Rulf Corne, à Peyredragon. Je la reprends entière.
   *Pour votre gouverne, puisque ça vous décrit* : on a fermé vos deux granges
   du haut avec des serrures neuves et on y compte le grain deux fois par jour.
   « On ne fait pas ça quand on en a. »
3. **Criston Cole, 16 croyances pour 3** (L.38, B.37) — la tête la plus vivante
   des trois grosses, et quatre de ses croyances sont sans source.

## → mj-leseyrie — une lettre en retard de quatre jours

**arrivee-lettre-privee-jeyne** : échéance du 129.3.30 encore « à-venir » (L.36)
et la diffusion qui va avec, non livrée (B.31). Même affaire vue du moteur et du
brouillard. Quatre jours : ceux qui devaient l'avoir lue agissent sans elle.

## → mj-reposdesfreux — deux diffusions échues

**remise-actes-protection**, deux diffusions dues le 129.4.1, non livrées
(B.34). Chez la reine, l'acte est entre les mains de l'intendant de Sombreval
depuis le 1er et quatre cases y attendent un ser Steffon qui est ici : le
retard n'est pas seulement le vôtre, il se voit des deux bouts.

## → mj-barralfond — quatre hommes du fond sans source

**toll-oeil-noir 2 croyances sur 2**, sarn-vieux-sang, bren-racine-grise,
ygga-main-de-pierre (B.36). Sur Toll, c'est la totalité de sa tête : il n'y a
rien à recouper, tout est à rattacher ou à retirer.

---

## → dev — ce qui n'est pas de mon ressort

**La main est coupée (P05), et tout le reste en dépend.** `python` est refusé
dans ma session : ni `append_flux`, ni `tick`, ni `couverture`, ni
`verser_cahier`, ni `reprise`. J'ai fait la besogne de la feuille à la main.
**Aucune de mes actions de mutation n'a pu s'exécuter** — elles ne sont pas en
retard, elles sont empêchées. Si le refus tient au prochain réveil, ce n'est pas
un incident : c'est une contrainte permanente, et il faut le dire comme telle.

**Six décisions attendent, et aucune n'est à moi :**

| # | La décision | Ce qui pend | Le prix |
| --- | --- | --- | --- |
| ~~P.21~~ | ~~Faire tourner les trois rapporteurs~~ | **FAIT le 4e.** Une réserve, et une seule : `plan-actions`, `plan-clefs` et `plan-verrous` portent l'heure du passage ; **`plan-etats-cibles.json` est resté au 24 août.** Redérivé-et-identique, ou pas touché ? C'est le registre des BUTS — je ne clos P.11 qu'après ce mot-là | fait |
| **NEUF** | **Le refus de dépêche accuse le quartier quand la cause est une bande fermée** | `agents/depeche/brief.py` l.140 imprime « AUCUN CREUX aujourd'hui (%s) » avec `hors_quartier or "journee fermee"`. Or `disponibilite_regie.py` l.130-141 renseigne le motif du dehors **dans les deux cas** — avec ou sans creux. Résultat : un homme indisponible parce qu'une bande de sa routine est `ferme: true` se voit refuser **au nom du quartier**, alors que l.103-112 du même fichier dit que le quartier ne vaut plus empêchement depuis le 31.8. **Coût réel, ce soir** : mj-aurore a conclu qu'il fallait toucher le moteur pour joindre Rulf Corne, et m'a passé la main. Il fallait attendre trois heures — sa bande rouvre à midi, 300 minutes. Le message devrait dire l'HEURE du prochain creux, pas un motif de distance | dire « prochain creux à HHhMM » au lieu du motif de quartier |
| **NEUF** | **Deux pièces orphelines à la racine de `etat/inbox/`, et un dossier `vues/` qui n'existe pas** | `action-1787603817481` et `action-1787604561328`, du 24 août, type `vue`, préfixe **`sans-siege`** : des rendus de bataille adressés à personne, dans aucun dossier de siège. **Et `etat/vues/` n'existe pas** — leur `.webp` et leur index pointent dans le vide. Sept jours que rien ne les relève et que **rien ne dit qu'elles sont là** : la feuille de reprise ne lit que `inbox/<siège>/`. Deux questions : qui les dépose, et pourquoi `sans-siege` ? | un balayage de la racine de l'inbox à la reprise |
| **NEUF** | **Ne pas émettre de pièce de tête quand la matière est vide** | Trois pièces du 4e (`tete-gerardys`, `tete-corlys`, `tete-denys-bar-emmon`) portent `matiere.journal: []`, `conclusion: false`, et proposent **une seule mutation : `date_maj → 129.4.4`**. Or `date_maj` est le champ que l'audit lit pour dire qu'une tête est périmée : la poser sans avoir touché une croyance ni une étape **éteint le témoin sans réparer la fuite**. Sur denys-bar-emmon (tête au 129.4.2, deux jours, hors tolérance) ça effacerait un signal vrai. La dépêche du 4e a produit du `cahier2` — du travail sur les registres — et aucune matière de tête : c'est normal, et c'est justement pourquoi il ne faut pas dater | une condition : `if not journal and not conclusion: pas de pièce` |
| **NEUF — le plus urgent** | **`CHAMPS_TETE_REQUIS` doit lâcher `echelle`** | Le validateur (`scripts/etat/mutations/vocabulaire.py` l.40) exige `echelle` sur toute tête. **`"echelle"` apparaît ZÉRO fois dans `etat/intentions.json`** — pas une tête sur tout le corpus. Et `scripts/temps/bouche.py` l.19 : *« L'ÉCHELLE A DISPARU, et le QUARTIER la remplace… ne se déclare pas : se MESURE »*, parce qu'elle se contredisait avec le tissu six fois sur quinze. **Aucune tête neuve ne peut entrer par la porte**, et la réparation évidente — écrire une échelle dans la pièce — rouvrirait le système supprimé. Je refuse de réparer la pièce | une ligne à retirer du tuple |
| **NEUF — et c'est le plus gros** | **Une diffusion livrée n'écrit rien dans les têtes** | Mesuré le 5e : **74 diffusions `livree: true`, 25 seulement laissent une trace chez un destinataire. 49 n'en laissent aucune.** Le drapeau dit que la nouvelle est PARTIE ; écrire la croyance est un geste séparé, fait à la main une fois sur trois. Vérifié de près sur `remise-actes-protection` : livrée deux fois, et ni lord-rosby ni coryn-faille ne portent une ligne dessus. **L'audit ne compte que le drapeau : il dira « tout est livré » d'un monde où personne n'a rien appris.** Et ça retourne B.11 — si le chemin automatique n'écrit rien, toutes les croyances sont posées à la main, d'où l'absence de porteur repéré. Heuristique prudente, le vrai chiffre est plus haut | qu'une livraison pose sa croyance, ou dise pourquoi elle ne la pose pas |
| ~~fusionner les jumelles~~ | **FAIT de ma main le 5e** | 86 diffusions, 3 paires strictement identiques — `couronnement-rhaenyra` (5/6), `decheance-de-rhaenyra` (13/15), `remise-actes-protection` (0/1), **toutes trois livrées deux fois**. Il en reste 83, zéro jumelle. Sauvegarde `evenements.json.avant-fusion-jumelles-20260831` | fait |
| ~~ancienne ligne~~ | **Fusionner les diffusions jumelles dans `evenements.json`** | `remise-actes-protection` porte deux diffusions **identiques au caractère près** (index 0 et 1 : même date, canal, fiabilité, texte, destinataires). Le tick les livre toutes les deux. **C'est là que naissent les croyances doublées que je compte dans B.11** — je les mettais sur le dos de la main qui écrit, à tort. Tant que les jumelles ne sont pas fusionnées, chaque tick refabrique ce que je passe mes journées à tailler | une passe sur `evenements.json` : même `date` + même `canal` + même `version` + même `qui` = une seule |
| R.21 | Normaliser les 152 paroles en `quoi` vers `contenu` | La 8e ligne de la feuille de reprise restera muette sans ça. 282 écritures dans `etat/` avec une autre plume active — je ne le fais pas seul (R.41) | réversible par git |
| M.22 | `monde.date` dérivé de la plus avancée des horloges | L'audit tourne dessus : **ses onze retards de tête sont tous sous-estimés d'un jour** | à mesurer — il faut d'abord la liste de ce qui lit `monde.date` (M.33) |
| M.32 | Remettre les trois sièges vacants à l'heure | Écart mesuré ce matin : **un jour, pas deux** — la barrière d'`append_flux` ne mord pas encore. Elle mordra dès que la reine passe au 5e. Mais remettre à l'heure sans rattraper ce qu'ils ont produit **efface une journée** | à trancher avant, pas pendant |
| B.22 · L.21 | Un passage de `tick` avant la salle | **Quatre échéances passées non produites** (ralliement-trident 4.2, lettre-jeyne 3.30, rulf-fait-payer-les-deux-patrons 3.28, fin-des-moutons-des-fosses 4.1) et **quatre nouvelles dues non livrées**. Une horloge tombée à zéro se produit : c'est de l'arithmétique | un passage par battement |
| P.13 | Un refus de versement revient-il à son auteur ? | Le verseur refuse plutôt que de deviner — c'est juste — mais le refus ne remonte pas : **un travail juste est perdu et son auteur ne peut pas le savoir.** Gerardys l'a écrit dans sa propre chambre avant que je le voie | lire le verseur d'abord (P.33) |

~~**Et une zone qui n'existe pas :** `ralliement-trident`…~~ — **réglé le 4e :
`mj-vivesaigues` existe, l'amorce lit désormais les lieux de diffusion des
échéances. Le trou est bouché à la source et non pour ce cas-là seul.** La
ligne devient un billet ordinaire, ci-dessous.

## → mj-vivesaigues — une échéance en retard de deux jours, pour ouvrir

**`ralliement-trident`**, échéance du 129.4.2, encore « à-venir », avec deux
diffusions attachées. Elle est chez vous depuis avant que vous existiez : ce
n'est pas un reproche, c'est le premier dossier. Rien ne l'a produite parce que
personne ne pouvait la produire.

**Trois mesures que je ne sais pas prendre seul**, et qui disent toutes la même
chose — je ne peux pas prouver que je tiens mes propres règles :
- Z.31 : combien de répliques poussées ont un homme derrière. C'est le seul
  chiffre qui prouverait la Règle Zéro au lieu de l'affirmer.
- S.31 : mes tranches — combien, quelle longueur, combien de Couper.
- M.33 : ce qui lit `monde.date`, avant qu'on touche à `monde.date`.

**Une pièce de staging applicable** : `20260813-021934-chaine-b.json`, les
corrections mécaniques *certaines* du grand plan, calculées en lecture seule.
Elle passe par `scripts/reparer_renvois.py`. Je ne peux pas la lancer.
