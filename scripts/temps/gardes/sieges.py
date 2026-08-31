# -*- coding: utf-8 -*-
"""GARDES DES SIEGES — l'occupation mesuree, la regence, et les derives.

CE QUE CE MODULE POSSEDE : les verificateurs de ce qui tient au DEHORS du jeu
— l'occupation des sieges confrontee a la mesure (un drapeau qui ne ment pas
tout seul), les sieges vacants qui doivent une tete et la clause de regence,
les audiences du flux a plusieurs, les affectations au monde engendre, les
registres derives (un index ecrit a la main est un index qui va mentir), et
les activations (un taux de perte est une panne, pas une statistique).

CE QU'IL REFUSE : rafraichir quoi que ce soit — il renvoie aux commandes
(sieges.py --rafraichir, regence.py --poser, couverture.py --registres).

CONSOMMATEURS : gardes/__init__.py (verifier()), et
scripts/tests/essai_occupation.py (verifier_occupation, via la facade tick).
"""
import io
import json
import os
import sys

from temps.expose import occupation  # qui est ASSIS - mesure, pas drapeau
# La regence (docs/regence.md) : ce qu'un siege vacant peut faire et ce
# qu'il doit rendre. Branche ici pour la seule garde - clause posee,
# passation due.
from temps.expose import regence
from temps.lecture import RACINE, ETAT


def verifier_occupation(e, r):
    """L'IMPOSSIBLE QUE PERSONNE NE VOYAIT : un drapeau qui ne ment pas tout seul.

    L'invariant historique — occupe -> pas de tete, vacant -> une tete — est
    tenu par la coherence interne du fichier. Il ne dit RIEN quand le fichier
    entier est perime : quatre sieges a `occupe: true`, deux joueurs partis
    depuis la veille, et l'etat reste parfaitement coherent avec lui-meme
    pendant que deux personnages cessent d'exister — ni joues par un humain,
    ni actives par la machine, qui les exclut justement parce qu'ils sont
    marques occupes.

    On confronte donc le fichier au DEHORS : l'age de la veille de sa session
    et le contenu de son inbox (voir `scripts/occupation.py`). Quatre fautes.
    """
    if not e.mesures_sieges:
        return
    for pid in sorted(e.mesures_sieges):
        m = e.mesures_sieges[pid]
        drapeau = e.sieges_drapeau.get(pid, True)

        # 1. Le cache a derive. Grave dans le sens « marque occupe, plus
        #    personne » : c'est le siege qui dort. Simple avertissement dans
        #    l'autre sens — un siege marque vacant que quelqu'un vient de
        #    reveiller sera correctement joue, il est juste mal etiquete.
        if drapeau and not m["occupe"]:
            r.dire("grave", pid,
                   "siege marque `occupe` dans joueurs.json alors que plus "
                   "rien n'y respire ({}) — il n'est ni joue par un humain ni "
                   "active par la boucle, donc il DORT. "
                   "python scripts/sieges.py --rafraichir --vraiment"
                   .format(m["raison"]))
        elif not drapeau and m["occupe"]:
            r.dire("avertissement", pid,
                   "siege marque vacant alors qu'il respire ({}) — cache "
                   "perime (python scripts/sieges.py --rafraichir --vraiment)"
                   .format(m["raison"]))

        # 2. Ce que la fiche RACONTE contre ce qu'on mesure. La note de
        #    nicolas-reynolds disait « VACANT pour l'instant » sous un
        #    `occupe: true` : deux verites dans la meme entree, et c'est la
        #    prose qu'on croit en relisant.
        #    On ne lit que les DECLARATIONS, c'est-a-dire les majuscules : ces
        #    notes crient ce qu'elles affirment (« VACANT pour l'instant »,
        #    « siege ALTERNE ») et parlent en minuscules du reste (« quand ce
        #    siege est occupe, Rhaenyra doit avoir une tete »). Chercher le
        #    mot sans egard a la casse rendrait toute prose coupable.
        note = str(siege_par_id(e, pid).get("note") or "")
        if "VACANT" in note and m["occupe"]:
            r.dire("avertissement", pid,
                   "la note de sa fiche dit VACANT mais le siege est mesure "
                   "assis ({}) — reecrivez la note ou levez-vous".format(
                       m["raison"]))
        if ("OCCUPE" in note or "OCCUPÉ" in note) and not m["occupe"]:
            r.dire("avertissement", pid,
                   "la note de sa fiche dit OCCUPE mais plus rien n'y respire "
                   "({})".format(m["raison"]))

        # 3. Un siege tenu occupe par un inbox qui ne bouge plus. La
        #    definition dit « au moins un fichier » et on ne la change pas —
        #    mais un inbox jamais vide est un `occupe: true` qui ne
        #    redescendra jamais, c'est-a-dire le meme defaut par une autre
        #    porte.
        if m["inbox_dormant"]:
            r.dire("avertissement", pid,
                   "siege tenu occupe par {} action(s) d'inbox dont la plus "
                   "recente date de {} — soit le joueur est parti sans qu'on "
                   "les traite, soit le guetteur est eteint".format(
                       m["inbox"], occupation.dire_age(m["inbox_age_s"])))

    # 4. Deux sieges d'une meme paire ALTERNEE assis en meme temps. Alterne
    #    veut dire : le meme humain, jamais les deux a la fois. C'est declare
    #    par `alterne_avec` dans l'entree du siege — et une note qui parle
    #    d'alternance sans ce champ n'est pas une declaration, c'est un
    #    souvenir.
    for siege in e.sieges:
        pid = siege.get("personnage_id")
        if not pid:
            continue
        pairs = siege.get("alterne_avec")
        if isinstance(pairs, str):
            pairs = [pairs]
        note = str(siege.get("note") or "")
        if not pairs:
            if "ALTERNE" in note.upper():
                r.dire("avertissement", pid,
                       "sa note dit que ce siege est ALTERNE mais son entree "
                       "ne porte pas `alterne_avec` — rien ne peut le "
                       "verifier")
            continue
        for autre in pairs:
            if pid in e.sieges_occupes and autre in e.sieges_occupes:
                r.dire("grave", pid,
                       "siege ALTERNE avec '{}' et tous deux mesures assis en "
                       "meme temps — c'est le meme joueur : l'un des deux est "
                       "un fantome ({} / {})".format(
                           autre,
                           (e.mesures_sieges.get(pid) or {}).get("raison"),
                           (e.mesures_sieges.get(autre) or {}).get("raison")))
            if autre not in e.sieges_drapeau:
                r.dire("avertissement", pid,
                       "`alterne_avec` designe '{}', qui n'est pas un siege"
                       .format(autre))


def siege_par_id(e, pid):
    for siege in e.sieges:
        if siege.get("personnage_id") == pid:
            return siege
    return {}


def verifier_sieges(e, r):
    """Le siege vacant doit avoir une tete ; l'occupe ne doit pas en avoir.

    C'est la garde des sieges alternes. On quitte Rhaenyra pour jouer l'agent
    de Port-Real : elle redevient un PNJ, donc elle a besoin d'une tete, sans
    quoi elle passe la lune a ne rien faire pendant qu'on regarde ailleurs —
    et l'on ne s'en apercoit qu'en revenant s'asseoir, trois lunes trop tard.
    Le symetrique (une tete sous un siege occupe) est deja dit par
    verifier_intentions : le MJ jouerait le personnage du joueur.
    """
    for pid in sorted(e.sieges_vacants):
        if pid not in e.intention_par_id:
            r.dire("grave", pid,
                   "siege VACANT sans tete dans intentions.json — ce "
                   "personnage n'agira pas hors ecran tant qu'on ne lui en "
                   "ecrit pas une")
        else:
            # LA CLAUSE DE REGENCE. Le garde mecanique de
            # `boucle_activation.py` refuse deja les rapports qui franchissent
            # la ligne, mais un homme qui l'ignore y va, se fait refuser et
            # perd un passage de correction a chaque fois. La clause dans sa
            # tete est ce qui evite le mur ; le garde est ce qui le rattrape
            # quand il l'oublie. On veut les deux.
            if not regence.clause_posee(e.intention_par_id.get(pid)):
                r.dire("avertissement", pid,
                       "siege vacant dont la tete ne porte pas la clause de "
                       "regence — il ignore ce qu'il ne doit pas conclure "
                       "(python scripts/regence.py --poser {} --vraiment)"
                       .format(pid))
        perso = e.perso_par_id.get(pid)
        if perso is not None and perso.get("etat") != "actif":
            r.dire("avertissement", pid,
                   "siege vacant dont la fiche est '{}' — un siege qu'on "
                   "reprendra un jour reste actif".format(perso.get("etat")))
    for pid in sorted(e.sieges_occupes | e.sieges_vacants):
        if pid not in e.perso_par_id:
            r.dire("grave", pid,
                   "siege pour un personnage absent de personnages.json")
    verifier_occupation(e, r)
    if (e.sieges and e.joueur and e.joueur in e.sieges_vacants
            and not siege_par_id(e, e.joueur).get("laisser_faire")):
        # Un siege en LAISSER FAIRE PERMANENT (etat/joueurs.json) est vacant
        # par definition et pour longtemps : le journal peut continuer de le
        # designer comme personnage du joueur sans que ce soit une anomalie.
        r.dire("avertissement", "journal",
               "journal.personnage_joueur_id vaut '{}' alors que son siege "
               "est marque vacant".format(e.joueur))
    # Ce qu'un siege a decide seul et qu'on n'a pas encore rendu a celui qui
    # s'y rassoit. Ce n'est une faute pour personne tant qu'il est vacant ; ca
    # en devient une des qu'il est occupe, parce qu'alors le joueur joue sans
    # savoir ce qu'on a engage en son nom.
    for pid in sorted(e.sieges_occupes | e.sieges_vacants):
        _, en_attente = regence.compte_rendu(pid)
        if not en_attente:
            continue
        if pid in e.sieges_occupes:
            r.dire("avertissement", pid,
                   "{} decision(s) prises en regence jamais rendues a celui "
                   "qui s'y est rassis (python scripts/regence.py "
                   "--compte-rendu {})".format(len(en_attente), pid))
        franchies = sum(len(x.get("lignes_franchies") or [])
                        for x in en_attente)
        if franchies:
            r.dire("grave", pid,
                   "{} ligne(s) irreversible(s) franchies par ce siege en "
                   "regence — le garde a ete contourne, relisez son "
                   "registre".format(franchies))


def verifier_audiences(e, r):
    """A plusieurs, aucun item du flux ne doit etre sans audience.

    Un `pour` absent ne veut pas dire « pour tout le monde » : il veut dire
    « rien n'a ete declare ». Le serveur ne sert plus ces items-la passe le
    seuil (la ligne ou le dernier joueur s'est assis), donc ils ne fuitent
    plus — mais ils DISPARAISSENT, ce qui est un bug silencieux d'une autre
    espece : le MJ croit avoir pousse une scene que personne ne lit. On le dit
    ici, pendant que c'est encore reparable.
    """
    if len(e.sieges_occupes) < 2:
        return
    seuil = 0
    for j in e.sieges:
        seuil = max(seuil, j.get("depuis") or 0)
    chemin = os.path.join(RACINE, "etat", "flux.jsonl")
    orphelins = []
    try:
        with io.open(chemin, encoding="utf-8") as f:
            for i, ligne in enumerate(f):
                if not ligne.strip() or i < seuil:
                    continue
                try:
                    it = json.loads(ligne)
                except Exception:
                    continue
                if not it.get("pour"):
                    orphelins.append(i)
    except Exception:
        return
    if orphelins:
        r.dire("grave", "flux",
               "{} items du flux sans `pour` apres la ligne {} — ils ne sont "
               "servis a personne. Lignes : {}{}".format(
                   len(orphelins), seuil,
                   ", ".join(str(n) for n in orphelins[:8]),
                   "…" if len(orphelins) > 8 else ""))


def verifier_affectations(e, r):
    """Les adresses physiques donnees en jeu tiennent-elles encore ?

    Une affectation joint une chose de la fiction a un batiment du monde
    engendre (voir scripts/affecter.py). Le monde se regenere ; l'affectation,
    non. Une cible disparue ne casse rien a l'ecran — elle ment en silence, et
    l'on continue de calculer des distances sur un batiment qui n'existe plus.
    """
    try:
        from agents.expose import affecter
    except ImportError:
        return
    L = affecter.charger_liens()
    if not L["affectations"]:
        return
    try:
        # `verifier` ouvre lui-meme le monde nomme par CHAQUE affectation : le
        # batiment doit exister encore, et dans le bon monde. Un monde absent
        # se signale au lieu de faire taire toute la verification.
        maux = affecter.verifier(L)
    except SystemExit:
        return                       # pas de monde engendre : rien a verifier
    for mal in maux:
        r.dire("avertissement", "affectations", mal)


def verifier_registres_derives(e, r):
    """Un index ecrit a la main est un index qui va mentir.

    Les quatre registres par type — `plan-etats-cibles`, `plan-verrous`,
    `plan-clefs`, `plan-actions` — ne sont plus une seconde verite : ils sont
    DERIVES des cahiers d'affaire, par `python scripts/couverture.py
    --registres`. La regle du guide (« quand l'affaire et le registre se
    contredisent, c'est le registre qui a raison ») supposait un registre tenu ;
    il ne l'etait plus, 108 lignes contre 1312.

    Ce qu'on a paye pour l'apprendre : Le Sanglier avait renomme l'etat cible
    23000 dans son cahier, le registre portait toujours l'ancien nom, et sa
    propre liste de trous lui a resservi le nom perime le matin meme. Deux
    copies d'un plan n'est pas un defaut de proprete : c'est une machine a
    envoyer les hommes contre des fantomes.

    Sans cette garde, quelqu'un y posera une ligne de bonne foi dans six
    semaines — et la nuit du 31e sera a refaire a l'identique. `plan-moyens` et
    `plan-offices` n'en sont pas : ce sont des SOURCES, pas des copies.
    """
    try:
        from plan.expose import couverture
    except ImportError:
        return
    try:
        ecarts, divergences = couverture.ecart_registres(e.books)
    except Exception as mal:                      # un index ne bloque pas l'audit
        r.dire("note", "registres", "impossible de recalculer : {}".format(mal))
        return
    if divergences:
        # ON LES NOMME, ON NE LES COMPTE PAS SEULEMENT. Une retouche a la main
        # du NOM d'une piece cree une divergence que la regle de conservation
        # reproduit fidelement : l'ecart se referme sur lui-meme et la
        # comparaison ne voit rien. La liste, elle, s'allonge — et c'est le seul
        # signe qu'on ait.
        r.dire("note", "registres",
               "{} nom(s) divergent(s) entre index et cahier, conserves tels "
               "quels : {} — si cette liste s'allonge, quelqu'un a ecrit dans "
               "un index (voir docs/echiquier.md)".format(
                   len(divergences), " · ".join(n for _, n in divergences)))
    for bid, a, n in ecarts:
        if a < 0:
            r.dire("avertissement", "registre {}".format(bid),
                   "titre non marque « calcule » — relancer "
                   "`python scripts/couverture.py --registres`")
        else:
            r.dire("avertissement", "registre {}".format(bid),
                   "ECRIT A LA MAIN, ou perime : {} ligne(s) sur le disque, {} "
                   "derivees des cahiers. Le cahier est la verite — reporter la "
                   "modification dans le cahier d'affaire, puis relancer "
                   "`python scripts/couverture.py --registres` (voir "
                   "docs/echiquier.md)".format(a, n))


def verifier_activations(e, r):
    """Ce que la boucle d'activation a produit, et ce qui a ete jete.

    LE SILENCE DES REJETS EST LE PIRE DEFAUT QU'ON AIT EU. Le 10 aout, 326
    mutations sur 355 etaient refusees — 92 % — pour une seule et meme cause :
    le narrateur citait son resultat sous la clef `cite` quand le validateur
    lisait `resultat_id`. La boucle a tourne des nuits entieres en produisant
    presque rien, et rien nulle part ne le disait. Un taux de perte est une
    panne, pas une statistique : il doit crier des le premier tour.
    """
    depot = os.path.join(ETAT, "activations")
    if not os.path.isdir(depot):
        return

    # LE CUMUL DE TOUJOURS EST UNE MAUVAISE MESURE, et c'est la lecon du
    # 10 aout au soir : la panne `resultat_id` etait REPAREE, et le taux
    # affichait encore 78 % parce que les 326 rejets d'avant la reparation
    # dorment sur le disque et y dormiront toujours. Un taux qu'aucune
    # correction ne peut faire baisser ne signale plus rien.
    # On mesure donc la FENETRE RECENTE — c'est elle qui dit l'etat de la
    # boucle maintenant — et le cumul ne sort qu'en note, pour memoire.
    FENETRE = 25

    def depouiller(noms):
        retenues, rejetees, causes = 0, 0, {}
        for nom in noms:
            try:
                with io.open(os.path.join(depot, nom), encoding="utf-8") as fh:
                    rapport = json.load(fh)
            except (ValueError, OSError):
                continue
            if not isinstance(rapport, dict):
                continue
            retenues += len(rapport.get("mutations_proposees") or [])
            for jetee in rapport.get("mutations_rejetees") or []:
                rejetees += 1
                if isinstance(jetee, dict):
                    cause = str(jetee.get("erreur") or "sans cause")[:80]
                    causes[cause] = causes.get(cause, 0) + 1
        return retenues, rejetees, causes

    # Les rapports sont horodates dans leur nom : le tri alphabetique est
    # l'ordre chronologique, et on n'a pas a interroger le disque.
    noms = sorted(n for n in os.listdir(depot)
                  if n.endswith(".json") and n != "boucle.json")
    if not noms:
        return
    recents = noms[-FENETRE:]
    retenues, rejetees, causes = depouiller(recents)
    total = retenues + rejetees
    if not total:
        return
    part = 100.0 * rejetees / total
    niveau = "grave" if part >= 25 else ("avertissement" if part >= 5
                                         else "note")
    r.dire(niveau, "activations",
           "{} mutations sur {} jetees ({:.0f} %) sur les {} derniers "
           "rapports — la boucle produit {} changement(s) applicable(s)".format(
               rejetees, total, part, len(recents), retenues))
    for cause, combien in sorted(causes.items(), key=lambda x: -x[1])[:3]:
        r.dire(niveau, "activations",
               "  {} fois : {}".format(combien, cause))

    if len(noms) > len(recents):
        cum_ret, cum_rej, _ = depouiller(noms)
        cum_total = cum_ret + cum_rej
        if cum_total:
            r.dire("note", "activations",
                   "pour memoire, depuis le premier rapport : {} sur {} "
                   "jetees ({:.0f} %) en {} rapports — ce chiffre porte les "
                   "pannes deja reparees et ne baissera jamais".format(
                       cum_rej, cum_total, 100.0 * cum_rej / cum_total,
                       len(noms)))
