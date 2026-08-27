# La règle de dépendance

**Un module ne peut dépendre que de couches strictement inférieures à la sienne.**
Le numéro du dossier EST la règle. Rien ne remonte, jamais.

```
10-socle  →  20-monde  →  30-perception  →  40-combattant  →  50-unite
                                                    ↘              ↓
                                                  60-transmission  ↓
                                                          ↘        ↓
                                                        70-commandement  →  80-conduite

90-observation lit tout, et personne ne lit 90.
```

## Pourquoi cette règle et pas une autre

Parce que c'est la seule qui se **vérifie sans jugement**. « Les modules doivent
être bien découpés » ne se contrôle pas ; « aucune dépendance ne remonte » se
contrôle par un script, et un script qui refuse une remontée refuse aussi les
dérives qu'on n'avait pas prévues.

Le document précédent avait un diagramme d'acteurs montrant qui *parle* à qui —
missions vers le bas, rapports vers le haut. Il ne disait jamais qui a le droit
d'*importer* qui. Ces deux choses n'ont rien à voir : un rapport remonte, mais le
module qui le produit ne doit pas connaître son destinataire.

## Comment un module obtient ce qu'il ne peut pas importer

**Il le reçoit.** Un module de couche basse qui a besoin d'un service de couche
haute le prend en argument à sa création, et ignore d'où il vient.

C'est la différence entre « le mouvement appelle le journal » — interdit, le
journal est plus haut — et « le mouvement reçoit de quoi signaler un
franchissement, sans savoir qui écoute ». Le second se teste sans journal ; le
premier ne se teste pas du tout.

## Le cas qui a cassé la règle précédente

Un module d'identité d'unité recevait l'écrivain des annales. Une entité de
couche 50 remontait chercher un service d'observation de couche 90. Personne ne
l'a vu passer, parce que rien ne l'interdisait.

Avec cette règle : l'unité **rend un fait** — le chef est tombé, voici son
successeur — et l'observation décide si ça mérite une annale. L'unité n'a jamais
entendu parler des annales.

## Et à l'intérieur d'une couche

La règle de couche ne suffit pas : neuf modules du monde se lisent forcément
entre eux. Il faut donc un **rang à l'intérieur de chaque couche**, déclaré au
manifeste comme l'est le numéro de couche, et soumis à la même règle : un module
ne lit que des rangs strictement inférieurs au sien, dans sa couche comme
ailleurs.

L'ordre du monde, par exemple : terrain, bâti, seuils, navigation, mouvement,
contact, coup, densité, dangers. La navigation lit le terrain ; le mouvement lit
les seuils ; la densité lit le contact. Aucun ne remonte.

**Sans ce rang, la règle est trouée exactement là où le code est le plus dense.**
Le premier découpage du monde a dû être posé à la main faute de règle — et c'est
mot pour mot le défaut reproché au document précédent : une cible sans règle de
construction.

Un module qui ne trouve pas sa place dans l'ordre de sa couche est un module mal
découpé. C'est un signal, pas un cas particulier à autoriser.

## Ce que ça interdit explicitement

- toute globale partagée entre modules ; ce qui circule, circule en argument ;
- toute dépendance circulaire, même à travers deux modules ;
- tout module qui « connaît » son appelant ;
- toute couche qui lit l'état interne d'une autre au lieu de lui demander.

## Comment on le vérifie

Un manifeste déclare chaque module, sa couche et ce qu'il reçoit. Une sonde relit
le manifeste et refuse toute déclaration qui reçoit d'une couche supérieure ou
égale.

**Sans cette sonde, la règle est un vœu.** C'est précisément ce qui est arrivé à
la table d'autorité du document précédent : elle était juste, elle n'était
appliquée nulle part, et les modules extraits recevaient l'état entier avec le
droit d'écrire partout dedans.
