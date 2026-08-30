# -*- coding: utf-8 -*-
"""ADRESSER UN REGISTRE — facade (D.35, tranche le 31.8).

    python scripts/adresser_registre.py <volume-id>            a sec
    python scripts/adresser_registre.py <volume-id> --vraiment

Un fait arrete est adressable : chaque ligne de registre recoit un numero de
la SERIE 9 (90000-99999, reservee aux registres — les plans vivent en dessous),
tamponne en tete de sa premiere cellule (`**9xxxx** ...`). Des lors la ligne
s'indexe comme une ligne de plan : `[le compte des manquants](90007)` s'ouvre
et se surligne depuis le fil. On ne tamponne JAMAIS deux fois, et l'ecriture
passe par la porte.
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "noyau"))
from etat.expose import tables  # noqa: E402
import bibliotheque  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) \
    if os.path.basename(os.path.dirname(os.path.abspath(__file__))) == "scripts" \
    else os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep + "scripts", 1)[0]
ETAT = os.path.join(RACINE, "etat")

DEJA = re.compile(r"^\s*(?:\*\*)?\s*(\d{4,6})\b")


def _prochain_numero():
    """Le premier libre de la serie 9, en balayant TOUS les volumes."""
    pris = set()
    for v in bibliotheque.charger(ETAT):
        for t in (list(v.get("tables") or [])
                  + ([{"lignes": v.get("lignes")}] if v.get("lignes") else [])):
            for l in (t.get("lignes") or []):
                cells = (l.get("cellules") if isinstance(l, dict) else l) or []
                m = DEJA.match(str(cells[0]) if cells else "")
                if m:
                    pris.add(int(m.group(1)))
    n = 90000
    while n in pris:
        n += 1
    return n


def main():
    vraiment = "--vraiment" in sys.argv
    cibles = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not cibles:
        raise SystemExit(__doc__)
    volume_id = cibles[0]
    chemin = os.path.join(ETAT, "books", "%s.json" % volume_id)
    if not os.path.exists(chemin):
        raise SystemExit("volume introuvable : %s" % chemin)
    v = tables.lire(chemin, None)
    numero = _prochain_numero()
    tamponnees = 0
    groupes = list(v.get("tables") or [])
    if v.get("lignes"):
        groupes.append({"lignes": v["lignes"]})
    for t in groupes:
        for l in (t.get("lignes") or []):
            cells = l.get("cellules") if isinstance(l, dict) else None
            if not cells or DEJA.match(str(cells[0])):
                continue
            print("  %d <- %s" % (numero, str(cells[0])[:70]))
            if vraiment:
                cells[0] = "**%d** %s" % (numero, cells[0])
            numero += 1
            tamponnees += 1
    if vraiment and tamponnees:
        tables.ecrire(chemin, v)
    print("%d ligne(s) %s dans %s" % (
        tamponnees, "tamponnees" if vraiment else "a tamponner [a sec]",
        volume_id))


if __name__ == "__main__":
    main()
