# Porteur

## 1. Ce que c'est

L'homme qui porte un message et qui doit **retrouver un destinataire mobile** —
pas se rendre à une coordonnée.

## 2. Ce qu'il possède

- **La course d'un porteur** : qui il est, ce qu'il porte, à qui il va, ce qu'il
  croit savoir du destinataire, et où il en est.
- **Sa dernière information sur le destinataire** : un lieu, une date, une
  source, une confiance. C'est une croyance, elle peut être fausse, et il n'a
  aucun moyen de le savoir avant d'arriver.
- **Sa conduite quand l'information se révèle fausse**, qui est le cœur du
  module. Ne trouvant pas son homme là où il le croyait, il choisit entre :
  **demander** à qui se trouve là, **chercher un signe** (bannière, formation,
  bruit reconnaissable), **suivre une piste** qu'on lui indique, ou **revenir**
  avec l'échec. Il ne se téléporte pas vers la position réelle.
- **Son état** : parti, en recherche, arrivé, revenu, perdu, mort.
- **Ce qu'il a vu en route**, renseignement à part entière, qui voyage avec lui
  qu'on le lui ait demandé ou non.

## 3. Ce qu'il lit

Du socle : identité, horloge, urne. Du monde : le terrain et la navigation, pour
que sa course prenne le temps qu'elle prend ; la collision, parce qu'un porteur
meurt comme un autre homme. De la perception : ce qu'il voit en chemin, à sa
portée à lui. Du combattant : c'est un homme, avec sa fatigue, sa monture
éventuelle, sa mémoire. De l'unité : les signes reconnaissables d'un groupe et
l'identité de son chef.

Il ne lit **jamais** la position réelle de son destinataire. Il lit son
information sur elle. C'est la même règle que pour un chef, appliquée à un homme
qui court.

## 4. Ce qu'il produit

- **Une course en cours**, avec sa position et son état.
- **Une remise**, quand il a trouvé son homme et s'en est fait comprendre.
- **Un échec qualifié** : introuvable, arrivé trop tard, intercepté, mort en
  chemin — le message reste non remis, avec sa cause.
- **Ce qu'il rapporte de la route**, s'il revient.

## 5. Invariants

- **Un porteur mort emporte son message.** Le contenu ne parvient à personne, et
  l'émetteur ne l'apprend que par un autre canal ou par le silence.
- Aucune remise à distance : les deux hommes doivent s'être trouvés à portée de
  voix.
- Le temps d'une course est celui du terrain parcouru, jamais un forfait.
- Une sonde extérieure vérifie qu'aucune course ne se termine sans que le porteur
  ait matériellement atteint son destinataire.
- Le nombre de ses recherches est borné : au-delà, il revient ou renonce.

## 6. Ce qu'il ne fait pas

- **Il ne sait pas où est vraiment son destinataire.** La violer une fois vide
  la transmission de son sens.
- **Il ne se déplace pas lui-même** : il produit une intention de geste et le
  monde décide. Un porteur peut être bloqué par la foule.
- **Il ne comprend pas le contenu**, sauf ce qu'il a besoin d'en répéter, et
  n'accélère pas parce que c'est grave.
- **Il ne décide pas à la place de l'émetteur.** S'il ne trouve personne, il ne
  remet pas l'ordre à un autre chef de son propre chef.
- **Il ne raconte pas.** Ce qu'il a vu en route est un fait daté.

## 7. Ce que l'ancien moteur faisait mal ici

**Ce point n'a pas été mesuré.** L'ancien moteur comptait bien le trafic — 478
communications entre chefs sur une bataille — mais rien n'a été relevé sur les
porteurs eux-mêmes : ni durée de course, ni échec de remise, ni mort en chemin,
ni recherche d'un destinataire déplacé. Les statuts que ce module décrit
n'existaient pas, donc aucun chiffre ne les concerne.

Ce qu'on peut dire sans inventer : puisque **zéro ordre sur quinze chefs** n'a
été adapté à un renseignement, la fiabilité de la remise n'a jamais pu être mise
en cause — un tuyau parfait et un tuyau bouché donnaient le même résultat en
aval. La première mesure à poser ici est élémentaire et n'a jamais été faite :
**quelle part des messages confiés est remise, et en combien de temps.**
