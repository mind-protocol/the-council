# -*- coding: utf-8 -*-
# LIVRE — ouvrir un volume, et un seul, pour quelqu'un de nomme.
#
# POURQUOI CE SCRIPT EXISTE. `etat/books.json` fait 2,1 Mo — environ 547 000
# jetons. On ne le lit pas : on s'y noie. Un homme depeche a qui l'on disait
# « va le lire a son identifiant » y a passe huit minutes sans rien rendre.
# Un volume seul, lui, fait 2 300 jetons en mediane et 14 800 au pire : c'est
# la bonne unite, et c'est celle-ci qu'on sert.
#
# ET SURTOUT : LE TRI VIT ICI, PAS DANS LA CONSIGNE. Dire a quelqu'un « voici
# ton etagere, n'ouvre rien d'autre » n'est pas un verrou, c'est une priere :
# il suffit de deviner un identifiant. `--pour` est donc OBLIGATOIRE, et ce
# script refuse net un volume que cet homme-la ne peut pas ouvrir. Cinq
# coffrets sont `acteur: rhaenyra, prive: true` — sans ce refus, un sergent
# lirait le carnet de la reine sans que personne s'en apercoive.
#
# La regle de portee est transcrite de serveur/serveur.js, dans le meme ordre
# de tests, pour qu'un volume visible ici le soit aussi a l'ecran et
# reciproquement. Deux regles qui divergent valent une fuite.
#
# Usage :
#     python scripts/livre.py --pour le-sanglier --index
#     python scripts/livre.py --pour le-sanglier --ouvrir registre-des-offices
#     python scripts/livre.py --pour le-sanglier --ouvrir X --cherche "porte de mer"
import argparse
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")


def _charger(nom, defaut):
    p = os.path.join(ETAT, nom)
    if not os.path.exists(p):
        return defaut
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def etagere(qui):
    """Les volumes que `qui` peut ouvrir — exactement ce que `GET /books`
    lui servirait. Rend une liste de dicts, deja resolus (les coffrets ont
    donne leur place aux volumes qu'ils contiennent)."""
    livres = _charger("books.json", [])
    boites = _charger("boites.json", [])
    if isinstance(boites, dict):
        boites = boites.get("boites", [])
    gens = _charger("personnages.json", [])
    if isinstance(gens, dict):
        gens = gens.get("personnages", [])

    ou = {p.get("id"): p.get("lieu_id") for p in gens}
    ici = ou.get(qui)
    coffret = {c.get("id"): c for c in boites}

    for b in livres:
        c = coffret.get(b.get("boite"))
        if not c:
            continue
        # Range dans un coffret : le volume perd sa place et prend la sienne.
        b["lieu_id"] = c.get("lieu_id")
        b["salle_id"] = c.get("salle_id")
        b["acteur_id"] = c.get("acteur_id")
        b["prive"] = bool(c.get("prive"))
        # `lecteurs` ne se remplace pas, il s'AJOUTE : un coffret reserve peut
        # contenir un volume plus reserve encore, jamais moins.
        if c.get("lecteurs"):
            b["lecteurs"] = ([q for q in b["lecteurs"] if q in c["lecteurs"]]
                             if b.get("lecteurs") else list(c["lecteurs"]))

    def chateau(b):
        a = b.get("acteur_id")
        return ou[a] if (a and a in ou) else b.get("lieu_id")

    def visible(b):
        # `lecteurs` ne donne rien, il retire.
        if b.get("lecteurs") and qui not in b["lecteurs"]:
            return False
        if b.get("acteur_id") and b["acteur_id"] == qui:
            return True
        if b.get("prive") and b.get("acteur_id"):
            return False
        ch = chateau(b)
        return (not ch) or (not ici) or (ch == ici)

    return [b for b in livres if visible(b)]


def index(qui, noms):
    siens, maison = [], []
    for b in etagere(qui):
        t = u"%-34s %s" % (b.get("id", "?"), (b.get("titre") or u"")[:44])
        if b.get("acteur_id") == qui:
            siens.append(u"    " + t)
        else:
            p = b.get("acteur_id")
            ou_ = (u"porte par %s" % noms.get(p, p)) if p else \
                  (u"pose : %s" % b["salle_id"]) if b.get("salle_id") else u""
            maison.append(u"    %s%s" % (t, (u"   (%s)" % ou_) if ou_ else u""))
    return siens, maison


def _lignes_de(bloc):
    """Une table est {colonnes, lignes:[{cellules:[...]}]}. Certains volumes
    portent colonnes/lignes a la racine, d'autres une liste de `tables`."""
    return bloc.get("colonnes") or [], bloc.get("lignes") or []


def rendre(b, cherche=None, large=False):
    out = []
    a = out.append
    a(u"═" * 74)
    a(u"%s   [%s]" % (b.get("titre") or b.get("id"), b.get("id")))
    if b.get("sous_titre"):
        a(u"  %s" % b["sous_titre"])
    ou_ = (u"porte par %s" % b["acteur_id"]) if b.get("acteur_id") else \
          (u"pose : %s" % b["salle_id"]) if b.get("salle_id") else u"sans place"
    a(u"  %s · %s" % (b.get("type") or u"volume", ou_))
    a(u"═" * 74)

    blocs = []
    if b.get("colonnes"):
        blocs.append((None, b))
    for t in (b.get("tables") or []):
        blocs.append((t.get("titre"), t))

    for titre, bloc in blocs:
        cols, lignes = _lignes_de(bloc)
        if titre:
            a(u"\n── %s " % titre + u"─" * max(0, 70 - len(titre)))
        gardees = []
        for i, lg in enumerate(lignes, 1):
            cel = lg.get("cellules") or []
            plat = u" ".join(c or u"" for c in cel)
            if cherche and cherche.lower() not in plat.lower():
                continue
            gardees.append((i, cel))
        if cherche and not gardees:
            a(u"  (aucune ligne ne porte « %s »)" % cherche)
            continue
        for i, cel in gardees:
            a(u"\n  · ligne %d" % i)
            for j, c in enumerate(cel):
                nom = cols[j] if j < len(cols) else u"col%d" % (j + 1)
                v = (c or u"").strip()
                if not v:
                    continue
                if not large and len(v) > 600:
                    v = v[:600] + u" […]"
                a(u"    %s : %s" % (nom, v))

    # Une page est presque toujours du TEXTE NU (340 sur 343) ; les trois
    # autres sont des figures, qui n'ont rien a rendre a quelqu'un qui lit.
    pages = b.get("pages") or []
    if pages:
        a(u"\n── ce qui est ecrit " + u"─" * 52)
    for p in pages:
        if isinstance(p, dict):
            if p.get("legende"):
                a(u"\n  [figure] %s" % p["legende"])
            continue
        txt = p if isinstance(p, str) else u"%s" % p
        if cherche and cherche.lower() not in txt.lower():
            continue
        a(u"\n" + (txt if large or len(txt) < 4000
                   else txt[:4000] + u"\n[…]"))
    return u"\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pour", required=True,
                    help="qui ouvre — obligatoire, c'est le verrou")
    ap.add_argument("--index", action="store_true")
    ap.add_argument("--ouvrir")
    ap.add_argument("--cherche", help="ne rendre que les lignes qui le portent")
    ap.add_argument("--large", action="store_true", help="ne tronque rien")
    a = ap.parse_args()

    gens = _charger("personnages.json", [])
    if isinstance(gens, dict):
        gens = gens.get("personnages", [])
    noms = {p.get("id"): p.get("nom") or p.get("id") for p in gens}
    if a.pour not in noms:
        raise SystemExit(u"Personne ne s'appelle « %s »." % a.pour)

    if a.ouvrir:
        for b in etagere(a.pour):
            if b.get("id") == a.ouvrir:
                print(rendre(b, a.cherche, a.large))
                return
        # On ne dit PAS s'il existe ailleurs : ce serait deja une fuite.
        raise SystemExit(
            u"Il n'y a pas de volume « %s » sur votre etagere.\n"
            u"  python scripts/livre.py --pour %s --index"
            % (a.ouvrir, a.pour))

    siens, maison = index(a.pour, noms)
    print(u"L'ETAGERE DE %s — %d volume(s)"
          % (noms[a.pour].upper(), len(siens) + len(maison)))
    if siens:
        print(u"\n  LES VOTRES — vous les portez\n" + u"\n".join(siens))
    if maison:
        print(u"\n  CEUX DE LA MAISON\n" + u"\n".join(maison))


if __name__ == "__main__":
    main()
