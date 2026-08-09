# -*- coding: utf-8 -*-
# MESURER — ce qu'une journee de travail a rendu, et ce qui est arrive a la
# table. Le rapport que `travaux.py` ne peut pas donner : lui dit l'etat a
# l'instant, celui-ci dit le RENDEMENT sur une fenetre.
#
# POURQUOI. La chaine est ecrite (docs/travaux.md) :
#
#     une source touchee -> du travail -> des pensees datees
#                        -> une conclusion mure -> un message
#
# Chaque maillon a son fichier, et personne ne les regardait ensemble. Les
# etapes d'une journee dorment dans `etat/staging/travaux/<qui>.json` — champ
# `journal`, que AUCUN script ne lit. Les pensees vivent dans
# `etat/travaux.json`. Les messages reellement pousses sont dans
# `etat/flux.jsonl`. Tant que les trois ne sont pas mis cote a cote, on ne sait
# pas repondre a la seule question qui compte : QUEL TRAVAIL NOURRIT LA SALLE,
# ET LEQUEL TOURNE A VIDE.
#
# LES DEUX FAUTES QU'IL CHERCHE, et elles sont symetriques :
#   - un travail qui produit des pensees dont AUCUNE n'arrive a la table :
#     l'homme a travaille pour rien, ou le MJ n'a pas su s'en servir ;
#   - une replique qui n'a AUCUNE pensee derriere elle : c'est la faute que
#     tout l'edifice des travaux existe pour attraper — un homme qui commente
#     la salle parce que commenter la salle ressemble a avoir une raison
#     d'agir.
#
# LE RECOUPEMENT EST APPROCHE, ET C'EST ASSUME. On n'a pas de lien ecrit entre
# une replique et la pensee qui l'a produite — il faudrait l'ajouter au flux.
# En attendant, on recoupe par le VOCABULAIRE RARE : les mots qu'un texte
# partage avec une pensee et que presque personne d'autre n'emploie. Un chiffre,
# un nom propre, un metier. La rarete se mesure sur le corpus lui-meme (les
# mots frequents s'eliminent seuls), donc il n'y a pas de liste a tenir. C'est
# un indice, pas une preuve : le rapport le dit chaque fois qu'il le donne.
#
# CE SCRIPT N'ECRIT JAMAIS DANS etat/. Il lit et il compte.
#
# Usage :
#     python scripts/mesurer.py                 la fenetre du jour
#     python scripts/mesurer.py --jours 3       les trois derniers jours
#     python scripts/mesurer.py --qui gerardys  un seul homme
#     python scripts/mesurer.py --detail        les repliques et etapes en clair
import argparse
import io
import json
import math
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import travaux as mod_travaux  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
STAGING = os.path.join(ETAT, "staging", "travaux")

# ------------------------------------------------------------- les chiffres
# A l'essai, comme ceux de travaux.py. Tout est ici, en un bloc.

RECOUPEMENT = 3        # mots rares partages pour lier une replique a une pensee
RARETE = 0.08          # un mot est rare s'il est dans moins de 8% des textes
MOT_MIN = 4            # longueur minimale d'un mot retenu (les chiffres passent)
FENETRE = 1            # jours mesures par defaut, celui du monde inclus

JOURS_PAR_LUNE = 30
LUNES_PAR_AN = 12

# Ce qui compte comme « arrive a la table ». Un geste n'est pas une parole,
# mais c'est bien du travail qui sort : on le compte a part.
DIT = ("replique",)
FAIT = ("geste",)


# ---------------------------------------------------------------- outillage

def jour_absolu(date):
    """Meme convention que tick.py et travaux.py, au jour pres."""
    if not isinstance(date, dict):
        return None
    try:
        a = int(date.get("annee"))
        l = int(date.get("lune"))
        j = int(date.get("jour"))
    except (TypeError, ValueError):
        return None
    return (a * LUNES_PAR_AN + (l - 1)) * JOURS_PAR_LUNE + (j - 1)


def fmt(date):
    if not isinstance(date, dict):
        return "?"
    return "{}e j., {}e lune, an {}".format(
        date.get("jour", "?"), date.get("lune", "?"), date.get("annee", "?"))


def charger(nom, defaut):
    chemin = os.path.join(ETAT, nom + ".json")
    if not os.path.isfile(chemin):
        return defaut
    with io.open(chemin, encoding="utf-8") as fh:
        contenu = fh.read().strip()
    if not contenu:
        return defaut
    try:
        return json.loads(contenu)
    except ValueError as err:
        sys.exit("etat/{}.json illisible : {}".format(nom, err))


def plat(t):
    """Sans accents ni casse — pour comparer des mots, pas pour afficher."""
    t = unicodedata.normalize("NFD", t or "")
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def mots(texte):
    """Les mots d'un texte, gras d'appui et ponctuation retires.

    On garde les chiffres quelle que soit leur longueur : « 119 », « 26 » sont
    exactement le genre de trace qui relie une replique a la source qui l'a
    donnee.
    """
    t = plat(texte).replace("**", " ")
    out = set()
    for m in re.findall(r"[a-z0-9']+", t):
        m = m.strip("'")
        if m.isdigit() or len(m) >= MOT_MIN:
            out.add(m)
    return out


def pourcent(n, sur):
    return "{}%".format(int(round(100.0 * n / sur))) if sur else "-"


def tronque(t, n):
    t = re.sub(r"\s+", " ", (t or "").replace("**", "")).strip()
    return t if len(t) <= n else t[:n - 1] + "…"


# ------------------------------------------------------------- la collecte

def lire_travaux():
    brut = charger("travaux", {})
    return brut.get("travaux", []) if isinstance(brut, dict) else (brut or [])


def date_journee(d):
    """Le jour d'une journee deposee — deduit de ses pensees.

    Le fichier de staging ne porte AUCUNE date : c'est le dernier depot, un
    point c'est tout. Sans ce calcul, une fenetre de trois jours comparait un
    amont d'un seul jour a un aval de trois, et le rendement affiche etait faux
    d'un facteur trois. On prend donc le jour des pensees rendues, qui sont
    datees, elles.
    """
    jours = []
    for t in d.get("travaux") or []:
        for p in t.get("pensees") or []:
            j = jour_absolu(p.get("date"))
            if j is not None:
                jours.append(j)
    return max(jours) if jours else None


def lire_journees(debut, fin):
    """Les journees deposees en staging : `journal`, `rendu`, `cahier2`.

    C'est la seule source des ETAPES. Elle est facultative : sans elle, le
    rapport perd l'amont et le dit, il ne s'arrete pas.

    Rend (journees, hors_fenetre, sans_date, jours_couverts).
    """
    out, hors, muettes, couverts = {}, 0, 0, set()
    if not os.path.isdir(STAGING):
        return out, hors, muettes, couverts
    for nom in sorted(os.listdir(STAGING)):
        if not nom.endswith(".json"):
            continue
        chemin = os.path.join(STAGING, nom)
        try:
            with io.open(chemin, encoding="utf-8") as fh:
                d = json.load(fh)
        except ValueError:
            continue
        qui = d.get("qui") or nom[:-5]
        j = date_journee(d)
        if j is None:
            muettes += 1
            continue
        if not (debut <= j <= fin):
            hors += 1
            continue
        out[qui] = d
        couverts.add(j)
    return out, hors, muettes, couverts


def lire_flux(debut, fin):
    """Les items dates de la fenetre. Ceux sans date sont comptes a part.

    Un item non date ne peut pas etre place : le taire serait mentir sur la
    couverture de la mesure.
    """
    dedans, sans_date = [], 0
    chemin = os.path.join(ETAT, "flux.jsonl")
    if not os.path.isfile(chemin):
        return dedans, sans_date
    with io.open(chemin, encoding="utf-8") as fh:
        for ligne in fh:
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                item = json.loads(ligne)
            except ValueError:
                continue
            if item.get("type") not in DIT + FAIT:
                continue
            j = jour_absolu(item.get("date"))
            if j is None:
                sans_date += 1
                continue
            if debut <= j <= fin:
                dedans.append(item)
    return dedans, sans_date


def sterile(resultat):
    """Delegue a travaux.py — une seule definition pour toute la chaine."""
    return mod_travaux.sterile(resultat)


# ------------------------------------------------------------ le recoupement

def signatures(documents):
    """Le vocabulaire rare de chaque document, mesure sur le corpus lui-meme.

    Aucune liste de mots vides a tenir : « votre », « grace », « hommes »
    tombent d'eux-memes parce qu'ils sont partout. Ce qui reste est ce qui
    distingue — un chiffre, un nom, un metier, un lieu.
    """
    sacs = [mots(d) for d in documents]
    df = {}
    for sac in sacs:
        for m in sac:
            df[m] = df.get(m, 0) + 1
    plafond = max(2, int(math.ceil(RARETE * len(sacs))))
    return [set(m for m in sac if df[m] <= plafond) for sac in sacs]


def recouper(travaux, dits, par_id):
    """Pour chaque replique, le travail dont elle porte la trace.

    Rend (par_travail, orphelines) — `par_travail` : id -> [(item, score)], et
    `orphelines` : les repliques qu'aucune pensee n'explique.

    A CALCULER SUR TOUT LE CORPUS, toujours. La rarete d'un mot se mesure
    contre l'ensemble : restreindre a un homme avant de compter rendrait ses
    propres mots rares et lierait n'importe quoi a n'importe quoi. On filtre a
    l'affichage, jamais ici.
    """
    textes_t, index_t = [], []
    for trav in travaux:
        for p in trav.get("pensees") or []:
            textes_t.append(p.get("texte") or "")
            index_t.append(trav["id"])
        if trav.get("conclusion"):
            textes_t.append(trav["conclusion"])
            index_t.append(trav["id"])

    textes_r = [i.get("texte") or "" for i in dits]
    sigs = signatures(textes_t + textes_r)
    sigs_t, sigs_r = sigs[:len(textes_t)], sigs[len(textes_t):]

    par_travail, orphelines = {}, []
    for item, sig_r in zip(dits, sigs_r):
        qui = item.get("locuteur_id") or item.get("acteur_id")
        meilleur, score = None, 0
        for tid, sig_t in zip(index_t, sigs_t):
            # Un homme ne s'appuie que sur SES travaux : deux hommes qui parlent
            # de la meme affaire partagent le vocabulaire sans partager l'amont.
            if par_id[tid].get("qui") != qui:
                continue
            n = len(sig_r & sig_t)
            if n > score:
                meilleur, score = tid, n
        if meilleur and score >= RECOUPEMENT:
            par_travail.setdefault(meilleur, []).append((item, score))
        else:
            orphelines.append((item, score))
    return par_travail, orphelines


# ---------------------------------------------------------------- le rapport

def mesurer(travaux, journees, dits, faits, par_travail, orphelines):
    """Une ligne par homme, une par travail. Que du comptage."""
    hommes = {}
    for trav in travaux:
        qui = trav.get("qui")
        h = hommes.setdefault(qui, {
            "qui": qui, "travaux": [], "etapes": 0, "minutes": 0,
            "etapes_seches": 0, "journal": [], "rendu": None, "cahier2": 0})
        pensees = trav.get("pensees") or []
        lies = par_travail.get(trav["id"], [])
        h["travaux"].append({
            "id": trav["id"],
            "affaire": trav.get("affaire"),
            "etat": trav.get("etat"),
            "excitation": trav.get("excitation"),
            "pensees": len(pensees),
            "servies": sum(1 for p in pensees if p.get("servie")),
            "conclusion": bool(trav.get("conclusion")),
            "livre": trav.get("livre"),
            "repliques": lies,
        })

    for qui, d in journees.items():
        h = hommes.setdefault(qui, {
            "qui": qui, "travaux": [], "etapes": 0, "minutes": 0,
            "etapes_seches": 0, "journal": [], "rendu": None, "cahier2": 0})
        journal = d.get("journal") or []
        h["journal"] = journal
        h["etapes"] = len(journal)
        h["minutes"] = sum(int(e.get("duree") or 0) for e in journal)
        h["etapes_seches"] = sum(1 for e in journal
                                 if mod_travaux.etape_seche(e))
        h["trajets"] = sum(1 for e in journal
                           if mod_travaux.etape_est_trajet(e))
        h["rendu"] = d.get("rendu")
        h["cahier2"] = len(d.get("cahier2") or [])

    for h in hommes.values():
        h["dits"] = sum(1 for i in dits
                        if (i.get("locuteur_id") or i.get("acteur_id")) == h["qui"])
        h["faits"] = sum(1 for i in faits
                         if (i.get("locuteur_id") or i.get("acteur_id")) == h["qui"])
        h["avec_amont"] = sum(len(t["repliques"]) for t in h["travaux"])
    return hommes


def imprimer(hommes, dits, faits, orphelines, sans_date, date, jours, detail,
             cahiers, hors_fenetre, sans_jour, couverts):
    tot_etapes = sum(h["etapes"] for h in hommes.values())
    tot_seches = sum(h["etapes_seches"] for h in hommes.values())
    tot_min = sum(h["minutes"] for h in hommes.values())
    tot_pensees = sum(t["pensees"] for h in hommes.values() for t in h["travaux"])
    tot_servies = sum(t["servies"] for h in hommes.values() for t in h["travaux"])
    tot_avec = sum(h["avec_amont"] for h in hommes.values())
    journees = sum(1 for h in hommes.values() if h["etapes"])

    print("LA MESURE — {}{}".format(
        fmt(date), "" if jours <= 1 else " (fenetre : {} jours)".format(jours)))
    print()
    print("  {} journee(s) deposee(s) · {} min · {} etapes, dont {} sans rien "
          "rendre ({})".format(journees, tot_min, tot_etapes, tot_seches,
                               pourcent(tot_seches, tot_etapes)))
    print("  {} pensees produites · {} portees a la table ({})".format(
        tot_pensees, tot_servies, pourcent(tot_servies, tot_pensees)))
    print("  {} repliques poussees · {} portent la trace d'une pensee ({}) · "
          "{} gestes".format(len(dits), tot_avec, pourcent(tot_avec, len(dits)),
                             len(faits)))
    if tot_min and tot_avec and len(couverts) >= jours:
        print("  {} min de travail par replique qui porte quelque chose"
              .format(int(round(float(tot_min) / tot_avec))))
    elif jours > 1 and couverts:
        # AMONT ET AVAL DOIVENT COUVRIR LE MEME TEMPS, sinon le rendement est
        # un rapport entre deux echelles. On prefere ne pas le donner et dire
        # pourquoi : un chiffre faux se retient mieux qu'un chiffre absent.
        print("  pas de rendement : l'amont n'est depose que sur {} jour(s) "
              "des {} mesures".format(len(couverts), jours))
    if sans_date or hors_fenetre or sans_jour:
        manques = []
        if sans_date:
            manques.append("{} items du flux sans date".format(sans_date))
        if hors_fenetre:
            manques.append("{} journee(s) deposee(s) hors fenetre"
                           .format(hors_fenetre))
        if sans_jour:
            manques.append("{} journee(s) sans pensee datee, donc improuvable"
                           .format(sans_jour))
        print("  (hors de la mesure : {})".format(" · ".join(manques)))
    print()
    print("  Le lien replique->pensee est un INDICE, pas une preuve : {} mots "
          "rares partages.".format(RECOUPEMENT))
    print()

    ordre = sorted(hommes.values(),
                   key=lambda h: (-h["avec_amont"], -h["dits"], h["qui"]))

    print("PAR HOMME")
    for h in ordre:
        print("  {:<18} {:>3} repliques · {:>2} avec amont · {:>2} gestes"
              .format(h["qui"], h["dits"], h["avec_amont"], h["faits"]))
        if h["etapes"]:
            print("      journee   {} etapes · {} min · {} sans resultat"
                  .format(h["etapes"], h["minutes"], h["etapes_seches"]))
        else:
            print("      journee   aucune deposee en staging")
        c = cahiers.get(h["qui"])
        if c and c["proposes"]:
            print("      cahier    {} changements proposes · {} dans le livre "
                  "({}) · {} perdus".format(
                      c["proposes"], c["verses"],
                      pourcent(c["verses"], c["proposes"]),
                      len(c["perdus"])))
        for t in h["travaux"]:
            marque = "conclusion ecrite" if t["conclusion"] else "sans conclusion"
            print("      {:<30} {} pensees, {} servies · {}".format(
                tronque(t["affaire"], 30), t["pensees"], t["servies"], marque))
            print("          {} replique(s) le portent".format(len(t["repliques"])))
        print()

    # PREMIERE FAUTE — le travail qui n'atteint personne. Deux cas tres
    # differents sous un meme chiffre, et il faut les separer : celui qui n'a
    # pas eu l'occasion de parler n'a pas le meme probleme que celui qui a
    # parlé d'autre chose.
    vides = [(h, t) for h in ordre for t in h["travaux"]
             if t["pensees"] and not t["repliques"]]
    muet = [(h, t) for h, t in vides if not h["dits"]]
    a_cote = [(h, t) for h, t in vides if h["dits"]]
    print("LE TRAVAIL QUI N'ARRIVE PAS A LA TABLE ({})".format(len(vides)))
    if not vides:
        print("  rien.")
    if muet:
        print("  il n'a pas parle du tout ({}) :".format(len(muet)))
        for h, t in muet:
            print("    {:<18} {:<46} {} pensees{}".format(
                h["qui"], tronque(t["affaire"], 46), t["pensees"],
                " · conclusion ecrite" if t["conclusion"] else ""))
    if a_cote:
        print("  il a parle, mais d'autre chose ({}) :".format(len(a_cote)))
        for h, t in a_cote:
            print("    {:<18} {:<46} {} pensees · {} repliques ailleurs"
                  .format(h["qui"], tronque(t["affaire"], 46), t["pensees"],
                          h["dits"]))
    print()

    # SECONDE FAUTE, et c'est celle que tout l'edifice existe pour attraper :
    # une parole sans rien derriere.
    muets = {}
    for item, score in orphelines:
        qui = item.get("locuteur_id") or item.get("acteur_id") or "?"
        muets.setdefault(qui, []).append((item, score))
    sans_travail = [q for q in muets if q not in hommes]
    print("LA PAROLE SANS TRAVAIL DERRIERE ({} repliques, {} hommes)"
          .format(len(orphelines), len(muets)))
    for qui in sorted(muets, key=lambda q: -len(muets[q])):
        drapeau = "  AUCUN TRAVAIL OUVERT" if qui in sans_travail else ""
        print("  {:<18} {:>3}{}".format(qui, len(muets[qui]), drapeau))
        if detail:
            for item, score in muets[qui][:6]:
                print("      [{}] {}".format(score, tronque(item.get("texte"), 96)))
    if sans_travail:
        print()
        print("  {} homme(s) parlent sans avoir un seul travail ouvert : {}"
              .format(len(sans_travail), ", ".join(sorted(sans_travail))))
    print()

    if detail:
        print("LES ETAPES QUI N'ONT RIEN RENDU")
        for h in ordre:
            secs = [e for e in h["journal"] if mod_travaux.etape_seche(e)]
            if not secs:
                continue
            print("  {}".format(h["qui"]))
            for e in secs:
                print("      {:<6} {}".format(
                    e.get("heure") or "?", tronque(e.get("quoi"), 84)))
        print()


def cahier_verse(journees, books):
    """Combien des changements de cahier d'un homme sont VRAIMENT dans le livre.

    C'est la derniere marche de la chaine, et la seule qui se verifie sans
    approximation : un `cahier2` dit son livre, sa table, sa ligne, sa colonne
    et sa valeur, tous en toutes lettres. On relit `books.json` et on compare
    des chaines — pas d'indice ici, une egalite.

    Une premiere version cherchait plutot le TEXTE d'une conclusion dans le
    volume, par mots rares. Elle ne discriminait rien : les mots d'une
    conclusion se retrouvent dans n'importe quel gros registre, et le meilleur
    livre etranger scorait aussi haut que le bon. Mesurer faux est pire que ne
    pas mesurer — d'ou ce test-ci, qui ne repond qu'a ce qu'il sait.
    """
    import appliquer_travaux as ap
    index = {b.get("id"): b for b in books if isinstance(b, dict)}
    out = {}

    for qui, d in journees.items():
        proposes = d.get("cahier2") or []
        verses, perdus = 0, []
        for e in proposes:
            livre = index.get(e.get("livre"))
            if livre is None:
                perdus.append((e, "livre inconnu"))
                continue
            quoi = (e.get("quoi") or "").strip().lower()
            if quoi == "creer_table":
                if ap.grille_nommee(livre, (e.get("table") or "").strip())[0] \
                        is not None:
                    verses += 1
                else:
                    perdus.append((e, "table jamais creee"))
                continue

            colonnes, lignes = ap.grille_nommee(livre, e.get("table"))
            if colonnes is None:
                perdus.append((e, "aucune table de ce titre"))
                continue

            if quoi == "ajouter":
                tete = str((e.get("cellules") or [""])[0]).strip()
                trouve = any(str((l.get("cellules") or [""])[0]).strip() == tete
                             for l in lignes)
                verses += 1 if trouve else 0
                if not trouve:
                    perdus.append((e, "ligne jamais posee"))
                continue

            cible = None
            for l in lignes:
                if str((l.get("cellules") or [""])[0]).strip() \
                        == (e.get("ligne") or "").strip():
                    cible = l
                    break
            if cible is None:
                perdus.append((e, "aucune ligne de ce nom"))
                continue
            if quoi == "retirer":
                if cible.get("note"):
                    verses += 1
                else:
                    perdus.append((e, "ligne jamais marquee retiree"))
                continue

            j = None
            for k, nom in enumerate(colonnes):
                if str(nom).strip() == (e.get("colonne") or "").strip():
                    j = k
                    break
            if j is None:
                perdus.append((e, "aucune colonne de ce nom"))
                continue
            cellules = cible.get("cellules") or []
            valeur = str(cellules[j]) if j < len(cellules) else ""
            if valeur.strip() == str(e.get("valeur") or "").strip():
                verses += 1
            else:
                perdus.append((e, "la cellule ne porte pas cette valeur"))

        out[qui] = {"proposes": len(proposes), "verses": verses,
                    "perdus": perdus}
    return out


def lire_journal():
    """Le journal des journees — append-only, ecrit par verser_travaux.py."""
    chemin = os.path.join(ETAT, "journees.jsonl")
    out = []
    if not os.path.isfile(chemin):
        return out
    with io.open(chemin, encoding="utf-8") as fh:
        for ligne in fh:
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                out.append(json.loads(ligne))
            except ValueError:
                continue
    return out


def historique(qui_filtre, detail):
    """Ce que la boucle de travail a fait, jour par jour.

    C'est la seule vue qui survit a l'ecrasement des depots : `mesurer.py`
    sans `--historique` ne sait rien d'avant-hier, parce que
    `etat/staging/travaux/` ne garde que le dernier depot de chaque homme.
    """
    lignes = lire_journal()
    if not lignes:
        print("Le journal est vide — etat/journees.jsonl n'existe pas encore.")
        print("Il se remplit au versement : python scripts/verser_travaux.py "
              "--vraiment")
        return 0

    journees = [o for o in lignes if o.get("type") == "journee"]
    etapes = [o for o in lignes if o.get("type") == "etape"]
    if qui_filtre:
        journees = [o for o in journees if o.get("qui") == qui_filtre]
        etapes = [o for o in etapes if o.get("qui") == qui_filtre]

    def cle(o):
        d = o.get("jour") or {}
        return (d.get("annee") or 0, d.get("lune") or 0, d.get("jour") or 0)

    # DEUX SEANCES FONT UNE JOURNEE. Un homme peut retourner au travail le
    # soir ; l'afficher en deux lignes ferait croire a deux journees d'homme,
    # et le budget de rarete (deux affaires par jour) deviendrait illisible.
    par_jour, fusion = {}, {}
    for o in journees:
        k = (cle(o), o.get("qui"))
        if k in fusion:
            f = fusion[k]
            # DEUX NATURES DE CHIFFRE DANS LA MEME LIGNE. Les etapes sont
            # propres a la seance — `journaliser` ne consigne que celles qu'il
            # n'avait pas vues — donc elles s'ADDITIONNENT. Les pensees et le
            # cahier, eux, sont relus en entier dans le depot a chaque fois :
            # les additionner comptait deux fois la matinee, et Rulf affichait
            # 33 pensees pour 20. On prend le MAXIMUM.
            for champ in ("etapes", "minutes", "secs", "trajets"):
                f[champ] = (f.get(champ) or 0) + (o.get(champ) or 0)
            for champ in ("pensees", "conclusions", "cahier_proposes"):
                f[champ] = max(f.get(champ) or 0, o.get(champ) or 0)
            f["seances"] = max(f.get("seances", 1), int(o.get("seance") or 1))
        else:
            f = dict(o)
            f["seances"] = int(o.get("seance") or 1)
            fusion[k] = f
            par_jour.setdefault(cle(o), []).append(f)

    print("LE JOURNAL DES JOURNEES — {} journee(s), {} etape(s), {} jour(s)"
          .format(len(journees), len(etapes), len(par_jour)))
    print()
    for k in sorted(par_jour):
        lot = sorted(par_jour[k], key=lambda o: o.get("qui") or "")
        print("{}e j., {}e lune, an {} — {} homme(s), {} min, {} etapes, "
              "{} pensees".format(
                  k[2], k[1], k[0], len(lot),
                  sum(o.get("minutes") or 0 for o in lot),
                  sum(o.get("etapes") or 0 for o in lot),
                  sum(o.get("pensees") or 0 for o in lot)))
        for o in lot:
            print("  {:<18}{} {:>2} etapes ({} trajets) · {:>3} min · {} sans "
                  "resultat · {} pensees · {} conclusion(s) · {} au cahier"
                  .format(o.get("qui"),
                          "" if o.get("seances", 1) < 2
                          else " [{}×]".format(o["seances"]),
                          o.get("etapes"), o.get("trajets") or 0,
                          o.get("minutes"), o.get("secs"), o.get("pensees"),
                          o.get("conclusions"), o.get("cahier_proposes")))
            if detail:
                siennes = [e for e in etapes
                           if e.get("qui") == o.get("qui")
                           and cle(e) == k]
                for e in siennes:
                    ou = e.get("lieu") or "{} → {}".format(
                        e.get("de") or "?", e.get("a") or "?")
                    print("      {:<6} {:>3}min {:<22} {}".format(
                        e.get("heure") or "?", e.get("duree") or 0,
                        tronque(ou, 22), tronque(e.get("quoi"), 64)))
                    # Un trajet n'a pas de resultat a montrer : le dire
                    # « RIEN » ferait passer une marche pour un echec.
                    if e.get("genre") == "trajet":
                        continue
                    marque = "RIEN" if e.get("sec") else "→"
                    print("             {} {}".format(
                        marque, tronque(e.get("resultat"), 88)))
        print()
    return 0


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--historique", action="store_true",
                    help="le journal des journees, jour par jour")
    ap.add_argument("--jours", type=int, default=FENETRE,
                    help="fenetre en jours, celui du monde inclus")
    ap.add_argument("--qui")
    ap.add_argument("--detail", action="store_true")
    args = ap.parse_args()

    if args.historique:
        return historique(args.qui, args.detail)

    monde = charger("monde", {})
    date = monde.get("date") or {"annee": 0, "lune": 1, "jour": 1}
    fin = jour_absolu(date) or 0
    debut = fin - max(0, args.jours - 1)

    travaux = [t for t in lire_travaux()
               if t.get("etat") not in ("abandonne",) and t.get("id")]
    journees, hors_fenetre, sans_jour, couverts = lire_journees(debut, fin)
    par_id = {t["id"]: t for t in travaux}

    items, sans_date = lire_flux(debut, fin)
    dits = [i for i in items if i.get("type") in DIT]
    faits = [i for i in items if i.get("type") in FAIT]

    # Tout le corpus d'abord — la rarete d'un mot s'y mesure. On restreint
    # ensuite, jamais avant.
    par_travail, orphelines = recouper(travaux, dits, par_id)

    if args.qui:
        def sien(i):
            return (i.get("locuteur_id") or i.get("acteur_id")) == args.qui
        travaux = [t for t in travaux if t.get("qui") == args.qui]
        journees = {k: v for k, v in journees.items() if k == args.qui}
        dits = [i for i in dits if sien(i)]
        faits = [i for i in faits if sien(i)]
        orphelines = [(i, s) for i, s in orphelines if sien(i)]
        par_travail = {k: v for k, v in par_travail.items()
                       if par_id[k].get("qui") == args.qui}
    hommes = mesurer(travaux, journees, dits, faits, par_travail, orphelines)
    cahiers = cahier_verse(journees, charger("books", []))
    imprimer(hommes, dits, faits, orphelines, sans_date, date, args.jours,
             args.detail, cahiers, hors_fenetre, sans_jour, couverts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
