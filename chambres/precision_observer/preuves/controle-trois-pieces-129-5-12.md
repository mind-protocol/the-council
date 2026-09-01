# Contrôle de cohérence des moyens

Verdict : **A_CONTROLER**

| Mesure | Mains | Registre | Statut |
|---|---:|---:|---|
| containers déclarés | 9 | 9 | ACCORD |
| modules rattachés | 433 | 431 | ECART |
| modules orphelins | 20 | 20 | ACCORD |
| liens hors porte | 115 | 115 | ACCORD |
| dépendances remontantes | 13 | 13 | ACCORD |
| commandes-bibliothèques | 0 | 0 | ACCORD |

Total modules : 453 calculés, 451 annoncés — **ECART**.
Dates : mains ['129.5.12'], registre 129.5.12 — **ACCORD**.

Limite : Cohérence documentaire seulement : ce contrôle ne prouve ni le fonctionnement du code ni la visibilité de ses sorties.

## Verdicts par paire

- `mains_registre` : **A_CONTROLER**
  - `containers-declares` : mains=9, registre=9 — ACCORD
  - `modules-rattaches` : mains=433, registre=431 — ECART
  - `modules-orphelins` : mains=20, registre=20 — ACCORD
  - `liens-hors-porte` : mains=115, registre=115 — ACCORD
  - `dependances-remontantes` : mains=13, registre=13 — ACCORD
  - `commandes-bibliotheques` : mains=0, registre=0 — ACCORD
  - `modules-observes` : mains=453, registre=451 — ECART
- `mains_sonde` : **A_CONTROLER**
  - `modules-rattaches` : mains=433, sonde=433 — ACCORD
  - `modules-orphelins` : mains=20, sonde=21 — ECART
  - `modules-observes` : mains=453, sonde=454 — ECART
- `registre_sonde` : **A_CONTROLER**
  - `modules-rattaches` : registre=431, sonde=433 — ECART
  - `modules-orphelins` : registre=20, sonde=21 — ECART
  - `modules-observes` : registre=451, sonde=454 — ECART

Provenance de la troisième pièce : Mesures communiquées par xadme à precision-observer, ref vmti2d01qxnti ; cette pièce n'est pas la sortie brute de la sonde.
