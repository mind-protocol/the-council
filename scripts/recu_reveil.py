#!/usr/bin/env python3
"""Façade publique pour déposer un reçu de réveil depuis un fichier JSON."""

import argparse
import json
from pathlib import Path

from agents.recu_reveil import REGISTRE, RecuInvalide, deposer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("piece", help="fichier JSON du reçu sans id ni enregistre_le")
    ap.add_argument("--registre", default=str(REGISTRE),
                    help="journal JSONL append-only (runtime par défaut)")
    args = ap.parse_args()
    with open(args.piece, "r", encoding="utf-8") as source:
        piece = json.load(source)
    try:
        recu, ajoute = deposer(piece, Path(args.registre))
    except RecuInvalide as exc:
        raise SystemExit("REÇU REFUSÉ — %s" % exc)
    print(json.dumps({"statut": "DÉPOSÉ" if ajoute else "DÉJÀ PRÉSENT",
                      "registre": str(Path(args.registre).resolve()),
                      "recu": recu}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

