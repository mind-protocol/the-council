# -*- coding: utf-8 -*-
# Ygga Main-de-Pierre, 3e jour de la 4e lune, an 129.
# Grave l'etat de l'action 90311 dans chantier/affaires.json, et pose le
# verrou 90370 dans LES DEUX stocks. Adresses nues, jamais de signe devant
# un numero.
import io, json, os, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AFF = os.path.join(RACINE, "chantier", "affaires.json")
BOOKS = os.path.join(RACINE, "etat", "books.json")
ID = "affaire-migrer-la-bataille-vers-la-stack"

ETAT_90311 = (
    u"fait — `survival-stack/5-la-main.js`, 353 lignes, chargé par "
    u"`jeu.html` en observation ; banc `banc-la-main.js`, **11 cas, tous "
    u"tenus**. Tranche la contradiction que le README refusait de nommer : "
    u"**la somme n'est pas constructible** — la couche 1 rend un MOT, la 2 "
    u"des nombres et un cap, la 3 des modulations, la 4 des durées ; on "
    u"n'additionne pas « fuite » et 0,42. **Et le vainqueur unique est "
    u"faux aussi** : `ballants` retire les bras sans prendre l'homme. D'où la "
    u"forme — arbitrage **par emplacement** (jambes, bras), chaque couche "
    u"posant une **prétention** dans [0, 1] composée de ses propres nombres, "
    u"la plus forte prend. **L'ordre n'est pas un prétendant, c'est le sol** : "
    u"`barre(l3)` = `lettre` relu sur [0, 1], donc 0,50 pour l'homme "
    u"ordinaire, et l'appelant retombe dans la cascade quand personne ne la "
    u"franchit — c'est ce qui rend 90312 progressif. **Aucun tirage** : le "
    u"départage se fait par comparaison et par période réfractaire "
    u"`exigence(tenu)`, dont la constante de temps est prise dans `M.SEJOUR` "
    u"(0,20 s, la dérobade) et non inventée. Le Bassin a pris **6 cas sur "
    u"11** au premier passage : `depuis` initialisé à `t` faisait croire à "
    u"chaque homme que son ordre venait de prendre la main, donc `exigence(0)` "
    u"à 1,00, donc barre + 1 — infranchissable, tout homme obéissait la nuit "
    u"entière. Corrigé en `-Infinity` : un homme qui entre en scène obéit "
    u"depuis toujours, il n'a pas de geste à protéger. Second défaut trouvé "
    u"à la relecture et qu'aucun de mes cas ne montrait : le tenant était pesé "
    u"DANS la boucle, donc le résultat dépendait de l'ordre des clefs d'un "
    u"objet. Sorti de la boucle. Gravé au passage : `h.l1.pilote` → "
    u"`h.l1.corpsAgi` et `corpsPilote` → `corpsAgi` — le nom posé par Wenna "
    u"(90320), la main du Fer, `bataille2d.js` et `carte-ville.js`."
)

VERROU = [
    u"**90370**",
    u"**Rien n'appelle `2-reflexion.js`** — la couche est chargée, l'arbitre "
    u"l'attend, et personne ne la fait tourner",
    u"90300",
    u"Compté sur le disque le 3e, en branchant `5-la-main.js` : "
    u"`grep -rn \"Reflexion\" ecrans/ scripts/ serveur/` hors du module lui-même "
    u"rend **zéro occurrence**, et `h.l2` **n'existe nulle part** dans les "
    u"6 957 lignes de `bataille2d.js`. Les trois autres couches ont leur "
    u"pourvoyeur : la 1 a `bataille/corps-adapt.js`, **372 lignes** qui lui "
    u"bâtissent angles, voisins, stimuli et l'horloge de l'œil ; les 3 et 4 "
    u"sont nourries en ligne dans `soldat()` (3406, 4507, 1431, 3576, 4481). "
    u"**La 2 n'a rien.** Conséquence mesurable et non supposée : "
    u"`prendReflexion(undefined)` rend 0, donc la couche ne prétend jamais à "
    u"rien, donc l'arbitre branché demain conduirait **exactement ce que la "
    u"cascade conduit déjà** — on aurait un cinquième fichier, un banc vert, "
    u"et pas un homme qui se conduise autrement. Le verrou 90350 (`degage` "
    u"absent) en est un cas particulier : il manque UN signal ; ici il manque "
    u"le pourvoyeur entier. Se lèverait par un `bataille/reflexion-adapt.js`, "
    u"jumeau de `corps-adapt.js`, qui bâtit `degage`, `versLuiX/Y`, "
    u"`versEuxX/Y`, `alarme`, `trempe` et `epaule` depuis `h`, et pose `h.l2`.",
]

def charge(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)

def sauve(p, d):
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write(u"\n")

def affaire(d):
    lst = d["affaires"] if isinstance(d, dict) else d
    for a in lst:
        if a.get("id") == ID:
            return a
    raise SystemExit("affaire introuvable")

def table(a, bout):
    for t in a["tables"]:
        if bout in t["titre"]:
            return t
    raise SystemExit("table introuvable : " + bout)

rapport = []

# --- 1. l'etat de l'action 90311, dans chantier/affaires.json --------------
d = charge(AFF)
a = affaire(d)
t = table(a, u"Actions")
assert t["colonnes"][5] == u"✅ État", t["colonnes"]
pose = False
for l in t["lignes"]:
    if l["cellules"][0] == u"**90311**":
        l["cellules"][5] = ETAT_90311
        pose = True
if not pose:
    raise SystemExit("ligne 90311 introuvable")
rapport.append(u"chantier/affaires.json · Actions · 90311 · ✅ État")

# --- 2. le verrou 90370, dans les DEUX stocks ------------------------------
for chemin in (AFF, BOOKS):
    dd = d if chemin == AFF else charge(chemin)
    aa = affaire(dd)
    tv = table(aa, u"Verrous")
    pris = [l["cellules"][0] for l in tv["lignes"]]
    if u"**90370**" in pris:
        rapport.append(u"%s : 90370 deja pose, rien fait" % chemin)
        continue
    assert len(tv["colonnes"]) == len(VERROU), (tv["colonnes"], len(VERROU))
    tv["lignes"].append({"cellules": list(VERROU)})
    rapport.append(u"%s · Verrous · 90370 pose (numeros presents : %s)"
                   % (os.path.basename(chemin), u", ".join(pris)))
    if chemin != AFF:
        sauve(chemin, dd)

sauve(AFF, d)

out = io.open(1, "w", encoding="utf-8", closefd=False)
for r in rapport:
    out.write(r + u"\n")
out.flush()
