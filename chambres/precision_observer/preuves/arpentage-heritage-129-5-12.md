# Première preuve — arpentage des murs hérités

Date : 129.5.12  
Origine : parole de Nicolas Lester Reynolds, ref `vmti35qnkbyvy`

## Ouvrage

Adresse :
`C:/Users/reyno/le-conseil2/chambres/precision_observer/ouvrages/arpentage-heritage/index.html`

L'interface distingue l'origine rapportée, l'observation matérielle, l'usage
braavosi, la transformation désirée, son état, sa preuve et sa réserve. Une
transformation `ESSAYÉE` ou `RÉALISÉE` sans preuve rend la fiche non recevable.

## Épreuve

- `app.js` passe le contrôle syntaxique de Node.
- La page et sa feuille de style ont été rendues par Chrome.
- La capture visible est conservée sous `preuves/arpentage-heritage.png`.
- Le point de départ affiche correctement `NON ESSAYÉE` : aucun mur n'a été
  choisi ni mesuré par la construction de l'outil.

## Limite

Le rendu est éprouvé ; la formation et le téléchargement d'une fiche remplie
ne le sont pas encore par un second habitant. L'origine peyredragonienne reste
un témoignage référencé de Nicolas, non une analyse matérielle de la pierre.

## Répartition technique après la question de Nicolas

Ref : `vmti3gwinl1hb`.

- HTML/CSS/JavaScript : remplir et télécharger la fiche dans le lieu.
- Python : valider la pièce sans mesurer ni transformer le mur.
- Porte du monde : transformation matérielle ultérieure, après choix du
  segment et preuve attendue.

Le validateur `valider_fiche.py` passe trois tests : réserve pour dimensions
incomplètes, refus d'un état ESSAYÉE sans preuve, réception d'un état RÉALISÉE
avec dimensions et preuve.
