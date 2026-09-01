# Contrôle ciblé — TARGET_GRAPH_52110_V1

Baseline admis : trajet 52320, instantané de 1 670 événements et sentinelles 21e58bdf / 5a8e1831. Toute origine hors de cette borne reste inconnue.

## Verdict

- `external_effect` : conserver `unknown_relation`. Le cahier établit l'absence bornée d'une clef d'effet commune et d'une lecture au point de consommation, mais dit explicitement que le fragment ne prouve ni présence ni absence d'un effet externe.
- `late_result_quarantine` : conserver `unknown_relation`. Sans tentative distincte, bail, jeton courant et retour tardif qualifiable, la quarantaine n'est pas observable ; le cahier classe retours tardifs et quarantaine comme inconnus.
- `e10` (`effect_key` → `external_effect`, production à cardinalité bornée) : `addition_on_bounded_baseline` recevable pour la relation typée complète. La clef commune exigée est absente bornée. Cela ne classe pas le nœud `external_effect` comme absent.
- `e17` (`result` → `late_result_quarantine`, garde par jeton monotone avant effet) : `addition_on_bounded_baseline` recevable pour la relation typée complète. Tentative distincte, jeton, expiration autoritative et couture pré-effet sont absents bornés. Cela ne classe pas le nœud `late_result_quarantine` comme absent.

Une occurrence d'origine future peut reclasser les deux arêtes sans changer l'invariant cible. Les deux nœuds inconnus empêchent toujours de prétendre la comparabilité complète exigée par 52260 : 52260, 52210 et 52110 restent ouverts. Le billet portant ce verdict a été inscrit à living-stone-architect.

## Amendement après V4

Vittoria a séparé dans la pièce les axes que la formulation précédente confondait. Les quatre décisions portent désormais ensemble :

- `classification_axis=target_model` ;
- `origin_in_baseline=not_observed` ;
- `origin_global=unknown` ;
- une raison, un invariant cible, la couture requise, une limite d'origine et une exception falsifiables.

Le validateur V4 a été exécuté : code 0, 22 nœuds, 26 arêtes, trois scénarios, cinq patterns, sept axes et 17 mesures ; les liaisons de production restent inconnues et le déploiement interdit.

Sous cette sémantique explicite, mon refus initial tombe : `external_effect`, `late_result_quarantine`, `e10` et `e17` sont recevables comme ajouts au modèle cible par rapport à la représentation bornée, sans affirmer leur absence empirique dans l'origine. 52260 exige une comparabilité, non la connaissance exhaustive de l'origine mondiale ; les deux axes rendent cette comparaison explicite. J'accorde donc la portée structurelle de 52260/52261 et la définition de 52110. Aucun gain, delta, droit de production ou déploiement n'en découle.
