# L'étalon du four — ⚔️ 90110 et ⚔️ 91210

Toll Œil-Noir, l'eau. 129.4.3, à la Souche.

## Ce qu'on mesure ici, et ce qu'on ne mesure pas

Deux étalons, et ils ne servent pas la même affaire :

- **Les quatre comptes** (ordres déformés, déclencheurs tombés, initiatives,
  coureurs) — affaire *Migrer la bataille vers la stack*, état 90100. Ils disent
  que la nuit a du SENS.
- **La cadence** (secondes de machine par seconde de bataille) — affaire *Rendre
  les murs solides*, état 91200. Elle dit que la nuit reste JOUABLE.

Un chiffre sans sa condition n'est pas un étalon. **Les quatre ne valent qu'à
1700 hommes et 600 s** — c'est la condition de la référence du 14 août, et ce
ne sont PAS les défauts de `sac.js` (300 hommes, 1400 s). Sur `avant-400h`, à
400 hommes, les quatre valent 0, 0, 0 et 12 : aucun ordre ne se déforme, aucun
déclencheur ne tombe, aucune escouade ne prend d'initiative. On ne compare donc
jamais deux cuissons sans dire d'abord combien d'hommes et combien de secondes.

    python scripts/bataille.py --cuire --hommes 1700 --duree 600

## `deux-causes.js` — pourquoi ce banc existe

Le verrou 90110 dit que l'étalon confond deux causes : `git show 745c8eb` met
`PORTE_OUVERTE_ESSAI` à `false` ET branche `3-interpretation.js` et
`4-envie.js` dans la chaîne du four, en un seul anneau. Vérifié : les deux
couches sont bien dans `CHAINE` (`scripts/monde/sac.js` l.100–110), et le
drapeau est bien à `false` (`bataille2d.js` l.318). Les deux causes agissent
donc réellement sur la même cuisson, et l'étalon seul ne dira jamais laquelle a
bougé.

Ce banc monte la MÊME chaîne que le four, la fait tourner, et ne compte que les
faits — pas d'annales, pas de tranches, pas de relecture. Il ne touche à rien
dans `ecrans/` : il lit la source et la réécrit en mémoire, le temps du `eval`.
C'est de la mesure, pas de la taille — mon office s'arrête là.

    node analyse/etalon-90110/deux-causes.js --hommes=1700 --duree=600
    node analyse/etalon-90110/deux-causes.js --hommes=1700 --duree=150 --sans-couches
    node analyse/etalon-90110/deux-causes.js --hommes=1700 --duree=150 --porte-ouverte

Trois cuissons, trois variantes, un seul chiffre change à la fois : c'est la
seule façon de rendre à chaque cause ce qui lui revient.

## Le hasard, et le trou qui ne crie pas

`bataille/corps-adapt.js` l.350 : `H ? H.R() : Math.random()`. `H` est lié une
seule fois au chargement du module (l.194) sur `window.BatailleHasard`, que
`bataille/hasard.js` pose en premier dans la chaîne. Aujourd'hui `H` tient, et
le repli ne sert pas.

Mais **le repli est muet**. Le jour où une couche est chargée avant `hasard.js`,
ou qu'elle oublie la garde, la cuisson cesse d'être reproductible et RIEN ne le
dit : on lit des comptes, on les croit, ils ne veulent rien dire. C'est déjà
arrivé une fois — écart pire passé de 0,600 m à 329 m — et ça n'a été vu que
parce qu'un seuil est tombé.

`survival-stack/5-la-main.js` porte un `Math.random()`. Elle n'est pas dans la
chaîne du four aujourd'hui. Elle y sera le jour où l'arbitre (⚔️ 90311) se
branche.

Ce que ça demande, et c'est de mon office : que `sac.js` refuse de cuire quand
la graine n'est pas tenue, et qu'il dise la graine en tête de cuisson.

## Un orphelin sur la machine, le 3e au soir

La cuisson coupée hier n'est pas morte avec la séance : `node` 14520, démarré à
22h47, tournait encore à 23h30 avec 31 minutes de machine mangées. Toute mesure
de cadence prise pendant ce temps-là est fausse et l'est vers le haut. Tué à la
main avant de mesurer. **Une cadence se mesure sur une machine dont on a
regardé la charge d'abord** — sinon on grave le bruit.
