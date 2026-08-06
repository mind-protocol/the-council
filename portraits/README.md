# Portraits — Le Conseil

1. Ouvrir Ideogram, choisir le ratio **1:1** et le style **Realistic**.
2. Ouvrir `PROMPTS_IDEOGRAM.md`, copier le **STYLE BLOCK**, puis coller à la suite le prompt du personnage voulu.
3. Générer, choisir la meilleure image, la télécharger.
4. Renommer le fichier en `<id>.png` (id kebab-case, ex. `aemond-targaryen.png`).
5. Déposer le fichier dans `portraits/` (à côté de ce README) : chemin final `portraits/<id>.png`.
6. Pour un personnage joueur créé en partie, utiliser le template « Maison du joueur » en fin de `PROMPTS_IDEOGRAM.md`.

**Fallback** : tant que `portraits/<id>.png` n'existe pas, l'écran de scène affiche le médaillon placeholder `portraits/svg/<id>.svg` (240×240, couleurs de la maison, monogramme). Ne pas supprimer ces SVG : ils restent le fallback si un PNG manque.
