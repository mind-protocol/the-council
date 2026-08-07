# Le Conseil — Schéma de données

JDR narratif type CK3, univers ASOIAF, Danse des Dragons. Début : 129 AC, ~10 jours après la mort de Viserys I (gardée secrète, Aegon II vient d'être couronné). Le joueur est seigneur d'une maison NON-CANON des terres de la Couronne (créée en jeu → `etat/maison-joueur.json` + entrées `joueur` dans maisons/personnages).

Prototype : un fichier JSON par table dans `etat/`. Langue : français (noms de lieux officiels FR : Port-Réal, Peyredragon, Sombreval, Accalmie, Lamarck, Villevieille…). IDs en kebab-case. Dates : `{"annee": 129, "lune": 3, "jour": 12}`.

## Tables

### monde.json (singleton)
- `date` — {annee, lune, jour, minute} — `minute` = minutes écoulées depuis minuit, 0-1439. C'est l'horloge du monde et elle est tenue par `scripts/append_flux.py`, jamais à la main : chaque item poussé au flux estampe l'heure courante puis l'avance de sa durée. Au passage de 1440 le jour s'incrémente et la minute repart à 0.
- `phase` — ex: "succession-contestee", "guerre-ouverte"
- `tension` — 0-100 (module le seuil d'interruption du fast-forward)
- `deviations` — [] écarts au canon actés {date, cause, description}

### etat/flux.jsonl — durée des items (l'horloge)

Chaque item poussé au flux consomme du temps de jeu. `scripts/append_flux.py` estampe l'item d'un champ `heure` ("6h04", l'heure AU MOMENT où il se produit) puis avance `monde.date.minute` de sa durée. Le MJ ne calcule rien : il écrit `duree` (en minutes) quand elle sort de l'ordinaire, sinon le défaut du type s'applique.

- `duree` — entier, minutes. Facultatif ; à poser dès que l'action n'est pas ordinaire (une traversée, un repas, une attente, une descente de cent trente marches).
- `heure` — écrit par le script, jamais par le MJ.

Défauts par type : `replique` 1 · `geste` 1 · `vous` 1 · `recit` 5 · `table` 2 · `evenement` 2 · `salle` 0 · `breve` 0 · `marque` 0 · `objectif` 0 · `effacer` 0 · `question` 0 · `reponse` 0 · `pensee` 0.

Les trois derniers sont à zéro par principe et non par commodité : le mode Question est hors fiction, et « Penser » est explicitement gratuit — personne ne l'entend, le temps ne bouge pas. Les `recit` sont le levier principal : c'est là qu'on met les vraies durées (« il descend au quai » = 15, « la nuit passe » = 420).

### maisons.json
- `id, nom, devise`
- `blason` — description héraldique (base des portraits/médaillons)
- `siege_id` → lieux
- `suzerain_id` → maisons (null pour la Couronne)
- `allegeance_affichee` — "noir" | "vert" | "neutre"
- `allegeance_reelle` — peut différer (trahison structurelle)
- `or, revenus_lune, levees_dispo, levees_max`
- `statut` — "intacte" | "mobilisee" | "assiegee" | "tombee"
- `canon` — bool

### personnages.json
- `id, nom, maison_id, titre`
- `naissance` — année AC
- `traits` — 3-4 max ["ambitieux","pieux","lache",…]
- `objectifs` — [{but, priorite 1-3}] : moteur des actions hors écran
- `maniere` — 1 ligne : comment il/elle parle (nourrit les dialogues)
- `portrait` — {fichier: "ecrans/portraits/<id>.svg", physique: "1 ligne", prompt_ideogram: "prompt EN pour générer le vrai portrait via Ideogram — style unifié : oil painting portrait, dark fantasy, GoT"}
- `etat` — "actif" | "dormant" | "mort"
- `lieu_id` — position réelle (≠ ce que le joueur sait)
- `condition` — "libre" | "otage" | "prisonnier" | "blesse"

### relations.json (directionnelles, A→B ≠ B→A)
- `source_id, cible_id`
- `opinion` — -100..+100
- `liens` — ["suzerain","rival","amant","creancier",…]
- `connue_du_joueur` — bool
Ne stocker que les relations significatives (~40-60 au départ).

### lieux.json
- `id, nom, region, type` — "chateau" | "ville" | "ile" | "ruine"
- `controle_id` → maisons
- `jours_de_pr` — jours de voyage depuis Port-Réal (délai corbeaux ≈ /3)
- `alias` — [] autres ids désignant le même lieu. La couche carte (`ecrans/modules/geo.js`, généré depuis le mod AGOT) impose ses propres ids ; personnages et événements en emploient d'autres. Les deux sont valides, la résolution passe par `alias`.
- `roukerie` — {} facultatif : {<lieu_id d'origine>: <nombre>} — les corbeaux détenus ici, classés par le lieu où ils sont nés (un corbeau ne vole que vers là). Écrire vers B en consomme un ; on n'en regagne qu'à ce que B en renvoie. Voir `etat/plis.json` et `docs/plis.md`.

### plis.json (le courrier — un objet qui fait la route)
Rien n'atteint personne sans porteur. Champs : `id`, `canal` ("corbeau" | "cavalier" | "barque"), `scelle`, `porte` (le TEXTE FIGÉ au départ — un papier arrive périmé, jamais relu), `de`, `pour`, `vers` (lieu_id), `depuis` (lieu_id, facultatif), `parti_le`, `attendu_le`, `etat` ("en-route" | "remis" | "ouvert" | "retenu" | "perdu" | "intercepte"), `main` (qui l'a EN CE MOMENT — le mestre à la remise, jamais le `pour`). Format complet et délais : `docs/plis.md`. Coexiste avec `evenements.diffusion` pendant la transition.

### evenements.json (la file — cœur du moteur)
- `id, date_prevue, type` — "canon" | "emergent" | "programme"
- `importance` — 0-100 (comparée au seuil d'interruption)
- `description, lieu_id, acteurs`
- `conditions` — [] ce qui peut annuler/dévier (sinon l'événement SE PRODUIT)
- `statut` — "a-venir" | "resolu" | "devie" | "annule"
- `effets` — mutations d'état à appliquer à résolution
- `diffusion` — [] qui apprend la chose, quand, et déformée comment. Une entrée : {`ou` (lieu_id, nullable), `qui` ([personnage_id], nullable — au moins l'un des deux), `date`, `canal` ("corbeau" | "cavalier" | "barque" | "rumeur" | "temoin"), `fiabilite` 0-100, `version` (le fait tel qu'il arrive LÀ, déformé), `livree` bool}. Les dates se déduisent des `jours_de_pr` (corbeau ≈ /3, cavalier plein tarif, rumeur plus lente et plus tordue). C'est le brouillard côté PNJ, symétrique de `info.json` côté joueur : à la livraison, la `version` entre dans les `croyances` des concernés — jamais le fait vrai. Une entrée qui touche le personnage joueur doit AUSSI produire une entrée `info.json`.
**Le statut de l'événement commande la livraison** : `resolu` → livrable ; `a-venir` → suspendue (l'échéance peut tomber dans la fenêtre, mais la nouvelle d'une chose non arbitrée ne part pas) ; `devie` ou `annule` → ne part JAMAIS. On peut donc écrire à l'avance la diffusion d'un canon lointain sans risquer qu'elle se livre si le joueur le fait dévier.

### info.json (ce que le JOUEUR sait — jamais confondu avec la vérité)
- `id, evenement_id` (nullable — une rumeur peut être fausse)
- `version` — le récit tel qu'il parvient au joueur, déformé
- `source` — "corbeau" | "mestre" | "rumeur" | "espion" | "temoin"
- `fiabilite` — 0-100
- `date_apprise`

### objectifs.json (les objectifs du JOUEUR — distincts des objectifs des PNJ)
- `id, titre` — court, orienté action ("Recevoir le serment des bannerets de la baie")
- `description` — 1-2 lignes : l'enjeu, ce que ça coûterait d'échouer
- `source_id` — qui l'a suggéré/imposé (personnage_id, ou "vous-meme")
- `date_donne, echeance` (nullable)
- `statut` — "en-cours" | "accompli" | "echoue" | "abandonne"
Donné par le MJ via le flux (item `objectif`, action ajouter/accomplir/echouer/retirer) ET écrit ici. Un objectif naît toujours diégétiquement (une demande de Corlys, un serment fait, une menace reçue) — jamais d'un menu.

### annales.json (les événements marquants — la mémoire longue de la partie)
- `id, date`
- `titre` — une ligne, ce que l'Histoire retiendra ("Sombreval se déclare la première")
- `texte` — 1-2 phrases, le fait tel qu'il est acquis
- `portee` — "maison" | "royaume" | "regne"
Écrit ici D'ABORD, puis poussé au flux en item `marque` (ligne rouge et or, coiffée de « Il s'est passé »). Avec parcimonie : un fait qui change le cours (mort, serment prêté ou rompu, couronnement, trahison découverte, ville qui se déclare, bataille, dragon perdu) — jamais un beat de scène. C'est la vérité ACQUISE : les PNJ s'en souviennent et aucune scène ultérieure ne peut la contredire.

### journal.json
- `maison_joueur_id` — null tant que la création de partie n'a pas eu lieu
- `personnage_joueur_id` — le personnage incarné (peut être canon : dans ce cas il n'a PAS d'entrée dans intentions.json)
- `scenes` — [{date, lieu_id, participants, resume, choix_fait}]
- `scene_courante` — état du beat en cours (nullable)

### paroles.json (les choses DITES — mémoire verbale des PNJ)
- `id, date, locuteur_id, destinataire_id`
- `contenu` — citation ou résumé fidèle
- `type` — "serment" | "promesse" | "menace" | "mensonge" | "revelation" | "insulte" | "confidence"
- `temoins` — [] qui d'autre l'a entendu
- `poids` — 1-3 : importance pour la rancune/confiance future
Alimentée après chaque scène. Un PNJ ressort tes promesses non tenues.

### actes.json (les choses FAITES — registre des faits accomplis)
- `id, date, acteur_id, description, cible_id` (nullable)
- `connu_de` — [] ids de ceux qui le savent ("tous" possible)
Différent de la file evenements : ici c'est le grand livre de ce qui s'est réellement produit.

### intentions.json (les têtes des PNJ — JAMAIS montré au joueur)
Une entrée par personnage `actif`, et une seule source pour toute action hors écran : un PNJ ne fait JAMAIS rien qui ne sorte de là. Le personnage joueur n'a jamais d'entrée (sa tête appartient au joueur).
- `personnage_id`
- `echelle` — coût de simulation : "scene" | "orbite" | "royaume" (voir budgets)
- `croyances` — [] ce qu'il tient pour vrai (peut être FAUX : les PNJ subissent aussi le brouillard)
- `ignore` — [] 1-3 choses qu'il ne sait PAS et dont l'absence explique sa conduite. Sert à tenir le brouillard côté PNJ : ce qui est ici ne doit pas fuiter dans ses actes.
- `intention` — ce qu'il compte faire à court terme (1-2 lignes)
- `plan` — [] étapes horlogées (ci-dessous)
- `declencheurs` — [] réactions conditionnelles : {`si` (la condition, en clair), `alors` (ce qu'il fait), `une_fois` bool}. Les plans n'anticipent pas le joueur ; les déclencheurs si. Écrits à froid, évalués par le MJ à chaque tick.
- `attitude_joueur` — 1 ligne : ce qu'il pense du joueur en ce moment
- `date_maj`

Étape de `plan` :
- `id` — kebab-case, unique dans tout le fichier
- `quoi` — l'étape, concrète
- `etat` — "en-cours" | "fait" | "bloque" | "abandonne"
- `jours_restants` — entier : ce qu'il reste à courir. `null` = posture permanente (tenir la roukerie, garder ses enfants près de soi) : jamais « faite », jamais décomptée.
- `depend_de` — [] ids d'étapes qui doivent être `fait` avant que l'horloge tourne
- `cout` — [] ce que l'étape consomme ou exige : hommes, or, corbeaux, jours de mer, l'accord de quelqu'un
- `si_bloque` — ce qu'il fait à la place si le coût manque ou si l'étape échoue. Écrit À FROID, en pensant au personnage — c'est la pièce qui empêche d'improviser à chaud une porte de sortie au service du drame.

Une étape dont l'horloge tombe à 0 SE PRODUIT : elle donne une entrée `actes.json`, souvent un `programme` dans `evenements.json`, et une `info.json` si le joueur peut le percevoir. Le tick est alors de l'arithmétique, pas de l'invention.

Budgets par échelle — tenus à la main, vérifiés par `scripts/tick.py --verifier` :

| échelle | qui | croyances | étapes | déclencheurs | simulé |
|---|---|---|---|---|---|
| `scene` | dans la salle ou sur le point d'y entrer (~5 max) | 4-6 | 3-5 | 1-3 | à chaque battement |
| `orbite` | pèse sur la partie sans être en scène (~12 max) | 3-5 | 2-4 | 1-2 | à chaque tick |
| `royaume` | moteur lointain de la Danse | 1-3 | 1-2 | 0-1 | rafraîchi sur les fenêtres ≥ 5 jours |

Ces plafonds mesurent l'ATTENTION du MJ par tick, pas la taille du fichier : une tête coûte de relire des croyances, peser des déclencheurs et réécrire une intention. Les monter ne donne pas de la capacité, ça donne la même simulation en moins bien faite — au-delà, la boucle hors scène se joue en apparence. Un acteur qui n'a rien à décider n'a pas besoin d'une tête : donne-lui des mains (`activites.json`), qui ne sont jamais budgétées, et un seuil la lui rendra le jour où son affaire mord.

Un acteur `royaume` garde droit à UN déclencheur : sans lui il serait sourd au joueur, ce qui contredit la boucle hors scène. C'est même le seul endroit où l'on peut encore l'atteindre entre deux rafraîchissements.

Une échelle règle le RAFRAÎCHISSEMENT (croyances relues, horloges décomptées, déclencheurs pesés), jamais les échéances : une étape d'acteur `royaume` dont l'horloge tombe dans la fenêtre se produit quand même, et `tick.py` la rend marquée `malgre_saut`. Un coffre d'or promis pour demain arrive demain, même si la tête de celui qui l'apporte n'a pas été repassée en revue.

La provenance d'une croyance ne vit PAS ici : elle vit dans `evenements.diffusion`. Ici, seulement la tête.

### activites.json (les mains — ce qui avance sans qu'on décide)
Une entrée par affaire qui court. Orthogonal à `intentions.json` : la tête dit ce qu'un acteur veut et décide, les mains disent où en sont ses affaires. Un acteur peut avoir les deux (Daemon), une tête seule (un intrigant), ou des mains seules (un sergent recruteur). **Aucun budget** : c'est de l'arithmétique, simulée à chaque tick AVANT tout le reste. Le personnage joueur n'a pas de tête, mais il a des mains.
- `id` — kebab-case (`recrutement-peyredragon`, `radoub-flotte-velaryon`)
- `quoi` — l'affaire, en clair
- `porteur` — {`type`: "personnage" | "maison" | "lieu", `id`}. `id` peut être `null` : une affaire sans porteur tourne quand même, et personne n'en rend compte.
- `lieu_id` — où ça se passe
- (pas de champ de position : où se tient le porteur est décidé par `etat/routines.json`
  et calculé par `scripts/presence.py`. Une activité ne duplique jamais une position.)
- `mandat` — `null`, ou 1 ligne : ce que le joueur a confié, et depuis quand
- `mesure` — [] les compteurs (ci-dessous) ; 1 à 3, jamais plus
- `seuils` — [] les franchissements (ci-dessous)
- `dernier_rapport` — date du dernier compte rendu monté au joueur
- `date_maj`

Compteur de `mesure` :
- `id` — kebab-case, unique dans l'activité. Adressable de l'extérieur par `<activite_id>.<mesure_id>` : c'est cette adresse qu'un `cout` d'étape de plan cite.
- `quoi` — ce qu'on compte ; `unite` — "hommes", "jours", "muids", "nefs", "cerfs"
- `valeur` — entier : l'état VRAI, jamais montré tel quel au joueur
- `rythme` — {`par`: entier signé, `jours`: entier > 0, omis = 1} : « `par` unités tous les `jours` jours »
- `reliquat` — entier dans [0, `rythme.jours`[ : le reste de la division, reporté. **Tout est en entiers, jamais en flottants.** Posé par `tick.py`, jamais à la main.
- `plancher` / `plafond` — bornes ; `null` = court librement
- `depend_de` — [] adresses d'autres mesures qui GÈLENT celle-ci quand elles sont à leur plancher (on ne lève pas d'hommes qu'on ne peut pas nourrir)

Décompte, pour `n` jours écoulés : `total = par * n + reliquat` ; `valeur += total // jours` ; `reliquat = total % jours` ; puis bornage. Exact et sans dérive, quelle que soit la découpe des ticks.

Seuil de `seuils` :
- `id` ; `mesure_id` — la mesure surveillée
- `quand` — "sous" | "sur" ; `valeur` — le point de bascule
- `promeut` — "orbite" | "scene" : l'échelle du porteur au franchissement. S'il a déjà une tête à cette échelle ou au-dessus, rien ne bouge — l'affaire entre dans ses croyances.
- `affaire` — 1 ligne : la bifurcation qui monte au joueur, écrite À FROID comme un `si_bloque`. Seul texte du fichier que le joueur entendra un jour.
- `franchi_le` — date, ou `null`. Repasse à `null` quand la mesure revient du bon côté : un seuil retombe, et le porteur redescend.

Un franchissement ne produit JAMAIS un menu : il donne (ou étoffe) la tête du porteur, et la scène sort ensuite des deux autres boucles.

**La valeur d'une mesure est la vérité ; le rapport est une croyance.** Un porteur peut mentir sur son propre compteur — jugé à chaque rapport d'après sa `maniere`, jamais inscrit dans le fichier. Ce fichier ne contient que le vrai. Une activité dont le porteur est mort, absent ou fâché ne remonte rien, et le joueur découvre le chiffre trop tard.

**Aucun rendu** : le joueur ne voit jamais un compteur, seulement quelqu'un qui lui dit un chiffre. Une activité ne s'écrit que si son résultat doit atteindre le joueur — par un chiffre dit en scène, un `cout` qui rend un plan impossible, une ligne du matin, ou une crise. Note de conception : `docs/activites.md`.

## Registres d'IDs (OBLIGATOIRES — tout fichier utilise exactement ces IDs)

### Maisons
Préfixe `maison-` obligatoire : `maison-targaryen-vert` (Aegon II, Port-Réal), `maison-targaryen-noir` (Rhaenyra, Peyredragon), `maison-velaryon`, `maison-hightower`, `maison-rosby`, `maison-stokeworth`, `maison-darklyn` (Sombreval), `maison-staunton`, `maison-celtigar`, `maison-bar-emmon`, `maison-massey`, `maison-strong`, `maison-baratheon`. À créer au besoin : `maison-lannister`, `maison-stark`, `maison-arryn`, `maison-tully`, `maison-hayford`. La maison du joueur : id `joueur`, créée en jeu.

### Personnages (etat initial entre parenthèses)
Actifs cour verte : `aegon-ii`, `alicent`, `otto`, `criston`, `aemond`, `larys`, `helaena` (semi), `orwyle`.
Actifs cour noire : `rhaenyra`, `daemon`, `corlys`, `rhaenys`, `jacaerys`, `lucerys` (vivant au départ !), `mysaria`.
Actifs Couronne : `lord-rosby`, `lord-stokeworth`, `gunthor-darklyn`, `lord-staunton`, `bartimos-celtigar`, `lord-bar-emmon`.
Dormants : `daeron` (Villevieille), `baela`, `rhaena`, `aegon-le-jeune`, `viserys-le-jeune`, `cregan-stark`, `jeyne-arryn`, `borros-baratheon`, `jason-lannister`, `ormund-hightower`.
Prénoms non canon (Rosby, Stokeworth, Staunton…) : en inventer de plausibles, `canon` reste vrai pour la maison.

### Lieux
`port-real`, `peyredragon`, `sombreval`, `rosby`, `stokeworth`, `lamarck`, `accalmie`, `harrenhal`, `villevieille`, `castral-roc`, `winterfell`, `les-eyrie`, `vivesaigues`, `pointe-massey`. Trois lieux portent deux ids, l'un venu de la carte, l'autre de l'usage — les deux valent, `lieux.alias` fait le lien : `repaire-aux-corneilles` ↔ `repos-des-freux`, `griffes` ↔ `ile-aux-pinces`, `sharp-point` ↔ `pointe-aigue`. Le siège du joueur : id `siege-joueur`, créé en jeu.

## Conventions
- Calendrier : 12 lunes de 30 jours. Toute arithmétique de date (horloges des plans, dates de diffusion, délais de route) suit cette règle.
- La vérité vit dans `etat/*.json` ; le joueur ne voit que `info.json` + ce que ses scènes lui montrent.
- `etat/staging/` — propositions de mutations, jamais l'état. `scripts/tick.py` y écrit ce qui tombe (horloges échues, événements à résoudre, nouvelles à livrer, déclencheurs à évaluer) ; le MJ seul relit, arbitre et applique. Un seul écrivain.
- **Appliquer une proposition** : `python scripts/appliquer.py <fichier> [--vraiment]`. Le tick rédige d'office les mutations purement arithmétiques dans `mutations_proposees` (horloges décomptées, nouvelles marquées livrées) ; le MJ ajoute les siennes à la main dans la même liste, puis applique en un geste. Le vocabulaire des mutations est FERMÉ — aucun chemin JSON arbitraire — et fait autorité dans la docstring de `scripts/appliquer.py`. Trois gardes : l'empreinte sha1 des tables au moment du calcul (refus si un autre écrivain est passé), la validation intégrale avant toute écriture (une mutation invalide annule le lot), et le marquage `applique_le` contre la double application. Une proposition écrite à la main qui ne dépend d'aucune horloge peut omettre `empreintes` : la garde de fraîcheur ne s'applique alors pas.
- Portraits : `ecrans/portraits/<personnage-id>.svg` (médaillons héraldiques stylisés en attendant de vraies images).
- Toute mutation d'état est écrite sur disque à la fin de la scène/du battement, jamais gardée en mémoire seulement.
