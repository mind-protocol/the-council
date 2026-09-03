# 🧠 Brains / Oiseau

## Intention

Le ciel au-dessus de la bataille, et rien d'autre. Un corbeau suit l'armée ; un rapace de chasse se poste et fond. Ni l'un ni l'autre n'entre dans le combat : **il n'existe aucun état où un oiseau frappe**, et c'est une propriété, pas un oubli.

Ce brain a remplacé celui du dragon le 1er septembre 2026. Le SYSTÈME DE VOL est le même — c'est lui qu'on voulait garder : l'actuateur (`🏃 steering/vol.js`), le `z` sur le corps (`🌍 registre`), les distances 3D de la perception, l'altitude dans le snapshot. Ce qui est parti avec le dragon, c'est le FEU : `actes/souffler.js`, `monde/chaleur.js`, la brûlure du ❤️, les paramètres thermiques, le cône-sol.

## La machine

UNE machine pour les deux bêtes (`machine.js`, en donnée comme celle du soldat) :

```
poste → descend → passe → remonte → poste
```

- **poste** — le cercle au-dessus de ce qu'elle guette (rayon `16 + 0,26 × la hauteur du poste`), ou la courbe vers le point d'entrée quand une masse est crue en bas.
- **descend** — le cap se FIGE à l'entrée (le verrou : jamais de tourelle), la hauteur devient vitesse.
- **passe** — le vol rasant. C'est ici que les deux bêtes divergent le plus : deux secondes pour le rapace, vingt pour le corbeau.
- **remonte** — hauteur et champ repris, les verrous se lèvent.

**Ce qui sépare les deux bêtes n'est PAS le graphe, ce sont les chiffres du profil** (`❤️ corps/oiseaux.js`). C'est le test de falsifiabilité : si le corbeau n'est qu'un faucon ralenti à l'écran, le profil n'est pas propagé. Mesuré à la fumée (cas `deux-betes`) : le faucon se poste à 185 m et pointe à 37 m/s, le corbeau à 65 m et 17 m/s, et le corbeau traîne 134 s en passe basse contre 15.

## Deux pièges, payés une fois

- **`approcheDist` doit valoir le rayon du cercle.** C'est en TOURNANT que la bête se présente à son entrée ; elle ne va pas chercher un point d'approche ailleurs. Hérités du dragon (150 m pour un cercle de 64), les deux étaient découplés et les oiseaux tournaient éternellement sans jamais se décider — zéro seconde en passe, sur quatre cents.
- **L'accélération appartient à la bête** (`accelPique`, `accelMax`). Le plafond commun de 2,2 m/s² bridait le fond du rapace à trente mètres par seconde, quelle que soit sa hauteur : un piqué est tiré par la pesanteur, pas poussé par les ailes.

## Frontières

Les mêmes que tout brain : lecture de la seule Représentation (la masse CRUE en bas, jamais le registre), sortie en Intentions (`voler` seulement), `introspect()` obligatoire. Le profil est un SAVOIR SUR SOI, injecté au bootstrap comme l'arme du soldat.

## Ce qui n'est pas fait

- **Le corbeau ne voit pas les morts.** Il devrait tourner sur les cadavres — c'est son métier. La Représentation compte les morts vus (`mortsVus()`) mais ne garde pas leurs POSITIONS : les gisants n'entrent dans la perception que comme `{id, livree}`. Leur donner un lieu daté est la brique qui manque ; d'ici là il guette la masse vivante, ce qui est vrai aussi.
- Pas de cavalier, pas de fauconnier : l'oiseau du rapace de chasse vole seul. Le poing qui le lance et le rappelle n'existe pas.
