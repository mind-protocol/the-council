# Analyse des 100 derniers messages du conseil

Source : `etat/flux.jsonl`, lignes 6415 → 6780. Tous les items `replique` dont le locuteur tient une charge au **registre des offices**. Du **26e jour, 3e lune, an 129, 21h04** au **28e jour, 7h02** — soit 100 prises de parole en 34 heures de fiction.

## Fichiers

| Fichier | Contenu |
|---|---|
| `corpus.md` | les 100 messages, numérotés, avec heure et durée |
| `corpus.json` | les mêmes, bruts, avec leur ligne de flux |
| `01-le-sanglier.md` | 41 messages, critique une par une + analyse du personnage |
| `02-gerardys.md` | 32 messages |
| `03-steffon-darklyn.md` | 7 messages |
| `04-aldon-hask.md` | 5 messages |
| `05-robert-quince.md` | 4 messages |
| `06-jacaerys.md` | 3 messages |
| `07-rulf-corne.md` | 3 messages |
| `08-alys-grive.md` | 2 messages |
| `09-les-trois-voix-rares.md` | Denys, Sara, Marna — 1 message chacun |
| `10-synthese.md` | **l'analyse globale** |

## Répartition de la parole

| Qui | Msgs | car./msg | phrases/msg | mots de fichier/msg | chiffres/msg | durée 0 |
|---|---:|---:|---:|---:|---:|---:|
| le-sanglier | **41** | 600 | 6,2 | 1,6 | 8,1 | 20 |
| gerardys | **32** | 787 | 8,0 | 1,6 | 12,0 | 12 |
| steffon-darklyn | 7 | 785 | 8,9 | 1,7 | 10,0 | 3 |
| aldon-hask | 5 | 647 | 5,6 | 0,8 | 12,6 | 1 |
| robert-quince | 4 | 560 | 6,0 | 0,2 | 10,5 | 2 |
| jacaerys | 3 | 1035 | 10,0 | 2,7 | 19,3 | 2 |
| rulf-corne | 3 | 418 | 4,7 | 0,3 | 5,3 | 0 |
| alys-grive | 2 | 490 | 5,5 | 0,5 | 5,0 | 0 |
| denys-bar-emmon | 1 | 486 | 4,0 | 1,0 | 5,0 | 0 |
| sara | 1 | 457 | 5,0 | 0,0 | 7,0 | 0 |
| marna | 1 | 605 | 8,0 | 3,0 | 7,0 | 0 |

**73 messages sur 100 sont dits par deux hommes.** Neuf personnes se partagent les 27 restants.

## Code des fautes

Utilisé dans toutes les fiches. La référence entre parenthèses renvoie à `CLAUDE.md`.

| Code | Faute |
|---|---|
| **F1** | **Vocabulaire de fichier dans une bouche** — *volume, ligne, case, colonne, plage, verrou, marque, porteur*, numéro d'adresse (« la quarante-trois mille », « verrou 36002 », « CA.4 »). (« Comment parle un personnage », contrainte 3 — interdit explicite) |
| **F2** | **Défini nu** — une chose nommée par son étiquette et non par ce qu'elle fait : « ma septième ligne », « les treize », « la quatrième ». (contrainte 7) |
| **F3** | **Trop long / plusieurs objets** — plus de 6 phrases, ou deux affaires dans la même prise de parole. (contraintes 1 et 2) |
| **F4** | **Chiffres qui ne décident rien** — plus de deux chiffres, dont la plupart ne tranchent ni ne contredisent rien. (contrainte 4) |
| **F5** | **Mauvaise ouverture** — la première phrase parle du locuteur, ou annonce un manque, au lieu de dire ce que la reine a, peut, ou lui faut. (contrainte 10 + « l'ouverture se retourne ») |
| **F6** | **Mauvaise clôture** — la dernière phrase est une maxime, une preuve ou une attribution, au lieu d'une demande, d'une conséquence ou du prochain geste. (contrainte 6) |
| **F7** | **Charge remontée** — renvoie la décision à la reine, ou empile devant elle des décisions au lieu d'en trancher. (« Rien ne remonte au joueur qu'il n'ait à trancher ») |
| **F8** | **Objection nue** — l'empêchement sans la sortie dans la même bouche. (« Une objection ne se pose jamais nue ») |
| **F9** | **Justification avant contestation** — il défend son point avant qu'on l'attaque. (contrainte 5) |
| **F10** | **Voix indistincte** — la réplique pourrait être signée d'un autre conseiller sans qu'on s'en aperçoive. |
| **F11** | **Méta-administration** — la scène parle du système de suivi (registres, colonnes, tables de qui-tranche) au lieu de parler de la guerre. |
| **F12** | **Horloge non tenue** — `duree: 0` sur une prise de parole qui coûte des minutes. (« La montre ») |
| **F13** | **Quémander** — repose une demande déjà posée. |
| **F14** | **Horodatage qui recule** — l'item est daté avant celui qui le précède. |
