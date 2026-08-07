# -*- coding: utf-8 -*-
"""Les CORPS — donner une adresse physique à un personnage, ou une fiche à un corps.

    python scripts/corps.py                              l'état des liens
    python scripts/corps.py --qui wat-le-boiteux-tavernier
    python scripts/corps.py --ou mysaria                  où loge ce personnage
    python scripts/corps.py --chercher --role tavernier --quartier "Le Crochet"
    python scripts/corps.py --lier <acteur_id> <personnage_id> --vraiment
    python scripts/corps.py --delier <acteur_id> --vraiment
    python scripts/corps.py --promouvoir <acteur_id> --vraiment

Les corps sont ENGENDRÉS : quatre cent mille sans tête, découpés en cellules de
250 m dans `monde/gens/`, avec `monde/portreal.gens.json` pour manifeste. Tout
cela se réécrit à chaque passage de `scripts/monde/peupler.py` — on n'y écrit
donc jamais rien. Ce qui est décidé en jeu vit ici, dans `etat/corps.json`, et
survit à toutes les regénérations :

    {"liens": {"<acteur_id>": "<personnage_id>"},
     "corps": [{"personnage_id", "bat", "role", "x", "y", "z"}]}

`liens` emprunte un corps engendré ; `corps` en CRÉE un. Les deux sont
nécessaires et ne se remplacent pas : la matrone du Crochet existait déjà dans
la foule, et l'on n'a qu'à dire que c'est elle — le roi, non. Lui donner le
corps d'un intendant, ce n'est pas le physicaliser, c'est en faire un
domestique et voler sa place à quelqu'un.

Deux gestes, et ils vont dans les deux sens :

  - LIER : un personnage qui existe déjà (le mestre, l'agent, la matrone dont
    une scène a parlé) reçoit un corps — donc une maison, une rue, un étage,
    des voisins nommés, une distance en mètres jusqu'au Donjon Rouge.
  - PROMOUVOIR : un corps devient un personnage. Il avait déjà un nom, un
    métier et une adresse ; on lui écrit une fiche dans `personnages.json` et
    il entre dans l'histoire sans qu'on ait rien inventé de son décor.

Un corps lié reste un corps : il ne pense pas plus qu'avant. Ce sont
`intentions.json` et le MJ qui font une tête.
"""
import io, json, os, sys, tempfile, unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "scripts", "monde"))
import bati as _bati                                # le lecteur unique du bâti

GENS = os.path.join(RACINE, "monde", "portreal.gens.json")
LIENS = os.path.join(RACINE, "etat", "corps.json")
PERSOS = os.path.join(RACINE, "etat", "personnages.json")


def charger_gens():
    """Le MANIFESTE seul — quelques kilo-octets, jamais les quarante-cinq mégas.

    Les corps vivent dans monde/gens/<i>-<j>.json, une maille de 250 m. On ne
    lit une cellule que quand on la traverse : c'est vrai pour le navigateur,
    et autant le tenir ici aussi.
    """
    if not os.path.exists(GENS):
        sortir("monde/portreal.gens.json manque — lance d'abord "
               "python scripts/monde/peupler.py")
    G = json.load(io.open(GENS, encoding="utf-8"))
    C = {n: k for k, n in enumerate(G["_colonnes"])}
    return G, C


def cellules(G):
    """Chaque cellule, une par une. On ne garde jamais tout en mémoire."""
    d = os.path.join(RACINE, *G.get("dossier", "monde/gens").split("/"))
    for clef in sorted(G["cellules"]):
        f = os.path.join(d, clef + ".json")
        if not os.path.exists(f): continue
        yield clef, json.load(io.open(f, encoding="utf-8"))["gens"]


def tous(G):
    for _, lot in cellules(G):
        for g in lot:
            yield g


def par_identifiant(G, C, aid):
    for g in tous(G):
        if g[C["id"]] == aid:
            return g
    return None


def charger_liens():
    if not os.path.exists(LIENS):
        return {"liens": {}, "corps": []}
    L = json.load(io.open(LIENS, encoding="utf-8"))
    L.setdefault("liens", {})
    L.setdefault("corps", [])
    return L


def retrait(chemin, defaut=2):
    """L'indentation déjà en place dans le fichier.

    `personnages.json` est écrit avec un espace, les tables empilées avec deux.
    Réécrire avec la mauvaise, c'est un diff de deux mille lignes pour l'ajout
    d'une fiche — et à deux MJ, un diff illisible est un conflit garanti.
    """
    try:
        with io.open(chemin, encoding="utf-8") as f:
            for ligne in f:
                n = len(ligne) - len(ligne.lstrip(" "))
                if n: return n
    except OSError:
        pass
    return defaut


def ecrire(chemin, obj):
    """Relire-écrire dans la même milliseconde : à deux MJ, on ne s'écrase pas."""
    d = os.path.dirname(chemin)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with io.open(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=retrait(chemin)))
    os.replace(tmp, chemin)


def sortir(msg):
    print(msg)
    sys.exit(1)


def sans_accent(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def fiche(G, C, g, L):
    r = G["_roles"].get(g[C["role"]], {})
    lien = L["liens"].get(g[C["id"]])
    lignes = [
        "  %s" % g[C["id"]],
        "  %s — %s, %s ans" % (g[C["nom"]], r.get("nom", g[C["role"]]), g[C["age"]]),
        "  %s (%s), %s" % (g[C["quartier"]], g[C["usage"]], "bâtiment %d" % g[C["bat"]]),
        "  x %.1f  y %.1f  z %.1f  étage %d" % (g[C["x"]], g[C["y"]], g[C["z"]], g[C["etage"]]),
    ]
    if lien:
        lignes.append("  -> lié à %s" % lien)
    return "\n".join(lignes)


# ---------------------------------------------------------------------------
# INCARNER — apparier les personnages aux corps de la ville
# ---------------------------------------------------------------------------
# Une fiche sans corps n'est nulle part : le mestre existe, et il n'a ni rue,
# ni voisins, ni distance jusqu'au Donjon Rouge. L'appariement ne se tire pas au
# sort — on cherche le corps qui POURRAIT DÉJÀ ÊTRE LUI, et l'on prend un corps
# quelconque seulement faute de mieux.
#
# Le titre est la meilleure source dont on dispose : « Sergent du Guet à la
# porte de la Gadoue » dit le métier ET le quartier. `personnages.json` n'a pas
# de champ sexe (voir docs/schema.md) — on le lit dans les mots du titre, et
# quand rien ne le dit, on n'en fait pas un critère plutôt que de deviner.

# Un mot du titre -> les rôles qui lui correspondent, du plus proche au moins.
METIERS = [
    (("guet", "manteau"),            ["sergent", "capitaine-guet", "guet"]),
    (("gardien des dragons", "dragon"), ["gardien-dragons", "premier-gardien"]),
    (("alchimiste", "pyromant"),     ["sage-alchimiste", "alchimiste"]),
    (("septon", "septa", "foi"),     ["septon-superieur", "septon", "septa"]),
    (("mestre", "clerc", "role", "registre"), ["clerc-royal", "clerc-port", "clerc"]),
    (("port", "maitre du port"),     ["maitre-port", "clerc-port", "facteur"]),
    (("chantier", "bris", "bois"),   ["marchand-bois", "fendeur", "charbonnier"]),
    (("tenanciere", "taverne", "gaffe"), ["tavernier", "servante"]),
    (("close", "matrone", "fille"),  ["matrone", "fille"]),
    (("marchand", "marchande", "echoppe"), ["marchand", "commis", "etalier"]),
    (("preteu", "change", "usur"),   ["changeur", "clerc"]),
    (("forge", "acier"),             ["forgeron", "compagnon"]),
    (("boulang", "four"),            ["boulanger", "mitron"]),
    (("greve", "gamin", "gosse"),    ["enfant"]),
    (("veuve",),                     ["aieul", "epouse", "chef-de-feu"]),
    (("roi", "reine", "prince", "princesse", "main du roi", "garde royale"),
                                     ["officier-donjon", "intendant-royal", "clerc-royal"]),
    (("lord", "dame", "ser "),       ["maitre-maison", "officier-donjon"]),
    (("chuchoteur", "espion"),       ["logeur", "servante", "commis"]),
]
# Un mot du titre -> le quartier où l'on doit chercher.
QUARTIERS = [
    ("culpucier", "Le Culpucier"), ("crochet", "Le Crochet"),
    ("gadoue", "Le bourg de la Gadoue"), ("acier", "La rue d'Acier"),
    ("port", "Le port et ses hangars"), ("quai", "Le port et ses hangars"),
    ("greve", "Le port et ses hangars"), ("ville haute", "La ville haute"),
]
# LES GRANDS NE PRENNENT LE CORPS DE PERSONNE. Habiller Aegon II du corps d'un
# intendant de vingt-cinq ans n'est pas « le physicaliser », c'est en faire un
# domestique et voler sa place à quelqu'un. Ces gens-là habitent des lieux que
# la foule ne modélise pas — le Donjon Rouge est un maillage, pas un semis — et
# leur position vient des scènes, comme au château (scripts/presence.py).
# On les nomme, on dit où ils logent, et l'on n'apparie pas.
GRANDS = ("roi", "reine", "prince", "princesse", "main du roi", "lord commandant",
          "garde royale", "douairiere", "grand mestre")
DEMEURES = {"donjon-rouge": ("roi", "reine", "prince", "princesse", "main du roi",
                             "garde royale", "douairiere", "grand mestre")}

FEMININS = ("reine", "princesse", "dame", "septa", "tenanciere", "marchande",
            "veuve", "gamine", "maitresse", "cavaliere", "matrone", "soeur",
            "epouse-soeur", "douairiere", "fille")
MASCULINS = ("roi", "prince", "lord", "ser ", "sergent", "mestre", "septon",
             "maitre", "commis", "frere", "gamin", "capitaine", "messire")


def sexe_probable(p):
    t = sans_accent((p.get("titre") or "") + " " + (p.get("nom") or ""))
    f = any(m in t for m in FEMININS)
    h = any(m in t for m in MASCULINS)
    if f and not h: return "f"
    if h and not f: return "h"
    return None            # on ne devine pas : ce ne sera pas un critère


def incarner(G, C, L, vraiment, lieu):
    P = json.load(io.open(PERSOS, encoding="utf-8"))
    liste = P if isinstance(P, list) else P.get("personnages", [])
    pris = set(L["liens"])
    deja = set(L["liens"].values())
    gens = list(tous(G))            # une passe de lecture, pas une par acteur

    voulus = [p for p in liste
              if p.get("lieu_id") == lieu and p.get("etat") != "mort"
              and p["id"] not in deja]
    if not voulus:
        print("  personne à incarner à %s (tout le monde y a déjà un corps)" % lieu)
        return

    print("  %d acteurs à %s, %s corps disponibles"
          % (len(voulus), lieu, format(len(gens), ",d").replace(",", " ")))
    print()
    propositions = []
    for p in voulus:
        t = sans_accent((p.get("titre") or "") + " " + (p.get("nom") or ""))
        if any(m in t for m in GRANDS):
            propositions.append((p, None, ["GRAND"], None))
            continue
        age = 129 - p["naissance"] if p.get("naissance") else None
        sx = sexe_probable(p)
        roles = []
        for mots, r in METIERS:
            if any(m in t for m in mots): roles = r; break
        quartier = next((q for m, q in QUARTIERS if m in t), None)

        meilleur, note_max = None, -1
        for g in gens:
            if g[C["id"]] in pris: continue
            n = 0.0
            r = g[C["role"]]
            if roles:
                if r not in roles: continue          # le métier est un FILTRE,
                n += 6.0 - roles.index(r)            # pas une préférence
            if quartier:
                if g[C["quartier"]] != quartier: continue
                n += 3.0
            if sx and g[C["sexe"]] != sx: continue
            if age is not None:
                n += max(0.0, 3.0 - abs(g[C["age"]] - age) / 4.0)
            if n > note_max: note_max, meilleur = n, g
        if meilleur is None:
            propositions.append((p, None, roles, quartier))
            continue
        pris.add(meilleur[C["id"]])
        propositions.append((p, meilleur, roles, quartier))

    for p, g, roles, quartier in propositions:
        titre = (p.get("titre") or "")[:52]
        if g is None and roles == ["GRAND"]:
            demeure = next((d for d, mots in DEMEURES.items()
                            if any(m in sans_accent(titre) for m in mots)), None)
            print("  %-18s %-52s" % (p["id"], titre))
            print("      -- ne s'incarne pas : loge %s, position donnée par les scènes"
                  % ("au " + demeure if demeure else "hors de la foule"))
            continue
        if g is None:
            print("  %-18s %-52s  AUCUN CORPS PLAUSIBLE" % (p["id"], titre))
            print("      (cherché : %s%s)" % (", ".join(roles) or "n'importe qui",
                  " dans " + quartier if quartier else ""))
            continue
        print("  %-18s %-52s" % (p["id"], titre))
        print("      -> %s, %s, %s ans, %s (%s)"
              % (g[C["id"]], G["_roles"].get(g[C["role"]], {}).get("nom", g[C["role"]]),
                 g[C["age"]], g[C["quartier"]], g[C["usage"]]))

    faits = [(p, g) for p, g, _, _ in propositions if g is not None]
    grands = sum(1 for _, g, r, _ in propositions if g is None and r == ["GRAND"])
    print()
    print("  %d appariés, %d grands qui ne s'incarnent pas, %d sans corps plausible"
          % (len(faits), grands, len(propositions) - len(faits) - grands))
    if not vraiment:
        print("  (rien écrit — ajoute --vraiment)")
        return
    for p, g in faits:
        L["liens"][g[C["id"]]] = p["id"]
    ecrire(LIENS, L)
    print("  écrit dans etat/corps.json")


def loger(G, C, L, pid, ou, vraiment, monde=_bati.DEFAUT):
    """Créer un corps pour un personnage, dans un bâtiment donné.

    `ou` est un index de bâtiment, ou le nom d'un usage — « donjon-rouge »,
    « fosse-dragons » — auquel cas on prend le premier bâtiment de cet usage.
    `monde` dit dans QUEL bâti engendré on cherche cet index : Peyredragon a
    ses propres bâtiments, et son 12 n'est pas celui de Port-Réal.
    Le corps ainsi créé n'est pas dans les cellules engendrées : il vit dans
    `etat/corps.json`, il survit aux regénérations, et le rendu le pose par
    dessus la foule.
    """
    P = json.load(io.open(PERSOS, encoding="utf-8"))
    liste = P if isinstance(P, list) else P.get("personnages", [])
    p = next((x for x in liste if x.get("id") == pid), None)
    if not p: sortir("  aucun personnage de cet id : %s" % pid)
    if any(c.get("personnage_id") == pid for c in L["corps"]):
        sortir("  %s a déjà un corps créé — retire-le d'abord." % pid)

    try:
        BB, CB = _bati.charger(monde)
    except _bati.MondeInconnu as e:
        sortir("  %s" % e)
    if ou.isdigit():
        k = int(ou)
        if k >= len(BB): sortir("  pas de bâtiment n° %d dans « %s »" % (k, monde))
    else:
        k = next((i for i, b in enumerate(BB) if b[CB["usage"]] == ou), None)
        if k is None:
            sortir("  aucun bâtiment d'usage « %s » dans « %s »" % (ou, monde))
    b = BB[k]
    neuf = {
        "personnage_id": pid, "bat": k, "usage": b[CB["usage"]],
        "quartier": b[CB["quartier"]],
        "role": (p.get("titre") or "").split(",")[0][:40],
        # au centre de l'édifice, au sol : ce n'est pas une position de scène,
        # c'est une ADRESSE. Où il se tient à la minute près relève de
        # scripts/presence.py, comme au château.
        "x": b[CB["x"]], "y": b[CB["y"]], "z": b[CB["z"]],
    }
    # Comme pour les affectations : l'absence du champ VAUT portreal, donc on
    # ne l'écrit que lorsqu'il dit quelque chose.
    if monde != _bati.DEFAUT: neuf["monde"] = monde
    print("  %s -> %s (%s, %s), bâtiment %d%s"
          % (pid, neuf["role"], neuf["usage"], neuf["quartier"], k,
             "" if monde == _bati.DEFAUT else " de « %s »" % monde))
    if not vraiment:
        print("  (rien écrit — ajoute --vraiment)")
        return
    L["corps"].append(neuf)
    ecrire(LIENS, L)
    print("  écrit dans etat/corps.json")


def main():
    a = sys.argv[1:]
    def opt(nom, n=1):
        if nom not in a: return None
        i = a.index(nom)
        return a[i+1:i+1+n]
    vraiment = "--vraiment" in a

    G, C = charger_gens()
    L = charger_liens()

    # --- l'état -------------------------------------------------------------
    if not a:
        print("  %s corps engendrés en %d cellules de %d m, %d liés à un personnage"
              % (format(G["total"], ",d").replace(",", " "), len(G["cellules"]),
                 G.get("cellule_m", 250), len(L["liens"])))
        for acteur, perso in sorted(L["liens"].items()):
            print("   %-40s -> %s" % (acteur, perso))
        print()
        print("  python scripts/corps.py --chercher --role tavernier")
        return

    # --- consulter ----------------------------------------------------------
    if opt("--qui"):
        aid = opt("--qui")[0]
        g = par_identifiant(G, C, aid)
        if not g: sortir("  aucun corps de cet id : %s" % aid)
        print(fiche(G, C, g, L))
        return

    if opt("--ou"):
        pid = opt("--ou")[0]
        aids = [k for k, v in L["liens"].items() if v == pid]
        if not aids:
            print("  %s n'a pas de corps — aucune adresse dans Port-Réal." % pid)
            return
        for aid in aids:
            g = par_identifiant(G, C, aid)
            print(fiche(G, C, g, L) if g else
                  "  %s -> %s (corps disparu : la ville a été regénérée)" % (aid, pid))
        return

    if "--chercher" in a:
        role = (opt("--role") or [None])[0]
        usage = (opt("--usage") or [None])[0]
        quartier = (opt("--quartier") or [None])[0]
        rang = (opt("--rang") or [None])[0]
        combien = int((opt("--n") or ["12"])[0])
        trouves = []
        for g in tous(G):
            if role and g[C["role"]] != role: continue
            if usage and g[C["usage"]] != usage: continue
            if rang and g[C["rang"]] != rang: continue
            if quartier and sans_accent(quartier) not in sans_accent(g[C["quartier"]]):
                continue
            trouves.append(g)
            if len(trouves) >= combien: break
        if not trouves:
            print("  personne. (rôles connus : %s)"
                  % ", ".join(sorted(G["_roles"])[:20]))
            return
        for g in trouves:
            print(fiche(G, C, g, L)); print()
        return

    # --- lier ---------------------------------------------------------------
    if opt("--lier", 2):
        aid, pid = opt("--lier", 2)
        g = par_identifiant(G, C, aid)
        if not g: sortir("  aucun corps de cet id : %s" % aid)
        P = json.load(io.open(PERSOS, encoding="utf-8"))
        liste = P if isinstance(P, list) else P.get("personnages", [])
        if not any(x.get("id") == pid for x in liste):
            sortir("  aucun personnage de cet id : %s" % pid)
        deja = L["liens"].get(aid)
        if deja and deja != pid:
            sortir("  ce corps est déjà celui de %s — délie-le d'abord." % deja)
        print(fiche(G, C, g, L))
        print("  -> %s prendrait ce corps." % pid)
        if not vraiment:
            print("  (rien écrit — ajoute --vraiment)"); return
        L["liens"][aid] = pid
        ecrire(LIENS, L)
        print("  écrit dans etat/corps.json")
        return

    # --- loger : CRÉER un corps pour qui n'en emprunte pas ------------------
    if opt("--loger", 2):
        pid, ou = opt("--loger", 2)
        return loger(G, C, L, pid, ou, vraiment,
                     (opt("--monde") or [_bati.DEFAUT])[0])

    # --- incarner : donner un corps à tous les acteurs de la ville ----------
    if "--incarner" in a:
        return incarner(G, C, L, vraiment, (opt("--lieu") or ["port-real"])[0])

    if opt("--delier"):
        aid = opt("--delier")[0]
        if aid not in L["liens"]: sortir("  ce corps n'est lié à personne.")
        if not vraiment:
            print("  %s -> %s serait défait (ajoute --vraiment)" % (aid, L["liens"][aid])); return
        pid = L["liens"].pop(aid)
        ecrire(LIENS, L)
        print("  %s n'a plus de corps." % pid)
        return

    # --- promouvoir : un corps devient un personnage -------------------------
    if opt("--promouvoir"):
        aid = opt("--promouvoir")[0]
        g = par_identifiant(G, C, aid)
        if not g: sortir("  aucun corps de cet id : %s" % aid)
        if aid in L["liens"]:
            sortir("  ce corps est déjà celui de %s." % L["liens"][aid])
        r = G["_roles"].get(g[C["role"]], {})
        pid = aid
        naissance = 129 - int(g[C["age"]])
        neuf = {
            "id": pid,
            "nom": g[C["nom"]],
            "maison_id": None,
            "titre": r.get("nom", g[C["role"]]),
            "naissance": naissance,
            "traits": [],
            "objectifs": [],
            "maniere": "",
            "portrait": {"fichier": "", "physique": "", "prompt_ideogram": ""},
            "etat": "dormant",
            "lieu_id": "port-real",
            "condition": "libre",
        }
        print(fiche(G, C, g, L))
        print("  -> fiche à créer : %s (%s, né en %d)" % (pid, neuf["titre"], naissance))
        if not vraiment:
            print("  (rien écrit — ajoute --vraiment, puis remplis traits/maniere à la main)")
            return
        P = json.load(io.open(PERSOS, encoding="utf-8"))
        liste = P if isinstance(P, list) else P.setdefault("personnages", [])
        if any(x.get("id") == pid for x in liste):
            sortir("  un personnage porte déjà cet id : %s" % pid)
        liste.append(neuf)
        ecrire(PERSOS, P)
        L["liens"][aid] = pid
        ecrire(LIENS, L)
        print("  écrit dans etat/personnages.json et etat/corps.json")
        print("  reste à écrire à la main : traits, maniere, objectifs.")
        return

    sortir(__doc__)


if __name__ == "__main__":
    main()
