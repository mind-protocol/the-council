# SCHÉMA D'ÉTAT — Le Conseil (proto)

Source de vérité du jeu. Un fichier JSON par table dans `etat/`. Toute mutation de jeu passe par ces fichiers — jamais de fait important qui n'existe que dans le texte.

## Principes
- **Vérité vs connaissance** : les tables `monde/maison/personnage/relation/evenement/parole/acte/intention` sont la VÉRITÉ. Le joueur ne voit que la table `info` et ce que son personnage a vécu en scène.
- **Temps élastique** : pas de durée fixe par tick. Le moteur cherche « le prochain arrêt » (événement dont `importance >= seuil d'interruption`) et comprime le temps entre les deux.
- **IDs** : slugs kebab-case stables (`aegon-ii`, `port-real`, `maison-rosby`).
- **Dates** : `{annee, lune, jour}` en AC (calendrier de Westeros, 12 lunes/an, ~30 j/lune).

## Tables

### `etat/monde.json` (singleton)
```json
{
  "date": {"annee": 129, "lune": 3, "jour": 3},
  "phase": "paix_fragile | succession_contestee | guerre_ouverte | ...",
  "tension": 0-100,
  "deviations": [{"date": {...}, "description": "...", "cause": "..."}]
}
```
`tension` module le seuil d'interruption : seuil = max(20, 80 - tension) — plus le monde brûle, plus il en faut pour t'interrompre est FAUX, c'est l'inverse : en crise, seuil bas (tout t'interrompt), en paix, seuil haut. Et le seuil décroît avec la durée du fast-forward (plus tu avances longtemps, plus une petite nouvelle suffit).

### `etat/maisons.json` — liste de :
```json
{
  "id": "", "nom": "", "devise": "", "blason": "description héraldique",
  "siege_id": "", "suzerain_id": "",
  "allegeance_affichee": "noir | vert | neutre",
  "allegeance_reelle": "noir | vert | neutre",
  "or": 0, "revenus_lune": 0, "levees_dispo": 0, "levees_max": 0,
  "statut": "intacte | mobilisee | assiegee | tombee",
  "canon": true
}
```

### `etat/personnages.json` — liste de :
```json
{
  "id": "", "nom": "", "maison_id": "", "titre": "",
  "naissance": 100,
  "traits": ["3-4 max"],
  "objectifs": [{"but": "", "priorite": 1}],
  "maniere": "1 ligne : comment il parle",
  "portrait": {"fichier": "portraits/xxx.png|svg", "prompt_ideogram": "...", "physique": "1-2 lignes"},
  "etat": "actif | dormant | mort",
  "lieu_id": "",
  "condition": "libre | otage | prisonnier | blesse | ..."
}
```
`actif` = simulé à chaque battement (~10-15 max à la fois). `dormant` = fiche gelée.

### `etat/relations.json` — directionnelles (A→B ≠ B→A) :
```json
{"source_id": "", "cible_id": "", "opinion": -100, "liens": ["suzerain", "rival", "amant", "creancier"], "connue_du_joueur": false}
```

### `etat/lieux.json` :
```json
{"id": "", "nom": "", "region": "", "type": "chateau | ville | ile | ruine", "controle_id": "maison-x", "jours_de_pr": 0}
```
`jours_de_pr` = distance de Port-Réal, sert au délai des corbeaux/armées/rumeurs.

### `etat/evenements.json` — la file, cœur du moteur :
```json
{
  "id": "", "date_prevue": {...},
  "type": "canon | emergent | programme",
  "importance": 0-100,
  "description": "", "lieu_id": "", "acteurs": [],
  "conditions": ["ce qui peut l'annuler ou le dévier ; sinon il se produit"],
  "statut": "a_venir | resolu | devie | annule",
  "effets": "mutations d'état à appliquer à résolution"
}
```
Le canon de la Danse est pré-chargé en `type: canon`. Il se produit SAUF si les actions du joueur remplissent une condition de déviation → on logge dans `monde.deviations` et on recalcule la suite.

### `etat/infos.json` — ce que le JOUEUR sait :
```json
{"id": "", "evenement_id": "ou null (fausse rumeur)", "version": "le récit tel qu'il parvient, possiblement déformé", "source": "corbeau | mestre | rumeur | temoin", "fiabilite": 0-100, "date_apprise": {...}}
```

### `etat/paroles.json` — ce qui a été DIT (mémoire conversationnelle des PNJ) :
```json
{"id": "", "date": {...}, "lieu_id": "", "locuteur_id": "", "destinataires": [], "contenu": "citation ou résumé fidèle", "secret": false, "scene_id": ""}
```
Un PNJ se souvient de ce qu'on lui a dit, des promesses, des menaces. Toute promesse/menace/aveu significatif en scène DOIT être loggé ici.

### `etat/actes.json` — ce qui a été FAIT :
```json
{"id": "", "date": {...}, "lieu_id": "", "acteur_id": "", "description": "", "temoins": [], "connu_de": ["ids ou 'public'"]}
```

### `etat/intentions.json` — la tête des PNJ actifs (JAMAIS montrée au joueur) :
```json
{
  "personnage_id": "",
  "pensees": "état d'esprit courant, 2-3 lignes",
  "intentions": [{"but": "", "plan": "comment il compte s'y prendre", "horizon": "immediat | lune | saison", "secret": true}],
  "maj": {...}
}
```
Mise à jour à chaque battement pour les actifs, et après toute scène qui les implique. C'est d'ici que sortent les actions hors écran.

### `etat/journal.json` — la partie :
```json
{
  "maison_joueur_id": "",
  "scenes": [{"id": "", "date": {...}, "lieu_id": "", "participants": [], "resume": "", "choix_fait": ""}],
  "scene_courante": {"id": "", "beat": "...", "choix_proposes": []}
}
```

## Runtime (proto)
Le jeu se joue en session Claude Code : Claude est le MJ, lit/écrit `etat/`, et rend chaque scène via un widget HTML (show_widget). Les boutons du widget appellent `sendPrompt("...")` pour renvoyer l'action du joueur dans le chat : `Play`, `Advance`, `Advance jusqu'au prochain événement`, et les 3 choix préfaits + champ libre.
