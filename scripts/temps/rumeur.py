# -*- coding: utf-8 -*-
"""LA RUMEUR — ce qui saute de proche en proche, et les bouches qui arrivent.

CE QUE CE MODULE POSSEDE : la propagation des incidents de la table de guerre
(docs/carte.md) — certitudes qui se degradent a chaque saut, lenteur de la
bouche a oreille, plafond de voisins —, la detection des arrivees (la bouche :
qui arrive ou, et ce qu'il apporte que personne sur place ne sait), les
temoins, et les cycles du graphe de dependances d'etapes.

LE FUTUR « BRUIT DE FOND » ATTERRIT ICI (grain 3 : deux co-presents se sont
parle -> entree de diffusion canal rumeur/temoin, zero appel LLM). C'est la
feature qui a tire ce decoupage — docs/organisation.md §5.

CE QU'IL REFUSE : toute prose. Le script propose le saut, sa date, la
certitude degradee ; la `version` — ce qui se dit vraiment la-bas, de
travers — est ecrite a la main par le MJ. Une machine n'a rien a faire la ou
le brouillard se fabrique.

CONSOMMATEURS : fenetre.py (propager_rumeurs, detecter_bouches), gardes/
(temoins_des_incidents, relais_de, rang_certitude, cycles, SILENCE_RUMEUR).
"""

from temps.calendrier import jour_absolu, date_de
from temps.lecture import jours_de_route
from temps.bouche import croyances_de, se_recoupent, echelle_de

# LA RUMEUR — un incident de la table de guerre (docs/carte.md), pas une table
# de plus. Elle n'a pas de porteur nomme : elle saute de proche en proche.
# Echelle de certitude, du plus sur au plus trouble. Un saut degrade d'un cran.
CERTITUDES = ("sure", "rapportee", "rumeur")
# Plus lente que le cavalier : elle passe de bouche en bouche, elle s'arrete
# boire. Plein tarif x3/2, et jamais moins de deux jours pour un saut.
LENTEUR_RUMEUR = (3, 2)
SAUT_RUMEUR_MINIMUM = 2
# Au-dela, une place n'est plus « de proche en proche » : la rumeur y ira par
# un pli ou par une bouche, pas toute seule.
PORTEE_SAUT_RUMEUR = 3
# Plafond de voisins gagnes par rumeur et par fenetre — les `risque[]` ecrits
# par le MJ ne sont jamais plafonnes, ni un saut qui atteint le joueur.
VOISINS_PAR_RUMEUR = 3
# Silence tolere avant qu'une rumeur soit dite immobile — elle devrait avancer
# ou s'eteindre.
SILENCE_RUMEUR = {"vif": 5, "couve": 15}


# ------------------------------------------------------------- LA RUMEUR

def temoins_des_incidents(e):
    """Les gens nommes en `depuis` d'un relais : les temoins.

    Un temoin n'a PAS de tete dans intentions.json, et c'est voulu : il n'a pas
    de projet, il a vu quelque chose et il le raconte. Une tete coute du budget
    d'echelle et derive des qu'on ne la relit plus — on ne peuple pas la
    simulation de gens qui n'ont rien a poursuivre. S'il se met a en avoir un,
    il sera promu par les voies normales.
    """
    noms = set()
    for inc in e.incidents:
        for ent in inc.get("propage") or []:
            if isinstance(ent, dict) and ent.get("depuis") in e.perso_par_id:
                noms.add(ent["depuis"])
    return noms


def rang_certitude(valeur):
    """sure=2, rapportee=1, rumeur=0. Inconnu -> rapportee, au milieu."""
    try:
        return len(CERTITUDES) - 1 - CERTITUDES.index(valeur)
    except ValueError:
        return 1


def degrader(valeur):
    """Ce que devient une certitude apres un saut de bouche a oreille."""
    rang = rang_certitude(valeur)
    return CERTITUDES[len(CERTITUDES) - 1 - max(rang - 1, 0)]


def relais_de(incident):
    """Le foyer et tout ce qui a ete gagne, au meme format {ou, date, ...}."""
    relais = [{"ou": incident.get("ou"), "date": incident.get("date"),
               "certitude": incident.get("certitude"), "foyer": True,
               "ames": incident.get("ames")}]
    for ent in incident.get("propage") or []:
        if isinstance(ent, str):
            relais.append({"ou": ent, "date": None, "certitude": None})
        elif isinstance(ent, dict):
            relais.append(dict(ent))
    return [r for r in relais if r.get("ou")]


def saut_rumeur(e, depuis, vers):
    """Jours d'un saut de rumeur. Plus lent que le cavalier, par principe."""
    plein = jours_de_route(e, depuis, vers, "cavalier")
    if plein is None:
        return None
    haut, bas = LENTEUR_RUMEUR
    return max((plein * haut + bas - 1) // bas, SAUT_RUMEUR_MINIMUM)


def propager_rumeurs(e, fin, cible):
    """Ce qu'une rumeur gagne dans la fenetre. Le script n'ecrit aucune prose.

    Une rumeur n'a pas de porteur nomme : elle saute de proche en proche, et se
    deforme A CHAQUE SAUT. Le tick propose le saut, sa date et la certitude
    DEGRADEE d'un cran ; la `version` — ce qui se dit vraiment la-bas, de
    travers — est ecrite a la main par le MJ. C'est le seul endroit ou le
    brouillard se fabrique, et une machine n'a rien a y faire.

    Les places candidates ne sont pas tout le royaume : ce sont celles que le MJ
    a lui-meme portees en `risque[]`, plus les voisines a portee de voix d'une
    place deja gagnee (PORTEE_SAUT_RUMEUR jours de cavalier).
    """
    lieu_joueur = e.lieu((e.perso_par_id.get(e.joueur) or {}).get("lieu_id"))
    sauts, immobiles = [], []

    for inc in e.incidents:
        if inc.get("feu") == "eteint":
            continue
        relais = relais_de(inc)
        prises = {e.lieu(r["ou"]) for r in relais if e.lieu(r["ou"])}
        derniere = max([jour_absolu(r.get("date")) for r in relais
                        if jour_absolu(r.get("date")) is not None] or [None]
                       ) if any(jour_absolu(r.get("date")) is not None
                                for r in relais) else None

        # les craintes du MJ d'abord : c'est lui qui a dit ou ca peut prendre
        candidats = {}
        for crainte in inc.get("risque") or []:
            ou = crainte if isinstance(crainte, str) else (
                crainte.get("ou") if isinstance(crainte, dict) else None)
            canon = e.lieu(ou)
            if canon and canon not in prises:
                candidats[canon] = {
                    "raison": "risque",
                    "ames": (crainte.get("ames")
                             if isinstance(crainte, dict) else None),
                    "note": (crainte.get("note")
                             if isinstance(crainte, dict) else None),
                }
        # puis le voisinage immediat de ce qui a deja pris — mais seulement si
        # le feu est VIF. Une chose qui `couve` ne gagne pas de terrain toute
        # seule : elle n'ira que la ou le MJ a ecrit qu'elle risque de prendre.
        for lid in (e.fiche_lieu if inc.get("feu") == "vif" else ()):
            if lid in prises or lid in candidats:
                continue
            proche = min([jours_de_route(e, p, lid, "cavalier") or 99
                          for p in prises] or [99])
            if proche <= PORTEE_SAUT_RUMEUR:
                candidats[lid] = {"raison": "voisin", "ames": None,
                                  "note": None}

        propres = []
        for vers, quoi in sorted(candidats.items()):
            # la source la plus favorable : celle qui l'y amene le plus tot
            meilleur = None
            for r in relais:
                depuis = e.lieu(r["ou"])
                depart = jour_absolu(r.get("date"))
                if not depuis or depart is None:
                    continue
                jours = saut_rumeur(e, depuis, vers)
                if jours is None:
                    continue
                arrivee = depart + jours
                if meilleur is None or arrivee < meilleur[0]:
                    meilleur = (arrivee, depuis, r)
            if meilleur is None or meilleur[0] > fin:
                continue
            arrivee, depuis, source = meilleur
            propres.append({
                "incident_id": inc.get("id"),
                "nom": inc.get("nom"),
                "feu": inc.get("feu"),
                "depuis": depuis,
                "vers": vers,
                "date": date_de(arrivee),
                "en_retard": arrivee < e.aujourdhui,
                "certitude_source": source.get("certitude")
                                    or inc.get("certitude"),
                "certitude_proposee": degrader(source.get("certitude")
                                               or inc.get("certitude")),
                "raison": quoi["raison"],
                "ames_estimees": quoi["ames"],
                "note_du_mj": quoi["note"],
                "atteint_le_joueur": bool(lieu_joueur) and vers == lieu_joueur,
                "contenu_a_ecrire": (
                    "le MJ ecrit ce qui se dit LA-BAS, deforme d'un cran — "
                    "le script n'invente aucune prose"),
            })

        # Une rumeur ne prend pas dix places d'un coup : les craintes ecrites
        # par le MJ passent toutes, le voisinage est plafonne aux plus proches.
        # Sans ce plafond, une fenetre de six jours propose vingt sauts et le MJ
        # ne les relit plus — ce qui revient a ne rien proposer du tout.
        propres.sort(key=lambda s: jour_absolu(s["date"]) or 0)
        garde, voisins = [], 0
        for s in propres:
            if s["raison"] == "voisin":
                if voisins >= VOISINS_PAR_RUMEUR and not s["atteint_le_joueur"]:
                    continue
                voisins += 1
            garde.append(s)
        sauts.extend(garde)

        # une rumeur qui n'a pas bouge depuis longtemps : elle ment sur elle-meme
        toleree = SILENCE_RUMEUR.get(inc.get("feu"))
        if toleree is not None and derniere is not None:
            silence = e.aujourdhui - derniere
            if silence > toleree:
                immobiles.append({
                    "incident_id": inc.get("id"),
                    "nom": inc.get("nom"),
                    "feu": inc.get("feu"),
                    "silence_jours": silence,
                    "derniere_prise": date_de(derniere),
                })

    sauts.sort(key=lambda s: jour_absolu(s["date"]) or 0)
    return sauts, immobiles


def sans_accents(texte):
    plat = (texte or "").lower()
    for a, b in (("àâä", "a"), ("éèêë", "e"), ("îï", "i"), ("ôö", "o"),
                 ("ùûü", "u"), ("ç", "c"), ("-", " "), ("'", " ")):
        for lettre in a:
            plat = plat.replace(lettre, b)
    return plat


def lieu_cite(e, texte):
    """Le lieu nomme dans un texte d'etape, s'il y en a un de reconnaissable.

    Heuristique assumee : on cherche le nom (ou l'id) d'un lieu connu dans la
    phrase. C'est le seul moyen de deviner qu'une etape fait VOYAGER quelqu'un
    sans inventer un journal de deplacements.
    """
    plat = sans_accents(texte)
    if not plat:
        return None
    for lid, fiche in e.fiche_lieu.items():
        for etiquette in [fiche.get("nom") or "", lid]:
            aiguille = sans_accents(etiquette)
            if len(aiguille) >= 5 and aiguille in plat:
                return lid
    return None


def detecter_bouches(e, a_resoudre, tombent):
    """Qui arrive ou, et ce qu'il apporte que personne sur place ne sait.

    Deux sources, toutes deux DEJA presentes dans le tick — on branche ce qui
    existe, on n'invente pas de table :
    1. un evenement de la fenetre qui se tient quelque part, dont un acteur
       n'est pas encore sur place : il faudra bien qu'il y vienne ;
    2. une etape de plan qui tombe et dont le texte nomme un autre lieu.

    Le script sort le DIFFERENTIEL de croyances, jamais un verdict : il ne
    recopie rien, ne reecrit aucune tete. Un homme qui sait ne raconte pas tout,
    et ment parfois — c'est au MJ de dire ce qui se dit.
    """
    arrivees = {}       # (personnage, lieu) -> entree

    def noter(pid, vers, source, indice, quand):
        tete = e.intention_par_id.get(pid)
        if tete is None or pid == e.joueur:
            return          # sans tete, rien a porter ; le joueur a sa bouche
        canon = e.lieu(vers)
        ici = e.lieu((e.perso_par_id.get(pid) or {}).get("lieu_id"))
        if not canon or canon == ici:
            return          # deja sur place : personne n'arrive
        cle = (pid, canon)
        if cle in arrivees:
            return
        if source == "etape":
            # le lieu n'est que CITE dans la phrase : il peut n'y envoyer qu'un
            # homme, ou en parler sans y aller. A verifier d'un coup d'oeil.
            indice = "{}  [lieu seulement cite — verifie qu'il y va]".format(
                indice)
        arrivees[cle] = {
            "personnage_id": pid,
            "echelle": echelle_de(tete),
            "de": ici,
            "vers": canon,
            "source": source,
            "indice": indice,
            "date": quand,
        }

    for ev in a_resoudre:
        if not ev.get("lieu_id"):
            continue
        for pid in ev.get("acteurs") or []:
            noter(pid, ev["lieu_id"], "evenement", ev.get("id"), ev.get("date"))
    for s in tombent:
        vers = lieu_cite(e, s.get("quoi") or "")
        if vers:
            noter(s["personnage_id"], vers, "etape", s.get("quoi"),
                  s.get("date_estimee"))

    # ce que les tetes DEJA sur place tiennent pour vrai, lieu par lieu
    su_sur_place = {}
    for tete in e.intentions:
        pid = tete.get("personnage_id")
        lid = e.lieu((e.perso_par_id.get(pid) or {}).get("lieu_id"))
        if lid:
            su_sur_place.setdefault(lid, []).append((pid, croyances_de(tete)))

    lieu_joueur = e.lieu((e.perso_par_id.get(e.joueur) or {}).get("lieu_id"))

    bouches = []
    for (pid, vers), entree in sorted(arrivees.items()):
        tete = e.intention_par_id[pid]
        sur_place = su_sur_place.get(vers, [])
        apporte, deja = [], []
        for croyance in croyances_de(tete):
            porteurs = [autre for autre, sues in sur_place if autre != pid
                        and any(se_recoupent(croyance, s) for s in sues)]
            if porteurs:
                deja.append({"croyance": croyance, "su_par": sorted(porteurs)})
            else:
                apporte.append(croyance)
        entree["apporte"] = apporte
        entree["deja_su_sur_place"] = deja
        entree["tetes_sur_place"] = sorted(a for a, _ in sur_place if a != pid)
        # Le drapeau joueur est reserve aux arrivees SURES (source evenement).
        # Le cout d'un faux positif est asymetrique : bruyant chez le joueur,
        # inoffensif ailleurs. Une arrivee deduite d'une etape reste grise.
        entree["arrive_chez_le_joueur"] = (
            bool(lieu_joueur) and vers == lieu_joueur
            and entree["source"] == "evenement")
        bouches.append(entree)
    return bouches


def cycles(depend):
    """Cycles du graphe etape -> depend_de. Renvoie des chemins fermes."""
    trouves, etat = [], {}

    def descendre(noeud, chemin):
        etat[noeud] = 1
        for suivant in depend.get(noeud, []):
            if suivant not in depend:
                continue
            if etat.get(suivant) == 1:
                boucle = chemin[chemin.index(suivant):] + [suivant]
                if boucle not in trouves:
                    trouves.append(boucle)
            elif etat.get(suivant, 0) == 0:
                descendre(suivant, chemin + [suivant])
        etat[noeud] = 2

    for noeud in sorted(depend):
        if etat.get(noeud, 0) == 0:
            descendre(noeud, [noeud])
    return trouves
