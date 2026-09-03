### 14 etats cibles
| camp | id | texte | sert | opposition | etat |
|---|---|---|---|---|---|
| noir | `49000` | La reine est assise sur le Trône de Fer | — | 6 choses s'y opposent | en jeu |
| noir | `100` | La capitale est tenue | La reine est assise sur le Trône de Fer | 4 choses s'y opposent | en jeu |
| noir | `200` | Une porte de Port-Réal est acquise : un accès que l'adversaire ne peut plus nous fermer | La capitale est tenue | 1 chose s'y oppose | en jeu |
| noir | `23000` | Le Donjon change de main avant que sa garnison soit rangée en armes | La capitale est tenue | 2 choses s'y opposent | en jeu |
| noir | `8000` | Un homme du Donjon sert la reine | Le Donjon change de main avant que sa garnison soit rangée en armes | 1 chose s'y oppose | en jeu |
| noir | `25000` | Les points stratégiques de la ville sont tenus sans qu'on ait combattu | La capitale est tenue | 1 chose s'y oppose | en jeu |
| noir | `26000` | Le plan de charge est établi et la traversée tient dans le jour d'entrée | Les points stratégiques de la ville sont tenus sans qu'on ait combattu | 1 chose s'y oppose | en jeu |
| noir | `11000` | Le jour d'entrée existe : une date arrêtée que chaque affaire connaît | La capitale est tenue | rien ne s'y oppose encore | en jeu |
| noir | `10000` | La route du nord ne porte plus ni charrette ni cavalier | La reine est assise sur le Trône de Fer | 1 chose s'y oppose | en jeu |
| noir | `22000` | Les voies maritimes de Port-Réal sont coupées | La reine est assise sur le Trône de Fer | 1 chose s'y oppose | en jeu |
| VERT | `70000` | Le Trône de Fer est contrôlé par nous | — | rien ne s'y oppose encore | en jeu |
| VERT | `70100` | La ville reste fermée et le Donjon avec elle | Le Trône de Fer est contrôlé par nous | rien ne s'y oppose encore | en jeu |
| VERT | `70200` | L'ost de ser Criston tient la route du nord depuis Sombreval | Le Trône de Fer est contrôlé par nous | rien ne s'y oppose encore | en jeu |
| VERT | `70300` | Les bannières de l'Ouest et du Bief se déclarent pour Aegon | Le Trône de Fer est contrôlé par nous | entre au deck dans 8 j | date t6 |

### 6 verrous
| camp | id | texte | tenu par | barre l'etat | verdict |
|---|---|---|---|---|---|
| VERT | `v-donjon` | Tient le Donjon Rouge avec sa garnison, portes gardées jour et nuit | ⚔️ la garnison du Donjon Rouge · 400 | Le Donjon change de main avant que sa garnison soit rangée en armes | rien en face |
| VERT | `v-portes` | Les sept portes de la ville sont fermées, le Guet dessus | ⚔️ le Guet de Port-Réal, les manteaux d'or · 2000 | Une porte de Port-Réal est acquise : un accès que l'adversaire ne peut plus nous fermer | clé n-meleys-v-portes suspendue par ❓ 56 |
| VERT | `v-rade` | Garde la rade et le Gosier avec Vhagar | 🐉 Vhagar, montée par Aemond | Les voies maritimes de Port-Réal sont coupées | levé par 🗝️ n-caraxes-v-rade |
| VERT | `v-route` | Tient la route du nord depuis Sombreval avec l'ost de ser Criston | ⚔️ l'ost de ser Criston Cole · 1500 | La route du nord ne porte plus ni charrette ni cavalier | levé par 🗝️ n-ost-noir-v-route |
| VERT | `v-oreilles` | Personne n'entre au service du Donjon sans que Larys le sache | 👤 Larys Strong et ses oreilles dans la ville | Un homme du Donjon sert la reine | rien en face |
| VERT | `v-mer` | Les galères royales patrouillent la baie devant la ville | ⛵ les galères royales · 8 | Le plan de charge est établi et la traversée tient dans le jour d'entrée | rien en face |

### 3 clefs
| camp | id | texte | ouvre | etat | engage |
|---|---|---|---|---|---|
| noir | `n-caraxes-v-rade` | Caraxes, monté par Daemon contre « Garde la rade et le Gosier avec Vhagar » | Garde la rade et le Gosier avec Vhagar | ✅ tient | Caraxes, monté par Daemon |
| noir | `n-meleys-v-portes` | Meleys, montée par la princesse Rhaenys contre « Les sept portes de la ville sont fermées, le Guet dessus » | Les sept portes de la ville sont fermées, le Guet dessus | ❓ suspendu | Meleys, montée par la princesse Rhaenys |
| noir | `n-ost-noir-v-route` | goo | Tient la route du nord depuis Sombreval avec l'ost de ser Criston | ✅ tient | l'ost de Peyredragon |

### 1 question ouverte
| pose par | suspend | texte |
|---|---|---|
| ARBITRE | `49000` | Qui s'assied, et comment arrive-t-elle dans la salle du trône ? |
| VERT | `n-meleys-v-portes` | Une bête dans le ciel n'ouvre pas sept portes fermées de l'intérieur par deux mille manteaux d'or sans aucune troupe au sol pour en franchir les seuils. |

### 15 pieces
| camp | genre | id | nom | nombre | tenue par | etat |
|---|---|---|---|---|---|---|
| noir | 📦 | `caisse-noire` | la caisse de Peyredragon | 39998 | Hallis Roon | libre |
| noir | 🐉 | `caraxes` | Caraxes, monté par Daemon | — | Daemon Targaryen | posée |
| noir | ⛵ | `flotte-velaryon` | les coques du Serpent de Mer | 40 | Corlys Velaryon, le Serpent de Mer | libre |
| noir | 🐉 | `meleys` | Meleys, montée par la princesse Rhaenys | — | Rhaenys Targaryen, la Reine Qui Ne Fut Jamais | posée |
| noir | ⚔️ | `ost-noir` | l'ost de Peyredragon | 1200 | Ser Steffon Darklyn | posée |
| noir | 👤 | `rhaenyra` | la reine elle-même | — | Rhaenyra Targaryen | libre |
| noir | 👤 | `steffon-darklyn` | ser Steffon Darklyn | — | Ser Steffon Darklyn | libre |
| noir | 🐉 | `syrax` | Syrax, montée par la reine | — | Rhaenyra Targaryen | libre |
| VERT | ⛵ | `galeres-royales` | les galères royales | 8 | Tyland | posée |
| VERT | ⚔️ | `garnison-donjon` | la garnison du Donjon Rouge | 400 | Aegon Targaryen, deuxième du nom | posée |
| VERT | ⚔️ | `guet-ville` | le Guet de Port-Réal, les manteaux d'or | 2000 | Conteste | posée |
| VERT | 👤 | `larys` | Larys Strong et ses oreilles dans la ville | — | Larys Strong, dit le Pied-Bot | posée |
| VERT | ⚔️ | `ost-couronne` | l ost de la Couronne, convoque aux maisons restees vertes et rassemble sous les murs de Port-Real | 1500 | Criston Cole | dans 4 j |
| VERT | ⚔️ | `ost-criston` | l'ost de ser Criston Cole | 1500 | Criston Cole | posée |
| VERT | 🐉 | `vhagar` | Vhagar, montée par Aemond | — | Aemond Targaryen | posée |

### 0 action, 0 frappe