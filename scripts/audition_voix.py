# Construit voix/audition.html : une page locale pour écouter les voix conçues,
# extrait par extrait, avec la réplique d'audition et le portrait du personnage.
# Usage : python scripts/audition_voix.py
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "voix" / "audition.html"

from gen_voix import VOIX  # noqa: E402  (fiches vocales : description + réplique)

GABARIT = """<!doctype html>
<meta charset="utf-8">
<title>Le Conseil — auditions</title>
<style>
 body {{ background:#0d0c0f; color:#d8d2c8; font:15px/1.5 Georgia,serif; margin:0; padding:2rem 3rem; }}
 h1 {{ font-weight:400; letter-spacing:.08em; color:#c9a961; margin:0 0 2rem; }}
 .fiche {{ display:flex; gap:1.5rem; padding:1.2rem 0; border-top:1px solid #241f28; }}
 img {{ width:96px; height:96px; border-radius:50%; object-fit:cover; background:#1a171d; flex:none; }}
 .corps {{ flex:1; min-width:0; }}
 .nom {{ color:#e8e0d4; font-size:1.1rem; }}
 .desc {{ color:#6f6a78; font-size:.82rem; font-family:system-ui,sans-serif; margin:.35rem 0 .6rem; }}
 .replique {{ color:#a99fb0; font-style:italic; margin-bottom:.7rem; }}
 audio {{ height:32px; vertical-align:middle; width:270px; }}
 .id {{ color:#4a4552; font-family:monospace; font-size:.75rem; }}
 .variante {{ display:inline-block; margin:0 .8rem .4rem 0; }}
 .variante b {{ display:block; font-size:.72rem; font-weight:400; color:#6f6a78;
   font-family:system-ui,sans-serif; letter-spacing:.05em; }}
 .variante.retenue b {{ color:#c9a961; }}
 .attente {{ color:#c9a961; font-size:.78rem; font-family:system-ui,sans-serif; }}
</style>
<h1>Auditions — {n} voix</h1>
{fiches}
"""

FICHE = """<div class="fiche">
 <img src="../portraits/{pid}.png" alt="" onerror="this.style.visibility='hidden'">
 <div class="corps">
  <div class="nom">{nom} <span class="id">{pid} · {voice_id}</span></div>
  <div class="desc">{description}</div>
  <div class="replique">« {texte} »</div>
  {etat}
  {lecteurs}
 </div>
</div>"""


def main():
    registre_chemin = RACINE / "etat" / "voix.json"
    registre = json.loads(registre_chemin.read_text(encoding="utf-8")) if registre_chemin.exists() else {}
    persos = json.loads((RACINE / "etat" / "personnages.json").read_text(encoding="utf-8"))
    # les gens de la salle dans l'ordre du casting, précédés des deux voix qui
    # n'appartiennent à personne : celle qui raconte, celle qui pense.
    dans_le_casting = [p["id"] for p in persos if p["id"] in VOIX]
    ordre = [i for i in VOIX if i not in dans_le_casting] + dans_le_casting

    fiches = []
    for pid in ordre:
        fiche = VOIX[pid]
        inscrit = registre.get(pid, {})
        retenue = inscrit.get("variante_retenue")
        extraits = sorted((RACINE / "voix").glob(f"{pid}-*.mp3"))
        lecteurs = "".join(
            '<span class="variante{cl}"><b>{lbl}</b>'
            '<audio controls preload="none" src="{f}"></audio></span>'.format(
                f=p.name,
                cl=" retenue" if retenue == n else "",
                lbl=("%d — en place" % n) if retenue == n else str(n),
            )
            for n, p in enumerate(extraits, 1)
        )
        # un design refait dont aucune variante n'a encore été adoptée
        etat = ('<div class="attente">trois variantes neuves — aucune adoptée, '
                "la voix en place est l'ancienne</div>"
                if inscrit.get("variantes") and not retenue else "")
        fiches.append(
            FICHE.format(
                pid=pid,
                nom=inscrit.get("nom", pid),
                voice_id=inscrit.get("voice_id", "— non créée —"),
                description=fiche["description"],
                texte=fiche["texte"],
                etat=etat,
                lecteurs=lecteurs or "<i>aucun extrait</i>",
            )
        )

    SORTIE.write_text(GABARIT.format(n=len(fiches), fiches="\n".join(fiches)), encoding="utf-8")
    print(f"écrit {SORTIE} ({len(fiches)} fiches)")


if __name__ == "__main__":
    main()
