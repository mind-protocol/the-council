# Les activités — la troisième boucle

**État : validé et implémenté.** `docs/schema.md` et `CLAUDE.md` portent désormais la règle ;
ce document reste la note de conception — le POURQUOI, les exemples commentés, et ce qui a
été tranché en chemin. En cas de conflit, `docs/schema.md` a raison.

---

## L'axe

Ce n'est pas une catégorie de personnes, c'est une **dimension de tout acteur**. Corlys a
des nefs à radouber, Daemon des hommes à lever et un coffre qui se vide, le mestre un stock
de corbeaux, un sergent recruteur un rôle qui s'allonge. Aucun n'est « un office », tous ont
la même arithmétique.

| | `intentions.json` — la tête | `activites.json` — les mains |
|---|---|---|
| répond à | que veut-il, que croit-il, que décide-t-il | où en sont ses affaires |
| coûte | du jugement, à chaque tick | rien : une soustraction |
| budgété | oui, par `echelle` | **non, jamais** |
| produit | actes, paroles, croyances fausses | des chiffres, et des seuils qui sautent |

Les deux sont **orthogonales**. Un acteur peut avoir les deux (Daemon), seulement une tête
(Otto, qui ne fait qu'intriguer), ou seulement des mains (un sergent recruteur, qui ne
décide rien tant que rien ne casse). Le personnage joueur n'a jamais de tête — mais il a
des mains : ce qui se fait en son nom se compte comme celui des autres.

C'est la vraie explication du budget : un homme de maison ne mange pas d'orbite **parce
qu'il n'a pas de tête**, pas parce qu'il appartient à une classe à part. Un seuil qui saute
lui en donne une, et il redevient un acteur ordinaire.

---

## 1 — Section à insérer dans `CLAUDE.md`

À placer entre « La boucle hors scène » et « Orienter le joueur ».

> ### La boucle des activités — où en sont les choses
>
> Les deux premières boucles répondent à « qui a la plus forte raison d'agir » (la salle) et
> « qu'est-ce que ça produit dans le monde » (les absents). Il en manque une troisième, et
> c'est celle qui tient les chiffres : **où en sont les choses ?** Elle n'élit personne —
> tout avance en même temps. Elle ne croit rien — un tonneau n'a pas d'opinion. C'est de
> l'arithmétique, et à ce titre elle appartient à `tick.py`, pas à ton jugement.
>
> **Ce n'est pas une catégorie de gens, c'est une dimension.** Tout acteur a une tête
> (`intentions.json` : ce qu'il veut, croit, décide) et des mains (`activites.json` : ce qui
> avance chez lui sans qu'il ait à décider). Les deux sont indépendantes : Daemon a les deux,
> un intrigant n'a qu'une tête, un sergent recruteur n'a que des mains. Les mains ne sont
> **jamais budgétées** — tu peux en avoir cinquante, ça ne coûte qu'une soustraction.
>
> **Elle tourne EN PREMIER**, avant les deux autres, parce que sa sortie est leur entrée. Un
> conseil qui dit « nous avons du grain pour dix-neuf jours » doit trouver ce chiffre déjà
> écrit, pas l'inventer à la réplique. Et un `cout` d'étape de plan se vérifie contre les
> mesures : un `si_bloque` se déclenche alors **arithmétiquement**, au lieu d'être jugé au
> doigt mouillé. Ordre non négociable : les activités, puis les absents, puis la salle.
>
> **Elle ne produit jamais de décision ni de scène.** Trois sorties seulement :
> 1. les mesures bougent ;
> 2. une ligne au passé pour « ce qui s'est fait sans vous », s'il y a lieu ;
> 3. **un franchissement de seuil** — le seul événement qu'elle sache émettre.
>
> Un franchissement ne devient JAMAIS un menu. Il **donne ou étoffe la tête du porteur** à
> l'échelle dite : on lui écrit ses croyances et son plan, il monte l'escalier, et à partir
> de là il est joué par les deux autres boucles comme n'importe qui. Il redescend quand la
> mesure repasse du bon côté. Un acteur qui a déjà une tête ne monte pas d'un cran pour
> autant : son affaire entre simplement dans ses croyances, et le voilà qui en parle.
>
> **La boucle des activités n'a AUCUN rendu.** Le joueur ne voit jamais un compteur, jamais
> une barre, jamais un tableau. Il voit quelqu'un qui lui dit un chiffre, avec sa manière et
> son intérêt à le dire de travers. Le brouillard s'applique au RAPPORT, pas au calcul : le
> calcul est juste, ce qui remonte ne l'est pas forcément — on arrondit en sa faveur, on
> cache un déficit trois semaines. Une activité dont le porteur est mort, absent ou fâché ne
> remonte rien du tout, et le joueur découvre le chiffre quand il est trop tard.
>
> **Le mandat change la remontée, pas le calcul.** Sans mandat, le porteur vient demander et
> se couvre par écrit ; avec mandat, il tranche seul et rend compte en une ligne, au passé.
> La mesure, elle, avance pareil.
>
> **Une activité mal tenue pourrit toute seule**, sans simulation : la mesure dérive dans le
> mauvais sens et un jour le chiffre est intenable. C'est ça, la conséquence — pas une tête
> qui pense.

---

## 2 — Bloc à insérer dans `docs/schema.md`

À placer après `intentions.json`. **Ne pas l'écrire dans `schema.md` sans accord explicite :
le manuel interdit d'y toucher.**

> ### activites.json (les mains — ce qui avance sans qu'on décide)
>
> Une entrée par affaire qui court. Indépendant d'`intentions.json` : un porteur peut avoir
> l'un, l'autre, les deux, ou passer de l'un à l'autre. **Aucun budget** : simulé par
> arithmétique à chaque tick, avant tout le reste.
>
> - `id` — kebab-case (`recrutement-peyredragon`, `radoub-flotte-velaryon`)
> - `quoi` — l'affaire, en clair (« lever et armer des hommes sur l'île »)
> - `porteur` — `{type: "personnage"|"maison"|"lieu", id}`. `id` peut être `null` : une
>   affaire sans porteur tourne quand même, et personne n'en rend compte.
> - `lieu_id` — où ça se passe
> - `mandat` — `null`, ou 1 ligne : ce que le joueur a confié, et depuis quand
> - `mesure` — [] les compteurs (ci-dessous) ; 1 à 3, jamais plus
> - `seuils` — [] les franchissements (ci-dessous)
> - `dernier_rapport` — date du dernier compte rendu monté au joueur
> - `date_maj`
>
> Compteur de `mesure` :
> - `id` — kebab-case, unique dans l'activité. Adressable de l'extérieur par
>   `<activite_id>.<mesure_id>` — c'est cette adresse qu'un `cout` d'étape de plan cite.
> - `quoi` — ce qu'on compte (« hommes marqués au rôle », « jours de vivres »)
> - `valeur` — l'état VRAI, jamais montré tel quel au joueur
> - `unite` — « hommes », « jours », « muids », « nefs », « cerfs »
> - `rythme` — `{par: <entier signé>, jours: <entier > 0>}` : « `par` unités tous les `jours`
>   jours ». `jours` vaut 1 le plus souvent et peut être omis. C'est tout le moteur.
> - `reliquat` — entier dans `[0, rythme.jours[` : le reste de la division, reporté au tick
>   suivant. **Tout est en entiers, jamais en flottants** — trois hommes tous les deux jours
>   s'écrit `{par: 3, jours: 2}` et ne perd rien en route. Posé par `tick.py`, jamais à la main.
> - `plancher` / `plafond` — bornes ; `null` si la mesure court librement
> - `depend_de` — [] adresses d'autres mesures qui gèlent celle-ci si elles sont à leur
>   plancher (on ne lève pas d'hommes qu'on ne peut pas nourrir)
>
> Seuil de `seuils` :
> - `id`
> - `mesure_id` — la mesure surveillée
> - `quand` — `"sous"` | `"sur"` ; `valeur` — le point de bascule
> - `promeut` — `"orbite"` | `"scene"` : l'échelle du porteur au franchissement. S'il a déjà
>   une tête à cette échelle ou au-dessus, rien ne bouge — l'affaire entre dans ses croyances.
> - `affaire` — 1 ligne : la bifurcation qui monte au joueur, écrite À FROID, comme un
>   `si_bloque`. Seul texte du fichier que le joueur entendra un jour.
> - `franchi_le` — date, ou `null`. Repasse à `null` quand la mesure revient du bon côté :
>   un seuil retombe, et le porteur redescend.
>
> **La valeur d'une mesure est la vérité ; le rapport est une croyance.** Un porteur peut
> mentir sur son propre compteur — c'est un choix de personnage, jugé à chaque rapport
> d'après sa `maniere`, jamais un décalage inscrit dans le fichier.
>
> Un `cout` d'étape de `plan` peut citer une adresse de mesure. `tick.py` la vérifie :
> si elle ne couvre pas, c'est `si_bloque` qui s'applique, sans jugement.

---

## 3 — `etat/activites.json` — forme et exemples

Trois entrées volontairement dissemblables : un homme sans tête, un grand seigneur qui en a
une, et une affaire portée par une maison sans personne dessus.

```json
{
  "activites": [
    {
      "id": "recrutement-peyredragon",
      "quoi": "Lever et armer des hommes sur l'île, sous la voûte de la porte du Dragon",
      "porteur": { "type": "personnage", "id": "hobb-sanglier" },
      "lieu_id": "peyredragon",
      "mandat": null,
      "mesure": [
        { "id": "hommes-au-role", "quoi": "hommes marqués au rôle, en sus de la garnison",
          "valeur": 0, "unite": "hommes", "rythme": { "par": 3, "jours": 2 }, "reliquat": 0,
          "plancher": 0, "plafond": 400,
          "depend_de": ["vivres-peyredragon.jours-de-vivres"] },
        { "id": "solde-due", "quoi": "cerfs dus aux hommes levés, non payés",
          "valeur": 0, "unite": "cerfs", "rythme": { "par": 12 }, "reliquat": 0,
          "plancher": 0, "plafond": null, "depend_de": [] }
      ],
      "seuils": [
        { "id": "solde-intenable", "mesure_id": "solde-due", "quand": "sur", "valeur": 2000,
          "promeut": "scene",
          "affaire": "Hobb ne peut plus payer ce qu'il a promis : trouver l'or, ou renvoyer des hommes déjà armés — qui savent où sont les armes.",
          "franchi_le": null },
        { "id": "file-tarie", "mesure_id": "hommes-au-role", "quand": "sous", "valeur": 1,
          "promeut": "orbite",
          "affaire": "Plus personne ne se présente sous la voûte. Hobb en connaît la raison et n'ose pas la dire.",
          "franchi_le": null }
      ],
      "dernier_rapport": null,
      "date_maj": "129-3-14"
    },

    {
      "id": "radoub-flotte-velaryon",
      "quoi": "Remettre en état les nefs de Lamarck après l'hiver",
      "porteur": { "type": "personnage", "id": "corlys-velaryon" },
      "lieu_id": "lamarck",
      "mandat": null,
      "mesure": [
        { "id": "nefs-prêtes", "quoi": "nefs en état de prendre la mer",
          "valeur": 61, "unite": "nefs", "rythme": { "par": 7, "jours": 10 }, "reliquat": 0,
          "plancher": 0, "plafond": 90, "depend_de": [] }
      ],
      "seuils": [
        { "id": "flotte-au-complet", "mesure_id": "nefs-prêtes", "quand": "sur", "valeur": 85,
          "promeut": "orbite",
          "affaire": "La flotte est prête avant terme. Corlys veut s'en servir, et il n'attendra pas qu'on le lui demande.",
          "franchi_le": null }
      ],
      "dernier_rapport": null,
      "date_maj": "129-3-14"
    },

    {
      "id": "vivres-peyredragon",
      "quoi": "Ce que l'île a dans ses celliers",
      "porteur": { "type": "lieu", "id": "peyredragon" },
      "lieu_id": "peyredragon",
      "mandat": null,
      "mesure": [
        { "id": "jours-de-vivres", "quoi": "jours de vivres pour la maisonnée et la garnison",
          "valeur": 96, "unite": "jours", "rythme": { "par": -1 }, "reliquat": 0,
          "plancher": 0, "plafond": 240, "depend_de": [] }
      ],
      "seuils": [
        { "id": "cellier-court", "mesure_id": "jours-de-vivres", "quand": "sous", "valeur": 30,
          "promeut": "scene",
          "affaire": "Un mois de vivres. Il faut acheter au prix de la guerre, rationner, ou renvoyer des bouches.",
          "franchi_le": null }
      ],
      "dernier_rapport": null,
      "date_maj": "129-3-14"
    }
  ]
}
```

Noter : `recrutement-peyredragon` est gelé si `vivres-peyredragon.jours-de-vivres` touche son
plancher. Corlys a une tête ET des mains ; Hobb n'a que des mains ; les vivres n'ont personne.

---

## 4 — Ce que `tick.py` doit en faire

Dans l'ordre, avant la boucle des absents :

1. **Décompter, en entiers.** Pour chaque mesure, avec `n` jours écoulés :

   ```
   total    = rythme.par * n + reliquat
   valeur  += total // rythme.jours          # division plancher
   reliquat = total %  rythme.jours          # toujours dans [0, jours[
   ```

   Puis bornage par `plancher`/`plafond`. C'est exact et réversible : rien ne se perd en
   route, et trois hommes tous les deux jours donnent bien trois hommes tous les deux jours,
   quelle que soit la découpe des ticks. Une mesure dont un `depend_de` est à son plancher ne
   bouge pas (gelée, pas remise à zéro, reliquat conservé). Sans porteur vivant, le rythme est
   réputé nul dans le sens favorable et conservé dans le sens défavorable — une affaire sans
   personne ne produit plus, mais continue de coûter.
2. **Servir les coûts.** Toute étape de `plan` dont un `cout` cite une adresse de mesure est
   vérifiée ici : si la mesure ne couvre pas, l'étape passe `bloque` et `si_bloque`
   s'applique. Sans jugement, et avant que la boucle des absents ne tourne.
3. **Peser les seuils.** Franchissement → écrire dans la proposition de staging la promotion
   du porteur et l'`affaire` telle quelle, à charge du MJ d'en faire une scène. Retour du bon
   côté → `franchi_le: null`.
4. **Proposer la ligne du matin.** Une par activité au plus, trois à cinq au total pour « ce
   qui s'est fait sans vous ». `tick.py` propose, le MJ coupe.
5. **Ne jamais écrire dans `etat/`** : tout par `etat/staging/`, comme le reste.

`tick.py --verifier` doit signaler :
- une mesure sans `rythme`, dont `rythme.jours` est nul ou négatif, ou dont un `depend_de`
  pointe dans le vide ;
- un `cout` d'étape qui cite une adresse de mesure inexistante ;
- un seuil `franchi_le` non nul dont le porteur n'a toujours pas de tête à l'échelle dite ;
- un porteur promu dont la crise est close et qui traîne encore en `orbite` — du budget
  mangé pour rien ;
- une activité sans porteur depuis plus de N jours.

---

## Tranché

- **Le pas de temps : des entiers, avec reliquat.** `rythme: {par, jours}` et le reste
  reporté. Pas de flottant nulle part — on ne veut pas d'un stock de grain à 96,3 jours ni
  d'une dérive d'arrondi sur cent ticks.
- **La forme du mensonge : le jugement du MJ**, d'après la `maniere` du porteur. Aucun champ
  `biais_rapport`. Un chiffre faux est un choix de personnage — Hobb arrondit parce que c'est
  Hobb, pas parce qu'une constante le dit. Corollaire : le fichier ne contient JAMAIS le
  chiffre déclaré, seulement le vrai.

## Ce qui reste à trancher

- **Jusqu'où écrire des mains.** La tentation sera d'en donner à tout le monde. Le critère
  n'est pas mécanique — voir « Le critère d'écriture » ci-dessous — mais il reste à décider
  au bout de combien de lunes sans effet une activité se retire du fichier.

---

## Le critère d'écriture

**Une activité s'écrit si, et seulement si, elle doit produire un résultat que le joueur
verra.** Pas « si sa mesure peut franchir un seuil » : le seuil est un mécanisme interne,
et un mécanisme n'est pas une raison d'exister. Ce qui décide, c'est ce qui atteint l'écran.

Quatre façons pour un résultat d'atteindre le joueur — une seule suffit :

1. **Un chiffre dit en scène.** Quelqu'un l'énonce à une table, et le chiffre doit être vrai
   avant qu'on ouvre la bouche. Les vivres, les hommes, les nefs prêtes.
2. **Un `cout` qui mord.** Le joueur veut partir et les nefs ne sont pas radoubées ; il veut
   trois cents hommes et le rôle en porte quarante. L'activité n'a franchi aucun seuil — elle
   a rendu un plan impossible, et ça se voit mieux qu'un seuil.
3. **Une ligne du matin.** Ce qui s'est fait sans lui, au passé, dans « ce qui s'est fait
   sans vous ».
4. **Une crise qui monte l'escalier.** Le seuil franchi, quelqu'un qui arrive avec une
   bifurcation.

Corollaire, et c'est là que la règle mord : **si personne ne peut jamais voir le résultat,
l'activité ne s'écrit pas** — même si elle serait « réaliste ». Le grain d'un château où le
joueur n'ira pas, le compte des chandelles, la paie des palefreniers : ce sont des choses
vraies que rien ne rendra jamais lisibles. Les compter, c'est se donner du travail dont la
partie ne verra rien, et c'est la pente qui mène au tableur.

Le test à s'appliquer avant d'écrire une entrée : **par quelle bouche, ou par quel
empêchement, ce chiffre atteindra-t-il le joueur ?** Si la réponse ne vient pas en une
phrase, ne l'écris pas.

Inversement, une activité qui passe le test s'écrit même si elle ne bougera pas de trois
lunes : sa lenteur EST son résultat, le jour où le joueur en a besoin tout de suite.
