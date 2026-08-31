# Fournisseur des appels d'agents

Tous les appels passent par `scripts/agents/runtime.py`. La fiction conserve
ses identifiants de session ; l'adapter traduit ceux-ci vers les identifiants
de thread propres à Claude ou à Codex et rend, dans les deux cas, le contrat
historique `result`, `usage`, `duration_ms`, `session_id`.

## Basculer toute la simulation

```powershell
python scripts/fournisseur.py codex --modele gpt-5.3-codex-spark --effort low
python scripts/fournisseur.py claude
python scripts/fournisseur.py
```

`chatgpt` est accepté comme alias de `codex`. Le choix est local à la machine,
dans `.agents-runtime/config.json`, et n'entre pas dans l'état joué. Pour une
seule commande, l'environnement est prioritaire :

```powershell
$env:LE_CONSEIL_FOURNISSEUR = 'codex'
python scripts/depecher.py --qui aldon-hask
```

Le modèle Codex par défaut est `gpt-5.3-codex-spark`, effort `low`. Ils peuvent
aussi être définis par `LE_CONSEIL_CODEX_MODELE` et
`LE_CONSEIL_CODEX_EFFORT`.

## Chemins couverts

- journée d'un homme, en CALL ou en CAST ;
- réveil de l'unique MJ ;
- juge séparé ;
- dépôt du vécu depuis les événements JSONL Codex.

Les CAST passent par un worker détaché. Un verrou inter-processus sérialise
deux réveils portant la même session logique, puis le second reprend le thread
au lieu d'échouer sur un identifiant déjà utilisé.
