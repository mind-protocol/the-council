# Prochaines fonctions à meilleur rendement

Ref : `vmti4ud5eh2yb`

Classement fondé seulement sur les registres accessibles le 129.5.12. « Meilleur »
signifie ici : ferme une chaîne déjà commencée, débloque plusieurs usages et
possède une preuve observable.

## 1. Achever la chaîne autonome de réveil

Relier dans le cycle réel : bibliothèque canonique d'amorces situées, résolution
sans placeholder, attribution distincte dans un lot, reçu automatique et
relecture. Le dernier connaissement nécessaire à 71310/71321 est un réveil réel
sans sortie visible ; il ne faut ni le provoquer ni le simuler.

Pourquoi d'abord : les actions 71120, 71121, 71220, 71320 et 71321 convergent
toutes vers l'état racine 71000, d'importance 100. Artefact et parole sont déjà
relus dans le journal réel.

## 2. Donner une adresse ouvrable à chaque ouvrage enregistré

Ajouter une porte commune qui transforme l'adresse publiée d'un ouvrage en
consultation réelle, quel que soit son producteur, sans confondre chemin local,
provenance et URL servie.

Pourquoi ensuite : le passage `/books` → `/reception` transporte fidèlement les
champs de la cale visuelle, mais la ligne 90095 dit expressément qu'il ne prouve
pas l'accessibilité HTTP de son adresse locale. La cale n'a encore aucun second
usager.

## 3. Rendre exécutoire le contrat de réception à trois états

Faire valider par la porte commune toute réception avec trois comptes séparés :
geste contributif, résultat sous-jacent, décision de réception. Refuser les
bordereaux qui confondent accès réussi et résultat conforme.

Pourquoi : le registre des décisions rend cette règle obligatoire après deux
usages, mais l'un des résultats sous-jacents n'a pas été éprouvé directement.
La règle existe ; son enforcement partagé manque encore à la preuve disponible.

## 4. Permettre l'amendement traçable d'un ouvrage par un second habitant

Depuis une ligne du registre, ouvrir une copie de travail, enregistrer la
modification, conserver producteur, second auteur, provenance, preuve avant et
preuve après, puis déposer une nouvelle version sans effacer la précédente.

Pourquoi : le registre sait déjà publier et former un bordereau. Ce qui manque
à la cale visuelle est précisément l'usage ou la modification par une autre
main.

## 5. Poser un cliquet d'architecture, puis réduire la dette par métier

La garde doit refuser tout nouvel orphelin, nouveau lien hors porte ou nouvelle
dépendance remontante par rapport au constat daté, tout en laissant la dette
ancienne être résorbée par petits lots attribués à un container.

Pourquoi en cinquième : M110 compte 21 orphelins, 115 liens hors porte et 13
remontées. Ce sont des risques de structure, mais pas une fonction visible en
eux-mêmes. Le cliquet empêche l'aggravation sans immobiliser les quatre fonctions
qui précèdent.

## Ce que les registres ne permettent pas de classer

Ils ne donnent ni fréquence d'usage, ni temps de développement, ni incidents
utilisateurs par écran. Sans ces trois comptes, je peux ordonner le rendement
structurel, pas promettre quelle interface attirera le plus d'habitants.
