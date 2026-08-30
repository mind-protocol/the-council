# Ce qui parvient aux joueurs

**La règle est déjà écrite ailleurs et elle vaut ici sans un mot de plus :**
avant de narrer un fait, ont-ils une source pour le savoir ? Un fait de la nuit
n'arrive au joueur que si l'un de ses sièges était à portée, **à cette minute-là**.

← [le dossier](README.md) · [le narratif](narratif.md)

Le tuyau existe : c'est **la balade**. Elle produit un pas tous les vingt
mètres, daté et situé ; le sac produit des centaines de faits datés et situés.
`serveur/croiser.js` ne fait que joindre les deux, par une fonction pure de
(où, quand) — comme `journee.js` répond `ou(corps, minute)`.

---

## Trois portées, parce qu'un homme n'a pas qu'un sens

| | quoi | ce qu'on en dit |
|---|---|---|
| **vu** | c'est en train d'arriver, et c'est dans la rue | tout : qui, quoi, à combien de pas |
| **entendu** | c'est en train d'arriver, loin | **rien** — un fracas et un quartier. C'est le seul canal qui tourne au coin d'une rue |
| **trace** | c'est déjà arrivé et ça a laissé quelque chose | ce qu'on trouve par terre, et **depuis combien de temps** |

La troisième est la bonne. Une porte défoncée reste défoncée ; un homme assis
contre un mur est encore là au matin, à une adresse, et il sait quel ordre il
avait reçu. **Ça ne s'entend pas, ça ne s'invente pas : ça se voit en passant.**

## Et une quatrième, qui n'existe que dans ce cadre : ce qu'on croit voir

Un homme qui voit mille sept cents hommes enfoncer la porte de la Gadoue **voit
la chute de la ville**. Il a raison sur ce qu'il voit et tort sur ce que c'est.

**Personne dans la rue, cette nuit-là, ne dispose de l'information qui rendrait
la scène compréhensible** — et c'est le seul moment du jeu où le brouillard ne
protège pas un secret : il dissimule une farce.

## La table EST le système

Un type de fait, trois nombres — portée à l'œil, portée à l'oreille, durée de la
trace. Rien d'autre. **Tout comportement qu'on ajoutera — un pillard, un porteur
d'ordre, un clerc à tablette — devient perceptible en écrivant SA LIGNE**, et la
balade n'a pas à être retouchée. C'est le seul endroit à toucher, et c'est
délibéré.

Les chiffres sont des mesures, pas des réglages : une porte bardée de fer qu'on
enfonce s'entend à sept cents mètres dans une ville de nuit ; un homme qui tombe
ne s'entend pas à quarante.

## Ce qui se lève arrête la marche

Le manuel le dit — « alors on arrête de marcher » — et ça ne pouvait pas rester
à la main du MJ : **quand le joueur traverse un assaut, ses jambes s'arrêtent à
l'instant où il le voit**, pas trois pas plus loin. Un fait `vu` de la liste
`ARRETENT` coupe la balade, ferme le sac, et la page cesse d'avancer.

## Pas de fichier, pas de bataille

`etat/bataille.json` dit QUAND le sac tombe dans la partie :

```json
{ "sac": "portreal", "debut": { "jour": 9, "minute": 1200 } }
```

Sans lui, `croiser.autour()` rend `null` au premier test et ne lit rien — le cas
normal. **Un exercice cuit n'est pas un exercice en cours tant qu'un MJ ne l'a
pas daté**, et c'est pour ça que l'ancre est dans `etat/` et non dans le monde
engendré.

Ce que ça donne, mesuré :

```
devant la porte, à la minute du contact
   vu      : porte-enfoncée à 0 pas | homme à terre à 5 pas | chef-tombe à 5 pas | contact
   arrêt   : oui
à 300 m, même minute
   entendu : porte-enfoncée (Le port et ses hangars)      ← le quartier, rien d'autre
devant la porte, une heure plus tard
   traces  : porte-enfoncée depuis 60 min | trois hommes assis à 5 et 10 pas, depuis 60 min
```
