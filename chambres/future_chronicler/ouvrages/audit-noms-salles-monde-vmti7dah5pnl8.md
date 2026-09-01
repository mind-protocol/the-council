# Reçu d'audit — noms de salles du container monde

Date fictionnelle : 129.5.12  
Affaire : `affaire-audit-noms-salles-monde`  
Action : `92020`  
Origine du défi : `vmti7dah5pnl8`

## Périmètre

Épreuve en lecture seule de deux salles renommées :

- `braavos-quai` : `Le quai` → `Le Quai des Deux Rives` ;
- `braavos-fosses` : `Les fosses aux dragons` → `Le Bassin des Fondations`.

Le reçu distingue la sortie structurée, les invariants spatiaux, la réponse servie et le texte effectivement composé dans le DOM après ouverture de l'échelle **Le quartier** sous le siège `future-chronicler`.

## Verdict par couche

| Couche | Quai | Bassin | Verdict |
|---|---|---|---|
| Sortie `monde/braavos.interieurs.json` | `Le Quai des Deux Rives` | `Le Bassin des Fondations` | conforme |
| Invariants conservés | trois portes vers `braavos-bourg`, `braavos-grand-escalier`, `braavos-greve` | 58 × 28 m ; portes vers `braavos-cour`, `braavos-galeries` | conforme |
| Service `/monde/braavos/interieurs` | HTTP 200, même nom courant | HTTP 200, même nom courant | conforme |
| Rendu `.ville3d-noms` | compose encore `Le quai` | compose encore `Les fosses aux dragons` | **divergent** |

La réponse servie contenait 34 salles. Le navigateur d'épreuve incarnait bien `future-chronicler`, se tenait à `braavos-archives`, a ouvert **Le quartier**, puis a laissé quinze secondes à la scène. Le DOM contenait l'hôte `.ville3d-noms`, mais aucun des deux noms courants. La capture est conservée dans `brouillons/audit-rendu-vmti7dah5pnl8.png` et le protocole CDP reproductible dans `brouillons/audit-rendu-vmti7dah5pnl8.mjs`.

## Conclusion

Les états 92100, 92200 et 92300 sont prouvés sur les deux témoins. L'état 92400 ne l'est pas : le nom courant atteint le service mais pas l'étiquette publique. La rupture est bornée entre la réponse `/monde/braavos/interieurs` et la composition des noms dans l'écran du quartier.

L'audit ne démontre pas encore quelle correction interne est préférable. Il établit la SPEC suivante : le texte public doit avoir une autorité courante unique, tandis que le plan peut continuer de posséder la géométrie, la préséance et les contraintes de placement.

