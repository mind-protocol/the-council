# 🧠 `agents/` — le container des sièges : brief, dépêche, activation, parloir, jugement, affectation

Un acteur — humain ou PNJ — est un SIÈGE (docs/organisation.md §3, l'invariant
du siège). Ce container possède la machinerie qui fait vivre un siège hors
scène : lui servir son point de vue (le brief, le dossier), l'envoyer vivre sa
journée (la dépêche, la Règle Zéro), le laisser tourner au fil du graphe (la
boucle d'activation), lui parler pendant qu'il travaille (le parloir), juger
sa tentative (le jugement), et ancrer les choses de la fiction dans des mètres
(l'affectation).

**LA PORTE est `expose.py`** (docs/organisation.md §2) : on n'entre ici que
par `from agents.expose import ...`. Les commandes racine (`depecher.py`,
`boucle_activation.py`, `parloir.py`, `juger.py`, `dossier.py`,
`affecter.py`) sont des FAÇADES aux chemins gelés — les hooks de
`.claude/settings.json` tapent `scripts/parloir.py` et `scripts/juger.py`
tels quels — et elles passent elles aussi par la porte.

## Les modules du lot 2 — la matière des commandes

| Module | Descendu de | Ce qu'il sait |
|---|---|---|
| `depeche/` | `depecher.py` | envoyer un homme vivre sa journée — brief, manuel, narrateur, trous, mission, retour, cli |
| `activation/` | `boucle_activation.py` | la boucle pilotée par le graphe miroir — socle, horloges, graphe, taches, missions, dossier, mutations, rapport, continuite, appels, cycle, cli |
| `parloir.py` | `parloir.py` | se parler pendant qu'on travaille — un fil par paire, curseur par lecteur |
| `jugement.py` | `juger.py` | le juge séparé (claude -p) du hook Stop — dix questions, deux relances au plus |
| `matiere.py` | `dossier.py` | le dossier d'un sujet, rassemblé dans l'ordre d'autorité |
| `affectation/` | `affecter.py` | une adresse physique pour une chose de la fiction — lecture, controle, cli |
| `sieges.py` | `scene/sieges.py` (décision du 30 : les sièges sont la machinerie des acteurs, pas la peau) | s'asseoir, quitter : occupé → pas de tête ; vacant → une tête obligatoirement ; l'archive des têtes — façade `scripts/sieges.py` (chemin ULTRA-GELÉ) |
| `zone.py` | le modèle habitant (docs/habitant.md §3-§4, pas 4) | le réveil en CALL du MJ de zone — `appeler_zone(ville, de, mot, verbe)` (session continue, id uuid5 SANS date, `--session-id` puis `--resume`, verdict sur stdout), `arbitre_de` (l'arbitre d'un homme d'après sa ville ; la zone du joueur = `mj`), `est_une_zone`. Lié APRÈS `depeche` dans la porte (il relit `brief`) |
| `billet.py` | le modèle habitant (docs/habitant.md §4, pas 5) | écrire = réveiller — `deposer` (l'entrée au canal canonique de la paire), `ecrire` (dépôt puis réveil du destinataire en CAST via `mission.appeler(attendre=False)`, SANS garde de creux : un billet ne propose pas, il réveille). Lié après `depeche` dans la porte |
| `salle.py` | le modèle habitant (docs/habitant.md §2) | ce qu'un habitant entend là où il se tient — `entendre` (accumule, n'écrit rien), `deposer` (une écriture par chambre en fin de poussée : le fil de salle + les relations ouvertes par co-présence). Appelé par `scene/flux.py`, jamais bloquant. Le filtre est `chambre.existe` |
| `chambre.py` | le modèle habitant (docs/habitant.md §2, pas 1) | le domicile d'un habitant — `chemin`, `ouvrir` (arborescence + claude.md seedé UNE fois, jamais retouché), `canal` (le discussion.json canonique d'une paire, ordre lexical), `non_lus`/`marquer_lus` (le curseur `.lu` par canal), `problemes`/`en_souffrance` (les deux cahiers semés vides par `ouvrir`, lecture tolérante). Hommes et MJ : mêmes fonctions. RIEN dans `chambres/` ne fait foi — la vérité vit dans `etat/` |

## Les prompts (`prompts/`)

- `metier.md` — le manuel d'une personne dans le monde (servi par `depeche/manuel.py`).
- `mj-zone.md` — le manuel de l'arbitre d'une ville (habitant.md, pas 1) : électeur-greffier,
  jamais auteur (Règle Zéro), les trois verbes TENTER/FAIRE/DEMANDER, session continue.
  Branché au pas 4 : `zone.appeler_zone` le sert en session continue, les verbes
  du parloir (`--tenter`, `--faire`, `--demander`) l'appellent en CALL.

Les paquets (`depeche/`, `activation/`, `affectation/`) existent parce qu'un
module naît sous 500 lignes (le cliquet de `.claude/hooks/taille.js`) : la
coupe y est plus fine que le `brief/manuel/retour` et l'`activation.py`
d'organisation.md §7 — le plafond l'exige, les commentaires ont voyagé avec
leur code. Le découpage tiré par les features (le siège générique, deux
profils d'une même porte) reste au lot 2 features (organisation.md §5).

## L'ordre des imports de la porte — une contrainte

`depeche` et `activation` relisent `agents.expose` PENDANT son chargement :
`affectation` (et `depeche` pour la boucle) doivent être liés avant eux, et
la porte garde les anciens noms `affecter`, `depecher`, `boucle_activation`
vivants — les façades et les bancs (`analyse/`) les demandent sous ces noms.

Entre modules du MÊME container, l'import est direct
(`from agents.depeche.brief import brief_de`) ; seuls les façades et les
autres containers passent par la porte. `livre` et `bibliotheque` (noyau,
réclamés par plan) n'ont qu'un point de contact dans `depeche/` : `brief.py`.

NOTE aux bancs : les drapeaux de log de la boucle vivent dans
`activation/socle.py` (`activation.socle.AFFICHER_LOGS = False`).
