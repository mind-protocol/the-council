# -*- coding: utf-8 -*-
# REPRISE — la feuille de reprise : ce qu'il faut avoir en tete pour se rasseoir, et RIEN d'autre.
#
# Usage :
#     python scripts/reprise.py                    (le siege courant, 3 jours devant)
#     python scripts/reprise.py --jours 6
#     python scripts/reprise.py --qui aurore-inchauspe
#     python scripts/reprise.py --large            (les textes entiers, pas les entames)
#
# POURQUOI. `dossier.py` repond a « que sait-on de X » : il faut deja savoir
# quoi demander. Le mal d'un joueur qui revient est l'inverse — il ne sait plus
# QUELLE question poser. Trois lunes de jeu font 601 paroles et 2,4 Mo de
# livres ; relire ne remet pas dans le role, ca enterre.
#
# Ce script ne resume pas la partie. Il repond aux cinq questions qu'un homme
# se pose en ouvrant les yeux, et il s'arrete la :
#   ou je suis et dans quel etat — ce qui est sur la table a l'instant —
#   ce que j'ai lance qui court encore — ce qui me tombe dessus bientot —
#   ce que j'ai appris en dernier.
#
# Il est BREF par construction, et c'est le point : chaque section est plafonnee.
# Une feuille qui deborde est une feuille qu'on ne lit pas, donc un joueur qui
# ne se rassoit pas. Pour creuser un nom qui en sort, c'est dossier.py qui prend
# le relais. Ce script ne lit que l'etat ; il n'ecrit nulle part.
import io, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

racine = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
etat = os.path.join(racine, "etat")

MOIS = {1: "1re", 2: "2e", 3: "3e", 4: "4e", 5: "5e", 6: "6e",
        7: "7e", 8: "8e", 9: "9e", 10: "10e", 11: "11e", 12: "12e"}


def charger(nom, clef=None):
    p = os.path.join(etat, nom)
    if not os.path.exists(p):
        return []
    try:
        with io.open(p, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return []
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        if clef and isinstance(d.get(clef), list):
            return d[clef]
        return d
    return []


def rang(d):
    """Un ordre total sur une date d'etat, minute comprise quand elle y est."""
    if not isinstance(d, dict):
        return (0, 0, 0, 0)
    return (d.get("annee", 0), d.get("lune", 0), d.get("jour", 0), d.get("minute", 0))


def heure(d):
    m = d.get("minute")
    if m is None:
        return ""
    return "%dh%02d" % (m // 60, m % 60)


def date_courte(d):
    if not isinstance(d, dict):
        return "?"
    s = "%s le %de" % (MOIS.get(d.get("lune"), "?"), d.get("jour", 0))
    h = heure(d)
    return (h + " " + s) if h else s


def ecart_jours(a, b):
    """b - a en jours pleins. Les lunes font 30 jours, comme partout ici."""
    f = lambda d: (d.get("annee", 0) * 360 + d.get("lune", 0) * 30 + d.get("jour", 0))
    return f(b) - f(a)


def entame(t, n=150):
    """La premiere phrase, ou ce qui tient sur une ligne. On ne recopie pas un
    pave dans une feuille dont le but est de ne pas en etre un."""
    t = re.sub(r"\s+", " ", (t or "").strip())
    if not t:
        return ""
    if LARGE:
        return t
    coupe = re.split(r"(?<=[.!?…»])\s", t)
    p = coupe[0] if coupe else t
    if len(p) > n:
        p = p[:n].rsplit(" ", 1)[0] + "…"
    return p


def utile(t, n=170):
    """Ce qui a ete DIT, pas ou on se tenait en le disant. Les paroles s'ecrivent
    ici avec un en-tete de scene (« LA ROUKERIE, 20h24 LE 28e, en se levant du
    tabouret ») : le prendre pour la parole, c'est rendre une feuille de reprise
    ou l'on ne lit que des noms de salles."""
    t = re.sub(r"\s+", " ", (t or "").strip())
    if not t:
        return ""
    phrases = [p for p in re.split(r"(?<=[.!?…»])\s", t) if p.strip()]
    def entete(p):
        lettres = [c for c in p if c.isalpha()]
        hautes = sum(1 for c in lettres if c.isupper())
        return (re.search(r"\d{1,2}h\d{2}", p) is not None
                or (lettres and hautes / len(lettres) > 0.6))
    reste = [p for p in phrases if not entete(p)]
    if LARGE:
        return " ".join(reste) or t
    p = (reste or phrases)[0]
    if len(p) > n:
        p = p[:n].rsplit(" ", 1)[0] + "…"
    return p


def titre(s):
    print("")
    print(s)
    print("-" * len(s))


def nom_de(pid, gens):
    for p in gens:
        if p.get("id") == pid:
            return p.get("nom") or pid
    return pid or "?"


def main(argv):
    global LARGE
    jours = 3
    qui = None
    LARGE = "--large" in argv
    for i, a in enumerate(argv):
        if a == "--jours" and i + 1 < len(argv):
            jours = int(argv[i + 1])
        if a == "--qui" and i + 1 < len(argv):
            qui = argv[i + 1]
        if a in ("--aide", "-h", "--help"):
            print(__doc__ or "")
            print("usage : reprise.py [--qui <id>] [--jours N] [--large]")
            return 0

    monde = charger("monde.json")
    journal = charger("journal.json")
    gens = charger("personnages.json")
    joueur = qui or (journal.get("personnage_joueur_id") if isinstance(journal, dict) else None)
    if not joueur:
        print("Aucun siege : journal.personnage_joueur_id est vide.")
        return 1
    fiche = next((p for p in gens if p.get("id") == joueur), {})

    # L'horloge du monde, et celle du siege quand elle a pris de l'avance :
    # la scene en cours fait foi sur monde.date, qui traine souvent d'un tour.
    dm = monde.get("date", {}) if isinstance(monde, dict) else {}
    # `scene_courante` est tantot un objet, tantot une phrase libre — la
    # doctrine autorise les deux et le MJ ecrit souvent la seconde. Une chaine
    # n'a pas de date : on retombe alors sur l'horloge du monde au lieu de
    # tomber en marche, parce que c'est le PREMIER geste de chaque session.
    sc = journal.get("scene_courante") if isinstance(journal, dict) else None
    sc = sc if isinstance(sc, dict) else {}
    # ET L'HORLOGE DU SIEGE, qui est la vraie montre : append_flux.py la tient
    # a chaque poussee, et le joueur la voit dans son bandeau. Sans elle, une
    # `scene_courante` ecrite en prose (la doctrine l'autorise) faisait
    # retomber la feuille sur monde.date -- vu le 4e de la 4e lune : bandeau
    # au 3e jour 12h01 quand le siege etait au 4e jour, 8h58.
    horloges = charger("horloges.json")
    hs = horloges.get(joueur) if isinstance(horloges, dict) else None
    maintenant = dm
    for candidate in (sc.get("date"), hs):
        if isinstance(candidate, dict) and rang(candidate) > rang(maintenant):
            maintenant = candidate

    print("")
    print("=" * 72)
    print("  REPRISE — %s, %s" % ((fiche.get("nom") or joueur).upper(), date_courte(maintenant)))
    print("=" * 72)

    # 1. OU JE SUIS
    titre("OU JE SUIS, ET DANS QUEL ETAT")
    lieu = sc.get("salle") or sc.get("lieu_id") or fiche.get("lieu_id") or "?"
    print("  %s (%s)" % (lieu, fiche.get("lieu_id") or "?"))
    if fiche.get("condition"):
        print("  Etat du corps : %s" % fiche["condition"])
    if isinstance(monde, dict):
        print("  Le royaume : %s, tension %s" % (monde.get("phase", "?"), monde.get("tension", "?")))
    pres = [nom_de(p, gens) for p in (sc.get("participants") or []) if p != joueur]
    if pres:
        print("  Avec moi : " + ", ".join(pres))

    # 2. CE QUI EST SUR LA TABLE
    if sc.get("beat"):
        titre("CE QUI EST SUR LA TABLE, MAINTENANT")
        b = re.sub(r"\s+", " ", sc["beat"]).strip()
        if not LARGE and len(b) > 700:
            b = b[:700].rsplit(" ", 1)[0] + "…"
        for ligne in re.split(r"\s*\|\|\s*", b):
            if ligne.strip():
                print("  " + ligne.strip())

    # 3. CE QUE J'AI LANCE QUI COURT ENCORE
    paroles = charger("paroles.json")
    miennes = [p for p in paroles
               if p.get("locuteur_id") == joueur
               # PAS DE FILTRE PAR TYPE : le vocabulaire est ouvert (50 valeurs,
               # 174 paroles sans type) -- une liste fermee en ratait la plus
               # grande part. On filtre par bouche et par date, comme le dit
               # docs/schema.md depuis son amendement.
               and ecart_jours(p.get("date") or {}, maintenant) <= 2]
    miennes.sort(key=lambda p: rang(p.get("date") or {}), reverse=True)
    if miennes:
        titre("CE QUE J'AI ORDONNE OU PROMIS (2 derniers jours)")
        for p in miennes[:8]:
            # LE SCHEMA FAIT FOI (docs/schema.md) : une parole porte
            # `destinataire_id` et `contenu`. Lire `destinataires`/`texte`
            # ne levait rien -- ca imprimait "a la cantonade" et du vide.
            vises = p.get("destinataires")
            if not vises:
                vises = [p["destinataire_id"]] if p.get("destinataire_id") else []
            a = ", ".join(nom_de(d, gens) for d in vises) or "a la cantonade"
            print("  %s  a %s" % (date_courte(p.get("date") or {}), a))
            print("      %s" % utile(p.get("contenu") or p.get("quoi")
                                        or p.get("texte")))

    # 4. CE QUI EST PARTI ET N'EST PAS REVENU
    plis = charger("plis.json", "plis")
    courants = [p for p in plis if p.get("etat") in ("en-route", "parti", "attente", "muet", "retenu")]
    courants.sort(key=lambda p: rang(p.get("attendu_le") or p.get("parti_le") or {}))
    if courants:
        titre("CE QUI EST PARTI ET N'EST PAS REVENU")
        for p in courants[:8]:
            att = p.get("attendu_le")
            quand = ("attendu %s" % date_courte(att)) if att else "sans terme"
            if att and ecart_jours(att, maintenant) > 0:
                quand = "EN RETARD de %d jour(s)" % ecart_jours(att, maintenant)
            print("  [%s] %s -> %s (%s) — %s"
                  % (p.get("etat"), nom_de(p.get("de"), gens), nom_de(p.get("pour"), gens),
                     p.get("vers") or "?", quand))

    # 5. CE QUI TOMBE BIENTOT
    evs = charger("evenements.json")
    proches = [e for e in evs
               if e.get("statut") in ("programme", "prevu", None, "")
               and isinstance(e.get("date_prevue"), dict)
               and 0 <= ecart_jours(maintenant, e["date_prevue"]) <= jours]
    proches.sort(key=lambda e: rang(e.get("date_prevue")))
    if proches:
        titre("CE QUI TOMBE DANS LES %d JOURS" % jours)
        for e in proches[:10]:
            print("  %s  %s" % (date_courte(e["date_prevue"]), e.get("titre") or e.get("id")))

    # 6. CE QUE J'AI APPRIS EN DERNIER
    infos = sorted(charger("info.json"), key=lambda i: rang(i.get("date_apprise") or {}), reverse=True)
    if infos:
        titre("CE QUE J'AI APPRIS EN DERNIER")
        for i in infos[:5]:
            print("  %s  %s" % (date_courte(i.get("date_apprise") or {}), utile(i.get("version"))))

    # 7. LES DERNIERES SCENES
    scenes = journal.get("scenes") or [] if isinstance(journal, dict) else []
    if scenes:
        titre("LES DERNIERES SCENES (le journal — un resume, pas une source)")
        for s in scenes[-5:]:
            print("  %s  %s" % (date_courte(s.get("date") or {}), utile(s.get("resume"), 170)))

    print("")
    print("  Pour creuser un nom qui sort d'ici : python scripts/dossier.py --sur <mot>")
    print("")
    return 0


LARGE = False
