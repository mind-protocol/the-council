# Les scripts — ce qui est à la racine, et ce qui ne l'est pas

**La racine de `scripts/` est l'interface publique du jeu.** Ce qui s'y trouve est
tapé — par le MJ à son tour de jeu, par un homme dépêché dans sa journée, par un
hook, par le serveur. Ces chemins sont écrits en dur dans `CLAUDE.md`, dans
`docs/`, dans `ecrans/`, dans `serveur/`, et jusque dans les cahiers in-fiction de
`etat/maisons/<id>/documents/books/` que les prompts des dépêchés listent. **Ils ne se déplacent pas.** Un homme qui
suit son cahier et tombe sur un chemin mort perd sa journée sans que personne le
sache.

**Et chaque commande est une façade — la matière vit dans les containers.**
C'est le lot 2 (docs/organisation.md §5, §7) : une commande racine lit ses
arguments, appelle LA PORTE de son container (`<container>/expose.py`), et
imprime — trente à soixante lignes, plus personne n'a de raison de l'importer
pour sa logique (ses réexports de compatibilité gardent les importeurs
historiques vivants). La matière — modules et paquets nés sous 500 lignes —
vit dans `temps/`, `plan/`, `agents/`, etc., et chaque fiche
`<container>/CLAUDE.md` la déclare.

Les dossiers, eux, tiennent ce qui ne se tape pas au tour de jeu : les modules
qu'on importe, les migrations qui ont déjà tourné, l'outillage qu'on sort une fois
par lune. On peut y ranger, y renommer, y supprimer.

## Le partage

| Dossier | Ce qu'on y met | Qui l'appelle |
|---|---|---|
| *(racine)* | les commandes du tour de jeu | le MJ, les dépêchés, les hooks, le serveur |
| `noyau/` | les modules partagés, importés jamais tapés | les autres scripts |
| `monde/` | engendrer le monde 3D | la pipeline, les cahiers |
| `materialisation/` | Peyredragon vers Blender, les vues, les rendus | à la main |
| `ville/` | Port-Réal : le tissu et sa région | la pipeline |
| `plan/` | le Grand Plan : lecture, correction, colonnes | à la main, rarement |
| `peinture/` | ce qui appelle une API payante : images, voix, chansons | à la main, jamais en boucle |
| `figures/` | les SVG du mestre | à la main |
| `analyse/` | mesurer à froid, les bancs d'essai | à la main |
| `migrations/` | ce qui a déjà tourné, gardé pour la trace | plus personne |
| `tests/` | les tests unitaires et les harnais | `python -m unittest discover -s scripts/tests` |

## Le chemin des frères

Les modules s'importent par NOM NU — `import bibliotheque`, `import couverture` —
et non par chemin de paquet. Un fichier rangé dans un dossier ne les trouve donc
plus tout seul. Toute la conséquence tient dans une amorce, en tête de fichier,
avant le premier import de frère :

```python
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
```

Elle remonte jusqu'au dossier `scripts`, quel que soit l'étage — donc elle survit à
un nouveau classement. **Elle ne rend visibles que la racine et `noyau/`** : un
module de `plan/` ou d'`analyse/` ne s'importe pas depuis ailleurs. Ce qui doit
être partagé descend dans `noyau/`, ce n'est pas négociable.

## La racine du dépôt, et le piège du déplacement

Un fichier de la racine écrit `RACINE = dirname(dirname(abspath(__file__)))`. **Un
fichier d'un dossier a besoin d'un `dirname` de plus.** C'est la faute qui ne se
voit pas à la relecture et qui fait chercher `etat/books.json` dans `scripts/`.
Vaut aussi pour `Path(__file__).resolve().parent.parent`, pour `SCRIPTS = ...`, et
pour `path.dirname(__dirname)` en JavaScript.

Après tout déplacement, vérifier que chaque racine calculée tombe bien où il faut —
c'est de l'arithmétique de chemins, ça se contrôle sans rien exécuter.

## Ne JAMAIS vérifier en important

Beaucoup de ces scripts agissent au chargement : `seed_flux.py` réinitialise
`etat/flux.jsonl`, `exporter_plan.py` réécrit `exports/`. Un « test d'import » qui les balaie détruit une partie en cours. Pour
contrôler qu'un classement n'a rien cassé :

- **`node scripts/verifier.mjs`** — les sept étalons du dépôt, un
  code de sortie, et rien qui touche `etat/` : chaque épreuve tourne dans son
  propre processus, en dossier temporaire, sur un port éphémère. C'est le
  premier geste après tout déplacement, et il remplace la liste ci-dessous ;
- `python -m compileall -q scripts/` — la syntaxe ;
- l'évaluation statique des expressions de racine — les chemins ;
- `python -m unittest discover -s scripts/tests -p "test_*.py"` — le comportement
  (déjà compris dans `verifier.mjs`) ;
- les commandes en lecture seule, une par une : `reprise.py`, `sieges.py`,
  `occupation.py`, `dossier.py --sur <id>`, `presence.py --quartier`,
  `tick.py --verifier`.

## Ce qui est à la racine, et pourquoi

**Le tour de jeu** — `reprise.py` (la feuille de reprise, premier geste),
`dossier.py`, `fils.py`, `criticite.py`, `evaluer.py`, `veille.py`.
⚠ Homonymie levée côté Python (lot 2) : `fils.py` = *les affaires en cours* —
sa matière vit dans `plan/affaires.py`, la façade `scripts/fils.py` reste au
chemin gelé. `ecrans/modules/fils.js` = *le fil du récit* (scène) garde son
nom pour l'instant (docs/organisation.md §8 ⑧).

**La Règle Zéro** — `depecher.py` (envoyer un homme vivre sa journée),
`parloir.py` (lui écrire : verbes en call, billet-réveil — le hook-oreille
est mort le 31.8), `presence.py` (qui est à portée, et ses creux).
`depecher.py --contexte <N°>` (par exemple `23030`, `#23030` ou `n° 23030`)
normalise l'adresse globale d'une pièce d'affaire, ouvre une session et un fil
de chambre distincts, et borne le brief à sa chaîne ascendante.

**Le monde qui tourne** — `tick.py` (le calcul, n'écrit jamais dans `etat/`),
`ajouter.py` (une entrée à la fois),
`occupation.py`, `sieges.py`, `regence.py`.

**Le fil et l'écran** — `append_flux.py` (la seule plume du flux et de l'horloge),
`tunnel.py` et `carte_muette.py` sont ses compteurs, `seed_flux.py`, `regie.py`
(le siège de Corneille), `guetteur.sh` (à réarmer EN PREMIER).

**Les registres** — `couverture.py`, `etat_du_plan.py`, `mesures.py`,
`verser_cahier.py`, `exporter_plan.py`, `purger.py`, `tisser.py`.

**La géométrie** — `corps.py`, `affecter.py`, `marche.py`, `arpenter.py`,
`carte_geo.py`, `passer.py`.

**La vérification** — `verifier.mjs` : une commande, tous les étalons, un code de
sortie (`node scripts/verifier.mjs`, ou `--long` pour ce qui coûte des minutes).
Son manifeste est la seule déclaration de ce qui vérifie ce dépôt : une épreuve
neuve entre par ce fichier, sinon les listes divergent comme elles l'ont déjà
fait pour l'ordre de chargement. Les bancs eux-mêmes vivent dans `analyse/` et
`tests/`.

**La sauvegarde Git des données** — `pousser_donnees.py` : aperçu sans effet par
défaut ; `--vraiment` valide les JSON/JSONL modifiés, refuse un index déjà
préparé, vérifie que `etat/` et `chambres/` n'ont pas bougé pendant la capture,
commit uniquement ces deux racines puis pousse la branche courante. Les verrous,
temporaires, caches d'empreintes et `.agents-runtime/` ne partent jamais.

**Le reste** — `composer.py`.
