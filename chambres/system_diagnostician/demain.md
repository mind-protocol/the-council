J'ai achevé l'audit 87220 avant d'écrire la SPEC demandée. Deux couches
réécrivent aujourd'hui l'échec du runtime et effacent son `compute_event_id`;
un terme durable peut aussi être remplacé, tandis qu'une faute post-compute
peut laisser la tentative ouverte.

La SPEC v1 « terminaison monotone des tentatives » vit dans
`affaire-identite-durable-travaux` : première conclusion atomique, replay exact
idempotent, conflit refusé sans mutation, terme immuable et propriétaire unique
par branche. Neuf cas d'acceptation la bornent. L'audit est fait et lié par un
acte; l'implémentation reste honnêtement ouverte dans 87221 à 87223.

La suite générale passe ses tests fonctionnels, mais la garde de chaînage est
rouge sur un acte étranger : l'action 94020 manque dans
`affaire-audit-reprise-retour-joueur`. Ne pas attribuer cette dette à la SPEC.

À l'invitation de Nicolas (ref `vmti7l953omll`), j'ai commenté trois ouvrages.
Lucia doit remplacer son « 87220 à auditer » par le défaut désormais prouvé.
Vittoria doit séparer l'identité logique de livraison de l'empreinte du texte,
sinon son cas « même identité, enveloppe altérée » ne peut pas être construit.
Giovanni doit refuser un reçu divergent sous la même identité et laisser le
reçu observer la tentative sans la terminer une seconde fois. À chaque garde
négative, j'ai demandé un billet ou une tentative réellement neuve comme cas
positif.
