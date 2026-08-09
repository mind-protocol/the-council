# Les plans d'en face — `etat/plans.json`

Le plan d'une maison qui n'est pas la nôtre. **Format et doctrine ici** ; `docs/schema.md` porte la ligne de format et ne se modifie qu'avec l'autorisation expresse du joueur.

## Pourquoi cette table existe

Le camp vert n'existait nulle part. Il existait comme **la somme de treize têtes** — Aegon qui veut paraître roi, Otto qui veut payer des têtes plutôt que des osts, Ormund qui ne marchera pas avant d'être nourri — et rien ne disait ce que ces treize hommes poursuivent **ensemble**, ni ce qui les en empêche.

C'est cohérent avec la doctrine : on joue des gens, pas des factions. Mais la conséquence est qu'il n'y avait **aucun objet à calculer côté ennemi**. Nos 47 cahiers portaient 575 actions ; en face, zéro. Le joueur affrontait une brume.

## Le miroir porte sur la FORME, jamais sur la densité

C'est la règle qui commande tout le reste. Nous avons 575 actions, Hightower en a 10. Un miroir symétrique en volume doublerait le coût du monde à chaque maison et donnerait à l'ennemi une omniscience que rien ne lui a payée.

**Ce qui se reflète, c'est la grammaire des pièces — pas leur nombre.**

Et la dissymétrie doit être **écrite**, pas corrigée : Ormund lève six mille hommes sur une lettre de famille pendant que nous savons depuis douze jours que la guerre est ouverte. C'est ça, l'intérêt. Pas l'équilibre.

## Trois miroirs, pas un

| miroir | ce qu'il relie | ce qu'il produit |
|---|---|---|
| **de plan** | un état cible d'un côté ↔ un verrou de l'autre | leur but est notre empêchement, et réciproquement |
| **de connaissance** | un fait ↔ ce qu'on en croit | le brouillard : chaque pièce d'en face a une route pour nous parvenir |
| **d'effort** | un verrou ↔ une activité | ce qui gêne quelqu'un lui donne quelque chose à aller chercher |

Le troisième est celui qu'on cherchait : **il n'y a plus de sujets d'activité à inventer**, ils tombent du deuxième miroir appliqué au premier.

## Les quatre portées — le champ qui trie

Chaque verrou d'en face, vu de chez nous, tombe dans **exactement une** case. `portee_pour_nous` n'a pas de cinquième valeur.

1. **on peut le savoir** → une **activité**, dont le type et le sujet sortent de la formulation du verrou
2. **on peut agir dessus** → une **action** à ouvrir chez nous, avec sa clef et son prix
3. **seule la parole du souverain** → une **décision** : ça monte à la table, ça ne se délègue pas
4. **hors de portée** → **rien**, et l'écrire vaut mieux que le taire — ça évite d'y revenir tous les trois jours

Sur les six verrous de Hightower : trois en (1), un en (2), un en (3), un en (4). **Le tri est fait par le verrou lui-même, pas par le jugement du MJ.**

## Tout verrou naît avec sa route

Un verrou d'en face **sans route de fuite est un mur invisible** : il bloque, et le joueur ne saura jamais pourquoi. La route se planifie à l'écriture du verrou, pas après — par quel canal, par quelle bouche, en combien de jours, et déformé comment.

C'est la même règle que partout ailleurs : **une pièce d'en face ne devient une croyance chez nous que par une `diffusion` arrivée à échéance.** Sans elle, on aurait fabriqué une carte que le joueur lit par-dessus l'épaule du MJ.

`python scripts/evaluer.py --murs` compte les verrous sans portée.

## Ce qu'on n'invente pas

Le même partage que `docs/travaux.md`, et pour la même raison :

1. **Invente largement la matière** — les gens, les prix, les rancunes.
2. **N'invente pas le verdict** — ce que la source pouvait rendre.
3. **Toute pièce porte sa `source`.** Une pièce sans source a été inventée et non dérivée. C'est le seul contrôle qui rende ce fichier honnête.

Le bootstrap de Hightower en donne la preuve par l'exemple : chaque état cible, chaque verrou, chaque action cite la tête ou le canon d'où elle sort. L'action **71026** — *arrêter la dépense pour les trois* — est sortie **sans titulaire**, parce qu'aucune des cinq têtes ne la porte. C'est un résultat, pas un oubli.

## Où ça vit, et pourquoi pas dans les livres

`books.json` est **lisible par le joueur**. Un plan adverse n'y a pas sa place. `plans.json` n'est servi par aucune route du serveur.

Et le format est en **objet**, pas en tableaux de cellules : on calcule dessus. Le cahier n'en serait qu'une vue possible. Plages de numéros réservées : **70000-79999** pour ce qui n'est pas à nous.

## Ce que le canon donne gratuitement

Les événements `canon` à venir **sont déjà les états cibles datés du camp d'en face**, et leurs `conditions` de déviation en sont les verrous, déjà rédigés. Huit canons devant nous, **dix-neuf conditions** — du 129.4.2 au 130.5.1 :

> *[6.1]* **retardé tant que Criston n'a pas arraché à Otto l'or de l'ost**
> *[1.10]* **si le blocus du Gosier a été levé ou renforcé autrement**
> *[6.1]* **aggravé si la reine ne rend pas les quarante prisonniers verts**

On ne part donc jamais de rien.

## La taille

Un plan adverse n'a pas besoin de 575 actions. Hightower en a **10**, pour 4 états cibles, 6 verrous, 5 clefs et 2 tensions. Trente à quarante actions couvriraient les trois camps qui comptent. **Le coût est dans l'inférence, pas dans le volume.**

La borne, et c'est celle des mains : **on n'écrit une pièce d'en face que si elle produit quelque chose de ce côté-ci.** Un verrou de portée 4 qu'on n'écrirait pas ne manquerait à personne. Test avant d'écrire : *par quelle bouche, ou par quel empêchement, ça atteindra le joueur ?*

## La preuve que la boucle tourne

Sur Hightower seul, les six verrous ont engendré **quatre sujets chez nous**, aucun tiré d'une liste :

- **observer** — la date où la sommation d'Otto atteint Villevieille *(71002 : chaque jour d'ignorance d'Ormund est un jour gagné)*
- **interroger** — ce que la bourse d'Otto a déjà payé, et sur quel gage *(71004)*
- **éprouver** — ce qu'un dragon montré au sud fait à Daeron *(71003 : le seul verrou sur lequel le joueur agit sans perdre un homme)*
- **décision** — écrire à Ormund nommément, ou s'en abstenir *(71006 : son déclencheur est armé exactement là-dessus)*

## Ce qui reste ouvert

- **`equilibre` et `contredit` n'ont pas de domicile.** Les tensions sont écrites dans le plan, mais pas comme des arêtes : on ne peut pas encore demander « qu'est-ce qui contredit ceci ? » à travers les deux camps.
- **La route de fuite n'est pas un champ obligatoire.** Elle devrait l'être, au même rang que `bloque`, et `tick.py --verifier` devrait la réclamer.
- **Un seul plan existe.** Hightower. Les faux neutres — Rosby et Stokeworth, qui s'affichent neutres et sont verts — sont les suivants les plus rentables : ils sont à portée de main du joueur.
