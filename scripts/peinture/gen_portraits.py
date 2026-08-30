# Génère les icônes de personnages via l'API Ideogram (v3).
# Usage : python scripts/peinture/gen_portraits.py [id ...]   (sans argument : tous les personnages)
# Sortie : portraits/<id>.png — les fichiers déjà présents sont sautés.
import json
import sys
import time
from pathlib import Path

import requests

RACINE = Path(__file__).resolve().parent.parent.parent
SORTIE = RACINE / "portraits"
ENDPOINT = "https://api.ideogram.ai/v1/ideogram-v3/generate"
STYLE = "GENERAL"

# Le bloc de style : chaud, clair-obscur, plein cadre. Ne PAS y remettre « on aged
# canvas » — avec, le modele peint une toile encadree posee sur un mur, marge grise
# comprise, et le medaillon se retrouve borde de noir.
STYLE_BLOCK = (
    "Painted character portrait in oils, dark fantasy medieval court, bust framing "
    "showing head and shoulders, three-quarter view, lit by warm candlelight from one "
    "side, dramatic chiaroscuro, muted regal color palette, visible fine brushwork, "
    "dignified and somber mood. "
)
SUFFIXE = (
    ", head and shoulders medallion portrait, centered composition, dark background,"
    " face weathered and true to the stated age, full bleed, subject fills the frame"
    " edge to edge, no canvas border, no picture frame, no text, no watermark,"
    " square format"
)


def cle_api():
    for ligne in (RACINE / ".env").read_text(encoding="utf-8").splitlines():
        if ligne.startswith("IDEOGRAM_API_KEY="):
            return ligne.split("=", 1)[1].strip()
    raise SystemExit("IDEOGRAM_API_KEY introuvable dans .env")


def generer(cle, perso):
    prompt = STYLE_BLOCK + perso["portrait"]["prompt_ideogram"] + SUFFIXE
    reponse = requests.post(
        ENDPOINT,
        headers={"Api-Key": cle},
        files={
            "prompt": (None, prompt),
            "aspect_ratio": (None, "1x1"),
            "rendering_speed": (None, "TURBO"),
            "style_type": (None, STYLE),
            "num_images": (None, "1"),
        },
        timeout=120,
    )
    reponse.raise_for_status()
    url = reponse.json()["data"][0]["url"]
    image = requests.get(url, timeout=120)
    image.raise_for_status()
    (SORTIE / f"{perso['id']}.png").write_bytes(image.content)


def main():
    cle = cle_api()
    SORTIE.mkdir(exist_ok=True)
    persos = json.loads((RACINE / "etat" / "personnages.json").read_text(encoding="utf-8"))
    voulus = set(sys.argv[1:])
    if voulus:
        persos = [p for p in persos if p["id"] in voulus]
    for perso in persos:
        cible = SORTIE / f"{perso['id']}.png"
        if cible.exists():
            print(f"saute {perso['id']} (existe)")
            continue
        try:
            generer(cle, perso)
            print(f"ok    {perso['id']}")
        except Exception as erreur:
            print(f"ECHEC {perso['id']} : {erreur}")
        time.sleep(1)


if __name__ == "__main__":
    main()
