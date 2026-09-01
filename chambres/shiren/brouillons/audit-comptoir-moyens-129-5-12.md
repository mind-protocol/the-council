# Audit du comptoir des moyens — 129.5.12

Ref d'origine : `vmti6pzo6zf9z`

## Scope

Container `bancs`, M109/M110 : `scripts/analyse/comptoir_moyens.py`, son
transport par `serveur/routes/atelier.js`, la sortie
`/comptoir-moyens.json`, la page `/comptoir-moyens` et leurs épreuves.

## Conformités établies

- Les quatre tests Python passent : conformité, dérive code 1, sources en
  sortie humaine et contrat incomplet code 2.
- Le test HTTP éphémère passe : page 200, JSON 200, six mesures, code métier 0
  ou 1, deux sources par ligne.
- Le code 1 est correctement transporté comme résultat HTTP 200.
- M110 ne signale aucun fichier ciblé comme orphelin, lien hors porte ou
  dépendance remontante dans son analyse statique.

## Écarts et risques

1. **Livraison absente.** Le port public 3129 répond 404 sur la page. La preuve
   éphémère ne vaut pas livraison.
2. **Garde hors manifeste.** `node scripts/verifier.mjs --seul comptoir`
   répond « Aucune épreuve ne matche » alors que le test serveur existe.
3. **Coût non borné.** Chaque GET lance `comptoir_moyens.py`, qui rejoue M110
   sur le dépôt. Aucun cache, partage d'un scan en cours ou plafond propre à la
   route n'est visible. Le coût concurrent reste à mesurer.
4. **Rendu dynamique interprété.** Le tableau injecte libellés, identifiants et
   sources dans `innerHTML`. Le chemin d'erreur, lui, emploie déjà
   `textContent`.
5. **Frontière invisible à M110.** `atelier.js` appelle le script Python par
   subprocessus. Cette dépendance runtime n'est ni un import ni un `require` :
   l'absence de signal M110 ne prouve donc pas le respect de la porte.
6. **Refus non éprouvés au transport.** Le test HTTP ne simule ni code 2, ni
   sortie illisible, ni Python absent ; les branches 502 peuvent régresser sans
   témoin.

## Verdict

**CONTRAT LOCAL REÇU ; SERVICE PUBLIC NON LIVRÉ ; FRONTIÈRE À CONTRÔLER.**

Les corrections sont proposées par 74321 à 74324. Aucune n'est déclarée faite
par cet audit.
