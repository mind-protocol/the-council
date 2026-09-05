#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
partie.py — le terminal du greffier d'une partie (voir scripts/agents/prompts/mj-partie.md).

Il ne joue pas, il ne juge pas. Les règles et le repli vivent dans
scripts/noyau/partie_greffe.py ; ici : la ligne de commande, la recherche dans
l'état et les livres, et la présentation d'un tour au format du manuel.

    python scripts/partie.py <partie> --etat
    python scripts/partie.py <partie> --plateau [--camp <camp>]
    python scripts/partie.py <partie> --jouer '{"camp":"noir","coup":"lever",...}'
    python scripts/partie.py <partie> --fichier coups.jsonl
    python scripts/partie.py <partie> --tour
    python scripts/partie.py <partie> --presenter [--depuis-tour N]
    python scripts/partie.py <partie> --chaine 49000
    python scripts/partie.py <partie> --piece vhagar
    python scripts/partie.py <partie> --grand-livre
    python scripts/partie.py <partie> --chercher galeres

<partie> est un id (etat/parties/<id>.jsonl) ou un chemin. Le fichier est
append-only : --jouer, --fichier et --tour ajoutent des lignes, rien d'autre.
"""
import argparse
import io
import json
import os
import re
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from partie_greffe import (Partie, RACINE, DOSSIER, JOURS_PAR_TOUR,  # noqa: E402
                           EMOJI_CAMP, EMOJI_COUP, liste)
from partie_lecture import chaine, piece, grand_livre, etat, relire  # noqa: E402
import partie_cartes  # noqa: E402  — la vue joueur, en cartes (v0)
import partie_journal  # noqa: E402  — les derniers coups, dits en clair
import partie_marques  # noqa: E402  — ce que l'écran a le droit d'offrir
import partie_gestes  # noqa: E402  — une carte posée sur une carte, en coup (v1)
import partie_ascii  # noqa: E402  — la même vue, au terminal
import partie_grille  # noqa: E402  — la même vue en grille : où l'on se touche


# ---------------------------------------------------------------- chercher
def chercher(mot):
    """Ce que l'état et les livres savent d'un mot : lecture seule, avec la source."""
    mot_l = mot.lower()
    out = []
    for nom in ("personnages", "lieux", "maisons"):
        p = os.path.join(RACINE, "etat", nom + ".json")
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        d = d if isinstance(d, list) else next((v for v in d.values() if isinstance(v, list)), [])
        for x in d:
            if mot_l in json.dumps(x, ensure_ascii=False).lower():
                out.append("%s.json : %s — %s" % (nom, x.get("id"), (x.get("nom") or x.get("titre") or "")[:60]))
                for k in ("lieu_id", "controle_id", "condition", "maison_id"):
                    if x.get(k):
                        out[-1] += " · %s=%s" % (k, x[k])
    books = os.path.join(RACINE, "etat", "maisons")
    for dossier, _, fichiers in os.walk(books):
        for f in fichiers:
            if not f.endswith(".json") or "books" not in dossier:
                continue
            try:
                d = json.load(io.open(os.path.join(dossier, f), encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            for t in d.get("tables", []) or []:
                for l in t.get("lignes", []) or []:
                    c = [re.sub(r"\*\*", "", str(x)) for x in l.get("cellules", [])]
                    if any(mot_l in x.lower() for x in c[:2]):
                        out.append("%s › %s : %s — %s" % (d.get("id"), t.get("titre", "")[:14], c[0][:8], c[1][:90]))
            if len(out) > 40:
                break
    return out or ["rien dans l'état ni dans les livres pour « %s »" % mot]


# ---------------------------------------------------------------- présenter
def nom_clair(p, rid):
    """Un nom en clair pour n'importe quel id de la partie — pièce, état, blocage,
    clé, maillon, destruction — « jamais un id nu » (mj-partie.md §5.4)."""
    rid = str(rid)
    for reg in (p.ressources, p.etats, p.blocages, p.cles, p.maillons, p.menaces):
        x = reg.get(rid)
        if x and x.get("texte"):
            t = x["texte"].strip().rstrip(".")
            return t if len(t) <= 60 else t[:57].rstrip() + "…"
    return rid.replace("-", " ")


def noms(p, ids):
    return ", ".join(nom_clair(p, x) for x in liste(ids))


def verbe_gras(texte):
    """Le premier mot est le verbe du coup : on le met en gras, comme le manuel le demande."""
    texte = (texte or "").strip()
    if not texte:
        return ""
    m = re.match(r"^(\S+)(.*)$", texte, re.S)
    return "**%s**%s" % (m.group(1), m.group(2)) if m else texte


def presenter(p, depuis_tour=1):
    """La présentation d'un tour (mj-partie.md §5.4) : titre, coups, place pour l'analyse, état."""
    out = []
    tour_courant = None
    vues_mortes = set()
    for l in p.lignes:
        t = int(l.get("tour") or 1)
        if l.get("coup") == "tour":
            if t < depuis_tour:
                continue
            titre = "**— Tour %d —**" % t
            details = []
            if l.get("arrivees"):
                details.append("arrive : " + ", ".join(nom_clair(p, x) for x in l["arrivees"]))
            if l.get("degeles"):
                details.append("dégelé : " + ", ".join(nom_clair(p, x) for x in l["degeles"]))
            if l.get("menaces"):
                details.append("atterrit : " + noms(p, l["menaces"]))
            if l.get("parees"):
                details.append("parée, n'atterrit pas : " + noms(p, l["parees"]))
            if l.get("parades_tenues"):
                details.append("parade tenue, la frappe tombe : " + noms(p, l["parades_tenues"]))
            if l.get("constatables"):
                details.append("à constater : " + noms(p, l["constatables"]))
            if l.get("inactifs"):
                details.append("muet depuis trois tours : " + ", ".join(EMOJI_CAMP[c] for c in l["inactifs"]))
            if l.get("etats_arrives"):
                details.append("entre au deck : " + noms(p, l["etats_arrives"]))
            neuves = [x for x in (l.get("branches_mortes") or []) if x not in vues_mortes]
            vues_mortes.update(neuves)   # une branche morte se dit une fois, pas à chaque tour
            if neuves:
                details.append("branche morte : " + ", ".join(nom_clair(p, x) for x in neuves))
            out.append("")
            out.append(titre + (" *(%s)*" % " · ".join(details) if details else ""))
            tour_courant = t
            continue
        if t < depuis_tour:
            continue
        if tour_courant is None:
            out.append("**— Tour %d —**" % t)
            tour_courant = t
        e = EMOJI_CAMP.get(l.get("camp"), "?") + EMOJI_COUP.get(l.get("coup"), "?")
        coup = l.get("coup")
        if coup == "arbitrer":
            queue = ""
            if l.get("arrive_tour"):
                queue = ", **arrive au tour %s**" % l["arrive_tour"]
            if l.get("nombre") is not None:
                queue += ", %s" % l["nombre"]
            corps = "**%s** %s%s — *%s*" % (l.get("verdict", "").capitalize(), noms(p, l.get("sur", "")), queue, l.get("motif", ""))
        elif coup == "demander":
            corps = "**Demande** %s%s%s" % (nom_clair(p, l["id"]),
                                            (" à %s" % l["lieu"]) if l.get("lieu") else "",
                                            (", %s" % l["nombre"]) if l.get("nombre") else "")
        elif coup == "viser":
            corps = "**Vise** %s *(%s%s)*" % (l.get("texte", ""), l.get("id"),
                                             ", entre au tour %s" % l["arrive_tour"] if l.get("arrive_tour") else "")
        elif coup == "justifier":
            corps = "**Suspend** « %s » — *%s*" % (nom_clair(p, l.get("sur")), l.get("texte", ""))
        elif coup == "rearmer":
            corps = "**Réarme** « %s » avec %s — *%s*" % (nom_clair(p, l.get("id")), noms(p, l.get("engage")), l.get("texte", ""))
        elif coup == "constater":
            corps = "**Constate** « %s » %s — *%s*" % (nom_clair(p, l.get("etat")), l.get("verdict", ""), l.get("motif", ""))
        elif coup == "passer":
            corps = "**Passe** — *%s*" % (l.get("texte") or l.get("motif") or "")
        elif coup == "retirer":
            corps = "**Retire** %s, gel %s tours — *%s*" % (nom_clair(p, l["id"]), l.get("gel_tours", 2), l.get("texte", ""))
        else:
            corps = verbe_gras(l.get("texte") or l.get("motif") or coup)
            cible = l.get("sur") or l.get("ouvre") or l.get("cible") or (l.get("realise") if coup == "agir" else None)
            if cible:
                corps += " *(%s « %s »)*" % ({"bloquer": "sur", "lever": "lève", "justifier": "suspend",
                                              "detruire": "vise", "agir": "réalise"}.get(coup, "→"),
                                             noms(p, cible))
            if l.get("engage"):
                corps += " · engage " + noms(p, l["engage"])
            if l.get("avec"):
                corps += " · avec " + noms(p, l["avec"])
            if coup == "agir" and l.get("etat") == "faite":
                corps += " · **réalisé**"
        out.append("%s %s — %s" % (e, l.get("n"), corps))
    out.append("")
    out.append("**Analyse.** *(à écrire par le MJ : la qualité des coups, ce qu'ils changent)*")
    out.append("")
    out.append("**État**")
    out += etat(p)[1:]
    return out


# ---------------------------------------------------------------- écritures
def ecritures(p, depuis_tour=1):
    """Le récap de ce que la partie demande d'écrire dans l'état (mj-partie.md §6.3).

    Un coup posé n'écrit rien ; un coup réalisé, un arbitrage qui comble, une
    destruction qui atterrit, un état constaté, si. On liste, on n'écrit pas :
    c'est le MJ qui passe par ajouter.py et les fichiers d'état.
    """
    out = []
    jour = lambda t: "tour %d, jour +%d" % (t, (int(t) - 1) * JOURS_PAR_TOUR)
    for l in p.lignes:
        t = int(l.get("tour") or 1)
        if t < depuis_tour:
            continue
        coup = l.get("coup")
        if coup == "agir" and l.get("etat") == "faite":
            m = p.maillons.get(l.get("id"), {})
            out.append("📝 acte (%s) : %s — par %s%s · témoins et connu_de à poser · ajouter.py actes" % (
                jour(t), l.get("texte") or m.get("texte", ""), m.get("qui") or l.get("qui") or "?",
                (", avec " + ", ".join(nom_clair(p, x) for x in liste(m.get("avec") or l.get("avec")))) if (m.get("avec") or l.get("avec")) else ""))
        elif coup == "arbitrer" and l.get("verdict") in ("accorde", "tranche"):
            motif = (l.get("motif") or "").lower()
            comble = "combl" in motif or "canon" in motif
            for src in p._lignes_visees(l.get("sur")):
                if src.get("coup") == "demander" and comble:
                    out.append("🧩 fait comblé (%s) : %s à %s%s — %s · à écrire dans l'état (personnages, lieux, mains) avec la date" % (
                        jour(t), nom_clair(p, src["id"]), l.get("lieu") or src.get("lieu") or "?",
                        (", %s" % (l.get("nombre") or src.get("nombre"))) if (l.get("nombre") or src.get("nombre")) else "",
                        l.get("motif", "")))
                elif src.get("coup") == "detruire" and l.get("verdict") == "tranche":
                    out.append("💥 destruction partielle (%s) : %s perd %s — %s · acte, jetons.force, et diffusion vers qui peut l'apprendre" % (
                        jour(t), nom_clair(p, src.get("cible", "")), l.get("nombre"), l.get("motif", "")))
        elif coup == "tour":
            for mid in liste(l.get("menaces")):
                m = p.menaces.get(mid)
                if m and m.get("realisee") and not m.get("partielle"):
                    out.append("💥 destruction (%s) : %s n'existe plus — %s · acte avec témoins, retirer de l'état, diffusion datée" % (
                        jour(l["tour"]), nom_clair(p, m["cible"]), m.get("texte", "")))
        elif coup == "constater":
            e = p.etats.get(l.get("etat"), {})
            out.append("✅ état constaté (%s) : %s %s — %s · preuve au cahier ; annales si ça change le cours des choses" % (
                jour(t), l.get("etat"), l.get("verdict"), e.get("texte", "")))
        elif coup == "retirer" and l.get("id") in p.ressources:
            r = p.ressources[l["id"]]
            out.append("🗑️ retrait (%s) : %s se retire — %s · position et jetons à mettre à jour, programme si ça met du temps" % (
                jour(t), nom_clair(p, l["id"]), l.get("texte", "")))
        elif coup == "reconstruire":
            out.append("🔧 reconstruction (%s) : %s revient au tour %s — programme daté dans evenements.json" % (
                jour(t), nom_clair(p, l["id"]), l.get("revient_tour", "?")))
    if not out:
        out.append("rien à écrire : aucun coup réalisé depuis le tour %d" % depuis_tour)
    out.append("")
    out.append("Le monde avance de %d jours par tour : monde.date au tour %d = départ + %d jours." % (
        JOURS_PAR_TOUR, p.tour, (p.tour - 1) * JOURS_PAR_TOUR))
    return out


# ---------------------------------------------------------------- main
def chemin_de(partie):
    if partie.endswith(".jsonl") or os.path.sep in partie or "/" in partie:
        return os.path.abspath(partie)   # un nom nu sans dossier plantait makedirs("")
    return os.path.join(DOSSIER, partie + ".jsonl")


def main():
    ap = argparse.ArgumentParser(description="le greffier d'une partie")
    ap.add_argument("partie")
    ap.add_argument("--etat", action="store_true")
    ap.add_argument("--relire", type=int, nargs="?", const=1, metavar="DEPUIS")
    ap.add_argument("--jouer", metavar="JSON", help="une ligne de coup ; refusée si mal formée")
    ap.add_argument("--fichier", metavar="JSONL", help="jouer chaque ligne d'un fichier, dans l'ordre")
    ap.add_argument("--tour", action="store_true", help="passer au tour suivant")
    ap.add_argument("--chaine", metavar="ID")
    ap.add_argument("--piece", metavar="ID")
    ap.add_argument("--grand-livre", dest="grand_livre", action="store_true")
    ap.add_argument("--chercher", metavar="MOT")
    ap.add_argument("--presenter", action="store_true", help="la présentation des tours, format du manuel")
    ap.add_argument("--ecritures", action="store_true", help="le récap de ce qu'il faut écrire dans l'état")
    ap.add_argument("--depuis-tour", dest="depuis_tour", type=int, default=1)
    ap.add_argument("--cartes", action="store_true", help="la vue joueur en cartes, JSON (l'onglet « Le conseil »)")
    ap.add_argument("--plateau", action="store_true", help="la même vue, dessinée au terminal")
    ap.add_argument("--entier", action="store_true", help="avec --plateau : rien n'est coupé, les titres se replient")
    ap.add_argument("--grille", action="store_true", help="la position en grille : les points de contact, qui prévaut, et les creux")
    ap.add_argument("--ruban", metavar="SORTIE.html", nargs="?", const="-",
                    help="la partie DANS LE TEMPS : les coups tour par tour et la vie de chaque pièce")
    ap.add_argument("--camp", default=None, help="le camp du siège qui regarde ou qui joue (premier camp de la partie sinon)")
    ap.add_argument("--vu", type=int, default=0, metavar="N",
                    help="le dernier numero de ligne deja vu : ce qui suit est marque neuf")
    ap.add_argument("--geste", metavar="JSON",
                    help="un geste de l'écran : {quoi:poser|reprendre|jour, piece, sur, texte}")
    a = ap.parse_args()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8") if hasattr(sys.stdout, "buffer") else sys.stdout

    p = Partie(chemin_de(a.partie))
    def cartes(part, camp, vu):
        """La vue de l'écran, ET ce qui vient d'être joué en clair.

        Les deux voyagent ensemble parce qu'ils répondent à la même question en
        arrivant devant le plateau : « où en est-on, et qu'a-t-il joué ? ». La
        position seule marquait ce qui avait bougé sans jamais le dire. On ne
        touche pas `partie_cartes` pour autant — passé cinq cents lignes, il ne
        peut plus que maigrir (`.claude/hooks/taille.js`).
        """
        v = partie_cartes.vue(part, camp, vu)
        partie_marques.poser(v, part, camp)
        # le verdict d'un front est fait d'ids : on les rhabille avant l'ecran
        for f in v.get("fronts") or []:
            f["pourquoi"] = partie_journal.clair(part, f.get("pourquoi"))
        v["relecture"] = partie_journal.journal(part, camp, vu)
        return v

    if a.geste:
        # Le résultat porte la position d'APRÈS : l'écran redessine sans
        # redemander, et ce qu'il montre est ce que le greffe vient d'écrire —
        # pas ce que la page croyait avant le geste. Refus compris : la sortie
        # est toujours du JSON, et le code de retour reste 0.
        geste = json.loads(a.geste)
        # `--camp` VAUT POUR LE GESTE, et pas seulement pour la vue rendue. Le
        # serveur, lui, fond le camp dans le JSON avant d'appeler ; en ligne de
        # commande on l'oubliait, et le coup partait au premier camp de la
        # partie — refusé plus loin, avec un motif qui parlait d'un camp qu'on
        # n'avait pas demandé.
        geste.setdefault("camp", a.camp) if a.camp else None
        r = partie_gestes.jouer(p, geste)
        apres = Partie(p.chemin)
        r["vue"] = cartes(apres, a.camp, a.vu)
        print(json.dumps(r, ensure_ascii=False))
        return
    if a.ruban:
        import partie_ruban
        html = partie_ruban.rendre(partie_ruban.replier(p.chemin))
        if a.ruban == "-":
            print(html)
        else:
            io.open(a.ruban, "w", encoding="utf-8").write(html)
            print("ruban écrit : %s" % a.ruban)
        return
    if a.grille:
        print(chr(10).join(partie_grille.grille(partie_cartes.vue(p, a.camp, a.vu))))
        return
    if a.plateau:
        # le gras seulement vers un terminal : redirigé, ce ne serait que des
        # caractères parasites au milieu du texte
        vue = partie_cartes.vue(p, a.camp, a.vu)
        print(chr(10).join(partie_ascii.plateau(vue, gras=sys.stdout.isatty(), entier=a.entier)))
        return
    if a.cartes:
        print(json.dumps(cartes(p, a.camp, a.vu), ensure_ascii=False))
        return
    if a.chercher:
        print("\n".join(chercher(a.chercher)))
        return
    if a.jouer:
        refus = p.ecrire(json.loads(a.jouer))
        if refus:
            print("REFUSÉ : " + " ; ".join(refus))
            sys.exit(2)
        print("écrit n°%d (tour %d)" % (p.lignes[-1]["n"], p.tour))
    if a.fichier:
        ok = refuses = 0
        for brut in io.open(a.fichier, encoding="utf-8"):
            brut = brut.strip()
            if not brut:
                continue
            l = json.loads(brut)
            refus = p.ecrire(l)
            if refus:
                refuses += 1
                print("REFUSÉ %s/%s « %s » : %s" % (l.get("camp"), l.get("coup"), (l.get("texte") or l.get("id") or "")[:50],
                                                    " ; ".join(refus)))
            else:
                ok += 1
        print("%d écrites, %d refusées" % (ok, refuses))
    if a.tour:
        refus = p.ecrire({"camp": "arbitre", "coup": "tour"})
        if refus:
            print("REFUSÉ : " + " ; ".join(refus))
            sys.exit(2)
        l = p.lignes[-1]
        print("tour %d · arrivées %s · dégelés %s · menaces %s · branches mortes %s" % (
            l["tour"], l["arrivees"] or "—", l["degeles"] or "—", l["menaces"] or "—", l["branches_mortes"] or "—"))
    if a.presenter:
        print("\n".join(presenter(p, a.depuis_tour)))
    if a.ecritures:
        print("\n".join(ecritures(p, a.depuis_tour)))
    if a.relire is not None:
        print("\n".join(relire(p, a.relire)))
    if a.chaine:
        print("\n".join(chaine(p, a.chaine)))
    if a.piece:
        print("\n".join(piece(p, a.piece)))
    if a.grand_livre:
        print("\n".join(grand_livre(p)))
    if a.etat or not any([a.jouer, a.fichier, a.tour, a.relire is not None, a.chaine, a.piece, a.plateau, a.grille, a.ruban,
                          a.grand_livre, a.presenter, a.ecritures]):
        print("\n".join(etat(p)))
    if p.avertissements:
        print("⚠️  " + "\n⚠️  ".join(sorted(set(p.avertissements))))


if __name__ == "__main__":
    main()
