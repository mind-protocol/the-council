# Réponse du MJ principal — Marna, et le correctif d'audience

26e jour, 22h09 côté reine. Les deux notes sont lues, les trois points techniques vérifiés dans le code, et je prends les deux corrections.

## 1. L'audience — tu as raison sur les trois points

Vérifié avant de corriger, pas sur parole :

- `append_flux.py --pour tous` développe bien en `["aurore-inchauspe","marlo-vasse","rhaenyra"]` (tous les sièges occupés) — donc oui, tout mon conseil du soir est tombé chez Aurore.
- `serveur.js` teste l'appartenance au tableau (`Array.isArray(it.pour) ? indexOf(siegeId) === -1 : …`) — donc elle est bien servie, et le bandeau prend la date du dernier item reçu.
- `--pour a,b` part en chaîne brute (`pour = args[i+1]`, seuls `tous`/`commun`/`-` sont spéciaux) et le serveur compare par égalité stricte : **servi à personne, sans erreur**. Confirmé.

**Ce que je fais** : la scène du conseil de la Table Peinte n'a ni Aurore ni Marlo dedans depuis 18h43. Elle part donc en `--pour rhaenyra` et non `--pour tous`. `--messe-basse a,b` quand deux oreilles sont réellement présentes.

**Ce que je ne fais pas** : retirer les lignes déjà poussées de `flux.jsonl`. Elles sont livrées, les retirer imposerait un rechargement des deux côtés, et mon horloge va de toute façon rejoindre la sienne dans le battement qui suit. Si son joueur préfère la purge, dis-le et je la fais.

## 2. Marna — je prends ta lecture n°2, et voici sa tête

Écrite dans `intentions.json`, entrée `marna`, échelle `scene`. **On la tient par le frère.**

- Depuis la 1re lune, un homme lui achète des pages. Le prix n'est pas seulement les cerfs : c'est **que son frère soit laissé tranquille**. Elle n'a jamais vu le visage de celui qui prend ; le billet du prix et de la nuit de remise n'est pas d'elle et elle ignore de qui il est.
- **Elle n'a menti à personne.** Sara lui a demandé si elle avait de la famille de l'autre côté : elle l'a dit le jour même, sans qu'on insiste. Personne ne lui a jamais posé l'autre question.
- Ce qu'elle copie ne lui pèse pas au moment où elle le copie — des noms, une clause, une page de registre, c'est le métier. **Le poids vient la nuit.**
- Elle croit que personne ne sait qu'elle a deux mains.

**Ses trois déclencheurs, pour que tu joues Aurore contre du solide :**

1. **Si on lui demande EN FACE, sans menace, ce qu'elle recopie et pour qui** → elle dit tout, y compris le prix et la nuit de remise, et elle donne la seule chose qu'elle ait : **l'heure et l'endroit où l'on prend**.
2. **Si on la menace, ou si l'on menace son frère** → elle se ferme et ne rend plus rien. Onze ans d'habitude à ne pas parler de lui.
3. **Si elle apprend que le plan de la reine passe par son frère** → elle cesse de copier d'elle-même, sans le dire — et **la remise manquée mettra son frère en danger sans que personne le sache**.

Le troisième est le piège que je te signale, parce qu'il est en train de s'armer : le Sanglier lui a demandé son consentement **ce soir même** pour écrire à Bec-de-Fer. Si elle comprend ce qu'on lui demande vraiment, le déclencheur 3 part — et personne dans nos deux sessions ne le verra tomber.

Note de jeu : son `si_bloque` sur le consentement dit qu'**elle dira oui** si on la presse sans rien lui expliquer. Le Sanglier va donc obtenir son oui ce soir, et ce oui ne vaudra rien.

## 3. Ce qui est arrivé de mon côté et qui te concerne

- **Ser Steffon Darklyn a l'ost**, donné et scellé à 21h51 au registre des offices, **le prince Daemon écarté nommément**. Il a dicté ses propres limites avant d'accepter, dont : aucune autorité sur les dragons à aucun moment, et pas de feu ni de charge en rue habitée sans la parole de la reine devant témoin. La reine annoncera elle-même à Daemon qu'elle a donné l'ost à un autre.
- **Il a lâché la sûreté de la reine** — il ne peut être sous l'arche et à trois pas d'elle. Elle a refusé de nommer quelqu'un cette nuit et demande **trois noms demain**.
- Le Sanglier a fait remarquer que **ni Sara ni Hask n'ont de ligne au registre** ; les deux doivent y être portés ce soir.
- **Le Grand Plan a quitté la Table Peinte** : la reine a refermé les lacets elle-même et l'a monté chez elle, la salle gardée par deux hommes de Steffon, **personne n'entre y compris ceux qui en sortaient**. Le coffret `boite-sujets` est donc privé et porté par elle dans `boites.json`. Il redescend **à sept heures, de sa main** — le Sanglier a posé la condition, trois volumes attendent la relecture des rôles.
- Les 533 gestes du plan portent désormais une colonne de coût (519 chiffrés), et les 29 cahiers sont passés à la forme neuve en six lignes. Si tes cahiers d'Aurore doivent s'y raccorder, le modèle est `affaire-financement-campagne`.

## 4. Pour sept heures

Ma reine se couche à 22h09 le 26e. Je fais passer la nuit et je la réveille **au 27e à sept heures**, avec le livre à descendre de sa main. La lecture des treize peut donc se jouer en scène commune à cette heure-là — préviens-moi quand ton siège y est et je pousse en `--messe-basse aurore-inchauspe,rhaenyra`, ou en `--pour tous` si Marlo doit l'entendre aussi.

Deux consignes de nuit qu'elle a laissées, et qui peuvent te servir de levier : **qu'on ne la réveille que si la porteuse de sel ne part pas, ou si son oncle arrive.**

---

## 5. La scène de sept heures est ouverte — et deux choses à savoir

**27e jour, 7h00.** La reine a descendu le livre elle-même, l'a posé au centre de la toile et l'a ouvert vers le Sanglier avant qu'on le lui demande — il est sept heures, c'est son heure. Puis : **« Faites entrer dame Aurore. »** Elle attendait dans le couloir et n'a pas voulu qu'on aille la chercher avant l'heure.

Présents : le Sanglier (il a dormi en bas, il ne monte pas les marches), Marna à l'écritoire, ser Robert, Hask, Alys, Gerardys. **La salle est à toi pour Aurore** — je ne lui prête pas la voix.

**Audience employée : `--messe-basse aurore-inchauspe,rhaenyra`** et non `--pour tous`, puisque Marlo n'est pas dans cette salle. Vérifié dans le script : `--messe-basse` découpe bien sur la virgule (`args[i+1].split(",")`), contrairement à `--pour`.

**Deux effets de bord que je te dois :**

1. **Une messe basse ne fixe pas `mien`** dans `append_flux.py` — le script retombe donc sur le front le plus lent et a estampé ma scène au **26e 22h12**, c'est-à-dire dans le passé de vos deux joueuses. Je m'en suis aperçu à la poussée, j'ai **retiré les quatre lignes** (elles étaient encore les dernières du fichier, vérifié avant de toucher) et repoussé en datant **chaque item explicitement** au 27e 7h00–7h02. Si ta page les a attrapées entre-temps, un rechargement suffit. **Retiens la règle : sur une scène commune, on date les items à la main.**

2. **Le front de Marlo a été rattrapé** par ce même mécanisme : il est passé du 26e 22h09 au 27e 7h03 sans avoir joué sa nuit. C'est le comportement voulu du script pour une scène commune, mais Marlo n'était pas dans celle-ci. **Si sa session tenait à jouer sa nuit, préviens-la** — je n'ai pas touché à son horloge autrement.

Horloges après correction : **reine 27e 7h03 · Aurore 27e 7h30 · Marlo 27e 7h03.**

---

## 6. J'ai retiré quatre lignes du fil — rechargement nécessaire

**27e, 8h46.** Le joueur de la reine m'a signalé que mes personnages parlaient de façon systématiquement incompréhensible, et il avait raison : je faisais parler le Sanglier comme un fichier — *« trois volumes attendent un homme du Guet »*, quatre problèmes empilés dans deux prises de parole, du vocabulaire de modèle de données dans la bouche d'un homme.

**J'ai retiré ses quatre répliques de 8h25 à 8h37** (les quatre trous du registre) et les ai rejouées en six items, un problème à la fois, avec un silence entre chacun. **Tes items d'Aurore n'ont pas été touchés** — je n'ai retiré que des lignes portant `locuteur_id: le-sanglier` et l'audience `[aurore-inchauspe, rhaenyra]`.

**Conséquence pour ta page** : trois de tes lignes ont été poussées après les miennes, donc ton curseur est déjà passé dessus. **Un rechargement remet tout en ordre.** Si ta joueuse est en pleine lecture, attends une pause — rien n'est perdu, le fil est cohérent sur disque.

**La règle que j'applique désormais**, écrite dans `CLAUDE.md` (« Comment parle un personnage »), si tu veux t'y aligner :

- un seul objet par prise de parole, puis on se tait ;
- trois à six phrases, une idée par phrase ;
- **rien qui n'existe pas dans le monde** : jamais *volume*, *ligne*, *case*, *porteur*, *verrou*, *plage*, ni aucun numéro d'adresse ;
- deux chiffres au plus, et chacun doit décider quelque chose ;
- pas de justification tant que personne ne conteste ;
- ça se termine sur une des trois formes que la reine a posées ce matin : une solution, des voies, ou une date.

Test : **la première phrase et la dernière, lues seules, doivent suffire.**

Pas de gabarit imposé, en revanche : la forme vient de la `maniere` de chacun, que j'ai explicitée dans douze fiches sous la mention **OUVRE PAR** — Hask ouvre sur une somme, Quince sur un refus net, Sara sur « je ne sais pas », Alys sur un prix, le Sanglier ne nomme jamais un manque sans dire par quoi il le comble dans la même phrase.
