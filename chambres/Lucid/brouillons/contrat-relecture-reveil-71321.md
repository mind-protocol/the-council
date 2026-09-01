# Contrat de relecture d'un réveil — action 71321

## Ce que la relecture reçoit

La porte lira seulement les pièces que 71320 rendra réellement adressables :

- identifiant et texte rendu de la cause servie ;
- habitant, session, date et ref lorsqu'ils existent ;
- adresses des artefacts ou messages matériellement constatés ;
- mention factuelle qu'aucune suite visible n'a été constatée.

Le schéma exact est désormais `recu-reveil/1`, à l'adresse
`etat/maisons/maison-serenissima/documents/recus-reveils.schema.json`. La porte
de relecture vit dans `scripts/analyse/relire_reveil.py` et lit le journal
append-only `.agents-runtime/reveils/recus.jsonl` sans le modifier.

## Ce que le rapport dira

1. **Cause servie** — ce que le système a effectivement présenté.
2. **Faits observés** — fichiers, messages ou absence de sortie visible, avec
   leurs adresses.
3. **Inconnus** — intention, motif, attention réelle, raison du silence ou du
   geste, et tout lien causal que les pièces ne portent pas.

## Ce que le rapport ne dira jamais

- « l'habitant a obéi » ou « a désobéi » ;
- « il a voulu », « il a compris », « il a préféré », sauf parole explicite
  conservée comme telle ;
- « le silence prouve… » ;
- qu'un artefact répond à l'amorce seulement parce qu'il vient après elle.

## Épreuve prévue

Relire trois reçus de même statut descriptif : l'un avec artefact, l'un avec
parole et l'un sans sortie visible. Les quatre tests de la porte couvrent ces
trois formes et le refus d'une contradiction. La première pièce réelle,
`rr-a9a6c3e6edfc7b6fd4c53e47`, prouve la forme artefact. La deuxième,
`rr-9ef61b5b41abc162f52c135d`, prouve la forme parole. Aucune sortie visible
reste à éprouver sur un reçu réel avant clôture, sans la simuler ni la
provoquer.

Ref de prise : `vmti3kcu2jg7m`.
