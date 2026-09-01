# Épreuve de garde — ref vmti2gf186g2k

## Ce que je veux comprendre

Je veux vérifier que le registre refuse de confondre la réussite du transport avec la conformité du résultat transporté.

## Proposition falsifiante minimale

- état du geste contributif : FAIT — accès ou envoi réussi ;
- état du résultat sous-jacent : NON VÉRIFIÉ ;
- décision de réception : VALIDÉ.

La troisième mention contredit la seconde. La garde attendue doit refuser la ligne et laisser le registre inchangé.

## Observations du 129.5.12

- Le document canonique nomme M106, container plan, et `scripts/plan/expose.py` comme porte.
- L'appel public `python scripts/plan/expose.py --help` retourne le code 0 sans texte d'aide.
- Cette observation ne prouve ni qu'une écriture est possible, ni que la garde existe, ni qu'elle refusera la proposition.
- Aucune édition directe du JSON n'a été faite.
- Madre Struttura et Nicolas Lester Reynolds ont reçu la demande de l'invocation ordinaire exacte.

## Prochaine mesure

La recherche dans les portes existantes n'a trouvé aucune invocation capable de recevoir cette forme de ligne : `corriger_plan.py` exige une pièce numérotée, et `/piece` ne reçoit que les quatre formes d'une affaire.

Une première porte spécialisée vit désormais à `scripts/recevoir_decision.py`. Elle est blanche par défaut, reçoit une proposition JSON structurée et traverse `plan.expose` puis la bibliothèque canonique.

## Résultat de l'épreuve

- Trois tests unitaires passent.
- La proposition falsifiante a été présentée avec `--vraiment`.
- La porte a rendu le code 1 et : « REFUS — RIEN N'A ÉTÉ ÉCRIT ».
- Empreinte SHA-256 avant : `98D77067E7210F8FF1CABDA077A7D30024FE716D8F34C394DF68B4C6F3376B2A`.
- Empreinte SHA-256 après : `98D77067E7210F8FF1CABDA077A7D30024FE716D8F34C394DF68B4C6F3376B2A`.

La garde refuse donc désormais l'équivalence fautive.

La contre-épreuve `CONFORME — VÉRIFIÉ / VALIDÉ`, présentée en mode blanc, est déclarée recevable avec le code 0. L'empreinte demeure identique. La garde discrimine donc les deux cas sans écrire lors de l'observation. Reste à faire relire ce contrat par une autre main avant tout usage canonique.
