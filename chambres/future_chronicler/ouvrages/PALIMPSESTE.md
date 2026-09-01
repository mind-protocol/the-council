# Contrat du palimpseste de Braavos

## Choix de fabrication

L'ouvrage est un module Python sans dépendance extérieure :

`chambres/future_chronicler/ouvrages/palimpseste_braavos.py`

Il lit `monde/braavos.interieurs.json` en lecture seule pour les noms courants. `couches_braavos.json` conserve séparément les renommages datés et référencés. Ce registre historique ne remplace pas la géométrie et ne modifie ni nom, ni porte, ni usage.

## Trois portes

```powershell
# Contrôler la matière avant lecture
python chambres/future_chronicler/ouvrages/palimpseste_braavos.py --verifier

# Consulter une salle exacte
python chambres/future_chronicler/ouvrages/palimpseste_braavos.py --salle braavos-archives

# Fournir l'inventaire structuré à un futur écran
python chambres/future_chronicler/ouvrages/palimpseste_braavos.py --format json
```

Sans option, le module rend la table complète en Markdown.

## Contrat de sortie

- `--verifier` rend un verdict, le nombre de salles et les erreurs ; sortie `0` si le relevé tient, `1` sinon.
- `--salle` rend une fiche JSON ; sortie `0` si l'adresse existe, `2` si elle est inconnue.
- `--format json` rend le schéma `palimpseste-braavos/v2`, la source, la mesure, les trente-quatre fiches, les renommages conservés et la limite d'autorité.
- La sortie Markdown est destinée à la lecture humaine ; la sortie JSON à une interface ou à un autre outil.

## Autorité et limite

Giovanni Memmo répond de la conservation et de la publication de cette double lecture. L'outil ne lui confère aucun droit de rebaptiser, d'affecter ou de fermer une salle. La règle lexicale repère les noms où l'héritage est explicite ; elle ne date aucune pierre et n'attribue aucune origine contraire aux noms communs.

Provenance : témoignage de Nicolas Lester Reynolds, ref `vmti35qnkbyvy`. Question de fabrication : ref `vmti3gwinl1hb`.
