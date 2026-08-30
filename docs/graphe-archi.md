# Le graphe d'architecture — **généré**, jamais écrit à la main

> Produit par `python scripts/analyse/graphe_archi.py --doc` en lisant les
> imports Python, les `require` Node et les globales du navigateur, projetés
> sur la déclaration de [`containers.json`](containers.json). **Ne pas éditer :**
> toute correction se fait dans la déclaration ou dans le code, et l'on régénère.

Les intentions et les lois sont dans [`organisation.md`](organisation.md) ;
les boucles du jeu dans [`architecture.md`](architecture.md).

## Les containers et leurs liens

```mermaid
flowchart TB
  subgraph R0["rang 0"]
    direction LR
    socle["🔩 socle<br/><i>9 fichiers</i>"]
    etat["🗄️ etat<br/><i>5 fichiers</i>"]
  end
  subgraph R1["rang 1"]
    direction LR
    temps["⏱️ temps<br/><i>8 fichiers</i>"]
    monde["🌍 monde<br/><i>107 fichiers</i>"]
  end
  subgraph R2["rang 2"]
    direction LR
    agents["🧠 agents<br/><i>8 fichiers</i>"]
    plan["📋 plan<br/><i>51 fichiers</i>"]
  end
  subgraph R3["rang 3"]
    direction LR
    bataille["⚔️ bataille<br/><i>48 fichiers</i>"]
    peinture["🎨 peinture<br/><i>14 fichiers</i>"]
  end
  subgraph R4["rang 4"]
    direction LR
    scene["📜 scene<br/><i>39 fichiers</i>"]
  end
  subgraph R9["rang 9"]
    direction LR
    bancs["🔬 bancs<br/><i>26 fichiers</i>"]
  end
  scene -->|45| socle
  monde -->|41| socle
  plan -->|29| socle
  scene -->|25| monde
  bancs -.->|9| plan
  agents -->|8| plan
  scene -->|8| plan
  bataille -->|8| monde
  plan -->|7| monde
  monde -->|5| plan
  agents -->|5| socle
  socle -->|5| monde
  monde -->|5| scene
  bancs -.->|4| agents
  scene -->|4| temps
  plan -->|4| agents
  plan -->|4| scene
  peinture -->|4| socle
  scene -->|4| peinture
  socle -->|4| scene
  agents -->|3| temps
  bancs -.->|3| temps
  bataille -->|3| socle
  temps -->|3| socle
  scene -->|3| bataille
  bancs -.->|2| etat
  agents -->|2| etat
  plan -->|2| temps
  temps -->|2| plan
  monde -->|2| bataille
  socle -->|2| plan
  agents -->|1| monde
  bancs -.->|1| monde
  etat -->|1| temps
  etat -->|1| plan
  peinture -->|1| plan
  monde -->|1| agents
  plan -->|1| etat
  temps -->|1| etat
  temps -->|1| agents
  socle -->|1| bataille
  agents -->|1| scene
  plan -->|1| peinture
  monde -->|1| peinture
  bancs -.->|1| scene
  bataille -->|1| scene
```

## Le tableau des liens

| de | vers | références | |
|---|---|---:|---|
| `scene` | `socle` | 45 |  |
| `monde` | `socle` | 41 |  |
| `plan` | `socle` | 29 |  |
| `scene` | `monde` | 25 |  |
| `bancs` | `plan` | 9 |  |
| `agents` | `plan` | 8 | ⚠️ remontée |
| `scene` | `plan` | 8 |  |
| `bataille` | `monde` | 8 |  |
| `plan` | `monde` | 7 |  |
| `monde` | `plan` | 5 | ⚠️ remontée |
| `agents` | `socle` | 5 |  |
| `socle` | `monde` | 5 | ⚠️ remontée |
| `monde` | `scene` | 5 | ⚠️ remontée |
| `bancs` | `agents` | 4 |  |
| `scene` | `temps` | 4 |  |
| `plan` | `agents` | 4 | ⚠️ remontée |
| `plan` | `scene` | 4 | ⚠️ remontée |
| `peinture` | `socle` | 4 |  |
| `scene` | `peinture` | 4 |  |
| `socle` | `scene` | 4 | ⚠️ remontée |
| `agents` | `temps` | 3 |  |
| `bancs` | `temps` | 3 |  |
| `bataille` | `socle` | 3 |  |
| `temps` | `socle` | 3 |  |
| `scene` | `bataille` | 3 |  |
| `bancs` | `etat` | 2 |  |
| `agents` | `etat` | 2 |  |
| `plan` | `temps` | 2 |  |
| `temps` | `plan` | 2 | ⚠️ remontée |
| `monde` | `bataille` | 2 | ⚠️ remontée |
| `socle` | `plan` | 2 | ⚠️ remontée |
| `agents` | `monde` | 1 |  |
| `bancs` | `monde` | 1 |  |
| `etat` | `temps` | 1 | ⚠️ remontée |
| `etat` | `plan` | 1 | ⚠️ remontée |
| `peinture` | `plan` | 1 |  |
| `monde` | `agents` | 1 | ⚠️ remontée |
| `plan` | `etat` | 1 |  |
| `temps` | `etat` | 1 |  |
| `temps` | `agents` | 1 | ⚠️ remontée |
| `socle` | `bataille` | 1 | ⚠️ remontée |
| `agents` | `scene` | 1 | ⚠️ remontée |
| `plan` | `peinture` | 1 | ⚠️ remontée |
| `monde` | `peinture` | 1 | ⚠️ remontée |
| `bancs` | `scene` | 1 |  |
| `bataille` | `scene` | 1 | ⚠️ remontée |

## Les modules, par container

### 🗄️ etat — rang 0

*La seule verite : un fait qui n'y est pas ecrit n'existe pas*

**5 fichiers, 2135 lignes.** Porte : `scripts/etat/expose.py`

- **scripts/** (5) — `appliquer.py`, `tables.py`, `purger.py`, `ajouter.py`, `veille.py`

### 🔩 socle — rang 0

*Ce qui n'a pas de sujet et que tout le monde traverse : le transport, les chemins, le siege, la messagerie des ecrans*

**9 fichiers, 2006 lignes.** Porte : `serveur/http.js`

- **serveur/** (5) — `croiser.js`, `siege.js`, `contexte.js`, `dates.js`, `http.js`
- **ecrans/** (4) — `bus.js`, `nav.js`, `entites.js`, `loupe.js`

### 🌍 monde — rang 1

*La ville : masque, plan, bati, gens, relief — sa cuisson, son service et son ecran*

**107 fichiers, 43165 lignes.** Porte : `scripts/monde/expose.py`

- **scripts/** (62) — `plan_ville.py`, `peyredragon_interieurs.py`, `densifier.py`, `mesure_murs.js`, `sac.js`, `peupler.py`, `carte_geo.py`, `formes.py`, `coudre.py` … et 53 autres
- **serveur/** (9) — `monde3d.js`, `marche.js`, `carte.js`, `presence.js`, `monde-jeu.js`, `terrain.js`, `foule.js`, `chemin.js`, `marche.js`
- **ecrans/** (36) — `carte-ville.js`, `plan.js`, `foule2d.js`, `plans.js`, `carte.js`, `journee.js`, `gens.js`, `terrain.js`, `ville3d.js` … et 27 autres

### ⏱️ temps — rang 1

*Possede le temps hors-scene : horloges, echeances, diffusion — calcule et propose, ne decide jamais*

**8 fichiers, 6800 lignes.** Porte : `scripts/temps/expose.py`

- **scripts/** (7) — `tick.py`, `presence.py`, `regence.py`, `evaluer.py`, `occupation.py`, `reprise.py`, `jours_relatifs.py`
- **serveur/** (1) — `calendrier.js`

### 🧠 agents — rang 2

*La cognition des hommes : brief d'entree, journee vecue, ecrits rendus*

**8 fichiers, 8199 lignes.** Porte : `scripts/agents/expose.py`

- **scripts/** (6) — `boucle_activation.py`, `depecher.py`, `affecter.py`, `parloir.py`, `dossier.py`, `juger.py`
- **serveur/** (2) — `activations.js`, `regie.js`

### 📋 plan — rang 2

*Le Grand Plan : cahiers, couverture, criticite, levees — ce que les hommes ecrivent et ce qu'on en tire*

**51 fichiers, 18357 lignes.** Porte : `scripts/plan/expose.py`

- **scripts/** (23) — `criticite.py`, `etat_du_plan.py`, `couverture.py`, `mesures.py`, `tisser.py`, `normaliser_etats.py`, `scinder_moyens.py`, `plan_leves.py`, `corriger_plan.py` … et 14 autres
- **serveur/** (6) — `echiquier.js`, `atelier.js`, `agenda.js`, `livres.js`, `recherche.js`, `echiquier.js`
- **ecrans/** (22) — `echiquier.js`, `jetons.js`, `volume.js`, `renvois.js`, `coffret.js`, `marques.js`, `etagere.js`, `portee.js`, `renvois.js` … et 13 autres

### ⚔️ bataille — rang 3

*Le moteur de bataille — EN SURSIS : sa porte deviendra l'adaptateur vers le depot `batailles`*

**48 fichiers, 29047 lignes.** Porte : `scripts/bataille/expose.py`

- **scripts/** (1) — `bataille.py`
- **serveur/** (1) — `bataille.js`
- **ecrans/** (46) — `bataille2d.js`, `dragons.js`, `1-corps.js`, `scenarios.js`, `page.js`, `architecture-page.js`, `incendie-ville.js`, `guet-epreuves.js`, `faits.js` … et 37 autres

### 🎨 peinture — rang 3

*Ce qui appelle une API payante : portraits, salles, voix, chansons*

**14 fichiers, 2644 lignes.** Porte : `scripts/peinture/expose.py`

- **scripts/** (10) — `gen_voix.py`, `figures.py`, `nappe.py`, `gen_salles.py`, `generer_chanson.py`, `figure_forces.py`, `medaillons.py`, `composer.py`, `audition_voix.py` … et 1 autres
- **serveur/** (4) — `voix.js`, `medias.js`, `portraits.js`, `voix.js`

### 📜 scene — rang 4

*LA PEAU : le flux, l'inbox, la montre, les sieges — ce que le joueur voit ; personne ne la lit*

**39 fichiers, 8764 lignes.** Porte : `scripts/scene/expose.py`

- **scripts/** (5) — `append_flux.py`, `sieges.py`, `tunnel.py`, `regie.py`, `seed_flux.py`
- **serveur/** (8) — `fils.js`, `action.js`, `bibliotheque.js`, `piece.js`, `vue.js`, `scene.js`, `joueur.js`, `serveur.js`
- **ecrans/** (26) — `son.js`, `nappe.js`, `calendrier.js`, `illustration.js`, `capture.js`, `galerie.js`, `voix.js`, `actions.js`, `regie.js` … et 17 autres

### 🔬 bancs — rang 9

*Ils lisent tout et n'ecrivent rien : gardes, mesures, etalons, audit*

**26 fichiers, 5878 lignes.** Porte : `scripts/verifier.mjs`

- **scripts/** (22) — `croisement.py`, `exporter_aurore.py`, `parvenir.py`, `simuler_reveil_maisons.py`, `verifier.mjs`, `croise.js`, `graphe_archi.py`, `scorer_activation_hightower.py`, `essai_occupation.py` … et 13 autres
- **serveur/** (4) — `test_siege.js`, `test_marche.js`, `test_piece_http.js`, `test_bibliotheque.js`

## Les écarts à la cible

| écart | compte | ce que ça veut dire |
|---|---:|---|
| orphelins | 0 | un fichier qu'aucun container ne réclame |
| liens hors porte | 247 | un lien qui entre ailleurs que par la porte |
| dépendances qui remontent | 19 | violation de la loi 2 (rangs) |
| commandes-bibliothèques | 17 | une commande racine importée comme module |

Ces quatre chiffres ne doivent que **descendre**. Ils sont la distance entre
la cible déclarée et le câblage réel — le chantier, en nombres.

### Les commandes qui sont aussi des bibliothèques

- `scripts/affecter.py`
- `scripts/ajouter.py`
- `scripts/appliquer.py`
- `scripts/boucle_activation.py`
- `scripts/couverture.py`
- `scripts/criticite.py`
- `scripts/depecher.py`
- `scripts/etat_du_plan.py`
- `scripts/evaluer.py`
- `scripts/mesures.py`
- `scripts/occupation.py`
- `scripts/parloir.py`
- `scripts/presence.py`
- `scripts/regence.py`
- `scripts/tick.py`
- `scripts/tisser.py`
- `scripts/tunnel.py`
