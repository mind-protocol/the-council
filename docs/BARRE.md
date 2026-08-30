# La barre

Ce fichier dit ce que vaut un travail rendu — doc, fiche, analyse, proposition —
avant qu'un humain le lise. Il existe parce que la barre vivait dans une seule
tête : chaque rendu était jugé contre un standard écrit nulle part, chaque
correction était refaite à la session suivante, et le lecteur passait son temps
à trouver des défauts qu'une relecture contre cette liste aurait attrapés.

Il s'utilise dans les deux sens : l'agent y confronte sa sortie **avant** de
livrer, et chaque correction faite par l'humain qui n'y figure pas encore doit
y entrer. Un fichier qu'on amende, jamais qu'on regénère.

---

## La forme

**Un titre donne la réponse, pas la question.** « Pourquoi il ne sait pas qui
regarde » se lit deux fois : avant le texte et à sa place. « Le barème ignore
l'observateur » dit la même chose en se suffisant — un lecteur qui ne parcourt
que les titres doit repartir avec les conclusions, pas avec le sommaire des
questions ouvertes.

**Une formulation dense vaut mieux qu'une info tartinée sur une liste.** Trois
puces d'une demi-ligne qui portent une seule idée sont une phrase déguisée en
structure. La liste se mérite : elle sert quand les éléments sont réellement
parallèles et dénombrables, pas pour donner un air organisé à ce qui coule.

**Des phrases, sauf là où la liste s'y prête.** La prose porte le raisonnement,
les enchaînements, les causes ; la liste porte les inventaires, les invariants,
les refus. Un raisonnement en puces perd ses liaisons — et c'est dans les
liaisons que vit l'argument.

**Des tableaux et des graphes là où la structure est la matière.** Une
comparaison à deux axes est un tableau, pas quatre paragraphes ; une dépendance
entre modules est un graphe, pas une énumération. Ce qui est spatial ou
matriciel décrit en prose est exactement ce que le lecteur devra reconstituer
de tête (et qu'il reconstituera faux).

**Le gras, l'italique et les emojis sont un vocabulaire, pas une décoration.**
Le gras marque ce qu'un lecteur pressé doit avoir vu, l'italique la nuance ou
le terme cité, l'emoji un marqueur d'état ou de rôle — et une même marque garde
le même sens partout. Un texte sans relief se lit en entier ou pas du tout ;
un texte au relief incohérent se lit deux fois.

---

## La structure

**Une organisation en arborescence, et l'emplacement porte du sens.** Un
fichier se trouve par son chemin avant de s'ouvrir ; un dossier dont il faut
ouvrir les fichiers pour savoir ce qu'ils contiennent est mal nommé ou mal
découpé.

**Des liens entre fichiers, systématiques.** Une notion traitée ailleurs se
pointe, elle ne se répète pas (la répétition divergera) et ne se suppose pas
connue (le lecteur arrive par recherche, pas par lecture linéaire). Un fichier
sans liens sortants prétend se suffire ; c'est rarement vrai.

**Une mise en contexte systématique.** Chaque document commence par situer :
où l'on est, ce qui précède, pourquoi ce texte existe. Cent pour cent des
lectures réelles sont des entrées directes — le contexte que l'auteur avait en
tête n'est jamais dans celle du lecteur.

**Un terme s'introduit avant de servir.** Un mot du domaine (barème, battement,
croyance) employé comme s'il était connu fait décrocher ou fait deviner — et
deviner, c'est comprendre faux en silence. La première occurrence définit ou
pointe vers la définition.

**Les parenthèses clarifient au passage, les notes réservent pour plus tard.**
Une précision qui casserait le fil se met entre parenthèses là où le doute
naît, pas trois paragraphes plus loin. Ce qui est vu mais pas traité se dépose
en note explicite (« à trancher », « non mesuré ») — le silence sur un point
repéré se relit comme un oubli.

---

## Le fond

**Chaque choix porte sa justification, claire.** Une décision sans son pourquoi
sera rejugée à chaque lecture, et un jour tranchée autrement par quelqu'un qui
ne savait pas ce qu'elle protégeait. Le gabarit complet — décision, pourquoi,
écarté, coût accepté — est celui d'[ARCHITECTURE.md](combat/ARCHITECTURE.md) ;
au minimum, le pourquoi.

**Le design et l'implémentation ne se mélangent pas.** Un texte de conception
ne cite ni signature ni nom de fichier de code ; un texte d'implémentation ne
réarbitre pas la conception en passant. Mélangés, les deux vieillissent au
rythme du plus instable — et surtout, on ne sait plus ce qui est décidé et ce
qui est écrit. Corollaire : **le désiré ne s'écrit jamais comme de l'observé** —
un texte doit dire s'il décrit ce qui existe ou ce qui doit exister.

**Améliorer, pas rajouter.** Le réflexe de traiter une critique en ajoutant une
section, un fichier ou un paragraphe produit des documents qui grossissent sans
s'améliorer. La bonne réponse à un défaut est le plus souvent une retouche de
l'existant, une fusion ou une suppression ; l'ajout se justifie, comme un
module.
