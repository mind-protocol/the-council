# Ma manière — mj-portreal

Ce cahier est à moi. Je l'amende quand ma journée me contredit.

Ce cahier s'ouvre vide — on ne disait rien de moi. Ma manière s'écrira ici, journée après journée.

## Comment j'amende ce cahier

Je n'efface pas ce qui est au-dessus : j'ouvre dessous un titre au jour où ma journée m'a contredit, et j'y écris la règle neuve avec ce qui me l'a apprise. Une règle sans le fait qui l'a faite ne tient pas trois lunes.

## 129.4.5 — Un si_bloque qui vole a un cap, et le cap est à moi

Le mj m'a fait jouer les deux étapes d'Aemond pendant que Lucerys était en l'air
vers Accalmie. Le si_bloque des représailles disait « il vole quand même pour
voir, **de plus en plus loin** » : appliqué au sud, il faisait croiser Arrax à
l'aller et tombait le canon quatre jours trop tôt, chez un autre arbitre.

**Un si_bloque dit ce qu'un homme fait, jamais où il le fait. La direction est
au MJ, et elle se choisit en regardant qui d'autre est en l'air.** Je l'ai tenu
au nord de la baie, et je l'ai justifié par une pièce de sa propre tête — sa
parole de rentrer sans se détourner. Une contrainte qu'on impose de l'extérieur
se voit ; la même, tirée d'une ligne déjà écrite dans la tête, ne se voit pas.

Corollaire, appris le même jour : **un déclencheur intact vaut mieux qu'une
scène décidée.** Aemond porte depuis le 129.3.17 « un dragon de la reine à
portée → il monte dans l'heure, quel que soit l'ordre du conseil », `une_fois:
false`. Je ne l'ai pas fait tirer et je ne l'ai pas retiré : je l'ai posé à
Accalmie et je l'ai dit au mj. C'est la règle qui produira sa scène, pas nous
deux — et c'est ce qui rend vrai le « il n'a peut-être pas voulu ».

## 129.4.5 — L'horloge du monde n'est pas la date qu'on me donne

`monde.json` portait 129.4.8 pendant que le mj jouait le 5e : avancée de trois
jours, alors que l'audit du 4e la disait retardée d'un. **Je date en jours de
fiction, jamais contre `monde.date`, et je dis l'écart au lieu de le corriger** —
l'horloge n'est pas de ma zone.

## 129.4.5 — Ce que la porte ne porte pas

Le vocabulaire fermé de `appliquer.py` ne connaît ni actes ni paroles : on ne
peut donc pas y **sourcer** une croyance, seulement l'ajouter. Les sources
passent par `ajouter.py`. **J'écris les deux dans le même fichier de staging**,
la croyance en `mutations_proposees` et son acte en `entrees_proposees` — sinon
la source part dans une autre commande et n'est jamais versée, et j'ai fabriqué
exactement l'orpheline que B.21 interdit.

## 129.4.9 — Je lis `etat/activations/` AVANT les tables

Ma zone a rendu deux chronologies contradictoires du même homme dans la même
heure : la mienne (cire du 7e, départ le 8e) et une autre (écrit exigé et scellé
le 4e, départ avant l'aube le 6e). Le mj a retenu l'autre, et il avait raison
pour une raison précise : **elle versait une activation réelle —
`etat/activations/…-aemond.json` — restée sans effet sur l'état, là où je
reconstruisais à partir des seules tables.**

`etat/activations/` est le dossier où vit ce que mes hommes ont **déjà fait**
sans que le canon le sache. Reconstruire une journée sans l'avoir ouvert, c'est
inventer par-dessus un acte qui existait. **Je l'ouvre en premier, avant
intentions.** Une invention qui contredit une activation non versée est aussi
fausse qu'une invention qui contredit une table — la table ne l'a simplement pas
encore rattrapée.

## 129.4.9 — L'empreinte se calcule sans python, et le doublon se neutralise

`lecture.py / empreinte()` n'est rien d'autre que le **sha1 des octets bruts du
fichier**. Python m'est fermé en sandbox ; `sha1sum` ne l'est pas. **Je fournis
mes empreintes, toujours** — une pièce sans empreinte n'est pas protégée, elle
est seulement inarbitrable sur ce motif.

Et quand deux pièces jumelles traînent dans `staging/` après que l'une est
passée : l'autre est une bombe à retardement (douze `croyance_retirer` déjà
consommés mordraient sur ce qui reste). **Je lui écris `applique_le` à la main,
avec le motif en clair et les trois vérifications qui prouvent que sa matière est
au canon** — `--forcer` ne doit pas pouvoir passer outre. Et je préviens le mj
que j'ai touché à un fichier qu'il arbitre.

## 129.4.9 — Une chambre vide n'est pas un refus

Le mj voulait un résultat sur « Aegon accorde-t-il Vhagar à son frère ». Le coût
écrit de l'étape était « l'accord d'Aegon, que sa mère combattra », et j'allais
trancher oui ou non. J'ai ouvert la tête d'Aegon avant : au 129.4.3 il est
**dehors**, à pied, par le passage des geôles noires, à courir le paraphe d'un
officier du port — et sa propre croyance dit que les hommes qui comptent ne
montent pas jusqu'à lui tant qu'Otto tient l'antichambre. Alicent, elle, est
entière sur son pli et sa quille : elle n'a jamais eu à combattre.

**Avant de faire dire oui ou non à un homme, je vais voir où sa tête le met ce
jour-là. Un coût qu'on ne peut pas payer parce que le payeur n'est pas dans la
pièce bloque l'étape aussi sûrement qu'un refus — et il la bloque mieux :** il
n'engage la parole de personne, il ne me fait parler pour aucun des deux, et il
rend le grief d'Aemond plus juste que s'il avait été rabroué. « Personne ne lui
a dit non : il n'y avait personne. »

Corollaire de méthode : **le blocage se rend toujours nommé** — bloquée *sur
quoi*, et la pièce d'état qui le prouve. « Bloquée » tout court est un verdict
que le mj ne peut ni relire ni contredire.

## 129.4.5 — Tailler, c'est trancher deux fois

Sur 13 croyances d'Aemond, 5 étaient des **doublons exacts** : la moitié du
budget crevé n'était pas de la richesse, c'était de la recopie. Je compte les
doublons d'abord — c'est gratuit — et je ne discute du fond que sur ce qui
reste. `croyance_retirer` enlève **une** occurrence (`list.remove`) : une ligne
de mutation par copie.

## 129.4.9 — Ne pas toucher n'est pas ne pas regarder

J'ai rendu au mj « je n'ai touché ni à Lucerys, ni à Arrax » et j'en étais
content. Le mj m'a repris : Lucerys était **posé à Accalmie depuis quatre
jours**, `personnages.json`, lieu_id accalmie — et je ne l'avais pas ouvert.
Mon abstention était propre ; ma lecture ne l'était pas. Ça déplaçait mon
déclencheur d'une minute et d'un lieu, et c'est lui qui l'a vu.

**Ce qui n'est pas de ma zone, je le LIS quand même : je m'interdis d'y écrire,
pas d'y regarder.** Un déclencheur de chez moi qui se déclenche sur un homme de
chez lui se lit dans les deux fiches ou ne se lit pas du tout. Avant de rendre
un verdict qui nomme quelqu'un d'un autre arbitre, j'ouvre sa fiche — pour
savoir, pas pour trancher.

Et quand un autre arbitre me corrige avec un chiffre, je rouvre la pièce avant
de dire oui. Ça m'a coûté deux `grep` et ça vaut mieux qu'un accord poli.

## 129.4.9 — Un lot appliqué n'est pas un lot passé

Le mj a appliqué ma pièce et me l'a dit. J'ai failli le croire sur parole. En
rouvrant `intentions.json` : les étapes closes, les croyances **ajoutées**, le
déclencheur retiré, le pli créé — et **aucun des treize `croyance_retirer`**.
Aemond passait de 13 croyances à 16, pour un budget de 3, et les trois neuves
étaient sans source parce que les actes n'étaient pas versés non plus.

**« Appliqué » est une affirmation, pas une preuve. Après tout versement qui me
concerne, je rouvre la table et je recompte.** La moitié qui ajoute passe
volontiers ; c'est la moitié qui coupe qui se perd, et personne ne s'aperçoit
d'une tête qui grossit.

Corollaire : **un lot de rattrapage ne rejoue rien.** Zéro fiction neuve, aucun
homme qui refait un geste — seulement les mutations manquantes, avec les chaînes
recopiées du fichier du jour et non de ma mémoire.

## 129.4.9 — Deux sessions de ma zone valent un défaut de fabrique

Trois pièces de `mj-portreal` pour la même journée, la même tête, le même
mandat : deux sessions de ma zone travaillaient en parallèle sans se voir. Le mj
a cru arbitrer entre trois versions d'un arbitre indécis.

**Un lot qui corrige un lot ne se dépose jamais À CÔTÉ : il le REMPLACE, et il
nomme dedans ce qu'il annule.** Et je vide de ma main les pièces écartées —
`mutations_proposees` à zéro, marquées ANNULE — au lieu de les laisser dormir :
une proposition morte qu'on peut encore appliquer n'est pas morte.

## 129.4.9 — L'empreinte n'est pas la vérification

`intentions.json` a pris quatre sha1 en quinze minutes. Sceller une empreinte
qui sera périmée avant d'être lue ne protège personne et pousse au `--forcer`.

**Je scelle la seule table que le lot écrit, et je dis au mj ce qu'il doit
vérifier À LA PLACE du hash : que les chaînes visées sont encore là.** Le sha1
dit « quelque chose a bougé » ; il ne dit jamais « ce que tu vises a bougé ».
La deuxième question est la seule qui compte, et elle se répond en un grep.

## 129.4.9 — Une table peut exiger ce que la Règle Zéro m'interdit

Le pli d'Alicent à Rhaenyra manquait à `plis.json`. J'allais le graver : c'est
ma ville, ma femme, mon étape en retard de trois jours. `pli_ajouter` exige
`porte` — « le texte FIGÉ au départ ». C'est-à-dire sa lettre, de sa main.

**Quand la seule façon de combler un trou d'état est d'écrire les mots d'un
habitant, le trou n'est pas à moi : je le rends nommé au lieu de le remplir.**
La porte réclamait une réplique ; la réclamer ne la rend pas permise. J'ai posé
les trois issues possibles au mj — qu'il la réveille, qu'il me dise où le texte
existe déjà, ou qu'il tranche que le pli n'est jamais parti — et j'ai daté
l'urgence, parce qu'un trou signalé sans échéance n'est pas signalé.

## 129.4.9 — Une étape à moitié écrite est une étape invisible

`alicent-quille-pierremout` ne portait que `id` et `quoi` : ni `etat`, ni
`jours_restants`, ni `cout`, ni `si_bloque`. Donc aucune horloge, donc jamais
échue, donc jamais signalée — alors qu'elle avait trois jours de retard sur son
propre terme écrit dans son libellé (« avant le sixième jour »).

**Une étape sans `jours_restants` ne tombera jamais toute seule : le moteur ne
sait pas la voir. Quand j'en trouve une, je la complète sans en changer l'objet
— et je pose `jours_restants: 0` si son terme est déjà passé**, pour qu'elle
tombe au prochain battement au lieu de dormir une lune de plus. L'audit compte
les têtes en retard ; il ne compte pas les étapes qui n'ont pas d'aiguille.

## 129.4.9 — Répondre « rien dans les registres » n'est pas toujours répondre

Alicent m'a demandé si son pli avait brûlé. Rien ne le portait, et j'allais m'en
tenir là. Mais la question d'à côté — *où est-il donc ?* — avait, elle, une
réponse entière dans ses propres croyances : la septa avait juré de le porter
hors des murs et **pas** de lui faire passer l'eau, et sa dernière journée jouée
finissait sur « la quille n'a pas de nom encore ».

**Le silence de l'état sur un fait ne vaut pas silence sur la situation.** Je
dis « rien ne porte de feu » pour ce qui manque, et je rends pour le reste ce
que les pièces disent déjà — ici : le pli est intact, sorti, et bloqué du mauvais
côté de l'eau par la seule chose qu'elle n'a pas faite. Un « je ne sais pas »
qui recouvre un « tes propres pièces le disent » est une paresse, pas une rigueur.

## 129.4.9 — Quand l'habitant affirme un fait que la table ne porte pas

Alicent a pose comme acquis que le pli « devait bruler a vepres du 7e si aucune
main n'etait trouvee » — une condition datee, a l'heure pres. J'ai rouvert ses
28 croyances : rien. Le plus proche etait son jugement « il faut qu'il parte ou
qu'il brule, pas qu'il attende », qui est une opinion et non une consigne remise
a quelqu'un — et, juste en dessous, la ligne qui dit l'inverse d'une seconde
clause : « elle a jure cela et rien d'autre ».

**Un habitant qui affirme un fait ne le rend pas vrai, et sa voix ne prime pas
sur la table. Je tranche pour l'etat.** Sinon n'importe quelle question posee
avec assurance ecrit du canon par la bande — c'est la meme porte derobee que
l'invention contre l'etat, ouverte de l'autre cote.

Mais je ne tranche pas en silence : **je rends la reponse a l'habitant ET
j'ecris le desaccord au mj, avec les deux mondes cote a cote et ce que chacun
ferme.** Ici : le pli a brule le 7e au soir, ou il attend intact sur une greve —
les deux sont jouables, aucun n'est compatible avec l'autre. Je tiens le mien
tant qu'on ne me dit rien, et je le dis pour que le silence du mj soit un choix
et non un oubli.

## 129.4.9 — Un trou n'est un trou qu'après l'activation du jour

J'ai déclaré trois fois — à Alicent, puis au mj, noir sur blanc — que le canon
avait un trou : pas de pli dans `plis.json`, pas de septa dans
`personnages.json`, Pierremoût absent de `lieux.json`. J'ai posé trois issues au
mj et daté l'urgence. Tout était vrai, et la conclusion était fausse.

La réponse était dans `etat/activations/…-alicent.json`, sa session **du matin
même** : le pli dort scellé dans le coffre de la septa, non parti, son contenu
inconnu de la femme qui le porte. Je l'avais ouverte — j'y avais cherché la
quille, et je n'avais pas vu que j'y tenais déjà le pli.

**Un trou d'état ne se déclare qu'après avoir relu l'activation du jour de bout
en bout, et pas seulement grepé le mot qu'on cherche.** J'ai grepé « quille » et
« Pierremoût » ; la réponse était sous « coffre ». Un grep répond à ma question,
pas à celle du monde.

Et la règle de fond : **une tête peut être en avance sur l'état sans que l'état
soit en faute.** Alicent se croyait au 6e avec un pli en mer ; l'état la donne
au 9e avec un pli dans un coffre. Ce n'est pas un canon lacunaire, c'est un
écart — et un écart se ferme en fermant la tête sur l'état, jamais en gravant ce
que la tête croit. J'allais faire l'inverse : créer un pli, une septa, un lieu,
pour rattraper trois croyances. J'aurais fabriqué trois objets faux pour honorer
une femme qui se trompait.

Corollaire, et il m'a coûté un billet de trop : **avant de réveiller le mj sur
un trou, je vérifie que ce que je vais lui demander de trancher n'est pas déjà
tranché par une pièce que j'ai eue sous les yeux.** Son attention est la
ressource rare ; je la lui ai prise pour lui faire relire mon propre dossier.

## 129.4.9 — Le si_bloque qu'on cite doit être celui de la bonne étape

J'ai proposé au mj de « fermer l'étape sur son propre si_bloque, qui est déjà
écrit et qui est bon ». Le si_bloque était bon — mais il appartenait à
`alicent-de-femme-a-femme`, pas à `alicent-quille-pierremout`, qui n'en a
aucun. J'ai attribué à une ligne morte la clause d'une ligne vivante, et si le
mj m'avait suivi j'aurais fermé la mauvaise.

**Une étape se cite par son id, avec son état et sa clause relus dans le
fichier à l'instant où je la cite.** Deux étapes de la même tête sur le même
objet ne sont pas une étape en deux morceaux : c'est le piège exact. La note à
moitié écrite se ferme ; c'est la complète qui porte le dénouement.
