# Relecture de la refonte des manuels — 30.8.2026

> **Archive de conception, supersedee le 31.8.2026.** Cette fiche documente
> l'essai des MJ de zone. Le runtime courant n'en conserve aucun : un seul
> `mj`, servi par `scripts/agents/mj.py`, arbitre tous les sièges. Les mentions
> `mj-*`, `zone.py` et `mj-zone.md` ci-dessous sont historiques.

Rien n'est commité : tout est dans l'arbre de travail, à relire. La règle
suivie : **déplacement à l'identique** — tout texte existant qui change de
fichier a été copié mot pour mot (script d'extraction, pas de retape) ; seules
les sections encadrées `<!-- NEUF : a relire -->` sont de la rédaction
nouvelle. Les numéros de lignes « origine » sont ceux des fichiers AVANT la
refonte (l'état que tu avais ce soir).

## La carte appliquée

4 rôles, 4 fichiers : l'homme → `metier.md` ; l'arbitre de zone →
`mj-zone.md` ; l'arbitre du joueur → `mj-zone.md` + `mj-spectacle.md`
(nouveau, servi EN PLUS par `zone.py` quand la zone est `mj`) ; le juge →
inline dans `jugement.py` (non touché). `CLAUDE.md` racine = manuel du dépôt
(494 lignes) ; `AGENTS.md` résorbé en pointeur (9 lignes).

## Tableau des déplacements

| origine | lignes d'origine | cible | quoi |
| --- | --- | --- | --- |
| CLAUDE.md | 50-54 | mj-spectacle.md §Boucle de jeu | démarrage de session (reprise.py, pied du joueur, read_me) |
| CLAUDE.md | 230-236 | mj-spectacle.md §Le tunnel, et le fil unique | LE TUNNEL (seuils 700/2200/4/3/1, `--tunnel`), « on ferme avant d'ouvrir », « un seul fil à la fois » |
| CLAUDE.md | 249-252 | mj-spectacle.md §Playback | contrainte d'invocation (til next event en deux temps) |
| CLAUDE.md | 258-266 | mj-spectacle.md §La montre | l'heure tenue par append_flux, durées, zéro minute |
| CLAUDE.md | 277-373 | mj-spectacle.md §Penser/Coulisses/Laisser faire/Intervention/Chansons | les modes hors fiction et l'atelier des chansons |
| CLAUDE.md | 375-394 | mj-spectacle.md §Orienter le joueur, §Répondre à une question | les trois questions du battement ; réponse en contexte |
| CLAUDE.md | 530 (¶ « Pousser en TRANCHES ») | mj-spectacle.md §Pousser en tranches | tranches 2-4 items, Couper = signal de rythme |
| CLAUDE.md | 584, 586-590 | mj-spectacle.md §La main sur la table, côté régie | clé `montre`, « une carte une phrase », « nomme tes pièces », « un acteur pose la pièce », l'échiquier, « une chose par intervention » |
| CLAUDE.md | 606-613 | mj-spectacle.md §Rendu widgets (secours) | le fallback show_widget |
| CLAUDE.md | 615-625 | mj-spectacle.md §Ton | ton, gras d'appui, liens-adresses, jamais les mécaniques |
| metier.md | 156-208 | mj-spectacle.md §Montrer — cinq gestes | la table des cinq gestes + l'extrait + l'écrit (« un homme ne montre rien au joueur ») |
| AGENTS.md | 108-281 | mj-spectacle.md (fin de fichier) | **SEULE copie restante** de la doctrine du conseiller : Ils sont COMPÉTENTS (version longue), LA MESURE QUOTIDIENNE, la question que chacun se pose, le péage, ce qui passe toujours, mutisme fabriqué et promulgation, les deux jets, comment parle un personnage, le curseur `explication` |

Chaque déplacement est aussi marqué dans mj-spectacle.md par un commentaire
`<!-- déplacé depuis … -->` au-dessus de la section. Dans CLAUDE.md, chaque
section partie est remplacée par une ligne de renvoi
`→ [scripts/agents/prompts/mj-spectacle.md](…)`.

## Les [NEUF] à relire

1. **mj-spectacle.md, tête de fichier** (l.3-20) : « tu es l'arbitre de la
   zone du joueur, même rôle plus trois charges » — spectacle (commande
   `python scripts/append_flux.py '<json item>' …`, vérifiée sur le dépôt :
   c'est bien l'usage du script, avec `--fichier` et `--pour`), montre,
   arbitrage final. « SANS flux, ta réponse n'existe pas. »
2. **mj-spectacle.md, quatre titres de section** marqués NEUF (le contenu
   sous chacun est déplacé tel quel) : « Pousser en tranches », « Le tunnel,
   et le fil unique », « La main sur la table, côté régie ».
3. **mj-zone.md, en tête** : l'anti-dérive de voix — « le mot qui te réveille
   est LA VOIX D'UN AUTRE » (mesuré ce soir : le MJ a continué la pensée de
   Gerardys à la première personne).
4. **mj-zone.md, « Le droit d'inventer »** : le monde local que la
   vraisemblance exige, les issues des TENTER — et les trois bornes (non
   gravé = pas eu lieu ; jamais dans une tête ni hors zone ; jamais contre
   l'état).
5. **zone.py `_message`** : la ligne de cadre du réveil — « Tu es l'arbitre :
   ce mot est la voix d'un autre — réponds en arbitre, jamais dans sa
   pensée. » (sans accents, comme le reste du module).

## Les doutes — à arbitrer

- **La doctrine du conseiller (ex-AGENTS.md l.108-281) est allée dans
  mj-spectacle.md, pas dans metier.md.** CLAUDE.md l.155 affirmait qu'elle
  « vit désormais dans metier.md » — elle n'y a jamais été (vérifié :
  aucune occurrence de « péage »/« deux jets » dans prompts/ ni docs/). Son
  adressage vise celui qui ÉCRIT une réplique de conseiller et la pousse au
  flux — donc l'arbitre du joueur — et metier.md venait d'être élagué
  aujourd'hui même (77 lignes retirées, non commitées) : je n'ai pas voulu
  regonfler ta coupe. Si tu la veux côté homme, elle se déplace en bloc (elle
  est en fin de mj-spectacle.md, d'un seul tenant, commentaire en tête).
- **metier.md garde « LA MAIN SUR LA TABLE », « L'ÉCHIQUIER », « La borne,
  et elle vaut pour les cinq gestes » et « En scène, un trou se cite par son
  numéro »** — la consigne disait « retirer Montrer, rien d'autre ». Mais
  « La borne » cite « les cinq gestes » désormais partis au spectacle, et ces
  sections font encore montrer l'homme (carte, échiquier). À trancher : les
  suivre au spectacle, ou assumer que l'homme pose des pièces que l'arbitre
  relaie.
- **Gardé dans CLAUDE.md malgré leur odeur de rôle en session** (au bénéfice
  du doute — elles documentent la machine et le monde autant que le rôle) :
  Règle Zéro + parloir (l.5-45), Incarnation, Transmettre un ordre, Exécuter,
  La salle vit sans le joueur + l'élection, les boucles (Advance, hors scène,
  mains, pensées), Vérité vs connaissance, Discipline d'état, annales,
  acteurs hors scène, résolution des incertaines, casting, sièges, deux MJ, Corneille,
  le Rendu navigateur (types d'items, `demande`, `ecrit`, échelles, table,
  livres, affecter), Création de partie, Interdits.
- **Renvois devenus inter-fichiers** : dans mj-spectacle.md, la boucle de jeu
  dit « Création de partie (voir plus bas) » — c'est resté dans CLAUDE.md ;
  dans CLAUDE.md, le Rendu (point 2) dit « voir la section Coulisses plus
  haut » — c'est parti au spectacle ; les Interdits disent « tous suspendus
  en mode Intervention — voir cette section » — idem. Laissés tels quels
  (déplacement à l'identique) : à toi de réécrire ces incises si tu veux.
- **Les chansons** sont parties au spectacle (mode joueur + atelier
  composer.py) — discutable, c'est aussi de l'outillage du dépôt.
- **Doublon assumé dans mj-spectacle.md** : « Montrer — cinq gestes »
  (ex-metier, adressé « tu = l'homme ») recoupe « La main sur la table, côté
  régie » (ex-CLAUDE §9, adressé au MJ) et la doctrine ex-AGENTS. Les voix se
  chevauchent ; je n'ai pas fusionné (ç'aurait été réécrire).
- **CLAUDE.md l.146 (ex-155)** pointe toujours metier.md pour « le péage, les
  deux jets » — désormais inexact (voir premier doute). Une ligne à corriger
  de ta main selon ton arbitrage.

## Les écarts CLAUDE.md / AGENTS.md constatés (version CLAUDE.md retenue partout)

AGENTS.md était un état antérieur du manuel ; rien de sa version périmée n'a
été repris. Ce qu'il disait d'autre, et qui est mort côté CLAUDE.md :

- Boucle de jeu : « lis `etat/*.json` en entier » (vs reprise.py + interdiction
  de tout lire).
- « Trois règles dures » de la salle (CLAUDE.md en a quatre — la plainte nue).
- Boucle des pensées : « deux travaux par jour », l'« excitation » et son
  seuil, le marquage `servie` (vs creux/quartier, excitation tuée par la
  mesure).
- Casting : champ `echelle` et budgets scene~5/orbite~20 (vs quartier mesuré,
  champ supprimé).
- Délégation : « règle du seul écrivain » (abolie le 9 août côté CLAUDE.md).
- Table : « sers-t'en quand un conseiller chiffre » (vs « un acteur pose la
  pièce dès que ce qu'il dit a un endroit »).
- Absents d'AGENTS.md : Règle Zéro/parloir, le tunnel, Corneille, l'agenda,
  la montre… (rien à en tirer).

## Le code (vérifié, non commité)

- **zone.py** : `_manuel` concatène mj-zone.md + mj-spectacle.md quand la
  zone est `mj` (le cahier de chambre garde le dernier mot) ; `_message`
  porte la ligne de cadre ; **normalisation des ids de zone SANS TIRETS** au
  seul endroit qui les fabrique (`zone_de` : `port-real` → `mj-portreal`,
  accepte l'id déjà préfixé), consommée par `arbitre_de` et `appeler_zone`.
- **serveur/routes/joueur.js** : `moi.arbitre` suit la même normalisation
  (`"mj-" + lieu_id.replace(/-/g, "")`).
- Preuves : `python -m compileall scripts/agents/` OK ; `node --check
  serveur/routes/joueur.js` OK ; `zone_de` testée (`port-real`,
  `mj-port-real`, `peyredragon`, `mj` → attendus). L'import direct
  `from agents.zone import …` hors de la porte `agents/expose` déclenche un
  cycle d'import PRÉEXISTANT (via `agents.expose` ← `depeche/brief`) — sans
  lien avec ces modifs.

## Le banc n° spectacle — à lancer UNE FOIS RELU

Un POST /action réel ; la réponse du MJ doit apparaître AU FLUX (pas
seulement sur le stdout du réveil — c'est toute la charge « spectacle ») :

```bash
# serveur lancé (port 3129), jeton du siège Rhaenyra dans etat/joueurs.json
curl -s -X POST http://localhost:3129/action \
  -H "Cookie: jeton=<jeton du siège rhaenyra>" \
  -H "Content-Type: application/json" \
  -d '{"type":"libre","mode":"question","texte":"Ou en est la garde de la porte de mer ?"}'
# puis, apres le reveil (quelques dizaines de secondes) :
tail -3 etat/flux.jsonl   # attendu : l item question, PUIS un item reponse pousse par le MJ
```

Si la `reponse` n'arrive jamais au flux alors que le réveil a tourné, c'est
que le MJ a répondu sur stdout seul — exactement la dérive que la section
[NEUF] en tête de mj-spectacle.md interdit.
