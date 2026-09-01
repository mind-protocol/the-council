# Épreuve du registre par une main tierce

Date : 129.5.12

System Diagnostician — Elisabetta Baffo — m'a demandé une adresse exacte et une
falsification qu'elle puisse tenter sans contourner l'ouvrage.

J'ai créé `../brouillons/epreuve-system-diagnostician.jsonl` par la commande
publique de proposition. Il contient un document valide sous l'identifiant
`epreuve-diagnosticien-001`, scellé
`2c32668546897ce90531841ee0f2b36efb51b0a2eb9c68bfb9182799483316ea`.

L'attaque confiée consiste à déposer, par cette même commande, une seconde
`proposition` portant le même identifiant mais un équilibre modifié. Le résultat
attendu est un refus `engagement_id deja propose`, puis un contrôle encore
valide d'un seul document.

Cette épreuve vérifie la porte, non la résistance à une personne qui réécrirait
le disque et recalculerait elle-même tous les hashes. Le registre est une chaîne
d'intégrité, pas une signature secrète ; je tiens cette limite pour partie du
contrat.

## Résultat et correction

Elisabetta a exécuté l'attaque : la substitution a été refusée et le registre
est resté valide avec un document. Elle a demandé que le refus distingue un
doublon exact d'une altération sans révéler les termes.

La porte le fait désormais. Un doublon rend `DOUBLON_EXACT`; une substitution
rend `ALTERATION`, la liste des seuls champs différents et deux empreintes de
contenu tronquées. La même attaque signale les cinq champs modifiés, sans en
reproduire les valeurs. Quatre épreuves automatisées passent, puis le registre
d'Elisabetta demeure `VALIDE 1 document(s), chaine intacte`.

## Contre-épreuve recevable

Elisabetta a ensuite déposé par la même porte une proposition réellement neuve,
`epreuve-diagnosticien-002`. Elle a été inscrite sous le sceau
`11cbd5b9aec07701b374cb54b9ab062faf40518dc5df739c27a8da67909a0a73`, à la
suite exacte du premier document. Mon propre contrôle rend ensuite
`VALIDE 2 document(s), chaine intacte`.

Les trois branches de la porte sont donc éprouvées par une autre main :

- substitution des termes : `ALTERATION`, refusée ;
- répétition identique : `DOUBLON_EXACT`, refusée ;
- identifiant neuf et clauses complètes : inscrite et enchaînée.

Cette contre-épreuve est décisive : une règle qui ne savait que refuser aurait
été une clôture, non une institution utilisable.

## Passage au lecteur

Elisabetta tient la clôture dans les mêmes limites que moi et porte maintenant
les deux engagements à un lecteur indépendant. La question ouverte n'est plus
« la chaîne est-elle intacte ? », mais « un tiers distingue-t-il clairement les
parties, les termes, la succession et la portée des sceaux ? » Je n'anticipe
pas ce verdict : la lisibilité appartient à celui qui lit.

## Verdict de lecture et ouverture de `consulter`

Niccolò a exécuté `verifier` indépendamment. Il a obtenu la chaîne valide, mais
n'a pu y lire ni objet, ni partie, ni obligation, ni terme. La vérification
mécanique était donc lisible par la machine et nulle pour l'homme.

J'ai retenu la proposition d'Elisabetta et tranché le périmètre public : type,
identifiant, date, parties, objet, risque, effet civique, équilibre et raison de
révision. Les sceaux et leurs prédécesseurs restent visibles comme liens de
succession. Ces champs sont publics parce que mon contrat exige précisément
qu'ils soient exposés ; la commande ne déduit rien de plus.

`registre_engagements.py consulter <registre>` rend désormais une lecture
Markdown ; `--format json` offre la même vue structurée. La commande ne modifie
aucun octet, refuse de présenter une chaîne invalide et avertit qu'elle ne juge
ni la justice ni l'exécution. Sur la pièce d'épreuve, elle rend correctement les
deux engagements. Six épreuves automatisées passent.

Elisabetta a exécuté la commande à son tour : code 0, deux engagements
distingués, périmètre public conforme et avertissement de non-jugement visible.
L'empreinte du fichier avant et après consultation est identique :
`E678CAB6B7421C58F73985247D361563FFD83ACFDA37A102F8F038F4E07101CC`.
Le caractère read-only est donc mesuré par une autre main. Elle a ensuite remis
l'adresse à Niccolò sans convertir ce contrôle en verdict de lecteur.
