"""Applique une proposition de etat/staging/ a etat/*.json.

Usage :
    python scripts/appliquer.py tick-20260806-024652.json              -> blanc
    python scripts/appliquer.py tick-20260806-024652.json --vraiment   -> ecrit
    python scripts/appliquer.py <fichier> --vraiment --forcer          -> passe outre
                                                                          les gardes

Le pendant de scripts/tick.py. Le tick CALCULE et propose ; celui-ci APPLIQUE ce
que le MJ a validé. Entre les deux, le MJ relit la proposition et ajoute a la main
ses mutations narratives dans la liste "mutations_proposees" — ce que produit une
etape tombee, la croyance qu'une nouvelle installe, la tete qu'il vient de reecrire.

Trois gardes, dans cet ordre :
1. EMPREINTES — la proposition porte le sha1 des tables lues au moment du calcul.
   Si une table a bouge depuis, un autre ecrivain est passe : on refuse. C'est la
   protection contre deux sessions qui jouent en meme temps (voir CLAUDE.md).
2. VALIDATION — tout est verifie avant que rien ne soit ecrit : cible existante,
   operation connue, champs autorises, valeurs dans les enums. Une seule mutation
   invalide annule le lot entier.
3. ATOMICITE — ecriture par fichier temporaire puis remplacement, et le fichier de
   proposition est marque "applique_le" pour qu'on ne l'applique pas deux fois.

Vocabulaire des mutations — FERME, et c'est voulu : pas de chemin JSON arbitraire,
sinon n'importe quelle faute de frappe corrompt l'etat en silence.

    {table: "intentions", cible: <personnage_id>, operation: ...}
        etape            + etape: <id>, champs: {etat|jours_restants|quoi|cout|
                                                 si_bloque|depend_de|accompli}
        etape_ajouter    + valeur: <objet etape complet>
        tete             + champs: {echelle|intention|attitude_joueur|date_maj}
        croyance_ajouter | croyance_retirer   + valeur: <texte>
        ignore_ajouter   | ignore_retirer     + valeur: <texte>

    {table: "intentions", operation: "tete_ajouter", valeur: <objet intention>}
        CREE la tete d'un personnage qui n'en a pas encore (un dormant qu'on
        promeut). Pas de "cible" — le personnage_id est dans la valeur ; s'il y
        en a une, elle doit correspondre. La valeur porte personnage_id,
        echelle, croyances, intention, plan, date_maj (requis), et ignore,
        declencheurs, attitude_joueur (attendus). Refuse : une tete deja
        existante, un personnage inconnu de personnages.json, le personnage
        joueur (sa tete appartient au joueur), une echelle hors enumeration,
        une etape mal formee ou dont l'id est deja pris ailleurs dans le
        fichier, et tout depassement des budgets de l'echelle (docs/schema.md).

    {table: "evenements", cible: <evenement_id>, operation: ...}
        diffusion_livree   + index: <n>
        diffusion_ajouter  + valeur: <objet diffusion>
        evenement          + champs: {statut|effets|date_prevue|importance}

    {table: "personnages", cible: <personnage_id>, operation: "personnage",
     champs: {lieu_id|condition|etat}}

    {table: "monde", operation: "monde", champs: {date|tension|phase}}

Chaque mutation accepte un champ libre "pourquoi", ignore a l'application mais
precieux a la relecture.

Doc : docs/schema.md
"""
import argparse
import hashlib
import io
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(SCRIPTS)
ETAT = os.path.join(RACINE, "etat")
STAGING = os.path.join(ETAT, "staging")

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

try:
    # Une seule table de budgets pour les deux scripts : celle de tick.py,
    # qui transcrit docs/schema.md.
    from tick import BUDGETS
except ImportError:     # doublon de secours, a retoucher AVEC celui de tick.py
    BUDGETS = {
        "scene":   {"acteurs": 5,  "croyances": 6, "etapes": 5,
                    "declencheurs": 3},
        "orbite":  {"acteurs": 10, "croyances": 5, "etapes": 4,
                    "declencheurs": 2},
        "royaume": {"acteurs": None, "croyances": 3, "etapes": 2,
                    "declencheurs": 1},
    }

ETATS_ETAPE = ("en-cours", "fait", "bloque", "abandonne")
ETATS_ETAPE_VIVANTS = ("en-cours", "bloque")
ECHELLES = ("scene", "orbite", "royaume")
STATUTS_EVENEMENT = ("a-venir", "resolu", "devie", "annule")
ETATS_PERSO = ("actif", "dormant", "mort")

CHAMPS_ETAPE = ("etat", "jours_restants", "quoi", "cout", "si_bloque",
                "depend_de", "accompli")
CHAMPS_TETE = ("echelle", "intention", "attitude_joueur", "date_maj")
CHAMPS_TETE_REQUIS = ("personnage_id", "echelle", "croyances", "intention",
                      "plan", "date_maj")
CHAMPS_EVENEMENT = ("statut", "effets", "date_prevue", "importance")
CHAMPS_PERSO = ("lieu_id", "condition", "etat")
CHAMPS_MONDE = ("date", "tension", "phase")

OPERATIONS = {
    "intentions": ("etape", "etape_ajouter", "tete", "tete_ajouter",
                   "croyance_ajouter", "croyance_retirer", "ignore_ajouter",
                   "ignore_retirer"),
    "evenements": ("diffusion_livree", "diffusion_ajouter", "evenement"),
    "personnages": ("personnage",),
    "monde": ("monde",),
}


# ------------------------------------------------------------------ lecture

def lire(nom):
    chemin = os.path.join(ETAT, nom + ".json")
    if not os.path.isfile(chemin):
        sys.exit("etat/{}.json absent".format(nom))
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


def empreinte(nom):
    chemin = os.path.join(ETAT, nom + ".json")
    if not os.path.isfile(chemin):
        return None
    with io.open(chemin, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


def par_id(table, cle="id"):
    return {x.get(cle): x for x in table if isinstance(x, dict)}


# --------------------------------------------------------------- validation

def date_lisible(date):
    """Vrai si c'est bien un {annee, lune, jour} d'entiers."""
    if not isinstance(date, dict):
        return False
    return all(isinstance(date.get(c), int) for c in ("annee", "lune", "jour"))


def valider_tete_neuve(v, cible, tetes, personnages, joueur, ids_etapes):
    """Une tete neuve est-elle recevable ? Rend un message, ou None si oui.

    Tout est verifie ici : rien n'est ecrit avant que le lot entier passe.
    """
    if not isinstance(v, dict):
        return "tete a ajouter : 'valeur' doit etre l'objet intention complet"
    manquants = [c for c in CHAMPS_TETE_REQUIS if not v.get(c)]
    if manquants:
        return "tete a ajouter incomplete, il manque : {}".format(
            ", ".join(manquants))

    pid = v["personnage_id"]
    if cible is not None and cible != pid:
        return ("'cible' {!r} ne correspond pas au personnage_id {!r} de la "
                "tete".format(cible, pid))
    if pid in tetes:
        return ("une tete existe deja pour {} — patche-la (tete, etape, "
                "croyance_ajouter), ne la recree pas".format(pid))
    if pid not in personnages:
        return "personnage inconnu de personnages.json : {!r}".format(pid)
    if joueur and pid == joueur:
        return ("{} est le personnage joueur — sa tete appartient au joueur et "
                "n'a jamais d'entree dans intentions.json".format(pid))

    if v["echelle"] not in ECHELLES:
        return "echelle {!r} hors {}".format(v["echelle"], ECHELLES)
    if not date_lisible(v["date_maj"]):
        return "date_maj illisible (attendu {annee, lune, jour} d'entiers)"
    for liste in ("croyances", "ignore"):
        if v.get(liste) is not None and not isinstance(v.get(liste), list):
            return "{} doit etre une liste".format(liste)
    if not isinstance(v["plan"], list):
        return "plan doit etre une liste d'etapes"

    vus = set()
    for etape in v["plan"]:
        if not isinstance(etape, dict):
            return ("plan : etape en simple texte — il faut un objet horloge "
                    "(id, quoi, etat, jours_restants)")
        eid = etape.get("id")
        if not eid or not etape.get("quoi"):
            return "plan : etape sans id ou sans quoi"
        if eid in ids_etapes or eid in vus:
            return "id d'etape deja pris : {}".format(eid)
        vus.add(eid)
        if etape.get("etat") not in ETATS_ETAPE:
            return "etape {} : etat {!r} hors {}".format(
                eid, etape.get("etat"), ETATS_ETAPE)
        if "jours_restants" not in etape:
            return ("etape {} : jours_restants requis (entier, ou null pour "
                    "une posture permanente)".format(eid))
        jr = etape["jours_restants"]
        if jr is not None and not isinstance(jr, int):
            return "etape {} : jours_restants doit etre un entier ou null".format(
                eid)

    decl = v.get("declencheurs") or []
    if not isinstance(decl, list):
        return "declencheurs doit etre une liste"
    for d in decl:
        if not isinstance(d, dict) or not d.get("si") or not d.get("alors"):
            return "declencheur sans 'si' ou sans 'alors'"

    # budgets de l'echelle — la table est dans docs/schema.md
    budget = BUDGETS[v["echelle"]]
    trop = []
    n_croyances = len(v.get("croyances") or [])
    if n_croyances > budget["croyances"]:
        trop.append("{} croyances pour {}".format(n_croyances,
                                                  budget["croyances"]))
    vivantes = [e for e in v["plan"] if e.get("etat") in ETATS_ETAPE_VIVANTS]
    if len(vivantes) > budget["etapes"]:
        trop.append("{} etapes vivantes pour {}".format(len(vivantes),
                                                        budget["etapes"]))
    if len(decl) > budget["declencheurs"]:
        trop.append("{} declencheurs pour {}".format(len(decl),
                                                     budget["declencheurs"]))
    if trop:
        return "budget '{}' depasse : {}".format(v["echelle"], " ; ".join(trop))
    return None


def valider(mutations, tables):
    """Rend (plan, erreurs). Le plan decrit ce qui changerait, sans rien changer."""
    plan, erreurs = [], []
    tetes = par_id(tables["intentions"], "personnage_id")
    evenements = par_id(tables["evenements"])
    personnages = par_id(tables["personnages"])
    joueur = (tables.get("journal") or {}).get("personnage_joueur_id")
    # tous les ids d'etapes du fichier — grossit au fil du lot, pour qu'une
    # etape ajoutee deux fois dans la meme proposition soit refusee aussi.
    ids_etapes = {e.get("id") for t in tables["intentions"]
                  for e in (t.get("plan") or [])
                  if isinstance(e, dict) and e.get("id")}

    def faute(i, message):
        erreurs.append("mutation {} : {}".format(i, message))

    for i, m in enumerate(mutations, 1):
        if not isinstance(m, dict):
            faute(i, "n'est pas un objet")
            continue
        table, op = m.get("table"), m.get("operation")
        if table not in OPERATIONS:
            faute(i, "table inconnue : {!r}".format(table))
            continue
        if op not in OPERATIONS[table]:
            faute(i, "operation {!r} inconnue pour la table {}".format(op, table))
            continue
        cible = m.get("cible")
        champs = m.get("champs") or {}
        avant, apres = None, None

        # --- intentions
        if table == "intentions":
            if op == "tete_ajouter":
                v = m.get("valeur")
                souci = valider_tete_neuve(v, cible, tetes, personnages,
                                           joueur, ids_etapes)
                if souci:
                    faute(i, souci)
                    continue
                # la tete neuve devient patchable par la suite du meme lot
                tetes[v["personnage_id"]] = v
                ids_etapes.update(e["id"] for e in v["plan"])
                plan.append({"n": i, "mutation": m, "avant": None, "apres": {
                    "tete_ajoutee": v["personnage_id"],
                    "echelle": v["echelle"],
                    "croyances": len(v.get("croyances") or []),
                    "etapes": len(v["plan"]),
                    "declencheurs": len(v.get("declencheurs") or []),
                }})
                continue
            tete = tetes.get(cible)
            if tete is None:
                faute(i, "aucune tete pour {!r}".format(cible))
                continue
            if op == "etape":
                etapes = {e.get("id"): e for e in (tete.get("plan") or [])
                          if isinstance(e, dict)}
                etape = etapes.get(m.get("etape"))
                if etape is None:
                    faute(i, "{} n'a pas d'etape {!r}".format(
                        cible, m.get("etape")))
                    continue
                mauvais = [c for c in champs if c not in CHAMPS_ETAPE]
                if mauvais:
                    faute(i, "champs d'etape interdits : {}".format(
                        ", ".join(mauvais)))
                    continue
                if "etat" in champs and champs["etat"] not in ETATS_ETAPE:
                    faute(i, "etat d'etape {!r} hors {}".format(
                        champs["etat"], ETATS_ETAPE))
                    continue
                if "jours_restants" in champs:
                    jr = champs["jours_restants"]
                    if jr is not None and not isinstance(jr, int):
                        faute(i, "jours_restants doit etre un entier ou null")
                        continue
                avant = {c: etape.get(c) for c in champs}
                apres = dict(champs)
            elif op == "etape_ajouter":
                v = m.get("valeur")
                if not isinstance(v, dict) or not v.get("id") or not v.get("quoi"):
                    faute(i, "etape a ajouter incomplete (id et quoi requis)")
                    continue
                if v["id"] in ids_etapes:
                    faute(i, "id d'etape deja pris : {}".format(v["id"]))
                    continue
                ids_etapes.add(v["id"])
                apres = {"etape_ajoutee": v["id"]}
            elif op == "tete":
                mauvais = [c for c in champs if c not in CHAMPS_TETE]
                if mauvais:
                    faute(i, "champs de tete interdits : {}".format(
                        ", ".join(mauvais)))
                    continue
                if "echelle" in champs and champs["echelle"] not in ECHELLES:
                    faute(i, "echelle {!r} hors {}".format(
                        champs["echelle"], ECHELLES))
                    continue
                avant = {c: tete.get(c) for c in champs}
                apres = dict(champs)
            else:  # croyance_* / ignore_*
                liste = "croyances" if op.startswith("croyance") else "ignore"
                v = m.get("valeur")
                if not isinstance(v, str) or not v.strip():
                    faute(i, "valeur textuelle requise")
                    continue
                courant = tete.get(liste) or []
                if op.endswith("retirer") and v not in courant:
                    faute(i, "{} n'a pas cette entree dans {}".format(cible, liste))
                    continue
                apres = {liste: ("+ " if op.endswith("ajouter") else "- ") + v}

        # --- evenements
        elif table == "evenements":
            ev = evenements.get(cible)
            if ev is None:
                faute(i, "aucun evenement {!r}".format(cible))
                continue
            if op == "diffusion_livree":
                diff = ev.get("diffusion") or []
                idx = m.get("index")
                if not isinstance(idx, int) or not 0 <= idx < len(diff):
                    faute(i, "index de diffusion hors bornes : {!r}".format(idx))
                    continue
                if diff[idx].get("livree") is True:
                    faute(i, "diffusion {} de {} deja livree".format(idx, cible))
                    continue
                apres = {"diffusion[{}].livree".format(idx): True}
            elif op == "diffusion_ajouter":
                v = m.get("valeur")
                if not isinstance(v, dict) or not v.get("date") \
                        or not (v.get("ou") or v.get("qui")):
                    faute(i, "diffusion a ajouter incomplete (date, et ou/qui)")
                    continue
                apres = {"diffusion": "+1 entree le {}".format(
                    v["date"].get("jour"))}
            else:  # evenement
                mauvais = [c for c in champs if c not in CHAMPS_EVENEMENT]
                if mauvais:
                    faute(i, "champs d'evenement interdits : {}".format(
                        ", ".join(mauvais)))
                    continue
                if "statut" in champs and champs["statut"] not in STATUTS_EVENEMENT:
                    faute(i, "statut {!r} hors {}".format(
                        champs["statut"], STATUTS_EVENEMENT))
                    continue
                avant = {c: ev.get(c) for c in champs}
                apres = dict(champs)

        # --- personnages
        elif table == "personnages":
            perso = personnages.get(cible)
            if perso is None:
                faute(i, "aucun personnage {!r}".format(cible))
                continue
            mauvais = [c for c in champs if c not in CHAMPS_PERSO]
            if mauvais:
                faute(i, "champs de personnage interdits : {}".format(
                    ", ".join(mauvais)))
                continue
            if "etat" in champs and champs["etat"] not in ETATS_PERSO:
                faute(i, "etat {!r} hors {}".format(champs["etat"], ETATS_PERSO))
                continue
            avant = {c: perso.get(c) for c in champs}
            apres = dict(champs)

        # --- monde
        else:
            mauvais = [c for c in champs if c not in CHAMPS_MONDE]
            if mauvais:
                faute(i, "champs de monde interdits : {}".format(
                    ", ".join(mauvais)))
                continue
            avant = {c: tables["monde"].get(c) for c in champs}
            apres = dict(champs)

        plan.append({"n": i, "mutation": m, "avant": avant, "apres": apres})

    return plan, erreurs


# --------------------------------------------------------------- application

def appliquer(plan, tables):
    """Mute les structures en memoire. Rend l'ensemble des tables touchees."""
    touchees = set()
    tetes = par_id(tables["intentions"], "personnage_id")
    evenements = par_id(tables["evenements"])
    personnages = par_id(tables["personnages"])

    for ligne in plan:
        m = ligne["mutation"]
        table, op = m["table"], m["operation"]
        cible, champs = m.get("cible"), m.get("champs") or {}
        touchees.add(table)

        if table == "intentions":
            if op == "tete_ajouter":
                neuve = m["valeur"]
                tables["intentions"].append(neuve)
                tetes[neuve["personnage_id"]] = neuve
                continue
            tete = tetes[cible]
            if op == "etape":
                etape = next(e for e in tete["plan"] if e.get("id") == m["etape"])
                etape.update(champs)
            elif op == "etape_ajouter":
                tete.setdefault("plan", []).append(m["valeur"])
            elif op == "tete":
                tete.update(champs)
            else:
                liste = "croyances" if op.startswith("croyance") else "ignore"
                tete.setdefault(liste, [])
                if op.endswith("ajouter"):
                    tete[liste].append(m["valeur"])
                else:
                    tete[liste].remove(m["valeur"])
        elif table == "evenements":
            ev = evenements[cible]
            if op == "diffusion_livree":
                ev["diffusion"][m["index"]]["livree"] = True
            elif op == "diffusion_ajouter":
                ev.setdefault("diffusion", []).append(m["valeur"])
            else:
                ev.update(champs)
        elif table == "personnages":
            personnages[cible].update(champs)
        else:
            tables["monde"].update(champs)

    return touchees


def ecrire(nom, donnees):
    """Ecriture atomique : fichier temporaire puis remplacement."""
    chemin = os.path.join(ETAT, nom + ".json")
    temporaire = chemin + ".tmp"
    with io.open(temporaire, "w", encoding="utf-8", newline="\r\n") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(temporaire, chemin)


# ---------------------------------------------------------------------- main

def resumer(plan):
    for ligne in plan:
        m = ligne["mutation"]
        tete = "  {:>3}. {} {}".format(ligne["n"], m["table"],
                                       m.get("cible") or "")
        print("{} — {}".format(tete, m["operation"]))
        if ligne["avant"]:
            print("        avant : {}".format(
                json.dumps(ligne["avant"], ensure_ascii=False)))
        if ligne["apres"]:
            print("        apres : {}".format(
                json.dumps(ligne["apres"], ensure_ascii=False)))
        if m.get("pourquoi"):
            print("        motif : {}".format(m["pourquoi"]))


def main():
    a = argparse.ArgumentParser(
        description="Applique une proposition de etat/staging/ a etat/*.json.")
    a.add_argument("proposition",
                   help="nom du fichier dans etat/staging/ (ou chemin complet)")
    a.add_argument("--vraiment", action="store_true",
                   help="ecrire pour de bon (sans quoi : blanc)")
    a.add_argument("--forcer", action="store_true",
                   help="passer outre les empreintes et le deja-applique")
    args = a.parse_args()

    chemin = args.proposition
    if not os.path.isfile(chemin):
        chemin = os.path.join(STAGING, args.proposition)
    if not os.path.isfile(chemin):
        sys.exit("proposition introuvable : {}".format(args.proposition))
    with io.open(chemin, encoding="utf-8") as f:
        prop = json.load(f)

    mutations = prop.get("mutations_proposees") or []
    if not mutations:
        sys.exit("aucune mutation dans 'mutations_proposees' — rien a appliquer.")

    if prop.get("applique_le") and not args.forcer:
        sys.exit("proposition deja appliquee le {} — --forcer pour recommencer."
                 .format(prop["applique_le"]))

    # garde 1 : l'etat n'a pas bouge depuis le calcul
    derives = [nom for nom, sceau in (prop.get("empreintes") or {}).items()
               if empreinte(nom) != sceau]
    if derives:
        message = ("l'etat a change depuis le calcul de cette proposition : {}. "
                   "Un autre ecrivain est passe — relance le tick."
                   .format(", ".join(sorted(derives))))
        if not args.forcer:
            sys.exit("REFUS : " + message)
        print("AVERTISSEMENT (forcé) : " + message + "\n")

    # journal n'est jamais mutable : il sert a proteger la tete du joueur.
    tables = {nom: lire(nom) for nom in
              ("intentions", "evenements", "personnages", "monde", "journal")}

    # garde 2 : tout valider avant de rien ecrire
    plan, erreurs = valider(mutations, tables)
    print("Proposition : {}".format(os.path.basename(chemin)))
    print("{} mutation(s), {} valide(s), {} en erreur\n".format(
        len(mutations), len(plan), len(erreurs)))
    resumer(plan)
    if erreurs:
        print("\n== ERREURS ({}) — rien n'a ete ecrit ==".format(len(erreurs)))
        for e in erreurs:
            print("  " + e)
        return 1

    if not args.vraiment:
        print("\nBlanc : rien n'a ete ecrit. Relance avec --vraiment pour appliquer.")
        return 0

    # garde 3 : ecriture atomique, puis marquage de la proposition
    touchees = appliquer(plan, tables)
    for nom in sorted(touchees):
        ecrire(nom, tables[nom])
    prop["applique_le"] = datetime.now().isoformat(timespec="seconds")
    with io.open(chemin, "w", encoding="utf-8", newline="\r\n") as f:
        json.dump(prop, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("\nApplique. Tables ecrites : {}".format(", ".join(sorted(touchees))))
    print("Verifie la coherence : python scripts/tick.py --verifier")
    return 0


if __name__ == "__main__":
    sys.exit(main())
