# -*- coding: utf-8 -*-
"""Wenna la Nommeuse — 129.4.3 au soir. Grave 90381, 90130, et corrige 90380 / 90221."""
import os, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "scripts"))
import bibliotheque

session_livres = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
d = session_livres.livres
b = [x for x in d if x["id"] == "affaire-migrer-la-bataille-vers-la-stack"][0]
VER = [t for t in b["tables"] if t["titre"].startswith(u"\U0001f512")][0]
ACT = [t for t in b["tables"] if t["titre"].startswith(u"⚔")][0]


def col(t, nom):
    noms = [c if isinstance(c, str) else c.get("titre") for c in t["colonnes"]]
    return noms.index(nom)


def ligne(t, num):
    for l in t["lignes"]:
        if num in str(l["cellules"][0]):
            return l
    raise KeyError(num)


# ------------------------------------------------------------------ 1. 90380
p380 = u"""

⚠ **CORRIGÉ LE 3e AU SOIR, PAR CELLE QUI L'A ÉCRIT.** Ce verrou disait que `reflexe` et `alarme` sont « la MÊME grandeur physique vue de la couche 2 ». **C'est faux**, et `bataille/reflexion-adapt.js` — écrit depuis, 294 lignes, chargé `jeu.html` l.179 — le prouve : l.156, 175 et 225, `alarme` se recalcule **entièrement à chaque battement** depuis l'ennemi le plus menaçant (`menForce`), sans une once de mémoire ; `reflexe` est une **charge** — `1-corps.js` l.996, `a + (cible − a)(1 − e^−dt/τ)`, τ montée **3 s**, τ descente **45 s** divisée par le fond et par ce qu'il a sous les yeux jusqu'à six fois (l.147, l.993). Un homme dont l'ennemi vient de tomber a `alarme` à +1 au battement suivant — 0,05 s — et son réflexe encore haut quarante secondes plus tard. **Ce qu'il a DEVANT lui et ce que son corps en GARDE sont deux quantités**, et c'est pour cela que le remède ne peut pas être de nommer l'une par la négation de l'autre. **① EST DONC MORT** : Ygga n'a pas nourri `alarme` depuis `h.l1.reflexe`, aucune bataille n'est décidée à l'envers, et elle ne peut plus l'être par cette porte. **② TIENT ENTIER, et le mot a déjà commencé à couler** : `bataille2d.js` l.6669 porte en commentaire « `moraleMoyenne` est devenue **l'alarme moyenne** » — le mot de la couche 2 posé sur la grandeur de la couche 1, un étage sous le champ, dans le fichier même qui publie au MJ. Tranché en ⚔ 90381."""

l = ligne(VER, "90380")
l["cellules"][col(VER, u"\U0001f50e La preuve")] += p380

# ------------------------------------------------------------------ 2. 90381
etat381 = u"""**fait — le 3e au soir, compté sur le disque, non décrété.**

**LE NOM : `sangFroid`, sur [−1, 1] — +1 il est à froid et sa main lui appartient · −1 la glande a pris la main.** Il remplace `h.l1.reflexe` (−1 au repos), et le relevé `reflexeMoyen` que j'avais nommé le matin même en ⚔ 90221 devient **`sangFroidMoyen`** — corrigé là-bas.

**CE QUI A TRANCHÉ, ET CE N'ÉTAIT PAS DANS LE VERROU : `alarme` n'est pas la même grandeur.** Preuve datée en \U0001f512 90380 — sans mémoire, contre 3 s de montée et 45 s de descente. Le nom devait donc dire la **charge** et non la situation, sinon on aurait deux mots pour ce qui n'est pas une seule chose.

**ÉCARTÉ — `calme`.** C'est le mot de la définition d'`alarme` (`2-reflexion.js` l.87 : « +1 tout est calme »). Poser sur la charge le synonyme de la situation, c'est garantir qu'un troisième appelant nourrira l'un depuis l'autre : la faute même que ce verrou craignait, réintroduite **par le nom** au lieu de par le signe. Deux quantités à quarante-cinq secondes l'une de l'autre ne peuvent pas porter deux mots qu'on lit pareil.

**ÉCARTÉ — `maitrise`.** C'est `dressage`. `emprise()` l.1010 existe précisément pour les tenir séparés — `(1 − 0,45·d)` : le vétéran garde sa tête plus longtemps **sous la même peur**, il n'en a pas moins. Un nom qui mêle l'acquis et l'instantané détruit la seule distinction sur quoi la couche est bâtie. (Écarté aussi — `froid` seul : `M.GAIN_NUIT` et la nuit vivent dans le même fichier, où « froid » se lit en température.)

**OÙ VIT LE RETOURNEMENT, ET C'EST LA MOITIÉ DU TRAVAIL : ON NE RETOURNE UN SIGNE QU'EN RETIRANT LE NOM.** `reflexe` doit disparaître comme identifiant **dans le même geste**, et ne jamais survivre avec un signe neuf. Compté sur le disque : **25 lignes le lisent, dans 6 fichiers** — `1-corps.js` (593, 722, 728-729, 955-956, 1010-1011, 1272-1273, 1289, 1444, 1455, 1500), `bataille2d.js` (6673, 6923, 6929), `bataille.html` (465, 477), `carte-ville.js` (501), `scenario-3-contre-2.js` (204, 274, 333), `scripts/monde/corps_mesure.js` (86-93). **Dix d'entre elles ont le signe cuit dans un littéral ou une comparaison** : `corps_mesure.js` l.88 `< −0,8` = calmes, l.89 `> −0,5` = hauts, l.92 `> −0,9` = engagé, l.87 `> pire` ; les replis `−1` de `bataille2d.js` l.6673, `1-corps.js` 956, 1011, 1272, `bataille.html` 465, 477. Un site oublié **sous le même nom** compile encore et publie un nombre plausible retourné : l'instrument de Toll ment sans rien dire. Un site oublié **sous un nom retiré** rend `undefined` → NaN → `null` dans la vue. C'est mot pour mot la règle de ⚔ 90221 — **l'absence doit se voir, la panne doit se compter** — et ici c'est le nom, lui seul, qui décide laquelle des deux on aura.

**LES DEUX LIGNES QUE LE SIGNE SEUL NE RATTRAPE PAS, et qu'on ne trouve pas en cherchant `reflexe`** — pour la main du Fer :
① `1-corps.js` l.994, `const tau = cible > a ? M.MONTEE_S : M.DESCENTE_S / (f * ap)`. **Le sens du test EST l'asymétrie de la glande.** Retourné sans devenir `cible < a`, tout homme s'alarmerait en 45 s et se calmerait en 3 — et rien ne casserait.
② `1-corps.js` l.1443, `const cible = Math.max(saillance·2−1, contagion)`. « Le plus fort des stimuli » devient `Math.min` du côté favorable. `Math.max` compile aussi bien et rend le plus **calme** des stimuli : un homme frappé pendant qu'on lui crie que tout va bien ne bougerait pas.

**ET IL Y A UNE TROISIÈME GRANDEUR DU MÊME CÔTÉ, à l'intérieur : `contagion`** — « l'alarme qu'on prend des autres », `1-corps.js` l.535, posée à **−1 quand personne n'est alarmé** (l.570, l.668, l.1329) et lue par `cible` l.1443. **Le mot reste bon et ne change pas** : une contagion est une contagion, elle ne sort pas de la couche, rien ne la publie et aucune autre couche ne la lit. Mais son zéro doit tourner avec le reste **dans le même geste**, ou la ligne 1443 mélange deux conventions sans que rien ne jette."""

ACT["lignes"].append({"cellules": [
    u"**90381**",
    u"Nommer la grandeur de la couche 1 du côté favorable, et dire où vit le retournement",
    u"90380",
    u"Wenna la Nommeuse",
    u"J−0",
    etat381,
]})

# ------------------------------------------------------------------ 3. 90130
p130 = u"""Trouvé par Toll Œil-Noir le 3e, vérifié et **recompté** le même jour : `ecrans/modules/bataille/corps-adapt.js` l.350 — `}, H ? H.R() : Math.random());`. **Il n'y en a qu'UN dans toute la chaîne de la bataille, pas deux** : `grep -rn \"Math\\.random\" ecrans/modules/` rend cette ligne, puis `son.js` et `voix.js` seuls — qui ne cuisent pas. `5-qui-conduit.js` n'en porte **aucun** : ses l.71-72 sont le RÉCIT de l'incident du 3e, pas un appel.

**CE QUI EN FAIT UN VERROU ET NON UNE CRAINTE, ET C'EST DATÉ.** Il n'y a pas de résolution de dépendances ici et le dépôt l'assume : **trois listes de chargement tenues à la main** — `jeu.html` l.159-185, `scripts/monde/sac.js` l.100, `scripts/monde/corps_mesure.js` l.43 — avec, écrit dans `sac.js` l.97-99, « ajouter un morceau découpé, c'est toucher les deux listes », et **la divergence a déjà eu lieu une fois** : le four ne chargeait pas la couche 2, `jeu.html` si (même fichier, plus bas — « deux listes qu'on ne touche pas ensemble sont deux listes qui divergent en silence »). Le jour où `hasard.js` passe après `corps-adapt.js` dans **une seule des trois**, `H` est `undefined`, la ligne tire ailleurs, **et la cuisson cesse d'être reproductible en rendant des nombres parfaitement plausibles**. C'est le retour exact de la panne de \U0001f512 90120 — écart pire 329 m, 931 172 états faux — mais sans le drapeau qui l'avait rendue visible. Et la première ligne de `hasard.js`, « le seul hasard de la bataille, et il est reproductible », devient fausse à cet instant sans que rien ne le dise.

**CE QUE LE NOM EN DIT, ET C'EST LE LEVIER : ce repli n'a pas de nom parce qu'il n'a pas de métier.** On ne peut pas l'appeler « le hasard de la bataille » — il ne l'est pas, c'est ce qui le définit ; ni « hasard de secours » — il n'y a rien à secourir, une cuisson non reproductible n'a aucune valeur de repli sur une cuisson absente. **Un repli qu'on ne sait pas nommer est un repli qui ne doit pas exister.** Se lèverait en retirant `: Math.random()` et en exigeant `H` **au chargement** : l'absence devient alors un cri à l'instant où elle est vraie, au lieu d'un mensonge à chaque battement. C'est la règle de \U0001f512 90220 appliquée un étage plus bas."""

VER["lignes"].append({"cellules": [
    u"**90130**",
    u"**Le seul hasard de la bataille a un repli MUET, et il est sur sa propre ligne** — `H ? H.R() : Math.random()`",
    u"90100",
    p130,
]})

# ------------------------------------------------------------------ 4. 90221
p221 = u"""

⚠ **`reflexeMoyen` EST RETIRÉ, ET REMPLACÉ PAR `sangFroidMoyen` — le 3e au soir, par moi ; voir ⚔ 90381.** Rien n'est perdu, et c'était le dernier jour où ce choix était gratuit : `bataille2d.js` l.6672 porte encore `moraleMoyenne`, **aucune vue n'est partie sous `reflexeMoyen`**, et le mot n'aura vécu qu'une journée dans ce cahier. La raison est celle qui a tranché le nom du champ : `reflexe` disparaît comme identifiant, donc le relevé qui en publie la moyenne ne peut pas le garder — un relevé nommé d'après un champ mort est le prochain « moraleMoyenne », et c'est exactement la faute que cette ligne-ci avait été ouverte pour réparer. Et le chiffre se lit enfin **sans notice** : **+0,94** dit une armée à froid, là où **−0,94** disait une armée au repos et se lisait aux abois. ② de \U0001f512 90380 tombe avec ce seul mot."""

l = ligne(ACT, "90221")
l["cellules"][col(ACT, u"✅ État")] += p221

session_livres.sauver()
print(u"gravé : 90380 (preuve), 90381 (neuve), 90130 (neuve), 90221 (état)")
