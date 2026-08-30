# Trace de décision

## 1. Ce que c'est

Ce qu'un acteur laisse derrière lui chaque fois qu'il décide, pour qu'on puisse
comprendre sa décision **sans rejouer la bataille.**

## 2. Ce qu'il possède

La trace appartient à l'acteur qui a décidé ; ce module possède **la forme
qu'elle doit avoir** et **le recueil** de ce qui a été signalé.

Une trace porte :

- **qui** a décidé, **à quelle couche** de lui-même, et **quand** ;
- **l'ordre courant** et **l'objectif courant** au moment du choix ;
- **les faits et croyances utilisés**, chacun avec sa source, son âge et sa
  confiance — et l'intervalle plutôt que le nombre quand il s'agit d'un effectif ;
- **les options envisagées**, chacune avec sa projection, ses risques, ses gains,
  son score et, si elle a été écartée, **son motif de rejet** ;
- **le choix** et **sa raison** ;
- **l'heure du prochain examen**.

## 3. Ce qu'il lit

Ce que les acteurs signalent : combattants, unités, commandants, conduite. Il ne
va rien chercher dans leur état interne.

## 4. Ce qu'il produit

Les trois questions, sur n'importe quel acteur à n'importe quelle seconde, **sans
rejouer** :

1. **Qu'est-ce qu'il croyait ?** — les faits et croyances qu'il avait alors, avec
   leur âge.
2. **Qu'a-t-il envisagé, et pourquoi celle-ci ?** — les options, leurs
   projections, leurs rejets, et le motif du choix.
3. **Quand devait-il réexaminer ?** — sans quoi un réexamen manqué ne se voit pas.

Et une sortie de contrôle : **la pensée affichée d'un acteur**, qui se lit ici et
nulle part ailleurs.

## 5. Invariants

- **La pensée affichée est une lecture de la trace, jamais une écriture
  parallèle.** Deux vérités sur le même homme au même instant, c'est un écran qui
  ment sans qu'aucune sonde ne le sache.
- Une décision sans trace n'a pas eu lieu : la sonde compte les décisions
  signalées contre les changements d'ordre observés, et l'écart est une faute.
- Une trace nomme la couche qui a réellement tenu les jambes, pas la branche de
  code qui a produit le déplacement.
- Toute option écartée porte un motif de rejet ; une liste d'options sans rejets
  ne prouve rien.
- Une trace est complète au moment de la décision, jamais complétée après coup.
- Un réexamen prévu et non tenu est visible sans calcul.

## 6. Ce qu'il ne fait pas

- **Il ne décide pas**, ne recommande pas, ne rejoue pas. Il enregistre ce qui
  lui est remis.
- **Il n'écrit rien dans la simulation.** Aucun champ, aucun retour d'information
  vers l'acteur observé : un acteur ne lit jamais sa propre trace.
- **Il ne reconstitue pas ce qu'on ne lui a pas donné.** Une croyance non
  signalée reste absente ; on ne la déduit pas de l'état final.
- **Il ne résume pas.** Une trace agrégée sur une minute ne répond plus à « à
  cette seconde-là, pourquoi ? ».
- **Il n'invente pas de cause.** Faute de motif, la trace porte « sans motif », et
  c'est une information.

## 7. Ce que l'ancien moteur faisait mal ici

**Il n'y avait rien à tracer au niveau de la conduite** : aucun objectif, aucune
mission, aucune réserve, et tous les ordres venaient d'un scénario écrit à
l'avance — une décision qui n'est pas prise ne laisse pas de trace, et l'absence
ne se voyait nulle part.

Pour le reste, les grandeurs de cette fiche — part des décisions tracées, part
des options portant un motif de rejet, part des réexamens prévus et tenus —
**n'ont pas été mesurées** sur le moteur précédent.
