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

    {table: "activites", cible: <activite_id>, operation: ...}   (les mains)
        mesure     + mesure: <mesure_id>, champs: {valeur|reliquat}  ENTIERS SEULS
        seuil      + seuil:  <seuil_id>,  champs: {franchi_le}
        activite   + champs: {mandat|porteur|dernier_rapport|date_maj|salle}
        Le reste d'une activite (quoi, rythme, plancher, plafond, depend_de,
        libelle des seuils) s'ecrit a la main : ce sont des choix de conception,
        pas des mutations de partie.

    {table: "plis", cible: <pli_id>, operation: ...}   (le courrier)
        pli         + champs: {etat|main|attendu_le|canal|scelle|porte}
        Un pli remis, ouvert ou retenu DOIT avoir une main : c'est tout
        l'interet de la table (docs/plis.md). Un pli en route n'en a pas.
    {table: "plis", operation: "pli_ajouter", valeur: <objet pli complet>}
        Requiert id, canal, porte, de, pour, vers, parti_le, attendu_le, etat.
        `porte` est le texte FIGE au depart : on ne le relit pas a l'arrivee.

    {table: "jetons", cible: <incident_id>, operation: ...}   (la rumeur)
        incident_propage  + valeur: {ou, date, certitude, contenu, ames?,
                                     depuis?, note?}
            AJOUTE un endroit gagne a l'incident (docs/carte.md). `contenu` est
            OBLIGATOIRE et non vide : c'est ce qui se dit LA-BAS, deforme. Le
            tick propose le saut avec contenu null — le lot est refuse tant que
            le MJ n'a pas ecrit la prose. Une machine ne fabrique pas de
            brouillard. La certitude doit avoir DECRU d'au moins un cran par
            rapport au foyer : rien ne devient plus vrai en se repetant.
        incident          + champs: {feu|certitude|statut|ames|contenu|detail}

    {table: "lieux", cible: <lieu_id>, operation: "roukerie",
     champs: {<lieu_id d'origine>: <entier >= 0>}}
        Le stock de corbeaux. Un oiseau ne vole que vers la ou il est ne :
        ecrire de A vers B consomme lieux[A].roukerie[B].

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
        "orbite":  {"acteurs": 12, "croyances": 5, "etapes": 4,
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
# les mains : seul tick.py pose valeur/reliquat, seul le MJ pose le reste
CHAMPS_MESURE = ("valeur", "reliquat")
CHAMPS_SEUIL = ("franchi_le",)
CHAMPS_ACTIVITE = ("mandat", "porteur", "dernier_rapport", "date_maj", "salle")
# le courrier (docs/plis.md)
CANAUX_PLI = ("corbeau", "cavalier", "barque")
ETATS_PLI = ("en-route", "remis", "ouvert", "retenu", "perdu", "intercepte")
ETATS_PLI_EN_MAIN = ("remis", "ouvert", "retenu")
CHAMPS_PLI = ("etat", "main", "attendu_le", "canal", "scelle", "porte")
CHAMPS_PLI_REQUIS = ("id", "canal", "porte", "de", "pour", "vers",
                     "parti_le", "attendu_le", "etat")
# la rumeur : un incident de la table de guerre (docs/carte.md)
CERTITUDES = ("sure", "rapportee", "rumeur")
FEUX = ("vif", "couve", "eteint")
CHAMPS_INCIDENT = ("feu", "certitude", "statut", "ames", "contenu", "detail")
CHAMPS_PROPAGE_REQUIS = ("ou", "date", "certitude", "contenu")

OPERATIONS = {
    "intentions": ("etape", "etape_ajouter", "tete", "tete_ajouter",
                   "croyance_ajouter", "croyance_retirer", "ignore_ajouter",
                   "ignore_retirer"),
    "evenements": ("diffusion_livree", "diffusion_ajouter", "evenement"),
    "personnages": ("personnage",),
    "monde": ("monde",),
    "activites": ("mesure", "seuil", "activite"),
    "plis": ("pli", "pli_ajouter"),
    "lieux": ("roukerie",),
    "jetons": ("incident_propage", "incident"),
}


def rang_certitude(valeur):
    """sure=2, rapportee=1, rumeur=0. Inconnu -> rapportee."""
    try:
        return len(CERTITUDES) - 1 - CERTITUDES.index(valeur)
    except ValueError:
        return 1


def liste_jetons(table):
    """jetons.json a une racine {jetons, traits, zones} ; on rend les pieces."""
    return table.get("jetons", []) if isinstance(table, dict) else table


# ------------------------------------------------------------------ lecture

# Les tables qui appartiennent a UN JOUEUR, pas au monde. Elles ne decrivent
# pas ce qui est : elles decrivent ce qu'un joueur CROIT. A deux, les partager
# revient a donner la table de guerre de la reine a sa maitresse de la voix —
# elles vivent donc dans etat/joueurs/<personnage_id>/.
CROYANCES = ("jetons", "vues", "objectifs")


def chemin_table(nom, joueur=None):
    """Le fichier d'une table — dans le dossier du joueur si c'en est une.

    Meme regle que scripts/ajouter.py, et meme refus bruyant : une fois la
    racine archivee, ecrire une croyance sans dire A QUI reviendrait a la
    poser dans un fichier fantome que le jeu ne relira jamais. C'est
    exactement le bug qu'on vient de corriger — on ne le laisse pas revenir.
    """
    if nom in CROYANCES:
        if joueur:
            p = os.path.join(ETAT, "joueurs", joueur, nom + ".json")
            if os.path.isfile(p):
                return p
        p = os.path.join(ETAT, nom + ".json")
        if os.path.isfile(p):
            return p
        if joueur:
            sys.exit(
                "pas de {}.json pour le joueur '{}', et plus de repli a la "
                "racine.\nVerifiez etat/joueurs/{}/ : le --joueur est-il le "
                "bon personnage_id ?".format(nom, joueur, joueur))
        sys.exit(
            "{}.json n'existe plus a la racine : cette table appartient a un "
            "joueur.\nPrecisez a qui vous ecrivez : --joueur <personnage_id>."
            .format(nom))
    return os.path.join(ETAT, nom + ".json")


def lire(nom, joueur=None):
    chemin = chemin_table(nom, joueur)
    if not os.path.isfile(chemin):
        sys.exit("{} absent".format(chemin))
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


def liste_activites(table):
    """activites.json a une racine {activites: [...]} ; on rend la liste."""
    return table.get("activites", []) if isinstance(table, dict) else table


def liste_plis(table):
    """plis.json a une racine {plis: [...]} ; on rend la liste."""
    return table.get("plis", []) if isinstance(table, dict) else table


def empreinte(nom, joueur=None):
    # Le sceau doit porter sur le fichier qu'on va REELLEMENT ecrire : sceller
    # la racine tout en ecrivant dans le dossier du joueur ne garde rien.
    chemin = (chemin_table(nom, joueur) if nom in CROYANCES
              else os.path.join(ETAT, nom + ".json"))
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
    activites = par_id(liste_activites(tables["activites"]))
    plis = par_id(liste_plis(tables["plis"]))
    incidents = par_id([j for j in liste_jetons(tables["jetons"])
                        if isinstance(j, dict) and j.get("genre") == "incident"])
    lieux = par_id(tables["lieux"])
    # alias compris : la couche carte impose ses propres ids (docs/schema.md)
    for lieu in tables["lieux"]:
        for alias in lieu.get("alias") or []:
            lieux.setdefault(alias, lieu)
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

        # --- activites (les mains)
        elif table == "activites":
            act = activites.get(cible)
            if act is None:
                faute(i, "aucune activite {!r}".format(cible))
                continue
            if op == "mesure":
                mes = next((x for x in (act.get("mesure") or [])
                            if x.get("id") == m.get("mesure")), None)
                if mes is None:
                    faute(i, "aucune mesure {!r} dans {}".format(
                        m.get("mesure"), cible))
                    continue
                mauvais = [c for c in champs if c not in CHAMPS_MESURE]
                if mauvais:
                    faute(i, "champs de mesure interdits : {} (seuls {} se "
                             "posent par mutation)".format(
                                 ", ".join(mauvais), "/".join(CHAMPS_MESURE)))
                    continue
                pasentier = [c for c in champs
                             if not isinstance(champs[c], int)]
                if pasentier:
                    faute(i, "{} doit etre un entier — les mains ne "
                             "connaissent pas les flottants".format(
                                 ", ".join(pasentier)))
                    continue
                avant = {c: mes.get(c) for c in champs}
                apres = dict(champs)
            elif op == "seuil":
                seuil = next((s for s in (act.get("seuils") or [])
                              if s.get("id") == m.get("seuil")), None)
                if seuil is None:
                    faute(i, "aucun seuil {!r} dans {}".format(
                        m.get("seuil"), cible))
                    continue
                mauvais = [c for c in champs if c not in CHAMPS_SEUIL]
                if mauvais:
                    faute(i, "champs de seuil interdits : {}".format(
                        ", ".join(mauvais)))
                    continue
                avant = {c: seuil.get(c) for c in champs}
                apres = dict(champs)
            else:
                mauvais = [c for c in champs if c not in CHAMPS_ACTIVITE]
                if mauvais:
                    faute(i, "champs d'activite interdits : {}".format(
                        ", ".join(mauvais)))
                    continue
                avant = {c: act.get(c) for c in champs}
                apres = dict(champs)

        # --- plis (le courrier)
        elif table == "plis":
            if op == "pli_ajouter":
                v = m.get("valeur")
                if not isinstance(v, dict):
                    faute(i, "pli a ajouter : 'valeur' doit etre l'objet pli")
                    continue
                manquants = [c for c in CHAMPS_PLI_REQUIS if not v.get(c)]
                if manquants:
                    faute(i, "pli a ajouter incomplet, il manque : {}".format(
                        ", ".join(manquants)))
                    continue
                if cible is not None and cible != v["id"]:
                    faute(i, "'cible' {!r} ne correspond pas a l'id {!r}".format(
                        cible, v["id"]))
                    continue
                if v["id"] in plis:
                    faute(i, "un pli {} existe deja — patche-le".format(v["id"]))
                    continue
                if v["canal"] not in CANAUX_PLI:
                    faute(i, "canal {!r} hors {}".format(v["canal"], CANAUX_PLI))
                    continue
                if v["etat"] not in ETATS_PLI:
                    faute(i, "etat {!r} hors {}".format(v["etat"], ETATS_PLI))
                    continue
                for champ in ("de", "pour"):
                    if v[champ] not in personnages:
                        faute(i, "{} inconnu : {!r}".format(champ, v[champ]))
                        break
                else:
                    if v["vers"] not in lieux:
                        faute(i, "'vers' inconnu : {!r}".format(v["vers"]))
                        continue
                    if v.get("depuis") and v["depuis"] not in lieux:
                        faute(i, "'depuis' inconnu : {!r}".format(v["depuis"]))
                        continue
                    if not date_lisible(v["parti_le"]) or \
                            not date_lisible(v["attendu_le"]):
                        faute(i, "parti_le / attendu_le illisibles (attendu "
                                 "{annee, lune, jour} d'entiers)")
                        continue
                    if v["etat"] in ETATS_PLI_EN_MAIN and not v.get("main"):
                        faute(i, "un pli {} doit avoir une 'main' : dis qui "
                                 "l'a".format(v["etat"]))
                        continue
                    if v.get("main") and v["main"] not in personnages:
                        faute(i, "'main' inconnue : {!r}".format(v["main"]))
                        continue
                    plis[v["id"]] = v
                    plan.append({"n": i, "mutation": m, "avant": None,
                                 "apres": {"pli_ajoute": v["id"],
                                           "vers": v["vers"],
                                           "attendu_le": v["attendu_le"]}})
                continue
            pli = plis.get(cible)
            if pli is None:
                faute(i, "aucun pli {!r}".format(cible))
                continue
            mauvais = [c for c in champs if c not in CHAMPS_PLI]
            if mauvais:
                faute(i, "champs de pli interdits : {}".format(
                    ", ".join(mauvais)))
                continue
            if "etat" in champs and champs["etat"] not in ETATS_PLI:
                faute(i, "etat {!r} hors {}".format(champs["etat"], ETATS_PLI))
                continue
            if "canal" in champs and champs["canal"] not in CANAUX_PLI:
                faute(i, "canal {!r} hors {}".format(champs["canal"], CANAUX_PLI))
                continue
            if "main" in champs and champs["main"] is not None \
                    and champs["main"] not in personnages:
                faute(i, "'main' inconnue : {!r}".format(champs["main"]))
                continue
            if "attendu_le" in champs and not date_lisible(champs["attendu_le"]):
                faute(i, "attendu_le illisible")
                continue
            # un pli en main doit avoir une main, apres coup comme avant
            etat_apres = champs.get("etat", pli.get("etat"))
            main_apres = champs.get("main", pli.get("main"))
            if etat_apres in ETATS_PLI_EN_MAIN and not main_apres:
                faute(i, "{} sans 'main' — un pli est toujours dans la main de "
                         "quelqu'un, et ce n'est pas forcement le 'pour'"
                         .format(etat_apres))
                continue
            avant = {c: pli.get(c) for c in champs}
            apres = dict(champs)

        # --- jetons : les incidents seulement (la rumeur)
        elif table == "jetons":
            inc = incidents.get(cible)
            if inc is None:
                faute(i, "aucun incident {!r} dans jetons.json (genre "
                         "'incident')".format(cible))
                continue
            if op == "incident":
                mauvais = [c for c in champs if c not in CHAMPS_INCIDENT]
                if mauvais:
                    faute(i, "champs d'incident interdits : {}".format(
                        ", ".join(mauvais)))
                    continue
                if "feu" in champs and champs["feu"] not in FEUX:
                    faute(i, "feu {!r} hors {}".format(champs["feu"], FEUX))
                    continue
                if "certitude" in champs and champs["certitude"] not in CERTITUDES:
                    faute(i, "certitude {!r} hors {}".format(
                        champs["certitude"], CERTITUDES))
                    continue
                avant = {c: inc.get(c) for c in champs}
                apres = dict(champs)
            else:   # incident_propage
                v = m.get("valeur")
                if not isinstance(v, dict):
                    faute(i, "'valeur' doit etre l'endroit gagne")
                    continue
                manquants = [c for c in CHAMPS_PROPAGE_REQUIS if not v.get(c)]
                if manquants:
                    faute(i, "saut incomplet, il manque : {} — 'contenu' est ce "
                             "qui se dit LA-BAS, deforme, et c'est a toi de "
                             "l'ecrire".format(", ".join(manquants)))
                    continue
                if v["ou"] not in lieux:
                    faute(i, "lieu inconnu : {!r}".format(v["ou"]))
                    continue
                if not date_lisible(v["date"]):
                    faute(i, "date illisible")
                    continue
                if v["certitude"] not in CERTITUDES:
                    faute(i, "certitude {!r} hors {}".format(v["certitude"],
                                                             CERTITUDES))
                    continue
                if rang_certitude(v["certitude"]) >= rang_certitude(
                        inc.get("certitude")):
                    faute(i, "certitude {!r} pas moins sure que le foyer ({!r}) "
                             "— rien ne devient plus vrai en se repetant".format(
                                 v["certitude"], inc.get("certitude")))
                    continue
                deja = [x.get("ou") if isinstance(x, dict) else x
                        for x in (inc.get("propage") or [])]
                if v["ou"] in deja:
                    faute(i, "{} a deja pris pour cet incident".format(v["ou"]))
                    continue
                apres = {"propage": "+ {} ({}) le {}".format(
                    v["ou"], v["certitude"], v["date"].get("jour"))}

        # --- lieux (la roukerie, et rien d'autre)
        elif table == "lieux":
            lieu = lieux.get(cible)
            if lieu is None:
                faute(i, "aucun lieu {!r}".format(cible))
                continue
            if not champs:
                faute(i, "roukerie : aucun champ — rien a poser")
                continue
            souci = None
            for origine, nb in champs.items():
                if origine not in lieux:
                    souci = "lieu d'origine inconnu : {!r}".format(origine)
                elif not isinstance(nb, int) or isinstance(nb, bool) or nb < 0:
                    souci = ("stock vers {} : entier positif attendu, {!r} "
                             "recu".format(origine, nb))
                if souci:
                    break
            if souci:
                faute(i, souci)
                continue
            stock = lieu.get("roukerie") or {}
            avant = {c: stock.get(c) for c in champs}
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
    activites = par_id(liste_activites(tables["activites"]))
    plis = par_id(liste_plis(tables["plis"]))
    incidents = par_id([j for j in liste_jetons(tables["jetons"])
                        if isinstance(j, dict) and j.get("genre") == "incident"])
    lieux = par_id(tables["lieux"])
    for lieu in tables["lieux"]:
        for alias in lieu.get("alias") or []:
            lieux.setdefault(alias, lieu)

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
        elif table == "activites":
            act = activites[cible]
            if op == "mesure":
                mes = next(x for x in act["mesure"]
                           if x.get("id") == m.get("mesure"))
                mes.update(champs)
            elif op == "seuil":
                seuil = next(s for s in act["seuils"]
                             if s.get("id") == m.get("seuil"))
                seuil.update(champs)
            else:
                act.update(champs)
        elif table == "plis":
            if op == "pli_ajouter":
                neuf = m["valeur"]
                liste_plis(tables["plis"]).append(neuf)
                plis[neuf["id"]] = neuf
            else:
                plis[cible].update(champs)
        elif table == "jetons":
            inc = incidents[cible]
            if op == "incident_propage":
                inc.setdefault("propage", []).append(m["valeur"])
            else:
                inc.update(champs)
        elif table == "lieux":
            lieux[cible].setdefault("roukerie", {}).update(champs)
        elif table == "personnages":
            personnages[cible].update(champs)
        else:
            tables["monde"].update(champs)

    return touchees


def ecrire(nom, donnees, joueur=None):
    """Ecriture atomique : fichier temporaire puis remplacement."""
    chemin = chemin_table(nom, joueur)
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
    a.add_argument("--joueur", default=None,
                   help="personnage_id du joueur dont on ecrit les croyances "
                        "(jetons, vues, objectifs). Requis des que la racine "
                        "est archivee.")
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

    # A QUI sont les croyances de ce lot : --joueur prime, sinon celui que
    # tick.py a inscrit dans la proposition au moment du calcul. Les deux
    # scripts doivent sceller et ecrire le MEME fichier.
    joueur = args.joueur or prop.get("joueur")
    if args.joueur and prop.get("joueur") and args.joueur != prop["joueur"]:
        sys.exit("REFUS : proposition calculee pour '{}', vous appliquez avec "
                 "--joueur '{}'.".format(prop["joueur"], args.joueur))

    # garde 1 : l'etat n'a pas bouge depuis le calcul
    derives = [nom for nom, sceau in (prop.get("empreintes") or {}).items()
               if empreinte(nom, joueur) != sceau]
    if derives:
        message = ("l'etat a change depuis le calcul de cette proposition : {}. "
                   "Un autre ecrivain est passe — relance le tick."
                   .format(", ".join(sorted(derives))))
        if not args.forcer:
            sys.exit("REFUS : " + message)
        print("AVERTISSEMENT (forcé) : " + message + "\n")

    # journal n'est jamais mutable : il sert a proteger la tete du joueur.
    tables = {nom: lire(nom) for nom in
              ("intentions", "evenements", "personnages", "monde", "journal",
               "lieux")}
    # plis.json est facultatif : une partie d'avant le courrier tourne encore
    if os.path.isfile(os.path.join(ETAT, "plis.json")):
        tables["plis"] = lire("plis")
    else:
        tables["plis"] = {"plis": []}
    if isinstance(tables["plis"], dict):
        tables["plis"].setdefault("plis", [])
    # jetons.json : la table de guerre, ou vivent les incidents (la rumeur).
    # C'est une CROYANCE : elle appartient au joueur, pas au monde. Sans
    # --joueur et sans repli racine, chemin_table refuse bruyamment plutot que
    # d'ecrire dans un fichier que le jeu ne relira jamais.
    # On ne resout le chemin QUE si le lot y touche : une proposition sans
    # incident ne doit pas reclamer un --joueur dont elle n'a que faire.
    if any(m.get("table") == "jetons" for m in mutations):
        tables["jetons"] = lire("jetons", joueur)
    else:
        racine_jetons = os.path.join(ETAT, "jetons.json")
        tables["jetons"] = (lire("jetons") if os.path.isfile(racine_jetons)
                            else {"jetons": []})
    # activites.json est facultatif : une partie sans mains tourne tres bien
    tables["activites"] = (lire("activites")
                           if os.path.isfile(
                               os.path.join(ETAT, "activites.json"))
                           else {"activites": []})

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
        ecrire(nom, tables[nom], joueur)
    prop["applique_le"] = datetime.now().isoformat(timespec="seconds")
    with io.open(chemin, "w", encoding="utf-8", newline="\r\n") as f:
        json.dump(prop, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("\nApplique. Tables ecrites : {}".format(", ".join(sorted(touchees))))
    print("Verifie la coherence : python scripts/tick.py --verifier")
    return 0


if __name__ == "__main__":
    sys.exit(main())
