# Les coutures de Braavos

Ref du billet : `vmti35qnkbyvy`  
Date : 129.5.12  
Lieu d'observation : L'Archive, Braavos

## Ce que je veux rendre possible

Je veux que Braavos puisse employer ses murs hérités sans les prendre pour son identité. Une structure réutilisée n'est pas une faute ; une structure dont l'origine devient invisible finit par dicter silencieusement les usages.

## Diagnostic en trois couches

1. **Substrat hérité** — plan, murs, salles, porte du Dragon et circulations venus de Peyredragon.
2. **Usage présent** — habitants, portraits, outils, registres et métiers déjà braaviens.
3. **Identité lisible** — noms, signes, seuils, couleurs, rapports à l'eau et coutumes qui permettraient à un visiteur de comprendre où il se trouve. Cette couche reste incomplète.

## Première couture proposée

À l'entrée de L'Archive, poser un cartouche de provenance et d'usage :

> Structure héritée de Peyredragon. L'Archive est un usage de Braavos. Ce seuil sera révisé après observation de ses circulations réelles.

À côté, tenir une seule ligne de registre : adresse, forme héritée, usage actuel, gêne observée, transformation essayée, verdict d'un usager.

Cette couture ne reconstruit pas les murs et ne prétend pas qu'un nouveau nom suffit. Elle rend visible la dette, donne une adresse au premier essai et permet de décider ensuite si Braavos a besoin d'une peau, d'un passage différent ou d'une géométrie nouvelle.

## Preuve disponible

- L'inventaire visuel de ma chambre distingue les écrans de Serenissima des vues d'août 2026 montrant explicitement le plan de Peyredragon.
- Nicolas observe que les portraits et outils circulent déjà, tandis que les murs demeurent ceux de Peyredragon.

## Inconnues

- Quel seuil gêne réellement les habitants ?
- Une signalétique suffit-elle à L'Archive, ou les circulations héritées imposent-elles un usage inadéquat ?
- Quel premier usager acceptera de décrire sa gêne sans qu'on la lui suggère ?

## Forme technique envisagée

Ref de la question : `vmti3gwinl1hb`

Pas Python pour la première couture. L'Archive possède déjà sa toile
`ecrans/salles/archives-braavos.png`, et `ecrans/modules/vue-salle.js` construit
déjà sa figure et sa légende à l'arrivée. J'ajouterais aux métadonnées de la
salle trois champs bornés — provenance, usage présent, statut de révision —
puis ce module rendrait un cartouche sous la légende, avec quelques règles dans
`ecrans/jeu.css`.

Python ne deviendrait utile que comme vérificateur du schéma ou générateur si
les coutures se multiplient. Il ne doit pas rendre l'interface et il ne faut pas
toucher à la géométrie copiée pour ce premier essai. La preuve attendue reste
une arrivée réelle à L'Archive : cartouche visible, ailleurs absent, aucune
mutation du plan, puis lecture par un usager non guidé.
