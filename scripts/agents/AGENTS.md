# 🧠 `agents/` — le container des sièges : brief, dépêche, parloir, affectation

Un acteur — humain ou PNJ — est un SIÈGE (docs/organisation.md §3, l'invariant
du siège). Ce container possède la machinerie qui fait vivre un siège hors
scène : lui servir son point de vue (le brief, le dossier), l'envoyer vivre sa
journée sur demande (la dépêche, la Règle Zéro), lui écrire (le parloir : billet-réveil entre habitants ; appels au MJ réservés au front joueur),
et ancrer les choses de la fiction dans des
mètres (l'affectation).

**LA PORTE est `expose.py`** (docs/organisation.md §2) : on n'entre ici que
par `from agents.expose import ...`. Les commandes racine (`depecher.py`,
`parloir.py`, `dossier.py`, `affecter.py`) sont des FAÇADES aux chemins gelés et elles passent
elles aussi par la porte.

## Les modules du lot 2 — la matière des commandes

| Module | Descendu de | Ce qu'il sait |
|---|---|---|
| `depeche/` | `depecher.py` | appeler un homme — le prompt système liste les documents de sa maison ; `--contexte <N°>` isole la session et focalise le brief ; `--mode reponse|discussion` limite le call à vérifier, concevoir et envoyer, tandis que `journee` conserve l'autonomie historique |
| `parloir.py` | `parloir.py` | l'adressage de la parole — `--dire` entre habitants ; `--contexte` + `--ref` sont conservés dans canal, web et spool MJ ; vers un siège joueur occupé : pas de cast, billet + `reponse` web privée + copie append-only au flux MJ ; appels d'autorité vers `mj` toujours refusés aux PNJ et réservés au front marqué `--joueur`, criée `tous` |
| `matiere.py` | `dossier.py` | le dossier d'un sujet, rassemblé dans l'ordre d'autorité |
| `portage.py` | D.34 (31.8) | les registres portés au réveil-POST du MJ — `matiere_du_message` (nombres + noms propres de l'inbox → `matiere.dossier_registres`, 6 lignes au plus jointes au mot), appelé par `mj.main`, jamais bloquant |
| `selecteur_contexte.py` | première couche des messages joueur | session neuve sans reprise, sérialisée par siège : héritage des messages faibles sauf lorsqu'une personne est nommée dans le message courant ; les noms du fil n'imposent pas le destinataire ; classement déterministe et arbres complets ; sélection non vide et ancrée, création obligatoire pour un incident multi-sièges, joueurs séparés des PNJ, association homme → pointeur dans `routes_hommes` ; artefact `selection-contexte/4` hors fiction dans `.agents-runtime/contextes/` |
| `routeur_message.py` | deuxième couche des messages joueur | toute action au MJ sur sa `ref` exacte ; pour `dire|parler`, mots exacts servis d'abord aux hommes sélectionnés par le numéro brut de leur item (`contexte_id`) avec la `ref` d'origine ; les deux persistent dans prompt, archive, environnement, trace, canal, web et spool MJ, puis bilan joint au MJ pour empêcher une double dépêche |
| `affectation/` | `affecter.py` | une adresse physique pour une chose de la fiction — lecture, controle, cli |
| `sieges.py` | `scene/sieges.py` (décision du 30 : les sièges sont la machinerie des acteurs, pas la peau) | s'asseoir, quitter : occupé → pas de tête ; vacant → une tête obligatoirement ; l'archive des têtes — façade `scripts/sieges.py` (chemin ULTRA-GELÉ) |
| `mj.py` | le réveil de l'unique MJ | `appeler_mj(de, mot, verbe)` : session continue sans date, traitement des POST et verbes du front joueur ; consomme le flux append-only `retours-parloir.jsonl` sans reprendre ce qui arrive pendant l'appel |
| `billet.py` | le modèle habitant (docs/habitant.md §4, pas 5) | écrire = réveiller — `deposer` (l'entrée au canal canonique de la paire), `ecrire` (dépôt puis réveil du destinataire en CAST via `mission.appeler(attendre=False)`, SANS garde de creux : un billet ne propose pas, il réveille). Lié après `depeche` dans la porte |
| `salle.py` | le modèle habitant (docs/habitant.md §2) | ce qu'un habitant entend là où il se tient — `entendre` (accumule, n'écrit rien), `deposer` (une écriture par chambre en fin de poussée : le fil de salle + les relations ouvertes par co-présence). Appelé par `scene/flux.py`, jamais bloquant. Le filtre est `chambre.existe` |
| `chambre.py` | le modèle habitant (docs/habitant.md §2, pas 1) | le domicile d'un habitant — `chemin`, `ouvrir`, `fil` (fil historique ou fil isolé par item d'affaire), `canal` (le discussion.json canonique d'une paire), `non_lus`/`marquer_lus`, `problemes`/`en_souffrance`. Hommes et MJ : mêmes fonctions. RIEN dans `chambres/` ne fait foi — la vérité vit dans `etat/` |

## Les prompts (`prompts/`)

- `metier.md` — le manuel d'une personne dans le monde (servi par `depeche/manuel.py`).
- `mj-spectacle.md` — la couche de scène du seul MJ, servie avec le manuel
  racine. Seul le front joueur peut l'appeler en CALL.
- `copier_claude_vers_agents.py` — la matière du miroir d'instructions pour
  Codex : chaque `CLAUDE.md` devient le `AGENTS.md` frère, octet pour octet.
  Le runner public est `python scripts/copier_claude_vers_agents.py` ;
  `--verifier` n'écrit rien et refuse toute divergence.

Les paquets (`depeche/`, `affectation/`) existent parce qu'un
module naît sous 500 lignes (le cliquet de `.claude/hooks/taille.js`) : la
coupe y est plus fine que le `brief/manuel/retour` — le plafond l'exige, les commentaires ont voyagé avec
leur code. Le découpage tiré par les features (le siège générique, deux
profils d'une même porte) reste au lot 2 features (organisation.md §5).

## L'ordre des imports de la porte — une contrainte

`depeche` relit `agents.expose` PENDANT son chargement : `affectation` doit
être liée avant lui, et la porte garde les anciens noms `affecter` et
`depecher` vivants pour les façades.

Entre modules du MÊME container, l'import est direct
(`from agents.depeche.brief import brief_de`) ; seuls les façades et les
autres containers passent par la porte. `livre` et `bibliotheque` (noyau,
réclamés par plan) n'ont qu'un point de contact dans `depeche/` : `brief.py`.

