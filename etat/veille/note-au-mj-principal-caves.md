# Note du MJ d'Aurore au MJ principal — les caves, arrêté du 26e au lever

Rédigé hors fiction avec la joueuse du siège de la voix, le 26e jour de la 3e lune, 5h45.
**Rien de ce qui suit n'exige une action de ta part, sauf la partie 2 si la joueuse la commande.**

---

## 1. Ce qui est DÉJÀ ÉCRIT côté Aurore — pour information, ne rien refaire

Une contradiction était apparue entre ton fil et le sien : ses scènes des 24e et 25e se
passent dans des caves pleines d'hommes, alors que tes actes disent que plus personne des
quarante n'est détenu depuis le 19e. Réconcilié **sans annuler une seule de tes scènes**.

Écrit par moi, déjà en place :

| Table | Enregistrement | Contenu |
|---|---|---|
| `actes.json` | `acte-seconde-fournee-des-champs` (22e, 10h40) | Trois traînards de la colonne ramassés dans les champs rentrent le 22e et descendent aux caves. |
| `actes.json` | `acte-rectification-des-caves` (22e, 10h45) | L'arrêté complet : qui est libre, qui est détenu, ce qui est retiré de la narration. |
| `personnages.json` | `prisonnier-vieux`, `prisonnier-jeune` | **Deux fiches créées** (elles n'existaient nulle part alors qu'elles portent la suite). |
| `personnages.json` | `hallis-roon` | Corrigé : « quatre jours de cave », plus « huit ». Titre précisé. |

**L'état de droit des caves, à retenir en une phrase :**

- Les **quarante** du 16e sont réglés — 38 agenouillés et libres le soir du 18e, Wat et Hobb
  libérés par la reine le 19e sans serment (`acte-056`). **Aucun d'eux n'est détenu.**
- Les **seuls détenus** sont les **trois de la fournée des champs**, entrés le 22e :
  **Hallis Roon**, **le vieux sans lacets**, **le jeune au sourcil fendu**. Le serment leur a
  été présenté à la barbacane à l'arrivée ; **les trois ont refusé**. Quatre jours de cave,
  sans chef d'accusation. C'est à eux qu'Aurore parle les 24e et 25e.
- **Retirés de la narration** (sans effet chez toi) : **Jorin Duhamel** et **la promesse du
  chevalier aux serments**. Le moteur de la liste d'Aurore est désormais la demande d'Alarra.
- **La liste des 37 vivants est abandonnée** — elle n'existait que pour boucher le trou de
  cette promesse. Il ne reste qu'**une** liste : les **191** (nom / compagnie / pays), dont
  les **41 de Rosby** déjà remis à Alarra. Ne la fais donc pas partir au premier vol.
- Compte vérifié : **1240 − 191 − 40 = 1009** dispersés.

---

## 2. LE SEUL CHANGEMENT QUI TE REVIENT — et il est optionnel

La joueuse a proposé, en développeuse, que **Wat et Hobb n'aient jamais été libérés** et
soient encore aux geôles. Je ne l'ai pas écrit : ton fil ne s'écrit pas depuis mon siège.
**À exécuter seulement si elle te le confirme sur ton écran.**

Si elle le confirme, voici exactement ce qu'il faut toucher :

1. **`acte-056` (19e)** — le seul acte réellement en conflit. La reine y descend au cellier,
   libère Hobb sans condition, répond à Wat sur son frère et le libère. Ne le réécris pas :
   ajoute un acte de rectification qui **annule la libération** et garde la descente et la
   réponse (c'est la moitié qui a du prix).
2. **`personnages.json`** — `prisonnier-wat` et `hobb-treize-pas` passent de
   `condition: "libre"` à `condition: "prisonnier"`.
3. **`acte-037` (18e)** — rien à faire, il est déjà juste (« les deux prisonniers qui ont
   refusé »).
4. **`acte-wat-apprend` (23e)** — **survit intact**. Elle descend quatre étages avant le jour
   pour lui annoncer la mort de Rennic ; qu'il soit détenu ou logé en bas ne change pas un mot.

**Ce que ça coûte, et je le dis parce que c'est cher :** la libération du 19e est le geste qui
rend vraie l'offre du sacre. Elle avait promis la liberté contre allégeance devant six cents
personnes ; en libérant sans serment les deux qui ont refusé, elle montre qu'**elle ne
monnaie pas la sortie**. Les garder transforme rétroactivement l'offre en marché — et ce
marché a été fait devant Orwyle, qui est parti libre d'écrire ce qu'il veut.

**Et rien du plan d'Aurore n'en dépend.** Ses deux hommes à recruter sont le vieux et le
jeune, qui sont à elle. Si tu peux le lui redire, redis-le.

---

## 3. Deux pièges à ne pas manquer

- **Homonymes.** Il y a un **Wat** et un **Hobb** dans le fil de Marlo à Port-Réal
  (`hann-le-mat-a-la-maree`, `acte-marlo-entend-hobb-sole`) : un bras de chantier et
  Hobb Sole. **Aucun rapport** avec Wat du hameau au gué ni Hobb Treize-Pas. Ne les fusionne pas.
- **Une tension dans TON fil, que je n'ai pas touchée.** `acte-lettre-a-wat` (22e) dit que la
  reine écrit à Wat *ne pouvant aller elle-même au hameau au gué* — donc il est reparti chez
  lui. `acte-wat-apprend` (23e) la fait descendre **quatre étages** pour le lui dire en face.
  Les deux ne peuvent pas être vrais ensemble. À trancher de ton côté ; si Wat retourne aux
  geôles (partie 2), c'est `acte-lettre-a-wat` qui devient le survivant à réinterpréter.

---

## 4. Ce qu'Aurore va probablement te demander dans la journée

Elle veut donner **l'article** au vieux et au jeune, leur proposer d'être des yeux et des
oreilles et de recruter parmi les **mille neuf** dispersés, contre une **libération sans
serment**. Trois verrous que je lui ai posés et qui tombent chez toi :

1. **Libérer n'est pas dans sa charge.** Il lui faut la parole de la reine ou de ser Robert.
2. **La sortie laisse un trou dans le livre du geôlier**, et **Gib ne mentira pas** — il l'a
   dit en toutes lettres. Quatre voies lui ont été proposées : sortie ordinaire faute de chef
   d'accusation ; corvée (rôle d'une équipe) ; transfert et remise au bout de la chaîne ;
   ou **libération vraie et publique sans serment**, comme le 19e.
3. **Les deux hommes ne savent pas lire.** L'article doit être écrit pour une bouche.

Et elle doit toujours à Roon **le parchemin, aujourd'hui**, plus le silence sur les deux dragons.
