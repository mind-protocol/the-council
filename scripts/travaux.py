# -*- coding: utf-8 -*-
# LES TRAVAUX — ce qu'un homme a touche, ce que ca lui a appris, et s'il a
# quelque chose a dire ce matin.
#
# POURQUOI. Il manquait le milieu de la chaine. Les MAINS (`mains.json`)
# comptent des tonneaux sans avoir d'opinion ; la TETE (`intentions.json`) veut
# des choses et poursuit un plan. Entre les deux, rien ne disait CE QU'UN HOMME
# A APPRIS AUJOURD'HUI — et faute de ce milieu, une replique de conseiller
# n'avait pas d'amont : elle se fabriquait au moment de l'ecrire, a partir de ce
# qui venait d'etre dit dans la salle. D'ou des salles entieres ou l'on commente
# le registre au lieu de rapporter le dehors.
#
# LA CHAINE, ET SA CONTRAINTE D'ENTREE :
#
#     une source touchee -> du travail -> des pensees datees
#                        -> une conclusion mure -> un message
#
# PAS DE SOURCE, PAS DE PENSEE. Une pensee ne s'invente pas : elle nait de
# quelque chose que l'homme a reellement touche ce jour-la — un registre
# depouille, un homme ecoute, une mesure qui a bouge, un pli arrive, la
# conclusion d'un collegue. C'est la meme regle que pour les croyances des
# absents, qui ne changent que par une `diffusion` arrivee a echeance.
#
# L'EXCITATION EST UN CHIFFRE, ET C'EST DELIBERE. Un jugement souple n'a pas
# attrape la faute que les cent derniers messages du conseil ont montree : un
# homme excite en permanence sans sources, qui commente la salle parce que
# commenter la salle ressemble a avoir une raison d'agir. Un chiffre se verifie.
# Les constantes ci-dessous sont a l'essai — on les bouge apres mesure.
#
# CE SCRIPT NE DECIDE RIEN ET N'ECRIT JAMAIS DANS etat/. Il fait de
# l'arithmetique et rend une proposition, comme `tick.py` dont il est le module.
# En particulier : il dit qu'une conclusion est MURE, il ne l'ecrit pas. Le
# texte d'une conclusion appartient a celui qui tient la charge — la machine qui
# l'ecrirait a sa place refabriquerait exactement le vide qu'on veut supprimer.
#
# Usage :
#     python scripts/travaux.py                 l'etat des travaux aujourd'hui
#     python scripts/travaux.py --jours 2       ce que deux jours en font
#     python scripts/travaux.py --qui gerardys  un seul homme
#     python scripts/travaux.py --verifier      ce qui cloche dans la table
import argparse
import io
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")

# ------------------------------------------------------------- les chiffres
# A l'essai. Tout est ici, en un bloc, pour qu'on les bouge sans lire le code.

SEUIL_PAROLE = 3          # en dessous, il ne parle pas : il travaille
PLAFOND = 6               # un homme ne s'excite pas indefiniment
GAIN_PENSEE = 2           # une pensee neuve tombee depuis le dernier battement
GAIN_CONCLUSION = 3       # une conclusion qui murit
GAIN_ECHEANCE = 1         # l'echeance tombe aujourd'hui, ou elle est passee
PERTE_PAR_JOUR = 1        # decroissance, par jour sans source neuve
PENSEES_POUR_CONCLURE = 2 # en dessous, on n'a pas de quoi conclure
TRAVAUX_PAR_JOUR = 2      # une journee d'homme ne contient pas plus


# ------------------------------------------------------------------- dates

JOURS_PAR_LUNE = 30
LUNES_PAR_AN = 12


def jour_absolu(date):
    """MEME convention que tick.py, au jour pres — `aujourdhui` vient de lui.

    Le `- 1` sur le jour compte, et il a deja coute une alarme : avec une
    origine decalee d'une unite, une echeance d'hier tombait pile sur
    aujourd'hui et le retard ne se voyait plus.
    """
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


def lire_travaux():
    brut = charger("travaux", {})
    return brut.get("travaux", []) if isinstance(brut, dict) else (brut or [])


def sterile(resultat):
    """Une etape de journee qui n'a rien rendu.

    ICI, ET NULLE PART AILLEURS. Cette definition a d'abord ete ecrite deux
    fois — dans `mesurer.py` et dans `verser_travaux.py` — et les deux versions
    ont diverge aussitot sur la ponctuation d'ouverture : « — Rien. » comptait
    comme un resultat pour l'une et comme un vide pour l'autre. Le meme homme
    avait 4 etapes seches a la mesure et 13 au journal. Un chiffre qui ne
    s'accorde pas avec lui-meme ne se corrige pas, il se centralise.

    « Rien » est une reponse honnete et frequente — c'est meme ce qui rend le
    reste credible. On la compte pour la voir, pas pour la reprocher.
    """
    import re as _re
    import unicodedata as _ud
    t = _ud.normalize("NFD", resultat or "")
    t = "".join(c for c in t if _ud.category(c) != "Mn").lower()
    t = _re.sub(r"[^a-z0-9]+", " ", t).strip()
    if not t:
        return True
    return t.startswith("rien") or t.startswith("aucun")


def etape_est_trajet(etape):
    """Un deplacement : il porte un `de`/`a` et aucun lieu de travail."""
    if not isinstance(etape, dict):
        return False
    return bool(etape.get("de") or etape.get("a")) and not etape.get("lieu")


def etape_seche(etape):
    """Une etape qui devait rendre quelque chose et n'a rien rendu.

    LE TRAJET N'EST PAS UNE ETAPE SECHE, et les confondre fausse tout : « il
    descend a la greve, sa lanterne eteinte sous le bras », resultat « — », ce
    n'est pas un echec, c'est un homme qui marche. En les comptant, la premiere
    version annoncait 31% de journee sans resultat la ou il y avait des allers
    et venues normales. On ne juge que ce qui allait chercher quelque chose.
    """
    if not isinstance(etape, dict) or etape_est_trajet(etape):
        return False
    return sterile(etape.get("resultat"))


# --------------------------------------------------------- l'arithmetique

def borner(valeur):
    return max(0, min(PLAFOND, valeur))


def pensees_depuis(trav, depuis):
    """Les pensees tombees apres le jour `depuis` (exclu) et JAMAIS SERVIES.

    `servie: true` se pose sur une pensee dans laquelle on a PUISE pour ecrire
    une replique. On ne prononce jamais une pensee : la salle la lit, et
    quatorze pensees donnent quatre phrases. Sans cette marque, un homme se
    re-exciterait chaque matin sur ce dont il s'est deja servi hier.
    """
    out = []
    for p in trav.get("pensees") or []:
        if p.get("servie"):
            continue
        j = jour_absolu(p.get("date"))
        if j is not None and j > depuis:
            out.append(p)
    return out


def calculer_travaux(travaux, aujourdhui, jours=0):
    """L'etat des travaux a `aujourdhui + jours`. Arithmetique pure.

    Retourne (lignes, mutations). Une ligne par travail vivant ; les mutations
    sont STRICTEMENT ce qui se deduit — l'excitation nouvelle, et le fait
    qu'une conclusion soit mure. Jamais le texte d'une conclusion.
    """
    fin = aujourdhui + max(0, jours)
    lignes, mutations = [], []

    for trav in travaux:
        if trav.get("etat") in ("rendu", "abandonne"):
            continue

        tid = trav.get("id") or "?"
        dernier = jour_absolu(trav.get("dernier_travail"))
        neuves = pensees_depuis(trav, dernier - 1 if dernier else -1)
        total_pensees = len(trav.get("pensees") or [])
        conclusion = trav.get("conclusion")

        # Sans source declaree ET sans pensee en reserve, ce travail ne peut
        # rien produire : ce n'est pas un travail, c'est un voeu.
        sterile = not (trav.get("sources") or trav.get("pensees"))

        # La decroissance : un jour sans source neuve coute un point.
        jours_sans = (fin - dernier) if dernier is not None else jours
        jours_sans = max(0, jours_sans)

        excitation = int(trav.get("excitation") or 0)
        excitation -= PERTE_PAR_JOUR * jours_sans
        if neuves:
            excitation += GAIN_PENSEE * len(neuves)

        echeance = jour_absolu(trav.get("echeance"))
        due = echeance is not None and echeance <= fin
        if due:
            excitation += GAIN_ECHEANCE

        # Une conclusion murit quand assez de pensees ont converge, ou quand
        # l'echeance tombe et qu'il y a au moins de quoi rendre compte.
        mure = (conclusion is None and not sterile
                and (total_pensees >= PENSEES_POUR_CONCLURE
                     or (due and total_pensees >= 1)))
        if mure:
            excitation += GAIN_CONCLUSION

        excitation = borner(excitation)

        # TROIS VERDICTS, ET LA NUANCE COMPTE. Une conclusion mure dont toutes
        # les pensees ont deja ete servies ne donne PAS une prise de parole : ce
        # que l'homme doit alors, c'est l'ecrire a son cahier, pas parler une
        # cinquieme fois de ce qu'il a deja raconte. Et tant qu'il lui reste une
        # source a toucher avant l'echeance, il va la toucher — c'est le
        # « travailler avant de repondre ». On ne conclut de force que lorsqu'il
        # n'y a plus rien a aller chercher, ou que l'echeance est passee.
        assez = excitation >= SEUIL_PAROLE
        reste_a_toucher = bool(trav.get("sources"))
        en_retard = echeance is not None and echeance < fin and not conclusion
        if assez and neuves:
            verdict = "parle"
        elif assez and (conclusion or mure) and (en_retard or not reste_a_toucher):
            verdict = "conclut"
        else:
            verdict = "travaille"
        parle = verdict == "parle"

        lignes.append({
            "id": tid,
            "qui": trav.get("qui"),
            "affaire": trav.get("affaire"),
            "echeance": trav.get("echeance"),
            "due": due,
            "en_retard": en_retard,
            "pensees": total_pensees,
            "pensees_neuves": len(neuves),
            "jours_sans_source": jours_sans,
            "sterile": sterile,
            "excitation_avant": int(trav.get("excitation") or 0),
            "excitation": excitation,
            "conclusion_mure": mure,
            "conclusion": conclusion,
            "verdict": verdict,
            "prochaine_source": (trav.get("sources") or [{}])[0].get("quoi"),
        })

        if excitation != int(trav.get("excitation") or 0):
            mutations.append({
                "table": "travaux",
                "cible": tid,
                "operation": "excitation",
                "valeur": excitation,
                "pourquoi": "{} pensee(s) neuve(s), {} jour(s) sans source{}"
                            .format(len(neuves), jours_sans,
                                    ", echeance due" if due else ""),
            })
        if mure:
            mutations.append({
                "table": "travaux",
                "cible": tid,
                "operation": "conclusion_mure",
                "valeur": None,
                "pourquoi": "{} pensee(s) ont converge{} — ECRIS la conclusion "
                            "de SA main, puis porte-la dans son cahier ({}). "
                            "Sans texte, le lot est refuse."
                            .format(total_pensees,
                                    " et l'echeance tombe" if due else "",
                                    trav.get("livre") or "son cahier"),
            })

    lignes.sort(key=lambda l: (-l["excitation"], l.get("qui") or ""))
    return lignes, mutations


# ------------------------------------------------------------- verification

def verifier_travaux(travaux, personnages, intentions, aujourdhui, dire):
    """Les fautes que la table peut porter. `dire(gravite, quoi, texte)`."""
    connus = set()
    for p in personnages or []:
        if isinstance(p, dict) and p.get("id"):
            connus.add(p["id"])

    vus, par_homme_et_jour = set(), {}
    for trav in travaux:
        tid = trav.get("id")
        if not tid:
            dire("grave", "travaux", "un travail sans id")
            continue
        if tid in vus:
            dire("grave", "travaux", "id double : {}".format(tid))
        vus.add(tid)

        qui = trav.get("qui")
        if connus and qui not in connus:
            dire("grave", "travaux",
                 "{} : '{}' n'est pas un personnage connu".format(tid, qui))

        if trav.get("etat") in ("rendu", "abandonne"):
            continue

        if not (trav.get("sources") or trav.get("pensees")):
            dire("avertissement", "travaux",
                 "{} ({}) : ni source ni pensee — ce n'est pas un travail, "
                 "c'est un voeu. Il ne produira jamais rien."
                 .format(tid, qui))

        if trav.get("conclusion") and not (trav.get("pensees") or []):
            dire("grave", "travaux",
                 "{} ({}) : une conclusion sans une seule pensee derriere — "
                 "elle a ete inventee, pas trouvee.".format(tid, qui))

        for p in trav.get("pensees") or []:
            if not (p.get("source") or "").strip():
                dire("grave", "travaux",
                     "{} ({}) : une pensee sans source. Pas de source, pas de "
                     "pensee.".format(tid, qui))
            j = jour_absolu(p.get("date"))
            if j is None:
                dire("grave", "travaux",
                     "{} ({}) : une pensee sans date".format(tid, qui))
            else:
                # On compte les AFFAIRES touchees ce jour-la, pas les pensees.
                # La rarete porte sur ce qu'un homme peut ouvrir dans sa
                # journee ; une matinee entiere dans vingt-deux ans de releves
                # produit treize pensees et c'est tres bien. Compter les
                # pensees punirait le travail au lieu de le borner.
                par_homme_et_jour.setdefault((qui, j), set()).add(tid)

        ech = jour_absolu(trav.get("echeance"))
        if ech is not None and ech < aujourdhui and not trav.get("conclusion"):
            dire("avertissement", "travaux",
                 "{} ({}) : echeance passee le {} et rien de rendu — il doit "
                 "le dire lui-meme, avec une date neuve."
                 .format(tid, qui, fmt(trav.get("echeance"))))

    for (qui, jour), affaires in sorted(par_homme_et_jour.items()):
        if len(affaires) > TRAVAUX_PAR_JOUR:
            dire("avertissement", "travaux",
                 "{} a touche {} affaires le meme jour ({}) : {} — une journee "
                 "d'homme n'en contient pas plus de {}. Le nombre de pensees, "
                 "lui, n'est pas borne."
                 .format(qui, len(affaires), fmt(date_de(jour)),
                         ", ".join(sorted(affaires)), TRAVAUX_PAR_JOUR))

    # Une tete de scene sans aucun travail parlera sans source : c'est la faute
    # que tout ceci existe pour attraper.
    avec_travail = set(t.get("qui") for t in travaux
                       if t.get("etat") not in ("rendu", "abandonne"))
    for tete in intentions or []:
        if not isinstance(tete, dict):
            continue
        if (tete.get("echelle") or "").strip() != "scene":
            continue
        pid = tete.get("personnage_id")
        if pid and pid not in avec_travail:
            dire("avertissement", "travaux",
                 "{} est en echelle 'scene' et n'a aucun travail ouvert — il "
                 "parlera sans source.".format(pid))


def date_de(n):
    """Inverse de jour_absolu — meme convention que tick.py."""
    if n is None:
        return {}
    jour = int(n) % JOURS_PAR_LUNE
    lunes = int(n) // JOURS_PAR_LUNE
    return {"annee": lunes // LUNES_PAR_AN,
            "lune": (lunes % LUNES_PAR_AN) + 1,
            "jour": jour + 1}


# ------------------------------------------------------------------ rapport

def imprimer(lignes, date):
    parlent = [l for l in lignes if l["verdict"] == "parle"]
    concluent = [l for l in lignes if l["verdict"] == "conclut"]
    bossent = [l for l in lignes if l["verdict"] == "travaille"]

    print("Les travaux au {}".format(fmt(date)))
    print("  seuil de parole {} · plafond {} · {} travaux vivants"
          .format(SEUIL_PAROLE, PLAFOND, len(lignes)))
    print()

    print("QUI A QUELQUE CHOSE A DIRE ({})".format(len(parlent)))
    if not parlent:
        print("  personne — et c'est un etat normal, pas une panne.")
    for l in parlent:
        marque = "CONCLUSION MURE" if l["conclusion_mure"] else (
            "conclusion tenue" if l["conclusion"] else
            "{} pensee(s) neuve(s)".format(l["pensees_neuves"]))
        print("  [{}] {:<18} {}".format(l["excitation"], l["qui"], l["affaire"]))
        print("       {}{}".format(marque, " · DU AUJOURD'HUI" if l["due"] else ""))
        if l["en_retard"]:
            print("       EN RETARD — il le dit lui-meme, avec une date neuve")
    print()

    if concluent:
        print("QUI DOIT ECRIRE SA CONCLUSION ({}) — au cahier, pas a la table"
              .format(len(concluent)))
        for l in concluent:
            print("  [{}] {:<18} {}{}".format(
                l["excitation"], l["qui"], l["affaire"],
                " · EN RETARD" if l["en_retard"] else ""))
        print()

    print("QUI TRAVAILLE, ET SUR QUOI ({})".format(len(bossent)))
    for l in bossent:
        print("  [{}] {:<18} {}".format(l["excitation"], l["qui"], l["affaire"]))
        if l["sterile"]:
            print("       AUCUNE SOURCE — ce travail ne produira rien")
        elif l["prochaine_source"]:
            print("       va toucher : {}".format(l["prochaine_source"]))
        if l["jours_sans_source"] >= 3:
            print("       {} jours sans rien toucher".format(l["jours_sans_source"]))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jours", type=int, default=0)
    ap.add_argument("--qui")
    ap.add_argument("--verifier", action="store_true")
    args = ap.parse_args()

    monde = charger("monde", {})
    date = monde.get("date") or {"annee": 0, "lune": 1, "jour": 1}
    aujourdhui = jour_absolu(date) or 0
    travaux = lire_travaux()
    if args.qui:
        travaux = [t for t in travaux if t.get("qui") == args.qui]

    if args.verifier:
        anomalies = []
        verifier_travaux(travaux, charger("personnages", []),
                         charger("intentions", []), aujourdhui,
                         lambda g, q, t: anomalies.append((g, q, t)))
        if not anomalies:
            print("Les travaux : rien a signaler.")
            return 0
        for gravite, quoi, texte in anomalies:
            print("[{}] {} : {}".format(gravite, quoi, texte))
        return 1 if any(g == "grave" for g, _, _ in anomalies) else 0

    lignes, mutations = calculer_travaux(travaux, aujourdhui, args.jours)
    imprimer(lignes, date_de(aujourdhui + args.jours))
    if mutations:
        print()
        print("{} mutation(s) proposee(s) — a appliquer par le MJ."
              .format(len(mutations)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
