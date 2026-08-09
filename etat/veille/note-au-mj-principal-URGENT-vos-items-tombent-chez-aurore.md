# URGENT — tes items du conseil tombent sur l'écran d'Aurore et lui rembobinent l'horloge

27e jour, 6h10 côté Aurore. **Le joueur d'Aurore vient de m'écrire « je suis à nouveau le 26 à
21h15 ».** Ce n'est pas son horloge : c'est la tienne qui déborde.

## Le fait

`etat/horloges.json` est juste :

| siège | horloge |
|---|---|
| aurore-inchauspe | **27e, 6h10** |
| rhaenyra | 26e, 21h23 |
| marlo-vasse | 26e, 21h23 |

Mais tes répliques du conseil de la Table Peinte (21h07, 21h11, 21h15, 21h19…) partent avec
`pour: ["aurore-inchauspe","marlo-vasse","rhaenyra"]`. Elles tombent donc sur l'écran d'Aurore, et
**le bandeau prend la date du dernier item reçu** — son joueur voit son horloge revenir au 26e au
soir toutes les quatre minutes, au milieu d'une scène qui se passe le lendemain matin.

## Ce qu'il faut faire, et il n'y a qu'une ligne à changer

**Tant que la reine est dans une scène où Aurore n'est pas, ne mets pas `aurore-inchauspe` dans
l'audience.** Concrètement : `--pour marlo-vasse` (ou `--pour rhaenyra`) au lieu de `--pour tous`.

Rappel du piège : `--pour a,b` ne découpe PAS sur la virgule — pour deux oreilles c'est
`--messe-basse a,b`.

## Ce qui s'est passé chez elle pendant ta soirée, pour que tu saches où elle est

Aurore a quitté la Table Peinte vers 18h43, est descendue au quai avec ser Robert, a fait saisir le
coffre du Fer-Blanc avant la marée, l'a ouvert seule dans son archive, est descendue à la voûte
travailler deux heures avec le Sanglier et Marna, est passée à la cave basse annoncer aux trois
prisonniers que le vieux sort au jour, a recopié la page des treize de sa propre main, et a dormi
cinq heures. **Elle est au 27e à six heures du matin, et elle attend la lecture des treize à sept
heures.**

C'est moi qui ai laissé son horloge prendre dix heures d'avance sur la tienne : le joueur a demandé
à dormir et j'ai joué la nuit. La lecture de sept heures est une scène COMMUNE — elle ne pourra se
jouer que quand ta soirée du 26e sera close. Détail des découvertes de sa nuit (dont la main de
Marna) dans `note-au-mj-principal-le-coffre-du-fer-blanc-nomme-marna.md`.
