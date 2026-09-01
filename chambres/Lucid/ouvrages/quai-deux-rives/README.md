# Comptoir d'escales du Quai des Deux Rives

Adresse : `comptoir_escales.py`  
Registre présent : `escales.json`

Le comptoir sépare trois faits :

1. `ANNONCEE` — un billet sourcé annonce le navire ;
2. `A_QUAI` — une preuve distincte établit l'accostage ;
3. `REPARTIE` — une nouvelle preuve établit le départ.

Une annonce n'est donc jamais transformée automatiquement en présence.

## Consulter

```powershell
python comptoir_escales.py consulter
python comptoir_escales.py consulter --json
```

## Annoncer

```powershell
python comptoir_escales.py annoncer `
  --date "129.5.12" `
  --navire "Nom réel" `
  --capitaine "Personne réelle" `
  --provenance "Lieu établi" `
  --cargaison "Cargaison établie" `
  --preuve "Billet, registre ou témoin nommé"
```

## Accoster puis repartir

```powershell
python comptoir_escales.py accoster --id escale-0001 --preuve "preuve distincte"
python comptoir_escales.py repartir --id escale-0001 --preuve "preuve distincte"
```

Le paramètre `--registre` permet d'éprouver le comptoir sur une copie sans
toucher au registre présent.
