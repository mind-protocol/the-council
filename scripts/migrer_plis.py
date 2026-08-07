"""Convertit les entrees evenements.diffusion existantes en plis.

Usage :
    python scripts/migrer_plis.py
        Ecrit une PROPOSITION dans etat/staging/plis-<AAAAMMJJ-HHMMSS>.json
        et imprime un resume. N'ecrit JAMAIS dans etat/.

    python scripts/migrer_plis.py --sortie plis-essai.json
        Meme chose sous un autre nom (toujours dans etat/staging/).

Ce que fait la conversion, entree de diffusion par entree de diffusion :

- Seuls les canaux d'OBJET sont convertis : corbeau, cavalier, barque. La
  `rumeur` et le `temoin` ne sont pas des objets — ils ne voyagent pas dans une
  sacoche — et restent a `evenements.diffusion` (voir docs/plis.md).
- Une entree dont `qui` contient plusieurs destinataires donne PLUSIEURS plis :
  un pli est un papier, et un papier n'a qu'un destinataire.
- `porte` reprend la `version` de la diffusion : c'est deja le fait tel qu'il
  arrive LA, deforme. Fige au depart, il n'est plus relu ensuite.
- `parti_le` est reconstitue en remontant la route depuis `attendu_le` (la date
  de la diffusion) : corbeau ~ un tiers du plein tarif, cavalier et barque plein
  tarif, d'apres les `jours_de_pr` des deux lieux. Faute de lieu de depart
  lisible, on retombe sur la date de l'evenement.
- `etat` : une diffusion `livree` donne un pli `remis`, dans la main du
  destinataire NATUREL du lieu (le mestre) — jamais du `pour`. Une diffusion non
  livree donne un pli `en-route`, sans main.

La sortie porte les plis dans `plis_proposes` ET, pour ceux qui sont remis ou en
route, les mutations `pli_ajouter` correspondantes dans `mutations_proposees` :
le MJ relit, elague, puis applique lui-meme avec scripts/appliquer.py. Un seul
ecrivain — ce script n'en est pas un.
"""
import argparse
import io
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(SCRIPTS)

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from tick import (CANAUX_PLI, Etat, date_de, ecrire_staging, empreintes_etat,
                  fmt, jour_absolu, jours_de_route)


def id_de_pli(evenement_id, index, pour):
    """Un id stable et lisible : d'ou ca vient, et pour qui."""
    return "pli-{}-{}-{}".format(evenement_id, index + 1, pour)


def expediteur(e, ev):
    """A qui attribuer le pli : le premier acteur de l'evenement, a defaut."""
    for pid in (ev.get("acteurs") or []):
        if pid in e.perso_par_id:
            return pid
    return None


def convertir(e):
    """Rend (plis, laisses) : ce qui devient objet, et ce qui reste diffusion."""
    plis, laisses = [], []
    for ev in e.evenements:
        eid = ev.get("id")
        for i, ent in enumerate(ev.get("diffusion") or []):
            if not isinstance(ent, dict):
                continue
            canal = ent.get("canal")
            etiq = "{} / diffusion #{}".format(eid, i + 1)
            if canal not in CANAUX_PLI:
                laisses.append({"ou": etiq, "canal": canal,
                                "motif": "ni papier ni sacoche — reste a "
                                         "evenements.diffusion"})
                continue

            arrivee = ent.get("date")
            quand = jour_absolu(arrivee)
            if quand is None:
                laisses.append({"ou": etiq, "canal": canal,
                                "motif": "date illisible — a reprendre a la main"})
                continue

            vers = ent.get("ou")
            destinataires = [p for p in (ent.get("qui") or [])
                             if p in e.perso_par_id]
            if not destinataires and vers:
                # un pli adresse a un lieu tombe dans la main de son mestre
                naturel = e.destinataire_naturel(vers)
                destinataires = [naturel] if naturel else []
            if not vers and destinataires:
                perso = e.perso_par_id.get(destinataires[0]) or {}
                vers = perso.get("lieu_id")
            if not destinataires or not vers:
                laisses.append({"ou": etiq, "canal": canal,
                                "motif": "ni destinataire ni lieu exploitables"})
                continue

            de = expediteur(e, ev)
            depart_lieu = e.lieu(ev.get("lieu_id")) or (
                e.lieu((e.perso_par_id.get(de) or {}).get("lieu_id"))
                if de else None)
            route = jours_de_route(e, depart_lieu, vers, canal) \
                if depart_lieu else None
            if route is None:
                parti = ev.get("date_prevue") if jour_absolu(
                    ev.get("date_prevue")) is not None else arrivee
            else:
                parti = date_de(quand - route)

            livree = ent.get("livree") is True
            main = e.destinataire_naturel(vers) if livree else None
            for pour in destinataires:
                pli = {
                    "id": id_de_pli(eid, i, pour),
                    "canal": canal,
                    "scelle": True,
                    "porte": ent.get("version") or ev.get("description") or "",
                    "de": de,
                    "pour": pour,
                    "vers": vers,
                    "parti_le": parti,
                    "attendu_le": arrivee,
                    "etat": "remis" if livree else "en-route",
                    "main": main,
                }
                if depart_lieu:
                    pli["depuis"] = depart_lieu
                pli["_venu_de"] = etiq
                if livree and main is None:
                    pli["_probleme"] = ("remis a {} sans destinataire naturel — "
                                        "dis dans quelle main il tombe".format(
                                            vers))
                if de is None:
                    pli["_probleme"] = ("aucun expediteur deduit de {} — "
                                        "nomme-le".format(eid))
                plis.append(pli)
    return plis, laisses


def main():
    a = argparse.ArgumentParser(
        description="Convertit evenements.diffusion en plis (sortie dans "
                    "etat/staging/ uniquement).")
    a.add_argument("--sortie", metavar="FICHIER",
                   help="nom du fichier dans etat/staging/")
    args = a.parse_args()

    e = Etat()
    plis, laisses = convertir(e)
    deja = {p.get("id") for p in e.plis if isinstance(p, dict)}

    mutations = []
    for pli in plis:
        if pli["id"] in deja:
            continue
        propre = {k: v for k, v in pli.items() if not k.startswith("_")}
        mutations.append({
            "table": "plis",
            "operation": "pli_ajouter",
            "valeur": propre,
            "pourquoi": "converti de {}".format(pli["_venu_de"]),
        })

    prop = {
        "genere_le": datetime.now().isoformat(timespec="seconds"),
        "empreintes": empreintes_etat(),
        "avertissement": "Proposition — le MJ relit, elague et applique "
                         "lui-meme. Ce fichier n'est pas de l'etat. "
                         "evenements.diffusion reste en place : c'est une "
                         "coexistence, pas un remplacement.",
        "plis_proposes": plis,
        "laisses_a_diffusion": laisses,
        "mutations_proposees": mutations,
    }
    nom = args.sortie or "plis-{}.json".format(
        datetime.now().strftime("%Y%m%d-%H%M%S"))
    chemin = ecrire_staging(nom, prop)

    print("Diffusions converties en plis : {}".format(len(plis)))
    for pli in plis:
        print("  {:<44} {} {} -> {} pour {} ({}){}".format(
            pli["id"], fmt(pli["parti_le"]), pli["canal"], pli["vers"],
            pli["pour"], pli["etat"],
            "  << " + pli["_probleme"] if pli.get("_probleme") else ""))
    print("\nLaissees a evenements.diffusion : {}".format(len(laisses)))
    for l in laisses:
        print("  {:<40} {} — {}".format(l["ou"], l["canal"], l["motif"]))
    print("\n{} mutation(s) 'pli_ajouter' redigee(s).".format(len(mutations)))
    print("Relis, elague, puis :")
    print("  python scripts/appliquer.py {}            # blanc".format(
        os.path.basename(chemin)))
    print("\nProposition ecrite : {}".format(
        os.path.relpath(chemin, RACINE).replace("\\", "/")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
