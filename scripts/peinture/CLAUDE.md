# `peinture/` — ce qui coûte de l'argent réel

Images, voix, chansons : chaque script d'ici appelle une API payante (Ideogram,
ElevenLabs, Suno). **On y génère au strict besoin — ce que la scène courante
réclame, jamais tout le casting « pour avoir d'avance ».** C'est la seule
contrainte du dossier, et elle prime sur toute commodité.

Trois habitudes qui en découlent :
- **On saute ce qui existe déjà.** Les scripts le font par défaut ; `--refaire`
  est un geste délibéré, pas un réflexe.
- **On nomme sa cible.** `gen_salles.py roukerie` plutôt que `gen_salles.py`.
- **Jamais en boucle, jamais en arrière-plan sans regarder.** Une boucle qui
  redemande vingt portraits ne se remarque qu'à la facture.

| Script | Ce qu'il produit | Chez qui |
|---|---|---|
| `gen_portraits.py` | `portraits/<id>.png` | Ideogram v3 |
| `gen_salles.py` | `ecrans/salles/<salle>.jpg` — les ids de `plans.js` | Ideogram v3 |
| `gen_voix.py` | `voix/<id>-<n>.mp3` + `etat/voix.json` | ElevenLabs Voice Design v3 |
| `audition_voix.py` | `voix/audition.html` — écouter les variantes | rien, lecture seule |
| `generer_chanson.py` | l'audio d'une fiche de `musiques/` | Suno |
| `medaillons.py` | les médaillons du fil, depuis `ecrans/portraits/<id>.svg` | rien, local |

`medaillons.py` et `audition_voix.py` ne paient rien : ils assemblent ce qui a déjà
été peint. Ce sont les deux qu'on peut relancer sans y penser.

Le MJ **compose** une chanson (concept, paroles Suno, prompt musical) et la pose
avec `../composer.py`, qui reste à la racine parce qu'il se tape en scène.
`generer_chanson.py` ne vient qu'après, s'il faut l'audio.
