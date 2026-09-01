# Contrôleur des moyens

Ce service confronte les mesures courantes de `mains.json` à la ligne M110 du
registre des moyens. Il contrôle six mesures, le total des modules et la date
du constat.

## Usage

Depuis n'importe quel dossier :

```powershell
python C:/Users/reyno/le-conseil2/chambres/precision_observer/outils/controle_moyens.py
```

Pour une sortie exploitable par un autre outil :

```powershell
python C:/Users/reyno/le-conseil2/chambres/precision_observer/outils/controle_moyens.py --format json
```

Pour conserver une preuve lisible :

```powershell
python C:/Users/reyno/le-conseil2/chambres/precision_observer/outils/controle_moyens.py --sortie C:/Users/reyno/le-conseil2/chambres/precision_observer/preuves/controle-coherence-moyens-129-5-12.md
```

Codes de sortie : `0` pour un accord complet, `1` pour une pièce à contrôler,
`2` pour une entrée illisible. Le verdict porte sur la cohérence documentaire,
jamais sur le fonctionnement du code.

Le banc d'essai se lance ainsi :

```powershell
python -m unittest C:/Users/reyno/le-conseil2/chambres/precision_observer/outils/test_controle_moyens.py
```

Pour éprouver le bordereau depuis le siège de `precision-observer` sans
écraser la pièce historique sans siège :

```powershell
node C:/Users/reyno/le-conseil2/chambres/precision_observer/outils/eprouver_reception.mjs --siege
```

Le navigateur télécharge d'abord dans un répertoire isolé. La pièce n'est
publiée sous `preuves/bordereau-reception-siege.json` qu'après comparaison avec
la pièce affichée ; une sortie déjà présente provoque un arrêt.

## Mode à trois pièces

L'option `--sonde` ajoute un constat normalisé et produit trois verdicts
distincts : `mains_registre`, `mains_sonde` et `registre_sonde`.

```powershell
python C:/Users/reyno/le-conseil2/chambres/precision_observer/outils/controle_moyens.py --sonde C:/Users/reyno/le-conseil2/chambres/precision_observer/preuves/constat-sonde-xadme-129-5-12.json
```

La troisième pièce doit porter le type `constat-sonde-architecture/1`, une
`provenance`, une `date_constat` et les mesures `modules-observes`,
`modules-rattaches`, `modules-orphelins`. Ce contrat normalisé n'est pas encore
un lecteur de la sortie JSON brute de M110 : son schéma reste à obtenir.
