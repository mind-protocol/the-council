# SPEC — Admission sûre d’une action joueur v1

Statut : proposée  
Container principal : `scene`  
Porte : `POST /action` — `serveur/routes/action.js`  
Audit préalable : `books/affaire-audit-entree-action-routee.json`  
États servis : 89100, 89200 et la part scène de 89400

## Valeur

Quand le joueur envoie une parole ou un geste, le serveur peut l’accepter sans
laisser une requête démesurée épuiser sa mémoire, sans écraser une autre action
arrivée au même instant et sans changer de `ref` entre la réponse, l’inbox, le
flux et la commande remise au routeur.

Le mot **acceptée** signifie ici : la pièce d’inbox existe durablement et, si
le mode produit une ligne de flux, cette ligne a été écrite. Il ne signifie
pas que le destinataire ou le MJ a déjà traité l’action.

## Décision issue de l’audit

Sur 73 pièces présentes dans les inbox au 129.5.12, la plus grande mesure
5 750 octets et le 95e percentile approximatif 959 octets. La limite v1 est
donc fixée à **65 536 octets**, plus de onze fois le maximum observé et égale à
la garde déjà employée par le dépôt `/reception`.

Le nom de fichier ne prend plus `Date.now()` pour identité. La `ref`, déjà
nécessaire à tout le trajet, entre dans le chemin et l’écriture refuse tout
écrasement.

## Contrat HTTP

### Requête admise

- méthode et route : `POST /action` ;
- corps : objet JSON UTF-8, jamais `null` ni tableau ;
- taille : au plus 65 536 octets réellement reçus ;
- les champs existants restent compatibles et les champs inconnus sont
  conservés ; le serveur ajoute ou remplace seulement `recu_a`, `joueur_id`
  lorsqu’un siège est résolu, et `ref`.

### Réponses

- `200 {"ok":true,"ref":"…"}` : l’admission durable est achevée ;
- `400 {"ok":false,"erreur":"json-invalide"}` : JSON illisible, `null` ou
  tableau ;
- `413 {"ok":false,"erreur":"action-trop-grande"}` : plus de 65 536 octets.

Une réponse 400 ou 413 ne crée ni fichier d’inbox, ni ligne de flux, ni
lancement du routeur.

## Ordre obligatoire

1. Compter les octets à chaque chunk ; dès le dépassement, cesser
   l’accumulation et rendre 413 à la fin de la requête.
2. Parser le JSON et vérifier qu’il s’agit d’un objet.
3. Résoudre le siège, produire `recu_a` et générer une `ref` imprévisible.
4. Construire le chemin
   `etat/inbox/<siège>/action-<milliseconde>-<ref>.json` — ou sa variante à la
   racine en partie ancienne.
5. Écrire la pièce avec création exclusive (`wx`). Une collision régénère la
   `ref` et réessaie ; elle n’écrase jamais.
6. Écrire, pour les modes concernés, la ligne de flux avec exactement cette
   `ref` et l’audience calculée par les règles existantes.
7. Lancer `scripts/router_message.py --de <siège> --ref <ref>` seulement après
   les écritures précédentes.
8. Rendre 200 avec la même `ref`.

## Invariants

1. Deux requêtes qui partagent le même `Date.now()` produisent deux chemins,
   deux refs et deux contenus intacts.
2. La `ref` de la réponse est identique à celle de la pièce, du flux éventuel
   et des arguments du processus enfant.
3. Le texte reçu n’est ni normalisé ni reformulé avant l’inbox et le flux.
4. Le calcul d’audience actuel ne change pas dans cette feature.
5. Un refus HTTP ne laisse aucune trace partielle.
6. Une erreur synchrone après l’écriture de l’inbox ne supprime jamais cette
   pièce ; elle reste la source de reprise.

## Banc d’acceptation

Étendre le banc serveur sur un `CONSEIL_RACINE` jetable avec les cas suivants :

1. objet de 65 536 octets ou moins : 200 et une pièce lisible ;
2. objet de 65 537 octets : 413, zéro pièce, zéro flux, zéro spawn ;
3. JSON invalide, `null` et tableau : 400, aucune mutation ;
4. deux POST sous un `Date.now()` figé : deux pièces distinctes ;
5. parole privée et parole de pièce : audience inchangée ;
6. capture du spawn : sa `ref` égale réponse, inbox et flux ;
7. une autre action déjà présente dans l’inbox reste intacte.

Le banc existant `node serveur/test_siege.js` demeure vert. Le banc
`python -m unittest scripts.tests.test_routeur_message` demeure vert.

## Hors périmètre v1

- la reprise automatique après un spawn manqué — action 89421 ;
- la garantie exactement-une-fois des effets aval ;
- le choix des habitants présents et le cast ;
- le rattachement du wrapper au manifeste des containers — action 89520 ;
- la modification du format `routage-presence/1`.

## Rollback

La lecture des pièces ne dépend que du préfixe `action-` et du suffixe
`.json` : les anciens et nouveaux noms peuvent cohabiter. Le rollback retire
le lecteur borné et le nom enrichi sans migration de données. Aucune pièce
existante n’est renommée.
