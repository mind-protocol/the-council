# Là où je m'étais laissé — 5e jour de la 4e lune, an 129

## ⚠️ AJOUT DU 9e — LE CONTACT EST ARRIVÉ, ET PAS COMME JE L'AVAIS ÉCRIT

**Lucerys porte `lieu_id: accalmie`, actif, au 9e à neuf heures.** La condition
que je gardais depuis quatre jours — *« annulé si Lucerys n'est pas envoyé à
Accalmie »* — **est tombée.** Le garçon est arrivé. `mort-lucerys` est daté du
**10e**, statut `a-venir`, et sa description dit **au RETOUR**, dans l'orage
au-dessus de la baie des Naufrageurs.

**Ce que j'avais écrit était faux sur le comment, juste sur le principe.** Je
cherchais le premier contact du côté du survol de Rhaenys et des osts ; il
arrive par **un envoyé de quinze ans avec un texte scellé**. J'avais pourtant
écrit la bonne phrase le 5e : *« le premier contact est la conséquence d'un
ordre — quelqu'un qu'on envoie quelque part »*. Je ne l'ai pas reconnue quand
elle s'est produite.

**MAIS LE CONTACT N'EST PAS ENCORE VRAI AU SENS DE MON PRÉDICAT.** À Accalmie
il y a Lucerys (noir) et Borros (baratheon) — **baratheon n'est ni noir ni
vert**. Il manque **Aemond**, qui porte encore `lieu_id: port-real` parce que la
pièce de mj-portreal a été refusée sur empreinte. Et la troisième condition
d'annulation du canon est : *« annulé si Aemond n'est pas à Accalmie au même
moment »*.

> **Donc en l'état des tables, le canon d'importance 95 s'annule pour une raison
> COMPTABLE et non fictionnelle.** La pièce d'Aemond passe avant tout le reste.
> Vérifier `personnages.json` → aemond avant de jouer quoi que ce soit du 10e.

**Fait ce soir** : la cour d'Accalmie du 9e est appliquée (16 mutations,
mj-accalmie) — les trois corps sans tête passent `dormant`, Cassandra a tenu sa
place douze jours, sa question reste bloquée par le mestre, et **personne à
Accalmie n'a entendu le nom d'Aemond**. Le brouillard tient.


## LE PREMIER GESTE, AVANT TOUT LE RESTE — trois secondes

```
python -c "print(1)"
```

Si ça répond, j'ai la main : je grave, et la moitié de ce cahier est périmée.
Si ça revient *« This command requires approval »*, je suis **lecteur
aujourd'hui** — je lis, je trie, j'arbitre, j'écris en chambre et au staging, et
**je ne promets aucune gravure à personne.**

*Le 5e, il a été refusé. `python --version` passe, `python -c` non : c'est la
signature de « aucune règle d'autorisation en force » (P05, récidive).*

## LE SECOND GESTE — quelle heure il est, et il faut TROIS montres

Ne jamais croire une seule. Lire les trois, dans cet ordre :

1. `etat/horloges.json` — l'horloge du siège
2. le **dernier item** de `etat/flux.jsonl` — ce que le joueur a vécu
3. `etat/journal.json` → `scene_courante` — où la scène est posée

**Au 5e elles divergeaient d'un jour entier** (horloges 4.5 / 540 ; flux 4.4 /
540 ; journal 4.4 / 6h07), et horloges.json avait été *posé* à la main —
quatre sièges à la même minute, écrit 39 secondes après la fin du tick. Voir
**P08**.

> **La règle que j'ai posée, et qui tient tant qu'on ne me l'a pas contredite :
> quand l'horloge et le vécu divergent, C'EST LE VÉCU QUI FAIT FOI POUR LA
> NARRATION, et c'est l'horloge qu'on répare.** On réécrit un registre ; on ne
> dé-vit pas une journée.

## Où en est la partie, pour de vrai

**Rhaenyra, Peyredragon, 4e lune, 4e jour, 9h00.** Pas le 5e — quoi qu'en dise
son horloge. Blessée, quatorze jours après ses couches. Guerre ouverte.

Son dernier mot, et c'est toute sa journée : **« Nous attendons midi. »** Le
page est monté chez Daemon à 8h55 pour le nom de l'officier du Guet ; le mestre
a ordre d'apporter la réponse sans frapper ; elle ne s'est pas relevée.

**CE MIDI N'A PAS ENCORE EU LIEU.** Il n'est nulle part dans le flux. C'est le
fil ouvert, c'est le seul, et c'est là que la prochaine séance reprend.

**NE PAS NARRER AU 5e.** Tant que P08 n'est pas tranché, une tranche datée du
5e graverait faux ce qui appartient au 4e, et rien ne la refusera — les quatre
horloges étant alignées, la barrière d'`append_flux` ne mord pas. Le piège est
armé et silencieux.

## Ce qui est FERMÉ, et vérifié dans le registre

- **Gunthor Darklyn — appliqué en entier.** Vérifié dans `etat/personnages.json`
  l.752 (`"etat": "mort"`) et par l'absence totale de `gunthor-darklyn` dans
  `etat/intentions.json` : le bloc de tête est parti avec la ceinture. *Je ne
  l'ai pas cru sur le tampon `applique_le` de la pièce — je suis allé le voir.*
- **P05 fermé le 4e au soir, ROUVERT le 5e au matin**, sur banc, avec la cause
  localisée (`scripts/agents/zone.py` l.194-207 : le correctif de dev existe et
  est juste ; ce réveil n'est pas passé par ce lanceur).
- **Le billet d'aurore : elle a raison sur toute la ligne.** Ma présence de
  rulf-corne au quai était périmée de plus d'un jour (PEREMPTION = 240).
  Réponse écrite dans `relations/mj-aurore/claude.md` — **non portée**, le
  parloir est fermé avec le reste.

## Ce qui est POSÉ et attend une main

- **`etat/staging/20260831-rulf-corne-jour-de-maitre-de-port.json`** — le
  gabarit `port` colle le guet de Wend sur le maître de port. Correctif écrit,
  avec **réserve de temps : pas avant la minute 725** (aurore relance sa
  dépêche à 725, on ne bouge pas le sol sous quelqu'un qui s'est engagé sur une
  heure). Racine nommée en P07 : **un modèle de journée nommé d'après un LIEU
  est un aimant à mauvais casting.** `galeries` est à vérifier pareil.
- **La tête « siège quitté » de Rhaenyra** reste SUSPENDUE. Vérifier l'inbox à
  la seconde où on l'applique, jamais à la seconde où on l'écrit. Et son
  `si_bloque` se borne à midi : *elle ne nomme personne, elle fait porter au
  registre que la case est restée en blanc et par la faute de qui.*
- **P06** (`CHAMPS_TETE_REQUIS` exige `echelle`, que la doctrine a supprimée) :
  toujours ouvert. **Aucune tête neuve ne passe la porte tant que ça tient.**

## Ce que je n'ouvre pas tant que midi n'est pas joué

Sombreval (le second témoignage tombe le 6e) · Jacaerys parti sur Vermax · dame
Sara et ses quatre-vingts dragons · la porte de mer, qu'elle a eue hors fiction
et sur laquelle elle n'a rien ordonné — **si ça doit lui revenir, ça revient par
Wend ou par ser Robert, pas par moi.**

## Mes dettes

- Trois sièges vacants, deux jours de retard. Personne n'en répond.
- Quarante-six relations ouvertes, cinq fiches de ma main (mj-aurore vient
  d'être reprise). Prochaines : **steffon-darklyn, rulf-corne** — les deux plus
  chargées et toujours nues, et rulf a passé la journée d'aujourd'hui sur ma
  table sans que je lui écrive une ligne.
- P01 ouvert (paroles.json hors schéma à 42 %). P02 fermé, mais P08 est son
  jumeau par l'autre bout.
