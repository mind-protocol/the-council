# -*- coding: utf-8 -*-
# MATIERE — la descente lot 2 de scripts/dossier.py, qui reste la facade
# gelee (docs/organisation.md §7 : dossier.py -> agents/matiere.py).
# -*- coding: utf-8 -*-
# Le dossier d'un sujet : tout ce que l'etat sait deja de lui, avant d'ecrire.
#
# Usage :
#     python scripts/dossier.py --sur wat
#     python scripts/dossier.py --sur caves --sur roon --depuis 16
#     python scripts/dossier.py --sur rosby --large        (tout le texte, pas d'extrait)
#
# POURQUOI. Un journal n'est pas une source. `journal.scenes` et
# `scene_courante` sont des resumes ecrits par un MJ, parfois faux, souvent
# vieux d'un jour. Le 26e de la troisieme lune, le journal disait « les quarante
# dans les caves » pendant qu'un acte du 18e disait « trente-huit hommes sont
# libres » — et une scene entiere a ete jouee sur le resume.
#
# Ce script ne verifie rien et n'arbitre rien : il RASSEMBLE, dans l'ordre
# d'autorite. Les annales d'abord, parce qu'elles ne se contredisent pas ; puis
# les actes et les paroles ; puis les fiches et les evenements ; le journal en
# dernier, marque pour ce qu'il est. A lire avant d'ouvrir une scene, et avant
# de faire parler quelqu'un.
import io, json, os, re, sys, unicodedata
from plan.expose import bibliotheque  # LA PORTE de plan/

# La console Windows est en cp1252 : un seul caractere abime dans une parole
# (un `�` herite d'une vieille ecriture) tuait le script en plein milieu,
# et le dossier s'arretait AVANT ses dernieres sections sans rien dire. C'est
# ainsi que « ce qu'il a en tete » restait invisible pour Gerardys et pas pour
# Rulf : la difference n'etait pas dans les travaux, elle etait dans un octet.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Un etage de plus qu'a la racine : scripts/agents/ (voir scripts/CLAUDE.md).
racine = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
etat = os.path.join(racine, "etat")

# Ordre d'autorite. Ce qui est en haut gagne sur ce qui est en bas.
SOURCES = [
    ("annales.json",     "LES ANNALES — verite acquise, ne peut pas etre contreservie"),
    ("actes.json",       "LES ACTES"),
    ("paroles.json",     "LES PAROLES"),
    ("evenements.json",  "LES EVENEMENTS (canon et programmes)"),
    ("personnages.json", "LES FICHES"),
    ("intentions.json",  "LES TETES — jamais montre au joueur"),
    ("info.json",        "CE QUI EST PARVENU AU JOUEUR"),
]


def sans_accents(t):
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def charger(nom):
    if nom == "books.json":
        return bibliotheque.charger(etat)
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
        # {"vues": [...]} ou {"<id>": {...}} — on rend des dicts dans les deux cas
        for v in d.values():
            if isinstance(v, list):
                return v
        return [dict(v, personnage_id=k) if isinstance(v, dict) else {"id": k}
                for k, v in d.items()]
    return []


# ---- Les adresses : de quoi poser un pointeur au lieu d'un numero nu -------
# Un conseiller cite « les neufs », « la cinquieme file », « ce qu'on doit au
# Sanglier » — et le joueur devine. Le fil sait pourtant ouvrir la ligne exacte
# quand on l'ecrit `[les neufs](44022)` ; il n'y manquait que d'avoir la forme
# sous les yeux au moment ou l'on compose la replique. C'est ici qu'on regarde
# avant d'ecrire, donc c'est ici qu'on la donne, toute faite.
#
# On ne deballe pas les vingt lignes de chaque cahier : seulement les numeros
# qu'il a REELLEMENT en tete — ceux qui traversent ses pensees et sa
# conclusion. C'est exactement ce que le MJ s'apprete a distiller.
def index_des_lignes():
    index = {}
    for v in charger("books.json"):
        tables = list(v.get("tables") or [])
        if v.get("colonnes"):
            tables.append({"colonnes": v.get("colonnes"),
                           "lignes": v.get("lignes") or []})
        for t in tables:
            # Plus de porte « N° » (D.35) : une ligne est adressable si elle
            # COMMENCE par un numero — les plans l'ont toujours fait, les
            # registres tamponnes (serie 9xxxx) le font desormais aussi.
            for l in (t.get("lignes") or []):
                cells = l.get("cellules") if isinstance(l, dict) else l
                cells = cells or []
                m = re.match(r"\s*(?:\*\*)?\s*(\d{4,6})\b",
                             str(cells[0] if cells else ""))
                if not m:
                    continue
                lib = str(cells[1] if len(cells) > 1 else "")
                lib = re.sub(r"^\s*[^\w\s(]+\s*", "", lib).replace("**", "")
                index[m.group(1)] = (lib.strip(), v.get("titre") or v.get("id"))
    return index


def dossier_adresses(elements):
    if not elements:
        return
    index = index_des_lignes()
    if not index:
        return
    vus, trouves = set(), []
    for e in elements:
        for n in re.findall(r"(?<!\d)(\d{4,6})(?!\d)", texte_de(e)):
            if n in vus or n not in index:
                continue
            vus.add(n)
            trouves.append((n, index[n]))
    if not trouves:
        return
    trouves.sort()
    print("\n== SES ADRESSES — a poser en POINTEUR, jamais en numero nu")
    print("   Ce qu'il a en tete porte une adresse au registre. Ecrite ainsi,")
    print("   elle ouvre la ligne et la surligne ; ecrite en chiffres, elle ne")
    print("   dit rien a personne. Le libelle est ce que l'homme DIT — le")
    print("   voici tout fait, a raccourcir a sa bouche. Deux par replique.")
    for n, (lib, livre) in trouves:
        print("     [%s](%s)" % (lib or "…", n))
        print("        %s" % livre)


# ---- Les registres : ce qui est ARRETE, avant ce qui a ete dit -------------
# La spec est du MJ lui-meme (chambres/mj/books/affaire-retrouver-un-chiffre-
# arrete.json, D.31) : une joueuse a decroche sur un compte dont la reponse
# etait ecrite, datee et sourcee dans un registre que rien ne savait voir —
# index_des_lignes() ne lit que les tables a colonne N°, jamais mot -> ligne.
# Ici : AUCUNE condition sur l'intitule des colonnes, filtre conjonctif de
# main(), et le PLAFOND est la moitie de la spec — un registre deballe est un
# mur (le meme mal que le tunnel).
PLAFOND_REGISTRES = 12


def dossier_registres(sujets):
    """Les lignes de etat/books/ qui portent TOUS les sujets.

    Rend (lignes, restes) : au plus PLAFOND_REGISTRES tuples
    (volume, table, cellules), volumes les plus fournis d'abord, et le
    compte de ce qui n'est pas montre par volume — la queue du rendu."""
    par_volume = {}
    for v in charger("books.json"):
        titre_v = str(v.get("titre") or v.get("id") or "?")
        tables = list(v.get("tables") or [])
        if v.get("colonnes"):
            tables.append({"titre": "", "colonnes": v.get("colonnes"),
                           "lignes": v.get("lignes") or []})
        for t in tables:
            titre_t = str(t.get("titre") or "")
            for l in (t.get("lignes") or []):
                cells = (l.get("cellules") if isinstance(l, dict) else l) or []
                texte = sans_accents(" ".join(str(c) for c in cells)
                                     + " " + str((l.get("note") or "")
                                                 if isinstance(l, dict) else ""))
                if all(s in texte for s in sujets):
                    par_volume.setdefault(titre_v, []).append((titre_t, cells))
    ordre = sorted(par_volume.items(), key=lambda kv: -len(kv[1]))
    lignes, restes = [], {}
    for volume, trouvees in ordre:
        for titre_t, cells in trouvees:
            if len(lignes) < PLAFOND_REGISTRES:
                lignes.append((volume, titre_t, cells))
            else:
                restes[volume] = restes.get(volume, 0) + 1
    return lignes, restes


def imprimer_registres(sujets):
    """La section, PREMIERE du dossier : un registre est plus haut dans
    l'ordre d'autorite qu'un recit de scene. Rend le nombre de lignes."""
    lignes, restes = dossier_registres(sujets)
    if not lignes:
        return 0
    print("\n== CE QUI EST ARRETE AUX REGISTRES  (%d)" % len(lignes))
    for volume, table, cells in lignes:
        nettes = [re.sub(r"\*\*", "", str(c)).strip() for c in cells if
                  str(c).strip()]
        print("  [%s%s]" % (volume, (" — " + table) if table else ""))
        print("      " + " · ".join(nettes)[:400])
    if restes:
        print("      + %d autres ligne(s) dans %s" % (
            sum(restes.values()),
            ", ".join(sorted(restes))))
    return len(lignes)


def jour_de(x):
    d = x.get("date") or x.get("date_prevue") or x.get("date_maj") or {}
    if not isinstance(d, dict):
        return None
    return d.get("jour")


def texte_de(x):
    return json.dumps(x, ensure_ascii=False)


def etiquette(x):
    d = x.get("date") or x.get("date_prevue") or x.get("date_maj") or {}
    j = d.get("jour")
    m = d.get("minute")
    quand = ("%2de" % j) if j is not None else "  ?"
    if m is not None:
        quand += " %02dh%02d" % (m // 60, m % 60)
    return quand


def corps(x, large):
    for cle in ("quoi", "texte", "description", "resume", "intention", "titre"):
        if x.get(cle):
            t = re.sub(r"\s+", " ", str(x[cle])).strip()
            return t if large else (t[:400] + (" […]" if len(t) > 400 else ""))
    return re.sub(r"\s+", " ", texte_de(x))[:300]


def dossier_travaux(sujets, large):
    """Ce qu'un homme a appris — la MATIERE de sa voix, jamais son texte.

    LE MARQUAGE `servie` A DISPARU, et c'est une mesure qui l'a tue : 11
    pensees marquees sur 613. Il n'etait pas tenu, et son absence faisait
    croire a 98 % de perte. Ce qui le remplace est l'ordre du jour : les plus
    recentes d'abord, parce qu'un homme sert ce qu'il vient d'apprendre.

    On prend ses pensees par `qui`, ce qui est le cas courant (« que sait
    Gerardys ce matin ? »). A defaut, on retombe sur la recherche plein texte,
    pour qu'une AFFAIRE se retrouve aussi par son nom.
    """
    pensees = charger("pensees.json")
    conclusions = charger("conclusions.json")
    siennes = [p for p in pensees
               if sans_accents(str(p.get("qui") or "")) in sujets]
    siens_c = [c for c in conclusions
               if sans_accents(str(c.get("qui") or "")) in sujets]
    if not siennes:
        siennes = [p for p in pensees
                   if all(s in sans_accents(texte_de(p)) for s in sujets)]
        siens_c = [c for c in conclusions
                   if all(s in sans_accents(texte_de(c)) for s in sujets)]
    if not (siennes or siens_c):
        return 0

    def rang(p):
        d = p.get("date") or {}
        return (d.get("annee", 0), d.get("lune", 0), d.get("jour", 0))
    siennes.sort(key=rang, reverse=True)

    print("\n== CE QU'IL A EN TETE — JAMAIS MONTRE AU JOUEUR  (%d pensee(s))"
          % len(siennes))
    print("   La MATIERE de ses repliques, pas leur texte : on distille trois a")
    print("   six phrases la-dedans, on ne devide pas la liste. Les plus")
    print("   recentes d'abord — c'est ce qu'il a envie de dire.")

    for c in siens_c:
        print("\n  SA CONCLUSION, de sa main — %s" % (c.get("affaire") or "?"))
        print("    son cahier : %s" % (c.get("livre") or "aucun inscrit"))
        t = re.sub(r"\s+", " ", str(c.get("texte") or "")).strip()
        print("      " + (t if large else t[:600] +
                          (" […]" if len(t) > 600 else "")))

    n = 0
    par_affaire = {}
    for p in siennes:
        par_affaire.setdefault(p.get("affaire") or "(hors affaire)", []).append(p)
    for aff, lot in sorted(par_affaire.items(), key=lambda kv: -len(kv[1])):
        d = lot[0].get("date") or {}
        print("\n  %s  (%d, la derniere au %se jour)" % (
            aff, len(lot), d.get("jour", "?")))
        for p in lot:
            n += 1
            txt = re.sub(r"\s+", " ", str(p.get("texte") or "")).strip()
            print("      · " + (txt if large else txt[:400] +
                                (" […]" if len(txt) > 400 else "")))
            print("        source : %s" % re.sub(
                r"\s+", " ", str(p.get("source") or "?")).strip()[:160])
    dossier_adresses(siennes + siens_c)
    return n


def main(argv):
    sujets, depuis, large = [], None, False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--sur" and i + 1 < len(argv):
            sujets.append(sans_accents(argv[i + 1])); i += 2
        elif a == "--depuis" and i + 1 < len(argv):
            depuis = int(argv[i + 1]); i += 2
        elif a == "--large":
            large = True; i += 1
        elif not a.startswith("--"):
            sujets.append(sans_accents(a)); i += 1
        else:
            i += 1
    if not sujets:
        raise SystemExit(
            "usage : dossier.py --sur <mot> [--sur <mot>...] [--depuis <jour>] [--large]\n"
            "  Rassemble ce que l'etat sait deja d'un homme, d'un lieu ou d'une affaire,\n"
            "  dans l'ordre d'autorite : annales, actes, paroles, evenements, fiches.")

    print("DOSSIER : %s%s" % (" + ".join(sujets),
                              ("  (depuis le %de jour)" % depuis) if depuis else ""))
    total = 0
    # D.32 (la spec du MJ) : ce qui est ARRETE passe avant ce qui a ete dit.
    total += imprimer_registres(sujets)
    for fichier, titre in SOURCES:
        trouves = []
        for x in charger(fichier):
            t = sans_accents(texte_de(x))
            if not all(s in t for s in sujets):
                continue
            j = jour_de(x)
            if depuis is not None and j is not None and j < depuis:
                continue
            trouves.append(x)
        if not trouves:
            continue
        trouves.sort(key=lambda x: (jour_de(x) is None, jour_de(x) or 0), reverse=True)
        print("\n== %s  (%d)" % (titre, len(trouves)))
        for x in trouves:
            total += 1
            ident = x.get("id") or x.get("personnage_id") or x.get("nom") or "?"
            print("  [%s] %s" % (etiquette(x), ident))
            print("      " + corps(x, large))
        if fichier == "annales.json":
            print("      ^ Rien de ce qui precede ne peut etre contredit par une scene neuve.")

    # CE QU'IL A EN TETE. Une section a part, et pas une source de plus dans la
    # liste ci-dessus : les autres disent ce qui EST, celle-ci dit avec quoi il
    # va parler. C'est le trou que ce script avait — on le lisait « avant de
    # faire parler quelqu'un » sans jamais lui ouvrir son travail, et la
    # replique se fabriquait alors a partir de ce qui venait d'etre dit dans la
    # salle. Les pensees ne sont PAS des repliques a reciter : c'est la matiere
    # brute d'ou sortent trois a six phrases. On distille, on ne devide pas.
    total += dossier_travaux(sujets, large)

    # Le journal en dernier, et nomme pour ce qu'il est.
    jdir = os.path.join(etat, "joueurs")
    if os.path.isdir(jdir):
        for j in sorted(os.listdir(jdir)):
            p = os.path.join(jdir, j, "journal.json")
            if not os.path.exists(p):
                continue
            try:
                with io.open(p, encoding="utf-8") as f:
                    d = json.load(f)
            except Exception:
                continue
            scenes = [s for s in (d.get("scenes") or [])
                      if all(s in sans_accents(json.dumps(s, ensure_ascii=False))
                             for s in sujets)]
            scenes = [s for s in (d.get("scenes") or [])
                      if all(m in sans_accents(json.dumps(s, ensure_ascii=False))
                             for m in sujets)]
            if not scenes:
                continue
            print("\n== LE JOURNAL DE %s — RESUME, PAS UNE SOURCE (%d)" % (j, len(scenes)))
            print("   En cas de conflit : les annales gagnent, puis les actes, puis ceci.")
            for s in scenes[-4:]:
                print("  [%s] %s" % (etiquette(s), s.get("salle") or s.get("lieu_id") or ""))
                print("      " + corps(s, large))

    if not total:
        print("\nRIEN. Aucun acte, aucune parole, aucune annale ne parle de ca.")
        print("Si vous vous appretez a inventer quelqu'un ou quelque part, c'est neuf —")
        print("mais verifiez l'orthographe du sujet avant de conclure au vide.")


