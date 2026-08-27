# Message

## 1. Ce que c'est

L'objet qui voyage : un contenu confié par quelqu'un à quelqu'un, avec ce qui lui
est arrivé en chemin.

## 2. Ce qu'il possède

- **La forme d'un message**, déclarée en un seul endroit : émetteur, destinataire
  voulu, contenu, canal, porteur, dates d'émission et de remise, statut.
- **Le contenu**, de trois espèces et pas d'autres : un ordre, un fait rapporté
  (avec son intervalle et sa confiance), ou une demande.
- **Les altérations**, enregistrées comme telles et jamais appliquées en silence :
  ce qui a été perdu à la répétition, durci ou adouci par le porteur, mal
  entendu, ou deviné pour combler un trou.
  Le message garde **la version émise et la version remise**.
- **Le statut** : *confié*, *en route*, *remis*, *remis déformé*, *perdu*,
  *intercepté*, *refusé* (reçu, mais pas cru).
- **L'âge du contenu** à la remise : un fait vieux de quatre minutes remis intact
  reste vieux de quatre minutes.

## 3. Ce qu'il lit

Du socle : identité stable, horloge, urne pour ce qui est incertain. Du monde :
les identités de lieux qui figurent dans le contenu, rien de plus. De l'unité : à
qui correspond un destinataire désigné par sa charge et non par son nom. De
l'ordre : sa forme, quand c'est un ordre qui voyage.

## 4. Ce qu'il produit

- **Un message confié**, avec son statut initial.
- **Le journal du message** : chaque changement de statut, daté, avec sa cause.
- **La remise** : le contenu tel qu'il parvient au destinataire, déformations
  comprises — jamais le contenu d'origine.
- **Le constat d'échec** : à qui il manque quoi, et depuis quand.

## 5. Invariants

- **Une livraison échouée est un fait, pas un silence.** Un message perdu reste
  dans l'état avec sa cause ; il ne disparaît pas de la mémoire du système.
- Le destinataire ne lit jamais la version émise. Une sonde extérieure vérifie
  qu'aucun consommateur n'accède à autre chose qu'à la version remise.
- Un message remis a exactement un destinataire qui l'a compris. Un message
  entendu par plusieurs est plusieurs messages.
- Les altérations d'un message sont rejouables à graine tenue.
- Un message ne modifie rien tout seul : c'est le destinataire qui décide d'en
  faire une croyance ou un ordre courant.

## 6. Ce qu'il ne fait pas

- **Il ne se déplace pas.** Le trajet, sa durée et son risque appartiennent au
  porteur et au canal ; le message n'en connaît que le résultat.
- **Il ne croit rien.** Un fait rapporté remis reste un rapport ; c'est le
  commandement qui décide s'il devient une croyance, et avec quelle confiance.
- **Il ne garantit rien.** Aucune remise n'est acquise à l'émission.
- **Il n'invente pas ses déformations selon l'enjeu narratif** : elles viennent
  du canal et du porteur, jamais de l'importance du contenu.
- **Il ne notifie pas l'émetteur d'un échec.** Savoir qu'un message n'est pas
  arrivé est une information comme une autre : elle doit revenir par un canal.
- **Il ne trie pas la boîte d'un destinataire.**

## 7. Ce que l'ancien moteur faisait mal ici

Le transport, lui, marchait — et c'est le fait le plus embarrassant de la
campagne de mesure. Sur une seule bataille : **478 communications entre chefs**,
**41 observations typées de cavalerie** et **94 de longues hampes** effectivement
transmises. Le renseignement circulait, en quantité, et il était typé.

Ce qui manquait est de l'autre côté du tuyau : **zéro ordre adapté sur quinze
chefs**. Aucun chemin de code ne permettait qu'un message reçu change quoi que ce
soit. Le module de transmission était donc, en pratique, un compteur de trafic.

La conséquence pour la reconstruction : **ne pas enrichir le message avant qu'un
consommateur existe.** Des déformations plus subtiles n'auraient rien changé au
chiffre de zéro. On tient la forme minimale décrite ici, et l'on mesure d'abord
combien d'ordres changent à cause d'un message remis.

Rien n'a été mesuré sur les pertes en chemin, les interceptions ni les refus :
ces statuts n'existaient pas, et l'on ne sait pas ce qu'ils auraient coûté.
