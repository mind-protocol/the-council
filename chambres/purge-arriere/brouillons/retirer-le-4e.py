# -*- coding: utf-8 -*-
"""Le retrait du 4e — ce que je fais le 31.8, et ce que je garde pour pouvoir le rendre.

Le monde est revenu au 129.4.3 (minute 721). Restait, dans les tables du JOUE,
la matinee du 4e de Peyredragon. Je la retire — mais je la RECOPIE d'abord,
entiere, dans ma chambre : une purge qui ne peut pas se rendre est une perte,
non une reparation.

NE TOUCHE QUE `date` (ce qui a eu lieu). Jamais `date_prevue` (ce qui est prevu) :
mort-lucerys est prevu le 9e et doit rester.
"""
import json, os, sys, datetime

racine = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
etat = os.path.join(racine, "etat")
chambre = os.path.join(racine, "chambres", "purge-arriere")

CIBLES = ["actes.json", "paroles.json", "pensees.json"]
vraiment = "--vraiment" in sys.argv


def apres_le_3e(x):
    d = x.get("date")
    if not isinstance(d, dict):
        return False
    return d.get("annee") == 129 and d.get("lune") == 4 and (d.get("jour") or 0) > 3


manifeste = {
    "quoi": "Matinee du 4e de la 4e lune, retiree des tables du joue le 31.8 par purge-arriere,"
            " le monde etant revenu au 129.4.3 minute 721.",
    "pourquoi": "Le curseur du monde est au 3e ; ces pieces racontent un jour qui n'a pas eu lieu."
                " Si la direction rend les six jours, tout ceci se raccroche tel quel.",
    "retire_le": datetime.date.today().isoformat(),
    "tables": {},
}

for f in CIBLES:
    p = os.path.join(etat, f)
    brut = json.load(open(p, encoding="utf-8"))
    enveloppe = None
    liste = brut
    if isinstance(brut, dict):
        for k, v in brut.items():
            if isinstance(v, list):
                liste, enveloppe = v, k
                break
    vises = [x for x in liste if isinstance(x, dict) and apres_le_3e(x)]
    manifeste["tables"][f] = vises
    print("%-16s %3d a retirer sur %d" % (f, len(vises), len(liste)))
    for x in vises[:3]:
        print("      ex. :", x.get("id") or x.get("qui"))
    if vraiment and vises:
        restants = [x for x in liste if x not in vises]
        os.replace(p, p + ".avant-retrait-du-4e-20260831")
        if enveloppe:
            brut[enveloppe] = restants
            sortie = brut
        else:
            sortie = restants
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(sortie, fh, ensure_ascii=False, indent=1)
        print("      -> retire, copie de sauvegarde a cote")

if vraiment:
    dest = os.path.join(chambre, "ma-memoire", "retrait-du-4e-20260831.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(manifeste, fh, ensure_ascii=False, indent=1)
    print("\nManifeste :", dest)
else:
    print("\nMODE MONTRER. Relancer avec --vraiment si la liste est juste.")
