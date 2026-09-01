# Arpentage des murs hérités

La création est volontairement partagée entre trois portes :

1. `index.html`, `style.css` et `app.js` servent à observer, remplir une fiche
   et télécharger sa pièce JSON sur place ;
2. `valider_fiche.py` contrôle la forme, les mesures, l'état et la preuve ;
3. la transformation matérielle du mur devra passer par la porte du monde,
   après choix du segment. Ce dossier ne la simule pas.

Validation d'une fiche :

```powershell
python C:/Users/reyno/le-conseil2/chambres/precision_observer/ouvrages/arpentage-heritage/valider_fiche.py <fiche.json>
```

Codes de sortie : `0` pour recevable, `1` pour non recevable, `2` pour erreur
de lecture.

Épreuves du validateur :

```powershell
python -m unittest C:/Users/reyno/le-conseil2/chambres/precision_observer/ouvrages/arpentage-heritage/test_valider_fiche.py
```
