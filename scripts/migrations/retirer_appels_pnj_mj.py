# -*- coding: utf-8 -*-
"""Retire des volumes actifs les consignes PNJ -> MJ devenues caduques.

La migration conserve les etats, dates, preuves et notes deja ecrits par les
habitants. Elle ne remplace que le contrat commun des lignes C.1, C.3 et
P.3/P.8/P.9/P.10. Les pas deja clos restent declares historiques ; ils ne
sont pas reecrits comme s'ils avaient toujours suivi la nouvelle regle.
"""
from __future__ import print_function

import glob
import io
import json
import os
import re
import sys


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPTS = os.path.join(RACINE, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


NOUVEAUX = {
    "P.3": (
        u"Sourcer un élément de mon histoire",
        u"Chercher ce fait dans une source accessible ou auprès d'une "
        u"personne qui peut me le rappeler. Sans source, le marquer "
        u"incertain : ne pas demander au MJ de l'inventer ou de le valider.",
        u"mes sources",
        u"une source nommée, ou l'incertitude écrite"),
    "P.8": (
        u"Chercher ce que je ne sais pas encore",
        u"Ouvrir une source accessible ou écrire à une personne du monde "
        u"avec une question précise et datée. Si personne ni aucun registre "
        u"ne répond, conserver l'inconnu au lieu de demander au MJ.",
        u"mes sources ou un canal",
        u"une source citée ou un inconnu écrit"),
    "P.9": (
        u"Accomplir mon premier geste sans permission du MJ",
        u"Faire ce qui est à la portée de mes mains, de mon office et de mon "
        u"autorité, puis écrire le geste réellement accompli. Si son issue "
        u"dépend d'un autre ou du hasard, laisser la conséquence en attente "
        u"sans l'inventer.",
        u"dans le monde",
        u"un geste accompli ou une conséquence en attente"),
    "P.10": (
        u"Écrire à un homme du monde",
        u"`python scripts/parloir.py --dire --de <moi> --a <untel> \"...\"` "
        u"— la parole et l'enquête passent par les habitants, jamais par le "
        u"MJ.",
        u"au parloir",
        u"un canal de plus dans `relations/`"),
}


def _table(donnees, prefixe):
    for table in donnees.get("tables") or []:
        if str(table.get("titre") or "").startswith(prefixe):
            return table
    return None


def _clos(cellules):
    if len(cellules) < 6:
        return False
    return str(cellules[5] or "").strip().lower() in {
        "fait", "faite", "clos", "close", "termine", "terminée"
    }


def _historique(texte):
    """Conserve la trace sans laisser une commande copiable dans le brief."""
    if not isinstance(texte, str):
        return texte
    texte = re.sub(r"--(?:tenter|faire|demander)\b", u"[ancien verbe]",
                   texte, flags=re.IGNORECASE)
    texte = re.sub(r"\bmj-[a-z0-9-]+\b", u"[ancienne régie]", texte,
                   flags=re.IGNORECASE)
    return texte


def migrer(donnees):
    change = False
    cibles = _table(donnees, u"🎯")
    lignes_cibles = (cibles or {}).get("lignes") or []
    ancien_format = len(lignes_cibles) <= 2
    for ligne in lignes_cibles:
        c = ligne.get("cellules") or []
        if not c:
            continue
        if ancien_format and c[0] == "C.1" and len(c) >= 3:
            c[2] = (u"Mon cahier porte au moins un amendement daté, et mes "
                    u"deux journaux ont chacun une entrée ou une raison "
                    u"écrite de n'en pas avoir.")
            change = True
        elif ancien_format and c[0] == "C.2" and len(c) >= 4:
            c[2] = (u"J'ai cherché une source sans demander au MJ, puis "
                    u"écrit à un homme du monde.")
            c[3] = u"une source citée et un canal dans `relations/`"
            change = True
        elif c[0] == "C.1" and len(c) >= 3:
            c[2] = (u"Mon cahier porte ma manière à la première personne, "
                    u"un élément de mon histoire étayé par une source "
                    u"accessible, et mes objectifs posés ici.")
            change = True
        elif c[0] == "C.3" and len(c) >= 4:
            c[2] = (u"J'ai cherché une source sans demander au MJ, puis "
                    u"écrit à un homme du monde.")
            c[3] = u"une source citée et un canal dans `relations/`"
            change = True

    actions = _table(donnees, u"⚔️")
    lignes_actions = (actions or {}).get("lignes") or []
    ids_actions = {(ligne.get("cellules") or [None])[0]
                   for ligne in lignes_actions if ligne.get("cellules")}
    ancien_format = not any(i in ids_actions for i in ("P.8", "P.9", "P.10"))
    for ligne in lignes_actions:
        c = ligne.get("cellules") or []
        if not c:
            continue
        # Nettoie aussi les notes historiques : elles restent lisibles, mais
        # aucune commande PNJ -> MJ ne demeure copiable dans un volume actif.
        for index, valeur in enumerate(c):
            c[index] = _historique(valeur)

        titre_actuel = str(c[1] if len(c) > 1 else "").lower()
        role = None
        if "demander à mon arbitre" in titre_actuel:
            role = "P.8"
        elif "adresser mon premier geste" in titre_actuel:
            role = "P.9"
        elif "écrire à un homme qui n'est pas mon arbitre" in titre_actuel:
            role = "P.10"
        elif "faire tenir pour vrai" in titre_actuel or \
                "sourcer un élément" in titre_actuel:
            role = "P.3"
        elif ancien_format and c[0] == "P.5":
            role = "P.8"
        elif ancien_format and c[0] == "P.6":
            role = "P.9"
        elif ancien_format and c[0] == "P.7":
            role = "P.10"
        elif not ancien_format and c[0] in NOUVEAUX:
            role = c[0]

        # La première passe avait interprété P.3 comme le pas d'histoire dans
        # les anciens volumes à sept pas. Dans ce format P.3 signifie ouvrir
        # ses affaires : on le restaure sans toucher à sa preuve ni son état.
        if ancien_format and c[0] == "P.3" and \
                "historique clos" in titre_actuel:
            c[1] = u"Ouvrir mes affaires sous ces colonnes"
            c[2] = (u"Écrire ici, sous « ⚔️ Actions », ce dont je réponds "
                    u"vraiment : une ligne par pas, l'état en un mot et la "
                    u"preuve attendue.")
            c[3] = u"ce volume"
            role = None
            change = True

        if role not in NOUVEAUX:
            continue
        titre, geste, lieu, preuve = NOUVEAUX[role]
        if _clos(c) and role in {"P.3", "P.8", "P.9"}:
            c[1] = u"Historique clos — ancien appel au MJ"
            c[2] = (u"Ce pas appartenait au contrat retiré. Il reste clos "
                    u"comme trace, ne doit pas être rejoué et n'autorise "
                    u"aucun nouvel appel de PNJ vers le MJ.")
            c[3] = u"archive du volume"
        else:
            c[1], c[2], c[3] = titre, geste, lieu
            if len(c) >= 5:
                c[4] = preuve
        change = True
    return change


def _ecrire(fichier, texte):
    """Ecriture atomique : les chambres peuvent etre lues en parallele."""
    temporaire = fichier + ".tmp-pnj-mj"
    with io.open(temporaire, "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)
    os.replace(temporaire, fichier)


def main():
    motifs = [
        os.path.join(RACINE, "chambres", "*", "books", "affaire-*.json"),
        os.path.join(RACINE, "chambres", "*", "livres", "affaire-*.json"),
    ]
    faits = []
    for motif in motifs:
        for fichier in glob.glob(motif):
            with io.open(fichier, encoding="utf-8") as f:
                donnees = json.load(f)
            if not migrer(donnees):
                continue
            _ecrire(fichier, json.dumps(donnees, ensure_ascii=False,
                                        indent=1) + u"\n")
            if os.path.basename(os.path.dirname(fichier)) == "livres":
                from plan.expose import livre
                texte = livre.rendre(donnees, large=True)
                _ecrire(os.path.splitext(fichier)[0] + ".txt",
                        texte.rstrip() + u"\n")
            faits.append(os.path.relpath(fichier, RACINE))
    print(u"%d volume(s) migre(s)" % len(faits))


if __name__ == "__main__":
    main()
