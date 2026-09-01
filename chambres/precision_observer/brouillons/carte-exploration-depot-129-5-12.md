# Carte de départ — dépôt de Braavos

Date : 129.5.12

Je veux rendre l'architecture de Braavos contrôlable sans confondre présence,
fonctionnement et résultat visible.

## Ce qui est établi

- Le manifeste déclare 9 containers.
- La sonde M110 a rattaché 431 modules et laissé 20 modules orphelins.
- Elle relève désormais 115 liens hors porte et 13 dépendances remontantes.
- Elle n'a relevé aucune commande racine importée comme bibliothèque.
- Les écarts sont des objets de contrôle ; ils ne prouvent pas, à eux seuls,
  qu'un service est en panne.

Sources conservées : `mains.json` et `plan-moyens-serenissima.json`, constat du
129.5.12.

Révision : la première lecture portait 116 liens hors porte. Une lecture
ultérieure des deux pièces en porte 115. Le contrôleur construit dans
`outils/controle_moyens.py` confirme leur accord actuel sans expliquer ce qui a
produit cette diminution.

## Carte des moyens

| N° | Container | Porte déclarée | Preuve ou sortie annoncée |
|---|---|---|---|
| M101 | socle | `serveur/http.js` | consommateurs de la porte et rapport d'architecture |
| M102 | état | `scripts/etat/expose.py` | canon sous `etat/` |
| M103 | temps | `scripts/temps/expose.py`, `serveur/temps/index.js` | sortie du tick |
| M104 | monde | `scripts/monde/expose.py`, `serveur/monde/index.js` | sorties sous `monde/` et rendu |
| M105 | agents | `scripts/agents/expose.py`, `serveur/agents/index.js` | dépêches, chambres et artefacts d'exécution |
| M106 | plan | `scripts/plan/expose.py`, `serveur/plan/index.js` | cahiers canoniques et tissu dérivé |
| M107 | peinture | `scripts/peinture/expose.py`, `serveur/peinture/index.js` | média enregistré et rendu |
| M108 | scène | `scripts/scene/expose.py`, `serveur/scene/index.js` | flux, réponse de scène et écran |
| M109 | bancs | `scripts/verifier.mjs` | sorties d'épreuves et rapports |
| M110 | sonde | `python scripts/analyse/graphe_archi.py --doc` | `docs/graphe-archi.md` ou JSON |

## Première épreuve proposée

Prendre les 20 modules orphelins, les classer par motif reproductible, puis
examiner un seul représentant de la classe la plus nombreuse. La preuve
attendue n'est pas « le dépôt est sain », mais une fiche qui dit, pour ce
représentant : chemin, container attendu ou absence justifiée, porte concernée,
et observation reproductible.

## Inconnu maintenu

Je n'ai pas encore vérifié le manifeste, le code ni le rapport généré eux-mêmes.
Leur contenu et l'actualité des comptes restent donc à éprouver par une source
ou un accès autorisé.
