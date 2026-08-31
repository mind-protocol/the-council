# 🧠 `agents/` — le container des sièges : brief, dépêche, parloir, jugement, affectation

Un acteur — humain ou PNJ — est un SIÈGE (docs/organisation.md §3, l'invariant
du siège). Ce container possède la machinerie qui fait vivre un siège hors
scène : lui servir son point de vue (le brief, le dossier), l'envoyer vivre sa
journée sur demande (la dépêche, la Règle Zéro), lui écrire (le parloir : verbes en call, billet-réveil),
juger sa tentative (le jugement), et ancrer les choses de la fiction dans des
mètres (l'affectation).

**LA PORTE est `expose.py`** (docs/organisation.md §2) : on n'entre ici que
par `from agents.expose import ...`. Les commandes racine (`depecher.py`,
`parloir.py`, `juger.py`, `dossier.py`,
`affecter.py`) sont des FAÇADES aux chemins gelés — le hook Stop de
`.claude/settings.json` tape `scripts/juger.py` tel quel — et elles passent
elles aussi par la porte.

## Les modules du lot 2 — la matière des commandes

| Module | Descendu de | Ce qu'il sait |
|---|---|---|
| `depeche/` | `depecher.py` | envoyer un homme vivre sa journée — brief, manuel, trous, mission, retour, cli |
| `parloir.py` | `parloir.py` | l'adressage de la parole — les verbes en CALL vers l'unique `mj`, `--dire` = billet au canal + réveil cast, la criée `tous` seule au fil jsonl |
| `jugement.py` | `juger.py` | le juge séparé (claude -p) du hook Stop — dix questions, deux relances au plus |
| `matiere.py` | `dossier.py` | le dossier d'un sujet, rassemblé dans l'ordre d'autorité |
| `portage.py` | D.34 (31.8) | les registres portés au réveil-POST du MJ — `matiere_du_message` (nombres + noms propres de l'inbox → `matiere.dossier_registres`, 6 lignes au plus jointes au mot), appelé par `mj.main`, jamais bloquant |
| `affectation/` | `affecter.py` | une adresse physique pour une chose de la fiction — lecture, controle, cli |
| `sieges.py` | `scene/sieges.py` (décision du 30 : les sièges sont la machinerie des acteurs, pas la peau) | s'asseoir, quitter : occupé → pas de tête ; vacant → une tête obligatoirement ; l'archive des têtes — façade `scripts/sieges.py` (chemin ULTRA-GELÉ) |
| `mj.py` | le réveil de l'unique MJ | `appeler_mj(de, mot, verbe)` : session continue sans date, verdict sur stdout, traitement des POST joueur et des verbes des habitants |
| `billet.py` | le modèle habitant (docs/habitant.md §4, pas 5) | écrire = réveiller — `deposer` (l'entrée au canal canonique de la paire), `ecrire` (dépôt puis réveil du destinataire en CAST via `mission.appeler(attendre=False)`, SANS garde de creux : un billet ne propose pas, il réveille). Lié après `depeche` dans la porte |
| `salle.py` | le modèle habitant (docs/habitant.md §2) | ce qu'un habitant entend là où il se tient — `entendre` (accumule, n'écrit rien), `deposer` (une écriture par chambre en fin de poussée : le fil de salle + les relations ouvertes par co-présence). Appelé par `scene/flux.py`, jamais bloquant. Le filtre est `chambre.existe` |
| `chambre.py` | le modèle habitant (docs/habitant.md §2, pas 1) | le domicile d'un habitant — `chemin`, `ouvrir` (arborescence + claude.md seedé UNE fois, jamais retouché), `canal` (le discussion.json canonique d'une paire, ordre lexical), `non_lus`/`marquer_lus` (le curseur `.lu` par canal), `problemes`/`en_souffrance` (les deux cahiers semés vides par `ouvrir`, lecture tolérante). Hommes et MJ : mêmes fonctions. RIEN dans `chambres/` ne fait foi — la vérité vit dans `etat/` |

## Les prompts (`prompts/`)

- `metier.md` — le manuel d'une personne dans le monde (servi par `depeche/manuel.py`).
- `mj-spectacle.md` — la couche de scène du seul MJ, servie avec le manuel
  racine. Les verbes `--tenter`, `--faire`, `--demander` l'appellent en CALL.
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

